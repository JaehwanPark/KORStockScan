# Expanded lower-price entry-spot research — 2026-09-07

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-07`; trading dates `65`; calibration `49`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `13`.
Economic decision: same-window cost-adjusted net profit with positive EV; calibration-half signs are robustness diagnostics. HELD custody continues across date/window boundaries without invented resolution.

## Existing two-filter economic replay (source-only)

- `logic_samsung_heavy_midday`: rolling_high_drawdown_pct: hold_no_edge (-6.879999999999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.5070769300000002 KRW/day).
- `logic_samsung_heavy_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-18.15953846 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.2987692300000013 KRW/day).
- `logic_sk_eternix_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-10.565384609999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.863230770000001 KRW/day).
- `logic_mirae_asset_morning`: rolling_high_drawdown_pct: hold_no_edge (-27.36846154 KRW/day), rolling_low_proximity_pct: hold_no_edge (-9.005076920000008 KRW/day).
- `logic_jeju_semiconductor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.056615389999990384 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.235076920000012 KRW/day).
- `logic_doosan_enerbility_morning`: rolling_high_drawdown_pct: hold_no_edge (-38.70215384000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-45.93923077000001 KRW/day).
- `logic_hanwha_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-5.043230770000008 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-14.609076920000007 KRW/day).
- `logic_kakao_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.64323077 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kakao_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-11.80246154 KRW/day).
- `logic_sk_eternix_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-67.75846152999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_mirae_asset_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (37.907076929999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.05661538999999749 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.611076929999996 KRW/day), rolling_low_proximity_pct: hold_no_edge (-2.353230769999996 KRW/day).
- `logic_doosan_enerbility_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-48.660307689999996 KRW/day).
- `logic_kakao_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.6687692299999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_telecom_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.825538459999997 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-5.014923080000003 KRW/day).
- `logic_samsung_ea_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-15.583999999999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (18.024461540000004 KRW/day).
- `logic_samsung_ea_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_morning`: rolling_high_drawdown_pct: hold_no_edge (-29.096923079999996 KRW/day), rolling_low_proximity_pct: hold_no_edge (-6.133076920000001 KRW/day).
- `logic_sk_telecom_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-32.629692309999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-104.64846154 KRW/day).
- `logic_hanse_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.2978461499999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (4.996769230000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_cj_cgv_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.2864615400000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_cj_cgv_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_tym_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (1.48215384 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.8276923099999998 KRW/day).
- `logic_tym_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-0.36876923000000006 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_kepco_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.215230769999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.80476923 KRW/day).
- `logic_youngone_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.444615390000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.32200000000000095 KRW/day).
- `logic_kepco_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.4295384599999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.49384614999999954 KRW/day).
- `logic_nhn_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-32.42015385 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.238307690000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.7341538400000012 KRW/day).
- `logic_cj_cgv_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_youngone_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-35.608307690000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (-48.06138462 KRW/day).
- `logic_mirae_asset_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.774769230000004 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.484307700000002 KRW/day).
- `logic_kepco_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.5353846100000013 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0035384600000014643 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-3.562000000000001 KRW/day).
- `logic_nhn_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-39.55107691999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-3.222153849999998 KRW/day).
- `logic_sd_biosensor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sd_biosensor_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7463076900000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7389230800000002 KRW/day).
- `logic_sd_biosensor_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7378461500000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7255384600000001 KRW/day).
- `logic_doosan_enerbility_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (57.73384616 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (15.553692299999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-1.48461539 KRW/day).
- `logic_sk_telecom_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-5.290923070000002 KRW/day).
- `logic_fan_ocean_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5604615399999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.8360000000000003 KRW/day).
- `logic_fan_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.4904615299999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.668923080000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.49815385000000134 KRW/day).
- `logic_cj_cgv_morning`: source_runtime_policy_unavailable.
- `logic_fan_ocean_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.05276923 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.31646154000000015 KRW/day).
- `logic_youngone_midday`: source_runtime_policy_unavailable.
- `logic_sk_telecom_midday`: source_runtime_policy_unavailable.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `12/3`; completed legs `21/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | -0.037408 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 12 | 21 | 0 | 0.002508 | 0.002508 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 0 | None | -0.100354 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.051039 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 2 | None | -0.048848 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 14 | 27 | 0 | 0.033941 | 0.033941 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.02495 | 0.02495 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L15; DD0.5; NL0.75 | 6 | 10 | 0 | 0.012265 | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_pass_source_only_early_candidate | 09:10~09:59; L15; DD1.0; NL0.75 | 11 | 20 | 0 | 0.049923 | None |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L20; DD0.5; NL0.2 | 15 | 24 | 0 | 0.027735 | None |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_pass_source_only_early_candidate | 13:30~13:49; L15; DD0.5; NL0.5 | 5 | 8 | 1 | 0.048065 | None |
| existing_symbol_time_extension | 137310 | 에스디바이오센서 | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:40; L20; DD0.75; NL0.75 | 7 | 11 | 0 | 0.076816 | 0.090646 |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.233499 | 0.233499 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_failed_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 2 | 1 | 1 | 0.132555 | 0.132555 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_failed_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_failed_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 3 | 4 | 2 | 0.189615 | 0.189615 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_failed_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.300152 | 0.300152 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L45; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_failed_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 4 | 8 | 0 | 0.492674 | 0.492674 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_failed_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 3 | 1 | 0 | -0.004125 | -0.004125 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_pass_source_only_early_candidate | 10:15~10:34; L30; DD1.0; NL0.2 | 5 | 8 | 0 | 0.218451 | 0.142622 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:20~14:34; L20; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.173023 | 0.173023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.5; NL0.2 | 6 | 11 | 0 | 0.168514 | 0.184207 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:30~09:44; L15; DD0.75; NL0.75 | 6 | 9 | 0 | 0.154989 | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L45; DD0.5; NL0.75 | 6 | 5 | 0 | 0.225839 | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_failed_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_failed_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 4 | 6 | 0 | 0.039571 | 0.039571 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L60; DD2.0; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_pass_source_only_early_candidate | 14:30~14:39; L15; DD0.75; NL0.5 | 6 | 5 | 0 | 0.125257 | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 6 | 11 | 0 | 0.194644 | 0.194644 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:09; L15; DD0.5; NL0.35 | 10 | 8 | 0 | 0.210038 | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:45~10:54; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.442835 | 0.442835 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_failed_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_pass_source_only_early_candidate | 09:40~09:49; L15; DD1.5; NL0.35 | 3 | 5 | 0 | 0.293792 | None |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_positive_not_better_keep_baseline | 10:35~10:49; L20; DD1.25; NL0.75 | 4 | 6 | 0 | 0.28156 | 0.28156 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:25~13:54; L20; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:25~13:44; L15; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 3 | 5 | 0 | 0.102572 | 0.102572 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:14; L15; DD0.5; NL0.1 | 5 | 8 | 0 | 0.378811 | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | morning | holdout_failed_keep_baseline | 09:10~09:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | afternoon | holdout_failed_keep_baseline | 14:05~14:40; L30; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | midday | holdout_failed_keep_baseline | 13:15~13:44; L15; DD0.75; NL0.75 | 9 | 15 | 0 | 0.026569 | 0.026569 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | midday | holdout_failed_keep_baseline | 13:15~13:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |

## Target-date cumulative logic attribution

- `doosan_enerbility_late_morning`: candidate-only signal `2026-09-07T10:16:00+09:00`; completed `2` leg; held `0`; EV `0.252218`%.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
