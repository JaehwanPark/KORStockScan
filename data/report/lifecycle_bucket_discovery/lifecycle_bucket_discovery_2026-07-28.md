# Lifecycle Bucket Discovery - 2026-07-28

## 판정
- status: `pass`
- source_contract_status: `warning` / changes: `12`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `3` / `5` parsed, reviewed_candidates=`3`
- surfaced_candidate_count: `24`
- canonical/legacy buckets: `96` / `106`
- dual_proposals: deterministic=`118` ai=`3` hybrid_selected=`2`
- absorbed/source_quality_blocker: `33` / `0`
- lifecycle_flow_parent_granularity: `too_broad` level=`L2_default` parents=`7` target=`30-60`
- lifecycle_flow_absorbed_children: child=`13` sample=`39` conflict_parents=`0`
- ldm_refinement_pressure: input=`0` consumed=`0` closures=`{}`
- sim_auto_approved_count: `0`
- lifecycle_flow_sim_probe_candidate_count: `0`
- source_dimension_gap_count: `14` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `87` / sim_live_connected: `0`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['source_contract_drift_warning']`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `0`
- sim_eligible_after_resolution: `0`
- resolution_states: `{}`

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
- interpretation_count: `3`
- ai_tier2_proposal_count: `3`
- comparative_review_count: `3`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`35035`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`12` context_chars=`40071`
- `sim_policy_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`35005`
- `gap_workorder_review` status=`parsed` candidates=`1` omitted=`11` context_chars=`38569`
- `taxonomy_discovery_review` status=`parsed` candidates=`1` omitted=`10` context_chars=`38752`

### Source Dimension Gap Enrichment
- gap_count: `14` / actionable_unknown_gap_count: `0`
- join_gap_candidate_count: `0` / sampled: `0`
- join_gap_stage_counts: `{}`
- join_gap_bucket_type_counts: `{}`
- join_gap_recommended_next_action: `enrich_bucket_label_or_join_key_before_bucket_decision`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-1.1165` ai_final=`keep` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.1725` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`0.62` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`new_bucket_candidate` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`new_bucket_candidate` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`new_bucket_candidate` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`new_bucket_candidate` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_ok_or_u` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`new_bucket_candidate` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_order_bundle_submitted_revalidatio` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`0` ev=`None` ai_final=`-` taxonomy=`absorb_as_dimension`
- `source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:institutional_flow_context` joined=`0` ev=`None` ai_final=`correct` taxonomy=`create_new_dimension`
- `source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:lifecycle_ai_context_attribution` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`
- `source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:scale_in_attribution` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`
- `source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:scale_in_counterfactual_enrichment` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`
- `source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:scalp_sim_holding` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`
- `source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:scalp_sim_overnight` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`
- `source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic` stage=`source_contract` state=`new_bucket_candidate` action=`update_source_contract_or_taxonomy` relation=`new_bucket_candidate` canonical=`source_contract:source_added:scalp_sim_panic` joined=`0` ev=`None` ai_final=`-` taxonomy=`keep_bucket`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
