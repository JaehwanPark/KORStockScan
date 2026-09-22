# 보조 AI의 VETO 기회비용·PASS 오진입 튜닝 및 장중 정책 적용 계획

작성: 2026-09-22 KST
상태: **AI 단계 구현·회귀검증 중. 발행, 배포, 다음 장전 소비 및 자연 경제성은 별도 영수증으로 확인한다.**
실행 owner: [9/23 체크리스트](../checklists/2026-09-23-stage2-todo-checklist.md)의 `DirectFamilySourceRepairCompactAuxiliary`. 성공 PASS 대조군 반영은 이 owner의 기존 compact auxiliary source/label/evaluator 단계에 포함하며 별도 stage나 장후 실행기를 추가하지 않는다.
연결: [메인 기계판정](main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md), [장후 실행기 분리](machine-postclose-runner-separation-implementation-plan-2026-09-22.md).

## 1. 목표와 단계 경계

실제 메인 기계판정 ENTER_NOW 뒤 보조 AI에 전달된 기회만 대상으로 **수익 기회를 놓친 VETO를 PASS로 바꾸는 학습**과 **손실 위험을 허용한 PASS를 VETO/CAUTION으로 바꾸는 학습**을 함께 수행한다. 좋은 PASS와 올바른 VETO도 control 모집단으로 보존한다. 기계 BLOCK/RECHECK를 AI 학습에 섞거나 AI가 기계 action을 승격하지 않는다.

현재 compact runtime은 PASS만 기존 제출 경로로 보내고 VETO는 DROP, CAUTION/INSUFFICIENT/응답 실패는 WAIT·재확인한다. 실제 응답과 supporting/contradicting fact binding을 검증한다. confidence0~100은 현재 **schema 유효 범위**이며 실증적으로 보정된 진입 점수나 적용 임계치가 아니다.

현재 compact 튜닝은 학습20/holdout20·2일, portfolio 일별 이익, stress 및 운영 모델을 요구한다. 이를 새 **AI 단계 기회비용 계약**과 분리한다. 기존 계약·과거 보고서·정책은 frozen legacy로 읽고, 신규 평가에 old portfolio gate가 validator/publisher/loader에서 되살아나지 않게 schema/basis를 명시한다.

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
- 후보가 사실과 다른 판단을 한 것과, PASS 후 슬리피지/가격·수량/청산 때문에 실제 손실이 난 것을 구별한다. PASS 손실을 전부 AI 오류라고 단정하지 않는다.
- AI 단계의 최초 독립 평가 basis는 기존 outcome label의 같은 venue/session 10분 고정 target(+0.3%)/adverse(−0.7%)/종료 가격 경로에서 왕복 보수 비용을 뺀 `auxiliary_fixed_path_10m_v1`이다. 가격경로가 미완결·동일 봉 선후 불명·비용 누락이면 제외한다. 이는 기존 `entry_quality_path`의 **실제 계획 exact stop** 또는 체결 손익이라고 주장하지 않는다. 정확한 stop이 없는 과거 건을 임의로 보충하지 않는다. 실제 `COMPLETED + valid profit_rate` 및 같은 attempt의 실제 비용이 있는 경우만 별도 realized outcome으로 연결한다.
- 동일 봉 목표·손실 동시 도달, 종료 미확정, fill 불명확한 실현손익은 확정 성공/실패로 쓰지 않는다. 경로 라벨의 target/stop/horizon/cost 버전은 해당 평가 동안 고정한다.
- 날짜·종목·promotion 기회 단위로 동일 가중치를 부여하고, attempt 수가 많은 RECHECK/재호출이 점수를 부풀리지 않게 한다. 미래 경로는 label에만 쓰며 prompt와 selector에는 전달하지 않는다.

## 3. 후보 평가와 순위

### 3.1 서로 다른 두 후보 방식

A. **판정 기준/프롬프트 후보**: 기존 compact prompt template에서 선택된 소수 변형을 exact input으로 실제 재생한다. 현재 provider/model/timeout/토큰 budget을 유지한다. 후보 응답이 없는데 부모 응답을 복제해 후보 PASS로 처리하지 않는다.

B. **근거 임계치 후보**: 동일한 유효 AI 응답·근거 프레임을 공유 `evaluate_auxiliary_policy`에 넣어 위험의 중요도와 PASS 자격을 재판정한다. 응답 schema/발명 사실/기계 hard source 검증은 먼저 수행하며 실패는 non-exposure다. 후보가 요구하는 추가 근거가 기존 응답에 없으면 unsupported이며 해당 근거를 수집/재생한 뒤 평가한다.

