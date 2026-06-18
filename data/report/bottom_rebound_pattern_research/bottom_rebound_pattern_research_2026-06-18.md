# Bottom Rebound Pattern Research - 2026-06-18

- generated_at: `2026-06-18T20:26:30`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57188`
- label_rows: `1429700`
- latest_as_of_candidate_count: `115`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.369025`
- backtest_trade_count: `291`
- backtest_total_return_pct: `15.668891`
- backtest_max_drawdown_pct: `-23.12113`
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
| `signal_close_retest_entry` | `20` | `38740` | `0.677415` | `1.818807` | `1.818807` | `0.491043` | `-16.952741` | `17.22018` |
| `open_guarded_retest_entry` | `20` | `34190` | `0.597853` | `1.621095` | `1.621095` | `0.483241` | `-16.910295` | `16.589618` |
| `next_open_entry` | `20` | `55228` | `0.965727` | `2.026273` | `2.026273` | `0.485859` | `-16.759049` | `17.371603` |
| `close_zone_limit_entry` | `20` | `42268` | `0.739106` | `1.822292` | `1.822292` | `0.48791` | `-16.828982` | `17.01772` |
| `atr_pullback_entry` | `20` | `17953` | `0.313929` | `2.410776` | `2.410776` | `0.5193` | `-16.969231` | `17.966577` |
| `signal_close_retest_entry` | `10` | `39171` | `0.684951` | `0.994353` | `0.994353` | `0.497154` | `-12.427` | `11.229591` |
| `open_guarded_retest_entry` | `10` | `34486` | `0.603029` | `0.786055` | `0.786055` | `0.486864` | `-12.264615` | `10.72523` |
| `next_open_entry` | `10` | `55774` | `0.975275` | `1.115065` | `1.115065` | `0.496432` | `-12.253829` | `11.346154` |
| `close_zone_limit_entry` | `10` | `42717` | `0.746957` | `0.995261` | `0.995261` | `0.494417` | `-12.309585` | `11.10058` |
| `atr_pullback_entry` | `10` | `18261` | `0.319315` | `1.369025` | `1.369025` | `0.524889` | `-12.954733` | `11.541615` |
| `signal_close_retest_entry` | `5` | `39762` | `0.695286` | `0.394719` | `0.394719` | `0.488984` | `-8.76798` | `7.230714` |
| `open_guarded_retest_entry` | `5` | `34833` | `0.609096` | `0.25283` | `0.25283` | `0.480062` | `-8.565152` | `6.733137` |
| `next_open_entry` | `5` | `56487` | `0.987742` | `0.524359` | `0.524359` | `0.49137` | `-8.557211` | `7.444568` |
| `close_zone_limit_entry` | `5` | `43315` | `0.757414` | `0.410809` | `0.410809` | `0.488676` | `-8.622623` | `7.164831` |
| `atr_pullback_entry` | `5` | `18757` | `0.327988` | `0.435262` | `0.435262` | `0.501573` | `-9.505597` | `7.50361` |
| `signal_close_retest_entry` | `3` | `39870` | `0.697174` | `0.170538` | `0.170538` | `0.486657` | `-6.451754` | `5.232726` |
| `open_guarded_retest_entry` | `3` | `34887` | `0.610041` | `0.04476` | `0.04476` | `0.474475` | `-6.306495` | `4.781384` |
| `next_open_entry` | `3` | `56908` | `0.995104` | `0.257491` | `0.257491` | `0.480266` | `-6.412544` | `5.487532` |
| `close_zone_limit_entry` | `3` | `43436` | `0.75953` | `0.168374` | `0.168374` | `0.485519` | `-6.373464` | `5.18018` |
| `atr_pullback_entry` | `3` | `18783` | `0.328443` | `0.206508` | `0.206508` | `0.495661` | `-7.016264` | `5.439436` |
| `signal_close_retest_entry` | `1` | `39951` | `0.698591` | `-0.040415` | `-0.040415` | `0.472704` | `-3.259614` | `2.694611` |
| `open_guarded_retest_entry` | `1` | `34954` | `0.611212` | `-0.149732` | `-0.149732` | `0.450621` | `-3.16235` | `2.383017` |
| `next_open_entry` | `1` | `57073` | `0.997989` | `0.026527` | `0.026527` | `0.456591` | `-3.418803` | `2.772277` |
| `close_zone_limit_entry` | `1` | `43523` | `0.761051` | `-0.035092` | `-0.035092` | `0.472141` | `-3.241546` | `2.651084` |
| `atr_pullback_entry` | `1` | `18830` | `0.329265` | `-0.115397` | `-0.115397` | `0.467924` | `-3.268318` | `3.334346` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `15.668891`
- max_drawdown_pct: `-23.12113`
- diagnostic_win_rate: `0.512027`
- skipped_capacity_count: `17347`
- skipped_same_symbol_count: `623`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-17.264909` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `15.668891` | `-23.12113` | `0.512027` |
| `exclude_market_risk_off` | `270` | `27.212786` | `-30.550745` | `0.496296` |
| `require_foreign_not_sell` | `291` | `17.297991` | `-23.08101` | `0.505155` |
| `exclude_risk_off_and_foreign_sell` | `270` | `24.942563` | `-31.790127` | `0.492593` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `128820` | 대성산업 | `4910.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-62.633181` | `0.614754` | `0.801474` | `-0.013364` |
| `465770` | STX그린로지스 | `2495.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-74.010417` | `0.200803` | `0.598348` | `-0.018656` |
| `009580` | 무림P&P | `1740.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.633484` | `1.457726` | `0.4864` | `0.019007` |
| `001430` | 세아베스틸지주 | `43200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.297297` | `0.934579` | `0.775818` | `0.016368` |
| `014530` | 극동유화 | `3185.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-50.772798` | `0.157233` | `0.993068` | `-0.054679` |
| `017860` | DS단석 | `13920.0` |  |  | `market_risk_off` | `inst_buy_only` | `-47.372401` | `0.143885` | `0.477196` | `-0.029291` |
| `117580` | 대성에너지 | `6940.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-57.027864` | `1.461988` | `0.660889` | `-0.059868` |
| `005870` | 휴니드 | `5390.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-48.568702` | `1.315789` | `0.709429` | `-0.04697` |
| `272550` | 삼양패키징 | `8830.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.657925` | `3.882353` | `0.560416` | `0.013444` |
| `025860` | 남해화학 | `6290.0` |  |  | `market_risk_off` | `dual_buy` | `-50.936037` | `4.48505` | `0.402379` | `0.024361` |
| `271940` | 일진하이솔루스 | `12290.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-37.423625` | `0.244698` | `0.61054` | `-0.073872` |
| `084670` | 동양고속 | `34100.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-64.105263` | `3.490137` | `0.532224` | `-0.01517` |
| `009070` | KCTC | `4445.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.020262` | `7.36715` | `0.467759` | `0.040333` |
| `105630` | 한세실업 | `8650.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.337194` | `3.841537` | `0.911679` | `-0.098792` |
| `026890` | 스틱인베스트먼트 | `6820.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.859327` | `6.5625` | `1.040398` | `0.075787` |
| `035510` | 신세계 I&C | `14900.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.146758` | `4.561404` | `0.429608` | `-0.001541` |
| `003520` | 영진약품 | `1255.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.0839` | `4.322527` | `0.585642` | `-0.114558` |
| `003350` | 한국화장품제조 | `8070.0` |  |  | `market_risk_off` | `dual_buy` | `-84.450867` | `6.184211` | `0.743455` | `0.053022` |
| `084680` | 이월드 | `1173.0` |  |  | `market_risk_off` | `inst_buy_only` | `-41.203008` | `3.80531` | `0.556974` | `-0.017307` |
| `000520` | 삼일제약 | `7050.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.178849` | `6.495468` | `0.495645` | `-0.099727` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
