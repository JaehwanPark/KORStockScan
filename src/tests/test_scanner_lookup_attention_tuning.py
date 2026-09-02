from datetime import date, timedelta
import json

from src.engine.monitoring import scanner_lookup_attention_tuning as tuning
from src.engine.scalping import scanner_lookup_attention_policy as policy


def _outcome(day: date, *, candidate: bool, index: int) -> dict:
    return {
        "rec_date": day.isoformat(),
        "recommendation_id": index,
        "cohort": "candidate" if candidate else "control",
        "buy_notional_krw": 100_000.0,
        "net_pnl_krw": 500.0 if candidate else 100.0,
        "net_return_pct": 0.5 if candidate else 0.1,
    }


def _passing_rows(start: date, *, id_start: int = 1) -> list[dict]:
    rows = []
    for index in range(10):
        day = start + timedelta(days=index % 5)
        rows.append(_outcome(day, candidate=True, index=id_start + index))
        rows.append(_outcome(day, candidate=False, index=id_start + 100 + index))
    return rows


def test_promotion_requires_independent_forward_holdout_sample():
    target = date(2026, 9, 8)
    base_rows = _passing_rows(date(2026, 9, 2))
    base_book = tuning._cohort_book(base_rows)

    first = tuning.decide_promotion(
        target,
        base_book,
        base_rows,
        source_quality_pass=True,
        prior_policy={},
    )

    assert first["status"] == "forward_holdout_armed"
    assert first["holdout_armed_since"] == target.isoformat()
    assert first["forward_holdout_pass"] is False

    post_rows = _passing_rows(date(2026, 9, 9), id_start=1_000)
    second = tuning.decide_promotion(
        date(2026, 9, 15),
        tuning._cohort_book(base_rows + post_rows),
        base_rows + post_rows,
        source_quality_pass=True,
        prior_policy={
            "status": "forward_holdout_armed",
            "holdout_armed_since": target.isoformat(),
        },
    )

    assert second["status"] == "live_auto_apply_ready"
    assert second["forward_holdout_pass"] is True
    assert second["forward_holdout_book"]["all"]["completed_outcome_count"] == 20


def test_promotion_fails_closed_on_source_quality():
    rows = _passing_rows(date(2026, 9, 2))

    decision = tuning.decide_promotion(
        date(2026, 9, 8),
        tuning._cohort_book(rows),
        rows,
        source_quality_pass=False,
        prior_policy={},
    )

    assert decision["status"] == "source_quality_blocked"
    assert decision["forward_holdout_pass"] is False


def test_post_apply_mature_negative_edge_rolls_back_to_zero_bonus():
    rows = _passing_rows(date(2026, 9, 9), id_start=2_000)
    for row in rows:
        row["lookup_attention_weight_runtime_policy_eligible"] = True
        row["lookup_attention_weight_policy_source_date"] = "2026-09-08"
        if row["cohort"] == "candidate":
            row["net_pnl_krw"] = -500.0
            row["net_return_pct"] = -0.5

    attribution = tuning.evaluate_post_apply(
        {
            "status": "live_auto_apply_ready",
            "holdout_armed_since": "2026-09-08",
        },
        rows,
    )

    assert attribution["mature"] is True
    assert attribution["pass"] is False
    assert attribution["rollback_triggered"] is True
    assert attribution["status"] == "rollback_mature_ev_or_tail_failure"


def test_post_apply_worst_loss_guard_rolls_back_before_sample_floor():
    row = _outcome(date(2026, 9, 9), candidate=True, index=3_000)
    row.update(
        {
            "net_pnl_krw": -6_000.0,
            "net_return_pct": -6.0,
            "lookup_attention_weight_runtime_policy_eligible": True,
            "lookup_attention_weight_policy_source_date": "2026-09-08",
        }
    )

    attribution = tuning.evaluate_post_apply(
        {
            "status": "live_auto_apply_ready",
            "holdout_armed_since": "2026-09-08",
        },
        [row],
    )

    assert attribution["mature"] is False
    assert attribution["rollback_triggered"] is True
    assert attribution["status"] == "rollback_worst_loss_guard"


