# Bottom Rebound Pattern Research - 2026-05-29

- generated_at: `2026-05-29T21:26:59`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `55204`
- label_rows: `1380100`
- latest_as_of_candidate_count: `145`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.396078`
- backtest_trade_count: `280`
- backtest_total_return_pct: `61.958058`
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
| `signal_close_retest_entry` | `20` | `38044` | `0.689153` | `1.744216` | `1.744216` | `0.492114` | `-16.877761` | `17.150696` |
| `open_guarded_retest_entry` | `20` | `33592` | `0.608507` | `1.550696` | `1.550696` | `0.483955` | `-16.834328` | `16.496974` |
| `next_open_entry` | `20` | `53860` | `0.975654` | `2.052963` | `2.052963` | `0.487189` | `-16.64005` | `17.311995` |
| `close_zone_limit_entry` | `20` | `41527` | `0.752246` | `1.751367` | `1.751367` | `0.488766` | `-16.764499` | `16.949863` |
| `atr_pullback_entry` | `20` | `17605` | `0.318908` | `2.518705` | `2.518705` | `0.522068` | `-16.880626` | `17.976331` |
| `signal_close_retest_entry` | `10` | `38273` | `0.693301` | `0.953073` | `0.953073` | `0.499543` | `-12.154952` | `11.189445` |
| `open_guarded_retest_entry` | `10` | `33763` | `0.611604` | `0.733595` | `0.733595` | `0.487812` | `-12.074349` | `10.672221` |
| `next_open_entry` | `10` | `54348` | `0.984494` | `1.133973` | `1.133973` | `0.49919` | `-11.971831` | `11.320755` |
| `close_zone_limit_entry` | `10` | `41781` | `0.756847` | `0.951731` | `0.951731` | `0.496637` | `-12.067609` | `11.082433` |
| `atr_pullback_entry` | `10` | `17689` | `0.32043` | `1.396078` | `1.396078` | `0.529934` | `-12.569641` | `11.496648` |
| `signal_close_retest_entry` | `5` | `38502` | `0.697449` | `0.351665` | `0.351665` | `0.488962` | `-8.544353` | `7.100897` |
| `open_guarded_retest_entry` | `5` | `33932` | `0.614666` | `0.215691` | `0.215691` | `0.479606` | `-8.387002` | `6.652979` |
| `next_open_entry` | `5` | `54613` | `0.989294` | `0.517279` | `0.517279` | `0.492667` | `-8.31105` | `7.33704` |
| `close_zone_limit_entry` | `5` | `42014` | `0.761068` | `0.379876` | `0.379876` | `0.489146` | `-8.402462` | `7.048571` |
| `atr_pullback_entry` | `5` | `17869` | `0.32369` | `0.361203` | `0.361203` | `0.499916` | `-9.195791` | `7.243176` |
| `signal_close_retest_entry` | `3` | `38622` | `0.699623` | `0.147793` | `0.147793` | `0.486122` | `-6.306191` | `5.117815` |
| `open_guarded_retest_entry` | `3` | `34020` | `0.61626` | `0.020226` | `0.020226` | `0.474103` | `-6.213799` | `4.727953` |
| `next_open_entry` | `3` | `54849` | `0.993569` | `0.236784` | `0.236784` | `0.479626` | `-6.278109` | `5.344485` |
| `close_zone_limit_entry` | `3` | `42140` | `0.76335` | `0.148337` | `0.148337` | `0.485477` | `-6.240046` | `5.088259` |
| `atr_pullback_entry` | `3` | `17970` | `0.32552` | `0.16383` | `0.16383` | `0.493322` | `-6.794755` | `5.303745` |
| `signal_close_retest_entry` | `1` | `38821` | `0.703228` | `-0.044969` | `-0.044969` | `0.471652` | `-3.255528` | `2.651258` |
| `open_guarded_retest_entry` | `1` | `34178` | `0.619122` | `-0.155795` | `-0.155795` | `0.449032` | `-3.162942` | `2.358491` |
| `next_open_entry` | `1` | `55059` | `0.997373` | `0.025331` | `0.025331` | `0.456837` | `-3.401361` | `2.718325` |
| `close_zone_limit_entry` | `1` | `42339` | `0.766955` | `-0.039069` | `-0.039069` | `0.471055` | `-3.234978` | `2.603563` |
| `atr_pullback_entry` | `1` | `18142` | `0.328636` | `-0.118804` | `-0.118804` | `0.467369` | `-3.248352` | `3.306716` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `280`
- total_return_pct: `61.958058`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.525`
- skipped_capacity_count: `16818`
- skipped_same_symbol_count: `591`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `15.733652` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `280` | `61.958058` | `-23.08101` | `0.525` |
| `exclude_market_risk_off` | `262` | `60.553483` | `-24.651169` | `0.51145` |
| `require_foreign_not_sell` | `280` | `52.969744` | `-23.08101` | `0.525` |
| `exclude_risk_off_and_foreign_sell` | `262` | `75.374658` | `-23.78546` | `0.519084` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `037270` | YG PLUS | `3870.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.145861` | `1.976285` | `0.954957` | `0.117127` |
| `381970` | 케이카 | `9080.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.493813` | `0.665188` | `0.949492` | `0.025838` |
| `009240` | 한샘 | `30800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-37.777778` | `4.40678` | `1.019342` | `0.120973` |
| `950210` | 프레스티지바이오파마 | `6930.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-50.92068` | `1.911765` | `1.305391` | `0.016317` |
| `272550` | 삼양패키징 | `9600.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.186047` | `1.159115` | `0.682323` | `-0.023379` |
| `003520` | 영진약품 | `1299.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.088435` | `0.077042` | `1.503049` | `0.023739` |
| `249420` | 일동제약 | `21350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.608213` | `6.75` | `1.644804` | `0.111138` |
| `007110` | 일신석재 | `1167.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.061633` | `1.56658` | `0.877049` | `0.036087` |
| `008730` | 율촌화학 | `19640.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-39.846861` | `2.025974` | `1.16609` | `0.055883` |
| `192650` | 드림텍 | `4945.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-40.919952` | `1.644399` | `0.871292` | `-0.056908` |
| `005870` | 휴니드 | `6270.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.088608` | `1.129032` | `0.568465` | `-0.007069` |
| `007570` | 일양약품 | `8910.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-38.972603` | `1.020408` | `0.815506` | `-0.032863` |
| `285130` | SK케미칼 | `43150.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.26401` | `1.768868` | `1.284166` | `-0.06276` |
| `000120` | CJ대한통운 | `85500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-39.361702` | `3.26087` | `1.088922` | `-0.010982` |
| `034230` | 파라다이스 | `14100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-35.469108` | `4.059041` | `0.774826` | `0.004186` |
| `009580` | 무림P&P | `2050.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-50.780312` | `1.736973` | `0.624875` | `-0.017644` |
| `006220` | 제주은행 | `9950.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.24016` | `1.220753` | `0.927178` | `-0.017119` |
| `003350` | 한국화장품제조 | `8740.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-84.252252` | `3.187721` | `0.40706` | `-0.077386` |
| `001390` | KG케미칼 | `4770.0` |  |  | `market_risk_off` | `dual_buy` | `-35.540541` | `0.845666` | `0.520331` | `0.083937` |
| `105630` | 한세실업 | `8860.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-42.985843` | `1.605505` | `1.778477` | `-0.08511` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
