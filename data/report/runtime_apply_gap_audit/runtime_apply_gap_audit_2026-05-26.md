# Runtime Apply Gap Audit - 2026-05-26

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `19`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `2`

## 공격적 런타임 추진 대상
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:time_bucket:time_unknown`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=2.7821, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o`: stage=entry, EV=3.9731, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown`: stage=entry, EV=2.3066, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=2.3066, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.4885, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.4885, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5589, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.8918, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:scalping_pyramid_ok`: stage=scale_in, EV=2.448, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stage_policy:entry_weighted_adm_v1`: stage=entry, EV=2.28, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=14.597777, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=11.058628, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=6.947201, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_mid_mae_flat_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=3.139001, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_mid_mae_low_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=2.471131, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `entry_wait6579_score66_69_recovery_gate_v1:2026-05-26`: stage=entry, EV=2.3066, 방향=runtime_bridge, 현재=code_patch_required

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: entry_wait6579_score66_69_recovery_gate_v1:2026-05-26 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `IMPLEMENT_SCALE_IN_POLICY_CONTRACT`: IMPLEMENT_SCALE_IN_POLICY_CONTRACT: scale_in_bucket_runtime_policy_v1:2026-05-26 후보가 runtime_blocked_contract_gap 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
