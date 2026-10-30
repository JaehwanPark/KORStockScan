## Main-only 퇴역 계약

자동 실행은 Main 단일 owner다. 에피소드·위젯의 전용 실행/정책/연구/알림/예약과 독립 IPO 자동실행은 제거한다. 과거 체결 잔여분은 사용자 수동관리이며 Main은 인수·매도하지 않는다. 잔여 수량·미종료 intent·broker flat·손익 확인은 퇴역이나 Main 기동의 조건이 아니다. 공통 journal/DB와 Main 정책 부모, 수동 금지·주문 안전은 보존한다. 옛 설치/재가동 명령은 실행하지 않는다.

# Main runtime release routing

## Explicit database configuration for a migration candidate

The native database consumer accepts `KORSTOCKSCAN_POSTGRES_URL` or
`KORSTOCKSCAN_POSTGRES_URL_FILE`, exclusively. A migration launch profile sets
`KORSTOCKSCAN_REQUIRE_POSTGRES_URL=1` and supplies an absolute protected file;
unset incumbent configuration retains its existing consumer behavior. The file
must be a regular non-symlink leaf, owned by root or the runtime user, with no
group/other access. The bounded reader rejects empty, changed or unreadable input
without printing its contents. Configuration alone creates no DB connection.

The existing router's `main_supervisor_command` is shared by initial start and
`restart.sh`. It independently loads the selected constants consumer before
drain, forwards only the protected path and required flag, and removes a stale
tmux server's direct-URL variable from the child. Direct URL launch arguments,
conflicting configuration and invalid files fail before restart publication.
No credentials are placed in command arguments. Target credentials and file
permissions must be provisioned before native candidate/P5 validation; current
runtime proof does not validate a new host or a new source commit. This source
change does not select a release, install the candidate schedule or start Main.

Owner: deployment infrastructure. Main and scheduled consumers use the selected immutable release; web units require the same reviewed release pin. Release routing is separate from exact-date trading approval. Retired executors have no independent code or policy pin.

## 스캘핑 트레일링 익절 기계판정 영수증

강약 폐루프 v2는 `SCALP_TRAILING_START_PCT`, `SCALP_TRAILING_LIMIT_WEAK`, `SCALP_TRAILING_LIMIT_STRONG`의 3시장 9값과 `mechanical_strength_v2`의 3시장×8개 분류값을 한 `KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256` 영수증으로 묶는다. `book_cutoff`는 소비하지 않는다. `SCALP_TRAILING_STRONG_AI_SCORE` scalar는 soft-stop 소유자로 남고 익절 강약에는 쓰지 않는다. 구 4축·시장별 AI 점수 override·v1 선택 영수증은 v2 후보로 재적용하지 않는다. fast/normal은 같은 시장 수익값·분류값을 소비하며, 프리마켓의 청산 가능 여부는 평가시각의 실제 적용 `session_contract`로 판정한다.

장후 wrapper는 최종 `trade_review → post_sell_feedback → holding_exit_observation`을 `postclose_exit` profile로 다시 생성하고 세 파일의 SHA256 manifest를 `runtime_approval_summary` 전에 검증한다. `trailing_mechanical_market_tuning`과 분류기 연구 자체는 보고 전용이다. M1 첫 관측 진입일 이후의 완료 census를 별도 모수로 봉인하며, 이전 구세대의 미봉인 날짜가 새 모수를 영구 차단하지 않게 한다. 해당 M1 기간의 누락 날짜·미배치 ID는 차단한다. 다음 PREOPEN의 `scalp_trailing_mechanical_policy_apply`만 source date/profile/hash·완료 비용 모수·독립 날짜·보수 비용·한 시장 canary·부모 hash를 검토해 결합 정책 v2 후보 영수증을 만든다. 표본·edge 결손은 hold/carry, 변조된 선택 영수증은 bootstrap에서 차단한다. 선택된 시장별 시작값과 강약 설정은 무후보 날짜에도 같은 hash로 유지하며 명시적 운영 변경 시 귀속을 분리한다. 운영자 override/lock 우선순위와 단일 stage 규칙은 유지한다. Bootstrap 생성·검증, 선택 릴리스, 실제 PID 소비, 자연 완료 비용 후 성과는 별도 영수증이다.

## Authorized intraday policy-preserving code handoff

The existing policy-generation fixture publisher accepts repeated `--source-review`
references for report-only code succession. Each immutable review request binds
clean committed original/current trees, unchanged native family/execution membership,
every changed component's before/after SHA, all affected families and a frozen
review record. The reader derives the inventory from `COMPONENTS` and
`COMMON_CODE_COMPONENTS`; omitted files or families, aliases, dirty sources,
changed evidence and runtime authority flags reject the request. This replaces
new family-by-family report-capability pair additions. Issued legacy exact pairs
remain historical readers. Original native reports and their fixtures, independent
new network-denied fixtures, source/economic gaps and policy guards remain required.
Preserve both release origins and immutable request/review files through their last
consumer. A source review never authenticates an active policy or actual PID.

The sole admitted common-member extension binds the existing capability reader
itself into fixture code generations. Later reader changes receive new fixture
paths automatically. Original generations retain their original membership;
unreviewed execution-owner changes still fail. An issued source review identifies
its immutable issuer and exact code generation. Another clean immutable release
with identical code and fixture plan may reuse it; its selected identity and PID
remain subject to the independent native runtime checks.

Ordered deployment and full health use the same registered report-capability
consumer inventory. Candidate preflight records it; selected preparation and
actual-PID attestation reobserve the same source date and reject changed registry,
role or code identity. Missing optional reports and historical source/economic
warnings remain report-only observations, without becoming new Main startup gates.
The existing active-policy, trailing, quantity, native preparation/P5 and PID
checks retain their own authority and failure behavior.

The submission monitor's reviewed source transition is registered once in
`startup_validation_code_context.REVIEWED_SUBMISSION_MONITOR_TRANSITION`.
The independent preparation reader and ordered handoff derive their successor
profiles from that registration. Each preserves its complete native code profile
and physical-byte versus reviewed-formatting comparison contract. The handoff
checks the entire successor profile even when a caller's original contract has
no historical dependency trigger. Missing, dirty, aliased, mixed or newly added
unreviewed consumers fail before drain; legacy issued profiles remain immutable.
The native canonical-JSON prompt/input identities remain distinct from provider UTF-8 byte hashes, including non-ASCII inputs. Register transitive trace writers and stop source extensions in their actual native roles, and authenticate a complete issued predecessor independently from the merged successor. Unknown origins, missing members and mixed generations remain invalid.

Startup daily-report reads and conditional regeneration run through the existing named scheduler job after engine startup. A valid dated saved report retains its original as-of and is not rewritten as freshly validated input; absent/corrupt reports use the existing builder. Scheduled/explicit refresh and the MarketRegime avg_bull consumer retain their existing behavior. Atomic publication preserves the previous report on failure and prevents partial JSON consumption. The optional report is not a new startup admission gate.

This code compatibility does not make incomplete monitor observations valid.
Predecessor manifest-reader comparisons pass their authenticated selected origin
explicitly to the preparation predicate; candidate comparisons retain the
execution root. A compatible digest pair cannot substitute one phase's physical
source generation for the other.

When the current operational checklist was edited after an already-consumed handoff, first compare every frozen predecessor source. Only a checklist-only mismatch may use the exact prior-release Git checklist whose SHA equals the sealed handoff. Preserve both that original and the user's complete edited document. Under the ordered deployment and detector locks, stage the verified original for the strict predecessor check, then publish the reviewed candidate checklist with the new selector. Restore the edited document with compare-and-swap if transition fails before publication. This does not rewrite the predecessor receipt or permit policy/env/controller differences; retain both identities in the deployment evidence.

A reviewed native-code repair whose source hashes differ from the active policy requires `scalping.reversal_code_handoff` evidence before draining Main. The dated receipt binds the unchanged active pointer and branch definitions, the clean candidate commit, all current contract code, full origin-validator source hashes and native confirmation parity. Only that selected candidate can use it; policy/source errors, missing receipts, changed sources and unreviewed code still fail. The native dependency cache observes the selector and every receipt/source/code dependency. No policy pointer is activated or relabelled. Preserve the receipt, parity and old immutable validator release as referenced sources until their consumer/rollback lifetime ends; the next-session candidate remains separately bound to the final release.

An explicitly blocked initial PREOPEN Main may have native bootstrap/PID consumption but no intraday handoff. The ordered owner may adopt `operator_incident_startup_hold_v1` only with the caller's exact `operator_hold_sha256`, original selector/PID/start/cwd, the original live bootstrap verification, and the collector pin captured before the cooperative stop plus its native closed receipts. Missing proof preserves the hold. Snapshot original verification sources before preparation can advance mutable verification outputs; retain the original hold bytes. Complete candidate checks and P5 before compare-and-swap transfer to the normal ordered hold. Process absence or a new no-PID check is not live consumption. Use the existing drain/publish/prepare/validate/start/attest sequence and failure unwind; never manually delete the hold or infer flat inventory from shutdown.


A clean candidate's P5 may validate that operator-stopped native PREOPEN origin
through `closed_predecessor_review`. The prepared-generation reader must carry
its authenticated closed observation into the independent startup policy loader,
including original source hashes, actor identity and manifest, and repeat the
native proof after full verification. Use the distinct closed-native preservation
basis with historical consumption verified and actual PID consumption false.
The normal live-PID reader remains unchanged. Missing or changed closure evidence
fails; do not skip policy loading, invent a current PID receipt or renew a launch
window. Candidate validation alone never authorizes release selection or hold
transfer.

Normalized trailing reuse copies retain the existing512MiB per-invocation batch and native combined disk budget. A sealed copy checkpoint binds the original approved source inventory and current code generation; resume only after source/destination identity and byte checks. Partial copies never publish a manifest or currentness receipt. Interrupted/changed/corrupt inputs preserve their failed evidence; continue only the bounded remaining copy before full native replay and report verification.


For closed-source trailing preparation, `main_trailing_source_reuse` may stop at
its existing per-invocation copy-byte budget with `trailing_reuse_copy_checkpoint_pending`.
Resume only the same native preparation after verifying its sealed source/code
inventory and copied source/target identities. Preserve the partial attempt and
checkpoint; never increase the byte budget, rewrite the original manifest or
start replay before the complete consumer manifest is published. The final native
report/currentness and candidate/P5 consumers still verify the resulting generation.

Candidate P5 may verify an explicitly held native PREOPEN predecessor after collector closure through the existing closed-predecessor review. The readiness reader and isolated Main preparation reader must bind the original PID/start/cwd, unchanged selector, original consumption/collector/source hashes and full bootstrap. Historical consumption remains true while current/new PID consumption remains false; revalidate the same closed proof at the end. Ordinary readers without that authenticated scope still require live consumption, and subsequent selected P5 and actual successor PID checks remain mandatory.

Signal-clock integration retains the issued evaluation owner across NOT_SENT retries and unknown/in-flight outcomes. Register the complete merged source profile in both the handoff and independent preparation reader; retain immutable predecessor profiles. Validate actual native admission and hold transfer before rereading closed custody, and issue final candidate and selected P5 against that exact merged commit.

Partial SELL custody keeps the original DB position quantity distinct from registry-owned remaining quantity. Startup and periodic consumers must validate both active partial and canceled carried phases against their native journals; a later DB HOLDING/cleared cancel phase cannot rehydrate old submit authority. Preserve unrelated allocation/cancel interlocks through repeated syncs.

Capability fixture publication checks the preserved report origin against the supplied direct source review before issuing evidence. Deployment preparation pins report-original code separately from active-parent custody, and verifies every dated reader after publication. Preserve incomplete earlier fixtures; do not rewrite them or chain an intermediate live code generation into an unreviewed original-to-current claim.

Mandatory pre-drain sequence: (1) freeze selected release/PID/start and unchanged active pointer; (2) finish candidate review and targeted validation; (3) issue the exact candidate `scalping.reversal_code_handoff` receipt using verified native confirmation parity and origin ancestry; (4) run ordered deployment preflight, which validates the receipt, all contract code/source hashes, pointer and origin selector before acquiring a hold or draining Main. An absent receipt fails here with the incumbent still alive. Preparation for the next session cannot substitute for this same-day code handoff. Never reuse a receipt after candidate commit, pointer, source or origin selection changes.

The bounded source-reader successor binds its exact reviewed file hashes and complete predecessor dependencies through `REVIEWED_SOURCE_READER_DEPENDENCY_VARIANTS`. Delay/stop/holding retain their original policy digest and full source checks; unreviewed, missing or mixed reader generations fail before drain. Rising-missed and auxiliary capability reuse requires independent fixtures for the new code and preserved original report/fixture bytes. This permits no policy reselection or historical report rewrite. Verify temporary spool capacity separately from reduced resident memory. The P5 native CLI retains the same-process, same-root parent source-day digest session so its closure includes the native reads; standalone verification still opens its own invocation. Startup diagnostics validate semantic-reuse and invocation digest counters from the real DigestSession/native CLI boundary, accepting only known nonnegative integer counters; unknown keys, booleans and malformed values remain rejected. Exercise that actual issuer-to-reader transfer whenever the diagnostic producer changes, without reusing semantic verdicts or relaxing target-date expiry.

For the P5 post-isolation native recheck, the already authenticated same-run preparation closure may transfer exact byte digests through the private child input. The independent native CLI still reruns its semantic checks and revalidates the closure and source identities before and after the child. Changed, missing, mixed or expired generations fail their existing contracts; an oversized transfer falls back to a cold recheck. This is invocation-local and preserves the original policy and transition authority.

Startup health ordering is exact-PID consumption, completed ordered transition, bounded Sentinel plus observer publication under `run_buy_funnel_sentinel.lock`, then the first full detector sweep. Keep the existing late-admission cutoff. For an admitted producer reserve30 seconds for the observer and cleanup (25 plus5); the observer still requires at least20 seconds. Attestation, both children and cleanup share the original150-second process-start deadline; it is never renewed. The producer attempt shares the original 150-second process-start deadline and keeps detector heartbeats alive. Failure, timeout or partial semantics are passed to the normal detectors without a synthetic PASS or renewed grace. Native cron retains its existing owner; startup children do not notify externally themselves. The reviewed observer CLI reserves five seconds for publication when --notify is absent; with --notify it retains fifteen seconds for notification and publication. It discloses this allocation in execution_budget. This changes no total invocation/process deadline, child cleanup, admission or validation requirement. A startup source producer that could not launch within the original deadline is recorded as unstarted; it must not trigger a source-only publication over an existing full observation. An actually launched producer failure still uses the existing diagnostic path, and the first detector independently validates any retained report. Historical postclose checks use the already-consumed immutable checklist snapshot; they never reseal original strict/controller receipts against an edited operating document.

For a completed, exactly current observer with no applicable observations, the existing artifact detector may retain a close-time warning after its observation window ends only with the same-day native market-close terminal, zero unresolved scalping custody, a current same-PID Main heartbeat and independent live actor/generation verification. File/body/completion clocks must all be within the unchanged freshness bound at that terminal; recompute the exact empty health projection with no unmet conditions. Keep wall-clock staleness, partial validation and all coverage/source-gap fields visible. Watch terminal replacement in the existing final publication recheck, ignoring ordinary live heartbeat progress. Missing closure, stopped/unknown Main, current loss or a mismatched generation keeps the strict failure path; process absence alone never closes observation. This diagnostic classification grants no restart, policy, source or order authority.


Controlled Main self-termination closes diagnostic observations through the existing pre-SIGTERM producer-summary drain. It calls only an already-loaded engine's close_observation_sources; an unstarted engine is never imported. The same cleanup replaces the former inline run_sniper finally block. Seal observation/commit admission, stop the existing local sampler within one second, enqueue exact observation-only censor receipts at the first actual cutoff, drain the existing queue within one second, then flush summary. Failed sampler stop or unconfirmed writes remain failures; queue admission is not persistence. Already-overdue horizons remain missing and actual order terminals stay distinct. The exact successor code profile preserves every issued predecessor and rejects mixed cleanup/observer generations. This is prepared code behavior until an authorized release/PID consumes it; no new restart authority, signal handler, quote TTL, policy or order behavior is introduced. See the [causal repair and validation](audits/postclose-root-cause-recovery-review-2026-10-19.md#controlled-delay-observation-shutdown-repair-2026-10-20).

A reviewed immutable runtime release may be applied during the session under explicit user deployment/restart authority. Keep the original same-day PREOPEN status, bootstrap env/manifest, prepared index and prepared receipt unchanged. Use `src.engine.automation.ordered_intraday_deploy` from the reviewed candidate, following the ordered transition below. It verifies the incumbent before requesting graceful termination, waits for Main and its supervisor to exit, then publishes the candidate selector/checklist and prepares the native `--previous-stopped` handoff. Preparation binds the stopped predecessor's exact PID/start/cwd receipt, clean previous release, succeeded exact-day PREOPEN and native full bootstrap in a separate immutable receipt. This is a code handoff, not PREOPEN rerun or candidate promotion. If a removed historical release owned the original checklist symlink, preparation must use only its exact sealed Git/preserved snapshot and verified predecessor consumption; a missing path never permits arbitrary current-document substitution.

The launcher admits a different commit only through that verified same-day receipt; native bootstrap and custody guards still execute. First launch is bounded to 15 minutes. After native new-PID verification, a separate consumed receipt binds its cwd/start and policy manifest. `intraday_release_handoff --verify --target-date YYYY-MM-DD --pid PID` checks the consumed schema, status, release/date, handoff and manifest hashes, and exact live PID/start/cwd, then rechecks generation stability. Native PREOPEN without a code handoff is accepted only for its original selected commit with exact-PID bootstrap verification. The launcher records selector PID success only after this verification; failure is reported and does not authorize forced child termination. Ordered deployment independently repeats exact-PID verification before completion. A verified consumption permits later same-day guarded restarts with unchanged policy files; another date or changed file/selection fails closed. Prepared verification discloses preservation of the original generation and still checks its sources. Historical owner receipts remain immutable; retired executors are never restored. A failed source-day finalization remains FAIL.

Reviewed trailing event/SELL receipt repairs cross the same policy-preserving code gate only through exact original/candidate source hashes. The current rising-missed and holding-vote code generations require independent network-denied fixture receipts; preserve original reports, policy hashes, native receipt gaps and all execution guards. Native Main receipt custody does not manufacture scanner lifecycle identity or economic acceptance. Build integrations over the actual selected release so newer deployed source, routing and custody repairs are retained.

A reviewed holding/cumulative integration also binds entry-cancel-wait and auxiliary code generations. Publish fresh network-denied fixtures for each changed generation; a preserved historical auxiliary fixture is checked independently and cannot certify new code. Keep the original report, source state, target date, PREOPEN and policy bytes. Cumulative registration uses its sealed next-session publication/target contract; a code restart does not activate that future candidate.

The retired-helper/parser cleanup uses `REVIEWED_RETIRED_REVIEW_DEPENDENCY_VARIANTS` in the existing native handoff verifier. Its exact six-file generation retains the complete product-intake predecessor dependency set and original policy contract extensions. Matrix public outputs and the permanent False overnight entrypoint are preserved; report families keep their own reviewer, decisions and provider parameters. Missing, dirty, mixed or changed dependencies still fail before drain. This code-review profile does not issue a same-day policy handoff or establish PID consumption; prepare fresh candidate-bound parity and native receipts before an authorized deployment. The integrated cleanup/SQLite profile matches both exact selectors and includes all nine changed dependency files plus the complete predecessor set; each independently issued cleanup or SQLite profile remains verifiable.

The native handoff verifier also owns the exact formatting succession recorded in [the source-format review](audit-reports/2026-10-24-source-formatting-review.json.txt) and [its final consumer review](audit-reports/2026-10-24-source-formatting-consumer-review.json.txt). Only the pinned physical result may be compared with its verified original Git bytes; unknown source bytes retain the existing rejection rules. The original policy digest is computed from the original physical source, and candidate files remain bound to their actual committed bytes before historical comparison. The verifier itself is never projected. Independent preparation uses the same exact successor mapping; the sole preparation-reader logic change is separately identified in the review. This preserves historical contracts without rewriting receipts or granting deployment authority. A formatted candidate still needs fresh candidate-bound parity, family fixtures, preparation and final consumer verification under the normal authorized transition. Preserve the referenced original Git commit and formatting review through their last consumer. The router separately accepts only the reviewed original/formatted Main-only retirement guard pair while preserving the original retirement receipt and all removed-surface checks. Summary migration retains the original parser and callback-owner identities, verifies unchanged native callback text, archives the original checkpoint and reads only the suffix. The auxiliary production input contract binds the reviewed formatted transform bytes; unknown bytes and unreviewed registry generations remain rejected.

The auxiliary envelope owner preserves the authenticated registry's original wire contract when rebuilding a frozen request. Exact reviewed compatibility admits only the declared source generation; payload/schema hashes still come from the rebuilt request, and unknown or mixed contracts fail. Integrations of this reader change require fresh auxiliary capability fixtures, original-request parity, and candidate-bound historical reader receipts before optional research regeneration. Preserve prior complete code profiles and all original registry, request and compatibility evidence.

## Single selection

`data/runtime/retirements/main-only-retirement.json` seals the permanent automatic-owner exclusion and removed executable surfaces. The router rejects releases that restore those surfaces or change the approved retirement guard. Historical quantities and intents remain operator-managed; no broker-flat, terminal-order or residual exit-worker prerequisite applies. Keep only a clean Main recovery release with the same exclusion and manual boundary.

