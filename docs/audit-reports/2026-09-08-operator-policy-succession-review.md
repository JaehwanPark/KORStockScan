# 전략 operator lock 자동 정책 승계 구현·잔여 범위

기준: 2026-09-08 KST. 사용자가 전체 lock에 대해 검증 조건 충족 시 자동 정책 승계를 구현하도록 명시 지시했다. 그 승계 권한은 `user_authorized_strategy_lock_auto_succession_20260908`이며 최초 적용 가능일은 다음 PREOPEN인 2026-09-09다. 기존 9/8 적용 자료·원본 lock·operator env를 수동 수정하지 않는다. 안전·명시적 중지/veto·provider/호출 예산·custody·수량/cap·mutex 권한을 포함하지 않는다.

## 판정

기존 경제성 생산자가 있는 전략의 자동 승계와 기동 소비 경로를 구현했다. 후속 사용자 지시에 따라 `weak_pullback_entry_block_runtime`은 기존 Entry gate/recheck, `profit_stagnation_exit_runtime`은 기존 holding/exit의 관리 component로 통합했다. 이어 사용자가 **정확한 replay와 실제 체결 품질 검증 후 다음 PREOPEN의 제한된 canary까지 자동화**하도록 승인했다. 아래 최종 보완은 두 component의 한 단계 후보에 이 최초 적용 경로를 추가한다. 무제한 조건 탐색·무표본 승격·보호 lock 해제가 아니며 코드/배포/PREOPEN/PID/실수익은 각각 별도 상태다.

## 전체 JSON lock 대사

25개 파일 전수를 분류했다. 역사적 `enabled=false` 4개를 재활성화하지 않는다. 같은 family의 holding context 두 파일도 각각 센다. 실행 mutex·주문 custody lock·widget/episode manual veto는 전략 threshold lock이 아니므로 변경하지 않는다.

| 분류 | 건수 | 항목/처리 |
| --- | ---: | --- |
| 직접 경제성 승계 연결 | 2 | score65_74 recovery, scalping pyramid min-profit. 기존 경제성/AI/단일 stage 검증 후 exact key 승계 |
| 기존 정식 Entry owner 통합 연결 | 5 | early_accel, pre_submit_liquidity_relief, weak_context_late_entry, scanner_real_source_guard, score strong_micro. 정식 owner 선택 시 기존 `_close_*_for_live_owner` 계약 사용 |
| 기존 owner 관리 component 통합 | 2 | profit_stagnation_exit → holding/exit, weak_pullback → Entry gate/recheck. 기준값 보존에는 EV floor 없음. 후속 승인으로 exact replay + 실제 full-fill 품질 → 제한된 최초 canary → 실제 관측 profile 승계까지 연결 |
| 안전·운영·source-only 유지 | 11 | buy/sell 시간 guard, holding context 2개, quote consistency, latency safety relief, sim budget/window, entry-price gap profile, real pyramid quality/protective guard, rising-missed baseline bridge |
| 혼합 overlay | 1 | persistent operator overlay. 승인된 전략 exact key만 승계; 나머지 키 유지 |
| 비활성 이력 | 4 | buy-time disable, entry recheck 7/3, late-price drift, soft-stop grace. 복구/활성화 금지 |

AVG_DOWN의 기존 단일 pressure 경제성 계약도 같은 승계 등록부에서 지원하지만 현재 해당 독립 lock은 없어 위 직접 lock 수에 추가하지 않는다. 기존 승인 생산자가 없는 전략의 독립 파라미터 재튜닝을 완료했다고 주장하지 않는다.

## 구현 및 리뷰 보완

