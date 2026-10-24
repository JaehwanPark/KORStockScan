# Main 전체 종목·시장 보유청산·익절 및 장후 재생 개선 상세계획

작성일: 2026-10-10 KST

최신 연구 상태: **2026-10-23 §18의 보유 원천·수익 보존·약세장 기회 연구**와 [실행 검토](../audits/main-holding-exit-opportunity-research-review-2026-10-23.md)를 따른다. 새로 확보된 장전/정규/장후 네 관측 분할의569개 확인 지점에서 고정 폭 민감도를 실행했다. 오늘 삼성전자 익절의 자연 영수증과 매도 후 호가를 확인했고, 보유 AI 입력 결손·256개 상세 기록 소진을 분리했다. 정책 수치 변경·발행·배포는 없다. §14–§17 및 아래10/10 기록은 해당 시점의 실행·종결 이력으로 보존한다.

최신 수용 정정(10/10 21:27 KST): [정책 생성 구조 재점검](../audits/main-trailing-delay-policy-generation-structural-review-2026-10-10.md)의 TG1–TG4는 미해결이다. 아래 완료는 부모 계승 발행·분할 처리·검증된 운영 준비의 이력이다. 정상 완료 adapter의 원 holding-AI 증빙 누락, 신규 classifier SHA와 과거 pin의 순환 일치 조건, 대용량 시장 후보 미전달 및 일반 악화 전수 veto를 검증하지 못했으므로 **신규 학습 정책 생성까지 전체 구현 완료로 해석하지 않는다. 데이터 축적만으로 닫을 수 없다.** 보완 우선순위·종료 검사는 위 감사와 잔여계획의 최신 상태를 따른다.

상태: **AT0–AT7·TP1–TP7와 잔여 W0–W5의 구현·반복 리뷰·정식 발행·승인 배포·기동 준비를 완료했다.** `MainAllScopeTrailingReplay`는 완료다. 최종 릴리스는 `main-trailing-delay-residual-20261010-v6` / `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`이며 [실행 감사](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md)와 [최종 준비 영수증](../../data/report/main_trailing_delay_deployment/2026-10-10/final-residual-readiness.json)을 따른다. 10/12 실제 PID 소비와 실현 경제성은 미관측이며 기존 적용일 owner에서 확인한다. 아래 이전 문서·부분 배포 기록은 당시 이력이다.

구현 순서·owner·완료 검사는 [잔여작업 완료계획 W0–W6](main-trailing-delay-residual-work-completion-plan-2026-10-10.md)을 따른다. 자동 전수 source producer, 초과 입력의 분할·재개·전역 집계, 전체 성능 및 formal 장후/PREOPEN 인계를 검증했다. 초기 부모 계승은 추가 경제 gate 없이 수용했으며 W6 자연 PID 관측은 적용일의 별도 수용이다.

후속 승인 배포 이력(10/10, 잔여 구현 전): 검증된 공통 코드와 부모 동등 초기 구성은 `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28`로 배포했다. 10/12 PREOPEN 전체 계약·예약경로·최종화 세대는 PASS다. 신규 제출 지연 v2 정책 발행 및 전수 연구/대용량/전체 연구 성능 수용은 OPEN이며 상세 상태는 [후속 리뷰·배포 기록](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md)을 따른다.


대상: Main 보유청산의 트레일링 시작률, weak/strong 되돌림폭, 상황 분류, 실제 완료 거래와 ENTER_NOW+PASS 후행 경로를 이용하는 장후 계산·오프라인 재생.

현재 분할 입력 계약: normalized partition의 `paths[identity]`는 기존 event 배열 또는 `segments` 참조 배열과 전체 `event_count`를 가진 객체다. 각 참조는 input-root 내부의 상대 `path`와 해당 segment의 봉인 `artifact_sha256`를 가진다. segment는 동일 `source_date`와 `events`를 보관한다. 큰 경로의 경제 재생은 명시적 isolated output에서만 수행한다. 기본 preflight와 `dry-run`은 source/cache를 쓰지 않으며, segmented 경제 재생의 checkpoint output이 없으면 완료로 표시하지 않는다. source-feature cache는 numeric 부모/후보와 독립이며 원 leaf bytes·source/parser/M1 계약·cutoff가 바뀌면 무효화한다.

선행: [10/9 보유청산 보완계획과 구현 이력](./main-holding-profit-exit-runtime-and-postclose-remediation-plan-2026-10-09.md), [구현 리뷰](../audits/holding-profit-exit-runtime-and-postclose-implementation-review-2026-10-09.md), [공식 비용 원천 후속 통합](../audits/holding-profit-exit-official-cost-source-integration-deployment-review-2026-10-09.md).

## 1. 목표와 완료 범위

**런타임·장후작업·오프라인 재생 모두 삼성전자를 포함한 전체 Main 대상 종목과 모든 지원 시장·세션을 같은 계약으로 처리한다.** 특정 종목, 비삼성 집합, KRX 정규장만 구현한 뒤 나머지를 추후 지원으로 남기는 방식은 수용하지 않는다. 새 종목은 종목코드별 코드 수정 없이 공통 경로에 진입해야 한다.

전체 적용은 모든 종목에 주문하거나 실제 거래 불가 시장을 활성화한다는 뜻이 아니다. 종목 마스터·시장 세션·경로·수탁 기준에 따라 모든 범위에 처리 결과를 남기고, 거래 가능한 Main 보유에는 공통 판단기를 적용한다. 거래 불가·관측 없음·원천 결손은 각각 명시한다. 기존 entry 허용 범위, Main/manual 수탁과 운영자 veto, 주문·수량·계좌·자금·cooldown·freshness·hard/protect/emergency guard를 유지한다. episode/widget 수탁을 Main에 편입하거나 퇴역 executor·연구·publisher를 복원하지 않는다.

완료 산출물은 다음 다섯 가지다.

1. 전체 분석기간의 비용·체결·원천 정정을 끝단까지 전파하는 봉인·재사용 검증.
2. 모든 종목·시장에 공통인 opportunity/holding 원천 계약과 누락 없는 범위 대사.
3. runtime과 같은 트레일링·강약·유예 판정을 사용하는 실제 거래 재생 및 분리된 기회 재생.
4. 시장 정책을 부모로 하는 소수의 상황별 익절 정책과 전체 범위 초기정책 생성 경로.
5. 장후 원천 재생성 → 후보/부모 계승 → 선택 → 정확 날짜 PREOPEN → PID 소비를 구분하는 인계 계약.

공통 코드의 적용 범위는 처음부터 전체다. 경제 후보의 값 변경은 기존 `scalp_trailing_take_profit` family 선택·안전 계약을 따른다. 후보가 없는 시장·유형도 정상 정책 결과인 `parent_carry`를 발행하여 누락시키지 않는다. 기존 한 시장씩 후보를 변경하는 선택 규칙은 공통 엔진을 일부 시장에만 구현하는 근거로 사용하지 않는다.

## 2. 확인한 구현 상태와 추가 결함

### 2.1 현재 동작과 미완료 사항

| 항목 | 10/10 확인 근거 | 이번 계획의 처리 |
| --- | --- | --- |
| 트레일링 시작·되돌림 | [공통 판정기](../../src/engine/scalping/trailing_exit_decision.py), [정책](../../src/engine/scalping/trailing_mechanical_policy.py). 시작은 peak의 net 수익률, 되돌림은 peak 대비 실행 가능한 bid의 가격 하락률을 사용한다. | 두 비율의 분모·단위를 보존하고 runtime/replay가 같은 함수를 호출한다. |
| 동적 강약 | [M1 분류기](../../src/engine/scalping/trailing_mechanical_strength.py)는 같은 경로의 호가·signed 체결량으로 STRONG/WEAK/UNKNOWN을 판정한다. | 상황 유형과 강약을 별개 상태로 유지한다. UNKNOWN을 정상 WEAK 관측으로 집계하지 않는다. |
| 초기 수치 | 10/12 격리 준비 manifest의 세 시장 모두 시작 0.4%, weak 0.4%, strong 0.8%, `operator_directed_m1_baseline`이다. | 구현 시 다시 검증한 승인 부모를 계승한다. 이 문서의 숫자를 영구 하드코딩하지 않는다. |
| 기존 장후 최적화 | [holding report](../../src/engine/holding_exit_observation_report.py) → [mechanical replay](../../src/engine/scalping/trailing_mechanical_replay.py)는 엄격한 실제 완료 거래 cohort를 소비한다. | 실제 경제 원장은 유지하고 ENTER_NOW+PASS 기회 재생을 별도 cohort로 추가한다. |
| 기존 기회 재생 | [first-signal 연구](../../src/engine/scalping/entry_first_signal_exit_research.py), [M1 연구](../../src/engine/scalping/entry_mechanical_exit_research.py)에 비삼성·KRX 정규장·60분/15:30 제한이 있다. | 과거 연구의 의미를 보존하면서 공통 재생 엔진과 전체 범위 adapter로 확장한다. |
| 비용 원천 | [수집·배분](../../src/engine/lifecycle/broker_cost_source.py), [대사](../../src/engine/lifecycle/broker_cost_reconciliation.py). 현재 공식 일별 비용의 자동 배분 성공은 단일 Main position의 당일 완전 왕복과 전량 귀속 입증에 제한된다. | 모든 보유를 census에 넣고 복수 position·분할·익일 보유의 exact 배분 가능성을 각각 검증한다. 불명확한 비용은 결손으로 남긴다. |
| 구현과 운영 | 계획 작성 당시 선택 release는 `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06`이었다. 후속 선택은 §1 앞의 10/10 배포 기록과 실제 selector를 따른다. | 이 dated 확인을 새 코드의 배포/PID 증거로 재사용하지 않는다. 현재 준비와 전체 계획 적용은 별도다. |

선행 점검의 관련 14개 suite 475건 통과는 기존 코드의 표적 회귀 결과다. 아래 신규 결함이나 전체 시장 재생 지원을 이미 검증했다는 뜻이 아니다.

### 2.2 먼저 해결할 결함과 범위 공백

| ID | 결함·공백과 근거 | 영향 / 종료 검사 |
| --- | --- | --- |
| AT-F1 | [log archive](../../src/engine/log_archive_service.py)의 manifest 발행·재사용 검사가 `actual_cost_source_generations` 중 `target_date`만 비교한다. 이전 날짜 비용만 바꾼 합성 재현에서 오래된 누적 report의 재사용과 재봉인이 모두 허용됐다. | 누적 입력기간의 모든 소비 날짜를 검증하여 과거 비용 정정 후 stale report가 통과하지 않아야 한다. 자연 손익 오산 발생 자체가 입증된 것은 아니다. |
| AT-F2 | 10/8 holding report의 9/29–10/8 기간에 source-gap 날짜 7개, strict completed ID 0개, `hold_population_census_or_empty`, 후보 `null`이다. | 손익 0이나 전체 실제 체결 0으로 해석하지 않는다. 날짜별 복구 가능성/비용/봉인을 대사한 뒤 적격 모집단을 다시 확정한다. |
| AT-F3 | 비삼성·KRX·15:30 제한, 일부 연구의 표본 reservoir가 전체 기회 census를 대신할 수 없다. | 종목·시장 whitelist 제거, 전체 분모 대사, route/session별 실행·관측 계약 검증. |
| AT-F4 | ENTER_NOW/PASS만으로 주문가격·수량·체결·청산 비용을 알 수 없다. 기존 price replay의 고정 TP/SL·180초 모델도 실제 trailing replay와 다르다. | 정확한 기회·가격계획·후행 경로를 연결하고 미연결은 source gap. 모델 손익과 실제 손익 분리. |
| AT-F5 | 현재 시장별 정책+동적 강약은 있으나 상황별 시작률·폭 정책과 loader/selector 계약은 없다. | 현재 시장 부모를 유지하는 유형 schema, causal 분류, runtime/replay 동등성, 후보 선택 검증. |
| AT-F6 | 실제 SELL 이후, 대체 시점 AI 유예, partial/ADD·익일 구간은 관측 범위가 다르다. | 범위가 끝난 지점에서 검열하고 미관측 응답·체결을 만들지 않는다. 지원 상태를 전체 census에서 공개한다. |
| AT-F7 | `trailing_mechanical_replay`가 축별·쌍별·joint 후보의 position별 상세 dict를 보관한다. 후보 평가 cache가 있어도 전체 scope·유형 추가 시 보관량이 증폭될 수 있다. | 동일 effective vector를 dedup하고 후보 block별 streaming/임시 projection으로 집계한다. full detail은 최종 후보·필요 반례만 보관하며 전 후보의 공통 ID·검열은 보존한다. |
| AT-F8 | M1 분류는 bounded history를 정렬·순회한다. 숫자 후보마다 같은 source/feature/강약 경로를 처음부터 다시 계산하면 전체 replay 비용이 커진다. | source·classifier config·position 초기상태가 같은 계산만 공유한다. position별 reset/ADD·AI 분기·epoch를 넘어 상태를 공유하지 않는다. |
| AT-F9 | 원천 hash·부모·cost·grid를 하나의 cache key로만 다루면 비용 정정/선정 변경이 raw 전체 재파싱으로 번질 수 있다. | decode→feature→replay→selection별 의존성을 분리하고 영향 partition만 재계산한다. 정정에 영향받는 net 시작판정·holdout은 반드시 다시 계산한다. |
| AT-F10 | 기존 §10.2는 측정항목 중심이며 구체적인 감소 작업·실패 gate·두 계획의 합산 예산이 부족했다. | TP1–TP7, 단독/결합 부하, same-input 비악화·절감과 전체 scope 절대 예산 수용을 AT0–AT8에 연결한다. |

## 3. 전체 종목·시장 범위 계약

### 3.1 범위의 단일 원천

- 종목: 기준시각의 종목 마스터 및 Main discovery/보유 집합을 사용한다. 고정 감시 5종목이나 과거 거래 종목 목록을 전체 universe로 사용하지 않는다. 당시 상장·거래정지·시장 편입 상태를 보존하여 생존 종목 편향을 방지한다.
- 정책 시장: 기존 `PREMARKET`, `REGULAR`, `INTEGRATED_AFTERMARKET`을 부모 키로 유지한다. 실제 venue/session/route를 이 세 키로 덮어쓰지 않는다.
- 실제 세션과 가능 행위: [session contract](../../src/trading/market/session_contract.py)를 공통 owner로 사용한다. 연속매매·동시호가·휴장·종료·청산만 허용되는 구간을 구별한다. 특정 시각을 새 모듈마다 복제하지 않는다.
- 등록 범위: [등록 catalog](../../src/engine/scalping/reversal_registered_catalog.py)의 PRE SOR/NXT, REGULAR SOR/KRX/NXT, AFTER SOR/KRX/NXT를 읽되, 등록 경로와 현재 운영 선택 경로를 구별한다. 실행 적격성은 세션·종목별 시장 편입·기존 entry/exit 규칙으로 결정한다. KRX PRE 연속매매를 새로 가정하지 않는다.
- 수탁: [owner retirement](../../src/trading/config/owner_retirement.py)와 공통 journal 관리 disposition을 사용한다. 과거 episode가 보유한 적 있다는 이유로 종목 전체를 배제하지 않고, 해당 퇴역 owner의 수량·intent만 자동 실행에서 제외한다.

`broker_route_requested=SOR`는 체결시장 증거가 아니다. `actual_execution_venue`, `registration_item`, `_NX/_AL` 등 원 item, 시장 세션, 이벤트 시각, receipt source를 각각 보존한다. KRX와 NXT의 호가·체결량을 섞어 가상 체결가나 강약 상태를 만들지 않는다.

### 3.2 모든 소비자가 받는 coverage

`universe_snapshot_sha256 + scope_contract_version + as_of`를 기준으로 종목×지원 시장/경로 범위를 열거한다. 큰 직적집합을 event마다 재생성하지 않고 공유된 scope index와 실제 event 원장을 연결한다. 적어도 다음 상태를 상호 배타적으로 대사한다.

| scope 상태 | 의미 | 출력/정책 |
| --- | --- | --- |
| `operating_observed` | 현재 운영 적격이고 해당 범위의 관측이 있음 | 공통 엔진 평가, 후보 또는 부모 계승 |
| `operating_no_opportunity` | 필요한 관측 coverage가 충분하며 기회가 실제로 없음 | valid-empty, 부모 계승 |
| `operating_unobserved` | 적격이나 구독·예산·보관·전송 결손 등으로 판정 불가 | 사유·시간 구간 공개, 부모 계승; 기회 0으로 간주 금지 |
| `registered_nonoperating` | 계약에는 있으나 현재 entry 실행 범위가 아님 | 관측/재생을 분리 처리; 자동 거래 활성화 금지 |
| `not_tradable` | 종목·휴장·세션상 해당 거래 불가 | exact 사유와 as-of; 주문·가상 체결 생성 금지 |
| `custody_excluded` | Main 자동 관리 대상 수탁이 아님 | 역사 원장 보존, 자동 보유청산 금지 |

모든 범위에 disposition이 존재해야 한다. `coverage_complete`는 처리 결과 대사가 완전하다는 뜻이고, `economic_input_complete`와 다르다. `operating_unobserved`가 있으면 전체 데이터 관측 완료로 보고하지 않는다. collector 과부하를 유효한 무기회로 바꿔 전체 적용 성공을 주장하지 않는다.

전체 범위 적용을 위해 무제한 WS 구독·REST 호출을 추가하지 않는다. 기존 공유 source/subscription owner를 이용하고 범위별 공정한 대기열·예산·누락 카운터를 둔다. 종목 전체 census 및 무관측 표시는 필수이며, 실제 수집 SLA·보관기간·필요 용량은 AT2에서 측정하여 미달 범위를 보완한다.

## 4. 입력·모집단·계산 계약

### 4.1 원천과 identity

| 원천 | 필수 결속 | 용도 / 금지 |
| --- | --- | --- |
| 기계 ENTER_NOW | 원 native claim, scanner/fixed-watch generation, attempt/request, event/known-at 시각, 종목·경로·시장, 정책 hash | 기회 anchor. bucket 시각이나 후행 label로 native identity를 합성하지 않는다. |
| entry 보조 PASS | 원 요청/응답·generation·deadline, Main 인수 disposition | 실제 PASS와 Main accepted/rejected/deferred/unobservable 구분. 보유 EXIT PASS/VETO와 혼합 금지. |
| 진입 실행계획 | 해당 시점 ask/depth·가격 leg·총수량·자금/제약 snapshot·유효시간 | 기회 재생의 체결 가능성. PASS를 체결로 대체하거나 미래 가격으로 entry를 맞추지 않는다. |
| 0B/0D 후행 자료 | 원 item/venue/session, epoch/sequence, exchange/received/known-at 시각, signed 체결량, bid/ask depth, 원본 hash | 가격·강약·체결 가능성. sequence 연속만으로 긴 시간 공백을 정상 관측으로 인정하지 않는다. |
| 실제 거래 원장 | account binding, Main custody, position/record, buy generation, 주문·체결·partial·terminal | 실제 보유 replay와 비용 귀속. CF와 실제 동일 position으로 합산 금지. |
| 비용 | 체결/정산일·가용시각·revision, buy/sell 전 leg, 세금·수수료, 배분 근거 | actual PnL 전용. missing과 실제 0원을 구별하고 configured cost는 CF cost model로만 사용. |
| 보유 AI·안전 판단 | 원 판단시각/입력 hash, path, policy, veto 유효기간, safety state | 동일 조건에서 관측된 응답만 인과적으로 재사용. 다른 시점·후보의 AI 응답 합성 금지. |

모든 row는 `source_date`, `event_at`, `known_at`, `as_of`, `source_generation`, `policy/code/model hash`, `scope`, `owner`, `evidence_kind`를 가진다. `known_at > as_of`인 비용·응답·수정 자료는 그 cutoff의 상태 판정에서 제외한다. 정산 정정은 원래 거래 완료일에 귀속하되 새로운 지식 세대로 기록한다.

### 4.2 세 모집단을 분리

