# 2026-09-21 preflight / submission bottleneck repair

Scope: user-authorized defect repair, immutable deployment and graceful main-bot restart. Existing dirty widget/process-health changes are excluded. No threshold, provider, sizing, custody or source-freshness guard changes.

## Cause and repair

- Retired pre-cutover context promotion files triggered a baseline rollback without a baseline artifact date. The consumer selected a nonexistent current-day baseline and returned `artifact_missing` before machine assessment. The rollback now binds the original date and SHA-256 of the protective baseline available before that promotion; explicit prior pins take precedence. Missing, invalid, future or hash-mismatched evidence fails closed. This baseline is a protective rule version, not current-day market evidence. Exact live source checks and the existing process handoff remain mandatory.
- The monitor labeled source-invalid attempts with an economic event gap despite their `not_applicable_machine_source_invalid` status. Economic gaps now apply only to evaluated machine actions; source alerts use the recorded source blocker.
- `KRX_LIKE_PREMARKET` and `PREMARKET_KRX_LIKE` split one exact attempt into two report identities. The Sentinel normalizes this declared alias while preserving the other five identity fields. Existing alias incidents remain as `superseded_alias` evidence, never as a claimed recovery.

## Operating closure

The launcher resolves the protective baseline before launching and exports its source date/hash. Runtime consumers revalidate the hash and source date, including after a cached read. An invalid newest baseline is not skipped in favor of older evidence. No baseline file is copied or relabeled as today's evidence.

The scheduled Sentinel consumes the selected immutable release. Old failed attempts remain historical evidence; closure requires new source-valid evaluations reaching the machine assessment. Broker acceptance, fills and net economics remain separate observations.

## Validation and deployment

- Targeted regression: 152 promotion/snapshot/monitor tests and 145 bootstrap/Sentinel tests passed. Compile and diff checks passed.
- Read-only actual-artifact check: original baseline `2026-07-23`, SHA-256 `27e607109fc1dbf4120b9d86c161b2e0773cc38ca58b6a712662bf06d91b8343`, `ready_baseline_v1`. Its source date is retained. Print-only backlog parser passed. Ruff F/E9 found two pre-existing F841 findings in unchanged Sentinel diagnostics; comparison against the base commit confirmed both are unrelated.
- Source base: `17330cdad79fcbac552d8eae75e86cfdf8805b6c`. Isolated worktree: `KORStockScan-worktrees/preflight-submit-repair-20260921`.
- Deployment: merged main commit `20432a6e279823b033ddec0affade8163ac8942e`, preserving separately completed widget repair `bbdf8a8b3`. Managed release `preflight-submit-repaired-20260921-20432a6e2`; prior widget release/selection retained. A compare-before-switch check detected that concurrent deployment and prevented overwriting its receipt before the integrated successor was selected.
- Graceful restart completed at 09:36:48 KST, PID `54623 -> 55596`. Selected release/cwd receipt and dated bootstrap PID validation passed with no mismatches. PID env includes original baseline date `2026-07-23` and exact SHA-256 above. No baseline artifact was regenerated or relabeled.
- Natural acceptance: at 09:37:29, `232140` produced `ready_baseline_v1`, `preflight_allowed=True`, `machine_evaluation_status=assessed`, machine `BLOCK`. `348080`, `003160`, `067310`, `149950` also reached assessment. `226950` and `455900` retained required-feature freshness `RECHECK`. The former artifact-missing blocker is closed for these new attempts. This does not claim broker acceptance, fills or improved economics; unsupported economic scopes stay explicit.
- Evidence and rollback: [deployment receipt](../../tmp/preflight-submit-deploy-20260921-Sbj9Hd/deployment.json). Existing failed attempts and pre-repair monitor state are preserved in that directory.

## Natural-consumer supplemental repair

- The 09:40 scheduled Sentinel consumed the first repair and retained the original alias incident as `superseded_alias`, with ten canonical premarket attempts. It exposed two previously hidden contracts after baseline recovery: assessed events had no `evaluation_attempt_id`, and required-feature pre-assessment `RECHECK` used an unrecognized AI-screen status.
- The normal machine producer now restores snapshot/caller identity and explicit broker route omitted by compact formatting before both capture and economic observation. Explicit caller attempt IDs take precedence; otherwise the exact snapshot ID or a producer-owned attempt ID is shared by both paths. Missing venue/route is never inferred. Historical missing identities are not rewritten.
- Sentinel recognizes `not_requested_required_feature_insufficient` only for `RECHECK`. The economic monitor marks this explicit pre-assessment safety exclusion `guard_excluded`, not a missing economic event. Ordinary assessed `RECHECK` still requires economic evidence; conflicting statuses and `ENTER_NOW` remain invalid.
- Supplemental producer/trace/Sentinel/monitor tests: 413 passed, including snapshot/caller/generated identity and provider-cache/lock bypass contracts. Compile and diff checks passed. No provider/threshold/quantity/safety rule changes. Follow-up deployment and natural identity consumption are recorded below after the managed restart.
- Follow-up release `17bd05957` restarted gracefully at 09:48:27 KST, PID `55596 -> 63210`, exact-date bootstrap and selected release/cwd PASS. At 09:48:56 `041190` and subsequent symbols emitted matching `aims-*` attempt IDs in machine and economic events; required-feature `226950` remained `RECHECK/guard_excluded`.
- Natural terminal events also carried `policy_bundle_hash="None"` beside a valid `machine_bundle_sha256`. Sentinel's first-nonempty lookup incorrectly masked that exact receipt. The machine identity consumer now skips only declared missing tokens before selecting explicit identity aliases; absent identities remain missing. Added seven missing-token regressions; Sentinel/monitor tests 169 PASS. This is report-only identity normalization, not a trading-policy change.
- Bounded source replay at 09:51:18 (offset `445106833`, maximum 28 MiB) through the repaired consumer: 104 retained events, 11 exact attempts, identity-missing 0, conflicts 0, nine BLOCK and two required-feature RECHECK. Seven economics rows retained `exact_broker_capacity_missing` and two retained `frozen_operating_contract_missing`; neither is economic success. Runtime logs confirm bounded source-only `kt00011` requests deferred by `shared_read_rate_wait_budget_exhausted`. No request-limit, timeout or broker guard was changed. Existing main operating-economics OPEN owner retains these source contracts.
