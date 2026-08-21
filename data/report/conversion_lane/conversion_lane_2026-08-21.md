# Conversion Lane - 2026-08-21

## Decision
- conversion candidates: `16`
- terminal source-only exclusions: `2`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `2`
- positive EV previous-policy natural match 0: `0`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `1`
- positive EV sample-floor unknown floor: `0`
- positive EV sample-floor related total: `1`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1}` basis=`candidate_sample_vs_required_sample`
- active sim policy windows: events=`162` zero_count=`0` positive_count=`162` id_without_count=`0` zero_count_effect_excluded=`False`
- active sim taxonomy contracts: pending=`2` counts=`{'canonical': 28, 'new_axis_pending_taxonomy': 2}`
- active seed candidate validation: total=`90` eligible=`90` not_match_eligible=`0` not_match_eligible_reasons=`{}` new_entry=`6` followup=`84` matched=`64` matched_true_without_seed_id=`0` unmatched=`26` new_entry_unmatched=`3` followup_unmatched=`23` eligible_without_seed_id=`0` without_seed_reasons=`{}` without_seed_details=`{}` inferred_parent_seed_id=`0` inferred_stages=`{}` ambiguous_prefix=`0` missing_parent_stages=`{}` raw_without_seed_id=`26` eligible_followup_without_seed_id=`0` raw_followup_without_seed_id=`23`
- panic scale-in no-match: events=`0` unique_sim_records=`0` missing_sim_record_id=`0` repeated_followup=`0` status_counts=`{'matched': 19}` source_stage_counts=`{}`
- conversion candidate strategy scope: scalp=`16` swing=`0` unscoped=`0`
- bounded real canary requestable: `0`
- top blocker ranked: `lifecycle_stage_underproduction`; top blocker by count: `lifecycle_stage_underproduction`
- top LDM bucket blocker: `lifecycle_stage_underproduction`
- submit funnel blocker count: `0` (submit_drought_is_ldm_bucket_blocker=`False`)
- buy funnel source: present=`True` primary=`UPSTREAM_AI_THRESHOLD` matches=`['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD']` submit_drought_source_state=`not_submit_drought_critical`

## Top Conversion Blockers
- #1 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #2 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #3 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_`: env_mapping -> sample_floor
- #4 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #5 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #6 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_bottoming_entry_allowed_stal`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #7 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #8 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #9 `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio`: lifecycle_stage_underproduction -> lifecycle_stage_underproduction
- #10 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_:ac84e192b8`: sample_floor -> sample_floor
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s`: sample_floor -> sample_floor
- #12 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit`: sample_floor -> sample_floor
- #13 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f`: sample_floor -> sample_floor
- #14 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_`: sample_floor -> sample_floor

## Real Conversion Queue
- none
