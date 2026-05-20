# Sim Data Usage Audit - 2026-05-20

- generated_at: `2026-05-20T20:39:51+09:00`
- scope: `scalping sim -> Entry ADM -> Lifecycle Decision Matrix -> threshold/report consumers`
- runtime_effect: `false`
- decision_authority: `postclose_audit_only`
- forbidden_uses: `runtime_threshold_apply`, `order_submit`, `provider_route_change`, `bot_restart`
- overall_state: `YELLOW`
- blocked_stage: `historical_source_quality_gap`

## Post-Fix Verification

- verified_at: `2026-05-20T21:09:49+09:00`
- post_fix_state: `YELLOW`
- runtime/order/provider/bot mutation: `none`
- postclose verification after initial fix: `pass`
- current postclose verification after OpenAI correction regeneration: `pass`
- current blocking issue: `none`

The initial `RED` audit finding below is preserved as the pre-fix diagnosis. After the bugfix and artifact regeneration, the normal scalp sim source is no longer absent from LDM:

| Check | Post-fix result |
| --- | ---: |
| Entry ADM full rows | `rows=652`, `examples=50`, `total_candidates=652` |
| LDM entry source | `source_field=rows`, `source_rows=652` |
| LDM submit policy | `sample=239`, `joined_sample=238`, `source_quality_gate=pass` |
| LDM holding policy | `sample=238`, `joined_sample=238`, `source_quality_gate=pass` |
| LDM retained rows | `7155`, no `rows[:2000]` cap |
| LDM dropped rows | `{}` |
| runtime approval summary | `lifecycle_matrix_status=pass`, `lifecycle_matrix_ready_for_bounded_apply=true` |

Remaining source-quality caveat: `observation_source_quality_audit_2026-05-20` is `warning`, not `pass`, because historical raw events already written before this fix have provenance gaps:

- `scalp_sim_entry_armed`: `runtime_effect` missing in `238/238` historical rows.
- `scalp_sim_sell_order_assumed_filled`: `decision_authority` missing in `75/238` historical rows.

The LDM/report routing bug is fixed. The residual warning is a source-quality guard doing its job on pre-fix raw data; future `scalp_sim_entry_armed` logging now includes `runtime_effect=simulated_entry_armed_only`.

## Daily/Rolling and Full-Chain Re-Audit

- verified_at: `2026-05-20T21:27:52+09:00`
- sim_data_consumption_state: `YELLOW`
- postclose_chain_state: `pass_after_repair`
- runtime/order/provider/bot mutation: `none`
- repaired_at: `2026-05-20T21:45:00+09:00`

### Daily vs Rolling Use

판정: `YELLOW`

The threshold-cycle daily artifact was stale after the first LDM fix and still showed the old `lifecycle_decision_matrix_runtime` sample path. After regenerating the daily threshold-cycle report, the LDM candidate now reflects the repaired source size:

| Check | Current result |
| --- | ---: |
| LDM source sample in `threshold_cycle_2026-05-20` | `7155` |
| LDM retained rows | `7155` |
| LDM cap accounting | `dropped_rows_by_source={}` |
| `window_policy_audit.status` | `pass` |
| LDM secondary `rolling_5d` sample | `7155`, ready |
| LDM secondary `cumulative` sample | `7155`, ready |

The current daily/rolling policy is mostly being applied: non-daily families have rolling or cumulative denominator checks, and the LDM direct report is not being treated as real execution evidence. The remaining ambiguity is that `lifecycle_decision_matrix_runtime` uses `primary=latest_report` with `daily_only_allowed=false`; its primary snapshot is not populated, but secondary `rolling_5d` and `cumulative` are ready. That is acceptable only as a source-bundle or bounded-candidate input, not as standalone live-apply proof.

Consumer caveat resolved: `runtime_approval_summary_2026-05-20` now contains one `lifecycle_decision_matrix_runtime` row, sourced from the repaired LDM path with `sample.count=7155` and `joined=6109`. The stale `sample.count=2000` row is no longer rendered as a separate approval row.

Postclose caveat resolved: the postclose AI correction artifact was regenerated with OpenAI (`gpt-5.4-mini`) and strict schema parsing. `threshold_cycle_postclose_verification_2026-05-20` is now `pass` with `ai_status=parsed`, predecessor integrity `pass`, and no log issues.

### Simulation Collection and Consumption Sweep

판정: `YELLOW`

The raw 5/20 pipeline contains `70475` simulation-like events across `36` stages. Normal scalping sim collection is present and the repaired LDM now consumes the main lifecycle rows:

