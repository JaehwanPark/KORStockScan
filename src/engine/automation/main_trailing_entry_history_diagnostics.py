"""Causal stored OHLC prefixes for research, never a runtime classifier.

One private native carrier per day and one scope catalog per carrier avoid
repeated whole-catalog decoding. Original availability and bar closes bound
every named-revision read. Missing spread/VWAP remain missing.
"""
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime
import argparse
import json
import math
from pathlib import Path
import sqlite3
import sys
import zlib

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.main_exit_scope import build_scope
from src.engine.scalping import main_exit_scope as scope_owner, reversal_registered_catalog
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number
from src.engine.scalping.universal_trailing_replay import research_entry_window_start
from src.trading.market import completed_history as history
from . import main_trailing_minute_path_diagnostics as minute
from .main_trailing_all_scope_research import _sealed, _source_path

SCHEMA = 'main_trailing_causal_entry_history_diagnostics_v1'
FEATURES = ('range_pct', 'return_pct', 'trend_efficiency', 'rebound_pct')
WINDOW = 120
MAX_METADATA_BYTES = 4 * 1024 * 1024
SELECTION_CLOCK = 'revision_available_at_at_or_before_entry_and_bar_close_at_or_before_entry'
CLEAN_START_AT = research_entry_window_start(['2026-06-05'])


def _metadata_generation(path):
    if not 0 < path.stat().st_size <= MAX_METADATA_BYTES:
        raise ValueError('entry_history_metadata_budget_invalid')
    return byte_generation(path)


def _carrier_matches(path, generation):
    if generation == {'missing':True}:
        return not Path(path).exists() and not Path(str(path)+'-wal').exists()
    return minute.carrier_generation(path) == generation


def _clock(value):
    if type(value) not in (int, float):
        raise ValueError('entry_history_clock_invalid')
    try:
        valid = math.isfinite(value) and value > 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError('entry_history_clock_invalid')
    return value


