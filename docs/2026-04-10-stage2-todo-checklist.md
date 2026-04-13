# 2026-04-10 Stage 2 To-Do Checklist

## 목적

- 최종 목적은 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
- 현재 단계는 `1단계: 음수 leakage 제거 + 주문전 차단 병목 분해`다.
- `2026-04-09` 미완료건을 누락 없이 처리하고, 운영 반영은 `완화 우선순위`와 `필수 확인 게이트`를 통과한 항목만 수행한다.
- 전략별 운영 원칙(`2026-04-10 사용자 지시 반영`):
  - `스윙`: 충분한 표본/정밀 튜닝 이후 투입(관찰 우선, 성급한 실전 전환 금지).
  - `스캘핑`: 과감한 적용 + 빠른 피드백 중심으로 애자일 운영(단, `한 번에 한 축 canary`와 롤백 가드는 유지).

## 2026-04-09 미완료건 확인 후 처리

| 미완료 항목 (`2026-04-09`) | 현 상태 | `2026-04-10` 처리 방식 | 처리 시점 | 완료 기준 |
| --- | --- | --- | --- | --- |
| `curr`, `spread` 완화 후보 분석 기준 정리 | 미완료 | `WS2` 장전 선처리 | `08:00~08:25` | 집계축(`시간대/position_tag/entry_mode/종목군`)과 비교표 템플릿 확정 |
| canary 실시간 모니터링(`30~60분`) | 미완료 | 자동+수동 동시 유지 | `09:30~11:00` | `fallback 손익 + BUY후미진입 퍼널` 동시 기록 |
| 스윙 Gatekeeper missed case 표본 채집 | 미완료 | 이월 유지 | 장중/장후 | 표본 최소 `N>=5` 확보 또는 `데이터 부족` 명시 |
| `AI WAIT/latency` missed case 표본 채집 | 미완료 | 장중 우선 처리 | 장중 | 종목/사유(`WAIT`,`latency`,`liquidity`,`score`) 분리 표본화 |
| `AI BUY 후 미진입` 퍼널 차단 표본 채집 | 미완료 | 장중 우선 처리 | 장중 | `AI BUY -> entry_armed -> budget_pass -> blocked` 누적표 생성 |
| 공통 hard time stop 후보안 영향 추정 | 미완료 | 실전 미적용 유지 + 장후 분석 | 장후 | shadow 결과 기반 후보안 영향 메모 작성 |
| 스윙 missed case 요약 + threshold 완화 검토 | 미완료 | 이월 유지 | 장후 | `완화 보류/부분 canary/추가관찰` 중 1개 결론 |
| 스캘핑 진입종목의 스윙 자동전환 프레임 초안 | 미완료 | 이월 유지 | 장후 | shadow 전환 기준 초안 문서화 |
| 종일 유지 점검 11개 항목 | 체크 미완료 | 장전 재확인 후 종일 점검 | `08:30~09:00`, 장후 | 미적용 정책 위반 `0건` 기록 |

## 2026-04-10 장전 실행안 (08:00~09:00)

| 시간 | 작업 | 분류 | 필수 확인 | 산출물 |
| --- | --- | --- | --- | --- |
| `08:00~08:15` | 전일 장후 결론/실제 설정 일치 점검 | `WS3` | `trade_review`와 `buy_pause_guard` fallback cohort 일치 | 장전 상태 점검 메모 |
| `08:15~08:25` | `curr/spread` 분석축 확정 | `WS2` | 단일 손익으로 임계값 직접 완화 금지 | 분석 기준표(비교 템플릿) |
| `08:25~08:35` | 완화 우선순위 운영반영 후보 정리 | `WS5` | `latency > dynamic strength > overbought` 순서 고정 | 당일 후보안 패킷(최대 2안) |
| `08:35~08:45` | 미적용 정책 11개 재확인 | `가드레일` | `near_safe_profit/near_ai_exit` 직접 완화 금지 등 | 장전 체크 결과 |
| `08:45~08:55` | 모니터링/스냅샷/가드 준비 점검 | `WS4` | `10:00/12:00 snapshot`, `09:30~11:00 guard`, `16:00 remote fetch` | 운영 준비 완료 메모 |
| `08:55~09:00` | 장중 지시 트리거 재확인 | `운영` | `[자동]/[내 지시 필요]/[내 승인 필요]` 구분 확인 | 당일 실행 트리거 표 |

### 08:00~09:00 실행 로그 (조기 수행: `2026-04-10 02:04~02:09 KST`)

| 항목 | 실행 결과 | 상태 |
| --- | --- | --- |
| `08:00~08:15` 전일 결론/설정 일치 점검 | `run_monitor_snapshot --date 2026-04-10` 수동 실행 완료. `trade_review`/`buy_pause_guard` 모두 `completed_fallback_trades=0`, `sample_ready=false`, `paused=false` 확인 | `완료` |
| `08:15~08:25` `curr/spread` 분석축 확정 | 분석축을 `시간대/position_tag/entry_mode/종목군` + 결과축(`holding_skip_ratio`, `latency_block`, `blocked_strength_momentum`)으로 고정. 단일일 손익으로 임계값 직접 완화 금지 원칙 유지 | `완료` |
| `08:25~08:35` 완화 우선순위 운영반영 후보 정리 | `RELAX-LATENCY-20260410-V1`, `RELAX-DYNSTR-20260410-V1`, `RELAX-OVERBOUGHT-HOLD` 3개 추적 ID 기준으로 운영 | `완료` |
| `08:35~08:45` 미적용 정책 재확인 | `SCALP_SAFE_PROFIT=0.5`, `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=True`, `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER=False`, `SCALP_FALLBACK_ENTRY_QTY_MULTIPLIER=0.70` 확인. `overbought 완화`는 미적용 유지 | `완료` |
| `08:45~08:55` 모니터링/스냅샷/가드 준비 점검 | snapshot 파일 5종 생성 확인(`trade_review`, `performance_tuning`, `post_sell_feedback`, `missed_entry_counterfactual`, `server_comparison`). `buy_pause_guard status --json` 정상 | `완료` |
| `08:55~09:00` 장중 트리거 재확인 | cron 확인: `09:30~11:00 guard`, `10:00 snapshot`, `16:00 remote fetch` 등록됨. `12:00 snapshot` 1회 크론(`KOR_MONITOR_20260410_1200`) 추가 등록 | `완료` |

