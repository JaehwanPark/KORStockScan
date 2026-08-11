# Pure-market adaptive opportunity replay — 2026-06-05 to 2026-08-10

## Decision

- decision: `no_new_catastrophic_episode_observe`
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

## Fixed-entry split-buy and fixed-take-profit causal replay

| Venue | Arm | Trades | Planned-budget EV | Deployed EV | Compounded | Budget MAE | Avg deployed | Avg legs | Basis improvement | TP/Disaster/Close | TP below first entry |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| KRX | single_tp0p5 | 78 | -0.244535 | -0.244535 | -17.786214 | -0.839346 | 1.0 | 1.0 | 0.0 | 56/17/5 | 0 |
| KRX | two_40_60_add0p5_tp0p4 | 78 | -0.188961 | -0.08715 | -13.92758 | -0.505971 | 0.653846 | 1.423077 | 0.155007 | 63/13/2 | 0 |
| KRX | two_40_60_add0p5_tp0p5 | 78 | -0.202942 | -0.075089 | -14.898389 | -0.553075 | 0.684615 | 1.474359 | 0.174579 | 60/15/3 | 0 |
| KRX | two_40_60_add0p8_tp0p5 | 78 | -0.148918 | 0.007613 | -11.155254 | -0.483053 | 0.576923 | 1.294872 | 0.163776 | 61/13/4 | 0 |
| KRX | three_20_30_50_add0p4_0p8_tp0p5 | 78 | -0.183321 | 0.00457 | -13.506277 | -0.430202 | 0.514103 | 1.858974 | 0.257372 | 61/14/3 | 1 |
| KRX | three_20_30_50_add0p5_1p0_tp0p5 | 78 | -0.157403 | 0.049386 | -11.699645 | -0.382521 | 0.470513 | 1.730769 | 0.270262 | 62/13/3 | 6 |
| NXT | single_tp0p5 | 94 | -0.085584 | -0.085584 | -8.139325 | -0.707967 | 1.0 | 1.0 | 0.0 | 69/13/12 | 0 |
| NXT | two_40_60_add0p5_tp0p4 | 94 | -0.096365 | -0.005292 | -8.860512 | -0.405944 | 0.629787 | 1.382979 | 0.142666 | 76/10/8 | 0 |
| NXT | two_40_60_add0p5_tp0p5 | 94 | -0.041761 | 0.084028 | -4.071934 | -0.437712 | 0.655319 | 1.425532 | 0.159055 | 75/10/9 | 0 |
| NXT | two_40_60_add0p8_tp0p5 | 94 | -0.060555 | 0.077363 | -5.722413 | -0.396078 | 0.597872 | 1.329787 | 0.17994 | 73/11/10 | 0 |
| NXT | three_20_30_50_add0p4_0p8_tp0p5 | 94 | -0.048943 | 0.136182 | -4.644558 | -0.30354 | 0.481915 | 1.755319 | 0.228928 | 76/9/9 | 0 |
| NXT | three_20_30_50_add0p5_1p0_tp0p5 | 94 | -0.043711 | 0.160006 | -4.150106 | -0.28142 | 0.428723 | 1.62766 | 0.235825 | 77/9/8 | 7 |

| Venue | Arm dates | Prior-selected dates | Selected n/EV | Same-date single control n/EV | Selected/control compounded | Selected/control budget MAE | Decision |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| KRX | 18 | 17 | 73/-0.2151 | 73/-0.235848 | -14.720868/-16.220157 | -0.484426/-0.843274 | fixed_tp_split_pareto_improved |
| NXT | 16 | 15 | 88/-0.090211 | 88/-0.108362 | -7.829847/-9.494889 | -0.431329/-0.729662 | source_quality_blocked |

The economic-selector entry cohort is identical across arms. Split legs use planned-capital fractions, a target repriced from the weighted average, no ordinary adverse-first stop, and one common 2% catastrophic stop from the initial entry. A fill bar cannot also hit the repriced target. Primary EV is measured against the full planned budget; deployed-notional EV is diagnostic only. Arm choice for a date uses complete outcomes from earlier dates only and has no runtime authority.

