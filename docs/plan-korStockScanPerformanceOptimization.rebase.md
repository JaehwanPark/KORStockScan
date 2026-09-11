# KORStockScan Plan Rebase Core Document

Baseline date: `2026-06-05 KST` (clean data)
Document maintenance: `2026-09-11 KST` (history/duplication cleanup only; not runtime verification). Current execution and approved overrides come from the daily checklist and exact-date receipts.
Role: This is the core document that pins only the current tuning principles, automation-chain decision contracts, and active/open state.
Note: This document does not own auto-parsed checklist items. Executable work items are owned by the daily `stage2 todo checklist`.

Tuning data decision baseline: clean tuning data starts at `2026-06-05 KST`, with full-day start timestamp `2026-06-05T00:00:00+09:00`. Raw/report/analytics data before this baseline is `archive_only_not_allowed_for_clean_tuning` and must not be used for EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, or real execution quality approval. The policy artifact is `data/source_quality/clean_baseline_policy.json`; report and analytics residue enforcement is owned by [report-based-automation-traceability](./report-based-automation-traceability.md) and `threshold_cycle_postclose_verification`.

Historical progress belongs in checklist/audit/archive or execution-delta records. Read only task-relevant evidence; do not recursively load linked history at session entry.

---

## 1. Current Decision State

1. Maximize expected value and net profit. The period baseline is `main-only`, `normal_only`, `post_fallback_deprecation`; the clean-data boundary above applies to every tuning/promotion input. Remote comparison values are excluded.
2. The loop is `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`. §2–§4 own decision contracts; [traceability](./report-based-automation-traceability.md) owns detailed artifacts/consumers.
3. `observation_source_quality_audit` preflight excludes identifiable bad rows/windows through `raw_row_exclusion` before tuning/promotion. Required-field/invalid-label/contract warning-or-fail inputs are excluded. Whole-input blocking is reserved for missing/invalid preflight, failed isolation or unidentifiable high-volume no-contract loss. Unknown-token warnings alone are not a blanket stop; producer repair and workorder handoff remain required.
4. One live canary per stage; stage-disjoint concurrency requires separate stage, manipulation point, apply timing, cohort and rollback. Explicit intraday overrides follow §3/§6 `runtime_mutation_guard`, with source/provenance, values and safety priority. Operator locks do not expire merely for age or absent EV.
5. Dedicated entry, holding/exit, sizing, machine and scanner owners retain their existing guards (§5/§7). Selected policy, applied env, current PID consumption and R6 are separate receipts; this document certifies none of them.
6. Scalping ADM/LDM, statistical weight, lifecycle context/attribution, bucket discovery/refinement, LDM-derived scale-in/bridge, greenfield and dedicated institutional aggregation are retired (§8). Preserve raw candidate/submit/fill/terminal lineage and dedicated strategy/broker/hard-safety owners. `entry_observation_source` is normalized raw data, not matrix policy or sim-outcome substitution. PREOPEN retirement OFF guards and archived locks cannot restore this chain.
7. Swing stays operator OFF. Surviving scalp-sim candidate-window, AI-budget and rising-missed prior/control-tower remain source-only and are not detailed-tuning priority. Retired LDM inputs do not retire the whole surviving control tower. Sim/probe/CF cannot prove real execution quality or grant broker authority.
8. `entry_cancel_wait_runtime` independently owns BUY cancel timeout, not ADM/LDM or general threshold EV. Deterministic postclose CF EV may adjust standard/breakout/pullback/reserve within daily bounds for next PREOPEN. Effective from `2026-06-15`, it stays ON across hold/warning/missing-report states unless explicitly locked OFF. Entry-price AI `max_wait_sec` is advisory.
9. BUY Funnel Sentinel surfaces `SUBMIT_DROUGHT_CRITICAL` when `submitted/ai < 20.0%` with `ai_confirmed unique >=20`, or `submitted/budget <= 10.0%` with `budget_pass unique >=3`. Its postclose workorder/current-entry attribution handoff has `operator_action_required=false`; this does not bypass threshold/order/provider/bot or safety guards. `SAFE`/`CAUTION` proceed after slippage check; `DANGER`, stale and broker/account/order/quantity/cooldown blocks remain runtime safety, not an independent latency calibration family.
10. Review focus is real entry/submit bottlenecks, dedicated strategy economics and continuous offline Main AI prompt/input improvement. Use the current checklist's actual Due/Acceptance and exact-date receipts; completed reviews reopen only for a new defect, changed contract or mandatory handoff failure. Candidate/sample absence alone is not implementation failure.

## 2. Terms And Decision Contracts

