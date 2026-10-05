# 비삼성 기계정책 1회 지정과 적용 후 장후 비교 — 상세 구현계획

작성일: 2026-10-05 KST. 상태: **계획 수립 완료, 구현·지정 발행 미실행**.

## 1. 목적과 현재 기준

사용자가 제안한 순서는 `다음 영업일 신규 정책 지정 → 그날 장후부터 유지·교체 판단`이다. 대상은 Main의 `stock_code != 005930`, `KRX|KRX_REGULAR`, 고정 `pullback_p60_v0`다. 삼성·보조 AI·Widget·Episode의 정책 지정으로 확대하지 않는다. 이 문서는 구현계획이며 실행 영수증이나 신규 정책 적용 완료가 아니다.

[선행 실행 결과](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md)에서 후보는 계산·학습 적격이며, 탐색 자료의 군집 승률은45.75→70.20%다. 미선정 사유는 새 날짜 검증 부재다.9/29·9/30·10/2의 탐색 이력은 보존한다. 지정 적용 시에도 이 날짜들을 독립 검증으로 재분류하지 않는다.

계획 intake HEAD는 `161c11e7`, 선택 코드는 `c8c00c06`이다. 현재 bundle `6785d52e…`,10/6 예정 bundle `3c500f6a…`, KRX machine `d94fecaf…`를 [intake](../../tmp/designated-machine-and-samsung-planning-20261005/intake.json)에 봉인했다. 구현 시작 시 현재 상태를 다시 읽어 CAS 기준을 갱신해야 한다.

## 2. 실제 코드에서 확인한 보완 지점

| 문제 | 현재 소유 | 보완 방향 |
|---|---|---|
| 새 날짜 검증이 없으면 `candidate_policy=null` | [entry_admission_acceptance.py](../../src/engine/scalping/entry_admission_acceptance.py) | 자동 선정 결과는 유지하고, 지정 적용 근거를 별도 계약으로 발행 |
| 발행기가 successor hurdle과 report reason을 재검증 | [mechanistic_entry_runtime_policy.py](../../src/engine/scalping/mechanistic_entry_runtime_policy.py) | 독립 검증 PASS를 위조하지 않는 지정 전용 stage/loader 검증 |
|10/6 dated 정책은 이미 발행됐고 다른 세대의 덮어쓰기를 거부 | 같은 파일의 `stage_winrate_policy` | 명시적 supersession receipt·이전 세대 보관·정확한 CAS로 교체 |
| 분석기는 현재 parent에 recipe를 붙여 후보 구성 | [entry_admission_analysis.py](../../src/engine/scalping/entry_admission_analysis.py), [entry_admission_recipe.py](../../src/engine/scalping/entry_admission_recipe.py) | 적용 후 parent와 candidate가 같아지는 자기비교 제거; 종전 기준 정책 별도 보존 |
| stage/summary/strict가 기존 disposition과 발행 증빙을 검사 | [postclose_summary_handoff.py](../../src/engine/automation/postclose_summary_handoff.py), [runtime_approval_summary.py](../../src/engine/runtime_approval_summary.py), [verify_threshold_cycle_postclose_chain.py](../../src/engine/verify_threshold_cycle_postclose_chain.py) | 지정·자동 선정·승계·미관측을 마지막 소비자까지 일치시킴 |
| 삼성 adapter가 전체 parent hash 동등성을 요구 | [samsung_absorption_acceptance_research.py](../../src/engine/scalping/samsung_absorption_acceptance_research.py) | 비삼성 recipe만 추가된 경우의 삼성 component 동등성 검증; 단순 hash 검사 삭제 금지 |

## 3. 지정 적용 계약

### 3.1 적용 범위와 정책의 수명

