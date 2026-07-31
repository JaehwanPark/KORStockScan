# BUY Funnel Sentinel 2026-07-31

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

- as_of: `2026-07-31T15:20:03`
- baseline_date: `2026-07-30`
- ai_confirmed unique: `136`
- budget_pass unique: `89`
- latency_pass unique: `21`
- submitted unique: `5`
- holding_started unique: `5`
- budget/ai unique: `65.4%` (baseline `20.0`)
- submitted/ai unique: `3.7%` (baseline `0.0`)
- economic bundles: `observed=5, valid=5, probe_only=5, partial_residual=0, full=0`
- economic submitted/requested: `qty=5/18 (27.8%), notional=674200/2291800 (29.4%)`
- economic participation by venue: `{'KRX': {'bundle_count': 5, 'probe_only_bundle_count': 5, 'partial_residual_bundle_count': 0, 'full_submitted_bundle_count': 0, 'requested_qty': 18, 'submitted_qty': 5, 'requested_notional_krw': 2291800, 'submitted_notional_krw': 674200, 'submitted_qty_to_requested_qty_pct': 27.8, 'submitted_notional_to_requested_notional_pct': 29.4}}`
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `blocked_strength_momentum:below_window_buy_value=544, blocked_strength_momentum:insufficient_history=314, blocked_strength_momentum:below_strength_base=277, blocked_overbought:-=277, blocked_liquidity:-=239`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=153, blocked_ai_score:ai_score_50_buy_hold_override=119, blocked_ai_score:score_0.0=86, wait65_79_ev_candidate:score_65.0=39, blocked_ai_score:score_11.0=36`
- AI terminal reasons: `ai_terminal:entry_policy_no_buy_score_prior=218, ai_terminal:first_ai_wait_big_bite_not_confirmed=153`
- latency blockers: `latency_block:latency_state_danger=177`
- price guards: `pre_submit_entry_ai_authority_guard_block:entry_ai_result_stale_or_untrusted=16, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=5, scale_in_price_guard_block:micro_vwap_bp>60.0=4, scale_in_price_guard_block:micro_vwap_bp<-5.0=1`
- quote refresh: `attempted=77, applied=30, latency_recovered=5, submitted_after_refresh=1`
- quote refresh downstream: `{'order_bundle_submitted': 1, 'price_guard_or_revalidation': 4}`

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

- `5m`: ai=3, budget=5, latency=3, submitted=1, top=`latency_block:latency_state_danger=4, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `10m`: ai=3, budget=6, latency=4, submitted=1, top=`latency_block:latency_state_danger=9, pre_submit_entry_ai_authority_guard_block:fresh_ai_drop_real_buy_veto=2`, swing=`-`, upstream=`-`, ai_terminal=`-`
- `30m`: ai=8, budget=20, latency=4, submitted=1, top=`latency_block:latency_state_danger=38, blocked_liquidity:-=3, first_ai_wait:-=3`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=2, blocked_ai_score:score_11.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3, ai_terminal:entry_policy_no_buy_score_prior=3`
