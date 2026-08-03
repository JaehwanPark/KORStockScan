# Conversion Lane - 2026-08-03

## Decision
- conversion candidates: `40`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `11`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`391` zero_count=`391` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`47` counts=`{'canonical': 124, 'new_axis_pending_taxonomy': 47, 'unknown': 12}`
- active seed candidate validation: total=`391` eligible=`0` not_match_eligible=`391` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 391}` new_entry=`3` followup=`388` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`391` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`388`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 42}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`39` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `sample_floor`; top blocker by count: `source_quality`
- top LDM bucket blocker: `sample_floor`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `entry:overbought_bucket:overbought_ok`: sample_floor -> complete_parent_flow
- #2 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #3 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #4 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #5 `submit_drought:SIM_REAL_AUTHORITY`: submit_drought -> close_submit_drought_sim_real_authority
- #6 `submit_drought:SOURCE_TAXONOMY_LEAKAGE`: submit_drought -> close_submit_drought_source_taxonomy_leakage
- #7 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #8 `entry:source_stage:wait6579_ev_cohort`: env_mapping -> complete_parent_flow
- #9 `entry:stage_policy:entry_weighted_adm_v1`: env_mapping -> complete_parent_flow
- #10 `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: env_mapping -> complete_parent_flow
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: source_quality -> source_quality
- #12 `entry:chosen_action:wait_requote`: sample_floor -> complete_parent_flow
- #13 `entry:liquidity_bucket:liquidity_high`: sample_floor -> complete_parent_flow
- #14 `entry:overbought_bucket:overbought_watch`: sample_floor -> complete_parent_flow
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: source_quality -> source_quality
- #16 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_`: env_mapping -> sample_floor
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`: source_quality -> source_quality
- #18 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: source_quality -> source_quality
- #19 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: source_quality -> source_quality
- #20 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st`: source_quality -> source_quality

## Real Conversion Queue
- none
