# Lifecycle Bucket Discovery - 2026-06-24_rolling5d

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `2` / `5` parsed, reviewed_candidates=`2`
- surfaced_candidate_count: `238`
- canonical/legacy buckets: `39` / `500`
- dual_proposals: deterministic=`500` ai=`66` hybrid_selected=`66`
- absorbed/source_quality_blocker: `470` / `0`
- lifecycle_flow_parent_granularity: `too_broad` level=`L1_broad` parents=`26` target=`30-60`
- lifecycle_flow_absorbed_children: child=`225` sample=`16054` conflict_parents=`11`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'new_parent_candidate_created': 2, 'parent_refinement_candidate_created': 1, 'rare_observation_only_budget_capped': 1}`
- sim_auto_approved_count: `6`
- lifecycle_flow_sim_probe_candidate_count: `12`
- source_dimension_gap_count: `101` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `446` / sim_live_connected: `9`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `[]`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `11`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'sim_ineligible_ev_negative': 1, 'resolution_complete': 8, 'resolution_blocked_thin_sample': 2}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`sim_ineligible_ev_negative` tag=`제외 후에도 EV 음수` ev_before=`-0.777799` ev_after=`-0.8778` children=`24` sq_gap=`0` strategy_reversal=`0` exclude=`1` collecting=`2` positive_thin=`8` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'exclusion_proposed_not_applied']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_complete` tag=`resolution_complete` ev_before=`1.311876` ev_after=`1.311876` children=`19` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`16` positive_thin=`0` sim_eligible=`False` live_blockers=`[]`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.527414` ev_after=`-1.527414` children=`27` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.394544` ev_after=`-0.394544` children=`20` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`4` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.401342` ev_after=`-1.401342` children=`16` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`4` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.438381` ev_after=`-1.438381` children=`13` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.983227` ev_after=`-0.983227` children=`11` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.205617` ev_after=`-1.205617` children=`11` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`1.221118` ev_after=`1.221118` children=`3` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`2` positive_thin=`0` sim_eligible=`False` live_blockers=`[]`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.065822` ev_after=`-0.065822` children=`9` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.375714` ev_after=`-0.375714` children=`15` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`10` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`

## 근거

### AI Two-Pass Review
- interpretation_count: `2`
- ai_tier2_proposal_count: `2`
- comparative_review_count: `2`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31319`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`199` context_chars=`37878`
- `sim_policy_review` status=`parsed` candidates=`1` omitted=`7` context_chars=`37860`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31295`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31291`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`2.7581` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.7617` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`2.7877` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`2.2884` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.1504` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.6325` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`2.6084` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.5402` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`2.08` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`8038` ev=`-0.8213` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2211` ev=`0.8836` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`273` ev=`-0.9741` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`75` ev=`1.2116` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`50` ev=`1.564` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`hold_no_edge` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`34` ev=`0.1541` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`15` ev=`3.1107` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`11` ev=`-0.8041` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`6` ev=`-0.6133` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`6` ev=`2.881` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-1.4109` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
