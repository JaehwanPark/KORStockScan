# 스캘핑 익절 임계치 장후 생산자·소비자 연결 및 불필요 값 정리 계획

작성: 2026-09-24 KST. 상태: **격리 작업트리에서 원천 연결 및 삭제 구현 중; 선택 릴리스·정책·PID·봇 미변경**. 대상은 메인 실거래 `SCALPING/SCALP`의 `scalp_trailing_take_profit`과 그 신호 시각을 결정하는 입력·운영값이다. [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8 및 [9/28 실행 owner](../checklists/2026-09-28-stage2-todo-checklist.md)가 안전·원천·일정 기준이다. [기존 런타임 단일화 계획](./scalp-trailing-runtime-simplification-and-producer-closure-plan-2026-09-24.md)의 완료 코드와 [포지션 원천 연결 계획](./holding-exit-position-outcome-runtime-threshold-lineage-implementation-plan-2026-09-23.md)의 비용·체결 계약을 이어받는다.

## 1. 기준과 현재 연결 결손

기준 코드는 선택 릴리스 `2a099e1acff0c975abc221fc2d37d629ab11e794`이다. 9/28 bootstrap은 선택됐지만 `actual_pid_consumed=false`이고 새 자연 청산·비용 후 성과는 미확인이다. 작업본의 별도 미커밋 변경은 계획의 적용 증거가 아니다. `scalp_trailing_input_transition` → `trade_review` → `holding_exit_observation.trailing_threshold_readiness`는 코드상 연결돼 있다. 그러나 전이 때만 기록하는 현재 원천으로는 다른 임계치의 **첫 arm/첫 실행가능 bid crossing**을 전 구간에서 재현할 수 없고, readiness는 네 축 모두 `candidate_value=null`, `eligible_for_live_review=false`, `paired_replay_eligible_ids=[]`이다. 현재 effective receipt의 `effective_branch_only`는 설정 원천·정책 hash·PID 소비 증명이 아니다.

이 계획의 1차 완료 조건은 **고정 현행값을 유지한 채** `설정 원천 → 실제 소비 → 판정 전 구간 → 신호 → 주문·체결·비용 → 장후 적격/결손 분모 → 마지막 보고 소비자`를 같은 포지션·세션·정책 세대로 연결하는 것이다. 2차로 불필요한 값을 제거하고, 3차로 후보 생성·선택을 고도화한다. 연결 완료만으로 새 값 적용이나 수익 개선을 주장하지 않는다.

## 2. 전수 축과 소유권

| 축·현행값 | 현재 생산자 → 직접 소비자 | 장후 결손과 보완 owner | 적용 권한 |
| --- | --- | --- | --- |
| `SCALP_TRAILING_START_PCT` 0.6% | `TRADING_RULES` 코드 기본값 → fast/normal 공통 arm 판정 | 진입 직후부터 arm 전까지의 가격·bid 적격 경로가 부족. `sniper_state_handlers`의 bounded 원천 참조 → `holding_exit_observation`의 첫 arm/미발동 분모 | 익절 전용; 후보는 처음엔 보고 전용 |
| `SCALP_TRAILING_STRONG_AI_SCORE` 75점 | 코드 기본값, 선택 env 직접 override 없음 → 유효 보유 점수의 strong/weak 분기 | 점수 원본·provider·시각·TTL·품질·fallback과 분기 당시 값의 정책 출처 연결 부족. 기존 보유 AI receipt → 포지션 판정 receipt | 익절 전용; 한 축씩 검토 |
| `SCALP_TRAILING_LIMIT_WEAK` 0.4% / `LIMIT_STRONG` 0.8% | 각 코드 기본값 → 같은 공통 고점 대비 실행가능 bid 판정 | 후보폭의 첫 crossing·정확 비용·미체결·holdout 부족. 같은 고점/호가 원천에서 강약별 paired replay | 익절 전용; 동시 변경 금지 |
| `KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS` 250ms | 9/28 env → `ScalpExitSafetyMonitor` | 0B/0D source·receive→evaluation→token→order 시각, 누락/중복 crossing, CPU/REST 부담의 포지션별 분모 부족 | 운영 품질 축. stop 지연·부하 veto 우선 |
| `QUOTE_CONSISTENCY_MAX_WS_AGE_MS` 700ms / `MAX_REST_AGE_MS` 1500ms | quote consistency env → 고점/실행가능 bid·REST 재확인 | route별 원시/수신 시계, false accept/reject, quote 결손과 이후 주문 결과의 연결 부족 | **공유 시세 안전 owner**; 익절 보고서가 단독 적용 불가 |
| `QUOTE_CONSISTENCY_OK_GAP_BPS` 30bp / `WARN_GAP_BPS` 80bp | quote consistency env → `ok`/`warning`/`diverged`; fast 넓은 스프레드 재확인은 80bp 소비 | 품질 상태·틱 크기 보정·실제 reject/재확인 결과를 분리. 30bp가 익절 행동을 바꿨는지 별도 판정 | 공유 안전 owner; 30bp는 아래 정리 후보 |
| `QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS` 400ms / `HOLDING_EXIT_REST_QUOTE_FALLBACK_MIN_INTERVAL_SEC` 10초(하한 3초) | quote env·코드 기본값 → bounded REST 회복 | 요청/응답·route·symbol·age·timeout·rate·복구 성공과 신호 지연 대사 부족 | 공유 시세/주문 품질 owner; 자동 완화 금지 |
| `SCALP_NXT_TRAILING_BID_GUARD_MAX_0D_AGE_MS` 1500ms / `MIN_0B_STALE_MS` 1500ms | 9/28 env·실제 타입별 WS 시각 → 16:00~20:00 NXT normal bid 보정 | 실제 NXT suffix/item/route와 타입별 source clock의 적격·부적격 분모 부족 | 익절 입력 품질 owner; KRX와 분리 |
| 보유 AI 점수 TTL: `AI_HOLDING_CRITICAL_COOLDOWN` 45초 | 보유감시 기본값 → fast/normal 익절의 `fresh` 점수 gate | 점수 생성→유효 판정→강약 변경·fallback·호출 실패를 같은 event에 연결해야 함 | **공유 AI 품질 owner**; stale 점수를 허용하는 자동 완화 금지 |
| 재평가 간격: `AI_HOLDING_MIN_COOLDOWN` 45초 / `MAX_COOLDOWN` 180초 / `CRITICAL_MIN_COOLDOWN` 20초 / `CRITICAL_COOLDOWN` 45초 | AI 보유감시 설정 → 새 점수의 생성 시각 → strong/weak 입력 | 점수 갱신 간격과 실제 strong 전환 지연, 호출량·오류율·경제성을 함께 대사 | 공유 AI 운영 owner; 익절만의 값으로 복제 금지 |
| `SCALP_SAFE_PROFIT` 1.0%, 근접폭 ±0.20%p, 가격변화 재평가 0.20/0.40%p | 코드/환경의 안전수익 기준과 보유 AI 감시의 고정 경계 → 임박 구간·재평가 시각 | trailing arm 자체에는 쓰지 않음. real AI 감시와 sim AI의 별도 독자를 표시하고, 가격변화 기준을 장후 lineage에 노출 | 공유 AI 운영 owner; sim/real 혼합 적용 금지 |
| `AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC` 1.5초 | 보유 AI 기본값 → 점수 재호출 생략 판정 | score freshness와 다른 시계라는 점을 기록하고 재사용으로 인한 강약 지연을 측정 | 공유 AI 품질 owner |

`SCALP_FAST_EXIT_GUARD_ENABLED`는 fast 손절 스위치이고 익절 tuning 축이 아니다. `scalp_mfe_protect_exit`은 별도 보호 계약이며 현재 `TRIGGER_PROFIT_PCT=-0.3` operator lock과 코드의 수익률 `>=0` 하한이 겹쳐 발동 구간이 없다. 손절·보호·broker/account/order/quantity/cooldown·widget/episode/manual custody는 이 작업으로 바꾸지 않는다.

## 3. 먼저 닫을 생산자·소비자 연결

| 순서 | 구현 위치·산출물 | 수용 조건 |
| --- | --- | --- |
| P0. 유효 설정 원천 봉인 | 기존 `src/engine/automation/runtime_policy_bootstrap.py`, `src/utils/constants.py`, `src/trading/market/quote_consistency.py`와 메인 loader의 값별 출처를 목록화한다. 익절 네 값은 한 버전의 policy receipt에 incumbent 값·원천·범위·hash를 기록하고 fast/normal이 같은 snapshot을 소비하게 한다. 공유 품질값은 기존 owner의 hash를 참조하며 복제하지 않는다. | 선택 env·기본값·operator lock·실제 PID의 유효값을 각각 구분. 모든 축에 단위·비교 연산자·세션·source hash·consumer ID가 있고 미상 출처는 `source_gap`이다. 고정값 동작과 stop 우선순위는 동일. |
| P1. 판정 전 구간 생산 | `src/engine/sniper_state_handlers.py`와 기존 `src/engine/scalping/trailing_exit_decision.py` 주변에 포지션 시작, peak 갱신, arm 전/후, strong/weak 전환, 유효 bid 결손/회복, 후보 경계 접근, trigger·token의 bounded 이벤트와 원천 참조를 남긴다. 후보 grid와 필요한 관측 해상도를 **수집 전에 고정**하고, 전체 250ms tick 무제한 저장 대신 그 grid의 첫 crossing을 재현할 수 있는 간격·경계 coverage를 증명한다. | open/다른 규칙 청산/미발동도 censored 분모에 포함. 후보 arm·crossing 구간의 원천이 빠지면 replay 부적격; `0`·미발동으로 보간하지 않음. 타입별 `0B/0D`·REST 수신 시각, 종목·route·세션, 점수 생성·유효 시각과 평가 시각을 분리. |
| P2. 주문·결과 조인 | `sniper_trade_review_report.py`, `sniper_execution_receipts.py`, `sniper_post_sell_feedback.py`, `holding_exit_observation_report.py`의 기존 포지션·attempt/cycle·SELL order/fill 키로 직접 신호와 terminal을 연결한다. | `COMPLETED + valid profit_rate` 전체 ID = 적격 + 사유별 제외 ID. full/partial, 실거래/sim/probe/CF, 정확 비용/결손, 직접 fill/잔고대사, 정확 fill 시각/partial horizon을 분리. 사후 추가 상승은 진단이며 비용 후 반사실 이익이 아님. |
| P3. 장후 마지막 소비 | 기존 full monitor snapshot 순서의 `trade_review → post_sell_feedback → holding_exit_observation`을 source/hash 단위로 검증하고 `trailing_threshold_readiness`에 **네 수익축 + 모든 유지 운영축**의 qualified IDs, 결손 사유, 첫 crossing coverage, incumbent effective value/hash를 출력한다. `holding_exit_sentinel`·장후 summary는 원본 보고서 hash와 `source_gap|ready_for_research`만 소비한다. | 보고서가 없거나 늦거나 이전 hash면 stale 차단. 보고서 포인터·경고만으로 `candidate_value` 또는 live 적용 권한을 만들지 않음. 원천일/정책 적용일/세션/venue를 분리하고 새 자연 PID·신호 표본을 확인. |
| P4. 소비 계약 검사 | 값별 `producer → artifact → last consumer → effective runtime key` 표와 자동 대사기를 기존 report/verify 경로에 붙인다. 원천 보정으로 바뀐 생산자부터 마지막 소비자까지만 재생성한다. | 축별 `connected|source_gap|report_only|selected|pid_consumed` 상태를 혼용하지 않고, 선택 정책 hash·bootstrap env·PID cwd/env·runtime 판정 receipt의 값이 일치해야 소비 완료. 장후 terminal/strict handoff 실패는 이전 PASS로 대체하지 않음. |

`P0~P4`는 **현행값의 연결 수리**다. 장후 후보 계산이 가능해져도 승인된 정책 선택·다음 PREOPEN·실제 PID·자연 체결·비용 후 성과는 별도 단계다. 새 자동화 stage/wrapper가 꼭 필요하다면 기존 snapshot owner에 붙이는 방안과 영향 받은 운영 문서·체크리스트를 같은 변경집합에서 먼저 검토한다.

## 4. 불필요한 임계치 정리 결정

| 대상 | 판단 | 계획된 정리와 확인 |
| --- | --- | --- |
| `SCALP_TRAILING_LIMIT=0.5` | live 공통 판정 독자 0; 강/약 값으로 대체 | **삭제 대상.** live `TRADING_RULES`·bootstrap/문서·fixture 참조를 제거. `src/model/models_old/scalping_simulation.py`의 보존된 과거 모델은 archive 재현용으로 분리 표기하고 live 소비자로 계상하지 않음. |
| `AI_HOLDING_FAST_REUSE_CRITICAL_SEC=5`, `NORMAL_SEC=12` | 기본 45/180초에서는 동적 하한 47/182초가 우세하다. 최대 재평가 간격을 과거의 독립 하한보다 낮추면 재사용 시간은 그 간격을 따르게 된다. | **삭제.** 2026-09-25 사용자 지시로 독립 설정·런타임 조회·장후 운영축을 제거하고 `dynamic_max_cd+2`만 남긴다. 이후 cooldown 변경은 이 결합 동작을 함께 검토한다. |
| fast 넓은 스프레드 `min(warn_gap_bps, warn_gap_bps)` | 동일 값을 두 번 비교하는 계산 중복 | **중복 계산 삭제 대상.** 80bp 소비는 유지하고 결과 동등성 확인. |
| `QUOTE_CONSISTENCY_OK_GAP_BPS=30` | 현행 익절은 `ok`와 `warning`을 모두 허용하고 직접 재확인 경계는 80bp다. 30bp는 공유 quote 분류/다른 전략에 독자가 있음 | **익절 후보 목록에서는 제외**, 공유 코드·env는 유지. 전역 삭제는 모든 다른 독자의 행동·보고 계약을 대사한 별도 변경으로만 수행. |
| `BLOCK_ENTRY_ON_DIVERGENCE`, fast stop enable, 과거 AI decay/stagnation 임계치 | 각각 entry/stop 또는 observation-only 소유. 현재 익절 SELL의 조정축 아님 | 익절 tuning/policy에서 제외. 기존 소유자의 설정·관측을 이 계획으로 삭제하지 않음. |
| WS/REST 신선도, 80bp, NXT 0B/0D, AI TTL, REST 간격·제한, polling, `SCALP_SAFE_PROFIT` | 현재 신뢰가격·점수·평가시각·공유 sim/real 감시에 실제 영향 | **유지.** 측정 대상에는 넣되 품질·안전 기준 완화는 수익률만으로 자동 적용하지 않음. 동일 숫자 45초의 AI TTL과 재평가 최대간격도 의미가 달라 합치지 않음. |

삭제는 소스 코드 독자·bootstrap 생성자/loader·선택 env·오퍼레이터 lock·문서·회귀 fixture를 역검색해 영향 범위를 확정한 뒤 수행한다. 이미 선택된 immutable 릴리스를 제자리 수정하지 않는다.

## 4.1 격리 작업트리 구현 및 남은 증명

`/home/ubuntu/KORStockScan-worktrees/scalp-trailing-lineage-20260924`에서 익절 네 값의 bootstrap receipt·값 hash·런타임 관측, 운영값/출처의 bounded grid 전이, 완료 및 열린 포지션의 별도 분모, 장후 보고서의 정책 manifest 대사, sentinel·summary의 보고서 hash 소비를 추가했다. `SCALP_TRAILING_LIMIT`와 중복 80bp 계산은 제거했다. 변경은 보고 전용이고 후보값과 live 적용 권한을 만들지 않는다.

첫 리뷰에서 보유 AI 재사용 5/12초 값의 삭제가 다른 cooldown 설정과 결합할 때 동등하지 않음을 확인해 유지했다. 전이 이벤트의 dict는 로거가 문자열로 바꾸므로 공백 없는 JSON으로 기록하고 장후 trade review에서 명시적으로 복원한다. 열린 포지션은 현재 KST 날짜의 DB census에서만 전체 분모로 표시한다. 과거 날짜에 현재 DB 상태를 소급 적용할 수 없어 해당 재생성은 `source_gap_historical_open_census_not_reconstructible`로 남긴다.

2026-09-25 후속 결정은 위 독립 재사용값을 삭제하고 cooldown 기반 하한만 사용하는 것이다. `QUOTE_CONSISTENCY_OK_GAP_BPS=30`은 공유 시세 `ok`/`warning` 분류와 다른 소비자의 판단에 영향을 주므로 익절 조정 후보에서만 제외하고 기존 공유 기준을 유지한다.

재리뷰에서 관측 이벤트의 텍스트 출력이 기본적으로 억제됨을 확인했다. `trade_review`는 정식 `pipeline_events` JSONL과 late sidecar의 보유·신호·주문·체결 이벤트를 읽고 텍스트 중복을 제거한다. 원본 분할이 없거나 관측 계산이 실패하면 포지션별 `source_gap`으로 남긴다. 공유 시세·AI 운영값은 dated bootstrap env와 일치하는지 보고서에서 대사하되 코드 기본값과 실제 PID의 일치는 별도 증명으로 둔다.

커밋 후 재리뷰에서는 원본 파이프라인 분할의 hash가 빠진 점을 보완했다. `trade_review`가 원본·late 파일을 스트리밍하면서 논리적 내용 hash와 파일 변경 여부를 봉인하고, 완료 projection 및 `holding_exit_observation`의 포지션 원천 참조로 전달한다. 분할이 읽는 동안 바뀌거나 JSON 원천이 손상되면 후보 재현은 부적격이다.

현재 자료만으로 첫 후보 crossing과 주문 체결의 반사실 비용을 증명할 수 없다. 표본 상한, 장중 수집 시작 이전, 자정 넘어온 포지션, 누락된 quote/AI 원천은 replay 적격에서 제외한다. 새 릴리스의 실제 PID 소비와 자연 실거래 표본이 생기기 전에는 `candidate_value=null`, `paired_replay_eligible_ids=[]`이며, 장후 summary의 연결 상태는 독립적인 직접 경제성 PASS가 아니다.

## 5. 연결 수리 뒤 장후 튜닝 고도화

장후 생산자는 축마다 현재값과 후보값을 **동일 포지션·같은 원천 경로**로 replay한다. 시작값은 arm 전 경로, 강점수는 점수 생산/TTL/provider, 강·약 폭은 첫 bid crossing과 후속 고점, polling은 source→판정→주문 지연 및 부하, 품질값은 false accept/reject와 재확인·실패 주문을 각각 비교한다. 비교에는 실제 체결 가능 수량·부분체결·세금/수수료·슬리피지·기회비용, 순이익/EV, tail과 독립 최신일 holdout을 포함한다. PREMARKET·REGULAR·통합 AFTERMARKET과 KRX/NXT route를 분리한다. 결손 구간은 제외 ID와 첫 blocker를 남기고, 표본 미성숙은 `candidate=null`로 둔다.

익절 전용 네 축과 polling/NXT 입력 품질축은 각자의 권한 범위에서 **한 번에 한 축**만 후보로 낸다. 공유 quote·REST·AI 운영축은 장후 보고서가 같은 계약의 진단·후보를 만들되, 각 기존 owner의 안전/부하/원천 품질 검사를 통과해야 한다. 특히 stale/conflict 허용 확대, hard/protect/emergency 지연, broker/account/order/cooldown·provider·수량/자본 변경은 익절 EV만으로 허용하지 않는다. `SCALP_SAFE_PROFIT`은 real 보유 AI 감시와 sim 소비를 함께 비교하기 전에는 익절 전용 정책으로 승격하지 않는다. 적격 후보가 없으면 incumbent carry다.

2026-09-25 후속 [4축·3시장 튜닝 설계안](./scalp-trailing-four-axis-market-tuning-and-historical-evidence-plan-2026-09-25.md)은 위 한 축 후보 원칙을 연구 단계에서 재검토한다. 시작·점수·약폭·강폭의 상호작용이 입증되면 하나의 버전·하나의 canary로 묶은 복합 후보를 허용하는 방안을 제안한다. 이 설계안만으로 후보값이나 live 적용 권한이 생성되지 않으며, 운영 입력 품질축의 공유 owner 경계는 유지한다.

후보 선택을 구현할 때에만 exact-date policy와 다음 PREOPEN bootstrap의 단일 값 매핑, 이전 값·hash 롤백, PID 소비 및 post-apply version 귀속을 연결한다. 날짜는 정책 버전의 유효일이지 트레일링을 켜는 런타임 날짜 gate가 아니다. 계산/추천→선택→bootstrap→실제 PID→자연 SELL→비용 후 EV·순이익은 별도 영수증으로 판정한다.

## 6. 구현 리뷰와 수용 게이트

1. **P0~P4 연결:** 네 직접 임계치와 유지 운영축 모두 원천/단위/비교값/정책 hash/위치/last consumer가 명시된다. 무효·오래된 AI/호가, 다른 NXT 종목·route, REST timeout, 신호 없는 완료, 완료 없는 신호, partial fill과 sync-only를 각각 적격에서 제외·분류한다. `effective_branch_only`를 원천 증명으로 승격하지 않는다.
2. **삭제 동등성:** 제거 대상마다 호출자·문서·환경 역검색과 동일 입력 fast/normal replay를 남긴다. 30bp·보호 lock·공유 안전축은 별도 owner 변경 없이 유지하며 stop 우선순위와 익절 `trailing_peak_worsen_floor`는 동일하다.
3. **영향 검증:** 구현 시 최초 회귀를 보존하고 수리→재리뷰를 반복한다. 관련 판정·호가·AI·보고서·bootstrap/strict consumer의 targeted pytest/compile, wrapper 변경 시 `bash -n`·계약 검사, `git diff --check`를 통과한다. Kiwoom 요청/parser/recovery 변경이 생기면 AGENTS의 공식 reference gate를 먼저 수행한다.
4. **운영 판정:** 코드 PASS, 장후 source/terminal, 선택 릴리스, exact-date env, 실제 PID 소비와 새 자연 비용 후 효과를 각각 기록한다. 9/28 `HoldingExitPositionOutcomeLineageClosure`의 새 자연 표본은 이 계획의 첫 수용 입력이며, 과거 결손 영수증을 소급 합성하지 않는다. 실제 적용은 검증된 owner·정책 경계에서 별도로 판정한다.

## 7. 9/25 운영 입력 민감도 작업본

[운영 입력 재생·리뷰 기록](../audit-reports/2026-09-25-scalp-trailing-operational-input-replay-review.md)에 17개 유지 운영값의 세 시장별 관측 경계 비교, 평가별 shadow hash와 결손 격리, 공유 quote/REST·보유 AI 소유자 검토 상태를 기록했다. 이 계산은 행동이 바뀌는 후보의 비용 후 반사실 손익을 채우지 않으며 정책 후보·실제 적용을 생성하지 않는다. 선행 4축의 후행 경로 검열과 엄격 완료 모수 0건도 별도 OPEN 증거로 유지한다.