## Equal-share carry-to-target widget execution replay

| Venue | Selected arm | Calibration entries | Holdout dates/entries | Completed/censored | Completion ratio | Completed net avg | Same/cross-day | Median/max days | Avg/worst MAE | Max bundles/shares | Ending bundles/shares | Decision |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |
| KRX | three_equal_add0p5_1p0_tp0p5 | 62 | 6/16 | 16/0 | 1.0 | 0.392912 | 16/0 | 0.0/0 | -0.319658/-0.537057 | 1/3 | 0/0 | widget_auto_trade_policy_candidate_ready |
| NXT | three_equal_add0p4_0p8_tp0p5 | 75 | 6/19 | 16/2 | 0.888889 | 0.454363 | 16/0 | 0.0/0 | -0.523614/-5.516266 | 1/3 | 0/0 | source_quality_blocked |

Each execution leg is exactly one share and only one automated bundle may be active per symbol on a trade date. Calibration paths stop strictly before the six-date holdout begins; holdout outcomes cannot select the arm. Additional legs are allowed only in the original entry session. The runtime-candidate target is observed only until the daily reset; unhit positions become unmanaged inventory diagnostics and are never rewritten as zero-return wins or losses. This report does not itself authorize live orders or a widget policy change.

## Fixed-execution entry catastrophic-risk quality nested OOS

| Venue | OOS dates | Control n/EV | Selected n/EV | Control/Selected compounded | Control/Selected budget MAE | Control/Selected disaster stops | Retention | Skip disaster/non-disaster/profitable | AP/prevalence/Brier | Bounded exploration | Decision |
| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| KRX | 17 | 73/-0.147171 | 61/-0.09867 | -10.36379/-5.981592 | -0.482951/-0.461376 | 12/9 | 0.835616 | 3/9/7 | 0.189041/0.164384/0.175918 | 53 | entry_quality_pareto_improved |
| NXT | 14 | 76/-0.071537 | 64/-0.040897 | -5.462445/-2.720304 | -0.402673/-0.382723 | 10/8 | 0.842105 | 2/10/9 | 0.128048/0.131579/0.137001 | 56 | source_quality_blocked |

The 40/60 add-at-0.8% and average-price +0.5% execution owner is fixed. Entry-time economic features and prior-only fixed-arm outcomes estimate catastrophic-loss-adjusted net EV; catastrophic probability alone never blocks an entry. Negative-EV skips are bounded so both each evaluation date and cumulative opportunity retention remain at least 75%. Skipped realized outcomes are post-OOS attribution only and cannot change the same-date model.

## Broader-universe recoverable-basin direct-EV nested OOS

| Venue | OOS dates | Broad control n/EV | Economic baseline n/EV | Basin selected n/EV | Broad/Economic/Selected compounded | Broad/Economic/Selected disaster | Retention | Skip profitable/disaster | Predicted/realized EV | MAE/correlation | Decision |
| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| KRX | 17 | 191/-0.11214 | 73/-0.147171 | 170/-0.090151 | -19.696423/-10.36379/-14.58274 | 30/12/25 | 0.890052 | 27/6 | -0.082141/-0.097631 | 0.582784/-0.078347 | broader_universe_no_incremental_value |
| NXT | 17 | 257/-0.084322 | 88/-0.073836 | 239/-0.093123 | -19.97205/-6.477511/-20.406611 | 33/11/31 | 0.929961 | 38/4 | -0.058473/-0.074623 | 0.513178/-0.109026 | source_quality_blocked |

The candidate universe includes every causal armed candidate from model-ready economic lanes, not only economic-selected entries. Each candidate is independently labeled by the fixed 40/60 execution, while the executable state machine considers candidates chronologically, lets an entered position own its slot until fixed exit, and immediately reconsiders later candidates after a model skip. The direct-EV model and shrinkage use prior dates only. Three same-session entries earn at most one later negative-EV skip, so no future candidate count is needed for the 75% prefix retention guarantee.

