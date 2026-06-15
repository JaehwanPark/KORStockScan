# Tuning Observability Summary

- target_date: `2026-06-15`
- analysis_period: `2026-04-20 ~ 2026-06-15`

## Entry Funnel

- gatekeeper_decisions: `3023`
- gatekeeper_eval_ms_p95: `3631ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `3768ms`
- budget_pass_events: `6131`
- submitted_events: `2`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `6050`
- quote_fresh_latency_blocks: `2539`

## Buy Recovery Canary

- total_candidates: `47`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `59.6%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
