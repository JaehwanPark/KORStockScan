# 기계 ENTER + compact AI 보조심사 장후 구현·리뷰

기준 시각: `2026-09-14 17:48 KST`
구현 지시: [통합 workorder](../proposals/machine-compact-auxiliary-postclose-implementation-workorder-2026-09-14.md)
권한: 장후 source/report/선정/publisher/consumer 자동화 보완. 현재 PID·수동 env·주문·threshold·hard safety 변경 없음.

## 1. 판정

코드 구현과 검토 범위는 `PASS`, 자연 성과와 다음 PREOPEN/PID 소비는 `OPEN`이다. 장중 frozen 정책이 compact가 아니거나 compact 자연 호출이 없으면 그 날짜의 legacy 결과를 compact 성과로 섞지 않고 incumbent compact를 유지한다. 장후 결과는 exact compact partition과 비용후 성숙 경로가 있을 때만 다음 거래일 등록 prompt variant 선정에 영향을 준다.

## 2. 최초 결함과 보완

| WP | 최초 결함 | 보완·현재 판정 |
| --- | --- | --- |
| WP0 | 선택 release는 compact v3 코드이나 현재 PID는 이전 release에서 시작해 당일 frozen prompt를 소비 | 현재 PID 불변. 새 코드는 20:10 장후와 다음 PREOPEN 경로만 대상으로 함 |
| WP1 | 서로 다른 compact generation 또는 한 손상 scope가 섞이면 전체 측정을 막는 전역 gate | `version×venue×session×machine bundle` partition, exact issued prompt hash/variant, partition ID와 독립 allowed 상태를 추가. 정상 partition만 #82로 전달 |
| WP2 | `20 호출 + missed-VETO/dangerous-PASS 건수 차이`가 비용·성숙·분모 차이를 반영하지 않음 | `compact_auxiliary_economic_selection_v2`로 교체. 비용후 경로와 PASS/VETO별 분모·rate·tail·경계 도달시간을 분리하고 결측을 null/제외로 보존 |
| WP3 | legacy R0–R3 독립 selector 연구가 compact 보조심사와 같은 역할처럼 보일 수 있음 | #80에 legacy=`offline_independent_selector_prompt_research_only`, compact=`machine_enter_post_selection_risk_adjudication`를 명시. 자연 compact 평가는 Provider replay로 합성하지 않음 |
| WP4 | publisher/consumer가 단순 aggregate를 신뢰하고 새 경제성 보존식·source hash를 검증하지 않음 | source manifest와 경제 outcome hash를 publisher가 재계산하며 consumer·strict verifier가 역할/schema/hash/권한을 검증 |
| WP5 | #119/#23에 machine-primary funnel과 legacy recheck 경계가 이미 존재 | 재검증 결과 patch 불필요. machine RECHECK/BLOCK은 legacy #23 eligible로 올리지 않고 ENTER→AI→final guard→broker accepted 분모 유지 |
| WP6 | compact/legacy 역할과 다음 날짜 자동선정 상태가 consumer·runtime summary에 독립 표시되지 않음 | #80 handoff와 runtime summary에 역할·selection·source/economic hash·자동 publisher·현재 PID 미주장을 명시. strict verifier가 필수 receipt 결손을 실패 처리 |
| WP7 | 현재 장중 PID에 새 postclose 코드를 즉시 반영하면 frozen 실행을 바꿈 | 현재 PID 재기동 없음. 검증 commit을 새 immutable release로 배포하고 설치 route의 다음 자연 owner가 소비하도록 함 |

## 3. 확정한 자동선정 계약

