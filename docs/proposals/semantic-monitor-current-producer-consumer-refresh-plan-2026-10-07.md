# 의미적 감시기 현행 생산자·소비자 전수 정합화 계획

작성일: 2026-10-07 KST. 상태: **사용자 구현·반복 코드리뷰·전체 작업본 통합 배포·재기동 승인(2026-10-07)**. 승인 대상은 이 계획의 의미적 감시 개선이며, 매매 정책·주문·hard safety 변경 권한은 포함하지 않는다. 아래 06:50~07:02 조사 표는 원 시점 기록으로 보존한다.

## 1. 목적·권한·기준

없어진 기능의 보고서를 계속 요구하지 않고, 개선된 기능이 실제 원천부터 마지막 소비자까지 연결되는지를 감시한다. 파일 존재·mtime·프로세스 생존만으로 정상 판정하지 않는다. 새로운 감시 프레임워크나 중복 보고서 체계를 만들지 않고 기존 producer, native validator, detector, notifier를 보완한다.

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 소유: [10/7 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md). [10/1 감시기 계획](semantic-monitor-postclose-integration-repair-plan-2026-10-01.md)은 구현 이력이지만 현재 Main 선정 계약의 소유자가 아니다.
- 현행 Main: [연속 반전 전환 계획](continuous-reversal-machine-policy-nextday-plan-2026-10-06.md)의 기계 12셀·보조 12셀, 비용 후 30분/+0.4%/soft -3% 선도달 누적 **raw 승률**. EV·손익비·최소 표본/일수·holdout·구 제출 보존 문턱을 추가하지 않는다. 비교 분모·라벨·원천·hash 검증은 성과 문턱과 구분한다.
- 프리/애프터 무표본 승계는 동일 종목군·가격대 REGULAR payload 및 부모 hash를 그대로 보존한다. `NO_LOCAL_SAMPLE`과 로컬 승률 null을 유지하며 부모 승률을 로컬 실적으로 표시하지 않는다.
- cell의 시장/종목군/가격대, runtime venue/session cohort, WS item/route/epoch, broker 실제 체결 venue는 별도 차원이다. SOR 관측 route를 실제 체결 venue로 추정하거나 연구의 5초 허용을 모든 runtime stale guard로 전파하지 않는다.
- 운영 AI 횟수 quota는 영구 `None`. provider 간격·외부 요청 제한·중복·timeout, broker/account/order/custody/수량/자본 cap·manual veto·hard safety는 유지한다. 오프라인 연구의 승인된 유한 호출 수는 운영 횟수 quota와 다르다.
- 위젯은 runtime/UI/API/수집/연구/장후 발행까지 영구 퇴역. 에피소드 일부 퇴역은 전체 에피소드 OFF와 다르다. 과거 custody·취소/매도·체결 영수증은 보존한다.
- `code_validated → selected_release → prepared → applied → actual_pid_consumed → natural_observed → submit/fill/terminal → economics`는 독립 상태다. 감시기가 매매 승인·기존 수량·정책·provider 설정·봇 상태를 바꾸지 않는다.
- 이번 문서는 기존 dirty 변경을 보존하고 신규 제안서만 추가한다. 실행 OPEN·시간표를 중복 생성하지 않는다. 구현 승인 후 하나의 현행화 owner를 현재 체크리스트에 등록하고 기존 자연 수용 owner와 연결한다.

## 2. 조사 시점과 현재 증거

2026-10-07 06:50~07:02 KST의 소스·기존 영수증·설치 설정을 조사했다. 아래는 이 시점의 증거이며 이후 예약기동의 성공을 예측한 판정이 아니다.

| 층 | 확인한 사실 | 해석/잔여 확인 |
| --- | --- | --- |
| 기본 작업본 | HEAD `ad9d03a1`; 기존 수정·삭제·미추적 파일이 있음 | 전체 작업본 clean/PASS로 주장하지 않음 |
| 선택 릴리스 | `continuous-reversal-20261007-v9`, `0d4e5d2a4004e89a20ea14eb05c720d812e5bb27` | selector가 가리키는 코드, 현재 Main PID 소비와 별개 |
| 주요 코드 정합 | submission monitor, artifact/process/episode/cron detector, notifier, summary, readiness, reversal kernel, owner retirement의 작업본/선택본 10개 파일 bytes 동일 | 다른 파일·별도 systemd pin의 동등성을 대신하지 않음 |
| 장후 native | 원천일 10/6의 13단계: 11 `succeeded`, episode_policy·research_allocation 2 `off` (`explicit_schedule_disabled`) | 실행 성공/명시 OFF와 연구·경제·장중 소비를 분리 |
| 준비 | 10/7 latest → `2026-10-06_882209483c2aed35_0d4e5d2a4004e89a/readiness.json`; `prepared_verified`, `actual_pid_consumed=false` | prepared의 Main/compact 정책 공통 SHA `69dfb87d…`; 실제 예약 소비는 OPEN |
| 최종 detector | 원천일 10/6 보고서, 관측시각 10/7 06:34:07; machine/auxiliary `cumulative_winrate_selected`, handoff `done` | 과거 원천일 복구 검사이며 10/7 장중 검사와 구분 |
| 잔존 경고 | 위 detector에 episode source gap/invalid capture, 구 Samsung forward failure, finalization 자기 검사 대기 경고가 남음 | 현행 대상·OFF·이력·검사 중 상태를 각각 판별; 일괄 삭제/실패화 금지 |
| 실제 실행 | 조사 시 Main·거래 에피소드 PID 없음; fill Telegram PID `4073127` 실행 | 07:32 apply/07:35 bootstrap/07:55 Main 이전 부재는 기동 실패가 아님 |
| 별도 pin | owner auto-apply=`511664f3`, final-refresh=v8, fill notifier=`1667abb9` 릴리스 | root가 다르다는 이유만으로 교체하지 않고 각 계약·실제 마지막 소비자를 비교 |
| 에피소드 범위 | 10/7 `profiles_for_target_date` 31개; 기존 체크리스트에 186 pin 보존 수용 기록 | 현재 설치·정책·PID 자연 확인은 개별 예약 시각 이후 별도 수행 |

원 증거: `data/runtime/runtime_release_selection.json`, `data/report/postclose_stage_terminal/2026-10-06/*.json`, `data/runtime/policy_bootstrap/prepared/2026-10-07/latest.json`, `data/report/error_detection/error_detection_2026-10-06.json`, systemd의 유효 `ExecStart/WorkingDirectory/MainPID`, `/proc` 및 Git worktree 목록. 기존 보고서 재생성은 하지 않았다.

미추적 연구·WS 대체 제안서는 선택 릴리스의 적용 증거로 사용하지 않는다. 이 조사에서 모든 별도 unit pin의 code-equivalence와 외부 Windows 상태를 실증한 것은 아니며, 해당 확인은 후속 수용 항목으로 남긴다.

