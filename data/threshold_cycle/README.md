# Threshold Cycle Operations

작성 기준: `2026-09-08 KST`

이 디렉토리는 threshold 후보 수집, 장후 calibration, 장전 bounded runtime env apply, daily EV 리포트를 저장한다. 현재 원칙은 완전 무인 `auto_bounded_live` apply이며, 장중 runtime threshold 자동 변경은 계속 금지한다.

튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 이 기준 이전 `threshold_events`, raw pipeline events, report, DuckDB/Parquet analytics 산출물은 archive/audit evidence로만 보존하며 threshold-cycle EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다. 기준 이후 target의 postclose verifier는 pre-baseline report/analytics residue를 fail-closed한다.

report 기반 자동화의 전체 추적성은 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)를 기준으로 본다. 이 문서는 산출물별 producer/consumer와 현재 apply 단계만 설명하고, 미래 작업 owner는 날짜별 checklist가 소유한다.

현재 운영 기본 범위는 스캘핑 threshold-cycle, daily EV, PREOPEN runtime env와 code-improvement workorder다. `scalp_sim_*`과 probe/source-only row는 real과 분리하며 `combined`는 diagnostic-only다. 스윙 chain은 operator OFF가 기본이고, OFF 날짜에는 관련 산출물의 freshness를 필수로 요구하지 않는다. 별도 운영 지시로 다시 열더라도 dry-run과 broker-order forbidden 계약을 유지하며 final full-live conversion은 별도 사용자 승인 대상이다.

## 현행 해석과 검토 경계

- 최종 순서는 `EV/workorder/runtime summary → tower → checklist 최종 refresh → verifier --require-summary-handoff → controller DONE`이다. `postclose_summary_sources_v1`, tower의 `source_generation_contract`, checklist의 `POSTCLOSE_SUMMARY_SOURCES`를 같은 target date/실제 source SHA256으로 대사한다. 일반 verifier PASS나 이전 성공 파일로 마지막 명령 실패를 숨기지 않는다. verifier/controller 자체 hash는 순환 방지를 위해 제외한다.
- [9/7 원천 복구](../../docs/audit-reports/2026-09-08-postclose-priority-repair-review.md)는 CF route 관찰을 실제 ADD/NO_ADD와 분리해 기존 체결·손익 귀속을 회복한 것이지 신규 수익이 아니다. 미대사 `realized_pnl_krw`는 null과 사유를 유지한다. 건수 일치는 exact 비용 검증이 아니며 비가역적 과거 원천 결손은 격리·다음 자연 수집으로 관리한다.
- 별도 사용자 승인 위젯·에피소드의 9/8 policy/설치와 source-only 추천 생성을 구분한다. frozen 원본 ledger와 native metadata projection/승인 ledger는 원본 hash·위치로 대사하며 합산하지 않는다. 새 ID·코드 PASS·provider0 metadata terminal은 live 승격 근거가 아니다.

- 원칙/owner는 [Plan Rebase](../../docs/plan-korStockScanPerformanceOptimization.rebase.md), 상세검토는 [진행 목록](../../docs/audit-reports/2026-09-05-postclose-work-inventory.md), 명시적으로 호출한 모니터링/복구/2-pass는 [작업 지시문](../../docs/postclose-tuning-result-review-task-instructions.md)을 따른다. 문서 현행화는 운영 실행 요청이 아니다.
- ADM/LDM·statistical action weight·bucket·greenfield·전용 institutional aggregate는 retired다. 옛 경로/설명은 archive 호환이며 생성·복구·자동승격 조건이 아니다. Swing은 OFF, sim은 현재 우선 상세튜닝 대상이 아니다. 비-LDM scalp-sim control tower/prior는 별도 surviving source-only owner다.
- #8/#9/#11과 #119/#23/#49/#76/#78/#82의 코드·계약 보완 완료를 유지하되 자연 산출물/정책 선택/PID/비용 차감 EV는 기존 checklist OPEN owner로 따로 확인한다. 표본 0만으로 완료 검토를 재개하지 않는다.
- Main AI R0–R3는 지속적인 offline prompt/input 탐색이다. #76 self-hash·부분 정상행 학습 → #82 schema2/policy v5 → #78 offline optimizer, 21:05 terminal 상세결과 뒤 calibration·당일 선택 freeze·provider0 metadata binding·holding manifest·consumer를 갱신한다.
- #81 legacy Main AI runtime은 DISABLED이고 R3/#82 표본만으로 활성화되지 않는다. 지원 KRX V2.14/V2.15는 별도 `entry_setup_live_policy` owner의 기존 승격/PREOPEN/receipt가 필요하다.
- #11 자연 감사는 main의 예정 stage 전이면 `not_yet_due`다. 결손을 특정할 수 있는 row/window/cohort는 제외하고 정상 입력을 보존하며, preflight missing/invalid·격리 실패는 전체 차단한다. 진단 수리 완료에 별도 live/경제성 floor를 추가하지 않는다.
- Operator policy lock은 오래됐다는 이유로 해제하지 않는다. 구현 PASS·파일 생성·selected와 현재 PID 소비·실현 순이익은 각각 별도 증거다.

## 운영 흐름

| 시점 | wrapper | 역할 | 산출물 |
|---|---|---|---|
| runtime | `src.utils.pipeline_event_logger` | threshold 후보 stage를 compact stream에 적재 | `threshold_events_YYYY-MM-DD.jsonl` |
| POSTCLOSE 20:10 | `deploy/run_threshold_cycle_postclose.sh` | raw pipeline event를 family partition으로 backfill하고 source-quality, AI review, 활성 dedicated family, rising-missed, PYRAMID, widget/episode attribution, daily EV, workorder와 final verification을 순서대로 생성 | `date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/report/threshold_cycle_YYYY-MM-DD.json`, `threshold_cycle_ev`, `runtime_approval_summary`, `runtime_apply_gap_audit`, `code_improvement_workorder`, `threshold_cycle_postclose_verification`, `threshold_cycle_postclose_status` |
| PREOPEN 07:35 | `deploy/run_threshold_cycle_preopen.sh` | 최신 threshold report와 AI correction guard를 읽어 auto bounded runtime env 생성 | `apply_plans/threshold_apply_YYYY-MM-DD.json`, `runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}`, `data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_YYYY-MM-DD.status.json` |

cron completion detector는 wrapper log의 terminal marker를 source of truth로 본다. Threshold cycle postclose wrapper는 같은 `target_date`를 포함해 `[START]`, `[DONE]`, `[FAIL]` marker를 남겨야 하며, 완료 marker는 `[DONE] threshold-cycle postclose target_date=YYYY-MM-DD`다. artifact가 생성됐지만 marker가 없으면 threshold/runtime 실패가 아니라 wrapper/log 계약 결함으로 분류하고 marker 계약을 먼저 보강한다. `2026-05-22`부터 `12:05` intraday calibration cron은 제거됐고, intraday phase artifact는 명시 수동 forensic/legacy override가 있을 때만 생성한다.

PREOPEN artifact는 로컬 `data/threshold_cycle/apply_plans/`와 `runtime_env/`만 기동 authority다. GCP artifact push/promote 경로는 제거됐으며 remote staging artifact를 runtime 적용 증거로 사용하지 않는다. `src/run_bot.sh`는 당일 로컬 env가 없으면 로컬 PREOPEN bootstrap을 시도하고, 검증된 env가 생길 때까지 bounded wait한 뒤 source한다.

`artifact_freshness`는 `.json` artifact가 존재하더라도 generic JSON parse 검증을 먼저 수행한다. 깨진 JSON은 one-shot fresh로 통과하지 않으며, critical artifact는 fail로 닫는다. `threshold_cycle_preopen_status`와 `threshold_cycle_postclose_status`는 `status=succeeded`만 pass로 보며, lock skip/running/failed는 조용한 성공이 아니라 status artifact warning/fail 입력으로 남긴다.

