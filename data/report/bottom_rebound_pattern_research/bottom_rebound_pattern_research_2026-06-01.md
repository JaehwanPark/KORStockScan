# Bottom Rebound Pattern Research - 2026-06-01

- generated_at: `2026-06-01T21:27:11`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56820`
- label_rows: `1420500`
- latest_as_of_candidate_count: `175`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.554105`
- backtest_trade_count: `291`
- backtest_total_return_pct: `49.841158`
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
| `signal_close_retest_entry` | `20` | `38857` | `0.683861` | `1.794784` | `1.794784` | `0.491392` | `-16.881056` | `17.234705` |
| `open_guarded_retest_entry` | `20` | `34287` | `0.603432` | `1.581922` | `1.581922` | `0.483244` | `-16.851002` | `16.582915` |
| `next_open_entry` | `20` | `55363` | `0.974358` | `1.99996` | `1.99996` | `0.487528` | `-16.618911` | `17.385912` |
| `close_zone_limit_entry` | `20` | `42385` | `0.745952` | `1.788206` | `1.788206` | `0.488498` | `-16.767927` | `17.032361` |
| `atr_pullback_entry` | `20` | `18088` | `0.318339` | `2.38422` | `2.38422` | `0.518521` | `-16.869103` | `18.058563` |
| `signal_close_retest_entry` | `10` | `39065` | `0.687522` | `1.114042` | `1.114042` | `0.500986` | `-12.190351` | `11.245948` |
| `open_guarded_retest_entry` | `10` | `34455` | `0.606389` | `0.863222` | `0.863222` | `0.488928` | `-12.110473` | `10.72593` |
| `next_open_entry` | `10` | `55807` | `0.982172` | `1.268474` | `1.268474` | `0.500869` | `-11.979044` | `11.374129` |
| `close_zone_limit_entry` | `10` | `42607` | `0.749859` | `1.112531` | `1.112531` | `0.498017` | `-12.099133` | `11.111111` |
| `atr_pullback_entry` | `10` | `18173` | `0.319835` | `1.554105` | `1.554105` | `0.531448` | `-12.575711` | `11.564312` |
| `signal_close_retest_entry` | `5` | `39337` | `0.692309` | `0.420045` | `0.420045` | `0.48959` | `-8.576487` | `7.15037` |
| `open_guarded_retest_entry` | `5` | `34639` | `0.609627` | `0.276039` | `0.276039` | `0.48073` | `-8.442737` | `6.686069` |
| `next_open_entry` | `5` | `56144` | `0.988103` | `0.576163` | `0.576163` | `0.493107` | `-8.350885` | `7.392763` |
| `close_zone_limit_entry` | `5` | `42888` | `0.754805` | `0.435414` | `0.435414` | `0.489158` | `-8.447725` | `7.082989` |
| `atr_pullback_entry` | `5` | `18382` | `0.323513` | `0.479353` | `0.479353` | `0.502992` | `-9.24127` | `7.33926` |
| `signal_close_retest_entry` | `3` | `39467` | `0.694597` | `0.165256` | `0.165256` | `0.48595` | `-6.365762` | `5.143836` |
| `open_guarded_retest_entry` | `3` | `34701` | `0.610718` | `0.048355` | `0.048355` | `0.474251` | `-6.26208` | `4.743125` |
| `next_open_entry` | `3` | `56367` | `0.992027` | `0.256857` | `0.256857` | `0.479057` | `-6.344216` | `5.384615` |
| `close_zone_limit_entry` | `3` | `43025` | `0.757216` | `0.161637` | `0.161637` | `0.484648` | `-6.303544` | `5.115127` |
| `atr_pullback_entry` | `3` | `18459` | `0.324868` | `0.229575` | `0.229575` | `0.496181` | `-6.882943` | `5.339884` |
| `signal_close_retest_entry` | `1` | `39732` | `0.699261` | `-0.056721` | `-0.056721` | `0.47093` | `-3.268617` | `2.666348` |
| `open_guarded_retest_entry` | `1` | `34907` | `0.614344` | `-0.164065` | `-0.164065` | `0.449079` | `-3.17505` | `2.365802` |
| `next_open_entry` | `1` | `56645` | `0.99692` | `0.014777` | `0.014777` | `0.455221` | `-3.416584` | `2.732919` |
| `close_zone_limit_entry` | `1` | `43291` | `0.761897` | `-0.05052` | `-0.05052` | `0.470375` | `-3.249572` | `2.617636` |
| `atr_pullback_entry` | `1` | `18702` | `0.329145` | `-0.141326` | `-0.141326` | `0.466046` | `-3.301461` | `3.307303` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `49.841158`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.5189`
- skipped_capacity_count: `17267`
- skipped_same_symbol_count: `615`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `7.203852` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `49.841158` | `-23.08101` | `0.5189` |
| `exclude_market_risk_off` | `275` | `29.357369` | `-29.379953` | `0.487273` |
| `require_foreign_not_sell` | `291` | `38.951324` | `-23.08101` | `0.515464` |
| `exclude_risk_off_and_foreign_sell` | `275` | `31.521847` | `-28.1983` | `0.494545` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `117580` | 대성에너지 | `7440.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.931889` | `2.338377` | `0.713794` | `0.008171` |
| `004090` | 한국석유 | `12600.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-62.472077` | `2.857143` | `0.750857` | `-0.00931` |
| `272550` | 삼양패키징 | `9330.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.807298` | `1.302932` | `0.674762` | `-0.01323` |
| `009070` | KCTC | `4740.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.504172` | `1.390374` | `1.239644` | `0.036105` |
| `465770` | STX그린로지스 | `2855.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-70.260417` | `2.329749` | `0.429168` | `0.02274` |
| `000120` | CJ대한통운 | `84400.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.141844` | `1.442308` | `0.98413` | `0.011895` |
| `192650` | 드림텍 | `4880.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-42.248521` | `2.413431` | `1.100414` | `-0.01403` |
| `105630` | 한세실업 | `8650.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.337194` | `0.815851` | `1.730065` | `-0.013751` |
| `029780` | 삼성카드 | `45850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-33.742775` | `0.769231` | `1.265784` | `0.060643` |
| `013360` | 일성건설 | `1293.0` |  |  | `market_risk_off` | `inst_buy_only` | `-48.994083` | `2.782194` | `0.825475` | `-0.007822` |
| `381970` | 케이카 | `8920.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.90661` | `0.563698` | `1.010959` | `-0.112731` |
| `001550` | 조비 | `10900.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.97136` | `4.106972` | `0.577699` | `0.022298` |
| `014530` | 극동유화 | `3385.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.681607` | `5.287714` | `0.784865` | `0.05382` |
| `005870` | 휴니드 | `6000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-42.748092` | `0.166945` | `0.678134` | `0.011844` |
| `037270` | YG PLUS | `3785.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-50.262812` | `2.297297` | `1.140686` | `-0.06125` |
| `009240` | 한샘 | `31100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.761905` | `5.245347` | `1.074686` | `0.042783` |
| `950210` | 프레스티지바이오파마 | `6530.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.95389` | `1.872075` | `2.003029` | `0.006231` |
| `128820` | 대성산업 | `5580.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-57.534247` | `0.359712` | `1.195606` | `-0.014013` |
| `006220` | 제주은행 | `9640.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-46.145251` | `1.473684` | `1.622961` | `-0.02864` |
| `004310` | 현대약품 | `6470.0` |  |  | `market_risk_off` | `inst_buy_only` | `-57.434211` | `3.189793` | `1.089037` | `-0.04118` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
