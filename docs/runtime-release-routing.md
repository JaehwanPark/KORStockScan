# Main runtime release routing

Owner: deployment infrastructure. Installed main routing is separate from exact-date trading approval. Widget/episode services use the separately authorized machine pin described below, not the main selector.

## Single selection

`data/runtime/runtime_release_selection.json` selects one absolute managed release root and its full Git commit. The workspace entrypoint is `bash deploy/run_runtime_release.sh`. It checks the selected HEAD, clean `src/deploy/restart.sh` and shared `data/logs/tmp/.venv/docs/restart.flag` before invoking a target. Missing or invalid selection blocks execution; it must not fall back to mutable workspace code.

The canonical workspace `restart.sh` delegates to this entrypoint. The reviewed release's original `restart.sh` is unchanged, preserving its policy code pin and custody-aware restart procedure. Do not call old release restart scripts or workspace `src/run_bot.sh` directly to choose a deployment. Do not edit or pull inside the selected release.

Supported operations: `start`, `restart`, `preopen`, `postclose`, `paired-replay`, `controller`, `tuning`, `finalize`, `eod`, `archive`. Invocation resolves the selection once and pins `PROJECT_DIR/PYTHONPATH/VENV_PY` for its child chain. The selector does not update an already-running supervisor; moving the current PID requires a separately authorized graceful restart.

Read-only checks from the canonical workspace:

```bash
bash deploy/run_runtime_release.sh restart --print-plan
bash deploy/run_runtime_release.sh preopen 2026-09-11 --print-plan
bash deploy/run_runtime_release.sh --check-cron
```

Use the actual target date instead of the example. A plan check proves routing, not future policy approval, WS health or a running PID.

## Scheduled scope and maintenance

Nine cron entrypoints use the selection: 07:35 PREOPEN, 07:55 main start, 20:05 EOD, 20:10 postclose/controller/tuning, 20:50 archive, 21:05 paired replay and 21:55 finalization. Existing schedule, environment values, log ownership/redirection and wrapper locks are preserved. Existing 07:30/20:10 stop behavior is unchanged; routing is not a redesign of shutdown semantics. Other intraday observer/scanner jobs and machine systemd services remain outside this scope.

After an authorized cron installer is run, check routing again: older installers can recreate workspace entrypoints. `bash deploy/run_runtime_release.sh --install-cron` reconciles exactly these nine rows, preserves unrelated rows and leading environment/log redirections (including main start), creates before/after backups in `tmp/runtime-release-cron-*`, rejects missing/duplicate/unrecognized commands and verifies readback. It recognizes an actual command owner, not an echo/printf/conditional containing the route. Scheduled `--print-plan` and unexpected extra arguments are rejected; dated jobs retain the existing KST cron date expression. Unsupported command syntax requires review, not an automatic rewrite. `--check-cron` only reads the current snapshot and does not create or wait on an installer lock. Installation uses a nonblocking lock; do not run it concurrently with another crontab editor. Direct out-of-band edits after its final recheck cannot be atomically prevented by the crontab interface.

For a release update: review and test only intended changes in a separate worktree, commit that release, mount shared state/docs, verify dated code/source pins, then atomically replace the selection file with the approved exact root/commit. Never switch while scheduled wrappers are running: separately started followers could otherwise select different releases. Keep the prior release and selector record for rollback. Do not erase data, reset quota or change policy to make a route pass. Shared `.venv` means dependencies are not immutable; package changes need their own approval and validation.

Restoring a cron backup is appropriate only after checking for subsequent unrelated edits; never overwrite a newer crontab wholesale. Rollback selection requires the prior release to pass the same shared-path and source checks, including the shared `docs` contract. Merely reverting a commit string is not enough.

## Acceptance boundaries

Source review and dry-run routes do not prove economic improvement or validate unfinished adaptive exit. Actual day-specific candidate/env/activation, operator overrides, runtime verification, KRX/NXT authority, quota and broker guards remain owned by the existing PREOPEN/launcher/policy contracts. Current source selection, actual PID consumption and natural trade/economic evidence must be reported separately.

## Separately authorized machine supplement (2026-09-10)

The user subsequently authorized deployment of the minimal profit-stagnation supplement, persistent for NEW entries from September 11. `data/runtime/machine_profit_stagnation_deployment.json` owns its exact release/commit/policy pin and nine machine service/preflight drop-ins. This does not select that release for main or scheduled postclose jobs. See the [deployment and rollback receipt](audit-reports/2026-09-10-machine-profit-stagnation-deployment.md).

The frozen machine release is `machine-profit-stagnation-20260911` / `273807e3`; `70-machine-profit-stagnation-release.conf` routes widget, low-price and Samsung service/preflight commands there. They share canonical data/state, not duplicate custody. Existing timers, profile quantities, target rules and safety checks remain. A workspace pull or a main selector change does not update these machine commands; a future authorized machine update must review these pins explicitly. Do not edit an active release.

