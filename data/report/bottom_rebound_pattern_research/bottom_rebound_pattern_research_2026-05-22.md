# Bottom Rebound Pattern Research - 2026-05-22

- generated_at: `2026-05-24T15:50:28`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `54925`
- label_rows: `1373125`
- latest_as_of_candidate_count: `76`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.355032`
- backtest_trade_count: `278`
- backtest_total_return_pct: `71.054638`
- backtest_max_drawdown_pct: `-23.08101`
- kiwoom_enrichment_enabled: `True`
- kiwoom_enrichment_mapped: `20` / `20`
- warnings: `['kiwoom:sector_theme_missing']`

## Contract

- metric_role: `primary_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- sample_floor: `30`
- forbidden_uses: `['runtime_env_apply', 'broker_order_submit', 'provider_route_change', 'bot_restart_trigger', 'threshold_mutation', 'real_order_conversion_evidence', 'standalone_buy_or_exit_decision']`

## Entry Policy Comparison

| entry_policy | horizon | sample | fill_rate | ev | adjusted_ev | win_rate | mae_p10 | mfe_p80 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `signal_close_retest_entry` | `20` | `37921` | `0.690414` | `1.664926` | `1.664926` | `0.491865` | `-16.880382` | `17.073171` |
| `open_guarded_retest_entry` | `20` | `33549` | `0.610815` | `1.476459` | `1.476459` | `0.483591` | `-16.82279` | `16.456247` |
| `next_open_entry` | `20` | `53688` | `0.977478` | `1.998768` | `1.998768` | `0.487241` | `-16.627458` | `17.253791` |
| `close_zone_limit_entry` | `20` | `41398` | `0.753719` | `1.675269` | `1.675269` | `0.488526` | `-16.764946` | `16.864175` |
| `atr_pullback_entry` | `20` | `17521` | `0.318999` | `2.430449` | `2.430449` | `0.521945` | `-16.880721` | `17.870722` |
| `signal_close_retest_entry` | `10` | `38228` | `0.696004` | `0.940751` | `0.940751` | `0.499895` | `-12.130894` | `11.188537` |
| `open_guarded_retest_entry` | `10` | `33725` | `0.614019` | `0.715836` | `0.715836` | `0.488065` | `-12.048364` | `10.669646` |
| `next_open_entry` | `10` | `54287` | `0.988384` | `1.123811` | `1.123811` | `0.499512` | `-11.950074` | `11.3167` |
| `close_zone_limit_entry` | `10` | `41735` | `0.759854` | `0.940984` | `0.940984` | `0.496969` | `-12.036249` | `11.081657` |
| `atr_pullback_entry` | `10` | `17671` | `0.32173` | `1.355032` | `1.355032` | `0.530021` | `-12.55944` | `11.482181` |
| `signal_close_retest_entry` | `5` | `38385` | `0.698862` | `0.35513` | `0.35513` | `0.489957` | `-8.481376` | `7.107583` |
| `open_guarded_retest_entry` | `5` | `33858` | `0.616441` | `0.211574` | `0.211574` | `0.48033` | `-8.35004` | `6.655553` |
| `next_open_entry` | `5` | `54479` | `0.99188` | `0.522653` | `0.522653` | `0.49353` | `-8.278146` | `7.338847` |
| `close_zone_limit_entry` | `5` | `41895` | `0.762767` | `0.383428` | `0.383428` | `0.490106` | `-8.357785` | `7.05018` |
| `atr_pullback_entry` | `5` | `17781` | `0.323732` | `0.365614` | `0.365614` | `0.501603` | `-9.123046` | `7.247749` |
| `signal_close_retest_entry` | `3` | `38502` | `0.700992` | `0.146838` | `0.146838` | `0.487014` | `-6.2936` | `5.115713` |
| `open_guarded_retest_entry` | `3` | `33932` | `0.617788` | `0.016108` | `0.016108` | `0.474773` | `-6.205088` | `4.723248` |
| `next_open_entry` | `3` | `54613` | `0.99432` | `0.244326` | `0.244326` | `0.481039` | `-6.24261` | `5.34433` |
| `close_zone_limit_entry` | `3` | `42014` | `0.764934` | `0.148063` | `0.148063` | `0.486338` | `-6.219191` | `5.085722` |
| `atr_pullback_entry` | `3` | `17869` | `0.325335` | `0.151622` | `0.151622` | `0.4946` | `-6.780136` | `5.286634` |
| `signal_close_retest_entry` | `1` | `38622` | `0.703177` | `-0.037108` | `-0.037108` | `0.47315` | `-3.232291` | `2.65226` |
| `open_guarded_retest_entry` | `1` | `34020` | `0.61939` | `-0.149488` | `-0.149488` | `0.450441` | `-3.14193` | `2.36023` |
| `next_open_entry` | `1` | `54849` | `0.998616` | `0.031991` | `0.031991` | `0.458076` | `-3.37992` | `2.722772` |
| `close_zone_limit_entry` | `1` | `42140` | `0.767228` | `-0.031538` | `-0.031538` | `0.472544` | `-3.204005` | `2.605578` |
| `atr_pullback_entry` | `1` | `17970` | `0.327173` | `-0.110375` | `-0.110375` | `0.469171` | `-3.209634` | `3.305812` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `278`
- total_return_pct: `71.054638`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.528777`
- skipped_capacity_count: `16803`
- skipped_same_symbol_count: `590`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `22.155389` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `278` | `71.054638` | `-23.08101` | `0.528777` |
| `exclude_market_risk_off` | `262` | `60.553483` | `-24.651169` | `0.51145` |
| `require_foreign_not_sell` | `278` | `61.561484` | `-23.08101` | `0.528777` |
| `exclude_risk_off_and_foreign_sell` | `262` | `75.374658` | `-23.78546` | `0.519084` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `037270` | YG PLUS | `4255.0` | Data Processing, Hosting and Related activities; Web Portals |  | `market_risk_on` | `foreign_buy_only` | `-44.086728` | `3.780488` | `1.34618` | `0.118344` |
| `381970` | 케이카 | `9940.0` | Sale of Motor Vehicles |  | `market_risk_on` | `foreign_buy_only` | `-41.426046` | `2.053388` | `0.707107` | `0.016601` |
| `029780` | 삼성카드 | `48200.0` | Other Financial Intermediation |  | `market_risk_on` | `foreign_buy_only` | `-20.853859` | `1.15425` | `0.829893` | `0.129729` |
| `105630` | 한세실업 | `9450.0` | Manufacture of Sewn Wearing Apparel, Except Fur Apparel | 의복_OEM | `market_risk_on` | `dual_sell_or_flat` | `-39.189189` | `3.846154` | `1.637923` | `-0.045787` |
| `009580` | 무림P&P | `2220.0` | Manufacture of Pulp, Paper and Paperboard |  | `market_risk_on` | `dual_sell_or_flat` | `-46.698679` | `0.225734` | `1.816142` | `-0.015503` |
| `034230` | 파라다이스 | `14700.0` | Amusement and theme Park Operation | 카지노 | `market_risk_on` | `foreign_buy_only` | `-32.723112` | `5.376344` | `0.827755` | `0.002529` |
| `300720` | 한일시멘트 | `15250.0` | Manufacture of Cement, Lime and Plaster and Its Products |  | `market_risk_on` | `dual_sell_or_flat` | `-26.506024` | `2.006689` | `0.865043` | `-0.052261` |
| `003520` | 영진약품 | `1472.0` | Manufacture of Medicaments |  | `market_risk_on` | `foreign_buy_only` | `-33.24263` | `2.865129` | `0.866185` | `0.004779` |
| `009240` | 한샘 | `32900.0` | Wholesale of Household Goods | 가구 | `market_risk_on` | `foreign_buy_only` | `-33.535354` | `5.787781` | `1.643881` | `0.100774` |
| `000120` | CJ대한통운 | `89600.0` | Road Freight Transport | 운송_육상운송 | `market_risk_on` | `foreign_buy_only` | `-36.453901` | `6.035503` | `0.987252` | `0.046366` |
| `007570` | 일양약품 | `9830.0` | Manufacture of Medicaments |  | `market_risk_on` | `dual_sell_or_flat` | `-32.671233` | `3.039832` | `0.656894` | `-0.028893` |
| `030000` | 제일기획 | `19030.0` | Advertising | 미디어_방송광고 | `market_risk_on` | `dual_sell_or_flat` | `-18.32618` | `2.311828` | `0.926878` | `-0.196567` |
| `035720` | 카카오 | `41850.0` | Data Processing, Hosting and Related activities; Web Portals | SNS(Social Network Service), 게임_모바일 | `market_risk_on` | `dual_sell_or_flat` | `-34.813084` | `5.150754` | `0.975634` | `-0.016758` |
| `183190` | 아세아시멘트 | `10320.0` | Manufacture of Cement, Lime and Plaster and Its Products |  | `market_risk_on` | `dual_sell_or_flat` | `-27.170078` | `1.976285` | `0.447948` | `-0.131088` |
| `009270` | 신원 | `1179.0` | Manufacture of Sewn Wearing Apparel, Except Fur Apparel | 의복_OEM | `market_risk_on` | `foreign_buy_only` | `-28.415301` | `4.336283` | `0.996325` | `0.010725` |
| `352820` | 하이브 | `235000.0` | Audio Publishing and Original Master Recordings |  | `market_risk_on` | `dual_sell_or_flat` | `-38.802083` | `5.855856` | `0.505647` | `-0.121841` |
| `008730` | 율촌화학 | `21750.0` | Manufacture of Plastic Products |  | `market_risk_on` | `foreign_buy_only` | `-33.990895` | `7.407407` | `0.785429` | `0.069304` |
| `005870` | 휴니드 | `7050.0` | Manufacture of Telecommunication and Broadcasting Apparatuses |  | `market_risk_on` | `dual_sell_or_flat` | `-40.506329` | `5.067064` | `0.455311` | `-0.012812` |
| `006220` | 제주은행 | `10960.0` | Banking and Savings Institutions | 은행 | `market_risk_on` | `foreign_buy_only` | `-37.478608` | `4.281637` | `1.07166` | `0.008871` |
| `012750` | 에스원 | `70700.0` | Security, Guard and Detective Services |  | `market_risk_on` | `dual_sell_or_flat` | `-31.359223` | `2.761628` | `1.153298` | `-0.070875` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
