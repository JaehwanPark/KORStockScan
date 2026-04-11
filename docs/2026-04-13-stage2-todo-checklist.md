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
| `4` | 원격 수집 안정화 | 운영 보강 | `fetch_remote_scalping_logs`가 `live snapshot copy -> tar` 방식으로 장중 갱신 파일에도 재현 가능하게 동작 |
| `5` | 리포트 정합성 + 체결 품질 | 복원 품질 보강 | `trade_review`에서 `entry_mode/fill quality` 해석 왜곡이 줄고 `preset_exit_sync_mismatch`를 따로 볼 수 있음 |
| `6` | AI-필터 중복 감사 | 분석 선행 | `AI 입력 피처 vs dynamic strength/overbought` 중복 여부를 리포트로 설명 가능 |
| `7` | 원격 latency 프로파일링 | 관측 선행 | `quote_stale=False latency_block` hot path 후보를 1~3개 설명 가능 |
| `8` | live hard stop taxonomy audit | 청산 구조 감사 | `shadow-only/common/live stop` 구분을 문서/리포트로 설명 가능 |

## 코딩작업지시 연계

- 판정:
  - `지금 즉시 전부 구현`이 아니다.
  - `2026-04-13` 체크리스트는 `운영/관측 실행표`이고, `AI 코딩 작업지시서`는 그 체크리스트를 성립시키기 위한 `개발 백로그`다.
- 지금 착수 대상:
  - `fetch_remote_scalping_logs` 장중 수집 안정화
  - `0-1b 원격 경량 프로파일링` 수행 방식 고정
  - 이유:
    - `Phase 0/1` 본체는 이미 완료 상태다.
    - `4/13` 전 새로 고정해야 하는 것은 `원격 fetch 실패 재발 방지`와 `0-1b 수행 절차`다.
- 아직 보류 대상:
  - `Phase 2` 실전 로직 변경
  - `Phase 3` 분석 고도화 중 비필수 항목
  - 이유:
    - `4/13`은 우선 `관측/감사`를 완료해 다음 완화 판단의 근거를 쌓는 날이다.
    - 실전 변경은 `원격 1축 canary` 조건이 명확해진 뒤에만 진행한다.
- 실행 순서:
  1. `fetch_remote_scalping_logs` 안정화 패치 여부 결정
  2. `0-1b` 수행 주체/방식 고정
  3. `2026-04-13` 장중/장후 관측 수행
  4. 그 결과로 `Phase 2` 착수 여부 판정

## 구현 반영 상태 (2026-04-10)

- `Phase 0/1` 코드 기반 항목(계측/리포트 집계)을 본서버 코드베이스에 반영 완료.
- 동일 변경을 원격 `songstockscan` 코드베이스에도 반영 완료.
- 원격 `bot_main.py`는 `tmux bot` 세션으로 재기동해 상주 실행 상태 확인.
- 원격 `gunicorn`은 `HUP reload`로 워커 재적재 완료.
- `0-1b 원격 경량 프로파일링`은 별도 작업으로 남아 있음.
- `fetch_remote_scalping_logs`는 현재 live JSONL 직접 tar 방식이며, `2026-04-10 16:00` 실패 이력이 있어 장전 전 보강 여부를 확정해야 함.

## Phase 0-1b 수행시간 고정 (2026-04-13, KST)

- `08:20~08:35` 장전 baseline 1차 수집
  - 목적: 장 시작 전 `budget_pass -> latency_block` 직전 경로의 기준 지연값 확보
- `10:20~10:35` 장중 1차 수집
  - 목적: 오전 변동성 구간의 `quote_stale=False latency_block` hot path 후보 관측
- `13:20~13:35` 장중 2차 수집
  - 목적: 점심 이후 유동성 변화 구간 재측정 및 오전 결과와 비교
- `15:35~15:50` 장후 정리/확정
  - 목적: `hot path 후보 1~3개`를 문서화하고 다음 액션으로 연결

