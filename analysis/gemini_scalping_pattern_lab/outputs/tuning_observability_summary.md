# Tuning Observability Summary

- target_date: `2026-05-26`
- analysis_period: `2026-04-21 ~ 2026-05-26`

## Entry Funnel

- gatekeeper_decisions: `30`
- gatekeeper_eval_ms_p95: `5831ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `5831ms`
- budget_pass_events: `2706`
- submitted_events: `23`
- budget_pass_to_submitted_rate: `0.8%`
- latency_block_events: `2389`
- quote_fresh_latency_blocks: `1611`

## Buy Recovery Canary

- total_candidates: `163`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `79.8%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=79.8%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
