"""Small repeated net edge without changing scanner/broker authority."""

from datetime import date, datetime, timedelta
import copy
import json
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring import scanner_lookup_attention_tuning as tuning
from src.engine.scalping import scanner_lookup_attention_policy as policy
from src.tests.test_scanner_lookup_attention_tuning import (
    _passing_rows,
    _write_live_pair,
)


def small_rows(start=date(2026, 9, 2), id_start=1):
    rows = _passing_rows(start, id_start=id_start)
    for row in rows:
        row["net_return_pct"] = 0.06 if row["cohort"] == "candidate" else 0.02
        row["net_pnl_krw"] = row["net_return_pct"] * 1000
    return rows


def evidence(rows=None, post=None):
    book = tuning._cohort_book(small_rows() if rows is None else rows)
    return tuning._evidence(
        book, book, tuning._cohort_book(post or []), post_apply_mature=bool(post)
    )


def test_small_repeated_net_passes_all_three_economic_boundaries():
    rows = small_rows()
    book = tuning._cohort_book(rows)
    assert book["candidate_control_ev_uplift_pct"] == pytest.approx(0.04)
    assert tuning._book_passes(book) == (True, [])
    assert policy._evidence_valid(evidence(rows, rows))
    for row in rows:
        row.update(
            lookup_attention_weight_runtime_policy_eligible=True,
            lookup_attention_weight_policy_source_date="2026-09-02",
        )
    result = tuning.evaluate_post_apply(
        {"holdout_armed_since": "2026-09-02", "status": "live_auto_apply_ready"}, rows
    )
    assert result["status"] == "pass_mature"
    assert not result["rollback_triggered"]


