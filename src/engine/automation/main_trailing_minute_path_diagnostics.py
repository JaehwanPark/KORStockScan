"""Completed-minute price-path diagnostics, never executable trailing evidence.

Uses the existing ka10080 revision producer and its public verified reader.
Native ask references do not supply an order plan, depth or actual fill.
"""
from collections import Counter, defaultdict
from contextlib import closing, contextmanager
from datetime import datetime
import math
from pathlib import Path
import sqlite3
import stat
import tempfile
import zlib
from zoneinfo import ZoneInfo

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number
from src.trading.market import completed_history
from .main_trailing_all_scope_research import _sealed, _source_path

SCHEMA = 'main_trailing_completed_minute_path_diagnostics_v1'
HORIZONS = (1, 3, 5, 10, 20, 30, 60)
KST = ZoneInfo('Asia/Seoul')
# This is this offline reader's temporary-copy resource ceiling, not a native
# revision validity rule. completed_history.MAX_DATABASE_BYTES admits writes
# before insertion (publish lines 151/172); a valid commit can overshoot it.
# One daily private copy holds DB+WAL together and is removed before the next.
MAX_COPY_CARRIER_BYTES = 512 * 1024 * 1024
COPY_CHUNK_BYTES = 64 * 1024
BAR_DECODE_EXPANSION_FACTOR = 32


def carrier_generation(path):
    """SQLite's logical carrier includes the optional WAL, never the SHM cache."""
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('minute_history_path_invalid')
    if not path.exists():
        raise ValueError('minute_history_not_stored')
    result = {'schema':'minute_history_db_wal_carrier_v1'}
    present, total = [], 0
    for key, source in (('database',path),('wal',Path(str(path)+'-wal'))):
        if source.is_symlink():
            raise ValueError('minute_history_path_invalid')
        if not source.exists():
            result[key] = None
            continue
        info = source.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('minute_history_path_invalid')
        total += info.st_size
        present.append((key,source))
    # Admit the combined carrier before any potentially large hash/copy read.
    if total > MAX_COPY_CARRIER_BYTES:
        raise ValueError('minute_history_copy_resource_budget_exceeded')
    for key,source in present:
        result[key] = byte_generation(source)
    if sum(value['size'] for key,value in result.items() if key in {'database','wal'} and value) > MAX_COPY_CARRIER_BYTES:
        raise ValueError('minute_history_copy_resource_budget_exceeded')
    return result


@contextmanager
def _snapshot(root, day):
    """Copy one bounded daily carrier; SQLite never opens the original files.

    Even a read-only WAL connection can create/update its shared-memory index.
    The public reader therefore receives a private DB/WAL copy, once per day.
    """
    datetime.strptime(day, '%Y%m%d')
    path = Path(root)/'runtime/main_minute_history'/day/'completed.sqlite3'
    before = carrier_generation(path)
    with tempfile.TemporaryDirectory(prefix='holding-minute-source-') as directory:
        read_root = Path(directory)
        target = read_root/'runtime/main_minute_history'/day/'completed.sqlite3'
        target.parent.mkdir(parents=True)
        for key, suffix in (('database',''),('wal','-wal')):
            if before[key] is None:
                continue
            original, copied = Path(str(path)+suffix), Path(str(target)+suffix)
            with original.open('rb') as source, copied.open('xb') as output:
                remaining = before[key]['size']
                while True:
                    chunk = source.read(min(COPY_CHUNK_BYTES,remaining+1))
                    if not chunk: break
                    remaining -= len(chunk)
                    if remaining < 0:
                        raise ValueError('minute_history_provenance_changed')
                    output.write(chunk)
            if byte_generation(copied) != before[key]:
                raise ValueError('minute_history_provenance_changed')
        if carrier_generation(path) != before:
            raise ValueError('minute_history_provenance_changed')
        yield dict(read_root=read_root,path=path,generation=before)
        if carrier_generation(path) != before:
            raise ValueError('minute_history_provenance_changed')


def _read_series(snapshot, day, item, *, as_of):
    # Native row count does not bound JSON/deepcopy bytes of a stored bar.
    with Claim(0) as decoded:
        return _read_series_admitted(snapshot, day, item, as_of=as_of, decoded=decoded)


