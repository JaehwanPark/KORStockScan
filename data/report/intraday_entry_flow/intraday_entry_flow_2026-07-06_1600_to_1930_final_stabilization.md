# Intraday Entry Flow Final Stabilization - 2026-07-06

- window: 16:00:00~19:30:00 KST
- generated_at: 2026-07-06T19:30:00+09:00
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md
- source_events: data/pipeline_events/pipeline_events_2026-07-06.jsonl
- decision_authority: source_quality_only
- runtime_effect: false
- forbidden_uses: threshold_mutation, provider_route_change, bot_restart_authority, broker_guard_bypass, stale_quote_bypass, hard_safety_guard_bypass, quantity_or_cap_change, real_execution_quality_approval

## Decision

The 16:00~19:30 window was identified with valid intraday source artifacts, but the major remaining missed-entry evidence is source-only/code-improvement evidence, not direct real-runtime authority.

Normal BUY/submit did occur, so this is not a full submit drought. However, forced scout one-share events grew much faster than normal submit transitions and must stay separated from normal BUY success. The most actionable major blockers are:

- high-delta stale/queue path: Hanwha Systems (272210), max delta +12.61%, no normal submit.
- AI 70 near-buy latency path: Samsung Electronics (005930), ADTechnology (200710), Taesung (323280), repeatedly WAIT_REQUOTE / latency_state_danger.
- source-quality exclusion/watch-budget path: Kumho E&C (002990), Namkwang Engineering & Construction (001260), MakinaRocks (477850), persistent stale snapshot or REST-only recovery without usable realtime strength.

No intraday threshold/env mutation was made. Any runtime reflection must go through postclose feedback/workorder artifacts and next PREOPEN auto_bounded_live guards.

## Evidence

Final current report summary:

- symbol_count: 85
- buy_signal_or_pre_submit_pass_seen_symbols: 16
- real_submit_symbol_count_in_latest_diagnostic: 1
- rising_symbol_count_by_max_delta: 14
- rising_missed_buy_count_in_latest_diagnostic: 4
- rising_missed_symbol_count_in_report: 3
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 301
- rising_missed_forced_scout_symbol_count: 15
- stale_eval_symbol_count: 70
- rising_stale_eval_symbol_count: 14
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 30

Normal lifecycle evidence:

- 17 normal entry/holding stages were observed in the scoped event stream.
- Normal submit/holding symbols included Gaonchips (399720), Sungshin Cement (004980), Ilshin Spinning (003200), and Hanil Cement (300720).
- Later successful normal transitions occurred at 18:48 Gaonchips submit, 18:49 Hanil Cement submit, 18:51 Hanil Cement holding_started, 19:13 Gaonchips submit, and 19:14 Gaonchips holding_started.
- Sell lifecycle evidence in the window included completed low-profit exits for Gaonchips, Ilshin Spinning, and Hanil Cement, all recorded separately from new BUY bottlenecks.

Forced scout evidence:

- Forced scout top counts: Samsung Electronics 119, Ilshin Spinning 82, Sungshin Cement 57, Hanwha Systems 42, Hanil Cement 30, Gaonchips 15, ADTechnology 4, Taesung 2.
- These are one-share/rising missed observations and are not counted as normal BUY success.

High-AI near-buy evidence:

- Samsung Electronics: 107 AI 70 WAIT_REQUOTE latency_state_danger observations, no normal submit in the final unresolved row.
- Sungshin Cement: 39 AI 70 WAIT_REQUOTE latency_state_danger observations, but it also had earlier normal submit/holding evidence and later soft-stop events.
- ADTechnology: 4 AI 70 WAIT_REQUOTE latency_state_danger observations from 19:26~19:29, max delta +9.98%, no normal submit.
- Taesung: late latency_state_danger near-buy path, max delta +1.44%, no normal submit.
- Hanil Cement, Gaonchips, Ilshin Spinning, and Sungshin Cement also had BUY_DEFENSIVE observations that did lead to normal submit paths in parts of the window.

