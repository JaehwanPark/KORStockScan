# 삼성전자 연속 tick 구간의 매수압력 전환 — 추가연구 실행계획

작성일: 2026-10-05 KST. 상태: **실행 완료, 전체 origin의1틱 이동 후보1개를 이후 날짜 검증용으로 동결**. 상시감시 전용 개선과 운영 적용은 미입증이다. [실행·검증 결과](../audits/samsung-continuous-tick-transition-research-review-2026-10-05.md)를 따른다. 계획 작성 단계의 fixture 보완은 별도 [리뷰](../audits/samsung-historical-fixture-review-and-tick-research-planning-2026-10-05.md)에 기록했다.

## 1. 연구 질문과 기존 증거

기존 H2는 직전 기계판정 capture의 매수압력<60에서 현재≥60으로 전환한 경우만 원흡수 ENTER를 유지한다. 전체519관측에서는43건만 조건을 식별했다. 상시감시206건은 모두 미식별이며, 그중193건은 직전 capture 간격이5초를 넘었다. 나머지12건은 직전 capture 부재/현재 receipt 불충족 분기,1건은 직전 receipt 불충족이다. [원인 집계](../../tmp/samsung-kernel-recovery-20261005/H2-source-availability.json).

이는 시장 체결 데이터 전체가 없는지, 판정 capture 단위로만 비교해서 이미 가진 tick을 충분히 소비하지 못했는지 분리해야 하는 근거다. 기존 H2의 추가 개선은9/29 손절1건 제거이며 상시감시 전용 개선은 미입증이다. 기존 연구를 실패로 지우거나 같은 가설의 이름만 바꿔 재탐색하지 않는다.

질문은 하나다. **동일 판정시각 이전의 연속 체결 구간을 쓰면 압력 전환의 식별 가능 범위가 넓어지고, 원흡수 대비 실제 가격경로의 승패 구분도 개선되는가?** 식별률 상승과 성능 개선을 별도로 답한다.

## 2. 고정 범위와 권한

- 종목005930, Main `KRX|KRX_REGULAR`. 전체 origin519관측과 원native가 있는 상시감시206관측을 각각 보고한다.206개를519개에 다시 더하지 않는다.
- 원천 날짜9/29·9/30·10/2는 모두 탐색에 이미 사용됐다. 새 독립 holdout으로 재분류하지 않는다.
- 기존 capture, 보관 체결/호가, 완료 가격, 원 비용·stop·정책·source receipt만 읽는다. API/WS 등록·수집 확대·주문·threshold·수량·custody·runtime 정책 발행은 범위에 없다.
- 비삼성10/6 지정 정책과 Main/Widget/Episode의 실행·준비 owner를 보존한다. 과거 foreign/program veto2개의 검증과 이번 압력 전환 연구를 혼합하지 않는다.
- 원 H2 frozen·원흡수 frozen은 불변이다. 추가 정의는 별도 candidate ID·receipt로 봉인한다. 원 H2의 계산 방법을 소급 변경하지 않는다.

## 3. R0: 원천·커널과 재현 기준 봉인

입력 소유자는 [원 추가연구](samsung-absorption-differential-and-path-research-plan-2026-10-05.md)와 다음 산출물이다.

- `tmp/samsung-absorption-differential-research-20261005/final/observations.json`, `source-manifest.json`, `comparisons.json`, `frozen-candidate.json`.
- `tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json`의 원흡수 후보.
- 기존 연구 request가 지정하는 날짜별 locked-source 체결/호가와 원 machine capture. 경로를 추측하거나 최신 파일로 교체하지 않고 해당 manifest에서 해석한다.
- `entry_flat_buy_flow_research.valid_receipt/historical_receipt`, `entry_admission_analysis.capture_clock`, 원 cost/stop 및 기존 replay kernel.

읽기 전에 파일 크기/물리 SHA·정책 hash·receipt·원천 scope·epoch domain을 봉인하고 읽기 종료 후 재검증한다. 기존519관측의 identity/raw/원행동/label을 대사한다. 현재 시점 경로가 바뀌었으면 같은 SHA의 명시적 보관 사본으로 연결하고 relocation ledger를 남긴다. 요구 SHA를 새 bytes의 SHA로 고치지 않는다.

R0 종료: 같은 원자료를 재현할 수 없으면 원인별 source gap을 기록하고 계산을 멈춘다. 복원할 수 있는 식별된 일부 결손은 행별 격리한다.

## 4. R1: 결과를 보지 않는 구간 가용성 census

각 원판정의 cutoff `T0`에서 현재 원 receipt의10tick을 archive에서 **동일 사건으로** 찾는다. 시각·순서·방향·수량·가격·route/item·archive hash를 비교한다. 매수압력 요약값만 같다는 이유로 같은 구간이라고 간주하지 않는다.

다음 항목을 후보 결과/미래 가격을 읽기 전에 산출한다.

