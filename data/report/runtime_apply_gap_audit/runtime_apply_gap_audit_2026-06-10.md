# Runtime Apply Gap Audit - 2026-06-10

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `24`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `63` / actionable=`0`
- quiet gap: `338` / rollup=`338` / directive=`0`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f`: stage=lifecycle_flow, EV=0.7519, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.345, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`: stage=lifecycle_flow, EV=0.9145, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=0.4052, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:time_bucket:time_0900_1000`: stage=entry, EV=0.39, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=0.6407, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:chosen_action:wait_requote`: stage=entry, EV=0.4052, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=0.4052, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=0.5383, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_watch`: stage=entry, EV=0.6363, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.6479, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.6479, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5226, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:scalping_pyramid_ok`: stage=scale_in, EV=2.7417, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b74bbc500a`: stage=lifecycle_flow, EV=3.115107, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: stage=lifecycle_flow, EV=10.477788, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_387f622ebb`: stage=lifecycle_flow, EV=2.980416, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: scale_in_bucket_runtime_policy_v1:2026-06-10 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
