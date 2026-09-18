# 장후작업 현행 활성 목록

## 0. 현행 기준 — 2026-09-17 KST

이 문서는 장후 **결과 점검 대상과 의도한 출력**의 목록이다. 기존 경로와 stable review index를 유지하되 과거 검토·배포·PID·성과 이력을 제거했다. index는 참조용이며 실행 순번·native 추천 ID·새 schedule가 아니다. 실제 실행 큐·Due·Acceptance·권한은 현재 체크리스트가 소유한다.

현행화 근거: 설치 `crontab -l`, 두 장후 systemd timer의 유효 `ExecStart/WorkingDirectory`, `data/runtime/runtime_release_selection.json`으로 선택한 실제 release의 `deploy/run_threshold_cycle_postclose.sh`, `run_widget_evaluation.sh`, `run_machine_microstructure_final_refresh.sh`, `run_ai_entry_setup_paired_replay_postclose.sh`, `run_postclose_done_controller.sh`, `run_postclose_finalization.sh`와 직접 consumer를 대사했다. 이것은 현재 실행 경로·기본 flag의 목록이며 해당일 자연 terminal·전수 경제성 PASS 표가 아니다. 다음 점검 때 설치 flag와 실제 run snapshot/marker를 다시 확인한다.

결과 판정은 [장후 결과 점검 지시문](../postclose-tuning-result-review-task-instructions.md)을 따른다. 모든 활성 작업에 실행 정상성·분석 유효성·결손/결함·달성 가능성·직접 소비를 별도 기록한다. source-quality/운영 작업에는 양수 EV를 요구하지 않고, 경제성 작업에는 exit 0·파일 존재를 유효 분석으로 인정하지 않는다.

## 2. 상태와 lock 표기

- `정기 ON`: 설치 trigger가 활성. 아직 도래하지 않은 실행은 `not_yet_due`다.
- `조건부 ON`: 기존 flag·source/trigger·checkpoint contract에 따라 실행/reuse/skip. skip에는 실제 reason과 유효 대체 artifact/date/hash가 필요하다.
- `embedded`: 기존 producer 내부 출력·소비이며 독립 process/cron가 아니다.
- `입력 owner`: 장중/연속 producer의 장후 소비. 새로운 장후 실행으로 중복 계수하지 않는다.
- `제외`: OFF/retired/on-demand 또는 현행 wrapper에 없는 독립 호출. missing을 실패·복원 과제로 만들지 않는다.

PID·lock·progress·deadline·latest terminal을 실제 run 기준으로 확인한다. lock 파일만 존재하면 장애가 아니고 오래됐다는 이유만으로 삭제하지 않는다. 동일 작업의 여러 generation은 마지막 consumer까지 대사하며 논리 작업 수에 더하지 않는다.

## 3. 상위 장후 실행 목록

| 예약 | 실제 실행 owner/entrypoint | 점검할 의도한 출력·직접 소비 |
| --- | --- | --- |
| 20:05 | router `eod` → KOSPI EOD update | 대상일 DB latest date/rows·status terminal → widget 시장 연구/EOD-dependent 입력 |
| 20:10 | router `postclose` → `run_threshold_cycle_postclose.sh` | §4 분석·manifest·verifier. 설치 bot action=`stop`, Swing=false |
| 20:10 | router `controller` → `run_postclose_done_controller.sh` | main/follower 대기·복구/차단 reason·최신 verifier·controller done |
| 20:10 | router `tuning` → `run_tuning_monitoring_postclose.sh` | predecessor 완료 뒤 Parquet/DuckDB late-pass·counts/hash·status success |
| 20:10 | `korstockscan-samsung-widget-evaluation.timer/service` → `run_widget_evaluation.sh` | §4.3의 네 producer·EOD wait·같은 completed target date |
| 20:50 | router `archive` → dashboard DB archive | 대상일 DB/archive 검증·최신 DONE·원천 보존 |
| 21:05 | router `paired-replay` → `run_ai_entry_setup_paired_replay_postclose.sh` | detailed batch→calibration→optimizer/holding→consumer의 같은 source generation |
| 21:15 | `korstockscan-machine-microstructure-final-refresh.timer/service` → `run_machine_microstructure_final_refresh.sh` | §4.4 전체 stage rc·approval·checklist·unit terminal |
| 21:55부터, bounded | router `finalize` → `run_postclose_finalization.sh` | predecessor→summary/tower/checklist/strict→cleanup→final detector terminal |
| 정기 5분, 21:50까지 및 finalization 후 | `run_error_detection.sh` | operational/source-quality unresolved critical·canonical/final detector의 stage별 실제 receipt |

