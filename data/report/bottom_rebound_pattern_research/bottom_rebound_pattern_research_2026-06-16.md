# Bottom Rebound Pattern Research - 2026-06-16

- generated_at: `2026-06-16T20:24:49`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57151`
- label_rows: `1428775`
- latest_as_of_candidate_count: `54`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.395766`
- backtest_trade_count: `291`
- backtest_total_return_pct: `22.856351`
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
| `signal_close_retest_entry` | `20` | `38732` | `0.677713` | `1.810457` | `1.810457` | `0.490344` | `-16.947774` | `17.2187` |
| `open_guarded_retest_entry` | `20` | `34169` | `0.597872` | `1.604229` | `1.604229` | `0.482309` | `-16.921841` | `16.582915` |
| `next_open_entry` | `20` | `55300` | `0.967612` | `2.021794` | `2.021794` | `0.485967` | `-16.74349` | `17.365749` |
| `close_zone_limit_entry` | `20` | `42259` | `0.739427` | `1.811998` | `1.811998` | `0.487304` | `-16.828879` | `17.01772` |
| `atr_pullback_entry` | `20` | `17958` | `0.31422` | `2.39827` | `2.39827` | `0.518321` | `-16.972438` | `17.96756` |
| `signal_close_retest_entry` | `10` | `39082` | `0.683838` | `1.003448` | `1.003448` | `0.497927` | `-12.373541` | `11.233893` |
| `open_guarded_retest_entry` | `10` | `34418` | `0.602229` | `0.791512` | `0.791512` | `0.487274` | `-12.231925` | `10.732381` |
| `next_open_entry` | `10` | `55761` | `0.975678` | `1.123258` | `1.123258` | `0.49696` | `-12.209302` | `11.347518` |
| `close_zone_limit_entry` | `10` | `42627` | `0.745866` | `1.00243` | `1.00243` | `0.495132` | `-12.266013` | `11.110655` |
| `atr_pullback_entry` | `10` | `18205` | `0.318542` | `1.395766` | `1.395766` | `0.526778` | `-12.898463` | `11.562317` |
| `signal_close_retest_entry` | `5` | `39607` | `0.693024` | `0.379551` | `0.379551` | `0.488373` | `-8.779563` | `7.189294` |
| `open_guarded_retest_entry` | `5` | `34761` | `0.608231` | `0.252251` | `0.252251` | `0.480107` | `-8.571104` | `6.72` |
| `next_open_entry` | `5` | `56415` | `0.987122` | `0.508375` | `0.508375` | `0.490845` | `-8.566761` | `7.414915` |
| `close_zone_limit_entry` | `5` | `43160` | `0.755192` | `0.396337` | `0.396337` | `0.488114` | `-8.627997` | `7.120296` |
| `atr_pullback_entry` | `5` | `18613` | `0.325681` | `0.401629` | `0.401629` | `0.499866` | `-9.539137` | `7.407407` |
| `signal_close_retest_entry` | `3` | `39838` | `0.697066` | `0.171695` | `0.171695` | `0.48652` | `-6.463343` | `5.226026` |
| `open_guarded_retest_entry` | `3` | `34855` | `0.609876` | `0.042932` | `0.042932` | `0.47448` | `-6.314383` | `4.773536` |
| `next_open_entry` | `3` | `56796` | `0.993788` | `0.252677` | `0.252677` | `0.479946` | `-6.431453` | `5.469954` |
| `close_zone_limit_entry` | `3` | `43401` | `0.759409` | `0.168689` | `0.168689` | `0.485334` | `-6.379747` | `5.177919` |
| `atr_pullback_entry` | `3` | `18779` | `0.328586` | `0.209894` | `0.209894` | `0.4955` | `-7.021808` | `5.43774` |
| `signal_close_retest_entry` | `1` | `39893` | `0.698028` | `-0.038505` | `-0.038505` | `0.473241` | `-3.256594` | `2.695095` |
| `open_guarded_retest_entry` | `1` | `34890` | `0.610488` | `-0.148209` | `-0.148209` | `0.45096` | `-3.160568` | `2.383024` |
| `next_open_entry` | `1` | `57097` | `0.999055` | `0.028402` | `0.028402` | `0.457012` | `-3.418025` | `2.774031` |
| `close_zone_limit_entry` | `1` | `43464` | `0.760512` | `-0.033253` | `-0.033253` | `0.472644` | `-3.23877` | `2.652378` |
| `atr_pullback_entry` | `1` | `18790` | `0.328778` | `-0.115376` | `-0.115376` | `0.468228` | `-3.27746` | `3.329204` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `22.856351`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.512027`
- skipped_capacity_count: `17298`
- skipped_same_symbol_count: `616`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-12.258184` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `22.856351` | `-23.08101` | `0.512027` |
| `exclude_market_risk_off` | `270` | `25.158725` | `-31.672118` | `0.496296` |
| `require_foreign_not_sell` | `289` | `5.643395` | `-29.784536` | `0.50173` |
| `exclude_risk_off_and_foreign_sell` | `270` | `31.314774` | `-28.311347` | `0.496296` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `014530` | 극동유화 | `3275.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.381762` | `2.184087` | `0.492049` | `-0.025889` |
| `128820` | 대성산업 | `5270.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-59.893455` | `6.25` | `0.485075` | `-0.012432` |
| `000390` | SP삼화 | `6620.0` |  |  | `market_neutral` | `foreign_buy_only` | `-46.396761` | `9.240924` | `0.403716` | `0.024582` |
| `117580` | 대성에너지 | `7120.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-55.913313` | `4.093567` | `0.447511` | `-0.047451` |
| `272550` | 삼양패키징 | `9270.0` |  |  | `market_neutral` | `foreign_buy_only` | `-47.149373` | `9.058824` | `0.579288` | `0.017122` |
| `128940` | 한미약품 | `425500.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-34.23493` | `7.044025` | `0.792256` | `-0.025694` |
| `465770` | STX그린로지스 | `2665.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-72.239583` | `6.6` | `0.977953` | `-0.021421` |
| `017860` | DS단석 | `14630.0` |  |  | `market_neutral` | `inst_buy_only` | `-44.688091` | `4.799427` | `0.55664` | `-0.02951` |
| `004360` | 세방 | `13570.0` |  |  | `market_neutral` | `foreign_buy_only` | `-18.742515` | `5.767732` | `0.767416` | `0.101002` |
| `105630` | 한세실업 | `9110.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-41.377091` | `9.363745` | `0.774999` | `-0.07077` |
| `003520` | 영진약품 | `1285.0` |  |  | `market_neutral` | `inst_buy_only` | `-41.723356` | `6.816293` | `0.60072` | `-0.097014` |
| `003350` | 한국화장품제조 | `8200.0` |  |  | `market_neutral` | `dual_buy` | `-84.200385` | `7.894737` | `0.41249` | `0.053246` |
| `009160` | SIMPAC | `4520.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-34.110787` | `4.62963` | `0.458969` | `-0.052265` |
| `001790` | 대한제당 | `2470.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-24.233129` | `5.106383` | `0.428527` | `-0.13364` |
| `001780` | 알루코 | `2030.0` |  |  | `market_neutral` | `inst_buy_only` | `-41.917024` | `7.407407` | `0.514092` | `-0.004777` |
| `000080` | 하이트진로 | `16010.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-16.134102` | `3.290323` | `0.695753` | `-0.028955` |
| `403550` | 쏘카 | `11450.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-44.68599` | `8.633776` | `0.70121` | `-0.015038` |
| `005870` | 휴니드 | `5800.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-44.656489` | `9.022556` | `1.477414` | `-0.016332` |
| `000520` | 삼일제약 | `7240.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-43.7014` | `9.365559` | `0.504498` | `-0.085526` |
| `251270` | 넷마블 | `41800.0` |  |  | `market_neutral` | `inst_buy_only` | `-27.806563` | `7.179487` | `0.765137` | `-0.103283` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
