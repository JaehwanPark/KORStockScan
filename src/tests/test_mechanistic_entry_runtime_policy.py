import copy
import hashlib
import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping import mechanistic_entry_runtime_policy as policy


def source(tmp_path, source_date="2026-09-11"):
    report = calibration._with_artifact_content_sha256(
        {
            "schema": calibration.SCHEMA,
            "target_date": source_date,
            "clean_tuning_baseline_date": "2026-06-05",
            "mechanistic_entry_refinement": {
                "policy_candidate": None,
                "promotion_pass": False,
            },
            "mechanistic_flow_groups": {
                "source_population": {"accepted_unique_trace_count": 15}
            },
        }
    )
    path = tmp_path / f"source_{source_date}.json"
    calibration._atomic_write_json(path, report)
    return path


def initial(tmp_path):
    return policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        bootstrap=True,
        now=datetime(2026, 9, 13, 20, tzinfo=policy.KST),
    )


def test_operator_prompt_stage_preserves_machine_and_other_scopes(tmp_path):
    incumbent = initial(tmp_path)
    evidence = {
        'schema': 'auxiliary_prompt_operator_review_v1',
        'prompt_version': policy.ENTRY_MACHINE_AUXILIARY_COMPACT_CONTRACT_PROMPT_VERSION,
        'scope': 'KRX|KRX_REGULAR',
        'operator_direction': 'explicit_prompt_change',
        'independent_holdout_claimed': False,
        'research_dates': ['2026-09-22', '2026-09-23'],
    }
    result = policy.activate_operator_auxiliary_prompt(
        data_root=tmp_path, target_date='2026-09-28', evidence=evidence,
        now=datetime(2026, 9, 26, 12, tzinfo=policy.KST),
    )
    assert result['status'] == 'staged'
    assert policy._load_current(tmp_path, '2026-09-26')['bundle_sha256'] == incumbent['bundle_sha256']
    selected = policy.load_effective(data_root=tmp_path, target_date='2026-09-28')
    assert selected['ai_policy']['prompt_version'] == evidence['prompt_version']
    assert selected['machine_policy'] == incumbent['machine_policy']
    assert policy.activate_operator_auxiliary_prompt(
        data_root=tmp_path, target_date='2026-09-28', evidence=evidence,
        now=datetime(2026, 9, 26, 12, tzinfo=policy.KST),
    )['status'] == 'already_staged'
    source = policy.root(tmp_path) / 'sources' / f"{policy.digest(evidence)}.json"
    source.write_text('{}')
    policy._CURRENT_CACHE.clear()
    with pytest.raises(ValueError, match='auxiliary_operator_component_binding_invalid'):
        policy.load_effective(data_root=tmp_path, target_date='2026-09-28')


