# Lifecycle Bucket Discovery - 2026-06-25

## 판정
- status: `pass`
- source_contract_status: `warning` / changes: `12`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `4` / `5` parsed, reviewed_candidates=`4`
- surfaced_candidate_count: `86`
- canonical/legacy buckets: `154` / `482`
- dual_proposals: deterministic=`500` ai=`4` hybrid_selected=`4`
- absorbed/source_quality_blocker: `361` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L2_default` parents=`36` target=`30-60`
- lifecycle_flow_absorbed_children: child=`71` sample=`5583` conflict_parents=`2`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'new_parent_candidate_created': 1, 'parent_refinement_candidate_created': 2, 'rare_observation_only_budget_capped': 1}`
- sim_auto_approved_count: `5`
- lifecycle_flow_sim_probe_candidate_count: `5`
- source_dimension_gap_count: `50` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `411` / sim_live_connected: `3`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['source_contract_drift_warning']`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `2`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'resolution_blocked_thin_sample': 2}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.806543` ev_after=`-0.806543` children=`7` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-1.348033` ev_after=`-1.348033` children=`4` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`

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
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`34078`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`70` context_chars=`40655`
- `sim_policy_review` status=`parsed` candidates=`1` omitted=`22` context_chars=`37578`
- `gap_workorder_review` status=`parsed` candidates=`1` omitted=`11` context_chars=`37612`
- `taxonomy_discovery_review` status=`parsed` candidates=`1` omitted=`10` context_chars=`37795`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2813` ev=`-0.761` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`683` ev=`0.738` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`45` ev=`-0.924` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`28` ev=`1.8842` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`20` ev=`2.7449` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`8` ev=`3.7965` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.0287` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.02` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`0.11` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.88` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.5084` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`hold_no_edge` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.0802` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.5916` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.5748` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.7254` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.8467` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.2385` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`lifecycle_flow_sim_probe_candidate` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`0.8636` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.5196` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.0541` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
