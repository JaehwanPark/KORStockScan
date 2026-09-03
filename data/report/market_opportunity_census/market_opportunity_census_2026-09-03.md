# Market Opportunity Census - 2026-09-03

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
| KRX | 214 | 8 | 3.74 | 17.76 | 214 | 0 | pass |
| NXT | 391 | 0 | 0.0 | 2.81 | 391 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=140, `entry_ai_trace_gap`=19, `entry_authority_guard_block`=5, `late_discovery_after_opportunity_window`=25, `post_authority_submit_safety_gap`=13, `scanner_discovery_gap_or_unobserved`=2, `scanner_fast_precheck_gap`=1, `scanner_source_guard_blocked_before_promotion`=9
- NXT terminal coverage reasons: `candidate_not_promoted`=48, `entry_ai_trace_gap`=9, `late_discovery_after_opportunity_window`=10, `post_authority_submit_safety_gap`=1, `scanner_discovery_gap_or_unobserved`=322, `scanner_fast_precheck_gap`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=10, `manual_control_excluded`=5, `market_gainer_reserved_full`=46, `max_new_codes_reached`=8, `reentry_cooldown_no_material_upgrade`=71; count_sum=140; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=1, `manual_control_excluded`=4, `market_gainer_reserved_full`=11, `reentry_cooldown_no_material_upgrade`=32; count_sum=48; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=2780, valid=2740, invalid=40, unique=2740, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 214 | 102 | 47.66 | 94 | 70 | 25.53 | -0.17645257 | None | False |
| NXT | 391 | 221 | 56.52 | 203 | 111 | 44.22 | -0.43661888 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 336 | 7.14 | 10.42 | 1.19 | 33 | 40.516588 | 0 |
| all | 10 | KRX | forward_exact | 117 | 16.24 | 23.93 | 3.42 | 26 | 40.516588 | 0 |
| all | 10 | NXT | forward_exact | 219 | 2.28 | 3.2 | 0.0 | 7 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 336 | 88.39 | 85.71 | 56.85 | 102 | None | 3 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 117 | 83.76 | 79.49 | 64.1 | 60 | None | 3 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 219 | 90.87 | 89.04 | 52.97 | 42 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 336 | 87.2 | 84.23 | 45.24 | 207 | None | 3 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 117 | 83.76 | 79.49 | 64.1 | 60 | None | 3 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 219 | 89.04 | 86.76 | 35.16 | 147 | None | 0 |
| all | 20 | ALL | forward_exact | 634 | 7.1 | 10.57 | 1.26 | 71 | 39.585279 | 0 |
| all | 20 | KRX | forward_exact | 226 | 16.81 | 24.78 | 3.54 | 59 | 39.585279 | 0 |
| all | 20 | NXT | forward_exact | 408 | 1.72 | 2.7 | 0.0 | 12 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 634 | 82.65 | 79.5 | 44.95 | 150 | None | 4 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 226 | 76.99 | 72.57 | 53.98 | 96 | None | 4 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 408 | 85.78 | 83.33 | 39.95 | 54 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 634 | 79.97 | 76.18 | 35.17 | 305 | None | 4 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 226 | 76.99 | 72.57 | 53.98 | 96 | None | 4 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 408 | 81.62 | 78.19 | 24.75 | 209 | None | 0 |
| all | 50 | ALL | forward_exact | 1455 | 3.44 | 4.6 | 0.34 | 53 | 19.672139 | 0 |
| all | 50 | KRX | forward_exact | 520 | 7.31 | 10.19 | 0.96 | 46 | 19.672139 | 0 |
| all | 50 | NXT | forward_exact | 935 | 1.28 | 1.5 | 0.0 | 7 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1455 | 79.04 | 75.12 | 27.97 | 235 | None | 6 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 520 | 70.19 | 66.92 | 31.54 | 180 | None | 3 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 935 | 83.96 | 79.68 | 25.99 | 55 | None | 3 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1455 | 76.01 | 70.31 | 18.69 | 390 | None | 3 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 520 | 69.04 | 65.58 | 30.58 | 176 | None | 3 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 935 | 79.89 | 72.94 | 12.09 | 214 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 331 | 7.25 | 11.18 | 1.51 | 37 | 40.516588 | 0 |
| liquid_common | 10 | KRX | forward_exact | 111 | 16.22 | 23.42 | 4.5 | 26 | 29.63493 | 0 |
| liquid_common | 10 | NXT | forward_exact | 220 | 2.73 | 5.0 | 0.0 | 11 | 57.040875 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 331 | 94.56 | 92.15 | 64.05 | 111 | None | 4 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 111 | 99.1 | 94.59 | 80.18 | 71 | None | 4 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 220 | 92.27 | 90.91 | 55.91 | 40 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 331 | 93.96 | 90.94 | 51.96 | 224 | None | 4 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 111 | 99.1 | 94.59 | 80.18 | 71 | None | 4 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 220 | 91.36 | 89.09 | 37.73 | 153 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 612 | 8.01 | 12.09 | 1.31 | 82 | 37.71227 | 0 |
| liquid_common | 20 | KRX | forward_exact | 221 | 17.19 | 24.89 | 3.62 | 61 | 37.71227 | 0 |
| liquid_common | 20 | NXT | forward_exact | 391 | 2.81 | 4.86 | 0.0 | 21 | 57.040875 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 612 | 89.71 | 88.24 | 53.59 | 171 | None | 5 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 221 | 93.21 | 90.95 | 70.59 | 120 | None | 5 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 391 | 87.72 | 86.7 | 43.99 | 51 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 612 | 86.93 | 84.97 | 43.14 | 340 | None | 5 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 221 | 93.21 | 90.95 | 70.59 | 120 | None | 5 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 391 | 83.38 | 81.59 | 27.62 | 220 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1450 | 4.83 | 6.55 | 0.41 | 64 | 24.897856 | 0 |
| liquid_common | 50 | KRX | forward_exact | 531 | 9.23 | 12.81 | 1.13 | 48 | 19.672139 | 0 |
| liquid_common | 50 | NXT | forward_exact | 919 | 2.29 | 2.94 | 0.0 | 16 | 57.040875 | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1450 | 86.14 | 83.03 | 34.69 | 261 | None | 8 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 531 | 86.06 | 83.24 | 43.31 | 200 | None | 5 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 919 | 86.18 | 82.92 | 29.71 | 61 | None | 3 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1450 | 83.59 | 79.66 | 23.93 | 435 | None | 5 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 531 | 84.93 | 81.73 | 42.18 | 196 | None | 5 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 919 | 82.81 | 78.45 | 13.38 | 239 | None | 0 |

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
