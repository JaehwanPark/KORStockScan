# BUY Funnel Sentinel 2026-08-06

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

- as_of: `2026-08-06T15:20:04`
- baseline_date: `2026-08-05`
- ai_confirmed unique: `170`
- budget_pass unique: `121`
- latency_pass unique: `34`
- submitted unique: `0`
- holding_started unique: `0`
- budget/ai unique: `71.2%` (baseline `0.0`)
- submitted/ai unique: `0.0%` (baseline `0.0`)
- economic bundles: `observed=0, valid=0, probe_only=0, partial_residual=0, full=0`
- economic submitted/requested: `qty=0/0 (0.0%), notional=0/0 (0.0%)`
- economic participation by venue: `{}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=754, blocked_strength_momentum:insufficient_history=712, latency_block:latency_state_danger=614, blocked_liquidity:-=341, blocked_strength_momentum:below_strength_base=299`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:ai_score_50_buy_hold_override=219, first_ai_wait:-=122, blocked_ai_score:score_0.0=112, blocked_ai_score:score_11.0=57, blocked_ai_score:score_16.0=31`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=334, ai_terminal:first_ai_wait_big_bite_not_confirmed=122`
- latency blockers: `latency_block:latency_state_danger=614, latency_block:tp1_direct_recheck_expired=3`
- price guards: `pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=50, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=27, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=17, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and high spread, suggesting unfavorable entry conditions=1`
- quote refresh: `attempted=109, applied=41, latency_recovered=7, submitted_after_refresh=0`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'price_guard_or_revalidation': 6}`

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

- `5m`: ai=3, budget=7, latency=0, submitted=0, top=`latency_block:latency_state_danger=22, blocked_strength_momentum:insufficient_history=17, blocked_overbought:-=4`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_17.0=1, blocked_ai_score:score_14.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=2`
- `10m`: ai=7, budget=11, latency=0, submitted=0, top=`latency_block:latency_state_danger=31, blocked_strength_momentum:insufficient_history=23, blocked_strength_momentum:below_window_buy_value=8`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_11.0=2, blocked_ai_score:score_21.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=5`
- `30m`: ai=18, budget=20, latency=1, submitted=0, top=`blocked_strength_momentum:insufficient_history=69, latency_block:latency_state_danger=66, blocked_overbought:-=35`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=10, blocked_ai_score:score_11.0=7, blocked_ai_score:score_19.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=19`
