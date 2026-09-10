# 진입 직전 악화 보류 구현·리뷰

작성: 2026-09-10 KST. 대상: [최종 구현안](../proposals/widget-episode-entry-adverse-flow-implementation-plan-2026-09-10.md)의 V1. 사용자 명시 구현·반복 리뷰 요청에 따른 개발 코드 변경이다. **배포·운영 정책 발행·재기동·실주문·장후 재생성은 실행하지 않았다.**

## 1. 판정과 구현 범위

`code_review_closed / deployment_pending / natural_unobserved / economics_unmeasured`. 아래 최종 검증 범위의 결함을 보완했으며, 현재 선택 배포/PID가 새 코드를 사용한다고 주장하지 않는다. `korstockscan-review-gate`에 따라 직접 계산→owner→gateway→원장→receipt→장후 consumer를 리뷰하고 발견한 결함을 수정·재검증했다.

| 구현 위치 | 실제 역할 |
| --- | --- |
| `src/trading/market/entry_adverse_flow.py` | 기존 fixed-price window 정규화/원천 검증 재사용, bid 하락·두 반창 SELL 우세·SELL 속도 비감소·bid 미회복의 AND 판정 |
| `src/trading/config/machine_entry_adverse_policy.py` | 기본 OFF, 정확한 단일 scope·기간·SHA256 pin 소비. 기존 timing baseline만 허용 |
| `src/trading/order/entry_adverse_guard.py` | T0 고정, checkpoint0/1/3/5초, 처리 지연1.5초/전체6.5초, terminal identity 보존, 전송 직전 veto |
| `src/trading/order/entry_adverse_owners.py` | 위젯/공유 two-leg owner adapter, 원 정책/신호 재검사, 원 owner 상태 저장·선택적 진단 journal |
| `src/trading/widget_auto_trade/engine.py` | 최초 ENTRY_BUY에만 연결. scale-in/SELL 제외, 미전송만 원 registry에서 해제, 기존 EXIT/복구 유지 |
| `src/trading/order/regular_two_leg_machine.py` | midday/afternoon/low-price 공유 two-leg 경로. 각 원10주 leg 별도 판단·제출, 첫 leg 뒤 악화된 두 번째 leg는 기다림 |
| 해당 widget/episode `gateway.py` 5개 | token 처리 뒤 `session.post` 직전 동기 hook. 외부 callback 없는 기본 경로·SELL/취소/read 불변 |
| `src/engine/monitoring/entry_adverse_flow_summary.py` 및 기존 attribution | 날짜별 journal의 hash/identity/분모 점검과 JSON/Markdown child 소비. 새 cron/정책 승격 producer 없음 |

별도 morning legacy machine에는 owner adapter를 연결하지 않았다. morning gateway의 공통 hook만 추가됐으며 그 사실을 morning 실전 보류 기능 가동으로 확대하지 않는다. main·기존 fixed/dynamic timing·기존 보조청산/목표 상향은 이번 새 entry 정책의 대상이 아니다.

## 2. 시간·원 권한·설계 보완

