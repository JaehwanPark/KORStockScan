# AI Score Optimization Backtest - 2026-07-09

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
    "sample_count": 34,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 22,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 12,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 22,
      "loss_or_flat_rate": 0.6470588235294118,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 12,
      "recovered_rate": 0.35294117647058826,
      "sample_count": 34,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-09.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-09:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-09.json"
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
    "sample_count": 150,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 48,
      "correctly_blocked_rate": 0.32,
      "label_counts": [
        {
          "count": 55,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 48,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 47,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 150,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.8137333333333333,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.1344230769230769,
          "avg_missed_upside_after_threshold_pct": 1.6008653846153846,
          "eligible_count": 104,
          "eligible_rate": 0.6933333333333334,
          "label_counts": [
            {
              "count": 47,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 44,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 13,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.3076923076923077,
          "min_profit_pct": 0.8,
          "positive_exit_count": 72,
          "positive_exit_rate": 0.6923076923076923,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.14938775510204078,
          "avg_missed_upside_after_threshold_pct": 1.5946938775510204,
          "eligible_count": 98,
          "eligible_rate": 0.6533333333333333,
          "label_counts": [
            {
              "count": 47,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 43,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.29591836734693877,
          "min_profit_pct": 0.9,
          "positive_exit_count": 69,
          "positive_exit_rate": 0.7040816326530612,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3435164835164835,
          "avg_missed_upside_after_threshold_pct": 1.613956043956044,
          "eligible_count": 91,
          "eligible_rate": 0.6066666666666667,
          "label_counts": [
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 40,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 25,
          "loss_or_flat_rate": 0.27472527472527475,
          "min_profit_pct": 1.0,
          "positive_exit_count": 66,
          "positive_exit_rate": 0.7252747252747253,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3149999999999999,
          "avg_missed_upside_after_threshold_pct": 1.5675,
          "eligible_count": 88,
          "eligible_rate": 0.5866666666666667,
          "label_counts": [
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 39,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.3522727272727273,
          "min_profit_pct": 1.1,
          "positive_exit_count": 57,
          "positive_exit_rate": 0.6477272727272727,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.33878048780487807,
          "avg_missed_upside_after_threshold_pct": 1.5790243902439023,
          "eligible_count": 82,
          "eligible_rate": 0.5466666666666666,
          "label_counts": [
            {
              "count": 43,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 36,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.35365853658536583,
          "min_profit_pct": 1.2,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.6463414634146342,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.38544303797468354,
          "avg_missed_upside_after_threshold_pct": 1.5373417721518987,
          "eligible_count": 79,
          "eligible_rate": 0.5266666666666666,
          "label_counts": [
            {
              "count": 42,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 35,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.3670886075949367,
          "min_profit_pct": 1.3,
          "positive_exit_count": 50,
          "positive_exit_rate": 0.6329113924050633,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3755128205128206,
          "avg_missed_upside_after_threshold_pct": 1.4562820512820513,
          "eligible_count": 78,
          "eligible_rate": 0.52,
          "label_counts": [
            {
              "count": 42,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 34,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4230769230769231,
          "min_profit_pct": 1.4,
          "positive_exit_count": 45,
          "positive_exit_rate": 0.5769230769230769,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3153333333333333,
          "avg_missed_upside_after_threshold_pct": 1.4132,
          "eligible_count": 75,
          "eligible_rate": 0.5,
          "label_counts": [
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 32,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.49333333333333335,
          "min_profit_pct": 1.5,
          "positive_exit_count": 38,
          "positive_exit_rate": 0.5066666666666667,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3447826086956521,
          "avg_missed_upside_after_threshold_pct": 1.432028985507246,
          "eligible_count": 69,
          "eligible_rate": 0.46,
          "label_counts": [
            {
              "count": 40,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 28,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4782608695652174,
          "min_profit_pct": 1.6,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.5217391304347826,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3753125,
          "avg_missed_upside_after_threshold_pct": 1.440625,
          "eligible_count": 64,
          "eligible_rate": 0.4266666666666667,
          "label_counts": [
            {
              "count": 37,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 27,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 1.7,
          "positive_exit_count": 32,
          "positive_exit_rate": 0.5,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.3147540983606557,
          "avg_missed_upside_after_threshold_pct": 1.4096721311475409,
          "eligible_count": 61,
          "eligible_rate": 0.4066666666666667,
          "label_counts": [
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 27,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.5081967213114754,
          "min_profit_pct": 1.8,
          "positive_exit_count": 30,
          "positive_exit_rate": 0.4918032786885246,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.26614035087719307,
          "avg_missed_upside_after_threshold_pct": 1.4049122807017544,
          "eligible_count": 57,
          "eligible_rate": 0.38,
          "label_counts": [
            {
              "count": 32,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.543859649122807,
          "min_profit_pct": 1.9,
          "positive_exit_count": 26,
          "positive_exit_rate": 0.45614035087719296,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.2623076923076923,
          "avg_missed_upside_after_threshold_pct": 1.438076923076923,
          "eligible_count": 52,
          "eligible_rate": 0.3466666666666667,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 23,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.5384615384615384,
          "min_profit_pct": 2.0,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.46153846153846156,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.2778723404255318,
          "avg_missed_upside_after_threshold_pct": 1.4868085106382978,
          "eligible_count": 47,
          "eligible_rate": 0.31333333333333335,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.5106382978723404,
          "min_profit_pct": 2.1,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.48936170212765956,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.2790476190476189,
          "avg_missed_upside_after_threshold_pct": 1.5592857142857142,
          "eligible_count": 42,
          "eligible_rate": 0.28,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 2.2,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.4505128205128207,
          "avg_missed_upside_after_threshold_pct": 1.5784615384615386,
          "eligible_count": 39,
          "eligible_rate": 0.26,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.46153846153846156,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5384615384615384,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.42756756756756764,
          "avg_missed_upside_after_threshold_pct": 1.5597297297297297,
          "eligible_count": 37,
          "eligible_rate": 0.24666666666666667,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 12,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.43243243243243246,
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5675675675675675,
          "source_row_count": 150
        },
        {
          "avg_incremental_exit_profit_pct": 0.4476470588235294,
          "avg_missed_upside_after_threshold_pct": 1.5944117647058824,
          "eligible_count": 34,
          "eligible_rate": 0.22666666666666666,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 14,
          "loss_or_flat_rate": 0.4117647058823529,
          "min_profit_pct": 2.5,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5882352941176471,
          "source_row_count": 150
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.1351794871794874,
        "current_avg_incremental_exit_profit_pct": 0.3153333333333333,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.3153333333333333,
          "avg_missed_upside_after_threshold_pct": 1.4132,
          "eligible_count": 75,
          "eligible_rate": 0.5,
          "label_counts": [
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 32,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.49333333333333335,
          "min_profit_pct": 1.5,
          "positive_exit_count": 38,
          "positive_exit_rate": 0.5066666666666667,
          "source_row_count": 150
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.4505128205128207,
        "selected_min_profit_pct": 2.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.4505128205128207,
          "avg_missed_upside_after_threshold_pct": 1.5784615384615386,
          "eligible_count": 39,
          "eligible_rate": 0.26,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.46153846153846156,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5384615384615384,
          "source_row_count": 150
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 47,
      "recovered_or_extended_rate": 0.31333333333333335,
      "reversal_or_flat_count": 55,
      "reversal_or_flat_rate": 0.36666666666666664,
      "sample_count": 150,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-09.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-09:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-09.json"
  }
]
```
