# Main 병행 연구결과 운영 적용·scope 교체 계획 — 2026-10-13

상태: **구현·반복 리뷰·표적 검증 완료, P1 등록 및 10/14 작업본 정책 후보 준비.** 실제 배포·재기동·PID 소비·자연 성능은 아직 확인하지 않았다. 아래 §15와 [구현 리뷰](../audits/main-joint-operating-and-source-repair-implementation-review-2026-10-13.md)가 현재 상태를 소유하며, §14의 계획 단계 기록은 역사다. [연구 결과](../audits/main-machine-missed-rise-and-enter-failure-joint-research-review-2026-10-13.md)와 [후보 패키지](../../tmp/main-machine-joint-research-20261013/candidate-package.json)의 비교 view를 운영 정책 수로 합산하지 않는다.

## 1. 결정과 초기 적용 범위

기존보다 높은 비용 반영 확정 승률과 제출 기회 확대를 목표로, **기회 확대 선택의 특정 원 branch 교체＋추가 root OR**를 초기 적용안으로 한다. 최고 승률만 남기는 극단적 축소안을 자동 채택하지 않는다. 기존 성공100%/80% 보존이나 실패 절대 건수 불증가를 후보 탈락 조건으로 만들지 않는다.

| 순서 | exact scope | 초기 적용안 | 누적 WIN/확정·승률 | FAIL 변화 | 성격 |
|---|---|---|---|---|---|
| P1 | `036930\|AFTER\|GE_100000\|SOR` | A08＋F05의 특정 legacy branch 교체 | 258/664=38.86% → 264/631=41.84% | 406 → 367 | 주성 애프터의 성공 증가·실패 감소 |
| P1 | `other_non_fixed\|PRE\|LT_20000\|NXT` | A08＋F04의 특정 legacy branch 교체 | 163/239=68.20% → 175/235=74.47% | 76 → 60 | 일반 저가 프리의 성공 증가·실패 감소 |
| P2 | `036930\|REGULAR\|GE_100000\|SOR` | A03＋F03의 특정 legacy branch 교체 | 914/1292=70.74% → 1109/1500=73.93% | 378 → 391 | 확정 성공195건 증가, FAIL13건 증가의 확장안 |

P1 두 scope를 한 원자적 bundle 변경으로 준비한다. P2는 별도 확장 선택지이며 초기 membership delta에 자동 포함하지 않는다. 다른 후보·삼성은 이번 초기 적용 대상에 넣지 않는다. P2의 우선순위는 운영 선택의 범위이며 새 날짜/표본/EV 입증 대기 조건이 아니다.

연구 기준은 `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`, 계산 코드는 당시 불변 `main-residual-reviewed-20261013-v6`다. 계획 조회 시 selector는 `main-entry-deadline-20261013-v7` / `fbe42ca76cc46b5a3ebe3a00ee41eab0c878be38`이고 정책 pointer는 같은 d906 bundle이다. 이는 selector/파일 조회이며 현재 PID의 소비 영수증이 아니다. 구현 착수 때 실제 parent/release/code를 다시 pin한다.

## 2. 효과와 날짜 의존성 공개

[적용 검토 근거](../../tmp/main-machine-joint-research-20261013/operating-application-plan-evidence.json)의 고정 결과 SHA는 `eebaf02f318e04f899dad97d282ec338973d9a7804a5be95b165999ed97dd83a`다.

- 주성 AFTER: 기존 WIN8개·FAIL67개를 제거하고 WIN14개·FAIL28개를 추가한다. 후보 WIN의 목표 시각20개·U243이다. 10/12의 실제 적격 비교도131/275→132/268=47.64%→49.25%다. 날짜 하나씩을 제외한 진단에서도 누적 승률 개선 방향이 유지됐다.
- 일반 PRE 저가: 기존 WIN6개·STOP29개를 제거하고 WIN18개·FAIL13개를 추가한다. 목표 시각50개·U41이다. 제거 효과는9/29에 집중된다. 그 날짜를 제외하면80.25%→78.70%로 개선 방향이 뒤집힌다. **날짜 집중 위험을 공개하고 후속 장후 비교에 표시**하되 이를 최소 날짜/성공 보존율의 새 채택 gate로 쓰지 않는다.
- 주성 REGULAR: 기존 WIN63개·FAIL20개 제거, WIN258개·FAIL33개 추가다. 전체 FAIL 수는 늘어도 실패율은29.26%→26.07%로 낮아진다. 추가 WIN256개가10/8에 집중된다. 확장안의 기회 증가와 집중도를 함께 공개한다.

이 숫자는 같은 원천의 실제 확인점 재생 결과다. 새 날짜의 독립 성능, 실제 거래 수, 주문 성공 또는 PnL을 증명하지 않는다. cost0.0023·순 목표+0.4%·손절−3%·1,800초의 라벨과 source gap/UNRESOLVED 구분을 유지한다.

## 3. exact membership delta

아래 신규 이름은 English ASCII의 제안 alias다. 구현 때 definition/scope/version의 canonical digest로 최종 branch ID를 고정하고 같은 이름의 정의를 덮어쓰지 않는다.

### 3.1 주성 AFTER SOR 고가

- remove: **`legacy_dd5_ge_0_4_v1`만 해당 scope에서 제거**.
- add successor: `joint1013_jusung_after_vwap_refined`, 원 branch의 root·원 조건·확인점에 F05의 `vwap60>=0` 조건을 합성한다.
- add independent: `joint1013_jusung_after_breakout_a08`, A08의 직전60초 고점 돌파·ret60≥0%·DD≤0.4%·signed BUY10≥60.
- carry: `manual_extended_27bebc59a6315682`.
- before2개→after3개이며 기존 정책과 연구 후보의 숫자를 다시 더해 효과를 계산하지 않는다.

### 3.2 일반 PRE NXT 저가

- remove: **`legacy_dd5_0_8_vol_up_v1`만 해당 scope에서 제거**.
- add successor: `joint1013_general_pre_low_session_refined`, 원 branch의 root·원 조건·확인점에 F04의 `session_return<=0.4%`를 합성한다.
- add independent: `joint1013_general_pre_low_breakout_a08`, 해당 가격대/시장에 한정한 A08.
- carry: `manual_extended_f74502b35a4fae1f`, `manual_residual_29b499784843baed`, `manual_residual_bac0e83e966ed3ea`.
- before4개→after5개다. 같은 원 legacy ID의 다른 시장·가격대 membership은 유지한다.

### 3.3 P2 주성 REGULAR 확장안

- remove: 해당 scope의 `legacy_dd5_0_8_vol_up_v1`.
- add successor: 원 조건＋F03 `session_return>=-0.4%`.
- add A03: FIRST_PRICE_HOLD1, session_return≥−0.4%, ret60≥−0.2% 및<0.2%, DD<0.4%, BUY10≥60.
- carry: `manual_path_7d9fd5ccc8bfe99b`.
- P2 선택 시 P1 완료 bundle을 parent로 새 delta를 만든다. 원 d906 hash를 그대로 CAS에 재사용하지 않는다.

정의 catalog에는 원본·후속 정의를 모두 보존한다. **operating membership에 들어간 모든 branch만 동등하게 독립 탐지**한다. 비교 전용 원본/다른 variant를 live OR에 숨겨 넣지 않는다. 동일 tick의 multiple hit는 한 canonical opportunity·한 AI 요청·한 intent로 소비한다.

합성 정의의 원본은 `dependency_definition_ids`, 실제 OR 대상은 `operating_branch_ids`로 구분한다. 제거한 원 branch도 내부 FSM·predicate·원 proof를 계산할 정적 의존성으로 보존하지만 union signal/AI/intent 대상에는 넣지 않는다. 원 definition hash와 registry ancestry가 해석되지 않으면 fail closed다. 이번 합성은 승인된 원 정의를 한 번 감싼 형태로 고정하고 순환·자기 참조·합성 정의의 재합성을 허용하지 않는다. 후속 수동 연구가 새 합성을 필요로 하면 새 정의와 별도 승인을 만든다.

## 4. 현재 코드에서 확인한 구현 결손

| 경로 | 현재 상태 | 필요한 변경 |
|---|---|---|
| [manual intake](../../src/engine/scalping/reversal_manual_registration.py) | 이전6개·proposal SHA·ADD·4scope에 고정 | 새 batch 및 exact ADD/REPLACE delta, immutable 정의/evidence와 CAS 검증을 별도 version으로 지원 |
| [v6 membership](../../src/engine/scalping/continuous_reversal_policy_v6.py) | manifest는REPLACE를 지원하지만 기존 residual 정의가 있으면 마지막 receipt가 이전6개 승인과 같아야 함 | carried 정의의 원 승인＋새 delta 승인의 계보를 정의별/parent별로 검증. 마지막 변경 receipt 하나만으로 전체 원 승인을 대체하지 않음 |
| [catalog](../../src/engine/scalping/reversal_extended_catalog.py) | 고정38개 정의·기존 successor registry | 원 registry 보존, P1 신규4개 정의의 후속 registry generation·version 및 원 definition ref |
| [native State](../../src/engine/scalping/reversal_extended_state.py) | 기존 root의 TRUE/FALSE/UNKNOWN 및 단순 filter | 원 branch predicate＋새 보완의 ternary 합성, 원 확인 event/ask 유지, A08 독립 root |
| [typed signal](../../src/engine/scalping/reversal_extended_auxiliary.py) | 기존 extended signal kind/증빙 검증 | composed successor의 base proof·refinement proof·definition/version·source binding과 projection 지원 |
| [장후 producer](../../src/engine/scalping/continuous_reversal_operating_postclose.py) | 주로same/add_all/별칭ADD 비교, 평가가 operating membership을 임의 제거하지 않음 | 명시적 current/add-only/joint 및 승인 variant 비교·선택 연결. F 결과가 추천으로만 끝나지 않도록 publisher까지 확인 |
| [v6 보조 장후 분기](../../src/engine/scalping/reversal_auxiliary_tuning.py) | v6는 이 경로로 위임하며 현재 machine cell을 복사해 carry | 실제 사용 분기에서 선택된 machine membership을 소비. 이전 producer의 미사용 fallback만 수정하고 완료 처리하지 않음 |
| [실제 path anchor 복원](../../src/engine/scalping/reversal_path_runtime.py)·[carried native](../../src/engine/scalping/reversal_registered_runtime.py)·[native dispatcher](../../src/engine/scalping/reversal_extended_runtime.py) | 당일 원천 전체가 비었을 때만 새 anchor를 만드는 경로가 있고 union State는 복원된 stream anchor만 전달받음 | 날짜 전체의 원천 유무와 종목별 첫 관측을 분리하고, 검증된 anchor를 native/carried/union State에 같은 신원으로 연결 (§9.3) |
| [판정 특징 캐시](../../src/engine/scalping/reversal_path_runtime.py)·[진단 reader](../../src/engine/scalping/reversal_source_diagnostics.py) | base 특징의 복사본에 추가한 dd/volume이 진단 캐시에 없어 계산값과 결손 표시가 어긋남 | 실제 branch 판정 시점·phase의 특징과 진단을 같은 epoch/sequence에 결속 (§9.4) |
| [비상시 probe](../../src/engine/scalping/zero_base_probe.py)·[queue consumer](../../src/scanners/zero_base_discovery_runtime.py) | 정상 no-match도 required_feature_insufficient로 저장하며 처음 15초의 원천 미달로 남은 residence 전 종료 가능 | 결과 계약과 모든 독자를 함께 변경하고 원 lease 안에서 초기 수신 대기·native 탐지·계산 연결을 검증 (§9.5–§9.6) |

