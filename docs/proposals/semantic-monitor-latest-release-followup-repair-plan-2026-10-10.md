# 의미적 감시기 최신 릴리스 연계 상세 보완계획

작성일: 2026-10-10 KST

현재 릴리스에서 확인된 알림 누락·복구 상태 불일치·현행 담당 작업 결손을 먼저 수리하고, 제출 지연·트레일링·손절 변경을 생산자부터 마지막 소비자까지 연결한다. 기존 detector·native validator·notifier를 보완하며 새 감시 프레임워크나 중복 보고서 체계를 만들지 않는다.

상태: **10/11 반복 리뷰·보완 후 승인된 통합 배포와 10/12 기동 준비 PASS**. F1–F4/R1–R5 수리와 설치된 trailing/delay/수량 및 새 stop 계약 연결을 구현·격리 시험했다. [10/11 구현·반복 리뷰](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)에 변경·실측·잔여 수용을 기록한다. 승인된 후속 작업에서 native 장후 인계·배포·PREOPEN을 완료했다. 운영 Telegram과 휴일 봇 기동은 수행하지 않았고 실제 10/12 소비는 미래 수용이다. 기존 trailing/delay 작업의 수용을 감시 수리 완료로 소급 간주하지 않는다.

## 1 기준과 권한

- 원칙은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 소유는 [10/11 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md)의 `SemanticMonitorLatestReleaseRepair1010`이다. M0–M8은 이 작업의 내부 단계이며 별도 OPEN을 중복 생성하지 않는다. 실제 실행일이 바뀌면 같은 stable ID와 수용 조건을 이전한다.
- [10/7 현행화 계획](semantic-monitor-current-producer-consumer-refresh-plan-2026-10-07.md)과 [당시 구현 기록](../audits/semantic-monitor-current-producer-consumer-implementation-review-2026-10-07.md)은 역사적 근거다. 완료된 SM01–SM04를 재구현하지 않고 새 상태·연결 결함만 보완한다. 본 문서의 전체 퇴역 경계가 과거 계획의 에피소드 일부 존속 설명을 대체한다.
- 감시 권한은 `report_only`다. 자동 BUY/SELL/CANCEL/retry, 주문 재전송, 정책·threshold·provider·env·lock·봇 상태 변경을 추가하지 않는다. 감시 실패는 감시 배포 gate와 담당 작업에 연결하며 새로운 거래 차단 gate로 사용하지 않는다. 기존 native strict/source/hard safety 검증은 그대로 유지한다.
- episode/widget 자동 실행·수집·UI·연구·장후 발행은 영구 퇴역이다. 과거 보유분은 operator-managed이며 Main이 인수하거나 매도하지 않는다. 과거 journal attribution을 보존하고 잔량·미종결 intent를 Main 진입의 flat 요구로 바꾸지 않는다.
- 정책 등록, 경제 비교, 정책 발행, PREOPEN 준비, 실제 PID 소비, 자연 제출·체결·종결, 비용 후 경제성은 독립 상태다. 초기 등록·부모 계승에 별도의 양수 EV·표본수 gate를 추가하지 않는다. 결손을 0 EV·broker 거절·성공으로 바꾸지 않는다.
- Rebase의 구 entry 선정 수치와 최신 native family의 충돌은 해당 family·명시 승인·날짜별 원본으로 판별한다. 감시 수리에서 구 문턱을 재도입하거나 기준 문서를 무단 수정하지 않는다. README·runbook·Rebase·prompt·AGENTS의 변경은 별도 명시 요청 범위다.

## 2 고정한 출발점

10/10 점검 시 [selector](../../data/runtime/runtime_release_selection.json)는 `main-trailing-delay-20261010-v1`, commit `d61b36b00696865ca9dd13a466d8544a886e2e28`이다. 해당 release와 주요 감시 파일의 bytes를 대조했다. selector는 변할 수 있으므로 구현 직전 M0에서 다시 고정한다.

| 층 | 확인한 상태 | 수용 해석 |
| --- | --- | --- |
| 기존 의미적 감시 | 기계정책 stage 알림, cumulative 선택 복구, native family/date/hash 및 기계 영수증 검사 구현 | 당시 SM01–SM04의 핵심 수리 완료. 새 enum·consumer 결함은 별도 수리 |
| 등록 범위 | detector 7, cron 19, artifact 40, heartbeat 6, native 장후 stage 6 | 수량은 조사 스냅샷이지 영구 고정값이 아님. 예전 13 stage 복원 금지 |
| 선택 코드 | common trailing/replay 및 delay v2 loader 포함 | loader 존재는 v2 정책 선정·실제 소비가 아님 |
| 준비 | [15:42 준비 영수증](../../data/report/main_trailing_delay_deployment/2026-10-10/final-readiness.json)의 10/12 `current_full_contract=pass`, `actual_pid_consumed=false` | 10/12 예약기동 전 `future_due`; PID 장애로 경보하지 않음 |
| 감시 자연 증거 | 위 준비 검증은 이전 10/9 장후 finalization 영수증을 원시각 그대로 재사용 | 최신 release 감시의 자연 실행 완료 증거로 표시하지 않음 |
| 후속 변경 | W1–W5 관련 작업본 수정 진행, `full_plan_acceptance=open`, delay v2 미선정 | 미커밋 소스·격리 결과를 배포 계약에 합산하지 않음 |
| 손절 정책화 | [SL0–SL8](main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md)은 계획 단계 | 미설치 stage·정책 파일의 부재는 현재 장애가 아님 |

기존 선택 릴리스의 notifier/coverage/next-session 관련 테스트는 42개 통과했으나 다음 교차 계약 결함을 잡지 못했다. 이는 수리 후 회귀 결과가 아니라 보완 전 기준이다.

### 확인된 결함

