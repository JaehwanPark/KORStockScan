# Limit-Down Rotation Observation Lane — 2026-07-28 PREOPEN Work Instruction

## Objective

- Start the already-reviewed, source-observation-only prior-limit-down rotation lane only after the current source and runtime-env handoff gates pass.
- Confirm that the new process loads `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=true` and applies the `general 1 / opening 2 / limit-down 1 / rising 12` watch-budget policy.
- Keep the lane strictly outside Recommendation, ACTIVE_TARGET, BUY analysis, broker submission, provider routing, threshold, price, quantity, cap, and safety-guard authority.

## Scope and Authority

- Target runtime date: `2026-07-28 KST`.
- This document authorizes only prestart inspection, the existing standard supervised start after an explicit operator start instruction, and post-start observation/provenance verification.
- It does not authorize a direct `bot_main.py` launch, duplicate tmux process, provider/model/route change, threshold change, order-price/quantity/cap change, broker-guard change, hard/protect/emergency safety change, or any hot environment mutation.
- The limit-down lane remains `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, and `decision_authority=limit_down_source_observation_only`.

## Current Prepared State

- `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-28.{env,json}` exists for the target date.
- `data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-07-28.env` is the final overlay loaded by `src/run_bot.sh` and sets `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=true`.
- Prestart handoff verification completed with `status=pass`, finding count `0`, runtime-policy fail count `0`, and dated-override fail count `0`.
- Effective observation budget precheck completed as `general=1`, `opening=2`, `limit_down=1`, `rising=12`, total `16`.
- The original no-process prestart condition is superseded by the completed supervised restart record below. There is exactly one active `bot_main.py` process, PID `729936`, started at `2026-07-28T08:20:14+09:00`.

## Current Execution Record — 2026-07-28 08:31 KST

- The first source attempt from the prior PID failed closed with `candidate_source_exception:TypeError`. The responsible `ka10081` `NaT` index handling was repaired; malformed date rows are excluded per symbol and an all-invalid daily index remains blocked.
- Review gate closed with no unresolved finding. Relevant regression suite: `1,048 passed`; compile, shell syntax, checklist parser, and `git diff --check` passed.
- The existing supervised path restarted gracefully through `restart.flag`: PID `712183` exited, and `src/run_bot.sh` started PID `729936`. Target-date PID handoff is `status=pass`, `pid_passed=true`, with no missing or mismatched runtime key.
- The new PID loaded the dated limit-down flag as `true`, the reviewed dirty-source provenance, holding-score `gpt-5.4-nano`, holding-flow `gpt-5.4-mini`, and non-empty `holding_flow` Bedrock fallback configuration. No provider route was changed by this work.
- Official source artifact is `partial`: 3 valid candidates and 1 isolated `ka10081_no_valid_completed_dates` block. The first active observation, `131100`, was a source-quality `pass` `single_limit_down` row with one requested WS item and the observation-only authority contract.
- `131100` remained `WAITING_FIRST_TICK` with no trade tick, recorded a `first_tick_pending` re-REG/heartbeat, and then rotated after its bounded no-tick dwell. Ordered raw-`0B` capture therefore remains pending.
- The next candidate, `336260`, was registered once and then claimed by the normal scanner on an independent scanner promotion. The observation registry released it with `reason=normal_scanner_claimed` and `keep_ws=true`; no intermediate lane UNREG was sent. This is a successful ownership handoff, not a limit-down-lane BUY or order authority event. At that handoff moment, the observation registry had no active code until the next reconcile.
- The third candidate, `465770`, was also registered, received its `first_tick_pending` re-REG/heartbeat, and rotated after bounded no-tick dwell with the expected lane UNREG. `131100` was then revisited after cooldown and received another `first_tick_pending` re-REG at 08:31 KST. The current active observation is therefore `131100`; ordered raw-`0B` capture is still pending natural trade activity.
- No lane-attributable Recommendation, ACTIVE_TARGET, BUY analysis, broker order, requested quantity, Telegram-buy, or trade-signal event is present.

## Pass 1 — Start Gate (Completed)

1. Confirm there is no duplicate `bot_main.py` or `run_bot.sh` process before any operator-start action.
2. Re-run the target-date handoff gate:

   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.threshold_cycle_preopen_apply --verify --target-date 2026-07-28
   ```

   Required result: `status=pass`, no findings, no dated-override failure.

3. Reconfirm the actual load order is `threshold_runtime_env_2026-07-28.env -> operator_runtime_overrides.env -> operator_runtime_overrides_2026-07-28.env`; the dated file must remain present and the effective final value must be `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=true`.
4. Review the current dirty source paths before starting. The currently dirty holding-context/preopen-handoff changes must close through `korstockscan-review-gate`, relevant targeted tests, and `git diff --check`; do not launch a new runtime from unreviewed source.
5. Confirm the effective entry/holding provider configuration is non-empty. A future natural AI event with `provider=none` is an incident to record and investigate; do not compensate by changing a provider route in this task.

If any gate fails, do not start the bot. Record the failed gate and repair only the responsible source/configuration path through review before retrying.

Result: the initial candidate-source gate failed closed, the narrow source repair was review-gated, and all required start gates passed before the supervised restart.

## Pass 2 — Standard Supervised Start (Completed)