- 실행 명령 기록:
  - `PYTHONPATH=. .venv/bin/python -m src.engine.buy_pause_guard status --json`
  - `PYTHONPATH=. .venv/bin/python -m src.engine.run_monitor_snapshot --date 2026-04-10`
  - `crontab -l` 점검 및 `KOR_MONITOR_20260410_1200` 등록

## 완화 우선순위 운영 반영 필요사항 (필수 확인)

| 우선순위 | 축 | 오늘 원칙 | 운영 반영 전 필수 확인 | 차단 조건 |
| --- | --- | --- | --- | --- |
| `1` | `latency guard` | 조건부 완화안 `1~2개`만 검토 | 전역 완화 금지, `quote_stale=True` 제외, 분포 기반 조건 명시 | 조건 불명확/전역 완화이면 반영 금지 |
| `2` | `dynamic strength` | 국소 완화만 검토 | `momentum_tag`, `threshold_profile` 분리 근거 필수 | 분리 근거 없으면 반영 금지 |
| `3` | `overbought` | 완화 보류 | 표본 확장 전 실전 완화 금지 | 표본 부족 상태에서는 반영 금지 |
| `공통` | `fallback 수량 canary` | 현행 유지 | fallback cohort 정합성 먼저 확인 | 정합성 불일치 시 해석 보정 우선 |

## 반영여부 추가검토 필요한 사항 (4/10 계획 필수 기재)

| 항목 | 추가검토 내용 | 검토 시점 | 반영 판단 기준 |
| --- | --- | --- | --- |
| `latency` 후보안 수치 | `ws_age_ms/spread_ratio/quote_stale` 조합 임계값 | `10:00`, `12:00`, 장후 | missed-winner 개선 대비 오탐 증가 허용범위 충족 |
| `dynamic strength` 후보안 | `threshold_profile`별 완화 범위 | 장후 | 특정 profile에서만 기대값 개선 확인 |
| hard time stop 후보안 | shadow 결과의 손익/회전율 영향 | 장후 | 실전 적용 이득이 위험을 상회할 때만 |
| 스윙 관련 이월건 | Gatekeeper miss/threshold 완화 검토 | 장후 | 스캘핑 실행안과 충돌 없을 때만 |
| 원격 선행 적용/비교 | `songstockscan` 선행 canary/shadow 결과 우선 확인, 필요 시 로컬/원격 JSON snapshot 차이를 보조 점검 | 장중 수시, `16:00` 이후 | 원격 선행 결과가 `submitted 전환/체결 품질` 개선으로 이어지거나 safe-only 비교로 해석 왜곡이 없을 때 |

## 트리거 운영 표준

- `[자동 실행]` `09:30~11:00` `buy_pause_guard` 5분 평가, `10:00`/`12:00` snapshot, `16:00` 원격 수집 cron
- `[내 지시 필요]` `09:30~10:00` 판단기준표 기록, `10:00/12:00` 해석 기록, 장후 결론 확정
- `[내 승인 필요]` guard 경보 시 텔레그램 `/buy_pause_confirm <guard_id>` 또는 `/buy_pause_reject <guard_id>`

## 2026-04-10 시간대별 실행 트리거/주체/실행 방법

| 시간대 | 트리거 | 실행 주체(누가) | 실행 방법(어떻게) | 결과 확인 |
| --- | --- | --- | --- | --- |
| `08:00~09:00` | 장전 점검/실행안 확정 | `사용자 지시 -> Codex` | 이 문서의 장전 6개 작업을 순서대로 실행/기록 요청 | 체크리스트 항목/메모 업데이트 |
| `09:30~11:00` | buy pause guard 정기 평가(5분) | `시스템(자동)` | 기본은 자동 실행, 수동 재실행은 `cd /home/ubuntu/KORStockScan && PYTHONPATH=. .venv/bin/python -m src.engine.buy_pause_guard evaluate --date 2026-04-10` | `data/runtime/buy_pause_guard_state.json`, 텔레그램 ADMIN 경보 |
| `guard 경보 수신 시 즉시` | pause 승인/거절 | `사용자(텔레그램 ADMIN)` | 승인: `/buy_pause_confirm <guard_id>` / 거절: `/buy_pause_reject <guard_id>` / 상태: `/pause_status` | 텔레그램 응답 + pause 상태 변경 |
| `필요 시 즉시` | 프롬프트 백업 pause/resume | `사용자 지시 -> Codex` | pause: `cd /home/ubuntu/KORStockScan && PYTHONPATH=. .venv/bin/python -m src.engine.trade_pause_cli pause --source codex_prompt --reason \"manual_guard\"` / resume: `... trade_pause_cli resume --source codex_prompt --reason \"manual_resume\"` / status: `... trade_pause_cli status` | JSON 출력의 `paused`, `label` |
| `10:00` | monitor snapshot 생성 | `시스템(자동)` | cron 표준 실행: `cd /home/ubuntu/KORStockScan && PYTHONPATH=. .venv/bin/python -m src.engine.run_monitor_snapshot --date 2026-04-10` | `data/report/monitor_snapshots/*_2026-04-10.json` |
| `10:00~10:10` | 1차 해석 기록 | `사용자 지시 -> Codex` | 스냅샷 기준 해석 작성 요청 (`손익+미진입 퍼널` 동시 기록) | 체크리스트 해석 섹션 업데이트 |
| `12:00` | monitor snapshot 생성 | `시스템(자동)` | `10:00`와 동일 커맨드로 자동 실행(시간만 다름) | 동일 경로 파일 갱신 |
| `12:00~12:20` | 1차 실질 해석 기록 | `사용자 지시 -> Codex` | `12:00 스냅샷 기준 실질 해석` 작성 요청 | 체크리스트 해석 섹션 업데이트 |
| `16:00` | 원격 로그/스냅샷 수집 | `시스템(자동)` | `cd /home/ubuntu/KORStockScan && PYTHONPATH=. .venv/bin/python -m src.engine.fetch_remote_scalping_logs --date 2026-04-10 --include-snapshots-if-exist` | `tmp/remote_2026-04-10/`, `logs/remote_scalping_fetch_20260410_1600.log` |
| `장후` | 당일 결론 확정 | `사용자 지시 -> Codex` | `유지/적용/보류/롤백` 결론 작성 요청 | 체크리스트 장후 결론 및 익일 이월 항목 |