def test_winrate_stage_requires_explicit_preopen_activation(tmp_path, monkeypatch):
    from src.engine.scalping import entry_strategy_policy as strategy
    previous = copy.deepcopy(initial(tmp_path))
    previous['machine_policy'] = strategy.seed(previous['machine_policy'], ('KRX', 'KRX_REGULAR'))
    previous['bundle_sha256'] = policy.digest({k: v for k, v in previous.items() if k != 'bundle_sha256'})
    policy._atomic_write_json(policy.root(tmp_path) / 'policy_2026-09-14.json', previous)
    policy._atomic_write_json(policy.root(tmp_path) / 'generations' / f"{previous['bundle_sha256']}.json", previous)
    candidate = copy.deepcopy(previous['machine_policy'])
    candidate['entry_situation_veto'] = dict(schema='entry_situation_veto_v1',
        selection_basis='win_rate_only', market='REGULAR', exact_scope='KRX|KRX_REGULAR',
        feature='curr_vs_micro_vwap_bp', threshold_bp=68.75,
        condition='parent_ENTER_NOW_and_fresh_available', selected_action='BLOCK',
        unknown_action='parent')
    report = calibration._with_artifact_content_sha256(dict(
        schema='main_entry_winrate_policy_report_v1', target_date='2026-09-23',
        report_scope='main_entry_winrate', selection_basis='win_rate_only',
        policy_version='winrate_initial_v1',
        disposition='initial_adopted', source_contract_sha256='a' * 64,
        evaluated_attempt_manifest_sha256='b' * 64,
        source_receipt=dict(target_date='2026-09-23', tuning_input_allowed=True,
            machine_threshold_tuning_input_allowed=True),
        parent_bundle_sha256=previous['bundle_sha256'],
        parent_machine_policy_sha256=policy.digest(previous['machine_policy']),
        candidate_machine_policy_sha256=policy.digest(candidate), candidate_policy=candidate,
        policy_by_scope={'KRX|KRX_REGULAR': candidate},
        policy_sha256=policy.digest({'KRX|KRX_REGULAR': candidate}),
        candidate_threshold_bp=68.75, input_attempt_count=1485,
        accepted_attempt_count=351, source_contract_excluded_count=60,
        source_contract_exclusion_reasons={'conflicting_exact_attempt': 60},
        excluded_attempt_counts={'quality_path_cost_missing_or_mismatched': 1074},
        situation_attempt_counts={'VWAP_NOT_EXTENDED': 291, 'VWAP_EXTENDED': 60},
        market_census={
            'KRX|KRX_REGULAR': dict(market='REGULAR', input_attempt_count=1485,
                accepted_attempt_count=351, source_contract_excluded_count=60,
                source_contract_exclusion_reasons={'conflicting_exact_attempt': 60},
                excluded_attempt_counts={'quality_path_cost_missing_or_mismatched': 1074},
                gross_label_difference_count=9),
            'PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE': dict(market='PREMARKET',
                input_attempt_count=116, accepted_attempt_count=19, source_contract_excluded_count=6,
                source_contract_exclusion_reasons={'conflicting_exact_attempt': 6},
                excluded_attempt_counts={'quality_path_cost_missing_or_mismatched': 91}),
            'KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET': dict(market='AFTERMARKET',
                input_attempt_count=484, accepted_attempt_count=84, source_contract_excluded_count=8,
                source_contract_exclusion_reasons={'conflicting_exact_attempt': 8},
                excluded_attempt_counts={'quality_path_cost_missing_or_mismatched': 392})},
        gross_label_difference_count=9,
        historical_full_evaluation_reference=dict(
            artifact_content_sha256='10b29ced3cf6e61bee35e84de5e456db3dd78b562378cd0aef9db605fdc85564',
            total_eligible_count=476,
            exact_scope_eligible_counts={'KRX|KRX_REGULAR': 351,
                'PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE': 25,
                'KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET': 100}),
        train_dates=['2026-09-22'], holdout_dates=['2026-09-23'],
        candidate=dict(train=dict(selected_opportunity_count=11, winning_attempt_count=10),
                       holdout=dict(selected_opportunity_count=4, winning_attempt_count=3)),
        hurdle_errors=[]))
    source_path = tmp_path / 'winrate_report.json'
    policy._atomic_write_json(source_path, report)
    staged = policy.stage_winrate_policy(source_path, data_root=tmp_path,
        now=datetime(2026, 9, 24, 14, tzinfo=policy.KST))
    assert staged['status'] == 'staged' and staged['target_date'] == '2026-09-28'
    assert not (policy.root(tmp_path) / 'current.json').exists()
    assert policy.load(data_root=tmp_path, target_date='2026-09-28')['machine_policy'] == candidate
    assert policy.load_effective(data_root=tmp_path, target_date='2026-09-28')['machine_policy'] == previous['machine_policy']
    pending = copy.deepcopy(report)
    pending.update(target_date='2026-09-24', publication_date='2026-09-24',
        disposition='incumbent_carried', candidate_policy=None, policy_by_scope={},
        policy_sha256=policy.digest({}), candidate_threshold_bp=None,
        hurdle_errors=['initial_policy_pending_activation'],
        pending_initial_bundle_sha256=staged['bundle_sha256'],
        pending_initial_target_date='2026-09-28')
    pending['source_receipt']['target_date'] = '2026-09-24'
    pending = calibration._with_artifact_content_sha256({k: v for k, v in pending.items()
        if k != 'artifact_content_sha256'})
    policy._atomic_write_json(source_path, pending)
    carried = policy.stage_winrate_policy(source_path, data_root=tmp_path,
        now=datetime(2026, 9, 24, 14, tzinfo=policy.KST))
    assert carried['status'] == 'pending_initial_preserved'
    assert policy.load(data_root=tmp_path, target_date='2026-09-28')['bundle_sha256'] == staged['bundle_sha256']
    invalid_pending = copy.deepcopy(pending)
    invalid_pending['pending_initial_bundle_sha256'] = 'f' * 64
    invalid_pending = calibration._with_artifact_content_sha256({k: v for k, v in invalid_pending.items()
        if k != 'artifact_content_sha256'})
    policy._atomic_write_json(source_path, invalid_pending)
    with pytest.raises(ValueError, match='winrate_pending_initial_contract_invalid'):
        policy.stage_winrate_policy(source_path, data_root=tmp_path,
            now=datetime(2026, 9, 24, 14, tzinfo=policy.KST))
    changed = copy.deepcopy(report)
    changed['candidate_policy']['thresholds']['min_score'] = -999
    changed['candidate_machine_policy_sha256'] = policy.digest(changed['candidate_policy'])
    changed['policy_by_scope'] = {'KRX|KRX_REGULAR': changed['candidate_policy']}
    changed['policy_sha256'] = policy.digest(changed['policy_by_scope'])
    changed = calibration._with_artifact_content_sha256({k: v for k, v in changed.items()
        if k != 'artifact_content_sha256'})
    policy._atomic_write_json(source_path, changed)
    with pytest.raises(ValueError, match='winrate_candidate_contract_invalid'):
        policy.stage_winrate_policy(source_path, data_root=tmp_path,
            now=datetime(2026, 9, 24, 14, tzinfo=policy.KST))
    misbound = copy.deepcopy(report)
    misbound['policy_sha256'] = 'f' * 64
    misbound = calibration._with_artifact_content_sha256({k: v for k, v in misbound.items()
        if k != 'artifact_content_sha256'})
    policy._atomic_write_json(source_path, misbound)
    with pytest.raises(ValueError, match='winrate_candidate_contract_invalid'):
        policy.stage_winrate_policy(source_path, data_root=tmp_path,
            now=datetime(2026, 9, 24, 14, tzinfo=policy.KST))
    prompt_evidence = {
        'schema': 'auxiliary_prompt_operator_review_v1',
        'prompt_version': policy.ENTRY_MACHINE_AUXILIARY_COMPACT_CONTRACT_PROMPT_VERSION,
        'scope': 'KRX|KRX_REGULAR', 'operator_direction': 'explicit_prompt_change',
        'independent_holdout_claimed': False,
    }
    assert policy.activate_operator_auxiliary_prompt(
        data_root=tmp_path, target_date='2026-09-28', evidence=prompt_evidence,
        now=datetime(2026, 9, 26, 12, tzinfo=policy.KST),
    )['status'] == 'staged'
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 28, 8, 30, tzinfo=tz or policy.KST)
    monkeypatch.setattr(policy, 'datetime', FrozenDateTime)
    activated = policy.activate_dated_winrate_policy(data_root=tmp_path,
        target_date='2026-09-28', now=FrozenDateTime.now(policy.KST))
    assert activated['status'] == 'activated'
    assert policy.load_effective(data_root=tmp_path, target_date='2026-09-28')['machine_policy'] == candidate
    assert policy.load_effective(data_root=tmp_path, target_date='2026-09-28')['ai_policy']['prompt_version'] == prompt_evidence['prompt_version']
    repeated = policy.activate_dated_winrate_policy(data_root=tmp_path,
        target_date='2026-09-28', now=FrozenDateTime.now(policy.KST))
    assert repeated == {'status': 'already_active', 'bundle_sha256': activated['bundle_sha256']}
    auxiliary_child = copy.deepcopy(policy.load_effective(data_root=tmp_path, target_date='2026-09-28'))
    auxiliary_child['bundle_sha256'] = 'c' * 64
    auxiliary_child['strategy_activation'] = dict(schema='main_auxiliary_activation_v1',
        parent_bundle_sha256=activated['bundle_sha256'])
    with monkeypatch.context() as patch:
        patch.setattr(policy, '_load_current', lambda *_args: auxiliary_child)
        after_auxiliary = policy.activate_dated_winrate_policy(data_root=tmp_path,
            target_date='2026-09-28', now=FrozenDateTime.now(policy.KST))
    assert after_auxiliary == {'status': 'already_active', 'bundle_sha256': 'c' * 64}
    relaxed = copy.deepcopy(candidate)
    relaxed['entry_situation_veto']['threshold_bp'] = 80.0
    successor = copy.deepcopy(report)
    successor.update(target_date='2026-10-01', publication_date='2026-10-01',
        policy_version='winrate_successor_v1', disposition='successor_selected',
        parent_bundle_sha256=activated['bundle_sha256'],
        parent_machine_policy_sha256=policy.digest(candidate),
        candidate_policy=relaxed, candidate_machine_policy_sha256=policy.digest(relaxed),
        policy_by_scope={'KRX|KRX_REGULAR': relaxed},
        policy_sha256=policy.digest({'KRX|KRX_REGULAR': relaxed}),
        candidate_threshold_bp=80.0)
    successor['source_receipt']['target_date'] = '2026-10-01'
    successor = calibration._with_artifact_content_sha256({k: v for k, v in successor.items()
        if k != 'artifact_content_sha256'})
    successor_path = tmp_path / 'successor_report.json'
    policy._atomic_write_json(successor_path, successor)
    monkeypatch.setattr(policy, '_winrate_successor_hurdles_valid', lambda _source: True)
    with pytest.raises(ValueError, match='winrate_candidate_contract_invalid'):
        policy.stage_winrate_policy(successor_path, data_root=tmp_path,
            now=datetime(2026, 10, 1, 20, tzinfo=policy.KST))


