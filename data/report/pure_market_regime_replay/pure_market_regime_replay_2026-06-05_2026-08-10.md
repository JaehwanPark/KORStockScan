# Pure-market regime replay — 2026-06-05 to 2026-08-10

## Decision

- decision: `krx_research_sample_floor_passed_nxt_context_limited`
- qualified trading dates: `46` / required `46`
- round-trip selection cost: `0.20%`
- runtime_effect: `false`

## Regime-conditioned out-of-sample result

| Venue | Mode | Trades | Gross EV | Net EV @ cost | Source-quality adjusted EV | Gross win rate | Source quality |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | weak_capitulation | 19 | 0.03948 | -0.16052 | -0.16052 | 63.158 | PASS |
| KRX | bullish_recovery | 46 | -0.077608 | -0.277608 | -0.277608 | 36.957 | PASS |
| NXT | weak_capitulation | 9 | 0.334955 | 0.134955 | None | 88.889 | PARTIAL_CONTEXT |
| NXT | bullish_recovery | 37 | -0.018456 | -0.218456 | None | 43.243 | PARTIAL_CONTEXT |

## Combined controller and opportunity capture

| Venue | Trades | Gross EV | Net EV @ cost | Opportunity capture | Exit vs rebound peak | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 62 | -0.037338 | -0.237338 | 8.859 | -0.91213 | research_sample_floor_passed |
| NXT | 46 | 0.05069 | -0.14931 | 6.061 | -1.11211 | insufficient_for_strategy_or_runtime_judgment |

The regime split is structurally valid only as an offline causal experiment. Negative KRX cost-adjusted EV or a source-quality/sample-floor failure blocks strategy promotion even when an individual episode is favorable.

## Boundary

Regimes use completed timestamp-exact 3/5/15-minute Samsung and aligned KOSPI bars plus session VWAP. Bullish and bearish transition labels compare short and long windows available at that timestamp; future bars never assign a regime. NXT premarket/aftermarket are explicitly instrument-only, while NXT regular may use timestamp-aligned KOSPI context.
