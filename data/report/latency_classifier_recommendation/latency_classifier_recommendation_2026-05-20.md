# Latency Classifier Recommendation 2026-05-20

- latency_block_count: 621
- unique_codes: 3
- selected_profile_id: balanced_1200_1500_0100
- profile_generation: `{"mode": "grid_quantile_search", "profile_count": 486, "age_cap_ms": 1500, "jitter_cap_ms": 1500, "spread_cap_ratio": 0.012, "counterfactual_sample_floor": 3, "recovery_event_floor_ratio": 0.1}`
- counterfactual_source_status: `loaded`

| profile | action | age_ms | jitter_ms | spread | safe_pass | caution_reject | recovery | cf_sample | cf_ev_pct | missed_win | avoided_loser | stale_override | broker_bypass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_1200_1500_0100 | hold | 1200 | 1500 | 0.0100 | 0 | 220 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1500_spread0115 | hold | 1200 | 1500 | 0.0115 | 0 | 242 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1500_spread0120 | hold | 1200 | 1500 | 0.0120 | 0 | 246 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| loose_age_1500_1500_0100 | hold | 1500 | 1500 | 0.0100 | 0 | 220 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1500_spread0115 | hold | 1500 | 1500 | 0.0115 | 0 | 242 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1500_spread0120 | hold | 1500 | 1500 | 0.0120 | 0 | 246 | 220 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1500_spread0100 | hold | 950 | 1500 | 0.0100 | 0 | 218 | 218 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1500_spread0115 | hold | 950 | 1500 | 0.0115 | 0 | 240 | 218 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1500_spread0120 | hold | 950 | 1500 | 0.0120 | 0 | 244 | 218 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age700_jitter1500_spread0100 | hold | 700 | 1500 | 0.0100 | 0 | 213 | 213 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age700_jitter1500_spread0115 | hold | 700 | 1500 | 0.0115 | 0 | 234 | 213 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age700_jitter1500_spread0120 | hold | 700 | 1500 | 0.0120 | 0 | 238 | 213 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age668_jitter1500_spread0100 | hold | 668 | 1500 | 0.0100 | 0 | 212 | 212 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age668_jitter1500_spread0115 | hold | 668 | 1500 | 0.0115 | 0 | 233 | 212 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age668_jitter1500_spread0120 | hold | 668 | 1500 | 0.0120 | 0 | 237 | 212 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1500_spread0096 | hold | 1200 | 1500 | 0.0096 | 0 | 210 | 210 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1500_spread0096 | hold | 1500 | 1500 | 0.0096 | 0 | 210 | 210 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1500_spread0096 | hold | 950 | 1500 | 0.0096 | 0 | 208 | 208 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age536_jitter1500_spread0100 | hold | 536 | 1500 | 0.0100 | 0 | 206 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age536_jitter1500_spread0115 | hold | 536 | 1500 | 0.0115 | 0 | 226 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age536_jitter1500_spread0120 | hold | 536 | 1500 | 0.0120 | 0 | 230 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1377_spread0100 | hold | 1200 | 1377 | 0.0100 | 0 | 206 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1377_spread0115 | hold | 1200 | 1377 | 0.0115 | 0 | 227 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1200_jitter1377_spread0120 | hold | 1200 | 1377 | 0.0120 | 0 | 231 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1377_spread0100 | hold | 1500 | 1377 | 0.0100 | 0 | 206 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1377_spread0115 | hold | 1500 | 1377 | 0.0115 | 0 | 227 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age1500_jitter1377_spread0120 | hold | 1500 | 1377 | 0.0120 | 0 | 231 | 206 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1377_spread0100 | hold | 950 | 1377 | 0.0100 | 0 | 204 | 204 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1377_spread0115 | hold | 950 | 1377 | 0.0115 | 0 | 225 | 204 | 1 | -3.704 | 0 | 1 | 0 | 0 |
| grid_age950_jitter1377_spread0120 | hold | 950 | 1377 | 0.0120 | 0 | 229 | 204 | 1 | -3.704 | 0 | 1 | 0 | 0 |

## Apply Candidate

- calibration_state: hold_sample
- allowed_runtime_apply: False
- recommended_values: `{"max_ws_age_ms_for_caution": 1200, "max_ws_jitter_ms_for_caution": 1500, "max_spread_ratio_for_caution": 0.01, "recovery_enabled": false, "recovery_min_signal_score": 75.0, "recovery_max_ws_age_ms": 1200, "recovery_max_ws_jitter_ms": 1500, "recovery_max_spread_ratio": 0.01}`
- reason: recommended_action=hold; counterfactual_joined_sample=1 below floor=3; latency_blocks=621 recovery_count=220 floor=62 quote_stale_override=0 broker_guard_bypass=0
