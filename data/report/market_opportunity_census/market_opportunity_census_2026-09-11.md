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
| KRX/KRX_REGULAR | 135 | 2 | 1.48 | 18.52 |
| NXT/NXT_PREMARKET | 40 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 241 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 135 | 2 | 1.48 | 18.52 | 135 | 0 | pass |
| NXT | 281 | 0 | 0.0 | 0.0 | 281 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=74, `entry_ai_trace_gap`=11, `entry_decision_rejected`=13, `late_discovery_after_opportunity_window`=17, `scanner_discovery_gap_or_unobserved`=14, `scanner_fetch_seen_pool_unobserved`=2, `scanner_source_guard_blocked_before_promotion`=3, `submitted`=1
- NXT terminal coverage reasons: `late_discovery_after_opportunity_window`=1, `scanner_discovery_gap_or_unobserved`=280

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=10, `market_gainer_reserved_full`=2, `reentry_cooldown_no_material_upgrade`=2, `returned`=60; count_sum=74; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=2836, valid=2836, invalid=0, unique=2836, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 135 | 110 | 81.48 | 87 | 71 | 16.47 | 0.27464362 | None | False |
| NXT | 281 | 256 | 91.1 | 230 | 122 | 45.29 | -0.57366081 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 226 | 0.44 | 0.44 | 0.44 | 2 | 57.6818 | 0 |
| all | 10 | KRX | forward_exact | 77 | 1.3 | 1.3 | 1.3 | 2 | 57.6818 | 0 |
| all | 10 | NXT | forward_exact | 149 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 226 | 72.12 | 66.81 | 36.73 | 25 | None | 8 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 77 | 42.86 | 41.56 | 33.77 | 25 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 149 | 87.25 | 79.87 | 38.26 | 0 | None | 8 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 226 | 28.76 | 28.32 | 11.5 | 25 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 77 | 42.86 | 41.56 | 33.77 | 25 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 149 | 21.48 | 21.48 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 508 | 1.97 | 1.97 | 0.59 | 26 | 92.819811 | 0 |
| all | 20 | KRX | forward_exact | 196 | 5.1 | 5.1 | 1.53 | 26 | 92.819811 | 0 |
| all | 20 | NXT | forward_exact | 312 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 508 | 70.28 | 64.76 | 31.3 | 68 | None | 13 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 196 | 53.06 | 52.55 | 45.41 | 68 | None | 4 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 312 | 81.09 | 72.44 | 22.44 | 0 | None | 9 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 508 | 27.56 | 27.36 | 17.52 | 78 | None | 4 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 196 | 53.06 | 52.55 | 45.41 | 78 | None | 4 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 312 | 11.54 | 11.54 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 1181 | 3.39 | 3.13 | 0.51 | 75 | 57.6818 | 1 |
| all | 50 | KRX | forward_exact | 451 | 8.65 | 7.98 | 1.33 | 75 | 57.6818 | 1 |
| all | 50 | NXT | forward_exact | 730 | 0.14 | 0.14 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1181 | 63.08 | 53.51 | 22.95 | 157 | None | 20 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 451 | 52.11 | 51.88 | 36.59 | 157 | None | 11 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 730 | 69.86 | 54.52 | 14.52 | 0 | None | 9 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1181 | 24.64 | 24.56 | 13.97 | 165 | None | 11 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 451 | 52.11 | 51.88 | 36.59 | 165 | None | 11 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 730 | 7.67 | 7.67 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 206 | 3.88 | 3.88 | 1.94 | 15 | 9.405489 | 0 |
| liquid_common | 10 | KRX | forward_exact | 75 | 10.67 | 10.67 | 5.33 | 15 | 9.405489 | 0 |
| liquid_common | 10 | NXT | forward_exact | 131 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 206 | 85.92 | 81.07 | 51.46 | 43 | None | 14 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 75 | 80.0 | 80.0 | 72.0 | 43 | None | 5 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 131 | 89.31 | 81.68 | 39.69 | 0 | None | 9 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 206 | 43.69 | 43.69 | 26.21 | 49 | None | 5 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 75 | 80.0 | 80.0 | 72.0 | 49 | None | 5 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 131 | 22.9 | 22.9 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 440 | 5.68 | 5.68 | 0.45 | 43 | 75.526752 | 1 |
| liquid_common | 20 | KRX | forward_exact | 159 | 15.72 | 15.72 | 1.26 | 43 | 75.526752 | 1 |
| liquid_common | 20 | NXT | forward_exact | 281 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 440 | 79.09 | 72.73 | 34.55 | 74 | None | 14 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 159 | 74.84 | 74.84 | 55.97 | 74 | None | 8 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 281 | 81.49 | 71.53 | 22.42 | 0 | None | 6 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 440 | 33.86 | 33.86 | 20.23 | 81 | None | 8 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 159 | 74.84 | 74.84 | 55.97 | 81 | None | 8 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 281 | 10.68 | 10.68 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 892 | 4.15 | 3.14 | 0.22 | 34 | 26.371587 | 0 |
| liquid_common | 50 | KRX | forward_exact | 314 | 11.78 | 8.92 | 0.64 | 34 | 26.371587 | 0 |
| liquid_common | 50 | NXT | forward_exact | 578 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 892 | 74.1 | 65.92 | 24.44 | 112 | None | 24 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 314 | 78.03 | 74.2 | 37.9 | 112 | None | 17 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 578 | 71.97 | 61.42 | 17.13 | 0 | None | 7 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 892 | 33.74 | 32.4 | 13.34 | 126 | None | 17 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 314 | 78.03 | 74.2 | 37.9 | 126 | None | 17 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 578 | 9.69 | 9.69 | 0.0 | 0 | None | 0 |

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
| KRX/KRX_REGULAR | diagnostic_ready | 129/159 | {'master_unverified_or_not_common_equity': 24, 'capture_gap_or_pending_validity_window': 3, 'intended_new_buy_hard_cutoff': 3} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 40/40 | {} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/241 | {'main_overlap_route_policy_unproven': 236, 'intended_new_buy_hard_cutoff': 5} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 17 | 6 | -0.5439855 | 81.63492694117647 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 51 | 19 | -0.19202073 | 226.28986031372548 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 72 | 38 | 0.21692429 | 445.0115313472222 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 16 | 5 | -0.58092261 | 81.15227725 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 51 | 19 | -0.17681243 | 228.74459629411763 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 72 | 38 | 0.26771567 | 450.8460099583333 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 7 | 1 | -0.88424276 | 31.817241142857142 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 16 | 5 | -0.58092261 | 81.15227725 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 51 | 19 | -0.17681243 | 228.74459629411763 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 72 | 38 | 0.26771567 | 450.8460099583333 | False |
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
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 68 | 20 | -0.53384319 | 301.59390638235294 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 108 | 49 | -0.44162322 | 739.5365526203705 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 68 | 20 | -0.53384319 | 301.59390638235294 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 107 | 48 | -0.44547074 | 740.6422802897197 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 68 | 20 | -0.53384319 | 301.59390638235294 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 105 | 45 | -0.4661032 | 742.9873504761904 | False |