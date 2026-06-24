# Tuning Observability Summary

- target_date: `2026-06-24`
- analysis_period: `2026-06-04 ~ 2026-06-24`

## Entry Funnel

- gatekeeper_decisions: `0`
- gatekeeper_eval_ms_p95: `0ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `99`
- submitted_events: `8`
- budget_pass_to_submitted_rate: `8.1%`
- latency_block_events: `80`
- quote_fresh_latency_blocks: `53`

## Buy Recovery Canary

- total_candidates: `77`
- recovery_check: `0`
- promoted: `0`
- submitted: `2`
- blocked_ai_score_share: `41.6%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
