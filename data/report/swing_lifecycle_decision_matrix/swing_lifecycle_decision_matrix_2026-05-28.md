# Swing Lifecycle Decision Matrix 2026-05-28

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `2902`
- probe_rows: `48`
- discovery_rows: `2854`
- sim_auto_candidate_count: `16`
- workorder_count: `16`
- swing_entry_bottleneck_primary: `None`
- swing_lifecycle_contract_gap_count: `None`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### entry_bucket_attribution
- source_row_count: `2709`
- bucket_count: `243`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_swing_gap|-|BREAKOUT|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|KOSPI_BASE|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2884`
- bucket_count: `57`
- sim_auto_candidate_count: `14`
- workorder_count: `3`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`10` ev=`17.114405`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`14.871617`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`11.419721`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`10.439725`
- `mfe_mid|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`6` ev=`3.955072`
### scale_in_bucket_attribution
- source_row_count: `8`
- bucket_count: `1`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `AVG_DOWN|instrumentation_gap|swing_dynamic_allowed|market` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### discovery_arm_attribution
- source_row_count: `2854`
- bucket_count: `1103`
- sim_auto_candidate_count: `2`
- workorder_count: `13`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Semiconductor|반도체_생산|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`16.999784`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`11.649548`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`12.358245`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`10.334378`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Computer programming, System Integration and Management Services|-|DIAGNOSTIC` route=`code_patch_required` joined=`3` ev=`8.249021`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
