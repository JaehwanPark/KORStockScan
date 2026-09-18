# PYRAMID retirement and AVG_DOWN shared Main rebound review — 2026-09-18

## Decision and authority

The user's 9/18 correction supersedes the independent SI0–SI6 tuning objective: remove PYRAMID from tuning and runtime; AVG_DOWN consumes the existing Main rebound entry assessment and keeps common BUY/SELL safeguards. Existing deployment authorization continues through reviewed immutable source selection. Code/release selection, Main PID consumption, natural ADD and realized economics remain distinct.

Owning plan: [9/17 proposal, current correction](../proposals/scale-in-pyramid-avg-down-economic-tuning-implementation-plan-2026-09-17.md). Executable natural acceptance: [9/18 checklist](../checklists/2026-09-18-stage2-todo-checklist.md), existing `KiwoomCommonHealthOpportunityCostAcceptance0917`. No new OPEN owner, runtime model, collector, Python module, provider call or report rerun was introduced. Historical SI reports and receipts are preserved as audit evidence.

## What the old baseline meant

`SCALPING_PYRAMID_MIN_PROFIT_PCT=1.5` was the code-default minimum current net holding return before considering a PYRAMID ADD. It was not a minimum profit target after ADD, a slippage allowance or a stop threshold. The 9/17 quality report also displayed selected 1.5 with `code_default` provenance; this was not a newly selected positive economic edge. Strong-continuation 0.9 was a separately disabled alternative. No current Main PID receipt establishes either as an actually loaded live rule.

AVG_DOWN displayed shallow minimum buy pressure 85 from the runtime-rule baseline, with display-only current-value/provenance limitations. It likewise was not a new profitable selected policy. Frequent small profits are not proven optimal by either incumbent. PYRAMID removal ends use of its 1.5 hurdle; common exit, cost and slippage semantics are preserved rather than substituting an unsupported new profit target.

## Producer → consumer change

| Boundary | Current behavior | Review/closure evidence |
| --- | --- | --- |
| PYRAMID runtime | Main/Swing evaluator returns permanently retired; quantity is zero; direct submit is blocked before account/order calls; env cannot revive it | True-env and direct-call regressions, retired family/receipt tests |
| PYRAMID exit influence | ADD grace, trailing PYRAMID handoff and stop-delay paths cannot defer common SELL | Legacy armed-state and SELL priority regressions |
| Independent scale-in analysis | Feedback and both calibration producers return cheap explicit retired status; native postclose branches removed; legacy wrapper is a no-op | Wrapper/retirement/Daily/verifier tests; mandatory observation source preflight retained |
| Cron | Installer removes PYRAMID feedback registration while retaining original dedup logic; installed legacy wrapper does no analysis | Actual one-line removal recorded separately in deployment receipt |
| Daily/PREOPEN/succession | PYRAMID/AVG_DOWN independent candidates, reversal-add, post-probe winner and shallow source-gap recheck are retired; old report/env/lock/receipt cannot reapply them | Candidate intake, direct override, carry and succession regressions |
| AVG_DOWN input | Reuse already acquired Main holding completed bars/meta and current WS ticks/BBO; no budget observation collector or 250ms exit replay capture | Source acquisition callback and provider guards |
| Shared signal policy | Existing `resolve_live_prompt_policy` supplies Main same-stage activation, position tag, exact policy scope, venue/session and current mechanistic bundle | Scope-required negative test; real setup and machine assessment tests |
| Shared rebound assessment | Existing context/preflight, exact/recovery/setup and mechanistic decision; only PULLBACK_RECOVERY/RECOVERY_CONFIRMATION/MICRO_RECOVERY plus ENTER_NOW qualify | Positive rebound and negative continuation, source/policy gap, adverse-input regressions |
| ADD execution | Exact source/basis permit, 2-second freshness, signal dedup, holding-AI veto, common sizing/order/price/stop safeguards | Changed source/basis/symbol, extra action fields, stale/future permit, hard stop and partial-submit tests |
| Audit/actual outcome | Shared machine version/hash and source signal attach to existing episode/decision/order trace; historical pending/fill/COMPLETED ledgers retained | Partial accepted leg consumes signal and retains pending; archive-only EV audit remains explicit opt-in |

