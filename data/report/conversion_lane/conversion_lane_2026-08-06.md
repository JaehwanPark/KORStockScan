# Conversion Lane - 2026-08-06

## Decision
- conversion candidates: `18`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `1`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`140` zero_count=`0` positive_count=`140` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`1` counts=`{'canonical': 10, 'new_axis_pending_taxonomy': 1, 'unknown': 2}`
- active seed candidate validation: total=`140` eligible=`140` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`2` followup=`138` matched=`107` matched_true_without_seed_id=`0` unmatched=`33` new_entry_unmatched=`0` followup_unmatched=`33` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`33` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`33`
- panic scale-in no-match: events=`68` unique_sim_records=`2` missing_sim_record_id=`0` repeated_followup=`66` status_counts=`{'no_match': 68}` source_stage_counts=`{'blocked_ai_score': 68}`
- conversion candidate strategy scope: scalp=`17` swing=`0` unscoped=`1`
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
- #5 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #6 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #7 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #9 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #10 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #13 `entry_wait6579_score66_69_recovery_gate_v1:2026-08-06`: bridge_contract -> bridge_contract
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #16 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #18 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai_confirmed_stale_fresh_liquidity_liquidi`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #19 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #20 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction

## Real Conversion Queue
- none
