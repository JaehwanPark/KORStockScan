# 메인 BLOCK/RECHECK 전환 임계치 장후 학습·런타임 구현계획

작성일: 2026-09-21 KST
상태: 즉시 적용 경로 구현·리뷰·배포·기동 및 장후 재평가 실행. 후보별 downstream 재생 연결이 남아 새 수익성 정책 생성/승격은 미완료. 다음 장전 대기 없이 적격 generation을 적용하며 다음 적격 generation까지 승계한다. 실제 배포/PID/정책 선정 증거는 [구현 리뷰](../audit-reports/2026-09-21-main-entry-strategy-runtime-review.md)를 기준으로 구분한다.
실행 owner: [당일 체크리스트의 DirectFamilySourceRepairMainMechanisticEntry](../checklists/2026-09-21-stage2-todo-checklist.md). 기존 원천·경제성 acceptance를 보존하면서 아래 구현 범위를 연결한다.

## 1. 목표와 완료의 의미

목표는 **원천이 유효한 미진입 기회에 대해 기존 BLOCK/RECHECK를 ENTER_NOW로 바꿀 수 있는 모든 설정 가능한 main 전략 임계치의 조합을 탐색하고, 동일 기회 모집단의 비용 후 기대값과 거래일당 순이익을 개선한 적격 정책을 장중에도 기본 정책으로 적용하여 다음 적격 정책까지 승계하는 것**이다. 손실을 피한 미진입과 새로 발생하는 손실도 같은 기준으로 비교한다. ENTER_NOW 비율이나 주문 수 자체를 목표로 하지 않는다. 사용자 관찰의 all-BLOCK/RECHECK는 우선 검증 fixture와 문제 정의이며, 이 문서 점검이 현재 세션의 실시간 전수 계수를 재측정했다는 뜻은 아니다.

이 계획은 기존 계획의 3축 제한·작업 순서·복구 완료를 구현 범위의 상한으로 삼지 않는다. 기존 소유 코드와 검증된 원천은 재사용하되, 아래 계약이 기능 범위와 완료 기준이다. 과거 계획·완료 기록을 수정하거나 과거 완료를 전면 재개방하지 않는다.

구현 완료에는 다음이 모두 필요하다.

1. 후보가 당시 원시 입력에서 전략 사실·위험·action을 재계산한다. 고정된 BLOCK 라벨을 다시 넣고 유동성 숫자만 바꾸는 방식은 불가하다.
2. 전략적 BLOCK→ENTER_NOW, RECHECK→ENTER_NOW, 위험한 ENTER_NOW→미진입을 각각 동일 입력 fixture에서 재현한다. 모든 후보가 incumbent와 같은 action이면 차단 조건 미연결과 경제적 무개선을 구별한다.
3. 실제 원천의 동일 모집단에 incumbent/candidate를 적용해 회복 기회·추가 손실·실행 가능성·비용·자본점유를 비교한다. 미관측을 0이나 AI PASS로 채우지 않는다.
4. 적격 후보는 기존 publisher→공통 activation validator→장중 loader 또는 PREOPEN→기계판정→보조 AI→최종 주문 guard 경로로 전달된다. 장중 기본 정책과 다음 날 시작 정책이 같아야 하며 부적격/미생성 후보는 현재 기본 정책을 대체하지 않는다.
5. 코드/배포/정책 선정/PID 소비/자연 제출/비용 후 성과를 각각 보고한다. 후보 불합격은 구현 실패가 아니지만, 후보가 전략 BLOCK을 바꿀 수 없는 구조는 완료가 아니다.
6. 최종 산출물은 **현재 종목의 유형과 상태에 맞는 조합을 선택하는 하나의 기본 정책**이다. `분류 feature/경계 + 유형·상태별 전체 전략 임계치 + 선택 순서 + 상위 기본값/결손 처리`를 하나의 generation으로 평가·발행·소비한다. 장후만 유형별 분석하고 runtime은 공통 숫자를 쓰는 구현은 미완료다.

최초 요청은 계획 작성이었고, 후속 사용자는 전체 조합 탐색·과도하지 않은 갱신 조건·구현 후 실행 결과의 장중 적용과 기본 정책 승계를 명시했다. 최초 작성 turn은 계획 점검이었으며, 후속 사용자가 구현·반복 리뷰·커밋·푸시·배포·기동·장후 재생성과 즉시 적용을 명시 승인했다. 후속 구현이 검증되면 해당 main 정책의 평가 실행·적격 결과 적용을 개별 후보 재승인 없이 이어간다. 새 broker probe/테스트 주문·provider 교체·다른 프로세스 변경·안전 기준 완화 권한은 포함하지 않는다. main의 필요한 release 인계는 기존 관리 절차를 사용하고, 정책 갱신은 아래 원자적 reload를 기본으로 설계하여 불필요한 재기동을 만들지 않는다.

### 1.1 이번 점검에서 수정한 결함

- 단일좌표+조건 쌍으로만 탐색하면 세 개 이상을 함께 바꿔야 열리는 유효 진입을 놓친다. §6.2는 전체 전략 좌표의 joint search와 3축 이상 전환 시험으로 대체했다.
- 첫 수치 집합을 영구 허용 범위로 고정하거나 기존 상수를 `fixed_strategy`로 남기면 숨은 차단이 유지될 수 있다. §4는 전수 registry와 calibration 경계 확장 계약을 추가했다.
- 기존 5종목/5일 등 floor를 새 정책에 무조건 재사용하면 수익성 있는 scoped 정책의 갱신을 막을 수 있다. §6.4에서 연구·적용 gate를 구분하고 최소 갱신 계약을 명시했다.
- 다음 PREOPEN 전용 발행과 날짜별 파일 우선 로더만으로는 장중 적용과 지속 승계가 보장되지 않는다. §7을 승인된 기본 generation의 원자적 전환·지속 보존 계약으로 바꿨다.
- 유형별 조합의 구체적인 분류·선택·기본값 계약이 없었다. §4.1–§4.3 및 §6.5에서 유형·상태 선택과 전략 임계치의 공동 학습, 동일 runtime selector, 하나의 기본 정책 발행으로 보완했다.

## 2. 확인된 출발점과 소유 경계

- [기존 공통 후보](../../src/engine/scalping/ai_action_outcome_calibration.py)의 `MECHANISTIC_COMMON_FEATURE_GRID`는 spread/fillability/top3 ratio만 검색한다. `_mechanistic_policy_rows`는 보존된 setup을 재판정한다.
- [setup/core](../../src/engine/scalping/entry_setup_evidence.py)의 `build_entry_setup_evidence`는 상위 분석의 facts/hard_blockers/phase를 받는다. `mechanistic_entry_action_core`의 전략 BLOCK은 뒤쪽 임계치로 해소되지 않는다.
- [전략 사실 생성](../../src/engine/scalping/ai_decision_quality.py)의 `_entry_contract_facts` 및 유동성·회복 분석, [완료봉 구조](../../src/engine/scalping/entry_candle_context.py)의 `_local_breakout` 등에 전략 상수가 분산되어 있다. 단순히 최종 BLOCK 체크를 삭제하면 안 된다.
- 9/21 정책 파일을 읽은 시점의 공통값은 spread100bp/fillability15/top3비율5, hierarchy rules0이었다. 공통 grid의 가장 완화된 경계여서 공통축만으로 추가 회복을 찾기 어렵다. 이는 작업 시점 파일 증거이며 실제 PID 적용 증거가 아니다.
- 재사용 owner는 `ai_action_outcome_calibration`, `entry_setup_evidence`, `entry_setup_live_policy`, `mechanistic_entry_runtime_policy`, `strategy_owner_replay`, `entry_setup_paired_replay_batch`다. 신규 optimizer/DB/report family/cron/daemon은 만들지 않는다.

