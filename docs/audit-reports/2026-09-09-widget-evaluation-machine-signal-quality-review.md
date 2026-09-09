# Widget evaluation / Samsung·low-price 신호 품질 점검과 다음 작업

검토일: `2026-09-09 KST`, 운영 관찰 `15:46~15:48`. 범위: 읽기 전용 점검·개선작업 도출 및 기록. 코드 구현, 정책 publish, 주문/계좌 호출, PID 변경, 장후 재생성은 실행하지 않았다. 아래 F 번호는 이 문서의 finding 번호이며 producer native recommendation/workorder ID가 아니다.

## 1. 판정

자동 실행·기존 정책 소비 경로는 존재한다. 그러나 **원래 신호 선택의 품질, 확인 지연, 주문 실행, 출구 효과를 분리하여 현재 정책보다 비용 후 작은 수익을 자주 확보하는지 입증하는 수준은 미완성**이다. 우선순위는 임계값 일괄 완화가 아니라 `실현 경제성/정책 cohort 정정 → exact signal/order 대사 → 동일 신호의 확인·출구 분리 평가 → 불필요한 대기 gate 검토`다.

기존 #14/#15 subset 승격 폐기, #74 뒤 실행 순서, 기존 entry timing 공통 계산 수리는 유지한다. 새로 입증된 집계·판단 근거 결손만 재개하며, 표본 부족만으로 완료된 수리를 다시 열지 않는다. 별도 진행 중인 적응형 청산 구현을 이 리뷰로 완료 처리하지 않는다.

## 2. 목적과 자동화 대사

| 기존 owner | 목적 / 현재 연결 | 이번 판정 |
| --- | --- | --- |
| `widget_advisory_calibration` | 삼성·두산·한화의 10분 기회 결과로 10초 확인 횟수 2/3 결정 → dated advisory loader → collector | 자동. 단, 삼성 live가 최종 advisory state를 소비하므로 표시만의 변화로 해석할 수 없음(F3). |
| `widget_auto_trade_policy_calibration` | 관찰 신호에서 추가 leg·target·cutoff·cooldown·횟수 후보 재현 → 다음 날짜 policy → trader loader | 자동. 실행 실패 veto와 40일 연구 조건이 존재. actual execution과 replay는 별개(F2/F4/F5). |
| `widget_symbol_signal_policy_research` | 4개 별도 종목의 completed KRX 분봉에서 setup→reclaim→exit 연구; calibration/holdout 분리 | source-only 연구. 기존 신호·timing·target의 독립 증분 비교는 없음(F4). |
| `widget_symbol_runtime_policy` | 위 연구의 검증된 후보 → exact-date policy → collector/trader loader | 자동. 일반 3종목 calibration의 execution-quality veto를 이 4종목 bridge가 소비하는 연결은 없음(F2). 일반 runtime broker/custody guard가 없다는 뜻은 아님. |
| #14 `samsung_machine_entry_tuning` | actual policy·연속 적용 cohort·leg/청산 결과 감사; 신규 confirmation은 기존 entry timing owner로 전달 | #74 final audit 뒤 자동 실행. baseline 유지 및 적용된 legacy 축의 제한된 unwind 외에는 독자 신규 승격하지 않음. |
| #15 `low_price_two_leg_tuning` | 실제 profile·두 leg 결과와 applied policy 감사/유지; 기존 축 replay는 expanded research로 전달 | #74 뒤 자동. subset `ready=false` 유지. 누적 집계의 정책/경제성 분리 결함은 F1. |

설치된 `korstockscan-samsung-widget-evaluation.service`의 ExecStart는 `deploy/run_widget_evaluation.sh`. 순서는 advisory → auto-trade → EOD terminal wait → symbol research → runtime policy다. journal의 source9/8 최신 terminal은 **9/8 22:13:05 성공**, EOD는 21:00:02에 확인했다. service의 현재 `Result=success`만으로 판정하지 않고 journal과 네 산출물을 함께 대사했다. 9/9 timer active/다음20:10이므로 오늘 산출물은 아직 `not_yet_due`다.

최근 완료 3거래일의 auto-trade 산출물:

| Source date | runtime-ready session / carry | 삼성 accepted order 이벤트 / failure 이벤트 | 두산·한화 qualified dates |
| --- | --- | --- | --- |
| 9/4 | 3 / 3 | 8 / 0 | 15 / 15 |
| 9/7 | 3 / 3 | 4 / 0 | 15 / 15 |
| 9/8 | 2 / 2 | 9 / 4 | 15 / 16 |

위 order 수는 BUY/SELL 포함 이벤트 수이지 신규 진입 수가 아니다. 9/8 삼성은 BUY4/SELL5개의 고유 주문번호다. target9/9 실제 policy는 삼성 NXT 두 세션 carry, 삼성 KRX `execution_quality_safety_veto`, 두산·한화 `research_accumulation_incomplete`; symbol bridge는 제주반도체080220만 선택했다. source9/8 제주 재현 EV는 calibration `+0.295484%`, holdout `+0.206681%`(22/10 episode), 선택 target100bps다. 이는 체결 보장 또는 실제 순익이 아니다.

9/9 `widget_signal_auto_trade_state.json`의 15:46:12 cycle은 source9/8→target9/9 policy ID와 삼성 NXT/080220 KRX의 policy/runtime session 목록을 기록한다. startup receipt는 PID15090, 07:58:05, `startup_before_first_cycle`, `current_policy_consumption_verified=false`다. 따라서 **시작 로드+후속 state 기록은 있으나 exact signal별 실제 소비·체결·순익까지 검증했다는 판정은 하지 않는다**.

## 3. 발견사항과 보완안

### F1 — P1: #15의 현재 정책 성과와 실현 EV가 분리되지 않음

근거: `low_price_two_leg_tuning.py::_aggregate`는 완료 broker PnL을 모든 attempted leg의 예정 가격×수량으로 나눈 값을 `notional_weighted_ev_pct`로 표시한다. broker-priced completion이 없어도 attempted notional이 있으면 `0.0`이다. 실제 source9/8 누적 `sk_eternix_midday`는 완료2 leg가 모두 `configured_target_price_proxy`, broker-priced0인데 EV0.0이다. `kakao_midday`도 broker-priced0/HELD2에서 EV0.0이다. 순수 NO_FILL의 실현 cashflow0 자체는 가능하지만 **미관측 청산 EV/미해결 손익0과 혼용하면 안 된다**.

또한 `build_report`는 profile별 모든 과거 row를 `_aggregate`에 투입하고 현재 연속 applied cohort를 분리하지 않는다. `cj_cgv_late_morning`은 8/24 lookback15/target2의 COMPLETE2와 8/26 lookback45/target4, 9/1·9/4·9/7 lookback15/target4의 NO_FILL을 동일 누적값에 합친다. 전역 정책 hash 변화만이 아니라 실제 해당 profile의 매개변수 변화가 확인된다. #14는 이와 달리 현재 정책 cohort와 attempted-notional 진단을 이미 구분한다.

보완: #14의 계약을 재사용해 `archive/all-version audit`, `same-profile semantic policy cohort`, `contiguous post-apply epoch`를 분리한다. realized EV는 유효 완료 broker 체결금액 분모만 사용하고, 시도금액 수익률·NO_FILL 현금흐름·target proxy·실비용/고정비용 추정·미해결 경제성을 별도 필드로 둔다. 전역 hash가 바뀌어도 해당 profile 값이 같으면 불필요하게 표본을 초기화하지 않는다. 관측없는 realized EV는 null+reason이다.