## 현재 적용 정책

- `THRESHOLD_CYCLE_APPLY_MODE` 기본값은 `auto_bounded_live`다.
- `threshold_cycle_preopen_apply`는 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`, `auto_bounded_live`를 허용한다. `auto_bounded_live`는 승인 대기 없이 deterministic guard + AI correction guard를 통과한 family만 장전 runtime env 파일로 반영한다.
- apply plan은 자동 적용 후보/차단 사유/safety guard/calibration trigger context를 남기는 source of truth artifact다.
- 목표 미달은 rollback이 아니라 다음 manifest의 `calibration_state=adjust_up|adjust_down|hold|hold_sample|hold_no_edge|freeze`로 처리한다.
- sample 부족은 `hold_sample` 등 해당 family 계약으로 판정한다. 단지 표본 부족을 이유로 quantity/cap/안전 guard를 변경하거나 진단 수리를 미완료로 만들지 않는다.
- `safety_revert_required=true`는 hard/protect/emergency stop 지연, 주문 실패, receipt/provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다.
- 실제 env 반영은 다음 장전 1회 bounded apply로 자동 수행한다. 코드 hot mutation은 하지 않고, `src/run_bot.sh`가 당일 로컬 `runtime_env/threshold_runtime_env_YYYY-MM-DD.env`를 기동 시 source한다.
- scheduled calibration artifact는 매일 장후 1회 생성한다. 장중 intraday phase는 명시 수동 forensic/legacy override가 있을 때만 실행하며, canonical postclose threshold report를 덮어쓰지 않고 next-preopen apply 필수 단계가 아니다.
- postclose의 경제성 요약은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}`다. OFF Swing/retired LDM의 freshness·승격 후보는 요구하지 않고 real full-fill/partial/sim/CF를 구분한다.
- `lifecycle_decision_matrix_runtime`은 retired OFF/no-op다. 과거 env/policy/version으로 복원하지 않는다.
- `market_regime_continuous_thresholds`는 시장국면 source/diagnostic family다. `allowed_runtime_apply=false`, `runtime_effect=false`이며 retired ADM/LDM consumer를 요구하지 않는다.
- 기존 fixed threshold는 role contract로 처리한다. broker/stale/price freshness/stop/account/order/qty/cooldown은 `hard_safety`, `BUY_SCORE_THRESHOLD`와 entry score cutoff/VPW/strength/momentum은 `baseline_prior`, score65_74/soft stop/holding/scale-in price guard는 `bounded_tunable`, latency DANGER/stale/broker submit 차단은 `hard_safety_submit_quality`, fallback/legacy latency/shadow 축은 `legacy_archive`다.
- `BUY Funnel Sentinel`은 `submitted/ai < 20.0%` 또는 `submitted/budget <= 10.0%`이고 각각 `ai_confirmed unique >=20`, `budget_pass unique >=3` floor를 만족하면 `SUBMIT_DROUGHT_CRITICAL`로 강제 표면화한다. 이 상태는 `operator_action_required=false`이며 postclose code-improvement workorder와 활성 entry-recheck 진단/consumer에 handoff한다. Sentinel schema5/exact2의 날짜·분모·attempt/cycle·terminal·source digest를 소비자와 대사하고, 비차단 price fallback을 실제 veto로 세지 않는다. LDM submit bucket은 retired다. `threshold_cycle_ev`, `runtime_approval_summary`, postclose verifier가 이 handoff를 소비하지 못하면 `buy_funnel_submit_drought_handoff_missing`으로 실패한다. 단, threshold/order/provider/bot restart나 broker/stale/account/order/qty/cooldown guard 우회는 자동 수행하지 않는다.
- `runtime_apply_gap_audit`는 `runtime_approval_summary` 이후, 다음 checklist와 postclose verifier 이전에 실행한다. discovery/bridge/runtime summary/workorder/preopen/post-apply attribution의 생산/소비 drift를 후보별 ledger로 닫고, positive EV + source-quality pass 후보가 source-only에 묻히면 FAIL 또는 Codex 작업지시로 표면화한다. 내부 AI reviewer prompt는 영어와 `gpt-5.4` 이상 strict JSON schema를 사용하고, 사용자-facing Markdown은 한글이다. 산출물 자체는 `runtime_effect=false`, `allowed_runtime_apply=false`이며 runtime mutation executor가 아니다.
- 스윙 entry 병목 자동화는 현재 OFF다. 과거 Swing/LDM drought handoff를 현행 필수 consumer나 복구 권한으로 취급하지 않는다.
- `latency_classifier_runtime_profile`은 runtime DANGER/stale/broker hard-safety와 telemetry label로만 유지한다. `EntryPolicy`는 slippage check 이후 `SAFE`와 `CAUTION`을 normal submit으로 보내고 `DANGER`, stale quote, broker/account/order/qty/cooldown guard를 차단한다. 독립 `latency_classifier_recommendation` producer/PREOPEN candidate는 `latency_recommendation_retirement_20260906`으로 폐기됐다. latency block/pass/reason은 BUY Funnel, performance tuning, daily threshold report가 diagnostic-only로 집계하며, 별도 fresh spread-only operator lock은 그대로 유지한다.

## 주요 경로

