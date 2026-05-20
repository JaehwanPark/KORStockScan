import json

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
    event_dir.mkdir(parents=True)
    with (event_dir / f"pipeline_events_{target_date}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


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
                        "flow_state": "confirming",
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
