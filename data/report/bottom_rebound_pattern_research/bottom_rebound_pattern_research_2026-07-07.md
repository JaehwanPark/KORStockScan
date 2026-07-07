# Bottom Rebound Pattern Research - 2026-07-07

- generated_at: `2026-07-07T20:53:50`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57789`
- label_rows: `1444725`
- latest_as_of_candidate_count: `144`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.316166`
- backtest_trade_count: `291`
- backtest_total_return_pct: `191.104448`
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
| `signal_close_retest_entry` | `20` | `38715` | `0.669937` | `1.833035` | `1.833035` | `0.488131` | `-17.169009` | `17.185956` |
| `open_guarded_retest_entry` | `20` | `34119` | `0.590406` | `1.565925` | `1.565925` | `0.480641` | `-17.116768` | `16.536765` |
| `next_open_entry` | `20` | `55121` | `0.953832` | `2.093087` | `2.093087` | `0.483609` | `-16.966068` | `17.396594` |
| `close_zone_limit_entry` | `20` | `42241` | `0.730952` | `1.820435` | `1.820435` | `0.484837` | `-17.024129` | `17.003145` |
| `atr_pullback_entry` | `20` | `17995` | `0.311391` | `2.480143` | `2.480143` | `0.517033` | `-17.267286` | `17.969618` |
| `signal_close_retest_entry` | `10` | `39769` | `0.688176` | `0.932471` | `0.932471` | `0.493072` | `-12.783819` | `11.388714` |
| `open_guarded_retest_entry` | `10` | `34744` | `0.601222` | `0.691924` | `0.691924` | `0.482472` | `-12.556941` | `10.761396` |
| `next_open_entry` | `10` | `56369` | `0.975428` | `1.073476` | `1.073476` | `0.492735` | `-12.591971` | `11.463415` |
| `close_zone_limit_entry` | `10` | `43309` | `0.749433` | `0.939212` | `0.939212` | `0.490822` | `-12.643874` | `11.25187` |
| `atr_pullback_entry` | `10` | `18868` | `0.326498` | `1.316166` | `1.316166` | `0.518391` | `-13.48963` | `11.839034` |
| `signal_close_retest_entry` | `5` | `40188` | `0.695426` | `0.377119` | `0.377119` | `0.48731` | `-8.919775` | `7.316741` |
| `open_guarded_retest_entry` | `5` | `35041` | `0.606361` | `0.220424` | `0.220424` | `0.477926` | `-8.748765` | `6.777594` |
| `next_open_entry` | `5` | `57042` | `0.987074` | `0.493233` | `0.493233` | `0.489306` | `-8.777613` | `7.511737` |
| `close_zone_limit_entry` | `5` | `43743` | `0.756943` | `0.397343` | `0.397343` | `0.487507` | `-8.78302` | `7.24763` |
| `atr_pullback_entry` | `5` | `19167` | `0.331672` | `0.41873` | `0.41873` | `0.498722` | `-9.730288` | `7.646033` |
| `signal_close_retest_entry` | `3` | `40498` | `0.700791` | `0.240122` | `0.240122` | `0.488987` | `-6.608318` | `5.323546` |
| `open_guarded_retest_entry` | `3` | `35164` | `0.60849` | `0.049461` | `0.049461` | `0.474093` | `-6.467167` | `4.805223` |
| `next_open_entry` | `3` | `57388` | `0.993061` | `0.284279` | `0.284279` | `0.480118` | `-6.58083` | `5.518981` |
| `close_zone_limit_entry` | `3` | `44057` | `0.762377` | `0.23344` | `0.23344` | `0.488186` | `-6.521739` | `5.276812` |
| `atr_pullback_entry` | `3` | `19384` | `0.335427` | `0.356376` | `0.356376` | `0.499381` | `-7.238837` | `5.656768` |
| `signal_close_retest_entry` | `1` | `40712` | `0.704494` | `0.007283` | `0.007283` | `0.475904` | `-3.345672` | `2.752258` |
| `open_guarded_retest_entry` | `1` | `35310` | `0.611016` | `-0.141253` | `-0.141253` | `0.451232` | `-3.217226` | `2.406833` |
| `next_open_entry` | `1` | `57645` | `0.997508` | `0.05563` | `0.05563` | `0.458964` | `-3.486621` | `2.808989` |
| `close_zone_limit_entry` | `1` | `44275` | `0.766149` | `0.008675` | `0.008675` | `0.474828` | `-3.318982` | `2.700992` |
| `atr_pullback_entry` | `1` | `19529` | `0.337936` | `-0.007636` | `-0.007636` | `0.478724` | `-3.376062` | `3.462259` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `191.104448`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.512027`
- skipped_capacity_count: `17942`
- skipped_same_symbol_count: `635`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `108.552148` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `191.104448` | `-23.08101` | `0.512027` |
| `exclude_market_risk_off` | `270` | `32.101466` | `-30.487378` | `0.5` |
| `require_foreign_not_sell` | `291` | `184.142676` | `-23.08101` | `0.508591` |
| `exclude_risk_off_and_foreign_sell` | `270` | `41.221035` | `-26.126575` | `0.503704` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `249420` | 일동제약 | `16050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-63.481229` | `2.359694` | `0.581586` | `0.252484` |
| `950210` | 프레스티지바이오파마 | `6030.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.556196` | `4.145078` | `0.685651` | `0.121204` |
| `381970` | 케이카 | `8280.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.78775` | `1.346389` | `0.707767` | `0.032235` |
| `439260` | 대한조선 | `50800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.030217` | `2.316213` | `1.085994` | `0.021034` |
| `008350` | 남선알미늄 | `1043.0` |  |  | `market_risk_off` | `dual_buy` | `-70.071736` | `4.718876` | `0.413862` | `0.048337` |
| `011690` | 와이투솔루션 | `3100.0` |  |  | `market_risk_off` | `dual_buy` | `-68.527919` | `2.990033` | `0.649933` | `0.069917` |
| `377300` | 카카오페이 | `39500.0` |  |  | `market_risk_off` | `dual_buy` | `-46.404342` | `4.497354` | `0.601444` | `0.054818` |
| `019170` | 신풍제약 | `8190.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.71134` | `3.670886` | `0.728327` | `0.068712` |
| `005010` | 휴스틸 | `3865.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.763085` | `2.656042` | `0.58711` | `0.008514` |
| `100090` | SK오션플랜트 | `14610.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.702479` | `3.543586` | `0.976368` | `0.024223` |
| `011170` | 롯데케미칼 | `62900.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.098402` | `2.11039` | `0.709659` | `-0.001622` |
| `011500` | 한농화성 | `12800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.039497` | `2.4` | `0.62976` | `0.038312` |
| `008970` | KBI동양철관 | `1174.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.392694` | `1.998262` | `0.867944` | `0.017718` |
| `037560` | LG헬로비전 | `1613.0` |  |  | `market_risk_off` | `dual_buy` | `-55.928962` | `0.938673` | `0.586647` | `0.003327` |
| `017960` | 한국카본 | `24500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-54.713494` | `3.157895` | `0.64595` | `-0.011803` |
| `002710` | TCC스틸 | `9490.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.101545` | `2.594595` | `0.704923` | `0.050924` |
| `005690` | 파미셀 | `11500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.107399` | `1.769912` | `0.956595` | `0.03789` |
| `022100` | 포스코DX | `20250.0` |  |  | `market_risk_off` | `dual_buy` | `-52.071006` | `3.053435` | `0.565642` | `0.021332` |
| `100840` | SNT에너지 | `25600.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-62.017804` | `3.018109` | `0.638834` | `-0.005248` |
| `103140` | 풍산 | `65900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.605528` | `6.980519` | `0.762487` | `0.164897` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
