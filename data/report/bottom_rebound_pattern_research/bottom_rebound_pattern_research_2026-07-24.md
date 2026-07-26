# Bottom Rebound Pattern Research - 2026-07-24

- generated_at: `2026-07-24T20:53:33`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58960`
- label_rows: `1474000`
- latest_as_of_candidate_count: `140`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.316338`
- backtest_trade_count: `294`
- backtest_total_return_pct: `237.270296`
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
| `signal_close_retest_entry` | `20` | `39225` | `0.665282` | `1.764503` | `1.764503` | `0.484793` | `-17.512201` | `17.181502` |
| `open_guarded_retest_entry` | `20` | `34537` | `0.58577` | `1.474788` | `1.474788` | `0.47743` | `-17.357703` | `16.539667` |
| `next_open_entry` | `20` | `55812` | `0.946608` | `1.990756` | `1.990756` | `0.480542` | `-17.279982` | `17.395536` |
| `close_zone_limit_entry` | `20` | `42749` | `0.725051` | `1.7582` | `1.7582` | `0.481976` | `-17.332294` | `17.002987` |
| `atr_pullback_entry` | `20` | `18407` | `0.312195` | `2.299535` | `2.299535` | `0.50986` | `-17.910901` | `17.9364` |
| `signal_close_retest_entry` | `10` | `40462` | `0.686262` | `0.955066` | `0.955066` | `0.493154` | `-12.884423` | `11.510791` |
| `open_guarded_retest_entry` | `10` | `35187` | `0.596794` | `0.71973` | `0.71973` | `0.483218` | `-12.612512` | `10.830454` |
| `next_open_entry` | `10` | `57367` | `0.972982` | `1.049056` | `1.049056` | `0.490735` | `-12.771249` | `11.555785` |
| `close_zone_limit_entry` | `10` | `44009` | `0.746421` | `0.957772` | `0.957772` | `0.490741` | `-12.743572` | `11.358201` |
| `atr_pullback_entry` | `10` | `19369` | `0.328511` | `1.316338` | `1.316338` | `0.517373` | `-13.612186` | `12.053232` |
| `signal_close_retest_entry` | `5` | `40993` | `0.695268` | `0.357758` | `0.357758` | `0.485644` | `-8.972371` | `7.45098` |
| `open_guarded_retest_entry` | `5` | `35495` | `0.602018` | `0.215192` | `0.215192` | `0.477053` | `-8.768278` | `6.843789` |
| `next_open_entry` | `5` | `58090` | `0.985244` | `0.469675` | `0.469675` | `0.486968` | `-8.855594` | `7.611484` |
| `close_zone_limit_entry` | `5` | `44553` | `0.755648` | `0.37914` | `0.37914` | `0.485601` | `-8.85371` | `7.365077` |
| `atr_pullback_entry` | `5` | `19736` | `0.334735` | `0.379951` | `0.379951` | `0.496555` | `-9.819416` | `7.860626` |
| `signal_close_retest_entry` | `3` | `41256` | `0.699729` | `0.223261` | `0.223261` | `0.487275` | `-6.676238` | `5.376344` |
| `open_guarded_retest_entry` | `3` | `35646` | `0.604579` | `0.046854` | `0.046854` | `0.47405` | `-6.490371` | `4.848021` |
| `next_open_entry` | `3` | `58433` | `0.991062` | `0.250901` | `0.250901` | `0.477247` | `-6.666667` | `5.551766` |
| `close_zone_limit_entry` | `3` | `44827` | `0.760295` | `0.216397` | `0.216397` | `0.486292` | `-6.578106` | `5.323879` |
| `atr_pullback_entry` | `3` | `19899` | `0.3375` | `0.344906` | `0.344906` | `0.499724` | `-7.315549` | `5.749978` |
| `signal_close_retest_entry` | `1` | `41356` | `0.701425` | `-0.003252` | `-0.003252` | `0.474224` | `-3.368558` | `2.774367` |
| `open_guarded_retest_entry` | `1` | `35694` | `0.605393` | `-0.148772` | `-0.148772` | `0.449123` | `-3.229521` | `2.419865` |
| `next_open_entry` | `1` | `58820` | `0.997626` | `0.043353` | `0.043353` | `0.457446` | `-3.515687` | `2.844925` |
| `close_zone_limit_entry` | `1` | `44941` | `0.762229` | `-0.00139` | `-0.00139` | `0.473109` | `-3.340384` | `2.726687` |
| `atr_pullback_entry` | `1` | `19925` | `0.337941` | `-0.018771` | `-0.018771` | `0.476487` | `-3.405319` | `3.472622` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `294`
- total_return_pct: `237.270296`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.513605`
- skipped_capacity_count: `18430`
- skipped_same_symbol_count: `645`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `140.368714` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `294` | `237.270296` | `-23.08101` | `0.513605` |
| `exclude_market_risk_off` | `275` | `16.230148` | `-36.546494` | `0.487273` |
| `require_foreign_not_sell` | `294` | `225.130832` | `-23.08101` | `0.510204` |
| `exclude_risk_off_and_foreign_sell` | `275` | `24.794497` | `-31.870961` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `161000` | 애경케미칼 | `8710.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.362725` | `3.076923` | `0.579484` | `0.107379` |
| `011210` | 현대위아 | `56600.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-43.904856` | `4.044118` | `0.60989` | `0.094136` |
| `003530` | 한화투자증권 | `4270.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.781377` | `1.065089` | `0.665111` | `0.038081` |
| `034230` | 파라다이스 | `10030.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-54.09611` | `3.830228` | `0.506882` | `0.054886` |
| `016610` | DB증권 | `8850.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.962687` | `1.724138` | `0.843913` | `0.07642` |
| `066970` | 엘앤에프 | `81900.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-62.60274` | `1.361386` | `0.555207` | `0.020494` |
| `005690` | 파미셀 | `10590.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.451074` | `1.729107` | `0.651212` | `0.03737` |
| `010960` | 삼호개발 | `3095.0` |  |  | `market_risk_on` | `inst_buy_only` | `-40.480769` | `3.511706` | `0.844687` | `-0.011308` |
| `037270` | YG PLUS | `3180.0` |  |  | `market_risk_on` | `dual_buy` | `-57.543391` | `4.433498` | `0.446473` | `0.135182` |
| `001040` | CJ | `132200.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.270742` | `3.849175` | `0.792216` | `0.030028` |
| `005250` | 녹십자홀딩스 | `9540.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.641026` | `3.695652` | `0.950795` | `0.079249` |
| `000390` | SP삼화 | `5960.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-51.740891` | `3.114187` | `0.761175` | `0.073664` |
| `084670` | 동양고속 | `24350.0` |  |  | `market_risk_on` | `dual_buy` | `-70.662651` | `2.526316` | `0.435068` | `0.003732` |
| `019170` | 신풍제약 | `7870.0` |  |  | `market_risk_on` | `dual_buy` | `-42.132353` | `3.416557` | `0.864444` | `0.162563` |
| `034220` | LG디스플레이 | `9800.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-44.788732` | `-0.0` | `1.005327` | `-0.006279` |
| `489790` | 한화비전 | `42550.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-53.75` | `1.551313` | `0.539335` | `-0.014967` |
| `010660` | 화천기계 | `2705.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-58.952959` | `6.706114` | `0.419159` | `0.065147` |
| `003540` | 대신증권 | `25750.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.270988` | `3.830645` | `0.608141` | `0.087177` |
| `128820` | 대성산업 | `4120.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-68.645358` | `3.0` | `0.900511` | `0.049527` |
| `005070` | 코스모신소재 | `34900.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-47.439759` | `2.046784` | `0.976851` | `0.073989` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
