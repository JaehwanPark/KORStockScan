# BUY Funnel Sentinel 2026-07-02

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

- as_of: `2026-07-02T11:10:01`
- baseline_date: `2026-07-01`
- ai_confirmed unique: `25`
- budget_pass unique: `10`
- latency_pass unique: `5`
- submitted unique: `4`
- holding_started unique: `3`
- budget/ai unique: `40.0%` (baseline `105.6`)
- submitted/ai unique: `16.0%` (baseline `88.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:insufficient_history=60, blocked_strength_momentum:below_strength_base=54, blocked_strength_momentum:below_window_buy_value=40, blocked_liquidity:-=27, first_ai_wait:-=22`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=22, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_62.0=4, wait65_79_ev_candidate:score_74.0=4, blocked_ai_score:score_63.0=3`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=22, ai_terminal:blocked_ai_score_below_buy_score_threshold=12`
- latency blockers: `latency_block:latency_state_danger=14`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=4, scale_in_price_guard_block:quote_stale=1`
- quote refresh: `attempted=10, applied=7, latency_recovered=3, submitted_after_refresh=2`
- quote refresh downstream: `{'no_downstream_event': 1, 'order_bundle_submitted': 2}`

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

- `5m`: ai=5, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=10, blocked_strength_momentum:insufficient_history=8, first_ai_wait:-=7`, swing=`-`, upstream=`first_ai_wait:-=7, blocked_ai_score:score_67.0=1, blocked_ai_score:score_66.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=7, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `10m`: ai=8, budget=1, latency=0, submitted=0, top=`blocked_strength_momentum:insufficient_history=38, blocked_strength_momentum:below_strength_base=26, blocked_strength_momentum:below_window_buy_value=12`, swing=`-`, upstream=`first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=8, ai_terminal:blocked_ai_score_below_buy_score_threshold=4`
- `30m`: ai=25, budget=10, latency=5, submitted=4, top=`blocked_strength_momentum:insufficient_history=60, blocked_strength_momentum:below_strength_base=54, blocked_strength_momentum:below_window_buy_value=40`, swing=`-`, upstream=`first_ai_wait:-=22, blocked_ai_score:ai_score_50_buy_hold_override=5, blocked_ai_score:score_62.0=4`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=22, ai_terminal:blocked_ai_score_below_buy_score_threshold=12`