최초 구현은 기존 compact 모듈 내 함수와 versioned policy block으로 만든다. 별도 모델·분류 daemon·DB를 추가하지 않는다. legacy 응답은 어댑터로 읽되 없는 필드를 사실로 채우지 않는다.

### 3.2 양방향 점수

기회별 비용 반영 경로를 y, PASS 여부를 p라 하면 `value=p*y`, `paired_delta=(p_candidate-p_parent)*y`다. VETO→PASS의 양수 y와 PASS→VETO의 음수 y 회피가 모두 개선에 기여한다. 동시에 좋은 PASS 차단과 올바른 VETO 해제가 손실로 반영된다. CAUTION은 이 즉시 노출 실험에서 non-PASS로 두되, 향후 재확인 손익을 0이라고 확정하지 않는다.

공통 승률 우선 선호를 반영한 **초기 설계값**:
- `pass_win_rate`: 선택 PASS의 기회 가중 승률.
- `good_pass_retention`: 양수 경로 기회를 PASS로 남긴 비율.
- `bad_pass_rejection`: 음수 경로 기회를 non-PASS로 바꾼 비율.
- `balanced_quality`: good retention과 bad rejection의 평균. 한 class가 없으면 그 class 비율은 null, 관측 class만 사용하고 coverage를 명시한다.
- `Q = 0.6 * pass_win_rate + 0.4 * balanced_quality` (각 비율0~1)는 양방향 진단값으로 남긴다. 후보가 점수 가중치를 바꾸지 않는다.
- **기계판정과 같은 선정 순위**를 사용한다. 기회 단위 PASS 승률의 support-adjusted 점수 → 선택 PASS의 비용 후 평균 경로 이익 → 동일 분모의 부모 대비 paired delta → 선택 기회 수 → 단순성 순이다. 1건/100% 승률이 과대평가되지 않도록 기존 `machine_support_adjusted_win_rate`를 재사용한다. Q·좋은 PASS 보존·나쁜 PASS 차단은 별도로 보고한다.
- 적격 후보는 부모 대비 평균 paired delta가 음수가 아니고 위 순위가 부모보다 높아야 한다. **절대 평균이익 양수는 요구하지 않는다.** 동일 행동이면 부모를 유지한다.

모두 VETO/CAUTION으로 바꾸어 분모를 없앤 후보, 허용 PASS0인 후보, 지원 자료를 의도적으로 제외한 후보는 적용 후보가 아니다. 무근거 all-PASS도 fact/guard 검증을 통과할 수 없다. 실제 경로가 모두 양수라면 근거를 충족한 all-PASS 자체를 금지하지 않는다.

평가 한 기회부터 실행하며 고정20회·2일·portfolio 이익 문턱을 재도입하지 않는다. 유효 후보가 없거나 바꿀 방향의 근거가 없으면 scope별 부모 carry이다. 부족한 class를 가짜 표본으로 채우지 않는다. Q는 양방향 진단값으로 계산하며 선정은 위의 기계판정식 보정 승률·비용 후 EV·paired 순위를 따른다.

### 3.3 성공 PASS 대조군을 추가 부담 없이 학습에 반영

성공 PASS는 기존 AI 호출 로그와 기존 가격 경로·비용 라벨을 재사용해 후보가 보호해야 할 양성 대조군으로 반영한다. 별도 AI 재호출, 새 저장소, 전 종목 재생은 요구하지 않는다.