| Term | Current Meaning | Decision Rule |
| --- | --- | --- |
| `auto_bounded_live` | Mode that applies only families that passed deterministic guard, AI correction guard, and same-stage owner rule to the next preopen runtime env. | Current threshold apply boundary |
| `manifest_only` | State that creates candidates and recommendations without changing runtime env. | Default when approval/guard requirements are not met |
| `report_only` / `observe_only` | State used only for source bundles, workorders, approval requests, and operator review without changing runtime decisions. | No live-change authority |
| `operator_runtime_override` | State where the user explicitly instructed real application through runtime env and bot restart. | Must leave source/provenance and rollback env; must not bypass safety guards |
| `lifecycle_matrix_runtime_policy` | RETIRED scalping ADM/LDM umbrella. | Archive/audit only; no producer restoration or live authority. |
| `fixed_threshold_contract` | Contract that reclassifies existing thresholds as `hard_safety`, `baseline_prior`, `bounded_tunable`, and `legacy_archive`. | Score alone must not decide BUY/WAIT/DROP; no use outside assigned role |
| `approval_required` | Legacy/manual state where the automation chain created a final-stage candidate that still requires user approval. | Use only for final full-live conversion, cap release beyond bounded limits, provider/bot changes, or hard/protect/emergency safety relaxation |
| `sim_auto_approved` | Approval only within a surviving, explicitly enabled sim policy family. | No real order/provider/bot/cap authority; retired LDM inputs cannot be restored. |
| `active_sim_priority` | Source-only key/seed provenance where a surviving producer still emits it; former LDM bucket/swing priority chain is not current tuning authority. | Inspect actual owner and catalog; do not infer BUY authority or require retired consumers. |
| `live_auto_apply_ready` | An active family has closed its own source, economic, review, mapping, rollback and same-stage contract for next PREOPEN. | Not PID application; no universal 1% uplift or retired bridge gate may be imposed on unrelated families. |
| `safety_veto` | Immediate block condition such as severe loss, order failure, provenance damage, or hard/protect/emergency stop delay. | Daily-only evidence may block |
| `source_quality_blocker` | State where stale/missing/duplicate/provenance defects block edge judgment. | Not a threshold candidate |
| `instrumentation_gap` | State where required observation fields or contracts are missing and the decision cannot be closed. | Instrumentation must be improved first |
| `invalid_label_findings` | Source-quality finding raised when a producer emits a label outside the canonical contract, such as unknown holding `flow_state` or gatekeeper action values. | Fail the source contract; fix producer prompt/schema/parser instead of treating it as a valid new tag |
| `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` | Historical exceptional entry/split-entry paths. | Permanently deprecated. Reopening requires a new workorder and rollback guard |
| `shadow` | Former validation mode that computed in parallel without affecting real orders. | Forbidden for new/supplemental alpha axes |

New observation metrics consumed by the automation chain must declare `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, and `forbidden_uses` at creation time. Undeclared metrics route only to `instrumentation_gap` or `source_quality_blocker`.

| Metric Role | Purpose | Forbidden Use |
| --- | --- | --- |
| `primary_ev` | Primary decision metric for expected value and net-profit improvement. | Must not be replaced by `win_rate` or simple sums |
| `diagnostic_win_rate` | Supporting diagnostic for directionality, consistency, and tail risk. | Must not approve live/canary by itself |
| `funnel_count` | Participation, blocker, coverage, and submitted-drought judgment. | Must not be used alone as PnL edge evidence |
| `safety_veto` | Severe loss/order/provenance safety block. | Must not be used as an expected-value improvement metric |
| `source_quality_gate` | Stale/missing/duplicate/provenance quality gate. | Must not be used as a threshold recommendation value |
| `active_unrealized` | Open sim/probe/position context. | Must not be summed with closed EV |
| `execution_quality_real_only` | Real broker execution/receipt quality. | Must not be replaced by sim/probe |
| `sim_probe_ev` | Sim/probe equal-weight expected value observation. | Must not be standalone evidence for real-order conversion |
| `risk_regime_state` | State value that interprets allowed action scope for panic/market regimes. | Must not directly change orders, exits, thresholds, providers, or bot state without approval artifact and rollback guard |

## 3. Tuning Principles

### 3.1 Performance Decisions And Data Criteria

1. The final goal is not loss suppression, but expected value and net-profit maximization.
2. PnL decisions use only `COMPLETED + valid profit_rate`. Exclude `NULL`, incomplete, and fallback-normalized values from PnL criteria.
3. Do not merge `full fill` and `partial fill`. Fill quality, downstream exit, and PnL are separated.
4. Comparison priority is `trade_count -> funnel -> blocker -> fill_quality -> missed_upside -> PnL`. Do not sum `counterfactual` values with directly realized PnL.
5. Win rate is `diagnostic_win_rate`, not standalone live/canary approval criteria. `primary_ev` owns expected value and net-profit decisions.
6. Simple PnL sum is not EV. Name it `simple_sum_profit_pct`; EV fields must be one of `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, or `source_quality_adjusted_ev_pct`.
7. Daily-only values may be used for incidents, safety vetoes, freshness/source-quality, and intraday operational triggers. Edge apply approval must also check rolling/cumulative or `post_apply_version_window`.
8. If attribution is unclear, inspect report consistency, event reconstruction, and aggregation quality before changing strategy thresholds.
9. Report `decision -> evidence -> next action`. Separate contract/code review, deployment, natural source generation, policy selection, PID consumption and cost-adjusted EV/net-profit acceptance. Candidate 0 or thin samples are not alone failure; trace the first missing stage and distinguish maturity, source exclusion, unsupported design and measured no-edge. Report actual producer/consumer, owner, blocker and closure test; do not imply a source-only or disabled family will eventually become live merely as samples grow.

