# Expanded lower-price entry-spot research — 2026-09-10

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-10`; trading dates `68`; calibration `52`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `5`.
Economic decision: same-window cost-adjusted net profit with positive EV; calibration-half signs are robustness diagnostics. HELD custody continues across date/window boundaries without invented resolution.

## Existing two-filter economic replay (source-only)

- `logic_samsung_heavy_midday`: rolling_high_drawdown_pct: hold_no_edge (-6.57647059 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.4847058799999999 KRW/day).
- `logic_samsung_heavy_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-17.35838236 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.2414705899999987 KRW/day).
- `logic_sk_eternix_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-10.09926471 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.472205889999998 KRW/day).
- `logic_mirae_asset_morning`: rolling_high_drawdown_pct: hold_no_edge (-29.69426469999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.60764705999999 KRW/day).
- `logic_jeju_semiconductor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.05411764999999491 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.783529410000014 KRW/day).
- `logic_doosan_enerbility_morning`: rolling_high_drawdown_pct: hold_no_edge (-36.99470588 KRW/day), rolling_low_proximity_pct: hold_no_edge (-43.91250000000001 KRW/day).
- `logic_hanwha_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.820735290000016 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-13.964558820000008 KRW/day).
- `logic_kakao_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.4825 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kakao_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-11.281764710000001 KRW/day).
- `logic_sk_eternix_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-64.76911765 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_mirae_asset_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (36.23470587999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.054117650000002016 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.407647060000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-2.249411760000001 KRW/day).
- `logic_doosan_enerbility_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-21.46073530000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-18.828823530000008 KRW/day).
- `logic_kakao_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.59514706 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_telecom_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.656764710000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.793676470000001 KRW/day).
- `logic_samsung_ea_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-14.89647059 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (17.229264699999995 KRW/day).
- `logic_samsung_ea_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_morning`: rolling_high_drawdown_pct: hold_no_edge (-27.813235300000002 KRW/day), rolling_low_proximity_pct: hold_no_edge (-5.862500000000004 KRW/day).
- `logic_sk_telecom_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-11.09588235999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-111.13426471 KRW/day).
- `logic_hanse_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.28470588 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_morning`: rolling_high_drawdown_pct: hold_no_edge (-6.25132353 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.5680882300000007 KRW/day).
- `logic_cj_cgv_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.52558824 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_cj_cgv_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_tym_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (1.4167647100000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7911764699999999 KRW/day).
- `logic_tym_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-0.35250000000000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_kepco_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.3664705899999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.47205882999999993 KRW/day).
- `logic_hanse_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.3808823500000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.3077941200000005 KRW/day).
- `logic_nhn_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-30.98985294 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_youngone_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-50.47852941000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-15.35808824 KRW/day).
- `logic_hanse_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.61117647 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6576470600000004 KRW/day).
- `logic_cj_cgv_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-1.3888235299999998 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.6902941199999999 KRW/day).
- `logic_kepco_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-40.52235294 KRW/day).
- `logic_youngone_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-19.107499999999987 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.507205879999987 KRW/day).
- `logic_mirae_asset_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.696470590000004 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.021764700000006 KRW/day).
- `logic_kepco_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.37941176 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-21.89514706 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.730882350000002 KRW/day).
- `logic_nhn_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-37.80617647 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-3.0799999999999983 KRW/day).
- `logic_sd_biosensor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sd_biosensor_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7133823500000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7063235300000001 KRW/day).
- `logic_sd_biosensor_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7052941100000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.69352941 KRW/day).
- `logic_doosan_enerbility_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (55.1867647 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (14.8675 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-1.41911764 KRW/day).
- `logic_sk_telecom_morning`: rolling_high_drawdown_pct: hold_no_edge (-2.828088230000006 KRW/day), rolling_low_proximity_pct: hold_no_edge (-11.089117639999998 KRW/day).
- `logic_fan_ocean_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5357352999999998 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.8464705899999998 KRW/day).
- `logic_fan_ocean_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.88897059 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6169117699999997 KRW/day).
- `logic_samsung_heavy_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.462941179999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.47617646999999863 KRW/day).
- `logic_cj_cgv_morning`: source_runtime_policy_unavailable.
- `logic_fan_ocean_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-2.91808824 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.30249999999999977 KRW/day).
- `logic_youngone_midday`: source_runtime_policy_unavailable.
- `logic_sk_telecom_midday`: source_runtime_policy_unavailable.
- `logic_nhn_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-5.9920588299999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.8747058899999995 KRW/day).
- `logic_tym_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.469852939999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-21.56 KRW/day).
- `logic_sd_biosensor_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-1.8947058900000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_lotte_chemical_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-8.109264710000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.656911770000008 KRW/day).
- `logic_lotte_chemical_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-20.51970589 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.15558824000000016 KRW/day).
- `logic_tym_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5994117700000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.25191177 KRW/day).

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `9/3`; completed legs `16/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 8 | 15 | 0 | None | -0.044508 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 9 | 16 | 0 | 0.003815 | 0.003815 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 8 | 0 | None | -0.095087 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 2 | None | 0.0 |
| new_symbol | 006880 | 신송홀딩스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 006880 | 신송홀딩스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.022208 |
| new_symbol | 006880 | 신송홀딩스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 1 | 0 | None | -0.009853 |
| new_symbol | 006880 | 신송홀딩스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 108320 | LX세미콘 | morning | holdout_pass_source_only_early_candidate | 09:45~09:54; L15; DD1.25; NL0.75 | 3 | 4 | 0 | 0.028954 | None |
| new_symbol | 108320 | LX세미콘 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 108320 | LX세미콘 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 108320 | LX세미콘 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.050899 | 0.050899 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 15 | 27 | 0 | 0.035408 | 0.035408 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.02495 | 0.02495 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L15; DD0.5; NL0.75 | 5 | 9 | 0 | 0.004273 | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L20; DD0.5; NL0.2 | 15 | 24 | 0 | 0.033631 | None |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 011170 | 롯데케미칼 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 011170 | 롯데케미칼 | midday | holdout_pass_source_only_early_candidate | 13:15~13:34; L45; DD0.75; NL0.75 | 3 | 5 | 0 | 0.090828 | 0.118129 |
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
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L30; DD1.0; NL0.2 | 5 | 9 | 0 | 0.239086 | 0.239086 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:20~14:34; L20; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.173023 | 0.173023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.5; NL0.2 | 5 | 9 | 0 | 0.170079 | 0.170079 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:44; L15; DD0.75; NL0.75 | 4 | 6 | 0 | 0.163426 | 0.163426 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:29; L45; DD0.5; NL0.75 | 4 | 3 | 0 | 0.201244 | 0.201244 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_failed_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_failed_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 3 | 4 | 0 | 0.035562 | 0.035562 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L15; DD0.75; NL0.5 | 5 | 3 | 0 | 0.093412 | 0.093412 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 5 | 9 | 0 | 0.197077 | 0.197077 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 9 | 7 | 0 | 0.204062 | 0.204062 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:59; L30; DD1.25; NL0.05 | 5 | 6 | 0 | 0.226108 | 0.226108 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L20; DD1.25; NL0.75 | 3 | 6 | 0 | 0.50417 | 0.50417 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_failed_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_failed_keep_baseline | 09:40~09:49; L15; DD1.5; NL0.35 | 4 | 6 | 1 | 0.275715 | 0.275715 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_positive_not_better_keep_baseline | 10:35~10:49; L20; DD1.25; NL0.75 | 6 | 8 | 2 | 0.261509 | 0.261509 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:25~13:54; L20; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:25~13:44; L15; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 6 | 5 | 0 | 0.082984 | 0.082984 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 4 | 6 | 0 | 0.089397 | 0.089397 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L15; DD0.5; NL0.1 | 7 | 11 | 0 | 0.364034 | 0.364034 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | morning | holdout_pass_source_only_early_candidate | 09:30~09:39; L20; DD1.75; NL0.75 | 4 | 6 | 2 | 0.394243 | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | afternoon | holdout_failed_keep_baseline | 14:05~14:40; L30; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | midday | holdout_failed_keep_baseline | 13:15~13:44; L15; DD0.75; NL0.75 | 8 | 12 | 0 | 0.027331 | 0.027331 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | midday | holdout_failed_keep_baseline | 13:15~13:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:30~13:49; L15; DD0.5; NL0.5 | 5 | 8 | 1 | 0.048065 | 0.048065 |
| existing_symbol_logic_improvement | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L15; DD1.0; NL0.5 | 10 | 14 | 0 | 0.240345 | 0.240345 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L20; DD0.75; NL0.75 | 5 | 8 | 0 | 0.076499 | 0.076499 |
| existing_symbol_logic_improvement | 011170 | 롯데케미칼 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:59; L20; DD0.5; NL0.75 | 12 | 18 | 2 | 0.091565 | 0.091565 |
| existing_symbol_logic_improvement | 011170 | 롯데케미칼 | afternoon | holdout_pass_source_only_early_candidate | 14:25~14:34; L15; DD0.5; NL0.05 | 6 | 6 | 1 | 0.238472 | 0.081624 |
| existing_symbol_logic_improvement | 002900 | TYM | late_morning | holdout_failed_keep_baseline | 10:00~10:29; L15; DD0.5; NL0.2 | 10 | 16 | 0 | 0.043568 | 0.043568 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
