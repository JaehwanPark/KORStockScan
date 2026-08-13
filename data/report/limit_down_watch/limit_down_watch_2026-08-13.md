# Limit-Down Watch Report — 2026-08-13

- generated_at: `2026-08-13T20:14:29.150136`
- status: `no_observation`
- registered_code_count: `0`
- snapshot_code_count: `0`
- quote_snapshot_code_count: `0`
- market_data_observed_code_count: `0`
- event_source_required: `False`
- event_source_read_mode: `not_scanned_candidate_preflight`
- ordered_intraday_path_capture: `0`
- sim_candidate_ready: `False`
- real_trading_ready: `False`
- decision: `collect_source_and_auto_promote_eligible_type`
- conversion_decision: `keep_observing_and_build_evidence`
- observer_activation_observed: `True`
- live_conversion_review_ready: `False`
- operator_approval_required: `False`
- bounded_live_candidate_ready: `False`
- separate_preopen_apply_ready: `False`
- automatic_live_conversion_performed: `False`

## Blockers

- `ordered_intraday_path_sample_missing`
- `ordered_intraday_path_capture_missing`
- `bounded_live_candidate_contract_missing`

## Rolling Conversion Evidence

- status: `insufficient_sample`
- observation_day_count: `1`
- ordered_path_captured_code_count: `2`
- ordered_intraday_path_capture_rate: `33.3333`

## Conversion Artifact Checks

| artifact | status | issues |
| --- | --- | --- |
| counterfactual | invalid | status_not_pass, sample_floor_not_met, observation_day_floor_not_met, eligible_policy_missing, eligible_policy_ev_not_positive, contract_mismatch:sample_floor |
| sim_policy_catalog | invalid | status_not_pass, sim_apply_not_allowed, active_policy_missing |
| post_sim_attribution | invalid | status_not_pass, sample_floor_not_met, qualified_policy_missing, qualified_policy_ev_not_positive |
| bounded_live_candidate | invalid | runtime_apply_not_allowed, status_not_ready, ready_candidate_missing, candidate_row_contract_invalid |
| live_conversion_approval | not_required_live_auto | - |

## Cohort / Price Band

| cohort | price_band | registered | trade_snapshots | quote_snapshots | market_data_observed | unlocked | relocked | ordered_trade_path_capture_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |

## Contract

- decision_authority: `limit_down_source_observation_only`
- runtime_effect: `False`
- actual_order_submitted: `False`
- broker_order_forbidden: `True`
- allowed_sim_apply: `False`
- allowed_runtime_apply: `False`
