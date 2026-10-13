# Joint 정책·원천 연결·AI 입력 지연 구현 리뷰 — 2026-10-13

구현·반복 리뷰와 표적 검증을 완료했다. P1 신규4정의를 등록하고 10/14 작업본 기계·보조 후보를 준비했다. 최종 불변 release 결속·배포·재기동·PID 소비는 별도이며, 현재 운영 성능·HTTP 성공·주문·실현 손익의 완료로 해석하지 않는다.

## 승인된 배포 전 재리뷰

10/13 후속 지시는 기존 joint·비상시감시·입력 지연 개선의 리뷰·보완·배포·재기동이다. 사용자 응답으로 별도 약세 장후 WR0–WR5 신규 구현은 제외했다. 해당 계획·미완료 원천 연결은 유지한다.

- 신선한 두 체결 사이에도 native epoch/sequence/수신시각 단절이 있으면 그 구간을 `source_censored_count`에 남긴다. 이후 FALSE만 관측했다고 전체 관측을 `pattern_not_matched`로 확정하던 결함을 수리했다. epoch·sequence·역행 시각 반례와 최초 정상 두 체결 대조를 검증했다. 신호·주문 기한/조건은 변경하지 않았다.
- 기동 인계는 기존 초기 정책의 원 source SHA와 검토한 새 consumer SHA를 정확히 한 쌍으로 검증한다. 변경된 Main 연결·경제성 관측 시계·Buy Funnel 진단 세 파일을 등록하고, before/after/dirty/원 digest 변조 반례를 검사했다. 함수 전체나 미래 변경을 포괄 허용하지 않는다.
- [재검증 1,011건](../../tmp/joint-operating-deployment-20261013/final-tests.log) 통과. [동일 128경로·76,800체결](../../tmp/joint-operating-deployment-20261013/review-parity-benchmark.json)의 기존 확인점614개와 signal SHA가 보존됐다. 전체 Main 지연·provider 응답 개선은 아직 자연 관측 대상이다.
- [기동 전 원천 대조](../../tmp/joint-operating-deployment-20261013/predecessor-source-census.json)에서 v7의 frozen 정책/env/PREOPEN/controller/준비 영수증은 동일하고 체크리스트 편집본만 달랐다. Git의 v7 체크리스트가 정확한 봉인 SHA와 일치함을 확인했다. 승인된 전환 lock 안에서 편집본과 봉인본을 모두 보존하고, 기존 봉인본으로 선행 PID를 검증한 뒤 새 릴리스·편집본을 함께 발행한다. 실패 시 원 편집본을 CAS로 복구하며 타 작업의 문서를 덮어쓰지 않는다.
- 새 릴리스는 별도 Git index/불변 commit으로 만들고 운영 data/logs/tmp는 기존 공유 경로를 사용한다. 비교/AI 원장 복사0, workspace index·미커밋 작업 보존. 오늘 정책 유지·내일 등록 후보 결속·새 PID 소비를 각각 기록한다.
- 실제 candidate loader 재리뷰에서 오늘 d906의 이전 코드 pin과 수정된 native code가 충돌하는 기동 차단을 발견했다. scalping 소유의 `reversal_code_handoff`는 당일/현재 pointer/불변 candidate commit/정확 전체 contract code/원 validator가 읽은 모든 원천 hash/실제 parity·검증 근거를 묶은 승인 영수증만 소비한다. 원 validator는 보존된 v7에서 전체 검증하고, 새 runtime은 각 원천·코드 해시를 재검증한다. 일반 과거 fallback·정책 재선택은 없다. 원 source 오류는 호환성 영수증으로 우회하지 않으며 N의 dependency cache에 selector·영수증·각 source/code를 모두 연결한다. 이 파일의 위치는 live policy 검증을 소유하는 기존 `src/engine/scalping`이며 engine root 추가0이다.
- 다음날 joint 활성화에서 아직 이전 코드에 묶인 parent를 읽을 때 기존 manual-ADD 검증기를 잘못 호출하던 결함도 수정했다. 실제 joint schema의 승인 검증기로 분기하고 parent CAS·등록 원문·date/commit 검증은 유지한다. 내일 활성화 분기와 당일 호환성의 코드/원천/pointer/날짜/authority/멤버/봉인/selector 변조 및 영수증 결손을 회귀검증한다.

## 원 요청과 오류 근거

