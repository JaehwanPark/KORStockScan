# Bottom Rebound Pattern Research - 2026-06-04

- generated_at: `2026-06-04T21:35:15`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56917`
- label_rows: `1422925`
- latest_as_of_candidate_count: `152`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.539833`
- backtest_trade_count: `291`
- backtest_total_return_pct: `53.818566`
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
| `signal_close_retest_entry` | `20` | `38897` | `0.683399` | `1.786132` | `1.786132` | `0.490681` | `-16.904179` | `17.259184` |
| `open_guarded_retest_entry` | `20` | `34316` | `0.602913` | `1.576691` | `1.576691` | `0.482632` | `-16.884904` | `16.610139` |
| `next_open_entry` | `20` | `55387` | `0.973119` | `1.998076` | `1.998076` | `0.486883` | `-16.640201` | `17.404443` |
| `close_zone_limit_entry` | `20` | `42424` | `0.745366` | `1.781712` | `1.781712` | `0.487743` | `-16.78348` | `17.047619` |
| `atr_pullback_entry` | `20` | `18091` | `0.317849` | `2.365778` | `2.365778` | `0.517771` | `-16.912114` | `18.051371` |
| `signal_close_retest_entry` | `10` | `39082` | `0.686649` | `1.106498` | `1.106498` | `0.500716` | `-12.214486` | `11.239073` |
| `open_guarded_retest_entry` | `10` | `34462` | `0.605478` | `0.863557` | `0.863557` | `0.488915` | `-12.124345` | `10.726644` |
| `next_open_entry` | `10` | `55793` | `0.980252` | `1.24363` | `1.24363` | `0.499973` | `-12.008992` | `11.366866` |
| `close_zone_limit_entry` | `10` | `42622` | `0.748845` | `1.103571` | `1.103571` | `0.497795` | `-12.111922` | `11.111111` |
| `atr_pullback_entry` | `10` | `18192` | `0.319623` | `1.539833` | `1.539833` | `0.530563` | `-12.6338` | `11.562811` |
| `signal_close_retest_entry` | `5` | `39409` | `0.692394` | `0.402672` | `0.402672` | `0.488898` | `-8.621512` | `7.156563` |
| `open_guarded_retest_entry` | `5` | `34673` | `0.609185` | `0.262614` | `0.262614` | `0.480287` | `-8.466017` | `6.691091` |
| `next_open_entry` | `5` | `56192` | `0.987262` | `0.558955` | `0.558955` | `0.492205` | `-8.380578` | `7.394366` |
| `close_zone_limit_entry` | `5` | `42957` | `0.754731` | `0.419919` | `0.419919` | `0.488558` | `-8.484686` | `7.086462` |
| `atr_pullback_entry` | `5` | `18435` | `0.323893` | `0.444482` | `0.444482` | `0.501437` | `-9.301498` | `7.346855` |
| `signal_close_retest_entry` | `3` | `39562` | `0.695082` | `0.152511` | `0.152511` | `0.485213` | `-6.400634` | `5.142857` |
| `open_guarded_retest_entry` | `3` | `34773` | `0.610942` | `0.038366` | `0.038366` | `0.47373` | `-6.290062` | `4.743681` |
| `next_open_entry` | `3` | `56427` | `0.991391` | `0.24651` | `0.24651` | `0.478335` | `-6.367041` | `5.384542` |
| `close_zone_limit_entry` | `3` | `43116` | `0.757524` | `0.150179` | `0.150179` | `0.48402` | `-6.336654` | `5.114923` |
| `atr_pullback_entry` | `3` | `18555` | `0.326001` | `0.201225` | `0.201225` | `0.494314` | `-6.929009` | `5.345118` |
| `signal_close_retest_entry` | `1` | `39860` | `0.700318` | `-0.053012` | `-0.053012` | `0.47155` | `-3.267045` | `2.679462` |
| `open_guarded_retest_entry` | `1` | `34973` | `0.614456` | `-0.162536` | `-0.162536` | `0.449318` | `-3.174409` | `2.373321` |
| `next_open_entry` | `1` | `56765` | `0.997329` | `0.014767` | `0.014767` | `0.455369` | `-3.418591` | `2.743142` |
| `close_zone_limit_entry` | `1` | `43416` | `0.762795` | `-0.047277` | `-0.047277` | `0.470909` | `-3.24826` | `2.631019` |
| `atr_pullback_entry` | `1` | `18792` | `0.330165` | `-0.135422` | `-0.135422` | `0.46738` | `-3.300543` | `3.317591` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `53.818566`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.522337`
- skipped_capacity_count: `17281`
- skipped_same_symbol_count: `620`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `9.995893` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `53.818566` | `-23.08101` | `0.522337` |
| `exclude_market_risk_off` | `275` | `36.28737` | `-25.596658` | `0.494545` |
| `require_foreign_not_sell` | `291` | `35.026771` | `-23.08101` | `0.522337` |
| `exclude_risk_off_and_foreign_sell` | `275` | `51.887699` | `-23.78546` | `0.501818` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `009070` | KCTC | `4560.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.649583` | `-0.0` | `0.84574` | `0.031822` |
| `000120` | CJ대한통운 | `82600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.41844` | `0.36452` | `0.645352` | `0.00711` |
| `249420` | 일동제약 | `20200.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-54.03868` | `2.382159` | `0.814869` | `-0.066248` |
| `009580` | 무림P&P | `1843.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-58.303167` | `0.108637` | `0.508132` | `0.009844` |
| `029780` | 삼성카드 | `46050.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-31.777778` | `1.208791` | `1.088603` | `0.055797` |
| `007570` | 일양약품 | `8250.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.199507` | `1.226994` | `0.67622` | `-0.136333` |
| `000390` | SP삼화 | `6670.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.991903` | `2.300613` | `0.525808` | `0.003883` |
| `105630` | 한세실업 | `8480.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.431145` | `0.236407` | `0.854901` | `-0.036917` |
| `192650` | 드림텍 | `4770.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.010753` | `0.632911` | `0.733528` | `-0.019274` |
| `004090` | 한국석유 | `12300.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-63.365599` | `1.317957` | `0.490254` | `-0.010533` |
| `009240` | 한샘 | `30650.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-41.619048` | `3.722504` | `0.826543` | `0.044097` |
| `026890` | 스틱인베스트먼트 | `7070.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.948012` | `0.141643` | `1.481932` | `0.02831` |
| `007110` | 일신석재 | `1075.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.786852` | `0.279851` | `0.419932` | `-0.048309` |
| `011700` | 한신기계 | `2965.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.57483` | `1.022147` | `0.441498` | `-0.015094` |
| `037270` | YG PLUS | `3760.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-50.591327` | `1.759134` | `0.875491` | `-0.070305` |
| `002140` | 고려산업 | `1995.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-39.909639` | `0.402617` | `0.533021` | `-0.037036` |
| `004310` | 현대약품 | `6000.0` |  |  | `market_risk_off` | `inst_buy_only` | `-60.526316` | `2.214651` | `1.005234` | `-0.041397` |
| `007860` | 서연 | `8420.0` |  |  | `market_risk_off` | `dual_buy` | `-28.885135` | `1.690821` | `0.636938` | `0.061813` |
| `079980` | 휴비스 | `2005.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-50.737101` | `-0.0` | `0.498588` | `-0.025372` |
| `006880` | 신송홀딩스 | `5340.0` |  |  | `market_risk_off` | `dual_buy` | `-32.998745` | `2.10325` | `0.960375` | `0.021262` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
