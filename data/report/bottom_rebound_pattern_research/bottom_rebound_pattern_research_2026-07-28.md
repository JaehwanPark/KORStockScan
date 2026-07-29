# Bottom Rebound Pattern Research - 2026-07-28

- generated_at: `2026-07-28T21:39:02`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `59180`
- label_rows: `1479500`
- latest_as_of_candidate_count: `220`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.296167`
- backtest_trade_count: `296`
- backtest_total_return_pct: `219.69075`
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
| `signal_close_retest_entry` | `20` | `39357` | `0.665039` | `1.727137` | `1.727137` | `0.483777` | `-17.540856` | `17.184212` |
| `open_guarded_retest_entry` | `20` | `34619` | `0.584978` | `1.453808` | `1.453808` | `0.476848` | `-17.392082` | `16.543392` |
| `next_open_entry` | `20` | `55952` | `0.945455` | `1.962124` | `1.962124` | `0.479804` | `-17.323751` | `17.396716` |
| `close_zone_limit_entry` | `20` | `42882` | `0.724603` | `1.723493` | `1.723493` | `0.481041` | `-17.379497` | `17.003092` |
| `atr_pullback_entry` | `20` | `18528` | `0.313079` | `2.218371` | `2.218371` | `0.507448` | `-17.985841` | `17.93775` |
| `signal_close_retest_entry` | `10` | `40571` | `0.685553` | `0.93905` | `0.93905` | `0.492667` | `-12.895377` | `11.510791` |
| `open_guarded_retest_entry` | `10` | `35266` | `0.595911` | `0.70934` | `0.70934` | `0.48293` | `-12.628129` | `10.841652` |
| `next_open_entry` | `10` | `57496` | `0.971544` | `1.035461` | `1.035461` | `0.490295` | `-12.784091` | `11.554333` |
| `close_zone_limit_entry` | `10` | `44119` | `0.745505` | `0.942701` | `0.942701` | `0.490288` | `-12.755552` | `11.356958` |
| `atr_pullback_entry` | `10` | `19432` | `0.328354` | `1.296167` | `1.296167` | `0.516776` | `-13.627666` | `12.052776` |
| `signal_close_retest_entry` | `5` | `41109` | `0.694643` | `0.345166` | `0.345166` | `0.485003` | `-8.993933` | `7.456392` |
| `open_guarded_retest_entry` | `5` | `35559` | `0.600862` | `0.208802` | `0.208802` | `0.476673` | `-8.771496` | `6.845289` |
| `next_open_entry` | `5` | `58274` | `0.984691` | `0.453338` | `0.453338` | `0.486066` | `-8.879401` | `7.616025` |
| `close_zone_limit_entry` | `5` | `44677` | `0.754934` | `0.367288` | `0.367288` | `0.485015` | `-8.869192` | `7.370381` |
| `atr_pullback_entry` | `5` | `19777` | `0.334184` | `0.374875` | `0.374875` | `0.496284` | `-9.829284` | `7.867162` |
| `signal_close_retest_entry` | `3` | `41328` | `0.698344` | `0.220913` | `0.220913` | `0.4872` | `-6.678057` | `5.386611` |
| `open_guarded_retest_entry` | `3` | `35684` | `0.602974` | `0.045513` | `0.045513` | `0.473966` | `-6.494174` | `4.85228` |
| `next_open_entry` | `3` | `58641` | `0.990892` | `0.239037` | `0.239037` | `0.476544` | `-6.680806` | `5.57554` |
| `close_zone_limit_entry` | `3` | `44908` | `0.758837` | `0.213752` | `0.213752` | `0.486216` | `-6.583054` | `5.333185` |
| `atr_pullback_entry` | `3` | `19916` | `0.336533` | `0.34466` | `0.34466` | `0.499799` | `-7.316121` | `5.75233` |
| `signal_close_retest_entry` | `1` | `41495` | `0.701166` | `-0.014836` | `-0.014836` | `0.472828` | `-3.4` | `2.772479` |
| `open_guarded_retest_entry` | `1` | `35795` | `0.60485` | `-0.157252` | `-0.157252` | `0.448023` | `-3.251225` | `2.419355` |
| `next_open_entry` | `1` | `58960` | `0.996283` | `0.033996` | `0.033996` | `0.456428` | `-3.537008` | `2.841884` |
| `close_zone_limit_entry` | `1` | `45081` | `0.761761` | `-0.012237` | `-0.012237` | `0.47184` | `-3.37002` | `2.724796` |
| `atr_pullback_entry` | `1` | `20052` | `0.338831` | `-0.036376` | `-0.036376` | `0.474466` | `-3.443603` | `3.472682` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `296`
- total_return_pct: `219.69075`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.513514`
- skipped_capacity_count: `18490`
- skipped_same_symbol_count: `646`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `127.792607` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `296` | `219.69075` | `-23.08101` | `0.513514` |
| `exclude_market_risk_off` | `277` | `10.171881` | `-39.853883` | `0.487365` |
| `require_foreign_not_sell` | `296` | `208.184031` | `-23.08101` | `0.510135` |
| `exclude_risk_off_and_foreign_sell` | `277` | `18.289831` | `-35.422052` | `0.498195` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `019170` | 신풍제약 | `7630.0` |  |  | `market_risk_off` | `dual_buy` | `-43.897059` | `1.733333` | `0.823388` | `0.168741` |
| `003280` | 흥아해운 | `1584.0` |  |  | `market_risk_off` | `inst_buy_only` | `-65.788337` | `0.827498` | `0.793304` | `-0.020952` |
| `011210` | 현대위아 | `53300.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.175421` | `2.303263` | `1.061349` | `0.121153` |
| `004090` | 한국석유 | `10250.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-69.471333` | `1.1846` | `1.024035` | `0.005602` |
| `161000` | 애경케미칼 | `8120.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-59.318637` | `0.869565` | `0.894006` | `0.121618` |
| `130660` | 한전산업 | `10000.0` |  |  | `market_risk_off` | `dual_buy` | `-61.685824` | `-0.0` | `0.94595` | `0.102694` |
| `103140` | 풍산 | `60100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-62.248744` | `1.008403` | `1.062142` | `0.123728` |
| `249420` | 일동제약 | `13170.0` |  |  | `market_risk_off` | `dual_buy` | `-67.320099` | `1.152074` | `1.075395` | `0.176908` |
| `000390` | SP삼화 | `5760.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-53.360324` | `0.173913` | `0.916394` | `0.066575` |
| `005250` | 녹십자홀딩스 | `9320.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-46.894587` | `1.304348` | `0.742975` | `0.110543` |
| `008730` | 율촌화학 | `13070.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.085911` | `2.029664` | `0.509358` | `0.116494` |
| `009070` | KCTC | `3705.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-55.840286` | `1.091405` | `1.010471` | `0.130257` |
| `010960` | 삼호개발 | `3010.0` |  |  | `market_risk_off` | `inst_buy_only` | `-42.115385` | `1.176471` | `0.66308` | `-0.00996` |
| `016610` | DB증권 | `8400.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-47.761194` | `1.204819` | `0.993605` | `0.069686` |
| `011500` | 한농화성 | `11140.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-60.0` | `0.905797` | `0.989839` | `0.071135` |
| `200880` | 서연이화 | `10340.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-40.437788` | `1.571709` | `0.716391` | `0.109702` |
| `195870` | 해성디에스 | `46100.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-54.715128` | `0.985761` | `0.7162` | `0.096892` |
| `051910` | LG화학 | `240500.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-45.028571` | `1.691332` | `0.885097` | `0.062458` |
| `077970` | STX엔진 | `21850.0` |  |  | `market_risk_off` | `foreign_buy_only` | `-66.384615` | `1.157407` | `0.908747` | `0.064254` |
| `001060` | JW중외제약 | `23100.0` |  |  | `market_risk_off` | `dual_buy` | `-39.607843` | `1.094092` | `0.815471` | `0.08704` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