- 원천: #74의 exact incumbent compact partition만 사용한다. 다른 버전·scope·bundle·prompt hash 손상은 해당 partition만 제외한다.
- 경제 분모: 비용 계약, `net_target_first|exact_stop_first`, 경계값이 모두 있는 unique machine ENTER + AI PASS/VETO만 포함한다. 호출 수·미성숙·비용 결손은 floor를 채우지 않는다.
- 기본 floor: 경제적 유효20건, 선택 방향의 분모5건, 해당 오류3건, 오류율25% 이상, 반대 오류율보다10%p 이상 높음.
- tail: 비용후 counterfactual PASS 손실이 -1.0% 이하인 material tail이 하나라도 있고 PASS 분모5건이 있으면 risk-specificity variant가 우선한다. 이는 한 큰 손실을 다수의 작은 이익 건수로 가리지 않기 위한 제한이다.
- 분모0: rate는 `null`; all-PASS/all-VETO를 0% 오류로 보간하지 않는다. 충분한 방향별 근거가 없으면 carry한다.
- 권한: selector는 등록 compact variant만 다음 거래일 bundle로 자동 발행한다. 자유문구 생성, 기계 threshold·수량·가격·주문·hard safety 변경 권한은 없다. 수동 사용자 승인은 요구하지 않는다.
- rollback/carry: source 미관측과 source 손상을 구분한다. 미관측은 정상 carry, 손상은 해당 partition 제외/carry다. 현재 날짜 bundle과 PID는 불변이다.

이 조건은 모든 horizon·5/10/20일 동시 gate나 후보 적용 전 실체결을 요구하지 않아 과도한 무기한 차단을 피한다. 반대로 호출20건만으로 바꾸지 않으며, 비용후 작은 순익 빈도와 큰 tail 손실을 같은 단위에서 함께 본다.

## 4. 오늘 자연 원천 읽기 전용 점검

17:45 KST 시점 #74 입력을 새 계약으로 읽었고 파일·정책·Provider를 쓰지 않았다.

- machine capture 2,960: BLOCK 1,758 / RECHECK 1,172 / ENTER_NOW 30.
- entry screen trace 4,604: provider called 95 / not-called 4,509. AI 미호출을 Provider 실패나 AI VETO로 세지 않았다.
- exact snapshot/bundle/action join 2,957, action mismatch 3은 격리 대상이다.
- compact 자연 trace 0: 현재 장중 PID의 frozen 세대가 compact가 아니므로 `not_observed_on_source_date`, `measurement_allowed=false`가 정상이다.
- 비용후 machine case 0: 당일 장후 economic reference가 아직 없어서 2,957건 모두 `full_round_trip_cost_missing`이며 값을 0이나 gross target으로 보간하지 않았다.
- 따라서 successor는 compact v3 carry이고 오늘 이 읽기 전용 점검만으로 opportunity/risk variant, 수익 개선, 현재 PID 적용을 주장하지 않는다.

## 5. 예상 효과와 별도 acceptance

예상 효과는 (1) 과거/손상 source의 전역 차단 감소, (2) 비용 없는 호출 건수 기반 과잉 전환 제거, (3) missed-profit VETO와 dangerous PASS의 서로 다른 분모 공개, (4) 작은 비용후 이익을 보존하면서 material tail을 우선 억제, (5) legacy R0–R3 결과가 compact runtime 선택을 오염시키지 않는 것이다.

이는 코드 계약의 기대 효과이며 실제 이익 증명은 아니다. 다음 자연 compact generation에서 `prompt_version/variant/system prompt hash/machine bundle`, 경제 유효 분모, 자동 selection/carry, next-date bundle, PREOPEN 선택, PID first-use, accepted submit/fill/terminal과 비용후 순익을 순서대로 확인한다.

## 6. 리뷰·검증

- P0~P2 unresolved finding: 0 (본 변경 범위).
- 반례: 정상+손상 compact partition 혼재, compact 미관측, 비용 유효2/호출20, all-PASS 분모0, semantic invalid, material tail 1건, source/economic hash 변조, 기존 frozen migration/carry.
- targeted pytest: 관련 source audit/calibration/publisher/consumer/verifier/live-policy/funnel/recheck/runtime summary 724건과 runtime/replay prompt parity 69건 PASS.
- Python compile, formatter, `git diff --check`, 문서 링크/print-only parser를 최종 commit 전에 재검증한다.
- Provider 호출, 실주문, 현재 PID 재기동, 20:10 producer 조기 실행은 수행하지 않았다.

