# Market Opportunity Census - 2026-09-10

- status: `partial_diagnostics_ready`
- scanner_recall_state: `scoped_diagnostics_available`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- NXT scheduled-pause captures excluded from recall/economics: 6 (raw evidence and actual request-budget accounting preserved)
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
| KRX/KRX_REGULAR | 168 | 3 | 1.79 | 15.48 |
| NXT/NXT_AFTERMARKET | 75 | 2 | 2.67 | 12.0 |
| NXT/NXT_PREMARKET | 35 | 0 | 0.0 | 8.57 |
| NXT/NXT_REGULAR_OVERLAP | 299 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 168 | 3 | 1.79 | 15.48 | 168 | 0 | pass |
| NXT | 409 | 2 | 0.49 | 2.93 | 409 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=106, `entry_ai_trace_gap`=14, `entry_authority_guard_block`=2, `entry_decision_rejected`=8, `late_discovery_after_opportunity_window`=23, `scanner_discovery_gap_or_unobserved`=8, `scanner_heavy_eval_gap`=1, `scanner_runtime_attach_gap`=1, `scanner_source_guard_blocked_before_promotion`=5
- NXT terminal coverage reasons: `candidate_not_promoted`=35, `entry_ai_trace_gap`=8, `entry_decision_rejected`=4, `late_discovery_after_opportunity_window`=9, `scanner_discovery_gap_or_unobserved`=352, `scanner_fetch_seen_pool_unobserved`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=7, `market_gainer_reserved_full`=2, `max_new_codes_reached`=6, `reentry_cooldown_no_material_upgrade`=2, `returned`=89; count_sum=106; conservation_delta=0; conservation_status=`pass`
- NXT: `reentry_cooldown_no_material_upgrade`=1, `returned`=34; count_sum=35; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=3625, valid=3625, invalid=0, unique=3625, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 168 | 119 | 70.83 | 106 | 62 | 41.51 | -0.23393083 | None | False |
| NXT | 409 | 351 | 85.82 | 317 | 180 | 42.68 | -0.37110472 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 359 | 4.46 | 4.46 | 1.11 | 31 | 26.135026 | 0 |
| all | 10 | KRX | forward_exact | 167 | 6.59 | 6.59 | 1.2 | 25 | 26.135026 | 0 |
| all | 10 | NXT | forward_exact | 192 | 2.6 | 2.6 | 1.04 | 6 | 23.171199 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 359 | 79.11 | 76.6 | 58.77 | 110 | None | 12 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 167 | 60.48 | 56.89 | 42.51 | 76 | None | 12 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 192 | 95.31 | 93.75 | 72.92 | 34 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 359 | 78.27 | 75.77 | 50.97 | 162 | None | 12 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 167 | 59.88 | 56.29 | 41.92 | 80 | None | 12 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 192 | 94.27 | 92.71 | 58.85 | 82 | None | 0 |
| all | 20 | ALL | forward_exact | 706 | 4.53 | 4.39 | 0.85 | 66 | 26.135026 | 0 |
| all | 20 | KRX | forward_exact | 327 | 7.95 | 7.95 | 1.53 | 58 | 20.551957 | 0 |
| all | 20 | NXT | forward_exact | 379 | 1.58 | 1.32 | 0.26 | 8 | 52.269 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 706 | 82.01 | 79.75 | 51.42 | 196 | None | 23 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 327 | 66.67 | 64.83 | 49.85 | 153 | None | 23 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 379 | 95.25 | 92.61 | 52.77 | 43 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 706 | 80.31 | 76.91 | 45.47 | 300 | None | 23 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 327 | 66.36 | 64.53 | 49.24 | 174 | None | 23 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 379 | 92.35 | 87.6 | 42.22 | 126 | None | 0 |
| all | 50 | ALL | forward_exact | 1837 | 3.43 | 2.83 | 0.49 | 100 | 31.406457 | 0 |
| all | 50 | KRX | forward_exact | 837 | 6.09 | 5.02 | 0.96 | 92 | 30.971752 | 0 |
| all | 50 | NXT | forward_exact | 1000 | 1.2 | 1.0 | 0.1 | 8 | 52.269 | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1837 | 81.49 | 74.96 | 33.64 | 348 | None | 41 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 837 | 68.94 | 66.91 | 44.68 | 302 | None | 41 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1000 | 92.0 | 81.7 | 24.4 | 46 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1837 | 76.43 | 67.23 | 29.18 | 511 | None | 41 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 837 | 67.03 | 65.11 | 41.94 | 369 | None | 41 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1000 | 84.3 | 69.0 | 18.5 | 142 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 320 | 7.19 | 7.19 | 0.94 | 37 | 58.788502 | 0 |
| liquid_common | 10 | KRX | forward_exact | 97 | 14.43 | 14.43 | 2.06 | 26 | 115.643408 | 0 |
| liquid_common | 10 | NXT | forward_exact | 223 | 4.04 | 4.04 | 0.45 | 11 | 23.171199 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 320 | 94.38 | 94.38 | 72.81 | 98 | None | 6 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 97 | 83.51 | 83.51 | 61.86 | 60 | None | 6 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 223 | 99.1 | 99.1 | 77.58 | 38 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 320 | 94.06 | 94.06 | 63.44 | 172 | None | 6 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 97 | 83.51 | 83.51 | 61.86 | 66 | None | 6 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 223 | 98.65 | 98.65 | 64.13 | 106 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 596 | 6.71 | 6.38 | 0.84 | 65 | 38.838412 | 0 |
| liquid_common | 20 | KRX | forward_exact | 187 | 14.97 | 13.9 | 1.6 | 51 | 58.788502 | 0 |
| liquid_common | 20 | NXT | forward_exact | 409 | 2.93 | 2.93 | 0.49 | 14 | 12.478744 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 596 | 95.97 | 94.97 | 60.57 | 159 | None | 13 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 187 | 89.84 | 89.3 | 65.24 | 104 | None | 13 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 409 | 98.78 | 97.56 | 58.44 | 55 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 596 | 93.96 | 91.61 | 52.68 | 277 | None | 13 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 187 | 89.84 | 89.3 | 63.64 | 127 | None | 13 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 409 | 95.84 | 92.67 | 47.68 | 150 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1521 | 3.68 | 2.76 | 0.33 | 47 | 58.568641 | 0 |
| liquid_common | 50 | KRX | forward_exact | 436 | 9.4 | 6.19 | 0.92 | 35 | 58.568641 | 0 |
| liquid_common | 50 | NXT | forward_exact | 1085 | 1.38 | 1.38 | 0.09 | 12 | 23.171199 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1521 | 91.26 | 86.79 | 31.56 | 194 | None | 18 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 436 | 83.03 | 82.11 | 43.58 | 140 | None | 18 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1085 | 94.56 | 88.66 | 26.73 | 54 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1521 | 85.73 | 78.76 | 26.04 | 326 | None | 18 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 436 | 78.44 | 77.75 | 39.91 | 159 | None | 18 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 1085 | 88.66 | 79.17 | 20.46 | 167 | None | 0 |

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
| KRX/KRX_REGULAR | diagnostic_ready | 130/187 | {'master_unverified_or_not_common_equity': 19, 'capture_gap_or_pending_validity_window': 35, 'intended_new_buy_hard_cutoff': 3} | insufficient_economic_evidence |
| NXT/NXT_AFTERMARKET | diagnostic_ready | 49/75 | {'intended_new_buy_hard_cutoff': 25, 'capture_gap_or_pending_validity_window': 1} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 35/35 | {} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/299 | {'main_overlap_route_policy_unproven': 277, 'intended_new_buy_hard_cutoff': 22} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 3 | 1 | -0.53257699 | 14.38538 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 11 | 3 | -1.23859794 | 121.1259280909091 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 42 | 18 | -0.09104962 | 250.84462545238097 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 66 | 35 | -0.22099253 | 475.6289015757576 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 2 | 0 | -0.82451246 | 10.444040999999999 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 10 | 2 | -1.36758713 | 131.0117151 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 40 | 16 | -0.09852361 | 255.453004375 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 64 | 33 | -0.22507464 | 490.15463221875 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 2 | 0 | -0.82451246 | 10.444040999999999 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 10 | 2 | -1.36758713 | 131.0117151 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 40 | 16 | -0.09852361 | 255.453004375 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 64 | 33 | -0.22507464 | 490.15463221875 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h300 | 19 | 4 | -0.37604913 | 300.2672813157895 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h1200 | 33 | 16 | -0.22804752 | 654.4953156666667 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h300 | 19 | 4 | -0.37604913 | 300.2672813157895 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h1200 | 33 | 16 | -0.20816883 | 672.5504502121212 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h300 | 19 | 4 | -0.37604913 | 300.2672813157895 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h1200 | 33 | 16 | -0.18317664 | 681.6422698787879 | False |
| NXT/NXT_PREMARKET | net_0.03_h60 | 3 | 1 | -0.53916608 | 29.020954999999997 | False |
| NXT/NXT_PREMARKET | net_0.03_h180 | 4 | 1 | -0.47478778 | 66.919914 | False |
| NXT/NXT_PREMARKET | net_0.03_h300 | 16 | 7 | 0.10874061 | 233.0790926875 | False |
| NXT/NXT_PREMARKET | net_0.03_h1200 | 19 | 10 | 0.01936912 | 338.60204157894736 | False |
| NXT/NXT_PREMARKET | net_0.07_h60 | 3 | 1 | -0.53916608 | 29.020954999999997 | False |
| NXT/NXT_PREMARKET | net_0.07_h180 | 4 | 1 | -0.47478778 | 66.919914 | False |
| NXT/NXT_PREMARKET | net_0.07_h300 | 16 | 7 | 0.10874061 | 233.0790926875 | False |
| NXT/NXT_PREMARKET | net_0.07_h1200 | 19 | 10 | 0.01936912 | 338.60204157894736 | False |
| NXT/NXT_PREMARKET | net_0.10_h60 | 3 | 1 | -0.53916608 | 29.020954999999997 | False |
| NXT/NXT_PREMARKET | net_0.10_h180 | 4 | 1 | -0.47478778 | 66.919914 | False |
| NXT/NXT_PREMARKET | net_0.10_h300 | 16 | 7 | 0.10874061 | 233.0790926875 | False |
| NXT/NXT_PREMARKET | net_0.10_h1200 | 19 | 10 | 0.01936912 | 338.60204157894736 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 46 | 12 | -0.51272385 | 300.07155576086956 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 143 | 55 | -0.4418698 | 720.3698103776225 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 44 | 10 | -0.5383528 | 300.44199736363635 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 142 | 53 | -0.41678739 | 729.465611415493 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 43 | 9 | -0.55263566 | 301.1710950930232 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 140 | 51 | -0.42398719 | 729.4041205 | False |