All routed operations receive the two approved account/journal identity keys from `data/config/native_owner_custody.env`. The router parses this local file as bounded assignments without shell execution and fails closed when retirement is active and the identity is absent or invalid. Main startup, scheduled postclose/PREOPEN and web must use the same common journal namespace. Web unit drop-ins load the same file with `EnvironmentFile`; never print its values in diagnostics.

`data/runtime/runtime_release_selection.json` selects one absolute managed release root and its full Git commit. The workspace entrypoint is `bash deploy/run_runtime_release.sh`. It checks the selected HEAD, clean `src/deploy/restart.sh` and shared `data/logs/tmp/.venv/docs/restart.flag` before invoking a target. Missing or invalid selection blocks execution; it must not fall back to mutable workspace code.

The canonical workspace `restart.sh` delegates to this entrypoint. The reviewed release's original `restart.sh` preserves its policy code pin and custody-aware restart procedure, and its post-restart PID check uses `automation.runtime_policy_bootstrap --write-verify-artifact`; the retired generic apply module is not a valid verifier. Do not call old release restart scripts or workspace `src/run_bot.sh` directly to choose a deployment. Do not edit or pull inside the selected release.

The terminal-clock/custody successor preserves the strict market-session timezone contract, binds the live KST decision and HOLD receipt, and excludes only explicitly manual holdings with no pending order or reconciliation. Unknown custody, missing/stale/nonfinite/future HOLD evidence and in-flight exits remain unresolved. Its exact source handoff requires fresh rising/holding capability fixtures. A restart after the final intraday observer slot requires a bounded publication from the selected release and same-run detector verification; an old observer receipt or restart alone cannot establish current validation. Original terminal failures are retained and are never converted into successful HOLD receipts.

## Semantic detector routing and verification boundary

The `error-detection` router target runs the selected immutable release's full detector through the existing owned-log wrapper. `deploy/install_error_detection_cron.sh` retains the two weekday schedules (07:00–20:55 every five minutes; 21:00–21:50 every five minutes), environment and log owners; it preserves the separate finalization cron. Health reports record the actual detector root/commit/source hashes and selected release identity. A missing/dirty release fails closed without workspace fallback.

Periodic handoff monitoring uses the native read-only `generation_only` checks: sealed strict/controller identity, current summary/checklist/stage generation, selected-release preparation and bootstrap hashes. Current Main hashes retain the existing bounded validation. Pre-cutover summary reads use the sealed historical archive only for the original bytes; the archive never authorizes a producer rerun or a current/future source date. This is not a new whole-chain verification or trading approval. Preparation, finalization and PREOPEN retain full current-contract rechecks by default; the lightweight option is not exposed by their CLI. Selector changes require freshly prepared and fully verified next-startup receipts. Source gaps remain separate from normal carry and future PID consumption.

Quantity monitor historical exclusions require an explicit record-ID acknowledgement through the existing native projection publisher. Full terminal/census validation and exact stage/report/input/fact hashes remain required. Only an isolated past source-only carry with cost-eligible trades and bound policy may classify its accepted exclusions as historical diagnostics. Original source gaps, excluded counts and null economics remain visible; a new generation/population, changed source/cost/code, current-day collector failure or invalid contract still alerts. Re-publication preserves only the identical accepted population under the existing monitor lock. Publish the reviewed current-code projection under the ordered transition/detector locks before the first current-PID health verification; preserve original reports, cost indexes, active quantity policy and prior projection manifests. This is report-only classification, not historical economic reconstruction or runtime promotion.

## Closed-session trailing regeneration

An in-progress native weakness cursor is an optional issuer without terminal byte proof. Ignore that uncommitted issuer only; retain the same unproved-byte limit and all original/current source checks. Completed cursors still require exact sealed manifest/terminal/date/source binding.

Approved frozen replay may resolve the original native research-cost index through its immutable `index_generations/<physical-sha>.json` and original receipt bodies. Validate the live index contract and every original dependency; keep current actual/official costs mandatory and preserve historical nulls. This uses the existing replay context and native declared-research reader, without changing active cost/policy files. Current regular consumers remain bound to the current index.

When an official cost query window expands, approved frozen replay resolves only exact original source bytes named by the sealed inventory and its immutable allocation receipts. The native cost reader verifies unchanged original facts/account/provider/request scope and accepts only later-window rows whose execution date is also later than the source date. Original-date late fees, corrections, missing history and unknown bindings fail. Assembler, holding-cost cache and declared official/research generation consumers share that resolution; current discovery still observes latest bytes. Cache reuse pins both alias and original archive epochs and retains the existing read budgets. Reissue only affected report currentness/quantity projections through their native publishers before candidate P5; never edit original source or policy bytes.

Raw-input inventory admits exact native `.jsonl` and `.jsonl.gz` sources. Compression receipts, locks and failed-attempt sidecars are storage evidence, not additional research rows. Previously issued frozen inventories retain exact receipt bytes with their original verified logical source. Native archive/index validation remains mandatory, including when compression occurs after the original report was sealed.