범위는 기존 메인 기계판정이 소유하는 등록 venue/session의 초기 진입이다. widget/episode/manual, holding/exit, AVG_DOWN/PYRAMID의 판정·수량·custody는 바꾸지 않는다. 공유 함수를 수정하면 main 정책을 명시적으로 받은 호출에만 새 의미를 적용하고 다른 호출은 기존 결과를 보존한다.

## 3. 안전 조건과 전략 조건의 분리

기존 이름이 `hard_blocker`라는 이유만으로 모두 영구 고정하지 않으며, 수익 기회를 놓쳤다는 이유로 모두 튜닝 대상으로 바꾸지도 않는다. 각 조건의 실제 producer와 consumer를 연결해 다음 소유권을 확정한다.

| 분류 | 소유 조건 | 변경 방식 |
| --- | --- | --- |
| 고정 source/실행 안전 | quote freshness/stale·crossed/nonpositive BBO·route/epoch/clock 충돌·필수 자료 결손, DANGER/deadline/slippage, broker/account/order/qty/cooldown, hard/protect/emergency, 명시 operator lock | 후보 입력에 넣지 않음. 모든 후보와 런타임에서 기존 기준 우선 |
| main 전략 판정 | 과열 추격, 매도벽, 분산/하락 구조, 국소 돌파 실패, 거래량·체결·가격 확인, 재확인 필요성 | 당시 수치에서 정책별 재계산. 등록된 유한 범위 안에서 강화와 완화 후보 평가 |
| 경제성·승격 검증 | 비용·paired 비교·holdout·표본·tail·자본/실행 지원범위 | 전략 후보가 변경할 수 없음. 동일 버전의 evaluator/validator/publisher 기준 사용 |
| 관측 운영값 | 비진입 자금 cache5초, ENTER_NOW 준비2초 등 | 이번 전략 튜너의 범위 밖. 주문 자금 증거와 관측 source를 구분 |

특히 main의 `blocking_overextension` 같은 전략 사실과 최종 runtime overbought/submit safety를 같은 키로 완화하지 않는다. 보호된 최종 guard가 별도로 남아 후보를 차단하면 그대로 `next_blocker`에 남긴다. 보호 guard로 실제 실행이 불가능한 후보에 회복 순익을 부여하지 않는다. 명시 승인 override도 scope/expiry/우선권을 유지한다.

## 4. 정책으로 이동할 임계치와 첫 탐색 범위

아래 값은 **탐색의 시작점이며 영구 상한·하한이 아니다.** 현재값을 항상 포함하고 calibration만으로 후보를 정한다. 전략 registry는 좌표별 실제 consumer, 단위, 수학적/계약상 허용 범위, incumbent, 시작 grid, 경계 확장 규칙, source 요구사항을 소유한다. 시장·세션별 incumbent가 다르면 그 값도 포함한다. 단위는 퍼센트와 bp를 구분하고 bool/NaN/무한대/알 수 없는 키를 거부한다. 임계치 미충족과 입력 부재는 별도다.

동일 raw에서 판정이 달라지는 관측값의 경계와 그 양옆을 calibration에서 추출해 grid를 보강한다. integer/tick 좌표는 유효 격자를 사용한다. 최선 후보가 시작 grid 끝에 있거나 모든 후보가 같은 action이면 registry의 허용 범위 안에서 다음 경계까지 확장한다. 이 규칙과 최대 허용 범위는 holdout을 보기 전에 고정하며, 변경은 새 search generation으로 남긴다. 비용/미래 수익을 feature 경계 설정에 쓰지 않는다. 보호된 안전 범위는 확장하지 않는다.

| 전략 축 | 정책 좌표·첫 후보 | 전환 방식과 제한 |
| --- | --- | --- |
| 과열 추격 | 당일상승 기준 {12,15,18,20}%, micro-VWAP/MA5 이격 각각 {60,80,100,120}bp | 현재 복합 조건을 각 후보로 재계산. 상승·이격만 완화해도 다른 tape/구조 위험이 남으면 진입 불가. 최종 주문 과열 guard와 분리 |
| 매도벽 | wide-spread 기준 {40,50,60,80}bp, 최우선 ask/bid 금액비 {3,5,7,10} | 매도벽 위험 사실을 재계산. 기준 아래라는 이유만으로 ENTER_NOW를 만들지 않고 확인된 매수/가격·실행 가능성 요구 |
| 분산·하락 구조 | 5분 하락 {−0.3,−0.5,−0.75,−1.0}%, 10분 {−0.75,−1.0,−1.5}%, 고점낙폭 {−1.5,−2.0,−3.0}%, 거래량 약화 {0.3,0.5,0.7} | 각 비교 부호와 복합 AND/OR를 스키마에 명시. 단순 숫자 완화 뒤에도 진입 근거가 없으면 RECHECK. 하락 회피 손익을 대칭 평가 |
| 국소 돌파/재확인 | 사전 완료봉 lookback {5,10,20}, 최근 사건 window {2,3,5}, 같은 저항 아래 연속종가 {1,2,3}, 저항/지지 이탈 여유 {0,1,2}틱 | 저항은 돌파 이전 자료로 고정. 현재까지 확인된 봉만 사용. 확인 기간과 lookback 후보의 원천 부족을 별도 제외; 후행봉으로 과거 실패를 취소하지 않음 |
| 구조적 상승 확인 | 장기 5/10/20/60분 중 양수 수익률 최소개수 {2,3,4}, 양수 slope {2,3}, 초기 1/3/5/10분 양수 수익률·slope 최소개수 각각 {2,3} | 필요한 실제 window가 존재할 때만 계산. 미존재 window를 0이나 양수로 채우지 않음. 거래량·고저점 방향 등 동반 조건은 explicit policy/고정 조건으로 식별 |
| 거래량·매수 확인 | 거래량 확인비율 {0.8,1.0,1.2}, 매수압력 {55,60,65}, 순공격매수 delta {1,5,10}, 10tick 가격반응 하한 {0,0.02,0.05}% | delta·가격반응은 양의 확인을 유지하며 0/음수 매수 흐름을 진입 증거로 만들지 않음. trusted count는 P0에서 필수 source 최소치와 조정 가능한 전략 지지량을 구분하여 registry에 결속 |
| 대량매도 후 회복 확인 | 고정 검출기의 원 event를 보존하고, 이후 신뢰체결 {10,20,30}개·순매수 전환·가격회복 여유 {0,1,2}틱 | 검출기/FID 의미를 바꾸지 않음. 새 대량매도는 회복 상태를 reset. event 시각/체결 순서가 없는 옛 true/false만으로 완화 후보 평가 불가 |
| 늦은 진입/재승격 reset | watch age {300,600,900}초, 상승 연장 {0.5,1.0,1.5}%, 반복 promotion {2,3,4}, reset 낙폭 {−0.25,−0.5,−0.75}% | 정확한 promotion/timing 원천이 있는 경우만. AI timeout·submit deadline·보유 cooldown을 변경하지 않음 |
| 공통 유동성·micro | 기존 spread {40,60,80,100}bp, fillability {15,30,45,60}, top3 {1,1.5,2,3,5}; 기존 depletion/trade-backed/refill 집합 | 기존 3축은 유지하되 전체 탐색의 전부로 삼지 않음. 전략 BLOCK 해소 뒤 실제 유동성 재판정과 계층별 확인에 사용 |

숫자 목록만 설정으로 옮기고 기존 upstream 라벨을 그대로 쓰면 실패다. 구조 phase, invalidation_facts, corroborated_risk_codes, tail 분류, counterweight와 group/family 선택까지 후보 의미에 맞게 재계산한다. tail 복합 기준100bp/15/5, 상대약세−0.50%p, volume/supportive/adverse 판정 등 다른 설정 가능한 전략 수치도 registry에 포함한다. 단지 현재 상수라는 이유로 `fixed_strategy`에 남길 수 없다. 신뢰체결10개 같은 값은 필수 estimator/source 계약의 최소 지지량인지 전략 확인 강도인지 producer까지 구분하고, 후자이면 설정 가능한 축에 포함한다. 필수 입력의 존재·진위와 전략적 충분성은 다른 조건이다.

