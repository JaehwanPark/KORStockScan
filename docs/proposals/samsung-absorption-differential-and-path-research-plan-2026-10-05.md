# 삼성전자 흡수 후보의 성공·실패 차이와 가격경로 추가 연구계획

작성일: 2026-10-05 KST. 상태: **계획 수립 완료, 추가 계산 미실행**.

## 1. 연구 질문과 범위

사용자 요청은 삼성 후보 추가연구계획이다. 최신 `absorption_p60_v10`의 어느 원천 조건이 목표 선도달·손절 선도달·미도달을 가르는지, 기존 가격 자료를 더 일관되게 소비했을 때 삼성 전용 후보를 권고할 수 있는지 확인한다. source 수집 확대·임계값 무한 탐색·보조 AI 혼합은 이 계획에 포함하지 않는다.

Main `005930`, `KRX|KRX_REGULAR`를 소유한다. 전체 원 origin과 `MAIN_FIXED_WATCH`는 별도 결과다. Widget 실거래, NXT 장전·별도 premarket 가설은 설명 자료와 기존 owner에 남긴다. 그 성과를 정규장 Main의 성과로 합산하지 않는다.

이 계획은 추가 연구의 범위와 구현·검증 순서다. 삼성 신규 정책의 지정·등록·배포를 수행하거나 비삼성1회 지정 범위에 삼성까지 포함하는 문서가 아니다.

## 2. 이미 확정한 사실과 반복하지 않을 계산

[10/5 실행 리뷰](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md)의 S1~S3는 완료됐다.

| 항목 | 현재 근거 | 추가 연구에서의 처리 |
|---|---|---|
| 원 관측/상시감시 |519/206, 원 신호 구간68/31 | 첫 신호 계산 자체를 새 가설로 반복하지 않음 |
|10/2 기존/흡수 선택 |2/8 | 각각 원 선택 ID·시각을 보존 |
|10/2 목표/손절/완전60분 미도달 | 기존0/0/2, 후보4/2/2 | 기존 binary null을 실패0%로 치환하지 않음 |
| 미도달 포함 목표 도달률 |0/2→4/8 | 실제 계산 가능한 가격기회 지표로 별도 비교 |
| 비용 후 양수 비율 |1/2→4/8, 모두50% | 현 흡수 후보가 이 지표에서 이미 우세하다고 주장하지 않음 |
| 첫 신호 축소 | 기존과 후보 선택·결과 변화0 | 임의600초 thinning으로 좋은 결과를 골라내지 않음 |
| 미래 adapter | 최신 absorption frozen과 기존 veto2개 별도 준비 |10/6 이후 자료 부재는 waiting; 코드 준비와 성능 확인 구분 |

[환경 조건부 연구](../audits/samsung-environment-conditioned-pattern-research-review-2026-10-04.md)는 종목 방향·프로그램·투자자·이전 발행 breadth를 이미 폭넓게 계산했다. 과거51조건/여러 신호·종료의 전체 grid를 반복하지 않는다. 원519 capture에 intraday market/sector context가 없었고 유효 prior breadth도 하락 상태에 치우쳤다. 이 자료로 상승장/중립장/하락장 우열을 새로 검증했다고 주장하지 않는다.

[호가 회복 연구](../audits/samsung-quote-recovery-and-absorption-research-review-2026-10-04.md)와 [상시감시 연구](../audits/samsung-fixed-watch-evaluation-and-owner-comparison-review-2026-10-04.md)는 호가 결손·잠금호가·시점·비중복 점유의 영향을 이미 구분했다. 해당 결과는 가설 중복 검사에 사용하며 전체 재생을 기본값으로 삼지 않는다.

## 3. R0: 기존 원천과 가설 등록부 고정

