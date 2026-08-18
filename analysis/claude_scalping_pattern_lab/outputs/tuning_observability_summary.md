# Tuning Observability Summary

- target_date: `2026-08-18`
- analysis_period: `2026-06-05 ~ 2026-08-18`

## Entry Funnel

- gatekeeper_decisions: `0`
- gatekeeper_eval_ms_p95: `0ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `728`
- submitted_events: `2`
- budget_pass_to_submitted_rate: `0.3%`
- latency_block_events: `461`
- quote_fresh_latency_blocks: `450`

## Buy Recovery Canary

- total_candidates: `11`
- recovery_check: `0`
- promoted: `0`
- submitted: `1`
- blocked_ai_score_share: `81.8%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=81.8%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
