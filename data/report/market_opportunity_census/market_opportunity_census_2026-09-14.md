# Market Opportunity Census - 2026-09-14

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- NXT scheduled-pause captures excluded from recall/economics: 5 (raw evidence and actual request-budget accounting preserved)
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `installed_trigger_contract_missing`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `installed_trigger_contract_missing`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- Whole-population limitations do not block valid scoped diagnostics; economic floors do not authorize or block discovery diagnosis.

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_NXT_AFTERMARKET | 53 | 0 | 0.0 | 0.0 |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | 20 | 0 | 0.0 | 0.0 |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | 20 | 0 | 0.0 | 0.0 |
| KRX/KRX_REGULAR | 267 | 0 | 0.0 | 9.36 |
| NXT/KRX_NXT_AFTERMARKET | 68 | 0 | 0.0 | 0.0 |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | 20 | 0 | 0.0 | 0.0 |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | 20 | 0 | 0.0 | 0.0 |
| NXT/NXT_PREMARKET | 59 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 244 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 360 | 0 | 0.0 | 6.94 | 360 | 0 | pass |
| NXT | 411 | 0 | 0.0 | 0.0 | 411 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=162, `entry_ai_trace_gap`=7, `entry_decision_rejected`=17, `late_discovery_after_opportunity_window`=27, `scanner_discovery_gap_or_unobserved`=112, `scanner_fetch_seen_pool_unobserved`=18, `scanner_runtime_attach_gap`=1, `scanner_source_guard_blocked_before_promotion`=16
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=411

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=24, `max_new_codes_reached`=5, `returned`=133; count_sum=162; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=4114, valid=4114, invalid=0, unique=4114, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 360 | 288 | 80.0 | 237 | 147 | 32.26 | -0.00376359 | None | False |
| NXT | 411 | 398 | 96.84 | 361 | 206 | 37.76 | -0.3565125 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 368 | 1.36 | 1.36 | 0.0 | 17 | None | 0 |
| all | 10 | KRX | forward_exact | 147 | 3.4 | 3.4 | 0.0 | 17 | None | 0 |
| all | 10 | NXT | forward_exact | 221 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 368 | 83.15 | 78.26 | 36.68 | 57 | None | 14 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 147 | 71.43 | 70.75 | 29.93 | 56 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 221 | 90.95 | 83.26 | 41.18 | 1 | None | 14 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 368 | 25.27 | 25.27 | 6.52 | 64 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 147 | 63.27 | 63.27 | 6.8 | 64 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 221 | 0.0 | 0.0 | 6.33 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 763 | 2.88 | 2.75 | 0.13 | 38 | 173.832081 | 0 |
| all | 20 | KRX | forward_exact | 333 | 6.61 | 6.31 | 0.3 | 38 | 173.832081 | 0 |
| all | 20 | NXT | forward_exact | 430 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 763 | 80.21 | 74.71 | 30.28 | 111 | None | 23 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 333 | 68.47 | 66.37 | 34.53 | 110 | None | 9 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 430 | 89.3 | 81.16 | 26.98 | 1 | None | 14 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 763 | 26.87 | 26.74 | 7.21 | 128 | None | 9 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 333 | 61.56 | 61.26 | 12.61 | 128 | None | 9 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 430 | 0.0 | 0.0 | 3.02 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 1882 | 2.44 | 2.23 | 0.11 | 53 | 28.883765 | 0 |
| all | 50 | KRX | forward_exact | 871 | 5.28 | 4.82 | 0.23 | 53 | 28.883765 | 0 |
| all | 50 | NXT | forward_exact | 1011 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1882 | 70.72 | 61.74 | 18.33 | 226 | None | 23 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 871 | 62.34 | 60.39 | 22.39 | 225 | None | 9 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1011 | 77.94 | 62.91 | 14.84 | 1 | None | 14 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1882 | 26.51 | 26.3 | 4.94 | 242 | None | 9 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 871 | 57.29 | 56.83 | 8.96 | 242 | None | 9 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1011 | 0.0 | 0.0 | 1.48 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 381 | 1.31 | 1.31 | 0.0 | 19 | None | 0 |
| liquid_common | 10 | KRX | forward_exact | 172 | 2.91 | 2.91 | 0.0 | 19 | None | 0 |
| liquid_common | 10 | NXT | forward_exact | 209 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 381 | 88.98 | 85.83 | 39.63 | 85 | None | 15 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 172 | 81.4 | 80.81 | 35.47 | 84 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 209 | 95.22 | 89.95 | 43.06 | 1 | None | 14 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 381 | 32.55 | 32.28 | 7.09 | 95 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 172 | 72.09 | 71.51 | 8.72 | 95 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 209 | 0.0 | 0.0 | 5.74 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 781 | 3.2 | 3.07 | 0.0 | 52 | None | 0 |
| liquid_common | 20 | KRX | forward_exact | 370 | 6.76 | 6.49 | 0.0 | 52 | None | 0 |
| liquid_common | 20 | NXT | forward_exact | 411 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 781 | 87.96 | 85.66 | 33.42 | 159 | None | 27 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 370 | 83.78 | 83.24 | 40.0 | 158 | None | 13 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 411 | 91.73 | 87.83 | 27.49 | 1 | None | 14 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 781 | 37.0 | 36.88 | 9.86 | 189 | None | 13 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 370 | 78.11 | 77.84 | 17.84 | 189 | None | 13 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 411 | 0.0 | 0.0 | 2.68 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1804 | 3.27 | 2.94 | 0.06 | 68 | 35.398259 | 0 |
| liquid_common | 50 | KRX | forward_exact | 906 | 6.51 | 5.85 | 0.11 | 68 | 35.398259 | 0 |
| liquid_common | 50 | NXT | forward_exact | 898 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1804 | 80.76 | 72.89 | 22.39 | 280 | None | 27 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 906 | 78.48 | 76.16 | 27.7 | 276 | None | 13 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 898 | 83.07 | 69.6 | 17.04 | 4 | None | 14 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1804 | 36.86 | 36.25 | 6.98 | 309 | None | 13 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 906 | 73.4 | 72.19 | 12.36 | 309 | None | 13 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 898 | 0.0 | 0.0 | 1.56 | 0 | None | 0 |

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
| KRX/KRX_NXT_AFTERMARKET | insufficient_evidence_scanner_recall | 0/55 | {'global_source_contract_missing': 55} | insufficient_economic_evidence |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | insufficient_evidence_scanner_recall | 0/20 | {'global_source_contract_missing': 20} | insufficient_economic_evidence |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | insufficient_evidence_scanner_recall | 0/20 | {'global_source_contract_missing': 20} | insufficient_economic_evidence |
| KRX/KRX_REGULAR | insufficient_evidence_scanner_recall | 0/275 | {'global_source_contract_missing': 275} | insufficient_economic_evidence |
| NXT/KRX_NXT_AFTERMARKET | insufficient_evidence_scanner_recall | 0/68 | {'global_source_contract_missing': 68} | insufficient_economic_evidence |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | insufficient_evidence_scanner_recall | 0/20 | {'global_source_contract_missing': 20} | insufficient_economic_evidence |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | insufficient_evidence_scanner_recall | 0/20 | {'global_source_contract_missing': 20} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | insufficient_evidence_scanner_recall | 0/59 | {'global_source_contract_missing': 59} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/244 | {'global_source_contract_missing': 244} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.03_h300 | 14 | 6 | -0.16517592 | 300.774182 | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.03_h1200 | 19 | 10 | -0.20604289 | 521.4727498947368 | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.07_h300 | 14 | 6 | -0.16517592 | 300.774182 | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.07_h1200 | 19 | 10 | -0.20604289 | 521.4727498947368 | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.10_h300 | 13 | 5 | -0.18468725 | 301.41127353846156 | False |
| KRX/KRX_NXT_AFTERMARKET | net_0.10_h1200 | 18 | 9 | -0.22240479 | 534.1939031111111 | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h60 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h180 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h300 | 0 | 0 | None | None | False |
| KRX/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h1200 | 0 | 0 | None | None | False |
| KRX/KRX_REGULAR | net_0.03_h60 | 5 | 1 | -1.2824416 | 50.8057544 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 11 | 2 | -1.43835566 | 99.31354909090909 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 80 | 30 | -0.2867836 | 265.828607625 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 139 | 64 | 0.02783084 | 522.3828846258992 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 5 | 1 | -1.2824416 | 50.8057544 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 11 | 2 | -1.43835566 | 99.31354909090909 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 78 | 28 | -0.29516345 | 265.0140904358974 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 137 | 62 | 0.03382984 | 527.8226592262774 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 4 | 0 | -1.62525445 | 61.14159 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 10 | 1 | -1.5910722 | 108.29866280000002 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 76 | 25 | -0.32197594 | 267.23818688157894 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 133 | 57 | 0.02361828 | 525.0226320601504 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.03_h300 | 24 | 1 | -0.67126968 | 303.3213539166667 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.03_h1200 | 30 | 4 | -0.70677297 | 702.1505722666666 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.07_h300 | 24 | 1 | -0.67126968 | 303.3213539166667 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.07_h1200 | 30 | 4 | -0.70677297 | 702.1505722666666 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.10_h300 | 24 | 1 | -0.67126968 | 303.3213539166667 | False |
| NXT/KRX_NXT_AFTERMARKET | net_0.10_h1200 | 29 | 3 | -0.73364168 | 695.4589783448275 | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.03_h1200 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.07_h1200 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_CLOSE_ONLY | net_0.10_h1200 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.03_h1200 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.07_h1200 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h300 | 0 | 0 | None | None | False |
| NXT/KRX_NXT_AFTERMARKET_TERMINAL_EXIT | net_0.10_h1200 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h300 | 36 | 13 | 0.22086763 | 301.2512632222222 | False |
| NXT/NXT_PREMARKET | net_0.03_h1200 | 39 | 17 | 0.1962493 | 416.17792415384616 | False |
| NXT/NXT_PREMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h300 | 36 | 13 | 0.22086763 | 301.2512632222222 | False |
| NXT/NXT_PREMARKET | net_0.07_h1200 | 39 | 17 | 0.1962493 | 416.17792415384616 | False |
| NXT/NXT_PREMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h300 | 36 | 13 | 0.22086763 | 301.2512632222222 | False |
| NXT/NXT_PREMARKET | net_0.10_h1200 | 39 | 17 | 0.1962493 | 416.17792415384616 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 66 | 14 | -0.53914997 | 302.873574530303 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 145 | 50 | -0.44595387 | 721.4854412482758 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 65 | 13 | -0.54806788 | 303.04276472307697 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 144 | 49 | -0.43574654 | 730.6791896666667 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 64 | 12 | -0.55817186 | 303.21953340625 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 144 | 49 | -0.43365608 | 734.7254753680555 | False |