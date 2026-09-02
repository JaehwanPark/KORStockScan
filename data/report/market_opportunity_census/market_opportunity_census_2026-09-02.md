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
| KRX | 22 | 0 | 0.0 | 9.09 | 22 | 0 | pass |
| NXT | 69 | 0 | 0.0 | 0.0 | 69 | 0 | pass |

### Terminal Coverage Reasons

- KRX terminal coverage reasons: `candidate_not_promoted`=15, `entry_ai_trace_gap`=1, `late_discovery_after_opportunity_window`=1, `scanner_discovery_gap_or_unobserved`=2, `scanner_heavy_eval_gap`=1, `scanner_source_guard_blocked_before_promotion`=2
- NXT terminal coverage reasons: `scanner_discovery_gap_or_unobserved`=69

### Candidate Not Promoted First Reasons

- KRX: `general_slot_limit`=1, `market_gainer_reserved_full`=10, `reentry_cooldown_no_material_upgrade`=4; count_sum=15; conservation_delta=0; conservation_status=`pass`
- NXT: none; count_sum=0; conservation_delta=0; conservation_status=`pass`

## Coverage

| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | 10 | ALL | forward_exact | 63 | 4.76 | 3.17 | 0.0 | 5 | None | 0 |
| all | 10 | KRX | forward_exact | 21 | 14.29 | 9.52 | 0.0 | 5 | None | 0 |
| all | 10 | NXT | forward_exact | 42 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 10 | ALL | same_day_any_venue_retrospective_noncausal | 63 | 61.9 | 55.56 | 26.98 | 8 | None | 3 |
| all | 10 | KRX | same_day_any_venue_retrospective_noncausal | 21 | 47.62 | 38.1 | 14.29 | 8 | None | 1 |
| all | 10 | NXT | same_day_any_venue_retrospective_noncausal | 42 | 69.05 | 64.29 | 33.33 | 0 | None | 2 |
| all | 10 | ALL | same_day_venue_consistent_retrospective | 63 | 15.87 | 12.7 | 4.76 | 8 | None | 1 |
| all | 10 | KRX | same_day_venue_consistent_retrospective | 21 | 47.62 | 38.1 | 14.29 | 8 | None | 1 |
| all | 10 | NXT | same_day_venue_consistent_retrospective | 42 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | forward_exact | 127 | 2.36 | 0.79 | 0.0 | 5 | None | 0 |
| all | 20 | KRX | forward_exact | 36 | 8.33 | 2.78 | 0.0 | 5 | None | 0 |
| all | 20 | NXT | forward_exact | 91 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 20 | ALL | same_day_any_venue_retrospective_noncausal | 127 | 50.39 | 41.73 | 14.17 | 11 | None | 3 |
| all | 20 | KRX | same_day_any_venue_retrospective_noncausal | 36 | 36.11 | 27.78 | 11.11 | 11 | None | 1 |
| all | 20 | NXT | same_day_any_venue_retrospective_noncausal | 91 | 56.04 | 47.25 | 15.38 | 0 | None | 2 |
| all | 20 | ALL | same_day_venue_consistent_retrospective | 127 | 10.24 | 7.87 | 3.15 | 11 | None | 1 |
| all | 20 | KRX | same_day_venue_consistent_retrospective | 36 | 36.11 | 27.78 | 11.11 | 11 | None | 1 |
| all | 20 | NXT | same_day_venue_consistent_retrospective | 91 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | forward_exact | 258 | 1.55 | 0.39 | 0.0 | 6 | None | 0 |
| all | 50 | KRX | forward_exact | 85 | 4.71 | 1.18 | 0.0 | 6 | None | 0 |
| all | 50 | NXT | forward_exact | 173 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| all | 50 | ALL | same_day_any_venue_retrospective_noncausal | 258 | 43.02 | 33.33 | 6.98 | 10 | None | 3 |
| all | 50 | KRX | same_day_any_venue_retrospective_noncausal | 85 | 22.35 | 15.29 | 3.53 | 10 | None | 1 |
| all | 50 | NXT | same_day_any_venue_retrospective_noncausal | 173 | 53.18 | 42.2 | 8.67 | 0 | None | 2 |
| all | 50 | ALL | same_day_venue_consistent_retrospective | 258 | 7.36 | 5.04 | 1.16 | 10 | None | 1 |
| all | 50 | KRX | same_day_venue_consistent_retrospective | 85 | 22.35 | 15.29 | 3.53 | 10 | None | 1 |
| all | 50 | NXT | same_day_venue_consistent_retrospective | 173 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | forward_exact | 53 | 5.66 | 3.77 | 0.0 | 4 | None | 0 |
| liquid_common | 10 | KRX | forward_exact | 17 | 17.65 | 11.76 | 0.0 | 4 | None | 0 |
| liquid_common | 10 | NXT | forward_exact | 36 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 10 | ALL | same_day_any_venue_retrospective_noncausal | 53 | 73.58 | 66.04 | 32.08 | 10 | None | 3 |
| liquid_common | 10 | KRX | same_day_any_venue_retrospective_noncausal | 17 | 70.59 | 58.82 | 23.53 | 10 | None | 1 |
| liquid_common | 10 | NXT | same_day_any_venue_retrospective_noncausal | 36 | 75.0 | 69.44 | 36.11 | 0 | None | 2 |
| liquid_common | 10 | ALL | same_day_venue_consistent_retrospective | 53 | 22.64 | 18.87 | 7.55 | 10 | None | 1 |
| liquid_common | 10 | KRX | same_day_venue_consistent_retrospective | 17 | 70.59 | 58.82 | 23.53 | 10 | None | 1 |
| liquid_common | 10 | NXT | same_day_venue_consistent_retrospective | 36 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | forward_exact | 100 | 3.0 | 1.0 | 0.0 | 4 | None | 0 |
| liquid_common | 20 | KRX | forward_exact | 31 | 9.68 | 3.23 | 0.0 | 4 | None | 0 |
| liquid_common | 20 | NXT | forward_exact | 69 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 20 | ALL | same_day_any_venue_retrospective_noncausal | 100 | 64.0 | 56.0 | 18.0 | 10 | None | 3 |
| liquid_common | 20 | KRX | same_day_any_venue_retrospective_noncausal | 31 | 45.16 | 32.26 | 9.68 | 10 | None | 1 |
| liquid_common | 20 | NXT | same_day_any_venue_retrospective_noncausal | 69 | 72.46 | 66.67 | 21.74 | 0 | None | 2 |
| liquid_common | 20 | ALL | same_day_venue_consistent_retrospective | 100 | 14.0 | 10.0 | 3.0 | 10 | None | 1 |
| liquid_common | 20 | KRX | same_day_venue_consistent_retrospective | 31 | 45.16 | 32.26 | 9.68 | 10 | None | 1 |
| liquid_common | 20 | NXT | same_day_venue_consistent_retrospective | 69 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | forward_exact | 161 | 4.35 | 2.48 | 0.62 | 6 | 73.165163 | 0 |
| liquid_common | 50 | KRX | forward_exact | 72 | 9.72 | 5.56 | 1.39 | 6 | 73.165163 | 0 |
| liquid_common | 50 | NXT | forward_exact | 89 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |
| liquid_common | 50 | ALL | same_day_any_venue_retrospective_noncausal | 161 | 58.39 | 47.2 | 13.04 | 12 | None | 3 |
| liquid_common | 50 | KRX | same_day_any_venue_retrospective_noncausal | 72 | 45.83 | 29.17 | 8.33 | 12 | None | 1 |
| liquid_common | 50 | NXT | same_day_any_venue_retrospective_noncausal | 89 | 68.54 | 61.8 | 16.85 | 0 | None | 2 |
| liquid_common | 50 | ALL | same_day_venue_consistent_retrospective | 161 | 20.5 | 13.04 | 3.73 | 12 | None | 1 |
| liquid_common | 50 | KRX | same_day_venue_consistent_retrospective | 72 | 45.83 | 29.17 | 8.33 | 12 | None | 1 |
| liquid_common | 50 | NXT | same_day_venue_consistent_retrospective | 89 | 0.0 | 0.0 | 0.0 | 0 | None | 0 |

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
