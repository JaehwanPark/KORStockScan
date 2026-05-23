# Runtime Apply Gap Audit - 2026-05-22

- 상태: `warning`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `10`
- 실패 표면화: `0`
- 재시도 큐: `1`
- Codex 작업지시: `0`

## 공격적 런타임 추진 대상
- `entry_wait6579_score66_69_recovery_gate_v1:2026-05-22`: stage=entry, EV=2.1843, 방향=runtime_bridge, 현재=post_apply_attribution_pending
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.3199, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.3199, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.6584, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_63_65`: stage=entry, EV=1.5141, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.3993, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.8673, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stage_policy:entry_weighted_adm_v1`: stage=entry, EV=0.3471, 방향=runtime_bridge, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_green_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=18.57446, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_mae_low_held_missing_trailing_after_mfe_stop`: stage=unknown, EV=10.952632, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- `ready_but_not_applied`: owner=preopen_apply_candidate, stage=preopen_apply_candidate, deadline=2026-05-23

## Codex 작업지시
- 신규 작업지시 없음

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