## 3. 전수 점검의 경계와 등록 항목

전수 범위는 **현재 감시 entrypoint 전부, 등록 detector/cron/artifact/heartbeat 전부, native 장후 13단계 전부, 현행 정책·퇴역 소유권과 그 마지막 소비자**다. 무관한 연구 파일 전체를 매 실행마다 읽는다는 뜻이 아니다. 미등록 신규 경로와 잔존 legacy 경로도 아래 연결표에 포함한다. 정적 조사와 자연 실행 확인을 혼동하지 않는다.

### 3.1 감시 entrypoint와 등록 coverage

| 생산/실행 진입점 | 산출물·소비자 | 현행화 항목 |
| --- | --- | --- |
| `error_detector` 7개 detector/full 및 제한 mode | exact-date error report → `validate_report_contract` → `notify_error_detection_admin`/daemon incident | 모든 registered ID 초기화·실행·provenance를 유지; operational mutation과 전략 변경 권한 분리 |
| `run_buy_funnel_sentinel_intraday.sh` → buy_funnel_sentinel → submission monitor | source snapshot → `evaluate` + machine/execution/source semantics → 병목 알림 | 정규장뿐 아니라 설치된 08~19시 회차·exact attempt·fixed-watch 분모 반영 |
| submission monitor `--source-only` / `--delay-source-only` | probe/trace/pending 및 delay source → 독립 source semantics | CLI 존재와 실제 예약 설치 여부를 구분; Sentinel 실패가 원천 감시를 함께 끊지 않도록 점검 |
| `run_intraday_ws_freshness_monitor.sh` | pipeline/threshold/scanner 원천 → incremental freshness report/수용 | Main/episode 공통 원천, 정확 route·수신 기대·quiet tick과 stale 분리; workspace 진입은 선택 릴리스로 전달됨 |
| `system_metric_sampler` → resource_usage | CPU/I/O/메모리/디스크/FD 샘플 → health artifact | 감시 자체의 I/O도 측정; 자원 경고가 매매 위험차단의 정상 여부를 대신하지 않음 |
| postclose finalization → full detector → 최종 영수증 | strict/controller/cleanup → prepared 검증 → detector → DONE | v9의 detector-before-prepare 수리 보존; 자기 검사 pending을 terminal PASS로 합성하지 않음 |
| machine_trade_telegram | order_owner_registry confirmed fill → notification state | 살아 있는 Main/episode·과거 custody 체결 소비 유지; 구 unit description의 Widget 문구는 권한 증거가 아님 |

등록 7개 detector: `artifact_freshness`, `cron_completion`, `kiwoom_auth_8005_restart`, `log_scanner`, `process_health`, `resource_usage`, `stale_lock`. auth flag/token invalidation, 제한된 log rotation·stale-lock cleanup의 기존 운영 권한을 확대하지 않는다. lock은 나이만으로 제거하지 않는다.

등록 19개 cron ID를 빠짐없이 대조한다: `final_ensemble_scanner`, `threshold_cycle_preopen`, `buy_funnel_sentinel`, `bd_fbuy_accum_pre_intraday`, `holding_exit_sentinel`, `panic_sell_defense`, `buy_pause_guard`, `monitor_snapshot`, `swing_live_dry_run`, `threshold_cycle_postclose`, `postclose_done_controller`, `swing_model_retrain_postclose`, `tuning_monitoring_postclose`, `update_kospi`, `dashboard_db_archive`, `log_rotation_cleanup`, `postclose_finalization`, `system_metric_sampler`, `error_detection_full`.

등록 40개 artifact는 다음처럼 전부 분류한다. 실제 path/window/status/schedule contract의 소유자는 [artifact registry](../../src/engine/error_detectors/artifact_freshness.py)이며 동일 목록을 새 Python registry로 복제하지 않는다.

- 원천·발견 4: `pipeline_events`, `threshold_events`, `daily_recommendations_csv`, `daily_recommendations_diag`.
- 장전 2: `runtime_policy_bootstrap`, `threshold_preopen_status`.
- 장중·안전 9: `submission_bottleneck_monitor`, `buy_funnel_sentinel_report`, `bd_fbuy_accum_pre_artifact`, `holding_exit_sentinel_report`, `holding_exit_sentinel_premarket_report`, `holding_exit_sentinel_aftermarket_report`, `panic_sell_defense_report`, `market_panic_breadth_report`, `system_metric_samples`.
- 장후·작업지시 9: `runtime_approval_summary_report`, `threshold_postclose_status`, `postclose_done_controller_report`, `codex_workorder_runner_report`, `code_improvement_workorder`, `pipeline_event_verbosity_report`, `observation_source_quality_audit_report`, `codebase_performance_workorder_report`, `update_kospi_status`.
- Swing/연구 16: `swing_live_dry_run_status`, `swing_selection_funnel_report`, `swing_lifecycle_audit_report`, `swing_threshold_ai_review_report`, `swing_improvement_automation_report`, `swing_runtime_approval_report`, `swing_pattern_lab_automation_report`, `pattern_lab_currentness_audit_report`, `pattern_lab_propagation_audit_report`, `swing_model_retrain_diagnosis`, `swing_bull_period_ai_review`, `swing_model_retrain_report`, `swing_model_retrain_status`, `swing_model_registry_current`, `swing_daily_simulation_status`, `swing_daily_simulation_report`. Swing real OFF와 report/sim 설치 여부를 분리한다. 기존 schedule contract가 OFF/미설치를 구분하므로 이름만 보고 제거하거나 재활성화하지 않는다.

등록 heartbeat 6개: `main_loop`, `telegram`, `crisis_monitor`, `error_detection`, `sniper_engine`, `scalping_scanner`. [coverage 검사](../../src/engine/monitoring/error_detector_coverage.py)는 현재 ID 포함 여부만 검증하므로 **연결·퇴역·현행 schema coverage**를 추가 검증해야 한다. WS 연속 상태 갱신은 새 의무 heartbeat를 무조건 늘리는 대신 기존 원천 receipt와 연결한다.

### 3.2 현행 생산자 → 사실/산출물 → 소비자 전수 연결표