| Layer | Current result |
| --- | ---: |
| raw sim entry armed | `238` |
| raw sim virtual pending | `238` |
| raw sim assumed buy fill | `238` |
| raw sim holding started | `238` |
| raw sim assumed sell fill | `238` |
| LDM submit | `sample=239`, `joined_sample=238` |
| LDM holding | `sample=238`, `joined_sample=238` |
| LDM scale-in | `sample=4795`, raw normal scale-in rows `12` unfilled |
| LDM exit | `sample=740`, `joined_sample=659` |

Remaining coverage gaps found by the sweep:

1. Entry ADM now ingests `scalp_sim_entry_ai_price_skip_order` (`6` raw events) as `SKIP_PRE_SUBMIT_SAFETY`.
2. Source-quality contracts now cover normal sim lifecycle stages, sim holding AI budget stages, and panic/euphoria sim risk-context stages. Current warnings are historical 5/20 raw provenance gaps, not silent omissions.
3. Swing probe and swing sim stages are now in the threshold-cycle stage registry under `swing_strategy_discovery_sim` source observability.
4. `runtime_approval_summary` now dedupes `lifecycle_decision_matrix_runtime` by using the direct LDM summary row when available, instead of also rendering the stale calibration decision row.

Latest control state:

- state: `YELLOW`
- blocked_stage: `historical_source_quality_gap`
- impact: repaired sim consumption is visible in LDM, threshold-cycle daily artifacts, runtime approval summary, and postclose verification. Remaining warnings identify pre-fix raw events with missing provenance fields.
- next_action: keep source-quality warnings as attribution/provenance blockers for the affected historical stages; verify future intraday events include `sim_record_id`, `entry_adm_candidate_id`, `runtime_effect`, and `decision_authority` under the new contracts.

## Pre-Fix Executive Judgment

오늘 스캘핑 sim 데이터 자체는 생성됐다. `submit이 없었다`가 아니라 `LDM submit/holding stage가 sim 데이터를 먹지 못했다`가 맞다.

이 결함은 단순 표시 오류가 아니다. 5/20 LDM은 `submit=0`, `holding=0`으로 정책을 만들었고, Entry ADM도 LDM에 50개 example만 전달됐다. 따라서 5/20 LDM의 `entry promote_ready`, `submit hold_sample`, `holding hold_sample` 결론은 다음 튜닝 판단의 primary source로 쓰면 안 된다.

## Pre-Fix Evidence Snapshot

| Layer | Evidence | Judgment |
| --- | ---: | --- |
| raw scalp sim virtual entry | `scalp_sim_entry_armed=238` | present |
| raw scalp sim virtual submit | `scalp_sim_buy_order_virtual_pending=238`, `scalp_sim_buy_order_assumed_filled=238` | present |
| raw submit revalidation | `warning=221`, `block=0` | present |
| raw scalp sim holding/exit | `holding_started=238`, `sell_order_assumed_filled=238` | present |
| sim post-sell join | completed `238`, joined `238`, pending `0` | pass |
| Entry ADM | candidates `652`, joined `154`, status `pass` | usable with caveat |
| LDM submit policy | sample `0`, joined `0`, `hold_sample` | invalid coverage |
| LDM holding policy | sample `0`, joined `0`, `hold_sample` | invalid coverage |
| LDM entry source from ADM | source rows `50` vs ADM candidates `652` | truncated |
| LDM total source rows | source summaries at least `6077`, retained `2000` | silently capped |
| source-quality audit | no `scalp_sim_*` stage contract entries found | coverage gap |

## Pre-Fix First-Pass Audit

### 1. Input Health

판정: `YELLOW`

Raw sim collection is present and internally consistent. The threshold EV report captured the key sim lifecycle counts:

- `scalp_sim_entry_armed=238`
- `scalp_sim_buy_order_virtual_pending=238`
- `scalp_sim_buy_order_assumed_filled=238`
- `scalp_sim_holding_started=238`
- `scalp_sim_sell_order_assumed_filled=238`
- `scalp_sim_entry_submit_revalidation_warning=221`
- `scalp_sim_entry_submit_revalidation_block=0`

The post-sell join also closed cleanly: `completed_sample=238`, `joined_completed=238`, `pending_completed=0`.

The caveat is source-quality oversight. `observation_source_quality_audit_2026-05-20.json` has no `scalp_sim_*` stage contract rows, so sim submit/holding provenance is visible in threshold EV but not independently guarded by the source-quality audit.

### 2. Entry ADM Usage

판정: `YELLOW`

Entry ADM itself is using some sim data. It reads scalp entry, pre-submit, and selected scalp sim stages from `src/engine/scalp_entry_action_decision_matrix.py`:

- included: `scalp_sim_entry_armed`
- included: `scalp_sim_entry_submit_revalidation_warning`
- included: `scalp_sim_entry_submit_revalidation_block`
- included: `scalp_sim_buy_order_assumed_filled`
- included: `scalp_sim_sell_order_assumed_filled`
- not included: `scalp_sim_buy_order_virtual_pending`

