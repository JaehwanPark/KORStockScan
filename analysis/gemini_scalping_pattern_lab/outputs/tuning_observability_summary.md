# Tuning Observability Summary

- target_date: `2026-06-04`
- analysis_period: `2026-04-21 ~ 2026-06-04`

## Entry Funnel

- gatekeeper_decisions: `829`
- gatekeeper_eval_ms_p95: `3431ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `3700ms`
- budget_pass_events: `4444`
- submitted_events: `1`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `4418`
- quote_fresh_latency_blocks: `2412`

## Buy Recovery Canary

- total_candidates: `2`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `50.0%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