## Coarse parent-archetype prior-only attribution

| Venue | OOS dates | Broad control n/EV | Economic baseline n/EV | Prior-axis selected n/EV | Broad/Economic/Selected compounded | Broad/Economic/Selected disaster rate | Retention | Selected axis dates | Mixed-parent dates | Decision |
| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| KRX | 16 | 180/-0.121137 | 68/-0.173406 | 157/-0.093864 | -19.991865/-11.297196/-14.061252 | 16.111111/17.647059/15.286624 | 0.872222 | {'lane_parent': 1, 'session_time_parent': 2, 'volatility_parent': 13} | 16 | parent_bucket_conflict_only |
| NXT | 16 | 240/-0.090838 | 76/-0.071537 | 221/-0.079302 | -20.060415/-5.462445/-16.510809 | 13.333333/13.157895/12.669683 | 0.920833 | {'lane_parent': 9, 'range_position_parent': 7} | 10 | source_quality_blocked |

| Venue | Parent axis | OOS n/EV | Compounded | Budget MAE | Disaster stops |
| --- | --- | --- | ---: | ---: | ---: |
| KRX | lane_parent | 164/-0.095255 | -14.831241 | -0.461405 | 25 |
| KRX | session_time_parent | 166/-0.076644 | -12.31134 | -0.451791 | 24 |
| KRX | volatility_parent | 172/-0.06661 | -11.199644 | -0.451411 | 24 |
| KRX | relative_strength_parent | 165/-0.079836 | -12.706978 | -0.455959 | 24 |
| KRX | vwap_position_parent | 164/-0.08162 | -12.893159 | -0.456141 | 24 |
| KRX | range_position_parent | 164/-0.081369 | -12.857341 | -0.457549 | 24 |
| NXT | lane_parent | 236/-0.06158 | -13.96891 | -0.445461 | 27 |
| NXT | session_time_parent | 232/-0.071158 | -15.654257 | -0.456139 | 27 |
| NXT | volatility_parent | 238/-0.062241 | -14.20893 | -0.446737 | 27 |
| NXT | relative_strength_parent | 238/-0.062836 | -14.329798 | -0.437048 | 27 |
| NXT | vwap_position_parent | 235/-0.065953 | -14.794599 | -0.444263 | 27 |
| NXT | range_position_parent | 233/-0.068495 | -15.197257 | -0.457591 | 28 |

| Venue | Prior-selected axis bucket | OOS n/EV | Win rate | Disaster stops |
| --- | --- | --- | ---: | ---: |
| KRX | lane_parent:bullish_transition | 4/-1.218231 | 25.0 | 3 |
| KRX | lane_parent:weak_reversal | 5/-0.233028 | 80.0 | 1 |
| KRX | session_time_parent:high | 6/0.215802 | 83.333 | 0 |
| KRX | session_time_parent:low | 6/0.201214 | 100.0 | 0 |
| KRX | session_time_parent:middle | 6/-0.04964 | 83.333 | 1 |
| KRX | volatility_parent:high | 61/-0.108403 | 81.967 | 10 |
| KRX | volatility_parent:low | 26/-0.177516 | 73.077 | 5 |
| KRX | volatility_parent:middle | 43/0.007563 | 86.047 | 4 |
| NXT | lane_parent:bullish_transition | 31/-0.065704 | 74.194 | 4 |
| NXT | lane_parent:weak_reversal | 90/-0.047645 | 80.0 | 9 |
| NXT | range_position_parent:high | 30/-0.126429 | 80.0 | 5 |
| NXT | range_position_parent:low | 31/-0.007464 | 80.645 | 3 |
| NXT | range_position_parent:middle | 39/-0.184013 | 71.795 | 7 |

Each parent axis is evaluated independently; no multi-feature child combination owns a decision. Numeric tercile boundaries, bucket EV shrinkage, and the axis used on an evaluation date are all fitted from earlier dates only. Axis-wide summaries are diagnostic only. The executable comparison uses the prior-selected axis with the unchanged fixed 40/60 execution and the same prefix-safe 75% bounded-exploration contract.

