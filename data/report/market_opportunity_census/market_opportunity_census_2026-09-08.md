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
| KRX/KRX_REGULAR | 258 | 2 | 0.78 | 11.24 |
| NXT/NXT_PREMARKET | 36 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 315 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 258 | 2 | 0.78 | 11.24 | 258 | 0 | pass |
| NXT | 351 | 0 | 0.0 | 0.0 | 351 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=177, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=2, `entry_decision_rejected`=7, `late_discovery_after_opportunity_window`=29, `scanner_discovery_gap_or_unobserved`=17, `scanner_fast_precheck_gap`=9, `scanner_heavy_eval_gap`=2, `scanner_source_guard_blocked_before_promotion`=6
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=351

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=17, `market_gainer_reserved_full`=31, `max_new_codes_reached`=6, `reentry_cooldown_no_material_upgrade`=123; count_sum=177; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=1242, valid=1242, invalid=0, unique=1242, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 258 | 156 | 60.47 | 136 | 76 | 42.42 | -0.2142534 | None | False |
| NXT | 351 | 268 | 76.35 | 250 | 115 | 51.27 | -0.51244451 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 318 | 1.89 | 0.63 | 0.0 | 15 | None | 0 |
| all | 10 | KRX | forward_exact | 121 | 4.96 | 1.65 | 0.0 | 15 | None | 0 |
| all | 10 | NXT | forward_exact | 197 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 318 | 84.59 | 80.19 | 37.42 | 82 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 121 | 75.21 | 74.38 | 51.24 | 65 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 197 | 90.36 | 83.76 | 28.93 | 17 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 318 | 28.62 | 28.3 | 19.5 | 65 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 121 | 75.21 | 74.38 | 51.24 | 65 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 197 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 631 | 2.85 | 1.9 | 0.16 | 39 | 24.401143 | 0 |
| all | 20 | KRX | forward_exact | 244 | 7.38 | 4.92 | 0.41 | 39 | 24.401143 | 0 |
| all | 20 | NXT | forward_exact | 387 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 631 | 86.21 | 77.97 | 35.34 | 145 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 244 | 79.92 | 78.69 | 56.56 | 123 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 387 | 90.18 | 77.52 | 21.96 | 22 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 631 | 30.9 | 30.43 | 21.87 | 123 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 244 | 79.92 | 78.69 | 56.56 | 123 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 387 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 1601 | 1.56 | 1.12 | 0.19 | 55 | 32.165786 | 0 |
| all | 50 | KRX | forward_exact | 615 | 4.07 | 2.93 | 0.49 | 55 | 32.165786 | 0 |
| all | 50 | NXT | forward_exact | 986 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1601 | 78.14 | 67.21 | 23.8 | 272 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 615 | 70.24 | 66.02 | 39.84 | 243 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 986 | 83.06 | 67.95 | 13.79 | 29 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1601 | 26.98 | 25.36 | 15.3 | 243 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 615 | 70.24 | 66.02 | 39.84 | 243 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 986 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 324 | 4.63 | 2.16 | 0.31 | 23 | 157.090355 | 0 |
| liquid_common | 10 | KRX | forward_exact | 145 | 10.34 | 4.83 | 0.69 | 23 | 157.090355 | 0 |
| liquid_common | 10 | NXT | forward_exact | 179 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 324 | 87.04 | 82.41 | 41.05 | 101 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 145 | 80.0 | 79.31 | 53.79 | 87 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 179 | 92.74 | 84.92 | 30.73 | 14 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 324 | 35.8 | 35.49 | 24.07 | 87 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 145 | 80.0 | 79.31 | 53.79 | 87 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 179 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 647 | 4.64 | 2.78 | 0.31 | 60 | 33.421126 | 0 |
| liquid_common | 20 | KRX | forward_exact | 296 | 10.14 | 6.08 | 0.68 | 60 | 33.421126 | 0 |
| liquid_common | 20 | NXT | forward_exact | 351 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 647 | 89.34 | 81.92 | 39.88 | 175 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 296 | 85.47 | 84.12 | 60.14 | 155 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 351 | 92.59 | 80.06 | 22.79 | 20 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 647 | 39.1 | 38.49 | 27.51 | 155 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 296 | 85.47 | 84.12 | 60.14 | 155 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 351 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1621 | 3.02 | 1.91 | 0.25 | 82 | 31.527274 | 0 |
| liquid_common | 50 | KRX | forward_exact | 741 | 6.61 | 4.18 | 0.54 | 82 | 31.527274 | 0 |
| liquid_common | 50 | NXT | forward_exact | 880 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1621 | 82.6 | 71.68 | 27.39 | 338 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 741 | 79.62 | 73.95 | 42.78 | 312 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 880 | 85.11 | 69.77 | 14.43 | 26 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1621 | 36.4 | 33.81 | 19.56 | 312 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 741 | 79.62 | 73.95 | 42.78 | 312 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 880 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
| KRX/KRX_REGULAR | insufficient_evidence_scanner_recall | 19/296 | {'master_unverified_or_not_common_equity': 38, 'capture_gap_or_pending_validity_window': 239} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 35/36 | {'capture_gap_or_pending_validity_window': 1} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | diagnostic_ready | 84/315 | {'capture_gap_or_pending_validity_window': 231} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 9 | 1 | -1.53131788 | 89.77586000000001 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 43 | 10 | -0.76172821 | 254.40362065116278 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 81 | 34 | -0.20322308 | 589.5430131234568 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 8 | 0 | -1.7306395 | 81.198510875 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 42 | 9 | -0.78137068 | 256.68954845238096 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 78 | 31 | -0.21315201 | 598.6165046153845 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 3 | 0 | -1.01610758 | 33.852285333333334 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 8 | 0 | -1.7306395 | 81.198510875 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 42 | 9 | -0.78137068 | 256.68954845238096 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 78 | 31 | -0.21315201 | 598.6165046153845 | False |
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
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 101 | 41 | -0.50456209 | 686.6369037326733 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 73 | 15 | -0.49391975 | 303.7590228767123 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 101 | 41 | -0.50456209 | 686.6369037326733 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 73 | 15 | -0.49391975 | 303.7590228767123 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 101 | 41 | -0.50456209 | 686.6369037326733 | False |