def test_winrate_successor_publisher_rechecks_both_holdout_dates_and_winrate_hurdles():
    report = {'target_date': '2026-10-01',
        'train_dates': ['2026-09-24', '2026-09-28', '2026-09-29'],
        'holdout_dates': ['2026-09-30', '2026-10-01'], 'consumed_holdout_dates': [],
        'baseline': {
            'train': {'source_dates': ['2026-09-24', '2026-09-28', '2026-09-29'],
                'selected_attempt_count': 40, 'selected_opportunity_count': 40,
                'winning_attempt_count': 24, 'win_rate_pct': 60.0,
                'support_adjusted_win_rate_pct': 50.0},
            'holdout': {'source_dates': ['2026-09-30', '2026-10-01'],
                'selected_attempt_count': 20, 'selected_opportunity_count': 20,
                'winning_attempt_count': 12, 'win_rate_pct': 60.0,
                'support_adjusted_win_rate_pct': 45.0}},
        'candidate': {
            'train': {'source_dates': ['2026-09-24', '2026-09-28', '2026-09-29'],
                'selected_attempt_count': 32, 'selected_opportunity_count': 32,
                'winning_attempt_count': 23, 'win_rate_pct': 71.875,
                'support_adjusted_win_rate_pct': 58.0},
            'holdout': {'source_dates': ['2026-09-30', '2026-10-01'],
                'selected_attempt_count': 16, 'selected_opportunity_count': 16,
                'winning_attempt_count': 11, 'win_rate_pct': 68.75,
                'support_adjusted_win_rate_pct': 52.0}}}
    assert policy._winrate_successor_hurdles_valid(report)
    malformed = copy.deepcopy(report)
    malformed['candidate'] = ['wrong_type']
    assert not policy._winrate_successor_hurdles_valid(malformed)
    malformed = copy.deepcopy(report)
    malformed['candidate']['holdout']['selected_attempt_count'] = 1
    assert not policy._winrate_successor_hurdles_valid(malformed)
    one_day = copy.deepcopy(report)
    one_day['candidate']['holdout']['source_dates'] = ['2026-09-30']
    assert not policy._winrate_successor_hurdles_valid(one_day)
    reused = copy.deepcopy(report)
    reused['consumed_holdout_dates'] = ['2026-09-30']
    assert not policy._winrate_successor_hurdles_valid(reused)
    weak = copy.deepcopy(report)
    weak['candidate']['holdout']['support_adjusted_win_rate_pct'] = 49.0
    assert not policy._winrate_successor_hurdles_valid(weak)


def test_winrate_market_census_requires_all_three_markets_and_top_level_binding():
    row = dict(market='REGULAR', input_attempt_count=4, accepted_attempt_count=2,
        source_contract_excluded_count=1, source_contract_exclusion_reasons={'conflict': 1},
        excluded_attempt_counts={'path_missing': 1}, gross_label_difference_count=0)
    report = dict(input_attempt_count=4, accepted_attempt_count=2,
        source_contract_excluded_count=1, source_contract_exclusion_reasons={'conflict': 1},
        excluded_attempt_counts={'path_missing': 1}, gross_label_difference_count=0,
        market_census={'KRX|KRX_REGULAR': row,
            'PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE': dict(row, market='PREMARKET'),
            'KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET': dict(row, market='AFTERMARKET')})
    assert policy.winrate_market_census_valid(report)
    missing = copy.deepcopy(report)
    missing['market_census'].pop('PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE')
    assert not policy.winrate_market_census_valid(missing)
    changed = copy.deepcopy(report)
    changed['market_census']['KRX|KRX_REGULAR']['accepted_attempt_count'] = 3
    assert not policy.winrate_market_census_valid(changed)


def test_initial_policy_does_not_require_promotion_candidate(tmp_path):
    bundle = initial(tmp_path)
    assert bundle["target_date"] == "2026-09-14"
    assert bundle["machine_disposition"] == "initial_policy_not_performance_promotion"
    assert (
        bundle["machine_policy"]["thresholds"]
        == policy.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1["thresholds"]
    )
    assert bundle["ai_policy"]["system_prompt"].isascii()
    assert (
        bundle["historical_context"]["flow_source_population"][
            "accepted_unique_trace_count"
        ]
        == 15
    )
    assert policy.load(data_root=tmp_path, target_date="2026-09-14") == bundle


def test_historical_source_uses_publication_day_for_next_preopen_policy(tmp_path):
    initial(tmp_path)
    path = source(tmp_path, "2026-09-17")
    report = json.loads(path.read_text())
    report.update(
        report_scope="main_mechanistic_entry",
        noncompact_sections_refreshed=True,
        machine_full_evaluation={"state": "evaluated_no_edge"},
    )
    report.pop("artifact_content_sha256")
    report = calibration._with_artifact_content_sha256(report)
    calibration._atomic_write_json(
        path, report
    )

    bundle = policy.publish(
        path,
        data_root=tmp_path,
        publication_day="2026-09-20",
        now=datetime(2026, 9, 20, 6, tzinfo=policy.KST),
    )

    assert bundle["source_date"] == "2026-09-17"
    assert bundle["publication_date"] == "2026-09-20"
    assert bundle["target_date"] == "2026-09-21"
    assert bundle["machine_evaluation_source"]["artifact_content_sha256"] == report[
        "artifact_content_sha256"
    ]
    assert bundle["machine_evaluation_source"]["terminal_state"] == "evaluated_no_edge"
    policy.validate(bundle, target_date="2026-09-21")


def test_compact_successor_accepts_carried_machine_activation(tmp_path):
    bundle = initial(tmp_path)
    bundle["target_date"] = "2026-09-15"
    bundle["publication_date"] = "2026-09-14"
    bundle["strategy_activation"] = {
        "schema": "main_entry_activation_v3",
        "effective_from": "2026-09-14T21:00:00+09:00",
        "lifetime": "until_superseded",
    }
    bundle["bundle_sha256"] = policy.digest(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    policy.validate(bundle, target_date="2026-09-15")


@pytest.mark.parametrize("changed_parent", [False, True])
def test_common_successor_is_automatic_only_against_exact_current_parent(monkeypatch, tmp_path, changed_parent):
    from src.engine.scalping import entry_setup_live_policy as activation
    previous = initial(tmp_path)
    parent = copy.deepcopy(previous["machine_policy"])
    if changed_parent:
        parent["thresholds"]["minimum_micro_net_aggressive_delta_10t"] = 7.0
    successor_machine = copy.deepcopy(parent)
    successor_machine["thresholds"]["maximum_spread_bp"] = 40.0
    monkeypatch.setattr(activation, "_mechanistic_primary_activation_projection", lambda *a, **kw: ({
        "threshold_policy": successor_machine,
        "incumbent_machine_policy_sha256": policy.digest(parent),
    }, []))
    successor = policy.publish(
        source(tmp_path, "2026-09-14"), data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST),
    )
    if changed_parent:
        assert successor["machine_policy"] == previous["machine_policy"]
        assert successor["machine_disposition"] == "candidate_parent_changed_revalidation_required"
    else:
        assert successor["machine_policy"] == successor_machine
        assert successor["machine_disposition"] == "evidence_qualified_threshold_update"
    assert successor["ai_policy"]["prompt_version"] == previous["ai_policy"]["prompt_version"]


