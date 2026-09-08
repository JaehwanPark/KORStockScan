# #119 BUY Funnel → #23 Entry recheck 보완·재리뷰

## 판정

9/8 [10:25 점검](2026-09-08-buy-funnel-entry-recheck-1025-review.md)의 F1 수집/분류 누락, F2 record별 refresh 축약, F3 promotion/재시도 cycle 귀속을 보완했다. 원본 재대사에서 추가로 발견한 실제 제출 전 가격·micro·tick-speed terminal 누락도 함께 수정했다. **진단 코드 수리이며 제출 drought 해소 또는 런타임 ON/수익 개선 판정이 아니다.**

매매 함수 본문의 AST는 변경 전과 동일하다. guard·가격·수량·cap·provider·broker 요청·operator lock·env를 바꾸지 않았고 봇 재기동·장후 전체 재실행·canonical report/cache의 수동 재생성도 하지 않았다. 다른 세션의 모니터링 및 작업 파일은 보존했다.

## 구현

| 결함 | 보완 및 직접 consumer |
| --- | --- |
| 가격 terminal 누락 | `entry_submit_revalidation_block`, `entry_price_canary_submit_block`을 cache→PRICE_REVALIDATION→공통 validator에 결속 |
| 추가 상위 gate 누락 | 실제 반환 분기를 확인한 tick-speed, weak-AI/micro, micro unavailable, reversal pre-submit block을 공유 upstream 목록에 포함. #23의 AI-score/AI-authority addressable stage는 확대하지 않음 |
| record와 실행 횟수 혼합 | refresh도 공통 exact ledger의 event binding 사용. pass event/실행/record 분모를 별도로 발행하고 비차단 fallback을 terminal로 세지 않음 |
| promotion/retry 오귀속 | promotion을 parent로 유지하고 새 budget 평가·promotion 교체 시 cycle 분리. terminal 없는 이전 cycle은 정상 pending 대신 명시적 lineage gap. 동시 호출의 ID 없는 event는 추정 결속하지 않고 제외 |
| 미래 실행 ID·종료 계측 | `monitoring/entry_attempt_identity.py`가 제출 함수 호출마다 context-local ID를 발급. `_log_entry_pipeline`이 해당 ID를 단계에 주입하고 caller spoof를 제거. 함수 반환/예외 시 completion 관측을 발행하며 callback 실패는 경고하되 원래 반환/예외를 보존 |
| 종료 관측의 source-quality 계약 | 기존 audit에 새 completion stage의 필수 metadata·ID/schema·반환 enum과 runtime/apply false 검증을 추가. 다른 세션의 source-quality 수정은 보존 |
| stale cache/구 계약 재사용 | report schema6 / exact3 / raw cache10·lossless cache12. cache 버전 변경 시 기존 owner가 raw부터 재구축. 현재 판정 consumer는 구 schema5/exact2의 이름만 바꾼 산출물을 거부 |

신규 파일은 실행 정책이 아니라 관측 역할이므로 기존 `src/engine/monitoring`에 위치한다. 별도 tuning family, root engine 모듈 또는 주문/lifecycle/custody ID를 추가·교체하지 않는다. callback의 `entry_submit_attempt_finished`는 실제 submit receipt가 아니며, receipt 없는 성공 반환이나 terminal 없는 종료를 제출 성공으로 합성하지 않는다. 정상 async wait와 예외 종료도 구분한다.

## 10:25 원본 재대사

대상은 `pipeline_events_2026-09-08.jsonl`의 `ENTRY_PIPELINE`, KRX/KRX_REGULAR, 09:00~10:25:05다. 관련 raw 332행을 읽어 순수 집계/분류/공통 validator를 **메모리에서만** 실행했다. append 중 incomplete 마지막 row는 소비하지 않았다. 아래는 수정 코드로 재구성한 값이지 당시 파일을 덮어쓴 새 authoritative generation이 아니다.

| 항목 | 기존 집계 | 보완 후 원본 재구성 |
| --- | ---: | ---: |
| 시도 | 71 | 107 |
| terminal | 66 | 107 |
| pending / 미분류 terminal / submit | 5 / 0 / 0 | 0 / 0 / 0 |
| UPSTREAM_GATE | 33 | 51 |
| LATENCY_PRE_SUBMIT | 28 | 33 |
| ENTRY_AI_AUTHORITY_REVALIDATION | 5 | 6 |
| PRICE_REVALIDATION | 0 | 17 |
| BROKER_RECEIPT | 0 | 0 |

