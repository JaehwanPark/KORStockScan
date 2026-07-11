# AI Score Optimization Backtest - 2026-07-10

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
    "sample_count": 37,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 25,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 12,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 25,
      "loss_or_flat_rate": 0.6756756756756757,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 12,
      "recovered_rate": 0.32432432432432434,
      "sample_count": 37,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-10.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-10:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-10.json"
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
    "sample_count": 159,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 51,
      "correctly_blocked_rate": 0.32075471698113206,
      "label_counts": [
        {
          "count": 60,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 51,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 48,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 159,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.7813207547169811,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.14546296296296293,
          "avg_missed_upside_after_threshold_pct": 1.592037037037037,
          "eligible_count": 108,
          "eligible_rate": 0.6792452830188679,
          "label_counts": [
            {
              "count": 48,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 47,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 13,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.3148148148148148,
          "min_profit_pct": 0.8,
          "positive_exit_count": 74,
          "positive_exit_rate": 0.6851851851851852,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.15656862745098035,
          "avg_missed_upside_after_threshold_pct": 1.5816666666666666,
          "eligible_count": 102,
          "eligible_rate": 0.6415094339622641,
          "label_counts": [
            {
              "count": 48,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 46,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.30392156862745096,
          "min_profit_pct": 0.9,
          "positive_exit_count": 71,
          "positive_exit_rate": 0.696078431372549,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.3388421052631579,
          "avg_missed_upside_after_threshold_pct": 1.5949473684210527,
          "eligible_count": 95,
          "eligible_rate": 0.5974842767295597,
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
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.28421052631578947,
          "min_profit_pct": 1.0,
          "positive_exit_count": 68,
          "positive_exit_rate": 0.7157894736842105,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.30706521739130427,
          "avg_missed_upside_after_threshold_pct": 1.5455434782608695,
          "eligible_count": 92,
          "eligible_rate": 0.5786163522012578,
          "label_counts": [
            {
              "count": 45,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 42,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.358695652173913,
          "min_profit_pct": 1.1,
          "positive_exit_count": 59,
          "positive_exit_rate": 0.6413043478260869,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.334,
          "avg_missed_upside_after_threshold_pct": 1.5687058823529412,
          "eligible_count": 85,
          "eligible_rate": 0.5345911949685535,
          "label_counts": [
            {
              "count": 44,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 38,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.35294117647058826,
          "min_profit_pct": 1.2,
          "positive_exit_count": 55,
          "positive_exit_rate": 0.6470588235294118,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.3751219512195122,
          "avg_missed_upside_after_threshold_pct": 1.5245121951219511,
          "eligible_count": 82,
          "eligible_rate": 0.5157232704402516,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.36585365853658536,
          "min_profit_pct": 1.3,
          "positive_exit_count": 52,
          "positive_exit_rate": 0.6341463414634146,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.36172839506172844,
          "avg_missed_upside_after_threshold_pct": 1.4425925925925926,
          "eligible_count": 81,
          "eligible_rate": 0.5094339622641509,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.41975308641975306,
          "min_profit_pct": 1.4,
          "positive_exit_count": 47,
          "positive_exit_rate": 0.5802469135802469,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.3157142857142857,
          "avg_missed_upside_after_threshold_pct": 1.4162337662337663,
          "eligible_count": 77,
          "eligible_rate": 0.48427672955974843,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.4805194805194805,
          "min_profit_pct": 1.5,
          "positive_exit_count": 40,
          "positive_exit_rate": 0.5194805194805194,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.34154929577464777,
          "avg_missed_upside_after_threshold_pct": 1.4319718309859153,
          "eligible_count": 71,
          "eligible_rate": 0.44654088050314467,
          "label_counts": [
            {
              "count": 40,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 30,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4647887323943662,
          "min_profit_pct": 1.6,
          "positive_exit_count": 38,
          "positive_exit_rate": 0.5352112676056338,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.3678787878787879,
          "avg_missed_upside_after_threshold_pct": 1.4372727272727273,
          "eligible_count": 66,
          "eligible_rate": 0.41509433962264153,
          "label_counts": [
            {
              "count": 37,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 1.7,
          "positive_exit_count": 33,
          "positive_exit_rate": 0.5,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.30571428571428566,
          "avg_missed_upside_after_threshold_pct": 1.403968253968254,
          "eligible_count": 63,
          "eligible_rate": 0.39622641509433965,
          "label_counts": [
            {
              "count": 34,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5079365079365079,
          "min_profit_pct": 1.8,
          "positive_exit_count": 31,
          "positive_exit_rate": 0.49206349206349204,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.2547457627118645,
          "avg_missed_upside_after_threshold_pct": 1.3955932203389831,
          "eligible_count": 59,
          "eligible_rate": 0.3710691823899371,
          "label_counts": [
            {
              "count": 32,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 27,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5423728813559322,
          "min_profit_pct": 1.9,
          "positive_exit_count": 27,
          "positive_exit_rate": 0.4576271186440678,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.24629629629629632,
          "avg_missed_upside_after_threshold_pct": 1.422962962962963,
          "eligible_count": 54,
          "eligible_rate": 0.33962264150943394,
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
          "min_profit_pct": 2.0,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.4444444444444444,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.25551020408163255,
          "avg_missed_upside_after_threshold_pct": 1.464081632653061,
          "eligible_count": 49,
          "eligible_rate": 0.3081761006289308,
          "label_counts": [
            {
              "count": 28,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 21,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 26,
          "loss_or_flat_rate": 0.5306122448979592,
          "min_profit_pct": 2.1,
          "positive_exit_count": 23,
          "positive_exit_rate": 0.46938775510204084,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.24954545454545435,
          "avg_missed_upside_after_threshold_pct": 1.5261363636363634,
          "eligible_count": 44,
          "eligible_rate": 0.27672955974842767,
          "label_counts": [
            {
              "count": 26,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 18,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 23,
          "loss_or_flat_rate": 0.5227272727272727,
          "min_profit_pct": 2.2,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.4772727272727273,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.4056097560975611,
          "avg_missed_upside_after_threshold_pct": 1.5370731707317074,
          "eligible_count": 41,
          "eligible_rate": 0.2578616352201258,
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
          "loss_or_flat_count": 20,
          "loss_or_flat_rate": 0.4878048780487805,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5121951219512195,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.37641025641025644,
          "avg_missed_upside_after_threshold_pct": 1.512051282051282,
          "eligible_count": 39,
          "eligible_rate": 0.24528301886792453,
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
          "min_profit_pct": 2.4,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5384615384615384,
          "source_row_count": 159
        },
        {
          "avg_incremental_exit_profit_pct": 0.38555555555555554,
          "avg_missed_upside_after_threshold_pct": 1.5352777777777777,
          "eligible_count": 36,
          "eligible_rate": 0.22641509433962265,
          "label_counts": [
            {
              "count": 23,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 13,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 16,
          "loss_or_flat_rate": 0.4444444444444444,
          "min_profit_pct": 2.5,
          "positive_exit_count": 20,
          "positive_exit_rate": 0.5555555555555556,
          "source_row_count": 159
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.08989547038327539,
        "current_avg_incremental_exit_profit_pct": 0.3157142857142857,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.3157142857142857,
          "avg_missed_upside_after_threshold_pct": 1.4162337662337663,
          "eligible_count": 77,
          "eligible_rate": 0.48427672955974843,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.4805194805194805,
          "min_profit_pct": 1.5,
          "positive_exit_count": 40,
          "positive_exit_rate": 0.5194805194805194,
          "source_row_count": 159
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.4056097560975611,
        "selected_min_profit_pct": 2.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.4056097560975611,
          "avg_missed_upside_after_threshold_pct": 1.5370731707317074,
          "eligible_count": 41,
          "eligible_rate": 0.2578616352201258,
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
          "loss_or_flat_count": 20,
          "loss_or_flat_rate": 0.4878048780487805,
          "min_profit_pct": 2.3,
          "positive_exit_count": 21,
          "positive_exit_rate": 0.5121951219512195,
          "source_row_count": 159
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 48,
      "recovered_or_extended_rate": 0.3018867924528302,
      "reversal_or_flat_count": 60,
      "reversal_or_flat_rate": 0.37735849056603776,
      "sample_count": 159,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-10.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-10:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-10.json"
  }
]
```
