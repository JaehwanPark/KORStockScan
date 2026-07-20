# BUY Funnel Sentinel 2026-07-20

## 판정

- primary: `LATENCY_DROUGHT`
- secondary: `-`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `latency_quote_quality_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT`

## 근거

- as_of: `2026-07-20T12:50:02`
- baseline_date: `2026-07-16`
- ai_confirmed unique: `16`
- budget_pass unique: `63`
- latency_pass unique: `15`
- submitted unique: `9`
- holding_started unique: `9`
- budget/ai unique: `393.8%` (baseline `0.0`)
- submitted/ai unique: `56.2%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=90, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=9, blocked_strength_momentum:below_strength_base=8, blocked_liquidity:-=7, blocked_vpw:-=5`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:score_58.0=2, first_ai_wait:-=2, blocked_ai_score:score_70.0=2, blocked_ai_score:score_62.0=1`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=5, ai_terminal:first_ai_wait_big_bite_not_confirmed=2`
- latency blockers: `latency_block:latency_state_danger=90`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=9, entry_ai_price_canary_fallback:above_best_ask=2, entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and weak bid depth, making submission unfavorable=1, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=56, applied=48, latency_recovered=10, submitted_after_refresh=3`
- quote refresh downstream: `{'order_bundle_submitted': 3, 'price_guard_or_revalidation': 7}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Inspect latency_state_danger top reasons and recent quote quality.
- Do not auto-relax spread/ws/jitter caps; produce a candidate playbook with rollback guard first.

## Window Summary

- `5m`: ai=1, budget=3, latency=1, submitted=1, top=`latency_block:latency_state_danger=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=1, budget=4, latency=1, submitted=1, top=`latency_block:latency_state_danger=3`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=1, budget=12, latency=1, submitted=1, top=`latency_block:latency_state_danger=11, blocked_vpw:-=1, blocked_liquidity:-=1`, swing=`-`, upstream=`blocked_ai_score:score_70.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
