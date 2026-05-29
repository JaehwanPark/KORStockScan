# Runtime Apply Gap Audit - 2026-05-28

- 상태: `fail`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `17`
- 실패 표면화: `8`
- 재시도 큐: `0`
- Codex 작업지시: `9`

## 공격적 런타임 추진 대상
- `entry:time_bucket:time_1000_1200`: stage=entry, EV=0.4269, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:exit_rule:exit_unknown`: stage=entry, EV=0.173, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_normal`: stage=entry, EV=0.4583, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5982, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.7926, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=19.000977, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=15.206261, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=10.942032, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=10.359659, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=8.725511, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=3.492368, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_9f98f62c78f5`: stage=unknown, EV=11.888882, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_3d55602cd1b3`: stage=unknown, EV=10.435387, 방향=sim_policy_or_approval_ready, 현재=code_patch_required

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_mid_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_flat_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_deep_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_mid_mae_mid_held_missing_trailing_after_mfe_stop 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_9f98f62c78f5 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: swing_bucket_selection_discovery_arm_attribution_breakout_confirm_entry_confidence_weighted_trailing_after_mfe_manuf_3d55602cd1b3 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: entry_wait6579_score66_69_recovery_gate_v1:2026-05-28 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