| ID | 우선순위 | 생산자와 소비자의 불일치 | 재현과 영향 |
| --- | --- | --- | --- |
| F1 | P1 | [청산 의미 검사](../../src/engine/error_detectors/artifact_freshness.py)의 findings는 warning에만 누적되고 [notifier](../../src/engine/notify_error_detection_admin.py)의 구조화 stage에 연결되지 않음. 초기수량도 동일 | 단독 청산 policy binding 결손을 가진 artifact warning의 알림 결과 0건. 다른 fail이 함께 날 때 우연히 알림되는 것은 해당 결손의 전달 증거가 아님 |
| F2 | P1 | producer의 `operator_initial_registered`, `verified_carried`, `published_policy`와 notifier의 복구 허용 상태 불일치 | 같은 날짜·hash 결속의 결손 없는 관측에서 cumulative 상태는 incident 0건, 새 상태 3종은 각각 1건 잔류. 현재 실제 반복 발송을 확인했다는 뜻은 아님 |
| F3 | P1 | `_project_semantic_owner`가 과거 `DirectFamilySourceRepairMainMechanisticEntry`를 고정 참조 | 선택 release에서 10/10·10/12 모두 기계/보조 owner가 `UNRESOLVED_CURRENT_OWNER`. 10/12 handoff owner는 정상이며 구분 필요 |
| F4 | P2 | [functional coverage](../../src/engine/monitoring/error_detector_coverage.py)는 등록·callable 위주이며 상태별 전달·복구·현행 owner를 검증하지 않음 | F1–F3가 존재해도 coverage `pass`, native stage 6으로 반환 |

### 계획 재리뷰에서 보완한 설계 공백

아래 R1–R6는 F1–F4를 실행 가능한 수리로 닫기 위한 계획 보완이다. 모두 자연 운영 장애가 새로 발생했다는 뜻은 아니다.

| ID | 재검토 근거 | 반영한 기준 |
| --- | --- | --- |
| R1 | `_continuous_reversal_result_semantics`는 `comparison_state=source_gap`이어도 `findings=[]`를 반환할 수 있음 | findings 공백을 비교 원천 정상으로 해석하지 않음. 등록·발행·비교의 원인별 복구 분리 |
| R2 | 청산 getter의 파일 부재는 `not_assessed`, notifier는 `unobservable`을 발송에서 제외 | 기대일·기한·기존 grace를 먼저 검사하고, 기한 후 감시 불능을 별도 전달. 무표본과 미수집 구별 |
| R3 | notifier의 명시적 `native_recovered` 기록 분기는 현재 기계·보조 두 stage이며 state/history는 각 128건만 보관 | 새 청산·수량 stage의 실제 복구 분기, 미복구 상태 보존, 상한 초과·재시작 검증 명시 |
| R4 | owner 해석의 `today`가 과거 `postclose_source_date`일 수 있고, 정상 family는 현재 수리 OPEN이 없을 수 있음 | 관측일/원천일/적용일을 분리. 현행 조치가 필요한 incident에만 수리 owner 요구 |
| R5 | runtime/ref가 바뀌는 동안 여러 파일을 따로 읽거나 missing hash를 임의 키로 쓰면 잘못된 복구·중복 가능 | 일관된 snapshot, hash 종류와 결손 identity, scope별 원천 참조 명시 |
| R6 | M7의 전체 W4 성능 조건이 notifier-only 수리까지 묶을 수 있음 | 즉시 수리 A와 기능 연계 B의 검증·배포 gate 분리. 정책 전환과 미래 적용일은 각 원 owner 계약 유지 |

## 3 생산자와 마지막 소비자 대사

아래 표를 M0의 점검 범위로 사용한다. 각 행은 `expected / future_due / disabled / retired / historical / unobservable`을 native 일정·설치·적용일에 따라 구분한다. 파일 이름이나 stage 개수만으로 기대 대상을 정하지 않는다.

| 경로 | 기존 생산자와 원천 | 감시와 마지막 소비자 | 보완 범위 |
| --- | --- | --- | --- |
| 기계정책·보조 AI | `continuous_reversal_policy_v6` 및 [reversal_policy_status](../../src/engine/scalping/reversal_policy_status.py)의 native 상태·stage receipt | artifact freshness → notifier/state → 현행 작업; loader/PID 증거는 별도 | 등록·승계·비교 상태와 incident 복구의 분리 |
| 장중 기계·보조 원천 | exact native event/cell/route, AI 요청·trace·label·가격 원천 | [submission monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py)의 machine/source semantics → 기존 경보 | 정확 시도·원천 시각 보존. 기계 BLOCK/RECHECK를 보조 AI 미호출 결함으로 보지 않음 |
| PASS 인수·제출 | 원 요청·claim·deadline, Main disposition, intent·broker attempt | `async_disposition_coverage` 및 제출 관측 → 종결 사유 | response 수신을 Main 인수로 대체하지 않고 accepted/rejected/deferred/unobservable 분리 |
| 제출 지연 | [관측 producer](../../src/engine/scalping/pre_submit_delay_observation.py), committed policy, 가격 anchor, due 처리·terminal | `pre_submit_delay_source_semantics`, `entry_execution_tuning_semantics`, native stage/loader | 선택된 due와 원 시도부터 최종 disposition까지 연결 |
| 청산·트레일링 | [holding profit semantics](../../src/engine/scalping/holding_profit_exit_semantics.py), [holding sentinel](../../src/engine/holding_exit_sentinel.py)의 signal·pin·journal·cost generation | `_holding_profit_exit_semantics` → 구조화 알림·복구 | 의미·lifecycle·경제 상태를 나눠 전달 |
| 초기수량·분할 주문 | initial quantity current/ancestor·정책·bundle state·terminal | `_initial_quantity_semantics` → 구조화 알림·복구 | 적용일 정책·총수량·leg·주문 시작 기준 timeout 유지 |
| 전수 장후 연구 | trailing/delay 기존 producer, W1 원천·W2 shard/cohort·비용 revision | native validator → 선정/발행 → summary/strict/controller → PREOPEN | 전체 분모·원천/비용 세대·마지막 consumer 일치. 연구 재실행은 감시 권한 아님 |
| 기동·준비 | selector, prepared, bootstrap, 실제 PID/cwd/start ticks | process/artifact 검사 → next-session 수용 | 예정 전·준비 완료·실제 소비를 분리; 이전 PID를 현행으로 재사용하지 않음 |
| 퇴역 | [owner retirement](../../src/trading/config/owner_retirement.py), cutover receipt, unit/process/installer/journal | [process health](../../src/engine/error_detectors/process_health.py)의 negative census | 신규 자동 권한·실행·발행 부재 검사. 역사적 수탁을 자동 복구하지 않음 |
| 감시 자체 | detector·native stage·cron registry, notifier state, 체크리스트 parser | coverage 및 현행 담당 작업 | 누락/중복 owner, 미전달 상태, 실제 실행 release를 검사 |