### 원격 선행 적용 드라이브 원칙 (`2026-04-10 사용자 지시 반영`)

- `사전 적용 후보`(스캘핑 중심)가 관측되면 Codex가 원격(`songstockscan`) 선행 canary/shadow 적용을 기본 제안한다.
- 승인되면 즉시 원격에만 `1축` 적용하고, `30~60분` 단기 피드백(`퍼널 전환`, `blocker 분포`, `체결 품질`)을 회수한다.
- 본서버 반영은 원격 결과를 근거로 `유지/강화/축소/보류/롤백` 중 1개로만 결정한다.
- `전역 완화`, `다축 동시 변경`, `롤백 경로 없는 변경`은 원격에서도 금지한다.

## 원격 latency guard V2 선행 적용 (`2026-04-10 14:32 KST`)

- 판정:
  - 원격(`songstockscan`)에 `latency` 한 축만 선행 적용 완료.
  - 적용 범위는 `quote_stale=False` 조건을 유지한 채 `ws_jitter` 상한만 소폭 확장하는 `remote_v2` 프로필이다.

- 적용 내용:
  - 코드: `src/utils/constants.py`에 `KORSTOCKSCAN_LATENCY_CANARY_PROFILE`, `KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS` 환경변수 훅 추가.
  - 원격 런타임 값: `SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS 260 -> 400`.
  - 유지 항목: `quote_stale=True fail-closed`, `ws_age=450`, `spread_ratio=0.0100`, 태그 제한, 최소 AI 점수, slippage 검사는 그대로 유지.
  - 원격 서비스: `korstockscan-gunicorn.service.d/override.conf`에 아래 환경변수 주입 후 재시작 완료.
    - `KORSTOCKSCAN_LATENCY_CANARY_PROFILE=remote_v2`
    - `KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=400`

- 적용 이유:
  - 오늘 로컬 관측상 `budget_pass 후 미제출` 첫 blocker는 `latency`가 단일 병목이었다.
  - `quote_stale=False` 케이스가 다수라 stale quote를 건드리지 않고도 `latency` 축 내부에서 표본을 늘릴 여지가 있었다.
  - 기존 `LATENCY_GUARD_CANARY` 적용 로그가 사실상 없어, 기존 canary는 실전 표본을 거의 못 받고 있었다.

- 검증:
  - 로컬: `python -m py_compile src/utils/constants.py`, `pytest -q src/tests/test_constants.py src/tests/test_sniper_entry_latency.py` 통과(`8 passed`).
  - 원격: `py_compile` 통과, `systemctl show`에서 프로필 환경변수 반영 확인, `http://127.0.0.1:5000/` `HEAD 200`, gunicorn 재기동 정상 확인.
  - 원격 bot: `2026-04-10 14:35 KST` `tmux bot` 세션 재시작 완료, 새 `bot_main.py` PID `889889`에서 `KORSTOCKSCAN_LATENCY_CANARY_PROFILE=remote_v2`, `...MAX_WS_JITTER_MS=400` 반영 확인.

- 롤백 경로:
  - 원격 `override.conf`에서 위 2개 환경변수를 제거하고 `sudo systemctl daemon-reload && sudo systemctl restart korstockscan-gunicorn.service`.

- 다음 확인:
  - `30~60분` 후 원격 기준 `latency_canary_applied`, `order_bundle_submitted`, `holding_started`, `full/partial fill`, `budget_pass -> latency_block` 분포를 다시 본다.
  - 본서버는 원격에서 `submitted 전환` 또는 `missed_winner 회수` 근거가 확인될 때만 후속 반영 검토.

## 원격서버 접근 테스트 (수동, `2026-04-10 07:36 KST`)

| 테스트 | 실행 명령 | 결과 | 판정 |
| --- | --- | --- | --- |
| 당일(`2026-04-10`) 원격 수집 표준 경로 | `PYTHONPATH=. .venv/bin/python -m src.engine.fetch_remote_scalping_logs --date 2026-04-10 --include-snapshots-if-exist` | SSH 접속 성공. 원격에서 `missing_remote_file:/home/windy80xyt/KORStockScan/data/pipeline_events/pipeline_events_2026-04-10.jsonl` 반환 | `접속 정상`, `필수 파일 미생성` |
| 전일(`2026-04-09`) 원격 수집 표준 경로 | `PYTHONPATH=. .venv/bin/python -m src.engine.fetch_remote_scalping_logs --date 2026-04-09 --include-snapshots-if-exist` | `[REMOTE_FETCH]` 완료. 산출물 `tmp/remote_2026-04-09/remote_scalping_2026-04-09.tar.gz` + 풀린 파일(`pipeline_events/post_sell/monitor_snapshots/logs`) 확인 | `접속+수집 정상` |

- 운영 해석:
  - 현재 실패 원인은 `인증/네트워크`가 아니라 `당일 필수 산출물 생성 시점 이전`이다.
  - `16:00` 자동 수집은 동일 명령으로 재시도하면 되며, 실패 시 먼저 원격 `pipeline_events_2026-04-10.jsonl` 생성 여부를 점검한다.

## BUY 주문 추적 모니터링/점검 (`2026-04-10 09:15 KST`)