class EntryHistory:
    """Private snapshot reader; at most one full revision stays decoded."""
    def __init__(self, snapshot, day, items, retained):
        self.snapshot, self.day = snapshot, day
        self.catalog = defaultdict(list)
        self.cached = None
        self.stats = Counter()
        path = snapshot['read_root']/'runtime/main_minute_history'/day/'completed.sqlite3'
        self.db = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=.025)
        try:
            self.db.execute('PRAGMA query_only=ON')
            self.db.execute('PRAGMA mmap_size=0')
            self.db.execute('PRAGMA cache_size=-2048')
            for scope, revision in self.db.execute('SELECT scope,revision FROM current'):
                row = self.db.execute('SELECT manifest FROM revisions WHERE hash=? AND scope=?',
                                      (revision, scope)).fetchone()
                if row is None:
                    raise ValueError('entry_history_native_reader_rejected')
                manifest = self._decode(row[0], revision)
                identity = manifest['identity']
                if history._digest(identity) != scope:
                    raise ValueError('entry_history_scope_checksum_invalid')
                self.stats['catalog_scopes_inspected'] += 1
                if identity.get('item') not in items or identity.get('date') != day:
                    continue
                if (identity.get('schema') != history.SCHEMA or identity.get('interval_sec') != 60
                        or identity.get('time_basis') != 'provider_bar_open_kst'
                        or identity.get('adjustment') != 'ka10080:upd_stkpc_tp=1'
                        or not isinstance(identity.get('session'), str) or not identity['session']
                        or not isinstance(identity.get('auth_scope'),list) or not identity['auth_scope']
                        or any(not isinstance(v,str) or not v for v in identity['auth_scope'])):
                    raise ValueError('entry_history_chart_contract_invalid')
                clocks = self.db.execute('SELECT available,hash FROM revisions WHERE scope=? '
                    'ORDER BY available,hash LIMIT ?', (scope, history.MAX_REVISIONS_PER_SCOPE+1)).fetchall()
                if len(clocks) > history.MAX_REVISIONS_PER_SCOPE:
                    raise ValueError('entry_history_revision_budget_invalid')
                for at, fingerprint in clocks:
                    _clock(at)
                    if (not isinstance(fingerprint, str) or len(fingerprint) != 64
                            or any(c not in '0123456789abcdef' for c in fingerprint)):
                        raise ValueError('entry_history_revision_identity_invalid')
                retained.grow(len(clocks)*256+4096)
                self.catalog[identity['item']].append((scope, identity, clocks))
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.cached = None
        self.db.close()

    def _decode(self, blob, fingerprint):
        value = history._unpack(blob)
        if history._digest(value) != fingerprint:
            raise ValueError('entry_history_revision_checksum_invalid')
        self.stats['manifests_decoded'] += 1
        return value

    def read(self, item, entry_at):
        entry_at = _clock(entry_at)
        candidate, comparable, sessions, conflicting = None, None, set(), False
        for scope, identity, clocks in self.catalog.get(item, []):
            known = [(at, fingerprint) for at, fingerprint in clocks if at <= entry_at]
            if not known:
                continue
            chart = {k:v for k,v in identity.items() if k != 'session'}
            if comparable is not None and chart != comparable:
                raise ValueError('entry_history_exact_scope_ambiguous')
            comparable = chart
            sessions.add(identity['session'])
            latest = max(at for at, _ in known)
            for at, fingerprint in known:
                if at != latest:
                    continue
                blob = self.db.execute('SELECT manifest FROM revisions WHERE hash=? AND scope=?',
                                       (fingerprint, scope)).fetchone()
                if blob is None:
                    raise ValueError('entry_history_native_reader_rejected')
                manifest = self._decode(blob[0], fingerprint)
                _clock(manifest['first_receipt']['received_at'])
                if (manifest['identity'] != identity
                        or manifest['first_receipt']['received_at'] != at):
                    raise ValueError('entry_history_revision_clock_or_identity_invalid')
                if candidate is None or at > candidate[0]:
                    candidate, conflicting = (at,fingerprint,manifest), False
                elif at == candidate[0]:
                    conflicting |= manifest['bar_hashes'] != candidate[2]['bar_hashes']
                    if fingerprint > candidate[1]:
                        candidate = (at,fingerprint,manifest)
                # Only the winner and the current checked manifest survive;
                # a same-clock correction list must not retain 2048 decodes.
                del manifest
        if candidate is None:
            raise ValueError('entry_history_no_local_revision_known_by_entry')
        if conflicting:
            raise ValueError('entry_history_same_clock_revision_conflict')
        available, revision, manifest = candidate
        count = len(manifest['bar_hashes'])
        if not 0 < count <= history.MAX_ROWS:
            raise ValueError('entry_history_revision_count_invalid')
        if self.cached is not None and self.cached[0] == revision:
            bars = self.cached[1]
            self.stats['full_revision_cache_hits'] += 1
        else:
            self.cached = None
            # Native bars.content is plain JSON, not the bounded revision blob.
            # Admit its decode plus native deepcopy before the public read.
            query = 'SELECT COUNT(*),SUM(length(CAST(content AS BLOB))) FROM bars WHERE hash IN ('+','.join('?' for _ in manifest['bar_hashes'])+')'
            found, raw_bytes = self.db.execute(query,manifest['bar_hashes']).fetchone()
            if found != count or type(raw_bytes) is not int or raw_bytes <= 0:
                raise ValueError('entry_history_bar_content_missing')
            with Claim(raw_bytes*16):
                value = history.read(self.snapshot['read_root'], manifest['identity'], now=entry_at,
                                     limit=count, include_forming=False, revision=revision)
                if value is None:
                    raise ValueError('entry_history_native_reader_rejected')
                raw_bars, meta = value
                if (meta.get('api_id') != 'ka10080' or meta.get('request_code') != item
                        or meta.get('shared_history_available_at') != available
                        or len(raw_bars) != count
                        or raw_bars[0].get('source_timestamp') != manifest['first_completed']
                        or raw_bars[-1].get('source_timestamp') != manifest['last_completed']):
                    raise ValueError('entry_history_provenance_invalid')
                bars = _validate_bars(raw_bars, available=available, day=self.day)
                del raw_bars, value, meta
            self.cached = (revision, bars)
            self.stats['native_full_revision_reads'] += 1
            self.stats['admitted_native_bar_json_bytes'] += raw_bytes
        if available > entry_at or bars[-1]['closed_at'] > entry_at:
            raise ValueError('entry_history_future_revision_or_bar')
        source = dict(revision_sha256=revision, available_at=available,
            source_identity=manifest['identity'], comparable_chart_identity_sha256=digest(comparable),
            eligible_acquisition_sessions=sorted(sessions), source_completed_bar_count=count,
            first_completed=manifest['first_completed'], last_completed=manifest['last_completed'],
            source_generation=self.snapshot['generation'], source_path=str(self.snapshot['path']),
            selection_rule='latest_local_named_revision_available_at_or_before_entry')
        return bars, source


