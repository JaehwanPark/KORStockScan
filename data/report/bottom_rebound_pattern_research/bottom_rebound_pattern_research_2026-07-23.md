# Bottom Rebound Pattern Research - 2026-07-23

- generated_at: `2026-07-23T20:53:14`
- decision_authority: `research_only`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- signal_rows: `58820`
- label_rows: `1470500`
- latest_as_of_candidate_count: `79`
- top_primary_entry_policy: `atr_pullback_entry`
- top_primary_source_quality_adjusted_ev_pct: `1.28904`
- backtest_trade_count: `294`
- backtest_total_return_pct: `256.012425`
- backtest_max_drawdown_pct: `-24.136847`
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
| `signal_close_retest_entry` | `20` | `39172` | `0.665964` | `1.781779` | `1.781779` | `0.485576` | `-17.506608` | `17.221946` |
| `open_guarded_retest_entry` | `20` | `34458` | `0.585821` | `1.533092` | `1.533092` | `0.479105` | `-17.308507` | `16.596136` |
| `next_open_entry` | `20` | `55760` | `0.947977` | `1.978369` | `1.978369` | `0.480667` | `-17.317509` | `17.42975` |
| `close_zone_limit_entry` | `20` | `42706` | `0.726046` | `1.764541` | `1.764541` | `0.482508` | `-17.3444` | `17.028739` |
| `atr_pullback_entry` | `20` | `18339` | `0.311782` | `2.3741` | `2.3741` | `0.511751` | `-17.832732` | `18.01341` |
| `signal_close_retest_entry` | `10` | `40294` | `0.685039` | `0.923127` | `0.923127` | `0.492282` | `-12.944619` | `11.443399` |
| `open_guarded_retest_entry` | `10` | `35095` | `0.596651` | `0.734719` | `0.734719` | `0.484513` | `-12.584052` | `10.842496` |
| `next_open_entry` | `10` | `57319` | `0.974481` | `1.017749` | `1.017749` | `0.490012` | `-12.907147` | `11.524164` |
| `close_zone_limit_entry` | `10` | `43851` | `0.745512` | `0.929999` | `0.929999` | `0.489886` | `-12.830413` | `11.306043` |
| `atr_pullback_entry` | `10` | `19269` | `0.327593` | `1.28904` | `1.28904` | `0.516633` | `-13.653823` | `11.855364` |
| `signal_close_retest_entry` | `5` | `40652` | `0.691125` | `0.369783` | `0.369783` | `0.487209` | `-9.006548` | `7.366093` |
| `open_guarded_retest_entry` | `5` | `35260` | `0.599456` | `0.234576` | `0.234576` | `0.478701` | `-8.711809` | `6.83787` |
| `next_open_entry` | `5` | `58096` | `0.987691` | `0.45344` | `0.45344` | `0.487245` | `-8.930873` | `7.590273` |
| `close_zone_limit_entry` | `5` | `44224` | `0.751853` | `0.387204` | `0.387204` | `0.487156` | `-8.877391` | `7.281999` |
| `atr_pullback_entry` | `5` | `19425` | `0.330245` | `0.413025` | `0.413025` | `0.499974` | `-9.836318` | `7.689099` |
| `signal_close_retest_entry` | `3` | `40859` | `0.694645` | `0.137851` | `0.137851` | `0.48474` | `-6.676238` | `5.319149` |
| `open_guarded_retest_entry` | `3` | `35369` | `0.601309` | `0.020891` | `0.020891` | `0.473607` | `-6.435641` | `4.82904` |
| `next_open_entry` | `3` | `58416` | `0.993132` | `0.221692` | `0.221692` | `0.477643` | `-6.666667` | `5.558912` |
| `close_zone_limit_entry` | `3` | `44442` | `0.755559` | `0.137435` | `0.137435` | `0.483889` | `-6.586015` | `5.275523` |
| `atr_pullback_entry` | `3` | `19550` | `0.33237` | `0.15764` | `0.15764` | `0.491816` | `-7.38708` | `5.611655` |
| `signal_close_retest_entry` | `1` | `41044` | `0.69779` | `-0.038698` | `-0.038698` | `0.472615` | `-3.351082` | `2.745395` |
| `open_guarded_retest_entry` | `1` | `35429` | `0.602329` | `-0.158291` | `-0.158291` | `0.449378` | `-3.219803` | `2.397742` |
| `next_open_entry` | `1` | `58741` | `0.998657` | `0.023464` | `0.023464` | `0.455832` | `-3.525046` | `2.820212` |
| `close_zone_limit_entry` | `1` | `44635` | `0.758841` | `-0.033315` | `-0.033315` | `0.472073` | `-3.324431` | `2.698651` |
| `atr_pullback_entry` | `1` | `19686` | `0.334682` | `-0.108608` | `-0.108608` | `0.469369` | `-3.405293` | `3.381061` |