- 공통 계약은 `src/engine/automation/operator_policy_succession.py`에 둔다. engine root 신규 모듈 없음. lock 원본 대신 날짜별 runtime manifest에 self-hashed 승계 receipt를 보존한다. predecessor ID, 후보 digest, 적용일, 단계, 이전 값, 승계 값, 관련 operator source를 결속한다.
- PREOPEN의 ordinary candidate 검증을 통과한 뒤에만 역사적 `explicit_close_required`를 전략 승계로 대체한다. score는 현재 유효 lock profile(기존 micro floor 포함), 실제 비용 차감 book, 앞쪽 학습/뒤쪽 검증, 양수 EV·일평균 순익·자본시간 효율을 기존 경제성 함수로 재검증한다. 건당 수익 증가·별도 1.1% 문턱을 추가하지 않는다.
- PYRAMID는 기존 fixed-exit 경제성 grid를 다시 계산하고 current-value, clean cumulative window, 한 번의 bounded step, source-quality, AI evidence identity를 확인한다. AVG_DOWN은 기존 candidate contract 검증을 유지한다. 단순 `selected=true`·positive 숫자·sim 표본은 새 승계 권한이 아니다.
- 기존 혼합 overlay의 후행 덮어쓰기를 막는다. `src/run_bot.sh`가 기존 operator 파일을 읽은 **후**, 검증 receipt의 exact 전략 key만 다시 읽는다. verifier와 PID 기대값도 같은 계약을 사용한다. 원본 operator 파일을 덮어쓰거나 shell 명령을 자료에서 실행하지 않는다.
- 다음 날 sample gap/hold 시 마지막 승인 정책을 유지하고, 같은 날 재실행 시 승인 정책을 고정한다. 원본 lock 값이 재등장하지 않는다. 관련 새 운영자 지시·receipt 변조·파일/manifest 불일치는 명시적 실패다. 무관한 operator key 변경과 이전 dated 지시의 정상 만료는 정책 승계를 막지 않는다.
- scope/stage 오분류, 기존 lock metadata 때문에 정식 Entry owner가 누락되는 경로, raw micro floor 의존성, source-only/안전 key 유출을 추가 리뷰에서 보완했다. 기존 정식 Entry owner가 보조 lock 5종을 통합하는 경로를 유지한다. 그 scope의 정책 변경과 무관한 별도 보호·중지 guard는 자동 해제하지 않는다.
- runtime env와 manifest 파일은 각각 임시 파일/fsync/replace로 publish한다. 혼합 세대는 receipt의 실제 env 값 비교로 거절한다. 이 구현은 장중 hot mutation·provider 호출·주문·bot 재기동을 하지 않는다.

## 검증

최종 8개 관련 pytest 모듈 **569 passed (13.95초)**. 승계 전용 회귀 38개와 기존 PREOPEN/score/PYRAMID/AVG_DOWN/summary/wrapper/location gate를 포함한다. 영향 Python compile, launcher `bash -n`, 신규 코드 Ruff 및 공유 파일 fatal-rule 검사, 문서 print-only parser, `git diff --check` PASS. parser 35개 항목 중 `OperatorPolicySuccessionAcceptance0908`은 1회다. 현재 operator env 371개 key의 읽기 전용 파싱도 통과했다. 테스트는 격리 디렉터리/합성 경제성에서 수행하며 실제 9/9 승계나 수익을 뜻하지 않는다. baseline test의 이전 lock 유지·안전 revert 동작을 보존한다.

마지막 리뷰에서는 여러 export assignment에 포함된 OFF veto 누락 가능성을 보완하고, 승계 대상 shell 표현식을 추정 실행하지 않도록 했다. AVG_DOWN hold/carry에서는 기존 경제성 계약의 provenance env도 함께 유지하여 다음 날 과거 overlay가 복귀하지 않도록 했다. 확인된 공통 승계/등록 owner/직접 consumer 범위의 미해결 코드 finding은 0건이다. 이는 아래 두 경제성 owner 계약 미완료를 닫는 표현이 아니다.

검토 범위는 공통 승계·등록된 직접 owner·기존 통합 hook·launcher/verifier/summary다. 이 범위의 코드 finding과 위 두 개 owner 계약 OPEN, 배포, 자연 PREOPEN/PID, 실현 순익 수용은 각각 별도 상태다. 전체 요청에 대해 미해결 0 또는 완료로 보고하지 않는다.

## 남은 범위와 자연 수용

실행 owner는 현재 일일 체크리스트의 `OperatorPolicySuccessionAcceptance0908` 하나다. 아래 후속 통합으로 두 component의 관리 책임은 정해졌다. 미실행 조건의 최초 승격 계약과 자연 PREOPEN/PID/경제성 수용은 여전히 별도다. 기존 lock 삭제, 무관한 score 승인, source-only 결과만으로 이 잔여 범위를 닫지 않는다.

자연 PREOPEN의 candidate 부족/정상 유지와 코드 결함을 구분한다. 등록된 경로는 사용자 재승인 없이 기존 scheduled PREOPEN에서 조건부 실행되지만, merge/deployment·실제 PID 소비·submit/fill/terminal/net 개선은 아직 확인하지 않았다. 운영 report 재생성, provider 호출, 현재 env/lock 변경, 재기동, 커밋·푸시·외부 sync는 수행하지 않았다.

## 9/8 후속: 기존 Entry·holding owner 통합