def _read_series_admitted(snapshot, day, item, *, as_of, decoded):
    if type(as_of) not in (int,float) or not math.isfinite(as_of) or as_of <= 0:
        return None, 'minute_history_cutoff_invalid'
    path = snapshot['read_root']/'runtime/main_minute_history'/day/'completed.sqlite3'
    candidate, chart_identity, acquisition_sessions = None, None, set()
    latest_conflict = False
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=.025)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA mmap_size=0')
            db.execute('PRAGMA cache_size=-2048')
            for scope, revision in db.execute('SELECT scope,revision FROM current'):
                row = db.execute('SELECT manifest FROM revisions WHERE hash=? AND scope=?', (revision,scope)).fetchone()
                if row is None: return None, 'minute_history_native_reader_rejected'
                manifest = completed_history._unpack(row[0])
                identity = manifest['identity']
                if completed_history._digest(manifest) != revision or completed_history._digest(identity) != scope:
                    return None, 'minute_history_native_reader_rejected'
                if (identity['item'] == item and identity['date'] == day
                        and identity['schema'] == completed_history.SCHEMA
                        and identity['interval_sec'] == 60
                        and identity['time_basis'] == 'provider_bar_open_kst'
                        and identity['adjustment'] == 'ka10080:upd_stkpc_tp=1'):
                    # A later current revision must not hide a historical
                    # revision that was already available at the requested cutoff.
                    historical = db.execute('SELECT available,hash,manifest FROM revisions WHERE scope=? AND available<=? '
                        'ORDER BY available DESC,hash DESC LIMIT 1',(scope,as_of)).fetchone()
                    if historical is None: continue
                    historical_manifest = completed_history._unpack(historical[2])
                    if (completed_history._digest(historical_manifest) != historical[1]
                            or historical_manifest['identity'] != identity
                            or historical[0] != historical_manifest['first_receipt']['received_at']):
                        return None, 'minute_history_native_reader_rejected'
                    # kiwoom_utils.get_minute_candles_ka10080_with_meta stamps
                    # session_regime at acquisition (:5122); its chart payload
                    # (:5130) has item/interval/adjustment/date, no session filter.
                    # Keep the original identity for the public read; compare
                    # revisions only when every other identity field is exact.
                    comparable = {k:v for k,v in identity.items() if k != 'session'}
                    if chart_identity is not None and comparable != chart_identity:
                        return None, 'minute_history_exact_scope_ambiguous'
                    chart_identity = comparable
                    session = identity.get('session')
                    if not isinstance(session,str) or not session:
                        return None, 'minute_history_native_reader_rejected'
                    acquisition_sessions.add(session)
                    current = (historical[0],historical[1],historical_manifest)
                    same_scope_conflict = False
                    # Every revision at the latest clock participates. A→B→A
                    # corrections can put two equal A rows above the conflicting
                    # B hash; checking only two would conceal that ambiguity.
                    tied = db.execute('SELECT hash,manifest FROM revisions WHERE scope=? AND available=? '
                        'ORDER BY hash DESC LIMIT ?', (scope,current[0],completed_history.MAX_REVISIONS_PER_SCOPE+1))
                    for index,(other_hash,raw) in enumerate(tied):
                        if index >= completed_history.MAX_REVISIONS_PER_SCOPE:
                            return None, 'minute_history_revision_count_invalid'
                        other = completed_history._unpack(raw)
                        if (completed_history._digest(other)!=other_hash or other['identity']!=identity
                                or current[0]!=other['first_receipt']['received_at']):
                            return None, 'minute_history_native_reader_rejected'
                        same_scope_conflict |= other['bar_hashes']!=current[2]['bar_hashes']
                    if candidate is None or current[0]>candidate[0]:
                        latest_conflict = same_scope_conflict
                    elif current[0]==candidate[0]:
                        latest_conflict |= same_scope_conflict or current[2]['bar_hashes']!=candidate[2]['bar_hashes']
                    if candidate is None or current[:2] > candidate[:2]:
                        candidate = current
        if candidate is None:
            return None, 'minute_history_exact_item_or_known_revision_missing'
        if latest_conflict:
            return None, 'minute_history_same_clock_revision_conflict'
        available, revision, manifest = candidate
        count = len(manifest['bar_hashes'])
        if not 0 < count <= completed_history.MAX_ROWS:
            return None, 'minute_history_revision_count_invalid'
        # Admit exact UTF-8 payload bytes before the public reader parses and
        # deep-copies them. SQLite length(TEXT) counts characters, not bytes.
        marks = ','.join('?' for _ in manifest['bar_hashes'])
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True, timeout=.025)) as db:
            db.execute('PRAGMA query_only=ON')
            found, payload_bytes = db.execute(
                'SELECT count(*),coalesce(sum(length(CAST(content AS BLOB))),0) '
                'FROM bars WHERE hash IN ('+marks+')', manifest['bar_hashes']).fetchone()
        if found != count or type(payload_bytes) is not int or payload_bytes <= 0:
            return None, 'minute_history_native_reader_rejected'
        decoded.grow(payload_bytes * BAR_DECODE_EXPANSION_FACTOR)
        value = completed_history.read(snapshot['read_root'], manifest['identity'], now=as_of, limit=count,
                                       include_forming=False, revision=revision)
        if value is None:
            return None, 'minute_history_native_reader_rejected'
        bars, meta = value
        if (meta.get('api_id') != 'ka10080' or meta.get('request_code') != item
                or manifest['identity']['item'] != item or manifest['identity']['date'] != day):
            return None, 'minute_history_provenance_changed'
        normalized = []
        previous = None
        for bar in bars:
            stamp = str(bar['source_timestamp'])
            if len(stamp) != 14:
                return None, 'minute_history_timestamp_invalid'
            at = datetime.strptime(stamp, '%Y%m%d%H%M%S').replace(tzinfo=KST).timestamp()
            low, high = bar['저가'], bar['고가']
            if (type(low) is not int or type(high) is not int or not 0 < low <= high
                    or stamp[:8] > day or stamp[-2:] != '00'
                    or at+60 > available or available > as_of
                    or previous is not None and at <= previous):
                return None, 'minute_history_completed_bar_invalid'
            previous = at
            # Native 430/900-bar revisions deliberately preserve earlier days.
            # Validate that prefix but restrict this diagnostic to its day.
            if stamp[:8] == day:
                normalized.append((at, low, high))
        if not normalized:
            return None, 'minute_history_same_day_completed_bars_missing'
        return dict(bars=normalized, revision_sha256=revision, available_at=available,
                    source_path=str(snapshot['path']), source_generation=snapshot['generation'],
                    request_item=item, source_identity=manifest['identity'],
                    selection_rule='latest_available_same_chart_identity_across_acquisition_sessions',
                    comparable_chart_identity_sha256=digest(chart_identity),
                    eligible_acquisition_sessions=sorted(acquisition_sessions),
                    source_completed_bar_count=len(bars), diagnostic_day_bar_count=len(normalized),
                    selected_bar_payload_bytes=payload_bytes,
                    bar_decode_expansion_factor=BAR_DECODE_EXPANSION_FACTOR,
                    adjustment=manifest['identity']['adjustment'],
                    adjustment_equivalence_to_reference='unproven'), None
    except (OSError, ValueError, TypeError, KeyError, OverflowError, sqlite3.Error, zlib.error) as exc:
        if str(exc) == 'shared_research_budget_partition_resume_required':
            raise
        return None, 'minute_history_source_contract_invalid'


