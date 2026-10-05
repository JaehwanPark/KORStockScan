# 기계 후보 수용조건 보완 및 삼성전자 후속 검증계획 — 2026-10-05

현재 상태: §1~§7은 최초 계획 시점의 진단·설계이고, 실행 완료는 §8이다. 이후 사용자 요청에 따른 **비삼성1회 지정 코드 보완계획·삼성 추가연구계획**은 §9를 따른다. 새 계획의 작성은 지정 적용이나 추가 연구 계산 완료가 아니다.

## 1. 목적·현재 판단

사용자 요청은 결함보완계획 수립과 삼성전자 기존 정책 유지 사유·추가 연구 필요성 점검이다. 이번 산출물은 현재 코드와 보관 결과를 대사한 계획이다. 비삼성 수용 계약 변경, 삼성 후보 등록, 정책 발행·배포를 완료한 문서가 아니다.

- **비삼성:** `pullback_p60_v0`의 연구 개선은 재현된다. 관측 최초 신호와 native 승격 기회를 혼용하는 선정 연결, 계산/적격 상태 표시, 날짜 검사, 성공 보존 진단을 보완한다. 후보 규칙은 고정한다.
- **삼성:** 최신 `absorption_p60_v10`은 학습 선정됐지만10/2 기존 정책의 목표/손절 승률이 정의되지 않아 연구 우월 판정이 보류됐다. 현재 운영 생성기는 삼성 후보를 선정하지 않으며 최신 후보의 이후 날짜 검증 연결도 없다. 기존 정책이 우수하다고 입증돼 유지된 것은 아니다.
- **추가 연구 필요성:** 삼성은 고정 후보의 최초 신호·미도달 포함 결과·원천 시점·이후 날짜 연결을 한 번씩 검증할 필요가 있다. 이미 탐색한 임계값/시간종료/트레일링 조합을 다시 순회하거나 원천 수집을 확대하는 계획은 아니다.

근거는 [수용조건 대사](../audits/main-machine-admission-acceptance-contract-review-2026-10-05.md), [최신 관측 생성기 결과](../audits/machine-observation-generator-contract-review-2026-10-04.md), [이번 읽기 전용 점검](../../tmp/machine-acceptance-remediation-samsung-review-20261005/inspection.json)이다. 실행 소유는 [10/5 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)에 둔다.

## 2. 확정 결함과 설계 변경을 구분

