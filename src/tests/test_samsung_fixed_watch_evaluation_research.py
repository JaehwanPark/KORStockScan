from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess

import pytest

from src.engine.scalping import samsung_fixed_watch_evaluation_research as F
from src.tests.test_samsung_environment_conditioned_research import capture
from src.tests.test_samsung_pattern_campaign import cache, signal
from src.tests.test_samsung_program_sequence_research import points


def row(t=100., day='2026-09-30', trace='a', parent='ENTER_NOW'):
    return dict(t=t, day=day, trace=trace, parent=parent, ts='2026-09-30T09:00:00+09:00',
        native=[day, '005930', 'KRX', 'KRX_REGULAR', 'MAIN_FIXED_WATCH', 'watch1', 'generation1'],
        features=dict(stream_valid=True, stream_epoch=1), label=dict(binary=1, net=.1, status='target_first'))


def frozen():
    return dict(candidates=[dict(key=F.KEYS[0], conditions={'foreign': 'up'}, historical_gap=None),
        dict(key=F.KEYS[1], conditions={'program_change': 'down'}, historical_gap=180)],
        later_source_after_date='2026-10-04', parent_sha256='parent')


@pytest.mark.parametrize('defect', ['origin', 'symbol', 'venue', 'session', 'day', 'admission', 'generation'])
def test_fixed_watch_scope_requires_original_identity(defect):
    r = row(); assert F.fixed_watch(r)
    index = {'day': 0, 'symbol': 1, 'venue': 2, 'session': 3, 'origin': 4, 'admission': 5, 'generation': 6}[defect]
    r['native'][index] = '' if index > 4 else 'different'
    assert not F.fixed_watch(r)


def test_unknown_context_carries_parent_and_never_admits_block():
    rows = [row(), row(trace='block', parent='BLOCK')]
    masks = F.candidate_masks(rows, [], frozen())
    assert all(ids == {'a'} for ids in masks.values())


def test_fixed_masks_ignore_outcomes_and_retain_expired_context_parent():
    caps = points(); rows = [row(110., trace='a'), row(120., trace='b'), row(200., trace='c')]
    for c in caps:
        c['day'] = '2026-09-30'
    before = F.candidate_masks(rows, caps, frozen())
    assert before[F.KEYS[1]] == {'a', 'c'}
    for r in rows:
        r['label']['binary'] = 0
    assert F.candidate_masks(rows, caps, frozen()) == before
    assert F.candidate_masks(rows[:1], caps[:2], frozen())[F.KEYS[1]] == {'a'}


def test_duplicate_capture_clock_and_changed_filter_are_rejected():
    caps = points()
    with pytest.raises(ValueError, match='clock'):
        F.candidate_masks([row()], caps + [caps[-1]], frozen())
    f = frozen();f['candidates'][0]['conditions'] = {'foreign': 'down'}
    with pytest.raises(ValueError, match='unregistered'):
        F.candidate_masks([row()], [], f)


def test_price_episode_does_not_infer_watch_before_capture_or_cross_epoch():
    signals = [dict(t=t, ep=ep, index=i) for i, (t, ep) in enumerate([(90., 1), (110., 2), (120., 1)])]
    bound, excluded = F.bind_research_signals(signals, [row()])
    assert len(bound) == 1 and bound[0]['native_identity'] == row()['native']
    assert excluded == {'watch_not_yet_observed_or_other_origin': 1, 'watch_epoch_unproven': 1}


def test_replaced_origin_does_not_reuse_earlier_watch():
    changed = row(110., trace='scanner');changed['native'][4] = 'SCANNER'
    bound, _ = F.bind_research_signals([dict(t=120., ep=1)], [row(), changed])
    assert bound == []


def test_cluster_metric_reports_days_and_preserves_censoring():
    def out(day, net, complete=True):
        return dict(native_identity=row(day=day)['native'], complete=complete,
            net=net, binary=None, status='known' if complete else 'censored')
    outcomes = [out('2026-09-30', .1) for _ in range(10)] + [out('2026-10-02', -.1), out('2026-10-02', None, False)]
    result = F.clustered_episode_metric(outcomes)
    assert result['win_rate'] == 10/11 and result['equal_date_mean_win_rate'] == .5
    assert result['original_watch_clusters'] == 2 and result['censored'] == 1
    assert result['independent_native_support_added'] == 0


