# Bottom Rebound Pattern Research - 2026-07-09

- generated_at: `2026-07-09T20:53:29`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58079`
- label_rows: `1451975`
- latest_as_of_candidate_count: `193`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.331094`
- backtest_trade_count: `293`
- backtest_total_return_pct: `226.462108`
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
| `signal_close_retest_entry` | `20` | `38848` | `0.668882` | `1.811936` | `1.811936` | `0.487927` | `-17.211441` | `17.206837` |
| `open_guarded_retest_entry` | `20` | `34221` | `0.589215` | `1.55786` | `1.55786` | `0.480553` | `-17.129507` | `16.54426` |
| `next_open_entry` | `20` | `55267` | `0.951583` | `2.064594` | `2.064594` | `0.483562` | `-16.989456` | `17.391304` |
| `close_zone_limit_entry` | `20` | `42376` | `0.729627` | `1.802337` | `1.802337` | `0.484826` | `-17.056781` | `17.01772` |
| `atr_pullback_entry` | `20` | `18079` | `0.311283` | `2.465339` | `2.465339` | `0.516511` | `-17.279877` | `18.01341` |
| `signal_close_retest_entry` | `10` | `39868` | `0.686444` | `0.939005` | `0.939005` | `0.493203` | `-12.788311` | `11.396594` |
| `open_guarded_retest_entry` | `10` | `34830` | `0.5997` | `0.707206` | `0.707206` | `0.482888` | `-12.564804` | `10.778552` |
| `next_open_entry` | `10` | `56605` | `0.974621` | `1.047548` | `1.047548` | `0.491617` | `-12.675185` | `11.461029` |
| `close_zone_limit_entry` | `10` | `43409` | `0.747413` | `0.943698` | `0.943698` | `0.490843` | `-12.65265` | `11.262364` |
| `atr_pullback_entry` | `10` | `18933` | `0.325987` | `1.331094` | `1.331094` | `0.518618` | `-13.497371` | `11.859386` |
| `signal_close_retest_entry` | `5` | `40483` | `0.697033` | `0.389348` | `0.389348` | `0.488304` | `-8.92007` | `7.414279` |
| `open_guarded_retest_entry` | `5` | `35166` | `0.605486` | `0.230533` | `0.230533` | `0.47853` | `-8.746945` | `6.811429` |
| `next_open_entry` | `5` | `57355` | `0.987534` | `0.500621` | `0.500621` | `0.489879` | `-8.777893` | `7.582938` |
| `close_zone_limit_entry` | `5` | `44040` | `0.758278` | `0.40861` | `0.40861` | `0.488374` | `-8.783215` | `7.319969` |
| `atr_pullback_entry` | `5` | `19387` | `0.333804` | `0.430914` | `0.430914` | `0.499974` | `-9.73482` | `7.800394` |
| `signal_close_retest_entry` | `3` | `40689` | `0.70058` | `0.230142` | `0.230142` | `0.488363` | `-6.631648` | `5.32828` |
| `open_guarded_retest_entry` | `3` | `35296` | `0.607724` | `0.043824` | `0.043824` | `0.473765` | `-6.476329` | `4.814897` |
| `next_open_entry` | `3` | `57606` | `0.991856` | `0.275529` | `0.275529` | `0.479395` | `-6.605923` | `5.521472` |
| `close_zone_limit_entry` | `3` | `44248` | `0.761859` | `0.223558` | `0.223558` | `0.48748` | `-6.538753` | `5.28169` |
| `atr_pullback_entry` | `3` | `19521` | `0.336111` | `0.341394` | `0.341394` | `0.498899` | `-7.286327` | `5.661543` |
| `signal_close_retest_entry` | `1` | `40951` | `0.705091` | `0.006064` | `0.006064` | `0.475593` | `-3.355549` | `2.760996` |
| `open_guarded_retest_entry` | `1` | `35463` | `0.610599` | `-0.142776` | `-0.142776` | `0.450723` | `-3.226025` | `2.411793` |
| `next_open_entry` | `1` | `57886` | `0.996677` | `0.054487` | `0.054487` | `0.458885` | `-3.493656` | `2.816901` |
| `close_zone_limit_entry` | `1` | `44513` | `0.766422` | `0.007414` | `0.007414` | `0.474513` | `-3.328027` | `2.711231` |
| `atr_pullback_entry` | `1` | `19732` | `0.339744` | `-0.006054` | `-0.006054` | `0.478461` | `-3.387186` | `3.469954` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `226.462108`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.515358`
- skipped_capacity_count: `18006`
- skipped_same_symbol_count: `634`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `133.440331` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `226.462108` | `-23.08101` | `0.515358` |
| `exclude_market_risk_off` | `272` | `23.994735` | `-32.307575` | `0.496324` |
| `require_foreign_not_sell` | `293` | `220.12857` | `-23.08101` | `0.511945` |
| `exclude_risk_off_and_foreign_sell` | `272` | `27.669642` | `-30.301333` | `0.5` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `377300` | 카카오페이 | `37450.0` |  |  | `market_risk_off` | `dual_buy` | `-49.185889` | `1.490515` | `1.07985` | `0.11514` |
| `249420` | 일동제약 | `14850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-66.211604` | `1.712329` | `0.908575` | `0.263927` |
| `950210` | 프레스티지바이오파마 | `5680.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-59.07781` | `1.974865` | `0.63397` | `0.119217` |
| `103140` | 풍산 | `61500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-61.369347` | `2.5` | `0.95135` | `0.163569` |
| `003570` | SNT다이내믹스 | `32650.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.168285` | `1.55521` | `0.790383` | `0.10062` |
| `001500` | 현대차증권 | `7810.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.833333` | `1.825293` | `0.633344` | `0.123761` |
| `381970` | 케이카 | `7870.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-51.087632` | `1.026958` | `0.716042` | `0.042117` |
| `019170` | 신풍제약 | `7870.0` |  |  | `market_risk_off` | `dual_buy` | `-44.342291` | `0.897436` | `0.900689` | `0.119264` |
| `003540` | 대신증권 | `26450.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-43.783209` | `2.718447` | `0.79836` | `0.118999` |
| `439260` | 대한조선 | `47000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.618508` | `0.750268` | `0.526885` | `0.027493` |
| `000390` | SP삼화 | `5880.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.388664` | `1.730104` | `0.601277` | `0.089188` |
| `011170` | 롯데케미칼 | `61300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.444071` | `4.786325` | `1.049646` | `0.071428` |
| `037560` | LG헬로비전 | `1550.0` |  |  | `market_risk_off` | `dual_buy` | `-57.650273` | `0.911458` | `0.431906` | `0.004985` |
| `010660` | 화천기계 | `2575.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.925645` | `1.577909` | `0.482363` | `0.020732` |
| `200880` | 서연이화 | `10600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.940092` | `2.812803` | `0.471797` | `0.124067` |
| `128820` | 대성산업 | `4130.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-68.569254` | `1.849568` | `0.418152` | `0.022214` |
| `003530` | 한화투자증권 | `4370.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.769231` | `1.864802` | `0.616824` | `0.023927` |
| `011690` | 와이투솔루션 | `2930.0` |  |  | `market_risk_off` | `dual_buy` | `-70.253807` | `2.447552` | `0.713968` | `0.065368` |
| `008970` | KBI동양철관 | `1107.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.452055` | `1.373626` | `0.877872` | `0.024518` |
| `005010` | 휴스틸 | `3680.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.311295` | `0.821918` | `0.493914` | `0.001759` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