def test_post_apply_excludes_prior_campaign_rows():
    prior_row = _outcome(date(2026, 9, 8), candidate=True, index=4_000)
    prior_row.update(
        {
            "net_pnl_krw": -6_000.0,
            "net_return_pct": -6.0,
            "lookup_attention_weight_runtime_policy_eligible": True,
            "lookup_attention_weight_policy_source_date": "2026-09-05",
        }
    )

    attribution = tuning.evaluate_post_apply(
        {
            "status": "live_auto_apply_ready",
            "holdout_armed_since": "2026-09-08",
        },
        [prior_row],
    )

    assert attribution["campaign_start"] == "2026-09-08"
    assert attribution["book"]["all"]["completed_outcome_count"] == 0
    assert attribution["rollback_triggered"] is False


def test_join_keeps_full_fill_separate_from_partial_and_scale_in():
    observations = [
        {
            "recommendation_id": 1,
            "scanner_promotion_id": "SCANPROM-005930-1",
            "stock_code": "005930",
            "observation_date": "2026-09-02",
            "lookup_attention_snapshot_score": 0.8,
            "fill_class": "full_fill",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        {
            "recommendation_id": 2,
            "scanner_promotion_id": "SCANPROM-000660-2",
            "stock_code": "000660",
            "observation_date": "2026-09-02",
            "lookup_attention_snapshot_score": 0.2,
            "fill_class": "partial_fill",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        {
            "recommendation_id": 3,
            "scanner_promotion_id": "SCANPROM-035420-3",
            "stock_code": "035420",
            "observation_date": "2026-09-02",
            "lookup_attention_snapshot_score": 0.8,
            "fill_class": "full_fill",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
    ]
    facts = [
        {
            "recommendation_id": item["recommendation_id"],
            "scanner_promotion_id": item["scanner_promotion_id"],
            "stock_code": item["stock_code"],
            "rec_date": "2026-09-02",
            "status": "COMPLETED",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 10_000,
            "buy_qty": 1,
            "sell_price": 10_100,
            "profit_rate": 1.0,
            "add_count": 1 if item["recommendation_id"] == 3 else 0,
            "avg_down_count": 0,
            "pyramid_count": 0,
        }
        for item in observations
    ]

    outcomes, exclusions = tuning.join_completed_outcomes(
        observations,
        facts,
        eligible_symbols={"005930", "000660", "035420"},
    )

    assert len(outcomes) == 1
    assert outcomes[0]["recommendation_id"] == 1
    assert outcomes[0]["comparison_cost_krw"] == 23.215
    assert exclusions == {
        "partial_fill": 1,
        "scale_in_or_average_down_confounded": 1,
    }


def test_join_rejects_cross_date_identity_even_when_record_and_promotion_match():
    observation = {
        "recommendation_id": 1,
        "scanner_promotion_id": "SCANPROM-005930-1",
        "stock_code": "005930",
        "observation_date": "2026-09-02",
        "lookup_attention_snapshot_score": 0.8,
        "fill_class": "full_fill",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    fact = {
        "recommendation_id": 1,
        "scanner_promotion_id": "SCANPROM-005930-1",
        "stock_code": "005930",
        "rec_date": "2026-09-03",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10_000,
        "buy_qty": 1,
        "sell_price": 10_100,
        "profit_rate": 1.0,
    }

    outcomes, exclusions = tuning.join_completed_outcomes(
        [observation], [fact], eligible_symbols={"005930"}
    )

    assert outcomes == []
    assert exclusions == {"exact_trade_date_mismatch": 1}


def test_armed_base_rows_are_frozen_before_forward_holdout():
    prior = {
        "status": "forward_holdout_armed",
        "holdout_armed_since": "2026-09-08",
    }
    rows = [
        _outcome(date(2026, 9, 8), candidate=True, index=1),
        _outcome(date(2026, 9, 9), candidate=True, index=2),
    ]

    frozen = tuning._base_rows_for_prior(rows, prior)

    assert [row["recommendation_id"] for row in frozen] == [1]


def test_source_quality_requires_every_outcome_date_audit(monkeypatch, tmp_path):
    monkeypatch.setattr(tuning, "SOURCE_AUDIT_DIR", tmp_path)
    for audit_date, allowed in (
        (date(2026, 9, 1), False),
        (date(2026, 9, 2), True),
    ):
        payload = {
            "target_date": audit_date.isoformat(),
            "status": "pass" if allowed else "fail",
            "summary": {
                "tuning_input_allowed": allowed,
                "hard_blocking_contract_gap_count": 0 if allowed else 1,
                "hard_blocking_excluded_row_count": 0,
                "blocked_reason": None if allowed else "contract_gap",
            },
        }
        (tmp_path / f"observation_source_quality_audit_{audit_date}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    quality = tuning._source_quality(
        date(2026, 9, 2), {date(2026, 9, 1), date(2026, 9, 2)}
    )

    assert quality["status"] == "source_quality_blocked"
    assert quality["blocked_dates"] == ["2026-09-01"]


def test_receipt_direction_accepts_only_buy_execution():
    assert tuning._receipt_is_buy({"905": "+매수", "907": "2"}) is True
    assert tuning._receipt_is_buy({"905": "-매도", "907": "1"}) is False
    assert tuning._receipt_is_buy({}) is False


def test_lookup_source_timestamp_requires_bounded_freshness():
    fields = {
        "realtime_lookup_source_date": "20260902",
        "realtime_lookup_source_time": "093000",
    }
    fresh = {
        "emitted_date": "2026-09-02",
        "emitted_at": "2026-09-02T09:31:00+09:00",
    }
    stale = {
        "emitted_date": "2026-09-02",
        "emitted_at": "2026-09-02T09:32:01+09:00",
    }

    assert tuning._source_timestamp_valid(fresh, fields) is True
    assert tuning._source_timestamp_valid(stale, fields) is False


def _valid_live_policy(source_date: date) -> dict:
    evidence = {
        "completed_outcome_count": 20,
        "trading_date_count": 5,
        "candidate_completed_outcome_count": 10,
        "candidate_trading_date_count": 3,
        "control_completed_outcome_count": 10,
        "control_trading_date_count": 3,
        "candidate_source_quality_adjusted_ev_pct": 0.5,
        "control_source_quality_adjusted_ev_pct": 0.1,
        "candidate_control_ev_uplift_pct": 0.4,
        "candidate_downside_p10_pct": -0.1,
        "control_downside_p10_pct": -0.1,
        "candidate_worst_net_return_pct": -1.0,
        "forward_holdout_completed_outcome_count": 20,
        "forward_holdout_trading_date_count": 5,
        "forward_holdout_candidate_completed_outcome_count": 10,
        "forward_holdout_candidate_trading_date_count": 3,
        "forward_holdout_control_completed_outcome_count": 10,
        "forward_holdout_control_trading_date_count": 3,
        "forward_holdout_candidate_source_quality_adjusted_ev_pct": 0.5,
        "forward_holdout_control_source_quality_adjusted_ev_pct": 0.1,
        "forward_holdout_candidate_control_ev_uplift_pct": 0.4,
        "forward_holdout_candidate_downside_p10_pct": -0.1,
        "forward_holdout_control_downside_p10_pct": -0.1,
        "forward_holdout_candidate_worst_net_return_pct": -1.0,
        "post_apply_mature": False,
    }
    payload = {
        "schema_version": policy.SCHEMA_VERSION,
        "report_type": policy.REPORT_TYPE,
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "decision_authority": policy.DECISION_AUTHORITY,
        "activation_mode": policy.ACTIVATION_MODE,
        "user_authority": policy.USER_AUTHORITY,
        "operator_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": True,
        "source_quality_status": "pass",
        "holdout_armed_since": source_date.isoformat(),
        "source_report_artifact_sha256": "a" * 64,
        "policy": {
            "policy_version": policy.POLICY_VERSION,
            "min_lookup_attention_score": policy.MIN_SCORE,
            "max_bonus_points": policy.MAX_BONUS_POINTS,
            "max_source_age_sec": policy.MAX_SOURCE_AGE_SEC,
            "rollback_bonus_points": 0.0,
            "same_priority_tier_only": True,
            "priority_tier_or_slot_change_allowed": False,
            "weight_formula": "linear_above_min_score_capped_at_max_bonus",
            "eligible_venues": policy.ELIGIBLE_VENUES,
            "eligible_session_buckets": policy.ELIGIBLE_SESSION_BUCKETS,
        },
        "evidence": evidence,
        "forbidden_uses": [
            "priority_tier_or_slot_ownership_change",
            "candidate_pool_or_source_eligibility_change",
            "buy_drop_threshold_or_provider_change",
            "order_price_quantity_cap_or_broker_guard_change",
            "stale_conflict_or_hard_safety_bypass",
        ],
    }
    payload["artifact_sha256"] = policy.canonical_sha256(payload)
    return payload


def test_runtime_loader_uses_only_latest_prior_trading_day_and_bounded_bonus(tmp_path):
    source_date = date(2026, 9, 1)
    payload = _valid_live_policy(source_date)
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report = {
        "schema_version": 1,
        "report_type": "scanner_lookup_attention_tuning",
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "decision_authority": policy.DECISION_AUTHORITY,
        "user_authority": policy.USER_AUTHORITY,
        "source_quality": {"status": "pass"},
        "official_symbol_master": {"status": "pass"},
        "runtime_policy_provenance_status": "pass",
        "policy_evidence_sha256": policy.canonical_sha256(payload["evidence"]),
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report["artifact_sha256"] = policy.canonical_sha256(report)
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    path = tmp_path / f"scanner_lookup_attention_policy_{source_date}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=report_dir
    )
    bonus = policy.bounded_bonus(0.8, loaded)

    assert loaded["active"] is True
    assert bonus["applied"] is True
    assert bonus["runtime_effect"] is True
    assert bonus["bonus_points"] == 100.0

    report["artifact_sha256"] = "0" * 64
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    policy.clear_policy_cache()
    rejected_report = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=report_dir
    )
    assert rejected_report["active"] is False
    assert rejected_report["reason"] == "prior_source_report_contract_invalid"

    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    payload["artifact_sha256"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    policy.clear_policy_cache()
    rejected = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=report_dir
    )
    assert rejected["active"] is False
    assert rejected["reason"] == "prior_policy_contract_invalid"


def test_runtime_loader_fails_closed_on_non_numeric_evidence(tmp_path):
    source_date = date(2026, 9, 1)
    payload = _valid_live_policy(source_date)
    payload["evidence"]["completed_outcome_count"] = "not-a-count"
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report = {
        "schema_version": 1,
        "report_type": "scanner_lookup_attention_tuning",
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "decision_authority": policy.DECISION_AUTHORITY,
        "user_authority": policy.USER_AUTHORITY,
        "source_quality": {"status": "pass"},
        "official_symbol_master": {"status": "pass"},
        "runtime_policy_provenance_status": "pass",
        "policy_evidence_sha256": policy.canonical_sha256(payload["evidence"]),
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report["artifact_sha256"] = policy.canonical_sha256(report)
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    (tmp_path / f"scanner_lookup_attention_policy_{source_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=report_dir
    )

    assert loaded["active"] is False
    assert loaded["reason"] == "prior_policy_contract_invalid"
    assert "policy_evidence_contract_invalid" in loaded["validation_errors"]


def test_runtime_loader_treats_valid_hold_policy_as_inactive_not_corrupt(tmp_path):
    source_date = date(2026, 9, 1)
    payload = _valid_live_policy(source_date)
    payload["status"] = "forward_holdout_armed"
    payload["allowed_runtime_apply"] = False
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    (tmp_path / f"scanner_lookup_attention_policy_{source_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=tmp_path / "unused"
    )

    assert loaded["active"] is False
    assert loaded["reason"] == "prior_policy_not_live_auto_apply_ready"
    assert loaded["promotion_status"] == "forward_holdout_armed"


def test_runtime_loader_rejects_report_policy_evidence_hash_mismatch(tmp_path):
    source_date = date(2026, 9, 1)
    payload = _valid_live_policy(source_date)
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report = {
        "schema_version": 1,
        "report_type": "scanner_lookup_attention_tuning",
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "decision_authority": policy.DECISION_AUTHORITY,
        "user_authority": policy.USER_AUTHORITY,
        "source_quality": {"status": "pass"},
        "official_symbol_master": {"status": "pass"},
        "runtime_policy_provenance_status": "pass",
        "policy_evidence_sha256": "0" * 64,
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report["artifact_sha256"] = policy.canonical_sha256(report)
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    (tmp_path / f"scanner_lookup_attention_policy_{source_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=tmp_path, report_dir=report_dir
    )

    assert loaded["active"] is False
    assert loaded["reason"] == "prior_source_report_contract_invalid"
