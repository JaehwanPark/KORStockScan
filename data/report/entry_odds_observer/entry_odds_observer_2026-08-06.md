# Offline Entry Odds Observer V1 — 2026-08-06

## Decision

- Final state: `hold_sample`
- Identified with valid evidence: `True`
- Applied to simulation: `False`
- Runtime effect: `false`
- Source quality: `eligible_rows_only`
- Evaluation blockers: `["oos_evaluation_source_date_floor", "calibrated_probability_skill_not_proven", "counterfactual_fill_model_validation_not_closed", "negative_veto_sim_candidate_gate_not_closed", "cost_model_assumption_only"]`

## Evidence

- Predictions / eligible / excluded: 377 / 320 / 57
- Source-quality-adjusted EV: -0.238496573
- Assessment counts: `{"ABSTAIN": 57, "WOULD_BET": 0, "WOULD_NO_BET": 320}`
- Model-signal / prior-only fitted signatures: 0 / 9
- Raw calibration: `{"multiclass_brier_score": 0.794025, "multiclass_log_loss": 1.455666595, "sample_count": 320, "top_label_ece": 0.204625}`
- Calibrated: `{"multiclass_brier_score": 0.4518956542, "multiclass_log_loss": 0.8568168533, "sample_count": 320, "top_label_ece": 0.0819908065}`
- Historical-signature prior: `{"multiclass_brier_score": 0.4518956542, "multiclass_log_loss": 0.8568168533, "sample_count": 320, "top_label_ece": 0.0819908065}`
- Probability skill gate: `{"authority_if_passed": "evaluation_gate_only_no_runtime_apply", "baseline": "smoothed_exact_signature_historical_class_prior", "blockers": ["oos_log_loss_improves_historical_signature_prior"], "checks": {"oos_brier_not_worse_than_historical_signature_prior": true, "oos_log_loss_improves_historical_signature_prior": false}, "pass": false}`
- Independent fill validation rows / status: 0 / unvalidated
- Hypothetical avoided losers / foregone winners: 0 / 0
- Hypothetical buy retention: None

## Next action

- build_multi_date_oos_evaluation_window
- improve_probability_estimator_then_run_strict_oos_skill_test
- join_actual_submitted_order_fill_correlations_and_validate_fill_odds
- collect_existing_buy_overlap_and_measure_incremental_veto_ev
- replace_assumed_cost_fields_with_verified_instrument_execution_costs

> This report is counterfactual-only. `WOULD_BET` and `WOULD_NO_BET` are observer assessments, not trading actions.
