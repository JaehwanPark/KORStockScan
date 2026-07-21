# AI Score Optimization Backtest - 2026-07-21

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
    "sample_count": 43,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 30,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 13,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 30,
      "loss_or_flat_rate": 0.6976744186046512,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 13,
      "recovered_rate": 0.3023255813953488,
      "sample_count": 43,
      "source_quality_pass": false
    },
    "source_quality_blocked": "source_quality_not_pass",
    "source_quality_gate": "source_quality_blocked",
    "source_quality_status": "blocked",
    "source_reports": [
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-02.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-03.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-06.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-07.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-08.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-09.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-10.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-13.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-14.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-15.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-16.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-20.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-21.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-21:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-21.json"
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
    "sample_count": 192,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 58,
      "correctly_blocked_rate": 0.3020833333333333,
      "label_counts": [
        {
          "count": 85,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 58,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 49,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 192,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.6767708333333333,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.08702290076335874,
          "avg_missed_upside_after_threshold_pct": 1.5029770992366411,
          "eligible_count": 131,
          "eligible_rate": 0.6822916666666666,
          "label_counts": [
            {
              "count": 67,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 49,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 15,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 50,
          "loss_or_flat_rate": 0.3816793893129771,
          "min_profit_pct": 0.8,
          "positive_exit_count": 81,
          "positive_exit_rate": 0.6183206106870229,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.07943548387096772,
          "avg_missed_upside_after_threshold_pct": 1.484516129032258,
          "eligible_count": 124,
          "eligible_rate": 0.6458333333333334,
          "label_counts": [
            {
              "count": 65,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 49,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 10,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 46,
          "loss_or_flat_rate": 0.3709677419354839,
          "min_profit_pct": 0.9,
          "positive_exit_count": 78,
          "positive_exit_rate": 0.6290322580645161,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.23104347826086957,
          "avg_missed_upside_after_threshold_pct": 1.4972173913043478,
          "eligible_count": 115,
          "eligible_rate": 0.5989583333333334,
          "label_counts": [
            {
              "count": 60,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 48,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 7,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 41,
          "loss_or_flat_rate": 0.3565217391304348,
          "min_profit_pct": 1.0,
          "positive_exit_count": 74,
          "positive_exit_rate": 0.6434782608695652,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.2024545454545454,
          "avg_missed_upside_after_threshold_pct": 1.4637272727272725,
          "eligible_count": 110,
          "eligible_rate": 0.5729166666666666,
          "label_counts": [
            {
              "count": 58,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 6,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 45,
          "loss_or_flat_rate": 0.4090909090909091,
          "min_profit_pct": 1.1,
          "positive_exit_count": 65,
          "positive_exit_rate": 0.5909090909090909,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.20009708737864076,
          "avg_missed_upside_after_threshold_pct": 1.4598058252427186,
          "eligible_count": 103,
          "eligible_rate": 0.5364583333333334,
          "label_counts": [
            {
              "count": 54,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 45,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 4,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 42,
          "loss_or_flat_rate": 0.4077669902912621,
          "min_profit_pct": 1.2,
          "positive_exit_count": 61,
          "positive_exit_rate": 0.5922330097087378,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.2451546391752577,
          "avg_missed_upside_after_threshold_pct": 1.4473195876288658,
          "eligible_count": 97,
          "eligible_rate": 0.5052083333333334,
          "label_counts": [
            {
              "count": 50,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 41,
          "loss_or_flat_rate": 0.422680412371134,
          "min_profit_pct": 1.3,
          "positive_exit_count": 56,
          "positive_exit_rate": 0.5773195876288659,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.21687500000000007,
          "avg_missed_upside_after_threshold_pct": 1.3617708333333336,
          "eligible_count": 96,
          "eligible_rate": 0.5,
          "label_counts": [
            {
              "count": 49,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 45,
          "loss_or_flat_rate": 0.46875,
          "min_profit_pct": 1.4,
          "positive_exit_count": 51,
          "positive_exit_rate": 0.53125,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.18155555555555555,
          "avg_missed_upside_after_threshold_pct": 1.3506666666666667,
          "eligible_count": 90,
          "eligible_rate": 0.46875,
          "label_counts": [
            {
              "count": 45,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 42,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 47,
          "loss_or_flat_rate": 0.5222222222222223,
          "min_profit_pct": 1.5,
          "positive_exit_count": 43,
          "positive_exit_rate": 0.4777777777777778,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.20253012048192762,
          "avg_missed_upside_after_threshold_pct": 1.3601204819277106,
          "eligible_count": 83,
          "eligible_rate": 0.4322916666666667,
          "label_counts": [
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 40,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 43,
          "loss_or_flat_rate": 0.5180722891566265,
          "min_profit_pct": 1.6,
          "positive_exit_count": 40,
          "positive_exit_rate": 0.4819277108433735,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.24749999999999997,
          "avg_missed_upside_after_threshold_pct": 1.3826315789473684,
          "eligible_count": 76,
          "eligible_rate": 0.3958333333333333,
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
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 41,
          "loss_or_flat_rate": 0.5394736842105263,
          "min_profit_pct": 1.7,
          "positive_exit_count": 35,
          "positive_exit_rate": 0.4605263157894737,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.17520547945205475,
          "avg_missed_upside_after_threshold_pct": 1.337945205479452,
          "eligible_count": 73,
          "eligible_rate": 0.3802083333333333,
          "label_counts": [
            {
              "count": 37,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 40,
          "loss_or_flat_rate": 0.547945205479452,
          "min_profit_pct": 1.8,
          "positive_exit_count": 33,
          "positive_exit_rate": 0.4520547945205479,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.11838235294117654,
          "avg_missed_upside_after_threshold_pct": 1.332794117647059,
          "eligible_count": 68,
          "eligible_rate": 0.3541666666666667,
          "label_counts": [
            {
              "count": 34,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 33,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 39,
          "loss_or_flat_rate": 0.5735294117647058,
          "min_profit_pct": 1.9,
          "positive_exit_count": 29,
          "positive_exit_rate": 0.4264705882352941,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.12416666666666666,
          "avg_missed_upside_after_threshold_pct": 1.4066666666666667,
          "eligible_count": 60,
          "eligible_rate": 0.3125,
          "label_counts": [
            {
              "count": 30,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 29,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 35,
          "loss_or_flat_rate": 0.5833333333333334,
          "min_profit_pct": 2.0,
          "positive_exit_count": 25,
          "positive_exit_rate": 0.4166666666666667,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.11036363636363626,
          "avg_missed_upside_after_threshold_pct": 1.4309090909090907,
          "eligible_count": 55,
          "eligible_rate": 0.2864583333333333,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 26,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.5636363636363636,
          "min_profit_pct": 2.1,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.43636363636363634,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.13354166666666648,
          "avg_missed_upside_after_threshold_pct": 1.5347916666666663,
          "eligible_count": 48,
          "eligible_rate": 0.25,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 21,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.5416666666666666,
          "min_profit_pct": 2.2,
          "positive_exit_count": 22,
          "positive_exit_rate": 0.4583333333333333,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.2829545454545456,
          "avg_missed_upside_after_threshold_pct": 1.5729545454545457,
          "eligible_count": 44,
          "eligible_rate": 0.22916666666666666,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 18,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.5227272727272727,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4772727272727273,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.24285714285714294,
          "avg_missed_upside_after_threshold_pct": 1.5442857142857143,
          "eligible_count": 42,
          "eligible_rate": 0.21875,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5,
          "source_row_count": 192
        },
        {
          "avg_incremental_exit_profit_pct": 0.23333333333333334,
          "avg_missed_upside_after_threshold_pct": 1.5605128205128205,
          "eligible_count": 39,
          "eligible_rate": 0.203125,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 15,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 19,
          "loss_or_flat_rate": 0.48717948717948717,
          "min_profit_pct": 2.5,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5128205128205128,
          "source_row_count": 192
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.10139898989899007,
        "current_avg_incremental_exit_profit_pct": 0.18155555555555555,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.18155555555555555,
          "avg_missed_upside_after_threshold_pct": 1.3506666666666667,
          "eligible_count": 90,
          "eligible_rate": 0.46875,
          "label_counts": [
            {
              "count": 45,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 42,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 47,
          "loss_or_flat_rate": 0.5222222222222223,
          "min_profit_pct": 1.5,
          "positive_exit_count": 43,
          "positive_exit_rate": 0.4777777777777778,
          "source_row_count": 192
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.2829545454545456,
        "selected_min_profit_pct": 2.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.2829545454545456,
          "avg_missed_upside_after_threshold_pct": 1.5729545454545457,
          "eligible_count": 44,
          "eligible_rate": 0.22916666666666666,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 18,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.5227272727272727,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4772727272727273,
          "source_row_count": 192
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 49,
      "recovered_or_extended_rate": 0.2552083333333333,
      "reversal_or_flat_count": 85,
      "reversal_or_flat_rate": 0.4427083333333333,
      "sample_count": 192,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-07.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-08.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-09.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-10.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-13.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-14.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-15.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-16.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-20.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-21.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-21:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-21.json"
  }
]
```
