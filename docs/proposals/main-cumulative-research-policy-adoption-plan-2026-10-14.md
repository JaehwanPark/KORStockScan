# Main 누적 상승 포착·실패 감소 연구의 정책 반영 계획 — 2026-10-14 / 10-15 보완

## 1. 목적과 적용 범위

누적 원천으로 수동 연구한 후보를 **등록 → 실제 탐지 코드와 재생 일치 검증 → 기존형·추가형·정제형·결합형 비교 → 정책 발행 → 적용 확인**으로 연결한다. 10/14의 고정 25가설 재검증뿐 아니라 사용자 후속 지시에 따른 [10/15 신규 두 축 연구](main-machine-cumulative-dual-track-research-plan-2026-10-15.md)를 함께 소비한다. 새로운 가설·조건·경계값 탐색은 수동 연구가 담당한다. 장후에는 등록한 불변 후보와 실제 적용 정책을 평가한다.

10/15 사용자 지시에 따라 별도 작업본에서 구현·코드 리뷰·보완·격리 검증을 진행한다. 운영 등록·배포·재기동은 대기한다. 현재 구현과 인계 상태는 §10 및 [구현 검토](../audits/main-cumulative-policy-adoption-implementation-review-2026-10-15.md)가 소유한다. 본 계획의 Main 기계 후보와 [entry-split 관측 계약 수리](entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md)는 독립 작업이다.