def _validate_bars(rows, *, available, day):
    result, previous = [], None
    for row in rows:
        stamp = row.get('source_timestamp')
        if not isinstance(stamp, str) or len(stamp) != 14 or stamp[-2:] != '00':
            raise ValueError('entry_history_bar_timestamp_invalid')
        at = datetime.strptime(stamp, '%Y%m%d%H%M%S').replace(tzinfo=minute.KST).timestamp()
        fields = [row.get(k) for k in ('시가', '고가', '저가', '현재가', '거래량')]
        if (any(type(x) is not int or x < 0 for x in fields)
                or not 0 < fields[2] <= min(fields[0], fields[3]) <= max(fields[0], fields[3]) <= fields[1]
                or at+60 > available or stamp[:8] > day or previous is not None and at <= previous):
            raise ValueError('entry_history_completed_bar_invalid')
        result.append(dict(opened_at=at, closed_at=at+60, day=stamp[:8],
                           close=fields[3], high=fields[1], low=fields[2]))
        previous = at
    if not result:
        raise ValueError('entry_history_empty_revision')
    return result


def describe(bars, *, entry_at, source, config):
    """Four formulas shared with entry_features, without invented BBO/VWAP."""
    entry_at = _clock(entry_at)
    if (_clock(source['available_at']) > entry_at or any(b['closed_at'] > entry_at for b in bars)):
        raise ValueError('entry_history_future_revision_or_bar')
    eligible = [bar for bar in bars if bar['opened_at'] >= CLEAN_START_AT]
    selected = eligible[-WINDOW:]
    day = datetime.fromtimestamp(entry_at, minute.KST).strftime('%Y%m%d')
    close = [row['close'] for row in selected]
    low, high = [row['low'] for row in selected], [row['high'] for row in selected]
    gaps = sum(max(0, int((right['opened_at']-left['opened_at'])/60)-1)
               for left,right in zip(selected,selected[1:]) if left['day'] == right['day'] == day)
    features = None
    if len(selected) >= 2:
        travel = math.fsum(abs(b-a) for a,b in zip(close,close[1:]))
        features = dict(range_pct=100*(max(high)-min(low))/close[-1],
            return_pct=100*(close[-1]/close[0]-1),
            trend_efficiency=abs(close[-1]-close[0])/travel if travel else 0,
            rebound_pct=100*(close[-1]/min(low)-1))
        if any(not math.isfinite(v) for v in features.values()):
            raise ValueError('entry_history_nonfinite_features')
    bins = None
    if features:
        edges = config['pattern_bins']['range_pct_edges']
        trend = config['pattern_bins']['upward_efficient']
        bins = dict(range_band=sum(features['range_pct'] >= edge for edge in edges),
            upward_efficient=features['return_pct'] >= trend['return_pct_min']
                and features['trend_efficiency'] >= trend['trend_efficiency_min'],
            role='preregistered_descriptive_ohlc_only_no_policy_type')
    status = 'ohlc_window_diagnostic' if len(selected) == WINDOW else 'ohlc_partial_window'
    if not selected:
        status = 'source_gap'
    return dict(status=status,
        reason=None if features else ('fewer_than_two_completed_bars' if selected else 'entry_history_no_clean_completed_bars'), features=features,
        descriptive_bins=bins, window_bars=len(selected), full_120_bar_window=len(selected) == WINDOW,
        feature_clean_baseline_start_at=CLEAN_START_AT, source_pre_clean_bar_count=len(bars)-len(eligible),
        eligible_clean_completed_bar_count=len(eligible),
        prior_date_bar_count=sum(row['day'] < day for row in selected),
        source_prior_date_bar_count=sum(row['day'] < day for row in bars),
        first_bar_open_at=selected[0]['opened_at'] if selected else None,
        last_bar_close_at=selected[-1]['closed_at'] if selected else None,
        last_completed_bar_age_seconds=entry_at-selected[-1]['closed_at'] if selected else None,
        revision_age_seconds=entry_at-source['available_at'], same_day_internal_missing_minutes=gaps,
        same_day_gap_scope='between_selected_observed_bars_only_no_session_open_assumption',
        spread_pct=None, session_vwap=None, vwap_distance_pct=None,
        runtime_six_feature_classifier_ready=False, original_runtime_consumption_proven=False,
        adjustment_equivalence_to_reference='unproven', source=source)


