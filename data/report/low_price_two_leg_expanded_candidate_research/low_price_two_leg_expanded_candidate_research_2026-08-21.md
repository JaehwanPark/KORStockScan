# Expanded lower-price entry-spot research — 2026-08-21

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-21`; trading dates `54`; calibration `38`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `14`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `5/3`; completed legs `9/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | 0.038695 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 11 | 18 | 2 | None | 0.021531 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | 0.039435 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | 0.00997 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 5 | 9 | 0 | 0.022327 | 0.022327 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 8 | 0 | None | -0.086958 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 2 | None | -0.034917 |
| new_symbol | 111770 | 영원무역 | morning | holdout_pass_source_only_early_candidate | 09:20~09:39; L20; DD0.5; NL0.5 | 13 | 22 | 0 | 0.030952 | 0.023264 |
| new_symbol | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 18 | 0 | 0.033769 | 0.033769 |
| new_symbol | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 5 | 8 | 0 | 0.027246 | 0.027246 |
| new_symbol | 111770 | 영원무역 | afternoon | holdout_pass_source_only_early_candidate | 14:30~14:40; L30; DD0.5; NL0.75 | 9 | 13 | 2 | 0.031079 | 0.030769 |
| new_symbol | 181710 | NHN | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 4 | 8 | 0 | 0.069505 | 0.069505 |
| new_symbol | 181710 | NHN | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 9 | 1 | 0.05388 | 0.05388 |
| new_symbol | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 5 | 8 | 2 | 0.068465 | 0.068465 |
| new_symbol | 181710 | NHN | afternoon | holdout_pass_source_only_early_candidate | 14:00~14:40; L15; DD0.5; NL0.75 | 10 | 17 | 0 | 0.0641 | 0.059207 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.240054 | 0.240054 |
| existing_symbol_time_extension | 475150 | SK이터닉스 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 19 | 2 | 0.13403 | 0.13403 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 12 | 23 | 0 | 0.082425 | 0.082425 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.09347 | 0.09347 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 8 | 16 | 0 | 0.069088 | 0.069088 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 7 | 14 | 0 | 0.070558 | 0.070558 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 13 | 5 | 0.037057 | 0.037057 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.135852 | 0.135852 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 5 | 0 | 0.082905 | 0.082905 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.022698 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | 0.036267 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | 0.042425 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 7 | 10 | 0 | 0.07096 | 0.07096 |
| existing_symbol_time_extension | 015760 | 한국전력 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:59; L15; DD0.75; NL0.05 | 7 | 11 | 0 | 0.069756 | 0.057205 |
| existing_symbol_time_extension | 015760 | 한국전력 | midday | holdout_pass_source_only_early_candidate | 13:30~13:49; L45; DD0.5; NL0.5 | 8 | 12 | 2 | 0.066303 | None |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 9 | 0 | 0.027881 | 0.027881 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 5 | 9 | 0 | 0.015508 | 0.015508 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.01838 | 0.01838 |
| existing_symbol_time_extension | 105630 | 한세실업 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:59; L30; DD0.75; NL0.75 | 7 | 12 | 0 | 0.015805 | 0.009558 |
| existing_symbol_time_extension | 105630 | 한세실업 | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L15; DD0.5; NL0.75 | 7 | 11 | 0 | 0.01266 | 0.012195 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 9 | 16 | 0 | 0.157693 | 0.157693 |
| existing_symbol_time_extension | 079160 | CJ CGV | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:09; L15; DD0.5; NL0.75 | 14 | 23 | 0 | 0.147307 | 0.13753 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 10 | 0 | 0.094421 | 0.094421 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.083511 | 0.083511 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 2 | 3 | 0 | 0.204706 | 0.204706 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 5 | 9 | 0 | 0.403415 | 0.403415 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 6 | 12 | 0 | 0.382242 | 0.382242 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 7 | 14 | 0 | 0.362418 | 0.362418 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 4 | 8 | 0 | 0.365771 | 0.365771 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 3 | 6 | 0 | 0.260564 | 0.260564 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 11 | 17 | 5 | 0.25161 | 0.25161 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_pass_source_only_early_candidate | 14:00~14:29; L45; DD0.75; NL0.75 | 4 | 5 | 1 | 0.245128 | 0.06925 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 8 | 11 | 3 | 0.219035 | 0.219035 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 6 | 12 | 0 | 0.477705 | 0.477705 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 3 | 5 | 0 | 0.345877 | 0.345877 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 1 | 1 | 1 | 0.256914 | 0.256914 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 5 | 4 | 0 | 0.29163 | 0.29163 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 3 | 5 | 0 | 0.265404 | 0.265404 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 4 | 3 | 4 | 0.119766 | 0.119766 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_positive_not_better_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 5 | 9 | 1 | 0.217369 | 0.217369 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:14; L45; DD1.0; NL0.75 | 6 | 10 | 2 | 0.182756 | 0.016389 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:05~14:34; L20; DD0.75; NL0.35 | 7 | 10 | 0 | 0.168029 | 0.168029 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_positive_not_better_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 3 | 6 | 0 | 0.246014 | 0.246014 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.75; NL0.2 | 3 | 6 | 0 | 0.248012 | 0.018225 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 6 | 0 | 0.172815 | 0.014765 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:15~09:44; L15; DD0.75; NL0.75 | 11 | 17 | 1 | 0.183036 | 0.014726 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:49; L60; DD0.75; NL0.75 | 7 | 10 | 0 | 0.128558 | 0.128558 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:24; L30; DD0.5; NL0.75 | 5 | 8 | 2 | 0.438457 | 0.152363 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_pass_source_only_early_candidate | 13:15~13:44; L20; DD0.5; NL0.35 | 8 | 9 | 0 | 0.209402 | 0.058991 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 6 | 9 | 0 | 0.069151 | 0.069151 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
