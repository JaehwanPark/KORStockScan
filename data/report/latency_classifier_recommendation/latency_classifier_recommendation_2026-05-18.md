# Latency Classifier Recommendation 2026-05-18

- latency_block_count: 125
- unique_codes: 2
- selected_profile_id: balanced_1200_1500_0100

| profile | age_ms | jitter_ms | spread | pass_events | pass_ratio |
|---|---:|---:|---:|---:|---:|
| current_700_300_0050 | 700 | 300 | 0.0050 | 4 | 0.032 |
| quote_fresh_950_450_0075 | 950 | 450 | 0.0075 | 10 | 0.080 |
| mechanical_1200_500_0085 | 1200 | 500 | 0.0085 | 10 | 0.080 |
| balanced_1200_1500_0100 | 1200 | 1500 | 0.0100 | 112 | 0.896 |
| loose_age_1500_1500_0100 | 1500 | 1500 | 0.0100 | 112 | 0.896 |

## Apply Candidate

- calibration_state: adjust_up
- allowed_runtime_apply: True
- recommended_values: `{"max_ws_age_ms_for_caution": 1200, "max_ws_jitter_ms_for_caution": 1500, "max_spread_ratio_for_caution": 0.01}`
- reason: latency_block_profile_pass_count=112>=floor=25