- 판정:
  - `BUY 주문 추적 파이프라인 동작 정상`이며, 현재까지 체결 표본은 `테스(095610) 1건`이다.
  - 미진입 병목은 `latency guard miss(파두)`가 핵심이며, `liquidity/ai_score` 차단이 보조축으로 관측된다.

- 근거:
  - 런타임 상태: `buy_pause_guard paused=false`, `active_guard_id` 없음.
  - 주문 추적:
    - `ORDER_NOTICE_BOUND` 오늘자 BUY 주문 `2건` 모두 `접수+체결` 확인, `접수 후 미체결 0건`.
    - 체결 로그: `09:12:31~09:12:33` `테스(095610)` `ENTRY_FILL(scout 1/1, main 7/7)` + `ENTRY_BUNDLE_FILLED filled_qty=8/8`.
    - `full fill` 표본 `1건`, `partial fill` 표본 `0건`(현재 기준).
  - 퍼널(`pipeline_events_2026-04-10.jsonl`, unique `record_id` 기준):
    - `entry_armed=2`, `budget_pass=2`, `order_bundle_submitted=1`, `holding_started=1`.
    - `budget_pass 후 미제출=1`은 `파두(440110, id=1647)`이며 terminal stage는 `latency_block(REJECT_DANGER)`.
  - blocker 분포(이벤트 누적):
    - `latency_block=100`(주요 종목: `파두 41`, `테스 9`)
    - `blocked_liquidity=150`(주요 종목: `태광 66`, `에이치엠넥스 9`)
    - `blocked_ai_score=20`(주요 종목: `파두/에이피알/삼성중공업/LIG넥스원`)
  - 미진입 기회비용:
    - `missed_entry_counterfactual` 최신(`09:15:13`)에서 `파두` 1건이 `MISSED_WINNER`로 분류(`terminal=latency_block`, confidence tier `A`).

- 즉시 액션:
  - `09:30~11:00` 구간은 `파두 latency_block` 재발 빈도와 `테스 계열 체결 재현`을 동일 포맷으로 누적 기록한다.
  - `10:00` 스냅샷 해석 시 `BUY -> entry_armed -> budget_pass -> blocked/submitted` 퍼널과 `full/partial fill`을 분리 보고한다.

## 테스 손절 매매 점검 (`2026-04-10 09:24 KST`)

- 판정:
  - `테스(095610, id=1658)` 손절은 룰 위반 없이 정상 집행됐고, 현재 post-sell 평가는 `NEUTRAL`이다.
  - 단일 표본 기준으로는 `과도한 조기손절` 근거가 충분하지 않다.

- 근거:
  - 진입/체결: `09:12:31~09:12:33`, `fallback` 번들 `8/8` `full fill` 체결(`avg_buy=86125`).
  - 손절 집행: `09:16:07` `exit_rule=scalp_soft_stop_pct`, `profit_rate=-1.53%`, `09:16:09 sell_completed`.
  - 성과 반영(`trade_review 09:24:20`): `COMPLETED=1`, `loss_trades=1`, `realized_pnl_krw=-10564`.
  - post-sell(`09:24:25` 평가 완료):
    - outcome=`NEUTRAL`, `metrics_10m close_ret_pct=+0.235`, `mfe_pct=+0.824`.
    - `MISSED_UPSIDE` 조건(`mfe>=0.8` + `10분 종가>=0.3`)에서 `종가 조건 미달`로 분류.
  - 추가 관측: `09:16:03`에 `hard_time_stop_shadow(fallback_3m)`가 `-0.72%`에서 포착됐으나 `shadow_only`로 실전 미적용.

- 다음 액션:
  - 장후 결론에서 `테스`는 `bad_exit`가 아닌 `neutral defensive exit` 후보로 유지하고, 동일 패턴 표본 `N>=5` 전까지 손절 임계값 직접 완화는 보류한다.
  - `hard_time_stop_shadow`는 실전 전환 없이 `손실 절대값 절감 가능성`만 추적하고, `latency/liquidity` 병목과 분리해 원인 귀속한다.

## 10:00 snapshot 자동 생성 확인 + 1차 해석 (`2026-04-10 10:07 KST`)

- 판정:
  - `10:00` snapshot 자동 생성은 정상 수행됐다.
  - `손익`은 소폭 음수지만(`-3,714원`), `BUY 후 미진입` 퍼널의 기회비용 압력이 더 큰 상태다.

- 근거:
  - 자동 생성 확인:
    - `logs/realtime_monitor_20260410_1000.log` 생성 시각 `10:00`, 실행 결과에 `trade_review/performance_tuning/post_sell_feedback/missed_entry_counterfactual/server_comparison` 저장 경로 출력 확인.
    - 스냅샷 파일 mtime: `10:00:29~10:00:36`.
  - 손익(`trade_review` `10:00:07`):
    - `completed_trades=2`, `win/loss=1/1`, `avg_profit_rate=-0.25%`, `realized_pnl_krw=-3,714`.
    - `쏠리드(050890)` `+6,850원`, `테스(095610)` `-10,564원`.
    - 체결 품질: `ENTRY_BUNDLE_FILLED` 기준 `full fill=2`, `partial fill=0`.
  - BUY 후 미진입 퍼널(`pipeline_events`, unique `record_id`, `10:00:59` cutoff):
    - `ai_confirmed=43 -> entry_armed=15 -> budget_pass=15 -> order_bundle_submitted=2 -> holding_started=2`.
    - `budget_pass 후 미제출=13`(86.7%) terminal 분포:
      - `blocked_ai_score=5`
      - `blocked_strength_momentum=3`
      - `latency_block=3`
      - `blocked_overbought=2`
  - 미진입 기회비용(`missed_entry_counterfactual` `10:00:29`):
    - `evaluated_candidates=9`, `MISSED_WINNER=7(77.8%)`, `AVOIDED_LOSER=2(22.2%)`.
    - `latency_block` 계열 8건의 `missed_winner_rate=75.0%`.

