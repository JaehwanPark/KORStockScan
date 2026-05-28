# Swing Lifecycle Decision Matrix 2026-05-28

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `2922`
- probe_rows: `68`
- discovery_rows: `2854`
- sim_auto_candidate_count: `13`
- workorder_count: `9`
- swing_entry_bottleneck_primary: `SWING_ENTRY_BOTTLENECK_OBSERVE`
- swing_lifecycle_contract_gap_count: `4`
- daily_simulation_consumed: `False`
- warnings: `['pending_future_quotes']`

## Bucket Attribution
### entry_bucket_attribution
- source_row_count: `2802`
- bucket_count: `236`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `blocked_swing_gap|-|BREAKOUT|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_gatekeeper_reject|-|KOSPI_BASE|gap_down|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|gap_down_large|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_score_vpw|-|BREAKOUT|flat_up|lt55|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `blocked_swing_gap|-|KOSPI_BASE|gap_up|missing|vpw_extreme|KOSPI_ML|-|sim_virtual_budget_dynamic_formula` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `2899`
- bucket_count: `54`
- sim_auto_candidate_count: `11`
- workorder_count: `5`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`17.862866`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`13.68759`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`7` ev=`11.32841`
- `mfe_high|mae_flat|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`10.48803`
- `mfe_high|mae_deep|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`3` ev=`9.490516`
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
- workorder_count: `4`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Semiconductor|반도체_생산|DIAGNOSTIC` route=`sim_auto_approved` joined=`3` ev=`13.567215`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`sim_auto_approved` joined=`4` ev=`12.091918`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`10.039792`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|기계_건설기계|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`2` ev=`9.053244`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Semiconductor|반도체_생산,반도체_시스템반도체|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`7.926968`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
