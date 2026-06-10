# Lifecycle Bucket Discovery - 2026-06-10

## 판정
- status: `pass`
- source_contract_status: `warning` / changes: `11`
- ai_two_pass_review: `parsed` / model: `sharded` / tier: `tier2`
- ai_review_shards: `2` / `5` parsed, reviewed_candidates=`2`
- surfaced_candidate_count: `242`
- canonical/legacy buckets: `168` / `481`
- dual_proposals: deterministic=`500` ai=`10` hybrid_selected=`10`
- absorbed/source_quality_blocker: `345` / `0`
- lifecycle_flow_parent_granularity: `too_broad` level=`L1_broad` parents=`29` target=`30-60`
- lifecycle_flow_absorbed_children: child=`145` sample=`23779` conflict_parents=`10`
- ldm_refinement_pressure: input=`0` consumed=`0` closures=`{}`
- sim_auto_approved_count: `93`
- lifecycle_flow_sim_probe_candidate_count: `8`
- source_dimension_gap_count: `63` / actionable_unknown_gap_count: `0`
- quiet_gap_count: `338` / sim_live_connected: `7`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['source_contract_drift_warning']`

## 판정 (Conflict Resolution)
- parent_conflict_resolution_count: `10`
- sim_eligible_after_resolution: `0`
- resolution_states: `{'resolution_blocked_source_quality': 5, 'resolution_complete': 2, 'resolution_blocked_thin_sample': 3}`

- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-1.082593` ev_after=`-1.082593` children=`14` sq_gap=`14` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-1.273358` ev_after=`-1.273358` children=`15` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-1.424063` ev_after=`-1.424063` children=`15` sq_gap=`4` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`1` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_complete` tag=`resolution_complete` ev_before=`-0.350833` ev_after=`-0.350833` children=`11` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`3` sim_eligible=`False` live_blockers=`['parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-1.13382` ev_after=`-1.13382` children=`9` sq_gap=`3` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-1.216167` ev_after=`-1.216167` children=`5` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`1` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`-1.14544` ev_after=`-1.14544` children=`5` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`1` sim_eligible=`False` live_blockers=`['parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_unobserved|submit_q` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-0.015225` ev_after=`-0.015225` children=`4` sq_gap=`2` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`1` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|subm` state=`resolution_blocked_source_quality` tag=`source-quality 때문에 판정 불가` ev_before=`-3.415` ev_after=`-3.415` children=`6` sq_gap=`6` strategy_reversal=`0` exclude=`0` collecting=`0` positive_thin=`0` sim_eligible=`False` live_blockers=`['source_quality_gap_children', 'parent_ev_not_positive', 'sample_below_live_floor']`
- conflict_parent=`lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit` state=`resolution_blocked_thin_sample` tag=`sample 부족 keep collecting` ev_before=`0.0628` ev_after=`0.0628` children=`2` sq_gap=`0` strategy_reversal=`0` exclude=`0` collecting=`1` positive_thin=`0` sim_eligible=`False` live_blockers=`['sample_below_live_floor']`

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
- interpretation_count: `2`
- ai_tier2_proposal_count: `2`
- comparative_review_count: `2`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31331`
- `lifecycle_flow_review` status=`parsed` candidates=`1` omitted=`144` context_chars=`37890`
- `sim_policy_review` status=`parsed` candidates=`1` omitted=`59` context_chars=`34882`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31307`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`31303`

- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`3.0042` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.7523` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.122` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`1` ev=`1.4597` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`18108` ev=`-0.8219` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3985` ev=`0.6492` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`245` ev=`-1.1049` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`35` ev=`0.3296` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`33` ev=`0.2695` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`18` ev=`0.8011` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`14` ev=`-0.7379` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`9` ev=`-0.8867` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=entry_observed|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`5` ev=`-0.95` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-0.9132` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`3` ev=`-1.6944` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq` stage=`lifecycle_flow` state=`lifecycle_flow_sim_probe_candidate` action=`hold_no_edge` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`0.0097` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.6342` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.3424` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`keep_collecting` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_watch_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-2.355` ai_final=`-` taxonomy=`absorb_as_dimension`
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f` stage=`lifecycle_flow` state=`source_only_keep_collecting` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=scale_in_observed|exit=exit_observed` joined=`2` ev=`-1.4154` ai_final=`-` taxonomy=`absorb_as_dimension`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