- 다음 액션:
  - `12:00` 해석까지는 `budget_pass->미제출 13건`의 terminal 분포 변화를 최우선 추적한다.
  - 특히 `latency_block`과 `blocked_ai_score`를 분리 기록해, 손익보다 `order_bundle_submitted` 전환 증가 여부를 먼저 판정한다.

### `budget_pass -> 미제출(13건)` 실병목 검증 (`2026-04-10 10:13 KST`)

- 판정:
  - `예`, 해당 13건은 실제 매수진입 병목으로 확인됐다.
  - 공통 1차 차단은 전건 `latency_block`이며, 주문 접수 단계까지 도달한 건이 없다.

- 근거:
  - 13건 전체에서 `budget_pass` 직후 첫 blocker가 모두 `latency_block` (`13/13`).
  - 13건 모두 `order_bundle_submitted=False`, `holding_started=False`(해당 record_id 기준).
  - 13건의 종목별 `ORDER_NOTICE_BOUND type=BUY` 로그가 `접수=0`, `체결=0`으로 확인되어, 주문 라우팅 이전 단계에서 차단됨.
  - 동일 종목이 다른 record_id로 우회 진입한 케이스도 현재 시점 기준 `0건`.

- 해석:
  - `budget_pass 미제출`은 단순 집계 노이즈가 아니라, 이 구간에서는 사실상 `latency gate`가 주문제출을 막은 실진입 병목이다.

## 10:55 가드 구간 점검 (`2026-04-10 10:55 KST`)

- 판정:
  - `09:30~10:55` buy pause guard 자동 평가는 누락 없이 수행됐고, 경보/자동 pause는 없었다.

- 근거:
  - `buy_pause_guard.log`의 `evaluated_at`가 `09:30:02, 09:35:01, ..., 10:55:01`로 5분 간격 연속 확인.
  - 모든 평가에서 `should_alert=false`, `alert_sent=false`, `guard_id=""`, `triggered_flag_names=[]`.
  - 현재 상태 확인:
    - `buy_pause_guard status --json`: `paused=false`, `active_guard_id=""`.
    - `trade_pause_cli status`: `paused=false`.

- 다음 액션:
  - `11:00` 1회 자동 평가 결과만 추가 확인 후, `12:00` snapshot/실질 해석으로 전환한다.

## 완화 개선 악영향 검토 (`2026-04-10 11:11 KST`)

- 판정:
  - `어제 대비 완화 로직`이 손익을 직접 악화시켰다는 강한 증거는 현재 없다.
  - 다만 `손익극대화` 관점에서 경고 신호는 존재한다. 핵심은 `진입 후 성과`보다 `budget_pass 이후 미제출 확대`다.

- 근거:
  - 결과 요약(`4/9` -> `4/10`):
    - 실현손익: `-18,590원 -> -10,885원`(음수폭 축소)
    - 평균수익률: `-0.90% -> -0.41%`(개선)
    - 완료거래: `4 -> 6`(활동량 증가)
  - 하지만 퍼널 효율:
    - `budget_pass -> order_bundle_submitted` 전환율 `22.7%(5/22) -> 19.4%(6/31)`로 하락
    - `budget_pass 후 미제출` 1차 차단은 `4/9=17/17`, `4/10=25/25` 모두 `latency_block`
    - `quote_stale=True`가 붙은 latency 차단 표본이 `4/9=5건 -> 4/10=12건`으로 증가
  - 미진입 기회비용:
    - `missed_winner_rate 60.0% -> 73.7%` 상승
    - 다만 `estimated_counterfactual_pnl_10m_sum -104,313원 -> -33,140원`으로 절대 음수폭은 축소
  - 완화로 진입된 표본(동적강도 canary 경유, 제출까지 간 ID):
    - `테스(1658) -1.53%, -10,564원`
    - `쏠리드(1669) +1.03%, +6,850원 (post-sell: GOOD_EXIT)`
    - 단일 표본 기준 순손익 `-3,714원`으로, `완화 자체가 일방향 악영향`이라고 단정할 수준은 아님

- 해석:
  - 현재 리스크는 `완화가 너무 공격적`이라서 생긴 손실 확대보다, `latency gate(특히 quote_stale 동반)`로 주문제출이 막혀 EV를 깎는 구조가 더 크다.
  - 즉 `완화의 부작용`보다 `완화 효과 전달 실패(제출 전 차단)`가 본문제에 가깝다.

- 다음 액션:
  - `12:00` 해석에서는 `budget_pass 미제출`을 `quote_stale=True/False`로 분리해 각각의 missed_winner_rate를 기록한다.
  - `latency` 완화 검토는 `quote_stale=False` 구간의 오탐 증가 없이 `submitted` 전환을 올리는지부터 1차 판정하고, `quote_stale=True`는 별도 축으로 shadow 검증한다.

## entry-pipeline-flow 공백 이슈 조치 (`2026-04-10 11:15 KST`)

- 판정:
  - `dashboard entry-pipeline-flow` 빈 데이터 문제의 원인은 API가 `[ENTRY_PIPELINE]` 텍스트 로그 의존이었던 점이다.
  - `pipeline_events_YYYY-MM-DD.jsonl` 우선 사용으로 수정 완료.

- 조치:
  - `sniper_entry_pipeline_report.py`를 JSONL 우선 + 텍스트 fallback 구조로 변경.
  - JSONL event의 `record_id`를 `fields.id`로 보정해 기존 시각화/집계 로직과 호환 유지.

- 검증:
  - `pytest -q src/tests/test_entry_pipeline_report.py` 통과(`3 passed`).
  - API 재현 확인: `/api/entry-pipeline-flow?date=2026-04-10&since=09:41:30&top=10` 응답 `200`, `has_data=true`.
  - 실서버 반영: `korstockscan-gunicorn.service` 재시작 후 외부 URL(`https://korstockscan.ddns.net/...`) 응답 `has_data=true`, `recent_stocks=10` 확인.
  - 원격서버 반영: 동일 파일을 `songstockscan`에 배포 후 `korstockscan-gunicorn.service` 재시작, 외부 URL(`https://songstockscan.ddns.net/...`)도 `has_data=true`, `recent_stocks=10` 확인.

