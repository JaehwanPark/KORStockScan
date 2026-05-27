# Bottom Rebound Pattern Research - 2026-05-27

- generated_at: `2026-05-27T21:26:54`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `55059`
- label_rows: `1376475`
- latest_as_of_candidate_count: `134`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.401377`
- backtest_trade_count: `278`
- backtest_total_return_pct: `71.054638`
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
| `signal_close_retest_entry` | `20` | `37987` | `0.689933` | `1.735123` | `1.735123` | `0.492142` | `-16.881056` | `17.117583` |
| `open_guarded_retest_entry` | `20` | `33588` | `0.610037` | `1.548098` | `1.548098` | `0.483923` | `-16.834897` | `16.495982` |
| `next_open_entry` | `20` | `53755` | `0.976316` | `2.055813` | `2.055813` | `0.487508` | `-16.629976` | `17.288048` |
| `close_zone_limit_entry` | `20` | `41464` | `0.753083` | `1.743066` | `1.743066` | `0.48881` | `-16.765266` | `16.920956` |
| `atr_pullback_entry` | `20` | `17579` | `0.319276` | `2.514994` | `2.514994` | `0.522043` | `-16.880799` | `17.945913` |
| `signal_close_retest_entry` | `10` | `38252` | `0.694746` | `0.960789` | `0.960789` | `0.499817` | `-12.142155` | `11.191013` |
| `open_guarded_retest_entry` | `10` | `33746` | `0.612906` | `0.739924` | `0.739924` | `0.488028` | `-12.060302` | `10.67241` |
| `next_open_entry` | `10` | `54319` | `0.98656` | `1.141598` | `1.141598` | `0.499439` | `-11.964549` | `11.32454` |
| `close_zone_limit_entry` | `10` | `41759` | `0.758441` | `0.959267` | `0.959267` | `0.496899` | `-12.05708` | `11.083448` |
| `atr_pullback_entry` | `10` | `17681` | `0.321128` | `1.401377` | `1.401377` | `0.530174` | `-12.565217` | `11.496443` |
| `signal_close_retest_entry` | `5` | `38436` | `0.698088` | `0.364359` | `0.364359` | `0.489671` | `-8.501095` | `7.108022` |
| `open_guarded_retest_entry` | `5` | `33887` | `0.615467` | `0.224999` | `0.224999` | `0.480214` | `-8.361826` | `6.655728` |
| `next_open_entry` | `5` | `54545` | `0.990665` | `0.527188` | `0.527188` | `0.493207` | `-8.290685` | `7.339704` |
| `close_zone_limit_entry` | `5` | `41948` | `0.761874` | `0.391621` | `0.391621` | `0.489821` | `-8.373718` | `7.050692` |
| `atr_pullback_entry` | `5` | `17806` | `0.323399` | `0.386182` | `0.386182` | `0.501404` | `-9.134815` | `7.251762` |
| `signal_close_retest_entry` | `3` | `38603` | `0.701121` | `0.150361` | `0.150361` | `0.486335` | `-6.302756` | `5.117424` |
| `open_guarded_retest_entry` | `3` | `34011` | `0.617719` | `0.021978` | `0.021978` | `0.474229` | `-6.210818` | `4.729254` |
| `next_open_entry` | `3` | `54719` | `0.993825` | `0.245464` | `0.245464` | `0.48051` | `-6.25` | `5.345891` |
| `close_zone_limit_entry` | `3` | `42116` | `0.764925` | `0.151289` | `0.151289` | `0.48573` | `-6.235563` | `5.088257` |
| `atr_pullback_entry` | `3` | `17967` | `0.326323` | `0.164207` | `0.164207` | `0.493349` | `-6.787585` | `5.30311` |
| `signal_close_retest_entry` | `1` | `38696` | `0.70281` | `-0.041811` | `-0.041811` | `0.472271` | `-3.243664` | `2.650002` |
| `open_guarded_retest_entry` | `1` | `34084` | `0.619045` | `-0.153104` | `-0.153104` | `0.449683` | `-3.149107` | `2.358491` |
| `next_open_entry` | `1` | `54925` | `0.997566` | `0.028639` | `0.028639` | `0.457478` | `-3.389831` | `2.721088` |
| `close_zone_limit_entry` | `1` | `42214` | `0.766705` | `-0.035906` | `-0.035906` | `0.471739` | `-3.220197` | `2.603037` |
| `atr_pullback_entry` | `1` | `18040` | `0.327649` | `-0.118149` | `-0.118149` | `0.467517` | `-3.234085` | `3.303304` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `278`
- total_return_pct: `71.054638`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.528777`
- skipped_capacity_count: `16812`
- skipped_same_symbol_count: `591`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `22.155389` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `278` | `71.054638` | `-23.08101` | `0.528777` |
| `exclude_market_risk_off` | `262` | `60.553483` | `-24.651169` | `0.51145` |
| `require_foreign_not_sell` | `278` | `61.561484` | `-23.08101` | `0.528777` |
| `exclude_risk_off_and_foreign_sell` | `262` | `75.374658` | `-23.78546` | `0.519084` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `037270` | YG PLUS | `4005.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.371879` | `1.392405` | `1.379678` | `0.12312` |
| `272550` | 삼양패키징 | `10010.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-41.802326` | `1.624365` | `0.533061` | `-0.014154` |
| `009240` | 한샘 | `30200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.989899` | `1.342282` | `1.912825` | `0.104633` |
| `381970` | 케이카 | `9410.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.549204` | `0.212993` | `1.034123` | `0.014929` |
| `950210` | 프레스티지바이오파마 | `7390.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.66289` | `4.231312` | `1.053456` | `0.013115` |
| `034230` | 파라다이스 | `14050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-35.697941` | `1.079137` | `1.031006` | `0.006237` |
| `007110` | 일신석재 | `1199.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.418079` | `1.43824` | `1.313058` | `0.035311` |
| `008730` | 율촌화학 | `20250.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-37.97856` | `0.997506` | `1.195974` | `0.060333` |
| `105630` | 한세실업 | `9090.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-41.505792` | `1.90583` | `1.78975` | `-0.0797` |
| `005870` | 휴니드 | `6610.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.219409` | `0.30349` | `0.609171` | `-0.01039` |
| `029780` | 삼성카드 | `46850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-23.070608` | `0.752688` | `1.124917` | `0.134386` |
| `003520` | 영진약품 | `1380.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-37.414966` | `0.729927` | `1.793386` | `0.000156` |
| `000520` | 삼일제약 | `7450.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-42.068429` | `4.929577` | `0.902429` | `-0.033075` |
| `000120` | CJ대한통운 | `85800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-39.148936` | `1.538462` | `1.04522` | `0.019232` |
| `007570` | 일양약품 | `9310.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-36.232877` | `0.976139` | `1.138516` | `-0.036025` |
| `009580` | 무림P&P | `2100.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.579832` | `1.204819` | `0.90054` | `-0.014233` |
| `009270` | 신원 | `1101.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-33.151184` | `2.418605` | `1.483045` | `0.015269` |
| `009200` | 무림페이퍼 | `1620.0` |  |  | `market_risk_off` | `inst_buy_only` | `-39.664804` | `0.934579` | `1.236654` | `-0.007053` |
| `004090` | 한국석유 | `13030.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-32.135417` | `1.321928` | `0.474109` | `-0.001118` |
| `249420` | 일동제약 | `21900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.387347` | `9.5` | `1.10428` | `0.088672` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