@pytest.mark.parametrize("parent_changed", [False, True])
@pytest.mark.parametrize("scope", ["KRX|KRX_REGULAR", "NXT|NXT_AFTERMARKET"])
def test_full_population_hierarchy_automatic_publisher_requires_exact_parent(tmp_path, parent_changed, scope, monkeypatch):
    # This test isolates publisher parent binding. Operating model correctness
    # is tested with signed owner proofs in test_ai_action_outcome_calibration.
    original_metrics = calibration._mechanistic_paired_population_metrics
    def supported_metrics(*args, **kwargs):
        return {**original_metrics(*args, **kwargs),
                "operating_economic_promotion_pass": True,
                "downstream_operating_evidence_complete": True,
                "daily_net_profit_delta_krw": 10.0,
                "operating_economic_comparison": {
                    "status": "supported_operating_comparison",
                    "incumbent": {"ev_pct": 0.0}, "candidate": {"ev_pct": 0.12}}}
    monkeypatch.setattr(calibration, "_mechanistic_paired_population_metrics", supported_metrics)
    from src.tests.test_ai_action_outcome_calibration import _natural_refinement_fixture
    previous = initial(tmp_path)
    if scope != "KRX|KRX_REGULAR":
        previous = policy.publish(source(tmp_path), data_root=tmp_path,
                                  adopt_hierarchy=True, adopt_all_continuous=True,
                                  now=datetime(2026, 9, 13, 22, tzinfo=policy.KST))
    previous["hierarchy_adopted"] = True
    incumbent = previous["machine_policy"] if scope == "KRX|KRX_REGULAR" else previous["scope_policies"][scope]["machine_policy"]
    incumbent["thresholds"]["maximum_spread_bp"] = 20
    original_parent = json.loads(json.dumps(incumbent))
    cohort = tuple(scope.split("|"))
    rows, receipt = _natural_refinement_fixture()
    for row in rows:
        row["entry_group_observation"]["key_parts"].update(venue=cohort[0], session_bucket=cohort[1])
        row.update(effective_venue=cohort[0], session_bucket=cohort[1])
        row["comparison"]["entry_cost_contract"].update(effective_venue=cohort[0], session_bucket=cohort[1])
        row["comparison"]["entry_path_target_pct"] = 0.32
        evidence = row["setup_evidence"]
        evidence["micro_recovery_observation"] = {
            "source_usable": True, "net_aggressive_delta_10t": 20, "price_change_10t_pct": 0.1,
        }
        evidence["evidence_sha256"] = policy.digest({k: v for k, v in evidence.items() if k != "evidence_sha256"})
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={}, cohort=cohort,
    )
    extension = calibration.build_mechanistic_hierarchy_candidate(
        normalized, target_date="2026-09-15", parent_policy=original_parent,
        population_source_contract=contract,
        cohort=cohort,
    )
    assert extension["promotion_pass"] is True
    if parent_changed:
        incumbent["thresholds"]["minimum_micro_net_aggressive_delta_10t"] = 2.0
    previous["bundle_sha256"] = policy.digest({k: v for k, v in previous.items() if k != "bundle_sha256"})
    calibration._atomic_write_json(policy.root(tmp_path) / "policy_2026-09-14.json", previous)
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    report["hierarchical_entry_quality"] = {"runtime_extension": extension} if scope == "KRX|KRX_REGULAR" else {"runtime_extensions_by_scope": {scope: extension}}
    report["report_scope"] = "main_mechanistic_entry"
    report["machine_full_evaluation"] = {"state": "evaluated_no_edge"}
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(path, calibration._with_artifact_content_sha256(report))
    successor = policy.publish(path, data_root=tmp_path,
                               now=datetime(2026, 9, 15, 21, tzinfo=policy.KST))
    selected = successor if scope == "KRX|KRX_REGULAR" else successor["scope_policies"][scope]
    selected_disposition = selected["historical_context"]["hierarchy_disposition"] if scope == "KRX|KRX_REGULAR" else selected["machine_disposition"]
    if parent_changed:
        assert selected["machine_policy"] == incumbent
        assert selected_disposition == "candidate_parent_changed_revalidation_required"
    else:
        assert selected["machine_policy"] == extension["policy_candidate"]["threshold_policy"]
        assert selected_disposition == ("evidence_qualified_hierarchy_update" if scope == "KRX|KRX_REGULAR" else "evidence_qualified_exact_scope_update")
    if scope != "KRX|KRX_REGULAR":
        assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["ai_policy"]["prompt_version"] == previous["ai_policy"]["prompt_version"]


def test_proxy_only_full_population_candidate_is_carried_without_runtime_promotion(tmp_path):
    from src.tests.test_ai_action_outcome_calibration import (
        _natural_refinement_fixture, _mechanistic_evidence,
    )
    previous = initial(tmp_path)
    # Model an already selected tighter incumbent, not a second live owner.
    previous["machine_policy"]["thresholds"]["maximum_spread_bp"] = 40.0
    previous["bundle_sha256"] = policy.digest({k: v for k, v in previous.items() if k != "bundle_sha256"})
    calibration._atomic_write_json(policy.root(tmp_path) / "policy_2026-09-14.json", previous)
    rows, receipt = _natural_refinement_fixture()
    for row in rows:
        row["setup_evidence"] = _mechanistic_evidence(spread_bp=50)
        row["comparison"]["entry_path_target_pct"] = 0.27
    normalized, contract = calibration._common_refinement_population(
        [], rows, target_date="2026-09-15", source_receipt=receipt, paired_contract={},
    )
    refinement = calibration.build_clean_baseline_mechanistic_refinement(
        tmp_path / "unused", target_date="2026-09-15", source_rows=normalized,
        source_contract=contract, parent_policy=previous["machine_policy"],
    )
    assert refinement["promotion_pass"] is False
    assert refinement["policy_candidate"] is None
    assert refinement["best_observed_candidate"]["calibration_paired_population"][
        "downstream_operating_evidence_complete"
    ] is False
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    report["mechanistic_entry_refinement"] = refinement
    report["report_scope"] = "main_mechanistic_entry"
    report["noncompact_sections_refreshed"] = True
    report["machine_full_evaluation"] = {
        "state": "evaluated_no_edge",
    }
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(path, calibration._with_artifact_content_sha256(report))
    successor = policy.publish(path, data_root=tmp_path, now=datetime(2026, 9, 15, 21, tzinfo=policy.KST))
    assert successor["machine_disposition"] == "incumbent_carried"
    assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["ai_policy"]["prompt_version"] == previous["ai_policy"]["prompt_version"]
    assert successor["machine_evaluation_source"]["terminal_state"] == "evaluated_no_edge"


