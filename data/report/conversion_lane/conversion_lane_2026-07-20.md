# Conversion Lane - 2026-07-20

## Decision
- conversion candidates: `708`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `134`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `113`
- positive EV sample-floor related total: `113`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`source_report_window` window_counts=`{'source_report_window': 113}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`91` zero_count=`91` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`41` counts=`{'canonical': 112, 'new_axis_pending_taxonomy': 41, 'unknown': 13}`
- active seed candidate validation: total=`91` eligible=`0` not_match_eligible=`91` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 91}` new_entry=`7` followup=`84` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`91` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`84`
- panic scale-in no-match: events=`35` unique_sim_records=`5` missing_sim_record_id=`0` repeated_followup=`30` status_counts=`{'no_match': 35}` source_stage_counts=`{'blocked_ai_score': 30, 'first_ai_wait': 5}`
- conversion candidate strategy scope: scalp=`26` swing=`681` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`LATENCY_DROUGHT` matches=`['LATENCY_DROUGHT']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_5d_close_equal_notional_fixed_5d`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_mae_stop_time_stop_10d_close_risk_c_e93e893cd115`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #5 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_risk_capped_fixed_10d`: sample_floor -> sample_floor
- #6 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #7 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop_confidence_we_04dd3ed862f2`: sample_floor -> sample_floor
- #8 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #9 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_120eabab1d30`: sample_floor -> sample_floor
- #10 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32107919b18b`: sample_floor -> sample_floor
- #11 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_44479baded61`: sample_floor -> sample_floor
- #12 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_83c756e9a60a`: sample_floor -> sample_floor
- #13 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_b3df3092fcc0`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_manufacture_fa09ac98bf0d`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_trust_and_c_dfb40d77d0ee`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_125fc169ebdb`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_28e075b7575c`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_3dfc40c37c2c`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_a625e7e8ff55`: sample_floor -> sample_floor

## Real Conversion Queue
- none
