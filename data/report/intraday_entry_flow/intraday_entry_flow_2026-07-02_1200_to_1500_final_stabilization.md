# 2026-07-02 12:00-15:00 KST intraday entry flow final stabilization

- generated_at: 2026-07-02T15:00:00+09:00
- window: 2026-07-02T12:00:00+09:00 to 2026-07-02T15:00:00+09:00
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-02_current.md
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-02.json
- decision_authority: intraday_source_quality_and_blocker_diagnostic_only
- runtime_effect: false
- allowed_runtime_apply: false
- code_fix_commit: bf8cd0c6

## Decision

- Final stabilization decision: monitor-only closed. No additional intraday code, threshold, provider, bot, broker, stale-submit, account/order, quantity, cooldown, hard-safety, protect-safety, or emergency-safety mutation is allowed from this window.
- Normal BUY/submit/fill residual after excluding `rising_missed_one_share_entry` forced scout events is 0.
- `rising_missed_buy` remains diagnostic/source-quality evidence, not normal BUY success/failure evidence. Final class count is 5 `intended_guard_preserved` and 1 `source_quality_excluded`.
- One-share follow-up threshold opportunity-cost candidate exists at the score 60-62 bucket, but it is postclose counterfactual/workorder material only. It is not intraday BUY score relaxation authority.

## Evidence

- `entry_event_count`: 25582
- `promoted_symbol_count`: 49
- `real_submit_symbol_count`: 0
- `buy_signal_or_pre_submit_pass_seen_symbols`: 24
- `rising_missed_buy_count`: 6
- `rising_missed_residual_excluding_forced_scout_symbol_count`: 0
- `rising_missed_one_share_eligible_symbol_count`: 0
- `rising_missed_forced_scout_event_count`: 343
- `rising_missed_forced_scout_symbol_count`: 7
- `rising_missed_full_eval_budget_deferred_count`: 2
- `rising_missed_full_eval_budget_deferred_symbol_count`: 1
- `suppressed_non_actionable_blocker_count`: 763
- `actionable_major_blocker_count`: 211
- `rising_missed_low_ai_or_negative_pressure_eval_quality`: fresh 3, stale_or_delayed 120, unknown 14
- `rising_missed_stale_or_delayed_eval_category_counts`: diagnostic_quote_age_stale 115, pre_ai_stale_or_history_gap 5, full_eval_delay 0, pre_submit_hard_stale 0, ws_quote_missing 0

## Root Causes

1. Source freshness before threshold tuning
   - Final top priority is `scanner_strength_history_or_stale_eval`.
   - Decision: `fix_observation_freshness_before_threshold_tuning`.
   - Evidence: 115 diagnostic quote-age stale findings and 5 pre-AI stale/history-gap findings among rising missed low-AI/pressure events.
   - Runtime effect: false.

2. Score/baseline prior opportunity-cost candidate
   - Decision: `do_not_relax_score_without_fresh_positive_context_and_rolling_confirmation`.
   - The one-share/BUY-candidate opportunity-cost suspicion is strongest at score 60-62:
     - `007610` 선도전기: latest AI score 60, threshold 75, max delta 2.37%, class `source_quality_excluded`.
     - `013580` 계룡건설: latest AI score 61, threshold 75, max delta 7.55%, final blocker `blocked_ai_score_below_buy_score_threshold`.
     - `001260` 남광토건: latest AI score 62, threshold 75, max delta 5.11%, final blocker `latency_state_danger`.
   - This bucket needs postclose fresh-context separation and rolling confirmation before any runtime reflection.

3. Preserved entry guards
   - `entry_cooldown_active`, `scanner_fast_precheck_stability_pending`, `latency_state_danger`, stale quote, and spread/liquidity guard rows remain preserved.
   - `pre_submit_hard_stale` is 0, so there is no evidence for stale-submit bypass.
   - The 12:27 `378340` stale-context submit revalidation and 12:57 `000270` cancel path remain price/submit-quality attribution, not a guard relaxation reason.

4. Runtime backpressure and watch-budget routing
   - Final taxonomy contains 716 `runtime_backpressure`, 194 `strategy_reject`, 21 `intended_guard`, 18 `pre_submit_quality_guard`, 13 `watch_budget_reallocated`, 8 `source_freshness_recovering`, 3 `source_freshness_evictable`, and 1 `source_freshness_blocker`.
   - The deferred full-eval count stayed at 2 for 1 symbol and reached `deferred_then_evaluated`, so it is not a final never-evaluated BUY blocker.

## Next Action

- Postclose workorder input: split score 60-62 one-share profitable/rising cases by fresh context, stale/history gap, latency danger, and cooldown state before any threshold EV interpretation.
- Postclose source-quality input: inspect WS strength/momentum history and bounded subscription/recheck flow for the stale-eval priority.
- Keep forced one-share scout events excluded from normal BUY/submit/fill success, real execution quality approval, and threshold/runtime apply evidence.
- No bot restart, provider route change, threshold mutation, stale-submit bypass, broker/order guard relaxation, quantity/cap release, or safety guard relaxation was performed.