The shared signal is a current causal assessment of holding market inputs using the Main entry policy. Existing postclose Main entry learning/publishing and PREOPEN supply that policy; there is no file of future rebound prices and no separate AVG_DOWN threshold grid. Samsung/widget/episode timing research has different custody/scope and is not routed to Main.

A missing policy, incompatible position tag/scope, invalid source or negative rebound assessment blocks ADD. The shared signal grants neither quantity nor broker authority. Common pause/operator veto, quote freshness/conflict, deposit/broker quantity, original-entry sizing and ADD cap, cooldown, pending order, custody and exit claim remain effective. Normal soft-stop evaluation precedes the shared ADD path; hard/protect/emergency SELL priority is preserved. The old stop-line compulsory ADD and late-loss ADD/deferred stop retries were removed.

## Review, repairs and validation

Implementation → self-review → supplemental fixes → re-review → targeted validation completed for this scope. In-scope findings remaining: **0**. Repairs included generic PREOPEN retirement-env semantics, stale family succession resurrection, restoring cron dedup and mandatory source preflight, shared Main activation/scope instead of a direct policy bypass, exact action permits, pre-submit signal invalidation, partial acceptance identity and AI-only trace field access.

The full runtime regression first exposed expectations for removed alpha, compulsory ADD and exit deferral. Those obsolete expectations were removed, not skipped. Existing common SELL, quote, margin, buy-window and historical partial/unfilled reconciliation cases were migrated to a producer-minted shared signal. The transition manifest lists 157 obsolete function expectations; parametrization explains the difference from failed-case count. Existing unrelated workspace test changes and two new entry funnel tests were preserved through AST-aware merge. Backups and merge manifests are under `tmp/scale-in-rebound-unification-20260918/workspace-merge/` and `workspace-final-merge/`.

| Validation | Result | Evidence |
| --- | --- | --- |
| Final full isolated runtime plus real shared producer | 953 passed, 17.26s (946 runtime + 7 producer) | `tmp/scale-in-rebound-runtime-producer-final-20260918.log` |
| Affected retirement, feedback/calibration, Daily, PREOPEN, EV, chain and replay consumer contracts | 1,173 passed, 34.21s | `tmp/scale-in-rebound-contracts-20260918-closed.log` |
| Succession and runtime release router | 91 passed, 1.46s | `tmp/scale-in-rebound-routing-20260918-final-closed.log` |
| Latest shared Main resolver/runtime focused suite | 58 passed, 3.44s | `tmp/scale-in-rebound-runtime-20260918-resolver-closed.log` |
| Changed Python compile, three shell syntax checks, diff whitespace | PASS | `tmp/scale-in-rebound-unification-20260918/validation.json` |
| Working copy focused regression | 34 passed; final runtime comparison recorded in validation receipt | `tmp/scale-in-rebound-workspace-final-focused-20260918.log`, `tmp/scale-in-rebound-workspace-final-20260918.log` |
| Print-only document parser | PASS, 18 tasks, one current stable owner | `tmp/scale-in-rebound-doc-parser-final-20260918.log` |

The new signal/submit fixtures forbid network and mock broker/account responses. An earlier exploratory legacy test run attempted REST with a fixture token, producing rejected/missing-fixture responses; it was not economic evidence or real order validation. No authenticated live order, provider evaluation, broad postclose regeneration, package changes, performance benchmark or external Project/Calendar sync was requested or executed by this change.

## Release, runtime and economics

Commit/root/selection backup/cron delta/router plan evidence are recorded in `tmp/scale-in-rebound-unification-20260918/deployment.json`. Selection alone does not establish Main PID consumption. The working copy contains an unchanged older `micro_estimator_state.py` than the selected source baseline. Two original-depth/future-source tests fail against that older module and pass in the reviewed release; the comparison excludes only those two cases and preserves that unrelated module. Provenance is in `workspace-baseline-difference.json`. This is not an unresolved defect in the reviewed release.

