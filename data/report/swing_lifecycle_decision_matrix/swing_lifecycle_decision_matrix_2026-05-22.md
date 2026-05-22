# Swing Lifecycle Decision Matrix 2026-05-22

## Summary
- runtime_effect: `False`
- decision_authority: `swing_ldm_source_only`
- total_rows: `1200`
- probe_rows: `0`
- discovery_rows: `1200`
- sim_auto_candidate_count: `4`
- workorder_count: `0`
- daily_simulation_consumed: `False`
- warnings: `['swing_intraday_live_equiv_probe_missing', 'pending_future_quotes']`

## Bucket Attribution
### entry_bucket_attribution
- source_row_count: `1168`
- bucket_count: `159`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `swing_strategy_discovery_sim_v1|blocked_swing_gap|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|blocked_swing_gap|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|next_open_entry|next_open|volatility_adjusted` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|blocked_swing_gap|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_not_touched|equal_notional` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|blocked_swing_gap|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|pullback_limit_entry|pullback_not_touched|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
- `swing_strategy_discovery_sim_v1|blocked_swing_gap|MIDDLE|discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|gap_fade_entry|gap_fade_condition_not_met|risk_capped` route=`source_only_keep_collecting` joined=`0` ev=`0.0`
### holding_exit_bucket_attribution
- source_row_count: `1200`
- bucket_count: `31`
- sim_auto_candidate_count: `4`
- workorder_count: `0`
- `mfe_high|mae_green|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`4` ev=`18.57446`
- `mfe_high|mae_low|held_missing|trailing_after_mfe_stop|-|-|-` route=`sim_auto_approved` joined=`5` ev=`10.952632`
- `mfe_low|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`12` ev=`-3.0`
- `mfe_neg|mae_mid|held_missing|mae_stop_touched|-|-|-` route=`sim_auto_approved` joined=`3` ev=`-3.0`
- `mfe_high|mae_mid|held_missing|trailing_after_mfe_stop|-|-|-` route=`source_only_keep_collecting` joined=`2` ev=`4.874344`
### scale_in_bucket_attribution
- source_row_count: `0`
- bucket_count: `0`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
### discovery_arm_attribution
- source_row_count: `1200`
- bucket_count: `616`
- sim_auto_candidate_count: `0`
- workorder_count: `0`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Parts and Accessories for Motor Vehicles(New Products)|그린카_하이브리드카/전기차,자동차_전장화 수혜,자동차_차량용 반도체|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`4.176245`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),스마트폰_삼성전자관련주,휴대폰_카메라|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`3.207793`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|PCB(인쇄회로기판),반도체_후공정소재,스마트폰_삼성전자관련주|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`3.149539`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Other Financial Intermediation|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.863739`
- `breakout_confirm_entry|confidence_weighted|trailing_after_mfe|Manufacture of Electronic Components|-|DIAGNOSTIC` route=`source_only_keep_collecting` joined=`1` ev=`2.539859`

## Contract
Swing LDM only consumes probe and strategy discovery simulation sources.