## 12:00 snapshot 자동 생성 확인 + 1차 실질 해석 (`2026-04-10 12:58 KST`)

- 판정:
  - `12:00` snapshot 자동 생성은 정상이다.
  - 다만 `손익`보다 `BUY 후 미진입` 병목이 더 큰 상태이며, 핵심은 `budget_pass 이후 1차 latency 차단`이다.

- 근거:
  - 자동 생성 확인:
    - `data/report/monitor_snapshots/*_2026-04-10.json` 파일 mtime `12:00:30`(`server_comparison` `12:00:58`) 확인.
  - 손익(`trade_review` `saved_snapshot_at=12:00:05`):
    - `completed_trades=6`, `win/loss=2/4`, `avg_profit_rate=-0.41%`, `realized_pnl_krw=-10,885`.
  - BUY 후 미진입 퍼널(`pipeline_events`, `12:00:59` cutoff):
    - `ai_confirmed=67 -> entry_armed=36 -> budget_pass=36 -> submitted=6 -> holding_started=6`.
    - `budget_pass -> submitted` 전환율 `16.7%`.
    - `budget_pass 후 미제출=30건`.
    - terminal stage 분포는 `blocked_strength_momentum=19`, `blocked_ai_score=9`, `blocked_overbought=1`, `latency_block=1`.
    - 그러나 `budget_pass 이후 첫 blocker` 기준으로는 `latency_block=30/30`(quote_stale `True=14`, `False=16`).
  - 미진입 기회비용(`missed_entry_counterfactual` `saved_snapshot_at=12:00:20`):
    - `evaluated_candidates=20`, `missed_winner_rate=80.0%`, `avoided_loser_rate=15.0%`,
    - `estimated_counterfactual_pnl_10m_krw_sum=+19,459`.

- 다음 액션:
  - `16:00` 원격 수집 전까지 `quote_stale=False latency_block` 표본을 우선 축으로 누적해 `submitted` 전환 여지를 본다.
  - 장후 결론에서는 `latency/dynamic/overbought`를 손익 단일치보다 `퍼널 전환 + blocker 분포`로 우선 판정한다.

## 현재 시점 운영 실행 점검 (`2026-04-10 13:00 KST`)

- 판정:
  - `buy pause` 관련 즉시 조치 필요사항은 없다.
  - `12:00` 스냅샷 반영까지 완료됐고, 다음 자동 트리거는 `16:00 원격 수집`이다.

- 근거:
  - 수동 가드 1회 평가(`13:00:22`): `should_alert=false`, `alert_sent=false`, `sample_ready=false`.
  - pause 상태: `buy_pause_guard status` `paused=false`, `trade_pause_cli status` `paused=false`.
  - BUY 주문 추적 로그: `ORDER_NOTICE_BOUND type=BUY` 최신 시각 `10:46:31`(하림지주 접수), 이후 신규 BUY 바인드 로그 없음.

- 다음 액션:
  - `16:00` 자동 원격 수집 완료 여부(`tmp/remote_2026-04-10`, `logs/remote_scalping_fetch_20260410_1600.log`)만 확인하면 된다.

## performance-tuning 0값 이슈 조치 (`2026-04-10 13:20 KST`)

- 판정:
  - `performance-tuning`의 `0건/0ms` 표시는 정상 상태가 아니라, 입력 로그 경로 불일치로 인한 집계 누락이었다.
  - 로컬/원격(`songstockscan`) 모두 동일 원인이 확인되어 동일 패치로 조치 완료.

- 근거:
  - 이슈 시점 API:
    - 로컬 `https://korstockscan.ddns.net/api/performance-tuning?date=2026-04-10&since=11:07:51`에서 `gatekeeper_decisions=0`.
    - 원격 `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-10&since=11:07:51`도 `gatekeeper_decisions=0`.
  - 원인 확인:
    - `sniper_performance_tuning_report.py`가 `logs/sniper_state_handlers_info.log`의 `[ENTRY_PIPELINE]/[HOLDING_PIPELINE]`만 읽고 있었음.
    - 실제 운영 이벤트는 `data/pipeline_events/pipeline_events_2026-04-10.jsonl` 및 `logs/pipeline_event_logger_info.log*`에 기록되어 있었음.

- 조치:
  - `src/engine/sniper_performance_tuning_report.py`를 `pipeline_events_YYYY-MM-DD.jsonl` 우선 로드 + 텍스트 로그 fallback 구조로 변경.
  - JSONL의 `record_id -> fields.id` 보정 포함.
  - 테스트 추가: `src/tests/test_performance_tuning_report.py::test_performance_tuning_report_prefers_jsonl_events`.

- 검증:
  - 로컬 코드 직접 생성(`since=11:07:51`): `gatekeeper_decisions=20`.
  - 로컬 API 재시작 후 동일 URL: `gatekeeper_decisions=20`(`카드: Gatekeeper 결정 20건`).
  - 원격 서버 패치+재시작 후 동일 URL: `gatekeeper_decisions=29`(`카드: Gatekeeper 결정 29건`).

## 오늘 성과 압축 요약 (`2026-04-10 14:03 KST`, 로컬 단독)

- 판정:
  - 실현손익은 `-10,885원`으로 음수지만, `BUY 후 미진입` 기회비용 압력이 더 큼.
  - 실전 병목은 `2단계`: `AI BUY 직후 first_ai_wait 누적` + `budget_pass 이후 latency 단일 차단`.

