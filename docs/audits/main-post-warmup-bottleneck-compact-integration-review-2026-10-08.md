# Main 워밍업 이후 병목·compact 통합 구현 리뷰 — 2026-10-08

사용자가 [병목 계획](../proposals/main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)과 [compact 계획](../proposals/main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md)의 구현·반복 리뷰·수정·배포·재기동을 승인했다. B0/B1/B2/B3/B4/B5a/B6의 코드 수리를 완료했다. B5b source composition은 동등성 미입증으로 REST를 유지한다. 배포/PID/자연 결과는 아래 별도 기록을 따른다.

## 1. 원천과 권한 기준선

- 실제 이전 Main PID 241227, start ticks 2483072, selected/cwd `main-aux-compact-20261008-v3`, 코드 commit `dc769a09c052df06b265c7d9ce196428caae20ec`를 확인했다. [baseline](../../data/report/main_bottleneck_compact/2026-10-08/baseline.json)은 해당 시점의 기록이다.
- bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`, overlay `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626`를 보존한다. registry 128경로는 v2 네 scope·v1 124경로다. 기존 Main PID의 overlay 소비 receipt를 확인했으며, 새 PID 소비와는 구분한다.
- 원 5초 claim, scanner/fixed-watch native identity, canonical quote, 수동 veto, Main/manual custody, account/quantity/capital/cooldown, hard exit, provider 동시성/간격/5회 circuit 및 uncertain outbox를 보존한다. episode/widget 자동 실행은 계속 영구 퇴역이다.
- `DirectFamilySourceRepairMainMechanisticEntry` 현재 owner 한 개를 유지한다. checklist SHA는 `ca53931ef8e47bfab9d387460a17b1993a00355f24e91b9b6a4f3ccc3afadaf2`이며, 기존 dirty 문서/연구 자료는 덮어쓰지 않았다. 실제 release source와 공유 docs/checklist byte를 별도로 검증한다.
- 보조 I/G/W/C/X reader 파일 hash는 기존 overlay와 일치한다. 157쌍 연구·호환 증명을 재사용하며 새 연구 AI 호출은 0회다. 대용량 원장 복사·EOD/전수 장후 재실행·외부 sync·시험 주문은 수행하지 않는다.

## 2. 구현 및 리뷰 수리

| 단계 | 구현과 마지막 소비자 | 결함 보완 및 종료 증거 |
|---|---|---|
| B0 | runtime performance + client-attempt telemetry | strict `<5초`, `≤2초` 누적 CDF, circuit/reset 신원, 512 minute eviction 이후 late terminal, 256 coarse key/128 recent overflow를 보존. 상세 소실은 lower bound로 명시 |
| B1 | 실제 Main WATCHING/outer drain → native coordinator → state handler commit | 제거/holding/수동 차단된 exact request만 discard/ack; successor pending 보존. 원 monotonic/epoch 잔여 budget을 tick/candle/investor/refresh/continuation/admission/HTTP timeout에 전달. 만료한 첫 source가 다음 물리 조회를 시작하지 못함 |
| B2 | native validator → 예약 → adapter → SDK → response → outbox/commit | native 종료는 circuit을 증가·reset하지 않음. queue에서 취소된 미전송 wall deadline을 HTTP error로 포장하던 결함을 수리. SDK 시작은 전달 미확정, 응답만 response-confirmed. 실제 제공자 5실패 차단 유지 |
| B3 | 검증 저널 generation → symbol/account/manual projection → native policy | 같은 generation에 반복 deepcopy/reducer 제거. account 변경·동시 generation 변경·동일 길이 변조는 fail closed. 반환 dict 변조가 캐시를 오염시키지 않으며 수동 disposition은 해당 검증 generation에 고정 |
| B4 | WS ingress immutable row → owner lock freeze → 밖에서 materialize → 기존 full/dashboard 소비자 | 원 route/epoch/full history 유지, 120행은 dashboard에만 적용. mutable nested/비표준 object 복사와 deque capacity 및 기존 최종 list normalization을 검증. 기존 pending batch/lock 순서 유지 |
| B5a | exact ka10080 demand/cache/singleflight → native source selector | 완료분 cutoff가 identity에 포함됨. empty/truncated/missing continuation/rate/deferred는 cache 대상에서 제외. 원 수신시각/TTL 유지, 430봉 하한 유지 |
| B5b | 현재 430봉 source selector | 수정주가 REST/당일 원주가 WS의 동등성 미입증. 새 composition reader 선택을 활성화하지 않고 기존 REST 유지; 다른 수리 배포는 계속 |
| B6 | 국면 CNN 전용 memory session + 실제 Telebot CUSTOM_REQUEST_SENDER | `fear_and_greed` 전역 SQLite patch import 제거. poll/send thread·TTL 재생성에서도 plain session을 쓰며 설치본의 실제 retry engine을 보존. 미사용 uppercase SESSION adapter의 중첩 retry는 활성화하지 않음 |
| B7 | unchanged reader/128 bindings → native handoff → selected immutable release → actual PID | 기존 정책 ID/원 binding/strict checklist를 유지하여 새 코드로 인계. 재연구·경제성 gate 추가 없음 |

원 확인점 전후 v1/v2 선택과 같은 scope 철회만 reject하는 실제 `selected_definition`/`validate_decision` 검사를 통과했다. Main harness는 **실제 호출 statement/wrapper 및 outer drain**을 두 iteration에 연결하고 실제 coordinator/consumer를 실행한다. broker는 fake이며 실제 매수 체결 증거로 사용하지 않는다. 유효 commit 및 submit guard는 기존 별도 회귀로 검증한다.

## 3. 공식 참조 및 검증

[공식 Kiwoom 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인했다. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/core/auth.py`, `kiwoom/_data/kiwoom_api_spec.json`, Postman의 ka10003/ka10080/ka10059 PRD/MOCK·continuation·fields와 auth 경계를 검사했다. 조회시각 및 파일 hash는 [official-reference](../../data/report/main_bottleneck_compact/2026-10-08/official-reference.json)에 있다. path/api-id/header/body/FID/REG/REMOVE/real-demo 의미는 바꾸지 않았다. upstream 현재 tree의 `kiwoom_docs` 부재와 REST/WS adjustment 미입증을 source gap으로 남겼다.

