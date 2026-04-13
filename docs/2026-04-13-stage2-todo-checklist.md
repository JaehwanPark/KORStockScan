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
- `08:05~08:10` shadow canary preopen readiness check
  - 목적: `tmux bot`, `shadow env`, `07:40` 기동 상태를 장초반 전에 확인
- `09:05~09:10` shadow canary open collection check
  - 목적: `pipeline_events`가 실제로 갱신되고 있는지, `ENTRY_PIPELINE`/`ai_confirmed`가 들어오는지 확인
- `10:20~10:35` 장중 1차 수집
  - 목적: 오전 변동성 구간의 `quote_stale=False latency_block` hot path 후보 관측
- `13:20~13:35` 장중 2차 수집
  - 목적: 점심 이후 유동성 변화 구간 재측정 및 오전 결과와 비교
- `15:45~16:00` shadow fetch/report
  - 목적: 원격 fetch + `buy_diverged / 75~79 / missed_winner` 교차표 산출
- `15:35~15:50` 장후 정리/확정
  - 목적: `hot path 후보 1~3개`를 문서화하고 다음 액션으로 연결

## 작업 4 shadow canary 점검 명령세트

### 수동 실행

1. 장전 readiness (`08:05~08:10`)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary \
  --date 2026-04-13 \
  --phase preopen
```

2. 장초반 수집 확인 (`09:05~09:10`)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary \
  --date 2026-04-13 \
  --phase open_check
```

3. 오전 shadow fetch/report (`10:20~10:35`)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary \
  --date 2026-04-13 \
  --phase midmorning
```

4. 장후 fetch/report (`15:45~16:00`)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary \
  --date 2026-04-13 \
  --phase postclose
```

5. 원격 fetch 산출물 기준 shadow 집계

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.watching_prompt_75_shadow_report \
  --date 2026-04-13 \
  --data-dir tmp/remote_2026-04-13/data \
  --json-output tmp/watching_prompt_75_shadow_2026-04-13.json \
  --markdown-output tmp/watching_prompt_75_shadow_2026-04-13.md
