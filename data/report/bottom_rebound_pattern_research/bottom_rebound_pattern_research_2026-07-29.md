# Bottom Rebound Pattern Research - 2026-07-29

- generated_at: `2026-07-29T20:56:55`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `59117`
- label_rows: `1477925`
- latest_as_of_candidate_count: `229`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.273349`
- backtest_trade_count: `296`
- backtest_total_return_pct: `163.339892`
- backtest_max_drawdown_pct: `-34.32245`
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
| `signal_close_retest_entry` | `20` | `39435` | `0.667067` | `1.689302` | `1.689302` | `0.482896` | `-17.69175` | `17.22018` |
| `open_guarded_retest_entry` | `20` | `34634` | `0.585855` | `1.459486` | `1.459486` | `0.476844` | `-17.437475` | `16.584765` |
| `next_open_entry` | `20` | `56050` | `0.94812` | `1.918259` | `1.918259` | `0.478876` | `-17.460317` | `17.419709` |
| `close_zone_limit_entry` | `20` | `42971` | `0.726881` | `1.678089` | `1.678089` | `0.480068` | `-17.506252` | `17.018284` |
| `atr_pullback_entry` | `20` | `18560` | `0.313954` | `2.206365` | `2.206365` | `0.506735` | `-18.135967` | `17.966925` |
| `signal_close_retest_entry` | `10` | `40367` | `0.682832` | `0.909499` | `0.909499` | `0.491565` | `-12.972642` | `11.428571` |
| `open_guarded_retest_entry` | `10` | `35136` | `0.594347` | `0.723972` | `0.723972` | `0.484033` | `-12.620368` | `10.818986` |
| `next_open_entry` | `10` | `57675` | `0.975608` | `0.983427` | `0.983427` | `0.488739` | `-12.992126` | `11.518392` |
| `close_zone_limit_entry` | `10` | `43931` | `0.74312` | `0.916745` | `0.916745` | `0.489199` | `-12.866011` | `11.297347` |
| `atr_pullback_entry` | `10` | `19302` | `0.326505` | `1.273349` | `1.273349` | `0.516061` | `-13.695063` | `11.83864` |
| `signal_close_retest_entry` | `5` | `40835` | `0.690749` | `0.357679` | `0.357679` | `0.486813` | `-9.052709` | `7.374509` |
| `open_guarded_retest_entry` | `5` | `35356` | `0.598068` | `0.227959` | `0.227959` | `0.478391` | `-8.731582` | `6.843743` |
| `next_open_entry` | `5` | `58379` | `0.987516` | `0.426549` | `0.426549` | `0.485997` | `-9.025823` | `7.594937` |
| `close_zone_limit_entry` | `5` | `44417` | `0.751341` | `0.373848` | `0.373848` | `0.486683` | `-8.931816` | `7.290746` |
| `atr_pullback_entry` | `5` | `19545` | `0.330616` | `0.412859` | `0.412859` | `0.500435` | `-9.857681` | `7.705966` |
| `signal_close_retest_entry` | `3` | `41019` | `0.693861` | `0.150272` | `0.150272` | `0.485775` | `-6.679356` | `5.357221` |
| `open_guarded_retest_entry` | `3` | `35416` | `0.599083` | `0.023965` | `0.023965` | `0.473854` | `-6.440053` | `4.842394` |
| `next_open_entry` | `3` | `58703` | `0.992997` | `0.20916` | `0.20916` | `0.477505` | `-6.718968` | `5.611511` |
| `close_zone_limit_entry` | `3` | `44609` | `0.754588` | `0.147774` | `0.147774` | `0.484812` | `-6.595776` | `5.310286` |
| `atr_pullback_entry` | `3` | `19680` | `0.332899` | `0.185415` | `0.185415` | `0.493953` | `-7.364343` | `5.675364` |
| `signal_close_retest_entry` | `1` | `41175` | `0.6965` | `-0.052857` | `-0.052857` | `0.471087` | `-3.386426` | `2.746415` |
| `open_guarded_retest_entry` | `1` | `35487` | `0.600284` | `-0.160914` | `-0.160914` | `0.448897` | `-3.224792` | `2.398786` |
| `next_open_entry` | `1` | `58888` | `0.996126` | `0.014935` | `0.014935` | `0.455237` | `-3.547027` | `2.821999` |
| `close_zone_limit_entry` | `1` | `44766` | `0.757244` | `-0.046426` | `-0.046426` | `0.470692` | `-3.351204` | `2.700076` |
| `atr_pullback_entry` | `1` | `19813` | `0.335149` | `-0.135953` | `-0.135953` | `0.466966` | `-3.474143` | `3.380398` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `296`
- total_return_pct: `163.339892`
- max_drawdown_pct: `-34.32245`
- diagnostic_win_rate: `0.503378`
- skipped_capacity_count: `18362`
- skipped_same_symbol_count: `644`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `88.026839` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `296` | `163.339892` | `-34.32245` | `0.503378` |
| `exclude_market_risk_off` | `275` | `1.266074` | `-44.715829` | `0.487273` |
| `require_foreign_not_sell` | `296` | `158.940933` | `-34.003324` | `0.5` |
| `exclude_risk_off_and_foreign_sell` | `275` | `5.479788` | `-42.415437` | `0.494545` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `117580` | 대성에너지 | `6530.0` |  |  | `market_risk_off` | `dual_buy` | `-59.566563` | `2.03125` | `1.318999` | `0.056236` |
| `003280` | 흥아해운 | `1529.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-66.976242` | `0.328084` | `1.483598` | `0.003276` |
| `034230` | 파라다이스 | `9630.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.926773` | `1.475237` | `1.15621` | `0.124182` |
| `011210` | 현대위아 | `52200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-49.565217` | `3.366337` | `1.451984` | `0.152496` |
| `004990` | 롯데지주 | `21650.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-42.572944` | `1.882353` | `1.121919` | `0.197124` |
| `019170` | 신풍제약 | `7270.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.543071` | `3.708987` | `1.33605` | `0.116229` |
| `128820` | 대성산업 | `3700.0` |  |  | `market_risk_off` | `dual_buy` | `-71.841705` | `1.928375` | `1.526997` | `0.080132` |
| `011170` | 롯데케미칼 | `54600.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.309623` | `2.631579` | `0.940017` | `0.061423` |
| `015760` | 한국전력 | `33100.0` |  |  | `market_risk_off` | `dual_buy` | `-48.522551` | `3.4375` | `1.416328` | `0.08347` |
| `010780` | 아이에스동서 | `17020.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-50.087977` | `3.151515` | `1.312342` | `0.075267` |
| `003570` | SNT다이내믹스 | `29000.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.821656` | `2.112676` | `1.239957` | `0.077614` |
| `000490` | 대동 | `5890.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.818182` | `3.333333` | `1.497846` | `0.099839` |
| `005880` | 대한해운 | `1680.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-48.068006` | `1.818182` | `1.313258` | `0.047026` |
| `249420` | 일동제약 | `12150.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.851117` | `3.934987` | `1.467903` | `0.231758` |
| `002710` | TCC스틸 | `7390.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-67.799564` | `3.212291` | `1.426442` | `0.084555` |
| `001120` | LX인터내셔널 | `35200.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-38.994801` | `5.389222` | `0.71024` | `0.218988` |
| `004560` | 현대비앤지스틸 | `9910.0` |  |  | `market_risk_off` | `dual_buy` | `-56.053215` | `1.849949` | `2.592674` | `0.084121` |
| `051910` | LG화학 | `232500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.551724` | `3.794643` | `1.123938` | `0.06277` |
| `000390` | SP삼화 | `5360.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-56.59919` | `1.132075` | `2.371845` | `0.058247` |
| `011500` | 한농화성 | `10080.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-63.806104` | `2.857143` | `2.352113` | `0.126269` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
