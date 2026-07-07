# 2026-07-07 09:00~11:00 Intraday Entry Flow Final Stabilization

- generated_at: 2026-07-07T11:00:00+09:00
- source_flow_final: /home/ubuntu/KORStockScan/data/report/intraday_entry_flow/intraday_entry_flow_2026-07-07_current.md
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-07.jsonl
- event_window_since: 09:00:00
- event_window_until: 11:00:00
- decision_authority: source_quality_only
- runtime_effect: false
- allowed_runtime_apply: false

## Decision

- 유효한 source event 기준으로 09:00~11:00 BUY 전 흐름을 식별했다.
- 상승 또는 BUY 후보 접근 후 normal BUY/submit/fill/holding/exit로 이어지지 않은 핵심 흐름은 `monitor_only` 및 postclose source-only handoff 대상이다.
- `rising_missed_one_share_entry`/forced scout는 일반 BUY 성공으로 세지 않고 별도 source-only 기회비용 증거로 분리했다.
- real runtime 반영은 현재 열지 않는다. 다음 PREOPEN `auto_bounded_live` 후보가 되려면 postclose handoff 산출물, source-quality gate, sample floor, EV/guard 검증을 통과해야 한다.

## Evidence

- 전체 symbol_count: 28
- rising_symbol_count_by_max_delta: 4
- buy_signal_or_pre_submit_pass_seen_symbols: 18
- normal submit 미진입 핵심 rising rows:
  - 가온칩스(399720): max_delta 12.16%, actual_submit_count 0, main blocker `latency_state_danger`, latency root cause `spread_microstructure_wide`
  - 에코프로(086520): max_delta 3.75%, actual_submit_count 0, main blocker `ws_snapshot_missing_or_zero_recovered`
  - 칩스앤미디어(094360): max_delta 3.25%, actual_submit_count 0, main blocker `entry_cooldown_active`
  - 금호건설(002990): max_delta 1.98%, actual_submit_count 0, main blocker `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- forced scout observation:
  - event_count: 31
  - symbol_count: 11
  - symbols: 002990, 004980, 037710, 073240, 086520, 094360, 095500, 101730, 114190, 200710, 399720
  - rising_missed_residual_excluding_forced_scout_symbol_count: 0
- stale/source-quality split:
  - stale_eval_symbol_count: 22
  - rising_stale_eval_symbol_count: 4
  - stale_refresh_recovered_symbol_count: 20
  - rising_fresh_only_symbol_count: 0
- diagnostic freshness:
  - real_submit_symbol_count_in_latest_diagnostic: None
  - current report therefore uses live pipeline events as the authoritative source for this intraday window.

## Next Action

- postclose handoff:
  - `rising_missed_intraday_feedback`
  - `rising_missed_scout_workorder`
  - `rising_missed_first_touch_calibration`
  - `one_share_threshold_opportunity`
  - `code_improvement_workorder`
- expected workorder focus:
  - keep forced scout lineage separated from normal BUY/submit/fill success metrics
  - review 가온칩스 `spread_microstructure_wide`/latency danger as preserved guard evidence, not an intraday guard bypass request
  - review 에코프로/칩스앤미디어/금호건설 as source-only missed-entry opportunity and blocker evidence
- forbidden uses:
  - no intraday threshold mutation
  - no stale quote, broker, account, order, cooldown, quantity, hard/protect/emergency guard bypass
  - no provider route, bot restart, cap release, or real-order authority change from this artifact alone