사용자가 권고한 기존 owner 통합을 구현하도록 지시했다. 신규 독립 calibration family, AI route, 주문 권한, 실전 노출 시험을 만들지 않는다. 코드 소유 위치는 `src/engine/scalping/strategy_owner_components.py`이며 정책 승계는 기존 automation module, source는 기존 lifecycle materialization/daily threshold report, 소비는 기존 PREOPEN/launcher/sniper 경로다.

- 구조 통합: 다음 PREOPEN에서 exact effective operator 값과 provenance를 기존 owner component receipt로 보존한다. 두 옛 lock은 독립 stage owner를 더 이상 선점하지 않는다. 원본 lock/env는 수정하지 않는다. 명시 OFF/manual/safety veto, candidate safety revert와 family filter는 유지한다. baseline migration 자체에는 새 표본·양수 EV·AI 재승인 문턱을 두지 않는다.
- 실행 동등성: 아직 경제성 정책이 없으면 기존 `_rule_*` 판정과 enable, 횡보 anchor/확인시간, trailing 우선순위와 holding-flow 관여를 유지한다. 단순 AI BUY로 weak-pullback 조건을 건너뛰지 않는다. 미래 scoped 완화가 입력 누락을 통과시키지 않도록 기존 micro source 차단을 보존한다. 손절/호가 freshness/수량/주문/provider는 조정 키가 아니다.
- 원자료: 필요한 entry/submit/exit 시점에 두 component의 실제 설정과 다른 runtime rule context hash를 기록한다. frozen rule cache와 제한된 관측 stage를 사용하여 매 tick 전체 설정 재계산·무제한 로그 증가를 피한다. 계측 context 손상은 source-only 결손이며 주문 예외가 아니다. 같은 lifecycle의 profile/context 변경은 비교 표본에서 격리한다.
- 기존 장후 producer: signed `main_scalping_lifecycle_paired_daily_v2` → daily/rolling `strategy_owner_component_economics` → PREOPEN의 원본 재구성/동일 source hash 검증. 실제 완료·full-only·비용 및 명목 대사·자본시간만 비교한다. partial, sim, censoring, scale-in 혼합, 중복 identity, 비용/정책 출처 결손은 제외한다. 실제 체결가에 포함된 slippage는 다시 빼지 않는다.
- 조건 변경: 실제 실행 이력이 있는 인접 profile 중 동일 venue/session, 다른 component와 runtime context를 비교한다. 기존 조건 한 개만 bounded step으로 변경하며 enable·slippage 가정·AI score prior는 검색하지 않는다. 두 정책 각 20개 실제 표본, 공통 날짜 분할의 앞/뒤 각 10개 이상, 날짜 구성 일치를 요구한다. 앞/뒤에서 후보의 양수 net, 일평균 net와 자본시간당 net 개선을 확인한다. 건당 수익률 상승이나 일률 1% uplift를 요구하지 않는다. 이는 bounded observational comparison이지 인과적 수익 보장이 아니다.
- 소비/충돌: 승인 profile은 정확한 venue/session/context에만 적용한다. 같은 stage의 다른 변경은 새 component 승계를 보류한다. 다른 component가 달라지는 경우도 이전 비교를 무조건 재사용하지 않는다. same-day freeze, 이후 source gap에서 마지막 승인 정책 유지, operator source 변경 시 명시적 reconciliation, manifest/실제 env 불일치 fail-closed를 함께 검증한다. summary는 managed component와 독립 selected family/PID 소비를 분리한다.

### 후속 검증 및 한계

최종 10개 관련 모듈 **977 tests PASS**, 별도 Entry/holding 안전·동등성 **40 tests PASS**, 합계 **1,017 tests PASS**다. 계측 예외의 주문 경로 전파 방지, 순수 contract 검사에서 profile 상태를 변경하지 않도록 하는 보완, NXT 실제 세션명 보존과 정확한 stock scope 소비도 포함한다. 공유 세션의 venue/session 보완을 보존하고 현재 파일로 재검증했다. Python compile/Ruff, launcher `bash -n`, `git diff --check` PASS. print-only parser는 34개 항목 중 `OperatorPolicySuccessionAcceptance0908` 1개, Due 9/9를 확인했다. 25개 실제 JSON lock 분류와 두 component의 다음 PREOPEN effective profile 유효성도 읽기 전용으로 대사했다. 전체 보고서 재생성·실주문·원본 env/lock 변경·재기동·커밋/푸시·외부 sync는 하지 않았다.

