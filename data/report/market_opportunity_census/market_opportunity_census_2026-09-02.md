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
| KRX | 102 | 4 | 3.92 | 22.55 | 102 | 0 | pass |
| NXT | 151 | 0 | 0.0 | 0.0 | 151 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=67, `entry_ai_trace_gap`=9, `entry_authority_guard_block`=3, `late_discovery_after_opportunity_window`=9, `post_authority_submit_safety_gap`=9, `scanner_discovery_gap_or_unobserved`=1, `scanner_heavy_eval_gap`=2, `scanner_source_guard_blocked_before_promotion`=2
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=151

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=3, `market_gainer_reserved_full`=24, `reentry_cooldown_no_material_upgrade`=40; count_sum=67; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 169 | 7.1 | 10.65 | 1.18 | 21 | 67.35041 | 0 |
| all | 10 | KRX | forward_exact | 76 | 15.79 | 23.68 | 2.63 | 21 | 67.35041 | 0 |
| all | 10 | NXT | forward_exact | 93 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 169 | 79.88 | 78.7 | 51.48 | 40 | None | 5 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 76 | 77.63 | 77.63 | 69.74 | 38 | None | 3 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 93 | 81.72 | 79.57 | 36.56 | 2 | None | 2 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 169 | 34.91 | 34.91 | 31.36 | 38 | None | 3 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 76 | 77.63 | 77.63 | 69.74 | 38 | None | 3 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 93 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 311 | 7.4 | 8.68 | 1.93 | 30 | 69.122238 | 0 |
| all | 20 | KRX | forward_exact | 136 | 16.91 | 19.85 | 4.41 | 30 | 69.122238 | 0 |
| all | 20 | NXT | forward_exact | 175 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 311 | 73.95 | 68.49 | 36.33 | 51 | None | 7 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 136 | 69.85 | 69.12 | 56.62 | 50 | None | 5 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 175 | 77.14 | 68.0 | 20.57 | 1 | None | 2 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 311 | 30.55 | 30.23 | 24.76 | 50 | None | 5 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 136 | 69.85 | 69.12 | 56.62 | 50 | None | 5 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 175 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 734 | 4.36 | 5.45 | 0.82 | 34 | 105.000465 | 0 |
| all | 50 | KRX | forward_exact | 281 | 11.39 | 14.23 | 2.14 | 34 | 105.000465 | 0 |
| all | 50 | NXT | forward_exact | 453 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 734 | 63.62 | 56.13 | 14.99 | 40 | None | 3 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 281 | 50.89 | 49.11 | 27.05 | 36 | None | 1 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 453 | 71.52 | 60.49 | 7.51 | 4 | None | 2 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 734 | 19.48 | 18.8 | 10.35 | 36 | None | 1 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 281 | 50.89 | 49.11 | 27.05 | 36 | None | 1 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 453 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 156 | 11.54 | 12.82 | 2.56 | 22 | 28.662463 | 0 |
| liquid_common | 10 | KRX | forward_exact | 69 | 26.09 | 28.99 | 5.8 | 22 | 28.662463 | 0 |
| liquid_common | 10 | NXT | forward_exact | 87 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 156 | 87.18 | 86.54 | 57.05 | 44 | None | 4 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 69 | 92.75 | 92.75 | 81.16 | 42 | None | 2 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 87 | 82.76 | 81.61 | 37.93 | 2 | None | 2 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 156 | 41.03 | 41.03 | 35.9 | 42 | None | 2 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 69 | 92.75 | 92.75 | 81.16 | 42 | None | 2 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 87 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 272 | 9.19 | 10.66 | 1.84 | 33 | 141.647843 | 0 |
| liquid_common | 20 | KRX | forward_exact | 121 | 20.66 | 23.97 | 4.13 | 33 | 141.647843 | 0 |
| liquid_common | 20 | NXT | forward_exact | 151 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 272 | 84.93 | 81.25 | 43.75 | 49 | None | 4 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 121 | 85.95 | 84.3 | 68.6 | 48 | None | 2 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 151 | 84.11 | 78.81 | 23.84 | 1 | None | 2 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 272 | 38.24 | 37.5 | 30.51 | 48 | None | 2 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 121 | 85.95 | 84.3 | 68.6 | 48 | None | 2 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 151 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 630 | 6.83 | 6.83 | 0.95 | 26 | 73.165163 | 0 |
| liquid_common | 50 | KRX | forward_exact | 285 | 15.09 | 15.09 | 2.11 | 26 | 73.165163 | 0 |
| liquid_common | 50 | NXT | forward_exact | 345 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 630 | 73.33 | 69.52 | 21.27 | 52 | None | 3 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 285 | 71.58 | 68.42 | 33.68 | 49 | None | 1 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 345 | 74.78 | 70.43 | 11.01 | 3 | None | 2 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 630 | 32.38 | 30.95 | 15.24 | 49 | None | 1 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 285 | 71.58 | 68.42 | 33.68 | 49 | None | 1 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 345 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
