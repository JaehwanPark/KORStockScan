# Lifecycle Bucket Discovery - 2026-07-09_mtd

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `2` / `5` parsed, reviewed_candidates=`2`
- surfaced_candidate_count: `238`
- canonical/legacy buckets: `45` / `500`
- dual_proposals: deterministic=`500` ai=`78` hybrid_selected=`78`
- absorbed/source_quality_blocker: `464` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L1_broad` parents=`32` target=`30-60`
- lifecycle_flow_absorbed_children: child=`233` sample=`28773` conflict_parents=`12`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'new_parent_candidate_created': 3, 'parent_refinement_candidate_created': 1}`
- sim_auto_approved_count: `1`
- lifecycle_flow_sim_probe_candidate_count: `21`
- source_dimension_gap_count: `157` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `353` / sim_live_connected: `20`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `[]`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `12`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'resolution_complete': 5, 'resolution_blocked_thin_sample': 7}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_complete` tag=`resolution_complete` ev_before=`1.771194` ev_after=`1.771194` children=`18` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`16` positive_thin=`0` sim_eligible=`False` live_blockers=`[]`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.072413` ev_after=`-1.072413` children=`13` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.520529` ev_after=`-0.520529` children=`9` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`4` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.482242` ev_after=`-1.482242` children=`10` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_complete` tag=`resolution_complete` ev_before=`-2.010873` ev_after=`-2.010873` children=`7` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-2.885112` ev_after=`-2.885112` children=`6` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`1` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.968671` ev_after=`-0.968671` children=`7` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.201583` ev_after=`-0.201583` children=`6` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`0.074617` ev_after=`0.074617` children=`6` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`2` positive_thin=`0` sim_eligible=`False` live_blockers=`['sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-1.76252` ev_after=`-1.76252` children=`5` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`0.04325` ev_after=`0.04325` children=`4` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`2` positive_thin=`0` sim_eligible=`False` live_blockers=`['sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.125` ev_after=`-0.125` children=`7` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`5` positive_thin=`1` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`

## 근거

### AI Two-Pass Review
- interpretation_count: `2`
- ai_tier2_proposal_count: `2`
- comparative_review_count: `2`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`40558`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`199` context_chars=`47126`
- `sim_policy_review` status=`parsed` candidates=`1` omitted=`15` context_chars=`47110`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`40534`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`40530`

### Source Dimension Gap Enrichment
- gap_count: `157` / actionable_unknown_gap_count: `0`
- join_gap_candidate_count: `0` / sampled: `0`
- join_gap_stage_counts: `{}`
- join_gap_bucket_type_counts: `{}`
- join_gap_recommended_next_action: `enrich_bucket_label_or_join_key_before_bucket_decision`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`11744` ev=`-0.9679` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2070` ev=`0.6393` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`187` ev=`-1.02` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`41` ev=`0.9124` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`13` ev=`4.4797` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`hold_no_edge` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`13` ev=`0.2535` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`11` ev=`-0.9509` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`6` ev=`3.8073` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`5` ev=`-1.6896` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`5` ev=`-1.308` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-2.794` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-0.82` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-2.6964` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.3825` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.6292` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`0.415` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.3398` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.24` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.8977` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-2.2218` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