공통 validator PASS, structural issue0, stage-order violation0. 숫자 증가를 새 후보·제출·수익 증가로 해석하지 않는다. 과거 재시도와 누락 terminal을 복원한 것이다. call-local ID가 없던 과거 원본은 확인 가능한 parent/ordered retry로 재구성했고 미래 native ID 소비는 별도 acceptance다.

누락 stage의 자연 원본은 가격 context 재검증1, entry-price canary16, tick-speed7, weak-AI/micro1이다. 이들을 대사하기 전 나타난 terminal 없는 cycle은 추가 원본 확인 뒤 모두 실제 terminal로 연결됐다. refresh는 **7 pass / 7 실행 / 5 records**, 후속은 AI authority6·가격 재검증1·submit0이다. AI6은 fresh DROP4, WAIT63/probe intent 없음1, timeout1로 기존 점검의 exact trace와 일치한다.

## 검증과 리뷰

- Sentinel, 공통 계약, controller/policy/recheck/budget, pipeline logger/summary, lifecycle 직접 연결 회귀 469 PASS.
- engine location gate 3 PASS; Python compile 및 `git diff --check` 통과.
- 추가 반례: 구 cache 자동 rebuild, 구 schema 재라벨링 거부, 가격 차단 후 retry, main ID가 일부 단계에만 있는 promotion 교체/동일 promotion retry, 명시적 async wait, caller ID spoof, nested/thread/context reset, 예외·callback 실패, 중복 submit, 실제 reconciliation guard 조기 반환. API·실주문 호출 없이 검증했다.
- 제출 함수 본문 AST 동일성 확인. helper가 source-only telemetry를 넘어서 기존 함수의 반환값/예외·stock 상태·주문 권한을 바꾸지 않는지 재리뷰했다.
- source-quality audit 175 PASS. 위 직접 경로와 location gate를 함께 최종 실행해 647 PASS, workorder·strict verifier·PREOPEN·Entry AI gate·control tower·Daily·wrapper의 drought/recheck 직접 consumer 53 PASS로 총 700 PASS다. 재리뷰 범위의 미해결 코드 finding0이며 자연 산출물·기동 PID 소비·경제성은 이 테스트 결과로 종결하지 않는다.
- 최종 보완에서는 명시적인 refresh 차단0을 `attempted-applied` 차감값으로 덮어쓰던 fallback도 수정했다. exact0과 값 누락을 구분하며 구 cache/record 진단값으로 새 분모를 되살리지 않는다.
- 문서 링크, print-only parser32항목/기존 OPEN owner1건 및 `git diff --check`를 검증했다. 외부 Project/Calendar sync는 실행하지 않았다.

## 정기 producer 소비 관측

설치된 5분 cron의 11:35:01 START→11:36:20 DONE을 읽기 전용 확인했다. 운영 report as-of11:35:20은 schema6/exact3, lossless cache는12(11:35:19)였고 aggregate·KRX·PREMARKET의 공통 validator 모두 PASS/structural issue0이다. 정기 producer가 새 진단 계약을 소비한 증거이며 수동 재생성은 아니다. 당시 `SUBMIT_DROUGHT_CRITICAL`은 계속되고 가격/AI/latency drought가 분리되어 표시됐다. 이는 제출 성공 또는 #23/매매 PID의 새 코드 소비 증거가 아니다.

## 남은 자연 acceptance와 권한

기존 `EntryRecheckNaturalAttribution0907`을 유지한다. 다음 정상 Sentinel owner가 새 cache/report/exact 세대를 생성하고, controller→workorder/검증기→PREOPEN의 같은 날짜/hash를 소비하는지 확인한다. 신규 call-local ID는 새 코드가 정상 로드된 PID부터 관측 가능하며 현재 PID에 소급 주입하거나 재기동하지 않는다.

#23의 최근3거래일 source-quality 및 마지막 날 포함2일 addressable critical 조건은 변경하지 않았다. 현재 OFF를 강제 ON하지 않는다. **기존 9/3·9/4뿐 아니라 구 schema5/exact2인 9/7도 새 계약의 runtime 이력으로 그대로 재사용할 수 없다.** 구 source의 원본/identity가 충분한지 확인한 뒤 승인된 최소 Sentinel→controller 재생성을 수행하거나 새로운 유효 이력을 기다려야 한다. 불완전한 역사를 합성하거나 파일의 schema 숫자만 바꾸지 않는다. 이번 수정만으로 다음 PREOPEN ON 또는 제출 재개를 약속하지 않는다.

이후 eligible→evaluated→armed→submit→fill/terminal/net은 #23 후보군과 rising-missed scout 최종 AI 경로를 분리해 확인한다. 현재 병목은 더 정확히 드러났지만 AI DROP, 가격 입력 source-quality/stale, latency safety를 바꾸는 작업은 이번 범위가 아니다.
