# Bottom Rebound Pattern Research - 2026-07-14

- generated_at: `2026-07-14T20:53:53`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58381`
- label_rows: `1459525`
- latest_as_of_candidate_count: `193`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.303053`
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
| `signal_close_retest_entry` | `20` | `38928` | `0.666792` | `1.806042` | `1.806042` | `0.48731` | `-17.300597` | `17.212272` |
| `open_guarded_retest_entry` | `20` | `34285` | `0.587263` | `1.575509` | `1.575509` | `0.480298` | `-17.206611` | `16.582915` |
| `next_open_entry` | `20` | `55414` | `0.949179` | `2.031051` | `2.031051` | `0.482604` | `-17.082765` | `17.420063` |
| `close_zone_limit_entry` | `20` | `42449` | `0.727103` | `1.791272` | `1.791272` | `0.484181` | `-17.142733` | `17.01772` |
| `atr_pullback_entry` | `20` | `18186` | `0.311505` | `2.421896` | `2.421896` | `0.514407` | `-17.505832` | `18.051926` |
| `signal_close_retest_entry` | `10` | `39761` | `0.681061` | `0.919588` | `0.919588` | `0.492266` | `-12.867133` | `11.365848` |
| `open_guarded_retest_entry` | `10` | `34788` | `0.595879` | `0.726354` | `0.726354` | `0.483558` | `-12.555376` | `10.77753` |
| `next_open_entry` | `10` | `56765` | `0.97232` | `1.024052` | `1.024052` | `0.490144` | `-12.836674` | `11.471944` |
| `close_zone_limit_entry` | `10` | `43310` | `0.741851` | `0.926499` | `0.926499` | `0.489679` | `-12.74217` | `11.223918` |
| `atr_pullback_entry` | `10` | `18795` | `0.321937` | `1.303053` | `1.303053` | `0.517531` | `-13.502482` | `11.74064` |
| `signal_close_retest_entry` | `5` | `40369` | `0.691475` | `0.381743` | `0.381743` | `0.488419` | `-8.941873` | `7.351596` |
| `open_guarded_retest_entry` | `5` | `35121` | `0.601583` | `0.245708` | `0.245708` | `0.479428` | `-8.684527` | `6.828559` |
| `next_open_entry` | `5` | `57678` | `0.987958` | `0.462552` | `0.462552` | `0.488349` | `-8.849937` | `7.578273` |
| `close_zone_limit_entry` | `5` | `43928` | `0.752437` | `0.39614` | `0.39614` | `0.488117` | `-8.803974` | `7.272022` |
| `atr_pullback_entry` | `5` | `19325` | `0.331015` | `0.450898` | `0.450898` | `0.502561` | `-9.761905` | `7.697336` |
| `signal_close_retest_entry` | `3` | `40527` | `0.694181` | `0.142304` | `0.142304` | `0.485306` | `-6.634088` | `5.299797` |
| `open_guarded_retest_entry` | `3` | `35209` | `0.60309` | `0.024814` | `0.024814` | `0.473743` | `-6.417468` | `4.825378` |
| `next_open_entry` | `3` | `57887` | `0.991538` | `0.218908` | `0.218908` | `0.478` | `-6.616541` | `5.533544` |
| `close_zone_limit_entry` | `3` | `44087` | `0.75516` | `0.140063` | `0.140063` | `0.484292` | `-6.544605` | `5.253952` |
| `atr_pullback_entry` | `3` | `19420` | `0.332642` | `0.183681` | `0.183681` | `0.494696` | `-7.327305` | `5.608737` |
| `signal_close_retest_entry` | `1` | `40755` | `0.698087` | `-0.048474` | `-0.048474` | `0.470494` | `-3.354533` | `2.72795` |
| `open_guarded_retest_entry` | `1` | `35290` | `0.604477` | `-0.161019` | `-0.161019` | `0.448427` | `-3.220421` | `2.391658` |
| `next_open_entry` | `1` | `58188` | `0.996694` | `0.009397` | `0.009397` | `0.453908` | `-3.520658` | `2.800659` |
| `close_zone_limit_entry` | `1` | `44322` | `0.759185` | `-0.042825` | `-0.042825` | `0.470037` | `-3.327781` | `2.683717` |
| `atr_pullback_entry` | `1` | `19549` | `0.334852` | `-0.119453` | `-0.119453` | `0.467032` | `-3.403869` | `3.372624` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `259.615115`
- max_drawdown_pct: `-23.55014`
- diagnostic_win_rate: `0.508532`
- skipped_capacity_count: `17871`
- skipped_same_symbol_count: `631`

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
| `011170` | 롯데케미칼 | `59800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.958159` | `1.873935` | `0.800005` | `0.086969` |
| `103140` | 풍산 | `60700.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.871859` | `0.998336` | `0.768088` | `0.121043` |
| `004560` | 현대비앤지스틸 | `10920.0` |  |  | `market_risk_off` | `dual_buy` | `-51.574279` | `3.018868` | `1.078767` | `0.152179` |
| `003540` | 대신증권 | `25650.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.483528` | `3.012048` | `1.085403` | `0.110445` |
| `128820` | 대성산업 | `4115.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-68.683409` | `2.49066` | `0.577226` | `0.070167` |
| `000490` | 대동 | `6680.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.026393` | `2.453988` | `0.781675` | `0.043479` |
| `015760` | 한국전력 | `33950.0` |  |  | `market_risk_off` | `dual_buy` | `-47.200622` | `2.259036` | `1.128848` | `0.024208` |
| `489790` | 한화비전 | `41950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.648649` | `4.875` | `0.917337` | `0.17053` |
| `071090` | 하이스틸 | `2865.0` |  |  | `market_risk_off` | `dual_buy` | `-45.532319` | `2.321429` | `0.570426` | `0.019009` |
| `008730` | 율촌화학 | `13320.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.383562` | `0.150376` | `1.02076` | `0.065858` |
| `004990` | 롯데지주 | `23050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.859416` | `2.217295` | `0.754717` | `0.150163` |
| `003570` | SNT다이내믹스 | `33000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.452229` | `2.325581` | `0.782049` | `0.067399` |
| `002710` | TCC스틸 | `8750.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.873638` | `2.699531` | `1.037366` | `0.111383` |
| `000390` | SP삼화 | `5950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.821862` | `4.203152` | `0.92981` | `0.082962` |
| `003530` | 한화투자증권 | `4410.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.37581` | `3.764706` | `0.938222` | `0.065999` |
| `001430` | 세아베스틸지주 | `30350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.189189` | `3.231293` | `0.704418` | `0.024566` |
| `108320` | LX세미콘 | `37350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.502229` | `3.75` | `0.775589` | `0.048223` |
| `010780` | 아이에스동서 | `19210.0` |  |  | `market_risk_off` | `dual_buy` | `-43.665689` | `1.372032` | `0.903586` | `0.079446` |
| `249420` | 일동제약 | `13670.0` |  |  | `market_risk_off` | `dual_buy` | `-68.896473` | `3.954373` | `1.468346` | `0.123278` |
| `012450` | 한화에어로스페이스 | `872000.0` |  |  | `market_risk_off` | `dual_buy` | `-47.311178` | `1.160093` | `1.169536` | `0.022974` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
