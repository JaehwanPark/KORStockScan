# 장후작업 현행 활성 목록

## 0. 현행 기준 — 2026-10-02 KST

이 문서는 설치 예약, stage, wrapper 내부 producer, 정책 소비, OFF/퇴역 작업의 현행 목록을 소유한다. 파일명은 기존 참조 주소로 유지한다. 당일 OPEN·Acceptance는 [10/2 체크리스트](../checklists/2026-10-02-stage2-todo-checklist.md), 원칙·권한은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), 결과 점검·승인된 복구는 [장후 지시문](../postclose-tuning-result-review-task-instructions.md)이 소유한다. 문서 현행화는 작업 실행·보고서 재생성·배포·매매 재기동을 호출하지 않는다.

확인 근거는 설치 `crontab -l`, 두 독립 systemd timer/service의 effective 설정, [선택 릴리스 영수증](../../data/runtime/runtime_release_selection.json), 소비 release의 wrapper/dispatcher다. 확인 시 공통 selector는 `9dcbd482`, Widget/machine 분석 service pin은 `0a8fa0a0`다. 이후 값은 원 영수증을 따른다. 독립 승인 root와 실제 worker/PID 소비를 구분한다.

코드 owner는 [main wrapper](../../deploy/run_threshold_cycle_postclose.sh), [stage registry·dispatcher](../../src/engine/automation/postclose_summary_handoff.py), [Widget wrapper](../../deploy/run_widget_evaluation.sh), [machine wrapper](../../deploy/run_machine_microstructure_final_refresh.sh), [finalizer](../../deploy/run_postclose_finalization.sh)다. 작업본과 소비 root의 해당 코드도 대사한다. 과거 성공/실패를 현행 예약 또는 미래 자연 성공으로 복제하지 않는다.

정책 갱신 원천은 사용자 지정 **2026-09-29 이후 적격 자료**다. 첫날에도 비용·원천·독립 시간순 검증 조건을 통과하면 후보를 판정하며 이후 적격 날짜를 누적한다. 기계 v7/보조 v4 신규 선택 계약은 **10/2 원천의 장후 계산부터** 적용한다. 일반 clean-baseline 하한과 과거 감사·custody·rollback 보존은 별도다.

## 1. 설치 schedule

시각은 KST 예약 시각이다. EOD·자원·선행 대기 뒤의 실제 계산 시각은 run receipt가 소유한다.

| 시각 | 설치 owner | 실행·점검 경계 |
| --- | --- | --- |
| 매일 19:30~19:59 | `run_monitoring_instruction_refresh.sh --mode postclose` | workspace 문서 갱신. 문서 currentness/lock만 확인하며 장후 계산을 실행하지 않는다. |
| 평일 20:05 | router `eod` | 정확일자 EOD DB/status. 후처리의 선행 owner다. |
| 평일 20:10 | router `postclose` | main wrapper. 설치 `BOT_ACTION=stop`, Swing OFF, Episode 신규 후보 연구 OFF. 전용 family 계산. |
| 평일 20:10 | router `controller`, `tuning` | main/독립 선행 terminal과 같은 원천일 결과를 확인. 긴 대기는 계산 성공이 아니다. |
| 평일 20:10 | `korstockscan-samsung-widget-evaluation.timer` | 호환 이름이며 기존 Widget 범위 전체의 `widget_policy`를 실행한다. |
| 평일 20:50 | router `archive` | EOD 이후 DB archive·검증된 원천 보존. 경제성 정책 owner가 아니다. |
| 평일 21:15 | `korstockscan-machine-microstructure-final-refresh.timer` | `machine_group`: capacity→독립 6개 stage→summary. Main/compact 정책은 main wrapper가 launch한다. |
| 다음 KRX 거래일 05:00, 최대 06:50 | router `finalize --resolve-effective-today` | 직전 KRX 원천의 선행 확인→전체 controller/strict→cleanup→최종 detector→장전 준비. 선행 대기는 06:00에 끝나며 비거래일은 skip. |
| 평일 07:00~20:55 매 5분, 21:00~21:50 매 5분 | router `error-detection` | 정규 full 감시. source-date final detector는 finalizer 내부 인계. 매매 권한 변경 없음. |

`log_rotation_cleanup`은 finalization 내부 후행이다. `postclose_exit` snapshot도 main 내부 호출이며 별도 장후 cron을 추가하지 않는다. 두 timer는 설치 active이며 다음 예약의 자연 성공은 별도 확인한다.

## 2. Stage 영수증과 의존관계

