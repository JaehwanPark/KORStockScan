# Postclose release and verifier custody review (2026-09-16)

Scope: source-quality producer receipt repair, postclose verifier evidence custody, common release deployment and user-authorized graceful main restart. Independent machine unit pins, trading parameters, providers, quantities, custody and hard safety are unchanged.

## Yesterday: confirmed evidence versus unresolved cause

- The main wrapper used `integrated-sell-custody-r5-20260915-bc0889cd`. Its final checklist refresh completed at 22:13:33 KST. The verifier then returned `status=fail` at 22:14:15; the shell recorded only `reason=command_failed`. See [main log](../../logs/threshold_cycle_postclose_cron.log:20165).
- The first failing verifier artifact was replaced by later verification/recovery. The final remaining artifact is `warning`, generated 2026-09-16 01:18:01 KST, with source fingerprint PASS. This is a successor receipt, not evidence of the original failure contract.
- Later controller recovery used different immutable releases: `postclose-contract-order-r6-20260915-e341bcc6`, `postclose-empty-cohort-r7-20260915-e2c0ff42`, and `postclose-cleanup-generation-r8-20260915-916c675f`. Native paths are visible in [controller log](../../logs/postclose_done_controller_cron.log:19), [later recovery](../../logs/postclose_done_controller_cron.log:70) and [cleanup-generation recovery](../../logs/postclose_done_controller_cron.log:107).
- A changed release root by itself is not a broken source contract: data/docs are shared, while code is pinned separately. The surviving logs do not establish a Git/mount/router failure as the cause of the first 22:14 failure. Its exact failing contract is irrecoverable; do not claim that source exclusion or later DONE explains it.

Confirmed structural defects: generic shell failure attribution, overwritten verifier evidence, and a read/publish race between concurrent verifier consumers. Multiple recovery generations make missing execution provenance especially harmful.

## Repair and operating contract

1. A dated shared verifier lock serializes canonical read, first-failure selection and publication across releases. Unique attempt IDs and exclusive atomic publication prohibit replacing an existing attempt, including forced ID collisions.
2. Every immutable attempt and its receipt record the actual verifier path, file SHA256, executing project root and Git commit. These are execution evidence, not a read of the current selector or trading approval.
3. Canonical latest may advance to warning/PASS, but retains the original first-failure receipt. Shell status preserves the exact attempt/hash/failure summary; stale or non-failing canonical artifacts cannot be attributed to a new verifier failure.
4. Producer gap closure remains separate from raw sanitation: exclusion can allow bounded tuning input, but closure requires a producer repair receipt and post-fix natural zero recurrence.
5. The holding receipt uses receipt-time session/scope. Actual data route is not replaced by a clock-derived preference; missing route remains unknown. Actual execution venue is not inferred.
6. Switch the common selector only when scheduled wrappers are inactive. Preserve the previous selector and release for rollback. After authorized graceful restart, require a new PID receipt and exact-date runtime verification; selection/print-plan alone is not PID application.

## Today's recurrence conditions and next acceptance

- Frozen common release routing and shell snapshots already prevent mutable workspace shell/code mixing. Review/validation and a fresh PID transition address the current selector/PID difference.
- A different independent machine pin is not automatically a fault. Its 17 unit pins remain unchanged; do not broaden deployment or merge custody just to make commit strings equal. A late source producer can still invalidate final hashes: refresh affected sources -> tower -> checklist -> strict verifier before controller DONE/finalization.
- The new lock prevents first-failure pointer loss on concurrent publication; immutable execution provenance makes a later failure diagnosable. These changes do not guarantee every postclose contract will pass.
- Natural acceptance remains open: today's scheduled postclose chain must finish with matching final source hashes, strict summary handoff and controller/finalization receipts. The next session's post-fix audit must show no recurrence of the repaired producer defects. Missing source/outcome stays excluded/null, not fabricated.

Source validation: affected suites `1836 passed`; after the final route-provenance supplement, full sniper regression `1077 passed`. Python compile, shell syntax, Black checks for the affected receipt/verifier files, print-only backlog parser and diff checks passed. Re-review has no unresolved in-scope finding. Deployment and new-PID receipts are recorded separately in the runtime release selector; natural acceptance remains OPEN. No manual report regeneration, orders, env/threshold/provider mutation or independent service restart is authorized by this review.
