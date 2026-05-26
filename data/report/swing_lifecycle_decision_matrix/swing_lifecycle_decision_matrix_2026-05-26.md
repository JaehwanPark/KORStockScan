# Swing Lifecycle Decision Matrix 2026-05-26

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `1721`
- probe_rows: `121`
- discovery_rows: `1600`
- sim_auto_candidate_count: `6`
- workorder_count: `9`
- swing_entry_bottleneck_primary: `SWING_ENTRY_DROUGHT_CRITICAL`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### entry_bucket_attribution
- source_row_count: `1589`
- bucket_count: `192`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_swing_score_vpw|-|BOTTOM|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|KOSPI_BASE|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1672`
- bucket_count: `48`
- sim_auto_candidate_count: `6`
- workorder_count: `5`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`29` ev=`14.597777`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`11.058628`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`6.947201`
- `mfe_mid|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`18` ev=`3.139001`
- `mfe_low|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`8` ev=`-3.0`
### scale_in_bucket_attribution
- source_row_count: `19`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `1600`
- bucket_count: `760`
- sim_auto_candidate_count: `0`
- workorder_count: `4`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`27.418388`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`18.465607`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|그린카_하이브리드카/전기차,스마트 그리드,휴대폰_수동부품|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`8.432044`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`6.630175`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC` route=`code_patch_required` joined=`4` ev=`6.357769`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
