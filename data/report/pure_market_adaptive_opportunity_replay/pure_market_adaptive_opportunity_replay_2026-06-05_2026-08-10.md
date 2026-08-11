# Pure-market adaptive opportunity replay — 2026-06-05 to 2026-08-10

## Decision

- decision: `insufficient_wait_budget_history`
- qualified trading dates: `46` / required `46`
- round-trip cost: `0.2%`
- fixed drawdown/rebound opportunity labels: `none`
- runtime_effect: `false`

## Opportunity upper bound and causal walk-forward

| Venue | Oracle trades | Oracle avg/day | Oracle daily compounded | OOS dates | OOS trades | OOS net EV | Win rate | Buy AP lift | Sell AP lift | Source |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 1984 | 43.130435 | 23.675213 | 26 | 388 | -0.180963 | 38.402 | 2.471951 | 2.773464 | PASS |
| NXT | 2970 | 64.565217 | 34.255124 | 26 | 580 | -0.201704 | 38.448 | 2.681078 | 3.006767 | PARTIAL_CONTEXT |

## Nested pairability walk-forward

| Venue | Pairability OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Win rate | Weak-reversal EV | Bullish-transition EV | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 18 | 276 | -0.183845 | 151 | -0.165089 | 0.018756 | 42.384 | -0.170575 | -0.144688 | pairability_detected_execution_negative |
| NXT | 18 | 409 | -0.193714 | 155 | -0.197875 | -0.004161 | 47.097 | -0.197099 | -0.200031 | source_quality_blocked |

Pairability uses only candidate episodes from earlier base-model OOS dates. The current date's exit reason and profit are evaluation outcomes only; they do not select the model, selection fraction, or probability cutoff.

## Lane competing-risk direct-EV walk-forward

| Venue | OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Win rate | Weak-reversal EV | Bullish-transition EV | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 18 | 356 | -0.206315 | 80 | -0.205076 | 0.001239 | 43.75 | -0.169575 | -0.319053 | lane_ev_improved_but_negative |
| NXT | 18 | 538 | -0.21419 | 55 | -0.202319 | 0.011871 | 41.818 | -0.208615 | -0.191299 | source_quality_blocked |

This layer removes the common duration cap. Each lane predicts the first causal sell transition, adverse buy transition, or session-end censor and selects only candidates with prior-only predicted cost-adjusted EV above zero.

## Economic first-passage direct-EV walk-forward

| Venue | OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Compounded net | Avg MFE | Avg MAE | Full-session MFE >=0.5 | Adverse-first then target | Median duration | Weak-reversal EV | Bullish-transition EV | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 18 | 263 | -0.267165 | 78 | -0.251125 | 0.01604 | -18.012967 | 0.366817 | -0.450782 | 60 | 24 | 8.5 | -0.285194 | -0.152328 | economic_first_passage_improved_but_negative |
| NXT | 18 | 372 | -0.252212 | 94 | -0.235212 | 0.017 | -20.075681 | 0.381424 | -0.411824 | 67 | 23 | 8.0 | -0.192751 | -0.317481 | source_quality_blocked |

Favorable boundaries are round-trip cost plus a candidate's causal volatility scale; adverse boundaries use that same scale. Lane-specific multipliers are selected only on an earlier chronological validation suffix. Current-date paths are evaluation outcomes, never entry features or boundary-selection inputs.

## Recovery-aware exit and favorable trailing walk-forward

| Venue | OOS dates | Same-entry baseline trades | Baseline EV | Recovery trades | Recovery EV | EV delta | Compounded net | Deferred adverse exits | Recovered to favorable | Trailing exits | MFE capture | Weak-reversal EV | Bullish-transition EV | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 18 | 76 | -0.21752 | 76 | -0.221691 | -0.004171 | -15.712723 | 18 | 2 | 9 | 20.629 | -0.274604 | -0.051191 | no_incremental_predictive_value |
| NXT | 18 | 94 | -0.235212 | 94 | -0.23999 | -0.004778 | -20.46587 | 24 | 2 | 1 | 26.663 | -0.165199 | -0.384899 | source_quality_blocked |

The baseline and recovery rows use the exact same prior-only selected entry timestamps. Adverse exits are deferred only when the prior lane model predicts positive incremental EV; recovery probability and time are diagnostics. Favorable trailing and recovery bounds are selected only from earlier dates.

## Recovery and favorable-trailing axis separation

