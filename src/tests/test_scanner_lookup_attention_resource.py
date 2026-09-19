from copy import deepcopy
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping import scanner_lookup_attention_resource as resource
from src.engine.scalping import scanner_lookup_attention_policy as policy


def pair_rows(
    day=date(2026, 9, 9), minute=30, *, incoming_return=2.0, outgoing_return=0.5
):
    anchor = datetime(
        day.year, day.month, day.day, 9, minute, tzinfo=ZoneInfo("Asia/Seoul")
    ).timestamp()
    result = []
    for label in (False, True):
        epoch = anchor + (240 if label else 0)
        for code, high in (("100000", False), ("200000", True)):
            score = 0.9 if high and not label else 0.0
            base = 990.0 if high else 1000.0
            row = {
                "contract_version": policy.RESOURCE_PAIR_CONTRACT_VERSION,
                "observation_date": day.isoformat(),
                "scan_generation_id": f"SCANGEN-{epoch}",
                "stock_code": code,
                "scan_rank": 2 if high else 1,
                "ranked_candidate_count": 2,
                "rank_partition": 0,
                "priority_tier": "tier_b_price_jump_candidate",
                "watch_budget_owner": "general_scalping",
                "market_gainer_partition": False,
                "reserved_partition": "general",
                "source_priority": 1,
                "flu_rate": 2.0,
                "base_priority_score": base,
                "actual_priority_score": base,
                "candidate_priority_score": base + policy.bonus_points_for_score(score),
                "lookup_attention_snapshot_score": score,
                "counterfactual_bonus_points": policy.bonus_points_for_score(score),
                "partition_count": 2,
                "partition_codes_sha256": policy.canonical_sha256(["100000", "200000"]),
                "eligibility_pass": True,
                "eligibility_reason": "existing_guards_pass",
                "simple_capacity": True,
                "observed_epoch": epoch,
                "price_observed_epoch": epoch - 1,
                "price": (
                    10000.0 * (1 + (incoming_return if high else outgoing_return) / 100)
                    if label
                    else 10000.0
                ),
                "terminal": "promoted" if not label and not high else "pruned",
                "prune_reason": "max_new_codes_reached" if label or high else "",
                "eligible_source": True,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            }
            result.append(row)
    return result


def ready_resource_rows():
    return pair_rows() + pair_rows(minute=40) + pair_rows(day=date(2026, 9, 10))


def book(rows, **kwargs):
    return resource.allocation_book(
        rows, capacity_reasons={"max_new_codes_reached"}, **kwargs
    )


def test_non_lookup_control_swap_is_labelled_without_20_generation_hurdle():
    result = book(ready_resource_rows())
    assert result["ready_for_live_gate"] is True
    assert result["paired_generation_count"] == 3
    assert result["resolved_pair_count"] == 3
    assert result["resolved_date_count"] == 2
    assert result["source_quality_adjusted_ev_pct"] > 0
    assert result["pairs"][0]["outgoing_code"] == "100000"


def test_missing_resource_contract_is_not_an_authority_or_parser_crash():
    assert resource.event_row({"fields": "malformed"}) is None
    assert resource.event_row({}) is None


def test_negative_marginal_return_cannot_pass_on_positive_population_ev():
    rows = (
        pair_rows(incoming_return=-1)
        + pair_rows(minute=40, incoming_return=-1)
        + pair_rows(day=date(2026, 9, 10), incoming_return=-1)
    )
    result = book(rows)
    assert result["status"] == "hold_no_edge"
    assert result["ready_for_live_gate"] is False


def test_zero_bonus_population_is_no_effect_not_infinite_sample_wait():
    rows = pair_rows()
    for row in rows:
        row["lookup_attention_snapshot_score"] = 0.0
        row["counterfactual_bonus_points"] = 0.0
        row["candidate_priority_score"] = row["base_priority_score"]
    assert book(rows)["status"] == "hold_no_effect"


def test_missing_competitor_or_failed_admission_is_not_a_swap():
    rows = pair_rows()
    assert book(rows[1:])["resolved_pair_count"] == 0
    rows[1]["eligibility_pass"] = False
    rows[1]["eligibility_reason"] = "non_positive_rising_start"
    assert book(rows)["counterfactual_moved_in_count"] == 0


def test_actual_selection_must_match_replay():
    rows = pair_rows()
    rows[0]["terminal"], rows[1]["terminal"] = "pruned", "promoted"
    rows[0]["prune_reason"] = "max_new_codes_reached"
    assert (
        book(rows)["excluded_partition_counts"]["actual_selection_not_reproduced"] == 1
    )


def test_bad_partition_does_not_block_other_valid_pairs():
    broken = pair_rows(minute=50)
    broken[1]["base_priority_score"] = None
    result = book(ready_resource_rows() + broken, invalid_row_count=1)
    assert result["ready_for_live_gate"] is True
    assert result["excluded_partition_counts"]["invalid_partition"] == 1


def test_malformed_natural_pair_identity_quarantines_its_partition():
    rows = pair_rows()
    rows[0].update(
        scanner_selection_pair_id="bad",
        scanner_selection_pair_contract_version=(
            "scanner_lookup_attention_selection_pair_v1"
        ),
        scanner_selection_pair_role="outgoing",
        scanner_selection_pair_assignment="baseline",
    )
    result = book(rows)
    assert result["resolved_pair_count"] == 0
    assert result["excluded_partition_counts"]["invalid_partition"] == 1


def test_partial_natural_pair_identity_is_not_treated_as_a_complete_pair():
    rows = pair_rows()
    pair_id = "a" * 64
    rows[0].update(
        scanner_selection_pair_id=pair_id,
        scanner_selection_pair_contract_version=(
            "scanner_lookup_attention_selection_pair_v1"
        ),
        scanner_selection_pair_role="incoming",
        scanner_selection_pair_assignment="baseline",
    )
    result = book(rows)
    assert result["resolved_pair_count"] == 0
    assert result["excluded_partition_counts"]["selection_pair_identity_conflict"] == 1


