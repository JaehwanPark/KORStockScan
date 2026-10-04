from copy import deepcopy
import hashlib
import json

import pytest

from src.engine.scalping import samsung_opportunity_contract_research as S


def row(**extra):
    return dict(source_date='2026-09-29', stock_code='005930', effective_venue='KRX',
        session_bucket='KRX_REGULAR', decision_trace_id='capture-hash',
        decision_ts='2026-09-29T09:05:00+09:00', bundle_sha256='bundle',
        evaluation_attempt_id='machine-attempt', decision_snapshot_id='machine-snapshot', **extra)


def native():
    return dict(watch_origin='MAIN_FIXED_WATCH', watch_admission_id='admission', watch_generation_id='generation')


def capture(r, metadata=None):
    return dict(trace=r['decision_trace_id'], captured_at=r['decision_ts'], bundle=r['bundle_sha256'],
        context=dict(stock_code=r['stock_code'], effective_venue=r['effective_venue'],
            session_bucket=r['session_bucket'], snapshot_id=r['decision_snapshot_id'],
            evaluation_attempt_id=r['evaluation_attempt_id']), top_native=metadata or {},
        payload_native={}, path='payload.jsonl', physical_sha256='physical', line=5)


def event(r, metadata=None):
    identity = dict(source_date=r['source_date'], stock_code=r['stock_code'], decision_ts=r['decision_ts'],
        effective_venue=r['effective_venue'], session_bucket=r['session_bucket'],
        evaluation_attempt_id=r['evaluation_attempt_id'], machine_observation_sha256=r['decision_trace_id'],
        machine_bundle_sha256=r['bundle_sha256'], **(metadata or native()))
    capsule = S.A.capsule(identity, producer='test_exact_pre_ai', clock=r['decision_ts'])
    return dict(stage='ai_confirmed', fields=dict(machine_observation_sha256=r['decision_trace_id'],
        evaluation_attempt_id=r['evaluation_attempt_id'], entry_pre_ai_source_capsule=capsule),
        path='pipeline.jsonl', physical_sha256='physical', line=8)


def reseal(c):
    c['sha256'] = S.A.digest({k: v for k, v in c.items() if k != 'sha256'})


@pytest.mark.parametrize('location', ['context', 'top_native', 'payload_native'])
def test_exact_nested_native_is_recovered_without_rewriting_capture(location):
    r = row(); c = capture(r); c[location].update(native()); before = deepcopy(c)
    result = S.reconcile(r, [c], [])
    assert result['status'] == 'native_recovered'
    assert result['resolved_native'] == list(S.native_identity(r, native()))
    assert c == before and r.get('watch_admission_id') is None


@pytest.mark.parametrize('key', ['trace', 'captured_at', 'bundle'])
def test_capture_identity_conflict_cannot_supply_native(key):
    r = row(); c = capture(r, native()); c[key] = 'different'
    result = S.reconcile(r, [c], [])
    assert result['resolved_native'] is None
    assert result['status'] == 'identity_conflict'


@pytest.mark.parametrize('key', ['stock_code', 'snapshot_id', 'evaluation_attempt_id', 'effective_venue', 'session_bucket'])
def test_nested_capture_identity_conflict_cannot_supply_native(key):
    r = row(); c = capture(r, native()); c['context'][key] = 'different'
    assert S.reconcile(r, [c], [])['resolved_native'] is None


def test_no_native_id_remains_unknown_even_if_current_watch_exists():
    r = row(); e = event(r); e['fields'].pop('entry_pre_ai_source_capsule')
    e['fields'].update(native())
    result = S.reconcile(r, [capture(r)], [e])
    assert result['resolved_native'] is None
    assert result['status'] == 'native_not_recorded_in_original_capture_and_exact_receipts'


