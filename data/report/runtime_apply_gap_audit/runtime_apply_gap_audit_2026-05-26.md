# Runtime Apply Gap Audit - 2026-05-26

- 상태: `fail`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `13`
- 실패 표면화: `2`
- 재시도 큐: `1`
- Codex 작업지시: `3`
- source dimension gap: `3` / actionable=`2`
- quiet gap: `4` / rollup=`4` / directive=`1`

## 공격적 런타임 추진 대상
- `entry_wait6579_score66_69_recovery_gate_v1:2026-05-26`: stage=entry, EV=2.3066, 방향=runtime_bridge, 현재=post_apply_attribution_pending
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:time_bucket:time_unknown`: stage=entry, EV=3.3661, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=2.7821, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o`: stage=entry, EV=3.9731, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=2.3066, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.4885, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.4885, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5589, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.8918, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:scalping_pyramid_ok`: stage=scale_in, EV=2.448, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stage_policy:entry_weighted_adm_v1`: stage=entry, EV=2.28, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- `greenfield_policy_file_missing`: owner=runtime_apply_bridge, stage=runtime_apply_bridge, deadline=immediate_same_date_postclose_rerun

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: entry:time_bucket:time_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown_o 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