- 지정 대상일은 **2026-10-06 한 번**이다. 해당일의 Main 기동 전 준비까지만 새 지정을 수용한다. 첫 적용/PID 소비 뒤에는 같은 지시를 다시 행사할 수 없다. 늦게 실행하면 `target_window_closed`로 닫고 다른 날짜로 자동 이동하지 않는다.
- 지정된 정책 자체는 다음 정상적인 정책 선정 또는 명시적 안전 복귀까지 승계된다.10/6 장 마감에 자동 만료하거나, 영구 잠금으로 다른 후보의 선정을 막지 않는다.
- `candidate_policy = candidate_policy(B0)`로 현재 고정 규칙을 구성한다. 압력60 이상·신뢰 tick10 이상·양의 순공격 delta·micro VWAP 이하 등 recipe 값은 그대로 고정한다. arbitrary threshold/환경변수 입력으로 확장하지 않는다.
- 최초 지정에만 **새 날짜 검증 선행 조건**을 적용하지 않는다. 기존 source/cost/stop/guard, 후보 학습 적격, recipe·원천 hash 및 검토 결과는 검증한다. 현재 고정 보고서에 새 결함이나 추가 실패 이유가 생기면 지정 성공으로 처리하지 않는다.
- `adoption_basis=operator_designation`, `validation_status=not_observed`, `evidence_qualified_selection=false`를 기록한다. 기존 자동 보고서의 `candidate_selected=false`를 true로 바꾸지 않는다. 지정 성공 여부는 `designated_policy_staged`와 `designated_policy_activated`로 별도 표현한다.

### 3.2 보존해야 하는 네 가지 정책 식별자

| 이름 | 의미 | 사용처 |
|---|---|---|
| `B0` | 지정 직전의 종전 machine component 및 원 bundle | 고정 비교 기준·복원 기준 |
| `C0` | `B0`에서 구성한 `pullback_p60_v0` | 지정 후보·고정 비교 기준 |
| `I_t` | 해당 시각 실제 적용된 incumbent component | 실제 판정 재현·다음 발행의 parent CAS |
| `P_t` | 관측에 기록된 당시 bundle/component | capture의 실제 소속과 당시 행동 검증 |

`comparison_reference_sha256`와 `activation_parent_sha256`를 별도 필드로 둔다. B0가 과거 정책이어도 실제 발행은 최신 I_t를 parent로 사용한다. 실제 기록 행동은 P_t로 재현하고, B0/C0 행동은 같은 raw에서 재계산한 비교 행동으로 기록한다. B0 행동을 당시 실제 행동으로 강제하지 않는다.

### 3.3 지정 artifact 제안

제안 schema는 `main_machine_operator_designation_v1`이다. 최소 필드는 request ID·사용자 실행 지시 참조·작성/적용일·scope·recipe ID·B0/C0 policy와 hash·기존 staged bundle hash·고정 연구 report/kernel/source hash·review receipt·허용 component diff·1회 사용 상태·후속 비교 계약·복원 generation이다. 지시 참조는 후속 실제 실행 지시에서 채우며, 계획 문장을 실행 승인 영수증으로 사용하지 않는다.

지정 artifact에는 holdout PASS나 실제 수익 증거를 만들지 않는다. 경제성의 미확정 상태와 운영자의 지정 근거를 함께 공개한다. source·권한·날짜 오류가 있으면 파일 발행을 거절한다.

## 4. 이미 준비된10/6 정책의 교체와 소비

1. publisher lock 아래 현재/예정 정책·selection·prepared·활성 Main PID 소비 상태를 재조회한다. 예상 B0·기존 staged SHA가 하나라도 바뀌면 충돌로 중단한다.
2. 기존 dated 파일과 generation·관련 원보고서를 원 bytes로 보관한다. 새 지정 generation과 `supersedes_bundle_sha256`, request ID를 먼저 작성하고 hash·component 차이·loader readback을 검증한다.
3. dated canonical 파일은 검증된 새 generation으로 원자 교체한다. 중간 실패를 journal에 기록하고, 재실행은 같은 request/hash에서만 idempotent하게 완료한다. 여러 파일 전체가 원자적이라고 가정하지 않는다. 불완전 transaction은 activation을 차단한다.
4. stage verifier는 보관된 기존 보고서 → 기존 dated generation → 허용된 지정 supersession → 새 dated generation을 검증한다. 기존 자동 보고서를 새 지정의 우월성 증거로 쓰지 않는다. 승인되지 않은 기존 날짜 파일 교체는 계속 거부한다.
5. source10/2 report를 재조회/복구하더라도 지정 generation을 다시 incumbent으로 덮어쓰지 않는다.10/6 이후 일반 장후 발행은 새 I_t를 parent로 사용한다.
6. 장전 activation은 정확한 target day와 request·generation·release를 대조하고 current를 전환한다. 먼저 지정한 시각이나 코드 배포를 PID 소비로 표시하지 않는다.
7. 관련 summary/checklist를 고정한 뒤 **strict → 전체 DONE controller → prepared**를 새 세대로 생성한다. 기존 준비 PASS는 역사 증거로 남긴다.10/6 실제 PID 확인은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

