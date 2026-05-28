# 2026-04-15 expired_armed 처리 로직 설계

> 작성시각: 2026-04-15 16:06 KST
> Source: `docs/checklists/2026-04-15-stage2-todo-checklist.md`
> Section: `장후 체크리스트 (15:30~) > expired_armed 처리 로직 설계 문서 작성 완료`

## 1) 판정

- `expired_armed`는 단일 종목(anchor) 해석이 아니라 전수 분포 기준으로 처리한다.
- `2026-04-15` 기준으로 즉시 재진입 완화는 보류하고, `entry_armed_expired_after_wait` 원인 분해를 먼저 고정한다.

## 2) 근거

- Entry pipeline 집계 (`2026-04-15`):
  - main: `expired_armed_total=374` (`entry_armed_expired_after_wait=332`, `entry_armed_expired=42`)
  - remote: `expired_armed_total=394` (`entry_armed_expired_after_wait=352`, `entry_armed_expired=42`)
- 운영 로그 코호트(`ENTRY_PIPELINE`):
  - `dynamic_reason=strong_absolute_override` 구간에서 `entry_armed_resume -> budget_pass` 반복 후 `entry_armed_expired_after_wait`로 종료되는 패턴 다수
  - 당일 `budget_pass_to_submitted_rate=0.0%`로, 만료 전환의 핵심 병목은 주문 제출 직전 단계에 있음
- anchor case:
  - `023160(태광)`은 anchor 유지 대상이지만, 의사결정 기준은 전수 분포 우선

## 3) 처리 설계

1. 분류 축 고정
   - `expired_stage`: `entry_armed_expired`, `entry_armed_expired_after_wait`
   - `dynamic_reason`: `strong_absolute_override`, `buy_value_override`, `momentum_ok`
   - `transition`: `entry_armed(_resume) -> budget_pass -> submitted(미도달)`
2. 재진입 정책
   - 오늘(`2026-04-15`)은 재진입 완화 없음
   - `submitted` 미도달 원인 계측(쿨다운/호가/주문가드) 없이는 완화 금지
3. 판정 조건(익일)
   - `entry_armed_expired_after_wait / tracked_stocks` 비율
   - `budget_pass_to_submitted_rate`
   - `dynamic_reason`별 만료 편중도

## 4) 2026-04-16 실행 입력값

- Due: `2026-04-16`
- Slot: `PREOPEN`
- TimeWindow: `08:25~08:45`
- 실행 항목:
  - `budget_pass_no_submit` 분해 로그 추가 여부 확인
  - `dynamic_reason`별 만료율 재계산
  - 완화/유지/보류 중 1개 판정

## 5) 검증 기록

- `build_entry_pipeline_flow_report('2026-04-15')` 실행 완료
- main/remote `expired_armed_breakdown` 수치 확인 완료
- 운영 로그(`pipeline_event_logger_info.log`)에서 `entry_armed_expired_after_wait` 코호트 샘플 확인 완료

