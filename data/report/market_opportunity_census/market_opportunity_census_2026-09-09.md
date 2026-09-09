# Market Opportunity Census - 2026-09-09

- status: `partial_diagnostics_ready`
- scanner_recall_state: `scoped_diagnostics_available`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- Whole-population limitations do not block valid scoped diagnostics; economic floors do not authorize or block discovery diagnosis.

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_REGULAR | 144 | 5 | 3.47 | 9.03 |
| NXT/NXT_PREMARKET | 34 | 1 | 2.94 | 11.76 |
| NXT/NXT_REGULAR_OVERLAP | 172 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 144 | 5 | 3.47 | 9.03 | 144 | 0 | pass |
| NXT | 206 | 1 | 0.49 | 1.94 | 206 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=102, `entry_ai_trace_gap`=4, `entry_decision_rejected`=9, `late_discovery_after_opportunity_window`=14, `scanner_discovery_gap_or_unobserved`=10, `scanner_source_guard_blocked_before_promotion`=5
- NXT terminal coverage reasons: `entry_ai_trace_gap`=2, `entry_authority_guard_block`=1, `entry_decision_observe_only`=1, `late_discovery_after_opportunity_window`=2, `scanner_discovery_gap_or_unobserved`=200

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=24, `market_gainer_reserved_full`=24, `max_new_codes_reached`=13, `reentry_cooldown_no_material_upgrade`=41; count_sum=102; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=741, valid=741, invalid=0, unique=741, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 144 | 81 | 56.25 | 73 | 38 | 45.71 | -0.09932333 | None | False |
| NXT | 206 | 149 | 72.33 | 134 | 56 | 58.21 | -0.00554277 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 202 | 6.93 | 6.93 | 1.49 | 22 | 14.302211 | 0 |
| all | 10 | KRX | forward_exact | 104 | 10.58 | 10.58 | 1.92 | 22 | 16.37135 | 0 |
| all | 10 | NXT | forward_exact | 98 | 3.06 | 3.06 | 1.02 | 0 | 8.846703 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 202 | 83.66 | 79.7 | 60.4 | 53 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 104 | 78.85 | 78.85 | 58.65 | 46 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 98 | 88.78 | 80.61 | 62.24 | 7 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 202 | 69.8 | 69.8 | 38.12 | 58 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 104 | 77.88 | 77.88 | 57.69 | 58 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 98 | 61.22 | 61.22 | 17.35 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 391 | 7.93 | 7.93 | 2.3 | 44 | 31.719231 | 0 |
| all | 20 | KRX | forward_exact | 192 | 14.58 | 14.58 | 4.17 | 44 | 31.843244 | 0 |
| all | 20 | NXT | forward_exact | 199 | 1.51 | 1.51 | 0.5 | 0 | 14.302211 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 391 | 78.01 | 74.17 | 51.41 | 98 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 192 | 82.81 | 82.81 | 65.1 | 89 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 199 | 73.37 | 65.83 | 38.19 | 9 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 391 | 59.59 | 59.59 | 35.81 | 113 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 192 | 82.29 | 82.29 | 64.58 | 113 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 199 | 37.69 | 37.69 | 8.04 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 986 | 4.16 | 3.85 | 1.01 | 50 | 33.564321 | 0 |
| all | 50 | KRX | forward_exact | 490 | 8.16 | 7.55 | 2.04 | 50 | 33.564321 | 0 |
| all | 50 | NXT | forward_exact | 496 | 0.2 | 0.2 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 986 | 65.62 | 61.16 | 33.06 | 141 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 490 | 68.98 | 65.51 | 45.92 | 133 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 496 | 62.3 | 56.85 | 20.36 | 8 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 986 | 44.02 | 42.29 | 23.83 | 182 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 490 | 68.37 | 64.9 | 44.49 | 182 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 496 | 19.96 | 19.96 | 3.43 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 186 | 3.76 | 3.76 | 1.61 | 13 | 14.302211 | 0 |
| liquid_common | 10 | KRX | forward_exact | 78 | 5.13 | 5.13 | 2.56 | 13 | 23.650064 | 0 |
| liquid_common | 10 | NXT | forward_exact | 108 | 2.78 | 2.78 | 0.93 | 0 | 8.846703 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 186 | 89.78 | 84.95 | 63.98 | 49 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 78 | 89.74 | 89.74 | 70.51 | 41 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 108 | 89.81 | 81.48 | 59.26 | 8 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 186 | 72.58 | 72.58 | 38.17 | 50 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 78 | 89.74 | 89.74 | 70.51 | 50 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 108 | 60.19 | 60.19 | 14.81 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 358 | 5.03 | 5.03 | 1.96 | 29 | 31.719231 | 0 |
| liquid_common | 20 | KRX | forward_exact | 152 | 9.21 | 9.21 | 3.95 | 29 | 33.832444 | 0 |
| liquid_common | 20 | NXT | forward_exact | 206 | 1.94 | 1.94 | 0.49 | 0 | 14.302211 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 358 | 84.92 | 80.45 | 56.98 | 93 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 152 | 94.08 | 94.08 | 78.95 | 84 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 206 | 78.16 | 70.39 | 40.78 | 9 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 358 | 63.41 | 63.41 | 38.83 | 104 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 152 | 94.08 | 94.08 | 78.95 | 104 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 206 | 40.78 | 40.78 | 9.22 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 895 | 2.68 | 2.57 | 0.78 | 35 | 23.787052 | 0 |
| liquid_common | 50 | KRX | forward_exact | 373 | 5.63 | 5.36 | 1.61 | 35 | 27.100079 | 0 |
| liquid_common | 50 | NXT | forward_exact | 522 | 0.57 | 0.57 | 0.19 | 0 | 14.302211 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 895 | 72.85 | 68.16 | 36.65 | 137 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 373 | 82.31 | 77.75 | 56.84 | 128 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 522 | 66.09 | 61.3 | 22.22 | 9 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 895 | 46.59 | 44.69 | 25.25 | 173 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 373 | 82.31 | 77.75 | 55.23 | 173 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 522 | 21.07 | 21.07 | 3.83 | 0 | None | 0 |

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
| KRX/KRX_REGULAR | insufficient_evidence_scanner_recall | 0/152 | {'capture_gap_or_pending_validity_window': 144, 'master_unverified_or_not_common_equity': 8} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 34/34 | {} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/172 | {'main_overlap_route_policy_unproven': 172} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 3 | 0 | -0.81683719 | 9.314345333333334 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 7 | 2 | -0.37642162 | 54.85081257142857 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 24 | 9 | -0.45036371 | 225.87699804166667 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 39 | 19 | -0.09305261 | 426.2740815384616 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 3 | 0 | -0.81683719 | 9.314345333333334 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 7 | 2 | -0.37642162 | 54.85081257142857 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 24 | 9 | -0.45036371 | 225.87699804166667 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 39 | 19 | -0.09305261 | 426.2740815384616 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 3 | 0 | -0.81683719 | 9.314345333333334 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 7 | 2 | -0.37642162 | 54.85081257142857 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 24 | 9 | -0.45036371 | 225.87699804166667 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 39 | 19 | -0.09305261 | 426.2740815384616 | False |
| NXT/NXT_PREMARKET | net_0.03_h60 | 4 | 4 | 0.15029748 | 26.715154 | False |
| NXT/NXT_PREMARKET | net_0.03_h180 | 6 | 5 | 0.63712469 | 54.546954166666666 | False |
| NXT/NXT_PREMARKET | net_0.03_h300 | 19 | 8 | -0.38058053 | 223.59400421052632 | False |
| NXT/NXT_PREMARKET | net_0.03_h1200 | 18 | 10 | -0.31675042 | 302.35057183333333 | False |
| NXT/NXT_PREMARKET | net_0.07_h60 | 4 | 4 | 0.18717064 | 30.411595 | False |
| NXT/NXT_PREMARKET | net_0.07_h180 | 6 | 5 | 0.66170679 | 57.01124816666667 | False |
| NXT/NXT_PREMARKET | net_0.07_h300 | 19 | 8 | -0.37281776 | 224.37220231578948 | False |
| NXT/NXT_PREMARKET | net_0.07_h1200 | 18 | 10 | -0.30855638 | 303.1720031666666 | False |
| NXT/NXT_PREMARKET | net_0.10_h60 | 4 | 4 | 0.18717064 | 30.411595 | False |
| NXT/NXT_PREMARKET | net_0.10_h180 | 6 | 5 | 0.66170679 | 57.01124816666667 | False |
| NXT/NXT_PREMARKET | net_0.10_h300 | 19 | 8 | -0.37281776 | 224.37220231578948 | False |
| NXT/NXT_PREMARKET | net_0.10_h1200 | 18 | 10 | -0.30855638 | 303.1720031666666 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 28 | 14 | 0.18149512 | 309.2677562142857 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 45 | 29 | 0.08142716 | 642.3062632666666 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 28 | 14 | 0.18149512 | 309.2677562142857 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 44 | 28 | 0.08226129 | 636.5187843863637 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 28 | 14 | 0.18149512 | 309.2677562142857 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 42 | 26 | 0.08238398 | 637.7456958333333 | False |