| 기능/상태 | 현행 생산자·원천 | 마지막 소비자·기존 감시 | 보완/검증 대상 |
| --- | --- | --- | --- |
| scanner 발견, active | final_ensemble/scalping scanner, promotion·cycle | watch admission → sniper, Sentinel/source monitor | 후보·등록·평가 분모 별도; fixed watch에 scanner ID를 강제하지 않음 |
| Main 고정감시 5종목, 변경 | `scalping/main_fixed_watch.py`, owner/broker flat, admission/generation | Main WATCHING → machine; snapshot fixed-watch identity | 005930/034020/403870/196170/036930, 동일 cap 안 5slot; NXT 적격 미확인을 결함/허용으로 합성하지 않음 |
| 정규화 WS·공유 완료봉, 공통 이관 | `kiwoom_websocket` + `bd_fbuy_accum_pre_scanner.write_ws_snapshot`, `trading/market/shared_ws_snapshot.py` | Main snapshot/entry source, episode gateway → WS freshness | producer PID/start/route epoch/sequence·원 수신시각·bar close 일치; 위젯 collector 복구 불필요 |
| 연속 반전 상태, 신규 | `continuous_reversal.observe_normalized`의 tick 접두 상태 | `current_snapshot` → `sniper_state_handlers` 첫 uptick 평가 | 등록→수신→state advance→event→평가의 age/sequence; 평가 cooldown·AI 간격과 수신 갱신을 분리 |
| 기계 12셀, 교체 | frozen reversal source + kernel → machine.json → joint publisher | dated bundle/current → `continuous_reversal_policy.live_policy`/assessment | frozen family/cell/rule/hash·event identity; 구 전략 selector를 현행 validator로 사용하지 않음 |
| 실제 AI 보조 12셀, 교체 | production prompt/input/schema + call-freeze/provider-results → auxiliary.json | selected cell arm → 실제 요청/응답 validator → compose | 실제 provider 호출·response ID·prompt/input/schema/component hash·attempt 연결; ENTER_NOW 아닌 호출 구분 |
| AI quota 영구 None, 변경 | `ai/hot_path_ai_symbol_budget.py`, ledger·runtime policy | dispatcher/Main 요청 → provider 정산·장후 ledger summary | total/group None 실제 소비; 오래된 env가 quota를 되살리지 않음; rate limit/간격/중복/timeout 유지 |
| 기계·보조 capture/trace, 변경 필요 | `ai_decision_trace` observation + compose metadata + pipeline | submission machine/source semantics → labels/후속 분석 | 생산 receipt의 event/cell/rule/arm·입력 hash 확인; wrapper 공통 prompt version만으로 cell arm 일치 주장 금지 |
| 원천 probe·exact route, active | source recovery probe, WS subscription/epoch, pending auxiliary capsule | `source_gap_semantics`, ws_receive_expectation/WS freshness | 등록 충돌·수신 지연·소비 지연·quiet tick·누락 입력 분리; 임의 route 대체 금지 |
| WATCHING·recipe 확인, 수리 이력 | Main evaluation gate/recipe fact, exact source | 기계 → provider 원응답 → 기존 WAIT/BUY 경로 | 구 목표가 gate/확인 fact 연결의 새 family 적용 여부; 구 recipe를 새 반전 추가 확인 의무로 만들지 않음 |
| 제출 병목, active | exact pipeline attempt·submit terminal | buy_funnel snapshot → `evaluate`/notify | machine non-entry, AI veto/timeout, 실제 submit guard/실패 별도; AI confirmed≠BUY, ENTER_NOW≠submitted |
| 실행자금·운영 계획, active | broker/account cache + economic observation/frozen contract | action별 경제성 관측·order preflight → capacity evidence | non-entry cache miss는 관측 결손; ENTER/주문 전 계좌 검증과 구분. 요청 실패≠자금 부족; 5초 재사용이 주문 freshness를 완화하지 않음 |
| entry price·delay, active | mechanistic numeric price owner + `pre_submit_delay_tuning` | effective price → delay state/receipt → final submit guard; delay source/execution semantics | 준비/소비/호가 시각 동일 generation; delay quote 진단≠fill/net PnL |
| initial quantity·entry split, active | initial quantity policy/bundle state + atomic entry_split plan | leg/order/timeout/terminal → initial_quantity semantics | 선택 수량·leg합계·partial/cancel·PID binding; EntrySplit OPEN 보존 |
| cancel-wait, active | exact parent submit/cancel/fill reconciliation + native producer | dated policy → runtime consumer/summary/bootstrap; cancel-wait semantics | 비교 없음·source gap·carry·false-zero 분리; DirectFamilySourceRepairEntryCancelWait OPEN 보존 |
| holding/exit, active/별도 승인 | holding path vote/trailing, profit stagnation, target ratchet, entry adverse/adaptive-exit의 승인된 owner와 terminal | owner loops → holding_exit_sentinel/profit_exit semantics → 정책/경제 요약 | 현재 enabled/enrolled owner만 기대; 새 entry family가 보유종목 exit 권한을 바꾸지 않음; TP 신호≠SELL/terminal |
| AVG_DOWN 공유 rebound, 변경/소유 분리 | shared rebound receipt + `avg_down_replay_capture`, scale_in_split | 등록 scale-in owner/order receipt → 전용 replay·장후 소비 | Main initial quantity와 scale-in 분모/정책 분리; PYRAMID 새 주문 복구 금지 |
| 잔존 episode 31profile, active | profiles_for_target_date → applied policy/preflight → machine/gateway capture | native source sequence/terminal → family_policy_semantics/episode_health | 31profile별 예약 시각·quarantine·code pin·policy hash·generation sequence; 저가 확대 rename에도 퇴역 exclusion |
| 실제 주문·체결·custody, active/과거 호환 | broker-native receipt + owner_custody_registry/order_owner_registry | owner exit/reconciliation, confirmed-fill Telegram, terminal economics | real/sim/CF·full/partial·owner·venue 별도; historical widget ID는 새로운 주문 권한이 아님 |
| 가격 라벨·미진입 결과, 변경/관측 | exact decision ID/continuous event/source manifest + completed price paths | outcome labels/attribution/미진입 분석 | 새 반전 연구는 구 ENTER+provider_called 행을 필수 모집단으로 쓰지 않음. 기존 자연 AI 라벨의 entry/entry_screen alias·정확 경로는 계속 검증 |
| timing/market weakness, 존속 | machine attribution → timing/hysteresis tuning | 전용 dated policy/runtime owner + native stage | report-only/carry와 active policy 구분; 새 Main 셀 선정에 구 threshold AND를 추가하지 않음 |
| research capacity/allocation, 조건부 | native capacity source/closed-loop refresh | summary/runtime recommendation intake | 위젯 소비 제거; allocation OFF 영수증 부재와 실패 구분; 남은 episode capacity는 유지 |
| PREOPEN·릴리스·PID, active | summary/strict/controller → finalization/readiness → 07:32/07:35 적용 | launcher/actual PID → runtime consumption → post-apply attribution | root·commit·source/target·sealed generation·parent CAS·cell family·quota receipt; prepared만으로 PID 소비 PASS 금지 |

연결표의 custody/exit/자금 검증은 기존 계약 보존 대상으로 포함한 것이며 새 정책 성과 gate가 아니다. `holding_profit_exit_semantics`·initial-quantity·cancel-wait는 이미 존재하므로 재구현하지 않고 변경된 입력/owner와 마지막 projection의 정합만 보완한다. 별도 adaptive-exit 등의 활성 여부는 현재 policy/env/position owner로 확정하며 소스 파일 존재만으로 active 판정하지 않는다.

### 3.3 native 장후 13단계 전체

