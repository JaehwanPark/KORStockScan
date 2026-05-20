# KORStockScan

KORStockScan은 키움 REST/WebSocket 기반 한국 주식 자동매매 엔진, 장중/장후 리포트, 자동 한계값 튜닝(threshold tuning), 스캘핑/스윙 시뮬레이션, 운영 감시를 하나의 자동화체인(automation chain)으로 묶은 프로젝트입니다.

현재 기준 문서는 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md)입니다. 실행 항목과 Due/Slot/TimeWindow/Track은 날짜별 [stage2 checklist](docs/checklists/README.md)가 소유합니다.

현재 기준일: `2026-05-20 KST`

README, 런북(runbook), Plan Rebase, prompt, AGENTS 같은 기준 문서는 사용자의 명시 작업지시가 있을 때만 갱신합니다. 문서 갱신은 runtime/order/provider/bot/threshold 변경과 분리하고, 필요한 경우 1차 수정, 2차 감리, 최종 보완 순서로 parser 검증까지 닫습니다.

## 현재 운영 기준

목표는 손실 억제형 미세조정이 아니라 기대값(EV)과 순이익 극대화입니다. 손익 판단은 `COMPLETED + valid profit_rate`만 사용하고, 미완료/NULL/fallback 정규화 값은 손익 기준에서 제외합니다.

