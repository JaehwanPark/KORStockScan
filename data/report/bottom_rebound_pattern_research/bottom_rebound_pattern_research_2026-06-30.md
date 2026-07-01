# Bottom Rebound Pattern Research - 2026-06-30

- generated_at: `2026-06-30T23:30:27`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57748`
- label_rows: `1443700`
- latest_as_of_candidate_count: `133`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.27492`
- backtest_trade_count: `291`
- backtest_total_return_pct: `302.749426`
- backtest_max_drawdown_pct: `-24.763868`
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
| `signal_close_retest_entry` | `20` | `38695` | `0.670066` | `1.9185` | `1.9185` | `0.489753` | `-17.054674` | `17.252931` |
| `open_guarded_retest_entry` | `20` | `34116` | `0.590774` | `1.637633` | `1.637633` | `0.481563` | `-17.029909` | `16.595246` |
| `next_open_entry` | `20` | `55157` | `0.955133` | `2.126476` | `2.126476` | `0.484834` | `-16.867905` | `17.438094` |
| `close_zone_limit_entry` | `20` | `42220` | `0.731108` | `1.901352` | `1.901352` | `0.486594` | `-16.935108` | `17.039757` |
| `atr_pullback_entry` | `20` | `17958` | `0.310972` | `2.578676` | `2.578676` | `0.518265` | `-17.109494` | `18.041693` |
| `signal_close_retest_entry` | `10` | `39462` | `0.683348` | `0.937445` | `0.937445` | `0.493082` | `-12.759125` | `11.278493` |
| `open_guarded_retest_entry` | `10` | `34623` | `0.599553` | `0.728724` | `0.728724` | `0.483638` | `-12.483645` | `10.74508` |
| `next_open_entry` | `10` | `56111` | `0.971653` | `1.062433` | `1.062433` | `0.492613` | `-12.554113` | `11.384615` |
| `close_zone_limit_entry` | `10` | `43003` | `0.744666` | `0.94099` | `0.94099` | `0.49071` | `-12.6098` | `11.139139` |
| `atr_pullback_entry` | `10` | `18552` | `0.321258` | `1.27492` | `1.27492` | `0.516656` | `-13.433926` | `11.60501` |
| `signal_close_retest_entry` | `5` | `39794` | `0.689097` | `0.379548` | `0.379548` | `0.487134` | `-8.841086` | `7.266142` |
| `open_guarded_retest_entry` | `5` | `34794` | `0.602514` | `0.237072` | `0.237072` | `0.478358` | `-8.626589` | `6.738655` |
| `next_open_entry` | `5` | `56835` | `0.98419` | `0.472258` | `0.472258` | `0.488027` | `-8.723736` | `7.510931` |
| `close_zone_limit_entry` | `5` | `43354` | `0.750745` | `0.394323` | `0.394323` | `0.487014` | `-8.690869` | `7.195319` |
| `atr_pullback_entry` | `5` | `18769` | `0.325016` | `0.426209` | `0.426209` | `0.499654` | `-9.567839` | `7.510856` |
| `signal_close_retest_entry` | `3` | `40081` | `0.694067` | `0.134392` | `0.134392` | `0.484344` | `-6.58902` | `5.237106` |
| `open_guarded_retest_entry` | `3` | `34921` | `0.604714` | `0.009956` | `0.009956` | `0.472409` | `-6.381221` | `4.770648` |
| `next_open_entry` | `3` | `57128` | `0.989264` | `0.22405` | `0.22405` | `0.478119` | `-6.528282` | `5.491676` |
| `close_zone_limit_entry` | `3` | `43642` | `0.755732` | `0.133318` | `0.133318` | `0.483525` | `-6.493506` | `5.185041` |
| `atr_pullback_entry` | `3` | `19048` | `0.329847` | `0.150283` | `0.150283` | `0.49244` | `-7.272738` | `5.456835` |
| `signal_close_retest_entry` | `1` | `40320` | `0.698206` | `-0.05377` | `-0.05377` | `0.470164` | `-3.328183` | `2.705409` |
| `open_guarded_retest_entry` | `1` | `35076` | `0.607398` | `-0.163574` | `-0.163574` | `0.447856` | `-3.208846` | `2.377559` |
| `next_open_entry` | `1` | `57615` | `0.997697` | `0.003321` | `0.003321` | `0.453042` | `-3.492063` | `2.771855` |
| `close_zone_limit_entry` | `1` | `43885` | `0.75994` | `-0.047659` | `-0.047659` | `0.469773` | `-3.305785` | `2.660924` |
| `atr_pullback_entry` | `1` | `19265` | `0.333605` | `-0.125091` | `-0.125091` | `0.466286` | `-3.369261` | `3.350023` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `302.749426`
- max_drawdown_pct: `-24.763868`
- diagnostic_win_rate: `0.508591`
- skipped_capacity_count: `17636`
- skipped_same_symbol_count: `625`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `190.526489` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `302.749426` | `-24.763868` | `0.508591` |
| `exclude_market_risk_off` | `272` | `31.139476` | `-28.407047` | `0.488971` |
| `require_foreign_not_sell` | `291` | `201.237795` | `-23.08101` | `0.501718` |
| `exclude_risk_off_and_foreign_sell` | `272` | `11.521326` | `-39.117181` | `0.492647` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `004990` | 롯데지주 | `22950.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-39.124668` | `1.773836` | `0.642003` | `0.095779` |
| `017800` | 현대엘리베이터 | `71100.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-36.517857` | `6.119403` | `0.495915` | `0.141232` |
| `092200` | 디아이씨 | `4980.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-66.755674` | `1.529052` | `0.454431` | `-0.013864` |
| `103140` | 풍산 | `64400.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-59.547739` | `4.885993` | `0.611825` | `0.077459` |
| `014530` | 극동유화 | `3020.0` |  |  | `market_risk_on` | `inst_buy_only` | `-53.323029` | `2.372881` | `0.419877` | `-0.073764` |
| `003540` | 대신증권 | `27000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.61424` | `6.299213` | `0.437122` | `0.15803` |
| `128820` | 대성산업 | `4375.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-66.704718` | `5.421687` | `0.409834` | `-0.00371` |
| `117580` | 대성에너지 | `6580.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-59.256966` | `2.8125` | `0.554373` | `-0.039979` |
| `005010` | 휴스틸 | `3925.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-46.232877` | `3.698811` | `0.487462` | `0.002367` |
| `008970` | KBI동양철관 | `1213.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.485126` | `4.478898` | `0.823569` | `0.020129` |
| `015760` | 한국전력 | `37000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.457232` | `4.815864` | `0.855247` | `0.025654` |
| `004310` | 현대약품 | `5730.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-62.302632` | `5.914972` | `2.130494` | `-0.012317` |
| `000390` | SP삼화 | `6180.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.959514` | `8.231173` | `0.580887` | `0.07405` |
| `003570` | SNT다이내믹스 | `35050.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.187898` | `5.255255` | `2.499822` | `0.116525` |
| `010660` | 화천기계 | `2770.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-57.966616` | `4.33145` | `0.929415` | `-0.024595` |
| `114090` | GKL | `10320.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-32.327869` | `0.389105` | `0.671643` | `-0.022648` |
| `001040` | CJ | `154700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-34.029851` | `4.315577` | `0.560345` | `0.067905` |
| `105630` | 한세실업 | `8100.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-47.876448` | `3.846154` | `0.722155` | `-0.15086` |
| `006220` | 제주은행 | `9950.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-43.24016` | `8.624454` | `1.099321` | `0.00191` |
| `084680` | 이월드 | `1058.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-46.967419` | `4.545455` | `0.560286` | `-0.030544` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