P0에서 추가로 발견한 전략 차단은 위 표 밖이라는 이유로 제외하지 않는다. main의 모든 BLOCK/RECHECK 반환 지점을 대사하여 정책 연결, 보호된 안전 조건, 또는 원천/비숫자 구조 조건 중 하나에 대응시킨다. 현재 전략 상수라는 이유만으로 `hard_safety`로 재분류할 수 없다. 추가 축의 범위·단위·검증을 이 문서에 보완한 후 구현하며, source 미지원 축이 남으면 전체 전환 학습 완료가 아닌 부분 완료로 보고한다.

대량매도·돌파 실패에는 `BLOCK→RECHECK→ENTER_NOW` 순서도 가능하다. 후보별로 미리 선언한 fresh 회복 조건이 충족되기 전에는 ENTER_NOW로 바꾸지 않는다. RECHECK가 반드시 기다려야 하는 최소시간을 새로 강제하지 않으며, 현재 프레임에서 조건이 이미 충분하면 즉시 평가한다.

### 4.1 유형·상태 feature와 원천 계약

기존 `_entry_group_observation`/`build_entry_predecision_group_observation`을 확장한다. 현재 호가단위 비율·유동성·변동성 등의 관측과 제한된 hierarchy가 있다는 이유로 새 전략 전체의 유형별 소비가 구현된 것으로 보지 않는다. 시가총액은 현재 grouping key에 없고 `_resolve_stock_marcap`의 최신 DB 값만으로 역사 as-of가 증명되지 않는다.

| 유형/상태 | shared selector가 사용할 입력 | 장후·런타임 공동 계약 |
| --- | --- | --- |
| 시장·세션·시간대 | effective venue/session, 해당 시장 거래일·현재 평가시각, 세션 시작 이후 경과 | 최상위 scope는 고정 authority 경계. 장초/장중 등 하위 시간 구간은 train에서 선택·고정하고 다른 시장 정책을 빌리지 않음 |
| 가격·호가단위 | 현재 유효 가격, 해당 상품/시장 규칙의 tick, tick/price 비율, 가격대 | 명목가격과 tick 비율을 별도 보존. 현재 LT_5BP/5_TO_10BP/GE_10BP는 seed 분류이며 영구 최적 경계 아님. tick rule/version과 가격 변환 기준을 보존 |
| 유동성·거래활동 | 과거 종료된 window의 거래대금·체결 빈도, 실제 호가금액/깊이, spread ticks/bp, 매수·매도 체결 비율 | 창 길이·단위·coverage·거래 공백 처리를 schema에 고정. 학습할 fillability 임계치의 pass/fail을 다시 유형 입력으로 쓰지 않고 원시 수치를 사용 |
| 변동성 | 완료봉 수익률 변동·가격 범위, window와 관측 개수 | 계산식·완료봉 전용·연속성·최소 입력 수를 고정. 평가 이후 종가나 당일 최종 고저가를 가져오지 않음 |
| 시가총액·유통 규모 | 공식/기존 검증 metadata의 값·단위·기준일·실제 알게 된 시각, 유통주식/유통시총은 있을 때만 | `effective_at`과 `known_at`이 평가 이전인 자료만 as-of join. 기업행사·주식수 변경·수정주가/실가격 혼합을 검증. 역사 근거 없으면 UNKNOWN이며 현재 latest를 소급하지 않음 |
| 현재 흐름·상태 | 완료봉 추세/눌림/반등의 원시 수익률·slope·낙폭, 현재 tape/회복·재확인 이력 | action이나 candidate 위험등급이 아니라 입력 시점의 관측량에서 선택. 상태 feature kernel/version·필요한 prior revision을 정책에 결속 |

가격대·시가총액을 모두 필수 분할하지 않는다. `분할하지 않음`도 후보이며 실제 유동성과 변동성을 함께 평가한 뒤 비용 후 개선이 있는 구분을 선택한다. 업종 등 추가 metadata도 원천과 분류 이득이 확인될 때만 같은 registry에 등록한다. 단순 종목명·사후 수익률로 유형을 만들지 않는다.

물량 기준은 원 수량뿐 아니라 가격을 곱한 체결금액, 같은 과거 window의 거래량 대비 순매수, 호가금액 대비 체결금액 등의 정규화 후보를 함께 검토한다. 분모/창/단위와 0·결손 처리를 명시하고 ratio와 주수 값을 같은 threshold 필드에 섞지 않는다. feature 정의 변경은 새 feature version이며 구형 raw의 지원범위를 검증한다.

시가총액 metadata의 유효기간은 quote의 millisecond freshness와 별도다. 기존 검증된 metadata 갱신·기업행사 계약으로 판정하고 임의 TTL을 새로 강제하지 않는다. 유통주식이 없다는 이유로 전체 main 판정을 차단하거나 실시간 API 조회를 추가하지 않는다. 실제 Kiwoom 요청/응답/단위 해석을 수정하는 구현이 필요하면 해당 부분은 공식 reference gate를 선행한다.

### 4.2 하나의 기본 정책에 담을 내용

기존 machine bundle 안에 다음을 결속한다. 별도 유형별 publisher나 종목별 정책 파일군을 만들지 않는다.

| 내용 | 필수 의미 |
| --- | --- |
| feature contract | feature schema/kernel, 정규화 단위·window·as-of·필수/선택 입력, metadata provenance와 missing 처리 |
| selector | scope별 분기 tree, 사용 feature와 경계/비교 부호, child 우선순서, UNKNOWN 경로, leaf/parent reference, 필요 시 상태 전환 조건 |
| strategy profiles | root/유형/상태 leaf별 §4 전략 임계치 전체 조합. 허용된 종목 보정도 이 안에 포함. 유동성3축에 한정하지 않음 |
| inheritance | scope 기본값→유형/상태 child→검증된 종목 보정의 parent 관계와 missing 시 상위 선택. 부분 override는 발행 시 완전한 effective vector로 materialize해 저장 |
| evidence | 분류·threshold를 함께 선택한 train/holdout, 전체 모집단 및 유형별 기여/coverage, 미지원 영역과 부모 정책 사용, feature/selector/profile hash |

범위가 다른 정책을 parent로 참조하지 않는다. 모든 referenced node/profile은 동일 immutable generation 안에 있어야 하며 cycle/dangling reference/동순위 충돌·역전된 구간을 거부한다. v1은 기존 의미의 단일 root profile로 해석하고 v2의 필드 누락을 v1 default로 조용히 처리하지 않는다. 상위에서 상속된 각 좌표의 출처도 receipt로 추적할 수 있어야 한다.

### 4.3 공유 selector와 기본값 선택

1. 고정 source/실행 안전 및 등록 scope를 확인한 뒤 그 scope의 root를 선택한다. 공통 기본값은 시장·세션별로 검증된 값이며 전 시장의 숫자 하나를 강제하지 않는다.
2. 같은 frozen 입력에서 feature를 한 번 계산하고 정책 tree를 root→child로 순회한다. 유효한 값에는 경계 포함/제외와 child 순서를 명시하여 한 경로만 선택한다. label 문자열 정렬이나 유리한 profile의 사후 선택은 금지한다.
3. 정상적인 선택 metadata 결손·지원범위 밖 값이면 학습·재생에서 검증한 UNKNOWN/parent 경로를 따른다. 예를 들어 시가총액이 없으면 시가총액을 쓰지 않는 호환 parent로 돌아간다. 해시 손상·단위 충돌·route 불일치·필수 시장자료 결손은 정상 UNKNOWN으로 숨기지 않고 해당 safety/source 계약으로 차단한다.
4. optional symbol 보정은 검증된 child의 일부다. 데이터가 적으면 train에서 결정한 shrinkage로 parent에 가깝게 하거나 parent를 그대로 쓴다. runtime이 최근 손익을 보고 보정 가중치를 즉석 학습하지 않는다. 보정되지 않은 좌표는 검증된 parent 값을 상속한다.
5. 선택된 완전한 threshold vector로 전략 facts와 최종 action을 계산한다. `ENTER_NOW`를 내는 profile을 찾을 때까지 다음 leaf를 시험하는 방식은 금지한다. 유형이 달라도 매번 기존 안전 조건이 우선이다.
6. 각 fresh revision에서는 그때의 유형·상태를 다시 계산한다. 하나의 frozen frame 안에서 선택한 leaf를 중간에 바꾸지 않는다. 구간 경계의 왕복을 억제하는 hysteresis/최소 지속조건을 도입한다면 그 값·상태 이력도 후보 정책과 replay에 포함하며 숨은 런타임 상수로 추가하지 않는다.
7. 재확인 때 leaf가 달라지면 parent attempt·revision·이전/새 leaf·변경 이유를 기록한다. 이전 leaf의 AI 응답·가격/수량 준비를 새 판단에 무조건 재사용하지 않고 기존 exact-context 재검증 계약을 따른다. generation 교체와 같은 generation 안의 leaf 전환을 구분하여 중복 주문을 막는다.

