# Main 비고정 관측 및 제출 병목 개선계획 — 2026-10-14

상태: **계획 리뷰·보완, B0–B4 구현, 반복 코드 리뷰·수리·표적 검증 및 승인된 배포·Main 재기동을 완료했다.** 실제 릴리스 `f8dc4431d`와 PID378870/start1473429의 native128/auxiliary128scope 소비를 확인했다. 전체 observer 검증은 남은 source gap 때문에 partial이며 자연 기계/보조 표본·전체 Main 성능·경제성은 pending이다.

목표: 정상 입력과 유효 신호가 기존 Main 경로에 제때 도달하게 하고, 실제 중단 원인을 정확히 연결한다. 주문 수 증가나 PASS 비율 상승을 단독 성공 기준으로 삼지 않는다.

## 1. 기준과 기존 작업의 경계

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). 실행 owner: [10/14 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md).
- 점검 기준: **2026-10-14 10:33:50~11:17:00.605872 KST**, selected commit `ff32b99b395b1da9cb6275da3d82263306bd7047`, Main PID `53125`, start ticks `555479`, cwd `/home/ubuntu/KORStockScan-runtime-releases/main-io-residual-20261014-ff32b99b3/src`. 계획 작성 중 같은 selector/PID/cwd/start를 다시 확인했다. 이 수치를 이후 실행 시점의 현재값으로 고정하지 않는다.
- Main bundle `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`, native family `c366914f1a2a76d85bceacd406e6c377f1fb32b2b50d757fb195484ab783ff8c`; source/publication 10/13, effective 10/14. 실제 PID 소비 확인과 자연 주문/수익은 별개다.
- 원본 점검: [결과와 원천 경계](../../tmp/nonfixed-submission-inspection-20261014/result.json), [시도별 입력·응답](../../tmp/nonfixed-submission-inspection-20261014/main-attempts.json), [비고정 관측](../../tmp/nonfixed-submission-inspection-20261014/probe-summary.json), [원 응답 outbox](../../tmp/nonfixed-submission-inspection-20261014/outbox-evidence.json), [native lifecycle](../../tmp/nonfixed-submission-inspection-20261014/native-lifecycle.json). `tmp` 자료는 로컬 점검 증거이며 자동화 입력이 아니다. 구현 전 필요한 최소 fixture를 기존 테스트 owner에 고정하고 원 경로·offset·hash를 보존한다. 원천 소실 시 세부 재현은 `source_gap`으로 남긴다.
- [준비·전달 계획](main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md)의 wakeup/readiness/lease, [잔여 병목 계획](main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md)의 mixed branch 순환, [I/O 보완](main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md)의 bounded reader는 완료된 기반이다. 해당 구현 전체를 다시 열지 않는다.
- [REST·입력 축소 계획](main-rest-excessive-call-removal-and-input-quality-relaxation-plan-2026-10-13.md)의 CR7은 초기 Main/zero-base만 `reduced_completed_v1`을 사용한다. 이미 승인된 1page discovery·raw same-day 완성봉·선택 입력 unknown을 보존한다. 이번 성능 비교의 전체 범위는 **현재 승인되어 운영 중인 모집단**이며, 과거 전시장/수정주가/선택 외부조회 복원을 뜻하지 않는다.
- 변경 위치는 기존 `src/engine/scalping`, `src/engine/monitoring`, `src/scanners` 및 현재 Main caller·기존 테스트다. 새 `src/engine` root 모듈이나 별도 상시 worker/보고 원장을 추가하지 않는다. 기본 작업공간의 다른 미완료 변경을 포함하지 않고 구현 시 최신 selected release에 다시 기준을 맞춘다.

## 2. 확인된 사실과 미확정 원인

| 구간 | 고정된 사실 | 해석 경계 |
| --- | --- | --- |
| 비고정 discovery | 28회 cycle, 고유 claim 74 = 완료72 + 진행2 | 전체 시장 탐색 분모가 아니다. gainers는 기존 page limit에 도달한 panel이다. |
| 완료72 | 정상 원천·패턴 불일치22 + 원천 부족10 + 삼성전자 기존 target 충돌40 | 충돌40은 callback에서 물리 관측 슬롯 취득 전에 종료된다. 슬롯 장기 점유나 시장 기회 손실40으로 계산하지 않는다. |
| 비고정32종목 | 22개는 선택 branch FALSE·feature complete·source censor0. 나머지는 마지막 체결 stale9, 관측 censor1 | 32개 모두 exact 0B/0D 수신과 identity/duplicate/conflict 계측을 확보했다. 수신 사실만으로 stale10을 정상 no-match로 바꾸지 않는다. |
| 비고정 후속 | machine-only 평가·보조 호출·Main 편입·제출0 | native 관측과 후속 mechanistic assessment를 구분한다. no-pattern22는 관측된 범위의 결과이며 정책의 수익성 부재가 아니다. |
| 관측 대기 | 완료32 모두 원 residence150초. 전체5/long2. 대기671.16~2956.12초 | 이전 PID에서 이어진 대기가 포함된다. discovery source 나이와 다른 값이다. 11:16 누적 queue1114 중 stale692를 현재 적격 분모로 사용하지 않는다. |
| Main 비동기 시도 | 고유12, observation10 = ENTER_NOW5 + source_invalid5, 사전 계약 거부2 | trace에 action이 누락된 ENTER_NOW1도 원 observation으로 검증했다. `ai_confirmed` 반복 건수로 대체하지 않는다. |
| 보조 호출 | 실제4, 원 응답3 = PASS2 + CAUTION1, timeout1, inspected submit0 | 원 PASS와 유효 PASS, Main 수용, intent, broker submit은 각각 별도다. |
| native terminal | 64 = claimed12 + claim 전 invalidated49 + unobservable3. invalidated 수명 중앙값600.3ms | 발행된 terminal 분모이며 전체 기회 census가 아니다. 49개를 scheduler 장애나 놓친 수익으로 단정하지 않는다. |

