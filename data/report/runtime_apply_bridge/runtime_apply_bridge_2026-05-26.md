# Runtime Apply Bridge 2026-05-26

## 판정

- status: `pass`
- live_auto_apply_ready_count: `2`
- lifecycle_bucket_discovery_source_contract_status: `pass`
- lifecycle_bucket_discovery_ai_review_status: `parsed`
- lifecycle_bucket_discovery_live_followup_count: `1`
- human_approval_required: `False`
- runtime mutation: `none`
- warnings: `['lifecycle_bucket_discovery_live_auto_post_apply_followup_required', 'ai_review_ambiguous_live_candidate_kept_for_post_apply']`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`live_auto_apply_ready`, allowed_runtime_apply=`True`, approval_required=`False`, live_auto_apply=`True`, ai_followup=`post_apply_verification`
- `scale_in_bucket_runtime_policy_v1`: state=`bootstrap_pending`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`
- `greenfield_real_environment_authority`: state=`live_auto_apply_ready`, allowed_runtime_apply=`True`, approval_required=`False`, live_auto_apply=`True`, ai_followup=`-`

## 다음 액션

- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.
- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.
