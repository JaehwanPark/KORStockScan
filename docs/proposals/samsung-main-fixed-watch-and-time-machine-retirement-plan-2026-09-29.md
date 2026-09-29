# 삼성전자 Main 고정감시 이관 및 시간대별 기계 퇴역 구현계획 — 2026-09-29

상태: **작업본 구현·회귀 검증 완료, 운영 전환 대기**. 이 문서는 `005930`을 스캐너와 독립된 Main 고정감시 종목으로 편입하고, 별도 오전·점심·오후 삼성전자 기계의 신규 진입 기능을 대체하는 작업 범위를 정한다. 이번 구현은 실주문, 서비스 중단, 릴리스 선택 또는 재기동을 실행하지 않았다. [현행 정책](../plan-korStockScanPerformanceOptimization.rebase.md) §5·§7과 [오늘 실행 목록](../checklists/2026-09-29-stage2-todo-checklist.md)의 소유권·안전 경계를 따른다.

## 결정과 현재 근거

1. **구현 위치:** 별도 코드베이스·프로세스·주문 소유자를 만들지 않는다. 고정감시의 선언·동일 종목 중복 방지·세션 갱신은 `src/engine/scalping/`의 역할로 두고, Main 런타임 연결은 [`kiwoom_sniper_v2.py`](../../src/engine/kiwoom_sniper_v2.py), 실제 WATCHING 평가·주문은 기존 [`sniper_state_handlers.py`](../../src/engine/sniper_state_handlers.py)를 사용한다. `src/engine` 루트에는 새 모듈을 만들지 않는다. 삼성 전용 진입 점수나 1주 주문 규칙을 Main에 이식하지 않는다.
2. **이관 지점:** 제로베이스의 [`handle_zero_base_machine_enter`](../../src/engine/kiwoom_sniper_v2.py)는 짧은 probe의 `ENTER_NOW`, 출처 SHA, 5초 시계가 있어야 WATCHING에 편입한다. 고정감시는 이 함수를 호출하거나 가짜 `ZERO_BASE_DISCOVERY` 결과를 만들지 않는다. `005930`의 고정 편입 → 실제 WS 수신·웜업 → Main WATCHING의 기계 `BLOCK|RECHECK|ENTER_NOW` → `ENTER_NOW`에서만 compact 보조판정 → 기존 예산·가격·주문·보유·청산 경로로 흐른다.
3. **현재 충돌:** Main의 SCALPING 감시 기본 상한은 16이고 모든 SCALPING WATCHING 행이 FIFO·TTL·초과 슬롯 후보가 된다. 스캐너 편입과 재시작 복원은 `scanner_promotion_id`를 기대한다. 별도 [WS 기본 pin](../../src/engine/kiwoom_websocket.py)은 `005930_AL`의 위젯 읽기 전용 관측이며 Main 진입 권한이나 프리마켓 `_NX` 편입을 만들지 않는다. 고정감시를 스캐너로 가장하거나 pin만 재사용해서는 목표가 달성되지 않는다.
4. **실행 중인 퇴역 대상:** `src/trading/samsung_morning_one_share/`, `samsung_midday_one_share/`, `samsung_afternoon_one_share/`는 같은 저장소의 독립 서비스다. 9/29 확인 시 세 서비스는 `inactive`, `MainPID=0`이었으나 오전·점심·오후 기동 타이머와 점심·오후 사전검사 타이머는 활성이고 다음 영업일 실행이 예약돼 있었다. 세 state 파일은 `NO_TRADE`, 수량 0, 대기 confirmation 없음이었지만, 이는 전환 시점의 브로커·원장 대사를 대신하지 않는다.
5. **소유권:** 9/29 `005930` exact-date 소유권은 `COEXIST_ENTRY_ENABLED`이며 `episode`, `main_scalping`, `manual_operator`, `widget_auto_trade`를 허용한다. [`evaluate_main_bot_control_exclusion`](../../src/engine/risk/manual_control_exclusion.py)은 `machine_owner_scope` 호환 표지만 exact-date 정책으로 대체하며, 운영자 수동 veto와 자동 안전 제외는 계속 우선한다. `episode`를 무조건 제거하면 다른 episode 소유권에도 영향을 줄 수 있으므로 대상 세 서비스의 신규 BUY를 먼저 끊고 실제 005930 owner별 잔여 주문을 대사한다.

### 기능 대체의 정확한 의미