def _registration(path, manifest_path, manifest):
    value = _sealed(path)
    config = value.get('diagnostics', {}).get('entry_history', {})
    if (value.get('schema') != 'main_trailing_followup_registration_v1'
            or Path(value.get('input_manifest_path', '')).resolve() != manifest_path.resolve()
            or value.get('input_manifest_generation') != byte_generation(manifest_path)
            or any(value.get(k) != manifest.get(k) for k in ('source_date', 'target_date', 'as_of'))
            or value.get('allowed_runtime_apply') is not False or value.get('runtime_effect') is not False
            or value.get('actual_pid_consumed') is not False
            or value.get('decision_authority') != 'report_only'
            or type(config.get('window_bars')) is not int or config['window_bars'] != WINDOW
            or type(config.get('minimum_feature_bars')) is not int or config['minimum_feature_bars'] != 2
            or config.get('features') != list(FEATURES)
            or config.get('runtime_six_feature_classifier_ready') is not False
            or config.get('original_runtime_consumption_proven') is not False
            or config.get('selection_clock') != SELECTION_CLOCK
            or config.get('spread_pct') is not None or config.get('session_vwap') is not None):
        raise ValueError('entry_history_registration_contract_invalid')
    metric = value.get('metric_contract',{})
    if (metric.get('decision_authority') != 'report_only' or metric.get('primary_decision_metric') != 'none'
            or metric.get('metric_role') != 'funnel_count' or metric.get('sample_floor') != 'diagnostic_no_promotion'):
        raise ValueError('entry_history_registration_metric_contract_invalid')
    if not (date.fromisoformat(value['holdout_start_date']) <= date.fromisoformat(value['holdout_end_date'])
            <= date.fromisoformat(manifest['source_date'])):
        raise ValueError('entry_history_registration_holdout_invalid')
    for x in config['pattern_bins']['range_pct_edges'] + list(config['pattern_bins']['upward_efficient'].values()):
        if type(x) not in (int,float) or number(x) is None:
            raise ValueError('entry_history_registration_nonfinite')
    return value, config


def build(manifest_path, *, input_root, data_root, registration_path):
    with Claim(0) as retained:
        return _build(Path(manifest_path), Path(input_root).resolve(), Path(data_root).resolve(),
                      Path(registration_path), retained)


