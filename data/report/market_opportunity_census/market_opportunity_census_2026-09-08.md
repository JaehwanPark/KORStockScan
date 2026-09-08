# Market Opportunity Census - 2026-09-08

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
| KRX/KRX_REGULAR | 166 | 0 | 0.0 | 9.64 |
| NXT/NXT_PREMARKET | 36 | 0 | 0.0 | 0.0 |
| NXT/NXT_REGULAR_OVERLAP | 210 | 0 | 0.0 | 0.0 |

### Venue aggregation (diagnostic only)

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 166 | 0 | 0.0 | 9.64 | 166 | 0 | pass |
| NXT | 246 | 0 | 0.0 | 0.0 | 246 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=104, `entry_ai_trace_gap`=4, `late_discovery_after_opportunity_window`=17, `post_authority_submit_safety_gap`=3, `scanner_discovery_gap_or_unobserved`=26, `scanner_fast_precheck_gap`=8, `scanner_heavy_eval_gap`=1, `scanner_source_guard_blocked_before_promotion`=3
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=246

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=8, `market_gainer_reserved_full`=23, `max_new_codes_reached`=2, `reentry_cooldown_no_material_upgrade`=71; count_sum=104; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Ex-post Executable Opportunity (Source-only)

- Direct external-census, promoted-WS, and bounded prune-observer exact-route BBOs only; ka10027 mark prices are never substituted for executable prices.
- comparison cost: `0.23%`
- external BBO request reservation conservation: attempted=882, valid=882, invalid=0, unique=882, duplicate=0, delta=0, status=`pass`

| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KRX | 166 | 112 | 67.47 | 100 | 60 | 38.14 | -0.03729207 | None | False |
| NXT | 246 | 212 | 86.18 | 201 | 96 | 51.76 | -0.51172656 | None | False |

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 202 | 2.48 | 0.5 | 0.0 | 11 | None | 0 |
| all | 10 | KRX | forward_exact | 70 | 7.14 | 1.43 | 0.0 | 11 | None | 0 |
| all | 10 | NXT | forward_exact | 132 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 202 | 81.68 | 73.76 | 20.3 | 52 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 70 | 72.86 | 71.43 | 18.57 | 41 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 132 | 86.36 | 75.0 | 21.21 | 11 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 202 | 25.25 | 24.75 | 6.44 | 41 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 70 | 72.86 | 71.43 | 18.57 | 41 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 132 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 395 | 3.54 | 2.03 | 0.25 | 27 | 24.401143 | 0 |
| all | 20 | KRX | forward_exact | 137 | 10.22 | 5.84 | 0.73 | 27 | 24.401143 | 0 |
| all | 20 | NXT | forward_exact | 258 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 395 | 84.3 | 72.41 | 16.2 | 84 | None | 0 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 137 | 76.64 | 74.45 | 22.63 | 70 | None | 0 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 258 | 88.37 | 71.32 | 12.79 | 14 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 395 | 26.58 | 25.82 | 7.85 | 70 | None | 0 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 137 | 76.64 | 74.45 | 22.63 | 70 | None | 0 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 258 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 1018 | 1.47 | 0.88 | 0.1 | 34 | 24.401143 | 0 |
| all | 50 | KRX | forward_exact | 352 | 4.26 | 2.56 | 0.28 | 34 | 24.401143 | 0 |
| all | 50 | NXT | forward_exact | 666 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1018 | 72.1 | 58.25 | 10.22 | 161 | None | 0 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 352 | 66.48 | 59.66 | 16.19 | 144 | None | 0 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 666 | 75.08 | 57.51 | 7.06 | 17 | None | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 1018 | 22.99 | 20.63 | 5.6 | 144 | None | 0 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 352 | 66.48 | 59.66 | 16.19 | 144 | None | 0 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 666 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 223 | 4.93 | 1.79 | 0.0 | 16 | None | 0 |
| liquid_common | 10 | KRX | forward_exact | 95 | 11.58 | 4.21 | 0.0 | 16 | None | 0 |
| liquid_common | 10 | NXT | forward_exact | 128 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 223 | 86.1 | 77.58 | 21.08 | 70 | None | 0 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 95 | 80.0 | 78.95 | 20.0 | 61 | None | 0 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 128 | 90.62 | 76.56 | 21.88 | 9 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 223 | 34.08 | 33.63 | 8.52 | 61 | None | 0 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 95 | 80.0 | 78.95 | 20.0 | 61 | None | 0 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 128 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 436 | 3.9 | 1.61 | 0.0 | 36 | None | 0 |
| liquid_common | 20 | KRX | forward_exact | 190 | 8.95 | 3.68 | 0.0 | 36 | None | 0 |
| liquid_common | 20 | NXT | forward_exact | 246 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 436 | 88.76 | 78.21 | 18.35 | 118 | None | 0 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 190 | 84.74 | 82.11 | 24.74 | 104 | None | 0 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 246 | 91.87 | 75.2 | 13.41 | 14 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 436 | 36.93 | 35.78 | 10.78 | 104 | None | 0 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 190 | 84.74 | 82.11 | 24.74 | 104 | None | 0 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 246 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 1096 | 2.19 | 1.09 | 0.0 | 46 | 12.967943 | 0 |
| liquid_common | 50 | KRX | forward_exact | 479 | 5.01 | 2.51 | 0.0 | 46 | 12.967943 | 0 |
| liquid_common | 50 | NXT | forward_exact | 617 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 1096 | 78.74 | 64.14 | 13.05 | 230 | None | 0 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 479 | 78.08 | 68.89 | 19.42 | 214 | None | 0 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 617 | 79.25 | 60.45 | 8.1 | 16 | None | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 1096 | 34.12 | 30.11 | 8.49 | 214 | None | 0 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 479 | 78.08 | 68.89 | 19.42 | 214 | None | 0 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 617 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
