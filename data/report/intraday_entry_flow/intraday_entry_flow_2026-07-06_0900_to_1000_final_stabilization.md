# Intraday Entry Flow Final Stabilization - 2026-07-06 09:00~10:00 KST

- decision: `window_submit_drought_observation_not_critical_final`
- generated_at: `2026-07-06T10:00:00+09:00`
- source_flow_final: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md`
- source_events: `data/pipeline_events/pipeline_events_2026-07-06.jsonl`
- sentinel_sources: `data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-06.json`, `data/report/holding_exit_sentinel/holding_exit_sentinel_2026-07-06.json`
- decision_authority: `source_quality_and_blocker_observation_only`
- runtime_effect: `false`
- forbidden_uses: `runtime_threshold_mutation,broker_guard_bypass,provider_route_change,bot_restart,real_execution_quality_approval`

## Decision

The 09:00~10:00 flow was identified with usable intraday source evidence and the fixed current artifact was refreshed for the exact window. This window is not a normal-submit-zero drought: normal real submit occurred for three symbols, while forced scout lineage was kept separate from normal BUY/submit/fill evidence.

Real runtime reflection is not opened by this report. Remaining work is postclose source-only handoff and bounded PREOPEN review for the observed upstream AI/latency/source-quality blockers.

## Evidence

### Window Summary

- current flow summary: symbol_count=`36`, rising_symbol_count_by_max_delta=`13`, buy_signal_or_pre_submit_pass_seen_symbols=`17`, stale_eval_symbol_count=`30`, stale_refresh_recovered_symbol_count=`21`
- normal submit symbols: `두산에너빌리티(034020)`, `한화시스템(272210)`, `에이디테크놀로지(200710)`
- normal submit events:
  - `09:14:42` `두산에너빌리티(034020)` order_bundle_submitted reason=`caution_normal_entry_allowed`
  - `09:18:34` `한화시스템(272210)` order_bundle_submitted reason=`caution_normal_entry_allowed`
  - `09:59:08` `에이디테크놀로지(200710)` order_bundle_submitted reason=`safe_normal_entry_allowed`
- forced scout lineage was present in interval evidence but is not counted as normal BUY success.
- rising_missed_forced_scout_event_count in the current flow report remains `0` for this exact 09:00~10:00 flow artifact because forced scout lineage rows were not classified as new forced one-share entry events in the flow report.

### 10-Minute Checkpoints

| window | symbols | buy candidates | normal submit symbols | forced/scout lineage symbols | key observations |
| --- | ---: | ---: | --- | --- | --- |
| 09:00 | 56 | 4 | - | SK스퀘어, 에이디테크놀로지, 한화시스템 | latency_danger=`16`, stale=`21`, runtime_backpressure=`46`, cooldown=`1` |
| 09:10 | 29 | 6 | 두산에너빌리티, 한화시스템 | SK스퀘어, 에이디테크놀로지, 한화시스템 | normal submit recovered; latency_danger=`24`, runtime_backpressure=`62` |
| 09:20 | 28 | 7 | - | SK스퀘어, 에이디테크놀로지 | stale=`58`, cooldown=`4`, no normal submit |
| 09:30 | 35 | 6 | - | SK스퀘어, 에이디테크놀로지, 한화오션 | source_quality_exclusion=`1`, latency_danger=`12` |
| 09:40 | 33 | 9 | - | SK스퀘어, 에이디테크놀로지 | stale=`76`, runtime_backpressure=`37` |
| 09:50 | 37 | 6 | 에이디테크놀로지 | KBI메탈, SK스퀘어, 에이디테크놀로지, 한화오션 | normal submit recovered at 09:59; latency_danger=`10`, stale=`33` |

### Normal Submit And Holding/Exit

- `두산에너빌리티(034020)`: normal submit and holding started. Holding snapshots show AVG_DOWN blocked mostly by `pnl_out_of_range`, not by broker guard bypass.
- `한화시스템(272210)`: normal submit, holding, then real sell path completed at `09:49:49` with sell_completed profit_rate=`+0.59`. PYRAMID was blocked at profit-positive points by `profit_not_enough` or `pyramid_quality_blocked:ai_score_below_min,tick_accel_stale,micro_context_stale`.
- `에이디테크놀로지(200710)`: normal submit recovered at `09:59:08` after earlier latency/spread blocks.

### Sentinel Boundary

- BUY Funnel Sentinel as_of=`2026-07-06T10:00:01`:
  - primary classification=`UPSTREAM_AI_THRESHOLD`
  - secondary includes `LATENCY_DROUGHT`
  - entry_submit_drought_contract critical=`false`
  - stage_unique: ai_confirmed=`18`, budget_pass=`8`, latency_pass=`4`, order_bundle_submitted=`3`
  - ratios: submitted_to_ai_unique_pct=`16.7`, submitted_to_budget_unique_pct=`37.5`
  - runtime_effect=`false`, allowed_runtime_apply=`false`
- Holding/Exit Sentinel as_of=`2026-07-06T10:00:01`:
  - primary classification=`HOLD_DEFER_DANGER`
  - sell execution scope separates real/non-real exit evidence
  - runtime_effect=`false`

## Next Action

- route: `postclose_auto_analysis_handoff`
- handoff targets: `rising_missed_intraday_feedback`, `rising_missed_scout_workorder`, `rising_missed_first_touch_calibration`, `one_share_threshold_opportunity`, `code_improvement_workorder`
- immediate code change: `none`
- runtime action: `monitor_only`
- PREOPEN eligibility: only bounded candidates that pass postclose source-quality, sample floor, AI/deterministic guard, same-stage owner rule, and hard-safety guard may become next PREOPEN `auto_bounded_live` env.

## Cleanup

- Fixed current artifact retained: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md`
- This final stabilization file points to the fixed current artifact, not a deleted timestamp snapshot.
- Timestamped md/csv snapshots were not retained for this 09:00~10:00 window.