5/20 Entry ADM output:

- status: `pass`
- total_candidates: `652`
- joined_sample: `154`
- post_sell_evaluation rows: `238`
- action_counts: `NO_BUY_AI=645`, `BUY_NOW=2`, `WAIT_REQUOTE=4`, `SKIP_SOURCE_QUALITY=1`
- runtime_effect: `false`
- decision_authority: `entry_advisory_prompt_context_only`

문제는 Entry ADM report가 full row artifact를 LDM에 제공하지 않고 `examples`만 남긴다는 점이다. LDM `_load_entry_rows()`는 `payload.get("examples")`만 소비한다. 그래서 652개 ADM 후보 중 LDM에 들어간 것은 50개뿐이다.

Impact: Entry ADM 단독 report는 참고 가능하지만, LDM 안에서의 Entry ADM 반영도는 낮다. 5/20 LDM의 `entry sample=442`, `promote_ready=true`는 ADM 전체 652개를 완전 반영한 결과가 아니다.

### 3. LDM Submit Usage

판정: `RED`

Raw sim submit-like events are present, but LDM submit rows are absent.

Evidence:

- raw/reported sim virtual pending: `238`
- raw/reported sim assumed fill: `238`
- raw/reported sim submit revalidation warning: `221`
- LDM `submit` policy: `sample=0`, `joined_sample=0`, `source_quality_gate=hold_sample`

Root cause:

- `src/engine/lifecycle_decision_matrix.py` has stage mapping for `entry_submit_revalidation_warning`, `entry_submit_revalidation_block`, `pre_submit_*`, `latency_pass`, `latency_block`, and `order_bundle_submitted`.
- The LDM source loader list does not include a normal `scalp_sim_entry_submit_pipeline_events` loader.
- Current LDM sources include `scalp_sim_scale_in`, `scalp_sim_overnight`, and `scalp_sim_panic`, but not normal sim virtual submit.

Impact: LDM currently cannot answer whether `ALLOW_SUBMIT` or `NO_CHANGE` is better for sim-derived submit decisions. The 5/20 `submit hold_sample` is a routing gap, not a real absence of submit samples.

### 4. LDM Holding Usage

판정: `RED`

Raw sim holding data exists, but LDM holding rows are absent.

Evidence:

- threshold EV sim holding started: `238`
- sim holding live AI call: `1754`
- sim holding deferred: `715`
- LDM `holding` policy: `sample=0`, `joined_sample=0`, `source_quality_gate=hold_sample`

Root cause:

- LDM source loaders do not ingest `holding_exit_decision_matrix_YYYY-MM-DD.json`.
- LDM has an overnight loader, but 5/20 overnight rows are `0`.
- Normal scalp sim holding snapshots / holding AI review / deferred review are not mapped into `stage=holding`.

Impact: LDM cannot currently evaluate `HOLD` vs `EXIT` from normal sim holding behavior. Exit rows exist through post-sell and panic/euphoria sources, but holding-stage policy is not populated.

### 5. LDM Source Completeness

판정: `RED`

LDM source summaries imply at least `6077` candidate rows before truncation:

- Entry ADM examples: `50`
- sim post-sell: `238`
- wait6579: `25`
- scalp sim scale-in: `12`
- scalp sim overnight: `0`
- scalp sim panic/euphoria: `5752`

LDM retains only `2000` rows via `rows = rows[:2000]` and emits no truncation warning. This can bias policy entries toward earlier loader order and early panic/euphoria rows while hiding source coverage loss.

Impact: LDM summary says `status=pass`, but the policy distribution is not a full-source matrix. `total_rows=2000` should be interpreted as capped retained rows, not complete lifecycle source coverage.

### 6. Runtime Safety Separation

판정: `PASS`

The sim data is not being misused as real execution evidence in the checked artifacts.

- `scalp_simulator.post_sell_join.runtime_effect=false`
- `scalp_simulator.post_sell_join.decision_authority=sim_equal_weight_observation_only`
- Entry ADM `runtime_effect=false`
- LDM `runtime_effect=false`
- LDM forbidden uses include `real_execution_quality_from_sim_only`
- real `order_bundle_submitted_events=0` remains separate from sim virtual submit/fill

This part is working: the issue is underuse/misrouting of sim data inside LDM, not unsafe conversion into broker submit.

## Pre-Fix Second-Pass Audit

### Cross-Check A. Did the first pass confuse real submit and sim submit?

판정: `pass`

The report separates `order_bundle_submitted_events=0` from `scalp_sim_buy_order_virtual_pending=238` and `scalp_sim_buy_order_assumed_filled=238`. The issue is not lack of sim submit; it is LDM submit ingestion.