| ID | 확인 내용 | 보완 | 완료 기준 |
| --- | --- | --- | --- |
| D1 | 비삼성 연구는 전체 원 관측 최초 신호, 최종 선정은 native ID 보유 부분집합. 확정4,368개 중4,244개 제외; 원 연구 선택 부모217/후보197과 최종32/3의 대상·시점·가중 단위가 다름 | 진입 교체 후보 전용 평가/수용 계약을 정의하고, 관측 성과와 native 경로 적격 상태를 모두 발행 | 원401선택 identity/raw/action/binary 차이0. 선정에서 임의의 native 부분집합으로 분모가 바뀌지 않으며 각 상태의 근거·이유가 보존됨 |
| D2 | 계산했으나 `candidate_evaluated=bool(chosen)`가 false; 학습 부적격 후보의 최상위 metric은0/null | 계산·학습 적격·독립 검증·최종 선택을 별도 필드로 기록하고 실제 계산 metric 유지 | 기존3건1승 진단을 보존하면서 `computed=true, train_qualified=false, selected=false`; 후보 미계산과 구별 |
| D3 | `retained_baseline_winning_attempt_count`에 후보 승리 전체 수를 넣음. 현재1이나 부모 승리와 교집합0 | retained/excluded/new winner를 trace 집합 연산으로 계산 | retained0·new1·excluded17. 성공 보존율은 진단으로만 유지하며 탈락 조건 없음 |
| D4 | 생성기는 후보 학습 날짜1개 이상, publisher는 모든 학습 날짜 선택을 요구 | 버전별 공용 acceptance validator를 사용하고 실제 source 날짜와 후보 선택 날짜를 구별 | 같은 payload에 generator/publisher/loader 판단·reason 동일. 유효한 선택0일과 원천 결손일을 구분 |
| D5 | Main 승률 진단의 `metric_role=sim_probe_ev` | Main 진입 승률 역할과 CF 진단 역할을 명확히 선언 | 승률 선정 필드가 Main 계약을 선언하고 실제 수익/주문 증거로 소비되지 않음 |
| D6 | 현재 삼성 생산 분석519건은 candidate action을 parent와 동일하게 둠. 최신 흡수 후보는 연구 전용·미등록 | 삼성 상태를 `candidate_not_registered`와 연구 결과로 명시. 이후 등록 여부는 삼성 S1~S3 결과로 결정 | 삼성 승계 사유에 비삼성3건을 사용하지 않고, 연구 후보 계산/운영 미선정을 표시 |
| D7 | 기존 삼성 다음 날짜 frozen 계약은 `foreign=up veto`, `past_gap_180 program_change=down` 두 예전 후보만 포함 | 최신 흡수 후보를 새 frozen manifest로 기존 이후 날짜 owner에 인계 | 기존 계약 보존, 최신 후보 ID/hash/평가 단위/시작일/parent/source 조건과 준비 adapter 검증. 새 날짜 성과는 별도 |
| D8 | Plan Rebase §7에 이전3/2날짜·80% winner retention 문구 잔존; 현재 코드/최신 사용자 기준과 충돌 | 본 계획에 충돌을 명시하고, 후속 기준 문서 정리 시 해당 문장을 현행 계약으로 교정 | 성공 보존 veto 재도입 없음. 현재 소유 문서와 코드의 날짜·단위·허들을 대사 |

D1의 학습 원천/단위 변경과 아래50% coverage 처리 등은 **정책 수용 계약의 설계 변경**이다. 단순 표시 오류 수정으로 숨겨 적용하지 않는다. D2~D5는 보고·검사 일관성 결함이다. D6~D7은 삼성 최신 후보의 운영/이후 검증 연결 상태다. Plan Rebase 등 기준 문서는 명시적 문서 정리 지시 범위에서 수정하며, 이번 계획은 이를 임의 편집하지 않았다.

## 3. 비삼성 진입 후보 수용 계약안

### 3.1 평가할 모집단과 역할

`stock_code != 005930`, `KRX|KRX_REGULAR`, 고정 `pullback_p60_v0`와 현행 부모를 대상으로 한다. ENTER/BLOCK/RECHECK 원 관측을 함께 읽고 원 raw hash·판정시각·완성봉·원 비용/stop·정확한 route를 결속한다. 같은 trace 중복은 제거하고 식별 가능한 불량만 제외한다. native ID는 원 값 또는 null로 유지한다.

후보 비교는 연구와 같은 **최초 신호 사건 → 비중복 가상 점유 → 종목×날짜×venue/session 동일 가중** 순서로 고정한다. 관측은 경제적 가설 평가 자료로 선언하며 native 실행·주문/체결 원천의 별도 적격성 검사를 대신하지 않는다. 실제 주문 cadence·pending/holding/cooldown 상태는 기존 runtime owner를 따른다. 연구의60분 점유를 운영 쿨다운으로 복사하지 않는다.

운영 generator와 publisher에 새 버전 `main_machine_observation_admission_acceptance_v1`을 명시적으로 등록하는 안이다. 기존 native VWAP veto의 계약과 새 진입 교체 후보의 계약은 버전별 분기한다. 기존 연구의 `promotion_pass=false` 파일을 그대로 운영 publisher에 통과시키지 않는다. 새 보고서는 원 관측 manifest·공용 평가기·선택 ID·집계·독립 날짜를 재검증한 증거를 갖춰야 한다.

### 3.2 수용조건 변경안