Before selection, the current source root was `low-price-research-repaired-20260918` / `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`; no Main PID was present. The separate low-price service and other unrelated working-copy changes are preserved.

The previously recorded 9/18 PREOPEN integrated-entry handoff failure and 9/17 native resource-guard block are external to this retirement/change. They were not repaired by silently relaxing date/hash/env/lock/safety gates or rerunning the chain. No Main restart or fabricated PID consumption receipt was used to bypass them. Main startup/natural collection remains with the existing checklist owner.

| Remaining acceptance | Evidence required | Closure test |
| --- | --- | --- |
| Normal Main consumption | Current dated Main policy/PREOPEN handoff and actual PID/root/commit receipt | Canonical startup passes its existing handoff guards; PID consumes the selected source |
| Natural shared signal | Same-date Main scoped rebound version/hash, episode/decision and source signal | Valid rebound → common guard → ADD or explicit blocker; no PYRAMID/independent candidate emitted |
| Realized outcome | Actual completed fill/exit/cost ledger, full/partial and owner/venue separation | Deduplicate episode for actual code/machine application version; missing/censored economics remains null |
| Economic effect | Rolling/cumulative cost-adjusted EV, net profit, tail and exposure; separate model error | Evaluate actual completed population and baseline with valid lineage; model ΔEV never counts as realized incremental ADD profit |

No natural shared-signal/ADD or new completed economic population is established by these tests. EV/net profit/tail/exposure/model error for the new applied version are **null**, not zero or no-edge. Independent AVG_DOWN candidate zero is expected retirement, not an instruction to revive that tuner. For the shared consumer, separate policy/source/scope gaps, common safety/stop/pending blocks, valid absence of rebound and immature outcomes. Economic improvement cannot be claimed from Main entry-model EV alone.

## 09:30 KST immutable selection and final runtime receipt

- Reviewed commit: `7302dfe79d79257b38f57cfd199d4b74c30f2613`, parent `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`. Root: `/home/ubuntu/KORStockScan-runtime-releases/scale-in-shared-rebound-20260918`. `src/deploy/restart.sh` are clean and selected source hashes match the validation receipt. Working-copy integration preserves unrelated changes. No remote push was needed for local managed deployment.
- Atomic selector transition at09:30:01 KST used the existing release lock and exact predecessor comparison. Previous selection and SHA are backed up in the deployment receipt. Shared paths remain data/logs/tmp/docs/.venv/restart.flag. Print-only postclose/preopen/start router plans consume this root/commit; no worker/start/restart was executed.
- Removed exactly one installed `SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN` cron row. Other cron rows are byte-preserved. No full installer, cron restoration or resource guard mutation. The historical wrapper remains a cheap explicit retired no-op if a legacy caller invokes it.
- Final runtime + shared producer953PASS; related producer/consumer contracts1,173PASS; succession/router91PASS. Working-copy runtime948PASS with two documented unrelated older-module exclusions; focused shared path34PASS. Compile27/Python, shell syntax, source whitespace and print-only parserPASS. One current stable owner, 18 parsed tasks. No expensive report regeneration or external sync.
- Selected-release read-only PREOPEN verify returned1/fail, `runtime_env_handoff_missing`. Current integrated-entry findings: `integrated_axis_bundle_hash_mismatch`, `integrated_axis_unconfigured`, `integrated_axis_policy_date_mismatch`, `integrated_axis_shared_policy_hash_mismatch`. Owner is the existing integrated-entry dated publisher/PREOPEN handoff under the current checklist; next closure is a valid automatic dated policy projection/manifest/hash and its normal strict verifier before Main startup. This retirement does not repair or bypass that policy handoff.
- Main process/PID consumption absent. Separate low-price unit remains active/running, PID41757, NRestarts0; unit WorkingDirectory still points to its original low-price reviewed release. Direct `/proc/41757/cwd` access is permission-denied, so this turn does not claim a new direct cwd attestation. The service was not restarted or redirected. Natural shared rebound/ADD and applied-version COMPLETED economics remain OPEN/null.
- Rollback requires checking current selector/PID and validating the backed-up predecessor's clean source/shared mounts before a locked selector restore. Restoring the predecessor also restores removed PYRAMID/independent AVG_DOWN behavior; the current user retirement instruction must be respected, so do not restore that strategy merely to change source routing. Do not restore the full old crontab, rewrite dated policies/custody or erase actual ledgers.