### 3.2 Automation-Chain Decision Principles

Postclose closure contract: final sources -> control tower -> final checklist -> verifier `--require-summary-handoff` -> controller DONE. Validate canonical byte hashes and the successful strict verifier command, not a stale PASS artifact after a failed command/recovery. Exclude verifier/controller self hashes from summary inputs to avoid cycles. After midnight retain the original source date; an unchanged cleanup/detector receipt may be reused only after read-only predecessor checks establish that the repaired scope did not invalidate it, with its original as-of time disclosed.

Economic attribution contract: unreconciled/missing headline PnL remains null with a reason; matching counts alone do not prove exact costs. Validated source-only `avg_down_route_arbitration_observed` v2 rows are CF route observations, not actual ADD/NO_ADD transitions. Recovered historical realized PnL is not incremental profit from a repair. Irrecoverable historical source loss stays excluded; collect the next exact-date evidence rather than fabricate rows or repeat an unchanged replay.

Recommendation provenance contract: preserve each frozen canonical ledger. A later producer-issued native metadata projection and separately authorized implementation ledger must retain original path/location/hash mappings and its own authority/acceptance. Do not rewrite the historical denominator, add both ledgers as unique work, or treat new IDs as live permission. Current actionable state comes from the reconciled successor evidence, not an unchanged old ID-missing count.

1. The scheduled automation-chain unit is `postclose report/calibration/AI review -> PREOPEN runtime env -> post-apply attribution`. An explicit operator-directed intraday override may change exactly one existing `bounded_tunable` axis for one explicit KRX or NXT cohort only with fresh conflict-free source quality, effective price, target-first or sufficient post-block MFE, a single-blocker causal link, and no same-stage owner/canary conflict. The task instruction must fix the stage owner, evidence, before/after values, runtime env/PID provenance, rollback value/trigger, and immediate post-apply attribution. It must not create a competing owner or alter a common/KRX surface from NXT evidence.
2. Unmet conditions close as calibration states, not rollback: `adjust_up`, `adjust_down`, `hold`, `hold_sample`, `hold_no_edge`, or `freeze`.
3. Rollback/safety revert is used only for hard/protect/emergency stop delay, order failure, provenance damage, same-stage owner conflict, or severe loss guard breach.
4. AI correction and pattern lab automation are reviewer/proposer/work-instruction layers. They have no standalone runtime apply authority without deterministic guard.
5. Runtime-loaded AI system/user prompts, reviewer prompts, JSON classifier prompts, and schema instructions use English ASCII as the default contract. Internal decision role descriptions, rules, JSON field descriptions, and fallback reasons remain English; Korean user-facing text is separated into a formatting contract. Korean briefing/Telegram text shown directly to users and contract-required canonical labels are exceptions. Future edits to prompt-contract areas must keep this English standard and must not reintroduce Korean internal prompt wording.
6. Workorder generation does not authorize repo edits by itself. Explicit implementation or invocation of the [postclose monitoring instructions](./postclose-tuning-result-review-task-instructions.md) authorizes that document's bounded source-only recovery and 2-pass implementation; a document-update/read-only request does not invoke it. The default Codex runner remains OFF. Review/fix/validation must close before authorized minimal regeneration; no automatic trading-process restart or live env/lock/threshold/provider/order/safety changes.
7. Existing fixed thresholds are not deleted; their roles change. Broker submit/stale quote/price freshness/stop/account/order/quantity/cooldown guards are `hard_safety`; `BUY_SCORE_THRESHOLD` and entry score cutoff/VPW/strength/momentum families are candidate-generation `baseline_prior`; score65_74/soft stop/holding/scale-in price guard are `bounded_tunable`; latency DANGER/stale/broker submit block is `hard_safety_submit_quality`; fallback/legacy latency/shadow axes are `legacy_archive`.
8. Score is a baseline prior/feature, not a monotonic EV guarantee or standalone action authority. Dedicated active owners retain the existing entry/submit guards; retired matrix adapters do not regain authority.
9. Active producer -> workorder/EV/runtime summary -> verifier handoffs must preserve exact date, identity, source generation/hash and authority. Missing mandatory active handoffs fail; OFF/retired artifact absence does not. Repair acceptance closes on causal/contract/consumer evidence, not unrelated EV or promotion floors.
10. Canonical runtime label contracts are part of source quality. Prompt/schema producers may emit only declared English labels, and consumers must normalize only documented legacy aliases. Any undefined label is an explicit fail condition that blocks downstream promotion until the contract or producer is deliberately updated with tests.
11. Daily source-quality/incident observations and rolling/cumulative economic approval serve different decisions. Isolate invalid rows/windows/cohorts when their identity is reliable; reserve whole-input blocks for missing/invalid global contracts or unisolatable loss. Keep complete real full-fill outcomes distinct from partial, sim/probe and counterfactual samples.

