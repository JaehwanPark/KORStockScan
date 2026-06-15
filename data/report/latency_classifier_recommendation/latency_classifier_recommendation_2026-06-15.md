# Latency Classifier Recommendation 2026-06-15

- latency_block_count: 16406
- unique_codes: 61
- selected_profile_id: grid_age119_jitter150_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 900, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age119_jitter150_spread0050 | reject | 119 | 150 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0070 | reject | 119 | 150 | 0.0070 | 0 | 445 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0075 | reject | 119 | 150 | 0.0075 | 0 | 609 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0085 | reject | 119 | 150 | 0.0085 | 0 | 949 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0088 | reject | 119 | 150 | 0.0088 | 0 | 1008 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0100 | reject | 119 | 150 | 0.0100 | 0 | 1121 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0111 | reject | 119 | 150 | 0.0111 | 0 | 1468 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0117 | reject | 119 | 150 | 0.0117 | 0 | 1716 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0118 | reject | 119 | 150 | 0.0118 | 0 | 1772 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter150_spread0120 | reject | 119 | 150 | 0.0120 | 0 | 1781 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0050 | reject | 119 | 295 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0070 | reject | 119 | 295 | 0.0070 | 0 | 448 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0075 | reject | 119 | 295 | 0.0075 | 0 | 614 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0085 | reject | 119 | 295 | 0.0085 | 0 | 959 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0088 | reject | 119 | 295 | 0.0088 | 0 | 1018 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0100 | reject | 119 | 295 | 0.0100 | 0 | 1132 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0111 | reject | 119 | 295 | 0.0111 | 0 | 1479 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0117 | reject | 119 | 295 | 0.0117 | 0 | 1728 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0118 | reject | 119 | 295 | 0.0118 | 0 | 1785 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter295_spread0120 | reject | 119 | 295 | 0.0120 | 0 | 1794 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0050 | reject | 119 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0070 | reject | 119 | 300 | 0.0070 | 0 | 448 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0075 | reject | 119 | 300 | 0.0075 | 0 | 614 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0085 | reject | 119 | 300 | 0.0085 | 0 | 959 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0088 | reject | 119 | 300 | 0.0088 | 0 | 1018 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0100 | reject | 119 | 300 | 0.0100 | 0 | 1132 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0111 | reject | 119 | 300 | 0.0111 | 0 | 1479 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0117 | reject | 119 | 300 | 0.0117 | 0 | 1728 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0118 | reject | 119 | 300 | 0.0118 | 0 | 1785 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age119_jitter300_spread0120 | reject | 119 | 300 | 0.0120 | 0 | 1794 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 119, "max_ws_jitter_ms_for_caution": 150, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 119, "recovery_max_ws_jitter_ms": 150, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