| 구분 | 확인·기록 |
|---|---|
| 원 현재 구간 | 원10tick receipt 유효성, 수량가중 BUY/(BUY+SELL)·순공격 delta 재계산과 원 feature 동일성 |
| 직전 구간 | 필요한11개/20개 체결 존재, 연속 seq, 동일 route·item·epoch, endpoint의 당시 이용 가능성 |
| 시점 | 원판정 이전 event/수신/보관 시각의 의미, 늦게 수신된 tick 배제; 동일 timestamp는 확인된 seq로만 순서 판단 |
| freshness | 원현재 receipt 규칙 유지. 두 구간 endpoint 모두T0에서5초 이내, 원래 더 짧은 유효기간이 있으면 그 조건도 유지 |
| source domain | Main transport epoch와 독립 archive epoch를 동일 숫자로 치환하지 않음. 기존 `_AL/SOR` 보관 원천의 허용 결속만 재사용 |
| 결손 | current_receipt_invalid, current_window_not_exact, prior_ticks_missing, clock_unproven, epoch_or_sequence_gap, prior_endpoint_stale, quantity_or_side_invalid를 각각 기록 |

원현재 receipt가 허용한 구간의 시작·끝 의미를 그대로 사용한다. 예를 들어 기존 historical receipt의5초 규칙은 마지막 tick의 age를 검증하므로 이를 임의로 “20tick 전체가5초 안”이라고 바꾸지 않는다. 구간 길이와 모든 tick의 실제 나이는 추가 진단으로 공개한다.

음수·비정상 수량/가격·알 수 없는 방향, 중복·순서 역전, 합산 수량0은 unknown이다. 누락 tick을 보간하거나 뒤의 tick으로 채우지 않는다. 원본에서 당시 이용 가능성을 확인할 수 없으면 retrospective diagnostic으로만 남기고 새 적격 후보의 입력에서 제외한다.

R1 산출: 전체/상시감시·날짜·원 ENTER/BLOCK/RECHECK별 식별률, 기존 H2 unknown 중 새로 설명 가능한 수, 결손 이유. 아직 수익 개선을 주장하지 않는다.

## 5. R2: 신규 가설 두 개만 사전 고정

현재10tick을 `W0=[n-9,…,n]`, 매수압력 함수는 원 구현과 같은 수량·반올림 규칙을 사용하는 `P(W)`라 한다. 조건은 `P(Wprev)<60` 그리고 `P(W0)>=60`이다.60과10tick·5초를 다시 탐색하지 않는다.

| 후보 ID | 직전 구간 | 연구 의미 |
|---|---|---|
| `absorption_p60_tick_shift1_v1` | `[n-10,…,n-1]`, 현재와9tick 중복 | 마지막1tick의 진입/기존1tick의 이탈로 발생한 압력 전환. 최소11개 체결 필요 |
| `absorption_p60_tick_disjoint10_v1` | `[n-19,…,n-10]`, 현재와 비중복 | 인접한 두10tick 구간 사이 전환. 최소20개 체결 필요 |

기존 정책 B0, 원흡수 A0, 원 H2는 고정 대조군이다. 따라서 최대 **신규2개+대조3개=5개 정책**만 비교한다. shift1의 겹치는 tick을 독립 관측이나 표본 증가로 세지 않는다. 두 후보 조합·다른 pressure/시간대/sector threshold grid를 추가하지 않는다.

원흡수 ENTER에서 새 조건 pass는 ENTER 유지, 알려진 fail은 RECHECK, 새 조건 unknown은 **원흡수 행동 승계**다. 원흡수 BLOCK/RECHECK 및 원 hard/source guard는 보존한다. unknown 행을 분모에서 버려 식별률이나 승률을 높이지 않는다.

기존 H2가 미식별인 행에서 새로운 전환을 찾는 효과와, 기존 H2 식별 행에서 판단이 달라지는 효과를 따로 보고한다. 현재 구간 재구성 불일치를 새 신호로 사용할 수 없다.

## 6. R3: 진입시점 효과와 결과 비교

동일 원관측 집합에서 모든 정책을 계산한다. 이후 최초 신호·같은 watch/date/route의 행동 run과 비중복 점유를 기존 방식으로 재생한다. 원native가 없는 관측은 관측군집 진단이며 native 실거래 기회로 합성하지 않는다.

주 비교는 기존 연구와 같은 진입 ask·비용 계약·순목표/stop·최대60분 완료 가격 경로다.10분 미도달의 이후 가격 사용, stop 이후 반등 배제, 같은 봉 target/stop 순서 불명·경로 중단·장종료 검열을 기존 label대로 유지한다. 새 exit·holding 시간·비용률을 동시에 탐색하지 않는다.

두 패널을 산출한다.

1. 정책별 최초 신호·비중복 점유의 전체 결과: 진입을 건너뛴 효과와 다음 진입시각 이동을 포함한다.
2. 같은 원 사건/원 종료시각의 대조: 진입시각과 필터의 효과를 해석하는 진단이며 첫 패널의 barrier label을 덮어쓰지 않는다.

## 7. 지표·권고·종료 기준