기존 ADD receipt가 successor에서 `pending`으로 다시 열려 교체한 원 branch를 복구하지 않도록 consumed/superseded lineage와 idempotency를 검사한다. registration status, 새 policy publication, PREOPEN, 현재 PID consumption을 각각 별도 영수증으로 남긴다.

## 5. F 합성·UNKNOWN의 실행 계약

원 branch의 definition hash·원 predicate·root/phase·actual confirmation을 합성 정의에 고정한다. 원 legacy 조건을 일반 FIRST나 momentum 필터로 유사하게 바꾸지 않는다.

| 원 branch truth | 새 보완 truth | successor truth | 의미 |
|---|---|---|---|
| TRUE | TRUE | TRUE | 원 신호＋검증된 보완 충족 |
| TRUE | FALSE | FALSE | 검증된 보완 불일치로 해당 branch만 제외 |
| TRUE | UNKNOWN | TRUE | 연구의`preserve_current`와 같은 기본 동작; unknown 증빙 보존 |
| FALSE | 무엇이든 | FALSE | 새 보완으로 원 신호를 만들지 않음 |
| UNKNOWN | 무엇이든 | UNKNOWN | 원 source/root 미입증을 TRUE로 올리지 않음 |

이 UNKNOWN 보존은 새 선택 특징에만 적용된다. 원 source/quote·conflict·preflight·native interval·시장·계좌·주문·수량·custody·provider·hard safety 불명/실패는 기존 guard가 계속 소유한다. `owner_retirement.py`의 symbol/owner 신규 진입 제외와 Main/manual custody 경계도 모든 새 경로에 동일하게 적용한다. 역사 episode 보유를 Main이 인수하거나 잔여 수량 때문에 Main 전체를 막지 않는다. UNKNOWN을 숨기려고 현재 값/다른 route/이전 성공 응답을 빌리지 않는다.

원 root의 계산과 보완 특징을 현재 공유 rolling state에서 재사용한다. 구현 표현은 `original_definition_ref + conditional_refinement`의 새 definition kind를 권장한다. 내부 원 predicate 재사용이 원 branch를 operating 신호 목록에 다시 추가하는 결과를 내면 실패다. 이종 원 root/confirmation의 proof를 하나의 새 root라고 발행하지 않는다.

### 5.1 원 확인 event에서 한 번만 보완

연구의 F04/F05는 **이미 발생한 원 branch 확인점의 선택 필터**다. 원 FSM이 후보/hold/확인을 생성하고, 그 실제 확인 event에서 F를 한 번 평가해 successor를 발행하거나 제외한다. `base_condition AND refinement`의 FALSE→TRUE를 별도 root로 사용하지 않는다. F가 FALSE인 확인점을 소비한 뒤 다음 tick에서 F가 TRUE가 됐다는 이유로 같은 anchor를 재발행하거나 hold/deadline을 다시 시작하면 연구와 다른 정책이다.

원 legacy의 FIRST 시점 조건·동결 특징과 이후 CONFIRMED 시점 조건을 기존 계산 그대로 보존한다. 새 F 특징은 연구처럼 **실제 확인 tick까지의 prefix**에서 계산한다. `base_anchor_ref`, `base_confirmation_ref`, `refinement_feature_ref`에 각 시각·native epoch/sequence를 남기고 실제 확인 ask와 canonical opportunity를 유지한다. 원 FIRST 특징을 확인 시점 값으로 다시 계산하거나 F의 확인 시점 값을 FIRST proof로 표시하지 않는다. 독립 A08만 자신의 root transition에서 새 기회를 만든다.

### 5.2 optional UNKNOWN과 계약 오류 구분

위 진리표는 definition·source binding이 유효한 상태에서의 값 부족에 적용한다. optional rolling history/qty/side/검증된 session anchor가 부족하면 F는 UNKNOWN이고 원 확인을 유지한다. 반면 원 definition 미해석, 잘못된 phase·schema·해시·item/route·다른 확인점의 proof는 계약 오류다. 이를 optional UNKNOWN으로 바꿔 통과시키지 않고 기존 계약/source validator가 해당 신호를 차단한다. 식별 가능한 결함을 전체 입력 차단으로 확대하지 않는다.

F가 여러 조건이면 유효 입력에서 known FALSE가 UNKNOWN보다 우선한다. 진리표의 원 truth는 임의 tick의 원 조건 값이 아니라 **원 탐지기가 그 tick에 발행할 유효 확인 event**다. 원 확인이 없는 tick에는 F가 충족돼도 신호0이다. 보조 입력에는 검증된 원 proof와 optional 부족의 정확한 원인을 전달하고, 그 부족을 전체 신호 무효나 자동 PASS로 해석하지 않는다.

warm 연구 prefix와 cold live source의 history 차이는 의미 회귀와 운영 coverage를 구분한다. 과거 재생의175/235·264/631이 모든 cold source에서 그대로 재현된다고 주장하지 않는다. 실제 확보된 anchor/rolling 입력으로 같은 조건을 평가했는지와 refinement UNKNOWN/유지된 baseline의 비중을 자연 수용에서 별도로 측정한다. 필요한 공통 source가 없는 신호를 입력 보강 없이 강제 승격하지 않는다.

원 신호의5초 deadline·generation·single claim은 유지한다. A08/A03은 각각 실제 독립 확인 event의 신원을 갖고, 오래된 원 신호를 재확인한 것처럼 deadline을 연장하지 않는다.

F의 known FALSE는 해당 branch의 정상 패턴 불일치로 기록한다. 다른 branch가 TRUE이면 정상 union 신호이며, 전체 FALSE/UNKNOWN의 결과는 기존 native 판정 계약대로 구분한다. 이를 `SOURCE_INVALID`, API 장애, 주문 실패로 재분류하지 않는다. 새 보완 UNKNOWN의 원 판정 유지도 source hard gap 해소나 재조회 성공으로 표시하지 않는다.

## 6. 특징·root·cold source parity

| 특징 | 연구의 정확한 정의 | 실행 검증 |
|---|---|---|
| session_return | 해당 source/item/session의 첫 유효 관측 체결가 대비% | §9.3의 검증된 최초 관측/복원 ref를 사용. 재기동·재등록 시 기준가격을 다시 잡거나 당일 시가·현재가로 대체하지 않음 |
| ret60 | 현재 수신 체결가/`t-60` 이하의 마지막 체결가−1의% | 연속 source interval·60초 warmup, 경계 tick 포함. 미래/가장 가까운 tick으로 대체하지 않음 |
| vwap60 | 현재 **체결가**/`[t-60,t]`의 수량 가중 평균−1의% | 60초 source coverage·구간의 유효 가격/양수 qty·양수 합계. 구간 내 qty 부족은 UNKNOWN; 실제 ask outcome과 구분 |
| DD | `t-300`부터 현재 tick 직전까지 확보된 연속 prefix의 최고 체결가/current_trade−1의% | 현재 행 제외, 같은 시각의 이전 sequence는 포함. source reset·부분 prefix 허용을 대사하고 새로운 300초 필수 체류 조건을 추가하지 않음 |
| BUY10 | 현재 tick을 포함한 **연속 마지막10개 체결**의 매수 수량 비중% | 10개 모두 같은 유효 interval·알려진 side·양수 qty. 불명 체결을 건너뛰어 과거의 알려진10개를 모으거나 SELL로 치환하지 않음 |
| A08 breakout | current_trade가 직전60초 최고가를 엄격 초과한 known FALSE→TRUE | 선행 하락/FIRST 없이 모든 유효 tick에서 독립 탐지 |

연구에서 session anchor를 전체 보유 시리즈의 첫 유효 가격으로 썼다는 점을 확인한다. cold probe가 그 anchor의 provenance를 갖지 못하면 session 특징은UNKNOWN이다. 다만 **새 stream의 검증된 최초 실제 관측을 기록하는 정상 producer까지 UNKNOWN으로 고정하지 않는다.** §9.3은 이 연결 결함을 수리하며 이미 존재했던 최초 체결을 현재 tick으로 대체하지 않는다. 원 branch의 필수 session 결손과 새 F의 optional session UNKNOWN은 별개다. 과거 입출력으로 parity를 맞추려고 live anchor를 소급 생성하지 않으며 warm/cold의 anchor 범위와 효과를 각각 보고한다.

