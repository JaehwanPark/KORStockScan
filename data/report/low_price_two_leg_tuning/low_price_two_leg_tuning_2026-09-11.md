# Low-price two-leg tuning — 2026-09-11

- Decision: carry the actually applied policy; observed-signal subsets are diagnostic only and cannot promote new tightening.
- Economic replay owner: low_price_two_leg_expanded_candidate_research / existing_axis_economic_replay (same two filters, source-only, no new live authority).
- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.
- Cost model: exact ka10073 only on unique identity match (matched=0, fallback=0); otherwise fixed 0.23%.
- Clean-baseline actual observations: 23/69 trading dates; missing dates are coverage only and are not imputed.

- Main table uses the contiguous current applied-policy epoch; all-version totals remain audit-only in JSON. Missing realized EV is null, never zero.
| Profile | Symbol | Session | Daily status | Post-apply attempts | Complete legs | Manual exits/losses | Held/unresolved | Realized EV |
|---|---|---|---|---:|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| samsung_heavy_afternoon | 010140 | afternoon | pass | 1 | 1 | 0/0 | 0 | 0.234722 |
| sk_eternix_midday | 475150 | midday | gap | 2 | 0 | 0/0 | 0 | None |
| mirae_asset_morning | 006800 | morning | pass | 1 | 2 | 0/0 | 0 | 0.345954 |
| jeju_semiconductor_morning | 080220 | morning | pass | 2 | 4 | 0/0 | 2 | 0.274732 |
| doosan_enerbility_morning | 034020 | morning | pass | 1 | 2 | 0/0 | 0 | 0.300152 |
| hanwha_ocean_late_morning | 042660 | late_morning | pass | 3 | 4 | 1/1 | 0 | 0.085006 |
| kakao_morning | 035720 | morning | gap | 4 | 2 | 0/0 | 3 | 0.319074 |
| kepco_afternoon | 015760 | afternoon | gap | 2 | 2 | 0/0 | 4 | 0.361716 |
| kakao_late_morning | 035720 | late_morning | pass | 9 | 8 | 0/0 | 0 | 0.33256 |
| sk_eternix_morning | 475150 | morning | pass | 2 | 3 | 0/0 | 0 | 0.458468 |
| mirae_asset_midday | 006800 | midday | pass | 1 | 0 | 0/0 | 0 | None |
| sk_eternix_afternoon | 475150 | afternoon | pass | 1 | 2 | 0/0 | 0 | 0.172617 |
| samsung_heavy_morning | 010140 | morning | pass | 3 | 0 | 0/0 | 1 | None |
| doosan_enerbility_late_morning | 034020 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| kakao_midday | 035720 | midday | pass | 2 | 0 | 0/0 | 0 | None |
| sk_telecom_afternoon | 017670 | afternoon | pass | 0 | 0 | 0/0 | 2 | None |
| samsung_ea_late_morning | 028050 | late_morning | gap | 7 | 4 | 0/0 | 0 | 0.239851 |
| samsung_ea_afternoon | 028050 | afternoon | pass | 1 | 1 | 1/1 | 1 | -1.627206 |
| samsung_ea_morning | 028050 | morning | pass | 1 | 2 | 0/0 | 0 | 0.173023 |
| sk_telecom_late_morning | 017670 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| hanse_afternoon | 105630 | afternoon | pass | 1 | 0 | 0/0 | 0 | None |
| hanse_morning | 105630 | morning | pass | 3 | 2 | 0/0 | 0 | 0.222745 |
| cj_cgv_midday | 079160 | midday | gap | 0 | 0 | 0/0 | 0 | None |
| cj_cgv_afternoon | 079160 | afternoon | pass | 2 | 1 | 1/0 | 0 | 0.166058 |
| tym_midday | 002900 | midday | gap | 1 | 0 | 0/0 | 0 | None |
| tym_afternoon | 002900 | afternoon | gap | 2 | 1 | 0/0 | 0 | 0.050899 |
| hanse_late_morning | 105630 | late_morning | pass | 2 | 2 | 0/0 | 0 | 0.222617 |
| nhn_afternoon | 181710 | afternoon | gap | 2 | 2 | 0/0 | 0 | 0.46869 |
| kepco_late_morning | 015760 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| hanse_midday | 105630 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| cj_cgv_late_morning | 079160 | late_morning | pass | 3 | 0 | 0/0 | 0 | None |
| youngone_afternoon | 111770 | afternoon | pass | 0 | 0 | 0/0 | 0 | None |
| youngone_morning | 111770 | morning | pass | 12 | 6 | 0/0 | 0 | 0.038637 |
| kepco_midday | 015760 | midday | gap | 3 | 2 | 0/0 | 0 | 0.07349 |
| sk_eternix_late_morning | 475150 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| mirae_asset_late_morning | 006800 | late_morning | pass | 1 | 2 | 0/0 | 0 | 0.359536 |
| kepco_morning | 015760 | morning | pass | 6 | 7 | 3/3 | 2 | -0.526924 |
| nhn_morning | 181710 | morning | pass | 1 | 0 | 0/0 | 0 | None |
| nhn_late_morning | 181710 | late_morning | pass | 1 | 2 | 2/2 | 0 | -2.500816 |
| sd_biosensor_morning | 137310 | morning | pass | 6 | 2 | 0/0 | 0 | 0.427354 |
| sd_biosensor_late_morning | 137310 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| sd_biosensor_midday | 137310 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| doosan_enerbility_afternoon | 034020 | afternoon | pass | 2 | 3 | 0/0 | 0 | 0.226447 |
| samsung_ea_midday | 028050 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| sk_telecom_morning | 017670 | morning | gap | 3 | 1 | 0/0 | 1 | 0.206536 |
| fan_ocean_morning | 028670 | morning | pass | 2 | 2 | 0/0 | 0 | 0.127875 |
| fan_ocean_late_morning | 028670 | late_morning | pass | 1 | 2 | 0/0 | 0 | 0.441705 |
| samsung_heavy_late_morning | 010140 | late_morning | pass | 1 | 1 | 0/0 | 0 | 0.24455 |
| cj_cgv_morning | 079160 | morning | gap | 0 | 0 | 0/0 | 0 | None |
| fan_ocean_afternoon | 028670 | afternoon | gap | 4 | 2 | 0/0 | 0 | 0.105852 |
| youngone_midday | 111770 | midday | gap | 0 | 0 | 0/0 | 0 | None |
| sk_telecom_midday | 017670 | midday | gap | 0 | 0 | 0/0 | 0 | None |
| nhn_midday | 181710 | midday | pass | 2 | 2 | 0/0 | 0 | 0.108696 |
| tym_morning | 002900 | morning | pass | 0 | 0 | 0/0 | 0 | None |
| sd_biosensor_afternoon | 137310 | afternoon | pass | 0 | 0 | 0/0 | 0 | None |
| lotte_chemical_morning | 011170 | morning | gap | 1 | 0 | 0/0 | 0 | None |
| lotte_chemical_afternoon | 011170 | afternoon | pass | 0 | 0 | 0/0 | 0 | None |
| tym_late_morning | 002900 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| lotte_chemical_midday | 011170 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| lx_semicon_morning | 108320 | morning | pass | 0 | 0 | 0/0 | 0 | None |

## Next PREOPEN candidate

- No profile/axis mutation; carry forward current policies.
