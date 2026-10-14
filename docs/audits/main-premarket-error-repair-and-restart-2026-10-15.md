# 2026-10-15 장전 오류 수리·배포·재기동 검토

사용자 08:12 지시로 08:20까지 병목 감시를 중단하고 오류 처리·배포·재기동을 우선한다. 기준은 선택 릴리스 `3d644d8495a2c257784d96cd01df831bfb6022f8`, Main PID `1441388`, start ticks `8248936`이다. 최종 계산 수정 `a179bb42d`를 포함한 그 기준에서 격리 구현했다. 작업본의 다른 변경은 통합하지 않는다.

## 결함과 수리

- 08:05 holding missing: producer START 08:05:01, DONE 08:05:24 사이 08:05:17 검출. 첫 missing에 300초 유예를 registry와 semantic reader에 동일 적용한다. 08:10:01부터 실제 missing 검출, 기존 malformed/date mismatch/Markdown-only 즉시 검출을 회귀 검증했다. valid_empty는 실제 익절/경제성 수용이 아니다.
- 고정 watch 제출: `premarket_krx_like`와 `krx_like_premarket`가 같은 장전 구간인데 문자열 순서 차이로 source/revision 결속 실패. known alias만 동등 비교하고 원 필드·hash·watch parent·route·venue·수량·broker 안전 검증을 보존한다. 다른 시장/unknown/공백/비문자 입력은 거부한다. 실제 PASS가 있던 08:03:42 알테오젠 attempt `aims-0515d1d9a9aff574f8a2`가 재현 근거다.
- 08:10/08:15 submission observer: SOR-only native receipt 검사를 exact KRX/NXT/SOR item/route 검증으로 보완했다. frozen NXT 만료 2건/경로 무효화 4건을 native claim/registration/hash/source sequence 그대로 검증했다. pending anchor·현재 branch truth·누적 TRUE/UNKNOWN·타 cell raw ready를 동일 모수로 취급하던 오류를 수정했다. 현재 selected ready/TRUE 또는 stale source는 여전히 거부한다.
- source window: forward index 시작 08:05:05.341944 전 관측은 미완료로 유지한다. 08:19:24 검증은 최근 10분 93건, window complete, malformed 0, index+bounded append 19,164,667 bytes다. 기존 32MiB reader 한도/원 로그/인덱스를 변경하거나 과거를 backfill하지 않았다.

## 리뷰·검증

실제 producer/consumer 및 bootstrap/handoff/router를 검토했다. selected3d 코드에서 구현→자체 리뷰→보완→재리뷰 후 관련 pytest 1,973개 통과. live-clock 통합 fixture의 YYYY-MM-DD도 시각과 함께 이동하도록 수정해 자정 이후 정책 날짜 오검증을 해소했다. KRX/NXT/SOR × v5/v6 × lifecycle와 foreign route/hash/quote/source 반례를 포함한다. Compile, diff 및 문서 parser는 최종 배포 전 기록한다.

원 `entry_machine_input_deadline_expired` 10건은 native 종료 증빙이 없어 기존 실패로 보존한다. 실제 provider timeout/0B/source-quality/원 신호5초 guard도 완화하지 않는다. 이번 수리가 모든 자연 신호의 성공, 주문, terminal 또는 비용 후 성과를 보장하지 않는다. 새 PID 경보 상태와 과거 실패는 별도로 확인한다.

## 배포 수용

사용자가 배포 및 재기동을 명시 승인했다. ordered intraday driver로 incumbent 검증→graceful drain→불변 candidate 선택/문서 게시→원 정책 유지 handoff→정상 launcher→새 PID native 소비를 확인한다. frozen PREOPEN/bootstrap/env/정책 부모와 원 checklist 증빙을 보존한다. Main/manual custody와 퇴역 보유/intent는 변경하지 않는다. 재기동 전후 broker inventory/미체결, WS 수신, singleton PID, selected commit, 원 경보와 현재 source 상태를 대사한다. 실제 결과는 `tmp/intraday-submission-20261015-until0820`와 native `data/runtime/release_transitions` 영수증이 소유한다.

기존 OPEN owner는 `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`, `HoldingProfitExitSourceContractRepair`와 `DirectFamilyPreopenPolicyHandoff`다. 계획/리뷰와 배포/PID/자연 실행/경제성 완료를 혼동하지 않는다. 외부 Project/Calendar sync, provider replay, 수동 주문과 광역 장후 재계산은 실행하지 않는다.