Top blocker evidence:

- scalping_scanner_fast_precheck / stale_ws_snapshot: 1885
- scalping_scanner_watching_runtime_skip / scanner_fast_precheck_subscription_recheck_snapshot_applied: 1135
- scalping_scanner_fast_precheck / fast_precheck_pass: 1031
- scalping_scanner_watching_runtime_skip / scanner_full_eval_loop_budget_deferred: 790
- scalping_scanner_watching_runtime_skip / scanner_fast_precheck_stability_pending: 701
- scalping_scanner_fast_precheck / rising_stale_ws_snapshot_full_eval_relief: 599
- scalping_scanner_watching_runtime_skip / scanner_heavy_eval_stale_snapshot_recheck: 307
- scalping_scanner_fast_precheck / rising_rest_quote_recovery_without_realtime_strength: 237
- latency_block / latency_state_danger: 166

## 10-Minute Buckets

| Window | Normal BUY / lifecycle | Forced scout / one-share | Main unresolved evidence | Classification |
|---|---|---|---|---|
| 16:00~16:30 | Gaonchips normal holding/submit; earlier Gaonchips sell | Sungshin Cement, Samsung Electronics, stale source names | Samsung AI70 latency; Namkwang/Kumho stale REST-only | mixed normal + source-quality |
| 16:30~16:40 | Sungshin Cement holding/submit; Ilshin sell | Sungshin Cement, Samsung Electronics | Samsung AI70 latency; Namkwang stale continues | mixed normal + latency |
| 16:40~16:50 | Ilshin and Hanil normal submit/holding; Gaonchips sell | Samsung, Ilshin/Hanil one-share lineage | Scale-in mostly profit_not_enough or pnl_out_of_range | normal submit present |
| 16:50~17:00 | No new normal lifecycle | Samsung forced scout continues | Samsung latency_state_danger | latency blocker |
| 17:00~17:10 | No new normal lifecycle | Samsung forced scout continues | Chips&Media scale-in block then trailing TP | intended holding guard |
| 17:10~17:20 | No new normal lifecycle | Samsung forced scout continues | Samsung latency, stale scanner churn | latency/source-quality |
| 17:20~17:30 | Ilshin sell_order_sent | Samsung forced scout continues | Scale-in mostly intended guard | intended guard |
| 17:30~17:40 | Ilshin and Hanil exits completed/sent | Samsung latency continues | Namkwang stale path ends near 17:36 | source-quality exclusion |
| 17:40~17:50 | Hanil normal submit | Ilshin/Hanwha Systems begin rising-missed evidence | Samsung latency; Hanwha Systems high-delta appears | normal + high-delta stale |
| 17:50~18:00 | Ilshin normal submit in aggregate window | Samsung/Ilshin/Hanwha Systems forced evidence | No new high-AI submit path | monitor |
| 18:00~18:10 | Hanil normal submit | Samsung forced evidence | Samsung latency continues | normal + latency |
| 18:10~18:20 | No new normal lifecycle | Samsung/Hanwha Systems | LX Semicon appeared then strength/hardgate | intended strength guard |
| 18:20~18:30 | Hanil normal submit | Hanwha Systems +12.61; Ilshin pyramid feedback | Hanwha Systems high-delta unresolved; Ilshin pyramid bridge/block samples | actionable source-quality |
| 18:30~18:40 | No new normal lifecycle | Ilshin, Hanwha Systems | Hanwha Systems heavy-eval lag; Ilshin PYRAMID ok then trailing TP | source-quality + useful scale-in feedback |
| 18:40~18:50 | Gaonchips and Hanil normal submit | Ilshin, Hanwha Systems, Samsung | Hanwha Systems stale/queue; Samsung latency | normal submit present |
| 18:50~19:00 | Hanil holding_started | Ilshin, Hanwha Systems, Hanil | Hanwha Systems low-priority deferred; no high-AI near-buy | normal holding |
| 19:00~19:10 | No normal lifecycle | Ilshin, Hanil, Hanwha Systems, Samsung | No new high-AI near-buy; scale-in intended guards | monitor |
| 19:10~19:20 | Gaonchips normal submit and holding_started | Ilshin, Hanwha Systems, Hanil, Gaonchips | Hanwha Systems remains unresolved | normal submit present |
| 19:20~19:30 | No normal lifecycle | ADTechnology, Ilshin, Hanwha Systems, Taesung, Samsung | ADTechnology/Samsung/Taesung AI70 latency; Hanwha Systems +12.61 stale/queue | actionable latency + source-quality |

