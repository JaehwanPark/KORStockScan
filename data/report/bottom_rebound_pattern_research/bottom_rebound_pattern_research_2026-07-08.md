# Bottom Rebound Pattern Research - 2026-07-08

- generated_at: `2026-07-08T20:53:22`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57948`
- label_rows: `1448700`
- latest_as_of_candidate_count: `175`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.29015`
- backtest_trade_count: `293`
- backtest_total_return_pct: `149.70094`
- backtest_max_drawdown_pct: `-34.502188`
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
| `signal_close_retest_entry` | `20` | `38781` | `0.669238` | `1.854069` | `1.854069` | `0.488151` | `-17.192691` | `17.232123` |
| `open_guarded_retest_entry` | `20` | `34176` | `0.58977` | `1.603999` | `1.603999` | `0.480542` | `-17.125614` | `16.582915` |
| `next_open_entry` | `20` | `55147` | `0.951664` | `2.087592` | `2.087592` | `0.483707` | `-16.981866` | `17.401961` |
| `close_zone_limit_entry` | `20` | `42296` | `0.729896` | `1.839115` | `1.839115` | `0.48501` | `-17.049329` | `17.028739` |
| `atr_pullback_entry` | `20` | `18069` | `0.311814` | `2.465697` | `2.465697` | `0.515635` | `-17.336569` | `18.0389` |
| `signal_close_retest_entry` | `10` | `39647` | `0.684182` | `0.935502` | `0.935502` | `0.492698` | `-12.807916` | `11.367649` |
| `open_guarded_retest_entry` | `10` | `34679` | `0.59845` | `0.730031` | `0.730031` | `0.483866` | `-12.511287` | `10.770617` |
| `next_open_entry` | `10` | `56492` | `0.974874` | `1.028358` | `1.028358` | `0.490795` | `-12.744792` | `11.463415` |
| `close_zone_limit_entry` | `10` | `43188` | `0.745289` | `0.942983` | `0.942983` | `0.490136` | `-12.674693` | `11.235102` |
| `atr_pullback_entry` | `10` | `18707` | `0.322824` | `1.29015` | `1.29015` | `0.517186` | `-13.488241` | `11.735711` |
| `signal_close_retest_entry` | `5` | `40235` | `0.694329` | `0.389827` | `0.389827` | `0.488381` | `-8.919598` | `7.342009` |
| `open_guarded_retest_entry` | `5` | `35023` | `0.604387` | `0.249809` | `0.249809` | `0.479142` | `-8.664871` | `6.811824` |
| `next_open_entry` | `5` | `57172` | `0.986609` | `0.479889` | `0.479889` | `0.488963` | `-8.784383` | `7.559395` |
| `close_zone_limit_entry` | `5` | `43784` | `0.755574` | `0.404706` | `0.404706` | `0.488169` | `-8.783506` | `7.260557` |
| `atr_pullback_entry` | `5` | `19244` | `0.332091` | `0.45047` | `0.45047` | `0.501819` | `-9.759407` | `7.665315` |
| `signal_close_retest_entry` | `3` | `40331` | `0.695986` | `0.147657` | `0.147657` | `0.485557` | `-6.610995` | `5.294826` |
| `open_guarded_retest_entry` | `3` | `35077` | `0.605319` | `0.024505` | `0.024505` | `0.473587` | `-6.410775` | `4.812553` |
| `next_open_entry` | `3` | `57564` | `0.993373` | `0.226525` | `0.226525` | `0.478893` | `-6.58081` | `5.531915` |
| `close_zone_limit_entry` | `3` | `43888` | `0.757369` | `0.145488` | `0.145488` | `0.484666` | `-6.52697` | `5.249711` |
| `atr_pullback_entry` | `3` | `19282` | `0.332747` | `0.18207` | `0.18207` | `0.494866` | `-7.303763` | `5.583682` |
| `signal_close_retest_entry` | `1` | `40489` | `0.698713` | `-0.050637` | `-0.050637` | `0.470869` | `-3.336599` | `2.716224` |
| `open_guarded_retest_entry` | `1` | `35165` | `0.606837` | `-0.157481` | `-0.157481` | `0.44914` | `-3.20935` | `2.387116` |
| `next_open_entry` | `1` | `57773` | `0.99698` | `0.002618` | `0.002618` | `0.45298` | `-3.508772` | `2.783726` |
| `close_zone_limit_entry` | `1` | `44047` | `0.760113` | `-0.045204` | `-0.045204` | `0.470316` | `-3.315101` | `2.670541` |
| `atr_pullback_entry` | `1` | `19377` | `0.334386` | `-0.118274` | `-0.118274` | `0.468081` | `-3.382288` | `3.36611` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `149.70094`
- max_drawdown_pct: `-34.502188`
- diagnostic_win_rate: `0.505119`
- skipped_capacity_count: `17781`
- skipped_same_symbol_count: `633`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `79.027109` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `149.70094` | `-34.502188` | `0.505119` |
| `exclude_market_risk_off` | `275` | `7.025575` | `-41.571545` | `0.490909` |
| `require_foreign_not_sell` | `293` | `167.18656` | `-27.636917` | `0.505119` |
| `exclude_risk_off_and_foreign_sell` | `274` | `21.348872` | `-33.75203` | `0.50365` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `011170` | 롯데케미칼 | `60700.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.205021` | `1.845638` | `0.734602` | `0.078529` |
| `011500` | 한농화성 | `11960.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-57.055655` | `0.92827` | `0.788445` | `0.09529` |
| `100840` | SNT에너지 | `23800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-63.774734` | `0.634249` | `0.800618` | `0.089679` |
| `103140` | 풍산 | `62500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.741206` | `1.791531` | `0.722229` | `0.090351` |
| `001430` | 세아베스틸지주 | `30150.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.405405` | `1.515152` | `0.455257` | `0.061459` |
| `003160` | 디아이 | `21250.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.512821` | `1.190476` | `0.663871` | `0.069734` |
| `489790` | 한화비전 | `42900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.621622` | `2.631579` | `1.074618` | `0.141727` |
| `128820` | 대성산업 | `4165.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-68.302892` | `2.083333` | `0.512876` | `-0.003877` |
| `005010` | 휴스틸 | `3745.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.69863` | `1.216216` | `0.940269` | `0.026238` |
| `008970` | KBI동양철관 | `1124.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.558352` | `0.178253` | `0.963526` | `0.033404` |
| `011690` | 와이투솔루션 | `2915.0` |  |  | `market_risk_off` | `dual_buy` | `-70.555556` | `1.215278` | `0.918574` | `0.038959` |
| `015760` | 한국전력 | `36750.0` |  |  | `market_risk_off` | `dual_buy` | `-42.846034` | `4.107649` | `0.812225` | `0.016592` |
| `002710` | TCC스틸 | `8950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.002179` | `1.473923` | `0.716075` | `0.082561` |
| `450080` | 에코프로머티 | `35850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-59.628378` | `1.558074` | `1.075615` | `0.034853` |
| `454910` | 두산로보틱스 | `72500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.193353` | `1.398601` | `0.676584` | `0.105185` |
| `035510` | 신세계 I&C | `12460.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-57.474403` | `2.047502` | `0.434961` | `-0.009432` |
| `003530` | 한화투자증권 | `4485.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.565875` | `1.013514` | `0.998975` | `0.018327` |
| `004560` | 현대비앤지스틸 | `10920.0` |  |  | `market_risk_off` | `dual_buy` | `-51.574279` | `3.018868` | `0.977626` | `0.115303` |
| `001780` | 알루코 | `1573.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.992847` | `0.127307` | `0.757073` | `0.01851` |
| `037560` | LG헬로비전 | `1552.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.692058` | `0.453074` | `0.669362` | `-0.004542` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