## 7. 최종 결함 재리뷰 후 보완

앞선 §1~§6과 WP0~WP7 전체 완료 표현은 당시 검토 범위의 기록이다. 후속 리뷰에서 누적 partition, 비용 크기 반영, optimizer 직접 소비, publisher 선행 검증 결손을 확인해 재개했다. 아래 계약이 §3의 오류율 차이 선정 계약을 대체한다.

- 누적 창: 당일과 최근19개 관측일. 날짜별 final #74 receipt·manifest hash·현재 raw generation과 당시 정책을 검증한다. 날짜별 bundle hash가 달라도 machine policy와 AI policy가 동일한 경우 그 날짜의 partition으로 수용한다. 변경된 정책·손상 원천은 합치지 않는다. 현재 compact 미관측은 기존 carry다.
- 목표: missed-profit VETO의 비용후 기회 합계와 PASS 손실의 절댓값 합계를 비교한다. 이 값은 동일 비중 반사실 합계이며 EV·실현손익·후보 개선량으로 부르지 않는다. +0.07% 기회5건과 -0.93% 손실1건 사례는 기회보존 변형을 선택하지 않는다. 기존20건·방향분모5·오류3·오류율25%는 유지하며, 다른 분모의 오류율10%p 차이 조건은 제거했다. 구 `minimum_rate_margin`은 호환 metadata이고 판정에 사용하지 않는다. 분모0은 null을 보존하고 관측된 방향 자체의 오류율과 손익 근거로 판단한다.
- tail: `material_tail_alert`는 표본20건 이전에도 표시한다. 등록 변형의 자동 전환은 기존 근거 floor를 유지한다. 경보 자체에 주문 변경 권한은 없다.
- WP3: #78에 등록 compact prompt/variant/system hash와 #82 경제성·선정·원천 receipt를 담는 `compact_auxiliary_optimizer_evaluation_v1`을 추가했다. 21:05 batch와 metadata refresh도 이를 보존하며 #80은 실제 optimizer 투영을 재계산해 대조한다. 기존 legacy replay는 별도 연구로 유지한다. 이 연결은 자연 결과 기반 bounded feedback이며 새로운 compact 후보의 Provider 비교를 수행했다는 뜻이 아니다. `candidate_improvement_proven=false`를 명시한다.
- 발행: strict 이전 publisher에서 정수 분모·제외 보존식·오류율 재계산·tail 상한·원천 measurement 허용과 source/history hash를 확인한다. producer/publisher/strict의 경제적 방향 함수는 공통 owner로 단일화했다.
- 달성 가능성: 원천이 정상이고 같은 정책에서 일4건의 경제적 유효 사례가 유입되면5개 관측일로20건이 된다. 이는 산술 예시이며 오늘 compact0건에서 산출한 ETA가 아니다. 정책 변경·원천 차단이 지속되면 동일 floor가 달성된다고 주장하지 않는다.

새 collector, Provider 호출, 수동 정책값, 현재 PID 재기동은 이 보완에 필요하지 않다. 다음 자동 생성과 정책/PID 소비 및 실수익은 기존 체크리스트 owner의 자연 acceptance다. 새 후보의 개선량이나 전체 WP의 운영 종결을 테스트 성공으로 대신하지 않는다.

검증: 6개 직접 owner suite 388 PASS, compact registry/자연 선정 보존 반례 추가 후 optimizer/replay 52 PASS. 날짜별 raw 변경·정책 변경 제외, 비용 크기에 따른 carry/선정, 한쪽 분모0, 발행 직전 rate/count/source 변조를 검증했다. Ruff·compile·diff 및 print-only parser26 PASS. commit/release 식별자는 runtime release selection receipt에 기록한다.

배포 전 압축 보관 반례 추가: 원본 stat이 달라졌을 때 logical-content SHA256이 동일한 gzip만 수용하며 내용 변경은 계속 제외한다. 표적1 PASS. 운영 I/O 부하로 release 전체 중복 테스트는 중단했으며 전체 release suite PASS로 기록하지 않는다. 작업본 PASS와 최종 release 코드 hash 일치를 배포 검증으로 사용한다.

