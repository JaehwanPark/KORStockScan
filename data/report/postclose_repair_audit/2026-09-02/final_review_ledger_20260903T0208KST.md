# 2026-09-02 postclose repair and final review ledger

- review_completed_at_kst: `2026-09-03T02:08:29+09:00`
- reasoning_effort: `high`
- target_date: `2026-09-02`
- next_preopen_date: `2026-09-03`
- repository_branch: `main`
- repository_commit: `816ff339c41071a00cf2ba90c3cee7ff4da69715`
- source_dirty: `true` (existing user and generated-artifact changes preserved)
- authority: `runtime_effect=false`; no live env, order, provider, bot, cap, threshold, broker guard, or hard-safety mutation
- official_kiwoom_reference: `Kiwoom-Securities/Kiwoom-REST-API@234560d213acd8871ae344b5481aecd2f30287fa`, inspected `2026-09-03T01:16:11+09:00`

## Review result

- Final code-review finding count: `0` within the changed-path producer/consumer and authority-leak coverage.
- Final changed-path validation: `1431 passed`, one non-blocking third-party `pandas_ta` deprecation warning.
- The finalizer-focused regression subset passed after correcting prefixed controller failure classification.
- Python compile, shell syntax, checklist parser validation, and `git diff --check`: `pass`.

## Defects closed

1. The scanner-pruned cohort now has a bounded, source-only executable-BBO collector and explicit schedule/observation provenance. Full census and sampled executable-price evidence remain separate, and sampled results cannot be extrapolated to the full population.
2. Entry ADM outcome-join validation now compares only Entry ADM-relevant evaluations, avoiding terminal-only rows being reported as an entry source gap.
3. Final postclose ordering now refreshes pattern propagation and persisted AI provenance before final EV/workorder generation.
4. Limit-down observation explicitly requests both Kiwoom `0B` and `0D`; missing ordered-path evidence remains fail-closed until a new natural run supplies it.
5. Cleanup and the final detector are now owned by a terminal-aware 21:55 finalizer. Predecessor fail/error/blocked prefixes fail closed; cleanup is skipped on failure/timeout so originals are preserved.
6. Workorder generation contract v3 recognizes verified scanner-BBO and quiet-low-liquidity implementation states instead of reopening them as `implement_now`.

## Workorder two-pass conservation

### Intake

- generation_id: `2026-09-02-6e5bfe22f7f3`
- source_hash: `c886dd4e6e9bf7ded7ee62b0b0bebce74ea94286848e3e77f85d0d80dea536b0`
- selected/non-selected/source/unique: `50/19/69/69`
- implement_now: `1`
- order_id: `order_scanner_funnel_executable_bbo_join`
- runtime_effect/allowed_runtime_apply: `false/false`

### Final fixed point

- generation_id: `2026-09-02-5dc957b0ddb5`
- source_hash: `20d3e913b0402baefc5562b32c8cf7741fb7be738a4d8992567dd3fdc84fa1d6`
- preceding same-source generation: `2026-09-02-0203853d6927`
- selected/non-selected/source/unique: `49/20/69/69`
- duplicate or blank order IDs: `0`
- implement_now_total: `0`
- eligible new or decision-changed implement_now between the latest two generations: `0`
- final_eligible_actionable_open_count: `0`
- implement_now_unaccounted_count: `0`
- disposition: scanner BBO and quiet-low-liquidity orders are `attach_existing_family` with implemented source-quality contracts; natural sample acceptance remains open and does not grant runtime authority.

## Ordered regeneration

- pre-snapshot: `review_gate_pre_regen_20260903T014523KST/pre_regeneration_manifest.md`
- source-quality audit: `pass`, `tuning_input_allowed=true`, hard-blocking contract gaps `0`, review warnings `0`
- final workorder SHA-256: `3747692dc6ecb671556c931361dfeff69504e5ad0af2e4ec71ade7a4b84e3c2b`
- final verifier SHA-256: `3b9370a5f269f5d0c0459513295f4897e5a9702b693d4b2fa2eb330ad6d3872d`
- final controller SHA-256: `2febdddc417eef0db9b8b55d49b00212672d142a76c0333531cd55939fb589e6`
- verifier: `warning`, with missing required artifacts/downstream links/stale links/source-generation warnings all `0`
- controller: `done`, `allow_wrapper_rerun=false`, `full_wrapper_rerun_used=false`, no recovery action
- controller wrapper: exact-date latest `[DONE]` at `2026-09-03T02:04:21+09:00`

## Remaining warnings and acceptance

1. `lifecycle_bucket_discovery_mtd_parent_granularity_not_target`: MTD parent count `22`, target floor `30`; source contract passes. Keep promotion fail-closed and re-evaluate after new floor-qualified rows. No finite ETA is asserted without a declared conservative forecast contract.
2. `lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target`: rolling-5d parent count `28`, target floor `30`; rolling-10d count `45` passes. Recalculate arrivals and expiries at the next postclose; do not merge owners or lower the floor.
3. `limit_down_watch_ordered_path_not_observed`: the historical 2026-09-02 run lacks ordered `0B+0D` evidence. State is `collecting_after_structural_repair`, not resolved. Acceptance requires a new exact-session natural sample showing same-symbol/session ordered `0B+0D`, source-quality pass, and downstream report/verifier lineage.

These warnings remain source-only/live-promotion blockers. They do not authorize a runtime or real-order change.

## 2026-09-03 PREOPEN handoff

- Preopen wrapper is installed for `07:35`; the main bot starts as a fresh process at `07:55` through `src/run_bot.sh -> src/bot_main.py -> src.scanners.scalping_scanner.run_scalper`.
- At review time the main bot was correctly absent before its scheduled window; no manual restart was performed.
- The 2026-09-02 bounded candidate is date-scoped for effective date `2026-09-03`, status `bounded_exploration_apply_ready`, authority `preopen_date_scoped_krx_prompt_selection_only`, and `runtime_effect=false`.
- Actual 2026-09-03 apply-plan/runtime-env generation, loader verification, PID consumption, and natural sample acceptance are `not_yet_due`; the 2026-09-03 checklist owns those PREOPEN checks.
- Installed postclose schedule uses owned logs, omits the old 21:00 cleanup, runs normal detector windows through 21:50, and runs terminal-aware finalization at 21:55.

## Control state

- Tuning Chain Control State: `YELLOW`
- Reason: code and workorder fixed point are closed, but two sample-window warnings and one post-repair natural observation acceptance remain.
- Escalation: any missing/stale 2026-09-03 PREOPEN artifact, old PID policy consumption, absent scanner BBO observation when a scheduled cohort exists, or missing ordered limit-down `0B+0D` lineage must remain fail-closed and be reported against the owning checklist item.