| 조건 | 진입 교체 후보 계약안 | 해석·검증 |
| --- | --- | --- |
| 선정 주지표 | 양 분할에서 기존보다 높은 비용 결합 목표 선도달 군집 승률 | 승패는 target/stop 확정만. 미도달·검열·결손을 임의 실패/0으로 넣지 않음 |
| 지원수 | 비삼성 학습30·독립 검증10 **경계확정 종목/날짜 군집**을 명시적 초기 계약안으로 검증 | 기존30/10 native 단위를 조용히 치환하지 않음. 새 버전/필드에 단위를 기록하고 반복 관측은 군집 수를 늘리지 않음. 군집 간 독립성은 입증으로 주장하지 않음 |
| 지원조정 비교 | 현행 함수의 양 분할+5pp를 명시적으로 유지하는 안 | 경험적 지원조정 점수로 표기하며 독립 Bernoulli 신뢰구간으로 주장하지 않음. raw 승률·지원수·점수를 함께 제공 |
| 기존 대비 선택50% | 새 admission 계약에서는 진단으로 이동하는 안 | 좁은 유형의 더 높은 승률을 일반 coverage만으로 탈락시키지 않음. 최소 지원수·원천 적격·독립 검증은 별도 유지 |
| 기존 성공100%/80% 보존 | 탈락 조건 없음 | 제외된 기존 성공·회피 실패·새 성공을 진단값으로 제공 |
| 날짜 | 이번 고정 연구의9/29·9/30·10/2는 discovery로 봉인. 그 이후의 미소비 적격 날짜를 독립 검증으로 사용 | 입력이 있는 모든 날짜의 census를 요구하되 후보 선택이 매일 있어야 한다는 암묵 조건은 두지 않음. 학습/검증의 날짜 목록과 sample floor는 공용 함수로 검사 |
| 원천 결손/기존 binary 없음 | `comparison_not_identifiable` 등 구체적 상태 | 원천 missing, 가격 경계 미도달, 후보 선택0을 구분. 기존 승률 null을0으로 대입하지 않음 |
| 출처와 실행 적격성 | 관측·native 분모를 함께 기록하고 실제 runtime은 기존 admission/custody/guard를 검증 | probe를 가짜 native로 전환하지 않음. 관측 성과만으로 native 호출 빈도나 실현 손익이 같다고 주장하지 않음 |

이 안은 현재 수용조건을 변경한 실행 결과가 아니다. 구현 시작 시 평가 계약과 fixture를 먼저 고정하고, 과거 후보가 통과할 때까지 숫자를 낮추는 재조정은 하지 않는다. 삼성의 날짜별1군집에 비삼성30/10을 복사하지 않는다.

### 3.3 보완 후 현재 자료에서 기대할 결과

- 기존401선택과 날짜별 승률을 재현해야 한다. 학습42.59→67.75%,10/2 탐색 비교53.70→75.00%, 전체45.75→70.20%다.
- 원 연구 학습 경계 군집68→55,10/2 비교27→28과 지원조정 개선을 그대로 기록한다. 이미 쓴10/2는 새 검증 표본으로 수용하지 않는다.
- 따라서 현재 결과는 `candidate_computed=true`, `observation_train_qualified=true`, `fresh_validation=not_observed`, `candidate_selected=false`가 기대된다. **계약 수정만으로10/6 새 정책 선정이 보장되지는 않는다.**
- 공통39군집의52.47→53.24%,10/2 미확정 배정 민감도-17.54~+41.23pp도 함께 보존한다. 모든 미확정 해소·최악 가정 우월을 새 탈락 조건으로 만들지 않는다.

## 4. 구현 순서·영향 파일·검증