장후 6 stage의 소유자는 [postclose_summary_handoff](../../src/engine/automation/postclose_summary_handoff.py)의 `STAGE_REGISTRY`다: `main_machine_policy`, `pre_submit_delay`, `legacy_machine_report`, `main_auxiliary_policy`, `outcome_labels`, `summary_handoff`. `legacy_machine_report`는 현재 보조 AI 선행 입력이므로 이름만 보고 제거하지 않는다. 청산/수량 hook을 추가한다고 중복 장후 stage를 신설하지 않는다.

## 4 즉시 수리할 공통 계약

### M0 기준 고정과 영향 범위

1. selector·release commit·source/effective date·prepared generation·native registry·notifier state schema와 수정 전 해시를 읽기 전용으로 고정한다. 새 release가 선택됐으면 차이만 재대사한다.
2. 위 표의 producer → validator → detector → notifier → recovery → current owner를 조사한다. 적용되지 않은 W1–W5·손절 코드는 후속 범위로 표시하고 현재 기대 집합에 넣지 않는다.
3. 기존 dirty 변경과 역사적 봉인 파일을 보호한다. source 위치는 기존 `error_detectors`, `monitoring`, notifier 및 해당 producer package를 우선한다. 새 engine-root 모듈·중복 registry·주기 작업은 만들지 않는다.
4. F1–F4를 선택 release의 격리 fixture에서 먼저 고정한다. 실제 Telegram·브로커·provider·장후 producer를 호출하지 않는다.
5. 기대일은 기존 거래일 달력·예약 시각·active stage·적용일·승인된 OFF/retirement에서 산출한다. source date를 오늘 날짜로 치환하거나 10/12를 코드에 고정하지 않는다. 미래 준비 대상과 과거 장후 source 재검사를 별개로 유지한다.

종료 기준: 정확한 기준 release와 영향 파일, 실패 fixture, 보호 대상, 기대/미설치/퇴역 집합이 구분돼야 한다.

### M1 청산과 초기수량의 알림 연결

- 수량의 native 생산자·장후 소비자 수리는 [수량 상세 보완계획 Q0–Q8](initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md)과 `InitialQuantityProducerConsumerRepair1010`이 소유한다. 여기서는 Q4/Q6의 정책 PID·거래 결속·비용 표본 상태를 구조화 알림/복구까지 연결한다. 유효 거래 0건으로 PID 조회가 생략된 결과를 정책 미소비로 경보하지 않으며, 비용 결손으로 전부 제외된 원모수를 정상 `valid_empty`로 처리하지 않는다. 당시 PID archive와 현행 PID의 의미를 구별한다. 수량 코드 미수리를 감시 전달 PASS로 완료 처리하지 않는다.
- 기존 `_holding_profit_exit_semantics`와 `_initial_quantity_semantics` 결과를 semantic observations/bindings/alerts에 연결한다. event stage는 각각 `holding_profit_exit`, `initial_quantity`로 정하고 native 장후 stage와 구분한다. notifier의 stage 허용 목록·fallback 조회·복구 분기까지 같은 변경으로 대사한다. 범용 fallback으로 청산·수량 결손을 `machine_report_date_or_hash_invalid`로 표시하지 않는다.
- getter가 알림에 필요한 `source_date`, `target_date`, `artifact`, `generation`, 관측 시각, scope/position/bundle identity를 누락하지 않도록 한다. `report byte SHA`, native `source_generation`, 정책 hash는 서로 다른 필드로 보존한다.
- 현행 current 정책과 기존 포지션·주문 bundle에 유효하게 고정된 ancestor 정책을 구분한다. native 승계·pin 계약이 유효하면 최신 hash와 다르다는 이유만으로 결손 처리하지 않는다. 반대로 이름·숫자만 같은 정책은 정확한 hash 결속을 대체하지 못한다.
- 파일 자체의 부재·파손은 기대 artifact path와 detector 관측 identity로 알림할 수 있어야 한다. 읽을 수 없는 파일의 hash를 합성하거나 hash가 없다는 이유로 경보를 버리지 않는다. 복구는 이후 정상 native 영수증으로 검증한다.
- native 일정상 아직 예정 전이면 위 부재는 `future_due`, 퇴역/명시 OFF이면 비기대다. 기한과 기존 producer grace가 지났는데 expected receipt가 없거나 읽기/관측이 계속 불가능하면 감시 원천 결손을 구조화 알림한다. 이는 매매 실패가 아니라 관측 불능 경보다. 기존 deadline 소유자가 없다면 이를 계약 결손으로 남겨 구현 단계에서 기존 일정 소유자와 결속하고 임의의 새 거래 timeout을 만들지 않는다.
- `source_invalid`, `semantic_contract_invalid`, `policy_binding_gap`은 구조화 incident 대상이다. `runtime_not_consumed`는 적용 시각과 관측 가능한 현행 PID가 기대될 때 평가한다. 예정 전 상태는 `future_due`, 접근 불가·부분 수집은 `unobservable`로 유지한다.
- `pending_submit`, `pending_terminal`은 기존 해당 실행 경로의 deadline/종결 의무로 평가한다. 감시기 임의의 새 timeout이나 주문 재시도를 만들지 않는다. 정상 대기와 기한 초과는 분리한다.
- `valid_empty`는 완전한 원천과 정확한 날짜·분모 검증이 있을 때만 인정한다. `economics_status=pending/unavailable`, `economics_null`은 수집·비용 결손의 원인을 보존하되 단독으로 주문 장애나 손실을 단정하지 않는다. 비용 생산자가 기한 후 누락되거나 schema가 깨진 경우에만 해당 원천 문제로 귀속한다.
- 현재 getter가 개수로 축약하는 `source_gaps`, lifecycle 및 findings의 원인·정확 position/buy-fill/signal 또는 bundle/leg identity를 bounded 예시와 원본 위치로 보존한다. 하나의 손상 포지션을 전체 정상 포지션의 결손으로 확대하지 않고, 원천을 찾을 수 없는 집계값만으로 복구하지 않는다.