### 3.3 Canary, Cohort, And Live Change Principles

1. Only one live canary is allowed within the same stage. Bounded multi-arm canaries within the same family are allowed only when arm-level provenance, allocation, and rollback guards are closed.
2. Canary-to-live conversion must close `N_min`, primary EV improvement, no rollback guard breach, applied/not-applied cohort comparison, no cross-contamination, and restart/rollback path.
3. New/supplemental alpha axes must not open as shadow-only. Support axes that do not change real order/exit decisions, such as transport/schema, report-only decision support, and counterfactual enrichment, are allowed only when documented as observe/report-only.
4. Sim/probe/combined/counterfactual evidence cannot alone approve real execution quality or broker enablement. Swing remains OFF; archived LDM approval terms are not a current conversion path.

### 3.4 Document And Execution Ownership

1. Plan Rebase owns only current principles and active/open decisions.
2. Daily checklists own executable work, absolute times, `Due`, `Slot`, `TimeWindow`, and `Track`.
3. Report traceability and threshold README own automation artifacts, consumer contracts, and apply contracts.
4. Completed old checklist items are evidence, not current OPEN owners.
5. Baseline documents such as README, runbook, Plan Rebase, prompt, and AGENTS are updated only when the user explicitly asks.
6. Keep those document updates separate from runtime/order/provider/bot/threshold changes. When needed, close them through first edit, second review, final supplement, and parser validation.
7. Historical content is not accumulated in the current snapshot; preserve it in archive or execution-delta.
8. AI runs parser validation after document changes. The user manually runs Project/Calendar sync with the standard command.
9. Reopen a completed review only for a new reproducible defect, changed contract or failed mandatory consumer. Natural sample/EV absence alone leaves the existing natural-acceptance owner OPEN, not the implementation owner.

## 4. Automation-Chain Baseline

| Stage | Current Baseline | Live Impact |
| --- | --- | --- |
| `R0_collect` | Collect pipeline event, threshold compact event, DB completed trade, and monitor snapshot. | None |
| `R1_daily_report` | Generate Sentinel, panic, performance, and daily threshold reports. | None |
| `R2_cumulative_report` | Generate rolling/cumulative cohort and owner baseline. | None |
| `R3_manifest_only` | Create candidate families and source bundles without env mutation. | None |
| `R4_preopen_apply_candidate` | Check deterministic, AI, source-quality, and same-stage guards. | Pre-change stage |
| `R5_bounded_calibrated_apply` | Apply only guard-passing families to the next preopen runtime env. | Yes |
| `R6_post_apply_attribution` | Submit selected/applied/not-applied cohort, daily EV, and approval summary. | None |