def test_serialized_exact_capsule_is_indexed_and_reconciled():
    r = row(); e = event(r); e['fields'] = {'entry_pre_ai_source_capsule': json.dumps(e['fields']['entry_pre_ai_source_capsule'])}
    indexed = S.exact_events(r, S.event_index([e]))
    assert indexed == [e] and S.reconcile(r, [capture(r)], indexed)['status'] == 'native_recovered'


@pytest.mark.parametrize('key', ['source_date', 'stock_code', 'decision_ts', 'evaluation_attempt_id',
    'effective_venue', 'session_bucket', 'machine_observation_sha256', 'machine_bundle_sha256'])
def test_wrong_or_future_asof_capsule_is_rejected(key):
    r = row(); e = event(r); c = e['fields']['entry_pre_ai_source_capsule']
    c['identity'][key] = 'wrong'; reseal(c)
    key_, errors = S.capsule_native(r, e)
    assert key_ is None and errors


def test_later_append_retains_exact_asof_identity_but_missing_clock_is_rejected():
    r = row(); e = event(r); c = e['fields']['entry_pre_ai_source_capsule']
    c['producer_clock'] = '2026-09-29T09:06:00+09:00'; reseal(c)
    assert S.capsule_native(r, e)[0] == S.native_identity(r, native())
    c['producer_clock'] = '2026-09-29T09:04:00+09:00'; reseal(c)
    assert S.capsule_native(r, e)[0] is None


def test_conflicting_native_receipts_do_not_choose_one():
    r = row(); c = capture(r, native()); e = event(r, dict(native(), watch_generation_id='other'))
    assert S.reconcile(r, [c], [e])['status'] == 'identity_conflict'


def test_post_ai_snapshot_is_not_used_as_machine_snapshot():
    r = row(); e = event(r); e['fields'].update(ai_trace_snapshot_id='post-ai-snapshot',
        entry_machine_input_parent_snapshot_id=r['decision_snapshot_id'])
    assert S.reconcile(r, [capture(r)], [e])['status'] == 'native_recovered'


def test_original_machine_snapshot_links_even_when_post_ai_attempt_differs():
    r = row(); e = event(r)
    e['fields'] = dict(evaluation_attempt_id='post-ai-attempt',
        entry_machine_input_parent_snapshot_id=r['decision_snapshot_id'],
        snapshot_id='post-ai-snapshot', **native())
    indexed = S.exact_events(r, S.event_index([e]))
    result = S.reconcile(r, [capture(r)], indexed)
    assert len(result['linked_events']) == 1 and result['resolved_native'] is None


@pytest.mark.parametrize('key', ['original_machine_observation_sha256', 'recheck_first_machine_observation_sha256'])
def test_first_recheck_machine_hash_is_kept_and_linked_without_creating_admission(key):
    r = row()
    raw = dict(stock_code='005930', stage='zero_base_probe_result', fields={key: r['decision_trace_id']})
    e = S.normalized_event(raw, kind='pipeline_events', path='pipeline.gz', seal='hash', line=42)
    result = S.reconcile(r, [capture(r)], S.exact_events(r, S.event_index([e])))
    assert result['preadmission_probe_receipt_observed'] and result['resolved_native'] is None


def test_authority_invalid_capsule_cannot_supply_native():
    r = row(); e = event(r); c = e['fields']['entry_pre_ai_source_capsule']
    c['broker_order_forbidden'] = False; reseal(c)
    assert S.capsule_native(r, e)[0] is None


def test_malformed_capsule_is_excluded_with_reason():
    r = row(); e = event(r); c = e['fields']['entry_pre_ai_source_capsule']
    c['identity'] = ['invalid']; reseal(c)
    assert S.capsule_native(r, e) == (None, ['native_capsule_identity_structure_invalid'])
    result = S.reconcile(r, [capture(r, native())], S.exact_events(r, S.event_index([e])))
    assert result['status'] == 'native_recovered'
    assert result['rejected_reasons']['native_capsule_identity_structure_invalid'] == 1