def test_labels_are_not_synthesized_or_taken_from_different_generations():
    rows = pair_rows()
    rows[3]["scan_generation_id"] += "-other"
    result = book(rows)
    assert result["resolved_pair_count"] == 0
    assert result["unobserved_pair_count"] == 1


def test_overlapping_pairs_do_not_multiply_evidence():
    rows = pair_rows() + pair_rows(minute=31)
    assert book(rows)["resolved_pair_count"] == 1


def test_causal_sample_alone_cannot_enable_real_policy():
    from src.engine.monitoring import scanner_lookup_attention_tuning as tuning

    result = tuning.decide_promotion(
        date(2026, 9, 11),
        tuning._cohort_book([]),
        [],
        source_quality_pass=True,
        resource_allocation_ready=book(ready_resource_rows())["ready_for_live_gate"],
    )
    assert result["status"] == "hold_sample"


def test_frozen_base_survives_rolling_window_expiration():
    from src.engine.monitoring import scanner_lookup_attention_tuning as tuning
    from src.tests.test_scanner_lookup_attention_tuning import _passing_rows

    base = _passing_rows(date(2026, 9, 2))
    campaign = tuning._freeze_base(base, "2026-09-08")
    prior = {
        "status": "forward_holdout_armed",
        "target_date": "2026-12-14",
        "holdout_armed_since": "2026-09-08",
        "campaign_base": campaign,
    }
    future = _passing_rows(date(2026, 12, 7), id_start=10000)
    frozen = tuning._base_rows_for_prior(future, prior)
    assert frozen == base
    result = tuning.decide_promotion(
        date(2026, 12, 14),
        tuning._cohort_book(frozen),
        future,
        source_quality_pass=True,
        prior_policy=prior,
    )
    assert result["status"] == "live_auto_apply_ready"
    broken = deepcopy(prior)
    broken["campaign_base"]["outcomes"][0]["net_return_pct"] = 999
    assert tuning._base_rows_for_prior(future, broken) == []


def test_preopen_freezes_policy_and_survives_previous_source_overwrite(tmp_path):
    from src.tests.test_scanner_lookup_attention_tuning import _write_live_pair

    _write_live_pair(tmp_path, date(2026, 9, 17))
    target = date(2026, 9, 18)
    now = datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul"))
    receipt = policy.freeze_preopen_policy(
        target,
        write=True,
        now=now,
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
        applied_dir=tmp_path / "applied",
    )
    assert receipt["active"] is False
    loaded = policy.load_active_policy(target, applied_dir=tmp_path / "applied")
    (
        tmp_path / "policies" / "scanner_lookup_attention_policy_2026-09-17.json"
    ).write_text("{}")
    policy.clear_policy_cache()
    assert policy.load_active_policy(target, applied_dir=tmp_path / "applied") == loaded
    second = policy.freeze_preopen_policy(
        target,
        write=True,
        now=now + timedelta(hours=4),
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
        applied_dir=tmp_path / "applied",
    )
    assert second == receipt
    assert (
        policy.load_active_policy(date(2026, 9, 21), applied_dir=tmp_path / "applied")[
            "active"
        ]
        is False
    )


def test_no_intraday_first_preopen_activation(tmp_path):
    with pytest.raises(ValueError, match="outside_target_date_window"):
        policy.freeze_preopen_policy(
            date(2026, 9, 18),
            write=True,
            now=datetime(2026, 9, 18, 10, tzinfo=ZoneInfo("Asia/Seoul")),
            applied_dir=tmp_path,
        )


def test_compaction_keeps_complete_replay_proofs_and_same_economics():
    rows = ready_resource_rows()
    for index in range(300):
        extra = pair_rows(minute=50)
        for row in extra:
            row["scan_generation_id"] += f"-extra-{index}"
            row["counterfactual_bonus_points"] = 0.0
            row["lookup_attention_snapshot_score"] = 0.0
            row["candidate_priority_score"] = row["base_priority_score"]
        rows.extend(extra)
    compact, diagnostics = resource.compact_evidence_rows(
        rows, capacity_reasons={"max_new_codes_reached"}
    )
    assert diagnostics["raw_row_count"] == len(rows)
    assert len(compact) == 12
    for key in ("pairs", "ready_for_live_gate", "source_quality_adjusted_ev_pct"):
        assert book(compact)[key] == book(rows)[key]


def test_pair_budget_is_selected_before_future_return_is_known():
    rows = []
    for index in range(resource.MAX_ANCHOR_PAIRS_PER_DATE + 1):
        pair = pair_rows(incoming_return=-1 if index < 32 else 50)
        codes = [f"{100000 + index:06d}", f"{200000 + index:06d}"]
        for row in pair:
            row["scan_generation_id"] += f"-{index}"
            row["stock_code"] = codes[row["stock_code"] == "200000"]
            row["partition_codes_sha256"] = policy.canonical_sha256(codes)
        rows.extend(pair)
    result = book(rows)
    assert result["selected_anchor_pair_count"] == 32
    assert result["resolved_pair_count"] == 32
    assert result["incoming_snapshot_ev_pct"] < 0


def test_preopen_malformed_timezone_or_embedded_source_is_rejected(tmp_path):
    from src.tests.test_scanner_lookup_attention_tuning import _write_live_pair

    _write_live_pair(tmp_path, date(2026, 9, 17))
    receipt = policy.freeze_preopen_policy(
        date(2026, 9, 18), applied_dir=tmp_path / "applied"
    )
    for patch in ({"selected_at": "2026-09-18T08:00:00"}, {"source_policy": []}):
        invalid = {**receipt, **patch}
        invalid["artifact_sha256"] = policy.canonical_sha256(
            {key: value for key, value in invalid.items() if key != "artifact_sha256"}
        )
        assert not policy.validate_preopen_receipt(invalid, date(2026, 9, 18))