1. **실제 완료 거래:** `COMPLETED + valid profit_rate`, 정상 Main 실거래, 전 체결 수량 대사, 실제 비용 확인을 통과한 집합. 실현 손익·실제 실행 품질의 원천이다.
2. **실제 보유 경로 재생:** 같은 실제 entry/보유에 다른 exit 값을 대입한 paired 비교. 대체 SELL의 체결·비용은 모델이라는 점을 별도 표시한다. 실제 terminal 뒤 자료가 없으면 검열한다.
3. **ENTER_NOW+PASS 기회 재생:** 미진입 기회까지 포함하되 가격계획·후행 path·모델 비용·가상 체결을 확인한 `CF` 집합. 실제 completed ID나 실제 비용 원장을 생성하지 않는다.

ENTER_NOW 전체 → 보조 호출 여부/결과 → Main 인수 상태 → 가격계획 유효성 → replay fill 상태 → exit/검열 → 경제 적격성을 각각 대사한다. 각 단계의 `eligible + excluded + unobservable = input` ID 집합이 서로 겹치지 않아야 한다. timeout·VETO·not evaluated도 분모/원인 진단에 남기고 PASS 실험에 몰래 포함하지 않는다. 전체 census는 [보조 연구 population](../../src/engine/scalping/reversal_auxiliary_research_population.py)의 제한된 reservoir 표본을 사용하지 않는다.

같은 native opportunity의 재시도·여러 branch·collector 중복은 하나로 결속하되 실제 attempt 차이는 유지한다. position과 opportunity 연결은 별도 mapping이다. 실제 체결된 기회를 CF에 포함할 경우 paired 모델 검증용으로 표시하고 실현 손익과 중복 합산하지 않는다.

### 4.3 수익률과 비교