공통 consumer는 [postclose_summary_handoff](../../src/engine/automation/postclose_summary_handoff.py)의 stage registry·artifact binding, strict verifier, controller다. 표의 기능별 consumer까지 연결하고 단계 성공을 정책 우위/실제 소비와 구분한다.

| stage | producer / 필수 산출물 | 기능별 consumer / 10/6 현재 상태 |
| --- | --- | --- |
| main_machine_policy | `continuous_reversal_postclose --mode machine`; machine.json/source.json 및 machine_policy/terminal carrier | joint dated 12+12 publisher/native handoff → Main / succeeded |
| main_auxiliary_policy | 동 producer `--mode auxiliary`; auxiliary.json/call-freeze/provider-results 및 compact carrier | 실제 AI 12셀 → compact runtime / succeeded |
| pre_submit_delay | `pre_submit_delay_tuning`; tuning/policy | delay runtime·source monitor / succeeded |
| legacy_machine_report | `ai_action_outcome_calibration --machine-only --report-only` | 구 진단·historical validator, 현행 Main selection 권한 없음 / succeeded |
| outcome_labels | `ai_decision_quality --postclose --write`; labels | 자연 판정 trace 라벨·진단; 새 반전 연구의 필수 선행 분모 아님 / succeeded |
| episode_policy | expanded candidate research + closed_loop_refresh family episode; research/refresh | 잔존 episode policy/native semantics / off |
| machine_attribution | `monitoring.machine_microstructure_attribution`; attribution | timing/weakness/legacy approval / succeeded |
| machine_timing | `automation.machine_entry_timing_tuning`; tuning | 해당 policy/consumer / succeeded |
| market_weakness | `automation.market_weakness_hysteresis_tuning`; tuning | 해당 guard/consumer / succeeded |
| research_capacity | `monitoring.research_native_capacity_source`; capacity | 잔존 연구/summary / succeeded |
| research_allocation | `automation.machine_research_closed_loop_refresh --family allocation` | 활성 scope만 recommendation/summary / off |
| legacy_policy_approval | `automation.machine_microstructure_policy_approval --phase postclose` | 전용 legacy diagnostic/guard, 새 반전 adoption gate 아님 / succeeded |
| summary_handoff | `postclose_done_controller --summary-handoff-only --require-independent` | exact summary/checklist/strict/controller→finalization→prepared / succeeded |

v9는 Main/compact의 native reversal report·sealed source·joint dated bundle를 이미 검사한다. 그 검사를 재사용한다. main_auxiliary의 현재 선행은 main_machine이며, 옛 labels/legacy report 성공을 추가 필수 선행으로 되살리지 않는다. machine_group가 같은 기계 정책을 재생성하여 보조의 source generation을 바꾸지 않도록 기존 단일 producer 소유권을 유지한다. stage OFF는 stage별 설정/영수증으로 확인하고 해당 family의 살아 있는 runtime/PID까지 OFF라고 확대 해석하지 않는다.

### 3.4 사라진 기능의 생산자·소비자 처리

| 기능 | 없애야 할 현재 의무/재활성화 경로 | 보존할 마지막 소비 |
| --- | --- | --- |
| Widget 전체 | 11개 기존 service/timer·collector·UI/API·manual/auto BUY·research/publication·widget_policy/collector_recommendation stage 기대 | shared WS/cost/episode 원천, 과거 custody/체결/exit 호환·archive receipt; 외부 Windows 제거는 사용자 확인 별도 |
| Doosan 및 추가 8symbol episode | 034020/002900/079160/111770/017670/080220/105630/181710/035720의 dedicated profiles/timers와 expansion 재등록 | owner_retirement registry, retirement 영수증·instance mask·기존 exit custody; 같은 종목 Main 관측은 금지하지 않음 |
| Samsung one-share·time machine | morning/midday/afternoon 신규 BUY/authority/timer 요구 | process_health의 기존 decommission 검사·과거 receipt/취소/매도 |
| 구 Main winrate_initial/VWAP 선정·hierarchy | 새 continuous_reversal family에 구 score/68.75bp/승계 hurdle·train/holdout·paired EV 강제 | frozen 구 generation의 audit validator, compatibility carrier·source custody |
| 구 Samsung frozen candidate 진단 | 현재 checklist owner가 없는 forward validation 실패를 현행 Main failure로 승격 | historical/report-only 실패 증거. source/hash 무결성 손상과 진단 실패도 구분 |
| Opening Rotation·upper_limit_watch | scanner/slot/new entry/postclose/PREOPEN 기대 | historical receipt/exit custody만 |
| ADM/LDM·matrix/greenfield·institutional aggregation·WAIT6579 bridge | 정책/환경 승계·소비/자동 복구 기대 | raw audit, active exact AI investor/program context와 전용 strategy 원천은 유지 |
| PYRAMID·legacy fallback/latency recommendation·panic lifecycle sim | 새로운 entry/scale-in/order·standalone policy/장전 추천 기대 | 현재 latency hard safety·panic report-only·과거 scale-in receipt는 유지 |
| Swing real OFF·whipsaw OFF·surviving sim | absent sample로 실거래/상세 튜닝 복원 요구 금지 | 설치된 report/sim owner만 조건부 검사; 공통 control tower 전체 제거 금지 |

퇴역의 정상은 단순 데이터 없음이 아니라 **신규 권한/producer 실행/필수 의존성 0 + surviving custody 소비 정상**이다. 위젯 이름이 남은 공통 cost schema나 unit Description은 단독 leak 증거가 아니다. 되살릴 수 있는 installer·generic template·expansion·gateway 권한과 실제 프로세스/주문 owner를 검사한다.

## 4. 확인된 불일치와 수정 우선순위

