# Runtime Apply Gap Audit - 2026-07-10

- 상태: `pass`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `84`
- 실패 표면화: `0`
- 재시도 큐: `0`
- Codex 작업지시: `4`
- source dimension gap: `60` / actionable=`4`
- quiet gap: `339` / rollup=`339` / directive=`0`

## 공격적 런타임 추진 대상
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_17be04825a`: stage=lifecycle_flow, EV=6.102223, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dbcdc8c839`: stage=lifecycle_flow, EV=7.88732, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d766d7a8b3`: stage=lifecycle_flow, EV=3.794062, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_46c89131ff`: stage=lifecycle_flow, EV=5.98978, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76`: stage=lifecycle_flow, EV=13.812302, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1d2a773521`: stage=lifecycle_flow, EV=4.072785, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_53dd26ec9c`: stage=lifecycle_flow, EV=10.178904, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e13d2dea57`: stage=lifecycle_flow, EV=13.501397, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60abfbeb0f`: stage=lifecycle_flow, EV=7.17241, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c95c89b312`: stage=lifecycle_flow, EV=7.90998, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d27ece90a1`: stage=lifecycle_flow, EV=21.639072, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_65ddf62dd9`: stage=lifecycle_flow, EV=19.382352, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5f1fd88426`: stage=lifecycle_flow, EV=8.498406, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7070cfbbdd`: stage=lifecycle_flow, EV=6.01339, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8070f782ab`: stage=lifecycle_flow, EV=3.681741, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_387f622ebb`: stage=lifecycle_flow, EV=3.254127, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa`: stage=lifecycle_flow, EV=7.628498, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5`: stage=lifecycle_flow, EV=10.398278, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc`: stage=lifecycle_flow, EV=9.457675, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved
- `swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c515f99b98`: stage=lifecycle_flow, EV=11.06151, 방향=sim_policy_or_approval_ready, 현재=sim_auto_approved

## 재시도 큐
- 재시도 대상 없음

## Codex 작업지시
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: scale_in:supply_pass_bucket:supply_pass_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: scale_in:time_bucket:time_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: scale_in:peak_profit_band:peak_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `RESOLVE_SOURCE_DIMENSION_GAP`: RESOLVE_SOURCE_DIMENSION_GAP: scale_in:profit_band:profit_unknown 후보가 emit_or_backfill_source_field 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
