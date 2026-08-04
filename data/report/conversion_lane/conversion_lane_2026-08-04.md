# Conversion Lane - 2026-08-04

## Decision
- conversion candidates: `33`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `1`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`1172` zero_count=`1172` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`47` counts=`{'canonical': 130, 'new_axis_pending_taxonomy': 47, 'unknown': 12}`
- active seed candidate validation: total=`1166` eligible=`0` not_match_eligible=`1166` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 1166}` new_entry=`9` followup=`1157` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`1166` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`1157`
- panic scale-in no-match: events=`935` unique_sim_records=`9` missing_sim_record_id=`0` repeated_followup=`926` status_counts=`{'no_match': 935}` source_stage_counts=`{'blocked_ai_score': 935}`
- conversion candidate strategy scope: scalp=`32` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `submit_drought`; top blocker by count: `source_quality`
- top LDM bucket blocker: `source_quality`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #2 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #3 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #4 `submit_drought:SIM_REAL_AUTHORITY`: submit_drought -> close_submit_drought_sim_real_authority
- #5 `submit_drought:SOURCE_TAXONOMY_LEAKAGE`: submit_drought -> close_submit_drought_source_taxonomy_leakage
- #6 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #7 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`: source_quality -> source_quality
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi`: source_quality -> source_quality
- #9 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`: source_quality -> source_quality
- #10 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: source_quality -> source_quality
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`: source_quality -> source_quality
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: source_quality -> source_quality
- #13 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal`: source_quality -> source_quality
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale`: source_quality -> source_quality
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st`: source_quality -> source_quality
- #16 `entry_wait6579_score66_69_recovery_gate_v1:2026-08-04`: bridge_contract -> bridge_contract
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal`: source_quality -> source_quality
- #18 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai_confirmed_stale_fresh_liquidity_liquidi`: source_quality -> source_quality
- #19 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq`: source_quality -> source_quality
- #20 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale`: source_quality -> source_quality

## Real Conversion Queue
- none