연구의 spread가 필요한 후속 정의는 `100*(ask-bid)/trade_price`다. native quote guard나 기존 legacy 조건의 spread 공식을 이 값으로 변경하지 않는다. 새 복합 정의의 required history와 optional refinement history를 구분해 optional UNKNOWN이 무조건 긴 residence admission을 강제하지 않게 한다.

existing 슬롯5/long2·60/150초·원 lease와 cleanup/ACK를 유지한다. first data의 actual price band, 2만원 경계 이동, route/session 교체, shared owner/reconnect/REMOVE와 series gap을 검사한다. 다른 branch의 FIRST 무효화가 독립 A08을 무효화하지 않게 기존 branch별 lifecycle을 보존한다.

catalog 해시를 기존6개 residual ID 포함 여부로 추론하지 않는다. 선택한 후속 registry와 그 parent chain에서 operating＋dependency 정의·phase를 검증한다. `definition/branch/applicable/phase/matches`뿐 아니라 State dispatch, snapshot, typed projector/production request, union reader, residence/readiness descriptor, family validator와 cache/실행 hash를 함께 연결한다. readiness는 원 root의 필수 history와 F의 optional history를 따로 표시한다. F05의60초/qty 부족만으로 원 branch의 최소 체류를 늘리거나 REST 보강·새 구독을 시작하지 않는다.

등호/엄격 부등호·시간 구간 경계와 수치 계산 방식도 definition/version에 결속한다. threshold 주변의 부동소수점 차이를 넓은 tolerance로 통과시키지 않는다. 기존 공유 rolling 계산을 재사용하더라도 원 확인점의 조건값과 연구의 판단이 달라지면 원인을 특정하고 실제 후보 결과를 다시 계산해 보고한다. 당시 결과를 유지하려고 틱마다 전체 prefix를 재생하거나 값을 반올림해 조건을 맞추지 않는다.

## 7. registration·publisher·보조 소비 연결

1. 새 research batch를 P1 exact2scope·신규4정의·remove2개로 고정한다. baseline bundle/result/code/label/source hash와 native parity receipt, 원 승인 계보를 보존한다. `tmp`만을 publication source로 쓰지 않고 필요한 근거를 기존 content-addressed registration archive로 이관한다.
2. 하나의 `kind=REPLACE` receipt로 해당 scope의 remove와 A/F add를 원자적으로 검증한다. 정확한 user-designated initial adoption scope를 기록한다. 이전6개 승인 문자열/고정SHA를 이번 batch 승인으로 재사용하지 않는다.
3. publisher.lock/CAS로 parent와 target을 재확인한다. 정책/manifest/cell payload/registry/definition/code/source/hash가 같은 세대로 발행되어야 한다. receipt partial write·중복 실행·새 parent·이미 consumed·rollback successor를 검사한다.
4. 합성 branch의 typed source/input을 보조판정 normalizer/validator/backend/projector에 전달한다. 원 phase·root proof, 새 branch ID·refinement truth/feature ref를 정확히 검증한다. 보조 AI의 프롬프트/schema 필드·role/rule은 English ASCII로 유지한다. 정책 연구 수치나 후행 WIN/FAIL은 장중 prompt 특징으로 넣지 않는다.
5. 현재 보조 arm/model/provider를 유지하는 compatible binding으로 초기 채택한다. 새 typed kind의 reader 호환성을 동결 입력으로 검증하고 기존 `auxiliary_reader_readiness` receipt를 발행한다. 바뀐 input/hash에 옛 PASS/cache/request token을 재사용하지 않는다. 공유 원5초·소비 거절·source/quote·budget·quantity/intent/submit guard는 유지한다.
6. 초기 지정 채택에 새로운 EV·표본/일수·특정 새 날짜 WIN·보조 비교 완료 gate를 추가하지 않는다. 기계+보조 source/reader/native publish 계약은 검증한다. 초기 binding은 보조 PASS 성능 입증이나 자동 PASS가 아니며 자연 PASS→Main 소비는 별도다.

### 7.1 여러 등록 batch의 보존·소비

현재 단일 `residual-registration.json`은 다른 request가 있으면 conflict이며, `pending()`은 add가 이미 포함됐는지만 확인한다. 새 batch는 기존 content-addressed registration archive에 **별도 불변 request**로 저장하고, 기존 intake/publisher 소유의 선택 pointer와 parent CAS로 소비한다. 이전6개 v1 request·승인·근거를 덮어쓰거나 같은 승인 문자열의 의미를 확대하지 않는다. pending 선택은 한 번에 하나이며 다른 세션의 batch를 자동 합치거나 오래된 request를 찾아 재실행하지 않는다.

새 REPLACE의 완료는 `add_present`뿐 아니라 `remove_absent`, exact before/after scope hash와 발행 bundle에 결속된 consumed receipt가 모두 맞아야 한다. 동일 batch 재실행은 같은 완료 receipt를 반환한다. receipt 없는 부분 변경·다른 parent·target 변경은 충돌로 남긴다. consumed/superseded/rollback receipt는 append로 보존하고, rollback 후 옛 pending이 다시 적용되지 않도록 소비 상태를 함께 확정한다. 해시가 우연히 같은 membership만 보고 새 등록 승인을 생략하지 않는다.

effective 보조 binding은 arm뿐 아니라 prompt/model/provider·input/response schema·reader·overlay ancestry를 고정한다. 새 typed projection이 기존 input version으로 표현되지 않으면 동일 arm/prompt의 호환 successor binding을 새 hash로 발행한다. 과거 binding/overlay를 덮어쓰거나 다른 input version의 registry를 그대로 복사해 호환이라고 표시하지 않는다. model/provider/프롬프트 성능 변경 권한을 이 source 계약 보완으로 확대하지 않는다.

날짜는 `research_cutoff_date=2026-10-12`, 실제 `evaluation_source_date`, 실행의 `publication_date`, calendar가 정한 `effective_date`로 분리한다. 기존 ADD 전용 실행기의`day==publication` 전제를 새 계약의 전 날짜에 강제로 적용하지 않는다. 고정 과거 연구를 오늘 자료로 relabel하지 않고, 닫힌10/12 표준 report·controller/strict bytes를 새 등록 때문에 덮어쓰지 않는다. isolated typed-publication→native immutable candidate를 소유하며 당일 정상 장후 consumer가 새 등록/비교 영수증을 같은 세대로 연결하도록 구현한다. `source_date<=publication_date<effective_date`인 다음 세션 계약과 intraday 날짜 계약을 별도로 검증한다.

## 8. 장후 비교와 이후 선택

수동 연구의 고정 정의만 소비한다. 장후에서 새 threshold/조건/패턴을 만들지 않는다.

- 최소 비교: `CURRENT_NATIVE`, `ADD_A_ONLY`, `REPLACE_F_ONLY`, `JOINT_BALANCED`와 지정 원본 `PREVIOUS_BASELINE`을 같은 source cutoff·label·scope·확인점으로 재생한다.
- 보고 항목: 정책별/전체OR/leave-one-branch-out, 기회·WIN/STOP/TIMEOUT/U, 제거 WIN/FAIL, 추가 WIN/FAIL, 목표 시각·날짜/종목 집중, feature/source UNKNOWN, 실제 적용 version·실주문·비용 손익을 분리한다.
- definition catalog 등록과 operating membership을 구분한다. operating에 선정된 모든 branch는 동등하게 독립 탐지하며, 원형 baseline은 비교 catalog에만 남긴다. 원형과 보완형을 동시에 live OR로 둬 F 효과를 상쇄하지 않는다.
- 현재 publisher는 operating membership을 평가만으로 제거하지 않는다. 구현 단계에서 **명시적인 승인 variant group·선택 위임**을 정의해야 자동 교체를 허용한다. 그 위임은 exact scope와 이미 등록된 고정 membership alternatives에 한정한다. 새로운 정의·임의 branch 제거·다른 시장으로 확대하지 않는다.
- 이 선택 위임은 미래 구현·적용 지시에 포함되는 구체적 권한이며 **현재 계획 요청에서 이미 발급된 것으로 만들지 않는다**. 초기 P1 지정과 이후 승인 variant 사이의 비교·선택 권한을 receipt에서 구분한다. 재등록 정책 전체를 동일하게 독립 탐지하되 연구 catalog의 미선정 variant는 operating branch로 취급하지 않는다.
- selector는 동일 적격 범위의 누적 비용 반영 확정 승률로 current와 승인 successor를 비교한다. 더 높으면 해당 승인 variant를 다음 적용 주기로 선택하고, 동률은 추가 확정 성공·현재 variant 선호의 deterministic tie 순서를 쓴다. 새 성공 보존율·손실 건수 상한·EV/일수 gate는 없다. 분모0·검증 불완전·공통 원천 범위를 입증할 수 없는 결손은 null/원인과 current carry로 표시한다. 식별 가능한 결손 행/구간은 제외하고 나머지 비교를 유지한다.
- 최고 승률의 극단 축소 variant는 연구 비교로 보존한다. 이번 초기 채택은 `JOINT_BALANCED` 지정이다. 별도 명시되지 않은 극단 축소 variant를 selector의 live 허용 집합에 자동 추가하지 않는다.

선택 변경의 기준/입력/정확한 before→after membership과 parent/policy hash를 manifest로 발행한다. report 추천, 실제 policy 선택·발행, PREOPEN와 PID 소비를 같은 상태로 표시하지 않는다.

### 8.1 비교 분모·variant·실제 선택 경로