The automation chain reuses existing source bundles instead of adding observation axes indefinitely. Preferred sources are `buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, and `performance_tuning` for BUY; raw candidate/submit/fill/terminal lineage and dedicated strategy replay for current lifecycle evidence; `holding_exit_observation`, `post_sell_feedback`, `trade_review`, and `holding_exit_sentinel` for holding/exit; the existing exact AI `investor_flow`/`program_flow` snapshot for supply-demand context; and `panic_sell_defense` for panic context. The dedicated `institutional_flow_context` report and retired ADM/LDM artifacts are archive-only and cannot be reopened through an operator override. One-off follow-up records remain archive/reference material, not current automation-chain source bundle owners.

Surviving sim prior/control-tower artifacts remain source-only and non-priority for detailed tuning. Missing retired LDM inputs must not trigger restoration. Check installed flags and actual consumer scope; do not label the whole surviving control tower retired.

Unorganized report-only/legacy artifacts are managed by `calibration_source_bundle.report_only_cleanup_audit`. This audit is a `source_quality_gate`; it surfaces cleanup candidates through `cleanup_candidate_count`, but because it is `source_quality_only`, it has no authority to change threshold/env/order/bot/provider.

`Metric Decision Contract` is owned by [report-based-automation-traceability](./report-based-automation-traceability.md#26-metric-decision-contract). A new report or metric that does not satisfy this contract is source-quality/instrumentation backlog, not a threshold candidate.

## 5. Current Runtime And Observation Axes

| Area | Current State | Forbidden Use |
| --- | --- | --- |
| scalping entry | Score 50 fallback/neutral is held as `blocked_ai_score`. Existing score cutoff is a baseline prior. Selected `score65_74_recovery_probe` keeps its family id but uses the current score60 floor and feature-qualified score60-74 entry unlock. The current `WAIT6579_PROBE_CANARY` cap defaults are unlimited for separate probe budget/quantity (`0` means use normal new-buy sizing). OpenAI analyze_target engine-level min-interval must not create a score50 fallback blocker; it waits briefly and then makes the real model call. Submit drought is surfaced by `BUY Funnel Sentinel` as `SUBMIT_DROUGHT_CRITICAL`. `latency_classifier_runtime_profile` is only the DANGER/stale/broker runtime safety/telemetry label; its independent postclose recommendation and PREOPEN candidate path are retired. Runtime `EntryPolicy` sends `SAFE` and `CAUTION` to normal submit after slippage check. Fresh spread-only relief remains owned by the separate explicit operator lock. | Must not bypass threshold/provider/broker submit guards. Stale/liquidity/overbought/DANGER latency/price freshness pre-submit safety outranks entry tuning. Latency diagnostics cannot mutate thresholds or bypass hard safety, stale quote, broker/account/order/quantity/cooldown guards. |
| Opening Rotation one-share | Permanently retired under `opening_rotation_full_retirement_20260814`. Scanner ownership, protected watch capacity, new mechanical BUY authority, margin exception, postclose tuning, and PREOPEN policy production/verification are removed. Existing reports, runtime artifacts, and events are archive/audit evidence only. Receipt/exit parsing for an already-owned legacy position remains custody compatibility and grants no new entry or reactivation authority. | A former env key, dated policy, candidate artifact, or archived report cannot reactivate the family. Any future rotation concept requires a new workorder, namespace, evidence contract, runtime guard, and explicit operator authority; reuse of `opening_rotation_*` live authority is forbidden. |
| lifecycle decision matrix | RETIRED: policy/context/discovery/bridge producer and PREOPEN consumer disabled permanently; archived data is audit-only. | Preserve raw lineage, dedicated strategy EV and all broker/hard-safety guards. |
| greenfield real environment authority | RETIRED with scalping ADM/LDM; runtime adapter is no-op and archived candidates have no PREOPEN authority. | Do not restore bucket allowlists, env or apply bridge from historical artifacts. |
| institutional flow context | RETIRED with its sole scalping ADM/LDM consumer. The scheduled postclose producer and current EV/runtime-summary consumption are disabled; historical artifacts and the explicit CLI are archive/offline inspection only. Existing exact AI `investor_flow`/`program_flow` collection remains the active, non-duplicated context source. | Archived `institutional_accumulation_score`, former join-rate labels, or an inherited wrapper override cannot decide BUY/scale-in/exit, restore a consumer, bypass broker guards, or change threshold/provider/runtime env. |
| microstructure reaction context | Context schema v2/delivery telemetry v3 separates computed, payload included, confirmed sent, internal consumed and cache reuse per evaluation/attempt. Uses canonical quote freshness; invalid dates are excluded. Finite exact outcome 20 is diagnostic interpretation only. | No separate positive-EV runtime candidate or PREOPEN waiting queue. Source-only instrumentation gaps are distinct from economic/live approval. |
| entry price | `dynamic_entry_price_resolver_p1` plus `dynamic_entry_ai_price_canary_p2`; if passive probe submit revalidation is stale, block before submission. | Direct `ws_data.curr` chase and stale quote submit are forbidden. |
| holding/exit | Active dedicated holding/exit overrides and `scalp_trailing_take_profit` retain their target-date contracts. `soft_stop_whipsaw_confirmation` remains OFF/source-only; `holding_flow_ofi_smoothing` remains ON within its guards. Holding/Exit ADM and matrix biases are retired. SCALP preset TP is not a profit-taking owner; legacy stop provenance remains safety compatibility only. | No hard/protect/emergency/account/order/cooldown/quantity bypass. Report evidence cannot restart a process or enable a family. |
| scale-in/position sizing | Keep scale-in price resolver and dynamic quantity safety. `position_sizing_dynamic_formula` remains the upstream affordability owner for every active `SCALPING/SCALP` new buy, Rising Missed Scout, AVG_DOWN/PYRAMID, and scalping simulation. Source-count/time/venue classification selects fixed tiers `10%/15%/20%/25%/25%` under `entry_type_5stage_cap25_v1`; NXT, unknown venue, invalid/missing source, and unrecoverable original-entry context fail closed to tier 1 (10%). Scale-in reuses the initial tier. The 95% safe budget, minimum one-share floor, and downstream position/stage/broker caps remain. | Score-linear 10-30%, retired Opening Rotation margin/private-ratio authority, Rising Missed 400,000 KRW cap, sim 100% default, and `entry_armed_ratio` have no current sizing authority. Sim/probe real-order authority and hard-safety bypass are forbidden. An unapproved bot restart remains forbidden. |
| sim lifecycle | Surviving candidate-window, AI-budget, prior/control-tower and sim outcome sources keep their installed scope. LDM-derived scale-in/discovery/bridge is retired; sim is not current detailed-tuning priority. | `actual_order_submitted=false`, `broker_order_forbidden=true`; no real execution claims, BUY/order alerts or provider/bot/threshold/cap authority. |
| swing dry-run | Operator OFF; no due postclose/approval freshness requirement while disabled. | No implicit reactivation or broker trial. |
| swing strategy discovery sim | Operator OFF; existing artifacts are historical research, not current candidates. | No sim collection expansion, live conversion or runtime mutation from this document. |
| swing live conversion | No current active conversion workstream; legacy trial paths are not runtime owners. | No real authority from archived sim/LDM evidence. |
| AI route | Main live AI route is OpenAI except explicit endpoint-specific overrides. `entry_price` uses Bedrock Qwen3 32B primary with Nova Lite v2 failback, no third OpenAI fallback and defensive close if both Bedrock calls fail. Other Tier2 endpoints use OpenAI Responses WS; Gemini/DeepSeek fallback requires explicit env behavior, OpenAI initialization failure or non-operational analysis scope. `holding_flow` keeps Bedrock Nova Lite v2 primary with OpenAI failback. Removed Bedrock shadow/comparison surfaces are not active report inventory. AI input v2/call-policy surfaces remain disabled-by-default builders and bounded refresh flags unless a later owner enables them. | Provider route confirmation and AI input/cadence instrumentation must not be used as evidence to change thresholds, order price, quantity, or bot state. Endpoint allowlist, failback, audit rows, and disabled v2 input flags must remain separate from strategy edge judgment. |
| Sentinel/panic | BUY/HOLD/EXIT/panic sell are default report-only source bundles. `scalp_sim_panic_lifecycle` is a scalping sim-only actuator with `actual_order_submitted=false` and `broker_order_forbidden=true` that consumes panic-sell risk-regime context. It can apply `panic_level>=2` entry block and holding partial/full exit, with scale-in block/holding defense kept as separate sim actuators. `panic_level=1` market breadth risk-off entry is not a fixed hard gate; it is an observation regime, and bottoming state remains a `BOTTOMING`/`WEAK` feature. | Real automated selling, TP/trailing/threshold/provider/bot restart changes are forbidden. Level-1 risk-off/bottoming observation is sim-only and has no authority to change broker submit, Telegram BUY alerts, or real-entry relaxation. |
| System Error Detector | Report-only detector and gated filesystem maintenance detector are separated. | Strategy threshold/order changes are forbidden. |

## 6. Quantitative Targets And Guards

| Metric/Guard | Baseline | Action |
| --- | --- | --- |
| `N_min` | Family-specific decision floor, not a universal repair gate. | Below-floor economics is `hold_sample`, not measured failure or permission for cap/quantity reduction. Apply only the active family's explicit bounded carry/rollback contract. |
| `primary_ev` | Family contract's EV primary metric. | Primary evidence for apply/promotion. |
| `diagnostic_win_rate` | Supporting win-rate/consistency metric. | Standalone apply is forbidden. |
| `simple_sum_profit_pct` | Simple PnL sum. | Must not be named or used as EV. |
| `source_quality_gate` | Stale/missing/duplicate/provenance gap. | Exclude from threshold candidates if gate is not met. |
| `canonical_label_contract` | Internal labels emitted by prompts, schemas, JSONL/log-derived reports, and source-quality audits. | Unknown labels fail source quality; do not silently bucket or auto-promote them. |
| `execution_quality_real_only` | Real broker order/receipt/fill quality. | Must not be replaced by sim/probe/combined. |
| `safety_veto` | Severe loss, order failure, provenance damage, stop delay, or same-stage conflict. | May block/rollback even when daily-only. |
| `window_policy` | Separation of `daily_only`, rolling, cumulative, and post-apply version windows. | Daily-only edge apply is forbidden. |
| `runtime_mutation_guard` | An operator-directed intraday change is limited to one existing `bounded_tunable` axis, one explicit KRX or NXT cohort, one stage owner, recorded values/provenance, rollback, and immediate attribution. | Reject hard-safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, requested-quantity increase, or cross-venue/common-runtime changes; otherwise apply the recorded operator override contract immediately. |

## 7. Current Open State Summary

This section owns workstream boundaries, not dated completion history. Resolve executable OPEN owners from the current KST checklist, using actual Due/Source/Acceptance and stable IDs. Completed/ transferred older rows remain evidence only. Policy selection and live consumption require exact-date artifacts and current PID receipts; explicit approved overrides retain their own scope, persistence/expiry and rollback. Missing current evidence is not permission to reuse an old state snapshot.

| Workstream | Current Owner/State | Next Decision Path |
| --- | --- | --- |
| postclose closure | Source-generation/identity/cost and strict summary handoff contracts in §3.2; operational failures precede recommendation work. | Current recovery/workorder owner -> affected producer/last consumer -> tower/checklist/strict -> controller/finalization. Irrecoverable history stays excluded; no unchanged replay loop. |
| threshold auto apply | Active family-specific deterministic/AI guards, exact-date candidates and PREOPEN receipts. | Source -> selection -> PID -> R6. No env writes, lock release or restart from document/code PASS. |
| entry funnel / scanner recall | Entry gate/recheck and submit-drought controller own exact attempts/cycles, upstream/broker terminals and nonblocking fallback. Scanner discovery, post-promotion consumption and downstream submit have distinct denominators. | Valid same-scope recent 3-trading-day history -> controller -> PREOPEN/PID -> submit/fill/terminal/net EV. Independent market-wide recall source required; diagnostic repair adds no positive-EV/all-horizon gate. |
| entry price quality | P1/P2 resolver and passive probe submit revalidation; `pre_submit_price_guard` is downstream quote quality, not the primary latency drought owner. | Family-specific price-quality attribution. Stale quote submit remains blocked. Cancel timeout belongs to §1's standalone family. |
| widget / episode recommendations | Independent source/policy, profile, order/leg and custody owners. Use native recommendation IDs and separately authorized application receipts. | Current checklist acceptance -> exact policy/preflight/loader/PID -> signal/terminal/net evidence. Frozen canonical/projection/approval ledgers are not additive. |
| Samsung / low-price entry tuning | Actual-policy/as-of custody and broker-notional EV; Samsung morning baseline-only. Rise/rebound/delay recipes belong to `machine_entry_timing_tuning`. Default new episodes retain two separate 10-share legs; explicit approved overrides and legacy inventory retain their own quantities. | Current profile/target/validity and source/economic/PREOPEN contracts. No subset-only tightening or inferred profile/quantity/safety authority. |
| machine timing / exit | Source readiness, signal-time windows and economic acceptance are separate. Missing ordered/route/epoch source uses the owner's baseline carry. Approved persistent supplemental exits retain their distinct deployment/policy/custody/rollback contract. | Current machine lifecycle/startup owners and [postclose §1.2–§1.3](./postclose-tuning-result-review-task-instructions.md). Timing success does not activate a new adaptive-exit family; existing holdings are not automatically enrolled. |
| holding/exit and sizing | §5 owns dedicated holding-flow/trailing and `position_sizing_dynamic_formula`; whipsaw OFF/source-only, OFI smoothing ON within guards. Formula research compares selected `entry_type_5stage_cap25_v1` with `flat_10_fallback`, judged by notional-weighted or source-quality-adjusted EV. | Exact-path rolling economics and target-date receipts; old score-linear/correction candidates are archive/parser compatibility only. Report candidates cannot mutate runtime. |
| fixed threshold roles | `hard_safety`, `baseline_prior`, `bounded_tunable`, `legacy_archive` (§3.2). Legacy price-field protect-hard is removed; `hard_stop_price` is schema/S15 TTL compatibility only. | No legacy exit, scale-in, overnight, report-taxonomy or live-auto authority. |
| AI transport | §5 endpoint-specific routes and disabled-by-default input/cadence builders, unless enabled by a later authorized owner. | Current provider receipt validation is separate from threshold/order/quantity/bot authority or strategy EV. |
| AI decision-quality improvement | Continuous exact-payload R0–R3 research; self-hashed paired materialization -> calibration -> offline optimizer, isolated by stage/venue/session/prompt/contract. Valid partial-success rows may support offline learning while full-report gates remain closed. | Late follower: terminal detailed -> calibration -> frozen same-day optimizer -> provider0 metadata rebind -> holding manifest -> consumer hashes. Legacy runtime stays `LEGACY_RUNTIME_AUTHORITY_ENABLED=False`; samples cannot enable it. Supported KRX V2.14/V2.15 use separate `entry_setup_live_policy` review/PREOPEN/receipt; NXT/holding/unregistered candidates retain their own authority boundary. |
| scalping AI multi-timeframe context | The 3/5/15-minute completed-bar bundle, session VWAP, 5/15-minute opening range, previous-day lines, and market/sector context remain source-only observation and external-validation inputs until the next `PREMARKET_KRX_LIKE` final validation. The live integration owners are the existing stage-specific schemas: `entry_candle_context_v1` for entry-side calls and `holding_decision_context_v1` for holding/scale-in/exit/overnight calls. Both consume the same venue/session-normalized source and shared derived-feature version `scalping_multi_timeframe_context_v1`; that version is not a third parallel model payload. The user-directed target is one binary validation followed immediately by full live promotion across every scalping symbol, every active market session (`PREMARKET_KRX_LIKE`, `KRX_REGULAR`, `NXT_REGULAR_OVERLAP`, `NXT_AFTERMARKET`), and every applicable live scalping AI endpoint. This is not a canary, session-limited, partial-cohort, endpoint-limited, or call-rate rollout. | The gate is binary: final PREMARKET validation pass means global full application from the validation completion timestamp; failure means no promotion. The reviewed target-date promotion artifact records both context schemas, their shared `input_bundle_version`, exact payload/trace provenance, `provider!=none`, comparable required-field `MISMATCH=0`, completed-bar-only aggregation, fresh conflict-free source quality, and rollback. Once passed, no additional KRX, NXT, stage, or endpoint promotion gate is required. Each call still uses its own venue/session and stage-appropriate context without cross-venue or cross-stage substitution. Threshold, provider route, order price/quantity, broker/account/order/cooldown, hard/protect/emergency safety, and bot-state authority are unchanged. |
| scanner lookup-attention | Marginal snapshot opportunity-cost CF and real full-fill base/holdout are separate; immutable PREOPEN receipt and resource-pair provenance matter. | Natural source pairs -> policy -> next PREOPEN receipt -> PID/R6. Resource duplicate floors are diagnostic; active economic guards remain. |
| panic lifecycle | `panic_sell_defense` is report-only context. `scalp_sim_panic_lifecycle` separates market/symbol regimes; PANIC_CONFIRMED/LIQUIDITY_BROKEN prioritize sim defense, level-1 risk-off and BOTTOMING/WEAK remain observation features. | `panic_lifecycle_actuator`/`panic_entry_freeze_guard` are not standalone live-selectable families. Keep `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`; no real cancel/exit/threshold/provider/bot authority. |
| OFF / retired / sim | §5/§8 define exclusions and surviving source-only owners. | Missing disabled/retired artifacts create no restoration or promotion work; verify actual leaks only. |
| system health / metric quality | Detector, wrapper terminal and source-quality contracts; §2 declares metrics and canonical-label authority. | Operational evidence is separate from strategy effect. Invalid labels require producer/schema/parser correction before affected input promotion. |

## 8. Excluded From Current Baseline

1. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`, legacy latency composite, and closed shadow axes are archive-based historical/reference.
2. Completed `[x]` items in old daily checklists are not current owners. Current owners are owned by §7 of this document and open items/runtime state in the current daily checklist.
3. Operational automation evidence such as cron, wrapper, manifest, parser, and report freshness is separate from strategy effect or live approval evidence.
4. Scalping ADM/LDM/bucket/greenfield, dedicated institutional aggregation, WAIT6579 standalone entry bridge, independent latency recommendation/PREOPEN calibration and panic-buying are retired; Swing is OFF and sim is not current detailed-tuning priority. Completed contract reviews stay closed unless new defects or contract changes are demonstrated.
5. `combined` sim+real diagnostics may be used for operational observation, but not for real execution quality or real-order approval.
6. New report-only artifacts are not automation-chain inputs unless they have source bundle consumer, metric contract, and forbidden uses. If the user declares a separate `operator_runtime_override`, record artifact output and runtime env override separately, with rollback env and safety guard priority.
7. The previous-limit-up rotation observation family (`upper_limit_watch`, its candidate/report/counterfactual/bounded-live artifacts, and `UPPER_LIMIT_LIVE_RECLAIM`) is permanently retired by explicit operator direction. Historical artifacts are archive/audit evidence only and have no producer, verifier, runtime slot, scanner handoff, live-auto promotion, or reactivation path. A future previous-limit-up strategy requires a new workorder, namespace, evidence contract, and runtime guards.