| 단계 | 작업·기존 소유 파일 | 완료 기준 |
| --- | --- | --- |
| P0 계약·입력 고정 | `entry_admission_analysis.py`, `entry_observation_recipe_policy.py`, 기존 frozen 연구와 현재 report/parent/schema 비교 | D1~D8 및 위 제안값·평가 단위·날짜·authority가 fixture/manifest에 고정되고 역사 보고서는 보존 |
| P1 공용 수용 함수 | 역할상 `src/engine/scalping/postclose_entry_validation.py`의 기존 검증 소유를 우선 사용. 비대해지면 같은 package의 전용 helper 선택 이유를 명시 | legacy native와 새 observation 계약별 typed 입력·동일 reason. 생성기/publisher 중복 조건 제거. `src/engine` root 새 모듈 없음 |
| P2 보고·날짜·진단 수정 | `ai_action_outcome_calibration.py`, `entry_admission_analysis.py`, `entry_observation_recipe_policy.py` | computed/train/validation/selected 구분, 계산 metric 보존, winner 교집합, 정확한 역할, sample/source/holdout 상태. 기존 `candidate_evaluated`를 eligibility로 읽는 소비자도 함께 이행하며 boolean만 true로 바꾸지 않음 |
| P3 발행·소비 결속 | `mechanistic_entry_runtime_policy.py`의 stage/source 재검증·dated loader와 `entry_setup_evidence.py`/`entry_admission_recipe.py` | 유효 schema/parent CAS/date/hash/원천/공용 evaluator/manifest만 수용. 삼성·보조·타 session의 component 불변. unknown/stale/conflict·hard guard·주문·수량 소유 회귀 |
| P4 최종 보고·회귀 | `src/engine/automation/postclose_summary_handoff.py`의 stage registry·`stage_commands`·`_stage_output_issues` | 현재 `main_machine_policy`가 `--winrate-policy-only --admission-recipe pullback_p60_v0`를 호출함을 기준으로 연구 권고/검증 대기/최종 승계 이유를 마지막 소비자까지 전달. 새 wrapper/producer 중복 생성 금지 |
| P5 격리 재생·재리뷰 | 새 `tmp` 세대의 정확한3일 입력과 기존 연구 대사 | 부모/후보 행동 및401선택 차이0, 새 날짜 없음→발행 보류 재현. 4,244관측 제외가 자동 성능 실패로 요약되지 않음 |
| P6 후속 적용 검증 | 구현·리뷰가 닫힌 뒤 해당 적용 지시/현재 실행 owner 범위에서 수행 | 실제 선정일·유효일·release/rollback·strict/controller/prepared·당일 PID 각각 증빙. 다른 후보·미래 날짜 증거로 완료 합성 금지 |

표적 검증은 기존 `src/tests/test_entry_admission_analysis.py`, `test_entry_observation_recipe_policy.py`, `test_entry_first_signal_exit_research.py`, `test_postclose_entry_validation.py`, `test_mechanistic_entry_runtime_policy.py`와 해당 생성기 tests에 둔다. 새 synthetic fixtures는 독립 검증을 통과하는 정상 payload와 한 조건씩 손상한 거부 payload를 모두 포함한다.

필수 회귀는 (1) 높은 승률·충분한 지원·선택50% 미만의 신규 계약 후보, (2) 기존 성공 일부 제외, (3) probe ID 없음과 raw/hash 결손의 서로 다른 처리, (4) candidate 선택0일과 source 없는 날짜, (5) 관측 중복/다음날 누출, (6)10/2 재사용 검증 거절, (7) 계산됐지만 부적격인 후보의 metric 보존, (8) winner 교집합, (9) generator/publisher/loader 동일 판정, (10) scope·source·authority·CAS 거절이다. 통과 후보 fixture가 있어야 항상 승계하는 구현도 검출할 수 있다.

각 단계는 구현→리뷰→수정→재리뷰→해당 pytest/compile/diff로 닫는다. 장후 전체 재생은 표적 검증 뒤 영향 단계와 마지막 소비자에 한정해 필요성을 결정한다. 자동화 규칙 변경 시 운영 문서와 checklist를 같은 변경에 반영한다.