종료 기준: 청산·초기수량 결손 각각이 단독 warning 환경에서도 정확히 한 incident로 전달되고, 정상 대기·무표본은 오경보하지 않는다. 복구·재발·잘못된 generation의 경보 미해제까지 통과한다.

공통 알림 결속은 다음을 따른다. 새 별도 저장소가 아니라 기존 semantic payload/state의 호환 확장이다.

| 구분 | 필드와 처리 |
| --- | --- |
| 시각 | `source_date`, 실제 `target_date/effective_date`, `observed_at`, 기존 기대/종결 기한을 구별. 과거 source 재실행의 관측일은 현재 KST |
| 원천 | artifact path, 읽은 bytes의 SHA, native source generation, policy hash와 schema를 분리. 동일 원본 bytes를 읽어 hash·parse·검증하고 서로 다른 읽기 세대를 혼합하지 않음 |
| 범위 | stage/family와 native scope/cell/route, position/bundle/attempt identity. raw 원본의 offset/key 등 재조회 가능한 참조와 유한 예시를 유지 |
| 결손 | 파일 부재 시 source hash는 null, 기대 generation은 검증된 pointer가 제공할 때만 기록. 결손 key는 기대 경로·stage·원천일/적용일·scope·reason으로 안정화하고 실행시각·run ID를 key로 삼지 않음 |
| 발송/복구 | 현재 조치 여부와 역사적 상태, producer/repair owner, closure test를 분리. 여러 hook의 같은 결손을 중복 발송하지 않음 |

selector/current pointer·관련 참조가 검사 전후 바뀌면 한 invocation 안에서 유한 재조회하거나 `generation_changed/unobservable`로 종료한다. 이 결과로 기존 incident를 해제하지 않는다. 원천 변경을 기다리는 무한 retry와 전 파일 재해시를 추가하지 않는다.

### M2 정책 상태와 incident 복구 정합화

상태 판단은 기존 `reversal_policy_status.report_state`와 native validator를 재사용한다. 문자열 하나를 정상 목록에 추가하는 것으로 끝내지 않는다.

| 관측 | 처리 |
| --- | --- |
| `operator_initial_registered` | 등록·발행 및 해당 결손의 native 검증이 정상일 때만 구조 incident 복구. 경제 비교 완료를 요구하거나 합성하지 않음 |
| `verified_carried` | 승계 원본·부모·effective date·hash가 유효하면 승계 구조 결손 복구. 비교 미완료나 후보 부재는 그대로 표시 |
| `cumulative_winrate_selected` | 현재 검증을 보존하고 공통 정확 결속 검사 적용 |
| `published_policy` | 단순 catch-all 성공으로 취급하지 않음. 알려진 schema·발행 근거·native validation과 원 결손 해소가 증명될 때만 복구 |
| `source_gap`, `review_required`, warning | 상태명만으로 복구 금지. 원 incident와 같은 scope/reason이 해소됐는지 native 근거로 판단 |
| `future_due`, `unobservable`, 부분 읽기, 날짜 변경 | 정상 복구로 변환하지 않음. 현행 관측 가능성과 역사적 미복구를 분리 |
| `off`, `historical`, `retired` | 유효한 적용일·generation의 분류 전환만 기록. 과거 결손을 고쳤다는 `native_recovered`를 만들지 않음 |

등록/발행 구조와 비교 원천은 독립적으로 검사한다. `policy_states.comparison_state`, native scope의 blocker/exclusion 및 scope census가 요구 원천의 결손을 가리키면 `findings=[]`만으로 그 원천 incident를 해제하지 않는다. 반대로 유효 승계의 `comparison_complete=false`·무후보·정상 표본 부족 자체를 정책 발행 실패로 승격하지 않는다. 같은 보고서에서도 등록 hash 결손은 복구되고 비교 원천 결손은 남을 수 있다. 원인 증거가 없으면 unobservable/계약 결손으로 남기며 이유를 추정하거나 구 EV gate를 추가하지 않는다.

공통 복구 조건은 stage/family·scope·원천일·적용일·정책/원천 generation의 정확 결속, 최신 관측의 완전성, 원 결손 해소다. 같은 논리 평가의 정식 재생성도 새 generation으로 결속하고 원 봉인 bytes를 수정하지 않는다. 원 결손의 복구와 다른 successor에 의한 대체를 구분하며, 다른 날짜·다른 cell·다른 포지션의 성공으로 복구하지 않는다. 신규 세대로 대체됐지만 역사적 결손이 남으면 `superseded_generation_unrecovered` 등 기존 역사 분류를 보존한다.

