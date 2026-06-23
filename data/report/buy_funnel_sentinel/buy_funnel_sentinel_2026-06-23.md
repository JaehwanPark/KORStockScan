# BUY Funnel Sentinel 2026-06-23

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

- as_of: `2026-06-23T15:20:05`
- baseline_date: `2026-06-22`
- ai_confirmed unique: `78`
- budget_pass unique: `30`
- latency_pass unique: `10`
- submitted unique: `2`
- holding_started unique: `0`
- budget/ai unique: `38.5%` (baseline `25.6`)
- submitted/ai unique: `2.6%` (baseline `0.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=1650, blocked_strength_momentum:below_strength_base=438, blocked_liquidity:-=390, blocked_strength_momentum:insufficient_history=377, blocked_strength_momentum:below_window_buy_value=327`
- swing blockers: `blocked_swing_score_vpw:-=1594, blocked_swing_gap:-=155`
- upstream blockers: `first_ai_wait:-=271, blocked_ai_score:ai_score_50_buy_hold_override=180, blocked_ai_score:score_62.0=122, blocked_ai_score:score_60.0=42, blocked_ai_score:score_58.0=41`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=275, ai_terminal:first_ai_wait_big_bite_not_confirmed=271`
- latency blockers: `latency_block:latency_state_danger=1650`
- price guards: `entry_ai_price_canary_fallback:invalid_price=161, entry_ai_price_canary_fallback:pre_submit_price_guard=5, entry_ai_price_canary_fallback:above_best_ask=3, scale_in_price_guard_block:micro_vwap_bp>60.0=2, entry_ai_price_canary_fallback:low_confidence=1`
- quote refresh: `attempted=30, applied=27, latency_recovered=8, submitted_after_refresh=2`
- quote refresh downstream: `{'armed_expired_before_submit': 3, 'budget_pass_no_submit_event': 2, 'order_bundle_submitted': 2, 'upstream_block_after_latency_recovery': 1}`

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

- `5m`: ai=5, budget=3, latency=0, submitted=0, top=`blocked_liquidity:-=7, latency_block:latency_state_danger=7, blocked_strength_momentum:below_strength_base=6`, swing=`blocked_swing_score_vpw:-=6`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=5, first_ai_wait:-=4, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=4, ai_terminal:blocked_ai_score_below_buy_score_threshold=1`
- `10m`: ai=7, budget=5, latency=1, submitted=0, top=`latency_block:latency_state_danger=13, blocked_liquidity:-=12, blocked_strength_momentum:below_strength_base=8`, swing=`blocked_swing_score_vpw:-=13`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=7, first_ai_wait:-=6, blocked_ai_score:score_62.0=2`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=6, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `30m`: ai=11, budget=6, latency=1, submitted=0, top=`blocked_liquidity:-=21, blocked_strength_momentum:below_strength_base=20, latency_block:latency_state_danger=18`, swing=`blocked_swing_score_vpw:-=17`, upstream=`blocked_ai_score:ai_score_50_buy_hold_override=13, first_ai_wait:-=11, blocked_ai_score:score_62.0=3`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=11, ai_terminal:blocked_ai_score_below_buy_score_threshold=3`
