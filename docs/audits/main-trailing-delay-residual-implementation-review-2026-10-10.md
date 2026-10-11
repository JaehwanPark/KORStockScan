# Main trailing/delay 잔여 구현·반복 리뷰 — 2026-10-10

**후속 정정 — 10/10 21:27 KST:** [정책 생성 구조 재점검](main-trailing-delay-policy-generation-structural-review-2026-10-10.md)에서 정상 holding-AI 원천 연결·classifier 인과성·대용량 numeric 후보 전달·현재 PASS/보조 부모 연결 및 결손 격리에 새 결함을 재현했다. 아래 부모/0초 발행·성능·인계 영수증은 당시 범위의 기록으로 보존한다. 그러나 “신규 경제 적격 0·양수 지연 0은 구현 누락이 아니다”라는 포괄 결론은 철회한다. 이전 양수 회귀의 AI 불필요 fixture와 producer를 분리한 단위 검증으로 실제 정상 경로의 생성 가능성을 대신한 한계를 명시한다. 시간과 자료 증가만으로 새 정책이 생성될 것이라는 근거로 이 완료 기록을 사용하지 않는다.

Source는 2026-10-08, publication은 2026-10-10, 적용일은 2026-10-12다. [W0–W6 실행계획](../proposals/main-trailing-delay-residual-work-completion-plan-2026-10-10.md)의 **W0–W5 구현·반복 리뷰·정식 발행·배포·기동 준비를 완료했다.** 정책 계산·코드 수용·정식 chain·미래 PID·실현손익은 별도 판정한다. W6와 실현 경제성은 미관측이다.

## 구현과 리뷰

- 정상 `postclose_exit` holding producer가 원 census/cost/native trace를 읽어 불변 입력 세대와 전수 manifest를 만든다. 거대 completed projection은 기존 producer의 byte/census/dependency seal을 확인한 뒤 streaming adapter로 읽는다. aggregate 비용을 거래별로 배분하거나 누락한 수량·후행을 합성하지 않는다.
- 외부 정렬·전역 중복/conflict 격리·시간순 split/purge·최소 결과 tree가 기존 단일 객체 상한을 넘는 입력을 처리한다. 논리 hash와 물리 leaf hash를 구분하고 동일 feature를 복수 후보가 한 번의 stream에서 공유한다. warm terminal 재사용도 verifier의 전체 원천 byte 검증을 유지한다.
- actual/alternative/ENTER-PASS CF를 분리한다. 등록된 상황 hypothesis와 인접 numeric grid는 train에서 고정하고 독립 holdout으로 검사한다. 적격 actual 상황 셀만 기존 one-market selector의 비용·slippage·tail·rollback 계약으로 연결한다. 표본 부족 셀은 부모를 승계한다.
- 지연 v2는 두 anchor를 분리하고 valid `price_ready` pair의 글로벌 0초 초기값을 허용한다. 미검증 native/부모의 셀에는 양수 실행 권한을 주지 않는다. 20,000기회·4,096셀을 넘는 연구 자료도 tree로 보존하며 준비된 runtime lookup에는 현재 exact 부모의 적격 양수 셀만 담는다.
- 실제 writer→2-slot admission, deadline, CAS와 발행 상태를 검증한다. 동기 native adapter는 실제 잠금 FD와 서로 다른 정확한 slot 경로를 요구하며 제한된 metadata CLI만 실행한다. 원 deadline 뒤의 완료는 deferred다. marker→정책→companion receipt→verified 사이 중단은 incomplete이며 reader가 거절한다.
- release/정책/summary/checklist/strict/PREOPEN의 metadata writer는 durable 전환 journal에 참여한다. 각 rename/progress 경계의 전 세트 복구, 원 bytes 보존, unknown successor의 CAS 거절을 시험했다. EOD/trade snapshot 재생은 이 제한된 전환에서 금지한다. native 최종화의 별도 후속 세대는 자신의 terminal과 최신 source 검증으로 대사한다.

## 실제 원천과 성능

실제 원천은 **2,604종목 × 8시장·경로 = 20,832 scope**다. 복원한 원 ENTER/PASS는 **7기회**, 유효 후행/공통 경제 모집단은 **0**이다. raw completed snapshot missing/source-gap/unverified는 각각 **1/5/1**이며, native 연결 불가 50건·후행 미관측 7건을 손익 0으로 바꾸지 않았다. 시장·상황 **12셀 parent carry**다.

제출 지연은 **31 commit / 29 qualified PASS / P0 6 / price pair 21**이다. 정책 부모 미검증 29건이므로 **0초 baseline / 적격 양수 셀 0**이다. 해당일 raw/compact family overlap은 valid-empty이며 누적 원 날짜의 검증된 가격쌍을 사용한다. 원장을 새로 복제하지 않았다.

