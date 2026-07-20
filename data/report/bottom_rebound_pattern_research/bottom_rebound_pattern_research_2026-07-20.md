# Bottom Rebound Pattern Research - 2026-07-20

- generated_at: `2026-07-20T20:54:07`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58712`
- label_rows: `1467800`
- latest_as_of_candidate_count: `208`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.260722`
- backtest_trade_count: `293`
- backtest_total_return_pct: `220.859488`
- backtest_max_drawdown_pct: `-23.08101`
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
| `signal_close_retest_entry` | `20` | `39043` | `0.664992` | `1.785078` | `1.785078` | `0.487027` | `-17.348505` | `17.198983` |
| `open_guarded_retest_entry` | `20` | `34397` | `0.58586` | `1.536362` | `1.536362` | `0.479548` | `-17.239469` | `16.571585` |
| `next_open_entry` | `20` | `55650` | `0.947847` | `1.994258` | `1.994258` | `0.481923` | `-17.159916` | `17.391304` |
| `close_zone_limit_entry` | `20` | `42571` | `0.725082` | `1.774941` | `1.774941` | `0.483897` | `-17.174797` | `17.009346` |
| `atr_pullback_entry` | `20` | `18244` | `0.310737` | `2.367877` | `2.367877` | `0.514087` | `-17.652273` | `17.97104` |
| `signal_close_retest_entry` | `10` | `40156` | `0.683949` | `0.921602` | `0.921602` | `0.492106` | `-12.857056` | `11.410583` |
| `open_guarded_retest_entry` | `10` | `35084` | `0.597561` | `0.711076` | `0.711076` | `0.482528` | `-12.595091` | `10.800115` |
| `next_open_entry` | `10` | `56978` | `0.970466` | `1.030837` | `1.030837` | `0.49061` | `-12.732608` | `11.479804` |
| `close_zone_limit_entry` | `10` | `43695` | `0.744226` | `0.92678` | `0.92678` | `0.489804` | `-12.72277` | `11.285937` |
| `atr_pullback_entry` | `10` | `19174` | `0.326577` | `1.260722` | `1.260722` | `0.515646` | `-13.590441` | `11.877534` |
| `signal_close_retest_entry` | `5` | `40826` | `0.69536` | `0.365303` | `0.365303` | `0.486455` | `-8.959456` | `7.41969` |
| `open_guarded_retest_entry` | `5` | `35442` | `0.603659` | `0.22162` | `0.22162` | `0.477625` | `-8.768256` | `6.83757` |
| `next_open_entry` | `5` | `57819` | `0.98479` | `0.480083` | `0.480083` | `0.488179` | `-8.807728` | `7.589493` |
| `close_zone_limit_entry` | `5` | `44382` | `0.755927` | `0.385543` | `0.385543` | `0.486458` | `-8.844153` | `7.325416` |
| `atr_pullback_entry` | `5` | `19601` | `0.33385` | `0.38493` | `0.38493` | `0.497679` | `-9.824587` | `7.775769` |
| `signal_close_retest_entry` | `3` | `41036` | `0.698937` | `0.221009` | `0.221009` | `0.487401` | `-6.666667` | `5.354331` |
| `open_guarded_retest_entry` | `3` | `35526` | `0.605089` | `0.042692` | `0.042692` | `0.473738` | `-6.48424` | `4.827416` |
| `next_open_entry` | `3` | `58158` | `0.990564` | `0.252392` | `0.252392` | `0.477905` | `-6.654676` | `5.536319` |
| `close_zone_limit_entry` | `3` | `44600` | `0.75964` | `0.214023` | `0.214023` | `0.486368` | `-6.567262` | `5.303901` |
| `atr_pullback_entry` | `3` | `19762` | `0.336592` | `0.333375` | `0.333375` | `0.498431` | `-7.329774` | `5.711468` |
| `signal_close_retest_entry` | `1` | `41301` | `0.703451` | `-0.002064` | `-0.002064` | `0.474492` | `-3.368421` | `2.767528` |
| `open_guarded_retest_entry` | `1` | `35678` | `0.607678` | `-0.147747` | `-0.147747` | `0.449465` | `-3.22983` | `2.41749` |
| `next_open_entry` | `1` | `58504` | `0.996457` | `0.047123` | `0.047123` | `0.45814` | `-3.510723` | `2.831595` |
| `close_zone_limit_entry` | `1` | `44876` | `0.764341` | `-0.000225` | `-0.000225` | `0.473416` | `-3.340384` | `2.719411` |
| `atr_pullback_entry` | `1` | `19925` | `0.339368` | `-0.018636` | `-0.018636` | `0.476838` | `-3.405929` | `3.471598` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `220.859488`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.508532`
- skipped_capacity_count: `18239`
- skipped_same_symbol_count: `642`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `128.753612` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `220.859488` | `-23.08101` | `0.508532` |
| `exclude_market_risk_off` | `275` | `5.436202` | `-42.439232` | `0.487273` |
| `require_foreign_not_sell` | `293` | `208.166933` | `-23.08101` | `0.505119` |
| `exclude_risk_off_and_foreign_sell` | `275` | `13.707947` | `-37.923439` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `249420` | 일동제약 | `13490.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-68.221437` | `1.352367` | `0.488418` | `0.223717` |
| `103140` | 풍산 | `60000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.311558` | `0.840336` | `0.688782` | `0.139967` |
| `011210` | 현대위아 | `54900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.589693` | `0.919118` | `0.512118` | `0.116787` |
| `008730` | 율촌화학 | `12900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.670103` | `0.545596` | `0.664616` | `0.090819` |
| `130660` | 한전산업 | `10260.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.689655` | `1.083744` | `0.609257` | `0.127374` |
| `950210` | 프레스티지바이오파마 | `5210.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.549815` | `4.723618` | `0.495004` | `0.11887` |
| `019170` | 신풍제약 | `7720.0` |  |  | `market_risk_off` | `dual_buy` | `-43.235294` | `0.25974` | `0.992542` | `0.16197` |
| `013580` | 계룡건설 | `17930.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.156156` | `0.786959` | `1.007044` | `-0.002026` |
| `001500` | 현대차증권 | `7790.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.984848` | `3.452855` | `0.786037` | `0.13767` |
| `161000` | 애경케미칼 | `8550.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-57.164329` | `1.183432` | `0.547848` | `0.086038` |
| `128820` | 대성산업 | `4040.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.254186` | `0.74813` | `0.632841` | `0.050501` |
| `005250` | 녹십자홀딩스 | `9280.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.122507` | `0.215983` | `0.691252` | `0.061202` |
| `003160` | 디아이 | `19670.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.564103` | `0.613811` | `0.597673` | `0.049055` |
| `034230` | 파라다이스 | `9790.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.194508` | `1.345756` | `1.258405` | `0.050762` |
| `200880` | 서연이화 | `10340.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.437788` | `0.29098` | `0.537437` | `0.121646` |
| `011500` | 한농화성 | `11620.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.276481` | `1.573427` | `0.56035` | `0.023289` |
| `009070` | KCTC | `3720.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.661502` | `1.500682` | `2.219059` | `0.119567` |
| `032350` | 롯데관광개발 | `10990.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.32491` | `0.918274` | `1.082425` | `0.05366` |
| `079900` | 전진건설로봇 | `30300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.960227` | `2.192243` | `0.50728` | `0.02725` |
| `000390` | SP삼화 | `5900.0` |  |  | `market_risk_off` | `dual_buy` | `-52.226721` | `2.076125` | `0.601243` | `0.067581` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