- 대조군은 실제 machine `ENTER_NOW` 뒤 AI가 실제 호출되어 raw/effective verdict가 유효한 `PASS`였고, 해당 promotion의 완결된 비용 반영 경로가 양수인 기회로 한정한다. 단순 PASS, 미체결, 미완결·censored 경로는 성공으로 세지 않는다. 실제 `COMPLETED + valid profit_rate`는 별도 실현손익 표본으로 유지한다.
- 장후 `outcome_labels`/`compact_auxiliary_paired_replay`가 이미 만든 같은 attempt의 label을 verdict·input hash로 조인한다. 기존 라벨을 재생성하지 말고, 응답·label join이 없으면 그 행은 미연결 source gap으로 남긴다.
- deterministic 근거 임계치 후보는 기존 raw 응답과 fact frame을 공유 evaluator에 다시 넣는다. 추가 provider 호출 수는 0으로 제한하고, `good_pass_retention` 및 `pass_win_rate`에 성공 PASS를 포함한다. 후보가 성공 PASS를 non-PASS로 바꾸면 동일 기회 paired delta에서 그 기회 수익만큼 불이익을 받는다.
- prompt 후보가 필요한 경우에도 성공 PASS 행을 후보 manifest와 동일한 고정 분모에 넣는다. 기존 exact-input 응답 cache를 먼저 재사용하고, cache miss 재호출은 기존 최대 후보·provider budget 안에서만 수행한다. 성공 PASS만을 따로 표본추출하거나 평가 후 분모에서 제거하지 않는다.
- 독립 AI 단계 보고서가 존재하면 기존 owner-capital/exact-stop 기준의 prompt 승격 결과를 AI 단계 후보로 전용하지 않는다. 동일 고정경로·보정 승률 비교가 준비되지 않은 prompt 후보는 기존 prompt를 승계한다.
- 보고서에는 `eligible_successful_pass_count`, `linked_successful_pass_count`, `good_pass_retention`, 성공 PASS에서 바뀐 verdict 수, 추가 provider call 수를 기록한다. 이 값은 별도 score 보너스가 아니라 기존 paired score의 분모·전이 근거다.
- AI 단계 고정 경로의 target/adverse/horizon·왕복 비용·동일 route outcome provenance가 빠지면 PASS 행은 보존하되 success label은 미확정으로 분류하고 승격을 막는다. null을 0이나 성공으로 바꾸지 않는다. 기존 owner-capital/exact-stop 비교의 `exact_stop_distance_missing_or_invalid` 결손은 별도 legacy basis에 남는다.

성공 PASS 대조군 연결은 기존 compact auxiliary 평가 안에서 닫는다. 별도 장후 stage/cron, 모델 학습 서비스, 별도 승인 통로는 만들지 않는다.

### 3.4 시간·범위·계산량

- source generation과 부모 AI component를 pin하고 train에서만 후보·경계·학습 대상을 정한다. latest completed day는 가능한 경우 진단 holdout이며, 결과를 본 뒤 같은 holdout에서 다시 선택하지 않는다. 한 날짜뿐이면 holdout 없음으로 표시한다.
- 소스와 모델을 동일하게 맞춘 paired 비교를 수행한다. machine generation이 다른 기회는 층별 결과를 남긴다. 의미적으로 호환되는 입력 schema/지원 cohort에서만 묶고, 새로운 기계 scope에는 미학습 AI 임계치를 전파하지 않는다.
- 초기 prompt 후보는 부모+최대3개, deterministic 임계치 조합은 최대32개로 제한한다. source가 완성된 기회 → 기존 추천/오류 근거가 있는 기회 → 이전 train의 정보 가치 순서로 정한다. 분모 manifest와 가중치를 부모·후보에 동일하게 적용한다.
- 큰 모집단은 고정된 층별 결정적 표본으로 provider 재생을 제한하고 근거 임계치 평가는 확보된 유효 표본 전체에 수행한다. untouched 평가 집합을 보존한다. positive VETO/negative PASS만 골라 평가하고 좋은 control을 빼지 않는다.
- 비교 manifest는 후보 실행 전에 고정한다. 후보별로 실패 응답·손실 표본을 삭제해 분모를 바꾸지 않는다. 선택된 paired 표본의 응답이 미완성인 후보는 deferred이며, timeout/schema 오류를 올바른 손실 회피 점수로 세지 않는다. runtime은 그대로 WAIT한다. deterministic 후보의 원천 미지원은 사전 고정한 parent fallback으로 평가한다.
- exact input+prompt+model/provider+schema+policy hash로 응답 캐시를 묶는다. provider budget 소진 시 chunk를 저장하고 stage만 deferred 처리한다. 기계정책은 그대로 운영한다.

## 4. 런타임 조정 가능/불가능 항목

현재 코드에는 범용 `AI confidence >= X이면 PASS` 정책이 없다. 다음 표의 신규 임계치는 구현 대상이다. 현재 값과 신규 설계값을 보고서에서 분리한다.

