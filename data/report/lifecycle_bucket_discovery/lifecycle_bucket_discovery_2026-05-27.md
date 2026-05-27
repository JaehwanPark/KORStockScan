# Lifecycle Bucket Discovery - 2026-05-27

## 판정
- status: `pass`
- source_contract_status: `pass` / changes: `0`
- ai_two_pass_review: `parsed` / model: `gpt-5.4` / tier: `tier2`
- ai_review_shards: `2` / `4` parsed, reviewed_candidates=`7`
- surfaced_candidate_count: `186`
- canonical/legacy buckets: `206` / `369`
- dual_proposals: deterministic=`379` ai=`7` hybrid_selected=`0`
- absorbed/source_quality_blocker: `175` / `0`
- sim_auto_approved_count: `185`
- live_auto_apply_ready_count: `1`
- human_intervention_required: `False`
- warnings: `[]`

## 근거

### AI Two-Pass Review
- interpretation_count: `7`
- ai_tier2_proposal_count: `7`
- comparative_review_count: `7`
- audit_status: `pass`
- audit_issues: `[]`
- audit_reason: `sharded review aggregate`

### AI Review Shards
- `live_contract_review` status=`parsed` candidates=`1` omitted=`0` context_chars=`13365`
- `sim_policy_review` status=`parsed` candidates=`6` omitted=`179` context_chars=`29568`
- `gap_workorder_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`8961`
- `taxonomy_discovery_review` status=`skipped_empty` candidates=`0` omitted=`0` context_chars=`8957`

- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown` stage=`entry` state=`live_auto_apply_ready` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`entry:combo_entry_spot:score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` joined=`49` ev=`1.5253` ai_final=`keep` taxonomy=`merge`
- `entry:source_stage:wait6579_ev_cohort` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`entry:source_stage:wait6579_ev_cohort` joined=`130` ev=`2.2594` ai_final=`-` taxonomy=`keep_bucket`
- `entry:stale_bucket:fresh_or_unflagged` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`entry:stale_bucket:fresh_or_unflagged` joined=`130` ev=`2.2594` ai_final=`-` taxonomy=`keep_bucket`
- `entry:time_bucket:time_unknown` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`new_bucket_candidate` canonical=`entry:time_bucket:time_unknown` joined=`130` ev=`2.2594` ai_final=`-` taxonomy=`instrumentation_gap`
- `entry:score_band:score_70p` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`entry:score_band:score_70p` joined=`81` ev=`2.4554` ai_final=`-` taxonomy=`keep_bucket`
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`new_bucket_candidate` canonical=`entry:combo_entry_spot:score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` joined=`76` ev=`2.6587` ai_final=`-` taxonomy=`instrumentation_gap`
- `entry:score_band:score_66_69` stage=`entry` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`entry:score_band:score_66_69` joined=`49` ev=`1.5253` ai_final=`-` taxonomy=`keep_bucket`
- `entry:source_stage:scalp_entry_action_decision_snapshot` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`entry:source_stage:scalp_entry_action_decision_snapshot` joined=`18` ev=`-0.826` ai_final=`-` taxonomy=`keep_bucket`
- `entry:chosen_action:no_buy_ai` stage=`entry` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`entry:chosen_action:NO_BUY_AI` joined=`13` ev=`-0.8994` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:ai_score_band:score_70p` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:ai_score_band:score_70p` joined=`28678` ev=`-0.4042` ai_final=`keep` taxonomy=`keep_bucket`
- `scale_in:arm:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:arm:AVG_DOWN` joined=`17834` ev=`-0.6507` ai_final=`keep` taxonomy=`keep_bucket`
- `scale_in:blocker_namespace:avg_down` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_namespace:AVG_DOWN` joined=`11402` ev=`-0.8103` ai_final=`keep` taxonomy=`keep_bucket`
- `scale_in:blocker_namespace:avg_down_only` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_namespace:AVG_DOWN_ONLY` joined=`6432` ev=`-0.3678` ai_final=`keep` taxonomy=`keep_bucket`
- `scale_in:arm:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`scale_in:arm:PYRAMID` joined=`3878` ev=`0.3193` ai_final=`keep` taxonomy=`keep_bucket`
- `scale_in:blocker_namespace:pyramid` stage=`scale_in` state=`sim_auto_approved` action=`relax_or_recover` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_namespace:PYRAMID` joined=`3878` ev=`0.3193` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:blocker_reason:add_judgment_locked` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_reason:add_judgment_locked` joined=`3659` ev=`-0.3291` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:blocker_reason:profit_not_enough` stage=`scale_in` state=`sim_auto_approved` action=`keep_or_tighten_blocker_candidate` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_reason:profit_not_enough` joined=`3118` ev=`0.5044` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:ai_score_band:score_lt60` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:ai_score_band:score_lt60` joined=`1217` ev=`-1.8393` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:ai_score_band:score_63_65` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:ai_score_band:score_63_65` joined=`963` ev=`-0.4679` ai_final=`-` taxonomy=`keep_bucket`
- `scale_in:blocker_reason:low_broken` stage=`scale_in` state=`sim_auto_approved` action=`tighten_or_exclude` relation=`existing_bucket_refinement` canonical=`scale_in:blocker_reason:low_broken` joined=`918` ev=`-0.3522` ai_final=`-` taxonomy=`keep_bucket`

## 다음 액션
- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.
- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.
- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.
- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.