## 8. P1 세 건 후속 종결 — 18:56 KST

- 상세 outcome map에서 PASS/VETO·missed-profit VETO·dangerous PASS를 재계산하는 공통 검증을 publisher와 strict에 연결했다. 상세 PASS20/VETO0·집계 VETO5 반례는 발행되지 않고 incumbent carry다.
- source date의 실제 정책을 평가 incumbent로 사용한다. 먼저 생성한 다음날 opportunity 후보 뒤 늦게 risk 근거가 도착하면 재발행하며 당일 정책은 보존한다. 다음날07:35 이후에는 기존 frozen bundle을 유지한다.
- 과거 gzip의 EOFError는 날짜별 source gap으로 격리한다. 정상 압축본 수용과 truncated gzip 제외를 함께 검증했다.
- 관련 calibration/publisher/strict322 PASS, Ruff·compile·diff PASS. 새 표본 floor나 사용자 승인 단계는 추가하지 않았다. 검토한 세 결함은 종결했으며 자연 정책/PID 소비와 비용후 실수익은 기존 acceptance로 남긴다.

## 9. 지원 연속매매 장후 세션·판정 분모 수리 — 19:33 KST

### 9.1 최초 결함

- `entry_candle_context`가 16:00~20:00을 구 `nxt_aftermarket` 한 구간으로 자체 계산해 공통 session contract의 `KRX_NXT_AFTERMARKET`, 19:40 close-only, 19:45 terminal-exit 경계를 소비하지 않았다.
- 통합 venue와 구 `nxt_aftermarket` label 조합은 날짜별 bundle의 `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET` scope로 정규화되지 않아, 지원 연속매매 정책이 있어도 fallback prompt로 이탈할 수 있었다.
- input preflight가 기계 평가 전에 fail-closed한 시도는 정상 주문 차단이었지만, 기계 평가 기대·source-invalid 제외 receipt가 trace에 없어 장후 감사가 `기계 시도 0`과 `평가 전 원천 차단`을 구분하지 못했다.

### 9.2 최소 보완

- candle session은 공통 `session_contract.resolve_market_session`을 단일 owner로 사용한다. 통합 시간대라도 plain KRX와 `_NX` NXT exact source를 보존하고 `_AL`/integrated만 통합 venue로 분류한다. 모든 종목을 `_AL`로 강제하거나 주문 route·수량·threshold를 바꾸지 않는다.
- live-policy resolver가 `INTEGRATED|SOR|KRX_NXT` venue와 main-window legacy label만 canonical integrated scope로 정규화한다. close-only와 terminal-exit는 진입 scope로 접지 않아 19:40 이후 BUY 경계를 유지한다.
- 기계 평가가 예정된 exact attempt에 `assessment_pending|assessed|source_quality_blocked_before_assessment|assessment_contract_invalid`, capture hash와 attempt identity를 보존한다. source-invalid row는 튜닝에서 제외하되 시도 총수에 남기고, 미설명 시도 또는 input contract invalid가 하나라도 있으면 기계 threshold 튜닝을 차단한다. 누락 비용·손익은 0으로 대체하지 않는다.

### 9.3 리뷰·판정

