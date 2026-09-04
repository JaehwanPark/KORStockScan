# Limit-Down Watch Report — 2026-09-04

- generated_at: `2026-09-04T21:05:37.637927`
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
- sim_policy_applied_to_runtime: `False`
- automatic_live_conversion_performed: `False`
- real_post_apply_attribution_ready: `True`
- real_completed_sample_count: `0`
- real_source_quality_adjusted_ev_pct: `None`

## Blockers

- `ordered_intraday_path_sample_missing`
- `ordered_intraday_path_capture_missing`
- `bounded_live_candidate_contract_missing`
- `current_real_runtime_policy_not_applied`

| class | code | observed evidence | next action | acceptance test |
| --- | --- | --- | --- | --- |
| ordered_path_observation | ordered_intraday_path_sample_missing | evidence readiness contains blocker ordered_intraday_path_sample_missing | capture a valid same-session ordered trade/BBO path | ordered_unlock_relock_path_capture |
| ordered_path_observation | ordered_intraday_path_capture_missing | evidence readiness contains blocker ordered_intraday_path_capture_missing | capture a valid same-session ordered trade/BBO path | ordered_unlock_relock_path_capture |
| sample_or_ev_guard | bounded_live_candidate_contract_missing | no source-quality-bound positive bounded candidate exists | collect valid ordered paths until one cohort×band passes all guards | report contract check and threshold runtime env/PID verification pass |
| runtime_observation | current_real_runtime_policy_not_applied | no exact-date live policy is active in the target-date runtime state | retain source-only observation until a valid next-PREOPEN handoff occurs | report contract check and threshold runtime env/PID verification pass |

## Candidate Source Selection

- source_quality_status: `no_candidate`
- candidate_count: `0`
- blocked_count: `0`
- excluded_count: `1`
- excluded_rows: `[{"code": "286750", "reason": "near_ka10099_official_exclusion", "eligibility_reasons": ["audit_info_excluded"]}]`

## Rolling Conversion Evidence

- status: `insufficient_sample`
- observation_day_count: `4`
- ordered_path_captured_code_count: `5`
- ordered_intraday_path_capture_rate: `45.4545`

## Conversion Artifact Checks

| artifact | status | issues |
| --- | --- | --- |
| counterfactual | invalid | status_not_pass, sample_floor_not_met, observation_day_floor_not_met, eligible_policy_missing, eligible_policy_ev_not_positive |
| sim_policy_catalog | invalid | status_not_pass, sim_apply_not_allowed, active_policy_missing, runtime_payload_contract_invalid, runtime_payload:status_not_pass, runtime_payload:sim_apply_not_allowed, runtime_payload:source_artifact_invalid, runtime_payload:active_policy_count_invalid |
| post_sim_attribution | invalid | status_not_pass, source_quality_not_pass, source_quality_preflight_unbound, sample_floor_not_met, qualified_policy_missing, qualified_policy_ev_not_positive |
| real_post_apply_attribution | pass | - |
| bounded_live_candidate | invalid | runtime_apply_not_allowed, status_not_ready, ready_candidate_missing, candidate_row_contract_invalid, runtime_payload_contract_invalid, runtime_payload:status_not_ready, runtime_payload:source_artifact_invalid, runtime_payload:runtime_apply_not_allowed, runtime_payload:candidate_count_invalid |
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
