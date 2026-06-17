# Bottom Rebound Pattern Research - 2026-06-17

- generated_at: `2026-06-17T20:30:57`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56190`
- label_rows: `1404750`
- latest_as_of_candidate_count: `57`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.424262`
- backtest_trade_count: `284`
- backtest_total_return_pct: `19.615144`
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
| `signal_close_retest_entry` | `20` | `38295` | `0.681527` | `1.870804` | `1.870804` | `0.490534` | `-16.989029` | `17.189767` |
| `open_guarded_retest_entry` | `20` | `33773` | `0.60105` | `1.651274` | `1.651274` | `0.482338` | `-16.939787` | `16.536831` |
| `next_open_entry` | `20` | `54492` | `0.969781` | `2.153446` | `2.153446` | `0.485576` | `-16.798231` | `17.418164` |
| `close_zone_limit_entry` | `20` | `41804` | `0.743976` | `1.883939` | `1.883939` | `0.48713` | `-16.867389` | `17.000871` |
| `atr_pullback_entry` | `20` | `17724` | `0.31543` | `2.531704` | `2.531704` | `0.519916` | `-17.007143` | `17.967243` |
| `signal_close_retest_entry` | `10` | `38700` | `0.688735` | `1.00623` | `1.00623` | `0.49739` | `-12.451473` | `11.188262` |
| `open_guarded_retest_entry` | `10` | `34086` | `0.60662` | `0.778827` | `0.778827` | `0.485859` | `-12.316491` | `10.678218` |
| `next_open_entry` | `10` | `54975` | `0.978377` | `1.174418` | `1.174418` | `0.497826` | `-12.256728` | `11.346154` |
| `close_zone_limit_entry` | `10` | `42219` | `0.751361` | `1.008087` | `1.008087` | `0.49473` | `-12.318569` | `11.08276` |
| `atr_pullback_entry` | `10` | `18034` | `0.320947` | `1.424262` | `1.424262` | `0.52584` | `-13.013687` | `11.520024` |
| `signal_close_retest_entry` | `5` | `39196` | `0.697562` | `0.387458` | `0.387458` | `0.48806` | `-8.779593` | `7.166658` |
| `open_guarded_retest_entry` | `5` | `34439` | `0.612903` | `0.238521` | `0.238521` | `0.478876` | `-8.62347` | `6.69461` |
| `next_open_entry` | `5` | `55598` | `0.989464` | `0.542727` | `0.542727` | `0.491151` | `-8.556987` | `7.412923` |
| `close_zone_limit_entry` | `5` | `42721` | `0.760295` | `0.409561` | `0.409561` | `0.488144` | `-8.626198` | `7.100964` |
| `atr_pullback_entry` | `5` | `18434` | `0.328065` | `0.405976` | `0.405976` | `0.498481` | `-9.526179` | `7.356056` |
| `signal_close_retest_entry` | `3` | `39505` | `0.703061` | `0.213895` | `0.213895` | `0.486951` | `-6.459078` | `5.236081` |
| `open_guarded_retest_entry` | `3` | `34548` | `0.614842` | `0.050234` | `0.050234` | `0.473428` | `-6.338319` | `4.769337` |
| `next_open_entry` | `3` | `55931` | `0.995391` | `0.295272` | `0.295272` | `0.480109` | `-6.418338` | `5.453664` |
| `close_zone_limit_entry` | `3` | `43034` | `0.765866` | `0.209473` | `0.209473` | `0.486313` | `-6.377746` | `5.183125` |
| `atr_pullback_entry` | `3` | `18688` | `0.332586` | `0.302727` | `0.302727` | `0.495345` | `-7.026048` | `5.478261` |
| `signal_close_retest_entry` | `1` | `39552` | `0.703897` | `-0.015091` | `-0.015091` | `0.475374` | `-3.26339` | `2.692989` |
| `open_guarded_retest_entry` | `1` | `34590` | `0.61559` | `-0.141796` | `-0.141796` | `0.451518` | `-3.16448` | `2.377559` |
| `next_open_entry` | `1` | `56133` | `0.998986` | `0.044807` | `0.044807` | `0.459195` | `-3.420457` | `2.764977` |
| `close_zone_limit_entry` | `1` | `43087` | `0.766809` | `-0.011439` | `-0.011439` | `0.474459` | `-3.246482` | `2.64624` |
| `atr_pullback_entry` | `1` | `18701` | `0.332817` | `-0.054953` | `-0.054953` | `0.476712` | `-3.24826` | `3.373316` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `284`
- total_return_pct: `19.615144`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.517606`
- skipped_capacity_count: `17135`
- skipped_same_symbol_count: `615`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-14.39605` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `284` | `19.615144` | `-23.08101` | `0.517606` |
| `exclude_market_risk_off` | `267` | `18.760095` | `-35.165321` | `0.490637` |
| `require_foreign_not_sell` | `284` | `15.848477` | `-23.08101` | `0.514085` |
| `exclude_risk_off_and_foreign_sell` | `267` | `22.911138` | `-32.899143` | `0.494382` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `014530` | 극동유화 | `3275.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.381762` | `1.866252` | `0.697467` | `-0.034235` |
| `004090` | 한국석유 | `11910.0` |  |  | `market_neutral` | `foreign_buy_only` | `-64.527178` | `3.565217` | `0.497207` | `0.033619` |
| `009580` | 무림P&P | `1840.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-55.822329` | `6.235566` | `0.435166` | `-0.007685` |
| `006890` | 태경케미컬 | `6520.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-39.292365` | `3.492063` | `0.44697` | `-0.014272` |
| `007570` | 일양약품 | `8500.0` |  |  | `market_neutral` | `foreign_buy_only` | `-41.780822` | `9.254499` | `0.821959` | `0.069211` |
| `000520` | 삼일제약 | `7150.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-44.401244` | `7.035928` | `0.482572` | `-0.002369` |
| `003520` | 영진약품 | `1285.0` |  |  | `market_neutral` | `foreign_buy_only` | `-41.723356` | `6.374172` | `0.482421` | `0.005075` |
| `090430` | 아모레퍼시픽 | `109900.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-33.795181` | `4.170616` | `0.625449` | `-0.039158` |
| `271940` | 일진하이솔루스 | `12780.0` |  |  | `market_neutral` | `foreign_buy_only` | `-34.021683` | `4.754098` | `0.807532` | `0.110169` |
| `000080` | 하이트진로 | `15920.0` |  |  | `market_neutral` | `foreign_buy_only` | `-17.512953` | `2.709677` | `0.545733` | `0.070396` |
| `339770` | 교촌에프앤비 | `4060.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-18.145161` | `3.307888` | `1.104627` | `-0.014797` |
| `003350` | 한국화장품제조 | `8290.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-84.209524` | `7.244502` | `0.427927` | `-0.080764` |
| `000020` | 동화약품 | `5330.0` |  |  | `market_neutral` | `dual_buy` | `-20.447761` | `3.495146` | `0.654719` | `0.065223` |
| `009160` | SIMPAC | `4560.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-33.913043` | `5.069124` | `1.091111` | `-0.017918` |
| `210540` | 디와이파워 | `12280.0` |  |  | `market_neutral` | `foreign_buy_only` | `-24.616329` | `3.628692` | `1.243695` | `0.027575` |
| `105630` | 한세실업 | `9040.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-41.827542` | `8.784597` | `0.638481` | `-0.129847` |
| `001680` | 대상 | `18440.0` |  |  | `market_neutral` | `foreign_buy_only` | `-23.643892` | `4.951622` | `0.622367` | `0.091864` |
| `023800` | 인지컨트롤스 | `5780.0` |  |  | `market_neutral` | `foreign_buy_only` | `-31.678487` | `4.144144` | `0.580814` | `0.014167` |
| `006040` | 동원산업 | `33950.0` |  |  | `market_neutral` | `dual_buy` | `-29.927761` | `7.266983` | `1.048996` | `0.046416` |
| `084680` | 이월드 | `1220.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-41.904762` | `7.773852` | `0.485005` | `-0.042824` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