def series(root, day, item, *, as_of):
    """Read one completed revision with original DB/WAL lineage verification."""
    try:
        with Claim(completed_history.MAX_ROWS*4096+2*1024*1024*8), _snapshot(root,day) as snapshot:
            result = _read_series(snapshot,day,item,as_of=as_of)
        return result
    except (OSError,ValueError,TypeError,OverflowError) as exc:
        if str(exc) == 'shared_research_budget_partition_resume_required':
            raise
        issue = str(exc) if str(exc).startswith('minute_history_') else 'minute_history_source_contract_invalid'
        return None, issue


def measure(reference_price, entry_at, bars, *, horizon_minutes, modeled_cost_rate=.0023):
    """Full completed bars inside the horizon only; no intra-bar ordering."""
    if (number(reference_price) is None or reference_price <= 0 or number(entry_at) is None
            or type(horizon_minutes) is not int or horizon_minutes not in HORIZONS
            or number(modeled_cost_rate) is None or not 0 <= modeled_cost_rate < .05):
        raise ValueError('minute_diagnostic_measure_input_invalid')
    first = math.ceil(entry_at/60)*60
    stop = math.floor((entry_at+horizon_minutes*60)/60)*60
    expected = list(range(int(first), int(stop), 60))
    observed = {int(at):(low,high) for at,low,high in bars if first <= at < stop}
    missing = sorted(set(expected)-set(observed))
    result = dict(horizon_minutes=horizon_minutes, expected_completed_bars=len(expected),
        observed_completed_bars=len(observed), missing_completed_bar_count=len(missing),
        leading_unobserved_seconds=first-entry_at, trailing_unobserved_seconds=entry_at+horizon_minutes*60-stop,
        coverage='complete_completed_bar_window' if expected and not missing else 'partial_or_no_completed_bar_window',
        net_high_bound_pct=None, net_low_bound_pct=None, target_in_observed_bars=None,
        stop_in_observed_bars=None, intrabar_order_known=False, actual_profit_verified=False)
    result['horizon_fully_observed'] = bool(expected and not missing
        and first == entry_at and stop == entry_at+horizon_minutes*60)
    if observed:
        high = max(high for low,high in observed.values())
        low = min(low for low,high in observed.values())
        result.update(net_high_bound_pct=100*(high*(1-modeled_cost_rate)/reference_price-1),
            net_low_bound_pct=100*(low*(1-modeled_cost_rate)/reference_price-1))
        result['target_in_observed_bars'] = result['net_high_bound_pct'] >= .4
        result['stop_in_observed_bars'] = result['net_low_bound_pct'] <= -3
    return result


