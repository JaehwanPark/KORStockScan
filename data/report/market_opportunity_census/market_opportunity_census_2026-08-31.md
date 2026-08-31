# Market Opportunity Census - 2026-08-31

- status: `early_evidence_hold_sample`
- scanner_recall_state: `insufficient_evidence_scanner_recall`
- decision_authority: `source_only_scanner_coverage_audit`
- runtime_effect: `false`
- actual_order_submitted: `false`
- warning: forward_exact requires intraday captures; retrospective coverage is noncausal and cannot authorize BUY.
- instrumentation_blockers: `official_symbol_master_lookup_gap`, `capture_cadence_floor_not_met`, `capture_session_provenance_missing`, `capture_source_hash_missing`, `ex_post_executable_opportunity_label_not_available`

## Primary Decision Metric

- scope: `liquid_common/top_20/forward_exact`; official-master eligible; venue-separated
- metric: `entry_ai_provider_reach_rate_pct`

| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |
|---|---:|---:|---:|---:|---:|---:|---|
| KRX | 19 | 2 | 10.53 | 10.53 | 19 | 0 | pass |
| NXT | 59 | 2 | 3.39 | 8.47 | 59 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `late_discovery_after_opportunity_window`=1, `post_authority_submit_safety_gap`=2, `scanner_discovery_gap_or_unobserved`=15, `scanner_source_guard_blocked_before_promotion`=1
- NXT terminal coverage reasons: `candidate_not_promoted`=28, `entry_ai_trace_gap`=2, `late_discovery_after_opportunity_window`=4, `post_authority_submit_safety_gap`=3, `scanner_discovery_gap_or_unobserved`=22

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 41 | 12.2 | 17.07 | 4.88 | 7 | 7.118598 | 0 |
| all | 10 | KRX | forward_exact | 10 | 0.0 | 0.0 | 0.0 | 1 | None | 0 |
| all | 10 | NXT | forward_exact | 31 | 16.13 | 22.58 | 6.45 | 6 | 7.118598 | 0 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 41 | 95.12 | 92.68 | 73.17 | 27 | None | 1 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 10 | 80.0 | 70.0 | 50.0 | 4 | None | 1 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 31 | 100.0 | 100.0 | 80.65 | 23 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 41 | 95.12 | 92.68 | 78.05 | 4 | None | 5 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 10 | 80.0 | 70.0 | 50.0 | 4 | None | 1 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 31 | 100.0 | 100.0 | 87.1 | 0 | None | 4 |
| all | 20 | ALL | forward_exact | 81 | 9.88 | 16.05 | 4.94 | 13 | 30.415307 | 0 |
| all | 20 | KRX | forward_exact | 20 | 10.0 | 10.0 | 10.0 | 3 | 13.399536 | 0 |
| all | 20 | NXT | forward_exact | 61 | 9.84 | 18.03 | 3.28 | 10 | 37.55504 | 0 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 81 | 93.83 | 87.65 | 67.9 | 58 | None | 1 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 20 | 75.0 | 70.0 | 55.0 | 6 | None | 1 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 61 | 100.0 | 93.44 | 72.13 | 52 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 81 | 93.83 | 92.59 | 76.54 | 6 | None | 5 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 20 | 75.0 | 70.0 | 55.0 | 6 | None | 1 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 61 | 100.0 | 100.0 | 83.61 | 0 | None | 4 |
| all | 50 | ALL | forward_exact | 204 | 6.86 | 8.82 | 1.96 | 12 | 30.415307 | 0 |
| all | 50 | KRX | forward_exact | 50 | 8.0 | 10.0 | 4.0 | 6 | 13.399536 | 0 |
| all | 50 | NXT | forward_exact | 154 | 6.49 | 8.44 | 1.3 | 6 | 37.55504 | 0 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 204 | 90.2 | 83.33 | 29.41 | 54 | None | 1 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 50 | 72.0 | 70.0 | 52.0 | 14 | None | 1 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 154 | 96.1 | 87.66 | 22.08 | 40 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 204 | 90.69 | 87.75 | 38.73 | 14 | None | 5 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 50 | 72.0 | 70.0 | 52.0 | 14 | None | 1 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 154 | 96.75 | 93.51 | 34.42 | 0 | None | 4 |
| liquid_common | 10 | ALL | forward_exact | 39 | 12.82 | 17.95 | 7.69 | 8 | 13.399536 | 0 |
| liquid_common | 10 | KRX | forward_exact | 10 | 10.0 | 10.0 | 10.0 | 2 | 13.399536 | 0 |
| liquid_common | 10 | NXT | forward_exact | 29 | 13.79 | 20.69 | 6.9 | 6 | 7.118598 | 0 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 39 | 97.44 | 94.87 | 82.05 | 26 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 10 | 90.0 | 80.0 | 70.0 | 4 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 29 | 100.0 | 100.0 | 86.21 | 22 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 39 | 97.44 | 94.87 | 87.18 | 4 | None | 5 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 10 | 90.0 | 80.0 | 70.0 | 4 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 29 | 100.0 | 100.0 | 93.1 | 0 | None | 4 |
| liquid_common | 20 | ALL | forward_exact | 79 | 8.86 | 13.92 | 5.06 | 12 | 30.415307 | 0 |
| liquid_common | 20 | KRX | forward_exact | 20 | 10.0 | 10.0 | 10.0 | 3 | 13.399536 | 0 |
| liquid_common | 20 | NXT | forward_exact | 59 | 8.47 | 15.25 | 3.39 | 9 | 37.55504 | 0 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 79 | 98.73 | 92.41 | 75.95 | 61 | None | 1 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 20 | 95.0 | 90.0 | 80.0 | 10 | None | 1 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 59 | 100.0 | 93.22 | 74.58 | 51 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 79 | 98.73 | 97.47 | 83.54 | 10 | None | 5 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 20 | 95.0 | 90.0 | 80.0 | 10 | None | 1 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 59 | 100.0 | 100.0 | 84.75 | 0 | None | 4 |
| liquid_common | 50 | ALL | forward_exact | 205 | 6.34 | 8.29 | 1.95 | 12 | 30.415307 | 0 |
| liquid_common | 50 | KRX | forward_exact | 50 | 8.0 | 10.0 | 4.0 | 6 | 13.399536 | 0 |
| liquid_common | 50 | NXT | forward_exact | 155 | 5.81 | 7.74 | 1.29 | 6 | 37.55504 | 0 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 205 | 94.63 | 86.83 | 32.68 | 55 | None | 2 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 50 | 86.0 | 84.0 | 66.0 | 15 | None | 2 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 155 | 97.42 | 87.74 | 21.94 | 40 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 205 | 95.12 | 92.2 | 41.46 | 15 | None | 6 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 50 | 86.0 | 84.0 | 66.0 | 15 | None | 2 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 155 | 98.06 | 94.84 | 33.55 | 0 | None | 4 |

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