동일한 64 original-position·각 60 native quote·18 numeric candidate를 이전 불변 릴리스와 3회 비교했다. cold wall은 기존 **8.05–8.07초 → 4.26–4.28초**, warm wall은 **0.088–0.092초 → 0.063–0.065초**다. warm CPU는 **0.059초 → 0.064초**로 소폭 증가하므로 CPU까지 개선됐다고 표현하지 않는다. 합산 parent/child peak RSS는 **136,832KiB**로 512MiB 예산 안이다.

전체 Main loop의 normal/burst/slow-writer 3회 비교는 동일 loop SHA·동결 WS/계좌·격리 provider/broker 경계에서 due 관측·보유 handler·writer를 실행했다. 누락·주문·provider 호출 0이며 original 5초와 hard/protect/custody의 의미는 별도 실제 handler 회귀로 검사했다. 이 시험은 장중 실측이나 실제 주문 수용이 아니다. [계측·원천 근거](../../tmp/main-trailing-delay-residual-20261010/)에 individual wall/CPU/RSS·counter·source seal·시험 로그를 남겼다.

## 검증과 정식 인계

통합 회귀 **1,371 passed / 2 deselected**, 마지막 admission 보완 뒤 영향 회귀 **133 passed**다. 제외한 두 historical Samsung intake 시험은 현재 canonical 부모에 의존하며 이전 선택 릴리스에서도 같은 실패를 재현했다. 현재 범위의 정책을 과거 부모로 바꿔 통과시키지 않았다. 기존 4개 연구 command를 기대한 obsolete 시험은 현행 continuous-reversal 단일 producer와 원 source date를 검사하도록 수정했다.

compile·location gate·diff와 최종 불변 릴리스의 영향 회귀 **215 passed / 10.22초**를 확인했다. 아래 정식 발행·strict/controller/finalization·PREOPEN 검증으로 W5를 닫았다. 10/12 실제 기동·PID 소비·자연 주문/실현손익은 해당일 `DirectFamilyPreopenPolicyHandoff`가 수용한다.

### 정식 normal 경로 재리뷰

첫 제한 발행에서 shared data 전체를 출력 budget으로 순회하는 결함을 발견했다. 전환 journal 9개 metadata를 원 bytes로 복구하고 이전 릴리스의 PREOPEN `current_full_contract=pass`를 확인했다. 지연 연구·원천 ledger의 출력 budget을 각 family tree/cache/policy와 atomic old/new로 한정했다. 원천은 별도의 완전한 byte verifier가 계속 검증한다. 5GiB의 관련 없는 sparse 원천·공유 alias가 있는 `input_root == output_root` 정상 CLI/원천 ledger를 추가 회귀로 검사했다. 실패한 trial 릴리스를 최종 배포로 보고하지 않는다.

추가 normal 인계 검증에서 지연 v2 economic projection의 closure owner/test 누락과 기존 checklist validator의 초기 가격정책 handoff 미지원도 발견했다. journal 29개 metadata를 원 상태로 복구하고 이전 PREOPEN PASS를 확인했다. 실제 owner/test를 보완하고 초기 가격정책의 독립 handoff 상태를 consumer에 연결했다. 발행 상태는 정확한 정책 receipt·runtime contract 검증을 요구하며 경제 promotion 권한은 계속 false다. summary/checklist/strict 영향 회귀 121건이 통과했다.

대용량 holding 경로의 legacy vote 인계 누락으로 strict가 차단된 것을 추가 확인했다. journal 35개 metadata를 원 bytes로 복구하고 이전 PREOPEN을 검증했다. 전수 실제 cohort는 계속 봉인 참조로 보존하며 원 vote signal ledger가 없는 부분은 `source_gap_partitioned_vote_inputs_unavailable`로 명시한다. 기존 source-bound 부모 vote bundle을 생성할 수 있는 prior 구조와 별도 cohort role/ref/count를 유지하며 observed vote·실현 EV는 합성하지 않는다. 실제 original→normal holding→manifest→vote bundle 연결을 추가 회귀로 검사했고 영향 시험 188건이 통과했다.

정식 full controller `done`·strict pass 뒤 finalization의 bounded date header 검사에서 정렬 JSON roundtrip의 키 순서 결함을 확인했다. journal 37개 metadata를 복구하고 기존 PREOPEN PASS를 확인했다. snapshot writer가 제공된 date 값만 첫 key로 보존하게 수정했으며 날짜를 합성하거나 검증을 완화하지 않았다. 정상/journal 저장과 기존 최종화 영향 시험 60건이 통과했다.

