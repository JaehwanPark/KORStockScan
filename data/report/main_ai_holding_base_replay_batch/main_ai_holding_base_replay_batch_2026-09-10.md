# Main AI Holding Base Replay Manifest - 2026-09-10

## Decision
- status: `ready_source_only_holding_base_manifest`
- decision: `holding_base_request_path_hash_bound_provider_execution_gated`
- exact request fingerprints: `162`
- natural_empty_holding_observation: `False`
- provider_call_performed: `False`

## Cohorts
- `KRX/KRX_REGULAR` status=`connected_and_hash_bound`, requests=`162`, future provider candidate/deferred=`30/132`, reason=`None`

## Authority
- This manifest makes no provider call and cannot change a runtime prompt, provider route, order, threshold, price, quantity, cap, bot, broker guard, or hard safety.
- New Holding execution remains blocked until the shared provider-budget and durable-checkpoint acceptance test passes.
