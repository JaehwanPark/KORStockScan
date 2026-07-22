# BUY Funnel Sentinel 2026-07-22

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

- as_of: `2026-07-22T15:20:01`
- baseline_date: `2026-07-21`
- ai_confirmed unique: `28`
- budget_pass unique: `69`
- latency_pass unique: `20`
- submitted unique: `9`
- holding_started unique: `8`
- budget/ai unique: `246.4%` (baseline `769.2`)
- submitted/ai unique: `32.1%` (baseline `46.2`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=193, latency_block:latency_state_danger=118, blocked_strength_momentum:insufficient_history=22, first_ai_wait:-=18, blocked_ai_score:score_0.0=12`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=18, blocked_ai_score:score_0.0=12, blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_62.0=7, blocked_ai_score:score_58.0=7`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=37, ai_terminal:first_ai_wait_big_bite_not_confirmed=18`
- latency blockers: `latency_block:latency_state_danger=118`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=10, entry_ai_price_canary_fallback:skip_low_confidence=3, entry_ai_price_canary_fallback:low_confidence=1, entry_ai_price_canary_skip_order:orderbook_micro is ready and micro_state is bearish with strong negative OFI and adverse flow pressure=1`
- quote refresh: `attempted=55, applied=51, latency_recovered=15, submitted_after_refresh=7`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 7, 'price_guard_or_revalidation': 7}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`-`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=8, latency=1, submitted=0, top=`latency_block:latency_state_danger=5`, swing=`-`, upstream=`-`, ai_terminal=`-`
