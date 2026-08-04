# BUY Funnel Sentinel 2026-08-04

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
- submit_contract_weak_matches: `BROKER_RECEIPT, BUDGET_PASS_COLLAPSE, ECONOMIC_PARTICIPATION, FILL_QUALITY, LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, SIM_REAL_AUTHORITY, TELEGRAM_POST_SUBMIT_ONLY, UPSTREAM_GATE`

## 근거

- as_of: `2026-08-04T15:20:05`
- baseline_date: `2026-08-03`
- ai_confirmed unique: `209`
- budget_pass unique: `93`
- latency_pass unique: `39`
- submitted unique: `12`
- holding_started unique: `12`
- budget/ai unique: `44.5%` (baseline `64.6`)
- submitted/ai unique: `5.7%` (baseline `4.5`)
- economic bundles: `observed=10, valid=10, probe_only=9, partial_residual=1, full=0`
- economic submitted/requested: `qty=38/234 (16.2%), notional=215324/1652518 (13.0%)`
- economic participation by venue: `{'KRX': {'bundle_count': 10, 'probe_only_bundle_count': 9, 'partial_residual_bundle_count': 1, 'full_submitted_bundle_count': 0, 'requested_qty': 234, 'submitted_qty': 38, 'requested_notional_krw': 1652518, 'submitted_notional_krw': 215324, 'submitted_qty_to_requested_qty_pct': 16.2, 'submitted_notional_to_requested_notional_pct': 13.0}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=963, blocked_overbought:-=876, blocked_strength_momentum:insufficient_history=789, blocked_liquidity:-=375, blocked_vpw:-=319`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=211, blocked_ai_score:ai_score_50_buy_hold_override=152, wait65_79_ev_candidate:score_65.0=100, blocked_ai_score:score_11.0=48, blocked_ai_score:score_65.0=48`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=250, ai_terminal:first_ai_wait_big_bite_not_confirmed=211`
- latency blockers: `latency_block:latency_state_danger=254`
- price guards: `pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=21, pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=12, pre_submit_entry_ai_authority_guard_block:fresh_ai_wait_observation_only_probe_veto=7, entry_ai_price_canary_skip_order:orderbook_micro indicates bearish micro state with adverse OFI and high spread, suggesting unfavorable entry conditions=1, entry_ai_price_canary_fallback:skip_low_confidence=1`
- quote refresh: `attempted=91, applied=41, latency_recovered=6, submitted_after_refresh=1`
- quote refresh downstream: `{'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 1, 'price_guard_or_revalidation': 4}`

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

- `5m`: ai=0, budget=0, latency=0, submitted=0, top=`blocked_zero_qty:-=5`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=3, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=25, blocked_strength_momentum:insufficient_history=14, blocked_zero_qty:-=8`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=3, blocked_ai_score:score_19.0=1`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=1`
- `30m`: ai=14, budget=0, latency=0, submitted=0, top=`blocked_overbought:-=104, blocked_strength_momentum:insufficient_history=56, blocked_strength_momentum:below_window_buy_value=26`, swing=`-`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=12, first_ai_wait:-=5, blocked_ai_score:score_0.0=2`, ai_terminal=`ai_terminal:entry_policy_no_buy_score_prior=6, ai_terminal:first_ai_wait_big_bite_not_confirmed=5`
