# Low-price two-leg tuning — 2026-09-07

- Decision: carry the actually applied policy; observed-signal subsets are diagnostic only and cannot promote new tightening.
- Economic replay owner: low_price_two_leg_expanded_candidate_research / existing_axis_economic_replay (same two filters, source-only, no new live authority).
- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.
- Cost model: exact ka10073 only on unique identity match (matched=1, fallback=4); otherwise fixed 0.23%.
- Clean-baseline actual observations: 19/65 trading dates; missing dates are coverage only and are not imputed.

| Profile | Symbol | Session | Daily status | Clean cumulative attempts | Complete legs | Manual exits/losses | Held/unresolved | EV |
|---|---|---|---|---:|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| samsung_heavy_afternoon | 010140 | afternoon | pass | 1 | 1 | 0/0 | 0 | 0.117497 |
| sk_eternix_midday | 475150 | midday | pass | 3 | 2 | 0/0 | 0 | 0.0 |
| mirae_asset_morning | 006800 | morning | pass | 1 | 1 | 0/0 | 0 | 0.0 |
| jeju_semiconductor_morning | 080220 | morning | gap | 2 | 4 | 0/0 | 2 | 0.274732 |
| doosan_enerbility_morning | 034020 | morning | pass | 1 | 2 | 0/0 | 0 | 0.300152 |
| hanwha_ocean_late_morning | 042660 | late_morning | pass | 3 | 4 | 0/0 | 0 | 0.161528 |
| kakao_morning | 035720 | morning | pass | 4 | 6 | 0/0 | 3 | 0.153451 |
| kepco_afternoon | 015760 | afternoon | pass | 5 | 3 | 0/0 | 4 | 0.02597 |
| kakao_late_morning | 035720 | late_morning | pass | 9 | 9 | 0/0 | 2 | 0.122654 |
| sk_eternix_morning | 475150 | morning | pass | 4 | 7 | 0/0 | 0 | 0.230934 |
| mirae_asset_midday | 006800 | midday | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| sk_eternix_afternoon | 475150 | afternoon | pass | 3 | 4 | 0/0 | 0 | 0.097338 |
| samsung_heavy_morning | 010140 | morning | pass | 3 | 1 | 0/0 | 0 | 0.044507 |
| doosan_enerbility_late_morning | 034020 | late_morning | pass | 2 | 2 | 0/0 | 0 | 0.14428 |
| kakao_midday | 035720 | midday | pass | 3 | 0 | 0/0 | 2 | 0.0 |
| sk_telecom_afternoon | 017670 | afternoon | gap | 2 | 2 | 0/0 | 2 | -0.008625 |
| samsung_ea_late_morning | 028050 | late_morning | pass | 6 | 5 | 0/0 | 0 | 0.048653 |
| samsung_ea_afternoon | 028050 | afternoon | pass | 5 | 6 | 1/1 | 0 | 0.09465 |
| samsung_ea_morning | 028050 | morning | pass | 2 | 4 | 0/0 | 0 | 0.073337 |
| sk_telecom_late_morning | 017670 | late_morning | pass | 3 | 4 | 0/0 | 0 | 0.087536 |
| hanse_afternoon | 105630 | afternoon | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| hanse_morning | 105630 | morning | pass | 4 | 3 | 0/0 | 0 | 0.056554 |
| cj_cgv_midday | 079160 | midday | pass | 4 | 1 | 0/0 | 0 | 0.042898 |
| cj_cgv_afternoon | 079160 | afternoon | pass | 2 | 1 | 1/0 | 0 | 0.042643 |
| tym_midday | 002900 | midday | pass | 2 | 2 | 0/0 | 0 | 0.091834 |
| tym_afternoon | 002900 | afternoon | pass | 2 | 1 | 0/0 | 0 | 0.012734 |
| youngone_afternoon | 111770 | afternoon | pass | 6 | 4 | 1/1 | 0 | 0.074876 |
| youngone_morning | 111770 | morning | pass | 9 | 6 | 0/0 | 0 | 0.012422 |
| hanse_midday | 105630 | midday | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| nhn_afternoon | 181710 | afternoon | pass | 5 | 5 | 2/2 | 0 | -0.384771 |
| kepco_midday | 015760 | midday | pass | 2 | 1 | 0/0 | 0 | 0.020366 |
| hanse_late_morning | 105630 | late_morning | pass | 2 | 4 | 0/0 | 0 | 0.175879 |
| cj_cgv_late_morning | 079160 | late_morning | pass | 5 | 2 | 0/0 | 1 | 0.023655 |
| kepco_late_morning | 015760 | late_morning | pass | 2 | 3 | 0/0 | 1 | 0.261685 |
| sk_eternix_late_morning | 475150 | late_morning | pass | 0 | 0 | 0/0 | 0 | None |
| mirae_asset_late_morning | 006800 | late_morning | pass | 3 | 5 | 0/0 | 0 | 0.146218 |
| kepco_morning | 015760 | morning | gap | 5 | 7 | 3/2 | 0 | 0.048165 |
| nhn_morning | 181710 | morning | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| nhn_late_morning | 181710 | late_morning | gap | 6 | 1 | 0/0 | 0 | 0.007046 |
| sd_biosensor_morning | 137310 | morning | pass | 3 | 2 | 0/0 | 0 | 0.141444 |
| sd_biosensor_late_morning | 137310 | late_morning | pass | 1 | 1 | 0/0 | 0 | 0.006488 |
| sd_biosensor_midday | 137310 | midday | pass | 0 | 0 | 0/0 | 0 | None |
| doosan_enerbility_afternoon | 034020 | afternoon | pass | 2 | 4 | 0/0 | 0 | 0.133857 |
| samsung_ea_midday | 028050 | midday | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| sk_telecom_morning | 017670 | morning | pass | 1 | 0 | 0/0 | 0 | 0.0 |
| fan_ocean_morning | 028670 | morning | pass | 1 | 1 | 0/0 | 0 | 0.076652 |
| fan_ocean_late_morning | 028670 | late_morning | gap | 1 | 0 | 0/0 | 2 | 0.0 |
| samsung_heavy_late_morning | 010140 | late_morning | pass | 1 | 1 | 0/0 | 0 | 0.12242 |
| cj_cgv_morning | 079160 | morning | gap | 0 | 0 | 0/0 | 0 | None |
| fan_ocean_afternoon | 028670 | afternoon | pass | 1 | 2 | 0/0 | 0 | 0.105852 |
| youngone_midday | 111770 | midday | gap | 0 | 0 | 0/0 | 0 | None |
| sk_telecom_midday | 017670 | midday | gap | 0 | 0 | 0/0 | 0 | None |

## Next PREOPEN candidate

- No profile/axis mutation; carry forward current policies.
