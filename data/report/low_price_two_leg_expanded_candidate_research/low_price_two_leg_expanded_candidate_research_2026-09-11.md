# Expanded lower-price entry-spot research — 2026-09-11

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-11`; trading dates `69`; calibration `53`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `4`.
Economic decision: same-window cost-adjusted net profit with positive EV; calibration-half signs are robustness diagnostics. HELD custody continues across date/window boundaries without invented resolution.

## Existing two-filter economic replay (source-only)

- `logic_samsung_heavy_midday`: rolling_high_drawdown_pct: hold_no_edge (-6.481159419999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.4776811599999995 KRW/day).
- `logic_samsung_heavy_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-17.1068116 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.223478270000001 KRW/day).
- `logic_sk_eternix_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-9.95289855 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.349420289999998 KRW/day).
- `logic_mirae_asset_morning`: rolling_high_drawdown_pct: hold_no_edge (-29.26391303999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.482898550000002 KRW/day).
- `logic_jeju_semiconductor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.053333329999986745 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.641739130000005 KRW/day).
- `logic_doosan_enerbility_morning`: rolling_high_drawdown_pct: hold_no_edge (-36.45855071999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-43.27608695999999 KRW/day).
- `logic_hanwha_ocean_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.75086957000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-13.762173910000001 KRW/day).
- `logic_kakao_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.43202899 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kakao_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-11.11826087 KRW/day).
- `logic_sk_eternix_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-63.830434780000004 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_mirae_asset_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (35.709565219999995 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_eternix_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.053333330000000956 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_heavy_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.343768110000006 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-2.216811590000006 KRW/day).
- `logic_doosan_enerbility_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-21.14971015000002 KRW/day), rolling_low_proximity_pct: hold_no_edge (-18.55594203000001 KRW/day).
- `logic_kakao_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.57202898 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sk_telecom_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (3.6037681100000007 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.724202900000002 KRW/day).
- `logic_samsung_ea_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-14.680579709999996 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (16.979565209999997 KRW/day).
- `logic_samsung_ea_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_morning`: rolling_high_drawdown_pct: hold_no_edge (-27.41014493 KRW/day), rolling_low_proximity_pct: hold_no_edge (-5.777536230000003 KRW/day).
- `logic_sk_telecom_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-10.935072460000015 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-109.52362319000001 KRW/day).
- `logic_hanse_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.28057971000000004 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_hanse_morning`: rolling_high_drawdown_pct: hold_no_edge (-6.160724640000001 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.5598550800000002 KRW/day).
- `logic_cj_cgv_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.46 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_cj_cgv_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_tym_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (1.3962318800000002 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.7797101499999999 KRW/day).
- `logic_tym_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-0.34753623 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_nhn_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-30.54072464 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-39.93507247 KRW/day).
- `logic_hanse_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.5443478200000005 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.6336231899999998 KRW/day).
- `logic_hanse_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.3608695600000011 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.30333333000000096 KRW/day).
- `logic_youngone_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-49.74695652999999 KRW/day), rolling_low_proximity_pct: hold_no_edge (-15.13550724999999 KRW/day).
- `logic_youngone_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_kepco_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.3466666700000003 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.4652174000000002 KRW/day).
- `logic_cj_cgv_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-1.3686956500000003 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.6802898500000003 KRW/day).
- `logic_sk_eternix_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-18.830579709999995 KRW/day), rolling_low_proximity_pct: hold_no_edge (-8.38391304999999 KRW/day).
- `logic_mirae_asset_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-1.6718840599999965 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-9.876521740000001 KRW/day).
- `logic_kepco_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-3.330434780000001 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_nhn_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-21.57782608 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-8.604347820000001 KRW/day).
- `logic_nhn_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-37.25826087 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-3.0353623200000044 KRW/day).
- `logic_sd_biosensor_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_sd_biosensor_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.7030434799999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.6960869600000001 KRW/day).
- `logic_sd_biosensor_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-0.69507246 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.6834782599999998 KRW/day).
- `logic_doosan_enerbility_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (54.386956520000005 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (0.0 KRW/day).
- `logic_samsung_ea_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (14.65202899 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-1.3985507199999998 KRW/day).
- `logic_sk_telecom_morning`: rolling_high_drawdown_pct: hold_no_edge (-2.7871014499999944 KRW/day), rolling_low_proximity_pct: hold_no_edge (-10.928405799999993 KRW/day).
- `logic_fan_ocean_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.5279710199999998 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.81971015 KRW/day).
- `logic_fan_ocean_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.81811594 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.5934782599999995 KRW/day).
- `logic_samsung_heavy_late_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-4.398260869999998 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.4692753599999975 KRW/day).
- `logic_cj_cgv_morning`: source_runtime_policy_unavailable.
- `logic_fan_ocean_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-2.8757971 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.2981159400000002 KRW/day).
- `logic_youngone_midday`: source_runtime_policy_unavailable.
- `logic_sk_telecom_midday`: source_runtime_policy_unavailable.
- `logic_nhn_midday`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-5.905217389999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-0.8620289899999989 KRW/day).
- `logic_tym_morning`: rolling_high_drawdown_pct: hold_no_edge (-4.40507247 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-21.24753624 KRW/day).
- `logic_sd_biosensor_afternoon`: rolling_high_drawdown_pct: hold_no_edge (-1.8672463800000005 KRW/day), rolling_low_proximity_pct: hold_no_edge (0.0 KRW/day).
- `logic_lotte_chemical_morning`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-7.991739129999999 KRW/day), rolling_low_proximity_pct: hold_source_gap_external_custody_resolution (-4.589420290000007 KRW/day).
- `logic_lotte_chemical_afternoon`: rolling_high_drawdown_pct: hold_source_gap_external_custody_resolution (-48.01565218 KRW/day).
- `logic_tym_late_morning`: rolling_high_drawdown_pct: hold_no_edge (-0.59072463 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.2337681100000002 KRW/day).
- `logic_lotte_chemical_midday`: rolling_high_drawdown_pct: hold_no_edge (-16.71753623 KRW/day), rolling_low_proximity_pct: hold_no_edge (-1.220434779999998 KRW/day).
- `logic_lx_semicon_morning`: rolling_high_drawdown_pct: hold_no_edge (-3.4710145 KRW/day), rolling_low_proximity_pct: hold_no_edge (-0.06594203000000043 KRW/day).

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `8/3`; completed legs `14/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 9 | 17 | 0 | None | -0.044815 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 8 | 14 | 0 | 0.004594 | 0.004594 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 6 | 0 | None | -0.089577 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 0 | 2 | None | 0.0 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 14 | 25 | 0 | 0.035534 | 0.035534 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.02495 | 0.02495 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29; L15; DD0.5; NL0.75 | 5 | 9 | 0 | 0.004273 | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:59; L20; DD0.5; NL0.2 | 15 | 24 | 0 | 0.034612 | None |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 011170 | 롯데케미칼 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 108320 | LX세미콘 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 108320 | LX세미콘 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 108320 | LX세미콘 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.050899 | 0.050899 |
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
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_pass_source_only_early_candidate | 09:50~09:59; L15; DD1.5; NL0.35 | 6 | 7 | 0 | 0.312936 | 0.550488 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_failed_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 3 | 1 | 1 | -0.004159 | -0.004159 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L30; DD1.0; NL0.2 | 5 | 9 | 0 | 0.239086 | 0.239086 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:20~14:34; L20; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.173023 | 0.173023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.5; NL0.2 | 4 | 8 | 0 | 0.190389 | 0.190389 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:44; L15; DD0.75; NL0.75 | 3 | 4 | 0 | 0.148357 | 0.148357 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:29; L45; DD0.5; NL0.75 | 5 | 3 | 0 | 0.159403 | 0.159403 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_failed_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_failed_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 4 | 6 | 0 | 0.04053 | 0.04053 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L15; DD0.75; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:59; L30; DD1.25; NL0.05 | 5 | 6 | 0 | 0.226108 | 0.226108 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 4 | 8 | 0 | 0.219691 | 0.219691 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L15; DD0.75; NL0.5 | 4 | 2 | 0 | 0.077791 | 0.077791 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 8 | 7 | 0 | 0.228539 | 0.228539 |
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
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 6 | 5 | 0 | 0.082984 | 0.082984 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 4 | 6 | 0 | 0.089397 | 0.089397 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L15; DD0.5; NL0.1 | 7 | 11 | 0 | 0.364034 | 0.364034 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 079160 | CJ CGV | morning | holdout_pass_source_only_early_candidate | 09:30~09:39; L20; DD1.75; NL0.75 | 4 | 6 | 2 | 0.394243 | None |
| existing_symbol_logic_improvement | 028670 | 팬오션 | afternoon | holdout_failed_keep_baseline | 14:05~14:40; L30; DD0.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 111770 | 영원무역 | midday | holdout_failed_keep_baseline | 13:15~13:44; L15; DD0.75; NL0.75 | 7 | 11 | 0 | 0.02873 | 0.02873 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | midday | holdout_failed_keep_baseline | 13:15~13:24; L15; DD0.5; NL0.05 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:30~13:49; L15; DD0.5; NL0.5 | 4 | 6 | 1 | 0.049021 | 0.049021 |
| existing_symbol_logic_improvement | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L15; DD1.0; NL0.5 | 9 | 13 | 0 | 0.24816 | 0.24816 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L20; DD0.75; NL0.75 | 5 | 8 | 0 | 0.076499 | 0.076499 |
| existing_symbol_logic_improvement | 011170 | 롯데케미칼 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:59; L20; DD0.5; NL0.75 | 11 | 16 | 2 | 0.087805 | 0.087805 |
| existing_symbol_logic_improvement | 011170 | 롯데케미칼 | afternoon | holdout_positive_not_better_keep_baseline | 14:25~14:34; L15; DD0.5; NL0.05 | 5 | 4 | 1 | 0.187793 | 0.187793 |
| existing_symbol_logic_improvement | 002900 | TYM | late_morning | holdout_failed_keep_baseline | 10:00~10:29; L15; DD0.5; NL0.2 | 9 | 15 | 0 | 0.045126 | 0.045126 |
| existing_symbol_logic_improvement | 011170 | 롯데케미칼 | midday | holdout_failed_keep_baseline | 13:15~13:34; L45; DD0.75; NL0.75 | 3 | 5 | 0 | 0.090828 | 0.090828 |
| existing_symbol_logic_improvement | 108320 | LX세미콘 | morning | holdout_pass_source_only_early_candidate | 09:45~09:54; L15; DD1.25; NL0.75 | 3 | 4 | 0 | 0.211979 | 0.028954 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
