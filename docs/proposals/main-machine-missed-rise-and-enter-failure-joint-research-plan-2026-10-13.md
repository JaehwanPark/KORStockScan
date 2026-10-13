# Main 놓친 상승·ENTER_NOW 실패 감소 병행 연구계획 — 2026-10-13

상태: **계획 실행·격리 연구·리뷰·검증 완료.** [결과 리뷰](../audits/main-machine-missed-rise-and-enter-failure-joint-research-review-2026-10-13.md)에 두 연구 축과 실제 결합, 미확정·source gap·성공 손실을 연결한다. 실행 정책 등록/교체와 구분한다.

## 1. 목적과 비교 기준

사용자 요청에 따라 누적 원천에서 **추가 상승 기회 탐지와 기존 ENTER_NOW 실패 감소를 함께 연구**한다. 새로운 유형·특징·조건·확인 방식은 이 수동연구가 정의하며 장후 자동 새 패턴 생성으로 이전하지 않는다. [앞선 연구](main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md)의 추가 OR 후보만 평가하던 범위를 확장한다.

비교 기준은 연구 시작 때 선택된 `main-residual-reviewed-20261013-v6` 코드와 현재 bundle `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`의 실제 기계 branch payload다. 운영 변경이 진행돼도 이 고정 비교 기준을 중간 교체하지 않는다. 이전 연구의 incumbent bit를 최신 정책으로 대체하지 않는다. 현재 PID 적용 여부·실거래 수익은 이 연구의 주장이 아니다.

## 2. 원천·모집단·성과 정의

- `source_date>=2026-09-29`인 기존 frozen normalized 원천만 사용한다. 누적 manifest의 9/28 이전 파티션을 학습·순위·선택에 합산하지 않는다.
- PRE는 NXT `_NX`, REGULAR·AFTER는 SOR `_AL`이다. 삼성, 다른 상시4종목, 일반종목 및 가격대·시장·route를 구분한다. 실제 소유 원천에 없는 시장을 다른 시장으로 대체하지 않는다.
- 현재 10/12 source manifest에 보유된 적격 시장 파티션은 7개 날짜의21개다. preflight/유효성·exact item·epoch/sequence·연속 수신 구간을 보존한다. source 자체가 invalid이면 현재값이나 완료 분봉으로 진입 시점의 원천을 소급 복원하지 않는다.
- 등록 정책을 순수 native State에서 동일 prefix로 재생한다. 각 실제 확인점의 ask부터1,800초, 비용률0.0023·순 목표+0.4%·손절−3%의 기존 label을 쓴다. 10분 이후 동일 item 완료 가격/분봉은 결과 라벨 보조로 사용하며 판정 특징에는 미래를 넣지 않는다.
- WIN, FAIL_STOP, FAIL_TIMEOUT, UNRESOLVED를 구분한다. 승률은 `WIN/(WIN+FAIL_STOP+FAIL_TIMEOUT)`이다. UNRESOLVED·특징 UNKNOWN·실주문 손익은 별도다. 실제 미진입 신호에도 충분한 정확 후행 가격이 있으면 반사실 라벨을 붙이되 실제 손실이라고 부르지 않는다.
- 동일 `(date,item,epoch,sequence)`를 한 기회로 집계하고 branch membership을 유지한다. 정책별, 정책 단독 실패, 다른 정책과 중복된 실패, 전체 OR 실패를 따로 비교한다. 같은 목표 시각에 몰린 반복 확인점은 독립 거래 수가 아니다.

## 3. 명시적 두 연구 축

### A — 놓친 상승 추가 탐지

기존 실제 root·누적 원천을 활용해 고점 돌파, 작은 momentum, FIRST 가격 유지·저점 재시험의 고정9개 정의를 검토한다. 각 정의의 실제 필터·경계는 실행 전 manifest에 동결한다. 기존 정책이 없는 확인점의 추가 W/STOP/TIMEOUT/U와 baseline OR 후보를 계산한다. 이전 PRE/AFTER 후보를 REGULAR에 복사 적용하지 않고 새로 계산한다.

### F — 기존 ENTER_NOW 실패 감소

현재 확인 시점에서만 계산한 60초 수익률·종목 흐름·VWAP·signed BUY10·거래량 비율·spread·낙폭·고저 구조의 고정16개 보완 가설을 비교한다. 실패·성공 원천 분포와 유형별 확정 승률을 함께 산출한다.

1. scope 전체의 조건 보완과 개별 branch의 조건 보완을 별도로 계산한다. branch 한 개를 보완했는데 다른 branch가 같은 확인점을 허용하면 전체 OR에서 제거된 실패가 아니다.
2. 새로운 추가 특징이 UNKNOWN인 baseline 신호는 현재 판정을 유지하는 보수적 반사실 비교를 사용한다. 검증된 조건 불일치만 제거하며, 결손 행을 대량 제외해 승률이 오른 것처럼 만들지 않는다. UNKNOWN 수·유지된 실패/성공과 알려진 범위의 비교도 기록한다.
3. 제외한 기존 WIN/STOP/TIMEOUT/U, 남은 기회 수와 누적 승률을 모두 보고한다. 기존 성공100% 또는80% 보존을 후보 탈락 조건으로 두지 않는다. 성공 손실은 비용으로 공개하고 비교 목적은 기존보다 높은 확정 승률이다.
4. 이후 구현에는 변경된 definition/root·scope·필수 feature/UNKNOWN 처리·code hash가 명시돼야 한다. 연구의 일반 조건을 전 종목 runtime 공통 hard veto로 곧바로 적용하지 않는다.

