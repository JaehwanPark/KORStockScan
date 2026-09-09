# Expanded lower-price entry-spot research — 2026-09-09

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-09`; trading dates `67`; calibration `51`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `7`.
Economic decision: same-window cost-adjusted net profit with positive EV; calibration-half signs are robustness diagnostics. HELD custody continues across date/window boundaries without invented resolution.

## Existing two-filter economic replay (source-only)

- `logic_samsung_heavy_midday`: rolling_high_drawdown_pct: hold_no_edge (-6.674626870000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.49194029999999955 KRW/day).
- `logic_samsung_heavy_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-17.617462680000003 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.2600000000000016 KRW/day).
- `logic_sk_eternix_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-10.25 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.598656719999994 KRW/day).
- `logic_mirae_asset_morning`: rolling_high_drawdown_pct: hold_no_edge (-30.137462690000007 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.73611941 KRW/day).
- `logic_jeju_semiconductor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.054925380000014457 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.929552239999992 KRW/day).
- `logic_doosan_enerbility_morning`: rolling_high_drawdown_pct: hold_no_edge (-37.54686567 KRW/day), rolling_low_proximity_pct: hold_no_edge (-44.56791045 KRW/day).
- `logic_hanwha_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.892686569999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-14.172985080000018 KRW/day).
- `logic_kakao_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.53447761 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kakao_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-11.450149249999999 KRW/day).
- `logic_sk_eternix_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-65.73582089 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_mirae_asset_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (36.775522390000006 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.05492536999999942 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.47343283 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-2.2829850700000023 KRW/day).
- `logic_doosan_enerbility_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-21.78447761000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-19.113283580000015 KRW/day).
- `logic_kakao_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.61895522 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_telecom_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.7113432800000012 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.865223880000002 KRW/day).
- `logic_samsung_ea_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-15.118805970000004 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (17.48641791 KRW/day).
- `logic_samsung_ea_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_morning`: rolling_high_drawdown_pct: hold_no_edge (-28.228358210000003 KRW/day), rolling_low_proximity_pct: hold_no_edge (-5.950000000000003 KRW/day).
- `logic_sk_telecom_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-11.261492540000006 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-112.79298507000001 KRW/day).
- `logic_hanse_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.28895522 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_morning`: rolling_high_drawdown_pct: hold_no_edge (-6.34462687 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.5765671700000006 KRW/day).
- `logic_cj_cgv_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.59313433 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_cj_cgv_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_tym_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (1.4379104399999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.80298508 KRW/day).
- `logic_tym_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-0.35776118999999995 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_hanse_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.68 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6823880599999992 KRW/day).
- `logic_kepco_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.1192537300000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.51208955 KRW/day).
- `logic_kepco_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.3868656699999997 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.4791044799999993 KRW/day).
- `logic_cj_cgv_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-1.40955224 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.7005970100000001 KRW/day).
- `logic_hanse_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.4014925399999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.31238805999999997 KRW/day).
- `logic_youngone_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_youngone_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-51.231940300000005 KRW/day), rolling_low_proximity_pct: hold_no_edge (-15.587313429999995 KRW/day).
- `logic_nhn_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-31.45238806 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-19.392686569999995 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.63417911000002 KRW/day).
- `logic_mirae_asset_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.7217910399999994 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.171343280000002 KRW/day).
- `logic_kepco_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.42985075 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-22.221940290000006 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.861194030000007 KRW/day).
- `logic_nhn_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-38.370447760000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-3.1259701500000006 KRW/day).
- `logic_sd_biosensor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sd_biosensor_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.72402985 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7168656700000002 KRW/day).
- `logic_sd_biosensor_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7158209000000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7038806000000002 KRW/day).
- `logic_doosan_enerbility_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (56.010447760000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (15.08940298 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-1.4402985099999999 KRW/day).
- `logic_sk_telecom_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-5.132985079999999 KRW/day).
- `logic_fan_ocean_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5437313500000003 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.8740298499999999 KRW/day).
- `logic_fan_ocean_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.9619403 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6410447799999996 KRW/day).
- `logic_samsung_heavy_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.52955223 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.48328358000000193 KRW/day).
- `logic_cj_cgv_morning`: source_runtime_policy_unavailable.
- `logic_fan_ocean_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-2.9616417900000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.3070149200000003 KRW/day).
- `logic_youngone_midday`: source_runtime_policy_unavailable.
- `logic_sk_telecom_midday`: source_runtime_policy_unavailable.
- `logic_nhn_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-6.0814925399999975 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.8877611899999991 KRW/day).
- `logic_tym_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.536567160000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-21.88179104 KRW/day).
- `logic_sd_biosensor_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-1.9229850699999997 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).

Quarantined source symbols:
- `044380`: `044380_source_quality_fail`

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `10/3`; completed legs `18/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | -0.044211 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 10 | 18 | 0 | 0.00243 | 0.00243 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 10 | 0 | None | -0.099212 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 0 | None | 0.0 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 2 | None | 0.0 |
| new_symbol | 044380 | 주연테크 | morning | source_quality_quarantined_no_evaluation:044380_source_quality_fail | N/A | 0 | 0 | 0 | N/A | N/A |
| new_symbol | 044380 | 주연테크 | late_morning | source_quality_quarantined_no_evaluation:044380_source_quality_fail | N/A | 0 | 0 | 0 | N/A | N/A |
| new_symbol | 044380 | 주연테크 | midday | source_quality_quarantined_no_evaluation:044380_source_quality_fail | N/A | 0 | 0 | 0 | N/A | N/A |
| new_symbol | 044380 | 주연테크 | afternoon | source_quality_quarantined_no_evaluation:044380_source_quality_fail | N/A | 0 | 0 | 0 | N/A | N/A |
| new_symbol | 011170 | 롯데케미칼 | morning | holdout_pass_source_only_early_candidate | 09:20~09:59; L20; DD0.5; NL0.75 | 13 | 20 | 2 | 0.095561 | None |
| new_symbol | 011170 | 롯데케미칼 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 011170 | 롯데케미칼 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.118129 | 0.118129 |
| new_symbol | 011170 | 롯데케미칼 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:39; L30; DD1.0; NL0.75 | 5 | 7 | 0 | 0.081624 | None |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 14 | 25 | 0 | 0.034643 | 0.034643 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.02495 | 0.02495 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L15; DD0.5; NL0.75 | 6 | 10 | 0 | 0.006159 | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:29; L15; DD0.5; NL0.2 | 11 | 18 | 0 | 0.045221 | None |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L20; DD0.5; NL0.2 | 15 | 24 | 0 | 0.032256 | None |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.233499 | 0.233499 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_failed_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 2 | 1 | 1 | 0.132555 | 0.132555 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_failed_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 1 | 2 | 0 | 0.345954 | 0.345954 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_failed_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 2 | 2 | 2 | 0.155003 | 0.155003 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_failed_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.300152 | 0.300152 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L45; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_failed_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 3 | 6 | 0 | 0.500594 | 0.500594 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_failed_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 3 | 1 | 1 | -0.004159 | -0.004159 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L30; DD1.0; NL0.2 | 4 | 8 | 0 | 0.274096 | 0.274096 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:20~14:34; L20; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.173023 | 0.173023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.5; NL0.2 | 5 | 9 | 0 | 0.170079 | 0.170079 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:44; L15; DD0.75; NL0.75 | 5 | 7 | 0 | 0.15009 | 0.15009 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_positive_not_better_keep_baseline | 13:20~13:29; L45; DD0.5; NL0.75 | 5 | 4 | 0 | 0.216991 | 0.216991 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_failed_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_failed_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 3 | 4 | 0 | 0.035562 | 0.035562 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 5 | 9 | 0 | 0.197077 | 0.197077 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L30; DD1.25; NL0.05 | 4 | 4 | 0 | 0.187659 | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 9 | 7 | 0 | 0.204062 | 0.204062 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L15; DD0.75; NL0.5 | 5 | 3 | 0 | 0.093412 | 0.093412 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L20; DD1.25; NL0.75 | 3 | 6 | 0 | 0.50417 | 0.50417 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_failed_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_failed_keep_baseline | 09:40~09:49; L15; DD1.5; NL0.35 | 4 | 6 | 1 | 0.275715 | 0.275715 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_failed_keep_baseline | 10:35~10:49; L20; DD1.25; NL0.75 | 6 | 8 | 2 | 0.261509 | 0.261509 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:25~13:54; L20; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:25~13:44; L15; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_pass_source_only_early_candidate | 09:10~09:29; L30; DD0.5; NL0.75 | 5 | 4 | 0 | 0.078435 | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 4 | 6 | 0 | 0.089397 | 0.089397 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L15; DD0.5; NL0.1 | 7 | 11 | 0 | 0.364034 | 0.364034 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | morning | holdout_failed_keep_baseline | 09:10~09:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | afternoon | holdout_failed_keep_baseline | 14:05~14:40; L30; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | midday | holdout_failed_keep_baseline | 13:15~13:44; L15; DD0.75; NL0.75 | 7 | 12 | 0 | 0.031032 | 0.031032 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | midday | holdout_failed_keep_baseline | 13:15~13:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:30~13:49; L15; DD0.5; NL0.5 | 5 | 8 | 1 | 0.048065 | 0.048065 |
| existing_symbol_logic_improvement | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L15; DD1.0; NL0.5 | 10 | 15 | 0 | 0.258526 | 0.258526 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L20; DD0.75; NL0.75 | 6 | 10 | 0 | 0.081607 | 0.081607 |

## Target-date cumulative logic attribution

- `sk_telecom_morning`: candidate-only signal `2026-09-09T09:29:00+09:00`; completed `1` leg; held `0`; EV `0.103159`%.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