공통 router와 독립 systemd는 각각 실제 selected root/commit·snapshot/WorkingDirectory를 확인한다. 이름이 비슷한 workspace 파일을 실제 실행본으로 간주하지 않는다. 21:15의 `After=widget evaluation`은 순서 관계이며 widget 분석결과 유효성과 source 계약은 별도로 대사한다.

## 4. 20:10 main wrapper 상세 목록

행의 번호는 기존 #1–#119에서 유지한다. 같은 논리 작업의 여러 EV/summary/workorder refresh는 한 행으로 묶었으며 모든 실제 generation의 마지막 소비는 확인해야 한다. `조건부`의 최종 ON/reuse/skip는 해당 run flag·trigger marker로 판정한다.

### 4.1 입력 고정·품질·기계/집행 분석

| 기존 index | 작업/호출 owner | 상태·역할 | 의도한 출력·핵심 판정 |
| --- | --- | --- | --- |
| #1–#4 | Bot stop / wrapper·pipeline immutable snapshot / snapshot retention | 정기 ON, 운영 | stop-only·고정 code/input hash·완료 snapshot만 cleanup. 운영 성공이며 EV 아님 |
| #5 | `backfill_threshold_cycle_events` | 정기 ON, 입력 | exact-date compact·EOF/checkpoint·raw/retained/excluded 보존 → Daily/EV |
| #6 | `sniper_post_sell_feedback`의 sim post-sell | 조건부 ON, source-only | 성숙/미완료·same-session 결과; actual 손익/승인으로 전환 금지 |
| #7 | `monitoring.limit_down_watch_report` | 조건부 ON, 진단 | source-valid 급락/유동성 위험과 no-observation 직접 사유 → 기존 source/workorder |
| #8 | `monitoring.rising_missed_intraday_feedback` | 조건부 ON, 진단/CF | exact opportunity·최초 blocker·후행 executable/proxy 분리 |
| #9/#101 | `monitoring.rising_missed_scout_workorder` | RETIRED, 사용자 삭제 | 신규 scout runtime·전용 producer/consumer·산출물 삭제. prior 후 refresh도 제거; 과거 source gap은 복원 사유 아님 |
| #10 | `monitoring.scalping_pyramid_intraday_feedback` | RETIRED | PYRAMID 런타임·튜닝 폐기; 과거 원장 archive-only, 신규 필수 입력/cron 없음 |
| #11/#74 | `observation_source_quality_audit` preflight/final | ON/trigger-gated, 품질 | exact scope/clock/hash·row/window exclusion·machine/AI/operational gate·counts → 경제성 admission |
| #12 | `monitoring.scalping_pyramid_quality_calibration` | RETIRED | 독립 grid/후보/PREOPEN 폐기; historical pending/체결/완료 정산 보존 |
| #13 | `monitoring.scalping_avg_down_recovery_calibration` 및 별도 replay capture | RETIRED | AVG_DOWN 독립 튜닝/수집 폐기; 기존 Main 기계 entry 정책 반등 신호를 guard 후 소비 |
| #14 | `monitoring.samsung_machine_entry_tuning` | 조건부 ON, actual 분석 | #74 후 한 번·actual policy/profile·실현/HELD/cost·유효 carry; timing 연구 별도 |
| #15 | `monitoring.low_price_two_leg_tuning` | 조건부 ON, actual 분석 | #74 후 한 번·actual policy·leg/holding/terminal·missing cost=null |
| #16 | `monitoring.low_price_two_leg_expanded_candidate_research` → `automation.low_price_two_leg_auto_expansion_policy` | 조건부 ON, 연구/발행 | 실제 state/catalog·candidate/calibration/holdout·checkpoint/resume·dated publication. bar touch≠broker fill |
| #21 | `monitoring.one_share_threshold_opportunity` | RETIRED, 사용자 삭제 | 신규 scout runtime과 함께 전용 threshold/AI review·producer/consumer·산출물 삭제; 현행 필수 작업 아님 |
| #23 | `scalping.entry_recheck_drought_controller` | RETIRED, 사용자 삭제 | 전용 score/WAIT 복구 runtime·budget·장후/PREOPEN·maintenance·산출물 삭제. 정상 machine RECHECK·보조 AI와 공통 제출병목 진단은 기존 owner를 사용; [폐기 검증](2026-09-18-entry-recheck-drought-retirement-review.md) |
| #27 | `scalping.microstructure_reaction_context` | 조건부 ON, feature 진단 | 원 receipt/required feature·delivery·동일 cutoff·missing/unproven → 기존 평가/감사 |
| #45 | `market_panic_breadth_collector --report-only` | 조건부 ON, context | exact market/window·coverage·panic cohort; 직접 BUY/SELL authority 없음 |
| #46 | `panic_sell_defense_report` | 조건부 ON, context | panic risk/holding source·실제 action과 진단 분리 |
| #47 | `scalping.scale_in_split_order_plan` | 조건부 ON, 기존 owner | ADD sizing/leg 원자성·actual/CF·cost·유효 empty/hold → scale-in consumer |
| #48 | `strategy_position_performance_report --sync` | 정기 ON, fact | real/sim·owner·full/partial·COMPLETED valid profit_rate·effective cost → Daily/EV |
| #49 | `monitoring.scanner_lookup_attention_tuning` | 조건부 ON, 경제성 | 독립 opportunity/actual arm·marginal CF·자본/자원 paired·baseline/holdout → existing candidate |
| #50/#51/#54 | `daily_threshold_cycle_report` 및 기존 AI correction/cumulative 출력 | ON/conditional·embedded | inclusive source-day 분모·선정/탈락/carry·cost/EV·AI provenance·same-generation cumulative |
| #50 내부 | 기존 mechanistic price / position sizing / atomic quantity·leg 정책 평가·발행 | embedded, 경제성/발행 | price-ready no-submit/no-fill·native executable replay·immutable signed source-date·chronological union/4-arm·paired/tail/capital → next-date publisher |
| #55 | `automation.entry_cancel_wait_tuning` | 정기 ON, 진단/기존 family | 현재 touch/mark proxy는 executable fill/exit/cost가 없으면 diagnostic hold·incumbent 유지; 시간 경과만으로 결손 해소 불가 |

