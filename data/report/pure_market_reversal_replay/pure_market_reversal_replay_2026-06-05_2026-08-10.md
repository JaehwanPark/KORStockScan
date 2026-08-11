# Pure-market reversal replay — 2026-06-05 to 2026-08-10

## Objective

causally enter near the end of a decline and preserve the subsequent rebound through an exit, maximizing cost-adjusted expected value

Historic widget signals, AI decisions, policies, and orders are forbidden inputs. All simulated decisions use completed OHLCV available at that time; future bars are evaluation labels only.

- decision: `research_sample_floor_passed`
- trading dates: `46` / required `46`
- policy grid: `144`
- selection round-trip cost: `0.2%`
- runtime_effect: `false`

## Out-of-sample result

| Cohort | Bars | Qualified dates | Evaluated dates | Trades | Gross EV | Net EV @0.20% | Net win @0.20% | Opportunities captured | Entry vs trough | Exit vs peak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| KRX | 17269 | 46 | 26 | 27 | 0.019014 | -0.180986 | 66.667 | 25/587 | 0.531538 | -0.686937 |
| NXT | 31527 | 46 | 26 | 36 | 0.064759 | -0.135241 | 58.333 | 29/660 | 0.571622 | -0.885367 |

## Interpretation boundary

The report is a formal walk-forward backtest artifact. The operator-selected research floor is 46 coverage-qualified trading days per venue. Passing it does not create runtime or order authority. Historical BBO and signed tape are not imputed; costs are reported as sensitivity scenarios. Ex-post trough labels measure missed opportunities but never select a same-day policy or decision.
