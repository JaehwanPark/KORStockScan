# Tuning Observability Summary

- target_date: `2026-08-11`
- analysis_period: `2026-06-05 ~ 2026-08-11`

## Entry Funnel

- gatekeeper_decisions: `0`
- gatekeeper_eval_ms_p95: `0ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `145`
- submitted_events: `0`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `113`
- quote_fresh_latency_blocks: `113`

## Buy Recovery Canary

- total_candidates: `10`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `50.0%`

## Priority Findings

- `Budget pass without submit`: 경고 — `budget_pass=145`인데 `submitted=0`라 제출 전 병목이 기대값 회복을 끊고 있다.
