# BUY Funnel Sentinel 2026-06-26

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-26T15:20:03`
- baseline_date: `2026-06-25`
- ai_confirmed unique: `78`
- budget_pass unique: `22`
- latency_pass unique: `10`
- submitted unique: `6`
- holding_started unique: `4`
- budget/ai unique: `28.2%` (baseline `23.3`)
- submitted/ai unique: `7.7%` (baseline `5.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_liquidity:-=420, blocked_ai_score:score_62.0=259, blocked_strength_momentum:below_strength_base=255, first_ai_wait:-=208, blocked_vpw:-=204`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:score_62.0=259, first_ai_wait:-=208, blocked_ai_score:ai_score_50_buy_hold_override=139, blocked_ai_score:score_58.0=41, blocked_ai_score:score_60.0=34`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=411, ai_terminal:first_ai_wait_big_bite_not_confirmed=208`
- latency blockers: `latency_block:latency_state_danger=14, latency_block:quote_fresh_composite_orderbook_micro_block=1`
- price guards: `entry_ai_price_canary_fallback:invalid_price=68, scale_in_price_guard_block:micro_vwap_bp>60.0=1, scale_in_price_guard_block:invalid_quote=1`
- quote refresh: `attempted=22, applied=20, latency_recovered=10, submitted_after_refresh=6`
- quote refresh downstream: `{'armed_expired_before_submit': 2, 'no_downstream_event': 1, 'order_bundle_submitted': 6, 'upstream_block_after_latency_recovery': 1}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Auto-route ai_confirmed -> budget_pass -> latency_pass -> order_bundle_submitted drought into postclose workorder/LDM handoff.
- Split root cause into upstream gate, budget pass, latency/pre-submit guard, and broker receipt buckets before tuning thresholds.
- Do not require operator approval for submitted drought surfacing or downstream workorder generation.

## Window Summary

- `5m`: ai=8, budget=0, latency=0, submitted=0, top=`blocked_liquidity:-=5, blocked_ai_score:score_62.0=3, first_ai_wait:-=3`, swing=`-`, upstream=`blocked_ai_score:score_62.0=3, first_ai_wait:-=3, blocked_ai_score:score_60.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `10m`: ai=10, budget=0, latency=0, submitted=0, top=`blocked_liquidity:-=10, blocked_strength_momentum:below_strength_base=6, blocked_ai_score:score_62.0=5`, swing=`-`, upstream=`blocked_ai_score:score_62.0=5, first_ai_wait:-=5, blocked_ai_score:score_60.0=3`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
- `30m`: ai=15, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=25, blocked_liquidity:-=24, first_ai_wait:-=13`, swing=`-`, upstream=`first_ai_wait:-=13, blocked_ai_score:score_62.0=12, blocked_ai_score:ai_score_50_buy_hold_override=10`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=17, ai_terminal:first_ai_wait_big_bite_not_confirmed=13`
