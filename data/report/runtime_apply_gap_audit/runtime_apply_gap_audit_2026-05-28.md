# Runtime Apply Gap Audit - 2026-05-28

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `16`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `0`

## 공격적 런타임 추진 대상
- `entry:exit_rule:exit_unknown`: stage=entry, EV=0.0432, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_proxy_normal`: stage=entry, EV=0.5168, 방향=runtime_bridge, 현재=code_patch_required
- `scale_in:arm:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_namespace:pyramid`: stage=scale_in, EV=0.7624, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:profit_not_enough`: stage=scale_in, EV=0.5982, 방향=runtime_bridge, 현재=sim_auto_approved
- `scale_in:blocker_reason:trend_not_strong`: stage=scale_in, EV=2.7926, 방향=runtime_bridge, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- 신규 작업지시 없음

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