Registry의 15개 이름은 실제 계산 수나 경제 튜너 수가 아니다. `off/explicit_schedule_disabled`, `deferred/failed`, 정상 carry와 후보 선정을 exact-source terminal로 구분한다. `data/report/postclose_stage_terminal/YYYY-MM-DD/<stage>.json` v2의 source/publication/effective date, code/input/output/prerequisite hash, run/PID/시작·heartbeat·exit, policy disposition을 확인한다.

| stage | 실행·선행 | 역할 |
| --- | --- | --- |
| `main_machine_policy` | main launch; 원천 preflight·자원 | `ai_action_outcome_calibration --winrate-policy-only`; 승률 정책/terminal·완료봉 원천·제외 분모·dated handoff. |
| `pre_submit_delay` | main launch; family source ledger | 첫 제출 지연 튜닝/정책. 진입판정·분할 shape와 별도 축. |
| `outcome_labels` | main launch | `ai_decision_quality --mode postclose`; exact route 후행 라벨. 후보 선정 권한 없음. |
| `legacy_machine_report` | main launch | 이름을 유지한 full Main 평가·전략 정제. 현재 `--machine-only --activate-now`; 적격 전략의 current 선택까지 포함. |
| `main_auxiliary_policy` | main launch; labels + full Main report | compact 응답→paired full-cost 경제성→선정·발행·consumer. |
| `episode_policy` | main, 현재 OFF | expanded research/episode refresh 주소. 9/29 이후 forward-only 미지원 신규 연구 OFF. 기존 Episode 실매매/applied 정책은 유지. |
| `widget_policy` | Widget timer; EOD | advisory→auto policy calibration→signal research→family refresh/정책 적용 보고. |
| `research_capacity` | machine group 첫 단계 | native cash/inventory·capacity source receipt. 과거 원천을 현재 계좌 값으로 합성하지 않는다. |
| `collector_recommendation` | machine group; labels | 기존 bounded collector 추천·exact source/replay 검증. |
| `machine_attribution` | machine group | owner/route/시각/비용 결속 진단·다음 관측 manifest. |
| `machine_timing` | machine group; attribution | 진입 확인 지연·rebound 연구 및 exact-date timing 정책. |
| `market_weakness` | machine group; attribution | activation/release hysteresis와 exact-date 정책. |
| `research_allocation` | machine group; Widget + Episode + capacity | 공동 자본 비교. 유효 Episode OFF면 공동 stage도 OFF. Widget 단독 연구를 공동 성공으로 바꾸지 않는다. |
| `legacy_policy_approval` | machine group; attribution | 승인 queue/기존 PREOPEN handoff/원천 followup. 자체 주문·env 변경 없음. |
| `summary_handoff` | 그룹 끝·최종 closure | producer/summary/checklist/strict와 controller 결속. summary-only `summary_verified`와 전체 `done` 구분. |

`main_machine_policy` recovery의 빈 commands는 기존 발행물의 원천·승계 검증이며 새 계산으로 세지 않는다. OFF도 유효 terminal을 요구하며 missing을 OFF로 추정하지 않는다.

복구 Main과 compact를 함께 launch할 때 compact는 기존 제한(기본4시간) 안에서 선행 Main/labels 종료를 compute slot 밖에서 기다린다. terminal 실패·오염이 있는 peer는 다른 pending peer 때문에 대기하지 않고 deferred로 남긴다. 10/2 수리본의 코드 검증과 현재 소비 release는 [당일 복구 감사](../audits/postclose-semantic-source-monitoring-2026-10-02.md)를 따른다. 복구를 이유로 provider/예산·정책·주문 guard를 변경하지 않는다.

## 3. 독립 timer 내부 작업

### 3.1 Widget

outer wrapper→`widget_policy` dispatcher→정확일자 EOD gate→`widget_advisory_calibration`→`widget_auto_trade_policy_calibration`→`widget_symbol_signal_policy_research`→`machine_research_closed_loop_refresh --family widget` 순서다. 마지막 owner가 runtime policy/refresh를 결속한다. recovery는 검증된 기존 연구의 family refresh이며 전체 신규 연구 성공으로 기록하지 않는다.

기존 운영·명시 watch, `PASS_WITH_DATE_EXCLUSIONS`, 비용·동일 기회·holdout, deferred 모집단을 보존한다. 연구 max100/추가 history backfill 기본10의 기존 한도는 지시문·producer 계약을 따른다.

### 3.2 Machine group

capacity 완료 후 collector·attribution을 dispatch하고 두 부모의 현재 재실행이 terminal이 된 다음 timing·weakness·allocation·legacy approval을 dispatch한다. 후행은 자기 exact prerequisite receipt를 검증한다. 마지막 summary를 인계한다. main machine·compact·labels·Episode는 그룹의 검증 대상이며 이 timer가 다시 계산하는 목록에 포함하지 않는다. heavy child는 host 공통 두 slot, waiting은 slot 밖에서 수행한다. collector 실패가 다른 독립 분석을 취소하지 않는다.

