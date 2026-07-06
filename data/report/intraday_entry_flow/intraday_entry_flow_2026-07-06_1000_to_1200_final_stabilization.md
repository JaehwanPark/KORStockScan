# 2026-07-06 10:00~12:00 intraday entry flow final stabilization

- generated_at: 2026-07-06T12:00:00+09:00
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md
- source_events: data/pipeline_events/pipeline_events_2026-07-06.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-06.json
- decision_authority: source_quality_and_blocker_observation_only
- runtime_effect: false
- actual_order_submitted_by_this_report: false
- broker_order_forbidden_by_this_report: true
- forbidden_uses: runtime_threshold_mutation,broker_guard_bypass,provider_route_change,bot_restart,real_execution_quality_approval,hard_safety_relaxation,cap_or_quantity_change
- route: postclose_auto_analysis_handoff

## decision

`window_submit_drought_observation_not_critical_final`.

The 10:00~12:00 KST window did not show a full normal-submit drought. Normal submit/holding events were observed for `금호건설`, `한화오션`, `남광토건`, and `KBI메탈`; `에이디테크놀로지` had holding continuity from a prior submit. However, the window still produced many near-buy and rising/forced-scout observations that did not become normal BUY. The dominant residual patterns are:

- rising/forced one-share lineage is active and must remain separate from normal BUY success.
- spread/latency pre-submit guard delayed or blocked multiple near-buy candidates, but some of those later recovered to normal submit.
- strategy rejects and source freshness/backpressure dominated non-major blockers.
- some row-level current report submit counts are weaker than JSONL event evidence; event JSONL is the authoritative lifecycle source for final stabilization.

No intraday threshold/env mutation, provider change, bot restart, broker guard bypass, hard-safety relaxation, or quantity/cap change is supported by this report.

## evidence

### current flow summary

- symbol_count: 30
- rising_symbol_count_by_max_delta: 9
- buy_signal_or_pre_submit_pass_seen_symbols: 14
- real_submit_symbol_count_in_latest_diagnostic: 1
- stale_eval_symbol_count: 21
- stale_refresh_recovered_symbol_count: 17
- rising_missed_forced_scout_event_count: 145 in current flow report
- rising_missed_forced_scout_event_count from JSONL stage scan: 179
- rising_missed_residual_excluding_forced_scout_symbol_count: 0

### ten-minute window observations

| window | normal real submit/holding | forced/rising one-share lineage | notable non-normal evidence |
| --- | --- | --- | --- |
| 10:00~10:10 | 금호건설 submit; 에이디테크놀로지 holding_started | 금호건설, KBI메탈, SK스퀘어, 한화시스템 | KBI메탈 AI 70 latency_state_danger; 금호건설 later hard stop |
| 10:10~10:20 | none | KBI메탈, SK스퀘어, 한화시스템 | KBI메탈 latency_state_danger repeated |
| 10:20~10:30 | none | 금호건설, KBI메탈, SK스퀘어, 한화시스템 | KBI메탈 AI 70 latency; 파세코/엠앤씨솔루션 sim or weak signals |
| 10:30~10:40 | 금호건설 submit and holding_started | 금호건설, KBI메탈, SK스퀘어, 한화시스템 | 파세코 OpenAI timeout event; SK이노베이션 AI 75 sim-only |
| 10:40~10:50 | 한화오션 submit and holding_started | 금호건설, KBI메탈, 한화시스템 | 신한지주 74 WAIT; KBI메탈 latency continued |
| 10:50~11:00 | none | 금호건설, KBI메탈, SK스퀘어, 한화시스템 | 에이디테크놀로지 +0.78 exit; 두산에너빌리티 -3.16 exit; SK이노베이션 78 sim-only |
| 11:00~11:10 | none inside strict window | 금호건설, KBI메탈, 남광토건, 한화시스템 | 남광토건 submit occurred at 11:10:35, handled in next bucket |
| 11:10~11:20 | 남광토건 submit; KBI메탈 submit and holding_started | 금호건설, KBI메탈, 남광토건, 한화시스템 | KBI메탈 latency recovered to safe_normal_entry_allowed |
| 11:20~11:30 | none | 금호건설, KBI메탈, 한화시스템 | 파세코 AI 75 safe snapshot without order_bundle_submitted in this window |
| 11:30~11:40 | 남광토건 submit and holding_started | 금호건설, KBI메탈, 남광토건, 한화시스템 | 마키나락스/삼성공조 AI 75 but latency/sim-only |
| 11:40~11:50 | none | 금호건설, KBI메탈, 남광토건, 한화시스템 | KBI메탈 +0.52 exit |
| 11:50~12:00 | none | 금호건설, KBI메탈, 남광토건, 한화시스템 | 남광토건 AI 75 rising_missed submit blocked; no new normal submit |

### normal submit / holding / exit from JSONL