def test_frozen_legacy_prompt_bundle_remains_readable(tmp_path):
    bundle = initial(tmp_path)
    bundle["ai_policy"].update(
        prompt_version=policy.LEGACY_AI_VERSION,
        variant=policy.LEGACY_AI_VARIANT,
        system_prompt=policy.auxiliary_prompt(bundle["historical_context"]),
    )
    bundle["ai_policy"]["system_prompt_sha256"] = policy.digest(
        bundle["ai_policy"]["system_prompt"]
    )
    bundle["bundle_sha256"] = policy.digest(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    calibration._atomic_write_json(
        policy.root(tmp_path) / "policy_2026-09-14.json", bundle
    )

    loaded = policy.load(data_root=tmp_path, target_date="2026-09-14")

    assert loaded["ai_policy"]["prompt_version"] == policy.LEGACY_AI_VERSION
    assert "Historical policy context" in loaded["ai_policy"]["system_prompt"]


def test_frozen_compact_v1_bundle_remains_readable(tmp_path):
    bundle = initial(tmp_path)
    bundle["ai_policy"].update(
        prompt_version=policy.LEGACY_COMPACT_AI_VERSION,
        variant=policy.LEGACY_COMPACT_AI_VARIANT,
        system_prompt=policy.compact_auxiliary_prompt(
            prompt_version=policy.LEGACY_COMPACT_AI_VERSION
        ),
    )
    bundle["ai_policy"]["system_prompt_sha256"] = policy.digest(
        bundle["ai_policy"]["system_prompt"]
    )
    bundle["bundle_sha256"] = policy.digest(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    calibration._atomic_write_json(
        policy.root(tmp_path) / "policy_2026-09-14.json", bundle
    )

    loaded = policy.load(data_root=tmp_path, target_date="2026-09-14")

    assert loaded["ai_policy"]["prompt_version"] == policy.LEGACY_COMPACT_AI_VERSION


@pytest.mark.parametrize(
    "version,expected_hash",
    [
        (
            "entry_machine_auxiliary_compact_v2",
            "61db6c6864ac1c9f77f785cb6b18f64dc8aba25e20f8e51567c8cf6b8ac82491",
        ),
        (
            "entry_machine_auxiliary_compact_opportunity_v1",
            "d6f774047e7d4d1a4c41b0d40740a4dd713a0fbcdb7497cde6a501e2fd9f95fe",
        ),
        (
            "entry_machine_auxiliary_compact_risk_v1",
            "7416560b3722e3d1ab06d0d9d9564ce7d27a1bd8cb6711062fe23773ccfb95a9",
        ),
    ],
)
def test_frozen_compact_citations_migrate_only_next_date(
    tmp_path, version, expected_hash
):
    bundle = initial(tmp_path)
    prompt = policy.compact_auxiliary_prompt(prompt_version=version)
    assert hashlib.sha256(prompt.encode()).hexdigest() == expected_hash
    bundle["ai_policy"].update(
        prompt_version=version,
        variant=policy.compact_prompt_variant(version),
        system_prompt=prompt,
        system_prompt_sha256=policy.digest(prompt),
    )
    bundle["bundle_sha256"] = policy.digest(
        {key: value for key, value in bundle.items() if key != "bundle_sha256"}
    )
    frozen_path = policy.root(tmp_path) / "policy_2026-09-14.json"
    calibration._atomic_write_json(frozen_path, bundle)
    before = frozen_path.read_bytes()
    assert policy.load(data_root=tmp_path, target_date="2026-09-14") == bundle
    successor = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 22, tzinfo=policy.KST),
    )
    assert successor["target_date"] == "2026-09-15"
    assert successor["ai_policy"]["prompt_version"] == policy.AI_VERSION
    assert successor["compact_prompt_disposition"] == "compact_contract_migration"
    assert successor["machine_policy"] == bundle["machine_policy"]
    assert frozen_path.read_bytes() == before


@pytest.mark.parametrize(
    "corruption",
    [
        None,
        "rate",
        "preservation",
        "source",
        "bool_count",
        "tail_count",
        "detailed_counts",
    ],
)
def test_natural_direction_without_paired_proof_preserves_compact(
    tmp_path, corruption
):
    previous = initial(tmp_path)
    path = source(tmp_path, "2026-09-14")
    report = json.loads(path.read_text())
    report["hierarchical_entry_quality"] = {
        "machine_decision_case_table": {
            "machine_ai_natural_source_receipt": {
                "source_manifest_sha256": "d" * 64,
                "tuning_input_allowed": True,
            },
            "compact_auxiliary_policy_measurement": {"measurement_allowed": True},
            "compact_auxiliary_screen_outcomes": {
                "economic_contract": {
                    "schema": "compact_auxiliary_economic_selection_v2",
                    "economic_eligible_count": 20,
                    "screened_total": 20,
                    "denominator_preserved": True,
                    "exclusion_counts": {},
                    "evaluable_veto_count": 5,
                    "evaluable_pass_count": 15,
                    "missed_profit_veto_count": 5,
                    "dangerous_pass_count": 1,
                    "missed_veto_rate": 1.0,
                    "dangerous_pass_rate": 0.06666666666666667,
                    "counterfactual_not_realized_pnl": True,
                    "missing_economics_imputed": False,
                    "material_tail_loss_pct": -1.0,
                    "material_tail_pass_count": 0,
                    "missed_profit_veto_net_sum_pct": 1.0,
                    "dangerous_pass_loss_sum_pct": 0.5,
                    "verdict_x_action_neutral_outcome_counts": {
                        "PASS|CLEAN_FAST_LOSS_OR_ADVERSE": 1,
                        "PASS|CLEAN_FAST_PROFIT": 14,
                        "VETO|CLEAN_FAST_PROFIT": 5,
                    },
                },
                "automatic_successor_selection": {
                    "recommendation_id": (
                        "compact_auxiliary_prompt_automatic_successor_v2"
                    ),
                    "contract_version": "compact_auxiliary_economic_selection_v2",
                    "eligible": True,
                    "runtime_effect": True,
                    "allowed_runtime_apply": True,
                    "selection_contract": (
                        "bounded_registered_variant_exact_incumbent_only_no_freeform_edit"
                    ),
                    "incumbent_prompt_version": policy.AI_VERSION,
                    "selected_prompt_version": (
                        policy.ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION
                    ),
                    "minimum_economic_eligible_count": 20,
                    "minimum_error_count": 3,
                    "minimum_relevant_denominator": 5,
                    "minimum_error_rate": 0.25,
                    "minimum_rate_margin": 0.10,
                    "source_manifest_sha256": "d" * 64,
                },
            },
        }
    }
    economic = report["hierarchical_entry_quality"]["machine_decision_case_table"][
        "compact_auxiliary_screen_outcomes"
    ]["economic_contract"]
    outcome_hash = policy.digest(economic["verdict_x_action_neutral_outcome_counts"])
    economic["verdict_x_action_neutral_outcome_counts_sha256"] = outcome_hash
    if corruption == "rate":
        economic["missed_veto_rate"] = 0.9
    elif corruption == "preservation":
        economic["screened_total"] = 21
    elif corruption == "source":
        report["hierarchical_entry_quality"]["machine_decision_case_table"][
            "machine_ai_natural_source_receipt"
        ]["tuning_input_allowed"] = False
    elif corruption == "bool_count":
        economic["dangerous_pass_count"] = True
    elif corruption == "tail_count":
        economic["material_tail_pass_count"] = 16
    elif corruption == "detailed_counts":
        economic["verdict_x_action_neutral_outcome_counts"] = {
            "PASS|CLEAN_FAST_PROFIT": 20
        }
        outcome_hash = policy.digest(
            economic["verdict_x_action_neutral_outcome_counts"]
        )
        economic["verdict_x_action_neutral_outcome_counts_sha256"] = outcome_hash
    report["hierarchical_entry_quality"]["machine_decision_case_table"][
        "compact_auxiliary_screen_outcomes"
    ]["automatic_successor_selection"]["economic_outcome_counts_sha256"] = outcome_hash
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )

    successor = policy.publish(
        path,
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST),
    )

    assert successor["previous_bundle_sha256"] == previous["bundle_sha256"]
    if corruption is not None:
        assert (
            successor["ai_policy"]["prompt_version"]
            == previous["ai_policy"]["prompt_version"]
        )
        return
    assert successor["ai_policy"]["prompt_version"] == (
        policy.AI_VERSION
    )
    assert successor["ai_policy"]["variant"] == policy.compact_prompt_variant(
        successor["ai_policy"]["prompt_version"]
    )
    assert successor["ai_policy"]["system_prompt"] == policy.compact_auxiliary_prompt(successor["historical_context"], prompt_version=policy.AI_VERSION)
    # A later source still evaluates the policy used today, not tomorrow's
    # unlaunched opportunity candidate. It must be able to replace that draft.
    economic["material_tail_pass_count"] = 1
    selection = report["hierarchical_entry_quality"]["machine_decision_case_table"][
        "compact_auxiliary_screen_outcomes"
    ]["automatic_successor_selection"]
    selection["selected_prompt_version"] = (
        policy.ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION
    )
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    revised = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 14, 22, tzinfo=policy.KST)
    )
    assert (
        revised["ai_policy"]["prompt_version"]
        == policy.AI_VERSION
    )
    assert (
        policy.load(data_root=tmp_path, target_date="2026-09-14")["bundle_sha256"]
        == previous["bundle_sha256"]
    )
    economic["material_tail_pass_count"] = 0
    selection["selected_prompt_version"] = (
        policy.AI_VERSION
    )
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    frozen = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 15, 8, tzinfo=policy.KST)
    )
    assert frozen["bundle_sha256"] == revised["bundle_sha256"]