완료조건: 위 두 실제 profile 및 `전부 NO_FILL / HELD / proxy-only / full·partial / 수동청산 / A→B→A 정책` 회귀에서 경제성·표본·cohort가 구분되고 report→기존 candidate/summary consumer까지 단위·null 계약이 유지된다. 기존 carry-only 권한은 변하지 않는다.

### F2 — P1: 실행품질이 exact incident·복구보다 날짜별 이벤트 합계에 머묾

근거: `_load_execution_quality`는 source-date event 파일 하나의 event_type을 합산한다. 9/8 15:22:08/13/18 삼성 `TAKE_PROFIT_SELL` 같은 parent/target 요청의 실패3회(return20)와 15:22:19 terminal1회를 failure4로 집계한다. 네 번의 독립 진입 실패가 아니다. 해당 episode의 이후 수동 부분청산·잔여 custody 기록은 별도 owner에 있으나 calibration은 이를 exact recovery terminal로 접합하지 않는다. 날짜를 넘겨 파일에 실패가 없으면 이 함수는 PASS를 반환하므로 이것만으로 과거 incident 복구를 입증할 수도 없다. 현재 veto를 임의 해제할 근거는 없다.

일반 calibration은 이 veto를 `build_policy`에서 사용한다. 반면 4종목 symbol bridge의 `build_policy/_validated_selected_policy`는 research/schema/hash/경제성만 읽는다. 별도 branch에는 같은 owner의 실제 실패를 다음 policy selection에 전달하는 공통 입력이 없다. 실제 080220 장애 발생을 주장하는 것이 아니라 코드상 handoff 결손이다.

보완: owner/symbol/venue/session/policy/parent-signal/attempt/order-role/order-number로 `signal→confirmation→submit→receipt→full/partial fill→terminal`을 연결한다. BUY/scale-in/target SELL/cancel, retry 이벤트/고유 incident, 정상 WAIT·NO_FILL/실패/원천결손을 분리한다. 해결된 incident는 exact broker/custody receipt로만 종결하고 미해결은 다음 source일까지 유지한다. 기존 collector·runtime·events를 소비하며 새로운 주문 authority나 중복 매매 owner를 만들지 않는다. 같은 source-only incident contract를 두 widget policy branch에 연결한다.

완료조건: 9/8 사례가 BUY4·SELL5와 목표매도 incident1/실패 submit attempt3/terminal1로 설명되고, 최초 시도와 재시도·미해결·부분복구·완전복구·다음 날짜 무이벤트·다른 session/owner 반례가 각각 올바르게 분리된다. 보고서 진단 수리에 실체결/양수 EV floor를 추가하지 않는다. veto 동작 변경은 별도 영향 검토 후 기존 안전 범위에서만 진행한다.

### F3 — P1: 2회/3회 확인의 효과와 원래 신호 품질이 혼합됨

근거: advisory calibration은 이미 확정된 신호의 10분 `target_first|adverse_first`만 모아 평균 proxy 부호로 2/3을 결정한다. 같은 raw 기회에서 2회와 3회의 선택·지연·누락을 비교하지 않는다. 9/8 삼성 KRX 58 decisive 결과, proxy `-0.402057%`로 3회 유지다. 목표0.5%(삼성)/1.0%(두산·한화)와 adverse 양쪽에 모두 도달하지 않은 작은 움직임은 decisive 입력에서 제외된다. 이런 미도달을 실제 손실/기회 부재로 판정할 수 없다.

메모리 반례: 동일 ENTRY_READY를 t0/t10/t20에 주면 2회는 `WATCH/ENTRY_READY/ENTRY_READY`, 3회는 `WATCH/WATCH/ENTRY_READY`다. 삼성은 `event_based=False`이고 trader `_entry_signal`이 `advisory.state`를 소비하므로 10초 차이가 실제 진입 가능 시점에 영향을 준다. `trading_runtime_effect=false`가 표시 전용이라는 설명은 downstream 영향과 불일치한다. 이것이 현재 삼성 KRX의 직접 차단 원인이라는 뜻은 아니다(F2의 policy veto 별도).

보완: raw-state 최초 시각/ID → visible-state 시각·확인 policy → 실제 진입·체결 outcome을 분리한다. 기존 확인 축 2/3만 동일 causal raw episode에서 재현하고 exit/quantity/target을 고정한다. 최초/2회/3회 시점의 executable price와 비용 후 결과, 신호소멸·미체결·추격 악화를 비교한다. 진단용 작은 수익 구간과 미성숙/미도달도 보존하되 MFE를 실현 EV로 대체하지 않는다. producer의 비주문 권한과 downstream signal 영향 metadata를 함께 명시한다.

완료조건: 정상 지속/일시 신호/late·duplicate observation/guard 차단이 분리되고 동일 정책·신호에서 추가 확인의 순증분이 계산된다. 근거 없이 일괄 3→2로 낮추거나 기존 live authority를 확대하지 않는다.

### F4 — P1 목적 결손: 완료 승자 위주의 replay 순위와 신호·target 동시 변경

삼성 auto-trade `force_flat=False` 재현은 target 도달만 realized, 나머지는 right-censored다. `_candidate_ready`는 이 모드에서 최소 target completion2, holdout은1을 요구하지만 전체 위험/자본점유·현재 정책 대비 순이익 개선은 선택조건이 아니다. rank는 resolved EV를 앞에 두고 target_bps도 tie-break에 사용한다. 9/8 삼성 KRX 진단 후보(target80bps)는 calibration37 중26완료/11censored, holdout6 중4완료/2censored이며, 완료 표본 승률100%다. 완료 median은 약52.2분/126.4분, 180초 내 target은1/26·0/4다. **이는 신규 선택이 아닌 진단 challenger이고 실제 runtime은 기존 carry/veto이므로 현 PID의 전략 성과로 옮기지 않는다.**

별도 symbol 연구도 signal lookback/drawdown/reclaim과 target30/50/75/100bps를 동시에 탐색한다. 080220의 양수 재현 EV만으로 원신호 개선인지 출구/보유기간 효과인지 분리할 수 없다. 작은 수익 빈도의 개선이 보장되지 않는다.

보완: 기존 producer 안에서 `실제 적용 baseline 고정`, `signal-only`, `confirmation-only`, `exit-only` 평가를 같은 식별 가능한 기회집합에 대사한다. 후보 생성 grid를 늘리지 않고 기존 축의 평가를 개선한다. 완료 순이익/유효 관찰일, 완료 빈도, full/partial·미체결, censored 자본점유, tail을 동반 표시한다. censored 손익은 합성하지 않으며, 정확한 exit 연구가 필요한 부분은 이미 진행 중인 적응형 청산 owner/연구를 재사용한다. 신호/entry 연구에서 새 SELL adapter·강제청산을 만들지 않는다.

완료조건: 큰 target의 완료 승자만으로 작은 수익·빈도 목표를 충족했다고 선정하지 않는다. 동일 policy cohort의 비용 후 baseline 대비 증분과 미완료 노출이 설명되며, source-only 비교와 실제 체결 품질/승격을 분리한다.

### F5 — P2 검토대상: 고정 관찰일 조건과 source-ready 명칭