최종 단일 receipt는 `bundle/feature/selector hash, type_state inputs 및 as-of, traversed rule IDs, chosen leaf, fallback reason, complete effective thresholds/hash, action`을 포함한다. 장후 replay와 live가 동일 함수로 이 receipt를 만들고 불일치는 정책 전달 결함이다.

## 5. raw에서 action까지 하나의 공유 평가 함수

기존 `entry_setup_evidence` 안에 main 전용의 버전 있는 평가 진입점을 두거나 기존 함수 인자를 확장한다. 역할은 다음과 같다. 신규 파일이 필요하다면 먼저 location gate를 적용하며 engine root에 추가하지 않는다.

```text
frozen predecision primitives + effective policy + same-attempt prior state
  -> fixed source/safety admission
  -> shared feature transform + type/state selector + validated parent fallback
  -> one complete effective strategy threshold vector
  -> policy-dependent structure/tape/liquidity/timing facts
  -> all risk facts + counterweights + required recheck predicates
  -> BLOCK | RECHECK | ENTER_NOW + threshold comparison receipt
```

- 원시 facts: 완료봉 OHLCV/종료시각, 호가 가격·금액/잔량, 원 tick 순서·aggressor 근거, 가격반응, 원 수신시각·route/epoch, promotion 이력. 기존 capture/manifest에서 가져오며 평가 시점 이후 값은 label에만 사용한다.
- 기준선 v1은 기존 producer+kernel 결과와 동등해야 한다. v2 seed도 현행 좌표와 의미를 명시하고, 알고리즘 변화가 포함되면 threshold-only 효과와 분리한다. 실패 시 임의 default로 진입하지 않는다.
- `hard_safety_facts`, `strategy_risk_facts`, `confirmation_facts`의 의미를 분리한다. 과거 `hard_blocker` 문자열을 blanket 삭제하거나 unknown blocker를 전략 조건으로 자동 분류하지 않는다.
- 정책 의존 group/flow가 후보 생성과 순환하지 않게 raw 모집단·venue/session·시간순 train/holdout 경계를 고정한다. 후보의 selector가 만드는 유형/leaf 소속은 달라질 수 있으며 그 변경 자체가 평가 대상이다. candidate strategy 판정 결과를 selector 입력으로 되먹이지 않는다. 상태 추출이 설정 가능하면 raw만 입력받는 별도 선행 feature 단계로 버전 결속하고 그 다음에 strategy profile을 선택한다.
- receipt에는 raw/context hash, policy/hash/version, source contract, 각 조건의 observed/operator/threshold/result, 최초·잔여 blocker, action, evaluation revision을 남긴다. 기존 event/case table을 확장하며 중복 로그·새 report를 만들지 않는다.
- 과거 setup만 있고 필요한 raw가 없으면 `unsupported_strategy_replay`다. 자연 v2 capture에서 채울 필드와 회복 불가능한 역사 원천을 구분한다. 원문/구형 라벨과 hash는 보존한다.

## 6. 장후 평가·후보 선정

### 6.1 모집단과 후보가 바꿀 수 있는 범위

기존 natural machine rows와 exact paired rows의 합집합을 source hash·attempt·revision·venue/session으로 대사한다. BLOCK/RECHECK/ENTER_NOW 모두 유지하고 중복 attempt와 동일 기회의 반복평가를 구분한다. SOURCE_INVALID는 census에 남기되 전략 학습에는 제외한다. 날짜 전체 제외는 식별 가능한 row 격리가 불가능한 global 계약 결손일 때만 적용한다.

candidate마다 incumbent/candidate action의 3×3 전이표, 유일 기회 수, 전략 원인별 회복·추가 차단, remaining final guard를 기존 보고서에 출력한다. 최초 진단은 실제 차단 predicate를 바꾼 유한 후보가 action을 바꿀 수 있는지 확인한다. 후보 전체 action 동일은 `no_action_change_in_search_space`이며 `hold_no_edge`가 아니다. 일부 좌표만 비활성인 경우 해당 좌표에 이유를 남긴다.

### 6.2 전체 좌표 조합 탐색과 과적합 방지

1. 등록된 설정 가능한 전략 좌표 전부의 유한 domain으로 constrained joint search 공간을 구성한다. source 미지원 축은 필드와 원인을 명시하고 전체 완료라고 하지 않는다. 서로 다른 전략 family의 3개 이상 좌표 변경도 생성할 수 있어야 하며, 단일좌표/쌍은 초기 탐색 순서일 뿐 후보 자격 제한이 아니다.
2. 기존 calibration owner 안에서 결정적 joint traversal과 checkpoint를 구현한다. 무효 범위/모순 recipe는 제외하고, 동일 전체 action·RECHECK 시간순서·candidate AI context·후단 실행 및 경제성을 만드는 것이 입증된 후보만 중복제거한다. action 수가 같다는 이유로 사실/시점이 다른 후보를 합치지 않는다. 단일좌표에서 이익이 없거나 전환0이라는 이유로 그 좌표의 joint 분기를 자르지 않는다.
3. 처음에는 유망한 조합을 먼저 평가하되 남은 joint frontier를 보존한다. 분기 상한으로 pruning하려면 실제 사용 목적함수의 유효 upper bound를 검증해야 하며, 증명되지 않은 휴리스틱은 순서에만 사용한다. 작은 domain의 완전열거 oracle과 같은 최선 조합이 나오는지 검사한다. 모든 guard를 끄는 candidate나 전략 외 좌표 변경은 없다.
4. calibration에서 종목/날짜별 순서를 포함한 portfolio 결과로 순위를 정한다. 비교 가능한 지원범위에서 비용 후 기대값이 양수인 후보 중 거래일당 순익 개선을 우선하고 paired EV/기존 tail guard를 확인한다. 거의 동률이면 더 단순하고 incumbent에 가까운 조합을 택한다. 각 좌표 변화는 비선형적일 수 있으므로 임의 단조성을 가정하지 않는다.
5. grid/확장 규칙·목적함수·frontier·실행 budget·seed를 hash한다. 예산 소진이면 `search_incomplete`와 explored/pruned/remaining 수를 보존한다. 검증된 최선 후보가 있으면 §6.4를 통과해 적용할 수 있으며 전체 탐색 완료를 새로운 적용 gate로 붙이지 않는다. 이 경우 `best_validated_so_far`로 표시하고 전역 최적이라고 하지 않는다.
6. `domain_optimal`은 선언된 유한 domain을 완전 탐색하거나 유효 pruning으로 닫은 경우만 사용한다. 연속 전체 공간/미관측 시장의 절대 최적 보장은 하지 않는다. 적격 후보가 먼저 나와도 이후 정상 장후 실행에서 남은 범위·새 원천을 계속 평가한다.
7. train에서 후보·domain 확장·상호작용·계층 보정을 고정하고, untouched chronological holdout으로 한 번 확인한다. 실패 후 같은 holdout으로 후보를 계속 골라내지 않는다. 다음 평가에서는 새 독립 날짜/구간을 holdout으로 사용하고 과거 holdout은 train 편입 이력을 남긴다. 미지원 원천과 제외 분모는 동일 정책 비교에서 대사한다.

