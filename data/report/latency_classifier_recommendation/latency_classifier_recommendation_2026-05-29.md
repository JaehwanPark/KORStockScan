# Latency Classifier Recommendation 2026-05-29

- latency_block_count: 16003
- unique_codes: 55
- selected_profile_id: grid_age167_jitter210_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age167_jitter210_spread0050 | reject | 167 | 210 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0075 | reject | 167 | 210 | 0.0075 | 0 | 373 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0077 | reject | 167 | 210 | 0.0077 | 0 | 586 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0081 | reject | 167 | 210 | 0.0081 | 0 | 1074 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0085 | reject | 167 | 210 | 0.0085 | 0 | 1118 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0093 | reject | 167 | 210 | 0.0093 | 0 | 1782 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0094 | reject | 167 | 210 | 0.0094 | 0 | 2042 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0100 | reject | 167 | 210 | 0.0100 | 0 | 2096 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0107 | reject | 167 | 210 | 0.0107 | 0 | 2122 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter210_spread0120 | reject | 167 | 210 | 0.0120 | 0 | 2207 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0050 | reject | 167 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0075 | reject | 167 | 300 | 0.0075 | 0 | 381 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0077 | reject | 167 | 300 | 0.0077 | 0 | 596 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0081 | reject | 167 | 300 | 0.0081 | 0 | 1092 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0085 | reject | 167 | 300 | 0.0085 | 0 | 1136 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0093 | reject | 167 | 300 | 0.0093 | 0 | 1831 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0094 | reject | 167 | 300 | 0.0094 | 0 | 2091 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0100 | reject | 167 | 300 | 0.0100 | 0 | 2145 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0107 | reject | 167 | 300 | 0.0107 | 0 | 2175 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter300_spread0120 | reject | 167 | 300 | 0.0120 | 0 | 2261 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0050 | reject | 167 | 410 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0075 | reject | 167 | 410 | 0.0075 | 0 | 387 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0077 | reject | 167 | 410 | 0.0077 | 0 | 606 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0081 | reject | 167 | 410 | 0.0081 | 0 | 1113 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0085 | reject | 167 | 410 | 0.0085 | 0 | 1157 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0093 | reject | 167 | 410 | 0.0093 | 0 | 1925 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0094 | reject | 167 | 410 | 0.0094 | 0 | 2191 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0100 | reject | 167 | 410 | 0.0100 | 0 | 2246 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0107 | reject | 167 | 410 | 0.0107 | 0 | 2277 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age167_jitter410_spread0120 | reject | 167 | 410 | 0.0120 | 0 | 2365 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 167, "max_ws_jitter_ms_for_caution": 210, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 167, "recovery_max_ws_jitter_ms": 210, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
