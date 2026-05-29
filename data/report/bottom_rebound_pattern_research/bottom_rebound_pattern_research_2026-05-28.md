# Bottom Rebound Pattern Research - 2026-05-28

- generated_at: `2026-05-29T13:33:40`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56719`
- label_rows: `1417975`
- latest_as_of_candidate_count: `165`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.423559`
- backtest_trade_count: `293`
- backtest_total_return_pct: `26.629462`
- backtest_max_drawdown_pct: `-23.595563`
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
| `signal_close_retest_entry` | `20` | `38816` | `0.684356` | `1.574476` | `1.574476` | `0.491885` | `-16.885847` | `17.170008` |
| `open_guarded_retest_entry` | `20` | `34283` | `0.604436` | `1.398209` | `1.398209` | `0.483359` | `-16.870464` | `16.532728` |
| `next_open_entry` | `20` | `55344` | `0.975758` | `1.807384` | `1.807384` | `0.487858` | `-16.606958` | `17.336808` |
| `close_zone_limit_entry` | `20` | `42347` | `0.74661` | `1.566566` | `1.566566` | `0.488842` | `-16.772181` | `16.985034` |
| `atr_pullback_entry` | `20` | `18025` | `0.317795` | `2.231259` | `2.231259` | `0.519723` | `-16.869191` | `17.953508` |
| `signal_close_retest_entry` | `10` | `39083` | `0.689064` | `0.98949` | `0.98949` | `0.501676` | `-12.16669` | `11.235129` |
| `open_guarded_retest_entry` | `10` | `34479` | `0.607892` | `0.770273` | `0.770273` | `0.489573` | `-12.093666` | `10.723107` |
| `next_open_entry` | `10` | `55849` | `0.984661` | `1.154207` | `1.154207` | `0.501441` | `-11.957866` | `11.358575` |
| `close_zone_limit_entry` | `10` | `42630` | `0.7516` | `0.980689` | `0.980689` | `0.498639` | `-12.080535` | `11.110794` |
| `atr_pullback_entry` | `10` | `18163` | `0.320228` | `1.423559` | `1.423559` | `0.532676` | `-12.549387` | `11.56185` |
| `signal_close_retest_entry` | `5` | `39300` | `0.69289` | `0.3642` | `0.3642` | `0.490407` | `-8.546155` | `7.143015` |
| `open_guarded_retest_entry` | `5` | `34624` | `0.610448` | `0.233029` | `0.233029` | `0.481198` | `-8.404797` | `6.679252` |
| `next_open_entry` | `5` | `56134` | `0.989686` | `0.524102` | `0.524102` | `0.493783` | `-8.324269` | `7.37271` |
| `close_zone_limit_entry` | `5` | `42856` | `0.755585` | `0.385103` | `0.385103` | `0.48985` | `-8.41266` | `7.075448` |
| `atr_pullback_entry` | `5` | `18330` | `0.323172` | `0.402113` | `0.402113` | `0.504201` | `-9.203726` | `7.331472` |
| `signal_close_retest_entry` | `3` | `39466` | `0.695816` | `0.145446` | `0.145446` | `0.486469` | `-6.349931` | `5.14109` |
| `open_guarded_retest_entry` | `3` | `34734` | `0.612387` | `0.020293` | `0.020293` | `0.474549` | `-6.256601` | `4.741171` |
| `next_open_entry` | `3` | `56316` | `0.992895` | `0.241393` | `0.241393` | `0.480006` | `-6.299421` | `5.384615` |
| `close_zone_limit_entry` | `3` | `43024` | `0.758547` | `0.145338` | `0.145338` | `0.485171` | `-6.28607` | `5.11135` |
| `atr_pullback_entry` | `3` | `18454` | `0.325358` | `0.174181` | `0.174181` | `0.496694` | `-6.871078` | `5.336672` |
| `signal_close_retest_entry` | `1` | `39622` | `0.698567` | `-0.048153` | `-0.048153` | `0.472212` | `-3.24826` | `2.665598` |
| `open_guarded_retest_entry` | `1` | `34836` | `0.614186` | `-0.158278` | `-0.158278` | `0.450023` | `-3.155689` | `2.366325` |
| `next_open_entry` | `1` | `56554` | `0.997091` | `0.021594` | `0.021594` | `0.456272` | `-3.4` | `2.734038` |
| `close_zone_limit_entry` | `1` | `43186` | `0.761403` | `-0.042444` | `-0.042444` | `0.471657` | `-3.225806` | `2.616349` |
| `atr_pullback_entry` | `1` | `18577` | `0.327527` | `-0.129236` | `-0.129236` | `0.468429` | `-3.262163` | `3.306814` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `26.629462`
- max_drawdown_pct: `-23.595563`
- diagnostic_win_rate: `0.515358`
- skipped_capacity_count: `17244`
- skipped_same_symbol_count: `626`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-9.163354` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `26.629462` | `-23.595563` | `0.515358` |
| `exclude_market_risk_off` | `275` | `26.108442` | `-31.153639` | `0.494545` |
| `require_foreign_not_sell` | `293` | `37.270155` | `-23.08101` | `0.518771` |
| `exclude_risk_off_and_foreign_sell` | `275` | `32.936364` | `-27.426073` | `0.501818` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `272550` | 삼양패키징 | `9860.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.785633` | `0.612245` | `0.400552` | `-0.015416` |
| `000120` | CJ대한통운 | `85500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.54242` | `2.764423` | `1.215685` | `0.019696` |
| `009580` | 무림P&P | `2090.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.714932` | `2.200489` | `0.457467` | `0.013012` |
| `950210` | 프레스티지바이오파마 | `7110.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.775216` | `2.449568` | `1.149083` | `0.013638` |
| `003350` | 한국화장품제조 | `8840.0` |  |  | `market_risk_off` | `dual_buy` | `-82.967245` | `4.122497` | `1.234894` | `0.054541` |
| `004310` | 현대약품 | `6940.0` |  |  | `market_risk_off` | `inst_buy_only` | `-54.788274` | `3.27381` | `0.762618` | `-0.040542` |
| `103140` | 풍산 | `82500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.178392` | `3.254068` | `0.738491` | `0.007401` |
| `192650` | 드림텍 | `5040.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-41.121495` | `3.278689` | `1.199001` | `-0.009772` |
| `007570` | 일양약품 | `9080.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.08867` | `1.793722` | `1.115809` | `-0.146758` |
| `029780` | 삼성카드 | `46950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-32.153179` | `1.954397` | `1.511183` | `0.048694` |
| `381970` | 케이카 | `9300.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.602183` | `3.104213` | `0.973546` | `-0.141032` |
| `037270` | YG PLUS | `3935.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-48.291721` | `2.741514` | `1.104433` | `-0.063154` |
| `128820` | 대성산업 | `6030.0` |  |  | `market_risk_off` | `inst_buy_only` | `-54.109589` | `1.344538` | `1.243349` | `-0.010639` |
| `009240` | 한샘 | `30700.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.52381` | `3.891709` | `1.125272` | `0.025055` |
| `006220` | 제주은행 | `10270.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.488323` | `3.11245` | `1.11356` | `-0.042377` |
| `352820` | 하이브 | `223500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.814815` | `0.675676` | `1.322272` | `-0.115236` |
| `005870` | 휴니드 | `6480.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.167939` | `2.857143` | `0.64661` | `0.020549` |
| `105630` | 한세실업 | `9190.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-40.862291` | `3.490991` | `1.385902` | `-0.026813` |
| `003520` | 영진약품 | `1350.0` |  |  | `market_risk_off` | `inst_buy_only` | `-41.810345` | `1.580135` | `1.203111` | `-0.098227` |
| `001680` | 대상 | `19100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-20.910973` | `1.866667` | `0.908334` | `0.129602` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