@pytest.mark.parametrize(
    "veto_count,pass_count,missed,loss,expected",
    [
        (20, 0, 1.4, 0.0, "select_opportunity_preservation_variant"),
        (0, 20, 0.0, 2.0, "select_material_risk_specificity_variant"),
        (5, 15, 0.35, 0.93, "carry_balanced_compact_contract"),
    ],
)
def test_compact_direction_uses_cost_magnitudes_and_defined_single_sided_rates(
    veto_count, pass_count, missed, loss, expected
):
    dangerous = min(pass_count, 5) if not veto_count else min(pass_count, 1)
    economic = {
        "economic_eligible_count": 20,
        "evaluable_veto_count": veto_count,
        "evaluable_pass_count": pass_count,
        "missed_profit_veto_count": min(veto_count, 5),
        "dangerous_pass_count": dangerous,
        "material_tail_pass_count": 0,
        "missed_veto_rate": min(veto_count, 5) / veto_count if veto_count else None,
        "dangerous_pass_rate": dangerous / pass_count if pass_count else None,
        "missed_profit_veto_net_sum_pct": missed,
        "dangerous_pass_loss_sum_pct": loss,
    }
    assert policy.compact_economic_direction(economic) == expected


def test_next_preopen_publish_replaces_legacy_prompt_without_threshold_change(tmp_path):
    legacy = initial(tmp_path)
    legacy["ai_policy"].update(
        prompt_version=policy.LEGACY_AI_VERSION,
        variant=policy.LEGACY_AI_VARIANT,
        system_prompt=policy.auxiliary_prompt(legacy["historical_context"]),
    )
    legacy["ai_policy"]["system_prompt_sha256"] = policy.digest(
        legacy["ai_policy"]["system_prompt"]
    )
    legacy["bundle_sha256"] = policy.digest(
        {key: value for key, value in legacy.items() if key != "bundle_sha256"}
    )
    calibration._atomic_write_json(
        policy.root(tmp_path) / "policy_2026-09-14.json", legacy
    )

    successor = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST),
    )

    assert successor["target_date"] == "2026-09-15"
    assert successor["machine_policy"] == legacy["machine_policy"]
    assert successor["previous_bundle_sha256"] == legacy["bundle_sha256"]
    assert successor["ai_policy"]["prompt_version"] == policy.AI_VERSION
    assert successor["ai_policy"]["system_prompt"] == policy.compact_auxiliary_prompt()


@pytest.mark.parametrize("corruption", [None, "count", "contract_version", "partition", "nan_amount", "terminal_gate"])
def test_router_caution_without_paired_proof_preserves_compact(tmp_path, corruption):
    from src.tests.test_ai_action_outcome_calibration import _compact_router_case_table
    previous = initial(tmp_path)
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    table = _compact_router_case_table()
    outcome = table["compact_auxiliary_screen_outcomes"]
    if corruption == "count":
        outcome["economic_contract"]["evaluable_caution_count"] -= 1
    elif corruption == "contract_version":
        outcome["automatic_successor_selection"]["contract_version"] = "compact_auxiliary_economic_selection_v2"
    elif corruption == "partition":
        table["compact_auxiliary_policy_measurement"]["measurement_allowed"] = False
    elif corruption == "nan_amount":
        outcome["economic_contract"]["missed_profit_caution_net_sum_pct"] = float("nan")
    elif corruption == "terminal_gate":
        table["machine_ai_natural_source_receipt"]["machine_terminal_tuning_gate"]["decision_counterfactual_tuning_input_allowed"] = False
    report["hierarchical_entry_quality"] = {"machine_decision_case_table": table}
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(path, calibration._with_artifact_content_sha256(report))
    successor = policy.publish(path, data_root=tmp_path, now=datetime(2026, 9, 15, 21, tzinfo=policy.KST))
    assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["ai_policy"]["prompt_version"] == (policy.AI_VERSION)
    assert "model" not in successor["ai_policy"]
    assert "provider" not in successor["ai_policy"]


@pytest.mark.parametrize("corruption", [None, "unlocated", "duplicate", "missing", "learned", "count_bool"])
def test_localized_conflict_does_not_replace_missing_paired_proof(tmp_path, corruption):
    from src.tests.test_ai_action_outcome_calibration import _compact_conflict_case_table

    previous = initial(tmp_path)
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    table = _compact_conflict_case_table()
    if corruption == "unlocated":
        table["conflict_locations_complete"] = False
    elif corruption == "duplicate":
        table["conflicting_evaluation_keys"] *= 2
    elif corruption == "missing":
        table.pop("conflicting_evaluation_keys")
    elif corruption == "learned":
        table["policy_learning_exact_enter_keys"].extend(table["conflicting_evaluation_keys"])
    elif corruption == "count_bool":
        table["conflicting_attempt_identity_count"] = True
    report["hierarchical_entry_quality"] = {"machine_decision_case_table": table}
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(path, calibration._with_artifact_content_sha256(report))
    successor = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 15, 21, tzinfo=policy.KST)
    )
    assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["ai_policy"]["prompt_version"] == (
        policy.AI_VERSION
    )
    assert "model" not in successor["ai_policy"]
    assert "provider" not in successor["ai_policy"]