| ID/우선순위 | 직접 확인한 근거 | 영향·보완 |
| --- | --- | --- |
| SM01 / P0 | [notifier `_alert_results`](../../src/engine/notify_error_detection_admin.py)의 stage 허용 목록에 main_machine_policy 없음 | native machine source_invalid가 경고 상세에 있어도 구조화 알림에서 탈락. 동일 source/target/generation fixture에서 legacy_machine_report=1, main_machine_policy=0, main_auxiliary_policy=1 재현. 새 stage 등록과 전달 계약 보완 |
| SM02 / P0 | 같은 notifier의 recovery 상태 목록에 cumulative_winrate_selected 없음; fallback names도 main_machine_policy 누락 | 새 정상 generation으로 기존 incident를 해소하지 못할 수 있음. native findings/hash/date/stage 일치로만 복구, 단순 새 날짜/미관측은 복구 금지 |
| SM03 / P0 | [submission machine_semantics](../../src/engine/monitoring/submission_bottleneck_monitor.py)는 당일 machine_policy/terminal와 support-adjusted 구 score만 조회 | source=10/6/effective=10/7 native report/bundle를 장중에 정확히 읽지 못함. observation의 frozen family로 dispatch하고 날짜·native selection 계약 연결 |
| SM04 / P0 | 같은 함수가 strategy_raw_input·구 strategy.select/selector_leaf/effective_thresholds를 요구; capture의 runtime_consumption도 구 strategy_selection 필드를 작성 | native event/cell/rule/arm receipt 미연결·오경보 가능성. producer와 consumer 함께 보완하고 새 자연 관측 전에는 코드 경로 위험으로 표시; 임의 빈 값/legacy raw를 만들지 않음 |
| SM05 / P1 | artifact `_semantic_alerts`에 WidgetEpisodeNextSessionStartup1006/SamsungFrozenCandidateValidation1006/SemanticPolicyCoverageRemediation1006, cancel-wait에도 구 owner 문자열 잔존 | 현행 체크리스트 owner 없는 알림의 다음 행동 불명확. stable family→현행 parsed owner 매핑, 과거 owner는 이력 필드로 보존 |
| SM06 / P1 | 06:34 보고서의 삼성 forward failure/episode warning; `_samsung_forward_semantics`는 날짜·파일만으로 구 진단 계속 검사 | native family와 stage OFF/현행 owner/살아 있는 episode scope를 먼저 확인. 구 실패는 historical diagnostic으로 이동하되 잔존 31profile의 source/capture 결함은 숨기지 않음 |
| SM07 / P1 | process_health는 Samsung one-share decommission 검사, episode_health는 현행 profiles만 검사; owner_retirement 전체 대상 revival 검사는 그 둘에 없음 | 퇴역 대상은 정상 기대에서 빠지지만 불법 재기동을 놓칠 수 있음. 일반 retirement registry/transition receipts→timer/service/process/entry-owner 금지 검사 연결 |
| SM08 / P1 | coverage는 ID set 포함 여부만 검사; subset 검사에 submission monitor 등 신규 semantic ownership이 반영되지 않음 | 존재 coverage와 producer→last consumer coverage를 분리, 새 기능·OFF·historical fixture 누락을 실패로 검사 |
| SM09 / P1 | Rebase §7은 Main fixed watch 2slot 및 구 winrate_initial 승계 기준, 10/7 checklist·SPECS·native bundle은 5종목/연속 반전 12셀 | 명시 override 우선·충돌 공개. baseline 정정은 별도 명시 요청 시 owner 문서부터; 구 기준을 감시기의 추가 경제 gate로 적용하지 않음 |

SM01은 읽기 전용 pure 함수 fixture로 전달 누락을 확인했다. SM02/SM03/SM04/SM07은 코드 연결 불일치 확인이며, 아직 10/7 신규 장중 incident가 발생했다거나 무허가 주문이 존재한다는 뜻이 아니다. SM06 경고는 실제 보고서에 있으나 retired/OFF/활성 모집단별 재분류를 거쳐야 한다.

## 5. 구현 순서·수정 위치·종결 검사

### P0 — 새 Main producer/consumer/알림을 함께 연결

1. `artifact_freshness`의 기존 native reversal validator를 재사용한다. notifier에 main_machine_policy stage와 cumulative_winrate_selected의 **동일 결속 복구**를 추가한다. 성공 enum만으로 incident 제거하지 않는다.
2. submission `machine_semantics`를 frozen bundle family 기준으로 분기한다. native report source_date/publication/effective_date·joint cells·selection metric·inheritance를 확인한다. legacy generation은 기존 validator로 유지하되 current 결과와 분리한다.
3. `ai_decision_trace`의 기존 observation/capsule에 native event/cell/rule/arm·machine/aux component·실제 prompt/input/schema hash·PID/start ticks의 유효 receipt를 연결한다. compose metadata/trace/pending/outcome consumers가 같은 event/attempt를 소비하는지 검증한다. 해당 producer에 데이터가 없으면 명시 source_gap이지 통과가 아니다.
4. BLOCK/RECHECK의 provider 미호출은 정상, ENTER_NOW의 provider 미호출은 명시 preflight/cadence/dedup/source/transport 이유를 보존한다. compose의 `provider_called` 같은 판정 metadata만으로 실제 요청을 세지 않고 request/response/ledger 사실과 대조한다. AI PASS 이후 submit guard/실제 제출은 별도 funnel이다.
5. 종결: 12+12셀 native fixture·동일 source/effective hash에서 selection→PID receipt→semantic→notifier가 끝까지 연결되고 구 score/EV gate가 새 family에 호출되지 않음. 실패 mutation 1개마다 구체 이유·owner·closure_test를 출력한다.

### P1 — 퇴역·OFF·surviving scope·owner 현행화

1. 기대 모집단은 현재 registry/profiles/installed schedule·명시 OFF·retirement receipt·정책 family에서 산출한다. 기존 registries를 참조하는 작은 projection/검사로 구현하며 새 거대 registry를 만들지 않는다.
2. retired negative census는 `process_health`/`episode_health` 또는 기존 retirement validator에 연결한다. retired timer/service/generic instance·installer/expansion 신규 entry를 검출하되 Main 허용 종목·기존 custody exit는 오차단하지 않는다.
3. 구 Samsung forward/legacy diagnostics는 historical/report-only로 남긴다. episode stage OFF와 과거 report 경고는 별도 표시하고 현재 31profile source/sequence·quarantine·preflight/PID 검증은 유지한다.
4. 알림 owner는 현재 checklist stable ID와 producer owner를 분리 기록한다. 원천일/관측일/적용일·최초/최근 발생·affected/eligible/total·종목/route·누락 필드를 표시한다. 신규 결손과 historical_unrecovered, superseded_generation_unrecovered를 섞지 않는다.
5. 종결: retired absent=`retired_not_expected`, retired active/new BUY=`retirement_leak`, 명시 OFF=`off`, surviving active source missing=`source_gap`이 각기 판정된다. 현행 owner 매핑 누락은 명시 미결이다.

### P2 — 장후 전체와 다음 기동 마지막 소비를 연결

1. 13단계의 command/artifact/prerequisite/receipt/hash/last-consumer를 `STAGE_REGISTRY`에서 전부 검증한다. main_machine/main_aux는 joint publication, 나머지는 해당 native 계약을 사용한다. 성공 exit code와 no-comparable/carry/source_blocked를 분리한다.
2. dispatch→artifact→stage receipt→summary→strict/controller→cleanup→prepared→detector→DONE 순서를 보존한다. independent producer 재생성·moving generation·새 selector/checklist hash가 기존 준비를 무효화하는 경우 다시 봉인해야 한다. **이번 신규 proposal 자체를 준비 무효화/자동 재생성 요청으로 간주하지 않는다.**
3. release router/cron/systemd의 유효 root와 actual PID cwd/start/loaded family/hash를 수집한다. 오래된 pin은 해당 consumer 계약이 달라졌을 때만 후속 배포 대상으로 정한다. fill-only notifier 등의 별도 소유권을 보존한다.
4. 07:32/07:35/07:55 및 profile별 예약 전에는 future_due, 이후에는 적용/소비 영수증과 자연 원천으로 판단한다. prepared 또는 이전 원천일 episode PASS를 오늘 기동 PASS로 대체하지 않는다.
5. 종결: exact-date generation 전체 일치와 실제 Main/잔존 episode 자연 소비는 각각 영수증으로 확인. 자연 기회가 없으면 not_observed로 끝내며 강제 주문·provider 재호출·threshold 완화로 증거를 만들지 않는다.

