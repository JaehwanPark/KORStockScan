# Bottom Rebound Pattern Research - 2026-07-16

- generated_at: `2026-07-16T20:54:22`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58610`
- label_rows: `1465250`
- latest_as_of_candidate_count: `148`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.255395`
- backtest_trade_count: `293`
- backtest_total_return_pct: `194.21366`
- backtest_max_drawdown_pct: `-24.93578`
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
| `signal_close_retest_entry` | `20` | `39064` | `0.666507` | `1.772839` | `1.772839` | `0.486561` | `-17.372471` | `17.217597` |
| `open_guarded_retest_entry` | `20` | `34383` | `0.586641` | `1.539794` | `1.539794` | `0.479743` | `-17.235339` | `16.594274` |
| `next_open_entry` | `20` | `55588` | `0.948439` | `2.008868` | `2.008868` | `0.482244` | `-17.132616` | `17.4359` |
| `close_zone_limit_entry` | `20` | `42594` | `0.726736` | `1.760367` | `1.760367` | `0.483472` | `-17.219156` | `17.017946` |
| `atr_pullback_entry` | `20` | `18241` | `0.311227` | `2.353554` | `2.353554` | `0.513623` | `-17.611369` | `18.008785` |
| `signal_close_retest_entry` | `10` | `39921` | `0.68113` | `0.909591` | `0.909591` | `0.491871` | `-12.898551` | `11.380145` |
| `open_guarded_retest_entry` | `10` | `34904` | `0.59553` | `0.718668` | `0.718668` | `0.48344` | `-12.576582` | `10.790171` |
| `next_open_entry` | `10` | `56956` | `0.97178` | `1.006879` | `1.006879` | `0.490098` | `-12.868523` | `11.479945` |
| `close_zone_limit_entry` | `10` | `43476` | `0.741785` | `0.917991` | `0.917991` | `0.489534` | `-12.778779` | `11.243612` |
| `atr_pullback_entry` | `10` | `18889` | `0.322283` | `1.255395` | `1.255395` | `0.515326` | `-13.59837` | `11.718123` |
| `signal_close_retest_entry` | `5` | `40499` | `0.690991` | `0.366891` | `0.366891` | `0.487494` | `-8.956001` | `7.348578` |
| `open_guarded_retest_entry` | `5` | `35207` | `0.6007` | `0.2369` | `0.2369` | `0.479024` | `-8.686093` | `6.82709` |
| `next_open_entry` | `5` | `57886` | `0.987647` | `0.449032` | `0.449032` | `0.487562` | `-8.87473` | `7.567568` |
| `close_zone_limit_entry` | `5` | `44065` | `0.751834` | `0.384216` | `0.384216` | `0.487394` | `-8.82951` | `7.267981` |
| `atr_pullback_entry` | `5` | `19339` | `0.329961` | `0.418014` | `0.418014` | `0.501008` | `-9.78984` | `7.672943` |
| `signal_close_retest_entry` | `3` | `40680` | `0.69408` | `0.137753` | `0.137753` | `0.48498` | `-6.637523` | `5.313235` |
| `open_guarded_retest_entry` | `3` | `35268` | `0.60174` | `0.021584` | `0.021584` | `0.473687` | `-6.414664` | `4.827416` |
| `next_open_entry` | `3` | `58141` | `0.991998` | `0.219107` | `0.219107` | `0.477821` | `-6.621005` | `5.555556` |
| `close_zone_limit_entry` | `3` | `44252` | `0.755025` | `0.136926` | `0.136926` | `0.484023` | `-6.546256` | `5.270767` |
| `atr_pullback_entry` | `3` | `19431` | `0.33153` | `0.166686` | `0.166686` | `0.49313` | `-7.336079` | `5.600416` |
| `signal_close_retest_entry` | `1` | `40888` | `0.697628` | `-0.047116` | `-0.047116` | `0.471165` | `-3.350041` | `2.732053` |
| `open_guarded_retest_entry` | `1` | `35379` | `0.603634` | `-0.160096` | `-0.160096` | `0.448854` | `-3.217293` | `2.394163` |
| `next_open_entry` | `1` | `58462` | `0.997475` | `0.007035` | `0.007035` | `0.453594` | `-3.526642` | `2.8` |
| `close_zone_limit_entry` | `1` | `44471` | `0.758761` | `-0.041713` | `-0.041713` | `0.470666` | `-3.323263` | `2.688953` |
| `atr_pullback_entry` | `1` | `19558` | `0.333697` | `-0.120307` | `-0.120307` | `0.467175` | `-3.405675` | `3.375512` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `194.21366`
- max_drawdown_pct: `-24.93578`
- diagnostic_win_rate: `0.505119`
- skipped_capacity_count: `17958`
- skipped_same_symbol_count: `638`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `109.905633` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `194.21366` | `-24.93578` | `0.505119` |
| `exclude_market_risk_off` | `275` | `12.693304` | `-38.477363` | `0.490909` |
| `require_foreign_not_sell` | `293` | `199.084749` | `-23.08101` | `0.501706` |
| `exclude_risk_off_and_foreign_sell` | `275` | `15.805234` | `-36.778468` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `103140` | 풍산 | `62100.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-60.992462` | `3.327787` | `0.48796` | `0.120842` |
| `008730` | 율촌화학 | `13480.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-53.835616` | `1.735849` | `0.445329` | `0.075954` |
| `011170` | 롯데케미칼 | `61000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-48.953975` | `3.918228` | `0.773646` | `0.091585` |
| `003540` | 대신증권 | `25850.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.058448` | `3.815261` | `0.66116` | `0.0813` |
| `010780` | 아이에스동서 | `18510.0` |  |  | `market_risk_on` | `dual_buy` | `-45.718475` | `0.597826` | `1.061268` | `0.065848` |
| `004990` | 롯데지주 | `22800.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-39.522546` | `1.108647` | `0.606398` | `0.181342` |
| `022100` | 포스코DX | `18630.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-55.905325` | `0.92091` | `0.837701` | `0.063348` |
| `017800` | 현대엘리베이터 | `68900.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-38.482143` | `2.835821` | `0.556295` | `0.0807` |
| `000490` | 대동 | `6690.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-50.953079` | `2.607362` | `0.543999` | `0.048011` |
| `128820` | 대성산업 | `4070.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-69.025875` | `1.369863` | `0.513754` | `0.060847` |
| `064350` | 현대로템 | `159000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.328413` | `1.209421` | `0.867109` | `0.11951` |
| `011210` | 현대위아 | `57600.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.347826` | `3.225806` | `0.477037` | `0.139142` |
| `034230` | 파라다이스 | `10190.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-53.363844` | `2.104208` | `2.801078` | `0.078467` |
| `001040` | CJ | `135700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.132196` | `3.193916` | `0.716045` | `0.04424` |
| `001780` | 알루코 | `1621.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-53.619456` | `3.314213` | `0.400925` | `-0.002514` |
| `100840` | SNT에너지 | `24750.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-62.328767` | `4.651163` | `0.580076` | `0.095467` |
| `052690` | 한전기술 | `92700.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-52.944162` | `2.430939` | `0.574026` | `-0.031374` |
| `005010` | 휴스틸 | `3670.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.726027` | `3.23488` | `0.431654` | `0.050723` |
| `015760` | 한국전력 | `34050.0` |  |  | `market_risk_on` | `dual_buy` | `-47.045101` | `2.560241` | `0.8461` | `0.039324` |
| `004020` | 현대제철 | `26550.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-47.111554` | `3.106796` | `0.601455` | `-0.019659` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
