# 2026-06-03 Stage2 To-Do Checklist

## 오늘 목적

- Stage 2 offline replay를 실행해 current input과 v2 input의 입력/출력/parse/latency/decision delta를 비교한다.
- 결과는 report-only로만 남기고 live provider route, threshold, order guard, bot state는 유지한다.
- Stage 3 `entry_price_v2` report-only comparison audit 진입 여부를 go/no-go로 닫는다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[AIInputV2OfflineReplay0603] Stage 2 current vs v2 offline replay 실행 및 report-only 결과 확인` (`Due: 2026-06-03`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:50`, `Track: AIPrompt`)
  - Source: [pipeline_events_2026-06-03.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-03.jsonl), [threshold_cycle_ev_2026-06-03.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-03.json), [openai_ws_stability_2026-06-03.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-03.md)
  - IN scope: analyze_target, entry_price, holding_flow input comparison; model output parse status; latency p95; payload mean char/token estimate; decision delta by category.
  - OUT scope: runtime v2 enablement, provider route change, threshold/order/quantity guard change, bot restart.
  - Acceptance: parse success >=99%, duplicate AI call count is zero by candidate policy, p95 latency degradation <=20% or explicitly explained, payload average char increase <=20% unless decision-quality evidence justifies enrichment.
  - Go/no-go: pass이면 Stage 3 `entry_price_v2` report-only comparison audit 준비로 진행한다. fail이면 `stage2_replay_blocked`로 닫고 failing stage/category를 Stage 2 보완 항목으로 carry over한다.

- [ ] `[EntryPriceV2ReportOnlyReadiness0603] Stage 3 entry_price_v2 report-only comparison audit 준비상태 확인` (`Due: 2026-06-03`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:05`, `Track: AIPrompt`)
  - Source: [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)
  - IN scope: `entry_price_v2` report-only audit field names, current result remains runtime authority, same-candidate refresh maximum one-call guard.
  - OUT scope: replacing submitted order price with v2 output, extra OpenAI fallback for entry_price, broker guard relaxation.
  - Acceptance: report-only audit clearly records current result, v2 result, parse/latency/token estimate, stale/chase/negative-EV category, and `runtime_effect=false`.
  - Go/no-go: readiness pass이면 2026-06-04 Stage 3 실행 항목을 유지한다. fail이면 Stage 3 실행을 `blocked_by_report_contract_gap`로 변경한다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
