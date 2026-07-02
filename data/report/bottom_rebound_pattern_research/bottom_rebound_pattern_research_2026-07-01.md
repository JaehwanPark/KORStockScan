# Bottom Rebound Pattern Research - 2026-07-01

- generated_at: `2026-07-01T23:29:46`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57455`
- label_rows: `1436375`
- latest_as_of_candidate_count: `122`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.306192`
- backtest_trade_count: `289`
- backtest_total_return_pct: `183.538536`
- backtest_max_drawdown_pct: `-23.533127`
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
| `signal_close_retest_entry` | `20` | `38590` | `0.671656` | `1.863105` | `1.863105` | `0.488961` | `-17.098948` | `17.197106` |
| `open_guarded_retest_entry` | `20` | `34002` | `0.591802` | `1.593303` | `1.593303` | `0.481148` | `-17.051488` | `16.526946` |
| `next_open_entry` | `20` | `54975` | `0.956836` | `2.112275` | `2.112275` | `0.48422` | `-16.909104` | `17.405948` |
| `close_zone_limit_entry` | `20` | `42118` | `0.733061` | `1.848869` | `1.848869` | `0.485707` | `-16.964286` | `17.013163` |
| `atr_pullback_entry` | `20` | `17904` | `0.311618` | `2.527338` | `2.527338` | `0.518767` | `-17.139524` | `17.986208` |
| `signal_close_retest_entry` | `10` | `39402` | `0.685789` | `0.921869` | `0.921869` | `0.492843` | `-12.758921` | `11.236999` |
| `open_guarded_retest_entry` | `10` | `34586` | `0.601967` | `0.676119` | `0.676119` | `0.482247` | `-12.537128` | `10.717137` |
| `next_open_entry` | `10` | `55974` | `0.974223` | `1.074516` | `1.074516` | `0.492836` | `-12.542373` | `11.363636` |
| `close_zone_limit_entry` | `10` | `42941` | `0.747385` | `0.929725` | `0.929725` | `0.490557` | `-12.604043` | `11.111111` |
| `atr_pullback_entry` | `10` | `18572` | `0.323244` | `1.306192` | `1.306192` | `0.517876` | `-13.457051` | `11.586336` |
| `signal_close_retest_entry` | `5` | `39833` | `0.69329` | `0.376413` | `0.376413` | `0.487284` | `-8.850874` | `7.29229` |
| `open_guarded_retest_entry` | `5` | `34792` | `0.605552` | `0.215689` | `0.215689` | `0.477581` | `-8.686289` | `6.750123` |
| `next_open_entry` | `5` | `56589` | `0.984927` | `0.492168` | `0.492168` | `0.489159` | `-8.709209` | `7.495338` |
| `close_zone_limit_entry` | `5` | `43382` | `0.75506` | `0.397935` | `0.397935` | `0.487414` | `-8.706621` | `7.226695` |
| `atr_pullback_entry` | `5` | `18911` | `0.329145` | `0.425336` | `0.425336` | `0.499498` | `-9.603438` | `7.604193` |
| `signal_close_retest_entry` | `3` | `40141` | `0.698651` | `0.20612` | `0.20612` | `0.486834` | `-6.6103` | `5.25601` |
| `open_guarded_retest_entry` | `3` | `34995` | `0.609085` | `0.043163` | `0.043163` | `0.473753` | `-6.459117` | `4.78401` |
| `next_open_entry` | `3` | `56990` | `0.991907` | `0.257016` | `0.257016` | `0.478277` | `-6.586188` | `5.463086` |
| `close_zone_limit_entry` | `3` | `43699` | `0.760578` | `0.201685` | `0.201685` | `0.48619` | `-6.521739` | `5.202049` |
| `atr_pullback_entry` | `3` | `19134` | `0.333026` | `0.304432` | `0.304432` | `0.495923` | `-7.238837` | `5.532813` |
| `signal_close_retest_entry` | `1` | `40448` | `0.703994` | `0.002809` | `0.002809` | `0.474881` | `-3.321258` | `2.741756` |
| `open_guarded_retest_entry` | `1` | `35117` | `0.611209` | `-0.148082` | `-0.148082` | `0.45001` | `-3.205347` | `2.398786` |
| `next_open_entry` | `1` | `57333` | `0.997877` | `0.053827` | `0.053827` | `0.458584` | `-3.466575` | `2.803775` |
| `close_zone_limit_entry` | `1` | `44010` | `0.765991` | `0.005099` | `0.005099` | `0.473938` | `-3.30093` | `2.693191` |
| `atr_pullback_entry` | `1` | `19350` | `0.336785` | `-0.016627` | `-0.016627` | `0.476537` | `-3.353117` | `3.448824` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `289`
- total_return_pct: `183.538536`
- max_drawdown_pct: `-23.533127`
- diagnostic_win_rate: `0.508651`
- skipped_capacity_count: `17655`
- skipped_same_symbol_count: `628`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `102.364032` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `289` | `183.538536` | `-23.533127` | `0.508651` |
| `exclude_market_risk_off` | `270` | `18.092231` | `-35.529928` | `0.488889` |
| `require_foreign_not_sell` | `289` | `176.804954` | `-23.08101` | `0.50519` |
| `exclude_risk_off_and_foreign_sell` | `270` | `21.536345` | `-33.649683` | `0.492593` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `011170` | 롯데케미칼 | `64400.0` |  |  | `market_neutral` | `foreign_buy_only` | `-45.836838` | `3.04` | `0.751091` | `0.007312` |
| `084670` | 동양고속 | `29900.0` |  |  | `market_neutral` | `dual_buy` | `-70.914397` | `0.673401` | `0.445814` | `0.004764` |
| `249420` | 일동제약 | `16840.0` |  |  | `market_neutral` | `foreign_buy_only` | `-62.536151` | `7.192871` | `0.453153` | `0.269615` |
| `004310` | 현대약품 | `5600.0` |  |  | `market_neutral` | `dual_buy` | `-63.157895` | `4.089219` | `2.151261` | `0.003734` |
| `018470` | 조일알미늄 | `1004.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.0783` | `5.684211` | `0.434926` | `0.019936` |
| `010660` | 화천기계 | `2810.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-57.359636` | `5.440901` | `0.43356` | `-0.003648` |
| `007570` | 일양약품 | `7900.0` |  |  | `market_neutral` | `foreign_buy_only` | `-45.890411` | `7.923497` | `1.200806` | `0.134143` |
| `950210` | 프레스티지바이오파마 | `6410.0` |  |  | `market_neutral` | `dual_buy` | `-54.603399` | `8.460237` | `0.544218` | `0.112085` |
| `103140` | 풍산 | `66100.0` |  |  | `market_neutral` | `foreign_buy_only` | `-58.479899` | `7.305195` | `0.778351` | `0.168395` |
| `008350` | 남선알미늄 | `1059.0` |  |  | `market_neutral` | `dual_buy` | `-69.612626` | `6.006006` | `0.437388` | `0.051277` |
| `128820` | 대성산업 | `4440.0` |  |  | `market_neutral` | `foreign_buy_only` | `-66.210046` | `6.987952` | `0.45234` | `0.014809` |
| `000100` | 유한양행 | `70500.0` |  |  | `market_neutral` | `foreign_buy_only` | `-39.948893` | `6.015038` | `0.722692` | `0.043355` |
| `084680` | 이월드 | `1060.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.52381` | `3.7182` | `0.423588` | `-0.025082` |
| `450080` | 에코프로머티 | `41900.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-52.494331` | `2.070646` | `1.294585` | `-0.050878` |
| `024110` | 기업은행 | `20250.0` |  |  | `market_neutral` | `foreign_buy_only` | `-24.440299` | `4.327666` | `0.534699` | `0.09046` |
| `092200` | 디아이씨 | `4920.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-67.156208` | `1.652893` | `0.496425` | `-0.044216` |
| `006280` | 녹십자 | `124000.0` |  |  | `market_neutral` | `foreign_buy_only` | `-30.571109` | `4.995766` | `0.87886` | `0.037584` |
| `036460` | 한국가스공사 | `32550.0` |  |  | `market_neutral` | `dual_buy` | `-26.936027` | `3.006329` | `0.641204` | `0.091099` |
| `009270` | 신원 | `1001.0` |  |  | `market_neutral` | `foreign_buy_only` | `-39.222829` | `3.409091` | `0.634074` | `0.011006` |
| `000120` | CJ대한통운 | `75300.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-46.595745` | `5.020921` | `0.577658` | `-0.084267` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
