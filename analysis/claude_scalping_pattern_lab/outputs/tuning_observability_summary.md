# Tuning Observability Summary

- target_date: `2026-06-23`
- analysis_period: `2026-06-04 ~ 2026-06-23`

## Entry Funnel

- gatekeeper_decisions: `87`
- gatekeeper_eval_ms_p95: `4306ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `4306ms`
- budget_pass_events: `1027`
- submitted_events: `2`
- budget_pass_to_submitted_rate: `0.2%`
- latency_block_events: `953`
- quote_fresh_latency_blocks: `138`

## Buy Recovery Canary

- total_candidates: `23`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `39.1%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
