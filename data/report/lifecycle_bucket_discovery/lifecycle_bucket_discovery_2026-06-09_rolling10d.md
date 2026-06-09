# Lifecycle Bucket Discovery - 2026-06-09_rolling10d

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `disabled` / model: `-` / tier: `tier2`
- ai_review_shards: `0` / `5` parsed, reviewed_candidates=`0`
- surfaced_candidate_count: `311`
- canonical/legacy buckets: `41` / `500`
- dual_proposals: deterministic=`500` ai=`0` hybrid_selected=`0`
- absorbed/source_quality_blocker: `468` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L1_broad` parents=`38` target=`30-60`
- lifecycle_flow_absorbed_children: child=`309` sample=`57031` conflict_parents=`13`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'absorbed_into_existing_parent': 2, 'new_parent_candidate_created': 2}`
- sim_auto_approved_count: `2`
- lifecycle_flow_sim_probe_candidate_count: `31`
- source_dimension_gap_count: `125` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `404` / sim_live_connected: `30`
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
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28310`
- `lifecycle_flow_review` status=`disabled` candidates=`1` omitted=`199` context_chars=`34866`
- `sim_policy_review` status=`disabled` candidates=`1` omitted=`12` context_chars=`34840`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28286`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`28282`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`2.6813` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.0618` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.3597` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.3089` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.8776` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.7838` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`6.0932` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4271` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.393` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.1746` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.3678` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.94` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4887` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`6.9078` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.9121` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.7194` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4689` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.435` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.8346` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.0534` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