Main12의 **최초 확인된 중단**은 `candle_stale5 + 호출 전 신호 소멸3 + CAUTION1 + 유효 PASS 뒤 신호 소멸1 + 시간예산 종료1 + PASS 근거 계약 위반1`이다. 후속 native rejection은 앞선 입력 차단과 함께 존재할 수 있으므로 합산하지 않는다.

핵심 재현 시도:

- 주성엔지니어링(036930) `aims-91ef750f7fb21d0d31b6`: 원 PASS 유효, Main의 ready membership/branch survival 소멸, 원 deadline **2.372초 잔여**. provider/JSON/timeout 오류가 아니다.
- HPSP(403870) `aims-6f2c44632e44d7fb862a`: signal→claim **1.876초**, signal→request capture **2.710초**, HTTP **2.096초** 뒤 예산 종료. 요청1회, timeout1회이며 rate-limit/과다호출 원인은 입증되지 않았다. outbox `transmission_uncertain`을 보존한다.
- 두산에너빌리티(034020) `aims-f731f9d0803ac73d76e4`: 원 PASS는 `NO_BLOCKING_RISK`와 **분기 접두어가 붙은** `observed_machine_signal`을 인용했다. validator는 공통 ID를 요구하여 `union_pass_support_invalid`. Main 재검증은 통과했으나 남은 시간24ms였다. 이 시도의 최초 중단은 근거 계약이며, 늦은 소비는 별도 성능 증거다.
- `candle_stale`5: 036930 3건, 005930 1건, 403870 1건. candle age **91.950~120.254초**, quote/tape는 fresh. 완성봉 시작시각과90초 freshness의 불일치 가능성을 원 row/clock으로 검증해야 하며, 다섯 행 모두를 사전에 오차단으로 확정하지 않는다.

## 3. 우선순위와 실행 순서

| 순서 | 작업 | 변경 성격 | 완료 기준 |
| --- | --- | --- | --- |
| P0 / B0 | 정확한 요청·응답·Main terminal 집계 | 보고 계약 수리 | 원12 attempt·4 request·3 raw response·1 timeout이 같은 창에서 대사되고 missing≠0 |
| P1 / B1 | 완성봉 신선도 시각 계약 | 초기 entry source 의미 수리 | 정상 완성봉/실제 지연·결손을 구별하고 holding·quote safety 유지 |
| P1 / B2 | PASS 공통 근거 계약 | prompt/input/schema/validator 정합성 | 공통/분기 근거 역할 일치, 잘못된 원 응답은 계속 거부 |
| P1 / B3 | Main 인수·완료 소비 지연 | 계측 후 확인된 로컬 비용 수리 | 원5초·단일 소비·전체 현재 대상·보호 처리 보존, 기존 지연 목표 평가 |
| P2 / B4 | 비고정 대기·중복 요청 | 기존 scheduler/관측 계약 수리 | 현재 정책/슬롯/관측시간 내 중복 dispatch 감소와 공정한 배정 검증 |

B0으로 비교 분모를 먼저 확정한다. B1/B2는 각각 독립 fixture·리뷰로 닫고, B3/B4는 실제 병목 구간을 재현한 뒤 그 구간만 변경한다. 입력 의미가 달라지는 B1/B2 효과와 동작 동등 성능 변경 B3/B4 효과를 한 개선율로 합치지 않는다.

## 4. B0 — 모니터의 실제 producer 연결 수리

소유 경로: [machine observation/request/trace producer](../../src/engine/ai_engine_openai.py) → [trace projection](../../src/engine/scalping/ai_decision_trace.py) → [submission monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py) → 기존 [Sentinel](../../src/engine/buy_funnel_sentinel.py)·artifact health 소비.