기존 삼성 추가연구의 날짜 동일 가중 **완전 가격경로 비용 후 양수 비율**을 권고 주지표로 고정해 지표 교체 효과를 방지한다. Main의 비용결속 목표/손절 확정 승률은 별도 필수 비교이며 실제 기계정책 선정과 연구 권고를 구분한다. 지표가 충돌하면 둘을 공개하고 운영 우월성으로 결론내리지 않는다.

- 각 arm 완전 경로≥3, 비교 가능한 날짜≥2의 기존 연구 지원 기준을 재사용한다. 전체 origin과 상시감시를 별도로 판정한다.
  - 같은 날짜끼리 비교하기 위해 공통 적격 날짜의 양쪽 결과를 함께 재집계한다. 전체 날짜 집합이 같아야 한다는 조건은 두지 않는다. 후보의 진입 없는 날·미확정은 별도로 공개하고 승률0으로 대체하지 않는다.
- 원흡수 대비 양수 비율 개선과 원천/지원 조건을 충족한 후보 중 하나만 권고한다. 두 후보가 같으면 더 적은 원천으로 같은 결과를 내는 shift1을 선택한다. 순위는 양수 비율 개선 → 양쪽 정의될 때 목표/손절 승률 개선 → 단순성 순서로 사전 고정한다.
- 성공100%/80% 보존율, 고정 coverage 하한, 모든 미확정 해소를 후보 탈락 조건으로 두지 않는다. 잃은 승리·제외된 패배·미확정 이동은 진단에 남긴다.
- 날짜별 제외 분석, 종목 고정 내 watch/episode 중복, 현재 구간 매칭 실패 및 unknown 승계 민감도를 공개한다. 한 날짜/한 사건 효과에 집중되면 `single_event_or_day_sensitive`로 표시한다.
- 개선이 있어도 과거3날짜는 탐색 자료다. `recommend_register_for_forward`까지이며 실전 적격/적용 완료가 아니다. 상시감시에서 비교가 불가능하면 전체 개선을 전용 효과로 이식하지 않는다.

**유한 종료:** R1에서 두 정의 모두 원천으로 식별 불가능하면 `not_identifiable`; 적격 계산에서 개선이 없으면 `no_improvement`; 지원 부족이면 `insufficient_support`; 권고 가능하면 후보1개 동결 후 종료한다. 이번 입력에서 가설·threshold·보유기간을 더 늘리지 않는다.

## 8. 구현 위치와 검토 항목

새 구현이 필요하면 `src/engine/scalping/samsung_continuous_tick_transition_research.py`에 오프라인 연구 역할로 둔다. 대응 test는 `src/tests/test_samsung_continuous_tick_transition_research.py`다. engine root에 추가하지 않는다. 기존 receipt·가격·비용·replay helper를 호출하고 운영 판정 함수를 수정하지 않는다.

필수 회귀: endpoint off-by-one,11/20tick 미만, timestamp 동률과 seq, 미래/늦은 수신, route/item mismatch, epoch 교차·중복·gap, 음수/0합 수량, 원 feature 반올림 일치, source 파일 변경, 원현재 구간 오매칭, unknown/known-fail/원BLOCK, 결과 label을 바꿔도 selector 동일, prefix truncation 동일, date/watch 중복,60분 검열·stop 뒤 반등, 새 정의로 원 frozen 의미 변경 거부.

producer→receipt→선택 mask→최초 신호→가격경로→지표→권고를 리뷰한다. 수정 후 영향을 받은 회귀를 재실행하고 원 데이터 차이를 설명할 수 있을 때 종료한다. 실제 source count·행동 차이 없이 테스트 수만으로 연구 성과를 주장하지 않는다.

## 9. 산출물·보존·후속 소유

새 `tmp/samsung-continuous-tick-transition-research-20261005/<generation>/`에 `intake.json`, `source-availability.json`, `window-receipts.json`, `hypothesis-registry.json`, `decisions.json`, `paired-events.json`, `comparisons.json`, `recommendation.json`, `validation.json`을 발행한다. 권고 시에만 별도 frozen을 추가한다. 기존 locked source를 복제하지 않고 정확한 SHA와 보관 경로를 결속하며 cleanup 보호 대상을 명시한다.

새 연구 실행 owner는 `SamsungContinuousTickWindowResearch`다. 이후 날짜 고정 검증은 기존 `SamsungFrozenCandidateValidation1006`를 재사용한다. 원흡수·원H2·과거 두 veto·이번 추가 후보를 서로 다른 ID로 유지한다. 데이터 도착 전은 waiting이며 동일 재생을 반복하지 않는다.

최초 계획 작성 요청은 문서와 fixture 보완으로 종료했다. 이후 사용자 `계획 실행`으로 R0–R4와 두 가설의 실제 원천 재생·리뷰·회귀를 완료했다. 신규 운영 정책 발행·배포·삼성 정책 지정은 실행하지 않았다. 권고 후보의 이후 날짜 소비자는 기존 H2 adapter와 구분하여 후속 owner에서 연결한다.
