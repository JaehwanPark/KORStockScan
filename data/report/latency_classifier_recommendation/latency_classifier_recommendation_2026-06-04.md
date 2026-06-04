# Latency Classifier Recommendation 2026-06-04

- latency_block_count: 4501
- unique_codes: 15
- selected_profile_id: grid_age133_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age133_jitter300_spread0050 | reject | 133 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0061 | reject | 133 | 300 | 0.0061 | 0 | 170 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0075 | reject | 133 | 300 | 0.0075 | 0 | 273 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0078 | reject | 133 | 300 | 0.0078 | 0 | 302 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0085 | reject | 133 | 300 | 0.0085 | 0 | 372 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0090 | reject | 133 | 300 | 0.0090 | 0 | 395 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0100 | reject | 133 | 300 | 0.0100 | 0 | 443 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0108 | reject | 133 | 300 | 0.0108 | 0 | 445 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0117 | reject | 133 | 300 | 0.0117 | 0 | 471 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter300_spread0120 | reject | 133 | 300 | 0.0120 | 0 | 471 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0050 | reject | 133 | 428 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0061 | reject | 133 | 428 | 0.0061 | 0 | 174 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0075 | reject | 133 | 428 | 0.0075 | 0 | 280 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0078 | reject | 133 | 428 | 0.0078 | 0 | 309 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0085 | reject | 133 | 428 | 0.0085 | 0 | 382 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0090 | reject | 133 | 428 | 0.0090 | 0 | 409 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0100 | reject | 133 | 428 | 0.0100 | 0 | 458 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0108 | reject | 133 | 428 | 0.0108 | 0 | 460 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0117 | reject | 133 | 428 | 0.0117 | 0 | 487 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter428_spread0120 | reject | 133 | 428 | 0.0120 | 0 | 487 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0050 | reject | 133 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0061 | reject | 133 | 450 | 0.0061 | 0 | 174 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0075 | reject | 133 | 450 | 0.0075 | 0 | 282 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0078 | reject | 133 | 450 | 0.0078 | 0 | 311 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0085 | reject | 133 | 450 | 0.0085 | 0 | 385 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0090 | reject | 133 | 450 | 0.0090 | 0 | 412 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0100 | reject | 133 | 450 | 0.0100 | 0 | 461 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0108 | reject | 133 | 450 | 0.0108 | 0 | 463 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0117 | reject | 133 | 450 | 0.0117 | 0 | 490 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age133_jitter450_spread0120 | reject | 133 | 450 | 0.0120 | 0 | 490 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 133, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 133, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
