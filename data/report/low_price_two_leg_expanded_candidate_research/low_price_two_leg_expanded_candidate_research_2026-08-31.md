# Expanded lower-price entry-spot research — 2026-08-31

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-31`; trading dates `60`; calibration `44`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `3`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `9/3`; completed legs `17/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | -0.001995 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 12 | 21 | 2 | None | -0.003035 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | -0.00598 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 12 | 0 | None | -0.002891 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 9 | 17 | 0 | 0.026625 | 0.026625 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 0 | None | -0.074642 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 4 | 2 | None | -0.051366 |
| new_symbol | 069960 | 현대백화점 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 10 | 0 | None | 0.00374 |
| new_symbol | 069960 | 현대백화점 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 10 | 18 | 0 | None | 0.007564 |
| new_symbol | 069960 | 현대백화점 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | 0.006088 |
| new_symbol | 069960 | 현대백화점 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 3 | 0 | None | 0.006766 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.185585 | 0.185585 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.076434 | 0.076434 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 20 | 0 | 0.062605 | 0.062605 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 5 | 8 | 0 | 0.038102 | 0.038102 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 9 | 13 | 4 | 0.039344 | 0.039344 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | 0.020207 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.012427 | 0.012427 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 8 | 14 | 0 | 0.152566 | 0.152566 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_pass_source_only_early_candidate | 09:10~09:59; L15; DD0.75; NL0.75 | 14 | 27 | 0 | 0.084789 | 0.082021 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 7 | 11 | 0 | 0.069789 | 0.069789 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.086784 | 0.086784 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 16 | 0 | 0.05215 | 0.05215 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.065781 | 0.065781 |
| existing_symbol_time_extension | 137310 | 에스디바이오센서 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 5 | 0 | 0.114278 | 0.114278 |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.134728 | 0.134728 |
| existing_symbol_time_extension | 028670 | 팬오션 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.121386 | 0.121386 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_pass_source_only_early_candidate | 13:30~13:39; L60; DD0.5; NL0.2 | 3 | 5 | 0 | 0.456788 | 0.453772 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 3 | 6 | 0 | 0.356199 | 0.356199 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 4 | 8 | 0 | 0.299688 | 0.299688 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_failed_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.328053 | 0.328053 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 4 | 6 | 0 | 0.201584 | 0.201584 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 9 | 12 | 5 | 0.213545 | 0.213545 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 3 | 1 | 3 | 0.065795 | 0.065795 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 9 | 12 | 2 | 0.21935 | 0.21935 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 3 | 6 | 0 | 0.507339 | 0.507339 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 3 | 0 | 0.291624 | 0.291624 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 5 | 4 | 0 | 0.219201 | 0.219201 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 3 | 5 | 0 | 0.266811 | 0.266811 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 2 | 1 | 2 | 0.076654 | 0.076654 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 5 | 7 | 3 | 0.15153 | 0.15153 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 7 | 13 | 0 | 0.211207 | 0.211207 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_failed_keep_baseline | 14:15~14:34; L60; DD0.5; NL0.2 | 9 | 11 | 4 | 0.145386 | 0.145386 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.203023 | 0.203023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.75; NL0.2 | 5 | 10 | 0 | 0.218191 | 0.218191 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_positive_not_better_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 3 | 5 | 1 | 0.190005 | 0.190005 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:15~09:44; L15; DD0.75; NL0.75 | 9 | 13 | 1 | 0.171937 | 0.171937 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_positive_not_better_keep_baseline | 13:20~13:29; L20; DD0.75; NL0.35 | 5 | 6 | 2 | 0.326224 | 0.326224 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 5 | 8 | 2 | 0.435615 | 0.435615 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 5 | 7 | 0 | 0.249979 | 0.249979 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 5 | 7 | 0 | 0.061424 | 0.061424 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L60; DD1.0; NL0.75 | 7 | 10 | 2 | 0.269488 | 0.269488 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 16 | 27 | 0 | 0.041933 | 0.041933 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 7 | 12 | 0 | 0.208247 | 0.208247 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L45; DD0.5; NL0.75 | 12 | 15 | 5 | 0.196404 | 0.196404 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 5 | 5 | 2 | 0.047097 | 0.047097 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 8 | 9 | 2 | 0.313338 | 0.313338 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 1 | 2 | 0 | 0.207955 | 0.207955 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L60; DD2.0; NL0.2 | 3 | 5 | 0 | 0.327727 | 0.327727 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:45~10:54; L15; DD1.75; NL0.2 | 2 | 4 | 0 | 0.529262 | 0.529262 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 7 | 12 | 1 | 0.307296 | 0.307296 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 12 | 20 | 0 | 0.331878 | 0.331878 |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_positive_not_better_keep_baseline | 09:40~09:49; L20; DD0.5; NL0.5 | 4 | 6 | 0 | 0.245308 | 0.245308 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_positive_not_better_keep_baseline | 10:30~10:49; L30; DD0.5; NL0.5 | 8 | 12 | 0 | 0.251759 | 0.251759 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:39; L15; DD0.5; NL0.75 | 12 | 19 | 4 | 0.351547 | 0.351547 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_positive_not_better_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 9 | 12 | 3 | 0.289678 | 0.289678 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:25~13:54; L20; DD0.75; NL0.2 | 3 | 5 | 0 | 0.099973 | 0.099973 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:10~14:29; L15; DD0.75; NL0.05 | 5 | 8 | 0 | 0.042477 | 0.042477 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:20~13:49; L20; DD1.0; NL0.75 | 2 | 3 | 0 | 0.169375 | 0.169375 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 7 | 13 | 1 | 0.217243 | 0.217243 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 4 | 8 | 0 | 0.14904 | 0.14904 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:14; L45; DD1.75; NL0.5 | 6 | 11 | 0 | 0.448036 | 0.132578 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
