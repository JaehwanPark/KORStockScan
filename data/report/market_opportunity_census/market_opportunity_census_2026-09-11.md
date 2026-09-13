# Market Opportunity Census - 2026-09-11

- status: `partial_diagnostics_ready`
- scanner_recall_state: `scoped_diagnostics_available`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- NXT scheduled-pause captures excluded from recall/economics: 4 (raw evidence and actual request-budget accounting preserved)
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- Whole-population limitations do not block valid scoped diagnostics; economic floors do not authorize or block discovery diagnosis.

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_REGULAR | 136 | 2 | 1.47 | 18.38 |
| NXT/NXT_AFTERMARKET | 117 | 1 | 0.85 | 8.55 |
| NXT/NXT_PREMARKET | 40 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 242 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 136 | 2 | 1.47 | 18.38 | 136 | 0 | pass |
| NXT | 399 | 1 | 0.25 | 2.51 | 399 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=74, `entry_ai_trace_gap`=11, `entry_decision_rejected`=13, `late_discovery_after_opportunity_window`=17, `scanner_discovery_gap_or_unobserved`=15, `scanner_fetch_seen_pool_unobserved`=2, `scanner_source_guard_blocked_before_promotion`=3, `submitted`=1
- NXT terminal coverage reasons: `candidate_not_promoted`=65, `entry_ai_trace_gap`=9, `entry_decision_rejected`=1, `late_discovery_after_opportunity_window`=14, `scanner_discovery_gap_or_unobserved`=305, `scanner_fetch_seen_pool_unobserved`=2, `scanner_source_guard_blocked_before_promotion`=3

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=10, `market_gainer_reserved_full`=2, `reentry_cooldown_no_material_upgrade`=2, `returned`=60; count_sum=74; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=2, `returned`=63; count_sum=65; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=3873, valid=3873, invalid=0, unique=3873, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 136 | 111 | 81.62 | 88 | 72 | 18.18 | 0.21962973 | None | False |
| NXT | 399 | 374 | 93.73 | 337 | 186 | 44.31 | -0.51774046 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 285 | 2.81 | 2.81 | 1.05 | 13 | 50.32143 | 0 |
| all | 10 | KRX | forward_exact | 77 | 1.3 | 1.3 | 1.3 | 2 | 57.6818 | 0 |
| all | 10 | NXT | forward_exact | 208 | 3.37 | 3.37 | 0.96 | 11 | 27.964433 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 285 | 83.86 | 82.46 | 61.75 | 42 | None | 24 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 77 | 42.86 | 41.56 | 33.77 | 25 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 208 | 99.04 | 97.6 | 72.12 | 17 | None | 24 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 285 | 76.84 | 74.04 | 45.96 | 128 | None | 14 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 77 | 42.86 | 41.56 | 33.77 | 25 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 208 | 89.42 | 86.06 | 50.48 | 103 | None | 14 |
| all | 20 | ALL | forward_exact | 639 | 3.44 | 3.29 | 0.94 | 49 | 68.819812 | 0 |
| all | 20 | KRX | forward_exact | 197 | 5.08 | 5.08 | 1.52 | 26 | 92.819811 | 0 |
| all | 20 | NXT | forward_exact | 442 | 2.71 | 2.49 | 0.68 | 23 | 50.32143 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 639 | 83.88 | 81.53 | 46.01 | 103 | None | 33 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 197 | 53.3 | 52.79 | 45.18 | 69 | None | 5 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 442 | 97.51 | 94.34 | 46.38 | 34 | None | 28 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 639 | 79.34 | 75.43 | 35.68 | 293 | None | 18 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 197 | 53.3 | 52.79 | 45.18 | 79 | None | 4 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 442 | 90.95 | 85.52 | 31.45 | 214 | None | 14 |
| all | 50 | ALL | forward_exact | 1501 | 4.26 | 3.73 | 0.6 | 93 | 57.6818 | 1 |
| all | 50 | KRX | forward_exact | 453 | 8.61 | 7.95 | 1.32 | 75 | 57.6818 | 1 |
| all | 50 | NXT | forward_exact | 1048 | 2.39 | 1.91 | 0.29 | 18 | 50.32143 | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1501 | 81.75 | 72.75 | 29.11 | 189 | None | 40 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 453 | 52.1 | 51.88 | 36.64 | 157 | None | 12 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1048 | 94.56 | 81.77 | 25.86 | 32 | None | 28 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1501 | 78.61 | 67.36 | 20.85 | 387 | None | 25 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 453 | 52.1 | 51.88 | 36.64 | 165 | None | 11 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1048 | 90.08 | 74.05 | 14.03 | 222 | None | 14 |
| liquid_common | 10 | ALL | forward_exact | 261 | 4.21 | 4.21 | 1.53 | 25 | 16.422501 | 0 |
| liquid_common | 10 | KRX | forward_exact | 76 | 10.53 | 10.53 | 5.26 | 15 | 9.405489 | 0 |
| liquid_common | 10 | NXT | forward_exact | 185 | 1.62 | 1.62 | 0.0 | 10 | 50.537351 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 261 | 94.25 | 94.25 | 72.41 | 60 | None | 30 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 76 | 80.26 | 80.26 | 72.37 | 44 | None | 6 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 185 | 100.0 | 100.0 | 72.43 | 16 | None | 24 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 261 | 86.97 | 86.21 | 55.56 | 143 | None | 17 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 76 | 80.26 | 80.26 | 72.37 | 50 | None | 5 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 185 | 89.73 | 88.65 | 48.65 | 93 | None | 12 |
| liquid_common | 20 | ALL | forward_exact | 559 | 6.26 | 6.26 | 0.54 | 66 | 75.526752 | 1 |
| liquid_common | 20 | KRX | forward_exact | 160 | 15.62 | 15.62 | 1.25 | 43 | 75.526752 | 1 |
| liquid_common | 20 | NXT | forward_exact | 399 | 2.51 | 2.51 | 0.25 | 23 | 111.073076 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 559 | 92.49 | 91.06 | 48.48 | 107 | None | 32 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 160 | 75.0 | 75.0 | 56.25 | 74 | None | 10 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 399 | 99.5 | 97.49 | 45.36 | 33 | None | 22 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 559 | 87.84 | 85.33 | 38.1 | 271 | None | 21 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 160 | 75.0 | 75.0 | 56.25 | 81 | None | 9 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 399 | 92.98 | 89.47 | 30.83 | 190 | None | 12 |
| liquid_common | 50 | ALL | forward_exact | 1161 | 5.0 | 4.13 | 0.26 | 53 | 26.371587 | 0 |
| liquid_common | 50 | KRX | forward_exact | 315 | 11.75 | 8.89 | 0.63 | 34 | 26.371587 | 0 |
| liquid_common | 50 | NXT | forward_exact | 846 | 2.48 | 2.36 | 0.12 | 19 | 111.073076 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1161 | 91.3 | 85.01 | 32.3 | 139 | None | 44 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 315 | 77.78 | 74.29 | 43.17 | 112 | None | 21 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 846 | 96.34 | 89.01 | 28.25 | 27 | None | 23 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1161 | 88.11 | 80.36 | 21.1 | 315 | None | 29 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 315 | 77.78 | 73.97 | 37.78 | 126 | None | 17 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 846 | 91.96 | 82.74 | 14.89 | 189 | None | 12 |

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
| KRX/KRX_REGULAR | diagnostic_ready | 129/160 | {'master_unverified_or_not_common_equity': 24, 'capture_gap_or_pending_validity_window': 3, 'intended_new_buy_hard_cutoff': 4} | insufficient_economic_evidence |
| NXT/NXT_AFTERMARKET | diagnostic_ready | 85/117 | {'intended_new_buy_hard_cutoff': 25, 'capture_gap_or_pending_validity_window': 7} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 40/40 | {} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/242 | {'main_overlap_route_policy_unproven': 236, 'intended_new_buy_hard_cutoff': 6} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 17 | 6 | -0.5439855 | 81.63492694117647 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 52 | 19 | -0.25921949 | 227.7991233846154 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 73 | 38 | 0.16345469 | 443.09043557534244 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 16 | 5 | -0.58092261 | 81.15227725 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 52 | 19 | -0.24430366 | 230.20665290384616 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 73 | 38 | 0.2135503 | 448.8449898219178 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 16 | 5 | -0.58092261 | 81.15227725 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 52 | 19 | -0.24430366 | 230.20665290384616 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 73 | 38 | 0.2135503 | 448.8449898219178 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h300 | 49 | 8 | -0.42011958 | 301.3191377959184 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h1200 | 72 | 23 | -0.35975205 | 884.6224598611111 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h300 | 48 | 7 | -0.42963967 | 301.3528029166667 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h1200 | 72 | 22 | -0.35627557 | 905.4323819722223 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h300 | 48 | 7 | -0.42963967 | 301.3528029166667 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h1200 | 72 | 21 | -0.36189291 | 913.7992259444444 | False |
| NXT/NXT_PREMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.03_h300 | 22 | 5 | -0.80594606 | 300.0364808181818 | False |
| NXT/NXT_PREMARKET | net_0.03_h1200 | 25 | 5 | -0.94110147 | 368.70234495999995 | False |
| NXT/NXT_PREMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.07_h300 | 22 | 5 | -0.80594606 | 300.0364808181818 | False |
| NXT/NXT_PREMARKET | net_0.07_h1200 | 25 | 5 | -0.94110147 | 368.70234495999995 | False |
| NXT/NXT_PREMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_PREMARKET | net_0.10_h300 | 21 | 4 | -0.84849882 | 300.1183590952381 | False |
| NXT/NXT_PREMARKET | net_0.10_h1200 | 24 | 4 | -0.98396662 | 371.63506612500004 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 69 | 20 | -0.53115478 | 301.60940244927536 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 108 | 49 | -0.44162322 | 739.5365526203705 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 69 | 20 | -0.53115478 | 301.60940244927536 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 107 | 48 | -0.44547074 | 740.6422802897197 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 69 | 20 | -0.53115478 | 301.60940244927536 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 105 | 45 | -0.4661032 | 742.9873504761904 | False |