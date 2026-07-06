# Bottom Rebound Pattern Research - 2026-07-06

- generated_at: `2026-07-06T20:52:46`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57773`
- label_rows: `1444325`
- latest_as_of_candidate_count: `78`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.292905`
- backtest_trade_count: `291`
- backtest_total_return_pct: `154.717946`
- backtest_max_drawdown_pct: `-33.186202`
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
| `signal_close_retest_entry` | `20` | `38724` | `0.670279` | `1.873654` | `1.873654` | `0.488663` | `-17.141163` | `17.234705` |
| `open_guarded_retest_entry` | `20` | `34137` | `0.590882` | `1.618874` | `1.618874` | `0.480915` | `-17.091556` | `16.587118` |
| `next_open_entry` | `20` | `55085` | `0.953473` | `2.104839` | `2.104839` | `0.484125` | `-16.942839` | `17.405167` |
| `close_zone_limit_entry` | `20` | `42238` | `0.731103` | `1.857579` | `1.857579` | `0.485511` | `-17.006745` | `17.030569` |
| `atr_pullback_entry` | `20` | `18018` | `0.311876` | `2.502993` | `2.502993` | `0.516706` | `-17.250594` | `18.041693` |
| `signal_close_retest_entry` | `10` | `39622` | `0.685822` | `0.939803` | `0.939803` | `0.492858` | `-12.789094` | `11.365679` |
| `open_guarded_retest_entry` | `10` | `34667` | `0.600055` | `0.732577` | `0.732577` | `0.483976` | `-12.491554` | `10.771038` |
| `next_open_entry` | `10` | `56307` | `0.974625` | `1.055408` | `1.055408` | `0.491857` | `-12.650208` | `11.45955` |
| `close_zone_limit_entry` | `10` | `43160` | `0.747062` | `0.947668` | `0.947668` | `0.490338` | `-12.660194` | `11.232843` |
| `atr_pullback_entry` | `10` | `18701` | `0.323698` | `1.292905` | `1.292905` | `0.517245` | `-13.481698` | `11.736019` |
| `signal_close_retest_entry` | `5` | `40011` | `0.692555` | `0.386546` | `0.386546` | `0.487941` | `-8.907835` | `7.288266` |
| `open_guarded_retest_entry` | `5` | `34873` | `0.603621` | `0.240584` | `0.240584` | `0.478422` | `-8.663256` | `6.756745` |
| `next_open_entry` | `5` | `56945` | `0.985668` | `0.479166` | `0.479166` | `0.488805` | `-8.774428` | `7.527803` |
| `close_zone_limit_entry` | `5` | `43559` | `0.753968` | `0.402171` | `0.402171` | `0.487821` | `-8.771879` | `7.223866` |
| `atr_pullback_entry` | `5` | `19032` | `0.329427` | `0.437864` | `0.437864` | `0.500736` | `-9.737029` | `7.555202` |
| `signal_close_retest_entry` | `3` | `40249` | `0.696675` | `0.153151` | `0.153151` | `0.485851` | `-6.605062` | `5.284354` |
| `open_guarded_retest_entry` | `3` | `35027` | `0.606287` | `0.02871` | `0.02871` | `0.473749` | `-6.397459` | `4.805992` |
| `next_open_entry` | `3` | `57431` | `0.99408` | `0.23346` | `0.23346` | `0.479201` | `-6.568144` | `5.52546` |
| `close_zone_limit_entry` | `3` | `43801` | `0.758157` | `0.150782` | `0.150782` | `0.484898` | `-6.51657` | `5.23529` |
| `atr_pullback_entry` | `3` | `19248` | `0.333166` | `0.188938` | `0.188938` | `0.49522` | `-7.280907` | `5.5706` |
| `signal_close_retest_entry` | `1` | `40413` | `0.699514` | `-0.046571` | `-0.046571` | `0.471507` | `-3.324642` | `2.71403` |
| `open_guarded_retest_entry` | `1` | `35127` | `0.608018` | `-0.155457` | `-0.155457` | `0.449455` | `-3.204812` | `2.385412` |
| `next_open_entry` | `1` | `57695` | `0.99865` | `0.006082` | `0.006082` | `0.453488` | `-3.498925` | `2.782931` |
| `close_zone_limit_entry` | `1` | `43971` | `0.761099` | `-0.041361` | `-0.041361` | `0.470901` | `-3.304774` | `2.668253` |
| `atr_pullback_entry` | `1` | `19309` | `0.334222` | `-0.11199` | `-0.11199` | `0.469056` | `-3.364861` | `3.36192` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `154.717946`
- max_drawdown_pct: `-33.186202`
- diagnostic_win_rate: `0.505155`
- skipped_capacity_count: `17777`
- skipped_same_symbol_count: `633`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `82.75275` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `154.717946` | `-33.186202` | `0.505155` |
| `exclude_market_risk_off` | `270` | `17.800538` | `-35.689172` | `0.496296` |
| `require_foreign_not_sell` | `291` | `172.554888` | `-26.182994` | `0.505155` |
| `exclude_risk_off_and_foreign_sell` | `270` | `23.880814` | `-32.369768` | `0.503704` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `011170` | 롯데케미칼 | `63900.0` |  |  | `market_neutral` | `foreign_buy_only` | `-46.527197` | `5.445545` | `0.43069` | `0.075764` |
| `450080` | 에코프로머티 | `40200.0` |  |  | `market_neutral` | `foreign_buy_only` | `-54.72973` | `3.875969` | `0.550897` | `0.021153` |
| `011500` | 한농화성 | `13310.0` |  |  | `market_neutral` | `foreign_buy_only` | `-52.208259` | `6.48` | `0.415419` | `0.093909` |
| `001430` | 세아베스틸지주 | `32450.0` |  |  | `market_neutral` | `foreign_buy_only` | `-64.918919` | `5.016181` | `0.62085` | `0.055279` |
| `004310` | 현대약품 | `5000.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-67.105263` | `1.522843` | `0.820964` | `-0.009536` |
| `008970` | KBI동양철관 | `1209.0` |  |  | `market_neutral` | `foreign_buy_only` | `-44.668192` | `4.134367` | `0.600543` | `0.019256` |
| `100840` | SNT에너지 | `26550.0` |  |  | `market_neutral` | `foreign_buy_only` | `-59.589041` | `5.776892` | `0.504623` | `0.062169` |
| `011690` | 와이투솔루션 | `3290.0` |  |  | `market_neutral` | `inst_buy_only` | `-66.767677` | `2.8125` | `0.539577` | `-0.021191` |
| `017960` | 한국카본 | `25550.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-52.242991` | `2.2` | `0.463817` | `-0.121899` |
| `012610` | 경인양행 | `3290.0` |  |  | `market_neutral` | `dual_buy` | `-48.833593` | `3.459119` | `0.63297` | `0.01718` |
| `037560` | LG헬로비전 | `1639.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-46.871961` | `3.472222` | `0.453342` | `-0.004891` |
| `108320` | LX세미콘 | `38950.0` |  |  | `market_neutral` | `foreign_buy_only` | `-42.124814` | `4.423592` | `0.435754` | `0.015081` |
| `381970` | 케이카 | `8350.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.36325` | `3.08642` | `0.582523` | `-0.020149` |
| `003570` | SNT다이내믹스 | `35750.0` |  |  | `market_neutral` | `foreign_buy_only` | `-43.073248` | `7.357357` | `0.438975` | `0.102398` |
| `002710` | TCC스틸 | `9820.0` |  |  | `market_neutral` | `foreign_buy_only` | `-57.211329` | `4.357067` | `0.453871` | `0.08445` |
| `001040` | CJ | `152000.0` |  |  | `market_neutral` | `foreign_buy_only` | `-35.181237` | `2.494943` | `0.631459` | `0.05047` |
| `097230` | HJ중공업 | `19040.0` |  |  | `market_neutral` | `inst_buy_only` | `-43.668639` | `2.641509` | `0.628976` | `-0.139167` |
| `071090` | 하이스틸 | `3055.0` |  |  | `market_neutral` | `dual_buy` | `-41.920152` | `4.623288` | `0.456161` | `0.004712` |
| `000390` | SP삼화 | `6150.0` |  |  | `market_neutral` | `foreign_buy_only` | `-50.202429` | `7.705779` | `0.651194` | `0.082356` |
| `017860` | DS단석 | `11710.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.727788` | `9.746954` | `0.447109` | `0.039897` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