- 1차 리뷰 finding: assessment contract invalid가 분모에는 설명되어도 다른 정상 capture가 있으면 threshold 튜닝이 허용될 수 있었다. `warning_machine_assessment_contract_invalid`와 전용 blocked reason을 추가해 보완했다.
- 재리뷰 P0~P2 finding: 0. 기능·직접 consumer 1,026 PASS 후 보완 범위 514 PASS, Ruff(기존 E402/E722 제외), compile, `git diff --check` PASS.
- Kiwoom official reference gate: upstream `234560d213acd8871ae344b5481aecd2f30287fa`, `kiwoom_docs/실시간시세.md`의 REG/REMOVE 및 plain/`_NX`/`_AL` suffix, `kiwoom_docs/주문.md`의 `dmst_stex_tp=KRX|NXT|SOR`를 19:33 KST에 대사했다. 프로토콜 parser나 주문 API는 변경하지 않았다.
- 기대 효과는 지원 연속매매의 실제 정책 소비 회복과, 장후 임계치 학습에서 원천 차단 시도를 숨기지 않는 것이다. 비용후 +0.10% EV, 빈도, tail, 실주문 수익은 이 코드 검증으로 입증되지 않으며 다음 자연 generation의 policy publication→PREOPEN→PID→accepted submit/fill/terminal에서 별도 확인한다.
- 자동화는 기존 20:10 calibration `--write`→next-date policy publisher→PREOPEN resolver를 그대로 사용한다. 초기/incumbent bundle은 표본 부족이면 carry되고, threshold challenger만 비용후 +0.10% EV·동일 scope/holdout/source-quality guard를 통과해야 하므로 초기 정책 부재를 만드는 과도한 gate는 아니다.

## 10. 기계·compact AI 장후 consumer와 정책 발행 검증 수리

### 10.1 최초 결함과 영향

- #74가 `machine_attempt_conservation` 및 machine-specific threshold tuning gate를 발행했지만 #82 case table은 generic `tuning_input_allowed`만 복사했다. 따라서 machine assessment 미설명/contract-invalid 시도가 있어도 일반 원천이 유효하면 기계 threshold/hierarchy 학습에 들어갈 수 있었다.
- compact prompt 계약은 `PASS|VETO|CAUTION|INSUFFICIENT`를 허용하지만 case table은 PASS/VETO만 semantic-valid로 셌다. provider 미호출 ENTER도 screen 분모 밖으로 빠져 CAUTION/INSUFFICIENT/미평가와 VETO를 정확히 분리할 수 없었다.
- 1/3/5/10/20/30/60분 중 생성된 horizon만 projection하고 strict는 10분 하나만 확인했다. 장기 horizon 결손이 pending/source-gap인지 자체적으로 드러나지 않았다.
- calibration CLI가 publisher `None`을 정상 `not_enabled`로 출력하고 exit 0으로 끝날 수 있었고 wrapper와 strict verifier는 실제 next-date dated policy의 target/source/artifact hash를 직접 검증하지 않았다. report 성공이 자동 policy 발행 성공을 대신할 수 있었다.

### 10.2 최소 보완과 재리뷰

- machine source receipt에 전용 conservation/gate/reason을 전달하고 `policy_learning_eligible_observation_count`는 machine-specific gate만 사용한다. compact AI partition은 generic source/prompt measurement gate를 계속 사용해 서로의 결손을 전역 차단하지 않는다.
- 모든 기계 ENTER를 current compact/other compact/legacy-or-unknown/missing prompt로 보존한다. current compact는 provider called/not-called와 `PASS|VETO|CAUTION|INSUFFICIENT|NOT_EVALUATED|SEMANTIC_INVALID|SOURCE_PARTITION_NOT_ALLOWED`를 배타적으로 분류한다. CAUTION/INSUFFICIENT는 semantic-valid bounded 비진입이지만 PASS/VETO 경제 selector에는 넣지 않고, 미평가를 VETO로 합성하지 않는다.
- 모든 horizon key를 발행하고 원천이 없는 값은 수치 보간 없이 `pending_or_source_gap`과 null로 남긴다. strict verifier는 일곱 horizon과 상태를 모두 확인한다.
- canonical 20:10/21:05 calibration 호출에 `--require-policy-publication`을 추가했다. publisher 반환 policy의 next trading date, source date, calibration artifact hash, 기계-primary/AI-보조 role, 지원 연속 scope 유지와 주문 무권한을 즉시 검증한다. strict verifier도 실제 dated policy를 loader로 재검증한다.
- 1차 보완 뒤 추가 재리뷰에서 prompt version이 없는 기계 ENTER가 current compact 경제 분모뿐 아니라 전체 AI routing에서도 보이지 않는 결함을 확인해 `all_machine_enter_ai_routing` 보존식을 추가했다. 이 보완 뒤 P0~P2 finding은 0이다.

