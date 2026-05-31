# 2026-06-05 Stage2 To-Do Checklist

## 오늘 목적

- Stage 4 `entry_price_v2` runtime input 전환 결과를 post-apply attribution으로 확인한다.
- Stage 5 `holding_flow_v2`와 `entry_screen_v2`는 순차 후보로만 판정하고 동시 runtime enablement를 금지한다.
- 다음 영업일로 넘길 항목은 go/no-go, blocker, rollback guard, artifact source를 명시한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[EntryPriceV2PostApplyAttribution0605] Stage 4 entry_price_v2 runtime input post-apply attribution 확인` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:45`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [runtime_approval_summary_2026-06-05.md](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-05.md), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl)
  - IN scope: entry_price v2 input provenance, parse/fallback rate, latency, chase bps, stale submit block, negative EV category, duplicate refresh count.
  - OUT scope: provider route change, threshold/order/quantity guard change, holding/analyze runtime input switch, bot restart.
  - Acceptance: no duplicate-call regression, Bedrock failback chain remains Qwen3 32B -> Nova Lite v2 -> defensive fallback, p95 latency and parse rate stay within Stage 4 acceptance, post-apply attribution artifact can separate input effect from threshold/order guard effect.
  - Go/no-go: pass이면 Stage 5 후보 검토로 진행한다. fail이면 rollback flag를 next PREOPEN 후보로 남기고 `entry_price_v2_rollback_candidate`로 닫는다.

- [ ] `[HoldingFlowV2SequentialDecision0605] Stage 5 holding_flow_v2 순차 rollout 후보 판정` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~18:05`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl), [test_holding_flow_override.py](/home/ubuntu/KORStockScan/src/tests/test_holding_flow_override.py)
  - IN scope: holding_flow current vs v2 replay/report-only candidate, HOLD/TRIM early review state-change policy, hard/protect/emergency/order/account/cooldown/quantity guard precedence.
  - OUT scope: simultaneous `analyze_target` v2 runtime switch, forced exit rule change, score cutoff change, provider route change.
  - Acceptance: hard guard precedence is unchanged, parse success >=99%, stale/parse failure remains fail-closed, HOLD/TRIM early review triggers at most one bounded review per state-change window.
  - Go/no-go: pass이면 next trading day checklist에 report-only Stage 5 execution item을 create/keep한다. fail이면 `holding_flow_v2_rework_required`로 닫는다.

- [ ] `[EntryScreenV2SequentialDecision0605] Stage 5 entry_screen_v2 순차 rollout 후보 판정` (`Due: 2026-06-05`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: AIPrompt`)
  - Source: [threshold_cycle_ev_2026-06-05.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json), [pipeline_events_2026-06-05.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-05.jsonl), [test_ai_engine_openai_transport.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_openai_transport.py)
  - IN scope: analyze_target `entry_screen_v2` replay/report-only candidate, state-change early refresh one-per-cooldown guard, BUY/WAIT/DROP-only prompt boundary.
  - OUT scope: order price decision, provider route change, score threshold mutation, Telegram BUY alert expansion, broker guard relaxation.
  - Acceptance: cooldown duplicate-call guard holds, state-change trigger reason is audited, prompt does not decide price/quantity/holding/exit, output schema remains `entry_v1`.
  - Go/no-go: pass이면 holding_flow와 별도 날짜에만 sequential rollout로 넘긴다. fail이면 `entry_screen_v2_rework_required`로 닫는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
