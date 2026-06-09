# Lifecycle Bucket Discovery - 2026-06-05

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `disabled` / model: `-` / tier: `tier2`
- ai_review_shards: `0` / `5` parsed, reviewed_candidates=`0`
- surfaced_candidate_count: `256`
- canonical/legacy buckets: `146` / `483`
- dual_proposals: deterministic=`500` ai=`0` hybrid_selected=`0`
- absorbed/source_quality_blocker: `368` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L2_default` parents=`34` target=`30-60`
- lifecycle_flow_absorbed_children: child=`81` sample=`12294` conflict_parents=`4`
- ldm_refinement_pressure: input=`3` consumed=`3` closures=`{'new_parent_candidate_created': 3}`
- sim_auto_approved_count: `168`
- lifecycle_flow_sim_probe_candidate_count: `7`
- source_dimension_gap_count: `43` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `260` / sim_live_connected: `7`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['ai_review_provider_disabled', 'lifecycle_flow_review:ai_review_provider_disabled', 'ai_review_provider_disabled', 'sim_policy_review:ai_review_provider_disabled']`

## 근거

### AI Two-Pass Review
- interpretation_count: `0`
- ai_tier2_proposal_count: `0`
- comparative_review_count: `0`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28866`
- `lifecycle_flow_review` status=`disabled` candidates=`1` omitted=`80` context_chars=`35421`
- `sim_policy_review` status=`disabled` candidates=`1` omitted=`121` context_chars=`32400`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28842`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28838`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`10142` ev=`-0.666` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1542` ev=`0.5452` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`119` ev=`-1.0654` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`33` ev=`2.1037` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`10` ev=`1.441` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`9` ev=`2.7732` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`6` ev=`-1.03` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`5` ev=`-0.752` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-0.8943` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`4` ev=`-0.2125` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-0.9431` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-2.4213` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.9707` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.445` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.8103` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`hold_no_edge` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-0.1574` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.4646` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.4985` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-1.8108` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`-0.73` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
