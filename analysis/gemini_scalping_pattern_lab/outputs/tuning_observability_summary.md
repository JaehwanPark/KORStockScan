# Tuning Observability Summary

- target_date: `2026-05-28`
- analysis_period: `2026-04-21 ~ 2026-05-28`

## Entry Funnel

- gatekeeper_decisions: `5311`
- gatekeeper_eval_ms_p95: `3612ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `4090ms`
- budget_pass_events: `20927`
- submitted_events: `2`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `20790`
- quote_fresh_latency_blocks: `11687`

## Buy Recovery Canary

- total_candidates: `96`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `79.2%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=79.2%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
