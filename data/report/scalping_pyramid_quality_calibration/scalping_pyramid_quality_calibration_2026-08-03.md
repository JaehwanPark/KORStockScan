# 2026-08-03 Scalping Pyramid Quality Calibration

- generated_at: 2026-08-03T20:25:17+09:00
- family: scalping_pyramid_quality_gate
- stage: scale_in
- calibration_state: hold
- calibration_reason: mixed_cluster_hold
- allowed_runtime_apply: false
- source_quality_excluded_dates: [{"artifact": null, "blocked_reason": "source_quality_preflight_missing", "hard_blocking_contract_gap_count": 0, "load_error": "FileNotFoundError", "source_date": "2026-06-13", "source_quality_gate": "blocked_contract_gap", "status": "missing"}, {"artifact": null, "blocked_reason": "source_quality_preflight_missing", "hard_blocking_contract_gap_count": 0, "load_error": "FileNotFoundError", "source_date": "2026-06-14", "source_quality_gate": "blocked_contract_gap", "status": "missing"}, {"artifact": "/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-19.json", "blocked_reason": "blocked_contract_gap", "hard_blocking_contract_gap_count": 3, "load_error": null, "source_date": "2026-06-19", "source_quality_gate": "blocked_contract_gap", "status": "fail"}]
- runtime_effect: false
- decision_authority: postclose_calibration_candidate_preopen_only
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Metrics

- calibration_source_scope: one_share_event_opportunity
- one_share_event_source_present: True
- one_share_closed_pyramid_row_count: 50
- sample_count: 50
- recovered_or_extended_rate: 0.16
- reversal_or_flat_rate: 0.26
- correctly_blocked_rate: 0.58
- one_share_pyramid_avg_opportunity_cost_pct: 0.61
- profit_threshold_grid_status: hold
- profit_threshold_grid_reason: grid_ev_delta_lt_0_20
- profit_threshold_grid_selected_min_profit_pct: 0.8
- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: 0.00
- source_quality_pass: True
- provenance_present: True
- post_probe_real_outcome_state: hold_sample
- post_probe_real_outcome_closed_count: 14
- post_probe_confirmation_ready_count: 1
- post_probe_confirmation_ready_winner_count: 1
- post_probe_confirmation_ready_loss_or_flat_count: 0
- post_probe_confirmation_ready_notional_weighted_ev_pct: 0.2700
