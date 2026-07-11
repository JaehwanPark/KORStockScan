# Bottom Rebound Pattern Research - 2026-07-10

- generated_at: `2026-07-10T20:52:54`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58188`
- label_rows: `1454700`
- latest_as_of_candidate_count: `126`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.319436`
- backtest_trade_count: `293`
- backtest_total_return_pct: `259.615115`
- backtest_max_drawdown_pct: `-23.55014`
- kiwoom_enrichment_enabled: `False`
- kiwoom_enrichment_mapped: `0` / `0`
- warnings: `[]`

## Contract

- metric_role: `primary_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- sample_floor: `30`
- forbidden_uses: `['runtime_env_apply', 'broker_order_submit', 'provider_route_change', 'bot_restart_trigger', 'threshold_mutation', 'real_order_conversion_evidence', 'standalone_buy_or_exit_decision']`

## Entry Policy Comparison

| entry_policy | horizon | sample | fill_rate | ev | adjusted_ev | win_rate | mae_p10 | mfe_p80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `signal_close_retest_entry` | `20` | `38854` | `0.667732` | `1.836797` | `1.836797` | `0.488058` | `-17.226655` | `17.22207` |
| `open_guarded_retest_entry` | `20` | `34229` | `0.588248` | `1.602958` | `1.602958` | `0.480937` | `-17.126936` | `16.595839` |
| `next_open_entry` | `20` | `55336` | `0.950986` | `2.054373` | `2.054373` | `0.483176` | `-17.027121` | `17.433414` |
| `close_zone_limit_entry` | `20` | `42374` | `0.728226` | `1.819766` | `1.819766` | `0.484896` | `-17.070899` | `17.01772` |
| `atr_pullback_entry` | `20` | `18128` | `0.311542` | `2.475482` | `2.475482` | `0.515777` | `-17.357761` | `18.066241` |
| `signal_close_retest_entry` | `10` | `39712` | `0.682477` | `0.929008` | `0.929008` | `0.492622` | `-12.834176` | `11.3675` |
| `open_guarded_retest_entry` | `10` | `34745` | `0.597116` | `0.734091` | `0.734091` | `0.483868` | `-12.525591` | `10.778919` |
| `next_open_entry` | `10` | `56713` | `0.974651` | `1.031806` | `1.031806` | `0.490417` | `-12.807104` | `11.472742` |
| `close_zone_limit_entry` | `10` | `43260` | `0.743452` | `0.935633` | `0.935633` | `0.490014` | `-12.708749` | `11.228056` |
| `atr_pullback_entry` | `10` | `18754` | `0.3223` | `1.319436` | `1.319436` | `0.518236` | `-13.479635` | `11.755134` |
| `signal_close_retest_entry` | `5` | `40287` | `0.692359` | `0.390886` | `0.390886` | `0.488793` | `-8.92172` | `7.349335` |
| `open_guarded_retest_entry` | `5` | `35071` | `0.602719` | `0.252862` | `0.252862` | `0.479684` | `-8.670736` | `6.827102` |
| `next_open_entry` | `5` | `57545` | `0.98895` | `0.474259` | `0.474259` | `0.488852` | `-8.819942` | `7.578652` |
| `close_zone_limit_entry` | `5` | `43841` | `0.753437` | `0.40512` | `0.40512` | `0.488493` | `-8.783784` | `7.26879` |
| `atr_pullback_entry` | `5` | `19291` | `0.331529` | `0.46175` | `0.46175` | `0.502929` | `-9.738372` | `7.685396` |
| `signal_close_retest_entry` | `3` | `40451` | `0.695178` | `0.148248` | `0.148248` | `0.485847` | `-6.618532` | `5.297128` |
| `open_guarded_retest_entry` | `3` | `35171` | `0.604437` | `0.027734` | `0.027734` | `0.473998` | `-6.41249` | `4.825201` |
| `next_open_entry` | `3` | `57809` | `0.993487` | `0.223878` | `0.223878` | `0.478403` | `-6.602683` | `5.531915` |
| `close_zone_limit_entry` | `3` | `44011` | `0.756359` | `0.145618` | `0.145618` | `0.484788` | `-6.532785` | `5.25177` |
| `atr_pullback_entry` | `3` | `19352` | `0.332577` | `0.194002` | `0.194002` | `0.495814` | `-7.303763` | `5.600574` |
| `signal_close_retest_entry` | `1` | `40631` | `0.698271` | `-0.045382` | `-0.045382` | `0.471192` | `-3.338348` | `2.727925` |
| `open_guarded_retest_entry` | `1` | `35232` | `0.605486` | `-0.158693` | `-0.158693` | `0.448853` | `-3.214058` | `2.391658` |
| `next_open_entry` | `1` | `58062` | `0.997835` | `0.012429` | `0.012429` | `0.454445` | `-3.508772` | `2.80189` |
| `close_zone_limit_entry` | `1` | `44197` | `0.759555` | `-0.039839` | `-0.039839` | `0.470733` | `-3.31576` | `2.683287` |
| `atr_pullback_entry` | `1` | `19443` | `0.334141` | `-0.116486` | `-0.116486` | `0.467932` | `-3.382216` | `3.37319` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `259.615115`
- max_drawdown_pct: `-23.55014`
- diagnostic_win_rate: `0.508532`
- skipped_capacity_count: `17832`
- skipped_same_symbol_count: `629`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `156.097721` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `259.615115` | `-23.55014` | `0.508532` |
| `exclude_market_risk_off` | `275` | `2.108859` | `-44.255727` | `0.487273` |
| `require_foreign_not_sell` | `293` | `252.335354` | `-23.55014` | `0.505119` |
| `exclude_risk_off_and_foreign_sell` | `275` | `12.763479` | `-38.439052` | `0.494545` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `015760` | 한국전력 | `36200.0` |  |  | `market_risk_on` | `dual_buy` | `-43.7014` | `2.549575` | `0.600261` | `0.016786` |
| `003160` | 디아이 | `22000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-43.589744` | `4.265403` | `1.607679` | `0.071516` |
| `381970` | 케이카 | `7860.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-50.158529` | `0.127389` | `0.82607` | `-0.011383` |
| `249420` | 일동제약 | `15400.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-64.960182` | `3.91363` | `0.711497` | `0.126394` |
| `011170` | 롯데케미칼 | `61800.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-48.284519` | `3.691275` | `0.612256` | `0.077523` |
| `017800` | 현대엘리베이터 | `69500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-37.946429` | `3.731343` | `0.562634` | `0.126731` |
| `012450` | 한화에어로스페이스 | `967000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.570997` | `5.108696` | `1.355797` | `0.020803` |
| `003570` | SNT다이내믹스 | `33500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-46.656051` | `3.875969` | `0.637758` | `0.074312` |
| `005010` | 휴스틸 | `3785.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-48.150685` | `2.853261` | `0.488292` | `0.028101` |
| `004990` | 롯데지주 | `23400.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-37.931034` | `3.769401` | `0.647017` | `0.134324` |
| `001040` | CJ | `142200.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-39.360341` | `3.79562` | `0.98234` | `0.065803` |
| `004560` | 현대비앤지스틸 | `11290.0` |  |  | `market_risk_on` | `dual_buy` | `-49.933481` | `6.509434` | `0.501008` | `0.137188` |
| `008970` | KBI동양철관 | `1160.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-46.910755` | `4.787715` | `0.791855` | `0.056067` |
| `128820` | 대성산업 | `4260.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-67.579909` | `4.411765` | `0.461322` | `0.033047` |
| `007860` | 서연 | `7700.0` |  |  | `market_risk_on` | `dual_buy` | `-32.337434` | `2.941176` | `0.560527` | `0.094579` |
| `034230` | 파라다이스 | `12660.0` |  |  | `market_risk_on` | `dual_buy` | `-42.059497` | `2.593193` | `0.970669` | `0.007503` |
| `439260` | 대한조선 | `48250.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-54.438149` | `1.900739` | `0.816971` | `-0.070994` |
| `103140` | 풍산 | `65100.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-59.10804` | `6.372549` | `1.087623` | `0.091836` |
| `079900` | 전진건설로봇 | `35500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-51.70068` | `4.411765` | `0.646434` | `0.032749` |
| `272450` | 진에어 | `5420.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-27.733333` | `3.238095` | `0.569474` | `0.01249` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
