# 삼성전자 상시 감시 기계·보조 정책 구현계획 — 2026-10-03

## 결정과 적용 조건

[범위 재정리 계획](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)의 S0~S5를 보유 원천으로 실행했다. 아래는 연구 결과로 확정한 **운영 구현 설계**다. 삼성전자 전용 live selector/정책 schema는 아직 등록하지 않았다. 배포는 별도 지시까지 대기한다.

- 대상: `005930 + MAIN_FIXED_WATCH + KRX|KRX_REGULAR`. 다른 origin·세션·종목은 parent를 따른다.
- 연구 분모: 31시도, 2개 native admission. 학습9/30 12시도/1기회, 재사용 후단10/2 19시도/1기회. 삼성전자9/29의 다른 origin 4시도는 비교군이다.
- 30개 사전 정의 조합을 비교했다. `DEPTH_SUPPORTED + 현재 유효한 양의 매수 흐름/가격 반응`으로 허용된 soft 확인 대기를 대체하는 후보가 각 날짜1시도를 회수했다. 두 경로는 비용 결합 목표-first이며 각각 경로 순수익률 +0.1%다. 실제 체결·실현 수익이 아니다.
- 시간대/phase 제한을 추가해도 독립 지원수가 늘지 않았다. 60초 안에 같은 native admission·phase에서 연속2회 확인을 요구한 조건은 별도 반복성을 입증하지 못했다. 관측 상태 전이27구간을 새 승격 기회로 세지 않는다.
- 정식 gate: 학습 지원수 부족, 후단 지원수 부족, 후단 회수 지원수 부족, 미등록 의미 규칙 schema. 기존 gate를 유지한다. 이미 여러 번 사용한10/2는 독립 holdout이 아니다.
- 기존 삼성전자9개는 PASS 연구 집합이다. 이번 원응답 전수 검사에서는 유효 CAUTION 1개도 확인했다. fixed-watch로 exact 연결된 것은 PASS2·CAUTION1이다. 새 기계 ENTER2시도에 대응하는 AI 응답은0이다. 따라서 새 기계+보조 결합 성과는 null이다.
- **삼성전자 보조 정책은 공통 parent 상속이 현재 결론**이다. 응답이 없는 새 prompt/전용 soft 정책의 성능은 `not_evaluated_new_prompt_response_absent`다.

## 1. 정책 선택과 parent/child 결속

| 소유자 | 구현할 계약 | 종료 검증 |
|---|---|---|
| `entry_strategy_policy` | 승인된 child의 대상 필드를 symbol/origin/venue/session으로 명시한다. 현재 수치 feature에 가격을 종목 대용으로 넣지 않는다. | 대상 밖 action·threshold·source 요구가 parent와 완전 동일 |
| `mechanistic_entry_runtime_policy` | parent SHA, child SHA, source manifest, 대상일/만료일, 우선순위, rollback parent를 함께 검증한다. 같은 stage의 다른 child와 겹치면 선택하지 않는다. | 잘못된 날짜·origin·scope·parent, 중복 child, 누락 native lineage → parent 상속 및 이유 기록 |
| Main 판단 호출자 | 실제 stock/native watch receipt를 selector에 전달한다. 표시용 종목명·상시감시 env만으로 전용 정책을 고르지 않는다. | 실제 capture→assessment→AI trace에 동일 selector receipt 보존 |

별도 주문 프로세스, retired Samsung gateway, provider/계좌/quantity/holding/exit owner는 만들지 않는다. hard/protect/emergency·operator veto·custody는 기존 소유자가 계속 판단한다. 미지원 child 때문에 정상 parent를 임의 차단하거나 우회하지 않는다.

## 2. 기계 확인 규칙의 구현 경계

`entry_setup_evidence`의 등록된 순수 판단 함수에 승인된 확인 규칙을 추가하는 방식을 택한다. 연구 overlay를 runtime policy에 그대로 직렬화하지 않는다.

1. parent가 `RECHECK`이고 사유가 기존 soft 확인 대기일 때만 진입한다.
2. 대상 scope와 `DEPTH_SUPPORTED` family 일치, 최신의 사용 가능한 flow/price, parent의 해당 수치 경계를 모두 만족해야 한다.
3. unresolved risk는 연구에서 명시한 soft confirmation fact 집합에 한정한다. 미지 risk·hard/source·liquidity·local-breakout·선택된 기존 micro recipe를 우회하지 않는다.
4. 원래 fact, parent action, 대체 fact ID, 근거 입력 hash, child 선택 receipt를 함께 남긴다. 원본 `no_supported_setup`을 지우거나 가짜 긍정 fact로 바꾸지 않는다.
5. 외부 VWAP veto를 재적용하고 이후 계좌·주문·quantity·latency·holding guard를 그대로 통과해야 한다.