## Fixed parent conflict stability

| Venue | Focus | n/dates | EV | Positive dates | First/second half EV | Rolling-positive ratio | Leave-one min/max/all-positive | Catastrophic loss share | Worst-date loss share | Decision |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: | --- |
| KRX | volatility_parent:middle | 43/11 | 0.007563 | 7/0.636364 | -0.042464/0.043583 | 0.444444 | -0.037391/0.049382/False | 0.920388 | 0.296999 | parent_edge_concentrated_not_reproducible |
| NXT | volatility_parent:middle | None/None | None | None/None | None/None | None | None/None/None | None | None | source_quality_blocked |

| Venue | Focus date | n/EV | Simple sum | Win rate | Disaster stops |
| --- | --- | --- | ---: | ---: | ---: |
| KRX | 2026-07-23 | 3/0.093161 | 0.279482 | 66.667 | 0 |
| KRX | 2026-07-27 | 5/0.233328 | 1.166641 | 100.0 | 0 |
| KRX | 2026-07-28 | 4/-0.400168 | -1.60067 | 50.0 | 1 |
| KRX | 2026-07-30 | 2/-0.783381 | -1.566761 | 50.0 | 1 |
| KRX | 2026-07-31 | 4/0.239239 | 0.956958 | 100.0 | 0 |
| KRX | 2026-08-03 | 6/0.152982 | 0.91789 | 100.0 | 0 |
| KRX | 2026-08-04 | 7/0.238754 | 1.671278 | 100.0 | 0 |
| KRX | 2026-08-05 | 4/-0.246704 | -0.986816 | 75.0 | 1 |
| KRX | 2026-08-06 | 1/0.17974 | 0.17974 | 100.0 | 0 |
| KRX | 2026-08-07 | 5/-0.209732 | -1.048661 | 80.0 | 1 |
| KRX | 2026-08-10 | 2/0.178069 | 0.356138 | 100.0 | 0 |

This section consumes the already completed prior-selected parent decisions without refitting any boundary, bucket, axis, entry action, or execution owner. Rolling, leave-one-date, and concentration metrics are post-OOS diagnostics only. The predeclared volatility-middle focus cannot become a same-sample hard gate or runtime candidate.

## Fixed parent catastrophic pre-entry episode audit

| Venue | Focus decisions/EV | Catastrophic/target/session-close | Source gaps | Context available | Distribution shifts | Retention-safe signatures | Lane signature | Decision |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| KRX | 43/0.007563 | 4/37/2 | 0 | {'true': 43} | candidate_age_minutes, causal_volatility_scale_pct | none | False | loss_signature_not_separable |
| NXT | 0/None | 0/0/0 | 0 | {} | none | none | False | source_quality_blocked |