def test_nearby_unrelated_event_does_not_supply_missing_native():
    r = row(); e = event(r); e['fields']['machine_observation_sha256'] = 'other'
    e['fields']['evaluation_attempt_id'] = 'other'
    e['fields'].pop('entry_pre_ai_source_capsule')
    assert S.reconcile(r, [capture(r)], [e])['linked_events'] == []


def episode():
    key = list(S.native_identity(row(), native()))
    stamps = dict(entry_at='2026-09-29T09:05:00+09:00', terminal_at='2026-09-29T09:10:00+09:00',
        flat_at='2026-09-29T09:10:01+09:00', rearmed_at='2026-09-29T09:11:00+09:00')
    p = dict(schema=S.EPISODE, native_cluster=key, owner_type='main_scalping', position_id='main:1',
        evidence_class='actual_owner_receipts', kind='full_position_exit', **stamps,
        residual_qty=0, pending_order_count=0, late_fill_resolved=True,
        pending_orders_resolved=True, next_entry_guard_verified=True, source_references={})
    seals, facts = {}, {}
    for i, role in enumerate(('entry', 'terminal', 'flat', 'rearmed'), 1):
        path = role + '.jsonl'; seals[path] = role + '-hash'
        p['source_references'][role] = dict(path=path, physical_sha256=seals[path], line=i)
        facts[path, i] = dict(owner_type='main_scalping', position_id='main:1', native_cluster=key,
            evidence_class='actual_owner_receipts', role=role, observed_at=stamps[role + '_at'],
            physical_sha256=seals[path], residual_qty=0, pending_order_count=0,
            late_fill_resolved=True, pending_orders_resolved=True, next_entry_guard_verified=True)
    p['sha256'] = S.P.R.digest(p)
    return p, seals, facts


def ep_errors(p, seals, facts):
    return S.episode_errors(p, source_seals=seals, expected_native=p['native_cluster'], source_records=facts)


def test_closed_episode_keeps_original_correlated_native_cluster():
    p, seals, facts = episode()
    assert ep_errors(p, seals, facts) == []
    assert p['native_cluster'] == list(S.native_identity(row(), native()))


@pytest.mark.parametrize('refs', [[], {'flat': {'path': [], 'line': []}}])
def test_malformed_episode_reference_is_rejected_without_crashing(refs):
    p, seals, facts = episode(); p['source_references'] = refs
    p['sha256'] = S.P.R.digest({k: v for k, v in p.items() if k != 'sha256'})
    assert ep_errors(p, seals, facts)


@pytest.mark.parametrize('defect', ['widget', 'position', 'native', 'clock', 'partial', 'pending',
    'late_fill', 'guard', 'missing_row', 'wrong_line', 'unknown_custody'])
def test_episode_needs_actual_exact_source_fact_not_just_file_hash(defect):
    p, seals, facts = episode(); f = facts['flat.jsonl', 3]
    if defect == 'widget': f['owner_type'] = 'widget_auto_trade'
    elif defect == 'position': f['position_id'] = 'other'
    elif defect == 'native': f['native_cluster'] = ['other']
    elif defect == 'clock': f['observed_at'] = p['entry_at']
    elif defect == 'partial': f['residual_qty'] = 1
    elif defect == 'pending': f['pending_order_count'] = 1
    elif defect == 'late_fill': facts['rearmed.jsonl', 4]['late_fill_resolved'] = False
    elif defect == 'guard': facts['rearmed.jsonl', 4]['next_entry_guard_verified'] = False
    elif defect == 'missing_row': facts.clear()
    elif defect == 'wrong_line': p['source_references']['flat']['line'] = 99
    else: f['evidence_class'] = 'current_db_snapshot'
    p['sha256'] = S.P.R.digest({k: v for k, v in p.items() if k != 'sha256'})
    assert ep_errors(p, seals, facts)


