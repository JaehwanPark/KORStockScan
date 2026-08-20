# Expanded lower-price entry-spot research — 2026-08-20

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-20`; trading dates `53`; calibration `37`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `9`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `4/3`; completed legs `7/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | 0.051551 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 11 | 16 | 4 | None | 0.021986 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 12 | 0 | None | 0.051098 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | 0.00997 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 4 | 7 | 0 | 0.024641 | 0.024641 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 6 | 0 | None | -0.085156 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.075195 |
| new_symbol | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 10 | 0 | 0.10409 | 0.10409 |
| new_symbol | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.091353 | 0.091353 |
| new_symbol | 002900 | TYM | midday | holdout_pass_source_only_early_candidate | 13:15~13:44; L15; DD0.5; NL0.75 | 9 | 13 | 0 | 0.068529 | 0.036609 |
| new_symbol | 002900 | TYM | afternoon | holdout_pass_source_only_early_candidate | 14:30~14:39; L20; DD0.5; NL0.5 | 5 | 8 | 0 | 0.075091 | 0.071098 |
| new_symbol | 079160 | CJ CGV | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 9 | 16 | 0 | 0.157693 | 0.157693 |
| new_symbol | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 14 | 0 | 0.139437 | 0.139437 |
| new_symbol | 079160 | CJ CGV | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L60; DD0.75; NL0.75 | 6 | 9 | 0 | 0.13385 | 0.11689 |
| new_symbol | 079160 | CJ CGV | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:24; L20; DD0.5; NL0.35 | 5 | 9 | 0 | 0.126789 | 0.087348 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 7 | 11 | 2 | 0.207532 | 0.207532 |
| existing_symbol_time_extension | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 19 | 2 | 0.120044 | 0.120044 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 12 | 23 | 0 | 0.083575 | 0.083575 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.09347 | 0.09347 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 16 | 0 | 0.075862 | 0.075862 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 7 | 14 | 0 | 0.082743 | 0.082743 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 13 | 5 | 0.037057 | 0.037057 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.135852 | 0.135852 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 5 | 0 | 0.082905 | 0.082905 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.024802 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | 0.036267 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | 0.042425 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 7 | 10 | 0 | 0.07096 | 0.07096 |
| existing_symbol_time_extension | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 11 | 0 | 0.06155 | 0.06155 |
| existing_symbol_time_extension | 015760 | 한국전력 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.109358 | 0.109358 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.031164 | 0.031164 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 6 | 10 | 0 | 0.017815 | 0.017815 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.01838 | 0.01838 |
| existing_symbol_time_extension | 105630 | 한세실업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 4 | 6 | 1 | 0.009461 | 0.009461 |
| existing_symbol_time_extension | 105630 | 한세실업 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.012195 | 0.012195 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 2 | 3 | 0 | 0.204706 | 0.204706 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 5 | 9 | 0 | 0.403415 | 0.403415 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 7 | 13 | 0 | 0.357736 | 0.357736 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 7 | 14 | 0 | 0.362418 | 0.362418 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 5 | 10 | 0 | 0.375622 | 0.375622 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 3 | 6 | 0 | 0.268475 | 0.268475 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 11 | 19 | 3 | 0.28234 | 0.28234 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L60; DD0.5; NL0.75 | 12 | 17 | 0 | 0.068872 | 0.068872 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:24; L15; DD0.5; NL0.05 | 8 | 11 | 3 | 0.219035 | 0.212102 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 6 | 12 | 0 | 0.42383 | 0.42383 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 3 | 5 | 0 | 0.345877 | 0.345877 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L45; DD2.5; NL0.5 | 3 | 5 | 0 | 0.094388 | 0.094388 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_pass_source_only_early_candidate | 09:20~09:29; L20; DD1.75; NL0.75 | 5 | 4 | 0 | 0.29163 | 0.148168 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_pass_source_only_early_candidate | 10:15~10:34; L45; DD1.5; NL0.05 | 4 | 7 | 0 | 0.299629 | 0.063461 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L30; DD0.5; NL0.35 | 10 | 14 | 2 | 0.046213 | 0.046213 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_pass_source_only_early_candidate | 14:25~14:34; L15; DD0.75; NL0.5 | 5 | 9 | 1 | 0.217369 | 0.018026 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L20; DD1.5; NL0.2 | 2 | 3 | 1 | 0.023081 | 0.023081 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:05~14:34; L60; DD1.25; NL0.75 | 3 | 4 | 0 | 0.019763 | 0.019763 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_pass_source_only_early_candidate | 09:45~09:59; L15; DD2.0; NL0.5 | 3 | 6 | 0 | 0.246014 | 0.01254 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.75; NL0.2 | 4 | 8 | 0 | 0.261761 | 0.021722 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 6 | 0 | 0.172815 | 0.014765 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:15~09:44; L15; DD0.75; NL0.75 | 11 | 18 | 1 | 0.192259 | 0.014899 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
