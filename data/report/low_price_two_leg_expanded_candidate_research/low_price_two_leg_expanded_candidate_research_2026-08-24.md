# Expanded lower-price entry-spot research — 2026-08-24

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-24`; trading dates `55`; calibration `39`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `12`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `6/3`; completed legs `11/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.027911 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 12 | 20 | 2 | None | 0.018684 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | 0.017415 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | 0.00026 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 6 | 11 | 0 | 0.020856 | 0.020856 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | -0.088486 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 2 | None | -0.034917 |
| new_symbol | 023530 | 롯데쇼핑 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 9 | 15 | 1 | None | -0.00721 |
| new_symbol | 023530 | 롯데쇼핑 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 9 | 14 | 0 | None | -0.006392 |
| new_symbol | 023530 | 롯데쇼핑 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.021029 |
| new_symbol | 023530 | 롯데쇼핑 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | -0.015171 |
| new_symbol | 005950 | 이수화학 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 8 | 12 | 2 | None | -0.041107 |
| new_symbol | 005950 | 이수화학 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 13 | 24 | 2 | None | -0.048685 |
| new_symbol | 005950 | 이수화학 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 0 | None | -0.054145 |
| new_symbol | 005950 | 이수화학 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 12 | 0 | None | -0.054932 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.240054 | 0.240054 |
| existing_symbol_time_extension | 475150 | SK이터닉스 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L15; DD1.5; NL0.2 | 4 | 8 | 0 | 0.133532 | 0.1302 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:59; L20; DD0.75; NL0.75 | 16 | 32 | 0 | 0.084647 | 0.075809 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.076434 | 0.076434 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 18 | 0 | 0.068516 | 0.068516 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 6 | 12 | 0 | 0.056959 | 0.056959 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 12 | 5 | 0.039442 | 0.039442 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 3 | 0 | 0.061326 | 0.061326 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.022698 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.031884 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 015760 | 한국전력 | morning | holdout_pass_source_only_early_candidate | 09:35~09:59; L15; DD0.5; NL0.5 | 12 | 18 | 0 | 0.070684 | 0.065067 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 6 | 10 | 0 | 0.021889 | 0.021889 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 8 | 0 | 0.012993 | 0.012993 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.006825 | 0.006825 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 9 | 16 | 0 | 0.157693 | 0.157693 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 10 | 0 | 0.094421 | 0.094421 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.083511 | 0.083511 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 18 | 0 | 0.038118 | 0.038118 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 6 | 0 | 0.027538 | 0.027538 |
| existing_symbol_time_extension | 181710 | NHN | morning | holdout_pass_source_only_early_candidate | 09:40~09:49; L20; DD0.5; NL0.5 | 4 | 8 | 0 | 0.066064 | 0.065252 |
| existing_symbol_time_extension | 181710 | NHN | late_morning | holdout_pass_source_only_early_candidate | 10:30~10:49; L30; DD0.5; NL0.5 | 7 | 12 | 0 | 0.045007 | 0.04374 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 6 | 10 | 2 | 0.074462 | 0.074462 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 1 | 1 | 0 | 0.126901 | 0.126901 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 5 | 9 | 0 | 0.403415 | 0.403415 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 5 | 10 | 0 | 0.370044 | 0.370044 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 6 | 12 | 0 | 0.338962 | 0.338962 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 3 | 6 | 0 | 0.339205 | 0.339205 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 3 | 6 | 0 | 0.260564 | 0.260564 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 10 | 15 | 5 | 0.241264 | 0.241264 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 3 | 3 | 1 | 0.19294 | 0.19294 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 9 | 13 | 3 | 0.233254 | 0.233254 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 5 | 10 | 0 | 0.510606 | 0.510606 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 3 | 0 | 0.291624 | 0.291624 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 1 | 1 | 1 | 0.256914 | 0.256914 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 5 | 4 | 0 | 0.29163 | 0.29163 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 3 | 5 | 0 | 0.265404 | 0.265404 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 4 | 3 | 4 | 0.119766 | 0.119766 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_positive_not_better_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 6 | 9 | 3 | 0.176901 | 0.176901 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 7 | 11 | 2 | 0.174668 | 0.174668 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:05~14:34; L20; DD0.75; NL0.35 | 6 | 8 | 0 | 0.150604 | 0.150604 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_positive_not_better_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 2 | 4 | 0 | 0.225532 | 0.225532 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.75; NL0.2 | 3 | 6 | 0 | 0.248012 | 0.018225 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 7 | 1 | 0.201021 | 0.174018 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:15~09:44; L15; DD0.75; NL0.75 | 10 | 15 | 1 | 0.17776 | 0.17776 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:49; L60; DD0.75; NL0.75 | 6 | 8 | 0 | 0.119866 | 0.119866 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 5 | 8 | 2 | 0.438457 | 0.438457 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:44; L20; DD0.5; NL0.35 | 8 | 9 | 0 | 0.209402 | 0.209402 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 6 | 9 | 0 | 0.069151 | 0.069151 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L45; DD0.5; NL0.75 | 3 | 4 | 0 | 0.151064 | 0.012923 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:59; L20; DD0.75; NL0.35 | 5 | 8 | 0 | 0.185233 | 0.015805 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 14 | 23 | 0 | 0.031161 | 0.031161 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:09; L45; DD1.0; NL0.75 | 10 | 12 | 2 | 0.335324 | 0.146883 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:59; L20; DD0.75; NL0.5 | 12 | 16 | 2 | 0.258428 | 0.069756 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_pass_source_only_early_candidate | 14:00~14:40; L60; DD1.0; NL0.75 | 7 | 10 | 1 | 0.254477 | 0.054521 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 8 | 12 | 2 | 0.066303 | 0.066303 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_pass_source_only_early_candidate | 14:30~14:39; L45; DD0.5; NL0.75 | 9 | 12 | 3 | 0.19717 | 0.035428 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
