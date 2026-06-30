# 2026-06-30 13:00-15:00 intraday entry flow final stabilization

- generated_at: 2026-06-30T15:03:00+09:00
- time_window_kst: 2026-06-30T13:00:00+09:00/2026-06-30T15:00:00+09:00
- source_diagnostic_final: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1500_1300_goal.json
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_current.md
- decision_authority: diagnostic_only_no_runtime_change
- runtime_effect: false
- forbidden_uses_preserved: threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, quantity_or_cap_change, bot_restart

## Decision

- rising_missed was not hidden by forced scout handling. Final rising_missed_symbol_count_in_report=10, forced_scout_residual_symbol_count=5, and residual_excluding_forced_scout_symbol_count=5.
- The forced scout symbols remained visible as rising_missed residuals and were not counted as normal BUY/submit/fill success: 002990, 010120, 025320, 080220, 103590.
- Final normal submit count was 3, but all 3 were flat_or_falling rows, not rising_missed resolution rows: 093370, 222800, 036930.
- Repeated zero-strength/source-quality workorder was resolved by existing recovery paths after 13:30. It stayed 0 from 13:40 through 15:00.
- Full-eval deferred stayed 0 in every diagnostic slot, so no deferred_never_evaluated/high-delta unresolved path was observed.
- Known latency_state_danger was preserved as pre-submit quote/spread/microstructure quality guard and was not bypassed.

## Slot Summary

|slot|actionable_major|suppressed_non_actionable|zero_strength_workorder|rising_missed_report|forced_events|forced_residual|residual_ex_forced|normal_submit|buy_or_pre_submit_seen|stale_eval|stale_recovered|full_eval_deferred|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|13:10|63|28|0|9|17|5|5|0|1|6|8|0|
|13:20|44|76|0|10|41|5|5|0|1|7|8|0|
|13:30|67|112|1|10|63|5|5|0|1|7|11|0|
|13:40|62|141|0|10|81|5|5|0|1|7|12|0|
|13:50|96|86|0|10|95|5|5|0|1|10|14|0|
|14:00|80|189|0|10|110|5|5|0|1|12|14|0|
|14:10|83|223|0|10|119|5|5|1|3|12|14|0|
|14:20|81|250|0|10|137|5|5|1|4|12|14|0|
|14:30|85|279|0|10|154|5|5|2|6|12|15|0|
|14:40|75|323|0|10|169|5|5|2|6|13|15|0|
|14:50|77|351|0|10|180|5|5|2|6|13|15|0|
|15:00|79|369|0|10|198|5|5|3|6|13|15|0|

## Final Residual Excluding Forced Scout

|symbol|name|max_delta|latest_stage|latest_reason|stale_eval|stale_recovered|latest_ai|
|---|---|---:|---|---|---:|---:|---|
|000500|가온전선|20.44|ai_confirmed_terminal_no_budget|blocked_ai_score_below_buy_score_threshold|0|0|69 WAIT|
|475150|SK이터닉스|4.06|ai_confirmed_terminal_no_budget|blocked_ai_score_below_buy_score_threshold|9|0|76 WAIT|
|001820|삼화콘덴서|2.57|blocked_strength_momentum|below_strength_base|5|16|76 WAIT|
|095610|테스|1.24|ai_confirmed_terminal_no_budget|blocked_ai_score_below_buy_score_threshold|19|5|72 WAIT|
|240810|원익IPS|0.55|ai_confirmed_terminal_no_budget|blocked_ai_score_below_buy_score_threshold|9|12|73 WAIT|

## Root Cause Closure

- 080220 zero-strength/source-quality churn at 13:30 recovered before 13:40 through WS subscription recheck. Evidence later showed fresh WS snapshot, non-zero strength history, and snapshot_applied recovery; no threshold or stale-submit bypass was used.
- 001820 stale/holding freshness churn recovered through holding quote freshness recovery and REST quote application. This stayed inside the hard-safety price freshness guard.
- 002990 latency_state_danger remained quote_stale/quote unavailable quality guard; 010120 remained wide-spread guard; 025320/103590/080220 remained spread microstructure guard. These are preserved quality guards, not BUY threshold blockers to relax intraday.
- AI threshold/score baseline residuals remain strategy/EV tuning evidence only. They do not justify intraday BUY score relaxation.

## Normal Submit Follow-Up

|symbol|name|submit_time|order_no|qty|tag|status|
|---|---|---|---|---:|---|---|
|222800|심텍|14:08:46|0049274|9|normal|holding_started at 14:09:22|
|036930|주성엔지니어링|14:20:58|0050271|7|normal|0 filled, entry cancel confirmed at 14:22:26|
|093370|후성|14:50:31|0052882|79|normal|holding_started at 14:51:39|

## Guard Status

- stale quote guard: preserved
- broker/order/quantity guard: preserved
- cooldown guard: preserved
- hard/protect/emergency safety: unchanged
- runtime threshold mutation: not performed
- bot restart/provider route change: not performed
