# 의미적 감시기 생산자·소비자 전수 대사 및 현행화 계획 — 2026-10-16

## 1. 결정·범위

현재 선택 릴리스의 생산자 → 원천/영수증 → native 검증 → 실제 소비자 → 알림/복구 → 현행 담당 작업을 기준으로 감시를 현행화한다. 기존 감시기를 확장하며 새 병렬 감시 프레임워크·중복 연구·상시 전량 원문 스캔은 만들지 않는다.

상태: **사용자의 후속 승인에 따라 구현·반복 리뷰·보완·배포·재기동 완료(17:24 KST)**. 계획 작성 당시에는 읽기 전용이었으며, 후속 승인과 실제 실행 결과는 §9 및 아래 §10을 따른다. 기존 [10/10 계획](semantic-monitor-latest-release-followup-repair-plan-2026-10-10.md)의 기준 시점과 미구현 목록을 대체하지만, 원 구현·배포 영수증과 미완료 자연 수용을 삭제하거나 재완료 처리하지 않는다.

기준은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [10/16 체크리스트](../checklists/2026-10-16-stage2-todo-checklist.md), 선택 릴리스의 실제 코드·산출물이다. 기존 baseline의 옛 winrate 초기값/whipsaw 설명을 최신 승인된 누적 정책·Main stop의 원 영수증 위에 덮어쓰지 않는다. baseline/runbook 정정은 별도 명시 요청 대상이며 이번에는 수정하지 않는다.

- `metric_role=source_quality_gate`, `decision_authority=report_only`, `runtime_effect=false` 유지. 감시 추가를 이유로 주문·취소·수량·threshold·provider·봇·lock·계좌 조회 권한을 늘리지 않는다.
- 프로세스 정상, 원천 완전, 비교 완료, 정책 등록/선택, PID 소비, 자연 판정, 제출, broker 수락, 체결/terminal, 비용 후 성과는 서로 다른 판정이다.
- 특정 가능한 결손 row/window는 해당 범위만 격리한다. 결손을 0원·무수익·no-edge로 바꾸지 않으며, 정상 carry나 승인된 최초 등록에 새 경제성 gate를 붙이지 않는다.
- 위젯·에피소드의 실행/수집/UI/연구/장후 발행은 전부 퇴역이다. 과거 episode 잔량은 수동 관리이며 Main 자동 처분·Main 진입 차단의 근거가 아니다. OFF/퇴역 자료 부재를 복구하지 않는다.

## 2. 점검 시점과 증거 수준

### 2.1 전수 대사 기준본 — 아래 §2.3의 후속 전환 이전

