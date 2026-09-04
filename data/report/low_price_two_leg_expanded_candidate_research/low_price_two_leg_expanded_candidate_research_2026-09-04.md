# Expanded lower-price entry-spot research — 2026-09-04

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-09-04`; trading dates `64`; calibration `48`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `13`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `12/3`; completed legs `21/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 9 | 0 | None | -0.007 |
| new_symbol | 007660 | 이수페타시스 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 14 | 27 | 0 | -0.009863 | -0.009863 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 7 | 0 | None | -0.00598 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 13 | 1 | None | -0.003423 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 12 | 21 | 0 | 0.028925 | 0.028925 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 7 | 12 | 0 | None | -0.074642 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 3 | 4 | 2 | None | -0.051366 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_pass_source_only_early_candidate | 10:15~10:34; L30; DD0.75; NL0.35 | 5 | 7 | 0 | 0.195868 | 0.150211 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.089645 | 0.089645 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 13 | 26 | 0 | 0.064995 | 0.064995 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.044879 | 0.044879 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 10 | 13 | 6 | 0.039132 | 0.039132 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.023928 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.021852 | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 0 | 2 | 0.0 | 0.0 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.084293 | 0.084293 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_pass_source_only_early_candidate | 13:15~13:24; L15; DD0.5; NL0.05 | 5 | 8 | 1 | 0.006672 | 0.004186 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_pass_source_only_early_candidate | 09:10~09:39; L15; DD0.5; NL0.2 | 12 | 19 | 4 | 0.140509 | 0.123242 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 3 | 6 | 0 | 0.082021 | 0.082021 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 7 | 11 | 0 | 0.066931 | 0.066931 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 10 | 18 | 0 | 0.057809 | 0.057809 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_pass_source_only_early_candidate | 13:15~13:44; L15; DD0.75; NL0.75 | 8 | 13 | 0 | 0.049294 | 0.043757 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 9 | 14 | 2 | 0.070522 | 0.070522 |
| existing_symbol_time_extension | 137310 | 에스디바이오센서 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 7 | 0 | 0.116882 | 0.116882 |
| existing_symbol_time_extension | 028670 | 팬오션 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.13557 | 0.13557 |
| existing_symbol_time_extension | 028670 | 팬오션 | afternoon | holdout_pass_source_only_early_candidate | 14:05~14:40; L30; DD0.75; NL0.2 | 8 | 15 | 0 | 0.130629 | 0.110833 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 0 | 0 | 0 | None | None |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.263499 | 0.263499 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_failed_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 6 | 5 | 3 | 0.230468 | 0.230468 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_failed_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 1 | 2 | 0 | 0.315132 | 0.315132 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_failed_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 3 | 4 | 2 | 0.21032 | 0.21032 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_failed_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.330152 | 0.330152 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_pass_source_only_early_candidate | 10:05~10:24; L45; DD0.75; NL0.75 | 10 | 17 | 2 | 0.220369 | 0.184136 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 8 | 8 | 6 | 0.165204 | 0.165204 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 5 | 2 | 5 | 0.080993 | 0.080993 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 9 | 11 | 3 | 0.212234 | 0.212234 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_positive_not_better_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 4 | 8 | 0 | 0.522674 | 0.522674 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 2 | 0 | 0.190414 | 0.190414 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.202617 | 0.202617 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_failed_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 4 | 2 | 0 | 0.0929 | 0.0929 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_failed_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 3 | 3 | 1 | 0.157414 | 0.157414 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 4 | 4 | 2 | 0.16649 | 0.16649 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_failed_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 5 | 7 | 3 | 0.151965 | 0.151965 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 10 | 16 | 2 | 0.184709 | 0.184709 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:34; L20; DD0.75; NL0.35 | 3 | 5 | 0 | 0.185722 | 0.175561 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_failed_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 1 | 2 | 0 | 0.203023 | 0.203023 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_positive_not_better_keep_baseline | 10:45~10:54; L30; DD0.75; NL0.2 | 5 | 10 | 0 | 0.214207 | 0.214207 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_positive_not_better_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 5 | 9 | 1 | 0.209609 | 0.209609 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_pass_source_only_early_candidate | 09:30~09:44; L15; DD0.75; NL0.75 | 6 | 9 | 1 | 0.176767 | 0.171547 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_positive_not_better_keep_baseline | 13:20~13:29; L20; DD0.75; NL0.35 | 4 | 4 | 1 | 0.282727 | 0.282727 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 4 | 7 | 1 | 0.492748 | 0.492748 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:34; L15; DD0.5; NL0.75 | 4 | 6 | 0 | 0.271775 | 0.271775 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 4 | 5 | 0 | 0.051734 | 0.051734 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L30; DD0.75; NL0.75 | 7 | 12 | 0 | 0.208247 | 0.208247 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 5 | 5 | 2 | 0.054779 | 0.054779 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L60; DD2.0; NL0.2 | 3 | 5 | 0 | 0.327727 | 0.327727 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 2 | 3 | 0 | 0.164019 | 0.164019 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_failed_keep_baseline | 10:00~10:09; L15; DD0.5; NL0.35 | 10 | 12 | 3 | 0.333775 | 0.333775 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 16 | 28 | 0 | 0.05364 | 0.05364 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L45; DD0.5; NL0.75 | 14 | 20 | 5 | 0.234501 | 0.234501 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_pass_source_only_early_candidate | 14:00~14:40; L15; DD0.75; NL0.75 | 12 | 17 | 4 | 0.270915 | 0.2468 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_failed_keep_baseline | 10:45~10:54; L15; DD1.75; NL0.2 | 1 | 2 | 0 | 0.472835 | 0.472835 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:19; L45; DD1.0; NL0.5 | 8 | 12 | 2 | 0.273139 | 0.273139 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:59; L15; DD0.5; NL0.75 | 11 | 18 | 2 | 0.33642 | 0.33642 |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_positive_not_better_keep_baseline | 09:40~09:49; L20; DD0.5; NL0.5 | 3 | 4 | 0 | 0.250995 | 0.250995 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_pass_source_only_early_candidate | 10:35~10:49; L20; DD1.25; NL0.75 | 4 | 6 | 0 | 0.303967 | 0.231821 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | morning | holdout_positive_not_better_keep_baseline | 09:30~09:39; L15; DD0.5; NL0.75 | 13 | 20 | 4 | 0.344839 | 0.344839 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | late_morning | holdout_failed_keep_baseline | 10:40~10:59; L30; DD0.5; NL0.35 | 7 | 7 | 5 | 0.227755 | 0.227755 |
| existing_symbol_logic_improvement | 137310 | 에스디바이오센서 | midday | holdout_pass_source_only_early_candidate | 13:25~13:54; L20; DD0.75; NL0.2 | 4 | 6 | 0 | 0.334344 | 0.091919 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | afternoon | holdout_pass_source_only_early_candidate | 14:20~14:29; L15; DD0.75; NL0.75 | 4 | 5 | 1 | 0.179169 | 0.048271 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | midday | holdout_pass_source_only_early_candidate | 13:25~13:44; L15; DD0.75; NL0.2 | 4 | 8 | 0 | 0.223953 | 0.113158 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:29; L30; DD0.5; NL0.75 | 5 | 9 | 0 | 0.19842 | 0.19842 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | morning | holdout_failed_keep_baseline | 09:35~09:59; L30; DD2.0; NL0.2 | 3 | 5 | 0 | 0.127567 | 0.127567 |
| existing_symbol_logic_improvement | 028670 | 팬오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:14; L45; DD1.75; NL0.5 | 6 | 9 | 2 | 0.112887 | 0.112887 |

## Target-date cumulative logic attribution

- `nhn_afternoon`: candidate-only signal `2026-09-04T14:02:00+09:00`; completed `2` leg; held `0`; EV `0.391279`%.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
