"""Bounded source/feature spool for isolated Main exit research.

This report-producer adapter owns no runtime loader or execution authority.
Each original event remains source-bound. Numeric candidate/parent changes do
not invalidate the M1 projection; independent source-byte checks still run.
"""
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number, _atomic
from src.engine.scalping.trailing_mechanical_policy import classifier_hash
from src.engine.scalping.trailing_mechanical_strength import classify_ws_history, StrengthDecision
from src.engine.scalping.trailing_threshold_policy import market_type_at
from src.engine.scalping.universal_trailing_replay import (
    PreparedPath, PreparedVariants, MAX_EVENTS, expand_ws,
)
from src.trading.market.session_contract import resolve_market_session

SCHEMA = 'main_trailing_source_feature_projection_v1'
PIECE_BYTES = 256 * 1024
MAX_PIECES = 4096
MAX_TEMP_BYTES = 64 * 1024 * 1024


def source_contract():
    root = Path(__file__).resolve().parents[1]
    names = ('automation/main_trailing_path_projection.py', 'scalping/universal_trailing_replay.py',
             'scalping/trailing_mechanical_strength.py', 'scalping/trailing_mechanical_policy.py',
             'scalping/trailing_threshold_policy.py', '../trading/market/session_contract.py')
    return digest({name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names})


def read_sealed(path, expected=None):
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('trailing_projection_path_invalid')
    before = path.stat()
    if before.st_size > 4 * 1024 * 1024:
        raise ValueError('trailing_projection_partition_resume_required')
    with Claim(before.st_size * 8):
        raw = path.read_bytes()
        if len(raw) != before.st_size or source_stat(path.stat()) != source_stat(before):
            raise ValueError('trailing_projection_changed_during_read')
        value = json.loads(raw)
        if (value.get('artifact_sha256') != digest({k:v for k,v in value.items() if k!='artifact_sha256'})
                or expected is not None and value['artifact_sha256'] != expected):
            raise ValueError('trailing_projection_generation_invalid')
        yield value


def _relative(root, name):
    if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('trailing_projection_relative_path_invalid')
    path = root/name
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('trailing_projection_relative_path_invalid')
    return path


class EventSequence:
    def __init__(self, pairs, count):
        self.pairs, self.count = pairs, count

    def __len__(self):
        return self.count

    def __iter__(self):
        for event, _ in self.pairs():
            yield event


def prepared(root, description):
    def pairs():
        total = 0
        for reference in description['pieces']:
            path = _relative(root, reference['path'])
            for piece in read_sealed(path, reference['artifact_sha256']):
                if piece.get('schema') != SCHEMA or piece.get('classifier_sha256') != description['classifier_sha256']:
                    raise ValueError('trailing_projection_classifier_invalid')
                for row in piece['records']:
                    event, feature = row
                    market, permission, strength = feature
                    total += 1
                    yield event, (market, SimpleNamespace(**permission) if permission else None,
                                  StrengthDecision(**{**strength, 'new_observations':tuple(strength['new_observations'])})
                                  if strength else None)
        if total != description['event_count']:
            raise ValueError('trailing_projection_event_census_invalid')
    return PreparedPath(EventSequence(pairs, description['event_count']), (), description['classifier_sha256'],
                        pairs, description['observation_end_at'])


def _events(source, root, generations, as_of, counters, source_date):
    if isinstance(source, list):
        blocks = [source]
    elif isinstance(source, dict) and set(source) == {'segments','event_count'}:
        if (not isinstance(source['segments'],list) or len(source['segments']) > MAX_PIECES
                or type(source['event_count']) is not int or not 0 <= source['event_count'] <= MAX_EVENTS):
            raise ValueError('trailing_path_segment_manifest_invalid')
        def segmented():
            count, seen = 0, set()
            for ref in source['segments']:
                path = _relative(root,ref['path'])
                if str(path) in seen:
                    raise ValueError('trailing_path_segment_duplicate')
                seen.add(str(path))
                before = byte_generation(path)
                for piece in read_sealed(path,ref['artifact_sha256']):
                    if piece.get('source_date') != source_date or not isinstance(piece.get('events'),list):
                        raise ValueError('trailing_path_segment_contract_invalid')
                    count += len(piece['events'])
                    yield piece['events']
                if byte_generation(path) != before:
                    raise ValueError('trailing_path_segment_changed')
                generations[str(path)] = before
            if count != source['event_count']:
                raise ValueError('trailing_path_segment_census_invalid')
        blocks = segmented()
    else:
        raise ValueError('trailing_path_contract_invalid')
    retained = 0
    for events in blocks:
        for event in events:
            if not isinstance(event,dict):
                raise ValueError('trailing_path_event_invalid')
            if number(event.get('known_at')) is not None and number(event['known_at']) > as_of:
                counters['as_of_future_events_excluded'] += 1
                continue
            retained += 1
            if retained > MAX_EVENTS:
                raise ValueError('trailing_path_event_budget_invalid')
            yield event