1. `_reversal_provider_lineage`의 trace 시각 `created_at`을 실제 schema의 `decision_ts`, ID `ai_decision_trace_id`를 실제 `decision_trace_id`에 맞춘다. pipeline의 `ai_decision_trace_id`까지 전역 rename하지 않는다. schema별 명시 mapping으로 연결한다.
2. request에 없는 `continuous_reversal_request_binding`을 필수 join으로 가정하지 않는다. 기존 request ID/async ID/PID/start → trace의 attempt/observation hash, request payload semantic hash·prompt/envelope hash·native input hash를 검증한다. 종목/근접 시각만으로 연결하지 않는다. response 없는 timeout도 request·worker/native disposition으로 남기며 trace가 없으면 `request_unresolved`다.
3. 관측은 append 당시의 pre-call snapshot이다. observation의 `provider_called=false`로 이후 요청을 지우지 않는다. 실제 전송 시도, request 준비, raw response 수신, response 계약 유효성, 실행 재검증은 독립 필드로 유지한다.
4. fixed-watch와 scanner를 각각 보고한 뒤 명시된 전체 Main 집계를 만든다. scanner 평가0은 실제 scanner 결과일 수 있다. 이를 전체 Main 무가동으로 확대하지 않는다. 기존 `no_identified_machine_evaluation`의 cohort 표기를 점검한다.
5. 원 outbox와 trace의 raw verdict/risk codes/fact IDs를 대사한다. 두산 원문에는 분기 근거와 risk code가 있으나 trace의 raw 배열은 비어 있었다. 정규화가 원문을 덮지 않게 하고 raw·validated·effective를 구분한다. 원문/hash가 없는 행의 배열을 임의 복구하지 않는다.
6. bounded reader·현재 I/O 상한을 유지한다. 창 경계의 carry-in/out, 지연 append, 부분 마지막 줄, 회전, schema 차이, 다른 PID/date, 중복·충돌 hash를 검사한다. 필요한 bounded input을 확보하지 못하면 partial/source_gap이며 complete/0으로 처리하지 않는다. 요청/응답 window를 같은 observation cohort에 맞춰 대사한다.

수용: 고정 창의 최초 중단12·machine10·request4·raw response3·timeout1을 정확히 재현한다. valid PASS는1, raw PASS는2다. `decision_ts`를 Main commit 시각으로 사용하지 않는다. 자동화의 latest marker/partial 의미는 보존하며 알림 임계값을 낮추거나 partial을 PASS로 치환하지 않는다.

## 5. B1 — 완성봉 시각과 실제 원천 지연 분리

소유 경로: [초기 Main caller](../../src/engine/sniper_state_handlers.py)·[probe](../../src/engine/scalping/zero_base_probe.py) → [entry candle context](../../src/engine/scalping/entry_candle_context.py) → [AI market snapshot](../../src/engine/scalping/ai_market_snapshot.py) → input preflight.

1. 현 `reduced_completed_v1`은 현재 분봉을 제외하고 `now - latest_bar.dt`로 age를 계산한다. 봉의 시작/종료, expected last completed cutoff, producer receive/validation 시각, revision, route/session/date/transport epoch를 분리한다. 1분봉 시작과 종료 의미는 producer 계약과 raw fixture로 확인한다.
2. 검증된 완성봉 경로에서만 **bar close 기준 age**와 **수신·원천 연속성 freshness**를 각각 계산한다. 조회/복사 시각으로 원 자료의 freshness를 갱신하지 않는다. `age - 60` 일괄 보정이나90초 상수 증가는 사용하지 않는다. completed/current-forming, raw/adjusted, session 전체/rolling의 기존 구분을 보존한다.
3. 가장 최근 완성봉 존재·확정 cutoff·정정 revision·필수 window·route/epoch를 먼저 검증한다. 없거나 오래된 봉, 장중 단절, 미래봉, 다른 세션/route, 시계 역행, reconnect의 이전 자료는 기존 fail-closed/unknown을 유지한다. quote/tape가 fresh라는 사실만으로 candle 결손을 통과시키지 않는다.
4. minute rollover 직후 아직 확정되지 않은 봉은 기존 source readiness로 처리한다. 공백을 합성하거나 무거운 REST/현재봉/선택 MTF 수집을 복원하지 않는다. source timestamp의 의미를 입증할 수 없는 경우에는 B1 의미 변경을 적용하지 않고 결손으로 보고한다.
5. opt-in은 현재 초기 Main/zero-base reduced profile에 한정한다. holding/exit/AVG_DOWN·재가격·strict adjusted 소비자의 age/guard는 기존 계약을 유지한다. 공통 함수 변경이 이 경계 밖의 BUY/WAIT/SELL을 바꾸면 B1 수용 실패다.

검증: 분 경계 전후, :00/:29/:30/:59, 최신 정상 완성봉/한 봉 누락/수신 정지/정정/다른 epoch, 초기 세션 부족, raw/adjusted 혼합을 고정 시계로 비교한다. 원5행은 확인 가능한 input과 결손을 각각 표시한다. 허용한 B1 차이만 expected delta로 기록하고 실제 stale/quote 거부가 하나라도 통과하면 실패다. 이는 entry eligibility에 영향을 줄 수 있는 소비 계약 변경이다. Kiwoom 요청·응답 parser/FID 의미까지 변경해야 하는 경우에는 [공식 API reference gate](../kiwoom-api-data-contract.md)에 따라 당시 upstream revision·관련 파일·조회시각부터 검증하고 기록한다.

## 6. B2 — 공통 PASS 근거를 발행·검증·기록까지 일치

소유 경로: [extended union](../../src/engine/scalping/reversal_extended_union.py)의 production_request/response_schema/validate_response → [AI adapter](../../src/engine/ai_engine_openai.py) → [outbox](../../src/engine/scalping/reversal_operating_outbox.py)·trace → Main 재검증. 이전 [operating union](../../src/engine/scalping/reversal_operating_auxiliary.py) 소비가 남아 있는지는 실제 policy version으로 판정한다.

