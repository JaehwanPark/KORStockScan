# 2026-10-19 postclose root-cause recovery review

Source date: 2026-10-19. Next KRX session: 2026-10-20.
Baseline: `deb996a22689ac08e171ea38966d070d63d236ee` (selected immutable release).
Owner: existing `DirectFamilyPreopenPolicyHandoff`, `InitialQuantityProducerConsumerRepair1010`, and `HoldingProfitExitSourceContractRepair`; no new executable checklist owner.

## Decision and original evidence

EOD completed at20:56:42 with2,621 target-date quote rows and4 identified short-history exclusions. Main machine policy independently succeeded at21:16:23. Whole postclose failed at21:03:36: all three completion-prefix attempts raised `completed_census_id_mismatch`. A stage PASS is not whole-chain closure.

Original failed snapshot, wrapper terminal and all attempt output are preserved under `data/audit/postclose-recovery-2026-10-19/before-completed-census-repair/manifest.json`. Inspection evidence is in `tmp/postclose-monitoring-20261019/`. Preserve original policy/PREOPEN/checklist, failures, raw events and manual custody; do not manufacture terminal events, actual costs or target-day PID consumption.

## Root causes and permanent repair

1. The producer includes all DB-completed observations, while its census validator required exact equality with native `sell_completed` event IDs. The actual populations are4 DB observations versus3 native events. Record49362 was reconciled after the operator's direct sale (original exact broker/journal recovery is documented in [the morning review](preopen-alert-repair-2026-10-19.md)); a Main terminal event must not be invented. Bind a dated, hashed original DB-row witness, declare both populations, validate their exact union and independently preserve native IDs. DB-only rows explicitly remain excluded from strict completion economics. Future reconciled/DB-only completions now follow this contract rather than failing on every subsequent replay.
2. Snapshot publication preceded census/open-position validation. Invalid421MB canonical snapshots were therefore published on each failed attempt. The existing single projection validator now admits the canonical publisher only after date/census/open-census validation. Negative tests preserve original bytes and file identity on refusal. Missing validation input cannot silently skip the projection path.
3. The bounded sidecar must carry the same DB witness and population counters so holding and fact consumers validate the same census. Legacy snapshots without the new metadata retain their exact old manifest contract.

No new DB query, API call, order action, trading predicate, module, CLI, wrapper or schedule is introduced. Completed rows with missing cost/profit remain null/excluded; modeled PnL is not actual economics. This repair closes the population-contract defect, not missing historical execution receipts.

## Review and replacement/removal disposition

| Existing owner/path | Disposition and current consumer |
| --- | --- |
| `save_monitor_snapshot` raw publication block | consolidated into one local publisher callback; both ordinary snapshots and validated postclose snapshots use it |
| `_save_trade_review_completed_projection` | retained as the sole existing census/open gate and sidecar/fact/dependency producer; public snapshot publisher and named direct streaming test consume it |
| `verify_completed_census_manifest` | extended in place; holding observation, fact synchronization and projection publication retain the same implementation |
| Raw native IDs / historical manifest branch | retained for source lineage and immutable historical readers; DB observations never replace native events |
| Old optional-validation bypass | removed for postclose-exit trade review; missing census/open/date now refuses publication |

Reviewed static callers include `holding_exit_observation_report`, `strategy_position_performance_report`, the native snapshot CLI and `test_research_json_stream`; dispatch/schedules are unchanged. No forwarding module, duplicate validator or deferred replacement was added.

## Validation

Network-denied report/archive/stream regression:131 passed, zero connection attempts. Holding-window/holding-observation/fact/archive/stop/detector/trade-review/cost regression:789 passed, zero connection attempts. The DB-only sidecar-to-holding integration extension passed both populations (2 cases). Final compile/diff/document checks are recorded in the evidence directory before commit.

Supplemental fixture repairs: the full-profile publisher stub now supplies the real required empty census and verifier; a fact-only large timeline fixture uses actual event objects instead of a string; an unbound legacy gzip without original structured-source/full-profile proof is asserted as source gap rather than falsely accepted as valid empty. No production validation was weakened for these fixtures.

