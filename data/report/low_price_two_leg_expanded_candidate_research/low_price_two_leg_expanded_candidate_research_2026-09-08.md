# Expanded lower-price entry-spot research — 2026-09-08

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-08`; trading dates `66`; calibration `50`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `4`.
Economic decision: same-window cost-adjusted net profit with positive EV; calibration-half signs are robustness diagnostics. HELD custody continues across date/window boundaries without invented resolution.

## Existing two-filter economic replay (source-only)

- `logic_samsung_heavy_midday`: rolling_high_drawdown_pct: hold_no_edge (-6.7757575800000005 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.4993939400000009 KRW/day).
- `logic_samsung_heavy_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-17.88439394 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.2790909099999972 KRW/day).
- `logic_sk_eternix_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-10.405303029999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.728939400000002 KRW/day).
- `logic_mirae_asset_morning`: rolling_high_drawdown_pct: hold_no_edge (-30.59409090999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.868484839999994 KRW/day).
- `logic_jeju_semiconductor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.05575756999999726 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.080000000000013 KRW/day).
- `logic_doosan_enerbility_morning`: rolling_high_drawdown_pct: hold_no_edge (-38.115757570000014 KRW/day), rolling_low_proximity_pct: hold_no_edge (-45.24318182000002 KRW/day).
- `logic_hanwha_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.966818180000018 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-14.387727270000028 KRW/day).
- `logic_kakao_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.5880303 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kakao_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-11.623636359999999 KRW/day).
- `logic_sk_eternix_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-66.73181818 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_mirae_asset_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (37.33272727000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.055757570000004364 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.541212119999997 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-2.317575759999997 KRW/day).
- `logic_doosan_enerbility_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-22.114545460000016 KRW/day), rolling_low_proximity_pct: hold_no_edge (-19.402878790000017 KRW/day).
- `logic_kakao_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.64348485 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_telecom_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.7675757500000024 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.938939399999999 KRW/day).
- `logic_samsung_ea_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-15.347878790000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (17.75136363 KRW/day).
- `logic_samsung_ea_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_morning`: rolling_high_drawdown_pct: hold_no_edge (-28.656060609999997 KRW/day), rolling_low_proximity_pct: hold_no_edge (-6.040151520000002 KRW/day).
- `logic_sk_telecom_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-11.432121210000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-114.50196969000001 KRW/day).
- `logic_hanse_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.29333332999999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_morning`: rolling_high_drawdown_pct: hold_no_edge (-6.440757579999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.5853030299999986 KRW/day).
- `logic_cj_cgv_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.6627272699999995 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_cj_cgv_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_tym_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (1.4596969699999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.8151515200000001 KRW/day).
- `logic_tym_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-0.3631818200000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_youngone_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-31.92893939 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.750909089999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.7078787899999988 KRW/day).
- `logic_youngone_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-52.008181820000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (-15.82348485 KRW/day).
- `logic_kepco_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.4078787899999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.4863636299999996 KRW/day).
- `logic_kepco_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.1665151499999986 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.65621212 KRW/day).
- `logic_hanse_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.422727270000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.3171212099999998 KRW/day).
- `logic_cj_cgv_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-1.430909090000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.7112121200000008 KRW/day).
- `logic_sk_eternix_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-35.068787869999994 KRW/day), rolling_low_proximity_pct: hold_no_edge (-47.33318181 KRW/day).
- `logic_mirae_asset_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.7478787799999935 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-10.325454539999996 KRW/day).
- `logic_kepco_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.4818181799999977 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_morning`: rolling_high_drawdown_pct: hold_no_edge (-22.558636370000002 KRW/day), rolling_low_proximity_pct: hold_no_edge (-5.05015152 KRW/day).
- `logic_nhn_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-38.95181819 KRW/day), rolling_low_proximity_pct: hold_no_edge (-3.1733333399999992 KRW/day).
- `logic_sd_biosensor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sd_biosensor_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7349999999999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7277272799999999 KRW/day).
- `logic_sd_biosensor_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7266666699999997 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7145454599999996 KRW/day).
- `logic_doosan_enerbility_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (56.85909091 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (15.3180303 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-1.4621212100000003 KRW/day).
- `logic_sk_telecom_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-5.210757569999998 KRW/day).
- `logic_fan_ocean_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5519696999999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.8081818200000002 KRW/day).
- `logic_fan_ocean_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-5.03727273 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6660606100000006 KRW/day).
- `logic_samsung_heavy_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.598181820000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.49060606000000107 KRW/day).
- `logic_cj_cgv_morning`: source_runtime_policy_unavailable.
- `logic_fan_ocean_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.0065151500000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.31166667000000015 KRW/day).
- `logic_youngone_midday`: source_runtime_policy_unavailable.
- `logic_sk_telecom_midday`: source_runtime_policy_unavailable.
- `logic_nhn_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-6.173636369999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.9012121200000003 KRW/day).
- `logic_tym_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.6534848499999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.18545454000000028 KRW/day).
- `logic_sd_biosensor_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-1.9521212200000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `11/3`; completed legs `19/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | -0.043277 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 11 | 19 | 0 | 0.001658 | 0.001658 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 10 | 0 | None | -0.099212 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 0 | None | 0.0 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 2 | None | 0.0 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 14 | 27 | 0 | 0.035349 | 0.035349 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.02495 | 0.02495 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L15; DD0.5; NL0.75 | 6 | 10 | 0 | 0.012265 | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L20; DD0.5; NL0.2 | 15 | 24 | 0 | 0.029964 | None |
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
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.5; NL0.2 | 6 | 11 | 0 | 0.168514 | 0.168514 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:44; L15; DD0.75; NL0.75 | 6 | 9 | 0 | 0.154989 | 0.154989 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_positive_not_better_keep_baseline | 13:20~13:29; L45; DD0.5; NL0.75 | 6 | 5 | 0 | 0.225839 | 0.225839 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_failed_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_failed_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 4 | 6 | 0 | 0.039571 | 0.039571 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 6 | 11 | 0 | 0.193863 | 0.193863 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_positive_not_better_keep_baseline | 14:30~14:39; L15; DD0.75; NL0.5 | 6 | 5 | 0 | 0.125257 | 0.125257 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L60; DD2.0; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 9 | 7 | 0 | 0.204062 | 0.204062 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L20; DD1.25; NL0.75 | 4 | 8 | 0 | 0.487811 | 0.442835 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_failed_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_positive_not_better_keep_baseline | 09:40~09:49; L15; DD1.5; NL0.35 | 3 | 5 | 0 | 0.293792 | 0.293792 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_positive_not_better_keep_baseline | 10:35~10:49; L20; DD1.25; NL0.75 | 5 | 8 | 0 | 0.309308 | 0.309308 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:25~13:54; L20; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:25~13:44; L15; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 3 | 5 | 0 | 0.102572 | 0.102572 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L15; DD0.5; NL0.1 | 6 | 9 | 0 | 0.350589 | 0.350589 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | morning | holdout_failed_keep_baseline | 09:10~09:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | afternoon | holdout_failed_keep_baseline | 14:05~14:40; L30; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | midday | holdout_failed_keep_baseline | 13:15~13:44; L15; DD0.75; NL0.75 | 8 | 14 | 0 | 0.029855 | 0.029855 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | midday | holdout_failed_keep_baseline | 13:15~13:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:30~13:49; L15; DD0.5; NL0.5 | 5 | 8 | 1 | 0.048065 | 0.048065 |
| existing_symbol_logic_improvement | 002900 | TYM | morning | holdout_pass_source_only_early_candidate | 09:10~09:59; L15; DD1.0; NL0.5 | 11 | 17 | 0 | 0.264592 | 0.050906 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L20; DD0.75; NL0.75 | 7 | 11 | 0 | 0.076816 | 0.076816 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