1. 공통 기회 확인 fact `observed_machine_signal`과 `<branch_ref>/observed_machine_signal`의 역할을 명시한다. 현 제공 fact와 검증식에서 두산 원 응답이 왜 거부되는지 offline fixture로 재현한다. 분기 fact가 입력에 존재한다는 것과 공통 PASS 요건 충족은 다르다.
2. **리뷰 후 구현안은 validator·projector·입력·schema 바이트를 유지하고 현재 등록 프롬프트의 역할 표현을 보완**하는 것이다. 현재 v3 registry7개/128scope는 projector hash와 봉인돼 있으므로 union 모듈 변경이나 기존 registry 덮어쓰기는 하지 않는다. 기존 auxiliary 발행 owner에서 각 프롬프트에 동일 English ASCII 공통 근거 설명을 append한 successor를 준비하고, 전체 old/new registry·scope·원천·reader hash와 원 bundle/family/정의를 봉인한 manifest로 발행한다. 공통 필수 support·ANY_MATCH·전체 assessed refs·CAUTION/VETO adverse binding은 기존 validator가 계속 검사한다.
3. 기본안의 logical/wire schema·projector·provider/model/options와 기계 bundle/pointer·원 PREOPEN/env/manifest는 유지한다. 프롬프트 변경은 새 registry hash/prompt generation으로 드러낸다. 새 발행 API는 full-scope parent CAS·정확한 고정 설명 append만 허용하며 정책 연구·새 alpha 선택과 구분되는 명시 contract-repair authority를 요구한다. 기존 reader compatibility는 원 봉인 자료의 전체 binding parity와 exact old/new code 증거로 발행한다. 원 claim은 confirmation 당시의 프롬프트를 계속 사용한다.
4. 분기 ID를 사후 strip해서 공통 fact로 승격하거나, 잘못된 PASS에 근거를 채워 통과시키거나, semantic failure 때 provider를 재호출하지 않는다. 공통 PASS 조건 자체를 바꾸는 대안은 이 기본안의 계약 수리와 구분해 별도 의미 변경으로 남긴다.
5. B0와 함께 원 response/risk/fact IDs, 검증 오류, effective WAIT, native valid/invalid를 별도 보존한다. 두산의 계약 거부와 주성의 유효 응답 이후 실행 불가가 같은 `response_invalid` 원인으로 집계되지 않게 한다.

수용: 현 두산 원 응답은 계속 `union_pass_support_invalid`, 공통 필수 ID를 포함하는 정상 fixture만 valid PASS다. unknown/중복 인용, 빈 `risk_codes`, PASS의 공통 support 누락, assessed refs 누락/분기 교체·다른 prompt generation·CAUTION/VETO 오인용은 거부한다. 정상 PASS의 빈 `contradicting_fact_ids`와 기존 계약상 허용되는 배열 공백은 보존한다. provider 없는 fixture 통과는 자연 모델 응답 개선의 증거가 아니며, 다음 실제 정상 시도의 계약 일치율과 N은 별도 관측한다.

## 7. B3 — 원5초 안의 Main 인수·완료 소비 개선

소유 경로: native lifecycle → [Main state handler](../../src/engine/sniper_state_handlers.py) → [async coordinator](../../src/engine/scalping/scanner_async_eval.py) → native commit → 기존 submit owner. 계측은 [runtime performance](../../src/engine/monitoring/runtime_performance.py)의 기존 bounded owner를 사용한다.

1. 같은 signal/attempt/PID/start에서 `native-ready → Main visit/claim → prepare queue/service → AI dispatch/pre-provider → actual HTTP → response validation/mandatory append → worker completed → Main collect/guard → intent/submit`을 결속한다. nested duration을 더하지 않고 같은 프로세스 monotonic 구간으로 분해한다. broker 단계 미도달은 해당 단계 장애0의 근거가 아니다.
2. HPSP의1.876초 claim 지연과 두산의 worker 완료 이후 늦은 소비를 해당 시각의 Main 작업·lock·COMMIT/보호 작업에 연결한다. telemetry가 없어 원인이 특정되지 않으면 작은 bounded clock 보완까지만 먼저 수행한다. HTTP2096ms를 I/O 또는 provider rate-limit 탓으로 단정하지 않는다.
3. 이미 구현된 wakeup을 중복 구축하지 않는다. 구현에서는 남은 Main WATCHING queue에 동일 generation/cache의 fixed-watch target이 있는데도 undrained completion 때문에 다음 outer pass로 돌아가는 경로를 수리한다. 그 경우에만 현재 pass의 기존 handler가 원 result를 소비하며, scanner COMMIT·orphan/이미 방문한 target은 기존 drain 경로를 유지한다. 완료 target을 WATCHING 위치 안에서 우선 방문하고 COMMIT/holding/order 위치·전체 모집단을 보존한다. Main 소유 상태를 새 worker가 변경하거나 계좌/주문/보호 처리에 재진입하지 않는다. 필수 durable append·응답 검증을 제거하지 않는다.
4. 여러 fixed/nonfixed가 함께 ready인 부하에서 기존 정상 순회·기회 identity·원 priority를 보존한다. 종목/market/candidate 범위 축소, worker/provider 동시성·quota 확대, late result 재사용, 원 event epoch/perf deadline 재생성으로 성능을 얻지 않는다.
5. 49개 claim 전 invalidation은 `기존 정상 소멸`, `동일 사건에서 입증된 Main 지연`, `경계 미관측`으로 근거가 있는 범위만 분석한다. 같은 가격 유지/단일 tick 신호의 native 생존 의미에 결함이 의심되면 별도 최소 반례로 기록한다. 이번 scheduler 수정으로 신호를 latch하거나 TTL을 연장하지 않는다. 기존 submit-drought root-cause 분류 체계를 추가 확장하지 않는다.

