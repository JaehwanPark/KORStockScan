# Tuning Observability Summary

- target_date: `2026-05-29`
- analysis_period: `2026-04-21 ~ 2026-05-29`

## Entry Funnel

- gatekeeper_decisions: `2944`
- gatekeeper_eval_ms_p95: `3582ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `3713ms`
- budget_pass_events: `16148`
- submitted_events: `7`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `16003`
- quote_fresh_latency_blocks: `10837`

## Buy Recovery Canary

- total_candidates: `81`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `72.8%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=72.8%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
