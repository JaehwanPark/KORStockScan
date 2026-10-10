# Main 전체 종목·시장 보유청산·익절 및 장후 재생 개선 상세계획

작성일: 2026-10-10 KST

상태: 공통 코드 구현·반복 리뷰 및 승인된 코드 배포를 완료했다. **전체 계획 수용은 미완료**이며 `MainAllScopeTrailingReplay`를 OPEN으로 유지한다. 전수 원천 연결·상한 초과 분할·전체 연구 성능과 S6 신규 정책 발행/장후 재생성은 남아 있다. 아래 기존 문서 검증 기록은 작성 당시 이력이며 현행 코드·배포 근거는 후속 기록을 따른다.

후속 승인 배포(10/10): 검증된 공통 코드와 부모 동등 초기 구성은 `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28`로 배포했다. 10/12 PREOPEN 전체 계약·예약경로·최종화 세대는 PASS다. 신규 제출 지연 v2 정책 발행 및 전수 연구/대용량/전체 연구 성능 수용은 OPEN이며 상세 상태는 [후속 리뷰·배포 기록](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md)을 따른다.


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
| 구현과 운영 | 현재 선택 release는 `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06`; 준비 index는 10/12를 가리킨다. | 이 dated 확인을 새 코드의 배포/PID 증거로 재사용하지 않는다. 현재 준비와 새 계획 적용은 별도다. |

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
