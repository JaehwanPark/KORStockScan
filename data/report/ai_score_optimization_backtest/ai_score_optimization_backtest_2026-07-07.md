# AI Score Optimization Backtest - 2026-07-07

- calibration_state: `source_quality_blocked`
- allowed_runtime_apply: `False`
- calibration_candidate_count: `2`
- allowed_runtime_apply_candidate_count: `0`
- diagnostic_only_candidate_count: `2`

## Blocked Reasons

- `source_quality_blocked`: `2`

## Calibration Candidates

```json
[
  {
    "actual_order_submitted": false,
    "allowed_runtime_apply": false,
    "broker_order_forbidden": true,
    "calibration_reason": "source_quality_not_pass",
    "calibration_state": "hold_sample",
    "current_values": {
      "low_ai_block": 50.0,
      "max_repeated_blockers_without_support": 8,
      "max_spread_bps": 80.0,
      "min_ai_moderate": 60.0,
      "min_ai_support": 70.0,
      "min_prior_peak_pct": 0.3
    },
    "decision_authority": "postclose_calibration_candidate_preopen_only",
    "family": "rising_missed_first_touch_avgdown_decision_gate",
    "family_type": "bounded_tunable_scale_in_first_touch_gate",
    "forbidden_uses": [
      "intraday_threshold_mutation",
      "intraday_runtime_apply",
      "hard_safety_relaxation",
      "broker_guard_bypass",
      "order_guard_relaxation",
      "provider_route_change",
      "bot_restart",
      "real_execution_quality_approval"
    ],
    "priority": 38,
    "recommended_values": {
      "low_ai_block": 50.0,
      "max_repeated_blockers_without_support": 8,
      "max_spread_bps": 80.0,
      "min_ai_moderate": 60.0,
      "min_ai_support": 70.0,
      "min_prior_peak_pct": 0.3
    },
    "runtime_effect": false,
    "safety_revert_required": false,
    "sample_count": 20,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 10,
          "label": "first_touch_recovered_profit"
        },
        {
          "count": 10,
          "label": "first_touch_loss_or_flat"
        }
      ],
      "loss_or_flat_count": 10,
      "loss_or_flat_rate": 0.5,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 10,
      "recovered_rate": 0.5,
      "sample_count": 20,
      "source_quality_pass": false
    },
    "source_quality_blocked": "source_quality_not_pass",
    "source_quality_gate": "source_quality_blocked",
    "source_quality_status": "blocked",
    "source_reports": [
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-02.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-03.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-06.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-07.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-07:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-07.json"
  },
  {
    "actual_order_submitted": false,
    "allowed_runtime_apply": false,
    "broker_order_forbidden": true,
    "calibration_reason": "source_quality_not_pass",
    "calibration_state": "hold_sample",
    "current_values": {
      "max_micro_vwap_bps": 60.0,
      "max_spread_bps": 80.0,
      "min_ai_score": 70.0,
      "min_buy_pressure": 60.0,
      "min_profit_pct": 1.5,
      "min_tick_accel": 0.5,
      "strong_continuation_enabled": false,
      "strong_continuation_max_drawdown_pct": 0.2,
      "strong_continuation_min_profit_pct": 0.9
    },
    "decision_authority": "postclose_calibration_candidate_preopen_only",
    "family": "scalping_pyramid_quality_gate",
    "family_type": "bounded_tunable_scalping_pyramid_quality_gate",
    "forbidden_uses": [
      "intraday_threshold_mutation",
      "intraday_runtime_apply",
      "hard_safety_relaxation",
      "broker_guard_bypass",
      "order_guard_relaxation",
      "quantity_guard_relaxation",
      "position_cap_release",
      "provider_route_change",
      "bot_restart",
      "real_execution_quality_approval"
    ],
    "priority": 39,
    "recommended_values": {
      "max_micro_vwap_bps": 60.0,
      "max_spread_bps": 80.0,
      "min_ai_score": 70.0,
      "min_buy_pressure": 60.0,
      "min_profit_pct": 1.5,
      "min_tick_accel": 0.5,
      "strong_continuation_enabled": false,
      "strong_continuation_max_drawdown_pct": 0.2,
      "strong_continuation_min_profit_pct": 0.9
    },
    "runtime_effect": false,
    "safety_revert_required": false,
    "sample_count": 127,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 35,
      "correctly_blocked_rate": 0.2755905511811024,
      "label_counts": [
        {
          "count": 51,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 41,
          "label": "pyramid_would_have_helped"
        },
        {
          "count": 35,
          "label": "pyramid_correctly_blocked"
        }
      ],
      "one_share_closed_pyramid_row_count": 127,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.8697637795275591,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.22478260869565214,
          "avg_missed_upside_after_threshold_pct": 1.6666304347826084,
          "eligible_count": 92,
          "eligible_rate": 0.7244094488188977,
          "label_counts": [
            {
              "count": 42,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 9,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.30434782608695654,
          "min_profit_pct": 0.8,
          "positive_exit_count": 64,
          "positive_exit_rate": 0.6956521739130435,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.18761363636363634,
          "avg_missed_upside_after_threshold_pct": 1.6395454545454546,
          "eligible_count": 88,
          "eligible_rate": 0.6929133858267716,
          "label_counts": [
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 41,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 6,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.29545454545454547,
          "min_profit_pct": 0.9,
          "positive_exit_count": 62,
          "positive_exit_rate": 0.7045454545454546,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.36573170731707316,
          "avg_missed_upside_after_threshold_pct": 1.656219512195122,
          "eligible_count": 82,
          "eligible_rate": 0.6456692913385826,
          "label_counts": [
            {
              "count": 40,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 38,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 4,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.2804878048780488,
          "min_profit_pct": 1.0,
          "positive_exit_count": 59,
          "positive_exit_rate": 0.7195121951219512,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3462025316455695,
          "avg_missed_upside_after_threshold_pct": 1.6174683544303796,
          "eligible_count": 79,
          "eligible_rate": 0.6220472440944882,
          "label_counts": [
            {
              "count": 38,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 37,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 4,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.35443037974683544,
          "min_profit_pct": 1.1,
          "positive_exit_count": 51,
          "positive_exit_rate": 0.6455696202531646,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3762162162162162,
          "avg_missed_upside_after_threshold_pct": 1.6243243243243244,
          "eligible_count": 74,
          "eligible_rate": 0.5826771653543307,
          "label_counts": [
            {
              "count": 37,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 34,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.36486486486486486,
          "min_profit_pct": 1.2,
          "positive_exit_count": 47,
          "positive_exit_rate": 0.6351351351351351,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.44098591549295774,
          "avg_missed_upside_after_threshold_pct": 1.5911267605633803,
          "eligible_count": 71,
          "eligible_rate": 0.5590551181102362,
          "label_counts": [
            {
              "count": 36,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 33,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.38028169014084506,
          "min_profit_pct": 1.3,
          "positive_exit_count": 44,
          "positive_exit_rate": 0.6197183098591549,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3409859154929578,
          "avg_missed_upside_after_threshold_pct": 1.4911267605633804,
          "eligible_count": 71,
          "eligible_rate": 0.5590551181102362,
          "label_counts": [
            {
              "count": 36,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 33,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.43661971830985913,
          "min_profit_pct": 1.4,
          "positive_exit_count": 40,
          "positive_exit_rate": 0.5633802816901409,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.2833823529411765,
          "avg_missed_upside_after_threshold_pct": 1.4554411764705881,
          "eligible_count": 68,
          "eligible_rate": 0.5354330708661418,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.47058823529411764,
          "min_profit_pct": 1.5,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.5294117647058824,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3243548387096773,
          "avg_missed_upside_after_threshold_pct": 1.491774193548387,
          "eligible_count": 62,
          "eligible_rate": 0.4881889763779528,
          "label_counts": [
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 27,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.45161290322580644,
          "min_profit_pct": 1.6,
          "positive_exit_count": 34,
          "positive_exit_rate": 0.5483870967741935,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.34271186440677964,
          "avg_missed_upside_after_threshold_pct": 1.464915254237288,
          "eligible_count": 59,
          "eligible_rate": 0.4645669291338583,
          "label_counts": [
            {
              "count": 33,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 26,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.4915254237288136,
          "min_profit_pct": 1.7,
          "positive_exit_count": 30,
          "positive_exit_rate": 0.5084745762711864,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.27175438596491225,
          "avg_missed_upside_after_threshold_pct": 1.414561403508772,
          "eligible_count": 57,
          "eligible_rate": 0.44881889763779526,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 26,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.5087719298245614,
          "min_profit_pct": 1.8,
          "positive_exit_count": 28,
          "positive_exit_rate": 0.49122807017543857,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.210925925925926,
          "avg_missed_upside_after_threshold_pct": 1.3905555555555555,
          "eligible_count": 54,
          "eligible_rate": 0.4251968503937008,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.5555555555555556,
          "min_profit_pct": 1.9,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.4444444444444444,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.1918,
          "avg_missed_upside_after_threshold_pct": 1.4,
          "eligible_count": 50,
          "eligible_rate": 0.3937007874015748,
          "label_counts": [
            {
              "count": 27,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 23,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.56,
          "min_profit_pct": 2.0,
          "positive_exit_count": 22,
          "positive_exit_rate": 0.44,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.20466666666666658,
          "avg_missed_upside_after_threshold_pct": 1.451111111111111,
          "eligible_count": 45,
          "eligible_rate": 0.3543307086614173,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.5333333333333333,
          "min_profit_pct": 2.1,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4666666666666667,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.2017499999999998,
          "avg_missed_upside_after_threshold_pct": 1.5277499999999997,
          "eligible_count": 40,
          "eligible_rate": 0.31496062992125984,
          "label_counts": [
            {
              "count": 24,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.525,
          "min_profit_pct": 2.2,
          "positive_exit_count": 19,
          "positive_exit_rate": 0.475,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3816216216216218,
          "avg_missed_upside_after_threshold_pct": 1.550810810810811,
          "eligible_count": 37,
          "eligible_rate": 0.29133858267716534,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.4864864864864865,
          "min_profit_pct": 2.3,
          "positive_exit_count": 19,
          "positive_exit_rate": 0.5135135135135135,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3591428571428572,
          "avg_missed_upside_after_threshold_pct": 1.5351428571428574,
          "eligible_count": 35,
          "eligible_rate": 0.2755905511811024,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 12,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.45714285714285713,
          "min_profit_pct": 2.4,
          "positive_exit_count": 19,
          "positive_exit_rate": 0.5428571428571428,
          "source_row_count": 127
        },
        {
          "avg_incremental_exit_profit_pct": 0.3803125,
          "avg_missed_upside_after_threshold_pct": 1.5759375,
          "eligible_count": 32,
          "eligible_rate": 0.25196850393700787,
          "label_counts": [
            {
              "count": 21,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 14,
          "loss_or_flat_rate": 0.4375,
          "min_profit_pct": 2.5,
          "positive_exit_count": 18,
          "positive_exit_rate": 0.5625,
          "source_row_count": 127
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.15760356255178126,
        "current_avg_incremental_exit_profit_pct": 0.2833823529411765,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.2833823529411765,
          "avg_missed_upside_after_threshold_pct": 1.4554411764705881,
          "eligible_count": 68,
          "eligible_rate": 0.5354330708661418,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.47058823529411764,
          "min_profit_pct": 1.5,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.5294117647058824,
          "source_row_count": 127
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.44098591549295774,
        "selected_min_profit_pct": 1.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.44098591549295774,
          "avg_missed_upside_after_threshold_pct": 1.5911267605633803,
          "eligible_count": 71,
          "eligible_rate": 0.5590551181102362,
          "label_counts": [
            {
              "count": 36,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 33,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.38028169014084506,
          "min_profit_pct": 1.3,
          "positive_exit_count": 44,
          "positive_exit_rate": 0.6197183098591549,
          "source_row_count": 127
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 41,
      "recovered_or_extended_rate": 0.3228346456692913,
      "reversal_or_flat_count": 51,
      "reversal_or_flat_rate": 0.4015748031496063,
      "sample_count": 127,
      "source_quality_pass": false
    },
    "source_quality_blocked": "source_quality_not_pass",
    "source_quality_gate": "source_quality_blocked",
    "source_quality_status": "blocked",
    "source_reports": [
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-04.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-05.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-08.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-09.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-10.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-11.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-12.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-13.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-14.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-15.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-16.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-17.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-18.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-19.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-22.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-23.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-24.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-25.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-26.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-29.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-06-30.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-01.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-02.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-03.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-06.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-07.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-07:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-07.json"
  }
]
```