구조 통합·관측 profile 승계·직접 producer/consumer의 검토 범위에서 추가 미해결 코드 finding은 0이다. 아래 최초 승격 계약 OPEN, 배포 및 자연 경제성 수용까지 결함 0/전체 완료라고 주장하는 판정은 아니다.

`baseline_only_no_observed_challenger`는 다른 조건을 아직 관측하지 못한 상태다. 동일 기본값의 거래만 늘어나면 자동으로 최초 새 조건이 승인되지 않는다. 이 경우 source/기존 owner의 first-use 경제성 경로를 즉시 검토 대상으로 노출하며, rolling window로 도달할 수 없는 20일 누적 대기 문턱을 추가하지 않는다. 미실행 조건의 replay/최초 bounded 적용 계약은 이 observed-profile 승계 경로가 대신하지 않는다. 따라서 **통합·기존 관측 정책 승계의 코드 수리와 전체 새 조건 자동 탐색/최초 승격 완료를 구분**한다. natural/최초 승격 잔여는 기존 체크리스트 ID 한 곳에서 추적한다.

## 최초 replay·제한 canary 승인 후 최종 보완

위 1,017 PASS와 최초 승격 계약 OPEN은 후속 승인 전 기록이다. 이번 구현은 `src/engine/scalping/strategy_owner_replay.py`를 기존 owner의 source-only helper로 둔다. 새 engine-root module, 독립 alpha family, 주문 경로 또는 cron은 만들지 않았다.

### 보완한 결함

- Daily 한 날짜 book이 PREOPEN으로 전달되어 2일 이상 검증을 충족할 수 없던 경로를 수정했다. canonical/phase calibration 모두 기존 `rolling_20d` book을 소비한다.
- 같은 날짜에 baseline/challenger가 동시에 실행돼야 하는 조건을 제거했다. 각 실제 profile의 시간순 앞/뒤 구간을 따로 비교한다. 서로 다른 PREOPEN 버전의 실제 거래도 검증 가능하며, 인과적 수익 증명의 의미는 아니다.
- 같은 적용 범위의 합격 후보가 여러 개면 전부 탈락시키던 경로를 학습 구간 순익/자본 효율·고정 ID 정렬로 수정했다. venue/session/context/다른 component/score-recovery cohort를 source와 실제 소비까지 일치시킨다.
- 로그 회전·보존 등 검토된 7개 비판단 설정만 context hash에서 제외했다. 미지의 설정이나 전략·가격·안전 조건을 광범위하게 제외하지 않는다.
- 미실행 challenger의 실제 거래부터 요구하던 순환 조건을 별도 최초 canary 경로로 해소했다. replay만으로 정식 승인하거나 모든 보호 lock을 자동 해제하지 않는다.

### 자동 연결과 제한

`기존 Entry/holding 결정의 seed → 기존 bounded frame capture → postclose Daily CLI의 격리 replay → signed replay + signed real lifecycle → rolling book → PREOPEN 원본/hash 검증 → component receipt/env → 기존 launcher/runtime → 실제 profile 경제성 재검증`