## 사전 배포 검증 보완

첫 candidate `a2d8b8bdb`는 incumbent native/PID bootstrap PASS 후 `entry_consumer_unreviewed_change`로 drain 이전 차단됐다. selector/PID/hold 변경 없이 원 Main이 유지됐다. 3d native PREOPEN의 monitor SHA `90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d`와 수정본 SHA `7484dde211aeca61eb8172072f432c7d24bf7803e39c0f73ef9561cb64d0bfcf`만 별도 검토 pair로 등록했다. 원/수정 byte·dirty verifier·origin digest 변조 거부 회귀를 확장한다. 실패 attempt는 보존하고 새 commit에서 인계를 다시 검증한다.


## 08:32 경보 후속 수리

1차 배포 `10e53c3df84a5280ae268828f7fbc83328c11ac4`는 08:28:27 ordered transition complete다. 기존 PID 1441388을 graceful drain하고 새 Main PID 1481448/start ticks8438079의 실제 native 소비를 확인했다. 정책 bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`, bootstrap seal `73a9a4f20bc146ea40c2f74966e107a3cb7773ef623dd1b9df0750a838adebad`는 유지됐다. WS 수신과 기존 manual/retired custody·미체결 대사도 확인했다.

08:32 경보의 08:30:13 보고서 원본 SHA `62e533fbfc14181a9b547ae0fe6f9f6819f67093102137bae9427952803ec661`는 보존했다. 그 보고서의 원천 계약 issues는 비어 있으나 다음 소비 오류가 남았다.

- native fixed watch의 NXT 장전 허용 구간을 일반 KRX entry clock=false로 배제해 정상 초기 대기4건을 unknown으로 분류했다. native session_route·당일 generation·admission·source signature를 검증해 분리하며 exact owner/venue/session·주문 없음·broker 금지를 보존한다.
- bounded pending 건강 판정이 scanner rows=0/unobservable만 허용했다. 유효하고 완료된 observing 보고서는 신선한 input·exact current actor/birth·source/policy/lineage 계약을 모두 통과할 때만 warning_pending 경로를 사용한다. 다른 status/blocker·stale/date/dry-run·결손·변조는 계속 실패다. full_coverage_proven/current_observation_verified/runtime_effect/allowed_runtime_apply는 모두 false다.
- provider lineage의 30분 read에서 넘어온 partial 상태를 현재 10분+5초 cohort에도 그대로 적용했다. 동일 bytes의 first_read_at이 현재 window 시작 이전이고 malformed/missing-clock/incomplete가 모두 없을 때만 현재 coverage를 재산정한다. 원 reader 상태·byte/read count·inode·시각을 보존하며 추가 읽기나 과거 복원은 없다. consumer도 narrowed window 시작/기간/원 상태를 재검증한다.

원본 대기4건과 동일 reader 증빙을 사용한 순수 재현은 warning_pending/bounded_source_quality_observation으로 판정된다. 원 보고서·정책·원천 파일은 수정하지 않았다. 08:35 후속 원천의 실제 entry_machine_input_deadline_expired 등 새 결손은 정상화 대상이 아니며 원 진단을 보존한다. 이 수리는 정상 신호/주문/손익을 보장하지 않는다.

후속 candidate의 native monitor hash는 `dd164faf5619deb20eef0456cd1187164f09d7f2094c474a2c691e9b700a253f`이고 REVIEWED_ACTIVE_OBSERVER_SOURCES에 원 PREOPEN 해시와 exact pair로 등록한다. 이전 소비 pair는 유지한다. targeted pytest·compile·diff·문서 parser와 원 경보 재현 후 ordered driver로 배포/재기동하고 새 generation 소비를 별도로 기록한다.

후속 재리뷰·표적 검증: producer/consumer·handoff/router·source-window 총 2,047개 pytest 통과(18.43초). current active observer의 detector warning 및 source/date/actor 변조 FAIL 통합 회귀를 포함한다. py_compile, git diff --check, print-only parser PASS이며 당일 parsed OPEN owner는 기존9개다. 새 승인 요청·provider replay·임계값 변경·실주문은 없다.
