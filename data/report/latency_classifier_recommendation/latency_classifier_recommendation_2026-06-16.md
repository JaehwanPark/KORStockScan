# Latency Classifier Recommendation 2026-06-16

- latency_block_count: 20986
- unique_codes: 69
- selected_profile_id: grid_age139_jitter196_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 810, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age139_jitter196_spread0050 | reject | 139 | 196 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0073 | reject | 139 | 196 | 0.0073 | 0 | 582 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0075 | reject | 139 | 196 | 0.0075 | 0 | 609 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0085 | reject | 139 | 196 | 0.0085 | 0 | 670 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0094 | reject | 139 | 196 | 0.0094 | 0 | 1164 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0100 | reject | 139 | 196 | 0.0100 | 0 | 1237 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0109 | reject | 139 | 196 | 0.0109 | 0 | 1763 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0115 | reject | 139 | 196 | 0.0115 | 0 | 2018 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter196_spread0120 | reject | 139 | 196 | 0.0120 | 0 | 2029 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0050 | reject | 139 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0073 | reject | 139 | 300 | 0.0073 | 0 | 583 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0075 | reject | 139 | 300 | 0.0075 | 0 | 610 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0085 | reject | 139 | 300 | 0.0085 | 0 | 671 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0094 | reject | 139 | 300 | 0.0094 | 0 | 1167 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0100 | reject | 139 | 300 | 0.0100 | 0 | 1240 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0109 | reject | 139 | 300 | 0.0109 | 0 | 1768 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0115 | reject | 139 | 300 | 0.0115 | 0 | 2033 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter300_spread0120 | reject | 139 | 300 | 0.0120 | 0 | 2044 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0050 | reject | 139 | 325 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0073 | reject | 139 | 325 | 0.0073 | 0 | 583 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0075 | reject | 139 | 325 | 0.0075 | 0 | 611 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0085 | reject | 139 | 325 | 0.0085 | 0 | 672 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0094 | reject | 139 | 325 | 0.0094 | 0 | 1168 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0100 | reject | 139 | 325 | 0.0100 | 0 | 1241 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0109 | reject | 139 | 325 | 0.0109 | 0 | 1772 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0115 | reject | 139 | 325 | 0.0115 | 0 | 2038 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter325_spread0120 | reject | 139 | 325 | 0.0120 | 0 | 2049 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter450_spread0050 | reject | 139 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter450_spread0073 | reject | 139 | 450 | 0.0073 | 0 | 583 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age139_jitter450_spread0075 | reject | 139 | 450 | 0.0075 | 0 | 611 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 139, "max_ws_jitter_ms_for_caution": 196, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 139, "recovery_max_ws_jitter_ms": 196, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