### 4.2 AI·Pattern·EV와 최종 소비

| 기존 index | 작업/호출 owner | 상태·역할 | 의도한 출력·핵심 판정 |
| --- | --- | --- | --- |
| #67 | `analysis/claude_scalping_pattern_lab/run_all.sh` | 조건부 ON, source-only | 인과 feature/label·현재 유효 source·candidate evidence; 독립 Entry authority 없음 |
| #69 | `scalping_pattern_lab_automation` | 조건부 ON, handoff | 현재 pattern source/metric/consumer·추천 decision; 퇴역 axis 활성화 금지 |
| #71 | `pattern_lab_currentness_audit` | trigger-gated, 품질 | 최신 source generation·false reuse/결손 → source admission |
| #72/#94/#108 | `pattern_lab_ai_review` 및 current-generation provenance refresh | 조건부 ON, 리뷰 | 동일 scope 원 evidence/prompt/hash·review decision·후행 consumer 정합성 |
| #73 | `pipeline_event_verbosity_report` | 조건/reuse, 운영 | exact-date terminal freshness·source hash; raw suppression 비활성·EV 증거 아님 |
| #75 | `scalping.entry_split_order_plan` | 조건부 ON, 경제성/receipt | submitted/no-submit/no-fill·native quantity/leg 4-arm receipt·cost/exit·날짜 census → Daily |
| #76 | `scalping.ai_decision_quality` materialization | 조건부 ON, source-label v2 | control·보존 revision labels 두 출력→현행 case table diagnostic/compact; legacy baseline/paired/canary write/wait 없음 |
| #77 | `scalping.micro_reversion.ai_quality_cycle` | 완전 폐기 | 실행기·R2/R3 인계·전용 PREOPEN/live adapter 및 파생 산출물 제거. 환경 플래그로 복원 불가; 현행 compact 경로는 별도 보존 |
| #78 | `scalping.micro_reversion.main_ai_prompt_optimizer` | 조건/후행 refresh, 선정 | calibration 후보 고정·holdout·same-date freeze·현재 compact/legacy 분리 → publisher/consumer |
| #79 | `scalping.main_ai_holding_base_replay_batch` | 조건부 ON, holding 연구 | 원 holding stage/context·full-cost outcome·manifest; 초기 entry 분모와 분리 |
| #80 | `scalping.main_ai_prompt_consumer` | 조건부 ON, handoff | frozen evidence/current-role hash·trusted consumption → 기존 dated owner |
| #82 | `scalping.ai_action_outcome_calibration` | 조건/후행 refresh, 경제성 | natural machine 전체 actions + actual ENTER 후 AI screens·paired/case counts·incumbent 재판정·holdout/threshold/hierarchy/compact successor |
| 별도 기존 호출 | `automation.main_ai_current_axis` | 조건부 ON, manifest | 기존 current-axis source/metric/prompt partition·guard·consumer; legacy #81 live 복원 아님 |
| #89 | `monitoring.intraday_ws_freshness_monitor --finalize --monitor-only` | 조건부 ON, 품질 | type/route/epoch/원 clock·선언 scope/window·false invalid exclusion → #74/EV |
| #90/#92/#95/#104/#109 | `threshold_cycle_ev_report` 여러 refresh | ON/의존별, 경제성 요약 | 원 family EV·net profit·raw/economic/count·selected/blocked/carry와 새 source hash; 반복 refresh는 새 표본 아님 |
| #91/#103/#110 | `build_code_improvement_workorder` | 조건/후행 refresh, handoff | 의도한 defect/consumer/test·native ID/decision/authority·전수 disposition; 자동 repo 수정 아님 |
| #93/#107 | `pattern_lab_propagation_audit` | trigger-gated, 품질/handoff | 기존 pattern→manifest/selection/consumption의 source date/hash |
| #96/#105/#111 | `runtime_approval_summary` | ON/후행, 요약 | 전체 cohort/recommendation disposition·last consumer·기존 권한/경제성 gate; summary 성공≠live apply |
| #97 | `runtime_apply_gap_audit` | trigger-gated, handoff | publisher→PREOPEN/loader/PID의 실제 결손·미완료 acceptance |
| #98 | `automation.key_lineage_ledger` | ON, 품질 | source/report/candidate/selected/native ID/hash 보존·silent loss/conflict |
| #99 | `automation.conversion_lane --exclude-swing` | ON, handoff | 원 추천 전달·reason/authority; 미승인 신규 live owner 전환 금지 |
| #100 | `monitoring.rising_missed_classifier_prior` | 조건부 ON, source-only | 기존 miss prior·causal source; BUY authority 없음; #101 refresh 소비 |
| #106/#112 | `build_next_stage2_checklist` | ON/최종 refresh, handoff | 기존 stable ID·Due/window/Acceptance·단일 owner·same generation |
| 내부 trigger | `automation.automation_chain_trigger_decision` | embedded/최종 refresh, 운영 | run/skip 실제 predicate·reason·freshness/source hash; skip과 누락 구분 |
| #113/#116 | `verify_threshold_cycle_postclose_chain` pending/final | ON, contract | 최신 대상일 source/hash/mandatory artifact·실제 fail; allow-pending은 최종 strict 아님 |
| #114/#115 | backlog print-only / status·DONE marker | ON, 운영 | parser/단일 owner·현재 terminal; external Project/Calendar sync 없음 |
| #117 | `automation.tuning_performance_control_tower`와 `automation.postclose_summary_handoff` | 최종화/controller 소비, 요약 | late widget/machine/replay ready 뒤 tower→checklist→strict summary-handoff의 단일 generation; main 중간 DONE으로 종결하지 않음 |