### Cross-Check B. Is Entry ADM actually broken?

판정: `partially overstated in first suspicion; final state YELLOW`

Entry ADM does consume sim data and produces a valid report-only matrix. The defect is downstream: LDM consumes only the ADM report `examples`, not the full 652 candidate rows. Entry ADM is not the primary broken component, but its output contract is insufficient for LDM.

### Cross-Check C. Is LDM `submit=0` explainable by sample filtering or source authority?

판정: `fail`

No. The source events exist, carry sim authority, and are part of the threshold-cycle report. Current LDM has no normal scalp sim submit loader, so `submit=0` is not a meaningful sample result.

### Cross-Check D. Is LDM `holding=0` expected because only exit is outcome-labeled?

판정: `fail`

Outcome labeling may require exit/post-sell labels, but the matrix still defines a `holding` stage and allowed actions `HOLD/EXIT/NO_CHANGE`. 5/20 has holding AI events and a holding/exit decision matrix artifact, yet LDM does not ingest them. If holding rows cannot be scored yet, the report should say `contract_gap` or `instrumentation_gap`, not silently show `sample=0`.

### Cross-Check E. Does source-quality audit guard this?

판정: `fail`

The source-quality audit passes overall, but it does not contain `scalp_sim_*` contract entries. Therefore it cannot catch missing sim submit/holding routing.

### Cross-Check F. Any runtime/order/provider mutation caused by this audit?

판정: `pass`

No runtime file, order path, provider route, bot process, or threshold env was changed by this audit.

### Cross-Check G. Focused test result

판정: `warning`

Command:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_scalp_entry_action_decision_matrix.py
```

Result: `6 passed, 2 failed`.

The two failures are Entry ADM runtime-bias expectations that assume `BUY -> WAIT` forcing:

- `test_scalp_entry_adm_runtime_bias_forces_wait_on_negative_buy_bucket`
- `test_scalp_entry_adm_hypothesis_fallback_forces_wait_on_weak_chase_risk`

This does not invalidate the sim ingest finding above. It does mean the current Entry ADM runtime-bias test expectations are not aligned with the 5/20 artifact posture where Entry ADM is `entry_advisory_prompt_context_only` and `runtime_bias_applied_count=0`. Treat this as a separate ADM runtime contract drift to resolve after the source routing gap.

## Pre-Fix Final Control State

- state: `RED`
- blocked_stage: `decision_integrity`
- impact: 5/20 LDM policy entries for `entry`, `submit`, and `holding` are not reliable as a complete lifecycle tuning view. `submit=0` and `holding=0` are routing artifacts. `entry promote_ready=true` is suspect because ADM input is truncated and LDM rows are capped.
- next_action: block 5/20 LDM-derived submit/holding promotion and treat LDM entry promotion as `contract_gap` until the source adapters and full-row contracts are fixed, then regenerate LDM, threshold EV, runtime approval summary, and workorder diff.

## Pre-Fix Required Fix Scope

1. Add a normal scalp sim submit loader to LDM.
   - Map `scalp_sim_buy_order_virtual_pending`, `scalp_sim_buy_order_assumed_filled`, `scalp_sim_entry_submit_revalidation_warning`, and `scalp_sim_entry_submit_revalidation_block` to `stage=submit`.
   - Preserve `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`.

2. Add normal scalp sim holding / Holding-Exit ADM input to LDM.
   - Ingest `holding_exit_decision_matrix_YYYY-MM-DD.json` or sim holding review events into `stage=holding`.
   - If labels are unavailable, mark `contract_gap` explicitly instead of reporting silent `sample=0`.

3. Replace LDM Entry ADM `examples` dependency.
   - Entry ADM should expose a full machine-readable row artifact, or LDM should independently rebuild rows from ADM source events.
   - LDM must not use only the first 50 examples as the Entry ADM source.

4. Add truncation accounting to LDM.
   - Report `source_rows_before_cap`, `retained_rows`, `dropped_rows_by_source`, and a warning when rows are capped.

5. Extend source-quality audit coverage.
   - Add contracts for normal scalping sim stages, especially virtual submit/fill, submit revalidation, holding AI call/deferred, and assumed sell fill.

## Pre-Fix Do Not Use Until Fixed

- 5/20 LDM `submit sample=0` as evidence that sim submit did not happen.
- 5/20 LDM `holding sample=0` as evidence that holding samples are absent.
- 5/20 LDM `entry promote_ready=true` as a complete ADM-backed promotion decision.

## Pre-Fix Still Usable With Caveats

- `threshold_cycle_ev_2026-05-20` sim simulator counts and post-sell join.
- `scalp_entry_action_decision_matrix_2026-05-20` as a report-only Entry ADM view.
- real/sim separation and `actual_order_submitted=false` provenance.