timing/weakness는 report와 다음 날짜 policy/evidence를 쓸 수 있고 attribution은 관측 manifest를 쓸 수 있다. unit exit/stop만으로 정책 미작성·오염을 판정하지 않고 실제 SHA·생성시각·carry/후보·consumer를 대사한다.

## 4. 20:10 main wrapper 상세 목록

현재 설치 설정의 논리 호출 순서다. launch는 완료 순서를 뜻하지 않는다. early source/resource/command 실패 뒤의 후행은 미실행으로 남긴다. OFF 분기는 §6에 모았다.

| 순서 | producer/제어 | 역할·후행 소비 |
| --- | --- | --- |
| 1 | EOD gate·실행 snapshot/run ID·bot isolation·자원 admission | 원천일/발행일/예정 적용일 고정. 설치 stop 동작은 기존 owner 권한. |
| 2 | `ai_action_outcome_calibration --ensure-economic-reference-only` | 검증 비용·완료봉 근거 준비. live budget/정책 발행 없음. |
| 3 | 비활성 stage OFF receipt | 현재 Episode 연구 OFF 포함. |
| 4 | `monitoring.rising_missed_intraday_feedback` | miss/blocker·후행 진단. retired scout 복원 없음. |
| 5 | `observation_source_quality_audit --audit-phase preflight` | 불량 row/window 제외, 전역 원천 결손 차단. |
| 6 | `main_machine_policy` launch | 비용 결속 첫 도달 승률·dated 정책. 독립 AI/Widget 연구 완료를 기다리지 않는다. |
| 7 | `market_panic_breadth_collector` | 시장 context/report. |
| 8 | `strategy_position_performance_report` | exact trade fact-sync receipt 검증·실제 체결/terminal/cost census. `SKIP_DB`는 명시 skip. |
| 9 | `scalping.scale_in_split_order_plan` | 적용 가능한 실제 ADD fill의 조건부 비용 비교·정책. |
| 10 | source ledger 봉인→`pre_submit_delay` launch | 원천 summary/count/hash 대사 후 첫 제출 지연 평가. |
| 11 | `scalping.entry_split_order_plan` | submit/no-fill·운영 owner·cost/budget·동일 모집단 분할 비교. |
| 12 | `outcome_labels` launch | 검증 완료봉 exact route 재사용·기존 제한된 보강 또는 source gap. |
| 13 | `automation.entry_cancel_wait_tuning` | 취소 대기·native 청산 비용 비교·정확 적용일 정책. |
| 14 | `scalping.initial_quantity_policy` 조건부 refresh | 유효 current가 source date에 적용되면 immutable refresh stage. effective 전 skip, current 손상 실패. |
| 15 | `pipeline_event_verbosity_report` | 운영 진단. primary 경제성 분모와 별도. |
| 16 | `observation_source_quality_audit --audit-phase final` | 최종 consumer admission·원천 품질. |
| 17 | `monitoring.low_price_two_leg_tuning` | 기존 actual/held/custody/terminal/cost 경제성. 신규 Episode 탐색 OFF와 별도. |
| 18 | `legacy_machine_report`, `main_auxiliary_policy` launch | full Main 전략 정제; labels/full report 이후 compact 평가·승계. |
| 19 | `intraday_ws_freshness_monitor --finalize --monitor-only` | 증분 state·symbol master·통합 scanner lookup-attention section. |
| 20 | `monitoring.rising_missed_classifier_prior` | 정확 attempt 비용 차감 비교·next PREOPEN receipt. |
| 21 | `run_monitor_snapshot_safe.sh`, profile `postclose_exit` | trade_review/post_sell_feedback/missed_entry_counterfactual/holding_exit_observation 네 산출물의 날짜·manifest/SHA. holding/exit 및 PREOPEN 원천. |
| 22 | stage `wait`→`runtime_approval_summary` | 비동기 main family terminal 뒤 직접 family·정책·consumer 요약. 독립 timer 전체 완료와 별도. |
| 23 | `build_next_stage2_checklist` | 다음 KRX 거래일 owner·source repair/자연 수용 투영. |
| 24 | 성공한 full Main/compact scoped verifier | `--require-summary-handoff`·정확 publication/effective date. scoped PASS와 전체 closure 구분. |
| 25 | preterminal verifier→print-only parser→`--seal-main-run --expected-run-id` verifier | pending DONE 검증·실제 run 봉인. 최신 실패를 과거 PASS로 덮지 않는다. |
| 26 | `initial_quantity_activation` 조건부→main status/DONE | 적격 refresh만 release-set lock/parent CAS로 선택. main DONE과 독립 작업 전체 DONE 구분. |

