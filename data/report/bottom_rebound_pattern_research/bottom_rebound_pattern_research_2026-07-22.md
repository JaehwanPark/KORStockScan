# Bottom Rebound Pattern Research - 2026-07-22

- generated_at: `2026-07-22T20:53:52`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58893`
- label_rows: `1472325`
- latest_as_of_candidate_count: `181`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.265416`
- backtest_trade_count: `294`
- backtest_total_return_pct: `215.275468`
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
| `signal_close_retest_entry` | `20` | `39115` | `0.664171` | `1.808436` | `1.808436` | `0.486437` | `-17.407515` | `17.193499` |
| `open_guarded_retest_entry` | `20` | `34459` | `0.585112` | `1.52455` | `1.52455` | `0.478946` | `-17.292069` | `16.557447` |
| `next_open_entry` | `20` | `55722` | `0.946157` | `2.009983` | `2.009983` | `0.481515` | `-17.209729` | `17.385928` |
| `close_zone_limit_entry` | `20` | `42643` | `0.724076` | `1.796326` | `1.796326` | `0.483362` | `-17.233271` | `17.004918` |
| `atr_pullback_entry` | `20` | `18312` | `0.310937` | `2.380883` | `2.380883` | `0.512833` | `-17.755629` | `17.954088` |
| `signal_close_retest_entry` | `10` | `40302` | `0.684326` | `0.918452` | `0.918452` | `0.491837` | `-12.884423` | `11.421158` |
| `open_guarded_retest_entry` | `10` | `35174` | `0.597253` | `0.704784` | `0.704784` | `0.482515` | `-12.612715` | `10.809597` |
| `next_open_entry` | `10` | `57216` | `0.971525` | `1.017663` | `1.017663` | `0.489968` | `-12.77142` | `11.485452` |
| `close_zone_limit_entry` | `10` | `43850` | `0.744571` | `0.921691` | `0.921691` | `0.489532` | `-12.74978` | `11.295012` |
| `atr_pullback_entry` | `10` | `19239` | `0.326677` | `1.265416` | `1.265416` | `0.515255` | `-13.612186` | `11.894802` |
| `signal_close_retest_entry` | `5` | `40971` | `0.695685` | `0.359149` | `0.359149` | `0.485856` | `-8.970639` | `7.441197` |
| `open_guarded_retest_entry` | `5` | `35514` | `0.603026` | `0.217458` | `0.217458` | `0.477192` | `-8.768937` | `6.843743` |
| `next_open_entry` | `5` | `57964` | `0.984226` | `0.475114` | `0.475114` | `0.487751` | `-8.81459` | `7.608145` |
| `close_zone_limit_entry` | `5` | `44527` | `0.756066` | `0.379754` | `0.379754` | `0.485907` | `-8.849757` | `7.350552` |
| `atr_pullback_entry` | `5` | `19738` | `0.33515` | `0.375623` | `0.375623` | `0.496555` | `-9.830172` | `7.840666` |
| `signal_close_retest_entry` | `3` | `41154` | `0.698793` | `0.213406` | `0.213406` | `0.486563` | `-6.679498` | `5.354342` |
| `open_guarded_retest_entry` | `3` | `35591` | `0.604333` | `0.038258` | `0.038258` | `0.473238` | `-6.493418` | `4.827416` |
| `next_open_entry` | `3` | `58345` | `0.990695` | `0.243362` | `0.243362` | `0.47699` | `-6.666667` | `5.535055` |
| `close_zone_limit_entry` | `3` | `44726` | `0.759445` | `0.207` | `0.207` | `0.485601` | `-6.584552` | `5.304036` |
| `atr_pullback_entry` | `3` | `19803` | `0.336254` | `0.329166` | `0.329166` | `0.498056` | `-7.337697` | `5.711445` |
| `signal_close_retest_entry` | `1` | `41373` | `0.702511` | `-0.002932` | `-0.002932` | `0.474271` | `-3.367615` | `2.771619` |
| `open_guarded_retest_entry` | `1` | `35716` | `0.606456` | `-0.148628` | `-0.148628` | `0.449182` | `-3.228867` | `2.420499` |
| `next_open_entry` | `1` | `58712` | `0.996927` | `0.045014` | `0.045014` | `0.457709` | `-3.508772` | `2.839117` |
| `close_zone_limit_entry` | `1` | `44957` | `0.763367` | `-0.001098` | `-0.001098` | `0.473185` | `-3.340046` | `2.724371` |
| `atr_pullback_entry` | `1` | `19942` | `0.338614` | `-0.019373` | `-0.019373` | `0.476682` | `-3.406184` | `3.472194` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `294`
- total_return_pct: `215.275468`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.506803`
- skipped_capacity_count: `18302`
- skipped_same_symbol_count: `643`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `124.77254` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `294` | `215.275468` | `-23.08101` | `0.506803` |
| `exclude_market_risk_off` | `275` | `5.436202` | `-42.439232` | `0.487273` |
| `require_foreign_not_sell` | `294` | `202.803805` | `-23.544095` | `0.503401` |
| `exclude_risk_off_and_foreign_sell` | `275` | `13.707947` | `-37.923439` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `037270` | YG PLUS | `3100.0` |  |  | `market_neutral` | `dual_buy` | `-58.611482` | `1.80624` | `0.645152` | `0.145958` |
| `249420` | 일동제약 | `13450.0` |  |  | `market_neutral` | `foreign_buy_only` | `-66.62531` | `1.051841` | `0.500072` | `0.224649` |
| `008730` | 율촌화학 | `12860.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.80756` | `0.39032` | `0.599425` | `0.084895` |
| `019170` | 신풍제약 | `7610.0` |  |  | `market_neutral` | `dual_buy` | `-44.044118` | `-0.0` | `0.684447` | `0.106819` |
| `005250` | 녹십자홀딩스 | `9220.0` |  |  | `market_neutral` | `foreign_buy_only` | `-47.464387` | `0.217391` | `0.527722` | `0.074534` |
| `000390` | SP삼화 | `5820.0` |  |  | `market_neutral` | `dual_buy` | `-52.874494` | `0.692042` | `0.544519` | `0.075953` |
| `161000` | 애경케미칼 | `8570.0` |  |  | `market_neutral` | `foreign_buy_only` | `-57.064128` | `1.420118` | `0.532437` | `0.102515` |
| `128820` | 대성산업 | `4005.0` |  |  | `market_neutral` | `foreign_buy_only` | `-69.520548` | `0.125` | `0.885584` | `0.056798` |
| `034230` | 파라다이스 | `9730.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.469108` | `0.724638` | `0.762371` | `0.05708` |
| `001060` | JW중외제약 | `23400.0` |  |  | `market_neutral` | `dual_buy` | `-38.823529` | `0.862069` | `0.498312` | `0.103033` |
| `003530` | 한화투자증권 | `4235.0` |  |  | `market_neutral` | `foreign_buy_only` | `-57.135628` | `0.236686` | `0.632973` | `0.029478` |
| `003160` | 디아이 | `19330.0` |  |  | `market_neutral` | `foreign_buy_only` | `-50.435897` | `0.05176` | `1.004146` | `0.03465` |
| `066970` | 엘앤에프 | `82400.0` |  |  | `market_neutral` | `foreign_buy_only` | `-62.374429` | `0.365408` | `0.770249` | `0.019156` |
| `003570` | SNT다이내믹스 | `32450.0` |  |  | `market_neutral` | `foreign_buy_only` | `-47.491909` | `1.40625` | `1.488501` | `0.0443` |
| `010660` | 화천기계 | `2585.0` |  |  | `market_neutral` | `foreign_buy_only` | `-60.7739` | `1.972387` | `0.424028` | `0.045774` |
| `008700` | 아남전자 | `1028.0` |  |  | `market_neutral` | `dual_buy` | `-46.955624` | `0.390625` | `0.821801` | `0.012732` |
| `051910` | LG화학 | `252000.0` |  |  | `market_neutral` | `foreign_buy_only` | `-42.4` | `1.408451` | `0.511311` | `0.055023` |
| `272210` | 한화시스템 | `61900.0` |  |  | `market_neutral` | `foreign_buy_only` | `-66.358696` | `1.976936` | `0.660896` | `0.051964` |
| `016610` | DB증권 | `8890.0` |  |  | `market_neutral` | `foreign_buy_only` | `-44.71393` | `2.183908` | `0.608278` | `0.064186` |
| `103140` | 풍산 | `61400.0` |  |  | `market_neutral` | `foreign_buy_only` | `-61.432161` | `3.193277` | `0.671068` | `0.141327` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