## Final Unresolved Rows

| Symbol | Max delta | Last state | Normal submit | Forced scout | Interpretation |
|---|---:|---|---:|---:|---|
| Hanwha Systems (272210) | +12.61% | runtime_queue_lag / stale eval | 0 | 42 | high-delta source-quality/queue bottleneck; source-only workorder |
| ADTechnology (200710) | +9.98% | AI70 WAIT_REQUOTE latency_state_danger | 0 | 4 | high-AI latency blocker; bounded recheck candidate |
| MakinaRocks (477850) | +8.74% | stale snapshot early window | 0 | 0 | stale source-quality exclusion candidate |
| Kumho E&C (002990) | +4.49% | stale/REST-only recovery | 0 | 0 | source-quality/watch-budget candidate |
| Namkwang Engineering & Construction (001260) | +3.80% | scanner_heavy_eval_stale_snapshot_recheck | 0 | 0 | source-quality exclusion/watch-budget candidate |
| Taesung (323280) | +1.44% | AI70 WAIT_REQUOTE latency_state_danger | 0 | 2 | late near-buy latency blocker |
| Samsung Electronics (005930) | +1.26% | AI70 latency lineage earlier, no submit | 0 | 119 | repeated latency_state_danger; bounded pre-submit quality recovery candidate |

## Holding / Scale-In Notes

- Most scale-in blocks were intended guards: profit_not_enough, pnl_out_of_range, stale quote, micro_context_stale, tick_accel_stale, tick_aggressor_pressure_unusable.
- Ilshin Spinning supplied useful PYRAMID feedback: PYRAMID ok appeared before trailing take profit.
- Bumhan Fuel Cell showed one PYRAMID ok sample at +1.22, then later pyramid_quality_blocked with unavailable AI and stale micro inputs.
- Sungshin Cement hit first-touch avgdown decision blocked and holding_flow force-exit under scalp_soft_stop_pct in the last bucket. This should feed defensive feedback, not relax hard safety.

## Next Action

Postclose source-only/code-improvement handoff:

- rising_missed_intraday_feedback: include forced scout lineage, but keep it separate from normal BUY success.
- rising_missed_scout_workorder: prioritize Hanwha Systems high-delta stale/queue case and Samsung repeated latency lineage.
- rising_missed_first_touch_calibration: include only labeled first-touch/avgdown rows with provenance; do not infer from entry-only stale rows.
- one_share_threshold_opportunity: record opportunity cost from Hanwha Systems, Samsung Electronics, ADTechnology, Taesung, and Ilshin/Hanil/Gaonchips mixed cases.
- code_improvement_workorder: bounded pre-submit quality recovery for repeated latency_state_danger; high-delta source recovery and queue priority for Hanwha Systems; source-quality exclusion/watch-budget reallocation for stale REST-only rows such as Namkwang and Kumho.

Runtime stance:

- No runtime threshold/env mutation.
- No provider route change.
- No bot restart authority.
- No broker/stale/hard-safety/order/account/cooldown/quantity guard bypass.
- Real runtime reflection requires postclose candidate generation and next PREOPEN auto_bounded_live guard pass.