Non-test source:109 additions/29 deletions; tests:101 additions/20 deletions before this document (final git numstat is authoritative). Raw publication lines were moved into the callback; net growth primarily supplies the two-population source contract and adversarial coverage. No module/entrypoint/owner growth.

## Follow-up and acceptance

Code review and targeted tests precede expensive regeneration. Immutable candidate source/code handoff checks, preserved source-date recovery, downstream quantity/holding/EV/summary/tower/checklist/strict/controller and next-session preparation are still pending. Scheduled controller/tuning waiters are pinned to the original release; do not switch their code while they run. Main was stopped by the native postclose owner; no manual trading restart is required by this report repair.

Apply this root-cause standard to every newly observed2026-10-19 postclose error: repair the owning producer/consumer contract, test recurrence, regenerate affected descendants, and verify the intended last consumer. An irreversible historical source gap stays separately owned and is not a reason to replay unchanged input forever. Do not declare next-session readiness before exact-date native verification; prepared policy is not future PREOPEN/PID consumption or economics.


## Native handoff supplemental review

The first immutable candidate's native fixed workload matched128 scopes/76,800 rows/598 confirmation hits with identical signal SHA and no changed native decision module. Active-policy validation passed; delay validation correctly refused the new archive dependency. Original refusal remains in `tmp/postclose-monitoring-20261019/native-preflight-execution.log`.

Extend the existing `intraday_release_handoff` owner with one exact complete dependency successor of the approved AVG_DOWN generation. Only the reviewed report/archive hashes change; original digests, all other dependencies and historical branches remain bound. The current and historical two origins are covered across delay/stop/holding families; changed report, missing archive and unrelated dependency fail.2,567 native-handoff tests pass. This is an extension of the existing verifier, with no additional validator, bypass, CLI or execution authority. The incumbent policy/current pointer stays unchanged.

Supplemental delta relative to the first repair commit: non-test source31 additions/2 deletions; tests37 additions before import cleanup; this owning review updated. Baseline-to-final git numstat remains authoritative. Final immutable candidate validation and actual recovery remain separately pending.


## Full-consumer and shared-release-path root causes

The first recovery's completion prefix succeeded at21:43:53, but native fact synchronization failed at21:44:06. Both original failed statuses and the successful source generation are preserved under `data/audit/postclose-recovery-2026-10-19/before-completion-consumer-repair/manifest.json`. The temporary successful CLI result was already removed by its native owner; no replacement result is manufactured.

A read-only call using the actual selected release path reproduces `snapshot_archive_path_invalid`: the fact consumer admitted the shared data mount at its first path check, then passed the unresolved symlink spelling to the stricter archive reader. Canonicalize only after the original exact target/date/path and leaf-symlink checks, retain full source-generation checks, and recheck the requested alias after reading. Foreign paths, leaf symlinks and changed sources still fail.

Separate direct-path reproduction also exposed native-only population assumptions in fact, initial-quantity completion cache, holding completion collection and Main-stop economic input. The earlier local producer/sidecar tests did not exercise this unequal-population final-consumer path. Extend the existing report owner with one shared `completed_census_projection_ids` function: verify the sealed rows/count and native-plus-database union once, preserve opaque historical native IDs, and migrate those four consumers. Raw native count remains its original independent denominator. The legacy original streaming fallback retains its original raw-terminal equality and explicit gap contract; it is an immutable historical reader, not the new native projection path.

The newly added DB-only text warning would also globally exclude the otherwise valid report in holding/open-position readers. Remove that new global warning in favor of the exact already-present row source status, strict exclusion reason, DB witness, declared census and population counters. Genuine producer warnings keep their original refusal path. DB-only terminal gaps remain visible, including `completion_day_terminal_receipt_missing`; no terminal, cost or economic eligibility is invented.

Replacement map supplement: native-only population comparisons in four existing consumers are consolidated onto the same report-owned census reader; the original producer validator reuses that reader. Existing native dependency receipts, scalar fact projection, archive validation, source locks, dates, custody and cost checks remain retained. No new module/CLI/schedule/framework or forwarding surface is added. The exact handoff dependency generation now pins all six reviewed producer/consumer source files.