### 6.3 실행 가능한 기회비용

한 기회에 대해 두 정책의 action과 후속 RECHECK 시퀀스를 당시 입력 순서로 재생한다. RECHECK는 즉시 손익0 또는 즉시 진입으로 치환하지 않는다. 나중 입력에서 조건을 충족하면 그 시점 가격·자금·당시까지의 정보로만 진입을 평가한다. 다음 입력/만료 terminal이 없으면 censored/null이다.

기존 price/sizing/leg/exit/cost owner의 모델을 재사용하되 정책 비교에서는 같은 버전을 고정한다. 새 진입 시점의 정확한 plan이 없으면 나중 실제 주문계획을 과거로 소급하지 않는다. BLOCK의 관측 cache miss는 추가 동기 계좌호출로 메우지 않고, 검증된 당시 자본 증거가 없는 범위를 source gap으로 남긴다.

candidate ENTER에 실제 AI 응답이 없으면 `machine_opportunity_only`다. 현행 compact prompt/model을 고정한 exact candidate context의 승인된 offline replay가 있을 때만 모델 결과를 붙이고 실제 PASS로 바꾸지 않는다. 기존 checkpoint/provider budget을 재사용하며 live 런타임에서 BLOCK을 AI에 호출해 연구자료를 만들지 않는다. unsupported downstream은 기계 연구를 막지 않지만 end-to-end 순익 승격을 막는다.

미체결/no-fill, full/partial fill, holding terminal, 실행가격·수수료·세금·슬리피지·발생 AI 비용·자본 점유를 분리한다. 주문을 내지 않았음이 확인된 actual 노출손익0과 미관측 CF/null은 다르다. future high/MFE/단순 목표가 touch로 체결·이익을 확정하지 않는다.

주 비교식은 동일 유일 기회 모집단 U에서 `ΔEV = mean(net_candidate - net_incumbent)`, 동일 관측 거래일 D에서 `Δdaily_net = sum(net_candidate - net_incumbent) / |D|`다. portfolio/cash 제약을 포함한 시퀀스 결과로 일별 순익을 계산하고 중복 보유/자본 재사용을 금지한다. U/D에는 source-valid 미진입·무기회일·손실일을 보존한다. 미완결 기회는 양쪽 비교에서 동일하게 제외하고 coverage·원인을 노출한다. 결과는 `modeled_*`로 표기하며 actual 실현손익과 합산하지 않는다.

평가 가능한 일부 행에서의 이익을 미지원 행까지 일반화하지 않는다. 후보가 action을 바꾸는 행의 source/downstream 결손이 있으면 해당 scope의 완전한 순익 개선은 미확정이다. 자동 승격에는 기존 coverage 기준과 함께 그 결손이 비교를 편향시키지 않는 지원범위 증명이 필요하다. 지원범위 밖에서 incumbent를 쓰는 제한 정책을 채택하려면 그 분기 자체도 후보의 일부로 고정·재생·검증하고 runtime에 똑같이 전달한다. 데이터를 보고 유리한 종목/날짜만 사후 제외하는 방식은 금지한다.

### 6.4 승격 및 종료 상태

연구와 후보 생성에는 경제성 표본 floor를 두지 않는다. 유효 raw 한 기회부터 계산하고 부족한 부분을 표시한다. **새 기본 정책의 갱신은 아래 하나의 버전 있는 최소 계약을 evaluator→publisher→activation→loader가 공유**한다. 기존 서로 다른 family의 floor를 합산하거나 validator에서 옛10bp/5종목/5일 조건을 다시 요구하지 않는다. 이 변경은 신규 전략 정책의 계약이며 frozen legacy 정책의 과거 증거를 다시 쓰지 않는다.

| 갱신 항목 | 신규 정책의 기준 |
| --- | --- |
| 입력·실행 | 동일 as-of/route의 유효 원천, 변경된 action을 지원하는 비용·AI/price/qty/exit/capital replay. 실제 제출/체결이 미리 있어야 한다는 조건 없음 |
| 최소 독립 지지 | calibration 유일 기회10개, untouched holdout 유일 기회3개 중 action/진입시점이 실제 바뀌는 경제성 비교3개. train/holdout은 서로 다른 source 거래일을 적어도1일씩 포함. 이는 보수적 최소 지지이지 통계적 확증 선언이 아님 |
| 수익성 | 후보의 비용 후 기대값 >0, holdout paired 순익 개선 >0, 동일 관측일 분모의 순익 개선 >0. 계산 정밀도 오차를 제외한 고정 0.10%/1% uplift 하한 없음. 같은 U/D에서 동일한 개선을 중복 gate로 검사하지 않음 |
| 손실·실행 안전 | 기존 hard loss/tail·자본·주문 안전 한도 유지. 변동 지표의 미세 악화를 모두 veto하지 않으며 평균손실/p10/비용 민감도는 기존 명시된 위험 한도와 함께 보고. 모든 날짜/종목/1·3·5·10·20·30·60분 각각 양수 요구 없음 |
| 과적합 | holdout 미사용·기회 독립성·선택 이력 검증. 단일 우연 수익과 과대 집중을 표시하고 특정 symbol/session만 지지하면 그 scope에만 적용. 공통 정책에 충분한 scope 지지가 없으면 범위 밖은 incumbent 유지 |
| 적용 가능성 | 새 schema/kernel 호환, source/policy hash, scope/owner/보호 override 비충돌, 원자적 교체/rollback 가능. 추가 일수 대기·후보별 사용자 재승인·별도 shadow 단계 없음 |

소수 종목의 scoped 정책에 일괄 최소5종목·최소5일·실거래20건을 강제하지 않는다. 표본 부족 scope가 다른 적격 scope의 갱신을 막지 않는다. joint capital 영향은 전체 기본 정책과 함께 비교하여 scope 독립이라는 가정으로 공유 자금을 중복 사용하지 않는다. CI/유의확률·추가 stress 시나리오는 진단으로 보고하며 근거 없이 새 universal 통과 조건으로 쌓지 않는다. 비용·원천·holdout 진위·기존 hard risk를 완화해서 양수를 만들지는 않는다.

종료 상태는 `source_gap`, `unsupported_strategy_replay`, `no_action_change_in_search_space`, `search_incomplete`, `hold_sample`, `unsupported_downstream`, `evaluated_no_edge`, `eligible_candidate`, `incumbent_carried`를 기존 report에 결속한다. input 결손과 실제 경제적 무개선을 혼용하지 않는다.

### 6.5 분류와 임계치 조합의 공동 선택

장후 후보의 단위는 숫자 vector 하나가 아니라 **feature 변환·유형/상태 selector·root/leaf 임계치·상속/UNKNOWN 규칙을 포함한 전체 정책**이다. 현재 공통 정책, 분류 없는 새 공통 조합, 유형·상태별 조합을 같은 raw opportunity union에서 비교한다.

