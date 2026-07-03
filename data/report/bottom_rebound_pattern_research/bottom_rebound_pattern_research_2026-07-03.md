# Bottom Rebound Pattern Research - 2026-07-03

- generated_at: `2026-07-03T20:52:36`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57645`
- label_rows: `1441125`
- latest_as_of_candidate_count: `135`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.319961`
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
| `signal_close_retest_entry` | `20` | `38668` | `0.670795` | `1.84877` | `1.84877` | `0.488569` | `-17.121004` | `17.196464` |
| `open_guarded_retest_entry` | `20` | `34078` | `0.59117` | `1.58101` | `1.58101` | `0.481043` | `-17.070013` | `16.541157` |
| `next_open_entry` | `20` | `55073` | `0.955382` | `2.103908` | `2.103908` | `0.483921` | `-16.936098` | `17.401344` |
| `close_zone_limit_entry` | `20` | `42194` | `0.731963` | `1.834867` | `1.834867` | `0.485259` | `-16.989131` | `17.006891` |
| `atr_pullback_entry` | `20` | `17949` | `0.311371` | `2.514058` | `2.514058` | `0.517968` | `-17.175875` | `17.988354` |
| `signal_close_retest_entry` | `10` | `39609` | `0.687119` | `0.929686` | `0.929686` | `0.493145` | `-12.761879` | `11.325216` |
| `open_guarded_retest_entry` | `10` | `34647` | `0.601041` | `0.685054` | `0.685054` | `0.482524` | `-12.540451` | `10.725768` |
| `next_open_entry` | `10` | `56184` | `0.974655` | `1.074479` | `1.074479` | `0.492863` | `-12.549801` | `11.406071` |
| `close_zone_limit_entry` | `10` | `43145` | `0.74846` | `0.937043` | `0.937043` | `0.49088` | `-12.614179` | `11.189541` |
| `atr_pullback_entry` | `10` | `18754` | `0.325336` | `1.319961` | `1.319961` | `0.518343` | `-13.465672` | `11.73765` |
| `signal_close_retest_entry` | `5` | `40041` | `0.694614` | `0.368989` | `0.368989` | `0.486726` | `-8.908909` | `7.296849` |
| `open_guarded_retest_entry` | `5` | `34950` | `0.606297` | `0.21259` | `0.21259` | `0.477425` | `-8.736567` | `6.758632` |
| `next_open_entry` | `5` | `56802` | `0.985376` | `0.487406` | `0.487406` | `0.488838` | `-8.756286` | `7.493109` |
| `close_zone_limit_entry` | `5` | `43587` | `0.756128` | `0.390439` | `0.390439` | `0.486934` | `-8.767427` | `7.228916` |
| `atr_pullback_entry` | `5` | `19101` | `0.331356` | `0.410647` | `0.410647` | `0.498299` | `-9.708673` | `7.613086` |
| `signal_close_retest_entry` | `3` | `40389` | `0.700651` | `0.237866` | `0.237866` | `0.488648` | `-6.606311` | `5.318364` |
| `open_guarded_retest_entry` | `3` | `35085` | `0.608639` | `0.045781` | `0.045781` | `0.473735` | `-6.466043` | `4.799861` |
| `next_open_entry` | `3` | `57259` | `0.993304` | `0.282993` | `0.282993` | `0.479837` | `-6.579781` | `5.514472` |
| `close_zone_limit_entry` | `3` | `43947` | `0.762373` | `0.231443` | `0.231443` | `0.48786` | `-6.51801` | `5.269616` |
| `atr_pullback_entry` | `3` | `19321` | `0.335172` | `0.352916` | `0.352916` | `0.498887` | `-7.236359` | `5.647972` |
| `signal_close_retest_entry` | `1` | `40595` | `0.704224` | `0.007698` | `0.007698` | `0.475625` | `-3.33422` | `2.749774` |
| `open_guarded_retest_entry` | `1` | `35215` | `0.610894` | `-0.142315` | `-0.142315` | `0.450887` | `-3.210874` | `2.40179` |
| `next_open_entry` | `1` | `57510` | `0.997658` | `0.056549` | `0.056549` | `0.458946` | `-3.479057` | `2.808018` |
| `close_zone_limit_entry` | `1` | `44155` | `0.765981` | `0.009169` | `0.009169` | `0.474578` | `-3.31353` | `2.698694` |
| `atr_pullback_entry` | `1` | `19455` | `0.337497` | `-0.007703` | `-0.007703` | `0.478129` | `-3.369261` | `3.457545` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `191.104448`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.512027`
- skipped_capacity_count: `17833`
- skipped_same_symbol_count: `630`

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
| `249420` | 일동제약 | `16370.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.753129` | `4.201146` | `0.561622` | `0.260974` |
| `019170` | 신풍제약 | `8140.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.701087` | `3.037975` | `0.556235` | `-3.1e-05` |
| `011170` | 롯데케미칼 | `63500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.593776` | `3.084416` | `0.586852` | `-0.0017` |
| `381970` | 케이카 | `8440.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.430797` | `3.304774` | `0.618551` | `0.039746` |
| `950210` | 프레스티지바이오파마 | `6050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-57.152975` | `4.490501` | `1.067321` | `0.115459` |
| `005010` | 휴스틸 | `3955.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.523416` | `4.216074` | `0.452245` | `0.024939` |
| `108320` | LX세미콘 | `39250.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.242515` | `4.249668` | `0.477989` | `0.073235` |
| `128820` | 대성산업 | `4300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.275495` | `4.116223` | `0.423797` | `0.022741` |
| `103140` | 풍산 | `66800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.040201` | `8.441558` | `0.58603` | `0.170554` |
| `011690` | 와이투솔루션 | `3435.0` |  |  | `market_risk_off` | `dual_buy` | `-65.126904` | `7.849294` | `0.463412` | `0.076001` |
| `017960` | 한국카본 | `25950.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-52.033272` | `4.637097` | `0.692438` | `-0.013058` |
| `001430` | 세아베스틸지주 | `32100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-65.297297` | `6.644518` | `0.779001` | `0.049265` |
| `017810` | 풀무원 | `9310.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-32.142857` | `4.372197` | `0.501118` | `0.101168` |
| `000390` | SP삼화 | `6310.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.906883` | `9.16955` | `0.53235` | `0.085439` |
| `439260` | 대한조선 | `52300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-50.613787` | `5.125628` | `0.753855` | `0.000954` |
| `008350` | 남선알미늄 | `1046.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.985653` | `5.02008` | `0.506517` | `0.048747` |
| `377300` | 카카오페이 | `40600.0` |  |  | `market_risk_off` | `dual_buy` | `-44.911805` | `7.407407` | `0.738919` | `0.048364` |
| `000100` | 유한양행 | `70400.0` |  |  | `market_risk_off` | `dual_buy` | `-39.82906` | `5.864662` | `0.859565` | `0.056099` |
| `079900` | 전진건설로봇 | `37600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.428379` | `6.214689` | `0.501808` | `0.017395` |
| `021050` | 서원 | `1034.0` |  |  | `market_risk_off` | `inst_buy_only` | `-45.66474` | `4.761905` | `0.597727` | `-0.005083` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