Integration coverage uses the actual snapshot publisher, fact adapter/status writer, quantity completion reader, holding collection and Main-stop source reader. Native-only and DB-only completion populations plus direct/canonical and release-data-mount paths all pass; missing terminal/cost stays excluded/null. A previously passing fixture-only status directory is corrected to the real `strategy_position_fact_sync` consumer path. Subsequent full regression uses a stable code/hash generation; earlier during-edit refusal is preserved separately.

Stable-generation full regression:3,956 passed in154.25seconds; network-denied execution recorded zero connection attempts. This includes actual unequal-census final-consumer and shared-release-path coverage, all existing initial-quantity files and native handoff failure cases. Compile, diff and print-only parser pass. The six-file exact generation replaces only reviewed source bytes; runtime selection/regeneration and next-session readiness remain pending.


## Stopped-selection custody and immutable generation ancestry

Native preflight of26f2694bb passed active policy but refused delay origin custody. The prior stopped selection omitted the existing `inherit_prepared_delay_code` action. Its original passed preflight had authenticated the exact consumed deb996a22 prepared-code receipt. With Main and all analysis wrappers absent and release/selection/detector locks held, verify and temporarily expose only that exact preserved consumed selector, issue the missing a5831f833 native code-only receipt through its unchanged native issuer, then restore the identical stopped selector. The original policy, PREOPEN, receipts and current pointer remain unchanged; no PID consumption is fabricated. Evidence: `tmp/postclose-monitoring-20261019/consumer-native/missing-delay-handoff-recovery.log` and native receipt. Future selection must call the existing inheritance helper before publishing its selector.

Successor validation also exposed an overwritten intermediate dependency generation: the unchanged archive selector identified both the producer-only and full-consumer repairs. Keep the already-issued two-file generation, and identify the full six-file successor by its changed report source hash. Native historical receipt verification now selects exactly one complete matching generation and never mixes hashes across generations. Existing current/historical verification uses the same implementation; the intermediate generation is retained for its native prepared-code ancestry consumer, not an execution rollback.2,591 handoff tests pass, including both generations, both original origins, all three policy families and changed/missing/unrelated dependencies. The prior3,956 stable-generation tests and actual release-path source-only readback remain separate evidence. Capability validation issued the current holding fixture (128 cases) and verified the other three unchanged native fixtures.


## Producer-code-aware prefix reuse

The bf8465b5d recovery correctly read the shared path and full census, but failed at22:08:47 with `trade_review_source_warning`. Its `[REUSE] exact completion prefix` had reused the21:43:53 artifact, which still contained the removed global DB-only warning. The reuse contract sealed source bytes/cost/census but omitted the producing code generation. Preserve the failed receipts under `data/audit/postclose-recovery-2026-10-19/before-producer-code-cache-repair/`; the unchanged source bytes are already in the previous preservation directory.

Extend the existing prefix manifest and validator with the exact four report/publisher source hashes. Capture them before building reports, verify the same generation at publication and consumption, and refuse missing/changed code proof. Ordinary wrapper recovery then regenerates the prefix through its existing producer; no forced-success flag, warning suppression or manual cache deletion is used. Same-code reuse still avoids the expensive report work. The original validation implementation remains the owner; previous unbound prefix bytes are historical evidence and cease being reusable current inputs.

Retain the already-issued two-file and full-consumer dependency generations and add one exact prefix-code successor selected by its changed archive producer hash. Regression covers missing proof, recorded/current code changes, original/corrected source populations and all three immutable generations. Prefix regression77 passed; final generation/consumer validation is recorded before publication. No trading predicate, quantity, provider schedule, live policy or original PREOPEN is changed.

Prefix/three-generation handoff regression:2,692 passed in105.00seconds. Existing operating inventory and the two existing OPEN checklist owners are updated; original strict-bound checklist is preserved through the native routing preservation helper before operating progress changes. No new OPEN owner is created.