성능 목표는 기존 NS5/R2b를 재사용한다: **native-ready→claim p95≤250ms, signal→Main live capture p95≤1초, coordinator-ready→Main guard p95≤100ms/p99≤250ms**. 원5초·정상 종료·보호 처리·전체 scope는 필수 불변 조건이다. 목표 미달/소표본은 `performance_not_established`이며 새 매매 veto나 timeout 완화 조건이 아니다.

## 8. B4 — 비고정 중복 요청과 대기 배정 보완

소유 경로: [discovery queue](../../src/scanners/zero_base_discovery_queue.py) → [discovery runtime](../../src/scanners/zero_base_discovery_runtime.py) → [Main callback](../../src/engine/kiwoom_sniper_v2.py) → probe/lease → result/ACK.

1. 같은 existing target/owner generation이 유지되는 동안 삼성전자와 같은 반복 충돌을 claim 전에 defer하는 최소안을 검토한다. Main 소유의 현재 active-target snapshot을 읽고 callback의 최종 재검사를 유지한다. 영구 blacklist로 만들지 않으며 target 해제/세션·route·generation 변경 때 즉시 다시 적격 판단한다. snapshot이 오래됐거나 신원을 입증하지 못하면 종목을 제외하지 않고 기존 callback 경로를 사용한다.
2. discovery hint와 현재 source freshness·기존 retry due를 보존한다. 중복 defer는 신규 physical slot/claim 횟수·activity/gainers 소비 quota를 차지하지 않게 하되 기존 pending result/cleanup·historical conflict receipt는 유지한다. queue 전체 snapshot을 매 dispatch 다시 해시/읽거나 추가 broker/provider 조회로 active 여부를 확인하지 않는다.
3. 누적 후보/현재 same-route fresh·due 후보/long 필요 후보/짧은 branch 실행 가능 후보/진행/cleanup pending의 분모를 분리한다. `first_seen`, 기존 `residence_wait_since`, **현재 적격 대기의 시작**을 구별하고 재시작 carry-over와 source 나이를 따로 보고한다. 근거 없이 적격 대기 시작을 과거 first_seen으로 소급 합성하지 않는다.
4. 모든 실제32관측이150초였다는 사실은 현재 선택 branch의 최소 이력과 연결해 설명한다. 60초 이상의 cold history가 필요한 종목을 남은 short2슬롯에 강제로 넣지 않는다. 2026-10-15 사용자 확정으로 전체5/long3·60/150초와 mixed 짧은 branch의 빠른 admission, 긴 branch 순환, activity:gainers 기존3:1 선호·market 순환을 보존한다. 긴 배정 기아가 실제 재현될 때 기존 순환 결함만 수리한다.
5. 원32 = valid no-pattern22 + source gap10 분류를 유지한다. terminal 마지막 체결 age4.53~48.97초의9건과 censor1건에 대해 packet/receive/native ingest/quiet를 기존 receipt로 비교한다. 적은 거래와 수신 장애를 구분할 수 없으면 unresolved다. stale 허용·종료 시점 임의 연장·추가 REST/구독으로 채우지 않는다.

수용: 동일 discovery trace에서 active target 불변 구간의 반복 conflict dispatch가 제거되고 해제 후 정상 순환으로 복귀한다. physical lease·full branch 관측·필수 저장·원 deadline/단일 ACK 보존을 확인한다. 실제 관측 처리량/대기 개선은 별도 before/after로 측정한다. 충돌40 감소를 장기관측40개 증가로 환산하지 않는다. 비고정 ENTER/Main 편입 자연 표본이 없으면 해당 수용은 pending이다.

## 9. 검증·성능·발행 중단 기준

### 9.1 테스트와 계측 계약

| 범위 | 기존 테스트 owner 및 필요한 반례 |
| --- | --- |
| B0 | [submission monitor](../../src/tests/test_submission_bottleneck_monitor.py), [AI trace](../../src/tests/test_ai_decision_trace.py): exact ID/hash, request-only timeout, raw/valid PASS, wrong PID, 다른 schema/창, truncate/회전·중복 |
| B1 | [entry candle](../../src/tests/test_entry_candle_context.py), [market snapshot](../../src/tests/test_ai_market_snapshot.py), [zero-base probe](../../src/tests/test_zero_base_probe.py): close/cutoff/receive 구분, 실제 stale, reduced/strict·holding 격리 |
| B2 | [extended policy](../../src/tests/test_reversal_extended_policy.py), [AI transport](../../src/tests/test_ai_engine_openai_transport.py), AI trace: 공통/분기 fact·sealed hash·raw projection·semantic rejection과 native invalidation 분리 |
| B3 | [async eval](../../src/tests/test_scanner_async_eval.py), [entry bridge](../../src/tests/test_scanner_async_entry_bridge.py), [native claim](../../src/tests/test_native_signal_claim_diagnostics.py): 원4.999/5.001초, result 교체/중복·late callback, wakeup race·보호 처리 경합 |
| B4 | [queue](../../src/tests/test_zero_base_discovery_queue.py), [runtime](../../src/tests/test_zero_base_discovery_runtime.py), [Main attach](../../src/tests/test_zero_base_main_attach.py): active→해제·unknown snapshot, mixed/long 공정성, stale hint·원 lease·late/duplicate ACK·재시작 |