- Owner: [P1·N0–N4 구현계획](../proposals/main-joint-research-operating-adoption-and-scope-replacement-plan-2026-10-13.md).
- 13:54:55 주성 timeout의 정확 ID는 `analyze_target:036930:1791867294049:3345a46c`, snapshot은 `aims-375479a9437283692131`이다. [bounded 원천](../../tmp/joint-operating-implementation-20261013/reported-timeout-bounded-source.json)은 원 파일16MiB 이하 tail에서 찾은 연결 행이다.
- 호출 전1.546초 중 `entry_economics`775.427ms가 가장 길었다. HTTP lock0ms, provider1418ms, 남은 HTTP budget1440ms였다. 인증 오류나 broker 주문 실패의 증거는 아니다.
- 동일 policy snapshot 약671KB가 경제성 문맥과 조건부 seed에 반복 포함됐다. 이것이 전처리775ms 전체의 원인이라고 확정하지 않는다. clone→identity/route/capacity→sizing/price guard→policy/state freeze→split/TTL/plan→canonical append의 세부 시계를 추가했다. 원5초·계정/수량·quote/claim·주문·모델·회로 기준은 보존한다.

## 구현과 추가 리뷰 수리

| 범위 | 구현·수리 | 검증 경계 |
|---|---|---|
| P1 | 주성 AFTER/SOR 고가2→3개, 일반 PRE/NXT 저가4→5개. 신규4정의·remove2개이며 P2 REGULAR는 미포함 | exact128경로 중2경로만 membership 변경 |
| F 합성 | 원 확인점 dependency를 내부에서 유지하고 그 확인점에서 F를 한 번 평가. optional UNKNOWN은 유효 원 확인을 보존, FALSE는 해당 branch를 거부 | 원 ask/시각/sequence 보존, F 단독 재신호0, 원 필수 결손 UNKNOWN |
| A08 | 독립 BREAKOUT60와 ret≥0/DD≤0.4/BUY10≥60 | FIRST/하락 anchor 없이 실제 strict 돌파 확인 |
| 등록·발행 | 기존 수동 batch 승인 계보 보존, consumed/rollback 후 재적용 방지, 연구 결과·manifest·parity의 불변 소형 archive | provider/비교 원장 생성0. 리뷰 수정의 parity receipt 변경은 같은 parent·정의·날짜·범위의 미소비 batch만 supersede; 이전 객체 보존 |
| 장후 선택 | 승인된 이전/추가/교체/균형 조합 전체를 동일 원천에서 탐지하고 각자 전체 기회의 누적 확정 승률 비교 | 임의 조합·극단 축소 불허, 분모0/원천 범위 미확정은 current carry. 선택된 기계 목록을 보조 튜닝이 parent로 되돌리던 결함 수리 |
| N1 | 종목·item·venue·session·date별 최초 사실, v2 atomic index/cursor 및 v1 reader, bounded 증분 복원과 기존 준비 스레드의 미완료 복원 재개 | 새 stream anchor, restart·부분행·tamper·native/collector namespace·알려진 최초 값 유실의 UNKNOWN 보존·late restore의 union State 전달/캐시 무효화 검사. rolling interval은 이어 붙이지 않음 |
| index 저장 | 기존 단일 FIFO writer로 첫 사실을 저장하고 같은 날짜의 요청을 합침. 실행 중 들어온 변경은 최대2회 write 후 기존 FIFO로 catch-up | 신규 thread0, tick별 전체 index write0, 실제 최초 사실은 재가격화하지 않음 |
| N2/N3 | 실제 branch/phase projection, source 결손/필수 특징/정상 no-match/미완료 관측 구분. result v2·queue v3와 v1/v2 queue 복원 | 마지막 all-FALSE 한 장만으로 정상 전체 관측을 주장하지 않음. lifecycle·pending·source censor 근거, queue/scanner/Main/sentinel 소비 연결 |
| N4 | 부분 수신이15초에 부족해도 필수 window가 원60/150초 deadline 안에 맞으면 같은 lease에서 event wait | 데이터0건은 기존10초 종료, min5/fresh3초·slots5/long2·원5초·cleanup/REMOVE 소유권 유지. generation 교체/남은 window 불가 시 종료 |
| 입력 저장 | warm owner가 policy·코드·원천 파일 내용을 content-addressed parts로 저장하고 요청에는 rules와 참조를 보존 | 정확 원 snapshot/버전 복원, 누락/변조는 gap, 기존 inline reader 유지. 원 비용·상태·stock·quantity·guard 데이터 누락0 |

새 Python 모듈은 scalping catalog/registration/source index와 lifecycle replay storage에 두었다. engine root 추가0이며 Kiwoom wire/request/parser/FID/REG packet/인증 변경0이다.

정책 part/index는 필수 replay source다. 완료 연구 복제본처럼 삭제하지 않는다. 원 seed/정책/장후/replay/rollback 소비자의 ref census로 index→part까지 보호하며, 재생성할 때 원 canonical snapshot hash가 유지돼야 한다. archive는 실제 연구 result/manifest의 ref를 보존하고 시장·AI 원장을 복제하지 않는다.

## 검증 결과와 성능 한계