| 기존 시간대별 서비스 | 이관 후 Main 소유 |
| --- | --- |
| 오전·점심·오후 예약 기동과 독립된 진입 조건 | 활성 프리·정규·통합 애프터 세션의 고정감시에서 Main 기계가 판정. 예약 시각 자체는 매수 신호가 아니며 Main의 기존 매수 가능 시간은 유지 |
| 서비스별 1주 명칭, 독립 episode·leg 수량과 가격 | Main의 현행 초기 수량·분할·가격·예산 소유자가 결정. 고정 1주나 과거 두 leg 설정을 이식하지 않음 |
| 각 서비스의 독립 BUY 및 미체결 복원 | 신규 BUY는 Main 주문 경로 하나. 기존 서비스 주문·보유는 원래 owner의 취소·체결·SELL 복원으로 terminal까지 정산하고 Main 포지션으로 자동 전환하지 않음 |
| 삼성 전용 entry tuning 후보와 사전검사 | 신규 삼성 전용 후보 생산·PREOPEN 적용 중단. 신규 Main 판정은 Main 기계/장후 기회비용 모집단에 정확한 `watch_origin`으로 편입 |

## 구현 계약

### A. 고정 후보와 상태

- 선언은 우선 `005930` 한 종목만 허용하며 별도의 명시적 enable 값은 **기본 OFF**로 둔다. 등록의 근거는 `watch_origin=MAIN_FIXED_WATCH`, 날짜·코드·세션·route를 포함한 `watch_admission_id`와 `watch_generation_id`로 보존한다. 스캐너 `claim`, `promotion_id`, probe `ENTER_NOW` 또는 그 SHA를 합성하지 않는다. DB `RecommendationHistory`와 런타임·이벤트·장후 캡처에 원래의 출처가 같은 식별자로 남아야 한다. 기존 `position_tag=SCANNER`가 WATCHING 기술 분기에서 필요한 경우에도 업무 출처는 `watch_origin`으로 분리하고, 소비자가 이를 스캐너 성과 분모로 집계하지 않도록 수정한다.
- Main 시작·재기동·영업 세션 전환·보유 종료 후에는 먼저 동일 코드의 DB/메모리 WATCHING, BUY_ORDERED, HOLDING, SELL_ORDERED, 브로커 미결, owner custody를 대사한다. 정확히 하나의 활성 감시 행만 만들고 동일 세대 재시도는 idempotent하게 처리한다. 기존 주문·보유·불명확한 수량이 있으면 새 WATCHING/BUY를 보류하고 청산·복원 소유권은 유지한다. DB 임시 기록, 메모리 편입, WS 등록이 실패하면 한쪽만 활성인 행을 복원 또는 terminal 처리하는 영수증을 남긴다.
- `BLOCK/RECHECK` 및 원천 결손은 신규 BUY가 아니다. 감시 자격은 유지하되 기계 재평가 시도마다 별도 ID를 남긴다. `ENTER_NOW` 후 주문되지 않은 경우도 실제 사유를 기록한다. 체결 시 고정 WATCHING은 HOLDING으로 전이하고 빈 감시 슬롯을 반환한다. 이후 재편입은 기존 동일 종목·쿨다운·소유권·주문 가드와 새 세션 원천을 다시 통과해야 한다.

### B. WS·세션·자원

