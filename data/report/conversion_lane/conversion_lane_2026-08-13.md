# Conversion Lane - 2026-08-13

## Decision
- conversion candidates: `15`
- terminal source-only exclusions: `2`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `3`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `2`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `2`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`189` zero_count=`0` positive_count=`189` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`0` counts=`{'unknown': 2}`
- active seed candidate validation: total=`134` eligible=`134` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`15` followup=`119` matched=`17` matched_true_without_seed_id=`0` unmatched=`117` new_entry_unmatched=`13` followup_unmatched=`104` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`117` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`104`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`15` swing=`0` unscoped=`0`
- bounded real canary requestable: `0`
- top blocker ranked: `submit_drought`; top blocker by count: `lifecycle_stage_underproduction`
- top LDM bucket blocker: `lifecycle_stage_underproduction`
- submit funnel blocker count: `4` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `submit_drought:ENTRY_AI_AUTHORITY_REVALIDATION`: submit_drought -> join exact AI authority reason, executable BBO, and target/adverse first-hit outcomes before proposing a bounded one-share probe
- #2 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #3 `submit_drought:UPSTREAM_GATE`: submit_drought -> join upstream action/reason cohorts to executable BBO and first-hit outcomes; AI semantic tuning remains separately owned
- #4 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> treat pre-AI budget events as expected no-parent observations; repair only missing lineage contracts or stale/untrusted post-AI parents, and keep causal EV attribution limited to exact joins
- #5 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #6 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #7 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`: env_mapping -> sample_floor
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`: env_mapping -> sample_floor
- #9 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #10 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #13 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_ok_or_u`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #16 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_entry_ai_price_skip_order_stale_st`: sample_floor -> sample_floor

## Real Conversion Queue
- none
