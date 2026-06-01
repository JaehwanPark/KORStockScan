# Runtime Apply Gap Audit - 2026-05-22

- 상태: `warning`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `8`
- 실패 표면화: `0`
- 재시도 큐: `1`
- Codex 작업지시: `2`
- source dimension gap: `1` / actionable=`1`
- quiet gap: `1` / rollup=`1` / directive=`1`

## 공격적 런타임 추진 대상
- `entry_wait6579_score66_69_recovery_gate_v1:2026-05-22`: stage=entry, EV=2.1843, 방향=runtime_bridge, 현재=post_apply_attribution_pending
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.3199, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.3199, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.6584, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_63_65`: stage=entry, EV=1.5141, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.3993, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.8673, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stage_policy:entry_weighted_adm_v1`: stage=entry, EV=0.3471, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- `ready_but_not_applied`: owner=preopen_apply_candidate, stage=preopen_apply_candidate, deadline=2026-05-23

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
