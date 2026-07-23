# Tight Stop Entry Companion Report - 2026-07-23

- allowed_runtime_apply: `False`
- runtime_effect: `false`
- entry_path_sample_count: `4629`
- tight_stop_pct: `-0.7`
- mfe_target_pct: `0.3`
- mfe_before_tight_stop_rate: `0.147332`
- tight_stop_first_rate: `0.766688`
- top_companion_candidate_count: `0`
- companion_candidate_policy: `{'exclude_unknown_context': True, 'require_positive_survival_edge': True, 'primary_decision_metric': 'mfe_before_tight_stop_rate_minus_tight_stop_first_rate'}`

## Top Companion Candidates

```json
[]
```

## Real Submitted Path Validation

```json
{
  "decision": "hold_no_positive_real_submitted_pattern",
  "sample_floor": 20,
  "sample_floor_passed": true,
  "overall": {
    "sample_count": 50,
    "mfe_before_tight_stop_rate": 0.28,
    "tight_stop_first_rate": 0.58,
    "avg_mfe_10m_pct": -0.424,
    "avg_mae_10m_pct": -9.146
  },
  "row_authority": "real_submitted_path_observation",
  "companion_candidate_count": 0,
  "companion_candidates": [],
  "runtime_effect": false,
  "allowed_runtime_apply": false,
  "decision_authority": "source_only_tight_stop_entry_companion_observation"
}
```