최초 지정용 journal/receipt와 후속 자동 발행은 기존 `main_machine_policy` 단일 writer 아래 분기한다. 같은 날짜에 별도 지정 wrapper와 자동 publisher를 경쟁 실행하지 않는다. 비삼성 실제 적용이 확인되지 않으면10/6이라는 달력 날짜만으로 `post_apply`를 선언하지 않는다. activation 시각·실제 관측 P_t·PID receipt를 대사하고, 이전 시각 자료는 `pre_apply`로 분리한다. 준비/기동 실패와 실제 적용 후 source 부족은 다른 상태다.

Main의 지정 범위 밖 정책과 최신 보조 AI component를 보존한다. 안전 복귀는 검증된 종전 machine component만 복원한다. 원 bundle 전체를 복사해 보조 AI·다른 scope·custody를 과거로 되돌리지 않는다.

## 5. 지정 후 장후 판단 계약

### 5.1 동일 자료 비교

ENTER/BLOCK/RECHECK 전체 원 관측을 그대로 읽고 삼성 제외·KRX 정규장·원시각·비용/stop을 검증한다. 양 정책에 동일한 입력 집합을 제공한 뒤 각각 최초 신호와 비중복 점유를 재생한다. native ID 없는 관측과 raw provenance 결손을 구별한다. 실제 주문 이후 감시 중단 때문에 남지 않은 관측은 복원하지 않고 관측 가능 구간/공백을 공개한다.

10분 미도달은 기존 완료 가격으로60분까지 평가한다. 원 stop 이후의 반등을 원 진입의 승리로 바꾸지 않는다. 군집 단위는 종목×날짜×venue/session 동일 가중이다. 실제 제출·체결·실현 손익은 별도 결과다.

### 5.2 고정 두 정책의 비교와 새로운 후보 탐색을 구분

아래는 **후속 구현에서 고정할 신규 계약안**이며 현재 자동화의 동작이라고 주장하지 않는다.

| 경로 | 수용조건 제안 | 날짜 사용 |
|---|---|---|
| 최초 C0 지정 | 고정 후보 학습 적격 + 명시적1회 지정·원천/guard 검증 |9/29·9/30·10/2는 discovery; holdout 미관측 그대로 |
| 고정 B0↔C0의 적용 후 비교 | 교체 후보의 경계확정 군집≥10, incumbent binary 존재, raw 승률 상승·지원조정 점수+5pp를 **최신 적격 날짜와 적용 후 누적 창 모두**에서 충족 | 규칙은10/6 전 고정;10/6부터 실제로 새로 관측한 날짜만 적용 후 창에 포함 |
| 이후 새로 탐색/수정한 C1 등 | 기존 자동 acceptance의 학습30·독립 검증10, raw/+5pp 및 원천/날짜 계약 | 학습에서 선택한 뒤 미사용 미래 검증; 고정 두 정책 경로로 우회하지 않음 |

현재 `_hurdles`의 floor는 **후보 군집 수**에 적용되며 부모는 binary 존재를 요구한다. 양쪽 모두10개라는 설명으로 현행 코드를 오인하지 않는다. 고정 두 정책 경로는 이 역할 기준을 유지하고, B0와 C0가 challenger가 될 때 같은 규칙을 적용한다.

고정 두 정책의 후속 비교는 임계값을 재탐색하지 않으므로 과거 학습에서 B0가 졌다는 이유로 영구 배제하지 않는다. 이는 자동 학습30/검증10을 모든 정책에서 없애는 변경이 아니다. 별도 `main_machine_designated_fixed_pair_v1` 계약으로 등록하고 기존 승계·과거 연구·장후 비교 수치를 분리한다. 같은 날짜를 누적 창에 한 번만 넣으며 최신 날짜는 누적에도 포함됨을 밝힌다. 두 창을 서로 독립 표본이라고 주장하지 않는다.

### 5.3 처분과 반복 실행