### P3 — 감시 누락·자체 부하·회귀 종료

1. detector 7/cron 19/artifact 40/heartbeat 6/native stage 13 전체 등록 및 scope-eligibility를 검사한다. 새 semantic hook→notifier 상태 enum·owner 매핑까지 test로 연결한다. CLI만 있고 설치 소비자가 없는 경로도 드러낸다.
2. 기존 bounded tail/incremental cursor·content hash cache를 재사용한다. read 범위/중복/누락·rotation/truncation/midline·source identity 변경을 기록하고 truncated 창을 전수 관측으로 표시하지 않는다. 같은 대용량 파일을 hook별로 반복 읽는지 측정한다.
3. 한 invocation의 bytes/read 횟수·wall/CPU/I/O를 수리 전후 동일 fixture에서 비교한다. WS callback에 디스크/provider 작업·full-history 재스캔·거대 스냅샷 재발행을 넣지 않는다. 감시 부하 개선과 시장/자금 source gap 해소를 별도 보고한다.
4. 종결: review→fix→targeted regression→re-review에서 미해결 in-scope 결함 0. 자연 실행/경제성 미관측은 결함 0과 별도 상태로 남긴다. 이후 배포/재기동은 별도 승인 및 기존 예약 기동 owner를 따른다.

수정 위치는 기존 `engine/monitoring`, `engine/error_detectors`, `engine/scalping`, `engine/automation`, notifier 및 기존 tests다. engine root 신규 Python module은 기본 금지다. Kiwoom 요청/FID/parser/REG·recovery를 건드리게 되면 [공식 API reference gate](../kiwoom-api-data-contract.md)를 먼저 통과하고 upstream SHA·path·조회시각을 기록한다. 이번 계획 조사에서는 프로토콜을 수정하지 않았다.

## 6. 필수 회귀·자연 수용·실행 소유

| 검증 묶음 | 반드시 포함할 사례 | 종료 증거 |
| --- | --- | --- |
| native 선정 | 12+12 완전성/중복, raw wins/resolved, 비용·30분 라벨, prompt 실제 응답, REGULAR 무표본 승계/hash·로컬 null | native validator 결과; EV/minsample/holdout 추가 호출 0 |
| 장중 receipt | source/effective 날짜 분리, old/new frozen generation 혼재, cell/rule/arm/input mismatch, PID 재사용/start ticks, source-invalid와 미관측 | source→producer→consumer exact identity 및 부정 fixture |
| 알림 | native machine 경고 전달, cumulative 선택 복구, 같은 reason 다른 scope/세대, unresolved 이력, wrong date/hash/owner, quiet·unobservable 미복구 | 구조화 incident 상태·1회 전달/dedup, 실제 Telegram 호출 없는 test |
| 퇴역 | Widget producer/consumer absence, retired instance/generic template 부활, renamed expansion, 역사적 BUY 거부/SELL·취소 custody 허용 | registry/receipt/mask/authority fixture; 살아 있는 31profile 훼손 0 |
| 입력 freshness | route epoch/transport/observed/provider time, quiet tick·source gap 분리, completed-bar 끝시각, capture 동일 시각 연속 sequence, callback 상태 갱신과 요청 간격 독립 | 정확 시각/순서 분해; provenance 무효 통과 0 |
| 실행/자금 | non-entry cache miss 허용 범주, ENTER exact capital 결손, broker 거부, split partial/cancel/timeout, owner terminal/cost null | 주문 전 안전 미변경·missing≠zero/부족·real/sim 분리 |
| 장후/기동 | succeeded+empty/carry/source_blocked, OFF stage와 active runtime, 중간 세대/한쪽 stage 실패, stale prepared, source/publication/effective/as_of 분리, future_due/PID 소비 | 단계→last consumer 및 현재 코드/manifest/policy hash 결속 |
| 성능/실행 | tail 한도, cursor rotation/truncation/gzip, atomic publish read race, 여러 release pin, cron 단일 owner | bounded resource·설치/소비 비교 및 권한 누출 0 |

기존 테스트를 우선 보완한다: `test_notify_error_detection_admin.py`, `test_submission_bottleneck_monitor.py`, `test_continuous_reversal.py`, `test_reversal_auxiliary_contract.py`, `test_hot_path_ai_symbol_budget.py`, `test_next_session_semantic_coverage.py`, error-detector/coverage/schedule/process/artifact tests, `test_postclose_summary_handoff.py`, `test_next_preopen_readiness.py`, `test_widget_retirement.py`, `test_doosan_main_retirement.py`, `test_episode_retirement_main_watch.py`, source/sequence/quantity/cancel-wait 관련 기존 tests. 대상 code에 pytest·compile, wrapper 변경에 bash -n/contract test, 전체 diff-check를 수행한다. 실제 provider·브로커·주문 호출 없는 fixture를 사용한다.

자연 수용은 현행 체크리스트의 `DirectFamilySourceRepairMainMechanisticEntry`, `DirectFamilyPreopenPolicyHandoff`, `JejuEpisodeRetirementHpspAlteogenMainFixedWatch`, `DoosanEpisodeToMainFixedWatch`, `WidgetFullRetirement1006`, `EpisodeCaptureSequence1006`, `FixedWatchSourceAndCleanupRepair1006`, `FixedWatchBudgetSummaryPostcloseAcceptance1006`, `MainSubmitDroughtPathAcceptance1006`에 연결한다. direct cancel-wait/entry-split/low-price 원천 결손 OPEN은 해당 owner에 남긴다. 완료된 코드 review를 자연 표본 부재만으로 다시 OPEN하지 않는다.

현재 장중 원천 결손에 대해 무조건 다음 영업일까지 대기한다는 운영 계약을 만들지 않는다. source-only 수리도 실제 영향·권한·리뷰를 확인하여 별도 승인 범위에서 수행하며, 소급 provenance 합성·안전 guard 완화·무승인 restart는 금지한다. 계속 같은 증거로 재생성을 반복하지 않고 `blocked`/`not_observed` 및 필요한 새 증거·owner를 명시한다.

## 7. 이번 계획의 review/fix/validation