각 새/변경 지표는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언한다. 역할은 `funnel_count/source_quality_gate/runtime_scheduler_latency`, 권한은 `report_only`, 창은 `exact PID/start/route/session/generation + carry-in/out`, 표본은 row 대사에 별도 경제 floor 없음이다. source gap/소표본 성능·경제성은 null/미입증으로 남긴다. threshold/provider/order·독립 정책 승격은 금지 용도다.

주 지표는 B0 `exact_attempt_join_gap_count`, B1 `unexpected_source_admission_delta_count`, B2 `invalid_auxiliary_response_accepted_count`, B3 `native_ready_to_claim_ms`·`coordinator_ready_to_main_guard_ms`, B4 `redundant_active_target_dispatch_count`와 `eligible_queue_wait_seconds`다. source gate는 원 hash/PID/attempt 또는 claim/lease 일치와 해당 창 coverage이며, 충돌·결손이 있으면 분포/개선율을 확정하지 않는다. B1의 허용 delta는 원천 의미가 입증된 행만 별도 명세하고 목표0은 그 명세 밖의 변화에 적용한다.

### 9.2 비교와 종료 조건

- 원12시도·32관측을 재현하는 최소 frozen fixture와 충분한 입력의 정상 fixture를 분리한다. 원 응답/원 시계를 실제로 재호출하지 않는다. B0 집계 창을10분으로 유지한 실행과43분 점검 전체를 같은 분모로 비교하지 않는다.
- 다른 성능 변경의 기존 검증은 동일 baseline/candidate **교대3회**: fixed5+nonfixed5(긴2), 동일 panel·source/input rate·policy 및 COMMIT/holding/exit/account/필수 append 부하를 사용한다. B1/B2 의미 변경은 별도 fixture의 명시 delta로만 허용하고, B3/B4 성능 비교에서는 같은 소비 계약으로 고정한다.
- wall/CPU/RSS·worker/thread·물리 REST·WS churn·read/hash/decode bytes·lock hold/wait·Main 지연·original deadline miss·누락/중복·branch coverage·cohort 대기를 보고한다. component/local 대역 부하와 실제 전체 Main 검증을 구분한다. cold/warm 분리, 반복150초 관측 비용은 제외하지 않는다.
- B0/B4 수리로 reader·물리 요청·worker/slot 한도가 증가하면 중단한다. 단, 2026-10-15 사용자가 확정한 장기 관측2→3개는 이 제한의 명시 예외이며 전체 physical probe5개·worker5개는 유지한다. 동일 전체 Main/보호 부하 비교에서 CPU/RSS/I/O/COMMIT·보호 경로 p95가 모든 pair에서 악화되면 성능 변경 발행을 보류한다. 단일 helper 비용은 별도 원가로 공개하고 전체 Main 비교를 대체하지 않는다. 전체 실행 표본이 없으면 성능 주장은 보류하며, 정확한 결과 소비·출처 보존의 검증된 계약 수리와 구분한다. 변동/귀속 불가도 개선 확정으로 표시하지 않는다. 단순 warning은 자동 거래프로세스 재기동을 뜻하지 않는다.
- 임의 scope 축소·unknown→FALSE·필수 저장 생략으로 얻은 속도 개선은 실패다. B1/B2에서 명시한 계약 차이 밖의 전략/guard 변화, 중복 claim/provider/intent, 원 예산 증가, custody 침범, source freshness 허위 갱신, cleanup 누락은 즉시 수용 실패다.
- 자연 수용은 기존 정규5분 연속3슬롯과 다음 실제 정상 attempt를 사용한다. 시행 날짜/시각은 **승인된 실제 적용 이후**로 체크리스트 owner가 정하며 지나간 슬롯을 재사용하지 않는다. small N의 p99/timeout률을 일반화하지 않는다. 자연 표본 없음은 pending이고 코드 수리 완료를 부정하거나 경제성/실주문 시험을 추가 요구하지 않는다.

## 10. 구현 인계·되돌림·문서 리뷰

1. 후속 구현은 최신 selected commit/PID·소비자·기존 작업 diff를 다시 확인하고 해당 baseline에서 격리한다. B0→B1/B2→B3/B4 순으로 `구현 → self review → 보완 → 재리뷰 → 해당 pytest/compile → diff 검사`를 닫는다. source/prompt 계약 hash 변경을 숨기지 않는다.
2. 현재 실행 owner는 새 ID를 만들지 않고 유지한다. `AuxiliaryCircuitRecoveryRepair1012`는 B0/B2/B3의 자연 request→response→Main/submit 대사, `NonfixedDispatchReadinessReview1012`는 B0의 비고정 분모/B4, `DirectFamilySourceRepairMainMechanisticEntry`는 B1 및 관련 source 계약 수리, `DirectFamilyPreopenPolicyHandoff`는 후속 승인 범위 안의 릴리스/기동 인계를 소유한다. B1 진단에 현재 장후 실행창을 수동 장중 실행 권한으로 사용하지 않는다.
3. 문서 계획 자체는 source·prompt·policy 선택·cron·env·lock·provider·주문·배포·재기동을 실행하지 않는다. 실제 후속 동작은 이미 존재하는 승인과 당시 요청의 구체 범위를 적용한다. 중복 승인 절차를 만들지 않는다.
4. 후속 배포가 허용되면 검증된 release와 affected code/registry/prompt/schema pin의 호환성을 묶어 publication/selection/준비/실제 PID 소비를 각각 확인한다. 완료된 장후 전체 보고를 재생성하지 않는다. raw-response 개선·자연 편입·실제 submit/fill/terminal·비용 후 성과는 각각 별도 결과다.
5. 결함 발견 시 해당 candidate 발행을 중단하고, 배포 후에는 기존 안전 절차 안에서 **변경된 소비자와 계약이 함께 맞는 검증된 Main-only 조합**으로 되돌린다. sealed prompt를 코드만 역행하거나 과거 PASS/claim을 재생하지 않는다. episode/widget executor 복원, retired 보유 채택/청산, operator veto 제거는 되돌림 대상이 아니다.

