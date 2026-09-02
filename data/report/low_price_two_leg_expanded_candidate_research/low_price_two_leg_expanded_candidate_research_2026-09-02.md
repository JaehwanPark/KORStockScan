# Expanded lower-price entry-spot research — 2026-09-02

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-02`; trading dates `62`; calibration `46`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `10`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `10/3`; completed legs `19/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 8 | 0 | None | -0.006623 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 13 | 25 | 0 | None | -0.00649 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | -0.00598 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 12 | 0 | None | -0.002891 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 10 | 19 | 0 | 0.028727 | 0.028727 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 0 | None | -0.074642 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 4 | 2 | None | -0.051366 |
| new_symbol | 006360 | GS건설 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 9 | 16 | 2 | 0.076805 | 0.076805 |
| new_symbol | 006360 | GS건설 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 15 | 2 | 0.063145 | 0.063145 |
| new_symbol | 006360 | GS건설 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.07705 | 0.07705 |
| new_symbol | 006360 | GS건설 | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:34; L20; DD1.0; NL0.35 | 8 | 14 | 2 | 0.0659 | 0.057548 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_pass_source_only_early_candidate | 10:10~10:19; L15; DD0.5; NL0.75 | 7 | 10 | 0 | 0.189905 | 0.171089 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.076434 | 0.076434 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 22 | 0 | 0.061485 | 0.061485 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 6 | 0 | 0.040969 | 0.040969 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 9 | 13 | 4 | 0.042988 | 0.042988 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | 0.02218 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.021852 | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.004186 | 0.004186 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_pass_source_only_early_candidate | 09:40~09:59; L15; DD0.5; NL0.75 | 16 | 25 | 5 | 0.137582 | 0.129836 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.082021 | 0.082021 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 7 | 11 | 0 | 0.066931 | 0.066931 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 8 | 15 | 0 | 0.088457 | 0.088457 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 17 | 0 | 0.060709 | 0.060709 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.065781 | 0.065781 |
| existing_symbol_time_extension | 137310 | 에스디바이오센서 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 3 | 5 | 0 | 0.114278 | 0.114278 |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.134728 | 0.134728 |
| existing_symbol_time_extension | 028670 | 팬오션 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.121386 | 0.121386 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_pass_source_only_early_candidate | 13:30~13:39; L60; DD0.5; NL0.2 | 5 | 6 | 2 | 0.334988 | 0.333321 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_failed_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 1 | 2 | 0 | 0.315132 | 0.315132 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 3 | 6 | 0 | 0.290096 | 0.290096 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_failed_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:24; L20; DD0.75; NL0.5 | 11 | 17 | 4 | 0.198725 | 0.184136 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 9 | 9 | 7 | 0.163067 | 0.163067 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 4 | 2 | 3 | 0.100787 | 0.100787 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 9 | 11 | 3 | 0.206814 | 0.206814 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 4 | 8 | 0 | 0.522674 | 0.522674 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 2 | 0 | 0.190414 | 0.190414 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_failed_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 3 | 2 | 0 | 0.123376 | 0.123376 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 3 | 3 | 1 | 0.157414 | 0.157414 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 3 | 3 | 2 | 0.162921 | 0.162921 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 5 | 7 | 3 | 0.15153 | 0.15153 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 9 | 14 | 2 | 0.178608 | 0.178608 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:34; L60; DD0.5; NL0.2 | 10 | 13 | 4 | 0.154487 | 0.154487 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.203023 | 0.203023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.75; NL0.2 | 4 | 8 | 0 | 0.206607 | 0.206607 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_positive_not_better_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 7 | 1 | 0.201129 | 0.201129 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:30~09:44; L15; DD0.75; NL0.75 | 6 | 10 | 1 | 0.19662 | 0.177902 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:29; L20; DD0.75; NL0.35 | 4 | 4 | 2 | 0.274357 | 0.274357 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:24; L45; DD0.5; NL0.5 | 3 | 5 | 0 | 0.484969 | 0.412833 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 6 | 8 | 0 | 0.240322 | 0.240322 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 5 | 6 | 0 | 0.048504 | 0.048504 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_failed_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 10 | 12 | 3 | 0.331262 | 0.331262 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L60; DD1.0; NL0.75 | 9 | 13 | 2 | 0.273051 | 0.273051 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 2 | 3 | 0 | 0.164019 | 0.164019 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 7 | 12 | 0 | 0.208247 | 0.208247 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L60; DD2.0; NL0.2 | 3 | 5 | 0 | 0.327727 | 0.327727 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 5 | 5 | 2 | 0.049598 | 0.049598 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L45; DD0.5; NL0.75 | 14 | 17 | 7 | 0.192507 | 0.192507 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 16 | 28 | 0 | 0.048721 | 0.048721 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:45~10:54; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.472835 | 0.472835 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 7 | 10 | 2 | 0.257317 | 0.257317 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 12 | 21 | 0 | 0.352407 | 0.352407 |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_positive_not_better_keep_baseline | 09:40~09:49; L20; DD0.5; NL0.5 | 4 | 6 | 0 | 0.245308 | 0.245308 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_pass_source_only_early_candidate | 10:35~10:49; L20; DD1.25; NL0.75 | 4 | 7 | 0 | 0.317148 | 0.239836 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:39; L15; DD0.5; NL0.75 | 14 | 22 | 4 | 0.349517 | 0.349517 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 9 | 10 | 5 | 0.244454 | 0.244454 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_pass_source_only_early_candidate | 13:25~13:54; L20; DD0.75; NL0.2 | 4 | 6 | 0 | 0.334344 | 0.091919 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:10~14:29; L15; DD0.75; NL0.05 | 5 | 8 | 0 | 0.042477 | 0.042477 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:20~13:49; L20; DD1.0; NL0.75 | 2 | 3 | 0 | 0.169375 | 0.169375 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 5 | 10 | 0 | 0.227396 | 0.227396 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 5 | 9 | 0 | 0.134569 | 0.134569 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:14; L45; DD1.75; NL0.5 | 7 | 10 | 3 | 0.355556 | 0.13912 |

## Target-date cumulative logic attribution

No cumulative holdout candidate added a completed target-date rebound.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
