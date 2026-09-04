# Conversion Lane - 2026-09-04

## Decision
- conversion candidates: `18`
- terminal source-only exclusions: `1`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `6`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`495` zero_count=`495` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`0` counts=`{}`
- active seed candidate validation: total=`487` eligible=`0` not_match_eligible=`487` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 487}` new_entry=`5` followup=`482` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`487` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`482`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_disabled': 442}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`18` swing=`0` unscoped=`0`
- bounded real canary requestable: `0`
- top blocker ranked: `submit_drought`; top blocker by count: `lifecycle_stage_underproduction`
- top LDM bucket blocker: `env_mapping`
- submit funnel blocker count: `3` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `submit_drought:UPSTREAM_GATE`: submit_drought -> join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned
- #2 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #3 `submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION`: submit_drought -> join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe
- #4 `entry:stage_policy:entry_weighted_adm_v1`: env_mapping -> complete_parent_flow
- #5 `entry:liquidity_bucket:liquidity_high`: sample_floor -> complete_parent_flow
- #6 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #7 `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: bridge_contract -> bridge_contract
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #9 `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: bridge_contract -> bridge_contract
- #10 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #13 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #16 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #18 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale`: sample_floor -> sample_floor
- #19 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale`: sample_floor -> sample_floor
- #20 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`: sample_floor -> sample_floor

## Real Conversion Queue
- none