1. 원 capture519건과 완료 가격, 보관 tick/quote의 실제 경로·물리 SHA·raw canonical SHA·시각·route/request·epoch·원 비용/stop을 작은 manifest로 봉인한다. 현재 [연구 입력](../../tmp/admission-remediation-execution-20261005/replay-v2/research-request.json), [최신 삼성 결과](../../tmp/admission-remediation-execution-20261005/replay-v2/samsung-first-signal-report.json), [동결 계약](../../tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json)을 출발점으로 사용한다.
2. 날짜·origin·원 판정 ENTER/BLOCK/RECHECK별 입력→source 적격→feature 적격→후보 신호→비중복 선택→가격 확정 수를 보존한다. 고유 native/watch 수·원천 시간 coverage·가격 frame 수를 각각 표시한다.
3. 가설별 `already_tested`, `new_conditional_application`, `not_identifiable_from_existing_source`를 기록한다. 같은 식·모집단·점유·비용/label의 재실행은 생략한다. 단순 이름 변경을 새 가설로 세지 않는다.
4. 아래 H1~H4의 필수 필드가 원시각에 존재하는지 먼저 검증한다. 없으면 해당 가설을 닫는다. 이후 snapshot으로 채우거나 API 조회를 추가하지 않는다. 모르는 feature를0/중립으로 넣지 않는다.

원519 중 상시감시206은 하위집합이며 서로 더하지 않는다. fixed-watch 자료 없는9/29를 가짜 watch 학습으로 만들지 않는다. 과거 gzip3개 종전 압축 bytes 미보관은 역사 한계로 남기고 새 manifest가 원 bytes 복원이라고 주장하지 않는다.

## 4. R1: 성공·실패·미도달의 원천 차이

분석 대상을 현재 ENTER에 한정하지 않는다. 같은 원 관측의 기존/흡수 행동과 미래 가격 outcome을 연결해 다음을 만든다.

- 목표 선도달, 손절 선도달, 완전 미도달 중 비용 후 양수/0/음수, 가격 검열, source 결손의 **서로 배타적인 결과표**.
- 후보 추가/유지/제거 진입의 분해. 기존 성공 제거는 손실 진단이며 후보 탈락 조건이 아니다.
- buy pressure·공격 delta·신뢰 tick 수·원 가격 변화·bid/ask/spread·원 비용/stop·과거에만 관측한 가격 범위·유효 프로그램/투자자 상태의 날짜별 분포와 결손 수.
- 신호 시점과 후보 선택 시점의 차이, 가격 상승 시작 전에 이미 보였던 feature와 사후에만 계산 가능한 feature의 분리. outcome이 원인 변수로 들어가지 않았는지 필드 단위 검사.

목표 이후 최대 상승은 진입 성과를 추가로 부풀리지 않는다. 손절 뒤 반등은 `post_stop_recovery_diagnostic`으로만 기록한다. 한 봉 안에서 목표/손절 모두 닿아 순서를 모르면 기존 순서 결손을 유지한다.60분까지 연속 경로가 있어야 완전 timeout이며 장 종료로 짧아진 경로·gap 뒤 가격은 완전 timeout과 구별한다.

## 5. R2: 같은 선택과 같은 기회의 비교

평가는 두 표로 분리한다.

1. **정책 선택 전체:** 기존/후보가 같은 원 관측 집합에서 각각 최초 신호·원 비중복 점유로 고른 결과. 신호 수의 차이도 정책 효과다. native·broker 기회로 승격하지 않는다.
2. **공통 사건 비교:** 미래 label을 보지 않고 같은 원watch/날짜/route/epoch의 관측 신호 구간을 고정한다. 양 arm 모두 선택한 사건의 진입 시점 차이와 한쪽만 선택한 사건을 나란히 공개한다. 공통 부분집합만으로 전체 정책 성과를 대체하지 않는다.

각 진입의600초→최대3600초 기존 label을 주 결과로 유지한다. 공통 사건에서는 같은 절대 종료 시각을 쓰는 별도 가격 진단도 계산해 진입 시점 효과와 보유시간 효과를 구분한다. 이 진단으로 원 barrier/stop/점유 label을 바꾸지 않는다. 동일 시각·서로 다른 ask를 독립 사건으로 늘리지 않는다.