### 4.3 Widget evaluation 네 분석 producer

| 순서 | 호출 module (`src.engine` 아래) | 의도한 결과와 달성 가능성 판정 |
| --- | --- | --- |
| 1 | `monitoring.widget_advisory_calibration` | raw/advisory before-gate opportunity·valid seed/무seed·incumbent reject·paired delta/holdout/자본; 자기 signal 평균을 전체 수익으로 사용 금지 |
| 2 | `monitoring.widget_auto_trade_policy_calibration` | 원 owner actual/CF·component guard·비용/exit·유효 carry; actual0과 source missing 분리 |
| 대기 | wrapper EOD terminal gate | 동일 completed date의 DB rows/최신 date; 실제 wait/timeout/fail; 별도 분석 producer 아님 |
| 3 | `monitoring.widget_symbol_signal_policy_research` | raw-valid scope/zero-day/census·calibration 후보 고정·일별 순익/holding 자본·executable/proxy 분리; raw-only에 signal 합성 금지 |
| 4 | `monitoring.widget_symbol_runtime_policy` | studied/selected/carry disposition·next-date publisher·guard/current source/version과 실제 loader; 자연 미소비는 미관측 |

### 4.4 21:15 Machine final refresh

| 순서/기존 index 대응 | 호출 module (`src.engine` 아래) | 의도한 결과와 달성 가능성 판정 |
| --- | --- | --- |
| 1 | `monitoring.widget_collector_expansion_recommendation` | actual catalog/state·유효 source/readiness·추천 ID·bounded source wait; 연구 watch 등록≠live universe 승인 |
| 2 / #17 기능 | `monitoring.machine_microstructure_attribution` | real signal/as-of ordered route source·micro checkpoint·actual fill/outcome과 source-only lane 분리 |
| 3 / #18 기능 | `automation.market_weakness_hysteresis_tuning` | attribution source→calibration family 고정→한 번 holdout→reviewed bounded candidate; proof 결손 승격 금지 |
| 4 / #19 기능 | `automation.machine_entry_timing_tuning` | actual adapter의 적정 fill 조건과 nonentry decision CF lane의 실제 수용/제외 predicate·동일1초 window/비용/exit·opportunity union; 원 signal 없으면 diagnostic |
| 5 | `monitoring.research_native_capacity_source` | native decision/opportunity census·allocation/capacity·source-date/hash·actual owner/menu; missing과 유효0 분리 |
| 6 | `automation.machine_research_closed_loop_refresh` | shared research→next-date publication→actual consumer/version/cost attribution의 기존 closure; 각 결손을 대기/구조 차단으로 판정 |
| 7 / #20 기능 | `automation.machine_microstructure_policy_approval --phase postclose` | source/economic/authority guard·same-stage owner·approved carry/selected disposition; main 권한과 혼합 금지 |
| 8 | `build_next_stage2_checklist --completed-machine-source-date` | upstream rc 실패에도 durable followup·같은 completed date/단일 owner; 마지막 builder 성공으로 선행 실패 은폐 금지 |

