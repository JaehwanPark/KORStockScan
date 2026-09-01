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
| KRX | 128 | 8 | 6.25 | 17.97 | 128 | 0 | pass |
| NXT | 171 | 0 | 0.0 | 0.0 | 171 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=78, `entry_ai_trace_gap`=8, `entry_authority_guard_block`=3, `late_discovery_after_opportunity_window`=14, `post_authority_submit_safety_gap`=12, `scanner_discovery_gap_or_unobserved`=10, `scanner_source_guard_blocked_before_promotion`=3
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=171

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=11, `market_gainer_reserved_full`=27, `reentry_cooldown_no_material_upgrade`=40; count_sum=78; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 160 | 7.5 | 9.38 | 1.88 | 15 | 17.257907 | 0 |
| all | 10 | KRX | forward_exact | 64 | 18.75 | 23.44 | 4.69 | 15 | 17.257907 | 0 |
| all | 10 | NXT | forward_exact | 96 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 160 | 76.25 | 76.25 | 42.5 | 28 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 64 | 67.19 | 67.19 | 54.69 | 21 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 96 | 82.29 | 82.29 | 34.38 | 7 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 160 | 26.88 | 26.88 | 21.88 | 21 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 64 | 67.19 | 67.19 | 54.69 | 21 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 96 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 349 | 2.87 | 6.59 | 0.57 | 26 | 37.445621 | 0 |
| all | 20 | KRX | forward_exact | 164 | 6.1 | 14.02 | 1.22 | 26 | 37.445621 | 0 |
| all | 20 | NXT | forward_exact | 185 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 349 | 69.63 | 67.91 | 31.23 | 51 | None | 1 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 164 | 67.68 | 67.07 | 50.61 | 44 | None | 1 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 185 | 71.35 | 68.65 | 14.05 | 7 | None | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 349 | 31.81 | 31.52 | 23.78 | 44 | None | 1 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 164 | 67.68 | 67.07 | 50.61 | 44 | None | 1 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 185 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 785 | 4.2 | 5.99 | 0.38 | 32 | 46.713611 | 0 |
| all | 50 | KRX | forward_exact | 336 | 9.82 | 13.99 | 0.89 | 32 | 46.713611 | 0 |
| all | 50 | NXT | forward_exact | 449 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 785 | 61.91 | 58.22 | 15.41 | 72 | None | 3 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 336 | 64.88 | 63.1 | 25.3 | 66 | None | 2 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 449 | 59.69 | 54.57 | 8.02 | 6 | None | 1 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 785 | 27.77 | 27.01 | 10.83 | 66 | None | 2 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 336 | 64.88 | 63.1 | 25.3 | 66 | None | 2 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 449 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 144 | 7.64 | 10.42 | 2.08 | 16 | 92.025241 | 0 |
| liquid_common | 10 | KRX | forward_exact | 55 | 20.0 | 27.27 | 5.45 | 16 | 92.025241 | 0 |
| liquid_common | 10 | NXT | forward_exact | 89 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 144 | 88.89 | 88.19 | 48.61 | 38 | None | 1 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 55 | 90.91 | 89.09 | 70.91 | 29 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 89 | 87.64 | 87.64 | 34.83 | 9 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 144 | 34.72 | 34.03 | 27.08 | 29 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 55 | 90.91 | 89.09 | 70.91 | 29 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 89 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 305 | 7.54 | 11.8 | 2.62 | 38 | 24.837823 | 0 |
| liquid_common | 20 | KRX | forward_exact | 134 | 17.16 | 26.87 | 5.97 | 38 | 24.837823 | 0 |
| liquid_common | 20 | NXT | forward_exact | 171 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 305 | 87.54 | 86.56 | 36.39 | 57 | None | 1 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 134 | 93.28 | 92.54 | 64.18 | 51 | None | 1 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 171 | 83.04 | 81.87 | 14.62 | 6 | None | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 305 | 40.98 | 40.66 | 28.2 | 51 | None | 1 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 134 | 93.28 | 92.54 | 64.18 | 51 | None | 1 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 171 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 706 | 6.52 | 6.94 | 0.57 | 29 | 86.193293 | 0 |
| liquid_common | 50 | KRX | forward_exact | 318 | 14.47 | 15.41 | 1.26 | 29 | 86.193293 | 0 |
| liquid_common | 50 | NXT | forward_exact | 388 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 706 | 70.4 | 66.29 | 19.12 | 71 | None | 4 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 318 | 80.5 | 77.36 | 32.39 | 67 | None | 3 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 388 | 62.11 | 57.22 | 8.25 | 4 | None | 1 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 706 | 36.26 | 34.84 | 14.59 | 67 | None | 3 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 318 | 80.5 | 77.36 | 32.39 | 67 | None | 3 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 388 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
