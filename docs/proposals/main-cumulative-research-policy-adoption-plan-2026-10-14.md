# Main 누적 상승 포착·실패 감소 연구의 정책 반영 계획 — 2026-10-14

## 1. 목적과 적용 범위

9/29~10/13 누적 원천으로 연구한 고정 후보를 **등록 → 실제 탐지 코드와 재생 일치 검증 → 기존형·추가형·정제형·결합형 비교 → 정책 발행 → 적용 확인**으로 연결한다. 새로운 가설·조건·경계값 탐색은 수동 연구가 담당한다. 장후에는 등록한 불변 후보와 실제 적용 정책을 평가한다.

이 문서는 구현·검증·정책 반영 절차의 제안이다. 이번 작성으로 등록 요청, 정책 선택, 배포, 재기동 영수증을 발급하지 않는다. 구현 착수 시 그 지시의 적용 범위와 기존 승인을 구체적인 batch receipt에 결속한다. 본 계획의 Main 기계 후보와 [entry-split 관측 계약 수리](entry-split-large-report-verification-projection-remediation-plan-2026-10-14.md)는 독립 작업이다.

실행 인계는 [당일 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry`, `DirectFamilyPreopenPolicyHandoff`를 사용한다. 새로운 중복 OPEN ID나 자동 가설 생성 작업을 만들지 않는다. 구현·코드 리뷰·발행·자연 판정·실제 비용 성과는 각각 완료 상태를 갖는다.

## 2. 확인한 기준과 증거

- [누적 연구 결과](../audits/main-machine-cumulative-missed-rise-and-enter-failure-research-review-2026-10-14.md): 고정 가설 25개, 22개 scope, A/F 조합 8,432개. F 개선 12개 scope, A 개선 또는 동률 추가 성공 5개 scope, 두 효과를 함께 보인 J 10개 scope.
- **정정본** [cumulative-result.json](../../tmp/main-machine-joint-research-20261014/corrected/cumulative-result.json)의 SHA256은 `afa281aa051636505a1e4ed34eb2ac64fae53c5bf55706b3a644635c8a95436e`이다. 같은 디렉터리의 manifest, label 검증, native root parity, 원천 보정 receipt를 함께 소비한다. 상위 디렉터리의 정정 전 result는 등록 근거로 사용하지 않는다.
- 기준 bundle은 `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`, family는 `c366914f1a2a76d85bceacd406e6c377f1fb32b2b50d757fb195484ab783ff8c`이다. 이번 점검의 [current pointer](../../data/runtime/mechanistic_entry_policy/current.json)와 같았다.
- 연구 코드 기준은 `ff32b99b3…`였다. 현재 [release selection](../../data/runtime/runtime_release_selection.json)은 `main-nonfixed-submit-20261014-f8dc4431d`, commit `f8dc4431d0b3cc2cb84610979ec4f3440d3e8e46`로 바뀌었다. 따라서 정책이 같아도 구현 때 실제 선택 코드와 replay parity를 다시 확인한다. 이 점검은 현재 PID를 독립 검증한 결과가 아니다.
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

[연구 selector](../../tmp/main-machine-joint-research-20261014/corrected/select_joint.py)는 '새 W 존재 + 기존 F 제거'를 두 축의 효과를 보여 주는 J 표의 포함 조건으로 사용했다. **운영 selector의 필수 조건으로 옮기지 않는다.** F만 유효하거나 A만 유효한 정책도 선택 대상이다.

`highest_fraction_joint`는 J 집합 안의 최고 비율이다. A/F/current까지 합친 전체 승자를 뜻하지 않는다. 또한 `opportunity_joint`는 성공 수를 우선한 연구 대안이다. 운영에서 이를 자동으로 `JOINT_BALANCED` 고정 선택하면 사용자 승률 우선 기준과 충돌한다.

구현에서는 이미 고정한 후보 정의·대상 22개 scope·8,432개 조합 목록을 재사용해 평가한다. 새 조합 탐색을 늘리지 않는다. current/A-only/F-only/J의 기존 고정 대안 중 계약이 입증된 결과를 같은 분모 규칙으로 비교하고 최종 winner를 발행한다. 표의 연구 대표만 읽고 나머지 고정 대안을 누락하지 않는다. 등록 batch에 허용 대안의 전체 membership/hash를 먼저 동결하며, 비교 후 임의로 승인 범위를 넓히지 않는다.

## 4. 현재 결과로 예상하는 반영안

아래는 **현재 보고서에 제시된 대표 A/F/J 사이에서 승률 우선으로 비교한 제안**이다. 수치는 현 정책을 과거 원천에 재생한 확인점 CF이며 실제 발행 ENTER_NOW·독립 거래·체결 수가 아니다. 전체 고정 대안의 native parity와 최종 selection receipt를 대신하지 않는다. 가격대의 중가는 `20000_TO_100000`, 고가는 `GE_100000`, 저가는 `LT_20000`의 기존 코드 경계를 사용한다. PRE는 NXT `_NX`, REGULAR/AFTER는 SOR `_AL`이다.

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

25개 고정 특징/root 계산과 기회 집합을 source/feature/label/definition hash로 재사용해8,432개 조합마다 raw를 다시 읽지 않는다. 날짜별 immutable partition을 만들고 U의 관측 만기·기존 source 수정도 dependency로 무효화한다. 비교 완료 전에 cursor/누적 집계 완료를 먼저 저장하지 않는다. 부하를 줄이려고 종목·시장·후보·관측기간을 숨겨서 축소하지 않는다. 새 신호 증가에 따른 보조 요청 증가는 실제 고유 confirmation과 기존 예산으로 계측하고 중복 호출과 구분한다.

## 8. 계획 리뷰와 인계

계획 리뷰에서 수정한 사항: J 최고비율을 전체 winner로 오해하는 문제, F를 OR 추가해 원형이 우회하는 문제, extended 생성 전 F 평가, 기존 합성 의존성 미지원, 정정 전 BREAKOUT 결과 소비, 후보 catalog와 운영 membership 혼동, 이전 batch 고정 authority 재사용을 각각 구현 항목·반례로 명시했다.

이번 완료 기준은 두 계획의 실제 경로·링크·owner·권한·문서 parser 검증이다. 생산 코드 시험, 큰 보고서 재생성, 정책 변경, provider 호출, 배포/재기동은 계획 작성의 검증에 포함하지 않는다. 구현 완료 시 §7과 실제 적용 영수증은 별도로 보고한다.

계획 검증 결과: 두 문서의 로컬 링크26개·표7개에 오류0, 정정 연구 결과 SHA 일치, 관련 current OPEN owner3개가 각각1개임을 확인했다. print-only parser는25개 작업을 출력했고 `git diff --check`와 새 문서 공백 검사를 통과했다. 이는 계획 검증이며 §7의 구현 시험이 통과했다는 뜻은 아니다.

외부 동기화는 실행하지 않는다. 사용자가 수행할 표준 명령은 두 계획을 묶어 아래 한 개다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
