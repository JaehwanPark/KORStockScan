# Runtime Apply Gap Audit - 2026-06-11

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `24`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `66` / actionable=`0`
- quiet gap: `333` / rollup=`333` / directive=`0`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.7655, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`: stage=lifecycle_flow, EV=0.966, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `entry:time_bucket:time_1000_1200`: stage=entry, EV=0.338, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=0.9416, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.1815, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=0.6228, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:wait_requote`: stage=entry, EV=0.8699, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=0.8699, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_watch`: stage=entry, EV=0.6265, 방향=runtime_bridge, 현재=code_patch_required
- `entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hi`: stage=entry, EV=0.6663, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.6144, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.6144, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5422, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.8232, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b74bbc500a`: stage=lifecycle_flow, EV=3.173906, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: scale_in_bucket_runtime_policy_v1:2026-06-11 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