| Venue | OOS dates | Same-entry trades | Baseline EV | Recovery-only EV | Recovery delta | Trailing-only EV | Trailing delta | Combined EV | Combined delta | Recovery-only MAE | Trailing applied | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 18 | 76 | -0.21752 | -0.193819 | 0.023701 | -0.236889 | -0.019368 | -0.221691 | -0.00417 | -0.47991 | 8 | axis_separation_improved_but_negative |
| NXT | 18 | 94 | -0.235212 | -0.235557 | -0.000345 | -0.235212 | 0.0 | -0.23999 | -0.004778 | -0.466726 | 0 | source_quality_blocked |

All four arms preserve the exact economic-selected entry timestamps. Recovery labels use immediate favorable exits and contain no trailing outcome. Trailing is decided by a separate prior-only favorable-checkpoint incremental-EV model; a positive external OOS result is never reused as a same-report lane switch.

## Recovery-only outcome direct entry utility

| Venue | OOS dates | Eligible candidates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Control compounded | Selected compounded | Selected MAE | Prior OOS labels | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| KRX | 10 | 184 | 33 | -0.283379 | 50 | -0.304573 | -0.021194 | -9.057505 | -14.417204 | -0.468294 | 350 | no_incremental_predictive_value |
| NXT | 10 | 321 | 38 | -0.229463 | 63 | -0.331497 | -0.102034 | -8.537133 | -19.056933 | -0.579506 | 538 | source_quality_blocked |

The control keeps the existing economic entry selector while both selectors share each date's prior-only recovery-only exit policy. The new lane model is fitted only on recovery outcomes that were already evaluated out of sample on earlier dates. Current-date outcomes, trailing results, and full-session MFE/MAE cannot enter its features or selection rule.

## Prior-only recovery-entry calibration and capacity

| Venue | OOS dates | Eligible | Control n/EV | Raw n/EV | Calibrated n/EV | Cal EV delta vs raw | Control/Raw/Cal compounded | Control/Raw/Cal MAE | Cal mean+/final | Retention | Decision |
| --- | ---: | ---: | --- | --- | --- | ---: | --- | --- | --- | ---: | --- |
| KRX | 6 | 104 | 14/-0.210308 | 21/-0.292606 | 21/-0.292606 | 0.0 | -2.954557/-6.021327/-6.021327 | -0.528282/-0.54325/-0.54325 | 0/21 | 1.0 | no_incremental_predictive_value |
| NXT | 6 | 178 | 11/-0.32676 | 24/-0.249621 | 24/-0.249621 | 0.0 | -3.570574/-5.856936/-5.856936 | -0.414848/-0.516073/-0.516073 | 0/24 | 1.0 | source_quality_blocked |

Lane calibrators use only earlier OOS recovery-entry prediction residuals. Reliability-shrunk mean EV, not a positive lower confidence bound, owns selection. Prediction bins, date drift, and capacity losses are post-OOS diagnostics only and cannot change a lane or threshold in the same report.

## Recovery-entry causal timing nested OOS

| Venue | OOS dates | Raw n/EV | Timing n/EV | EV delta | Raw/Timing compounded | Raw/Timing MAE | Retention | Fallback dates | Missed entries | Decision |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| KRX | 6 | 18/-0.244312 | 18/-0.094412 | 0.1499 | -4.360088/-1.753384 | -0.569936/-0.534256 | 1.0 | 2 | 9 | entry_timing_pareto_improved |
| NXT | 6 | 20/-0.186469 | 19/-0.180315 | 0.006154 | -3.691843/-3.398741 | -0.504395/-0.437816 | 0.95 | 3 | 9 | source_quality_blocked |

Each arm is triggered from completed bars and entered at the next open. The arm and maximum wait are selected only from earlier OOS arm outcomes. Current-date outcomes cannot select the current-date timing, all arms retain the recovery-only exit owner, and date-level fallback enforces the 75% raw-opportunity floor.

| Venue | Arm | OOS trades | Net EV | Compounded | MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| KRX | confirmation_continuation | 18 | -0.094412 | -1.753384 | -0.534256 |
| KRX | first_non_chasing_pullback | 18 | -0.244312 | -4.360088 | -0.569936 |
| KRX | vwap_reclaim_hold | 18 | -0.244312 | -4.360088 | -0.569936 |
| NXT | confirmation_continuation | 19 | -0.180315 | -3.398741 | -0.437816 |
| NXT | first_non_chasing_pullback | 20 | -0.186469 | -3.691843 | -0.493957 |
| NXT | vwap_reclaim_hold | 20 | -0.186425 | -3.691005 | -0.473036 |

## Candidate timing incremental utility nested OOS