청산·수량의 recovery도 명시적으로 구현한다. 현재 기계·보조 전용 분기 뒤에서 다른 stage가 unresolved와 history 양쪽에 남지 않고 탈락하는 경우를 금지한다. stage별 native closure test에 따라 active 유지, 관측 불능, 역사적 미복구 분류(대체/OFF/퇴역 포함), 검증된 복구 중 정확히 하나의 처분을 남긴다. `pending_terminal`에서 binding만 정상화된 경우 binding incident만 해제하고 종결 미확정은 유지한다. 대상이 cursor/window에서 사라졌다는 사실은 종결·복구 증거가 아니다.

notifier state를 지워서 경보를 없애지 않는다. 담당 작업 이전만으로 incident fingerprint가 바뀌어 중복 발송되지 않도록 기존 state의 호환 migration을 검증한다. Telegram 실패는 미전달로 남겨 기존 재시도·중복 억제 계약을 유지하고, 복구 결과는 신규 fail이 없는 호출에서도 정확히 저장한다. 호출 wrapper의 기존 잠금이 같은 state를 사용하는 CLI까지 보호하는지 대사한다. 보장이 없으면 notifier state에 한정한 유한 잠금으로 load→정합화→atomic 저장의 경합을 막되 operator/trading lock은 변경하지 않는다. 부분 전송·중간 종료 후의 재시도 의미를 검증하고, 전송 실패를 성공으로 기록하거나 정확히 한 번 전달을 보장한다고 과장하지 않는다.

현재 128건 state/history 상한을 단순 제거하지 않는다. 상한 경계에서 누락 수·범위와 원 보고서 참조를 보존하고 불완전 상태임을 표시하며, 잘려 나간 미복구를 해제·전체 정상으로 계산하지 않는다. 원인별 유한 집계와 기존 원천 재조회로 처리하고 재조회 불가능한 역사는 `historical_unrecovered/unobservable`로 남긴다. state 손상/legacy migration 실패도 조용한 빈 state 초기화 대신 해당 감시 결손을 기록한다. 상세 조회가 필요한 기존 보고서의 보존 범위는 retention owner와 대사하되 이 수리에서 무제한 archive를 신설하지 않는다.

종료 기준: 새 상태 3종과 기존 상태에서 유효한 원 결손만 해제된다. 날짜·hash·scope 변조, source 재작성·구세대 지연 도착, state 재시작, 전송 실패, 중복 invocation 시험을 통과한다.

### M3 현재 실행 가능한 담당 작업 연결

- production owner와 repair owner를 분리한다. native 생산자의 원래 책임·역사 ID는 보존하고, 현재 조치 담당은 현재 KST 실행일의 정확한 체크리스트 OPEN을 사용한다. 과거 source-date 재점검이라고 과거 완료 항목을 현행 담당으로 삼지 않는다.
- 기존 parser와 `_project_semantic_owner`를 보완한다. 유일한 현행 stable ID 및 명시적 이전 관계만 인정하고 문자열 유사도·가장 최근 문서·과거 `[x]`로 임의 대체하지 않는다. **현재 조치가 필요한 incident**에 대해 0건/중복이면 `UNRESOLVED_CURRENT_OWNER`를 숨기지 않고 coverage finding으로 연결한다. 정상 family나 역사적 미복구가 있다는 이유만으로 매일 source repair OPEN을 강제하지 않는다. parser 예외·현재 문서 부재는 정상적인 OPEN 0건과 별도로 기록한다.
- F1–F4의 수리 담당은 `SemanticMonitorLatestReleaseRepair1010`이다. 이는 이번 감시기 코드 결함의 owner이며 모든 향후 기계·보조 원천 장애를 영구 인수하는 fallback이 아니다. 업무 유형별 기존 source repair owner 또는 명시적으로 이전된 현행 owner가 필요하다.
- 자연 기동 수용은 적용일의 기존 `DirectFamilyPreopenPolicyHandoff`와 연결한다. [10/12 체크리스트](../checklists/2026-10-12-stage2-todo-checklist.md)에는 보조 AI의 `DirectFamilySourceRepairCompactAuxiliary`가 실제로 존재한다. 현재 두 stage 모두 기계 담당 ID를 참조하는 것이 결함이며, 보조 담당 자체가 없는 것은 아니다. 기계의 `DirectFamilySourceRepairMainMechanisticEntry`는 그 목록에 없다. 구현 착수 시 미연결 기계 결함의 실제 실행 owner/명시 이전 관계를 등록하고 parser로 하나인지 확인한다.
- 봉인된 10/12 체크리스트·prepared를 지금 수정하지 않는다. 후속 승인된 인계에서 문서가 바뀌면 영향받는 summary/strict/prepared를 정식 successor로 재봉인한다. 별도 파일만 바꿔 기존 PASS를 재사용하지 않는다.
- 구현 시 필요한 기계 원천 조치가 실제로 있으면 체크리스트에 정확한 native family/source/blocker/closure test와 명시 연결을 함께 등록한다. 정상 기계정책이라면 owner 부재 자체를 새 사고로 만들지 않는다. 이 문서 등록만으로 selected release의 `_project_semantic_owner` 또는 원천 수리 권한이 변경되지는 않는다. owner 해석 실패를 다시 같은 owner resolver로 반복 전달하는 재귀 경보는 한 감시 계약 결손으로 제한한다.

