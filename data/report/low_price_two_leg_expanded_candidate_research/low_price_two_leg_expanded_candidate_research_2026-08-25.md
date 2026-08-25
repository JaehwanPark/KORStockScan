# Expanded lower-price entry-spot research — 2026-08-25

Source-only clean-baseline expanding calibration / latest 16-day holdout. No machine or live session was added.

Window: `2026-06-05~2026-08-25`; trading dates `56`; calibration `40`; holdout `16`.

Recommendation status: `recommendations_ready`; profiles: `14`.

## Operator source-only observation candidates

- `theborn_morning_0940_0959_l20_dd0p5_nl0p35_t4_v1`: `더본코리아` `morning`; OOS episodes `6/3`; completed legs `11/4`; source-only, no runtime/order authority.

| Lane | Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| new_symbol | 007660 | 이수페타시스 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.027911 |
| new_symbol | 007660 | 이수페타시스 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 12 | 20 | 2 | None | 0.012883 |
| new_symbol | 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.013355 |
| new_symbol | 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | 0.00026 |
| new_symbol | 475560 | 더본코리아 | morning | holdout_positive_not_better_keep_baseline | 09:40~09:59; L20; DD0.5; NL0.35 | 6 | 11 | 0 | 0.020856 | 0.020856 |
| new_symbol | 475560 | 더본코리아 | late_morning | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 10 | 0 | None | -0.088486 |
| new_symbol | 475560 | 더본코리아 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 0 | None | -0.036652 |
| new_symbol | 475560 | 더본코리아 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 2 | 2 | None | -0.034917 |
| new_symbol | 137310 | 에스디바이오센서 | morning | holdout_pass_source_only_early_candidate | 09:30~09:49; L15; DD0.75; NL0.75 | 11 | 20 | 0 | 0.107783 | 0.093701 |
| new_symbol | 137310 | 에스디바이오센서 | late_morning | holdout_pass_source_only_early_candidate | 10:40~10:59; L30; DD0.5; NL0.5 | 11 | 20 | 0 | 0.105969 | 0.06795 |
| new_symbol | 137310 | 에스디바이오센서 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 0 | 0 | 0.0 | 0.0 |
| new_symbol | 137310 | 에스디바이오센서 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.138983 | 0.138983 |
| existing_symbol_time_extension | 010140 | 삼성중공업 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.181907 | 0.181907 |
| existing_symbol_time_extension | 006800 | 미래에셋증권 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.076434 | 0.076434 |
| existing_symbol_time_extension | 080220 | 제주반도체 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 9 | 18 | 0 | 0.065037 | 0.065037 |
| existing_symbol_time_extension | 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 7 | 13 | 0 | 0.053638 | 0.053638 |
| existing_symbol_time_extension | 080220 | 제주반도체 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 9 | 11 | 5 | 0.037927 | 0.037927 |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 034020 | 두산에너빌리티 | afternoon | holdout_pass_source_only_early_candidate | 14:10~14:29; L15; DD0.75; NL0.05 | 4 | 6 | 0 | 0.044419 | 0.027406 |
| existing_symbol_time_extension | 042660 | 한화오션 | morning | no_robust_calibration_candidate_do_not_promote | N/A | 6 | 11 | 0 | None | 0.022698 |
| existing_symbol_time_extension | 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.021852 |
| existing_symbol_time_extension | 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 1 | 2 | 0 | None | 0.031884 |
| existing_symbol_time_extension | 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| existing_symbol_time_extension | 017670 | SK텔레콤 | morning | holdout_failed_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 6 | 10 | 0 | 0.021889 | 0.021889 |
| existing_symbol_time_extension | 017670 | SK텔레콤 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 8 | 0 | 0.012993 | 0.012993 |
| existing_symbol_time_extension | 028050 | 삼성E&A | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L30; DD1.0; NL0.75 | 3 | 5 | 0 | 0.00744 | 0.006825 |
| existing_symbol_time_extension | 079160 | CJ CGV | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 9 | 16 | 0 | 0.158069 | 0.158069 |
| existing_symbol_time_extension | 002900 | TYM | morning | holdout_positive_not_better_keep_baseline | 09:10~09:59; L30; DD1.25; NL0.2 | 5 | 10 | 0 | 0.094421 | 0.094421 |
| existing_symbol_time_extension | 002900 | TYM | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 6 | 11 | 0 | 0.083511 | 0.083511 |
| existing_symbol_time_extension | 181710 | NHN | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 6 | 10 | 2 | 0.074462 | 0.074462 |
| existing_symbol_time_extension | 111770 | 영원무역 | late_morning | holdout_positive_not_better_keep_baseline | 10:00~10:59; L30; DD1.25; NL0.2 | 11 | 19 | 0 | 0.037664 | 0.037664 |
| existing_symbol_time_extension | 111770 | 영원무역 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 3 | 4 | 0 | 0.027496 | 0.027496 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | midday | holdout_failed_keep_baseline | 13:20~13:29; L30; DD0.75; NL0.35 | 1 | 1 | 0 | 0.126901 | 0.126901 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:40; L45; DD1.0; NL0.35 | 3 | 4 | 0 | 0.180949 | None |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | midday | holdout_positive_not_better_keep_baseline | 13:30~13:39; L60; DD0.75; NL0.35 | 4 | 7 | 0 | 0.439169 | 0.439169 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | morning | holdout_positive_not_better_keep_baseline | 09:35~09:44; L30; DD1.75; NL0.75 | 5 | 10 | 0 | 0.370044 | 0.370044 |
| existing_symbol_logic_improvement | 080220 | 제주반도체 | morning | holdout_positive_not_better_keep_baseline | 09:10~09:49; L20; DD2.5; NL0.1 | 5 | 10 | 0 | 0.321173 | 0.321173 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:49; L15; DD1.75; NL0.2 | 3 | 6 | 0 | 0.339205 | 0.339205 |
| existing_symbol_logic_improvement | 042660 | 한화오션 | late_morning | holdout_failed_keep_baseline | 10:05~10:24; L20; DD1.25; NL0.1 | 4 | 7 | 0 | 0.231221 | 0.231221 |
| existing_symbol_logic_improvement | 035720 | 카카오 | morning | holdout_failed_keep_baseline | 09:20~09:39; L15; DD0.75; NL0.35 | 10 | 15 | 5 | 0.241264 | 0.241264 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:29; L45; DD0.75; NL0.75 | 3 | 3 | 1 | 0.19294 | 0.19294 |
| existing_symbol_logic_improvement | 035720 | 카카오 | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:24; L15; DD0.5; NL0.05 | 9 | 13 | 3 | 0.235083 | 0.235083 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | morning | holdout_failed_keep_baseline | 09:50~09:59; L15; DD2.5; NL0.75 | 5 | 10 | 0 | 0.510606 | 0.510606 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | midday | holdout_failed_keep_baseline | 13:15~13:24; L45; DD1.0; NL0.2 | 2 | 3 | 0 | 0.291624 | 0.291624 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | afternoon | holdout_failed_keep_baseline | 14:15~14:40; L15; DD2.0; NL0.5 | 1 | 1 | 1 | 0.256914 | 0.256914 |
| existing_symbol_logic_improvement | 010140 | 삼성중공업 | morning | holdout_positive_not_better_keep_baseline | 09:20~09:29; L20; DD1.75; NL0.75 | 6 | 5 | 0 | 0.246987 | 0.246987 |
| existing_symbol_logic_improvement | 034020 | 두산에너빌리티 | late_morning | holdout_positive_not_better_keep_baseline | 10:15~10:34; L45; DD1.5; NL0.05 | 4 | 7 | 0 | 0.281907 | 0.281907 |
| existing_symbol_logic_improvement | 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:20~13:39; L15; DD0.5; NL0.2 | 4 | 3 | 4 | 0.119766 | 0.119766 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | afternoon | holdout_positive_not_better_keep_baseline | 14:25~14:34; L15; DD0.75; NL0.5 | 6 | 9 | 3 | 0.165522 | 0.165522 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | late_morning | holdout_positive_not_better_keep_baseline | 10:05~10:14; L45; DD1.0; NL0.75 | 8 | 13 | 2 | 0.183597 | 0.183597 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | afternoon | holdout_positive_not_better_keep_baseline | 14:05~14:34; L20; DD0.75; NL0.35 | 5 | 7 | 0 | 0.153791 | 0.153791 |
| existing_symbol_logic_improvement | 028050 | 삼성E&A | morning | holdout_positive_not_better_keep_baseline | 09:45~09:59; L15; DD2.0; NL0.5 | 2 | 4 | 0 | 0.225532 | 0.225532 |
| existing_symbol_logic_improvement | 017670 | SK텔레콤 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L30; DD0.75; NL0.2 | 3 | 6 | 0 | 0.217609 | 0.012538 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | afternoon | holdout_failed_keep_baseline | 14:20~14:29; L15; DD0.5; NL0.75 | 4 | 7 | 1 | 0.201021 | 0.201021 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | morning | holdout_positive_not_better_keep_baseline | 09:15~09:44; L15; DD0.75; NL0.75 | 9 | 13 | 1 | 0.170401 | 0.170401 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | midday | holdout_failed_keep_baseline | 13:20~13:49; L60; DD0.75; NL0.75 | 6 | 8 | 0 | 0.119866 | 0.119866 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | afternoon | holdout_positive_not_better_keep_baseline | 14:15~14:24; L30; DD0.5; NL0.75 | 5 | 8 | 2 | 0.438457 | 0.438457 |
| existing_symbol_logic_improvement | 002900 | TYM | midday | holdout_positive_not_better_keep_baseline | 13:15~13:44; L20; DD0.5; NL0.35 | 9 | 11 | 0 | 0.226951 | 0.226951 |
| existing_symbol_logic_improvement | 002900 | TYM | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L20; DD0.5; NL0.5 | 6 | 9 | 0 | 0.069151 | 0.069151 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:19; L20; DD0.75; NL0.2 | 3 | 4 | 0 | 0.165404 | 0.155207 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | midday | holdout_failed_keep_baseline | 13:30~13:49; L45; DD0.5; NL0.5 | 8 | 11 | 2 | 0.062 | 0.062 |
| existing_symbol_logic_improvement | 181710 | NHN | afternoon | holdout_pass_source_only_early_candidate | 14:00~14:29; L60; DD0.5; NL0.75 | 7 | 12 | 1 | 0.303038 | 0.28771 |
| existing_symbol_logic_improvement | 105630 | 한세실업 | midday | holdout_failed_keep_baseline | 13:20~13:49; L45; DD0.5; NL0.75 | 2 | 3 | 0 | 0.164995 | 0.164995 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | afternoon | holdout_failed_keep_baseline | 14:30~14:39; L45; DD0.5; NL0.75 | 10 | 14 | 3 | 0.20971 | 0.20971 |
| existing_symbol_logic_improvement | 079160 | CJ CGV | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:09; L20; DD0.5; NL0.75 | 14 | 19 | 4 | 0.378603 | 0.335732 |
| existing_symbol_logic_improvement | 111770 | 영원무역 | morning | holdout_failed_keep_baseline | 09:20~09:39; L20; DD0.5; NL0.5 | 15 | 24 | 0 | 0.031303 | 0.031303 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | late_morning | holdout_failed_keep_baseline | 10:00~10:59; L20; DD0.75; NL0.5 | 12 | 17 | 2 | 0.276338 | 0.276338 |
| existing_symbol_logic_improvement | 475150 | SK이터닉스 | late_morning | holdout_pass_source_only_early_candidate | 10:45~10:54; L15; DD1.75; NL0.2 | 3 | 6 | 0 | 0.524857 | 0.162428 |
| existing_symbol_logic_improvement | 006800 | 미래에셋증권 | late_morning | holdout_pass_source_only_early_candidate | 10:00~10:29; L20; DD1.0; NL0.35 | 11 | 18 | 0 | 0.306268 | 0.08399 |
| existing_symbol_logic_improvement | 015760 | 한국전력 | morning | holdout_pass_source_only_early_candidate | 09:35~09:59; L15; DD0.5; NL0.75 | 12 | 18 | 0 | 0.291618 | 0.06873 |
| existing_symbol_logic_improvement | 181710 | NHN | morning | holdout_pass_source_only_early_candidate | 09:40~09:49; L20; DD0.5; NL0.5 | 3 | 6 | 0 | 0.323732 | 0.061866 |
| existing_symbol_logic_improvement | 181710 | NHN | late_morning | holdout_pass_source_only_early_candidate | 10:30~10:49; L30; DD0.5; NL0.5 | 8 | 13 | 0 | 0.26033 | 0.047401 |

## Target-date cumulative logic attribution

- `kepco_morning`: candidate-only signal `2026-08-25T09:55:00+09:00`; completed `2` leg; held `0`; EV `0.412089`%.

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
