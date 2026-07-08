# BUY Funnel Sentinel 2026-07-08

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

- as_of: `2026-07-08T12:20:03`
- baseline_date: `2026-07-07`
- ai_confirmed unique: `54`
- budget_pass unique: `12`
- latency_pass unique: `8`
- submitted unique: `7`
- holding_started unique: `6`
- budget/ai unique: `22.2%` (baseline `19.5`)
- submitted/ai unique: `13.0%` (baseline `14.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=189, blocked_vpw:-=122, blocked_strength_momentum:below_strength_base=117, first_ai_wait:-=85, blocked_liquidity:-=66`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=85, blocked_ai_score:ai_score_50_buy_hold_override=40, blocked_ai_score:score_62.0=37, blocked_ai_score:score_0.0=23, blocked_ai_score:score_58.0=8`
- AI terminal reasons: `ai_terminal:first_ai_wait_big_bite_not_confirmed=85, ai_terminal:entry_policy_no_buy_score_prior=70`
- latency blockers: `latency_block:latency_state_danger=49`
- price guards: `pre_submit_price_guard_block:ai_tier2_use_defensive=11, scale_in_price_guard_block:invalid_spread=1, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=1`
- quote refresh: `attempted=12, applied=11, latency_recovered=5, submitted_after_refresh=1`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 1, 'price_guard_or_revalidation': 3}`

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

- `5m`: ai=8, budget=0, latency=0, submitted=0, top=`first_ai_wait:-=8, blocked_strength_momentum:below_strength_base=8, blocked_vpw:-=7`, swing=`-`, upstream=`first_ai_wait:-=8, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=8, ai_terminal:entry_policy_no_buy_score_prior=1`
- `10m`: ai=15, budget=2, latency=1, submitted=1, top=`blocked_strength_momentum:below_strength_base=19, blocked_vpw:-=16, first_ai_wait:-=15`, swing=`-`, upstream=`first_ai_wait:-=15, blocked_ai_score:score_62.0=3, blocked_ai_score:ai_score_50_buy_hold_override=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=15, ai_terminal:entry_policy_no_buy_score_prior=4`
- `30m`: ai=19, budget=4, latency=3, submitted=3, top=`blocked_strength_momentum:below_strength_base=38, blocked_strength_momentum:below_window_buy_value=33, blocked_vpw:-=30`, swing=`-`, upstream=`first_ai_wait:-=24, blocked_ai_score:ai_score_50_buy_hold_override=13, blocked_ai_score:score_0.0=7`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=24, ai_terminal:entry_policy_no_buy_score_prior=15`
