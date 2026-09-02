# Market Opportunity Census - 2026-09-02

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `ex_post_executable_opportunity_label_not_available`

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 104 | 4 | 3.85 | 22.12 | 104 | 0 | pass |
| NXT | 201 | 0 | 0.0 | 1.99 | 201 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=67, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=3, `late_discovery_after_opportunity_window`=9, `post_authority_submit_safety_gap`=9, `scanner_discovery_gap_or_unobserved`=3, `scanner_heavy_eval_gap`=2, `scanner_source_guard_blocked_before_promotion`=2
- NXT terminal coverage reasons: `candidate_not_promoted`=17, `entry_ai_trace_gap`=3, `entry_authority_guard_block`=1, `late_discovery_after_opportunity_window`=2, `scanner_discovery_gap_or_unobserved`=177, `scanner_source_guard_blocked_before_promotion`=1

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=3, `market_gainer_reserved_full`=24, `reentry_cooldown_no_material_upgrade`=40; count_sum=67; conservation_delta=0; conservation_status=`pass`
- NXT: `market_gainer_reserved_full`=5, `reentry_cooldown_no_material_upgrade`=12; count_sum=17; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 202 | 7.43 | 11.39 | 0.99 | 26 | 67.35041 | 0 |
| all | 10 | KRX | forward_exact | 77 | 15.58 | 23.38 | 2.6 | 21 | 67.35041 | 0 |
| all | 10 | NXT | forward_exact | 125 | 2.4 | 4.0 | 0.0 | 5 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 202 | 86.14 | 83.17 | 62.38 | 43 | None | 6 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 77 | 80.52 | 77.92 | 68.83 | 39 | None | 3 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 125 | 89.6 | 86.4 | 58.4 | 4 | None | 3 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 202 | 75.74 | 74.75 | 55.45 | 108 | None | 3 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 77 | 77.92 | 77.92 | 68.83 | 39 | None | 3 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 125 | 74.4 | 72.8 | 47.2 | 69 | None | 0 |
| all | 20 | ALL | forward_exact | 370 | 7.57 | 9.19 | 1.62 | 36 | 69.122238 | 0 |
| all | 20 | KRX | forward_exact | 138 | 16.67 | 19.57 | 4.35 | 30 | 69.122238 | 0 |
| all | 20 | NXT | forward_exact | 232 | 2.16 | 3.02 | 0.0 | 6 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 370 | 81.08 | 75.14 | 43.78 | 54 | None | 8 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 138 | 71.01 | 69.57 | 57.25 | 51 | None | 5 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 232 | 87.07 | 78.45 | 35.78 | 3 | None | 3 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 370 | 66.49 | 60.54 | 38.92 | 120 | None | 5 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 138 | 70.29 | 69.57 | 57.25 | 51 | None | 5 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 232 | 64.22 | 55.17 | 28.02 | 69 | None | 0 |
| all | 50 | ALL | forward_exact | 864 | 5.56 | 6.25 | 0.69 | 37 | 105.000465 | 0 |
| all | 50 | KRX | forward_exact | 285 | 11.23 | 14.04 | 2.11 | 34 | 105.000465 | 0 |
| all | 50 | NXT | forward_exact | 579 | 2.76 | 2.42 | 0.0 | 3 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 864 | 74.31 | 65.51 | 19.68 | 45 | None | 4 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 285 | 52.63 | 50.18 | 29.12 | 39 | None | 1 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 579 | 84.97 | 73.06 | 15.03 | 6 | None | 3 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 864 | 51.97 | 45.25 | 17.01 | 98 | None | 1 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 285 | 50.88 | 49.12 | 26.67 | 37 | None | 1 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 579 | 52.5 | 43.35 | 12.26 | 61 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 188 | 11.17 | 13.3 | 2.13 | 27 | 28.662463 | 0 |
| liquid_common | 10 | KRX | forward_exact | 69 | 26.09 | 28.99 | 5.8 | 22 | 28.662463 | 0 |
| liquid_common | 10 | NXT | forward_exact | 119 | 2.52 | 4.2 | 0.0 | 5 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 188 | 91.49 | 89.89 | 68.09 | 46 | None | 5 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 69 | 92.75 | 92.75 | 81.16 | 42 | None | 2 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 119 | 90.76 | 88.24 | 60.5 | 4 | None | 3 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 188 | 81.91 | 80.85 | 61.17 | 111 | None | 2 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 69 | 92.75 | 92.75 | 81.16 | 42 | None | 2 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 119 | 75.63 | 73.95 | 49.58 | 69 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 324 | 8.95 | 10.8 | 1.54 | 39 | 141.647843 | 0 |
| liquid_common | 20 | KRX | forward_exact | 123 | 20.33 | 23.58 | 4.07 | 33 | 141.647843 | 0 |
| liquid_common | 20 | NXT | forward_exact | 201 | 1.99 | 2.99 | 0.0 | 6 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 324 | 88.89 | 85.49 | 50.31 | 53 | None | 5 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 123 | 86.18 | 84.55 | 69.11 | 50 | None | 2 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 201 | 90.55 | 86.07 | 38.81 | 3 | None | 3 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 324 | 72.84 | 71.3 | 45.37 | 111 | None | 2 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 123 | 86.18 | 84.55 | 69.11 | 50 | None | 2 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 201 | 64.68 | 63.18 | 30.85 | 61 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 729 | 8.5 | 7.96 | 0.82 | 30 | 73.165163 | 0 |
| liquid_common | 50 | KRX | forward_exact | 287 | 14.98 | 14.98 | 2.09 | 27 | 73.165163 | 0 |
| liquid_common | 50 | NXT | forward_exact | 442 | 4.3 | 3.39 | 0.0 | 3 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 729 | 79.7 | 74.49 | 25.79 | 59 | None | 4 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 287 | 73.87 | 70.38 | 37.63 | 54 | None | 1 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 442 | 83.48 | 77.15 | 18.1 | 5 | None | 3 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 729 | 55.28 | 51.17 | 21.54 | 99 | None | 1 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 287 | 71.78 | 68.64 | 33.45 | 50 | None | 1 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 442 | 44.57 | 39.82 | 13.8 | 49 | None | 0 |

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