- 1차 검토: 구 10/1 Main 경제성 선정 계약을 현행화 기준에서 분리하고, 이미 구현된 native reversal/위젯 퇴역 수리를 다시 만드는 항목을 제거했다.
- 보완: notifier main_machine_policy 전달 누락을 pure fixture로 확인하고 P0로 승격; recovery enum/producer receipt를 같은 변경 묶음에 포함했다. 13단계 OFF와 surviving episode 상태를 분리하고 정적 조사·준비·자연 기동·경제성의 완료 기준을 분리했다.
- 재검토: 새 raw 승률 정책에 EV·표본/holdout gate를 추가하지 않음, quota None/기존 hard safety 보존, retired 위젯 복구 금지, 이전 원천일 detector를 오늘 PID 수용으로 합성하지 않음, checklist 중복 실행 owner 없음.
- 문서 검증: local link 10개 존재, registry의 artifact 40개/cron 19개 ID 본문 누락 0, 열거한 기존 test 경로 존재. 작업본 `git diff --check` 및 신규 제안서 no-index 공백 검사 PASS; print-only backlog parser PASS(28개 기존 항목, 외부 sync 없음).
- 생략/잔여: 문서 작업이므로 trading pytest·compile·wrapper 실행·provider/브로커 호출·전체 detector 실행·보고서 재생성은 하지 않았다. 별도 unit code pin의 전체 비교, 07:32/07:35/07:55 이후 실제 PID·자연 원천, 외부 Windows 제거는 아직 검증하지 않았다. 이것을 현행 감시 정상화 완료로 표시하지 않는다.
- 이번 종결은 계획 작성·검토·문서 검증이다. SM01~SM09 코드 수리·배포·재기동·정책 소비 및 자연 수용은 아직 수행하지 않았다.

## 8. 승인 후 구현·통합 배포 계약

사용자가 10/7 의미적 감시 개선의 구현, 결함 해소까지 반복 검토, 전체 작업본 통합 배포와 재기동을 명시 승인했다. 현재 실행 owner는 `SemanticMonitorProducerConsumerRefresh1007`이며, 기존 기계정책·PREOPEN·fixed-watch·episode 자연 수용 owner는 유지한다.

### 실행 디렉터리 결함 후속 보완

10/7 실제 Main의 `src/` 실행에서 체크리스트 파서가 4/13 고정 fallback만 찾고 현재 OPEN owner를 0건으로 반환하는 추가 결함을 확인했다. 사용자 후속 승인에 따라 문서 읽기와 glob을 해당 코드 릴리스 루트에 결속하고 4/13 checklist fallback을 제거한다. 오늘 날짜는 호출마다 KST로 계산하며 일반 backlog의 미래 작업과 명시적 오프라인 경로 지정은 유지한다. 의미적 감시기는 정확한 root/date 체크리스트를 직접 지정하여 오프라인 env나 과거/미래 문서가 현행 owner를 대신하지 않게 한다. 읽기 위해 process cwd를 변경하지 않는다.

동일 날짜 두 번째 코드 배포는 새 PID가 실행되기 전에 새 selector의 소비 영수증을 요구하는 순환 검증을 피해야 한다. 기존 native whole-chain PASS의 정확한 generation hash를 재검증하고 기존 살아 있는 PID의 bootstrap·cwd/start ticks·직전 native consumed receipt·원 PREOPEN/env/prepared를 결속한다. 이는 새 장후 PASS나 정책 채택이 아니라 같은 정책의 코드 인계이다. 새 PID 소비 뒤 기존 전체 계약을 다시 검사한다. current checklist의 기존 stable ID와 Acceptance를 재사용하며 이미 봉인된 자동 블록을 이번 작업본에 함께 기록한다. EOD·연구·정책·PREOPEN·checklist bytes가 그대로인 경우 관련 장후 stage를 재생성하지 않는다.

후속 실경로 검사에서 준비 문서 조회도 Main `src/` cwd를 잘못 거부하는 것을 확인했다. `verify_prepared`는 native router 및 exact-generation 검사로 읽기 전용 조회를 검증하고 process cwd를 요구하지 않는다. 새 준비를 만드는 `prepare`는 선택 release root에서만 실행할 수 있다. 경로 제한을 조회와 생성에 동일하게 적용하여 의미적 감시 경고를 잘못 만드는 결함까지 후속 배포 범위에 포함한다.

### Episode 준비·프로세스 관측 분리

09:15:03의 `episode_current_preflight_not_observed`는 당일 준비 producer가 완료되기 전 검사였으며 삼성중공업·롯데케미칼은 09:15:15~16에 준비를 마쳤다. 같은 날 시작한 실제 preflight unit이 active/activating인 경우에만 예약 시각부터 최대 60초를 `waiting_producer`로 기록한다. 명시 실패·지난 날짜·producer 부재·상한 초과는 그대로 경고한다. 거래용 authority validator와 scan 시작 조건은 변경하지 않는다.

Main과 episode 서비스의 실행 group이 달라 `/proc/PID/cwd` 읽기가 EACCES인 경우와 검사 중 PID가 종료한 경우는 `unobservable`로 기록한다. current state/date/profile/PID/policy/capture sequence/120초 freshness 및 producer의 선언 cwd와 unit 설정을 계속 대조한다. 선언 cwd를 실제 관측 cwd로 대입하거나 PID 소비 PASS를 만들지 않는다. 다른 원천 결함이 있으면 permission 관측 불가와 관계없이 경고하며 affected/eligible/total은 해당 profile 수로 제시한다. 원 상태·관측 불가 이유는 full report에 보존한다. current checklist의 기존 `SemanticMonitorProducerConsumerRefresh1007`과 `EpisodeCaptureSequence1006` owner를 재사용하고 이미 봉인된 checklist/정책·원 PREOPEN·186개 episode pin 및 episode PID/group은 변경하지 않는다. 후속 Main 감시 코드 배포·정상 재기동은 기존 사용자 승인 범위로 실행한다.

09:20 두 경고의 후속 점검에서 09:35 미래에셋의 별도 초기화 단계 오판도 확인했다. prior custody policy로 날짜를 넘긴 `daily_state_initialized` 기록은 첫 적격 완성 분봉 전에 생성되며, 오늘 entry policy의 소비 증거가 아니다. 당일 active service·valid authority, current date/PID/profile/cwd/real persisted capture·일반 초기화 sequence=1/전일 terminal 초기화 sequence=2·120초 freshness, READY·미시도·보유/leg/주문/평가/확인 대기 없음이 모두 성립하고, 현재 applied의 source_date에 해당하는 이전 native applied가 유효하며 그 profile/hash와 초기화 hash가 일치할 때만 `waiting_runtime_policy_binding`으로 분리한다. 상한은 해당 scan_start 분봉의 완성 시각(scan_start+1분)이며 별도 grace를 추가하지 않는다. 소비 PASS를 만들지 않고 그 이후의 미전환·평가 기록 hash 오류·보유/주문·결손·미확인 prior hash는 계속 경고한다. 추가 source 조회는 그 단계의 이전 applied 한 건만 읽고 캐시하며 atomic publication race는 unobservable로 남긴다. 원 09:35 관측과 native 정책 검증·오프라인 재현은 `data/report/episode_startup_observability/2026-10-07/followup-0920-and-0935-replay.json`에 보존한다.

