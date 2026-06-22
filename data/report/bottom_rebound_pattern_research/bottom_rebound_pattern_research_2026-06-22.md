# Bottom Rebound Pattern Research - 2026-06-22

- generated_at: `2026-06-22T20:24:13`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `57170`
- label_rows: `1429250`
- latest_as_of_candidate_count: `179`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.365793`
- backtest_trade_count: `291`
- backtest_total_return_pct: `8.038959`
- backtest_max_drawdown_pct: `-28.192334`
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
| `signal_close_retest_entry` | `20` | `38657` | `0.676176` | `1.809178` | `1.809178` | `0.490131` | `-16.992125` | `17.221946` |
| `open_guarded_retest_entry` | `20` | `34091` | `0.596309` | `1.597689` | `1.597689` | `0.482209` | `-16.95853` | `16.582915` |
| `next_open_entry` | `20` | `55110` | `0.963967` | `2.033482` | `2.033482` | `0.485738` | `-16.792893` | `17.418552` |
| `close_zone_limit_entry` | `20` | `42177` | `0.737747` | `1.804347` | `1.804347` | `0.487114` | `-16.86511` | `17.01772` |
| `atr_pullback_entry` | `20` | `17931` | `0.313644` | `2.413469` | `2.413469` | `0.518711` | `-17.046927` | `17.99422` |
| `signal_close_retest_entry` | `10` | `39083` | `0.683628` | `0.982341` | `0.982341` | `0.496917` | `-12.454754` | `11.233807` |
| `open_guarded_retest_entry` | `10` | `34368` | `0.601154` | `0.782618` | `0.782618` | `0.486586` | `-12.283652` | `10.723107` |
| `next_open_entry` | `10` | `55722` | `0.974672` | `1.084995` | `1.084995` | `0.495388` | `-12.340426` | `11.352534` |
| `close_zone_limit_entry` | `10` | `42625` | `0.745583` | `0.982487` | `0.982487` | `0.494123` | `-12.339579` | `11.104471` |
| `atr_pullback_entry` | `10` | `18224` | `0.318769` | `1.365793` | `1.365793` | `0.524583` | `-12.957806` | `11.557007` |
| `signal_close_retest_entry` | `5` | `39700` | `0.69442` | `0.404008` | `0.404008` | `0.48869` | `-8.748765` | `7.266076` |
| `open_guarded_retest_entry` | `5` | `34736` | `0.607591` | `0.253447` | `0.253447` | `0.479387` | `-8.559183` | `6.7406` |
| `next_open_entry` | `5` | `56527` | `0.988753` | `0.525895` | `0.525895` | `0.490845` | `-8.551724` | `7.48731` |
| `close_zone_limit_entry` | `5` | `43254` | `0.756586` | `0.419183` | `0.419183` | `0.488579` | `-8.603452` | `7.195377` |
| `atr_pullback_entry` | `5` | `18713` | `0.327322` | `0.449572` | `0.449572` | `0.501523` | `-9.470437` | `7.508048` |
| `signal_close_retest_entry` | `3` | `39757` | `0.695417` | `0.166305` | `0.166305` | `0.485952` | `-6.455593` | `5.219053` |
| `open_guarded_retest_entry` | `3` | `34772` | `0.608221` | `0.037329` | `0.037329` | `0.473772` | `-6.311217` | `4.769011` |
| `next_open_entry` | `3` | `56825` | `0.993965` | `0.246854` | `0.246854` | `0.479278` | `-6.4353` | `5.479452` |
| `close_zone_limit_entry` | `3` | `43319` | `0.757723` | `0.162731` | `0.162731` | `0.484914` | `-6.378198` | `5.169115` |
| `atr_pullback_entry` | `3` | `18726` | `0.327549` | `0.208041` | `0.208041` | `0.495087` | `-7.011853` | `5.425551` |
| `signal_close_retest_entry` | `1` | `39918` | `0.698233` | `-0.047411` | `-0.047411` | `0.471241` | `-3.268188` | `2.692229` |
| `open_guarded_retest_entry` | `1` | `34894` | `0.610355` | `-0.155783` | `-0.155783` | `0.449074` | `-3.167352` | `2.377377` |
| `next_open_entry` | `1` | `56991` | `0.996869` | `0.02024` | `0.02024` | `0.455282` | `-3.424191` | `2.765648` |
| `close_zone_limit_entry` | `1` | `43481` | `0.760556` | `-0.041544` | `-0.041544` | `0.470757` | `-3.25` | `2.646316` |
| `atr_pullback_entry` | `1` | `18874` | `0.330138` | `-0.124745` | `-0.124745` | `0.465932` | `-3.278279` | `3.333333` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `8.038959`
- max_drawdown_pct: `-28.192334`
- diagnostic_win_rate: `0.508591`
- skipped_capacity_count: `17315`
- skipped_same_symbol_count: `618`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-22.401495` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `8.038959` | `-28.192334` | `0.508591` |
| `exclude_market_risk_off` | `270` | `29.499707` | `-29.302246` | `0.503704` |
| `require_foreign_not_sell` | `291` | `15.463473` | `-23.25766` | `0.512027` |
| `exclude_risk_off_and_foreign_sell` | `270` | `32.315987` | `-27.764755` | `0.5` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `092200` | 디아이씨 | `6150.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-58.94526` | `1.151316` | `0.467808` | `-0.017611` |
| `009070` | KCTC | `4270.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.106079` | `3.140097` | `0.430576` | `0.039552` |
| `117580` | 대성에너지 | `6760.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-58.142415` | `1.197605` | `0.422158` | `-0.046465` |
| `003570` | SNT다이내믹스 | `39100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-37.738854` | `0.25641` | `0.680743` | `0.132904` |
| `249420` | 일동제약 | `17760.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-59.590444` | `1.718213` | `0.735392` | `0.027296` |
| `007570` | 일양약품 | `7870.0` |  |  | `market_risk_off` | `inst_buy_only` | `-51.539409` | `1.287001` | `0.401269` | `-0.095096` |
| `001430` | 세아베스틸지주 | `39350.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-57.459459` | `1.026958` | `0.796447` | `0.031479` |
| `005870` | 휴니드 | `4930.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-52.958015` | `1.649485` | `0.666594` | `-0.025991` |
| `128820` | 대성산업 | `4640.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-64.687976` | `0.4329` | `0.74315` | `-0.009718` |
| `003350` | 한국화장품제조 | `7750.0` |  |  | `market_risk_off` | `dual_buy` | `-85.067437` | `1.973684` | `0.442991` | `0.060772` |
| `009290` | 광동제약 | `5650.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-48.117539` | `1.436266` | `1.20726` | `-0.01596` |
| `018470` | 조일알미늄 | `1085.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.387494` | `2.455146` | `0.439946` | `-0.008788` |
| `128940` | 한미약품 | `403500.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-37.63524` | `1.63728` | `0.54999` | `-0.004239` |
| `026890` | 스틱인베스트먼트 | `6270.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-52.06422` | `4.674457` | `1.005008` | `0.075947` |
| `004140` | 동방 | `1892.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-39.358974` | `3.275109` | `0.426615` | `0.006824` |
| `105630` | 한세실업 | `8590.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-44.723295` | `3.121248` | `0.53361` | `-0.102516` |
| `035510` | 신세계 I&C | `13620.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-53.515358` | `0.516605` | `0.483998` | `-0.004411` |
| `016610` | DB증권 | `9780.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.97767` | `2.408377` | `0.774443` | `0.01866` |
| `001780` | 알루코 | `1901.0` |  |  | `market_risk_off` | `dual_sell_or_flat` | `-45.608011` | `2.867965` | `0.425044` | `-0.012257` |
| `950210` | 프레스티지바이오파마 | `6440.0` |  |  | `market_risk_off` | `dual_buy` | `-54.390935` | `4.885993` | `0.70999` | `0.000428` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
