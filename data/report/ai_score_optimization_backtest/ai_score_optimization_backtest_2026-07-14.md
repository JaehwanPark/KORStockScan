# AI Score Optimization Backtest - 2026-07-14

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
    "sample_count": 39,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 26,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 13,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 26,
      "loss_or_flat_rate": 0.6666666666666666,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 13,
      "recovered_rate": 0.3333333333333333,
      "sample_count": 39,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-14.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-14:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-14.json"
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
    "sample_count": 165,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 56,
      "correctly_blocked_rate": 0.3393939393939394,
      "label_counts": [
        {
          "count": 60,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 56,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 49,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 165,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.7678181818181818,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.1481081081081081,
          "avg_missed_upside_after_threshold_pct": 1.5818918918918918,
          "eligible_count": 111,
          "eligible_rate": 0.6727272727272727,
          "label_counts": [
            {
              "count": 49,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 47,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 15,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 36,
          "loss_or_flat_rate": 0.32432432432432434,
          "min_profit_pct": 0.8,
          "positive_exit_count": 75,
          "positive_exit_rate": 0.6756756756756757,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.15619047619047613,
          "avg_missed_upside_after_threshold_pct": 1.5683809523809524,
          "eligible_count": 105,
          "eligible_rate": 0.6363636363636364,
          "label_counts": [
            {
              "count": 49,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 46,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 10,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.3142857142857143,
          "min_profit_pct": 0.9,
          "positive_exit_count": 72,
          "positive_exit_rate": 0.6857142857142857,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.32979591836734695,
          "avg_missed_upside_after_threshold_pct": 1.5772448979591835,
          "eligible_count": 98,
          "eligible_rate": 0.593939393939394,
          "label_counts": [
            {
              "count": 48,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 43,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 7,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 29,
          "loss_or_flat_rate": 0.29591836734693877,
          "min_profit_pct": 1.0,
          "positive_exit_count": 69,
          "positive_exit_rate": 0.7040816326530612,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.30585106382978716,
          "avg_missed_upside_after_threshold_pct": 1.542872340425532,
          "eligible_count": 94,
          "eligible_rate": 0.5696969696969697,
          "label_counts": [
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 42,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 6,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.3617021276595745,
          "min_profit_pct": 1.1,
          "positive_exit_count": 60,
          "positive_exit_rate": 0.6382978723404256,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.3297701149425287,
          "avg_missed_upside_after_threshold_pct": 1.5629885057471262,
          "eligible_count": 87,
          "eligible_rate": 0.5272727272727272,
          "label_counts": [
            {
              "count": 45,
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
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.3563218390804598,
          "min_profit_pct": 1.2,
          "positive_exit_count": 56,
          "positive_exit_rate": 0.6436781609195402,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.36738095238095236,
          "avg_missed_upside_after_threshold_pct": 1.5172619047619047,
          "eligible_count": 84,
          "eligible_rate": 0.509090909090909,
          "label_counts": [
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 37,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.36904761904761907,
          "min_profit_pct": 1.3,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.6309523809523809,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.35180722891566274,
          "avg_missed_upside_after_threshold_pct": 1.4348192771084338,
          "eligible_count": 83,
          "eligible_rate": 0.503030303030303,
          "label_counts": [
            {
              "count": 44,
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
          "loss_or_flat_count": 35,
          "loss_or_flat_rate": 0.42168674698795183,
          "min_profit_pct": 1.4,
          "positive_exit_count": 48,
          "positive_exit_rate": 0.5783132530120482,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.3039240506329114,
          "avg_missed_upside_after_threshold_pct": 1.4062025316455697,
          "eligible_count": 79,
          "eligible_rate": 0.47878787878787876,
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
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 38,
          "loss_or_flat_rate": 0.4810126582278481,
          "min_profit_pct": 1.5,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.5189873417721519,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.32534246575342457,
          "avg_missed_upside_after_threshold_pct": 1.417945205479452,
          "eligible_count": 73,
          "eligible_rate": 0.44242424242424244,
          "label_counts": [
            {
              "count": 41,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 30,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.4657534246575342,
          "min_profit_pct": 1.6,
          "positive_exit_count": 39,
          "positive_exit_rate": 0.5342465753424658,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.3467647058823529,
          "avg_missed_upside_after_threshold_pct": 1.4191176470588236,
          "eligible_count": 68,
          "eligible_rate": 0.4121212121212121,
          "label_counts": [
            {
              "count": 38,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 1.7,
          "positive_exit_count": 34,
          "positive_exit_rate": 0.5,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.28246153846153843,
          "avg_missed_upside_after_threshold_pct": 1.382923076923077,
          "eligible_count": 65,
          "eligible_rate": 0.3939393939393939,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.5076923076923077,
          "min_profit_pct": 1.8,
          "positive_exit_count": 32,
          "positive_exit_rate": 0.49230769230769234,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.22836065573770498,
          "avg_missed_upside_after_threshold_pct": 1.3701639344262295,
          "eligible_count": 61,
          "eligible_rate": 0.3696969696969697,
          "label_counts": [
            {
              "count": 33,
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
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.5409836065573771,
          "min_profit_pct": 1.9,
          "positive_exit_count": 28,
          "positive_exit_rate": 0.45901639344262296,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.21818181818181817,
          "avg_missed_upside_after_threshold_pct": 1.4176363636363636,
          "eligible_count": 55,
          "eligible_rate": 0.3333333333333333,
          "label_counts": [
            {
              "count": 29,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.5636363636363636,
          "min_profit_pct": 2.0,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.43636363636363634,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.22239999999999988,
          "avg_missed_upside_after_threshold_pct": 1.4554,
          "eligible_count": 50,
          "eligible_rate": 0.30303030303030304,
          "label_counts": [
            {
              "count": 28,
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
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.54,
          "min_profit_pct": 2.1,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.46,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.21066666666666645,
          "avg_missed_upside_after_threshold_pct": 1.5128888888888885,
          "eligible_count": 45,
          "eligible_rate": 0.2727272727272727,
          "label_counts": [
            {
              "count": 26,
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
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.5333333333333333,
          "min_profit_pct": 2.2,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4666666666666667,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.357857142857143,
          "avg_missed_upside_after_threshold_pct": 1.5202380952380954,
          "eligible_count": 42,
          "eligible_rate": 0.2545454545454545,
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
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.32450000000000007,
          "avg_missed_upside_after_threshold_pct": 1.4925000000000002,
          "eligible_count": 40,
          "eligible_rate": 0.24242424242424243,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 19,
          "loss_or_flat_rate": 0.475,
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.525,
          "source_row_count": 165
        },
        {
          "avg_incremental_exit_profit_pct": 0.3264864864864864,
          "avg_missed_upside_after_threshold_pct": 1.5108108108108107,
          "eligible_count": 37,
          "eligible_rate": 0.22424242424242424,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 13,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 17,
          "loss_or_flat_rate": 0.4594594594594595,
          "min_profit_pct": 2.5,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5405405405405406,
          "source_row_count": 165
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.06345690174804097,
        "current_avg_incremental_exit_profit_pct": 0.3039240506329114,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.3039240506329114,
          "avg_missed_upside_after_threshold_pct": 1.4062025316455697,
          "eligible_count": 79,
          "eligible_rate": 0.47878787878787876,
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
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 38,
          "loss_or_flat_rate": 0.4810126582278481,
          "min_profit_pct": 1.5,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.5189873417721519,
          "source_row_count": 165
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.36738095238095236,
        "selected_min_profit_pct": 1.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.36738095238095236,
          "avg_missed_upside_after_threshold_pct": 1.5172619047619047,
          "eligible_count": 84,
          "eligible_rate": 0.509090909090909,
          "label_counts": [
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 37,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.36904761904761907,
          "min_profit_pct": 1.3,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.6309523809523809,
          "source_row_count": 165
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 49,
      "recovered_or_extended_rate": 0.296969696969697,
      "reversal_or_flat_count": 60,
      "reversal_or_flat_rate": 0.36363636363636365,
      "sample_count": 165,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-14.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-14:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-14.json"
  }
]
```
