# Bottom Rebound Pattern Research - 2026-07-27

- generated_at: `2026-07-27T20:57:59`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58888`
- label_rows: `1472200`
- latest_as_of_candidate_count: `108`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.295732`
- backtest_trade_count: `294`
- backtest_total_return_pct: `183.048855`
- backtest_max_drawdown_pct: `-29.406991`
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
| `signal_close_retest_entry` | `20` | `39299` | `0.667352` | `1.737293` | `1.737293` | `0.484084` | `-17.596513` | `17.201256` |
| `open_guarded_retest_entry` | `20` | `34557` | `0.586826` | `1.480788` | `1.480788` | `0.477501` | `-17.39051` | `16.582915` |
| `next_open_entry` | `20` | `55887` | `0.949039` | `1.958094` | `1.958094` | `0.479825` | `-17.391304` | `17.415115` |
| `close_zone_limit_entry` | `20` | `42834` | `0.727381` | `1.722175` | `1.722175` | `0.481136` | `-17.429313` | `17.01772` |
| `atr_pullback_entry` | `20` | `18466` | `0.313578` | `2.289439` | `2.289439` | `0.508827` | `-17.99125` | `17.968196` |
| `signal_close_retest_entry` | `10` | `40285` | `0.684095` | `0.930427` | `0.930427` | `0.492119` | `-12.937709` | `11.43313` |
| `open_guarded_retest_entry` | `10` | `35086` | `0.595809` | `0.737459` | `0.737459` | `0.484353` | `-12.585696` | `10.823238` |
| `next_open_entry` | `10` | `57542` | `0.977143` | `1.006883` | `1.006883` | `0.489312` | `-12.948261` | `11.522251` |
| `close_zone_limit_entry` | `10` | `43844` | `0.744532` | `0.936888` | `0.936888` | `0.489714` | `-12.827234` | `11.299175` |
| `atr_pullback_entry` | `10` | `19268` | `0.327197` | `1.295732` | `1.295732` | `0.516556` | `-13.658337` | `11.839034` |
| `signal_close_retest_entry` | `5` | `40753` | `0.692043` | `0.374492` | `0.374492` | `0.487449` | `-9.01529` | `7.372915` |
| `open_guarded_retest_entry` | `5` | `35305` | `0.599528` | `0.235867` | `0.235867` | `0.478714` | `-8.712655` | `6.839667` |
| `next_open_entry` | `5` | `58186` | `0.988079` | `0.460872` | `0.460872` | `0.487282` | `-8.940926` | `7.594937` |
| `close_zone_limit_entry` | `5` | `44325` | `0.7527` | `0.391911` | `0.391911` | `0.487377` | `-8.884573` | `7.289125` |
| `atr_pullback_entry` | `5` | `19526` | `0.331579` | `0.421542` | `0.421542` | `0.500615` | `-9.841091` | `7.700282` |
| `signal_close_retest_entry` | `3` | `40975` | `0.695812` | `0.156484` | `0.156484` | `0.486052` | `-6.666667` | `5.347329` |
| `open_guarded_retest_entry` | `3` | `35401` | `0.601158` | `0.027508` | `0.027508` | `0.473941` | `-6.428695` | `4.837124` |
| `next_open_entry` | `3` | `58523` | `0.993802` | `0.234977` | `0.234977` | `0.478547` | `-6.666667` | `5.585394` |
| `close_zone_limit_entry` | `3` | `44557` | `0.75664` | `0.154568` | `0.154568` | `0.485087` | `-6.577239` | `5.300875` |
| `atr_pullback_entry` | `3` | `19672` | `0.334058` | `0.187695` | `0.187695` | `0.494052` | `-7.361835` | `5.673775` |
| `signal_close_retest_entry` | `1` | `41067` | `0.697375` | `-0.039479` | `-0.039479` | `0.472253` | `-3.350067` | `2.744597` |
| `open_guarded_retest_entry` | `1` | `35455` | `0.602075` | `-0.158556` | `-0.158556` | `0.449274` | `-3.215158` | `2.398786` |
| `next_open_entry` | `1` | `58780` | `0.998166` | `0.024434` | `0.024434` | `0.456039` | `-3.524497` | `2.820513` |
| `close_zone_limit_entry` | `1` | `44658` | `0.758355` | `-0.034099` | `-0.034099` | `0.471763` | `-3.324145` | `2.697997` |
| `atr_pullback_entry` | `1` | `19706` | `0.334635` | `-0.109091` | `-0.109091` | `0.469299` | `-3.403297` | `3.380539` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `294`
- total_return_pct: `183.048855`
- max_drawdown_pct: `-29.406991`
- diagnostic_win_rate: `0.506803`
- skipped_capacity_count: `18330`
- skipped_same_symbol_count: `644`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `101.836593` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `294` | `183.048855` | `-29.406991` | `0.506803` |
| `exclude_market_risk_off` | `272` | `11.7002` | `-39.019528` | `0.492647` |
| `require_foreign_not_sell` | `294` | `178.320668` | `-29.063981` | `0.503401` |
| `exclude_risk_off_and_foreign_sell` | `272` | `16.348081` | `-36.482111` | `0.5` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `128820` | 대성산업 | `4020.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.406393` | `1.772152` | `1.029874` | `0.080869` |
| `066970` | 엘앤에프 | `81500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-63.777778` | `1.242236` | `0.502167` | `0.029979` |
| `489790` | 한화비전 | `41750.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.864865` | `4.375` | `0.555709` | `0.168981` |
| `011210` | 현대위아 | `56000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.89372` | `4.868914` | `0.616249` | `0.106783` |
| `003530` | 한화투자증권 | `4310.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.455724` | `4.86618` | `0.58042` | `0.079684` |
| `084670` | 동양고속 | `23500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-67.808219` | `2.620087` | `0.477494` | `-0.00501` |
| `003540` | 대신증권 | `26000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.739639` | `4.417671` | `0.701088` | `0.065215` |
| `005070` | 코스모신소재 | `35100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.330275` | `4.61997` | `0.651908` | `0.069979` |
| `000390` | SP삼화 | `5990.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.497976` | `4.903678` | `0.715288` | `0.070526` |
| `002710` | TCC스틸 | `8860.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.394336` | `4.728132` | `0.410517` | `0.124808` |
| `020150` | 롯데에너지머티리얼즈 | `29400.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-64.620939` | `2.977233` | `0.970411` | `0.023808` |
| `010960` | 삼호개발 | `3065.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.272727` | `2.680067` | `0.903492` | `0.00399` |
| `002220` | 한일철강 | `3010.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.477589` | `3.082192` | `0.717089` | `0.04514` |
| `016610` | DB증권 | `8870.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.469523` | `3.259604` | `0.715983` | `0.061688` |
| `008970` | KBI동양철관 | `1102.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.565217` | `6.268081` | `0.462887` | `0.078633` |
| `039490` | 키움증권 | `300000.0` |  |  | `market_risk_off` | `inst_buy_only` | `-38.016529` | `1.010101` | `0.586389` | `-0.004741` |
| `019170` | 신풍제약 | `7830.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.348315` | `3.571429` | `0.928224` | `0.090366` |
| `005880` | 대한해운 | `1806.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.173107` | `2.555366` | `0.882943` | `0.038603` |
| `117580` | 대성에너지 | `7020.0` |  |  | `market_risk_off` | `dual_buy` | `-56.532508` | `9.6875` | `1.023889` | `0.041906` |
| `249420` | 일동제약 | `14060.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-65.111663` | `6.920152` | `0.507189` | `0.1491` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
