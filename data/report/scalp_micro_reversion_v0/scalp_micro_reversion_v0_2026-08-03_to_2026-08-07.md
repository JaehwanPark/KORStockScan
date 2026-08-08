# Scalp Micro-Reversion V0 — scalp_micro_reversion_v0_2026-08-03_to_2026-08-07

## 판정

- status: `v0_aggregate_taxable_equity_gate_failed_subcohort_execution_unresolved`
- hypothesis identified: `True`
- gross reversion supported: `True`
- positive EV at selected cost supported: `False`
- aggregate taxable-equity economic gate: `False`
- tax classification complete: `False`
- subcohort opportunity discovery: `open`
- execution economics resolved: `False`
- candidate gate passed: `False`
- applied to sim: `false`
- real runtime reflected: `false`
- actual_order_submitted: `false`
- broker_order_forbidden: `true`

## 근거

- input rows: `2644506`
- deduplicated observations: `469231`
- shock events: `2399`
- fully mature events: `99`
- manual-control event leaks: `0`

### Candidate gates

| gate | actual | threshold | passed |
|---|---:|---:|:---:|
| manual_control_exclusion_leak_count_eq_0 | 0 | 0 | true |
| shock_event_count_gt_0 | 2399 | 1 | true |
| fully_mature_event_count_ge_1000 | 99 | 1000 | false |
| fully_mature_event_coverage_rate_ge_0_90 | 0.04126719466444352 | 0.9 | false |
| legacy_complete_case_cost_adjusted_ev_pct_300s_gt_0 | -0.151012 | 0.0 | false |
| trade_date_count_ge_5 | 5 | 5 | true |
| positive_300s_ev_day_count_ge_3 | 0 | 3 | false |
| max_date_ev_contribution_rate_le_0_25 | 0.462022 | 0.25 | false |
| eligible_positive_parent_count_ge_1 | 0 | 1 | false |
| instrument_tax_classification_complete | False | True | false |
| aggregate_ordinary_taxable_equity_fixed_horizon_ev_gt_0 | False | True | false |

| horizon | resolved/all signals | complete-case adjusted EV pct | all-signal zero-unresolved EV pct | win rate | median MFE bps | median MAE bps |
|---:|---:|---:|---:|---:|---:|---:|
| 15 | 1731/2399 | -0.10809 | -0.077992 | 0.238013 | 14.792899 | 0.0 |
| 30 | 1431/2399 | -0.091375 | -0.054505 | 0.278127 | 22.271715 | 0.0 |
| 60 | 1096/2399 | -0.085499 | -0.039061 | 0.333942 | 32.025641 | 0.0 |
| 120 | 693/2399 | -0.101278 | -0.029256 | 0.34632 | 37.664783 | -14.347202 |
| 180 | 498/2399 | -0.099659 | -0.020688 | 0.323293 | 41.04696 | -16.95634 |
| 300 | 292/2399 | -0.151012 | -0.018381 | 0.390411 | 49.019608 | -23.613047 |
| 600 | 103/2399 | -0.291444 | -0.012513 | 0.330097 | 61.349693 | -45.300113 |

### Statutory sell-tax gate

The aggregate gate assumes an ordinary taxable KOSPI/KOSDAQ equity. It is not event-level tax proof while instrument classification is incomplete.

- ordinary taxable-equity floor bps: `20.0`
- best gross minus statutory floor bps: `-5.549861`
- classified events: `0 / 2399`
- exact sample gate: `blocked_missing_verified_instrument_tax_class`
- raw BBO candidate rows: `1998`
- event-joined BBO context: `0`
- raw micro capture rows: `0`
- raw complete micro-context candidates: `0`
- event-joined micro context: `0`

### Common-maturity horizon comparison

| cohort | common events | horizon | gross EV pct | selected-cost EV pct |
|---|---:|---:|---:|---:|
| through_30s | 1407 | 15 | 0.124355 | -0.105645 |
| through_30s | 1407 | 30 | 0.140714 | -0.089286 |
| through_60s | 1058 | 15 | 0.136885 | -0.093115 |
| through_60s | 1058 | 30 | 0.151889 | -0.078111 |
| through_60s | 1058 | 60 | 0.146896 | -0.083104 |
| through_120s | 666 | 15 | 0.142015 | -0.087985 |
| through_120s | 666 | 30 | 0.148429 | -0.081571 |
| through_120s | 666 | 60 | 0.145338 | -0.084662 |
| through_120s | 666 | 120 | 0.131289 | -0.098711 |
| through_180s | 473 | 15 | 0.14409 | -0.08591 |
| through_180s | 473 | 30 | 0.143539 | -0.086461 |
| through_180s | 473 | 60 | 0.141449 | -0.088551 |
| through_180s | 473 | 120 | 0.132782 | -0.097218 |
| through_180s | 473 | 180 | 0.135904 | -0.094096 |

### All-in cost sensitivity

`0bps` means friction-free, not slippage-only. Cost components are not decomposed.

| horizon | break-even cost bps | EV@0bps pct | EV@5bps pct | EV@10bps pct | EV@15bps pct | EV@20bps pct | EV@23bps pct |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 12.191025 | 0.12191 | 0.07191 | 0.02191 | -0.02809 | -0.07809 | -0.10809 |
| 30 | 13.862546 | 0.138625 | 0.088625 | 0.038625 | -0.011375 | -0.061375 | -0.091375 |
| 60 | 14.450139 | 0.144501 | 0.094501 | 0.044501 | -0.005499 | -0.055499 | -0.085499 |
| 120 | 12.872206 | 0.128722 | 0.078722 | 0.028722 | -0.021278 | -0.071278 | -0.101278 |
| 180 | 13.034053 | 0.130341 | 0.080341 | 0.030341 | -0.019659 | -0.069659 | -0.099659 |
| 300 | 7.898789 | 0.078988 | 0.028988 | -0.021012 | -0.071012 | -0.121012 | -0.151012 |
| 600 | -6.144352 | -0.061444 | -0.111444 | -0.161444 | -0.211444 | -0.261444 | -0.291444 |

## 다음 액션

- Close the V0 walk-forward sample, coverage, and cost-adjusted EV gates.
- Supply verified symbol-level listing-market and instrument-type metadata.
- Accumulate continuous market paths before implementing entry/exit joint replay.
- Keep policy candidates frozen and report resolved, unresolved, and conservative bounds separately.
- Do not connect this report to sim or real order authority.
- Collect forward continuous microstructure before execution-quality review.
