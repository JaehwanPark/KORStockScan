# 보조 AI의 VETO 기회비용·PASS 오진입 튜닝 및 장중 정책 적용 계획

작성: 2026-09-22 KST
상태: **9/26 네 조정축의 생산·후보·평가·발행·장중 소비 코드와 회귀 검증을 구현했다. 유형 leaf는 학습 기회 5건 미만이면 생성하지 않는다. 9/23 고정 원천은 독립 날짜 holdout과 후보 prompt 응답이 없어 incumbent carry이며, 9/28 자연 stage terminal·정책 승격·실제 PID 소비·비용 후 성과는 별도 미종결 수용이다.**
실행 owner: [9/28 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `DirectFamilySourceRepairCompactAuxiliary`. [9/23 원래 owner](../checklists/2026-09-23-stage2-todo-checklist.md)는 이관 이력이다. 성공 PASS 대조군은 기존 compact auxiliary source/label/evaluator 단계에서 처리하며 별도 stage나 장후 실행기를 추가하지 않는다.
연결: [메인 기계판정](main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md), [장후 실행기 분리](machine-postclose-runner-separation-implementation-plan-2026-09-22.md).

## 1. 목표와 단계 경계

실제 메인 기계판정 ENTER_NOW 뒤 보조 AI에 전달된 기회만 대상으로 **수익 기회를 놓친 VETO를 PASS로 바꾸는 학습**과 **손실 위험을 허용한 PASS를 VETO/CAUTION으로 바꾸는 학습**을 함께 수행한다. 좋은 PASS와 올바른 VETO도 control 모집단으로 보존한다. 기계 BLOCK/RECHECK를 AI 학습에 섞거나 AI가 기계 action을 승격하지 않는다.

현재 compact runtime은 PASS만 기존 제출 경로로 보내고 VETO는 DROP, CAUTION/INSUFFICIENT/응답 실패는 WAIT·재확인한다. 실제 응답과 supporting/contradicting fact binding을 검증한다. confidence0~100은 현재 **schema 유효 범위**이며 실증적으로 보정된 진입 점수나 적용 임계치가 아니다.

기존 owner-capital/exact-stop prompt 계약에는 학습20/holdout20·2일 및 portfolio 조건이 남아 있다. 현재 별도 AI soft stage는 그 계약과 독립된 고정 10분 경로로 두 개의 근거 개수 축을 평가한다. 두 basis의 모집단·성과·승격을 섞지 않는다. legacy 자료는 이력으로 보존하고 신규 AI stage에는 새 basis/validator/publisher를 명시한다.

**구현 완료 범위는 네 조정축 모두다:** ① 유효 AI 응답의 soft VETO/PASS 근거 개수, ② bounded risk family별 수치적 중요도, ③ 종목 유형·현재 상태에 따른 조합 선택, ④ versioned compact prompt 변형. 네 축 각각에 source/후보/경제성 평가/승격 검증/runtime loader/적용 영수증/rollback 경로를 만든다. 적격 자연 표본이 없다는 이유로 해당 축의 코드 구현을 후속 과제로 넘기지 않는다. 다만 근거가 없는 특정 scope의 **정책 승격**은 parent carry이며, 없는 실현 EV를 만들어 구현 완료라고 주장하지 않는다.

### 1.1 구현 전 결손과 미종결 자연 수용

- 런타임은 기계 `ENTER_NOW` 뒤 한 번의 유효 compact AI 판정을 소비한다. 현 soft evaluator가 조정하는 수치는 `veto_min_independent_evidence_count`, `pass_min_positive_evidence_count` 각 1~3뿐이다. confidence 0~100은 schema 검사이며 PASS 임계치가 아니다. prompt 문구의 위험·긍정 근거 우선순위는 수치 튜닝값이 아니다.
- 장후 soft stage는 동일 raw AI 응답을 3×3 조합으로 재평가한다. 9/23 산출물은 74건 선별 중 경제성 적격 11건, 제외 63건, 비교한 9개 조합 중 행동 변경이 있는 3개가 부모보다 낮은 paired delta여서 현재 정책을 유지했다. 이는 후보 계산 성공과 신규 정책 승격 실패를 구분한 결과다. 이 고정 경로는 실체결·실현손익이 아니다.
- prompt 후보용 원천 계약은 9/23 `source_contract_blocked`/`natural_exact_row_count=0`이다. 현 publisher는 soft `auxiliary_stage`가 붙으면 prompt 후보 승격을 건너뛰므로 독립 prompt 폐루프가 닫히지 않았다. soft-only 승격을 보고서 최종 disposition에 반영하지 않는 경로도 보완 대상이다.
- 현재 적용 AI prompt는 `entry_machine_auxiliary_compact_v3`이고 확인한 bundle의 `auxiliary_soft_policy`는 비어 있다. 9/28 실제 PID 소비 및 자연 비용 후 성과는 아직 증명되지 않았다. 단순 stage terminal, 파일 존재, 배포 준비를 완료 증거로 취급하지 않는다.

## 2. 실제 호출 데이터와 모집단

필수 key: source date, symbol, venue/session, promotion/attempt/trace, input snapshot/as-of, machine generation/profile/assessment hash, AI component/prompt/model/provider/schema hash, raw response hash, 실제 호출 여부, raw/effective verdict, supporting·contradicting fact IDs, cutoff, 비용/경로 label provenance.

| 원래 AI 판정·경로 | 학습 의미 | 목표 |
| --- | --- | --- |
| VETO + 양수 경로 | false veto, 놓친 이익 | 근거를 충족하는 PASS 전환 |
| VETO + 음수 경로 | correct avoidance | VETO 보존 |
| PASS + 양수 경로 | correct pass | PASS 보존 |
| PASS + 음수 경로 | false pass 후보, 잘못 허용한 진입 | VETO 또는 CAUTION 전환 |
| 비용 후0 | 중립 | 이익/승리로 세지 않고 전이 보고 |
| CAUTION/INSUFFICIENT/transport 실패 | 평가 보류·운영 실패 | VETO로 합치지 않고 별도 coverage/재확인 집계 |
| 시간·비용·경로 미완결 | censored/source gap | 경제성 분모에서 제외, 원본 보존 |

- 동일 입력 시점의 부모·후보 AI를 비교한다. 최신 기계정책 때문에 새롭게 ENTER_NOW가 된 과거 BLOCK/RECHECK는 보조 AI의 실제 호출 모집단에 소급 편입하지 않는다. 이후 실제 호출에서 자료를 쌓는다.
- clean tuning baseline `2026-06-05T00:00:00+09:00` 이후의 실제 호출만 선정·승격에 사용한다. 이전 원천은 이력 감사에만 쓰고, 현 AI prompt/model·기계 generation이 다른 표본의 호환성을 검증 없이 합치지 않는다.
- 후보가 사실과 다른 판단을 한 것과, PASS 후 슬리피지/가격·수량/청산 때문에 실제 손실이 난 것을 구별한다. PASS 손실을 전부 AI 오류라고 단정하지 않는다.
- AI 단계의 최초 독립 평가 basis는 기존 outcome label의 같은 venue/session 10분 고정 target(+0.3%)/adverse(−0.7%)/종료 가격 경로에서 왕복 보수 비용을 뺀 `auxiliary_fixed_path_10m_v1`이다. 가격경로가 미완결·동일 봉 선후 불명·비용 누락이면 제외한다. 이는 기존 `entry_quality_path`의 **실제 계획 exact stop** 또는 체결 손익이라고 주장하지 않는다. 정확한 stop이 없는 과거 건을 임의로 보충하지 않는다. 실제 `COMPLETED + valid profit_rate` 및 같은 attempt의 실제 비용이 있는 경우만 별도 realized outcome으로 연결한다.
- 동일 봉 목표·손실 동시 도달, 종료 미확정, fill 불명확한 실현손익은 확정 성공/실패로 쓰지 않는다. 경로 라벨의 target/stop/horizon/cost 버전은 해당 평가 동안 고정한다.
- 날짜·종목·promotion 기회 단위로 동일 가중치를 부여하고, attempt 수가 많은 RECHECK/재호출이 점수를 부풀리지 않게 한다. 미래 경로는 label에만 쓰며 prompt와 selector에는 전달하지 않는다.

## 3. 후보 평가와 순위

### 3.1 네 조정축의 후보 생성과 동일 기준 비교

A. **Prompt 변형 — 필수 구현**: 기존 v3, opportunity, risk 변형의 versioned template와 hash를 같은 frozen exact input에 실행한다. 장후 source producer가 9/23 `natural_exact_row_count=0`의 첫 결손을 추적해 실제 pre-AI input/model/provider/schema/시각·부모 hash를 자연 호출 때 저장하고, 재현 불가한 옛 행은 `source_gap`으로 남긴다. 후보 응답이 없는데 부모 응답을 복제해 후보 PASS로 처리하지 않는다. exact-input cache를 먼저 쓰고 cache miss만 제한된 provider budget에서 호출한다. 현 `candidate_direction_selection`의 legacy owner-capital/exact-stop 점수를 전용하지 않고, 새 prompt 후보 raw 응답을 아래 B/C와 같은 고정경로 경제성·holdout으로 비교한다. 응답 계약·동일 basis 발행기를 구현하는 것이 이 계획의 필수 산출물이다.

B. **근거 개수 — 현 구현 보완**: 동일한 유효 AI 응답·근거 프레임을 공유 `evaluate_auxiliary_policy`에 넣어 soft VETO 독립 근거 개수와 PASS 긍정 근거 개수를 재판정한다. 응답 schema/발명 사실/기계 hard source 검증은 먼저 수행하며 실패는 non-exposure다. 현 응답에 없는 추가 근거를 추정하거나 후보 성과로 세지 않는다.

C. **Soft 위험도 수치 — 필수 구현**: 이미 fact-bound인 `LIQUIDITY_FRAGILE`, `ADVERSE_TAPE`, `REWARD_RISK_WEAK` 각각에 한정해 판정 전 값·단위·as-of·source ID와 독립 근거 ID를 담은 작은 `auxiliary_materiality_v1` registry를 만든다. 후보축은 spread excess(bp), signed pressure adverse margin(정규화 단위), 비용 후 사전 reward/risk 부족량으로 한정한다. 기존 exact analysis에서 직접 재현할 수 없는 값은 producer가 같은 시점의 입력에서 계산·기록하도록 보완하며, **역사적 결손을 임의 숫자로 채우지 않는다**. hard source/order/구조 차단과 AI risk enum 자체는 변경하지 않는다. 수치가 없는 행은 해당 수치 후보만 unsupported로 표시하고 parent 규칙을 그대로 평가한다.

D. **종목 유형·상태별 선택 — 필수 구현**: 현재 `build_entry_predecision_group_observation`의 가격 대비 tick, 유동성, 완료 봉 변동성, 구조 단계와 venue/session 계산을 **권한 없는 관측물에서 순수 feature 계산으로 분리**한다. versioned AI selector가 이 판정 전 값과 source hash를 장후·장중에서 동일하게 사용하되, 기존 `runtime_effect=false` 관측물 자체를 live 승인 입력으로 전용하지 않는다. 시가총액은 시점·출처가 검증된 snapshot 필드를 producer에 추가한 경우에만 분기값으로 쓰고, 없으면 명시적 `UNKNOWN` parent fallback이다. 시간 이후 체결·결과를 selector에 넣지 않는다. 전 종목 공통 부모 조합과 지원되는 소수 leaf 조합을 함께 평가하고, 빈/희박한 leaf는 상위 parent를 소비한다. 이 selector 및 leaf/parent fallback 자체를 구현·테스트한 뒤 데이터 부족한 leaf만 carry한다.

네 축의 검증과 발행은 기존 compact 모듈과 versioned `ai_policy` 안에 둔다. 별도 분류 daemon·DB·무제한 AI 재호출은 추가하지 않는다. legacy 응답은 어댑터로 읽되 없는 필드를 사실로 채우지 않는다.

### 3.2 양방향 점수

기회별 비용 반영 경로를 y, PASS 여부를 p라 하면 `value=p*y`, `paired_delta=(p_candidate-p_parent)*y`다. VETO→PASS의 양수 y와 PASS→VETO의 음수 y 회피가 모두 개선에 기여한다. 동시에 좋은 PASS 차단과 올바른 VETO 해제가 손실로 반영된다. CAUTION은 이 즉시 노출 실험에서 non-PASS로 두되, 향후 재확인 손익을 0이라고 확정하지 않는다.

공통 승률 우선 선호를 반영한 **초기 설계값**:
- `pass_win_rate`: 선택 PASS의 기회 가중 승률.
- `good_pass_retention`: 양수 경로 기회를 PASS로 남긴 비율.
- `bad_pass_rejection`: 음수 경로 기회를 non-PASS로 바꾼 비율.
- `balanced_quality`: good retention과 bad rejection의 평균. 한 class가 없으면 그 class 비율은 null, 관측 class만 사용하고 coverage를 명시한다.
- `Q = 0.6 * pass_win_rate + 0.4 * balanced_quality` (각 비율0~1)는 양방향 진단값으로 남긴다. 후보가 점수 가중치를 바꾸지 않는다.
- 현 코드는 기회 단위 PASS 승률의 `machine_support_adjusted_win_rate` → 선택 PASS의 비용 후 평균 경로 이익 → 동일 분모의 부모 대비 paired delta → 선택 기회 수 → 단순성 순이다. 이는 기계판정과 같은 **선호 순서**이나 AI 단계의 충분한 승격 근거는 아니다. 1건/100% 또는 매우 적은 행동 변경에서 부모보다 좋아 보이는 결함을 보완한다.
- 보완 후에는 train·holdout 각각 같은 전체 기회 분모의 비용 후 `paired_delta >= 0`와 전체 기회 가중 EV 비악화, 양수 PASS 보존율 및 음수 PASS 거절률의 심각한 퇴행 없음, support-adjusted 승률 우세를 **함께** 확인한다. 선택 PASS만의 조건부 평균 EV는 구성 변화로 달라지므로 진단으로 보고하되 독립적인 비악화 강제 조건으로 쓰지 않는다. 원천·비용 label 동일성, 유일 기회 수, 양·음 class 수, 행동 변경 수와 날짜별 기여를 고정 분모로 공개한다. 절대 평균이익이 음수라는 이유만으로 단독 탈락시키지 않지만, 손실을 늘리는 후보를 승률 하나로 승격하지 않는다. 동률·동일 행동은 부모 유지다.
- 학습 집합에서 후보를 고른 뒤 더 늦은 날짜를 단 한 번 독립 holdout으로 사용한다. 첫 계약은 scope별 train 적격 유일 기회 5건·holdout 3건, train 행동 변경 2건·holdout 1건을 최소로 하고, 양수·음수 label이 합계에서 각 1건 이상 없으면 해당 방향의 개선 주장을 보류한다. 한 날짜 또는 한 행동 변경만 있으면 평가·진단은 계속하되 승격은 `insufficient_independent_evidence`로 보류한다. 다음 자연일로 누적하여 재평가한다. 기존 legacy의 학습20/holdout20·2일 portfolio 문턱을 AI stage에 그대로 복사하지 않는다. 이 바닥은 후보 탐색 전에 versioned 계약으로 고정하고, 검증 실패 후 축소하지 않는다.

모두 VETO/CAUTION으로 바꾸어 분모를 없앤 후보, 허용 PASS0인 후보, 지원 자료를 의도적으로 제외한 후보는 적용 후보가 아니다. 무근거 all-PASS도 fact/guard 검증을 통과할 수 없다. 실제 경로가 모두 양수라면 근거를 충족한 all-PASS 자체를 금지하지 않는다.

평가는 한 기회부터 실행하되 **평가 가능과 정책 승격 가능을 분리**한다. 유효 후보·독립 holdout·전이 양방향 근거가 없으면 scope별 부모 carry이다. 부족한 class를 가짜 표본으로 채우지 않는다. Q는 양방향 진단값이며 승격의 단독 점수가 아니다.

### 3.3 성공 PASS 대조군을 추가 부담 없이 학습에 반영

성공 PASS는 기존 AI 호출 로그와 기존 가격 경로·비용 라벨을 재사용해 후보가 보호해야 할 양성 대조군으로 반영한다. **근거 개수·수치·유형 selector의 결정론적 재평가는 provider 호출 0건**이며, prompt 변형의 실제 응답이 필요한 동일 manifest 행만 기존 호출 budget 안에서 재생한다. 새 저장소와 전 종목 재생은 요구하지 않는다.

- 대조군은 실제 machine `ENTER_NOW` 뒤 AI가 실제 호출되어 raw/effective verdict가 유효한 `PASS`였고, 해당 promotion의 완결된 비용 반영 경로가 양수인 기회로 한정한다. 단순 PASS, 미체결, 미완결·censored 경로는 성공으로 세지 않는다. 실제 `COMPLETED + valid profit_rate`는 별도 실현손익 표본으로 유지한다.
- 장후 `outcome_labels`/`compact_auxiliary_paired_replay`가 이미 만든 같은 attempt의 label을 verdict·input hash로 조인한다. 기존 라벨을 재생성하지 말고, 응답·label join이 없으면 그 행은 미연결 source gap으로 남긴다.
- 결정론적 근거·수치·유형 후보는 기존 raw 응답과 판정 전 fact/feature frame을 공유 evaluator에 다시 넣는다. 추가 provider 호출 수는 0으로 제한하고, `good_pass_retention` 및 `pass_win_rate`에 성공 PASS를 포함한다. 후보가 성공 PASS를 non-PASS로 바꾸면 동일 기회 paired delta에서 그 기회 수익만큼 불이익을 받는다.
- prompt 후보가 필요한 경우에도 성공 PASS 행을 후보 manifest와 동일한 고정 분모에 넣는다. 기존 exact-input 응답 cache를 먼저 재사용하고, cache miss 재호출은 기존 최대 후보·provider budget 안에서만 수행한다. 성공 PASS만을 따로 표본추출하거나 평가 후 분모에서 제거하지 않는다.
- 독립 AI 단계 보고서가 존재하면 기존 owner-capital/exact-stop 기준의 prompt 승격 결과를 AI 단계 후보로 전용하지 않는다. 새 prompt 후보는 **같은 고정경로·분모·비용·독립 검증**을 생산하고 적격 여부를 판정해야 한다. 자연 exact input이 아직 없어 승격이 불가능해도 producer/evaluator/publisher/loader 구현을 생략하지 않는다.
- 보고서에는 `eligible_successful_pass_count`, `linked_successful_pass_count`, `good_pass_retention`, 성공 PASS에서 바뀐 verdict 수, 추가 provider call 수를 기록한다. 이 값은 별도 score 보너스가 아니라 기존 paired score의 분모·전이 근거다.
- AI 단계 고정 경로의 target/adverse/horizon·왕복 비용·동일 route outcome provenance가 빠지면 PASS 행은 보존하되 success label은 미확정으로 분류하고 승격을 막는다. null을 0이나 성공으로 바꾸지 않는다. 기존 owner-capital/exact-stop 비교의 `exact_stop_distance_missing_or_invalid` 결손은 별도 legacy basis에 남는다.

성공 PASS 대조군 연결은 기존 compact auxiliary 평가 안에서 닫는다. 별도 장후 stage/cron, 모델 학습 서비스, 별도 승인 통로는 만들지 않는다.

### 3.4 시간·범위·계산량

- source generation과 부모 AI component를 pin하고 train에서만 후보·경계·학습 대상을 정한다. latest completed day는 독립 검증에 쓸 때 후보 탐색에서 완전히 격리하고 한 번만 소비한다. 한 날짜뿐이면 holdout 없음으로 표시하고 발행은 보류한다. 미래 날짜의 같은 frozen contract만 다음 검증에 추가한다.
- 소스와 모델을 동일하게 맞춘 paired 비교를 수행한다. machine generation이 다른 기회는 층별 결과를 남긴다. 의미적으로 호환되는 입력 schema/지원 cohort에서만 묶고, 새로운 기계 scope에는 미학습 AI 임계치를 전파하지 않는다.
- prompt 후보는 부모+최대3개로 고정한다. 근거 개수 3×3과 수치 3 family·유형/state leaf는 **모든 축을 최소 한 번씩 평가**하는 사전 고정된 단일축 후보 집합을 먼저 계산한다. 그다음 train 상위 조합을 제한된 beam으로 합쳐 scope/leaf별 최대32개 최종 joint 후보를 같은 manifest에서 재평가한다. 이 절차가 전체 실수 공간의 전역 최적값을 증명한다고 주장하지 않고, versioned 후보 격자·제외 조합·budget 도달 여부를 보고한다. budget 때문에 미평가된 축이 있으면 선정 성공이 아니라 `search_incomplete`다. source가 완성된 기회 → 기존 추천/오류 근거가 있는 기회 → 이전 train의 정보 가치 순서로 정하며 부모·후보 분모와 가중치를 동일하게 유지한다.
- 큰 모집단은 고정된 층별 결정적 표본으로 provider 재생을 제한하고 근거 임계치 평가는 확보된 유효 표본 전체에 수행한다. untouched 평가 집합을 보존한다. positive VETO/negative PASS만 골라 평가하고 좋은 control을 빼지 않는다.
- 비교 manifest는 후보 실행 전에 고정한다. 후보별로 실패 응답·손실 표본을 삭제해 분모를 바꾸지 않는다. 선택된 paired 표본의 응답이 미완성인 후보는 deferred이며, timeout/schema 오류를 올바른 손실 회피 점수로 세지 않는다. runtime은 그대로 WAIT한다. deterministic 후보의 원천 미지원은 사전 고정한 parent fallback으로 평가한다.
- exact input+prompt+model/provider+schema+policy hash로 응답 캐시를 묶는다. provider budget 소진 시 chunk를 저장하고 stage만 deferred 처리한다. 기계정책은 그대로 운영한다.

## 4. 런타임 조정 가능/불가능 항목

현재 코드에는 범용 `AI confidence >= X이면 PASS` 정책이 없다. **현행**, **이번에 구현 필수**, **고정 안전/운영**을 구분한다. 미구현 축은 코드·source·runtime evaluator·publisher·loader를 이번 계획 안에서 완성하되, 증거가 부족한 leaf/후보는 승격하지 않는다.

| 현 상태 | 항목 | 장후·runtime 계약 |
| --- | --- | --- |
| **현행 소비 가능** | `veto_min_independent_evidence_count` {1,2,3} | 독립 adverse 근거를 세고 bounded soft VETO에만 적용. 확정 hard VETO는 제외 |
| **현행 소비 가능** | `pass_min_positive_evidence_count` {1,2,3} | 필수 setup/trigger 사실 뒤 추가 PASS 자격. 필수 사실 부재를 개수로 보상하지 않음 |
| **이번에 구현 필수: prompt** | compact v3/opportunity/risk variant | 영어 ASCII versioned template, 후보 실제 응답, 같은 고정경로 경제성·독립 holdout, prompt 포함 AI component 발행·loader·rollback. v3는 후보 미승격 시 부모값 |
| **이번에 구현 필수: soft 중요도** | `LIQUIDITY_FRAGILE` spread excess(bp), `ADVERSE_TAPE` signed pressure adverse margin, `REWARD_RISK_WEAK` 비용 후 사전 reward/risk 부족량 | 수치·단위·as-of·source·risk fact binding producer, train에서 고정한 유한 경계 후보, schema 범위와 hard guard 우선순위, offline/live 동일 평가. 관측값 없는 행만 parent fallback |
| **이번에 구현 필수: 유형/state** | venue/session → 가격·tick/시가총액·유동성·완료 봉 변동성·구조 상태 selector | 같은 predecision feature builder, 상위 parent/소수 leaf 정책, source 시각·해시, 희박/UNKNOWN fallback, 선택된 profile·policy hash 영수증. 시가총액 snapshot이 없는 표본은 전체 구현 차단이 아니라 해당 차원 UNKNOWN |
| **고정 입력 계약** | risk code enum, fact 존재·binding·충돌, confidence 정수0~100, schema/version/hash | validator가 허구·불일치 응답을 거절. confidence는 판정 cutoff 아님 |
| **고정 기계 소유** | BLOCK/RECHECK/ENTER_NOW, 구조/트리거·기계 threshold | AI는 ENTER_NOW 모집단 안에서만 판단하고 기계 component를 변경하지 않음 |
| **고정 안전·운영** | stale/deadline/route·clock·epoch/crossed BBO, broker/account/order/qty/cooldown, hard/protect/emergency/operator lock; provider/model/timeout/retry/token/cache | AI 품질 후보가 source 안전·호출 운영 값을 변경하지 않음 |
| **고정 후단 소유** | 가격·수량·분할·scale-in·청산·위젯/에피소드 custody | PASS는 최종 주문/체결 허가가 아님 |
| **이번 평가 고정** | confidence cutoff, target/stop/horizon·비용 label, 점수 가중치 | cutoff는 도입하지 않으며 label과 평가 목적함수는 후보 비교 전 동결 |

soft materiality 수치는 82개 machine registry를 복사하지 않는다. 세 family의 수치 정의와 정규화 단위는 구현 시작 시 versioned registry에 고정한다. 경계 후보는 train의 관측 분포에서 만들되 기계 hard threshold보다 느슨한 통과 권한을 만들 수 없고, 지원하지 않는 family에 다른 수치를 대신 적용하지 않는다. 값이 없는 역사적 행은 parent로 비교하고 `materiality_source_missing`을 남긴다. producer를 보완해 새 자연 입력에서는 세 family의 지원 가능 여부를 매번 기록한다.

초기 수치 계약은 `LIQUIDITY_FRAGILE`의 현재 spread(bp)와 기존 지지 유동성 band 초과분, `ADVERSE_TAPE`의 fresh 10-tick signed aggressive delta를 동일 구간 총 절대 체결량으로 나눈 부호 있는 비율, `REWARD_RISK_WEAK`의 판정 전 계획 target·stop·왕복 비용으로 산출한 순 reward/risk 부족량이다. 분모·계획 stop·source 시각이 없으면 null과 사유를 남긴다. 경계 후보는 각 수치의 train 분위수에서 부모값을 포함해 소수만 고르고, 단위 변경 시 registry 버전을 올린다. 이 세 수치는 **AI의 이미 검증된 bounded risk 판단 강도**에만 적용하며 기계 ENTER_NOW나 최종 주문 가격·수량 가드를 다시 쓰지 않는다.

## 5. 판정 함수·관측·발행 연결

`capture actual machine ENTER_NOW → exact AI input/response → validate raw response → shared auxiliary policy evaluation → effective verdict → existing composer → price/sizing/final guards`.

- `validate_mechanistic_risk_screen`의 입력 무결성/필수 사실 검사와, versioned soft risk 판단을 분리한다. 위험 근거 사실 자체를 바꾸지 않고 중요도와 허용 조건만 학습한다.
- 공유 평가 순서는 `exact venue/session → 판정 전 유형/state selector → 해당 profile의 prompt 선택 → 단일 AI 호출/원문 검증 → soft 근거 개수와 bound materiality 평가 → effective verdict`다. 같은 pure selector/evaluator를 장후 replay와 runtime이 호출한다. prompt가 달라진 후보는 해당 후보의 실제 raw 응답을 사용하며 부모 응답을 재사용하지 않는다.
- materiality는 이미 결합된 soft risk fact의 강도만 판정한다. bounded VETO→PASS에는 기존 setup/trigger 지지와 hard 부재에 더해, 관측된 adverse 수치가 해당 profile 경계 안임을 요구한다. PASS→VETO/CAUTION에는 유효 adverse fact와 경계 초과 근거를 함께 요구한다. 값 누락·만료·단위 충돌은 기존 부모 verdict 또는 더 보수적인 CAUTION으로 귀속하고 새 PASS 권한을 만들지 않는다. hard `BLOCKING_VETO_RISK_CODES`, source 무효, 제출 안전 가드는 항상 우선한다.
- raw verdict와 effective verdict를 모두 저장한다. 유효한 raw VETO가 새 soft policy에서 PASS가 되려면 필요한 긍정 사실·trigger·안전 조건이 모두 검증되어야 한다. raw 응답 위조나 raw hash 변경은 금지한다. PASS→VETO/CAUTION도 부정 사실과 정책 이유를 연결한다.
- 신규 effective assessment는 별도 versioned schema로 나타내고 기존 PASS의 `NO_BLOCKING_RISK` 계약에 raw VETO의 risk code를 무리하게 붙이지 않는다. old composer는 legacy adapter로 호환하고 새 composer는 raw/effective 양쪽 hash와 family decision을 검증한다.
- runtime trace에는 machine/AI hash pair, selector profile, raw/effective verdict, 바뀐 근거, 최종 submit guard disposition, 실제 order/terminal link를 남긴다. 최종 가드로 미제출이면 AI PASS 실제 진입으로 집계하지 않는다.
- 장중에는 단일 AI 응답에 유효성 검증과 작은 메모리 내 soft 평가만 적용한다. 투표용 재호출·동기 DB/파일 조회·장후 replay를 판정 경로에 넣지 않는다. 입력 생성→provider 요청 전 지연→provider 응답→soft 평가→최종 가드 시간을 나눠 계측하고, 실제 적용된 처리 예산·freshness 만료·provider 실패를 각각 기록한다. stale/invalid 응답을 재표기해 PASS로 사용하지 않는다.
- 정책 artifact는 기존 bundle의 `ai_policy` component를 확장하여 prompt/template hash, 네 축 parameter registry/version, 유형별 selector tree·parent fallback, source/evidence hashes, parent AI hash, 평가 basis, train/holdout 지표, effective_from, rollback을 저장한다. loader는 필수 field·허용 범위·profile 상속·source feature version을 검증하고 모르는 버전은 기존 검증된 AI 부모값으로 fail closed한다. attempt는 최종 선택된 leaf와 AI component hash를 고정해 중간 교체를 섞지 않는다.
- 기존 `entry_setup_paired_replay_batch`/`compact_auxiliary_paired_replay`가 source/label/학습을 담당하고 `mechanistic_entry_runtime_policy`가 발행한다. `entry_setup_live_policy`/`ai_engine_openai`/`entry_setup_evidence`와 기존 submit handoff가 소비한다. legacy `machine_microstructure_policy_approval`의 queue를 신규 AI 승인 통로로 재사용하지 않는다.

### 5.1 장후 생산자·선정·발행 결손 수리

1. **원천**: 실제 AI 호출의 machine `ENTER_NOW`·exact pre-AI input/response/prompt/model/policy hash·raw/effective verdict·판정 전 유형 feature·세 risk family 수치/as-of/source를 하나의 promotion 기회로 조인한다. 정상 PASS·VETO, CAUTION/INSUFFICIENT, 호출 실패, 최종 가드 미제출, 실제 주문/완료를 각각 분모로 보존한다. 9/23 제외 63건은 경로·비용 미완결 50, 중복 promotion 7, 자연 응답 무효 6으로 분해해 다음 실행에서 원인이 개선됐는지 같은 규칙으로 비교한다. prompt exact 원천이 0인 이유를 writer/조인/파일 경로별로 분해하고 새 자연 호출에서 exact 입력이 쌓이는지 별도 계약 테스트를 둔다. source gap을 손실 0이나 모델 거절로 바꾸지 않는다.
2. **경제성**: 부모/후보에 같은 10분 target/adverse/horizon·왕복 비용·venue/session·source cutoff를 적용한다. 동일 봉 순서 불명, 미래 정보 입력, missing cost는 censored/excluded로 남긴다. `COMPLETED + valid profit_rate`의 실제 보유·매도 결과는 별도 실현 성과이며 고정경로 label을 대신하지 않는다. 성공 PASS/올바른 VETO를 모두 보호하도록 전이표와 paired delta를 만든다.
3. **후보·선정**: 두 근거 개수 축의 3×3, 세 수치 family 경계, 유형/상태 parent·leaf, 세 prompt variant를 모두 후보 manifest에 등록한다. 각 축의 지원 분모·한 축 변경 시 행동 전이·비용 후 EV를 계산하고, 예산 내 공동 후보를 재평가한다. train과 미사용 날짜 holdout, 유일 기회/행동 변경·class 최소 바닥, 보정 승률, 비용 후 paired delta, 좋은 PASS 보존/잘못된 PASS 차단, leaf 대 parent를 같은 기회 manifest에서 검증한다. 미지원 수치/유형은 parent fallback 횟수로 남기며 해당 축을 평가한 것처럼 보고하지 않는다. 후보 부족은 `candidate_evaluated_but_not_promotable`, `search_incomplete` 또는 `source_gap`으로 명시하고 부모를 승계한다. 한 건 100% 승률로 승격하지 않는다.
4. **발행**: 현재 `auxiliary_stage`가 있으면 prompt 승격을 건너뛰는 publisher 분기를 제거하고, 같은 basis의 prompt 응답·soft/수치·유형 후보를 독립 검증한다. 두 축 이상이 동시에 통과하면 전체 leaf/parent와 prompt를 하나의 AI component로 병합해 한 번의 CAS/rollback receipt로 발행한다. 일부 축만 합격하면 해당 축만 바꾸고 나머지 축은 부모를 보존한다. legacy `promotion_valid`의 20/20·portfolio 결과를 신규 AI stage 통과로 대체하지 않는다. candidate response가 없는 prompt는 v3 carry하지만 **후보 생산·검증·발행 경로 코드는 완성**한다.
5. **보고·controller**: 최종 `selection_disposition`은 prompt·근거 개수·materiality·type selector의 선정/미선정/원천결손을 각각 소비하고, 실제 component 변경이 없을 때만 `incumbent_preserved`라고 한다. stage terminal·policy approval·bootstrap/PREOPEN·실제 loader/PID를 동일 generation으로 묶는다. PREOPEN wrapper의 AI 활성화 경고를 전체 성공으로 숨기지 말고 AI 가족의 명시적 `deferred`/carry와 첫 blocker를 기록한다. 기계 stage 성공은 AI 승인으로 전용하지 않는다.

### 5.2 생산자 원천 결손의 정확한 수리 조건

- 현재 prospective 계약의 writer `entry_execution_sizing_plan_sha256` → AI trace `entry_economic_plan_sha256` → owner replay seed `plan_sha256`를 `evaluation_attempt_id + plan_sha256`로 연결한다. source date, promotion, symbol, venue/session, machine bundle, prompt/model/input hash가 달라지면 합치지 않는다. 세 지점 각각의 `present/valid/joined/conflicted` 수와 최초 결손을 영수증에 기록한다. 9/23 `natural_exact_row_count=0`을 단순히 표본 부족이라고 닫지 말고 writer 누락, trace 누락, owner seed/완료 결손, 식별자 불일치를 구분한다.
- AI 판정 전 exact 입력·응답·source as-of·수치 materiality·유형 selector feature를 호출 시점에 저장한다. 장후에서 종가·체결 결과를 역산해 입력을 만들지 않는다. 기존 `ai_decision_trace`/`ai_decision_payloads`와 outcome label을 한 번씩 스트리밍·필요 키만 인덱싱하고, 중복·conflict는 임의 최신값 선택 없이 격리한다.
- 9/23의 `screened_total=74`, `eligible_count=11`, `excluded_count=63`과 제외 원인 50/7/6을 고정 회귀 기준으로 보존한다. 새 자연 원천에서는 writer→trace→owner→label 각 단계의 수와 제외 원인을 같은 형식으로 비교한다. exact 원천과 비용/경로 label 중 어느 쪽이 비었는지 분리하고, 미완결 label을 손익 0으로 채우지 않는다.

### 5.3 소비자 결함의 정확한 수리 조건

- 현 `auxiliary_soft_policy_v1` 두 필드 소비를 보존하면서 네 축의 versioned AI component/selector schema를 추가한다. `mechanistic_entry_runtime_policy`의 validator·publisher·dated activation·parent CAS, `entry_setup_live_policy`의 scope/profile/prompt 선택, `ai_engine_openai`의 실제 단일 호출·최종 composer까지 **같은 profile/AI hash/raw→effective verdict**를 대사한다. 옛 bundle은 기존 의미로 읽고, 새 필드가 누락·변조되거나 leaf가 미지원이면 검증된 parent로 되돌린다.
- prompt-only, 근거 개수-only, materiality-only, type-only 및 복합 합격을 각각 발행·재로드·롤백한다. soft-only 변경도 최종 `selection_disposition`에 반영한다. PREOPEN의 auxiliary activation 실패가 shell 경고로 흘러도 해당 AI family는 `deferred`/carry·첫 실패 이유를 남겨 bootstrap 성공과 구분한다. 날짜가 맞는 정책 파일만으로 소비를 증명하지 않고 실제 선택 release/PID의 첫 자연 AI 호출에서 profile·prompt·정책 hash를 확인한다.

### 5.4 장후 성능·결과 동일성 수용

- 변경 전 동일 frozen source로 현재 `main_auxiliary_policy`의 두 명령(`--execute-compact-candidate`, `--finalize-compact`)을 포함한 **stage 전체** `postclose_command_metrics_v1`을 기준선으로 저장한다. 현 wrapper의 계측은 stage 전체와 reaped child 범위이므로 이를 개별 명령 성능이라고 오인하지 않는다. 구현 시 두 명령의 경과·입력/후보/호출 수를 별도로 계측하고, 변경 후 **동일 source/manifest/host**의 stage 전체 wall·child CPU·peak child RSS·입출력 block operations·resource-guard 대기·exit/terminal 상태 및 새 명령별 경과를 비교한다. `bounded_wait`를 계산 시간에 합치지 않고, 측정 누락·다른 source·stale terminal이면 성능 PASS를 선언하지 않는다.
- 프로젝션 입력 파일은 날짜별 한 번씩 스트리밍하고 필요한 trace/payload/label 키만 유지한다. 결정론적 네 축 후보는 캐시한 판정 전 feature와 raw 응답으로 평가하여 추가 provider call 0건을 검증한다. prompt 후보는 frozen manifest의 cache hit/miss·신규 호출·token/비용·checkpoint/resume 수를 기록하고 유한 daily provider budget을 넘으면 그 후보만 명시적으로 `deferred`한다. 예산 부족을 빈 후보나 경제성 0으로 바꾸지 않는다.
- 동일 frozen 분모의 기존 incumbent·현 3×3 후보는 74/11/63·행동 전이·EV가 변경 전과 같아야 한다. 새 수치·유형·prompt 후보의 결과는 별도 열로 비교한다. 9/23 소형 원천뿐 아니라 더 큰 결정적 fixture에서 wall·RSS가 입력 기회/후보 수에 비례하는지 확인한다. provider 실행을 제외하거나 응답을 고정 캐시한 **결정론적 구간**이 같은 source 기준선 대비 wall 25% 이상 또는 peak RSS 25% 이상 증가하면 I/O 재읽기, 후보 중복, 캐시·메모리 보유를 원인별로 검토·수정하고 재계측한다. provider 대기 시간은 별도이며 postclose terminal이 당일 후속 handoff 창에 도달하는지도 확인한다.

## 6. 장중 정책 교체와 지속 승계

1. 코드·schema·consumer 리뷰/검증 후 배포본을 준비한다. 장중 현재 PID·machine/AI component·override·source cutoff를 다시 확인한다.
2. 후보를 고정 원천에서 재생·선정하고 적용 가능한 scope·지원 class·positive/negative 전이표·예상 다음 blocker를 남긴다. 기존 AI와 같은 행동이면 새 포인터를 만들지 않는다.
3. 같은 publisher lock에서 최신 bundle을 읽고 **AI component parent CAS**를 검사한다. 현재 machine component를 보존한 새 bundle을 atomic publish한다. 기계 policy만 바뀐 경우 지원 schema/cohort의 호환을 확인하며, 원래 기계 입력이 달라진 과거 AI 응답을 재작성하지 않는다. 호환성 불명확하면 해당 AI candidate만 보류한다.
4. machine/AI 동시 갱신은 한 pointer 아래 순차 CAS로 처리한다. 각 component를 고친 publisher가 상대 component를 오래된 dated bundle로 덮지 못하게 한다. AI rollback도 최신 machine은 유지한다.
5. attempt 시작에서 두 generation을 함께 pin한다. 진행 중 응답은 그 pair에만 귀속시킨다. 제출 직전 generation/유효시간이 달라지면 기존 신규진입 재확인 경로로 돌려 source와 AI를 다시 확인한다. response만 새 generation으로 재표기하지 않는다.
6. 코드 배포에 restart가 필요하면 기존 guarded procedure를 쓰고, 정책만 바뀌면 live loader의 다음 attempt에서 반영한다. 주문/보유 custody를 유지한다. 다음 날짜까지 기다리거나 시험 주문을 제출하지 않는다.
7. actual PID/start/release/AI component/effective verdict 영수증을 확인한다. 자연 호출이 없으면 `published_awaiting_natural_attempt`이며, synthetic 검증을 실제 소비로 표시하지 않는다.
8. 다음 적격 AI 정책/명시 rollback까지 carry한다. 기계 튜닝 실패·장후 전체 실패·날짜 변경으로 AI를 초기값으로 돌리지 않는다. 기존 `main_auxiliary_policy` 장후 stage가 같은 evaluator/validator/publisher를 사용한다. **정책 승인 후, 장중 교체에 대한 그 시점의 명시적 사용자 지시와 당일 checklist mutation gate 충족 시에만** `--activate-auxiliary-now --source-date YYYY-MM-DD`가 현재 machine/AI 부모와 보고서 재생 결과를 잠금 안에서 CAS 검사해 AI component만 즉시 활성화한다. 다음 거래일 07:35 preopen wrapper도 dated 후보에 같은 CAS를 적용한다. 후보가 없거나 AI stage가 deferred이면 현재 pair를 유지하며 날짜가 지났다는 이유로 무조건 재발행하지 않는다.

## 7. 구현·검증 순서

| 단계 | 구현 범위 | 필수 회귀/완료 근거 |
| --- | --- | --- |
| A1 | 실제 AI 모집단·exact prompt input·판정 전 유형/수치 producer·독립 label | 기계 nonentry 제외, VETO/PASS·censored·미제출·실현손익 분리; 9/23 제외 63건과 prompt `natural_exact_row_count=0`의 writer→trace→owner plan hash 첫 결손 재현·신규 자연 writer 검증 |
| A2 | 기존 두 근거 개수 축의 3×3·선정 기준 수리 | 한 건 100% 반례, 비용 후 EV 악화, 성공 PASS 차단, 올바른 VETO 해제, all-veto 분모 소실, 독립 날짜 holdout·낮은 class coverage 보류 |
| A3 | 세 bounded-risk 수치 registry와 공통 장후/장중 evaluator **구현 완료** | spread(bp)·signed pressure margin·사전 reward/risk 값/단위/as-of 검증; 각 family 후보/parent fallback, hard 우선순위, raw/effective hash, 누락·불일치 fail closed |
| A4 | 가격·tick/시가총액·유동성·변동성·구조 상태 selector와 leaf/parent 정책 **구현 완료** | 판정 전 동일 group key, UNKNOWN/희박 leaf parent fallback, leaf별 동일 분모·cost/holdout, 기계 유형정책과 독립; 장후/장중 동일 입력 동일 profile·verdict |
| A5 | prompt v3/opportunity/risk exact 재생·같은 basis 선정·통합 발행 **구현 완료** | 기존 cache 우선·유한 provider budget, 후보별 실제 raw 응답, 0 natural exact면 명시 carry, legacy 경제성 혼합 거절; prompt/soft/수치/유형 단독·동시 합격 시 단일 AI CAS |
| A6 | v1→새 AI schema validator/publisher/loader·장중 attempt | prompt/근거/수치/유형 단독·복합 재로드, 잘못된 candidate/schema/hash 거절, 동시 machine/AI CAS, stale response, mid-attempt 변경, rollback, 자정·재시작 carry, 단일 호출 지연 회귀 |
| A7 | 고정 source 재생·stage terminal·PREOPEN/장중 소비·성능 수용 | 네 축별 후보·선정 disposition, soft-only 반영, AI activation 경고=deferred, source/후보/적용 전후/실제 PID·자연 호출·후단 주문/비용 별도 receipt; 같은 frozen source의 stage wall/CPU/RSS/I/O·resource 대기·provider budget·후속 handoff 도달 비교 |

관련 테스트는 기존 compact replay, mechanistic policy, entry risk/composer, AI engine, submit handoff, stage controller 테스트에 추가한다. provider mock과 작은 paired fixtures로 구현 회귀를 하고 실제 후보 재생은 기존 budget 안에서 실행한다. Python compile·대상 pytest·diff/parser 후 재리뷰한다.

**완료 보고는 학습 완료 / 정책 선정 / 발행 / 실제 PID 소비 / 자연 PASS·VETO 변화 / 실제 주문·비용 후 성과를 분리한다.** 한 영역의 근거가 부족하면 해당 상태와 다음 source를 명시한다. 다른 hard guard·scale-in·청산 튜닝은 후속 별도 작업으로 남긴다.

## 8. 이번 계획 검증과 종료 기준

현행 두 축의 코드 존재는 정책 후보의 경제성·승격·자연 성과 완료를 뜻하지 않는다. 우선 9/23 source를 **읽기 전용 고정 재생**하여 74/11/63 분모, soft 9개 조합, prompt source gap, 부모 carry를 재현한다. 구현 후에는 네 축 각각의 합성 fixture(원천 수치/유형/후보 응답이 충분한 경우와 결손 경우)를 통과시키고 실제 bounded 장후 재생으로 코드 경로를 확인한다. legacy 9/23 자료에 없는 필드를 합성 값으로 승격하지 않는다. wall/CPU/RSS·provider call 수·manifest 수를 기록하고 전체 시장 AI 재호출은 하지 않는다.

**계획의 구현 종료**에는 ① writer→trace→owner plan hash와 네 축 전부의 source/후보/evaluator·train/holdout 선정, ② 같은 AI component의 v1/신규 validator·publisher·loader와 leaf/parent fallback, ③ stage·bootstrap/PREOPEN/장중 활성화·rollback 경로, ④ 네 축의 단독·복합·미지원 regression과 같은-source 결과 동등성·stage 성능 수용이 모두 필요하다. 한 축의 source가 자연일에 부족하면 구현을 생략하는 대신 그 축의 생산·선정·소비 fixture를 검증하고 실제 승격 상태만 `source_gap`/parent carry로 남긴다.

**운영·경제성 수용**은 별개로 ⑤ 실제 PID의 정책 hash 및 자연 판정 변화, ⑥ 후단 제출·`COMPLETED + valid profit_rate` 비용 후 성과를 검증한다. 원천일 부족으로 ⑤·⑥을 확인할 수 없으면 구현 완료와 별개로 자연 수용을 OPEN으로 둔다. 문서 수정 자체는 어떤 정책도 발행하거나 봇을 재기동하지 않는다.