- 통합 대상 회귀 **1,074 passed / 18 deselected**. 제외된 18건은 영구 삭제된 shared-rebound/PYRAMID 및 episode gateway/policy를 import하는 퇴역 기능 검사다. 삭제 기능을 복원하여 통과시키지 않았다.
- 최종 WS 컨테이너·원천·Main/AI 재리뷰 회귀 **727 passed / 7 deselected**. 제외된 7건은 같은 퇴역 shared-rebound 검사다. 이 수치는 중복 검사를 합산한 고유 검증 수가 아니다.
- 마지막 실제 Main 호출/outer drain/commit와 보조 wire·철회·submit 원천 검사 **212 passed**. WAIT 및 ENTER_NOW+PASS/BUY fixture 각각의 worker 호출 1회와 단일 commit 소비, route/generation 교체 시 거절을 검증했다. 실제 broker 주문은 실행하지 않았다.
- 첫 immutable v1의 확대 검사에서 fixture 두 건이 실패하여 배포하지 않았다. 30ms worker 시작 가정은 선행 worker 준비·bounded event 대기로 고쳤고, configure fixture는 자기 backend generation을 격리했다. 보완 후 관련 **135 passed**. runtime code의 deadline을 늘리거나 guard를 완화하지 않았다. 최종 immutable 결과는 아래 배포 증거에 별도 기록한다.
- 기존 auth retry 테스트의 전체 dict 동등성은 원천 metadata 추가 계약에 맞춰 metadata 별도 검사로 보완했다. token replacement·첫 8005 이후 같은 stale token 재사용 방지·실제 요청 순서를 계속 검증한다.
- Python compile, `git diff --check`, print-only backlog parser를 검증했다. parser 21개·현재 실행 owner 1개, 경고 0건이다. package 설치/제거, 실 provider/broker 테스트, 퇴역 테스트 복원, Project/Calendar sync는 생략했다.

## 4. 성능 증거와 한계