두산/한화는 8/12 이후 **40개 유효 KRX 관찰일**, 각 날짜 PASS row≥300·첫 관찰≤09:30·마지막≥15:20이 필요하다. 최근 3거래일 두산15→15→15, 한화15→15→16이다. 최선에도 추가25/24개 유효일이 필요하며 실제 도달일은 보장되지 않는다. 한화는 calibration/holdout EV `+0.169685%/+0.57%`와 holdout3건 통과인데40일 때문에 대기한다. 반대로 두산은 `-0.194166%/-0.356103%`여서40일만 줄여도 경제성이 통과하지 않는다.

고정40일은 두 곳(producer 및 runtime loader)의 명시 계약이고 자동화 미연결은 아니다. 이 수치의 충분한 경제적 근거를 이번 코드/현행 산출물에서 확인하지 못했다. 자동 삭제하지 말고 기존 calibration/holdout의 유효 신호·시간창 coverage·실행 source를 기준으로 한 중복 여부/필요조건 분리 검토가 적절하다. 종가 exit에 필요한15:20 근거는 유지하되 무관한 장중 누락을 모든 신호의 경제성 결손으로 확장하지 않는다. 장기간 수집과 sparse signal은 서로 다른 조건이다.

#14 morning의 `auto_bounded_candidate_ready`는 source/sample readiness다. 같은 row에 `allowed_runtime_apply=false`, weighted EV `-0.946269%`, post-apply 평균 보유1590.885분이 있다. 음수 baseline이 양수 challenger 연구를 막지 않는 것은 정상이며 이를 강제 positive-control gate로 바꾸면 안 된다. 명칭/표를 `source_ready / causal_candidate_ready / selected / consumed / economics`로 분리하는 보완이 타당하다. 재진입/오후의 floor 예상51일/29일은 stationary 표본 추정이지 승격 ETA가 아니다.

## 4. 지금 수행할 작업 순서와 완료 판정

| 순서 | 기존 수정 owner / 작업 | 완료 판정 |
| --- | --- | --- |
| A1 | #15 경제성 null·분모·semantic profile/연속 epoch(F1) | 잘못된0 EV와 정책 혼합 제거, 관련 consumer 회귀. 조건 부족과 계산 결함 분리. |
| A2 | widget 실제 event→order incident·복구/두 policy branch 전달(F2) | 3거래일 exact 분모 보존; unresolved next-day 이관, 정상 차단·실행 장애·원천 결손 분리. |
| B1 | advisory raw→visible→trade 및 2/3 동일 기회 재현(F3) | 신호선택과 추가10초의 순효과 분리; 기존 entry timing과 중복 축 없음. |
| B2 | 기존 calibration/research의 baseline·신호·timing·exit 분해(F4) | 현재 정책 대비 비용 후 이익·빈도·자본점유·tail이 설명됨. 미결속은 null/source-gap. |
| C | 40일 중복 gate/조건 진행도와 source-ready 표기(F5) | 한화 sample-wait와 두산 no-edge 구분, producer/loader/rollback 정합성 검토 후 필요한 조건만 변경 제안. |
| 공통 후속 | 기존 native recommendation/workorder → #91/#103/#110·strict 및 기존 PREOPEN consumer | native ID·source hash·권한·최종 소비 대사. finding 번호를 native ID로 발명하지 않음. 코드·배포·자연소비·경제성 개별 상태. |

