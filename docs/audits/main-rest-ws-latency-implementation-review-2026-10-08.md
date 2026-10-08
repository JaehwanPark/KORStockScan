# Main REST/WS·평가 지연 구현 검토 — 2026-10-08

사용자가 두 계획의 구현, 반복 리뷰/보완, 배포·재기동을 승인했다. 작업본의 별도 보조 compact 연구·튜닝 변경은 배포에서 제외하며 현재 v6 기계·보조 정책 128경로/48운영 scope·추가 13개 등록과 Main-only 수동관리 경계를 유지한다.

## 구현과 실제 소비 경계

- **LP7/RW0:** 생존 물리 HTTP 경계 6곳(공통 조회/인증, 주문·인증 재시도, offline backfill 두 곳)을 연결했다. 시작 ID·KST 날짜·PID/start ticks·release·token/origin digest·API/owner/class·원 route·분당 bounded 계수와 terminal/timeout/inflight를 구분한다. 이미 파싱한 응답의 return code/bytes만 추가하며 body·계좌·token을 복제하지 않는다. admission은 기존 read-control 영수증, session/server 수신·미파싱 body는 unknown이다. 정적 376개 기록 중 사라진 전용 파일의 기록 54개를 퇴역으로 분리했다. 파일 존재만으로 실제 활성/호출 0을 증명하지 않는다.
- **LP8:** 스캐너 mode와 독립적으로 기존 coordinator를 고정감시에도 연결했다. 고유 native token·원 proof·원 deadline을 불변 context로 넘기며 scanner promotion ID를 합성하지 않는다. worker는 private stock 복사와 evidence만 반환하고 Main이 native claim/현재 quote·상태·주문/cooldown을 검사해 한 번 commit한다. 대기 중 확정 신호 우선/aging, 물리 작업 완료 전 슬롯 유지, 완료 알림으로 기존 대기를 깨운다. 같은 claim은 trigger/score가 달라져도 기존 request/cache identity를 유지한다.
- **LP10:** 원 claim epoch+5초와 caller budget의 작은 값을 queue/lock/전송/재확인까지 전달한다. 비동기 context의 monotonic deadline도 계속 전달하여 wall-clock 역행으로 유효시간을 연장하지 않는다. 짧은 유효 요청에 50ms 최소값을 더하지 않는다. 필수 후처리의 관측 p95 reserve는 최대 250ms이며, 관측 없으면 0이다. 만료·늦은 응답·취소는 기존 outbox를 해제하거나 주문 권한을 만들지 않는다.
- **RW1:** Radar의 동기 FDR/잘못된 직접 REST fallback을 기존 qualifying tick 기반 단일 준비 worker로 옮겼다. 공식 ka20006 chart/body와 고유 내림차순 20일/정확 base date/100 scale을 검증한다. 원 query clock을 보존하며 늦은/결손 응답은 기존 보수적 BEAR와 invalid 상태다. 기존 2값 helper는 유지한다.
- **RW2/RW4:** 동일 route/item/epoch·원 0B clock·연속 local ingress 10체결이 적격일 때만 entry prepare에서 WS를 재사용한다. local 순서는 broker 무손실 증명이 아니다. 불충분하면 기존 bounded REST/cache/single-flight로 간다. 0w는 자기 시각/item/epoch만 사용하며 새 0B가 옛 프로그램 값을 fresh로 만들지 않는다. 전일 프로그램/분집계·계좌/capacity·최종 독립 REST BBO는 유지한다.
- **RW3:** 공통 completed-bar writer/reader/마지막 Main candle consumer를 연결하고 episode admission을 제거했다. SOR/_AL의 원 journal·동일 PID/epoch·완성봉·전체 session prefix만 허용한다. **현재 Main 요구 floor 430봉은 당일 projection만으로 충족되지 않으므로 해당 경로의 REST가 유지된다.** 임의 lookback 축소·누락봉 채움·다른 seed/route 결합을 하지 않았고 분봉 절감 완료로 표시하지 않는다.
- **RW5:** dashboard snapshot의 후처리를 ingress 잠금 밖으로 이동했다. frozen copy·raw/journal·full history와 기존 protected subscription/lease/remove 경계를 유지한다. 재사용 consumer는 기존 Main 소유 구독을 읽기만 하므로 새 REG/REMOVE/refcount·세션/cap·wire 필드를 만들지 않는다. local sent registry는 broker ACK가 아니다. 전체 ACK 귀속·type별 wire 상한을 구현 완료로 표시하지 않는다.
- **LP9/LP11:** 필수 machine 본문/capture append·provider reservation을 동기로 보존하고 준비/capacity/capture/reserve/응답 검증/Main commit/guard/실제 주문 ACK timing을 분리했다. path 실패 predicate는 기존 원인값을 덮지 않는 추가 진단이다. v6에서 승계된 v4의 자기 registry/lock/cell을 사용한다. `ai_confirmed_terminal_no_budget`는 `pipeline_event_summary`가 exact attempt·전이 원문을 요구하므로 본문 생략 대상에서 제외했다. 비교 원장/AI 호출/새 주기 broker 요청은 생성하지 않았다.

