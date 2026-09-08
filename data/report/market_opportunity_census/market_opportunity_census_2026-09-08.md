# Market Opportunity Census - 2026-09-08

- status: `partial_diagnostics_ready`
- scanner_recall_state: `scoped_diagnostics_available`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- Whole-population limitations do not block valid scoped diagnostics; economic floors do not authorize or block discovery diagnosis.

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_REGULAR | 260 | 2 | 0.77 | 11.15 |
| NXT/NXT_AFTERMARKET | 115 | 3 | 2.61 | 6.09 |
| NXT/NXT_PREMARKET | 36 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 335 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 260 | 2 | 0.77 | 11.15 | 260 | 0 | pass |
| NXT | 486 | 3 | 0.62 | 1.44 | 486 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=177, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=2, `entry_decision_rejected`=7, `late_discovery_after_opportunity_window`=29, `scanner_discovery_gap_or_unobserved`=19, `scanner_fast_precheck_gap`=9, `scanner_heavy_eval_gap`=2, `scanner_source_guard_blocked_before_promotion`=6
- NXT terminal coverage reasons: `candidate_not_promoted`=68, `entry_ai_trace_gap`=1, `entry_authority_guard_block`=1, `entry_decision_observe_only`=1, `entry_decision_rejected`=2, `late_discovery_after_opportunity_window`=15, `scanner_discovery_gap_or_unobserved`=396, `scanner_fast_precheck_gap`=1, `scanner_heavy_eval_gap`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=17, `market_gainer_reserved_full`=31, `max_new_codes_reached`=6, `reentry_cooldown_no_material_upgrade`=123; count_sum=177; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=2, `market_gainer_reserved_full`=28, `reentry_cooldown_no_material_upgrade`=38; count_sum=68; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=2302, valid=2302, invalid=0, unique=2302, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 260 | 156 | 60.0 | 136 | 80 | 41.18 | -0.22139061 | None | False |
| NXT | 486 | 389 | 80.04 | 362 | 168 | 51.3 | -0.5147441 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 378 | 2.38 | 0.79 | 0.0 | 24 | 49.855343 | 0 |
| all | 10 | KRX | forward_exact | 131 | 4.58 | 1.53 | 0.0 | 15 | None | 0 |
| all | 10 | NXT | forward_exact | 247 | 1.21 | 0.4 | 0.0 | 9 | 49.855343 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 378 | 90.21 | 89.42 | 62.17 | 102 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 131 | 75.57 | 74.81 | 51.91 | 69 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 247 | 97.98 | 97.17 | 67.61 | 33 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 378 | 88.1 | 87.3 | 49.47 | 265 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 131 | 75.57 | 74.81 | 51.91 | 69 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 247 | 94.74 | 93.93 | 48.18 | 196 | None | 0 |
| all | 20 | ALL | forward_exact | 751 | 3.2 | 2.13 | 0.4 | 54 | 24.401143 | 0 |
| all | 20 | KRX | forward_exact | 264 | 6.82 | 4.55 | 0.38 | 39 | 24.401143 | 0 |
| all | 20 | NXT | forward_exact | 487 | 1.23 | 0.82 | 0.41 | 15 | 10.797751 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 751 | 92.01 | 87.62 | 55.79 | 177 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 264 | 80.68 | 78.79 | 59.09 | 132 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 487 | 98.15 | 92.4 | 54.0 | 45 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 751 | 88.55 | 84.69 | 44.87 | 461 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 264 | 79.92 | 78.79 | 56.82 | 132 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 487 | 93.22 | 87.89 | 38.4 | 329 | None | 0 |
| all | 50 | ALL | forward_exact | 1901 | 2.05 | 1.26 | 0.21 | 64 | 32.165786 | 0 |
| all | 50 | KRX | forward_exact | 665 | 3.76 | 2.71 | 0.45 | 55 | 32.165786 | 0 |
| all | 50 | NXT | forward_exact | 1236 | 1.13 | 0.49 | 0.08 | 9 | 173.770131 | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1901 | 86.53 | 79.22 | 33.61 | 322 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 665 | 72.18 | 67.52 | 45.11 | 265 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1236 | 94.26 | 85.52 | 27.43 | 57 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1901 | 80.69 | 73.28 | 25.88 | 655 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 665 | 70.68 | 66.47 | 40.6 | 262 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1236 | 86.08 | 76.94 | 17.96 | 393 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 394 | 4.82 | 2.28 | 0.51 | 34 | 157.090355 | 0 |
| liquid_common | 10 | KRX | forward_exact | 147 | 10.2 | 4.76 | 0.68 | 23 | 157.090355 | 0 |
| liquid_common | 10 | NXT | forward_exact | 247 | 1.62 | 0.81 | 0.4 | 11 | 49.855343 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 394 | 92.13 | 91.12 | 62.94 | 118 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 147 | 80.27 | 79.59 | 54.42 | 87 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 247 | 99.19 | 97.98 | 68.02 | 31 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 394 | 90.61 | 89.59 | 50.51 | 289 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 147 | 80.27 | 79.59 | 54.42 | 87 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 247 | 96.76 | 95.55 | 48.18 | 202 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 785 | 4.71 | 2.93 | 0.64 | 80 | 82.220462 | 0 |
| liquid_common | 20 | KRX | forward_exact | 299 | 10.03 | 6.02 | 0.67 | 60 | 33.421126 | 0 |
| liquid_common | 20 | NXT | forward_exact | 486 | 1.44 | 1.03 | 0.62 | 20 | 173.770131 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 785 | 94.01 | 90.45 | 58.73 | 202 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 299 | 85.28 | 83.95 | 62.21 | 156 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 486 | 99.38 | 94.44 | 56.58 | 46 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 785 | 91.46 | 87.77 | 48.15 | 499 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 299 | 85.28 | 83.95 | 60.2 | 156 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 486 | 95.27 | 90.12 | 40.74 | 343 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1959 | 3.32 | 1.99 | 0.31 | 97 | 33.421126 | 0 |
| liquid_common | 50 | KRX | forward_exact | 748 | 6.55 | 4.14 | 0.53 | 82 | 31.527274 | 0 |
| liquid_common | 50 | NXT | forward_exact | 1211 | 1.32 | 0.66 | 0.17 | 15 | 173.770131 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1959 | 89.94 | 83.51 | 36.65 | 378 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 748 | 80.48 | 75.4 | 48.26 | 319 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1211 | 95.79 | 88.52 | 29.48 | 59 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1959 | 85.09 | 78.1 | 28.18 | 718 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 748 | 79.68 | 73.93 | 42.78 | 315 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 1211 | 88.44 | 80.68 | 19.16 | 403 | None | 0 |

