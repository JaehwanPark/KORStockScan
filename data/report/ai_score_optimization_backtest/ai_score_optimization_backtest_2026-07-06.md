# AI Score Optimization Backtest - 2026-07-06

- calibration_state: `hold_sample`
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
    "sample_count": 14,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 8,
          "label": "first_touch_recovered_profit"
        },
        {
          "count": 6,
          "label": "first_touch_loss_or_flat"
        }
      ],
      "loss_or_flat_count": 6,
      "loss_or_flat_rate": 0.42857142857142855,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 8,
      "recovered_rate": 0.5714285714285714,
      "sample_count": 14,
      "source_quality_pass": false
    },
    "source_quality_blocked": "source_quality_not_pass",
    "source_quality_gate": "source_quality_blocked",
    "source_quality_status": "blocked",
    "source_reports": [
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-02.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-03.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-06.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-06:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-06.json"
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
    "sample_count": 108,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 26,
      "correctly_blocked_rate": 0.24074074074074073,
      "label_counts": [
        {
          "count": 48,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 34,
          "label": "pyramid_would_have_helped"
        },
        {
          "count": 26,
          "label": "pyramid_correctly_blocked"
        }
      ],
      "one_share_closed_pyramid_row_count": 108,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.8949074074074075,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.2573076923076923,
          "avg_missed_upside_after_threshold_pct": 1.7114102564102565,
          "eligible_count": 78,
          "eligible_rate": 0.7222222222222222,
          "label_counts": [
            {
              "count": 39,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.2948717948717949,
          "min_profit_pct": 0.8,
          "positive_exit_count": 55,
          "positive_exit_rate": 0.7051282051282052,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.21842105263157893,
          "avg_missed_upside_after_threshold_pct": 1.6546052631578947,
          "eligible_count": 76,
          "eligible_rate": 0.7037037037037037,
          "label_counts": [
            {
              "count": 38,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 4,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.2894736842105263,
          "min_profit_pct": 0.9,
          "positive_exit_count": 54,
          "positive_exit_rate": 0.7105263157894737,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.4468571428571429,
          "avg_missed_upside_after_threshold_pct": 1.6925714285714286,
          "eligible_count": 70,
          "eligible_rate": 0.6481481481481481,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 33,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.2571428571428571,
          "min_profit_pct": 1.0,
          "positive_exit_count": 52,
          "positive_exit_rate": 0.7428571428571429,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.4453731343283582,
          "avg_missed_upside_after_threshold_pct": 1.666417910447761,
          "eligible_count": 67,
          "eligible_rate": 0.6203703703703703,
          "label_counts": [
            {
              "count": 34,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 31,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.3283582089552239,
          "min_profit_pct": 1.1,
          "positive_exit_count": 45,
          "positive_exit_rate": 0.6716417910447762,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.48349206349206353,
          "avg_missed_upside_after_threshold_pct": 1.6695238095238096,
          "eligible_count": 63,
          "eligible_rate": 0.5833333333333334,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 30,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.3333333333333333,
          "min_profit_pct": 1.2,
          "positive_exit_count": 42,
          "positive_exit_rate": 0.6666666666666666,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.4414754098360656,
          "avg_missed_upside_after_threshold_pct": 1.6221311475409836,
          "eligible_count": 61,
          "eligible_rate": 0.5648148148148148,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.36065573770491804,
          "min_profit_pct": 1.3,
          "positive_exit_count": 39,
          "positive_exit_rate": 0.639344262295082,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.34147540983606567,
          "avg_missed_upside_after_threshold_pct": 1.5221311475409838,
          "eligible_count": 61,
          "eligible_rate": 0.5648148148148148,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 25,
          "loss_or_flat_rate": 0.4098360655737705,
          "min_profit_pct": 1.4,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.5901639344262295,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.276271186440678,
          "avg_missed_upside_after_threshold_pct": 1.4720338983050847,
          "eligible_count": 59,
          "eligible_rate": 0.5462962962962963,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.4576271186440678,
          "min_profit_pct": 1.5,
          "positive_exit_count": 32,
          "positive_exit_rate": 0.5423728813559322,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.31481481481481477,
          "avg_missed_upside_after_threshold_pct": 1.5033333333333332,
          "eligible_count": 54,
          "eligible_rate": 0.5,
          "label_counts": [
            {
              "count": 27,
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
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.4444444444444444,
          "min_profit_pct": 1.6,
          "positive_exit_count": 30,
          "positive_exit_rate": 0.5555555555555556,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.3511764705882353,
          "avg_missed_upside_after_threshold_pct": 1.4886274509803923,
          "eligible_count": 51,
          "eligible_rate": 0.4722222222222222,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 25,
          "loss_or_flat_rate": 0.49019607843137253,
          "min_profit_pct": 1.7,
          "positive_exit_count": 26,
          "positive_exit_rate": 0.5098039215686274,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.2706,
          "avg_missed_upside_after_threshold_pct": 1.4178,
          "eligible_count": 50,
          "eligible_rate": 0.46296296296296297,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.52,
          "min_profit_pct": 1.8,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.48,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.19583333333333341,
          "avg_missed_upside_after_threshold_pct": 1.3739583333333334,
          "eligible_count": 48,
          "eligible_rate": 0.4444444444444444,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.5833333333333334,
          "min_profit_pct": 1.9,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.4166666666666667,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.14400000000000002,
          "avg_missed_upside_after_threshold_pct": 1.3639999999999999,
          "eligible_count": 45,
          "eligible_rate": 0.4166666666666667,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 22,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.5777777777777777,
          "min_profit_pct": 2.0,
          "positive_exit_count": 19,
          "positive_exit_rate": 0.4222222222222222,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.1649999999999999,
          "avg_missed_upside_after_threshold_pct": 1.4294999999999998,
          "eligible_count": 40,
          "eligible_rate": 0.37037037037037035,
          "label_counts": [
            {
              "count": 21,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.55,
          "min_profit_pct": 2.1,
          "positive_exit_count": 18,
          "positive_exit_rate": 0.45,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.17028571428571407,
          "avg_missed_upside_after_threshold_pct": 1.5282857142857142,
          "eligible_count": 35,
          "eligible_rate": 0.32407407407407407,
          "label_counts": [
            {
              "count": 19,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 19,
          "loss_or_flat_rate": 0.5428571428571428,
          "min_profit_pct": 2.2,
          "positive_exit_count": 16,
          "positive_exit_rate": 0.45714285714285713,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.39093750000000016,
          "avg_missed_upside_after_threshold_pct": 1.5706250000000002,
          "eligible_count": 32,
          "eligible_rate": 0.2962962962962963,
          "label_counts": [
            {
              "count": 18,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 2.3,
          "positive_exit_count": 16,
          "positive_exit_rate": 0.5,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.382,
          "avg_missed_upside_after_threshold_pct": 1.5703333333333334,
          "eligible_count": 30,
          "eligible_rate": 0.2777777777777778,
          "label_counts": [
            {
              "count": 18,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 12,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 14,
          "loss_or_flat_rate": 0.4666666666666667,
          "min_profit_pct": 2.4,
          "positive_exit_count": 16,
          "positive_exit_rate": 0.5333333333333333,
          "source_row_count": 108
        },
        {
          "avg_incremental_exit_profit_pct": 0.4281481481481481,
          "avg_missed_upside_after_threshold_pct": 1.6411111111111112,
          "eligible_count": 27,
          "eligible_rate": 0.25,
          "label_counts": [
            {
              "count": 16,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 12,
          "loss_or_flat_rate": 0.4444444444444444,
          "min_profit_pct": 2.5,
          "positive_exit_count": 15,
          "positive_exit_rate": 0.5555555555555556,
          "source_row_count": 108
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.20722087705138553,
        "current_avg_incremental_exit_profit_pct": 0.276271186440678,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.276271186440678,
          "avg_missed_upside_after_threshold_pct": 1.4720338983050847,
          "eligible_count": 59,
          "eligible_rate": 0.5462962962962963,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.4576271186440678,
          "min_profit_pct": 1.5,
          "positive_exit_count": 32,
          "positive_exit_rate": 0.5423728813559322,
          "source_row_count": 108
        },
        "reason": "grid_loosen_profit_threshold_direct",
        "selected_avg_incremental_exit_profit_pct": 0.48349206349206353,
        "selected_min_profit_pct": 1.2,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.48349206349206353,
          "avg_missed_upside_after_threshold_pct": 1.6695238095238096,
          "eligible_count": 63,
          "eligible_rate": 0.5833333333333334,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 30,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.3333333333333333,
          "min_profit_pct": 1.2,
          "positive_exit_count": 42,
          "positive_exit_rate": 0.6666666666666666,
          "source_row_count": 108
        },
        "status": "adjust_down"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 34,
      "recovered_or_extended_rate": 0.3148148148148148,
      "reversal_or_flat_count": 48,
      "reversal_or_flat_rate": 0.4444444444444444,
      "sample_count": 108,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-06.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-06:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-06.json"
  }
]
```
