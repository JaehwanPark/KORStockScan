# Expanded lower-price entry-spot research — 2026-08-18

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-18`; trading dates `51`; calibration `35`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `14`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `3/3`; completed legs `5/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 8 | 15 | 0 | None | 0.052901 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 12 | 19 | 4 | None | 0.02865 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 10 | 2 | None | 0.057441 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | 0.026338 |
| new_symbol | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 7 | 13 | 0 | 0.031807 | 0.031807 |
| new_symbol | 017670 | SK텔레콤 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 19 | 0 | 0.023005 | 0.023005 |
| new_symbol | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 6 | 0 | 0.025808 | 0.025808 |
| new_symbol | 017670 | SK텔레콤 | afternoon | holdout_pass_source_only_early_candidate | 14:25~14:34; L15; DD0.75; NL0.2 | 3 | 5 | 0 | 0.027635 | 0.013653 |
| new_symbol | 028050 | 삼성E&A | morning | holdout_pass_source_only_early_candidate | 09:45~09:59; L15; DD1.25; NL0.5 | 7 | 14 | 0 | 0.01507 | 0.013452 |
| new_symbol | 028050 | 삼성E&A | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:14; L20; DD1.5; NL0.2 | 3 | 5 | 1 | 0.020086 | 0.013754 |
| new_symbol | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.024509 | 0.024509 |
| new_symbol | 028050 | 삼성E&A | afternoon | holdout_pass_source_only_early_candidate | 14:05~14:34; L60; DD1.25; NL0.75 | 4 | 5 | 1 | 0.017936 | 0.014114 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 3 | 5 | 0 | 0.04376 | 0.04376 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.077863 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.076429 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | -0.075195 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | morning | holdout_pass_source_only_early_candidate | 09:20~09:29; L20; DD0.5; NL0.5 | 10 | 17 | 0 | 0.225639 | 0.223344 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 15 | 2 | 0.219274 | 0.219274 |
| existing_symbol_time_extension | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 18 | 4 | 0.112673 | 0.112673 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 12 | 23 | 0 | 0.08229 | 0.08229 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.083723 | 0.083723 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 17 | 0 | 0.075396 | 0.075396 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 8 | 16 | 0 | 0.086533 | 0.086533 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 13 | 5 | 0.041031 | 0.041031 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | late_morning | holdout_pass_source_only_early_candidate | 10:15~10:59; L30; DD1.75; NL0.05 | 6 | 11 | 0 | 0.073356 | 0.065498 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.121802 | 0.121802 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.089583 | 0.089583 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 8 | 15 | 0 | None | 0.027515 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 6 | 0 | None | 0.039091 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 5 | 0 | None | 0.036131 |
| existing_symbol_time_extension | 035720 | 카카오 | midday | holdout_pass_source_only_early_candidate | 13:20~13:39; L30; DD0.5; NL0.35 | 10 | 15 | 1 | 0.051619 | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 8 | 12 | 0 | 0.068573 | 0.068573 |
| existing_symbol_time_extension | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 13 | 0 | 0.063531 | 0.063531 |
| existing_symbol_time_extension | 015760 | 한국전력 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.109358 | 0.109358 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 2 | 3 | 0 | 0.204706 | 0.204706 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 1 | 0 | 0.142892 | 0.142892 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_pass_source_only_early_candidate | 13:30~13:39; L60; DD0.75; NL0.35 | 5 | 9 | 0 | 0.403415 | 0.097242 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_pass_source_only_early_candidate | 09:35~09:44; L30; DD1.75; NL0.75 | 8 | 15 | 0 | 0.361792 | 0.266869 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 8 | 14 | 0 | 0.316655 | 0.316655 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_pass_source_only_early_candidate | 09:20~09:49; L15; DD1.75; NL0.2 | 5 | 10 | 0 | 0.375622 | 0.375457 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 4 | 8 | 0 | 0.268384 | 0.268384 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_pass_source_only_early_candidate | 09:20~09:39; L15; DD0.75; NL0.35 | 13 | 22 | 4 | 0.279526 | 0.182602 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L60; DD0.5; NL0.75 | 10 | 14 | 0 | 0.064737 | 0.064737 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:24; L20; DD0.5; NL0.05 | 10 | 14 | 3 | 0.225195 | 0.051991 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_pass_source_only_early_candidate | 09:50~09:59; L15; DD2.5; NL0.75 | 6 | 12 | 0 | 0.418047 | 0.128373 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_pass_source_only_early_candidate | 13:15~13:24; L45; DD1.0; NL0.2 | 3 | 6 | 0 | 0.423539 | 0.108024 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L45; DD2.5; NL0.5 | 5 | 8 | 0 | 0.089374 | 0.089374 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