- 실현 순손익: `전체 SELL 체결대금 - 전체 BUY 체결대금 - 확인된 매수/매도 수수료 - 확인된 세금`. 분할·추가매수의 원가/수량은 기존 거래 원가 규칙을 동일하게 적용한다. 누락 비용을 0으로 채우지 않는다.
- CF 순손익: 가정한 체결 leg의 대금과 versioned 비용·slippage model을 사용하며 `modeled_net_*`로 저장한다. 실제와 동일한 수익률 분모를 명시하되 실제 실적 필드에 쓰지 않는다.
- 트레일링: 기존 net peak 시작 판정과 가격 peak 대비 drawdown 판정을 공통 함수로 실행한다. weak/strong 폭을 net 수익률 차이로 바꾸지 않는다.
- 정책 비교: 같은 entry·수량·기회 ID·경로·기간에서 부모와 후보 exit만 변경한 paired 비교가 기본이다. `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `paired_delta_net_krw`, 손실 꼬리·검열·노출·슬리피지 민감도를 함께 기록한다. 승률은 진단이다.
- 동시 기회의 개별 CF 결과를 합산하여 일일 실행 가능 순이익이라고 부르지 않는다. 별도 portfolio 재생에서 기존 자금·슬롯·중복 종목·예약 해제·partial 잔량 제약을 시간순으로 처리한 경우만 실행 가능 모델 손익을 낸다.
- 알려진 결손 row/window는 격리하고 제외 분모·최악조건 민감도를 공개한다. 전역 preflight 부재/손상, 격리 불가능한 identity 손실만 전체 경제 선택을 막는다. 임의로 건강한 범위까지 모두 0점 처리하지 않는다.

## 5. AT1 — 누적 비용 정정·봉인 재사용 결함 수리

수정 owner는 기존 [log archive](../../src/engine/log_archive_service.py), [trade review](../../src/engine/sniper_trade_review_report.py), [holding report](../../src/engine/holding_exit_observation_report.py), [비용 대사](../../src/engine/lifecycle/broker_cost_reconciliation.py)와 장후 wrapper다.

1. 누적 report가 실제 소비한 날짜별 trade projection/census/cost generation과 profile/run/cutoff를 정규화한 dependency manifest를 만든다. 분석기간의 휴장·valid-empty·missing도 명시한다. 임의 폴더 glob 결과로 소비 범위를 추측하지 않는다.
2. `input_window_generation_sha256`에 정렬된 전체 의존성 map을 결속한다. 원본 row를 manifest마다 복제하지 않고 기존 크기·파일 수 제한 아래 fingerprint를 소비한다. 결손 날짜를 빈 generation으로 합성하지 않는다.
3. 발행과 재사용 모두 각 소비 날짜의 현재 generation을 검사한다. 읽기 전후 generation이 달라지거나 일부 sidecar만 새 세대면 보류한다. data root·symlink·날짜·schema 불일치도 검사한다.
4. 과거 완료일 비용 정정은 그 날짜의 trade review/census/projection부터 재생성하고, 그 날짜를 소비하는 이후 누적 report·manifest·selector·summary·handoff의 영향을 계산한다. 실제 미소비 날짜의 비용 변경은 무관한 결과를 무효화하지 않는다.
5. 기존 봉인 파일을 같은 run identity로 덮어써 성공을 유지하지 않는다. 새 generation을 발행하고 부모 해시 CAS·원자적 교체 후 마지막 consumer까지 검증한다. 실패한 중간 세대는 selector나 latest가 가리키지 못한다.
6. legacy manifest에 전체 dependency 정보가 없으면 `window_dependency_unverified`로 분류한다. 유효한 원천으로 재구성할 수 있을 때만 새 봉인을 생성한다. unchanged 입력 재실행은 동일 결과를 재사용한다.

generation 검증의 비용도 관리한다. producer는 날짜별 bounded cost/census fingerprint와 소비 의존성을 한 번 만들고 같은 run의 report/manifest/summary는 검증된 snapshot handle을 공유한다. 독립 verifier는 봉인 hash·필수 내용 검증을 유지한다. 모든 consumer가 전체 기간 비용 파일을 다시 열거나 mutable 파일의 mtime만으로 비용 동일성을 인정하는 양극단을 피한다. 변경일→소비 report 역방향 index를 사용하되 index의 부모 inventory/hash도 검증한다. 최종 발행 직전 source 변경은 새 세대로 재검사하고 cache 성공으로 덮지 않는다.

이미 발행된 정책·PID 소비·당시 판단 영수증은 역사 증거로 보존한다. 비용 정정은 해당 경제 평가와 다음 선택/준비의 재검증을 요구하지만 과거 실행 기록을 새 비용으로 덮어쓰거나 실행 중 정책 값을 자동 수정하는 권한은 아니다.

종료 검사: 당일 입력을 전혀 바꾸지 않고 과거 날짜 비용만 revision한 fixture에서 오래된 report의 재사용·재봉인을 모두 거부한다. 정정 뒤 원래 완료일/holdout 귀속은 유지되고 새 비용·source hash가 최종 handoff까지 전파되어야 한다. 이 수리는 source 계약 수용으로 종료하며 양의 EV·자연 체결을 추가 수리 승인 조건으로 만들지 않는다.

## 6. AT2–AT3 — 공통 범위·수집과 실제 비용 coverage

### 6.1 공통 scope 및 후행 수집

공통 scope/identity adapter는 runtime과 offline이 함께 import할 수 있는 `src/engine/scalping/` 역할에 둔다. 신규 모듈이 필요하면 구현 착수 시 인접 owner와 위치 gate를 다시 확인한다. 새 `src/engine/*.py` root 모듈을 만들지 않는다.

- [공유 forward collector](../../src/engine/scalping/micro_reversion/forward_collector.py)와 [path capture](../../src/engine/scalping/micro_reversion/path_capture.py)의 현재 정상 source owner를 재사용한다. 역사적인 package 이름은 퇴역 전략 권한을 복원하지 않는다.
- ENTER_NOW 발생 시 기회 identity를 동결하고, 원 보조 응답과 Main disposition을 뒤이어 결속한다. 후행 자료 수집을 PASS가 도착한 뒤에만 시작해 응답 대기 구간을 잃지 않도록 기존 공통 원천의 해당 구간을 연결한다.
- capture 대상은 체결 종목으로 제한하지 않는다. 유효한 ENTER_NOW+PASS, 실제 보유, 해당 관측 의무가 있는 전체 scope를 동일한 수집 기준으로 처리한다. 가격·거래소·fixed-watch 여부로 비공개 축소하지 않는다.
- 실행 당시 사용 가능한 원천을 우선하고, 보관 원본으로 복원한 feature는 `reconstructed`와 별도 코드/version을 기록한다. 실제 native receipt가 없으면 reconstruction으로 native ID를 만들지 않는다.
- 저장은 날짜/종목/route/session/epoch 단위로 분할하고 immutable index·hash·coverage interval을 둔다. 완결되지 않은 partition은 연구 후보 선택에 포함하지 않는다. 보관기간은 최대 replay horizon·지연 비용 정정·holdout 필요기간을 포괄하도록 실제 저장량으로 산정한다.
- 공정한 bounded queue, 공유 subscription, 해제 시 lease ownership, 고정 감시와 scanner 간 starvation 검사를 수행한다. 진단 저장 실패가 기존 exit 안전 경로를 중단시키지 않도록 계산과 비동기 관측을 분리한다.

### 6.2 비용 배분 확장

모든 실제 Main position을 비용 census에 포함한다. 현 adapter가 배분 가능한 단일 당일 왕복 외에도 동일 종목 복수 position, partial BUY/SELL, ADD 후 청산, 익일 보유, venue 혼합, manual 혼재를 분리 평가한다.

exact execution 비용 영수증이 있으면 기존 대사 경로로 소비한다. 공식 일별/정산 집계만 있다면 계좌·거래일/정산일·주문/체결·수량/대금·전체 owner 귀속이 유일하게 성립할 때만 배분한다. 정산 거래 식별자를 주문번호로 해석하지 않는다. 금액 비례 임의 배분, manual 비용 전가, CF 비용의 actual 대입은 금지한다. 모호하면 `actual_cost_unallocated`와 막힌 항목을 기록하며, 거래를 census에서 삭제하지 않는다.

API 요청·응답 parser·FID·continuation 변경 전에는 [공식 API 참조 gate](../kiwoom-api-data-contract.md)를 수행하고 그 시점 upstream SHA·파일·조회시각을 구현 증거에 남긴다. 10/9 공식 revision 확인을 새 변경의 gate로 재사용하지 않는다. 과거 자료가 공식 API의 날짜/보관 계약으로 제공되지 않는다면 반복 호출하지 않고 역사적 결손을 확정한다.

## 7. AT4 — 전체 시장에 공통인 offline replay

### 7.1 runtime과 공유할 계산

기존 `trailing_exit_decision`, `trailing_mechanical_strength`, 시장 resolver를 공유하고 데이터 입출력 adapter만 구분한다. 재생 순서는 `원천 수신/가용 → 보유·peak·강약 상태 → 시작 latch → 최초 crossing → 기존 보유 AI 유예/해제 → SELL 가능시각 → 체결/잔량 → 비용`이다. signal, intent, submit, fill, terminal은 별도 event다.

기존 [entry price replay](../../src/engine/scalping/strategy_owner_replay.py)의 native opportunity·실행 leg 검증을 재사용할 수 있으나 그 모듈의 180초 고정 exit 모델을 trailing 엔진으로 채택하지 않는다. `entry_first_signal_exit_research`와 `entry_mechanical_exit_research`의 과거 report 스키마·연구 범위는 보존하고 새 universal entrypoint가 공통 엔진을 호출하게 한다. 실제 caller가 있는 경우에만 기존 호환 wrapper를 남기고 중복 구현은 제거한다.

### 7.2 시간·체결·AI의 한계 처리

- 모든 세션의 시작/종료·청산 가능 시간을 공통 contract로 결정한다. 고정 15:30 종료를 제거한다. 1/3/5/10/20/30/60분 진단 horizon과 실제 holding replay 종료 조건을 구별하고, 60분 초과/익일 보유도 관측 coverage가 있으면 이어서 재생한다.
- 거래정지·세션 전환·휴장에는 거래가 가능한 다음 시각의 원천을 요구한다. 없는 호가에서 terminal을 만들거나 정지 전 가격으로 매도하지 않는다. horizon 끝의 평가가격만 있으면 mark-to-market 진단으로 남긴다.
- 체결은 같은 경로의 executable ask/bid와 depth, 주문 가격·유효기간·잔량을 적용한다. full, partial, no-fill, censored를 분리한다. 관측 구간이 완전하여 미체결이 입증된 경우만 no-fill이며, 데이터 부재는 no-fill이 아니다.
- 부분 청산 뒤 잔량과 ADD는 실제 수량/원가/세대 전이를 처리한다. ADD를 새 독립 기회로 재집계하거나 latch를 임의 초기화하지 않는다. runtime이 정의한 상태 승계를 그대로 재생한다.
- 후보가 관측된 AI 질문시점·입력과 달라지는 최초 지점에서 운영 AI 포함 replay는 검열한다. 미래 응답을 과거 시점에 재사용하지 않는다. 별도 `mechanical_only_cf` 비교는 가능하나 full operating replay나 AI 포함 정책의 경제 증명으로 표시하지 않는다. 신규 유형을 위해 과거 AI를 재호출하지 않는다.
- actual SELL 이후에도 후행 수집이 있으면 CF를 이어갈 수 있다. 단, 실제 체결의 존재만으로 그 이후 가상 보유의 응답·depth·cost를 충족했다고 보지 않는다. bid 잔량 부족·데이터 시간 공백·identity 충돌마다 중단 원인을 보존한다.
- 분봉 OHLC만 있는 구간은 같은 봉 안의 고점·저점 도달 순서, trigger 당시 bid와 잔량을 확정할 수 없다. 해당 구간은 별도 가격경로 진단/상하한 분석으로 표시하고 tick/depth 기반 실행 재생과 같은 증거 등급으로 승격하지 않는다.

### 7.3 비교 설계

날짜 순 train/holdout을 동결하고 같은 opportunity/position의 반복 관측과 겹치는 경로가 양쪽에 섞이지 않도록 group/purge한다. 기준은 clean baseline 이후이면서 현재 policy-refresh forward 경계 이후다. 현재 값은 6/5 clean, 9/29 forward이며 더 오래된 자료는 audit/복원 검증용이다.

부모·후보는 공통 적격 ID에서 비교하고 제외 ID/시간/종목/시장/금액을 함께 낸다. 미래 수익률로 유형을 붙이거나 holdout 결과로 분류 임계값을 재학습하지 않는다. symbol/date concentration, 각 시장·유형·강약·UNKNOWN 노출, slippage 0/30/100bp의 기존 stress, 손실 꼬리와 coverage 악화를 확인한다. 특정 종목 하나의 수익으로 전체 정책의 개선이라고 결론내리지 않는다.

기존 실제 거래 selector의 최소 7개 유효 날짜, train 30·holdout 10 및 2개 이후 holdout 날짜와 경제/꼬리 조건은 이 계획에서 완화하지 않는다. 새 CF 연구는 별도 evidence schema로 기준을 선언하고 실제 증거와 표본 수를 합산하지 않는다. 모든 종목마다 동일 최소 체결 수를 요구하여 전체 적용을 막는 방식도 사용하지 않는다. 표본이 적은 유형은 부모를 계승한다.

## 8. AT5 — 시장 부모 + 상황 유형 + 동적 강약

### 8.1 첫 버전의 분류와 시점

유형은 종목의 영구 성격이 아니라 그 보유의 진입 시점에 관측된 상태다. 첫 버전은 다음 소수의 상호 배타적 유형을 연구하며, 현재 M1 강약 parameter는 고정한다. 유형·숫자 3축·강약 8개 parameter를 동시에 대규모 탐색하지 않는다.

| 유형 후보 | 당시 관측 feature | 연구 가설 |
| --- | --- | --- |
| `HIGH_VARIABILITY` | 완료 봉의 변동폭/가격, spread/가격, 연속 원천 품질 | 변동성으로 생긴 짧은 흔들림과 실제 악화를 구분할 폭이 필요한가 |
| `TREND_CONTINUATION` | 완료 봉 trend/구조, session VWAP 상대 위치, 기존 거래량·수급 context | 추세 지속 상태에서 시작/되돌림 조합이 부모보다 유리한가 |
| `REBOUND_RANGE` | 이전 하락·반등 구조와 추세 지속 미충족, 기존 range context | 반등/횡보 상태에서 부모 대비 다른 익절 조합이 유리한가 |
| `BASE` | 나머지 상태 또는 분류 근거 부족 | 시장 부모 그대로 사용; 결손 여부는 별도 reason |

우선순위는 `HIGH_VARIABILITY → TREND_CONTINUATION → REBOUND_RANGE → BASE`로 동결한다. 구현 때 feature 정의·필수 원천·missing 규칙·유한 임계값 후보 집합을 먼저 manifest로 등록한다. 훈련 구간에서만 임계값을 정하고 이후 holdout에 고정한다. 이 문서가 새로운 수치 임계값을 운영 승인하지 않는다.

첫 feature 계약은 기존 공유 완료 봉·VWAP·호가에서 계산한다. 예를 들어 `range_pct = 100 × (구간 최고가 - 구간 최저가) / 마지막 종가`, `return_pct = 100 × (마지막 종가 / 구간 시작 종가 - 1)`, `trend_efficiency = |마지막 종가 - 시작 종가| / Σ|인접 종가 변화|`, `vwap_distance_pct = 100 × (종가 / session VWAP - 1)`, `spread_pct = 100 × (ask - bid) / mid`다. 되돌림·반등 구조도 anchor 이전 완료 봉의 peak/low/close만 사용한다. 실제 구간 길이와 각 threshold 후보를 manifest에 등록한 뒤 재생하며, 분모 0·구간 결손·다른 venue 혼합은 feature 결손으로 처리한다. 공통 feature owner에 이미 있는 값을 우선 사용하고 장중 별도 history 조회를 만들지 않는다.

필수 feature 결손으로 상위 유형 조건을 평가할 수 없으면 임의로 다음 유형을 확정하지 않고 `BASE + classification_source_gap`으로 처리한다. 분류를 완전히 수행한 `BASE`와 결손으로 부모를 사용하는 경우를 통계에서 구분한다. 원천이 충분한 기존 데이터를 이용한 모든 시장 공통 분류기이며 삼성 전용 entry observation helper를 범용 원천으로 오인하지 않는다.

최초 실제 BUY 시점에 사용 가능했던 entry context로 `situation_type`을 정하고 position에 pin한다. CF는 모델 entry fill 시점까지 알려진 동일 계약의 context를 사용한다. 뒤늦게 받은 자료로 이미 고정한 유형을 수정하지 않는다. restart에는 저장된 유형/feature/policy hash를 복원한다. 기존 보유에 pin이 없으면 확인된 시장 부모를 사용하고 `legacy_context_unbound`를 남긴다.

유형 계산은 같은 entry/feature generation에 한 번 수행한다. 장중 매 tick마다 완료 봉을 다시 집계하거나 파일·원문 AI payload를 재해석하지 않는다. 기존 공유 feature에 필요한 값이 없으면 그 관측의 `BASE + classification_source_gap`을 반환하고 추가 REST·AI 조회를 발생시키지 않는다. 이 결과가 다른 신호·다른 세대의 결손까지 영구 cache하는 것은 아니며 원 identity별로만 유지한다.

보유 중 강약은 기존 M1 방식대로 갱신한다. 유형은 첫 버전에서 ADD나 매 tick마다 재분류하지 않는다. ADD buy generation에도 원 situation pin과 runtime 상태 승계 규칙을 함께 기록한다. 이는 강약 변화 대응을 유지하면서 시작률 이동·latch reset·무한 유예를 막기 위한 경계다. 보유 중 유형 전환은 별도 검증 없이는 추가하지 않는다.

### 8.2 정책 해석과 변경 가능 값

정책 조회는 `정확 날짜의 승인 부모 → 현재 시장 → 해당 situation override(유효할 때만) → 현재 M1 강약에 맞는 폭` 순서다. 세션 전환에서는 기존 시장 전환·latch·유예 해제 규칙을 유지하고 새 시장의 같은 pin 유형을 조회한다. peak/crossing을 초기화하지 않는다. 상황 분류 version/hash도 수치 vector와 함께 policy identity에 포함한다.

유형을 고정한 `classification_origin_hash`와 각 판단에 적용한 `effective_policy_hash`를 구별한다. restart/정책 교체 후에도 기존 pin을 새 분류기로 소급 재분류하지 않는다. 새 정책이 옛 pin schema를 해석하지 못하면 검증된 시장 부모로 처리하고 사유를 남긴다. 이미 최초 crossing에서 동결된 값·AI 유예 상태는 기존 runtime의 승계 계약을 따르며 서로 다른 정책의 수치 일부를 섞지 않는다.

| 값/규칙 | 장후 변경 범위 |
| --- | --- |
| 시작률·weak/strong 폭 | 기존 허용 grid·안전 제약 안에서 시장/유형별 후보 산출 가능. 부모와 증거 결속 후 기존 선택 owner로 변경. |
| 상황 분류 임계값 | versioned feature·유한 후보·train/holdout으로 연구 가능. 별도 classifier hash와 검증 필수. |
| M1 강약 parameter | 기존 8개 bounded parameter의 기존 owner를 유지. 첫 상황 정책 실험에서는 동결; 후속 실험에서 한 변경 원인씩 검증. |
| Main entry/AI PASS 정책, 가격·수량·자금·슬롯 | 이 exit family의 변경 대상이 아님. 원래 정책/가드 입력으로만 소비. |
| hard/protect/emergency, custody, 세션 거래 허용, provider, 주문 실행 | 장후 최적화로 변경 불가. |
| 보유 AI 5 path×3 시장 baseline, 최대 유예·악화 해제 | 기존 owner·승인 유지. 새 유형으로 AI 권한이나 HP6 자동 투표 최적화를 묵시 확장하지 않음. |

새 typed schema는 모든 시장과 유형의 effective 값을 완전히 해석할 수 있어야 한다. 희소 override를 저장하더라도 부모 hash와 `parent_carry`를 명시한다. 잘못된 유형/policy hash는 새 임의 default를 적용하지 않고 검증된 부모 또는 기존 runtime의 안전한 거부 규칙으로 처리한다. loader·semantic monitor·replay·bootstrap의 schema 전환은 같은 변경 묶음으로 검증한다.

## 9. AT6 — 장후 재생성을 통한 초기정책 생성

### 9.1 가능 여부: 현재 가능한 것과 추가 구현이 필요한 것

**초기정책 생성은 가능하다. 다만 승인 부모를 계승하는 초기정책과 데이터로 새로 계산한 정책을 구별해야 한다.**

| 초기 결과 | 현재 가능 여부 | 필요한 조건 |
| --- | --- | --- |
| 기존 시장 정책의 초기/계승 bundle | 기존 bootstrap이 이미 지원한다. 10/12 준비에는 세 시장 0.4/0.4/0.8이 존재한다. | exact-date 승인 부모·operator lock·hash 확인. 재생성으로 최적화된 값이라고 표시하지 않는다. |
| 새 상황 schema의 전체 범위 초기 bundle | AT5–AT6 구현 후 가능. 모든 유형이 자기 시장 부모를 계승하는 동등 정책으로 시작할 수 있다. | 변환 전후 유효값·강약·runtime 판정 동등성, 전체 scope 완결성. 승인 초기값 계승에 새로운 경제 증명 gate를 추가하지 않는다. |
| 실제 거래로 새로 최적화한 초기 후보 | 현 10/8 봉인 자료만으로는 불가. 원천/비용 복구 후 조건부 가능. | AT1 수리, 날짜별 raw/census/비용 복구, 기존 모집단·holdout·선택 조건 충족. |
| ENTER_NOW+PASS를 추가한 유형별 초기 연구 후보 | 현 selector는 이 모집단을 소비하지 않으므로 단순 재실행으로는 불가. AT2–AT6 후 조건부 가능. | exact PASS·가격계획·후행 경로·모델 비용·분리된 CF 검증. 후보 생성과 실거래 적용 권한은 별개. |

10/10 읽기 확인에서 9/29–10/8의 `holding_actual_costs/<date>/*.json`은 각 날짜 0개, `holding_broker_cost_sources/<date>.json`은 10/8만 존재했다. 일부 과거 trade snapshot/압축본은 존재하지만 현재 봉인·profile·generation 검증을 충족하지 않는다. 특히 9/30은 파일 존재 자체와 보고서가 기록한 missing 사유가 다르므로 원 producer가 당시 무엇을 소비했는지 확인해야 한다. 파일 목록만으로 복구 가능이나 비용 충분을 판정하지 않는다.

따라서 현재 확정할 수 있는 것은 **동등 초기정책 계승 경로가 있고, 최적화 초기값은 원천 census 및 새 재생 구현 이후 판정해야 한다**는 점이다. 복구로 과거 실제 실적을 되살리는 것은 신규 수익 창출이 아니다. 재생성만으로 없던 호가·PASS·비용·native receipt를 만들 수 없다.

### 9.2 최초 생성 절차

아래는 구현 후 수행할 절차이며 현재 wrapper 실행 지시가 아니다. 재생 준비/계산 CLI는 `src/engine/automation/` 역할 아래 기존 orchestrator를 우선 확장한다. 실제 승인 경로와 분리된 output root, dry-run, manifest 입력을 지원하고 기본값은 read-only preflight로 한다.

1. **정확한 입력 동결:** source date D, target date T, clean/forward 경계, data root, 코드/부모 정책/분류기 hash, 분석창과 cutoff를 고정한다. 현재 기존 증거 점검은 D=10/8이지만 실제 실행 날짜에는 최신 유효 부모와 D/T를 다시 정한다. 10/12 적용을 미리 약속하지 않는다.
2. **범위·원천 preflight:** 모든 종목·시장에 대해 native/PASS/가격계획/0B·0D/체결/비용/census의 존재·크기·연속성·schema·세대를 목록화한다. 읽기 한도 내 `recoverable`, `irrecoverable`, `not_required`, `not_observed`를 구분한다. 원천을 전수 replay하기 전에 필요한 partition과 예상 시간/용량을 출력한다.
3. **복구 계획 확정:** 복구 가능한 날짜/partition만 지정한다. gzip/raw와 sealed projection의 우선순위·중복·원장 귀속을 검사한다. 공식 과거 비용 조회가 필요한 경우 API gate와 허용된 source-only 절차를 먼저 충족한다. 이미 회복 불가로 확인한 입력을 반복 재생성하지 않는다.
4. **선행 원천 재생성:** 비용 → 원래 완료일 trade review/census/projection → 날짜별 source 봉인 순으로 생성한다. 이어 AT1의 의존 그래프에 따라 영향받은 누적 holding report를 새 generation으로 생성한다. 진행 중 wrapper와 같은 파일/세대를 동시에 수정하지 않는다.
5. **전체 scope 재생:** 모든 유효 실제 보유/기회 partition을 공통 엔진으로 재생한다. 실행 미대상·valid-empty·검열·결손도 output에 남긴다. source hash가 같으면 검증된 partition cache를 재사용하며 후보 grid마다 전체 원천을 다시 읽지 않는다.
6. **초기 후보 계산:** 시장 부모 대비 상황별 후보를 train에서 선정하고 동결 holdout에서 평가한다. 실제/CF별 결과·노출·coverage를 분리한다. 적격 증거가 없거나 개선이 없으면 해당 시장/유형은 부모 값을 계승한다. 데이터 부족을 임의 중앙값·전 종목 평균 최적값으로 대체하지 않는다.
7. **불변 초기 bundle:** 모든 scope에 effective policy, `parent_carry|qualified_candidate|hold_source_gap|hold_sample_or_edge`, 이유, parent/candidate hash, evidence kind, source manifest, target/effective date, rollback을 기록한다. bundle 생성 성공과 후보 적격/적용 가능은 각각 다른 필드다.
8. **검증·선택 분리:** 연구 bundle은 기본 `allowed_runtime_apply=false`, `runtime_effect=false`다. 동등 부모 계승은 기존 승인 범위·값 동등성으로 검증하고 별도 경제 gate를 추가하지 않는다. 경제 변경은 기존 family selector/정확 부모 CAS/경제·안전 기준을 통과해야 한다. CF만으로 실거래 실행 품질·실현 PnL 승인을 대체하지 않는다.
9. **허용된 인계:** 선택된 결과만 source bundle → runtime summary → strict `--require-summary-handoff` → controller/finalization → 정확 날짜 PREOPEN으로 연결한다. 새 source·코드·checklist hash가 바뀌면 준비 세대를 새로 만들고 이전 prepared receipt를 현재 성공으로 재사용하지 않는다. 마지막에 실제 PID 정책 hash 소비와 자연 exit 결과를 별도로 확인한다.

`initialization_manifest`에는 단계별 input/output hash, ID partition counts, 선택/계승 사유, 재개 지점, 비용/시간, 오류·원천 결손을 남긴다. 새 파일명과 schema는 구현에서 확정하되 기존 `holding_exit_observation` source bundle을 유일한 상위 owner로 사용하고 경쟁하는 별도 정책 publisher를 만들지 않는다. 연구 output은 운영 `current`나 봉인 snapshot을 직접 덮어쓰지 않는다.

### 9.3 초기화 종료 조건

정상 초기화는 모든 scope에 해석 가능한 부모 또는 적격 후속 정책이 있고, source/evidence/계승 이유가 검증되는 상태다. 모든 유형에 새 숫자가 생겨야 성공인 것은 아니다. `initial_bundle_ready`, `optimized_candidate_ready`, `selected_for_target_date`, `prepared_verified`, `actual_pid_consumed`를 따로 기록한다.

불완전 원천이 있어도 전체 scope 부모 계승 bundle은 만들 수 있다. 다만 원천 결손을 정상 연구 완료로 표시하지 않는다. 전역 identity/preflight가 손상되면 새 경제 후보 생성은 중단하고 검증된 기존 정책을 유지한다. 복구 불가 데이터는 수집 보완과 자연 자료 축적 owner로 넘기며 같은 입력의 반복 재생성을 예약하지 않는다.

## 10. AT7 — 장후 선택·소비·성능 계약

### 10.1 producer에서 마지막 consumer까지

`native/보유 원천 → 날짜별 source/cost projection → 전체 scope replay → holding_exit_observation → source bundle/selector → runtime summary → strict/controller/finalization → bootstrap → runtime loader → semantic monitor/PID`를 하나의 연결표로 검증한다.

[mechanical selector](../../src/engine/automation/scalp_trailing_mechanical_policy_apply.py)는 현재 실제 completed report와 one-market candidate를 검증한다. 새 상황/CF 필드를 넣기만 하고 현재 validator를 우회하지 않는다. evidence kind별 적격성, 전체 scope 부모 계승, typed policy/hash, 같은 stage 충돌·부모 CAS·rollback을 명시한 versioned 선택 계약으로 확장한다. CF 연구 후보만 있을 때 기존 real selector가 자동 승격시키지 못하도록 회귀를 둔다.

[runtime bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py), [runtime summary](../../src/engine/runtime_approval_summary.py), [summary handoff](../../src/engine/automation/postclose_summary_handoff.py), [holding semantics](../../src/engine/scalping/holding_profit_exit_semantics.py)의 source/code pin·유형 hash·날짜·수탁·signal/buy generation 검사를 함께 보완한다. selector나 semantic PASS를 SELL/terminal/economics로 바꾸지 않는다.

처음부터 전체 scope engine을 연결하되 새 typed schema의 `BASE` 및 부모 계승 결과는 기존 판정과 완전히 같아야 한다. pending/retry/fast/normal exit와 restart도 동일하다. UNKNOWN과 stale source는 기존 안전 처리이며 situation 분류가 안전 guard를 대신하지 않는다.

### 10.2 비용과 성능 수용

다음 TP1–TP7은 구현할 성능 개선 묶음이며 이미 달성한 성능 수치가 아니다. [시장원천 정리의 기존 PF1–PF5와 성능 gate](main-market-source-consolidation-and-micro-reversion-retirement-cleanup-implementation-plan-2026-10-09.md#61-성능-저하-방지개선의-구체-변경-묶음)는 구현 착수 때 최신 source/selected release로 확인하여 재사용한다. 완료된 공통 writer 개선을 중복 구현하거나 아직 미측정인 Main/장후 경로를 이번 계획의 성공으로 가져오지 않는다.

| 묶음 | 변경과 실제 owner | 감소 목표 / 보존할 계약 |
| --- | --- | --- |
| TP1 사전 준비·메모리 조회 | `trailing_mechanical_policy`·기존 bootstrap/loader가 generation별 시장/유형 effective map을 검증해 고정한다. classifier config normalization/hash와 situation feature는 동일 identity에서 재사용한다. | warm 판단에서 정책 파일/report read·전체 hash·전체 scope/cell 순회 0. 날짜/expiry/승인 hash·기존 safety는 계속 확인. 기존 M1의 이미 구현된 cache를 재사용하고 불필요한 새 cache를 겹치지 않음. |
| TP2 공유 호가·bounded 관측 | 기존 Main/0B·0D owner의 immutable snapshot/feature를 참조한다. 이벤트는 해당 symbol/item/route/epoch의 활성 보유·기회에만 전달한다. writer에 scalar envelope를 넘기고 통계/JSON/hash는 기존 적절한 준비·writer 경계에서 처리한다. | 같은 snapshot의 중복 복사/직렬화/원천 hash 감소, 새 동기 REST·AI·정산 I/O 0. 원 신호·응답·custody/order intent의 필수 저장을 진단 queue로 옮기지 않음. |
| TP3 한 번 decode·feature 준비 | holding/entry replay adapter가 날짜·symbol·route·epoch partition을 한 번 정규화하고 exact-ID/time index·원천 hash를 만든다. 같은 run의 report/selector는 검증된 projection을 공유한다. | 동일 partition 중복 JSON decode·source-only feature 계산 0. 독립 verifier의 필수 byte/hash 검증은 유지하며 검증 읽기와 파싱 읽기를 따로 계수. |
| TP4 상태 공유 범위 제한 | M1 raw feature 경로와 numeric candidate 독립 계산을 분리한다. source/config·position 초기상태·buy generation이 같은 경우에만 강약 경로를 공유한다. | 같은 classifier/config의 중복 계산 감소. 다른 position reset·ADD·epoch·정책·AI 인과 분기 뒤 상태를 공유하지 않으며 histogram/강약 노출·검열 동일성 검증. |
| TP5 후보 block 집계 | 같은 effective vector+classifier+입력 상태 후보를 canonical key로 dedup하고 alias를 남긴다. 후보 block·position partition별 최소 결과를 저장하고 report 상세 객체는 마지막에 만든다. | candidate×position×전체 event dict 상주 제거. 원 grid·모든 후보의 common-ID/검열·holdout·tail/slippage 계산을 유지. 속도만을 위해 후보를 누락하지 않음. |
| TP6 증분 비용·의존성 | AT1의 날짜별 비용/census 의존 map과 계층 cache를 연결한다. 비용 정정은 해당 position 및 그것을 소비한 report/선정만 무효화한다. | cost-only revision으로 변경 없는 0B/0D raw를 다시 decode하지 않음. net 시작판정·모델 PnL·순위·holdout에 영향을 주는 계산은 재실행. |
| TP7 checkpoint·최종 상세화 | 완결 partition/cache를 명시적 output root에 봉인하고 실패 뒤 그 지점부터 재개한다. full event journal은 incumbent/최종 후보와 검열 반례 중심으로 별도 bounded artifact에 둔다. | 동일 입력 warm 재파싱 0, 정상 재개 때 완료된 partition replay 0. 모든 row의 최소 identity/result/reason·집계 재현 근거는 보존하고 상세 생략을 모집단 삭제로 사용하지 않음. |

TP1의 handle은 PID/start generation·적용일·승인 manifest/code·부모/lock hash에 결속한다. 장중 lookup이 파일을 glob하거나 validation을 동기 재구축하지 않는다. 기존 owner의 승인된 정책 갱신/무효화 경로만 사용하고 새로운 reload worker를 만들지 않는다. pin된 situation 원 분류와 현재 수치 정책 hash를 구분하며, 기존 crossing·유예/주문 상태의 원자적 승계를 유지한다.

TP2는 전체 대상 적용을 유지하면서 WS callback에서 전체 universe나 모든 active opportunity를 순회하지 않는다는 뜻이다. universe/index 갱신은 세대 변경/기존 관리 주기에서 수행한다. 공유 snapshot key에는 item/route/epoch/sequence/시각·source generation을 포함하고 mutable stock/ws 객체를 queue에 넣지 않는다. 참조 수·최대 보관시간·종료 시 해제를 제한한다. queue full에서 Main 동기 append·무한 retry로 돌아가지 않으며 범위별 결손을 남긴다. 정상/목표 burst의 새 손실은 성능 수용 실패다.

TP4에서 공유 가능한 것은 후보와 독립인 계산뿐이다. numeric 후보의 조기 청산·실제/가상 ADD·상황 pin·AI 유예가 상태의 후속 경로를 바꾸면 그 지점부터 별도 계산한다. 기존 `HISTORY_LIMIT=120` bounded history의 정렬·누적을 새 rolling 자료구조로 바꾸는 작업은 프로파일에서 병목이 확인된 경우에만 수행하며 out-of-order/duplicate/시간창·재접속·restart 반례에서 기존 classifier와 같아야 한다. 인과 상태 변경을 단순 성능 refactor로 승인하지 않는다.

TP5의 common cohort는 모든 비교 후보의 적격 ID 교집합을 먼저 확정하고 그 ID에서 동일 train/holdout 통계를 산출한다. 메모리 제한 때문에 두 단계가 필요하면 최소 결과/ID bitmap·정렬 projection을 임시 저장하고 다시 집계한다. 원본 raw를 다시 읽거나 후보마다 독립 분모로 계산하지 않는다. exact quantile·tail·worst-case 제외 notional은 bounded 정렬/spill로 보존하며 근사값을 같은 계약 이름으로 대체하지 않는다. 후보 block마다 큰 source 객체를 복제하는 process pool은 기본 구현에 넣지 않는다.

### 10.3 계층 cache와 두 계획의 합산 자원

cache는 다음 네 계층으로 나눈다. 최종 결과에 필요한 key를 누락하지 않되 부모/비용/적용일 변경만으로 원천 decode를 다시 하지 않는다.

1. `source_decode`: 명시적 data root, immutable partition bytes/inventory hash, source/parser/schema·identity/clock/route 계약.
2. `feature_path`: source hash, feature/config version, item/epoch, position/기회 초기상태가 필요한 계산의 해당 identity, event/known-at/cutoff·window. 순수 가격 feature와 position 상태를 구분한다.
3. `replay`: feature hash, position/opportunity·buy generation·상황 pin, parent/candidate vector·classifier config, 비용/slippage model과 AI 증거. net 시작판정에 영향받는 비용 변경은 여기부터 재계산한다.
4. `selection_handoff`: 모집단·dedup·train/holdout/purge·grid·분류·부모·source/effective date·선정 코드와 실제 비용 증거. 날짜 추가로 split 경계가 바뀌면 aggregate/선정을 다시 계산한다.

cache는 source 증거를 대체하지 않는다. producer에서 한 번 확인한 immutable generation을 같은 run에서 재사용하고 독립 verifier는 내용·manifest를 다시 검증한다. mutable 파일은 mtime/size만으로 동일성을 인증하지 않는다. append/late partition·같은 크기 교체·압축표현 전환·partial write·root 변경·schema/algorithm 변경을 시험한다. 손상 cache는 bounded 재구축 대상이며 필수 원천 손상은 source gap이다. 읽기 전후 generation 변경을 발견하면 게시하지 않는다.

[제출 지연 계획의 관측·원천 재사용](pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md#44-장중-비용을-제한하는-구현-계약)과 공통인 source decode/exact identity·clock·snapshot만 공유한다. 그 계획의 `signal_ready/price_ready` 가격 개선과 이 계획의 실제/CF 손익·M1/AI 상태·후보 선정은 독립 owner다. 통합 feed BBO를 물리 venue 체결 증거로 바꾸거나 두 family의 표본·경제 권한을 합치지 않는다.

S0/AT0에서 한 개의 `performance_budget` manifest를 함께 참조한다. host/선택 baseline code, 전체 universe·기회·event 수와 burst schedule, queue/event/bytes 상한, process별 및 **합산** RSS/CPU/I/O/temp disk, worker 수, postclose/다음 PREOPEN 가용 시간창, source/candidate hash·측정 표본/해상도를 고정한다. 수치는 현재 상한·baseline 측정으로 채우고 미정인 상태에서 전체 확대를 완료 처리하지 않는다. 두 모듈에 같은 메모리 여유분을 각각 배정하지 않는다.

후속 실제 코드 대조에서 `research_input_budget.Claim`은 process-local이고 stage dispatcher는 두 자식을 허용함을 확인했다. [잔여작업 W2](main-trailing-delay-residual-work-completion-plan-2026-10-10.md#5-w2-상한-초과를-처리하는-분할재개)의 기존 slot 가중 접수·heavy job 순차 실행으로 합산 예산을 구현한다. scope 6개 disposition, 기회/실제 거래 장부, shard의 논리 digest/물리 hash를 구분하고 cache뿐 아니라 정렬/결과/old-new 세대 공존의 peak disk를 측정한다. 최종 source bundle은 실제 profile snapshot→holding report caller에서 생성하고 W5의 전환 세트·실패 복구 및 당일 selector 순서까지 검증한다.

기존 admission/scheduler/단일 writer를 사용한다. 두 family가 같은 source를 요구하면 봉인 projection을 공유하고 필요하면 기존 순차 stage에서 실행 순서를 조정한다. 새 worker·process pool·cron으로 비용을 떠넘기지 않는다. due 재평가의 실제 AI 호출 수·기존 entry/exit queue wait도 합산하며 cap/deadline·Provider 예산을 늘려 통과시키지 않는다. 일정/동시성 변경이 필요하면 그 구현 변경에서 운영 owner·문서·회귀를 함께 갱신한다.

입력이 기존 읽기 상한을 넘으면 상한 우회·최근 기간 절단 대신 제한된 partition/job 단위로 재개 가능한 처리를 구현한다. 기존 pre-submit compact의 64MiB 전체 decode 상한은 현재 코드의 제약이며, 더 큰 모집단 지원에는 분할 작업·전역 census validator·전체 run 예산을 함께 바꾸는 명시적 구현이 필요하다. 단순히 파일당 64MiB로 재해석하지 않는다. 메모리에 남는 index·중복 set·candidate bitmap·cache·spool을 모두 합산한다. 아직 처리하지 않은 partition은 `resource_deferred/in_progress`이고, 모든 범위의 disposition과 필수 계산이 닫히기 전 전체 재생 완료/경제 후보를 발행하지 않는다. preview sampling 산출물은 전체 초기정책 선택의 입력이 아니다.

### 10.4 성능 비교와 적용 gate

[기존 runtime 성능 계측](../../src/engine/monitoring/runtime_performance.py)의 bounded counters/histogram을 우선 사용한다. `loop_first`와 `loop_work_warm`, 0B/0D callback, lock wait/hold, native→claim→machine, exit wake→판정, 최초 crossing→유예 해제/SELL 가능시각, queue/writer enqueue→fsync·drain, CPU/RSS/thread/read/write bytes를 분리한다. 새 대용량 성능 원장을 만들거나 매 event마다 분위수/JSON을 lock 안에서 계산하지 않는다.

비교는 (a) 기존 지원 범위의 동일 source·policy/vector에서 의미 동등성과 처리 비용, (b) 새 종목·모든 지원 시장·전체 기회가 포함된 목표 부하의 절대 예산/coverage 두 종류를 모두 수행한다. 구버전의 미지원 row skip 시간을 신버전 전체 계산의 분모로 삼지 않는다. 새 정책이 의도적으로 바꾸는 판단은 별도 기대값 fixture로 검증하고 성능 refactor의 판단 차이와 구분한다. 지연 정책과 함께 측정할 때 30~180초의 의도한 대기와 due 이후 처리 지연을 나눠 보고하되 총 제출시간도 보존한다.

| 시나리오 | 필수 비교 |
| --- | --- |
| 정상 혼합·cold/warm | 삼성/고정 감시/scanner·신규 종목, PRE/REGULAR/AFTER, 다중 실제/CF 기회와 holding/fast/normal exit. 기동 준비 비용을 warm 측정 밖에 숨기지 않음 |
| 목표 burst·due 군집 | 관측 최대 유입과 현재 상한 내 합성 burst, 여러 기회 동시 due·청산, queue fairness·추가 signal 만료·보유 평가 진척 |
| 오류·경합 | slow fsync·source queue full·snapshot/summary 동시 실행·reconnect/정책 무효화. 의도된 관측 보호 중단을 정상 손실과 분리하되 Main/청산 지연은 계속 검사 |
| 장후 cold/warm/delta | 최초 전체 입력, 같은 generation, 한 source partition/과거 cost-only 정정, split 경계 이동, cache 손상, 중단/재개. incremental 결과와 clean recompute 비교 |
| 두 family 결합 | 기존 자원 admission 아래 관측+due 재평가+holding 계산, 장후/재생 공존. 합산 RSS/CPU/I/O·전체 종료시간·Main/청산 tail·writer drain과 coverage |

baseline/candidate를 같은 host·설정·동결 bounded fixture/projection으로 번갈아 각 3회 측정한다. workload hash·warmup·표본수·해상도를 후보 결과 전에 고정한다. 역사 raw full scan·정식 발행을 성능 측정 때문에 3회 반복하지 않으며 cold cache는 task-local 범위만 초기화한다. 불리한 GC/queue/실패/만료 표본을 제외하거나 통과까지 무변경 재측정을 반복하지 않는다. 작은 N에서는 개별값/max를 제시하고 p99를 새 자의적 합격선으로 만들지 않는다.

| gate | 수용 / 실패 처리 |
| --- | --- |
| 의미·coverage | 동일 비교의 identity·판정·금액·공통 ID·검열·holdout에 설명되지 않은 차이 0. 정상/목표 burst의 새 누락·중복·deadline miss 0. 조기 종료·샘플/후보/시장 삭제로 단축하면 실패 |
| 절대 guard·합산 자원 | 기존 경로별 safety·TTL·resource guard와 동결된 전체 예산 모두 준수. collector 0B 전용 수치/표본 기준을 Main/0D 기준으로 전용하지 않음. baseline 자체 실패도 새 허용치로 쓰지 않음 |
| 상대 비악화 | 같은 시나리오의 충분한 표본에서 지연 p95/p99/max·drain 및 동등 작업 wall/CPU/RSS의 후보 3회 중앙값 ≤ baseline 3회 최대값+사전 해상도, 후보 최악값 ≤ baseline 최대값+(최대−최소)+해상도. 기존 더 엄격한 경로 guard가 우선. 평균 개선으로 tail 악화 상쇄 금지 |
| 구조적 절감 | TP1 warm policy/report I/O 0, TP2 같은 snapshot 중복 작업 감소, TP3/TP6/TP7 동일 partition 중복 decode/feature/replay 감소, TP5 최대 상주 candidate/detail bytes 감소를 직접 계수. 필수 검증 읽기는 별도 기록하고 제거하지 않음 |
| 성능 개선 입증 | 위 gate 통과 후 목표 병목의 CPU/I/O/wall 중 하나 이상이 baseline 잡음 밖에서 감소해야 `performance_improved`. 작업량만 줄거나 측정 차이가 불확실하면 `effect_unproven`; 기능 확대 총비용과 동일 작업 절감은 따로 보고 |

실패·표본 부족·환경 불안정은 `performance_not_established`이며 AT8의 전체 새 경로 적용 근거로 사용하지 않는다. 병목을 수정하고 영향 시나리오만 재측정한다. 전체 scope를 처리하지 못하면 예산·입출력 설계를 보완하고 일단 일부 종목만 지원한 상태를 완료로 올리지 않는다. 이 기준은 엔지니어링 수용이며 원천 수리 코드 완료나 승인 초기값 계승에 실제 체결·양의 EV gate를 추가하지 않는다.

### 10.5 성능 회귀와 영수증

관련 trailing decision/strength/replay·holding report·log archive·runtime bootstrap·원천 writer 테스트에 policy 사전 적재, 동일 snapshot 참조/종료 해제, multi-position 상태 격리, candidate block=기존 계산, 손상 cache·same-size source 변경, 과거 cost-only revision, incremental=clean recompute, 격리 output/cache write, 반복 등록/종료 메모리 수렴을 추가한다. 실제 API/Provider는 호출하지 않는다.

AT7 성능 영수증은 baseline/candidate source·code·policy·workload hash, 입력 분모, 각 3회 수치, 원천 parse/필수 검증 bytes, cache hit/miss·무효화 사유·재계산 partition, peak retained bytes, queue/drain·만료/검열·최악 사례, 단독/결합 gate와 미측정 경로를 포함한다. AT8은 이 영수증을 확인하며 테스트 건수·문서 parser·과거 다른 release의 성능 PASS로 대체하지 않는다.

## 11. 구현 순서·owner·검증

### 11.1 작업 순서와 종료 검사

| 단계 | 수정 위치/책임 | 선행 | 종료 검사 |
| --- | --- | --- | --- |
| AT0 범위·원천 census | 기존 holding report/source bundle, 공통 scope 계약 | 없음 | 전체 symbol/market 분모, 원천 지도, parent hash, 복구 가능/불가, TP1–TP7 baseline·두 family 합산 수치 예산 확정 |
| AT1 비용 세대 수리 | log archive·비용 대사·trade/holding report·wrapper | AT0 | 과거 날짜 cost-only revision의 stale reuse/reseal 거부, 끝단 새 세대 검증 |
| AT2 전체 scope·capture | scalping 공통 adapter·기존 collector/source owner | AT0 | 삼성/비삼성·신규 종목·모든 route/session census 및 누락 사유, bounded 수집 |
| AT3 비용 coverage | lifecycle broker cost producer/reconciler | AT0–AT1 | 모든 position 분류, exact 비용만 경제 적격, ambiguous 배분 금지 |
| AT4 universal replay | 공통 trailing kernel·entry/holding replay adapter | AT1–AT3 | 동일 event runtime/replay 동등성, 미관측·partial·AI 검열, 전 scope 처리, TP3–TP5 streaming/공통 ID 보존 |
| AT5 상황 정책 | trailing policy·situation classifier·runtime consumer | AT2·AT4 | 부모 계승 동등성, causal pin, 소수 유형 연구·독립 holdout, TP1/TP2 장중 작업량·지연 수용 |
| AT6 최초 재생성/초기 bundle | automation orchestrator·holding report | AT1–AT5 | 모든 범위의 초기값/후보/계승 이유, immutable 출력, 운영 pointer 비변경, TP6/TP7 cold/warm/delta·재개 동등성 |
| AT7 선택·운영 인계 | selector·summary/handoff·bootstrap·semantics | AT6 | evidence별 authority, CAS·source/target/hash, 전체 소비·rollback, §10의 단독/결합 성능 gate·영수증 검증 |
| AT8 허용된 적용·자연 확인 | 기존 배포 및 PREOPEN/PID owner | 코드 리뷰/회귀와 해당 실행 권한 | 실제 release/PID/정책 hash, 자연 signal→terminal→cost 별도 수용 |

AT2의 공통 지원을 한 시장만으로 완료 처리하지 않는다. 단위 fixture 추가 순서와 최종 배포 범위는 다르다. 실제 자료가 없는 시장도 adapter·상태 전이·부모 계승 계약을 합성 fixture로 검증하고 자연 증거는 미관측으로 남긴다.

실행 owner는 계획 문서가 아닌 당일 checklist가 소유한다. 과거 [10/9 checklist](../checklists/2026-10-09-stage2-todo-checklist.md)의 `HoldingProfitExitSourceContractRepair`는 기존 잔여 원천 수리 이력이며, AT-F1 착수 시 stable ID·수용·이력을 보존하여 당일 owner로 재배치한다. 신규 전체 범위/상황 재생의 제안 stable ID는 `MainAllScopeTrailingReplay`다. 구현 착수 시 `Due/Slot/TimeWindow/Track`과 한 개의 현재 parsed owner를 확정하며 이 계획의 AT 번호를 별도 backlog로 중복 등록하지 않는다.

현재 [10/10 checklist](../checklists/2026-10-10-stage2-todo-checklist.md)의 완료 PASS 배포 승인을 이 계획의 실행 승인으로 확장하지 않는다. 봉인된 [10/12 checklist](../checklists/2026-10-12-stage2-todo-checklist.md)의 `DirectFamilyPreopenPolicyHandoff`는 기존 정확 날짜 자연 소비 owner이며, 새 코드를 위해 지금 수정하지 않는다. 자연 수용 날짜는 실제 구현/배포 일정에 맞춰 기존 인계 owner가 소유한다.

### 11.2 표적 검증표

| 검증 묶음 | 필수 case | 기존 테스트 owner |
| --- | --- | --- |
| 비용·전체 창 세대 | 과거 cost-only 수정, 당일 수정, 미소비 날짜 무영향, missing/null/zero, 부분 발행, read-race, root/경로 오류, 재실행 멱등성 | `test_log_archive_service.py`, `test_broker_cost_reconciliation.py`, `test_holding_exit_observation_report.py`, `test_threshold_cycle_wrappers.py` |
| 실제 비용 귀속 | 단일/복수/partial/ADD/익일/manual 혼재, 동일 체결 중복, 정산일·거래일·가용일, 실제 0원, 비용 revision | `test_broker_cost_source.py`, `test_broker_cost_reconciliation.py` |
| 전체 scope | 005930·나머지 고정 감시·새 임의 종목, 전체 가격대, PRE/REGULAR/AFTER×유효 route, 거래정지·비편입·auction·휴장·retired custody | `test_market_session_contract.py`, 기존 entry 연구 테스트, 공통 scope 테스트(위치 gate 후 추가) |
| 기회 census | ENTER/PASS와 Main 인수 분리, no-AI/VETO/timeout, priceplan missing, 중복 attempt/branch, 실제/CF mapping, reservoir 비사용 | `test_strategy_owner_replay.py`, `test_entry_first_signal_exit_research.py` |
| replay 동등성 | source clock gap·epoch 전환, 15:30 이후·익일·세션 경계, depth 부족·partial·ADD·잔량, 실제 SELL 이후 검열, 대체 AI 시점, latch/유예·fast/normal/retry | `test_entry_mechanical_exit_research.py`, `test_scalp_trailing_decision.py`, `test_scalp_trailing_mechanical_strength.py`, `test_scalp_trailing_operational_replay.py`, `test_holding_path_vote_replay.py` |
| 유형·경제 비교 | causal feature/pin, missing→BASE reason, 중복 유형 우선순위, restart·ADD·세션 승계, 미래 label 금지, grouped holdout, 부모/후보 공통 ID, 손실 꼬리·원천 제외 민감도 | 기존 trailing policy/replay 테스트, 신규 유형 테스트(위치 gate 후 추가) |
| 초기 생성·선택 | 부모만 존재·후보 일부/없음·전역 계약 손상, 모든 scope 해석, CF→actual 승격 거부, preview 소비 거부, parent CAS/잠금/target date, 중단·재개 | `test_runtime_policy_bootstrap.py`, `test_next_preopen_readiness.py`, `test_threshold_cycle_wrappers.py`, holding report 테스트 |
| 성능·인계 | TP1–TP7 사전 적재·공유 상태/후보 block·영향 partition, source 변경 시 cache/준비 세대 무효화, 메모리 수렴, 단독/결합 부하·정상/오류 분리, PID hash와 경제 상태 분리 | 관련 runtime/summary/handoff/semantic 테스트 및 §10.4 고정 입력 비교 |

구현은 각 묶음마다 구현 → 자체 리뷰 → 보완 → 재리뷰 → 관련 pytest/compile → 결과 기록으로 닫는다. wrapper 변경 시 `bash -n`·계약 테스트, 자동화 변경 시 운영 문서와 실행 checklist를 같은 변경에 갱신한다. API 변경은 공식 gate를 먼저 수행한다. 테스트 수만으로 전체 scope 계약이나 실제 정책 소비를 대체하지 않는다.

## 12. 중단·복원·계획 검증 기록

hard/protect/emergency 지연, owner/수량 침범, 중복 주문, stale/conflict 허용, 잘못된 시장 호가 혼용, 검열 손익의 실제 승격, unbounded hot-path 또는 정책/source hash 불일치가 발견되면 해당 새 경로를 중단한다. 전체 시장에서 검증된 부모 정책과 이전 정상 source/consumer 세대로 복원하며 퇴역 executor나 archive-only 정책을 살리지 않는다. 기존 보유 latch·peak·pin·주문 잔량을 보존하고 새 주문을 합성하지 않는다.

계획 자체의 검토 기준은 AT-F1 비용 세대 결함, 전체 universe/route와 실행 적격성의 구분, 실제/CF/AI 권한 분리, 초기정책 생성과 선택의 구분, source 복구 불가 처리, 모든 consumer·owner·위치·검증 경로의 연결이다. 구현·경제 적용·자연 수용을 별도로 남긴다.

아래 첫 작성 기록은 당시 이 제안서 하나의 변경에 대한 것이다. 후속 성능 리뷰는 §13에 구분한다. README/runbook/Rebase/prompt/AGENTS와 운영/봉인 checklist를 이 계획 리뷰에서 변경하지 않으며 병행 문서 변경은 보존한다.

- 자체 리뷰 보완: 잘못 연결한 trade review 경로를 실제 producer로 수정하고, Markdown 줄 끝 공백을 제거했다. 분봉 경로와 tick/depth 실행 증거를 분리하고 상황 feature 계산식·필수 feature 결손 시 부모 계승·삼성 전용 helper의 범용 오용 방지를 추가했다.
- 문서 검증: 로컬 링크 33개·기존 테스트 참조 15개 경로 확인, print-only parser exit 0·기존 backlog 20개, `git diff --check` 및 신규 파일 별도 whitespace 검사 통과. `MainAllScopeTrailingReplay`는 실행 checklist에 아직 등록하지 않은 제안 ID이며 현재 parsed 실행 owner로 주장하지 않는다. `DirectFamilyPreopenPolicyHandoff`는 10/12에 한 개다.
- 작업 중 다른 문서 작업이 10/10 checklist 목적·규칙과 pre-submit delay 계획 기록을 변경하여 재독했다. 이 작업의 계획 전용 범위와 충돌하지 않으며 그 변경을 되돌리지 않았다. 봉인된 10/12 checklist SHA256 `9e7d9f001a13cfac3b0fbd566bcfa860bd598ce41a9d1280437dcccaefff40a3`는 유지됐다.
- 코드 pytest·compile, provider/브로커 호출, 장후 원장 재생성, 정책 발행/선택, 배포·재시작·PID 수용, 외부 Project/Calendar sync는 이번 문서 작업에서 실행하지 않았다. 최적화 초기값의 실제 생성 가능 범위는 AT0 원천 preflight 이후 확정하며, 현재 파일 목록 점검을 전수 replay 결과로 대신하지 않는다.

## 13. 10/10 성능 중심 후속 리뷰

AT-F7–AT-F10을 추가하고 TP1–TP7을 실제 loader·observer·classifier·replay·원천/비용 consumer에 연결했다. 정책 사전 적재, snapshot 공유, candidate detail 상주 제거, position 상태의 공유 금지 경계, 단계별 cache 무효화, 두 family의 합산 자원, 독립 의미 검증과 성능 gate를 AT0–AT8에 반영했다. 제출 지연 계획의 병행 성능 보완을 보존하며 공통 source만 공유하고 가격 비교/실제·CF 경제 권한은 분리했다.

- 재리뷰에서 warm cache와 필수 내용 검증, 비용 정정과 net 시작판정, 공통 ID 교집합과 후보 block, 다른 position의 M1 상태 공유 금지, 두 family의 별도 경제 권한, 64MiB 기존 상한과 향후 분할 지원을 대조했다. 잘못 작성한 기존 성능계획 anchor를 실제 제목으로 보완했다.
- 두 상세계획의 로컬 링크 52개(앵커 포함 링크 6개) 결손 0, 참조 테스트 경로·fence·공백 검사 통과. print-only parser exit 0·backlog 20개, `git diff --check`와 신규 문서 개별 whitespace 검사 통과. 기존 10/12 handoff owner 1개를 유지하며 새로운 실행 owner를 등록하지 않았다.
- 작업 시작 시 고정한 기존 PASS 계획·10/2 delay 계획과 10/12 봉인 checklist는 불변이다. 병행 작업의 10/10 checklist 성능 리뷰 기록을 재독·보존했다. 이번 직접 보완은 이 문서와 제출 지연 계획의 전체 scope/분할·합산 자원/gate 연결이며 병행 수정 내용을 덮어쓰지 않았다.
- 코드 pytest/compile·성능 실측·장후 재생성·정책 발행/배포·외부 sync는 문서 리뷰 범위 밖이라 수행하지 않았다. 수치 예산과 실측 결과는 AT0/AT7 후속 수용이며 구조적 절감 목표를 현재 성능 개선 실적으로 보고하지 않는다.

## 잔여 구현 실행 기록 — 2026-10-10

[반복 리뷰·실제 원천·성능 근거](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md)를 따른다. 전수 streaming/shard·전역 중복/split·부모 승계와 0초 초기값·정식 writer/consumer 연결을 구현했다. 코드 수용과 W5 발행/chain, 10/12 자연 PID 수용을 분리한다. 최종 v6 발행·native finalization DONE·10/12 `current_full_contract=pass`까지 수용했다. 실제 적용일 PID·경제 결과만 별도 자연 관측으로 남는다.

## 14. 2026-10-18 연구 실행안 — 원천 확보와 생산·소비 계약부터 경제 비교까지

### 14.1 연구 질문·범위·확인 기준

연구 질문은 **동일한 진입·수량·후행 관측에서 청산만 변경했을 때 비용 후 기대수익과 원화 순이익이 개선되는가**다. 기계 진입 라벨·보조판정 원응답·membership을 보존하고 별도 보유 연구로 연결한다. 진입 선택이나 수량 변경의 효과를 청산 개선으로 합산하지 않는다. 실험은 시작 전 보유 판단, 시작 후 이익 보존, 신호 이후 체결 손실을 나누며 세 구간별 모집단과 손익 기여를 보고한다.

조사 기준은 workspace `7c241ea21619ce3153f1a338f1b846b0313a894f`의 아래 함수들이다. 선택 릴리스는 `900234d791b0bf31797cd4e823d0ae40296f790b`, 다음 운영일은10/19, selector의 `actual_pid_consumed=false`다. 이 기록은 운영 PID 확인이나 자연 데이터 전수 재생 결과가 아니다. 병행 수정은 보존하고 실제 착수 때 코드·파일 SHA를 다시 고정한다.

전체 종목·시장 범위는 §3의 universe/session/route/custody를 그대로 사용한다. **전체 범위 처리, 실제 관측 coverage, 경제 평가 적격성은 서로 다른 분모**다. 자료가 없는 범위까지 결과와 사유는 남기되 전 종목의 연속 tick/depth를 이미 보유한다고 가정하지 않는다. 연구기간은 clean baseline과 현행 forward 경계 모두를 만족해야 하며 현재 후자는2026-09-29다. 더 오래된 자료는 원천 복원·계약 검증용으로 분리한다.

아래 `HX-*`, `R*`, 원천 상태와 산출물 이름은 이 실행안의 제안 식별자다. 현재 런타임에 이미 존재하는 enum·field·CLI라고 해석하지 않는다. 현행 코드의 실제 이름은 §14.3에서 별도로 명시한다.

### 14.2 현재 확인한 계약 공백과 선행 수리

| ID | 현재 코드에서 확인한 사실 | 필요한 보완과 종료 검사 |
| --- | --- | --- |
| HX-01 | [source assembler](../../src/engine/automation/main_trailing_source_assembler.py)의 `_trace_rows()`는 native event에서 `planned_qty`, `buy_basis_krw`, `entry_cost_model`, `execution_plan_sha256`, `entry_depth_verified`, `trailing_entry_context`를 읽는다. 이 조사에서 `execution_plan_sha256`·`entry_depth_verified`의 운영 native 생산 경로는 확인되지 않았다. | 실제 실행계획 owner가 생산하는 불변 receipt를 exact attempt에 연결한다. 소비 필드를 임의로 채우거나 실제 주문이 없는 기회를 제출됐다고 표시하지 않는다. 실제 producer→저장→decode→assembler의 비어 있지 않은 fixture가 required field를 모두 공급해야 한다. |
| HX-02 | 같은 함수는 event의 `universal_trailing_quote` 하나로 `path_events`를 시작한다. 보유 전용 `_observe_scalp_trailing_input_transition()`에는 quote 생산이 있으나 미체결 기회의 연속 후행 stream을 이 함수에 연결하는 경로는 확인되지 않았다. | 기존 공유 market-data owner의 route/epoch별 후행 저장을 기회와 연결한다. 시작 quote 하나를 후행 경로로 인정하지 않는다. 실제 SELL 뒤 연장도 같은 자료 계약을 요구한다. 누락·종료·구독 실패가 명시된 구간 manifest와 실제 후행 event 소비로 닫는다. |
| HX-03 | CF의 `entry_at`은 현재 보조판정 `decision_ts`다. 실제 `freeze_entry_operating_context()`의 계획·비용 모델은 제출 직전에 생성된다. `freeze_shared_entry_context()`도 accepted-entry의 `completed_epoch`를 anchor로 사용한다. | 결정·계획 가용·모델 체결·최초 실제 체결 시각을 분리한다. 나중에 생성된 계획을 PASS 시점 가상 체결에 소급 사용하지 않는다. 실제 pin 시점과 문서의 첫 BUY 표현을 명시적으로 정합화한다. |
| HX-04 | [event logger](../../src/utils/pipeline_event_logger.py)의 `emit_pipeline_event()`는 `fields` 값을 문자열로 저장한다. 보유 quote/context/pin은 JSON 문자열이며 `completed_sources()`가 이를 decode한다. | raw JSON object라고 가정하는 소비를 금지한다. 저장 타입→decode 타입→정규 타입의 단일 adapter를 검사한다. 원문·SHA는 보존하고 잘못된 JSON, `"False"`, `"None"`, 숫자 문자열을 암묵적 truthy/0으로 처리하지 않는다. |
| HX-05 | `_trailing_entry_cost_model.known_at`의 실제 생산값은 `operating_context.frozen_at`인 timezone 포함 ISO 문자열이다. [ADD 모델](../../src/engine/scalping/holding_vote_exit_models.py)의 `record_generation()`은 `finite(known_at)` 숫자만 받고, universal `_replay_cursor()`도 `number(known_at)`로 ISO를 거부한다. 반대로 universal의 `known_at=None`은 해당 검사를 건너뛴다. | `main_stop_replay.cost_known_epoch()`와 같은 명시적 ISO/epoch adapter를 연결한다. ADD/universal/stop에서 정상 ISO와 같은 epoch의 결과가 같고 naive/future/missing/nonfinite는 거부해야 한다. 원 시각은 보존한다. ADD 세대 삭제와 `cost_model_not_known_at_entry` 오제외 반례를 포함한다. 실제 함수의 무I/O 최소재현에서 ISO 거부/epoch 통과 차이를 확인했으며 코드 수리·pytest 수용은 아직 아니다. |
| HX-06 | 보유 관측은 상태변화/heartbeat와 position sample 상한을 갖는다. universal replay는 native depth sequence 연속성을 검사한다. | sample 번호와 native depth sequence를 구분한다. bounded history의 중첩분은 원 sequence로 중복 제거하고 빠진 구간은 복구 가능한 source에만 연결한다. 단순 상한 확대·sequence 재번호화로 연속성을 만들지 않는다. |
| HX-07 | `_replay_cursor()`는 depth 부족에 따른 부분 매도 후 `partial_depth_residual_unobserved`로 검열한다. 실제/가상 ADD, 잔량 체결을 모두 끝까지 지원한다고 단정할 수 없다. | 미지원 branch는 census와 검열에 남긴다. 잔량 재생을 확장할 때 주문 가격/유효기간·다음 depth·체결 중복 소비 방지·수량 보존을 함께 구현한다. 지원 전에는 해당 후보의 종결 손익을 만들지 않는다. |
| HX-08 | [exact 비용 reader](../../src/engine/lifecycle/broker_cost_reconciliation.py)는 `runtime/holding_actual_costs/<completion_date>/<record_id>.json`을 읽지만 이 조사에서 해당 schema의 자동 writer는 확인되지 않았다. 별도 공식 전체 활동 대사 producer는 존재한다. | reader가 있다는 이유로 전 거래의 exact-execution 비용 파일을 필수 입수 목표로 삼지 않는다. 실제 producer가 있는 whole-position 비용, 연구 배분, 모델 비용을 §14.7대로 분리한다. 미확인 writer의 자연 생산을 기다리는 종료 조건을 두지 않는다. |
| HX-09 | [자동 원천 테스트](../../src/tests/test_main_trailing_source_assembler.py)의 native binding 사례는 처리 `complete`와 함께 `common_ids_ref.count == 0`을 기대한다. | 처리 완료/부모 계승과 경제 재생 완료를 분리한다. 새 생산 연결은 실제 producer 출력으로 적격 actual·CF fixture가 각각 1개 이상 평가되는 테스트와 source-gap 제외 테스트를 모두 통과해야 한다. 이는 코드 계약 테스트이며 자연 표본 최소치나 새 경제 승인 문턱이 아니다. |
| HX-10 | `completed_sources()`의 leg 부재 fallback은 `buy_fill_quantity`를 읽지만 완료 execution ledger의 실제 생산명은 `buy_filled_qty`다. | fill leg가 정상인 기존 행은 보존한다. leg가 없는 행은 producer/schema를 확인한 versioned mapping과 수량/금액 대사 없이 복구하지 않는다. 올바른 이름이 존재해도 최종 누적 수량을 최초 진입 수량으로 간주하지 않는다. |
| HX-11 | `broker_cost_source._position_result()`는 whole-position `actual_cost_reconciled`에 `source_sha256`·`receipt_sha256`을 생산한다. trade review는 이를 전달하지만 universal actual replay는 `raw_sha256`도 무조건 요구한다. | exact-execution과 whole-position scope별 원 provenance를 검증하는 adapter를 마련한다. `source_sha256`을 의미 확인 없이 `raw_sha256`으로 복사하지 않는다. 실제 whole-position producer→완료 projection→재생의 정상 fixture와 변조/다중 owner 거부 fixture로 닫는다. |

HX 항목은 확인한 코드 경로의 수리 요구다. 현재 모든 운영 거래에서 같은 장애가 발생했다는 빈도·경제 피해 주장은 하지 않는다. 10/18 사용자 정정에 따라 별도 보유·재생 계약 수리 세션을 전제로 하지 않는다. 이번 `MainAllScopeTrailingReplay`가 연구에 필요한 생산/소비·ADD/비용 시각 수리를 직접 소유한다. 기존 checklist 식별자는 별도 수리의 진행/완료 증거가 아니다. 과거 미저장 원천은 코드 수리와 구별하고 다른 연구의 공통 함수 변경은 실제 diff와 테스트로 조율한다.

### 14.3 변수·생산자·소비자 사전

R0에서 아래 실제 이름을 바탕으로 기계 검증 가능한 사전을 만든다. 각 항목에는 `producer module/function/callsite`, 저장 artifact와 JSON path, schema/version, 소비 module/function, wire/저장/정규 타입, 단위·부호, event/known 시각, identity/route, null 의미, 변환 함수, 해당 fixture를 기록한다. 이 메타데이터는 제안 연구 산출물이며 새로운 runtime 필드가 아니다.

| 현행 값·필드 | 실제 생산/저장 | 실제 소비·의미와 검사 |
| --- | --- | --- |
| `machine_observation_sha256`, `evaluation_attempt_id`, `canonical_opportunity_id` | `ai_decision_payloads`의 native 기계 관측과 `ai_decision_trace`의 연결 | assembler `_native_index()`/`_trace_rows()`; symbol/time 근접 매칭 금지, 원 observation hash와 attempt 일치 |
| `entry_mechanistic_policy_decision.event` | 원 기계 평가 envelope | `_trace_rows()`가 참조하는 event 위치. 보조 trace 최상위와 혼동 금지 |
| `decision_ts`, `entry_ai_risk_verdict` | `ai_decision_trace`의 timezone 포함 문자열·canonical verdict | projected `auxiliary_verdict`, CF `auxiliary_completed_at`로 변환. PASS/CAUTION/VETO/INSUFFICIENT 원문 보존 |
| `planned_qty` → `position.qty` | 현재 CF는 native event에서 읽음; 해당 native 생산 연결을 HX-01에서 확정 | 양의 정수 주수. 실제 `buy_qty`, 목표 수량, probe 수량과 구분 |
| `buy_basis_krw` | CF는 native event, 실제 완료는 fill leg 금액/수량 정규화 | 총 매수대금 원화. 주당 `buy_price`를 그대로 대입하지 않음 |
| `execution_plan_sha256`, `entry_depth_verified` | 현재 CF required consumer는 있으나 producer 연결 미확인 | 원 실행계획·당시 ask/잔량·유효기간·route를 검증한 receipt에서만 생성. hash 존재/boolean true만으로 경제 적격화 금지 |
| `_trailing_entry_cost_model` → quote.`entry_cost_model` → position.`cost_model` | submit 전 `freeze_entry_operating_context()` → Main 보유 observer → `completed_sources()` | `buy_cost_krw`는 원화, `sell_cost_rate`는 비율(0.0023=0.23%), `known_at`은 원 ISO를 보존하고 정규 epoch와 분리 |
| `trailing_replay_cost_model` | trade projection에 있으면 `completed_sources()`가 우선 소비 | 다른 모델보다 우선하는 이유·producer·동일 원 receipt를 검사. 이름이 존재한다는 이유로 0비용 기본값을 넣지 않음 |
| `universal_trailing_quote` | `_observe_scalp_trailing_input_transition()` → `_log_holding_pipeline()` → 문자열 JSON | `completed_sources()` decode 후 `kind=QUOTE` 검사. CF native event의 같은 이름에 자동 존재한다고 간주 금지 |
| quote.`event_at`, `known_at` | `quote_projection()`에 전달한 원 호가/로컬 가용 epoch seconds | 거래소 HHmmss, `received_at_ms`, 로그 기록시각과 구분. 계산 가능한 시각은 known_at 기준 |
| quote.`sequence`, `sample_sequence` | 각각 native depth `route_sequence`, 보유 관측 sequence | 재생 연속성은 native 원천 기준. heartbeat 번호로 depth 연속성을 증명하지 않음 |
| quote.`route`, `item`, `transport_epoch` | 동일 snapshot의 `market_route`, 원 item, 연결 epoch | `recent_depth_ticks_by_route`/`recent_trade_ticks_by_route`와 함께 검증. symbol 6자리만으로 KRX/NXT/SOR를 병합하지 않음 |
| quote.`bid`, `ask`, `bid_qty`, `trade_peak_price` | 실행 가능 호가·잔량·관측 고점을 `quote_projection()`이 봉인 | 가격 원화, 잔량 주수. trade peak를 그 가격에서 매도 가능한 bid로 간주 금지 |
| `sell_execution_plan.valid_until/limit_price/quantity/quote_source_sha256` | quote projection의 제한된 재생 계획 | 실제 제출 receipt 아님. 후보별 주문 가정·잔량·유효기간 평가에만 사용 |
| `trailing_entry_context`, `trailing_situation_pin` | `freeze_shared_entry_context()`/상황 pin → position/event JSON 문자열 | `pin_context()`/`validate_pin()`; `feature_sha256`, `classifier_sha256`, `classification_origin_hash`의 서로 다른 대상을 검증 |
| `buy_fill_legs`, `sell_fill_legs` | canonical trade projection 및 검증된 체결 leg | `completed_sources()`의 정상 첫 BUY 시각은 `buy_fill_legs[0].at`에서 읽음. ADD/종결의 체결 관측 순서와 주문 ACK 순서를 구별 |
| `first_buy_at_epoch` | 이번 조사에서 `completed_sources()` fallback reader만 확인; 해당 projection producer 미확인 | 존재를 가정해 required input으로 두지 않음. leg 없는 역사 행의 진입시각을 손익/로그 시각으로 추정하지 않음 |
| `holding_vote_source`, `holding_vote_replay_ref` | `holding_vote_replay_source.runtime_source()` 및 `assemble_votes()` | 원 요청·응답·모델·policy·crossing hash를 exact join. 후보가 다른 질문을 만들면 원 응답 재사용 금지 |
| `actual_cost_reconciliation` | exact receipt 대사 또는 별도 whole-position 공식 활동 대사 | `status`, `exact_pnl_krw`, `exact_profit_rate`, `receipt_sha256`와 scope별 source provenance. 현재 whole-position `source_sha256`/consumer `raw_sha256` 불일치는 HX-11 수리 대상. 연구 배분을 actual로 변환 금지 |

필드가 다른 stage에서 같은 이름으로 쓰이면 stage/schema를 사전 key에 포함한다. `entry_depth_verified`처럼 소비만 확인한 항목은 `producer_unverified`로 명시하며 구현 완료 목록에 넣지 않는다. rename은 단일 versioned adapter에만 두고 alias 기간·충돌 시 거부·제거 조건을 기록한다. canonical 입력에는 누락/오타/단위 불일치를 검사하되 vendor 원문에 새 필드가 생겼다는 이유만으로 전체 원천을 폐기하지 않는다.

현재 quote의 `event_at` 인수는 거래소 체결시각이 아니라 `bid_received_at` 로컬 수신시각이다. `trade_peak_price`도 runtime `peak_price` 인수이므로 이름만으로 특정 원천의 체결 최고가라고 보증하지 않는다. `ws_data` compact는 해당 route의 top-of-book/tape projection이며 원 10호가 전체·숨은 잔량·거래소 주문 대기열을 보관한 자료가 아니다.

CF 계획·후행 연결은 원 native event를 수정하지 않고 원 ID/hash를 참조하는 별도 versioned receipt로 생산한다. 최초 ENTER_NOW부터 기존 공유 원천의 구간 참조를 붙이고, 보조 결과/계획 가용/관측 종료를 후속 receipt로 연결한다. PASS 시점 이전의 필요한 구간을 확보하지 못했으면 그 공백을 그대로 남긴다. 현재 `entry_at=decision_ts`와 새 modeled fill anchor를 동일한 필드 의미로 섞지 않고 schema 변경·호환 adapter를 함께 검증한다.

### 14.4 시각·수량·원천 가용성의 불변식

1. 원본 ISO·거래소 시각·수신 epoch/ms는 그대로 보관한다. 정규화는 명시적 timezone과 단위가 있는 adapter에서 한 번 한다. naive datetime의 의미가 source 계약에 없으면 현재 KST로 추정하지 않는다.
2. 기존 `decision_ts`와 별도로 계획 생성/가용, 모델 entry fill, 실제 first BUY를 구별한다. CF 모델 체결은 `max(원 신호, 유효 PASS 가용시각, 계획 가용시각)` 이후이면서 해당 계획의 유효구간 안이어야 한다. 사전에 동결된 유효 계획도 허용하되 원 attempt·route에 결속한다. 체결 이전 자료는 당시 state 준비에만, 체결 이후 자료는 후행 평가에 사용한다. 계획이 없으면 기회 census/가격경로 진단까지만 수행한다.
3. 실제 entry context는 원 anchor를 보존한다. first BUY 전에 알려진 값만 사용하며, context 재생성이나 후보 classifier 학습에 미래 결과를 사용하지 않는다. 문서의 첫 BUY pin과 현재 accepted-entry anchor 차이를 숨기지 않는다.
4. 모델 비용은 진입 당시 가용해야 한다. 실제/연구 정산 비용은 진입 이후 확정될 수 있지만 후보 학습 cutoff 이전에 알려진 버전만 사용한다. 실제 비용까지 `known_at ≤ entry_at`을 요구해 모든 정상 거래를 제외하지 않는다.
5. target/probe/submitted/filled/cancel-confirmed/remaining 수량을 구별한다. 체결번호·주문번호·날짜·side·route·owner가 같은 원 receipt로 수량 보존을 검사하며 ACK나 현재 미체결 0만으로 과거 terminal을 만들지 않는다.
6. manual handoff 시각 이후 자동 정책 재생은 검열한다. 수동 매도의 실제 경제 기록은 별도 owner로 보존한다. retired episode/widget 잔량은 Main에 편입하지 않는다.
7. sampling 누락, 실제 무체결, 거래정지, 세션 종료는 다른 상태다. 수집 공백에 선형 가격/잔량 보간을 넣거나 source gap을 WEAK/no-fill/손익0으로 바꾸지 않는다.

### 14.5 키움 원천의 확보 가능성 확인 절차

공식 upstream은2026-10-18 확인 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`다. 해당 tree에는 `kiwoom_docs`가 없으므로 문서가 있다고 가정하지 않고 packaged spec·SDK·Postman·공식 포털을 교차 확인한다. 확인한 API 존재와 해당 계좌·날짜의 실제 데이터 확보 성공은 별개다. 인증·실계좌 조회·구독은 이번 계획 검토에서 실행하지 않는다.

각 원천은 다음 제안 분류로 관리한다. 원 API가 지원하는 능력과 로컬 보관 여부는 별도 열로 둔다.

- `local_verified`: 원 bytes/원천일/route/identity/coverage가 검증돼 재사용 가능.
- `official_fetchable_unverified`: 공식 조회 방법은 있으나 요청 날짜·페이지·계좌/경로의 실제 coverage는 아직 미확인.
- `requires_live_capture`: 당시 수집해야 하는 자료. 기존 로컬 보관본이 있으면 복원 가능성을 먼저 검사.
- `official_semantics_unconfirmed`: API 또는 필드는 있지만 필요한 귀속·시간·단위 의미가 공식 근거로 확정되지 않음.
- `historical_unrecoverable`: 보관본·공식 조회 경로·기간을 확인한 뒤에도 필요한 과거 정보가 복원 불가능하다고 확정한 경우만 사용.

세부 공식 원천 목록은 §14.12에 고정한다. 확보 가능 원천은 consumer가 사용하지 않는다는 이유로 누락시키지 않고 기존 adapter 유무·pagination·요청 날짜·route·writer·재시도 owner를 함께 기록한다. 반대로 문서에서 못 찾았다는 이유만으로 곧바로 확보 불가로 분류하지 않는다.

수집/복원 순서는 **로컬 raw·lossless archive → 기존 검증 projection → 공식 날짜/기간 조회 → 앞으로의 자연 수집**이다. 복원 요청 원장에는 요청 범위, 원 endpoint/body, upstream SHA, 모든 continuation, 최초/최종 시각, 종목·시장별 covered interval, raw SHA, 정상 종료/제한 도달/미확인, 소비자가 사용할 수 있는 정밀도를 남긴다. pagination 상한 도달을 조회 완료로 표시하지 않는다. 동일 과거 gap에 새 근거 없이 반복 호출하지 않는다.

공식 포털은 현재 국내 조회5회/초, 토큰별 WS1세션·실시간200종목을 안내한다. [공식 사용안내](https://openapi.kiwoom.com/intro). 기존 공유 limiter·활성 보유/실행 lease를 보존하고 연구용 구독이 이를 축출하지 못하게 한다. 모든 종목의 모든 시장을 동시에 연속 호가로 관측할 수 있다고 약속하지 않는다. 종목 마스터 전체와 모든 유효 route/session의 처리 대사를 유지하고, 실제 tick/depth 관측은 예산·수집기간·미관측 구간을 공개한다. 전 범위의 완전한 과거 order-book 재생이 필수라면 현재 원천의 한계를 명시하고 별도 데이터 제공 계약이 검증되기 전 완료를 주장하지 않는다.

### 14.6 단계별 실행·책임·산출물

아래 파일 이름은 격리 실행 root 아래의 제안 산출물이다. 기존 `source assembler → all_scope_research → holding report → handoff`가 유일한 정식 생산 경로이며 별도 경쟁 publisher를 만들지 않는다. 새 검증 코드가 필요하면 기존 automation/scalping/lifecycle 역할 패키지에 배치하고 engine root에 모듈을 추가하지 않는다.

| 단계 | 실제 작업과 owner 경계 | 입력 → 산출물 | 종료 조건 |
| --- | --- | --- | --- |
| R0 계약 동결 | 연구 owner가 코드/정책/원천·공식 능력 사전 작성. 보유 수리 owner와 함수 단위 변경 소유권 대사 | 원 코드·기존 source → `source-contract-audit.json`, `source-capability-matrix.json`, `research-run-manifest.json` | required field별 producer/callsite/consumer/타입/단위/fixture 존재 또는 명시적 미지원. producer 없는 required consumer를 ready로 표시한 항목0 |
| R1 모집단·복구 분류 | 기존 assembler/universe/native trace/체결 ledger를 같은 cutoff로 대사 | 전 종목×유효 route/session, 실제 보유, native 기회 → `population-census.json` 및 구간별 참조 | 전체 scope에 disposition, 실제·대체·CF·보조 대조군 분리, 중복/제외/미관측 분모 보존, 원천별 복구 작업 지정 |
| R2 생산 계약 보완 | HX-01~11의 실제 producer/consumer 수리. 기존 보유 수리와 중복 작업 금지 | 실제 writer output → 봉인 input partition/원 receipt | 실제 serialize/decode 경유 계약 시험, 정상 비어 있지 않은 actual·CF fixture, 실패주입·review/fix/re-review 완료. 부재 raw를 fixture로 복구했다고 보고하지 않음 |
| R3 제한 복원·수집 | 기존 공식 read adapter·공유 limiter·collector owner를 통해 허용된 원천 확보. 없는 adapter는 먼저 구현·리뷰 | 원 API/보관 자료 → raw·receipt·coverage manifest | 가능한 날짜/원천의 완료 또는 정확한 종료 사유, 원문 보존, 과거 수집 시각 위조0, 준비 root에만 새 세대 |
| R4 기준 재현 | runtime 공통 trailing/strength/session/AI deferral 함수를 그대로 사용 | 검증된 actual 경로 → 기준 정책 decision/trigger/intent/fill/terminal 비교표 | 비교 가능한 decision·최초 crossing·수량 전이 일치. 비교 불가 구간은 검열. 실제 fill과 모델 fill의 차이는 실행 모델 오차로 별도 기록 |
| R5 후보 실험 | §14.8의 등록된 단일축 후보·시간순 검증 | 같은 진입/수량/경로 → `paired-candidate-results`·상황별 진단 | 공통 적격 ID와 제외 민감도, 후보별 실제/CF·비용 등급, tail/자본 점유 및 runtime 성능 검사 |
| R6 초기·후속 정책 생성 | 기존 상황 selector/부모 계승/장후 handoff만 사용 | 원 parent hash+평가 → 전체 scope 초기 bundle 또는 qualified successor | 범위 누락0, 부족 범위 parent_carry, CF를 actual로 승격0, 원 승인 초기값에 새 경제 gate 추가0 |
| R7 정식 인계 | 기존 장후 owner가 정확 source/target date·strict/controller 인계. 배포·PID는 기존 승인 경로 | 연구 결과 → 정식 summary/정책 receipt → 별도 release/PID receipt | 코드 검증·연구완료·정식발행·배포·PID·자연경제 각각 별도 상태. 준비본만으로 실현 성과 완료 금지 |

R0/R1/실험 등록과 이번 작업이 소유하는 보유 수리는 병행한다. R2/R3는 원천 종류별로 독립 진행한다. R4/R5에서 사용하는 계약만 선행 수리를 요구하며, 미지원 CF 때문에 정상 actual 전체를 중단하거나 반대로 CF 결손을 숨겨 완료하지 않는다. 전역 preflight/identity/source isolation 자체가 깨지면 전체 평가를 중단한다.

실행 backlog는 당일 checklist의 `MainAllScopeTrailingReplay` 후속 owner가 연구 연결과 결과를 소유한다. 공통 연구 수리는 이번 owner가 처리하며, `DirectFamilyPreopenPolicyHandoff`의 실제 PREOPEN/PID acceptance는 그대로 유지한다. 과거 완료를 다시 여는 근거는 위 HX 신규 계약 공백이며 이미 완료된 일반 리뷰를 반복하기 위한 것이 아니다.

### 14.7 실제·가상·비용 증거 수준

`actual_completed`, `actual_entry_alternative_exit`, `enter_pass_opportunity_cf`를 분리한다. 보조 CAUTION/VETO는 별도 대조군으로 보존하며 현행 CF 경제 모집단의 PASS 조건을 조용히 넓히지 않는다. 모든 거래는 full/partial, ADD 포함 여부, 수동 이관, terminal/censored를 함께 표시한다.

| 비용/경로 등급 | 허용 사용 | 금지 |
| --- | --- | --- |
| 거래별 확인 또는 유일하게 대사된 whole-position 실제 비용 | 확인된 실제 완료 순손익 | 비용 귀속이 불명확한 거래까지 실제 비용 확대 |
| `broker_confirmed_total_allocated` 연구 배분 | 별도 보유 연구 소비 계약이 마련된 경우 연구 손익·민감도 | 현행 `economics_scope=initial_quantity_research_only`를 보유 actual 승인으로 전용, canonical 비용/profit_rate 덮어쓰기 |
| entry 전에 동결된 모델 비용 | 기준/후보 동일 가정의 모델 비교 | 실제 확정 비용·실현 수익으로 표시 |
| 실행 가능한 연속 tick/depth | 관측된 범위의 체결 가능성·정책 재생 | 숨은 잔량·queue position·시장 충격이 완전히 알려졌다는 주장 |
| 체결 당시 BBO 또는 OHLC만 복원 | 가격경로 진단·사전에 정의한 상하한/민감도 | depth 없는 full fill, 같은 봉 고저 순서, 원 AI 응답/주문시각 합성 |

확정 총비용 배분의 현재 소유권은 [10/17 비용 검토](../audits/initial-quantity-broker-cost-closed-loop-repair-review-2026-10-17.md)다. 재사용은 해당 기존 producer의 원 증거·배분 보존식을 유지한 별도 보유 연구 consumer 계약으로 설계하고, 이 문서만으로 승인 범위를 변경하지 않는다. 실제 비용이 없는 거래도 모집단에서 삭제하지 않으며 지원되는 모델 연구와 actual 평가의 분모를 각각 보여준다.

### 14.8 등록할 실험과 경제 평가

| 순서 | 실험 | 고정/비교와 질문 |
| --- | --- | --- |
| E0 | 현재 정책 재현 | 당시 source/policy/fast·normal/유예·preset·hard safety 우선순위 재현. 기계의 기존 +0.4/-3/1800 라벨과 실제 운영 종료 결과는 병렬 보존 |
| E1 | 시작률 단일축 | `registered_research_grid()`의 기존 부모 인접 후보. weak/strong·M1 고정. 빨리 시작한 이익 보존과 조기 청산 후 놓친 상승 비교 |
| E2 | weak/strong 폭 각각 | 시작률·M1 고정. 정상 눌림 허용과 이익 반납의 비용 후 차이 |
| E3 | 기존 네 상황의 추가 설명력 | HIGH_VARIABILITY/TREND_CONTINUATION/REBOUND_RANGE/BASE와 시장 부모 비교. 종목별 영구 임계값과 대규모 교차 grid를 먼저 만들지 않음 |
| E4 | 보유 중 강약 전환 | M1 기존 값과 후보를 별도 실험. 가격 전진·체결 압력·스프레드/잔량·회복을 당시 정보로 계산. 진입 pin을 사후 재분류하지 않음 |
| E5 | 시작 전 정체·반등 실패 | 30/60/120/180초 관측창별 유지/조건부 조기 청산 가설. 무진전 하나만으로 자동 청산 결론을 내리지 않음. 새로운 실주문 owner가 아니라 연구 비교 |
| E6 | 기존 보유 AI 유예 효과 | 원 요청·응답이 같은 crossing에서만 운영 비교. 질문시점/입력이 달라지면 검열, 별도 mechanical_only_cf는 운영 AI 성과로 표시하지 않음 |
| E7 | 검증된 조합 | 단일축 결과를 보고 사전에 등록한 제한된 조합만 이후 기간에서 평가. 같은 holdout으로 반복 선택·재검증하지 않음 |

트레일링 `start_pct`는 peak 순수익률이고 되돌림폭은 고점 대비 실행 가능한 bid 하락률이다. 단위가 모두 %여도 분모와 비용 반영이 다르므로 하나의 손익보장 수치로 해석하지 않는다. 하드스톱 완화·수동 veto·브로커/수량/신선도 guard 변경은 위 후보 축에 포함하지 않는다.

순수 청산 효과의 별도 연구 진단은 같은 적격 ID의 `candidate_net_replay - parent_net_replay`로 정의한다. 제안 이름은 `exit_only_paired_delta_net_krw`이며 현재 구현/발행된 필드가 아니다. 기준/후보 모두 같은 비용·체결 가정으로 비교하고 실제 손익과 혼합한 인과 효과라고 부르지 않는다.

**현행 actual-completed selector는 `candidate - max(parent modeled, actual realized)`의 실제 실현 하한을 보존한 보수적 비교를 사용한다.** `universal_trailing_replay.common_evaluation()`/`_aggregate_streamed_evaluation()`와 `trailing_situation_policy`의 기존 집계·선정 계약을 유지한다. 새 exit-only 진단으로 기존 지표의 의미·실현 하한·선정 기준을 덮어쓰지 않는다. 기존 상황 집계의 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `paired_delta_net_krw`와 범용 집계의 `paired_ev_pct`를 각각 실제 분모·참조값과 함께 표시하고 새 진단은 별도 열로 출력한다. 연구 배분 비용의 사용도 §14.7의 별도 계약을 따른다. 일별 손익·이익→손실 전환·이익 반납·tail loss·보유시간/자본 점유·실행 슬리피지·source/censor 비율을 함께 보고한다. 승률은 보조지표다.

후보별 유리한 ID만 남기지 않고 부모/후보 공통 적격 집합과 각 탈락 집합·사유·차이를 함께 보고한다. 같은 position/겹친 후행 경로는 시간순 train/holdout을 넘어 섞지 않는다. 실제 SELL 이후 경로가 필요한 후보는 해당 관측을 요구한다. 비용 revision/late response를 과거 cutoff에서 알고 있던 값으로 소급 사용하지 않는다. 불확실성·날짜/종목 집중도와 기존 family의 표본/선정 계약을 보고하며 새 임의 표본 수·승률·EV 문턱은 추가하지 않는다.

자동화가 소비할 새 지표는 Rebase의 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언한다. 상태·진단 지표만 추가하고 이를 threshold 권한으로 사용하지 않는다.

### 14.9 장후 재생성과 실제 지원 명령

현재 정상 생산 경로는 `log_archive_service(profile=postclose_exit)` → `build_holding_exit_observation_report(all_scope_research=True)` → `main_trailing_source_assembler.assemble()` → `main_trailing_all_scope_research.run()` → holding report 확장·handoff다. `assemble()`에는 독립 CLI가 없다. CLI가 있는 것처럼 모듈명이나 `--date/--output-root`를 추정해 실행하지 않는다.

재생성은 비용/완료 원천 → 해당 원천일 projection → 새 불변 assembly → replay → selector → summary/strict/controller 순서다. source date와 target trading date를 구별하고 달력 owner로 다음 거래일을 결정한다. 원 실패·기존 policy/PREOPEN·historical receipt는 보존하며 새 산출물은 별도 generation에 쓴다. 부모 동등 초기정책 생성과 개선 후보 선정의 완료를 구분한다. 이미 소실된 depth/AI/내부 계획을 재생성 작업이 만들어 준다고 가정하지 않는다.

아래는 **검증된 입력 manifest가 준비된 뒤** 사용하는 현존 offline CLI 형식이다. placeholder 경로는 R0의 run manifest에 기록한 실제 격리 경로로 치환한다. 이 문서 검토에서는 실행하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.automation.main_trailing_all_scope_research \
  --input-manifest /ABS/ISOLATED/ASSEMBLY/manifest.json \
  --input-root /ABS/ISOLATED/ASSEMBLY --dry-run

PYTHONPATH=. .venv/bin/python -m src.engine.automation.main_trailing_all_scope_research \
  --input-manifest /ABS/ISOLATED/ASSEMBLY/manifest.json \
  --input-root /ABS/ISOLATED/ASSEMBLY \
  --output-root /ABS/ISOLATED/RESEARCH --resume
```

출력 root가 없는 CLI는 preflight로만 끝난다. 경제 재생은 output root와 기존 admission/disk/input budget을 사용한다. `complete`만 보지 말고 population/common IDs·actual/CF 평가/검열·비용·runtime apply 상태를 읽는다. source/header preflight는 producer 계약 전수 통과나 경제 평가 완료와 다르다.

정식 장후 재생성은 기존 `run_threshold_cycle_postclose.sh`의 `postclose_exit`/safe-wrapper 인계를 따른다. wrapper gate를 우회한 `run_monitor_snapshot` 직접 실행, 운영 DATA_DIR를 쓰는 `main_stop_postclose`를 격리 연구 명령으로 제시하지 않는다. 공식 read adapter의 검증 전 실제 계좌 호출이나 전수 장후작업을 먼저 수행하지 않는다.

### 14.10 성능 구현 조건

1. Runtime은 기존 공유 snapshot과 이미 준비된 policy/context만 사용한다. 새 동기 REST/AI/정산 조회와 report 전체 읽기는0이다. 필수 주문·체결·custody 영수증을 손실 가능한 진단 queue로 옮기지 않는다.
2. 시장 source는 route/epoch별 한 번 저장하고 opportunity/position은 segment 참조를 공유한다. position의 latch/peak/잔량/AI 상태는 공유하지 않는다. 원 native sequence·중복·gap을 보존한다.
3. 장후는 immutable partition을 한 번 decode하고 후보 독립 feature를 공유한다. 동일 vector dedup, candidate block/streaming, checkpoint resume를 사용하고 마지막 후보와 반례만 상세 결과를 유지한다. 전체 모집단·제외 근거는 보존한다.
4. 비용 정정이 최종 손익만 바꾸면 economic 집계만 갱신한다. 순수익 기준 arm/정책 경로·학습 가용시각도 바뀌면 영향 replay/selection까지 무효화한다. 비용 변경을 무조건 집계 전용으로 제한하지 않는다.
5. §10의 기존 측정·합산 예산을 재사용한다. 동일 universe·기간·후보·적격 ID로 baseline/candidate 각3회 비교하며 p95/p99 판단 지연, queue drain, source gap, CPU/RSS/read bytes를 기록한다. 원천 누락·표본 축소·후보 삭제로 얻은 속도 개선은 수용하지 않는다.
6. REST/WS 한도, 운영 수집 우선순위, disk/input budgets를 유지한다. 예산 초과는 분할/재개·명시적 미수집으로 처리하며 cap 상향이나 무제한 구독으로 감추지 않는다.

### 14.11 검증·수용과 결과 보고

문서 검토 다음의 구현은 아래 실제 테스트 owner를 확장한다. 없는 test/module 이름을 실행했다고 보고하지 않는다.

| 검증 | 기존 파일 | 추가해야 할 핵심 반례 |
| --- | --- | --- |
| native 생산→소비 | [source assembler tests](../../src/tests/test_main_trailing_source_assembler.py) | 실제 producer output의 native ID/plan/후행 연결, producer 필드 삭제·오타·다른 attempt/route, complete이지만 경제0과 실제 평가 성공 구분 |
| 정규화·기회/실제 재생 | [all scope tests](../../src/tests/test_main_all_scope_trailing.py), [path projection tests](../../src/tests/test_main_trailing_path_projection.py) | ISO/epoch/ms·JSON 문자열·bool/null, 동일 시각 순서, 미래 plan/cost/context, BBO-only/OHLC-only의 경제 승격 차단 |
| 보유/ADD/AI | [holding path replay tests](../../src/tests/test_holding_path_vote_replay.py), [holding report tests](../../src/tests/test_holding_exit_observation_report.py) | 정상 ISO 비용의 ADD 세대 보존, 원 AI 미호출/입력 부족, 후보 질문 변경, 수동 이관/부분체결·잔량 수량 보존 |
| 경제 정책 생성 | [structural generability tests](../../src/tests/test_trailing_delay_structural_generability.py) | 실제 생산 fixture로 parent carry/변경 후보 분리, 공통 ID와 비용 등급, sparse 전범위 결과, CF→actual 금지 |
| 분할/정정/재개 | [partitioned tests](../../src/tests/test_main_trailing_partitioned_research.py), [log archive tests](../../src/tests/test_log_archive_service.py) | native gap/중복/epoch 전환, 64KiB row 초과, 과거 비용 revision, late 원천·새 파일, 중단 후 재개=clean recompute |
| 공식 원천 adapter | [broker cost tests](../../src/tests/test_broker_cost_source.py), [reconciliation tests](../../src/tests/test_broker_cost_reconciliation.py), 해당 기존 Kiwoom helper 테스트 | 전일·날짜 지정, continuation 반복/중단, route 혼합, 주문/체결번호 혼동, 비용 총합≠per-fill 비용, 문서 미정의 필드의 거부 |

정상 경로 테스트는 consumer 입력 dict를 손으로 채우는 것만으로 닫지 않고 실제 producer의 serializer·저장·decoder를 거쳐야 한다. 네 유형·모든 등록 scope·삼성/비삼성/신규 임의 종목·full/partial/ADD·수동/retired·세션 경계의 계약 fixture를 포함한다. 외부 provider/실계좌는 fixture 검사에서 호출하지 않는다.

수용은 (a) 필드/producer 계약, (b) 공식 원천 수집과 coverage, (c) 기준 재현, (d) 후보 경제성, (e) 성능, (f) 정식 인계, (g) 별도 승인된 실제 PID/자연 성과로 구분한다. unavailable 자료가 남으면 해당 연구 분기의 한계를 명시한다. 구조적으로 없는 자료를 기다리며 무한 재생하거나 parent_carry를 개선 정책 생성 성공으로 보고하지 않는다.

각 결과는 `결정 → 원 source/producer/consumer 증거 → 다음 action/owner → 종료 검사` 순서로 남긴다. 이번 문서 검증에서는 코드 pytest·API/provider·장후 재생성·정책 발행·배포·재기동을 수행하지 않는다.

### 14.12 공식 제공 원천과 로컬 생산 차이 — 2026-10-18 확인

공식 조회 시각은2026-10-18 08:23:59~08:25:35 KST, upstream SHA는 `953e5dbff123f437ab4d11a78a95191a685eb51f`다. `git ls-remote`와 독립 checkout의 SHA가 일치했다. `kiwoom_docs` 부재를 확인하고 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/client.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/{packets,schemas,decoders,stream}.py`, `postman/kiwoom-openapi.postman_collection.json`의 해당 PRD/MOCK 요청과 공식 `/intro`를 대조했다. 개별0B/0D/1h 포털 페이지 조회는 실패했으므로 그 페이지의 확인되지 않은 의미는 보완 근거로 사용하지 않았다.

아래는 [고정 revision 공식 스펙](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json), [REST/continuation 구현](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/core/client.py), [WS 패킷 구현](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/realtime/packets.py)을 확인한 제공 범위다. 응답 실제 확보·보관기간 전수 검증은 수행하지 않았다. wire/parser 구현 전에 그때의 공식 HEAD를 다시 확인하고 로컬 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md)를 적용한다.

| 원천/공식 수단 | 정확한 요청·응답 필드 또는 FID | 확보 범위·로컬 실행 과제·금지되는 대체 |
| --- | --- | --- |
| 종목/시장 master: `ka10099`, `ka10100` | ka10099 요청 `mrkt_tp` → `list[].code/marketCode/marketName/state/orderWarning/nxtEnable`; ka10100 요청 `stk_cd` → top-level `code/marketCode/.../nxtEnable` | 현재 master 제공. 응답 nesting을 공통으로 추정하지 않음. 과거 기준일 요청 없음. 연구일 당시 snapshot과 verified master를 사용하며 현재 NXT 편입을 과거에 소급하지 않음 |
| 실시간 체결: `0B` | `20` HHmmss, `10` 현재가, `27/28` ask/bid, `15` signed 체결량, `13` 누적량, `14` 누적대금 | 기존 공유 WS owner를 사용. 가격 원화/수량 주, `14`는 백만원. 가격 부호와 체결 방향 부호를 분리. 원 item/route/수신시각/epoch 보관 |
| 실시간 호가: `0D` | `21` 호가시각, ask41–50/bid51–60, ask qty61–70/bid qty71–80, totals121/125 | 당시 저장한 연속 book 원천으로만 과거 depth 재생. 현행 compact top-of-book만으로 전체10단계를 복원하지 않음 |
| 현재 book: `ka10004` | `sel_fpr_bid/buy_fpr_bid`, `sel_fpr_req/buy_fpr_req` 및 후속 호가 | 과거 날짜 인수 없음. 현재 snapshot은 현재 원천. `bid_req_base_tm`의 공식 설명은 YYYYMMDD이므로 이름만 보고 HHmmss 추정 금지; 의미 미확정 시 raw 보존/승격 금지 |
| 당일/전일 체결 당시 BBO: `ka10084` | `tdy_pred=1/2`, `tic_min=0/1`, `tm`; `tdy_pred_cntr[].tm/cur_prc/pri_sel_bid_unit/pri_buy_bid_unit/cntr_trde_qty/stex_tp` | **확보 가능한 복구 후보**. 당시 depth 수량은 제공하지 않음. 현행 `get_recent_signed_trades_ka10084()`는 당일 고정·단일 페이지·기본10행이며 연구용 전일/pagination/BBO producer가 아님. 기존 negative-veto 의미를 보존한 별도 역할 adapter가 필요 |
| 최근 체결: `ka10003` | `cntr_infr[]`, `tm/cur_prc`, 우선호가·체결량/강도 | 날짜 인수 없음. 같은 `acc_trde_prica`도 ka10003은 원, ka10084는 백만원이므로 API별 unit adapter 필요. 이름만으로 공통 scaling 금지 |
| 틱 OHLC: `ka10079` | `stk_cd/tic_scope/upd_stkpc_tp`, `stk_tic_chart_qry[].cntr_tm` | 요청 날짜 인수 없음, 이번 공식 spec에서 과거 보존기간·최대 페이지 보장 미확인. 받은 기간만 검증. 틱 차트로 당시 bid/ask/depth/체결방향을 합성하지 않음 |
| 분봉: `ka10080` | `base_dt/tic_scope/upd_stkpc_tp`, `stk_min_pole_chart_qry[]` | 날짜 지정 가능. `get_minute_candles_ka10080_with_meta(base_dt,explicit_request_code,...)` 재사용 검토. 완료봉·정정/수정주가·종목 route·페이지 종료 검증. 봉 내부 crossing·full fill 증거로 사용 금지 |
| 실시간 계좌 체결: `00` | `9201` 계좌, `9203` 주문, `909` 체결번호, `908` 시각, `910/911`, `914/915` 가격/량, `904` 원주문, `2134/2136` venue/SOR | 날짜·계좌 scope·원 receipt와 결속. `938/939` 당일 수수료/세금을 개별 fill 확정 비용으로 단정 금지 |
| 날짜별 주문/체결: `kt00007`, `kt00009` | 모두 `ord_dt`; 07의 `ord_no/ori_ord/cntr_qty/cntr_uv/ord_remnq/cnfm_qty/ord_tm/cnfm_tm`; 09의 `ord_no/cntr_no/cntr_tm/cntr_qty/cntr_uv` | **kt00009는 날짜별 체결번호·체결시각 복구 후보**. 이번 src 검색에서는 로컬 사용 producer 미확인. 공식 제공됨/로컬 미수집으로 등록하고 날짜+계좌+venue+주문+체결 identity·pagination을 검증한 read adapter를 먼저 마련 |
| 현재 미체결/체결: `ka10075`, `ka10076` | ka10075 `oso[].tm`은 주문시각 HHmmss; ka10076 `cntr[].ord_tm`은 주문시각 HHmmss. 주문 식별자 `ord_no/orig_ord_no` | 날짜 요청 없음. 두 주문시각을 체결 발생시각으로 대체하지 않음. ka10076 `ord_no`는 해당 번호보다 과거 체결 조회 기준이며 exact 주문 filter가 아님. 과거 날짜에 오늘 결과를 붙이지 않음. 현재 미체결0을 과거 terminal로 사용 금지 |
| 정산 비용: `kt00015` | `strt_dt/end_dt/tp/dmst_stex_tp`; `trde_dt/cntr_dt/trde_no/orig_deal_no/trde_amt/exct_amt/cmsn/trde_agri_tax/tax_sum_cmsn/proc_tm` | 날짜 범위 조회 가능. `trde_no`는 주문번호가 아님. 기존 `broker_cost_source.collect()`의 BUY/SELL 원천을 재사용. 정확 귀속 미확정이면 연구 배분/미배분으로 분리 |
| 거래일지/손익: `ka10170`, 관련 `ka10072/73/74/77` | `base_dt`, `tdy_trde_diary/cmsn_alm_tax/pl_amt`와 totals | ka10170 최근2개월 명시. 다른 API의 기간을 동일하다고 추정하지 않음. ka10074는 실현손익 발생일만 행을 만들므로 무행=거래0/비용0 금지. 기존 비용 producer는 ka10170·kt00015·당일 ka10076 수집을 이미 수행 |
| 장운영/VI: `0s`, `1h`, `ka10054` | `0s.215`, `1h.1223/1224`, VI 목록/시각 | 기존 session owner와 당시 원 receipt 사용. ka10054 과거 날짜 요청 없음. 현재 목록으로 과거 전체 정지 이력을 보장하지 않음. 미정의 `1h.9068` 의미는 추정하지 않음 |
| 내부 원천·반사실 | 실제 원 prompt/response, policy pin, receive/decision clock, transport epoch, 가상 주문 체결·queue | 미저장 내부 시각/AI/정책 문맥은 키움에서 복구 불가. 실행하지 않은 가상 주문의 실제 fill은 원리적으로 관측 불가. queue position/hidden liquidity는 검토 API에서 제공 근거 미확인. 각각 로컬 미기록·반사실 관측불가·검토 API 미제공을 구분 |

`available_not_ingested`, `available_not_requested`, `request_failed`, `partial_window`, `retention_expired`, `not_recorded_locally`, `official_semantics_unconfirmed`, `not_provided_by_reviewed_api`, `counterfactual_unobservable`를 상세 사유로 구분한다. 이 이름들은 제안 inventory 값이며 운영 enum을 변경한 것이 아니다. 특히 `not_provided_by_reviewed_api`를 키움 전체에서 절대 제공되지 않는다는 뜻으로 사용하지 않는다. `retention_expired`는 공식 보존기간 또는 provider의 명시적 조회가능 경계/기간 오류로 만료가 입증된 경우만 사용한다. 단순 실패·빈 응답은 만료 증거가 아니다. 무거래·조건·route 오류를 먼저 분리하고 불명확하면 coverage 미확인으로 남긴다.

R3의 우선 복구는 보존기간이 짧은 ka10084의 당일/전일 자료와 날짜별 체결 식별자, 그 다음 검증 가능한 비용/분봉이다. 요청 당일/전일의 정확한 달력 의미와 거래일 경계는 공식 응답으로 확인한다. 오래된 주성 사례의 depth/내부 시각이 없으면 현재 호가나 다른 날의 자료로 채우지 않는다. 외부 원천의 과거 시각과 오늘 조회한 가용시각을 둘 다 보존하고 당시 runtime이 알고 있던 정보로 소급하지 않는다.

### 14.13 실행안 리뷰·검증 기록

- 생산/소비·재생, 비용/AI/ADD/시각·권한, 공식 API 가용성의 세 독립 리뷰를 수행했다. 실제실현 하한과 새 진단의 분리, 첫 BUY fallback의 생산 미확인, 사전 계획의 시각 조건, universal ISO 비용 거부, whole-position 비용 hash 불일치, API별 nesting/주문시각, 보존기간 만료 조건을 보완했다. 변경부 재리뷰에서 문서의 미해결 지적0건을 확인했다. HX-01~11의 코드·원천 수리는 OPEN이다.
- 로컬 링크는 이 계획60개와 당일 checklist14개가 존재하며 fence·신규 owner anchor를 검사했다. print-only parser는24개 항목을 출력하고 `MainAllScopeTrailingReplay`를10/18 문서의 단일 현재 OPEN owner, Due10/19로 인식했다. `git diff --check`를 통과했다. 병행 손절 연구 계획/checklist와 기존10/19 원 Acceptance는 보존했다.
- 이번 변경은 이 계획의 §14와 최신 상태 안내, 당일 checklist의 해당 후속 owner다. 코드 pytest/compile·실제 원천 재수집·경제 재생·정책 발행·배포·재시작·외부 Project/Calendar sync는 실행하지 않았다. 공식 공개 저장소/포털 조회와 무I/O 함수 반례 확인은 계좌/provider 호출·경제성 수용이 아니다.


## 15. 2026-10-18 연구 실행 결과와 잔여 수용

실행 owner는 당일 checklist `MainAllScopeTrailingReplay`다. 별도 보유·재생 수리 세션의 완료를 전제하지 않는다. [실제 실행 검토](../audits/main-holding-exit-research-execution-review-2026-10-18.md)가 source/code/attempt/결과의 증거를 소유한다.

### 15.1 수리·원천 계약

격리 branch `codex/holding-exit-research-20261018`에 `0ab270be080c1154e5a2a6b0f5a51cad65aa796b` → `d07c3ee3f406d9f324331369698558e430f23a71` → `7dc2a934e3a0a45ff6eca7600c35a41ceda83cb2`를 보존했다. 최종 코드 계약은 `2df6ba7d0a9ddc2a7f2dcec6f780c49473c0050b7be641d64b0b4062fedd3d12`다. 실제 실행계획 receipt·문자열 JSON decode·정확한 BUY 세대/후행 quote·ISO 비용시각·scope별 비용 provenance·시간순 train 비용 가용성·cost-only resume·별도 exit-only 진단을 수리했다.

CF는 원 actual과 진입/수량/원가/계정 namespace/비용/route/세대/수동관리·원 AI 입력이 동등할 때만 원 holding vote를 연결한다. 합성 fixture에서 실제 producer→저장→public assembler→replay를 거쳐 VALID PASS2/VETO2 소비와 다른 modeled 결과를 확인했다. 가상 보유가 없었던 과거 기회에는 보유 AI를 생성하지 않는다. runtime 계정 진단은 기존 config read의 메모리 provenance를 재사용하며 추가 config I/O·계좌 조회·주문 권한을 만들지 않는다.

완료일 파일의9/28 진입 carry48376 1건을 발견했다. assembler와 일반/분할 public replay는 실제 `consumed_dates`의 최소일 KST00:00과 clean baseline을 경계로 사용한다. actual1+alternative1의 ID·entry·분모·기존 gap을 유지하고 별도 제외 사유를 남긴다. 원천을 나중에 복구해도 경계 전 진입이 튜닝에 편입되지 않으며 정각 진입은 허용한다. 선언 경계는 checkpoint/source context에도 결속했다.

[원천 계약 사전 v2](/home/ubuntu/KORStockScan-storage-archives/recovered-doc-links-20261024/files/tmp/holding-exit-research-20261018/source-audit/source-contract-audit-v2.json)는22개 계약·102개 코드 참조·23개 코드 파일과 실제 producer/저장/consumer·타입·단위·시각·identity를 검증했다. [공식 원천 능력15종](/home/ubuntu/KORStockScan-storage-archives/recovered-doc-links-20261024/files/tmp/holding-exit-research-20261018/source-audit/source-capability-matrix.json)은 로컬 미수집·공식 복구 후보·실시간 수집 필요·의미 미확정·반사실 관측불가를 분리한다. 기존14파일 원 audit와18필드 catalog는 보존했다. 공식 source 검토는 새 계좌/API 요청·구독의 실행 증거가 아니다.

### 15.2 실제 분모·초기정책·연구 방향

원천일 master2,605종목×8route/session=20,840범위를 처리했다. PRE는SOR/NXT, REGULAR와AFTER는각SOR/KRX/NXT다. scope는 등록/처리 범위이며 당시 전 종목의 연속 tick/depth 확보를 뜻하지 않는다. source일 구간9/29~10/16의 완료 census는 진입 전 carry를 포함할 수 있다. 원 보고서의 `raw_census_complete=false`, scope별 source 상태와 제외 ID를 보존한다.

v1/v3 실제 재생은 actual_completed13·actual_entry_alternative_exit13·ENTER_NOW+PASS CF482를 별도 처리했다. 공통 경제 적격은0이다. 원 custody boolean을 변경하거나 미확인 비용을0으로 채우지 않았고, 기존 수량 연구 전용 배분 비용을 holding actual로 전용하지 않았다. 보유 AI5,465행은 모두 INSUFFICIENT/provider_called=true0으로 AI HOLD/유예 성과가 아니다. 원천일 미청산3건은 별도 우측 검열 census로 유지한다.

장후 원천 재생성 경로의 **초기정책 생성은 가능**하다. 연구 부모의 시작0.4%·weak0.4%·strong0.8%를3시장×4기존 상황의12개 parent_carry cell로 생성했다. 전 범위를 위한 공통 구성이며 개별 종목20,840개의 학습 정책이 아니다. 최초 부모 계승에 추가 경제 허들을 붙이지 않는다. 신규 개선값의 경제 우위를 입증하거나 운영 정책을 발행한 것은 아니다.

분봉 진단495행(실제13+CF482) 중460행은 해당일 revision에 연결됐고 진입 후 완료봉이 하나라도 있는 경우는411행이다. CF49행은 후행 완료봉이 없고35행은 exact item/route/revision·auth scope/보관 결손이다. partial minute을 제외했으므로 진입부터 요청 종료까지 전체 horizon을 관측한 행은0이다. CF6종목 중 주성260/482의 중첩 경로를 독립 거래·승률로 계산하지 않는다.

후속 비교는 시작 전 즉시 악화/지연 회복/상승 지속, 시작 후 이익 보존, 신호 이후 체결 손실로 나눈다. 시장/venue/session은 별도 조건으로 유지하고 당시 생산된 입력만 사용한다. event 순서와 진입 기준가격·원 수탁/비용을 입증한 뒤 시작률·weak/strong을 비교하며 시간순 및 종목·날짜·겹친 경로 cluster를 분리한다. 사전 등록 numeric18개·상황 가설2개를 보존하고 새 E4/E5/E7 조합을 사후로 등록 완료 처리하지 않는다. 주성 OHLC의 사후 반등만으로 하드스톱 오판이나 안전선 완화를 결론 내리지 않는다.

### 15.3 검증·성능과 남은 단계

최종13개 파일524 PASS/75.87초,23개 변경 Python 파일 compile, 최신8개 production module Ruff, task3개 commit 전체 diff check를 통과하고 독립 재리뷰의 미해결 지적0을 확인했다. 초기 실패·중단·fixture 보완 영수증은 덮어쓰지 않는다. 더 넓은 pre-AI12실패 중 대표1건만 동일 base 재현했고12건 전체를 개별로 baseline이라고 주장하지 않는다.

실제 v1 fresh replay는995.454초에 완료했다. 기존 완료 보고서 digest 검증은cold55.892초/warm중앙5.442초였으나 이를 동일 fresh replay의 speedup으로 계산하지 않는다. 분봉 writer128MiB admission softcap을 reader source-invalid 한도로 오용한 별도 결함을 수리했고 수정 진단은5.455초에 완료했다.64MiB managed Claim과 실제 process RSS는 별도 지표다.

최종 [v3 완료 영수증](/home/ubuntu/KORStockScan-storage-archives/recovered-doc-links-20261024/files/tmp/holding-exit-research-20261018/attempts/reviewed-v3/terminal.json)은 v1과같은 source/cutoff/window/IDs/grid에서 신규 산출물 cold1회와 completed-report resume3회를 완료했다. cold 합계336.454초, warm5.460/5.503/5.530초, 전체 invocation362.301초다. 네 번의 semantic 결과가 같고 원본·보호 정책/selector/env가 불변이다. 누적 peak RSS193,100KiB와 managed Claim64MiB(종료 used0)를 구별한다. OS page cache cold·Main 지연 비악화·cold/warm 작업 간 인과적 가속비를 주장하지 않는다. v2는 native/private 봉인 인코더 차이로 OUT 생성 전 종료됐고 원 script·log·실패 영수증을 보존했다. [독립 결과 대사](/home/ubuntu/KORStockScan-storage-archives/recovered-doc-links-20261024/files/tmp/holding-exit-research-20261018/v3-output-review.json)에서 범위/ID·정책·경제 적격0·분봉 horizon 수치와 보호 세대를 확인했다.

HX09 후속은 공식 비용 생산→완료 projection→archive→assembler→공개 재생의 actual/대체청산/CF 양성 시험을 추가했다. 가짜 공식 응답의 비용1원·실현손익1원과 원 AI PASS2건을 실제 생산·소비했으며 actual/model/CF 손익을 분리했다. 해당 모듈122 PASS/16.59초·독립 신규1 PASS/4.52초·지적0으로 종결했다. 기존524개와121개는 중복되므로 합산하지 않는다. 시험만 바꾼 commit `1bf35e6c258cdcda373c813432b52725898f22ab`과 [후속 종결](/home/ubuntu/KORStockScan-storage-archives/recovered-doc-links-20261024/files/tmp/holding-exit-research-20261018/code-review-closure-v4.json)을 보존했고 production SHA·실제 v3 원천/보고서는 동일하다. 합성 계약 검증이 자연 경제성 증거를 대신하지 않는다.

현재 owner는 경제 비교 적격 원천, 별도 holding 연구 배분 consumer, 미지원 ADD/부분잔량·실제 SELL 이후 경로와 후속 실험을 OPEN으로 유지한다. 복구 불가능한 과거 내부 AI/계획과 가상 실제 fill의 자연 생산을 기다리는 종료 조건은 두지 않는다. 선택900/PREOPEN 정책·수동 제외를 변경하지 않았고 운영 발행·배포·Main 재기동·계좌/API 조회·신규 구독·provider 호출·주문은 실행하지 않는다. 실제 PREOPEN/PID 수용은 기존 DirectFamilyPreopenPolicyHandoff의 별도 수용이다.

## 16. 2026-10-18 후속 실험·진입 이력·비용 소비 수리

[후속 실행 검토](../audits/main-holding-exit-followup-research-execution-review-2026-10-18.md)가 실험 등록·실제 결과·첫 비용 undercoverage와 보완 결과를 소유한다. 격리 `a4a51fd8b`의 최초 실행과 `57a4659f4`의 비용 소비 시각 수리를 분리한다. 실행 owner는 같은 `MainAllScopeTrailingReplay`이며 별도 수리 세션을 기다리지 않는다.

### 16.1 실제로 추가 활용한 원천

- 전체2,605종목·8route/session=20,840범위를 재생 census에 유지했다. 등록 범위와 관측 coverage는 다르다. 실제13+CF482=495행을 다루며 대체청산13은 독립 거래로 중복 합산하지 않는다.
- 진입 전에 가용한 native named revision으로120봉 OHLC 특징227행(실제3+CF224)을 복원했다. 전일 봉 포함34행·내부 공백157행, 마지막 봉 경과 중앙84.6분이다. 같은 원천을 공유하는 revision64개를 decode·cache163회 재사용했다. 기존6특징의 spread/session VWAP·가격 조정 등가성과 과거 실제 소비를 입증한 것이 아니므로 원 pin·AI를 변경하지 않았다.
- 고정120초 prefix와 후행10/60분을 연결한 연관 분석은176행(실제3+CF173)·304개 row-window·23개 중첩군이다. 원495행의 결측 사유는 모두 남겼다. 내부 완료봉 관측과 전체 horizon 관측0건을 구분한다. 이번 시간순 분할은 이미 보았던 기간의 탐색 분석이며 새 holdout 검증으로 부르지 않는다.
- 별도 holding 연구 비용 consumer는 원 승인8건을 원scope `initial_quantity_research_only`로 연결했다. 최초5건만 연결된 것은 체결 발생시각과 projection 최초 관측시각의 의미 혼동이었다. 원 producer의 exact 신원·payload digest·가용시각/재관측 감사로3건을 연결했고 허용 시차는0이다. 원5건 결과와 최초 terminal을 보존했다. 비용4,065원·배분 연구 순액19,535원은 과거 관측8건의 참고이며 개선액/실제 자동성과가 아니다. 49294 부적격·미청산3건·다중BUY terminal의 구분은 유지한다.

### 16.2 연구 판정

ENTER_NOW+PASS와 후행 자료를 추가 활용할 수 있지만 실제 fill·원 holding AI·연속 수탁·대체청산 비용을 생성하지 않는다. 진입 OHLC 네 특징은 별도 설명변수다. 이번 `upward_efficient` 양성은0이어서 새 상승 지속 유형의 효과 비교는 불가하다. 시장 외 상황 구분 연구는 유지하되 오래된 원천/내부 공백을 현 상황으로 간주하거나 기존6특징 분류기를 대체하지 않는다.

주성의 특징 복원163행·연관119행은 모두CF다.10/15 실제49294의 진입 특징은 결손이며 그날 진입120초 이후60분 관측봉은 -3% 비교선 접촉·+0.4% 목표 미접촉이다. 다른 날 반등·CF를 합쳐 하드스톱 오판이나 수동 이관 후 자동 성과를 결론 내리지 않는다. 신호 snapshot→기록상 완료 간격도 주문/브로커 latency와 구별한다.

시작률·weak/strong 개선값의 경제 우위는 미입증이다. 선행 연구의12cell 부모 계승 초기값·classifier=null과 정책 hash를 그대로 보존했으며 새 정책을 생성·발행하지 않았다. 초기값에 추가 경제 승인 허들을 붙이지 않는다.

### 16.3 수용 범위와 다음 owner

최초 네 진단 단계12.748초·peak RSS61,336KiB, 별도 비용 재실행0.142초·24,496KiB를 관측했다.64MiB는 managed Claim 한도이며 종료 used0이다. 이전 전체 재생과 다른 작업이어서 가속비·Main 지연 비악화를 주장하지 않는다. 최종 대상 통합284 PASS/8compile/Ruff/diff-check와 독립 코드·결과 검토로 닫았다. 실제 초기 비용5건 결과와 원 실패·원 source/정책/PREOPEN·보호9해시는 보존했다.

별도 관측 terminal 배분비용의 diagnostic 소비 수리는 완료했다. 잔여 `MainAllScopeTrailingReplay`는 당시 입력의 경과시간/공백·실행 가능 기준가격·연속 순서를 입증한 범위의 정책 비교, ADD/부분잔량 lifecycle·실제 SELL 뒤 경로 및 신호→제출→체결 신원 연결을 소유한다. 원천이 없는 과거 내부 판정·가상 실제 fill을 대기 조건으로 두지 않으며 이번 자료로 비교 불가인 가설은 그대로 구분한다. 실제 PREOPEN/PID는 기존 `DirectFamilyPreopenPolicyHandoff`의 수용이고 P5는 이번 연구에서 실행하지 않았다. 운영 배포·재기동·외부 조회/구독·provider·주문·Project/Calendar sync는 없다.


## 17. 2026-10-18 현재 원천 범위 연구 종결

사용자의 잔여연구 종결 지시에 따라 §15–§16의 기존 실행과 [보유 비용 소비 후속 검토 §6](../audits/main-holding-research-cost-consumer-followup-review-2026-10-18.md#6-native-비용-결손-사유-보완과-최종-별도-대사)의 결과를 대사했다. 이번 원천·가설 범위의 `MainAllScopeTrailingReplay`를 종결한다. §15–§16의 당시 OPEN 기록은 역사로 보존하며, 신규 정책의 경제 우위·운영 적용 완료로 바꾸지 않는다.

- 별도 holding 배분비용 adapter는 `d81a80778`→`3ab6916e2`에서 public assembler·분할 재생·진단에 연결했다. native producer의 `source_gap_exact_cost_missing` 상태명 누락까지 수리하고 정상 생산→소비·duplicate/unknown 사유 거부를 검증했다. 전체 비용행은 managed SQLite/참조로 보관하며 4slot cache·exact stat/종료 해시 대사와 공유64MiB admission을 유지한다.
- 최종 실제 비용 전용 attempt03은 원508개(13 actual/13 alternative/482 CF), 엄격 비용 provenance5건·경제 paired0건, 원247개 nullable outcome·초기정책·사용19개 의존 세대를 보존했다. native 비용 label 수리 후20 PASS와 독립 재리뷰 지적0, wall23.513초·CPU22.421초·peak RSS168,648KiB·종료 shared used0을 확인했다. 전체12GB fresh replay 또는 Main 성능 비교로 확대하지 않는다.
- 병행 `57a4659f4`의 관측 terminal 참고8건은 등록된 native 재관측 audit의 발생·최초 관측 시각 bridge를 소비한 별도 계약이다. 공통5건의 영수증·비용·net 참고값은 같고 추가3건의 증명 범위는 분리한다. 두 branch를 통합 검증한 것으로 부르지 않으며 어느 쪽도 canonical 실제 비용·손익·자동관리 적격을 변경하지 않는다.
- 경과시간/내부 공백이 있는 OHLC227행과 탐색적 연관176행은 원6특징·원 AI·연속 실행 가능 경로를 증명하지 않는다. 현재 cohort의 시작률/weak/strong 우위, ADD/부분잔량 lifecycle, SELL 이후 미저장 경로, exact signal→intent→order→fill bridge는 해당 입력으로 비교 불가라는 결론으로 닫는다. E4/E5/E7의 새 전략을 구현·실행했다고 처리하지 않는다. 새로운 원천·가설은 별도 사전 등록 실험이며 같은 과거의 자연 표본 축적을 기다리는 blocker는 두지 않는다.

원12cell 초기 부모 계승과 원천·보조 AI·수탁/수동 제외·비용·selector/PREOPEN은 보존했다. 이후 자연 원천·실제 PREOPEN/PID는 기존10/19 owner의 별도 수용이다. P5는 **모든 연구 종료 뒤에도 사용자의 별도 실행 지시 전까지 보류**한다. 운영 발행·배포·Main 재기동·외부 계좌/API·구독·provider·주문·외부 sync는 실행하지 않았다.

## 18. 2026-10-23 방향 갱신과 새 원천 연구 실행

사용자 요청에 따라 현재 AGENTS.md, Plan Rebase §1–§8,10/23 checklist를 다시 읽었다. §17의 과거 연구 종결을 취소하지 않고10/22 봉인 원천·10/23 신규 실제 체결로 후속 연구를 실행했다. 실행·수치·검증은 [10/23 검토](../audits/main-holding-exit-opportunity-research-review-2026-10-23.md), 실행 중인 후속 원천 작업은 [현재 checklist](../checklists/2026-10-23-stage2-todo-checklist.md)의 `HoldingProfitExitSourceContractRepair`가 소유한다. 기계/진입 연구의 기존 owner를 복제하지 않는다.

### 18.1 연구 질문을 청산 단계별로 나눈다

1. **진입→자동 보유 인계:** 실제 fill 이후 자동 보유가 시작되지 않은 시간, 부분 체결·미제출 잔량, 복구/수동 이관을 분리한다.10/22 주성49445의 복구 전 시간을 정상적인 장기 보유 전략 성과에 넣지 않는다.
2. **시작률 도달 전:** 진입 근거와 초기 역행·시간 경과를 연구하되 hard/protect/emergency의 완화와 섞지 않는다. ENTER_NOW+PASS 미체결 기회는 원시각의 ask와 후행 bid, 누락·취소·경로를 붙인 별도 CF 모집단이다.
3. **시작률 도달 후:** 체결가 기준 최고점과 실제 매도 가능 bid의 차이, 최소 호가 단위·spread·잔량·모델 비용을 함께 측정한다. 시작률과 되돌림폭은 결합 변수다. 약+0.4%에서 시작해0.4%를 반납하면 비용모형이 같은 이상적 연속 가격에서도 약−0.0016%이며, tick/호가 괴리로 손실이 커질 수 있다. 시작은 최소 수익 보장을 뜻하지 않는다.
4. **기계 강약·보유 AI:** `mechanical_strength_v2`의 사건별 상태와 `holding_path_vote`의 입력 적격·투표·유예를 분리한다. 고정0.4/0.8 진단은 실제 강약 전환 재생이 아니다. 투표0을 PASS/VETO 또는 AI 품질 점수로 대체하지 않는다.
5. **청산 신호→실제 체결→매도 후:** 동일 BUY 신원·signal·submit·terminal을 연결하고1/3/5/10분의 같은 item/route bid를 사용한다. 종가·분봉 고가를 당시 매도 가능한 가격으로 바꾸지 않는다. 후행 상승만으로 앞선 hard stop을 오판으로 판정하지 않는다.

### 18.2 이번 실행으로 확정한 방향

- 10/22 장전 NXT41·정규장 NXT 별도 관측179·정규 통합160·장후 통합189개, 총569개 확인 지점에 시작률0.4와 고정 폭0.4/0.8을 적용했다. 전체는 이미 본 부모 정책 원천이므로 탐색 분석이다. 중첩 지점은 독립 거래가 아니며 전략 수익으로 합산하지 않는다.
- 두 폭 모두 가격 조건 종점이 있는216쌍에서0.4가 우세165·0.8이 우세36·동일15였다. 잔량·M1·유예·실제 주문 및 시간 guard를 재생하지 않았으므로 수치 승격 근거가 아니다. **strong 폭을 일괄 확대하는 방향은 채택하지 않고 수익 보존과 상승 지속의 구별을 먼저 연구한다.**
- 약세장에서도 선행 관측과 이후 bid 상승을 확인했다.034020·036930의 예시에서는0.8로 기다릴 때 더 반납했다.003010·290720는 후행 목표 bid가 존재해도 체결가 최고점과 bid의 괴리로 단순 trailing 조건이 먼저 발생했다. 종목코드는 사례 식별 기준이며 종목별 whitelist를 만들지 않는다.
- 다음 상황 특징은 기존 계약을 확장해 다룬다: **상승 지속, 약세 속 반등, 호가 괴리/가격 변동**, 그리고 입력 결손. 진입 전 특징으로 최초 유형을 정하고 이후 M1 상태 변화는 시간순 상태로 유지한다. 사후 고점·사후 승패로 진입 유형을 지정하지 않는다. 새 classifier나 종목 whitelist는 이번에 발행하지 않았다.
- 시장 약세를 일괄 진입 금지로 해석하지 않는다. [누적 기회 연구](main-cumulative-opportunity-and-executable-quote-research-plan-2026-10-17.md)의 선행 패턴·시장 상대 강도·원 ask→bid 증명을 재사용한다. 잘못된 PASS, 유효 PASS의 후단 차단, 기계 미포착, 청산 후 상승은 별도 분모다. 약세장 반등 수익이 있었다는 사실과 실행 가능 수량·실제 순익 증명은 다르다.

### 18.3 원천·변수·소비 계약을 먼저 닫는다

| 우선순위 / 기존 owner | 첫 확인 계약과 다음 작업 | 종료 검사 |
| --- | --- | --- |
| 1 / `HoldingProfitExitSourceContractRepair` | 49480 보유 투표29행 중22행은 `executable_exit_pnl_missing`,7행은 quote/tape 불가다. `build_holding_decision_context()`의 `execution_pnl.executable_sell_price`·`estimated_net_executable_pnl_pct`가 `path_vote_input_gaps()`까지 전달되는 exact 입력을 대사한다. `_trailing_entry_cost_model`, 정상화된 book, 수량, fee/slippage의 absent/invalid를 각각 보존한다. | 당시 원 gap fixture와 새 동일 route 입력의 producer→context→vote preflight 소비. 결손을0으로 채우거나 quote guard를 해제하지 않는다. 현재 증거로 내부 어느 cost/book 분기가 원인인지 미확정인 점을 유지한다. |
| 2 / 동일 owner | `_observe_scalp_trailing_input_transition()`이 상세 기록256개와 한도 고지1개 이후 중단했다. 기계 입력3999개·별도 stop source2047개와 중복 저장하는 대신 기존 writer/index/segment를 재사용해 quote·M1·AI state와 정책/BUY 세대 참조를 연결한다. 단순 한도 증가는 해법이 아니다. | 256개를 넘는 보유·재시작·ADD/부분잔량·세대 전환에서도 실제 coverage/gap과 first crossing/terminal이 보존되는 분할 재생. 기록 bytes·이벤트 처리량·지연·RSS·index 읽기량 대사. |
| 3 / 동일 owner, 경제 비교는 기존 trailing selector | 위 두 원천이 적격인 actual/alternative/CF 각각에서 시작률×폭×유형의 공통 ID 비교. 0.4/0.8 고정 진단을 실제 강약/AI 성과로 승격하지 않는다. | 동시대 부모/후보, 실제 비용/모델 비용 분리, censored 수량/경로, 누적·후속 미사용 기간, winner 보존/실패 감소를 같은 분모로 검증. 부적격 구간만 제외하고 전체를0건 수익으로 처리하지 않는다. |
| 연계 / `MachinePatternOpportunityResearch1023` | 소스22의 이미 본 결과를 새 holdout으로 사용하지 않는다. 소스23 봉인 후 기존 예정 창에서 같은 정의로 약세 반등·상승 지속과 실패 대조군을 평가한다. | 기존10/26 07:40–08:00 owner에서 closed receipt·source epoch·선행 시장 관측을 결속한다. 장후 오래된 정규장 지수는 장후 약세 증거로 사용하지 않는다. |

공식 원천 가용성은 §14.5/§14.12와 [키움 원천 계약](../kiwoom-api-data-contract.md)을 따른다. 이번에는 외부 요청/파서/구독을 바꾸지 않았다. 향후 변경 전 공식 참조 gate를 수행한다. 현재 저장된 BBO·체결·book·봉·계좌/체결/비용 영수증은 해당 필드의 실제 producer·단위·시각·item·route로 연결한다. **과거 미저장 호가 전량 경로, 실제 발주하지 않은 가상 체결/대기열, 호출하지 않은 과거 AI 답변, 명시 거래소가 없는 SOR 체결 거래소**를 조회 가능 원천으로 약속하지 않는다.

전체2,602종목×8scope=20,816등록 범위와 실제 관측 범위는 구분한다. 이번 네 분할 외의 scope는 기존 scope ledger의 unobserved/nonoperating 사유를 유지하며 지원 삭제로 처리하지 않는다. PREMARKET의 `_NX`/NXT와 정규·장후 `_AL`/SOR를 분리하고 물리 체결 venue는 native 영수증이 없으면 UNKNOWN이다. 정규장 NXT 별도 원천은 현 Main 기본 경로가 아니라 해당 역사 연구 분할이다. 현재 승인 초기값0.4/0.4/0.8의 운영 사용에는 새 경제 gate를 붙이지 않는다.