| 분류 | 항목 | 튜닝/적용 계약 |
| --- | --- | --- |
| 조정 가능: 기존 version surface | compact prompt variant, 위험 설명·긍정 근거 보존 기준 | 영어 ASCII versioned template 후보 재생. provider/model은 고정 |
| 조정 가능: 신규 근거 개수 | `veto_min_independent_evidence_count` 초기 {1,2,3} | 같은 사실의 중복 인용을 한 증거로 세고 soft risk에만 적용. 확정 source/order hard veto는 제외 |
| 조정 가능: 신규 PASS 품질 | `pass_min_positive_evidence_count` 초기 {1,2,3} | 기존 필수 setup/trigger 사실을 모두 충족한 뒤 추가 품질 조건. 필수 사실 부재를 개수로 보상하지 않음 |
| 조정 가능: 신규 중요도 | soft risk family별 materiality boundary | 실제 판정 전 수치·단위·source가 있는 항목만 registry 등록. 우선 spread excess(bp), 실제 pressure adverse margin(point), 비용 반영 reward-risk 부족량을 점검. 원천 없는 항목은 부모 고정 |
| 조정 가능: 조건부 | 유형/state별 위 임계치 | 기존 shared selector 사용. train price/tick/liquidity/volatility·지원 metadata만 이용하고 unknown parent fallback |
| 조정 불가: schema/fact 무결성 | risk code enum, fact 존재·binding·충돌, confidence 정수0~100, schema/version/hash | validator로 고정. 허구/잘못된 응답을 완화해서 PASS로 바꾸지 않음 |
| 조정 불가: 기계 소유 | BLOCK/RECHECK/ENTER_NOW, 구조/트리거·기계 threshold | AI는 ENTER_NOW 모집단 안에서만 판단. machine component 변경 없음 |
| 조정 불가: hard source/runtime | stale/deadline/route·clock·epoch/crossed BBO, account/order/qty/cooldown, hard/protect/emergency, operator lock | 기존 owner 조건 우선. tuning 후보에서 제외 |
| 조정 불가: 호출 운영 | provider/model, timeout/retry, 토큰 한도, cache TTL | 별도 운영 범위. AI 품질 후보가 비용·운영 제한을 변경하지 않음 |
| 조정 불가: 후단 정책 | 가격·수량·분할·scale-in·청산·위젯/에피소드 custody | 각 owner 유지. PASS는 주문/체결 허가의 최종 단계가 아님 |
| 이번에는 조정 불가 | confidence cutoff, 목표/stop/horizon·비용 라벨, 점수 가중치 | confidence는 calibration 부재로 진입 임계치에 쓰지 않음. label/목적함수는 회차 내 고정 |

soft materiality 수치는 82개 machine registry를 복사하지 않는다. 기존 runtime AI fact binding에서 실제 조정 의미가 있는 것만 작은 allowlist로 관리한다. 지원되는 train 분포 경계를 초기 후보로 사용하고 scope별 단위와 유효 범위를 validator가 검사한다.

## 5. 판정 함수·관측·발행 연결

`capture actual machine ENTER_NOW → exact AI input/response → validate raw response → shared auxiliary policy evaluation → effective verdict → existing composer → price/sizing/final guards`.

- `validate_mechanistic_risk_screen`의 입력 무결성/필수 사실 검사와, versioned soft risk 판단을 분리한다. 위험 근거 사실 자체를 바꾸지 않고 중요도와 허용 조건만 학습한다.
- raw verdict와 effective verdict를 모두 저장한다. 유효한 raw VETO가 새 soft policy에서 PASS가 되려면 필요한 긍정 사실·trigger·안전 조건이 모두 검증되어야 한다. raw 응답 위조나 raw hash 변경은 금지한다. PASS→VETO/CAUTION도 부정 사실과 정책 이유를 연결한다.
- 신규 effective assessment는 별도 versioned schema로 나타내고 기존 PASS의 `NO_BLOCKING_RISK` 계약에 raw VETO의 risk code를 무리하게 붙이지 않는다. old composer는 legacy adapter로 호환하고 새 composer는 raw/effective 양쪽 hash와 family decision을 검증한다.
- runtime trace에는 machine/AI hash pair, selector profile, raw/effective verdict, 바뀐 근거, 최종 submit guard disposition, 실제 order/terminal link를 남긴다. 최종 가드로 미제출이면 AI PASS 실제 진입으로 집계하지 않는다.
- 정책 artifact는 기존 bundle의 `ai_policy` component를 확장하여 prompt/template hash, parameter registry/version, scope/tree, source/evidence hashes, parent AI hash, 평가 basis, train/holdout 지표, effective_from, rollback을 저장한다.
- 기존 `entry_setup_paired_replay_batch`/`compact_auxiliary_paired_replay`가 source/label/학습을 담당하고 `mechanistic_entry_runtime_policy`가 발행한다. `entry_setup_live_policy`/`ai_engine_openai`/`entry_setup_evidence`와 기존 submit handoff가 소비한다. legacy `machine_microstructure_policy_approval`의 queue를 신규 AI 승인 통로로 재사용하지 않는다.

## 6. 장중 정책 교체와 지속 승계