모든 rc와 unit Result/최신 terminal을 함께 대사한다. 21:15 기능은 active이며 #17–#20에서 제거된 것은 20:10 중복 사본이다.

## 5. 다음 자연 실행에서 분리해 확인할 것

BUY/HOLD sentinels·market opportunity census/pruned BBO·rising-missed 관찰·WS freshness·micro/holding journal·widget/advisory/research raw와 system metric sampler는 기존 입력 owner다. 각각 source-valid scope·coverage/as-of·exact key/clock·현재 policy/prompt·cost/exit/maturity와 위 reader의 실제 소비를 확인한다. 두 번째 collector나 같은 시장 분모를 만들지 않는다.

### 5.1 비활성 정기 작업과 경계

- Swing 전체 chain OFF: #56–#66/#70 및 strategy discovery/labels/EV/lifecycle/model retrain은 당일 필수 결손으로 세지 않는다.
- #22/#24–#26/#28–#42/#44/#52–#53/#68: ADM/LDM/bucket/greenfield·독립 institutional·overnight·latency 추천 등 퇴역. missing artifact로 복원하지 않는다.
- #81 legacy Main AI runtime family disabled. 기존 #77–#80 offline과 current-axis/기계 주판정·compact 전체의 비활성을 의미하지 않는다.
- #83–#88: codebase performance/time-window/producer-gap/stage-hook은 현행 기본 flag OFF. 기존 owner의 실제 활성 증거가 없으면 active로 세지 않는다. 잔존 CLI/검색 hit는 설치 trigger가 아니다.
- #43/#102: 현행 main wrapper에 독립 sim auto-approval/control refresh 호출이 없어 구표의 scheduled ON을 유지하지 않는다. 기존 sim prior/catalog의 source-only 소비와 퇴역 policy control-tower/prior refresh를 구분한다. base simulator·candidate-window·AI budget·price 관찰·post-sell feedback은 유지하고 퇴역 policy control/prior producer는 복원하지 않는다.
- #118 bot restart OFF, postclose stop-only. #23 누적 Entry AI gate backtest는 on-demand only이며 부족 표본 확보용 정기 producer가 아니다.
- 비활성 literal 호출도 대사한다: `swing_strategy_discovery_sim`, `swing_strategy_discovery_label_builder`, `swing_strategy_discovery_ev_report`, `swing_lifecycle_decision_matrix`, `swing_lifecycle_bucket_discovery`, `swing_lifecycle_audit`, `swing_pattern_lab_automation`; `codebase_performance_workorder_report`, `automation.time_window_regime_counterfactual`, `automation.producer_gap_source_bundle`, `automation.producer_gap_discovery`, `automation.stage_hook_workorder_discovery`, `automation.stage_hook_runtime_scaffold`. 이들의 조건부 코드 존재를 실제 ON으로 세지 않는다.
- `sync_docs_backlog_to_project --print-backlog-only`는 #114의 실제 module이며 운영 parser 소비다.
- monitoring instruction refresh는 문서 유지 owner이며 거래/경제성 분석이 아니다. 성능 benchmark/profile은 검증 도구이며 자연 장후 필수 결과 owner가 아니다.

## 6. 다음 상세검토 우선순위

먼저 due owner의 실제 실패/mandatory handoff, 다음 source/date/hash/count/cost 결손, 마지막 유효 비교의 EV/순익·tail·자본과 달성 가능성을 점검한다. main submit drought와 widget/episode 두 경로를 함께 우선하되 설치 producer 순서는 바꾸지 않는다.

[결과 점검 §9](../postclose-tuning-result-review-task-instructions.md#9-최종-판정과-보고)에 따라 각 활성 논리 작업의 결과 행을 작성한다: 기계적 terminal, 실제 출력/primary metric, 분석 판정, 결손/영향 범위, 시간 경과/구조 차단 판정, 직접 consumer와 다음 closure. 오래된 완료 이력을 반복하지 않고 미관측을 PASS로 채우지 않는다. 불명 ETA=null이다. 이 목록의 현행화 자체는 producer·API/Provider·report 재생성·policy apply·restart를 실행하지 않는다.
