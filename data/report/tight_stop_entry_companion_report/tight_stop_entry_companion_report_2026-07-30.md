# Tight Stop Entry Companion Report - 2026-07-30

- allowed_runtime_apply: `False`
- runtime_effect: `false`
- entry_path_sample_count: `4657`
- tight_stop_pct: `-0.7`
- mfe_target_pct: `0.3`
- mfe_before_tight_stop_rate: `0.148164`
- tight_stop_first_rate: `0.765944`
- top_companion_candidate_count: `0`
- companion_candidate_policy: `{'exclude_unknown_context': True, 'require_positive_survival_edge': True, 'primary_decision_metric': 'mfe_before_tight_stop_rate_minus_tight_stop_first_rate'}`

## Top Companion Candidates

```json
[]
```

## Real Submitted Path Validation

```json
{
  "decision": "source_only_real_submitted_positive_pattern_found",
  "sample_floor": 20,
  "sample_floor_passed": true,
  "overall": {
    "sample_count": 69,
    "mfe_before_tight_stop_rate": 0.304348,
    "tight_stop_first_rate": 0.565217,
    "avg_mfe_10m_pct": -0.16,
    "avg_mae_10m_pct": -7.145942
  },
  "row_authority": "real_submitted_path_observation",
  "companion_candidate_count": 1,
  "companion_candidates": [
    {
      "companion_key": "score_band=score_lt60|buy_pressure_bucket=pressure_lt55",
      "dimensions": [
        "score_band",
        "buy_pressure_bucket"
      ],
      "sample_count": 20,
      "mfe_before_tight_stop_rate": 0.4,
      "tight_stop_first_rate": 0.3,
      "avg_mfe_10m_pct": 0.3575,
      "avg_mae_10m_pct": -0.865,
      "tight_stop_survival_edge": 0.1,
      "runtime_effect": false,
      "allowed_runtime_apply": false,
      "decision_authority": "source_only_tight_stop_entry_companion_observation"
    }
  ],
  "runtime_effect": false,
  "allowed_runtime_apply": false,
  "decision_authority": "source_only_tight_stop_entry_companion_observation"
}
```
