# Lifecycle Bucket Discovery - 2026-05-22

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `disabled` / model: `-` / tier: `tier3`
- surfaced_candidate_count: `120`
- sim_auto_approved_count: `119`
- live_auto_apply_ready_count: `1`
- human_intervention_required: `False`
- warnings: `['ai_review_provider_disabled', 'ai_two_pass_review_disabled_live_auto_deferred_to_post_apply']`

## 근거

### AI Two-Pass Review
- interpretation_count: `0`
- audit_status: `-`
- audit_issues: `[]`
- audit_reason: `-`

- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown` stage=`entry` state=`live_auto_apply_ready` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`24` ev=`2.1843` ai_final=`-`
- `entry:chosen_action:no_buy_ai` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`102` ev=`-0.3299` ai_final=`-`
- `entry:source_stage:scalp_entry_action_decision_snapshot` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`102` ev=`-0.3299` ai_final=`-`
- `entry:stale_bucket:fresh` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`80` ev=`-0.3696` ai_final=`-`
- `entry:source_stage:wait6579_ev_cohort` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`35` ev=`2.3199` ai_final=`-`
- `entry:stale_bucket:fresh_or_unflagged` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`35` ev=`2.3199` ai_final=`-`
- `entry:exit_rule:scalp_trailing_take_profit` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`34` ev=`-0.3781` ai_final=`-`
- `entry:time_bucket:time_1000_1200` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`33` ev=`-0.8942` ai_final=`-`
- `entry:score_band:score_66_69` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`28` ev=`1.6584` ai_final=`-`
- `entry:exit_rule:scalp_hard_stop_pct` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`23` ev=`-0.4198` ai_final=`-`
- `entry:score_band:score_63_65` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`16` ev=`1.5141` ai_final=`-`
- `scale_in:arm:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`14657` ev=`-0.3673` ai_final=`-`
- `scale_in:blocker_namespace:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`9960` ev=`-0.4206` ai_final=`-`
- `scale_in:blocker_reason:profit_not_enough` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`3633` ev=`0.3993` ai_final=`-`
- `scale_in:blocker_reason:low_broken` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`402` ev=`-0.3394` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_74` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`335` ev=`-0.6702` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_1_29` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`286` ev=`-1.184` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_76` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`89` ev=`-0.6967` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_71` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`76` ev=`-0.5846` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_96` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`73` ev=`-0.7814` ai_final=`-`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
