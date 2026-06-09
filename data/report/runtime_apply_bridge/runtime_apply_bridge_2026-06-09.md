# Runtime Apply Bridge 2026-06-09

## 판정

- status: `pass`
- live_auto_apply_ready_count: `0`
- greenfield_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`
- greenfield_policy_emit_blocker: `no_live_auto_ready_lifecycle_flow`
- greenfield_policy_emit_blocker_detail: `lifecycle flow exists, but no lifecycle flow is live_auto_apply_ready for greenfield policy emission`
- greenfield_lifecycle_flow live/surfaced/total: `0` / `200` / `326`
- lifecycle_bucket_discovery_source_contract_status: `pass`
- lifecycle_bucket_discovery_ai_review_status: `partial`
- lifecycle_bucket_promotion_window: `mtd`
- lifecycle_bucket_promotion_contract_passed: `False`
- lifecycle_bucket_discovery_live_followup_count: `0`
- note: `not_emitted_no_live_auto_ready_lifecycle_flow` means lifecycle flow exists but no greenfield live-auto-ready flow is available.
- human_approval_required: `False`
- runtime mutation: `none`
- warnings: `['promotion_lifecycle_bucket_discovery_contract_not_passed', 'greenfield_policy_not_emitted_no_live_auto_ready_lifecycle_flow', 'ai_review_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'ai_review_selected_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq']`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`blocked_source_quality`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`
- `scale_in_bucket_runtime_policy_v1`: state=`bootstrap_pending`, allowed_runtime_apply=`False`, approval_required=`False`, live_auto_apply=`False`, ai_followup=`-`

## 다음 액션

- `live_auto_apply_ready` 후보는 별도 approval artifact 없이 다음 PREOPEN env 후보로 소비한다.
- `blocked_*` 후보는 source-quality/rolling conflict가 해소될 때까지 env로 소비하지 않는다.
