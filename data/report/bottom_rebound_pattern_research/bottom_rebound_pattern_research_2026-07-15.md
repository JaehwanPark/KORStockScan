# Bottom Rebound Pattern Research - 2026-07-15

- generated_at: `2026-07-15T20:53:26`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58484`
- label_rows: `1462100`
- latest_as_of_candidate_count: `159`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.329429`
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
| `signal_close_retest_entry` | `20` | `39035` | `0.667448` | `1.768428` | `1.768428` | `0.486973` | `-17.369813` | `17.170936` |
| `open_guarded_retest_entry` | `20` | `34394` | `0.588092` | `1.533089` | `1.533089` | `0.479619` | `-17.265257` | `16.551194` |
| `next_open_entry` | `20` | `55488` | `0.948772` | `2.029549` | `2.029549` | `0.482861` | `-17.091482` | `17.370259` |
| `close_zone_limit_entry` | `20` | `42565` | `0.727806` | `1.762386` | `1.762386` | `0.483872` | `-17.195481` | `16.992791` |
| `atr_pullback_entry` | `20` | `18255` | `0.312137` | `2.383865` | `2.383865` | `0.51427` | `-17.661034` | `17.969618` |
| `signal_close_retest_entry` | `10` | `39999` | `0.683931` | `0.927882` | `0.927882` | `0.493087` | `-12.833189` | `11.392741` |
| `open_guarded_retest_entry` | `10` | `34973` | `0.597993` | `0.71364` | `0.71364` | `0.48303` | `-12.586411` | `10.786337` |
| `next_open_entry` | `10` | `56786` | `0.970966` | `1.032767` | `1.032767` | `0.491248` | `-12.720602` | `11.461318` |
| `close_zone_limit_entry` | `10` | `43545` | `0.744563` | `0.932354` | `0.932354` | `0.490619` | `-12.695106` | `11.250039` |
| `atr_pullback_entry` | `10` | `19026` | `0.32532` | `1.329429` | `1.329429` | `0.518554` | `-13.506075` | `11.853471` |
| `signal_close_retest_entry` | `5` | `40722` | `0.696293` | `0.378453` | `0.378453` | `0.487697` | `-8.940338` | `7.420334` |
| `open_guarded_retest_entry` | `5` | `35354` | `0.604507` | `0.234066` | `0.234066` | `0.478673` | `-8.746258` | `6.829184` |
| `next_open_entry` | `5` | `57664` | `0.985979` | `0.490898` | `0.490898` | `0.489283` | `-8.785942` | `7.59173` |
| `close_zone_limit_entry` | `5` | `44282` | `0.757164` | `0.398664` | `0.398664` | `0.487715` | `-8.805613` | `7.323712` |
| `atr_pullback_entry` | `5` | `19544` | `0.334177` | `0.420595` | `0.420595` | `0.499488` | `-9.765003` | `7.793576` |
| `signal_close_retest_entry` | `3` | `40984` | `0.700773` | `0.233572` | `0.233572` | `0.488654` | `-6.649904` | `5.346617` |
| `open_guarded_retest_entry` | `3` | `35521` | `0.607363` | `0.048734` | `0.048734` | `0.474311` | `-6.487324` | `4.834517` |
| `next_open_entry` | `3` | `57944` | `0.990767` | `0.273675` | `0.273675` | `0.479273` | `-6.611397` | `5.532702` |
| `close_zone_limit_entry` | `3` | `44547` | `0.761696` | `0.226411` | `0.226411` | `0.487665` | `-6.55214` | `5.297415` |
| `atr_pullback_entry` | `3` | `19755` | `0.337785` | `0.353337` | `0.353337` | `0.500127` | `-7.319073` | `5.71109` |
| `signal_close_retest_entry` | `1` | `41167` | `0.703902` | `0.008094` | `0.008094` | `0.475988` | `-3.351054` | `2.769336` |
| `open_guarded_retest_entry` | `1` | `35598` | `0.608679` | `-0.142191` | `-0.142191` | `0.450615` | `-3.219803` | `2.418818` |
| `next_open_entry` | `1` | `58325` | `0.997281` | `0.057324` | `0.057324` | `0.459477` | `-3.493976` | `2.834319` |
| `close_zone_limit_entry` | `1` | `44746` | `0.765098` | `0.009633` | `0.009633` | `0.474925` | `-3.323263` | `2.721088` |
| `atr_pullback_entry` | `1` | `19820` | `0.338896` | `-0.005789` | `-0.005789` | `0.478607` | `-3.384146` | `3.472494` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `293`
- total_return_pct: `217.391441`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.505119`
- skipped_capacity_count: `18091`
- skipped_same_symbol_count: `642`

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
| `950210` | 프레스티지바이오파마 | `5370.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-60.917031` | `3.667954` | `0.756883` | `0.125224` |
| `011210` | 현대위아 | `58700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.823588` | `1.733102` | `0.546357` | `0.1149` |
| `013580` | 계룡건설 | `19140.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.522523` | `4.305177` | `0.823073` | `0.003006` |
| `003540` | 대신증권 | `26250.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.208289` | `1.941748` | `0.69674` | `0.08533` |
| `008730` | 율촌화학 | `13730.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-52.817869` | `2.081784` | `0.679217` | `0.09078` |
| `052690` | 한전기술 | `95000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-52.020202` | `1.387407` | `0.695974` | `0.027032` |
| `381970` | 케이카 | `7570.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-51.629393` | `0.264901` | `0.743622` | `-0.008848` |
| `103140` | 풍산 | `62400.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-60.80402` | `4.0` | `0.62496` | `0.163305` |
| `001040` | CJ | `134500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.266376` | `2.281369` | `1.375973` | `0.035366` |
| `003090` | 대웅 | `16670.0` |  |  | `market_risk_on` | `dual_buy` | `-43.105802` | `4.77687` | `0.813537` | `0.018309` |
| `439260` | 대한조선 | `45600.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.94051` | `1.55902` | `0.69582` | `0.020157` |
| `034020` | 두산에너빌리티 | `73000.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.845697` | `1.955307` | `0.835074` | `-0.039468` |
| `011170` | 롯데케미칼 | `60700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-48.948696` | `3.760684` | `0.665424` | `0.033447` |
| `005250` | 녹십자홀딩스 | `9730.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.558405` | `1.991614` | `0.548659` | `0.03748` |
| `249420` | 일동제약 | `14390.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-67.258248` | `4.124457` | `0.821425` | `0.24149` |
| `006280` | 녹십자 | `121500.0` |  |  | `market_risk_on` | `dual_buy` | `-31.970885` | `3.404255` | `0.955337` | `0.085732` |
| `100090` | SK오션플랜트 | `13340.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-57.78481` | `2.300613` | `0.992202` | `0.024404` |
| `123690` | 한국화장품 | `6210.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.286344` | `5.076142` | `0.945259` | `0.122113` |
| `012450` | 한화에어로스페이스 | `929000.0` |  |  | `market_risk_on` | `dual_buy` | `-43.867069` | `3.337041` | `1.077046` | `0.012184` |
| `302440` | SK바이오사이언스 | `35200.0` |  |  | `market_risk_on` | `dual_buy` | `-32.56705` | `0.42796` | `0.606335` | `0.068574` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