현재 연구용 구현은 `samsung_auxiliary_scope_research`와 기존 `entry_policy_confirmation_research`에만 있다. live 호출 연결은 하지 않았다.

## 3. 보조 정책과 응답 coverage

| 상태 | 처리 |
|---|---|
| 기존 정확한 input/prompt/parent/response가 있음 | 동일 원응답의 count/materiality/citation 정합성을 평가 |
| 새 기계 ENTER에 대응하는 응답 없음 | `auxiliary_response_not_observed_for_candidate`; PASS 대입 금지 |
| CAUTION 뒤 같은 기회에 INVALID 응답 | 후속 응답은 관측됐지만 해소·재진입·terminal 성공은 미입증 |
| 새 prompt만 설계됨 | 정적 schema 검토만 가능; 기존 답변을 새 prompt 성능으로 사용하지 않음 |

전용 보조 soft 정책은 기존 parent 대비 실제 행동 변화, 성공 제외, 회피 손실, 비용 결합 paired delta와 현재 정식 gate를 통과할 때만 별도 구현 대상으로 삼는다. 현재 후보는 행동 변화0으로 종료한다.

## 4. 장후 소비·발행·loader 및 마이그레이션

1. 삼성전자 fixed-watch, 삼성전자 다른 origin/세션, 그 외 유효 종목, 식별 결손을 분리한다. 원시 관측·원응답·native 기회·평가 적격 분모를 각각 봉인한다.
2. 연구 episode는 native admission에 역연결하고 같은 admission의 상관된 반복 관측을 같은 fold에 둔다. 실제 재시작/종료 receipt 없는 전이를 독립 에피소드로 승격하지 않는다.
3. 학습 전에 후보 정의·대상·source/code/cost/parent hash를 고정한다. 학습 선택 후 후단을 확인한다. 종목별 child의 split/selection manifest가 전체 KRX 정책으로 발행되지 않게 검증한다.
4. 공통 source capsule은 신규 기록에 추가하고 기존 v9는 호환 유지한다. 과거 metadata는 exact trace generation 또는 exact native link로만 보완한다. 과거 stop/fill/capacity/응답을 현재 값으로 복원하지 않는다.
5. child schema 등록이 승인되면 publisher/loader/정식 candidate validator를 같은 변경에서 수정한다. report→summary→strict→controller→dated PREOPEN의 scope·parent·child hash를 동일하게 유지한다.

이번 실행은 공통 source capsule·분모 ledger·종목 분리 연구 차단·비용 scope 결합 결함을 수정했다. 정식 child 발행과 canonical handoff는 실행하지 않았다.

## 5. 회귀·격리 검증 및 rollback

- 순수 판정: parent 보존, 대상 밖 동일성, stale/미래/route/unknown fact, 기존 micro recipe, liquidity/local-breakout/VWAP veto, hard safety를 확인한다.
- lineage: request/payload/schema/parent 충돌, 동일 attempt retry, partial JSONL/gzip, append 실패, 다른 native admission, 미래 응답, cost 날짜·scope 불일치를 검증한다.
- 분모: 같은 native ID가 양쪽 fold에 들어갈 수 없고, 관측 전이 수로 support를 늘릴 수 없다. 전체/삼성전자/그 외 cache와 발행 권한을 교차 사용하지 않는다.
- 재생성: 보유 자료만 사용하는 격리 cold/warm 실행의 내용 hash가 같아야 한다. source 변화·미완성 checkpoint는 재사용하지 않는다. 실제 wall/CPU/RSS와 원천 읽기를 기록한다.
- 운영 구현 승인 후에도 child 선택·PREOPEN·PID 소비·자연 실행·실현 수익을 각각 검증한다. source/계보 손상·order/hard guard 위반·승인된 canary rollback 조건은 parent SHA로 되돌린다. 성과 미입증을 성공으로 발표하지 않는다.

## 완료 및 남은 소유자

연구·설계 완료 기록은 [실행 리뷰](../audits/samsung-auxiliary-scope-execution-review-2026-10-03.md)와 당일 checklist `SamsungDedicatedMachineAuxiliaryResearch1003`가 소유한다. 삼성전자 live 정책 승격은 현재 조건 미충족이다. 그 외 기계정책은 새 회수 근거가 없어 변경계획 보류를 유지한다. 기존10/6 자연 수용/PREOPEN owner를 대체하거나 완료로 바꾸지 않는다.