def build(manifest_path, *, input_root, data_root):
    with Claim(0) as retained:
        return _build(manifest_path,input_root=input_root,data_root=data_root,retained=retained)


def _partitions(root, manifest):
    for ref in storage.iter_tree(root,manifest['partitions_ref']):
        path = _source_path(root,ref['path'])
        generation = byte_generation(path)
        with Claim(generation['size']*8):
            part = _sealed(path,ref['artifact_sha256'])
            yield path,generation,part
            del part


def _build(manifest_path, *, input_root, data_root, retained):
    root = Path(input_root).resolve()
    manifest_path = Path(manifest_path).absolute()
    if not manifest_path.is_relative_to(root):
        raise ValueError('minute_diagnostic_manifest_path_invalid')
    manifest_path = _source_path(root,str(manifest_path.relative_to(root)))
    manifest_before = byte_generation(manifest_path)
    code_before = byte_generation(Path(__file__))
    retained.grow(manifest_before['size']*8)
    manifest = _sealed(manifest_path)
    if (manifest.get('schema') != 'main_all_scope_exit_input_manifest_v2'
            or type(manifest.get('as_of')) not in (int,float)
            or not math.isfinite(manifest['as_of']) or manifest['as_of'] <= 0):
        raise ValueError('minute_diagnostic_manifest_contract_invalid')
    if Path(manifest['source_data_root']).resolve() != Path(data_root).resolve():
        raise ValueError('minute_diagnostic_source_root_mismatch')
    groups, rows, populations, partition_generations = defaultdict(list), [], set(), {}
    for partition_path, generation, part in _partitions(root,manifest):
        if str(partition_path) in partition_generations:
            raise ValueError('minute_diagnostic_duplicate_partition')
        partition_generations[str(partition_path)] = generation
        if (part.get('source_date') != manifest['source_date']
                or part.get('target_date',manifest['target_date']) != manifest['target_date']):
            raise ValueError('minute_diagnostic_partition_scope_invalid')
        for position in part['positions']:
            kind = position['evidence_kind']
            identity = position['position_key']
            if not isinstance(identity,str) or not identity or identity in populations:
                raise ValueError('minute_diagnostic_duplicate_identity')
            retained.grow(256)
            populations.add(identity)
            if kind == 'actual_entry_alternative_exit':
                continue
            if kind not in {'actual_completed','enter_pass_opportunity_cf'}:
                raise ValueError('minute_diagnostic_evidence_kind_invalid')
            retained.grow(8192)
            at = number(position.get('entry_at'))
            price = number(position.get('entry_reference_ask'))
            role = position.get('entry_reference_role')
            if kind == 'actual_completed' and not position.get('source_gap'):
                qty, basis = number(position.get('qty')), number(position.get('buy_basis_krw'))
                if qty is not None and qty > 0 and basis is not None and basis > 0:
                    price, role = basis/qty, 'verified_buy_leg_price_path_only'
            row = dict(identity=identity, symbol=position.get('symbol'), evidence_kind=kind,
                       item=position.get('item'), route=position.get('route'), entry_at=at,
                       reference_price=price, reference_role=role, horizons=[],
                       automatic_management_allowed=position.get('automatic_management_allowed'),
                       runtime_effect=False, actual_profit_verified=False)
            if (at is None or at <= 0 or at > manifest['as_of'] or price is None or price <= 0
                    or not isinstance(row['item'],str) or row['item'].split('_',1)[0] != row['symbol']
                    or role not in {'native_entry_ask_price_path_only','verified_buy_leg_price_path_only'}):
                row.update(status='source_gap', reason='native_entry_reference_or_exact_item_missing')
                rows.append(row)
                continue
            day = datetime.fromtimestamp(at,KST).strftime('%Y%m%d')
            groups[(day,row['item'])].append(row)
        del part
    expected = set()
    for identity in storage.iter_tree(root,manifest['population_ids_ref']):
        if not isinstance(identity,str) or identity in expected:
            raise ValueError('minute_diagnostic_population_manifest_invalid')
        expected.add(identity)
    if expected != populations:
        raise ValueError('minute_diagnostic_population_mismatch')
    del expected
    sources, carriers = [], {}
    for day in sorted({day for day,_ in groups}):
        day_rows, day_sources = [], []
        try:
            with Claim(completed_history.MAX_ROWS*4096+2*1024*1024*8), _snapshot(data_root,day) as snapshot:
                for (group_day,item), positions in sorted(groups.items()):
                    if group_day != day: continue
                    source, issue = _read_series(snapshot,day,item,as_of=manifest['as_of'])
                    if source is not None:
                        day_sources.append({k:v for k,v in source.items() if k!='bars'})
                    for row in positions:
                        if issue:
                            row.update(status='source_gap', reason=issue)
                        else:
                            row.update(status='price_path_diagnostic', reason=None,
                                revision_sha256=source['revision_sha256'],
                                adjustment_equivalence_to_reference='unproven',
                                horizons=[measure(row['reference_price'],row['entry_at'],source['bars'],horizon_minutes=n)
                                          for n in HORIZONS])
                        day_rows.append(row)
                    source = None  # Release this group's bars before the next reader.
                carriers[str(snapshot['path'])] = snapshot['generation']
            sources.extend(day_sources)
            rows.extend(day_rows)
        except (OSError,ValueError,TypeError,OverflowError) as exc:
            if str(exc) == 'shared_research_budget_partition_resume_required':
                raise
            issue = str(exc) if str(exc).startswith('minute_history_') else 'minute_history_source_contract_invalid'
            for (group_day,_), positions in groups.items():
                if group_day == day:
                    for row in positions:
                        row.update(status='source_gap',reason=issue,horizons=[])
                        rows.append(row)
    for path,generation in carriers.items():
        if carrier_generation(path) != generation:
            raise ValueError('minute_diagnostic_source_carrier_changed')
    for path,generation in partition_generations.items():
        if byte_generation(path) != generation:
            raise ValueError('minute_diagnostic_partition_changed')
    # Tree readers verify their physical leaf and logical stream hashes. Repeat
    # at final publication so mutable shard files cannot change mid-build.
    for _ in storage.iter_tree(root,manifest['partitions_ref']): pass
    for _ in storage.iter_tree(root,manifest['population_ids_ref']): pass
    if byte_generation(manifest_path) != manifest_before or byte_generation(Path(__file__)) != code_before:
        raise ValueError('minute_diagnostic_manifest_changed')
    counts = Counter((r['evidence_kind'],r['status'],r.get('reason')) for r in rows)
    body = dict(schema=SCHEMA, source_date=manifest['source_date'], target_date=manifest['target_date'],
        input_manifest_generation=manifest_before, population_count=len(rows),
        diagnostic_code_sha256=code_before['sha256'], input_population_count=len(populations),
        excluded_alternative_exit_count=len(populations)-len(rows),
        status_counts=[dict(evidence_kind=k[0],status=k[1],reason=k[2],count=v) for k,v in sorted(counts.items(),key=lambda x:str(x[0]))],
        rows=sorted(rows,key=lambda x:x['identity']), source_revisions=sources,
        copy_resource_contract=dict(max_daily_db_plus_wal_bytes=MAX_COPY_CARRIER_BYTES,
            streaming_chunk_bytes=COPY_CHUNK_BYTES, concurrent_daily_copies=1,
            native_writer_soft_cap_is_read_validity_limit=False),
        model=dict(cost_rate=.0023,target_net_pct=.4,stop_net_pct=-3,
            entry_reference='native_ask_or_verified_buy_leg_no_fill_assumption',
            use='completed_bar_price_bounds_only', executable_ordering=False,
            adjustment_equivalence_to_reference='unproven',
            reference_comparison='unverified_adjustment_price_diagnostic_only'),
        metric_contract=dict(metric_role='funnel_count',decision_authority='report_only',
            window_policy='same_day_verified_completed_bars',sample_floor='diagnostic_no_promotion',
            primary_decision_metric='none',source_quality_gate='native_revision_and_exact_item',
            forbidden_uses=['actual_pnl','fill','trailing_first_crossing','winrate_selection','runtime_apply']),
        actual_profit_verified=False,allowed_runtime_apply=False,runtime_effect=False)
    body['artifact_sha256'] = digest(body)
    return body
