# 위젯·에피소드 적응형 청산 상세 구현계획

작성: `2026-09-09 KST` · 최신 상태: `PARTIAL_ALL_SCOPE_IMPLEMENTATION` · 실거래 활성화: `PENDING_APPROVED_ENVELOPE_AND_INTEGRATION`.

상위 [검토 제안서](widget-episode-adaptive-exit-plan-2026-09-09.md)의 시간/진행률 조기청산과 빠른 접근 일부 잔량 trailing을 구현 가능한 작업 단위로 분해한다. 최초 요청은 상세계획 작성이었고, 이후 사용자가 코드 구현·반복 리뷰를 지시했다. 실제 완료/미완료 경계는 아래 후속 구현 상태와 [구현 리뷰](../audit-reports/2026-09-09-widget-episode-adaptive-exit-implementation-review.md)를 우선한다. 본문의 WP0~WP9·신규 schema/경로는 전체 목표 설계이며, 일부 코드 존재를 전체 구현·자동 적용 완료 또는 producer native 추천 ID로 해석하지 않는다.

### 후속 구현 상태

- 사용자는 **전체 종목·전체 프로필 코드 지원/연구**와 **후보 자동 산출, 승인된 범위에서만 자동 적용**을 지시했다. 첫 연구 scope를 다시 선택하도록 요구하지 않는다. 실제 숫자 envelope·기존 보유 이관·현재 프로세스 재기동을 승인한 것으로 확대하지 않는다. 최신 근거는 [전체 scope 보완 리뷰](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md)다.
- WP2는 조기청산·trailing·결합의 세 모드와 명시적 runner lot 배분을 지원한다. 지정되지 않은 lot을 전량 trailing으로 바꾸지 않으며 합산 target의 부분취소 미지원은 연구에서 별도 격리한다.
- WP0/WP3는 전체 catalog → 엄격한 정규화 입력 → 공통 execution base/stress replay → episode 단위 paired EV/순이익·purge/holdout·회전 지표 → native 연구 후보까지 확장했다. 후속 재개에서 기존 attribution의 owner state/동일 stream read → 자연 census → 연속 관측일 history → 자동 연구 grid → child/Markdown을 연결했다. 미생성 optional 입력 파일 의존은 제거했다. 코드 연결/fixture E2E와 실제 배포 이후의 자연 생성은 구분한다.
- WP1은 위젯·공통 two-leg·별도 Samsung 오전에 최초 체결 **관측시각**과 접수된 target의 lot/정책/주문번호·응답 관측시각을 불변 계측한다. 기존 `buy_filled_at` 의미를 바꾸거나 과거 보유의 첫 시각을 발명하지 않는다. 기존 정규화 원천에서 target 완료와 독립적인20분 연구 경로를 재사용하고, 부분매수·합산 target·교체 epoch·원천/예산 결손은 분모에 남긴다. 거래소 체결시각 복원·실제 PID 계측 소비는 완료로 주장하지 않는다.
- WP4/WP5/WP6은5개 gateway→구체 port/session→**위젯 및 공통 two-leg의 실제 `run_once` 소비 분기**까지 연결했다([최신 리뷰 §9](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#9-실제-owner-loop-연결과-custody-보존)). 원 target/lot/registry 결속, 부분체결·교체 SELL 수량, 잠금 상실 시 저장 금지, 날짜/카탈로그 변경 시 session 보존, episode manager 종료 조건을 모의 검증했다. constructor의 `OwnerLoopServices`는 기본 없음이며 실제 launcher의 승인·시세·거래정지 시계·전체 safety 서비스는 아직 설치하지 않았다. 비용 미대사 수량 종료는 `ADAPTIVE_EXIT_FLAT`/별도 위젯 잔량 view로 분리하고 기존 수익 완료/새 BUY로 전환하지 않는다. 합산 target/runner 배분·pending BUY/새 source EXIT의 승인된 중재·전일 주문/미정의 취소/거절 복구·정확한 체결가/비용 원장 반영과 다음 episode handoff→승인 envelope/dispatch/PREOPEN publisher(WP7)·신규 session enrollment가 미완료다. 연구 hash/후보는 활성화 권한이 아니다.
- source9/8의 위젯19·episode136 연구 scope/30 lifecycle은 당시 이력이다. 후속 source9/9 owner-state 읽기 전용 census에서는61 scope(등록 low-price56+Samsung route/profile5), complete56 scope·기존 filled lot19·신규 target/first-fill 결속0을 확인했다. 위젯 당일 accepted BUY scope는0이며 두 분모를 합산하지 않는다. WP8/9 실적용·순이익 개선은 미검증이다. gateway 코드는 확장했으나 실제 목표주문·runtime policy/PID/cron/systemd는 변경하지 않았다.
- 아래 최초 계획 작성 당시의 ‘수정하지 않았다’·‘코드 미구현’ 문장은 이력이다. 현행 구현 경계는 이 절과 최신 리뷰를 따른다. 신규 연구에 상대1%·5/10/20일 동시 양수·모든 조기매도 양수·첫 활성화 전 새 exit 실체결을 요구하지 않는다. 위험값 누락과 미완성 소비 경로를 floor 완화로 숨기지 않는다.

### 최신 후속: 수량 종료와 다음 진입 연결 (§10)

[최신 리뷰 §10](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#10-수량-종료-원장과-기존-다음-진입-handoff)이 위§9 bullet의 후속 상태다. 원 target/교체 SELL exact 수량 terminal→위젯 일반 orders/완료 횟수/기존 다음 신호 gate, 공통 two-leg 당일 횟수 보존→전일 전체 종료 archive→기존 다음 날짜 entry owner를 연결했다. 재시작·저장 실패·날짜/retention의 증거 보존과 전일 완료의 당일 cap 오집계를 보완했다. 수량0은 익절/순이익 성공이 아니며 **정확한 체결금액/비용 대사는 아직 미완료**다. 비용 결손은 null로 보존하고 다음 진입에 별도 경제성 대기 gate를 추가하지 않는다. 최초 승인 envelope와 실제 서비스 설치/정책 발행·enrollment, 합산 target/runner·source EXIT/BUY 중재 및 미해결 전일 broker 복구는 남아 있다. 운영/PID/실주문을 변경한 것은 아니다.

### 최신 후속: 공통 체결 통보와 종료 대사 (§11)

최신 후속은 [§11 공통 체결 통보/종료 대사 순서 보완](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#11-공통-체결-통보와-종료-대사-순서-충돌-보완)이다. WS terminal 선행 시에도 별도의 exact 수량 대사 proof가 원 종료 consumer까지 전달되도록 수리했다. 일반 terminal 멱등성·구 증거·소유권/잔량 안전 조건은 유지한다. 이는 수신 순서에 따른 반복 진입 단절의 코드 수리이며 정확한 비용/순이익·최초 실제 자동 활성화 완료가 아니다. 다음 실행 가능 중재/전일 복구와 외부 정산 원천 gap을 분리해 기존 checklist owner에서 이어간다.

### 최신 후속: 위젯 원 EXIT 단일 owner 중재 (§12)

[리뷰 §12](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#12-위젯-원래-exit와-적응형-청산-단일-owner-중재)는 원 producer와 동결 실행정책이 허용한 위젯 final EXIT를 불변 receipt로 접수해 기존 adaptive driver의 취소/잔량 대사/SELL로 연결한다. 접수 뒤 원천 부재·재시작에도 의도는 유지하며 원천/접수 시각, 원 포지션·정책·lot, fresh BBO·잠금/전체 safety는 검증한다. 미제출 entry confirmation만 철회하고 실제 pending BUY·합산 target/runner·legacy/force-flat·전일 주문 복구는 별도 미완료다. 새 경제성/표본 gate나 실제 자동 활성화는 없으며 원 정책 검증 callback의 실제 launcher 공급·승인 envelope/PREOPEN/enrollment·정확한 비용 consumer는 남아 있다. 이 상태가 위§9~11의 source EXIT 전체 미구현 문구에 대한 후속이다.

### 최신 후속: 합산 target 계산·진단 (§13)

최신 [§16](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#16-group-부분취소와-첫-runner-sellttl-연결)은 승인 action 불변 저장→첫 부분취소→exact 해제량의 첫 runner 지정가 SELL→TTL 취소/runner 수량 terminal을 opt-in으로 연결했다. 기존 target 잔량 예약·단일-lot 전량 terminal guard를 유지하며 ACK/재시작은 재전송 권한이 아니다. runner 종료도 group flat/손익/새 진입 완료가 아니다. 아래§15의 모든 주문 action 미구현은 이전 상태이며, 실제 group 판단 producer·whole-target/잔량·거절/전일 복구와 group 전체 terminal/owner handoff, 최초 numeric envelope/실제 validator·PREOPEN/enrollment/launcher는 여전히 미완료다. 자연 연구 false/exclusion과 실제 운영은 변경하지 않았다.

현재 후속 [§15](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#15-동결-runner-배분과-group-증거-소비-coordinator)는 명시적 runner 회계/전체 lot 순서·취소 전 동결→account/dated-target 단일 저장 슬롯→기존 partial proof/예약 소비 coordinator를 구현했다. 내부 회계를 실제 broker lot별 손익으로 바꾸지 않으며 `sell_authority=false`인 시점별 수량 receipt로 끝난다. 아래§14의 배분/coordinator 전체 미구현은 이전 상태이고, 현재 **group 판단/취소 action→runner SELL/TTL/terminal·whole-target/복구·원 owner handoff와 실제 launcher/enrollment**는 아직 미완료다. 최초 numeric envelope/validator·PREOPEN publisher 및 자연/경제성은 별도이며 코드 지원을 활성화로 보고하지 않는다.

후속 [§14](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#14-부분취소-확인과-원장-예약-보존-연결)에서 정상 부분취소 요청 전량 확인의 dated/current proof→registry 단일 append/잔량 예약 보존을 구현했다. 아래§13의 실제 proof/예약 미구현은 이전 기록이다. 이 opt-in primitive의 소비자인 동결 회계/runner 배분·group coordinator·runner SELL은 아직 없으며 실제 활성화가 아니다. 일부확인/거절·전일 복구는 별도 구현으로 남기고 불가능한 full-request 수량을 계속 기다리는 정상 대기로 처리하지 않는다. 최초 승인 envelope/PREOPEN/enrollment/launcher·자연 소비·경제성은 별도다.

[리뷰 §13](../audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#13-합산-target-배분부분취소-계산-계약과-장후-진단-연결)은 WP4/6의 선행 group 계산·source 진단 범위다. 불변 BUY lot/합산 target와 현재 원장을 대사하고 runner 잔량 하한/상한·부분취소 후 예약/미예약 수량 보존을 검증한다. 기존21:15 census→study→Markdown에 연결했지만 live group coordinator·부분취소 proof/예약 해제/runner SELL은 미구현이다. 실제 합산 SELL의 lot 귀속을 임의 FIFO/비례로 만들지 않으며, 존재하지 않는 broker lot label을 기다리는 대신 동결 owner 회계 배분 계약을 구현해야 한다. 실제 정책/PID/주문·자연 report는 변경하지 않았다. 현재 다음 순서와 검증은§13 및 기존 checklist owner를 따른다.

## 1. 범위와 첫 릴리스 결정

- 목표: 비용 차감 EV와 누적 순이익 개선. 자본점유 감소와 작은 익절 빈도는 보조 지표이며 큰 손실·추가 거래비용을 함께 평가한다.
- 대상: 기존 widget 및 Samsung/low-price의 독립 주문 owner. main bot의 entry/holding/exit/sizing 코드는 변경하지 않는다.
- 첫 runtime 릴리스는 `time_progress_exit`만 지원하고 `fast_partial_trailing`은 별도 후속 릴리스로 둔다. 두 기능의 OFF 코드/회귀 설계는 같이 준비할 수 있지만 첫 실전부터 결합 효과로 평가하지 않는다.
- 첫 적용 cohort는 **승인된 한 owner/symbol/profile/session의 신규 episode**다. 적용 대상은 원천·취소 인터페이스·경제성 확인 후 선택하고 특정 종목을 이 문서에서 임의 승인하지 않는다.
- 수량·진입 신호·목표 tick·일일 cap·cooldown은 보존한다. 청산 intent 이후 추가매수를 막는 중재는 새 exit 계약의 명시적 범위다. 기존 보유·legacy custody는 자동 이관하지 않는다.
- 새 실시간 alpha shadow나 별도 주문 daemon을 만들지 않는다. 기존 원천의 offline 반사실 연구와 허용된 source-only 계측을 사용하고, 실전은 동일 청산 stage의 한 bounded canary만 허용한다.

### 권한 단계

| 단계 | 필요한 지시/증거 | 그 단계에서 금지되는 것 |
| --- | --- | --- |
| 상세계획 | 이번 사용자 요청 | 코드 구현·운영 산출물/PID/env/주문 변경 |
| 코드·회귀 구현 | 후속 구현 지시 | 검증 전 배포/재기동, OFF 코드를 작성한 것을 live 승인으로 해석 |
| source-only 자연 계측 반영 | 해당 수집 변경의 승인된 배포/실행 경로 | 시세 호출량/동시성 상향, 관찰 성공을 매도 권한으로 전환 |
| 최초 exit 활성화 | §3 승인 envelope, 경제성/실행준비, 별도 적용·기동 권한 | 기존 `no_stop/hold_target` 금지사항을 공통으로 삭제, 기존 보유 소급 전환 |
| 이후 자동 조정 | 최초 승인 범위·유효한 evidence/candidate·exact-date PREOPEN | 승인 밖 종목/모드/위험 확대, 매일 수동 env 변경 |

## 2. 코드 대사 결과와 수정 위치

| 기존 파일/역할 | 확인한 연결·제약 | 예정 변경 |
| --- | --- | --- |
| [turnover research](../../src/engine/monitoring/machine_lifecycle_turnover_policy_research.py) | timeout 60/120/180, 실제/CF 종료 용어 혼재, 5/10/20일 동시 조건 | v1 읽기 호환을 보존하고 v2 연구/metric contract 추가. timeout과 trailing의 실행전환 비용·공통 horizon·미완료 분모 분리 |
| [attribution](../../src/engine/monitoring/machine_microstructure_attribution.py) | widget/episode 원천, anchor, turnover 연결 | 실제 fill/lot/정책 epoch·exit 전환 event·후행 경로 결속; 조인 실패는 gap |
| [공통 two-leg machine](../../src/trading/order/regular_two_leg_machine.py) | `_submit_target`, `_reconcile_target`, `_run_once_impl`, `_save`, `_reserve_episode_intent`; gateway Protocol은 `cancel_buy`만 정의 | owner state에 exit 서브상태 추가, 단일 주문 중재, 정확한 SELL 취소/재대사와 crash 복구 |
| [low-price gateway](../../src/trading/low_price_two_leg/gateway.py) | `submit_limit_sell`; `cancel_buy`는 잔량 전체 취소; `current_open_sell_snapshot`은 현재 미체결과 과거 체결 이력 구분 | BUY 취소 재활용이 아닌 owner-validated `cancel_owned_sell` 인터페이스와 explicit 잔량, 원주문·후속주문·날짜·전시장 대사 |
| [widget engine](../../src/trading/widget_auto_trade/engine.py), [gateway](../../src/trading/widget_auto_trade/gateway.py) | target 취소 및 source EXIT 기반 있음; target 자동 재생성과 scale-in이 같은 cycle에 존재 | 기존 registry/gateway를 통해 exit intent를 중재. 잔량 취소 중 target 재생성·추가매수·중복 SELL 차단 |
| [low-price machine](../../src/trading/low_price_two_leg/machine.py), [policy runtime](../../src/trading/low_price_two_leg/policy_runtime.py) | 기존 보유의 생성 당시 policy carry, target 일치 검증 | baseline validator 유지 + 새 exit policy로 생성된 상태만 versioned validator 사용 |
| [low-price preflight](../../src/trading/low_price_two_leg/preflight.py), [Samsung morning preflight](../../src/trading/samsung_morning_one_share/preflight.py) 및 midday/afternoon owner | timeout/forced exit 금지 | 별도 승인된 bounded exit 계약만 추가 확인. 기존 금지의 전역 삭제 없음 |
| [widget policy](../../src/trading/widget_auto_trade/policy.py), [runtime verification](../../src/trading/widget_auto_trade/runtime_verification.py) | entry/target 정책 및 startup receipt | 별도 exit policy hash, 실제 episode 선택 receipt 추가. startup/import만으로 소비 성공 처리하지 않음 |
| [microstructure approval](../../src/engine/automation/machine_microstructure_policy_approval.py) | `evidence_readiness_errors`에도 5/10/20일·상대 EV 1%가 재검증됨; trusted family registry 존재 | trusted family+schema별 evidence validator dispatch. 새 exit family만 새 승인 계약 사용; 기존 family 우회 방지 |
| [final refresh wrapper](../../deploy/run_machine_microstructure_final_refresh.sh), [PREOPEN wrapper](../../deploy/run_threshold_cycle_preopen.sh) | attribution→timing→approval→checklist 및 별도 family consumer | 동일 날짜/세대의 exit 후보/적용 단계 결속. parent rc=0이나 이전 PASS로 새 실패를 가리지 않음 |

### 신규 파일 배치안

- `src/trading/order/adaptive_exit/{__init__,models,decision,reducer}.py`: broker/network/file I/O 없는 타입·판정·상태 전이. 상태 저장은 기존 owner state/registry에 남긴다.
- `src/trading/config/machine_adaptive_exit_policy.py`: schema/hash/envelope 검증과 owner scope의 신규 episode 정책 선택. `machine_entry_timing_policy.py`와 권한을 공유하지 않는다.
- `src/engine/monitoring/machine_adaptive_exit_replay.py`: 기존 turnover producer가 호출하는 offline replay helper. 별도 상시 producer/cron이 아니다.
- `src/engine/automation/machine_adaptive_exit_policy_apply.py`: family-owned PREOPEN 검증·atomic policy publish·apply receipt. broker import/call 금지.
- `src/tests/test_machine_adaptive_exit_{decision,reducer,policy,replay}.py`: 순수 로직 및 artifact 계약. 실제 adapter/회귀는 기존 widget/two-leg 테스트에도 추가한다.

구현 직전 location gate에서 이름 충돌·인접 owner를 다시 확인한다. `src/engine` root에 신규 모듈을 만들지 않는다. 이 계획은 파일을 생성하지 않았다.

## 3. 정책·권한 계약

### 3.1 사전 확정할 승인 envelope

설계 family명은 `machine_adaptive_exit_v1`, stage는 `exit`다. 실제 등록은 최초 승인 후 수행한다. 다음 값은 승인되지 않았으며 누락되면 `blocked_missing_initial_authority`다. 0/null을 무제한 허용으로 해석하지 않는다.

| 필드 | 결정 내용 | 값 확정 전 처리 |
| --- | --- | --- |
| `allowed_owner_scopes` | owner/symbol/profile/session/허용 entry policy 버전, 실제 지원 route | live 선택 0건 |
| `allowed_modes` | 첫 `time_progress_exit`, 후속 `fast_partial_trailing`/결합의 허용 여부 | `baseline`만 |
| `new_positions_only`, `valid_from`, `valid_until` | 적용 범위/기간, 기존 포지션 관리 유효성 별도 | 과거 보유 baseline carry |
| `t_soft_bounds_sec`, `extension_bounds_sec`, `max_extensions` | 정상 시간창·유예; v1 유예 최대 1회 제안 | 연구 후보만 출력 |
| `t_hard_policy`, `loss_budget`, `max_unprotected_duration` | 강제 시간청산 여부, 손실/무주문 잔량 위험 예산 | runtime 활성화 불가 |
| `trail_progress_bounds`, `gap_tick_bounds`, `runner_allocation` | 도달 전 전환 기준·여유·lot/leg | trailing 비활성 |
| `sell_execution_bounds` | 허용 가격/주문종류/TTL/시도·취소 상한/최종 미체결 처리 | broker 호출 금지 |
| `session_end_policy`, `halt_policy`, `source_loss_policy` | 정상 거래시간 밖·VI·시세 공백·장애 후 관리 | generic 기본값으로 청산하지 않음 |
| `evaluation_contract`, `rollback_contract` | 주 평가창·N_min·검증 구간·허용 tail/오차/자동 중지 범위 | apply-ready 불가 |

위험 예산은 운영상 중지/복구 트리거이지 가격제한·유동성 공백에서의 보장 손실 상한이 아니다. 기준가격 미달 시에도 stale 시세나 모호한 주문으로 새 매도를 보내지 않는다.

### 3.2 Artifact 4종

| Artifact/schema 설계 | 필수 내용 | 권한 |
| --- | --- | --- |
| `machine_adaptive_exit_evidence_v1` | source date/byte hashes, cost/master/entry policy hash, exact denominator, A/B/C/D 결과·censor·실행모델·평가창/불확실성 | source-only; actual와 CF metrics 분리 |
| `machine_adaptive_exit_candidate_v1` | producer native recommendation ID, evidence hash, scope, baseline/candidate policy hash, parameter diff, validator version, decision/reason | `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_forbidden=true` |
| `machine_adaptive_exit_policy_applied_v1` | source/target date, next-trading-day 검증, approval envelope hash, exact candidate/evidence hash, selected scopes, frozen per-scope bounds, activation expiry | 승인된 owner의 지정 SELL 전환만 허용. BUY·증액·main·타 owner 권한 없음 |
| `machine_adaptive_exit_apply_receipt_v1` 및 owner load/decision receipt | publication vs load vs actual decision 분리, code/schema/policy hash, PID/starttime, episode/lot/order lineage, consumption 시각 | PREOPEN publisher는 broker-call 금지; actual 주문 receipt는 원래 owner가 발급 |

canonical 연구 저장 방식은 **기존 attribution JSON의 `rolling_policy_research_v2` child**로 정한다. 새 독립 연구 producer/저장 디렉터리를 만들지 않는다. 별도 파일이 필요한 consumer에는 그 child의 hash-bound projection만 발급한다. 적용 파일은 `data/runtime/machine_adaptive_exit_policy/`의 날짜별 파일이며 기존 entry timing 정책 파일을 덮지 않는다.

child에는 raw/upstream source hash를 넣되 자신을 포함한 최종 parent 파일의 hash를 넣지 않는다. child canonical digest는 선언한 hash 필드 제외 규칙으로 계산하고, parent byte SHA256은 parent publish 후 외부 approval/handoff에 기록한다. canonical hash와 byte hash를 서로 대체하지 않는다. v1/v2가 같은 의미의 후보를 발행하면 producer의 successor/native ID mapping으로 한 건만 intake하며 두 배로 집계하지 않는다.

새 schema/권한 값은 typed validator로 다룬다. bool/string 혼동, NaN/Inf, 미래 source, negative quantity, 미등록 mode/owner는 실패다. recommendation ID는 native producer가 발행하며 WP 번호를 구현 권한 ID로 사용하지 않는다.

### 3.3 호환과 schema dispatch

- 기존 v1 `candidate_realized`는 삭제/이름 치환만 하지 않고 old consumer에서 CF 종료 의미로 읽게 유지한다. v2는 `counterfactual_exit_resolved`/`actual_broker_terminal`을 별도로 사용한다.
- 새 evidence validator는 trusted registry에 등록된 exact family/schema/envelope에만 연결한다. 후보가 자기 `schema`나 `validator_version`만 바꿔 낮은 gate를 선택하지 못한다.
- 연구 단계에서도 새 validator를 사용할 수 있지만 그 결과는 `research_ready`뿐이다. 미등록 family의 `eligible_for_next_preopen` 발급은 금지한다.
- 공통 approval ledger는 handoff만 한다. exit policy가 주문 동작에 영향을 준다는 사실을 숨기지 않고 registry에 `owned_sell_only` 권한 범위를 명시한다. `direct_order_authority` 같은 기존 bool만 true로 켜서 모든 주문을 허용하는 설계는 금지하며, publisher·runtime adapter별 허용 동작 검증을 추가한다.
- `apply_receipt`의 no-broker-call과 applied policy의 owner-exit 허용을 별도 필드/validator로 검증한다. 권한 true가 있는 policy를 source-only report처럼 취급하거나 반대로 report를 runtime policy로 읽지 않는다.
- `initial_canary`와 `auto_maintenance`를 구분한다. 최초 적용은 명시적 envelope·기존 broker 실행준비/회귀·직접 경제성 근거로 승인하며 아직 존재할 수 없는 새 exit 실체결 receipt를 요구하지 않는다. 이후 자동 유지/확대는 기존 registry의 post-apply 확인 취지를 유지해 해당 정책의 R6 근거를 요구한다. 이 분기는 trusted family의 최초 1회 범위이지 report가 임의로 선택하는 면제 flag가 아니다.

## 4. R0 계측과 원천 계약

### 4.1 event와 key

공통 event schema 설계는 `machine_adaptive_exit_event_v1`이다. 기존 owner 로그/registry에 다음 사건을 기록하며 새 중앙 custody 원장을 만들지 않는다.

`POLICY_BOUND`, `EVALUATED`, `EXTENSION_GRANTED`, `EXIT_INTENT`, `TRAIL_ARM_INTENT`, `CANCEL_REQUESTED`, `CANCEL_CONFIRMED`, `TARGET_FILLED_DURING_CANCEL`, `TRAIL_ARMED`, `TRAIL_UPDATED`, `EXIT_SUBMITTED`, `EXIT_PARTIAL_FILLED`, `EXIT_TERMINAL`, `RECOVERY_REQUIRED`, `POLICY_REJECTED`.

필수 key는 `owner_id/profile_id/symbol/episode_id/lot_id/leg_id`, `entry_order_date/order_no`, `target_order_date/order_no`, `intent_id`, `entry_policy_hash/exit_policy_hash`, `position_epoch`, `event_id/schema_version`다. 종목·현재 날짜·PID만으로 identity를 만들지 않는다. 취소/정정 후속 주문은 parent order에 결속한다.

필수 시간/원천은 `event_at`, `observed_at`, `received_at`, `first_fill_at`, `active_age_sec`, `wall_age_sec`, `quote_at`, `source_epoch/sequence`, `market_session`, `entry_venue/exit_venue`, source hash다. SOR 주문을 KRX 체결로 추정하지 않고 주문 route와 실제 체결 venue를 구분한다.

### 4.2 가격·수량·시계

- `fill_qty/cumulative_buy_fill/cumulative_sell_fill/open_qty/reserved_sell_qty`를 분리한다. 취소 수량을 매도 체결 수량에 넣지 않는다.
- `entry_cost_basis`, `original_target`, `executable_bid_for_qty`, `depth_covered_qty`, `round_trip_cost_contract`, 실제 비용의 `exact|modeled|unknown`을 보존한다. 모델 비용을 exact 비용으로 정규화하지 않는다.
- executable bid는 그 잔량을 처리할 깊이의 수량가중 가격이며 marketable limit 주문가격은 해당 수량의 최악 체결 가능 level과 승인된 가격 bound로 따로 결정한다. 평균 bid를 그대로 전량 체결 limit으로 사용하지 않는다.
- 실제 첫 fill clock은 추가체결·재시작으로 리셋하지 않는다. 거래정지로 입증된 시간과 단순 WS 결손을 구분하며 후자는 시간을 멈추는 근거가 아니다. 시계/세션 결손은 `clock_source_gap`으로 기록한다.
- first fill 이전 구간은 entry 실행 지연이다. target ack 이전도 보유시간에는 포함하고 `target_protection_delay`를 별도 계산한다.
- v1은 scale-in 없는 안정적인 lot/target epoch를 우선 적용한다. 추가매수로 합산 target이 바뀐 widget episode는 source-only 비교에는 남기되 정확한 lot/부분취소 지원 전에는 새 정책 activation 대상에서 제외한다. 제외율이 너무 크면 구조적 미지원이며 성공으로 포장하지 않는다.

### 4.3 표본 보존과 관측 종료

`all_owner_episodes = eligible + source_invalid + unsupported_policy_epoch + outside_scope`를 배타적으로 닫고 eligible 내에 `target_filled`, `still_held`, `manual_exit`, `other_exit`, `right_censored`를 시간/종료 이유와 함께 보존한다. actual 평가·CF 평가의 eligibility는 별도 필드다.

후행 경로는 모든 선택 episode에서 동일한 사전 고정 horizon까지 수집한다. 목표 익절 뒤 상승한 거래만 추가 수집하지 않는다. 기존 read-only WS source를 재사용하고 메모리/디스크/episode budget과 stop reason을 명시한다. 관측이 target fill과 동시에 끝나는 구조면 WP1 미완료다. 필요한 자연 원천이 없는 과거 날짜의 replay는 반복하지 않는다.

## 5. 순수 판정 인터페이스

설계 함수는 `evaluate_exit(policy, position, snapshot, clock, previous_state) -> ExitDecision`과 `reduce_event(state, event) -> next_state`다. 함수 내부에서 broker·AI·파일·wall clock을 호출하지 않는다. offline/runtime은 같은 normalization·함수·단위를 사용한다.

`ExitDecision`은 `KEEP_TARGET|GRANT_EXTENSION|REQUEST_EARLY_EXIT|REQUEST_TRAIL_ARM|KEEP_TRAIL|REQUEST_TRAIL_EXIT|SOURCE_GAP|RECOVERY_REQUIRED`와 reason, exact snapshot/policy hash, 대상 lot/잔량, next evaluation deadline을 반환한다. 주문 payload는 포함하지 않고 owner adapter가 별도 권한/최신 잔량을 재검증해 만든다.

### 5.1 시간/진행률

`progress = (P_exec - P_entry) / (P_target - P_entry)`; 분모가 0/음수면 invalid. `T_soft` 이후 낮은 progress·최근 개선 부진·bid/체결 지지 약화가 함께 검증된 predicate에서만 early exit intent다. source missing은 support=false가 아니다.

진행 개선·반등 지지가 있으면 승인된 범위에서 1회 유예한다. 유예 종료 후의 규칙과 `T_hard` 선택은 policy에 필수이며 무기한 KEEP으로 빠지는 기본값은 없다. `T_hard` 미사용을 선택했다면 `time_progress_exit`만으로 최대 보유시간이 보장되지 않음을 policy/보고서에 명시한다. 최초 활성화에 필요한 위험 선택은 §3에서 별도로 닫는다.

v1 연구 grid는 timeout `{60,120,180}`초로 시작한다. progress/지지 기준은 훈련 source에서 사전에 고정하고 최대 후보 수를 선언한다. 모든 시간×progress×gap×종목 조합을 전수 최적화하지 않는다. 실제 runtime 숫자는 아직 미정이다.

### 5.2 빠른 접근 trailing

`T_fast` 내에 pretarget progress·지지·비용여유를 통과하고, 지원되는 한 leg/lot의 취소 확인 후에도 조건이 남아 있으면 활성화한다. 첫 설계는 `T_fast <= T_soft`로 역할을 분리하고, 이미 활성화된 trailing 잔량에는 time-progress 분기를 중복 실행하지 않는다. 승인된 hard deadline/명시적 final EXIT는 trailing보다 우선한다.

취소 확인 후 fresh snapshot을 기준으로 high-water를 초기화한다. 이후 `stop = max(previous_stop, cost_cover_floor, high_water - frozen_gap)`이며 tick 반올림 방향까지 함수 계약으로 고정한다. gap 변동으로 stop을 내리거나 미래 봉 고가로 high-water를 복원하지 않는다.

활성화 가능 구간은 `cost_cover_floor + minimum_gap < original_target - transition_buffer`다. 구간이 없거나 실제 취소확인 지연이 fast window를 대부분 소진하면 `unsupported_trailing_geometry|execution_latency_infeasible`로 baseline을 유지한다. 안전 freshness를 완화해서 통과시키지 않는다.

대상 lot의 잔량이 달라지면 quantity epoch를 기록하고 같은 수량 기준 source로 재평가한다. 타 leg 체결이나 quote depth 감소를 새로운 가격 고점으로 오인하지 않는다. 취소 중 전량 체결은 FLAT이며 재진입하지 않는다.

## 6. 주문 상태 전이와 잔량 관리

아래는 기존 machine 상태를 대체하는 것이 아니라 owner state 안의 `adaptive_exit` 서브상태다. baseline 분기는 기존 상태 계약을 유지한다.

| 현재 상태 | 사건/검증 | 다음 상태와 허용 동작 |
| --- | --- | --- |
| `TARGET_WORKING` | predicate 통과, 권한/원주문/잔량 exact | `INTENT_PERSISTED`; 먼저 durable intent 기록 |
| `INTENT_PERSISTED` | registry reservation 성공, cancel 미전송 확인 | `CANCEL_PENDING`; 원주문 exact 잔량 취소 1회 |
| `CANCEL_PENDING` | 단순 취소 ACK 또는 조회 실패 | 상태 유지/`RECOVERY_REQUIRED`; 다른 SELL 금지 |
| `CANCEL_PENDING` | target 일부/전량 fill | 실제 체결 반영; 잔량 0이면 `FLAT`; 아니면 취소/잔량 대사 계속 |
| `CANCEL_PENDING` | 현재 미체결 원장+체결/잔고로 원주문 및 successor 잔량 해소 확인 | `RESIDUAL_READY`; 취소 중 늦은 fill 포함 |
| `RESIDUAL_READY` | early exit, fresh price/broker/잔량 통과 | `EXIT_SUBMITTING` 영속 후 SELL 제출 |
| `RESIDUAL_READY` | trail intent와 arm 조건 유지 | `TRAIL_ACTIVE`; 해당 잔량의 software exit 책임 유지 |
| `RESIDUAL_READY` | trail arm 조건 소멸 | 사전 정책의 `EXIT` 또는 `REPROTECT_TARGET` 중 하나만. 불명확하면 복구 상태 |
| `TRAIL_ACTIVE` | high-water 갱신 | stop/receipt만 갱신; broker 정정 반복 없음 |
| `TRAIL_ACTIVE` | stop/hard deadline/final EXIT | 단일 `EXIT_SUBMITTING` |
| `EXIT_SUBMITTING` | 접수 ACK와 exact order binding 성공 | `EXIT_WORKING`; ACK를 fill/terminal로 세지 않음 |
| `EXIT_SUBMITTING` | ACK 유실/예외/재시작 | registry/실제 미체결·체결 조회로 대사; blind retry 금지 |
| `EXIT_WORKING` | partial fill | 잔량과 reservation 갱신; 그 주문이 살아 있으면 추가 SELL 금지 |
| `EXIT_WORKING` | terminal + 잔량 존재 | bounded 미체결 처리 규칙; 이전 주문 해소 후에만 재제출 |
| any | 실제 owner 잔량 0 및 모든 intent/원주문 해소 | `FLAT`; exit reason과 비용 대사 |
| any | owner conflict/unknown order/source gap | 상태/증거 보존·알림; 승인된 recovery 외 새 주문 금지 |

### 필수 불변식

1. `owned_open_qty = exact_owned_buy_fills - exact_owned_sell_fills - verified_manual_exit_qty`. 음수·불일치는 clamp해서 숨기지 않는다.
2. `new_sell_qty <= owned_open_qty - all_live_owned_sell_reservations`. 계좌 가용 수량은 추가 상한이지 owner 증거 대체가 아니다. 모호한 submit intent도 해소 전 예약으로 본다.
3. 단일 owner lock 안에서 수량 대사→reservation→durable intent를 결속한다. 파일 lock 존재만으로 stale을 선언하거나 삭제하지 않는다.
4. write-ahead intent는 broker 효과의 exactly-once를 보장하지 않는다. crash 경계마다 idempotent local 처리와 실제 주문 대사가 함께 필요하다.
   - 실제 API 전 `CANCEL_PENDING`/`EXIT_SUBMITTING`까지 durable하게 기록한다. 전송 전에 crash한 경우에도 그 상태를 보고 API 미실행으로 단정하지 않는다. negative broker evidence의 조회 완결성·receipt 지연을 확인한 뒤 기존 bounded recovery 절차로만 재개한다.
5. 취소된 주문은 position 감소가 아니다. fill과 cancel의 도착 순서가 달라도 최종 수량이 같아야 한다.
6. `exit_requested`와 새 서브상태를 단일 중재 함수로 연결한다. target 재생성·scale-in·source EXIT가 별도 독립 SELL을 만들지 않는다.
7. 신규 entry/policy expiry와 기존 보유 관리 수명을 분리한다. 다음 날 새 파일이 없다고 활성 exit 책임을 삭제하지 않는다.

### gateway 구현 경계

low-price의 `cancel_buy(order_no)`는 그대로 보존하고 `cancel_owned_sell(order_context, expected_remaining_qty)`를 추가하는 안이다. 이름만 바꿔 기존 잔량 전체 취소 호출을 재사용하지 않는다. widget의 기존 quantity-aware cancel은 lot/원주문·전체 잔고 guard를 재검토해 활용한다. Samsung 각 adapter의 실제 gateway 구현도 함께 확장한다.

프로토콜 구현 전 [공식 Kiwoom reference gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 재수행한다. 원주문·취소/정정 후속 주문, 실시간 체결과 현재 미체결 전체 페이지, route별 주문 허용, ACK/terminal 의미·오류·호출량을 확인한다. 기존 제안서의 spec 부분 열람은 전체 구현 gate 완료가 아니다. 계좌/주문 호출로 단위 테스트를 검증하지 않는다.

## 7. 생존성·장애·rollback

- 기존 widget 서비스 및 episode 서비스가 각자의 보유를 관리한다. 다른 exit daemon이 동일 custody를 공유하지 않는다. 명시적 lease/owner handoff 없는 두 process 동시 소비 금지.
- 기존 read-only WS snapshot consumer를 재사용하되 entry용 짧은 snapshot을 180초의 완전한 exit 경로라고 가정하지 않는다. live 판정용 최근 창과 장후 replay용 영속 경로를 각각 검증한다.
- 기존 polling과 deadline의 차이를 계측한다. 개선은 기존 budget 안의 deadline-aware wake/coalescing으로 제한하며 order/read rate cap을 올리지 않는다. 측정된 delay가 정책 유효창을 넘으면 그 정책은 미지원이다.
- 원천 결손 시 target이 살아 있으면 전환하지 않는다. 이미 취소됐다면 `RECOVERY_REQUIRED`, unprotected duration/알림과 지속 관리가 필요하다. 타이머가 끝났다는 이유로 stale 가격 매도를 허용하지 않는다.
- `run_until_terminal`/service stop/세션 종료에서 active exit를 `HELD` 정상 종결로 넘기지 않는다. 현재 기본 service 모드·타이머를 설치 receipt로 검증한 뒤 변경한다.
- 재기동 복원 필수값은 policy hash/원본 payload, lot clock, trail high-water/stop, source epoch, intent·주문 계보·잔량이다. 필수값 손실 시 baseline target을 임의 재생성하지 않고 exact 복구한다.
- 자동 중지는 **새 정책 선택/새 arm/신규 노출**에 적용한다. 이미 취소된 잔량의 manager를 같이 OFF하지 않는다. 예전 binary가 새 상태를 해석하지 못하면 무조건 코드 downgrade하지 않고 forward-compatible recovery를 사용한다.
- 수동/계좌/global veto의 적용 범위는 현행 계약을 보존한다. 매수 전용 pause와 청산 허용을 혼동하지 않되 새 family가 operator veto를 무시하지 않도록 테스트한다.

## 8. 장후 경제성·달성 가능성 설계

### 8.1 비교와 metric 계약

기존 turnover의 A=baseline, B=time-progress, C=partial trailing, D=combined를 같은 entry 집합/수량·비용 계약에서 계산한다. 실제 완전 체결 완료 집합, 부분체결 집합, 미완료 HELD, CF resolved는 서로 다른 metric namespace다.

주 metric은 `paired_source_quality_adjusted_ev_uplift_pct_points`와 같은 집합의 net KRW 차이다. actual EV는 실제 completed+valid costs만, CF EV는 사전 horizon에서 평가 가능한 경로만 쓴다. unresolved를 0으로 채우지 않고 eligibility/제외율·민감도 한계를 함께 보고한다. 장기 HELD는 공통 horizon CF/점유·tail 연구에 남기되 실현손익으로 만들지 않는다.

동일 episode의 leg와 tick을 독립 표본으로 세지 않는다. chronological train/holdout을 나누고 종료 horizon이 겹치는 episode는 경계에서 purge한다. 비용·가격·epoch를 as-of로 고정하며 유효 source가 있었던 양의 유입일만 골라 ETA를 계산하지 않는다.

전환 지연/부분체결/target queue에 대한 base/stress 실행모델을 미리 고정한다. 모델 불확실성을 비용 buffer와 통계 오차에 이중 차감하지 않는다. 최종 gate는 두 종류의 불확실성이 어디에 반영됐는지 명시한다. 매수 비용은 전체 PnL에 한 번, 동일 비교 시점에서 이미 공통으로 지불한 비용은 잔여 EV 차이에 중복 부과하지 않는다.

### 8.2 평가 계약 확정 절차

1. WP0/1에서 scope별 전체 source-day·고유 episode 유입률·성숙기간·분산·누락/지원률을 산출한다. 후보 성과를 보고 표본 기준을 낮추지 않는다.
2. 주 평가창 `W_primary`, 최소 거래일/episode `N_min`, holdout 구간, 허용 tail deterioration·보수적 execution stress를 사전 versioned 계약으로 고정한다. 인접 window의 중복 양수 판정은 제거 제안이며 현재 코드를 바꾸지 않았다.
3. `Delta_EV`, 같은 집합 net profit, 날짜/episode cluster 불확실성, holdout 비훼손, tail/주문 위험을 함께 판정한다. baseline EV=0에서도 절대 증분은 계산 가능해야 한다.
4. 분석 가능한 연구 row와 live 검토 후보를 분리한다. 연구에는 live N_min을 붙이지 않고 실제 활성화에는 직접 scope 근거·새 권한·실행준비를 요구한다. 새 exit의 실체결을 최초 활성화 전에 요구하는 순환 gate는 금지한다.
5. 실제 자동 유지/확대에는 후보 정책 버전의 자연 cancel/submit/fill/terminal 및 경제성을 요구한다. CF만으로 broker 품질 또는 수익 개선을 확정하지 않는다.

N_min과 위험 수치가 미정인 것은 설계 gate의 명시적 미결정이지 default 승인값이 아니다. 이 단계에서 목표 수익률을 임의로 1%p 등으로 정하지 않는다. 조기청산 subset이 손실이어도 전체 정책의 개선을 평가하며 모든 조기청산의 양수 손익을 요구하지 않는다.

### 8.3 shortage 출력

`raw episodes → exact fill/target/lot → supported epoch → same-route price path → cost-qualified → CF/actual eligible → rolling/holdout ready`의 최초 결손을 기록한다. required/current/deficit, source-day 수, maturity·expiry를 반영한 finite ETA 또는 waiting 불가 이유가 필수다.

`time_resolvable_shortage`, `structural_population_exhaustion`, `blocked_missing_evidence`, `pending_declared_window`, `unsupported_strategy_geometry`, `hold_no_edge`, `pending_initial_authority`를 구분한다. 마지막 두 전략/권한 상태를 표본 부족으로 바꾸지 않는다. 연구 floor 재설계가 정상 source 수집을 차단하는 새 무한 대기열이 되지 않아야 한다.

## 9. 장후→PREOPEN→자연 소비 연결

### postclose

기존 `expansion → attribution(새 turnover child 포함) → weakness → entry timing → approval → checklist`의 entry 동작을 유지한다. 새 exit 후보는 attribution child에서 source-only로 생성하고 approval이 같은 byte/canonical hash 규칙의 generation을 소비한다. 신규 별도 cron/중복 attribution은 없다.

새 child 필수 여부는 schema/활성화 단계로 판정한다. 미등록/disabled 상태의 후보 0은 정상이다. 등록된 활성 family의 필수 child 누락·date/hash 불일치는 해당 exit family failure로 남기며 unrelated family를 무조건 중지하지 않는다. approval/checklist 후 요약→strict verifier→controller의 generation 결속도 유지한다.

### PREOPEN

1. 기존 승인 ledger가 가족별 handoff를 만든 다음 `machine_adaptive_exit_policy_apply`가 envelope·source/evidence·경제성 validator·same-stage 비충돌·거래일/cutoff를 검증한다.
2. 초기 cutoff는 기존 approval ledger와 같은 **08:00 KST 이전** 계약을 따른다. 이를 새 owner가 임의로 장중까지 확장하지 않는다. 등록 시 해당 venue/session과 PREOPEN trigger가 실제로 맞는지 확인한다.
3. 날짜별 mutex 하에 write-temp→validate→atomic publish→receipt 순서다. `--check-only`는 쓰기/주문/알림이 없는 별도 모드로 설계한다. 실제 publish는 기존 auto-apply mode와 새 envelope가 함께 허용할 때만 한다.
4. 이전 날짜 정책을 오늘로 복사하거나 기존 파일의 날짜를 변경하지 않는다. 당일 파일이 이미 신규 episode에 소비됐다면 장중 재계산으로 바꾸지 않는다. 같은 hash 재실행은 idempotent; 다른 hash는 conflict다.
5. 새 파일이 없거나 무효면 새 episode에 baseline을 선택하고 정확한 reason receipt를 남긴다. 기존 활성 exit는 frozen policy/보유 관리 계약을 유지한다. 모호한 주문/잔고 자체가 있으면 신규 매수도 현행 safety에 따라 차단한다.
6. publisher receipt만으로 적용 완료가 아니다. widget/two-leg/Samsung loader 및 신규 episode의 `POLICY_BOUND`→실제 `EVALUATED`/intent receipt가 있어야 runtime 소비다. long-running widget은 day-boundary/new-episode load, episode는 preflight/service startup+new episode binding으로 구현한다.

주문 관련 config가 바뀌는 신규 family는 기존 entry-timing이나 main threshold env에 위장하지 않는다. 새 family 실패를 wrapper가 warning으로 넘기는 경우에도 source/selected/loaded 상태와 실패 원인을 필수 산출물로 남겨 '전체 성공이므로 exit 적용 성공' 오판을 막는다.

## 10. 구현 순서·완료조건

아래 `WP`는 설계 작업 번호다. authoritative recommendation/workorder ID가 아니며 새로운 live 실행 권한을 만들지 않는다. 달력 일정은 구현 승인 시 기존 daily owner의 Due/Slot/TimeWindow/Track으로 기록하며 데이터 성숙 완료일을 약속하지 않는다.

| 작업 | 선행 | 변경/산출물 | 종료조건 |
| --- | --- | --- | --- |
| WP0 계약 고정 | 구현 지시 | canonical child/외부 hash 연결, scope census, schema·risk 미결정 목록, 공식 API 검증 계획 | 역할/권한·단위·consumer 및 예상 지원률 확인. 빈 위험값으로 live 통과 불가 |
| WP1 원천 보완 | WP0 | fill/lot/target/exit epoch, event/후행 경로·gap 계측 | 자연 hook과 offline fixture 별도 검증, 보존식/중복0, 미완료·무표본 분리 |
| WP2 순수 조기청산 | WP0 | models/decision/reducer, time-progress+한 번 유예 | 경계 시각·source missing·restart·동일원천 runtime/replay 결정 일치 |
| WP3 장후 replay/gate | WP1+2 | turnover v2 child, 실제/CF·train/holdout·gate dispatch | source-only 후보/미달사유·baseline EV0·희소 floor 도달성·consumer 재검증 정합 |
| WP4 주문 전환 | WP2+protocol gate | SELL cancel/대사, owner intent·잔량·adapter 중재 | crash/late fill/중복/부분취소/원주문 successor 전수 회귀, 타 owner 영향0 |
| WP5 정책/생존성 | WP4 | schema migration, preflight/loader, polling/deadline, frozen carry·recovery | old baseline 동작 유지, 신규 무권한 주문0, active exit 조기 종료0 |
| WP6 trailing 후속 | WP1+2+4 | supported lot 일부 전환·high-water·gap·후행 replay | 전환구간 불가능 명시, cancel-race baseline fill, stop 단조성·수량 epoch 회귀 |
| WP7 자동화 연결 | WP3+5, 최초 envelope 승인 | trusted exit family, PREOPEN apply/receipt, summary/verifier/checklist | 당일 source→policy→owner dry fixture E2E; 범위 밖/날짜/hash/동일 stage 충돌 차단 |
| WP8 제한 적용 | WP7, 실행/배포 승인+경제성/실행준비 | 첫 한 scope의 `time_progress_exit` 신규 episode, 즉시 대사 | 실제 load/intent/cancel/fill/cost 확인, 오류 시 신규 선택 중지·잔량 관리 지속 |
| WP9 후속 비교 | WP6+8 및 해당 모드 승인 | trailing 단독/결합의 별도 정책 버전·R6 | 실제 버전별 EV/순이익·tail·빈도/자본효율 비훼손 근거; 자동 범위 밖 확대 금지 |

코드 PR/commit 분리는 `계약·계측`, `순수 로직·replay`, `gateway·상태`, `policy·생존성`, `trailing`, `자동화·승인`, `적용 receipt` 순서를 권장한다. 이 계획은 commit/push 명령이 아니다. 각 변경은 review→fix→재리뷰→targeted validation 후 다음 단계로 간다.

## 11. 회귀 테스트 매트릭스

| ID | 입력/반례 | 기대 결과 |
| --- | --- | --- |
| D01 | T_soft 직전/같음/직후, source weak vs missing | 시계 경계 일치, missing을 약세로 치환하지 않음 |
| D02 | 한 번 유예 후 반등·재약화, 재시작 | 유예 중복0, elapsed reset0, 종료 규칙 명시 |
| D03 | target-entry 0/음수, NaN/Inf, stale/crossed BBO, 수량 깊이 부족 | 명시적 invalid, 새 전환0 |
| D04 | target 몇 tick·비용 여유 없음, 취소 p95가 fast window 초과 | trailing 미지원/baseline, target/guard 자동 변경0 |
| D05 | 고점 갱신/되돌림, lot 잔량 변화, epoch 전환 | stop 비감소, future/타 lot 고점 혼입0 |
| O01 | cancel ACK만 성공, timeout/429/조회 continuation 미완료 | 해소 전 새 SELL0, cap/retry 상향0 |
| O02 | cancel 중 전량/부분 target fill; fill-before-ACK | 실제 잔량만 보존·정확한 terminal, 재매수0 |
| O03 | intent 저장/전송/ACK/registry bind/save 각각에서 crash | 조회 후 복구, unresolved 예약 보존, blind duplicate0 |
| O04 | 재제출 SELL 일부 체결·만료·응답 유실 | 살아 있는 주문과 새 주문 수량 겹침0 |
| O05 | 같은 symbol 타 owner/manual 수량·재사용 order no/다른 날짜 | 타 owner 취소/매도0, 잘못된 identity reject |
| O06 | target 재생성+scale-in+source EXIT+trailing 동시 조건 | 단일 intent 우선순위, 새 exposure와 중복 SELL0 |
| O07 | 합산 target의 runner 부분취소 지원 없음 | 지원불가·baseline; 전량 target 취소로 대체0 |
| P01 | 미등록/권한근거 없는 승인, hash/date/수치/범위 변조, schema spoof | 신규 정책 거절, legacy validator 회귀 유지 |
| P02 | prior-day 보유 + 오늘 다른 정책, 당일 정책 재발행 | 기존 frozen policy, consumed generation 불변 |
| P03 | 활성 trailing 중 policy expiry/feature OFF/WS 단절/서비스 종료 | 잔량 관리 책임 유지·recovery; generic 정상종결 금지 |
| E01 | 느린 HELD·manual exit·target touch뿐인 경로 | 연구 분모 보존, actual profit/null 분리, queue fill 과대평가0 |
| E02 | 기준 EV0/음수·희소 표본·rolling expiry·양수일만 유입 | 절대 uplift 유효, first gap·ETA 정확, floor 자체승인0 |
| E03 | train/holdout 시간 겹침·반복 leg/tick·mixed costs | purge/dedup/격리; actual-CF 합산0 |
| A01 | attribution 성공 뒤 approval 실패/child missing/old PASS | exit chain 실패·reason; stale 성공 재사용0 |
| A02 | same-date duplicate PREOPEN, partial publish, late cutoff | atomic/idempotent 또는 명시 실패; 다른 family 비훼손 |
| A03 | startup receipt만 있고 episode consumption 없음 | loaded/called 미검증을 applied/economic 성공으로 보고하지 않음 |

기존 회귀는 [widget trade](../../src/tests/test_widget_signal_auto_trade.py), [low-price](../../src/tests/test_low_price_two_leg.py), [turnover research](../../src/tests/test_machine_lifecycle_turnover_policy_research.py), [attribution](../../src/tests/test_machine_microstructure_attribution.py), [approval](../../src/tests/test_machine_microstructure_policy_approval.py), [checklist builder](../../src/tests/test_build_next_stage2_checklist.py)를 포함한다. 특히 기존 target 유지·source EXIT·ambiguous cancel·prior HELD·금지 preflight 테스트를 새 정책만의 예외와 baseline 보존 두 갈래로 확장한다.

구현 후 검증은 프로젝트 `.venv`의 해당 pytest/compile, wrapper 변경이면 `bash -n` 및 관련 wrapper 테스트, `git diff --check`다. 문서·checklist는 print-only parser를 실행한다. mock/회귀 검증 중 실계좌 주문·취소·Provider 호출·외부 sync는 하지 않는다.

## 12. 승인 전 미결정·handoff·계획 검증

연구·구현 대상은 사용자 지시에 따라 전체 owner/profile이다. 실전 활성화 전에 남은 결정은 (1) 실제 활성화 envelope의 scope·기간, (2) 시간/가격 손실·세션 경계 정책, (3) sell 가격/TTL/최종 잔량 처리, (4) runner leg/lot, (5) 경제성 평가창/N_min/허용 tail, (6) 실제 process 배포·복구 권한이다. 후보 수치는 자동 연구에서 제안하되 승인 수치로 가장하지 않는다. 이는 §3에 따라 비어 있으면 차단되는 activation 입력이며, 이미 승인된 범위 안에서 매일 별도 수동 승인을 반복 요구하는 설계가 아니다. 미완성 자연 source/owner adapter/PREOPEN 코드는 승인값 대기와 별도로 추적한다.

향후 원천/계획 수용은 [오늘 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`에 연결한다. 해당 항목의 source-only 권한은 유지한다. 실행 승인 시에만 필요한 구현·배포 단계를 현재 checklist에 이관하며 계획 번호를 producer native ID로 발명하지 않는다. 완료된 entry timing 상세검토는 새 exit 설계가 생겼다는 이유만으로 재개하지 않는다.

이번 작성에서는 baseline 문서·runtime 코드·운영 artifact를 수정하지 않는다. 향후 automation 구현에서 runbook/traceability/설치 계약 변경이 필요하면 사용자 승인 범위에 포함시켜 같이 검증한다. 외부 동기화는 실행하지 않으며 필요한 표준 사용자 명령은 [상위 제안서 §9](widget-episode-adaptive-exit-plan-2026-09-09.md#9-다음-액션과-이번-검토-완료-범위)에 한 번만 둔다.

계획 검증 범위는 파일/consumer 실재, 신규 위치 역할, 권한/정책/시간·수량 불변식, baseline 호환, state transition, checklist 중복 및 print-only parser다. 설계 검증을 코드 구현·실제 broker 품질·자연 수익 효과 완료로 보고하지 않는다.

문서 review/fix에서는 canonical child와 parent hash의 순환 참조 방지, 최초 canary와 R6 이후 자동 유지의 분리, 접수 ACK 성공 전이·API 전 durable 상태를 추가 명시했다. 링크와 기존 OPEN owner 1회 포함을 확인했고 print-only parser 및 `git diff --check`를 통과했다. 실제 코드 테스트와 broker/API 실행은 계획 작성 범위 밖이므로 수행하지 않았다. §3의 미결정 위험값과 신규 자연/경제성 acceptance는 완료 처리하지 않는다.