## 9/18 authorized re-review, Git management and artifact cleanup

User authorization: repeat code review/fixes, then commit/push, deploy and start through the existing canonical safety gates. Inspect Git exclusions and delete past PYRAMID/AVG_DOWN products. This does not approve intraday policy-date/hash fabrication, safety/threshold/provider/cap relaxation or restoration of the stopped native chain.

Review found and fixed two boundaries:

1. Source signal identity included computed quote/tick ages but omitted completed-bar input. Exclude the known consumer age projections, keep original source inputs and include completed bars. Reevaluation clocks/age projections do not mint new signals; a new completed source bar changes identity. Regression uses the real shared setup/machine assessment and forbids provider/network calls.
2. Main's current effective stop line was checked before shared ADD judgment, while final resolved order price only checked the global hard stop. Bind that existing stop line into the exact permit, reject stop/invalid-line inputs before signal production and recheck it at execution and final resolved price. No new tunable stop, grid, model or provider. A final-price stop crossing cannot submit/reserve or consume the signal; valid partial submission still retains its accepted pending leg.

Runtime+producer956PASS and retirement/PREOPEN/succession/wrapper485PASS. Changed Python compilePASS, shell syntax and whitespace checks close in the final validation receipt. Unresolved in-scope source findings0. Current evidence: `tmp/scale-in-review-git-cleanup-20260918/validation.json`, `runtime-review-final.log`, `consumer-retirement-review.log`, `workspace-focused-final.log`.

Generated-directory Git rules: `/data/report/`, `/data/cache/`, `/data/runtime/`, `/data/daily_recommendations*.csv`. Versioned generated files are removed from the index in the reviewed delivery tree while local files remain, except the expressly deleted retired products. Source/tests, daily checklists, proposals, operating/audit documents, `data/config` reviewed static assets and source-quality baseline/contracts remain versioned. Source/document modifications are not hidden merely to reduce pending counts. Protected assets and generated paths were checked with print-only Git ignore resolution. The removal list is recorded in the Git management receipt; no Git history rewrite, secret/token inspection or external sync.

Past products deleted: four retired report groups (PYRAMID feedback/quality, AVG_DOWN recovery and `scale_in_incremental_counterfactual`), pre-9/18 dedicated old event-family partitions, legacy PYRAMID feedback logs/status/unused lock, and physical report copies in inactive worktrees/mount backups. Totals: **11,464 files / 193,147,886 bytes**, 348 dedicated roots; target remainder0. Metadata manifests and aggregate receipt are in `tmp/scale-in-review-git-cleanup-20260918/`. Do not restore these from an old report backup.

Mixed actual order/custody/fill/COMPLETED ledgers, live shared AVG_DOWN evidence, current execution safeguards, operator configuration, source/tests/docs and current release/review receipts were preserved. In particular, the old `real_pyramid_scale_in_quality_guard` configuration also owns pending revalidation safeguards, so a filename match does not delete its common protection. The independent PYRAMID floor lock remains historical configuration and cannot reactivate its retired evaluator. Deleted historical report paths in older audits are intentionally unavailable; historical modeled results are not fresh economic evidence and absence cannot reopen retired tuning.

Commit/push/root/selector/predecessor/source-clean/routing and canonical startup results are recorded in `tmp/scale-in-review-git-cleanup-20260918/deployment.json`. Main's actual entrypoint is `bot_main.py`; the final process check covers both that file and the sniper module rather than relying on the imported sniper filename alone. Actual PID/natural ADD and economics remain separate and require their own receipts.

Final producer re-review traced the actual WS snapshot owner: `market_data_health` contains consumer-clock ages and `market_session_remaining` is a countdown. These projections are also excluded from signal identity, while original typed source receipts remain included. Seven real-core producer regressionsPASS after this supplement. This changes dedup identity only, not input quality or order freshness checks.
