# 2026-04-13 Stage 2 To-Do Checklist

## 목적

- 최종 목적은 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
- `2026-04-10` 장후 결론을 실제 다음 영업일 운영으로 연결한다.
- 실전 반영은 `한 번에 한 축 canary`, `원격 선행 적용 우선`, `즉시 롤백 가능` 원칙을 유지한다.

## 전일(2026-04-10) 핵심 요약

- 로컬 실현손익: `-10,885원`, `completed=6`, `win/loss=2/4`
- BUY 후 미진입 기회비용: `evaluated=21`, `MISSED_WINNER=17`, `estimated_counterfactual_pnl_10m_krw_sum=24,960`
- 최종 결론:
  - `RELAX-LATENCY`: `강화`
  - `RELAX-DYNSTR`: `유지`
  - `RELAX-OVERBOUGHT`: `유지`
- 원격 참고:
  - `remote_v2`는 `2026-04-10 14:35 KST`에 반영돼 관찰 시간은 짧았음
  - `16:00` 자동 수집은 `pipeline_events jsonl file changed as we read it`로 실패
- 관찰 기간 결론:
  - `2026-04-10` 장후에 1차 결론은 이미 확정됐다.
  - `2026-04-13~2026-04-14`는 `RELAX-LATENCY` 원격 강화 관찰의 연장 구간이며, `RELAX-DYNSTR/RELAX-OVERBOUGHT`는 기본적으로 재오픈하지 않는다.

## 다음 영업일 우선순위

| 우선순위 | 항목 | 방향 | 완료 기준 |
| --- | --- | --- | --- |
| `1` | `RELAX-LATENCY` | 원격 우선 강화 관찰 | `quote_stale=False` 축에서 `submitted/holding_started` 전환 또는 `missed_winner` 개선 근거 확보 |
| `2` | `RELAX-DYNSTR` | 현행 유지 + 재설계 | `below_window_buy_value`를 `momentum_tag/threshold_profile`별로 재분해 |
| `3` | `RELAX-OVERBOUGHT` | 유지 | 표본 추가 전 실전 완화 금지 유지 |
| `4` | 원격 수집 안정화 | 운영 보강 | `fetch_remote_scalping_logs`가 장중 갱신 파일에도 실패 없이 동작 |
| `5` | 리포트 정합성 + 체결 품질 | 복원 품질 보강 | `trade_review`에서 `entry_mode/fill quality` 해석 왜곡이 줄고 `preset_exit_sync_mismatch`를 따로 볼 수 있음 |
| `6` | AI-필터 중복 감사 | 분석 선행 | `AI 입력 피처 vs dynamic strength/overbought` 중복 여부를 리포트로 설명 가능 |
| `7` | 원격 latency 프로파일링 | 관측 선행 | `quote_stale=False latency_block` hot path 후보를 1~3개 설명 가능 |
| `8` | live hard stop taxonomy audit | 청산 구조 감사 | `shadow-only/common/live stop` 구분을 문서/리포트로 설명 가능 |

## 코딩작업지시 연계

- 판정:
  - `지금 즉시 전부 구현`이 아니다.
  - `2026-04-13` 체크리스트는 `운영/관측 실행표`이고, `AI 코딩 작업지시서`는 그 체크리스트를 성립시키기 위한 `개발 백로그`다.
- 지금 착수 대상:
  - `Phase 0`
  - `Phase 1`
  - 이유:
    - `4/13` 체크리스트의 `latency reason breakdown`, `expired_armed`, `partial fill sync`, `AI overlap audit`, `hard stop taxonomy audit`는 코드 계측/리포트가 있어야 실제로 점검 가능하다.
- 아직 보류 대상:
  - `Phase 2` 실전 로직 변경
  - `Phase 3` 분석 고도화 중 비필수 항목
  - 이유:
    - `4/13`은 우선 `관측/감사`를 완료해 다음 완화 판단의 근거를 쌓는 날이다.
    - 실전 변경은 `원격 1축 canary` 조건이 명확해진 뒤에만 진행한다.
- 실행 순서:
  1. `Phase 0` 계측 보강
  2. `Phase 1` 리포트 집계 반영
  3. `2026-04-13` 장중/장후 관측 수행
  4. 그 결과로 `Phase 2` 착수 여부 판정

## 구현 반영 상태 (2026-04-10)

- `Phase 0/1` 코드 기반 항목(계측/리포트 집계)을 본서버 코드베이스에 반영 완료.
- 동일 변경을 원격 `songstockscan` 코드베이스에도 반영 완료.
- 원격 `bot_main.py`는 `tmux bot` 세션으로 재기동해 상주 실행 상태 확인.
- 원격 `gunicorn`은 `HUP reload`로 워커 재적재 완료.
- `0-1b 원격 경량 프로파일링`은 별도 작업으로 남아 있음.

## Phase 0-1b 수행시간 고정 (2026-04-13, KST)

