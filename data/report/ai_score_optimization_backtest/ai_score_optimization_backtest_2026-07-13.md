# AI Score Optimization Backtest - 2026-07-13

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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-13.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-13:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-13.json"
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
    "sample_count": 163,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 54,
      "correctly_blocked_rate": 0.3312883435582822,
      "label_counts": [
        {
          "count": 60,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 54,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 49,
          "label": "pyramid_would_have_helped"
        }
      ],
      "one_share_closed_pyramid_row_count": 163,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.7710429447852761,
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.15513761467889906,
          "avg_missed_upside_after_threshold_pct": 1.5876146788990824,
          "eligible_count": 109,
          "eligible_rate": 0.6687116564417178,
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
              "count": 13,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.3119266055045872,
          "min_profit_pct": 0.8,
          "positive_exit_count": 75,
          "positive_exit_rate": 0.6880733944954128,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.16572815533980578,
          "avg_missed_upside_after_threshold_pct": 1.576116504854369,
          "eligible_count": 103,
          "eligible_rate": 0.6319018404907976,
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
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 31,
          "loss_or_flat_rate": 0.30097087378640774,
          "min_profit_pct": 0.9,
          "positive_exit_count": 72,
          "positive_exit_rate": 0.6990291262135923,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.34572916666666664,
          "avg_missed_upside_after_threshold_pct": 1.5878125,
          "eligible_count": 96,
          "eligible_rate": 0.588957055214724,
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
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 27,
          "loss_or_flat_rate": 0.28125,
          "min_profit_pct": 1.0,
          "positive_exit_count": 69,
          "positive_exit_rate": 0.71875,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.3134408602150537,
          "avg_missed_upside_after_threshold_pct": 1.5376344086021505,
          "eligible_count": 93,
          "eligible_rate": 0.5705521472392638,
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
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.3548387096774194,
          "min_profit_pct": 1.1,
          "positive_exit_count": 60,
          "positive_exit_rate": 0.6451612903225806,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.3394186046511628,
          "avg_missed_upside_after_threshold_pct": 1.5587209302325582,
          "eligible_count": 86,
          "eligible_rate": 0.5276073619631901,
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
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.3488372093023256,
          "min_profit_pct": 1.2,
          "positive_exit_count": 56,
          "positive_exit_rate": 0.6511627906976745,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.3790361445783132,
          "avg_missed_upside_after_threshold_pct": 1.5134939759036143,
          "eligible_count": 83,
          "eligible_rate": 0.50920245398773,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 30,
          "loss_or_flat_rate": 0.3614457831325301,
          "min_profit_pct": 1.3,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.6385542168674698,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.36463414634146346,
          "avg_missed_upside_after_threshold_pct": 1.431219512195122,
          "eligible_count": 82,
          "eligible_rate": 0.5030674846625767,
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
              "count": 2,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 34,
          "loss_or_flat_rate": 0.4146341463414634,
          "min_profit_pct": 1.4,
          "positive_exit_count": 48,
          "positive_exit_rate": 0.5853658536585366,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.31807692307692303,
          "avg_missed_upside_after_threshold_pct": 1.4033333333333333,
          "eligible_count": 78,
          "eligible_rate": 0.4785276073619632,
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
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.47435897435897434,
          "min_profit_pct": 1.5,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.5256410256410257,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.342361111111111,
          "avg_missed_upside_after_threshold_pct": 1.4163888888888887,
          "eligible_count": 72,
          "eligible_rate": 0.44171779141104295,
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
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4583333333333333,
          "min_profit_pct": 1.6,
          "positive_exit_count": 39,
          "positive_exit_rate": 0.5416666666666666,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.366865671641791,
          "avg_missed_upside_after_threshold_pct": 1.418955223880597,
          "eligible_count": 67,
          "eligible_rate": 0.4110429447852761,
          "label_counts": [
            {
              "count": 38,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 33,
          "loss_or_flat_rate": 0.4925373134328358,
          "min_profit_pct": 1.7,
          "positive_exit_count": 34,
          "positive_exit_rate": 0.5074626865671642,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.30406249999999996,
          "avg_missed_upside_after_threshold_pct": 1.38375,
          "eligible_count": 64,
          "eligible_rate": 0.39263803680981596,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 29,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5,
          "min_profit_pct": 1.8,
          "positive_exit_count": 32,
          "positive_exit_rate": 0.5,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.25216666666666676,
          "avg_missed_upside_after_threshold_pct": 1.3725,
          "eligible_count": 60,
          "eligible_rate": 0.36809815950920244,
          "label_counts": [
            {
              "count": 33,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 27,
              "label": "pyramid_overheat_or_reversal_risk"
            }
          ],
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5333333333333333,
          "min_profit_pct": 1.9,
          "positive_exit_count": 28,
          "positive_exit_rate": 0.4666666666666667,
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.24629629629629632,
          "avg_missed_upside_after_threshold_pct": 1.422962962962963,
          "eligible_count": 54,
          "eligible_rate": 0.3312883435582822,
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
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.25551020408163255,
          "avg_missed_upside_after_threshold_pct": 1.464081632653061,
          "eligible_count": 49,
          "eligible_rate": 0.3006134969325153,
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
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.24954545454545435,
          "avg_missed_upside_after_threshold_pct": 1.5261363636363634,
          "eligible_count": 44,
          "eligible_rate": 0.26993865030674846,
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
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.4056097560975611,
          "avg_missed_upside_after_threshold_pct": 1.5370731707317074,
          "eligible_count": 41,
          "eligible_rate": 0.25153374233128833,
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
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.37641025641025644,
          "avg_missed_upside_after_threshold_pct": 1.512051282051282,
          "eligible_count": 39,
          "eligible_rate": 0.2392638036809816,
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
          "source_row_count": 163
        },
        {
          "avg_incremental_exit_profit_pct": 0.38555555555555554,
          "avg_missed_upside_after_threshold_pct": 1.5352777777777777,
          "eligible_count": 36,
          "eligible_rate": 0.22085889570552147,
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
          "source_row_count": 163
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.08753283302063808,
        "current_avg_incremental_exit_profit_pct": 0.31807692307692303,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.31807692307692303,
          "avg_missed_upside_after_threshold_pct": 1.4033333333333333,
          "eligible_count": 78,
          "eligible_rate": 0.4785276073619632,
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
          "loss_or_flat_count": 37,
          "loss_or_flat_rate": 0.47435897435897434,
          "min_profit_pct": 1.5,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.5256410256410257,
          "source_row_count": 163
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.4056097560975611,
        "selected_min_profit_pct": 2.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.4056097560975611,
          "avg_missed_upside_after_threshold_pct": 1.5370731707317074,
          "eligible_count": 41,
          "eligible_rate": 0.25153374233128833,
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
          "source_row_count": 163
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 49,
      "recovered_or_extended_rate": 0.3006134969325153,
      "reversal_or_flat_count": 60,
      "reversal_or_flat_rate": 0.36809815950920244,
      "sample_count": 163,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-13.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-13:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-13.json"
  }
]
```
