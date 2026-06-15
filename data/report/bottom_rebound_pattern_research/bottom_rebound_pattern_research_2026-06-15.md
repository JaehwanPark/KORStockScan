# Bottom Rebound Pattern Research - 2026-06-15

- generated_at: `2026-06-15T20:24:30`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56133`
- label_rows: `1403325`
- latest_as_of_candidate_count: `65`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.440253`
- backtest_trade_count: `283`
- backtest_total_return_pct: `21.276422`
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
| `signal_close_retest_entry` | `20` | `38280` | `0.681952` | `1.876318` | `1.876318` | `0.490726` | `-16.967282` | `17.195866` |
| `open_guarded_retest_entry` | `20` | `33759` | `0.601411` | `1.657181` | `1.657181` | `0.482538` | `-16.929801` | `16.538706` |
| `next_open_entry` | `20` | `54469` | `0.970356` | `2.160347` | `2.160347` | `0.485781` | `-16.775552` | `17.422954` |
| `close_zone_limit_entry` | `20` | `41788` | `0.744446` | `1.889512` | `1.889512` | `0.487317` | `-16.853649` | `17.004066` |
| `atr_pullback_entry` | `20` | `17719` | `0.315661` | `2.535006` | `2.535006` | `0.520063` | `-16.992558` | `17.97104` |
| `signal_close_retest_entry` | `10` | `38621` | `0.688027` | `1.014783` | `1.014783` | `0.497812` | `-12.392427` | `11.188811` |
| `open_guarded_retest_entry` | `10` | `34024` | `0.606132` | `0.785397` | `0.785397` | `0.486274` | `-12.265077` | `10.678693` |
| `next_open_entry` | `10` | `54892` | `0.977892` | `1.181817` | `1.181817` | `0.498196` | `-12.201149` | `11.347387` |
| `close_zone_limit_entry` | `10` | `42139` | `0.750699` | `1.015573` | `1.015573` | `0.4951` | `-12.264323` | `11.08276` |
| `atr_pullback_entry` | `10` | `17958` | `0.319919` | `1.440253` | `1.440253` | `0.526729` | `-12.902523` | `11.517559` |
| `signal_close_retest_entry` | `5` | `39041` | `0.695509` | `0.368887` | `0.368887` | `0.486822` | `-8.75576` | `7.131966` |
| `open_guarded_retest_entry` | `5` | `34327` | `0.61153` | `0.221653` | `0.221653` | `0.477671` | `-8.597132` | `6.666667` |
| `next_open_entry` | `5` | `55431` | `0.987494` | `0.531729` | `0.531729` | `0.490448` | `-8.538012` | `7.380074` |
| `close_zone_limit_entry` | `5` | `42566` | `0.758306` | `0.39302` | `0.39302` | `0.487032` | `-8.603426` | `7.070707` |
| `atr_pullback_entry` | `5` | `18322` | `0.326403` | `0.370554` | `0.370554` | `0.49607` | `-9.520273` | `7.298378` |
| `signal_close_retest_entry` | `3` | `39353` | `0.701067` | `0.177865` | `0.177865` | `0.484995` | `-6.473407` | `5.177048` |
| `open_guarded_retest_entry` | `3` | `34457` | `0.613846` | `0.026353` | `0.026353` | `0.472038` | `-6.343951` | `4.735132` |
| `next_open_entry` | `3` | `55755` | `0.993266` | `0.267562` | `0.267562` | `0.478558` | `-6.427221` | `5.409224` |
| `close_zone_limit_entry` | `3` | `42878` | `0.763864` | `0.175085` | `0.175085` | `0.484468` | `-6.385824` | `5.135078` |
| `atr_pullback_entry` | `3` | `18580` | `0.331` | `0.24488` | `0.24488` | `0.492465` | `-7.041081` | `5.40685` |
| `signal_close_retest_entry` | `1` | `39512` | `0.7039` | `-0.01514` | `-0.01514` | `0.475375` | `-3.264934` | `2.69235` |
| `open_guarded_retest_entry` | `1` | `34555` | `0.615592` | `-0.14208` | `-0.14208` | `0.45131` | `-3.166464` | `2.376248` |
| `next_open_entry` | `1` | `56068` | `0.998842` | `0.04571` | `0.04571` | `0.45946` | `-3.420293` | `2.764977` |
| `close_zone_limit_entry` | `1` | `43043` | `0.766804` | `-0.011412` | `-0.011412` | `0.474433` | `-3.248155` | `2.645052` |
| `atr_pullback_entry` | `1` | `18689` | `0.332941` | `-0.055093` | `-0.055093` | `0.476644` | `-3.248873` | `3.372624` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `283`
- total_return_pct: `21.276422`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.519435`
- skipped_capacity_count: `17064`
- skipped_same_symbol_count: `611`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-13.207137` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `283` | `21.276422` | `-23.08101` | `0.519435` |
| `exclude_market_risk_off` | `267` | `18.760095` | `-35.165321` | `0.490637` |
| `require_foreign_not_sell` | `283` | `17.457442` | `-23.08101` | `0.515901` |
| `exclude_risk_off_and_foreign_sell` | `267` | `22.911138` | `-32.899143` | `0.494382` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `117580` | 대성에너지 | `7030.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.470588` | `2.928258` | `0.744173` | `0.034455` |
| `004090` | 한국석유 | `11850.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-64.705882` | `3.043478` | `0.673464` | `0.037374` |
| `005870` | 휴니드 | `5570.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-52.995781` | `2.767528` | `0.50823` | `-0.008726` |
| `014530` | 극동유화 | `3265.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-49.536321` | `1.55521` | `0.777357` | `-0.030885` |
| `006890` | 태경케미컬 | `6460.0` |  |  | `market_risk_on` | `dual_buy` | `-39.851024` | `2.539683` | `0.482094` | `0.009255` |
| `272550` | 삼양패키징 | `9250.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-46.22093` | `9.080189` | `0.606864` | `0.02787` |
| `003520` | 영진약품 | `1271.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.358277` | `5.215232` | `0.81826` | `0.013651` |
| `465770` | STX그린로지스 | `2725.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-71.614583` | `7.072692` | `2.521448` | `0.017277` |
| `105630` | 한세실업 | `8950.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-42.406692` | `7.701564` | `0.587531` | `-0.114822` |
| `008930` | 한미사이언스 | `30350.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.315315` | `7.243816` | `0.566567` | `-0.030566` |
| `024720` | 콜마홀딩스 | `8320.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-22.962963` | `5.987261` | `0.518151` | `0.100238` |
| `007570` | 일양약품 | `8500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.780822` | `9.254499` | `0.600952` | `0.03397` |
| `001680` | 대상 | `18550.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-23.188406` | `5.577689` | `1.348885` | `0.107218` |
| `009070` | KCTC | `4510.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-46.24553` | `9.73236` | `0.425027` | `-0.028737` |
| `000120` | CJ대한통운 | `85300.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-39.503546` | `9.079284` | `0.489528` | `-0.065607` |
| `128940` | 한미약품 | `420500.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-35.007728` | `9.220779` | `0.647589` | `-0.004288` |
| `001780` | 알루코 | `2010.0` |  |  | `market_risk_on` | `dual_buy` | `-41.654572` | `7.2` | `0.442403` | `0.034125` |
| `000080` | 하이트진로 | `16020.0` |  |  | `market_risk_on` | `dual_buy` | `-16.994819` | `3.354839` | `1.040888` | `0.081675` |
| `090430` | 아모레퍼시픽 | `112500.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-32.228916` | `6.635071` | `0.550549` | `-0.030577` |
| `006040` | 동원산업 | `34400.0` |  |  | `market_risk_on` | `dual_buy` | `-28.998968` | `8.688784` | `0.936603` | `0.03846` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