| Venue | Feature | Cat median | Target median | Direction/probability | Same-side catastrophic | Leave-one minimum | Target retention | Shift/signature |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| KRX | causal_volatility_scale_pct | 0.25618346 | 0.22053949 | catastrophic_higher/0.85135135 | 4/4 | 0.81081081 | 0.51351351 | True/False |
| KRX | candidate_age_minutes | 1.0 | 2.0 | catastrophic_lower/0.82432432 | 4/4 | 0.82432432 | 0.64864865 | True/False |
| KRX | pre_entry_return_3m_pct | -0.21071271 | -0.09285051 | catastrophic_lower/0.73986486 | 4/4 | 0.68918919 | 0.51351351 | False/False |
| KRX | confirmation_return_3m_vol_units | -0.8498515 | -0.38417062 | catastrophic_lower/0.70945946 | 4/4 | 0.64864865 | 0.51351351 | False/False |
| KRX | pre_entry_return_5m_pct | -0.53066556 | -0.20080321 | catastrophic_lower/0.7027027 | 3/4 | 0.6036036 | 0.51351351 | False/False |
| KRX | confirmation_bar_range_vol_units | 1.54800786 | 1.84233401 | catastrophic_lower/0.68918919 | 3/4 | 0.61261261 | 0.51351351 | False/False |
| KRX | confirmation_return_5m_vol_units | -2.17053507 | -0.82678399 | catastrophic_lower/0.68581081 | 3/4 | 0.58108108 | 0.51351351 | False/False |
| KRX | confirmation_short_long_acceleration_vol_units | 2.0786019 | 0.0 | catastrophic_higher/0.67567568 | 3/4 | 0.58558559 | 0.54054054 | False/False |
| KRX | confirmation_session_progress | 0.3 | 0.43846154 | catastrophic_lower/0.6722973 | 3/4 | 0.59009009 | 0.51351351 | False/False |
| KRX | pre_entry_return_10m_pct | -0.43767851 | -0.21367521 | catastrophic_lower/0.64864865 | 2/4 | 0.53153153 | 0.51351351 | False/False |
| KRX | confirmation_relative_3m_vol_units | -0.04544424 | 0.13543585 | catastrophic_lower/0.63513514 | 4/4 | 0.6036036 | 0.51351351 | False/False |
| KRX | pre_entry_negative_step_count_5 | 3.0 | 2.0 | catastrophic_higher/0.62837838 | 3/4 | 0.5990991 | 0.51351351 | False/False |
| KRX | confirmation_drawdown_from_20m_high_range_units | -0.63095238 | -0.5 | catastrophic_lower/0.62162162 | 2/4 | 0.5045045 | 0.54054054 | False/False |
| KRX | confirmation_position_in_20m_range | 0.36904762 | 0.5 | catastrophic_lower/0.62162162 | 2/4 | 0.5045045 | 0.54054054 | False/False |
| KRX | confirmation_kospi_return_3m_vol_units | -0.75594614 | -0.5070773 | catastrophic_lower/0.62162162 | 3/4 | 0.57657658 | 0.51351351 | False/False |
| KRX | confirmation_volume_vs_20m_median_log | -0.30838252 | 0.0 | catastrophic_lower/0.61486486 | 3/4 | 0.54054054 | 0.51351351 | False/False |
| KRX | confirmation_return_1m_vol_units | 0.88232714 | 0.95538478 | catastrophic_lower/0.60135135 | 2/4 | 0.55855856 | 0.51351351 | False/False |
| KRX | confirmation_vwap_distance_vol_units | -4.26658611 | -2.79438852 | catastrophic_lower/0.58108108 | 2/4 | 0.44144144 | 0.51351351 | False/False |
| KRX | pre_entry_down_volume_share_5 | 0.56511541 | 0.54231004 | catastrophic_higher/0.56756757 | 3/4 | 0.46846847 | 0.51351351 | False/False |
| KRX | pre_entry_return_1m_pct | 0.21787707 | 0.21645022 | catastrophic_lower/0.52027027 | 2/4 | 0.45045045 | 0.51351351 | False/False |

| Venue | Outcome | Entry | Lane | Return | Context |
| --- | --- | --- | --- | ---: | --- |
| KRX | catastrophic_stop | 2026-07-28T11:47:00 | weak_reversal | -1.675939 | True |
| KRX | catastrophic_stop | 2026-07-30T13:02:00 | weak_reversal | -1.774531 | True |
| KRX | catastrophic_stop | 2026-08-05T09:43:00 | weak_reversal | -1.80405 | True |
| KRX | catastrophic_stop | 2026-08-07T10:09:00 | bullish_transition | -1.816688 | True |

The audit joins unchanged fixed-parent entry identities to their original causal candidate and completed bars immediately preceding entry. Outcome labels only define the comparison groups. No post-entry MFE, MAE, low, high, or exit value is used as a feature. Each diagnostic dimension stands alone; a signature candidate is future-date research input only and cannot become a same-sample hard gate, runtime policy, or order authority.

## Fixed catastrophic-stop recovery path

