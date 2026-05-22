# Tuning Observability Summary

- target_date: `2026-05-22`
- analysis_period: `2026-04-21 ~ 2026-05-22`

## Entry Funnel

- gatekeeper_decisions: `105`
- gatekeeper_eval_ms_p95: `5221ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `5220ms`
- budget_pass_events: `92`
- submitted_events: `0`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `82`
- quote_fresh_latency_blocks: `30`

## Buy Recovery Canary

- total_candidates: `35`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `74.3%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=74.3%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Budget pass without submit`: 경고 — `budget_pass=92`인데 `submitted=0`라 제출 전 병목이 기대값 회복을 끊고 있다.