```

### 자동 실행 권장 시간

- `08:05` `preopen`
- `09:05` `open_check`
- `10:25` `midmorning`
- `15:45` `postclose`

### 자동 실행용 cron 예시

```bash
5 8 * * 1-5 cd /home/ubuntu/KORStockScan && PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary --date $(date +\\%F) --phase preopen >> logs/shadow_canary_check.log 2>&1
5 9 * * 1-5 cd /home/ubuntu/KORStockScan && PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary --date $(date +\\%F) --phase open_check >> logs/shadow_canary_check.log 2>&1
25 10 * * 1-5 cd /home/ubuntu/KORStockScan && PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary --date $(date +\\%F) --phase midmorning >> logs/shadow_canary_check.log 2>&1
45 15 * * 1-5 cd /home/ubuntu/KORStockScan && PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.check_watching_prompt_75_shadow_canary --date $(date +\\%F) --phase postclose >> logs/shadow_canary_check.log 2>&1
```

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

- [x] 원격 `latency remote_v2` 설정 유지 상태 확인
  - `2026-04-13 08:01 KST` 원격 `run_bot.sh`를 재기동해 `bot_main.py` PID `1151319`의 `/proc/<pid>/environ`에서 `KORSTOCKSCAN_LATENCY_CANARY_PROFILE=remote_v2`, `...MAX_WS_JITTER_MS=400`를 직접 확인.
- [x] `fetch_remote_scalping_logs`를 `live snapshot copy -> tar` 방식으로 보강할지 장전 전 최종 결정
  - `src/engine/fetch_remote_scalping_logs.py`는 이미 원격 `mktemp -d -> cp -p snapshot -> tar` 구조와 `snapshot_only_on_live_failure` fallback을 사용한다.
- [x] `GitHub Project -> Google Calendar` 동기화 워크플로우 마지막 실행 상태 확인
  - GitHub Actions API 기준 마지막 실행 `run_number=53`, `2026-04-13 08:02:51 KST`, `conclusion=success`, `head_sha=433e0408b2bab5ef054cd522f622af6486b4d823`.
- [x] `Sync Docs Backlog To GitHub Project` 워크플로우 마지막 실행 상태 확인
  - GitHub Actions API 기준 마지막 실행 `run_number=29`, `2026-04-13 04:08:25 KST`, `conclusion=success`, `head_sha=433e0408b2bab5ef054cd522f622af6486b4d823`.
- [x] `RELAX-LATENCY / RELAX-DYNSTR / RELAX-OVERBOUGHT` 시작 상태를 체크리스트에 고정
  - 상단 `전일(2026-04-10) 핵심 요약`에 `RELAX-LATENCY=강화`, `RELAX-DYNSTR=유지`, `RELAX-OVERBOUGHT=유지`를 고정했다.
- [x] `AI 코딩 작업지시서` 기준 `Phase 0 / Phase 1` 선반영 범위 확정
- [x] `latency reason breakdown / expired_armed / partial fill sync` 계측 반영 여부 확인
- [x] `0-1b 원격 경량 프로파일링` 수행 주체와 표준 절차(`OS 기본 sampling 우선`) 고정 (`08:00~08:10`)
  - `docs/2026-04-11-remote-profiling-fetch-ai-coding-instructions.md`에 수행 주체/윈도우/명령 기준을 고정했고, `src/engine/collect_remote_latency_baseline.py` + `deploy/run_remote_latency_baseline.sh`를 추가했다.
- [x] 원격 경량 프로파일링 장전 baseline 1차 수집 (`08:20~08:35`)
  - `2026-04-13 08:20:01 KST` local cron `REMOTE_LATENCY_BASELINE_PREOPEN` 실행 확인.
  - 산출물: `tmp/remote_latency_baseline/2026-04-13/2026-04-13_preopen_20260413_082001.json`, `...082001.md`
  - 결과: `status=ok`, `bot_running=true`, `bot_pid=1151319`, `pipeline_exists=false`, `pipeline_line_count=0`
- [x] `buy_pause_guard`, `run_monitor_snapshot`, 원격 fetch cron 상태 확인
  - local cron: `buy_pause_guard` 기존 유지 확인.
  - local cron 추가: `RUN_MONITOR_SNAPSHOT_1000`, `RUN_MONITOR_SNAPSHOT_1200`, `REMOTE_SCALPING_FETCH_1600`.
  - 원격 crontab에는 동일 잡이 없고, 표준 경로는 local cron -> SSH fetch로 고정한다.
  - smoke 실행 확인: `./deploy/run_monitor_snapshot_cron.sh 2026-04-13`, `./deploy/fetch_remote_scalping_logs_cron.sh 2026-04-10` 성공.

### 2026-04-13 08:02 장전 점검 메모

- 원격 bot: `08:01` 재기동 후 `tmux bot` 세션/`bot_main.py` PID `1151319` 활성.
- 원격 canary env: `/proc/1151319/environ`에서 `remote_v2`, `MAX_WS_JITTER_MS=400`, `AI_WATCHING_75_PROMPT_SHADOW_ENABLED=true`, `MIN=75`, `MAX=79` 확인.
- 장전 baseline smoke: [2026-04-13_preopen_20260413_080230.json](/home/ubuntu/KORStockScan/tmp/remote_latency_baseline/2026-04-13/2026-04-13_preopen_20260413_080230.json), [2026-04-13_preopen_20260413_080230.md](/home/ubuntu/KORStockScan/tmp/remote_latency_baseline/2026-04-13/2026-04-13_preopen_20260413_080230.md)
- 장전 baseline 자동 실행 결과: [2026-04-13_preopen_20260413_082001.json](/home/ubuntu/KORStockScan/tmp/remote_latency_baseline/2026-04-13/2026-04-13_preopen_20260413_082001.json), [2026-04-13_preopen_20260413_082001.md](/home/ubuntu/KORStockScan/tmp/remote_latency_baseline/2026-04-13/2026-04-13_preopen_20260413_082001.md)
- 현재 시각 기준 `pipeline_events_2026-04-13.jsonl`은 아직 생성 전이며, 장전 상태로는 정상이다.
- snapshot/fetch wrapper smoke:
  - `run_monitor_snapshot`: `2026-04-13` snapshot JSON 5종 + `server_comparison_2026-04-13.md` 생성 확인
  - `fetch_remote_scalping_logs`: `2026-04-10` 기준 `[REMOTE_FETCH] ... status=ok` 확인
- GitHub Actions 확인:
  - `Sync Docs Backlog To GitHub Project`: `2026-04-13 04:08:25 KST` `success`
  - `GitHub Project -> Google Calendar`: `2026-04-13 08:02:51 KST` `success`

## 장중 체크리스트 (09:00~15:30)

- 운영 원칙:
  - `원격 경량 프로파일링 장중 1차/2차 수집`처럼 1회성 완료 작업만 즉시 `- [x]`로 닫는다.
  - `RELAX-LATENCY / RELAX-DYNSTR / RELAX-OVERBOUGHT / 체결 품질 / 미결 이월건 추적`은 장후 종합판정 전까지 관찰형 작업으로 보고 `- [ ]`를 유지한다.

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
- [x] 원격 경량 프로파일링 장중 1차 수집 (`10:20~10:35`)
- [x] 원격 경량 프로파일링 장중 2차 수집 (`13:20~13:35`)

### 2026-04-13 10:03 KST 장중 중간 점검 메모

- `GitHub Project -> Google Calendar` 마지막 실행 상태:
  - 장전 점검에서 이미 확인 완료.
  - GitHub Actions API 기준 마지막 실행 `run_number=53`, `2026-04-13 08:02:51 KST`, `conclusion=success`.
- `RELAX-LATENCY` 관찰:
  - `data/report/server_comparison/server_comparison_2026-04-13.md` 기준 `submitted_stocks=0`, `blocked_stocks local/remote = 29/30`.
  - `ENTRY_PIPELINE`에는 `entry_armed`, `entry_armed_resume`, `entry_armed_expired_after_wait`가 반복 기록되고 있으나 `submitted/holding_started` 전환은 아직 확인되지 않았다.
  - 따라서 현재 시점 판정은 `강화 유지 관찰 계속`, `quote_stale=False latency_block hot path`는 `10:20` 1차 수집 이후 재점검이 맞다.
- `RELAX-DYNSTR` 관찰:
  - `ENTRY_PIPELINE strength_momentum_observed / blocked_strength_momentum`에서 `below_window_buy_value`, `below_buy_ratio`, `below_strength_base` 3유형이 모두 확인됐다.
  - 각 표본에 `momentum_tag=SCANNER`, `threshold_profile=default`가 함께 남아 재분해 가능한 상태다.
- `RELAX-OVERBOUGHT` 관찰:
  - `server_comparison_2026-04-13.md` 기준 local/remote 모두 `blocked_overbought count=18`.
  - 오전 표본만으로도 과열 차단은 충분히 누적되고 있어 지금 단계에서 실전 완화 재오픈은 부적절하다.
- 체결 품질 관찰:
  - 현재 시점 `submitted/holding_started`가 없어 `full fill / partial fill` 평가는 유보.
  - 대신 `entry_armed -> expired_after_wait` 반복은 누적 중이며, 장후에는 latency/quote 품질과 함께 봐야 한다.
- 미결 이월건 추적:
  - `태광(023160)`에서 `entry_armed`와 `entry_armed_expired_after_wait` 반복이 확인돼 `미체결 이월/소진` 관찰 포인트로 유지한다.
  - `live hard stop` 계열은 현재 시점 검색 표본 없음.
- 시간 조건:
  - `원격 경량 프로파일링 장중 1차 수집 (10:20~10:35)`은 `2026-04-13 10:20:02 KST` cron 자동 실행으로 완료.
  - `원격 경량 프로파일링 장중 2차 수집 (13:20~13:35)`도 아직 시작 전이라 미착수 유지.

### 2026-04-13 10:20 KST 장중 1차 프로파일링 메모

- 산출물:
  - `tmp/remote_latency_baseline/2026-04-13/2026-04-13_midmorning_20260413_102002.json`
  - `tmp/remote_latency_baseline/2026-04-13/2026-04-13_midmorning_20260413_102002.md`
- 결과 요약:
  - `status=ok`
  - `bot_running=true`
  - `bot_pid=1159650`
  - `pipeline_exists=true`
  - `pipeline_line_count=78390`
  - `latency_block_rows=308`
  - `latest_event_at=2026-04-13T10:20:04.116052`
- 해석:
  - 원격 `remote_v2` 관측 경로와 shadow env는 장중에도 정상 유지되고 있다.
  - `quote_stale=False latency_block` hot path 설명은 장후에 `midmorning`/`13:20` 결과를 합쳐 최종 정리한다.

### 2026-04-13 10:43 KST WATCHING 75 shadow 중간집계

- 집계 명령:
  - `PYTHONPATH=. .venv/bin/python -m src.engine.watching_prompt_75_shadow_report --date 2026-04-13 --data-dir data --json-output tmp/watching_prompt_75_shadow_2026-04-13.json --markdown-output tmp/watching_prompt_75_shadow_2026-04-13.md`
- 결과:
  - `shadow_samples=0`
  - `buy_diverged_count=0`
  - 최근 3일 `eligible_shadow(75~79, non-BUY, non-fallback)`는 `2026-04-09=0`, `2026-04-10=1`, `2026-04-13=0`
- 추가 해석:
  - `WAIT 65`는 최근 3일 총 `286건`이며 `missed_entry_counterfactual`에 붙은 `85건` 중 `MISSED_WINNER=62`, `AVOIDED_LOSER=20`, `NEUTRAL=3`이다.
  - 오늘 `fallback50` `4건`은 모두 `ai_result_source=cooldown`이라 파싱 실패보다 쿨다운 경로로 봐야 한다.
  - 현재 판정은 `shadow band 즉시 하향 보류`, `작업 5 보류 유지`, `13:20/장후에 표본 재확인`이다.

### 2026-04-13 10:49 KST WAIT 65 blocker 교차집계

- 산출물:
  - `tmp/wait65_blocker_crosstab_2026-04-13.json`
- 최근 3일 `WAIT 65` 총 `288건`, counterfactual join `85건`
- `terminal_stage x outcome`
  - `latency_block`: `MISSED_WINNER=50`, `AVOIDED_LOSER=20`, `NEUTRAL=2`
  - `blocked_strength_momentum`: `MISSED_WINNER=11`, `NEUTRAL=1`
  - `blocked_liquidity`: `MISSED_WINNER=1`
- `blocked_overbought x outcome`
  - 전 표본 `False`
  - 즉 현재 `WAIT 65` missed-winner 묶음은 `overbought gate miss`보다 `latency/strength` 축으로 읽는 것이 맞다.
- 해석:
  - `WAIT 65`는 단순 AI threshold miss라기보다 `latency_block`과 `strength_momentum` blocker에 더 강하게 묶인다.
  - 다음 우선순위는 `shadow band 하향`보다 `WAIT 65 + latency_block`, `WAIT 65 + blocked_strength_momentum` 분해다.

### 2026-04-13 11:02 KST latency canary 개선 패치

- 목적:
  - `quote_stale=False` 중심 latency canary를 전면 완화가 아니라 더 좁고 해석 가능하게 유지
- 코드 반영:
  - `src/engine/sniper_entry_latency.py`
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_entry_pipeline_report.py`
  - `src/engine/sniper_performance_tuning_report.py`
  - `src/utils/constants.py`