문서 리뷰에서는 다음을 재확인한다: (a) 캔들5건을 검증 전에 오차단으로 확정하지 않음, (b) 두산 raw support가 비어 있다는 trace 오표현을 원 응답과 분리, (c) 비고정 conflict40의 물리 슬롯 영향 과장 금지, (d) native49를 확정된 유실 기회로 계산하지 않음, (e) 기존 scope·감축 승인·성능 목표·stable ID 보존, (f) 코드/배포/자연 증거/경제성의 별도 종료.

문서 검증: 변경 문서2개의 로컬 링크72개 결손0, 관련 stable ID4개 각각 현재 parsed owner1개, 원 task header/Due/Slot/TimeWindow 및 AUTO 영역 byte 불변을 확인했다. print-only parser는 exit0·총25항목을 반환했으며 다른 참조 문서의 기존 항목을 이번 실행 owner로 채택하지 않았다. `git diff --check`와 새 문서의 공백/구조 검사를 통과했다. 리뷰에서 정상 PASS의 빈 adverse 배열 허용, B1/B2의 의도된 계약 차이와 성능 parity 분리, 공식 API reference gate를 보완했다. 최종 문서에도 동일 검증을 재실행한다. 검증 로그는 로컬 `tmp/nonfixed-submit-plan-review-20261014`에 보존한다. 코드 시험·실제 provider/주문·보고 재생성·배포/재기동·외부 sync는 미실행이며 실제 개선 효과는 후속 검증 대상이다.

## 11. 후속 승인 구현의 리뷰 보완

후속 사용자 요청은 “개선계획 리뷰 및 보완”, “계획을 구현하고 코드리뷰 후 수정보완 완료시 배포 및 재기동 승인”이다. 이 요청을 이번 B0–B4 구현과 검증된 code/contract-repair 발행·배포·Main 재기동 권한으로 기록한다. 이전 문서 작성 단계의 미실행 기록은 그 시점의 역사다.

- B0의 frozen 재현은 원 machine10/attempt12/request4/HTTP4/raw3/timeout1/rawPASS2/validPASS1을 대사했다. 과거 raw 배열 provenance가 없는3행은 결손을 유지한다. raw adapter는 composer 전에 원 응답 hash/verdict/risk/fact/confidence를 보존하고 trace에 presence/truncation을 전달한다. validator·후속 local 예외에서도 request/PID/hash 연결을 유지하며 수신 후 local 결함을 provider transport 실패로 계수하지 않는다. 기존 recovery ticket 정리와 WAIT는 유지한다.
- B1은 bar-open age를 보존한 채 증명된 reduced entry만 close/cutoff/원 수신 시각으로 판단한다. WS 최신 승인 봉의 현재 observer epoch·revision/hash·watermark·fresh transport를 확인한다. source 조회 이후의 capture는 측정한 로컬 monotonic 소요만 반영하며 원 source receive·entry deadline을 갱신하지 않는다. 미래 watermark·분 경계 결손·holding/strict 계약을 반례로 검증한다. 역사5행은 증거 없는 오차단으로 복원하지 않는다.
- B2는 설명 append만 허용한 새 registry/manifest/overlay를 기존 auxiliary owner의 lock/CAS로 발행한다. 독립 리뷰에서 runtime manifest 검증의 원자료 반복 hash와 rollback에 남는 issuance field를 발견했다. 파일 digest만 기존 signature-bound bounded cache로 재사용하고 매번 semantic/binding 검증을 유지하며, 발행 전 full 검증·변조/회전 검출을 보존한다. 되돌림은 원 manifest를 역사 참조로 남기고 활성 발행 field를 제거한다.
- B3은 coordinator ready 시각을 retained map의 잠금 안 publication 경계에서 기록한다. worker 평가 완료→coordinator poll/ready 지연을 별도 보존해 빠른 ready→guard 수치로 앞선 대기를 숨기지 않는다. 원5초·exact result·모든 Main/native/quote/account/order guard를 유지한다. baseline bridge 시험의 이미 퇴역한 사전 capacity prefetch 기대값도 현재 승인된 lazy-demand 계약에 맞췄다.
- B4는 현재 target snapshot을 readiness callback 완료 시각에서 검증한다. callback 진입 이전 clock으로 내부 observed stamp를 미래값이라 거부하는 결함을 보완한다. 중복 defer가 claim/rotation/physical lease를 소비하지 않으며 actual callback/worker의 기존 active-target 재검사는 유지한다. 임의 종목 제외·long/short 한도 변경은 없다.