Retired panic-buying cannot be restored through an operator override. A future rebound/exhaustion strategy requires a new workorder, namespace, evidence contract and guards. Runtime latency safety, separately approved spread-relief locks, raw WAIT6579 provenance and exact AI investor/program context remain separate surviving contracts.

## 9. Delta/Q&A Routing

| Document | What It Stores | Why It Is Excluded Here |
| --- | --- | --- |
| [plan prompt](./plan-korStockScanPerformanceOptimization.prompt.md) | Lightweight pointer for next session entry. | Rebase owns the core baseline. |
| [execution-delta](./plan-korStockScanPerformanceOptimization.execution-delta.md) | Date-based task registry, expired schedules, same-day pivots, and effect records. | Rebase does not accumulate historical progress. |
| [qna](./plan-korStockScanPerformanceOptimization.qna.md) | FAQ to prevent automation-chain misjudgment, metric authority, and proposal/apply separation. | Stores repeated policy only. |
| Daily checklist | Time-specific work, Due/Slot/TimeWindow, and complete/incomplete state. | Auto-parsing and Project/Calendar owner document. |
| audit/report | Externalized copies, detailed numeric evidence, and review-perspective explanations. | Rebase keeps approval criteria only. |
| [archive](./archive/) | Closed observation axes, old workorders, and pre-renewal original text. | Excluded from current active/open decisions. |