Widget PID1138215 was started September 10 at19:19:33 with verified policy pins. Its continuous loop reads the dated policy, so activation on September11 does not depend on a timer restarting an already-active service. Verify the actual startup receipt date and subsequent live-policy consumption separately. Episode services retain their scheduled next-day startup/preflight and are not force-started by publication. The policy has no daily renewal requirement but never enrolls pre-September11 entries.

For rollback, revoke new candidates while retaining the current recovery consumer for pending supplementary orders. Do not remove its state or revert to old code until exact terminal/original-target restoration is reconciled. The main selector, existing broker holdings and old owner targets are not rollback targets for this supplement.

## Reviewed repair and all-scope additions update (2026-09-10 23:53 KST)

The explicitly authorized common repair release is now `postclose-repaired-20260911` / `939d90f6`. Its 10 V2.14 approval code hashes are unchanged; actual September 11 policy selection remains PREOPEN-owned. Main was already stopped and was not restarted. Nine cron routes verify successfully.

The machine update is `reviewed-additions-20260911` / `f9d53a9a`. Nine `80-machine-additions-release.conf` drop-ins override the earlier 70 drop-ins. `machine_additions_deployment.json` records the entry-adverse and target-ratchet pins; `machine_profit_stagnation_deployment.json` records the current root and unchanged persistent profit policy. Widget PID2651657 started at23:53:08; earlier PID1138215 is historical. Existing episode timers are retained. User approval explicitly covers all existing widget/episode scopes, effective for September11 new signals/entries, without symbol admission expansion or old holding enrollment. No single-scope restriction remains; existing timing-conflict, expiry, source freshness and order guards remain.

The [review and deployment receipt](audit-reports/2026-09-10-approved-additions-deployment.md) records validation and rollback. Keep prior release roots, policy files, original70 drop-ins and manifest backups. Before removing80 drop-ins or reverting code, reconcile pending amendment/supplement ownership to terminal or restored original target; never clear the ledger to enable rollback.

## September 11 unified code generation

The explicit September 11 request includes main, common postclose, widget and independent Samsung/low-price machines in one reviewed code generation. The deployment receipt is [SCALPING unification review](audit-reports/2026-09-11-scalping-unified-release-v214-review.md). A unified deployment must preserve each unit's arguments, timers, shared custody and exact policy hashes; matching code does not combine order owners or publish new machine trading parameters. The latest unified manifest/drop-in takes precedence over older deployment receipts, which remain rollback/history evidence. An active PID still needs a verified graceful transition; changing a selector or drop-in alone does not reload it.

The main Entry rollout is separately pinned by `KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH` and `KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256` in the existing operator handoff. The publisher is `src.engine.scalping.entry_setup_scalping_rollout`, with an aware effective timestamp, full reviewed commit and explicit `APPLY_ALL_SCALPING_V2_14` confirmation. It uses a new immutable file, preserves the existing global daily accepted-order ledger and execution guards, and remains effective until operator revocation. It does not relabel old PREOPEN candidates, alter Holding/Exit schemas or add AI calls to independent machines. Startup clears inherited rollout pins before reloading current operator settings. Future exact-date env validation remains required; daily reapproval of the same persistent rollout is not.

The separately authorized V2.15+ auto-promotion pin uses `KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH` and `KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_SHA256`, generated with `--auto-promotion --confirm APPLY_ALL_SESSIONS_V2_15_PLUS_AUTO_PROMOTION`. It covers the existing exchange/session scope plus integrated KRX/NXT aftermarket, but promotes only a registered V2.15+ candidate with exact-cohort postclose evidence and a same-policy-hash PREOPEN activation. Any absent, invalid, stale, or cross-cohort candidate falls back to V2.14; it does not change quantity, caps, broker guards, providers, or create new AI calls. The launcher clears both pins before it loads the current operator handoff.

### September 11 completed unified deployment

The explicit all-machine unification first selected `unified-scalping-r2-20260911` / `57a90bd9a19aa6baac5e78624eb9f0a27168b57a`. The later reviewed sell-timeout race repair superseded that code generation for main and all 17 current independent service/preflight/analysis routes through `zz-unified-runtime.conf`. `data/runtime/runtime_release_selection.json` and `data/runtime/unified_runtime_deployment.json` own the exact current release root and commit; earlier machine manifests preserve historical receipts and link the successor. Existing independent policy hashes, order/custody owners and schedules remain distinct. Future release changes must reconcile both the common selector and these unit pins; changing only the main selector does not reload independent services. See the [latest review and deployment receipt](audit-reports/2026-09-11-sell-timeout-race-custody-projection-review.md).
