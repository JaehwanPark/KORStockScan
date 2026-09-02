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
    trading_days = []
    cursor = start
    while len(trading_days) < 5:
        if tuning.is_krx_trading_day(cursor):
            trading_days.append(cursor)
        cursor += timedelta(days=1)
    rows = []
    for index in range(10):
        day = trading_days[index % 5]
        rows.append(_outcome(day, candidate=True, index=id_start + index))
        rows.append(_outcome(day, candidate=False, index=id_start + 100 + index))
    return rows


def _write_live_pair(root, source_date: date) -> tuple[dict, dict]:
    policy_dir = root / "policies"
    report_dir = root / "reports"
    policy_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)
    payload = _valid_live_policy(source_date)
    base_book = tuning._cohort_book(_passing_rows(source_date))
    holdout_book = tuning._cohort_book(_passing_rows(source_date, id_start=10_000))
    post_apply_book = tuning._cohort_book([])
    report = {
        "schema_version": tuning.SCHEMA_VERSION,
        "report_type": "scanner_lookup_attention_tuning",
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "metric_role": "primary_ev",
        "decision_authority": policy.DECISION_AUTHORITY,
        "window_policy": "rolling_90_calendar_days_clean_post_rollout",
        "sample_floor": "base_and_independent_forward_holdout_each_total20_dates5_candidate10_control10_cohort_dates3",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "daily_audit_exact_lineage_full_fill_official_common_stock_and_effective_cost",
        "forbidden_uses": list(tuning.FORBIDDEN_USES),
        "user_authority": policy.USER_AUTHORITY,
        "operator_approval_required": False,
        "source_quality": {"status": "pass"},
        "official_symbol_master": {"status": "pass"},
        "runtime_policy_provenance_status": "pass",
        "policy_evidence_sha256": policy.canonical_sha256(payload["evidence"]),
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "holdout_armed_since": source_date.isoformat(),
        "full_fill_contract": tuning.FULL_FILL_CONTRACT,
        "cost_contract": {
            **tuning.COST_CONTRACT,
            "contract_sha256": policy.canonical_sha256(tuning.COST_CONTRACT),
        },
        "base_book": base_book,
        "forward_holdout_book": holdout_book,
        "base_gate": {"pass": True, "reasons": []},
        "forward_holdout_gate": {"pass": True, "reasons": []},
        "post_apply_attribution": {
            "status": "collecting",
            "mature": False,
            "pass": None,
            "rollback_triggered": False,
            "book": post_apply_book,
        },
    }
    report["artifact_sha256"] = policy.canonical_sha256(report)
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    (report_dir / f"scanner_lookup_attention_tuning_{source_date}.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    (policy_dir / f"scanner_lookup_attention_policy_{source_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return report, payload


def _observation_event(*, day: date = date(2026, 9, 2), record_id: object = 1):
    compact = day.strftime("%Y%m%d")
    return {
        "stage": "scalping_scanner_runtime_target_attach",
        "stock_code": "005930",
        "emitted_date": day.isoformat(),
        "emitted_at": f"{day.isoformat()}T09:31:00+09:00",
        "fields": {
            "runtime_record_id": record_id,
            "scanner_promotion_id": "SCANPROM-005930-1",
            "lookup_attention_state": "observed_source_only",
            "lookup_attention_snapshot_score": 0.8,
            "realtime_lookup_source_date": compact,
            "realtime_lookup_source_time": "093000",
            "lookup_attention_runtime_effect": False,
            "lookup_attention_allowed_runtime_apply": False,
            "lookup_attention_actual_order_submitted": False,
            "lookup_attention_broker_order_forbidden": True,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
    }


def _receipt_event(
    *,
    requested: object = 1,
    filled: object = 1,
    remaining: object = 0,
    side_text: str = "+매수",
    side_code: str = "2",
):
    return {
        "stage": "position_rebased_after_fill",
        "stock_code": "005930",
        "emitted_date": "2026-09-02",
        "emitted_at": "2026-09-02T09:32:00+09:00",
        "fields": {
            "runtime_record_id": 1,
            "scanner_promotion_id": "SCANPROM-005930-1",
            "905": side_text,
            "907": side_code,
            "fill_quality": "FULL_FILL",
            "order_requested_qty": requested,
            "order_filled_qty": filled,
            "order_remaining_qty": remaining,
            "receipt_quantity_contract_complete": True,
            "main_lifecycle_venue": "KRX",
            "main_lifecycle_session_bucket": "krx_regular",
            "main_lifecycle_trade_date": "2026-09-02",
        },
    }


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
            "report_type": "observation_source_quality_audit",
            "target_date": audit_date.isoformat(),
            "status": "pass" if allowed else "fail",
            "summary": {
                "tuning_input_allowed": allowed,
                "hard_blocking_contract_gap_count": 0 if allowed else 1,
                "hard_blocking_excluded_row_count": 0,
                "blocked_reason": None if allowed else "contract_gap",
                "review_warning_count": 0,
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


def test_source_quality_rejects_fractional_hard_gap_count(monkeypatch, tmp_path):
    monkeypatch.setattr(tuning, "SOURCE_AUDIT_DIR", tmp_path)
    audit_date = date(2026, 9, 2)
    payload = {
        "report_type": "observation_source_quality_audit",
        "target_date": audit_date.isoformat(),
        "status": "pass",
        "summary": {
            "tuning_input_allowed": True,
            "hard_blocking_contract_gap_count": 0.5,
            "hard_blocking_excluded_row_count": 0,
            "blocked_reason": None,
            "review_warning_count": 0,
        },
    }
    (tmp_path / f"observation_source_quality_audit_{audit_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    quality = tuning._source_quality(audit_date)

    assert quality["status"] == "source_quality_blocked"
    assert quality["audits"][0]["hard_blocking_contract_gap_count"] is None


def test_symbol_master_rejects_fractional_census_count(monkeypatch, tmp_path):
    monkeypatch.setattr(tuning, "SYMBOL_MASTER_DIR", tmp_path)
    source_date = date(2026, 9, 1)
    target = date(2026, 9, 2)
    upstream_hash = "a" * 64
    payload = {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "verified": True,
        "verification_status": "verified",
        "source_artifacts": [
            {
                "source_id": "kis-official-common-stock-master-2026-09-01",
                "verified": True,
                "status": "verified",
                "expected_sha256": upstream_hash,
                "observed_sha256": upstream_hash,
                "kind": "symbol_product_master",
                "payload_schema": "micro_reversion_raw_symbol_product_master_v3",
                "effective_from": source_date.isoformat(),
                "record_count": 1,
                "expected_size_bytes": 100,
                "observed_size_bytes": 100,
            }
        ],
        "census": {"record_count": 1.5, "symbol_count": 1},
        "records": [
            {
                "symbol": "005930",
                "metadata_source": "official_symbol_product_master_v2",
                "instrument_type": "EQUITY",
                "listing_market": "KOSPI",
                "conflict_status": "clean",
                "effective_from": source_date.isoformat(),
                "effective_to": None,
            }
        ],
    }
    payload["content_sha256"] = policy.canonical_sha256(payload)
    (tmp_path / f"micro_reversion_symbol_master_{source_date}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    symbols, provenance = tuning._latest_symbol_master(target)

    assert symbols == set()
    assert provenance["status"] == "contract_invalid"


def test_receipt_direction_accepts_only_buy_execution():
    assert tuning._receipt_is_buy({"905": "+매수", "907": "2"}) is True
    assert tuning._receipt_is_buy({"905": "-매도", "907": "1"}) is False
    assert tuning._receipt_side({"905": "-매도", "907": "2"}) == "conflict"
    assert tuning._receipt_is_buy({}) is False


def test_lineage_blocks_malformed_json_and_conflicting_receipt_side(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(tuning, "EVENT_DIR", tmp_path)
    event_path = tmp_path / "pipeline_events_2026-09-02.jsonl"
    event_path.write_text(
        "\n".join(
            [
                json.dumps(_observation_event(), ensure_ascii=False),
                "{malformed",
                json.dumps(
                    _receipt_event(side_text="-매도", side_code="2"),
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rows, lineage = tuning.collect_lineage(date(2026, 9, 2))

    assert lineage["malformed_json_line_count"] == 1
    assert lineage["invalid_fill_contract_count"] == 1
    assert rows[0]["fill_class"] == "fill_contract_invalid"


def test_lineage_does_not_truncate_fractional_fill_quantity(monkeypatch, tmp_path):
    monkeypatch.setattr(tuning, "EVENT_DIR", tmp_path)
    event_path = tmp_path / "pipeline_events_2026-09-02.jsonl"
    event_path.write_text(
        "\n".join(
            [
                json.dumps(_observation_event(), ensure_ascii=False),
                json.dumps(
                    _receipt_event(requested=1.5, filled=1.5),
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rows, lineage = tuning.collect_lineage(date(2026, 9, 2))

    assert lineage["invalid_fill_contract_count"] == 1
    assert rows[0]["fill_class"] == "fill_contract_invalid"


def test_lineage_blocks_missing_runtime_hook_when_prior_policy_requires_live_use(
    monkeypatch, tmp_path
):
    event_dir = tmp_path / "events"
    event_dir.mkdir()
    _write_live_pair(tmp_path, date(2026, 9, 1))
    monkeypatch.setattr(tuning, "EVENT_DIR", event_dir)
    monkeypatch.setattr(tuning, "POLICY_DIR", tmp_path / "policies")
    monkeypatch.setattr(tuning, "REPORT_DIR", tmp_path / "reports")
    (event_dir / "pipeline_events_2026-09-02.jsonl").write_text(
        json.dumps(_observation_event(), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    rows, lineage = tuning.collect_lineage(date(2026, 9, 2))

    assert len(rows) == 1
    assert lineage["invalid_runtime_policy_provenance_count"] == 1
    assert rows[0]["lookup_attention_weight_runtime_policy_eligible"] is False


def test_lineage_accepts_exact_hash_bound_active_runtime_provenance(
    monkeypatch, tmp_path
):
    event_dir = tmp_path / "events"
    event_dir.mkdir()
    _, live_policy = _write_live_pair(tmp_path, date(2026, 9, 1))
    monkeypatch.setattr(tuning, "EVENT_DIR", event_dir)
    monkeypatch.setattr(tuning, "POLICY_DIR", tmp_path / "policies")
    monkeypatch.setattr(tuning, "REPORT_DIR", tmp_path / "reports")
    observation = _observation_event()
    observation["fields"].update(
        {
            "lookup_attention_weight_policy_state": "applied_same_priority_tier",
            "lookup_attention_weight_policy_reason": "bounded_linear_bonus",
            "lookup_attention_weight_policy_version": policy.POLICY_VERSION,
            "lookup_attention_weight_policy_source_date": "2026-09-01",
            "lookup_attention_weight_policy_artifact_sha256": live_policy[
                "artifact_sha256"
            ],
            "lookup_attention_weight_decision_authority": policy.DECISION_AUTHORITY,
            "lookup_attention_weight_same_priority_tier_only": True,
            "lookup_attention_weight_eligible_venues": "KRX",
            "lookup_attention_weight_eligible_session_buckets": "krx_regular",
            "lookup_attention_weight_effective_venue": "KRX",
            "lookup_attention_weight_market_session_bucket": "krx_regular",
            "lookup_attention_weight_source_age_sec": 30.0,
            "lookup_attention_weight_source_fresh": True,
            "lookup_attention_weight_max_source_age_sec": 120.0,
            "lookup_attention_weight_bonus_points": 100.0,
            "lookup_attention_weight_policy_applied": True,
            "lookup_attention_weight_runtime_effect": True,
            "lookup_attention_weight_allowed_runtime_apply": True,
            "lookup_attention_weight_actual_order_submitted": False,
            "lookup_attention_weight_broker_order_forbidden": True,
            "lookup_attention_weight_rollback_bonus_points": 0.0,
            "lookup_attention_weight_forbidden_uses": ",".join(tuning.FORBIDDEN_USES),
        }
    )
    (event_dir / "pipeline_events_2026-09-02.jsonl").write_text(
        json.dumps(observation, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    rows, lineage = tuning.collect_lineage(date(2026, 9, 2))

    assert lineage["invalid_runtime_policy_provenance_count"] == 0
    assert rows[0]["lookup_attention_weight_runtime_policy_eligible"] is True


def test_lineage_does_not_require_krx_policy_hook_for_out_of_scope_nxt(
    monkeypatch, tmp_path
):
    event_dir = tmp_path / "events"
    event_dir.mkdir()
    _write_live_pair(tmp_path, date(2026, 9, 1))
    monkeypatch.setattr(tuning, "EVENT_DIR", event_dir)
    monkeypatch.setattr(tuning, "POLICY_DIR", tmp_path / "policies")
    monkeypatch.setattr(tuning, "REPORT_DIR", tmp_path / "reports")
    observation = _observation_event()
    observation["fields"].update(
        {"effective_venue": "NXT", "market_session_bucket": "nxt_regular"}
    )
    (event_dir / "pipeline_events_2026-09-02.jsonl").write_text(
        json.dumps(observation, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    rows, lineage = tuning.collect_lineage(date(2026, 9, 2))

    assert len(rows) == 1
    assert lineage["invalid_runtime_policy_provenance_count"] == 0
    assert rows[0]["lookup_attention_weight_runtime_policy_eligible"] is False


def test_join_treats_policy_floor_as_control_because_bonus_is_zero():
    observation = {
        "recommendation_id": 1,
        "scanner_promotion_id": "SCANPROM-005930-1",
        "stock_code": "005930",
        "observation_date": "2026-09-02",
        "lookup_attention_snapshot_score": policy.MIN_SCORE,
        "fill_class": "full_fill",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    fact = {
        "recommendation_id": 1,
        "scanner_promotion_id": "SCANPROM-005930-1",
        "stock_code": "005930",
        "rec_date": "2026-09-02",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10_000,
        "buy_qty": 1,
        "sell_price": 10_100,
        "profit_rate": 1.0,
        "add_count": 0,
        "avg_down_count": 0,
        "pyramid_count": 0,
    }

    outcomes, exclusions = tuning.join_completed_outcomes(
        [observation], [fact], eligible_symbols={"005930"}
    )

    assert exclusions == {}
    assert outcomes[0]["cohort"] == "control"


def test_join_rejects_fractional_scale_in_count_and_quantity():
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
    base_fact = {
        "recommendation_id": 1,
        "scanner_promotion_id": "SCANPROM-005930-1",
        "stock_code": "005930",
        "rec_date": "2026-09-02",
        "status": "COMPLETED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10_000,
        "buy_qty": 1,
        "sell_price": 10_100,
        "profit_rate": 1.0,
        "add_count": 0.5,
        "avg_down_count": 0,
        "pyramid_count": 0,
    }

    outcomes, exclusions = tuning.join_completed_outcomes(
        [observation], [base_fact], eligible_symbols={"005930"}
    )
    assert outcomes == []
    assert exclusions == {"scale_in_count_contract_invalid": 1}

    fractional_qty = {**base_fact, "add_count": 0, "buy_qty": 1.5}
    outcomes, exclusions = tuning.join_completed_outcomes(
        [observation], [fractional_qty], eligible_symbols={"005930"}
    )
    assert outcomes == []
    assert exclusions == {"economics_input_invalid": 1}


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
    evidence = tuning._evidence(
        tuning._cohort_book(_passing_rows(source_date)),
        tuning._cohort_book(_passing_rows(source_date, id_start=10_000)),
        tuning._cohort_book([]),
        post_apply_mature=False,
    )
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
    report, payload = _write_live_pair(tmp_path, source_date)
    policy_dir = tmp_path / "policies"
    report_dir = tmp_path / "reports"
    report_path = report_dir / f"scanner_lookup_attention_tuning_{source_date}.json"
    path = policy_dir / f"scanner_lookup_attention_policy_{source_date}.json"
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=policy_dir, report_dir=report_dir
    )
    bonus = policy.bounded_bonus(0.8, loaded)

    assert loaded["active"] is True
    assert bonus["applied"] is True
    assert bonus["runtime_effect"] is True
    assert bonus["bonus_points"] == 100.0

    report["artifact_sha256"] = "0" * 64
    report_path.write_text(json.dumps(report), encoding="utf-8")
    policy.clear_policy_cache()
    rejected_report = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=policy_dir, report_dir=report_dir
    )
    assert rejected_report["active"] is False
    assert rejected_report["reason"] == "prior_source_report_contract_invalid"

    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    payload["artifact_sha256"] = "0" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")
    policy.clear_policy_cache()
    rejected = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=policy_dir, report_dir=report_dir
    )
    assert rejected["active"] is False
    assert rejected["reason"] == "prior_policy_contract_invalid"


def test_runtime_loader_rejects_hash_consistent_report_cost_contract_mismatch(
    tmp_path,
):
    source_date = date(2026, 9, 1)
    report, payload = _write_live_pair(tmp_path, source_date)
    report["cost_contract"]["buy_fee_bps"] = 0.0
    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )
    report_path = (
        tmp_path / "reports" / f"scanner_lookup_attention_tuning_{source_date}.json"
    )
    policy_path = (
        tmp_path / "policies" / f"scanner_lookup_attention_policy_{source_date}.json"
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        date(2026, 9, 2),
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
    )

    assert loaded["active"] is False
    assert loaded["reason"] == "prior_source_report_contract_invalid"


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
        "schema_version": policy.TUNING_REPORT_SCHEMA_VERSION,
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
        "schema_version": policy.TUNING_REPORT_SCHEMA_VERSION,
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


def test_runtime_loader_recovers_when_prior_artifacts_appear_without_cache_clear(
    tmp_path,
):
    source_date = date(2026, 9, 1)
    policy_dir = tmp_path / "policies"
    report_dir = tmp_path / "reports"
    policy_dir.mkdir()
    report_dir.mkdir()
    policy.clear_policy_cache()

    missing = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=policy_dir, report_dir=report_dir
    )
    assert missing["reason"] == "prior_policy_missing"

    _write_live_pair(tmp_path, source_date)
    recovered = policy.load_active_policy(
        date(2026, 9, 2), policy_dir=policy_dir, report_dir=report_dir
    )

    assert recovered["active"] is True
    assert recovered["policy_source_date"] == source_date.isoformat()


def test_runtime_loader_ignores_nontrading_day_artifact_for_latest_prior_policy(
    tmp_path,
):
    friday = date(2026, 9, 4)
    saturday = date(2026, 9, 5)
    monday = date(2026, 9, 7)
    _write_live_pair(tmp_path, friday)
    (
        tmp_path / "policies" / f"scanner_lookup_attention_policy_{saturday}.json"
    ).write_text("{}", encoding="utf-8")
    policy.clear_policy_cache()

    loaded = policy.load_active_policy(
        monday,
        policy_dir=tmp_path / "policies",
        report_dir=tmp_path / "reports",
    )

    assert loaded["active"] is True
    assert loaded["policy_source_date"] == friday.isoformat()


def test_artifact_validator_rejects_hash_consistent_evidence_not_derived_from_books(
    tmp_path,
):
    source_date = date(2026, 9, 1)
    report, payload = _write_live_pair(tmp_path, source_date)
    payload["evidence"]["candidate_source_quality_adjusted_ev_pct"] = 0.75
    report["policy_evidence_sha256"] = policy.canonical_sha256(payload["evidence"])
    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )

    issues = tuning.validate_artifact_pair(report, payload, target=source_date)

    assert "policy_evidence_not_derived_from_report_books" in issues


def test_artifact_validator_rejects_forward_status_after_holdout_gate_pass(tmp_path):
    source_date = date(2026, 9, 1)
    report, payload = _write_live_pair(tmp_path, source_date)
    report["status"] = "forward_holdout_armed"
    report["allowed_runtime_apply"] = False
    report["forward_holdout_gate"] = {"pass": False, "reasons": ["collecting"]}
    payload["status"] = "forward_holdout_armed"
    payload["allowed_runtime_apply"] = False
    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )

    issues = tuning.validate_artifact_pair(report, payload, target=source_date)

    assert "promotion_policy_holdout_gate_inconsistent" in issues
    assert "forward_holdout_status_stale_after_gate_pass" in issues


def test_artifact_validator_requires_boolean_post_apply_state(tmp_path):
    source_date = date(2026, 9, 1)
    report, payload = _write_live_pair(tmp_path, source_date)
    report["post_apply_attribution"]["mature"] = "false"
    report["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    payload["source_report_artifact_sha256"] = report["artifact_sha256"]
    payload["artifact_sha256"] = policy.canonical_sha256(
        {key: value for key, value in payload.items() if key != "artifact_sha256"}
    )

    issues = tuning.validate_artifact_pair(report, payload, target=source_date)

    assert "post_apply_mature_not_boolean" in issues


def test_artifact_validator_fails_closed_instead_of_crashing_on_malformed_books():
    issues = tuning.validate_artifact_pair(
        {"base_book": [], "forward_holdout_book": {}, "post_apply_attribution": []},
        {},
        target=date(2026, 9, 2),
    )

    assert "report_evidence_source_books_invalid" in issues