3쌍 고정5/비고정5 및 holding/order component 비교에서는 완료 target 방문이9번째→1번째로 바뀌고 전체12개·보호 위치가 유지됐다. helper p95는 약3.7→8.6µs로 늘었다. 이 추가 약5µs 비용을 숨기지 않으며 전체 Main CPU/I/O/guard 지연 개선은 아직 `performance_not_established`다. 실제 전체 부하가 모든 pair에서 악화되면 기존 종료 기준으로 수리 조합의 성능 변경을 재검토한다.

릴리스 검증과 실제 배포 결과는 후속 [구현 리뷰](../audits/main-nonfixed-submit-bottleneck-implementation-review-2026-10-14.md)와 `data/report/main_nonfixed_submit_deployment/2026-10-14`의 봉인 자료로 기록한다. 코드 source pair·sealed prompt generation·문서 publication·실제 PID 소비·자연 성능·경제성은 각각 대사한다.

## 12. 배포 후 수용과 남은 source 계약

13:05:27 기존 Main 정상 종료·선택,13:07:20 ordered transition PASS를 확인했다. [최종 소비 검증](/home/ubuntu/KORStockScan/data/report/main_nonfixed_submit_deployment/2026-10-14/postdeployment-verification.json)에 릴리스·PID·원 native policy/PREOPEN/env/prepared byte 보존·128scope·별도 auxiliary generation과 원문 source hash를 기록했다. 기동13:06:54의 strict checklist 경보는13:07:11 소비 영수증 이전 상태였고, 이후 원 snapshot의 현재 PID 검증으로 recovered_late에 복귀했다. 과거08:49:10 지연 복구 이력은 보존한다.

`submission_bottleneck_monitor.partial`은 유지한다. 원10/13 entry_split 보고서459,131,089B는 현재8,388,608B consumer 제한을 넘는다. 후보3938B 정책은 runtime_apply_allowed=false·bucket0이며 실제657B operator incumbent과 분리된다. 해시-only storage/reuse receipt나 작은 Markdown으로 전체 보고서의 의미 검증을 대신하지 않는다. scanner 평가 표본 부재도 snapshot의 cumulative decode/tail/cache/raw generation 완전성 증거가 없으므로 무조건 valid_empty로 바꾸지 않는다. fixed 표본을 scanner 평가로 대입하지 않는다.

후속 closure owner는 기존 `DirectFamilySourceRepairEntrySplit`다. producer가 native 원 report/policy/generation/source SHA에 묶인 작은 immutable observation projection을 발행하고, 기존 monitor가8MiB 내에서 읽어 source/economic blocker·비설치 후보·현재 incumbent을 각각 보존해야 한다. source/hash/부분 tail/회전 충돌은 실패로 남긴다. 기존 `NonfixedDispatchReadinessReview1012`는 scanner source completeness receipt와 실제 승인 이후의 자연 판정 표본을 대사한다. 이 추가 경계 진단은 대형 보고 재생성, 읽기 한도 확대, alert suppression 또는 신규 매매 권한을 실행하지 않았다.

정규13:10/13:15/13:20의 새 릴리스 보고 실행을 관측했다. 최초 cold validation97파일/약11.60GB/36.45초와13:20 warm full hash0회·3.36초 및 해당 실행 physical read약49.7MB를 구분한다. 원 자연3슬롯 실행은 전체 source 검증·기계/보조 실제 판정·p95 목표·비용 후 성과의 완료가 아니다. 최신 봉인 health13:26:54는 resource PASS/I/O wait12.19%, postclose_finalization recovered_late다. 전체 Main 성능은 계속 performance_not_established다.


## 13. 2026-10-15 사용자 확정 — 장기 슬롯3 및 대기 계측 연결

- 장기 관측 슬롯은2→3개로 확정한다. 전체 physical probe/worker5개와60/150초 원 deadline, 종료 ACK·동일 lease 귀속, mixed 짧은 분기와 source/market 순환을 유지한다. 이는 관측 배정 한도만 변경하며 Main 보유·주문 수량 cap이나 broker 권한을 바꾸지 않는다.
- 사용자의 지시로 이 변경을 위한 별도 적용 전 용량 비교,2대3 부하실험, 추가 승인/경제성 확인은 실행하지 않는다. §9.2의 교대 성능 비교를 이 확정 변경의 적용 조건으로 재도입하지 않는다. 요청된 코드 리뷰·보완·기능 회귀·compile·문서 parser 검증은 수행한다.
- `probe_claim_eligibility`, `probe_residence_deferred`, active-target snapshot 상태/세대, 재시작 복원 수를 `zero_base_discovery_cycle`과 `zero_base_probe_dispatch_cycle` 양쪽에 전달한다. 현재 적격 대기시간은 dispatch 관측 기준이며 과거 first_seen으로 소급하지 않는다. 기존 PID/경로/시각과 report-only 권한을 유지한다.
- 실행 owner는 `NonfixedDispatchReadinessReview1012`를 유지한다. 적용 후 자연 관측·Main 편입 및 실제 제출/경제성은 기존 owner에서 별도로 기록하며 이번 코드 완료를 자연 성공으로 대체하지 않는다.