## Later official costs and immutable original facts

Baseline for this supplement: `082234567cfa529eca881eac448eafa84d7345a5`. The native recovery reached fact synchronization successfully at22:24:46, then failed initial quantity at22:29:21. The19-date publisher was valid. Its16-date completion dependency still carried the original cost seal, while the normal pending-cost collector had refreshed16-date official observations at21:42:35. The settlement query window and returned pages changed; this was not merely a timestamp change. Global equality between immutable original report costs and the current official alias made a valid original terminal census unusable. Original failure/status, current cost/index and16-date fact/dependency receipts are preserved under `data/audit/postclose-recovery-2026-10-19/before-historical-cost-rebinding/`.

The existing lifecycle allocation owner now recomputes a research derivative from byte-verified original native fills, original terminal authority, current verified Main custody and current dated official totals. Broker totals retain outside/manual activity in their denominator. Missing/invalid inputs remain per-record null/exclusions. The old receipt generations and exact previous index bytes remain retained; no canonical report, DB fact, realized PnL, policy, PREOPEN or terminal is resealed. A stable original-source/registry/official-source revision is reused without streaming the historical timeline again. Only the existing quantity publication CLI prepares this derivative; read-only census, monitor, serialized replay and verification cannot publish it.

Quantity verifies the original fact/census seal independently of current costs and pins both generations. A cost revision clears stale actual money before attaching a current immutable research receipt. The compact monitor consumes that same current generation. Holding-window/assembly/replay/selector/handoff consumers use the same explicit original-native/current-cost mode: original census coverage survives, stale actual reconciliation is not reused, and the existing holding research-cost owner independently validates the current allocation. Legacy/unsealed sources retain strict refusal. Windows without a meaningful native cost revision keep their original schema/hash. All issued producer, full-consumer and prefix-code handoff generations are retained alongside one complete exact successor; no mixed per-file alternatives or weaker policy authority are introduced.

Native read-only reproduction verifies the original16-date census of9 completed records. A dry allocation against the actual current sources yields8 valid research allocations and1 execution-source exclusion, with no provider call or source mutation. This is research allocation, never canonical actual execution PnL or fresh natural profit. The preserved original execution gap is not fabricated away. Test coverage changes the official total, removes a required source, changes it again after publication, checks byte preservation, verifies idempotent preparation and follows the result through quantity, compact monitoring, holding window and actual trailing assembly.

Replacement/removal disposition: the global current-cost equality and stale-fact abort in quantity are replaced by the original-seal plus current-derivative join; original cost money is cleared from revised in-memory rows. Existing native projection, allocation, immutable receipt, source lock, monitor and replay owners are extended in place. Strict current-only/legacy readers are retained for their existing callers. Existing holding research cost attribution remains the only holding allocation consumer; no duplicate allocator, new module, report producer, CLI, wrapper or schedule is added. Old canonical reports and issued handoffs are retained as immutable historical evidence, with current consumers selecting one complete native code generation. There is no deferred implementation removal in this supplement.

Validation: initial quantity/cost/window regression568 passed with network denied and0 attempted connections. Supplemental review found and fixed false cost-revision classification of legacy null/no-cost sources, moved derivative publication out of the read-only DB reader, removed repeated record-index construction and updated the last holding replay/selector/handoff consumers. Stable-generation expanded regression, native code/parity/capability gates, selection and actual recovery remain separately recorded before execution.

Stable-generation late-cost regression:4,265 passed in258.61seconds across28 affected test files; network denied with0 attempted connections. Compile/diff and print-only parser pass. Supplemental review is clear for the reviewed source-only repair. Native candidate/parity/capability/handoff, actual dated derivative publication and postclose final consumers remain separate follow-up.

Supplemental diff versus082234567: non-test source399 additions/50 deletions; tests113 additions/4 deletions. Documentation is confined to this review, the operating inventory and the two existing checklist owners. Net growth implements independent original/current cost proof, bounded derivative publication/index preservation and shared consumer coverage. Existing owners and execution entrypoints are unchanged.