| time | symbol | event | note |
| --- | --- | --- | --- |
| 10:00:41 | 에이디테크놀로지 | holding_started | prior submit continuity |
| 10:03:14 | 금호건설 | buy_signal_telegram_enqueued / order_bundle_submitted | caution_normal_entry_allowed |
| 10:36:57 | 금호건설 | buy_signal_telegram_enqueued / order_bundle_submitted | caution_normal_entry_allowed |
| 10:37:01 | 금호건설 | holding_started | normal holding |
| 10:41:43 | 한화오션 | buy_signal_telegram_enqueued / order_bundle_submitted | caution_normal_entry_allowed |
| 10:42:02 | 한화오션 | holding_started | normal holding |
| 11:10:35 | 남광토건 | buy_signal_telegram_enqueued / order_bundle_submitted | caution_normal_entry_allowed |
| 11:14:46 | KBI메탈 | buy_signal_telegram_enqueued / order_bundle_submitted | safe_normal_entry_allowed |
| 11:16:45 | KBI메탈 | holding_started | normal holding |
| 11:34:16 | 남광토건 | buy_signal_telegram_enqueued / order_bundle_submitted | safe_normal_entry_allowed |
| 11:35:06 | 남광토건 | holding_started | normal holding |

Post-sell outcomes in the same window:

| time | symbol | profit_rate | exit_rule | source |
| --- | --- | ---: | --- | --- |
| 10:08:48 | 금호건설 | -3.16 | scalp_preset_hard_stop_pct | PRESET_HARD_STOP |
| 10:50:26 | 에이디테크놀로지 | +0.78 | scalp_low_profit_stagnation_hard_exit | MANUAL |
| 10:59:20 | 두산에너빌리티 | -3.16 | scalp_soft_stop_pct | HOLDING_FLOW_OVERRIDE |
| 11:04:02 | 금호건설 | +2.55 | scalp_trailing_take_profit | HOLDING_FLOW_OVERRIDE |
| 11:44:55 | KBI메탈 | +0.52 | scalp_low_profit_stagnation_hard_exit | MANUAL |

### blocker separation

Major observed blocker counts from JSONL stage scan:

- manual_control_excluded_symbol_blocked: 270
- blocked_strength_momentum / below_window_buy_value: 123
- blocked_strength_momentum / below_strength_base: 63
- blocked_ai_score: 62
- blocked_overbought: 57
- blocked_liquidity: 57
- blocked_vpw: 46
- latency_block / latency_state_danger: 27
- blocked_ai_score / ai_score_50_buy_hold_override: 23
- same_symbol_loss_reentry_cooldown: 2

Current report blocker taxonomy:

- runtime_backpressure: 720
- strategy_reject: 112
- pre_submit_quality_guard: 49
- watch_budget_reallocated: 29
- intended_guard: 22
- source_freshness_evictable: 21
- source_freshness_recovering: 5
- source_quality_exclusion_candidate: 2

Latency danger root causes from current report:

- 가온전선: 95, spread_microstructure_wide
- 한미반도체: 62, spread_too_wide
- 에코프로: 61, spread_microstructure_wide
- LG이노텍: 48, spread_microstructure_wide
- 삼성전자: 34, spread_microstructure_wide
- 에이디테크놀로지: 32, spread_microstructure_wide
- 두산에너빌리티: 28, spread_microstructure_wide
- KBI메탈: 20, spread_microstructure_wide
- 한화시스템: 9, spread_microstructure_wide
- 남광토건: 3, spread_microstructure_wide

## interpretation

1. Normal BUY did happen, so the window is not a critical normal-submit drought by itself.
2. KBI메탈 and 남광토건 show that repeated latency/spread blockers can recover into normal submit when the guard conditions improve.
3. 삼성공조, 마키나락스, and some 파세코 snapshots show near-buy or BUY-score candidates that did not become normal submit; these are postclose review candidates, not intraday guard bypass candidates.
4. The forced scout/rising missed line is large and active, but it is not counted as normal BUY success and must feed `one_share_threshold_opportunity` and rising-missed feedback/calibration only.
5. Current report row-level submit counts can understate JSONL lifecycle events for some rows. JSONL event evidence should be preferred for final lifecycle status, and report-consistency should be reviewed postclose.

## next action

- runtime action: monitor_only
- immediate code change: none
- postclose handoff:
  - rising_missed_intraday_feedback
  - rising_missed_scout_workorder
  - rising_missed_first_touch_calibration
  - one_share_threshold_opportunity
  - code_improvement_workorder
- additional postclose review candidates:
  - latency/spread recovery split: KBI메탈 and 남광토건 recovered; 삼성공조 and 마키나락스 did not.
  - report-consistency check: row-level submit count versus JSONL normal submit/holding events.
  - AI/transport note: 파세코 had a 10:39 OpenAI timeout and later safe snapshots without strict-window order submit.

## completion checks

- fixed current flow artifact updated: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-06_current.md
- final stabilization artifact retained: this file
- temporary CSV output: removed
- timestamped intermediate md/csv snapshots for this 10:00~12:00 goal: not retained
- final source_flow_final points to current md, not a deleted timestamp snapshot
