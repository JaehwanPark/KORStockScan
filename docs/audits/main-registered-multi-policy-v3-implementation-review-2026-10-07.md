# Main 등록 복수 정책 v3 구현·리뷰·배포 검토

소유는 `DirectFamilySourceRepairMainMechanisticEntry`다. 사용자 P1~P7 구현·반복 리뷰·배포·재기동 승인을 적용한다. [실행 계획](../proposals/main-all-scope-registered-multi-policy-implementation-plan-2026-10-07.md)의 기계 raw 승률과 보조 실제 raw PASS 승률 계약을 유지한다.

현재 상태는 구현 검증 중이다. 배포 및 실제 정책/PID 소비를 이 문서의 코드 검증으로 대체하지 않는다.

- 위치 gate: registry/rolling runtime/v3 policy/route replay·provider checkpoint는 기존 `src/engine/scalping`이 소유하고 새 테스트는 `src/tests`가 소유한다. engine root 신규 Python 파일은 없다.
- v1/v2 해시 고정 kernel·branch·보조 contract/phases bytes를 보존한다. native loader/AI/Main state/normalized callback/진단/장후 dispatcher/semantic/strict 소유만 v3를 분기한다. Kiwoom wire/FID/parser/REG/auth/account/order의 변경은 없다.
- 48 logical cell의 128 지원 route scope를 분리한다. KRX PRE 관측은 실제 연속 execution 지원으로 만들지 않는다. 새 S1~G4는 SOR REGULAR만 등록하고 일반 유형은 상시감시 5종목을 제외한다.
- 10,736 고정 catalog portfolio와 실제 native 소비 이력·현행을 비교한다. 후보 definition 및 원천/code/result hash를 등록하고 정기 작업에서 가설을 새로 만들지 않는다.
- 동일 확인 틱은 canonical opportunity 1개다. FIRST/CONFIRMED 입력과 anchor lineage를 보존하고 primary/보조/intent를 단일 경로로 연결한다. 5초 claim·최신 FIRST·중복 provider/intent·broker/quantity/cap/custody/retirement/hard safety는 유지한다.
- 장후의 각 route 원천을 재생하고 confirmed ask부터 비용 후 +0.4%/soft -3%/30분을 라벨한다. UNRESOLVED와 확인 실패를 손실로 만들지 않는다. 요청은 label·승률·분기명을 포함하지 않는 기존 English ASCII allowlist를 사용한다.
- 리뷰 보완: JSON tuple/list 발행 결속, retrospective ready queue로 인한 표본 잘림, 비교 이후 기계 stage 파일 덮어쓰기, 12셀 잔존 validator, exact request/owner ID 분리, 반복 PID 소비 이력 덮어쓰기, 일반 G1의 ret=0 경계, mutable 완성 분봉의 read/copy race를 수정했다.
- 완성 분봉 race에서 생긴 미발행 snapshot은 해시와 원 bytes를 별도 보존했다. 이제 producer가 읽은 동일 bytes를 atomic content-addressed source로 봉인한다. 기존 발행 family 및 EOD 원본은 변경하지 않았다.

검증과 실행 증거는 [작업 evidence](../../tmp/main-registered-v3-20261007/)에 저장한다. 최종 숫자·선택·배포·기동·자연 감시는 검증 종료 후 기록한다.

추가 리뷰에서 같은 틱의 CONFIRMED와 FIRST가 다른 저점을 가질 때 오프라인 FIRST 입력에 CONFIRMED의 하락 구간을 넣던 결함을 수정했다. 두 phase가 각자의 저점(103.30/103.35)을 실제 요청에 유지하는 회귀를 추가했다. 무표본 scope의 보조 binding은 새로 발행할 정규장 쌍이 호환될 때 그 binding을 승계한다. 동일 canonical 중복은 1개로 합치고 서로 다른 사본은 그 ID만 격리한다. native 적용 receipt는 불변 사본과 정의 hash로 결속하고 등록 연구 근거도 issued source에 포함한다.

코드 gate: 영향 경로 15개 pytest suite **784 PASS** (`final-complete-tests.log`), Python compile·`bash -n restart.sh`·`git diff --check`·print-only parser PASS. kernel/v1/v2 branch·보조 phases/contract bytes 변경 0. 기존 historical-checklist observer 수리를 포함한다. fresh launch/activation guard는 계속 현재 체크리스트를 검증하며 이미 소비된 10/6 DONE의 관측에만 봉인한 역사 체크리스트를 사용한다.

원천 gate: 별도 수동 필터 재계산과 지점/native index/라벨 대조에서 기존 삼성 32 WIN/33 확정과 S1 18/18, S2 15/15, D1 205/205, H1 31/31, A1 11/11, J1 29/29, G1 35/35, G2 29/29, G3 17/17, G4 12/12 모두 일치했다. 각 후보의 미확정은 별도 보존했다. 최종 코드의 전체 route replay와 실제 보조 비교 census는 실행 증거로 후속 기록한다.

