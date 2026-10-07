# Finalization historical checklist observer repair — 2026-10-07

## Decision and authority

Repair the two report consumers that reject an approved historical finalization solely because the current checklist changed. Existing owner: `SemanticMonitorProducerConsumerRefresh1007`; existing user approval covers implementation, review, integrated deployment and restart. The frozen daily checklist and its existing acceptance remain unchanged. No new postclose completion, policy selection or economic acceptance is claimed.

## Evidence

- The original 2026-10-06 finalization DONE was recorded at 2026-10-07 08:56:16 KST, after the 06:50 cutoff.
- Original chain: `fb84848e3085e3b6f4938e23a8f708b954dc61968320eeb5115dfc4150e63693`; snapshot: `cd83b048db1745630e0fcea8e0ddf3f8fcde8f45d6af04f8bb4826f853d36158`.
- Strict checklist SHA: `0f470d5ec16f3888cd3d1d489813cb67647ee2768d5f46167a5bc1b790da6f61`. The approved immutable historical snapshot has these exact bytes.
- Current checklist SHA: `1b7156388db7b592a45cbfc81dad0b1adb8e620c96b17d9c7b7c2c468a17893c`. Native intraday handoff and current PID consumption preserve both generations, but finalization/semantic observers omitted that custody.
- Before repair, cron reported `strict_checklist_generation_stale`; semantic handoff additionally reported `strict_generation_changed_during_recheck`.

## Implementation and review

1. Startup automation provides a read-only historical checklist reference only after exact source/current trading date, selected release, frozen handoff, consumed receipt schema/status, actual live PID/start ticks/cwd, bootstrap manifest and race checks pass.
2. The finalization marker observer retries only the checklist-stale failure with that reference. It still validates all strict/stage/summary/Main terminal and snapshot sources against original DONE hashes. Public fresh finalization capture keeps the current checklist requirement.
3. The semantic postclose observer consumes the same reference and reruns the native generation validator. Other source errors remain failures.
4. Cron health exposes the validation basis. Genuine late completion remains `recovered_late`; original DONE and postclose artifacts are not rewritten.

Review covered malformed/missing handoff, schema/status/manifest mismatch, reused PID, handoff mutation during verification, snapshot changes, summary/stage changes and both DONE generation hashes. No unresolved in-scope findings remain after the race-check supplement.

## Validation and deployment closure

Evidence directory: `tmp/finalization-checklist-alert-20261007/`.

- Targeted suite: 305 tests covering intraday handoff, finalization, both detectors, PREOPEN, controller and Main v2 publication.
- Local real-source replay: finalization issues `[]`; semantic handoff `done` with findings `[]`; cron retains historical late-completion warnings only.
- Compile and `git diff --check`, document owner/link check and print-only backlog parser are required before release selection.
- Workspace and immutable release both passed 305 tests. Compile, `git diff --check`, link/owner review and print-only parser passed.
- Deployed `/home/ubuntu/KORStockScan-runtime-releases/finalization-observer-20261007-v1`, execution commit `a96b1196e8aaa023fbe05f9441077ae29e000089`. Native graceful restart retired PID 870498 and launched PID 879064 at 13:20:38 KST, start ticks `96766960`.
- Bootstrap, intraday handoff, prepared verification and release-set validation passed; all 186 episode policy pins and ten frozen files (including original finalization log, PREOPEN and current checklist) retained exact hashes.
- Main v2 metadata reissue uses bundle `102a7167d1d12a9e34fcaa76b9d41b003445c50618bde61e69e49b1b148e2001`, family `b9f72e7e8253880a92a47ae56dd05fcec9b1c52c02323905950aed8d4eb97c14`. Machine cells, auxiliary cells, label and research contract file hashes are identical. Actual new PID consumption was recorded at 13:22:36.666176 KST.
- Natural full health at 13:21:09 KST proves new release consumption. Cron finalization is `recovered_late` with `consumed_intraday_preserved_historical_generation` proof for PID 879064; semantic postclose handoff is `done`, findings `[]`. The reported checklist-stale failure is absent.
- Native startup account synchronization succeeded at 13:21:06; all five fixed-watch symbols received real-time data at 13:21:11. No manual broker/provider request or order was made by this repair. The older 09:19 inventory receipt is not used as current broker evidence.
- Separate observations: episode current-PID source warning remains independent of this repair; the first startup health reported elevated I/O wait. Subsequent natural observation is recorded below without treating all health as green.
- Final natural check at 13:24:35 KST: all five fixed-watch symbols (`005930`, `034020`, `403870`, `196170`, `036930`) have machine capture tied to PID 879064 and the identical-policy bundle (3 RECHECK, 5 BLOCK). Shared WS producer is the same PID, connected, snapshot age 1.03 seconds. These captures prove operation, not entry/fill/economics.
- Natural health at 13:22:49 and 13:24:05 retains finalization `recovered_late` and semantic handoff `done`; the checklist-stale failure is absent. Resource/process/auth/log/lock detectors pass after startup. One Main PID remains. The independent episode warning is still present.
- Final closure: reviewed scope has no unresolved code defects; deployment and actual PID/source observation complete. Original postclose source generation is unchanged. `natural-health.json`, `natural-monitor.json`, `policy-consumption.json` and `final-closure.json` retain exact evidence in the directory above.
- Heavy postclose regeneration, EOD, provider/order requests, external document sync and unrelated widget retirement are excluded from this consumer repair.

