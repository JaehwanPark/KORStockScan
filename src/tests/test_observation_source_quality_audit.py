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