## 6. R3: 최대 다섯 변형만 검증

흡수 기준의 pressure60·trusted10·원 soft/hard fact·replace semantics를 고정하고 아래 조건을 **각각 하나씩** 추가한다. 기존 연구와 같은 조건이면 R0에서 생략한다. 모든 조건은 진입 시점 이전 원천으로만 계산한다.

| ID | 질문/고정 정의 제안 | 원천 전제·중단 사유 |
|---|---|---|
| H1 공격 매수의 분산 | 원 신뢰10tick 창에서 최대 단일 BUY 수량이 총 BUY 수량의 절반 이하인 흡수 신호가 더 낫나? 원흡수 vs 이 조건 추가 비교 | 같은 receipt의 개별 거래 방향·수량·순서가 있어야 함. 요약 pressure만 있으면 계산 불가.50%는 새 연구의 사전 고정값이며 결과에 맞춰 조정하지 않음 |
| H2 매수 우위 전환 | 같은 epoch의 직전 적격 capture에서 pressure<60, 현재≥60인 전환 신호와 이미≥60이던 지속 신호가 다른가? 변형은 전환만 수용 | 직전 capture는 원 TTL 이내·현재 이전이어야 함. 단절/이전 값 없음은 unknown; 뒤의 capture로 대체 금지 |
| H3 호가에 나타난 가격 반응 | 같은 원 신호 구간 직전 호가 대비 현재 bid가 낮아지지 않고 spread가 커지지 않은 흡수 신호가 더 낫나? | 정확한 선행 quote와 현재 quote·route·epoch 필요. 잠금/역전 quote는 원 실행 적격과 가격 진단을 분리하고 guard 완화 금지 |
| H4 비용을 넘을 과거 변동 여유 | 진입 전 완료5분의 원 가격 범위가 당시 총비용+순목표0.1%보다 큰 흡수 신호가 더 낫나? | 과거5분 연속·완료 가격과 원 비용이 모두 필요. 봉 완료 시각과 실제 이용 가능 시각 모두 진입 이전인지 검증. 당일 고가/미래 range 사용 금지. 기존 range/cost 가설과 동일하면 생략 |
| H12 사전 고정 조합 | H1∧H2 하나만 추가 | 두 원천이 원시각에 존재할 때만 계산. 결과를 보고 다른 조합을 추가하지 않음 |

따라서 최대 **5변형 + 원흡수 + 기존 정책 = 7개 정책**이다. 각 변형은 원흡수 C0의 ENTER에만 추가 조건을 적용한다. 조건 pass는 C0 ENTER, 알려진 fail은 RECHECK, 추가 조건 unknown은 **C0 행동 승계**로 고정한다. 원흡수가 BLOCK/RECHECK이면 그대로 유지한다. 기존 parent와 원흡수의 차이는 별도 대조군에서 평가하고, 추가 필터 실험에서 이를 동시에 바꾸지 않는다. unknown 행은 제외하지 않고 C0 승계 건수·결과를 공개한다. 원 source 자체가 무효인 행은 기존 source ledger에서 제외한다.

환경은 시간대·당시 종목 방향·유효 프로그램/투자자 상태에 따른 설명표로 먼저 사용한다. 추가 환경×가설 전수조합이나 intraday index/sector의 새 수집은 하지 않는다. 필수 원천이 없다면 해당 가설은 `not_identifiable`로 종료한다.

## 7. 삼성 전용 연구 목적과 후보 권고

기존 정책10/2의 binary null 때문에 결과를 하나의 승률로 뭉개지 않는다. 이번 추가 연구에서는 다음 **신규 연구 계약안**을 실행 전에 고정한다.