## 10. Key Reference Documents

| Document | Role |
| --- | --- |
| Current daily stage2 checklist (`docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`) | Current daily preopen/intraday/postclose execution table and postclose auto-generated items. |
| [postclose review inventory](./audit-reports/2026-09-05-postclose-work-inventory.md) | Stable review indices, completed review evidence and separate natural acceptance; not execution authority. |
| [postclose monitoring instructions](./postclose-tuning-result-review-task-instructions.md) | Explicitly invoked monitoring/recovery and safe-scope fixed-point implementation procedure. |
| [report-based-automation-traceability.md](./report-based-automation-traceability.md) | R0-R6 ladder, source bundle, Metric Decision Contract, and forbidden-use lines. |
| [data/source_quality/clean_baseline_policy.json](../data/source_quality/clean_baseline_policy.json) | Clean tuning data baseline policy. Data before `2026-06-05T00:00:00+09:00` is archive-only and forbidden as current tuning decision input. |
| [data/threshold_cycle/README.md](../data/threshold_cycle/README.md) | Threshold collector/report/apply plan/runtime env operating method. |
| [data/report/README.md](../data/report/README.md) | Regular report inventory and Markdown-missing candidates. |
| [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md) | Lightweight session-start pointer. |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | Changes from the original plan, date-based history, and closed-axis records. |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | Repeated decision criteria and review Q&A. |
| [archive](./archive/) | Closed observation axes, pre-renewal original text, runtime override records, and other historical evidence excluded from current active/open decisions. |