def test_small_net_policy_reaches_frozen_preopen_and_runtime_without_approval(tmp_path):
    source_date = date(2026, 9, 17)
    report, payload = _write_live_pair(tmp_path, source_date)
    base = small_rows()
    holdout = small_rows(date(2026, 9, 9), 10_000)
    report["outcomes"] = base + holdout
    report["base_book"] = tuning._cohort_book(base)
    report["forward_holdout_book"] = tuning._cohort_book(holdout)
    report["campaign_base"] = tuning._freeze_base(base, "2026-09-08")
    payload["campaign_base"] = report["campaign_base"]
    payload["evidence"] = tuning._evidence(
        report["base_book"],
        report["forward_holdout_book"],
        report["post_apply_attribution"]["book"],
        post_apply_mature=False,
    )
    report["economic_acceptance"] = tuning._economic_acceptance(report)
    report["policy_evidence_sha256"] = policy.canonical_sha256(payload["evidence"])
    report["artifact_sha256"] = policy.canonical_sha256(
        {k: v for k, v in report.items() if k != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {k: v for k, v in payload.items() if k != "artifact_sha256"}
    )
    assert tuning.validate_artifact_pair(report, payload, target=source_date) == []
    (
        tmp_path / "reports" / f"scanner_lookup_attention_tuning_{source_date}.json"
    ).write_text(json.dumps(report))
    (
        tmp_path / "policies" / f"scanner_lookup_attention_policy_{source_date}.json"
    ).write_text(json.dumps(payload))
    applied_dir = tmp_path / "small-net-applied"
    receipt = policy.freeze_preopen_policy(
        "2026-09-18",
        write=True,
        now=datetime(2026, 9, 18, 8, tzinfo=ZoneInfo("Asia/Seoul")),
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
        applied_dir=applied_dir,
    )
    assert receipt["active"]
    assert not receipt["operator_approval_required"]
    loaded = policy.load_active_policy("2026-09-18", applied_dir=applied_dir)
    assert loaded["active"]
    assert policy.bounded_bonus(0.8, loaded)["bonus_points"] > 0


@pytest.mark.parametrize("value", [0, -0.01, 0.02])
def test_nonpositive_candidate_or_increment_does_not_approve(value):
    rows = small_rows()
    for row in rows:
        if row["cohort"] == "candidate":
            row.update(net_return_pct=value, net_pnl_krw=value * 1000)
    assert not tuning._book_passes(tuning._cohort_book(rows))[0]
    assert not policy._evidence_valid(evidence(rows))


def test_day_cluster_variation_not_hidden_by_repeated_same_day_trades():
    rows = small_rows()
    for row in rows:
        if row["cohort"] == "candidate":
            value = 0.3 if row["rec_date"] == "2026-09-02" else 0.01
            row.update(net_return_pct=value, net_pnl_krw=value * 1000)
    book = tuning._cohort_book(rows)
    assert book["candidate"]["source_quality_adjusted_ev_pct"] > 0
    assert book["candidate"]["net_return_robust_se_pct"] > 0.04
    assert not tuning._book_passes(book)[0]
    assert not policy._evidence_valid(evidence(rows))


def test_large_loss_cannot_hide_behind_frequent_small_gains():
    rows = small_rows()
    rows[0].update(net_return_pct=-3.0, net_pnl_krw=-3000)
    assert not tuning._book_passes(tuning._cohort_book(rows))[0]


@pytest.mark.parametrize("prefix", ["", "forward_holdout_", "post_apply_"])
@pytest.mark.parametrize("value", [None, True, -1.0, float("nan"), float("inf")])
def test_missing_or_malformed_uncertainty_fails_closed(prefix, value):
    payload = evidence(post=small_rows())
    payload[prefix + "candidate_net_return_robust_se_pct"] = value
    assert not policy._evidence_valid(payload)


def test_candidate_total_net_loss_with_positive_equal_weight_mean_rejected():
    book = tuning._cohort_book(small_rows())
    book["candidate"]["net_pnl_krw"] = -1
    assert "candidate_positive_net_missing" in policy.net_edge_reasons(book)


def test_mature_post_apply_cannot_be_hidden_as_immature():
    payload = evidence(post=small_rows())
    payload["post_apply_mature"] = False
    assert not policy._evidence_valid(payload)


def test_immature_post_apply_cannot_hide_known_emergency_loss():
    payload = evidence()
    payload["post_apply_candidate_completed_outcome_count"] = 1
    payload["post_apply_candidate_worst_net_return_pct"] = -6
    assert not policy._evidence_valid(payload)


def test_missing_capital_time_is_not_an_approval_floor():
    book = tuning._cohort_book(small_rows())
    assert book["candidate"]["net_per_capital_hour"] is None
    assert tuning._book_passes(book)[0]
    rows = small_rows()
    for row in rows:
        row["capital_hours_krw"] = 100_000 * 0.5
    metrics = tuning._cohort_book(rows)["candidate"]
    assert metrics["net_per_capital_hour"] == pytest.approx(60 / 50_000)


def test_new_source_cannot_strip_contract_to_use_legacy_fixed_gate(tmp_path):
    report, payload = _write_live_pair(tmp_path, date(2026, 9, 17))
    payload["evidence"].pop("economic_contract_version")
    assert "policy_net_economic_contract_required" in policy.validate_policy_payload(
        payload, source_date=date(2026, 9, 17)
    )
    assert "net_economic_contract_required" in tuning.validate_artifact_pair(
        report, payload, target=date(2026, 9, 17)
    )


def test_books_recomputed_from_rows_even_when_hashes_are_repaired(tmp_path):
    report, payload = _write_live_pair(tmp_path, date(2026, 9, 17))
    report["forward_holdout_book"]["candidate"]["net_return_robust_se_pct"] = 0.01
    payload["evidence"] = tuning._evidence(
        report["base_book"],
        report["forward_holdout_book"],
        report["post_apply_attribution"]["book"],
        post_apply_mature=False,
    )
    report["policy_evidence_sha256"] = policy.canonical_sha256(payload["evidence"])
    report["artifact_sha256"] = policy.canonical_sha256(
        {k: v for k, v in report.items() if k != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {k: v for k, v in payload.items() if k != "artifact_sha256"}
    )
    assert "economic_books_not_reproducible" in tuning.validate_artifact_pair(
        report, payload, target=date(2026, 9, 17)
    )


def test_zero_trade_days_count_for_bounded_review_but_missing_audits_do_not():
    days = []
    day = date(2026, 9, 2)
    while len(days) < 20:
        if tuning.is_krx_trading_day(day):
            days.append(day.isoformat())
        day += timedelta(days=1)
    report = {
        "target_date": days[-1],
        "status": "hold_sample",
        "outcomes": [],
        "lineage": {"observed_event_dates": days, "valid_observation_count": 0},
        "natural_observation_audit": {
            "audits": [{"target_date": d, "status": "pass"} for d in days]
        },
    }
    result = tuning._economic_acceptance(report)
    assert result["maintenance_review_due"]
    assert result["full_completed_per_valid_source_day"] == 0
    assert result["net_per_valid_source_day_krw"] is None
    assert result["next_action"] == "review_integrate_or_retire_no_evidence_or_edge"
    assert not result["allowed_runtime_apply"]
    report["natural_observation_audit"]["audits"][-1][
        "status"
    ] = "source_quality_blocked"
    assert not tuning._economic_acceptance(report)["maintenance_review_due"]


def test_independent_forward_holdout_still_required_with_small_positive_edge():
    rows = small_rows()
    result = tuning.decide_promotion(
        date(2026, 9, 8), tuning._cohort_book(rows), rows, source_quality_pass=True
    )
    assert result["status"] == "forward_holdout_armed"
    assert result["forward_holdout_book"]["all"]["completed_outcome_count"] == 0


def test_legacy_frozen_metrics_keep_original_hash_shape():
    book = tuning._cohort_book(small_rows(), economic_contract=False)
    assert "economic_contract_version" not in book
    assert "net_return_robust_se_pct" not in book["candidate"]
    assert not tuning._book_passes(book)[
        0
    ]  # Old 0.10 rule is audit compatibility only.


@pytest.mark.parametrize("mode", ["ready", "blocked_master", "post_loss"])
def test_actual_artifact_builder_closes_reproducible_state_branches(
    tmp_path, monkeypatch, mode
):
    original, prior = _write_live_pair(tmp_path, date(2026, 9, 17))
    rows = copy.deepcopy(original["outcomes"])
    lineage = copy.deepcopy(original["lineage"])
    lineage.update(
        window_start="2026-09-02",
        window_end="2026-09-18",
        _resource_pair_rows=original["resource_pair_rows"],
    )
    if mode == "post_loss":
        for row in rows:
            if row["rec_date"] > "2026-09-08":
                row.update(
                    lookup_attention_weight_runtime_policy_eligible=True,
                    lookup_attention_weight_policy_source_date="2026-09-17",
                )
                if row["cohort"] == "candidate":
                    row.update(net_return_pct=-1, net_pnl_krw=-1000)
    monkeypatch.setattr(tuning, "collect_lineage", lambda target: ([], lineage))
    monkeypatch.setattr(tuning, "load_completed_facts", lambda start, target: [])
    monkeypatch.setattr(tuning, "join_completed_outcomes", lambda *a, **kw: (rows, {}))
    monkeypatch.setattr(
        tuning,
        "_latest_symbol_master",
        lambda target: (
            set(),
            {"status": "blocked" if mode == "blocked_master" else "pass"},
        ),
    )
    monkeypatch.setattr(tuning, "_latest_prior_policy", lambda target: prior)
    monkeypatch.setattr(
        tuning, "_source_quality", lambda *a: {"status": "pass", "audits": []}
    )
    monkeypatch.setattr(tuning, "_cohort_funnel", lambda *a: original["cohort_funnel"])
    report, payload = tuning.build_artifacts(date(2026, 9, 18))
    assert (
        tuning.validate_artifact_pair(report, payload, target=date(2026, 9, 18)) == []
    )
    assert (
        report["status"]
        == {
            "ready": "live_auto_apply_ready",
            "blocked_master": "source_quality_blocked",
            "post_loss": "hold_no_edge",
        }[mode]
    )
    if mode == "post_loss":
        assert report["post_apply_attribution"]["rollback_triggered"]
        assert report["campaign_base"] == {}
