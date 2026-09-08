# #73 Pipeline verbosity 보완 리뷰

기준일: 2026-09-08 KST. 범위: 원본 기록 보호, 경량 producer summary, 장후 대사/유지 판정, 직접 workorder·BUY Funnel·wrapper 소비. 매매 전략·threshold·provider·수량·operator lock은 변경하지 않는다.

## 판정과 목적

목표는 원본 증거를 보존하면서 반복 로그의 부하를 줄여 작은 순수익 기회의 처리를 지원하는 것이다. 로그 절감을 위해 기회/주문/안전/실현손익 증거를 없애거나, 단순 대사 성공을 EV 개선으로 해석하지 않는다.

9/7 정식 report에는 raw 4,744,832,377 bytes, 고빈도 161,387건, producer 160,970건이 기록돼 있다. producer 전부가 lossless 보존 대상이고 suppressed=0이다. 완료 공통 구간에서도 278건이 달랐지만 최종 상태는 pending_flush였다. clean baseline 이후 확인한 65개 report는 pending 63, partial coverage 1, no-eligible 1로 유효 표본이 있는 parity pass는 없었다. 이는 검토 당시 과거 증거이며 이번 구현으로 원본 결손이 복원됐다는 뜻이 아니다.

## 1차 구현과 재리뷰

| 결함 | 보완 | 검증 기준 |
| --- | --- | --- |
| 요약 오류가 원본·threshold companion 저장을 막음 | 원본/companion 먼저 기록; 요약은 별도 예외 구간과 raw writer lock 밖에서 수행 | constructor/submit 오류 주입에도 두 원본 경로 기록 성공; raw 실패 시 요약 증거 생성 금지 |
| 마지막 이벤트 이후 저장되지 않는 tail | 기본 60초 periodic flush, 종료 best-effort drain, pending group 4,096 제한 | 신규 이벤트 없이 idle flush; 날짜 혼입 방지; 손실된 과거 메모리는 합성하지 않음 |
| 재시도·동시 저장의 중복/manifest 경합 | thread serialization + 날짜별 nonblocking filesystem mutex; 실패한 locked append만 rollback | 병렬 제출 보존, manifest 오류 후 retry 중복 0, 잘못된 target-date flush 거절 |
| 건수만 같은 다른 종목·사건도 parity PASS | bucket/symbol/pipeline/stage/strategy/market/reason/order count + 전체 canonical payload SHA256 multiset 대사 | 종목·record ID·시각·session·비투영 필드 변조 차단; flush 분할/순서 차이는 정상 처리 |
| 완료 구간 mismatch를 pending이 가림 | 완료 구간 불일치 우선; 기본 120초 지난 tail은 flush timeout과 native repair workorder | 대기 중이어도 닫힌 구간의 손실을 수리 대상으로 전달 |
| 잘못된 입력/캐시가 정상으로 보임 | malformed raw/producer, 잘못된 manifest count, same-size raw rewrite, 원본 0/producer 양수 구분 | invalid input은 parity PASS/valid-empty로 승격하지 않음; 구 schema1 identity 부족과 새 schema 결함 분리 |
| 절감 대상 0인데 무기한 승격 대기·상세 이중 기록 | producer/parity 모두 counts_identity_v2; sample/numeric/second 상세 중복 제거; no_suppressible_events 판정 | 절감 가능 bytes와 실제 raw 감소 0 구분. BUY Sentinel 기본 full-detail summary는 유지 |
| 검증 없는 env suppress와 과거 승격 workorder | 기존 suppress 요청은 raw-preserving shadow로 처리; 과거 suppress-guard workorder 재개 제거 | 실질 원본 생략 0, 별도 EV/실체결/2영업일 승인 대기 없음 |
| pending 결과의 영구 freshness 재사용 | wrapper의 read-only schema/date/terminal cache gate와 logger/registry 코드 의존성 추가 | pending/source-changing은 재사용 금지; 정상 terminal은 기존 freshness 검증 후 재사용 |

