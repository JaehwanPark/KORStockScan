# Runtime Apply Gap Audit - 2026-06-16

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `48`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `62` / actionable=`0`
- quiet gap: `405` / rollup=`405` / directive=`0`

## 공격적 런타임 추진 대상
- `entry:score_band:score_70p`: stage=entry, EV=0.9564, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.3544, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.3342, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: stage=entry, EV=1.3968, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=1.2732, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=0.7258, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:wait_requote`: stage=entry, EV=2.1966, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=2.1966, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_watch`: stage=entry, EV=3.2053, 방향=runtime_bridge, 현재=code_patch_required
- `entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hi`: stage=entry, EV=0.3982, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_ok`: stage=entry, EV=3.6472, 방향=runtime_bridge, 현재=code_patch_required
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: stage=lifecycle_flow, EV=14.205358, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: stage=lifecycle_flow, EV=12.85031, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_fbf43185e8`: stage=lifecycle_flow, EV=14.291363, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8070f782ab`: stage=lifecycle_flow, EV=2.742745, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ccc3dfa9db`: stage=lifecycle_flow, EV=6.916828, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c515f99b98`: stage=lifecycle_flow, EV=14.202819, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a`: stage=lifecycle_flow, EV=11.468694, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_310f349c63`: stage=lifecycle_flow, EV=10.508592, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077`: stage=lifecycle_flow, EV=9.83015, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: scale_in_bucket_runtime_policy_v1:2026-06-16 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
