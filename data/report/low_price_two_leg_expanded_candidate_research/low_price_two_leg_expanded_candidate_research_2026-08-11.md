# Expanded lower-price entry-spot research — 2026-08-11

Source-only rolling 30-day calibration / 16-day untouched holdout. No live symbol was added.

Recommendation status: `recommendations_ready`; profiles: `4`.

| Symbol | Name | Session | Decision | Recommended spot | Holdout episodes | Completed | Held | Candidate EV | Baseline EV |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | midday | holdout_pass_source_only_early_candidate | 13:15~13:24; L45; DD1.0; NL0.5 | 5 | 10 | 0 | 0.108024 | 0.073793 |
| 006800 | 미래에셋증권 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 4 | 6 | 1 | 0.069013 | 0.069013 |
| 007660 | 이수페타시스 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 8 | 2 | None | 0.076265 |
| 007660 | 이수페타시스 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 4 | 5 | 2 | None | 0.03886 |
| 015760 | 한국전력 | midday | holdout_positive_not_better_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.109358 | 0.109358 |
| 015760 | 한국전력 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 2 | 3 | 0 | 0.075794 | 0.075794 |
| 017670 | SK텔레콤 | midday | holdout_pass_source_only_early_candidate | 13:20~13:49; L45; DD0.75; NL0.1 | 4 | 7 | 0 | 0.032962 | 0.025808 |
| 017670 | SK텔레콤 | afternoon | holdout_pass_source_only_early_candidate | 14:10~14:29; L30; DD0.5; NL0.35 | 11 | 19 | 0 | 0.021896 | 0.019659 |
| 028050 | 삼성E&A | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 4 | 8 | 0 | 0.028833 | 0.028833 |
| 028050 | 삼성E&A | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 5 | 9 | 0 | 0.019432 | 0.019432 |
| 034020 | 두산에너빌리티 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 2 | 4 | 0 | 0.121802 | 0.121802 |
| 034020 | 두산에너빌리티 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 5 | 9 | 1 | 0.096535 | 0.096535 |
| 035720 | 카카오 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 0 | 0 | 0 | None | None |
| 035720 | 카카오 | afternoon | holdout_failed_keep_baseline | 14:00~14:40; L30; DD1.25; NL0.2 | 1 | 2 | 0 | 0.082286 | 0.082286 |
| 042660 | 한화오션 | midday | no_robust_calibration_candidate_do_not_promote | N/A | 2 | 4 | 0 | None | 0.048756 |
| 042660 | 한화오션 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | 5 | 8 | 0 | None | 0.034308 |
| 080220 | 제주반도체 | midday | holdout_failed_keep_baseline | 13:15~13:54; L30; DD1.25; NL0.2 | 11 | 20 | 0 | 0.075903 | 0.075903 |
| 080220 | 제주반도체 | afternoon | holdout_pass_source_only_early_candidate | 14:15~14:24; L15; DD1.5; NL0.2 | 4 | 7 | 0 | 0.071906 | 0.057684 |

Candidate selection never reads holdout outcomes. Minute-bar touches are proxies, not real fills.