1. calibration에서만 가격/호가단위·유동성·변동성·규모·시간·상태의 분류 경계 후보를 만들고 §6.2의 joint search에 포함한다. tree depth/leaf 수·분기 가능한 feature·종목 보정 허용 범위를 search manifest에 선언한다. 제한된 구조 안의 최적과 무제한 최적을 혼동하지 않는다.
2. root가 먼저 승격되어야 child를 연구할 수 있는 순서를 강제하지 않는다. 공통값·분류 경계·각 leaf 전략 좌표를 함께 바꾸는 조합도 생성한다. 분류만 바꾸거나 개별 leaf만 바꾸면 이익이 없고 둘을 함께 바꾸면 개선되는 사례를 탐색해야 한다.
3. 가격대×시총×유동성×변동성 전체 곱으로 독립 소표본 정책을 자동 생성하지 않는다. `분할 없음`을 항상 포함하고 parent 공유·train에서 고정한 shrinkage·단순한 tree의 동률 우선으로 복잡도를 제어한다. 구조의 제한은 검색 manifest에 공개하며 전역 최적 주장에 숨기지 않는다.
4. calibration에서 선택한 전체 정책을 freeze하고 untouched holdout에서 한 번 재생한다. 유리한 leaf만 holdout을 본 뒤 다시 조합해 발행하지 않는다. §6.4 최소 지지는 기본적으로 전체 비교 정책에 적용하며 모든 leaf에 5종목/5일/실체결 floor를 복제하지 않는다. 새 child의 변경 효과를 지지할 유효 독립 관측이 없으면 parent를 사용하는 candidate를 train에서 정하고 검증한다.
5. 유형별 기회/전환/회복이익/추가손실/미지원/parent 사용을 보고하되 순위는 전체 순익·paired 경제성·기존 위험 한도 기준이다. 일부 대형/고유동성 leaf의 이익으로 다른 leaf의 source gap·위험 한도 위반을 덮지 않는다. 각 leaf가 모든 날짜에서 양수여야 하는 새 gate도 만들지 않는다.
6. 하나의 기회는 실제 selector가 택한 경로에서 한 번만 계수한다. 시간에 따른 유형 전환, RECHECK 지연, 동시 종목의 자본 경쟁, AI/가격/수량/exit 비용을 전체 정책의 event 순서로 재생한다. 겹치는 그룹별 평균 EV를 더해 전체 이익으로 표시하지 않는다.
7. source-valid UNKNOWN/parent 사용도 평가 분모에 남긴다. 새로운 분류에 필요한 metadata가 없어졌을 때의 경로까지 검증하고 발행한다. 지원되지 않는 branch는 incumbent/parent 유지로 표현하며 한 축의 metadata 결손으로 다른 지원된 축의 학습을 중단하지 않는다.

완료 산출물은 기존 main report의 `common_vs_typed_policy` 비교와 단일 후보 bundle이다. 실제 live에 적용하지 않는 독립 shadow/report 축은 만들지 않는다. grouping cache도 feature/selector/profile 조합의 hash에 종속시키고, 최초 구형 그룹을 모든 후보가 공유하지 않게 한다.

## 7. 장중 기본 정책 적용·다음 적격 정책까지 승계

기존 `mechanistic_entry_policy` bundle 안의 machine policy를 버전 확장한다. 새 env 임계치나 두 번째 publisher를 만들지 않는다.

| 계약 | 필수 내용 |
| --- | --- |
| 정책 본문 | §4.2 feature/selector tree·root/leaf 전체 strategy profiles·상속/UNKNOWN 처리·복합 recipe·단위/범위·fixed guard contract·schema/kernel version |
| 적용 범위 | venue/session/stage와 기존 scope authority. 다른 시장의 최적값 상속 금지 |
| lineage | incumbent parent hash, source manifest/as-of, candidate grid hash, train/holdout 기간·소비 영수증, 경제성/검증 hash, evaluated_at/validated_at/effective_from, 원 source 날짜와 적용 날짜 분리 |
| 호환성 | 구형 v1은 기존 의미로 읽기. 새 필드 무시/unknown version의 default 통과 금지. 런타임 최소 지원 버전 명시 |
| receipt | 선택·carry 사유, policy/feature/selector/profile hash·kernel version·release/PID, attempt/revision/source hash, 실제 type/state·leaf·parent 경로와 effective thresholds |

1. 구현 리뷰·targeted validation이 닫히면 기존 full calibration CLI로 frozen 원천을 평가한다. 기존 정상 장후는 계속 사용하며 최초 검증 실행이 장중 끝나더라도 다음 PREOPEN까지 기다리지 않는다. 평가는 실행 시점까지 완료·성숙한 source만 사용하고 적용은 검증 종료 이후 시각부터다. compact-only writer가 main 평가를 생략/덮어쓰지 못한다.
2. 같은 publisher/validator가 적격 후보를 immutable generation으로 발행한다. `search_incomplete`여도 독립 holdout을 통과한 best-so-far는 적용 가능하다. 현행 `next_target(publication)==target_date` 전용 검사와 날짜 파일 우선 선택은 v2 effective-time 계약으로 버전 분기한다. 과거 source 날짜를 오늘로 조작하지 않는다.
3. 기존 정책 저장소 안의 승인된 current generation 선택을 확장한다. candidate 작성→전체 검증→현재 parent와 CAS 대조→원자적 activation receipt 갱신 순서다. generation/body/source 보관과 디스크 영속성, crash 전후 current/previous 정합성을 검증한다. 두 평가가 경쟁하면 낡은 parent 기반 후보는 새 incumbent와 재검증하고 마지막 writer가 무조건 이기지 않게 한다.
4. main loader는 파일 세대 변경을 기존 평가 경계에서 감지해 immutable 정책을 reload한다. 새 attempt의 정책을 먼저 고른 후 raw에서 facts를 계산한다. 기존 장중 작업·다른 owner와 충돌하지 않으면 그 시각부터 **새 기본 정책**이다. 시험용 별도 진입 lane이나 원복 타이머가 아니다. 여러 전략 좌표의 하나의 검증된 bundle 교체를 이번 사용자 지시로 허용하며, 일반 수동 단일축 override 제한을 재승인 사유로 사용하지 않는다.
5. WATCHING sync/async·RECHECK·pre-submit이 모두 명시적 generation을 사용한다. 이미 평가 중인 attempt는 원 generation으로 끝내고 다음 fresh revision/attempt부터 새 정책을 사용한다. source/parent revision을 보존하며 단순 파일 변경 때문에 이미 종료된 시도를 재주문하지 않는다. 이전 generation의 inflight 평가에는 기존 deadline과 최종 guard가 계속 적용된다.
6. ENTER_NOW만 고정된 compact AI·price/sizing·최종 guard로 진행한다. 새 정책을 AI가 덮거나 BLOCK/RECHECK를 임의 승격하지 못한다. 최신 입력 재판정 실패면 제출하지 않는다. 보조 AI policy가 나중에 바뀌어도 current machine generation을 오래된 dated bundle로 되돌리지 않으며 결합된 부모/경제성 계약을 검증한다.
7. 적용 receipt에는 before/after hash, activation 시각·scope·source cutoff·검증 근거, 실제 release/PID 및 첫 소비 attempt, rollback generation을 남긴다. 테스트 성공·파일 쓰기만으로 PID 적용 완료라 하지 않는다. 최초 적용은 기존 main 배포 경로로 호환 코드를 인계하고 이후 정책 교체는 reload한다.
8. 다음 거래일 PREOPEN·프로세스 재시작도 같은 승인 current generation을 기본값으로 읽는다. 날짜별 파일은 source/적용 인계 projection이며 정책 선택의 더 높은 권한이 아니다. 다음 후보 없음/실패/hold_sample/장후 미완료/하루 경과/주말·휴장/재시작 때문에 초기값 또는 과거 dated 정책으로 원복하지 않는다. 매일 새 경제성 승격을 통과해야 기존 정책을 유지하는 조건도 없다.
9. 정책 수명은 `until_superseded`다. 다음 **적격·검증·활성화 완료 정책** 또는 명시적 안전 rollback/운영자 변경까지 승계한다. 단순 candidate 파일 발생·갱신 mtime은 교체 사유가 아니다. 전략의 지속 승계와 개별 quote/account/source의 freshness는 별개이며 후자는 매 결정마다 재검증한다. 적용 당시 scope와 별도 operator lock 만료는 그대로 따른다.
10. 새 후보 손상/미지원이면 activation을 거부하고 유효 current를 유지하며 실패를 표시한다. 이미 활성인 current 자체의 hash/참조/호환성 손상이면 조용히 날짜 fallback하지 않고 해당 진입을 차단하거나 검증된 previous generation으로 명시적 안전 rollback한다. 파일 없음과 손상을 구분한다. 열린 포지션의 exit/custody는 초기진입 정책 교체로 바꾸지 않는다.

