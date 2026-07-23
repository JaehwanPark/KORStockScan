# Conversion Lane - 2026-07-23

## Decision
- conversion candidates: `695`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `128`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `80`
- positive EV sample-floor related total: `80`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`source_report_window` window_counts=`{'source_report_window': 80}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`194` zero_count=`194` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`45` counts=`{'canonical': 116, 'new_axis_pending_taxonomy': 45, 'unknown': 13}`
- active seed candidate validation: total=`194` eligible=`0` not_match_eligible=`194` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 194}` new_entry=`12` followup=`182` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`194` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`182`
- panic scale-in no-match: events=`99` unique_sim_records=`8` missing_sim_record_id=`0` repeated_followup=`91` status_counts=`{'no_match': 99}` source_stage_counts=`{'blocked_ai_score': 21, 'first_ai_wait': 78}`
- conversion candidate strategy scope: scalp=`23` swing=`671` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`UPSTREAM_AI_THRESHOLD` matches=`['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #2 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_mae_stop_time_stop_10d_close_risk_c_e93e893cd115`: sample_floor -> sample_floor
- #3 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop_confidence_9fe639819399`: sample_floor -> sample_floor
- #4 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_equal_notional_fixed_10d`: sample_floor -> sample_floor
- #5 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_fixed_10d_close_volatility_adjusted_fixed_10d`: sample_floor -> sample_floor
- #6 `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_fixed_5d_close_risk_capped_fixed_5d`: sample_floor -> sample_floor
- #7 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_32b59151de7b`: sample_floor -> sample_floor
- #8 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_44479baded61`: sample_floor -> sample_floor
- #9 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_heavy_const_dc555624f7ff`: sample_floor -> sample_floor
- #10 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_real_estate_e5a8439ce3f0`: sample_floor -> sample_floor
- #11 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_sea_and_coa_a639078f42a0`: sample_floor -> sample_floor
- #12 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_next_open_entry_equal_notional_fixed_10d_wholesale_o_a64b7a7411b7`: sample_floor -> sample_floor
- #13 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_4cdc337daf57`: sample_floor -> sample_floor
- #14 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_a625e7e8ff55`: sample_floor -> sample_floor
- #15 `swing_bucket_selection_discovery_arm_attribution_bottom_rebound_signal_close_retest_limit_entry_risk_capped_fixed_10_fb21b59a3c76`: sample_floor -> sample_floor
- #16 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_f95ca498b403`: sample_floor -> sample_floor
- #17 `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_risk_capped_mae_stop_time_stop_manufacture_o_044b6c899b11`: sample_floor -> sample_floor
- #18 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_basic_iron_a_eeee0d502816`: sample_floor -> sample_floor
- #19 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_manufacture_of_semiconductor_반도체_생산_main`: sample_floor -> sample_floor
- #20 `swing_bucket_selection_discovery_arm_attribution_next_open_entry_equal_notional_fixed_5d_other_financial_intermediat_550a25892d04`: sample_floor -> sample_floor

## Real Conversion Queue
- none