- 프리마켓은 정확한 `_NX` 시장자료와 해당 진입 route, 정규장과 통합 애프터마켓은 `_AL` 통합 시장자료와 SOR 주문 route를 사용한다. 현재 [`_scanner_runtime_ws_item`](../../src/engine/kiwoom_sniper_v2.py)의 suffix 변환 계약과 해당 세션 판정을 공유하되, 세션 전환 전후 자료를 섞지 않는다. 각 전환에서 이전 item의 잔여 구독 소유자와 신규 item 등록·첫 수신을 대사한다. WS 위젯 pin과 Main 감시가 같은 `_AL` item을 쓰면 실제 REG는 중복하지 않고 소유자 참조를 별도로 보존한다. 위젯만 남아 있으면 Main이 REMOVE를 보내지 않는다.
- 첫 평가 전 해당 세션 item을 **최소 10초 등록 상태로 유지**하고, 그 이후에도 새 0B/0D·체결 방향·가격의 기계 입력 조건을 충족할 때까지 기다린다. 이미 위젯이 `_AL`을 구독 중이어도 Main 고정감시 편입·세션 전환 전의 수신만으로 웜업을 완료했다고 보지 않는다. 기존 Main의 원천 신선도와 hard guard를 적용하며 `route_snapshot_missing` 또는 체결 부족을 임의의 `BLOCK`·0값으로 바꾸지 않는다. 거래가 뜸한 프리·애프터마켓에도 감시 자격은 유지하고 수신 상태를 계측한다. 감시가 상시라는 이유로 주문 직전 신선도, 조회 주기 또는 API 제한을 완화하지 않는다.
- WATCHING 상한의 **유효값 안에 1칸을 예약**한다. 기본 16이면 고정감시 1 + 회전 감시 최대 15다. 동적 cap이 줄어도 총합을 초과하지 않는다. 고정감시는 스캐너 FIFO·TTL·`_scanner_watch_eviction_decision_*`·scheduler boot TTL의 퇴출 대상에서 분리한다. 이를 위해 감시 출처별 공통 cap 계산과 일반 스캐너 overflow 후보 목록을 명시적으로 나누고, 고정감시가 보유·미결 주문을 밀어내거나 다른 종목의 보호 감시를 무조건 축출하지 못하게 한다. 현재 상한이 가득 찼을 때 초기 편입 처리와 다음 빈 슬롯 대기 영수증을 정한다.
- 현재 위젯 읽기 전용 pin은 유지 여부를 별도로 판단한다. 고정감시 enable만으로 pin의 관측 목적이 주문 권한으로 승격되지 않으며, 동일 item REG/REMOVE와 transport 재연결 시 실제 등록 수·수신 지연·실패율을 측정한다.

### C. 소유권·시간대별 기계 퇴역

1. **전환 전 동결:** 두 시장의 005930 잔고·미결 주문, 세 기계와 오전 reentry/manual-addon state, owner registry, Main·widget·다른 episode state를 주문번호·수량으로 대사한다. 미결·보유가 있으면 기존 SELL/취소·체결 복원에 필요한 최소 호환 경로를 terminal까지 유지하고 해당 owner의 신규 BUY는 차단한다. 수동·위젯 소유권은 사용자 요청 대상이 아니므로 유지하되, 같은 코드에 서로 다른 owner의 새 주문이 겹치지 않게 registry guard를 검증한다.
2. **신규 진입 퇴역:** 오전·점심·오후 서비스와 preflight의 신규 BUY 진입을 중단한다. 활성 timer, drop-in, 독립 immutable release의 실제 `ExecStart`/`WorkingDirectory`를 대조해 재부팅·다음날에도 다시 살아나지 않도록 systemd timer/service·설치/제거 스크립트·[`run_symbol_owner_policy_auto_apply.sh`](../../deploy/run_symbol_owner_policy_auto_apply.sh)의 정지·복원 목록을 정리한다. 8월 수동 addon의 비활성 unit도 신규 BUY 재활성화 경로가 없게 점검한다. 운영 원장/브로커 custody가 남은 코드는 호환 read/exit 경로만 유지한다.
3. **소유 정책:** 신규 Main 진입을 열기 직전 exact-date owner policy와 activation receipt를 갱신하고 실제 Main PID 소비를 검증한다. 기존 `005930 # machine_owner_scope` 표지를 조용히 삭제하거나 수동 veto를 무시하지 않는다. 세 기계의 독립 진입 권한 제거와 `episode` 전체 owner 제거는 다르므로, 005930의 다른 episode 소유 여부를 확인한 뒤 필요한 최소 정책 변경만 한다. `COEXIST_EXIT_ONLY` 롤백은 전체 Main 신규 BUY도 막는다는 점을 전환 계획에 명시한다.
4. **장후·PREOPEN 퇴역:** [`run_threshold_cycle_postclose.sh`](../../deploy/run_threshold_cycle_postclose.sh)의 `samsung_machine_entry_tuning` 기본 생산, 삼성 전용 [`samsung_machine_entry_policy_apply`](../../src/engine/automation/samsung_machine_entry_policy_apply.py)·preflight, [`runtime_approval_summary`](../../src/engine/runtime_approval_summary.py)의 `machine_entry` family, [`postclose_recommendation_intake`](../../src/engine/automation/postclose_recommendation_intake.py)와 관련 verifier/marker 소비를 전환 날짜 이후 `retired/not_applicable`로 정리한다. [`low_price_two_leg_policy_apply`](../../src/engine/automation/low_price_two_leg_policy_apply.py)와 [`machine_entry_timing_tuning`](../../src/engine/automation/machine_entry_timing_tuning.py)의 삼성 candidate 동일 단계 충돌 판정은 퇴역 날짜 이후의 **신규** 삼성 후보만 제외하고 과거 후보 검증·감사는 유지한다. Main 고정감시 판정은 기존 Main 기계/미진입 후행경로에 출처별로 포함하며, 과거 독립 기계 성과를 Main 수익으로 합산하지 않는다.
5. **코드 제거:** 세 `src/trading/samsung_*_one_share/`의 신규 진입 서비스·기계·preflight, 전용 systemd/wrapper와 테스트를 소비자 참조 조사 후 제거한다. terminal이 남은 주문·보유의 파서/복원/청산은 남기고, 완전 정산 영수증 뒤 호환 경로를 제거한다. `widget`, 공용 owner registry, 타 종목 episode, 공용 `machine_entry_timing_tuning`, 기록된 raw/state/report 및 독립 rollback 릴리스는 범위 밖이다. [운영 runbook](../time-based-operations-runbook.md)과 Plan Rebase의 삼성 현재 상태는 구현 시 명시적으로 수정한다.

