# Runtime Apply Gap Audit - 2026-06-17

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `51`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `61` / actionable=`0`
- quiet gap: `429` / rollup=`429` / directive=`0`

## 공격적 런타임 추진 대상
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=1.8511, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=1.8511, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=1.8157, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=1.2913, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=2.0801, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: stage=entry, EV=2.6681, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.6894, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=0.9511, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=0.8991, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:wait_requote`: stage=entry, EV=1.8511, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=1.8511, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=1.6437, 방향=runtime_bridge, 현재=code_patch_required
- `entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hi`: stage=entry, EV=0.4995, 방향=runtime_bridge, 현재=code_patch_required
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf`: stage=lifecycle_flow, EV=17.789738, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: stage=lifecycle_flow, EV=11.004848, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8070f782ab`: stage=lifecycle_flow, EV=2.764235, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: stage=lifecycle_flow, EV=12.368759, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e59ff4f40e`: stage=lifecycle_flow, EV=9.265582, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077`: stage=lifecycle_flow, EV=7.446808, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ece5318efb`: stage=lifecycle_flow, EV=3.571373, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET`: IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET: scale_in_bucket_runtime_policy_v1:2026-06-17 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
