# AI Score Optimization Backtest - 2026-07-22

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
    "sample_count": 47,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 34,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 13,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 34,
      "loss_or_flat_rate": 0.723404255319149,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 13,
      "recovered_rate": 0.2765957446808511,
      "sample_count": 47,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-21.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-22.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-22:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-22.json"
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
    "sample_count": 206,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 64,
      "correctly_blocked_rate": 0.3106796116504854,
      "label_counts": [
        {
          "count": 91,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 64,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 51,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 206,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.6525728155339806,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.06857142857142855,
          "avg_missed_upside_after_threshold_pct": 1.4623571428571427,
          "eligible_count": 140,
          "eligible_rate": 0.6796116504854369,
          "label_counts": [
            {
              "count": 73,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 51,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 56,
          "loss_or_flat_rate": 0.4,
          "min_profit_pct": 0.8,
          "positive_exit_count": 84,
          "positive_exit_rate": 0.6,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.05375939849624057,
          "avg_missed_upside_after_threshold_pct": 1.4362406015037594,
          "eligible_count": 133,
          "eligible_rate": 0.6456310679611651,
          "label_counts": [
            {
              "count": 71,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 51,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 52,
          "loss_or_flat_rate": 0.39097744360902253,
          "min_profit_pct": 0.9,
          "positive_exit_count": 81,
          "positive_exit_rate": 0.6090225563909775,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.18524193548387097,
          "avg_missed_upside_after_threshold_pct": 1.437258064516129,
          "eligible_count": 124,
          "eligible_rate": 0.6019417475728155,
          "label_counts": [
            {
              "count": 66,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 50,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 47,
          "loss_or_flat_rate": 0.3790322580645161,
          "min_profit_pct": 1.0,
          "positive_exit_count": 77,
          "positive_exit_rate": 0.6209677419354839,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.14932773109243688,
          "avg_missed_upside_after_threshold_pct": 1.3962184873949577,
          "eligible_count": 119,
          "eligible_rate": 0.5776699029126213,
          "label_counts": [
            {
              "count": 64,
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
          "loss_or_flat_count": 52,
          "loss_or_flat_rate": 0.4369747899159664,
          "min_profit_pct": 1.1,
          "positive_exit_count": 67,
          "positive_exit_rate": 0.5630252100840336,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.14522522522522524,
          "avg_missed_upside_after_threshold_pct": 1.3934234234234233,
          "eligible_count": 111,
          "eligible_rate": 0.5388349514563107,
          "label_counts": [
            {
              "count": 59,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 47,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 48,
          "loss_or_flat_rate": 0.43243243243243246,
          "min_profit_pct": 1.2,
          "positive_exit_count": 63,
          "positive_exit_rate": 0.5675675675675675,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.1879807692307692,
          "avg_missed_upside_after_threshold_pct": 1.3840384615384616,
          "eligible_count": 104,
          "eligible_rate": 0.5048543689320388,
          "label_counts": [
            {
              "count": 55,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 46,
          "loss_or_flat_rate": 0.4423076923076923,
          "min_profit_pct": 1.3,
          "positive_exit_count": 58,
          "positive_exit_rate": 0.5576923076923077,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.1844554455445545,
          "avg_missed_upside_after_threshold_pct": 1.3231683168316832,
          "eligible_count": 101,
          "eligible_rate": 0.49029126213592233,
          "label_counts": [
            {
              "count": 52,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 48,
          "loss_or_flat_rate": 0.4752475247524752,
          "min_profit_pct": 1.4,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.5247524752475248,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.16117021276595744,
          "avg_missed_upside_after_threshold_pct": 1.3198936170212765,
          "eligible_count": 94,
          "eligible_rate": 0.4563106796116505,
          "label_counts": [
            {
              "count": 47,
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
          "loss_or_flat_count": 50,
          "loss_or_flat_rate": 0.5319148936170213,
          "min_profit_pct": 1.5,
          "positive_exit_count": 44,
          "positive_exit_rate": 0.46808510638297873,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.1827906976744185,
          "avg_missed_upside_after_threshold_pct": 1.3375581395348837,
          "eligible_count": 86,
          "eligible_rate": 0.4174757281553398,
          "label_counts": [
            {
              "count": 42,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 42,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 45,
          "loss_or_flat_rate": 0.5232558139534884,
          "min_profit_pct": 1.6,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.47674418604651164,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.22050632911392404,
          "avg_missed_upside_after_threshold_pct": 1.3534177215189873,
          "eligible_count": 79,
          "eligible_rate": 0.38349514563106796,
          "label_counts": [
            {
              "count": 39,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 39,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 43,
          "loss_or_flat_rate": 0.5443037974683544,
          "min_profit_pct": 1.7,
          "positive_exit_count": 36,
          "positive_exit_rate": 0.45569620253164556,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.14605263157894735,
          "avg_missed_upside_after_threshold_pct": 1.3053947368421053,
          "eligible_count": 76,
          "eligible_rate": 0.36893203883495146,
          "label_counts": [
            {
              "count": 39,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 36,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 42,
          "loss_or_flat_rate": 0.5526315789473685,
          "min_profit_pct": 1.8,
          "positive_exit_count": 34,
          "positive_exit_rate": 0.4473684210526316,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.09314285714285721,
          "avg_missed_upside_after_threshold_pct": 1.3130000000000002,
          "eligible_count": 70,
          "eligible_rate": 0.33980582524271846,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 40,
          "loss_or_flat_rate": 0.5714285714285714,
          "min_profit_pct": 1.9,
          "positive_exit_count": 30,
          "positive_exit_rate": 0.42857142857142855,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.09225806451612903,
          "avg_missed_upside_after_threshold_pct": 1.3787096774193548,
          "eligible_count": 62,
          "eligible_rate": 0.30097087378640774,
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
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 36,
          "loss_or_flat_rate": 0.5806451612903226,
          "min_profit_pct": 2.0,
          "positive_exit_count": 26,
          "positive_exit_rate": 0.41935483870967744,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.07263157894736831,
          "avg_missed_upside_after_threshold_pct": 1.396140350877193,
          "eligible_count": 57,
          "eligible_rate": 0.2766990291262136,
          "label_counts": [
            {
              "count": 29,
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
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5614035087719298,
          "min_profit_pct": 2.1,
          "positive_exit_count": 25,
          "positive_exit_rate": 0.43859649122807015,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.08559999999999979,
          "avg_missed_upside_after_threshold_pct": 1.4869999999999999,
          "eligible_count": 50,
          "eligible_rate": 0.24271844660194175,
          "label_counts": [
            {
              "count": 27,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 22,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.54,
          "min_profit_pct": 2.2,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.46,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.22000000000000017,
          "avg_missed_upside_after_threshold_pct": 1.5150000000000003,
          "eligible_count": 46,
          "eligible_rate": 0.22330097087378642,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.5217391304347826,
          "min_profit_pct": 2.3,
          "positive_exit_count": 22,
          "positive_exit_rate": 0.4782608695652174,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.23604651162790702,
          "avg_missed_upside_after_threshold_pct": 1.5169767441860467,
          "eligible_count": 43,
          "eligible_rate": 0.2087378640776699,
          "label_counts": [
            {
              "count": 26,
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
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.5116279069767442,
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4883720930232558,
          "source_row_count": 206
        },
        {
          "avg_incremental_exit_profit_pct": 0.22374999999999998,
          "avg_missed_upside_after_threshold_pct": 1.5282499999999999,
          "eligible_count": 40,
          "eligible_rate": 0.1941747572815534,
          "label_counts": [
            {
              "count": 24,
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
          "loss_or_flat_count": 20,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 2.5,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5,
          "source_row_count": 206
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.07487629886194958,
        "current_avg_incremental_exit_profit_pct": 0.16117021276595744,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.16117021276595744,
          "avg_missed_upside_after_threshold_pct": 1.3198936170212765,
          "eligible_count": 94,
          "eligible_rate": 0.4563106796116505,
          "label_counts": [
            {
              "count": 47,
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
          "loss_or_flat_count": 50,
          "loss_or_flat_rate": 0.5319148936170213,
          "min_profit_pct": 1.5,
          "positive_exit_count": 44,
          "positive_exit_rate": 0.46808510638297873,
          "source_row_count": 206
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.23604651162790702,
        "selected_min_profit_pct": 2.4,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.23604651162790702,
          "avg_missed_upside_after_threshold_pct": 1.5169767441860467,
          "eligible_count": 43,
          "eligible_rate": 0.2087378640776699,
          "label_counts": [
            {
              "count": 26,
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
          "loss_or_flat_count": 22,
          "loss_or_flat_rate": 0.5116279069767442,
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4883720930232558,
          "source_row_count": 206
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 51,
      "recovered_or_extended_rate": 0.24757281553398058,
      "reversal_or_flat_count": 91,
      "reversal_or_flat_rate": 0.441747572815534,
      "sample_count": 206,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-21.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-22.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-22:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-22.json"
  }
]
```
