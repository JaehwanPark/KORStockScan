# Runtime Apply Bridge 2026-05-21

## 판정

- status: `pass`
- ready_for_approval_count: `0`
- runtime mutation: `none`

## 근거

- `entry_wait6579_score66_69_recovery_gate_v1`: state=`bootstrap_pending`, allowed_runtime_apply=`False`, approval_required=`True`
- `scale_in_bucket_runtime_policy_v1`: state=`bootstrap_pending`, allowed_runtime_apply=`False`, approval_required=`True`

## 다음 액션

- `ready_for_approval` 후보만 별도 approval artifact가 있으면 다음 PREOPEN env 후보로 소비한다.
- `bootstrap_pending` 후보는 rolling confirmation 후 다시 판정한다.
