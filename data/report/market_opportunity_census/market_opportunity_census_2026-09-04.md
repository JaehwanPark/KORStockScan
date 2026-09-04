# Market Opportunity Census - 2026-09-04

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 229 | 1 | 0.44 | 5.24 | 229 | 0 | pass |
| NXT | 461 | 2 | 0.43 | 3.47 | 461 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=129, `entry_ai_trace_gap`=7, `late_discovery_after_opportunity_window`=25, `post_authority_submit_safety_gap`=5, `scanner_discovery_gap_or_unobserved`=61, `scanner_source_guard_blocked_before_promotion`=2
- NXT terminal coverage reasons: `candidate_not_promoted`=69, `entry_ai_trace_gap`=5, `entry_authority_guard_block`=2, `late_discovery_after_opportunity_window`=10, `post_authority_submit_safety_gap`=6, `scanner_discovery_gap_or_unobserved`=365, `scanner_fast_precheck_gap`=2, `scanner_heavy_eval_gap`=1, `scanner_source_guard_blocked_before_promotion`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=19, `market_gainer_reserved_full`=39, `max_new_codes_reached`=6, `reentry_cooldown_no_material_upgrade`=65; count_sum=129; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=2, `market_gainer_reserved_full`=8, `reentry_cooldown_no_material_upgrade`=59; count_sum=69; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=1962, valid=1962, invalid=0, unique=1962, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 229 | 152 | 66.38 | 137 | 41 | 70.07 | -0.4253275 | None | False |
| NXT | 461 | 343 | 74.4 | 327 | 117 | 62.38 | -0.38947785 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 345 | 4.93 | 6.67 | 1.16 | 30 | 34.944109 | 0 |
| all | 10 | KRX | forward_exact | 117 | 9.4 | 11.97 | 0.85 | 21 | 16.840873 | 0 |
| all | 10 | NXT | forward_exact | 228 | 2.63 | 3.95 | 1.32 | 9 | 41.43778 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 345 | 93.62 | 90.14 | 64.93 | 84 | None | 31 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 117 | 83.76 | 75.21 | 46.15 | 46 | None | 5 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 228 | 98.68 | 97.81 | 74.56 | 38 | None | 26 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 345 | 93.62 | 90.14 | 50.14 | 244 | None | 5 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 117 | 83.76 | 75.21 | 40.17 | 46 | None | 5 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 228 | 98.68 | 97.81 | 55.26 | 198 | None | 0 |
| all | 20 | ALL | forward_exact | 717 | 6.69 | 8.79 | 1.26 | 86 | 35.457595 | 0 |
| all | 20 | KRX | forward_exact | 265 | 12.83 | 15.85 | 2.26 | 60 | 26.905924 | 0 |
| all | 20 | NXT | forward_exact | 452 | 3.1 | 4.65 | 0.66 | 26 | 41.43778 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 717 | 94.28 | 90.93 | 55.09 | 234 | None | 49 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 265 | 87.17 | 81.89 | 53.21 | 128 | None | 18 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 452 | 98.45 | 96.24 | 56.19 | 106 | None | 31 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 717 | 94.28 | 90.38 | 43.79 | 463 | None | 18 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 265 | 87.17 | 81.89 | 44.15 | 128 | None | 18 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 452 | 98.45 | 95.35 | 43.58 | 335 | None | 0 |
| all | 50 | ALL | forward_exact | 1759 | 3.64 | 4.49 | 0.51 | 92 | 29.329743 | 1 |
| all | 50 | KRX | forward_exact | 617 | 7.62 | 8.59 | 0.97 | 72 | 26.905924 | 1 |
| all | 50 | NXT | forward_exact | 1142 | 1.49 | 2.28 | 0.26 | 20 | 41.43778 | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1759 | 90.62 | 81.92 | 29.96 | 346 | None | 62 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 617 | 79.9 | 74.07 | 35.82 | 234 | None | 24 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1142 | 96.41 | 86.16 | 26.8 | 112 | None | 38 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1759 | 88.29 | 79.08 | 22.06 | 584 | None | 24 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 617 | 76.99 | 70.34 | 25.28 | 217 | None | 24 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 1142 | 94.4 | 83.8 | 20.32 | 367 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 359 | 2.79 | 5.29 | 0.28 | 26 | 25.349766 | 0 |
| liquid_common | 10 | KRX | forward_exact | 124 | 4.03 | 8.87 | 0.81 | 17 | 32.081776 | 0 |
| liquid_common | 10 | NXT | forward_exact | 235 | 2.13 | 3.4 | 0.0 | 9 | 25.349766 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 359 | 99.44 | 96.38 | 64.62 | 103 | None | 33 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 124 | 99.19 | 90.32 | 45.97 | 64 | None | 4 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 235 | 99.57 | 99.57 | 74.47 | 39 | None | 29 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 359 | 99.44 | 96.38 | 49.58 | 271 | None | 4 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 124 | 99.19 | 90.32 | 39.52 | 64 | None | 4 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 235 | 99.57 | 99.57 | 54.89 | 207 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 704 | 3.98 | 6.96 | 0.43 | 63 | 41.297827 | 0 |
| liquid_common | 20 | KRX | forward_exact | 243 | 4.94 | 11.11 | 0.41 | 37 | 32.081776 | 0 |
| liquid_common | 20 | NXT | forward_exact | 461 | 3.47 | 4.77 | 0.43 | 26 | 41.297827 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 704 | 98.3 | 96.31 | 57.81 | 233 | None | 47 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 243 | 95.88 | 90.53 | 55.56 | 126 | None | 13 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 461 | 99.57 | 99.35 | 59.0 | 107 | None | 34 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 704 | 98.15 | 95.74 | 45.6 | 482 | None | 13 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 243 | 95.88 | 90.53 | 45.27 | 126 | None | 13 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 461 | 99.35 | 98.48 | 45.77 | 356 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1748 | 2.17 | 3.66 | 0.23 | 64 | 41.297827 | 0 |
| liquid_common | 50 | KRX | forward_exact | 570 | 2.63 | 5.96 | 0.35 | 44 | 32.081776 | 0 |
| liquid_common | 50 | NXT | forward_exact | 1178 | 1.95 | 2.55 | 0.17 | 20 | 41.297827 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1748 | 94.39 | 87.93 | 32.67 | 358 | None | 64 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 570 | 89.3 | 83.33 | 41.4 | 243 | None | 24 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1178 | 96.86 | 90.15 | 28.44 | 115 | None | 40 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1748 | 92.85 | 84.84 | 24.08 | 613 | None | 24 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 570 | 85.79 | 78.77 | 29.82 | 225 | None | 24 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 1178 | 96.26 | 87.78 | 21.31 | 388 | None | 0 |

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