### 10.3 목표·gate·자동 적용 판정

- 기계 challenger는 같은 scope의 source-valid chronological holdout, 비용후 EV `>= +0.10%`, positive paired delta와 tail guard를 통과할 때만 바뀐다. 이는 작은 순익 목표의 최소 경제 경계이며 초기/incumbent 정책의 존재나 carry에 다시 붙지 않으므로 정책을 무기한 null로 만드는 과도한 gate가 아니다.
- compact successor의 유효20건·방향분모5·오류3·오류율25% 조건은 등록 prompt 간 성과 전환에만 적용된다. 미달은 현행 compact carry이고 AI 정책 부재가 아니다. CAUTION/INSUFFICIENT/미평가는 호출 성공이나 VETO로 부풀리지 않는다.
- 자동 경로는 `final #74 -> #82 calibration/case table -> bounded publisher -> next-date policy -> PREOPEN resolver -> actual PID`이다. 이번 수리는 앞 네 단계의 실패를 fail-closed하고 hash로 드러내지만 PREOPEN 선택·PID 소비·accepted submit/fill/terminal·실제 비용후 순익은 미래 자연 receipt로 별도 확인한다.
- 기대 효과는 손상된 기계 시도로 잘못된 임계치를 만드는 위험 제거, AI 비진입 유형의 정확한 귀속, 늦은/놓친 타점 horizon 결손 가시화, silent no-policy 성공 제거다. 코드 검증은 실제 수익 증가 증명이 아니다.

검증: source audit, calibration, publisher, PREOPEN policy, prompt consumer, wrapper와 strict verifier 7개 직접 suite `705 passed`; Python compile, Ruff check/format, shell syntax, `git diff --check`, 문서 print-only parser 27건 PASS. Provider 호출·실주문·현재 실행 중인 장후 wrapper 수정 또는 중복 실행은 하지 않았다.

## 11. 자연 장후 실행 결함 복구·최종 배포 세대

### 11.1 자연 실행에서 확인한 추가 결함

- 20:10 선택 release의 자연 실행은 22:18:33 verifier에서 실패했다. 최초 원인은 Pattern Lab 후속 추천 두 행이 같은 native ID를 발급한 충돌이었고, 기존 검증 수리를 재사용해 ID 유일성을 복원했다.
- 기계 timing loader는 다른 owner가 같은 stage를 발행했다는 이유만으로 `scopes={}`인 무변경 baseline carry까지 veto했다. 실제 timing scope가 있을 때만 same-stage owner veto를 적용하도록 줄였다. 정책 변경이 없는 carry를 차단하던 과도한 조건만 제거했으며 scoped challenger 충돌은 계속 fail-closed다.
- #82 calibration은 6GB대 일별 pipeline을 hierarchy scope마다 반복 읽었다. 하루 파일을 한 번 읽어 지원 scope별 price series cache를 구성하도록 바꿔 동일 계산·분모·정책 결과를 유지하면서 반복 I/O를 제거했다. 최적화 recovery는 658.53초에 끝났고 2026-09-15 dated policy를 발행했다.
- 가장 늦게 드러난 결함은 main verifier와 21:05 replay follower의 순환 대기였다. follower는 main DONE을 기다리지만 main 내부 verifier가 follower terminal을 먼저 요구했다. wrapper 내부 verifier만 exact-date `running` source-only placeholder를 허용하고, controller/finalization의 외부 strict는 terminal batch·consumer를 계속 요구하도록 분리했다. 부분 cohort, 잘못된 schema/date, 주문 권한 누수는 pending으로 인정하지 않는다.

### 11.2 정책 발행·gate 판정