def test_fold_contract_keeps_date_and_admission_in_one_fold():
    with pytest.raises(ValueError, match='same_date'):
        F.fold_contract([row()], ['2026-09-30'], ['2026-09-30'])
    with pytest.raises(ValueError, match='admission'):
        F.fold_contract([row(), row(day='2026-10-02')], ['2026-09-30'], ['2026-10-02'])
    later = row(day='2026-10-02');later['native'][5] = 'new_watch'
    result = F.fold_contract([row(), later], ['2026-09-30'], ['2026-10-02'])
    assert not result['same_admission_crosses_folds']
    assert not result['episode_count_replaces_generic_native_floor']


@pytest.mark.parametrize('destination', ['data/runtime/new-policy', 'data/policy/new-policy'])
def test_cli_cannot_write_runtime_policy(tmp_path, destination):
    with pytest.raises(SystemExit) as error:
        F.main(['--root', str(tmp_path), '--output', str(tmp_path / destination)])
    assert error.value.code == 2


def test_unknown_episode_blocks_all_later_signals():
    c = cache(2800); ctx = F.C.campaign_context(c)
    watch = row(0.)
    signals = [dict(signal(c, i), ep=1) for i in (4, 100, 1000)]
    result = F.episode_replay(ctx, signals, [watch], .23)
    assert result['metric']['attempts'] == 1 and result['blocked_signals'] == 2
    assert result['outcomes'][0]['net'] is None
    assert result['outcomes'][0]['native_identity'] == watch['native']


def test_widget_target_rounding_uses_gross_target_and_sale_notional_cost():
    c = cache(5000)
    for q in c['depth']:
        q.update(bid=275000., ask=275500.)
    for q in c['depth'][100:]:
        q.update(bid=277000., ask=277500.)
    out = F.widget_target_label(F.C.campaign_context(c), signal(c), 40, .0023)
    assert out['complete'] and out['target_price'] == 277000
    assert out['net'] == pytest.approx((277000*(1-.0023)/275500-1)*100)
    assert out['exit_t'] == c['depth'][100]['t']


def test_resting_widget_limit_does_not_assume_better_fill_on_quote_jump():
    c = cache(5000)
    for q in c['depth']:
        q.update(bid=275000., ask=275500.)
    for q in c['depth'][100:]:
        q.update(bid=280000., ask=280500.)
    out = F.widget_target_label(F.C.campaign_context(c), signal(c), 40, .0023)
    assert out['modeled_exit_price'] == 277000 and out['observed_exit_bid'] == 280000
    assert out['net'] == pytest.approx(F.net_pct(275500, 277000, .0023))


@pytest.mark.parametrize('defect', ['valid', 'ep', 'seq', 'continuous'])
def test_widget_target_cannot_cross_invalid_prefix(defect):
    c = cache(5000)
    c['depth'][100][defect] = False if defect in ['valid', 'continuous'] else 999
    for q in c['depth'][200:]:
        q.update(bid=280000., ask=280500.)
    out = F.widget_target_label(F.C.campaign_context(c), signal(c), 80, .0023)
    assert not out['complete'] and out['net'] is None


def test_widget_never_turns_target_nonarrival_into_forced_time_loss():
    c = cache(5000)
    out = F.widget_target_label(F.C.campaign_context(c), signal(c), 80, .0023)
    assert not out['complete'] and out['net'] is None and out['binary'] is None


@pytest.mark.parametrize('values', [(0, 100, .0023), (100, 0, .0023), (100, 100, -1), (100, 100, float('nan')), (True, 100, .0023)])
def test_missing_or_invalid_cost_is_not_zero_pnl(values):
    with pytest.raises(ValueError):
        F.net_pct(*values)


def test_original_native_metric_does_not_count_repeated_watch_as_new_support():
    rows = [row(100., trace='a'), row(110., trace='b')]
    result = F.native_comparison(rows, {key: {'a', 'b'} for key in F.KEYS})
    assert result['fixed_watch']['observations'] == 2
    assert result['fixed_watch']['original_native_clusters'] == 1
    assert result['fixed_watch']['train']['baseline']['selected_opportunity_count'] == 1


def test_frozen_contract_requires_registered_sealed_kernel_and_parent():
    with pytest.raises(ValueError):
        F.validate_frozen(frozen())


@pytest.mark.parametrize('defect', ['schema', 'old_date', 'parent'])
def test_later_replay_rejects_reused_dates_schema_or_parent_before_read(tmp_path, defect):
    capsule = dict(schema='samsung_frozen_candidate_replay_input_v1', day='2026-10-06', parent_sha256='parent')
    if defect == 'schema':capsule['schema'] = 'other'
    if defect == 'old_date':capsule['day'] = '2026-10-02'
    if defect == 'parent':capsule['parent_sha256'] = 'other'
    with pytest.raises(ValueError):
        F.validate_replay_input(tmp_path, capsule, frozen())


