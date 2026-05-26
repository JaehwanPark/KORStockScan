# Runtime Apply Bridge 2026-05-26

## 판정

- status: `pass`
- live_auto_apply_ready_count: `0`
- lifecycle_bucket_discovery_source_contract_status: `pass`
- lifecycle_bucket_discovery_ai_review_status: `parsed`
- lifecycle_bucket_discovery_live_followup_count: `0`
- human_approval_required: `False`
- runtime mutation: `none`
- warnings: `[]`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`legacy_counterfactual_live_exception_removed`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`
- `scale_in_bucket_runtime_policy_v1`: state=`runtime_blocked_contract_gap`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`

## 다음 액션

- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.
- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.
