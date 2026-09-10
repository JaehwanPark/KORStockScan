# Main runtime release routing

Owner: deployment infrastructure. Installed routing is separate from exact-date trading approval. Widget/episode services and the ongoing adaptive-exit implementation are outside this change.

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
