# Low-price two-leg tuning — 2026-08-20

- Decision: profile-separated actual broker outcomes; next-PREOPEN bounded tightening only.
- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.
- Cost model: exact ka10073 only on unique identity match (matched=1, fallback=3); otherwise fixed 0.23%.
- Clean-baseline actual observations: 7/53 trading dates; missing dates are coverage only and are not imputed.

| Profile | Symbol | Session | Daily status | Clean cumulative attempts | Complete legs | Held/unresolved | EV |
|---|---|---|---|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | pass | 0 | 0 | 0 | None |
| samsung_heavy_afternoon | 010140 | afternoon | pass | 0 | 0 | 0 | None |
| sk_eternix_midday | 475150 | midday | pass | 1 | 2 | 0 | 0.0 |
| mirae_asset_morning | 006800 | morning | pass | 1 | 1 | 0 | 0.0 |
| jeju_semiconductor_morning | 080220 | morning | pass | 1 | 2 | 0 | 0.25048 |
| doosan_enerbility_morning | 034020 | morning | pass | 0 | 0 | 0 | None |
| hanwha_ocean_late_morning | 042660 | late_morning | pass | 0 | 0 | 0 | None |
| kakao_morning | 035720 | morning | pass | 2 | 4 | 0 | 0.142875 |
| kepco_afternoon | 015760 | afternoon | pass | 4 | 2 | 0 | 0.021529 |
| kakao_late_morning | 035720 | late_morning | pass | 2 | 3 | 2 | 0.020349 |
| sk_eternix_morning | 475150 | morning | pass | 3 | 6 | 0 | 0.217302 |
| mirae_asset_midday | 006800 | midday | pass | 1 | 0 | 0 | 0.0 |
| sk_eternix_afternoon | 475150 | afternoon | pass | 2 | 2 | 0 | 0.064275 |
| samsung_heavy_morning | 010140 | morning | pass | 1 | 1 | 0 | 0.134544 |
| doosan_enerbility_late_morning | 034020 | late_morning | pass | 0 | 0 | 0 | None |
| kakao_midday | 035720 | midday | pass | 1 | 0 | 2 | 0.0 |
| sk_telecom_afternoon | 017670 | afternoon | pass | 2 | 2 | 0 | -0.008625 |
| samsung_ea_late_morning | 028050 | late_morning | pass | 0 | 0 | 0 | None |
| samsung_ea_afternoon | 028050 | afternoon | pass | 0 | 0 | 0 | None |
| samsung_ea_morning | 028050 | morning | pass | 1 | 2 | 0 | -0.027057 |

## Next PREOPEN candidate

- No profile/axis mutation; carry forward current policies.