def test_later_preparation_waits_without_collecting_or_creating_inputs(tmp_path):
    output = tmp_path / 'tmp/later'
    assert F.prepare_later_input(tmp_path, '2026-10-06', frozen(), output) is None
    result = F.R.read(output / 'preparation-status.json')
    assert result['status'] == 'waiting_new_source_date' and len(result['missing_source_paths']) == 4
    assert result['data_collected'] is False and result['candidate_reselection'] is False
    assert list(output.iterdir()) == [output / 'preparation-status.json']
    with pytest.raises(ValueError, match='prefreeze'):
        F.prepare_later_input(tmp_path, '2026-10-02', frozen(), output)


def test_source_bad_row_is_identified_without_excluding_good_population():
    good = dict(stock_code='005930', effective_venue='KRX', session_bucket='KRX_REGULAR',
        decision_trace_id='good', source_provenance_verified=True, machine_observation_hash_verified=True)
    bad = dict(good, decision_trace_id='bad', source_provenance_verified=False)
    malformed = dict(good, decision_trace_id='malformed', source_provenance_verified='true')
    result = F.excluded_native_rows([good, bad, malformed])
    assert [r['trace'] for r in result] == ['bad', 'malformed']


def actual_widget():
    root = Path(__file__).resolve().parents[2]
    source = root / 'data/report/widget_signal_auto_trade_events/widget_signal_auto_trade_events_20261002.jsonl'
    if not source.exists():
        pytest.skip('sealed local evidence unavailable')
    owners = F.R.read(root / 'tmp/samsung-opportunity-contract-20261004/accepted-cold/result.json')['owner_inventory']['rows']
    projection = F.R.read(root / 'tmp/samsung-continuous-recovery-research-20261003/source-02/projection.json')
    rows = [r for r in projection['main'] if r['day'] == '2026-10-02']
    return [json.loads(s) for s in source.open()], owners, rows


def test_actual_widget_receipt_is_not_same_main_event_and_cost_is_not_settlement():
    events, owners, rows = actual_widget()
    out = F.widget_receipt(events, owners, rows)
    assert out['custody_verified'] and out['main_research_capture_overlap'] == 0
    assert out['configured_net_pnl_krw'] == pytest.approx(8629)
    assert out['original_target_bps'] == 40 and out['regular_target_bps'] == 80


def test_actual_premarket_main_rechecks_have_canonical_endpoint_comparison():
    events, owners, rows = actual_widget()
    root = Path(__file__).resolve().parents[2]
    widget = F.widget_receipt(events, owners, rows)
    out = F.premarket_owner_bridge(root, widget, {})
    first, second = out['rows']
    assert first['observed_ask'] == 274500 and second['observed_ask'] == 275500
    assert [r['parent_action'] for r in out['rows']] == ['RECHECK', 'RECHECK']
    assert first['entry_price_effect_vs_actual_widget_pct'] > 0
    assert second['entry_price_effect_vs_actual_widget_pct'] == pytest.approx(0.)
    assert second['overlaps_actual_widget_holding'] is True
    assert all(r['actual_main_pnl'] is None for r in out['rows'])


def test_later_replay_rejects_changed_current_parent_before_normalization(tmp_path, monkeypatch):
    p = tmp_path / 'policy.json';p.write_text('{}')
    bundle = dict(scope_policies={'KRX|KRX_REGULAR': {'machine_policy': {'different': True}}})
    monkeypatch.setattr(F.P, 'current_generation', lambda root: ({}, bundle, p, p))
    with pytest.raises(ValueError, match='parent_changed'):
        F.parent_generation(tmp_path, frozen(), '2026-10-06')


@pytest.mark.parametrize('defect', ['partial', 'cost', 'custody', 'notional', 'policy'])
def test_owner_receipt_rejects_partial_cost_or_foreign_custody(defect):
    events, owners, rows = actual_widget();events = deepcopy(events);owners = deepcopy(owners)
    sell = next(e for e in events if e.get('side') == 'SELL' and e.get('order_status') == 'FILLED')
    if defect == 'partial':sell['remaining_qty'] = 1
    if defect == 'cost':sell['timing_operating_opportunity']['contract']['cost_contract']['rate'] = .003
    if defect == 'policy':sell['execution_policy_content_sha256'] = 'other'
    if defect == 'custody':owners = [r for r in owners if r['side'] != 'SELL']
    if defect == 'notional':
        for r in owners:
            if r['event'] == 'ORDER_TERMINAL' and r['side'] == 'SELL':r['fill_amount'] = 1
    with pytest.raises(ValueError):
        F.widget_receipt(events, owners, rows)


