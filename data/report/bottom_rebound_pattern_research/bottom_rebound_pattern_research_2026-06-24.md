# Bottom Rebound Pattern Research - 2026-06-24

- generated_at: `2026-06-24T23:30:12`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57398`
- label_rows: `1434950`
- latest_as_of_candidate_count: `228`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.299496`
- backtest_trade_count: `291`
- backtest_total_return_pct: `8.038959`
- backtest_max_drawdown_pct: `-28.192334`
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
| `signal_close_retest_entry` | `20` | `38670` | `0.673717` | `1.802606` | `1.802606` | `0.489966` | `-17.00643` | `17.219353` |
| `open_guarded_retest_entry` | `20` | `34104` | `0.594167` | `1.589021` | `1.589021` | `0.482026` | `-16.976185` | `16.582915` |
| `next_open_entry` | `20` | `55146` | `0.960765` | `2.016562` | `2.016562` | `0.485421` | `-16.817624` | `17.414248` |
| `close_zone_limit_entry` | `20` | `42194` | `0.735113` | `1.794487` | `1.794487` | `0.486918` | `-16.879842` | `17.01772` |
| `atr_pullback_entry` | `20` | `17934` | `0.31245` | `2.410195` | `2.410195` | `0.518624` | `-17.055557` | `17.991828` |
| `signal_close_retest_entry` | `10` | `39188` | `0.682742` | `0.949775` | `0.949775` | `0.495713` | `-12.526084` | `11.235129` |
| `open_guarded_retest_entry` | `10` | `34454` | `0.600265` | `0.75367` | `0.75367` | `0.485459` | `-12.344743` | `10.723107` |
| `next_open_entry` | `10` | `55827` | `0.97263` | `1.061811` | `1.061811` | `0.494528` | `-12.407462` | `11.353597` |
| `close_zone_limit_entry` | `10` | `42730` | `0.744451` | `0.952586` | `0.952586` | `0.493003` | `-12.417264` | `11.110476` |
| `atr_pullback_entry` | `10` | `18324` | `0.319245` | `1.299496` | `1.299496` | `0.521993` | `-13.08723` | `11.559078` |
| `signal_close_retest_entry` | `5` | `39726` | `0.692115` | `0.39932` | `0.39932` | `0.488396` | `-8.762708` | `7.271049` |
| `open_guarded_retest_entry` | `5` | `34749` | `0.605404` | `0.250358` | `0.250358` | `0.479237` | `-8.565383` | `6.74155` |
| `next_open_entry` | `5` | `56714` | `0.988083` | `0.500111` | `0.500111` | `0.489473` | `-8.625731` | `7.508874` |
| `close_zone_limit_entry` | `5` | `43283` | `0.754086` | `0.4141` | `0.4141` | `0.488275` | `-8.623423` | `7.198626` |
| `atr_pullback_entry` | `5` | `18719` | `0.326126` | `0.446775` | `0.446775` | `0.501362` | `-9.473327` | `7.510221` |
| `signal_close_retest_entry` | `3` | `39806` | `0.693508` | `0.154908` | `0.154908` | `0.485379` | `-6.489759` | `5.213568` |
| `open_guarded_retest_entry` | `3` | `34815` | `0.606554` | `0.025946` | `0.025946` | `0.473216` | `-6.337105` | `4.767379` |
| `next_open_entry` | `3` | `56877` | `0.990923` | `0.238006` | `0.238006` | `0.478875` | `-6.453976` | `5.47619` |
| `close_zone_limit_entry` | `3` | `43369` | `0.755584` | `0.15207` | `0.15207` | `0.484378` | `-6.410256` | `5.165505` |
| `atr_pullback_entry` | `3` | `18767` | `0.326963` | `0.189894` | `0.189894` | `0.494165` | `-7.055124` | `5.421623` |
| `signal_close_retest_entry` | `1` | `40093` | `0.698509` | `-0.040113` | `-0.040113` | `0.472427` | `-3.267746` | `2.70431` |
| `open_guarded_retest_entry` | `1` | `34942` | `0.608767` | `-0.154981` | `-0.154981` | `0.449202` | `-3.168735` | `2.379115` |
| `next_open_entry` | `1` | `57170` | `0.996028` | `0.024937` | `0.024937` | `0.456166` | `-3.424658` | `2.777778` |
| `close_zone_limit_entry` | `1` | `43657` | `0.760601` | `-0.034833` | `-0.034833` | `0.47186` | `-3.249097` | `2.659814` |
| `atr_pullback_entry` | `1` | `19046` | `0.331823` | `-0.107162` | `-0.107162` | `0.468865` | `-3.271889` | `3.347924` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `8.038959`
- max_drawdown_pct: `-28.192334`
- diagnostic_win_rate: `0.508591`
- skipped_capacity_count: `17410`
- skipped_same_symbol_count: `623`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-22.401495` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `8.038959` | `-28.192334` | `0.508591` |
| `exclude_market_risk_off` | `275` | `5.829127` | `-42.224722` | `0.494545` |
| `require_foreign_not_sell` | `291` | `15.463473` | `-23.25766` | `0.512027` |
| `exclude_risk_off_and_foreign_sell` | `275` | `3.863276` | `-43.297939` | `0.490909` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `000390` | SP삼화 | `5990.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.497976` | `1.525424` | `0.658223` | `0.075893` |
| `016610` | DB증권 | `9240.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.236572` | `1.986755` | `0.9832` | `0.024531` |
| `010780` | 아이에스동서 | `21050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.269795` | `2.184466` | `0.598863` | `0.127307` |
| `100840` | SNT에너지 | `28850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.08828` | `1.763668` | `0.725989` | `0.005375` |
| `004990` | 롯데지주 | `23950.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-36.472149` | `2.7897` | `0.768052` | `0.131411` |
| `002790` | 아모레퍼시픽홀딩스 | `21000.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-40.594059` | `2.189781` | `0.728338` | `-0.0075` |
| `011500` | 한농화성 | `14350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.473968` | `3.015075` | `0.785765` | `0.060362` |
| `105630` | 한세실업 | `8190.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.297297` | `0.614251` | `0.559646` | `-0.117978` |
| `000120` | CJ대한통운 | `74600.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.092199` | `3.038674` | `0.907811` | `-0.011442` |
| `001430` | 세아베스틸지주 | `34450.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.756757` | `2.835821` | `0.980077` | `0.035341` |
| `024110` | 기업은행 | `20150.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-24.813433` | `1.664985` | `1.303199` | `0.038597` |
| `352820` | 하이브 | `193900.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-51.645885` | `1.945321` | `1.128435` | `-0.021211` |
| `035720` | 카카오 | `34000.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.708464` | `1.492537` | `0.880254` | `-0.116931` |
| `002350` | 넥센타이어 | `6420.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-36.498516` | `2.72` | `0.904948` | `0.031743` |
| `005870` | 휴니드 | `4660.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.534351` | `2.75634` | `0.552505` | `0.005232` |
| `017800` | 현대엘리베이터 | `72000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-35.714286` | `2.710414` | `0.686237` | `0.147716` |
| `084680` | 이월드 | `1062.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.766917` | `1.919386` | `0.9456` | `-0.026847` |
| `092200` | 디아이씨 | `5580.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-62.750334` | `2.762431` | `0.418431` | `-0.019679` |
| `014280` | 금강공업 | `3890.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-48.339973` | `2.368421` | `0.569423` | `-0.003051` |
| `003540` | 대신증권 | `27150.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-42.29543` | `5.436893` | `0.611413` | `0.171885` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
