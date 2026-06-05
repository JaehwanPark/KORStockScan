# Runtime Apply Gap Audit - 2026-06-05

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `10`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `0`
- source dimension gap: `46` / actionable=`0`
- quiet gap: `199` / rollup=`199` / directive=`0`

## 공격적 런타임 추진 대상
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.0921, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.0921, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:chosen_action:wait_requote`: stage=entry, EV=2.0921, 방향=runtime_bridge, 현재=code_patch_required
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=2.0921, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=0.8406, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=1.8817, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:weak_strength_momentum`: stage=entry, EV=2.7167, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.5453, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.5453, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.543, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- 신규 작업지시 없음

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