def test_source_only_eligibility_failure_and_zero_bonus_do_not_raise(monkeypatch):
    from src.scanners import scalping_scanner as scanner

    def unexpected(*args, **kwargs):
        raise RuntimeError("injected read-only precheck failure")

    monkeypatch.setattr(scanner, "_scanner_candidate_pre_filter_reason", unexpected)
    target = {
        "Code": "005930",
        "Price": 70000,
        "_ScannerRankPriorityProfile": {
            "lookup_attention_counterfactual_bonus_points": 100,
        },
    }
    scanner._prepare_lookup_resource_evidence(None, [target], {}, 1, 0, None)
    assert (
        target["_LookupResourceEvidence"]["lookup_attention_resource_eligibility_pass"]
        is False
    )
    assert (
        target["_LookupResourceEvidence"][
            "lookup_attention_resource_eligibility_reason"
        ]
        == "source_only_eligibility_check_failed"
    )
    target["_ScannerRankPriorityProfile"][
        "lookup_attention_counterfactual_bonus_points"
    ] = 0
    scanner._prepare_lookup_resource_evidence(None, [target], {}, 1, 0, None)
    assert (
        target["_LookupResourceEvidence"][
            "lookup_attention_resource_eligibility_reason"
        ]
        == "no_positive_bonus_in_partition"
    )


@pytest.mark.parametrize(
    ("arm", "expected_codes", "runtime_effect"),
    [
        ("baseline", ["100000", "200000"], False),
        ("candidate", ["200000", "100000"], True),
    ],
)
def test_marginal_experiment_binds_one_pair_without_promotion_id(
    arm, expected_codes, runtime_effect
):
    from src.scanners import scalping_scanner as scanner

    seed = "a" * 64

    def target(code, base, candidate, score):
        profile = {
            "scanner_priority_rank_partition": 0,
            "scanner_priority_tier": "tier_b_price_jump_candidate",
            "scanner_priority_source_rank": 1,
            "scanner_priority_flu_rate": 2.0,
            "scanner_priority_market_gainer_partition": False,
            "scanner_priority_reserved_partition": "general",
            "scanner_priority_score_without_lookup_attention": base,
            "scanner_priority_score_with_lookup_attention": candidate,
            "lookup_attention_counterfactual_bonus_points": candidate - base,
            "lookup_attention_weight_experiment_mode": True,
            "lookup_attention_weight_experiment_arm": arm,
            "lookup_attention_weight_experiment_allocation_seed_sha256": seed,
            "lookup_attention_weight_experiment_max_marginal_slots": 1,
        }
        return {
            "Code": code,
            "Source": "PRICE_JUMP_START",
            "FluRate": 2.0,
            "ScannerScanRank": 1 if code == "100000" else 2,
            "ScannerWatchBudgetOwner": scanner.GENERAL_SCALPING,
            "_ScannerRankPriorityProfile": profile,
            "_LookupResourceEvidence": {
                "lookup_attention_resource_eligibility_pass": True,
                "lookup_attention_resource_actual_score": base,
            },
        }

    targets = [target("100000", 1000.0, 1000.0, 0.0), target("200000", 990.0, 1190.0, 0.9)]
    result = scanner._prepare_lookup_selection_pair(
        targets,
        scan_generation_id="SCANGEN-fixture",
        general_slot_limit=1,
        simple_capacity=True,
    )
    assert [row["Code"] for row in result] == expected_codes
    incoming = next(row for row in targets if row["Code"] == "200000")
    outgoing = next(row for row in targets if row["Code"] == "100000")
    assert incoming["_LookupSelectionPairEvidence"]["scanner_selection_pair_id"] == outgoing["_LookupSelectionPairEvidence"]["scanner_selection_pair_id"]
    assert incoming["_LookupSelectionPairEvidence"]["scanner_selection_pair_runtime_effect"] is runtime_effect
    assert "scanner_promotion_id" not in incoming["_LookupSelectionPairEvidence"]


def test_preopen_hash_survives_scanner_event_to_runtime_payload(monkeypatch):
    from src.scanners import scalping_scanner as scanner

    monkeypatch.setattr(scanner, "_scanner_priority_profile", lambda *args: {})
    target = {"Code": "005930", "Name": "Samsung", "Price": 70000}
    payload = scanner._scanner_runtime_target_payload(
        target, {"lookup_attention_weight_preopen_artifact_sha256": "b" * 64}
    )
    assert payload["lookup_attention_weight_preopen_artifact_sha256"] == "b" * 64


def test_invalid_generated_contract_is_not_published(monkeypatch):
    from src.engine.monitoring import scanner_lookup_attention_tuning as tuning

    monkeypatch.setattr(
        "sys.argv", ["tuning", "--target-date", "2026-09-07", "--write"]
    )
    monkeypatch.setattr(tuning, "build_artifacts", lambda target: ({}, {}))
    monkeypatch.setattr(
        tuning,
        "validate_artifact_pair",
        lambda *args, **kwargs: ["injected_invalid_contract"],
    )
    published = []
    monkeypatch.setattr(tuning, "write_artifacts", lambda *args: published.append(args))
    assert tuning.main() == 2
    assert published == []


