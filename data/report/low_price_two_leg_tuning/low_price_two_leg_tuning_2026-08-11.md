# Low-price two-leg tuning — 2026-08-11

- Decision: profile-separated actual broker outcomes; next-PREOPEN bounded tightening only.
- No market-history query, cross-profile pooling, stop loss, forced exit, quantity, target, or validity change.

| Profile | Symbol | Session | Daily status | Cumulative attempts | Complete legs | Held/unresolved | EV |
|---|---|---|---|---:|---:|---:|---:|
| samsung_heavy_midday | 010140 | midday | gap | 0 | 0 | 0 | None |
| samsung_heavy_afternoon | 010140 | afternoon | gap | 0 | 0 | 0 | None |
| sk_eternix_midday | 475150 | midday | gap | 0 | 0 | 0 | None |

## Next PREOPEN candidate

- No profile/axis mutation; carry forward current policies.