1. 코드·schema·consumer 리뷰/검증 후 배포본을 준비한다. 장중 현재 PID·machine/AI component·override·source cutoff를 다시 확인한다.
2. 후보를 고정 원천에서 재생·선정하고 적용 가능한 scope·지원 class·positive/negative 전이표·예상 다음 blocker를 남긴다. 기존 AI와 같은 행동이면 새 포인터를 만들지 않는다.
3. 같은 publisher lock에서 최신 bundle을 읽고 **AI component parent CAS**를 검사한다. 현재 machine component를 보존한 새 bundle을 atomic publish한다. 기계 policy만 바뀐 경우 지원 schema/cohort의 호환을 확인하며, 원래 기계 입력이 달라진 과거 AI 응답을 재작성하지 않는다. 호환성 불명확하면 해당 AI candidate만 보류한다.
4. machine/AI 동시 갱신은 한 pointer 아래 순차 CAS로 처리한다. 각 component를 고친 publisher가 상대 component를 오래된 dated bundle로 덮지 못하게 한다. AI rollback도 최신 machine은 유지한다.
5. attempt 시작에서 두 generation을 함께 pin한다. 진행 중 응답은 그 pair에만 귀속시킨다. 제출 직전 generation/유효시간이 달라지면 기존 신규진입 재확인 경로로 돌려 source와 AI를 다시 확인한다. response만 새 generation으로 재표기하지 않는다.
6. 코드 배포에 restart가 필요하면 기존 guarded procedure를 쓰고, 정책만 바뀌면 live loader의 다음 attempt에서 반영한다. 주문/보유 custody를 유지한다. 다음 날짜까지 기다리거나 시험 주문을 제출하지 않는다.
7. actual PID/start/release/AI component/effective verdict 영수증을 확인한다. 자연 호출이 없으면 `published_awaiting_natural_attempt`이며, synthetic 검증을 실제 소비로 표시하지 않는다.
8. 다음 적격 AI 정책/명시 rollback까지 carry한다. 기계 튜닝 실패·장후 전체 실패·날짜 변경으로 AI를 초기값으로 돌리지 않는다. 기존 `main_auxiliary_policy` 장후 stage가 같은 evaluator/validator/publisher를 사용한다. 오늘 원천에서 후보가 선정되면 `--activate-auxiliary-now --source-date YYYY-MM-DD`가 현재 machine/AI 부모와 보고서 재생 결과를 잠금 안에서 CAS 검사해 AI component만 즉시 활성화한다. 다음 거래일 07:35 preopen wrapper도 dated 후보에 같은 CAS를 적용한다. 후보가 없으면 현재 pair를 유지한다.

## 7. 구현·검증 순서

| 단계 | 구현 범위 | 필수 회귀/완료 근거 |
| --- | --- | --- |
| A1 | 실제 AI 모집단·raw/effective schema·독립 label | 기계 nonentry 제외, 원래 VETO/PASS·censored·미제출·실현손익 분리 |
| A2 | stage 지표·후보 재생·bounded 탐색 | false veto/false pass 양방향, 좋은 control 보존, all-veto 분모 소실, class 부족, 비용 누락 |
| A3 | 공유 soft 판단·registry·prompt | raw와 effective 구분, invented fact/없는 근거 거절, hard veto 보존, offline/live 동일 입력 동일 정책 일치 |
| A4 | 새 basis validator/publisher/loader | old20회·portfolio gate 미혼입, legacy load, 잘못된 candidate/schema/hash 거절 |
| A5 | 장중 component 적용·캐시·attempt | 동시 machine/AI CAS, stale response, mid-attempt 변경, rollback, 자정·재시작 carry |
| A6 | 고정 source 재생·실제 장중 적용·독립 장후 stage | source/후보/적용 전후/실제 PID 소비·예약 실행 receipt |

관련 테스트는 기존 compact replay, mechanistic policy, entry risk/composer, AI engine, submit handoff, stage controller 테스트에 추가한다. provider mock과 작은 paired fixtures로 구현 회귀를 하고 실제 후보 재생은 기존 budget 안에서 실행한다. Python compile·대상 pytest·diff/parser 후 재리뷰한다.

**완료 보고는 학습 완료 / 정책 선정 / 발행 / 실제 PID 소비 / 자연 PASS·VETO 변화 / 실제 주문·비용 후 성과를 분리한다.** 한 영역의 근거가 부족하면 해당 상태와 다음 source를 명시한다. 다른 hard guard·scale-in·청산 튜닝은 후속 별도 작업으로 남긴다.

## 8. 이번 계획 검증

세 계획의 상대 링크와 당일 stable owner를 점검하고 print-only backlog parser 및 diff 검증을 통과했다. 문서 전용 변경이므로 pytest/compile·실제 provider 재생·배포·장중 변경은 실행하지 않았다. 초기 Q 가중치와 신규 soft registry는 구현 시 versioned 계약으로 명시하며 기존 confidence를 보정 점수로 오인하지 않는다.
