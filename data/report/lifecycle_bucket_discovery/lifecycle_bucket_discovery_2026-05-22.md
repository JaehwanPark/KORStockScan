# Lifecycle Bucket Discovery - 2026-05-22

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `disabled` / model: `-` / tier: `tier3`
- surfaced_candidate_count: `94`
- sim_auto_approved_count: `84`
- live_auto_apply_ready_count: `0`
- human_intervention_required: `False`
- warnings: `['ai_review_provider_disabled']`

## 근거

### AI Two-Pass Review
- interpretation_count: `0`
- audit_status: `-`
- audit_issues: `[]`
- audit_reason: `-`

- `entry:source_stage:wait6579_ev_cohort` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:stale_bucket:fresh_or_unflagged` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:chosen_action:action_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:exit_rule:exit_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:liquidity_bucket:liquidity_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:overbought_bucket:overbought_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:strength_bucket:strength_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `entry:time_bucket:time_unknown` stage=`entry` state=`new_bucket_candidate` action=`relax_or_recover` relation=`new_bucket_candidate` joined=`16` ev=`3.4568` ai_final=`-`
- `scale_in:arm:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`3306` ev=`-0.5472` ai_final=`-`
- `scale_in:blocker_namespace:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`2141` ev=`-0.6893` ai_final=`-`
- `scale_in:arm:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`1560` ev=`0.5504` ai_final=`-`
- `scale_in:blocker_namespace:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`1560` ev=`0.5504` ai_final=`-`
- `scale_in:blocker_reason:profit_not_enough` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`1324` ev=`0.525` ai_final=`-`
- `scale_in:blocker_reason:low_broken` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`234` ev=`-0.3345` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_82` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`52` ev=`-0.7169` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_96` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`51` ev=`-0.7881` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_76` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`46` ev=`-0.6882` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_0_90` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`38` ev=`-0.7983` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_1_12` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`38` ev=`-0.9804` ai_final=`-`
- `scale_in:blocker_reason:pnl_out_of_range_1_20` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`32` ev=`-1.0006` ai_final=`-`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