새 acceptance 버전의 source·kernel·학습/검증 날짜·선택 manifest를 publisher와 loader가 다시 확인하도록 한다. 기존 artifact를 새 단위로 재해석하지 않으며, 버전/단위 불일치나 일부 소비자 미이행이면 현재 정책을 승계하고 계약 오류를 표시한다. source가 변하면 새 generation으로 계산하며 역사 report bytes는 덮어쓰지 않는다. 후속 적용의 rollback은 직전 유효 machine component/hash를 사용하고 다른 family·custody·주문 guard를 보존한다.

## 5. 삼성전자가 기존 정책을 유지한 세 가지 이유

### 5.1 최신 후보의 실제 연구 결과

아래는 삼성 최신 후보 `absorption_p60_v10`이며 예전 외국인/프로그램 veto 두 후보와 다르다. 원 관측519건, 전체 origin 연구와 fixed-watch 하위집단을 구분한다.

| 구간 | 기존 | 최신 후보 | 판단 |
| --- | --- | --- | --- |
| 9/29·9/30 학습 | 목표3·손절5, 날짜 동일 가중21.43% | 목표4·손절4·시간종료1·미확정1, 날짜 동일 가중50.00% | 학습 선정, 각2날짜 군집 |
| 10/2 비중복 선택 |2건 모두60분 미도달 |8건: 목표4·손절2·60분 미도달2 | 기존 목표/손절 승률 null, 후보66.67%; 비교 보류 |
| 10/2 유효 가격경로 종료의 양수 비율 |1/2=50% |4/8=50% | 기존 고정 선택의 산술 진단. 실제 체결/실현 승률 아님 |
| 같은 가격경로 종료의 평균 CF |−0.2300% |−0.3079% | 해당 종료 모델에서 후보 우수 미입증. 기계 진입의 자동 탈락 조건으로 사용하지 않음 |

기존 두 미도달은11:01:24와13:04:13 진입이며10분 이후까지 이미 평가했다.60분 종료 가격CF는 각각 **+0.04172%, −0.50176%**다. ‘미도달이라 가격자료가 전혀 없다’는 뜻이 아니다. 정해진 목표+0.1% 또는 원 손절에 먼저 닿지 않은 것이다. 비용·부분봉·순서 결손과 구별한다.

10/2 양쪽 선택10건의 원 identity/raw/parent와 target/stop/timeout 상태를 현재 생산 분석에 대사해 차이0을 확인했다. 현재 생산기는 timeout의 종료수익을 null로 두므로 위 종료 CF는 원 연구가 봉인한 별도 진단값을 인용한다. source 시점/비용을 바꿔 새로운 성과로 계산하지 않았다.

원 연구600초 사전 축소에서는10/2 후보가 목표0·손절1·미도달2, 기존은 선택0이었다. 이 값은 열등성의 확정 비교도 아니지만,66.67%가 관측 빈도·첫 선택 시점과 무관한 결과가 아니라는 점을 보여준다.

### 5.2 운영 연결 상태

현재 `winrate_policy_2026-10-02.json`의 `admission_analysis.samsung_candidate_selection`은 `separate_owner`다. 삼성519건의 부모/후보 행동 차이는0이며 ENTER38·RECHECK340·BLOCK141을 그대로 재생한다. 공용 운영 `entry_admission_recipe.py`가 등록한 것은 **삼성전자 제외 조건 `exclude_005930`의 pullback 하나**다. 삼성 absorption은 `unregistered_report_recipe`, 연구 보고서는 `policy_by_scope={}`다.