09:25 경고 후속: sd_biosensor_morning의 preflight는 09:25:00 시작·09:25:15 성공이므로 완료 전 경고이며 위 exact-date 60초 waiting으로 처리한다. 추가로 그 검사 및 09:49 검사 중 새로 게시된 capture를 전체 검사 시작 시각과 비교하여 source_age_sec가 음수로 계산된 결함을 확인했다. 운영 호출은 state를 읽은 직후의 KST 시각을 별도로 전달하고 source_freshness_as_of를 기록하여 freshness 및 첫 분봉 대기 deadline을 그 시각에 검증한다. 관측 시각이 실제 읽기 시각 이후이거나 120초를 넘으면 계속 경고하며 미래 timestamp 허용치/신선도 상한을 늘리지 않는다. clock 없는 오프라인 호출은 지정 as-of를 유지하고 관측 clock이 naive/과거/invalid이면 계약 검증에 실패한다. 기존 owner/checklist·정책·PREOPEN·EOD와 개별 Episode 실행은 그대로 둔다.

- SM01~SM04: notifier에 현행 기계 stage와 exact-date/native-generation 복구를 연결한다. submission monitor는 frozen family에 따라 native reversal/legacy로 dispatch한다. 새 `continuous_reversal_consumption_v1`은 event/cell/rule/arm, source/publication/effective date, 두 component, 원 입력·판정·실제 보조 input/prompt/schema hash, snapshot 읽기 시각과 PID/start ticks를 결속한다. 새 계약에서 receipt 누락은 결손이며, 이전 capture는 `historical_reversal_capture`로 별도 계수한다. quote as-of와 WS 반전 snapshot 읽기 시각을 구분한다.
- 실제 요청 provenance에는 `continuous_reversal_request_binding`을 저장한다. request 준비와 원 응답 관측은 별도로 계수하고 compose의 provider_called를 실제 호출 근거로 쓰지 않는다. BLOCK/RECHECK의 미호출은 정상이며 ENTER_NOW의 미관측/원인과 partial source window를 남긴다.
- SM05~SM07: 현재 날짜 checklist의 parsed OPEN stable ID만 owner로 사용한다. producer/historical owner와 denominator를 보존하고 매핑 부재는 `UNRESOLVED_CURRENT_OWNER`다. native OFF 영수증은 explicit_schedule_disabled만 인정한다. 구 Samsung 실패 및 OFF episode 장후 결손은 historical_findings로 보존하며, 오늘 surviving 31profile 검사는 그대로 유지한다. episode applied의 생산자는 07:35 Main PREOPEN이고 publication grace는 60초다. failed producer는 grace 중에도 실패로 분류한다. 퇴역 registry/transition receipt를 이용한 batched unit·bounded process/new BUY census는 Main 관측과 기존 SELL/CANCEL custody를 제외한다.
- SM08: artifact 필수 coverage를 실제 40개로 완성하고 STAGE_REGISTRY의 command/artifact/prerequisite/native-validator/마지막 소비자 및 notifier/hook 연결을 검증한다. retirement·OFF·historical 상태는 현재 의무와 구분한다.
- SM09: Rebase의 2종목/구 선정 규칙은 현재 사용자 override·5종목 SPECS·native 12+12와 불일치한다. 감시기에 구 성과 문턱을 추가하지 않는다. Rebase/README/기준 runbook은 이번 승인에 포함된 명시 수정 대상이 아니므로 별도 baseline 수정 없이 충돌을 공개한다.
- 자원: 원 capture는 bounded complete-line tail로 읽고 inode/rotation/truncation을 확인한다. bytes/read count/partial window를 기록하며 전체 관측으로 합성하지 않는다. 기계 비진입과 요청 원천 없음이 확인된 때에는 대용량 응답 trace 재독해를 생략한다. WS callback에 새 디스크/provider 작업을 추가하지 않는다.
- 배포: 기존 사용자/generated dirty 변경을 보존하고 모든 현행 source 변경을 통합 immutable release로 만든다. selected router·cron·별도 systemd pin의 계약을 비교하며 fill-only/episode의 변경되지 않은 정책 pin은 보존한다. current checklist 변경 후 summary/strict/controller를 native로 다시 봉인하고 원 PREOPEN 준비 영수증과 새 문서 generation을 장중 handoff의 검증된 reseal로 결속한 뒤, 같은 날 원 PREOPEN·정책·env를 보존하는 intraday handoff로 승인 재기동한다. EOD·연구 frozen 원천·실제 연구 응답은 재생성하지 않는다.
- 완료 근거는 [실행 검토](../audits/semantic-monitor-current-producer-consumer-implementation-review-2026-10-07.md)와 `data/report/semantic_monitor_refresh/2026-10-07/`에 남긴다. code gate, 배포, 실제 PID/영수증, 자연 provider/submit/체결/경제성은 별도 상태다.

장중 인계 보완: 이미 열린 10/7의 PREOPEN을 소급 재생성하지 않는다. `intraday_release_handoff --prepare --reseal-postclose-source`는 원 PREOPEN/env/manifest/prepared index와 정책 bytes를 그대로 보존하고, native DONE/strict가 검증한 새 controller/summary/오늘 checklist의 hash를 별도 immutable receipt에 결속한다. dated policy hash 차이·moving generation·checklist 변경은 fail closed다. readiness는 이 승인된 결속만 인정하며 prepared의 실제 PID 소비 여부는 별도로 남긴다.

새 PID 기록 이후에도 원 summary/controller를 재작성하지 않는다. 현행 future-handoff consumer는 검증된 intraday reseal의 원 summary hash와 native consumed-PID receipt만 연결한다. selector의 정상 PID attestation 갱신은 허용하되 policy/env/PREOPEN/summary·consumption 변조는 거부한다. summary 회복의 publication은 원천일 10/6, prepared session은 10/7을 유지한다.

### Finalization의 과거 체크리스트 소비 보완

`strict_checklist_generation_stale` 후속 결함은 finalization DONE observer와 semantic postclose observer가 위 장중 인계를 소비하지 않은 데서 발생했다. 현재 날짜·선택 release·실제 살아 있는 PID/start ticks/cwd·bootstrap·native consumed receipt·봉인된 원천이 모두 일치할 때만 승인된 historical checklist snapshot으로 원 DONE의 세대를 다시 검증한다. 다른 원천·snapshot·DONE 해시 변경은 계속 실패한다. 새로운 finalization을 생성하는 경로는 현재 checklist 검증을 유지하며 원 DONE/summary/controller/PREOPEN을 재작성하지 않는다. 06:50 이후 완료된 이력은 `recovered_late`로 유지한다. 기존 `SemanticMonitorProducerConsumerRefresh1007` owner와 동결 checklist를 보존하며 [검토·배포 근거](../audits/finalization-historical-checklist-observer-review-2026-10-07.md)에 기록한다.