- 22:54:59 recovery 발행본은 `policy_2026-09-15.json`, bundle `0325e48b2818311673bf4af0d8127ffd83c296f62476901fb3506118d78ca709`, `machine_disposition=incumbent_carried`, `hierarchy_adopted=true`, `all_continuous_adopted=true`다.
- 기계 challenger의 비용후 EV `>= +0.10%`, 같은 scope chronological holdout, positive paired delta와 tail guard는 유지했다. 이 gate는 challenger 교체에만 적용되고 initial/incumbent policy carry를 막지 않으므로 정책 부재를 만드는 과도한 조건이 아니다.
- compact AI successor의 경제 유효20건·방향분모5·오류3·오류율25%는 등록 prompt 교체에만 적용된다. 당일 자연 compact 경제 분모가 없으면 v3 carry이며, 이를 AI 정책 부재나 Provider 실패로 바꾸지 않는다.
- 23:12:57 controller의 검증된 `tail_repair_done_reconciliation`으로 main status/DONE을 복원했다. 그 뒤 기존 follower는 23:14:17 KRX 6건 평가와 NXT exact-source 결손을 분리한 terminal batch를 만들었고, tuning monitoring은 23:16:20 성공 terminal이 됐다. 최종 replay metadata/consumer·strict·controller·finalization은 아래 최신 receipt로 다시 닫는다.

### 11.3 코드·리뷰·배포 경계

- commits: `c88d8127` 정책 handoff, `ee9f4765` Pattern Lab ID 충돌, `ff214fc6` timing carry/I/O 최적화, `5b78931b` replay 순환 대기 해소. 모두 `origin/main`에 push했다.
- 최종 검토 release는 `/home/ubuntu/KORStockScan-runtime-releases/machine-entry-postclose-handoff-r5-20260914` / `5b78931b622f66aec24bf9c66e35f8a154d057b2`다. shared `data/docs/logs/tmp/.venv/restart.flag`와 source/deploy cleanliness를 확인했다.
- 최종 보완 범위는 직접 verifier/wrapper/controller suite `427 passed`; 앞선 calibration/timing 누적 검증은 기능·consumer 확대 suite `977 passed`다. Ruff, formatter, compile, `bash -n`, `git diff --check` PASS이고 P0~P2 unresolved finding은 0이다.
- release selector 전환은 실행 중인 scheduled follower가 모두 terminal인 뒤에만 수행한다. selector 전환은 다음 예약 코드 경로 승인이고, 2026-09-15 PREOPEN 선택·실제 PID 소비·accepted submit/fill/terminal·비용후 순익 증명은 아니다. main bot은 20:10 이후 중지 상태이므로 이 source-only 복구를 위해 재기동하지 않는다.

### 11.4 Replay follower terminal 판정 계약 수리

- r5 selector 전환 뒤 controller module은 23:46:45 `done`이었지만 wrapper follower는 산출물 재생성을 모두 끝낸 뒤에도 `retry_required:cohort_contract_expected_census_invalid`로 실패했다. 최초 원인은 producer가 발행하는 안정 schema가 `version`·`expected_cohorts`·`contract_content_sha256`인데 controller inline validator만 존재하지 않는 `contract_version`·`expected_cohorts_by_contract_version` 형태를 요구한 계약 drift였다.
- validator를 producer 소유 schema에 맞췄다. contract self-hash·batch hash, v1/v2, expected/actual cohort identity census, runtime/order 무권한을 검증하고, integrated dual-aftermarket row는 계속 `OBSERVE_ONLY|BLOCKED_MISSING_APPROVAL` terminal만 허용한다. live authority나 candidate hash가 들어오면 fail-closed한다. KRX/NXT exact live-candidate hash·effective-date 검증도 별도로 유지한다.
- 실제 9/14 batch·consumer를 새 validator에 입력한 결과는 `terminal_ready:validated_batch_candidate_and_main_ai_consumer`다. 직접·wrapper·producer/consumer 확대 회귀 `234 passed`, `bash -n`, Ruff, formatter, `git diff --check`가 통과했고 재리뷰 P0~P2 finding은 0이다.
- 이 수리는 retry loop만 제거하며 prompt, threshold, provider, order, quantity, custody 또는 hard-safety를 바꾸지 않는다. 새 release 배포 뒤 controller/finalization의 exact-date terminal을 다시 확인한다.