- 감시의 마지막 nominal 시점은 T0+5초, **새 전송 시작 절대 상한은 T0+6.5초**다. 원 signal/session deadline이 더 빠르면 원 조건이 우선한다. 이미 전송한 응답을 6.5초에 취소/재전송하지 않는다.
- 위젯 T0는 원 loop가 기존 신호를 진입 확인 단계에 처음 넘긴 `observed` 시각을 저장한다. snapshot의 시세/bar 시각을 원 owner의 매수 판단시각으로 가장하지 않는다. 동일 confirmation identity의 반복 loop·재시작은 저장한 T0를 재사용한다. 에피소드는 기존 `signal_features.signal_decision_at`을 사용하며 누락/naive clock은 새 현재시각으로 대체하지 않는다.
- 준비 시 원 정책 hash와 기존 timing hash를 고정하고, 마지막 검사에서 현재 신호·원 정책·pause·시장약세·세션/원 진입창을 다시 확인한다. CONTINUE는 추가 악화 veto 부재일 뿐 BUY 권한이 아니다. 기존 가격/수량/유동성/집행속도/원장 guard는 유지한다.
- 기존 설계의 “최신 메모리 view를 전달하는 no-I/O 검사”는 현재 gateway/collector 구조와 맞지 않아 **검증된 로컬 snapshot/정책 재읽기**로 구체화했다. 추가 broker/API 조회·token 발급·네트워크 polling은 없다. I/O·상태 저장 뒤 deadline을 다시 확인하며, 최신0B/0D receipt와 실제 window endpoint의 sequence/time도 대조한다. 이것은 raw WS callback 즉시 전송이나 네트워크 지연 제거가 아니다.
- 전송 직전 `TRANSPORT_STARTED`를 원 owner 상태에 먼저 저장한다. 그 뒤의 crash/모호한 wire 결과는 원 reconciler 소유이며 자동 재진입하지 않는다. hook이 발생시킨 `EntryNotSent`만 확정 미전송이다. 취소 API를 호출하지 않고 정확한 자기 예약만 기존 rejected transition으로 해제한다.
- 원 소스 소멸·정책 변경·deadline 종료·손상된 저장시계는 별도 SKIP다. 판정용 자료 부족은 남은 checkpoint까지만 대기하며, 같은 신호를 baseline에 몰래 재투입하지 않는다.

## 3. 리뷰 finding과 보완

| 확인한 위험 | 보완·직접 검증 |
| --- | --- |
| gateway 바깥 검사 후 대기 중 시장 악화 | 실제5개 gateway의 token 이후/전송 이전 hook 테스트. latest endpoint mismatch·owner/source/epoch/deadline 변동에서 wire0 |
| 같은 신호 재호출·재시작·두 번째 leg에서 시간 재설정 | 원 T0/terminal history 유지, 저장 clock/schema 손상 종료, leg별 독립 마지막 검사 |
| 상태 저장 중 원 진입창·정책 유효기간·source freshness 경과 | 원 deadline/정책 만료/0B·0D endpoint freshness 중 먼저 도래하는 상한을 저장 뒤 다시 확인. clock 역행도 전송0 |
| 비대상 episode에 활성 widget 정책의 새 원천 요구 전파 | 정확한 scope 미선택이면 원 경로를 그대로 통과. 대상 scope의 누락된 original signal time만 차단 |
| dynamic/fixed 및 원 정책 변경과의 충돌 | baseline 외 SKIP, timing/source owner policy hash 재대조. 기존 dynamic ADVERSE→REJECT 불변 |
| 미전송을 broker reject/ambiguous와 혼합 | 별도 EntryNotSent와 widget NOT_SENT, 원장 해제 실패는 fail-closed, 이미 보낸 leg 복구권한 불변 |
| 진단용 ask 잔량 결손을 새 entry gate로 사용 | fixed ask level/수량 진단 결손만 이 bid/trade 가설의 필수 gate에서 분리. 기존 공통 kernel/기존 guard는 수정하지 않음 |
| 로그 저장 실패로 이미 받은 주문응답 처리 중단 | 원 owner 상태가 안전성의 원본. 선택적 journal 오류는 `entry_adverse_flow_receipt_error`로 남기며 주문응답/보유관리 흐름을 끊지 않음 |
| 늦은 원 guard 거절·소스 소멸을 계속 pending으로 표시 | 원 거절 SKIP/신호 소멸 receipt, upstream 대기 중에도 widget 절대 deadline 만료 처리 |
| 잘못된 집계 분모/손상 receipt | `observed_guard_identity_count`로 guard intake와 최종 executable 기회를 구분. body hash·날짜·scope·action 검증, 오류 row 격리, 중복 identity 최신행 대사 |

진단 journal에 기록 실패가 있으면 해당 자연 관찰은 불완전하다. 집계의 보존식은 **읽은 유효 receipt 집합 내부**의 점검이며 collector/owner 전체 무손실의 증명이 아니다. 원 owner 상태/오류 로그까지 함께 대사해야 한다.

