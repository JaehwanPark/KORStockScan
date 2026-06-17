# Latency Classifier Recommendation 2026-06-17

- latency_block_count: 45315
- unique_codes: 70
- selected_profile_id: grid_age101_jitter217_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age101_jitter217_spread0050 | reject | 101 | 217 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0068 | reject | 101 | 217 | 0.0068 | 0 | 1656 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0075 | reject | 101 | 217 | 0.0075 | 0 | 2375 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0081 | reject | 101 | 217 | 0.0081 | 0 | 3082 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0085 | reject | 101 | 217 | 0.0085 | 0 | 3440 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0100 | reject | 101 | 217 | 0.0100 | 0 | 4117 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0105 | reject | 101 | 217 | 0.0105 | 0 | 4628 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0113 | reject | 101 | 217 | 0.0113 | 0 | 5219 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0114 | reject | 101 | 217 | 0.0114 | 0 | 5532 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter217_spread0120 | reject | 101 | 217 | 0.0120 | 0 | 5625 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0050 | reject | 101 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0068 | reject | 101 | 300 | 0.0068 | 0 | 1688 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0075 | reject | 101 | 300 | 0.0075 | 0 | 2415 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0081 | reject | 101 | 300 | 0.0081 | 0 | 3130 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0085 | reject | 101 | 300 | 0.0085 | 0 | 3489 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0100 | reject | 101 | 300 | 0.0100 | 0 | 4176 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0105 | reject | 101 | 300 | 0.0105 | 0 | 4691 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0113 | reject | 101 | 300 | 0.0113 | 0 | 5285 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0114 | reject | 101 | 300 | 0.0114 | 0 | 5604 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter300_spread0120 | reject | 101 | 300 | 0.0120 | 0 | 5700 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0050 | reject | 101 | 425 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0068 | reject | 101 | 425 | 0.0068 | 0 | 1741 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0075 | reject | 101 | 425 | 0.0075 | 0 | 2479 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0081 | reject | 101 | 425 | 0.0081 | 0 | 3201 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0085 | reject | 101 | 425 | 0.0085 | 0 | 3562 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0100 | reject | 101 | 425 | 0.0100 | 0 | 4268 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0105 | reject | 101 | 425 | 0.0105 | 0 | 4786 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0113 | reject | 101 | 425 | 0.0113 | 0 | 5386 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0114 | reject | 101 | 425 | 0.0114 | 0 | 5713 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age101_jitter425_spread0120 | reject | 101 | 425 | 0.0120 | 0 | 5821 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 101, "max_ws_jitter_ms_for_caution": 217, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 101, "recovery_max_ws_jitter_ms": 217, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
