# AI Score Optimization Backtest - 2026-07-08

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
    "sample_count": 33,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 21,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 12,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 21,
      "loss_or_flat_rate": 0.6363636363636364,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 12,
      "recovered_rate": 0.36363636363636365,
      "sample_count": 33,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-08.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-08:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-08.json"
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
    "sample_count": 145,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 46,
      "correctly_blocked_rate": 0.31724137931034485,
      "label_counts": [
        {
          "count": 53,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 46,
          "label": "pyramid_would_have_helped"
        },
        {
          "count": 46,
          "label": "pyramid_correctly_blocked"
        }
      ],
      "one_share_closed_pyramid_row_count": 145,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.8306206896551724,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.1667326732673267,
          "avg_missed_upside_after_threshold_pct": 1.6051485148514852,
          "eligible_count": 101,
          "eligible_rate": 0.696551724137931,
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
              "count": 13,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.3069306930693069,
          "min_profit_pct": 0.8,
          "positive_exit_count": 70,
          "positive_exit_rate": 0.693069306930693,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.18736842105263155,
          "avg_missed_upside_after_threshold_pct": 1.6022105263157895,
          "eligible_count": 95,
          "eligible_rate": 0.6551724137931034,
          "label_counts": [
            {
              "count": 46,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 41,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.29473684210526313,
          "min_profit_pct": 0.9,
          "positive_exit_count": 67,
          "positive_exit_rate": 0.7052631578947368,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.39454545454545453,
          "avg_missed_upside_after_threshold_pct": 1.6261363636363635,
          "eligible_count": 88,
          "eligible_rate": 0.6068965517241379,
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
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.2727272727272727,
          "min_profit_pct": 1.0,
          "positive_exit_count": 64,
          "positive_exit_rate": 0.7272727272727273,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.3703529411764705,
          "avg_missed_upside_after_threshold_pct": 1.582,
          "eligible_count": 85,
          "eligible_rate": 0.5862068965517241,
          "label_counts": [
            {
              "count": 43,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 37,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.35294117647058826,
          "min_profit_pct": 1.1,
          "positive_exit_count": 55,
          "positive_exit_rate": 0.6470588235294118,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.4030379746835443,
          "avg_missed_upside_after_threshold_pct": 1.598860759493671,
          "eligible_count": 79,
          "eligible_rate": 0.5448275862068965,
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
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.35443037974683544,
          "min_profit_pct": 1.2,
          "positive_exit_count": 51,
          "positive_exit_rate": 0.6455696202531646,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.4580263157894736,
          "avg_missed_upside_after_threshold_pct": 1.5602631578947368,
          "eligible_count": 76,
          "eligible_rate": 0.5241379310344828,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.3684210526315789,
          "min_profit_pct": 1.3,
          "positive_exit_count": 48,
          "positive_exit_rate": 0.631578947368421,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.35802631578947375,
          "avg_missed_upside_after_threshold_pct": 1.460263157894737,
          "eligible_count": 76,
          "eligible_rate": 0.5241379310344828,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4342105263157895,
          "min_profit_pct": 1.4,
          "positive_exit_count": 43,
          "positive_exit_rate": 0.5657894736842105,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.2982191780821918,
          "avg_missed_upside_after_threshold_pct": 1.4189041095890411,
          "eligible_count": 73,
          "eligible_rate": 0.503448275862069,
          "label_counts": [
            {
              "count": 40,
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
          "loss_or_flat_count": 36,
          "loss_or_flat_rate": 0.4931506849315068,
          "min_profit_pct": 1.5,
          "positive_exit_count": 37,
          "positive_exit_rate": 0.5068493150684932,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.3299999999999999,
          "avg_missed_upside_after_threshold_pct": 1.4417910447761193,
          "eligible_count": 67,
          "eligible_rate": 0.46206896551724136,
          "label_counts": [
            {
              "count": 39,
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
          "loss_or_flat_rate": 0.47761194029850745,
          "min_profit_pct": 1.6,
          "positive_exit_count": 35,
          "positive_exit_rate": 0.5223880597014925,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.3635483870967742,
          "avg_missed_upside_after_threshold_pct": 1.4546774193548386,
          "eligible_count": 62,
          "eligible_rate": 0.42758620689655175,
          "label_counts": [
            {
              "count": 36,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 26,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 1.7,
          "positive_exit_count": 31,
          "positive_exit_rate": 0.5,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.303728813559322,
          "avg_missed_upside_after_threshold_pct": 1.426779661016949,
          "eligible_count": 59,
          "eligible_rate": 0.4068965517241379,
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
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.5084745762711864,
          "min_profit_pct": 1.8,
          "positive_exit_count": 29,
          "positive_exit_rate": 0.4915254237288136,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.24321428571428577,
          "avg_missed_upside_after_threshold_pct": 1.4007142857142856,
          "eligible_count": 56,
          "eligible_rate": 0.38620689655172413,
          "label_counts": [
            {
              "count": 31,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 25,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.5535714285714286,
          "min_profit_pct": 1.9,
          "positive_exit_count": 25,
          "positive_exit_rate": 0.44642857142857145,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.23901960784313725,
          "avg_missed_upside_after_threshold_pct": 1.436078431372549,
          "eligible_count": 51,
          "eligible_rate": 0.35172413793103446,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 23,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.5490196078431373,
          "min_profit_pct": 2.0,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.45098039215686275,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.2545652173913043,
          "avg_missed_upside_after_threshold_pct": 1.4878260869565216,
          "eligible_count": 46,
          "eligible_rate": 0.31724137931034485,
          "label_counts": [
            {
              "count": 27,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 19,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 24,
          "loss_or_flat_rate": 0.5217391304347826,
          "min_profit_pct": 2.1,
          "positive_exit_count": 22,
          "positive_exit_rate": 0.4782608695652174,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.25536585365853637,
          "avg_missed_upside_after_threshold_pct": 1.5646341463414632,
          "eligible_count": 41,
          "eligible_rate": 0.2827586206896552,
          "label_counts": [
            {
              "count": 25,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 16,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 21,
          "loss_or_flat_rate": 0.5121951219512195,
          "min_profit_pct": 2.2,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.4878048780487805,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.4321052631578949,
          "avg_missed_upside_after_threshold_pct": 1.5873684210526318,
          "eligible_count": 38,
          "eligible_rate": 0.2620689655172414,
          "label_counts": [
            {
              "count": 24,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 18,
          "loss_or_flat_rate": 0.47368421052631576,
          "min_profit_pct": 2.3,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5263157894736842,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.4102777777777778,
          "avg_missed_upside_after_threshold_pct": 1.571388888888889,
          "eligible_count": 36,
          "eligible_rate": 0.2482758620689655,
          "label_counts": [
            {
              "count": 24,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 12,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.4444444444444444,
          "min_profit_pct": 2.4,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5555555555555556,
          "source_row_count": 145
        },
        {
          "avg_incremental_exit_profit_pct": 0.43242424242424243,
          "avg_missed_upside_after_threshold_pct": 1.6112121212121213,
          "eligible_count": 33,
          "eligible_rate": 0.22758620689655173,
          "label_counts": [
            {
              "count": 22,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 11,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 14,
          "loss_or_flat_rate": 0.42424242424242425,
          "min_profit_pct": 2.5,
          "positive_exit_count": 19,
          "positive_exit_rate": 0.5757575757575758,
          "source_row_count": 145
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.15980713770728183,
        "current_avg_incremental_exit_profit_pct": 0.2982191780821918,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.2982191780821918,
          "avg_missed_upside_after_threshold_pct": 1.4189041095890411,
          "eligible_count": 73,
          "eligible_rate": 0.503448275862069,
          "label_counts": [
            {
              "count": 40,
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
          "loss_or_flat_count": 36,
          "loss_or_flat_rate": 0.4931506849315068,
          "min_profit_pct": 1.5,
          "positive_exit_count": 37,
          "positive_exit_rate": 0.5068493150684932,
          "source_row_count": 145
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.4580263157894736,
        "selected_min_profit_pct": 1.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.4580263157894736,
          "avg_missed_upside_after_threshold_pct": 1.5602631578947368,
          "eligible_count": 76,
          "eligible_rate": 0.5241379310344828,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 28,
          "loss_or_flat_rate": 0.3684210526315789,
          "min_profit_pct": 1.3,
          "positive_exit_count": 48,
          "positive_exit_rate": 0.631578947368421,
          "source_row_count": 145
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 46,
      "recovered_or_extended_rate": 0.31724137931034485,
      "reversal_or_flat_count": 53,
      "reversal_or_flat_rate": 0.36551724137931035,
      "sample_count": 145,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-08.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-08:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-08.json"
  }
]
```