실제 `python -I` filename router 검사에서 상대 import 결함도 발견했다. 환경/cwd package를 import하지 않고 canonical sibling 두 파일만 읽으며, 일반 package mode는 기존 ContextVar/FD proof를 유지한다. 악성 PYTHONPATH/cwd와 publishing fence 거절을 subprocess로 검사했고 실제 PREOPEN print-plan도 성공했다. 초기/trailing 계산 contract·policy bytes가 같으므로 이번 수정 발행은 release/summary/strict/controller/PREOPEN만 다시 결속하며 연구를 재계산하지 않는다.

## 최종 수용 — 2026-10-10 20:51 KST

최종 불변 릴리스는 `main-trailing-delay-residual-20261010-v6` / `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`다. [최종 준비 영수증](../../data/report/main_trailing_delay_deployment/2026-10-10/final-residual-readiness.json)은 source 10/8·target 10/12의 `current_full_contract=pass`, finalization issues=[]를 기록한다. native 최종화는 실제 20:50:41 KST DONE이며 chain `30b1205f5acbd04a2ffeb64d3f3b106a87c90500520a987de885a1381888e316`, snapshot `f8b6e9b91b65e4d7da57a54761f116588e79bc23e8272b9804af9bef3838337d`와 정확 detector receipt를 대사했다. 과거 trial의 strict pass나 수동 DONE으로 대신하지 않았다.

설치 cron의 8개 경로, 실제 `python -I` PREOPEN/start print-plan, release source integrity 검증은 PASS다. 웹은 ubuntu·v6 cwd·PID 143446·HTTP 200이다. Main은 중지 상태로 10/12 07:35 PREOPEN / 07:55 자연 기동을 기다린다. 실제 Main PID 소비는 false이며 준비 완료를 장중 적용·체결·실현 순익으로 보고하지 않는다. 그 자연 수용은 봉인된 10/12 기존 `DirectFamilyPreopenPolicyHandoff`가 맡는다.

이번 정식 발행은 trailing의 정확한 부모 계승 12셀과 delay의 0초 초기 baseline을 수용했다. 신규 실제 경제 적격 모집단 0·양수 지연 적격 cell 0은 원천/선정 결과이며 구현 누락이 아니다. 원 기계·보조 정책 SHA `04f13c0bbc438e28f8f97de86f0fa4d52e6ea73a35fc355123daa5b7b2ce5a27`와 두 EOD 원본 SHA는 최종 준비 검사에서 불변을 확인했다. 후속 holding vote는 원 vote 입력 부족을 명시하고 기존 부모 값을 보존한다. provider·AI·주문 호출 및 EOD 재생은 0이다.

미사용 trial checkout v1–v4는 process/FD·systemd/cron·현재/rollback·runtime source 변경·공유 symlink를 점검하고 각 HEAD를 `refs/archive/disk-cleanup-20261010/`에 보존한 뒤 제거했다. 현재 v6·직전 v5·기존 d61 release와 원천·원장·과거 검증 영수증은 보존했다. free-space 증가 **276,152,320 bytes**이며 raw 삭제는 0이다. [정리 근거](../../tmp/main-trailing-delay-residual-20261010/cleanup-result.json)에 후보·이유·보존 ref·결과를 기록했다.

## 문서·작업본 종료 검증

변경 연계 문서 7개의 로컬 링크/anchor **129개 결손 0**, fence·공백·`git diff --check` PASS다. print-only parser는 **23개 OPEN·stderr 0**이며 오늘 두 구현 owner는 완료로 제외되고 10/12 자연 인계 owner는 정확히 하나다. Python 45개 compile과 현재 작업본/선택 v6의 runtime source byte 일치를 확인했다. 해당일 봉인 checklist는 native successor의 SHA `6850f76ca1deeb68dff8d44d5f3f4240525f9cd5bba348795e128ef525d95ae2`를 유지하며 Plan Rebase도 불변이다. 완료 기록 보완과 trial 정리 후 PREOPEN/현재 finalization/실제 예약 경로를 다시 검사해 PASS를 확인했다.

외부 Project/Calendar sync는 실행하지 않았다. 최초 수량·손절 퇴역·의미적 감시기 후속 계획의 별도 문서 변경은 이번 구현에 포함하지 않고 보존했다. 실제 시장 성능·Main 자연 PID·주문/청산·비용 후 성과는 이후 해당 owner의 증거가 필요하다. 이미 통과한 전체 회귀는 문서 종료만을 이유로 반복하지 않았으며 최종 코드 영향 회귀와 실제 normal 인계 검사로 닫았다.
