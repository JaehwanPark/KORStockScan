# Runtime Apply Gap Audit - 2026-05-28

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `27`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `0`

## 공격적 런타임 추진 대상
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:time_bucket:time_unknown`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=1.5086, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o`: stage=entry, EV=1.643, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.1823, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:liquidity_bucket:liquidity_unknown`: stage=entry, EV=1.2917, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_unknown`: stage=entry, EV=1.2898, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:action_unknown`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strength_unknown`: stage=entry, EV=1.6101, 방향=runtime_bridge, 현재=code_patch_required
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown`: stage=entry, EV=1.1823, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.6052, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.605, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5982, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.7926, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=19.000977, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=15.206261, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=10.942032, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=10.359659, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- 신규 작업지시 없음

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