- [최종 표적317건](../../tmp/joint-operating-implementation-20261013/final-targeted-validation.txt), [경제성/trace/deadline244건](../../tmp/joint-operating-implementation-20261013/final-clock-tests.txt), [최종 source 복원53건](../../tmp/joint-operating-implementation-20261013/final-source-contracts.txt) 통과. 중복된 테스트 수를 합산하지 않는다. family/replay189건과 소비자283건도 관련 변경 단계에서 통과했다.
- Python compile, engine 위치 gate, diff 검증을 수행했다. 문서는 print-only parser와 링크/owner 검증으로 닫는다. 패키지 설치·외부 sync·Provider 호출·실주문·전체 장후 재생성은 수행하지 않았다.
- [교대 성능 근거](../../tmp/joint-operating-implementation-20261013/performance.json): 불변 v7와 작업본을3회 교대로128경로·76,800틱 재생. 기존 확인614건과 signal SHA가 모두 같았다. 최종 detector wall 중앙값은 약5.6% 증가했다. warmup/steady·CPU/RSS를 별도로 남겼다.
- 같은 문맥의 snapshot 참조 전환은 canonical 크기736,315→109,685bytes이며 좁은 deepcopy+encoding+digest 측정은 약5.9→2.0ms였다. source/수수료/규칙/원 상태 roundtrip은 동일하다. 작은 파일 하나만 바뀐 fixture의 추가 저장은3KB 미만이다.
- 이 replay에는 전체 Main loop·실제 WS/REST·보유/청산·completion·실제 writer 부하의 시간 분포가 포함되지 않는다. 관련 guard/holding/replay 회귀 통과와 전체 loop p95/실제 timeout 개선을 구분한다. 실제 runtime 개선은 배포 후 같은 attempt/PID에서 새 세부 시계로 확인해야 한다.
- [저장 manifest](../../tmp/joint-operating-implementation-20261013/storage-manifest.json): 새 task 임시 근거 약9.6MB, 최초 등록 archive 약0.66MB, 원장 복제0. anchor512bytes/stream·3,000stream의 약1.54MB는 예측이며 실제 증가/필수 raw와 따로 측정한다. 새 index 최대16MiB, replay snapshot 최대16MiB, 동일 파일 부분 재사용 계약을 유지한다.

## 원천 epoch 제외

[10/12 disposition](../../tmp/joint-operating-implementation-20261013/historical-epoch-disposition.json)에 retained closed source owner가 증명하는3개 collector epoch와 frozen normalization의 원 제외를 보존했다. PRE15,347·REGULAR496,054·AFTER33,853행, 합계545,254행의 `source_epoch_unverified`는 보완하지 않았다. 해당 owner에서 다른 역사 epoch를 승인하는 원 증거를 찾지 못했으며, 미검사 archive까지 영구 복구 불가라고 주장하지 않는다. 현재 epoch·native epoch를 대신 주입하거나 허용 목록을 확대하지 않는다. 이 제외는 P1 지정 초기 채택의 추가 승인 gate가 아니다.

## 실제 준비 상태와 후속 인계

- 등록 request: `8d624a144de50727a98193dab77d5fd93cf4c87d0003db42a41b7e36660f8e09`; 리뷰 전 request `7d892a54...`는 불변 archive에 보존하며 superseded다. [intake 근거](../../tmp/joint-operating-implementation-20261013/registration-intake.json).
- 기계 component: `1367332c81bc4ac996459e769bf18e278727055caed128ab3d6a0dbf9165fcd6`; 보조 component: `bd930dfce6afaadc726a436472a848ffb4646ea97825a2d517b569bedc8dcbb8`. AI comparison_complete=false, 새 실제 Provider 호출0이다.
- 10/14 작업본 후보: `eed8b8280771d546b2a6015e54d5651bf30fc247a3ffd61a59c3d32f4a04fd9c`. [native 원천·인계 검증](../../tmp/joint-operating-implementation-20261013/next-session-prepared-validation.json)에서128경로 준비와 exact2scope delta를 확인한다. 이는 최종 배포 release/PID 수용이 아니다.
- 원 운영 pointer d906와 선택 v7를 유지했다. 당일 적용·배포·재기동은 하지 않았다. 배포 전 최종 reviewed immutable release commit/실행 code·reader 증빙에 후보를 다시 결속하고 `DirectFamilyPreopenPolicyHandoff`의 native strict/PREOPEN 검증을 수행한다. 낡은 code pin으로 기동하지 않는다.
- 자연 수용은 기존 `NonfixedDispatchReadinessReview1012`와 `AuxiliaryCircuitRecoveryRepair1012`에 연결한다. 다음 날짜 checklist로 stable ID와 Acceptance/History를 이전하고, 과거07:55~08:15 완료나 이 문서 자체로 미래 실행 권한을 만들지 않는다. source-ready→native→claim→machine→AI→Main 소비를 같은 lease/attempt에서 확인한다.

이번 리뷰 범위에서 남은 구현 결함은 발견하지 못했다. 최종 release 결속/배포·자연 성능/실제 주문·경제성은 별도 미완료 상태다. 다른 미커밋 작업본은 보존했다.