<a id="44-ev승인최종검증-단계"></a>

## 5. 최종화와 정책 소비

### 5.1 전체 장후 closure

필수 stage의 유효 terminal/OFF→source generation→summary/tower/checklist→strict `--require-summary-handoff`→전체 controller `done`→cleanup→exact-source 최종 detector→장전 prepared를 확인한다. finalizer는 controller를 `POSTCLOSE_STAGE_WORKER=1`로 실행하고 `summary_verified`가 전체 `done`을 덮지 않게 검증한다. code/input/output/prerequisite/strict checklist generation 변경 시 이전 PASS를 재사용하지 않는다.

선행 실패/timeout/deadline이면 cleanup을 실행하지 않는다. cron은 exact-source 최신 pre-cleanup FAIL과 cleanup run 부재를 `blocked_by_finalization`으로 구분하며 parent FAIL을 유지한다. 실제 cleanup 실패·미상 원인·다른 날짜는 일반 판정이다. 복구는 원본 FAIL을 보존한 승인된 `--recover-closed-target`와 정식 선행 재검증을 따른다.

### 5.1.1 보관 생산자의 장후 source custody

Main DONE·DB 적재·snapshot manifest만으로 원 canonical 파일의 모든 후행 소비가 완료된 것은 아니다. 후속 보관 수리본의 `compress_db_backfilled_files`는 native 미종결, 다음 KRX 정책일 미경과, 전체 controller 미종결/receipt 검증 실패의 원천 날짜를 압축에서 보류한다. 같은 날짜의 raw·snapshot·threshold snapshot·canonical context·summary·partition과 보류 사유를 묶는다. metadata/깨진 symlink/불완전 receipt는 fail closed다. 보관 압축이 이미 발생했다면 봉인 manifest와 해제 hash가 같은 canonical snapshot만 복원하고 원 gzip을 보존한다. raw의 archive identity를 확인하며 representation 변경의 영향 ledger/최종 consumer를 재결속한다. cutoff/compute/정책/주문 한도를 바꾸지 않는다. 이 guard의 현재 선택 여부는 [10/2 감사 영수증](../audits/postclose-semantic-source-monitoring-2026-10-02.md)이 소유한다.

### 5.2 정책별 선택 경계

| owner | 선택·소비 경계 |
| --- | --- |
| Main 승률 | dated staging→정확 날짜 `--activate-dated-winrate`/parent CAS→PREOPEN/bootstrap/PID. |
| Main full 전략 정제 | `--machine-only --write --activate-now`→적격 scope/source/비용/승계 검증→immutable generation/current parent CAS. 현행 지속 계약은 새 attempt부터 소비하고 다음 적격 generation까지 승계한다. current·dated handoff·PID 각각 확인. |
| Compact 보조 AI | paired full-cost/응답/독립 검증→machine 부모 결속 publisher/dated consumer/PREOPEN. CAUTION 후행 경로·원천/비용 결손을 성공으로 대체하지 않는다. |
| Entry/submit/scale-in/timing/weakness/수량/holding/exit | 전용 publisher·bounded 축·부모/날짜·override/lock·rollback/loader 계약. 공통 보고서 성공으로 새 live 권한을 만들지 않는다. |
| Widget/Episode | applied policy·profile/격리·systemd pin·loader/preflight/live. Episode 연구 OFF와 기존 매매 owner 소비는 별개. |

v7/v4 후보는 해당 계획의 source-date 계약과 기존 publisher/승계 권한을 모두 만족해야 한다. 10/2 장중의 이미 선정된 정책을 문서 현행화로 바꾸지 않는다. 계획의 다음 거래일 적용 목표와 실제 activation/dated receipt를 함께 대사한다.

격리된 `next_preopen_readiness --prepare/--verify`와 실제 당일 활성화/PID 소비를 구분한다. release 변경 시 정식 준비·전체 verify를 다시 수행한다. 07:35 PREOPEN→07:55 Main→Widget 날짜 전환/Episode 예약의 자연 receipt를 확인한다. `postclose_all_active_stages_complete`와 `next_session_policy_ready`는 별도 상태다.

## 6. OFF·퇴역·수동 작업