def test_all_continuous_adoption_carry_and_exact_scope_projection(tmp_path):
    from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES

    legacy = initial(tmp_path)
    assert policy.for_cohort(legacy, ("NXT", "NXT_AFTERMARKET")) is None
    bundle = policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        adopt_all_continuous=True,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 13, 22, tzinfo=policy.KST),
    )
    assert set(bundle["scope_policies"]) == set(AUTO_PROMOTION_SCOPES)
    policy.validate(bundle, target_date="2026-09-14")
    for scope in AUTO_PROMOTION_SCOPES:
        projected = policy.for_cohort(bundle, tuple(scope.split("|")))
        assert projected["historical_context"]["scope"] == scope
        assert (
            projected["machine_policy"] == policy.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
        )
    assert policy.for_cohort(bundle, ("KRX", "CLOSING_AUCTION")) is None
    carried = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 22, tzinfo=policy.KST),
    )
    assert carried["all_continuous_adopted"] is True
    assert set(carried["scope_policies"]) == set(AUTO_PROMOTION_SCOPES)
    del carried["scope_policies"]["NXT|NXT_AFTERMARKET"]
    carried["bundle_sha256"] = policy.digest(
        {k: v for k, v in carried.items() if k != "bundle_sha256"}
    )
    with pytest.raises(ValueError, match="coverage"):
        policy.validate(carried, target_date="2026-09-15")


def test_hierarchy_adoption_is_explicit_and_preserves_existing_daily_freeze(tmp_path):
    before = initial(tmp_path)
    after = policy.publish(
        source(tmp_path),
        data_root=tmp_path,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 13, 21, tzinfo=policy.KST),
    )
    assert after["hierarchy_adopted"] is True
    assert after["historical_context"]["hierarchy_disposition"] == (
        "adopted_no_qualified_child"
    )
    assert after["machine_policy"] == before["machine_policy"]
    assert after["bundle_sha256"] != before["bundle_sha256"]
    assert (
        policy.root(tmp_path) / "generations" / f"{before['bundle_sha256']}.json"
    ).is_file()
    assert (
        policy.publish(
            source(tmp_path),
            data_root=tmp_path,
            now=datetime(2026, 9, 14, 8, tzinfo=policy.KST),
        )
        == after
    )


def test_hierarchy_child_cannot_be_loaded_without_adoption(tmp_path):
    bundle = initial(tmp_path)
    machine = bundle["machine_policy"]
    machine["hierarchy"] = {
        "schema": "mechanistic_entry_hierarchy_v1",
        "parent_sha256": policy.digest(machine["thresholds"]),
        "rules": [],
    }
    bundle["bundle_sha256"] = policy.digest(
        {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    )
    with pytest.raises(ValueError, match="adoption_missing"):
        policy.validate(bundle, target_date="2026-09-14")


def test_qualified_hierarchy_publishes_loads_and_automatically_carries(tmp_path):
    from src.tests.test_ai_action_outcome_calibration import _hierarchy_training_rows

    initial(tmp_path)
    path = source(tmp_path, "2026-09-15")
    report = json.loads(path.read_text())
    report["hierarchical_entry_quality"] = {
        "runtime_extension": calibration.build_mechanistic_hierarchy_candidate(
            _hierarchy_training_rows(), target_date="2026-09-15"
        )
    }
    report.pop("artifact_content_sha256")
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    unadopted = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 15, 21, tzinfo=policy.KST)
    )
    assert "hierarchy" not in unadopted["machine_policy"]
    adopted = policy.publish(
        path,
        data_root=tmp_path,
        adopt_hierarchy=True,
        now=datetime(2026, 9, 15, 22, tzinfo=policy.KST),
    )
    assert adopted["machine_policy"]["hierarchy"]["rules"]
    assert "WAIT_CONFIRMATION" in adopted["ai_policy"]["system_prompt"]
    assert policy.load(data_root=tmp_path, target_date="2026-09-16") == adopted
    carried = policy.publish(
        source(tmp_path, "2026-09-16"),
        data_root=tmp_path,
        now=datetime(2026, 9, 16, 21, tzinfo=policy.KST),
    )
    assert carried["machine_policy"] == adopted["machine_policy"]
    assert carried["hierarchy_adopted"] is True


@pytest.mark.parametrize(
    "explicit,late,corrupt",
    [
        (False, False, False),
        (True, True, False),
        (True, False, True),
        (True, False, False),
    ],
)
def test_legacy_initial_role_replacement_is_explicit_frozen_and_preserved(
    tmp_path, explicit, late, corrupt
):
    old = copy.deepcopy(initial(tmp_path))
    old["role_contract"]["ai_role"] = "auxiliary_advisory_no_veto_no_override"
    old["role_contract"]["ai_can_veto_entry"] = False
    old["role_contract"]["decision_precedence"][-1] = "ai_auxiliary_advisory"
    old["ai_policy"]["variant"] = "machine_first_auxiliary_v1"
    old["ai_policy"]["system_prompt"] = "Historical nonbinding advisory prompt."
    old["ai_policy"]["system_prompt_sha256"] = policy.digest(
        old["ai_policy"]["system_prompt"]
    )
    old["bundle_sha256"] = policy.digest(
        {k: v for k, v in old.items() if k != "bundle_sha256"}
    )
    if corrupt:
        old["ai_policy"]["system_prompt"] = "corrupt"
    calibration._atomic_write_json(
        policy.root(tmp_path) / "policy_2026-09-14.json", old
    )
    args = dict(
        data_root=tmp_path,
        replace_initial_role=explicit,
        now=(
            datetime(2026, 9, 14, 8, tzinfo=policy.KST)
            if late
            else datetime(2026, 9, 13, 22, tzinfo=policy.KST)
        ),
    )
    if not explicit or late or corrupt:
        with pytest.raises(ValueError):
            policy.publish(source(tmp_path), **args)
    else:
        new = policy.publish(source(tmp_path), **args)
        assert new["role_contract"]["ai_can_veto_entry"] is True
        assert new["previous_bundle_sha256"] == old["bundle_sha256"]
        assert new["machine_policy"] == old["machine_policy"]
        assert (
            new["machine_disposition"]
            == "initial_role_corrected_not_performance_promotion"
        )
        assert (
            policy.root(tmp_path) / "generations" / f"{old['bundle_sha256']}.json"
        ).is_file()


def test_daily_no_candidate_carries_machine_and_refreshes_ai_context(tmp_path):
    previous = initial(tmp_path)
    successor = policy.publish(
        source(tmp_path, "2026-09-14"),
        data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST),
    )
    assert successor["target_date"] == "2026-09-15"
    assert successor["machine_policy"] == previous["machine_policy"]
    assert successor["previous_bundle_sha256"] == previous["bundle_sha256"]
    # The compact role is intentionally immutable; daily historical metadata
    # must not be spliced into the executed prompt.
    assert (
        successor["ai_policy"]["system_prompt_sha256"]
        == previous["ai_policy"]["system_prompt_sha256"]
    )
    assert successor["historical_context"] != previous["historical_context"]
    assert successor["ai_policy"]["prompt_version"] == policy.AI_VERSION
    assert successor["ai_policy"]["variant"] == policy.AI_VARIANT
    assert successor["machine_disposition"] == "incumbent_carried"


