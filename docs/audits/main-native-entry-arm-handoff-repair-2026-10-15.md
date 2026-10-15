# Native entry arm 완료 연결 수리 — 2026-10-15

## 범위와 원인

초기 구현 세션은 사용자 요청에 따른 코드 수리·반복 리뷰·표적 검증만 수행했다. 후속 사용자의 `86f789693 코드리뷰하고 배포 및 재기동` 지시에 따른 재리뷰와 실행은 아래 후속 절에 기록한다. 기준은 통합본 `3d43544e3bf2e6c3a326f924f373ac9337f6cb84`이며, 기존 재시작 signal epoch/내부 오류 분류 수리를 포함한다.

10:53:45 주성엔지니어링 요청 `analyze_target:036930:1792029225578:2f5acaa4`는 HTTP 경계에서 607ms가 남아 응답 처리 예약 250ms를 제외한 예산이 357ms였다. 첫 큐 방문→native 확보가 3035ms였다. 이전 signal 507의 PASS가 `real_weak_pullback_entry_block`으로 주문 없이 반환된 뒤에도 `entry_armed`가 남아 signal 509의 새 평가 경로를 가로막았다. 이후 source-quality 차단과 Main 방문 대기도 존재하므로 전체 지연을 arm 하나로 단정하지 않는다. 원 인과 자료는 `tmp/entry-timeout-105345-20261015/diagnosis.json`에 보존한다.

해당 timeout의 outbox는 `transmission_uncertain`이다. 기존 provider 호출/예약 초기화, 재전송, 원 native 마감 연장은 하지 않는다. kt00011 원 요청은 약 73ms에 성공했고 이번 수리 대상은 아니다.

## 구현과 보완 리뷰

- arm을 원 async 요청·평가·trace·native signal·PID/start ticks에 결속한다. 다른 요청의 완료가 후속 arm을 지울 수 없다. 재기동 또는 문맥 누락으로 결속이 유효하지 않은 arm은 과거 PASS의 재사용 권한이 되지 않는다.
- Main 완료 finally에서 같은 요청의 submit 함수가 `returned_false`이고 물리 주문 호출 0임을 확인한 경우에만 arm을 정리한다. 기존 완료→대기 native 재방문 연결이 다음 신호를 원래 5초 마감으로 확보한다.
- 주문 attempt·broker accepted·보유 수량·미체결 주문·initial quantity bundle·양수 지연 진입 의도·예외·불명확한 반환은 기존 custody를 보존한다. 확인과 arm 제거는 같은 ENTRY_LOCK에서 수행한다. 정리 예외가 나도 기존 async 정리/ack/revisit은 진행한다.
- 1차 리뷰에서 arm만 지우면 cooldown 중 저장된 BUY/PASS를 다시 사용할 수 있는 경로를 발견했다. 해당 평가의 종료 표시를 추가해 새 native가 없을 때 재사용을 막았다. 원 PASS와 원 마감은 그대로 보존하며, 후속 native의 식별자·마감은 새 원천에서만 온다.
- 후속 리뷰에서 복원된 arm의 deadline 누락·0/NaN·request/evaluation/trace 결속 불일치도 검사하도록 보완했다. 마감 조회 전에 유효성을 확인해 예외나 20초 arm TTL로의 잘못된 재사용을 방지한다. 손상된 원 근거를 새 마감으로 덮어쓰지 않는다.
- quote/source/account/order/quantity/cooldown/hard safety, 정책 수치, provider timeout/회로, WS/API 계약과 원천 생산자는 변경하지 않는다. 레거시 non-native arm 동작은 유지한다.

## 재기동 인계 계약

`sniper_state_handlers.py`는 기존 pre-submit delay/stop/holding 코드 계약에 포함된다. 정책 원본과 PREOPEN 영수증을 재작성하는 대신 `intraday_release_handoff.REVIEWED_NATIVE_ARM_COMPLETION_SOURCES`에 검토된 파일의 정확한 전후 SHA만 등록한다. 전 SHA는 원 PREOPEN `3d644d8495a2c257784d96cd01df831bfb6022f8`의 `b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500`, 86f789693의 후 SHA는 `930921a6e3b77fa1e4342d46f29e117cdf18301a8f24220736ebdb384e97af8c`였고, 아래 잠금 경합 보완 후 배포 후보에 등록한 후 SHA는 `93285e4678038c07e56b34187dc4a9b4ba7b6ee70c380a32f18eaf622fd57335`이다. 다른 코드 변경, 원본 digest 변경, dirty candidate/verifier는 계속 거절한다.