[microbench](../../data/report/main_bottleneck_compact/2026-10-08/microbench.json)는 2,000행 WS view와 3,000 event 저널에서 동일 입력을 50회 반복했다. WS 잠금 내 median은 약 2.78ms → 0.42ms, 저널 반복 query는 11.83ms → 0.006ms였다. 새 WS materialize는 잠금 밖에서 약 3.85ms이므로 전체 복사시간 감소나 실제 loop p99 개선으로 바꾸어 보고하지 않는다. 원 내용·route·전체 행 수·mutation isolation을 검사했다.

[이전 성능 snapshot](../../data/report/main_bottleneck_compact/2026-10-08/previous-performance.json)의 PID 241227 warm loop 2,863회는 p95 0.894초/p99 1.948초, >5초 2회였다. 이전 schema에는 circuit 관측이 없고 새 배포와 장세·부하 window가 다르므로 인과적 전후 개선율을 계산하지 않는다. 새 release의 circuit/신호/source/HTTP demand 및 warmup 이후 분모를 별도로 수집한다. 자연 요청이 없으면 async/provider/submit 성능은 미관측이다.

첫 운영 v2 배포의 [자연 관측](../../data/report/main_bottleneck_compact/2026-10-08/new-performance-latency-incident.json)에서 warm loop 65회 중 72.847초 지연 1회를 확인했다. 첫 loop 1.191초와 별개이며 워밍업 제외로 숨기지 않는다. 해당 시점에는 async/native claim 분모가 0이었는데, 신호 없는 fixed-watch의 `not_enabled`가 실제 Main의 inline REST 준비를 시작했다. 관측된 개별 HTTP 시간만으로 72초 전체를 증권사 지연이라고 확정하지 않는다.

추가 수리에서는 검증된 당일 정책의 exact 종목/시장/가격대/주문 route가 `union_v5/v6`로 활성화되어 있고 native claim이 없으면 `waiting_native_signal`로 돌아온다. 실제 Main consumer가 inline 준비 이전에 반환함을 실행 검증했다. 유효 claim은 기존 비동기 준비/AI/commit 경로를 그대로 사용하며, 비지원 backend는 기존 경로를 유지한다. 5종목 × PRE/REGULAR/AFTER × native/legacy backend 경계와 단일 신호 소비 회귀 **279 passed**를 확인했다. false 첫 AI 시작 로그도 신호 대기 중에는 출력하지 않는다. 최종 immutable 배포 후 성능은 별도 PID 창으로 기록한다.

## 5. 배포 및 실제 소비

중간 immutable v2 `f1cd48730419eababc9b9bd994ef093ad78404fb`는 확대 회귀 **1,107 passed / 18 deselected** 후 17:01 KST에 배포했다. Main PID 271405와 web release를 정렬했고 native handoff·base/auxiliary 실제 소비·HTTP 200을 확인했다. 기존 bundle/overlay/128 bindings 및 네 scope v2를 그대로 승계했다. 위 추가 발견을 수리한 후보는 다시 immutable 검증과 인계를 수행하며 최종 결과를 이 절에 이어 기록한다.

후보 v3의 추가 확대 검사에서는 생존 경로 1,231개가 통과했으나 주문 분할 테스트의 autouse fixture가 삭제된 `machine_microstructure_attribution`을 불러와 200개 setup error가 났다. 후보는 배포하지 않았다. 이미 퇴역한 collector 격리 fixture를 제거했고 생존 주문 분할 회귀 **198 passed / 2 deselected**를 확인했다. 제외된 2건은 삭제된 collector 기반 옛 replay 검사다. 실제 주문 분할·broker 불확실성·submit 예외 보호를 건너뛰지 않았다. 최종 immutable에 이 테스트 수리까지 포함한다.

v2의 read-only cron 검사에서 finalization generation issue는 `{}`이며 `strict_checklist_generation_stale`은 재현되지 않았다. cleanup/finalization의 과거 06:50 cutoff 이후 복구 warning은 계속 보고한다. 전체 health PASS 또는 실제 체결 성공으로 표현하지 않는다.

최종 준비 직전 별도 문서 작업이 약세 관찰 계획 owner를 추가했다. 현재 checklist SHA `503685557588993927f13d39db72218cce9deeeafe877f6630c1afff26c9ed93`, parser 22개·이번 Main owner 1개이며 원 AUTO 봉인 블록은 동일하다. 이 변경을 덮어쓰거나 해당 계획을 구현하지 않는다. 최신 checklist 인계는 기존 native handoff에서 검증한다.
