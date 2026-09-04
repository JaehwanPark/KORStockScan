# Main AI Prompt Consumer - 2026-09-03

## Decision
- status: `ready_source_only_consumer_closure`
- decision: `all_main_ai_request_paths_classified_runtime_update_still_blocked`
- unclassified_request_path_count: `0`
- entry_followup_terminal_ready: `False`
- runtime_prompt_update_allowed: `False`
- profit_improvement_demonstrated: `False`
- future_profit_improving_output_likelihood: `blocked_pending_entry_hash_refresh_and_holding_provider_checkpoint`

## Base Consumers
- `entry_base`: connected=`0`, blocked=`2`
  - `KRX/KRX_REGULAR` status=`intentionally_blocked_with_owner_and_acceptance_test` reason=`entry_batch_optimizer_hash_binding_missing`
  - `NXT/NXT_AFTERMARKET` status=`intentionally_blocked_with_owner_and_acceptance_test` reason=`entry_batch_optimizer_hash_binding_missing`
- `holding_base`: connected=`1`, blocked=`0`
  - `KRX/KRX_REGULAR` status=`connected_and_hash_bound` reason=`None`

## Optional 2x2 Prompt/Input Cells
- cell_count: `48`
- status_counts: `{'intentionally_blocked_with_owner_and_acceptance_test': 45, 'retired_as_duplicate_of_existing_r0_r3': 3}`
- Existing exact R0-R3 cells are routed as duplicates; they are not queued by this consumer.

## Runtime Guard
- Runtime prompt update remains blocked until isolated 5/10/20-day EV, net-profit, p10-tail, HELD, and post-apply guards pass.
