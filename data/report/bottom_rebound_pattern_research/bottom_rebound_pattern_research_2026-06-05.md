# Bottom Rebound Pattern Research - 2026-06-05

- generated_at: `2026-06-05T21:38:57`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `55617`
- label_rows: `1390425`
- latest_as_of_candidate_count: `164`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.535793`
- backtest_trade_count: `281`
- backtest_total_return_pct: `52.514453`
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
| `signal_close_retest_entry` | `20` | `38108` | `0.685186` | `1.99528` | `1.99528` | `0.491944` | `-16.88775` | `17.218149` |
| `open_guarded_retest_entry` | `20` | `33642` | `0.604887` | `1.772987` | `1.772987` | `0.483949` | `-16.836869` | `16.548623` |
| `next_open_entry` | `20` | `54086` | `0.972472` | `2.257517` | `2.257517` | `0.486577` | `-16.666667` | `17.384844` |
| `close_zone_limit_entry` | `20` | `41605` | `0.748063` | `2.000199` | `2.000199` | `0.488667` | `-16.771753` | `17.01611` |
| `atr_pullback_entry` | `20` | `17623` | `0.316864` | `2.70143` | `2.70143` | `0.521761` | `-16.880673` | `18.01343` |
| `signal_close_retest_entry` | `10` | `38346` | `0.689465` | `1.085491` | `1.085491` | `0.49927` | `-12.215612` | `11.214036` |
| `open_guarded_retest_entry` | `10` | `33830` | `0.608267` | `0.838926` | `0.838926` | `0.487496` | `-12.104886` | `10.692939` |
| `next_open_entry` | `10` | `54475` | `0.979467` | `1.254346` | `1.254346` | `0.498926` | `-12.02206` | `11.337638` |
| `close_zone_limit_entry` | `10` | `41860` | `0.752648` | `1.092159` | `1.092159` | `0.496417` | `-12.111622` | `11.095299` |
| `atr_pullback_entry` | `10` | `17734` | `0.318859` | `1.535793` | `1.535793` | `0.528815` | `-12.639236` | `11.53556` |
| `signal_close_retest_entry` | `5` | `38637` | `0.694698` | `0.401411` | `0.401411` | `0.48803` | `-8.598721` | `7.113275` |
| `open_guarded_retest_entry` | `5` | `34039` | `0.612025` | `0.252182` | `0.252182` | `0.478627` | `-8.450833` | `6.658124` |
| `next_open_entry` | `5` | `54909` | `0.98727` | `0.554064` | `0.554064` | `0.491613` | `-8.403361` | `7.347447` |
| `close_zone_limit_entry` | `5` | `42161` | `0.75806` | `0.423041` | `0.423041` | `0.488176` | `-8.466819` | `7.055861` |
| `atr_pullback_entry` | `5` | `17975` | `0.323193` | `0.429367` | `0.429367` | `0.498192` | `-9.275727` | `7.272669` |
| `signal_close_retest_entry` | `3` | `38846` | `0.698456` | `0.153647` | `0.153647` | `0.485146` | `-6.369101` | `5.117424` |
| `open_guarded_retest_entry` | `3` | `34204` | `0.614992` | `0.031179` | `0.031179` | `0.473161` | `-6.281596` | `4.726351` |
| `next_open_entry` | `3` | `55130` | `0.991244` | `0.254614` | `0.254614` | `0.478796` | `-6.336193` | `5.346576` |
| `close_zone_limit_entry` | `3` | `42370` | `0.761817` | `0.153298` | `0.153298` | `0.484612` | `-6.303108` | `5.087312` |
| `atr_pullback_entry` | `3` | `18155` | `0.326429` | `0.192279` | `0.192279` | `0.491765` | `-6.912123` | `5.304551` |
| `signal_close_retest_entry` | `1` | `39149` | `0.703903` | `-0.047175` | `-0.047175` | `0.470944` | `-3.282979` | `2.657241` |
| `open_guarded_retest_entry` | `1` | `34407` | `0.618642` | `-0.15808` | `-0.15808` | `0.448426` | `-3.182221` | `2.362554` |
| `next_open_entry` | `1` | `55453` | `0.997051` | `0.019722` | `0.019722` | `0.455719` | `-3.430572` | `2.719562` |
| `close_zone_limit_entry` | `1` | `42674` | `0.767283` | `-0.041394` | `-0.041394` | `0.47031` | `-3.258537` | `2.608696` |
| `atr_pullback_entry` | `1` | `18397` | `0.33078` | `-0.115143` | `-0.115143` | `0.467739` | `-3.281148` | `3.316817` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `281`
- total_return_pct: `52.514453`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.523132`
- skipped_capacity_count: `16853`
- skipped_same_symbol_count: `600`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `8.962236` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `281` | `52.514453` | `-23.08101` | `0.523132` |
| `exclude_market_risk_off` | `262` | `64.458657` | `-24.651169` | `0.507634` |
| `require_foreign_not_sell` | `281` | `46.653133` | `-23.08101` | `0.523132` |
| `exclude_risk_off_and_foreign_sell` | `262` | `76.590666` | `-23.78546` | `0.515267` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `249420` | 일동제약 | `19700.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.27081` | `1.129363` | `0.659721` | `0.126323` |
| `037270` | YG PLUS | `3675.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.708279` | `0.547196` | `0.88047` | `0.142031` |
| `272550` | 삼양패키징 | `8890.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.313953` | `0.793651` | `0.494056` | `0.035459` |
| `103140` | 풍산 | `72300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.294118` | `2.118644` | `0.560419` | `0.185787` |
| `007570` | 일양약품 | `8210.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.767123` | `1.73482` | `0.402528` | `0.009952` |
| `009240` | 한샘 | `30750.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-39.349112` | `4.237288` | `0.551527` | `0.127163` |
| `381970` | 케이카 | `8660.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.968768` | `3.033908` | `0.451328` | `0.070156` |
| `004090` | 한국석유 | `11990.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-39.748744` | `0.587248` | `0.484809` | `0.043103` |
| `003520` | 영진약품 | `1267.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-42.539683` | `3.767404` | `0.89722` | `0.047058` |
| `008730` | 율촌화학 | `17500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.401225` | `3.183962` | `0.825394` | `0.04413` |
| `001390` | KG케미칼 | `4390.0` |  |  | `market_risk_off` | `dual_buy` | `-40.675676` | `1.385681` | `0.418227` | `0.084916` |
| `100090` | SK오션플랜트 | `15780.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.834711` | `2.401038` | `0.549855` | `0.058564` |
| `009070` | KCTC | `4535.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.947557` | `1.454139` | `0.441826` | `-0.024229` |
| `352820` | 하이브 | `209500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.755611` | `1.699029` | `0.510708` | `-0.101412` |
| `029780` | 삼성카드 | `46000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-31.851852` | `1.882614` | `0.909213` | `0.134016` |
| `005870` | 휴니드 | `5700.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.898734` | `1.423488` | `0.495194` | `0.008321` |
| `000120` | CJ대한통운 | `81900.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-41.914894` | `1.612903` | `0.923154` | `-0.039612` |
| `058730` | 다스코 | `2480.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-41.578327` | `2.268041` | `0.436021` | `-0.004511` |
| `094800` | 맵스리얼티 | `5100.0` |  |  | `market_risk_off` | `dual_buy` | `-37.728938` | `2.719033` | `0.929853` | `0.03957` |
| `000520` | 삼일제약 | `7150.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.401244` | `2.877698` | `0.603108` | `-0.002106` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
