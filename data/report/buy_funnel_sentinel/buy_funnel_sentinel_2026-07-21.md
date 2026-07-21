# BUY Funnel Sentinel 2026-07-21

## 판정

- primary: `SUBMIT_DROUGHT_CRITICAL`
- secondary: `LATENCY_DROUGHT`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `entry_submit_drought_auto_workorder`
- followup_owner: `postclose_threshold_cycle_and_lifecycle_decision_matrix`
- runtime_effect: `auto_workorder_no_intraday_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, FILL_QUALITY, LATENCY_PRE_SUBMIT, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY`

## 근거

- as_of: `2026-07-21T15:20:03`
- baseline_date: `2026-07-20`
- ai_confirmed unique: `13`
- budget_pass unique: `100`
- latency_pass unique: `13`
- submitted unique: `6`
- holding_started unique: `4`
- budget/ai unique: `769.2%` (baseline `365.2`)
- submitted/ai unique: `46.2%` (baseline `73.9`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=146, blocked_strength_momentum:below_strength_base=29, blocked_zero_qty:-=19, pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=11, blocked_vpw:-=11`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=4, blocked_ai_score:score_54.0=3, blocked_ai_score:score_0.0=2, blocked_ai_score:score_57.0=2, blocked_ai_score:score_72.0=2`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=9, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- latency blockers: `latency_block:latency_state_danger=146, latency_block:tp1_direct_recheck_expired=2`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_score_unavailable=11, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=75, applied=68, latency_recovered=12, submitted_after_refresh=4`
- quote refresh downstream: `{'order_bundle_submitted': 4, 'price_guard_or_revalidation': 8}`

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

- `5m`: ai=0, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=0, budget=3, latency=0, submitted=0, top=`latency_block:latency_state_danger=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=0, budget=9, latency=0, submitted=0, top=`latency_block:latency_state_danger=9, latency_block:tp1_direct_recheck_expired=1`, swing=`-`, upstream=`-`, ai_terminal=`-`