## 작업 순서와 수용 시험

| 순서 | 구현·검증 작업 | 완료 영수증 |
| --- | --- | --- |
| 1 | 전환 시점 owner·브로커·세 기계의 BUY/SELL/pending 대사; 정확한 퇴역·보존 파일 목록 확정 | 코드/주문번호/잔량/소유자별 대사, 미해결 custody 별도 보류 |
| 2 | Main의 고정감시 선언·DB 원자 편입·재시작 복원·세션 갱신·WS 소유 참조·1칸 cap 구현 | 스캐너 입력 없이 005930 한 건만 WATCHING, 중복/재기동/세션전환/상한 회귀 |
| 3 | Main 기계 판정 및 장후 출처 결속 | `BLOCK/RECHECK/ENTER_NOW/source_gap`별 캡처·후행 자료, 스캐너 분모 비혼합, 주문 가드 회귀 |
| 4 | 독립 세 기계 신규 BUY/타이머/PREOPEN·장후 family 퇴역, 과거 custody 보존 | 새 기동·신규 주문=0; 과거 미결/SELL 복원·정산; 다음 장후 retired 영수증 |
| 5 | 하나의 불변 릴리스에서 선택·Main 재기동·systemd 적용 | selector와 실제 PID cwd/env/policy SHA 일치, 활성 timer 목록, 실제 WS item/route·등록 수, 감시 1칸 확인 |
| 6 | 다음 자연 거래와 장후 수용 | 세션별 기계 도달·결손/지연·제출/미제출·체결/terminal·비용 후 성과를 구분해 기록 |

단위·통합 회귀에는 `src/tests/test_scalping_watch_budget.py`, `test_watching_scalping.py`, scanner scheduler/boot·owner coexistence·symbol owner auto-apply, 세 삼성 서비스 퇴역·threshold wrapper·postclose consumer 계약을 포함한다. 성공/실패를 명확히 구분한다: 고정감시 편입 성공은 BUY 또는 수익 증거가 아니고, `BLOCK/RECHECK`의 후행 원천이 없으면 `source_gap`이다. 문서 및 shell 수정은 링크/owner/authority 점검, print-only checklist parser, `bash -n`, 해당 wrapper 테스트로 닫는다. Kiwoom REG/REMOVE·reconnect·WS parser를 수정할 때는 구현 직전 공식 Kiwoom 저장소 revision·관련 문서·로컬 계약을 확인하고 SHA·열람 시각·파일을 리뷰 증거에 남긴다.

**롤백:** Main 고정감시 enable만 OFF로 되돌리고 기존 세 기계의 신규 BUY는 계속 OFF로 둔다. 과거 custody의 복원·청산 경로는 유지한다. Main 퇴행 때문에 옛 서비스 timer를 자동 재활성화하지 않는다. 별도 신규 진입 재개는 owner 정책·원장·브로커와 다음날 release/PID를 다시 검증한 뒤 결정한다.

## 2026-09-29 구현·리뷰 영수증

