# Bottom Rebound Pattern Research - 2026-07-02

- generated_at: `2026-07-02T20:30:39`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57763`
- label_rows: `1444075`
- latest_as_of_candidate_count: `131`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.28909`
- backtest_trade_count: `291`
- backtest_total_return_pct: `280.950558`
- backtest_max_drawdown_pct: `-26.544856`
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
| `signal_close_retest_entry` | `20` | `38699` | `0.669962` | `1.899579` | `1.899579` | `0.489444` | `-17.09733` | `17.252931` |
| `open_guarded_retest_entry` | `20` | `34119` | `0.590672` | `1.645827` | `1.645827` | `0.481638` | `-17.055735` | `16.595839` |
| `next_open_entry` | `20` | `55091` | `0.953742` | `2.107681` | `2.107681` | `0.484526` | `-16.905981` | `17.416378` |
| `close_zone_limit_entry` | `20` | `42217` | `0.730866` | `1.880693` | `1.880693` | `0.486297` | `-16.965014` | `17.038054` |
| `atr_pullback_entry` | `20` | `17976` | `0.311203` | `2.548167` | `2.548167` | `0.517857` | `-17.166101` | `18.039216` |
| `signal_close_retest_entry` | `10` | `39571` | `0.685058` | `0.94117` | `0.94117` | `0.492911` | `-12.775735` | `11.328125` |
| `open_guarded_retest_entry` | `10` | `34649` | `0.599848` | `0.733594` | `0.733594` | `0.483708` | `-12.485504` | `10.755438` |
| `next_open_entry` | `10` | `56146` | `0.972006` | `1.058087` | `1.058087` | `0.492163` | `-12.58082` | `11.406423` |
| `close_zone_limit_entry` | `10` | `43104` | `0.746222` | `0.943475` | `0.943475` | `0.490349` | `-12.640626` | `11.1866` |
| `atr_pullback_entry` | `10` | `18678` | `0.323356` | `1.28909` | `1.28909` | `0.517186` | `-13.472646` | `11.697829` |
| `signal_close_retest_entry` | `5` | `39866` | `0.690165` | `0.371866` | `0.371866` | `0.486806` | `-8.899429` | `7.259714` |
| `open_guarded_retest_entry` | `5` | `34847` | `0.603275` | `0.235243` | `0.235243` | `0.478205` | `-8.666898` | `6.742607` |
| `next_open_entry` | `5` | `56832` | `0.983882` | `0.468116` | `0.468116` | `0.487718` | `-8.768956` | `7.508458` |
| `close_zone_limit_entry` | `5` | `43418` | `0.751658` | `0.387183` | `0.387183` | `0.486734` | `-8.762536` | `7.193995` |
| `atr_pullback_entry` | `5` | `18858` | `0.326472` | `0.41125` | `0.41125` | `0.498568` | `-9.7224` | `7.504274` |
| `signal_close_retest_entry` | `3` | `40267` | `0.697107` | `0.153689` | `0.153689` | `0.485758` | `-6.60413` | `5.283707` |
| `open_guarded_retest_entry` | `3` | `35047` | `0.606738` | `0.029057` | `0.029057` | `0.473792` | `-6.396416` | `4.807107` |
| `next_open_entry` | `3` | `57240` | `0.990946` | `0.237029` | `0.237029` | `0.479158` | `-6.545518` | `5.521133` |
| `close_zone_limit_entry` | `3` | `43821` | `0.758634` | `0.151003` | `0.151003` | `0.484745` | `-6.514225` | `5.230386` |
| `atr_pullback_entry` | `3` | `19244` | `0.333154` | `0.197554` | `0.197554` | `0.495635` | `-7.275725` | `5.571109` |
| `signal_close_retest_entry` | `1` | `40363` | `0.698769` | `-0.04983` | `-0.04983` | `0.470728` | `-3.327396` | `2.711143` |
| `open_guarded_retest_entry` | `1` | `35101` | `0.607673` | `-0.158633` | `-0.158633` | `0.448734` | `-3.205347` | `2.383995` |
| `next_open_entry` | `1` | `57632` | `0.997732` | `0.005342` | `0.005342` | `0.453359` | `-3.49433` | `2.782399` |
| `close_zone_limit_entry` | `1` | `43925` | `0.760435` | `-0.044192` | `-0.044192` | `0.470211` | `-3.304774` | `2.664913` |
| `atr_pullback_entry` | `1` | `19282` | `0.333812` | `-0.117255` | `-0.117255` | `0.467794` | `-3.367217` | `3.357087` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `280.950558`
- max_drawdown_pct: `-26.544856`
- diagnostic_win_rate: `0.512027`
- skipped_capacity_count: `17759`
- skipped_same_symbol_count: `628`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `174.559693` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `280.950558` | `-26.544856` | `0.512027` |
| `exclude_market_risk_off` | `272` | `-5.851493` | `-48.601521` | `0.485294` |
| `require_foreign_not_sell` | `291` | `215.057382` | `-23.423792` | `0.508591` |
| `exclude_risk_off_and_foreign_sell` | `272` | `2.430938` | `-44.079895` | `0.492647` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `001430` | 세아베스틸지주 | `31700.0` |  |  | `market_neutral` | `foreign_buy_only` | `-65.72973` | `1.116427` | `0.531177` | `0.067781` |
| `003570` | SNT다이내믹스 | `34900.0` |  |  | `market_neutral` | `foreign_buy_only` | `-44.426752` | `4.804805` | `0.424951` | `0.119345` |
| `450080` | 에코프로머티 | `40350.0` |  |  | `market_neutral` | `foreign_buy_only` | `-54.560811` | `3.196931` | `0.938932` | `0.011304` |
| `011170` | 롯데케미칼 | `63500.0` |  |  | `market_neutral` | `foreign_buy_only` | `-46.861925` | `4.785479` | `0.646983` | `0.064028` |
| `004310` | 현대약품 | `5140.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-66.184211` | `0.784314` | `1.366432` | `-0.010608` |
| `008970` | KBI동양철관 | `1191.0` |  |  | `market_neutral` | `foreign_buy_only` | `-45.491991` | `2.583979` | `0.849248` | `0.013776` |
| `103140` | 풍산 | `65600.0` |  |  | `market_neutral` | `foreign_buy_only` | `-58.79397` | `6.840391` | `0.688511` | `0.093494` |
| `092200` | 디아이씨 | `4530.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-69.75968` | `0.221239` | `0.466166` | `-0.011183` |
| `025860` | 남해화학 | `5670.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.772231` | `3.278689` | `0.644388` | `0.020769` |
| `249420` | 일동제약 | `16300.0` |  |  | `market_neutral` | `foreign_buy_only` | `-62.9124` | `4.554201` | `0.541627` | `0.036036` |
| `011500` | 한농화성 | `13060.0` |  |  | `market_neutral` | `foreign_buy_only` | `-53.105925` | `4.48` | `0.598775` | `0.070408` |
| `010660` | 화천기계 | `2740.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-58.421851` | `3.201507` | `0.511586` | `-0.022211` |
| `128820` | 대성산업 | `4250.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-67.656012` | `2.409639` | `0.459853` | `-0.003135` |
| `097230` | HJ중공업 | `19060.0` |  |  | `market_neutral` | `inst_buy_only` | `-43.609467` | `2.198391` | `0.842519` | `-0.134814` |
| `071090` | 하이스틸 | `3000.0` |  |  | `market_neutral` | `dual_buy` | `-42.965779` | `2.739726` | `0.468937` | `0.002489` |
| `084670` | 동양고속 | `29200.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-69.263158` | `0.516351` | `1.350076` | `-0.01405` |
| `003540` | 대신증권 | `27150.0` |  |  | `market_neutral` | `foreign_buy_only` | `-42.29543` | `6.889764` | `0.611386` | `0.140967` |
| `381970` | 케이카 | `8330.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.484536` | `2.839506` | `0.5168` | `-0.008784` |
| `117580` | 대성에너지 | `6690.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-58.575851` | `4.53125` | `0.750508` | `-0.012438` |
| `003780` | 진양산업 | `4555.0` |  |  | `market_neutral` | `dual_buy` | `-33.697234` | `1.560758` | `0.404397` | `0.006227` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