원본 payload hash 합은 분할된 batch 간 동일 사건 집합을 대사한다. 순서 검증용 주문 원장이나 broker authority의 대체물이 아니다. 실제 사건 순서는 raw에 보존한다. 기존 producer schema1 요약의 identity를 raw에서 복제해 새 정상 producer receipt로 만들지 않는다.

## 1차 경량화 확인

로컬 `HEAD:src/engine/pipeline_event_summary.py`(검사 시 `1010e97a`)의 기존 full-detail 집계와 새 counts/identity 집계를 동일한 합성 입력으로 비교했다. 조건은 scanner fast-precheck 2,000건, 20종목/20개 분 bucket, source-quality·market/session·promotion/record ID 및 queue/lag 필드, 각각 5회 process CPU 중앙값이다. 파일 I/O·실제 봇 처리·주문·EV 측정은 아니다.

| 지표 | 기존 | 보완 | 해석 |
| --- | ---: | ---: | --- |
| summary JSONL 크기 | 52,330 bytes | 17,160 bytes | 67.21% 감소, raw 크기 감소 아님 |
| 집계·직렬화 CPU 중앙값 | 50.571 ms | 30.292 ms | 해당 합성 비교에서 40.10% 감소; 운영 지연 개선으로 외삽하지 않음 |
| 요약된 event count | 2,000 | 2,000 | 입력 건수 보존 |

실제 producer manifest에는 마지막 flush bytes/duration, 저장 크기, writer PID, periodic mode와 오류 provenance를 남긴다. 실운영 logger/queue p95·p99 및 순이익 효과는 별도 자연 관찰 전까지 미측정이다. 불필요한 실주문 표본이나 양수 EV를 진단 수리의 완료 허들로 추가하지 않았다.

## 1차 검증·반영 경계

회귀 검증은 logger/summary/report, submit-drought contract, BUY Funnel, code-improvement workorder, postclose wrapper와 archive 소비를 포함한다. skill `korstockscan-review-gate`에 따라 직접 소비자·silent fail·동시성·날짜/캐시·원본 보존을 재리뷰하며 발견 결함을 수정했다. 검토 범위의 미해결 finding은 0이며, 전체 시스템 무결함이나 자연 경제성 성공을 의미하지 않는다.

- 코드 검증: 최종 관련 8개 test file **487 passed (13.96초)**. ruff, Python compile, `bash -n deploy/run_threshold_cycle_postclose.sh`, `git diff --check` 통과. 문서 print-only parser 34건 중 `PipelineVerbosityNaturalEvidence0908`이 당일 owner로 포함됨. 외부 Project/Calendar sync는 실행하지 않음.
- 현재 PID/env/주문/operator lock 변경, 봇 재기동, commit/push: 이번 작업에서 실행하지 않음.
- 9/7 및 9/8 canonical 운영 report 재생성: 실행하지 않음. 테스트 산출물은 격리된 임시 디렉터리에서만 생성.
- 기존 실행 중 PID의 logger가 새 코드를 읽었다고 주장하지 않음. 장후 새 report와 새 logger producer의 반영 시점은 다르다.
- 다음 자연 확인: 당일 체크리스트 `PipelineVerbosityNaturalEvidence0908`. 새 producer schema/정상 idle flush·identity·report/workorder/BUY Funnel 소비를 확인하며 legacy 소스만 있으면 deployment/source 증거 대기로 남긴다. 이 항목은 재기동 권한이 아니다.
- 기존 운영 문서의 과거 suppress 설계 대기 설명은 현재 적용 권한이 아니다. 이번 source contract의 원본 보존·비활성 결정은 traceability §2.3에 명시하며 runbook의 retention/실행 권한은 바꾸지 않는다.

결론: 원본 근거를 희생하지 않는 경량 진단으로 유지한다. 별도의 로그 생략 승격 대기열은 없으며, 매매 횟수·실현 EV 증가를 이번 코드 수리 성과로 보고하지 않는다.

## 추가 최종 리뷰와 2차 보완

