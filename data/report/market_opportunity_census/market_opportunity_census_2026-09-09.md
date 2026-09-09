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
| KRX/KRX_REGULAR | 314 | 10 | 3.18 | 8.6 |
| NXT/NXT_AFTERMARKET | 101 | 2 | 1.98 | 12.87 |
| NXT/NXT_PREMARKET | 34 | 1 | 2.94 | 11.76 |
| NXT/NXT_REGULAR_OVERLAP | 312 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 314 | 10 | 3.18 | 8.6 | 314 | 0 | pass |
| NXT | 447 | 3 | 0.67 | 3.8 | 447 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=219, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=1, `entry_decision_rejected`=17, `late_discovery_after_opportunity_window`=22, `scanner_discovery_gap_or_unobserved`=28, `scanner_fetch_seen_pool_unobserved`=7, `scanner_source_guard_blocked_before_promotion`=11
- NXT terminal coverage reasons: `candidate_not_promoted`=54, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=1, `entry_decision_observe_only`=1, `entry_decision_rejected`=3, `late_discovery_after_opportunity_window`=10, `scanner_discovery_gap_or_unobserved`=364, `scanner_fetch_seen_pool_unobserved`=2, `scanner_runtime_attach_gap`=3

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=45, `market_gainer_reserved_full`=24, `max_new_codes_reached`=21, `reentry_cooldown_no_material_upgrade`=48, `returned`=81; count_sum=219; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=1, `max_new_codes_reached`=2, `returned`=51; count_sum=54; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=2641, valid=2641, invalid=0, unique=2641, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 314 | 144 | 45.86 | 124 | 63 | 49.19 | -0.33269331 | None | False |
| NXT | 447 | 316 | 70.69 | 297 | 146 | 49.31 | -0.12377821 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 376 | 5.32 | 5.32 | 1.06 | 39 | 11.883545 | 0 |
| all | 10 | KRX | forward_exact | 164 | 8.54 | 8.54 | 1.83 | 30 | 11.883545 | 0 |
| all | 10 | NXT | forward_exact | 212 | 2.83 | 2.83 | 0.47 | 9 | 8.846703 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 376 | 91.49 | 90.96 | 74.2 | 95 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 164 | 81.1 | 80.49 | 61.59 | 64 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 212 | 99.53 | 99.06 | 83.96 | 31 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 376 | 91.22 | 90.69 | 63.03 | 176 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 164 | 80.49 | 79.88 | 60.98 | 81 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 212 | 99.53 | 99.06 | 64.62 | 95 | None | 0 |
| all | 20 | ALL | forward_exact | 741 | 6.34 | 6.34 | 1.21 | 80 | 31.843244 | 0 |
| all | 20 | KRX | forward_exact | 308 | 11.04 | 11.04 | 2.6 | 60 | 31.843244 | 0 |
| all | 20 | NXT | forward_exact | 433 | 3.0 | 3.0 | 0.23 | 20 | 39.14875 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 741 | 93.79 | 92.58 | 72.74 | 173 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 308 | 86.69 | 86.04 | 71.43 | 127 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 433 | 98.85 | 97.23 | 73.67 | 46 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 741 | 93.52 | 92.04 | 64.91 | 340 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 308 | 86.04 | 85.39 | 71.1 | 161 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 433 | 98.85 | 96.77 | 60.51 | 179 | None | 0 |
| all | 50 | ALL | forward_exact | 1853 | 4.43 | 4.1 | 0.7 | 94 | 34.072349 | 0 |
| all | 50 | KRX | forward_exact | 769 | 7.67 | 7.28 | 1.69 | 79 | 34.072349 | 0 |
| all | 50 | NXT | forward_exact | 1084 | 2.12 | 1.85 | 0.0 | 15 | 86.011592 | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1853 | 88.07 | 86.89 | 48.03 | 289 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 769 | 78.67 | 77.76 | 58.0 | 236 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1084 | 94.74 | 93.36 | 40.96 | 53 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1853 | 85.54 | 81.98 | 38.32 | 516 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 769 | 75.55 | 75.03 | 52.93 | 302 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1084 | 92.62 | 86.9 | 27.95 | 214 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 399 | 4.76 | 4.51 | 1.75 | 38 | 23.650064 | 0 |
| liquid_common | 10 | KRX | forward_exact | 170 | 7.65 | 7.65 | 3.53 | 27 | 33.832444 | 0 |
| liquid_common | 10 | NXT | forward_exact | 229 | 2.62 | 2.18 | 0.44 | 11 | 17.9639 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 399 | 95.99 | 95.74 | 79.7 | 106 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 170 | 90.59 | 90.59 | 72.35 | 72 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 229 | 100.0 | 99.56 | 85.15 | 34 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 399 | 95.99 | 95.74 | 68.67 | 193 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 170 | 90.59 | 90.59 | 72.35 | 89 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 229 | 100.0 | 99.56 | 65.94 | 104 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 776 | 5.93 | 5.54 | 1.8 | 73 | 33.832444 | 0 |
| liquid_common | 20 | KRX | forward_exact | 329 | 8.81 | 8.81 | 3.34 | 52 | 41.300243 | 0 |
| liquid_common | 20 | NXT | forward_exact | 447 | 3.8 | 3.13 | 0.67 | 21 | 28.904429 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 776 | 97.42 | 97.29 | 77.45 | 189 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 329 | 94.53 | 94.53 | 81.16 | 140 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 447 | 99.55 | 99.33 | 74.72 | 49 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 776 | 97.42 | 97.16 | 69.59 | 355 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 329 | 94.53 | 94.53 | 81.16 | 176 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 447 | 99.55 | 99.11 | 61.07 | 179 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1929 | 3.84 | 3.42 | 0.88 | 87 | 29.542838 | 0 |
| liquid_common | 50 | KRX | forward_exact | 802 | 6.36 | 5.99 | 1.75 | 72 | 29.542838 | 0 |
| liquid_common | 50 | NXT | forward_exact | 1127 | 2.04 | 1.6 | 0.27 | 15 | 28.904429 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1929 | 93.11 | 92.48 | 52.77 | 356 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 802 | 89.03 | 88.65 | 69.58 | 301 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1127 | 96.01 | 95.21 | 40.82 | 55 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1929 | 92.12 | 89.06 | 42.56 | 587 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 802 | 87.28 | 86.91 | 64.21 | 374 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 1127 | 95.56 | 90.59 | 27.15 | 213 | None | 0 |

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
| KRX/KRX_REGULAR | diagnostic_ready | 61/329 | {'capture_gap_or_pending_validity_window': 233, 'intended_new_buy_hard_cutoff': 20, 'master_unverified_or_not_common_equity': 15} | insufficient_economic_evidence |
| NXT/NXT_AFTERMARKET | diagnostic_ready | 54/101 | {'intended_new_buy_hard_cutoff': 25, 'capture_gap_or_pending_validity_window': 22} | insufficient_economic_evidence |
| NXT/NXT_PREMARKET | diagnostic_ready | 34/34 | {} | insufficient_economic_evidence |
| NXT/NXT_REGULAR_OVERLAP | insufficient_evidence_scanner_recall | 0/312 | {'main_overlap_route_policy_unproven': 290, 'intended_new_buy_hard_cutoff': 22} | insufficient_economic_evidence |