- 첫 가설은 기존 weak-pullback의 `MIN_MICRO_POSITIVES` 한 단계 감소와 기존 low-profit-stagnation의 `MIN_HOLD_SEC` 300초 감소다. 현재값에서 허용된 한 key만 변경하며 enable, 비용 가정, 수량·cap·AI 권한·hard safety는 고정한다. 별도 1.1% 수익률 문턱은 없다.
- Entry는 실제 AI 재검증 통과 후 weak-pullback으로 막힌 exact attempt에서만 수집한다. 같은 promotion/record·거래일의 재시도는 새 경제성 표본이 아니며 첫 native attempt를 보존한다. 현재 AI 상태와 실제 매매 루프가 이미 사용한 시장 국면도 추가 호출 없이 기록한다. 미래 국면은 거절하고, 누락 AI 상태를 이전 보유 상태에서 빌리지 않는다. 기존 약한 진입 predicate와 전체 holding/exit engine을 재현한다. executable ask·단일 limit 전량 깊이 기반의 **조건부 quote CF**이며 후행 주문/계좌 guard 통과나 broker receipt를 재현했다고 주장하지 않는다. 실제 canary에서도 후행 guard가 그대로 실행된다.
- Holding은 실제 첫 보유 상태를 고정한다. 각 arm의 상태·AI 요청·비용·terminal을 독립 처리하고 hard/protect/emergency 경로를 유지한다. 다른 owner의 ADD를 억제하지 않으며 모델 범위 밖 ADD/부분 청산/외부 입력 결손이면 해당 replay를 제외한다. 최초 seed의 실패를 나중의 유리한 시점으로 교체하지 않는다.
- 수집은 하루 owner당 4개, 합계 8개 seed이며 기존 shared capture의 active 8개·연속 frame/byte bound를 유지한다. postclose는 합계 provider 요청 8회/대상일, replay 300초 예산, 날짜별 mutex와 원자 checkpoint를 사용한다. 호출 전 예산을 먼저 예약하므로 중단/결과 미상의 요청도 자동 중복 호출하지 않는다. 미상 시 budget charge는 상한 예약이며 실제 과금 호출 횟수 주장이 아니다. 동일 seed terminal 실패/거절은 반복 호출하지 않으며 손상 checkpoint로 예산을 초기화하지 않는다. source-only checkpoint는 terminal 산출물로 승격하지 않는다. raw seed는 한 번만 저장하고 text payload에는 identity만 남긴다.
- 최초 canary: exact paired replay 10건 이상·2일 이상, 시간순 각 절반 5건 이상; 동일 profiles/context/venue/session/score cohort의 실제 완료·full-fill·비용 대사 20건 이상·2일 이상, 각 절반 10건 이상과 양수 합계 순익을 요구한다. replay 양쪽 구간에서 후보 순익이 양수이고 기준보다 크며 자본시간 효율도 개선돼야 한다. 건당 큰 수익이나 모든 MFE horizon은 요구하지 않는다. 현재 owner별 하루 4개 cap 아래에서는 양쪽 5건을 채우는 데 최소 4개 유효 거래일이 필요하다. 이는 유한한 검증 구간이며 실제 체결이 계속 없으면 사용자 승인 조건인 real 품질을 충족하지 못한 것으로 남긴다.
- 합격해도 owner당 한 가설·한 cohort만 최대 7 calendar days 적용한다. same-stage 새 변경 및 서로 충돌하는 component는 보류하며 미적용 trial ID를 소진하지 않는다. 같은 날 정책은 고정하고, pinned replay/real 원천이 없어지거나 바뀐 경우·실제 충분 비교의 개선 미달·기간 만료에는 다음 PREOPEN에서 기준으로 복귀한다. 동일 baseline/profile/cohort trial은 새 보고서 hash만으로 재개하지 않는다. 실제 양쪽 profile의 별도 경제성 검증을 통과해야 정식 정책으로 승계한다.
- `first_use_evaluation.cohort_checks`는 replay 표본, 실제 체결 표본, 구간별 순익/효율 미달, 이미 종료한 trial을 구분한다. baseline-only는 구현된 최초 연구 경로의 입력 대기이며 즉시 수동 계약 수리/maintenance를 요구하지 않는다. 보호/veto/운영 lock과 기존 정식 Entry/score/PYRAMID 승인 경로는 그대로다.

### 검증과 잔여 상태

최종 14개 관련 pytest 모듈 **995 PASS (53.91초)**, 별도 weak-pullback/청산 안전 회귀 **24 PASS**, 합계 **1,019 PASS**다. 생산 문자열 wire·중첩 BBO 수량, exact source 재구성, 최초 canary PREOPEN/launcher/runtime, 만료·source pin·중복 trial·same-day freeze, 호출 전 crash reservation, 원본 lock 보존, 격리 holding/시장 국면 cutoff와 기존 AVG_DOWN 경로를 포함한다. Python compile, 신규/관련 helper Ruff 및 공유 모듈 fatal-rule 검사, launcher/postclose `bash -n`, `git diff --check`를 통과했다. print-only parser는 34개 항목과 `OperatorPolicySuccessionAcceptance0908` 1개를 확인했다. 구현→리뷰→수정→재검증을 반복했으며 이 요청의 코드·계약 검토 범위에서 미해결 finding 0이다. 전체 저장소 무결함이나 배포/자연 경제성 완료를 뜻하지 않는다.

현재 env/PID/원본 lock, 운영 산출물 및 설치 cron은 변경하지 않았다. 장후 전체 재실행·provider 실제 호출·커밋/푸시·재기동도 하지 않았다. 자연 source가 없는 과거 날짜를 복제하지 않는다. 9/9 PREOPEN은 기준 통합/배포 receipt 확인 시점이지 최초 canary의 강제 시작일이 아니다. 필요한 새 원천이 검증된 뒤 정규 PREOPEN에서 자동 판단하며 `OperatorPolicySuccessionAcceptance0908`이 배포·자연 수집·실제 소비·종료/정식 승계·비용 차감 순익을 계속 소유한다.
