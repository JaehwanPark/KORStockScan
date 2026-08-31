# 2026-08-31 Scalping Pyramid Quality Calibration

- generated_at: 2026-08-31T20:27:09+09:00
- family: scalping_pyramid_quality_gate
- stage: scale_in
- calibration_state: hold
- calibration_reason: normal_winner_expansion_non_positive_ev_hold:grid_loosen_profit_threshold_direct
- allowed_runtime_apply: false
- source_quality_excluded_dates: [{"artifact": null, "blocked_reason": "source_quality_preflight_missing", "hard_blocking_contract_gap_count": 0, "load_error": "FileNotFoundError", "source_date": "2026-06-13", "source_quality_gate": "blocked_contract_gap", "status": "missing"}, {"artifact": null, "blocked_reason": "source_quality_preflight_missing", "hard_blocking_contract_gap_count": 0, "load_error": "FileNotFoundError", "source_date": "2026-06-14", "source_quality_gate": "blocked_contract_gap", "status": "missing"}, {"artifact": "/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-19.json", "blocked_reason": "blocked_contract_gap", "hard_blocking_contract_gap_count": 3, "load_error": null, "source_date": "2026-06-19", "source_quality_gate": "blocked_contract_gap", "status": "fail"}, {"artifact": null, "blocked_reason": "source_quality_preflight_missing", "hard_blocking_contract_gap_count": 0, "load_error": "FileNotFoundError", "source_date": "2026-08-17", "source_quality_gate": "blocked_contract_gap", "status": "missing"}]
- runtime_effect: false
- decision_authority: postclose_calibration_candidate_preopen_only
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Metrics

- calibration_source_scope: one_share_event_opportunity
- one_share_event_source_present: True
- one_share_closed_pyramid_row_count: 80
- sample_count: 80
- recovered_or_extended_rate: 0.23
- reversal_or_flat_rate: 0.17
- correctly_blocked_rate: 0.60
- one_share_pyramid_avg_opportunity_cost_pct: 0.57
- profit_threshold_grid_status: adjust_down
- profit_threshold_grid_reason: grid_loosen_profit_threshold_direct
- profit_threshold_grid_selected_min_profit_pct: 1.0
- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: 0.03
- source_quality_pass: True
- source_quality_excluded_row_count: 209
- provenance_present: True
- normal_winner_expansion_state: non_positive_ev_hold
- normal_winner_expansion_sample_count: 31
- normal_winner_expansion_ev_eligible_sample_count: 31
- normal_winner_expansion_notional_weighted_ev_pct: -0.3007
- normal_winner_expansion_loosen_veto_applied: True
- post_probe_real_outcome_state: hold_sample
- post_probe_real_outcome_closed_count: 44
- post_probe_confirmation_ready_count: 1
- post_probe_confirmation_ready_winner_count: 1
- post_probe_confirmation_ready_loss_or_flat_count: 0
- post_probe_confirmation_ready_notional_weighted_ev_pct: 0.2700
- winner_recovery_bounded_canary_state: bounded_one_share_canary_evidence_ready
- winner_recovery_bounded_canary_exact_blocker_sample_count: 13
- winner_recovery_real_execution_state: observe_one_share_canary
- winner_recovery_real_source_quality_valid_closed_count: 0
- winner_recovery_real_source_quality_adjusted_ev_pct: 0.0000
- winner_recovery_recommended_next_qty_stage: retain_one_share_winner_recovery_canary