Provider-lineage observation uses the existing native trace index. New entry projections retain exact PID/attempt/request/response fields; issued projections use only verified original offset/size/SHA reads. Projection plus raw intake remains bounded to the existing8MiB. Missing/stale/incomplete/changed index or unidentified clock/source gaps never certify complete coverage; unindexed sources retain the bounded raw reader. Local deadline/unsent cancellation terminals pass through the existing trace annotation without provider retry, order permission or budget changes. See the [same owning review](audits/postclose-root-cause-recovery-review-2026-10-19.md#exact-lineage-eight-and-frozen-cost-reader-repair-2026-10-22).

Use `src.engine.automation.main_trailing_source_reuse` for an already approved frozen holding/input epoch after a report-code repair. It preserves the original extraction contract, every normalized field and source gap, the original holding/PREOPEN/policy bytes, and the parent-equivalent bundle. Current replay, complete partition/census checks and independent arithmetic validation still run. It reuses native byte/identity attestations only; it never reuses an old semantic verdict or grants runtime apply authority.

Native market-weakness cursor issuer paths may retain the normal immutable release/data mount. Frozen-source reuse accepts only the exact canonical data root and namespace/date/generation/filename suffix, rejects all links below that mount, and applies its original strict seal/owner/epoch/source checks to canonical issuer paths. It never rewrites the cursor or its source/terminal receipts.

The native report must bind each SHA to its exact current device/inode/size/mtime/ctime, or an earlier native identity observation must bracket the original sealed full-SHA publication in the same unchanged epoch. Metadata-only preservation repairs require a separate native full-byte attestation. A changed/expired proof cannot fall back to a large full-file read. Unproved sources are capped at32MiB before intake, with a separate32MiB vote-journal population cap. The digest session has a32MiB cumulative full-hash budget; normalized tree reads, bounded journal validation and code/metadata reads are separately accounted. This is not a claim that total process I/O is32MiB.

Historical vote inventory binds only native events through the source session. The registry retains its exact original byte prefix and complete native hash chain; later-session orders for owners outside the frozen research cohort do not invalidate it. Late historical events, cohort-owner changes, unknown/global custody changes, altered prefixes and invalid native terminal proofs still block. No live custody or journal is written.

Example, with the actual source/target dates and an isolated normalized input root:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.automation.main_trailing_source_reuse --data-root /home/ubuntu/KORStockScan/data --source-date 2026-10-16 --target-date 2026-10-19 --input-output-root /home/ubuntu/KORStockScan/data-research-inputs/main_trailing/reused-2026-10-16
```

The default is byte-proof preflight only. `--write` explicitly performs the admitted native regeneration and issues the report-only currentness receipt after full native verification. It never edits the selector or restarts Main. A new report code generation requires the usual reviewed candidate, active/delay/stop/holding handoffs and authorized ordered transition before live observation.

New AI payload/trace/prompt/request, pipeline raw and holding-vote append owners also publish indexed compact rows and native offset/size/SHA hash chains. Completed snapshot writers hash bytes while writing and publish resident normalized trees with a sealed census/cost/snapshot manifest. Normal trailing assembly, original holding-request lookup, position/date-scoped votes, archived-source readers and the delay source observer consume those projections. This is byte/source acceleration, not a cached semantic verdict. Missing, interrupted or stale coverage stays pending; a changed source never silently reuses its old index.

Use `src.engine.automation.main_trailing_source_store --data-root <data> --source <plain-jsonl>` for one explicit resumable historical migration step (at most8MiB, default1second; native background catch-up uses50ms per0.5second rotating turn). No report reader launches migration. Monolithic legacy gzip requires a separate offline migration; normal reports/retries must not scan full100–200GB sources or rewind gzip. Native append callbacks never scan history or checkpoint; busy writes use a bounded resident-byte retry queue. WAL checkpoints run outside the native append lease at most once per minute.

The pre-submit observation sampler reads only existing route-owned0D cache every50ms. It preserves real observation time, route/transport epoch, quote freshness and horizon tolerance; it creates no subscription, provider or order call. Final auxiliary submit validation shares a verified immutable policy view, rechecks the pointer at exit and retains latest revocation and the original five-second signal boundary. Deployment, exact PID consumption, natural coverage and actual submission remain separate acceptance under the current checklist owners.

## Cross-session deployment gate

Before a coordinated release transition, run `bash deploy/run_runtime_release.sh --check-release-set`. The read-only check serializes against transitions, validates the selected Main release and rejects a running retired service. A valid empty installed-unit inventory is expected after removal. Verify web `WorkingDirectory`, effective `ExecStart`, commit pin and actual PID separately. A routing PASS does not establish functional health, policy consumption or economic results.

The main `start`/`restart` transition, cron installation, and every repository systemd installer/uninstaller use the same nonblocking `data/runtime/runtime_release_set.lock`. If it is held, the competing transition fails before changing an owner. Repository installers acquire it themselves; do not wrap one in another lock. For a manual selector publication or out-of-band systemd change, hold it with `bash deploy/with_runtime_release_set_lock.sh <command>`; this also takes the PID-receipt selection lock so an atomic selector write cannot overwrite a concurrent receipt. PID-receipt writes use that selection lock and revalidate the selected root before replacing the manifest. This cannot coordinate edits made outside the wrapper, so release selection and owner configuration must be changed only through these guarded paths. A release transition still changes only the explicitly named owners; never restart a retired executor or restore its old installer.

Supported operations: `start`, `restart`, `validate-startup`, `preopen`, `postclose`, `paired-replay`, `controller`, `tuning`, `finalize`, `eod`, `archive`, `buy-funnel`, `holding-exit-sentinel`, `monitor-snapshot`. Intraday holding-exit sentinel cron uses `holding-exit-sentinel` so its report code follows the selected release. Invocation resolves the selection once and pins `PROJECT_DIR/PYTHONPATH/VENV_PY` for its child chain. The selector does not update an already-running supervisor; moving the current PID requires a separately authorized graceful restart.

Explicitly authorized `postclose-stop SOURCE_DATE` routes the existing wrapper's
`--stop-only` branch. After native calendar/EOD admission, the ordered transition
owner pins code, consumed policy, actor and collector, requests cooperative
termination and verifies Main/supervisor/writer closure. It neither selects nor
starts code. Only that owner's hold can be removed after closure; failed requests
retain their original evidence. Closed-log/tmp retention uses its existing bounds
before calculation. Foreign holds, changed sources, unclosed writers or failed
cleanup block calculation. The one-day delay restores its stop-only row together
with the exact owned schedule rows; normal next-session PREOPEN stays separate.

Read-only checks from the canonical workspace:

```bash
bash deploy/run_runtime_release.sh restart --print-plan
bash deploy/run_runtime_release.sh preopen 2026-09-11 --print-plan
bash deploy/run_runtime_release.sh --check-cron
```

Use the actual target date instead of the example. A plan check proves routing, not future policy approval, WS health or a running PID.

## Scheduled scope and maintenance

Manual archive recovery retains the native `dashboard_db_archive_cron` owned-log
boundary and its canonical cron log. The internal `dashboard_db_archive.log`
records compression details; it cannot replace the wrapper's source-dated terminal
receipt. Preserve the router's source-date environment and reuse verified archive
prefixes. Never copy a DONE marker into a missing consumer log.

Final detector suffix recovery accepts both failed scheduled and failed recovery
attempts. A scheduled prefix additionally binds its effective day and KST start
to the native trading calendar. Original controller, cleanup, detector clocks,
source generations and raw logs remain mandatory. A rejected preflight before a
new START preserves the preceding execution anchor and all rejection evidence;
it cannot grant stage completion or reset a deadline. Use the existing
`--recover-closed-target --resume-final-detector` owner only for an unchanged
authenticated prefix. Changed calculations or generations require their native
dependency disposition; a report-only repair grants no new startup or policy
authority.

Nine cron entrypoints use the selection: 07:35 PREOPEN threshold, 07:55 main start, 20:05 EOD, 20:10 cooperative postclose stop and bounded cleanup, 20:30 postclose/controller/tuning, 20:50 archive and 05:35 next-KRX-session finalization. Main and archive wrappers validate the exact-date EOD terminal before resource-heavy work. The finalizer resolves the immediately prior KRX trading date from the effective date, skips non-trading effective dates, stops predecessor waiting at 06:00 and bounds cleanup/detector completion by 06:50, leaving 30 minutes before the 07:20 PREOPEN scanner. The 21:05 paired replay wrapper is manual compatibility; the main wrapper owns the current auxiliary calculation. The operational cron check requires all nine installed owners. Existing environment values, log ownership/redirection and wrapper locks are preserved. The 07:30 legacy stop remains separate; the 20:10 stop uses the native stop-only transition and verifies collector closure before calculation. Other Main intraday observer/scanner jobs retain their separate owners. Dedicated retired services, timers and IPO auto-order cron are removed.

The normal installer migrates only recognized owned postclose/controller/tuning
rows from20:10 to20:30, adds the routed20:10 stop-only owner when absent, and
rejects unknown schedules or an active one-day override. The read-only check
requires that final order without installing it. Stop failure, unclosed collectors
or incomplete cleanup still block calculation; original stage deadlines and all
other scheduled owners remain unchanged. The dated one-day mechanism below is
historical compatibility and cannot duplicate an installed permanent stop owner.

An explicitly authorized one-day postclose delay uses the existing cron router's
`--install-postclose-delay-once` and `--restore-postclose-delay-once` modes. The
owner records the original and installed cron rows, selection identity and an
immutable raw selection snapshot before publication,
verifies installation with compare-and-swap, and schedules bounded restoration
of its own rows while preserving unrelated edits. The cron detector accepts the
later start only while the issued receipt, producer and installed schedule agree;
its original selection is authenticated as of installation, rather than requiring
a mutable current selector to retain historical bytes. Legacy receipts may use
the exact same-date native transition backup; no missing identity is inferred.

missing or changed evidence is not a successful start and the original completion
deadlines remain in force. This scheduling facility does not stop Main, run
pre-postclose cleanup, or establish collector closure. Those require their own
native transition and verification before any operational sequence is claimed.

After the exact-source controller reaches `done` with a current whole-chain strict receipt, its wrapper prepares the next operating day's bootstrap under `data/runtime/policy_bootstrap/prepared/<target>/`. The 05:35 finalizer repeats this preparation after any controller refresh and successful final detector, so the latest closed generation owns the preparation. This isolated env/manifest/verification is bound to the controller, direct Main machine and compact auxiliary policy receipts, verified incumbent, and selected immutable release. A late recovery after the scheduled 07:35 PREOPEN cutoff prepares the next KRX trading day after the recovery date; it does not require a postclose run on an intentionally skipped bot day. The preparation writes no active env, policy pointer, order, or PID receipt. If preparation fails, the controller/finalizer wrapper reports failure without turning controller `done` into a readiness claim.

At 07:35 the selected release first rechecks the preparation's exact source, policy and release hashes; it then executes existing date-bound publishers and activators and writes the live bootstrap. The 07:55 launcher requires an exact-date `succeeded` PREOPEN status from the same release before sourcing the live env, and it still verifies the live bootstrap and actual PID separately. A changed source, selector, missing preparation, failed PREOPEN, or stale status blocks startup. Preparation success is a preflight result, not proof of target-day activation, broker availability, live orders, or economic improvement.

The cron completion detector checks the finalizer and its cleanup against the immediately prior KRX source date, while their 05:35–06:50 window belongs to the effective KRX date. A valid terminal completed after 06:50 is reported as `recovered_late` and remains visible as a warning. Missing terminals, missing completion times and invalid current-generation bindings remain failures. A receipt created before the selected generation-binding release may be marked as a dated historical gap; this does not validate a new source date.

The widget-evaluation, episode final-refresh and owner-policy timers/installers are removed. Main postclose dispatch owns six stages: machine policy, pre-submit delay, legacy Main report, auxiliary policy, outcome labels and summary handoff. Optional Samsung diagnostics are report-only sidecars. Retired output absence is not a current startup or policy gap.

After an authorized cron installer is run, check routing again: older installers can recreate workspace entrypoints. `bash deploy/run_runtime_release.sh --install-cron` reconciles the nine mandatory pipeline rows and all three intraday snapshot rows, preserves unrelated rows and leading environment/log redirections (including main start), creates before/after backups in `tmp/runtime-release-cron-*`, rejects missing/duplicate/unrecognized commands and verifies readback. It recognizes an actual command owner, not an echo/printf/conditional containing the route. Scheduled `--print-plan` and unexpected extra arguments are rejected; dated jobs retain the existing KST cron date expression. Unsupported command syntax requires review, not an automatic rewrite. `--check-cron` only reads the current snapshot and does not create or wait on an installer lock. Installation uses a nonblocking lock; do not run it concurrently with another crontab editor. Direct out-of-band edits after its final recheck cannot be atomically prevented by the crontab interface.

Ordered deployment keeps already-existing native source-index readonly connections resident across Main drain, launch and exact PID attestation. The existing source owner checks paths/ownership; at most six current-day/global namespaces claim2MiB each. It opens no read transaction, creates no missing index, reads no raw history and changes no busy/quote/startup deadline. Pin failure leaves Main undrained; success/failure closes all pins. This prevents concurrent cold WAL recovery between the final old client and the new Main/launcher. Original failed transitions and owned holds remain subject to the documented phase-specific recovery.

For a release update: review and test only intended changes in a separate worktree, commit that release, mount shared state/docs and verify dated code/source pins. An authorized intraday Main transition uses `src.engine.automation.ordered_intraday_deploy` from that immutable candidate. Do not publish a new selector while the predecessor Main is alive. Never switch while scheduled wrappers are running: separately started followers could otherwise select different releases. Keep the selector record and a clean recovery release that preserves permanent retirement. Do not restore a pre-retirement executable release. Do not erase data, reset quota or change policy to make a route pass. Shared `.venv` means dependencies are not immutable; package changes need their own approval and validation.

Restoring a cron backup is appropriate only after checking for subsequent unrelated edits; never overwrite a newer crontab wholesale. Rollback selection requires the prior release to pass the same shared-path and source checks, including the shared `docs` contract. Merely reverting a commit string is not enough.

The reviewed scheduled-execution repair pins EOD/postclose/controller/tuning/archive/finalize/PREOPEN before selector resolution and through the wrapper child. These readers share the existing router's execution lease; ordered execute requires its exclusive side before preflight through success/failure recording. New scheduled readers wait for an already-started deployment before resolving its selection. Native family/release writer locks remain independent, and the wrapper inherits the lease so killing only its router cannot release it early. The common workspace router must be installed from the same reviewed source at an idle boundary; an older already-running wrapper has no retroactive lease. Preserve its original code/receipts and verify it has ended before publication. This changes neither cron times nor policy/startup authority.

During a bound live/closed predecessor review, authenticate an existing prepared-code receipt against the selected release's own inventory before comparing the reviewed candidate. The existing native origin resolver proves that selected custody; the consumer bridge then checks the candidate's exact complete delta, actual hash and unchanged sources/review identity. Never compare candidate hashes directly to a selected-release receipt or substitute a code handoff for candidate P5 or actual next Main consumption.

## Acceptance boundaries

### Policy loading and exit before the operating day

In a release containing this implementation, `bash deploy/run_runtime_release.sh validate-startup YYYY-MM-DD` validates the selected preparation with Main's real native policy loaders and exits before DB, broker, provider, Telegram, scanner or trading initialization. The target date is mandatory. It can be a future trading date while the current day is closed; neither the system clock nor the live PREOPEN date check is overridden. `--print-plan` remains read-only. This manual operation adds no cron, startup hold or operating policy activation requirement.

The shared `main_policy_environment.sh` preserves the live launcher's defaults, bootstrap, authoritative AI-context overlay, native custody, retirement and final settings in their original order. Validation accepts literal policy assignments and uses private copies, strips ambient shell/interpreter hooks and starts an isolated Main child. Normal Main retains the original delay/trailing preparation timing and the other consumers' existing later loading and operating receipts.

For an already consumed intraday policy, the validation parent may authenticate the existing live handoff and consumption receipt when no prepared-code receipt was issued for that family. Bind the original policy/code inventory, frozen sources, selector and exact PID/start/cwd; the isolated child independently verifies those bytes and identity fields, and the parent rechecks the live identity after the child. This read-only proof does not publish operating receipts or authorize a stop. Existing prepared-policy origin verification remains mandatory for that route.

The existing trailing-index background owner can recover a pipeline append-chain cache gap by preserving and checking its SQLite snapshot before a bounded reset. Snapshot I/O stays outside native writer locks (64MiB/0.5s cap); reset uses both existing writer locks and a 50ms progress budget. A large failed cache is cleared in durable batches of at most128rows/8MiB plus128minute entries while its invalid source state and original snapshot stay bound; only the empty derived partition can enter prefix rebuilding. Raw JSONL remains untouched. Existing 8MiB/50ms migration verifies the whole prefix before readers become consumable. Lock, archive, inode or generation failure preserves pending/invalid status. Recovery start is not source closure or policy authority.

A preserved intraday PREOPEN scope keeps its original label. P5 may delegate the current invocation's independently verified native Main closure under a distinct intraday basis only when selected release, preserved PREOPEN commit, bundle/family identity, frozen validation and source digests all bind. A sealed-generation PASS or missing bundle observation cannot supply that closure.

The parent records successful native bundle loading and semantic validation boundaries: an intraday preserved generation can validate an already-read bundle. A rejected native validation never contributes a successful closure, and the original source, inventory and isolation checks remain required.

The child requires unprivileged Linux Landlock and seccomp, closes inherited control descriptors and permits writes only in its private run directory. Native source/code/policy validation remains mandatory. A denied side effect, invalid or incomplete consumer, identity mismatch, timeout, changed input or surviving worker fails the validation; exit zero alone is insufficient. Results live under `data/report/main_startup_validation/<target>/<run-id>/final.json`. They always retain `actual_pid_consumed=false`, `allowed_runtime_apply=false` and `runtime_effect=false` and never replace the operating bootstrap/PID or observer receipts.

Before deployment, invoke the same module from the clean reviewed candidate with `--workspace <canonical-workspace> --target-date <date> --candidate-root <that-candidate-root>`. The candidate must already have the normal shared mounts and source validation. This does not publish a selector or issue an operating code handoff. Parent validation preserves the exact original prepared-policy code lineage, including authenticated historical origin receipts, then seals the reviewed source delta for a read-only child context. The context cannot be installed outside OS isolation and has no operating authority. Day-specific PREOPEN activation and real Main PID consumption retain their existing owners and checks. See the [plan and implementation boundaries](proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md).

Ordered deployment requires explicit `--candidate-p5-path` and `--candidate-p5-sha256` (or the same Deployment constructor arguments for an embedded `execute` caller). Before any startup hold or drain, the owner authenticates the bounded original final.json, SHA, run/date, execution root/commit, successful isolated termination/source checks and non-operating authority flags. Its selected root/commit bind the incumbent selected during candidate validation; they are not required to equal candidate execution. Keep this exact identity through every pre-publication CAS. Publication replaces inherited candidate_p5_path/candidate_p5_sha256 with the pinned current candidate proof and revalidates under the selector lock. StoppedDeploymentRecovery uses the same proof contract against its failed selected origin and preserves original failed selectors/proofs. Selected prepared P5 remains a separate execute prepared-validation hook and never overwrites the pre-drain candidate evidence. No manual selector repair is authorized by this contract.

For the reviewed AVG_DOWN input and Main SOR integration, the existing handoff owner binds the full predecessor dependency closure plus the exact vote-context and route-proof sources. The two new holding inventory members are family-specific reviewed extensions; historical policy digests and original receipts remain unchanged. Premarket, regular and aftermarket use the existing session windows, routes and hard guards.

A reviewed handler generation that adds research-source imports must also bind those dependencies to exact reviewed bytes and candidate Git objects during native code-handoff verification. Historical handlers retain their original dependency requirements and frozen policy digests. An integrated candidate may be assembled and checked offline while other research continues, but an explicitly deferred P5 must wait for the final code and source generation. Candidate layout validation neither publishes the selector nor validates a real prepared-policy child. See the [integrated candidate boundary](audits/main-policy-holding-integrated-candidate-review-2026-10-18.md).

The postclose overview recognizes a fully rechecked isolated preparation for the same source date as `isolated_prepared_next_preopen`. This reports next-session readiness with `day_of_activation_required=true` and `actual_pid_consumed=false`; it creates no live bootstrap. Historical retired-family receipts remain archive evidence; current Main handoff neither requires them nor activates research or expansion.

The final controller reseal requires the summary stage's consumed input and prerequisite generations to remain current before writing its receipt. After producer recovery changes those generations, refresh the native `summary_handoff` stage before whole-chain finalization. A changed controller output alone cannot refresh a stale summary computation.

A current Main win-rate carry evaluation can preserve an already staged immutable publication. Summary readiness accepts this only when the native Main stage validates `existing_incumbent_preserved`, the exact target, original publication sources, unchanged parent/policy and the current evaluation generation. The summary reports original publication and latest evaluation hashes separately. A changed candidate, stale stage or mismatched target remains invalid; this receipt does not establish policy improvement or PID consumption.

Artifact semantics accepts a legacy support diagnostic only for an explicit non-promoting `source_gap` without a candidate, or a `hold_candidate` whose runtime effect and apply authority are both explicitly false; current promotion version checks remain mandatory for selected candidates. Auxiliary split checks reconstruct the native scanner or full fixed-watch identity through the postclose identity owner and retain chronology, overlap and frozen-selection checks.

For a published cancel-wait reconciliation contract from 2026-10-02, the native controller refreshes the direct report tower after the runtime summary and before the next checklist. Direct strict verification requires the tower's current source binding and cancel projection. Summary stage code custody includes the tower producer. Legacy reports without this contract retain their historical diagnostic boundary; the report tower does not revive common tuning search or grant runtime authority.

Source review and dry-run routes do not prove economic improvement or validate unfinished adaptive exit. Actual day-specific candidate/env/activation, operator overrides, runtime verification, KRX/NXT authority, quota and broker guards remain owned by the existing PREOPEN/launcher/policy contracts. Current source selection, actual PID consumption and natural trade/economic evidence must be reported separately.

## Historical independent-machine deployment

The September 10 independent machine supplements and September 11 shared-machine pins are historical evidence only. Their executable releases, service pins, timers, recovery instructions and pending-order auto-management no longer apply. Original journal receipts are preserved for operator manual management. Main rollout, sizing and hard safety continue under their own current policy contracts.

## Main rollout and bootstrap compatibility

The main Entry rollout is separately pinned by `KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH` and `KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256` in the existing operator handoff. The publisher is `src.engine.scalping.entry_setup_scalping_rollout`, with an aware effective timestamp, full reviewed commit and explicit `APPLY_ALL_SCALPING_V2_14` confirmation. It uses a new immutable file, preserves the existing global daily accepted-order ledger and execution guards, and remains effective until operator revocation. It does not relabel old PREOPEN candidates, alter Holding/Exit schemas or add AI calls to independent machines. Startup clears inherited rollout pins before reloading current operator settings. Future exact-date env validation remains required; daily reapproval of the same persistent rollout is not.

The exact-date bootstrap refreshes only its handoff coordinates, `KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true` and `KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE=<target-date>`, before applying operator overrides and locks. These coordinates do not select a new threshold. An explicit operator value still takes precedence and a false or mismatched value fails PREOPEN. PID verification compares the final launcher environment, including the same hash-verified AI-context overlay loaded immediately before `bot_main.py`. Plain `--verify` is read-only; the launcher and authority preflights commit the current receipt only with `--write-verify-artifact` after that check passes.

A committed multi-timeframe context marker normally remains hash-bound to its original manifest and env. If both legacy pre-bootstrap-cutover commit files were retired together, the launcher applies the existing context-only rollback environment instead of blocking the whole bot: multi-timeframe entry/holding context is OFF and the baseline input preflight remains required. A partial file loss, post-cutover gap, marker authority change or hash mismatch still fails closed and blocks startup. This recovery changes no threshold, provider, order, quantity, cap or hard-safety owner.

The separately authorized V2.15+ auto-promotion pin uses `KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH` and `KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_SHA256`, generated with `--auto-promotion --confirm APPLY_ALL_SESSIONS_V2_15_PLUS_AUTO_PROMOTION`. It covers the existing exchange/session scope plus integrated KRX/NXT aftermarket, but promotes only a registered V2.15+ candidate with exact-cohort postclose evidence and a same-policy-hash PREOPEN activation. Any absent, invalid, stale, or cross-cohort candidate falls back to V2.14; it does not change quantity, caps, broker guards, providers, or create new AI calls. The launcher clears both pins before it loads the current operator handoff.

The prompt contract never owns main quantity, residual legs, or scale-in: their existing owners remain `position_sizing_dynamic_formula`, `entry_split_order_plan`, and `scale_in_split_order_plan`. A bounded integrated-aftermarket SOR one-share canary can publish a separate exact-date successor policy only after broker acceptance, receipt/route/type validation, source-quality pass, and a valid central sizing policy. The next PREOPEN selects that policy by hash and exact active date; missing or invalid evidence leaves the one-share canary/ordinary guards in place. The successor policy never changes caps, cooldowns, hard safety, or a symbol with unknown current venue eligibility.

## Main fixed watches

The five authorized fixed watches consume Main machine/auxiliary policies and native Main/manual custody. Former Doosan group transitions and generic episode templates are superseded by complete retirement. Historical quantities must not be adopted, sold, canceled or used as a retired-owner restart prerequisite. Main flat/source/order safety and manual vetoes still apply independently.

## Bounded auxiliary tuning and intraday binding

Release preparation uses `automation.auxiliary_reader_readiness` to validate the exact candidate bundle's auxiliary source, registered bindings and current readers. Changed readers require the native compatibility receipt, hash-bound parity evidence and complete frozen original readers; matching readers need no additional receipt. Missing or changed proof fails before PREOPEN readiness publication. The receipt freezes its small dependency hash set for sealed-generation rechecks.

The same read-only check runs in intraday release preparation/consumption and in `src/run_bot.sh` after native current-policy validation but before spawning Main. Run `PYTHONPATH=. .venv/bin/python -m src.engine.automation.auxiliary_reader_readiness --target-date YYYY-MM-DD` from the reviewed release; add `--preparation` to inspect the exact dated candidate. This check never issues compatibility proof, changes a policy, calls a provider/broker or claims PID consumption. It does not run inside each live AI evaluation. Native readiness preserves valid legacy/nonregistered consumers without restoring retired owners.

PREOPEN preparation also binds the exact dated v6 activation candidate, its bundle/file hash and selected release commit. A reviewed code-only release must stage an identical-policy code refresh before rebuilding summary, strict/controller and prepared receipts; a bootstrap PASS alone cannot attest the later activation. The prepared generation checks this binding without running provider calls or policy reselection.

An explicitly approved recovery of a failed PREOPEN can use `next_preopen_readiness.failed_preopen_recovery` only between07:35 and08:40 KST. It holds the native PREOPEN lock, requires today's failed terminal with no live bootstrap, no Main PID and no current-day activated machine policy, and pins the failed status hash. Within that lease `continuous_reversal_policy_v6.stage_code_refresh(..., recover_failed_preopen=True)` and `next_preopen_readiness.prepare(..., recover_failed_preopen=True)` preserve the original source/effective day and policy behavior. Close the complete CAS/strict/controller handoff before releasing the lease, then rerun the native PREOPEN wrapper. Running/succeeded/activated/late recovery cannot use this path. The wrapper must produce its own success; no recovery receipt substitutes for actual Main consumption.

The reviewed registry and tuner live in `src/engine/scalping/reversal_auxiliary_{registry,tuning,intraday}.py`. Register an ASCII prompt file with the registry CLI (`--data-root`, `--arm`, `--prompt-file`, `--hypothesis`, optional `--development-key`). Registration does not activate it. Configure one candidate with the tuner CLI (`--mode configure --candidate HASH --scope SCOPE --seed SEED --max-pairs 50`). The existing operating postclose dispatcher then uses bounded paired preparation/calls/evaluation. Without a tuning configuration its legacy behavior is unchanged.

For a bounded intraday study use tuner `--mode prepare`, `--mode calls`, then `--mode evaluate` with the actual closed `--date`. The shared 100-attempt source-date budget includes failures and uncertain attempts; changing campaign/release/date does not replenish an old request's budget. There is no database copy or full five-arm completion prerequisite. The provider receives only the typed confirmation snapshot, never future labels. New prompt text requires reviewed registration; postclose does not generate it.

From the selected reviewed release, publish the exact evaluation with intraday CLI `--mode publish --evaluation PATH --confirm APPROVED_INTRADAY_AUXILIARY_TUNING` and the current `--expected-parent HASH` if present. The publisher recomputes paired metrics, checks the exact machine parent and current auxiliary binding, and applies only improved scopes. No improvement carries the incumbent. Rollback uses `--mode rollback --expected-parent HASH --reason TEXT` with the same authority; it revokes the defective generation without clearing machine or order dedup state. The actual PID receipt under `data/runtime/mechanistic_entry_policy/auxiliary/consumed` is separate from the publication receipt and from natural AI/order evidence.

The base v5 code pins stay unchanged. A reviewed policy-preserving release handoff allows the new dispatcher/reader to consume the original base bundle, recording both the policy-origin commit and actual PID release. Before editing a strict-bound auto-generated daily checklist, `intraday_release_handoff.preserve_checklist(target_day)` verifies the original prepared/controller/strict binding and saves its exact bytes by SHA256. `--reseal-postclose-source` can use these verified original bytes when they postdate the source Git commit. Arbitrary workspace snapshots cannot substitute for the bound hash. Finish current-owner edits before preparing the new handoff. EOD and completed postclose reports are not regenerated for this code-only transition.

New managed-runtime stage receipts bind `stage_code_root` alongside their original code fingerprint. The existing stage reader checks that exact non-alias managed origin, then all native artifact/input/prerequisite bindings. Legacy receipts first locate the selected root, strict verifier commit or succeeded exact next-session PREOPEN commit through Git worktree metadata; the commit only locates bytes, and the full original fingerprint still must match. Remaining legacy discovery stays bounded to256 origins; release inventory growth cannot skip direct checks or authorize receipt rewrites, deletion or postclose recomputation. Preserve those native origin releases through the last policy/strict consumer.

## Buy Funnel report recovery

The selected release owns `buy-funnel` report generation and its bounded submission-monitor projection. The report exporter serializes native disposition clocks with `datetime.isoformat()`, preserving the supplied timezone and microseconds; it does not replace native attempt identities or rewrite evidence/policy hashes. Unknown object types still fail strict JSON serialization. Validate all JSON/Markdown projections before publication, replace each artifact atomically, and publish the bounded consumer file last. Existing reader permissions are preserved. No trading, provider or threshold authority is created.

For Buy Funnel recurring completion only, the latest exact-date owner DONE closes older FAIL markers. A newer START is in progress; a newer failure or an error after DONE remains a warning. Another owner's DONE and SKIP never prove recovery. Original log failures remain as history and artifact freshness still checks the actual report timestamp. Other recurring jobs and once-only postclose deadline/generation contracts retain their existing checks.

After an approved repair, use the ordinary selected-release cron to prove current-date report publication, bounded-consumer refresh and native DONE. A test or manually generated file alone does not establish cron recovery. Intraday code replacement uses the approved immutable policy-preserving handoff above; preserve original PREOPEN/policy/postclose bytes and distinguish PID consumption from report natural completion.

## Nonfixed observation dispatch readiness

Scanner discovery can run before Main finishes startup reconciliation and subscribes to probe requests. Discovery may continue during that interval, but no physical observation reservation is created until a local request receiver exists. The EventBus counted-publication API reports callback attempts, not WS registration, source readiness, policy/PASS, or order acceptance; the legacy `publish()` API continues to return None.

If the receiver disappears during durable reservation I/O, only zero attempted callbacks permits closing that unstarted reservation as `probe_capacity_deferred`. An attempted callback, including one that raises after starting asynchronous work, does not permit assuming physical cleanup or retrying an uncertain dispatch. Existing physical leases, cleanup acknowledgements, five-worker/item budgets, source freshness, original native deadline and Main/AI/order guards remain unchanged. No manual queue/lease reset or Kiwoom protocol/authentication change is part of this repair.

Verify scanner fetch, exact probe requests/results, subscription/data, native observation, Main admission and order stages separately. Five fixed Main watches do not represent the full rotating discovery population. Lack of ENTER/PASS is not proof of absent observation; lack of results or cleanup progress is not healthy monitoring. After an approved immutable-code restart, use actual PID/root-bound scanner receipts and natural nonfixed WS observations/results to close the repaired path.

For an integrated probe, registration alone cannot select an SOR candle. Await the existing bounded, fresh exact-item 0B/0D source before calling the unchanged shared candle resolver; otherwise an empty initial WS view can select a plain KRX chart that the probe correctly rejects. Keep chart/tick receive-clock and route checks, post-read WS refresh, cleanup ownership and the original native five-second budget. An absent source spends no unbound chart request. The current official Kiwoom revision and inspected spec/core/realtime/Postman paths are recorded in `tmp/nonfixed-dispatch-readiness-repair-20261012/official/revision.json`; request envelopes, parsers, FIDs and REG/REMOVE are unchanged.

## Same-day entry consumer repair and delay-policy custody

`intraday_release_handoff.verify_entry_consumer_code` retains the exact PREOPEN delay policy and already-consumed holding-vote incumbent across an authorized entry repair. It checks the original policy/source binding, Git code generation and current immutable release bytes. During prepare it verifies the live predecessor and its hash-bound manifest/env/PREOPEN consumption; after prepare it requires the native same-day handoff. Missing identity, source, authority or changed bytes fail validation.

The bounded AST exception covers the reviewed WATCHING/entry-arm functions, final machine-input freeze helper (`_final_entry_machine_inputs`) and the corresponding delay/holding compatibility validation functions. Producer, projection, selection and all other function bodies remain identical; the code-generation inventory is unchanged. Holding numeric successors are excluded. Research/publication still require the full current code hash. This preserves policy values and grants no new policy selection or execution authority. PREOPEN/postclose artifacts are not regenerated for a consumer-only repair.

Before restart, require both bootstrap verification and delay preparation from the selected release with the existing exact-date environment. Preserve the compatibility receipt and verify the holding policy loads as the same incumbent. The launcher, auxiliary-reader readiness, new Main PID and heartbeat are separate checks. A successful handoff does not prove live AI acceptance or an order.

The final input freeze retains the original deadline and isolates both caller inputs and callback-returned objects. Only its already-owned graph can skip duplicate copies during canonical revalidation; ordinary callers keep copy isolation. Record copy/refresh/revalidation/feature-build times and signed remaining budget in the existing decision trace. Preserve expired attempts as historical evidence and re-evaluate through the existing fresh-snapshot path. No clock renewal, source-age relaxation or extra provider request is authorized by this optimization.

Early source/preflight and non-entry receipts retain the caller's original async request, producer PID/start, deadline, venue and scanner generation through the same result/trace writer as provider completions. Only these identity fields are copied; arbitrary metadata cannot become a decision. `REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES` admits the exact reviewed engine bytes before an authorized ordered restart. Dependency validation may reuse canonical absolute path strings, but must still stat every source and verify symlink, ancestor, inode and ctime identity at each boundary. Neither optimization renews a deadline, changes signal priority or concurrency, hides a source failure, or proves natural latency acceptance. See the [implementation and deployment review](audits/main-entry-price-progress-deployment-review-2026-10-15.md).

Completed fixed-watch requests retain their original queue identity across session closure or a route/generation change. A known route conflict goes through normal async rejection, original-result disposition and claim cleanup; it cannot terminate the Main loop or fall back to another route. Pending physical work continues draining and cannot be replaced by a new request. Unexpected exceptions still fail visibly. `REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES` binds the reviewed handler bytes, and the affected rising/holding capability generations require fresh isolated fixtures before ordered deployment. Session clocks, order guards, original deadlines and policy values remain unchanged.

## Reviewed nonfixed observation and completion consumption repair

The approved B0–B4 repair uses exact original PREOPEN-to-candidate pairs in `intraday_release_handoff.REVIEWED_NONFIXED_SUBMIT_SOURCES`. The code gate rejects dirty code, changed origins and any further unreviewed bytes. Main keeps the same native signal, original five-second deadline, selected scope, provider options and final quote/account/order/custody guards. Completed fixed-watch requests may advance only an exact generation/cache identity within the remaining WATCHING queue; scanner COMMIT and protected positions retain their existing lanes.

The auxiliary common-support repair is issued by `reversal_auxiliary_intraday.prepare_contract_repair` and `publish_contract_repair`, using `APPROVED_REVIEWED_COMMON_SUPPORT_CONTRACT_REPAIR`. Preparation is read-only. Publication, after the incumbent has drained, uses the existing auxiliary and native publisher locks, parent/pointer/code CAS and a sealed full-scope manifest. Only the exact English ASCII clarification is appended to immutable successor prompts. Validator, projector, input/schema, provider/model/options, machine bundle/family/membership and original PREOPEN/env/manifest bytes remain bound. Issue exact-source reader compatibility from the preserved original readers and complete binding parity before the candidate reads those sources. Preserve confirmation-time selection for historical claims; invalid historical PASS output remains invalid. Rollback restores the prior bindings through the existing owner and retains the repair manifest as historical evidence.

An active machine code handoff freezes original auxiliary generations and their
native lineage, not `auxiliary/current.json`. That alias is owned by the auxiliary
publisher. The origin reader resolves its originally observed physical SHA to
the exact sealed immutable generation before omitting the mutable alias from a
successor receipt. A legacy changed alias requires the native common-support
manifest, full source/code/scope validation, exact parent and old/new bindings,
current native generation and an aware nonfuture publication clock. Unknown,
missing or conflicting originals and unreviewed successors remain failures.
Legacy discovery is bounded to128 generation records and8MiB; new receipts name
their immutable generations directly. Original receipts/bytes are retained.
An old alias observed while checking another day or bundle is custody evidence,
never that day's consumed policy or economic evidence.

For an explicitly authorized repair in an ordered deployment, provide both
`--auxiliary-repair-path` and `--auxiliary-repair-sha256`, with the latter
binding the manifest's actual file bytes. Before acquiring the hold the owner
verifies the native prepared manifest, unchanged parent and original sources,
and all incumbent PID bindings. Until selection changes, preparation, publication
and any preselection rollback run in the original selected release's native
reader. The ordered owner validates that clean issuer, exact reader hashes,
selector and owned drained hold, then independently rereads the issued generation
and its byte hash. Candidate imports cannot impersonate an original policy
reader. After drain it invokes that native publisher;
the selected preparation and native P5 then validate the resulting generation
before launch. Attestation checks the successor PID's complete auxiliary
binding receipt. A preselection failure rolls back a published repair only with
the original selector, owned hold and no live Main; later failures retain their
selected generation and hold for native recovery. No prompt publication is
implicit when the two repair arguments are absent.

Stopped recovery may inherit a repair already issued by the exact failed
transition. It authenticates the original prepared manifest, native overlay,
current pointer, base policy and source bytes, retains the failed transition,
and reuses that generation without another publication or rollback. Final
selected P5 and actual successor PID checks still require its complete bindings.

When an existing sentinel source-window index is bound to a reviewed predecessor
issuer, keep that issuer's exact original bytes in the content-addressed
`data/runtime/sentinel_event_cache/issuers` custody directory. The successor
continues the original writer and independently validates the indexed source;
it does not relabel the existing index with its own code digest. Missing,
writable, linked, changed or unreviewed issuer files fail before cache writes.
Preserve the issuer through the final historical and rollback reader, and
include it in portable provenance while either reader still requires it.

Storage succession composes only the owning preparation registry's already
reviewed predecessor edges into the exact new successor. Both independent and
handoff readers keep their full physical/comparison profiles and original policy
digest checks; a disconnected, unknown or mixed origin remains invalid. This
retains older actually consumed policy issuers without starting intermediate
releases solely to acquire another code receipt.

Raw response evidence is diagnostic, bounded and captured before frozen validation. Receiving a raw PASS, passing the response contract and remaining executable at Main are separate stages. Signature-bound digest reuse skips only previously verified file hashing; semantic/source/identity checks run each time, and prepare/publication force full hashing. Missing or conflicting evidence remains source gap. Code fixtures and PID consumption do not establish natural latency or economics. See the [implementation review](audits/main-nonfixed-submit-bottleneck-implementation-review-2026-10-14.md).

## Ordered intraday deployment

Run the reviewed candidate's CLI with `--workspace /home/ubuntu/KORStockScan --release-root <immutable-candidate> --target-date <current-KST-day> --confirm APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART`. It holds the release-set lock and first verifies the current singleton PID, supervisor, consumed handoff, bootstrap and unchanged source bytes. It creates its own `operator_startup_hold.json` exclusively; an existing operator hold or restart request blocks the transition. The ordinary restart flag requests graceful Main termination. Both the Main PID and its supervisor must exit before selection or document publication. There is no forced termination.

Before preflight or runtime mutation, deployment also acquires the error detector wrapper's existing `tmp/run_error_detection.lock`. It waits at most 60 seconds for an active detector to finish publication and notification while the incumbent Main keeps running. Timeout leaves the selector, checklist, startup hold and Main untouched. Hold this lock through successor PID attestation, and release it on every exit without deleting the lock inode. Scheduled detection yields while the lock is held; an explicit postclose detection attempt returns retry exit 75. The detector revalidates its selected release after acquiring the lock, before rotation or report production, so a delayed old reader cannot publish after the switch. A changed valid selection yields; invalid selection still fails. The next scheduled run performs the full unchanged validation. This serializes observation with the transition rather than accepting an unconsumed handoff or resetting failure history.

The ordered driver preserves the editable shared checklist throughout deployment. After graceful predecessor drain, it selects the candidate under the selection lock and prepares the native `--previous-stopped --freeze-operating-checklist` handoff. The handoff seals a bounded, stable copy as `<commit>.operating-checklist.md`; subsequent launch/consume checks require that immutable snapshot. The original strict-bound historical checklist, original PREOPEN and every policy/source receipt remain independently frozen. It verifies bootstrap and auxiliary compatibility, removes only its own hold, starts the ordinary launcher and verifies the actual successor PID. During stopped preparation, nested policy-code validation accepts only the exact historical predecessor already validated by the native prepare call; it cannot be reused outside that call or while the predecessor is alive.

An already-consumed legacy handoff can use its sealed historical checklist only while its exact consumed PID/start/cwd, selector, manifest, original policy and source hashes still verify. If the incumbent reader rejects a later editable-document change or never-consumed observation tail, the immutable candidate may run the full read-only `--verify-predecessor` check before drain. Exact reviewed source pairs and all native bootstrap/auxiliary validation remain mandatory. Active-policy compatibility also requires the separately issued immutable candidate receipt, its exact incumbent selector/root/commit, current PID and unchanged pointer/source/code hashes; the read-only context cannot escape into ordinary execution. Preserve the old failure log; this result never attests candidate PID consumption. Full postclose research remains strict. A carried stop policy with no selected cells and no consumed vote sources may exclude only complete native holding observations strictly later than its source date; existing consumed inputs, earlier-date rows, replacement, partial rows and unknown files still fail. New watch bindings seal original decoded prefixes; legacy unused prefixes have no historical hash and are not claimed byte-verified. See the [integration review](audits/main-postdeployment-policy-source-binding-repair-2026-10-15.md).

A preserved intraday preparation may carry the original strict checklist bytes in its verified `operating_checklist` launch snapshot. The preparation reader binds that role, target/source date, original strict digest and actual non-symlink bytes before using the existing sealed-generation source check. An edited current checklist cannot replace those bytes. Missing, changed or mismatched snapshots fail closed; full bootstrap and auxiliary verification still run. This does not reseal postclose or grant policy/start authority.

For the first intraday deployment after native PREOPEN, verify the incumbent with `intraday_release_handoff --verify --target-date <day> --pid <live-pid>`. An intraday handoff for that native commit need not exist. The ordered driver seals this actual live verification and exact manifest/env/PREOPEN/prepared hashes into its immutable `native-predecessor.json` before requesting termination. It also preserves the current strict-bound checklist bytes before publication: a PREOPEN-generated dated document may be absent from the original release Git tree. Preparation can use only that exact verified snapshot if Git bytes are absent; missing/corrupt snapshots fail closed. Stopped preparation and successor verification require the same proof path/hash, original selector, PID/start/cwd, date, source generation and original native commit. Missing proof fails closed; no historical intraday consumption is manufactured. Subsequent intraday transitions continue to require the predecessor's actual consumed handoff. Both paths keep graceful stop before selector publication and the normal new-PID/bootstrap checks.

The native readiness/claim delivery and local AI timing repair is admitted by reviewed original-to-candidate file hash pairs in `intraday_release_handoff.REVIEWED_ENTRY_CONSUMER_SOURCES`. The shared-deadline latency repair adds separate exact pairs in `REVIEWED_ENTRY_LATENCY_SOURCES` and `REVIEWED_ENTRY_BOUNDARY_SOURCES`, retaining the predecessor pairs. This includes the actual timeout/failure timing path and cache-clock isolation. The final synchronous provider guard uses a fresh loader-owned immutable view and one signature pass; all existing native/registry/model/revocation checks execute and pointer/path custody is rechecked before the view closes. The pass never spans provider I/O or response/submit validation. Native load, claim and auxiliary timing are children of the aggregate final-guard interval, not additive top-level durations. Source-only capacity request budgets, freshness and required live sizing remain unchanged. The pre-stop candidate check verifies those exact bytes against the original delay-policy code contract; any further source change needs another reviewed pair. This code-only handoff does not alter source/quote age, the original entry deadline, policy membership, provider selection, custody or order guards. See [deployment review](audits/main-native-readiness-deployment-review-2026-10-12.md) and [latency review](audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md). Incumbent bootstrap and candidate delay-code/auxiliary-reader preflight must pass before draining the incumbent; full bootstrap and source-exact checks run again after selection and for the actual successor PID.

The candidate stop-code preflight also runs before drain. An already-approved, unchanged stop incumbent may cross this code-only handoff through `REVIEWED_STOP_CONSUMER_SOURCES` and the same exact-day manifest/native-or-intraday predecessor proof. Validate all stop cells, original policy hash, original implementation digest and every actual source pair; never rewrite the stop bundle/report to match new code. Changed numeric successors and full research/publication verification still require the current implementation hash. Runtime preload and the normal committed-source reader use this same constrained consumer proof. Missing source, authority, date/PID binding or an unreviewed source change blocks startup.

The transition stores its original selector/checklist and phase receipts under `data/runtime/release_transitions/<day>/<candidate-commit>/`. A failed validation never advances to launch. A failed start restores its own startup hold without changing another operator's hold or switching the selector under a possibly live successor. Inspect the recorded phase, current PID and held source generation before recovery; do not delete the hold blindly. Reusing an existing attempt directory is rejected. No monitor cursor reset, alert suppression, policy reselection or expensive postclose regeneration belongs to this workflow.

Historical finalization observation binds the consumed original checklist and all other frozen sources. Its nested delay/holding code-custody check uses the same read-only historical scope, so a subsequent operational document edit cannot silently reintroduce a current-document hash requirement. Public launch, consume and activation verification remain strict. Editing the current checklist still does not grant a new bootstrap or policy authority.

The native entry arm completion repair binds the exact reviewed `sniper_state_handlers.py` source pair in `REVIEWED_NATIVE_ARM_COMPLETION_SOURCES`. Preserve the original native deadline, PASS evidence, reservations and delayed/order/quantity custody. Validate ownership and remove an invalid arm under the same ENTRY_LOCK so a successor cannot be erased. A shared-handler edit also changes the full `rising_missed` and `holding_vote` code generations: review their exact successor hashes, run the network-denied native capability fixtures and verify all four current capability observations before drain; preserve historical native report bytes and status. Verify candidate delay/stop/holding code and issue the active-policy code handoff before drain; ordered deployment then preserves the native policy and attests the actual successor PID. See the [native arm review](audits/main-native-entry-arm-handoff-repair-2026-10-15.md).

The response transport repair uses `REVIEWED_ENTRY_RESPONSE_SOURCES` for its exact reviewed engine bytes. An on-time schema-valid response ends a CLOSED transport failure chain even if subsequent native validation rejects execution or consumes the remaining local budget. Recovery still requires valid execution within the original deadline. A fresh post-response loader boundary preserves source, PID and native signal validation. Changes to the pinned v6 validator require an issued active-policy code handoff and an identical-policy refresh of any already-staged next-session candidate. Preserve the active pointer and policy values; publish the candidate checklist only after graceful drain. See the [response repair review](audits/main-restart-machine-monitoring-and-timeout-structural-repair-review-2026-10-13.md).

For consecutive active-policy code handoffs, preserve the predecessor selector hash as transition provenance. Do not include that mutable selector in the immutable policy-source hash set: selection and PID attestation intentionally replace it. Receipt issuance verifies unchanged predecessor selection, while each consumer independently requires the exact candidate root and commit from the current selector. Keep every other policy source, prior receipt and code hash frozen; selection races or mismatches fail closed. A selected-phase failure keeps startup held. Recovery first verifies that no Main/supervisor exists, preserves failed selector/checklist/phase evidence, restores the verified predecessor sources under the release and detector locks, then uses ordinary bootstrap, launcher and actual-PID attestation. Never force-stop or bypass failed policy validation.

The reviewed REST reduction uses `REVIEWED_REST_REDUCTION_SOURCES` for the exact Main and initial-entry consumer bytes. Optional enrichment, discovery coverage, pre-signal source preparation and initial candle history may be reduced under the approved plan; original entry deadlines, live source clocks, final quote/account/order/quantity checks and custody remain required. Pre-stop delay/stop validation and active/future identical-policy code handoffs still run. If the live checklist alone differs from the incumbent's frozen sources, preserve both versions, verify the incumbent Git checklist against that exact sealed hash, then stage it only under the release-set and detector locks for predecessor validation. Publish the reviewed candidate checklist after graceful drain. Restore the edited version by byte comparison if selection has not advanced; never substitute arbitrary snapshots or ignore another frozen-source mismatch. See the [REST implementation review](audits/main-rest-call-removal-and-reduced-input-implementation-review-2026-10-13.md).


## Intraday diagnostic storage and refresh cadence

The reviewed scoped-scoring successor uses `REVIEWED_SCOPED_SCORING_PROFILE`
and the independent preparation reader's exact source pairs. The complete
generation binds the v6 consumer, cumulative selector and postclose producer;
mixed, dirty, missing or unreviewed dependencies still fail before drain.
Active-policy confirmation parity and the issued native code handoff remain
mandatory. Loading this code does not select a scoring contract. A scoped
request freezes all parent memberships, names only its approved alternatives,
and carries every unscored scope. `prepare-scoring --scope SCOPE --candidate
A09` writes an unapproved preparation only; intake remains explicit and binds
the native source generation, current parent and exact reviewed code.


The source-first successor prepares scoped scoring from the native exact-date
EOD, preflight binding and frozen source manifest before the first machine
stage. An explicitly approved `request-scoring` freezes only the parent map and
allowed alternatives. The existing postclose wrapper calls `fulfill-scoring`
after preflight/resource checks and before machine launch. No matching request
is a no-op. Intake uses the existing publisher and stage-writer CAS; a started
stage, stale source, changed parent/code or conflicting request still fails.
The terminal and stage bind the actual raw/scoped metric and both scoring hashes.
Replay checkpoints include the requested detection memberships. The machine
stage validates its immutable comparison and bound projection after the enabled
auxiliary tuner replaces the separate publication view; changed original
comparisons remain invalid. Keep historical
raw/scoped profiles and receipts for their original consumers. Code deployment
and unchanged-parent P5 do not prove A09 selection, new-policy startup or a full
source-day postclose chain.


The current ordered CLI pins candidate P5; it does not install the optional
selected-validation callback. The approved transition workflow must invoke the
existing `execute(driver, validate_prepared=...)` hook and run native
`main_startup_validation.run_validation` against the final selected/prepared
generation before `start`. A failed selected P5 stops the native transition.
Post-start validation is recovered proof and cannot establish the omitted
pre-start ordering. Preserve the original omission and its later verification.

The observer validates the canonical ordered deployment transition before publication. During selected/prepared/starting it retains the exact frozen predecessor and incident state, skips calculation and notification, and returns deferred (75). The wrapper records DEFERRED without DONE, a cooldown update, or recovery of any earlier failure. A changed or invalid transition cannot publish current evidence. The existing detector allows only the exact captured predecessor through its bounded first scheduled slot; the next ordinary run must bind the attested current PID.

Buy Funnel remains on its existing five-minute cron with the exclusive wrapper flock. Its default completion cooldown is zero: a long run no longer makes the next available scheduled run skip another window. A valid explicit `BUY_FUNNEL_SENTINEL_COOLDOWN_SEC` still overrides the default. The 600-second freshness check, native DONE/failure rules and source-only authority remain unchanged; a genuinely late report still fails freshness.

Repeated entry ADM snapshots retain economic attempt/capsule/hash references after a successful canonical append, rather than repeat both frozen code contexts. Canonical economic events and AI traces keep the replay input; failed/missing append keeps the original snapshot body. Buy Funnel first calculates its economic proof projection, then omits only unused code copies from its cache. Optional streaming cache projection preserves identities, population, source custody, mode and fsync/atomic publication. Malformed/unverified caches remain intact. Maintenance without row materialization records the full census; ordinary report generation still consumes every cached row.

Pre-provider validation can reuse static v6 configuration only for the current loader-owned immutable, configured and consumed view. It rechecks source dependencies, selection, PID/start/cwd, handoff and backend generation and invokes the original fresh native claim/ref/model/auxiliary guards. Cold/unverified/v5 views use the original full validator. No decision or signal result, provider deadline or submit authority is reused.

Prepare the reviewed code-preserving release with these wrapper/consumer contracts and exact source pairs, then use the ordered deployment above. Validate actual successor PID consumption and the next ordinary scheduled report separately from regression or component performance checks. Keep canonical current-policy, custody, rollback and unverified historical source files during cache cleanup.


The sentinel cache reader also shares bounded, short immutable field names and string values within one read. It keeps at most 2048 key strings and 8192 value strings of at most192 characters. Containers, JSON types, field values, row population, cache bytes and raw source remain unchanged; larger/unique values decode normally. This reduces repeated-object memory at some CPU cost. Verify peak RSS, full report completion and freshness under the ordinary scheduled workload; a prefix decoder benchmark is not whole-Main performance evidence.


## Pending source-first scoring requests

An approved source-first scoring intent is a pending policy consumer. The
ordered deployment preflight checks its exact code profile before a startup
hold or drain, and every pre-publication CAS includes its presence and byte
identity. Scoring registration shares the release-set lock and rechecks the
selected origin before publishing. A request created during an older writer's
transition remains detectable by the CAS; unknown or changed code is rejected.

The existing cumulative registration owner's `handoff_scoring_intent` may
transfer the same approved recipe to an already selected, reviewed immutable
code generation before its source machine stage starts. It independently reads
the original and selected code, verifies both against Git, attests the unchanged
active parent and all frozen memberships, and requires a review bound to the
exact source and target profiles. Preserve the original intent and review in
content-addressed evidence before native publisher/stage CAS publication.
Dates, score specification, candidate scopes, memberships and authority cannot
change. The operational writer binds the selected consumer's profile, never its
own newer source. A materialized scoring contract or started stage prohibits
this transfer. Registration, source fulfillment, policy selection and actual
Main consumption remain separate; the handoff starts no Main or order.

Deployment distinguishes pending approval from exact native materialization.
A same-date materialization must retain every approval field and bind the
original intent's raw bytes in its native content-addressed evidence archive.
Both live intent and materialization bytes remain in every deployment CAS.
Missing, conflicting, corrupt or foreign evidence fails closed; an unmaterialized
current/future approval still requires its exact consumer code. This custody
classification proves neither source validity nor completed machine calculation
or Main consumption, and does not permit rewriting the original approval.

For a stopped next-session code change, inventory every family consumer against
the predecessor's verified preparation before selector publication or source
regeneration. Issue changed prepared-policy code contracts through the existing
`prepared_policy_code_handoff.issue` owner while its original controller,
summary, policy and verification bytes still authenticate. An active Main code
handoff and candidate P5 do not replace this family custody. Exercise the actual
source-date strict/controller reader too: it may consume a next-session policy
before that session's live bootstrap exists. Missing proof stops the first write.

After an origin was already invalidated, preserve it and the failed attempt.
Use the affected native producer's verified sealed qualification/cache path to
republish only that family, then compare its source, dates and numerical policy
payload with the original. Rebuild its dependent summary/strict/controller and
preparation, followed by selected P5. Do not reconstruct an origin receipt,
manufacture a live bootstrap, relax code checks or repeat the whole wrapper.

## Observer verification and Sentinel I/O custody

The approved I/O release uses `REVIEWED_IO_OBSERVER_SOURCES` for the exact original-to-reviewed bootstrap bytes. Only the historical health observer context enables process-local successful delay-generation reuse. Public preparation, startup, policy publication and live guards retain native full verification. Inventory signatures include source/code/date/pointer and canonical evidence shards; noncanonical trees remain fully verified. One in-flight observer validates a generation, failures remain failures during finite retry backoff, and no old success may authorize a changed generation.

Sentinel retains the native raw/cache population and cadence. Its optional SQLite index commits position, compressed payload, metadata and cursor together. Only complete newly appended cache rows are indexed. Bounded lazy field reads and lossless equality avoid holding all decoded evidence in memory. A full native aggregate is reused only for the same ordered row/summary/code/window identity. Changed populations use the original aggregation. Small source-bound summary projections are opt-in for Sentinel; native policy/source verifiers remain unchanged. Failed optional index builds cannot publish DONE and resume from the sealed native cache; an unsealed canonical cache mismatch preserves evidence and fails. Cache generation signatures inherit the native append-writer contract and do not claim cryptographic detection of arbitrary simultaneous prefix rewrite plus append.

The existing workspace-owned one-minute system sampler records physical block devices without partition duplication, per-PID birth/owner/I/O, swap and PSI. Missing identity/counters are unobserved. Serialize the entire sample to keep interval state consistent. Publish its reviewed workspace file only after validation, recording its hash separately from selected-release/PID consumption. No cron interval, alert threshold, package, order guard or trading priority is changed. Large development benchmarks run sequentially at low priority. The implementation evidence and natural-acceptance boundaries are in the [I/O review](audits/main-io-contention-and-repeated-validation-implementation-review-2026-10-13.md).


## Scoped recovery from initial quantity

After explicit recovery authorization, `deploy/run_threshold_cycle_postclose.sh SOURCE_DATE --resume-from-initial-quantity` resumes only a native `initial_quantity_policy` command failure. It verifies the original run metrics, completed artifact reuse receipts and byte hashes, unchanged aftermarket contracts, exact EOD/preflight and successful machine/delay/label stages before START. It preserves the failed attempt and binds a scoped resume receipt. This path skips the completed prefix and bot actions, then executes the failed quantity stage and ordinary downstream consumers. The existing two-slot heavy admission is retained with the dispatcher four-hour admission deadline. Joint initial registration binds its real machine/auxiliary, operator request and frozen sources; it does not require legacy research/call ledgers or additional economics for initial designation. Strict/controller closure, future PREOPEN/PID and economics remain separate.

Direct postclose recovery and standalone semantic/health checks read the same attested `native_owner_custody.env` assignments through `native_custody_environment` as the release router. It never executes or edits that file. `--resume-from-final-handoff` accepts only a native tower command failure following a verified initial-quantity resume. It validates completed native metrics, the previous resume proof, every active analysis stage, the exit snapshot and quantity terminal before START. It preserves those calculations and bot custody, regenerates the affected runtime summary, then runs tower/checklist/strict and normal terminal publication. Source/publication dates remain explicit; missing or changed evidence refuses the resume.

The final handoff boundary accepts the full native strict verifier failure (exit 1) only with its immutable UUID attempt, exact source date/run/code, full preterminal or main-precommit invocation and original first-failure binding. Scoped summary exit 2 is not a full-verifier failure. It verifies bounded, hashed ancestry of earlier scoped resumes without relabelling their command identities. When a pretty entry-split report exceeds its unchanged 512 MiB native read bound, the publication adapter can remove formatting whitespace only. It validates the entire compacted report against the existing native report/policy generation, preserves original bytes and policy bytes, and updates the byte reuse receipt. Ordinary entry-split publication uses the same adapter before downstream readers. A changed generation, oversized physical line, concurrent source change or still oversized compacted report is refused; no event, field or policy value is dropped.

Checklist strict verifies every expected native task ID and every generated task, including holding/source repair owners without the DirectFamily prefix. It retains unrelated manual owners outside that projection and still rejects duplicate, missing, unexpected generated or unowned DirectFamily tasks. An OPEN holding/source repair is preserved rather than deleted to obtain a PASS.


## Explicit validation digest sessions

The reviewed I/O repair retains every native semantic, source, custody, policy, selector and PID check. Bootstrap and intraday handoff CLIs accept an internal `--validation-session` namespace only for verification/consumption or existing preparation, never policy activation/bootstrap creation. Ordered deployment supplies an opaque identifier to candidate calls and the actual tmux launcher child. The launcher unsets the inherited identifier before starting Main and passes it explicitly to its native verification commands. Standalone CLI calls without the flag and old predecessors/origin subprocesses retain full verification.

The session shares only actual large-file SHA-256 values, scoped by local data root, boot/day, validator code root/hash, transition identifier and prestart or exact post-launch PID/start/cwd. It uses a separate private `data/runtime/validation_digests/transition` store with120-second file-digest lifetimes. New source metadata, PID or code identities invalidate reuse; all small-file reads, expected hash comparisons, independent driver attestation and native output publication still execute. Metadata reuse relies on trusted local writers, as the existing in-process hash cache does; it is not an administrator-tamper proof or cached native PASS. Observer storage is never a transition proof. Storage faults use full verification, contention fails the attempt, and existing phase deadlines still bound each command.

`REVIEWED_IO_DIGEST_SOURCES` pins exact original-to-reviewed bootstrap/monitor consumer bytes without changing the original policy. This does not replace active-policy code handoff issuance, future identical-policy refresh, source resealing or actual-PID acceptance. The current stopped Main selection remains stopped during implementation. See the [implementation review](audits/main-io-residual-implementation-review-2026-10-14.md).

For an explicitly authorized start after a non-starting release selection, keep the latest selected release and last actually consumed Main release as separate identities. The live-predecessor ordered driver is not applicable while Main is absent. Under the same release-set and detector locks, preserve both selectors and checklist generations, verify no Main/supervisor or unrelated startup hold, and use the existing native `--previous-stopped` preparation against the last exact-day consumed handoff. Freeze original policy/PREOPEN/prepared bytes, validate reviewed candidate source deltas, and bind the new selector to that actual predecessor; preserve the intervening selected release separately as source/deployment provenance. Publish only reviewed merged documentation, then perform native bootstrap, auxiliary readiness, ordinary launcher and independent exact-PID verification. Failed preparation keeps the owned startup hold; never fabricate a historical consumption receipt.

The pre-selection code gate also verifies the exact holding-vote incumbent bundle, original PREOPEN code pin and reviewed holding-generation source pair. Run `verify_candidate_holding_vote_code` alongside delay/stop preflight before any graceful drain or stopped selector publication. This admits only unchanged incumbent carry; numeric successors and source validation retain their native current-code requirements.

The driver must remove its byte-verified owned startup hold before calling the ordinary router's `make_plan`, because that router rejects all startup holds. Keep the release-set lock across this boundary. Validate the actual launcher command before launching; the existing failure handler restores only the same owned hold on planning/launch failure. Never add a general hold bypass to the router. Regression must exercise the real router, not only a mocked launch plan.

Historical unarmed holding-generation rebinding receipts retain their original report/contract/code identity after a code deployment. Read them with exact source and authority checks and keep them unverified for current code; never attach a current fixture receipt or rewrite the historical report. New rebinding publication still requires the current numeric code hash and all unarmed, source-only restrictions.

## Entry-split verification projection and native-ready delivery

Entry-split publication retains its native full report/policy generation and emits a bounded report-only projection, validation receipt, and final atomic manifest in the existing family directory. The Sentinel reader reuses the producer's full-validation receipt only for the same source identities, date, generation and validator contract. Missing, changed or invalid metadata remains unobservable/partial; an active bootstrap cannot hide that state. The monitor never performs a cold full-report parse. Runtime approval summary retains its independent full byte hash at its one-shot postclose boundary; that cost is not a warm monitor saving. Native policy loading and economic/selection authority are unchanged.

Legacy over-limit report verification uses only the explicit bounded migration CLI in `src.engine.scalping.entry_split_monitor_projection`; it creates a value-preserving temporary whitespace-compacted copy without modifying original report, policy or immutable paths. The migration must finish native verification of both aliases/snapshots before publishing a receipt. Record resource use and keep source gaps or invalid generations. It is not report research regeneration or policy promotion, and it does not run inside Main or the monitor loop.

The Main delivery repair keeps wake hints until an actual target visit acknowledges the matching token. A new eligible hint after a WATCHING target's visit may re-enter at most once in the same outer pass, preserving protected positions, mixed-target fairness and the original native claim/deadline. Existing bounded diagnostics carry Main phases and exact transport remaining/reserve/SDK settlement without additional per-tick I/O. Release preparation uses exact reviewed PREOPEN-to-candidate source pairs and the existing policy-preserving ordered transition; source-only verification cannot reset a deadline or authorize an additional call/order. See the [implementation review](audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md).

The entry-execution observer resolves the trusted data mount once at its consumer boundary before deriving family/date source paths. This accepts routed `release/data` mounts while preserving all below-root symlink, exact canonical source, receipt and policy checks. A component fixture using only canonical paths does not close routed-consumer acceptance; retain the release-style mount regression and a subsequent scheduled report.

기동 직후 full health sweep은 선택된 immutable router가 기존 launcher의 마지막 위치에서 기록한 자기 PID/start/cwd·commit/root·당일 bootstrap 및 필요한 consumed receipt를 먼저 확인한다. Main 시작과 별개인 이 감시 장벽은 원 시작부터150초로 제한되며 heartbeat를 유지하고, timeout/잘못된 세대는 실제 실패를 보고한다. ordered publication은 정확한 dated observer predecessor bytes 신원을 기록하고, 새 observer는 run/selection/code/PID generation을 봉인한다. 과거 partial의 pending은 이 증거와 다음 정상5분 slot+180초에만 한정하며 stale/실패/현재 partial은 유지한다. 기술 수용은 경제성·전체 원천 완전성 또는 새 주문의 입증이 아니다.

이번 ordered transition으로 기동한 첫 PID는 final record-pid에 더해 동일 transition의 complete/pass·successor identity를 확인한 뒤 첫 full sweep을 시작한다. 이후 같은 릴리스의 검증된 재기동/다음 날짜 native PREOPEN을 과거 successor PID로 제한하지 않는다. 첫 대기 한도는 원 프로세스 시작부터150초로 유지한다.

Selected router를 직접 실행하는 final record-pid의 `--workspace`는 해당 record-only 명령에만 허용한다. 실행 파일·선택 release·canonical 공유 workspace와 기존 PID/source guard를 검증하고 실제 -I subprocess 시험을 통과해야 한다. 실패 기동의 native 소비 메타데이터 복구는 ordered 완료를 뜻하지 않는다. 새 배포의 명시적 failed-hold adoption만 정확한 canonical starting/attestation-timeout 실패·소유/bytes·native/source 검증 뒤 기존 hold를 새 owned hold로 CAS 교체할 수 있으며, 원 terminal과 old hold 사본은 보존한다.

Submission observer health diagnostics retain independent report freshness, exact observer generation, semantic state and original source blocker. A partial report must not hide stale or noncurrent evidence. The same bounded report snapshot supplies status and source details; `source_as_of` retained from an earlier accepted snapshot is not the current upstream clock. Ordinary600-second stale and actual-defect partial failures remain; only the operator-authorized pending exceptions below change diagnostic severity. Empty evaluation populations do not prove valid-empty source coverage or recovery. Release-cold digest reads and later natural warm reuse are measured separately.

The operator-authorized observer handoff allowance applies only to the exact frozen predecessor that was fresh at ordered completion, through the next scheduled five-minute slot plus the existing180-second wrapper limit. Retain its current stale age and prior partial state; this is warning/pending, never validation or recovery. Already-stale predecessors, failed producers, changed identity or expired deadlines remain failures. A current report can separately declare strictly recomputed observation-pending when source readers and native contracts succeeded and the cohort is empty or consists of exactly bound guard outcomes, valid CAUTION/VETO, or PASS with exact Main rejection or processing closure. Unknown PASS consumption, failed/conflicting submission, actual contract errors, reader/production failure, generation or stale failures remain errors. Current health uses the same single-clock 600-second window and current PID/start across machine, lineage and Main evidence; original 30-minute/all-PID populations and historical unresolved/failure evidence remain separate and unchanged. Observation-pending retains source gaps and partial/unobservable status; it is never validation, recovery, policy or order authority.

The composed source repair changes only reversal_extended_state.State._source for joint definitions. Validate the retained original confirmation and top/base DD-volume equality, then align only those two source facts; retain rolling refinement features and strict validators. A native code handoff must bind that exact old/new module and fresh baseline/candidate128-scope signal parity, all other native module bytes, frozen policy definition/membership/pointer and targeted evidence. It grants no policy reselection or additional execution authority.

The startup barrier retries only a receipt changed during its bounded read as pending within the original process-start150second deadline. Polling never renews the deadline. Persistent read races time out; malformed, symlink, wrong identity/generation, explicit failed receipts and source provenance remain failures. This preserves ordered completion and current PID consumption before the first full sweep and does not change observer grace or policy authority.

Current observer health separately proves the exact live actor lifetime within the600second bound. A conservative verified native birth lower bound can exclude only provably prelaunch rows and establish required read coverage since launch; preserve the original ten-minute/all-PID partial and history. Unknown postlaunch actors, incomplete current coverage and invalid receipts remain failures. Exact fail-closed source warmup/no-tick guards and natively verified confirmation pending may be observation WARNING with original UNKNOWN/censored/source gaps, never PASS, no-match or policy/economic approval.

Native history lifecycle counts outlive the current continuous segment. A finite zero-duration segment may verify history only with exact native identity and positive known lifecycle counts; current no-match/pending still require their original positive interval. History never proves current source coverage, admission or no-match, and stale/censored diagnostics remain visible. Probe census and diagnostics share native PID/symbol/route/physical-lease identity, retaining the original timestamp/result/reason fallback for legacy rows.

Final observer health separates a valid report execution from bounded source and outcome verification. A second bounded_source_quality_observation WARNING requires exact fresh current publication, live actor/native birth, valid input clocks/schema/counts/policy/native proofs, clean complete or explicitly bounded-tail readers, and no current stage issues. Preserve partial/uncovered/source gaps, invalid/timeout and unverified PASS/Main consumption; never claim full validation, recovery or execution authority. Hard reader/identity/policy/schema errors and actual current contract issues remain failures. This supersedes treating those bounded unverified outcomes alone as an artifact production failure.

Incident classification completes the existing bounded256-item scan even after an actionable incident. This keeps exact old-PID evidence classification independent of dictionary order while retaining the failure flag. The warning-only quality path still requires native historical identity/hash/birth proofs and exactly derived route coverage; unknown/current incidents and altered evidence remain failures. Reviewed source successors use exact origin/candidate hashes under the existing pre-drain gate. See the [incident-order repair](audits/postclose-root-cause-recovery-review-2026-10-19.md#submission-observer-incident-order-repair).

The reviewed product-intake successor binds the shared pure-equity name predicate and its prefetch/restored-queue consumers as one exact dependency generation. Preserve issued predecessor profiles, queue history and ordinary-equity eligibility; reject missing, dirty or independently changed helper/consumer bytes before drain. ETF exclusion does not change quote freshness, WS/request contracts, price/quantity/account/order guards or retired custody. See the [integration review](audits/postclose-root-cause-recovery-review-2026-10-19.md#etf-product-intake-integration).

Before draining after any report CODE_PATHS dependency changes, verify the candidate's native bounded report currentness using the source date from its verified prepared receipt. A shared kiwoom_utils change invalidates the all-scope trailing report fingerprint even when numeric policy modules and capability generations are unchanged. Missing currentness leaves the incumbent running; use the existing bounded main_trailing_source_reuse preflight/write and independent issuer for only that source/target generation. Preserve original PREOPEN/holding/policy bytes and failures. A deferred health publication does not close the completed-full-consumer check.

The observer computes observation_health only from the final publication dictionary after notifications and the final generation recheck, immediately before writing state/latest/dated files. Producer declaration must equal consumer recomputation. A selection/code generation change refuses publication. Integration coverage executes main parser/stage/notify/final-seal/publication, including a changed second completion clock and canonical fixed_watch_post_receipt_warmup evidence. This does not alter policies, native kernels or trade authority.

### 원천 커버리지 품질 집계와 보고서 건강

The FIRST cancellation successor binds the rejected probe reference producer and observer reader as one exact reviewed group, retaining the issued predecessor generation. Consume an original native ready selection for an issued empty reference only with exact root, actor, scope, sequence, source and deadline agreement. Verified cancellation is diagnostic; recompute remaining route coverage over its eligible population and retain low coverage and unknown/current loss. Candidate P5 includes the independent Main preparation inventory; the unchanged ordered execute sequence and failure paths must pass offline before drain. Native expiry diagnostics and closed-PASS endings share the same verified terminal set; malformed, unexpired or conflicting rejection evidence remains actionable. A later reviewed observer generation retains the consumed FIRST group and requires fresh native handoff/P5 before its ordered transition.

알려진 route별 원 건수/유효 원천 건수와 원 coverage floor에서 정확히 재계산한 coverage_degraded issue/scope는 source quality 경고로 보존한다. 유효 보고서의 제한 관측 건강을 이 집계만으로 장애로 분류하지 않는다. 원 partial·domain 알림·AI/Main 미검증·거래 guard는 유지하며 타입/route/집계 불일치나 다른 계약/읽기 오류는 실패다. 실제 정규 run/hash와 그 보고서를 읽은 daemon에서 별도 수용한다.

### 전체 관측과 Main provider 적격 모집단

보고서 건강은 native 검증된 전체 관측의 역할별 건수/원 해시 분할을 확인하고, Main provider 계보는 main_live/unspecified_legacy 적격 집합과만 정확히 대사한다. probe/CF의 provider/주문 금지와 원 역할을 보존한다. 분할 합계·해시·actor·bundle·소속이 다르거나 과거 원 분할 증빙이 없으면 성공 처리하지 않는다. 매매 정책/native 정의·주문 권한은 변경하지 않는다.

### Native 완료 prefix와 승인된 보조 집합의 복구

`--resume-from-final-handoff`는 native tower/strict 실패를 최소 재개한다. 이전 scoped ancestry 또는 `normal` 원 run의 실제 완료 command receipts가 있어야 하며, 다른 regeneration/reuse·누락/변조 prefix·source/commit 불일치를 거부한다. 모든 stage·exit snapshot·수량 terminal 검증 후 summary→tower→checklist→strict→controller를 갱신한다. 이전 실행/원천/실패는 보존하며 이전 scoped 복구를 합성하지 않는다. 보조 준비의 집합 차이는 검증된 parent에서 native 승인 selector의 manifest/cells/선정 영수증을 정확히 재현하는 경우만 허용한다. 새 scope/variant·예산 reset·live current 변경 권한은 없다. [구현 검증](audits/postclose-auxiliary-membership-and-final-resume-recovery-review-2026-10-14.md)을 따른다.

Next-session 발행이 승인된 active parent의 native v4 조상을 상속할 때는 현재 code handoff를 검증한 뒤 기존 불변 metadata refresh builder를 사용한다. behavioral payload equality·native source 재검증과 원 parent/승인 receipt SHA를 보존한다. source/code 전환은 새 scope/가드/활성화 권한이 아니며 intraday 경로에는 적용하지 않는다. native 계약 파일 변경은 fresh parity와 영향받은 producer code identity로 재생성한다.

### 자정 이후 장후 source 인계와 과거 관측

명시한 이전 source date의 Main terminal이 succeeded인 경우, 종료된 장중 observer는 최대16개 보존 selector 중 원 generation SHA·release/코드·run/date seal이 일치하는 원 영수증으로만 감사한다. 과거 partial/source gap은 경고로 보존하며 current generation/coverage/PID 소비를 인정하지 않는다. 장중 현재 selector/코드 검증과 손상·누락의 실패는 유지한다.

이미 발행된 code-refresh candidate가 당일 code-handoff 만료 후 동일 active parent의 원 release를 증명하는 경우, 발행 origin 검증은 그 불변 generation·전체 source 검증·원 parent CAS를 사용한다. 새 code refresh는 명시한 source/publication의 다음 거래일인 당일07:30 전, PREOPEN status와 live bootstrap JSON/env/verify가 모두 없는 경우에만 허용한다. 날짜·payload·집합·budget·current pointer는 보존하며 bootstrap 시작 후 변경이나 후보 재선정·실행 권한을 만들지 않는다. [장후 복구 리뷰](audits/postclose-auxiliary-membership-and-final-resume-recovery-review-2026-10-14.md)를 따른다.

A Friday completed calculation may need a code-only detector repair after midnight. The existing `reversal_code_handoff` midnight owner requires the original source-day EOD and exact selected workflow, plus current whole-chain controller/strict verification and immutable attempt hashes, before issuing compatibility for the unchanged active parent. It preserves the original source date and next trading date; running or invalid completion, changed ancestry, live Main, startup holds and restart requests remain rejected. EOD local timestamps follow their native KST producer contract; observer and selector clocks remain offset-aware. Historical retained observations cannot establish current coverage or PID consumption.

### Finalization preparation budget

`run_postclose_finalization.sh` gives native next-session preparation its own positive integer `POSTCLOSE_FINALIZATION_PREPARE_TIMEOUT_SEC`, default600 seconds. Normal scheduled execution remains capped by the existing finalization finish-by cutoff and retains the10-second kill grace. A preparation failure records its actual child exit code, runs the existing detector path and exits1; it cannot emit DONE. This maintenance budget does not change trading/AI or Sentinel report deadlines. See [10/15 repair evidence](audits/morning-finalization-preparation-and-generation-warning-repair-2026-10-15.md).

A previous PID delay/bootstrap receipt incident remains historical_unresolved in the immutable observation history. The current health projection may exclude only the two exact pre-submit-delay handoff/env mismatches when its last observation predates the verified current PID birth and the current bootstrap/PID, split native projection, delay policy hash and environment all independently verify. Current-PID incidents, unknown reasons and incomplete native proof remain errors. This grants bounded observation-pending only, not source repair or trade/economic acceptance.

Price-progress code deployments preserve the existing next-session cumulative registration and active membership. The native diagnostics project cumulative hold anchors and same-row price features; positive raw ready counts are distinct from selected ready only with exact native scope/readiness binding. Auxiliary capability generations include the cumulative producers and consumers, and changed generations require fresh isolated fixtures. Preserve original postclose reports and exact PREOPEN/code handoffs, then verify ordered PID consumption and the next scheduled observer/detector. See the [deployment review](audits/main-entry-price-progress-deployment-review-2026-10-15.md).

The reviewed nonfixed source-continuity consumer transfer preserves the original native five-second clock and exact lease/PID/transport identity. Its exact PREOPEN-origin source pairs are admitted only by the unchanged ordered pre-drain validators. REG/REMOVE local-send receipts and server-response evidence remain separate; ambiguous responses cannot approve a symbol or erase another owner. Publish the current startup observer after exact-PID attestation and before the full health sweep. See [implementation review](audits/nonfixed-source-continuity-review-2026-10-16.md).

Code-handoff review and test evidence must be frozen in a dedicated immutable run directory before issuing the receipt. Never bind an editable worktree review/checklist as validation evidence. If an existing receipt already references such a path, keep its exact bytes for the full ancestry/rollback lifetime and write every follow-up into a separate file; even a temporary edit followed by restoration can invalidate live AI evaluation. Verify all referenced hashes before transition and before any evidence maintenance. Source/code references remain the exact committed immutable release, and original failures must remain auditable.


## Snapshot cron release binding

The three intraday snapshot tags `RUN_MONITOR_SNAPSHOT_INTRADAY_INC_09`, `RUN_MONITOR_SNAPSHOT_INTRADAY_INC_10_11` and `RUN_MONITOR_SNAPSHOT_1200` use the canonical `run_runtime_release.sh monitor-snapshot <KST-date>` bootstrap inside their existing owned-log wrapper. The bootstrap validates the current selector and pins its child environment and working directory before invoking the selected release's `run_monitor_snapshot_incremental_cron.sh`. That wrapper, its safe wrapper, Python producers and asynchronous child use the same selected root. The immutable trading release and its policy/PREOPEN receipts are not rewritten for this bootstrap repair.

Keep schedules, noon jitter override, target date, profile, lock and completion paths unchanged. The installed snapshot group must contain each tag exactly once; partial groups, duplicate tags, deceptive shell commands and unexpected arguments fail closed. The existing eight mandatory Main/postclose routes remain separately validated. Apply a reviewed migration through `run_runtime_release.sh --install-cron`, preserve the backup and verify readback; do not run a broad installer to repair only these three rows. `install_stage2_ops_cron.sh` emits the same routes for future installs.

Snapshot completion publication uses the selected producer's temporary-file flush/fsync and atomic replacement. A dispatched async process or wrapper DONE is not a successful terminal: verify its selected code root, worker outcome and complete new receipt. Preserve prior and failed receipts. Verify failed workers do not advance success cooldown, and concurrent readers see a whole old or whole new JSON generation. Sunday/manual verification does not prove the next regular session's natural report or Main policy consumption.

A stopped failed transition at `starting/deployment_pid_attestation_timeout` may use the same embedding-only `StoppedDeploymentRecovery` owner as the existing selected-phase validation failure. Require the exact original selection and consumed predecessor, no Main/supervisor/restart flag, unchanged original policy/PREOPEN sources, a new clean reviewed candidate and all four native code checks. Preserve the failed transition and original owned hold; transfer it with CAS only after preflight. Other phase/error combinations remain invalid. Evidence-only snapshot ctime changes require complete originally sealed byte/hash verification with unchanged device/inode/size/mtime; they never permit rewritten content, replacement or a policy update.

Main runtime orchestration may retry its first `machine_policy_consumer_source_changed` once when launcher PID attestation races first consumption. It discards configuration/consumption state and executes the entire native reader again. It never retries inside an already-open evaluation view; source hash, pointer and dependency failures and a second source change remain failures. This is not a cached verdict, changed signal deadline or policy apply permission.


P5가 장중 `intraday_preserved_historical_generation`을 검증할 때 auxiliary transition manifest가 없는 실제 경로는 같은 호출에서 full read-only bootstrap과 이미 소비된 인계 영수증을 확인한 typed preserved closure로 결속한다. source/target·선택 code·정책·준비본·원천 hash가 필수이며 빈 manifest/기존 PASS는 대체 증거가 아니다. 현재/full auxiliary 경로는 기존 manifest·frozen 검증을 유지한다. parent와 격리 child가 같은 source CAS를 검증하고 candidate12consumer·child 종료·부작용0을 확인하기 전에는 incumbent을 정지하지 않는다. [통합 검토](audits/postclose-root-cause-recovery-review-2026-10-19.md#0255cb05f-integration-and-actual-preserved-p5-closure).

P5 historical vote source checks use the existing bounded canonical JSONL reader inside the authenticated isolated validation context. Ordinary runtime and research retain their indexed reader. This avoids opening the live SQLite index inside the child without permitting database access or reusing a semantic verdict; date/root, original raw limits, full native generation equality and source-change rejection remain mandatory.


After a source-reader change, validate the selected buy-funnel sentinel producer before claiming current observer coverage. Native summary migration accepts only its reviewed exact parser/callback successor; projection-read reuse alone preserves parser semantics but still requires the explicit successor pin. Preserve the native predecessor archive and append cursor, then regenerate sentinel and current observer before the full health sweep. A current observer generation without a valid sentinel is not completion.

The original missing-BUY report-only successor binds the exact holding semantic source hash as one complete integration dependency profile. Earlier issued profiles remain independently checkable. A predecessor may omit this selector only when its committed tree also predates that file; removing a file owned by the candidate tree remains a hard failure. Native current-generation fixtures, exact active policy parity and P5 remain mandatory before the ordered transition. Incident deduplication does not repair historical source loss or grant runtime/economic acceptance.


Before either a normal ordered drain or stopped-transition hold transfer, the existing ordered deployment owner verifies both trailing currentness and the initial-quantity bounded contract using the exact source date from the prepared receipt. A changed dependency in initial_quantity_monitor_projection invalidates its proof even when the original stage, policy and economics are unchanged. Preserve the old proof and use that existing publisher for full native stage/policy/timeout/census revalidation, retaining the original historical-exclusion acknowledgement. Economic gaps stay visible and do not block this code-currentness handoff. The checker never regenerates or substitutes hashes automatically. See the [final integration review](audits/postclose-root-cause-recovery-review-2026-10-19.md#delay-v4-and-retired-pyramid-final-integration-2026-10-20).


When a reviewed cleanup or delay-registry change alters rising/auxiliary/holding capability fingerprints, fresh fixture publication must be consumed through the existing exact policy_generation_code_handoff pairs as well. Preserve every historical pair and historical fixture; require the exact original report/source/date/state plus the independent current fixture. Current code capability never repairs historical sources or grants policy/economic authority. Check the actual post-start regular consumer, not fixture exit0 alone. See the [final capability review](audits/postclose-root-cause-recovery-review-2026-10-19.md#final-current-capability-successor-closure-2026-10-20).


The reviewed 2026-10-20 local completion and role-model candidate uses the existing intraday handoff owner's exact dependency group. Delay/stop/holding verification binds the entire new group and predecessor dependencies before any drain; a partially reverted selector, missing source or changed Git object remains invalid. Role configuration and compact fixed-model identity are code compatibility only, with unchanged provider/prompt/budget/guard authority. Candidate preparation does not select it or restart Main; native parity, active-policy handoff, current report contracts and isolated load-and-exit validation precede a separately authorized ordered transition. Historical reports/checklists/receipts retain their original bytes. See the [review and replacement disposition](audits/postclose-root-cause-recovery-review-2026-10-19.md#local-completion-latency-and-role-model-integration-2026-10-20).

Interrupted-process custody verifies the main-loop, worker and collector clocks independently within the authenticated consumption lifetime. Independent heartbeat writers have no relative clock ordering. Keep absent-process, PID/start/cwd, unchanged handoff/bootstrap and final source-byte checks; interrupted custody does not verify source admission, normal terminal or new PID consumption.

A normally stopped, already consumed Main may be inspected through `closed_consumption_observation`: the exact selected consumed PID/start/cwd must be absent, process inventory must be known empty, and native market-close/zero-unresolved, same-day postclose isolation, EOD completion and all original frozen sources must agree. This is historical consumption evidence; it cannot claim current observation or a new PID. Diagnostic stop/observer/checklist readers use this bounded scope. A clean candidate may use it for full native predecessor and isolated P5 validation before an authorized ordered restart. The ordered driver retains every policy/code/currentness gate, records the already-stopped basis, then uses ordinary prepare/start/actual-new-PID attestation. No artificial live predecessor or manual startup-hold removal is allowed.

After the observer window closes, an unchanged quiet bounded-empty publication remains a warning only while its exact actor, terminal window and source generation verify; a normally stopped actor additionally needs the native closed-consumption proof above. New loss, invalid provenance, mixed generation and incomplete execution remain failures. An unstarted reversal stage is pending only while the same-date native postclose parent, actual process and nonterminal cron agree before the existing23:20 deadline. The quantity monitor cold publisher binds logical snapshot SHA/size and original identity once; a later native sealed gzip transformation may satisfy that exact logical dependency without repeated warm full scans. Unrelated source/cost/lifecycle mutations remain invalid.

Quantity timeout replay must keep the original logical pipeline source receipt across a verified native gzip archive. The quantity producer reuses the existing native raw archive seal reader and checks the complete compressed epoch before preserving logical path/size/SHA; cache/proof fingerprints include that reused reader. A physical gzip alias must not become a new timeout input. Preserve old report/timeout bytes; revalidate through the existing publisher after only the affected source-date feature caches are rebuilt. Changed bytes, invalid seal/ctime or unknown custody remain failures. Concurrent deployment sessions must settle on one final selector/restart owner before shared proof publication or ordered runtime mutation.

### Closed-date source diagnostic resolution

An explicitly authorized historical source repair uses the existing holding Sentinel producer's `publish_historical_buy_resolution`, followed by its native warm reader. Preserve original report bytes and require exact closed date, complete ID/reason/hash population, native original-cutoff re-audit, durable BUY receipt restoration and later complete collection evidence. Archived policy and PID validation are diagnostic-only; current-day runtime policy/PREOPEN guards remain unchanged. The immutable companion is keyed by original report, current code and source inventory; a new or invalid binding remains actionable. Quantity uses its existing native monitor publisher and exact historical exclusion disposition after full producer/census validation. Recovery evidence, original excluded/null economics, deployment, current PID and next natural window remain separate. See the [owning review](audits/postclose-root-cause-recovery-review-2026-10-19.md#historical-source-resolution-and-authorized-release--2026-10-21).

Before candidate report-currentness validation, the existing initial-quantity native publisher may prepare `publish_current=False`. It performs the full unchanged semantic/source validation and writes the exact code-addressed monitor manifest without replacing the selected reader's legacy pointer. The candidate reads only its matching code proof and rejects altered sources or a malformed exact-code manifest; issued ancestry continues to use the original legacy contract. After selection, normal native publication updates both views. This prepares diagnostic proof only and does not activate policies or claim PID consumption.

Exact-AI cleanup and database-backed compression share the native raw archive receipt constructor. Exact-AI cleanup binds its existing locked decoded SHA/CRC and original index to the final archive identity through the pinned parent after custody cleanup. Historical receipt-less gzip uses explicit offline enrollment only; a complete old index keeps its prefix/append boundary only after both raw-record chains, counts and coverage revalidate. Changed content is rejected before replacing that original index. Readers never launch migration or weaken generation checks.

An authorized closed-target `deploy/run_postclose_finalization.sh SOURCE_DATE --recover-closed-target --rebind-final-generation` rebinds a previously completed finalization only when original immutable controller/strict and successful detector bytes verify, cleanup is still the same completed attempt, all Main/stage/source/snapshot bindings are unchanged, and only summary/checklist closure advanced. Require the current native controller/strict and its exact checklist bytes. When those current bytes still match the strict binding, do not require a new Main PID receipt before scheduled startup. When the operating checklist changed, revalidate its native SHA-addressed strict-bound original; only legacy generations without that archive use the exact consumed-checklist proof. The paired native DONE markers close the preceding START attempt; later pre-START diagnostics are preserved in the recovery anchor, while a new START, changed source, duplicate/missing terminal or invalid controller remains rejected. Preserve original as-of and inputs through the existing suffix recovery receipt. Run a fresh final detector and recheck generation before native DONE. Never rerun controller/cleanup or replace policy/PREOPEN to satisfy a live consumer. Failed suffix retries revalidate the same original anchor. Changed/unknown evidence fails; ordinary finalization remains unchanged. Sealed controller, finalization-marker and authorized suffix readers share that original-checklist reader. Ordinary native PREOPEN has no intraday handoff to invent; later working-checklist edits do not invalidate an unchanged sealed postclose generation. All other current controller/strict/source/date/hash checks remain mandatory, and actual current PID/policy/observer validation remains separate.

Submission observation health applies its existing exact historical scanner identity/hash/PID/birth proof to pending notification keys as well as incident classification. Keep original incidents, pending delivery and null/source-gap diagnostics. A pending historical notification does not itself prove current source failure; unknown/current keys and new source loss remain actionable. This is bounded quality WARNING, never full observation validation.

The submission receipt/cache successor preserves explicit root-parent lineage and liquidity-guard terminals under existing guards. Cache schemas21/22 use verified forward-only migration; the source-window producer/reader must upgrade together before startup. The native summary keeps exact unchanged parser/callback semantics and preserves its predecessor checkpoint. Missing-feature diagnostics allow independently proven FALSE prerequisites alongside UNKNOWN branches, with all native identity/clock/source checks and zero trading authority retained. Root-change rejection traces keep both native roots for causal diagnosis; their presence alone is not recovery.

The ordered deployment prepare phase invokes the existing bounded `sentinel_source_window.prepare` while its startup hold is owned, after native policy/bootstrap checks and before Main starts. Record the preparation receipt in the transition. Missing/stale cache or incomplete native index keeps the transition stopped with its owned hold; do not rebuild a full-day source or start with an unverified projection.


The native hold-invalidation observation successor binds the exact runtime lifecycle, native snapshot/rejection, AI adapter, probe producer/scanner and monitor files as one reviewed source generation. Pre-drain delay/stop/holding checks reject a missing, dirty or mixed file and retain issued predecessor profiles. This is a diagnostic code handoff: FIRST_PRICE_HOLD decisions, deadlines and native rejection remain unchanged. The existing producer lock and current-PID observer publication still precede full health. Exact historical receipts without the original native terminal cannot be reclassified from price resemblance alone. See the [native invalidation review](audits/postclose-root-cause-recovery-review-2026-10-19.md#native-first_price_hold-invalidation-observation--2026-10-21).


The revived fixed-watch wait successor derives missing observation source_signature from the new native watch admission only inside the existing pipeline logger. Runtime revival still clears inherited source/route and enforces warmup; conflicting signatures remain actionable. The exact handler/capability-reader group requires fresh rising/holding fixtures and full pre-drain native policy/stop/delay/holding checks. Preserve original waits and strict monitor boundaries. See the [wait identity review](audits/postclose-root-cause-recovery-review-2026-10-19.md#revived-fixed-watch-wait-identity-and-1005-log-burst---2026-10-21).


A reviewed residual-receipt successor carries the existing registry's exact current Main residual BUY identity into the native entry ledger before REST staging completes. Bounded inventory recovery uses the same registry and probe owners, requiring every exact unit-leg terminal/amount and no SELL/cancel/manual conflict; it never copies account aggregate cost or invents fills. Keep the source-generation profile complete, publish fresh entry-cancel/rising/holding capability fixtures and verify native report currentness before the ordered transition. Preserve initial failure/registry/probe bytes and verify the repaired DB/runtime quantity through the normal startup or periodic sync consumer. See the [receipt recovery review](audits/postclose-root-cause-recovery-review-2026-10-19.md#exact-residual-receipt-and-owned-quantity-recovery-review).

Exact reviewed wait/receipt successors retain the historical-resolution late-fixture path: the original fixture must bind the unchanged original report SHA and independently verifiable test/network evidence, while a new fixture proves the current code. A fixture published after an immutable report never permits modifying that report or accepting an unbound/mixed generation.

Owned unit-entry quantity recovery must publish and natively restore the exact holding BUY receipt before committing the DB quantity. A matching already-completed recovery proof permits source-only identity completion while the position remains open; any actual SELL/cancel/manual custody blocks this path. Preserve the prior receipt and failed boot evidence; validate the boot consumer, not only the quantity projection.


The cooperative collector-close successor routes both restart claimants through the existing restart request owner. Main joins the engine before summary termination drain; the native WebSocket close must retain its collector until the immutable final snapshot is persisted. The existing ten-second collector deadline is shared across worker/writer phases. Ordered deployment pins the running collector PID/start/epoch before a stop request and verifies its native closed receipt after exit. Missing actor or closure proof retains the incumbent/owned transition; PID absence alone cannot advance selection. Legacy self-SIGTERM incumbents cannot be treated as supporting this contract. Their first transition remains a separate native predecessor closure requirement; do not inject running code, fabricate a close or waive the guard. Full timestamp rejection journals retain exact coverage while the diagnostic tail remains64. Preserve both journal and closed receipt for every dependent source; midnight closure binds the original source date separately. See the [existing cause and repair review](audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#종료와-거부-증빙-생산자-수리--2026-10-21).


For the first legacy-to-cooperative transition, the existing ordered pin accepts a collector already closed by the native market-close path. Before requesting Main restart, require same-day consumed selection, normal engine terminal with zero unresolved positions, the original shared-WS PID/start/boot/root/commit and matching observer epoch, and all native immutable closed receipts. Recheck exact frame/latest/closed bytes after exit. A running legacy collector, missing/changed receipt or incomplete rejection coverage remains blocked. The already-stopped predecessor path additionally retains its original closed-consumption proof. This adds no signal injection, collection cutoff, scheduler, forced exit or historical approval. See the [first transition review](audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#최초-전환의-native-장-종료-연결--2026-10-21).

The reviewed quantity capture successor extends the existing exact handoff profile with the bounded native context reader and durable SELL-to-capture terminal delivery. It preserves the issued collector-close and first-transition generations and rejects missing, changed or mixed readers. No quantity, split, timeout or policy selection changes accompany this profile. Its code validation does not replace native market-close evidence for the first legacy transition or prove a naturally completed capture window. See the [quantity source review](audits/postclose-root-cause-recovery-review-2026-10-19.md#수량-실행-원천의-bounded-전달과-종료-영수증--2026-10-21).

The quantity successor's frozen trailing reuse reads original completed-source byte observations only from exact manifest path/hash references already sealed in the approved input epoch. The existing completed owner shares schema, source epoch and filename validation with its current semantic reader, but returns no historical normalized-row binding to new code. Current extraction readers still require current code, and current research semantics run anew. Changed originals, dependencies, authority or manifest bytes remain invalid; the32MiB unproved-source budget is unchanged. The operator chose native natural closure for the first legacy transition; clock time alone never authorizes drain.


### Normal-exit and holding-input source handoff

The prepared holding-input generation binds the DB datetime producer, both Main HOLDING dispatch clocks, native rebound adapter, stop observation/quantity projections and holding vote cost context as one exact dependency set. `REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS` preserves issued predecessor policy/report readers; missing, dirty or mixed files reject preparation. It does not select a release or relax a trading guard. Before any authorized transition, verify this candidate's active-policy parity, delay/stop/holding code contracts, native report currentness and the existing natural-close receipt contract. Configured fee/current-book estimates remain modeled inputs; missing original receipts, actual broker costs and historical arm provenance remain unresolved under their existing source owners. See the [existing repair review](audits/postclose-root-cause-recovery-review-2026-10-19.md#2026-10-21-normal-exit-receipt-and-holding-input-repair).


### Post-sell source reader preparation

The reviewed post-sell successor binds its candidate recorder, route registration, exact-item recovery and 0D horizon reader as one complete code generation. `REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS` preserves issued predecessor readers. The code-only handoff does not select/restart a release. Native physical SOR venue ambiguity remains UNKNOWN/unverified separately from operator assignment and quote scope; it must not become a universal promotion/restart gate. Source-only horizons retain exact route/item, clock/depth/transport and existing bounded additive REG/retention contracts. See the [existing source review](audits/postclose-root-cause-recovery-review-2026-10-19.md#2026-10-21-post-sell-route-source-repair-and-unresolved-physical-venue).


### Operator Market Default Candidate

The operator KRX/SOR default candidate extends the prepared post-sell source
release. Its source-only native fixtures, original active policy parity and
exact complete dependency generation must verify before any transition.
Original raw native venue and quote evidence cannot be repaired by selection.
Preparation does not restart, reserve or schedule a transition. Main's
incumbent collector must still produce its native natural-close evidence under
`DirectFamilyPreopenPolicyHandoff` before the separately authorized ordered
transition. [Default scope and proof boundaries](audits/postclose-root-cause-recovery-review-2026-10-19.md#2026-10-21-operator-krx-sor-defaults).

### Evening Deployment And Postclose Continuation

For the approved first natural-close transition, start preflight at19:55 KST.
The installed20:05 EOD,20:10 stop-only,20:30 postclose/controller/tuning and20:50 archive
triggers do not wait for a deployment startup hold. Before their due times,
the authorized operator must preserve and temporarily pause only the affected
entries, including conflicting research/finalization triggers. Record the
original bytes, hashes, owner and restoration condition, and preserve concurrent
schedule changes. A deployment lock alone does not provide this pause.

Do not force-stop the incumbent before its native epoch closure. Verify the
original collector/WS actor, writer drain and complete terminal evidence, then
use the reviewed candidate's ordered driver. Resume postclose computation only
after exact successor PID/policy consumption and current observer/full-health
verification. A failed transition retains its original phase, hold and attempts.
Stop an incorrectly started postclose wrapper through its owned TERM/trap path;
escalate only its verified surviving child group after the documented grace.
Never erase a lock or hold, use a broad process kill, or force a terminal status.

Resume the same source date through the existing stage/checkpoint contracts.
Preserve EOD dependencies, original failed attempts and actual publication dates.
The router's `finalize` target always passes `--resolve-effective-today`; a
positional date is not an explicit source-date recovery interface. An authorized
early finalization must use the selected release's existing source-date wrapper
recovery, with its native terminals, custody, logging and lock checks. The next
scheduled05:35 finalizer still rechecks the latest closed generation. Existing
06:00 predecessor and06:50 finish limits remain in force.

The prepared-startup ancestry repair accepts one consumed generation and at most
its exact original prepared generation. Both retain full native verification,
date, policy, source and bootstrap bindings. Unknown extra generations and mixed
sources remain invalid; prior issued single-generation profiles remain readable.
The [dated execution instruction](audits/postclose-root-cause-recovery-review-2026-10-19.md#1955-통합-전환과-장후-작업-실행-지시--2026-10-21)
records the complete authorization and failure/resume sequence. Documentation
and review do not execute, schedule or reserve that transition.

Inside isolated startup validation, source-anchor checks seal the current mount
information and compare every file's identity and lexical ancestry. Shared
parents are checked once per pass and again at the boundary; aliases retain the
original identity reader. A mount, inode, size, clock, permission, source or
request generation change remains invalid. This bounds redundant metadata work
without changing the child timeout, kernel isolation or native policy checks.


### Integrated entry source, receipt and quantity cost handoff

`REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS` binds the complete reviewed postclose predecessor and exact original-to-integrated source pairs. Each changed entry/receipt/cost member requires the entire generation; missing, dirty or mixed dependencies still fail before drain. Use fresh native parity and capability fixtures, revalidate the code-specific initial-quantity prepared stage with the existing publisher, and preserve every original policy, PREOPEN, strict/checklist and failed attempt.

The existing native inventory recovery may consume a terminal initial one-share probe whose original DB still contains the requested bundle quantity and no fill clock. It requires exact owned same-day journal census, sealed original plan/account/route, positive native fill amount and original aware fill clock, and no residual submission or SELL custody. The original requested bundle and unsent remainder stay recorded as residual_not_submitted with expansion forbidden; aggregate account values never create cost, clock or ownership. The authorized ordered driver and ordinary bootstrap remain the only transition owners. Verify actual successor PID consumption, current Sentinel/observer and the original failing inventory check after startup. Historical source exclusions remain separate from present code/currentness and economics.

For the first restart after native PREOPEN, PID attestation may change selector metadata while the selected commit is unchanged and no intraday receipt exists. The existing readiness verifier authenticates the exact live native PID/bootstrap, sealed original checklist and unchanged prepared source receipts, then repeats PID/selector validation after full bootstrap. Candidate P5 enters the existing exact live predecessor review context and runs the full native CLI; it does not synthesize an intraday handoff, alter original preparation or accept a stale PASS. Changed commit, unknown/stopped PID, different source or modified sealed checklist still fails before drain.

A carried stop policy consumes its original sealed research-allocation scope. A new quantity research index is not an actual-cost revision. Routine carry validation rechecks the original immutable allocation receipts plus current official source dates and the complete actual-cost census; changed/missing original receipts or official/actual costs still fail. Numeric selected cells and full research verification require the current allocation generation. This repairs the shared mutable research-index dependency without changing the original policy/report or treating recovered research allocation as actual execution costs.

P5 native-consumed PREOPEN closure retains both the original prepared full-bootstrap proof and the separately verified actual consumption. The typed consumer rechecks the current selector PID/start/cwd, selected commit and active bootstrap JSON/env hashes. This distinguishes a loaded native PREOPEN from an intraday handoff while preserving the original prepared policy/activation and code inventories. The new closure grants no execution authority; the independent active-policy parity and ordered runtime handoff remain mandatory.

The native P5 result records its actual verification code root/commit separately from the selected policy origin. Delay inventory attestation uses that verified candidate or selected tree consistently in the parent and isolated child; foreign roots and mixed commits fail. The exact Sentinel submit-terminal successor preserves callback AST/dependencies and migrates only the reviewed parser/owner pair, retaining the original checkpoint/archive and reading only the new raw suffix. Current active-policy parity, source CAS and actual successor PID verification are unchanged requirements.

Ordered deployment also checks the native diagnostic-summary migration before draining Main. Keep its32MiB suffix bound: an oversized predecessor stays running for ordinary producer catch-up or a separately bounded native suffix recovery. After selection, finish the existing summary producer under its lock and the owned startup hold before Main starts, alongside the existing lossless cache/source-window preparation. Retain original checkpoint bytes and failed attempts; no full-day rebuild, limit increase, cursor reset or old report publication is implied. The startup account owner reconciles registered BUY_ORDERED custody before the timeout loop. A missing local order number cannot clear an unresolved owner interlock; a zeroed same-day WATCHING row is recoverable only through its exact original Main terminal/probe receipt, never aggregate account inventory. See the [integrated transition review](audits/postclose-root-cause-recovery-review-2026-10-19.md#integrated-entry-receipt-and-quantity-deployment-2026-10-22).

Main shutdown closes admission to diagnostic probes and drains their existing exact leases/completion callbacks before stopping the same WebSocket. The45-second shutdown resource bound does not change a probe/signal/handoff deadline or authorize a new lease/order. Keep native failure and retry semantics; even a failed drain still executes WS and observation-source cleanup. No UNKNOWN log record or scanner cursor is removed.

Native capability JSON may use the existing snapshot_archive identity protocol when its original physical report exceeds the observer8MiB limit. The existing publisher fully validates the original native source within16MiB and verifies a lossless gzip CRC/hash round trip under the JSON generation lock; retain the original file and hash. Readers cap compressed bytes at8MiB and decoded source at16MiB, validate exact original/archive identity and native semantics, and return the original physical SHA. Missing/changed source, receipt or archive remains actionable. Future entry-cancel publication uses generation-safe JSON plus this existing archive path; no field/row reduction, old-contract promotion, policy change or cached semantic PASS is allowed. Independently fresh fixtures and exact reviewed code succession remain required. [Cause, regression and current acceptance](audits/postclose-root-cause-recovery-review-2026-10-19.md#integrated-entry-receipt-and-quantity-deployment-2026-10-22).

On native report regeneration, preserve the predecessor archive receipt before replacing its current alias. Authenticate the retained gzip's full compressed and logical hashes, CRC and bounded sizes against the sealed original receipt; preserve that receipt byte-for-byte under its own content hash. Native retention may deduplicate identical gzip bytes, so historical inode/clock coordinates remain historical evidence, not the identity of the retained blob. Multiple original receipts for equal bytes must coexist. Current source/archive epoch checks remain strict. Missing, changed, conflicting or symlinked predecessor evidence rejects publication. A shared capability-code change requires fresh native fixtures for each affected family before their current consumers; it does not promote historical report generations.

A user-authorized operational exception may classify a strictly verified native observation wait as pass_verified_observation_wait. Only the existing recorded_guard_or_cohort_pending or bounded_no_applicable_observations projection with zero unmet predicates, exact recomputation, fresh body/file, current generation and native consumed-actor proof qualifies. Record report SHA/run/actor/window, MainEntrySourceTerminalRepair1022 owner and removal on report/actor/health change in the existing detector details; retain partial/UNKNOWN/null economics and current_observation_verified=false. Revalidate each publication. Bounded-source-quality WARNING, unknown/current loss, invalid provenance and other artifacts do not qualify. The daemon preserves prior failure state and never announces recovery from this incomplete observation exception.


Ordered deployment reserves the existing `run_buy_funnel_sentinel.lock` after native preflight and before acquiring its startup hold or draining Main. Keep it through selector publication, source-window preparation and summary migration; release it before launching Main so the current-PID startup observer uses the same owner. The existing60-second owner drain bounds admission while the incumbent remains live; no trading/startup deadline is enlarged. A legacy selected-phase EAGAIN after all three native preparation commands succeeded may use the existing stopped-transition recovery only with their exact bounded JSON/date/hash proofs, original hold/selection and genuine stopped-predecessor consumption. Preserve the failed attempt and freeze every preparation proof through hold transfer. Missing/changed/failed preparation, an unknown phase/error, current Main, source mutation or mixed code still rejects recovery. This coordinates the existing producer; it adds no cron, source reset, policy change or new startup path.


For a stopped recovery, retain every failed attempt and original first-launch expiry. Use the existing ordered owner's verified preflight/hold transfer/publication/preparation, then issue the native unchanged prepared-policy code handoffs and run isolated P5 before start/attestation. The prepared-intraday native closure authenticates the current unconsumed handoff, its original prepared full bootstrap and all frozen sources in the same invocation; its distinct basis retains actual_pid_consumed=false and the historical validation scope. It never substitutes a prepared proof for live consumption or extends the15-minute launch deadline. Missing/changed sources, failed full validation, a consumed/foreign selection or invalid native evidence remains a failure.


Prepared-intraday P5 keeps the original prepared bootstrap semantic hash separate from the active bootstrap hash. Bind the current native handoff to its exact frozen active manifest/date/hash while independently retaining the original full bootstrap and prepared receipt. The existing stopped-recovery owner accepts the exact retained prepared-stage embedding return-shape failure only after all three native commands, source-window and summary proofs verify; follow at most three immutable failed-transition references back to the genuinely consumed predecessor. Freeze both failed statuses and all native sources, preserve original expiry/hold/selection and reject unknown failures, changed ancestry or deeper chains. Embedded startup validation unpacks the existing `(result, receipt_path)` return and checks its actual status before starting Main.


The isolated Main preparation consumer has its own exact reviewed source-pair inventory, independent of delay/stop/holding handoff checks. Register only reviewed original/current custody-recovery bytes there and exercise candidate P5 before selection, then selected P5 before start. A retained legacy full-result assertion must exactly match its original native final JSON/run/date/selection/verifier identity and its known intake failure; freeze that original report with every preparation proof. Record later P5 failure using short status/findings plus original report path; never copy the full result into transition errors or treat failed P5 as live consumption.

Indexed stop inputs remain under the native source-store coverage and record-chain contract. For isolated P5, its parent verifies each exact preparation-bound report input through that native reader and seals the observed generation with raw/archive/receipt and database/WAL identities, including absent paths. The child checks the same report, source scope and identities without opening SQLite or rescanning raw history; the parent repeats native generation verification after the child. Missing, changed or unbound sources reject validation. Archive enrollment or a later append invalidates the invocation and requires fresh native preparation evidence. Ordinary runtime readers keep their native index validation, and isolated database/network prohibitions remain enforced.


Embedding uses the existing `execute(driver, validate_prepared=...)` owner for the complete transaction. The optional callback issues native prepared-code handoffs and validates P5 after preparation; a failed callback uses the same failure handler and cannot start Main. Do not call the pre-publication old-selector `assert_unchanged` after publication. The native `start` checks the current published selection and exact owned hold. Retain an exact prepared-stage legacy comparison failure only through the same authenticated native preparation, original hold/selector and immutable predecessor proofs; do not reset the original attempt or fabricate consumption.

The ordered owner's prepare step completes native unchanged pre_submit_delay, main_stop and holding_vote code custody before selected P5. The existing prepared_policy_code_handoff.issue_selected producer verifies the selected native handoff and all three original policy bindings under the selector lock; verified existing receipts are reused without rewriting their bytes or file generations. Missing, changed or mixed custody fails before the prepared checkpoint and Main start. Embedding callbacks consume this completed preparation and run selected P5; per-caller issuance is replaced by this common producer. A retained short selected_p5_failed reference may authenticate only its exact original custody-intake failure with run/date/selection/verifier and all native prepared-stage proofs; preserve the failed bytes, owned hold and original expiry. It never supplies PID consumption, suppresses an unknown P5 failure or authorizes start without a fresh passing selected P5.

For a native closed collector with explicit PID/start ticks, bind those fields to the genuinely consumed selected actor and its expected engine terminal, then verify the immutable closed epoch and complete native source census before any stop request. It need not have published a WS frame after an after-hours startup; another actor's latest frame cannot supply or invalidate its own collector identity. Legacy receipts without actor fields retain the existing WS process/boot/root/commit/epoch and clock proof. Both paths reject changed closure bytes, actor conflicts, source loss and unresolved holdings, and recheck the pinned closure after drain. This describes the reviewed successor; deployment and natural next-startup consumption require their own receipts.

An expired failed preparation may be inspected only inside isolated candidate P5 through the existing ordered recovery custody inspection and predecessor-review scope. Authenticate the owned hold, original failed/native preparation evidence, stopped consumed predecessor, clean managed successor and all frozen hashes. Bind the unchanged original expiry and false runtime/PID/apply flags in the parent and isolated child. Ordinary launch verification remains expired and consume is forbidden in this analysis scope. A new authorized ordered attempt requires fresh native preparation and selected P5; never rewrite or extend the failed attempt.

Entry and active-policy readers share the existing predecessor-review custody predicate. Preserve exact live/closed PID identity; failed-preparation P5 uses its authenticated stopped-source proof without claiming a PID for the unconsumed selection. Complete native active-policy code handoff issuance before candidate P5; retain all original source/authority and currentness checks.


### Postclose admission failures and workflow provenance

The postclose status writer preserves the previous producer terminal byte-for-byte when a new invocation fails before publishing RUNNING. It records the separate early attempt and the preceding immutable snapshot under the existing attempts directory. Once RUNNING belongs to that invocation, ordinary terminal publication remains unchanged.

A reviewed immutable postclose workflow repair can execute against the unchanged selected runtime through the existing PROJECT_DIR override before candidate P5. Record the actual workflow root/commit/script hash separately from the selected runtime code_commit; hold the router scheduled-execution lease and use native custody. This source-only workflow execution grants no selector, policy or Main-start authority. For the legacy pre-start clobber only, --resume-from-final-handoff --origin-code-handoff authenticates the original failed status frozen by the native same-day code-handoff producer, unchanged selection and active pointer, absent Main/supervisor, and the clobber attempt's successful pre-start-only metrics. It binds both original producer and current input failure hashes; it never restores or edits the old status. Missing or changed evidence rejects admission. Full native strict verification and sealing still own completion.


A postclose workflow repair is part of the complete reviewed dependency generation. Bind its exact script SHA in the existing prepared-owner inventory and Main's independent original/current history. A changed, missing or mixed wrapper remains rejected. An earlier cleanup selector may be skipped only for the exact current reviewed selector while the complete current dependency closure is independently checked; historical native generations retain their own complete inventory.

Native active-parent source issuance selects an already-issued identical-policy code-refresh preparation by its role while the active pointer still predates that target. Validate the exact frozen next-session generation, source code, authority, target/publication dates and identical attested active parent. Do not infer this route from a backend error prefix. The already-active session follows its ordinary loader without reading a preparation alias. Missing, changed or conflicting preparation remains invalid; no active pointer or policy payload is rewritten by source validation.


Closed-session active-parent code handoffs bind the original native parent receipt's verified source/code closure explicitly. The original validator runs in an immutable child release, so parent-process I/O observation cannot substitute for that closure. A separately validated next-session preparation binds only its immutable generation and unchanged active pointer; its incidental future evaluation caches are not active-parent sources. Content-addressed auxiliary evaluation/resolution writers preserve first physical bytes under the existing writer lock and reject conflicting or aliased snapshots.

For the exact unconsumed legacy prepared-parent producer, reviewed `reversal_code_handoff.repair_prepared_parent_scope` is the existing native metadata repair owner. It requires the exact old receipt hash, unchanged selected consumer/code inventory, verified native cold-selection transaction and historical candidate P5, no Main/supervisor/hold/restart, the original closed-postclose window, and full native active-parent validation in the original immutable release. It preserves original receipt bytes in that receipt's attempts directory and publishes only the corrected parent closure with workflow identity and CAS. It does not alter policy/selector/PID or validate future policy. Preserve the failed future evaluation and rerun only its auxiliary producer and downstream summary/strict/controller/preparation after the native active-parent consumer verifies. A new candidate still requires fresh parity, independent source review, exact candidate P5, the actual offline-tested publication sequence and later selected P5.

For an explicitly authorized stopped source-cohort recovery spanning scheduled finalization, reuse the native scheduled-execution lease exclusively across the minimal machine, auxiliary and summary prefix; inherit its descriptor through each native child, pin the selected release/selector and stopped state, stop on first failure and preserve the original06:00 predecessor deadline. The05:35 finalizer waits before selection resolution and then owns whole-controller, cleanup, detector and preparation. This uses the existing lock and CLI owners; do not launch a parallel finalizer/controller, alter cron or renew the deadline. Full candidate P5 precedes selection; selected P5 consumes the final prepared generation afterward.

A repaired immutable workflow may also rebuild the current preparation while a previously verified cold selection remains stopped and unconsumed. The existing predecessor-review owner authenticates that exact native single-selector transaction, its original candidate P5, unchanged active pointer and both selected/successor active-parent source receipts. Require a clean managed workflow, the source-to-next-operating-day calendar window, absent Main/supervisor/hold/restart and explicit no-start scope. Historical P5 proves the predecessor transaction only; every current source, whole strict/controller and full native bootstrap is revalidated, followed by a fresh isolated candidate P5 before any new selection. Native auxiliary publication and bootstrap bind the selected runtime commit separately from the workflow commit. In the bootstrap manifest, `producer_code_sha` identifies the actual generating code and `selected_release_sha` identifies the authenticated selected runtime; the two may differ during reviewed recovery. The prepared receipt records its actual verification workflow and custody digest; the isolated child independently repeats the same custody check. Missing or changed proof, source, date, actor or selector fails closed. No PID, activation, first-launch extension, policy change or Main-start authority is produced. Keep the original failed stage and old prepared generation, and revalidate the final selected preparation after the native code transition.

The shared prepared-policy consumer also enters that native stopped review when controller or strict verification runs in the repaired workflow. Bind custody to the actual observation day and the policy to the exact prepared target day recorded by that review. Neither date substitutes for the other. Recheck the selected predecessor's original prepared-code custody, the successor's complete reviewed code and unchanged sources; propagate entry, exit and generation failures. A different target or ordinary foreign workflow does not acquire this scope.

Cancel-wait report reuse requires both its existing source/implementation fingerprint and the current native policy-generation code digest. Shared publication, preparation or validation dependencies can change without changing the narrower calculation fingerprint. Preserve the displaced report and rebuild it through its existing producer; do not copy its obsolete capability contract into the new publication or rewrite it by hand. An unchanged generation retains the native cache, historical gaps and incumbent thresholds.


A live Main may outlast its source-only observer after the native latency canary closes that collector. The ordered owner binds this distinct `native_observer_canary_stop` basis only to the exact consumed PID/start/root, unchanged guard configuration, recomputed latency-only stop reasons and immutable reconciled writer receipts. The original stopped epoch remains semantically ineligible; byte closure permits an approved process transition and never grants source, policy or trading admission. Unknown stops, loss, changed guard/receipt/actor/date or incomplete epochs still block before a restart request. Recheck the same native bytes after drain; retain the stop reason and verify fresh successor collection without resetting or relaxing the canary.


Bounded observer health accepts the existing native entry-trace index without requiring a raw rescan. Validate the exact dated namespace, sealed generation, source stat/identity/size, chain hashes, record counts, complete clean window and combined index/raw byte budget. Projection-only zero raw reads and legacy exact-row multiple reads retain their original receipts. This admits only bounded incomplete-observation WARNING; current observation/full coverage remain unverified and all original diagnostics survive. Foreign, missing, stale, partial, changed or malformed index evidence remains actionable. Original raw-tail readers remain the owner for unindexed journals.


A historical holding-policy parent may close its recursive audit ancestry only through an existing native consumed intraday handoff. Bind exact dated bootstrap bytes/env, policy receipt and rollback cells, prepared handoff SHA, original consumed PID/start/cwd and launch interval. This authenticates a historical policy only; current observation, numerical selection, summary and strict terminal proofs remain mandatory. Missing/changed native proof falls back to strict ancestry or fails. Never regenerate a lost old summary or invent consumption to obtain continuity.

The runtime summary owner validates DATA_DIR/REPORT_DIR custody and preserves old/new summary and holding-policy bytes in exclusive content-addressed read-only generations before native transactional replacement. Unit tests use private filesystem write roots inherited by children, reusing startup isolation. Capability test outputs stay private until the existing trusted publisher copies their bounded XML/network evidence. Production data/log roots remain unwritable to tests. See [cause and acceptance](audits/postclose-root-cause-recovery-review-2026-10-19.md#consumed-policy-parent-closure-and-test-write-custody-2026-10-23).

Candidate P5 may use its repaired native verifier for either an exactly verified live native-PREOPEN or consumed intraday predecessor. Both use the existing predecessor_review custody scope, clean candidate, full policy checks and selector/PID recheck; an unknown/unconsumed origin retains the original verifier and never earns candidate consumption or launch authority.


The reviewed2026-10-23 KRX listing/SOR repair uses the complete `REVIEWED_AFTERMARKET_LISTING_PROFILE`, retaining its consumed auxiliary-capability/REST predecessors. The independent Main preparation inventory binds the same reviewed source generations; missing, dirty or mixed sources still fail. The candidate needs fresh native parity, affected capability fixtures and candidate P5 before an authorized transition. No dated trial SOR approval file is a current entry requirement. [Review](audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md#krx-listing-eligibility-and-sor-preflight-repair---2026-10-23).

The authorized current-release integration retains the consumed numeric/source-flush profile as the complete parent of the KRX/SOR listing successor. Independent Main preparation uses the same merged source bytes; candidate P5 and selected prepared P5 remain separate. Original a12b56117/P5 intake failure is preserved as historical evidence. [Current integration](audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md#current-release-krxsor-integration-and-authorized-deployment---2026-10-23).

A signed legacy source-invalid preflight capture is historical process evidence only when its exact schema/action/reason, six-field scanner identity, bundle, original hash, same-day capture/consumption clock and strictly prior PID/start/birth all verify. Require explicit no-provider/no-order/no-runtime/no-apply flags, broker prohibition and no native reversal-consumption claim. The existing observer retains the original unresolved incident and source error; bounded WARNING does not grant current coverage, policy consumption or trading acceptance. Current actors, missing/conflicting proofs and unknown legacy captures remain actionable. The complete `REVIEWED_SCANNER_PREFLIGHT_PROFILE` retains the consumed listing generation and independent Main preparation review. [Cause and regression](audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md#submission-monitor-legacy-preflight-lineage-repair---2026-10-23).

Before the initial-quantity refresh (including its scoped resume), the postclose wrapper uses the existing `main_trailing_source_store.prepare_window` for the exact source day. Preflight quarantine can replace the raw inode after the earlier index was sealed. The native owner preserves displaced SQLite/WAL contents, verifies surviving sources and reuses covered generations before the cost revision reader binds them. No reader starts this migration, source dates and cost-null semantics remain unchanged.


Historical source-profile discovery does not enlarge the inventory declared by
that original contract. An absent optional detector selector is not a missing
policy source. The existing native code verifier still requires every declared
source and every dependency of a selected reviewed profile, with committed bytes,
exact hashes and no aliases. Present invalid selectors and dangling aliases remain
errors. Source reconciliation into main is a code change; it does not issue native
handoff receipts, select a release or prove next-session consumption.

A reviewed successor retains an earlier operator source only when that source's
reviewed successor exactly matches the pinned predecessor. The complete current
dependency generation remains mandatory; an isolated matching file cannot
authenticate a mixed profile.

Stopped postclose code custody follows the native KRX source-to-next-trading-day
interval across weekends and holidays. The source must be a trading date and
the selected next operating date must equal its native next trading date.
Retain the stopped-process, restart/hold, full terminal and unchanged active
parent checks. A previously selected cold successor resolves only its exact
offset-bearing selection-day receipt, with the original postclose source date;
it never searches for a convenient historical proof. A retained earlier
workflow must be clean and already hash-bound by that parent's native closure,
and the selected predecessor still performs whole-controller verification.
The reviewed source-repair profile binds the complete producer dependencies
and independent preparation pairs; current fixtures attest code capability,
not the correctness of superseded calculation results. Rebuild affected
producers before summary/strict/controller/finalization/preparation closure.

Frozen auxiliary registries retain their original projector, compact wire and production-input contracts after a reviewed source formatting transition. The existing compatibility owner compares exact reviewed generations without returning historical bytes as a physical code hash. Registry parent reconstruction and native request/response readers preserve original identities; unknown code, changed semantic fields and mixed source/transform generations remain invalid. A successor requires fresh full native registry/request parity, its own compatibility receipts, the complete code profile and independent capability fixtures before candidate P5. A prepared holding-prompt baseline with no eligible candidate remains the native parent-only disposition. [Review](audits/postclose-root-cause-recovery-review-2026-10-19.md#postclose-approved-integration-2026-10-25).

For a stopped postclose repair workflow, P5 must attest the newly computed Main inventory against the exact native verifier/workflow Git origin bound by the frozen prepared receipt and same-invocation cold observation. The selected runtime commit remains the policy activation binding; embedded carried families keep their own historical Git origins. Bind the workflow source hashes and actual native reader paths in the parent and isolated child, require the full prepared bootstrap, and reject missing/mixed workflow proofs. Do not relabel old family origins or substitute a previous P5. [Failure, repair and acceptance](audits/postclose-root-cause-recovery-review-2026-10-19.md#postclose-approved-integration-2026-10-25).

Keep the cold observation's raw predecessor history under its native full verification and same-invocation digest/identity closure. Generic startup request sources remain the existing bounded metadata/code inventory. Do not flatten all predecessor raw paths into that inventory or increase its read cap; continue rechecking the bound cold observation and rejecting changed source bytes or generations.

The protected database configuration successor is admitted only through the complete exact migration source profile and the independent Main preparation source-pair inventory. Preserve issued predecessor profiles and original policy origins; missing, dirty, changed or mixed dependencies remain invalid. Verify unchanged trading configuration and native launcher behavior, then issue fresh active-parent parity, prepared-code custody and candidate P5 before stopped selection. After the minimal invalidated postclose suffix, bind selected P5 to the final prepared generation. This permits no Main start or account cutover by itself. [Integration review](audits/postclose-root-cause-recovery-review-2026-10-19.md#approved-migration-profile-deployment-2026-10-25).

After the last affected source writer, verify report-only consumer generations as well as policy preparation. A monitor projection whose manifest binds changed detector code must be renewed by its native producer after full source validation, preserving existing historical exclusions. An optional research dependency whose physical identity changes must be revalidated only for the affected dates, followed by cumulative/notification consumers without resetting scheduled quota or sending research notifications. If these repairs occur after sealing, retain the original health observation and use native generation readers to prove whether strict/controller/preparation remain unchanged; report current diagnostic closure separately and never overwrite sealed health for another PASS.

The quantity replay reader revalidates native BUY custody against the full current registry, but compares a sealed historical trade by its exact receipt, BUY identity, fill-event hashes, native clock and all economic fields. An unrelated append may change only the diagnostic whole-registry SHA. The existing issued-representation comparison may retain that original SHA in memory only when the independently digest-verified issued replay and every other native proof field agree; it never edits the source registry or frozen replay. The summary handoff uses the existing native quantity projection with exact current dependency/code/cost verification, retaining cold validation when no proof exists and rejection when a published proof is invalid.

StoppedDeploymentRecovery may authenticate a selected P5 that failed in its isolated native intake before creating the Main child only when the exact failed attempt, source/target and dedicated verifier process session prove complete termination and descendant cleanup. This is recovery admission, not a passed startup check. Preserve the original failure/hold/deadline; run fresh candidate validation, phase-specific CAS, native prepare, selected P5, start and actual PID attestation through the existing ordered owner. Present execution identities must match their original failed candidate. Publish the exact successor observer before the first full health sweep.

The active-policy handoff's stopped-origin reader follows the selector's explicit predecessor basis: native_predecessor_path and its SHA use the native PREOPEN verifier; an intraday origin uses the existing intraday reader. A rejected native proof never falls back to the other receipt kind. Both retain original policy ancestry, failed transition/hold binding and post-read selector/source checks.

For that native origin, authenticate the failed candidate's already-issued pre-drain active-parent receipt against the original native Main root/commit/selector SHA and exact receipt/source/code hashes. It proves compatibility only; the separately verified native predecessor proves actual original PID consumption. Never require a nonexistent intraday receipt from the original native Main or use the new candidate's unissued receipt to prove its predecessor.

A fully verified unconsumed intraday handoff may resolve the retained PREOPEN generation as intraday_prepared. Require the exact original PID receipt, unchanged native manifest/verification and selector, plus no successor consumption receipt. Its source-summary reseal permits preparation checks only: summary readers return intraday_prepared_generation_unconsumed with actual_pid_consumed=false, and the runtime approval consumer must not adopt the predecessor PID as the successor. Existing ordinary launch expiry remains effective; authenticated failed-preparation review is read-only. After actual start, the existing strict consumed-PID path remains mandatory.

StoppedDeploymentRecovery owns its verified stopped-origin hold transfer internally. Embedded callers use its default adoption mode; the separate adopt_failed_hold option is for Deployment's verified live preflight path. Verify the actual constructor arguments together with phase ordering and failure unwind before executing a caller.

Shared preparation/consumption metadata participates in policy-generation capability signatures. Before a code-only transition, run the existing native family fixture publisher and verify the unchanged historical reports through policy_generation_code_handoff's exact reviewed successor pairs. Preserve both fixture generations and original report/policy bytes; capability verification never establishes original economics or successor PID consumption. Include this direct artifact consumer in candidate review/current health checks.

A diagnostic-only change in a shared runtime owner still needs the complete reviewed successor profile and independent preparation pairs. Preserve consumed predecessor profiles and source-generation reports; publish fresh native fixtures for every affected family before candidate validation. A corrected local-deadline label or additional receive/gate timing never grants a new deadline, source-quality exception, circuit reset or provider call. [Preclaim and exact-lease review](audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#preclaim-guard-and-exact-lease-causal-follow-up---2026-10-27).

Snapshot memory repairs retain exact source identity and full published report schemas. The report/archive owners may spill lossless row bodies into private temporary files and hash canonical JSON incrementally; downstream metadata readers must validate discarded timeline values and the unchanged whole-file identity. Scratch failures remain failed snapshots. Review the complete code profile and independent preparation bindings, run fresh native capability fixtures, and verify the actual native snapshot consumer under unchanged resource limits before claiming recovery.


The indexed stop-source P5 adapter is installed by the existing validation code
context only after OS isolation and the bound Main preparation proof pass. It
replaces the child process's native index reader with the exact parent-verified
generation, retaining source/archive/DB/WAL identities and native parent checks
before and after the child. The shared production assembler remains byte-identical
to its original implementation, so this I/O-only validation repair does not
invalidate research or policy-generation fingerprints. No adapter is installed
outside isolation or without the Main proof; unknown paths and changed inputs
remain rejected. Previously issued complete code profiles remain verifiable.


A failed detector-only completed-prefix retry can leave the previous full report
unchanged when admission prevented publication. The recovery owner may preserve
that absence only against its authenticated immutable completed prefix and exact
original report bytes, with unchanged source/controller/cleanup/snapshot bindings.
It records the failed suffix start and actual reader path/SHA separately. It
never treats the prior report as current success: native full detector execution
and a fresh matching terminal receipt remain required before DONE. Recheck the
scheduled detector and lock owner before recovery admission; keep retries within
the original stage budget and preserve every failed attempt.


Admit this recovery-source successor only through its complete exact source
profile and independent preparation pair inventory. Keep the original completed
prefix and distinguish the recovery reader's code path from the selected Main
root. Fresh selected preparation/P5 and actual PID consumption remain separate
from successful tool recovery; a recovery receipt cannot attest successor Main
consumption.

Ordered collector drain verifies exact PID/start/epoch, closed original receipts,
zero pending callbacks/queues and capture loss, and equal enqueue/process/persist
counts. A research-ineligible row population is retained with its native semantic
verdict; lossless process closure grants no source admission. Legacy actorless
first-transition rules and canary-stop guard bindings remain strict. If this
verification failed after shutdown but before selection, the existing stopped
recovery owner may consume only the exact owned failed hold, byte-identical original
selector, captured prior PID consumption and newly verified closed receipts. It
preserves the failed attempt, transfers its hold by CAS and requires a new clean
candidate/P5 followed by selected P5 and actual PID verification. No manual hold
removal, fabricated consumption, EOD proof or research promotion is permitted.

Stopped-recovery collector `latest.json` is a pre-start source: verify its exact
identity through the final start check. Preserve immutable closed epoch receipts
and policy proofs through successor attestation; a new collector epoch must not
be mistaken for a changed policy generation. Running failed-hold adoption after
this preserved drain failure requires fresh current PID/native validation and
unchanged original consumed-policy ancestry before the existing CAS transfer.

The same predecessor-review owner admits a clean preparation reader for a
normally closed, consumed ordered release. Derive the consumed source session
from its native closed-consumption proof, separately from the selector's earlier
deployment source and the active parent's calculation date. Require the exact
absent PID/start/cwd, normal zero-unresolved terminal, EOD/isolation and unchanged
source receipts, clean managed reader, no hold/restart, native next-session
calendar and both original-issuer and successor active-parent code proofs. The
successor proof must preserve the active parent's original source/effective
roles. Recheck selection, sources and stopped state across the scope; unknown,
interrupted, changed or live actors fail closed. Preparation and isolated P5 use
this same owner, preserving existing cold-selection and live-predecessor paths.
These are preparation/code-custody receipts, with no activation, policy
reselection, current observation or new PID-consumption claim. The existing
`native_cold_review_sha256` workflow field is retained for compatibility and
binds the exact native stopped review, including its explicit ordered-closed
basis; its name grants no additional authority.

For an isolated startup family whose execution code digest exactly equals the
natively verified prepared policy's declared code digest, bind that exact
execution generation directly. The selected predecessor remains an independently
bound actor; do not require it to have consumed a policy calculated by a later
workflow. The OS-isolated child rechecks the execution contract, original policy
hash, selector/root/commit and unchanged source closure. This exact-code basis
grants no compatibility delta or runtime/PID authority. Non-exact code still
requires the existing original-issuer compatibility chain. Active-parent custody,
complete native preparation, policy loading and selected-generation/PID checks
remain separate mandatory consumers.

An active-policy handoff records a native transition coordinator seen by its
origin reader as observed provenance, rather than freezing its mutable current
pointer as policy input.
Before issue, authenticate its canonical native record and readable ownership,
and recheck the exact observed bytes through publication. Foreign publishing,
corrupt/changed records and aliases fail. Policy, immutable terminal, original
receipt and code sources remain frozen; the current release router continues to
enforce native transaction readability at consumption. Prior issued receipts
remain untouched. Exercise proof consumption under real native transition state
changes in the isolated replay, including publishing and verified phases.

For a normally closed, consumed ordered release crossing midnight, issue the
active-parent proof from that parent's exact original effective-session receipt
only after native closure, calendar, absent-actor/hold/restart and original-source
checks. Preserve the deployment, consumed-session and policy-calculation roles.
Closure is admission provenance; unrelated next-session preparation is not an
immutable active-parent input. Recheck native closure and protected generations
through issue. Missing original proof remains blocked.

Inside the existing authenticated stopped predecessor review, the next Main
policy can retain its selected original issuer while a clean reviewed workflow
verifies preparation. Run the original issuer's complete native source validator
and the complete current code-delta review. Recheck selected identity and scope.
This grants no ordinary runtime fallback or new receipt; candidate P5's isolated
child repeats its independent Main code proof. After the native code selection,
the identical-policy publisher must bind the future bundle to the final selected
code before selected preparation/P5 and actual activation.

Preparation's native verifier and the policy's code-inventory origin are
separate identities. An authenticated workflow may read a family still pinned
to its selected original issuer. Compare every declared module with that issuer;
when all match, retain the declared origin and attest it in Git. A family actually
computed with different workflow code retains the verified workflow origin.
Parent and isolated child repeat the same choice; changed scope/source, unknown
code in both explicit origins and altered attestations still fail.


The reviewed BUY preclaim-role successor uses `REVIEWED_PRECLAIM_MARKET_PROFILE`
and the independent preparation reader's exact source pairs. Preserve the
complete slot-return, carried-SELL and completion-report predecessor generation;
missing, dirty or mixed shared handler/diagnostic/preparation sources fail before
drain. This repair preserves the existing market veto and every source/safety
guard. Research-only R1 or discovery allocation/pattern changes gain no live
authority from code compatibility. Shared-handler changes still require fresh
rising/holding capability evidence, native active-parent parity and candidate
P5. See the [implementation review](audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-preclaim-implementation-20261028).


### Prepared source checks after working checklist updates

Next-session preparation can outlive edits to the operating checklist. When the native controller reports only checklist-generation drift, the existing readiness source reader authenticates the strict-bound original through `strict_bound_checklist_for_observer` and rechecks the sealed controller and every source generation against that exact document. Missing, changed or untrusted originals and all other controller/strict defects still fail. This preserves the original completed computation; it issues no new whole-chain PASS. Prepared receipt, selector, policies, activation candidate, auxiliary reader and full bootstrap checks retain their existing owners and requirements. Do not restore the working document or rerun calculations to satisfy a checksum of later task notes.


### Validation ownership and late PREOPEN recovery

The public controller and PREOPEN preparation APIs own their native source-day
`postclose_session`, including direct recovery callers. An enclosing invocation
with the same data root/date shares that byte identity cache; a new invocation
revalidates sources and semantic decisions. Missing, changed or invalid inputs
and failed validators still fail. Child processes do not inherit ContextVar
custody: an explicit historical activation-parent reader selects its exact
original dated handoff, rechecking its code/source hashes and pointer, rather
than entering the current live trading/recovery context to discover its role.
Missing or altered original evidence cannot use that route.

The whole-chain strict receipt writer atomically preserves its bound checklist
bytes before publishing PASS. The document-preservation entrypoint reuses that
same byte publisher; concurrent identical writes are safe, and conflicting,
symlinked or oversized originals reject publication. This stores evidence only:
readers must still validate all strict/controller/source and actual PID bindings.

The Main launcher's existing environment-wait budget covers both bootstrap
publication and the exact PREOPEN terminal. An env file alone does not end the
handoff wait. The existing completion reader may wait only for the same-day,
same-release RUNNING producer while its native exclusive lock is actually held;
failed, absent, foreign, stale or unowned states fail. Use only the remaining
original budget, then require ordinary PREOPEN/bootstrap/policy/PID checks.

Before cold selector publication, check the strict/current closure and time
window required by the subsequent native policy-code rebind and preparation,
not just candidate P5. Complete the active-parent handoff and any independently
reviewed workflow preparation before candidate P5; distinguish the original
policy issuer from the workflow verifier. A later required phase outside its
native window preserves the incumbent. Execute each actual transition through
its existing owner, with all phases and failure unwind validated offline.

A late finalization suffix uses current detector obligations. If that detector
already requires target-day PREOPEN/Main, complete their existing native gates
before resuming the final detector suffix. Preserve the failed suffix anchor,
original cleanup and full strict evidence. This does not change the ordinary
scheduled finalization order, extend its deadline, suppress current failures or
claim unassisted acceptance. Recheck the exact selected code root for analysis
and execution; a mutable source checkout is not the running validator.

For Main stop watch custody, canonical watch keys remain logical `.jsonl`
identities. A source that was already compressed at publication retains its
physical `.jsonl.gz` dependency and native generation seal. Verify that exact
original generation and stable physical identity; do not require a decoded
plain-to-gzip transition seal that its original publisher never issued. Only
verified carried policies without selected cells may partition complete later
observations. Changed originals, unknown provenance, missing indexes, partial
or historical tails and full research/selected policy validation remain strict.

Both operational preparation and Main's isolated original/current reader own
independent exact code inventories. Before a candidate is committed, reconcile
the complete changed-source generation against both readers, including shell
launchers and strict/controller writers. A profile-presence check in one reader
is insufficient. Regression must exercise the independent native pair reader
and reject a missing, changed, aliased or mixed sibling; retain issued profiles
and all policy/source validation. Authenticate the isolated reader's own bytes
through the operational profile as well.

When the native deployment preserves the editable operating checklist, it reads
and retains those existing working bytes after authenticating the consumed
historical checklist. It must not request an unused candidate Git blob first.
Replacement mode still requires the exact committed candidate document; an
unversioned/missing candidate document never supplies replacement authority.
Preservation is not a substitute for native predecessor/policy/source validation.


During successor P5, the reviewed holding-history handoff owner must verify the
already-consumed predecessor with its own complete committed dependency profile.
Select that predecessor profile only after every declared dependency matches;
otherwise enforce the candidate profile and reject missing, changed or mixed
generations. Exact per-file compatibility alone does not select a whole issued
profile. Preserve the previous issuer/selector and contract-extension bindings,
and exercise both native incumbent policy intake and independent candidate
preparation before repeating the ordered transition.

### Native startup preparation byte custody and diagnostic report memo

The existing P5 preparation context carries historical v6 source validation
through the original-issuer byte capsule owner. Only digests actually consumed
by a full native original reader cross the subprocess boundary; issuer/root,
bundle, invocation, boot and current file identities remain mandatory. Local
semantic validation still executes. A current lifetime child used to verify its
immediate dated report parent is an independently observed generation; recheck
its current pointer through the last preparation reader. Keep the ordinary
small-source bound and original validation deadlines unchanged.

The ordered transition prepares the existing sentinel source window and
incremental summary under its sentinel lock. First-health startup invokes the
existing BUY producer with `--submission-monitor-source`: read the complete
current-day population and publish the identical native submission snapshot
through the existing atomic bounded-source writer. Do not perform prior-day
comparison, whole-funnel classification or scope/economic diagnostics for that
consumer, and do not replace the full report or Markdown. Ordinary scheduled
BUY reporting retains its complete work. Source, clock, lineage and missing-input
validation stay unchanged; the actual PID must still run the source producer
and observer within the original process-start deadline and finish first health.
The summary owner permits only the reviewed prior parser/owner pair; preserve
original manifests and raw offsets, and append incrementally without rebuilding
historical raw data. No old report or cache becomes current-PID success.

The post-EOD stop owner authenticates the currently selected actor with the
current-PID consumption reader, including exact target date and consumed=true.
The predecessor reader belongs to candidate admission before selection; it
intentionally rejects an already-selected candidate and cannot authenticate a
current stop. Both readers retain their original root, policy and generation
checks. Invalid consumption must fail before collector pinning or stop intent.

A failed selection can precede issuance of its intraday preparation. In that phase, stopped preparation review binds the native original consumed predecessor and verifies that the failed selection's handoff and consumption remain absent. Readiness may revalidate that exact preserved historical generation; it cannot attest preparation or consumption of the failed selection. Newly prepared selected P5 and actual successor PID remain separate requirements, and the read-only scope grants no launch authority.

Source-window health binds two code roles independently: the indexed projection's original writer and the current reader. An unchanged native index may retain an exact preserved writer while the selected reader gains archive compatibility. The detector authenticates that writer through the existing source-window issuer owner, including immutable original bytes and the declared supported generation, and also requires the selected reader's exact code bytes. Unknown, missing, changed, writable or aliased issuers remain invalid; this compatibility does not assert complete observations or erase source gaps.
