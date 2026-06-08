# Latency Classifier Recommendation 2026-06-08

- latency_block_count: 16584
- unique_codes: 92
- selected_profile_id: grid_age110_jitter300_spread0050
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 720, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_normal | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| grid_age110_jitter300_spread0050 | reject | 110 | 300 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0075 | reject | 110 | 300 | 0.0075 | 0 | 369 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0075 | reject | 110 | 300 | 0.0075 | 0 | 371 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0085 | reject | 110 | 300 | 0.0085 | 0 | 631 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0090 | reject | 110 | 300 | 0.0090 | 0 | 736 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0100 | reject | 110 | 300 | 0.0100 | 0 | 834 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0117 | reject | 110 | 300 | 0.0117 | 0 | 1059 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter300_spread0120 | reject | 110 | 300 | 0.0120 | 0 | 1085 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0050 | reject | 110 | 386 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0075 | reject | 110 | 386 | 0.0075 | 0 | 369 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0075 | reject | 110 | 386 | 0.0075 | 0 | 371 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0085 | reject | 110 | 386 | 0.0085 | 0 | 632 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0090 | reject | 110 | 386 | 0.0090 | 0 | 737 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0100 | reject | 110 | 386 | 0.0100 | 0 | 835 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0117 | reject | 110 | 386 | 0.0117 | 0 | 1062 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter386_spread0120 | reject | 110 | 386 | 0.0120 | 0 | 1088 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0050 | reject | 110 | 450 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0075 | reject | 110 | 450 | 0.0075 | 0 | 378 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0075 | reject | 110 | 450 | 0.0075 | 0 | 380 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0085 | reject | 110 | 450 | 0.0085 | 0 | 645 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0090 | reject | 110 | 450 | 0.0090 | 0 | 750 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0100 | reject | 110 | 450 | 0.0100 | 0 | 849 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0117 | reject | 110 | 450 | 0.0117 | 0 | 1080 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter450_spread0120 | reject | 110 | 450 | 0.0120 | 0 | 1106 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0050 | reject | 110 | 500 | 0.0050 | 0 | 0 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0075 | reject | 110 | 500 | 0.0075 | 0 | 380 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0075 | reject | 110 | 500 | 0.0075 | 0 | 382 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0085 | reject | 110 | 500 | 0.0085 | 0 | 647 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0090 | reject | 110 | 500 | 0.0090 | 0 | 753 | 0 | 0 | None | 0 | 0 | 0 | 0 |
| grid_age110_jitter500_spread0100 | reject | 110 | 500 | 0.0100 | 0 | 852 | 0 | 0 | None | 0 | 0 | 0 | 0 |

## Apply Candidate

- calibration_state: hold
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 110, "max_ws_jitter_ms_for_caution": 300, "max_spread_ratio_for_caution": 0.005, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 110, "recovery_max_ws_jitter_ms": 300, "recovery_max_spread_ratio": 0.005}`
- reason: latency runtime simplified: CAUTION no longer blocks submit after slippage check; DANGER/stale/broker safety remains blocked; no adaptive latency env apply
