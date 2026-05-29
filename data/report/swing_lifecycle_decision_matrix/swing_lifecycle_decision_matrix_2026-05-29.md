# Swing Lifecycle Decision Matrix 2026-05-29

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `3685`
- probe_rows: `81`
- discovery_rows: `3604`
- sim_auto_candidate_count: `0`
- workorder_count: `7`
- swing_lifecycle_flow_bucket_count: `63`
- complete_flow_count: `14`
- incomplete_flow_count: `3611`
- identity_join_rate: `1.0`
- complete_flow_rate: `0.003862`
- join_contract_blocked: `False`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### swing_lifecycle_flow_bucket_attribution
- source_row_count: `3685`
- bucket_count: `63`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`11` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_mid_mae_mid_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`9` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_low_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`8` ev=`-3.0`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_green_held_missing_trailing_after_mfe_stop` route=`source_only_keep_collecting` joined=`6` ev=`17.445292`
- `entry=entry:missing|holding=holding:missing|scale_in=scale_in:none|exit=swing_exit:holding_exit_bucket_attribution:mfe_high_mae_deep_held_missing_mae_stop_touched` route=`source_only_keep_collecting` joined=`5` ev=`-3.0`
### entry_bucket_attribution
- source_row_count: `3587`
- bucket_count: `253`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_swing_gap|-|BOTTOM|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|KOSPI_BASE|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|BREAKOUT|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `3653`
- bucket_count: `56`
- sim_auto_candidate_count: `0`
- workorder_count: `2`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`17.445292`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`9.519058`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`7.486802`
- `mfe_high|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`11` ev=`-3.0`
- `mfe_mid|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`9` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `11`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `3604`
- bucket_count: `1316`
- sim_auto_candidate_count: `0`
- workorder_count: `5`
- `pullback_limit_entry|risk_capped|mae_stop_time_stop|Manufacture of Electronic Components|LCD_부품,LED,무선충전기관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`5` ev=`-3.0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`13.766213`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`10.094596`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Basic Chemicals|-|DIAGNOSTIC` route=`code_patch_required` joined=`3` ev=`4.921204`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`4.092489`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
