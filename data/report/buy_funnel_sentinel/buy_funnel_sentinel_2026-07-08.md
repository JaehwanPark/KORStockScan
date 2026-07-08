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

- as_of: `2026-07-08T15:20:03`
- baseline_date: `2026-07-07`
- ai_confirmed unique: `71`
- budget_pass unique: `17`
- latency_pass unique: `9`
- submitted unique: `9`
- holding_started unique: `8`
- budget/ai unique: `23.9%` (baseline `29.2`)
- submitted/ai unique: `12.7%` (baseline `23.1`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_strength_base=302, blocked_strength_momentum:below_window_buy_value=268, blocked_vpw:-=256, latency_block:latency_state_danger=151, first_ai_wait:-=134`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=134, blocked_ai_score:score_62.0=84, blocked_ai_score:ai_score_50_buy_hold_override=76, blocked_ai_score:score_0.0=37, blocked_ai_score:score_58.0=21`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=150, ai_terminal:first_ai_wait_big_bite_not_confirmed=134`
- latency blockers: `latency_block:latency_state_danger=151`
- price guards: `pre_submit_price_guard_block:ai_tier2_use_defensive=12, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=2, scale_in_price_guard_block:invalid_spread=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with strong negative OFI and high top_depth_ratio indicating downward pressure=1, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low execution strength=1`
- quote refresh: `attempted=15, applied=14, latency_recovered=5, submitted_after_refresh=1`
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

- `5m`: ai=2, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=7, blocked_strength_momentum:below_strength_base=3, blocked_vpw:-=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `10m`: ai=2, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=16, blocked_strength_momentum:below_strength_base=5, blocked_vpw:-=1`, swing=`-`, upstream=`blocked_ai_score:score_62.0=1, first_ai_wait:-=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=9, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=48, blocked_strength_momentum:below_strength_base=21, blocked_vpw:-=11`, swing=`-`, upstream=`first_ai_wait:-=7, blocked_ai_score:score_62.0=5`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=7, ai_terminal:entry_policy_no_buy_score_prior=5`