- `08:20~08:35` 장전 baseline 1차 수집
  - 목적: 장 시작 전 `budget_pass -> latency_block` 직전 경로의 기준 지연값 확보
- `10:20~10:35` 장중 1차 수집
  - 목적: 오전 변동성 구간의 `quote_stale=False latency_block` hot path 후보 관측
- `13:20~13:35` 장중 2차 수집
  - 목적: 점심 이후 유동성 변화 구간 재측정 및 오전 결과와 비교
- `15:35~15:50` 장후 정리/확정
  - 목적: `hot path 후보 1~3개`를 문서화하고 다음 액션으로 연결

## 장전 체크리스트 (08:00~09:00)

- [ ] 원격 `latency remote_v2` 설정 유지 상태 확인
- [ ] `fetch_remote_scalping_logs` 보강안 적용 여부 결정
- [ ] `RELAX-LATENCY / RELAX-DYNSTR / RELAX-OVERBOUGHT` 시작 상태를 체크리스트에 고정
- [x] `AI 코딩 작업지시서` 기준 `Phase 0 / Phase 1` 선반영 범위 확정
- [x] `latency reason breakdown / expired_armed / partial fill sync` 계측 반영 여부 확인
- [ ] 원격 경량 프로파일링 실행 여부 및 방식(`표준 도구만`) 결정 (`08:00~08:10`)
- [ ] 원격 경량 프로파일링 장전 baseline 1차 수집 (`08:20~08:35`)
- [ ] `buy_pause_guard`, `run_monitor_snapshot`, 원격 fetch cron 상태 확인

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-LATENCY` 관찰
  - `AI BUY -> entry_armed -> budget_pass -> submitted` 전환율 추적
  - `quote_stale=False latency_block` 표본 우선 기록
  - `expired_armed`와 `latency_block`을 분리 기록
  - `remote_v2 vs local` 퍼널/체결 품질 차이를 함께 기록
  - 원격 우선, 본서버는 결과 확인 전 전역 완화 금지
- [ ] `RELAX-DYNSTR` 관찰
  - `below_window_buy_value` / `below_buy_ratio` / `below_strength_base`를 분리 기록
  - `momentum_tag`, `threshold_profile`, `canary_applied`를 같이 묶어 본다
  - `AI 입력 피처와 중복되는 차단인지` 감사 메모를 남긴다
- [ ] `RELAX-OVERBOUGHT` 관찰
  - `blocked_overbought` 표본만 누적
  - missed-winner 여부를 장후까지 분리 보존
- [ ] 체결 품질 관찰
  - `full fill / partial fill`을 분리 기록
  - `preset_exit_sync_mismatch` 여부를 같이 본다
- [ ] 미결 이월건 추적
  - `스윙 Gatekeeper missed case` 표본 `N>=5` 계속 누적
  - `hard time stop shadow` 영향 메모
  - `live hard stop` 계열(`preset/protect/scalp_hard_stop`) 분기 확인 메모
  - `스캘핑 -> 스윙 자동전환` shadow 조건 초안 정리
- [ ] 원격 경량 프로파일링 장중 1차 수집 (`10:20~10:35`)
- [ ] 원격 경량 프로파일링 장중 2차 수집 (`13:20~13:35`)

## 장후 체크리스트 (15:30~)

- [ ] `RELAX-LATENCY` 원격 결과 기준 `유지/강화/축소/롤백` 재판정
- [ ] `RELAX-DYNSTR` 재설계 후보안 문서화
- [ ] `RELAX-OVERBOUGHT` 표본 누적 여부 재판정
- [ ] 원격 수집 안정화 패치 필요 시 작업지시서화
- [ ] 원격 경량 프로파일링 결과 정리 (`15:35~15:50`, hot path 후보 1~3개 확정)
- [ ] `live hard stop taxonomy audit` 결과 정리
- [ ] `2026-04-13` 결과를 다음 세션 플랜/체크리스트에 승격

## 이월 메모

- `trade_review` 해석은 여전히 `entry_mode/fill quality` 복원 품질을 함께 점검해야 한다.
- 원격 `remote_v2`는 실패 결론이 아니라 `표본 시간 부족` 상태로 읽는 것이 맞다.
- 다음 영업일에도 `latency`가 1순위, `dynamic strength`가 2순위, `overbought`는 보류 유지다.
- 다음 로직 완화 전에는 `latency reason`, `expired_armed`, `partial fill sync`, `AI overlap audit` 4개 감사축을 먼저 보강한다.

## 참고 문서

- [2026-04-10-scalping-expert-review-onepager.md](./2026-04-10-scalping-expert-review-onepager.md)
- [2026-04-10-scalping-review-validation.md](./2026-04-10-scalping-review-validation.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-10-scalping-expert-proposals-not-fit.md](./2026-04-10-scalping-expert-proposals-not-fit.md)
