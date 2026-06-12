# Tuning Observability Summary

- target_date: `2026-06-12`
- analysis_period: `2026-06-04 ~ 2026-06-12`

## Entry Funnel

- gatekeeper_decisions: `2204`
- gatekeeper_eval_ms_p95: `4132ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `4141ms`
- budget_pass_events: `7701`
- submitted_events: `24`
- budget_pass_to_submitted_rate: `0.3%`
- latency_block_events: `7592`
- quote_fresh_latency_blocks: `1083`

## Buy Recovery Canary

- total_candidates: `76`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `28.9%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
