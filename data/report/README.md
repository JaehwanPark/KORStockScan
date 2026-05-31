# Report Directory Inventory

작성 기준: `2026-05-20 KST`

이 디렉토리는 운영/감리용 산출물을 저장한다. 기본 원칙은 JSON/JSONL을 canonical data로 두고, 사람이 장후 판정에 바로 읽어야 하는 항목만 Markdown 리포트로 별도 생성한다.

report 산출물이 threshold calibration, 자동 threshold 적용, bot restart, post-apply attribution으로 이어지는 전체 추적성은 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)를 기준으로 확인한다. calibration은 새 관찰축을 만들지 않고 이 디렉토리의 기존 BUY, 보유/청산, decision-support 리포트를 source bundle로 읽는다.

## Bucket Runtime Calibration ON 기준

`SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 현재 기본값 `False`다. 즉, OFI/QI는 P2 내부 live 입력 feature로 계속 사용되지만 bucket별 threshold는 아직 runtime에 적용하지 않는다.

ON 가능한 시점은 다음 조건이 모두 닫힌 뒤다.

| 조건 | 현재 상태 |
|---|---|
| `data/config/ofi_bucket_threshold_manifest.json` 존재 | 완료. 초기 manifest는 global threshold와 동일값 |
| `OrderbookMicroP2Canary0504-Postclose` provenance 점검 | 2026-05-04 POSTCLOSE 예정 |
| `ThresholdOpsTransition0506` acceptance | 2026-05-06 POSTCLOSE 예정 |
| bucket별 sample floor 충족 | 미확정. manifest의 `min_bucket_samples`, `min_symbol_samples` 기준 필요 |
| 별도 workorder/체크리스트에서 단일 조작점과 rollback owner 확정 | 미확정 |
| env/code 반영 후 restart | 미실행 |

따라서 현재 기준 ON 예정일은 고정되어 있지 않다. 가장 빠른 검토 지점은 `2026-05-06 POSTCLOSE`의 `ThresholdOpsTransition0506` 이후이며, 실제 ON은 별도 승인된 workorder에서 `KORSTOCKSCAN_SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED=true`와 restart를 통해서만 가능하다.

## 현재 정기 Markdown 리포트

| 리포트 | 경로 패턴 | 생성 주체 | 주기/트리거 | 상태 |
|---|---|---|---|---|
| Server Comparison | `data/report/server_comparison/server_comparison_YYYY-MM-DD.md` | `src.engine.log_archive_service._save_server_comparison_artifacts` | full monitor snapshot에서 server comparison이 enabled일 때 | 정기 경로 존재. 최근 기본 wrapper는 `MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON=1`이라 자동 생성이 정책상 꺼질 수 있음 |
| Statistical Action Weight | `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.md` | `src.engine.daily_threshold_cycle_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 2026-04-30, 2026-05-01 생성 확인 |
| Holding/Exit Decision Matrix | `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.md` | `src.engine.daily_threshold_cycle_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 2026-04-30, 2026-05-01 생성 확인 |
| Threshold Cycle AI Review | `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.md` | `src.engine.daily_threshold_cycle_report` | threshold-cycle intraday/postclose cron | AI correction proposal + deterministic guard 결과 |
| Scalping Pattern Lab Automation | `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.md` | `src.engine.scalping_pattern_lab_automation` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | Gemini/Claude pattern lab의 improvement order/family candidate 요약. runtime/code 직접 변경 없음 |
| Code Improvement Workorder | `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md` | `src.engine.build_code_improvement_workorder` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | Codex 세션 입력용 구현 작업지시서. `generation_id`, `source_hash`, `lineage` diff로 같은 날짜 재생성/2-pass 구현 여부를 추적 |
| Threshold Cycle Daily EV | `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md` | `src.engine.threshold_cycle_ev_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 무인 threshold apply 이후 제출 기준 리포트 |
| Runtime Approval Summary | `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.md` | `src.engine.runtime_approval_summary` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 스캘핑 threshold-cycle 판정과 스윙 runtime approval을 합친 읽기 전용 요약. runtime 변경 권한 없음 |
| Runtime Apply Gap Audit | `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.md` | `src.engine.runtime_apply_gap_audit` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | discovery/bridge/runtime summary/workorder/preopen/post-apply 소비 누락을 후보별 ledger, retry queue, Codex 작업지시로 표면화. runtime 변경 권한 없음. 사용법은 [runtime-apply-gap-audit-user-guide.md](/home/ubuntu/KORStockScan/docs/runtime-apply-gap-audit-user-guide.md) 참조 |
| Swing Strategy Discovery Sim | `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.md` | `src.engine.swing_strategy_discovery_sim` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 스윙 safe pool 전체를 sim-only candidate와 8-arm 가상 전략 row로 확장하는 감사 리포트. runtime 변경 권한 없음 |
| Swing Strategy Discovery Labels | `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.md` | `src.engine.swing_strategy_discovery_label_builder` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | discovery arm의 1d/5d/10d/policy_exit label과 PENDING_ENTRY/ENTERED/EXITED/EXPIRED 상태 전개 요약 |
| Swing Strategy Discovery EV | `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.md` | `src.engine.swing_strategy_discovery_ev_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | arm/entry/sizing/exit/selection/sector/theme 축 source-only EV 리포트. surviving/avoid bucket을 표시하지만 runtime apply 권한 없음 |
| Bedrock Nova Lite Shadow | `data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_YYYY-MM-DD.md` | `src.tests.bedrock_nova_lite_shadow_report` | 수동 테스트 또는 shadow 토글 실행 | `gpt-5.4-mini` Tier2 payload에 대한 Nova Lite v1 테스트 비교. runtime enqueue는 `src.engine.bedrock_nova_lite_shadow`가 담당하며, latency/cost/prompt cache/action agreement/source linkage만 제공한다 |
| Bedrock Nova Lite v2 Shadow | `data/report/bedrock_nova_lite_v2_shadow/bedrock_nova_lite_v2_shadow_report_YYYY-MM-DD.md` | `src.tests.bedrock_nova_lite_v2_shadow_report` | Lite v1 primary 성공 후 v2 shadow 토글 실행 | `entry_price`/`holding_flow` Lite v1 primary payload를 baseline으로 Nova Lite v2를 shadow 비교한다. v2 결과는 report-only이며 Lite v1 route, threshold, order guard, bot restart 변경 권한 없음 |
| Bedrock Nova Primary Provider Audit | `data/report/bedrock_nova_primary_provider/bedrock_nova_primary_provider_YYYY-MM-DD.jsonl` | `src.engine.bedrock_nova_provider` | `KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=primary`일 때 | Bedrock Lite primary 우회 호출과 OpenAI failback 감사 row. Tier1 `gpt-5-nano`는 OpenAI route로 고정한다 |

## 비정기/legacy Markdown

| 리포트 | 경로 | 비고 |
|---|---|---|
| Preclose Sell Target legacy root | `data/report/preclose_sell_target_YYYY-MM-DD.md` | 2026-05-10 기능 제거 및 사용자 요청으로 과거 산출물 삭제 |
| Add Blocked Lock Markdown | `data/report/monitor_snapshots/add_blocked_lock_2026-04-16.md` | legacy 단발 산출물로 보이며 최근 snapshot 체인에서는 JSON만 생성됨 |

## 정기 JSON Snapshot

`deploy/run_monitor_snapshot_cron.sh` 또는 `deploy/run_monitor_snapshot_incremental_cron.sh`는 wrapper를 통해 아래 snapshot JSON을 생성한다.

| profile | 생성 JSON |
|---|---|
| `full` | `trade_review`, `performance_tuning`, `wait6579_ev_cohort`, `post_sell_feedback`, `missed_entry_counterfactual`, `holding_exit_observation`, `monitor_snapshot_manifest` |
| `intraday_light` | `trade_review`, `performance_tuning`, `wait6579_ev_cohort`, `monitor_snapshot_manifest` |

저장 경로는 `data/report/monitor_snapshots/{kind}_YYYY-MM-DD.json`이며 오래된 파일은 `.json.gz`로 압축될 수 있다. 이 계열은 API/dashboard/snapshot용 canonical JSON이며, 현재 설계상 전부 Markdown을 생성하지는 않는다.

## 정기 JSON/JSONL 산출물

| 산출물 | 경로 패턴 | 생성 주체 | 현재 Markdown |
|---|---|---|---|
| Daily Report | `data/report/report_YYYY-MM-DD.json` | `src.engine.daily_report_service` | 없음 |
| Threshold Cycle Report | `data/report/threshold_cycle_YYYY-MM-DD.json` | `src.engine.daily_threshold_cycle_report` | 없음. 단, 파생 Markdown 3종 생성 |
| Threshold Cycle Calibration | `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_{intraday,postclose}.json` | `src.engine.daily_threshold_cycle_report` | 없음. 장중/장후 2회 자동 calibration artifact |
| Threshold Cycle AI Review | `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.json` | `src.engine.daily_threshold_cycle_report` | `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.md` |
| Scalping Pattern Lab Automation | `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.json` | `src.engine.scalping_pattern_lab_automation` | `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.md` |
| Code Improvement Workorder | `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json` | `src.engine.build_code_improvement_workorder` | `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md`, `generation_id/source_hash/lineage` 포함 |
| Threshold Cycle Daily EV | `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.json` | `src.engine.threshold_cycle_ev_report` | `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.md` |
| Runtime Approval Summary | `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.json` | `src.engine.runtime_approval_summary` | `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.md` |
| Runtime Apply Gap Audit | `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.json` | `src.engine.runtime_apply_gap_audit` | `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.md` |
| Swing Strategy Discovery Sim | `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.json` | `src.engine.swing_strategy_discovery_sim` | `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.md` |
| Swing Strategy Discovery Labels | `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.json` | `src.engine.swing_strategy_discovery_label_builder` | `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.md` |
| Swing Strategy Discovery EV | `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.json` | `src.engine.swing_strategy_discovery_ev_report` | `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.md` |
| Cumulative Threshold Cycle Report | `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.json` | `src.engine.daily_threshold_cycle_report` | `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.md` |
| Threshold Compact Events | `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | `src.engine.backfill_threshold_cycle_events` | 없음 |
| Pipeline Events | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` | runtime pipeline event writer | 없음 |
| Gatekeeper Snapshots | `data/gatekeeper/gatekeeper_snapshots_YYYY-MM-DD.jsonl` | gatekeeper snapshot writer | 없음 |
| Post-sell Candidates/Evaluations | `data/post_sell/post_sell_candidates_YYYY-MM-DD.jsonl`, `data/post_sell/post_sell_evaluations_YYYY-MM-DD.jsonl` | post-sell feedback collector | 없음 |
| Bedrock Nova Lite Shadow Rows | `data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_YYYY-MM-DD.jsonl` | `src.engine.bedrock_nova_lite_shadow` | `data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_YYYY-MM-DD.md`; `gpt-5.4-mini` Tier2 호출 지점만 수집하며 Bedrock explicit prompt cache token bucket 포함 |
| Bedrock Nova Lite v2 Shadow Rows | `data/report/bedrock_nova_lite_v2_shadow/bedrock_nova_lite_v2_shadow_YYYY-MM-DD.jsonl` | `src.engine.bedrock_nova_lite_v2_shadow` | `data/report/bedrock_nova_lite_v2_shadow/bedrock_nova_lite_v2_shadow_report_YYYY-MM-DD.md`; Lite v1 primary baseline 대비 `v1_v2_action_match`, `v1_v2_score_delta`, `v2_parse_ok`, `v2_latency_ms`, `v2_estimated_cost_usd` 포함 |
| Bedrock Nova Primary Provider Audit Rows | `data/report/bedrock_nova_primary_provider/bedrock_nova_primary_provider_YYYY-MM-DD.jsonl` | `src.engine.bedrock_nova_provider` | Markdown 없음. Bedrock primary route가 켜진 호출의 provider/model/key-index/latency/usage/parse/failback audit trail |

## Markdown 누락 후보

아래는 JSON/JSONL canonical data가 있는데, 현재 운영자가 바로 읽는 Markdown 리포트가 없는 항목이다. “모든 JSON에 Markdown이 없어 문제”라는 뜻은 아니며, 장후 판정/감리 효율 관점의 후보 목록이다.

| 우선순위 | 누락 후보 | 근거 | 권고 |
|---:|---|---|---|
| 1 | `threshold_cycle_YYYY-MM-DD.md` | `threshold_cycle_YYYY-MM-DD.json`은 apply candidate, rollback guard, threshold snapshot을 직접 담지만 top-level Markdown은 없다. 현재는 `statistical_action_weight`와 `holding_exit_decision_matrix` Markdown만 파생 생성된다. | 장후 운영자가 threshold 후보와 적용 금지 사유를 한 장으로 보는 Markdown 추가 권고 |
| 2 | `performance_tuning_YYYY-MM-DD.md` | `performance_tuning_YYYY-MM-DD.json`은 gatekeeper, holding, dual persona, OFI bucket/source 분포까지 포함하는 핵심 장후 판정 snapshot이다. Markdown이 없어 감리/운영자가 JSON을 직접 열어야 한다. | 핵심 metrics/breakdowns/watch_items 중심 Markdown 추가 권고 |
| 3 | `trade_review_YYYY-MM-DD.md` | `trade_review_YYYY-MM-DD.json`은 `COMPLETED + valid profit_rate`, open/entered rows의 기준 snapshot이다. | full/partial, completed/open, valid profit basis 요약 Markdown 추가 권고 |
| 4 | `holding_exit_observation_YYYY-MM-DD.md` | holding/exit 감리와 `GOOD_EXIT/MISSED_UPSIDE` 해석에 쓰이는 JSON만 존재한다. | soft stop/rebound/post-sell 요약 Markdown 추가 권고 |
| 5 | `post_sell_feedback_YYYY-MM-DD.md` | post-sell 후보/평가 JSON은 있으나 장후 사람이 읽는 요약이 없다. | missed upside, good exit, extra upside 중심 Markdown 추가 권고 |
| 6 | `missed_entry_counterfactual_YYYY-MM-DD.md` | 미진입 기회비용 분석 JSON만 존재한다. | latency/liquidity/AI threshold/overbought blocker별 Markdown 추가 권고 |
| 7 | `wait6579_ev_cohort_YYYY-MM-DD.md` | WAIT 65~79 EV cohort JSON만 존재한다. 현재 owner가 약해졌지만 prompt/score 재판정 감사에는 유용하다. | 필요 시 archive 성격 Markdown 또는 dashboard-only 유지 결정 |
| 8 | `add_blocked_lock_YYYY-MM-DD.md` | 정기 full snapshot 생성에서 제외한 legacy 축이다. Markdown은 2026-04-16 단발만 있다. | 추가매수 blocker가 active owner일 때만 새 workorder로 JSON/Markdown 재개 |
| 9 | `daily_report_YYYY-MM-DD.md` | `report_YYYY-MM-DD.json`은 web/API/Flutter 소비용 구조화 리포트다. | 운영자 장후 판정용으로는 우선순위 낮음. dashboard-only 유지 가능 |

## 정상적으로 Markdown 제외해도 되는 항목

| 항목 | 제외 사유 |
|---|---|
| `monitor_snapshot_manifest_YYYY-MM-DD_profile.json` | snapshot 검증/압축/중복 방지용 manifest다. 사람이 읽는 판정 리포트가 아니다. |
| `pipeline_events_YYYY-MM-DD.jsonl` | raw event stream이다. Markdown은 파생 리포트에서 생성해야 한다. |
| `gatekeeper_snapshots_YYYY-MM-DD.jsonl` | raw snapshot stream이다. Markdown은 gatekeeper/performance 파생 리포트에서 생성해야 한다. |
| `post_sell_candidates/evaluations_YYYY-MM-DD.jsonl` | raw collector output이다. Markdown은 post-sell feedback 파생 리포트에서 생성해야 한다. |
| `threshold_cycle/date=*/family=*/part-*.jsonl` | compact partition이다. Markdown은 threshold cycle report에서 생성해야 한다. |

## 현재 파일 기준 확인 요약

- Markdown 정기 산출물: server comparison, statistical action weight, holding/exit decision matrix, cumulative threshold cycle.
- JSON snapshot 정기 산출물: monitor snapshots 7종, daily report, threshold cycle report.
- Markdown 누락 최우선 후보: `threshold_cycle`, `performance_tuning`, `trade_review`.
- OFI bucket runtime calibration은 현재 OFF이며, 2026-05-06 이후 별도 승인 없이는 ON하지 않는다.

## 누적/rolling threshold cycle report

`threshold_cycle_cumulative`는 daily report의 당일 판정을 누적/rolling 표본과 대조하기 위한 report-only 산출물이다. 기본 누적 시작점은 `2026-04-21` fallback 폐기 이후이며, rolling window는 최근 `5/10/20` calendar day다.

운영 해석 원칙:

- `COMPLETED + valid profit_rate`만 손익 표본으로 사용한다.
- `all_completed_valid`, `normal_only`, `initial_only`, `pyramid_activated`, `reversal_add_activated`를 분리한다.
- full/partial fill split이 없는 누적 손익은 hard 승인 근거로 쓰지 않는다.
- daily, rolling, cumulative가 같은 방향을 가리킬 때만 다음 checklist의 threshold 후보로 넘긴다.
- 이 산출물은 runtime change, bot restart, live threshold auto-mutation을 수행하지 않는다.
- 자동 threshold 적용과 적용 후 version attribution은 `report-based-automation-traceability.md`의 `R5/R6` gate가 별도 checklist owner로 닫힌 뒤에만 구현 완료로 본다.

## Efficient Trade-Off Calibration Source Bundle

calibration의 source는 `threshold_cycle` compact event만이 아니다. 아래 기존 report를 함께 읽어 `calibration_source_bundle`에 요약한다.

- `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/wait6579_ev_cohort_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/missed_entry_counterfactual_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/performance_tuning_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/holding_exit_observation_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/post_sell_feedback_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/trade_review_YYYY-MM-DD.json`
- `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.json`
- `data/report/panic_sell_defense/panic_sell_defense_YYYY-MM-DD.json`
- `data/report/panic_buying/panic_buying_YYYY-MM-DD.json`
- `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.json`
- `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.json`

`sentinel_followup_2026-05-07.md`는 단발 follow-up 기록으로 archive/reference에 남기며, 최신 calibration source bundle에는 포함하지 않는다.

`threshold_cycle`의 `calibration_source_bundle.report_only_cleanup_audit`는 현재 source bundle consumer가 없는 report-only/legacy 산출물을 매 실행마다 관리한다. 대상은 `sentinel_followup`, policy-disabled `server_comparison`, 정기 full snapshot에서 제외된 legacy `add_blocked_lock`, 제거된 `preclose_sell_target`이며, 결과는 source-quality warning/정리 후보로만 쓰고 runtime 변경 권한은 없다.

운영 원칙:

- calibration은 매일 `intraday`, `postclose` 2회 시행한다.
- `intraday`는 `threshold_cycle_calibration_YYYY-MM-DD_intraday.json`만 생성하고 runtime threshold를 바꾸지 않는다.
- `postclose`는 canonical `threshold_cycle_YYYY-MM-DD.json`과 `threshold_cycle_calibration_YYYY-MM-DD_postclose.json`을 함께 생성한다.
- 새 관찰축을 늘리지 않는다. 기존 report의 soft-stop tail, defer cost, trailing outcome, safety/provenance 요약을 calibration 입력으로 재사용한다.
- BUY 병목은 partial sample `0`을 live 전면 차단으로 쓰지 않고, score65~74 EV/close_10m 우위와 submitted drought를 `score65_74_recovery_probe` 후보로 연결한다.
- soft-stop/post-sell feedback은 10분 중심 분류를 유지하되 `1/3/5/10/20/30/60분` forward horizon을 함께 남겨 회복 지연, late rebound, defer cost calibration source로 쓴다.
- ADM/SAW는 all `no_clear_edge`이면 `hold_no_edge`로 두고, non-`no_clear_edge` + `candidate_weight_source` bucket만 advisory canary 후보로 연결한다.
- bad-entry는 naive hard block 재개가 아니라 `bad_entry_refined_candidate`의 soft-stop tail/defer cost 감소 후보만 calibration한다. 단, `bad_entry_refined_candidate`는 provisional signal이며 최종 유형은 진입부터 청산, 장후 `post_sell_evaluations`까지 `record_id`로 join한 lifecycle attribution에서 닫는다.
- `trade_lifecycle_attribution`은 bad-entry 전용 리포트가 아니라 entry price/passive probe, soft-stop, trailing, holding_flow, scale-in family가 공통으로 참조하는 전중후 attribution layer다. 각 family는 부분 로그의 즉시 라벨이 아니라 postclose joined lifecycle type을 calibration 입력으로 쓴다.
- `preclose_sell_target`은 2026-05-10 제거되어 tuning/calibration source와 운영 cron에서 제외한다. 과거 `data/report/preclose_sell_target*` 산출물도 사용자 요청으로 삭제했다.

## Statistical Action Weight 적용 범위

`statistical_action_weight`는 장후 action weight source이며 직접 runtime에 적용하지 않는다.

- 입력: completed trade, compact `exit_signal/sell_completed/scale_in_executed/stat_action_decision_snapshot`, 가격대/거래량/시간대 bucket.
- 산출: `exit_only`, `avg_down_wait`, `pyramid_wait`의 bucket별 confidence-adjusted score, `policy_hint`, `eligible_but_not_chosen` proxy.
- 1차 소비자: `holding_exit_decision_matrix` report-only matrix. bucket별 `recommended_bias`와 `prompt_hint`를 만든다.
- 금지선: `statistical_action_weight` 단독으로 runtime threshold, 주문/청산 행동, AI 응답을 변경하지 않는다.
- live/advisory 전환: 별도 checklist에서 sample floor, baseline/candidate/excluded cohort, safety guard, feature flag, cache/provenance가 닫힌 뒤에만 가능하다.