- 본 batch의 비교 하한은 `2026-09-29`다. 초기 연구 cutoff는10/12, 이후 장후 cutoff는 그 작업의 확정 source date다. producer의 기존 `retained_clean_baseline` 표시만 믿지 않고 원 manifest·cache·누적 집계의 실제 일자/route/item을 검사한다. 이 batch의 하한을 전역 source-quality baseline 변경으로 확대하지 않는다.
- 같은 source universe와 라벨 계약에 각 variant를 적용하고 **각자 선택한 기회 전체**로 `WIN/(WIN+STOP+TIMEOUT)`을 계산한다. 정책 hit의 교집합이나 보조 PASS만을 기계 승률 분모로 사용하지 않는다. U는 별도, source-invalid는 제외 이유·행/기회 수와 함께 보존한다. 후보·baseline이 다른 raw 유효성/유실 구간을 사용하면 같은 검증된 범위로 맞추고, 그 범위를 입증할 수 없으면 비교 불완전으로 표시한다. 결손 행을 FAIL0/WIN0으로 채우지 않는다. 새 root가 필요한 특징 부족으로 UNKNOWN인 것과 raw source-invalid를 구분하고, optional F UNKNOWN이나 식별된 역사 결손 일부만으로 누적 전체를 차단하지 않는다.
- variant group은 exact scope·불변 기준 membership·각 alternative의 전체 ID 목록/hash·선택 규칙·위임 receipt를 고정한다. P1 적용 뒤 `CURRENT_NATIVE`는 **실제로 적용 중인 JOINT**이며, `PREVIOUS_BASELINE`은 불변 원본이다. 매일 current에 A를 다시 더하거나 이미 합성된 F를 다시 감싸지 않는다. 동일 membership variant는 같은 비교 object를 참조하되 alias/승인 역할은 보존한다.
- 정상 누적 비교는 원 definition/refinement/UNKNOWN 의미·feature code/history contract·scope/cutoff·canonical label/source hash를 generation에 결속한다. 기존 보고서를 복사해 manifest만 바꾼 초기 publication은 `comparison_complete=false`인 **지정 채택 영수증**이다. 그 보고서의 옛 metrics를 새 정의의 재생 결과로 표시하지 않는다. 등록 archive의 연구 결과와 새 native 비교 결과를 각각 참조한다.
- machine selector의 정확한 선정 variant를 v6의 실제 보조 장후 분기에 전달한다. 현재 `reversal_auxiliary_tuning.auxiliary_report()`가 복사하는 parent machine cell을 그대로 stage하면 선정이 소실된다. machine membership·source/schema에 호환되는 **실제 effective 보조 binding/overlay**를 읽고 같은 세대의 machine/auxiliary bundle로 발행한다. 보조 prompt/arm의 성능 교체는 그 기존 비교 owner가 담당하며 기계 선택을 `add_all`의 PASS 건수로 다시 결정하지 않는다.
- machine 비교 불완전·분모0은 실제 current machine과 호환 보조 binding을 carry한다. P1 이후 carry가 자동으로 원 legacy를 복구하면 실패다. 보조 비교가 불완전해도 호환 arm carry가 가능하면 machine의 유효 선택을 새 보조 성능 gate로 막지 않는다. 실제 reader/schema/source 호환 계약이 깨졌다면 current pair를 유지하고 그 결손을 표시한다. 초기 P1 지정에 대한 §7의 비교 불필요 계약은 별도로 유지한다.
- 기존 shared ledger의 request identity·dedup·일일 Provider budget을 유지한다. machine 전체 기회 비교는 완전한 원천 population으로 수행하고, budget으로 샘플된 보조 비교는 expected/sampled/not-sampled·pending을 별도 보고한다. 새 variant마다 예산을 초기화하거나 동일 입력을 중복 전송하지 않는다. 이번 계획 검증에서는 Provider 호출0이다.

## 9. 원천 결손 보완과 비상시감시 연결 수리

### 9.1 10/12 source epoch 결손 보완

PRE15347행·REGULAR496054행의 valid0은 원 `sequence_epoch`가 없다는 결론이 아니다. 현재 정규화 조건은 원 숫자 epoch가 quality의 `allowed_sequence_epochs`에 없으면 `source_epoch_unverified`로 제외한다.

1. 기존 `main_market_source_v1` 원 CSV/header·manifest/quality·collector instance/sequence epoch·native transport/route seq·수신 session과 hash를 같은 item/route/date에서 대조한다.
2. raw에는 실제 epoch가 있고 quality receipt가 빠뜨렸는지, 다른 collector/세대/manifest를 읽었는지, 일자/venue key/상대경로·cutoff가 잘못 연결됐는지 최초 단절을 특정한다. 확인된 원 자료로만 새 isolated generation을 만든다.
3. 원 증빙이 실제 없으면 그 row/window의 source gap을 유지한다. 현재 PID/현재 시각/다른 epoch를 역사 값으로 주입하거나 quality의 허용 목록을 무조건 넓히지 않는다.
4. 복구된 적격 source는 동일 고정 후보/기준으로 재생해 원 결과와 delta를 별도로 보고한다. 그 재생을 새로운 패턴 최적화나 다른 source date의 혼합으로 바꾸지 않는다. source gap 수리는 지정 초기 채택의 새 대기일 조건이 아니다.
5. WS parser/FID/REG/recovery·실제 요청/인증 흐름을 수정하게 되면 AGENTS의 현행 공식 Kiwoom reference gate를 먼저 닫고 SHA·경로·조회 시각을 기록한다. 현재 계획은 프로토콜 수정이 아니다.

이 점검은 I0~I3과 병행하는 범위 제한된 source 작업이다. 원 증빙으로 복구되면 새 비교 generation을 만들고, 복구 불가능하면 excluded/source-gap 영수증으로 종료한다. **과거 PRE/REGULAR의 valid0을 모두 복구해야 P1을 발행할 수 있다는 선행 gate를 만들지 않는다.** 적용 시점의 실제 source/reader/guard 검증은 그대로 필요하다.

### 9.2 새 점검 근거와 보완 순서

[비상시감시 점검 원천](../../tmp/nonfixed-source-pattern-machine-check-20261013/findings.json)과 [격리 재현](../../tmp/nonfixed-source-pattern-machine-check-20261013/structural-reproduction.json)을 구현 착수 때 기존 근거 archive에 작은 불변 객체로 이관한다. 원장·raw 전체 복제는 하지 않는다. 근거의 PID는 `2535402`, start ticks는 `10896411`, release는 `main-entry-deadline-20261013-v7`, bundle은 d906, family는 `745df78f7234a6b02e2b57f6623ce31846e6f8dd642643a095648f8c4fd3be7c`다. 이 값은 10/13 점검 당시 신원이며 다음 실행의 current pin으로 재사용하지 않는다.

- 13:32 집계의 비상시 917종목·937경로 중 현재 PID 가동 구간에서 claim된 169경로의 **최신 상태**는 source_unavailable111·required_feature_insufficient57·queued1이다. 시도 전체·주문 수·실패 승률의 분모가 아니며 진행 중인 lease와 과거 latest 상태를 분리한다. native ready/claim은0이다.
- 비츠로테크 `042370`은 약149.5초·체결40/호가105건을 확보했지만 session이 부족했다. `111770`의 약145.7초 관측에도 같은 결손이 표시됐다. 반면 JB금융지주 `175330`은 session 결손 없이 패턴 미충족으로 종료됐다. 57건 전부를 같은 결함 또는 놓친 WIN으로 확정하지 않는다.
- 격리 State에 정상 체결을600초 입력해도 anchor=None이면 session/session_trend=None이 유지됐다. 합성 fixture의 다른 G4 조건을 모두 같게 두면 session 유무에 따라 TRUE/UNKNOWN이 달랐다. 이는 구조적 계약 재현이며 실제 진입·성과·600초 체류 권한을 증명하지 않는다.
- 정규장의 초기 source wait는15초, empty wait는10초, 최소 exact 0B는5건이다. 0B/0D의3초 최신성 검사를 통과해야 다음 단계로 진행한다. 엔투텍의3/6건·0B age 약3.38초와 한일철강의0/2건은 원천 확보 전 종료 사례다. 체결 희소와 API 손실을 구분한다.

보완은 **N0 기준 고정 → N1 종목별 세션 기준가격 연결 → N2 실제 판정 특징과 진단값 일치 → N3 패턴 미충족과 원천 결손 분리 → N4 기존 관측시간 안에서 체결 대기 방식 개선** 순서다. N1은 탐지 기능 수리, N2/N3은 원인·증빙 수리, N4는 관측 실행 개선이다. P1 membership은 §3의 두scope만 교체하지만 이 공통 source 수리는 기존 특징을 쓰는 실제 stream에 적용한다. 그 영향을 membership 변경으로 숨기지 않는다.

### 9.3 N1 — 종목별 세션 기준가격 연결

**owner:** 기존 normalized source/anchor 복원·registered/path/extended runtime·State다. 별도 가격 조회 API나 detector를 만들지 않는다.

1. anchor key를 기존 의미인 `(date, symbol, venue, exact item, market session)`으로 고정한다. 실제 양수 체결가·수신/거래 시각·원 transport epoch/route sequence·source ref·필수 품질을 보존한다. `PRE/NXT/_NX`, `REGULAR/SOR/_AL`, `AFTER/SOR/_AL` 사이의 anchor를 섞지 않는다. policy price band는 anchor의 신원이 아니므로 같은 stream의 가격대 이동에서 기준가격을 다시 잡지 않는다.
2. 복원된 유효 anchor가 있으면 그대로 쓴다. **그 날짜에 다른 종목의 파일이 있다는 이유로 신규 stream의 최초 관측 기록을 금지하는 조건을 제거**한다. 신규 stream은 기존 collector가 검증한 최초 실제 관측 체결로 한 번만 초기화한다. cache miss만으로 신규라고 판단하지 않고 이전 관측 없음/복원 완료 범위·collector 최초 관측 ref를 확인한다.
3. 이미 관측됐던 stream의 첫 값이 유실·불명인 경우에는 원 증빙의 정확한 ref/index로만 복원한다. 복원 불가능하면 `session_anchor_unobservable`을 유지한다. 현재가·당일 시가·다른 route의 값·재기동 후 첫 tick을 역사 anchor로 대체하지 않는다. 필수 session 결손은 원 branch UNKNOWN이며 §5의 optional F 보존으로 우회하지 않는다.
4. 원 anchor owner의 동일 ref를 carried native와 operating/union State에 전달한다. State 생성 후 합법적으로 복원이 완료되면 기존 owner lock 아래 해당 stream의 소비자만 갱신하고 특징 캐시도 무효화한다. 같은 row의 이전 None 캐시가 남거나 이미 소비한 확인점이 재발행되지 않게 한다. 당일 다른 종목·세션·warm stream의 anchor를 변경하지 않는다.
5. 최초 관측 ref는 기존 필수 source 저장/metadata 경로에 작게 dedup해 보존하고, 재등록/재기동·generation 전환에서도 복원한다. provider/DB/file read를 신호의5초 경로에 추가하지 않는다. 새 보조 index가 필요하면 기존 source owner에서 bounded·atomic·단일 writer로 유지하며 값/세대 충돌은 해당 stream 결손으로 처리한다. 재기동 시 index의 원 source 신원·완전성·보존 범위를 검증하고 매번 일중 전체 raw를 다시 읽지 않는다. anchor index는 rolling 구간의 연속성 증거가 아니므로 서로 다른 lease의 rolling history를 이어 붙이지 않는다.

