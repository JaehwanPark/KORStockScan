# Expanded lower-price entry-spot research — 2026-08-26

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-26`; trading dates `57`; calibration `41`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `12`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `7/3`; completed legs `13/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | 0.020672 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 11 | 19 | 2 | None | 0.011365 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | 0.004624 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 12 | 0 | None | -0.002891 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 7 | 13 | 0 | 0.02143 | 0.02143 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 10 | 0 | None | -0.073883 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 4 | 2 | None | -0.051366 |
| new_symbol | 137310 | 에스디바이오센서 | morning | holdout_pass_source_only_early_candidate | 09:30~09:49; L15; DD0.75; NL0.75 | 11 | 20 | 0 | 0.10814 | 0.097068 |
| new_symbol | 137310 | 에스디바이오센서 | late_morning | holdout_pass_source_only_early_candidate | 10:40~10:59; L30; DD0.5; NL0.5 | 10 | 18 | 0 | 0.105912 | 0.073889 |
| new_symbol | 137310 | 에스디바이오센서 | midday | holdout_pass_source_only_early_candidate | 13:25~13:54; L20; DD0.75; NL0.2 | 3 | 5 | 0 | 0.099973 | 0.0 |
| new_symbol | 137310 | 에스디바이오센서 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.138983 | 0.138983 |
| new_symbol | 361610 | SK아이이테크놀로지 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 9 | 2 | None | -0.036862 |
| new_symbol | 361610 | SK아이이테크놀로지 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 13 | 24 | 0 | None | -0.060865 |
| new_symbol | 361610 | SK아이이테크놀로지 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.068031 |
| new_symbol | 361610 | SK아이이테크놀로지 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.181907 | 0.181907 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.076434 | 0.076434 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 20 | 0 | 0.065287 | 0.065287 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 7 | 13 | 0 | 0.053638 | 0.053638 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 9 | 12 | 5 | 0.039272 | 0.039272 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_pass_source_only_early_candidate | 14:10~14:29; L15; DD0.75; NL0.05 | 5 | 8 | 0 | 0.042477 | 0.031155 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 0 | None | 0.02185 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.031884 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 6 | 10 | 0 | 0.014741 | 0.014741 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 8 | 0 | 0.012993 | 0.012993 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L30; DD1.0; NL0.75 | 4 | 7 | 0 | 0.007583 | 0.006825 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 8 | 14 | 0 | 0.153517 | 0.153517 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 10 | 0 | 0.094421 | 0.094421 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 7 | 11 | 0 | 0.071297 | 0.071297 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 17 | 0 | 0.038503 | 0.038503 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 6 | 0 | 0.035935 | 0.035935 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 7 | 12 | 2 | 0.079706 | 0.079706 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 1 | 1 | 0 | 0.126901 | 0.126901 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 3 | 6 | 0 | 0.530149 | 0.530149 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 5 | 10 | 0 | 0.370044 | 0.370044 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 6 | 12 | 0 | 0.322876 | 0.322876 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 3 | 6 | 0 | 0.339205 | 0.339205 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 4 | 7 | 0 | 0.231221 | 0.231221 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 9 | 13 | 5 | 0.22943 | 0.22943 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 3 | 1 | 3 | 0.063061 | 0.063061 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 8 | 11 | 3 | 0.222041 | 0.222041 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_failed_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 5 | 10 | 0 | 0.510606 | 0.510606 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 3 | 0 | 0.291624 | 0.291624 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 1 | 1 | 1 | 0.256914 | 0.256914 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 5 | 4 | 0 | 0.219201 | 0.219201 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 4 | 7 | 0 | 0.281907 | 0.281907 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 3 | 3 | 2 | 0.157942 | 0.157942 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_positive_not_better_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 6 | 9 | 3 | 0.165522 | 0.165522 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 7 | 13 | 0 | 0.208335 | 0.208335 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_positive_not_better_keep_baseline | 14:05~14:34; L20; DD0.75; NL0.35 | 6 | 9 | 0 | 0.164489 | 0.164489 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_positive_not_better_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 2 | 4 | 0 | 0.225532 | 0.225532 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.75; NL0.2 | 3 | 6 | 0 | 0.217609 | 0.008872 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 7 | 1 | 0.201021 | 0.201021 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:15~09:44; L15; DD0.75; NL0.75 | 9 | 13 | 1 | 0.170401 | 0.170401 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:49; L60; DD0.75; NL0.75 | 6 | 8 | 0 | 0.119866 | 0.119866 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 5 | 8 | 2 | 0.438457 | 0.438457 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:44; L20; DD0.5; NL0.35 | 9 | 11 | 0 | 0.226951 | 0.226951 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 6 | 9 | 0 | 0.069151 | 0.069151 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 15 | 24 | 0 | 0.033394 | 0.033394 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L60; DD1.0; NL0.75 | 7 | 11 | 1 | 0.286361 | 0.286361 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 2 | 3 | 0 | 0.164995 | 0.164995 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 7 | 9 | 2 | 0.057664 | 0.057664 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L45; DD0.5; NL0.75 | 11 | 14 | 5 | 0.191617 | 0.191617 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:09; L15; DD0.5; NL0.35 | 9 | 12 | 1 | 0.374308 | 0.305359 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L20; DD0.75; NL0.5 | 13 | 19 | 2 | 0.283537 | 0.283537 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:19; L20; DD0.75; NL0.2 | 3 | 4 | 0 | 0.165404 | 0.155207 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L15; DD1.75; NL0.2 | 3 | 6 | 0 | 0.524857 | 0.162428 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:29; L20; DD1.0; NL0.35 | 10 | 17 | 0 | 0.315972 | 0.082711 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_pass_source_only_early_candidate | 09:35~09:59; L15; DD0.5; NL0.75 | 12 | 18 | 0 | 0.289524 | 0.067522 |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_failed_keep_baseline | 09:40~09:49; L20; DD0.5; NL0.5 | 2 | 4 | 0 | 0.059011 | 0.059011 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_pass_source_only_early_candidate | 10:30~10:49; L30; DD0.5; NL0.5 | 8 | 13 | 0 | 0.26033 | 0.047401 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
