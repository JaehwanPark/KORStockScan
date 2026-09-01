# Market Opportunity Census - 2026-09-01

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
| KRX | 102 | 6 | 5.88 | 19.61 | 102 | 0 | pass |
| NXT | 158 | 0 | 0.0 | 0.0 | 158 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=64, `entry_ai_trace_gap`=8, `entry_authority_guard_block`=2, `late_discovery_after_opportunity_window`=12, `post_authority_submit_safety_gap`=10, `scanner_discovery_gap_or_unobserved`=3, `scanner_source_guard_blocked_before_promotion`=3
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=158

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=5, `market_gainer_reserved_full`=21, `reentry_cooldown_no_material_upgrade`=38; count_sum=64; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 137 | 8.03 | 10.22 | 2.19 | 14 | 17.257907 | 0 |
| all | 10 | KRX | forward_exact | 54 | 20.37 | 25.93 | 5.56 | 14 | 17.257907 | 0 |
| all | 10 | NXT | forward_exact | 83 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 137 | 78.1 | 78.1 | 43.07 | 23 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 54 | 66.67 | 66.67 | 50.0 | 18 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 83 | 85.54 | 85.54 | 38.55 | 5 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 137 | 26.28 | 26.28 | 19.71 | 18 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 54 | 66.67 | 66.67 | 50.0 | 18 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 83 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 315 | 3.17 | 7.3 | 0.63 | 26 | 37.445621 | 0 |
| all | 20 | KRX | forward_exact | 144 | 6.94 | 15.97 | 1.39 | 26 | 37.445621 | 0 |
| all | 20 | NXT | forward_exact | 171 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 315 | 70.16 | 68.25 | 31.11 | 49 | None | 1 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 144 | 68.75 | 68.06 | 50.0 | 42 | None | 1 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 171 | 71.35 | 68.42 | 15.2 | 7 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 315 | 31.43 | 31.11 | 22.86 | 42 | None | 1 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 144 | 68.75 | 68.06 | 50.0 | 42 | None | 1 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 171 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 704 | 4.26 | 6.11 | 0.43 | 30 | 46.713611 | 0 |
| all | 50 | KRX | forward_exact | 294 | 10.2 | 14.63 | 1.02 | 30 | 46.713611 | 0 |
| all | 50 | NXT | forward_exact | 410 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 704 | 60.65 | 56.68 | 15.48 | 66 | None | 3 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 294 | 63.61 | 61.56 | 25.17 | 60 | None | 2 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 410 | 58.54 | 53.17 | 8.54 | 6 | None | 1 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 704 | 26.56 | 25.71 | 10.51 | 60 | None | 2 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 294 | 63.61 | 61.56 | 25.17 | 60 | None | 2 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 410 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 123 | 8.13 | 10.57 | 2.44 | 14 | 92.025241 | 0 |
| liquid_common | 10 | KRX | forward_exact | 47 | 21.28 | 27.66 | 6.38 | 14 | 92.025241 | 0 |
| liquid_common | 10 | NXT | forward_exact | 76 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 123 | 90.24 | 89.43 | 49.59 | 30 | None | 1 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 47 | 91.49 | 89.36 | 65.96 | 25 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 76 | 89.47 | 89.47 | 39.47 | 5 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 123 | 34.96 | 34.15 | 25.2 | 25 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 47 | 91.49 | 89.36 | 65.96 | 25 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 76 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 265 | 7.55 | 11.7 | 2.26 | 33 | 70.611694 | 0 |
| liquid_common | 20 | KRX | forward_exact | 107 | 18.69 | 28.97 | 5.61 | 33 | 70.611694 | 0 |
| liquid_common | 20 | NXT | forward_exact | 158 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 265 | 87.92 | 86.79 | 35.47 | 49 | None | 1 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 107 | 93.46 | 92.52 | 64.49 | 43 | None | 1 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 158 | 84.18 | 82.91 | 15.82 | 6 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 265 | 37.74 | 37.36 | 26.04 | 43 | None | 1 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 107 | 93.46 | 92.52 | 64.49 | 43 | None | 1 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 158 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 611 | 6.71 | 7.36 | 0.65 | 28 | 86.193293 | 0 |
| liquid_common | 50 | KRX | forward_exact | 267 | 15.36 | 16.85 | 1.5 | 28 | 86.193293 | 0 |
| liquid_common | 50 | NXT | forward_exact | 344 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 611 | 70.05 | 66.28 | 17.35 | 66 | None | 3 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 267 | 80.52 | 77.9 | 28.46 | 62 | None | 2 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 344 | 61.92 | 57.27 | 8.72 | 4 | None | 1 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 611 | 35.19 | 34.04 | 12.44 | 62 | None | 2 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 267 | 80.52 | 77.9 | 28.46 | 62 | None | 2 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 344 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