1차 검토의 finding 0은 당시 검증 범위다. 후속 읽기 전용 리뷰에서 아래 3개 경계를 새로 재현했으며, 사용자의 추가 보완 요청에 따라 구현했다. 200ms/150ms 수치는 격리된 지연 주입으로 운영에서 측정한 지연이 아니다.

| 추가 결함 | 재현 | 2차 보완·회귀 기준 |
| --- | --- | --- |
| background publish가 submit과 잠금을 공유 | 저장 200ms 지연에서 호출자 202.75ms 대기 | 집계와 게시 잠금 분리, detached retry batch. 실시간 submit은 날짜 변경·주기 0·high-water에서도 disk flush를 하지 않음. 게시가 막힌 상태에서 신규 호출 반환·최종 건수 보존 확인 |
| 지원 주기와 timeout 불일치 | 600초 설정에서 121초에 timeout | `max(120, interval+60)` bounded allowance. 600초 설정의 121초는 pending, 661초는 timeout. invalid/무제한 주기는 manifest 결함 |
| manifest I/O가 저장시간에서 빠짐 | 전체 150.56ms인데 기록 0.122ms | canonical 게시 완료 뒤 full publish 시간 측정. 별도 PID/date health receipt의 자체 I/O는 측정 scope에서 제외하며 manifest hash에 결속. summary submit 최근 최대 2,048개 호출 p95/p99/max와 장후 JSON/Markdown 연결 |

추가 자체 리뷰에서 synchronous/offline 호출도 잠금 순서를 뒤집지 않도록 집계 잠금 밖에서 flush하도록 보완했다. retry batch와 신규 buffer는 날짜별로 분리하고 각각 최대 4,096 group이다. high-water 2,048에서 worker를 깨우며 실패 시에는 주기별 bounded retry만 허용한다. overflow는 원본 보존·명시적 summary gap, 종료는 비동기 요청 또는 최대 5초 drain 대기이며 강제 kill이나 무한 대기는 하지 않는다.

측정 metadata는 기존 `data/pipeline_event_summaries/` owner 아래 `pipeline_event_producer_health_DATE_PID.json`에 둔다. 새 Python producer/module이나 독립 전략축은 만들지 않는다. mode handover의 같은 PID writer도 날짜 mutex와 current manifest hash로 대사한다. health 기록 실패는 성공한 canonical append를 재시도하지 않으며 consumer는 stale/invalid health를 측정 결손으로 구분한다. raw parity와 측정 결손은 별도이고 경제성·매매 승격 권한은 계속 없다. wrapper의 freshness 의존성에도 해당 health receipt를 추가했다.

자연 반영은 기존 `PipelineVerbosityNaturalEvidence0908`에서 확인한다. 실제 비교 baseline이 없으면 `runtime_latency_improvement=null`이며 수리 완료를 실제 봇/주문 지연 감소나 순이익 증가로 보고하지 않는다. 운영 원천 재생성·봇 재기동·env/lock/주문 변경·commit/push는 이 보완에서 실행하지 않는다.

2차 최종 검증: 관련 8개 test file **507 passed (13.92초)**, ruff·compile·shell syntax·`git diff --check` 통과. print-only parser는 34건이며 기존 natural ID가 1회 포함된다. `korstockscan-review-gate`로 직접 소비자·잠금 순서·날짜/재시도·원본 보존·측정 authority를 재리뷰한 범위의 미해결 finding은 0이다. 전체 시스템 무결함이나 현재 PID 반영을 뜻하지 않는다.

최종 격리 재현에서는 게시 잠금이 풀리기 전에 summary submit이 0.102ms로 반환했다. canonical manifest에 150ms 지연을 주입했을 때 health 포함 전체 작업은 150.852ms, 별도 기록된 canonical publish 구간은 150.520ms였다. 임시 raw→producer→report는 `v2_shadow_parity_pass`, identity parity true, timing `observed_no_comparable_baseline`, 개선량 null로 종료했다. 이는 합성 수리 검증이며 실제 시장/주문/EV 결과가 아니다.
