# 2026-06-02 Stage2 To-Do Checklist

## 오늘 목적

- 진입/보유/청산 AI input v2 rollout의 Stage 1을 문서와 테스트 기준으로 닫는다.
- `entry_screen_v2`, `entry_price_v2`, `holding_flow_v2` builder와 bounded refresh flag가 runtime disabled 상태인지 확인한다.
- provider route, threshold, broker/order guard, quantity, bot restart 변경 없이 offline replay 준비물만 확정한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 수동 롤아웃 체크리스트: 진입/보유/청산 AI input v2

- [ ] `[AIInputV2Stage1SurfaceGate0602] Stage 1 disabled runtime surface 및 contract provenance 확인` (`Due: 2026-06-02`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:50`, `Track: AIPrompt`)
  - Source: [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [test_ai_engine_openai_transport.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_openai_transport.py)
  - IN scope: v2 input builders, input contract metadata, disabled-by-default flags, call-policy guard tests, parser-friendly rollout checklist presence.
  - OUT scope: provider route change, threshold/order/quantity guard change, bot restart, live runtime enablement.
  - Acceptance: targeted tests pass, v2 flags default OFF, `ai_input_schema`/`ai_input_contract_mode` metadata is present on success and fallback paths, compact/current route contracts remain unchanged when v2 flags are OFF.
  - Go/no-go: pass이면 Stage 2 offline replay로 진행한다. fail이면 `stage1_blocked_contract_or_test_gap`로 닫고 Stage 2 checklist를 carry-over 수정한다.

- [ ] `[AIInputV2ReplayCasePlan0602] Stage 2 offline replay 표본군과 report-only 산출물 계약 확정` (`Due: 2026-06-02`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: AIPrompt`)
  - Source: [pipeline_events_2026-06-02.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-02.jsonl), [threshold_cycle_ev_2026-06-02.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)
  - IN scope: current vs v2 input generation, output parse status, latency, token/char estimate, decision delta, source-quality tags.
  - OUT scope: live order submission, runtime env mutation, provider/bot restart, threshold apply.
  - Acceptance: replay case set includes entry chase/stale submit/negative EV/missed positive outcome and holding defer_exit/force_exit/missed_upside/good_exit categories where source data exists.
  - Go/no-go: source data가 충분하면 Stage 2 replay 실행으로 진행한다. 부족하면 `stage2_source_quality_blocked`로 닫고 필요한 artifact gap을 workorder 후보로 남긴다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