def _build(manifest_path, root, data_root, registration_path, retained):
    manifest_path = _source_path(root, str(manifest_path.absolute().relative_to(root)))
    manifest_generation, registration_generation = _metadata_generation(manifest_path), _metadata_generation(registration_path)
    modules = (minute,history,storage,scope_owner,reversal_registered_catalog,
        *(sys.modules[owner.__module__] for owner in
          (research_entry_window_start,_sealed,_source_path,digest,number,byte_generation,Claim)))
    code_paths = sorted({Path(__file__),*(Path(module.__file__) for module in modules)})
    code = {str(p):byte_generation(p) for p in code_paths}
    retained.grow((manifest_generation['size']+registration_generation['size'])*8)
    manifest = _sealed(manifest_path)
    if (manifest.get('schema') != 'main_all_scope_exit_input_manifest_v2'
            or Path(manifest['source_data_root']).resolve() != data_root):
        raise ValueError('entry_history_manifest_contract_invalid')
    cutoff = _clock(manifest['as_of'])
    registration, config = _registration(registration_path, manifest_path, manifest)
    window_start = research_entry_window_start(manifest['consumed_dates'])
    window_end = datetime.fromisoformat(manifest['source_date']+'T00:00:00+09:00').timestamp()+86400
    registered_scope_width = sum(map(len,scope_owner.ROUTES.values()))
    with Claim(len(manifest['universe'])*registered_scope_width*512):
        full_scope = build_scope(manifest['universe'], as_of=cutoff,
            universe_source_sha256=manifest['universe_source_sha256'], operating=manifest.get('operating'),
            coverage=manifest.get('coverage'), custody=manifest.get('custody'))
        scope = {k:v for k,v in full_scope.items() if k != 'scopes'}
        del full_scope
    groups, rows, populations, parts = defaultdict(list), [], set(), {}
    for path,generation,part in minute._partitions(root,manifest):
        if (str(path) in parts or part['source_date'] != manifest['source_date']
                or part.get('target_date',manifest['target_date']) != manifest['target_date']):
            raise ValueError('entry_history_partition_contract_invalid')
        parts[str(path)] = generation
        for p in part['positions']:
            identity, kind = p['position_key'], p['evidence_kind']
            if not isinstance(identity,str) or not identity or identity in populations:
                raise ValueError('entry_history_duplicate_population')
            retained.grow(8192+8*len(json.dumps([p.get('entry_context'),p.get('situation_pin')],
                ensure_ascii=True,allow_nan=False).encode()))
            populations.add(identity)
            if kind == 'actual_entry_alternative_exit':
                continue
            if kind not in ('actual_completed','enter_pass_opportunity_cf'):
                raise ValueError('entry_history_evidence_kind_invalid')
            try:
                at = _clock(p.get('entry_at'))
            except ValueError:
                at = None
            row = dict(identity=identity, symbol=p.get('symbol'), item=p.get('item'), route=p.get('route'),
                evidence_kind=kind, entry_at=at, automatic_management_allowed=p.get('automatic_management_allowed'),
                original_entry_context=p.get('entry_context'), original_situation_pin=p.get('situation_pin'),
                research_entry_window_start_at=window_start, features=None, source=None,
                research_entry_window_end_exclusive_at=window_end,
                spread_pct=None, session_vwap=None, vwap_distance_pct=None,
                original_runtime_consumption_proven=False,
                runtime_six_feature_classifier_ready=False, runtime_effect=False, actual_profit_verified=False)
            rows.append(row)
            if at is not None and at < window_start:
                row.update(status='audit_only', reason='entry_before_research_window')
            elif at is not None and at >= window_end:
                row.update(status='audit_only', reason='entry_after_research_window')
            elif (at is None or at <= 0 or at > cutoff or not isinstance(row['item'],str)
                    or row['item'].split('_',1)[0] != row['symbol'] or not row['route']):
                row.update(status='source_gap', reason='entry_history_original_entry_or_item_missing')
            else:
                day = datetime.fromtimestamp(at, minute.KST).strftime('%Y%m%d')
                row['chronological_partition'] = ('holdout' if day >= registration['holdout_start_date'].replace('-','') else 'train')
                groups[day].append(row)
        # _partitions' raw/decode Claim ends when iteration advances. Keep only
        # the explicitly budgeted row projections, not the last partition.
        p = None
        del part
    expected = list(storage.iter_tree(root,manifest['population_ids_ref']))
    if len(expected) != len(set(expected)) or set(expected) != populations:
        raise ValueError('entry_history_population_mismatch')
    carriers, reader_stats = {}, Counter()
    for day, day_rows in sorted(groups.items()):
        staged = []
        try:
            with Claim(history.MAX_ROWS*4096+2*2*1024*1024*8), Claim(0) as catalog_budget, minute._snapshot(data_root,day) as snapshot:
                with closing(EntryHistory(snapshot, day, {r['item'] for r in day_rows}, catalog_budget)) as reader:
                    for row in sorted(day_rows,key=lambda r:(r['item'],r['entry_at'],r['identity'])):
                        try:
                            bars, source = reader.read(row['item'],row['entry_at'])
                            retained.grow(8*len(json.dumps(source,ensure_ascii=True,allow_nan=False).encode()))
                            staged.append((row,describe(bars,entry_at=row['entry_at'],source=source,config=config)))
                        except (ValueError,TypeError,KeyError,OverflowError,sqlite3.Error,zlib.error) as exc:
                            if str(exc) == 'shared_research_budget_partition_resume_required':
                                raise
                            issue = str(exc) if str(exc).startswith('entry_history_') else 'entry_history_source_contract_invalid'
                            row.update(status='source_gap',reason=issue,features=None,source=None)
                    reader_stats.update(reader.stats)
                carriers[str(snapshot['path'])] = snapshot['generation']
            for row, result in staged:
                row.update(result)
        except (OSError,ValueError,TypeError,KeyError,OverflowError,sqlite3.Error,zlib.error) as exc:
            if str(exc) in {'minute_history_provenance_changed', 'window_dependency_changed_during_read',
                            'shared_research_budget_partition_resume_required'}:
                raise
            issue = str(exc) if str(exc).startswith(('minute_history_','entry_history_')) else 'entry_history_source_contract_invalid'
            if issue == 'minute_history_not_stored':
                carriers[str(data_root/'runtime/main_minute_history'/day/'completed.sqlite3')] = {'missing':True}
            for row in day_rows:
                row.update(status='source_gap',reason=issue,features=None,source=None)
    for path,generation in carriers.items():
        if not _carrier_matches(path,generation):
            raise ValueError('entry_history_source_carrier_changed')
    for path,generation in {**parts,**code}.items():
        if byte_generation(Path(path)) != generation:
            raise ValueError('entry_history_consumed_generation_changed')
    for _ in storage.iter_tree(root,manifest['partitions_ref']):
        pass
    for _ in storage.iter_tree(root,manifest['population_ids_ref']):
        pass
    if byte_generation(manifest_path) != manifest_generation or byte_generation(registration_path) != registration_generation:
        raise ValueError('entry_history_manifest_or_registration_changed')
    counts = Counter((r['evidence_kind'],r['status'],r.get('reason')) for r in rows)
    body = dict(schema=SCHEMA,source_date=manifest['source_date'],target_date=manifest['target_date'],as_of=cutoff,
        registration_generation=registration_generation,input_manifest_generation=manifest_generation,
        code_generations=code,input_partition_generations=parts,source_carrier_generations=carriers,
        input_population_count=len(populations),population_count=len(rows),count_unit='position_or_opportunity_rows',
        excluded_alternative_exit_count=len(populations)-len(rows),scope=scope,
        scope_projection='native_summary_and_full_scope_digest_without_retained_scope_rows',
        rows=sorted(rows,key=lambda r:r['identity']),reader_stats=dict(reader_stats),
        status_counts=[dict(evidence_kind=k[0],status=k[1],reason=k[2],count=v) for k,v in sorted(counts.items(),key=lambda x:str(x[0]))],
        original_entry_context_or_pin_modified=False,runtime_six_feature_classifier_ready=False,
        original_runtime_consumption_proven=False,local_source_gap_proves_official_unavailability=False,
        metric_contract=registration['metric_contract'],runtime_effect=False,allowed_runtime_apply=False,
        actual_profit_verified=False)
    return {**body,'artifact_sha256':digest(body)}