초기 적용 뒤에는 existing post-apply 관측으로 선택된 조건의 실제 전환·최종 차단·체결·비용 성과를 추적한다. 자연 표본이 없다고 기본 정책을 해제하지 않으며, 실제 위험·원천·계약 회귀의 rollback은 기존 안전 계약대로 한다. 장후 main report→runtime summary→strict verifier에는 현재 generation, 새 candidate 실패, 평가 완료를 별도 필드로 전달해 carry와 장후 DONE을 혼동하지 않는다.

캐시 key와 재사용 검증에는 raw/source semantic version, frozen input hash, incumbent/candidate 전체 정책 hash, 전략 kernel, scope, auxiliary prompt, price/sizing/exit/cost 계약, 평가 window 및 holdout을 포함한다. 새 임계치가 변해도 옛 fixed facts/outcome cache를 재사용하는 silent failure를 테스트한다. 동일 source에서 정책 독립 원시 파싱만 공유하고 후보 의존 결과는 구분한다.

원자적 적용·지속 승계 단위도 selector와 모든 profile을 포함한 bundle 전체다. 분류 경계만 신세대이고 threshold는 구세대인 조합은 허용하지 않는다. 하나의 bundle이 종목/시점에 따라 다른 검증된 leaf를 선택하는 것은 정책 교체가 아니다. reload/PREOPEN/재시작 이후에도 동일한 frozen 입력이면 같은 leaf·effective vector를 선택해야 한다. 정상적인 새 시장 입력에 따른 상태 변화는 같은 selector 계약에 따라 다시 평가한다.

## 8. 구현 작업 순서와 산출물

단계 번호는 이 계획 내부 순서이며 새로운 checklist owner를 만들지 않는다. 전 단계의 자연 경제성을 기다릴 필요 없이 의존 계약이 확정되면 다음 구현을 진행한다.

| 단계 | 기존 수정 위치 | 산출물·완료 시험 |
| --- | --- | --- |
| P0 조건 전수 연결·계약 고정 | ai_decision_quality, entry_candle_context, entry_setup_evidence, 현행 metadata source/정책 | main 비교문→정책좌표·유형 feature/as-of/단위→selector→후단 guard 표. 시총/유통 원천 지원범위, v1 golden 결과 고정 |
| P1 정책·공유 평가 함수 | entry_setup_evidence의 group/hierarchy/core, ai_decision_quality, entry_candle_context | source/strategy 분리, shared feature/selector·parent 경로·전체 전략 profile, graph/bounds validator, v1 parity·v2 transition |
| P2 원천·revision·replay | 기존 machine capture/ai_decision_trace, sniper_state_handlers, strategy_owner_replay | primitive와 metadata의 exact as-of/known-at 연결, 유형·leaf 전환 receipt, 구형 unsupported, RECHECK 순서·plan/capital 보존 |
| P3 장후 후보·경제성 | ai_action_outcome_calibration, entry_setup_paired_replay_batch 및 기존 owner replay | 분류 경계+공통/유형/상태 조합 joint search, common-vs-typed 전체 replay, 3축 및 분류+임계치 상호작용 oracle, 최소 갱신 계약 |
| P4 발행·검증 | mechanistic_entry_runtime_policy, entry_setup_live_policy, runtime_approval_summary, verify_threshold_cycle_postclose_chain | feature/selector/profile 단일 schema/effective_from·전체 validator, immutable generation/current CAS·실패 보존. 구형 writer 퇴행 방지 |
| P5 런타임 소비 | entry_setup_live_policy, ai_engine_openai, sniper_state_handlers의 실제 호출부 | 장중 원자적 reload→shared selector→effective vector→facts, inflight/revision별 leaf·AI 재검증, PID receipt 및 재시작 승계 |
| P6 운영 연결·반복 리뷰 | 기존 postclose/preopen wrapper와 운영 문서 중 변경된 부분 | review/validation→최초 평가 실행→적격 정책 장중 기본 적용→다음 적격 정책까지 승계→R6. 자연 표본 부재와 적용 여부 분리 |

wrapper 변경이 필요하면 [postclose wrapper](../../deploy/run_threshold_cycle_postclose.sh), [PREOPEN wrapper](../../deploy/run_threshold_cycle_preopen.sh)의 기존 step를 수정한다. 새 정기 실행을 추가하지 않는다. 자동화 규칙을 실제 수정하는 후속 구현에서는 해당 운영 문서와 checklist를 같은 change set으로 갱신한다. 이번 계획 작성은 README/runbook/Plan Rebase/prompt/AGENTS를 변경하지 않는다.

## 9. 필수 회귀와 완료 판정

기존 테스트 파일을 확장한다. `test_entry_setup_evidence`, `test_entry_candle_context`, `test_ai_action_outcome_calibration`, `test_strategy_owner_replay`, `test_entry_setup_paired_replay_batch`, `test_mechanistic_entry_runtime_policy`, `test_entry_setup_live_policy`, source-quality/threshold wrapper 테스트 중 실제 영향 부분을 선택한다. provider/계좌/실주문은 mock 또는 보존 fixture를 사용한다.

