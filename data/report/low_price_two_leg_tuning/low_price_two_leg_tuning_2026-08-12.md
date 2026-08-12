# Low-price two-leg tuning — 2026-08-12

- Decision: profile-separated actual broker outcomes; next-PREOPEN bounded tightening only.
- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.
- Clean-baseline actual observations: 2/48 trading dates; missing dates are coverage only and are not imputed.

| Profile | Symbol | Session | Daily status | Clean cumulative attempts | Complete legs | Held/unresolved | EV |
|---|---|---|---|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | pass | 0 | 0 | 0 | None |
| samsung_heavy_afternoon | 010140 | afternoon | pass | 0 | 0 | 0 | None |
| sk_eternix_midday | 475150 | midday | pass | 0 | 0 | 0 | None |
| mirae_asset_morning | 006800 | morning | gap | 0 | 0 | 0 | None |
| jeju_semiconductor_morning | 080220 | morning | gap | 0 | 0 | 0 | None |
| doosan_enerbility_morning | 034020 | morning | gap | 0 | 0 | 0 | None |
| hanwha_ocean_late_morning | 042660 | late_morning | gap | 0 | 0 | 0 | None |
| kakao_morning | 035720 | morning | gap | 0 | 0 | 0 | None |
| kepco_afternoon | 015760 | afternoon | gap | 0 | 0 | 0 | None |
| kakao_late_morning | 035720 | late_morning | gap | 0 | 0 | 0 | None |
| sk_eternix_morning | 475150 | morning | gap | 0 | 0 | 0 | None |
| mirae_asset_midday | 006800 | midday | gap | 0 | 0 | 0 | None |
| sk_eternix_afternoon | 475150 | afternoon | gap | 0 | 0 | 0 | None |

## Next PREOPEN candidate

- No profile/axis mutation; carry forward current policies.