**종료 기준:** 다른 종목의 원천이 있는 날짜에 처음 들어온 stream도 검증된 첫 체결 후 session 값이 계산된다. 동일 stream 재등록·restart·가격대 이동은 같은 anchor ref를 유지하고 session/day/route가 바뀌면 섞이지 않는다. 기존 anchor가 유실된 fixture는 끝까지 UNKNOWN이다. N0의 같은 600초 fixture에서 ‘값이 영구 None’인 결함은 제거되며, 실제 패턴 발생이나 WIN 자체를 성공 조건으로 강제하지 않는다.

### 9.4 N2 — 실제 판정 특징과 진단값 일치

**owner:** 기존 State/feature cache·`branch_readiness`·typed source projector다.

현재 `features()`는 base 캐시의 복사본을 반환하고 dd/volume은 그 복사본에 추가된다. 진단이 base `_feature_values`만 읽으면 실제 계산값을 결손으로 표시한다. 이를 고치려고 공통 캐시에 current DD를 무조건 넣어 legacy FIRST의 low-based DD나 동결 volume을 덮어쓰지 않는다.

- 실제 detector가 사용한 **branch/phase별 확인점**의 값·존재 여부·실제 source ref·기준 native epoch/sequence를 작은 읽기 전용 projection으로 제공한다. root/필수 특징과 optional F 특징을 분리한다. low-based FIRST, 원 CONFIRMED, confirmation-based DD/volume의 서로 다른 의미를 보존한다.
- `branch_readiness`는 producer projection을 같은 lock·generation·row identity로 읽는다. 신원 불일치/소스 부족은 UNKNOWN이며 현재/직전/다른 branch 값을 채우지 않는다. 진단을 위해 State를 다시 observe하거나 root/ready/claim/deadline을 변경하지 않는다.
- side/qty·60/120초 window·session 결손과, 해당 branch에서 사용하지 않는 특징·root 부재·pending 확인을 구분한다. 진단에 새 raw 버퍼·틱별 전체 JSON 복사·파일 hash/전체 prefix 재계산을 넣지 않는다. 기존 저장 영수증에 최종 scalar/ref만 추가하고 비교 원장을 다시 생성하지 않는다.

**종료 기준:** 실제 확인 event에 쓰인 값과 same-sequence 진단이 일치한다. 042370·111770의 session 결손은 숨기지 않으며, 정상 dd가 base 캐시에 없다는 이유만으로 결손이라고 표시하지 않는다. source/quote/branch truth·확인 ask·hit/claim은 진단 보완 전후 동일하고, phase가 다른 수치로 맞춘 parity는 실패다.

### 9.5 N3 — 패턴 미충족과 원천 결손 분리

**owner:** probe result producer, discovery queue/runtime, scanner receipt, Main attach, sentinel/보고서/장후 source-quality 독자다. 실제 consumer allowlist와 schema/version을 구현 전 N0에서 조사한다.

- 새 result 계약에 `pattern_not_matched`를 추가한다. 관측된 native lifecycle에서 필요한 source가 유효하고, 실제 root/필터의 결정적인 FALSE로 적격 신호가 없었던 경우다. **종료 직전의 all-FALSE 한 장이나 base 특징 캐시만으로 관측시간 전체가 정상이라고 확정하지 않는다.** root 부재로 사용하지 않은 특징은 별도 availability이며 그 때문에 결정적인 root FALSE를 결손으로 뒤집지 않는다.
- `required_feature_insufficient`는 실제 평가에 필요한 anchor/rolling/qty/side 등이 부족해 UNKNOWN인 경우다. source identity·stale/conflict·receipt 결손은 `source_unavailable`이다. 진행 중에는 기존 `lease_phase=observing`을 유지하고, 값은 있으나 확인 window/관측이 원 deadline에 끝나 미확정인 경우는 새 terminal `observation_incomplete`와 정확한 pending/censored 이유로 남긴다. 슬롯 admission 중단은 기존 `probe_capacity_deferred`다. 현재 `RESULTS`에는 pending/censored terminal이 없으므로 이름만 표시하고 consumer 연결을 생략하지 않는다. 관측 종료를 임의의 machine BLOCK으로 만들지 않는다.
- 같은 branch에서 known FALSE와 별도 특징 결손이 함께 있으면 실제 ternary 결과를 보존하고 결손 진단을 따로 기록한다. 정상 no-root/FALSE, UNKNOWN 및 source guard를 배타적인 원인 하나로 억지 압축하지 않는다. branch별 사실과 union 결과를 함께 대사한다.
- queue `RESULTS`·`resolve`·restore·runtime `drain_results`·재평가 간격·scanner emit·Main attach·funnel/source alert·장후 reader까지 같은 result version을 지원한다. `pattern_not_matched`/`observation_incomplete`는 해당 기존 관측 종료의60초 재평가 간격을 유지하며, `assessed + ENTER_NOW`만 기존 편입 경로로 간다. 새 결과가 allowlist에서 조용히 버려지거나 slot/lease를 남기면 실패다.
- 과거 raw의 원 result/reason을 수정하지 않는다. reader의 명시적 legacy projection에서 원 reason과 **증거로 확정한 범위**만 재분류한다. 근거 부족은 unobservable이며 최신 queue 상태111/57를 전체 시도·주문/놓친 WIN 수로 재집계하지 않는다. quiet/stale 체결이 자동 API 장애·보강 요청 폭증으로 이어지지 않게 한다.

**종료 기준:** 정상 no-match는 source-gap 경고에서 빠지지만 실제 필수 특징·시각/신원 결손은 계속 드러난다. 구/신 result의 읽기·재기동·slot 해제·retry·Main 소비를 검증하고 old raw·machine action·주문 authority는 보존한다.

### 9.6 N4 — 기존 관측시간 안에서 체결 대기 방식 개선

**owner:** 기존 `wait_for_exact_probe_ws_data`/probe worker와 Main의 observation profile·scanner residence 예약이다. 슬롯5/long2, 원60/150초의 absolute lease와 단일 REG/REMOVE 소유권을 유지한다.

1. REG/실제 lease 시작·첫 exact0B/0D·5번째0B·source-ready·native root/확인·machine 시작/종료·release/해제 clock을 같은 claim/source generation·physical lease에 결속한다. local REG send는 broker ACK가 아니며 무체결 구간의 거래 존재를 가정하지 않는다.
2. 정규장15초는 초기 source **점검 시점**으로 사용한다. 일부 유효한 exact0B/0D 도착이 있고 source-ready 및 선택 branch의 남은 필수 관측이 원 lease 안에 가능하면, 같은 등록·같은 deadline 안에서 event-driven 수신 대기를 이어간다. 새 lease/claim, REG 재전송, 대기 연장을 위한 REST/AI, deadline reset은 하지 않는다. source-ready 이후의 기존 필수 source 준비/확인 시점 refresh는 정규 경로대로 수행하며 도달 표본 증가에 따른 호출량과 추가 조회 루프를 구분한다. 완전 무수신의 기존10초 조기 반환과 session별 empty/partial 계약은 보존한다.
3. 원천이 늦게 도착하면 이미 관측된 실제 native 구간과 남은 시간을 계산한다. 첫 데이터가 준비됐다는 이유로60/120초 history를 새로 만들어내거나 warmup clock을 다시 시작하지 않는다. 어떤 선택 branch도 남은 구간에 확인할 수 없으면 feature-window/censored 사유를 남기고 해제한다. 처음 partial이 있다고 무조건150초를 점유하지 않는다.
4. exact item/route/epoch·0B/0D3초 최신성·최소 exact0B5건·native5초·계좌/주문/수량·hard safety를 유지한다. 처음 source를 기다리는 동안은 관측만 가능하며 stale 입력으로 REST source 준비·기계/AI/진입을 앞당기지 않는다. ready 이후 native 확인이 발생하면 **확인 event epoch+5초**를 원 계산/보조/Main에 전달하며 residence deadline을 진입 deadline으로 쓰지 않는다.
5. 기존 메모리 notifier/waiter를 사용하고 수신 이벤트 또는 bounded 종료 확인에만 snapshot을 읽는다. 초기50ms polling을150초 내내 반복하지 않는다. 취소/rollover·reconnect·consumer/policy generation 변화·source 충돌이면 기존 경로로 종료한다. cleanup 완료 여부·shared/borrowed owner·REMOVE 권한과 capacity ACK를 보존한다.
6. 더 오래 점유하는 candidate로 fresh 미관측 후보가 굶지 않도록 기존 oldest-claim 순환과 long admission을 함께 검증한다. quiet/partial/충분 수신·혼합 long/short를 같은 candidate 유입·원천 시각·슬롯에서 비교해 source-ready/native 확인·기계 계산 도달, 점유초/큐 대기·미관측/기한경과·CPU/RSS·저장 증가를 공개한다. 개선이 없거나 전체 감시/보유/청산 처리 회귀가 있으면 N4의 대기 변경만 보완/철회하고 N1~N3의 결함 수리를 부정하지 않는다.

**종료 기준:** 15초 이후·원 deadline 이전에 실제 수신이 충족되는 fixture는 기존 guard를 통과한 뒤 native 탐지/기계 계산 경로로 진행한다. 계속 무체결/희소·stale인 fixture는 통과하지 않고 원 시각에 종료하며 slot/lease 해제가 닫힌다. 이는 계산 연결의 계약 검증이고 특정 종목의 ENTER/PASS/주문/수익을 성공 조건으로 삼지 않는다.