10/14 인계 기준은 [당시 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry`, `DirectFamilyPreopenPolicyHandoff`였다. [10/15 체크리스트](../checklists/2026-10-15-stage2-todo-checklist.md)에는 전자의 OPEN이 없으므로 과거 완료/인계 항목을 현재 executable owner로 재사용하지 않는다. 후속 등록 구현 시 현재 정책 owner와 `DirectFamilyPreopenPolicyHandoff`의 적용일·수용 범위를 연결한다. 이번 수동 연구로 중복 OPEN이나 자동 가설 생성 작업을 만들지 않는다. 구현·코드 리뷰·발행·자연 판정·실제 비용 성과는 각각 완료 상태를 갖는다.

## 2. 확인한 기준과 증거

- [누적 연구 결과](/home/ubuntu/KORStockScan/docs/audits/main-machine-cumulative-missed-rise-and-enter-failure-research-review-2026-10-14.md): 고정 가설 25개, 22개 scope, A/F 조합 8,432개. F 개선 12개 scope, A 개선 또는 동률 추가 성공 5개 scope, 두 효과를 함께 보인 J 10개 scope.
- **정정본** [cumulative-result.json](/home/ubuntu/KORStockScan/tmp/main-machine-joint-research-20261014/corrected/cumulative-result.json)의 SHA256은 `afa281aa051636505a1e4ed34eb2ac64fae53c5bf55706b3a644635c8a95436e`이다. 같은 디렉터리의 manifest, label 검증, native root parity, 원천 보정 receipt를 함께 소비한다. 상위 디렉터리의 정정 전 result는 등록 근거로 사용하지 않는다.
- 10/14 연구 기준 bundle은 `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`, family는 `c366914f1a2a76d85bceacd406e6c377f1fb32b2b50d757fb195484ab783ff8c`이며 **당시** current pointer와 같았다. 10/15 연구 baseline은 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`로 재고정했다.
- 10/14 연구 코드는 `ff32b99b3…`, 당시 후속 선택은 `f8dc4431d…`였다. 10/15 연구는 `policy-custody-incident-integrated-20261015-bb4808c77`을 사용한다. 실제 구현 때 [선택 릴리스](/home/ubuntu/KORStockScan/data/runtime/runtime_release_selection.json)와 [현재 정책](/home/ubuntu/KORStockScan/data/runtime/mechanistic_entry_policy/current.json)을 다시 결속한다. 이 연구는 현재 PID를 독립 검증한 결과가 아니다.
- 24개 partition의 raw 5,261,652행 중 유효 3,831,217행, 제외 1,430,435행이다. 10/13은 애프터 19:36:41~20:00:00의 18,688행만 적격이었다. 누적 비교의 소스 범위가 10/13 전체 장을 대표한다고 표현하지 않는다.

원천·결과를 운영 등록에 사용할 때 필요한 작은 근거/정의/manifest/검증 receipt를 기존 등록 archive로 이관하고 SHA와 상대경로 해석을 검증한다. 임시 디렉터리의 수명에 runtime validation을 의존시키지 않는다. 대용량 raw의 중복 복제는 피하고 기존 보존 owner와 원천 generation ref를 연결한다.

## 3. 정책 선택 기준

### 3.1 승률의 정확한 의미

확인점의 실제 ask, 30분, 비용률 0.0023, 비용 후 목표 +0.4%와 soft −3%의 선도달 계약을 그대로 쓴다.

- W: 목표 선도달.
- F: 손절 선도달 또는 충분한 30분 관측 후 목표·손절 모두 미도달. `FAIL_TIMEOUT`을 실제 손실이라고 부르지 않는다.
- U: 경로 검열·미확정. source-invalid는 별도의 제외 사유다. U/결손을 실패나 0원으로 채우지 않는다.
- 같은 item의 완료 분봉은 기존 계약에 따라 10분 이후 경로를 보조한다. 미래 봉·다른 route·현재 값으로 과거 결손을 대체하지 않는다.

선정의 1순위는 동일 유효 원천 범위에서 각 정책이 선택한 확인점의 **누적 `W/(W+STOP+TIMEOUT)`**이다. 분수 비교로 반올림 역전을 방지한다. 동률이면 확정 W 수, 동일 membership이면 current 유지, 마지막으로 고정 variant ID 순서를 사용한다. 대상의 교집합이나 보조 PASS만을 기계 분모로 삼지 않는다.

성공 100%·80% 보존율, 최소 표본·최소 일수, 새 날짜 holdout, 추가 EV/payoff 개선을 Main 기계 후보의 새 탈락 조건으로 넣지 않는다. 원천·신원·정의·계산 일치와 실제 runtime safety는 검증한다. 날짜별 편중, U, 반복 확인점, distinct target clock, 실제 ENTER 기록과 CF의 차이는 공개한다. 분모 0은 비율 null이며 승률 비교로 승자를 만들지 않는다.

### 3.2 연구에서 뽑은 J와 실제 selector를 구분

[연구 selector](/home/ubuntu/KORStockScan/tmp/main-machine-joint-research-20261014/corrected/select_joint.py)는 '새 W 존재 + 기존 F 제거'를 두 축의 효과를 보여 주는 J 표의 포함 조건으로 사용했다. **운영 selector의 필수 조건으로 옮기지 않는다.** F만 유효하거나 A만 유효한 정책도 선택 대상이다.

`highest_fraction_joint`는 J 집합 안의 최고 비율이다. A/F/current까지 합친 전체 승자를 뜻하지 않는다. 또한 `opportunity_joint`는 성공 수를 우선한 연구 대안이다. 운영에서 이를 자동으로 `JOINT_BALANCED` 고정 선택하면 사용자 승률 우선 기준과 충돌한다.

구현에서는 수동 연구가 동결한 버전별 catalog·대상 scope·전체 대안 목록을 재사용한다. 10/14는 25가설·22개 scope·A/F 조합 8,432개였고, 10/15 연구는 신규 13가설을 더한 별도 불변 버전이다. 장후 자동 작업이 이를 임의 확장하지 않는다. current/A-only/F-only/J 중 계약이 입증된 결과를 같은 분모 규칙으로 비교하고 최종 winner를 발행한다. 표의 연구 대표만 읽고 나머지 고정 대안을 누락하지 않는다. 등록 batch에 허용 대안의 전체 membership/hash를 먼저 동결하며, 연구 실행을 운영 등록 승인으로 전용하지 않는다.

## 4. 현재 결과로 예상하는 반영안

아래는 **10/14 보고서의 당시 baseline에 대한 대표 제안**이다. 10/15 재고정 결과는 별도 추가 연구 검토를 우선 소비하고 이 표를 현재 정책 수치로 전용하지 않는다. 수치는 정책을 과거 원천에 재생한 확인점 CF이며 실제 발행 ENTER_NOW·독립 거래·체결 수가 아니다. 전체 고정 대안의 native parity와 최종 selection receipt를 대신하지 않는다. 가격대의 중가는 `20000_TO_100000`, 고가는 `GE_100000`, 저가는 `LT_20000`의 기존 코드 경계를 사용한다. PRE는 NXT `_NX`, REGULAR/AFTER는 SOR `_AL`이다.

| scope | 대표 우선 대안 | 현재 W/확정 → 후보 W/확정 | U 전→후 | 변경 의미 |
|---|---|---|---|---|
| 두산 AFTER 중가 | F16 / extended 원 branch | 40/54 → 40/48 (83.33%) | 109→90 | 기존 실패 6개 제외 |
| 주성 AFTER 고가 | F11 / 현재 scope 전체 | 264/631 → 62/105 (59.05%) | 279→17 | 기존 W 202·F 324개 제외 |
| 주성 REGULAR 고가 | A07 + F15 / 현재 scope 전체 | 914/1292 → 24/24 (100%) | 2033→7 | 기존 W 914·F 378개 제외, 새 W 24개 |
| 알테오젠 PRE 고가 | A03 + F15 / legacy 원 branch | 404/483 → 78/78 (100%) | 1089→705 | 기존 W 334·F 79개 제외, 새 W 8개 |
| 알테오젠 REGULAR 고가 | A07 + F11 / legacy 원 branch | 20/81 → 22/22 (100%) | 63→29 | 기존 F 61개 제외, 새 W 2개 |
| HPSP AFTER 중가 | F15 / legacy 원 branch | 10/20 → 10/10 (100%) | 5→5 | 기존 F 10개 제외 |
| HPSP REGULAR 중가 | F05 / type 원 branch | 438/453 → 392/392 (100%) | 680→656 | 기존 W 46·F 15개 제외 |
| 일반 비고정 AFTER 중가 | F09 / legacy 원 branch | 21/30 → 3/3 (100%) | 6→0 | 기존 W 18·F 9개 제외 |
| 일반 비고정 AFTER 고가 | A05 추가 | 2/2 → 3/3 (100%) | 12→12 | 동률에서 새 W 1개 추가 |
| 일반 비고정 AFTER 저가 | F16 / legacy 원 branch | 36/111 → 17/44 (38.64%) | 86→24 | 기존 W 19·F 48개 제외 |
| 일반 비고정 PRE 중가 | A09 + F06 / legacy 원 branch | 29/30 → 28/28 (100%) | 2→2 | 기존 W 2·F 1개 제외, 새 W 1개 |
| 일반 비고정 PRE 저가 | F15 / 현재 scope 전체 | 173/233 → 27/32 (84.38%) | 39→4 | 기존 W 146·F 55개 제외 |
| 일반 비고정 REGULAR 중가 | F16 / path 원 branch | 30/35 → 7/7 (100%) | 23→4 | 기존 W 23·F 5개 제외 |

기존 성공을 크게 줄이는 후보도 탈락시키지 않지만, **24/24와 914/1292의 기회 규모가 같다고 설명하지 않는다.** 승률 우선 규칙을 적용한 결과이며 실현 수익 개선 증명이 아니다. 표본 3/3·7/7, 특정 날짜 편중과 U도 숨기지 않는다.

HPSP AFTER의 A09+F15는 13/19(68.42%)로 current 50%보다 높지만 F15-only 100%보다 낮다. 이를 초기 운영에 강제 결합하지 않는다. A09와 결합형은 고정 비교 후보로 남겨 이후 누적 비교에서 선택할 수 있게 한다. 두산 AFTER의 확정 성과는 10/8에 집중되며, 알테오젠 REGULAR의 기존 W는 10/7·새 W는 10/8에 있다.

삼성 PRE 13/13, REGULAR 88/88, AFTER 0/48에는 이번 고정 가설의 개선 후보가 확인되지 않았다. 삼성과 나머지 개선 미확인 scope는 기존 정책을 유지하는 제안이다. 특히 삼성 AFTER의 U 1,776개를 실패로 합치거나 '모든 패턴에 기회 없음'으로 확대하지 않는다. 등록 후보가 없다는 사실과 이후 수동 연구의 필요성은 별개다.

## 5. 정의·탐지 계약 보완

### 5.1 위치와 현재 구현의 제약

정책/특징/탐지의 소유 패키지는 기존 `src/engine/scalping`이다. engine 루트에 모듈을 추가하지 않는다. 기존 [joint catalog](../../src/engine/scalping/reversal_joint_catalog.py), [registration](../../src/engine/scalping/reversal_joint_registration.py), [extended State](../../src/engine/scalping/reversal_extended_state.py), [typed auxiliary proof](../../src/engine/scalping/reversal_extended_auxiliary.py), [v6 policy](../../src/engine/scalping/continuous_reversal_policy_v6.py)를 versioned successor로 보완한다.

현재 joint v1은 10/13의 네 정의·두 scope·고정 parent/authority에 묶여 있다. refinement도 단일 `feature/operator/bound`, 원 정의도 BASE 한 단계 합성이다. 이번 F11의 구조 비교, F15/F16의 AND, extended/type/path와 이미 합성된 분기를 처리하지 못한다. 기존 v1 상수를 새 값으로 덮어 과거 정의·승인 검증을 깨뜨리지 않는다.

현재 State는 old signal에 F를 적용한 뒤 새 extended root 후보를 발행한다. 따라서 extended 원 branch가 필요한 F를 단순히 COMPOSED에 추가하면 원 확인 신호를 보지 못할 수 있다. **동일 event의 모든 원 root 확인 생성 → 동결된 의존성 순서의 F 평가 → 운영 membership만 OR 결합** 순서로 보완한다. 원 FSM의 FIRST/hold/confirmation 시각을 바꾸지 않는다.

### 5.2 정의와 특징의 동결

- 새 definition ID는 canonical hash로 고정한다. exact scope, 원 definition ID/hash, root/confirmation 계약, feature version, 라벨, F 조건과 UNKNOWN 의미를 포함한다.
- F05는 60초 VWAP 이상, F06은 10틱 매수 비중 ≥50%, F09는 spread ≤0.1%, F11은 최근 30초 고점·저점이 직전 30초보다 모두 높음, F15는 spread ≤0.1% AND 10틱 매수 비중 ≥60%, F16은 최근/직전 60초 체결량 비율 ≥1 AND 60초 수익률 ≥0.05%다. 모든 경계의 포함/제외·단위·수신 prefix는 정정본 정의와 일치시킨다.
- branch 대상의 정확한 ID는 연구 JSON에서 추출해 batch에 기록한다. 예: 두산 AFTER F16의 원본은 `manual_extended_b3f20a28786bbd4e`, HPSP REGULAR F05는 `manual_type_ae4445459dc942c8`이다. 이름이 유사한 branch로 대체하지 않는다.
- 현재 주성 AFTER의 `manual_joint_1b973523648b1619`는 VWAP 정제형이다. 일반 PRE의 `manual_joint_8008535bc6aa2678`는 **돌파 A08**이며 `manual_joint_9a28e37e454ce928`가 session 정제형이다. 별칭/의존성 의미를 서로 바꾸지 않는다.
- 원형→기존 정제형→새 정제형 의존성이 필요한 scope는 고정된 유한 DAG로 검증한다. 순환·자기 참조·정의 유실을 거부하고 깊이는 이번 batch의 실제 의존성으로 한정한다. 각 단계의 기존 UNKNOWN/confirmation 의미를 유지한다. AND 하나로 평탄화해 동작을 바꾸지 않는다.

### 5.3 F는 원 확인점의 필터, A는 독립 root

| 조건 | 결과 |
|---|---|
| 원 확인 TRUE, 새 F TRUE | successor 신호 발행 |
| 원 확인 TRUE, 새 F FALSE | 그 확인점의 해당 branch 제외 |
| 원 확인 TRUE, 새 F UNKNOWN | 연구와 같이 원 정상 확인을 보존하고 UNKNOWN 기록 |
| 원 확인 FALSE/UNKNOWN | 새 F로 신호 승격하지 않음 |

AND는 한 항이라도 알려진 FALSE면 FALSE, 모두 TRUE면 TRUE, 나머지는 UNKNOWN이다. 불명 값을 0/False로 바꾸지 않는다. F가 FALSE였던 확인점에서 다음 tick의 특징만 바뀌었다고 hold/deadline을 다시 시작하거나 같은 확인점을 재발행하지 않는다.

scope 전체 F는 동결된 current branch 각각의 실제 확인에 적용한다. 새 A까지 전역 veto로 걸면 `F(current) OR A` 연구와 달라진다. branch F는 지정 branch만 교체하며 다른 정상 OR branch가 같은 기회를 허용하면 그 사실을 유지한다. dependencies는 계산용이며 운영 신호·AI 요청 대상으로 되살리지 않는다.

A는 기존 하락반전의 선행 발생에 종속시키지 않는다. 각 root 계약에 맞게 유효 틱에서 독립 탐지한다. BREAKOUT 계열은 선행 60초 비교값이 UNKNOWN인 상태에서 다음 TRUE를 FALSE→TRUE로 오인하지 않는 정정본 계약을 적용한다. 현재 선택되지 않은 후보 전체를 live 매 틱에 추가 평가하지는 않는다. 운영 선정된 branch는 동등하게 독립 평가하고 연구 후보는 장후 동일 원천으로 비교한다.

## 6. 등록·장후 선정·적용 흐름

1. **R0 증거 고정:** selected release, current bundle/registry/원 membership, 정의/코드/source hashes와 cutoff를 고정한다. 정정본·불변 후보 목록·scope 목록을 보존하고 현재 parent 변화를 검사한다.
2. **R1 runtime 동등성:** 새 typed 정의와 root/특징 proof를 구현한다. 동일 입력 replay에서 기회 key/ask/시각/branch membership/UNKNOWN/라벨을 비교한다. native 결과가 연구와 다르면 원인을 수리하고 같은 고정 후보를 재계산한다. 계산 결함을 숨기려고 임계값을 다시 탐색하지 않는다.
3. **R2 등록안:** scope별 full before/after membership, ADD와 REPLACE, 내부 dependency 목록, 후보 variant hash, 근거 archive, 등록 승인·이후 variant 선택 위임을 분리해 기록한다. A-only/F-only/J/current는 한 variant group에서 서로 대안이다. 모두 동시에 OR로 켜서 필터 효과를 없애지 않는다.
4. **R3 선정:** [operating postclose](../../src/engine/scalping/continuous_reversal_operating_postclose.py)와 joint registration의 실제 호출 분기에서 §3의 누적 승률 선택을 수행한다. 기존 batch를 재적용하거나 이미 정제된 분기를 매일 중첩하지 않는다. 동일 membership은 계산을 재사용하되 승인/비교 역할을 보존한다.
5. **R4 발행:** 선택된 machine membership과 호환되는 기존 보조 binding을 [보조 장후 consumer](../../src/engine/scalping/reversal_auxiliary_tuning.py)에 전달해 같은 세대 bundle로 발행한다. 기존 auxiliary prompt/input/response 연구를 변경하거나 기계 비진입을 PASS로 승격하지 않는다. 호환 보조 carry가 가능하면 새 보조 성과 입증을 machine의 추가 선택 gate로 삼지 않는다.
6. **R5 적용 준비:** 코드 리뷰·표적 검증 후 지정된 적용일로 PREOPEN 또는 승인된 intraday handoff를 준비한다. parent CAS, 정의·registry·원천 상대경로·archive·membership·release compatibility를 검사한다. parent가 바뀌면 새 current를 기준으로 영향 scope를 재비교하고 원 archive를 덮어쓰지 않는다. 검증되지 않은 delta를 강제 적용하지 않는다.
7. **R6 자연 확인:** 적용 승인 범위에서 배포/기동 후 실제 policy receipt와 branch hit를 확인한다. 동일 canonical confirmation의 여러 branch hit는 AI 요청·주문 intent 한 개로 dedup한다. ENTER_NOW→보조→Main 소비→제출/체결→비용 결과는 각각 기록한다. 자연 신호가 없으면 미관측이며 주문을 만들어 검증하지 않는다.

초기 지정 채택이 명시되면 기술 계약 검증 후 그 지정안으로 시작할 수 있다. 새로운 독립 날짜 대기나 경제성 gate를 추가하지 않는다. 이후 장후는 실제 current와 등록된 고정 대안만 비교한다. 분석 불완전이면 입증 가능한 row/window를 유지하고, 비교 자체가 입증되지 않는 scope만 실제 current와 호환 보조를 carry한다. 과거 legacy로 자동 복귀하지 않는다.

기존 5초 신호 예산, 원천 신선도·충돌, 주문가격/수량/cap, broker/account/cooldown, Main/manual custody, 영구 진입 제외와 hard/protect/emergency guard는 원 owner가 유지한다. widget/episode 실행 경로는 복구하지 않는다.

## 7. 구현 검증과 중단 기준

| 검증 | 필수 반례/완료 조건 |
|---|---|
| 선정 기준 | F-only 10/10 vs J 13/19에서 F 선택; 동률 W tie; 성공 100%/80% 감소로 자동 탈락 없음; U/분모0·source gap 별도 |
| 원 확인 보존 | legacy/type/path/extended/기존 composed 각각에서 동일 native epoch/sequence/ask/confirmation, F FALSE 뒤 늦은 재발행 0 |
| 삼치 연산 | 알려진 FALSE+UNKNOWN=FALSE, TRUE+UNKNOWN은 선택 F 보존, 원 source UNKNOWN 승격 0 |
| membership | scope F와 branch F의 차이, dependency 유출 0, 새 A의 전역 F 오적용 0, 영향 없는 scope membership/hash 불변 |
| 독립 탐지/중복 | 선행 하락 없는 상승 root, 동일 event multiple hit 한 AI/intent, BREAKOUT UNKNOWN→TRUE 오발행 0 |
| 재기동/재등록 | consumed receipt 재적용 0, parent CAS 충돌, stale source/relative cwd, rollback 후 이전 pending 복구 0 |
| 누적 비교 | 현재 적용 정책을 baseline으로 사용, P1 효과 중복 가산 0, 정정본 source hash와 수치 재현, 실제/CF 분리 |
| 성능 | 동일 source·종목·route·branch 수의 전/후 event 처리 p50/p95/p99, queue·claim 지연, REST/WS·provider 호출량 측정; 새 per-tick 디스크/API 호출 0; 장후에는 동일 고정 대안 수·기간·원천으로 peak RSS/읽기 bytes/wall 비교 |

기존 `test_reversal_extended_policy.py`, `test_reversal_operating_policy.py`, `test_reversal_manual_registration.py`, `test_reversal_auxiliary_contract.py`, `test_continuous_reversal_policy_v3.py`, `test_runtime_policy_bootstrap.py` 중 실제 수정 계약의 시험과 새 반례만 실행한다. Python compile, diff 확인, immutable artifact hash·reader 검증을 추가한다. 시험 개수 자체를 경제성 증거로 쓰지 않는다.

정의/기회/label parity 불일치, 권한 밖 membership 변경, 과거 승인 손상, dedup 깨짐 또는 기존 시간·자원 계약 퇴행은 발행 중단 사유다. 수리는 같은 고정 후보로 재검증한다. 실제 적용 뒤 코드/원천/hard safety 결함 rollback은 당시 승인된 compatible incumbent와 receipt를 사용하며, 단순 하루 패배는 다음 누적 비교로 처리한다. 옛 전체 릴리스를 복원해 retired executor를 되살리지 않는다.

버전별 고정 특징/root 계산과 기회 집합을 source/feature/label/definition hash로 재사용해 대안마다 raw를 다시 읽지 않는다. §8의 10/15 연구는 38가설·19,892개 current/A/F/J 대안이며, §10의 후속 불변 버전은 50가설·35,558개 대안이다. 날짜별 immutable partition을 만들고 U의 관측 만기·기존 source 수정도 dependency로 무효화한다. 비교 완료 전에 cursor/누적 집계 완료를 먼저 저장하지 않는다. 부하를 줄이려고 종목·시장·후보·관측기간을 숨겨서 축소하지 않는다. 새 신호 증가에 따른 보조 요청 증가는 실제 고유 confirmation과 기존 예산으로 계측하고 중복 호출과 구분한다.

## 8. 10/15 추가 연구의 반영 보완

38가설 버전의 근거는 [추가 연구 검토](../audits/main-machine-cumulative-dual-track-research-review-2026-10-15.md), [frozen manifest](/home/ubuntu/KORStockScan/tmp/main-machine-cumulative-research-20261015/frozen-manifest.json), [reviewed 결과](/home/ubuntu/KORStockScan/tmp/main-machine-cumulative-research-20261015/result-reviewed.json), [검증 receipt](/home/ubuntu/KORStockScan/tmp/main-machine-cumulative-research-20261015/validation.json)다. reviewed 결과 SHA256은 `2a0663bcf24378574d101371855266dd2bd6f9810dc80599f2aae68002eef956`이다. 원 10/14 자료와 초기 selector 결과는 보존하고 제안은 `recommendation` 필드를 소비한다. raw `winner`의 0% 동률·U만 증가를 개선으로 등록하지 않는다. 이후 가격 전진 연구가 바꾼 세 범위와 최신 결과 신원은 §10을 우선한다.

원천 검토는 9개 날짜·27개 partition, 적격 입력은 기존 8개 날짜·3,831,217행이다. 추가 10/14 325,775행은 원천 epoch 계약으로 제외됐다. 10/15도 epoch 입증 미비여서 제외했다. 새 가설 13개를 실제 검증했으나 새 독립 날짜 검증을 확보한 것은 아니다. 새 날짜 대기를 정책 채택의 추가 조건으로 만들지는 않는다.

현재 parent `1f069c…` 기준 변경 검토는 15개 scope(A2/F8/J5), 개선 미확인 current 유지 7개다. 이 중 **기존 연구 후보 최고보다 나아진 새 가설은 아래 4곳**이다.

| scope | 추가 구현 대상 | 현재 → 새 제안 | 인계 주의 |
|---|---|---|---|
| 두산 PRE 중가 | 조건부 F21 | 51/72 → 48/48 | 해당 종목 세션 중립에서만 volume≥1 AND buy≥60 AND spread≤0.1%; 밖/UNKNOWN은 원 확인 보존. W3·TIMEOUT21 제외, U3,943 |
| 일반 AFTER 저가 | 원 legacy branch의 F18 | 36/111 → 16/37 | ret60≥0.05 AND vwap60≥0 AND volume≥1. 원 branch `legacy_drop_0_4_rebound_le_0_3_v1` 교체, 다른 OR branch 보존 |
| 일반 PRE 고가 | A10 | 10/10 → 11/11 | FIRST_HOLD1 + 중립 세션·작은 수익률/낙폭·거래량 조건. 새 W1/U1 |
| 일반 PRE 저가 | A14 + scope F10 | 157/204 → 2/2 | 독립적인 고점·저점 상승 구조 FALSE→TRUE 뒤 3초 hold. F10은 current만 정제하고 A14는 독립 OR. 기존 W156 제외·새 W1 |

나머지 11개는 기존 고정 후보의 재비교이며 새 발견으로 세지 않는다. 전체 branch ID·조건·U·제거/추가 W/F·날짜 편중은 reviewed JSON에 동결돼 있다. 15개 제안을 합한 확인점 CF는 67.80%→79.39%이지만 W2,579→905, distinct target clock288→117로 감소한다. 성공 보존율을 gate로 쓰지 않되 이를 제출/순이익 증가라고 주장하지 않는다. 기회 수 우선 대안을 모두 합한 67.72%는 current 67.80%보다 낮으므로 그대로 전체 운영 winner로 채택하지 않는다.

구현 보완은 다음과 같다.

1. A/F 번호는 이번 연구 namespace의 local ID다. runtime definition은 root·hold·prefix feature·삼치 조건·exact scope/parent를 canonical hash로 고정한다. 10/14 목록을 덮어쓰거나 이번 연구를 운영 등록 승인으로 사용하지 않는다.
2. F18의 AND와 F21의 `when/require` 삼치 평가를 versioned successor에 추가한다. 조건부 regime은 개별 종목의 첫 유효 세션 관측 대비 변화이며 KOSPI/KOSDAQ 시장 regime으로 바꾸지 않는다. regime FALSE는 원 신호 보존, UNKNOWN도 원 신호 보존, regime TRUE일 때만 고정 require를 평가한다.
3. A10은 existing FIRST/hold confirmation을 재사용해 연구 key/ask/시각을 대조한다. A14는 기존 반전 FSM에 종속시키지 않는 독립 상승 구조 root가 필요하다. root 이전 UNKNOWN을 FALSE로 간주하지 않고 3초 hold 중 source break·한 번의 가격 하회도 거부한다. 조건은 root가 아닌 confirmation prefix에서 읽는다.
4. 비교 대상은 current와 등록 승인에 결속한 고정 대안 전부다. 성공 100%/80% 보존율·최소 표본/일수·새 holdout·추가 EV를 넣지 않는다. 비율·W 수까지 같고 실제 개선이 없는 대안은 current를 유지하며, 같은 membership의 별칭은 current canonical ID로 묶는다.
5. 기존/새 A를 무차별 OR하지 않는다. 이번 신규 가설 전체에서 과거 연구에 없던 W3,276개가 확인됐지만 STOP28·TIMEOUT21,484개도 있다. 좁은 scope의 검증된 대안을 등록하고 기존 보조 입력/응답·5초 예산·주문 guard·custody·퇴역 경계를 유지한다.
6. 원천·현재 native State·연구 라벨 검증과 신규 runtime root parity는 구분한다. 연구 38개 시험·정규화 가격 경로214개·실제 native ENTER_NOW240개 검사를 등록 구현 완료로 갈음하지 않는다. 운영 archive와 actual reader/CAS 및 자연 소비는 §6~§7의 별도 수용이다.

## 9. 계획 리뷰와 인계

아래 초기 계획 검증 수치는 10/14 당시 문서 검증 이력이다. 10/15에는 §8의 실제 격리 연구·검증을 추가했으며 운영 등록/적용 수용은 별도다.

계획 리뷰에서 수정한 사항: J 최고비율을 전체 winner로 오해하는 문제, F를 OR 추가해 원형이 우회하는 문제, extended 생성 전 F 평가, 기존 합성 의존성 미지원, 정정 전 BREAKOUT 결과 소비, 후보 catalog와 운영 membership 혼동, 이전 batch 고정 authority 재사용을 각각 구현 항목·반례로 명시했다.

10/14 계획 작성의 완료 기준은 두 계획의 실제 경로·링크·owner·권한·문서 parser 검증이었다. 생산 코드 시험, 큰 보고서 재생성, 정책 변경, provider 호출, 배포/재기동은 당시 계획 작성의 검증에 포함하지 않았다. 10/15 구현·격리 검증은 §10, 실제 적용 영수증은 이후 별도 수용으로 관리한다.

계획 검증 결과: 두 문서의 로컬 링크26개·표7개에 오류0, 정정 연구 결과 SHA 일치, 관련 current OPEN owner3개가 각각1개임을 확인했다. print-only parser는25개 작업을 출력했고 `git diff --check`와 새 문서 공백 검사를 통과했다. 이는 계획 검증이며 §7의 구현 시험이 통과했다는 뜻은 아니다.

외부 동기화는 실행하지 않는다. 사용자가 수행할 표준 명령은 두 계획을 묶어 아래 한 개다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 10. 10/15 가격 전진·회복 유형 연구 반영

사용자 후속 연구 지시에 따라 [사전 고정 계획](main-entry-price-progress-and-situation-research-plan-2026-10-15.md)과 [실행 검토](../audits/main-entry-price-progress-and-situation-research-review-2026-10-15.md)를 추가했다. 15:22:36 KST 동결 시점 parent는 §8과 같은 `1f069c…`이며, 선택본 `451b6c1ec…`의 관련 기계 의존 파일 28개가 기존 연구본과 byte 동일했다. 기존 결과를 보존한 별도 버전에서 새 A17~A20/F23~F30을 추가했다. 50가설·35,558개 대안의 [결과](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/result.json) SHA256은 `5210ddad3d5ec1c74b942cbf6b49b65d2ecd9c44d8d963644487e4f4654b8363`이다. 운영 등록/발행 승인을 뜻하지 않는다.

48개 정책 scope와 원천 전체 1,876종목을 census했고, 유효 입력은 8개 날짜·1,809종목·3,831,217행이다. 적격 확인점이 있는 22 scope 중 15개 제안을 유지하되 아래 세 범위만 이전 최선안에서 변경한다. 26개 scope는 `no_eligible_confirmation`, 관측됐으나 개선 없는 7개는 current 유지다. SOR `_AL`을 독립 KRX/NXT 원천으로 복제하지 않는다. 동결 입력의 10/14·10/15 제외를 그대로 보존했다.

| scope | 이전 최선 → 추가 구현 대상 | W/확정·U | 반영 계약 |
|---|---|---|---|
| 두산 AFTER 중가 | 원 extended branch F02 → scope F23 | 40/48·U91 → 24/28·U48 | 연속 유효 10체결 가격 전진 >0. current 전체 정제이므로 이전 branch F 위에 누적하지 않음 |
| HPSP REGULAR 중가 | 원 type branch F05 → A19 + 동일 branch F05 | 392/392·U656 → 394/394·U664 | 고점·저점 상승 전환 후 3초 유지, bid10 상승·buy≥60·ret60≥0. A19는 독립 OR |
| 일반 PRE 중가 | scope A09+F06 → A09 + 원 legacy branch F25 | 28/28·U2 → 30/30·U2 | 최근 10체결 가격 범위 >현재 spread. `legacy_dd5_0_8_vol_up_v1`만 교체, 다른 OR branch 보존 |

두산은 이전 제안의 W16·TIMEOUT5·U44를 제거하고 TIMEOUT1·U1을 추가한다. HPSP는 W2·U8 추가, 일반 PRE는 `455900`의 W2·목표 clock1개 복구다. 전체 제안 합계는 이전 905/1,140 (79.39%)에서 893/1,124 (79.45%), U8,362→8,327이다. 승률 소폭 개선과 성공12개 감소를 함께 보고하며 실현 순손익 증가로 표현하지 않는다.

주성 REGULAR은 기존 `J:A07+F09`의 24/24·U7을 유지한다. 매수 비중 ≥60%·가격 무진전군이 230/306 (75.16%), 그 밖이 684/986 (69.37%)여서 이번 사건을 근거로 무진전·약세를 범용 veto하지 않는다. 상황 6유형은 설명·비교 축이며 기존 기계/보조/보유 약세 유형을 대체하지 않는다. 새 A 전체를 일괄 OR하지 않는다. 기존 모든 A/current에도 없던 신규 확인점의 합계는 2,381/6,639 (35.86%), U4,048이다.

구현 시 추가로 검증할 계약은 다음과 같다.

1. **새 특징:** 기존 수신 prefix를 재사용해 연속 10체결 가격, 동일 구간 bid 이동, 현재 spread 대비 가격 범위를 계산한다. quote 결손은 bid 특징 UNKNOWN이고 입증된 체결 가격까지 0으로 바꾸지 않는다. F UNKNOWN은 원 확인점 보존, A UNKNOWN은 불일치다. 현재 quote로 과거 bid 이동을 추정하지 않는다.
2. **새 root:** A19의 상승 구조 FALSE→TRUE와 3초 hold를 같은 native key/ask/시각으로 대조한다. 후보 catalog에 A17/A18도 등록하는 경우 최초 bid 상승 소비, 30초 만료, 체결가·bid 유지, quote/native 단절·저점 하회 후 재사용 금지를 별도 검증한다. 연구 탐지 통과를 runtime 구현 parity로 갈음하지 않는다.
3. **평가 분리:** 과거 실제 ENTER_NOW 2,438개 중 exact source 적격 240개는 모두 10/12 AFTER다. 이들의 CF label을 보조 PASS·체결·실현 결과로 승격하지 않는다. 원 보조 입력/응답·membership·지표를 보존하며 새 문맥은 별도 연구 version으로 다룬다.
4. **성능:** 기존 native/label 236,597개를 재사용했고 새 label은 10,687개만 계산했다. partition 합계96.87초·집계16.04초·집계 최대RSS 약1.18GiB다. runtime은 기존 공유 상태에서 특징을 계산하고 새 per-tick IO/API를 추가하지 않는다. 장후는 동일 hash별 cache·bounded partition을 사용하며, live p95/p99 개선은 실제 구현 후 같은 입력 benchmark로 확인한다.
5. **수리 인계:** 기계 특징·root·등록/선정 구현은 보유 수리와 독립이다. 실제 preset/trailing/manual 종료·실현 비용과 결합할 때 기존 `HoldingProfitExitSourceContractRepair`의 context/path·cost 시각·preset 실효값·전이/peak/pin·custody/terminal 증거를 문의한다. 수리 commit·선택·PID·과거 원본 재생·자연 영수증을 구분하며 소실된 과거 원천을 복구된 것으로 간주하지 않는다.

13개 표적 시험, 독립 feature 1,236,420개·root series203개·label430개 대조, 기존19,892개 대안 보존, 전체 분수 순위·scope·partition·봉인 검증이 통과했다. [검증 receipt](/home/ubuntu/KORStockScan/tmp/main-entry-price-progress-research-20261015/validation.json)의 errors는0이다. 이는 오프라인 연구 검증이며 §6의 운영 archive/registry/selector/CAS/자연 소비 완료가 아니다. 현재 작업은 중복 checklist OPEN을 생성하거나 보유 수리 코드를 수정하지 않는다.

## 11. 10/15 별도 작업본 구현과 배포 대기 인계

- 작업본: `/home/ubuntu/KORStockScan-worktrees/cumulative-policy-adoption-20261015`, branch `codex/cumulative-policy-adoption-20261015`, 기준 commit `c938ace0610aeec2e68dde9a024e0b82579a1c3b`. 운영 데이터·임시 디렉터리는 공유하지 않는다. 동시 진행 중인 원 작업본 변경은 그대로 보존한다.
- [catalog](../../src/engine/scalping/reversal_cumulative_catalog.py), [고정 정의 resource](../../src/engine/scalping/reversal_cumulative_data.json), [detector](../../src/engine/scalping/reversal_cumulative_runtime.py), [등록 owner](../../src/engine/scalping/reversal_cumulative_registration.py), [장후 owner](../../src/engine/scalping/reversal_cumulative_postclose.py)가 새 계약을 소유한다. 과거 joint v1과 기존 auxiliary prompt/binding은 유지한다.
- 후보는 수동 연구의 16개 A·22개 F다. 구현은 22개 scope의 원 membership 전체에 같은 고정 표현을 적용하므로 26,928개 표현을 제공한다. 연구에서 실제 hit가 없었던 A와 같은 결과의 별칭도 포함된다. 새 가설·특징·임계값을 자동 탐색하는 기능은 추가하지 않는다. 관측된 19,892개 연구 대안과 계산을 대조한다.
- initial 지정안은 reviewed `recommendation`의 변경 15개 scope·승계 7개 scope다. 초기 등록은 기술 계약을 검증하며 새 독립 날짜·성공 보존율·표본/EV gate를 추가하지 않는다. 이후에는 실제 current와 고정 대안을 각자의 동일 원천 누적 승률로 비교한다. 동일 비율·동일 W 수 또는 비교 불완전이면 current를 유지한다.
- 모든 원 root 확인을 만든 뒤 유한 의존성 순서로 F를 평가한다. 내부 원 branch는 운영 OR/AI 요청에 포함하지 않는다. 새로운 상승 지속 root는 FIRST 반전에 종속되지 않는다. 비선정 후보는 장후에만 비교한다.
- 전체 비교표는 immutable `.json.gz`로 보관하고 해시를 보고서에 결속한다. 운영 보고서는 현재/선정 membership·W/STOP/TIMEOUT/U·추가/제외 수치를 제공한다. 원천 결손과 미확정·실현 손익을 혼합하지 않는다.
- 보조 연구가 설정돼 있으면 선정 membership의 확인점만 기존 bounded consumer에 전달한다. 설정이 없으면 호환 현재 보조를 승계한다. 기계의 모든 후보별 AI fanout과 새 provider 호출을 초기 등록 조건으로 만들지 않는다. 이전 provider 응답 원장은 덮어쓰지 않는다.

### 11.1 준비 명령과 권한

다음 명령은 private 배포대기 산출물만 만든다. 아래 근거 경로는 해시가 고정된 원 연구 디렉터리다. 코드와 원천 parity가 바뀌면 먼저 재검증한다.

```bash
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.scalping.reversal_cumulative_registration prepare \
  --evidence-root /home/ubuntu/KORStockScan/tmp/main-machine-cumulative-research-20261015 \
  --parent /home/ubuntu/KORStockScan/tmp/main-machine-cumulative-research-20261015/baseline-bundle.json \
  --parity tmp/cumulative-adoption-review/native-parity.json \
  --output tmp/cumulative-adoption-review/deploy-wait \
  --publication-date 2026-10-15 --target-date 2026-10-16
```

운영 등록은 배포 지시 후 `reversal_cumulative_registration intake` owner로 수행한다. `--confirm APPROVED_CUMULATIVE_POLICY_REGISTRATION_V2`, `--data-root`, `--prepared`, `--origin-root`, `--origin-commit`을 명시한다. 실제 검토된 origin release의 검증, 코드 해시, publication/target, 현재 parent CAS와 같은 parent의 타 등록 요청 충돌을 검사하고 작은 근거를 durable archive로 복사한다. 준비 산출물의 `operator_receipt=null`을 직접 수정해 등록하지 않는다.

그 다음 기존 `continuous_reversal_postclose`의 machine→auxiliary, v6 stage, 정확한 target PREOPEN/정상 기동 소비 절차를 따른다. 초기 prepare-inputs/calls는 provider 0의 호환 승계이며 소비한 등록안은 다시 적용하지 않는다. registry/selection authority/범위/근거의 봉인을 유지한다. **운영 parent가 연구 parent와 달라지면 CAS 실패를 우회하지 않는다.** 변경된 membership·탐지 코드·근거를 재대조한 별도 successor 등록안을 준비한다. 동일 정책의 코드 배포와 실제 새 정책 선택을 구분한다.

이 인계는 target `2026-10-16`의 다음 세션 준비다. 승인 시점에 날짜가 지났으면 publication/target을 새로 준비한다. 이 작업으로 intraday 활성화·봇 재기동·주문을 수행하지 않는다. `CumulativePolicyAdoptionDeployment1015`가 별도 배포대기를 소유하고, 승인된 적용의 정책/bootstrap/PID 수용은 기존 `DirectFamilyPreopenPolicyHandoff`와 연결한다. 과거 source 수리 OPEN을 새로 만들지 않는다.

### 11.2 최종 수용

격리 검증의 수치·코드 리뷰 findings와 완료 상태는 [구현 검토](../audits/main-cumulative-policy-adoption-implementation-review-2026-10-15.md)에 기록한다. 코드·정의·원천 재생 검증, 배포대기 근거 준비, 실제 등록/배포/자연 신호/실현 성과를 별도 상태로 유지한다.

## 12. 추가 12가설의 구현·리뷰 완료 인계

사용자 후속 구현 지시에 따라 §10의 A17~A20·F23~F30을 기존 선택본 `d05ebbf8770cb63b51a4ae57e9d2924de3fdf975` 기준의 별도 작업본 `/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015`에 구현했다. branch는 `codex/entry-progress-cumulative-20261015`이며 [추가 구현 검토](../audits/main-entry-price-progress-implementation-review-2026-10-15.md)가 실제 변경·성능·검증을 소유한다. §11의 기존 38가설 등록과 이번 50가설 후속 준비를 구분한다.

- 기존 정의1,430개·registry hash와 기존 승인 등록 reader를 보존했다. 신규 고정 resource는50가설·정의3,510개·연구48 scope를 지원한다. 전체 운영128 scope는 native 구조·보조 승계로 검증하며 다른80 scope는 실제 current를 유지한다. 원천이 없는 route를 SOR에서 복제하거나 모든 상장종목의 관측이 완전하다고 표현하지 않는다.
- 연속10체결 가격/bid·30초 bid 전진·spread 대비 범위를 공유 State에서 계산하고, 최초 bid 상승 소비·가격/bid 유지·source 단절·만료·실패 후 재사용 금지·ready 무효화를 구현했다. F는 원 확인점의 정확한 branch replacement이고 신규 A는 독립 OR다. UNKNOWN·custody·기존 주문/안전 guard와 보조 입력·응답·prompt는 보존했다.
- 최종 관련 회귀214개, 동결27 partition·5,587,427행의 확인247,284개·선정9,451개·불일치0, 연구35,558개 대안·48개 선정 확인점 집합 일치를 검증했다. label 원천은 기존 검증본을 재사용했다. 실제 자연 신호·체결·실현 성과의 수용은 별도다.
- 불변 정의 해시 반복 계산을 제거해 같은 신규 family의 평가+typed 투영 p95 CPU를83.30→55.14ms로 줄였다. 동일1만 행에서 기존 정책 p95 CPU307.67→310.31µs, A19 추가322.68µs다. 한 구간의 장후 checkpoint30.22초·cache2.87초·raw 재생0·결과 동일을 확인했다. 실제 PID의 전체 queue/WS 지연 개선을 입증한 결과는 아니다.

[private 준비안](/home/ubuntu/KORStockScan-worktrees/entry-progress-cumulative-20261015/tmp/entry-progress-implementation/deploy-wait/prepared-registration.json)은 publication10/15·target10/16, content SHA `82796bfeee2778ef25433e4cb41d89696ec006653910f5b1a9bf5ac204b4b1db`, `operator_receipt=null`, runtime authority false다. 실제 운영 pending `c15491190e72…`와 current는 이 작업에서 변경하지 않았다. 새 준비는 실제 등록·발행·배포·재기동 완료가 아니다.

기존 `CumulativePolicyAdoptionDeployment1015`가 후속 인계를 소유한다. 실제 적용 시 현재 selected code/parent·기존 등록 소비 여부·날짜·archive를 다시 확인한다. 같은 parent의 기존 pending과 충돌하면 자동 교체하지 않으며, parent가 바뀌었으면 변경 membership을 기준으로 후속 재비교가 필요하다. 지난 초기 등록 승인을 새12가설의 운영 승인으로 재사용하지 않는다. 보유·재생 수리는 기존 별도 owner가 계속 소유하고 이 구현의 선행 수리로 중복 작업하지 않는다.