def test_existing_date_is_immutable_even_after_source_refresh(tmp_path):
    first = initial(tmp_path)
    path = source(tmp_path)
    updated = json.loads(path.read_text())
    updated["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(updated)
    )
    assert (
        policy.publish(
            path, data_root=tmp_path, now=datetime(2026, 9, 14, 10, tzinfo=policy.KST)
        )
        == first
    )


def test_late_postclose_can_refresh_before_preopen_and_preserves_generation(tmp_path):
    previous = initial(tmp_path)
    path = source(tmp_path)
    report = json.loads(path.read_text())
    report["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    calibration._atomic_write_json(
        path, calibration._with_artifact_content_sha256(report)
    )
    successor = policy.publish(
        path, data_root=tmp_path, now=datetime(2026, 9, 13, 22, tzinfo=policy.KST)
    )
    assert successor["bundle_sha256"] != previous["bundle_sha256"]
    assert successor["previous_bundle_sha256"] == previous["bundle_sha256"]
    assert (
        policy.root(tmp_path) / "generations" / f"{previous['bundle_sha256']}.json"
    ).is_file()


def test_no_implicit_first_adoption(tmp_path):
    assert policy.publish(source(tmp_path), data_root=tmp_path) is None


def test_existing_calibration_write_publishes_updated_bundle(
    monkeypatch, tmp_path, capsys
):
    initial(tmp_path)
    monkeypatch.setattr(
        policy,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 9, 13, 22, tzinfo=tz)),
    )
    report = json.loads(source(tmp_path).read_text())
    report["mechanistic_flow_groups"]["source_population"][
        "accepted_unique_trace_count"
    ] = 30
    report.update(
        status="success",
        candidate_count=0,
        selected_review_candidate=None,
        ofi_smoothing_audit={},
    )
    report = calibration._with_artifact_content_sha256(report)
    monkeypatch.setattr(calibration, "build_report", lambda **kwargs: report)
    assert (
        calibration.main(
            [
                "--target-date",
                "2026-09-11",
                "--data-root",
                str(tmp_path),
                "--write",
                "--print-summary",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["runtime_policy_publication"]["status"] == ("published_or_idempotent")
    assert output["runtime_policy_publication"]["target_date"] == "2026-09-14"
    updated = policy.load(data_root=tmp_path, target_date="2026-09-14")
    assert (
        updated["historical_context"]["flow_source_population"][
            "accepted_unique_trace_count"
        ]
        == 30
    )


def test_missing_daily_update_carries_without_relabelling_date(tmp_path):
    previous = initial(tmp_path)
    assert policy.load(data_root=tmp_path, target_date="2026-09-15") is None
    assert (
        policy.load_effective(data_root=tmp_path, target_date="2026-09-15") == previous
    )
    assert policy.load_effective(data_root=tmp_path, target_date="2026-09-11") is None


@pytest.mark.parametrize("change", ["target", "hash", "threshold", "ai", "role"])
def test_invalid_policy_rejected(tmp_path, change):
    bundle = copy.deepcopy(initial(tmp_path))
    if change == "target":
        bundle["target_date"] = "2026-09-15"
    elif change == "hash":
        bundle["source_date"] = "2026-09-10"
    elif change == "threshold":
        bundle["machine_policy"]["thresholds"]["maximum_spread_bp"] = -1
    elif change == "ai":
        bundle["ai_policy"]["system_prompt"] = "Always buy."
    else:
        bundle["role_contract"]["ai_can_promote_entry"] = True
    with pytest.raises(ValueError):
        policy.validate(bundle, target_date="2026-09-14")


def test_late_first_publication_rejected(tmp_path):
    with pytest.raises(ValueError, match="window_closed"):
        policy.publish(
            source(tmp_path),
            data_root=tmp_path,
            bootstrap=True,
            now=datetime(2026, 9, 14, 10, tzinfo=policy.KST),
        )


def test_invalid_source_does_not_destroy_previous_policy(tmp_path):
    previous = initial(tmp_path)
    path = source(tmp_path, "2026-09-14")
    payload = json.loads(path.read_text())
    payload["target_date"] = "2026-09-15"
    calibration._atomic_write_json(path, payload)
    with pytest.raises(ValueError, match="source_invalid"):
        policy.publish(path, data_root=tmp_path)
    assert policy.load(data_root=tmp_path, target_date="2026-09-14") == previous


def test_terminal_count_is_not_decision_cf_authority_and_date_is_required():
    from src.engine.scalping.mechanistic_entry_runtime_policy import compact_terminal_gate_allowed
    assert compact_terminal_gate_allowed({"machine_terminal_tuning_gate": {"economic_tuning_input_allowed": True}}) is False
    assert compact_terminal_gate_allowed({"target_date": "2026-09-17", "machine_terminal_tuning_gate": {"economic_tuning_input_allowed": True}}) is False
    assert compact_terminal_gate_allowed({"target_date": "2026-09-17", "machine_terminal_tuning_gate": {
        "decision_counterfactual_tuning_input_allowed": True, "lineage_gap_excluded_count": 4}}) is True


@pytest.mark.parametrize("joint", [False, True])
def test_scoped_common_candidate_uses_own_incumbent_when_krx_has_no_candidate(tmp_path, monkeypatch, joint):
    from src.engine.scalping import entry_setup_live_policy as activation
    previous = policy.publish(source(tmp_path), data_root=tmp_path, bootstrap=True,
        adopt_all_continuous=True, now=datetime(2026, 9, 13, 20, tzinfo=policy.KST))
    scope = "NXT|NXT_AFTERMARKET"
    parent = previous["scope_policies"][scope]["machine_policy"]
    successor = copy.deepcopy(parent)
    successor["thresholds"]["maximum_spread_bp"] = 40.0
    def projection(*a, cohort=("KRX", "KRX_REGULAR"), **kw):
        if "|".join(cohort) != scope:
            return None, []
        return {"threshold_policy": successor,
                "incumbent_machine_policy_sha256": policy.digest(parent)}, []
    monkeypatch.setattr(activation, "_mechanistic_primary_activation_projection", projection)
    path = source(tmp_path, "2026-09-14")
    if joint:
        report = json.loads(path.read_text())
        report.pop("artifact_content_sha256")
        report.update(report_scope="main_mechanistic_entry", mechanistic_refinements_by_scope={
            k: {"policy_candidate": {"fixture": "projection_mocked_above"}} for k in (scope, "NXT|NXT_PREMARKET")})
        calibration._atomic_write_json(path, calibration._with_artifact_content_sha256(report))
    result = policy.publish(path, data_root=tmp_path,
        now=datetime(2026, 9, 14, 21, tzinfo=policy.KST))
    assert result["machine_policy"] == previous["machine_policy"]
    assert result["scope_policies"][scope]["machine_policy"] == (parent if joint else successor)
    assert result["scope_policies"][scope]["machine_disposition"] == (
        "joint_scope_capital_replay_required_incumbent_carried" if joint else "evidence_qualified_exact_scope_common_update")
    assert result["scope_policies"][scope]["ai_policy"]["prompt_version"] == previous["scope_policies"][scope]["ai_policy"]["prompt_version"]
    assert policy.load(data_root=tmp_path, target_date="2026-09-15") == result
