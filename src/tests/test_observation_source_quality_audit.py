import json
import subprocess
from pathlib import Path

from src.engine import observation_source_quality_audit as audit


def _event(stage: str, fields: dict, *, record_id: int = 1) -> dict:
    return {
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_name": "TEST",
        "stock_code": "123456",
        "record_id": record_id,
        "fields": fields,
        "emitted_at": "2026-05-15T10:00:00",
        "emitted_date": "2026-05-15",
    }


def _write_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_market_halt_window_artifact_is_not_gitignored():
    path = Path("data/source_quality/market_halt_windows/windows/2026-06-08.json")
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
    )

    assert result.returncode == 1


def test_market_halt_session_events_artifact_is_gitignored():
    path = Path("data/source_quality/market_halt_windows/session_events/2026-06-08.json")
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
    )

    assert result.returncode == 0


def test_observation_source_quality_audit_flags_missing_ai_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "ai_confirmed",
                {
                    "tick_source_quality_fields_sent": True,
                    "tick_accel_source": "computed_10ticks",
                    "tick_context_quality": "fresh_computed",
                    "quote_age_source": "missing",
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "-1.0",
                    "intraday_range_pct": "4.0",
                },
            ),
            _event(
                "blocked_ai_score",
                {
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "0.0",
                    "intraday_range_pct": "0.0",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "warning"
    blocked = report["stage_contracts"]["blocked_ai_score"]
    assert blocked["status"] == "warning"
    assert "tick_accel_source" in blocked["missing_violations"]
    assert blocked["zero_violations"]["intraday_range_pct"] == 1.0
    assert report["summary"]["tuning_input_allowed"] is False
    assert "blocked_ai_score" in report["summary"]["hard_blocking_stages"]
    assert report["summary"]["blocked_reason"] == "blocked_contract_gap"


def test_observation_source_quality_audit_detects_high_volume_contract_gap(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event("strength_momentum_observed", {"reason": "below_strength_base"}, record_id=idx)
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    gaps = {item["stage"]: item for item in report["high_volume_no_source_fields"]}
    assert gaps["strength_momentum_observed"]["event_count"] == 60
    assert report["policy"]["decision_authority"] == "source_quality_only"
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_contract_gap_count"] == 1


def test_observation_source_quality_audit_warns_on_high_rate_unknown_tokens(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_stale_bucket": "stale_unknown",
                    "entry_adm_overbought_bucket": "overbought_unknown",
                    "entry_adm_liquidity_bucket": "liquidity_high",
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "warning"
    assert report["summary"]["unknown_token_stage_count"] == 1
    finding = report["unknown_token_findings"][0]
    assert finding["stage"] == "scalp_entry_action_decision_snapshot"
    fields = {item["field"]: item for item in finding["fields"]}
    assert fields["entry_adm_score_bucket"]["rate"] == 1.0
    assert fields["entry_adm_stale_bucket"]["rate"] == 1.0
    assert finding["decision_authority"] == "source_quality_only"
    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["review_warning_count"] == 1
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert finding["runtime_effect"] is False


def test_observation_source_quality_audit_warns_on_any_unknown_token_field(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "arbitrary_source_stage",
            {
                "source_id": f"SRC-{idx}",
                "custom_context_state": "custom_unknown_placeholder" if idx == 7 else "observed",
            },
            record_id=idx,
        )
        for idx in range(100)
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["status"] == "warning"
    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["review_warning_count"] == 1
    assert report["summary"]["tuning_input_allowed"] is True
    finding = report["unknown_token_findings"][0]
    assert finding["stage"] == "arbitrary_source_stage"
    fields = {item["field"]: item for item in finding["fields"]}
    assert fields["custom_context_state"]["count"] == 1
    assert fields["custom_context_state"]["rate"] == 0.01


def test_observation_source_quality_audit_separates_reviewed_unknown_tokens(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "orderbook_stability_observed",
            {
                "orderbook_micro_ofi_bucket_key": "spread=unknown|price=unknown|depth=unknown|sample=insufficient",
                "custom_context_state": "observed",
            },
            record_id=1,
        ),
        _event(
            "orderbook_stability_observed",
            {
                "orderbook_micro_ofi_bucket_key": "spread=known|price=known|depth=known|sample=ok",
                "custom_context_state": "custom_unknown_placeholder",
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 1
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    finding = report["unknown_token_findings"][0]
    assert {field["field"] for field in finding["fields"]} == {"custom_context_state"}
    reviewed = report["reviewed_unknown_token_findings"][0]
    reviewed_fields = {field["field"]: field for field in reviewed["fields"]}
    assert reviewed_fields["orderbook_micro_ofi_bucket_key"]["reviewed_reason"] == "reviewed_insufficient_sample"


def test_observation_source_quality_audit_reviews_missing_risk_regime_context(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "metric_role": "action_decision_matrix",
                    "decision_authority": "entry_advisory_prompt_context_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "risk_regime_context": {
                        "panic_context_status": "MISSING",
                        "panic_level_reason": "context_not_ok",
                        "panic_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                        "market_risk_state": "UNKNOWN",
                    },
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed = report["reviewed_unknown_token_findings"][0]
    assert reviewed["stage"] == "scalp_entry_action_decision_snapshot"
    assert reviewed["fields"][0]["reviewed_reason"] == "reviewed_missing_risk_regime_context"
    assert reviewed["runtime_effect"] is False


def test_observation_source_quality_audit_reviews_panic_context_warning_unknown_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_panic_context_warning",
                {
                    "panic_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                    "market_risk_state": "UNKNOWN",
                    "liquidity_state": "UNKNOWN",
                    "risk_regime_epoch_id": "2026-06-04|NORMAL|NORMAL|L0|unknown",
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["summary"]["unknown_token_stage_count"] == 0
    assert report["summary"]["reviewed_unknown_token_stage_count"] == 1
    reviewed_fields = {
        item["field"]: item for item in report["reviewed_unknown_token_findings"][0]["fields"]
    }
    assert reviewed_fields["panic_epoch_id"]["reviewed_reason"] == "reviewed_missing_risk_regime_context"
    assert reviewed_fields["market_risk_state"]["reviewed_reason"] == "reviewed_missing_risk_regime_context"


def test_observation_source_quality_audit_warns_on_top_level_and_all_unknown_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {f"custom_unknown_field_{idx}": "value_unknown" for idx in range(25)}
    rows = [
        {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stage": "unknown_custom_stage",
            "stock_name": "TEST",
            "stock_code": "123456",
            "record_id": 1,
            "fields": fields,
            "emitted_at": "2026-06-04T10:00:00",
            "emitted_date": "2026-06-04",
        }
    ]
    _write_events(tmp_path, "2026-06-04", rows)

    report = audit.build_observation_source_quality_audit("2026-06-04")

    finding = report["unknown_token_findings"][0]
    found_fields = {item["field"] for item in finding["fields"]}
    assert "__stage" in found_fields
    for idx in range(25):
        assert f"custom_unknown_field_{idx}" in found_fields


def test_observation_source_quality_audit_has_entry_micro_context_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "swing_entry_micro_context_observed",
                {
                    "orderbook_micro_ready": False,
                    "orderbook_micro_state": "insufficient",
                    "orderbook_micro_reason": "missing_snapshot",
                    "orderbook_micro_snapshot_age_ms": 0,
                    "orderbook_micro_observer_healthy": False,
                    "swing_micro_runtime_effect": False,
                    "swing_micro_observe_only": True,
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["swing_entry_micro_context_observed"]
    assert contract["status"] == "pass"
    assert contract["decision_authority"] == "source_quality_only"
    assert contract["runtime_effect"] is False


def test_observation_source_quality_audit_accepts_high_volume_contract_labels(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "strength_momentum_observed",
                {
                    "reason": "below_strength_base",
                    "metric_role": "ops_volume_diagnostic",
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []


def test_observation_source_quality_audit_accepts_order_failure_diagnostic_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event("order_bundle_failed", {"reason": "broker_receipt_missing"}, record_id=idx)
            for idx in range(60)
        ]
        + [
            _event("order_leg_fail", {"reason": "leg_rejected"}, record_id=idx + 100)
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["field_presence_top"]["order_bundle_failed"]["metric_role"] == 60
    assert report["field_presence_top"]["order_leg_fail"]["metric_role"] == 60


def test_observation_source_quality_audit_enforces_sim_authority_contracts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_duplicate_buy_signal",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-1",
                    "threshold_family": "entry_mechanical_momentum",
                    "sim_parent_record_id": 101,
                },
            ),
            _event(
                "swing_probe_discarded",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "evidence_quality": "quota_observation",
                    "source_record_id": "SRC-1",
                    "probe_origin_stage": "blocked_swing_score_vpw",
                    "discard_reason": "max_per_symbol_reached",
                    "blocker_authority": "probe_capacity_only",
                    "quota_observation_scope": "symbol_probe_quota",
                    "allowed_runtime_apply": False,
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["stage_contracts"]["scalp_sim_duplicate_buy_signal"]["status"] == "warning"
    assert (
        report["stage_contracts"]["scalp_sim_duplicate_buy_signal"]["missing_violations"]["runtime_effect"]
        == 1.0
    )
    assert report["stage_contracts"]["swing_probe_discarded"]["status"] == "warning"
    assert report["stage_contracts"]["swing_probe_discarded"]["missing_violations"]["decision_authority"] == 1.0


def test_observation_source_quality_audit_accepts_complete_sim_authority_contracts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "scalp_sim_duplicate_buy_signal",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "sim_observation_skipped",
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-1",
                    "threshold_family": "entry_mechanical_momentum",
                    "sim_parent_record_id": 101,
                },
            ),
            _event(
                "scalp_sim_entry_submit_revalidation_warning",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "sim_entry_pre_submit_warning_only",
                    "decision_authority": "sim_observation_only",
                    "sim_record_id": "SIM-2",
                    "threshold_family": "pre_submit_price_guard",
                    "sim_parent_record_id": 102,
                    "entry_submit_revalidation_warning": "stale_context_or_quote",
                    "quote_age_at_submit_ms": 1500,
                    "submitted_order_price": 10000,
                    "mark_price_at_submit": 9990,
                },
                record_id=2,
            ),
            _event(
                "swing_probe_discarded",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "decision_authority": "swing_sim_exploration_only",
                    "evidence_quality": "quota_observation",
                    "source_record_id": "SRC-1",
                    "probe_origin_stage": "blocked_swing_score_vpw",
                    "discard_reason": "max_per_symbol_reached",
                    "blocker_authority": "probe_capacity_only",
                    "quota_observation_scope": "symbol_probe_quota",
                    "allowed_runtime_apply": False,
                },
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    assert report["stage_contracts"]["scalp_sim_duplicate_buy_signal"]["status"] == "pass"
    assert report["stage_contracts"]["scalp_sim_entry_submit_revalidation_warning"]["status"] == "pass"
    assert report["stage_contracts"]["swing_probe_discarded"]["status"] == "pass"


def test_observation_source_quality_audit_normalizes_pre_contract_ai_and_latency(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-21",
        [
            _event(
                "ai_confirmed",
                {
                    "latest_strength": "120.0",
                    "buy_pressure_10t": "61.0",
                    "distance_from_day_high_pct": "-1.0",
                    "intraday_range_pct": "4.0",
                },
                record_id=1,
            ),
            _event(
                "latency_block",
                {
                    "reason": "latency_fallback_deprecated",
                    "latency_state": "CAUTION",
                    "effective_decision": "WAIT_REQUOTE",
                    "quote_stale": False,
                    "signal_price": 10000,
                    "latest_price": 10010,
                    "latency_canary_applied": False,
                    "threshold_family": "latency_classifier_runtime_profile",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                record_id=2,
            ),
            _event(
                "latency_pass",
                {
                    "reason": "safe",
                    "latency_state": "SAFE",
                    "policy_decision": "ALLOW_SUBMIT",
                    "effective_decision": "ALLOW_SUBMIT",
                    "ws_age_ms": 10,
                    "ws_jitter_ms": 2,
                    "spread_ratio": "0.001",
                    "quote_stale": False,
                    "signal_price": 10000,
                    "latest_price": 10000,
                    "latency_canary_applied": False,
                    "threshold_family": "latency_classifier_runtime_profile",
                    "runtime_effect": False,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
                record_id=3,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-21")

    assert report["stage_contracts"]["ai_confirmed"]["status"] == "pass"
    assert report["stage_contracts"]["latency_block"]["status"] == "pass"
    assert report["stage_contracts"]["latency_pass"]["status"] == "pass"


def test_observation_source_quality_audit_accepts_real_execution_diagnostic_contracts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-21",
        [
            _event("holding_started", {"strategy": "SCALPING", "buy_qty": 1}, record_id=idx)
            for idx in range(60)
        ]
        + [
            _event("scale_in_executed", {"add_type": "PYRAMID", "new_buy_qty": 2}, record_id=100 + idx)
            for idx in range(60)
        ]
        + [
            _event(
                "same_symbol_loss_reentry_cooldown",
                {"exit_rule": "scalp_soft_stop_pct", "profit_rate": "-1.0", "cooldown_sec": 3600},
                record_id=200 + idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-21")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["holding_started"]["status"] == "pass"
    assert report["stage_contracts"]["scale_in_executed"]["status"] == "pass"
    assert report["stage_contracts"]["same_symbol_loss_reentry_cooldown"]["status"] == "pass"


def test_observation_source_quality_audit_blocks_swing_loss_reentry_placeholder_source(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    contract = report["stage_contracts"]["swing_same_symbol_loss_reentry_cooldown"]
    assert contract["status"] == "warning"
    assert contract["missing_violations"]["source_probe_id"] == 1.0
    assert contract["missing_violations"]["source_record_id"] == 1.0
    assert report["summary"]["tuning_input_allowed"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 1
    assert report["hard_blocking_row_exclusions"][0]["stage"] == "swing_same_symbol_loss_reentry_cooldown"


def test_observation_source_quality_write_excludes_bad_rows_instead_of_blocking_full_date(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    valid_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": "-",
                    "source_record_id": "-",
                    "source_stage": "exit",
                },
                record_id=1,
            ),
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": valid_id,
                    "source_record_id": valid_id,
                    "source_stage": "exit",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.write_report("2026-06-04")
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl"
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]

    assert report["summary"]["tuning_input_allowed"] is True
    assert report["summary"]["hard_blocking_contract_gap_count"] == 0
    assert report["summary"]["raw_row_exclusion_applied"] is True
    assert report["raw_row_exclusion"]["excluded_row_count"] == 1
    assert len(rows) == 1
    assert rows[0]["record_id"] == 2
    manifest = Path(report["raw_row_exclusion"]["manifest_path"])
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["policy"] == "exclude_defective_rows_not_full_day_raw"
    assert payload["excluded_row_count"] == 1
    assert payload["stage_counts"] == {"swing_same_symbol_loss_reentry_cooldown": 1}
    assert payload["field_gap_counts"] == {
        "missing_fields:source_probe_id": 1,
        "missing_fields:source_record_id": 1,
    }
    assert payload["exclusion_reasons"]["required_field_missing"] == 1
    assert payload["exclusion_reasons"]["provenance_missing"] == 1
    assert payload["producer_hint"][0]["stage"] == "swing_same_symbol_loss_reentry_cooldown"
    assert payload["sample_rows"][0]["gap_fields"]["missing_fields"] == [
        "source_probe_id",
        "source_record_id",
    ]
    assert Path(payload["backup_path"]).exists()


def test_observation_source_quality_raw_row_exclusion_summary_is_stage_generic(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    monkeypatch.setitem(
        audit.STAGE_CONTRACTS,
        "custom_runtime_context_stage",
        audit.StageContract(
            required_fields=("source_record_id", "risk_context"),
            zero_sensitive_fields=("risk_context",),
            max_zero_rate=0.0,
        ),
    )
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "custom_runtime_context_stage",
                {
                    "source_quality_route": "source_quality_blocker_or_workorder_only",
                    "source_quality_blocker": "context_not_ready",
                    "risk_context": "0",
                    "reason": "insufficient_history",
                },
                record_id=1,
            ),
            _event(
                "custom_runtime_context_stage",
                {
                    "source_record_id": "SRC-2",
                    "risk_context": "5",
                },
                record_id=2,
            ),
        ],
    )

    report = audit.write_report("2026-06-04")
    manifest = json.loads(Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8"))

    assert manifest["stage_counts"] == {"custom_runtime_context_stage": 1}
    assert manifest["field_gap_counts"]["missing_fields:source_record_id"] == 1
    assert manifest["field_gap_counts"]["zero_fields:risk_context"] == 1
    assert manifest["exclusion_reasons"]["source_quality_blocker"] == 1
    assert manifest["exclusion_reasons"]["insufficient_history"] == 1
    assert manifest["exclusion_reasons"]["provenance_missing"] == 1
    assert manifest["producer_hint"][0]["stage"] == "custom_runtime_context_stage"


def test_observation_source_quality_raw_row_exclusion_marks_market_halt_overlap(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    market_halt_dir = tmp_path / "source_quality" / "market_halt_windows" / "windows"
    market_halt_dir.mkdir(parents=True, exist_ok=True)
    (market_halt_dir / "2026-06-08.json").write_text(
        json.dumps(
            {
                "report_type": "market_halt_windows",
                "target_date": "2026-06-08",
                "windows": [
                    {
                        "context_type": "market_halt_or_circuit_window",
                        "source": "operator_confirmed_intraday_circuit_breaker",
                        "halt_started_at": "2026-06-08T09:03:42",
                        "continuous_trading_halted_until": "2026-06-08T09:23:42",
                        "single_price_order_acceptance_until": "2026-06-08T09:33:42",
                        "normal_flow_check_after": "2026-06-08T09:35:00",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    rows = []
    base_fields = {
        "latest_strength": "0.0",
        "buy_pressure_10t": "0.00",
        "distance_from_day_high_pct": "0.000",
        "intraday_range_pct": "0.000",
        "metric_role": "risk_context",
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        "threshold_family": "strength_momentum_soft_gate_p1",
        "gate_action": "source_quality_block",
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "reason": "insufficient_history",
    }
    for idx in range(10):
        row = _event("blocked_strength_momentum", dict(base_fields), record_id=idx + 1)
        row["emitted_at"] = f"2026-06-08T09:{6 + idx:02d}:00"
        row["emitted_date"] = "2026-06-08"
        rows.append(row)
    good_row = _event(
        "blocked_strength_momentum",
        {**base_fields, "intraday_range_pct": "5.000"},
        record_id=99,
    )
    good_row["emitted_at"] = "2026-06-08T09:40:00"
    good_row["emitted_date"] = "2026-06-08"
    rows.append(good_row)
    _write_events(tmp_path, "2026-06-08", rows)

    report = audit.write_report("2026-06-08")
    manifest = json.loads(Path(report["raw_row_exclusion"]["manifest_path"]).read_text(encoding="utf-8"))

    assert manifest["market_halt_or_circuit_window_overlap"] is True
    context = manifest["market_halt_or_circuit_context"]
    assert context["classification"] == "market_halt_or_circuit_window_overlap"
    assert context["overlap_excluded_row_count"] == 10
    assert context["after_normal_flow_excluded_row_count"] == 0
    assert report["raw_row_exclusion"]["market_halt_or_circuit_window_overlap"] is True


def test_observation_source_quality_does_not_exclude_rows_when_contract_passes_tolerance(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    monkeypatch.setitem(
        audit.STAGE_CONTRACTS,
        "tolerated_contract_stage",
        audit.StageContract(required_fields=("source_id",), max_missing_rate=0.5),
    )
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event("tolerated_contract_stage", {"source_id": "SRC-1"}, record_id=1),
            _event("tolerated_contract_stage", {}, record_id=2),
        ],
    )

    report = audit.write_report("2026-06-04")
    raw_path = tmp_path / "pipeline_events" / "pipeline_events_2026-06-04.jsonl"
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]

    assert report["stage_contracts"]["tolerated_contract_stage"]["status"] == "pass"
    assert report["summary"]["raw_row_exclusion_applied"] is False
    assert report["summary"]["hard_blocking_excluded_row_count"] == 0
    assert len(rows) == 2


def test_observation_source_quality_audit_accepts_swing_loss_reentry_fallback_source(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fallback_id = "swing_dry_run:2026-06-04:KOSPI_ML:004710:exit:1780556300"
    _write_events(
        tmp_path,
        "2026-06-04",
        [
            _event(
                "swing_same_symbol_loss_reentry_cooldown",
                {
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "source_book": "swing_dry_run",
                    "source_probe_id": fallback_id,
                    "source_record_id": fallback_id,
                    "source_stage": "exit",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-06-04")

    contract = report["stage_contracts"]["swing_same_symbol_loss_reentry_cooldown"]
    assert contract["status"] == "pass"
    assert report["summary"]["tuning_input_allowed"] is True


def test_observation_source_quality_audit_routes_entry_arm_and_loss_diagnostics_by_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(60):
        rows.extend(
            [
                _event(
                    "entry_armed",
                    {
                        "ai_score": "82.0",
                        "ratio": "0.1000",
                        "target_buy_price": 12000,
                        "current_vpw": "110.0",
                        "reason": "dynamic_entry",
                        "ttl_sec": 90,
                    },
                    record_id=idx * 4 + 1,
                ),
                _event(
                    "entry_armed_expired_after_wait",
                    {
                        "waited_sec": "91.0",
                        "resume_count": 1,
                        "reason": "dynamic_entry",
                    },
                    record_id=idx * 4 + 2,
                ),
                _event(
                    "loss_fallback_probe",
                    {
                        "gate_allowed": False,
                        "gate_reason": "fallback_disabled",
                        "fallback_candidate": True,
                        "fallback_reason": "loss_recovery",
                        "profit_rate": "-0.2",
                        "peak_profit": "0.1",
                    },
                    record_id=idx * 4 + 3,
                ),
                _event(
                    "soft_stop_whipsaw_confirmation",
                    {
                        "threshold_family": "soft_stop_whipsaw_confirmation",
                        "threshold_version": "v1",
                        "threshold_calibration_state": "selected",
                        "profit_rate": "-0.3",
                        "flow_state": "recovery",
                        "exit_rule_candidate": "soft_stop",
                    },
                    record_id=idx * 4 + 4,
                ),
            ]
        )
    _write_events(tmp_path, "2026-05-15", rows)

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["entry_armed"]["status"] == "pass"
    assert report["stage_contracts"]["entry_armed_expired_after_wait"]["status"] == "pass"
    assert report["stage_contracts"]["loss_fallback_probe"]["status"] == "pass"
    assert report["stage_contracts"]["soft_stop_whipsaw_confirmation"]["status"] == "pass"


def test_observation_source_quality_audit_normalizes_optional_holding_context(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "loss_fallback_probe",
            {
                "gate_allowed": False,
                "gate_reason": "add_judgment_locked",
                "fallback_candidate": False,
                "fallback_reason": "-",
                "profit_rate": "-1.0",
                "peak_profit": "0.0",
            },
        ),
        _event(
            "soft_stop_whipsaw_confirmation",
            {
                "threshold_family": "soft_stop_whipsaw_confirmation",
                "threshold_version": "runtime_default",
                "threshold_calibration_state": "runtime_default",
                "profit_rate": "-1.5",
                "flow_state": "-",
                "exit_rule_candidate": "scalp_soft_stop_pct",
            },
            record_id=2,
        ),
    ]
    _write_events(tmp_path, "2026-05-15", rows)

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["stage_contracts"]["loss_fallback_probe"]["status"] == "pass"
    assert report["stage_contracts"]["soft_stop_whipsaw_confirmation"]["status"] == "pass"


def test_observation_source_quality_audit_normalizes_legacy_flow_state_label():
    normalized = audit._normalized_fields_for_contract(
        "soft_stop_whipsaw_confirmation",
        {
            "threshold_family": "soft_stop_whipsaw_confirmation",
            "threshold_version": "runtime_default",
            "threshold_calibration_state": "runtime_default",
            "profit_rate": "-1.5",
            "flow_state": "흡수",
            "exit_rule_candidate": "scalp_soft_stop_pct",
        },
    )

    assert normalized["flow_state"] == "absorption"
    assert normalized["raw_flow_state"] == "흡수"
    assert normalized["flow_state_source"] == "audit_normalized_legacy_runtime_flow_state"


def test_observation_source_quality_audit_accepts_score_vpw_prior_sentinel():
    normalized = audit._normalized_fields_for_contract(
        "swing_probe_entry_candidate",
        {
            "gatekeeper_action": "NOT_EVALUATED_SCORE_VPW_PRIOR",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
    )

    assert normalized["action_key"] == "not_evaluated_score_vpw_prior"
    assert "invalid_gatekeeper_action_label" not in normalized
    assert normalized["actual_order_submitted"] is False
    assert normalized["broker_order_forbidden"] is True
    assert normalized["runtime_effect"] is False


def test_observation_source_quality_audit_fails_unknown_flow_state_label(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "soft_stop_whipsaw_confirmation",
                {
                    "threshold_family": "soft_stop_whipsaw_confirmation",
                    "threshold_version": "runtime_default",
                    "threshold_calibration_state": "runtime_default",
                    "profit_rate": "-1.5",
                    "flow_state": "confirming",
                    "exit_rule_candidate": "scalp_soft_stop_pct",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["soft_stop_whipsaw_confirmation"]
    assert report["status"] == "fail"
    assert contract["status"] == "fail"
    assert contract["invalid_label_violations"] == {"flow_state": 1.0}
    assert report["invalid_label_findings"][0]["field"] == "flow_state"
    assert report["summary"]["tuning_input_allowed"] is False
    assert "soft_stop_whipsaw_confirmation" in report["summary"]["hard_blocking_stages"]


def test_observation_source_quality_audit_fails_unknown_gatekeeper_action_label(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "blocked_gatekeeper_reject",
                {
                    "action": "ambiguous_chase",
                    "cooldown_policy": "pullback_wait",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    contract = report["stage_contracts"]["blocked_gatekeeper_reject"]
    assert report["status"] == "fail"
    assert contract["status"] == "fail"
    assert contract["invalid_label_violations"] == {"action": 1.0}
    assert report["invalid_label_findings"][0]["field"] == "gatekeeper_action"


def test_observation_source_quality_audit_fails_unknown_labels_on_uncontracted_stage(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "holding_flow_override_review",
                {
                    "flow_state": "confirming",
                    "flow_action": "HOLD",
                },
            ),
            _event(
                "swing_probe_entry_candidate",
                {
                    "simulation_book": "swing_intraday_live_equiv_probe",
                    "simulation_owner": "SwingIntradayLiveEquivalentProbe0511",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": "in_memory_probe_only",
                    "probe_origin_stage": "blocked_gatekeeper_reject",
                    "gatekeeper_action": "None",
                    "curr_price": "1000",
                    "assumed_fill_price": "1000",
                    "score": "50",
                    "v_pw": "120",
                    "virtual_budget_override": True,
                    "budget_authority": "sim_virtual_not_real_orderable_amount",
                },
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["status"] == "fail"
    assert report["invalid_label_findings"] == [
        {
            "stage": "holding_flow_override_review",
            "field": "flow_state",
            "count": 1,
            "examples": ["confirming"],
            "routing": "source_quality_blocker",
        }
    ]


def test_observation_source_quality_audit_routes_holding_diagnostics_by_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "ai_holding_fast_reuse_band",
            {
                "metric_role": "ops_volume_diagnostic",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "telemetry_only": True,
                "action": "skip",
            },
        ),
        _event(
            "soft_stop_expert_shadow",
            {
                "metric_role": "ops_volume_diagnostic",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "shadow_only": True,
                "hierarchy": "mae_mfe_quantile|recovery_probability|partial_de_risk",
            },
        ),
        _event(
            "holding_flow_override_candidate_cleared",
            {
                "metric_role": "funnel_count",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                "source_quality_route": "source_quality_blocker_or_workorder_only",
                "reason": "exit_rule_changed",
                "previous_key": "ABC:1",
            },
        ),
    ]
    _write_events(tmp_path, "2026-05-15", [dict(row, record_id=idx) for idx, row in enumerate(rows * 55)])

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    assert report["stage_contracts"]["ai_holding_fast_reuse_band"]["status"] == "pass"
    assert report["stage_contracts"]["soft_stop_expert_shadow"]["status"] == "pass"
    assert report["stage_contracts"]["holding_flow_override_candidate_cleared"]["status"] == "pass"
    assert report["status"] == "pass"


def test_observation_source_quality_audit_routes_probe_state_persisted_by_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-15",
        [
            _event(
                "swing_probe_state_persisted",
                {
                    "simulation_book": "swing_intraday_probe",
                    "simulation_owner": "owner",
                    "reason": "probe_scale_in",
                    "active_count": 1,
                },
                record_id=idx,
            )
            for idx in range(60)
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-15")

    assert report["high_volume_no_source_fields"] == []
    persisted = report["stage_contracts"]["swing_probe_state_persisted"]
    assert persisted["status"] == "warning"
    assert "metric_role" in persisted["missing_violations"]


def test_observation_source_quality_audit_accepts_pre_ai_and_pre_submit_gate_contracts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-18",
        [
            _event(
                "blocked_liquidity",
                {
                    "metric_role": "risk_context",
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "gate_action": "risk_context_only",
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "liquidity_value": 100_000_000,
                    "min_liquidity": 500_000_000,
                },
            ),
            _event(
                "pre_submit_liquidity_guard_block",
                {
                    "metric_role": "source_quality_gate",
                    "decision_authority": "order_safety_pre_submit_only",
                    "runtime_effect": "pre_submit_block",
                    "forbidden_uses": "provider_route_change/bot_restart/runtime_threshold_apply_without_approval",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "gate_action": "pre_submit_block",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "liquidity_value": 100_000_000,
                    "min_liquidity": 500_000_000,
                },
                record_id=2,
            ),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-18")

    assert report["stage_contracts"]["blocked_liquidity"]["status"] == "pass"
    assert report["stage_contracts"]["pre_submit_liquidity_guard_block"]["status"] == "pass"


def test_observation_source_quality_audit_accepts_scalp_sim_stage_contracts(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": False,
        "sim_record_id": "SIM-1",
    }
    liquidity_guard_fields = {
        **fields,
        "decision_authority": "sim_submit_path_observation_only",
        "threshold_family": "liquidity_pre_submit_guard_p1",
        "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_liquidity_reason": "below_min_liquidity",
        "sim_liquidity_value": 100_000_000,
        "sim_min_liquidity": 500_000_000,
        "sim_parent_record_id": 1,
    }
    overbought_guard_fields = {
        **fields,
        "decision_authority": "sim_submit_path_observation_only",
        "threshold_family": "overbought_pullback_guard_p1",
        "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
        "sim_pre_submit_overbought_reason": "overbought_ok",
        "sim_overbought_risk_state": "pullback_observed",
        "sim_parent_record_id": 1,
    }
    overbought_block_fields = {
        **overbought_guard_fields,
        "sim_pre_submit_overbought_guard_action": "WOULD_BLOCK",
        "sim_pre_submit_overbought_reason": "pullback_or_rebreak_not_confirmed",
        "sim_overbought_risk_state": "pullback_required",
    }
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event("scalp_sim_entry_armed", fields, record_id=1),
            _event("scalp_sim_pre_submit_liquidity_guard_would_block", liquidity_guard_fields, record_id=11),
            _event(
                "scalp_sim_pre_submit_liquidity_guard_would_pass",
                {
                    **liquidity_guard_fields,
                    "sim_pre_submit_liquidity_guard_action": "WOULD_PASS",
                    "sim_pre_submit_liquidity_reason": "liquidity_ok",
                    "sim_liquidity_value": 800_000_000,
                },
                record_id=12,
            ),
            _event(
                "scalp_sim_pre_submit_liquidity_guard_unknown",
                {
                    **liquidity_guard_fields,
                    "sim_pre_submit_liquidity_guard_action": "WOULD_UNKNOWN",
                    "sim_pre_submit_liquidity_reason": "liquidity_unknown",
                    "sim_liquidity_value": "UNKNOWN",
                },
                record_id=15,
            ),
            _event("scalp_sim_pre_submit_overbought_guard_would_block", overbought_block_fields, record_id=13),
            _event("scalp_sim_pre_submit_overbought_guard_would_pass", overbought_guard_fields, record_id=14),
            _event("scalp_sim_buy_order_virtual_pending", fields, record_id=2),
            _event("scalp_sim_buy_order_assumed_filled", fields, record_id=3),
            _event("scalp_sim_entry_ai_price_skip_order", fields, record_id=4),
            _event("scalp_sim_holding_started", fields, record_id=5),
            _event("scalp_sim_sell_order_assumed_filled", fields, record_id=6),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")

    for stage in (
        "scalp_sim_entry_armed",
        "scalp_sim_pre_submit_liquidity_guard_would_block",
        "scalp_sim_pre_submit_liquidity_guard_would_pass",
        "scalp_sim_pre_submit_liquidity_guard_unknown",
        "scalp_sim_pre_submit_overbought_guard_would_block",
        "scalp_sim_pre_submit_overbought_guard_would_pass",
        "scalp_sim_buy_order_virtual_pending",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_entry_ai_price_skip_order",
        "scalp_sim_holding_started",
        "scalp_sim_sell_order_assumed_filled",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"


def test_observation_source_quality_audit_fails_mismatched_sim_submit_guard_stage_action(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event(
                "scalp_sim_pre_submit_liquidity_guard_would_pass",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "simulated_order": True,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_submit_path_observation_only",
                    "runtime_effect": False,
                    "sim_record_id": "SIM-1",
                    "threshold_family": "liquidity_pre_submit_guard_p1",
                    "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
                    "sim_pre_submit_liquidity_reason": "below_min_liquidity",
                    "sim_liquidity_value": 100_000_000,
                    "sim_min_liquidity": 500_000_000,
                    "sim_parent_record_id": 1,
                },
                record_id=1,
            )
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")
    contract = report["stage_contracts"]["scalp_sim_pre_submit_liquidity_guard_would_pass"]

    assert contract["status"] == "fail"
    assert contract["invalid_label_counts"]["sim_submit_guard_action_contract"] == 1


def test_observation_source_quality_audit_contracts_sim_budget_and_risk_context(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    budget_fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": "sim_ai_live_call_only",
        "sim_record_id": "SIM-1",
        "entry_adm_candidate_id": "ADM-1",
    }
    risk_fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": "sim_panic_action_deduped",
        "threshold_family": "panic_lifecycle_actuator",
        "source_stage": "scalp_sim_holding_started",
        "sim_record_id": "SIM-1",
    }
    _write_events(
        tmp_path,
        "2026-05-20",
        [
            _event("scalp_sim_ai_holding_live_call", budget_fields, record_id=1),
            _event("scalp_sim_ai_holding_deferred", budget_fields, record_id=2),
            _event("sim_ai_budget_exhausted", budget_fields, record_id=3),
            _event("sim_ai_critical_bypass", budget_fields, record_id=4),
            _event("scalp_sim_panic_action_deduped", risk_fields, record_id=5),
            _event("scalp_sim_panic_scale_in_blocked", risk_fields, record_id=6),
            _event("scalp_sim_euphoria_context_noop", risk_fields, record_id=7),
        ],
    )

    report = audit.build_observation_source_quality_audit("2026-05-20")

    for stage in (
        "scalp_sim_ai_holding_live_call",
        "scalp_sim_ai_holding_deferred",
        "sim_ai_budget_exhausted",
        "sim_ai_critical_bypass",
        "scalp_sim_panic_action_deduped",
        "scalp_sim_panic_scale_in_blocked",
        "scalp_sim_euphoria_context_noop",
    ):
        assert report["stage_contracts"][stage]["status"] == "pass"


def test_observation_source_quality_audit_writes_json_and_markdown(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(tmp_path, "2026-05-15", [_event("swing_probe_entry_candidate", {
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "simulated_order": True,
        "evidence_quality": "counterfactual_after_gap",
        "source_record_id": "1",
        "virtual_budget_override": True,
        "budget_authority": "sim_virtual_not_real_orderable_amount",
    })])

    report = audit.write_report("2026-05-15")
    json_path, md_path = audit.report_paths("2026-05-15")

    assert report["stage_contracts"]["swing_probe_entry_candidate"]["status"] == "pass"
    assert json_path.exists()
    assert md_path.exists()


def _write_threshold_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    event_dir = tmp_path / "threshold_cycle"
    event_dir.mkdir(parents=True)
    with (event_dir / f"threshold_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_observation_source_quality_backfill_quarantines_only_derived_bucket_interpretation(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-18",
        [
            _event(
                "scalp_sim_buy_order_assumed_filled",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                    "profit_rate": "0.4",
                },
            )
        ],
    )
    _write_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_adm_score_bucket": "score_unknown",
                    "entry_adm_stale_bucket": "stale_unknown",
                    "lifecycle_matrix_entry_bucket": "entry_unknown",
                },
            ),
            _event(
                "scalp_sim_pre_submit_overbought_guard_would_pass",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "sim_pre_submit_overbought_reason": "overbought_unknown",
                    "sim_overbought_context_source": "unknown",
                    "sim_overbought_source_quality": "unknown",
                },
                record_id=2,
            ),
        ],
    )
    _write_threshold_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_sim_buy_order_assumed_filled",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_observation_only",
                },
                record_id=3,
            )
        ],
    )
    stale_report = (
        tmp_path
        / "report"
        / "scalp_entry_action_decision_matrix"
        / "scalp_entry_action_decision_matrix_2026-05-19.json"
    )
    stale_report.parent.mkdir(parents=True)
    stale_report.write_text("{}", encoding="utf-8")

    report = audit.build_observation_source_quality_backfill_audit(
        "2026-05-19",
        start_date="2026-05-18",
    )

    by_date = {item["date"]: item for item in report["date_impacts"]}
    assert by_date["2026-05-18"]["raw_sim_preserved"] is True
    assert by_date["2026-05-18"]["bucket_interpretation_quarantined"] is False
    assert by_date["2026-05-19"]["raw_sim_preserved"] is True
    assert by_date["2026-05-19"]["bucket_interpretation_quarantined"] is True
    assert set(by_date["2026-05-19"]["quarantine_scope"]) == {
        "entry_adm_bucket_dimensions",
        "ldm_bucket_attribution",
        "sim_overbought_context_provenance",
    }
    assert by_date["2026-05-19"]["recommended_action"] == "regenerate_derived_reports_with_source_quality_gate"
    assert report["summary"]["first_entry_adm_unknown_date"] == "2026-05-19"
    assert report["summary"]["first_ldm_unknown_date"] == "2026-05-19"
    assert report["summary"]["first_sim_overbought_unknown_date"] == "2026-05-19"
    assert report["summary"]["operator_action_required"] is False
    assert report["policy"]["runtime_effect"] is False
    assert by_date["2026-05-19"]["stale_derived_reports"][0]["report_type"] == "scalp_entry_action_decision_matrix"


def test_observation_source_quality_backfill_writes_json_and_markdown(monkeypatch, tmp_path):
    monkeypatch.setattr(audit, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        "2026-05-19",
        [
            _event(
                "scalp_entry_action_decision_snapshot",
                {
                    "simulation_book": "scalp_ai_buy_all",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "entry_adm_score_bucket": "score_unknown",
                },
            )
        ],
    )

    report = audit.write_backfill_report("2026-05-19", start_date="2026-05-19")
    json_path, md_path = audit.backfill_report_paths("2026-05-19")

    assert report["status"] == "warning"
    assert json_path.exists()
    assert md_path.exists()
    assert "Raw SIM rows and fill/outcome labels are preserved" in md_path.read_text(encoding="utf-8")