F를 신규 정책으로만 등록해 원 정책과 OR로 유지하면 제거하려던 실패가 원 정책에서 그대로 허용된다. F의 실제 소비는 해당 scope/branch의 검토된 후속 정의로 **교체**하는 구조여야 한다. 원 정의·역사 membership은 유지하고 frozen ID를 덮어쓰지 않는다. scope 전체 F는 해당 scope의 모든 원 branch에 같은 보완을 적용한 반사실이며, 실제 교체 목록과 다른 scope를 명시해야 한다. 이 연구 자체에 원 정책 제거·runtime 공통 veto·배포 권한은 없다.

### J — 실패 감소와 추가 탐지 결합

`보완한 기존 정책 OR 추가 후보`를 실제 확인점 합집합으로 계산한다. 기존 단독, 보완 단독, 추가 후보 단독, 기존+추가, 보완+추가를 비교한다. A/F 개별 숫자를 더해 결합 승률·추가 기회 수를 만들지 않는다. 추가 후보가 다시 허용하는 실패도 결합 분모에 포함한다.

고정9개 A와 고정16개 F의 scope/branch 보완 조합을 비교한다. A가 보완 전 baseline 단독 승률을 높이지 못해도 F와 결합한 승률이 개선될 수 있으므로 A의 단독 우위를 J의 선행 조건으로 두지 않는다. learning에서 제거된 확정 실패와 추가된 확정 성공을 모두 확인한 조합을 두 효과의 연구 제안으로 분류한다. 이는 지정 채택의 추가 경제성/표본/일수 gate가 아니며 개별 A/F의 제안도 별도 보존한다.

승률 최고 조합은 기존 성공을 거의 전부 잃을 수 있다. 같은 고정 조합의 learning 결과에서 승률과 확정 성공 수의 Pareto 후보도 공개하고, **기존보다 높은 승률을 유지하는 조합 중 성공 기회가 가장 많은 선택**을 별도로 고정해 뒤 날짜/누적으로 평가한다. 임의 승률 하한이나 성공 보존율 gate를 추가하지 않고 최고 승률의 극단적 축소와 기회 확대 선택을 구분한다.

## 4. 탐색·선정·불확실성

1. 고정25개 정의만 사용한다. 대규모 임의 grid·outcome을 본 뒤 연속 threshold 최적화는 실행하지 않는다. 실제 원천 census와 가설 정의·기준 bundle/code/source hash를 먼저 freeze한다.
2. 9/29~10/8의 실제 보유6일에서 후보를 정하고10/12를 별도 날짜 비교로 공개한다. 현재 기준 정책 자체가10/12 원천을 소비했으므로 이는 보지 않은 독립 미래 holdout이 아니다. source invalid로 그날 표본이 없으면 source_gap이며 후보 실패/0수익이 아니다.
3. learning에서 정한 A/F 후보의 누적·일별 결과를 공개한다. 누적 승률 개선을 우선하고 동률의 추가 성공을 구분한다. 새로운 일수·표본·EV·특정 새 날짜 WIN 조건이나 성공 보존율 gate를 추가하지 않는다. 기준 확정 분모가0이면 우위 비교는 null이고 후보 자체 결과만 공개한다.
4. 유형·가설 수·날짜/종목/목표 시각 집중, 잃은 성공, 제거 실패, 미확정·UNKNOWN의 양을 기록한다. 사후 탐색 결과를 미래 승률 보장으로 표현하지 않는다.

## 5. 구현 위치·상한·리뷰

- 임시 도구·frozen 입력·결과는 `tmp/main-machine-joint-research-20261013`의 offline 역할이다. 기존 계산기를 읽고 순수 State를 사용하며 `src/engine` root 신규 모듈·운영 registry/DB 쓰기·Provider/API 호출·주문·기동은 없다.
- 불변 릴리스의 코드로 실행한다. 단일 프로세스/계산 thread, nice19, 주소공간2GiB, 파티션별 CPU480초·wall600초 상한이다. 완료 파티션을 checkpoint해 재실행 때 같은 입력을 중복 집계하지 않는다. 초과는 partial로 기록하고 분모를 줄여 성공으로 보고하지 않는다.
- 입력 selector/current pointer는 시작 시 로컬 receipt로 동결한다. 타 세션의 승인 배포로 현재 pointer가 바뀌는 것은 원 연구 세대의 변경이 아니다. 이 연구의 immutable bundle/source/code 자체가 바뀌면 혼합 결과를 거절한다.
- 구현→self review→보완→재리뷰→표적 pytest·compile, source/label/경계·UNKNOWN·same-tick dedup·branch 중복 보호·성공 손실 허용·정확 결합 비교를 검증한다. 문서 link/owner/authority·print-only parser·공백 검사로 닫는다.
- 보유 원천의 source gap은 연구의 결과와 미평가 범위다. 원천 수리·실시간 소비·신규 등록의 자연 수용은 기존 당일 `NonfixedDispatchReadinessReview1012` owner와 구분한다. 현재 sealed checklist와 타 세션 작업본은 변경하지 않는다.

## 6. 산출물과 다음 연결

완료 산출물은 원천 census, 성공/실패의 유형별 분포, 고정 가설별 baseline·보완·추가·결합 비교, 등록/교체를 검토할 후보 정의와 남은 결손이다. 성과가 나쁘거나 검증 불가능한 가설도 결과로 보존한다. 새로운 패턴 생성은 수동연구, 고정 등록 후보/적용 정책의 누적 비교는 기존 장후 소비자가 소유한다.

사용자 실행용 표준 동기화 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