| 경로 | 의미 |
|---|---|
| `threshold_events_YYYY-MM-DD.jsonl` | runtime compact event stream |
| `snapshots/pipeline_events_YYYY-MM-DD_*.jsonl` | POSTCLOSE collector가 live append 중인 raw 파일 대신 읽는 immutable source snapshot |
| `date=YYYY-MM-DD/family=*/part-*.jsonl` | family별 report 입력 partition |
| `checkpoints/YYYY-MM-DD.json` | incremental backfill resume/checkpoint |
| `apply_plans/threshold_apply_YYYY-MM-DD.json` | 장전 apply plan artifact |
| `runtime_env/threshold_runtime_env_YYYY-MM-DD.env` | 봇 기동 시 source되는 bounded runtime env override |
| `runtime_env/threshold_runtime_env_YYYY-MM-DD.json` | runtime env override와 selected family provenance |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 장후 canonical threshold report |
| `data/report/report_YYYY-MM-DD.json` | daily market report. `market_regime_continuous_score`, label, component scores, legacy gate score를 threshold-cycle source-only 진단에 제공; retired ADM/LDM에는 공급하지 않음 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/lifecycle_ai_context/lifecycle_ai_context_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 현재 producer/consumer/PREOPEN 적용 또는 복구 권한 없음. |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | 누적/rolling cohort 기반 threshold cycle 파생 artifact |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_postclose.{json,md}` | scheduled AI correction proposal + deterministic guard 파생 artifact. `_intraday` review는 manual forensic/legacy manifest-only source이며 runtime apply source가 아니다 |
| `data/report/latency_classifier_recommendation/latency_classifier_recommendation_YYYY-MM-DD.{json,md}` | RETIRED/archive only. 신규 생성·PREOPEN 소비·runtime apply·재활성화 권한이 없다. 현행 latency 진단은 BUY Funnel/performance/daily threshold report가 소유한다 |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | Gemini/Claude pattern lab 기반 improvement order 및 auto family 후보 artifact. runtime/code 직접 변경 없음 |
| `data/runtime/scalp_live_simulator_state.json` | 스캘핑 live simulator open sim 포지션 복원 상태. threshold report 입력은 이 파일이 아니라 `scalp_sim_*` pipeline events를 기준으로 한다 |
| `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.{json,md}` | 스윙 선정-DB 적재-진입-보유-추가매수-청산 lifecycle audit artifact. runtime/code 직접 변경 없음 |
| `data/report/swing_threshold_ai_review/swing_threshold_ai_review_YYYY-MM-DD.{json,md}` | 스윙 threshold/logic proposal-only review artifact. 기본 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`이라 OpenAI 호출 없이 생성하며, 명시적으로 `openai`를 준 경우에만 AI review를 수행한다. deterministic guard와 수동 workorder가 최종 source of truth |
| `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.{json,md}` | 스윙 lifecycle 기반 improvement order 및 auto family 후보 artifact. 모든 order는 `runtime_effect=false`, family candidate는 `allowed_runtime_apply=false`로 시작 |
| `data/report/swing_runtime_approval/swing_runtime_approval_YYYY-MM-DD.{json,md}` | 스윙 hard floor + EV trade-off score 기반 dry-run pre-final 후보, final approval request, blocked reason. 일반 dry-run runtime 후보는 parsed AI Tier2 review 통과 시 `dry_run_auto_apply_ready` pre-final auto approval로 다음 PREOPEN에 소비될 수 있다. Phase0 one-share/scale-in real canary 요청은 생성하지 않는다. Final full-live/cap/provider/bot/safety 변경은 user approval 전용이다 |
| `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.{json,md}` | 스윙 safe pool 후보는 8개 arm, bottom rebound source 후보는 전용 anticipatory 3-arm으로 확장하는 source-only artifact |
| `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.{json,md}` | discovery arm의 `1d/5d/10d/policy_exit` label과 `PENDING_ENTRY/ENTERED/EXITED/EXPIRED` 상태 전개 artifact |
| `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.{json,md}` | discovery arm별/정책별/sector-theme별 source-only EV, surviving arm, avoid bucket artifact. runtime env apply 권한 없음 |
| `data/runtime/swing_strategy_discovery/sector_theme_map_YYYY-MM-DD.json` | discovery candidate의 sector/theme enrichment cache. 섹터/업종은 수동 reference(`KORSTOCKSCAN_SWING_SECTOR_MANUAL_FILE` 또는 `docs/reference/data_5126_YYYYMMDD.xlsx`), 테마는 키움 `ka90001 qry_tp=2` 기준으로 기록하며 실패 시 fallback/missing source-quality로 남긴다 |
| `data/threshold_cycle/sim_auto_approvals/swing_sim_auto_approval_YYYY-MM-DD.json` | Swing LDM과 bottom rebound sim-only 승격 결과를 단일 control-tower artifact로 합치는 source-only approval |
| `data/threshold_cycle/swing_sim_policies/swing_sim_policy_catalog_YYYY-MM-DD.json` | 다음 PREOPEN swing sim policy input catalog. 실주문/runtime threshold 변경 권한 없음 |
| `data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_YYYY-MM-DD.json` | `scalp_sim_scale_in_window_expansion` sim-auto artifact. It defaults to `approved=true`, `approval_state=sim_auto_approved`, and `human_approval_required=false` only when the lifecycle matrix source report is readable. Missing source closes as `source_quality_blocked`; preopen may apply only next PREOPEN sim-source env values. Real scale-in, cap release, hard-safety relaxation, provider changes, and bot restart are forbidden |
| `data/threshold_cycle/approvals/swing_runtime_approvals_YYYY-MM-DD.json` | Final-stage user approval artifact. Pre-final dry-run auto approvals do not require this artifact, but final full-live conversion, cap release beyond bounded limits, provider/bot changes, and hard/protect/emergency safety relaxation do. Historical `swing_one_share_real_canary_YYYY-MM-DD.json` and `swing_scale_in_real_canary_YYYY-MM-DD.json` artifacts are ignored |
| `data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_YYYY-MM-DD.{json,md}` | DeepSeek 스윙 pattern lab 기반 automation artifact. fresh single-day 조건 미충족 시 warning만 남기고 order로 승격하지 않음 |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | 완전 무인 반영 이후 daily EV 성과 제출 artifact |
| `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}` | 스캘핑 selected family, 스윙 approval request, panic approval 후보를 묶은 read-only 요약 artifact. runtime mutation 권한 없음 |
| `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.{json,md}` | runtime uptake gap watchdog. 후보별 ledger, retry queue, Codex 작업지시, AI reasoning review를 남기며 runtime mutation 권한 없음 |

## 누적/rolling threshold cycle report

`threshold_cycle_cumulative` artifact는 daily report를 대체하지 않는다. 역할은 `daily`, `rolling`, `cumulative`가 같은 방향을 가리키는지 확인해 threshold 후보의 지속성을 보는 report-only 입력이다.

기본 구간:

- cumulative: `2026-06-05T00:00:00+09:00` 이후 clean-baseline `post_fallback_deprecation` 구간. 과거 4/21 시작 label은 호환명일 뿐 결정 입력 범위가 아니다.
- rolling: 최근 `5/10/20` calendar-day window
- completed 손익 기준: `COMPLETED + valid profit_rate`
- cohort: `all_completed_valid`, `normal_only`, `initial_only`, `pyramid_activated`, `reversal_add_activated`

금지선:

- 누적 평균 단독으로 live threshold mutation을 수행하지 않는다.
- full/partial fill split이 없는 누적 손익은 hard 승인 근거로 쓰지 않는다.
- `main_only`/runtime flag cohort/source provenance가 비어 있으면 방향성 판정으로 격하한다.
- 누적/rolling은 추천값 확정이 아니라 방향성과 step size 산정에만 사용한다.

## bounded calibration loop

`threshold_cycle_YYYY-MM-DD.json`은 다음 두 목록을 분리한다. `family_readiness_list`는 family의 구현 capability와 근거 준비 상태를 진단하고, `apply_candidate_list`는 window policy까지 확정된 `adjust_up|adjust_down` 중 `runtime_apply_eligible_now=true`인 변경 후보만 담는다. `hold`/`hold_sample`/`freeze`는 신규 적용 후보가 아니며, 기존에 승인·적용된 값을 유지하는 PREOPEN carry-forward와도 구분한다.

- `calibration_candidates`: family별 `threshold_version`, target env keys, current/recommended/applied values, bounds, `max_step_per_day`, sample floor, confidence, `calibration_state`, `safety_revert_required`를 담는다.
- `sample_window`/`window_policy`: family별로 당일 데이터와 clean baseline 2026-06-05 이후 누적/rolling 데이터의 역할을 분리한다. 당일 운영 상태로 판단할 family와 누적 지속성이 필요한 family를 섞지 않는다.
- `calibration_source_bundle`: `data/report`의 기존 보유/청산 리포트 경로와 soft-stop tail/defer cost/trailing/safety 요약을 담는다.
- `trade_lifecycle_attribution`: `record_id` 기준으로 진입 주문/취소, 보유 중 후보 신호, 청산 rule/source, 장후 `post_sell_evaluations`를 join해 전중후 유형을 닫는다. runtime stage는 provisional signal이고, 최종 유형은 post-sell outcome이 붙은 뒤 family view로 제공한다.
- `post_apply_attribution`: threshold version별 applied/not-applied cohort key와 GOOD_EXIT/MISSED_UPSIDE/soft-stop tail/defer cost/safety breach metric 정의를 담는다.
- `safety_guard_pack`: 원복 후보를 safety breach로만 제한한다.
- `calibration_trigger_pack`: 목표 미달, 표본 부족, 방향성 불일치의 다음 calibration action을 담는다.

`holding_score_v2`는 보유 중 포지션 상태 score의 provenance/source-quality 계약이다. 이는 intraday threshold mutation, env override, provider route change, bot restart, broker/order guard bypass, quantity/cap change가 아니며, scale-in/avg-down/pyramid 소비층이 `live + fresh|partial + TTL` score만 support로 쓰도록 제한하는 runtime data-quality guard다. `holding_flow`는 기존처럼 sell candidate override/recheck 전용으로 유지한다.

