# AI Score Optimization Backtest - 2026-07-03

- calibration_state: `candidate_ready`
- allowed_runtime_apply: `True`
- calibration_candidate_count: `2`
- allowed_runtime_apply_candidate_count: `1`
- diagnostic_only_candidate_count: `2`

## Blocked Reasons

- `hold_sample`: `1`

## Calibration Candidates

```json
[
  {
    "actual_order_submitted": false,
    "allowed_runtime_apply": false,
    "broker_order_forbidden": true,
    "calibration_reason": "rolling_closed_first_touch_rows_lt_10",
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
    "sample_count": 7,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 4,
          "label": "first_touch_recovered_profit"
        },
        {
          "count": 3,
          "label": "first_touch_loss_or_flat"
        }
      ],
      "loss_or_flat_count": 3,
      "loss_or_flat_rate": 0.42857142857142855,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "rolling_closed_first_touch_rows_lt_10",
      "recovered_count": 4,
      "recovered_rate": 0.5714285714285714,
      "sample_count": 7,
      "source_quality_pass": true
    },
    "source_reports": [
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-02.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-03.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-03:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "source_quality_gate": "pass",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-03.json"
  },
  {
    "actual_order_submitted": false,
    "allowed_runtime_apply": true,
    "broker_order_forbidden": true,
    "calibration_reason": "grid_loosen_profit_threshold_direct",
    "calibration_state": "adjust_down",
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
      "min_profit_pct": 1.1,
      "min_tick_accel": 0.5,
      "strong_continuation_enabled": false,
      "strong_continuation_max_drawdown_pct": 0.2,
      "strong_continuation_min_profit_pct": 0.9
    },
    "runtime_effect": false,
    "safety_revert_required": false,
    "sample_count": 90,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 15,
      "correctly_blocked_rate": 0.16666666666666666,
      "label_counts": [
        {
          "count": 45,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 30,
          "label": "pyramid_would_have_helped"
        },
        {
          "count": 15,
          "label": "pyramid_correctly_blocked"
        }
      ],
      "one_share_closed_pyramid_row_count": 90,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.9561111111111111,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.3180597014925373,
          "avg_missed_upside_after_threshold_pct": 1.793134328358209,
          "eligible_count": 67,
          "eligible_rate": 0.7444444444444445,
          "label_counts": [
            {
              "count": 36,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 30,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 17,
          "loss_or_flat_rate": 0.2537313432835821,
          "min_profit_pct": 0.8,
          "positive_exit_count": 50,
          "positive_exit_rate": 0.746268656716418,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.2853030303030303,
          "avg_missed_upside_after_threshold_pct": 1.7192424242424242,
          "eligible_count": 66,
          "eligible_rate": 0.7333333333333333,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 30,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.24242424242424243,
          "min_profit_pct": 0.9,
          "positive_exit_count": 50,
          "positive_exit_rate": 0.7575757575757576,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.5545901639344262,
          "avg_missed_upside_after_threshold_pct": 1.7563934426229508,
          "eligible_count": 61,
          "eligible_rate": 0.6777777777777778,
          "label_counts": [
            {
              "count": 32,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 29,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 13,
          "loss_or_flat_rate": 0.21311475409836064,
          "min_profit_pct": 1.0,
          "positive_exit_count": 48,
          "positive_exit_rate": 0.7868852459016393,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.5608474576271186,
          "avg_missed_upside_after_threshold_pct": 1.7152542372881354,
          "eligible_count": 59,
          "eligible_rate": 0.6555555555555556,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 17,
          "loss_or_flat_rate": 0.288135593220339,
          "min_profit_pct": 1.1,
          "positive_exit_count": 42,
          "positive_exit_rate": 0.711864406779661,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.5321428571428571,
          "avg_missed_upside_after_threshold_pct": 1.7051785714285714,
          "eligible_count": 56,
          "eligible_rate": 0.6222222222222222,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 27,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 17,
          "loss_or_flat_rate": 0.30357142857142855,
          "min_profit_pct": 1.2,
          "positive_exit_count": 39,
          "positive_exit_rate": 0.6964285714285714,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.4994444444444444,
          "avg_missed_upside_after_threshold_pct": 1.6659259259259258,
          "eligible_count": 54,
          "eligible_rate": 0.6,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.3333333333333333,
          "min_profit_pct": 1.3,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.6666666666666666,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.3994444444444445,
          "avg_missed_upside_after_threshold_pct": 1.565925925925926,
          "eligible_count": 54,
          "eligible_rate": 0.6,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.3888888888888889,
          "min_profit_pct": 1.4,
          "positive_exit_count": 33,
          "positive_exit_rate": 0.6111111111111112,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.3269811320754717,
          "avg_missed_upside_after_threshold_pct": 1.4943396226415095,
          "eligible_count": 53,
          "eligible_rate": 0.5888888888888889,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.4528301886792453,
          "min_profit_pct": 1.5,
          "positive_exit_count": 29,
          "positive_exit_rate": 0.5471698113207547,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.2779999999999999,
          "avg_missed_upside_after_threshold_pct": 1.4813999999999998,
          "eligible_count": 50,
          "eligible_rate": 0.5555555555555556,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 24,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.46,
          "min_profit_pct": 1.6,
          "positive_exit_count": 27,
          "positive_exit_rate": 0.54,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.29229166666666667,
          "avg_missed_upside_after_threshold_pct": 1.4410416666666668,
          "eligible_count": 48,
          "eligible_rate": 0.5333333333333333,
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
          "loss_or_flat_count": 25,
          "loss_or_flat_rate": 0.5208333333333334,
          "min_profit_pct": 1.7,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.4791666666666667,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.21170212765957444,
          "avg_missed_upside_after_threshold_pct": 1.371063829787234,
          "eligible_count": 47,
          "eligible_rate": 0.5222222222222223,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 22,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.5531914893617021,
          "min_profit_pct": 1.8,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.44680851063829785,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.13600000000000007,
          "avg_missed_upside_after_threshold_pct": 1.328888888888889,
          "eligible_count": 45,
          "eligible_rate": 0.5,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 20,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.6,
          "min_profit_pct": 1.9,
          "positive_exit_count": 18,
          "positive_exit_rate": 0.4,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.08333333333333334,
          "avg_missed_upside_after_threshold_pct": 1.322142857142857,
          "eligible_count": 42,
          "eligible_rate": 0.4666666666666667,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 19,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 25,
          "loss_or_flat_rate": 0.5952380952380952,
          "min_profit_pct": 2.0,
          "positive_exit_count": 17,
          "positive_exit_rate": 0.40476190476190477,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.10594594594594585,
          "avg_missed_upside_after_threshold_pct": 1.3954054054054053,
          "eligible_count": 37,
          "eligible_rate": 0.4111111111111111,
          "label_counts": [
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 18,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.5675675675675675,
          "min_profit_pct": 2.1,
          "positive_exit_count": 16,
          "positive_exit_rate": 0.43243243243243246,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.11187499999999981,
          "avg_missed_upside_after_threshold_pct": 1.5074999999999998,
          "eligible_count": 32,
          "eligible_rate": 0.35555555555555557,
          "label_counts": [
            {
              "count": 16,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.5625,
          "min_profit_pct": 2.2,
          "positive_exit_count": 14,
          "positive_exit_rate": 0.4375,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.3596551724137933,
          "avg_missed_upside_after_threshold_pct": 1.5624137931034483,
          "eligible_count": 29,
          "eligible_rate": 0.32222222222222224,
          "label_counts": [
            {
              "count": 15,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 15,
          "loss_or_flat_rate": 0.5172413793103449,
          "min_profit_pct": 2.3,
          "positive_exit_count": 14,
          "positive_exit_rate": 0.4827586206896552,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.35851851851851857,
          "avg_missed_upside_after_threshold_pct": 1.5725925925925925,
          "eligible_count": 27,
          "eligible_rate": 0.3,
          "label_counts": [
            {
              "count": 15,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 12,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 13,
          "loss_or_flat_rate": 0.48148148148148145,
          "min_profit_pct": 2.4,
          "positive_exit_count": 14,
          "positive_exit_rate": 0.5185185185185185,
          "source_row_count": 90
        },
        {
          "avg_incremental_exit_profit_pct": 0.42,
          "avg_missed_upside_after_threshold_pct": 1.665,
          "eligible_count": 24,
          "eligible_rate": 0.26666666666666666,
          "label_counts": [
            {
              "count": 13,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 11,
          "loss_or_flat_rate": 0.4583333333333333,
          "min_profit_pct": 2.5,
          "positive_exit_count": 13,
          "positive_exit_rate": 0.5416666666666666,
          "source_row_count": 90
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.23386632555164694,
        "current_avg_incremental_exit_profit_pct": 0.3269811320754717,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.3269811320754717,
          "avg_missed_upside_after_threshold_pct": 1.4943396226415095,
          "eligible_count": 53,
          "eligible_rate": 0.5888888888888889,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.4528301886792453,
          "min_profit_pct": 1.5,
          "positive_exit_count": 29,
          "positive_exit_rate": 0.5471698113207547,
          "source_row_count": 90
        },
        "reason": "grid_loosen_profit_threshold_direct",
        "selected_avg_incremental_exit_profit_pct": 0.5608474576271186,
        "selected_min_profit_pct": 1.1,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.5608474576271186,
          "avg_missed_upside_after_threshold_pct": 1.7152542372881354,
          "eligible_count": 59,
          "eligible_rate": 0.6555555555555556,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            }
          ],
          "loss_or_flat_count": 17,
          "loss_or_flat_rate": 0.288135593220339,
          "min_profit_pct": 1.1,
          "positive_exit_count": 42,
          "positive_exit_rate": 0.711864406779661,
          "source_row_count": 90
        },
        "status": "adjust_down"
      },
      "provenance_present": true,
      "recommended_action": "adjust_down",
      "recommended_action_reason": "grid_loosen_profit_threshold_direct",
      "recovered_or_extended_count": 30,
      "recovered_or_extended_rate": 0.3333333333333333,
      "reversal_or_flat_count": 45,
      "reversal_or_flat_rate": 0.5,
      "sample_count": 90,
      "source_quality_pass": true
    },
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-03.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [
      "SCALPING_PYRAMID_MIN_PROFIT_PCT",
      "SCALPING_PYRAMID_MIN_AI_SCORE",
      "SCALPING_PYRAMID_MIN_BUY_PRESSURE",
      "SCALPING_PYRAMID_MIN_TICK_ACCEL",
      "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS",
      "SCALPING_PYRAMID_MAX_SPREAD_BPS",
      "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED",
      "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT",
      "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT"
    ],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-03:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": true,
    "source_quality_gate": "pass",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-03.json"
  }
]
```
