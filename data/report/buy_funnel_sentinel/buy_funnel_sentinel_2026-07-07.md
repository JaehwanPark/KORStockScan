# BUY Funnel Sentinel 2026-07-07

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-07-07T11:45:03`
- baseline_date: `2026-07-06`
- ai_confirmed unique: `35`
- budget_pass unique: `7`
- latency_pass unique: `6`
- submitted unique: `5`
- holding_started unique: `4`
- budget/ai unique: `20.0%` (baseline `45.5`)
- submitted/ai unique: `14.3%` (baseline `24.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=124, blocked_strength_momentum:below_window_buy_value=109, blocked_vpw:-=83, first_ai_wait:-=67, blocked_liquidity:-=49`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=67, blocked_ai_score:score_62.0=34, blocked_ai_score:ai_score_50_buy_hold_override=32, blocked_ai_score:score_0.0=13, blocked_ai_score:score_64.0=2`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=67, ai_terminal:entry_policy_no_buy_score_prior=53`
- latency blockers: `latency_block:latency_state_danger=9`
- price guards: `entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=7, applied=7, latency_recovered=6, submitted_after_refresh=5`
- quote refresh downstream: `{'armed_expired_before_submit': 1, 'order_bundle_submitted': 5}`

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

- `5m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=7, blocked_strength_momentum:below_window_buy_value=5, blocked_vpw:-=3`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3`
- `10m`: ai=7, budget=0, latency=0, submitted=0, top=`blocked_strength_momentum:below_strength_base=10, blocked_strength_momentum:below_window_buy_value=10, blocked_vpw:-=8`, swing=`-`, upstream=`first_ai_wait:-=5, blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_62.0=4`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
- `30m`: ai=13, budget=1, latency=1, submitted=0, top=`blocked_strength_momentum:below_window_buy_value=39, blocked_strength_momentum:below_strength_base=22, blocked_vpw:-=17`, swing=`-`, upstream=`first_ai_wait:-=14, blocked_ai_score:ai_score_50_buy_hold_override=9, blocked_ai_score:score_62.0=9`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=14, ai_terminal:entry_policy_no_buy_score_prior=13`