bounded calibration family는 아래 묶음이 중심이다. 목적은 완벽한 threshold spot 탐색이 아니라 efficient trade-off 지점의 bounded live canary와 자동 calibration이다.

1. `lifecycle_decision_matrix_runtime`: retired이며 현재 bounded calibration 대상에서 제외한다.
2. `score65_74_recovery_probe`: family id는 유지하지만 current runtime floor는 score60이다. broad score threshold 완화가 아니라 score60~74이면서 실제 probe 계약이 있는 exact cohort, latency DANGER 제외, 수급/가속/micro-VWAP 유지 조건의 entry unlock 후보다. 분모는 broad WAIT/차단 건수가 아니라 이 exact cohort만 사용한다. counterfactual gross EV는 탐색 진단일 뿐이며, effective-dated round-trip cost와 forward candle source-quality가 모두 pass인 행의 비용 차감 EV만 primary metric이다. 결손 행은 개별 격리하고 raw/eligible/excluded count를 함께 남긴다. 비용 계약이 없거나 유효 경제성 표본이 없으면 `source_quality_blocked|hold_sample`로 두고 실체결 품질로 주장하지 않는다. 현재 `WAIT6579_PROBE_CANARY` 별도 예산/수량 cap은 `0`일 때 기본 신규 BUY sizing을 사용하므로 1주/5만원 cap이 active 설명이 아니다.
3. `latency_classifier_runtime_profile`: runtime hard-safety/telemetry label이다. `SAFE`/`CAUTION`은 slippage check 이후 normal submit, `DANGER`/stale/broker safety는 차단으로 본다. 독립 calibration candidate는 만들지 않는다.
4. `bad_entry_refined_canary`: naive hard block 재개가 아니라 soft-stop tail/defer cost 감소 후보. `bad_entry_refined_candidate`는 runtime provisional signal이며, 최종 유형은 장후 `post_sell_evaluations`가 `record_id`로 join된 뒤 lifecycle attribution으로만 닫는다.
5. `soft_stop_whipsaw_confirmation`
6. `holding_flow_ofi_smoothing`
7. `protect_trailing_smoothing`
8. `holding_exit_decision_matrix_advisory`: SAW/ADM과 함께 retired, 과거 matrix bucket은 live 후보가 아니다.
9. `trailing_continuation`: GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 `freeze/report_only_calibration`만 허용
10. `market_regime_continuous_thresholds`: `market_regime_continuous_score` label threshold와 component weight를 rolling 10d source bundle에 등록한다. 1차 개발은 manifest-only/context-only이며, `KORSTOCKSCAN_MARKET_REGIME_*` env 반영은 별도 2차 review 전까지 금지한다.

### Lifecycle Decision Matrix와 fixed threshold

Lifecycle matrix/ADM/discovery/bridge는 retired다. 예전 action bucket·handoff·env 설명은 현행 필수 producer 또는 승격 권한이 아니다. `producer_gap_discovery`도 기본 OFF이며 단순 과거 산출물 부재로 열지 않는다.

현재 fixed threshold의 역할은 hard safety, baseline prior, bounded tunable, legacy archive로 유지한다. 활성 dedicated family의 후보만 기존 bounds/max step/source-quality/경제성/owner 계약을 통과해 다음 PREOPEN으로 전달한다. 수량·broker/account/order/cooldown/stale/hard safety는 별도 최상위 guard다.

`pre_submit_price_guard`는 실제 제출 직전 safety이며 튜닝용 자동완화 후보가 아니다. 가격 후보 비교는 `dynamic_entry_price_resolver`, 실제 broker/cancel/late/partial/full-fill 감사는 `entry_price_execution_quality`가 소유한다. Submit drought가 upstream에서 발생했는지 먼저 확인하고 cancel-wait/Entry split을 원인 없이 우선 완화하지 않는다.

### Latency classifier runtime profile

`latency_classifier_runtime_profile`은 실매매 submit 직전 latency 품질 감사 owner다. runtime path는 `EntryPolicy`를 평가하되 CAUTION은 slippage check 이후 normal submit으로 단순화했고, `DANGER`, hard safety, stale quote, broker/account/order/qty/cooldown guard를 우회하지 않는다. 제출 고갈 자체는 `BUY Funnel Sentinel`의 `SUBMIT_DROUGHT_CRITICAL` incident가 소유한다.

적용 경로:

1. R0 수집: `latency_block`, `latency_pass`, `order_bundle_submitted`는 `reason`, `latency_state`, `policy_decision`, `effective_decision`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, `quote_stale`, `signal_price`, `latest_price`, `latency_canary_applied`, `latency_canary_reason`, `threshold_family`, `runtime_effect`, `actual_order_submitted`, `broker_order_forbidden`를 남긴다.
2. R1/R2 분석: BUY Funnel, performance tuning, daily threshold report가 `latency_block/pass`, reason, freshness, counterfactual coverage를 diagnostic-only로 분리한다.
3. R3 후보: 독립 latency calibration candidate는 생성하지 않는다. 과거 `latency_classifier_recommendation` candidate는 retirement filter가 제거한다.
4. R4/R5 적용: `threshold_cycle_preopen_apply`에는 latency recommendation loader나 AI exemption이 없다. 과거 artifact나 selected family가 runtime env를 복원할 수 없다.
5. R6 피드백: 실제 `latency_pass/block`, `order_bundle_submitted`, 후행 fill/exit outcome은 기존 BUY Funnel/performance attribution으로 확인한다. fresh spread-only operator lock 성과는 그 family provenance로 별도 대사한다.

`dynamic_entry_price_resolver`는 이 결과를 daily EV에 함께 노출해 `bid-1`, `bid-2`, `bid-3`, `best_bid`, `AI_candidate`, `reference_target`, `timeout_15s`, `timeout_30s` 후보별 fill/cancel/late-fill/EV를 비교한다. `AI_candidate`의 `missing_snapshot`, `invalid_price`, `pre_submit_price_guard`, `above_best_ask`, `skip_low_confidence`는 후보 실패율로 별도 집계하고, `submitted_order_price=0`인 sim stale/unpriced 표본은 `unpriced_or_stale_warning_count`와 `excluded_from_fill_ev_count`로 보존하되 fill/EV 분모에서 제외한다. 이 count는 정상 telemetry일 수 있으므로 단독으로 code-improvement workorder를 만들지 않고, `report_contract_gap` 또는 `dynamic_entry_price_report_contract_status=failed|missing|incomplete` 같은 명시적 계약 gap이 있을 때만 workorder 입력으로 사용한다. `pre_submit_price_guard`는 `latency_pass_events=0`의 primary owner가 아니며, quote/price 품질을 보는 제출 직전 safety layer로만 유지한다.

## AI correction proposal layer

`threshold_cycle_ai_review` artifact는 AI를 검토자뿐 아니라 이상치 수정안 제안자로 쓰기 위한 보조 layer다. deterministic `calibration_candidates`가 source of truth이며, AI correction은 후보 위에 아래 필드를 덧붙인다.

- `ai_proposed_value`
- `ai_proposed_state`
- `ai_anomaly_route`
- `ai_required_evidence`
- `guard_accepted`
- `guard_reject_reason`

AI가 제안할 수 있는 범위는 `adjust_up|adjust_down|hold|hold_sample|freeze`, family bounds 안의 후보값, 이상치 routing(`threshold_candidate|incident|instrumentation_gap|normal_drift`), sample window(`daily_intraday|rolling_5d|rolling_10d|cumulative`)까지다. AI 단독 env/code/runtime 직접 변경, 장중 threshold mutation, safety guard 우회, `safety_revert_required` 강제 변경, 단일 사례 live enable 확정은 금지한다.

