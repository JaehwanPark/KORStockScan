# Lifecycle Bucket Discovery - 2026-07-02

## 판정
- status: `pass`
- source_contract_status: `warning` / changes: `14`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `4` / `5` parsed, reviewed_candidates=`4`
- surfaced_candidate_count: `82`
- canonical/legacy buckets: `140` / `483`
- dual_proposals: deterministic=`500` ai=`6` hybrid_selected=`6`
- absorbed/source_quality_blocker: `374` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L2_default` parents=`43` target=`30-60`
- lifecycle_flow_absorbed_children: child=`77` sample=`6255` conflict_parents=`2`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'parent_refinement_candidate_created': 2, 'rare_observation_only_budget_capped': 2}`
- sim_auto_approved_count: `1`
- lifecycle_flow_sim_probe_candidate_count: `1`
- source_dimension_gap_count: `76` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `397` / sim_live_connected: `0`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['source_contract_drift_warning']`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `2`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'resolution_blocked_source_quality': 2}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`1.437567` ev_after=`1.437567` children=`2` sq_gap=`2` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['source_quality_gap_children']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|entry_so` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-0.65855` ev_after=`-0.65855` children=`2` sq_gap=`2` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive', 'sample_below_live_floor']` 

## 근거

### Source Contract Changes
- `source_added` severity=`warning` subject=`entry` detail=`{'source_key': 'entry'}`
- `source_added` severity=`warning` subject=`institutional_flow_context` detail=`{'source_key': 'institutional_flow_context'}`
- `source_added` severity=`warning` subject=`lifecycle_ai_context_attribution` detail=`{'source_key': 'lifecycle_ai_context_attribution'}`
- `source_added` severity=`warning` subject=`scale_in_attribution` detail=`{'source_key': 'scale_in_attribution'}`
- `source_added` severity=`warning` subject=`scale_in_counterfactual_enrichment` detail=`{'source_key': 'scale_in_counterfactual_enrichment'}`
- `source_added` severity=`warning` subject=`scalp_sim_holding` detail=`{'source_key': 'scalp_sim_holding'}`
- `source_added` severity=`warning` subject=`scalp_sim_overnight` detail=`{'source_key': 'scalp_sim_overnight'}`
- `source_added` severity=`warning` subject=`scalp_sim_panic` detail=`{'source_key': 'scalp_sim_panic'}`
- `source_added` severity=`warning` subject=`scalp_sim_scale_in` detail=`{'source_key': 'scalp_sim_scale_in'}`
- `source_added` severity=`warning` subject=`scalp_sim_submit` detail=`{'source_key': 'scalp_sim_submit'}`
- `source_added` severity=`warning` subject=`sim_post_sell` detail=`{'source_key': 'sim_post_sell'}`
- `source_added` severity=`warning` subject=`wait6579` detail=`{'source_key': 'wait6579'}`

### AI Two-Pass Review
- interpretation_count: `4`
- ai_tier2_proposal_count: `4`
- comparative_review_count: `4`
- audit_status: `pass`
- audit_issues: `['Input classification_state lifecycle_flow_sim_probe_candidate is outside review output state enum; normalized to source_only_keep_collecting.', 'current_ai_tier2_proposal says reject/not_provided, but independent Tier2 review can still assess taxonomy.']`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`41157`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`76` context_chars=`47724`
- `sim_policy_review` status=`parsed` candidates=`1` omitted=`9` context_chars=`44657`
- `gap_workorder_review` status=`parsed` candidates=`1` omitted=`13` context_chars=`44691`
- `taxonomy_discovery_review` status=`parsed` candidates=`1` omitted=`12` context_chars=`44874`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2720` ev=`-0.9518` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`469` ev=`0.5635` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`46` ev=`-1.0143` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`11` ev=`0.7047` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.4367` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-2.1328` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`0.8157` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`0.655` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.654` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.9776` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.83` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.4308` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.125` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`0.0041` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`9.4991` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.5266` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-2.017` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-2.2285` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-2.7521` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`lifecycle_flow_sim_probe_candidate` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`0.8991` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