@pytest.mark.parametrize('defect', ['clock', 'hash', 'kind', 'owner', 'unresolved', 'partial'])
def test_episode_body_cannot_replace_hard_guards(defect):
    p, seals, facts = episode()
    if defect == 'clock': p['entry_at'] = p['rearmed_at']
    elif defect == 'kind': p['kind'] = 'modeled_target'
    elif defect == 'owner': p['owner_type'] = 'widget_auto_trade'
    elif defect == 'unresolved': p['pending_orders_resolved'] = False
    elif defect == 'partial': p['residual_qty'] = 1
    if defect != 'hash': p['sha256'] = S.P.R.digest({k: v for k, v in p.items() if k != 'sha256'})
    else: p['sha256'] = 'wrong'
    assert ep_errors(p, seals, facts)


def test_selector_matches_only_exact_fixed_watch_scope():
    c = S.child_contract('parent', '2026-10-06')
    r = dict(S.SELECTOR, source_date='2026-10-06', **{k: v for k, v in native().items() if k != 'watch_origin'})
    assert S.child_matches(c, r, parent_sha256='parent', now='2026-10-06T09:00:00+09:00')


@pytest.mark.parametrize('defect', ['symbol', 'origin', 'venue', 'session', 'parent', 'empty_selector',
    'expiry', 'date', 'naive_clock', 'live_authority', 'changed_rules', 'missing_admission', 'stale_source_date'])
def test_selector_falls_back_to_parent_outside_reviewed_contract(defect):
    c = S.child_contract('parent', '2026-10-06')
    r = dict(S.SELECTOR, source_date='2026-10-06', **{k: v for k, v in native().items() if k != 'watch_origin'})
    parent = 'parent'; now = '2026-10-06T09:00:00+09:00'
    if defect == 'symbol': r['stock_code'] = '000660'
    elif defect == 'origin': r['watch_origin'] = 'SCANNER'
    elif defect == 'venue': r['effective_venue'] = 'NXT'
    elif defect == 'session': r['session_bucket'] = 'KRX_AFTERMARKET'
    elif defect == 'parent': parent = 'other'
    elif defect == 'empty_selector': c['selector'] = {}
    elif defect == 'expiry': now = c['expiry']
    elif defect == 'date': now = '2026-10-07T09:00:00+09:00'
    elif defect == 'naive_clock': now = '2026-10-06T09:00:00'
    elif defect == 'live_authority': c['runtime_registered'] = True
    elif defect == 'missing_admission': r.pop('watch_admission_id')
    elif defect == 'stale_source_date': r['source_date'] = '2026-09-30'
    else: c['selected_price_rules'] = []
    assert not S.child_matches(c, r, parent_sha256=parent, now=now)


def test_fixed_watch_child_denominator_excludes_samsung_scanner_origin():
    fixed = list(S.native_identity(row(), native()))
    rows = [dict(trace='fixed', native=fixed), dict(trace='scanner', native=fixed[:4] + ['promotion']),
            dict(trace='missing', native=None), dict(trace='other_scope', native=[fixed[0], '005930', 'NXT', *fixed[3:]])]
    assert S.fixed_watch_rows(rows) == [rows[0]]


def test_native_group_metric_does_not_inflate_fixed_watch_or_impute_unknown():
    rows = [dict(trace=str(i), native=['fixed'], day='2026-09-29', label=dict(binary=i % 2, net=.1)) for i in range(20)]
    rows += [dict(trace='unknown', native=['fixed'], day='2026-09-29', label=dict(binary=None)),
             dict(trace='missing', native=None, day='2026-09-29', label=dict(binary=1))]
    m = S.group_metric(rows, {r['trace'] for r in rows})
    assert m['selected_opportunity_count'] == 1 and m['selected_attempt_count'] == 20
    assert m['win_rate_pct'] == 50 and m['unknown_selected_attempt_count'] == 1
    assert m['native_missing_selected_attempt_count'] == 1


