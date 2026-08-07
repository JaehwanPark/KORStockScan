# Conversion Lane - 2026-08-07

## Decision
- conversion candidates: `14`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `1`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`207` zero_count=`0` positive_count=`207` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`2` counts=`{'canonical': 10, 'new_axis_pending_taxonomy': 2}`
- active seed candidate validation: total=`170` eligible=`170` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`1` followup=`169` matched=`2` matched_true_without_seed_id=`0` unmatched=`168` new_entry_unmatched=`1` followup_unmatched=`167` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`168` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`167`
- panic scale-in no-match: events=`145` unique_sim_records=`1` missing_sim_record_id=`0` repeated_followup=`144` status_counts=`{'no_match': 145}` source_stage_counts=`{'blocked_ai_score': 145}`
- conversion candidate strategy scope: scalp=`13` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `submit_drought`; top blocker by count: `lifecycle_stage_underproduction`
- top LDM bucket blocker: `lifecycle_stage_underproduction`
- submit funnel blocker count: `4` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #2 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #3 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #4 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #5 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #6 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #7 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #9 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #10 `entry_wait6579_score66_69_recovery_gate_v1:2026-08-07`: bridge_contract -> bridge_contract
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #13 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_bottoming_entry_allowed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_entry_ai_price_skip_order_stale_st`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #16 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f`: sample_floor -> sample_floor
- #18 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`: sample_floor -> sample_floor

## Real Conversion Queue
- none
