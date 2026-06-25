# BUY Funnel Sentinel 2026-06-25

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `PRICE_GUARD_DROUGHT, LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-25T15:20:03`
- baseline_date: `2026-06-24`
- ai_confirmed unique: `60`
- budget_pass unique: `14`
- latency_pass unique: `6`
- submitted unique: `3`
- holding_started unique: `2`
- budget/ai unique: `23.3%` (baseline `25.9`)
- submitted/ai unique: `5.0%` (baseline `8.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=421, blocked_strength_momentum:below_strength_base=339, blocked_liquidity:-=262, first_ai_wait:-=235, blocked_ai_score:score_62.0=198`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=235, blocked_ai_score:score_62.0=198, blocked_ai_score:ai_score_50_buy_hold_override=179, blocked_ai_score:score_60.0=27, blocked_ai_score:score_58.0=23`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=311, ai_terminal:first_ai_wait_big_bite_not_confirmed=235`
- latency blockers: `latency_block:latency_state_danger=15`
- price guards: `entry_ai_price_canary_fallback:invalid_price=59, scale_in_price_guard_block:micro_vwap_bp>60.0=1, entry_ai_price_canary_fallback:pre_submit_price_guard=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish, indicating unfavorable submission conditions=1`
- quote refresh: `attempted=14, applied=12, latency_recovered=6, submitted_after_refresh=2`
- quote refresh downstream: `{'armed_expired_before_submit': 2, 'order_bundle_submitted': 2, 'upstream_block_after_latency_recovery': 2}`

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

- `5m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_liquidity:-=4, blocked_overbought:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=4, first_ai_wait:-=2, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=2, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `10m`: ai=8, budget=0, latency=0, submitted=0, top=`blocked_liquidity:-=9, first_ai_wait:-=8, entry_ai_price_canary_fallback:invalid_price=5`, swing=`-`, upstream=`first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=8, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `30m`: ai=16, budget=1, latency=1, submitted=0, top=`first_ai_wait:-=23, blocked_liquidity:-=22, blocked_ai_score:ai_score_50_buy_hold_override=12`, swing=`-`, upstream=`first_ai_wait:-=23, blocked_ai_score:ai_score_50_buy_hold_override=12, blocked_ai_score:score_62.0=10`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=23, ai_terminal:blocked_ai_score_below_buy_score_threshold=13`