| 알림 종류 | 연결 기준 |
| --- | --- |
| 감시기 코드 F1–F4 | 현재 단일 `SemanticMonitorLatestReleaseRepair1010` 또는 명시적으로 이전된 같은 작업 |
| 보조 AI 원천·native 비교 계약 | 해당 날짜의 `DirectFamilySourceRepairCompactAuxiliary`; 정상 승계와 비교 미완료를 구별 |
| 기계정책 원천 계약 | 기계의 명시 현행 source repair owner. 현재 미등록을 숨기지 않고 등록/이전 전 unresolved 유지 |
| 준비·PID handoff | 해당 적용일 `DirectFamilyPreopenPolicyHandoff`; 미래 예정 owner를 오늘 완료된 작업으로 간주하지 않음 |
| 청산·수량·delay의 업무 결함 | 해당 producer의 실제 OPEN과 scope/closure test 일치 확인. 감시 코드 owner 또는 이름이 비슷한 entry split 작업에 일괄 전가하지 않음 |

종료 기준: 루트·`src/`·다른 cwd, 휴일·자정·과거 source 재검사, closed/duplicate/missing/이전 owner 사례를 통과한다. 미연결은 정상으로 숨기지 않고, owner 이전 때문에 기존 incident가 중복되거나 복구되지 않는다.

## 5 최신 기능과 연결할 검사

### M4 제출 지연과 PASS 제출 경로

[PASS 인수 계획](main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md) 및 [제출 지연 S0–S6](pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md)의 기존 identity·deadline·successor 계약을 소비한다. 감시를 위해 재평가 요청·호가 조회·AI 호출을 추가하지 않는다.

1. 원 PASS 요청/response → Main accepted/rejected/deferred/unobservable → delay commit → 선택된 due 처리 → intent/submit 또는 최종 guard 종료를 원 attempt/claim/policy generation으로 연결한다. 저장 실패는 진단 결손이지 broker 거절·주문 미제출 증거가 아니다.
2. `price_ready`와 `signal_ready` anchor를 구분한다. 기존 0초 관측·route·terminal 검사를 유지하고 선택되지 않은 30/60/120/180초의 부재는 진단으로 남긴다. 실제 선택한 due가 왔는데 필요한 갱신·완료·명시적 만료 종결이 없는 경우를 별도 결손으로 다룬다.
3. due 원천 요청의 접수·중복 결합·admission·완료·만료는 실제 producer의 상태명과 영수증부터 확인한다. 일부 상태가 원천에 없으면 `instrumentation_gap`이며 호출 성공으로 추정하지 않는다. 추가 필드는 기존 경량 이벤트 경로에만 둔다.
4. 원 PASS TTL과 successor 자체 deadline, due+허용 budget을 각각 보존한다. 만료된 원 시도를 연장하거나 후속 claim을 이전 결과로 소모하지 않는다. 진짜 stale·route conflict·수량/계좌 guard 종료는 정상 위험차단 사유로 남긴다.
5. 장후 가격 비교의 완료에 실제 체결·손익을 추가 필수조건으로 붙이지 않는다. 가격쌍 유효성, 정식 정책 발행, 실제 runtime 소비는 별도 수용이다.

종료 기준: 선택 지연 0초/양수, deadline 경계, 정상 reject/defer, 요청 미접수·완료 유실, 중복 callback·후속 claim, 일부 원천 읽기와 회복을 격리 시험한다. `response_received`만으로 submit 성공을 만드는 사례가 없어야 한다.

### M5 장후 전수 연구와 정책 인계

[잔여계획 W0–W6](main-trailing-delay-residual-work-completion-plan-2026-10-10.md), [전수 트레일링](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md)의 실제 배포 상태를 소비한다. 감시기가 해당 연구·발행 기능을 대신 구현하거나 전수 연구를 실행하지 않는다.

- 원천 manifest → shard/checkpoint → 전역 census/cohort → 선택/부모 유지 → committed generation → loader → summary/strict/controller/finalization → PREOPEN → PID/pin을 연결한다. 기존 설치 stage 외부의 producer도 실제 마지막 소비자까지 확인한다.
- shard별 성공을 전체 성공으로 합산하지 않는다. 분모 누락·중복·늦은 conflict·source/cost revision은 native global validator 결과로 확인한다. code/source/cost hash가 바뀌면 구 결과의 적용 범위를 무효화하고 영향받은 생성 경로만 담당 작업에 연결한다.
- 부모 계승·검증된 0초 baseline은 그 family의 정식 발행 계약에 따라 인정한다. `comparison_complete=false`, `source_gap`, `hold`, 초기 등록, `published`, `selected`, `consumed`를 구분한다. 원천 producer/caller 미연결을 단순 표본 대기로 분류하지 않는다.
- 후속 v2 발행 전에는 기존 정상 v1/부모 정책 부재를 만들지 않는다. 전환 뒤에는 selected release의 loader, 정책 pointer/bytes, verifier, bootstrap, prepared가 같은 전환 세트인지 검증한다. 구코드와 신규 pointer 혼합은 source/contract 결손이다.
- 연구의 합산 자원·기한·admission 지연은 W4의 기존 영수증을 읽는다. `running` 정상 작업, 예산 거절·재개 가능, producer 실패, 최종 기한 초과를 분리한다. 감시가 새로운 heavy job이나 무한 재시도를 시작하지 않는다.

종료 기준: 기존 정상 세대, 일부 shard 실패, global denominator 불일치, 비용 사후 정정, 구 reader/new policy 혼합, 정식 부모 승계와 준비/PID 분리 사례를 통과한다. 후속 기능 미배포는 M5 수용 대기로 기록하며 M1–M3의 독립 수리를 지연시키지 않는다.

### M6 손절 정책화와 퇴역 경계

손절의 구현 책임은 `MainStopLossRetirementRuntimeTuning1010`에 남는다. 감시 연결은 그 구현의 배포 전 fixture 검증에 포함하고, 실제 적용 뒤 native 소비로 확인한다. 배포될 때까지 검증 구현을 미룬다는 뜻은 아니다.