- 핵심 수치:
  - 거래 성과(`COMPLETED + valid profit_rate`): `6건`, `승/패=2/4`, `승률 33.3%`, `avg -0.41%`, `realized -10,885원`.
  - BUY 퍼널: `ai_confirmed 75 -> entry_armed 37 -> budget_pass 37 -> submitted 6` (`ai_confirmed->submitted 8.0%`).
  - BUY 이후 미진입 분류: `69건` 모두 `ai_threshold_miss(first_ai_wait)`로 시작, terminal은 `blocked_strength_momentum 40`, `blocked_ai_score 23`, `blocked_overbought 5`, `first_ai_wait 1`.
  - budget_pass 이후 미제출: `31건`, `first blocker latency_guard_miss 31/31`, `quote_stale False/True = 14/17`.
  - BUY 시그널 universe: `attempt 22`, `entered 1`, `missed 21`; missed outcome은 `MISSED_WINNER 16`, `AVOIDED_LOSER 4`, `NEUTRAL 1`.
  - counterfactual(`10분`): `estimated +24,960원`, `missed_winner_rate 76.2%`.
  - 체결 품질: `normal full=6`, `fallback partial=3`; partial 포함 ID 손익합 `-9,280원`.

- 즉시 인사이트(반영 후보):
  - `latency`는 canary가 실전 제출 전환으로 이어지지 못하고 있어(`budget 이후 31/31 latency`) EV 회수 실패가 지속.
  - `fallback partial` 코호트가 손실 기여도가 크므로(`-9,280원`) full/partial 분리 성과선을 장후 결론의 필수 판정 항목으로 고정할 가치가 있음.
  - `first_ai_wait -> blocked_strength_momentum/blocked_ai_score` 연쇄가 크므로 BUY 직후 미진입 분석은 해당 연쇄를 고정 축으로 추적해야 함.

## 완화안 코드 반영 상태 (2026-04-10 기준)

| 항목 | 상태 | 코드 수정 여부 | 이유/조건 |
| --- | --- | --- | --- |
| `latency guard` 완화안 | `조건부 canary 반영` | `반영됨` | `REJECT_DANGER` 중 `quote_stale=False`, 태그/점수/ws/spread/slippage 조건을 동시에 만족한 케이스만 fallback 허용 |
| `dynamic strength` 완화안 | `조건부 canary 반영` | `반영됨` | `blocked_strength_momentum` 중 근소 미달(`buy_ratio/exec_buy_ratio/window_buy_value`) 케이스만 태그 제한 하에 통과 |
| `overbought` 완화안 | `보류` | `미반영` | 표본 부족으로 실전 완화 금지 원칙 유지 |
| `buy pause guard 승인형 플로우` | `반영 완료` | `반영됨` | `buy_pause_guard.py`, 텔레그램 confirm/reject, `trade_pause_cli.py` 경로 사용 가능 |

- 해석 기준:
  - `latency/dynamic`은 전역 완화가 아니라 `조건부 canary` 코드 반영 상태다.
  - 실행 중 프로세스에 반영하려면 프로세스 재시작 또는 설정 재로딩이 필요하다.

## 완화 이력 추적 보드 (오늘 필수 업데이트)

| 추적 ID | 축 | 오늘 시작 상태 | 코드/설정 기준 | 10:00 기록 | 12:00 기록 | 장후 최종 |
| --- | --- | --- | --- | --- | --- | --- |
| `RELAX-LATENCY-20260410-V1` | `latency guard` | `조건부 canary ON` | `SCALP_LATENCY_GUARD_CANARY_*` + `latency_canary_applied` 로그 | `counterfactual latency_block=8건, missed_winner_rate=75.0%, budget_pass후 terminal latency=3건` | `counterfactual latency_block=19건, missed_winner_rate=78.9%, budget_pass후 first blocker latency=30건(quote_stale=True/False=14/16)` | `강화` |
| `RELAX-DYNSTR-20260410-V1` | `dynamic strength` | `조건부 canary ON` | `SCALP_DYNAMIC_STRENGTH_CANARY_*` + `canary_relaxed_*` 로그 | `budget_pass후 terminal blocked_strength_momentum=3건, strength_momentum_pass(canary_applied=True)=131 events` | `budget_pass후 terminal blocked_strength_momentum=19건, strength_momentum_pass(canary_applied=True)=219 events` | `유지` |
| `RELAX-OVERBOUGHT-HOLD` | `overbought` | `완화 보류 유지` | 기존 차단 유지, 완화 파라미터 미적용 | `budget_pass후 terminal blocked_overbought=2건, 완화 보류 유지` | `budget_pass후 terminal blocked_overbought=1건, 완화 보류 유지` | `유지` |

## 연결고리 기록 규칙 (최적화 지점 찾을 때까지 유지)

- 같은 ID 기준으로 `코드 변경 -> 지표 변화 -> 의사결정`을 한 줄로 연결해서 기록한다.
- `10:00`, `12:00`, `장후`에 아래 3개를 반드시 갱신한다.
  - `latency_block / blocked_strength_momentum / blocked_overbought` 건수
  - `latency_canary_applied / canary_relaxed_*` 적용 건수
  - 실체결 전환(`order_bundle_submitted`, `holding_started`) 및 손익 분포
- 장후에는 각 ID별로 `유지/강화/축소/롤백` 중 1개를 확정한다.
- 다음 세션에서 신규 실험을 추가할 때는 새 이름을 만들지 않고 기존 ID를 `V2`로 승격한다.

## 2026-04-10 스냅샷별 필수 체크

- [x] `10:00` 스냅샷에 3개 추적 ID의 중간 상태가 기록된다
- [x] `12:00` 스냅샷에 3개 추적 ID의 중간 상태가 갱신된다
- [x] 장후 결론에 3개 추적 ID별 `유지/강화/축소/롤백`이 확정된다

## 16:00 원격 수집 / 스냅샷 확인 (`2026-04-10 16:01 KST`)

- 판정:
  - `16:00` 자동 원격 수집은 `실패`했다.
  - 다만 원격 `15:45` 스냅샷 JSON은 이미 생성돼 있었고, 이를 별도 수집해 장후 결론에 반영했다.

- 근거:
  - 자동 수집 로그 `logs/remote_scalping_fetch_20260410_1600.log`에서 원격 `pipeline_events_2026-04-10.jsonl`이 `file changed as we read it`로 종료.
  - 원격 서버에는 `trade_review/performance_tuning/post_sell_feedback` 스냅샷이 `2026-04-10 15:45 KST` 기준으로 존재.
  - 별도 수집 경로: `tmp/remote_2026-04-10_snapshot/*.json`

