# Runtime Apply Gap Audit - 2026-05-27

- 상태: `warning`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `17`
- 실패 표면화: `0`
- 재시도 큐: `2`
- Codex 작업지시: `0`

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
- `ready_but_not_applied`: owner=preopen_apply_candidate, stage=preopen_apply_candidate, deadline=2026-05-28
- `ready_but_not_applied`: owner=preopen_apply_candidate, stage=preopen_apply_candidate, deadline=2026-05-28

## Codex 작업지시
- 신규 작업지시 없음

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