## Forbidden Uses

- `standalone_buy`
- `live_candidate_injection`
- `score_or_threshold_mutation`
- `provider_or_model_change`
- `order_price_or_quantity_change`
- `broker_or_account_guard_bypass`
- `stale_or_source_conflict_bypass`
- `upper_limit_chase_authority`
- `bot_restart`
- `real_execution_quality_approval`
- `bounded_bbo_observer_ev_extrapolation_to_full_external_population`


## Scoped diagnostic readiness

| Venue/session | Status | Eligible / raw episodes | Exclusions | Economic status |
|---|---|---:|---|---|
| KRX/KRX_REGULAR | diagnostic_ready | 21/299 | {'master_unverified_or_not_common_equity': 39, 'capture_gap_or_pending_validity_window': 239} | insufficient_economic_evidence |
| NXT/NXT_AFTERMARKET | diagnostic_ready | 112/115 | {'capture_gap_or_pending_validity_window': 3} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 35/36 | {'capture_gap_or_pending_validity_window': 1} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | diagnostic_ready | 84/335 | {'capture_gap_or_pending_validity_window': 251} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 9 | 1 | -1.53131788 | 89.77586000000001 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 43 | 10 | -0.76172821 | 254.40362065116278 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 85 | 37 | -0.21045953 | 610.9561136941177 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 8 | 0 | -1.7306395 | 81.198510875 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 42 | 9 | -0.78137068 | 256.68954845238096 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 82 | 34 | -0.22016887 | 620.3704019634147 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 8 | 0 | -1.7306395 | 81.198510875 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 42 | 9 | -0.78137068 | 256.68954845238096 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 82 | 34 | -0.22016887 | 620.3704019634147 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h300 | 36 | 2 | -0.64702518 | 300.57832086111114 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h1200 | 50 | 12 | -0.47431069 | 738.7339870000001 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h300 | 36 | 2 | -0.64702518 | 300.57832086111114 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h1200 | 49 | 11 | -0.48508618 | 741.5918341836735 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h300 | 36 | 2 | -0.64702518 | 300.57832086111114 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h1200 | 48 | 10 | -0.4969725 | 744.5554318541667 | False |
| NXT/NXT_PREMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h300 | 18 | 5 | -0.27559435 | 299.9785475 | False |
| NXT/NXT_PREMARKET | net_0.03_h1200 | 22 | 6 | -0.37358689 | 382.0317602727273 | False |
| NXT/NXT_PREMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h300 | 18 | 5 | -0.27559435 | 299.9785475 | False |
| NXT/NXT_PREMARKET | net_0.07_h1200 | 21 | 5 | -0.39413426 | 343.1050132857143 | False |
| NXT/NXT_PREMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h300 | 18 | 5 | -0.27559435 | 299.9785475 | False |
| NXT/NXT_PREMARKET | net_0.10_h1200 | 21 | 5 | -0.39413426 | 343.1050132857143 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 73 | 15 | -0.49391975 | 303.7590228767123 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 108 | 43 | -0.51547806 | 702.5442418518519 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 73 | 15 | -0.49391975 | 303.7590228767123 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 108 | 43 | -0.51547806 | 702.5442418518519 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 73 | 15 | -0.49391975 | 303.7590228767123 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 108 | 43 | -0.51547806 | 702.5442418518519 | False |