실행 방식은 세 가지다. `daily_threshold_cycle_report` 직접 실행 기본값은 provider를 호출하지 않고 deterministic calibration과 `ai_status=unavailable` artifact를 남긴다. postclose cron wrapper는 `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai`를 기본으로 넣어 장후 AI correction proposal 생성을 자동 시도한다. OpenAI correction은 Responses API와 `threshold_ai_correction_v1` strict JSON schema를 사용하며, 모델은 `GPT_THRESHOLD_CORRECTION_MODEL=gpt-5.5`, fallback은 `GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS=gpt-5.4,gpt-5.4-mini`다. 운영상 AI 호출을 끄려면 wrapper/cron env에서 `THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=none`을 지정하고, 이미 생성된 strict JSON 응답을 검증할 때는 `THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON=PATH` 또는 `--ai-correction-response-json PATH`를 사용한다. Gemini provider는 수동 fallback/비교용으로 남긴다.

비용 guard는 AI 사용 확대 전 필수 조건이다. AI input은 full blob을 직접 싣지 않고 source metrics top-N summary, artifact path, full hash로 참조하며 누적 snapshot/source metric은 실제 검토 대상 family만 싣는다. `ai_input_context_chars`와 hash는 실제 provider에 전달하는 compact ASCII JSON 직렬화와 동일한 문자열에서 계산하고, 최종 직렬화 뒤에도 hard cap을 재검증한다. section별 budget, token usage, elapsed_ms, output_chars, estimated cost field를 `threshold_cycle_ai_review`에 기록한다. 가격 계약은 운영 env `KORSTOCKSCAN_THRESHOLD_AI_INPUT_COST_PER_1M_USD`, `KORSTOCKSCAN_THRESHOLD_AI_OUTPUT_COST_PER_1M_USD`가 모두 있을 때만 USD로 계산하고, 없으면 비용을 0으로 대체하지 않고 `estimated_cost_usd=null`, `cost_estimate_status=missing_price_contract`로 남긴다.

중복 호출 방지는 `--reuse-ai-review-if-valid`가 담당한다. wrapper 기본값은 `THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID=true`이며, 같은 date/phase/schema/input_context_hash의 parsed artifact가 있으면 provider를 다시 호출하지 않고 기존 review를 재사용한다. 재사용 artifact는 `ai_provider_status.status=reused_valid_artifact`, `new_provider_call=false`, `estimated_incremental_cost_usd=0.0`으로 남긴다.

cron wrapper에서 provider가 `openai`인 경우 `ai_status=unavailable|parse_rejected`는 조용히 통과시키지 않는다. `THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS`만큼 재시도하고, 장중 calibration은 최종 실패 시 `[FAIL] threshold-cycle calibration`으로 종료한다. 장후 postclose의 AI hard failure는 `runtime_apply_eligible_now=true`인 비결정적 `adjust_up|adjust_down` 후보가 있을 때만 적용한다. `hold`는 AI 요청 목록에서 제외하며, 이미 결정된 entry/scale-in split plan이나 post-probe recovery handoff는 threshold AI가 다시 승인할 대상이 아니다. 검토 대상이 0개면 provider를 호출·재시도하지 않고 parsed empty review와 `skipped_no_review_candidates` receipt를 남긴다. preopen apply는 실제 AI 검토 대상 후보에 postclose parsed review가 없으면 intraday artifact로 우회하지 않고 fail-closed한다. 기계 적격성 `false`는 신규 자동 적용을 막지만 명시적 operator lock의 기존 우선권을 해제하지 않는다.

OpenAI correction prompt는 영어 control instruction, 한국어 시장용어 glossary, 원문 enum/raw label 보존 규칙을 포함한다. `BUY/WAIT/DROP/HOLD/TRIM/EXIT/SELL_TODAY`, family id, ticker, field name은 번역하지 않는다. 이 contract는 correction proposal 품질과 schema 안정성을 위한 것이며, AI에게 runtime/env/code 변경 권한을 주지 않는다.

deterministic guard는 AI 제안을 그대로 적용하지 않는다.

- 값 제안은 family bounds와 `max_step_per_day` 안으로 clamp한다.
- `sample_window/window_policy`와 맞지 않으면 reject 또는 `hold_sample`로 둔다.
- `soft_stop_whipsaw_confirmation`, `bad_entry_refined_canary`, `scale_in_price_guard`처럼 rolling/cumulative가 필요한 family는 단일 당일 이상치만으로 live 후보를 승격하지 않는다.
- `holding_flow_ofi_smoothing`처럼 daily_intraday family는 장중 anomaly correction 후보가 될 수 있지만 runtime mutation은 금지하고 다음 장전 apply 후보로만 넘긴다.
- `score65_74_recovery_probe`, `protect_trailing_smoothing`, `scale_in_price_guard`처럼 rolling/cumulative primary를 가진 family는 daily source가 있더라도 `window_policy_resolution.primary_sample_count` 기준으로 후보 상태를 재평가한다.
- AI API/parse 실패 시 deterministic calibration artifact는 정상 생성되고 `ai_status=unavailable|parse_rejected`, family item은 `ai_review_state=unavailable`로 남는다. 단, wrapper/verification/apply guard는 이 상태를 runtime apply 가능 후보의 pass 조건으로 보지 않는다.

## calibration window policy

family별 기준 window는 다르게 적용한다. 아래 `cumulative_since_2026-04-21`은 기존 코드의 호환 label이며 현재 입력 시작일을 뜻하지 않는다. 모든 누적 결정 입력에는 2026-06-05 clean-baseline clamp가 우선한다.

| family | primary window | 보조 window | 해석 |
|---|---|---|---|
| `soft_stop_whipsaw_confirmation` | `rolling_10d` | `daily`, `cumulative_since_2026-04-21` | soft-stop late rebound는 단일 당일 사례로 live enable하지 않고 반복성/지속성을 본다. |
| `holding_flow_ofi_smoothing` | `daily_intraday` | `rolling_5d` | defer cost/HOLD_DEFER_DANGER는 장중 운영 상태가 빠르게 변하므로 당일 artifact를 우선하되 재발성만 rolling으로 본다. |
| `protect_trailing_smoothing` | `rolling_10d` | `daily`, `rolling_20d` | 단일 tick/단일 종목이 아니라 반복 이탈과 safety guard를 본다. |
| `trailing_continuation` | `rolling_10d` | `daily`, `rolling_20d` | GOOD_EXIT 훼손 리스크 때문에 당일 단독 live apply를 금지한다. |
| `score65_74_recovery_probe` | `rolling_5d` | `daily_intraday`, `cumulative_since_2026-04-21` | BUY drought는 당일 병목을 trigger로 쓰되 EV/close 우위와 false-positive risk는 rolling/cumulative 전용 표본으로 확인한다. 당일만으로 회수축 부활 또는 live/bounded canary 승격을 확정하지 않는다. family id는 artifact 호환을 위해 유지하지만 현 runtime floor는 score60이며, 전일 `panic_sell_defense.panic_detected` 또는 `panic_state in {PANIC_SELL, RECOVERY_WATCH}`이고 effective score60~74 표본이 sample floor의 70% 이상, EV/close 우위와 submitted drought guard를 통과하면 `panic_adjusted_ready` 후보가 될 수 있다. 최종 승격은 window policy guard를 통과해야 한다. |
| `latency_classifier_runtime_profile` | runtime event telemetry | BUY Funnel/performance/daily threshold diagnostic | DANGER/stale/broker safety 감사 label이다. 독립 recommendation/PREOPEN 후보 및 live apply 권한은 폐기됐다. |
| `bad_entry_refined_canary` | `rolling_10d` | `daily`, `cumulative_since_2026-04-21` | loser classifier 과적합을 피하기 위해 누적/rolling tail, 당일 safety, 장후 post-sell outcome join을 같이 본다. runtime 후보만으로 배드엔트리 확정 라벨을 붙이지 않는다. |
| `holding_exit_decision_matrix_advisory` | RETIRED | archive only | 현재 window/후보/소비자 요구 없음 |
| `scale_in_price_guard` | `rolling_10d` | `cumulative_since_2026-04-21`, `daily` | 물타기/불타기는 체결 표본이 희소하므로 당일만으로 guard 값을 정하지 않는다. |
| `market_regime_continuous_thresholds` | `rolling_10d` | `daily`, `rolling_5d` | VIX/Fear & Greed/국내 breadth/WTI pullback relief/local model 연속 점수를 risk-context feature로 검증한다. sample floor는 valid market cache + daily report 10일이며, 1차에서는 `allowed_runtime_apply=false`로 manifest-only 후보만 만든다. |