@pytest.mark.parametrize("positive_marginal", [True, False])
def test_builder_to_preopen_auto_apply_requires_real_and_marginal_economics(
    tmp_path, monkeypatch, positive_marginal
):
    from src.engine.monitoring import scanner_lookup_attention_tuning as tuning
    from src.tests.test_scanner_lookup_attention_tuning import (
        _passing_rows,
        _write_live_pair,
    )

    seed = tmp_path / "seed"
    seed.mkdir()
    fixture, _ = _write_live_pair(seed, date(2026, 9, 17))
    base = _passing_rows(date(2026, 9, 2))
    outcomes = base + _passing_rows(date(2026, 9, 9), id_start=10000)
    observations = [
        {
            "observation_date": row["rec_date"],
            "recommendation_id": row["recommendation_id"], "scanner_promotion_id": row.get("scanner_promotion_id", "SCANPROM-fixture"),
            "stock_code": row.get("stock_code", "100000"), "effective_venue": "KRX", "market_session_bucket": "krx_regular",
            "lookup_attention_snapshot_score": (
                0.9 if row["cohort"] == "candidate" else 0.4
            ),
            "fill_class": "full_fill",
        }
        for row in outcomes
    ]
    resources = (
        ready_resource_rows()
        if positive_marginal
        else pair_rows(incoming_return=-1)
        + pair_rows(minute=40, incoming_return=-1)
        + pair_rows(day=date(2026, 9, 10), incoming_return=-1)
    )
    lineage = {
        **fixture["lineage"],
        "window_start": "2026-09-02",
        "_resource_pair_rows": resources,
    }
    monkeypatch.setattr(
        tuning, "collect_lineage", lambda target: (observations, deepcopy(lineage))
    )
    monkeypatch.setattr(tuning, "load_completed_facts", lambda *args: [])
    monkeypatch.setattr(
        tuning, "join_completed_outcomes", lambda *args, **kwargs: (outcomes, {})
    )
    monkeypatch.setattr(
        tuning, "_latest_symbol_master", lambda target: (set(), {"status": "pass"})
    )
    monkeypatch.setattr(tuning, "_source_quality", lambda *args: {"status": "pass"})
    monkeypatch.setattr(
        tuning,
        "_latest_prior_policy",
        lambda target: {
            "status": "forward_holdout_armed",
            "target_date": "2026-09-16",
            "holdout_armed_since": "2026-09-08",
            "campaign_base": tuning._freeze_base(base, "2026-09-08"),
        },
    )
    monkeypatch.setattr(tuning, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(tuning, "POLICY_DIR", tmp_path / "policies")
    report, candidate = tuning.build_artifacts(date(2026, 9, 17))
    assert (
        tuning.validate_artifact_pair(report, candidate, target=date(2026, 9, 17)) == []
    )
    assert report["allowed_runtime_apply"] is positive_marginal
    with pytest.raises(RuntimeError, match="publisher_retired"):
        tuning.write_artifacts(report, candidate)
    receipt = policy.freeze_preopen_policy(
        date(2026, 9, 18),
        write=True,
        now=datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul")),
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
        applied_dir=tmp_path / "applied",
    )
    assert receipt["active"] is False
    assert receipt["operator_approval_required"] is False
    loaded = policy.load_active_policy(
        date(2026, 9, 18), applied_dir=tmp_path / "applied"
    )
    assert policy.bounded_bonus(0.9, loaded)["bonus_points"] == 0


def integrated_fixture(monkeypatch):
    from src.engine.monitoring import scanner_lookup_attention_tuning as tuning
    monkeypatch.setattr(tuning, "load_completed_facts", lambda *args: [])
    monkeypatch.setattr(tuning, "_latest_symbol_master", lambda *args: (set(), {"status": "pass"}))
    monkeypatch.setattr(tuning, "_source_quality", lambda *args: {"status": "pass"})
    monkeypatch.setattr(tuning, "_latest_prior_policy", lambda *args: {})
    monkeypatch.setattr(tuning, "_event_path", lambda *args: pytest.fail("rolling raw scan forbidden"))
    return tuning


def test_native_capture_decoder_preserves_full_partial_and_conflicting_mirrors(monkeypatch):
    from src.tests.test_scanner_lookup_attention_tuning import _observation_event, _receipt_event
    tuning = integrated_fixture(monkeypatch)
    state = {}
    for event in (_observation_event(), _receipt_event(), _receipt_event()):
        resource.capture_native_event(state, event)
    assert len(state["lookup_attention_native_events"]) == 2
    events = list(state["lookup_attention_native_events"].values())
    observations, lineage = tuning.collect_lineage(date(2026, 9, 2), events_by_date={"2026-09-02": events})
    assert observations[0]["fill_class"] == "full_fill"
    conflict = _observation_event()
    conflict["fields"]["lookup_attention_snapshot_score"] = 0.1
    resource.capture_native_event(state, conflict)
    observations, lineage = tuning.collect_lineage(date(2026, 9, 2), events_by_date={"2026-09-02": list(state["lookup_attention_native_events"].values())})
    assert observations == []
    assert lineage["invalid_observation_count"] == 1


def test_positive_snapshot_and_completed_cohorts_never_replace_executable_portfolio_ev(monkeypatch, tmp_path):
    tuning = integrated_fixture(monkeypatch)
    from src.tests.test_scanner_lookup_attention_tuning import _passing_rows
    monkeypatch.setattr(tuning, "join_completed_outcomes", lambda *args, **kwargs: (_passing_rows(date(2026, 9, 2)), {}))
    section = resource.integrated_selection_evaluation(date(2026, 9, 17), {}, migration={"resource_pair_rows": ready_resource_rows()})
    assert section["snapshot_proxy"]["diagnostic_snapshot_gate_pass"]
    assert section["actual_completed"]["book"]["candidate_control_ev_uplift_pct"] > 0
    assert section["primary_economics"]["paired_delta_ev_pct"] is None
    assert section["selection_opportunity_economics"]["selection_opportunity_ev_pct"] > 0
    assert section["selection_opportunity_economics"]["daily_net_profit_krw"] is None
    assert section["status"] == "experiment_ready"
    report = {"target_date": "2026-09-17", "evaluation_phase": "postclose_final",
              "scanner_unique_funnel": {"economic_cohorts": {"lookup_attention_selection": section}}}
    policies = tmp_path / "policies"
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "intraday_ws_freshness_monitor_2026-09-17.json").write_text(
        __import__("json").dumps(report)
    )
    payload = policy.publish_integrated_policy(report, policy_dir=policies)
    assert not resource.validate_integrated_selection(section, payload, target=date(2026, 9, 17))
    receipt = policy.freeze_preopen_policy(
        "2026-09-18",
        write=True,
        now=datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul")),
        policy_dir=policies,
        report_dir=reports,
        applied_dir=tmp_path / "applied",
    )
    assert receipt["active"]
    loaded = policy.load_active_policy(
        "2026-09-18", applied_dir=tmp_path / "applied"
    )
    assert loaded["active"] and loaded["experiment_mode"]
    assert policy.bounded_bonus(0.9, loaded)["bonus_points"] == 0.0
    fabricated = {**payload, "status": "live_auto_apply_ready"}
    fabricated["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in fabricated.items() if k != "artifact_sha256"})
    assert "integrated_disposition_invalid" in resource.validate_integrated_selection(section, fabricated, target=date(2026, 9, 17))


def test_integrated_zero_policy_next_open_source_dates_cache_and_preopen_window(monkeypatch, tmp_path):
    import json
    integrated_fixture(monkeypatch)
    section = resource.integrated_selection_evaluation(date(2026, 9, 17), {})
    report = {"target_date": "2026-09-17", "evaluation_phase": "postclose_final",
              "scanner_unique_funnel": {"economic_cohorts": {"lookup_attention_selection": section}}}
    reports = tmp_path / "reports"
    policies = tmp_path / "policies"
    reports.mkdir()
    source_path = reports / "intraday_ws_freshness_monitor_2026-09-17.json"
    source_path.write_text(json.dumps(report))
    payload = policy.publish_integrated_policy(report, publication_date="2026-09-18", effective_date="2026-09-21", policy_dir=policies)
    assert payload["source_evaluation_date"] == "2026-09-17"
    candidate = policy.load_candidate_policy("2026-09-21", policy_dir=policies, report_dir=reports)
    assert candidate["reason"] == "prior_policy_not_live_auto_apply_ready"
    # Cache invalidates on the actual observation source, not publication date.
    report["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"]["primary_economics"]["paired_delta_ev_pct"] = 100
    source_path.write_text(json.dumps(report))
    assert policy.load_candidate_policy("2026-09-21", policy_dir=policies, report_dir=reports)["reason"] == "prior_policy_contract_invalid"
    with pytest.raises(ValueError, match="outside_target_date_window"):
        policy.freeze_preopen_policy("2026-09-21", write=True,
            now=datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul")),
            policy_dir=policies, report_dir=reports, applied_dir=tmp_path / "applied")


def test_identical_final_input_reuses_result_and_cost_revision_invalidates(monkeypatch):
    tuning = integrated_fixture(monkeypatch)
    section = resource.integrated_selection_evaluation(date(2026, 9, 17), {})
    monkeypatch.setattr(tuning, "_resource_allocation_pair_book", lambda *args, **kwargs: pytest.fail("unchanged input re-evaluated"))
    assert resource.integrated_selection_evaluation(date(2026, 9, 17), {}, predecessor=section) is section


def test_daily_and_strict_consume_same_section_without_touching_other_families(monkeypatch, tmp_path):
    import json
    from src.engine import daily_threshold_cycle_report as daily
    from src.engine import verify_threshold_cycle_postclose_chain as verifier
    integrated_fixture(monkeypatch)
    root = tmp_path / "data" / "report"
    root.mkdir(parents=True)
    monkeypatch.setattr(daily, "REPORT_DIR", root)
    monkeypatch.setattr(verifier, "REPORT_DIR", root)
    (root / "threshold_cycle_2026-09-17.json").write_text(json.dumps({"date": "2026-09-17", "unrelated_family": [1, 2]}))
    micro = root / "microstructure_reaction_context"
    micro.mkdir()
    (micro / "microstructure_reaction_context_2026-09-17.json").write_text(json.dumps({"date": "2026-09-17", "summary": {}}))
    section = resource.integrated_selection_evaluation(date(2026, 9, 17), {})
    report = {"target_date": "2026-09-17", "evaluation_phase": "intraday",
              "scanner_unique_funnel": {"economic_cohorts": {"lookup_attention_selection": section}}}
    monitor = root / "intraday_ws_freshness_monitor"
    monitor.mkdir()
    (monitor / "intraday_ws_freshness_monitor_2026-09-17.json").write_text(json.dumps(report))
    payload = policy.publish_integrated_policy(report, policy_dir=root.parent / "threshold_cycle" / "scanner_lookup_attention_policy")
    daily.refresh_machine_evaluation_only("2026-09-17")
    consumed = json.loads((root / "threshold_cycle_2026-09-17.json").read_text())
    assert consumed["unrelated_family"] == [1, 2]
    assert consumed["scanner_lookup_attention_selection"]["source_section_sha256"] == section["artifact_sha256"]
    assert verifier._scanner_lookup_attention_status(report, payload, target_date="2026-09-17")["status"] == "pass"
    consumed["scanner_lookup_attention_selection"]["source_section_sha256"] = "0" * 64
    (root / "threshold_cycle_2026-09-17.json").write_text(json.dumps(consumed))
    assert verifier._scanner_lookup_attention_status(report, payload, target_date="2026-09-17")["status"] == "fail"



def test_production_native_decoder_has_no_dependency_on_retired_reports(monkeypatch, tmp_path):
    from src.tests.test_scanner_lookup_attention_tuning import _observation_event
    tuning = integrated_fixture(monkeypatch)
    monkeypatch.setattr(tuning, "PREOPEN_DIR", tmp_path / "applied")
    monkeypatch.setattr(tuning, "_latest_prior_policy", lambda *args: pytest.fail("retired campaign read"))
    original = tuning._load_json
    def no_retired_report(path):
        assert "scanner_lookup_attention_tuning_" not in str(path)
        return original(path)
    monkeypatch.setattr(tuning, "_load_json", no_retired_report)
    section = resource.integrated_selection_evaluation(date(2026, 9, 2), {"2026-09-02": [_observation_event()]})
    assert section["lineage"]["valid_observation_count"] == 1
    assert section["lineage"]["invalid_runtime_policy_provenance_count"] == 0
    assert section["status"] == "source_gap"



def test_final_native_resource_export_is_bounded_but_preserves_exact_receipts(monkeypatch):
    tuning = integrated_fixture(monkeypatch)
    target = date(2026, 9, 17)
    _, lineage = tuning.collect_lineage(target, events_by_date={})
    rows = pair_rows(day=target)
    lineage["_resource_pair_rows"] = rows
    lineage["resource_capture_diagnostics"] = {target.isoformat(): {"raw_row_count": 58_532}}
    monkeypatch.setattr(tuning, "collect_lineage", lambda *args, **kwargs: ([], deepcopy(lineage)))
    def event(generation, code="100000"):
        return {"stage": "scalping_scanner_candidate_pruned", "emitted_date": target.isoformat(),
                "stock_code": code, "fields": {"scanner_scan_generation_id": generation}}
    proof = event(rows[0]["scan_generation_id"])
    receipt = {"stage": "position_rebased_after_fill", "emitted_date": target.isoformat(), "fields": {}}
    events = [event(f"unused-{index}") for index in range(200)] + [proof, receipt]
    section = resource.integrated_selection_evaluation(target, {target.isoformat(): events})
    assert section["native_events"] == [proof, receipt]
    assert section["lineage"]["resource_capture_diagnostics"][target.isoformat()]["raw_row_count"] == 58_532
    assert section["snapshot_proxy"]["pairs"] == book(rows)["pairs"]



@pytest.mark.parametrize("field", ["baseline_budget_ev_pct", "candidate_net_pnl_krw", "tail", "model_error"])
def test_source_gap_policy_rejects_self_hashed_zero_or_fabricated_primary_metrics(monkeypatch, tmp_path, field):
    integrated_fixture(monkeypatch)
    section = resource.integrated_selection_evaluation(date(2026, 9, 17), {})
    section["primary_economics"][field] = 0
    section["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in section.items() if k != "artifact_sha256"})
    report = {"target_date": "2026-09-17", "scanner_unique_funnel": {"economic_cohorts": {"lookup_attention_selection": section}}}
    with pytest.raises(ValueError, match="integrated_disposition_invalid"):
        policy.publish_integrated_policy(report, policy_dir=tmp_path)


def execution_frame(day, ordinal=0, *, outgoing=.2, incoming=1.):
    """Existing synthetic owner witnesses; no market or economic acceptance."""
    from src.tests.test_entry_setup_paired_replay_batch import operating_compact_row, full_compact_proof
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    proof = full_compact_proof()
    inputs, rows = {}, []
    source = operating_compact_row(day, ordinal)
    epoch = datetime.fromisoformat(source["owner_replay"]["seed"]["observed_at"]).timestamp()
    for index, rate in enumerate((outgoing, incoming)):
        row = deepcopy(source)
        row.update(stock_code=f"00593{index}", incumbent_verdict="PASS",
            scanner_promotion_id=source["scanner_promotion_id"] + f"-{index}",
            evaluation_attempt_id=source["evaluation_attempt_id"] + f"-{index}",
            natural_contract_evidence=dict(model="gpt-5.4-nano",provider_actual="openai",
                semantic_validation_status="pass",decision_quality_contract_status="pass"))
        replay = row["owner_replay"]
        seed = replay["seed"]
        seed.update({k: row[k] for k in ("stock_code", "scanner_promotion_id", "evaluation_attempt_id")})
        seed["seed_sha256"] = compact.digest({k:v for k,v in seed.items() if k != "seed_sha256"})
        for arm in replay["operating_arms"].values():
            arm.update(net_return_pct=rate, stress_net_return_pct=rate-.05,
                net_pnl_krw=rate / 100 * arm["budget_krw"],stress_net_pnl_krw=(rate-.05) / 100 * arm["budget_krw"])
            arm["sha256"] = compact.digest({k:v for k,v in arm.items() if k != "sha256"})
        replay["replay_sha256"] = compact.digest({k:v for k,v in replay.items() if k != "replay_sha256"})
        assert compact.owner_operating_arm(replay, row)
        assert compact.owner_model_scope_valid(proof["owner_execution_model_validation"], row)
        native = pair_rows(date.fromisoformat(day))[:2][index]
        native.update(stock_code=row["stock_code"],scanner_promotion_id=row["scanner_promotion_id"],
            observation_date=day,scan_generation_id=f"SCANGEN-{day}-{ordinal}",
            observed_epoch=epoch,price_observed_epoch=epoch-1,
            partition_codes_sha256=policy.canonical_sha256(["005930", "005931"]))
        rows.append(native)
        inputs[(day,row["scanner_promotion_id"],row["stock_code"])] = dict(row=row,
            model=proof["owner_execution_model_validation"],source_projection_sha256="a"*64,
            pricing=proof["runtime_inference_cost_receipt"])
    return rows, inputs


def execution_population(days):
    rows, inputs = [], {}
    for day, ordinal in days:
        frame, values = execution_frame(day, ordinal)
        rows += frame
        inputs.update(values)
    return rows, inputs


def test_supported_small_sample_measures_same_frozen_budget_and_holds(monkeypatch):
    integrated_fixture(monkeypatch)
    rows, inputs = execution_frame("2026-09-17")
    monkeypatch.setattr(resource, "execution_inputs", lambda *args: inputs)
    section = resource.integrated_selection_evaluation(date(2026,9,17),{},migration={"resource_pair_rows":rows})
    assert section["status"] == "hold_sample"
    book = section["primary_economics"]
    assert book["baseline_budget_ev_pct"] == pytest.approx(.2)
    assert book["candidate_budget_ev_pct"] == pytest.approx(1.)
    assert book["paired_delta_ev_pct"] == pytest.approx(.8)
    assert book["daily_net_delta_krw"] == {"2026-09-17":pytest.approx(960.)}
    assert book["exposure"]["budget_krw"] == 120000.
    assert book["counterfactual_not_realized_pnl"] is True
    assert all(p["filter_role"] == "scanner_selection_not_ai" for p in book["pairs"])


def test_no_effect_skips_execution_and_missing_changed_arm_stays_null():
    rows, inputs = execution_frame("2026-09-17")
    broken = resource.selection_execution_book(rows, {next(iter(inputs)):next(iter(inputs.values()))})
    assert broken["status"] == "source_gap"
    assert broken["paired_delta_ev_pct"] is None
    for row in rows:
        row.update(candidate_priority_score=row["base_priority_score"],counterfactual_bonus_points=0.,lookup_attention_snapshot_score=0.)
    same = resource.selection_execution_book(rows,{})
    assert same["status"] == "no_effect" and same["paired_delta_ev_pct"] == 0.
    assert same["baseline_budget_ev_pct"] is None


def test_ready_native_proof_publication_source_date_preopen_and_scanner_bonus(monkeypatch,tmp_path):
    import json
    from src.tests.test_scanner_lookup_attention_tuning import _passing_rows
    tuning = integrated_fixture(monkeypatch)
    rows, inputs = execution_population([("2026-09-14",0),("2026-09-14",2),("2026-09-16",0)])
    monkeypatch.setattr(resource,"execution_inputs",lambda *args: inputs)
    outcomes = _passing_rows(date(2026,9,14))
    monkeypatch.setattr(tuning,"join_completed_outcomes",lambda *args,**kwargs: (outcomes,{}))
    learning = resource.integrated_selection_evaluation(date(2026,9,18),{},migration={"resource_pair_rows":rows})
    assert learning["status"] == "forward_holdout_armed"
    assert learning["independent_holdout"]["learning_cutoff"] >= datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    assert resource.integrated_selection_evaluation(date(2026,9,18),{},predecessor=learning,
        migration={"resource_pair_rows":rows}) is learning
    future, values = execution_population([("2026-09-21",0),("2026-09-21",2),("2026-09-22",0)])
    rows += future
    inputs.update(values)
    outcomes += _passing_rows(date(2026,9,21),id_start=10000)
    ready = resource.integrated_selection_evaluation(date(2026,9,29),{},predecessor=learning,migration={"resource_pair_rows":rows})
    assert ready["status"] == "live_auto_apply_ready"
    report = {"target_date":"2026-09-29","evaluation_phase":"intraday",
        "scanner_unique_funnel":{"economic_cohorts":{"lookup_attention_selection":ready}}}
    published = policy.publish_integrated_policy(report,publication_date="2026-09-30",policy_date="2026-09-30",
        effective_date="2026-10-01",policy_dir=tmp_path / "policies")
    assert resource.validate_integrated_selection(ready,published,target=date(2026,9,29)) == []
    reports = tmp_path / "reports"
    reports.mkdir()
    source = reports / "intraday_ws_freshness_monitor_2026-09-29.json"
    source.write_text(json.dumps(report))
    receipt = policy.freeze_preopen_policy("2026-10-01",write=True,
        now=datetime(2026,10,1,8,tzinfo=ZoneInfo("Asia/Seoul")),policy_dir=tmp_path / "policies",
        report_dir=reports,applied_dir=tmp_path / "applied")
    assert receipt["active"]
    loaded = policy.load_active_policy("2026-10-01",applied_dir=tmp_path / "applied")
    assert policy.bounded_bonus(.9,loaded)["bonus_points"] == 150.
    source.write_text("{}")
    policy.clear_policy_cache()
    assert policy.load_active_policy("2026-10-01",applied_dir=tmp_path / "applied") == loaded
    forged = deepcopy(receipt)
    forged["source_report"]["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"]["primary_economics"]["paired_delta_ev_pct"] = 100.
    section = forged["source_report"]["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"]
    section["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in section.items() if k != "artifact_sha256"})
    forged["source_policy"]["source_report_artifact_sha256"] = section["artifact_sha256"]
    forged["source_policy"]["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in forged["source_policy"].items() if k != "artifact_sha256"})
    forged["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in forged.items() if k != "artifact_sha256"})
    assert not policy.validate_preopen_receipt(forged,date(2026,10,1))


@pytest.mark.parametrize("defect", ["partial_fill", "natural_contract", "pricing_expiry", "future_model"])
def test_execution_preflight_does_not_impute_unsupported_inputs(defect):
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    rows, inputs = execution_frame("2026-09-17")
    value = list(inputs.values())[1]
    if defect == "partial_fill":
        replay = value["row"]["owner_replay"]
        for arm in replay["operating_arms"].values():
            arm["modeled_filled_qty"] -= 1
            arm["sha256"] = compact.digest({k:v for k,v in arm.items() if k != "sha256"})
        replay["replay_sha256"] = compact.digest({k:v for k,v in replay.items() if k != "replay_sha256"})
    elif defect == "natural_contract":
        value["row"]["natural_contract_evidence"]["semantic_validation_status"] = "fail"
    elif defect == "pricing_expiry":
        value["pricing"]["effective_to"] = "2026-09-16"
    else:
        proof = value["model"]["validated_scopes"][0]
        proof["available_after_date"] = "2026-09-17"
        proof["sha256"] = compact.digest({k:v for k,v in proof.items() if k != "sha256"})
    result = resource.selection_execution_book(rows, inputs)
    assert result["paired_delta_ev_pct"] is None
    assert result["status"] == "source_gap"


def test_overlapping_capital_and_incomplete_partition_cannot_promote():
    rows, inputs = execution_frame("2026-09-17")
    duplicate = deepcopy(rows)
    for row in duplicate:
        row["scan_generation_id"] += "-overlap"
    assert "overlapping_owner_capital_allocation_unsupported" in resource.selection_execution_book(rows+duplicate,inputs)["source_gaps"]
    supported = resource.selection_execution_book(rows, inputs)
    broken = deepcopy(rows)
    for index, row in enumerate(broken):
        row["scan_generation_id"] += f"-incomplete-{index}"
    result = resource.selection_execution_book(rows+broken, inputs)
    assert result["status"] == "supported_operating_comparison"
    assert result["paired_delta_ev_pct"] == supported["paired_delta_ev_pct"]
    assert result["complete_coverage"] is False
    assert not resource.selection_edge_passes(result)


def test_prior_model_lookup_uses_independently_valid_proof_for_each_pair():
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    rows, inputs = execution_frame("2026-09-17")
    baseline = resource.selection_execution_book(rows, inputs)
    for value in inputs.values():
        model = value["model"]
        future = deepcopy(model["validated_scopes"][0])
        future["available_after_date"] = "2026-09-17"
        future["optimistic_net_error_budget_pct"] = 100.
        future["sha256"] = compact.digest({k:v for k,v in future.items() if k != "sha256"})
        model["validated_scopes"].insert(0,future)
    assert resource.selection_execution_book(rows,inputs)["robust_delta_ev_lower_bound_pct"] == baseline["robust_delta_ev_lower_bound_pct"]


def test_late_intraday_writer_preserves_final_economics_and_publication(monkeypatch,tmp_path):
    import json
    from src.engine.monitoring import intraday_ws_freshness_monitor as monitor
    integrated_fixture(monkeypatch)
    section = resource.integrated_selection_evaluation(date(2026,9,17),{})
    report = {"target_date":"2026-09-17","evaluation_phase":"intraday", "summary":{"quality_revision":1},
        "scanner_unique_funnel":{"economic_cohorts":{"lookup_attention_selection":section}}}
    monkeypatch.setattr(monitor,"REPORT_DIR",tmp_path / "report")
    monkeypatch.setattr(monitor,"_render_monitor_markdown",lambda *args: "fixture")
    publish = policy.publish_integrated_policy
    monkeypatch.setattr(policy,"publish_integrated_policy",lambda report,**kwargs:publish(report,policy_dir=tmp_path / "policies",**kwargs))
    monitor.write_report(report,monitor_only=True,publication={"publication_date":"2026-09-19","policy_date":"2026-09-18","effective_date":"2026-09-21"})
    initial = deepcopy(report["scanner_lookup_attention_publication"])
    late = deepcopy(report)
    late["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"] = {"status":"intraday_capture_only"}
    late["summary"]["quality_revision"] = 2
    monitor.write_report(late,monitor_only=True)
    stored = json.loads((tmp_path / "report/intraday_ws_freshness_monitor_2026-09-17.json").read_text())
    assert stored["scanner_unique_funnel"]["economic_cohorts"]["lookup_attention_selection"] == section
    assert stored["scanner_lookup_attention_publication"] == initial
    assert stored["summary"]["quality_revision"] == 2
    assert stored["evaluation_phase"] == "intraday"


def test_post_apply_requires_exact_immutable_policy_receipt_hash(monkeypatch):
    from src.engine.monitoring.scanner_lookup_attention_tuning import _cohort_book
    from src.tests.test_scanner_lookup_attention_tuning import _passing_rows
    rows = _passing_rows(date(2026,9,14))
    for row in rows:
        row.update(lookup_attention_weight_runtime_policy_eligible=True,
            lookup_attention_weight_policy_artifact_sha256="b"*64,
            lookup_attention_weight_policy_version=policy.POLICY_VERSION,
            lookup_attention_weight_policy_source_date="2026-09-11")
    monkeypatch.setattr(policy,"load_active_policy",lambda *args: {"active":False})
    assert resource.post_apply_inputs(date(2026,9,18),rows)[1] == []
    monkeypatch.setattr(policy,"load_active_policy",lambda *args: dict(active=True,policy_source_date="2026-09-11",
        policy_artifact_sha256="a"*64,preopen_artifact_sha256="c"*64,policy_version=policy.POLICY_VERSION))
    assert resource.post_apply_inputs(date(2026,9,18),rows)[1] == []
    for row in rows:
        row["lookup_attention_weight_policy_artifact_sha256"] = "a"*64
    incumbent, selected, receipts = resource.post_apply_inputs(date(2026,9,18),rows)
    assert incumbent["status"] == "live_auto_apply_ready"
    assert len(selected) == 20 and len(receipts) == 5
    assert _cohort_book(selected)["all"]["notional_weighted_ev_pct"] == .3

    monkeypatch.setattr(policy,"load_active_policy",lambda *args: dict(active=True,policy_source_date="2026-09-11",
        policy_artifact_sha256="a"*64,preopen_artifact_sha256="c"*64,policy_version=policy.POLICY_VERSION,
        experiment_mode=True,experiment_arm="baseline"))
    incumbent, selected, _ = resource.post_apply_inputs(date(2026,9,18),rows)
    assert incumbent["status"] == "experiment_ready"
    assert len(selected) == 20
