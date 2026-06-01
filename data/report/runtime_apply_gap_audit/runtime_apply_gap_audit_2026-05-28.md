# Runtime Apply Gap Audit - 2026-05-28

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `7`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `3`
- source dimension gap: `61` / actionable=`46`
- quiet gap: `3` / rollup=`3` / directive=`1`

## 공격적 런타임 추진 대상
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu`: stage=lifecycle_flow, EV=2.2548, 방향=sim_policy_or_approval_ready, 현재=runtime_blocked_contract_gap
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.55, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq`: stage=lifecycle_flow, EV=0.0765, 방향=sim_policy_or_approval_ready, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5982, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.7926, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq 후보가 resolve_unknown_source_dimensions 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