## Recurrence after a current-work checklist edit

At 15:08:09 KST, release `2950f674` / PID 918591 again reported `strict_checklist_generation_stale`. The historical observer called full startup `verify()`, which compared the operational checklist against its launch-time hash. The only changed frozen source was the current checklist, following an unrelated new implementation-plan reference. The historical snapshot and original finalization chain/snapshot hashes were unchanged.

The observer now uses a private, read-only verification path. It can exclude only that operational checklist from byte comparison, only when a sealed historical snapshot and consumed receipt exist. Exact required-source inventory, every other frozen hash, inherited snapshot custody, selected release, live PID/start ticks/cwd, bootstrap and race checks remain mandatory. Public `verify()`, `consume()`, activation and new finalization still require the current checklist generation. Old handoff, consumed receipt and DONE are not rewritten.

Regression coverage changes the current checklist after actual fixture consumption and verifies observation still succeeds while public verification, new consumption and activation fail. It also rejects changed env, controller, summary or historical snapshot, and absent consumption. Existing status/schema/manifest/PID/race negative tests run with the edited checklist. Real-source read-only replay has finalization issues `[]`; public launch verification still fails on the current document edit, as required. Evidence directory: `tmp/finalization-observer-document-edit-20261007/`.

Repeated review and targeted validation passed: **329 tests** across handoff, finalization, cron/artifact detectors, PREOPEN, controller, bootstrap and Main v2. Compile, diff and print-only parser passed. The original DONE/strict/controller/PREOPEN and all policy cells remain protected. The unrelated work-in-progress plan reference is preserved separately from the code commit.

Applied immutable release `/home/ubuntu/KORStockScan-runtime-releases/finalization-observer-docedit-20261007-v1`, execution commit `3d946012ba7003c7791393acdba4474dedc64a13`. Immutable tests also passed 329. Normal graceful restart retired PID 918591 and launched PID **936414**, start ticks `97450025`, at 15:14:29 KST. Bootstrap, native handoff, prepared and release-set checks passed; ten protected files and 186 independent episode pins retained their hashes before the operational progress update. Machine/auxiliary cells, label and research-contract hashes are identical; native metadata activation uses bundle `7c500126d082c4ef866ef0b74eb4012141b37902ab52e6463bcb0b7bd6b7b2da` and family `615093a91146d391842c9a3d4492537139469224436b05a946109a9bb00e5b50`.

The scheduled 15:15:08 full detector reports original finalization as `recovered_late` with no generation issue. After adding the actual deployment progress to the current checklist, natural health at **15:16:44 and 15:18:33** still verifies the sealed historical generation against PID 936414. Public launch verification remains fail-closed for this later operational edit. All other frozen inputs and original DONE remain unchanged; no fresh finalization or PREOPEN is claimed.

All five fixed-watch symbols receive live data from PID 936414; the loop reports five WATCHING/zero HOLDING. New machine captures and the new bundle's actual policy-consumption receipt remain `not_observed`: `handle_watching_state` returns on the unchanged 15:10 KRX hard cutoff before machine refresh, and the next configured BUY window starts at 16:00. Preserve the existing source/semantic owner for that future natural acceptance; do not force a provider call, decision, order or relax the time guard. Process/auth/log/resource/lock health passes; independent episode-source and historical late-cron warnings remain. No expensive postclose replay, EOD, historical marker rewrite or external sync was run.