- 핵심 변경:
  - `latency_state_danger`를 `quote_stale / ws_age_too_high / ws_jitter_too_high / spread_too_wide / other_danger`로 분해해 로그에 남긴다.
  - `KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS` env로 canary를 특정 danger reason에만 허용할 수 있게 했다.
  - `latency_block`/`latency_pass` 이벤트에 `latency_danger_reasons`를 함께 남기고, 리포트 breakdown에도 추가했다.
- 테스트:
  - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py src/tests/test_constants.py`
  - 결과 `11 passed`

### 2026-04-13 12:51 KST 장중 재판정 메모

- 시간 조건:
  - 현재 시각 `12:51 KST`
  - `원격 경량 프로파일링 장중 2차 수집 (13:20~13:35)`은 아직 시작 전이므로 미착수 유지
- `RELAX-LATENCY` 관찰:
  - `server_comparison_2026-04-13.md` 기준 local/remote 모두 `submitted_stocks=0`
  - raw `ENTRY_PIPELINE`에서는 `latency_danger_reasons`가 실제로 누적 중이다.
  - 현재 분포는 `ws_jitter_too_high=181`, `other_danger=151`, `ws_age_too_high=126`, `spread_too_wide=93`, `quote_stale=88`
  - 따라서 현 시점 판정은 `전면 완화 금지`, `quote_stale=False latency canary 해석 강화 계속`이 맞다.
- `RELAX-DYNSTR` 관찰:
  - 오전과 동일하게 `blocked_strength_momentum`은 주요 2순위 blocker로 유지된다.
  - 다음 재분해 축은 `below_window_buy_value / below_buy_ratio / below_strength_base` 3개로 고정한다.
- `RELAX-OVERBOUGHT` 관찰:
  - `server_comparison_2026-04-13.md` latest stage 기준 `blocked_overbought=20`
  - raw 이벤트는 장중 내내 반복 누적되며, 현재도 과열 차단이 강하게 유지된다.
  - 따라서 장중 재오픈 근거는 없다.
- 체결 품질 관찰:
  - `server_comparison_2026-04-13.md` 기준 `entered_rows=1`, `completed_trades=1`, `holding_events=0`
  - `submitted/holding_started` 신규 전환은 없어 `full fill / partial fill` 평가는 계속 유보다.
- 미결 이월건 추적:
  - `entry_armed_expired_after_wait` 상위 종목은 `세미파이브 26`, `태광 18`, `레이크머티리얼즈 5`, `코세스 4`다.
  - `태광`은 계속 핵심 추적 대상으로 유지한다.
  - `hard stop / protect / preset` 계열 관련 표본은 현재 시점에도 검색되지 않았다.

### 2026-04-13 13:39 KST 장중 후속 관찰 메모

- 시간 조건:
  - 현재 시각 `13:39 KST`
  - `원격 경량 프로파일링 장중 2차 수집 (13:20~13:35)` 완료 (`afternoon` window). 산출물: `tmp/remote_latency_baseline/2026-04-13/2026-04-13_afternoon_20260413_132002.json`, `...134211.json`
- `RELAX-LATENCY` 관찰:
  - `server_comparison_2026-04-13.md` 기준 `submitted_stocks=0` 유지.
  - `latency_danger_reasons` 분포: `ws_jitter_too_high`, `other_danger` 등 비슷한 패턴 유지.
  - `quote_stale=False latency canary` 해석 강화 계속 필요. 장후 hot path 후보 정리 예정.
- `RELAX-DYNSTR` 관찰:
  - `blocked_strength_momentum` 여전히 주요 blocker. `below_window_buy_value / below_buy_ratio / below_strength_base` 분해는 장후 재설계로 넘김.
- `RELAX-OVERBOUGHT` 관찰:
  - `blocked_overbought=20` 유지. 과열 차단 지속.
- 체결 품질 관찰:
  - `submitted/holding_started` 신규 전환 없음. `full fill / partial fill` 평가 유보.
- 미결 이월건 추적:
  - `entry_armed_expired_after_wait` 상위 종목 변동 없음. `태광` 계속 추적.
  - `hard stop / protect / preset` 계열 표본 없음.

## 장후 체크리스트 (15:30~)

- [ ] `RELAX-LATENCY` 원격 결과 기준 `유지/강화/축소/롤백` 재판정
- [ ] `RELAX-DYNSTR` 재설계 후보안 문서화
- [ ] `RELAX-OVERBOUGHT` 표본 누적 여부 재판정
- [ ] 원격 수집 안정화 패치 필요 시 `partial_snapshot_only` fallback까지 포함해 재작업지시
- [ ] 원격 경량 프로파일링 결과 정리 (`15:35~15:50`, hot path 후보 1~3개 확정)
- [ ] `post-sell` 지표 기준 `원격 1축 매도시점 canary` 후보안 작성 (`15:35~15:50`)
  - `estimated_extra_upside_10m_krw_sum`, `timing_tuning_pressure_score`, `exit_rule_tuning`, `tag_tuning`, `priority_actions`를 함께 검토한다.
  - 전면 청산 규칙 교체는 금지하고 `exit_rule` 또는 `position_tag` 기준 국소 미세조정안만 다음 세션 원격 canary 후보로 정리한다.
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

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-13 12:00:56`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-13.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`2`
  - all_rows local=106 remote=109 delta=3.0; expired_rows local=63 remote=65 delta=2.0
- `Performance Tuning`: status=`ok`, differing_safe_metrics=`10`
  - gatekeeper_eval_ms_avg local=12114.81 remote=13082.27 delta=967.46; gatekeeper_eval_ms_p95 local=24171.0 remote=23826.0 delta=-345.0; holding_review_ms_avg local=2315.06 remote=2080.6 delta=-234.46
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`3`
  - total_events local=258443 remote=260079 delta=1636.0; tracked_stocks local=101 remote=99 delta=-2.0; blocked_stocks local=28 remote=30 delta=2.0
<!-- AUTO_SERVER_COMPARISON_END -->
