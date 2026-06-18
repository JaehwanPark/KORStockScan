# Runtime Apply Gap Audit - 2026-06-18

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `65`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `1`
- source dimension gap: `86` / actionable=`0`
- quiet gap: `395` / rollup=`395` / directive=`0`

## 공격적 런타임 추진 대상
- `entry:source_stage:wait6579_ev_cohort`: stage=entry, EV=2.2814, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:stale_bucket:fresh_or_unflagged`: stage=entry, EV=2.2814, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_70p`: stage=entry, EV=1.7396, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_66_69`: stage=entry, EV=2.6802, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over`: stage=entry, EV=1.5823, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov`: stage=entry, EV=1.6698, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:score_band:score_63_65`: stage=entry, EV=0.6283, 방향=runtime_bridge, 현재=sim_auto_approved
- `entry:liquidity_bucket:liquidity_high`: stage=entry, EV=1.6568, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_normal`: stage=entry, EV=1.132, 방향=runtime_bridge, 현재=code_patch_required
- `entry:chosen_action:wait_requote`: stage=entry, EV=2.2814, 방향=runtime_bridge, 현재=code_patch_required
- `entry:exit_rule:exit_unknown`: stage=entry, EV=2.2814, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:strong_strength_momentum`: stage=entry, EV=2.2234, 방향=runtime_bridge, 현재=code_patch_required
- `entry:strength_bucket:weak_strength_momentum`: stage=entry, EV=0.5707, 방향=runtime_bridge, 현재=code_patch_required
- `entry:overbought_bucket:overbought_ok`: stage=entry, EV=4.6088, 방향=runtime_bridge, 현재=code_patch_required
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dba225c97a`: stage=lifecycle_flow, EV=14.325534, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ccc3dfa9db`: stage=lifecycle_flow, EV=8.795684, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: stage=lifecycle_flow, EV=9.697522, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e15ee9c1d5`: stage=lifecycle_flow, EV=11.04438, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_56e6380928`: stage=lifecycle_flow, EV=8.082254, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7480cc41ef`: stage=lifecycle_flow, EV=8.643072, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `IMPLEMENT_SCALE_IN_POLICY_CONTRACT`: IMPLEMENT_SCALE_IN_POLICY_CONTRACT: scale_in_bucket_runtime_policy_v1:2026-06-18 후보가 env_mapping_missing 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