## 반복 리뷰와 검증

리뷰에서 준비 executor enqueue 실패의 잔여 context, 취소 전 실행 여부 경쟁, mutable nested AI result, live stock observer closure, 고정감시 장 경계 route/watch 식별자 변경, 원 deadline 재설정, 만료 후 준비/commit, 진단 원인 덮어쓰기와 v4 승계 cell/registry 관측을 보완했다. native policy/kernel·주문 guards의 허용 조건은 변경하지 않았다.

고정감시 worker→Main commit/trigger 변경 중복, 큐 우선/비선점·취소, 50ms 미만·queue 만료·clock 역행, WS 부족/순서/item/epoch/지연, 지수 잘못된 날짜/중복/NaN/20일 결손, HTTP timeout/응답 계수/비밀 비보존, deque eviction을 회귀했다. 기존 정책·AI·WS/원천·퇴역 관련 530개, source/control/candle 관련 206개, native 제출/monitor/coordinator 관련 360개 및 deadline/AI/handoff/router 388개가 변경별 검증에서 통과했다. 중복 실행 수를 고유 총수로 합산하지 않는다. 최종 통합 검증은 1,092 passed/18 deselected이며, 후속 장 경계 route/watch 변경 회귀를 별도로 수행했다. 영수증은 아래 증거 폴더에 남긴다.

이미 삭제된 episode gateway/policy 11개와 옛 shared-rebound 전용 모듈 7개 테스트는 실행 대상에서 제외했다. WS의 삭제된 연구 worker 테스트는 Main publication/잠금 밖 후처리/퇴역 부재 계약으로 갱신했다. 전체 suite의 오래된 삭제 모듈 수집 성공이나 모든 미래 결함 0은 주장하지 않는다. Python compile·wrapper bash syntax·diff 및 print-only 문서 파서를 검사한다.

## 성능과 인계

동일 8개 item×120행과 qualifying tick 30회/모의 원천 지연40ms를 쓴 무네트워크 비교에서 Radar callback p95 **41.212ms→0.012ms**, p99 **43.290ms→0.317ms**, 원천 준비 **30→1회**다. 이는 callback network 대기 제거의 모의 결과이며 실제 REST 절감률이 아니다. 같은 dashboard fixture의 lock p95 **2.417ms→2.508ms**로 유의한 개선을 주장하지 않는다. frozen snapshot의 필드/원 clock과 원 데이터 격리는 유지한다.

배포 전 Main-only PID161317의 마지막 자연 누적 warm 표본1,489회는 p95 **2.837초**, p99 **4.702초**, 5초 초과 **9회**다. cold 60.364초는 별도다. native claim/provider 표본0이며 complete HTTP baseline도 없어 절감률은 null이다. 자연 신규 PID 표본은 새 창으로 분리하고 fixed-watch ready/claimed·원천 coverage·defer/만료·물리 계수를 함께 확인한다. warm p95≤2초·WS lock p99≤10ms·자연 provider 개선은 관측된 범위만 보고하며 표본 결손을 성공으로 바꾸지 않는다.

정책 발행/EOD·비용 큰 연구/장후 재생은 하지 않는다. 검증된 변경만 clean immutable release에 넣고 native policy-preserving intraday handoff로 현 policy pointer·원 strict/PREOPEN의 후행 인계를 봉인한 후 재기동한다. web도 동일 release로 고정하고 rollback은 episode/widget을 복구하지 않는 현재 Main-only release다. 새 PID/bootstrap/loader/5 fixed watch·guard·최종화의 `strict_checklist_generation_stale` 부재를 확인한다.

공식 upstream: [Kiwoom commit 953e5db](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f), retrieval **13:07:06 KST**, inspected specs/_data/core client/ws_client/realtime packets/decoders SHA는 [공식 영수증](../../data/report/main_rest_ws_implementation/2026-10-08/official_reference.json)에 있다. 조회 tree에 `kiwoom_docs`가 없으며 로컬 gate·이전 조사 Postman/공식 안내의 wire 차이를 임의로 해소하지 않는다. OpenAI timeout은 [공식 Python API](https://developers.openai.com/api/reference/python)와 installed SDK를 대조하고 기존 SDK retries0·provider/outbox 보호를 보존했다.

증거: [baseline](../../data/report/main_rest_ws_implementation/2026-10-08/baseline.json), [현 호출 분류](../../data/report/main_rest_ws_implementation/2026-10-08/callsite_scope.json), [모의 baseline](../../data/report/main_rest_ws_implementation/2026-10-08/benchmark_baseline.json), [모의 treatment](../../data/report/main_rest_ws_implementation/2026-10-08/benchmark_treatment.json), [재현 스크립트](../../data/report/main_rest_ws_implementation/2026-10-08/benchmark_reproduce.py).