승률은 보조 진단 지표(diagnostic win rate)입니다. 적용과 승격의 1차 판단은 기대값(EV)이며, EV 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct`처럼 명시적으로 구분합니다. `simple_sum_profit_pct`는 EV로 취급하지 않습니다.

장중 런타임 한계값 변경(runtime threshold mutation)은 금지합니다. 적용은 장후 산출물, 다음 장전 런타임 환경(runtime env), 장후 귀속 분석(attribution) 순서로만 다룹니다.

## 핵심 원칙

- 실전 변경은 같은 단계(stage) 안에서 단일 소유자(owner) 카나리(canary)를 기본으로 합니다.
- 실주문 안전장치(hard safety)는 항상 우선합니다. broker submit guard, stale quote submit block, price freshness, hard/protect/emergency stop, 계좌/order/cooldown/qty guard는 우회할 수 없습니다.
- 시뮬레이션, 실주문 없는 추적관찰(probe), 놓친 경우 복기(counterfactual)는 source bundle과 approval request 근거가 될 수 있지만, 실제 체결 품질(real execution quality)이나 실주문 전환 근거로 단독 사용하지 않습니다.
- Sentinel, panic sell/buying, system error detector는 리포트 전용(report-only) 또는 source-quality 입력입니다. approval artifact와 rollback guard 없이 주문, 청산, threshold, provider, bot 상태를 바꾸지 않습니다.
- code-improvement workorder는 자동 repo 수정이 아니라 Codex 구현 지시 입력입니다.

## 처음 설치하기

### 1. 전제 조건

- Linux 서버 또는 WSL 계열 환경
- Python 3.13.12 권장. 현재 `.venv` 검증 기준은 `Python 3.13.12`입니다.
- Git
- PostgreSQL 또는 프로젝트에서 사용하는 DB 접속 정보
- 키움 API app key/secret과 계좌 권한
- OpenAI API key
- 선택 사항: Telegram bot token, GitHub Project token, Google Calendar service account

### 2. 저장소 받기

```bash
git clone <repository-url> KORStockScan
cd KORStockScan
```

### 3. Python 가상환경 만들기

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

패키지 설치/업그레이드/제거는 운영 영향이 있으므로 변경 전에 별도로 판단합니다.

### 4. 설정 파일 준비

샘플 설정을 복사해 운영 설정을 만듭니다.

```bash
cp data/config_sample.json data/config_prod.json
```

`data/config_prod.json`에 최소한 아래 항목을 채웁니다.

```json
{
  "TELEGRAM_TOKEN": "optional",
  "ADMIN_ID": "optional",
  "VIRTUAL_ORDERABLE_AMOUNT": 0,
  "KIWOOM_WS_URI": "wss://api.kiwoom.com:10000/api/dostk/websocket",
  "KIWOOM_BASE_URL": "https://api.kiwoom.com",
  "KIWOOM_APPKEY": "required",
  "KIWOOM_SECRETKEY": "required",
  "DB_URL": "postgresql://user:password@localhost:5432/dbname"
}
```

민감정보는 git에 커밋하지 않습니다. `data/credentials.json`을 쓰는 환경이면 같은 원칙으로 운영 서버에만 둡니다.

### 5. 키움 조건검색식 사전등록

KORStockScan의 조건검색 기반 후보 수집은 키움증권 영웅문4 HTS에 등록된 사용자 조건검색식을 전제로 합니다. 키움 REST/OpenAPI 조건검색 목록은 HTS에서 만든 조건검색식을 조회하는 구조이므로, 봇을 실행하기 전에 영웅문4에서 조건검색식을 먼저 작성하거나 복사해 `내조건식`에 저장해야 합니다.

기본 확인 경로:

- 영웅문4 `[0150] 조건검색` 화면에서 조건식을 작성/저장합니다.
- 키움 공식 조건검색 도움말: [영웅문4 [0150] 조건검색](https://download.kiwoom.com/hero4_help_new/0150.htm)
- 키움 REST API 조건검색 목록조회 문서: [조건검색 목록조회 ka10171](https://openapi.kiwoom.com/m/guide/apiguide?jobTpCode=15)
- 다른 PC에서 HTS 설정을 옮겨야 하면 키움 공식 도움말의 [설정저장/불러오기](https://download.kiwoom.com/hero4_help_new/p021.htm)를 확인합니다.

조건검색식 복사 또는 공유 과정에서 원천 소유자의 키움증권 ID를 입력해야 하는 화면이 나오면 `windy80x`를 사용합니다. 복사 후에는 영웅문4에서 해당 조건식이 실제로 `내조건식`에 보이는지 확인하고, 봇/API가 조건검색 목록을 다시 불러오도록 재시작 또는 장전 초기화를 수행합니다.

### 6. AI와 운영 환경변수

스캘핑 live AI route는 OpenAI 고정입니다.

```bash
export OPENAI_API_KEY="..."
export KORSTOCKSCAN_SCALPING_AI_ROUTE=openai
export KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws
export KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true
```

Gemini/DeepSeek 계열은 분석/리포트 경로에서만 별도 키를 사용할 수 있습니다. live 스캘핑 route fallback으로 해석하지 않습니다.

### 7. 기본 검증

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

문서 checklist parser만 확인하려면 아래 명령을 사용합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

### 8. 웹 대시보드 실행

```bash
PYTHONPATH=. .venv/bin/python src/web/app.py
```

기본 바인딩은 `0.0.0.0:5000`입니다. systemd/nginx 운영 설정은 `deploy/systemd/`, `deploy/nginx/`를 봅니다.

### 9. 장전 런타임 환경 생성

봇은 당일 `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.env`를 source합니다. 수동 검증 환경에서는 먼저 장전 자동화체인을 실행할 수 있습니다.

```bash
THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live \
THRESHOLD_CYCLE_AUTO_APPLY=true \
THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true \
./deploy/run_threshold_cycle_preopen.sh "$(TZ=Asia/Seoul date +%F)"
```

생성물:

- `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json`
- `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.env`
- `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.json`

### 10. 봇 실행

운영 wrapper는 당일 runtime env가 없으면 장전 apply 생성을 시도한 뒤 봇을 시작합니다.

```bash
cd src
bash run_bot.sh
```

직접 실행은 개발/점검 용도로만 사용합니다.

```bash
PYTHONPATH=. .venv/bin/python src/bot_main.py
```

### 11. Cron 설치

운영 자동화는 `deploy/install_*.sh` 스크립트로 설치합니다. 설치 전 서버 시간대가 `Asia/Seoul`인지 확인합니다.

```bash
./deploy/install_threshold_cycle_cron.sh
./deploy/install_error_detection_cron.sh
./deploy/install_stage2_ops_cron.sh
```

스윙 dry-run, panic report, pattern lab 등은 운영 범위에 맞춰 개별 install script를 사용합니다.

## 시스템 구성

1. 스캐너와 조건검색식이 감시 후보(WATCHING candidate)를 생성합니다.
2. 실시간 시세, 호가, 체결강도, 수급, AI 판단을 묶어 진입(entry) 후보를 평가합니다.
3. latency, 가격 품질, 유동성, AI score, 과열(overbought) 조건을 분리해 주문 또는 시뮬레이션/실주문 없는 추적관찰(sim/probe) 경로로 보냅니다.
4. 주문/체결 receipt와 position tag를 기준으로 `BUY_ORDERED`, `HOLDING`, `SELL_ORDERED`, `COMPLETED` 상태를 관리합니다.
5. 보유 중에는 hard/protect/emergency stop, soft stop, trailing, holding-flow AI review, scale-in/pyramid, bad-entry, overnight gate를 분리 판단합니다.
6. 장중/장후 pipeline event, threshold compact event, monitor snapshot, Sentinel, panic report, swing lifecycle audit를 source bundle로 모읍니다.
7. threshold-cycle 자동화체인이 다음 장전 적용 후보, approval summary, code-improvement workorder를 생성합니다.

## 자동화체인

| 단계 | 한글 의미 | 역할 | live 영향 |
| --- | --- | --- | --- |
| `R0_collect` | 수집 | pipeline event, threshold compact event, DB completed trade, monitor snapshot 수집 | 없음 |
| `R1_daily_report` | 일일 리포트 | Sentinel, panic, threshold, swing, system report 생성 | 없음 |
| `R2_cumulative_report` | 누적 리포트 | rolling/cumulative cohort와 owner baseline 생성 | 없음 |
| `R3_manifest_only` | 후보 목록화 | 후보 family와 source bundle 생성, env 미반영 | 없음 |
| `R4_preopen_apply_candidate` | 장전 적용 후보 | deterministic guard, AI correction, source-quality, same-stage owner rule 확인 | 직접 변경 전 단계 |
| `R5_bounded_calibrated_apply` | 제한 적용 | guard 통과 family만 다음 장전 runtime env에 반영 | 있음 |
| `R6_post_apply_attribution` | 적용 후 귀속 | selected/applied/not-applied cohort, daily EV, approval summary 생성 | 없음 |

자동화체인은 신규 관찰축을 무한히 늘리는 방식이 아니라 기존 source bundle을 재사용합니다. BUY 쪽은 `buy_funnel_sentinel`, `wait6579_ev_cohort`, 놓친 진입 복기(`missed_entry_counterfactual`), `performance_tuning`; 관리자 의사결정 모듈(ADM)과 lifecycle 쪽은 `lifecycle_decision_matrix`, `scalp_entry_action_decision_matrix`, `holding_exit_decision_matrix`, `sim_post_sell_evaluations`, `statistical_action_weight`; 보유/청산 쪽은 `holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`; 패닉 쪽은 `panic_sell_defense`, `panic_buying`을 우선 source로 씁니다.

## 의사결정 매트릭스와 한계값 역할

생애주기 의사결정 매트릭스 런타임(Lifecycle Decision Matrix Runtime)은 관리자 의사결정 모듈(ADM)을 확장하는 umbrella owner입니다. 개별 후보 lifecycle row를 `entry`, `submit`, `holding`, `scale_in`, `exit` stage별 weighted ADM policy로 해석합니다.

기존 고정 한계값(fixed threshold)은 삭제하지 않고 역할을 바꿉니다.

| 역할 | 대상 | 런타임 의미 |
| --- | --- | --- |
| 실주문 안전장치(hard safety) | broker submit guard, stale quote submit block, price freshness, hard/protect/emergency stop, 계좌/order/cooldown/qty guard | matrix나 ADM이 우회할 수 없음 |
| 기준 prior(baseline prior) | `BUY_SCORE_THRESHOLD`, entry score cutoff, VPW/strength/momentum 계열 | 후보 생성 feature로만 사용. score 단독 BUY/WAIT/DROP 확정 금지 |
| 제한 튜닝값(bounded tunable) | latency caution, score65_74 추적관찰(probe), soft stop/holding flow, scale-in price guard | bounds, max step, sample floor, source-quality gate 통과 시 다음 장전 env 후보 |
| 보관/폐기(legacy archive) | fallback scout/main, fallback single, latency fallback split-entry, legacy latency composite, closed shadow axes | runtime feature로도 쓰지 않음. 재개하려면 새 workorder와 rollback guard 필요 |

런타임 우선순위는 `hard safety veto -> account/order/broker guard -> lifecycle matrix runtime policy -> existing ADM adapter -> baseline fixed threshold fallback`입니다.

## 스캘핑

| 영역 | 현재 기준 |
| --- | --- |
| 진입(entry) | AI score는 feature입니다. score가 높을수록 EV가 단조 증가한다는 가정은 사용하지 않습니다. score 50 fallback/neutral은 신규 BUY 제출로 내려보내지 않고 `blocked_ai_score`로 보류합니다. |
| 가격(entry price) | `dynamic_entry_price_resolver_p1`과 `dynamic_entry_ai_price_canary_p2`가 entry price 품질을 담당합니다. stale quote, spread, 대기형 추적관찰(passive probe) 가격 문제는 broker 제출 전 차단합니다. |
| 제출(submit) | latency/source freshness/price guard를 보되 hard safety와 broker guard가 항상 우선합니다. |
| 보유/청산(holding/exit) | `soft_stop_micro_grace`, `soft_stop_whipsaw_confirmation`, `holding_flow_override`, `holding_exit_matrix_runtime_bias_p1`는 hard/protect/emergency/order safety를 우회하지 않습니다. |
| 추가매수/수량(scale-in/position sizing) | scale-in price resolver와 dynamic qty safety를 유지합니다. 신규/추가매수 1주 cap 해제는 `position_sizing_cap_release` approval request 이후 사용자 승인으로만 다룹니다. |

## 스윙

스윙은 dry-run self-improvement 체인입니다. `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` lifecycle을 장후 감사하고, approval request는 생성할 수 있지만 별도 approval artifact 없이는 runtime env 또는 live order 전환으로 보지 않습니다.

주요 산출물:

- `swing_selection_funnel`
- `swing_daily_simulation`
- `swing_lifecycle_audit`
- `swing_threshold_ai_review`
- `swing_improvement_automation`
- `swing_runtime_approval`
- `swing_pattern_lab_automation`

one-share real canary와 scale-in real canary는 별도 approval-required 축입니다. 전체 스윙 실주문 전환으로 해석하지 않습니다.

## 시뮬레이션과 추적관찰

실주문 가능 여부, 예수금, 1주 cap, 현재 selected family 여부는 시뮬레이션/실주문 없는 추적관찰(sim/probe) 후보 제외 사유가 아닙니다. 대신 provenance tag로 남겨 real/sim/combined를 분리합니다.

| 축 | 설명 | 금지선 |
| --- | --- | --- |
| 스캘핑 BUY 전체 관측(`scalp_ai_buy_all`) | 스캘핑 BUY 후보를 실주문 없이 lifecycle로 추적 | real execution 품질이나 실주문 전환 근거로 단독 사용 금지 |
| 놓친 진입 복기(missed-entry counterfactual) | latency, liquidity, AI threshold, overbought gate 때문에 진입하지 못한 경우를 사후 비교 | 실제 체결 손익과 합산 금지 |
| 스윙 dry-run | 추천부터 entry, holding, scale-in, exit, attribution까지 dry-run으로 실행 | approval artifact 없는 실주문 전환 금지 |
| 스윙 실주문 없는 실전형 추적관찰(live-equivalent probe) | blocked candidate도 `actual_order_submitted=false` virtual holding으로 관찰 | broker order 품질로 해석 금지 |
| 패닉 상황 복기(counterfactual) | panic sell defense, panic buying runner TP 가능성을 source bundle에 고정 | 자동매도, 추격매수, TP/trailing 변경 금지 |

## 패닉 리스크 레짐

패닉 신호는 현재 매매 로직을 즉시 덮어쓰는 alpha signal이 아닙니다. 리스크 레짐(risk regime) 상태를 report-only로 분리해 workorder, approval request, runtime approval summary에 전달합니다.

| 리포트 | 상태 흐름 | 후보 |
| --- | --- | --- |
| 패닉셀 방어(`panic_sell_defense`) | `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` | `panic_entry_freeze_guard`, scalping `entry_pre_submit` 신규 BUY 차단 후보 |
| 패닉바잉(`panic_buying`) | `NORMAL -> PANIC_BUY_DETECTED -> PANIC_BUY_CONTINUATION -> PANIC_BUY_EXHAUSTION -> COOLDOWN` | `panic_buy_runner_tp_canary`, 기존 보유분 TP/runner 후보 |

미체결 진입 주문 cancel, holding/exit panic context, 강제 축소/청산, 추격매수 차단, continuation trailing, exhaustion cleanup, cooldown reentry guard는 각각 별도 owner, approval artifact, rollback guard가 필요합니다.

## 코드 구조

```text
KORStockScan/
├── src/
│   ├── bot_main.py                         # 운영 루프, 봇 진입점
│   ├── run_bot.sh                          # runtime env source 후 봇 실행
│   ├── engine/                             # 매매 엔진, AI, 리포트, 자동화 CLI
│   ├── trading/                            # entry/orderbook 관련 로직
│   ├── scanners/                           # 스캐너, 장전/장후 후보 분석
│   ├── web/                                # Flask 대시보드/API
│   ├── database/                           # DB manager와 모델
│   ├── model/                              # ML dataset/training/recommendation
│   ├── market_regime/                      # 시장 레짐 데이터/룰/서비스
│   ├── notify/                             # Telegram 등 알림
│   ├── utils/                              # constants, runtime flags, event logger
│   └── tests/                              # pytest 회귀 테스트
├── analysis/                               # offline bundle, pattern lab, 관찰 분석
├── data/
│   ├── pipeline_events/                    # runtime pipeline event JSONL
│   ├── threshold_cycle/                    # compact stream, apply plan, runtime env
│   ├── report/                             # daily/monitor/threshold/swing 리포트
│   ├── runtime/                            # runtime flag/state artifacts
│   └── config/                             # feature/threshold manifest
├── deploy/                                 # cron, systemd, nginx, 운영 wrapper
├── docs/                                   # Plan Rebase, checklist, workorder, runbook
└── logs/                                   # 운영 로그
```

## 핵심 모듈

| 모듈 | 역할 |
| --- | --- |
| `src/bot_main.py` | 메인 운영 루프 |
| `src/engine/kiwoom_sniper_v2.py` | 스캘핑 엔진 본체와 Kiwoom runtime orchestration |
| `src/engine/sniper_state_handlers.py` | WATCHING/HOLDING/SELL 상태 처리 |
| `src/engine/sniper_entry_latency.py` | latency gate, entry price guard |
| `src/engine/sniper_scale_in.py` | REVERSAL_ADD, PYRAMID, scale-in blocker와 attribution |
| `src/engine/sniper_execution_receipts.py` | 주문/체결 receipt binding |
| `src/engine/ai_engine_openai.py` | OpenAI schema, transport, Responses WS 경로 |
| `src/engine/lifecycle_decision_matrix.py` | lifecycle row matrix와 weighted ADM policy artifact |
| `src/engine/lifecycle_decision_matrix_runtime.py` | stage별 lifecycle runtime resolver |
| `src/engine/daily_threshold_cycle_report.py` | threshold source bundle과 calibration report 생성 |
| `src/engine/threshold_cycle_preopen_apply.py` | 장전 apply plan과 runtime env 생성 |
| `src/engine/threshold_cycle_ev_report.py` | daily EV와 post-apply attribution |
| `src/engine/runtime_approval_summary.py` | 스캘핑/스윙/패닉 approval 상태 요약 |
| `src/engine/build_code_improvement_workorder.py` | 자동화 산출물 기반 code-improvement 작업지시 생성 |
| `src/engine/swing_lifecycle_audit.py` | 스윙 lifecycle audit와 improvement source |
| `src/engine/error_detector.py` | 운영 감시 detector 실행 |
| `src/web/app.py` | Flask dashboard와 JSON API |

## 주요 산출물

| 경로 | 내용 |
| --- | --- |
| `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` | runtime pipeline event stream |
| `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | threshold compact event stream |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | threshold cycle canonical report |
| `data/report/threshold_cycle_calibration/` | 장중/장후 calibration artifact |
| `data/report/threshold_cycle_ai_review/` | AI correction proposal와 deterministic guard 결과 |
| `data/report/lifecycle_decision_matrix/` | lifecycle row, fixed threshold contract, weighted ADM policy artifact |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | 다음 장전 apply plan |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}` | guard 통과 runtime env |
| `data/report/threshold_cycle_ev/` | daily EV, selected/applied/not-applied attribution |
| `data/report/runtime_approval_summary/` | runtime approval 상태 요약 |
| `data/report/panic_sell_defense/` | 패닉셀 source bundle |
| `data/report/panic_buying/` | 패닉바잉 source bundle |
| `data/report/swing_*` | 스윙 selection/simulation/lifecycle/approval 산출물 |
| `docs/code-improvement-workorders/` | Codex 구현 지시용 workorder |
| `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md` | 장전/장중/장후 판정/승인/운영 체크리스트 |
| `data/report/error_detection/` | System Error Detector 결과 |

JSON/JSONL이 canonical data입니다. 사람이 장후 판정에 바로 읽어야 하는 항목만 Markdown report로 별도 생성합니다. report inventory는 [data/report/README.md](data/report/README.md)를 봅니다.

## 운영 자동화

| 자동화 | 경로 | 설명 |
| --- | --- | --- |
| threshold PREOPEN | `deploy/run_threshold_cycle_preopen.sh` | 전일 report/AI correction guard 기반 `auto_bounded_live` apply plan과 runtime env 생성 |
| threshold INTRADAY calibration | `deploy/run_threshold_cycle_calibration.sh` | 장중 calibration/AI correction artifact 생성. runtime mutation 없음 |
| threshold POSTCLOSE | `deploy/run_threshold_cycle_postclose.sh` | calibration, cumulative, AI review, ADM/lifecycle matrix, swing/scalping automation, workorder, daily EV, checklist 생성 |
| panic sell/buy intraday | `deploy/run_panic_sell_defense_intraday.sh`, `deploy/run_panic_buying_intraday.sh` | panic risk-regime report-only source 생성 |
| swing live dry-run POSTCLOSE | `deploy/run_swing_live_dry_run_report.sh` | 스윙 selection funnel, lifecycle audit, AI review, improvement automation 생성 |
| tuning monitoring POSTCLOSE | `deploy/run_tuning_monitoring_postclose.sh` | Parquet/DuckDB refresh와 tuning monitoring |
| nightly KOSPI update | `src/utils/update_kospi.py` | 야간 원천 DB 업데이트와 status JSON 생성 |
| monitor snapshot | `deploy/run_monitor_snapshot_safe.sh`, `deploy/run_monitor_snapshot_incremental_cron.sh` | 장중/장후 snapshot 생성 |
| system error detector | `deploy/run_error_detection.sh full` | process/cron/log/artifact/resource/stale-lock 감시 |
| Project/Calendar sync | `src.engine.sync_docs_backlog_to_project`, `src.engine.sync_github_project_calendar` | checklist backlog와 일정 동기화 |

신규 recurring job, report artifact, daemon/thread를 추가하면 detector coverage도 같은 변경 세트에 포함합니다.

## 주요 API

| 경로 | 용도 |
| --- | --- |
| `GET /api/daily-report?date=YYYY-MM-DD` | 일일 리포트 JSON |
| `GET /api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10` | 진입 퍼널/blocked flow |
| `GET /api/gatekeeper-replay?date=YYYY-MM-DD&code=000000&time=HH:MM:SS` | gatekeeper 판단 복원 |
| `GET /api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS` | 튜닝/성과 snapshot |
| `GET /api/post-sell-feedback?date=YYYY-MM-DD` | 매도 후 missed upside/good exit 평가 |
| `GET /api/strategy-performance?date=YYYY-MM-DD` | 전략/포지션 성과 |
| `GET /api/trade-review?date=YYYY-MM-DD&code=000000` | 거래 리뷰 |
| `GET /api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10` | strength/momentum 분석 |

HTML 대시보드 경로는 `/`, `/dashboard`, `/daily-report`, `/entry-pipeline-flow`, `/gatekeeper-replay`, `/performance-tuning`, `/post-sell-feedback`, `/strategy-performance`, `/trade-review`, `/strength-momentum`입니다.

## 문서와 동기화

문서 변경 후 checklist parser 검증은 AI가 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

GitHub Project / Google Calendar 동기화는 사용자가 아래 표준 명령으로 수동 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 핵심 문서

| 문서 | 역할 |
| --- | --- |
| [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md) | 현재 튜닝 원칙, active/open 상태, 금지선 |
| [Report Automation Traceability](docs/report-based-automation-traceability.md) | R0~R6 ladder, source bundle, metric decision contract |
| [Threshold Cycle README](data/threshold_cycle/README.md) | threshold collector/report/apply plan/runtime env 운영방법 |
| [Time-Based Operations Runbook](docs/time-based-operations-runbook.md) | cron/window별 운영 확인 기준 |
| [Data Report README](data/report/README.md) | 정기 report inventory |
| 날짜별 `stage2-todo-checklist` | 장전/장중/장후 실행 항목과 Project/Calendar 동기화 source |

## 면책

이 프로젝트는 개인 자동매매/리서치 운영 코드입니다. 실계좌 주문, API key, 계좌 권한, 주문가능금액, 세금/수수료, 거래소/브로커 장애는 사용자가 직접 관리해야 합니다. README와 리포트는 투자 조언이 아니며, 실주문 전환은 항상 approval artifact, rollback guard, runtime owner, source-quality gate를 확인한 뒤에만 다룹니다.
