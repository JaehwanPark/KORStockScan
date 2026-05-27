# Tuning Observability Summary

- target_date: `2026-05-27`
- analysis_period: `2026-04-21 ~ 2026-05-27`

## Entry Funnel

- gatekeeper_decisions: `1091`
- gatekeeper_eval_ms_p95: `4007ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `4084ms`
- budget_pass_events: `37059`
- submitted_events: `13`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `36812`
- quote_fresh_latency_blocks: `19254`

## Buy Recovery Canary

- total_candidates: `130`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `61.5%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
