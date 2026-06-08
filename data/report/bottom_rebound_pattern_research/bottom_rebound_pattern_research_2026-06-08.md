# Bottom Rebound Pattern Research - 2026-06-08

- generated_at: `2026-06-08T20:45:45`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56935`
- label_rows: `1423375`
- latest_as_of_candidate_count: `231`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.461108`
- backtest_trade_count: `291`
- backtest_total_return_pct: `20.607622`
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
| `signal_close_retest_entry` | `20` | `38781` | `0.681145` | `1.789787` | `1.789787` | `0.490807` | `-16.91202` | `17.238328` |
| `open_guarded_retest_entry` | `20` | `34201` | `0.600703` | `1.582317` | `1.582317` | `0.482822` | `-16.877621` | `16.603425` |
| `next_open_entry` | `20` | `55289` | `0.97109` | `2.003655` | `2.003655` | `0.486335` | `-16.680938` | `17.39342` |
| `close_zone_limit_entry` | `20` | `42308` | `0.743093` | `1.792931` | `1.792931` | `0.487709` | `-16.791993` | `17.035705` |
| `atr_pullback_entry` | `20` | `18015` | `0.316413` | `2.358886` | `2.358886` | `0.51829` | `-16.931234` | `18.013391` |
| `signal_close_retest_entry` | `10` | `39005` | `0.685079` | `1.050191` | `1.050191` | `0.4995` | `-12.23943` | `11.245948` |
| `open_guarded_retest_entry` | `10` | `34377` | `0.603794` | `0.819138` | `0.819138` | `0.48803` | `-12.113874` | `10.731124` |
| `next_open_entry` | `10` | `55656` | `0.977536` | `1.177479` | `1.177479` | `0.498634` | `-12.059836` | `11.36` |
| `close_zone_limit_entry` | `10` | `42545` | `0.747256` | `1.051036` | `1.051036` | `0.496674` | `-12.134565` | `11.111111` |
| `atr_pullback_entry` | `10` | `18149` | `0.318767` | `1.461108` | `1.461108` | `0.528789` | `-12.685919` | `11.566108` |
| `signal_close_retest_entry` | `5` | `39312` | `0.690472` | `0.384103` | `0.384103` | `0.488197` | `-8.622542` | `7.158308` |
| `open_guarded_retest_entry` | `5` | `34554` | `0.606903` | `0.256476` | `0.256476` | `0.480089` | `-8.437258` | `6.694581` |
| `next_open_entry` | `5` | `56110` | `0.98551` | `0.512899` | `0.512899` | `0.490679` | `-8.450704` | `7.383696` |
| `close_zone_limit_entry` | `5` | `42865` | `0.752876` | `0.401313` | `0.401313` | `0.487904` | `-8.491026` | `7.089088` |
| `atr_pullback_entry` | `5` | `18359` | `0.322455` | `0.412684` | `0.412684` | `0.500463` | `-9.28499` | `7.349597` |
| `signal_close_retest_entry` | `3` | `39571` | `0.695021` | `0.129629` | `0.129629` | `0.484496` | `-6.455354` | `5.145414` |
| `open_guarded_retest_entry` | `3` | `34756` | `0.610451` | `0.024462` | `0.024462` | `0.47353` | `-6.316545` | `4.749098` |
| `next_open_entry` | `3` | `56382` | `0.990287` | `0.217846` | `0.217846` | `0.477546` | `-6.408135` | `5.386162` |
| `close_zone_limit_entry` | `3` | `43125` | `0.757443` | `0.129293` | `0.129293` | `0.483409` | `-6.374478` | `5.115419` |
| `atr_pullback_entry` | `3` | `18596` | `0.326618` | `0.153118` | `0.153118` | `0.492579` | `-7.036821` | `5.345212` |
| `signal_close_retest_entry` | `1` | `39865` | `0.700184` | `-0.054483` | `-0.054483` | `0.471391` | `-3.281008` | `2.685306` |
| `open_guarded_retest_entry` | `1` | `34893` | `0.612857` | `-0.1616` | `-0.1616` | `0.449689` | `-3.182539` | `2.376431` |
| `next_open_entry` | `1` | `56704` | `0.995943` | `0.013804` | `0.013804` | `0.455506` | `-3.425775` | `2.750753` |
| `close_zone_limit_entry` | `1` | `43420` | `0.762624` | `-0.048287` | `-0.048287` | `0.47082` | `-3.255819` | `2.638919` |
| `atr_pullback_entry` | `1` | `18843` | `0.330956` | `-0.139249` | `-0.139249` | `0.46638` | `-3.317458` | `3.324151` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `20.607622`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.515464`
- skipped_capacity_count: `17243`
- skipped_same_symbol_count: `615`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-13.682964` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `20.607622` | `-23.08101` | `0.515464` |
| `exclude_market_risk_off` | `272` | `31.631125` | `-28.138642` | `0.507353` |
| `require_foreign_not_sell` | `291` | `24.580353` | `-23.08101` | `0.512027` |
| `exclude_risk_off_and_foreign_sell` | `272` | `33.800978` | `-26.954054` | `0.503676` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `001550` | 조비 | `10020.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.171838` | `1.932859` | `0.541295` | `0.017453` |
| `005870` | 휴니드 | `5450.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-47.996183` | `2.443609` | `0.611453` | `-0.004807` |
| `009240` | 한샘 | `28550.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.688363` | `0.883392` | `0.707469` | `0.03375` |
| `009070` | KCTC | `4200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.940405` | `0.598802` | `0.986256` | `0.029526` |
| `381970` | 케이카 | `8400.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-49.670461` | `1.083032` | `0.957079` | `-0.11963` |
| `117580` | 대성에너지 | `7090.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-56.099071` | `3.654971` | `0.767974` | `-0.012384` |
| `103140` | 풍산 | `67800.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-57.41206` | `2.108434` | `0.954734` | `0.058141` |
| `013360` | 일성건설 | `1179.0` |  |  | `market_risk_off` | `inst_buy_only` | `-56.892139` | `0.08489` | `0.621902` | `-0.014526` |
| `272550` | 삼양패키징 | `8540.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-51.311288` | `-0.0` | `0.651683` | `-0.014574` |
| `014530` | 극동유화 | `3280.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.304482` | `2.340094` | `0.778775` | `0.002557` |
| `000120` | CJ대한통운 | `77600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.964539` | `1.83727` | `1.568704` | `0.01182` |
| `214390` | 경보제약 | `5080.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.376344` | `0.594059` | `0.677133` | `0.001283` |
| `009580` | 무림P&P | `1735.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.746606` | `1.166181` | `0.610544` | `0.010011` |
| `361610` | SK아이이테크놀로지 | `16600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-44.57429` | `2.091021` | `0.73172` | `0.005468` |
| `950210` | 프레스티지바이오파마 | `6160.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-56.373938` | `0.325733` | `1.364434` | `-0.001813` |
| `112610` | 씨에스윈드 | `40900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.488665` | `4.871795` | `0.493227` | `0.048708` |
| `004090` | 한국석유 | `11840.0` |  |  | `market_risk_off` | `inst_buy_only` | `-64.735666` | `1.630901` | `1.224398` | `-0.022456` |
| `004140` | 동방 | `1860.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-42.325581` | `0.540541` | `0.608732` | `-0.019033` |
| `004310` | 현대약품 | `5510.0` |  |  | `market_risk_off` | `inst_buy_only` | `-63.75` | `1.473297` | `0.727244` | `-0.041759` |
| `002140` | 고려산업 | `1892.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-43.012048` | `0.584795` | `0.515927` | `-0.043176` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