| 항목 | 10/16 확인 결과 | 해석 |
| --- | --- | --- |
| 기본 작업공간 | `/home/ubuntu/KORStockScan`, HEAD `c938ace06`, 기존 tracked/untracked 변경 다수 | 이번 작업은 새 제안서만 추가. 기본 작업본이 배포본이라고 가정하지 않음 |
| 선택 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3`, commit `922b9cbc370c4c6c002b3c1fcdb3ed061719e4a2` | 아래 코드 경로는 별도 표시가 없으면 이 릴리스 기준 |
| 실제 Main | PID `3729660`, start ticks `19142841`; `/proc` cwd가 선택 릴리스 `/src`와 일치 | selector 선언만이 아닌 생존 프로세스 대조. 개별 family 자연 소비까지 일괄 증명하지 않음 |
| 배포 transition | 같은 commit의 `data/runtime/release_transitions/2026-10-16/<commit>/status.json`: pass/complete | 새 감시 수리의 배포 증거가 아님 |
| 원천/적용일 | 기존 장후 source `10/15`, 실제 운영 target `10/16`; 다음 운영일 `10/19` | 현재 관측일·원천일·봉인 적용일·다음 예정일을 혼용하지 않음 |
| 작업본 대조 | semantic incident, submission monitor, coverage, notifier, artifact freshness, summary handoff 6개 파일 모두 선택본과 bytes 상이 | 구현은 그때의 선택본을 다시 고정한 격리 작업본에서 시작. dirty 기본 작업본을 일괄 동기화하지 않음 |

이번 조회의 selector SHA256은 `e4175399a341d16a5824baaed335b7ad8147315cdb81e21f13164b1410acd761`, 당일 editable checklist SHA256은 `e959674f9957cc0165cc4b37da0933b9fdbf25306aeb2b4bcf3ec008b9a0c9e1`이다. 이 해시는 조회 시점 식별자이며 과거 strict-bound snapshot의 hash나 미래 배포 기준으로 대용하지 않는다.

### 2.2 자연 산출물에서 확인한 상태

- [정규 detector](../../data/report/error_detection/error_detection_2026-10-16.json) **15:42:55 KST**: detector 7개 중 artifact warning, 나머지 6개 pass. 구조화 incident는 cancel-wait/rising-missed의 `policy_generation_unverified`와 holding의 `source_gap`이며 세 건 모두 현행 OPEN owner로 연결된다. 이는 Telegram 실제 수신 증명은 아니다.
- 같은 결과의 기계 정책은 `cumulative_winrate_selected`, 보조는 `operator_initial_registered`, stop은 `published_policy`, 수량은 `policy_selected`다. `findings=[]`나 발행 성공만으로 source/comparison/PID/economics를 완료 처리하지 않는다.
- [제출병목 감시](../../data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json) **15:40:29 KST**: `execution_status=completed`, `semantic_status=partial`, `observation_health=warning_pending/bounded_no_applicable_observations`. 현재 actor는 위 PID/start ticks. 10분 구간의 fixed-watch 236행은 `SESSION_TRANSITION`의 `session_generation_mismatch` 대기이고 실제 평가 대상은 0이다. 이를 236건 주문 실패·API 결함·전체 정상으로 바꾸지 않는다. top-level blocker는 `missing_stale_or_noncurrent_sentinel_evidence`로 남아 있어 상세 상태와 함께 읽어야 한다.
- 기계 원본 `machine.json`의 `comparison_complete=true`와 감시 projection의 `comparison_complete=false`가 불일치한다. 원본 SHA는 `8bc4c041d63ecb2b365d76718a4d4f6da0be2b110039c20fab3d981f9eec1a5d`; 보조 원본은 false, SHA `a9e6805b9e01355fe8c516707a655c86e075a076ffc9b1e4852aa684cef06097`다. `_continuous_reversal_result_semantics()`가 component 값보다 공동 `handoff.comparison_complete`를 우선하는 코드 경로를 확인했다. 정책 자체가 잘못됐다는 결론은 아니다.
- 장후 handoff 관측은 source10/15의 DONE에 target10/19를 표시하지만 같은 정책 관측의 봉인 target은10/16이다. 예정일 계산과 봉인 적용일을 별도 이름으로 노출해야 한다. 원 source/target 영수증을 재라벨링하지 않는다.

각 산출물은 서로 다른 자연 실행 시점이다. 하나의 원자적 snapshot이나 새 전체 장후 재검증으로 주장하지 않는다. 링크의 `latest`/dated JSON도 후속 실행으로 변할 수 있으므로 구현 시 재고정한다.

### 2.3 작성 중 후속 릴리스 전환과 추가 대사

마지막 확인에서 다른 승인 작업이 **15:45:29**에 `long4-source-retention-20261016-628771e9c` / `628771e9cbb1023cb0b97175000d22e1593b196c`를 선택했다. [해당 transition](../../data/runtime/release_transitions/2026-10-16/628771e9cbb1023cb0b97175000d22e1593b196c/status.json)은 **15:45:35 fail**, `failed_phase=selected`, `deployment_validation_failed:src.engine.automation.intraday_release_handoff`다. selector의 `actual_pid_consumed=false/drained_awaiting_verified_start`, 원 PID3729660의 종료를 직접 확인했다. 따라서 §2.1의 실제 PID와 §2.2의 자연 감시를 이 후속 릴리스의 정상 기동·감시 증거로 사용하지 않는다. 이후 복구 성공 여부는 별도 최신 영수증의 영역이다.

[동시 통합 리뷰](../audits/long4-source-retention-integration-review-2026-10-16.md)와 두 commit의 실제 차이를 추가 대사했다. 공통 coverage/artifact/notifier/incident/stage registry는 같고 submission monitor, policy-generation code handoff, resource detector가 변경됐다. 따라서 §3 등록 수와 SM26-1의 component/joint 표현 결함은 유지되며 아래 변화가 C01/C02/C13/C22/C25에 추가된다.

- 물리5개 슬롯 안의 장기4/단기1 배분, 매도 후 fixed-watch 신원/새 admission 보존; native TRUE/FALSE 역사와 현재 실행 가능 원천을 별도 관측한다.
- local REG→wire→normalized→native의 0B/0D별 exact item/epoch 최초 수신 진단. 최초 체결의 0초 간격은 feature-gap 증거에만 허용하고 no-match/현재 coverage/매매 허가에는 사용하지 않는다.
- holding의 `sealed_partition_vote_inputs`, strict completed/excluded ID, 동일 코드 source-pair 승계; Main 공유 rebound adapter의 별도 원천·권한 경계.
- 닫힌 로그 세대/FD·pin·참조·tmp 용량/증가 감시 및 기존 resource 복구의 좁은 log lane. exit0과 exact run-id/applied/complete terminal이 모두 있어야 성공 cooldown으로 인정한다.

후속 선택본의 변경은 코드/계약 대사이며 배포 실패를 복구하거나 자연 수용했다고 주장하지 않는다. 기존 배포 owner가 원 실패·hold·정책·원 소비 증거를 보존한 정상 복구를 맡는다. 이번 작업은 이를 실행하지 않았다.

## 3. 전수 대사 범위와 기존 수리 처분

전수 범위는 ① 선택 코드의 전체 감시 registry, ② 10/10 기준 이후 변경된 Main/장후/인계 기능, ③ 설치 cron과 별도 연구 소비자, ④ OFF/퇴역 경계다. 파일 이름만 세지 않고 아래 기능별 계약과 마지막 소비자를 연결했다. 대용량 원천 전체 재생·모든 주문의 경제성 재산출은 수행하지 않았다.

### 3.1 등록 범위

선택본의 [coverage](</home/ubuntu/KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3/src/engine/monitoring/error_detector_coverage.py>), [artifact registry/의미 검사](</home/ubuntu/KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3/src/engine/error_detectors/artifact_freshness.py>), [stage registry](</home/ubuntu/KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3/src/engine/automation/postclose_summary_handoff.py>)를 직접 대조했다.

| 집합 | 전체 등록 | 완전성 대사 |
| --- | ---: | --- |
| detector | 7 | artifact freshness, cron, Kiwoom auth, log, process, resource, stale lock. 이 계획은 공통 실행 건강과 기능 의미를 분리 |
| artifact | 39 | pipeline/threshold 2 + recommendations 2 + bootstrap/preopen/postclose 3 + submission/buy funnel 2 + BD 1 + holding 3 + panic/breadth 2 + approval/controller 2 + generic runner/verbosity/source-quality/performance 4 + system metric 1 + Swing/pattern/model 16 + EOD 1 |
| cron | 19 | scanner, preopen, buy funnel, BD, holding, panic, buy pause, snapshot, Swing dry-run, postclose, controller, Swing retrain, tuning storage, EOD, archive, cleanup, finalization, metrics, full detector |
| heartbeat | 5 | main_loop, telegram, error_detection, sniper_engine, scalping_scanner |
| native terminal stage | 7 | main_machine_policy, main_stop_confirmation, pre_submit_delay, legacy_machine_report, main_auxiliary_policy, outcome_labels, summary_handoff |
| incident hook | 10 | legacy_machine_report, main_machine_policy, main_auxiliary_policy, postclose_handoff, entry_cancel_wait_tuning, samsung_frozen_validation, holding_profit_exit, initial_quantity, main_stop_confirmation, policy_generation |
| policy-generation capability | 4 family × 5 step | entry_cancel_wait/rising_missed/auxiliary/holding_vote의 source→comparison→selection→publication→reader |

39/19는 **등록 수**다. 실제 기대 집합은 installed marker·parent flag·거래일·시간창·정상 skip/retirement로 좁힌다. Swing·generic workorder 등록이 있다는 이유로 실행/복원을 요구하지 않는다. `coverage_kind=static_contract_bindings_not_delivery_receipt`의 PASS는 상태별 알림 전달·복구 및 모든 신규 기능의 자연 수용 PASS가 아니다.

추가 대사: 실제 crontab에 `MAIN_MARKET_WEAKNESS_RESEARCH_NIGHT`가 설치되어 있고 별도 wrapper/notifier가 존재한다. 위 19/39와 공통 native hook에는 이 optional 연구의 연결이 없다. 연구 자체의 미구현으로 판단하지 않고 **기존 독립 경로와 공통 coverage 간 연결 대상**으로 등록한다.

### 3.2 10/10 계획의 현재 처분

| 과거 항목 | 선택 릴리스 확인 | 이번 처분 |
| --- | --- | --- |
| F1 청산/수량 알림 | native hook, alert stage, notifier, recovery 연결 존재; holding 실제 source-gap alert 존재 | 재구현하지 않음. 새 lifecycle/partial/outbox 입력 변형 회귀 확대 |
| F2 새 상태 복구 불일치 | 공통 `semantic_incident_contract`에 operator initial/carry/published/valid-empty/pending 상태와 bounded reconciliation 존재 | 현재 문제는 상태 이름 추가보다 동일 incident의 근거·generation·비교 상태를 올바르게 결속하는지 |
| F3 과거 owner | 현재 actionable 3건은 current OPEN으로 해석됨 | 정상 family에 수리 OPEN 부재를 결함 처리하지 않음. 새 actionable reason의 owner 0/중복 회귀 필요 |
| F4 정적 coverage | 등록/callable/상태/owner 검사가 확장되었고 정적 검사임을 명시 | 신규 기능마다 producer-negative fixture→alert→recovery까지 검증하는 계약 행 보완 |
| R1–R5 | source/comparison gap 복구 방지, overdue 관측, bounded state, 현재 owner/date, generation 검증 존재 | 유지·회귀 대상. 모두 미구현이라는 과거 설명 폐기 |
| 제출 지연 selected due | `selected_due_completion_missing`, `selected_due_instrumentation_gap` 구현 확인 | 새로운 동일 검출기를 만들지 않고 intent/terminal/research consumer까지 대사 |
| 대용량 읽기 | entry-split verified projection, Sentinel window/index, invocation digest 공유 구현 | 제한 확대·전량 재해시로 되돌리지 않음. cross-process cache가 구현됐다고 주장하지 않음 |

## 4. 기능별 생산자→마지막 소비자 대사표

경로는 선택 릴리스의 `src/engine/` 기준이다. 표의 보완은 감시/표현/증거 연결 범위이며 전략 생산자의 별도 수리를 자동 승인하지 않는다.

| ID | 기능·생산자와 주 증거 | 현재 소비자/감시 | 현행화·수용 기준 |
| --- | --- | --- | --- |
| C01 | WS/완료봉·exact route: `kiwoom_websocket.py`, `scalping/entry_observation_source.py`; native item/epoch/sequence/lease/수신시각 | machine input→`submission_bottleneck_monitor.source_gap_semantics`; WS freshness | 재시작 epoch, 예약 충돌, 공급 지연과 입력 소비 지연 구분. 후속628의 local REG/wire/normalized/native 진단은 ACK·과거 수신 증명이 아님. 0초 feature-gap을 no-match로 승격 금지 |
| C02 | 고정감시/Scanner/nonfixed handoff: `kiwoom_sniper_v2.py`, `sniper_state_handlers.py`; promotion·등록·admission receipt | probe/source-window→현재 actor cohort→machine | 세 모집단·pending/feature gap/등록 누락의 분모 보존. 후속 장기4/단기1·재감시 admission·history-only 관측을 현재 source coverage와 구별. warmup·세션 전환 무평가를 ENTER_NOW 부재 장애로 합치지 않음 |
| C03 | 누적 기계 catalog/등록/비교: `scalping/reversal_cumulative_{catalog,registration,postclose,runtime}.py`, policy v6 | current bundle→loader/PID/decision→machine semantic | 원 component 비교 완료, 공동 비교, 지정 최초 채택, 자동 비교 선택을 분리. 등록 전체/선택 scope/관측 scope 분모 보존 |
| C04 | 보조 AI: `scalping/reversal_auxiliary_tuning.py`, `scalping/ai_decision_quality.py`; trace·label·exact plan/owner/cost | paired comparison→auxiliary component→native handoff/alert | transport 성공≠정확 라벨≠경제 비교. entry_screen/entry 경로·동일 시도 결속, 정상 호환 carry·request0와 source_gap을 구분. 원 보조 입력/응답/모집단 불변 |
| C05 | PASS 비동기 전달·claim/consume: `sniper_state_handlers.py`, monitoring attempt identity; deadline/generation | async disposition coverage→Main consume→submit | PASS→consume→submit-call→broker accepted→fill을 별도 계수. 무소비/기한 만료/반환 false를 체결 실패로 오표현하지 않음. 불필요한 submit-drought 세분류 추가 금지 |
| C06 | pre-submit delay: runtime intent/quote/terminal, `automation/pre_submit_delay_source_ledger.py` | incremental delay semantic→partitioned research→dated policy | 선택 due와 CF horizon 구분. 원 commit 시각·selected delay·route·취소/terminal 귀속. 정상 terminal 후 미관측 horizon을 재제출 실패로 보지 않음 |
| C07 | entry 가격 진행/상황 연구: `scalping/reversal_cumulative_{catalog,runtime,registration,postclose}.py`, `scalping/reversal_extended_state.py`; 버전별 resource·source manifest | 고정 대안/상황 진단→등록 batch→v6 reader/장후 비교 | delay 연구와 별도 소유권. 준비된 catalog·parity와 활성 정책/PID를 분리. 구/신 batch·UNKNOWN/OR·quote 연속성·원 확인점 membership 보존 |
| C08 | 분할진입/초기수량: `scalping/entry_split_order_plan.py`, initial_quantity 모듈 | `entry_split_monitor_projection.py`→entry-execution semantic; qty native→alert | 원 plan·계좌 capacity·reservation·leg·terminal/cost 결속. cached 관측 결손과 주문 직전 검증 분리; 큰 report 대신 검증된 manifest 사용 |
| C09 | partial fill/잔여·cancel-wait: `sniper_execution_receipts.py`, `scalping/entry_cancel_wait_runtime.py` | pending journal/custody checkpoint→cancel-wait tuning→policy | 목표9/체결1 같은 부분체결도 잔여 terminal 확인 전 pending 유지. CANCEL_PENDING/unknown/late fill은 정상 flat/전량 완료로 바꾸지 않음 |
| C10 | Main/manual/퇴역 custody: `scalping/main_custody_checkpoint.py`, `src/trading/config/owner_retirement.py` | submit/holding/exit 및 native replay | 역사 owner 유지·manual veto 존중. 퇴역 잔량/intent를 Main 차단이나 자동 exit로 연결하지 않음 |
| C11 | trailing/TP 첫 crossing: `scalping/trailing_mechanical_strength.py`, `holding_exit_observation_report.py` | `holding_exit_sentinel.py`→`holding_profit_exit_semantics.py`→artifact/notifier | sampled-grid exhaustion과 실제 runtime source failure 분리. 원 BUY generation/TP signal/position별 과거 결손 보존; 새 발생만 재발로 식별 |
| C12 | SELL outbox/overnight terminal: `sniper_execution_receipts.py` | native ACK→journal/position fact→holding semantic/장후 | broker_position_sell receipt와 기존 scanner lineage 모두 검증. ACK≠추가 SELL≠비용 검증. 단지 PARTIAL이라는 로그명으로 부분체결 판정 금지 |
| C13 | Main stop/holding vote: `automation/main_stop_postclose.py`, `ai/holding_exit_vote.py`, `scalping/main_stop_policy.py` | committed policy→dated reader/pinned position→PID→native stop semantic | 구 손절 퇴역과 남은 hard safety 구분. source-gap carry, numeric not-armed, valid ancestor pin 및 source-pair code handoff를 감시. 신규 장중 tail이 과거 봉인 입력을 오염시키는지 검증 |
| C14 | 실제 비용/position fact: `lifecycle/broker_cost_reconciliation.py`, execution receipts | completed facts→quantity/holding/stop/paired economics | 주문별 수량·체결·수수료/세금/비용 배분. cost-unallocated/unknown은 null. `COMPLETED`만으로 유효 net PnL 승격 금지 |
| C15 | 장후 raw quality/label/replay: source-quality audit, `ai_decision_quality.py`, legacy calibration | family exclusion→legacy/outcome terminal→auxiliary | mature/partial/pending label과 source contract를 별도 표시. 시간이 지나도 없는 plan/가격 reference는 자동 회복하지 않음. legacy 결손을 승인된 새 기계 채택의 추가 gate로 전용하지 않음 |
| C16 | trailing 전체 모집단/상황 연구: `automation/main_trailing_{source_assembler,partitioned_research,population_aggregation,situation_aggregation}.py` | native manifest→holding vote/next policy→summary | 연구 완료·raw census 완전·경제 eligible/common을 분리. scope 개수/partition 완료를 경제 수용 개수로 세지 않음 |
| C17 | rising-missed/cancel-wait/aux/holding code capability: `monitoring/policy_generation_*` | fixture/source-pair→artifact→current owner | 4 family의 5 step 검증과 실제 source/comparison 결과 별도. 원 code pin 보존; exact reviewed source-pair 외 자동 수용 금지 |
| C18 | optional Main 약세 연구: `automation/main_market_weakness_research.py`/notify, 전용 wrapper | calendar→source_scope/cursor→daily/cumulative→추천 outbox | 최신 attempt와 마지막 계산 구분. 미시작 날짜도 pending, native 입력 행/projection 행/연결 건수 구분. 기존 추천/정정/철회 notifier를 재사용하고 공통 전달과 중복 금지 |
| C19 | policy publication/intake: `automation/operator_policy_succession.py`, `postclose_recommendation_intake.py` | native registration/parent CAS→current/dates→bootstrap | 후보·등록안·선택·승계·PID consumption 단계별 실제 hash. operator 지정 채택에 별도 EV gate 신설 금지 |
| C20 | stage/strict/controller: `automation/postclose_summary_handoff.py`, `verify_threshold_cycle_postclose_chain.py`, controller | 7 stage receipt→summary/checklist→strict→DONE | 7 stage success와 family source gap 동시 보존. summary component 상태 오표현 수리, 원 실행/실패/재개 ancestry 유지 |
| C21 | finalization/preopen/배포: native finalization, `next_preopen_readiness.py`, `intraday_release_handoff.py` | committed generation→prepared→PREOPEN→launcher/PID→current-policy receipt | 이전 성공·future prepared를 현재 PID 수용으로 사용 금지. publication 중간 세대·drain/startup pending은 제한 대기, deadline 경과 후 별도 결손 |
| C22 | I/O·자료 수명: `lifecycle/research_storage.py`, digest sessions, source-window/compact stores | bounded readers→resource/semantic observation health→finalization | gzip/plain 논리 원천·CRC/EOF·late file·동일 크기 교체/append·code/date/PID 변경 검사. budget exhausted는 미관측이며 empty/pass 아님 |
| C23 | 알림/복구 자체: `monitoring/semantic_incident_contract.py`, `notify_error_detection_admin.py`, submission notify | alert candidate→transport receipt→state→reconcile→current OPEN | 중복억제/재전송/복구/과거미복구/새재발 별도. alert 생성과 전달 성공 별도; reporter hash 변경만으로 동일 역사 결손 재알림 금지 |
| C24 | 퇴역/OFF·독립 건강 | retirement config, installed schedules, heartbeat/artifact/cron registry | expected-set 결정→coverage→운영자 | widget/episode/독립 AVG_DOWN·PYRAMID/구 panic/Swing OFF/generic 작업의 부재 비기대. 실제 잘못 설치/소비된 퇴역 경로만 권한 누출로 보고 |
| C25 | 후속628 Main 공유 rebound/보유 분류: `scalping/avg_down_rebound.py`, fixed admission·native snapshot·선택 union | `sniper_state_handlers.py`의 기존 Main 보유/추가매수 경로, holding vote/replay | 독립 퇴역 AVG_DOWN producer와 구별. adapter는 entry claim/order owner가 아니며 continuation-only branch로 ADD 권한을 만들지 않음. 당시 fixed custody/현재 venue·freshness·signal expiry·source hash와 실제 action 결과를 분리 |

### 4.1 장후 전체 논리 작업의 누락 방지 대사

[10/16 장후 의미 점검의 35개 논리 작업](../audits/main-postclose-semantic-review-and-repeated-read-findings-2026-10-16.md)을 아래와 같이 모두 연결했다. 그 감사의 06시대 수치·당시 미구현 설명을 현재 사실로 복사하지 않았다. 이후 [읽기 감축/배포 기록](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md), [약세 연구 보완](../audits/main-market-weakness-source-completeness-and-status-review-2026-10-16.md), 현재 선택 코드를 함께 대조했다.

| 원 점검 번호 / 논리 작업 | 현재 감시 owner/최종 소비 | 본 계획 |
| --- | --- | --- |
| 1 EOD, 2 archive | cron/content native status→EOD 선행 gate→장후/cleanup | C22/C24; 영수증 success와 종목별 결손 분리 |
| 3 source-quality, 4 rising feedback, 5 breadth | raw exclusion→family/진입 문맥; 보고 전용 | C02/C15/C17 |
| 6 broker cost, 7 position fact, 8 scale-in skip | 비용/terminal→해당 family; 퇴역 producer 부활 금지 | C10/C14/C24 |
| 9 entry split, 10 cancel-wait, 11 qty refresh | policy generation→bootstrap/loader→runtime receipt | C08/C09/C17/C19 |
| 12 verbosity, 13 WS freshness, 14 lookup attention | identity parity/원천→Main 입력·source quality | C01/C02/C22; 자료 절감 예상치≠실현 절감 |
| 15 rising prior, 16 exit/trade-review, 17 post-sell, 18 missed-entry CF | native source manifest→family 연구; actual/CF 분리 | C14/C15/C16/C17 |
| 19 holding population, 20 mechanical trailing, 21 all-scope trailing, 22 holding path vote, 23 stop | population→연구→carry/선정→dated pin/실제 holding | C11/C13/C16 |
| 24 cumulative machine, 25 compact auxiliary, 26 legacy full, 27 outcome labels, 28 microstructure CF | 각각 native component/label/diagnostic consumer→handoff | C03/C04/C15; legacy/CF가 실제 정책 gate를 대신하지 않음 |
| 29 tuning storage parity, 30 approval/checklist, 31 strict/controller | 원 event/window 보존→summary→sealed generation | C20/C22 |
| 32 cleanup, 33 finalization/detector, 34 prepared | terminal ancestry→다음 PREOPEN→실제 PID | C21/C22/C23 |
| 35 optional weakness | 독립 calendar/cursor/cumulative/notify; strict/PREOPEN 비차단 | C18; 날짜 완전성/초기 보류 보고 보완 코드는 선택본에 존재, 자연 야간 수용 별도 |

## 5. 보완 항목과 우선순위

확인된 결함과 아직 재현하지 않은 회귀 위험을 구분한다. 아래 SM26 ID는 **계획 내부 절 식별자**이며 새 체크리스트 OPEN/실행 승인으로 사용하지 않는다.

### SM26-0 — 구현 기준·범위 재고정

선택 commit/release·PID/start ticks·selector·policy bundle·source/target·code generation·현재 owner를 다시 고정한다. 변경 집합을 C01–C25에 매핑하고 registry/설치 schedule 차집합을 작성한다. 특히 §2.3의 실패 전환 뒤 selector가 다시 바뀌거나 새 PID가 기동하면 원3729660 증거를 대용하지 않는다. 새 기능은 producer/output/validator/최종 consumer/expectedness/owner/test 중 빈 칸이 없도록 하되 기존 registry와 native receipt를 단일 권위로 사용한다. 새 `.py`/producer가 필요하면 먼저 위치 gate와 중복 제거 이유를 검토한다.

### SM26-1 — 비교 상태·날짜·증거 단계 표현 수리 (P0, 확인된 결함)

1. `reversal_policy_status.report_state`, artifact의 component projection, native handoff 및 요약 consumer를 함께 대조한다. **machine comparison / auxiliary comparison / joint handoff comparison**를 각각 보존한다. 현재 machine true/aux false/joint false를 재현 fixture로 고정한다.
2. top-level 등록/선택·component의 `adoption_basis`·carry 근거를 구분한다. 기존 문자열 매핑에 없는 승인된 adoption basis를 임의 `comparison_selected`로 추정하지 않는다. 원 보고서/정책을 다시 쓰지 않고 감시 projection부터 고친다. 봉인 summary를 고쳐야 하면 기존 handoff owner의 정상 successor 발행으로만 진행한다.
3. `observation_date`, `source_date`, `bound_target_date`, `next_due_target_date`를 명확히 구별한다. 기존 필드 의미 변경은 모든 reader/notifier/fingerprint 이행과 함께 검증한다. 금요일10/16→월요일10/19, 자정, 과거 source 재검사 fixture 포함.
4. 판정 차원을 분리한다: 실행 상태 / 관측 완전성 / 원천 품질 / 비교 / 발행·소비 / lifecycle / economics. 현재 partial/no-applicable을 성공으로 승격하지 않는다. 장후 scheduled-before-due·정상 carry·실제 source gap을 각각 설명한다.

종결: 원 component 값·hash/date와 projection이 일치하고 같은 fixture에서 machine/aux/joint를 서로 바꿀 수 없으며, 보고 수리가 기존 정책 승인·거래 권한을 변경하지 않는다.

### SM26-2 — 장중 원천·제출·수량·보유 변경을 상태별로 연결 (P1)

- C01–C14의 현재 함수/영수증을 재사용한다. 새 경보 추가 전 기존 source-gap/async/delay/holding 의미 결과에 이미 포함되는지 확인한다. 같은 root incident의 중복 감시를 만들지 않는다.
- 기대 기회/관측 범위가 입증되지 않으면 `unknown/unobservable`; exact complete window에서 적용 대상0이면 별도의 정상 비대상 설명. 세션 전환·정상 pending·본래 no-match를 원천 복구 명령으로 연결하지 않는다. 전환 상태가 native 기한을 넘었는지는 별도 확인한다.
- 일부 체결/SELL outbox/과거 TP 결손은 position·BUY generation·leg·signal 단위로 확인한다. source-gap5 같은 과거 이력의 개수만으로 지금 재발을 판정하지 않는다. 기존 `holding_gap_identity`의 exact gap-set 검증/이행을 유지하고 불완전 목록에는 확장 적용하지 않는다.
- 자금 관측 cache hit/miss, 기계 비진입, 주문 직전 capacity 검증은 분리한다. 감시에서 동기 계좌 재조회·임계치 완화·과거 평가 소급을 실행하지 않는다.

종결: 같은 exact attempt가 source→decision→aux→consume→submit-call→broker→terminal까지 어디에서 끝났는지 보존한다. 평가가 없는 구간의 빈 issues는 거래 건강/전체 coverage PASS가 아니다. 경제성은 terminal+유효 비용 자료가 있어야 별도 평가한다.

### SM26-3 — 장후 family·capability·optional 연구 연결 (P1)

- C15–C20 및 35개 논리 계약에서 `stage_succeeded`와 분석 의미를 동시에 전달한다. native source-gap/비교 미완료/실제 eligible0를 숨기지 않고 valid-empty/insufficient/carry와 구별한다.
- 현재 두 `policy_generation_unverified`는 현행 owner의 기존 보고서 generation, fixture receipt, reviewed source-pair, 실제 reader code를 대조하여 원인을 좁힌다. 무조건 fixture 재실행·pin 교체·warning 제거를 완료 기준으로 삼지 않는다. fixture 검증도 실제 모집단/정책 우월성 증거는 아니다.
- optional 약세 연구는 native installed calendar·enabled/notify·검증된 시간창·EOD/admission/budget·latest attempt·last computed source·source_scope/pending/invalidated dates·cumulative currentness·outbox disposition을 읽기 전용으로 연결한다. `regular_postclose_or_eod_active` 같은 정상 보류와 장기 미진전을 구별하되 새 임의 deadline을 만들지 않는다.
- 추천 메시지는 기존 전용 notifier가 소유하고 공통 감시기는 실행/원천 건강만 담당한다. 두 notifier의 incident identity/전달 책임을 명시한다. optional source gap을 Main strict/PREOPEN 전역 차단으로 승격하지 않는다.

종결: 단계 exit0이면서 source-gap인 fixture가 경제성 성공으로 표시되지 않는다. 설치된 optional 기능도 누락 없이 정상 보류/기한 초과/원천 결손/미전달을 구분하고, 공급자 호출·실제 알림 없이 검증한다.

### SM26-4 — 인계 generation·효율·자기 감시 (P1)

- C21/C22의 이미 구현된 invocation digest 재사용·bounded projection을 유지한다. full semantic validation을 digest-only로 바꾸지 않는다. 감시 프로세스가 큰 report를 반복 읽지 않도록 producer가 검증한 immutable projection/manifest를 소비하며, 없는 projection은 해당 producer owner의 변경으로 계획한다.
- single-file atomic replace와 summary→checklist→strict→controller→prepared의 전체 세대 완성은 다르다. 현행 committed/successor 계약을 확인하고 혼합 세대/부분 게시/timeout 시 native validator가 거부하거나 미관측으로 유지하는지 회귀한다. 전체 게시 방식 수리는 별도 I/O/인계 owner가 맡으며 이 계획이 그 수리를 완료했다고 표시하지 않는다.
- 원 child rc/signal/phase가 없는 중단은 unknown이다. 감시기에서 시간 경과만으로 exit124를 합성하지 않는다. 기존 예산과 cutoff를 보존한다.
- reader 오류/size limit/CRC/EOF/경합/lock busy/budget exhaustion은 빈 입력이 아니다. 읽기 bytes, 원천 종류, validation mode, currentness, 실행 wall time을 함께 표시한다. cold/warm·동일 프로세스/별도 프로세스 계측을 구분하고 kernel I/O와 requested bytes를 합산하지 않는다.
- 후속628의 로그 복구는 기존 resource detector가 가진 별도 운영 권한이다. 이 의미적 감시 계획이 삭제/회전/압축 권한을 추가하지 않는다. producer의 닫힌 세대 등록→보호 FD/pin/참조 검사→정확 terminal→cooldown 및 tmp census freshness를 대사하고, 없는/오래된 census를 capacity 정상으로 추정하지 않는다. 신규06:17 일정은 실제 installer 적용 영수증과 설치 cron을 별도로 확인한다.
- 실패 배포는 원 transition/phase와 최신 selector·hold·살아 있는 actor를 연결한다. 정책 code-handoff 준비 누락은 drain 전 preflight에서 확인할 수 있는지 기존 배포 owner에 인계한다. 과거 native parity·원 PID 보존은 새 실행 완료를 뜻하지 않는다.

종결: append/truncate/같은 크기 교체/late partition/gzip 전환/code·date·PID 변경을 잡고, bounded reader로 기존 native 결과와 parity를 유지한다. 동일 source의 반복 감시 때문에 과거 반복 I/O를 재도입하지 않는다.

### SM26-5 — 전달·복구·현재 owner와 coverage 폐쇄 (P1)

- 기존 incident 계약에 맞춰 `active`, `notification_pending`, 실제 전달, 검증된 복구, `historical_unrecovered`, `superseded`, `unobservable`을 별도 유지한다. 저장 경로가 사라지거나 window 밖으로 나갔다는 사실은 복구 증거가 아니다.
- 전송 실패 뒤 sent/cooldown으로 성공 처리하지 않는다. state 이행은 원 fingerprint/원 전달 증거를 보존한다. owner 변경이나 보고서 재발행만으로 같은 결손을 신규 경보로 만들지 않는다. 반대로 새 position/source/attempt의 재발은 숨기지 않는다.
- production owner와 actionable repair owner를 분리한다. 현재 KST checklist에서 유일한 OPEN 및 명시 transfer만 인정한다. 정상 family에 수리 OPEN이 없다는 이유로 실패시키지 않는다.
- `validate_semantic_coverage`에 새 실행 job을 강제로 등록하기보다 기존 registry와 기능 계약 행의 연결·OFF 사유·전용 notifier 소유권을 대사한다. 정적 coverage와 동작 fixture 결과는 별도 산출한다. 실 Telegram 전달은 승인된 자연 증거가 생겼을 때만 완료로 주장한다.

종결: 각 active 계약 행에서 fault injection→구조화 incident→현재 owner→가짜 transport 실패/재시도→같은 세대 native recovery가 검증되고, retired/OFF/정상 비대상에는 복구 작업이 생성되지 않는다.

## 6. 소유권·실행 순서

| 책임 | 기존 현재 owner / 인계 조건 |
| --- | --- |
| 기계/보조/summary/날짜·bootstrap | `DirectFamilyPreopenPolicyHandoff`, 보조 원천은 `DirectFamilySourceRepairCompactAuxiliary` |
| cancel-wait / split | `DirectFamilySourceRepairEntryCancelWait` / `DirectFamilySourceRepairEntrySplit` |
| rising / stop·holding capability | `PostcloseStructuralPolicyCompletion1011` / `MainStopLossRetirementRuntimeTuning1010` |
| holding·terminal·비용 | `HoldingProfitExitSourceContractRepair` |
| optional 약세 자연 수용 | `MainMarketWeaknessPostcloseObservation1008` |
| 누적 등록 배포 자연 수용 | `CumulativePolicyAdoptionDeployment1015` |
| native 원천/비동기 보조 전달 | `NonfixedDispatchReadinessReview1012` / `AuxiliaryCircuitRecoveryRepair1012` |
| 운영 로그 보존 | 동시 작업으로 추가된 `OperationalLogRetentionRepair1016`; C22의 수명/보호 자료 계약은 이 owner의 변경과 대사 |
| 공통 감시 구현 | 과거 `SemanticMonitorLatestReleaseRepair1010`은 당일 OPEN이 아님. 구현 승인 시 기존 ID의 명시 승계 또는 새 유일 owner를 정상 checklist 인계 경로로 등록 |

위 표는 이번에 새로운 권한을 부여하지 않는다. 기존 family owner에 감시 수리와 생산자 원천 복구를 혼합해 완료 표시하지 않는다. 당일 봉인 checklist/summary/prepared는 수정하지 않았다. 실행 owner 등록이 봉인 인계에 영향을 주면 원 bytes를 보존하고 기존 handoff 절차의 successor로 발행한다. 과거 `[x]`/문서 링크만으로 실행 owner를 대체하지 않는다.

순서: **SM26-0 → SM26-1 → SM26-2/3의 독립 변경 → SM26-4/5 공통 회귀 → 배포 후보 검증**. 각 변경은 구현→self review→보완→재리뷰→표적 검증을 통과해야 한다. 구조 수리 완료, 배포, 자연 관측, 비용 후 경제성은 각각 별도 종료 기준이다.

## 7. 검증·배포 수용 계획

### 7.1 구현 시 기존 시험 확장

새 대형 시험 체계를 만들지 않고 선택본의 기존 `test_error_detector_artifact_freshness.py`, `test_notify_error_detection_admin.py`, `test_error_detector_coverage.py`, `test_next_session_semantic_coverage.py`, `test_submission_bottleneck_monitor.py`, `test_postclose_policy_generation_contract.py`, `test_postclose_summary_handoff.py`, `test_postclose_finalization_generation.py`, `test_holding_exit_sentinel.py`, `test_initial_quantity_producer_consumer_repair.py`, `test_reversal_price_progress.py`, `test_main_market_weakness_research_automation.py`와 notify 시험에 해당 fixture를 추가한다.

필수 행렬:

1. machine true/aux false/joint false, operator initial/cumulative selected/carry/source-gap의 독립 표현; 기존 승인 권한 불변.
2. source10/15→target10/16와 next-due10/19, 자정·휴일·future-due·기한 초과·과거 snapshot/현행 PID 구분.
3. current actor 변경, fixed/scanner/nonfixed·정상 세션 대기·native feature gap·정확 경로 불일치·부분 window.
4. PASS 미소비·submit returned-false·broker accepted 미확인·부분체결/취소미정·SELL ACK/비용미상; leg/owner 오결속 거부.
5. holdings의 동일 역사 gap-set과 새 gap-set, report hash만 변경, source completeness false, 비교미완료/빈 findings, valid ancestor pin.
6. code capability verified지만 실제 source-gap, old receipt/new code mismatch, 정확 source-pair 이외 거부.
7. optional 정상 보류/미시작 날짜/pending/invalidated/currentness/알림 권한 OFF/전송 실패; 공통·전용 notifier 중복0.
8. bounded projection 누락/변조, raw/compact 불일치, gzip/plain alias·CRC/EOF, generation 중간 변경·예산 소진·부분 게시.
9. state overflow/손상/마이그레이션·알림 재시도·원 전달 보존·current owner 0/중복; 퇴역 producer 소비 시도 탐지.

네트워크/주문/provider/실 Telegram은 차단한 fixture로 검증한다. 변경된 Python compile, shell 변경 시 `bash -n`, 영향 계약 pytest, 문서 parser, `git diff --check`를 실행한다. native 검증/보고서 재생성은 코드 검증과 별도 권한·비용 범위로 다룬다.

### 7.2 승인된 후속 배포에서만 확인할 것

배포 직전 선택본이 달라지면 SM26-0과 영향 계약을 다시 대사한다. 원 policy/report/code pin·기존 성공과 실패 attempt·OPEN custody를 보존하며 bootstrap/strict/code capability의 현행 successor 요구를 만족시킨다. 단순 감시 코드 배포도 sealed code 계약에 걸리면 기존 인계 owner가 처리한다. 무조건 전체 봇 재기동하거나 전체 장후를 재실행하지 않는다.

완료 판정은 다음을 별도 기록한다: (a) 코드/fixture, (b) 선택 릴리스와 실제 감시 실행본, (c) 다음 적용 가능한 자연 장중 구간, (d) exact-date 장후 terminal→prepared, (e) 다음 운영일 실제 PID 소비, (f) 알림 전달·복구가 실제 발생한 경우 그 영수증. 자연 사건이 없으면 해당 항목은 미관측이며 테스트 PASS로 채우지 않는다. 현재 계획의 수용을 위해 실제 주문/알림/경제 이익을 강제로 발생시키지 않는다.

## 8. 이번 문서 작업의 검증과 한계

이번 계획은 selected registry와 변경된 producer/consumer, 현재 작은 산출물, 설치 cron, 실제 PID, 직접 관련 감사 기록을 대조했다. 기존 skill의 review gate에 따라 이미 구현된 수리를 다시 OPEN하지 않고, component-vs-joint 표현 결함·날짜 의미·optional coverage와 나머지 회귀 위험을 구분했다.

문서 링크/선택본 경로·25개 고유 계약 ID·35개 장후 논리 작업 매핑·registry 합계·owner·권한 경계를 재리뷰하고 print-only parser 및 whitespace 검사를 수행했다. 재리뷰에서 entry 가격 진행 연구를 delay 연구와 잘못 묶은 경로를 누적 catalog/runtime/registration/postclose로 바로잡았다. 마지막 선택 변경을 발견해 후속628 차이를 추가하고, 원 PID가 현재 정상이라는 설명이 남지 않도록 기준 시점을 분리했다. print-only parser는 전체28항목, 당일 OPEN12개·stable ID 중복0을 확인했다. Python/운영 코드를 바꾸지 않아 trading pytest·대용량 보고 재생성·provider/API·외부 Project/Calendar 동기화·Telegram·배포·재기동은 수행하지 않았다.

당일 checklist는 이 작업에서 편집하지 않았다. 작성 도중 다른 작업의 운영 로그 보존 owner 추가로 SHA가 `d5624eaa16680f3233e402b616445344e6f4c792f29db03d154bf37a1102293f`로 바뀐 것을 확인했다. 원 조회 hash와 구분해 기록하고 동시 변경을 되돌리지 않았다. 계획만 새로 추가했으며 기존 dirty 파일·봉인 산출물은 건드리지 않았다.

남은 한계는 실제 구현·자연 장후/장전 소비·전달/복구와 경제성 수용이다. 이번 전수 대사는 계약 범위의 누락을 찾는 작업이지 모든 과거 raw/event를 새로 replay하거나 source-gap을 복구한 결과가 아니다.


## 9. 승인된 구현·배포 실행 인계

2026-10-16 사용자는 상황·해시 계약, 세 생산/조회 경로, 0초 정책 보존, 의미감시, 과거 projection, 영향 범위 장후 재계산의 구현·반복 리뷰·배포·재기동을 승인했다. 이 승인으로 §1의 문서 작성 당시 비실행 범위를 갱신한다. 주문/공급자 직접 호출과 임계치 완화 권한은 추가하지 않는다.

실행 기준은 실제 선택 `6c97e83f1`이며 현재 OPEN `PreSubmitSemanticCurrentization1016`이 코드·감시·배포 closure를 맡는다. 기존 family의 자연 자료·경제성 owner는 유지한다. [구현 리뷰](../audits/pre-submit-semantic-implementation-review-2026-10-16.md)에서 실제 시험·재계산·PID 소비 결과를 구분한다.

운영 소비 계약: v4 commit은 native matched branch/definition refs/상황/선택 지연을 해시에 묶는다. 기존 v2/v3 원 bytes와 digest는 보존한다. producer manifest의 최근20분 요약은 기존 append 세대에 결속하며 감시기는 최대2MiB manifest와 bounded raw/compact를 읽는다. 구 manifest는 기존 native 검증으로 읽고 writer의 다음 flush에서 이관한다. 구 cursor는 관측 범위를 다시 확보하며 과거 incident를 복구 완료로 만들지 않는다. signal_ready의0/30/60/120/180초 관측 완료는 주문 terminal을 요구하지 않는다.

`observation_date/source_date/bound_target_date/next_due_target_date`를 분리하고 기존 notifier/fingerprint의 `target_date`는 호환 필드로 보존한다. optional 연구는 native 설치 calendar/권한/최근 attempt/last-completed/cursor/source scope를 읽으며 추천 전송은 기존 전용 notifier가 소유한다. 정적 C01–C25 연결은 실제 주문·경제성·Telegram 전달 증명이 아니다.


## 10. 승인 후 실행 결과 — 17:25 KST

최종 코드45fa0470e/Main PID167546의 ordered 전이·정책 소비와 새 writer 원천 감시를 확인했다. raw/summary/compact complete, 현재창 결손0, flush error0이며 현재0초 정책을 유지한다. 원67건은 사용자 제공 이력으로 보존하고 과거 stale 호가나 terminal 부재를 복구 완료로 처리하지 않았다. 해당 구간 신규 delay event0이므로 v4 후행 관측의 자연 수용은 대기한다.

기계/보조/joint 비교는 true/false/false, 봉인 적용일10/16와 다음 예정일10/19를 분리했다. 과거 장후 취소대기·상승누락의 exact 세대 인계 누락도 보완했으며 실제 조회에서 current capability verified를 확인했다. native source/comparison/정책 유지 상태는 보존한다. C01–C25 정적 연결 PASS와 실제 전체 감시의 holding/source/scanner/tmp 잔여 경고는 별도 결과다.

과거 native capture와 exact join한238개 anchor로 상황 UNKNOWN267→29, cell97→195를 얻었다. source10/15의 영향 family만 격리 재계산하고 최종 코드로 검증했으며, 초기 정책은0초다. 현재10/16 canonical 정책을 대체하지 않았고 오늘 정규 장후 및10/19 실제 소비는 기존 OPEN owner로 유지한다. 상세 시험·성능·실제 receipt와 잔여 수용은 [구현 리뷰](../audits/pre-submit-semantic-implementation-review-2026-10-16.md#최종-배포실제-소비-및-잔여-자연-수용)를 따른다.

## 11. 비상시 원천 인계·제어응답 후속 수리

18:35 상세 점검에 따른 구현·리뷰·보완·배포·재기동 승인을 접수했다. 원천 인계와 Main 준비 조건을 함께 수리하고, 원 신호/5초·실제 수신시각을 보존한다. 제어응답은 local 송신과 분리하며 불명 귀속을 정상 ACK로 세지 않는다. 미배포 unsigned first-trade feature-gap 관측 수리도 통합한다. [구현 리뷰](../audits/nonfixed-source-continuity-review-2026-10-16.md)의 코드 검증과 actual PID/자연 수용을 분리하며 현재 owner는 `NonfixedDispatchReadinessReview1012`를 유지한다.

## 12. raw cursor 경계와 누적 보조연구 통합

후속 사용자는 raw117/summary118의 cursor 결함 보완과 `7d62534e3`의 누적 보조연구를 함께 코드리뷰·수정·배포·재기동하도록 승인했다. v3 cursor는 as-of 이후 읽힌 event의 최소 projection을 보존하고 현재 intent 분석에서 제외한다. v2의 결손 가능 상태는 bounded 관측 경계로 이행하며 과거 원천 복구를 주장하지 않는다. 실제118행의 incremental/fresh count·hash parity 및 영향 회귀를 검증한다.

보조연구의 전면 교체 비권고와800회 누적 사용량을 유지한다. 같은 seed와 actual 요청/응답을 재사용해 native 인계를 확인하고 주성 AFTER/SOR·10만원 이상, 기타 비삼성 PRE/NXT·2만~10만원의 두 개선 scope만 기존 CAS publisher로 적용한다. 새 연구 호출은 없다. cursor 코드 owner는 `PreSubmitSemanticCurrentization1016`, 보조정책 owner는 `DirectFamilySourceRepairCompactAuxiliary`, 실제 종목 수신 결손은 `NonfixedDispatchReadinessReview1012`를 유지한다.

003540·417860의 local 송신·연결 success·귀속 unknown·실제 wire0은 분리한다. 기존 bounded probe/회전을 유지하고 새 exact source가 생기기 전 정상화하지 않는다. [통합 리뷰](../audits/main-source-cursor-and-auxiliary-integration-review-2026-10-16.md)의 정지 전 정책 인계·native parity·delay/stop/holding gate 후 정규 전환, 새 PID/observer/full detector와 보조 binding 소비를 각각 확인한다.

## 13. EOD 이후 원천 세대·원장 경로 보완

source10/16의 EOD는20:56:06에 완료됐다. 수집2,622/2,626, DB 최신일10/16·2,622행과 원 경고4종목을 보존한다. 정규 장후 원 run은082096071이며 진행 중 코드·입력을 교체하지 않는다.

상승누락 보고서는 원천 감사 preflight의 격리 완료 뒤 생성한다. 감사가 결함 행을 제거한 경우 격리 이전 보고서의 source hash/count를 현재 입력으로 승계하지 않는다. 정상·복구 모드의 기존 검증된 preflight 재사용과 live reader 보호, 자원·EOD gate는 유지한다. 관리 릴리스의 종목원장 조회는 공용 DATA_DIR의 검증된 mount를 사용하고, 하위 링크·plain/gzip 충돌·손상된 최신 세대는 기존 strict reader가 계속 거부한다. 퇴역 collector나 정책 발행기를 복원하지 않는다.

기존 원본·실패·원천 격리 영수증을 보존한 뒤 영향 producer와 직접 소비자만 재생성하고 tower/checklist/strict/controller·10/19 준비로 닫는다. 현재 기계정책·비용·custody·runtime env·provider·주문·수량·hard safety는 바꾸지 않는다. 실제 완료 영수증과 의미적 잔여는 기존 DirectFamilyPreopenPolicyHandoff 및 PostcloseStructuralPolicyCompletion1011 owner에 기록한다.

## 14. 장후 보유 연구 캐시의 물리 레코드 분할

정규 postclose_exit 최초 시도는 보유 연구에서 `research_shard_record_partition_required`로 실패했다. 앞선 거래·매도 후속·누락 진입 보고서와 원 실패 로그를 보존했다. 같은 입력을 다시 계산하던 분석 retry의 정확한 PGID만 확인 후 중단했으며 매매 프로세스·정책·주문은 변경하지 않았다.

격리된 native replay에서 호가 9,665바이트와 파생 feature 77,987바이트의 결합 레코드 87,655바이트를 재현했다. 32개 `new_observations`는 정상 계산 결과이며 source gap이나 잘림으로 처리하지 않는다. 이 목록을 기존 content-addressed tree로 분할하고 캐시 소비 시 hash/count 검증 후 복원한다. 64KiB 물리 row·256KiB leaf·64MiB 캐시 한도, 후보·분류·경제성 계약은 유지한다. 단일 관측 자체가 분할 한도를 넘으면 기존 무캐시 streaming으로 동일 feature를 소비하며 유효 관측을 버리지 않는다.

소유 모듈은 기존 `automation/main_trailing_partitioned_research.py`와 대응 테스트다. 분할 전후 원 관측의 전수 일치·한 번 분류·변조 거부·무캐시 보존 및 native 연구/holding 회귀를 검증한 후 복구한다. 기존 네 산출물의 완전한 manifest가 없으면 세 파일의 존재만으로 완료나 재사용 영수증을 만들지 않는다. 불완전 snapshot은 수리된 producer로 다시 생성하고, 별도 성공한 정책 stage는 native 계약 검증 후 재사용한다. owner는 `HoldingProfitExitSourceContractRepair`이며 다음 영업일 준비와 실제 PREOPEN/PID 수용은 구분한다.
