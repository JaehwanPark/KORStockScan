# 2026-06-04 Stage2 To-Do Checklist

## 오늘 목적

- Stage 3 `entry_price_v2` report-only comparison audit를 실행하고 current runtime result와 v2 result를 비교한다.
- 실제 주문가는 기존 current 결과만 사용한다.
- Stage 4 `entry_price` runtime input 전환 여부를 postclose 기준으로만 판정한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[EntryPriceV2ReportOnlyAudit0604] Stage 3 entry_price_v2 report-only comparison audit 결과 확인` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:50`, `Track: AIPrompt`)
  - Source: [pipeline_events_2026-06-04.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-04.jsonl), [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json), [openai_ws_stability_2026-06-04.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-06-04.md)
  - IN scope: `entry_price` current vs v2 output delta, chase bps, stale submit block, negative EV bucket, parse success, latency, Bedrock failback provenance.
  - OUT scope: runtime authority transfer to v2, threshold/order/quantity guard change, provider route change, bot restart.
  - Acceptance: v2 improves or does not degrade chase/negative-EV category, parse success >=99%, p95 latency degradation <=20%, duplicate-call guard holds, current runtime output remains the only submitted price source.
  - Go/no-go: pass이면 Stage 4 runtime input 전환 후보를 `go_candidate`로 둔다. fail이면 `stage3_report_only_reject_or_rework`로 닫고 v2 runtime enablement를 금지한다.

- [ ] `[EntryPriceV2RuntimeSwitchDecision0604] Stage 4 entry_price runtime input 전환 go/no-go 판정` (`Due: 2026-06-04`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: AIPrompt`)
  - Source: [2026-06-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-06-04-stage2-todo-checklist.md), [threshold_cycle_ev_2026-06-04.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json)
  - IN scope: enabling only `entry_price_v2` runtime input after report-only pass, preserving Qwen3 32B primary -> Nova Lite v2 failback -> defensive fallback.
  - OUT scope: `analyze_target` or `holding_flow` runtime input switch, provider route change, broker/order guard relaxation, threshold mutation.
  - Acceptance: Stage 2 and Stage 3 both pass, rollback flag is documented, audit provenance distinguishes `ai_input_schema=entry_price_v2`, and submit-before-broker revalidation remains active.
  - Go/no-go: pass이면 next PREOPEN bounded env 후보로만 넘긴다. fail이면 `entry_price_v2_runtime_switch_blocked`로 닫는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