`threshold_cycle_cumulative`는 `threshold_snapshot_by_window`와 별도로 `calibration_source_bundle_by_window`를 생성한다. 모든 누적 입력은 clean baseline 2026-06-05로 clamp하고 날짜별 source/pipeline은 한 번만 읽어 재사용한다. rolling 5/10/20은 KRX 거래일 window이며 daily 운영 window와 구분한다. baseline 이전 daily 재생성은 archive/audit 출력만 허용하고 적용 권한을 fail-closed한다. 비소비 partition은 읽지 않고 available/skipped 수와 추정 byte를 남긴다. 선택 partition read 실패는 `pipeline_projection_read_complete=false`로 기록하되, 검토된 dependency 및 실제 window에 해당하는 후보만 차단한다. raw fallback skip/미식별 loss/미등록 consumer는 보수적으로 차단한다. 독립 producer의 source-quality 계약을 우회하지 않는다. 진단 목록은 상한과 full count/hash를 보존한다. source report의 rolling/cumulative metric은 `window_policy_resolution.primary_source_sample_count`로 소비하며 snapshot과 차이는 audit에 남긴다. Entry split의 floor는 real submit/outcome만 사용하고 sim은 진단이다.

Daily threshold 최종 보완은 [review](../../docs/audit-reports/2026-09-07-daily-threshold-final-defect-review.md)를 따른다. 기존 WAIT collector의 `score_recovery_observation_v1`은 실제 probe 적용과 독립적인 상승/반등 관측이다. 당시 설정/hash·시장 구간·가격·exact identity·source-quality·비용 계약이 필요하고, 적용/미적용 계수와 실체결은 분리한다. 신규 관측 계약이 invalid이면 applied marker로 우회하지 않는다. 빈 날의 비용 결손은 유효 비용 표본을 오염시키지 않는다. 기존 실전 절대 EV floor는 임의 완화하지 않고 `condition_feasibility`로 양수-but-subfloor와 근거 결손을 구분한다. AI input은 실제 ASCII 직렬화 크기로 검사하며 초과 payload는 provider/coverage repair 호출을 차단한다.

정규 입력 경로 계측은 `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date YYYY-MM-DD --benchmark-inputs-only`를 사용한다. source loader와 DB 조회를 생략하지 않고 report 저장/Provider 호출 없이 반환한다. `--skip-db`를 명시했다면 DB 포함 정규 성능과 구분한다. 미래 자연 수용·PREOPEN/PID·실수익을 계측 완료로 대체하지 않는다.

새 관찰축 추가는 기본 금지다. follow-up이 어려운 신규 observe/report axis를 늘리지 않고 BUY 쪽 `buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`, 보유/청산 쪽 `holding_exit_observation`, `post_sell_feedback`, `holding_exit_sentinel`, `trade_review`, 활성 dedicated strategy의 기존 source를 calibration 입력으로 재사용한다. `holding_exit_decision_matrix`와 `statistical_action_weight`는 retired라 현재 입력에서 제외한다. `sentinel_followup`은 2026-05-07 단발 Markdown follow-up으로 현재 calibration 입력에서 제외한다. `preclose_sell_target`은 2026-05-10 제거된 operator review 축이므로 calibration 입력에서 제외한다.

