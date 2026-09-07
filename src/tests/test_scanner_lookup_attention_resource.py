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
    assert receipt["active"] is True
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
    assert tuning.main() == 1
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
    tuning.write_artifacts(report, candidate)
    receipt = policy.freeze_preopen_policy(
        date(2026, 9, 18),
        write=True,
        now=datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul")),
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
        applied_dir=tmp_path / "applied",
    )
    assert receipt["active"] is positive_marginal
    assert receipt["operator_approval_required"] is False
    loaded = policy.load_active_policy(
        date(2026, 9, 18), applied_dir=tmp_path / "applied"
    )
    assert policy.bounded_bonus(0.9, loaded)["bonus_points"] == (
        150 if positive_marginal else 0
    )
