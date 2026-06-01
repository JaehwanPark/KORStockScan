# Runtime Apply Gap Audit - 2026-05-29

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `20`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `4`
- source dimension gap: `96` / actionable=`48`
- quiet gap: `4` / rollup=`4` / directive=`1`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale`: stage=lifecycle_flow, EV=0.8633, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_watch_liquidi`: stage=lifecycle_flow, EV=0.7997, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.6217, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=1.9704, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=1.9704, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=1.9148, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.5423, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: stage=entry, EV=2.794, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:chosen_action:wait_requote`: stage=entry, EV=1.9704, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=1.9704, 방향=runtime_bridge, 현재=code_patch_required
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=1.9704, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=2.0934, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_normal`: stage=entry, EV=1.4616, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_watch`: stage=entry, EV=2.2663, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_chase_risk`: stage=entry, EV=1.4611, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:blocker_reason:scalp_sim_panic_scale_in_blocked`: stage=scale_in, EV=0.3343, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:arm:pyramid`: stage=scale_in, EV=1.1904, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=1.1904, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.6796, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.607, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_watch_liquidi 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