def historical_policy_snapshot(root, tmp_path, path, expected_sha256):
    """Relocate an old dated policy to exact archived bytes in this fixture."""
    policy_root = root / 'data/runtime/mechanistic_entry_policy'
    if path.parent.resolve() != policy_root.resolve() or not re.fullmatch(r'policy_\d{4}-\d{2}-\d{2}\.json', path.name):
        return path
    if not isinstance(expected_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('historical_policy_expected_sha_invalid')
    archive = policy_root / 'sources' / (expected_sha256 + '.json')
    original = path if path.is_file() and F.R.P.file_sha(path) == expected_sha256 else archive
    if not original.is_file() or F.R.P.file_sha(original) != expected_sha256:
        raise ValueError('historical_policy_original_archive_missing_or_changed')
    snapshot = tmp_path / 'historical-policy-sources' / archive.name
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(original.read_bytes())
    if F.R.P.file_sha(snapshot) != expected_sha256:
        raise ValueError('historical_policy_archive_changed_during_snapshot')
    return snapshot


@pytest.mark.parametrize('archive_state', ['exact', 'missing', 'changed'])
def test_historical_policy_snapshot_preserves_original_hash_and_live_pointer(tmp_path, archive_state):
    root = tmp_path / 'root'; policy = root / 'data/runtime/mechanistic_entry_policy/policy_2026-10-06.json'
    policy.parent.mkdir(parents=True)
    policy.write_text('{"generation":"old"}')
    expected = F.R.P.file_sha(policy)
    archive = policy.parent / 'sources' / (expected + '.json')
    archive.parent.mkdir()
    if archive_state != 'missing':
        archive.write_bytes(policy.read_bytes() if archive_state == 'exact' else b'changed')
    policy.write_text('{"generation":"new"}')
    current = policy.read_bytes()
    if archive_state == 'exact':
        snapshot = historical_policy_snapshot(root, tmp_path / 'fixture', policy, expected)
        assert snapshot != archive and F.R.P.file_sha(snapshot) == expected
        snapshot.write_bytes(b'tampered fixture')
        with pytest.raises(ValueError, match='sealed_file_changed'):
            F.Q.verify_hashes({str(snapshot): expected})
    else:
        with pytest.raises(ValueError, match='original_archive_missing_or_changed'):
            historical_policy_snapshot(root, tmp_path / 'fixture', policy, expected)
    assert policy.read_bytes() == current


def test_historical_snapshot_does_not_relax_other_source_hashes(tmp_path):
    source = tmp_path / 'arbitrary/policy_2026-10-06.json'
    source.parent.mkdir(); source.write_text('original')
    expected = F.R.P.file_sha(source); source.write_text('changed')
    assert historical_policy_snapshot(tmp_path, tmp_path / 'fixture', source, expected) == source
    with pytest.raises(ValueError, match='sealed_file_changed'):
        F.Q.verify_hashes({str(source): expected})


def test_historical_policy_snapshot_is_independent_of_later_pointer_changes(tmp_path):
    policy = tmp_path / 'data/runtime/mechanistic_entry_policy/policy_2026-10-06.json'
    policy.parent.mkdir(parents=True); policy.write_text('original bytes')
    expected = F.R.P.file_sha(policy)
    snapshot = historical_policy_snapshot(tmp_path, tmp_path / 'fixture', policy, expected)
    policy.write_text('next generation')
    F.Q.verify_hashes({str(snapshot): expected})


def historical_intake_fixture(tmp_path):
    """Exercise raw intake on existing bytes, never label it a new holdout."""
    root = Path(__file__).resolve().parents[2]
    original = root / 'tmp/samsung-continuous-recovery-research-20261003/source-02/projection.json'
    if not original.exists():
        pytest.skip('sealed local evidence unavailable')
    projection = F.R.read(original)
    projection['main'] = [r for r in projection['main'] if r['day'] == '2026-10-02']
    projection.pop('content_sha256')
    census = F.R.read(root / 'tmp/samsung-environment-conditioned-research-20261004/accepted-cold/source-census.json')
    census['captures'] = [r for r in census['captures'] if r['day'] == '2026-10-02']
    census.pop('content_sha256')
    # Keep the discovery generation's exact kernel bytes in this test fixture.
    # Never rehash an old production census against a repaired working file.
    # This historical unit intake is already rejected by validate_frozen at CLI.
    seals = {}
    for name, digest in census['source_seals'].items():
        path = Path(name)
        kernel_root = next((base for base in (root, (root / 'data').resolve().parent)
                            if path.is_relative_to(base / 'src')), None)
        if kernel_root is not None:
            data = path.read_bytes()
            if F.R.P.file_sha(path) != digest:
                relative = path.relative_to(kernel_root).as_posix()
                data = subprocess.check_output(['git', '-C', str(root), 'show',
                    'a17bd6d2587e1204eacd0cd283bcbd854eb71bfc:' + relative])
            snapshot = tmp_path / 'historical-kernels' / path.relative_to(kernel_root)
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(data)
            assert F.R.P.file_sha(snapshot) == digest
            name = str(snapshot)
        else:
            name = str(historical_policy_snapshot(root, tmp_path, path, digest))
        seals[name] = digest
    census['source_seals'] = seals
    native = root / 'data/report/machine_observation_projection/machine_observation_projection_2026-10-02_0_1.json'
    paths = {'projection': tmp_path / 'projection.json', 'capture_census': tmp_path / 'census.json', 'native_projection': native}
    for role, data in [('projection', projection), ('capture_census', census)]:
        paths[role].write_text(json.dumps(data))
    f = frozen()
    f['later_source_after_date'] = '2026-09-30'  # Unit intake only; CLI validate_frozen rejects this override.
    f['parent_sha256'] = projection['parent_sha256']
    f['parent_policy'] = F.R.read(root / 'tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json')['parent_policy']
    capsule = dict(schema='samsung_frozen_candidate_replay_input_v1', day='2026-10-02', parent_sha256=f['parent_sha256'],
        **{role: dict(path=str(path), sha256=F.R.P.file_sha(path)) for role, path in paths.items()})
    return root, f, capsule, paths, projection, census


def test_historical_intake_roundtrips_native_and_canonical_sources(tmp_path):
    root, f, capsule, _, projection, _ = historical_intake_fixture(tmp_path)
    rows, captures, seals = F.validate_replay_input(root, capsule, f)
    assert rows == projection['main'] and len(rows) == len(captures) == 160
    assert seals and F.candidate_masks(rows, captures, f)[F.KEYS[1]] == {
        r['trace'] for r in rows if r['parent'] == 'ENTER_NOW'}


def test_historical_intake_rejects_changed_sealed_kernel_snapshot(tmp_path):
    root, f, capsule, _, _, census = historical_intake_fixture(tmp_path)
    kernel = next(Path(p) for p in census['source_seals'] if 'historical-kernels' in p)
    kernel.write_bytes(kernel.read_bytes() + b'\n# changed fixture generation\n')
    with pytest.raises(ValueError, match='sealed_file_changed'):
        F.validate_replay_input(root, capsule, f)


@pytest.mark.parametrize('defect', ['label', 'native', 'omitted_row', 'unsealed_source'])
def test_later_adapter_rejects_changed_native_labels_identity_and_incomplete_source(tmp_path, defect):
    root, f, capsule, paths, projection, census = historical_intake_fixture(tmp_path)
    if defect == 'label':projection['main'][0]['label']['binary'] = 1
    if defect == 'native':projection['main'][0]['native'][5] = 'invented'
    if defect == 'omitted_row':projection['main'].pop()
    if defect == 'unsealed_source':census['source_seals'] = {}
    for role, data in [('projection', projection), ('capture_census', census)]:
        paths[role].write_text(json.dumps(data));capsule[role]['sha256'] = F.R.P.file_sha(paths[role])
    with pytest.raises(ValueError):
        F.validate_replay_input(root, capsule, f)


@pytest.mark.parametrize('defect', ['program', 'stream_quality', 'suffix', 'duplicate_location'])
def test_canonical_capture_cannot_be_replaced_by_resealed_derived_context(tmp_path, monkeypatch, defect):
    root, f, capsule, paths, projection, census = historical_intake_fixture(tmp_path)
    cap = census['captures'][0]
    if defect == 'program':cap['program']['value']['net_qty'] += 1
    if defect == 'stream_quality':cap['stream_valid'] = not cap['stream_valid']
    if defect == 'suffix':cap['market_suffix'] = '_NX'
    if defect == 'duplicate_location':census['captures'][1]['source_location'] = deepcopy(cap['source_location'])
    paths['capture_census'].write_text(json.dumps(census))
    capsule['capture_census']['sha256'] = F.R.P.file_sha(paths['capture_census'])
    # Raw native/canonical readers remain real. Only the separately tested
    # expensive stream reconstruction is supplied as its known historical value.
    monkeypatch.setattr(F.R, 'stream_rows', lambda *a: ([], {}))
    monkeypatch.setattr(F.R, 'market_features', lambda *a: [r['features'] for r in sorted(projection['main'], key=lambda r: r['t'])])
    with pytest.raises(ValueError):
        F.validate_replay_input(root, capsule, f)
