# Bottom Rebound Pattern Research - 2026-06-10

- generated_at: `2026-06-10T20:44:49`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57126`
- label_rows: `1428150`
- latest_as_of_candidate_count: `191`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.424577`
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
| `signal_close_retest_entry` | `20` | `38817` | `0.679498` | `1.783815` | `1.783815` | `0.490558` | `-16.9293` | `17.243256` |
| `open_guarded_retest_entry` | `20` | `34228` | `0.599167` | `1.579029` | `1.579029` | `0.482646` | `-16.902448` | `16.609099` |
| `next_open_entry` | `20` | `55348` | `0.968876` | `1.996728` | `1.996728` | `0.486052` | `-16.701176` | `17.401733` |
| `close_zone_limit_entry` | `20` | `42345` | `0.741256` | `1.787066` | `1.787066` | `0.487472` | `-16.819348` | `17.038399` |
| `atr_pullback_entry` | `20` | `18030` | `0.315618` | `2.349072` | `2.349072` | `0.51797` | `-16.953187` | `18.011196` |
| `signal_close_retest_entry` | `10` | `39070` | `0.683927` | `1.03095` | `1.03095` | `0.498925` | `-12.277111` | `11.24503` |
| `open_guarded_retest_entry` | `10` | `34424` | `0.602598` | `0.80553` | `0.80553` | `0.487654` | `-12.174451` | `10.730325` |
| `next_open_entry` | `10` | `55727` | `0.97551` | `1.161065` | `1.161065` | `0.498197` | `-12.099301` | `11.359973` |
| `close_zone_limit_entry` | `10` | `42611` | `0.745913` | `1.032995` | `1.032995` | `0.496139` | `-12.179979` | `11.111111` |
| `atr_pullback_entry` | `10` | `18206` | `0.318699` | `1.424577` | `1.424577` | `0.527573` | `-12.779567` | `11.562975` |
| `signal_close_retest_entry` | `5` | `39424` | `0.690124` | `0.364778` | `0.364778` | `0.487368` | `-8.689711` | `7.160566` |
| `open_guarded_retest_entry` | `5` | `34645` | `0.606466` | `0.240121` | `0.240121` | `0.479348` | `-8.492378` | `6.694989` |
| `next_open_entry` | `5` | `56222` | `0.984175` | `0.498952` | `0.498952` | `0.490075` | `-8.500141` | `7.387308` |
| `close_zone_limit_entry` | `5` | `42977` | `0.752319` | `0.383508` | `0.383508` | `0.487144` | `-8.54606` | `7.090693` |
| `atr_pullback_entry` | `5` | `18466` | `0.32325` | `0.372989` | `0.372989` | `0.498646` | `-9.405489` | `7.351816` |
| `signal_close_retest_entry` | `3` | `39716` | `0.695235` | `0.120877` | `0.120877` | `0.483609` | `-6.51718` | `5.149339` |
| `open_guarded_retest_entry` | `3` | `34840` | `0.60988` | `0.020039` | `0.020039` | `0.473077` | `-6.351682` | `4.750176` |
| `next_open_entry` | `3` | `56554` | `0.989987` | `0.209428` | `0.209428` | `0.476854` | `-6.453574` | `5.387931` |
| `close_zone_limit_entry` | `3` | `43271` | `0.757466` | `0.121107` | `0.121107` | `0.482563` | `-6.430408` | `5.117273` |
| `atr_pullback_entry` | `3` | `18697` | `0.327294` | `0.138654` | `0.138654` | `0.491255` | `-7.116777` | `5.350521` |
| `signal_close_retest_entry` | `1` | `39947` | `0.699279` | `-0.050977` | `-0.050977` | `0.472101` | `-3.278689` | `2.692761` |
| `open_guarded_retest_entry` | `1` | `34934` | `0.611525` | `-0.159718` | `-0.159718` | `0.450049` | `-3.182519` | `2.381064` |
| `next_open_entry` | `1` | `56935` | `0.996657` | `0.016534` | `0.016534` | `0.455994` | `-3.431373` | `2.75957` |
| `close_zone_limit_entry` | `1` | `43512` | `0.761685` | `-0.044929` | `-0.044929` | `0.471548` | `-3.255695` | `2.64782` |
| `atr_pullback_entry` | `1` | `18863` | `0.3302` | `-0.137397` | `-0.137397` | `0.466893` | `-3.317458` | `3.325704` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `20.607622`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.515464`
- skipped_capacity_count: `17299`
- skipped_same_symbol_count: `616`

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
| `009070` | KCTC | `4240.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.463647` | `2.415459` | `0.453307` | `0.023028` |
| `010660` | 화천기계 | `2740.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-58.421851` | `3.201507` | `0.700705` | `-0.011746` |
| `014530` | 극동유화 | `3255.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-49.690881` | `1.560062` | `0.508718` | `-0.01418` |
| `003520` | 영진약품 | `1235.0` |  |  | `market_risk_on` | `inst_buy_only` | `-43.99093` | `2.660017` | `0.749166` | `-0.085903` |
| `006890` | 태경케미컬 | `6380.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.189003` | `1.430843` | `1.038909` | `-0.025019` |
| `103140` | 풍산 | `70100.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-55.967337` | `5.572289` | `0.797591` | `0.049804` |
| `004090` | 한국석유 | `11930.0` |  |  | `market_risk_on` | `inst_buy_only` | `-64.46761` | `2.403433` | `0.707329` | `-0.034017` |
| `001360` | 삼성제약 | `1335.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-41.447368` | `2.929838` | `0.505181` | `-0.027732` |
| `117580` | 대성에너지 | `6980.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-56.780186` | `2.046784` | `0.409973` | `-0.037118` |
| `128820` | 대성산업 | `5150.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-60.806697` | `3.830645` | `0.629791` | `-0.01397` |
| `011700` | 한신기계 | `2665.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-54.676871` | `3.294574` | `0.562625` | `-0.012693` |
| `105630` | 한세실업 | `8520.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.173745` | `2.280912` | `0.765725` | `-0.087616` |
| `128940` | 한미약품 | `411500.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-36.398764` | `3.522013` | `1.073655` | `-0.023488` |
| `004310` | 현대약품 | `5590.0` |  |  | `market_risk_on` | `inst_buy_only` | `-63.223684` | `3.327172` | `0.5513` | `-0.042298` |
| `005870` | 휴니드 | `5500.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-47.519084` | `3.383459` | `0.587173` | `-0.011376` |
| `381970` | 케이카 | `8460.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-49.310965` | `2.794654` | `0.635444` | `-0.092185` |
| `017860` | DS단석 | `14260.0` |  |  | `market_risk_on` | `inst_buy_only` | `-46.086957` | `2.148997` | `0.801289` | `-0.023462` |
| `001680` | 대상 | `17920.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-25.797101` | `2.341519` | `0.993854` | `0.079689` |
| `352820` | 하이브 | `205000.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-48.877805` | `5.128205` | `0.661924` | `-0.064421` |
| `000490` | 대동 | `7210.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-47.140762` | `2.706553` | `0.937701` | `-0.043436` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
