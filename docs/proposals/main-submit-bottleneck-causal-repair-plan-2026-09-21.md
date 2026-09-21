# 메인 제출병목 인과 복원·정상 제출 경로 검증 상세계획

- 상태: **확인된 코드 결함 구현·반복 리뷰·후속 승인 배포 완료, 자연 수용 OPEN**. 판정 revision/경제성 이력, 제한적 large-sell RECHECK 연결, 후보 admission 사유와 원본 입력 로그를 기존 owner에 구현했다. 후속 사용자 배포/재기동 승인으로 기존 WS 배포를 보존한9e828ab85/main PID244168에 인계했다. [구현·검증·운영 잔여 기록](../audit-reports/2026-09-21-main-submit-causal-repair-review.md). 전체 health·자연 제출·비용 경제성 및 미기록 과거 인과는 별도 OPEN이며 원격 push·수동 주문·안전 기준 완화는 하지 않았다.
- 최신 후속 승인 배포: §4.5 국소 돌파 의미·§4.6 최종 입력 freshness 연결 및 §6.1 비진입5초를 반복 리뷰·보완하여 **9e998bddd / 메인 PID280948 / 15:55:30 기동**으로 인계했다. 최신 WS/P2 `4914977fd` 기반을 보존했다. 배포본865 PASS, 정책 인계 PASS,15:55:38 health7/7 PASS. 자연 수용·비용/holdout 검증은 별도 OPEN이다. [최종 배포 기록](../audit-reports/2026-09-21-main-submit-causal-repair-review.md#후속-승인--국소-돌파stale-최종-배포와-재기동).
- 주 실행·자연 검증 owner: [당일 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 `SubmissionBottleneckMonitorNatural0921`. WS 전송·P2/P3는 같은 checklist의 `KiwoomCommonHealthOpportunityCostAcceptance0917`, 비용 경제성은 `DirectFamilySourceRepairMainMechanisticEntry`를 유지한다. 새 중복 OPEN을 만들지 않는다.
- 목표: 자금 결손 경보를 없애는 것이 아니라 **신선한 입력에서 기계판정을 통과한 동일 시도가 기존 안전장치 아래 정상 제출 경로에 도달하는지 입증**한다. 합법적인 BLOCK/RECHECK·위험 차단은 실패율을 낮추기 위해 제거하지 않는다.
- 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [기존 제출병목 수리 기록](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md), [공유 WS 개선 계획](widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md). 본 계획은 main-only이며 위젯·에피소드·수동 보유 주문 owner를 변경하지 않는다.

## 1. 진단 기준선과 미확정 사항

다음은 **2026-09-21 13:50 산출물, 13:20:11–13:50:11 KST 평가 95건**에 대한 진단이다. 이후 latest 파일이 갱신되면 동일 숫자를 현재 상태로 인용하지 않는다. 메인 당시 release=`4b3b4080c`, PID=`174887`, 재기동12:57:40. 최신 구현 착수 때 selection·PID/cwd·정책 영수증을 다시 확인한다.

| 단계 | 확인된 사실 | 해석/남은 질문 |
| --- | --- | --- |
| 식별 | 감시기의 최근10분 식별156 event, 누락0 | 평가95건과 다른 창·분모. 식별자 누락0이 판정 계약 충돌0을 뜻하지 않음 |
| 입력 | SOURCE_INVALID14: 실시간 provenance/freshness7, 현재가 stale3, prepared snapshot 재검증2, BBO 결손1, candle quality1 | 결손·지연·venue 충돌을 서로 구분. 공급자 지연과 로컬 처리 지연의 책임 미확정 |
| 판정 | BLOCK37, RECHECK42, UNKNOWN/충돌2 | BLOCK 사유의 구조 훼손19·대량매도15는 중복 가능. RECHECK는 미세가격반응22·setup3·trigger3·필수입력부족14 |
| 실제 통과 | 원천상 ENTER_NOW2가 같은 ID의 후속 BLOCK과 합쳐져 UNKNOWN으로 표시됨 | 최종 집계0과 최초 통과0은 다르다. 재판정의 적법성과 집계 계약을 별도 검증 |
| 자금/계획 | 명시적 비진입 cache miss62, 충돌 시도에 남은 cache miss2, guard 제외16, source-invalid 비대상14, 자금/계획 source-only 연결1 | 합계95. 62건은 계좌 잔액 부족이나 주문 실패62건이 아님. 연결1건도 비용 경제성 검증은 아님 |
| 제출 | 당일 메인 report의 budget_pass/entry_armed/order_leg_sent0 | 제출 이전 병목. 브로커 장애나 이후 경로 정상 여부를 이 표본으로 확정할 수 없음 |

근거: [제출 원천](../../data/report/buy_funnel_sentinel/submission_bottleneck_source_2026-09-21.json), [감시 상태](../../data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json), [메인 funnel](../../data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-21.json), [증분 이벤트 캐시](../../data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-09-21.jsonl). 변경 가능한 latest 경로이며 원본 전체 재스캔/덮어쓰기를 지시하지 않는다.

중점 재현 표본:

- `078350 / aims-dda353eba39503b31058`: 13:39:32 ENTER_NOW 경제성 관측에 `common_guard_block:latency_state_danger` →13:39:34 보조 AI `caution`/WAIT →13:39:36 같은 ID BLOCK 경제성 cache miss →13:39:37 terminal.
- `085910 / aims-711db1287740625894bf`: **원천 재검증 정정:** 13:43:11 최초 경제성 결손은 `exact_broker_capacity_missing / kt00011_empty`다. →13:43:14 ENTER_NOW/보조 AI `response_invalid` →같은 ID BLOCK/cache miss →13:43:15 terminal. 최초 원인을 078350과 같은 DANGER로 합치지 않는다.
- 이 guard 기록은 **경제성 관측의 중단 원인**이다. 실제 제출 직전 guard가 실행됐다는 증거로 바꾸지 않는다. 보조 AI의 `caution`과 실행 지연 분류의 `CAUTION`도 서로 다른 계약이다.
- 13:36/13:37 I/O wait38.13%/38.35%, 이후 임계치 아래 회복. 메인 약5MB WS checkpoint 반복 저장·swap I/O를 확인했으나 078350의 DANGER와 직접 인과는 아직 미확정이다.

## 2. 우선순위와 기존 수정 위치

필수 수리·인계 순서는 **S0 원천 고정 → S1 판정 이력 복원 → S2 실제 지연/AI 재검증 경로 → S3 필요한 성능 수리 → S5 승인 배포·자연 인계**다. S3은 S2에서 원인이 확인된 부분만 선택하며 전체 WS P2/P3 완료를 메인 수리의 선행 조건으로 만들지 않는다. **S4는 기존 자금 연결의 조건부 검증**으로, S5 자연 관측에서 실제 진입이 제출 직전 경로까지 도달했을 때만 확인한다. 기존 자금 연결 재구현은 기본 수리 범위에서 제외하며 자금 표본 부재가 S1–S3 수리 완료·승인된 배포를 막지 않는다.

위험 차단 적정성 후속 점검은 S2의 아래 §4.1–§4.4에 포함한다. 우선순위는 **재확인 의도의 최종 BLOCK 전환 → 후보 승격/발견 지연의 최초 누락 단계 → 판정 입력/요약 로그 동일성 → failed_breakout의 차단 적정성**이다. 구현된 guard라는 이유로 경제적으로 적정한 차단이라고 단정하지 않으며, 반대로 사후 상승만으로 정상 guard를 완화하지 않는다.

| 단계 | 기존 소유 코드/산출물 | 최소 작업 | 종료 기준 |
| --- | --- | --- | --- |
| S0 | 기존 source/cache·release/PID receipt | 2개 시도 및 비교 시도의 필요한 이벤트만 고정 | 시간순서·동일성·원본 참조 검증, 미래 증거 소급0 |
| S1 | [state handlers](../../src/engine/sniper_state_handlers.py), [Sentinel](../../src/engine/buy_funnel_sentinel.py), [monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py) | 최초 판정·재검증·terminal·경제성 관측 연결 | 정상 전이와 실제 충돌을 분리, 최초 ENTER_NOW 보존 |
| S2 | [latency monitor](../../src/trading/entry/latency_monitor.py), [entry policy](../../src/trading/entry/entry_policy.py), [setup/최종 판정](../../src/engine/scalping/entry_setup_evidence.py), 기존 AI·scanner census | DANGER/AI 실패·재평가, 재확인→BLOCK, 승격 누락, 입력/로그 및 위험 차단 적정성 검증 | 실제 main 경로의 의도/최종 결과 정합성 및 최초 차단 근거 확인. SAFE/CAUTION 정상 경로·DANGER 및 주문 안전 유지 |
| S3 | [WS writer](../../src/engine/bd_fbuy_accum_pre_scanner.py), [WS receiver](../../src/engine/kiwoom_websocket.py), [shared reader](../../src/trading/market/shared_ws_snapshot.py), [machine consumer](../../src/trading/market/micro_confirmation.py) | 중복 파싱/불필요 복사부터 감축, 필요 시 저장 표현 개선 | 동일 자료·판정 보존, 실제 비용 감소·지연 비악화 |
| S4 조건부 검증 | 기존 `_observe_entry_economics_before_ai`·계좌 캐시/준비 worker·sizing owner | 자연 진입이 제출 직전 경로에 도달할 때 기존 연결 확인; 새 결함 재현 때만 해당 부분 추가 수리 | 정상 연결 또는 정확한 차단 사유 확인. 대상 표본이 없으면 미관측으로 별도 인계하며 S1–S3 완료를 막지 않음 |
| S5 | 기존 release launcher·정책/PID receipt·정기 Sentinel | 범위 승인 후 immutable 인계·정상 스케줄 관측 | 코드/배포/소비/제출/체결/경제성을 각각 판정 |

새 daemon·broker probe·중복 report producer·engine-root 모듈을 기본 해법으로 만들지 않는다. 기존 함수·테스트·report 필드 확장이 우선이며 새 파일이 불가피하면 구현 전에 location gate와 단일 owner를 확정한다.

## 3. S0/S1 — 같은 시도의 판정 전이를 잃지 않게 수리

1. 구현 시작 때 파일 stat/시각·source commit·PID·정책 hash를 확인하고, 작은 해당 이벤트 묶음과 hash/추출 범위만 수리 기록에 보존한다. 큰 JSONL은 manifest/offset/ bounded tail 우선이며 동일 범위를 반복 읽지 않는다.
2. 동일 scanner promotion·evaluation attempt 아래 최초 기계판정, AI 요청/응답, 최신 입력 재검증, terminal, 자금 관측의 순서를 복원한다. 각 단계의 snapshot/source hash·원 수신시각·판정 owner를 연결한다.
3. producer가 별도 입력으로 재평가했으면 기존 parent를 보존하고 명시적 revision/child 연결을 최소 추가한다. 같은 ID를 새 ID로 치환해 과거 경제성·terminal 연결을 끊거나 평가/제출 수를 부풀리지 않는다.
4. 단순히 마지막 값을 취해 충돌을 숨기지 않는다. 근거가 있는 정상 전이만 순서대로 인정하며, 같은 revision의 상반된 판정·역순·부모/원천 미결합은 contract gap으로 남긴다. 구형 이벤트가 이를 증명하지 못하면 과거 충돌을 자동 recovered로 바꾸지 않는다.
5. 기존 Sentinel에 최초 ENTER_NOW 수, 최종 action, 최종 차단 단계/사유, revision chain 유효성을 전달한다. 경제성 증거도 revision별로 연결해 최초 DANGER가 후속 cache miss로 덮이지 않게 한다. 기존 consumer와의 호환성을 테스트하고 필요할 때만 cache schema를 변경한다. schema 변경 시 제한된 migration/증분 전환 또는 명시적 gap을 택하며 장중 대용량 전체 재구축은 별도 비용 검토 없이 실행하지 않는다.
6. 상위 `UPSTREAM_AI_THRESHOLD` 표시는 legacy stage명/score만으로 보조 AI를 원인으로 확정하지 않도록 실제 machine owner·AI 호출 여부와 대사한다. 기존 분모·원본·경보 유예를 보존하고 새로운 병목 taxonomy를 계속 추가하지 않는다.

완료: 위2개 fixture에서 ENTER_NOW→AI→재검증 BLOCK의 순서와 각각의 자금 관측 사유가 보존됨. 중복 이벤트를 넣어도 고유 attempt/submit 수 불변. 진짜 충돌·수신 누락·출처 불일치는 계속 차단됨.

## 4. S2 — 지연/AI/재검증의 실제 차단 원인 확인

- 기존 자료로 signal 생성, WS 원 수신, snapshot 생성/소비, AI queue/start/end, 재검증, 최종 제출 guard 시각을 먼저 대사한다. 없는 시각은 추정값을 채우지 않고 기존 telemetry에 필요한 최소 필드만 추가하는 구현안을 낸다. 경과시간은 monotonic, 원천 사건시각은 명시 timezone으로 비교한다.
- DANGER를 만든 `quote_stale`, WS age/jitter, 주문 RTT, spread 입력과 실제 적용 config를 해당 평가 시점으로 재현한다. 기본값·잘못된 단위·예전 주문 RTT/다른 route 재사용·clock skew·대기열 지연인지 확인한다. 단순 DANGER 라벨이나 I/O 경보의 시간 근접성만으로 원인을 확정하지 않는다.
- 로컬 처리 지연은 queue/lock/serialization/동기 I/O owner에서 줄인다. 공급자 늦은 체결은 수신시각 갱신으로 신선하게 위장하지 않으며 정상 신규 자료를 기다린다. 분봉 venue conflict는 원 요청·응답·변환·소비 route를 추적하고 다른 시장 값을 임의로 같은 값으로 취급하지 않는다.
- AI `response_invalid`는 저장된 응답/검증 사유로 timeout·불완전 응답·schema·파서 결함을 구분한다. 재현에는 mock/보존 표본을 쓰며 유료 호출을 반복하지 않는다. 모호한 응답을 PASS로 바꾸거나 timeout/모델/provider를 바꾸지 않는다.
- AI `caution` 처리와 첫 WAIT 후 재평가가 현재 정책 계약과 일치하는지 확인한다. **실행 지연 CAUTION은 기존 slippage 통과 후 normal path**, AI caution은 보조 판정 계약을 따른다. 둘을 혼용해 제출을 허용/차단하지 않는다.
- 패턴·점수 조정은 본 수리에서 제외한다. 신선한 입력에서도 단일 bounded-tunable이 유일 원인으로 확인된 경우에만 기존 postclose/명시 override owner로 근거를 인계한다.

완료: 두 시도에서 관측 guard와 실제 terminal 원인의 관계를 설명할 수 있고, 재현 테스트가 잘못된 입력/연결과 정상 차단을 구분한다. 과거 세부 값 미기록이면 해당 과거 인과는 unresolved로 보존하고 다음 자연 평가에서 계측한다.

### 4.1 재확인 의도가 실제 main 최종 판정에서 보존되는지

- 확인 사실: 13:20:11–13:50:11 BLOCK37건의 저장된 exact payload를 대조했다. 아래4건은 setup=`WAIT_CONFIRMATION`, reason=`LARGE_SELL_EXHAUSTION_RECHECK`이나 assessment=`BLOCK`이었다. 해당 `entry_setup_evidence.py` 작업본/당시 운영4b3b4080c 파일 hash는 일치했다. 결과 불일치는 확인됐지만 어떤 계약이 최종 우선하는지는 active main 계약에서 확정해야 한다.

| 종목 | 평가 시각(KST) | 고정 재현 ID |
| --- | --- | --- |
| SFA반도체(036540) | 13:22:47 | `aims-66d3e5f8c1c07233e752` |
| 디아이(003160) | 13:23:44 | `aims-c64ab5cea08621d3a5e5` |
| 예스티(122640) | 13:41:25 | `aims-382eefbf0d05278cb7fa` |
| 엑셈(205100) | 13:47:29 | `aims-4426caf5c08d6fe53215` |

- 근거: [저장된 판정 payload](../../data/ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl)의 `label_context.snapshot_id`→`source.exact_payload/setup_evidence/assessment`. 필요한4행·원본 hash만 추출해 구현 fixture로 사용하고 개인정보/계좌 식별자는 필요한 범위에서 비식별화한다.
- 확인 경로: `build_entry_setup_evidence`는 유효 source·유효 setup·단독 large-sell blocker·structural edge·confirmed volume·tail fragility 없음일 때 재확인으로 분류한다. 하지만 `_risk_fact_bindings`는 `hard_blocker:*`를 `STRUCTURE_INVALIDATED`에 묶고 `mechanistic_entry_action_core`는 그 위험을 BLOCKING으로 처리한다. `mechanistic_entry_policy_decision`→main state handler→terminal→Sentinel까지 추적해 재확인 의도 유실인지 명시적 상위 차단인지 판정한다.
- 테스트 공백: [기존 테스트](../../src/tests/test_entry_setup_evidence.py)의 `test_large_sell_only_blocker_becomes_recheck_not_probe`는 setup과 `compose_entry_decision`의 WAIT/recheck를 확인한다. **실제 main의 `mechanistic_entry_action_core`/`mechanistic_entry_policy_decision`까지 검증한 테스트는 아니다.** 기존 PASS를 main 경로 정합성 증거로 대체하지 않는다.
- 검증/수리 조건: active 계약이 위 조건의 재확인을 요구하면 새 연결 회귀로 현재 BLOCK을 재현한 뒤 그 조건에만 RECHECK 의도가 전달되도록 최소 보완한다. 명시적 상위 BLOCK이 의도라면 모순된 setup/진단 표시를 정합화한다. 코드상 이름 `hard_blocker`만으로 변경 권한을 판단하지 말고 Plan Rebase의 hard safety와 전략 판정 역할을 대조한다. 안전 완화·전략 변경이 필요하면 별도 권한/계획으로 인계한다.
- 종료 기준: source→setup→risk binding→최종 main action→재확인 대기/후속 재평가→terminal/report가 같은 입력 세대로 설명된다. 조건부 RECHECK는 즉시 ENTER_NOW/BUY/probe 허용이 아니며, 매도 위험 해소·신선한 재판정 없이 진입하지 않는다. 복수 blocker, source-invalid, failed_structure, spread/계좌/주문 안전이 함께 있으면 기존 차단을 보존한다.

### 4.2 상승 미진입의 후보 승격·발견 경로 검증

- 기준선은 [12:00 market census](../../data/report/market_opportunity_census/market_opportunity_census_2026-09-21.json)의 `liquid_common/top_20/forward_exact`, KRX·symbol_master_status=verified123구간이다. 그중1200초 horizon의 비용 모형 결과 양수35구간/26종목에서 candidate_not_promoted20, late_discovery9, entry_decision_rejected3, scanner source guard1, runtime attach gap1, AI trace gap1을 확인했다. 이는 관측 표본의 분류이며 당일 전체·현재 배포 효과·실현손익이 아니다.
- **사유 정정:** 미승격20건의 `candidate_evaluated` 첫 사유는 모두 `returned`다. 별도 `source_seen`에는 returned8/partial_adapter_return8/reserved_full3/cooldown1이 있다. 반환 성공/부분 반환은 종단 탈락 이유가 아니며, source_seen 사유를 같은 시도의 최종 차단으로 전용하지 않는다.
- 기존 [scanner source census](../../src/scanners/scanner_source_census.py)와 [market census](../../src/engine/monitoring/market_opportunity_census.py)를 재사용해 `source capture → candidate evaluation → slot/admission → promotion → runtime attach → heavy evaluation → machine decision`의 첫 미도달 단계를 대사한다. capture/cycle·종목·venue/session·promotion ID·정책/프로세스 세대·원 시각을 연결하고 다른 재승격 시도를 끼워 넣지 않는다.
- 미승격20건은 반환→실제 admission disposition/제외 사유를 복원한다. 없으면 명시적 instrumentation gap으로 남기고 기존 receipt의 누락 필드만 보완한다. 늦은 발견9건은 source 도착 지연과 대기열/선정 지연, 이미 종결된 과거 기회의 재등록을 구분한다. slot/cap/cooldown/상승률 제한을 늘리거나 우회하지 않는다.
- 오전 거절3구간의 동방메디컬·삼현·한양디지텍은 `completed_bars_missing`이 공통이었다. 12:39 fee046b21 완료봉 전달 수리 전 표본으로 보존하고 현 세대의 재발 증거가 없으면 그 수리를 재구현하지 않는다. 삼현은 census상 목표 관측이 해당 판정 전에 있었으므로 판정으로 인한 놓친 수익으로 계상하지 않는다.
- 종료 기준: 각 표본의 최초 미도달 단계가 source와 일치하거나 정확한 결손으로 표시됨. source/candidate returned가 더 이상 최종 위험 차단으로 오해되지 않으며 재승격·다른 세션·집계 중복이 없음. 자연 승격 증가 자체는 별도 관측이며 이 진단 때문에 강제 후보/추가 broker 호출을 만들지 않는다.

### 4.3 판정 원본과 요약 로그의 동일성 검증

- 대량 매도 `False`인 ai_confirmed 요약과 같은 snapshot의 exact payload `True`가 함께 관측됐다. 원본을 확인한 SFA반도체·광전자는 실제 판정 입력에 신뢰 체결10개·순매도 및 large-sell=True가 있었다. 따라서 로그 불일치를 매도 위험이 없었다는 증거로 해석하지 않는다.
- main ai_confirmed는 기존 `feature_probe.large_sell_print`를 별도 기록하는 반면 최종 평가가 사용하는 exact features는 WS 갱신 후일 수 있다. 최초 probe와 최종 snapshot의 원 시각/hash·입력 추출 경로를 비교한다. 같은 이름의 필드가 다른 시점 의미라면 명시적으로 구분하거나 최종 판정 원본에서 투영하고 구형 의미는 호환 경계에서 설명한다.
- 종료 기준: 위험 근거로 제시하는 값·시각·source hash가 실제 평가 snapshot과 일치한다. 원본/이전 관측은 보존하며 로그값을 바꾸는 수리와 실제 판정 변경은 별도 검증한다. 같은 위험코드 안의 여러 사실도 임의로 하나만 선택해 숨기지 않는다.

### 4.4 failed_breakout 등 위험 차단의 적정성 검증

- BLOCK37건 중 failed_structure19건은 exact payload의 failed_breakout과 모두 일치했다. [봉 구조 producer](../../src/engine/scalping/entry_candle_context.py)는 최근 고점 접촉·고점 아래 종가에 윗꼬리 비율≥0.35 또는 고점 대비 하락≤-0.25% 등을 결합한다. 입력/규칙 일치는 구현 정합성일 뿐 위험 차단의 경제적 적정성 증명이 아니다.
- 분석 기준시각은 census 최초 발견이 아니라 **해당 실제 차단 시각**으로 고정한다. 그 이전 자료만으로 setup과 guard를 재현하고 같은 route의 당시 executable ask→이후 executable bid, 가능 수량, 비용, 역행폭, 목표/손절 도달 순서를 본다. 차단 이전 상승·타 시장 가격·mark price만 있는 구간을 이익으로 대체하지 않는다.
- 상승 종목만 고르지 않는다. 같은 시간대/venue/session·source quality·정책 세대의 비상승/하락·통과/RECHECK 표본을 대조하고 차단 사유의 전체 분모와 상승/비상승 빈도를 함께 보고한다. 종목별 반복 평가와 기회 episode를 분리하며 여러 사유의 공존을 중복 합산하거나 단일 원인으로 확정하지 않는다.
- 기존 census1200초 결과는 limited BBO sampling·1주 표시잔량·0.23% 비용 모형이며 continuous first-hit/실제 fill 권한이 없다. gap/censor/분봉내 목표-손절 순서 불명은 unresolved로 남긴다. 높은 사후 수익률만으로 false veto를 확정하지 않는다.
- 판정은 `입력/연결 결함`, `규칙대로 차단·경제적 적정성 미확정`, `정상 안전 차단 근거 확인`, `과잉 차단 후보`, `증거 부족`으로 서술하되 새 runtime taxonomy/report producer를 만들지 않는다. 조정 검토는 fresh·단일 blocker·비용/역행 및 기존 튜닝 계약이 충족될 때 기존 owner로 인계한다. threshold나 hard safety 변경은 이번 경로 수리에 포함하지 않는다.

### 4.5 9/21 후속 — 공식 원천과 국소 돌파 실패 보완계획

계획 수립 시 범위는 **돌파/stale 계획 구체화 + 비진입 자금 관측의5초 재사용 구현**이었다. 후속 “계획구현하고 코드리뷰 후 수정보완 반복실행” 승인으로 아래 돌파/stale 및 장후 의미 분리까지 작업본에 구현했다. 구현 turn에는 배포/재기동하지 않았으며, 이후 명시 승인 배포는 상단 최신 receipt와 감사 기록에 구분한다. 외부 sync·수동 실거래 호출은 실행하지 않았다.

공식 참조: 2026-09-21T15:18:05+09:00 GitHub `main` SHA **953e5dbff123f437ab4d11a78a95191a685eb51f**. 해당 tree에는 `kiwoom_docs`가 없어 [packaged specification](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json), `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/schemas.py`, `kiwoom/realtime/packets.py`, `postman/kiwoom-openapi.postman_collection.json`을 교차 확인했다. 337 API의 저항/돌파/resistance/breakout 명시 필드는 발견되지 않았다. portal 0B 페이지는 이 조회에서 접근 실패했으므로 미확인 의미를 확정하지 않는다.

| 필요한 값 | 공식 제공 범위 | 사용 경계 |
| --- | --- | --- |
| 국소 저항선·돌파 발생시각 | 해당 전략 의미의 직접 필드는 확인되지 않음 | 아래 completed-bar 로컬 파생 계약 필요 |
| 고가·고가시간 | 실시간 `0B`의 FID17(고가), FID1891(고가시간) 존재 | 고가를 국소 저항선으로 치환하지 않음. 1891은 명칭 외 형식/동률 갱신/route별 의미가 불명확하므로 현재 파서 추가·실행 승격 안 함 |
| 분봉 가격과 시각 | `ka10080`: `cntr_tm`(YYYYMMDDHHmmss), `open_pric/high_pric/low_pric/cur_prc`, `trde_qty` | 봉 시각으로 고점이 포함된 구간을 특정; 봉 안의 정확한 초 단위 돌파시각을 생성하지 않음 |
| 일반 시세·최고가일 | `ka10001/ka10007`: 고가, 최고가일 및 일반 시세시각 | 일반 `tm`/최고가일은 국소 돌파 발생시각이 아님 |

`ka10080` POST `/api/dostk/chart`, `stk_cd`의 KRX/NXT/SOR suffix, `tic_scope=1`, 수정주가 구분 및 continuation은 기존 owner를 유지한다. 새 API 호출/구독·봉 합성은 필요하지 않다. 공식 계좌 `kt00011` POST `/api/dostk/acnt`, `stk_cd/uv`, 현금 가능금액·수량, PRD/MOCK·공통 headers도 확인했으며 아래 TTL 변경은 요청/응답·수량·단위를 바꾸지 않는다. 공식 자료는 5초 TTL의 안전성/최적성을 보증하지 않는다.

전문 지식 근거: [Fidelity CMT 공저 자료 pp.9–13](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/learning-center/Idenitfying-Chart-Patterns.pdf)는 실제 저항 돌파→같은 돌파가격 아래 복귀→반대 방향 실패를 구분하고 종가/시간/가격 확인을 설명한다. [Schwab 거래량 설명](https://www.schwab.com/learn/story/trading-volume-as-market-indicator)은 거래량을 보조 확인으로 다룬다. 이는 의미 설계 참고이지 국내 1분 전략 임계치나 수익성 검증의 대체물이 아니다.

구체 구현 계약(기존 `entry_candle_context._structure` 및 setup/기계판정 owner 확장; 구현 결과는 아래):

1. 동일 거래일·venue/session의 연속 완료봉만 사용한다. 현재 10봉 비교/최근3봉 탐색 범위를 초기 재생 기준으로 유지하고, 각 돌파 후보 봉 t **직전** 10개 완료봉의 고가 최대치를 `resistance_price`로 고정한다. 10봉 부족·결손/중복충돌은 insufficient이며 미래봉/타 route로 보충하지 않는다.
2. 가격·기준 구간·동률 고점의 마지막 봉 시각·원천 hash·available_at을 함께 보존한다. `resistance_anchor_bar_at`은 봉 단위 근거시각이고, `breakout_confirmed_bar_at`은 실제 확인된 종가 돌파 봉으로 별도 기록한다. 고점 형성시각/수신시각/확인 가능시각을 혼동하지 않는다.
3. 고가 접촉만으로 돌파를 선언하지 않는다. 초기 의미 재생안은 **종가가 고정 저항선을 초과**해야 breakout-confirmed이며, 종목 tick size는 기존 owner로 정규화한다. 돌파 봉 자체·후속 고점을 resistance에 재편입하지 않는다. 동일 저항 episode를 중복 카운트하지 않고 세션 변경/원천 계약 변경/탐색 창 종료 시 명시 종료한다.
4. 돌파 후 고정 저항선 위의 눌림은 그 이유만으로 failed_breakout이 아니다. 아래 복귀는 우선 false-break/재확인 근거로 분리하고, 구조 실패는 고정된 사전 지지구간 이탈 또는 후속 완료봉의 지속 재이탈 등 확인 근거를 요구하는 후보안으로 비교한다. 실패 미확정이 ENTER_NOW를 생성하지 않으며 다른 source·spread·tail·broker guard를 보존한다.
5. 당일 고점 이격은 session risk context로만 유지한다. 기존 -0.25%/윗꼬리0.35를 새 의미의 자동 승격 기준으로 복사하지 않는다. 윗꼬리·거래량·국소 이탈폭은 같은 기준선/시점의 보조 근거로 재생한다. 확인 봉수·가격폭의 최종 수치는 아래 기존 비용/holdout 검증 전 확정하지 않는다.
6. 실제 `036810/14:59:11`, `092220/15:00:19`를 회귀에 포함한다. 후자는 최근3봉 이전10봉 고점3,120원, 완료종가3,155원으로, 새 고점3,185원 아래라는 사실만으로 실패하면 안 된다. 전자는 별도 재이탈 위험을 보존한다. 진짜 실패·고점 접촉만·돌파 유지·동률·forming 제외·역순/결손·세션경계·타 route 혼입 및 판정→RECHECK 소비/terminal까지 검증한다.
7. 완료 조건은 기준선·시각·source hash·판정이 시간순으로 재현되고 false-break와 확정 실패를 혼동하지 않는 것이다. 상승/비상승·손실 대조군과 차단 이후 비용/역행/목표-손절 순서로 경제적 적정성을 별도 검증한다. 구조 분류는 다른 consumer에도 쓰이므로 call graph와 source version 변경 영향도 함께 리뷰한다.

장후 연계 점검: `run_threshold_cycle_postclose.sh`의 machine-only → `ai_action_outcome_calibration` → runtime policy publication 경로를 확인했다. `MECHANISTIC_COMMON_FEATURE_GRID`는 spread/fillability/top3 ratio 세 축이며, **failed_breakout의 10봉/3봉/0.35/-0.25는 producer 고정 조건으로 장후 튜닝 대상이 아니다.** 따라서 기존 돌파 튜너를 수정하는 작업은 없고 새 자동 튜닝 축도 이번에 만들지 않는다. 후속 구조 구현 시에는 frozen `setup_evidence`를 소비하는 `_mechanistic_policy_rows`와 live producer의 의미 버전을 일치시키고 구형/신형 분모를 분리한다. 구형 값을 신형 의미로 소급 재라벨하지 않으며, 캐시/원천 hash 의존성·새 구조의 비용/holdout 통과·기존 다음날 policy/PREOPEN/PID 인계를 기존 main owner에서 검증한다.

작업본 구현: `entry_local_breakout_completed_v1`을 **entry wrapper에만** 적용하고 공용/holding 기본 분류는 보존했다. 첫 종가 돌파 직전10봉을 고정하며, 저항 아래 첫 복귀는 `retest_pending`, 사전 지지 하향 종가 또는 후속2개 연속 하향 종가는 `failed_breakout`으로 구분한다. 이는 비용 최적화된 임계치라는 뜻이 아니다. 구형 failed 판정만 해제된 경우에는 곧바로 진입하지 않고 기존 `TRIGGER_CONFIRMATION_RECHECK`로 연결한다. 10봉 부족은 국소 판정 `insufficient`이며 독립적인 opening-flow setup 전체를 새로 차단하지 않는다. 탐색은 최근3개 완료봉으로 제한되고 별도 장수명 episode 상태/새 counter를 만들지 않는다. episode ID는 원천봉 hash·request code·venue/session에 결속했다.

재현 수치 정정: 092220의 최근3봉 **이전** 고점은3,120원이지만, 실제 최초 종가 돌파는14:58이며 그 **직전10봉**에는14:57 고가3,135원이 포함된다. 구현의 고정선은3,135원이고 후속3,185원으로 재설정하지 않는다. 036810은 고가 접촉/종가 동률만으로 돌파 확인을 만들지 않는다. 회귀는 해당 최근봉 수치와 통제된 선행봉으로 만든 재현 fixture이며 전체 당시 raw를 재생했다는 의미가 아니다.

장후 구현: frozen setup에 의미 버전/국소 근거를 전달하고 main machine-only의 common/hierarchy/joint 튜닝 입력을 현재 버전으로 격리한다. 구형 case table·전체 표본 수와 버전별 제외 수는 보존하고 `current_structure_eligible_count`를 별도 표기한다. 구형을 신형으로 재라벨하지 않으며 신형 표본 부족은 승격 불가다. producer 파일을 cache/economic-kernel hash에 추가했다. 기존 세 축과 비용/holdout·PREOPEN/PID 기준은 그대로이며 장후 작업을 수동 실행하지 않았다.

### 4.6 9/21 후속 — stale 불일치 개선계획

원천 확인: `425040` snapshot14:57:43.930(BBO age0.388초)→machine capture14:58:42.183(features age58.288초), 분석 총58.508초. `009900` snapshot15:00:40.223(age2.378초)→capture15:00:41.293(features age3.381초); 최신 갱신은 bid=ask=8,710으로 거부(`latest_best_levels_invalid`)됐다. `quote`는 WS의 앞선 boolean, features는 원 수신시각 기준 재계산을 써 동시 표현이 충돌했다. 58초의 세부 지연 함수는 미계측이며 provider 지연이라고 단정하지 않는다.

1. 기존 `refresh_before_evaluate`→`analyze_target`→feature packet→hot payload를 단일 owner 경로로 유지한다. 정책/문맥 준비 등 지연 작업 **후**, 기계판정 입력 확정 직전에 동일 route/epoch의 최신 유효 BBO·체결을 한 번 재검증한다. 유효한 갱신이 없거나 기존 deadline을 넘으면 평가를 보류/원천 결손으로 남기고 무한 갱신·추가 REST로 해결하지 않는다.
2. 한 `as_of`와 원 BBO 수신시각으로 freshness를 계산하여 `quote`·features·snapshot preflight·guard receipt에 같은 판정을 투영한다. snapshot_id/hash는 실제 입력 세대에 결속하고, 입력 변경은 기존 parent/revision으로 남긴다. 과거 snapshot의 fresh 표시를 현재 입력의 freshness로 재사용하지 않는다.
3. shared mutable WS를 직접 덮어쓰지 않고 동일 frozen 입력으로 계산한다. 새 BBO가 locked/crossed/route-conflict면 채택하지 않으며 이전 BBO도 같은 as_of에서 만료면 불가다. 3초 호가 freshness·5초 체결·실제 주문 직전 guard는 이번 계획으로 완화하지 않는다.
4. 기존 telemetry에 `received_at`, `snapshot_at`, `evaluation_as_of`, 단계별 monotonic duration(정책/문맥 준비·feature build·평가)을 필요한 만큼만 연결한다. 새 logger/daemon/report producer 없이 위2개 사례의 로컬 지연 owner를 특정한다.
5. frozen-clock 회귀: fresh→3초 경계 초과, 58초 처리, 유효 새 BBO, bid=ask 갱신 거부, route/epoch 전환, 미래/무시각, 늦게 도착한 worker 결과를 포함한다. payload 내부 stale/age/as_of 동일성과 source gap 보존, BLOCK/RECHECK의 AI 승격 불가를 검사한다. source/schema 변경으로 영향받는 장후 exact-input 소비에도 의미 버전·원본 보존을 적용한다.

작업본 구현: sync/async watching·두 재확인·pre-submit AI authority retry에서 기존 로컬 WS refresh를 분석 내부의 정책/문맥·파일 기반 micro 입력 준비 **후** 연결했다. 최종 frozen 입력과 단일 `as_of`로 snapshot과 feature를 계산하고 quote는 같은 feature age/stale를 투영한다. 원 수신시각·snapshot 시각·preparation/refresh/feature-build duration은 기존 machine capture metadata와 결과에 남긴다. 평가 ID/parent snapshot을 유지하고 경제성 observer도 갱신된 같은 WS를 받는다. 기존 async deadline을 연장하지 않으며 refresh 예외·route/epoch 변경·snapshot/feature quote clock 불일치는 명시적 source gap으로 차단한다. 최신 BBO 거부 시 과거 입력을 현재 시각에서 다시 검증하며 원천 수신시각을 새로 찍지 않는다. 실제58초 지연의 세부 함수별 운영 원인은 새 자연 telemetry 확인 전 미확정이다.

## 5. S3 — WS/I/O 수리는 관측 손실 없이 선택 적용

1. 기존 checkpoint의 모든 실제 consumer가 쓰는 필드·체결/호가 history 길이·route·epoch·clock을 먼저 조사한다. 파일이 dashboard라는 이유로 machine history를 삭제하지 않는다.
2. 동일 atomic 파일 세대의 중복 JSON 읽기/파싱을 먼저 줄인다. cache key는 path뿐 아니라 교체 세대(inode/stat 및 필요 시 내용 hash)까지 구분하고 bounded 메모리로 운영한다. reuse해도 현재시각 기준 stale/producer liveness/epoch 검증을 다시 한다. 파일 부재·손상 때 이전 성공을 무조건 반환하지 않는다.
3. receiver lock 안의 불필요한 이력 복사와 쓰기용 중복 표현을 검토한다. 직렬화 표현 변경은 모든 기존 consumer의 동등성을 먼저 입증한다. delta/checkpoint 분리를 선택한다면 원자적 manifest·세대 일치·누락/재시작 복구가 필요하므로 단순 cache로 목표를 달성하면 추가하지 않는다. RAM 저장소 이전은 swap 부하를 악화시킬 수 있어 기본안에서 제외한다.
4. checkpoint 발행 주기·3초 등 기존 만료 기준·보존 이력 길이를 임의로 완화하지 않는다. reader가 소비하는 원 tick 시간과 publish 시간을 혼동하지 않는다. 전체 WS 전환·신규 구독·P3 분봉 생성으로 확대하지 않는다.
5. CPU/RSS, process write bytes/s, swap in/out, disk await/I/O wait, publish/read p95/p99, machine 입력 age·DANGER 빈도를 같은 세션/유사 입력량으로 비교한다. 기록량 감소와 I/O/DANGER 개선의 인과는 각각 보고한다. 1초 표본이나 장세가 다른 전후 평균만으로 개선 완료를 선언하지 않는다.

완료: 동일 frozen 입력에서 소비 필드·원 timestamp·route·epoch·기계판정 동일, 손실/중복/혼합세대0. 성능 수리 자체의 정량 개선이 재현되고 자연 표본에서 기존 freshness·오류·지연이 악화되지 않음. 정확한 개선율 목표는 S0의 재현 가능한 기준선 확보 후 고정하며 안전 임계치로 사용하지 않는다.

## 6. S4 — 기존 자금 연결의 조건부 검증(필수 수리 단계 아님)

- 정책 캐시·자금 조회 준비·성공 응답 재사용·운영계획 연결은 기존 수리/배포 이력을 재사용한다. 최근 두 시도의 미제출 원인이 자금 결함이라고 입증되지 않았으므로 이를 다시 구현하거나 독립 필수 과제로 열지 않는다.
- **착수 조건:** 자연 진입이 앞선 판정·AI·재검증을 거쳐 제출 직전 경로에 도달한 경우 기존 자금 연결을 확인한다. 그 과정에서 새로운 코드/계약 결함이 재현된 경우에만 원인·영향 범위·승인 범위를 확인하고 해당 부분을 추가 수리한다. 정상적인 잔액 부족·guard 차단·관측 cache miss 자체는 재구현 사유가 아니다.

- **주문을 허용할 때 필요한 유효 자금·계좌·가격·수량·주문 상태 증거는 결손 허용0**이다. 증거가 없으면 해당 시도는 미제출; 주문 증거 성공률을 맞추려고 추정 잔액·과거 응답·다른 종목/가격을 사용하지 않는다.
- BLOCK/RECHECK 관측은 exact cache 미존재를 허용하되 source_gap/경제성 null·해당 분모를 보존한다. 이 62건의 100% 수집을 목표로 REST를 늘리지 않는다. 허용은 매매 안전 증거 생략이나 해당 표본의 튜닝 사용 승인이 아니다.
- ENTER_NOW 또는 실제 submit 단계의 결손과 계약 충돌은 관측 coverage로 제외하지 않는다. 정당한 common guard는 자금 조회 실패가 아니라 guard 제외로 구분하며 후속 변경이 앞선 사유를 덮지 않게 한다.
- 착수 조건 충족 시 기존 bounded worker/singleflight·성공 응답 재사용의 소비 증거를 확인한다. 계좌·token/date·종목·가격·주문/잔고 상태·기존 유효기간 일치, 주문/취소 우선권과 공유 요청 한도는 그대로 유지한다. 검증용 추가 계좌 조회나 반복 prefetch를 만들지 않는다.
- 자금 성공 뒤 동일 시도의 정책 cache→signed sizing/운영계획→최종 guard의 **기존 연결**을 확인한다. 나중 조회한 값을 과거 평가에 소급하지 않고, 증거금 가능액을 현금 흐름으로 대체하지 않는다. 새 결함이 재현되지 않으면 추가 자금 수리는 하지 않는다.

조건부 검증 결과: 대상 시도에서 기존 연결 정상 또는 구체적인 안전 차단을 확인하면 그 결과만 기록한다. 표본이 없으면 `pending_natural_evidence`로 기존 owner에 남기되 판정 이력·지연·AI 경로 수리 완료를 보류하지 않는다. 실제 재현 결함만 추가 수리의 미완료 항목으로 관리한다. 연결1건은 해당 경로의 운영 증거일 뿐 안정적 coverage/수익성 달성은 아니다.

### 6.1 9/21 명시 승인 — 비진입 관측 캐시 5초

- 앞선 S4의 기본 조건부 원칙에 대한 이번 좁은 추가 구현: `_read_entry_capacity_snapshot(source_only=True, reuse_only=True)`만 2→**5초 이하** 재사용한다. caller는 기존 BLOCK/RECHECK 경제성 관측이다. `_ENTRY_NONENTRY_CAPACITY_REUSE_MAX_AGE_SEC=5.0` 고정 운영값이며 자동 최적화 값이 아니다.
- ENTER_NOW source 조회/사전준비의2초 및 실제 sizing의 fresh API 조회는 그대로다. 계좌/token/origin/date/종목/정확한 가격/보유·주문·예수금 상태/hash 검증, 미래 응답 거부, inflight·공유 요청 한도·우선권은 유지한다. 비진입 cache miss의 추가 동기조회0, 원 응답시각 보존, 미래값 소급0을 검사한다.
- 성공 재사용 receipt와 기존 경제성 budget 전달에 `capacity_reuse_max_age_sec`를 남겨 기존2초 관측과 새5초 관측을 구별한다. 독립 report/schema/임계치 env를 추가하지 않는다. 원래 미기록인 실패 캐시 나이를 복구했다고 주장하지 않는다.
- 장후 검색 결과 이 TTL을 조정하는 tuner/정책 publisher는 없다. 유지/폐기할 기존 TTL 튜너가 없으므로 새로 만들지 않는다. 장후 capital freeze는 원 응답시각/hash를 보존하고 시간 역전만 거부하며 별도2초 재검증으로 덮어쓰지 않는다. source-only capital은 주문 권한이나 full-cost EV가 아니다.
- 근거 한계: 09:37–15:03 누적 관측805건 중 성공26건(실재사용9), 명시 비진입 cache miss296건. 실재사용 응답→이벤트 기록 간격0.790–2.124초/중앙1.478초는 이미 선택된 성공 표본이고 실제 캐시 판정 나이와 다르다. 5초는 사용자 지시 운영값이며 측정된 최적값이라고 표시하지 않는다. source/시도·정책 세대별 관측 coverage와 비용 경제성 분모는 계속 분리한다.
- 작업본 변경→경계/authority 회귀→리뷰까지 이번 범위다. 배포·PID 적용·자연 재사용/결손 감소는 별도이며 현재 실행 중인 배포본에 적용됐다고 주장하지 않는다. rollback은 이 상수5→2 복귀이고 계좌/주문·과거 원본 삭제를 포함하지 않는다.
- 검증 receipt: 자기리뷰에서5초 receipt의 실제 budget consumer 전달과 상태세대 변경 거부를 추가 확인했다. `pytest -q src/tests/test_entry_cash_capacity_contract.py src/tests/test_sniper_scale_in.py -k 'capacity or source_capacity or nonentry_five_second_receipt'` **61 PASS/908 deselected**, 두 변경 Python compile PASS, `git diff --check` PASS. print-only backlog parser29 tasks/기존 제출 owner1개 유지. 실제 API/계좌/provider 호출, 장후 재생성, 외부 sync, 배포/재기동은 미실행이다. 돌파/stale 계획의 구현 검증이나5초 자연 수용 완료를 의미하지 않는다.

## 7. 반복 리뷰·테스트·공식 참조

- 매 변경은 `최소 구현 → producer/consumer 자기리뷰 → 결함 보완 → 재리뷰 → 관련 테스트`로 닫는다. 기존 사용자 변경을 보존한다. 미해결 in-scope 결함이면 배포 gate 미통과다.
- S1: 두 실제 전이, 정상 단일 판정, 같은 revision 충돌, 역순/중복, source/owner mismatch, 구형 cache, 경제성 사유 덮임, 역사 incident 보존, 최초 통과/최종 상태/고유 시도 수 보존.
- S2: SAFE/CAUTION+slippage 통과와 초과, DANGER/stale/deadline/clock 경계, AI caution와 invalid/timeout, 최신 입력 재검증 실패, BLOCK을 AI가 승격하지 못함. 테스트는 실제 주문/계좌/provider 호출을 대체한다.
- S2 경로 추가: 위4개 large-sell 원본 fixture의 **실제 main 최종 판정**과 후속 RECHECK 소비/terminal을 함께 검증한다. 구형 compose WAIT 테스트만으로 종료하지 않는다. 단독 위험과 복합/source-invalid 위험, 위험 지속/해소, fresh input revision 및 중복 주문 방지를 포함한다. scanner 반환 성공→미승격의 첫 누락 단계, promotion/attach 지연, 타 cycle 혼입 거부, 최종 payload↔로그 동일성은 기존 `test_entry_setup_evidence`, `test_market_opportunity_census`, `test_scanner_source_census` 등 해당 owner의 테스트를 확인해 최소 확장한다. 비용 비교는 차단 이전 상승 제외·역행 선행·censored/route mismatch·반복 episode 보존을 검증하며 broad replay는 자동 실행하지 않는다.
- S3: atomic replace·동일크기/빠른 교체·재시작·fork·삭제·손상·메모리 상한·동시 reader, 이전 epoch 거부, cache 재사용 후 stale 재판정, 기존 machine/widget 필드 동등성.
- S4: 기존 자금 코드를 건드리지 않으면 전용 회귀를 반복하지 않는다. 새 결함 재현으로 수정할 때만 영향에 맞춰 exact key·주문/잔고 변경·만료·rate wait/취소 우선·singleflight 실패/timeout·직렬화 사례를 선택한다. S1 등 다른 수정이 자금 projection에 영향을 주면 그 연결 회귀만 수행하며 nonentry 추가 조회0·actual pre-submit fresh 검증 유지 여부를 확인한다.
- 기존 `test_submission_bottleneck_monitor`, `test_buy_funnel_sentinel`, `test_sentinel_event_cache_parity`, `test_sniper_entry_latency`, `test_sniper_scale_in`, `test_quote_consistency`, `test_kiwoom_websocket`, `test_entry_cash_capacity_contract`, `test_entry_execution_sizing_plan`의 영향받는 사례만 선택한다. 통합 회귀는 마지막 변경 후 필요한 합집합 1회로 제한하고 장중 동일 대규모 suite를 반복하지 않는다. compile/해당 wrapper bash 검사/diff 검사와 별도로 실환경 자연 검증을 보고한다.
- Kiwoom 요청·응답 파서·FID·REG/REMOVE·재연결·계좌/주문 흐름을 수정하게 되면 구현 전에 [공식 참조 gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 실행하고 upstream SHA·경로·조회시각을 수리 기록에 남긴다. 이 문서 작성은 API 수정을 하지 않았으며 공식 프로토콜 검증 완료를 주장하지 않는다.

## 8. 승인 후 배포·롤백·자연 종료 판정

1. 먼저 main/consumer의 실제 release/PID를 다시 확인한다. 문서 기준 collector는 별도 `6c1bfa172`13:51 인계이며 메인과 동일 배포라고 가정하지 않는다. shared writer 변경 시 collector·웹·machine reader의 호환성을 포함하고 기존 WS owner의14:00–14:45 자연 비교 창을 임의 재시작으로 무효화하지 않는다. 승인 재시작이 필요하면 새 세대로 완전한 창을 다시 구분한다.
2. 검증된 변경만 immutable release에 포함하고 승인 범위에 해당하는 프로세스만 기존 절차로 인계한다. 선택 release 백업·환경/정책 해시·단일 main PID·custody·실제 cwd·bootstrap/health를 확인한다. 커밋푸시와 배포는 별도 기록한다.
3. rollback 대상은 코드/reader 호환성 또는 source/성능 회귀다. 이전 release와 호환 cache schema 경로를 사전에 검증하고 해당 범위 승인·절차로 복귀한다. 원본 사건/주문/incident 삭제, 포지션 청산, thresholds/env 임의 변경은 rollback에 포함하지 않는다. 기회 없음·정상 위험 차단·경제성 표본 부족만으로 rollback하지 않는다.
4. 기존 5분 Sentinel의 다음2회 정상 갱신에서 revision 전이·분모·신규 충돌과 정확한 원인 표시를 확인한다. 이는 보고 소비 확인이며 실제 제출 검증과 구분한다. 발생하지 않은 사건을 만들거나 테스트 주문을 넣지 않는다.
5. 정상 자동매매에서 **기계 ENTER_NOW→허용된 보조 판정→신선한 재검증→유효 자금/계획→SAFE 또는 실행 CAUTION+slippage 통과→order attempt→broker 접수/거절**의 한 시도를 end-to-end 대사한다. 접수는 order number/실제 broker 증거로 확인하고 no response는 reconciliation 대상이다. 재시도/child가 같은 주문을 중복 제출하지 않았는지 확인한다.
6. 자연 기회가 없거나 정당한 guard로 중단되면 코드/배포/보고 소비만 완료, 제출 경로 자연 수용은 `pending_natural_evidence`로 기존 owner에 남긴다. S4 자금 검증 표본 부재만으로 완료된 S1–S3 수리를 재개방하거나 배포 gate를 막지 않는다. 기존 TimeWindow 끝에 무한 대기/추가 과거 재생을 하지 않고 첫 차단과 다음 자연 세션 의존성을 인계한다. 임의로 blocker를 지워 성공 처리하지 않는다.
7. 자연 정상 제출1건은 해당 경로의 운영 증거이며 전체 병목 해소율·지속 성능·체결·순이익 보장은 아니다. full/partial fill 및 `COMPLETED + valid profit_rate`의 비용 후 경제성은 별도 owner가 판단한다.

지표 계약: funnel/revision/coverage 계수는 `metric_role=funnel_count`, `decision_authority=report_only`, `window_policy=exact_attempt_revision_same_session_30m`, `sample_floor=none_for_counts`, `primary_decision_metric=normal_submit_path_reachability`, `source_quality_gate=ordered_same_attempt_source_bound_events`로 취급한다. 성능 비교는 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=matched_session_input_load_and_process_generation`, `sample_floor=paired_replay_plus_natural_observation_required`, `primary_decision_metric=consumer_latency_and_io_cost_nonregression`, `source_quality_gate=lossless_fields_original_clocks_epochs_and_matched_denominator`다. 두 계약 모두 `forbidden_uses=order_authority/threshold_relaxation/positive_ev_claim`이며 측정값을 새로운 매매 정책으로 소비하지 않는다.

## 9. 문서 수립 이력과 후속 구현 범위

최초 문서 수립 요청에서는 계획과 기존 checklist owner 연결만 변경했다. 이후 사용자의 “계획구현하고 코드리뷰 후 수정보완 반복실행” 요청으로 S0/S1 및 S2의 확인된 코드 결함과 필요한 진단 전달을 구현한다. 구현 receipt는 위 수리 기록에 보존한다. S3은 DANGER 인과가 입증되지 않아 별도 WS owner의 기존 작업을 중복 수정하지 않는다. S4의 자금 연결은 조건부 검증 원칙을 유지하며, 최초 kt00011_empty를 숨기거나 계좌 재조회/안전 기준 완화로 대체하지 않는다. S5 배포·자연 수용 및 §4.4 차단 경제성은 작업본 테스트 완료와 구분한다.
