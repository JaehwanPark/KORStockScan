# Intraday Entry Flow Final Stabilization - 2026-07-06 12:00~16:00 KST

- generated_at: 2026-07-06T16:00:00+09:00
- source_flow_final: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md`
- window: 12:00:00~16:00:00 KST
- buy_window_policy: active until 15:20:00, then pause/monitor_only until 16:00:00
- runtime_threshold_mutation: false
- broker_or_hard_guard_bypass: false
- forced_scout_counted_as_normal_buy_success: false

## Decision

The 12:00~16:00 window was not a single normal-submit drought. Normal lifecycle recovery appeared in multiple buckets:

- KBI메탈: normal submit at 12:16 and normal submit plus holding at 12:39, later +0.90% sell_completed.
- 에이디테크놀로지: normal submit plus holding at 13:16, later protect trailing stop sell_completed at -2.12%.
- 가온칩스: normal submit plus holding at 13:42.
- 일신방직: last active-buy-window normal submit at 15:17.

However, several high-score near-BUY opportunities remained unfilled or source-only, mostly due to latency/state separation, AI terminal/no-budget behavior, strength/momentum blockers, and monitor-only timing. Forced/rising-missed scout events were frequent but are kept separate from normal BUY success.

## Evidence

Final current report summary:

- `symbol_count=54`
- `buy_signal_or_pre_submit_pass_seen_symbols=17`
- `real_submit_symbol_count_in_latest_diagnostic=1`
- `rising_missed_forced_scout_event_count=279`
- `rising_missed_forced_scout_symbol_count=15`
- `rising_missed_symbol_count_in_report=2`
- `rising_missed_residual_excluding_forced_scout_symbol_count=0`
- `stale_eval_symbol_count=46`
- `stale_refresh_recovered_symbol_count=25`

Normal lifecycle / exit evidence:

| Window | Normal lifecycle / exit |
| --- | --- |
| 12:00~12:10 | 남광토건 sell_completed -5.32%, `scalp_hard_stop_pct` |
| 12:10~12:20 | KBI메탈 normal submit, `safe_normal_entry_allowed` |
| 12:30~12:40 | KBI메탈 normal submit and `holding_started` |
| 12:40~12:50 | 한화오션 sell_completed +0.45%, `scalp_low_profit_stagnation_hard_exit` |
| 13:10~13:20 | 에이디테크놀로지 normal submit and `holding_started`; KBI메탈 sell_completed +0.90% |
| 13:40~13:50 | 가온칩스 normal submit and `holding_started`; 오성첨단소재 hard-stop signal -5.52% |
| 14:30~14:40 | 에이디테크놀로지 sell_completed -2.12%, `protect_trailing_stop` |
| 15:10~15:20 | 일신방직 normal submit, `caution_normal_entry_allowed` |

High-score near-BUY / opportunity evidence:

| Window | Evidence |
| --- | --- |
| 12:10~12:20 | HD건설기계 AI 78, fresh micro, buy_pressure 85.09, then blocked/terminal |
| 12:20~12:30 | iM금융지주 AI 74, fresh micro, buy_pressure 97.01, terminal/no-budget |
| 12:50~13:10 | 마키나락스 AI 75, buy_pressure 92.49, repeated `latency_state_danger` |
| 13:10~13:20 | 와이지-원 AI 75, buy_pressure 77.74, `latency_state_danger` |
| 13:30~13:40 | 오성첨단소재 AI 76, buy_pressure 90.38, `latency_state_danger` |
| 13:40~13:50 | 와이지-원 AI 75, buy_pressure 92.73, `latency_state_danger` |
| 14:10~14:20 | 테크윙 AI 75, fresh micro, buy_pressure 100.0, `blocked_ai_score`/terminal |
| 14:30~14:40 | 레몬헬스케어 AI 74, fresh micro, buy_pressure 97.92, sim/terminal only |
| 15:10~15:20 | 가온전선 AI 74, fresh micro, buy_pressure 94.12, sim/terminal only |

Scale-in / holding quality evidence:

- KBI메탈 recovered to normal lifecycle, but PYRAMID/AVG_DOWN attempts mostly stayed blocked by `profit_not_enough`, `ai_score_unavailable`, `large_sell_detected`, or stale micro confirmation.
- 에이디테크놀로지 reached +1.59% but PYRAMID was blocked by AI/micro quality and later exited at -2.12%.
- 가온칩스 reached +1.33% but PYRAMID was blocked by `buy_pressure_severe_below_min`, `large_sell_detected`, and missing fresh micro confirmation.
- 레몬헬스케어 AVG_DOWN was blocked by `supply_conditions_not_met`; later PYRAMID at +1.30% was blocked by overheated micro VWAP, large sell, and fresh confirmation missing.

15:20~16:00 policy:

- 15:20~16:00 was treated as `monitor_only_after_buy_window`.
- Scanner/runtime trace remained high, but new BUY bottleneck expansion was not used after the 15:20 buy-window boundary.

## Next Action

- `entry_ai_gate_backtest` / `ai_score_optimization_backtest`: review high-score terminal/no-budget or latency cases, especially HD건설기계, 마키나락스, 와이지-원, 오성첨단소재, 테크윙, 레몬헬스케어, 가온전선.
- `scalping_pyramid_intraday_feedback`: add/refresh PYRAMID missed opportunity rows for 에이디테크놀로지, 가온칩스, 레몬헬스케어, and KBI메탈.
- `rising_missed_intraday_feedback` and `rising_missed_scout_workorder`: keep forced scout lineage separate from normal BUY lifecycle; do not use forced scout results as direct live authority.
- `code_improvement_workorder`: investigate why some AI 74~78 fresh-micro rows closed as `blocked_ai_score` or sim/terminal only, and why repeated `latency_state_danger` persisted for high-score candidates.
- PREOPEN application remains limited to `auto_bounded_live` candidates that pass source-quality, same-stage owner, AI guard, and hard-safety constraints.