| 지표 | 역할 |
|---|---|
| 목표/손절 확정 승률 | 기존 Main 지표와 비교하는 필수 보고값. 양쪽 정의될 때만 개선을 말함 |
| 완전 가격경로의 비용 후 양수 비율 | **이번 삼성 추가 연구의 권고 주지표 제안**. target/stop/완전60분 timeout의 같은 종료 정의로 계산. 실제 체결 승률이 아님 |
| 미도달 포함 목표 도달률 | 목표 포착 효과·기존 binary 미식별 상태 설명 |
| 평균 가격 CF·손실 분포·미확정 민감도·빈도 | 별도 진단. mean CF 양수/기존 성공 보존을 새 자동 탈락 조건으로 추가하지 않음 |

이는 기존 binary null을0으로 바꾸는 수정이 아니다. 평가 목적을 달리한 **삼성 연구 계약**이며, 실제 운영 선정 지표로 채택하려면 삼성 전용 schema·producer/consumer·후속 검증 계획이 필요하다. 현 `absorption_p60_v10`은 양수 비율50→50이므로 이 기준의 개선 후보라고 미리 선언하지 않는다.

날짜 동일 가중으로 원전체와 fixed-watch를 따로 계산한다. 연구 최소 지원 제안은 각 arm 완전 경로 총3개 이상·서로 비교 가능한2날짜 이상이며 날짜별 분모를 공개한다. 이는 비삼성30/10의 운영 승격 조건을 복사한 값이 아니고, 삼성 운영 승인 기준도 아니다. 한 날짜의 반복 tick/watch/episode가 독립 날짜 지원을 늘리지 않는다.

9/29·9/30 발견,10/2 고정 재생과 날짜별 제외 민감도를 제공하되 **세 날짜 모두 이미 탐색된 자료**임을 표시한다. 기존 후보와 흡수 후보를 모두 대조하고, 신규 변형의 양수 비율 개선·지원·원천 적격·같은 날짜 비교가 충족되면 가장 단순한1개만 `recommend_register_for_forward`로 권고한다. 동률이면 원 후보를 유지하며 새 조합을 열지 않는다. 전체 origin만 개선되고 fixed-watch가 미식별이면 권고 scope에 그 한계를 명시한다.

원천/지원이 부족하면 `not_identifiable`, 적격 계산에서 개선이 없으면 `no_improvement`다. 후보가 발견돼도 과거 자료만으로 `independent_validated` 또는 `runtime_selected`라고 하지 않는다. 연구를 통해 별도 지정 적용을 권고할 경우에도 이번 비삼성 지정 요청에 묶어 적용하지 않는다.

## 8. R4 이후 원천 연결과 비삼성 변경 의존성

[비삼성 지정 계획 §6](non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md)의 삼성 component 동등성 검증이 선행한다. 현재 adapter는 전체 parent/kernel hash를 검증하므로 비삼성 recipe 추가 후 자연 원천을 그대로 읽으면 중단될 수 있다. 원 frozen을 덮어쓰지 않고 허용 diff·원/새 kernel·삼성 행동 동일성의 migration receipt를 만든다. 실제 삼성 component가 바뀌면 연구를 재계획한다.

최신 absorption 원 후보의 기존 frozen은 보존한다. 추가 연구에서 권고된 후보가 있으면 별도 frozen에 정확한 rule·연구 목적·B0/흡수/신규 후보 hash·source/kernel·discovery cutoff·이후 날짜 조건을 결속한다. 처음 보는 날짜는 해당 frozen을 만든 뒤의 미소비 적격 날짜로 결정한다.10/6 결과를 먼저 확인했다면 같은10/6을 그 결과로 고른 후보의 독립 검증으로 사용하지 않는다.

이후 자연 검증은 기존 `SamsungFrozenCandidateValidation1006` 한 owner에 후보 목록을 추가한다. 과거 foreign/program veto2개, 원흡수, 새 권고를 서로 다른 candidate ID로 유지한다. 현재 source가 없으면 waiting, 유효 관측0이면 valid-empty, 식별 가능한 불량은 excluded로 남긴다. 동일 입력을 반복 실행하지 않는다.

## 9. 구현 위치·리뷰·산출물