### 11.5 Storage·cleanup 최종 결함과 9/14 terminal 복구 — 00:43 KST

- replay follower 수리 뒤 cleanup에서 공유 관측 원장에 의도적으로 공존하는 `ai_decision_payload_v1`과 `mechanistic_entry_observation_v1`을 단일 schema 파일로 오판하는 결함이 드러났다. 허용 schema의 행별 검증과 혼합 보존식을 적용하되 unknown schema, 손상 JSON, 필수 identity 결손은 계속 실패하도록 수리했다. commit `f3aba22b53187f691a998e411a7976cb0113bccb`다.
- 다음 cleanup은 현재 target의 active log가 owner rollover로 검증·gzip 회전됐는데도 원본 파일 부재를 반복 writer defer로 세었다. receipt의 schema/date/source path, gzip 무결성, compressed SHA256과 decoded source SHA256을 모두 검증한 경우에만 원본 부재를 정상 rollover로 인정하도록 수리했다. receipt가 없거나 hash가 다르면 기존처럼 fail-closed한다. commit `6286fcf8644e7d022ead8082f457aa7732bade14`다.
- storage/cleanup 전체 계약 suite `151 passed`, owner receipt 정상·결손·reset 집중 반례 `3 passed`, mixed schema 정상·unknown schema 반례 `2 passed`다. 앞선 replay 직접 suite `234 passed`, verifier/controller `427 passed`, 영향 범위 확대 `977 passed`와 함께 Ruff, Black check, Python compile, `bash -n`, `git diff --check`가 통과했고 재리뷰 P0~P2 finding은 0이다.
- 최종 immutable release는 `/home/ubuntu/KORStockScan-runtime-releases/machine-entry-postclose-handoff-r8-20260915` / `6286fcf8644e7d022ead8082f457aa7732bade14`다. selector·공통 cron 9경로·finalize/PREOPEN/start/restart print-plan이 이 release를 가리킨다. 장 종료 후 main bot이 없으므로 수동 기동은 하지 않았고 다음 예약 PREOPEN/기동이 실제 PID 소비 owner다.
- 9/14 finalization recovery는 00:37:46 시작, 00:43:52 cleanup DONE, 00:43:54 final detector DONE으로 종료했다. 최신 detector run은 `cron-20260915T004352-1153933`, Telegram은 `no_alert`다. 이전 cleanup FAIL보다 최신 성공 receipt가 권위를 갖는다.
- 다음 날짜 정책 `policy_2026-09-15.json`은 source date 9/14, bundle `719218d4d3899fea6021bbbc3a72b67421f2f76fa5a8fc57e980b89e6b9c0de0`, `machine_disposition=incumbent_carried`, hierarchy/all-continuous adopted로 발행됐다. 비용후 `+0.10%`와 동일 scope chronological holdout·positive paired delta·tail guard는 challenger 교체에만 적용되고 incumbent carry를 막지 않는다. compact AI도 경제 분모 미달이면 등록 v3를 carry하므로 정책 존재 자체를 차단하는 과도한 gate가 아니다.
- 자동 적용 경로는 `final #74 -> #82 calibration/case table -> bounded publisher -> next-date policy -> PREOPEN resolver -> actual PID`로 닫혔다. 다만 PREOPEN 선택, 실제 PID receipt, accepted submit/fill/terminal과 비용후 작은 순익의 빈도·tail·총 순익은 아직 자연 관측 전이다. 코드·발행·배포 성공을 경제성 수용으로 바꾸지 않는다.
- 최신 recommendation intake는 총73, 구현 요청14, 비구현59, 미분류0이다. 구현 요청 중 `blocked_missing_evidence=3`, `eligible_actionable_open=11`이라 전체 2-pass fixed-point는 아직 아니다. 이번 기계+compact AI 수리 범위의 finding은 닫혔지만 scanner/WS/Pattern Lab 등 다른 native workorder를 구현 완료로 확대하지 않는다. 따라서 운영 chain은 terminal이나 종합 판정은 자연 적용·경제성 및 남은 eligible workorder 때문에 `YELLOW`다.