- `src/engine/scalping/main_fixed_watch.py`가 기본 OFF의 단일 고정감시 선언, KRX/NXT 잔고·미체결 및 owner 미결 검증, DB/메모리 동일 종목 충돌·상한, 세션별 admission, 정확한 WS item과 웜업을 소유한다. Main은 기존 WATCHING 기계/주문 경로를 사용하고 `watch_origin`, admission/generation ID를 이벤트·장후 기계 case에 전달한다. 스캐너 promotion ID를 합성하지 않는다.
- 세 독립 서비스와 오전 수동 addon의 신규 BUY gateway는 `RETIRED_NEW_BUY`로 차단하고 SELL·취소·기존 state 파서는 유지한다. 신규 삼성 전용 장후 후보·PREOPEN 적용은 9/30 이후 퇴역한다. 설치 스크립트는 재활성화를 거절하며 timer 중지 스크립트는 별도 운영 전환용으로 준비했다.
- 코드리뷰에서 위젯 `_AL` pin이 이미 있는 상태의 프리마켓 `_NX` REG 누락, 퇴역 장후 family 집계 예외, 불명확한 미체결 side/수량의 평탄 오판, 고정감시에 대한 불필요한 스캐너 promotion 파일 재탐색, OFF 복귀 시 미확인 custody 조기 만료, 실제 수동 addon state 구조와 퇴역 스크립트의 불일치를 찾아 보완했다. 마지막 표적 회귀는 기계 trace/판정·감시·WS·브로커 스냅샷 574건, 삼성 서비스·장후·wrapper 204건, Python compile, `bash -n`, `git diff --check`, checklist print-only parser를 통과했다.
- Kiwoom 공식 저장소 `Kiwoom-Securities/Kiwoom-REST-API` revision `953e5dbff123f437ab4d11a78a95191a685eb51f`를 2026-09-29 16:00 KST에 조회했다. `kiwoom/realtime/packets.py`, `kiwoom/core/ws_client.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`, Postman을 확인했다. 그 revision의 `kiwoom_docs`는 부재했다. 정확한 `_NX`/`_AL` 선택은 로컬 세션·WS item 계약으로 검증하고, 공식 REG/REMOVE 메시지와 교차 확인했다.
- 운영 대기: 16:33 KST 읽기 전용 확인에서 기존 오전·점심·오후 서비스는 inactive이고 해당 state는 `NO_TRADE`/`NO_FILL`, 잔여 수량 0이지만 다음날 기동 timer 5개는 활성이다. 수동 addon timer는 비활성이다. **현재 브로커/owner 실시간 대사, timer 적용, 불변 릴리스 선택, Main PID 소비, 자연 장중·장후 수익 증거는 완료되지 않았다.** 기존 `strategy_owner_replay`의 scanner promotion 필수 계약에 고정감시 후행 비용행이 연결되는지는 자연 자료로 별도 검증해야 하며, 결손이면 성과 0으로 치환하지 않는다.
- 통합 재리뷰: 날짜를 넘긴 미체결 고정감시가 예전 메모리 ID와 신규 DB ID를 혼합하지 않도록 이전 행을 `EXPIRED`로 보존하고 새 날짜 행으로 편입한다. 계좌 스냅샷의 동일 코드 중복 잔고는 평탄으로 간주하지 않는다. 16:5x KST 읽기 전용 `kt00005`/`ka10075` 확인에서 KRX·NXT 조회와 미체결 응답이 성공했고, `005930` 잔고·미체결 0, 미해결 owner intent 0이었다. 공식 Kiwoom HEAD는 재조회 시에도 `953e5dbff123f437ab4d11a78a95191a685eb51f`였다. 이번 통합 표적 회귀 2,205건과 추가 620건, Python compile·셸 문법·diff 검사·문서 parser가 통과했다. 실제 timer·release·PID 영수증은 운영 전환 뒤 별도로 기록한다.
- 첫 기동 재리뷰: 17:00 KST `d28b4636` 선택·PID `1435317`·고정감시 enable 및 구형 timer 퇴역은 확인됐지만, 실제 고정감시 편입은 `same_symbol_db_conflict`로 보류됐다. 읽기 전용 DB 조회에서 `005930`의 3~6월 무체결 `WATCHING` 15행이 발견됐다. 이들은 당일 감시·보유·미결 주문이 아니므로 과거 행은 그대로 보존하고, 당일 `WATCHING` 및 날짜와 무관한 실제 주문·보유 상태만 충돌시키도록 수정했다. 생산 DB와 동일한 조회의 당일 충돌 건수는 0이며, 역사 행 보존·당일 입장 회귀를 추가했다. 후속 불변 릴리스와 실제 Main 편입은 별도 수용 영수증으로 확인한다.