현재와10/6 staged의 KRX 정규장 machine hash는 모두 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`다. **삼성 최신 후보의 운영 비교·선정 자체가 연결돼 있지 않으므로 비삼성 계약만 고쳐도 삼성 정책은 바뀌지 않는다.** 비삼성3건1승을 삼성 유지 근거로 쓰지 않는다.

### 5.3 이후 날짜 인계의 누락

기존 `SamsungFrozenCandidateValidation1006`이 가리킨 frozen 파일은 `parent_only|foreign=up|veto`, `parent_only|past_gap_180|program_change=down` 두 후보만 담고 있다. 최신 `absorption_p60_v10`은 포함하지 않는다. 과거 두 후보를 다음날 검증해도 최신 흡수 후보의 검증이 완료되지 않는다.

10/6 native projection·원 payload·보관 체결·호가4경로는 이번 확인 시점에도 부재다. 휴장일의 미래 원천 부재를 장애나 연구 실패로 처리하지 않는다. 최신 후보의 준비 adapter·평가 계약을 먼저 봉인하고 기존 이후 날짜 소유자에 추가 인계한다.

## 6. 삼성 추가 연구는 세 단계로 한정

| 단계 | 질문·실행할 검증 | 종료/다음 판단 |
| --- | --- | --- |
| S1 최신 후보의 첫 신호·관측 빈도 | `absorption_p60_v10` replace·p60·trusted10·원 guard·비용·10분→60분을 고정. 원519관측에서 전체 origin과 fixed-watch206을 구분하고 미래 label 없이 첫 신호 구간/비중복 점유를 구성. `entry_first_signal_exit_research.py`는 현재 비삼성만 허용하므로 group을 바꿔 우회하지 않고 삼성 전용 adapter/검증을 구현 | 날짜별 부모/후보 첫 선택, 반복 제거 전후 승률·미확정·원watch/date 지원수를 확정. 기존600초 결과를 목표로 threshold를 바꾸지 않음 |
| S2 미도달 포함한 비교 목적 | 동일한 S1 선택을 고정해①목표/손절 확정 승률②목표/(목표+손절+완전60분 미도달) 도달률③경계 종료 또는60분 종료 가격의 비용 후 양수 비율을 나란히 계산. 선택 ID/점유·표본·양수0/음수/미확정·종료시각을 함께 기록. 알 수 없는 경로는 분모 밖 결손으로 공개 | ‘목표 먼저 도달’과 ‘시간 내 순이익 양수’ 중 어떤 개선이 있는지 `improves/no_improvement/not_identifiable`로 확정. 현재 fixed 선택은 도달률0/2→4/8, 양수 비율1/2→4/8이므로 지표마다 결론이 다름. 이 사후 진단을 과거 독립 검증으로 표시하지 않음 |
| S3 원천 시점·최신 후보 인계 | 원 capture의 전체 feature와 원시각 receipt를 기준으로 재생. 과거 최신 snapshot 전체 feature 입력이 보관되지 않은 경우 부분3필드 교체 효과와 혼합하지 않음. 최신 후보/표현식/parent/kernel/평가계약을 새 frozen manifest로 만들고 기존 다음날 owner에 연결 | 같은 입력의 연구/공용 평가 일치 또는 식별 불가 사유. 이후 날짜 intake 정상·거절 fixture 및 source 부재 대기 검증. 원 자료 없이 새 정책 성능을 주장하지 않음 |

위 작업은 기존 자료에서 계산 가능한 질문만 닫는다. 양수 비율/도달률을 새 운영 주지표로 채택하려면 결과를 보기 전 고정한 계약과 이후 날짜 검증이 필요하다. 기존 binary null을0으로 강제하거나 시간종료 미도달을 실제 손절로 바꾸지 않는다. 삼성의 반복8관측이 원watch1개·하루 군집1개라는 사실을 유지하며 이를 독립8기회로 올리지 않는다. 비삼성30/10군집 규칙을 단일 종목에 복사해 자동 선정 불능으로 만들지도 않는다.

추가 임계값·외부 환경·새 원천 탐색은 이번 S1~S3 범위에 없다. 세 단계가 끝나면 고정 후보의 준비 권고/개선 없음/판단 불가와 구체적인 부족 항목을 기록하고 종료한다. 이후 자연원천은 기존 `SamsungFrozenCandidateValidation1006`에서 검증하며, 기존 장전 `SamsungPremarketForwardValidation1006` 및 Main/Widget/Episode 기동 owner를 합치지 않는다. 다음날 자료가 없다는 이유로 과거 연구를 반복하지 않는다.

## 7. 계획 완료와 구현 완료의 기준

이번 완료 범위는 D1~D8의 근거·영향 파일·수용 계약안·회귀·예상 결과, 삼성 최신/과거 후보의 구분·실제 승계 경로·S1~S3·후속 owner 인계다. 계획 리뷰에서는 최신 원 보고서/정책 hash 보존,10개 삼성 선택 대사, 로컬 링크/중복 소유/권한·diff·print-only parser를 확인한다.

후속 구현 완료는 P0~P5와 삼성 S1~S3 각각의 코드 리뷰·표적 검증·새 세대 산출물로 판단한다. 경제적 우월성이 미확정인 상태를 구현 실패나 정상 선정으로 바꾸지 않는다. 배포와 당일 정책/PID 소비는 P6의 별도 증거다. 외부 Project/Calendar 동기화는 실행하지 않는다.

이번 계획의 리뷰·보완·재리뷰와 [검증](../../tmp/machine-acceptance-remediation-samsung-review-20261005/validation.json)을 완료했다. 입력7파일 hash 보존, 삼성10개 선택 대사 차이0, 현재/10/6 machine hash 동일, 후속 소유7개 각각1건·print-only parser29항목·로컬 링크·diff를 확인했다. 코드 변경이 없는 문서/읽기 전용 점검이므로 거래 pytest와 정책 재생성·배포·재기동은 수행하지 않았다.

## 8. 사용자 실행 지시에 따른 구현 결과

P0~P5·S1~S3를 실행했다. 전용 순수 수용 helper와 삼성 adapter를 `src/engine/scalping`에 두고 generator/publisher/loader/최종 보고 연결을 보완했다. 비삼성401선택 및 연구7,069관측 대사 차이0, 현재 계약의 학습 승률45.75→70.20%, 학습 적격·새 날짜 검증 대기다. 삼성 첫 신호 축소 후10/2 결과는 같고 목표 도달률0→50%, 비용 후 양수 비율50→50%다. 최신 absorption frozen과10/6 대기 adapter를 기존 이후 날짜 owner에 인계했다. 실제 세부 결과·리뷰·복원 정리 증빙은 [실행 리뷰](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md)에 기록한다. 원 계획의 수치 제안은 새 계약 버전으로 구현했으며 D8의 기준 문서 잔존 문구는 이번 범위에서 임의 변경하지 않았다.

## 9. 지정 적용과 추가 연구의 후속 상세계획

사용자는10/6에 신규 정책을 먼저 지정하고 장후부터 유지·교체를 판단하는 방식의 코드 보완 상세계획과 삼성 후보 추가연구계획을 요청했다.

1. [비삼성 지정·적용 후 장후 비교 상세계획](non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md): 고정 `pullback_p60_v0`1회 지정, 기존 dated generation의 명시적 supersession·CAS·복원, 기존 B0/지정 C0/실제 incumbent·capture 정책 분리, 고정 두 정책의 양방향 비교와 이후 새 후보의 자동 검증, 삼성 component 동등성, 마지막 장전 소비까지의 코드·회귀·실행 순서를 규정한다.
2. [삼성 원천 차이·가격경로 추가연구계획](samsung-absorption-differential-and-path-research-plan-2026-10-05.md): 기존 S1~S3 결과를 보존하고 전체519/fixed-watch206 원천에서 성공·손절·미도달 차이, 같은 사건의 진입 시점 효과, 최대5개 변형을 검증한다. 삼성 연구 주지표의 별도 제안·null/검열·이후 날짜와 원천 부재 종료를 명시한다.

실행 owner는 각각 `NonSamsungDesignatedPolicyImplementation1005`, `SamsungAbsorptionDifferentialResearch1005`다. 이후 날짜 비교·실제 기동은 기존 owner를 재사용한다. 계획 문서 작성 중 코드·정책·release·10/6 준비 artifact를 변경하지 않는다. 현재 정책은 §8의 승계 상태를 유지한다.
