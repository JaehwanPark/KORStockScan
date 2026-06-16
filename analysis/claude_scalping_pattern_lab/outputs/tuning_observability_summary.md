# Tuning Observability Summary

- target_date: `2026-06-16`
- analysis_period: `2026-06-04 ~ 2026-06-16`

## Entry Funnel

- gatekeeper_decisions: `3180`
- gatekeeper_eval_ms_p95: `3756ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `3906ms`
- budget_pass_events: `8757`
- submitted_events: `3`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `8649`
- quote_fresh_latency_blocks: `3640`

## Buy Recovery Canary

- total_candidates: `133`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `79.7%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=79.7%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