배포 세션에서는 최종 통합 commit으로 candidate delay/stop/holding 검증을 다시 수행하고, 원 native family/auxiliary 등록·PREOPEN/source 해시를 유지한 기존 ordered handoff 절차를 사용한다. 현재 코드 검증을 새 PID 소비로 대체하지 않는다. 누락/변경 원천은 그대로 실패시키며 새 원천이나 성공 영수증을 합성하지 않는다.

## 검증과 남은 수용

- Main completion→submit observer→arm 정리→첫 native 재방문 통합 시험과 보호 경계, 재기동 식별자 누락/불일치, source 부재 때 PASS 재사용 금지를 검증했다.
- 진입/async bridge/기존 scale-in 회귀와 정책/기동/async coordinator 계약 총 2,402개 통과(29.50초). 컴파일 5개·diff·print-only parser가 통과했고 기존 자연 수용 owner가 1개임을 확인했다. 검토 범위의 미해결 결함은 없다.
- 실제 동결 정책의 candidate delay/stop/holding 검증, bootstrap 원천 해시 대조, 기존 선택본의 native 원천 838개 검증이 통과했다. native 계약 모듈 33개는 후보와 기존 선택본이 동일하다. 최종 commit 읽기 전용 대조·테스트·소스 SHA 증거는 `/home/ubuntu/KORStockScan/tmp/entry-arm-native-handoff-20261015/`에 보존한다. selector/bootstrap/current pointer는 변경하지 않는다. 새 후보의 handoff 영수증 발행·실제 PID 로딩은 배포 세션에서 수행한다.
- 원천 결손·stale·source-quality 차단과 외부 응답시간 때문에 발생할 수 있는 모든 timeout의 제거를 주장하지 않는다. 실제 배포·재기동·자연 provider 응답·주문/체결·비용 후 경제성은 미수행이며 다음 자연 수용은 당일 checklist `AuxiliaryCircuitRecoveryRepair1012`가 소유한다.


## 11:37 사용자 승인 후 독립 재리뷰

현재 선택3d43544e3/PID1743907/start9268703를 확인하고 기존 통합 작업 트리의 b861a80e5에86f789693을 병합했다. 다른 세션의 작업본과 공유 작업공간 변경은 보존하며 동결된 checklist는 기존 ordered 배포의 drain 이후에만 게시한다.

추가 발견 P2: `_get_live_entry_arm`의 무효 소유권 판정은 잠금 밖에서, 제거는 잠금 안에서 실행됐다. 그 사이 같은 ENTRY_LOCK의 후속 writer가 소유권/마감을 교체하면 유효한 후속 arm을 지울 수 있었다. 후속 writer가 먼저 잠금을 얻는 순서를 고정한 회귀시험은 원 커밋에서 실패했다. 판정·원 평가 종료 표기·arm 제거를 동일 잠금으로 묶어 보완했다. 잠금 안에서 provider/파일 I/O/알림을 수행하지 않고 기존 reentrant ENTRY_LOCK을 재사용한다. 무효 원천 복구나 deadline 갱신, 새로운 provider/주문 권한은 없다. 첫 재검증의 native 완료/async bridge138개가 통과했다.

최종 배포 전 새 코드 SHA를 기존 정확한 전후 source pair에 결속하고 candidate delay/stop/holding, active-native 코드 handoff를 검증한다. 원 입력/정책/예약/transmission_uncertain은 그대로 보존한다. 다음 자연 신호의 타이밍·provider·제출/체결은 현재 code review/배포 영수증과 별도 수용이다.

재리뷰 검증: 진입/async/native 완료/지연/scale-in/동결 정책/ordered/router13개 시험 모듈2,970개 PASS(36.31초). 기존 pandas_ta deprecation 경고1건은 기능 실패가 아니다. Python compile5개·diff·print-only parser PASS, 당일9개 OPEN ID와 자연 수용 owner1개를 유지했다. 최초 경합 재현 실패와 보완 통과를 `tmp/native-entry-arm-review-deploy-20261015-1137/`에 분리 보존한다. 변경 코드·소비자·unknown/미체결/후속 소유권을 재리뷰했고 현재 수정 범위의 미해결 결함은 없다. Kiwoom wire/parser/auth/등록 흐름은 변경하지 않아 이번 범위의 API 계약 수정 검증은 해당하지 않는다.


## 11:50 capability 인계 보완

038fe6ea8의 ordered 재기동은11:49:10 PASS(PID1907749/start9642233)였지만, 후속 실제 reader 대조에서 rising_missed/holding_vote의 정책 코드 capability가 unverified로 남았다. 공용 handler의 전체 파일 해시가 두 family 세대에 포함되므로 기존92785 successor 등록·fixture를 그대로 재사용할 수 없었다. 배포 전 점검 누락이며, policy/원천 실패 또는 전략 수치 변경은 아니다. 원본86에도 같은 인계 누락이 있다.