- 해석:
  - 실패 원인은 `인증/접속`이 아니라 `실시간 갱신 중인 JSONL을 tar로 직접 묶는 방식`이다.
  - 다음 영업일 운영 보강은 2단계로 분리한다.
    - `1차(기본 경로)`: 원격 live JSONL을 `임시 파일로 복사`한 뒤 그 사본을 `tar`로 수집한다.
    - `2차(비상 fallback)`: JSONL 수집이 다시 실패하면 `monitor snapshot JSON만이라도 반드시 회수`하는 `snapshot-only fallback`을 둔다.

## 장후 최종결론 (`2026-04-10 16:02 KST`, 로컬+원격 스냅샷 기준)

- 판정:
  - `RELAX-LATENCY`: `강화`
  - `RELAX-DYNSTR`: `유지`
  - `RELAX-OVERBOUGHT`: `유지`

- 근거:
  - 로컬 최종 스냅샷(`2026-04-10 15:46 KST`):
    - `trade_review`: `completed_trades=6`, `realized_pnl_krw=-10,885원`, `win/loss=2/4`
    - `missed_entry_counterfactual`: `evaluated=21`, `MISSED_WINNER=17`, `missed_winner_rate=81.0%`, `estimated_counterfactual_pnl_10m_krw_sum=24,960`
    - unique 퍼널: `ai_confirmed 75 -> entry_armed 44 -> budget_pass 40 -> submitted 6`
    - `budget_pass 후 미제출` 첫 blocker는 `34/34 latency_block`
  - `RELAX-LATENCY`:
    - 오늘 실전 EV 훼손의 주축은 여전히 `latency_block`
    - 로컬 canary 적용 흔적은 제한적이라 `과완화 부작용`보다 `적용 범위 부족` 해석이 맞다
    - 원격 `remote_v2`는 `2026-04-10 14:35 KST`에 반영돼 표본 시간이 짧았고, 원격 `trade_review`는 `1건/-216원`, `entry_pipeline_flow` safe 비교는 `submitted_stocks local 4 vs remote 0`으로 마감했다
    - 따라서 본서버 즉시 전역 반영은 아니지만, 다음 영업일에도 `quote_stale=False` 축 중심으로 원격 강화 관찰을 이어가는 결론이 맞다
  - `RELAX-DYNSTR`:
    - `dynamic canary` 적용 로그는 `unique id 49건`, 그중 `submitted 2건`
    - `AI BUY 후 미제출` terminal은 여전히 `blocked_strength_momentum 41`, `blocked_ai_score 21`, `blocked_overbought 4`
    - canary는 작동 중이지만 downstream 전환 증거가 약해, 추가 완화보다 현행 유지 후 조건 재설계가 맞다
  - `RELAX-OVERBOUGHT`:
    - unique terminal 기준 `blocked_overbought 4건`으로 비중이 낮다
    - 병목 1순위는 `latency`, 2순위는 `dynamic strength`이며 overbought는 오늘 핵심 원인이 아니다
    - 표본이 부족한 상태에서 실전 완화를 열 근거는 없다
  - 원격 스냅샷 참고:
    - 원격 `trade_review`: `completed_trades=1`, `realized_pnl_krw=-216원`
    - 원격 `post_sell_feedback`: `evaluated=1`, `MISSED_UPSIDE=100%`
    - 원격 `performance_tuning`: `gatekeeper_decisions=90`, `gatekeeper_eval_ms_p95=14,247`, `holding_review_ms_p95=2,471`
    - 원격은 `latency remote_v2`가 장 마감 직전 투입돼 오늘 결론의 주근거보다는 `익일 관찰용 선행 실험`으로 보는 편이 맞다

- 다음 액션:
  - `RELAX-LATENCY`: 다음 영업일 원격 우선 관찰 축으로 승격
  - `RELAX-DYNSTR`: 현행 유지, `below_window_buy_value` 계열만 `momentum_tag/threshold_profile`로 재설계
  - `RELAX-OVERBOUGHT`: 유지, 표본 누적 전 실전 완화 금지
  - 운영 보정: `fetch_remote_scalping_logs`는 실시간 JSONL 변경에 깨지지 않도록 보강 필요

## 2026-04-10 완료 기준

- [x] 장전 `08:00~09:00` 6개 작업 결과가 시각/수치와 함께 기록된다
- [x] 장중 미진입 표본(`AI WAIT/latency/liquidity`)이 종목 단위로 누적된다
- [x] 장후 이월건(스윙/hard stop/자동전환)이 `처리 또는 재이월 사유`와 함께 문서화된다
- [x] 완화 우선순위 반영 대상은 `필수 확인` 통과 여부가 명시된다
- [x] `2026-04-13`로 넘길 적용/보류/추가검토 근거가 남는다

## 참고 문서

- [2026-04-09-stage2-todo-checklist.md](./2026-04-09-stage2-todo-checklist.md)
- [2026-04-09-scalping-remaining-plan.md](./2026-04-09-scalping-remaining-plan.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-10 16:02:16`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-10.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`5`
  - expired_rows local=162 remote=145 delta=-17.0; total_trades local=6 remote=1 delta=-5.0; completed_trades local=6 remote=1 delta=-5.0
- `Performance Tuning`: status=`ok`, differing_safe_metrics=`14`
  - holding_review_ms_p95 local=11622.0 remote=2471.0 delta=-9151.0; gatekeeper_eval_ms_p95 local=22469.0 remote=14247.0 delta=-8222.0; gatekeeper_eval_ms_avg local=12419.29 remote=11177.19 delta=-1242.1
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=6 remote=1 delta=-5.0; evaluated_candidates local=6 remote=1 delta=-5.0
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`5`
  - total_events local=304135 remote=363046 delta=58911.0; tracked_stocks local=168 remote=163 delta=-5.0; submitted_stocks local=4 remote=0 delta=-4.0
<!-- AUTO_SERVER_COMPARISON_END -->
