# Bottom Rebound Pattern Research - 2026-06-12

- generated_at: `2026-06-12T20:25:17`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57097`
- label_rows: `1427425`
- latest_as_of_candidate_count: `110`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.413979`
- backtest_trade_count: `290`
- backtest_total_return_pct: `24.642696`
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
| `signal_close_retest_entry` | `20` | `38725` | `0.678232` | `1.813912` | `1.813912` | `0.490433` | `-16.94257` | `17.22018` |
| `open_guarded_retest_entry` | `20` | `34161` | `0.598298` | `1.60824` | `1.60824` | `0.482363` | `-16.912328` | `16.582915` |
| `next_open_entry` | `20` | `55277` | `0.968124` | `2.029751` | `2.029751` | `0.486133` | `-16.733281` | `17.368229` |
| `close_zone_limit_entry` | `20` | `42252` | `0.740004` | `1.815442` | `1.815442` | `0.487385` | `-16.827508` | `17.01772` |
| `atr_pullback_entry` | `20` | `17957` | `0.3145` | `2.40135` | `2.40135` | `0.518349` | `-16.972914` | `17.967878` |
| `signal_close_retest_entry` | `10` | `39009` | `0.683206` | `1.014777` | `1.014777` | `0.498372` | `-12.316335` | `11.236395` |
| `open_guarded_retest_entry` | `10` | `34363` | `0.601835` | `0.802057` | `0.802057` | `0.487647` | `-12.193773` | `10.732381` |
| `next_open_entry` | `10` | `55684` | `0.975253` | `1.1324` | `1.1324` | `0.497306` | `-12.167672` | `11.3508` |
| `close_zone_limit_entry` | `10` | `42553` | `0.745276` | `1.012935` | `1.012935` | `0.495547` | `-12.215298` | `11.111111` |
| `atr_pullback_entry` | `10` | `18148` | `0.317845` | `1.413979` | `1.413979` | `0.527717` | `-12.814761` | `11.563285` |
| `signal_close_retest_entry` | `5` | `39463` | `0.691157` | `0.362372` | `0.362372` | `0.487368` | `-8.747544` | `7.165663` |
| `open_guarded_retest_entry` | `5` | `34678` | `0.607352` | `0.239985` | `0.239985` | `0.479382` | `-8.552365` | `6.70061` |
| `next_open_entry` | `5` | `56244` | `0.985061` | `0.496459` | `0.496459` | `0.490115` | `-8.543721` | `7.392996` |
| `close_zone_limit_entry` | `5` | `43015` | `0.753367` | `0.380603` | `0.380603` | `0.487179` | `-8.593361` | `7.097548` |
| `atr_pullback_entry` | `5` | `18512` | `0.32422` | `0.375627` | `0.375627` | `0.49865` | `-9.495136` | `7.360276` |
| `signal_close_retest_entry` | `3` | `39756` | `0.696289` | `0.148804` | `0.148804` | `0.485461` | `-6.469562` | `5.198777` |
| `open_guarded_retest_entry` | `3` | `34814` | `0.609734` | `0.032287` | `0.032287` | `0.473861` | `-6.318925` | `4.766049` |
| `next_open_entry` | `3` | `56565` | `0.990683` | `0.218151` | `0.218151` | `0.477946` | `-6.440259` | `5.417277` |
| `close_zone_limit_entry` | `3` | `43309` | `0.758516` | `0.145471` | `0.145471` | `0.484241` | `-6.385824` | `5.150315` |
| `atr_pullback_entry` | `3` | `18759` | `0.328546` | `0.198161` | `0.198161` | `0.494962` | `-7.023014` | `5.425682` |
| `signal_close_retest_entry` | `1` | `39864` | `0.69818` | `-0.039076` | `-0.039076` | `0.473033` | `-3.257786` | `2.694543` |
| `open_guarded_retest_entry` | `1` | `34868` | `0.61068` | `-0.148698` | `-0.148698` | `0.450815` | `-3.162315` | `2.382528` |
| `next_open_entry` | `1` | `56987` | `0.998073` | `0.027451` | `0.027451` | `0.456894` | `-3.417778` | `2.771855` |
| `close_zone_limit_entry` | `1` | `43430` | `0.760635` | `-0.033846` | `-0.033846` | `0.472392` | `-3.240746` | `2.650646` |
| `atr_pullback_entry` | `1` | `18785` | `0.329002` | `-0.115863` | `-0.115863` | `0.468139` | `-3.278143` | `3.329204` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `290`
- total_return_pct: `24.642696`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.513793`
- skipped_capacity_count: `17245`
- skipped_same_symbol_count: `613`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-10.982408` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `290` | `24.642696` | `-23.08101` | `0.513793` |
| `exclude_market_risk_off` | `270` | `25.158725` | `-31.672118` | `0.496296` |
| `require_foreign_not_sell` | `289` | `5.643395` | `-29.784536` | `0.50173` |
| `exclude_risk_off_and_foreign_sell` | `270` | `31.314774` | `-28.311347` | `0.496296` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `014530` | 극동유화 | `3300.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-48.995363` | `2.964119` | `0.46428` | `-0.014081` |
| `006890` | 태경케미컬 | `6460.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-44.501718` | `2.702703` | `0.766742` | `-0.037295` |
| `004090` | 한국석유 | `12140.0` |  |  | `market_risk_on` | `inst_buy_only` | `-63.842144` | `4.206009` | `0.72493` | `-0.02819` |
| `005870` | 휴니드 | `5600.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-46.564885` | `5.263158` | `0.886774` | `-0.013595` |
| `128940` | 한미약품 | `411000.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-36.476043` | `3.396226` | `0.910296` | `-0.025929` |
| `117580` | 대성에너지 | `7170.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-55.603715` | `4.824561` | `0.600836` | `-0.034637` |
| `003570` | SNT다이내믹스 | `40900.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-34.872611` | `4.871795` | `1.966871` | `0.118129` |
| `112610` | 씨에스윈드 | `41500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-47.732997` | `6.410256` | `0.690904` | `0.038035` |
| `128820` | 대성산업 | `5170.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-60.65449` | `4.233871` | `0.948101` | `-0.012764` |
| `105630` | 한세실업 | `8690.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-44.079794` | `4.321729` | `0.894695` | `-0.051667` |
| `009070` | KCTC | `4445.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-47.020262` | `7.36715` | `0.612811` | `0.051824` |
| `004310` | 현대약품 | `5730.0` |  |  | `market_risk_on` | `inst_buy_only` | `-62.302632` | `5.914972` | `0.642003` | `-0.042044` |
| `010660` | 화천기계 | `2895.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-56.069803` | `9.039548` | `0.806741` | `-0.001734` |
| `214390` | 경보제약 | `5370.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.258065` | `6.336634` | `0.605501` | `0.013007` |
| `249420` | 일동제약 | `19270.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.154721` | `9.80057` | `0.848414` | `0.000844` |
| `001550` | 조비 | `10700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-48.926014` | `8.850458` | `0.468176` | `0.019124` |
| `011700` | 한신기계 | `2770.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-52.891156` | `7.364341` | `0.414519` | `-0.011192` |
| `003520` | 영진약품 | `1265.0` |  |  | `market_risk_on` | `inst_buy_only` | `-42.630385` | `5.153782` | `0.588827` | `-0.08968` |
| `008930` | 한미사이언스 | `30100.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.765766` | `7.117438` | `0.755259` | `-0.138769` |
| `001360` | 삼성제약 | `1376.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-39.649123` | `6.090979` | `0.501266` | `-0.020787` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