def test_missing_holdout_stays_null_and_blocks_formal_hurdles():
    rows = [dict(trace='u', native=['held'], day='2026-10-02', parent='ENTER_NOW', label=dict(binary=None))]
    masks = {key: {'u'} for key in S.FROZEN_MASKS}
    for result in S.native_comparison(rows, masks):
        metric = result['publisher_metric_source']['candidate']['holdout']
        assert metric['win_rate_pct'] is None and metric['selected_opportunity_count'] == 0
        assert not result['registered_successor_hurdles_pass']


def test_better_candidate_can_remove_incumbent_winners():
    rows = []
    for day, n in [('2026-09-29', 40), ('2026-09-30', 40), ('2026-10-02', 20)]:
        for i in range(n):
            rows.append(dict(trace=f'{day}-{i}', native=[day, str(i)], day=day,
                parent='ENTER_NOW', label=dict(binary=int(i < n * .6), net=.1 if i < n * .6 else -.7)))
    ids = set()
    for r in rows:
        i = int(r['trace'].rsplit('-', 1)[1])
        winners = 12 if r['day'] == '2026-10-02' else 24
        losses = 3 if r['day'] == '2026-10-02' else 5
        if (i < winners and i % 5 != 0) or winners <= i < winners + losses:
            ids.add(r['trace'])
    # Keeps under 80% of old winners, while improving native win rate and
    # the registered support-adjusted hurdle with >50% coverage.
    results = S.native_comparison(rows, {key: ids for key in S.FROZEN_MASKS})
    assert all(r['selection_without_new_retention_veto'] for r in results)
    assert all(r['registered_successor_hurdles_pass'] for r in results)


def test_writer_retains_new_authority_and_seal(tmp_path):
    p = tmp_path/'result.json'; S.write(p, dict(runtime_effect=True, consumer_scope='wrong'))
    value = S.P.R.read(p)
    assert value['consumer_scope'] == S.AUTHORITY['consumer_scope']
    assert value['runtime_effect'] is False and value['live_selector_registered'] is False


def test_adapter_retains_serialized_capsule_and_physical_line():
    r = row(); e = event(r)
    record = dict(stock_code='005930', stage='ai_confirmed', fields={**e['fields'],
        'entry_pre_ai_source_capsule': json.dumps(e['fields']['entry_pre_ai_source_capsule'])})
    normalized = S.normalized_event(record, kind='pipeline_events', path='archive.gz', seal='hash', line=93)
    assert normalized['line'] == 93 and S.capsule_native(r, normalized)[0] is not None


def test_canonical_capture_corruption_is_not_normalized():
    body = dict(schema='mechanistic_entry_observation_v1', label_context={'stock_code': '005930'})
    body['machine_observation_sha256'] = hashlib.sha256(S._json_bytes(body)).hexdigest()
    assert S.capture_record(body, path='source', seal='hash', line=3)['trace'] == body['machine_observation_sha256']
    body['label_context']['stock_code'] = '000660'
    with pytest.raises(ValueError, match='canonical_machine_capture_hash_invalid'):
        S.capture_record(body, path='source', seal='hash', line=3)


def test_owner_journal_tracks_physical_lines_across_blanks_and_redacts_account(tmp_path):
    path = tmp_path/'owner.jsonl'; registry = S.OrderOwnerRegistry(path=path)
    event_ = dict(schema='order_owner_registry_event_v1', previous_hash='0' * 64,
        symbol='005930', order_date='2026-09-29', owner_type='widget_auto_trade', account_key='private')
    event_['event_hash'] = hashlib.sha256(('0' * 64).encode() + registry._canonical(event_)).hexdigest()
    path.write_text('\n' + json.dumps(event_) + '\n')
    result = S.owner_inventory(path, {})
    assert result['rows'][0]['line'] == 2 and 'account_key' not in result['rows'][0]
    assert not result['historical_flat_proven'] and path.read_text().startswith('\n')
