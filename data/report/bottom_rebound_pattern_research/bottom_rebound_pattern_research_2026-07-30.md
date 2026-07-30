# Bottom Rebound Pattern Research - 2026-07-30

- generated_at: `2026-07-30T20:52:33`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `59331`
- label_rows: `1483275`
- latest_as_of_candidate_count: `220`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.286286`
- backtest_trade_count: `296`
- backtest_total_return_pct: `153.761404`
- backtest_max_drawdown_pct: `-36.319736`
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
| `signal_close_retest_entry` | `20` | `39484` | `0.665487` | `1.681189` | `1.681189` | `0.482398` | `-17.632352` | `17.184605` |
| `open_guarded_retest_entry` | `20` | `34700` | `0.584854` | `1.407958` | `1.407958` | `0.475648` | `-17.459034` | `16.543103` |
| `next_open_entry` | `20` | `56075` | `0.945121` | `1.929788` | `1.929788` | `0.478573` | `-17.403796` | `17.386052` |
| `close_zone_limit_entry` | `20` | `43005` | `0.724832` | `1.679929` | `1.679929` | `0.479595` | `-17.460317` | `17.0002` |
| `atr_pullback_entry` | `20` | `18630` | `0.314001` | `2.146236` | `2.146236` | `0.505099` | `-18.114709` | `17.931534` |
| `signal_close_retest_entry` | `10` | `40634` | `0.68487` | `0.93957` | `0.93957` | `0.491633` | `-12.913382` | `11.509437` |
| `open_guarded_retest_entry` | `10` | `35286` | `0.594731` | `0.717747` | `0.717747` | `0.482543` | `-12.640124` | `10.840662` |
| `next_open_entry` | `10` | `57566` | `0.970252` | `1.032703` | `1.032703` | `0.489612` | `-12.810312` | `11.554846` |
| `close_zone_limit_entry` | `10` | `44179` | `0.744619` | `0.942695` | `0.942695` | `0.489418` | `-12.78465` | `11.355552` |
| `atr_pullback_entry` | `10` | `19488` | `0.328462` | `1.286286` | `1.286286` | `0.515343` | `-13.676624` | `12.053352` |
| `signal_close_retest_entry` | `5` | `41218` | `0.694713` | `0.328586` | `0.328586` | `0.484133` | `-9.056694` | `7.467397` |
| `open_guarded_retest_entry` | `5` | `35615` | `0.600276` | `0.202375` | `0.202375` | `0.476204` | `-8.806089` | `6.862745` |
| `next_open_entry` | `5` | `58377` | `0.983921` | `0.445108` | `0.445108` | `0.485345` | `-8.928571` | `7.623774` |
| `close_zone_limit_entry` | `5` | `44785` | `0.754833` | `0.353077` | `0.353077` | `0.484269` | `-8.921994` | `7.389519` |
| `atr_pullback_entry` | `5` | `19880` | `0.335069` | `0.336734` | `0.336734` | `0.494618` | `-9.921223` | `7.907117` |
| `signal_close_retest_entry` | `3` | `41318` | `0.696398` | `0.21083` | `0.21083` | `0.486906` | `-6.692298` | `5.38674` |
| `open_guarded_retest_entry` | `3` | `35663` | `0.601085` | `0.044239` | `0.044239` | `0.473937` | `-6.497607` | `4.852196` |
| `next_open_entry` | `3` | `58762` | `0.99041` | `0.213013` | `0.213013` | `0.475596` | `-6.739486` | `5.577586` |
| `close_zone_limit_entry` | `3` | `44899` | `0.756754` | `0.204108` | `0.204108` | `0.485891` | `-6.597447` | `5.333973` |
| `atr_pullback_entry` | `3` | `19906` | `0.335508` | `0.334712` | `0.334712` | `0.499347` | `-7.327457` | `5.750779` |
| `signal_close_retest_entry` | `1` | `41660` | `0.702162` | `0.009159` | `0.009159` | `0.474988` | `-3.396226` | `2.80095` |
| `open_guarded_retest_entry` | `1` | `35779` | `0.603041` | `-0.155961` | `-0.155961` | `0.448308` | `-3.250304` | `2.421831` |
| `next_open_entry` | `1` | `59111` | `0.996292` | `0.05028` | `0.05028` | `0.457969` | `-3.535354` | `2.869565` |
| `close_zone_limit_entry` | `1` | `45244` | `0.762569` | `0.009883` | `0.009883` | `0.473875` | `-3.363705` | `2.755505` |
| `atr_pullback_entry` | `1` | `20227` | `0.340918` | `0.012596` | `0.012596` | `0.478865` | `-3.429045` | `3.516496` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `296`
- total_return_pct: `153.761404`
- max_drawdown_pct: `-36.319736`
- diagnostic_win_rate: `0.5`
- skipped_capacity_count: `18542`
- skipped_same_symbol_count: `650`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `81.144234` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `296` | `153.761404` | `-36.319736` | `0.5` |
| `exclude_market_risk_off` | `275` | `14.286863` | `-37.607392` | `0.483636` |
| `require_foreign_not_sell` | `296` | `155.223806` | `-35.058523` | `0.496622` |
| `exclude_risk_off_and_foreign_sell` | `275` | `12.438281` | `-38.616588` | `0.490909` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `004090` | 한국석유 | `10050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-70.067014` | `1.10664` | `1.10276` | `0.004509` |
| `002020` | 코오롱 | `21300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-75.85034` | `1.428571` | `1.498412` | `0.095507` |
| `195870` | 해성디에스 | `38150.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.524558` | `1.733333` | `0.982142` | `0.08398` |
| `000520` | 삼일제약 | `5830.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.66563` | `1.745201` | `1.108906` | `0.049007` |
| `003280` | 흥아해운 | `1569.0` |  |  | `market_risk_off` | `inst_buy_only` | `-66.112311` | `2.415144` | `1.119128` | `-0.022183` |
| `000990` | DB하이텍 | `71200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.110629` | `3.188406` | `1.073117` | `0.080452` |
| `117580` | 대성에너지 | `6650.0` |  |  | `market_risk_off` | `dual_buy` | `-58.823529` | `3.74415` | `0.476772` | `0.010478` |
| `128940` | 한미약품 | `311500.0` |  |  | `market_risk_off` | `dual_buy` | `-51.854714` | `0.809061` | `0.840702` | `0.0448` |
| `001040` | CJ | `124200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.764192` | `2.390767` | `1.048068` | `0.035559` |
| `454910` | 두산로보틱스 | `55400.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.411765` | `0.544465` | `1.011297` | `0.03822` |
| `037560` | LG헬로비전 | `1493.0` |  |  | `market_risk_off` | `dual_buy` | `-59.20765` | `0.878378` | `0.449023` | `0.014488` |
| `034230` | 파라다이스 | `9450.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.750572` | `1.39485` | `0.753613` | `0.05205` |
| `012200` | 계양전기 | `3280.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-73.97858` | `1.234568` | `0.618004` | `0.008231` |
| `002900` | TYM | `5640.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.030303` | `4.251386` | `0.928822` | `-0.023875` |
| `006800` | 미래에셋증권 | `30200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-65.603645` | `2.372881` | `1.162053` | `0.085468` |
| `007810` | 코리아써키트 | `38500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-73.702186` | `1.583113` | `1.030343` | `0.058438` |
| `004960` | 한신공영 | `9090.0` |  |  | `market_risk_off` | `dual_buy` | `-48.730964` | `2.020202` | `0.802996` | `0.002085` |
| `001440` | 대한전선 | `20800.0` |  |  | `market_risk_off` | `dual_buy` | `-72.192513` | `1.216545` | `1.100233` | `0.019412` |
| `039490` | 키움증권 | `258500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.51269` | `2.988048` | `1.431993` | `0.021283` |
| `005850` | 에스엘 | `50100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-36.981132` | `1.417004` | `0.538506` | `0.066327` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