| owner | 현행 분류 |
| --- | --- |
| common Daily/EV tuning·generic workorder runner, ADM/LDM·bucket/bridge·institutional aggregate | 퇴역. dedicated family와 원천은 유지. |
| `sniper_post_sell_feedback --evaluate-sim`, base scalp sim/candidate-window/AI-budget, scalp-sim tower/prior/overnight | 정규 Main sim chain 퇴역. explicit 과거 replay는 감사용. real post-sell feedback snapshot은 독립 원천. |
| `samsung_machine_entry_tuning`, PYRAMID·AVG_DOWN legacy quality/recovery calibration, opening rotation | 퇴역/고정 OFF. 삼성 Main fixed-watch와 현행 AVG_DOWN shared-rebound owner는 별도. |
| Episode expanded research·공동 allocation | forward-only 미지원 연구 OFF; 유효 Episode OFF에 따른 공동 allocation OFF. 기존 low-price tuning/실매매/applied 정책 유지. |
| Swing discovery/lifecycle/pattern 및 공유 currentness/AI review/propagation | 설치 Swing OFF에 따라 OFF. Main pattern 실험으로 세지 않는다. |
| entry AI gate backtest | `on_demand`, critical chain OFF. 수동 진단은 자연 예약이 아니다. |
| performance workorder·time-window regime·producer-gap source/discovery·stage-hook workorder/scaffold | 기본 OFF. 별도 flag/승인 범위만 허용. |
| `runtime_apply_gap_audit`, `key_lineage_ledger`, `conversion_lane` | 비활성 진단. direct-family 완료 조건이 아니다. |
| `run_ai_entry_setup_paired_replay_postclose.sh` | 수동 호환 wrapper. 추가 설치 owner가 아니다. |

## 7. 현재 결과·남은 수용의 소유자

날짜별 결과는 원 artifact·감사 기록이 소유한다. 과거 분모/EV/선정값과 완료 검토를 현재 OPEN으로 누적하지 않는다.

- [10/2 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 `FinalPolicyStartupAcceptance1002`, `EntryDecisionSourcePreopen1002`, `MainMachineMissedEntryLogicReady1002`, `MainMachineMissedEntryPriority1002`, `CompactAuxiliaryPassVetoLogicReady1002`, `CompactAuxiliaryPassVetoPostclose1002`의 해당 Acceptance를 확인한다. 완료된 과거 수리를 중복 등록하지 않는다.
- 새 계산·샘플 성능: [Main 계획](../proposals/main-machine-missed-entry-priority-postclose-plan-2026-10-01.md), [compact 계획](../proposals/compact-auxiliary-pass-veto-postclose-remediation-plan-2026-10-01.md), [구현·리뷰 기록](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md).
- 의미감시·세대/분모·purge·원천/정상 carry: [감시 연계 계획](../proposals/semantic-monitor-postclose-integration-repair-plan-2026-10-01.md), [구현·배포 기록](../audits/semantic-monitor-postclose-integration-implementation-2026-10-01.md).
- 전일 원천 결손·최종화 실패와 별도의 당일 준비: [10/2 아침 점검](../audits/morning-finalization-dependency-alert-review-2026-10-02.md), [현재 prepared index](../../data/runtime/policy_bootstrap/prepared/2026-10-02/latest.json). 이 근거로 10/1 전체 장후 DONE을 주장하지 않는다.
- 원 코드·historical PREOPEN 소유권을 검증하는 과거 릴리스는 현재 consumer가 참조할 수 있다. 미선택/미기동만으로 불필요한 복사본이라 추정하지 않는다. 보존/복원은 위 감사와 runtime release 계약을 따른다.

각 작업을 `실행 정상성 / 분석 유효성 / 결손·결함 / 달성 가능성 / 직접 소비·다음 조치`로 판정한다. full/partial/no-fill/held/custody, actual/sim/probe/CF, 진단 가격 경로/주 경제성을 구분한다. 결측 비용·손익은 null/source gap이며 valid-empty·무기회·zero EV로 대체하지 않는다. 유입/성숙 근거가 없으면 ETA는 null이다.

<a id="6-다음-상세검토-우선순위"></a>
과거 proposal/checklist의 명시 anchor는 주소 호환용이다. 현재 수용·우선순위는 이 절과 당일 checklist가 소유하며 오래된 Due/PID/완료 상태를 승계하지 않는다.

장후 복구의 독립 machine 그룹은 부모 collector/attribution 완료 뒤 timing/weakness/allocation/approval을 실행하고 Main의 checklist 세대 발행은 모든 producer terminal 뒤 수행하도록 추가 검토했다. compute 슬롯·상한·예약은 유지한다. [10/2 실제 실패와 후속 수리 후보](../audits/postclose-semantic-source-monitoring-2026-10-02.md)의 selector/pin 영수증으로 실제 적용을 판정한다.