스캘핑 simulator 청산 후 MFE/MAE는 실주문 `post_sell_feedback`과 분리한 `data/post_sell/sim_post_sell_candidates_YYYY-MM-DD.jsonl`, `sim_post_sell_evaluations_YYYY-MM-DD.jsonl`에 기록한다. 입력은 `scalp_sim_sell_order_assumed_filled + numeric profit_rate`만 인정하고, join key는 `sim_record_id`/`sim_parent_record_id`다. 이 source는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_equal_weight_observation_only`, `runtime_effect=false`를 유지하며, threshold/order/provider/bot/broker submit 변경의 단독 근거가 아니다. 소비자는 `daily_threshold_cycle_report.scalp_simulator.post_sell_join`과 `threshold_cycle_ev` 요약이다.

`calibration_source_bundle.report_only_cleanup_audit`는 report-only/legacy 산출물 중 현재 source bundle consumer가 없는 항목을 자동 감사한다. `sentinel_followup`, 정기 full snapshot에서 제외된 legacy `add_blocked_lock`, 제거된 `preclose_sell_target`이 관리 대상이다. 결과는 `metric_role=source_quality_gate`, `decision_authority=source_quality_only`, `primary_decision_metric=cleanup_candidate_count`로만 쓰며, 정리 후보 표면화 외에 runtime env, threshold, 주문, bot restart, provider route를 바꾸지 않는다.

`claude_scalping_pattern_lab`과 활성 scalping pattern automation은 clean baseline 2026-06-05 이후만 평가한다. Gemini lab은 자동실행에서 retired이며 누락을 복구하지 않는다. 유효 결과도 existing-family/source-only 후보·workorder이지 runtime 직접 authority가 아니다. legacy `ANALYSIS_START_DATE` 예시를 새 실행 시작일로 재사용하지 않는다.

`position_sizing_dynamic_formula`는 모든 활성 SCALPING/SCALP 신규·추가매수와 sim의 upstream sizing owner다. 현재 `entry_type_5stage_cap25_v1`은 source-count/time/venue별 10/15/20/25/25% 고정 tier, 절대25% cap, 95% safe budget과 최소1주 floor를 적용하고 scale-in은 최초 tier를 재사용한다. NXT/unknown/invalid source는 tier1이다. 보고서 비교는 선택 공식과 `flat_10_fallback`뿐이며 과거 score-linear 7개 후보·10~30% 산식·`position_sizing_cap_release`는 현재 authority가 아니다. selected formula는 exact terminal join 30건·source-quality pass·gross EV `>=0.1%`·cost-adjusted EV `>=0%`를 모두 만족할 때만 `data/threshold_cycle/approvals/position_sizing_dynamic_formula_YYYY-MM-DD.json`으로 발행되고, 미종결 submit은 경제성 분모 밖 `unmatched_real_submit_count`로 보존한다. 다음 PREOPEN이 file/version/source-date/SHA256를 대사한다. artifact/env 검증 실패는 `flat_10_fallback`으로 fail-closed하며 canary one-share/cap과 downstream hard safety는 그대로 우선한다. 독립 episode의 두10주 leg 및 legacy custody는 별도 owner다. 실제 적용은 exact-date env/PID receipt로 확인한다.

`post_probe_winner_recovery`는 venue별 source-quality-valid closed one-share 실체결 20건과 비용후 EV `>=0.1%`를 충족하면 다음 PREOPEN에 중앙 `position_sizing_dynamic_formula` 사용 플래그를 자동 발행한다. 이 플래그는 독립 수량공식이나 cap 해제가 아니며 exact-date 중앙 정책이 `policy_loaded`일 때만 첫 residual leg의 1주 stage cap을 제거한다. 정책 검증 실패 또는 EV `0% 초과 0.1% 미만`은 1주 canary로 복귀하고, EV `<=0%`는 해당 venue를 비활성화한다. 기존 cash/position/broker/cooldown/hard-safety 가드는 계속 우선한다.

`panic_regime_mode`는 `panic_sell_defense`의 `panic_state`를 threshold-cycle이 해석하는 risk-regime 상태다. 현재 runtime authority는 `report_only`이며, `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` 모드는 source bundle, approval request, workorder evidence에만 들어간다. V2.0 후보는 `panic_entry_freeze_guard`이고 적용 범위는 scalping `entry_pre_submit` 신규 BUY 차단으로 제한한다. 미체결 진입 주문 cancel, holding/exit `panic_context`, 강제 축소/청산은 각각 별도 owner로 분리하며, approval artifact와 rollback guard 없이 preopen env나 broker order path에 반영하지 않는다. panic mode로 AI score threshold, stop-loss, TP/trailing, provider route, bot restart를 직접 바꾸는 것은 금지한다.

`panic_buy_regime_mode` 및 panic-buying detector/report/candidate/runner/entry modifier는 2026-08-08 retired다. 과거 V2.x 후보는 archive-only이고 생성·복구·승격 또는 재활성화 권한이 없다. 현행 panic-sell/market-weakness와 신규 namespace의 machine rebound-reentry owner를 구분한다.

`panic_lifecycle_actuator`는 live-selectable threshold family가 아니라 `sim_lifecycle_source`다. `threshold_family=panic_lifecycle_actuator`가 pipeline registry routing key로 남더라도 event는 `source_family=panic_lifecycle_actuator`, `family_type=sim_lifecycle_source`, `live_selectable=false`, `preopen_apply_allowed=false`, `env_apply_allowed=false`, `real_order_allowed=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`를 함께 남긴다. `panic_entry_freeze_guard`와 `panic_buy_runner_tp_canary`는 compatibility/read-only 이름이며 standalone preopen env, threshold mutation, provider route, bot restart trigger를 만들 수 없다. panic sell과 euphoria는 같은 source family를 쓰되 `risk_context_owner`, `risk_direction`, `action_namespace`로 방어성 축소와 수익확장/과열회수를 분리한다.

sim-first lifecycle 탐색은 별도 canonical report chain이 아니라 기존 threshold-cycle 자동화체인의 입력 범위와 판정 방식이다. 목적은 `scalp_ai_buy_all`처럼 BUY 확정 이후만 따라가거나 스캘핑 진입만 보는 것이 아니라, 스캘핑과 스윙의 BUY/selection 가능 후보 전체를 `selection -> entry -> holding -> scale_in -> exit` virtual lifecycle로 넓게 실행해 최적 threshold 후보와 기능개선 workorder를 찾는 것이다. 예수금 부족, 1주 cap, current selected family, 실주문 미제출은 sim exclusion 사유가 아니며 `real_blocker`/`actual_order_submitted=false` provenance로만 남긴다. 산출과 승격은 기존 `threshold_cycle_ev`, `threshold_cycle_cumulative`, `runtime_approval_summary`, `code_improvement_workorder`가 소유한다. 스캘핑 sim entry의 `entry_price` canary, passive submit revalidation, virtual pending은 `dynamic_entry_price_resolver` family의 sim-only 관찰 필드로 집계하고, stale/unpriced warning은 real execution defect가 아니라 `sim_unpriced_stale_warning` provenance로 분리한다. scale-in fill/unfill은 `scale_in_price_guard`에 남긴다. sim 결과는 실주문 enable/cap 해제/provider 변경/bot restart의 단독 근거가 아니며, 손실이 난 arm은 전체 탐색축 폐기가 아니라 해당 bucket tighten 후보로 라우팅한다.

스윙 discovery sim은 이 sim-first 원칙의 스윙 탐색 구현체다. `swing_strategy_discovery_sim`이 safe pool 후보와 8개 arm을 만들고, bottom rebound source 후보는 breakout confirmation을 요구하지 않는 전용 anticipatory 3-arm으로 분리한다. `swing_strategy_discovery_label_builder`가 성숙 quote 기준으로 label을 채우며, `swing_strategy_discovery_ev_report`가 source-only EV를 집계한다. postclose wrapper는 `swing_daily_simulation` 직후 이 세 단계를 실행하고, `swing_bottom_rebound_candidate_source_YYYY-MM-DD.json`의 source-only contract가 pass이면 자동으로 `--include-bottom-rebound-source`를 붙인다. bottom source를 포함했는데 selected/persisted candidate 또는 arm 수가 0이면 `threshold_cycle_postclose_verification.bottom_rebound_sim_handoff`가 fail-closed한다. `threshold_cycle_ev`와 `runtime_approval_summary`는 candidate/arm/labeled/pending/top surviving/avoid bucket 요약만 소비하고, `code_improvement_workorder`는 `runtime_effect=false` source-quality/report order만 만들 수 있다. 이 체인은 기존 스윙 runtime이나 `recommendation_history`를 대체하지 않는다.

`update_kospi` 이후 EOD DB refresh가 끝나면 바닥 반등 swing sim 후보 루프를 source-only로 실행한다. 순서는 `bottom_rebound_pattern_research -> swing_bottom_rebound_policy_auto_loop -> swing_bottom_rebound_candidate_source -> swing_strategy_discovery_sim --include-bottom-rebound-source`다. Tier-2 AI review가 백테스트/sim EV를 검토해 1% 이상 개선이면 `sim_auto_approved`로 다음 후보 source policy만 승격한다. 이 승격은 `swing_sim_auto_approval` control-tower artifact에 먼저 통합되고, `swing_bottom_rebound_candidate_source`는 해당 artifact에 bottom rebound source 승인이 있을 때만 후보를 넘긴다. postclose wrapper도 동일한 source contract를 확인해 valid source만 자동 포함하고, contract fail/missing이면 safe-pool-only로 계속 진행하되 verifier와 checklist에서 source-quality warning으로 본다. 승격은 virtual swing discovery candidate/arm 생성에만 연결되고, runtime env, broker order, real canary, threshold, provider, bot, `recommendation_history` 변경 권한은 없다.

스윙은 `swing_lifecycle_audit`와 `swing_improvement_automation`이 lifecycle 관찰축과 proposal/workorder를 만들고, `swing_runtime_approval`이 보수적 runtime 승인 요청만 만든다. hard floor는 family sample floor, critical instrumentation gap 없음, DB load gap 없음, fallback diagnostic contamination 없음, severe downside guard, same-stage owner 충돌 없음이다. 그 위에서 `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%`의 `tradeoff_score >=0.68`이면 승인 요청을 생성한다. 완벽한 개별 threshold spot을 찾지 않고 전체 EV trade-off가 충분한 지점을 요청 기준으로 본다. 1차 env 적용 가능 family는 `swing_model_floor`, `swing_selection_top_k`, `swing_gatekeeper_reject_cooldown`, `swing_market_regime_sensitivity`이며, `AVG_DOWN`, `PYRAMID`, exit OFI/QI smoothing, AI contract 변경은 approval request까지만 허용한다.

스윙 entry drought와 후속 weak-contract audit는 approval request와 별개인 code-improvement/source-quality 경로다. `holding_exit_contract`, `scale_in_contract`, `discovery_label_contract` gap은 workorder evidence로만 전달하며, final full-live approval artifact 없이 env apply, 1주 real canary, broker submit, provider route 변경으로 확장하지 않는다.

`swing_one_share_real_canary_phase0`와 `swing_scale_in_real_canary_phase0`는 removed legacy stage다. `threshold_cycle_preopen_apply`는 historical approval artifacts를 approved로 승격하지 않고 `legacy_phase0_real_canary_ignored` warning 또는 `blocked_legacy_real_canary_removed` reason으로만 남긴다. 스윙 actual trading reflection은 complete `swing_lifecycle_flow_bucket` parent evidence, parsed review, source-quality gates, and explicit final full-live user approval artifact가 닫힌 future path에서만 열린다.

## statistical_action_weight 적용 범위

`statistical_action_weight`와 `holding_exit_decision_matrix` producer/consumer는 2026-09-06 retired다. 과거 report, policy hint, advisory bucket을 재생성하거나 PREOPEN/live authority로 사용하지 않는다. 현재 dedicated holding-flow·trailing/AVG_DOWN/PYRAMID 계약과는 구분한다.

## 보호트레일링 평탄화 threshold family

`protect_trailing_smoothing` family는 `protect_trailing_smooth_hold`와 `protect_trailing_smooth_confirmed` stage를 수집한다.

관리 대상 값:

- `SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES`
- `SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO`
- `SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT`
- `SCALP_PROTECT_TRAILING_EMERGENCY_PCT`

런타임 override 키는 각각 `KORSTOCKSCAN_` prefix를 붙인 동일 이름이다. `protect_trailing_smoothing`은 GOOD_EXIT 훼손/safety risk가 커서 기본적으로 `hold_sample` 또는 `freeze`가 우선이며, 자동 적용은 같은 stage priority rule에서 선택된 경우에만 runtime env로 반영된다.

## OFI AI smoothing threshold family

`entry_ofi_ai_smoothing` family는 `entry_ai_price_ofi_skip_demoted` stage를 중심으로 P2 raw `SKIP` demotion 표본을 수집한다. `holding_flow_ofi_smoothing` family는 `holding_flow_ofi_smoothing_applied`와 `holding_flow_override_force_exit` stage를 수집해 flow 내부 OFI debounce/confirm 및 force-exit 우선권을 분리한다.

관리 대상 후보값:

- `SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE`
- `OFI_AI_SMOOTHING_STALE_THRESHOLD_MS`
- `OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED`
- `HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT`

holding/exit 쪽 `holding_flow_ofi_smoothing`은 `calibrated_apply_candidate` 후보가 될 수 있으며, same-stage priority와 AI correction guard를 통과하면 다음 장전 runtime env에 자동 반영된다. entry 쪽 `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 기존대로 기본 OFF이며, ON 전환은 별도 family metadata, manifest id/version, sample floor, fallback 급증 guard가 필요하다.