## `0-1b` / 원격 수집 트리거, 수행주체, 수행방식

### A. `0-1b 원격 경량 프로파일링`

- 트리거:
  - `2026-04-13`에는 `RELAX-LATENCY` canary가 계속 활성 상태이고 `quote_stale=False latency_block`의 hot path가 아직 미확정이므로 장전부터 **고정 수행**한다.
  - 장중에는 아래 중 하나가 보이면 정해진 시간 외 추가 1회 수행을 허용한다.
    - `quote_stale=False latency_block` 반복 누적
    - `budget_pass`는 누적되는데 `submitted` 전환이 거의 없음
    - 운영자가 `fresh quote인데 DANGER` 대표 표본 2~3건 이상 확보
- 수행주체:
  - 트리거 판정: 시스템운영자
  - 실제 실행: 원격 접근 권한이 있는 개발자 또는 운영자
  - 장후 해석: 운영자 + 전략 검토 담당
- 수행방식:
  - `songstockscan` 원격 서버에서만 수행
  - 패키지 설치 없이 `OS 기본 sampling + 기존 pipeline event` 상관관계로 1차 운영
  - `08:20~08:35`, `10:20~10:35`, `13:20~13:35` 3회 고정
  - `4/13` 장후에도 hot path 후보 설명이 부족하면 그때만 경량 instrumentation 코드 추가 여부를 재판정

### B. `fetch_remote_scalping_logs` 대응

- 트리거:
  - `2026-04-10 16:00` 자동 수집이 `file changed as we read it`로 실패했으므로, `2026-04-13` 장전 전에 **대응 방식 확정이 필수**다.
  - 장중/장후 수집에서 아래가 나오면 fallback 절차를 즉시 사용한다.
    - `file changed as we read it`
    - remote tar non-zero exit
    - live JSONL copy 실패
- 수행주체:
  - 구현 결정: 시스템운영자
  - 코드 보강: 개발자/Codex
  - 실제 실행: cron 또는 수동 실행 담당 운영자
- 수행방식:
  - 기본 경로는 `live snapshot copy -> tar`
  - optional snapshot JSON은 계속 `if exist` 방식 유지
  - live copy가 다시 실패하면 최소 `trade_review / performance_tuning / post_sell_feedback` snapshot은 회수

### 관련 작업지시서

- [2026-04-11-remote-profiling-fetch-ai-coding-instructions.md](./2026-04-11-remote-profiling-fetch-ai-coding-instructions.md)

## 장전 체크리스트 (08:00~09:00)

- [ ] 원격 `latency remote_v2` 설정 유지 상태 확인
- [ ] `fetch_remote_scalping_logs`를 `live snapshot copy -> tar` 방식으로 보강할지 장전 전 최종 결정
- [ ] `GitHub Project -> Google Calendar` 동기화 워크플로우 마지막 실행 상태 확인
- [ ] `Sync Docs Backlog To GitHub Project` 워크플로우 마지막 실행 상태 확인
- [ ] `RELAX-LATENCY / RELAX-DYNSTR / RELAX-OVERBOUGHT` 시작 상태를 체크리스트에 고정
- [x] `AI 코딩 작업지시서` 기준 `Phase 0 / Phase 1` 선반영 범위 확정
- [x] `latency reason breakdown / expired_armed / partial fill sync` 계측 반영 여부 확인
- [ ] `0-1b 원격 경량 프로파일링` 수행 주체와 표준 절차(`OS 기본 sampling 우선`) 고정 (`08:00~08:10`)
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
- [ ] 원격 수집 안정화 패치 필요 시 `partial_snapshot_only` fallback까지 포함해 재작업지시
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
- [2026-04-11-remote-profiling-fetch-ai-coding-instructions.md](./2026-04-11-remote-profiling-fetch-ai-coding-instructions.md)
- [2026-04-10-scalping-expert-proposals-not-fit.md](./2026-04-10-scalping-expert-proposals-not-fit.md)
