# Market Opportunity Census - 2026-09-07

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`
- scanner_recall_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `ex_post_executable_bbo_join_coverage_floor_not_met`, `ex_post_executable_right_censored_ceiling_exceeded`

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue/session-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue/session | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % |
|---|---:|---:|---:|---:|
| KRX/KRX_REGULAR | 299 | 3 | 1.0 | 10.37 |
| NXT/NXT_AFTERMARKET | 104 | 1 | 0.96 | 11.54 |
| NXT/NXT_PREMARKET | 43 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 303 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 299 | 3 | 1.0 | 10.37 | 299 | 0 | pass |
| NXT | 450 | 1 | 0.22 | 2.67 | 450 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=206, `entry_ai_trace_gap`=17, `entry_authority_guard_block`=1, `late_discovery_after_opportunity_window`=19, `post_authority_submit_safety_gap`=11, `scanner_discovery_gap_or_unobserved`=37, `scanner_fast_precheck_gap`=2, `scanner_source_guard_blocked_before_promotion`=6
- NXT terminal coverage reasons: `candidate_not_promoted`=57, `entry_ai_trace_gap`=8, `late_discovery_after_opportunity_window`=11, `post_authority_submit_safety_gap`=2, `scanner_discovery_gap_or_unobserved`=370, `scanner_fast_precheck_gap`=1, `scanner_heavy_eval_gap`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=38, `market_gainer_reserved_full`=65, `max_new_codes_reached`=19, `reentry_cooldown_no_material_upgrade`=84; count_sum=206; conservation_delta=0; conservation_status=`pass`
- NXT: `general_slot_limit`=12, `manual_control_excluded`=3, `market_gainer_reserved_full`=2, `reentry_cooldown_no_material_upgrade`=40; count_sum=57; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=2767, valid=2767, invalid=0, unique=2767, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 299 | 202 | 67.56 | 170 | 102 | 40.0 | -0.6622159 | None | False |
| NXT | 450 | 382 | 84.89 | 369 | 201 | 45.23 | -0.16775925 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 335 | 2.99 | 2.39 | 0.3 | 19 | 123.207316 | 0 |
| all | 10 | KRX | forward_exact | 129 | 3.1 | 3.1 | 0.0 | 6 | None | 0 |
| all | 10 | NXT | forward_exact | 206 | 2.91 | 1.94 | 0.49 | 13 | 123.207316 | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 335 | 74.93 | 74.33 | 47.16 | 86 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 129 | 43.41 | 43.41 | 30.23 | 51 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 206 | 94.66 | 93.69 | 57.77 | 35 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 335 | 71.34 | 70.45 | 37.31 | 215 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 129 | 43.41 | 43.41 | 30.23 | 51 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 206 | 88.83 | 87.38 | 41.75 | 164 | None | 0 |
| all | 20 | ALL | forward_exact | 674 | 6.23 | 5.64 | 0.74 | 62 | 55.057661 | 0 |
| all | 20 | KRX | forward_exact | 273 | 10.99 | 10.62 | 1.47 | 40 | 17.606875 | 0 |
| all | 20 | NXT | forward_exact | 401 | 2.99 | 2.24 | 0.25 | 22 | 123.207316 | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 674 | 81.01 | 80.42 | 51.19 | 182 | None | 6 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 273 | 57.88 | 57.88 | 44.69 | 116 | None | 6 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 401 | 96.76 | 95.76 | 55.61 | 66 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 674 | 78.19 | 77.0 | 43.18 | 410 | None | 6 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 273 | 57.88 | 57.88 | 43.96 | 116 | None | 6 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 401 | 92.02 | 90.02 | 42.64 | 294 | None | 0 |
| all | 50 | ALL | forward_exact | 1624 | 4.37 | 3.57 | 0.49 | 97 | 52.123117 | 1 |
| all | 50 | KRX | forward_exact | 636 | 8.81 | 7.55 | 0.94 | 79 | 18.432493 | 0 |
| all | 50 | NXT | forward_exact | 988 | 1.52 | 1.01 | 0.2 | 18 | 52.123117 | 1 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1624 | 80.54 | 77.59 | 30.73 | 282 | None | 13 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 636 | 58.33 | 57.39 | 34.91 | 207 | None | 8 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 988 | 94.84 | 90.59 | 28.04 | 75 | None | 5 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1624 | 78.33 | 72.29 | 24.63 | 522 | None | 13 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 636 | 57.55 | 56.6 | 32.7 | 202 | None | 8 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 988 | 91.7 | 82.39 | 19.43 | 320 | None | 5 |
| liquid_common | 10 | ALL | forward_exact | 392 | 4.59 | 4.08 | 0.51 | 35 | 46.546471 | 0 |
| liquid_common | 10 | KRX | forward_exact | 156 | 7.05 | 6.41 | 0.64 | 20 | 13.351593 | 0 |
| liquid_common | 10 | NXT | forward_exact | 236 | 2.97 | 2.54 | 0.42 | 15 | 123.207316 | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 392 | 88.78 | 88.52 | 58.16 | 140 | None | 1 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 156 | 78.21 | 77.56 | 57.69 | 100 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 236 | 95.76 | 95.76 | 58.47 | 40 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 392 | 84.95 | 84.69 | 46.94 | 288 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 156 | 78.21 | 77.56 | 57.05 | 100 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 236 | 89.41 | 89.41 | 40.25 | 188 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 766 | 5.61 | 5.09 | 0.52 | 73 | 46.546471 | 0 |
| liquid_common | 20 | KRX | forward_exact | 316 | 9.81 | 9.18 | 0.95 | 50 | 33.333622 | 0 |
| liquid_common | 20 | NXT | forward_exact | 450 | 2.67 | 2.22 | 0.22 | 23 | 123.207316 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 766 | 89.69 | 89.43 | 56.53 | 251 | None | 7 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 316 | 79.75 | 79.43 | 55.7 | 175 | None | 7 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 450 | 96.67 | 96.44 | 57.11 | 76 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 766 | 86.81 | 86.03 | 47.91 | 508 | None | 7 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 316 | 79.75 | 79.43 | 54.75 | 175 | None | 7 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 450 | 91.78 | 90.67 | 43.11 | 333 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1850 | 3.57 | 3.08 | 0.49 | 99 | 52.123117 | 1 |
| liquid_common | 50 | KRX | forward_exact | 757 | 6.34 | 5.81 | 0.79 | 78 | 46.546471 | 0 |
| liquid_common | 50 | NXT | forward_exact | 1093 | 1.65 | 1.19 | 0.27 | 21 | 92.241223 | 1 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1850 | 84.81 | 82.54 | 34.54 | 367 | None | 16 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 757 | 70.81 | 68.69 | 40.16 | 280 | None | 9 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 1093 | 94.51 | 92.13 | 30.65 | 87 | None | 7 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1850 | 82.7 | 78.11 | 27.41 | 648 | None | 16 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 757 | 69.62 | 67.5 | 36.59 | 271 | None | 9 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 1093 | 91.77 | 85.45 | 21.04 | 377 | None | 7 |

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
