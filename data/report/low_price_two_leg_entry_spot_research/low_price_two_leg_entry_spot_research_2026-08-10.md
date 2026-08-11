# Lower-price profile entry-spot research — 2026-08-10

Source-only 30-day calibration / 16-day untouched holdout. No runtime policy was changed.

| Profile | Symbol | Session | Decision | Selected window | Lookback | Drawdown | Near low | Holdout legs | Held | Holdout EV | Baseline EV |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | holdout_pass_source_only_early_candidate | 13:20~13:29 | 30 | 0.75 | 0.35 | 5 | 0 | 0.228178 | 0.208971 |
| samsung_heavy_afternoon | 010140 | afternoon | holdout_positive_not_better_keep_baseline | 14:00~14:40 | 30 | 1.25 | 0.2 | 6 | 0 | 0.20605 | 0.20605 |
| daewoo_ec_midday | 047040 | midday | no_robust_calibration_candidate_do_not_promote | N/A | N/A | N/A | N/A | 11 | 0 | -0.043105 | -0.043105 |
| daewoo_ec_afternoon | 047040 | afternoon | no_robust_calibration_candidate_do_not_promote | N/A | N/A | N/A | N/A | 14 | 0 | -0.056004 | -0.056004 |
| sk_eternix_midday | 475150 | midday | holdout_pass_source_only_early_candidate | 13:30~13:54 | 20 | 2.0 | 0.75 | 6 | 0 | 0.069208 | 0.053195 |

Candidate selection never reads holdout outcomes. Price touches are minute-bar proxies, not real fills.
