# Runtime Apply Gap Audit - 2026-06-12

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `29`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `72` / actionable=`0`
- quiet gap: `284` / rollup=`284` / directive=`0`

## 공격적 런타임 추진 대상
- `entry:time_bucket:time_1000_1200`: stage=entry, EV=1.0702, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=1.6939, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=1.6939, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_63_65`: stage=entry, EV=2.1288, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.2648, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=3.0443, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=0.5157, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=0.7552, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:wait_requote`: stage=entry, EV=1.6939, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=1.6939, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=1.5937, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_ok`: stage=entry, EV=0.3071, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_watch`: stage=entry, EV=1.7649, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.8946, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.8946, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5583, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:scalping_pyramid_ok`: stage=scale_in, EV=3.464, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_9694893e9a`: stage=lifecycle_flow, EV=3.616884, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: stage=lifecycle_flow, EV=13.281604, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7d92990310`: stage=lifecycle_flow, EV=15.378545, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: scale_in_bucket_runtime_policy_v1:2026-06-12 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
