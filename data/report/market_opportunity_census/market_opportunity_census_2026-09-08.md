# Market Opportunity Census - 2026-09-08

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_resolved_outcome_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_REGULAR | 23 | 0 | 0.0 | 26.09 |
| NXT/NXT_PREMARKET | 36 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 33 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 23 | 0 | 0.0 | 26.09 | 23 | 0 | pass |
| NXT | 69 | 0 | 0.0 | 0.0 | 69 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=9, `entry_ai_trace_gap`=1, `late_discovery_after_opportunity_window`=1, `post_authority_submit_safety_gap`=1, `scanner_discovery_gap_or_unobserved`=5, `scanner_fast_precheck_gap`=4, `scanner_source_guard_blocked_before_promotion`=2
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=69

### Candidate Not Promoted First Reasons

- KRX: `market_gainer_reserved_full`=9; count_sum=9; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=322, valid=322, invalid=0, unique=322, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 23 | 19 | 82.61 | 15 | 8 | 0.0 | -1.83164258 | None | False |
| NXT | 69 | 66 | 95.65 | 63 | 34 | 27.66 | -0.68446561 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 66 | 1.52 | 0.0 | 0.0 | 2 | None | 0 |
| all | 10 | KRX | forward_exact | 16 | 6.25 | 0.0 | 0.0 | 2 | None | 0 |
| all | 10 | NXT | forward_exact | 50 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 66 | 71.21 | 62.12 | 4.55 | 5 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 16 | 43.75 | 18.75 | 0.0 | 5 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 50 | 80.0 | 76.0 | 6.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 66 | 10.61 | 4.55 | 0.0 | 5 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 16 | 43.75 | 18.75 | 0.0 | 5 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 50 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 128 | 3.12 | 1.56 | 0.0 | 6 | None | 0 |
| all | 20 | KRX | forward_exact | 32 | 12.5 | 6.25 | 0.0 | 6 | None | 0 |
| all | 20 | NXT | forward_exact | 96 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 128 | 67.19 | 57.03 | 2.34 | 9 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 32 | 37.5 | 25.0 | 0.0 | 9 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 96 | 77.08 | 67.71 | 3.12 | 0 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 128 | 9.38 | 6.25 | 0.0 | 9 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 32 | 37.5 | 25.0 | 0.0 | 9 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 96 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 347 | 0.58 | 0.0 | 0.0 | 7 | None | 0 |
| all | 50 | KRX | forward_exact | 83 | 2.41 | 0.0 | 0.0 | 7 | None | 0 |
| all | 50 | NXT | forward_exact | 264 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 347 | 51.59 | 42.65 | 1.15 | 12 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 83 | 26.51 | 15.66 | 1.2 | 12 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 264 | 59.47 | 51.14 | 1.14 | 0 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 347 | 6.34 | 3.75 | 0.29 | 12 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 83 | 26.51 | 15.66 | 1.2 | 12 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 264 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 53 | 7.55 | 1.89 | 0.0 | 4 | None | 0 |
| liquid_common | 10 | KRX | forward_exact | 13 | 30.77 | 7.69 | 0.0 | 4 | None | 0 |
| liquid_common | 10 | NXT | forward_exact | 40 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 53 | 86.79 | 73.58 | 3.77 | 6 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 13 | 61.54 | 30.77 | 0.0 | 6 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 40 | 95.0 | 87.5 | 5.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 53 | 15.09 | 7.55 | 0.0 | 6 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 13 | 61.54 | 30.77 | 0.0 | 6 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 40 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 93 | 6.45 | 2.15 | 0.0 | 7 | None | 0 |
| liquid_common | 20 | KRX | forward_exact | 24 | 25.0 | 8.33 | 0.0 | 7 | None | 0 |
| liquid_common | 20 | NXT | forward_exact | 69 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 93 | 79.57 | 69.89 | 3.23 | 9 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 24 | 50.0 | 33.33 | 4.17 | 9 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 69 | 89.86 | 82.61 | 2.9 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 93 | 12.9 | 8.6 | 1.08 | 9 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 24 | 50.0 | 33.33 | 4.17 | 9 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 69 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 236 | 3.39 | 1.27 | 0.0 | 7 | None | 0 |
| liquid_common | 50 | KRX | forward_exact | 60 | 13.33 | 5.0 | 0.0 | 7 | None | 0 |
| liquid_common | 50 | NXT | forward_exact | 176 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 236 | 64.83 | 53.81 | 1.69 | 10 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 60 | 43.33 | 23.33 | 3.33 | 10 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 176 | 72.16 | 64.2 | 1.14 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 236 | 11.02 | 5.93 | 0.85 | 10 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 60 | 43.33 | 23.33 | 3.33 | 10 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 176 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