## Scale-in price guard threshold family

`scale_in_price_guard` family는 REVERSAL_ADD/PYRAMID 주문 직전 scale-in P1 resolver와 dynamic qty safety 표본을 수집한다.

수집 stage:

- `scale_in_price_resolved`
- `scale_in_price_guard_block`
- `scale_in_price_p2_observe`

관리 대상 후보값:

- `SCALPING_SCALE_IN_MAX_SPREAD_BPS`
- `SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS`
- `SCALPING_PYRAMID_MIN_AI_SCORE`
- `SCALPING_PYRAMID_MIN_BUY_PRESSURE`
- `SCALPING_PYRAMID_MIN_TICK_ACCEL`
- `SCALPING_PYRAMID_MIN_PROFIT_PCT`
- `SCALPING_PYRAMID_MAX_SPREAD_BPS`
- `SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED`
- `SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT`
- `SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT`

이 family는 resolved/block/P2 observe 건수, add_type, block_reason, qty_reason, P2 observe action, spread/micro-VWAP 분포, resolved-vs-curr, effective_qty를 장후 report 입력으로 남긴다. P2 `scale_in_price_v1`은 observe-only이며, threshold-cycle이 `SKIP`/`USE_DEFENSIVE`/`IMPROVE_LIMIT` 결과를 live 주문가나 주문 여부에 반영하지 않는다. PYRAMID quality 값은 `scalping_pyramid_quality_calibration`이 특정 종목 사례가 아니라 전체 one-share event의 `one_share_pyramid_opportunity_rows` sample floor/source-quality/provenance를 통과한 경우에만 다음 PREOPEN `auto_bounded_live` env 후보가 될 수 있고, 장중 threshold/env mutation 및 cap/quantity 계열 자동 변경은 금지한다.

현재 `scale_in_price_guard`는 `report_only_calibration`이다. calibration candidate에 포함되지만, resolved/executed cohort가 없으면 `hold_sample`로만 출력한다. sample floor를 만족하기 전까지 threshold-cycle 산출물이 scale-in env 값을 자동 변경하지 않는다.

## 운영 판정 기준

1. `threshold_events`와 family partition은 canonical raw/compact data다. 사람이 읽는 판정은 `data/report/README.md`의 Markdown 생성 기준을 따른다.
2. `threshold_cycle_YYYY-MM-DD.json`은 top-level threshold 후보, calibration candidates, safety guard, calibration trigger를 담지만 현재 top-level Markdown은 없다. 운영자가 매일 직접 판정해야 하는 항목이면 `data/report/README.md`의 누락 후보로 승격하고 날짜별 checklist에 Markdown 생성 작업계획을 만든다.
3. `statistical_action_weight`/`holding_exit_decision_matrix`는 retired archive이고 `threshold_cycle_cumulative`는 활성 누적 근거다. 보고서 자체는 주문/청산 authority가 아니다.
4. POSTCLOSE collector는 기본적으로 live append 중인 `pipeline_events_YYYY-MM-DD.jsonl`을 직접 읽지 않고 immutable snapshot을 만든 뒤 backfill한다. `stopped_source_changed`가 발생하면 snapshot source로 재실행하고, report는 `checkpoint_completed=true`일 때만 완주 산출물로 본다.
5. IO guard 또는 availability guard로 backfill이 중단되면 같은 snapshot/checkpoint에서 chunk size를 낮춰 resume한다. 같은 날 무리한 raw full rebuild를 반복하지 않고 checkpoint, raw file size, paused reason을 report/checklist에 남긴다.
6. PREOPEN에는 전일 POSTCLOSE에서 생성된 report/apply plan과 AI correction guard를 읽어 `auto_bounded_live` runtime env를 생성한다. 같은 날 성과를 장전 통과조건으로 쓰지 않는다.
7. 자동 threshold 적용은 `report-based-automation-traceability.md`의 `R5` active 단계로 관리하고, `R6`는 daily EV report와 threshold version별 post-apply attribution으로 제출한다.
8. `pipeline_events_YYYY-MM-DD.jsonl`은 당일 forensic raw stream이고, `threshold_events_YYYY-MM-DD.jsonl`은 compact decision stream이다. 고빈도 diagnostic stage의 반복 raw count는 source-quality/ops volume 신호이며, summary/sampling artifact 없이 threshold 승격/rollback 근거로 쓰지 않는다.
9. raw/snapshot 압축은 `compress_db_backfilled_files`가 verified/backfilled 파일만 대상으로 수행한다. 당일 raw와 `skipped_unverified` 파일은 수동 삭제하지 않는다.

## 금지 사항

- 장중 live threshold auto-mutation 금지.
- `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`, `auto_bounded_live` 외 apply mode 임의 추가/사용 금지.
- family별 sample floor, safety guard, owner 없이 threshold를 runtime에 반영 금지.
- raw JSONL을 사람이 직접 해석해 승격/롤백 판정을 닫는 것 금지. 필요한 경우 Markdown/report artifact를 먼저 만든다.
