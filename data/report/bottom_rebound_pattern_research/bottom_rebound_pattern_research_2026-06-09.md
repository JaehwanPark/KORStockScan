# Bottom Rebound Pattern Research - 2026-06-09

- generated_at: `2026-06-09T20:44:11`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `55791`
- label_rows: `1394775`
- latest_as_of_candidate_count: `174`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.492223`
- backtest_trade_count: `283`
- backtest_total_return_pct: `42.045864`
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
| `signal_close_retest_entry` | `20` | `38144` | `0.683695` | `1.988919` | `1.988919` | `0.491663` | `-16.907325` | `17.220599` |
| `open_guarded_retest_entry` | `20` | `33665` | `0.603413` | `1.767739` | `1.767739` | `0.483767` | `-16.859437` | `16.547097` |
| `next_open_entry` | `20` | `54151` | `0.970605` | `2.247965` | `2.247965` | `0.486233` | `-16.692913` | `17.391304` |
| `close_zone_limit_entry` | `20` | `41645` | `0.746447` | `1.992712` | `1.992712` | `0.488366` | `-16.78637` | `17.01772` |
| `atr_pullback_entry` | `20` | `17631` | `0.316019` | `2.704531` | `2.704531` | `0.521638` | `-16.885018` | `18.013468` |
| `signal_close_retest_entry` | `10` | `38401` | `0.688301` | `1.064583` | `1.064583` | `0.498685` | `-12.259711` | `11.208406` |
| `open_guarded_retest_entry` | `10` | `33875` | `0.607177` | `0.820871` | `0.820871` | `0.486967` | `-12.171348` | `10.688854` |
| `next_open_entry` | `10` | `54530` | `0.977398` | `1.23907` | `1.23907` | `0.498515` | `-12.053192` | `11.333333` |
| `close_zone_limit_entry` | `10` | `41915` | `0.751286` | `1.072964` | `1.072964` | `0.495885` | `-12.147917` | `11.091282` |
| `atr_pullback_entry` | `10` | `17787` | `0.318815` | `1.492223` | `1.492223` | `0.52752` | `-12.731658` | `11.522783` |
| `signal_close_retest_entry` | `5` | `38715` | `0.693929` | `0.38374` | `0.38374` | `0.487279` | `-8.653846` | `7.111084` |
| `open_guarded_retest_entry` | `5` | `34107` | `0.611335` | `0.236063` | `0.236063` | `0.477937` | `-8.501818` | `6.656093` |
| `next_open_entry` | `5` | `54990` | `0.985643` | `0.540264` | `0.540264` | `0.491053` | `-8.43501` | `7.345738` |
| `close_zone_limit_entry` | `5` | `42239` | `0.757093` | `0.406761` | `0.406761` | `0.487488` | `-8.510723` | `7.054386` |
| `atr_pullback_entry` | `5` | `18049` | `0.323511` | `0.396892` | `0.396892` | `0.496648` | `-9.356596` | `7.271728` |
| `signal_close_retest_entry` | `3` | `38986` | `0.698787` | `0.141249` | `0.141249` | `0.484071` | `-6.42146` | `5.117424` |
| `open_guarded_retest_entry` | `3` | `34291` | `0.614633` | `0.023858` | `0.023858` | `0.472369` | `-6.311217` | `4.726351` |
| `next_open_entry` | `3` | `55278` | `0.990805` | `0.24514` | `0.24514` | `0.478038` | `-6.371776` | `5.346535` |
| `close_zone_limit_entry` | `3` | `42511` | `0.761969` | `0.141732` | `0.141732` | `0.483616` | `-6.348881` | `5.087497` |
| `atr_pullback_entry` | `3` | `18282` | `0.327687` | `0.167497` | `0.167497` | `0.489607` | `-7.014382` | `5.30476` |
| `signal_close_retest_entry` | `1` | `39313` | `0.704648` | `-0.032319` | `-0.032319` | `0.472795` | `-3.276804` | `2.680759` |
| `open_guarded_retest_entry` | `1` | `34426` | `0.617053` | `-0.157021` | `-0.157021` | `0.448702` | `-3.181484` | `2.36367` |
| `next_open_entry` | `1` | `55617` | `0.996881` | `0.029884` | `0.029884` | `0.457054` | `-3.425105` | `2.741206` |
| `close_zone_limit_entry` | `1` | `42838` | `0.76783` | `-0.027803` | `-0.027803` | `0.471987` | `-3.255584` | `2.630295` |
| `atr_pullback_entry` | `1` | `18549` | `0.332473` | `-0.08519` | `-0.08519` | `0.471508` | `-3.272046` | `3.347918` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `283`
- total_return_pct: `42.045864`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.519435`
- skipped_capacity_count: `16901`
- skipped_same_symbol_count: `603`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `1.608882` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `283` | `42.045864` | `-23.08101` | `0.519435` |
| `exclude_market_risk_off` | `262` | `64.458657` | `-24.651169` | `0.507634` |
| `require_foreign_not_sell` | `283` | `35.289528` | `-23.08101` | `0.519435` |
| `exclude_risk_off_and_foreign_sell` | `262` | `76.590666` | `-23.78546` | `0.515267` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `007110` | 일신석재 | `1018.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.714432` | `2.311558` | `1.108545` | `0.075307` |
| `029780` | 삼성카드 | `45350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-32.814815` | `2.024747` | `0.932515` | `0.138895` |
| `381970` | 케이카 | `8310.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.031232` | `0.605327` | `0.92633` | `0.014111` |
| `100090` | SK오션플랜트 | `14540.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.933884` | `3.047484` | `0.885803` | `0.098704` |
| `003520` | 영진약품 | `1242.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.673469` | `2.306425` | `0.634379` | `0.039565` |
| `112610` | 씨에스윈드 | `40350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.269231` | `3.461538` | `0.676449` | `0.114944` |
| `094800` | 맵스리얼티 | `5100.0` |  |  | `market_risk_off` | `dual_buy` | `-37.728938` | `2.719033` | `0.587322` | `0.042362` |
| `103140` | 풍산 | `69100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.803922` | `2.980626` | `0.962449` | `0.166781` |
| `017860` | DS단석 | `13940.0` |  |  | `market_risk_off` | `dual_buy` | `-46.996198` | `1.603499` | `0.721479` | `0.01196` |
| `272550` | 삼양패키징 | `8770.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.011628` | `3.419811` | `0.604397` | `0.033277` |
| `010660` | 화천기계 | `2765.0` |  |  | `market_risk_off` | `inst_buy_only` | `-58.042489` | `0.181159` | `0.926323` | `-0.041978` |
| `007570` | 일양약품 | `8070.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.726027` | `3.727506` | `0.478074` | `0.018554` |
| `009240` | 한샘 | `29900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.025641` | `4.728546` | `0.476258` | `0.118098` |
| `004090` | 한국석유 | `11820.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.603015` | `2.782609` | `0.801354` | `0.055654` |
| `003570` | SNT다이내믹스 | `39800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-35.598706` | `1.790281` | `0.616793` | `0.398432` |
| `271940` | 일진하이솔루스 | `12510.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-35.415591` | `-0.0` | `1.137965` | `0.159679` |
| `249420` | 일동제약 | `18770.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.335183` | `6.105144` | `0.874257` | `0.142163` |
| `006890` | 태경케미컬 | `6430.0` |  |  | `market_risk_off` | `dual_buy` | `-40.130354` | `1.100629` | `1.00081` | `0.031468` |
| `123890` | 한국자산신탁 | `2165.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-37.608069` | `2.122642` | `0.932542` | `0.032169` |
| `003090` | 대웅 | `16700.0` |  |  | `market_risk_off` | `inst_buy_only` | `-43.003413` | `1.829268` | `0.991553` | `-0.124277` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