| Venue | Episodes | Stop control EV/compounded | Continue EV/compounded | Target recovery | Continue better/Stop protected | Recovery by 1/3/5/10/20/30/60m | Source gaps/terminal limited | Evidence complete | Decision |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| KRX | 4 | -1.767802/-6.885959 | None/-1.890903 | 2/0.5 | 4/0 | 0/0/0/1/2/2/2 | 0/2 | False | mixed_post_stop_paths_no_owner_change |
| NXT | 0 | None/0.0 | None/0.0 | 0/None | 0/0 | 0/0/0/0/0/0/0 | 0/0 | False | source_quality_blocked |

| Venue | Entry/Stop | Stop return | Continued exit/reason/return | Target hit minutes | Additional drawdown/Rebound from stop | Terminal mark/time/exact-close |
| --- | --- | ---: | --- | ---: | --- | ---: |
| KRX | 2026-07-28T11:47:00/2026-07-28T12:11:00 | -1.675939 | 2026-07-28T12:20:00/post_stop_average_target_recovery/0.339326 | 9.0 | -0.681818/2.5 | -1.899857/2026-07-28T15:19:00/False |
| KRX | 2026-07-30T13:02:00/2026-07-30T13:16:00 | -1.774531 | 2026-07-30T13:28:00/post_stop_average_target_recovery/0.37554 | 12.0 | 0.0/3.398058 | -1.296738/2026-07-30T15:19:00/False |
| KRX | 2026-08-05T09:43:00/2026-08-05T10:04:00 | -1.80405 | 2026-08-05T15:19:00/post_stop_last_observed_regular_mark/-1.000818 | None | -0.408163/2.040816 | -1.000818/2026-08-05T15:19:00/False |
| KRX | 2026-08-07T10:09:00/2026-08-07T10:21:00 | -1.816688 | 2026-08-07T15:19:00/post_stop_last_observed_regular_mark/-1.603738 | None | -0.865801/1.515152 | -1.603738/2026-08-07T15:19:00/False |

The stop-bar itself is excluded because intrabar high/low order after the stop fill is unknowable. The hard-stop control and same-quantity continuation counterfactual are reported separately and never summed. A KRX terminal mark before 15:30 is diagnostic only, makes continuation source-quality-adjusted EV unavailable for a non-target episode, and cannot support an owner change. Post-stop paths are execution outcomes only, not entry features or same-sample stop-removal authority.

## Fixed post-stop bounded grace arms

| Venue | Grace | Episodes | EV/adjusted EV/compounded | Target recovered | Improved/Worsened/Equal | Avg/Worst conservative additional MAE | Prospective only |
| --- | ---: | ---: | --- | ---: | --- | --- | --- |
| KRX | 5 | 4 | -1.07078/-1.07078/-4.216988 | 0 | 4/0/0 | -0.054113/-0.21645 | True |
| KRX | 10 | 4 | -0.491882/-0.491882/-1.958971 | 1 | 4/0/0 | -0.054113/-0.21645 | True |
| KRX | 20 | 4 | -0.756123/-0.756123/-3.015503 | 2 | 3/1/0 | -0.21645/-0.865801 | True |
| NXT | 5 | 0 | None/None/None | 0 | 0/0/0 | None/None | False |
| NXT | 10 | 0 | None/None/None | 0 | 0/0/0 | None/None | False |
| NXT | 20 | 0 | None/None/None | 0 | 0/0/0 | None/None | False |

| Venue | Control EV/compounded | Candidate horizons | Same-sample best selected | Source gaps | Decision |
| --- | --- | --- | --- | ---: | --- |
| KRX | -1.767802/-6.885959 | [5, 10, 20] | False | 0 | bounded_grace_candidate_for_prospective_only |
| NXT | None/None | [] | False | 0 | source_quality_blocked |

