"""Offline reconciliation of Samsung source identities and episode contracts.

Canonical captures and native clusters stay immutable. No live caller, broker,
provider, policy writer or database mutation is part of this consumer.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from src.engine.scalping import samsung_policy_episode_research as P
from src.engine.scalping import auxiliary_source_contract as A
from src.engine.scalping import postclose_entry_validation as V
from src.engine.scalping.ai_decision_trace import _json_bytes
from src.trading.order.owner_custody_registry import OrderOwnerRegistry

CONTRACT = 'samsung_source_opportunity_reconciliation_v1'
EPISODE = 'main_fixed_watch_closed_episode_v1'
FROZEN_PRICE = ('base_recovery:300:5:barrier:0.23:60',
                'absorption_release:300:5:barrier:0.23:60')
FROZEN_MASKS = ('base_recovery:300:5:soft_add',
                'absorption_release:900:5:soft_add')
NATIVE_KEYS = ('watch_origin', 'watch_admission_id', 'watch_generation_id', 'scanner_promotion_id')
LINK_KEYS = ('machine_observation_sha256', 'evaluation_attempt_id', 'parent_decision_trace_id',
             'entry_machine_input_parent_snapshot_id', 'machine_snapshot_id', 'parent_snapshot_id',
             'decision_trace_id', 'original_machine_observation_sha256',
             'recheck_first_machine_observation_sha256')
SELECTOR = dict(stock_code='005930', watch_origin='MAIN_FIXED_WATCH',
                effective_venue='KRX', session_bucket='KRX_REGULAR')
CAPSULE_KEYS = ('entry_pre_ai_source_capsule', 'entry_source_capsule', 'main_fixed_watch_closed_episode')
FIELD_KEYS = (*NATIVE_KEYS, *LINK_KEYS, 'decision_ts', 'decision_trace_id',
    'snapshot_id', 'entry_machine_input_parent_snapshot_id', 'machine_bundle_sha256',
    'zero_base_source_sha256', 'zero_base_route', 'position_id', 'position_cycle_id',
    'owner_type', 'owner_id', 'broker_order_no', 'intent_id', 'side', 'state', 'status',
    'quantity', 'filled_qty', 'remaining_qty', 'residual_qty', 'pending_order_count',
    'late_fill_resolved', 'pending_orders_resolved', 'next_entry_guard_verified')
AUTHORITY = {**P.AUTHORITY, 'consumer_scope': 'offline_samsung_opportunity_contract',
    'source_quality_gate': 'canonical_capture_exact_identity_and_owner_receipt',
    'metric_role': 'source_quality_and_frozen_price_pattern_revalidation',
    'sample_floor': 'census_none_registered_publisher_30_train_10_holdout_native_groups',
    'primary_decision_metric': 'native_group_cost_bound_target_first_win_rate',
    'opportunity_identity_contract': V.OPPORTUNITY_IDENTITY_VERSION,
    'episode_identity_contract': EPISODE, 'live_selector_registered': False}


def write(path, value):
    body = {**{k: v for k, v in value.items() if k != 'content_sha256'}, **AUTHORITY}
    body['content_sha256'] = P.R.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + '\n')


def source_rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line, text in enumerate(handle, 1):
            if text.strip():
                row = json.loads(text)
                if not isinstance(row, dict):
                    raise ValueError('source_row_not_object')
                yield line, row


def normalized_event(row, *, kind, path, seal, line):
    source = row.get('fields') if kind == 'pipeline_events' else row
    source = source if isinstance(source, dict) else {}
    fields = {k: source[k] for k in FIELD_KEYS if k in source
              and isinstance(source[k], (str, int, float, bool, type(None)))}
    for key in CAPSULE_KEYS:
        # Pipeline emitters may serialize the entire capsule as a JSON string.
        # Invalid nonempty values survive to the rejection ledger.
        if key in source:
            fields[key] = source[key]
    return dict(source_kind=kind, stage=row.get('stage') or row.get('decision_stage'),
        emitted_at=row.get('emitted_at') or row.get('decision_ts'), record_id=row.get('record_id'),
        fields=fields, stock_code=row.get('stock_code'),
        path=str(path), physical_sha256=seal, line=line)


def capture_record(row, *, path, seal, line):
    trace = row.get('machine_observation_sha256')
    body = {k: v for k, v in row.items() if k != 'machine_observation_sha256'}
    if not trace or hashlib.sha256(_json_bytes(body)).hexdigest() != trace:
        raise ValueError('canonical_machine_capture_hash_invalid')
    context = row.get('label_context') or {}
    payload = (row.get('source') or {}).get('exact_payload') or {}
    return dict(trace=trace, captured_at=row.get('captured_at'), bundle=row.get('bundle_sha256'),
        source_event_stage=row.get('source_event_stage'), zero_base_source_sha256=row.get('zero_base_source_sha256'),
        context=context, top_native={k: row.get(k) for k in NATIVE_KEYS},
        payload_native={k: payload.get(k) for k in NATIVE_KEYS},
        path=str(path), physical_sha256=seal, line=line)


def prepare(root, output, db_snapshot):
    """Freeze existing archives with the reviewed adapter; no source collection."""
    if (output/'manifest.json').exists():
        raise ValueError('prepared_generation_already_exists')
    adapter_path = Path(__file__).resolve()
    adapter_seal = P.R.P.file_sha(adapter_path)
    _regular, _sessions, projection, _seals, binding = P.load_sources(root)
    wanted = {r['trace'] for r in projection['main']}
    seals, days, artifacts = {}, {}, {}
    for day in P.R.DAYS:
        captures, events, census = [], [], {}
        for kind in ('pipeline_events', 'ai_decision_trace', 'ai_decision_payloads'):
            path = root/'data'/kind/f'{kind}_{day}.jsonl'
            if not path.exists():
                path = path.with_suffix('.jsonl.gz')
            seal = P.R.P.file_sha(path); seals[str(path)] = seal
            stages = Counter(); count = total = 0
            for line, row in source_rows(path):
                total += 1
                context = row.get('label_context') or {}
                code = context.get('stock_code') if kind == 'ai_decision_payloads' else row.get('stock_code')
                if code != '005930':
                    continue
                count += 1; stages[row.get('stage') or row.get('decision_stage') or row.get('schema')] += 1
                if kind == 'ai_decision_payloads':
                    if row.get('schema') == 'mechanistic_entry_observation_v1' and row.get('machine_observation_sha256') in wanted:
                        captures.append(capture_record(row, path=path, seal=seal, line=line))
                else:
                    events.append(normalized_event(row, kind=kind, path=path, seal=seal, line=line))
            P.Q.verify_hashes({str(path): seal})
            census[kind] = dict(total_rows=total, samsung_rows=count, stages=dict(stages))
        path = output/f'{day}.json'
        write(path, dict(day=day, captures=captures, events=events, census=census))
        days[day] = str(path); artifacts[str(path)] = P.R.P.file_sha(path)
        print(day, 'prepared_captures', len(captures), flush=True)
    db = P.R.read(db_snapshot)
    if db.get('read_only') is not True or db.get('query_role') != 'bounded_read_only_snapshot_not_historical_flat_receipt':
        raise ValueError('db_inventory_contract_invalid')
    seals[str(db_snapshot)] = P.R.P.file_sha(db_snapshot)
    seals[str(adapter_path)] = adapter_seal
    P.Q.verify_hashes(seals)
    db_output = output/'db-recommendation.json'; write(db_output, db)
    artifacts[str(db_output)] = P.R.P.file_sha(db_output)
    write(output/'manifest.json', dict(schema=CONTRACT, adapter_sha256=seals[str(Path(__file__).resolve())],
        source_seals=seals, artifact_seals=artifacts, source_day_files=days, current_binding=binding))


def event_index(events):
    """Index exact references once; no nearest-clock or symbol join."""
    index = defaultdict(list)
    for event in events:
        fields = event.get('fields') or {}
        keys = {fields.get(k) for k in LINK_KEYS if V.source_identifier(fields.get(k))}
        capsule = A.unpack(fields.get('entry_pre_ai_source_capsule'))
        identity = capsule.get('identity')
        identity = identity if isinstance(identity, dict) else {}
        keys.update(identity.get(k) for k in LINK_KEYS if V.source_identifier(identity.get(k)))
        for key in keys:
            index[key].append(event)
    return index


def exact_events(row, index):
    found = {}
    for key in (row['decision_trace_id'], row['evaluation_attempt_id'], row['decision_snapshot_id']):
        for event in index.get(key, []):
            found[(event['path'], event['line'])] = event
    return list(found.values())


def native_identity(row, metadata):
    return V.opportunity_identity({
        'source_date': row['source_date'], 'stock_code': row['stock_code'],
        'effective_venue': row['effective_venue'], 'session_bucket': row['session_bucket'],
        **{k: V.source_identifier(metadata.get(k)) for k in NATIVE_KEYS}})


def capture_errors(row, capture):
    context = capture.get('context') or {}
    checks = dict(trace=capture.get('trace') == row['decision_trace_id'],
        clock=capture.get('captured_at') == row['decision_ts'],
        bundle=capture.get('bundle') == row['bundle_sha256'],
        symbol=context.get('stock_code') == row['stock_code'],
        snapshot=context.get('snapshot_id') == row['decision_snapshot_id'],
        attempt=context.get('evaluation_attempt_id') == row['evaluation_attempt_id'],
        venue=str(context.get('effective_venue', '')).upper() == row['effective_venue'],
        session=str(context.get('session_bucket', '')).upper() == row['session_bucket'])
    return ['capture_identity_conflict:' + k for k, valid in checks.items() if not valid]


def capsule_native(row, event):
    """Only an exact, sealed as-of capsule can add missing native metadata."""
    raw = (event.get('fields') or {}).get('entry_pre_ai_source_capsule')
    value = A.unpack(raw)
    if not value:
        return None, ['native_capsule_absent' if raw is None else 'native_capsule_invalid']
    if not isinstance(value.get('identity'), dict):
        return None, ['native_capsule_identity_structure_invalid']
    try:
        errors = A.capsule_errors(value)
    except (ValueError, TypeError, AttributeError):
        return None, ['native_capsule_structure_invalid']
    if value.get('broker_order_forbidden') is not True:
        errors.append('capsule_broker_authority_invalid')
    identity = value.get('identity') or {}
    expected = dict(source_date=row['source_date'], stock_code=row['stock_code'],
        decision_ts=row['decision_ts'], evaluation_attempt_id=row['evaluation_attempt_id'],
        effective_venue=row['effective_venue'], session_bucket=row['session_bucket'],
        machine_observation_sha256=row['decision_trace_id'], machine_bundle_sha256=row['bundle_sha256'])
    for key, val in expected.items():
        if not A.identity_equal(key, identity.get(key), val):
            errors.append('capsule_exact_field_missing_or_conflicting:' + key)
    try:
        if P.R.epoch(value['producer_clock']) < P.R.epoch(row['decision_ts']):
            errors.append('capsule_producer_clock_before_identity')
    except (ValueError, TypeError, KeyError):
        errors.append('capsule_producer_clock_invalid')
    # Later append clocks are permitted only with the exact as-of identity;
    # no timestamp-neighbour search or mutable current state is accepted.
    if errors:
        return None, errors
    try:
        return native_identity(row, identity), []
    except ValueError:
        return None, ['capsule_native_missing']


def reconcile(row, captures, events):
    """Produce a sidecar; never rewrite a canonical capture or its label."""
    original = {k: row.get(k) for k in NATIVE_KEYS}
    try:
        original_native = native_identity(row, original)
    except ValueError:
        original_native = None
    candidates, references, rejected = set(), [], Counter()
    exact_captures = [c for c in captures if c.get('trace') == row['decision_trace_id']]
    for capture in exact_captures:
        errors = capture_errors(row, capture)
        if errors:
            rejected.update(errors)
            continue
        for location in ('context', 'top_native', 'payload_native'):
            meta = capture.get(location) or {}
            try:
                key = native_identity(row, meta)
            except ValueError:
                continue
            candidates.add(key)
            references.append(dict(path=capture['path'], physical_sha256=capture['physical_sha256'],
                line=capture['line'], native_location=location, native_identity=list(key)))
    linked = []
    for event in events:
        fields = event.get('fields') or {}
        identity = A.unpack(fields.get('entry_pre_ai_source_capsule')).get('identity')
        identity = identity if isinstance(identity, dict) else {}
        values = [fields.get(k) for k in LINK_KEYS] + [identity.get(k) for k in LINK_KEYS]
        if not any(key in values for key in (row['decision_trace_id'], row['evaluation_attempt_id'], row['decision_snapshot_id'])):
            continue
        linked.append(dict(stage=event['stage'], path=event['path'], line=event['line'],
                           physical_sha256=event['physical_sha256']))
        key, errors = capsule_native(row, event)
        if key is not None:
            candidates.add(key)
            references.append(dict(path=event['path'], physical_sha256=event['physical_sha256'],
                line=event['line'], native_location='sealed_pre_ai_capsule', native_identity=list(key)))
        elif errors != ['native_capsule_absent']:
            rejected.update(errors)
    if original_native is not None:
        candidates.add(original_native)
    capture_valid = bool(exact_captures) and not any(capture_errors(row, c) for c in exact_captures)
    if not capture_valid or len(candidates) > 1:
        status, selected = 'identity_conflict', None
    elif candidates:
        selected = next(iter(candidates))
        status = 'native_preserved' if selected == original_native else 'native_recovered'
    else:
        selected = None
        status = 'native_not_recorded_in_original_capture_and_exact_receipts'
    return dict(schema=CONTRACT, trace=row['decision_trace_id'],
        source_date=row['source_date'], original_native=list(original_native) if original_native else None,
        resolved_native=list(selected) if selected else None, status=status,
        exact_capture_count=len(exact_captures), references=references,
        linked_events=linked, rejected_reasons=dict(rejected),
        preadmission_probe_receipt_observed=any(e['stage'] == 'zero_base_probe_result' for e in linked),
        original_label_preserved=True, historical_snapshot_used_as_flat_proof=False)


def episode_errors(proof, *, source_seals, expected_native, source_records):
    """A closed episode remains correlated with its original native cluster."""
    errors = []
    if not isinstance(proof, dict):
        return ['episode_not_object']
    body = {k: v for k, v in proof.items() if k != 'sha256'}
    try:
        if proof.get('schema') != EPISODE or proof.get('sha256') != P.R.digest(body):
            return ['episode_hash_or_contract_invalid']
    except (ValueError, TypeError):
        return ['episode_hash_or_contract_invalid']
    if proof.get('native_cluster') != list(expected_native):
        errors.append('episode_native_cluster_conflict')
    if proof.get('owner_type') != 'main_scalping' or proof.get('evidence_class') != 'actual_owner_receipts':
        errors.append('episode_owner_or_evidence_class_invalid')
    required = ('entry_at', 'terminal_at', 'flat_at', 'rearmed_at')
    try:
        stamps = [P.R.epoch(proof[k]) for k in required]
        if stamps != sorted(stamps) or stamps[0] == stamps[-1]:
            errors.append('episode_clock_order_invalid')
    except (KeyError, ValueError, TypeError):
        errors.append('episode_clock_missing_or_invalid')
    for key in ('late_fill_resolved', 'pending_orders_resolved', 'next_entry_guard_verified'):
        if proof.get(key) is not True:
            errors.append('episode_required_proof_missing:' + key)
    for key in ('residual_qty', 'pending_order_count'):
        if type(proof.get(key)) is not int or proof[key] != 0:
            errors.append('episode_not_flat:' + key)
    if proof.get('kind') not in ('full_position_exit', 'confirmed_unfilled_cancel', 'confirmed_no_submit'):
        errors.append('episode_terminal_kind_invalid')
    refs = proof.get('source_references')
    if not isinstance(refs, dict):
        refs = {}; errors.append('episode_reference_structure_invalid')
    for role in ('entry', 'terminal', 'flat', 'rearmed'):
        ref = refs.get(role) if isinstance(refs.get(role), dict) else {}
        path_valid = isinstance(ref.get('path'), str)
        if (not path_valid or source_seals.get(ref.get('path')) != ref.get('physical_sha256')
                or not ref.get('physical_sha256') or type(ref.get('line')) is not int or ref['line'] < 1):
            errors.append('episode_source_reference_invalid:' + role)
        fact = (source_records.get((ref.get('path'), ref.get('line'))) or {}
                if isinstance(ref.get('path'), str) and type(ref.get('line')) is int else {})
        if (not fact or fact.get('physical_sha256') != ref.get('physical_sha256')
                or fact.get('owner_type') != 'main_scalping'
                or not proof.get('position_id') or fact.get('position_id') != proof.get('position_id')
                or fact.get('native_cluster') != list(expected_native)
                or fact.get('evidence_class') != 'actual_owner_receipts'
                or fact.get('role') != role or fact.get('observed_at') != proof.get(role + '_at')):
            # A filename/hash is not evidence that its referenced row proves
            # this Main position, native cluster, terminal or custody state.
            errors.append('episode_source_fact_missing_or_conflicting:' + role)
        if role == 'flat' and any(fact.get(k) != 0 or type(fact.get(k)) is not int
                                  for k in ('residual_qty', 'pending_order_count')):
            errors.append('episode_flat_source_not_zero')
        if role == 'rearmed' and any(fact.get(k) is not True for k in (
                'late_fill_resolved', 'pending_orders_resolved', 'next_entry_guard_verified')):
            errors.append('episode_rearm_source_unverified')
    return errors


def child_contract(parent_sha256, target_date):
    return dict(schema='samsung_fixed_watch_research_selector_v1', parent_sha256=parent_sha256,
        target_date=target_date, selector=dict(SELECTOR),
        expiry=target_date + 'T15:30:00+09:00', outside_scope='parent',
        unsupported_or_missing='parent', runtime_registered=False,
        live_promotion_forbidden=True, selected_price_rules=list(FROZEN_PRICE))


def child_matches(contract, row, *, parent_sha256, now):
    if (contract.get('schema') != 'samsung_fixed_watch_research_selector_v1'
            or contract.get('parent_sha256') != parent_sha256
            or contract.get('outside_scope') != 'parent'
            or contract.get('unsupported_or_missing') != 'parent'
            or contract.get('runtime_registered') is not False
            or contract.get('live_promotion_forbidden') is not True):
        return False
    if contract.get('selector') != SELECTOR or contract.get('selected_price_rules') != list(FROZEN_PRICE):
        return False
    try:
        stamp = datetime.fromisoformat(now)
        if stamp.tzinfo is None or stamp.astimezone(V.KST).date().isoformat() != contract['target_date']:
            return False
        if contract['expiry'] != contract['target_date'] + 'T15:30:00+09:00' or stamp >= datetime.fromisoformat(contract['expiry']):
            return False
    except (ValueError, TypeError, KeyError):
        return False
    if row.get('source_date') != contract['target_date']:
        return False
    try:
        native_identity(row, row)
    except (ValueError, TypeError, KeyError):
        return False
    return all(row.get(k) == v for k, v in contract['selector'].items())


def group_metric(rows, selected_ids):
    """Use the registered native group estimand, with unknown counts separate."""
    accepted, unknown, missing = [], 0, 0
    for row in rows:
        if row['trace'] not in selected_ids:
            continue
        if row['native'] is None:
            missing += 1
        elif row['label']['binary'] is None:
            unknown += 1
        else:
            accepted.append(dict(opportunity_id=P.R.digest(row['native']), source_date=row['day'],
                win=row['label']['binary'], net_path_pct=row['label'].get('net')))
    metric = P.R.P.calibration._winrate_opportunity_metrics(accepted)
    return dict(metric, unknown_selected_attempt_count=unknown, native_missing_selected_attempt_count=missing)


def native_comparison(rows, masks, *, train_dates=None, scope='all_captured_samsung_origins'):
    train_dates = list(P.R.DAYS[:2]) if train_dates is None else train_dates
    train = [r for r in rows if r['day'] in train_dates]
    held = [r for r in rows if r['day'] == P.R.DAYS[2]]
    old = {r['trace'] for r in rows if r['parent'] == 'ENTER_NOW'}
    results = []
    for key in FROZEN_MASKS:
        source = dict(selection_objective_version='winrate_native_improvement_without_winner_retention_v3',
            opportunity_identity_contract=V.OPPORTUNITY_IDENTITY_VERSION, target_date='2026-10-02',
            train_dates=train_dates, holdout_dates=[P.R.DAYS[2]], consumed_holdout_dates=[],
            baseline=dict(train=group_metric(train, old), holdout=group_metric(held, old)),
            candidate=dict(train=group_metric(train, masks[key]), holdout=group_metric(held, masks[key])))
        results.append(dict(key=key, comparison_scope=scope, publisher_metric_source=source,
            registered_successor_hurdles_pass=P.M._winrate_successor_hurdles_valid(source),
            selection_without_new_retention_veto=True, pristine_holdout=False,
            runtime_selector_registered=False, official_policy_candidate=None))
    return results


def fixed_watch_rows(rows):
    return [r for r in rows if r['native'] is not None and len(r['native']) == 7
            and r['native'][1:5] == ['005930', 'KRX', 'KRX_REGULAR', 'MAIN_FIXED_WATCH']]


def owner_inventory(path, records):
    """Validate the complete journal chain; return only bounded redacted rows."""
    records[str(path)] = P.R.P.file_sha(path)
    journal = OrderOwnerRegistry(path=path)._read_locked()
    P.Q.verify_hashes({str(path): records[str(path)]})
    selected = []
    allowed = ('event', 'event_hash', 'event_id', 'observed_at_kst', 'order_date', 'symbol',
               'owner_type', 'owner_id', 'position_id', 'intent_id', 'side', 'state', 'route',
               'quantity', 'filled_qty', 'fill_amount', 'broker_order_no', 'reason')
    physical_lines = [line for line, _row in source_rows(path)]
    if len(physical_lines) != len(journal):
        raise ValueError('owner_journal_physical_line_count_conflict')
    for line, row in zip(physical_lines, journal):
        if row.get('symbol') == '005930' and row.get('order_date') in P.R.DAYS:
            selected.append({**{k: row.get(k) for k in allowed}, 'line': line,
                'account_identity_sha256': P.R.digest(row.get('account_key')),
                'path': str(path), 'physical_sha256': records[str(path)]})
    return dict(chain_valid=True, all_journal_events=len(journal), rows=selected,
                historical_flat_proven=False)


def run(root, intake, output):
    if (output/'result.json').exists():
        raise ValueError('replay_generation_already_exists')
    regular, _sessions, projection, seals, binding = P.load_sources(root)
    primary_path = root/'tmp/samsung-policy-episode-research-20261004/frozen-strict/result.json'
    primary = P.R.read(primary_path)
    seals[str(primary_path)] = P.R.P.file_sha(primary_path)
    manifest_path = intake/'manifest.json'
    manifest = P.R.read(manifest_path)
    if manifest.get('schema') != CONTRACT or manifest.get('adapter_sha256') != P.R.P.file_sha(Path(__file__).resolve()):
        raise ValueError('intake_adapter_generation_conflict')
    P.Q.verify_hashes(manifest['source_seals'])
    P.Q.verify_hashes(manifest['artifact_seals'])
    if manifest.get('current_binding') != binding:
        raise ValueError('intake_policy_binding_conflict')
    seals.update(manifest['source_seals'])
    seals[str(manifest_path)] = P.R.P.file_sha(manifest_path)
    for p in (Path(__file__).resolve(), root/'src/tests/test_samsung_opportunity_contract_research.py',
              root/'docs/proposals/samsung-opportunity-contract-reconciliation-plan-2026-10-04.md',
              root/'src/engine/scalping/auxiliary_source_contract.py',
              root/'src/engine/scalping/ai_decision_trace.py',
              root/'src/engine/scalping/postclose_entry_validation.py',
              root/'src/trading/order/owner_custody_registry.py'):
        seals[str(p)] = P.R.P.file_sha(p)
    corrected = deepcopy(projection['main'])
    by_trace = {r['trace']: r for r in corrected}
    lineage, census, event_census = [], {}, {}
    episode_candidates, source_records = [], {}
    for day in P.R.DAYS:
        p = Path(manifest['source_day_files'][day]); seals[str(p)] = P.R.P.file_sha(p)
        source = P.R.read(p)
        if source['day'] != day:
            raise ValueError('intake_source_date_conflict')
        index = event_index(source['events'])
        raw_path = root/f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
        for row in P.R.P.stream_array(raw_path):
            if row.get('decision_trace_id') not in by_trace:
                continue
            result = reconcile(row, source['captures'], exact_events(row, index))
            lineage.append(result)
            by_trace[row['decision_trace_id']]['native'] = result['resolved_native']
        census[day] = dict(Counter(r['status'] for r in lineage if r['source_date'] == day))
        event_census[day] = source['census']
        # Only an explicit producer-issued proof is considered for this new
        # contract. A terminal label or current DB row cannot create one.
        for event in source['events']:
            proof = A.unpack(event['fields'].get('main_fixed_watch_closed_episode'))
            if proof:
                episode_candidates.append(proof)
            # No generic pipeline status is implicitly elevated to a custody
            # receipt. A registered native owner producer would be needed for
            # role facts; none is registered in this offline consumer.
        print(day, 'lineage', census[day], flush=True)
    owner = owner_inventory(root/'data/runtime/order_owner_registry.jsonl', seals)
    if len(lineage) != len(corrected) or len({r['trace'] for r in lineage}) != len(corrected):
        raise ValueError('lineage_capture_missing_or_duplicate')
    db_path = intake/'db-recommendation.json'
    seals[str(db_path)] = P.R.P.file_sha(db_path)
    db = P.R.read(db_path)
    if db.get('read_only') is not True:
        raise ValueError('db_snapshot_not_read_only')
    db_census = dict(rows=len(db['rows']), positive_buy_qty=sum(r['buy_qty'] > 0 for r in db['rows']),
        rows_with_buy_time=sum(r['buy_time'] is not None for r in db['rows']),
        role='current_db_inventory_not_historical_native_or_flat_proof')
    episodes = []
    native_set = {tuple(r['native']) for r in corrected if r['native'] is not None}
    for proof in episode_candidates:
        cluster = proof.get('native_cluster')
        key = tuple(cluster) if isinstance(cluster, list) and all(isinstance(x, str) for x in cluster) else ()
        errors = episode_errors(proof, source_seals=seals, expected_native=key, source_records=source_records)
        if key not in native_set:
            errors.append('episode_unknown_native_cluster')
        episodes.append(dict(proof=proof, errors=errors, usable=not errors))
    masks = {key: set() for key in FROZEN_MASKS}
    prices = []
    for day in P.R.DAYS:
        prepared = P.R.read(Path(regular['files'][day]['path']))
        cache = P.E.read_cache(Path(prepared['cache']['path'])); ctx = P.C.campaign_context(cache)
        frames = prepared['frames']; day_rows = [r for r in corrected if r['day'] == day]
        needed = {':'.join(k.split(':')[:3]) for k in (*FROZEN_PRICE, *FROZEN_MASKS)}
        signals = {d['id']: P.state_signals(ctx, frames, d, regular['fee_profiles'][day]['cost_pct'])
                   for d in P.definitions() if d['id'] in needed}
        for key in FROZEN_MASKS:
            def_id, mode = key.rsplit(':', 1)
            ids, _ = P.captured_mask(day_rows, frames, ctx, signals[def_id], mode)
            masks[key].update(ids)
        for key in FROZEN_PRICE:
            definition, model, cost, cd = key.rsplit(':', 3)
            result = P.replay(signals[definition], lambda f: P.exit_label(ctx, f, model, float(cost)), cooldown=int(cd))
            if result['metric'] != primary['daily']['SOR_REGULAR|'+day][key]['metric']:
                raise ValueError('frozen_price_replay_changed')
            prices.append(dict(day=day, key=key, **result, identity_repair_changes_price_metric=False,
                actual_main_episode_support=sum(e['usable'] and e['proof']['native_cluster'][0] == day for e in episodes),
                actual_order_authority=False))
    comparison = native_comparison(corrected, masks)
    fixed = fixed_watch_rows(corrected)
    fixed_train_dates = sorted({r['day'] for r in fixed if r['day'] in P.R.DAYS[:2]})
    fixed_comparison = native_comparison(fixed, masks, train_dates=fixed_train_dates,
                                        scope='005930_MAIN_FIXED_WATCH_KRX_REGULAR')
    selector = child_contract(binding['parent_sha256'], '2026-10-06')
    P.Q.verify_hashes(seals); P.Q.verify_hashes(primary['preserved'])
    write(output/'lineage.json', dict(rows=lineage, census=census))
    write(output/'price-revalidation.json', dict(rows=prices))
    write(output/'result.json', dict(status='reconciled_and_revalidated_no_qualified_policy',
        source_seals=seals, preserved=primary['preserved'], binding=binding,
        lineage_census=census, source_event_census=event_census,
        resolved_native_groups={d: len({tuple(r['native']) for r in corrected if r['day']==d and r['native'] is not None}) for d in P.R.DAYS},
        publisher_feasibility=P.promotion_feasibility(corrected), native_comparisons=comparison,
        fixed_watch_publisher_feasibility=P.promotion_feasibility(fixed),
        fixed_watch_native_comparisons=fixed_comparison,
        selector_contract=selector, episode_candidates=episodes,
        usable_episode_count=sum(r['usable'] for r in episodes), owner_inventory=owner, db_inventory=db_census,
        native_episode_producer_registered=False, independent_native_support_unit='original_native_cluster',
        frozen_price_replay_metrics_unchanged=True, frozen_rules=list(FROZEN_PRICE),
        formal_generator_execution_claimed=False, official_policy_candidate=None,
        stop_reason='historical_native_support_and_comparable_holdout_below_publisher_contract'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--intake', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--db-snapshot', type=Path)
    args = parser.parse_args(argv)
    if args.prepare:
        if args.db_snapshot is None:
            parser.error('--prepare requires --db-snapshot')
        prepare(args.root.resolve(), args.output.resolve(), args.db_snapshot.resolve())
    else:
        if args.intake is None:
            parser.error('--intake is required for replay')
        run(args.root.resolve(), args.intake.resolve(), args.output.resolve())


if __name__ == '__main__':
    main()