기존 원천 reader·비용/stop·가격 label은 `entry_admission_analysis.py`, `entry_flat_buy_flow_research.py`, `samsung_absorption_acceptance_research.py`를 재사용한다. 새로운 조건부 원천 비교만 제안 `src/engine/scalping/samsung_absorption_differential_research.py`에 둔다. 역할은 Main 삼성 오프라인 연구이며 engine root에 새 모듈을 만들지 않는다. 새 test는 대응 `src/tests/test_samsung_absorption_differential_research.py`다. 연구 식이 나중에 운영 등록될 때 공용 evaluator로 옮기고 연구/운영 두 구현을 독립 유지하지 않는다.

새 `tmp/samsung-absorption-differential-research-20261005/<generation>/`에 다음을 생성한다.

- `source-manifest.json`, `hypothesis-registry.json`: 원천·이미 실행한 식·가용성·사전 고정값.
- `outcome-census.json`, `feature-differences.json`: 원 판정별 분모·손절/목표/완전미도달/결손과 원천 차이.
- `paired-events.json`, `comparisons.json`: 정책 전체와 공통 사건, 원 선택 ID·미확정·날짜별 결과.
- `recommendation.json`, 필요시 `frozen-candidate.json`: 개선/개선 없음/식별 불가와 정확한 후보·scope·이후 날짜 조건.
- `validation.json`: provenance·당시 이용 가능성·계산·재현성·기존정책/준비 hash 보존.

구현→리뷰→보완→재리뷰→표적 pytest/compile/diff 순서를 적용한다. 필수 회귀는 미래 tick/quote·미완성봉·늦게 이용 가능해진 봉 누출, TTL/epoch 단절, 같은 시각 순서, unknown의 C0 승계/known-fail의 RECHECK/원BLOCK 보존, 단일 큰 거래 수량 단위, 원천 중복, 장 종료 검열, stop 뒤 반등, null/0, 전체/fixed-watch 중복 가산, 삼성/비삼성 component 변경, quote 잠금/역전, fold 간 가설 재선정이다. 검증은 기존 원 데이터와 이전519관측 parity를 포함하되 문서 작성 단계에서 무거운 재생을 실행하지 않는다.

## 10. 실행 순서와 유한 종료

`SamsungAbsorptionDifferentialResearch1005`가 R0→R1→R2→R3→R4 및 리뷰를 소유한다. 비삼성 지정 구현과 연구 계산은 별개이며 한쪽 연구 결론 때문에 다른 쪽 적용 scope를 확대하지 않는다. 이후 자연 날짜 검증과 당일 기동 owner는 기존 항목을 재사용한다.

R0에서 모두 중복/원천 부재면 가설별 근거를 기록하고 종료한다. R3까지 진행하면 최대7개 정책의 비교로 종료하며, 이번 입력에서 후보1개 권고/개선 없음/판단 불가 중 하나를 확정한다. 후보가 없다고 임계값·보유시간·분류 경계를 계속 바꾸거나 수집 확대를 자동으로 시작하지 않는다. 새 원천이 없는 상태에서 미래 성능 확인을 완료로 선언하지 않는다.

## 실행 기록

사용자 `계획 실행`으로 구현·리뷰·실제 원천 재생을 수행했다. 최신 상태와 역사 원천 결손, 발행/배포/준비 증빙은 [실행 리뷰](../audits/designated-machine-policy-and-samsung-differential-execution-review-2026-10-05.md)를 따른다. 계획 본문의 미실행 표현은 작성 시점 상태다.


## 다음 연구계획

기존5변형 연구는 종료했다. 판정 capture 간격으로 식별되지 않은 H2를 기존 연속 체결 구간에서 평가할 수 있는지 [별도 추가연구계획](samsung-continuous-tick-window-transition-research-plan-2026-10-05.md)으로 분리했다. 원 H2와 원흡수 frozen의 의미·과거 결과를 수정하지 않는다. 추가 가설 재생은 아직 실행하지 않았다.