## Small net alternatives (source-only, non-additive)

| Venue/session | Net target / horizon | Resolved | Profitable | Observed EV % | Mean duration sec | Ready |
|---|---|---:|---:|---:|---:|---|
| KRX/KRX_REGULAR | net_0.03_h60 | 4 | 0 | -0.79816887 | 10.82156275 | False |
| KRX/KRX_REGULAR | net_0.03_h180 | 11 | 3 | -0.62964997 | 87.93990918181818 | False |
| KRX/KRX_REGULAR | net_0.03_h300 | 39 | 13 | -0.53027806 | 241.16857428205128 | False |
| KRX/KRX_REGULAR | net_0.03_h1200 | 67 | 31 | -0.30655345 | 475.9769515522388 | False |
| KRX/KRX_REGULAR | net_0.07_h60 | 4 | 0 | -0.79816887 | 10.82156275 | False |
| KRX/KRX_REGULAR | net_0.07_h180 | 11 | 3 | -0.62964997 | 87.93990918181818 | False |
| KRX/KRX_REGULAR | net_0.07_h300 | 39 | 13 | -0.53027806 | 241.16857428205128 | False |
| KRX/KRX_REGULAR | net_0.07_h1200 | 66 | 30 | -0.31207349 | 475.0627638030303 | False |
| KRX/KRX_REGULAR | net_0.10_h60 | 4 | 0 | -0.79816887 | 10.82156275 | False |
| KRX/KRX_REGULAR | net_0.10_h180 | 11 | 3 | -0.62964997 | 87.93990918181818 | False |
| KRX/KRX_REGULAR | net_0.10_h300 | 39 | 13 | -0.53027806 | 241.16857428205128 | False |
| KRX/KRX_REGULAR | net_0.10_h1200 | 66 | 30 | -0.31207349 | 475.0627638030303 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.03_h300 | 38 | 6 | -0.40128336 | 301.763845 | False |
| NXT/NXT_AFTERMARKET | net_0.03_h1200 | 58 | 20 | -0.22732072 | 932.0044533275861 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.07_h300 | 38 | 6 | -0.40128336 | 301.763845 | False |
| NXT/NXT_AFTERMARKET | net_0.07_h1200 | 56 | 17 | -0.2227839 | 986.7066549107143 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_AFTERMARKET | net_0.10_h300 | 38 | 6 | -0.40128336 | 301.763845 | False |
| NXT/NXT_AFTERMARKET | net_0.10_h1200 | 55 | 16 | -0.228154 | 982.8627756000001 | False |
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
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h300 | 70 | 24 | -0.07974558 | 307.96055717142855 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.03_h1200 | 87 | 52 | -0.00872543 | 734.11566 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h300 | 70 | 24 | -0.07974558 | 307.96055717142855 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.07_h1200 | 86 | 51 | -0.00934694 | 732.2221754186047 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h60 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h180 | 0 | 0 | None | None | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h300 | 70 | 24 | -0.07974558 | 307.96055717142855 | False |
| NXT/NXT_REGULAR_OVERLAP | net_0.10_h1200 | 82 | 47 | -0.01371918 | 724.0968484268293 | False |