| Venue | Grace | Trade date | Exit/reason | Grace return | Delta vs stop | Conservative additional MAE |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| KRX | 5 | 2026-07-28 | 2026-07-28T12:16:00/exact_grace_horizon_completed_bar_mark | -1.004184 | 0.671755 | 0.0 |
| KRX | 5 | 2026-07-30 | 2026-07-30T13:21:00/exact_grace_horizon_completed_bar_mark | -0.580048 | 1.194483 | 0.0 |
| KRX | 5 | 2026-08-05 | 2026-08-05T10:09:00/exact_grace_horizon_completed_bar_mark | -1.201626 | 0.602424 | 0.0 |
| KRX | 5 | 2026-08-07 | 2026-08-07T10:26:00/exact_grace_horizon_completed_bar_mark | -1.497262 | 0.319426 | -0.21645 |
| KRX | 10 | 2026-07-28 | 2026-07-28T12:20:00/existing_average_target_recovery | 0.339326 | 2.015265 | 0.0 |
| KRX | 10 | 2026-07-30 | 2026-07-30T13:26:00/exact_grace_horizon_completed_bar_mark | -0.341151 | 1.43338 | 0.0 |
| KRX | 10 | 2026-08-05 | 2026-08-05T10:14:00/exact_grace_horizon_completed_bar_mark | -1.000818 | 0.803232 | 0.0 |
| KRX | 10 | 2026-08-07 | 2026-08-07T10:31:00/exact_grace_horizon_completed_bar_mark | -0.964885 | 0.851803 | -0.21645 |
| KRX | 20 | 2026-07-28 | 2026-07-28T12:20:00/existing_average_target_recovery | 0.339326 | 2.015265 | 0.0 |
| KRX | 20 | 2026-07-30 | 2026-07-30T13:28:00/existing_average_target_recovery | 0.37554 | 2.150071 | 0.0 |
| KRX | 20 | 2026-08-05 | 2026-08-05T10:24:00/exact_grace_horizon_completed_bar_mark | -1.603242 | 0.200808 | 0.0 |
| KRX | 20 | 2026-08-07 | 2026-08-07T10:41:00/exact_grace_horizon_completed_bar_mark | -2.136115 | -0.319427 | -0.865801 |

Each 5/10/20-minute arm starts strictly after the catastrophic-stop bar, retains the existing filled quantity and average-price target, and exits at the target if it is hit first or at the exact completed horizon-bar close. Additional MAE includes the target-hit bar as a conservative intrabar envelope; the known pre-target-bar MAE remains available per episode. Arms are never summed or ranked into a same-sample winner. Any improving horizon is prospective attribution only and has no runtime, order, quantity, target, emergency-floor, provider, or bot authority.

## Fixed grace prospective OOS attribution

| Venue | Frozen at/Start | Calibration excluded/New OOS | Control EV/compounded | Source gaps | Decision |
| --- | --- | --- | --- | ---: | --- |
| KRX | 2026-08-10/2026-08-11 | 4/0 | None/None | 0 | no_new_catastrophic_episode_observe |
| NXT | 2026-08-10/2026-08-11 | 0/0 | None/None | 0 | source_quality_blocked |

| Venue | Grace | New OOS | EV/adjusted EV/compounded | Target recovered | Improved/Worsened | Avg/Worst conservative additional MAE |
| --- | ---: | ---: | --- | ---: | --- | --- |
| KRX | 5 | 0 | None/None/None | 0 | 0/0 | None/None |
| KRX | 10 | 0 | None/None/None | 0 | 0/0 | None/None |
| KRX | 20 | 0 | None/None/None | 0 | 0/0 | None/None |
| NXT | 5 | 0 | None/None/None | 0 | 0/0 | None/None |
| NXT | 10 | 0 | None/None/None | 0 | 0/0 | None/None |
| NXT | 20 | 0 | None/None/None | 0 | 0/0 | None/None |

The candidate horizons are frozen from the report ending 2026-08-10. Episodes through that date are counted only as excluded calibration provenance and never enter prospective EV. Zero new catastrophic episodes is a valid observe state with null EV, not a zero-return result. Prospective outcomes cannot select a same-sample winner or acquire runtime/order authority.

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