- 적용 전에는 손절 신규 bundle/stage를 `not_installed`로 구분한다. 적용 뒤에는 실제 role별 기준·소프트 유예·보호 트레일링 파라미터의 유효 정책, position pin, fast/normal 소비 일치를 native 영수증으로 확인한다. 60초는 현재 초기 기본값이지 감시기에 고정할 정상값이 아니다. 시간·수치·정책 해석은 해당 producer와 실제 selected/ancestor pin을 재사용한다.
- 수동 인계, hard/protect/emergency 우선권, quote 시각, deadline·claim 연결은 검증하되 감시기에서 손절 평가·매도·유예 연장을 실행하지 않는다. 과거 score 손절·whipsaw 전용 관측/추천/발행이 제거되면 그 부재를 회복 대상으로 등록하지 않는다.
- episode/widget은 unit/process뿐 아니라 설치·복원·gateway·새 journal intent·장후 stage의 재유입도 기존 negative census로 검사한다. 퇴역 후 BUY뿐 아니라 자동 SELL/CANCEL/retry도 금지 대상이다. 역사적 journal·수동 관리·공통 cost/WS 이름만으로 누출 경보하지 않는다.

종료 기준: 적용 전 부재 정상, 적용 후 binding 결손 경보, retired 실행 재유입 경보, 역사적 잔량·수동 관리 비차단, 구정책 rollback으로 퇴역 기능 복원 금지를 시험한다.

## 6 검증과 성능 기준

### M7 교차 계약 회귀

`validate_semantic_coverage`는 기존 registry에서 기대 집합을 구하고 producer → hook → 구조화 알림 → recovery → owner → terminal consumer를 대사한다. 정적 검사와 격리 동작 시험을 구분하며 등록 개수 PASS를 전달 PASS로 표현하지 않는다. 외부 호출 없는 의존성 치환으로 검증한다.