1. Start only after an explicit operator start instruction, through the existing `tmux bot` / `src/run_bot.sh` supervised path defined by the runbook. Do not invoke `bot_main.py` directly or create a second supervisor.
2. Read the startup log and verify the three runtime sources were echoed, including the dated `operator_runtime_overrides_2026-07-28.env` file, before the bot process starts.
3. Capture the new `bot_main.py` PID, start timestamp, loaded commit, and `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY` provenance. A source-dirty value is not silently accepted; it must correspond to the review-gated source state from Pass 1.
4. Run target-date PID handoff verification:

   ```bash
   PYTHONPATH=. .venv/bin/python -m src.engine.threshold_cycle_preopen_apply --verify --target-date 2026-07-28 --pid <BOT_PID>
   ```

   Required result: `status=pass`, `pid_passed=true`, no required-key mismatch or missing key.

Result: completed through the existing supervisor; do not create another process or repeat a start action while PID `729936` is healthy.

## Pass 3 — First Observation and Isolation Checks (In Progress)

1. Confirm runtime state records the policy version `general1_opening2_limitdown1_rising_residual_v1`.
2. If official `ka10017` candidates are available, verify one active observation has:
   - official request/response provenance hash, valid `cnt` cohort, completed daily-close/date match, and no source-quality block;
   - actual WS route/item count within the existing cap;
   - first ordered raw `0B` tick and state/snapshot heartbeat.
3. If no valid candidate exists, record `no_eligible_limit_down_candidate`; rising may borrow the slot. Do not synthesize a candidate or issue a probe order.
4. Verify the lane has zero `RecommendationHistory`, `ACTIVE_TARGET`, `SCALPING_SCANNER_PROMOTED_TARGET`, BUY-analysis, `TRADE_SIGNAL_DETECTED`, broker-order, requested-quantity, or Telegram-buy events attributable to `LIMIT_DOWN_WATCH`.
5. Confirm any observed AI/provider audit row has `provider != none`; this is a provenance check only and does not permit a provider configuration change.

Current Pass 3 result: source provenance, cohort, completed-close match, requested WS item cap, heartbeat, bounded no-tick rotation, normal-scanner ownership handoff, and trade-authority isolation are confirmed. The valid rows have no source-quality block; the one blocked source row is excluded. Raw-`0B` capture and actual WS route/item confirmation remain pending a natural observation tick. Keep observing; do not synthesize a tick, force a candidate, or issue a probe order.

## Rollback and Incident Boundary

- Roll back only the limit-down observation lane when source quality blocks the candidate, WS REG item cap is exceeded, the observation registry leaks, ordered raw-tick capture fails after a valid active candidate, or trade authority leaks.
- Rollback action: set `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=false` in the dated override, release the active observation code, and use the standard graceful restart path. The legacy `opening 3` policy then resumes automatically.
- Do not alter provider, threshold, price, quantity, cap, broker guard, or other scanner owners as part of this rollback.

## Completion Criteria and Report

Close the checklist item only after reporting:

1. Decision: `started_and_limit_down_on`, `started_no_eligible_candidate`, `blocked_prestart_gate`, or `rolled_back_observation_lane`.
2. Evidence: handoff/PID verification, loaded dated override, policy/budget, source/PID provenance, WS route/items, candidate or no-candidate reason, and zero-trade-authority check.
3. Next action: continue source-only observation, collect the postclose diagnostic report, repair the named gate, or retain rollback.

`no_eligible_limit_down_candidate` is a valid ON-state result; it is not evidence that the flag or budget policy failed.

Current decision: `started_and_limit_down_on`, with Pass 3 raw-tick capture pending. The next action is continued source-only observation through a future natural raw-`0B` capture, bounded no-tick rotation, or normal-scanner ownership handoff, followed by the postclose diagnostic report.

## 2026-08-03 Persistent Daily Extension

- The observer is now a persistent daily launcher policy. `src/run_bot.sh` defaults `KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED=true`, and the persistent `operator_runtime_overrides.env` records the same explicit operator decision. A dated or persistent explicit `false` remains the rollback authority.
- The postclose wrapper runs `limit_down_watch_report` every day unless `THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT` explicitly disables it. A missing candidate source is therefore reported as missing observer activation instead of silently skipping the check.
- `conversion_readiness` checks daily source integrity, rolling ordered-path sample floors, counterfactual clean-baseline EV, sim-policy handoff, post-sim attribution, and the separate user live-conversion approval artifact.
- Counterfactual and post-sim EV artifacts must declare the complete metric contract (`metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, and `forbidden_uses`). Sim-policy and approval artifacts must use their dedicated source-only authority labels; incomplete or mismatched contracts remain `invalid` with field-level issues.
- The automated decision is limited to `keep_observing_and_build_evidence`, `operator_live_conversion_approval_required`, or `approved_for_separate_preopen_apply`. It always keeps `automatic_live_conversion_performed=false`, `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, and `allowed_runtime_apply=false`.
- Even `approved_for_separate_preopen_apply` is a readiness signal only. Real-order authority requires a separately reviewed PREOPEN apply with an explicit rollback guard; the postclose job never changes orders, thresholds, providers, quantity, caps, broker guards, or bot state.
