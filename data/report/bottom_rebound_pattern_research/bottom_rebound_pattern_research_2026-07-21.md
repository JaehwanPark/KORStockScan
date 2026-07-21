# Bottom Rebound Pattern Research - 2026-07-21

- generated_at: `2026-07-21T20:53:47`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58793`
- label_rows: `1469825`
- latest_as_of_candidate_count: `183`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.250816`
- backtest_trade_count: `294`
- backtest_total_return_pct: `178.001646`
- backtest_max_drawdown_pct: `-29.072033`
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
| `signal_close_retest_entry` | `20` | `39098` | `0.665011` | `1.810354` | `1.810354` | `0.486291` | `-17.408358` | `17.212272` |
| `open_guarded_retest_entry` | `20` | `34389` | `0.584917` | `1.547001` | `1.547001` | `0.479688` | `-17.237866` | `16.590417` |
| `next_open_entry` | `20` | `55699` | `0.947375` | `2.005561` | `2.005561` | `0.481499` | `-17.227988` | `17.418753` |
| `close_zone_limit_entry` | `20` | `42632` | `0.72512` | `1.792818` | `1.792818` | `0.483205` | `-17.245508` | `17.01772` |
| `atr_pullback_entry` | `20` | `18249` | `0.310394` | `2.410909` | `2.410909` | `0.513508` | `-17.624137` | `18.008112` |
| `signal_close_retest_entry` | `10` | `40096` | `0.681986` | `0.908477` | `0.908477` | `0.49157` | `-12.911169` | `11.397426` |
| `open_guarded_retest_entry` | `10` | `34952` | `0.594493` | `0.723089` | `0.723089` | `0.483577` | `-12.56412` | `10.799134` |
| `next_open_entry` | `10` | `57135` | `0.971799` | `1.006022` | `1.006022` | `0.489892` | `-12.88198` | `11.493482` |
| `close_zone_limit_entry` | `10` | `43652` | `0.742469` | `0.916888` | `0.916888` | `0.489279` | `-12.793495` | `11.269827` |
| `atr_pullback_entry` | `10` | `19061` | `0.324205` | `1.250816` | `1.250816` | `0.514611` | `-13.620414` | `11.757058` |
| `signal_close_retest_entry` | `5` | `40575` | `0.690133` | `0.358387` | `0.358387` | `0.486925` | `-8.984187` | `7.349148` |
| `open_guarded_retest_entry` | `5` | `35245` | `0.599476` | `0.232983` | `0.232983` | `0.478763` | `-8.697211` | `6.827989` |
| `next_open_entry` | `5` | `57964` | `0.9859` | `0.442345` | `0.442345` | `0.48713` | `-8.897279` | `7.567786` |
| `close_zone_limit_entry` | `5` | `44141` | `0.750787` | `0.376275` | `0.376275` | `0.486872` | `-8.855664` | `7.26879` |
| `atr_pullback_entry` | `5` | `19407` | `0.33009` | `0.402827` | `0.402827` | `0.499923` | `-9.82566` | `7.674135` |
| `signal_close_retest_entry` | `3` | `40806` | `0.694062` | `0.129732` | `0.129732` | `0.484144` | `-6.655767` | `5.315851` |
| `open_guarded_retest_entry` | `3` | `35328` | `0.600888` | `0.017108` | `0.017108` | `0.473279` | `-6.421524` | `4.827416` |
| `next_open_entry` | `3` | `58269` | `0.991087` | `0.212906` | `0.212906` | `0.477183` | `-6.636634` | `5.555556` |
| `close_zone_limit_entry` | `3` | `44379` | `0.754835` | `0.129387` | `0.129387` | `0.483224` | `-6.560014` | `5.273526` |
| `atr_pullback_entry` | `3` | `19539` | `0.332335` | `0.155441` | `0.155441` | `0.491837` | `-7.370314` | `5.61307` |
| `signal_close_retest_entry` | `1` | `41032` | `0.697906` | `-0.042371` | `-0.042371` | `0.47229` | `-3.347019` | `2.739726` |
| `open_guarded_retest_entry` | `1` | `35425` | `0.602538` | `-0.159207` | `-0.159207` | `0.449315` | `-3.216018` | `2.39581` |
| `next_open_entry` | `1` | `58610` | `0.996887` | `0.01022` | `0.01022` | `0.454376` | `-3.52425` | `2.803738` |
| `close_zone_limit_entry` | `1` | `44615` | `0.758849` | `-0.037385` | `-0.037385` | `0.47168` | `-3.321924` | `2.694065` |
| `atr_pullback_entry` | `1` | `19689` | `0.334887` | `-0.109604` | `-0.109604` | `0.469552` | `-3.403204` | `3.380327` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `294`
- total_return_pct: `178.001646`
- max_drawdown_pct: `-29.072033`
- diagnostic_win_rate: `0.503401`
- skipped_capacity_count: `18126`
- skipped_same_symbol_count: `641`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `98.339233` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `294` | `178.001646` | `-29.072033` | `0.503401` |
| `exclude_market_risk_off` | `275` | `12.693304` | `-38.477363` | `0.490909` |
| `require_foreign_not_sell` | `294` | `182.604324` | `-26.65353` | `0.5` |
| `exclude_risk_off_and_foreign_sell` | `275` | `15.805234` | `-36.778468` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `034230` | 파라다이스 | `9670.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.743707` | `1.57563` | `1.152724` | `0.090848` |
| `008730` | 율촌화학 | `12830.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.061644` | `3.218021` | `0.769137` | `0.08374` |
| `011170` | 롯데케미칼 | `56600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.635983` | `2.536232` | `0.960563` | `0.072679` |
| `004560` | 현대비앤지스틸 | `10710.0` |  |  | `market_risk_off` | `dual_buy` | `-52.505543` | `2.684564` | `0.425199` | `0.1242` |
| `004990` | 롯데지주 | `22200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.114058` | `2.068966` | `0.675741` | `0.17889` |
| `005010` | 휴스틸 | `3570.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.09589` | `1.420455` | `0.806624` | `0.062239` |
| `272210` | 한화시스템 | `60600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.065217` | `2.538071` | `0.628636` | `0.06862` |
| `003530` | 한화투자증권 | `4270.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.887689` | `3.892944` | `0.592686` | `0.071169` |
| `002710` | TCC스틸 | `8570.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.657952` | `1.300236` | `0.858111` | `0.088591` |
| `003160` | 디아이 | `19690.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.512821` | `3.795467` | `0.680204` | `0.068436` |
| `016610` | DB증권 | `8770.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.073024` | `2.09546` | `0.701094` | `0.080897` |
| `128820` | 대성산업 | `4030.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.330289` | `2.025316` | `0.659175` | `0.060197` |
| `005490` | POSCO홀딩스 | `303000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.095941` | `3.412969` | `0.682093` | `0.064781` |
| `103140` | 풍산 | `59800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.437186` | `1.528014` | `0.732698` | `0.113911` |
| `011500` | 한농화성 | `11500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.707361` | `2.495544` | `0.611431` | `0.114309` |
| `022100` | 포스코DX | `17600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.343195` | `2.984201` | `1.185955` | `0.052229` |
| `079900` | 전진건설로봇 | `29950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-59.251701` | `3.633218` | `0.675964` | `0.050271` |
| `051910` | LG화학 | `250500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-42.413793` | `3.08642` | `0.92031` | `0.058238` |
| `003540` | 대신증권 | `25450.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.908608` | `2.208835` | `0.623869` | `0.056831` |
| `017800` | 현대엘리베이터 | `67000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.178571` | `1.208459` | `0.557927` | `0.091854` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