def _spool(events, config, out, *, used_bytes):
    state, records, size, references, count, end = {}, [], 0, [], 0, 0
    sha = classifier_hash(config)
    def flush():
        nonlocal records, size
        if not records:
            return
        piece = {'schema':SCHEMA,'classifier_sha256':sha,'records':records}
        piece['artifact_sha256'] = digest(piece)
        name = 'pieces/'+piece['artifact_sha256']+'.json'
        encoded_size = len(json.dumps(piece,ensure_ascii=True).encode())
        # Count every retained piece once, including reuse within this job.
        if sum(used_bytes.values()) - used_bytes.get(name,0) + encoded_size > MAX_TEMP_BYTES:
            raise ValueError('trailing_projection_temp_partition_resume_required')
        used_bytes[name] = encoded_size
        _atomic(out/name,piece)
        references.append({'path':name,'artifact_sha256':piece['artifact_sha256']})
        if len(references)>MAX_PIECES:
            raise ValueError('trailing_projection_piece_budget_invalid')
        records, size = [], 0
    # This conservative claim bounds Python expansion of the output buffer;
    # source segment claims stay held independently until their iterator exits.
    with Claim(PIECE_BYTES*8):
        for event in events:
            known = number(event.get('known_at'))
            market = market_type_at(known) if known is not None else None
            permission = resolve_market_session(datetime.fromtimestamp(known,ZoneInfo('Asia/Seoul'))) if known is not None else None
            strength, age = None, number(event.get('max_quote_age_sec'))
            if event.get('kind')=='QUOTE' and known is not None and age is not None and 0<age<=.7 and event.get('ws_data') is not None:
                try:
                    strength,state = classify_ws_history(expand_ws(event['ws_data']),state,now_ms=int(known*1000),
                        max_quote_age_ms=int(age*1000),market=market,config=(config or {}).get(market))
                except (ValueError,TypeError,KeyError,AttributeError,OverflowError):
                    strength = None
            feature = [market,{'exit_allowed_by_clock':permission.exit_allowed_by_clock,'blocker':permission.blocker}
                       if permission else None,asdict(strength) if strength else None]
            row = [event,feature]
            row_size = len(json.dumps(row,allow_nan=False).encode())
            if row_size>64*1024:
                raise ValueError('trailing_projection_event_partition_resume_required')
            if size+row_size>PIECE_BYTES:
                flush()
            records.append(row);size+=row_size;count+=1;end=max(end,known or 0)
        flush()
    return {'pieces':references,'event_count':count,'classifier_sha256':sha,'observation_end_at':end}


def load_or_build(path, *, root, out, expected, as_of, source_date, configs, counters, resume, used_bytes):
    """One source projection, keyed without numeric parent/candidate or costs."""
    source = byte_generation(path)
    key = digest([source,expected,as_of,source_date,source_contract()])
    index_path = out/(key+'.json')
    index = None
    if resume and index_path.is_file():
        try:
            for candidate in read_sealed(index_path):
                if (candidate.get('schema')!=SCHEMA or candidate.get('source_date')!=source_date
                        or candidate.get('source_generation')!=source or candidate.get('key')!=key):
                    raise ValueError('trailing_source_projection_key_invalid')
                for name,generation in candidate['sources'].items():
                    path_source=Path(name)
                    if not path_source.is_absolute() or not path_source.resolve().is_relative_to(root.resolve()):
                        raise ValueError('trailing_source_projection_path_invalid')
                    if byte_generation(path_source)!=generation:
                        raise ValueError('trailing_source_projection_changed')
                # Fail on missing/corrupt pieces before using a cached outcome.
                for variants in candidate['paths'].values():
                    for description in variants.values():
                        for ref in description['pieces']:
                            piece_path = _relative(out,ref['path'])
                            if ref['path'] not in used_bytes:
                                used_bytes[ref['path']] = piece_path.stat().st_size
                            if sum(used_bytes.values()) > MAX_TEMP_BYTES:
                                raise ValueError('trailing_projection_temp_partition_resume_required')
                            for _ in read_sealed(piece_path,ref['artifact_sha256']):
                                pass
                index = candidate
            counters['source_feature_projection_reused'] += 1
        except (OSError,ValueError,TypeError,KeyError,AttributeError):
            counters['source_feature_projection_invalid_rebuilt'] += 1
    if index is None:
        # Retain the source decode claim until every feature piece is sealed.
        for payload in read_sealed(path):
            if digest(payload)!=expected or payload.get('source_date')!=source_date or len(payload['positions'])>500:
                raise ValueError('trailing_source_projection_input_invalid')
            paths, sources = {}, {str(path):source}
            for identity,events in payload['paths'].items():
                variants = {}
                try:
                    for config in configs:
                        variants[classifier_hash(config)] = _spool(_events(events,root,sources,as_of,counters,source_date),config,out,used_bytes=used_bytes)
                except ValueError as exc:
                    if str(exc) not in {'trailing_path_event_invalid','trailing_path_contract_invalid'}:
                        raise
                    # Identity is intact; preserve its source-gap result while
                    # other healthy positions in this partition continue.
                    variants = {}
                    counters['identified_path_invalid'] += 1
                paths[identity] = variants
            index = {'schema':SCHEMA,'source_date':source_date,'key':key,'source_generation':source,'sources':sources,
                     'positions':payload['positions'],'cost_generations':payload.get('cost_generations'),'paths':paths}
        if byte_generation(path)!=source:
            raise ValueError('trailing_source_projection_input_changed')
        counters['decoded_partitions'] += 1
    else:
        for variants in index['paths'].values():
            if not variants:
                continue
            original = prepared(out,next(iter(variants.values())))
            for config in configs:
                sha = classifier_hash(config)
                if sha not in variants:
                    variants[sha] = _spool(iter(original.events),config,out,used_bytes=used_bytes)
                    counters['new_classifier_from_source_projection'] += 1
    index.pop('artifact_sha256',None);index['artifact_sha256'] = digest(index)
    if len(json.dumps(index).encode())>4*1024*1024:
        raise ValueError('trailing_source_projection_index_partition_resume_required')
    claim = Claim(len(json.dumps(index).encode())*8)
    try:
        _atomic(index_path,index)
    except Exception:
        claim.close()
        raise
    return index, {identity:PreparedVariants({sha:prepared(out,description) for sha,description in variants.items()})
                   for identity,variants in index['paths'].items()}, claim