부하 재생: 삼성 185,031행에서 v2 1.156초, v3 2.855초(약 64,806행/초), ready peak 3, pending/ready overload 0. 이 측정은 고정 파일의 코드 처리량이며 실시간 WS lock 지연·주문·경제성 검증을 대신하지 않는다.

최종 인계 리뷰에서 등록일 이후에도 같은 registry의 최소 연구 증빙을 native 보존 원천에서 찾도록 수정했다. 날짜가 바뀌었다는 이유로 registration custody를 누락하지 않으며 hash 변조를 거부한다. 추가 검증 **785 PASS** (`custody-final-tests.log`). 재생 모집단은 1,530,748 opportunity이며 실제 소비 정의가 있는 6개 version을 비교했다. 최종 비교 digest는 `d9379669052cbf82e6aaf9039661226625fc55fd0fab0f8c5ba032247e8cb3af`; canonical 충돌 격리 대상 0. 연구 고정 지점·라벨 대조는 최종 재생에서도 11개 정의 모두 불일치 0이다.

실규모 P4 원장 검증에서 per-call 전체 request BLOB 정렬과 재개 시 비커버 조회가 I/O 병목을 만들었다. 아직 신규 provider reservation이 0인 상태에서 중단·원장 보존 후 재개했다. 준비된 동일 generation/opportunity의 5 arm ID를 대조해 재사용하고, covering owner index·64MiB SQLite cache·한 번의 indexed identity iterator로 변경했다. read-only 구 query는 245초 이후에도 미완료였고 새 identity 정렬은 약 15.70초, covering index 생성은 1.84초였다. 전체 요청 배열을 Python 메모리에 만들거나 표본/횟수 제한을 추가하지 않았다. 최종 수정 검사 **786 PASS** (`ledger-final-tests.log`).

P4 전수 census: **116,007 입력점 / 580,035 비교 요청**, exact reuse로 generation의 unique transport request는 578,510개다. 과거 실제 응답 exact hit 1,624개, needs-call 576,886개다. offline 실행은 4 in-flight와 durable checkpoint를 사용하고 resource 시간 종료를 전수 완료로 표시하지 않는다. 신규 registered primary 우선 처리 후 잔여 비교를 이어간다. 현재 실제 provider 실행 및 발행 scope 검증 중이다.

추가 실규모 리뷰에서 outcome covering index를 provider 실행과 동시에 만들면서 SQLite 30초 write timeout을 유발한 작업 결함이 있었다. 신규 primary 4개 정의의 1,405개 arm 요청은 모두 완료된 뒤였으며, 과거 legacy 후속 호출 4건은 reserved/응답 저장 불확실 상태로 남겨 중복 호출하지 않는다. 전역 worker/schema/입력준비 잠금과 provider 응답 선행 fsync journal·정확 요청 재조정·부분 append tail 보존을 추가했다. 실제 추가 29개 응답 ID를 journal과 원장에 모두 보존했고 reserved 증가는 0이다. 누적 generation 상태는 completed 3,699 / planned 574,807 / reserved 4이며 이를 전수 비교 완료로 표시하지 않는다. 응답 유효성 오류는 순위에서 승률 보정하지 않고 진단으로 기록한다.

최종 재리뷰는 입력 census 대비 owner 전체 지점 누락도 비교 결손으로 식별하고, 일관된 SQLite read snapshot·내용 hash 기반의 atomic 실제 응답 사본을 사용하도록 보완했다. request BLOB를 읽던 종료 census는 covering index EXISTS 조회로 교체했다. 신규 주정책 D1/G1/G2/G4는 각각 205/35/29/12 입력점에서 5 arm 공통 비교를 완료했다. 선택 보조 reversal_complete_source_v7의 PASS는 각각 141/141, 24/24, 25/25, 8/8 WIN이다. 이 모집단은 기계 후보가 모두 WIN인 표본이므로 실패 분류력·실거래 수익 증거가 아니다. 미완료 scope는 검증된 기존 기계·보조 쌍을 함께 유지한다.

최종 코드 gate는 15개 영향 suite **790 PASS** (`journal-final-tests.log`), compile·shell syntax·diff 검사 PASS다. 원장 owner 전체 누락·crash journal 복원/부분 tail·동시 schema/입력준비 잠금 회귀를 포함한다. 기존 query가 로딩된 오프라인 검증 프로세스는 실제 응답 29개 모두 committed 및 이전 reserved 4개 불변을 확인한 뒤 종료했다. bot/episode 프로세스는 이 조치 대상이 아니다.
