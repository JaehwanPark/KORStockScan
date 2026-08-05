# Conversion Lane - 2026-08-05

## Decision
- conversion candidates: `41`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `14`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `0`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `0`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`204` zero_count=`204` positive_count=`0` id_without_count=`0` zero_count_effect_excluded=`True`
- active sim taxonomy contracts: pending=`47` counts=`{'canonical': 131, 'new_axis_pending_taxonomy': 47, 'unknown': 12}`
- active seed candidate validation: total=`202` eligible=`0` not_match_eligible=`202` not_match_eligible_reasons=`{'policy_active_seed_count_zero_effect_excluded': 202}` new_entry=`4` followup=`198` matched=`0` matched_true_without_seed_id=`0` unmatched=`0` new_entry_unmatched=`0` followup_unmatched=`0` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`72` inferred_stages=`{'scalp_sim_buy_order_assumed_filled': 1, 'scalp_sim_buy_order_virtual_pending': 1, 'scalp_sim_entry_ai_price_applied': 1, 'scalp_sim_entry_ai_price_skip_order': 26, 'scalp_sim_entry_armed': 1, 'scalp_sim_holding_started': 1, 'scalp_sim_panic_bottoming_entry_allowed': 1, 'scalp_sim_panic_level1_entry_observed': 19, 'scalp_sim_panic_scale_in_blocked': 18, 'scalp_sim_pre_submit_liquidity_guard_would_pass': 1, 'scalp_sim_pre_submit_overbought_guard_would_pass': 1, 'scalp_sim_sell_order_assumed_filled': 1}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`202` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`198`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'policy_missing': 76}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`40` swing=`0` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `key_lineage`; top blocker by count: `lifecycle_stage_underproduction`
- top LDM bucket blocker: `key_lineage`
- submit funnel blocker count: `4` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`SUBMIT_DROUGHT_CRITICAL` matches=`['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL']` submit_drought_source_state=`submit_drought_critical`

## Top Conversion Blockers
- #1 `active_seed_7cf1c198fc1e5246`: key_lineage -> key_lineage_preopen_missing
- #2 `active_seed_94696687ea1be0c3`: key_lineage -> key_lineage_preopen_missing
- #3 `active_seed_b99a2dea7aac2a83`: key_lineage -> key_lineage_preopen_missing
- #4 `entry:strength_bucket:weak_strength_momentum`: sample_floor -> complete_parent_flow
- #5 `entry:source_stage:wait6579_ev_cohort`: env_mapping -> complete_parent_flow
- #6 `entry:stale_bucket:fresh_or_unflagged`: env_mapping -> complete_parent_flow
- #7 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #8 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #9 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit_quote_freshness
- #10 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #11 `entry:score_band:score_63_65`: env_mapping -> complete_parent_flow
- #12 `entry:stage_policy:entry_weighted_adm_v1`: env_mapping -> complete_parent_flow
- #13 `entry:overbought_bucket:overbought_watch`: sample_floor -> complete_parent_flow
- #14 `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: env_mapping -> complete_parent_flow
- #15 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #16 `entry:chosen_action:wait_requote`: sample_floor -> complete_parent_flow
- #17 `entry:liquidity_bucket:liquidity_high`: sample_floor -> complete_parent_flow
- #18 `entry:strength_bucket:neutral_strength_momentum`: sample_floor -> complete_parent_flow
- #19 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #20 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction

## Real Conversion Queue
- none
