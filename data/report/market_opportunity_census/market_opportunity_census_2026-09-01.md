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
| KRX | 129 | 8 | 6.2 | 17.83 | 129 | 0 | pass |
| NXT | 231 | 1 | 0.43 | 4.33 | 231 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=80, `entry_ai_trace_gap`=8, `entry_authority_guard_block`=3, `late_discovery_after_opportunity_window`=15, `post_authority_submit_safety_gap`=12, `scanner_discovery_gap_or_unobserved`=8, `scanner_source_guard_blocked_before_promotion`=3
- NXT terminal coverage reasons: `candidate_not_promoted`=22, `entry_ai_trace_gap`=5, `entry_authority_guard_block`=1, `late_discovery_after_opportunity_window`=2, `post_authority_submit_safety_gap`=1, `scanner_discovery_gap_or_unobserved`=197, `scanner_fast_precheck_gap`=3

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=11, `market_gainer_reserved_full`=27, `reentry_cooldown_no_material_upgrade`=42; count_sum=80; conservation_delta=0; conservation_status=`pass`
- NXT: `market_gainer_reserved_full`=5, `reentry_cooldown_no_material_upgrade`=17; count_sum=22; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 189 | 6.88 | 8.47 | 1.59 | 16 | 17.257907 | 0 |
| all | 10 | KRX | forward_exact | 65 | 18.46 | 23.08 | 4.62 | 15 | 17.257907 | 0 |
| all | 10 | NXT | forward_exact | 124 | 0.81 | 0.81 | 0.0 | 1 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 189 | 87.83 | 87.83 | 61.38 | 44 | None | 0 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 65 | 69.23 | 69.23 | 55.38 | 21 | None | 0 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 124 | 97.58 | 97.58 | 64.52 | 23 | None | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 189 | 85.19 | 85.19 | 55.03 | 110 | None | 0 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 65 | 67.69 | 67.69 | 55.38 | 21 | None | 0 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 124 | 94.35 | 94.35 | 54.84 | 89 | None | 0 |
| all | 20 | ALL | forward_exact | 413 | 3.63 | 7.02 | 0.48 | 33 | 37.445621 | 0 |
| all | 20 | KRX | forward_exact | 166 | 6.02 | 13.86 | 1.2 | 26 | 37.445621 | 0 |
| all | 20 | NXT | forward_exact | 247 | 2.02 | 2.43 | 0.0 | 7 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 413 | 83.29 | 82.57 | 46.0 | 69 | None | 7 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 166 | 68.07 | 67.47 | 50.6 | 44 | None | 1 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 247 | 93.52 | 92.71 | 42.91 | 25 | None | 6 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 413 | 77.97 | 77.48 | 43.83 | 150 | None | 7 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 166 | 67.47 | 66.87 | 50.6 | 44 | None | 1 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 247 | 85.02 | 84.62 | 39.27 | 106 | None | 6 |
| all | 50 | ALL | forward_exact | 934 | 4.82 | 6.0 | 0.32 | 34 | 46.713611 | 0 |
| all | 50 | KRX | forward_exact | 339 | 10.03 | 14.16 | 0.88 | 34 | 46.713611 | 0 |
| all | 50 | NXT | forward_exact | 595 | 1.85 | 1.34 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 934 | 79.01 | 74.52 | 20.02 | 93 | None | 11 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 339 | 67.26 | 64.9 | 28.32 | 71 | None | 3 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 595 | 85.71 | 80.0 | 15.29 | 22 | None | 8 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 934 | 71.63 | 67.45 | 16.6 | 144 | None | 10 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 339 | 64.9 | 63.13 | 25.66 | 66 | None | 3 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 595 | 75.46 | 69.92 | 11.43 | 78 | None | 7 |
| liquid_common | 10 | ALL | forward_exact | 171 | 7.6 | 9.36 | 1.75 | 18 | 92.025241 | 0 |
| liquid_common | 10 | KRX | forward_exact | 56 | 19.64 | 26.79 | 5.36 | 16 | 92.025241 | 0 |
| liquid_common | 10 | NXT | forward_exact | 115 | 1.74 | 0.87 | 0.0 | 2 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 171 | 96.49 | 95.91 | 71.35 | 52 | None | 1 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 56 | 91.07 | 89.29 | 71.43 | 29 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 115 | 99.13 | 99.13 | 71.3 | 23 | None | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 171 | 94.15 | 93.57 | 64.91 | 121 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 56 | 91.07 | 89.29 | 71.43 | 29 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 115 | 95.65 | 95.65 | 61.74 | 92 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 366 | 9.02 | 12.57 | 2.46 | 48 | 33.833266 | 0 |
| liquid_common | 20 | KRX | forward_exact | 135 | 17.04 | 27.41 | 5.93 | 39 | 24.837823 | 0 |
| liquid_common | 20 | NXT | forward_exact | 231 | 4.33 | 3.9 | 0.43 | 9 | 33.833266 | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 366 | 95.9 | 95.36 | 50.55 | 81 | None | 7 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 135 | 93.33 | 92.59 | 64.44 | 52 | None | 1 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 231 | 97.4 | 96.97 | 42.42 | 29 | None | 6 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 366 | 88.52 | 88.25 | 47.81 | 153 | None | 7 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 135 | 93.33 | 92.59 | 63.7 | 52 | None | 1 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 231 | 85.71 | 85.71 | 38.53 | 101 | None | 6 |
| liquid_common | 50 | ALL | forward_exact | 849 | 5.89 | 6.48 | 0.47 | 30 | 86.193293 | 0 |
| liquid_common | 50 | KRX | forward_exact | 322 | 14.29 | 15.53 | 1.24 | 30 | 86.193293 | 0 |
| liquid_common | 50 | NXT | forward_exact | 527 | 0.76 | 0.95 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 849 | 85.63 | 83.04 | 23.2 | 92 | None | 13 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 322 | 84.16 | 80.75 | 35.09 | 73 | None | 4 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 527 | 86.53 | 84.44 | 15.94 | 19 | None | 9 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 849 | 78.8 | 76.8 | 19.91 | 132 | None | 12 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 322 | 80.43 | 77.33 | 32.3 | 67 | None | 4 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 527 | 77.8 | 76.47 | 12.33 | 65 | None | 8 |

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