1. 과열·매도벽·돌파·분산의 각 source-valid fixture에서 baseline BLOCK, bounded candidate ENTER_NOW를 재현한다. 다른 필수 진입 근거와 최종 guard는 충족한 fixture로 만들고 future label은 판정 입력에서 제거한다. 대량매도는 순서가 있는 회복 후에만 전환한다.
2. 거래량/미세확인/타이밍의 baseline RECHECK→candidate ENTER_NOW와, 위험한 incumbent ENTER_NOW→candidate 미진입을 검증한다. 여러 blocker가 남으면 전환 불가이며 첫 blocker만 제거해 성공 처리하지 않는다.
3. 모든 전략 좌표를 완화해도 source-invalid/stale/crossed/route/epoch/계좌·주문 안전 위반이 통과하지 않는다. guard가 통과할 수 없는 candidate의 end-to-end 경제성은 회복 이익으로 기록하지 않는다.
4. 당시 raw를 같게 둔 online/offline의 facts·risk·action·비교 receipt가 일치한다. 경계값 직전/같음/직후, 퍼센트/bp, 음수 비교, nullable 필드를 확인한다.
5. RECHECK→새 입력→ENTER와 RECHECK→만료를 실제 state 경로로 확인한다. 동일 revision 중복·역순·정책 변경·worker 늦은 결과·final revalidation 실패에 이중 제출0.
6. all-BLOCK이면서 유효 raw/CF가 있는 모집단에서도 후보 생성·평가를 실행한다. source-only 상류 개선과 AI/집행 미지원 상태를 분리한다. actual AI 미호출을 PASS로 합성하지 않는다.
7. 총 BLOCK/RECHECK/ENTER 분모 보존, 같은 기회의 반복 이익 중복0, 회복 이익보다 추가 손실이 큰 후보 탈락, 선택된 진입 평균은 좋지만 전체 일별 순익이 나쁜 후보 탈락을 검증한다.
8. 다음 시점 source를 과거에 소급하거나 다른 route/capital/price/exit를 섞은 사례, partial/미체결/censored/null을 0으로 바꾸는 사례를 거부한다.
9. 전략 좌표 하나만 변경해도 facts/cache/bundle hash가 달라지고 publisher/PREOPEN/runtime이 같은 값을 소비한다. 구형 cache 완료 표시·정책 hash만 맞는 낡은 receipt로 성공하지 않는다.
10. 미지원 schema, 범위 밖 값, 보호키 주입, 다른 scope/적용시각/parent, holdout 재사용, 평가가 끝나지 않은 후보의 적용을 거부한다. 전체 search 미완료와 개별 후보 검증 미완료는 구분한다. v1·기존 widget/episode/holding 소비의 golden parity를 보존한다.
11. 단일축과 모든 2축 변경은 진입0이지만 서로 다른 family의 3축 이상을 함께 변경하면 source-valid ENTER_NOW와 양수 순익이 생기는 fixture를 필수로 둔다. joint search가 이를 찾고 소규모 완전열거의 최선 조합과 일치해야 한다. 시작 grid 밖의 유효 경계 확장, 순위가 낮은 좌표의 joint 기여, 비단조 목적함수도 검사한다.
12. search 중단에도 독립 holdout을 통과한 best-so-far는 적용되고 미검증 후보는 적용되지 않는다. 다음 frontier 재개가 같은 holdout을 재선택에 오용하지 않아야 한다. 같은 action이지만 AI 입력·재확인 시점이 다른 후보를 잘못 중복제거하지 않는다.
13. source가 유효한 all-BLOCK baseline에서 새 정책의 비용 후 소액 양수·paired 개선이 최소 지지 계약을 만족하면 기존10bp/5종목/5일/실체결 floor 때문에 거부되지 않는다. 실제 손실 후보·비용 누락·holdout 미래 누출은 여전히 거부한다. evaluator/publisher/activation/loader의 동일 판정을 검사한다.
14. 장중 generation 전환→첫 소비 receipt→자정→다음 PREOPEN→주말/재시작→신규 후보 없음/실패까지 같은 기본 정책이 승계된다. 새 적격 generation만 원자적으로 교체하고 단순 파일 생성/날짜/compact-only 정책으로 되돌리지 않는다.
15. 동시 publisher parent 충돌, 원자교체 중 crash, 새 candidate 손상과 활성 current 손상의 구분, inflight 구세대/새 attempt 신세대 분리, rollback과 기존 holding custody 보존을 검증한다.
16. 가격/tick 비율·유동성·변동성·규모·시간·상태가 다른 source-valid fixture에서 각각 다른 leaf/전략 조합이 선택되고 online/offline receipt가 일치한다. threshold 숫자만 분리하고 selector를 runtime에 연결하지 않으면 실패한다.
17. 공통 정책은 이익이 없고 유형 경계와 3축 이상 전략 조합을 함께 변경하면 개선되는 소규모 fixture를 완전열거와 비교한다. 유형 분할만/임계치만 검색하는 구현, leaf별 중복 기회/자본 계수, holdout 후 유리한 leaf 재조합을 거부한다.
18. 시총 metadata가 당시 미공개/기준일 미래/단위 오류/기업행사 불일치인 경우 최신 DB 소급을 거부한다. 정상 UNKNOWN은 검증된 parent로, 필수 source 충돌은 차단으로 간다. optional metadata 결손이 전체 학습/진입 blanket block이 되지 않는다.
19. 구간 경계의 같음/직전/직후, 다중 rule 충돌, 순환/없는 parent, 다른 scope parent, 불완전 effective vector, 구형 hierarchy가 새 필드를 무시하는 경우를 거부한다. 사용되는 유형 전체에 추가 표본 floor를 중복 부과하지 않는다.
20. fresh revision에서 leaf가 바뀐 재확인, 정책 reload 직전 worker, 같은 selector의 재시작 후 복원, 선택/threshold 세대 혼합, 이전 leaf AI 응답의 잘못된 재사용을 검사한다. 안전 guard와 중복주문 불변을 확인한다.

통합 validation은 마지막 수정의 영향 합집합으로 실행하고 Python compile, wrapper 변경 시 bash -n, git diff --check를 수행한다. 문서 변경에는 print-only parser만 사용한다. 실제 대량 재생성·배포·재기동·자연 수용은 테스트와 분리한다.

## 10. 실제 적용 이후 검증과 잔여 결손

기존 direct-family owner가 다음 항목의 owner artifact·blocker·다음 행동·closure test를 관리한다.

| 상태 | 필요한 증거 | 다음 행동/종료 조건 |
| --- | --- | --- |
| 구현 완료 | P0–P6 코드/targeted validation, 실제 BLOCK/RECHECK 전환 fixture | 구현 리뷰 종료. 자연 양수 EV를 코드 통과로 대체하지 않음 |
| source 미지원 | required primitive/route/as-of/terminal gap과 정확한 row 분모 | 기존 capture/consumer 수리 또는 다음 자연 원천. 동일 불완전 replay 반복 금지 |
| 후보 평가 완료 | common-vs-typed 전체 정책, 유형/leaf별 기여와 joint 전이표, 비용·holdout·daily net, eligible/hold/frontier | 분류+임계치+기본값을 함께 검증한 best-so-far부터 발행. domain 최적과 구분 |
| 정책/장중 activation·PREOPEN 완료 | effective_from/current generation·검증·release 전달 receipt | 장중 PID 소비와 다음 PREOPEN/재시작의 같은 기본값 승계 확인 |
| PID 소비 완료 | 실제 cwd/release/PID와 새 attempt의 source/policy/type-state/leaf/effective-threshold/action receipt | 실제 선택 조합과 후단 차단 확인. 자연 미발생 유형은 미관측으로 별도 보존 |
| 자연 수용 | 조건 전환→AI→최종 guard→broker receipt 또는 정확한 미제출 사유 | 제출1건으로 전체 병목 해결 선언하지 않음 |
| 경제성 수용 | 적용 버전별 real full/partial/COMPLETED+valid profit_rate, 비용·rolling/cumulative 및 모델 비교 | 실제 비용 후 개선 여부 판정. 자연 기회 부재는 pending이며 완료 아님 |

이 계획은 실제 미진입 손실 중 어떤 전략 조건의 비중이 가장 큰지 확정하지 않는다. 첫 장후 평가에서 그 순위를 기존 case table로 산출하되 우선순위가 낮다는 이유로 등록된 축을 영구 미연결로 두지 않는다. 근거 없는 최적값·예상 수익률·완료 날짜를 약속하지 않는다.

## 11. 이번 문서 검증 기록

초기 문서 자기리뷰에서는 upstream 고정 facts·동시 blocker·정책 의존 group 순환·부분 source 지지·cache 경로를 보완했다. 후속 요구사항 점검에서 joint search 범위·임의 grid 고정·과도한 기존 floor 상속·PREOPEN 전용 적용/승계의 네 결함을 확인하여 §1.1 및 §4/§6/§7/회귀15개에 반영했다. 초기 문서 PASS를 전체 조합 탐색·장중 지속 적용의 완료 근거로 재사용하지 않는다.

유형·상태 후속 보완에서는 §4.1–§4.3/§6.5와 P0–P5/회귀16–20을 추가했다. 분류 결과를 후보에 무관하게 고정하던 문구를 수정하고, raw/train/holdout만 고정한 상태에서 selector와 전략 조합을 함께 학습하도록 정합화했다. selector→profile 순환·시총 latest 소급·UNKNOWN과 source 손상 혼동·leaf별 gate 과증식·세대 혼합을 자기리뷰에서 점검했다. 장후 산출과 실제 runtime의 동일 전체 정책 소비를 공동 완료 조건으로 둔다.

- 상대링크7개 유효, 당일 기존 OPEN stable owner1개 유지. 체크리스트의 기존 변경·역사 acceptance는 보존했다.
- print-only backlog parser: exit0, 전체29 tasks 및 `DirectFamilySourceRepairMainMechanisticEntry` parsed owner1개 확인.
- `git diff --check`와 새 문서의 whitespace 검사 통과. 문서 전용 작업이므로 pytest/compile/거래 suite·Provider/API·보고서 재생성·외부 sync·정책/env 변경·배포/재기동은 미실행이다.
- 실제 잔여는 P0–P6 구현, 원천 지원범위, 평가 실행·검증된 후보 생성, 장중 기본 적용/승계와 실제 PID 소비 및 자연 비용 후 성과다. 탐색 시작값 자체는 최적값이 아니며, 사용자 적용 지시는 §6.4를 통과한 결과에 대한 것이다.
