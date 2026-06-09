# Tuning Observability Summary

- target_date: `2026-06-09`
- analysis_period: `2026-06-04 ~ 2026-06-09`

## Entry Funnel

- gatekeeper_decisions: `3403`
- gatekeeper_eval_ms_p95: `3625ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `3734ms`
- budget_pass_events: `5169`
- submitted_events: `2`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `5140`
- quote_fresh_latency_blocks: `1776`

## Buy Recovery Canary

- total_candidates: `114`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `90.4%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=90.4%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