- C0 우세/동률이고 C0가 incumbent이면 유지. B0가 incumbent일 때 C0가 위 비교조건을 만족하면 C0로 교체한다.
- B0가 동일 조건으로 C0보다 우세하면 B0 재선택. 이는 성과에 따른 정책 교체이며 비상 안전 rollback과 구분한다.
- 미관측·비교 불가·지원 부족·개선 미달은 **현재 유효 I_t 승계**다. 지정 C0를 자동으로 과거 B0로 복귀시키지 않는다. source 오류는 진단을 남기고 기존 runtime source guard를 따른다.
- 성공100%/80% 보존·선택50% coverage·모든 미확정 해소는 탈락 조건으로 넣지 않는다.
- receipt는 pair ID·정책 두 hash·source generation·최신 날짜·누적 날짜·평가 manifest·처분·발행 parent를 결속한다. 동일 입력 재실행은 같은 결과를 반환하며 중복 날짜 소비/교체가 없다. 사후 source 수정은 새 평가 revision으로 공개하고 독립 증거 수를 늘리지 않는다.
- 새 C1이 정상 자동 선정되면 B0↔C0 전용 교체 권한은 종료한다. 과거 지정이나 두 정책 비교가 C1을 덮어쓰지 않는다. 이후 비교 기준 갱신은 명시적인 다음 비교 계약을 따른다.

이번 구현의 challenger 집합은 B0/C0로 고정한다. C1 경로는 기존 자동 acceptance를 보존하는 호환 경계이며 미등록 신규 후보를 생성하는 작업이 아니다. 나중에 C1을 등록할 때 동일 날짜의 단일 selector·후보 우선순위·전용 비교 종료를 함께 정의해야 하며, 두 publisher가 각자 승자를 발행하게 두지 않는다.

## 6. 삼성 후속 연구와의 호환

비삼성 recipe 추가는 공통 machine hash를 바꾸므로 현 삼성 adapter는 `samsung_forward_parent_changed`를 낼 수 있다. 원 frozen 파일을 수정하거나 parent hash 비교를 없애지 않는다.

- 허용 diff가 검증된 `entry_admission_recipe` 한 항목이고 `exclude_005930`·KRX 정규장 조건을 만족하며, 나머지 policy/hard guard가 동일한 경우에만 삼성 component 동등성 증명을 만든다.
- 원 frozen·원 parent·새 실제 parent·원 kernel·새 kernel·허용 diff와 행동 대사 결과를 별도 migration receipt에 결속한다. 과거 커널이나 연구 결과가 새 커널로 계산됐다고 재기록하지 않는다.
- 원519관측에서 삼성 행동/guard 차이0을 검증하고 exact scope 밖 경로도 확인한다. hash 외 component 변화나 행동 변화가 있으면 `replan_required`다.
- 미래 capture는 반드시 **그 관측 당시 실제 bundle**로 source를 검증한다. 장후 current와 다르다는 이유로 정상 오전 관측 전체를 버리지 않는다. 존재하는 generation/activation 시각 증거 없이 다른 bundle을 허용하지 않는다.
- 최신 absorption adapter와 기존 fixed-watch·premarket frozen 소비자를 함께 대사한다. 호환은 연구 입력의 동일성만 보장하며 삼성 후보 등록/운영 적용 권한을 만들지 않는다.

## 7. 파일별 구현과 위치

| 단계 | 파일/책임 | 검토·완료 기준 |
|---|---|---|
| C0 intake | 기존 계획/closure·정책·frozen·release·10/6 준비 | 이전 bytes·source hash·실제 소비 상태·scope 고정 |
| C1 계약 | 제안 `src/engine/scalping/entry_designated_policy.py` | 지정 schema·순수 validator·scope/component 비교. Main 정책 역할 package에 두며 engine root 새 모듈 금지 |
| C2 발행·loader | `mechanistic_entry_runtime_policy.py`의 지정 stage/activation/validate/source 검증 |1회 요청·target day·parent CAS·journal·archive·readback·재실행. 현재 자동 stage의 무조건 force 옵션 금지 |
| C3 비교 생성 | `entry_admission_analysis.py`, `entry_admission_acceptance.py`, `ai_action_outcome_calibration.py` | B0/C0/I_t/P_t 분리, 고정 pair branch, self-comparison 차단, 적용 후 날짜 registry·동일 입력 source |
| C4 전달·소비 | `postclose_summary_handoff.py`, `runtime_approval_summary.py`, `verify_threshold_cycle_postclose_chain.py`, `automation/runtime_policy_bootstrap.py`, `automation/next_preopen_readiness.py` | 지정/자동/승계 reason·동일 generation 확인; launcher의 기존 dated activation 호출 계약도 점검 |
| C5 삼성 호환 | `samsung_absorption_acceptance_research.py`, `samsung_fixed_watch_evaluation_research.py`, 관련 premarket 소비자 | 허용된 비삼성 차이만 동등성 인정, 원 capture 행동·hash 검증 유지 |
| C6 리뷰·격리검증 | 기존 대응 `src/tests/test_*.py`, 신규 계약 test는 `src/tests/test_entry_designated_policy.py` | 아래 회귀·실제 원 데이터 parity·producer→consumer 검증 |
| C7 후속 실행 | 기존 release/정책/장전 owner | 구현 승인 범위의 commit→불변 release→지정 stage→summary/strict/controller/prepared. 실제 기동은 당일 기존 owner |