### 9.7 N0·버전 전환·원장/성능 검증

N0는 실행 때 선택 release·실제 PID/start/cwd·bundle/family/registry·source generation과 코드 SHA를 다시 고정한다. 기존 source tail/집계와 작은 frozen fixture로 N1~N4의 전후를 비교하고, 누적 시장 원장 전체를 구현할 때마다 복제하지 않는다. 최초 기준값·진단 scalar/ref·종료 receipt는 기존 저장 owner에만 결속한다. read-only 점검은 파일당16MiB 이하 bounded read를 사용한다. 단일 단계의 작은 격리 fixture는 한 process·CPU60초/wall120초·RSS512MiB, 새 임시 근거 총64MiB를 기본 상한으로 고정하고 실제 결합 측정은 §11의480/600초·2GiB 계약으로 별도 수행한다. source/index의 신규 예상 bytes/stream·실제 stream 수·일별 증가·필수 writer 수는 실행 전 storage manifest에 고정하며 anchor는 최초 관측/검증된 수리 때만 기록하고 틱마다 저장하지 않는다. 기존 필수 raw 저장량과 신규 metadata/fixture 증가량을 각각 측정한다. 예산이 모자라면 해당 offline 측정/새 migration을 중단하고 미완료로 보고하며, 실시간 필수 append를 줄이거나 원 증빙을 지워 PASS하지 않는다.

State/dispatcher/anchor 코드가 `contract_modules()` pin에 들어 있으면 기존 d906/v6의 `contract_file_sha256`을 덮어쓰지 않는다. **리뷰한 source 수리 코드와 등록 변경을 구별한 successor 실행 세대**, immutable parent attestation·loader/backend/reader 지원·manifest/compatibility receipt로 전달한다. catalog definition/membership을 그대로 유지하는 code 수리라도 session의 실제 UNKNOWN이 해소될 수 있으므로 ‘신호 의미/분포 전부 동일’인 변경으로 허위 인증하지 않는다. 이미 anchor가 완전한 입력은 native 의미 parity, 실제 결손이 수리된 입력은 source ref와 의도된 truth/hit delta를 각각 검증한다.

§3의 P1두scope restriction은 **membership 변경**에 적용한다. 공통 source 수리로 비대상scope의 계산 가능성이 회복되는 효과는 별도 source/코드 delta이며 적용 범위·영향·rollback을 공개한다. 과거 수리 불가능 원천 전부 복구, 실제 WIN/주문, 보조 비교 완료, 새 EV floor를 수리/지정 등록의 추가 gate로 만들지 않는다. code/schema/guard·source provenance 검증과 성능/저장 무손실 검증은 실제 배포 준비의 필수 조건이다.

## 10. 구현 순서·역할 경계

| 단계 | 직접 owner/위치 | 구체 산출물 | 종료 기준 |
|---|---|---|---|
| I0 | scalping 연구 인계/registration | P1 batch·parent pin·exact delta·원 정의 hash·archive | 신규4정의/2remove/2scope 일치; 원 연구 view와 정책 수 구분 |
| I1 | existing catalog/state/runtime/auxiliary/readiness | dependency closure·successor registry·확인 event 필터·A08·typed proof/reader | 원 FSM/확인점/ask parity; F 단독 재신호0; optional UNKNOWN/계약 오류 분리 |
| I2 | existing manual registration/policy loader | batch archive·ADD/REPLACE 승인 계보·consumed/superseded·pointer CAS | 이전ADD 재적용0; add_present/remove_absent·발행 receipt 일치 |
| I3 | operating postclose/보조 v6 분기/evaluation/publisher | 고정 variant 비교·위임 selector·effective binding·초기 designated publish | 추천→선택 membership→machine/auxiliary bundle 연결; 초기/재생 metrics 분리 |
| I4(병행) | source producer/quality consumer | epoch 첫 단절·isolated 보완 또는 잔여gap | 확인된 역사 proof만 사용; 원천 수집 확대0; 과거 결손이 지정 채택의 추가 gate가 되지 않음 |
| N0→N1→N2→N3→N4 | §9.2–§9.7의 기존 source/State/diagnostics/probe/queue owner | 현재 기준 pin·stream anchor·same-sequence 특징 projection·result 계약·lease 안의 대기 | 각 단계 종료 기준·구/신 reader·pinned successor·전체 작업량/slot/저장 parity 확인; N4 대기 변경과 N1~N3 수리를 별도 판정 |
| I5 | deployment infrastructure/Main loader | immutable release·bootstrap/preparation/selection·startup receipt | 정확 release/target/bundle/registry·actual PID/start/cwd 분리 검증 |
| I6 | existing natural-acceptance/postclose owner | typed signal·AI/Main·intent/submit/terminal·후속 결과 | 신호 없음=pending, source gap/거절/실주문/손익을 각각 표기 |

N0~N3은 I0/I1의 source·execution version 설계와 먼저 결속하고 N4는 그 유효 원천/진단/result 계약 위에서 검증한다. I2 등록 및 I3 발행의 실행 세대에는 완료한 N 단계와 명시적으로 carry한 기존 대기 disposition을 반영한다. 코드 수정 전에 낡은 code hash로 새 bundle을 발행하거나 I5 배포 후 N 단계의 필수 reader를 뒤늦게 붙이는 순서를 허용하지 않는다. 과거 원천 수리 I4는 이 현재 runtime 연결 수리와 구분해 병행한다.

기본 적용 방식은 승인된 전체 구현·리뷰 후 **다음 운영 세션**이다. `publication_date`와 target은 실행 시 기존 calendar/`next_target` owner로 산출한다. 오늘 장중 적용을 별도로 지시하면 기존 ordered deployment·exact-date handoff/activation을 사용하며 env/pointer 수동 수정은 하지 않는다.

신규 파일이 꼭 필요하면 location gate를 거쳐 `src/engine/scalping`의 등록/평가 역할 또는 `src/tests`를 선택한다. 기존 `reversal_manual_registration`, catalog/state/evaluation/operating producer를 우선 사용하고 engine-root 신규 모듈·별도 cron/timer/worker·중복 report producer를 만들지 않는다. 실제 automation 변경 시 owning runbook과 당일 stable owner를 같은 change set으로 갱신한다. 현재 계획 작업은 sealed checklist·baseline 문서를 편집하지 않는다.

## 11. 테스트·성능·stop 조건

### 의미·source·등록 회귀

- N1: 다른 종목의 원천이 있는 날짜의 새 stream, 이전 관측 없음/실제 첫 source ref, 알려진 원 anchor 유실·무효·중복/충돌, restart/재등록/가격대 이동·세션/route/day 분리, 복원 뒤 캐시 무효화·재발행0을 검사한다. 무효 stream이 과거 부분값·현재가로 채워지면 실패다.
- N2/N3: 실제 branch/phase별 dd/volume·optional F·same-row projection, 실제 session 결손과 진단 캐시 누락의 분리, no-root/FALSE/UNKNOWN/pending/stale/계약 오류, legacy raw 유지·새 result 전체 allowlist/restore/retry/해제를 검사한다. 진단/분류만 바꾼 fixture는 실제 신호·claim·action/주문 효과가 같아야 한다.
- N4: exact 데이터0건·0D만 도착·5번째0B가15초 이후 도착·늦어 남은 필수 window 불가능·원 deadline 경계·기존 borrowed lease/REMOVE·generation/transport 교체·취소/rollover를 검사한다. 각 fixture의 기계 계산 호출 수와 원5초 전달, REST/Provider/REG 수·slot/cleanup clock을 대조한다. 프로토콜/요청 흐름 변경이 필요하면 구현 전에 공식 Kiwoom reference gate를 수행한다.
- frozen25개 가설 중 P1 정확 정의와 실제 native engine 결과의 canonical 확인점/ask/feature/라벨 일치. 원 branch clone, 현재 원본/보완/추가/실제OR를 같은 입력에서 비교한다.
- UNKNOWN 진리표 전체, 원 predicate false/unknown, 부분 조건 known FALSE＋다른 특징 UNKNOWN, 원 session anchor 미관측/재기동, qty/side 불명, epoch/route/item/source gap·stale/future를 검사한다.
- F FALSE 확인 후 F만 TRUE로 바뀌는 tick은 신호0, 다음 정상 원 확인에는 F 재평가1회다. FIRST 특징과 CONFIRMED 특징이 달라지는 fixture에서도 원 predicate·확인 ask를 보존한다. optional 값 부족과 definition/phase/hash/source binding 오류를 다른 결과로 검증한다.
- 같은 tick의 원형＋다른 carry branch＋A08 중복, independent rising root without FIRST, base FIRST 무효화와 A08 생존, source gap/reset·native deadline/claim·late/duplicate response·single intent를 검사한다.
- 실제2scope delta, 동일 원 branch의 다른scope, 2만원/10만원 경계, 상시/비상시·cold/warm source를 검사한다. 비대상scope의 정책 의미와 원 안전/custody 결과를 바꾸지 않는다.
- registry ancestry/승인 정의별 linkage, old ADD pending/consumed, partial write·CAS drift·target rollover·중복 실행·선택/carry/rollback과 relative source path를 검사한다.
- dependency로만 남긴 원 branch의 runtime proof는 계산되지만 OR/AI/intent 기여0이다. 새 registry에 기존6개 ID가 없는 scope도 동일 generation을 해석하며 phase/production request/readiness dispatch 누락0을 확인한다. BUY10의9개 known＋1개 unknown은 UNKNOWN이고 더 과거 체결로 보충하지 않는다.
- ret60=0·DD=0.4·BUY10=60·vwap60=0·session_return=0.4와 바로 양옆의 값, 시간 경계 predecessor/동일시각 sequence·직전 최고가와 같은 값/엄격 돌파를 검사한다. 계산 순서 차이가 조건/확인점을 바꾸면 수리 또는 새 계산 결과를 명시하고 old parity PASS를 재사용하지 않는다.
- v1·새 batch 동시 보존, add_present지만 remove가 남은 부분 변경, rollback 뒤 오래된 pending, v6 보조 tuning 활성/비활성, effective overlay carry, 초기 metadata-only report와 실제 새 재생, 비교0/불완전 시 적용 중 JOINT carry를 검사한다. 두scope 선정 결과와 staged payload IDs/hash가 같아야 한다.
- typed auxiliary source/input/response·consumer·reader readiness 및 원request/generation/cache hash·공유5초를 검증한다. 합성 신호가 validator를 통과하려고 fictitious FIRST/price proof를 넣으면 실패다.
- 정책·프롬프트의 원 source/label과 심리·리서치·Provider 요청 namespace를 분리한다. source/API/Provider를 호출하지 않는 frozen fixture와 기존 관련 회귀를 사용한다. 실제 live wire 변경은 별도 공식 reference gate다.