## Portfolio Backtest

- entry_policy: `atr_pullback_entry`
- horizon_days: `10`
- max_positions: `5`
- trade_cost_pct: `0.23`
- trade_count: `294`
- total_return_pct: `256.012425`
- max_drawdown_pct: `-24.136847`
- diagnostic_win_rate: `0.510204`
- skipped_capacity_count: `18335`
- skipped_same_symbol_count: `640`

| year | portfolio_return_pct |
| --- | ---: |
| `2023` | `32.781024` |
| `2024` | `-15.034401` |
| `2025` | `26.736821` |
| `2026` | `153.739278` |

### Backtest Variants

| variant | trades | total_return | max_drawdown | win_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | `294` | `256.012425` | `-24.136847` | `0.510204` |
| `exclude_market_risk_off` | `275` | `1.977717` | `-44.327322` | `0.487273` |
| `require_foreign_not_sell` | `294` | `245.175734` | `-25.698734` | `0.506803` |
| `exclude_risk_off_and_foreign_sell` | `275` | `14.045474` | `-37.739173` | `0.494545` |

## Latest Research-Only Candidates

| code | name | close | sector | themes | regime | flow | drawdown60 | dist_low60 | volume_ratio | foreign20 |
| --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `003540` | 대신증권 | `26200.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.314559` | `5.220884` | `0.704882` | `0.085671` |
| `016610` | DB증권 | `9130.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-44.900422` | `6.28638` | `1.13253` | `0.070534` |
| `019170` | 신풍제약 | `7900.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-45.138889` | `4.497354` | `1.0895` | `0.076467` |
| `128820` | 대성산업 | `4220.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-67.884323` | `6.835443` | `0.71952` | `0.084404` |
| `249420` | 일동제약 | `13920.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-65.459057` | `5.855513` | `0.638343` | `0.146969` |
| `900140` | 엘브이엠씨홀딩스 | `1234.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-31.785517` | `4.222973` | `0.679841` | `0.022898` |
| `030610` | 교보증권 | `9760.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-39.0` | `8.203991` | `0.457331` | `0.10247` |
| `381970` | 케이카 | `7560.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-51.225806` | `5.586592` | `0.658318` | `0.065073` |
| `004990` | 롯데지주 | `23350.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-38.06366` | `7.356322` | `0.736558` | `0.217244` |
| `017800` | 현대엘리베이터 | `70400.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-37.142857` | `6.344411` | `0.525314` | `0.118617` |
| `003530` | 한화투자증권 | `4435.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-52.105832` | `7.907543` | `0.835489` | `0.088674` |
| `000390` | SP삼화 | `6180.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.959514` | `8.231173` | `0.747536` | `0.097447` |
| `034230` | 파라다이스 | `10180.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-53.409611` | `6.932773` | `0.829594` | `0.124573` |
| `037270` | YG PLUS | `3255.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-56.542056` | `6.721311` | `1.048526` | `0.085816` |
| `002220` | 한일철강 | `3430.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-46.98609` | `5.053599` | `1.824574` | `0.043161` |
| `001500` | 현대차증권 | `8100.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-37.013997` | `6.299213` | `0.43991` | `0.086004` |
| `008700` | 아남전자 | `1074.0` |  |  | `market_risk_on` | `inst_buy_only` | `-44.582043` | `4.170708` | `0.715361` | `-0.021948` |
| `010960` | 삼호개발 | `3195.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-41.909091` | `7.035176` | `1.618885` | `0.00437` |
| `001040` | CJ | `133700.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-42.985075` | `6.61882` | `0.954099` | `0.021925` |
| `000490` | 대동 | `6910.0` |  |  | `market_risk_on` | `foreign_buy_only` | `-49.340176` | `9.68254` | `0.457925` | `0.08286` |

## Notes

- This report is research-only and cannot be used as a live BUY/EXIT or runtime apply source.
- Candidate selection uses signal-day and prior data only; labels use later quotes only after the signal.
- Scannerization requires a separate workorder and approval path.
