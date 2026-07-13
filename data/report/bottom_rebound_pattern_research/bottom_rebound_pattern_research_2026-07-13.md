# Bottom Rebound Pattern Research - 2026-07-13

- generated_at: `2026-07-13T20:54:24`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58325`
- label_rows: `1458125`
- latest_as_of_candidate_count: `187`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.344532`
- backtest_trade_count: `293`
- backtest_total_return_pct: `217.391441`
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
| `signal_close_retest_entry` | `20` | `38941` | `0.667655` | `1.801813` | `1.801813` | `0.487789` | `-17.278701` | `17.177097` |
| `open_guarded_retest_entry` | `20` | `34324` | `0.588495` | `1.562651` | `1.562651` | `0.480364` | `-17.200313` | `16.557447` |
| `next_open_entry` | `20` | `55390` | `0.949679` | `2.055091` | `2.055091` | `0.483481` | `-17.030021` | `17.373791` |
| `close_zone_limit_entry` | `20` | `42470` | `0.728161` | `1.792769` | `1.792769` | `0.484601` | `-17.11421` | `16.995976` |
| `atr_pullback_entry` | `20` | `18164` | `0.311427` | `2.452171` | `2.452171` | `0.515966` | `-17.414921` | `17.982505` |
| `signal_close_retest_entry` | `10` | `39938` | `0.684749` | `0.935001` | `0.935001` | `0.49344` | `-12.808385` | `11.391252` |
| `open_guarded_retest_entry` | `10` | `34923` | `0.598766` | `0.717921` | `0.717921` | `0.483292` | `-12.577466` | `10.786337` |
| `next_open_entry` | `10` | `56725` | `0.972568` | `1.037935` | `1.037935` | `0.491494` | `-12.708056` | `11.461029` |
| `close_zone_limit_entry` | `10` | `43484` | `0.745547` | `0.938915` | `0.938915` | `0.490939` | `-12.66432` | `11.249267` |
| `atr_pullback_entry` | `10` | `18965` | `0.325161` | `1.344532` | `1.344532` | `0.519325` | `-13.490235` | `11.854417` |
| `signal_close_retest_entry` | `5` | `40625` | `0.696528` | `0.384835` | `0.384835` | `0.488148` | `-8.926261` | `7.415707` |
| `open_guarded_retest_entry` | `5` | `35303` | `0.605281` | `0.237343` | `0.237343` | `0.478939` | `-8.734473` | `6.825786` |
| `next_open_entry` | `5` | `57542` | `0.986575` | `0.497666` | `0.497666` | `0.489764` | `-8.777763` | `7.592305` |
| `close_zone_limit_entry` | `5` | `44184` | `0.757548` | `0.40466` | `0.40466` | `0.488118` | `-8.785367` | `7.321966` |
| `atr_pullback_entry` | `5` | `19473` | `0.333871` | `0.427748` | `0.427748` | `0.49982` | `-9.736964` | `7.780924` |
| `signal_close_retest_entry` | `3` | `40839` | `0.700197` | `0.22834` | `0.22834` | `0.488283` | `-6.653129` | `5.324459` |
| `open_guarded_retest_entry` | `3` | `35449` | `0.607784` | `0.048011` | `0.048011` | `0.474231` | `-6.488049` | `4.825201` |
| `next_open_entry` | `3` | `57799` | `0.990982` | `0.270422` | `0.270422` | `0.479005` | `-6.610195` | `5.519202` |
| `close_zone_limit_entry` | `3` | `44402` | `0.761286` | `0.221637` | `0.221637` | `0.48732` | `-6.552935` | `5.278425` |
| `atr_pullback_entry` | `3` | `19618` | `0.336357` | `0.342283` | `0.342283` | `0.499235` | `-7.330437` | `5.656966` |
| `signal_close_retest_entry` | `1` | `41049` | `0.703798` | `0.006304` | `0.006304` | `0.475529` | `-3.353667` | `2.761039` |
| `open_guarded_retest_entry` | `1` | `35533` | `0.609224` | `-0.14157` | `-0.14157` | `0.450595` | `-3.219803` | `2.41425` |
| `next_open_entry` | `1` | `58138` | `0.996794` | `0.054558` | `0.054558` | `0.458771` | `-3.496503` | `2.826087` |
| `close_zone_limit_entry` | `1` | `44620` | `0.765024` | `0.00787` | `0.00787` | `0.474406` | `-3.3245` | `2.712522` |
| `atr_pullback_entry` | `1` | `19779` | `0.339117` | `-0.005157` | `-0.005157` | `0.478437` | `-3.382202` | `3.470466` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `217.391441`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.505119`
- skipped_capacity_count: `18031`
- skipped_same_symbol_count: `641`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `125.925011` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `293` | `217.391441` | `-23.08101` | `0.505119` |
| `exclude_market_risk_off` | `275` | `5.436202` | `-42.439232` | `0.487273` |
| `require_foreign_not_sell` | `293` | `207.409809` | `-23.08101` | `0.505119` |
| `exclude_risk_off_and_foreign_sell` | `275` | `13.28876` | `-38.152286` | `0.498182` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `249420` | 일동제약 | `14510.0` |  |  | `market_neutral` | `foreign_buy_only` | `-66.98521` | `0.624133` | `0.698543` | `0.245933` |
| `008730` | 율촌화학 | `13970.0` |  |  | `market_neutral` | `foreign_buy_only` | `-51.993127` | `2.045289` | `0.629929` | `0.085469` |
| `012450` | 한화에어로스페이스 | `936000.0` |  |  | `market_neutral` | `dual_buy` | `-43.444109` | `1.079914` | `0.805292` | `0.006192` |
| `019170` | 신풍제약 | `7890.0` |  |  | `market_neutral` | `dual_buy` | `-42.950108` | `1.153846` | `0.792497` | `0.089961` |
| `381970` | 케이카 | `7740.0` |  |  | `market_neutral` | `foreign_buy_only` | `-50.543131` | `0.650195` | `0.808315` | `0.033695` |
| `000520` | 삼일제약 | `6020.0` |  |  | `market_neutral` | `foreign_buy_only` | `-53.18818` | `0.333333` | `0.688754` | `0.053874` |
| `950210` | 프레스티지바이오파마 | `5530.0` |  |  | `market_neutral` | `foreign_buy_only` | `-60.158501` | `4.339623` | `1.017619` | `0.109581` |
| `439260` | 대한조선 | `46450.0` |  |  | `market_neutral` | `foreign_buy_only` | `-56.137866` | `0.21575` | `0.904933` | `0.023452` |
| `079900` | 전진건설로봇 | `33400.0` |  |  | `market_neutral` | `foreign_buy_only` | `-55.077337` | `0.3003` | `0.720628` | `0.018903` |
| `003160` | 디아이 | `20800.0` |  |  | `market_neutral` | `foreign_buy_only` | `-46.666667` | `0.970874` | `1.007605` | `0.036859` |
| `003540` | 대신증권 | `26250.0` |  |  | `market_neutral` | `foreign_buy_only` | `-44.208289` | `1.941748` | `1.803847` | `0.112597` |
| `000390` | SP삼화 | `5910.0` |  |  | `market_neutral` | `dual_buy` | `-52.145749` | `2.249135` | `0.988851` | `0.082453` |
| `001360` | 삼성제약 | `1243.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-46.422414` | `0.322841` | `0.702956` | `-0.004452` |
| `123690` | 한국화장품 | `6200.0` |  |  | `market_neutral` | `foreign_buy_only` | `-51.065509` | `4.906937` | `0.799162` | `0.104841` |
| `008970` | KBI동양철관 | `1087.0` |  |  | `market_neutral` | `foreign_buy_only` | `-50.365297` | `0.184332` | `1.36967` | `0.01691` |
| `011170` | 롯데케미칼 | `60600.0` |  |  | `market_neutral` | `foreign_buy_only` | `-49.032801` | `3.589744` | `0.70705` | `0.057046` |
| `103140` | 풍산 | `62800.0` |  |  | `market_neutral` | `foreign_buy_only` | `-60.552764` | `4.666667` | `0.952941` | `0.156109` |
| `000100` | 유한양행 | `68100.0` |  |  | `market_neutral` | `dual_buy` | `-40.885417` | `2.406015` | `0.786232` | `0.059098` |
| `005010` | 휴스틸 | `3635.0` |  |  | `market_neutral` | `dual_sell_or_flat` | `-49.931129` | `1.536313` | `0.695035` | `-0.0071` |
| `011700` | 한신기계 | `2350.0` |  |  | `market_neutral` | `foreign_buy_only` | `-58.333333` | `2.396514` | `0.561972` | `0.018752` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