자동화 계약을 실제 수정하는 변경에는 장후 운영 지침과 checklist를 함께 갱신한다. Plan Rebase의 D8 잔존 문구는 현재 사용자 기준과 충돌하는 역사 문구로 표시하며 새 성공 보존 veto로 사용하지 않는다. 기준 문서 자체 편집은 해당 유지보수 범위를 따른다.

## 8. 필수 회귀와 재리뷰

1. 실제 frozen 보고서는 자동 selected=false를 유지하면서 지정 stage만 성공한다. 미승인/다른 recipe/학습 부적격/추가 source 실패는 거절한다.
2. 날짜 오기·미래 날짜 연장·이미 시작한 target·중복 request·상반된 두 request·CAS 충돌을 거절한다. 동일 성공 요청 재실행은 무변경이다.
3. 기존 dated generation과 그 증빙을 복원할 수 있다. journal 각 쓰기 지점 실패 뒤 회복 또는 명확한 거절을 확인한다. 부분 발행으로 activation되지 않는다.
4. 비삼성 외 component·보조 AI·source/quote/liquidity/account/order/quantity/cooldown/손절 guard가 보존된다. 즉시 매수/수량 증가 경로를 추가하지 않는다.
5. 적용 뒤 actual C0·benchmark B0를 구분하고 두 arm이 실제로 다른 행동을 재생한다. P_t의 행동 검증은 여전히 실패를 탐지한다.
6. C0 유지, B0 재선택, 표본 부족 승계, source 오류, same-day 중복, 날짜 누출, 양성 일부 제외·coverage50% 미만, 신규 C1 전용 gate 및 fixed-pair 종료를 모두 검증한다.
7.10/2를 새 forward로 쓰지 않고10/6 관측부터 적용 후 창에 포함한다. 테스트 fixture 날짜 변경을 실제 독립 검증으로 쓰지 않는다.
8. 삼성 허용 diff와 실제 guard 변경·알 수 없는 diff·서로 다른 source bundle·kernel migration 불일치를 각각 구분한다. 호환 후 frozen 평가 결과가 바뀌지 않는다.
9. source10/2 summary 재실행이 지정 정책을 취소하지 않는다. 잘못된 supersession chain·낡은 prepared·report hash 위조는 마지막 consumer에서도 거절한다.

대상 pytest는 위 영향 파일의 기존 suites와 새 계약 suite로 한정한다. Python compile·`git diff --check`, 문서 링크/소유자와 print-only parser를 수행한다. wrapper를 실제 수정하면 그때 `bash -n`·관련 contract test를 추가한다. 보고서 전체 재생·거래 suite·API 호출을 문서 계획 검증에 실행하지 않는다.

## 9. 소유·실행 순서·종료

`NonSamsungDesignatedPolicyImplementation1005`가 C0~C7 준비를 소유한다. 적용 후 비교는 기존 `NonSamsungMachineForwardComparison1006`, 실제 Main 당일 소비는 `DirectFamilyPreopenPolicyHandoff`를 재사용한다. 기존 완료 항목을 실행 중으로 되돌리거나 새 기동 owner를 중복 생성하지 않는다.

구현 완료 기준은 지정 정상경로/거부경로와 양방향 장후 비교의 producer→publisher→loader→summary 검증, 삼성 동등성, 반복 리뷰 후 미해결 범위 내 결함0이다. 적용 완료는 별도의 지정 generation·prepared·당일 PID 증거로 판단한다. 신규 정책의 우월성은 별도 이후 관측 결과다. 이번 계획 작성에서는 코드·정책·기동·원천·예약 작업을 변경하지 않는다.

## 실행 기록

사용자 `계획 실행`으로 구현·리뷰·실제 원천 재생을 수행했다. 최신 상태와 역사 원천 결손, 발행/배포/준비 증빙은 [실행 리뷰](../audits/designated-machine-policy-and-samsung-differential-execution-review-2026-10-05.md)를 따른다. 계획 본문의 미실행 표현은 작성 시점 상태다.