## 4. 자동 적용과 과도한 조건 여부

**최초 배포/활성화 전체가 자동화된 상태는 아니다. 승인된 pin을 읽고 신호마다 적용하는 runtime 소비는 구현했다.**

- 새 loader 입력은 `KORSTOCKSCAN_MACHINE_ENTRY_ADVERSE_POLICY_PATH`와 `KORSTOCKSCAN_MACHINE_ENTRY_ADVERSE_POLICY_SHA256`이다. 승인 작업이 설치한 정확한 단일 scope/period/pin만 소비한다. `approval_reference` 문자열은 승인 증거의 위치이지 문자열 자체가 새 권한을 만드는 것이 아니다.
- 기존 timing nightly 후보를 이 신규 alpha에 자동 승인하거나, PREOPEN env에 몰래 넣는 publisher는 추가하지 않았다. 최초 검토 commit/root·scope·effective 시점·rollback과 서비스별 pin 설치는 별도 배포 승인 작업이다. 승인된 지속 정책은 `valid_until=null`을 허용하며 매일 새 envelope/실체결/양수EV를 요구하지 않는다.
- 최초 canary gate는 코드/원천/시계/실제 hook/권한·safety/같은 stage 중복 여부다. **새 실체결을 모아야 실체결 기능을 켤 수 있는 순환 gate, 양수EV, 20일/모든 horizon/fixed20의 일괄 floor를 추가하지 않았다.** 기존 원 정책의 합법적인 guard는 유지한다.
- 한 완전한 checkpoint에서 악화가 해소되면 추가 연속 PASS 횟수를 요구하지 않는다. ask 감소·BUY 설명·refill을 모두 독립 신규 threshold로 붙이지 않았다. 반대로 입력 결손을 정상 BUY로 허용하지 않는다.
- 첫5거래일은 초기 review window 제안이며 자동승격/확대·강제 만료·충분표본 판정이 아니다. 새 threshold 자동최적화와 실전 종목 확대는 없다.

22:10 KST 이후 읽기 전용 확인에서 별도 machine manifest는 `machine-profit-stagnation-20260911`/`273807e3767bc92cd89cd0394e8aa374679795c6`, main selector는 `unified-runtime-20260910`/`b665e0a3abdff1abdf6902d3fc39af9df6591f64`였다. 검사한 deploy/systemd 파일에서 새 adverse pin 설정을 찾지 못했다. 이는 선택 원장/설치 파일 점검이며 전체 현재 PID 환경 검증이 아니다. 이번 세션은 두 원장/서비스/PID를 변경하지 않았다. **9/11에 새 entry 보류가 자동 가동된다고 보고하지 않는다.**

## 5. 목표·기대효과와 남은 경제성

목표는 “비용을 차감하고 작은 수익을 빈번하게”이며, 본 구현은 그 중 **하락·매도 우세 중 불리한 진입을 잠깐 보류하는 한 축**이다. 손실 억제나 주문 수 감소 자체가 성공은 아니다. 원 target·수량·청산 가격과 비용 계약을 바꾸지 않았다.

확인한 기계적 효과는 합성 입력에서 악화 시 전송0, 1초 뒤 회복 시 기존 주문1회, 최종 악화/결손 시 신호 종료, 첫 leg 후 악화 시 두 번째 leg 미전송이다. 비용 후 순이익 증가율이나 실제 성공률은 측정하지 않았다. 예상 이익은 불리한 체결/자본 점유 감소이며, 반대 위험은 급반등 누락·진입가격 악화·소스 결손에 의한 참여 감소다.

새 child는 `대기 / 미전송 terminal / 전송 시작`과 order/intent 연결을 제공한다. 전송 시작은 accepted/full-fill이 아니다. 실제 체결·partial/full·terminal·비용은 기존 widget/episode lifecycle owner의 원천과 exact order/leg를 대사한다. **새 child 자체는 경제성 추정기나 자동 정책 선정기가 아니며 비용/순익/EV는 null이다.** 기존 timing 4군 연구의 새 완료 arm으로 합산하지 않는다.