신규 감시 필드의 metric 계약은 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=native_exact_date_generation_and_existing_bounded_window`, `sample_floor=expected_source_contract_no_statistical_floor`, `primary_decision_metric=exact_binding_delivery_recovery_findings`, `source_quality_gate=native_validator_and_complete_observation`으로 명시한다. `forbidden_uses`에는 매매/정책/threshold/provider 변경, 누락을 0 EV로 대체, 미관측 PID·제출·체결 성공 주장을 포함한다. 기존 funnel·경제 지표를 이 진단 분모에 혼합하지 않는다.

| 시험 묶음 | 필수 사례 | 실패 시 조치 |
| --- | --- | --- |
| 전달·복구 | F1·F2 재현, 모든 신규 상태, 잘못된 날짜/hash/scope, findings 공백+비교 source gap, 원천 부재와 hash null, scope 하나만 복구 | 감시 코드 gate 미통과; 거래 guard 변경 금지 |
| notifier state | 재시작·중복·부분 전송 실패·owner 이전·과거 세대 지연 도착·새 fail 없는 복구 저장·128건 초과·state 손상·비기계 stage 탈락 | 기록 보존 및 호환 수리; state 삭제 금지 |
| owner·기대 집합 | F3·F4, 단일/중복/완료/이전, 정상 family의 OPEN 0건, parser 실패, 휴일·과거 source, 기한 전/후 미관측, active/OFF/retired/미설치 | 현행 owner/기대 계약 보완; 과거 완료를 현행으로 복원 금지 |
| 청산·수량 | pin 불일치, runtime 미소비, valid-empty, 정상 pending, 기한 초과, 비용 미확정 | 원인·기한·원천에 따라 분류; 가짜 종결/0 EV 금지 |
| 제출·장후 | M4–M6 identity, 선택 due, shard/global census, v1/v2, 비용 revision, exact PREOPEN | 해당 native source/consumer로 귀속; 전체 입력 blanket 차단 금지 |

기존 테스트 파일을 확장한다: `test_notify_error_detection_admin.py`, `test_error_detector_artifact_freshness.py`, `test_error_detector_coverage.py`, `test_next_session_semantic_coverage.py`, `test_submission_bottleneck_monitor.py`, `test_holding_exit_sentinel.py`, `test_main_only_retirement.py`, 해당 pre-submit/initial-quantity suite. 신규 test/module이 필요하면 AGENTS의 위치 gate를 먼저 적용한다.

성능 검증은 수정 전 동일 selected release와 수정 후 코드에 같은 동결 입력·작업량을 주고 정상/burst/slow-writer를 각 3회 비교한다. detector/notifier-only 변경은 그 경로의 wall time·CPU·RSS·읽기/쓰기 bytes·decode/hash 횟수·기존 cadence와 budget만 검사한다. 미완료 전체 W4 연구를 F1–F4 수리의 선행조건으로 만들지 않는다. Main 이벤트 producer·due scheduler·청산 hot path까지 변경하면 해당 경로의 지연 및 W4 합산 예산을 추가 검증하고 기존 통합 성능 근거 중 영향 없는 부분은 재사용한다. 의도한 경보/복구 수정 외의 판정·분모 변화 및 전달 누락은 0이어야 한다. 허용 성능 오차는 측정 전에 동일 환경의 baseline 편차와 기존 gate로 고정하고, 결과를 본 뒤 상한을 늘리지 않는다.

기존 incremental cursor·10분 window·32MiB raw read budget 및 각 reader의 유한 크기 제한을 보존한다. 변경 없는 원천을 매 주기 전부 decode/hash하거나 전체 WS snapshot을 재저장하지 않는다. 한 invocation 내 동일 검증 결과 재사용은 가능하나 inode/size만으로 같은 generation이라고 추정하지 않는다. budget 초과·rotation·읽기 불완전은 `partial/unobservable`이며 incident 해제 근거가 아니다. 새 주기/상주 worker·동기 브로커/AI 호출은 0개다.

검증 순서는 실패 fixture → 구현 → self review → 보완 → 재리뷰 → 영향 pytest/compile → diff/document parser다. 발견된 in-scope 결함이 남으면 감시 구현 완료로 표시하지 않는다. 자연 표본 부재는 구현 결함과 분리한다.

## 7 배포와 자연 수용

### M8 승인 후 인계

1. **A 묶음**은 M0–M3와 그 영향 M7로 F1–F4 및 필요한 R1–R5 계약을 닫는다. **B 묶음**은 M4–M6와 그 영향 M7로 최신 기능을 연결한다. A의 별도 승인 배포는 B 전체 연구·미래 자연 표본을 기다리지 않으며, B에 미배포 의존성이 있으면 owner·조건을 남긴다. B 대기를 포함한 상태를 전체 계획 완료로 표시하지 않는다.
2. 감시 배포 승인이 있을 때 불변 release에서 재검증하고 selector·cron router·실제 detector 실행 root를 대사한다. 감시 변경만으로 Main 재기동이 필요한지부터 확인하며, 기존 trailing/delay의 별도 승인을 이 작업의 재기동 권한으로 전용하지 않는다.
3. 정책 bytes·주문 guard·operator lock·수탁을 보존한다. 코드/체크리스트/summary 변경이 prepared 계약에 영향을 주면 승인된 기존 경로로 successor 세대를 준비·검증한다. 장후 재생성은 영향받는 producer/consumer만 수행하며, 회복 runbook 실행 권한 없이 넓은 장후 작업을 시작하지 않는다.
4. 검증된 다음 예약 detector/notifier 실행에서 새 release provenance와 읽은 source/target/generation을 확인한다. 테스트 알림을 운영 Telegram으로 보내지 않는다. 자연 결손이 없으면 알림 전달은 fixture 검증 완료로만 표시하고 실제 사건 전달을 주장하지 않는다.
5. 현재 목표는 10/12이며 그 기동 이전에는 `future_due`를 유지한다. 구현 시점에 목표가 달라지면 실제 selector/prepared·거래일 달력의 적용일과 기존 자연 수용 owner를 함께 이전하고 날짜를 고정하지 않는다. 적용일에는 실제 PID/cwd/start ticks·정책/pin 소비와 관측된 PASS·선택 due·청산 사건만 마지막 disposition까지 추적한다. 사건을 만들기 위한 AI/주문 호출은 하지 않는다.
6. 첫 해당 장후에서 native 의미와 stage terminal·strict/controller/finalization의 일치를 확인한다. 과거 finalization 재사용은 허용된 read-only predecessor 검증과 원 as-of 표시가 있을 때만 인정한다. 이전 release receipt를 새 release 자연 실행 증거로 바꾸지 않는다.

실패 시 감시 변경의 검증된 이전 호환 세대로 되돌리되 신규 정책 pointer와 구 loader를 혼합하지 않는다. 이미 바뀐 family가 있다면 해당 owner의 전환 세트 복구 계약을 따른다. 상태 이력·원천을 삭제하거나 전체 pre-retirement release로 복원하지 않는다. 정책·봇 재기동이 필요한 복구는 별도 권한으로 처리한다.

## 8 완료 보고 기준

- 현재 결함 F1–F4: 재현·수리·재검증 결과와 미해결 finding 수를 기록한다. 계획/코드/배포/자연 전달은 각각 표시한다.
- 최신 기능: 설치된 producer와 마지막 consumer별 수용, 미배포 의존성, 명시 owner·원천 artifact·다음 조건·closure test를 남긴다. 감시기 hook 하나의 PASS로 전체 장후·실행·경제성을 승인하지 않는다.
- 퇴역/권한: 자동 실행 재유입 0, Main/manual 수탁 및 기존 guard 변경 0. 역사적 미복구는 보존한다.
- 문서 단계: 로컬 링크·현재 owner 단일성·권한·날짜·공백을 검토하고 print-only parser로 검증한다. 10/11에는 작업본 코드와 격리 상태를 검증했으며 운영 정책/state/봉인 준비는 변경하지 않았다.

권장 실행 순서는 **A: M0 → M1·M2 → M3 → 영향 M7 → 승인된 M8**, 이후 **B: 실제 설치/배포 예정 범위의 M4–M6 → 영향 M7 → 승인된 M8**이다. 중간에 새 release가 선택되면 M0 차이 대사 후 영향 단계만 다시 검증한다.

## 9. 10/11 구현 인계

[10/11 구현·반복 리뷰](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)에 F1–F4 및 R1–R5 반례, native ancestor/PID/선택 due/새 stop 연결, notifier 부분 batch 실패·stale/corrupt state·보고서 읽기 교체 시험을 기록했다. 공유 stage registry는9개이며 수량 자체가 성공 조건은 아니다. A의 정적/격리 수리는 B 전체 성능·미래 자연 자료와 구분한다. 실제 전달·선택 release 자연 실행·M8 운영 인계는 미관측이며 current owner를 CLOSED로 만들지 않았다.


### 10/11 후속 승인 배포

[구현 리뷰 §7–§8](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md)의 추가 지연 보완·1057/187개 회귀(중복 포함)와 실제 인계 검증 후 `main-stop-semantic-20261011-v1` / `91edc62844180be6a279e761f32996c3c76ce72e`를 선택했다. source10/8의 정식 finalization은11:33:05 KST DONE이며 target10/12 준비는 전체 계약 PASS다. 기존 임계값·수량·EOD를 보존했고 신규 stop 장후 stage는source10/12부터 연결한다. 실제 PID/자연 청산·경제성과 전체 Main/동시 연구 성능은 이 배포 영수증으로 완료 처리하지 않는다.
