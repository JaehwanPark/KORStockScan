# AI Score Optimization Backtest - 2026-07-29

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
    "sample_count": 54,
    "sample_floor": 10,
    "source_metrics": {
      "label_counts": [
        {
          "count": 40,
          "label": "first_touch_loss_or_flat"
        },
        {
          "count": 14,
          "label": "first_touch_recovered_profit"
        }
      ],
      "loss_or_flat_count": 40,
      "loss_or_flat_rate": 0.7407407407407407,
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_count": 14,
      "recovered_rate": 0.25925925925925924,
      "sample_count": 54,
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
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-22.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-23.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-24.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-27.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-28.json",
      "/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-29.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "rising_missed_first_touch_avgdown_decision_gate:2026-07-29:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "rising_missed_first_touch_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/rising_missed_first_touch_calibration/rising_missed_first_touch_calibration_2026-07-29.json"
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
    "sample_count": 219,
    "sample_floor": 20,
    "source_metrics": {
      "calibration_source_scope": "one_share_event_opportunity",
      "correctly_blocked_count": 81,
      "correctly_blocked_rate": 0.3698630136986301,
      "label_counts": [
        {
          "count": 86,
          "label": "pyramid_overheat_or_reversal_risk"
        },
        {
          "count": 81,
          "label": "pyramid_correctly_blocked"
        },
        {
          "count": 52,
          "label": "pyramid_would_have_helped"
        }
      ],
      "normal_winner_expansion_observation": {
        "allowed_runtime_apply": false,
        "by_effective_venue": [
          {
            "allowed_runtime_apply": false,
            "effective_venue": "KRX",
            "notional_weighted_ev_pct": -0.3929,
            "runtime_effect": false,
            "sample_count": 5,
            "sample_floor": 20,
            "sample_floor_met": false
          },
          {
            "allowed_runtime_apply": false,
            "effective_venue": "NXT",
            "notional_weighted_ev_pct": 0.1441,
            "runtime_effect": false,
            "sample_count": 2,
            "sample_floor": 20,
            "sample_floor_met": false
          },
          {
            "allowed_runtime_apply": false,
            "effective_venue": "PREMARKET_KRX_LIKE",
            "notional_weighted_ev_pct": -3.4867,
            "runtime_effect": false,
            "sample_count": 1,
            "sample_floor": 20,
            "sample_floor_met": false
          }
        ],
        "by_market_session_bucket": [
          {
            "allowed_runtime_apply": false,
            "market_session_bucket": "krx_like_premarket",
            "notional_weighted_ev_pct": -3.4867,
            "runtime_effect": false,
            "sample_count": 1,
            "sample_floor": 20,
            "sample_floor_met": false
          },
          {
            "allowed_runtime_apply": false,
            "market_session_bucket": "krx_regular",
            "notional_weighted_ev_pct": -0.3929,
            "runtime_effect": false,
            "sample_count": 5,
            "sample_floor": 20,
            "sample_floor_met": false
          },
          {
            "allowed_runtime_apply": false,
            "market_session_bucket": "nxt_entry_window",
            "notional_weighted_ev_pct": 0.1441,
            "runtime_effect": false,
            "sample_count": 2,
            "sample_floor": 20,
            "sample_floor_met": false
          }
        ],
        "decision_authority": "rolling_source_only_normal_winner_expansion_observation",
        "diagnostic_win_rate": 0.375,
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
        "metric_role": "bounded_tunable_scale_in_counterfactual",
        "notional_weighted_ev_pct": -0.5176,
        "primary_decision_metric": "notional_weighted_ev_pct",
        "provenance_rejected_count": 0,
        "realized_incremental_winner_count": 3,
        "runtime_effect": false,
        "sample_count": 8,
        "sample_floor": 20,
        "sample_floor_met": false,
        "section_present": true,
        "source_quality_gate": "source_quality_valid_positive_pyramid_candidate_with_post_candidate_sell",
        "state": "hold_sample",
        "window_policy": "rolling_clean_baseline_closed_normal_winner_expansion_rows"
      },
      "one_share_closed_pyramid_row_count": 219,
      "one_share_event_source_present": true,
      "one_share_pyramid_avg_opportunity_cost_pct": 0.6557077625570776,
      "post_probe_real_outcome_observation": {
        "allowed_runtime_apply": false,
        "by_effective_venue": [
          {
            "allowed_runtime_apply": false,
            "effective_venue": "NXT",
            "notional_weighted_ev_pct": 0.27,
            "runtime_effect": false,
            "sample_count": 1,
            "sample_floor": 20,
            "sample_floor_met": false
          }
        ],
        "by_market_session_bucket": [
          {
            "allowed_runtime_apply": false,
            "market_session_bucket": "nxt_entry_window",
            "notional_weighted_ev_pct": 0.27,
            "runtime_effect": false,
            "sample_count": 1,
            "sample_floor": 20,
            "sample_floor_met": false
          }
        ],
        "closed_real_outcome_count": 3,
        "confirmation_ready_count": 1,
        "confirmation_ready_counterfactual_source_blocked_count": 0,
        "confirmation_ready_loss_or_flat_count": 0,
        "confirmation_ready_winner_count": 1,
        "decision_authority": "rolling_source_only_post_probe_real_outcome_no_runtime_mutation",
        "diagnostic_win_rate": 0.3333,
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
        "metric_role": "multi_leg_post_probe_real_outcome_attribution",
        "notional_weighted_ev_pct": 0.27,
        "primary_decision_metric": "notional_weighted_ev_pct",
        "provenance_rejected_count": 0,
        "realized_loss_or_flat_zero_fill_count": 2,
        "realized_winner_zero_fill_count": 1,
        "runtime_effect": false,
        "sample_floor": 20,
        "sample_floor_met": false,
        "sample_floor_policy": "rolling_confirmation_ready_source_quality_valid_rows_ge_20",
        "section_present": true,
        "source_quality_gate": "exact_probe_terminal_fill_real_sell_profit_explicit_venue_and_version_proven_post_probe_evidence",
        "source_quality_rejected_count": 0,
        "state": "hold_sample",
        "window_policy": "rolling_clean_baseline_closed_zero_fill_probe_to_terminal_sell"
      },
      "profit_threshold_grid": [
        {
          "avg_incremental_exit_profit_pct": 0.04902097902097899,
          "avg_missed_upside_after_threshold_pct": 1.4153846153846155,
          "eligible_count": 143,
          "eligible_rate": 0.6529680365296804,
          "label_counts": [
            {
              "count": 68,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 52,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 23,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 59,
          "loss_or_flat_rate": 0.4125874125874126,
          "min_profit_pct": 0.8,
          "positive_exit_count": 84,
          "positive_exit_rate": 0.5874125874125874,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.06015151515151512,
          "avg_missed_upside_after_threshold_pct": 1.4292424242424242,
          "eligible_count": 132,
          "eligible_rate": 0.6027397260273972,
          "label_counts": [
            {
              "count": 66,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 52,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 14,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 51,
          "loss_or_flat_rate": 0.38636363636363635,
          "min_profit_pct": 0.9,
          "positive_exit_count": 81,
          "positive_exit_rate": 0.6136363636363636,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.20565573770491802,
          "avg_missed_upside_after_threshold_pct": 1.4427868852459018,
          "eligible_count": 122,
          "eligible_rate": 0.5570776255707762,
          "label_counts": [
            {
              "count": 61,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 51,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 10,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 45,
          "loss_or_flat_rate": 0.36885245901639346,
          "min_profit_pct": 1.0,
          "positive_exit_count": 77,
          "positive_exit_rate": 0.6311475409836066,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.17732758620689645,
          "avg_missed_upside_after_threshold_pct": 1.4155172413793102,
          "eligible_count": 116,
          "eligible_rate": 0.5296803652968036,
          "label_counts": [
            {
              "count": 59,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 49,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 8,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 48,
          "loss_or_flat_rate": 0.41379310344827586,
          "min_profit_pct": 1.1,
          "positive_exit_count": 68,
          "positive_exit_rate": 0.5862068965517241,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.17481481481481484,
          "avg_missed_upside_after_threshold_pct": 1.416851851851852,
          "eligible_count": 108,
          "eligible_rate": 0.4931506849315068,
          "label_counts": [
            {
              "count": 55,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 48,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 5,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 44,
          "loss_or_flat_rate": 0.4074074074074074,
          "min_profit_pct": 1.2,
          "positive_exit_count": 64,
          "positive_exit_rate": 0.5925925925925926,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.22435643564356433,
          "avg_missed_upside_after_threshold_pct": 1.4118811881188118,
          "eligible_count": 101,
          "eligible_rate": 0.4611872146118721,
          "label_counts": [
            {
              "count": 51,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 47,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 42,
          "loss_or_flat_rate": 0.4158415841584158,
          "min_profit_pct": 1.3,
          "positive_exit_count": 59,
          "positive_exit_rate": 0.5841584158415841,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.1930000000000001,
          "avg_missed_upside_after_threshold_pct": 1.3254000000000001,
          "eligible_count": 100,
          "eligible_rate": 0.45662100456621,
          "label_counts": [
            {
              "count": 50,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 47,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 3,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 47,
          "loss_or_flat_rate": 0.47,
          "min_profit_pct": 1.4,
          "positive_exit_count": 53,
          "positive_exit_rate": 0.53,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.15340425531914892,
          "avg_missed_upside_after_threshold_pct": 1.3081914893617022,
          "eligible_count": 94,
          "eligible_rate": 0.4292237442922374,
          "label_counts": [
            {
              "count": 46,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 45,
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
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.191860465116279,
          "avg_missed_upside_after_threshold_pct": 1.325,
          "eligible_count": 86,
          "eligible_rate": 0.3926940639269406,
          "label_counts": [
            {
              "count": 44,
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
          "loss_or_flat_count": 45,
          "loss_or_flat_rate": 0.5232558139534884,
          "min_profit_pct": 1.6,
          "positive_exit_count": 41,
          "positive_exit_rate": 0.47674418604651164,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.23037974683544302,
          "avg_missed_upside_after_threshold_pct": 1.339746835443038,
          "eligible_count": 79,
          "eligible_rate": 0.3607305936073059,
          "label_counts": [
            {
              "count": 41,
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
          "loss_or_flat_count": 44,
          "loss_or_flat_rate": 0.5569620253164557,
          "min_profit_pct": 1.7,
          "positive_exit_count": 35,
          "positive_exit_rate": 0.4430379746835443,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.1641333333333333,
          "avg_missed_upside_after_threshold_pct": 1.3085333333333333,
          "eligible_count": 75,
          "eligible_rate": 0.3424657534246575,
          "label_counts": [
            {
              "count": 37,
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
          "loss_or_flat_count": 42,
          "loss_or_flat_rate": 0.56,
          "min_profit_pct": 1.8,
          "positive_exit_count": 33,
          "positive_exit_rate": 0.44,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.10528571428571436,
          "avg_missed_upside_after_threshold_pct": 1.2985714285714287,
          "eligible_count": 70,
          "eligible_rate": 0.319634703196347,
          "label_counts": [
            {
              "count": 35,
              "label": "pyramid_would_have_helped"
            },
            {
              "count": 34,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 1,
              "label": "pyramid_correctly_blocked"
            }
          ],
          "loss_or_flat_count": 41,
          "loss_or_flat_rate": 0.5857142857142857,
          "min_profit_pct": 1.9,
          "positive_exit_count": 29,
          "positive_exit_rate": 0.4142857142857143,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.11622950819672132,
          "avg_missed_upside_after_threshold_pct": 1.3862295081967213,
          "eligible_count": 61,
          "eligible_rate": 0.2785388127853881,
          "label_counts": [
            {
              "count": 30,
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
          "loss_or_flat_count": 36,
          "loss_or_flat_rate": 0.5901639344262295,
          "min_profit_pct": 2.0,
          "positive_exit_count": 25,
          "positive_exit_rate": 0.4098360655737705,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.10017857142857133,
          "avg_missed_upside_after_threshold_pct": 1.4064285714285714,
          "eligible_count": 56,
          "eligible_rate": 0.2557077625570776,
          "label_counts": [
            {
              "count": 29,
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
          "loss_or_flat_count": 32,
          "loss_or_flat_rate": 0.5714285714285714,
          "min_profit_pct": 2.1,
          "positive_exit_count": 24,
          "positive_exit_rate": 0.42857142857142855,
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.13354166666666648,
          "avg_missed_upside_after_threshold_pct": 1.5347916666666663,
          "eligible_count": 48,
          "eligible_rate": 0.2191780821917808,
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
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.2829545454545456,
          "avg_missed_upside_after_threshold_pct": 1.5729545454545457,
          "eligible_count": 44,
          "eligible_rate": 0.2009132420091324,
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
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.24285714285714294,
          "avg_missed_upside_after_threshold_pct": 1.5442857142857143,
          "eligible_count": 42,
          "eligible_rate": 0.1917808219178082,
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
          "source_row_count": 219
        },
        {
          "avg_incremental_exit_profit_pct": 0.23333333333333334,
          "avg_missed_upside_after_threshold_pct": 1.5605128205128205,
          "eligible_count": 39,
          "eligible_rate": 0.1780821917808219,
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
          "source_row_count": 219
        }
      ],
      "profit_threshold_grid_decision": {
        "avg_incremental_exit_profit_delta_pct": 0.1295502901353967,
        "current_avg_incremental_exit_profit_pct": 0.15340425531914892,
        "current_min_profit_pct": 1.5,
        "current_row": {
          "avg_incremental_exit_profit_pct": 0.15340425531914892,
          "avg_missed_upside_after_threshold_pct": 1.3081914893617022,
          "eligible_count": 94,
          "eligible_rate": 0.4292237442922374,
          "label_counts": [
            {
              "count": 46,
              "label": "pyramid_overheat_or_reversal_risk"
            },
            {
              "count": 45,
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
          "source_row_count": 219
        },
        "reason": "grid_ev_delta_lt_0_20",
        "selected_avg_incremental_exit_profit_pct": 0.2829545454545456,
        "selected_min_profit_pct": 2.3,
        "selected_row": {
          "avg_incremental_exit_profit_pct": 0.2829545454545456,
          "avg_missed_upside_after_threshold_pct": 1.5729545454545457,
          "eligible_count": 44,
          "eligible_rate": 0.2009132420091324,
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
          "source_row_count": 219
        },
        "status": "hold"
      },
      "provenance_present": true,
      "recommended_action": "hold_sample",
      "recommended_action_reason": "source_quality_not_pass",
      "recovered_or_extended_count": 52,
      "recovered_or_extended_rate": 0.2374429223744292,
      "reversal_or_flat_count": 86,
      "reversal_or_flat_rate": 0.3926940639269406,
      "sample_count": 219,
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
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-22.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-23.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-24.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-27.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-28.json",
      "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-29.json"
    ],
    "stage": "scale_in",
    "target_env_keys": [],
    "threshold_version": "scalping_pyramid_quality_gate:2026-07-29:v1",
    "same_stage_owner_stage": "scale_in",
    "sample_floor_passed": false,
    "apply_block_reason": "source_quality_blocked",
    "ai_score_optimization_source_report_type": "scalping_pyramid_quality_calibration",
    "ai_score_optimization_source_path": "/home/ubuntu/KORStockScan/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_2026-07-29.json"
  }
]
```