실행 추적은 [9/9 checklist](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`(21:30~21:40), 적용/incident 확인은 `WidgetEpisodeRecommendationApplyAcceptance0908`을 재사용한다. 이 리뷰는 제안과 acceptance의 기록이며 구현/새 실전권한 지시가 아니다. 이후 구현이 승인되면 source-only 집계·대사부터 review/fix를 닫고, live gate 변화는 영향과 기존 승인 범위를 분리한다. 전체 장후 재실행은 필요 작업에 포함하지 않는다.

## 5. 검증과 경계

8개 기존 테스트 모듈 `327 passed in 17.35s`: widget advisory/auto calibration/auto policy/symbol research/symbol policy, Samsung tuning/policy, low-price two-leg. 이는 기존 회귀 통과이며 위 finding을 해소한 검증이 아니다. 메모리 진단으로 확인2/3의10초 차이, decisive 밖 micro row 제외, broker-priced0 EV0, 실제9/8 failure4 집계를 추가 확인했다. API/provider 호출·비싼 연구 실행 없이 파일·함수·기존 fixture를 사용했다.

문서만 수정했고 `$korstockscan-review-gate`의 읽기 전용/문서 범위를 적용했다. 문서 연결·owner·권한·계수 재검토를 마쳤다. print-only parser는36개 작업과 위 두 기존 owner가 당일 각각1개 존재함을 확인했고 `git diff --check`는 통과했다. 검토한6개 생산자 소스 hash도 재확인 시 불변이다. 코드 finding은 OPEN이며 결함0/경제성 성공을 주장하지 않는다.

source9/8 읽기 시점 byte SHA256:

| Artifact | SHA256 |
| --- | --- |
| widget_advisory_calibration | `3e1f61d4e7f2cd403b747b871a9f06d96356baab0013ebcf990af61713939af5` |
| widget_auto_trade_policy_calibration | `89a66ac2e2a3aaf8a725dad061705d6ebbbbc47d7a7117d9bc5b4a1d86aba450` |
| widget_symbol_signal_policy_research | `9c4192f387b58d5ae0f3c0c05af16ae4e7ad4dd98247dfb03787a0da4c9d0cb3` |
| widget_symbol_runtime_policy_apply | `854d30841e12f6832e61dab19d68cdcb440d9e2689ada4616eb3ed3b621b0155` |
| samsung_machine_entry_tuning | `b0dfdc3500f1ce09ca001fdba7110deba7646515e34a57f500827f076f895bdd` |
| low_price_two_leg_tuning | `4b86574c7f156a3558f95933e1f2550b7f9e392c077202293059f96b2d7a34b1` |

파일 경로는 repository-relative `data/report/<Artifact>/<Artifact>_2026-09-08.json`이다. byte hash와 JSON 내부 canonical hash를 혼동하지 않는다.

## 6. 후속 구현·재리뷰 (9/9 16시대)

후속 사용자 구현 지시에 따라 A1/A2의 집계·전달과 B1/B2/C의 계측·분해·진행도 보완을 실행했다. 위 읽기 전용/327 PASS는 이전 단계의 기록이다. **코드 수리와 모든 전략 선정 결함의 종결은 구분한다. 아래 미완료를 자연 표본 대기만으로 바꾸지 않는다.**

| 항목 | 이번 구현과 검증 범위 | 남은 판정 |
| --- | --- | --- |
| A1 | #15 report v8: broker 완료 실제금액 분모, 미관측 EV/순익 null, 시도금액 진단·full/partial 고정비용 추정 분리. clean 전체 이력은 audit-only, 동일 profile semantic cohort와 연속 post-apply epoch를 분리하고 dated applied source/hash를 보존. v8 candidate/attribution consumer 호환 및 carry-only 유지. | 실제 broker 비용과 fixed-cost estimate는 혼합 승인하지 않는다. 결손 applied receipt는 cohort를 추정하지 않으며 기존 자연 owner에서 확인. |
| A2 | 기존 event 파일에서 owner/session/policy/parent/role별 incident, retry/terminal, 고유 BUY/SELL 주문, full/partial을 분리. exact 후행 full-fill 또는 zero-fill BUY 취소 receipt로만 대응 사건 종료. 확정 거절 BUY는 무체결 종결이지 회복 체결/수익 아님. same-day veto 유지, 미해결은 다음 날짜로 carry. 일반 calibration과 별도 symbol research→policy 양쪽에 연결. | source9/8 삼성 KRX 미해결 목표매도1건은 유지. 수동 부분청산을 전체 복구로 추정하지 않는다. 외부 custody receipt를 canonical widget event로 자동 투영하는 별도 adapter는 아직 없으며 이번 event-only 수리를 전체 custody 복구로 쓰지 않는다. |
| B1 | compact observation에서 버려지던 확인 전 input/range를 최근8회 trace로 보존하고 기존 filter를 사용한 2/3 시점 비교를 daily evaluation→advisory report에 연결. 같은 timestamp 중복 관찰은 runtime 확인 횟수를 증가시키지 않도록 수정. 비주문 권한과 downstream 신호 영향 metadata를 분리. | 추가10초/신호소멸 진단은 구현됐지만 **executable quote/fill·고정 exit 비용 후 paired EV와 이를 사용하는 확인 횟수 선정은 미완료**. 기존 proxy 부호 heuristic은 남으며 명시적으로 unpaired로 표기. `executable_net_ev_delta_pct=null`을 0/효과 없음으로 쓰지 않는다. |
| B2 | 기존 두 연구 producer에 exact-date 검증 정책 control, signal-only, exit-only, combined 비교 추가. 같은 source window/calibration·holdout에서 재현하고 빈도·보유/미완료 노출을 표시. control 파일 로드는 PID 소비 증명이 아님을 명시. 신규 grid·수량·target live 변경 없음. | **기존 winner 중심 순위를 위 paired 경제성으로 교체하는 선정 로직은 미완료**. 비교 생성은 실제 EV 개선/자동 승격 완료가 아니다. 정확한 exit 재현은 병행 적응형 청산 owner를 재사용해야 하며 미완료 노출을 0손익으로 대체하지 않는다. |
| C | 유효 관찰일 잔여 최솟값·실제 coverage 비율·승격 ETA null을 표시. #14 source-ready와 경제성/live 승격을 별도 필드로 분리. | 40일을 대체할 검증 근거는 확보되지 않아 수치를 임의 변경하지 않음. coverage·신호/holdout 중복 조건 재설계는 다음 구현 판단 대상이며 source-ready만으로 승격하지 않는다. |

읽기 전용 자연 자료 재현: 9/4 BUY4/SELL4, 9/7 BUY2/SELL2, 9/8 BUY4/SELL5. 9/8 clean incident8건 중 과거 확정 거절 BUY7건은 무체결 종결, 목표매도1건만 미해결이다. 동일 목표매도는 submit 실패3+terminal1이며 다음 날짜 무이벤트·다른 owner/정책/신호의 체결로 복구되지 않는다. `sk_eternix_midday`와 `kakao_midday`의 기존0.0 EV는 메모리 재집계에서 각각 null로 정정됐다. 원본 운영 report는 덮어쓰지 않았다.

자동화: 설치된 기존 evaluation wrapper의 실행 순서는 바꾸지 않았다. 새 event ledger는 symbol research JSON 자체에 동결되어 기존 hash 검증/dated policy consumer가 읽는다. source9/9부터 누락된 execution-quality handoff는 신규 symbol 적용을 차단하되 observation은 유지한다. source9/8 이전 기존 policy 재구성 형태를 보존했으며 target9/9 loader는 여전히080220 한 종목이다. advisory trace는 수정 collector가 정상 승인 기동에서 로드된 뒤부터 자연 생성되며, 이번 작업에서 collector/trader PID는 바꾸지 않았다.

리뷰: `$korstockscan-review-gate`로 첫 집계 수정→2개 기존 fixture 분모/schema 정정→incident 날짜/거절/부분복구/owner 재리뷰→중복 확인 수리 및6개 fixture의 실제10초 진행 보완→재검증을 수행했다. 13개 관련 모듈의 **589 PASS**는 마지막 추가 integration test 직전 receipt이며 최종 검증은 아래에 기록한다. 이 수는 병행 adaptive-exit 구현 전체의 검증이 아니다. 새 두 helper는 `src/engine/monitoring` 소유이며 별도 CLI/producer·engine-root 모듈을 추가하지 않았다.

전체 목적 판정은 **YELLOW/부분 구현**이다. A1/A2 및 계측 수리의 검증 완료를 이유로 B1/B2의 미구현 경제성 선정까지 finding0이라고 선언하지 않는다. 다음 실제 작업은 `같은 raw confirmation의 executable paired replay→검증 정책 control 대비 EV/빈도/자본점유 평가→기존 확인/target 선정 consumer 연결`이며 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`가 소유한다. 운영 장후 전체 재실행·정책 publish·실주문·PID 변경·commit/push는 수행하지 않았다.

최종 receipt: 위13개 관련 모듈 **592 passed in 22.59s**, 수정 Python의 compile·Ruff PASS, `git diff --check` PASS. 신규 비교 producer 연결·빈 baseline·잘못된 수량/boolean receipt·동일 날짜 quality 누락과 이전 dated policy 호환 반례를 포함한다. print-only 문서 parser는36개 작업과 기존 두 OPEN owner를 유지하며 외부 Project/Calendar sync는 실행하지 않았다. 검증한 수리 범위 밖의 B1/B2 선정 미구현·canonical custody adapter 결손은 위 표대로 OPEN이다.

## 7. 남은 선정·custody 전달 구현

후속 `남은 작업 시행`에 따라 §6의 미구현 경로를 보완했다. §6의592 PASS와 미완료 표시는 당시 이력이다. 이번 범위는 기존 widget evaluation/선정/incident consumer이며 병행 적응형 청산의 실제 owner loop·활성화나 새 SELL adapter를 대신 구현한 것이 아니다.

### 구현과 자동화 연결

- 삼성 collector의 기존 정규화 BBO·수신시각·수량·raw 신호·최종 entry/exit 충돌 여부를 최근8회 trace에 보존한다. 요청/API/FID parser·호출 주기·수량·주문 guard는 바꾸지 않았다. 기존 advisory calibration이 이 trace에서 확인2/3을 비교하고, auto-trade calibration은 같은 검증 incumbent에서 기존 target grid만 비교한다. source9/9부터 unpaired proxy 부호와 완료 승자 순위는 새 값 선정 권한을 갖지 않는다.
- `widget_paired_policy_replay`는 같은 raw 기회, 같은 leg10·add·cap·cutoff·cooldown을 고정한다. 다음 fresh BBO·보수적 잔량 참여50%/25%·서로 다른 두 target 호가와 날짜별 비용을 사용한다. 모델의20분 공통 청산은 **평가 전용 CF**이며 실제 terminal/PnL, live 시간청산 또는 broker fill proof가 아니다. 경로·호가 결손, 부분체결 가능성, 미성숙을0손익으로 채우지 않는다. 공통 초기 자본 분모의 기회 EV, 거래별 tail, 모델 순익/관찰일, 자본시간과180초 내 작은 순익 횟수를 별도로 비교한다.
- 평가창은 대상일 기준 최근20 KRX 거래일의 chronological calibration/holdout이다. 관측이 끊겼다고 오래된20개 표본일을 무기한 재사용하지 않는다. 최소 calibration2쌍·별도 날짜 holdout1쌍, base/stress 모두 양수 후보 EV·baseline 대비 개선·순익/일·tail·자본점유·빠른 작은 순익 비열화를 확인한다. calibration에서 후보를 고정하며 holdout 실패 후 차순위 후보를 재탐색하지 않는다. 기존 정책의 EV가 먼저 양수여야 개선 후보를 검토할 수 있다는 선행조건은 없다. 가격 미관측과 경제성 미충족을 분리하며 정확 경로가 없는 상태의 승격 ETA는 주장하지 않는다.
- 신규 collector source가 없으면 검증된 기존값을 carry한다. 일시 incident veto가 마지막 recipe까지 영구 소실시키지 않도록 이전 검증 recipe를 **동일값 복구 전용**으로 찾되, 최신 source/실제 incident gate를 다시 통과해야 한다. operator/다른 차단 사유는 넘어가지 않는다. 확인 축이 바뀌면 당일 target 변경은 보류하고, 기존21:15 timing owner에도 같은 entry-stage 변경을 전달한다.
- policy consumer가 source-date/scope/axis·연결 study hash·원 incumbent 파일 hash와 비변경 parameter를 재검증하고 paired 판정을 재계산한다. 기존 source9/8 정책의9/9 소비 형태는 보존한다. 실제 적용은 기존 dated policy writer/loader가 소유한다. 이번 작업에서 운영 policy를 발행하거나 PID를 바꾸지는 않았다.
- 별도4종목 연구는 기존 baseline이 있을 때 joint grid를 진단으로 내리고 `signal_only` 또는 `exit_only`만 비교·선정한다. cap과 다른 축은 고정한다. 기존 calibration/양쪽 half/holdout·고차 cap 증분 guard를 유지하며 동일 창의 비용 EV·순익/일·tail·보유시간·작은 수익 횟수로 baseline 대비 개선을 확인한다. 선정 실패 시 경제성 검증을 통과한 baseline을 사용하며, 그것도 실패하면 source-only다. 첫 admission처럼 incumbent가 없는 종목은 기존 독립 승인 계약이며 증분 개선을 입증했다고 표시하지 않는다. 결과의 정확한 arm/통계/parameter를 symbol policy consumer가 다시 대사한다. 종목명이 비교 arm 이름으로 덮이는 부수 결함도 수정했다.
- append-only owner registry를 읽기 전용으로 검증해 동일 account/위젯 owner/position/parent의 후행 수동청산을 incident에 투영한다. 모든 수량이 대사되어 잔여0이고 미결 주문이 없을 때만 `resolved_exact_manual_custody_flat`이다. 이는 보유 해소이지 목표주문 성공/전략 수익이 아니다. 부분청산, 다른 owner·parent, 미래 receipt, 해시 손상과 pending 상태는 자동 종결하지 않는다. canonical event 파일/registry를 재작성하지 않고 양쪽 기존 policy producer가 frozen projection을 소비한다.

### 실제 상태와 조건 검토

읽기 전용9/9 확인: 삼성 NXT 두 세션은 기존9/9 정책(애프터80bps/프리40bps), KRX는 실행품질 veto이고 확인 횟수3이다. 새3→2 또는 target 변경을 적용하지 않았다. KRX 동일 사건은9/8·9/9 모두 미해결1건, 수동 custody projection0건이다. 실제 원장 근거가 full-flat을 입증하지 못하므로 adapter 구현을 이유로 veto를 해제하지 않는다.9/4·9/7 미해결0과 분리한다. 복구용 recipe는9/8 effective 정책으로 식별되지만 현재 차단 해소/실적용 receipt는 아니다.

두산·한화는 이벤트 기반 entry/source EXIT를 사용하므로 삼성의 표시 확인 횟수와20분 CF를 그대로 실전 효과로 대입하지 않는다. 이번 신규 replay의 자동 적용 범위에서 제외한다. 기존40 유효일 조건은 최초 admission 계약이고 그 수치를 대체할 실행품질·독립 경제성 근거가 없다. **40일의 최적성을 입증한 것은 아니며 임의 감축/삭제하지 않는 것으로 이번 변경 판단을 종결한다.** 기존 관찰일 진행도와 실제 경제성 미달 사유를 계속 따로 표시한다. 신호·표본 또는40일 충족만으로 hard guard/실주문 권한이 새로 열리지 않는다.

### 리뷰·완료 경계

`$korstockscan-review-gate`에 따라 단일 축·계수·시간/venue·중복 BBO·원천 결손·부분체결·비용·holdout 재탐색·기존 recipe 영구소실·hash/date/consumer 변조·수동 custody·native handoff를 반복 리뷰하고 보완했다. 두 기존 fixture의 실제 producer 계약(entry-cap 비교/유효 minimum-history)을 바로잡고 producer→consumer 정상/거절 반례를 추가했다. 아래 최종 receipt는 이번 widget 경로와 직접 timing consumer의 검증이며 병행 adaptive-exit 전체의 완료 선언이 아니다.

코드 연결과 목적에 맞는 **선정 기준의 보완**은 닫되, 배포·신규 trace 자연 생성·다음 dated policy/PID 소비·실체결 비용 후 EV/빈도 개선은 OPEN이다. 모델상 후보 선택은 실전 수익 개선의 증거가 아니다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`와 `WidgetEpisodeRecommendationApplyAcceptance0908`을 유지한다. 별도 collector/trader 재기동, 정책 수동 변경, 실주문, 전체 장후 재실행, commit/push는 수행하지 않았다.

최종 receipt (9/9 KST): 직접 영향15개 테스트 모듈 **680 passed in 26.01s**, 수정 Python compile·Ruff PASS, `git diff --check` PASS. print-only parser36개 작업과 기존 두 OPEN owner 유지. 최종 source/consumer 리뷰의 단일 축·원 incumbent 결속·오래된 표본 재선정 금지까지 이 회귀에 포함되며 검토한 변경 범위의 미해결 finding0이다. 단, C의40일 최적성·자연 source/PID·수익 효과와 병행 적응형 exit는 별도 미완료/근거 경계다. 해당 calibration/research/timing producer의 실행 PID는 없었고 관측된 관련 PID는 이 회귀 테스트뿐이었다. 운영 장후 체인 재실행·external sync는 하지 않았다.

## 8. 잔여 자연 입력·진단 handoff 보완

후속 `남은 작업 시행`에서 §7 완료 범위를 재구현하지 않고 현재 자연 입력과 consumer를 대사했다. 9/9 17:30 읽기 전용 확인에서 삼성 수집기 PID663은07:10:59 기동한 `korstockscan-samsung-widget-collector.service`다. 17:34대 읽은 당일 파일은 KRX387/NXT 프리50/애프터116개 관찰시점, 새 replay input0개였다. 이 숫자는 저장된 관찰시점 수이지 기회·체결·EV 표본 분모가 아니다. 해당 파일 snapshot SHA256은 `d144b94958b8b70fa7fa83d973a2576328fbf7e2c703b761709bf630bacec700`이며 이후 append가 계속되는 원천의 영구 hash가 아니다. 이는 신규 trace 미반영 근거이지 시그널 부재/경제성 실패가 아니다.

확인한 추가 결함과 보완:

- 기존 입력 reader가 최근 확인 trace와 최상위 input만 읽어 `advisory.execution_replay_input`의 현재 관찰값을 trace 부재 시 누락했다. 정식 nested 입력도 소비하고 동일 시점 중복·내용 충돌 판정을 유지한다.
- 기존 carry 사유는 원천 미반영·표본 부족·기간 만료·경제성 미달을 구분하지 못했다. 동일 날짜/세션의 관찰/input 수와 원천 진단을 기존 study→advisory/target policy→loader에 전달하고, 기존 선정 조건을 바꾸지 않은 채 `source_gap`, baseline 계약 결손, rolling expiry, paired sample floor, 미완료 outcome, 경제성 미달, 고정 calibration winner의 holdout 미통과를 분리했다. `replay_input_observed`도 PID 소비·실체결·수익 acceptance가 아니다.
- 잘못된 session/state 타입이 전체 연구를 예외 종료시키는 반례를 격리했다. malformed state 경로는 제외하고 미관측/부분체결을0손익으로 만들지 않는다. 초기 baseline/지원 session 거절에도 hash를 발급해 정상 비적격과 손상 계약을 구분한다. source9/8 loader의 반환 형태는 유지한다.

검증은 기존15개 직접 영향 모듈과 producer→consumer 정상/거절 반례에 한정한다. 중간 malformed-state 회귀에서 발견한 이전 raw-state 보관 경로의 TypeError도 수정하고 재검증한다. 연구/선정 허들·40일·주문/수량/안전 조건은 바꾸지 않았다. 현재 NXT 검증 recipe80/40bps는 메모리 판정에서도 그대로 carry이고 KRX 실행품질 veto는 유지한다. 정책·원천·원장을 쓰거나 장후 전체 재실행·Provider/실주문 호출을 하지 않았다.

남은 운영 단계는 삼성 수집기의 검증된 코드 반영·승인된 정상 기동 후 새 trace 확인, 기존20:10 평가와 다음 dated policy/PID, 비용 후 실제 EV/빈도 acceptance다. 이번 범위의 수리 완료를 이유로 collector/trader를 임의 재기동하지 않는다. 병행 적응형 청산은 별도 최신 owner-loop 리뷰를 따르며 여기서 종료하지 않는다. 기존 두 OPEN owner에 후속을 유지한다.

최종 receipt: 직접 영향15개 모듈 **684 PASS/26.42초**, Ruff·Python compile·`git diff --check` 통과. print-only parser36개 중 기존 두 owner가 각각1개이며 외부 sync는 실행하지 않았다. `$korstockscan-review-gate`의 원천→study→dated producer/loader, 정상 비적격/손상 계약, silent-fail 및 기존 권한 경계를 반복 리뷰했고 **이번 source/진단 수리 범위 미해결 finding0**이다. 운영 반영·자연 소비·실제 수익 및 병행 적응형 청산 전체 구현 완료는 이 receipt에 포함되지 않는다.

## 9. 사용자 승인 삼성 수집기 단독 재기동

사용자가 `매매 프로세스와 정책은 유지하고 삼성 수집기만 우아하게 재기동`에 동의하여 **9/9 17:42:15 KST**에 `sudo -n systemctl restart --no-block korstockscan-samsung-widget-collector.service`를1회 실행했다. §8의 재기동 미실행은 이전 시점 기록이다. 이번에는 코드 추가 수정·commit/push·정책 발행·전체 장후 재실행을 하지 않았다.

- 사전 gate: 현행 Plan/checklist·실제 unit과 역방향 의존성 확인. 서비스의 `PartOf/ConsistsOf/PropagatesStopTo`가 비어 있고 독립 control-group임을 확인했다. 직접 영향5개 테스트 모듈 **196 PASS/4.44초**, compile·`git diff --check` 통과 후 실행했다. 기존684 회귀와 중복이므로 합산하지 않는다.
- 정상 SIGTERM 종료: 기존PID663 → 새PID679800, systemd `Deactivated successfully`→`Started`, 새 invocation `e11bcffdce2f4656bea0ab607eef0981`. 관찰 시 `active/running`, `Result=success`, `NRestarts=0`; 강제 KILL/별도 kill 명령·unit/env 변경 없음.
- 새 원천: 첫 snapshot `17:42:21.797880+09:00`부터 `widget_confirmation_input_trace_v1`와 `widget_paired_replay_input_v1`을 생성했다. 분당 recorder의 다음 저장 `17:43:00.663999+09:00`에서 최근5개10초대 관찰 입력을 복구했고 **exact5/valid BBO5/invalid0/conflict0**, NXT_AFTERMARKET·source-quality PASS를 확인했다. current snapshot과 분당 history의 생성시점 차이를 장애로 판정하지 않았다. 당시 history byte hash는 `a12c9666fc55971dcc130cca437b1d6991786be8c560c8d630456fb64b169f82`이며 계속 append되는 파일의 as-of 근거다. journal warning/error는 해당 재기동 이후 관찰 구간에 없었다.
- 보존: main PID412924, widget trader PID15090, 두산/한화 collector PID661/662 및 start/invocation이 유지됐다. 당일 advisory/auto-trade/symbol 정책3개와 `owner_custody.env`의 전후 SHA256이 동일하다. 계좌/주문 API를 직접 호출하거나 다른 owner의 보유·주문을 재귀속하지 않았다. 계속 실행 중인 다른 세션/매매 owner의 자연 활동까지 동결했다고 주장하지 않는다.

검증·기동 시점 code SHA256:

| 파일 | SHA256 |
| --- | --- |
| `samsung_widget_advisory.py` | `5fb8869ad56cfde131b737b6c1d9c2d959af6a4b6ba66d4fc9fa572c40bf7066` |
| `widget_paired_policy_replay.py` | `22f849b780265531676788f3c534982d275423a1f01edc3962ccf8de93ccbc09` |
| `widget_advisory_calibration_policy.py` | `de3171fae258e1d83f49c97c930c36435391ffeb81c093cede76c315d0ff7966` |
| 설치 collector unit | `cc75400a9b4d1629d9f32a77afa559724904358eb296483e161937d7ad25f7c4` |

판정: **승인된 수집기 코드 반영·새 PID·자연 trace→reader 전달 확인 완료**. 기존 정책을 바꾸지 않았으며 신규20분 paired 경제성/holdout, 다음 dated selection·실제 매매 PID 소비·순이익/빈도 개선은 별도 OPEN이다. KRX/프리 구간의 지난 원천을 소급 생성하지 않는다. 기존 `WidgetEpisodeRecommendationApplyAcceptance0908`/`MachineLifecycleTurnoverObjectiveFollowup0909`에서 예정된 자연 producer·다음 정상 세션을 확인하며 추가 재기동·수동 정책 변경 권한으로 확대하지 않는다.

후속17:45 관찰: `17:45:00.561270` snapshot은 기존 Kiwoom 공유 read 예산의 `shared_read_rate_wait_budget_exhausted`로 DATA_WAIT/BLOCKED였고, **17:45:39.228434 정상 주기에서 WATCH/PASS·새 trace로 자연 회복**했다. 같은PID679800/NRestarts0이며 API 호출량·retry/budget·guard를 높이거나 추가 재기동하지 않았다. 이 일시 source gap을 가용한20분 경제성 경로로 채우지 않는다. 그 후 확인에서도 정책3개/owner env 전후 hash는 동일했다. 문서 반영 후 print-only parser36개/기존 두 OPEN 각각1개와 `git diff --check`를 확인했다.

## 10. 비용 후 수익 빈도·조기 결과·자동 소비 재리뷰

후속 코드리뷰/수정 지시에 따른 9/9 18시대 보완이다. 범위는 widget 평가·기존 축 선정과 직접 consumer이며, 병행 적응형 청산 전체의 구현 완료를 선언하지 않는다. §7~9는 각 시점 이력이다.

### 확인한 결함과 수정

| 결함 | 보완과 회귀 근거 |
| --- | --- |
| 순익 상한 구간을 빈도 gate로 사용 | 같은 청산시점·자본시간에서 비용 후 수익률이0.27%→0.57%, 모델 순익/일540→1140원으로 개선되어도 `작은 수익<=0.5%` 횟수가2→0이라 후보가 탈락했다. 해당 구간은 진단으로 유지하고 선정은 **180초 내 비용 후 양수 청산 횟수, 수익률 상한 없음**으로 비교한다. 삼성 paired 및4종목 component producer/selector에 함께 반영했다. 0.5%는 최소 수익 목표가 아니다. |
| 양쪽 결과가 끝나도 전체20분 원천 요구 | baseline/candidate가 동일한 유효 연속 원천에서 모두 완료됐으면 이후 단순 자료 결손은 해당 결과를 무효화하지 않는다. `path_source_gaps`와 전체 제외를 분리하고 한쪽 미완료/부분체결은 승격 분모에서 제거하거나0손익으로 만들지 않는다. 짧은 미확인 경로는 censored, 관측된 신호 종료는 확정 no-entry다. 동일 호가 ID 충돌은 시간 역행보다 먼저 검사하여 과거 가격을 포함한 경로를 제외한다. 완료 outcome의 진입/청산 시각·날짜·공통 horizon도 consumer가 검증한다. |
| 추가매수 실런타임 trigger와 BBO 대용값 혼동 | 실제 widget scale-in은 현재 체결가와 tick 정렬 trigger·독립 guard를 사용하지만 연구는 best ask로 대체했다. 정확한 trigger 입력이 없는 추가매수 recipe는 `scale_in_runtime_trigger_source_missing`로 새 값 선정을 금지하고 검증 incumbent를 carry한다. 잘못된 대용 계산은 제거하고 consumer에서도 거절한다. 현재 삼성 NXT80/40bps 두 recipe는 add=[]라 적용 범위가 줄지 않는다. 추가매수 수량·trigger·실제 주문을 바꾼 것이 아니다. |

기존 최소 calibration2쌍/독립 날짜 holdout1쌍, 최근20 KRX 거래일, base/stress의 비용 후 양수 EV·baseline 대비 개선·순익/일·tail·자본시간·수익 빈도 비열화, calibration winner 고정 후 holdout 검증, 기존 한 축·수량·주문 안전 조건은 유지했다. 4종목 grid의 calibration 선정 후 holdout 순서도 재검토했으며 holdout 실패 후 차순위 탐색은 하지 않는다. 비용 추정 CF는 실체결 품질·실현수익의 증명이 아니다.

두산/한화의 별도 최초 admission40유효일은 이 삼성 계약의 문턱이 아니다. source9/8은 각각15/40·16/40일이며, 유효일 기준 최소25·24일이 더 필요하다. 최근 source coverage 제외가 있어 달력상 승격 ETA를 보장할 수 없다. **조건이 가볍거나 최적이라고 판정하지 않는다.** event/source EXIT·실행품질의 대체 검증 없이40일만 낮추는 변경은 하지 않으며, 기존 OPEN의 해당 owner 재평가로 남긴다. 삼성 결과를 두산/한화 승격 근거로 전용하지 않는다.

### 자동화와 실제 반영의 구분

- 설치된 evaluation timer는9/9 **20:10** 예정이며, 기존 wrapper의 advisory→auto-trade calibration→EOD 확인→symbol research→symbol policy 순서는 유지됐다. 장후 새 process는 수정된 selector와 같은 generation/hash를 사용하고 dated consumer는 판정을 재계산한다. 이번에는 운영 산출물 발행·장후 전체 재실행을 하지 않았다.
- trader의 날짜 rollover는 정책을 다시 읽지만 장중 catalog refresh는 신규 session 추가만 허용하며 이미 적용 중인 정책을 교체하지 않는다. 타이머의 `start`도 이미 active인 장기 process의 코드 reload를 뜻하지 않는다.
- **이번 수정의 장기 PID 반영은 미완료다.** 삼성 collector PID679800은17:42에 이전 paired module을 import했다. 모듈의 엄격한 metric-contract 비교가 바뀌었으므로 다음 새 정책을 기존 메모리 코드가 자동 수용한다고 주장할 수 없다. 검증된 코드의 최초 배포·승인된 정상 기동과 policy/PID receipt가 필요하다. hot reload·수동 env/정책 변경·추가 재기동으로 우회하지 않았다. 이후 동일 배포 generation에서 조건을 충족한 정식 정책의 날짜별 소비는 기존 자동 경로다.

18:11 읽기 전용 자연 입력은90건/유효 BBO90/충돌0, raw WATCH80·ENTRY_CAUTION9·NO_CHASE1이다. source byte hash `07a5d427ac63f0a705c110c7ff94325b9048862da781a483e01733e8ca475b1b`, 마지막 관찰18:11:13이며 이후 append되는 원천의 as-of 값이다. KRX/프리의 과거 입력0을 소급 생성하지 않는다. 후속 메모리 진단의 삼성 NXT 애프터 기회1건(17:55:21)은 observation gap으로 모든 target arm이 `right_censored`, `candidate_ready=false`, `paired_outcome_incomplete`, 기존80bps carry였다. 이 진단 source hash는 `db8eb62873e2509974b0574823e3c328337e5ba5199cdb2ebf58933ca30c0113`이다. raw 입력90건을 경제성90쌍으로 세지 않는다. API/provider 호출·파일 publish 없이 기존 파일과 함수를 사용했다.

### 최종 검증과 남은 acceptance

`$korstockscan-review-gate`로 반례 재현→수정→직접 producer/consumer 재리뷰→추가 호가 충돌·시각·scale-in 반례 보완→재검증을 수행했다. 직접 영향15개 모듈 **695 passed in27.59초**, Ruff·Python compile·`git diff --check` 통과다. 중간89/691 PASS와 합산하지 않는다. 현재 코드 수리 범위 미해결 finding0이며, 수리 효과는 **불필요한 후보 탈락 제거와 부정확한 승격 방지**로 확인했다. 실제 비용 후 수익·빈도 개선은 아직 입증되지 않았다.

기존 `MachineLifecycleTurnoverObjectiveFollowup0909`와 `WidgetEpisodeRecommendationApplyAcceptance0908`에 최초 코드 배포/승인 기동→20:10 자연 산출물/후행 consumer→다음 dated policy/PID→실체결 비용 후 EV·빈도·자본점유를 구분해 남긴다. 미래 데이터 부족·추가매수 trigger 원천 결손을 반복 동일 재현으로 해소했다고 쓰지 않는다. 현재 매매/collector PID·주문·정책·guard·cron/systemd·commit/push는 변경하지 않았으며 별도 적응형 청산의 미완료 owner도 유지한다.

최종 문서 validation: print-only parser36개 중 기존 두 OPEN owner 각각1개, `git diff --check` 통과. 재확인한 collector679800/trader15090은 active·NRestarts0이고 당일 advisory/auto-trade/symbol 정책3개 SHA256은 §9 시점과 동일하다. 외부 Project/Calendar sync는 실행하지 않았다.

## 11. 사용자 승인 배포·기동 실행

후속 `배포, 기동승인`은 위 widget 평가/선정 consumer의 검증 코드 반영 승인으로 해석한다. 새 정책값·적응형 청산 활성화·실주문 직접 실행·전체 main/episode 재기동·커밋/푸시 권한으로 확대하지 않는다. 기존 systemd ExecStart가 작업트리를 읽으므로 별도 코드 복사나 unit/env 변경 없이 필요한 장기 process만 정상 재기동한다. 미커밋 작업트리이며 파일 SHA로 반영 세대를 결속한다.

18:19~18:21 사전 확인: 삼성 collector679800, widget trader15090, main412924, 두산/한화 collector661/662. 기존 삼성 NXT episode는 BUY0063427/FILLED10주와 SELL0063429/SUBMITTED10주·target273500원, policy `widget_auto_trade_policy_2026-09-09_from_2026-09-08`/80bps/add=[]를 보유한다. 이 수량·주문번호·원 정책과 상태 파일을 보존한다. 적응형 session은 없고 실제 launcher는 `adaptive_exit_services`를 공급하지 않는다.

배포 전 추가 gate: widget/paired/실제 consumer 및 병행 owner-loop 회귀에서 **516 PASS/4 SKIP/1 FAIL(32.75초)**. 실패는 `test_machine_adaptive_exit_arbitration.py::test_pending_broker_buy_stays_explicit_recovery_not_implicit_cancel[widget]`이며 pending BUY/ACCEPTED가 `competing_order`로 남아야 하는데 `owner_loop_step_completed`가 됐다. 검증 중 shared `widget_auto_trade/engine.py` SHA도 변경되어 이번 회귀를 최신 파일 전체의 PASS로 인정할 수 없다. **위젯 매매기 재기동은 보류**하고 병행 작업을 덮어쓰지 않는다. §10의695 PASS는 그때의 범위/세대 이력이며 이 새 실패를 닫지 않는다.

삼성 collector는 해당 live engine/owner-loop에 의존하지 않는다. 분리된 직접5개 모듈 **230 PASS/5.55초**, compile·Ruff·diff gate를 통과했고 아래 소스와 설치 unit hash가 검증 전후 동일하다. collector만 정상 SIGTERM→systemd start를1회 수행할 수 있으며 실패 시 강제 KILL·반복 재시작·API 예산 상향으로 우회하지 않는다. 매매기 pending target을 취소하거나 수동 청산하지 않는다.

| 배포 대상 | SHA256 |
| --- | --- |
| `samsung_widget_advisory.py` | `5fb8869ad56cfde131b737b6c1d9c2d959af6a4b6ba66d4fc9fa572c40bf7066` |
| `widget_advisory_calibration_policy.py` | `de3171fae258e1d83f49c97c930c36435391ffeb81c093cede76c315d0ff7966` |
| `widget_paired_policy_replay.py` | `d4be309208b3ecfc651ea5668e2ae3eb8b4b7f01a783b9cd17d67a231d85ab46` |
| 설치 collector unit | `cc75400a9b4d1629d9f32a77afa559724904358eb296483e161937d7ad25f7c4` |

실행 상태: 사전 gate 완료, 삼성 collector 재기동 후 PID/자연 원천·원 정책/다른 owner 보존 확인 예정. 위젯 매매기 gate 실패는 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`에서 안정된 소스의 수정·재검증 후 승인 범위의 정상 기동으로 닫아야 한다.

18:22~18:26 후속: 삼성 collector는18:22:35 정상 SIGTERM 종료·시작1회로 **679800→727306**, invocation `4d80b8ca7b294addb9aa15071df2e9d4`, active/running·Result success·NRestarts0이다.18:22:59 새 WATCH/PASS snapshot과 trace/replay schema를 확인했다. 기존 매매기/main/타 collector와 정책3개/owner env는 유지했다.

병행 작업에서 pending 주문 분기를 보완한 뒤 직접 재검토했다. 허용된 target 외 주문은 명시 terminal 또는 확정 미접수 FAILED가 아니면 recovery로 남기며 ACCEPTED/UNKNOWN/AMBIGUOUS를 무시하지 않는다. 최신 engine SHA `e23e48f57ec170b8155079fb2cb1d85b66122f9ca0c41789377f53d3a7e236dd`와 관련17개 소스/테스트가 재검증 전후 불변인 상태에서 **527 PASS/4 owner-비대상 SKIP/31.76초**, Ruff·compile·diff PASS를 확인했다. 앞선1 FAIL은 이 성공보다 이전 세대의 기록으로 보존한다. 해당 병행 코드를 여기서 수정하거나 새 기능 권한을 열지 않았다.

실제 주문 기능 없는 사전 constructor 검증(gateway/registry는 inert object, loop 미실행): same-date state policy 일치, 삼성 open10주, 적응형 services 없음, 기존 캐시 토큰 유효를 확인했다. 설정 SHA `3d17ee40f6ad7fbb901113625e40daa3b47b2037ce386c94085f1adad5e930e4`, 로드 정책 SHA `7cadc012560746bcc3d67cadf052cc1f9386328ffff1c1e17190138e470d8ac2`가 기존 startup receipt와 동일하다. 현재 정책/원장 mismatch 없는 검증 코드로 widget 매매기 정상 재기동1회를 진행하며, 이후 같은 expected config/policy로 새 PID receipt·원 주문/수량을 재대사한다. 새 signal/order를 시험 생성하거나 상태를 초기화하지 않는다.

### 실행 완료 receipt

위 사전 보류는 후행 성공 gate로 해소했다. `sudo -n systemctl restart --no-block`를 **각 서비스에1회씩** 사용했고 정상 SIGTERM 종료/Started를 journal에서 확인했다. 강제 KILL·unit/env 변경·토큰 재발급·정책 publish·계좌/주문 API 직접 호출·상태 초기화는 없었다.

| Owner | 정상 시작 KST | 이전 PID → 새 PID | 최신 상태 |
| --- | --- | --- | --- |
| Samsung collector | 18:22:35 | 679800 → 727306 | active/running, Result success, NRestarts0;18:22:59 새 WATCH/PASS trace |
| Widget signal auto trader | 18:25:55 | 15090 → 731458 | active/running, Result success, NRestarts0;18:26:21 새 cycle |

Widget 새 invocation은 `8d8467cf531040e0b0ec55de45275538`이고 원 `.lock`의 flock 점유자가731458 한 개임을 root 읽기 전용 `lslocks`로 확인했다. 새 startup receipt SHA `99645ef409390a83a1467987054ad90270ffc21041b598ea714445352f53a856`는 위 expected config/policy SHA를 명시한 verifier에서 **PASS/findings0/mismatch0**다. 이 verifier의 `current_policy_consumption_verified=false`는 startup 검증과 후행 매매 소비의 분리 표식이므로 실제 EV 성공으로 해석하지 않는다.

18:26 재대사에서 당일 state의 entry qty/허용 종목·session, 삼성 원 entry signal/동결 정책·target·주문별 수량/상태 projection이 재기동 전과 동일하다. BUY0063427/FILLED10, SELL0063429/SUBMITTED10·limit273500,80bps/add=[]를 그대로 관리한다. 신규 adaptive session0·서비스 미주입이라 병행 적응형 청산은 활성화되지 않았다. 검증한17개 소스/테스트 SHA도 재기동 직후까지 동일했고 별도 main412924·두산661·한화662의 PID/시작시각은 유지됐다. 당일 advisory/auto-trade/symbol 정책3개와 owner env SHA는 §9~10 시점과 동일하다.

판정: **요청한 widget 평가/consumer 배포·승인 기동 완료**, 이전 §10의 장기 PID 미반영은 위 receipt로 해소했다. 설치20:10 정기 평가→새 dated policy→다음 실제 정책 소비·비용 후 EV/빈도는 미래 자연 acceptance이므로 기존 두 OPEN을 유지한다. 실주문 테스트·20:10 조기 강제 실행·장후 전체 재실행·추가 canary/전략 승인·commit/push는 하지 않았다. 배포 후 새 소스가 다시 수정되면 그 변경까지 이번 PID가 소비한다고 주장하지 않는다.