우선 확장할 기존 테스트 owner는 [extended policy](../../src/tests/test_reversal_extended_policy.py), [manual registration](../../src/tests/test_reversal_manual_registration.py), [v6 보조 tuning](../../src/tests/test_reversal_auxiliary_tuning.py), [native claim/source diagnostics](../../src/tests/test_native_signal_claim_diagnostics.py), [보조 reader readiness](../../src/tests/test_auxiliary_reader_readiness.py)다. 새 root/test 모듈을 일괄 생성하지 않고 실제 변경 producer/consumer의 계약에 맞춰 해당 fixture를 확장한다. 아래 성능 측정과 구분해 테스트 수만으로 전체 Main 성능/자연 수용을 완료 처리하지 않는다.

### 성능과 완전한 작업량

현재 승인 parent/code와 후보의 같은 frozen source에 대해 baseline/candidate를3회 교대로 비교한다. 원래 대상/유효 tick·판정·필수 append·carry branch 수를 보존한다. P1 신규4정의의 hit와 N1/N4로 실제 source 준비·탐지가 회복되는 hit를 구분해 세며, 진단/분류만 바꾸는 N2/N3은 hit delta0이다. N1이 허용된 실제 첫 source로 결손을 해결한 변화는 원 의미 위반과 구분하고 ref로 증명한다. 입력을 누락해 빨라진 결과는 실패다. 기동 warmup과 steady-state를 분리한다.

측정은 detection/feature/typed normalization·Main handoff/commit의 p50/p95/p99/max, 원5초 miss, source gap·정상/UNKNOWN·claim/AI/intent 수, 프로세스 CPU·RSS·부하·bytes/append 및 기존 queue/slot 상한이다. 한 offline process/계산thread·nice19·주소공간2GiB·파티션별CPU480초/wall600초를 기본 상한으로 사용한다.

hot path에 새 file read/DB·전일 원장 decode·Provider/REST 사전 조회·구독·thread·전체 rolling 반복 계산을 넣지 않는다. 새 정상 신호로 인한 AI 수요는 기존 budget/queue에 귀속하고 packet마다 새 AI를 호출하지 않는다. 같은 fixture의 기존 branch와 guard 결과/원5초 적시 소비가 나빠지거나 입력/필수 저장 누락·자원/물리 상한 위반·stale/unknown의 TRUE 승격이 있으면 배포 전 수리한다. 수치 기준은 현재 local stage의 원 예산/기준 receipt로 구현 시작 때 freeze하며 본 계획을 실측 성능 PASS로 쓰지 않는다.

실행 프로토콜은 후보 측정 전에 workload manifest·baseline 환경·자원 상한·판정 기준을 고정한다. native replay와 Main 통합 fixture를 분리해 수행한다. replay에서는 P1의 의도된 membership/hit delta를 허용하고, 통합 fixture는 동일 원천·제공된 신호·기록된 보조 응답/지연·필수 저장을 사용해 처리 비용과 guard 회귀를 비교한다. 기회가 줄어든 정책을 전체 소요시간만으로 성능 개선이라고 표시하지 않는다.

통합 fixture에는 상시/비상시 감시 혼합, 복수 hit·UNKNOWN·cold/warm source, 기존 보유/청산·completion·필수 writer 작업을 포함한다. 측정하는 작업이 빠지면 censored/불완전이다. 기존 [공유 deadline 보완계획](main-entry-auxiliary-shared-deadline-latency-remediation-plan-2026-10-13.md)의 동일 입력 교대 측정과 회귀 한계를 따른다. 보유/청산/completion p95 또는 전체 loop p95·CPU/RSS가 baseline보다10%를 넘게 악화하면 원인을 수리하고 재검증한다. 원5초 연장·중복 claim/intent·필수 write 손실은 수치와 무관하게 실패다. 새 정책 채택에 local p95 개선20% 같은 새 성능 향상 floor를 만들지 않는다. 자연 새 신호의 AI 수요 증가는 처리 비용 회귀와 구분해 기존 queue/예산 내에서 보고한다.

## 12. 배포·기동·rollback

1. 구현→self review→수정보완→재리뷰→표적 테스트/compile·bash/contract(해당 wrapper 변경 시)·diff/문서 parser로 코드 gate를 닫는다.
2. code·registry·candidate batch·policy 및 원/source/reader receipts를 같은 reviewed immutable release에 결속한다. 초깃값 수동 env/lock/provider/broker guard 조정은 없다.
3. 기존 native machine/auxiliary stage로 operator-designated P1 bundle을 준비한다. 초기 등록은 provider 비교 PASS나 실현 수익을 가정하지 않는다. membership은 P1두scope만 변경됐는지 exact manifest diff와 family validator로 확인하고, N1~N4의 공통 source/코드/result delta와 영향을 별도로 검증한다. 원 anchor index·구/신 결과 독자·pinned 실행 세대·보조 reader 증빙이 준비돼야 한다.
4. 기존 ordered release/PREOPEN preparation을 재생성/검증한다. code compatibility·policy provenance·날짜/receipt bytes 변경에 맞는 handoff를 만든다. 이전 strict/DONE 영수증을 새 세대의 성공으로 재사용하지 않는다.
5. 승인된 적용 시점에 native selector/activation·Main 기동을 실행하고 실제 PID/start/cwd·bundle/registry/scope payload를 확인한다. 준비 성공만으로 정상 소비라고 표시하지 않는다.
6. 자연 신호에서 독립 A08/합성 F의 각 output, original proof/refinement receipt, `ENTER_NOW→보조결과→Main disposition→intent→submit→terminal`을 분리 대사한다. PASS 또는 actor 실행0을 broker 실패0/수익으로 대체하지 않는다.

generation 전환은 기존 runtime configure/claim validator가 소유한다. 새 hash와 맞지 않는 old FSM/claim·늦은 AI 응답을 새 membership으로 해석하거나 다시 주문하지 않는다. same-input cache라도 branch membership·definition/refinement proof·effective 보조 binding이 달라지면 새 request identity다. 영향을 받은 scope의 정상 warmup/source 부족과 계약 오류를 분리하고, 전환을 이유로 기존 broker 주문·체결·보유 owner를 바꾸지 않는다. 모든 scope의 기존 state가 무조건 유지된다고 보장하지 않고 execution hash 변경에 따른 실제 재설정 범위를 보고한다.

rollback은 **호환되는 code＋registry＋policy bundle＋날짜/approval/PREOPEN receipt의 짝**을 기존 native path로 되돌리는 절차다. 원4/2 membership과 reader compatibility를 보존해 원본 variant를 복구한다. journal/custody·pending broker order·이미 체결된 포지션·실제 손익을 삭제하거나 이전 snapshot으로 되감지 않는다. 다른 세션의 승인 변경이 진행됐다면 stale parent로 넓게 rollback하지 않고 새로운 CAS의 해당scope successor disposition을 준비한다. retired widget/episode executors를 복구하지 않는다.

적용 날짜가 달라졌으면 원 d906의 과거 날짜 env/activation/PID receipt를 그대로 복사하지 않고 현재 target에 유효한 rollback successor/preparation을 만든다. 정책 변경으로 현재 주문을 자동 취소하거나 포지션을 강제 청산하지 않는다.

N4의 대기 변경은 N1~N3의 수리 및 정책 membership과 구분한 선택/rollback 영수증을 갖는다. 이미 기록된 실제 최초 anchor·raw/result 이력은 rollback으로 삭제하거나 새 가격으로 덮어쓰지 않는다. 이전 reader가 새 schema를 해석하지 못하면 검증된 호환 successor를 사용하며 새 결과를 버리는 구 code/새 data 조합을 기동하지 않는다. 자연 확인은 source-ready→native 확인→machine call/assessed→기존 편입/AI/Main 소비를 같은 claim/lease/epoch/sequence로 연결한다. 반복적으로 마지막 source 값만 없으면 pending/source gap이며 자동 ENTER를 만들지 않는다.

## 13. 계획 완료·인계

이번 산출물은 구현 가능한 **P1 두scope의 신규4정의·remove2개, TRUE/FALSE/UNKNOWN의3값 의미, 등록 계보/REPLACE, 장후 variant 선택·초기 채택, N1~N4 비상시감시 원천·진단·분류·대기 수리, 검증·배포·rollback** 계획이다. 모델/원5초/quantity/broker/custody·retired boundaries의 변경 권한은 만들지 않았다.

구현 종료는 I0~I3 및 N0~N4의 계약·실제 분기 연결, §11의 회귀/성능, I5의 승인된 적용 준비까지 정확한 산출물로 판정한다. I4는 복구 또는 증빙 있는 제외의 disposition을 남긴다. N4를 보완/철회하는 경우 그 명시적 disposition과 안전한 기존 wait carry를 남기고 전체 대기 개선 완료라고 표시하지 않는다. I6의 자연 신호/주문/손익은 별도 관측이며 신호를 만들기 위한 호출·주문을 하지 않는다. 계획 리뷰 완료, 코드 리뷰 완료, 지정 선택/발행, 다음 세션 준비, PID 소비, 자연 성능을 하나의 완료 상태로 합치지 않는다.

