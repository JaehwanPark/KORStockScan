# Lifecycle Bucket Discovery - 2026-06-09

## 판정
- status: `pass`
- source_contract_status: `warning` / changes: `11`
- ai_two_pass_review: `disabled` / model: `-` / tier: `tier2`
- ai_review_shards: `0` / `5` parsed, reviewed_candidates=`0`
- surfaced_candidate_count: `219`
- canonical/legacy buckets: `137` / `486`
- dual_proposals: deterministic=`500` ai=`0` hybrid_selected=`0`
- absorbed/source_quality_blocker: `372` / `0`
- lifecycle_flow_parent_granularity: `target_pass` level=`L2_default` parents=`51` target=`30-60`
- lifecycle_flow_absorbed_children: child=`153` sample=`18944` conflict_parents=`7`
- ldm_refinement_pressure: input=`4` consumed=`4` closures=`{'absorbed_into_existing_parent': 2, 'new_parent_candidate_created': 1, 'parent_refinement_candidate_created': 1}`
- sim_auto_approved_count: `54`
- lifecycle_flow_sim_probe_candidate_count: `18`
- source_dimension_gap_count: `51` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `353` / sim_live_connected: `17`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['source_contract_drift_warning', 'ai_review_provider_disabled', 'lifecycle_flow_review:ai_review_provider_disabled', 'ai_review_provider_disabled', 'sim_policy_review:ai_review_provider_disabled']`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `7`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'resolution_complete': 4, 'resolution_blocked_thin_sample': 3}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.177048` ev_after=`-0.177048` children=`15` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`5` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.616448` ev_after=`-0.616448` children=`15` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`5` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.173693` ev_after=`-1.173693` children=`9` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entr` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.496427` ev_after=`-0.496427` children=`11` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`4` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|entry_so` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-1.042889` ev_after=`-1.042889` children=`8` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|entry_so` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-0.601083` ev_after=`-0.601083` children=`6` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`2` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']` 
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`0.24115` ev_after=`0.24115` children=`4` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`1` positive_thin=`0` sim_eligible=`False` live_blockers=`['sample_below_live_floor']` 

## 근거

### Source Contract Changes
- `source_added` severity=`warning` subject=`entry` detail=`{'source_key': 'entry'}`
- `source_added` severity=`warning` subject=`institutional_flow_context` detail=`{'source_key': 'institutional_flow_context'}`
- `source_added` severity=`warning` subject=`lifecycle_ai_context_attribution` detail=`{'source_key': 'lifecycle_ai_context_attribution'}`
- `source_added` severity=`warning` subject=`scale_in_attribution` detail=`{'source_key': 'scale_in_attribution'}`
- `source_added` severity=`warning` subject=`scalp_sim_holding` detail=`{'source_key': 'scalp_sim_holding'}`
- `source_added` severity=`warning` subject=`scalp_sim_overnight` detail=`{'source_key': 'scalp_sim_overnight'}`
- `source_added` severity=`warning` subject=`scalp_sim_panic` detail=`{'source_key': 'scalp_sim_panic'}`
- `source_added` severity=`warning` subject=`scalp_sim_scale_in` detail=`{'source_key': 'scalp_sim_scale_in'}`
- `source_added` severity=`warning` subject=`scalp_sim_submit` detail=`{'source_key': 'scalp_sim_submit'}`
- `source_added` severity=`warning` subject=`sim_post_sell` detail=`{'source_key': 'sim_post_sell'}`
- `source_added` severity=`warning` subject=`wait6579` detail=`{'source_key': 'wait6579'}`

### AI Two-Pass Review
- interpretation_count: `0`
- ai_tier2_proposal_count: `0`
- comparative_review_count: `0`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31265`
- `lifecycle_flow_review` status=`disabled` candidates=`1` omitted=`152` context_chars=`37821`
- `sim_policy_review` status=`disabled` candidates=`1` omitted=`57` context_chars=`34798`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31241`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31237`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`2.6813` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.0618` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4271` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.94` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4887` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.9121` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`12575` ev=`-0.6946` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`5251` ev=`0.6423` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`202` ev=`-1.0963` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`66` ev=`2.5152` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`31` ev=`2.9054` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`17` ev=`2.374` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`10` ev=`-0.235` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`7` ev=`-0.8343` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`6` ev=`-1.771` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.0195` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-0.7941` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.3164` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-0.4437` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-0.549` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
