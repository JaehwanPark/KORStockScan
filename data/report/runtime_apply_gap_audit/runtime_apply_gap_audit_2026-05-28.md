# Runtime Apply Gap Audit - 2026-05-28

- 상태: `fail`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `32`
- 실패 표면화: `7`
- 재시도 큐: `0`
- Codex 작업지시: `8`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.55, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid`: stage=lifecycle_flow, EV=0.6803, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui`: stage=lifecycle_flow, EV=0.7773, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi`: stage=lifecycle_flow, EV=0.4138, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.2802, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.0765, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f`: stage=lifecycle_flow, EV=0.4806, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
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

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE`: RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f 후보가 positive_edge_stuck_source_only 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: entry_wait6579_score66_69_recovery_gate_v1:2026-05-28 후보가 runtime_blocked_contract_gap 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
