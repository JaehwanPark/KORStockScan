# Latency Classifier Recommendation 2026-08-26

- latency_block_count: 501
- unique_codes: 96
- selected_profile_id: grid_age113_jitter118_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age113_jitter118_spread0050 | reject | 113 | 118 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0070 | reject | 113 | 118 | 0.0070 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0075 | reject | 113 | 118 | 0.0075 | 0 | 50 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0085 | reject | 113 | 118 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0085 | reject | 113 | 118 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0095 | reject | 113 | 118 | 0.0095 | 0 | 99 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0100 | reject | 113 | 118 | 0.0100 | 0 | 100 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0118 | reject | 113 | 118 | 0.0118 | 0 | 112 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter118_spread0120 | reject | 113 | 118 | 0.0120 | 0 | 117 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0050 | reject | 113 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0070 | reject | 113 | 300 | 0.0070 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0075 | reject | 113 | 300 | 0.0075 | 0 | 50 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0085 | reject | 113 | 300 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0085 | reject | 113 | 300 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0095 | reject | 113 | 300 | 0.0095 | 0 | 99 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0100 | reject | 113 | 300 | 0.0100 | 0 | 100 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0118 | reject | 113 | 300 | 0.0118 | 0 | 112 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter300_spread0120 | reject | 113 | 300 | 0.0120 | 0 | 117 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0050 | reject | 113 | 382 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0070 | reject | 113 | 382 | 0.0070 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0075 | reject | 113 | 382 | 0.0075 | 0 | 50 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0085 | reject | 113 | 382 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0085 | reject | 113 | 382 | 0.0085 | 0 | 70 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0095 | reject | 113 | 382 | 0.0095 | 0 | 99 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0100 | reject | 113 | 382 | 0.0100 | 0 | 100 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0118 | reject | 113 | 382 | 0.0118 | 0 | 112 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter382_spread0120 | reject | 113 | 382 | 0.0120 | 0 | 117 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter398_spread0050 | reject | 113 | 398 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter398_spread0070 | reject | 113 | 398 | 0.0070 | 0 | 40 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age113_jitter398_spread0075 | reject | 113 | 398 | 0.0075 | 0 | 50 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 113, "max_ws_jitter_ms_for_caution": 118, "max_spread_ratio_for_caution": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
