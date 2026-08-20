# Expanded lower-price entry-spot research — 2026-08-19

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-19`; trading dates `52`; calibration `36`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `11`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `4/3`; completed legs `7/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 8 | 15 | 0 | None | 0.052901 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 11 | 17 | 4 | None | 0.028243 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 2 | None | 0.044291 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.019066 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 4 | 7 | 0 | 0.037521 | 0.037521 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | -0.084024 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.075195 |
| new_symbol | 000430 | 대원강업 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 000430 | 대원강업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.039377 | 0.039377 |
| new_symbol | 000430 | 대원강업 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 000430 | 대원강업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| new_symbol | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:15~09:44; L15; DD0.75; NL0.75 | 11 | 18 | 0 | 0.013945 | 0.007919 |
| new_symbol | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 3 | 5 | 1 | 0.008897 | 0.008897 |
| new_symbol | 105630 | 한세실업 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.012195 | 0.012195 |
| new_symbol | 105630 | 한세실업 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:29; L30; DD0.5; NL0.75 | 5 | 10 | 0 | 0.015773 | None |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 13 | 2 | 0.21578 | 0.21578 |
| existing_symbol_time_extension | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 18 | 2 | 0.126515 | 0.126515 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 12 | 23 | 0 | 0.083575 | 0.083575 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.083723 | 0.083723 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 15 | 0 | 0.07507 | 0.07507 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 8 | 16 | 0 | 0.086533 | 0.086533 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 13 | 5 | 0.041031 | 0.041031 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.121802 | 0.121802 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.089583 | 0.089583 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | 0.027048 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 6 | 0 | None | 0.039091 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 5 | 0 | None | 0.036131 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 8 | 12 | 0 | 0.073655 | 0.073655 |
| existing_symbol_time_extension | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 11 | 0 | 0.06155 | 0.06155 |
| existing_symbol_time_extension | 015760 | 한국전력 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.109358 | 0.109358 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 7 | 13 | 0 | 0.031807 | 0.031807 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:59; L60; DD1.25; NL0.5 | 8 | 15 | 0 | 0.023942 | 0.021465 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 5 | 8 | 0 | 0.020599 | 0.020599 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.024509 | 0.024509 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 2 | 3 | 0 | 0.204706 | 0.204706 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 1 | 0 | 0.142892 | 0.142892 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 5 | 9 | 0 | 0.403415 | 0.403415 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 8 | 15 | 0 | 0.361792 | 0.361792 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 7 | 14 | 0 | 0.362418 | 0.362418 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 5 | 10 | 0 | 0.375622 | 0.375622 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 3 | 6 | 0 | 0.268475 | 0.268475 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 12 | 20 | 4 | 0.274014 | 0.274014 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L60; DD0.5; NL0.75 | 11 | 16 | 0 | 0.069863 | 0.069863 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:24; L15; DD0.5; NL0.05 | 8 | 11 | 3 | 0.219035 | 0.212102 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 5 | 10 | 0 | 0.418119 | 0.418119 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 4 | 7 | 0 | 0.361583 | 0.361583 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:40; L15; DD2.0; NL0.5 | 3 | 4 | 1 | 0.212074 | 0.073071 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_pass_source_only_early_candidate | 09:20~09:29; L20; DD1.75; NL0.75 | 6 | 4 | 0 | 0.243288 | 0.231919 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_pass_source_only_early_candidate | 10:15~10:34; L45; DD1.5; NL0.05 | 4 | 7 | 0 | 0.299629 | 0.071079 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_pass_source_only_early_candidate | 13:20~13:39; L15; DD0.5; NL0.2 | 5 | 7 | 2 | 0.239137 | 0.051416 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_pass_source_only_early_candidate | 14:25~14:34; L20; DD0.5; NL0.75 | 11 | 18 | 3 | 0.214955 | 0.020961 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L20; DD1.5; NL0.2 | 2 | 3 | 1 | 0.023081 | 0.023081 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_pass_source_only_early_candidate | 14:05~14:34; L20; DD0.75; NL0.35 | 8 | 11 | 2 | 0.16812 | 0.017936 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_pass_source_only_early_candidate | 09:45~09:59; L15; DD1.75; NL0.5 | 4 | 7 | 0 | 0.214612 | 0.01575 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
