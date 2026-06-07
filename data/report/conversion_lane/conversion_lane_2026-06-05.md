# Conversion Lane - 2026-06-05

## Decision
- conversion candidates: `574`
- real conversion queue: `0`
- positive EV runtime observed: `0`
- positive EV not due until next PREOPEN: `26`
- positive EV previous-policy natural match 0: `4`
- positive EV real conversion queue: `0`
- positive EV sample-floor blocked known floor: `4`
- positive EV sample-floor unknown floor: `11`
- positive EV sample-floor related total: `15`
- positive EV sample-floor provenance: scope=`conversion_candidates` window=`mixed_source_windows` window_counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 4, 'source_report_window': 11}` basis=`candidate_sample_vs_required_sample`
- conversion candidate strategy scope: scalp=`199` swing=`374` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `submit_drought`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `env_mapping`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)

## Top Conversion Blockers
- #1 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #2 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #3 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit
- #4 `submit_drought:SIM_REAL_AUTHORITY`: submit_drought -> close_submit_drought_sim_real_authority
- #5 `submit_drought:SOURCE_TAXONOMY_LEAKAGE`: submit_drought -> close_submit_drought_source_taxonomy_leakage
- #6 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #7 `entry:source_stage:wait6579_ev_cohort`: env_mapping -> complete_parent_flow
- #8 `entry:stale_bucket:fresh_or_unflagged`: env_mapping -> complete_parent_flow
- #9 `scale_in:blocker_reason:trend_not_strong`: env_mapping -> complete_parent_flow
- #10 `entry:strength_bucket:weak_strength_momentum`: sample_floor -> complete_parent_flow
- #11 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: source_quality -> source_quality
- #12 `scale_in:arm:pyramid`: env_mapping -> complete_parent_flow
- #13 `scale_in:blocker_namespace:pyramid`: env_mapping -> complete_parent_flow
- #14 `scale_in:blocker_reason:profit_not_enough`: env_mapping -> complete_parent_flow
- #15 `entry:chosen_action:wait_requote`: sample_floor -> complete_parent_flow
- #16 `entry:liquidity_bucket:liquidity_high`: sample_floor -> complete_parent_flow
- #17 `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge`: source_quality -> source_quality
- #18 `entry:strength_bucket:strong_strength_momentum`: sample_floor -> complete_parent_flow
- #19 `swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_scale_in_none_3527c127d645`: sample_floor -> sample_floor
- #20 `scale_in:blocker_namespace:avg_down_only`: env_mapping -> complete_parent_flow

## Real Conversion Queue
- none
