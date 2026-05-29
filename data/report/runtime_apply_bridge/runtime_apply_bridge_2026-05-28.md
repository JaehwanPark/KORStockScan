# Runtime Apply Bridge 2026-05-28

## 판정

- status: `pass`
- live_auto_apply_ready_count: `0`
- greenfield_policy_emit_state: `not_emitted_no_complete_lifecycle_flow`
- greenfield_lifecycle_flow live/surfaced/total: `0` / `97` / `97`
- lifecycle_bucket_discovery_source_contract_status: `warning`
- lifecycle_bucket_discovery_ai_review_status: `parsed`
- lifecycle_bucket_discovery_live_followup_count: `0`
- human_approval_required: `False`
- runtime mutation: `none`
- warnings: `['greenfield_policy_not_emitted_no_complete_lifecycle_flow', 'lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`blocked_source_quality`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`
- `scale_in_bucket_runtime_policy_v1`: state=`bootstrap_pending`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`

## 다음 액션

- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.
- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.
