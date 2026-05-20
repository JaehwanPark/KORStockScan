# Latency Classifier Recommendation 2026-05-20

- latency_block_count: 621
- unique_codes: 3
- selected_profile_id: balanced_1200_1500_0100

| profile | age_ms | jitter_ms | spread | pass_events | pass_ratio |
|---|---:|---:|---:|---:|---:|
| current_700_300_0050 | 700 | 300 | 0.0050 | 0 | 0.000 |
| quote_fresh_950_450_0075 | 950 | 450 | 0.0075 | 0 | 0.000 |
| mechanical_1200_500_0085 | 1200 | 500 | 0.0085 | 2 | 0.003 |
| balanced_1200_1500_0100 | 1200 | 1500 | 0.0100 | 220 | 0.354 |
| loose_age_1500_1500_0100 | 1500 | 1500 | 0.0100 | 220 | 0.354 |

## Apply Candidate

- calibration_state: adjust_up
- allowed_runtime_apply: True
- recommended_values: `{"max_ws_age_ms_for_caution": 1200, "max_ws_jitter_ms_for_caution": 1500, "max_spread_ratio_for_caution": 0.01}`
- reason: latency_block_profile_pass_count=220>=floor=124
