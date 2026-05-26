# Lifecycle Bucket Discovery - 2026-05-26

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `parsed` / model: `gpt-5.4` / tier: `tier2`
- surfaced_candidate_count: `184`
- sim_auto_approved_count: `183`
- live_auto_apply_ready_count: `1`
- human_intervention_required: `False`
- warnings: `['ai_review_ambiguous_live_candidate_kept_for_post_apply']`

## 근거

### AI Two-Pass Review
- interpretation_count: `60`
- audit_status: `correction_required`
- audit_issues: `['Summary says 184 surfaced candidates, but 60 records were provided; conclusions apply to provided records only.', 'entry:time_bucket:time_unknown was labeled new_bucket_candidate, but time_bucket is already in the contract.', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o was labeled new_bucket_candidate, but combo_entry_spot is already in the contract.', 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown was labeled new_bucket_candidate, but combo_entry_spot is already in the contract.']`
- audit_reason: `Three input relation labels need correction; no contract failure was found.`

- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown` stage=`entry` state=`live_auto_apply_ready` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`49` ev=`2.3066` ai_final=`correct`
- `entry:source_stage:wait6579_ev_cohort` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`163` ev=`3.3661` ai_final=`keep`
- `entry:stale_bucket:fresh_or_unflagged` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`163` ev=`3.3661` ai_final=`keep`
- `entry:time_bucket:time_unknown` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`163` ev=`3.3661` ai_final=`correct`
- `entry:score_band:score_70p` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`135` ev=`2.7821` ai_final=`keep`
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`107` ev=`3.9731` ai_final=`correct`
- `entry:score_band:score_66_69` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`49` ev=`2.3066` ai_final=`keep`
- `entry:source_stage:scalp_entry_action_decision_snapshot` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`46` ev=`-1.5688` ai_final=`keep`
- `entry:chosen_action:buy_now` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`26` ev=`-1.7658` ai_final=`keep`
- `entry:exit_rule:scalp_soft_stop_pct` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`21` ev=`-1.0755` ai_final=`keep`
- `entry:chosen_action:no_buy_ai` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`20` ev=`-1.3126` ai_final=`keep`
- `entry:exit_rule:scalp_trailing_take_profit` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`17` ev=`-1.9702` ai_final=`keep`
- `entry:overbought_bucket:overbought_ok` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`10` ev=`-2.9831` ai_final=`keep`
- `scale_in:arm:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`19436` ev=`-0.6197` ai_final=`keep`
- `scale_in:blocker_namespace:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`12321` ev=`-0.7722` ai_final=`keep`
- `scale_in:blocker_namespace:avg_down_only` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`7115` ev=`-0.3555` ai_final=`keep`
- `scale_in:arm:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`5749` ev=`0.4885` ai_final=`keep`
- `scale_in:blocker_namespace:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` joined=`5749` ev=`0.4885` ai_final=`keep`
- `scale_in:ai_score_band:score_66_69` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` joined=`5223` ev=`-0.3253` ai_final=`keep`
- `scale_in:blocker_reason:profit_not_enough` stage=`scale_in` state=`sim_auto_approved` action=`keep_or_tighten_blocker_candidate` relation=`existing_bucket_refinement` joined=`4709` ev=`0.5589` ai_final=`keep`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
