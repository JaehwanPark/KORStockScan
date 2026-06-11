# Bottom Rebound Pattern Research - 2026-06-11

- generated_at: `2026-06-11T20:24:10`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `55932`
- label_rows: `1398300`
- latest_as_of_candidate_count: `141`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.478961`
- backtest_trade_count: `283`
- backtest_total_return_pct: `42.045864`
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
| `signal_close_retest_entry` | `20` | `38170` | `0.682436` | `1.983471` | `1.983471` | `0.491433` | `-16.922031` | `17.22018` |
| `open_guarded_retest_entry` | `20` | `33679` | `0.602142` | `1.767196` | `1.767196` | `0.483655` | `-16.86548` | `16.547606` |
| `next_open_entry` | `20` | `54202` | `0.96907` | `2.242263` | `2.242263` | `0.485941` | `-16.711382` | `17.397844` |
| `close_zone_limit_entry` | `20` | `41677` | `0.745137` | `1.989645` | `1.989645` | `0.488111` | `-16.803479` | `17.01772` |
| `atr_pullback_entry` | `20` | `17638` | `0.315347` | `2.699026` | `2.699026` | `0.521488` | `-16.899991` | `18.012284` |
| `signal_close_retest_entry` | `10` | `38456` | `0.687549` | `1.048862` | `1.048862` | `0.498232` | `-12.299487` | `11.199095` |
| `open_guarded_retest_entry` | `10` | `33909` | `0.606254` | `0.809495` | `0.809495` | `0.486655` | `-12.199629` | `10.685335` |
| `next_open_entry` | `10` | `54604` | `0.976257` | `1.224647` | `1.224647` | `0.498114` | `-12.091452` | `11.331869` |
| `close_zone_limit_entry` | `10` | `41974` | `0.750447` | `1.058104` | `1.058104` | `0.495473` | `-12.196289` | `11.085957` |
| `atr_pullback_entry` | `10` | `17815` | `0.318512` | `1.478961` | `1.478961` | `0.527084` | `-12.774134` | `11.525646` |
| `signal_close_retest_entry` | `5` | `38846` | `0.694522` | `0.365543` | `0.365543` | `0.486408` | `-8.723541` | `7.109005` |
| `open_guarded_retest_entry` | `5` | `34204` | `0.611528` | `0.217999` | `0.217999` | `0.477079` | `-8.589976` | `6.654338` |
| `next_open_entry` | `5` | `55130` | `0.985661` | `0.525452` | `0.525452` | `0.490404` | `-8.493652` | `7.344764` |
| `close_zone_limit_entry` | `5` | `42370` | `0.757527` | `0.389753` | `0.389753` | `0.486665` | `-8.568529` | `7.05272` |
| `atr_pullback_entry` | `5` | `18155` | `0.324591` | `0.366943` | `0.366943` | `0.494905` | `-9.46026` | `7.257466` |
| `signal_close_retest_entry` | `3` | `39149` | `0.699939` | `0.135862` | `0.135862` | `0.483461` | `-6.47774` | `5.121133` |
| `open_guarded_retest_entry` | `3` | `34407` | `0.615158` | `0.019332` | `0.019332` | `0.471881` | `-6.350587` | `4.726495` |
| `next_open_entry` | `3` | `55453` | `0.991436` | `0.238486` | `0.238486` | `0.477467` | `-6.414295` | `5.344518` |
| `close_zone_limit_entry` | `3` | `42674` | `0.762962` | `0.136381` | `0.136381` | `0.483058` | `-6.385824` | `5.090551` |
| `atr_pullback_entry` | `3` | `18397` | `0.328917` | `0.16201` | `0.16201` | `0.488884` | `-7.061972` | `5.30685` |
| `signal_close_retest_entry` | `1` | `39464` | `0.705571` | `-0.019883` | `-0.019883` | `0.474382` | `-3.273333` | `2.690022` |
| `open_guarded_retest_entry` | `1` | `34517` | `0.617124` | `-0.148347` | `-0.148347` | `0.449923` | `-3.178347` | `2.370589` |
| `next_open_entry` | `1` | `55791` | `0.997479` | `0.038757` | `0.038757` | `0.458192` | `-3.425775` | `2.752294` |
| `close_zone_limit_entry` | `1` | `42993` | `0.768666` | `-0.015797` | `-0.015797` | `0.473472` | `-3.254446` | `2.641731` |
| `atr_pullback_entry` | `1` | `18656` | `0.333548` | `-0.062687` | `-0.062687` | `0.474271` | `-3.264334` | `3.364796` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `283`
- total_return_pct: `42.045864`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.519435`
- skipped_capacity_count: `16929`
- skipped_same_symbol_count: `603`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `1.608882` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `283` | `42.045864` | `-23.08101` | `0.519435` |
| `exclude_market_risk_off` | `262` | `64.458657` | `-24.651169` | `0.507634` |
| `require_foreign_not_sell` | `283` | `35.289528` | `-23.08101` | `0.519435` |
| `exclude_risk_off_and_foreign_sell` | `262` | `76.590666` | `-23.78546` | `0.515267` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `007110` | 일신석재 | `1028.0` |  |  | `market_neutral` | `foreign_buy_only` | `-47.200822` | `3.316583` | `0.576268` | `0.061868` |
| `003520` | 영진약품 | `1241.0` |  |  | `market_neutral` | `foreign_buy_only` | `-43.718821` | `2.731788` | `0.734742` | `0.028236` |
| `006890` | 태경케미컬 | `6380.0` |  |  | `market_neutral` | `dual_buy` | `-40.595903` | `1.269841` | `0.473807` | `0.026176` |
| `103140` | 풍산 | `69900.0` |  |  | `market_neutral` | `foreign_buy_only` | `-45.176471` | `4.172876` | `1.162467` | `0.186528` |
| `249420` | 일동제약 | `18570.0` |  |  | `market_neutral` | `foreign_buy_only` | `-58.779134` | `4.974562` | `0.521344` | `0.143189` |
| `005870` | 휴니드 | `5580.0` |  |  | `market_neutral` | `foreign_buy_only` | `-52.911392` | `2.95203` | `0.695472` | `0.001344` |
| `272550` | 삼양패키징 | `8890.0` |  |  | `market_neutral` | `foreign_buy_only` | `-48.313953` | `4.834906` | `0.508114` | `0.026021` |
| `271940` | 일진하이솔루스 | `12300.0` |  |  | `market_neutral` | `foreign_buy_only` | `-36.499742` | `0.819672` | `0.816297` | `0.132239` |
| `001360` | 삼성제약 | `1340.0` |  |  | `market_neutral` | `dual_buy` | `-42.241379` | `3.395062` | `0.429546` | `0.007321` |
| `112610` | 씨에스윈드 | `40550.0` |  |  | `market_neutral` | `foreign_buy_only` | `-48.012821` | `4.241645` | `2.053263` | `0.114012` |
| `007570` | 일양약품 | `8200.0` |  |  | `market_neutral` | `foreign_buy_only` | `-43.835616` | `5.398458` | `0.404419` | `0.034579` |
| `009070` | KCTC | `4245.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.404052` | `3.284672` | `0.527913` | `-0.012146` |
| `381970` | 케이카 | `8520.0` |  |  | `market_neutral` | `foreign_buy_only` | `-49.793754` | `3.1477` | `0.658323` | `0.015199` |
| `071970` | HD현대마린엔진 | `62300.0` |  |  | `market_neutral` | `foreign_buy_only` | `-46.200345` | `4.006678` | `0.608992` | `0.039445` |
| `071090` | 하이스틸 | `3010.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-47.007042` | `1.861252` | `0.402975` | `-0.002206` |
| `000520` | 삼일제약 | `7090.0` |  |  | `market_neutral` | `foreign_buy_only` | `-44.867807` | `6.137725` | `0.428829` | `0.004784` |
| `006660` | 삼성공조 | `11230.0` |  |  | `market_neutral` | `dual_buy` | `-40.894737` | `3.789279` | `1.410073` | `0.009464` |
| `000120` | CJ대한통운 | `79800.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-43.404255` | `2.046036` | `1.065021` | `-0.055762` |
| `105630` | 한세실업 | `8490.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-45.366795` | `2.166065` | `0.633939` | `-0.117342` |
| `015860` | 일진홀딩스 | `6720.0` |  |  | `market_neutral` | `foreign_buy_only` | `-54.254595` | `3.543914` | `0.415496` | `0.042215` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
