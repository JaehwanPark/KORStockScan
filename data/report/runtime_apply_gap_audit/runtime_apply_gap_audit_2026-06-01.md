# Runtime Apply Gap Audit - 2026-06-01

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `38`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `4`
- source dimension gap: `150` / actionable=`5`
- quiet gap: `287` / rollup=`287` / directive=`1`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_belo`: stage=lifecycle_flow, EV=0.7064, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_bel`: stage=lifecycle_flow, EV=0.0499, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.1479, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.1479, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=1.5129, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=2.7847, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: stage=entry, EV=1.9222, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_63_65`: stage=entry, EV=0.9412, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.2473, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:chosen_action:wait_requote`: stage=entry, EV=2.1479, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=2.1479, 방향=runtime_bridge, 현재=code_patch_required
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=2.1479, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=2.3409, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_normal`: stage=entry, EV=2.1265, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_unknown`: stage=entry, EV=0.0984, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_watch`: stage=entry, EV=2.5485, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_chase_risk`: stage=entry, EV=2.644, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:weak_strength_momentum`: stage=entry, EV=0.9197, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=0.8926, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.6293, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_unknown_liquid 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: exit:exit_outcome:outcome_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
