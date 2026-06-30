# BUY Funnel Sentinel 2026-06-30

## 판정

- primary: `PRICE_GUARD_DROUGHT`
- secondary: `LATENCY_DROUGHT, UPSTREAM_AI_THRESHOLD`
- report_only: `true`
- live_runtime_effect: `false`
- operator_action_required: `false`
- followup_route: `pre_submit_price_guard_review`
- followup_owner: `postclose_threshold_cycle`
- runtime_effect: `report_only_no_mutation`
- submit_contract_downstream: `code_improvement_workorder, lifecycle_decision_matrix.submit_bucket_attribution, threshold_cycle_ev_report, runtime_approval_summary, postclose_verifier`
- submit_contract_weak_matches: `LATENCY_PRE_SUBMIT, PRICE_REVALIDATION, UPSTREAM_GATE`

## 근거

- as_of: `2026-06-30T15:20:02`
- baseline_date: `2026-06-29`
- ai_confirmed unique: `30`
- budget_pass unique: `36`
- latency_pass unique: `32`
- submitted unique: `30`
- holding_started unique: `24`
- budget/ai unique: `120.0%` (baseline `17.4`)
- submitted/ai unique: `100.0%` (baseline `0.6`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=590, blocked_vpw:-=171, blocked_strength_momentum:below_strength_base=156, blocked_strength_momentum:below_buy_ratio=147, blocked_strength_momentum:below_window_buy_value=90`
- swing blockers: `-`
- upstream blockers: `blocked_ai_score:score_62.0=70, first_ai_wait:-=48, blocked_ai_score:score_73.0=31, blocked_ai_score:score_72.0=30, blocked_ai_score:score_70.0=30`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=306, ai_terminal:first_ai_wait_big_bite_not_confirmed=48`
- latency blockers: `latency_block:latency_state_danger=590`
- price guards: `entry_ai_price_canary_fallback:above_best_ask=20, scale_in_price_guard_block:micro_vwap_bp>60.0=19, scale_in_price_guard_block:quote_consistency_diverged=11, scale_in_price_guard_block:micro_vwap_bp<-5.0=7, entry_ai_price_canary_fallback:pre_submit_price_guard=5`
- quote refresh: `attempted=36, applied=35, latency_recovered=20, submitted_after_refresh=15`
- quote refresh downstream: `{'armed_expired_before_submit': 2, 'budget_pass_no_submit_event': 2, 'order_bundle_submitted': 15, 'upstream_block_after_latency_recovery': 1}`

## 금지된 자동변경

- `score_threshold_relaxation`
- `spread_cap_relaxation`
- `fallback_reenable`
- `live_threshold_runtime_mutation`
- `bot_restart`

## 권고 액션

- Review top price guard block labels and affected symbols.
- Keep threshold/runtime mutation blocked before ThresholdOpsTransition0506.

## Window Summary

- `5m`: ai=2, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=8, blocked_ai_score:score_70.0=2, blocked_strength_momentum:below_window_buy_value=2`, swing=`-`, upstream=`blocked_ai_score:score_70.0=2, blocked_ai_score:score_64.0=1, blocked_ai_score:score_62.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=4`
- `10m`: ai=3, budget=2, latency=0, submitted=0, top=`latency_block:latency_state_danger=14, blocked_overbought:-=6, blocked_strength_momentum:below_window_buy_value=6`, swing=`-`, upstream=`blocked_ai_score:score_70.0=5, blocked_ai_score:score_62.0=3, blocked_ai_score:score_72.0=1`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=10, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
- `30m`: ai=8, budget=6, latency=3, submitted=3, top=`latency_block:latency_state_danger=42, blocked_overbought:-=12, blocked_strength_momentum:below_window_buy_value=12`, swing=`-`, upstream=`blocked_ai_score:score_62.0=11, blocked_ai_score:score_70.0=8, blocked_ai_score:score_58.0=2`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=28, ai_terminal:first_ai_wait_big_bite_not_confirmed=1`
