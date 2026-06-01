# Runtime Apply Gap Audit - 2026-05-27

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `12`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `4`
- source dimension gap: `3` / actionable=`2`
- quiet gap: `3` / rollup=`3` / directive=`1`

## 공격적 런타임 추진 대상
- `entry_wait6579_score66_69_recovery_gate_v1:2026-05-27`: stage=entry, EV=1.5253, 방향=runtime_bridge, 현재=post_apply_attribution_pending
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.2594, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.2594, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:time_bucket:time_unknown`: stage=entry, EV=2.2594, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=2.4554, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o`: stage=entry, EV=2.6587, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.5253, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.3193, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.3193, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5044, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.6781, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stage_policy:entry_weighted_adm_v1`: stage=entry, EV=1.8842, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: entry:time_bucket:time_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: greenfield_real_environment_authority:2026-05-27 후보가 runtime_blocked_contract_gap 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
