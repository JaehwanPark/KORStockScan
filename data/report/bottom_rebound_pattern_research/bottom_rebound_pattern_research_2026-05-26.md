# Bottom Rebound Pattern Research - 2026-05-26

- generated_at: `2026-05-26T21:26:52`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `56554`
- label_rows: `1413850`
- latest_as_of_candidate_count: `116`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.430219`
- backtest_trade_count: `291`
- backtest_total_return_pct: `37.144523`
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
| `signal_close_retest_entry` | `20` | `38759` | `0.685345` | `1.567127` | `1.567127` | `0.492015` | `-16.878788` | `17.143095` |
| `open_guarded_retest_entry` | `20` | `34254` | `0.605687` | `1.392369` | `1.392369` | `0.483476` | `-16.864777` | `16.517602` |
| `next_open_entry` | `20` | `55248` | `0.976907` | `1.802215` | `1.802215` | `0.488018` | `-16.604684` | `17.306741` |
| `close_zone_limit_entry` | `20` | `42288` | `0.747746` | `1.559281` | `1.559281` | `0.488933` | `-16.767589` | `16.955162` |
| `atr_pullback_entry` | `20` | `18010` | `0.318457` | `2.239306` | `2.239306` | `0.519933` | `-16.853589` | `17.937239` |
| `signal_close_retest_entry` | `10` | `39058` | `0.690632` | `0.997337` | `0.997337` | `0.501997` | `-12.149896` | `11.237561` |
| `open_guarded_retest_entry` | `10` | `34459` | `0.609311` | `0.777193` | `0.777193` | `0.489858` | `-12.087752` | `10.723107` |
| `next_open_entry` | `10` | `55816` | `0.986951` | `1.162041` | `1.162041` | `0.501738` | `-11.940299` | `11.363636` |
| `close_zone_limit_entry` | `10` | `42603` | `0.753315` | `0.988412` | `0.988412` | `0.498955` | `-12.071941` | `11.111111` |
| `atr_pullback_entry` | `10` | `18153` | `0.320985` | `1.430219` | `1.430219` | `0.53297` | `-12.543895` | `11.56185` |
| `signal_close_retest_entry` | `5` | `39256` | `0.694133` | `0.372447` | `0.372447` | `0.490829` | `-8.533366` | `7.145536` |
| `open_guarded_retest_entry` | `5` | `34610` | `0.611981` | `0.236932` | `0.236932` | `0.481393` | `-8.396209` | `6.681463` |
| `next_open_entry` | `5` | `56044` | `0.990982` | `0.537362` | `0.537362` | `0.494486` | `-8.289886` | `7.377557` |
| `close_zone_limit_entry` | `5` | `42808` | `0.75694` | `0.393433` | `0.393433` | `0.490306` | `-8.399153` | `7.076117` |
| `atr_pullback_entry` | `5` | `18308` | `0.323726` | `0.410965` | `0.410965` | `0.504643` | `-9.177067` | `7.332514` |
| `signal_close_retest_entry` | `3` | `39374` | `0.69622` | `0.150993` | `0.150993` | `0.487174` | `-6.337654` | `5.133929` |
| `open_guarded_retest_entry` | `3` | `34680` | `0.613219` | `0.024742` | `0.024742` | `0.475115` | `-6.2478` | `4.736217` |
| `next_open_entry` | `3` | `56213` | `0.99397` | `0.245004` | `0.245004` | `0.480476` | `-6.288125` | `5.378436` |
| `close_zone_limit_entry` | `3` | `42931` | `0.759115` | `0.149655` | `0.149655` | `0.485803` | `-6.271777` | `5.101198` |
| `atr_pullback_entry` | `3` | `18388` | `0.325141` | `0.183647` | `0.183647` | `0.497933` | `-6.84121` | `5.327494` |
| `signal_close_retest_entry` | `1` | `39506` | `0.698554` | `-0.045285` | `-0.045285` | `0.472865` | `-3.225806` | `2.666442` |
| `open_guarded_retest_entry` | `1` | `34743` | `0.614333` | `-0.156738` | `-0.156738` | `0.450307` | `-3.140704` | `2.366183` |
| `next_open_entry` | `1` | `56438` | `0.997949` | `0.023888` | `0.023888` | `0.456731` | `-3.388012` | `2.734769` |
| `close_zone_limit_entry` | `1` | `43070` | `0.761573` | `-0.039765` | `-0.039765` | `0.472254` | `-3.202424` | `2.617499` |
| `atr_pullback_entry` | `1` | `18466` | `0.32652` | `-0.125024` | `-0.125024` | `0.469457` | `-3.211918` | `3.311252` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `291`
- total_return_pct: `37.144523`
- max_drawdown_pct: `-23.08101`
- diagnostic_win_rate: `0.5189`
- skipped_capacity_count: `17236`
- skipped_same_symbol_count: `626`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `-1.775673` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `291` | `37.144523` | `-23.08101` | `0.5189` |
| `exclude_market_risk_off` | `275` | `26.108442` | `-31.153639` | `0.494545` |
| `require_foreign_not_sell` | `291` | `44.215875` | `-23.08101` | `0.522337` |
| `exclude_risk_off_and_foreign_sell` | `275` | `32.936364` | `-27.426073` | `0.501818` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `004090` | 한국석유 | `13370.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-60.178704` | `2.061069` | `0.461453` | `0.023532` |
| `465770` | STX그린로지스 | `3245.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-66.197917` | `0.154321` | `0.486341` | `0.041822` |
| `117580` | 대성에너지 | `7860.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-51.331269` | `1.158301` | `0.613136` | `0.023598` |
| `950210` | 프레스티지바이오파마 | `7500.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.965418` | `4.311544` | `1.252674` | `0.026078` |
| `352820` | 하이브 | `236000.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-41.728395` | `3.508772` | `0.680684` | `-0.115408` |
| `009580` | 무림P&P | `2210.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-50.0` | `0.454545` | `0.701432` | `0.012051` |
| `029780` | 삼성카드 | `47650.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-31.141618` | `0.527426` | `1.043984` | `0.041484` |
| `009240` | 한샘 | `31450.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-40.095238` | `0.801282` | `1.897872` | `0.010685` |
| `007570` | 일양약품 | `9650.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-40.578818` | `0.730689` | `1.068741` | `-0.156645` |
| `381970` | 케이카 | `9760.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-40.812614` | `0.411523` | `0.912172` | `-0.159059` |
| `009070` | KCTC | `5200.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-38.021454` | `0.970874` | `0.824843` | `0.045928` |
| `037270` | YG PLUS | `4110.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-45.992116` | `1.231527` | `1.2431` | `-0.074003` |
| `000120` | CJ대한통운 | `89000.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-38.108484` | `2.890173` | `0.989495` | `0.023408` |
| `013360` | 일성건설 | `1524.0` |  |  | `market_risk_on` | `inst_buy_only` | `-39.881657` | `2.281879` | `0.655377` | `-0.002339` |
| `003520` | 영진약품 | `1436.0` |  |  | `market_risk_on` | `inst_buy_only` | `-38.103448` | `0.630694` | `0.977168` | `-0.10837` |
| `103140` | 풍산 | `87900.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-44.786432` | `4.023669` | `0.668813` | `-0.002047` |
| `005870` | 휴니드 | `6870.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-34.446565` | `1.029412` | `0.544936` | `0.018185` |
| `105630` | 한세실업 | `9270.0` |  |  | `market_risk_on` | `dual_sell_or_flat` | `-40.34749` | `0.980392` | `1.745364` | `-0.047644` |
| `128820` | 대성산업 | `6300.0` |  |  | `market_risk_on` | `inst_buy_only` | `-52.054795` | `3.960396` | `1.428049` | `-0.016409` |
| `002140` | 고려산업 | `2330.0` |  |  | `market_risk_on` | `dual_buy` | `-29.819277` | `1.304348` | `0.510328` | `0.004118` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
