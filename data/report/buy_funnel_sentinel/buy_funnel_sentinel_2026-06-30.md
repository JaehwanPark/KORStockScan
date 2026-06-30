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

- as_of: `2026-06-30T10:25:04`
- baseline_date: `2026-06-29`
- ai_confirmed unique: `14`
- budget_pass unique: `17`
- latency_pass unique: `15`
- submitted unique: `15`
- holding_started unique: `10`
- budget/ai unique: `121.4%` (baseline `14.2`)
- submitted/ai unique: `107.1%` (baseline `0.0`)
- critical submit thresholds: `submitted/ai < 20.0%` or `submitted/budget <= 10.0%` (floors: ai>=20, budget>=3)
- top blockers: `latency_block:latency_state_danger=260, blocked_strength_momentum:below_strength_base=47, blocked_vpw:-=27, blocked_overbought:-=21, first_ai_wait:-=18`
- swing blockers: `-`
- upstream blockers: `first_ai_wait:-=18, blocked_ai_score:score_62.0=11, blocked_ai_score:score_73.0=4, blocked_ai_score:score_70.0=4, blocked_ai_score:score_72.0=3`
- AI terminal reasons: `ai_terminal:blocked_ai_score_below_buy_score_threshold=30, ai_terminal:first_ai_wait_big_bite_not_confirmed=18`
- latency blockers: `latency_block:latency_state_danger=260`
- price guards: `scale_in_price_guard_block:micro_vwap_bp>60.0=5, entry_ai_price_canary_fallback:above_best_ask=3, scale_in_price_guard_block:micro_vwap_bp<-5.0=3, scale_in_price_guard_block:quote_consistency_diverged=3, scale_in_price_guard_block:invalid_spread=1`
- quote refresh: `attempted=17, applied=17, latency_recovered=7, submitted_after_refresh=7`
- quote refresh downstream: `{'order_bundle_submitted': 7}`

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

- `5m`: ai=3, budget=4, latency=4, submitted=4, top=`blocked_strength_momentum:below_strength_base=11, latency_block:latency_state_danger=5, blocked_vpw:-=4`, swing=`-`, upstream=`first_ai_wait:-=3, blocked_ai_score:ai_score_50_buy_hold_override=1, blocked_ai_score:score_54.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=3, ai_terminal:blocked_ai_score_below_buy_score_threshold=2`
- `10m`: ai=6, budget=5, latency=4, submitted=4, top=`blocked_strength_momentum:below_strength_base=18, latency_block:latency_state_danger=11, blocked_overbought:-=10`, swing=`-`, upstream=`first_ai_wait:-=7, blocked_ai_score:score_62.0=1, wait65_79_ev_candidate:score_74.0=1`, ai_terminal=`ai_terminal:first_ai_wait_big_bite_not_confirmed=7, ai_terminal:blocked_ai_score_below_buy_score_threshold=3`
- `30m`: ai=12, budget=10, latency=8, submitted=8, top=`latency_block:latency_state_danger=44, blocked_strength_momentum:below_strength_base=36, blocked_vpw:-=22`, swing=`-`, upstream=`first_ai_wait:-=15, blocked_ai_score:score_62.0=8, blocked_ai_score:score_70.0=3`, ai_terminal=`ai_terminal:blocked_ai_score_below_buy_score_threshold=18, ai_terminal:first_ai_wait_big_bite_not_confirmed=15`