두 family의 원 코드→검토 완료 코드의 정확한 전체 세대 해시만 갱신한다. rising_missed 후속은 d2af96d68157d270ed4fc8f44c67896180210100e0f86ddc3505c288d7470807, holding_vote 후속은 d0a28277da5dccdeaf07830fc426ff2cf7b9eb0ebbea35bd48ed20adbacdedd3이다. native fixture 생성기는 네트워크 차단·provider/order0·원 보고서/정책/selector/bootstrap 불변을 확인하고 새 해시 경로에만 영수증을 생성한다. 역사적 unverified/native_validated=false는 그대로 두고 현재 reader capability만 독립 검증한다.

재발 방지 시험은 실제 소스 세대와 검토된 후속 해시의 일치를 확인한다. 보완 전2개 모두 실패했고, 원천/계약/fixture/권한 변조는 기존 거부 회귀로 검증한다. 다음 배포는4개 family의 실제 reader 검증을 포함한 사전 점검 이후 진행한다. 기존 실행 파일을 덮어쓰지 않고 불변 후속 release를 사용한다.

보완 재리뷰: capability/native 계약/탐지 소비자354개 PASS(4.32초), compile2개·diff·print-only parser PASS. 두 family 구성 파일을 기존3d435와 대조해 변경은 검토한 공용 handler 한 파일뿐임을 확인했다. 정확한 해시 제한과 원본/fixture 거부 동작을 유지했다.


## 최종 통합 배포·실제 PID 소비

최종 실행 commit은 `3b390be1e71f6b90f309ecce6ca49a8ddb2629b3`이며 원86f789693 및 이전 승인a179bb42d/92785b7da/e6326b0b1/87fda9479를 모두 조상으로 포함한다. release는 `/home/ubuntu/KORStockScan-runtime-releases/native-entry-arm-capability-20261015-3b390be1e`다. 기존038fe6ea8/PID1907749를11:55:44에 정상 drain한 후 선택·prepare·시작·실제 소비 검증이11:57:59 PASS로 종료했다. 새 Main은 PID1927180/start9694877이며 실제 cwd/selector가 이 release와 일치한다. startup hold는 없다.11:58:36 WS snapshot의 transport producer도 이 PID/start로 갱신됐다.

배포 전 네 family reader 모두verified, 두 신규 fixture177개(rising_missed86, holding_vote91) PASS/provider0/orders0/네트워크 시도0이다. 원 보고서4개의 SHA는 그대로 보존했다. active-native33개 코드 계약은 변경되지 않아 원 sealed parity를 사용했고 모든 정책/원천844개 해시와 candidate delay/stop/holding을 검증해 새 handoff를 발행했다. 기존 정책 숫자/선택/current pointer/원 PREOPEN을 재생성하지 않았다.

통합 검증은 진입·기동2970개, capability·탐지354개, native fixture177개로 구분해 기록한다. live 전환 중11:51의 일시 I/O wait 경보는 다음 자연 탐지에서 사라졌으며 과거 실패 기록은 보존한다. 현재 code repair와 실제 실행 소비의 완료가 다음 자연 AI 응답/주문/체결/비용 후 성과의 완료를 의미하지 않는다. 자연 수용은 기존 `AuxiliaryCircuitRecoveryRepair1012` OPEN으로 유지한다.

증거: [최종 후보·승인 조상](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/candidate.json), [native 사전 검증](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/native-preflight.json), [보존한 원 보고서](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/preserved-report-hashes.json), [배포 로그](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/deployment.log).

최종 자연 소비 검증:12:00 정규 슬롯의 run `30745732ad31473d8a4b4f67a11cc4c4`가12:01:44 완료됐고, observer 계산57.263초로 정상 게시됐다.12:02:56 탐지기가 같은 run·현재 code/PID·report SHA·health projection을 소비했다.12:03:15 대조15항목 모두PASS이며 실패 detector0/정책 capability4개verified이다. 원본 네 보고서는 계속 같은 SHA다. `recorded_guard_or_cohort_pending`과 과거 장후 effective-date06:50 이후 복구 경고는 그대로 남으며 full coverage·제출/체결·경제성 성공을 뜻하지 않는다. [최종 수용 영수증](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/final-acceptance-120315.json), [실제 PID·WS 확인](../../tmp/native-entry-arm-review-deploy-20261015-1137/capability-successor/deployment-check-120236.json).

코드 재리뷰 범위의 미해결 결함은 없고 당일 OPEN9개와 자연 신호 owner1개를 유지한다. 실행 중인 PID의 checklist 봉인은 수정하지 않는다. 최종 운영 기록만 별도 문서 commit으로 남기며 selected 실행 commit은3b390be1e다. 외부 Project/Calendar 동기화·수동 provider 호출/주문·광범위 재계산은 수행하지 않았다.