def run(registration_path, manifest_path, *, input_root, data_root, output_root):
    registration_path, manifest_path = Path(registration_path), Path(manifest_path)
    input_root, data_root, output_root = Path(input_root), Path(data_root), Path(output_root)
    for path in (registration_path,manifest_path,input_root,data_root,output_root):
        if path.is_symlink() or any(p.is_symlink() for p in path.absolute().parents):
            raise ValueError('entry_history_source_or_output_symlink')
    _metadata_generation(registration_path)
    registered = _sealed(registration_path)['diagnostics']['entry_history']['output_root']
    if output_root.resolve() != Path(registered).resolve() or output_root.exists():
        raise ValueError('entry_history_output_not_new_registered_destination')
    if output_root.resolve().is_relative_to(data_root.resolve()) or output_root.resolve().is_relative_to(input_root.resolve()):
        raise ValueError('entry_history_output_overlaps_original_source')
    result = build(manifest_path,input_root=input_root,data_root=data_root,registration_path=registration_path)
    for path,generation in {**result['input_partition_generations'],**result['code_generations'],
            str(manifest_path):result['input_manifest_generation'],str(registration_path):result['registration_generation']}.items():
        if byte_generation(Path(path)) != generation:
            raise ValueError('entry_history_prepublication_generation_changed')
    for path,generation in result['source_carrier_generations'].items():
        if not _carrier_matches(path,generation):
            raise ValueError('entry_history_prepublication_carrier_changed')
    manifest = _sealed(manifest_path)
    for key in ('population_ids_ref','partitions_ref'):
        for _ in storage.iter_tree(input_root,manifest[key]):
            pass
    output_root.mkdir(parents=True,exist_ok=False)
    with (output_root/'report.json').open('x') as handle:
        json.dump(result,handle,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        handle.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('registration','manifest','input-root','data-root','output-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    result = run(args.registration,args.manifest,input_root=args.input_root,data_root=args.data_root,output_root=args.output_root)
    print(f"complete population={result['population_count']} scope={result['scope']['scope_count']}")


if __name__ == '__main__':
    main()
