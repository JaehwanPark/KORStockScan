# Runtime Apply Bridge 2026-07-13

## 판정

- status: `pass`
- live_auto_apply_ready_count: `0`
- greenfield_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`
- greenfield_policy_emit_blocker: `no_live_auto_ready_lifecycle_flow`
- greenfield_policy_emit_blocker_detail: `lifecycle flow exists, but no lifecycle flow is live_auto_apply_ready for greenfield policy emission`
- greenfield_lifecycle_flow live/surfaced/total: `0` / `200` / `267`
- lifecycle_bucket_discovery_source_contract_status: `pass`
- lifecycle_bucket_discovery_ai_review_status: `parsed`
- lifecycle_bucket_promotion_window: `mtd`
- lifecycle_bucket_promotion_contract_passed: `True`
- lifecycle_bucket_discovery_live_followup_count: `0`
- note: `not_emitted_no_live_auto_ready_lifecycle_flow` means lifecycle flow exists but no greenfield live-auto-ready flow is available.
- human_approval_required: `False`
- runtime mutation: `none`
- warnings: `['greenfield_policy_not_emitted_no_live_auto_ready_lifecycle_flow']`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`entry_only_bridge_metadata`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, metadata_only=`True`, ai_followup=`-`
- `scale_in_bucket_runtime_policy_v1`: state=`blocked_incremental_ev_runtime_authority`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, metadata_only=`False`, ai_followup=`-`

## 다음 액션

- `live_auto_apply_ready` complete lifecycle/scale-in 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.
- `entry_only_bridge_metadata` 후보는 entry dimension/provenance로만 보존하며 PREOPEN live env 후보로 소비하지 않는다.
- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.