| Venue | OOS dates | Control n/EV | Selected n/EV | EV delta | Control/Selected compounded | Control/Selected MAE | Retention | Enter now | Wait | Trigger enter | Decision |
| --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| KRX | 2 | 6/-0.307658 | 5/-0.45852 | -0.150862 | -1.838699/-2.275189 | -0.360498/-0.389401 | 0.833333 | 5 | 1 | 0 | no_incremental_predictive_value |
| NXT | 2 | 2/0.279133 | 2/0.279133 | 0.0 | 0.558796/0.558796 | -0.853804/-0.853804 | 1.0 | 2 | 0 | 0 | source_quality_blocked |

The baseline decision uses only features available at the original recovery-entry candidate. A wait decision may use completed-bar trigger features only after that trigger exists, and then chooses timed entry or no trade. There is no retroactive next-open fallback. A causal three-enter-now to one-wait exploration budget preserves at least 75% opportunity capacity before the final cross-lane retention gate.

## Trigger utility calibration and bounded exploration

| Venue | OOS dates | Control n/EV | Raw gate n/EV | Calibrated n/EV | Calibrated delta vs raw | Control/Raw/Calibrated compounded | Control/Raw/Calibrated MAE | Opportunity retention | Trigger entry retention | Forced trigger entries | Decision |
| --- | ---: | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| KRX | 1 | 3/-0.128383 | 2/-0.415901 | 3/-0.128383 | 0.287518 | -0.387128/-0.830072/-0.387128 | -0.216334/-0.216509/-0.144339 | 1.0 | 1.0 | 1 | calibrated_trigger_utility_pareto_improved |
| NXT | 1 | 0/None | 0/None | 0/None | None | 0.0/0.0/0.0 | None/None/None | None | None | 0 | source_quality_blocked |

Trigger calibration consumes only earlier OOS raw predictions and realized recovery-only outcomes. The affine rank slope, residual intercept, and recent-date drift are shrunk toward the raw forecast. Three observed trigger entries earn at most one model skip, so a nonpositive calibrated forecast cannot eliminate the initial trigger sample. Realized outcomes remain post-OOS diagnostics and cannot update the same-date calibration.

## Candidate timing wait-budget arm comparison

| Venue | Arm OOS dates | 3:1 n/EV | 2:1 n/EV | 1:1 n/EV | 3:1/2:1/1:1 compounded | 3:1/2:1/1:1 MAE | Trigger retention 3:1/2:1/1:1 | Prior-selected OOS dates | Decision |
| --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| KRX | 1 | 3/-0.128383 | 3/-0.092497 | 3/-0.092497 | -0.387128/-0.279438/-0.279438 | -0.144339/-0.180414/-0.180414 | 1.0/1.0/1.0 | 0 | insufficient_wait_budget_history |
| NXT | 1 | 0/None | 0/None | 0/None | 0.0/0.0/0.0 | None/None/None | None/None/None | 0 | source_quality_blocked |

All three arms share the same prior-only trigger calibration, bounded trigger exploration, and recovery-only exit owner. The current evaluation date contributes arm outcomes only after all arm decisions are complete. A prior-selected executable arm is absent until at least one earlier complete arm-comparison date exists; same-date best-arm selection is forbidden.

## Opportunity-density cost sensitivity

| Venue | Round-trip cost | Oracle trades | Oracle avg/day | Oracle avg net/trade |
| --- | ---: | ---: | ---: | ---: |
| KRX | 0.2 | 1984 | 43.130435 | 0.485229 |
| KRX | 0.4 | 1059 | 23.021739 | 0.637183 |
| KRX | 0.6 | 636 | 13.826087 | 0.801926 |
| KRX | 1.0 | 288 | 6.26087 | 1.184305 |
| NXT | 0.2 | 2970 | 64.565217 | 0.442679 |
| NXT | 0.4 | 1479 | 32.152174 | 0.616148 |
| NXT | 0.6 | 858 | 18.652174 | 0.798348 |
| NXT | 1.0 | 394 | 8.565217 | 1.139625 |

This sensitivity table is still perfect-foresight evidence. Its purpose is only to test whether cost-bearing price movement exists after progressively larger execution-cost assumptions.

## Two-sided transition completion diagnostic

| Venue | Buy then sell transition completed | Completed-pair net EV | Completed-pair win rate | Prior-duration expiry exits |
| --- | ---: | ---: | ---: | ---: |
| KRX | 152 | 0.155613 | 68.421 | 235 |
| NXT | 324 | 0.05659 | 58.951 | 245 |

The oracle is an unattainable ex-post ceiling, not a strategy result. Average precision must be compared with oracle-action prevalence; OOS net EV is the executable next-open diagnostic. Future prices never enter classifier features or same-day training.
A completed two-sided pair is known only after its sell transition occurs. Its positive diagnostic EV cannot be used at entry. The nested pairability section tests a prior-only predictor and must retain its reported negative result when it fails to make execution EV positive.