실제 실행의 policy handoff는 당일 `DirectFamilyPreopenPolicyHandoff`, source/등록 자연 수용은 `NonfixedDispatchReadinessReview1012`의 기존 owner에 필요한 새 범위로 결속한다. 이 문서의 리뷰 완료는 해당 OPEN 작업이나 실운영 적용을 완료 처리하지 않는다. source/data/PID 상태는 실행 시점에 다시 확인한다.

현재 두 owner는10/13 PREOPEN07:35~08:05와 INTRADAY07:55~08:15의 당일 OPEN 항목이다. 다음 세션 구현을 이 과거 TimeWindow의 권한/완료로 취급하지 않는다. 실행 지시 후 해당 실제 대상일 checklist로 stable ID·Acceptance/History를 유지해 연결하고 한 현재 parsed owner를 확인한다.

## 14. 계획 리뷰·검증 결과

리뷰에서 ADD 전용 intake, 기존6개 승인에 마지막 change를 고정한 validator, 단순AND가 UNKNOWN을 원 신호 거절로 바꾸는 문제, old branch OR 유지로 F 효과가 사라지는 문제, 추천만 남기는 장후 소비, 원천 epoch의 허용 목록 불일치와 날짜/rollback 과거 영수증 재사용 위험을 확인해 설계에 반영했다.

P1 두scope의 원 branch·A08 정의와 연구 JSON이 일치하고 before4→after5·before2→after3 membership을 대사했다. 날짜 제외 진단과 실제10/12 source/후보 수치를 별도 evidence로 보존했다. **1차 검증에서** 로컬 링크9개·owner/authority/공백·`git diff --check` 및 print-only parser23항목을 확인했다. 문서 계획 작업이므로 거래/Python 구현 회귀·Provider 호출·비싼 보고서 재생성·새 정책 선택/배포/PID 검증은 실행하지 않았다. 원19개 테스트·102개 라벨 재검증은 연구의 영수증이며 이번 후속 구현 PASS로 이전하지 않는다.

### 2차 리뷰의 구체 보완

| 확인한 누락/모호함 | 수정 위치 | 후속 구현의 종료 검증 |
|---|---|---|
| F를 원 조건과 AND한 새 transition으로 구현하면 연구에 없는 확인점을 생성할 수 있음 | §5.1 | 원 확인점에서1회 필터; F만 변한 tick의 신호0; FIRST/CONFIRMED 특징 분리 |
| removed 원본을 catalog에만 보존하면 내부 FSM·phase 의존성이 누락될 수 있음 | §3·§6 | dependency/operating 분리; registry·State·typed request·readiness 전 경로 해석 |
| optional UNKNOWN을 계약 오류에도 적용할 여지와 BUY10의 알려진 체결만 취하는 모호함 | §5.2·§6 | binding 오류 차단; 연속10개 모두 검증; 원 source UNKNOWN 승격0 |
| 단일 pending 파일과 add-only 완료 판정으로 후속 REPLACE/rollback이 충돌하거나 재적용될 수 있음 | §7.1 | 불변 batch·pointer CAS·remove_absent·consumed 발행 계보; 오래된 pending 재적용0 |
| v6의 실제 보조 장후 분기가 parent machine을 복사해 F 선택이 발행에서 사라질 수 있음 | §4·§8.1 | 선정 machine IDs가 staged payload와 일치; effective 보조 binding carry·초기 지정 분리 |
| 초기 metadata-only 보고서/교집합 분모를 실제 새 정책 누적 성능으로 오해할 수 있음 | §8.1 | 실제 날짜/전체 source universe·각 variant 기회 분모·새 재생 generation 구분 |
| 과거 source 전부 복구를 초기 적용 선행 gate로 해석할 수 있음 | §9·§10 | 복구/증빙 있는 제외로 병행 종료; 적용 시점 source guard 유지 |
| 정책 hit 감소·빠진 Main 작업으로 성능 PASS를 주장하거나 전환 상태를 과대 보장할 수 있음 | §11·§12 | 같은 통합 workload·기존10% 회귀 한계·원5초·필수 저장·generation 검증 |

2차 리뷰의 문서 검증 결과는 [리뷰 영수증](../../tmp/main-machine-joint-research-20261013/operating-plan-review-validation.json)에 기록한다. 위 표는 설계 보완과 **후속 구현에서 실행할 검증**이며 현재 코드의 결함 수리/테스트 통과를 뜻하지 않는다. P1 범위·연구 수치·P2 선택지·성공100%/80% 보존 gate 제거는 유지한다. 남은 코드 변경은 이 계획의 구현 단계이며 현재 요청에서는 실행하지 않는다.

### 3차 리뷰 — 비상시감시 연결 수리와 기존 계획의 충돌 보완

| 확인한 누락/충돌 | 보완 위치 | 후속 종료 검증 |
|---|---|---|
| cold source UNKNOWN만 유지하면 합법적인 최초 관측 기록 결함도 영구 방치됨 | §6·§9.3 | 신규 stream 첫 source ref와 이전 관측 유실을 분리; 기존 anchor 보존·restart 복원 |
| dd 캐시 결손을 수리하며 원 phase의 low-based/confirmation-based 값을 덮어쓸 위험 | §9.4 | branch/phase·epoch/sequence별 실제 값 parity; 진단-only hit delta0 |
| 최신 all-FALSE/no-match를 특징 충분/전체 구간 정상으로 과대 판정하거나 새 result를 consumer가 버림 | §9.5·§11 | 실제 lifecycle/필수 특징/결정적 FALSE 구분·구/신 reader와 retry/slot 해제 |
| 15초 원천 대기를 늘리며 총 lease·native5초·최신성/물리 슬롯을 바꾸거나 후보가 굶음 | §9.6·§11 | partial/empty·원 deadline·60/150·5/2·전체 candidate/workload·cleanup/저장 비교 |
| P1두scope 외 코드 수리를 membership 확대 또는 완전 parity로 오해함 | §9.7·§11·§12 | membership/공통 source-code delta 분리·완전 입력 parity/결손 회복 별도 증빙 |
| pinned State/anchor 변경을 기존 family hash에 덮어쓰거나 rollback에서 source 이력을 잃음 | §9.7·§12 | successor pin/loader/reader·원 ref 보존·구 code/새 schema 소비 차단 |

3차 리뷰의 문서 검증은 [보완계획 검증 영수증](../../tmp/nonfixed-source-pattern-machine-check-20261013/plan-review-validation.json)에 기록한다. 이번 변경의 실행 권한은 계획 작성·리뷰·parser 검증이며 코드 변경·새 Provider 호출·원장/장후 재생성·등록·배포·재기동을 수행하지 않는다. 600초 격리 재현과 이전 PID 기록은 설계 근거이지 이 계획의 후속 구현/운영 PASS가 아니다.

문서 검증은 로컬 링크27개, 현재 checklist의 두 기존 stable owner 각각1개, print-only parser23항목, 공백·`git diff --check` 및 untracked 계획 본문의 별도 diff 검사를 통과했다. Plan Rebase와 sealed checklist는 수정하지 않았고 다른 미커밋 작업본을 보존했다. 거래/회귀/성능 테스트는 후속 구현 단계이며 이번 계획 검증에 합산하지 않는다.

사용자 실행용 표준 동기화 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 15. 구현 실행과 반복 리뷰 결과 — 10/13

[구현 리뷰](../audits/main-joint-operating-and-source-repair-implementation-review-2026-10-13.md)와 [준비 인계 검증](../../tmp/joint-operating-implementation-20261013/next-session-prepared-validation.json)이 현재 결과다. P1 exact2scope의 신규4정의·remove2개, dependency/F/독립 A08·등록 승인 계보·장후 승인 variant selector·N1~N4를 구현했다. 리뷰에서는 원 필수 UNKNOWN의 합성 전달, 제거 dependency의 재신호, 원 확인값/진단 캐시, 승인 조합 전체의 기회 탐지와 분모, 보조 튜닝의 선택 목록 덮어쓰기, archive의 연구 result 연결, 미완료 복원 재개·late anchor의 union 전달·index write coalescing을 추가 수리했다.

13:54:55 주성 timeout은 pre-provider1.546초·경제성775ms·HTTP lock0ms였다. policy snapshot 반복 body를 warm owner의 불변 component/file parts와 참조로 바꾸고 clone/capacity/guard/freeze/plan/append의 세부 clock을 연결했다. 원5초·모델·HTTP/회로·quote/quantity/order/custody는 그대로다. 저장 reader는 정확 원 snapshot/버전을 복원하며 누락/변조를 source gap으로 처리한다. 참조 index/parts는 replay/정책/rollback ref census 없이 삭제하지 않는다.

최종 표적317건·clock/replay244건·source 복원53건을 통과했으며 중복 합산하지 않는다. 고정128경로·76,800틱의 기존614확인은 SHA까지 같았다. 3회 교대 detector wall은 약5.6% 증가, 좁은 문맥 encoding은736KB→110KB·약5.9→2.0ms다. 전체 Main 혼합/보유/청산/completion·writer/실제 Provider의 시간 분포와 원5초 timeout 감소는 아직 미검증이다. 좁은 측정으로 전체 성능 PASS를 만들지 않는다.

P1은 request `8d624a14...`로 등록됐고10/14 작업본 후보 `eed8b828...` 및 기계/보조 component를 실제 준비했다. comparison_complete=false·Provider0이며 초기 지정 채택을 새 비교 gate로 바꾸지 않았다. I4는545,254개 identifiable unverified epoch 행의 원 제외를 유지하는 [disposition](../../tmp/joint-operating-implementation-20261013/historical-epoch-disposition.json)으로 종료한다.

최종 reviewed immutable release의 commit/code/reader에 재결속→native strict/PREOPEN→승인된 배포/재기동→새 PID/자연 수용은 후속 단계다. 현재 작업본 후보를 이미 배포된 정책으로 해석하지 않는다. 원 d906 current pointer·선택 v7는 유지하며 §14의 계획-only 실행 경계는 그 당시 역사로 보존한다.
