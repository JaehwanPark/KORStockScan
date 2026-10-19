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
