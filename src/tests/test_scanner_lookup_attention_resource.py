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
    assert section["status"] == "source_gap"
    report = {"target_date": "2026-09-17", "evaluation_phase": "postclose_final",
              "scanner_unique_funnel": {"economic_cohorts": {"lookup_attention_selection": section}}}
    payload = policy.publish_integrated_policy(report, policy_dir=tmp_path)
    assert not resource.validate_integrated_selection(section, payload, target=date(2026, 9, 17))
    fabricated = {**payload, "allowed_runtime_apply": True, "status": "live_auto_apply_ready"}
    fabricated["artifact_sha256"] = policy.canonical_sha256({k:v for k,v in fabricated.items() if k != "artifact_sha256"})
    assert "unsupported_execution_authority" in resource.validate_integrated_selection(section, fabricated, target=date(2026, 9, 17))


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
