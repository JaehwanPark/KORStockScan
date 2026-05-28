# Latency Classifier Recommendation 2026-05-28

- latency_block_count: 15392
- unique_codes: 52
- selected_profile_id: grid_age175_jitter99_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age175_jitter99_spread0050 | reject | 175 | 99 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0057 | reject | 175 | 99 | 0.0057 | 0 | 732 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0075 | reject | 175 | 99 | 0.0075 | 0 | 1124 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0079 | reject | 175 | 99 | 0.0079 | 0 | 1218 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0085 | reject | 175 | 99 | 0.0085 | 0 | 1599 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0092 | reject | 175 | 99 | 0.0092 | 0 | 1723 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0094 | reject | 175 | 99 | 0.0094 | 0 | 1974 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0100 | reject | 175 | 99 | 0.0100 | 0 | 2026 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0109 | reject | 175 | 99 | 0.0109 | 0 | 2063 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter99_spread0120 | reject | 175 | 99 | 0.0120 | 0 | 2093 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0050 | reject | 175 | 197 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0057 | reject | 175 | 197 | 0.0057 | 0 | 740 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0075 | reject | 175 | 197 | 0.0075 | 0 | 1133 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0079 | reject | 175 | 197 | 0.0079 | 0 | 1227 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0085 | reject | 175 | 197 | 0.0085 | 0 | 1609 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0092 | reject | 175 | 197 | 0.0092 | 0 | 1733 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0094 | reject | 175 | 197 | 0.0094 | 0 | 1986 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0100 | reject | 175 | 197 | 0.0100 | 0 | 2038 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0109 | reject | 175 | 197 | 0.0109 | 0 | 2075 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter197_spread0120 | reject | 175 | 197 | 0.0120 | 0 | 2105 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0050 | reject | 175 | 284 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0057 | reject | 175 | 284 | 0.0057 | 0 | 748 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0075 | reject | 175 | 284 | 0.0075 | 0 | 1141 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0079 | reject | 175 | 284 | 0.0079 | 0 | 1235 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0085 | reject | 175 | 284 | 0.0085 | 0 | 1617 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0092 | reject | 175 | 284 | 0.0092 | 0 | 1741 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0094 | reject | 175 | 284 | 0.0094 | 0 | 1994 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0100 | reject | 175 | 284 | 0.0100 | 0 | 2046 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0109 | reject | 175 | 284 | 0.0109 | 0 | 2083 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age175_jitter284_spread0120 | reject | 175 | 284 | 0.0120 | 0 | 2113 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 175, "max_ws_jitter_ms_for_caution": 99, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 175, "recovery_max_ws_jitter_ms": 99, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