자연 평가에서는 같은 owner/symbol/profile/venue/session·원 signal/exit/비용 계약의 baseline/canary version을 분리하고, 비용 후 EV·순익/일을 우선해 양수 terminal 빈도·유효 참여·미진입 반등 기회·tail·자본시간을 함께 판정한다. 비무작위 전후 비교의 국면 혼입, source gap·미성숙/미대사 비용과 부분체결은 별도 표시한다. 무표본/부분평균을 전체EV0·성공으로 바꾸지 않는다.

## 6. 검증과 실행 인계

- 최종 targeted validation: **676 PASS / 19.92초**. 새3개 테스트 파일63 cases + widget/삼성/low-price·공통 kernel·attribution/timing 기존 회귀613 cases. pytest 대상은 `test_entry_adverse_flow`, `test_entry_adverse_owners`, `test_entry_adverse_handoff`, `test_widget_signal_auto_trade`, `test_widget_auto_trade_policy`, `test_samsung_morning_one_share`, `test_samsung_midday_one_share`, `test_samsung_afternoon_one_share`, `test_low_price_two_leg`, `test_machine_confirmation_window`, `test_machine_microstructure_attribution`, `test_machine_entry_timing_tuning`이다. 합성 fixture/가짜 transport/임시 출력의 테스트이며 자연 경제성 증거가 아니다.
- 새 모듈 F-rule 정적 점검, 관련 compile, `git diff --check` 통과. print-only parser exit0/40개, 기존 lifecycle owner가9/10 checklist에서 정확히1개 파싱됨을 확인했다. 문서 직접 로컬 링크도 확인했다. 최종 문서 보완 뒤 parser/공백과 새63 cases도 재검증 통과했다(63 PASS/1.64초). 이 범위 재리뷰의 unresolved finding0이며 저장소 전체/병행 변경/최종 배포 commit에 대한 finding0은 아니다. 실주문·provider 호출·고비용 canonical report 재생성은 하지 않았다.
- Kiwoom 공식 repository HEAD를 변경 전 확인하고, `2026-09-10T22:10:12+09:00`에 재확인했다: `234560d213acd8871ae344b5481aecd2f30287fa`. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 kt10000, Postman PRD/MOCK 요청을 읽었다. 해당 tree에는 `kiwoom_docs`가 없었다. POST `/api/dostk/ordr`, api-id/Bearer/continuation, 수량/가격/route·주문종류와 ord_no 응답 계약을 대사했다. 이번 변경은 전송 전 veto만 추가하며 protocol·인증·retry/capacity는 바꾸지 않았다.
- 현재 후속은 [9/10 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md)의 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`이다. 검토 코드 묶음/배포 승인→원천/같은 stage 정책 점검→별도 machine 배포/pin/PID→자연 receipt/비용 후 경제성을 분리해 남긴다. OPEN을 닫거나 미래 거래일의 기동을 앞당기지 않는다.
- 공유 workspace에는 병행 사용자 변경이 있다. 배포 시 이 작업과 무관한 adaptive exit/target-ratchet/main 변경을 일괄 복사하지 않고 검토 변경집합과 의존성을 별도로 고정해야 한다. 이 receipt는 현재 workspace 테스트 근거이지 최종 배포 commit 검증서가 아니다.

## Subsequent approved deployment — 2026-09-10 23:53 KST

The user explicitly authorized deployment and all existing widget/episode scopes. The [final review and deployment receipt](2026-09-10-approved-additions-deployment.md) supersedes earlier deployment-pending or single-scope statements in this historical review. Frozen code f9d53a9a, widget PID2651657, all nine service/preflight paths and policy pins are verified. New signals/entries from September11 are eligible; actual transitions and economics remain separate natural acceptance.
