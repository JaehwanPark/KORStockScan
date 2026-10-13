# Main 놓친 상승·ENTER_NOW 실패 감소 병행 연구 결과 — 2026-10-13

## 1. 결정과 범위

[연구계획](../proposals/main-machine-missed-rise-and-enter-failure-joint-research-plan-2026-10-13.md)을 실행하고 리뷰·수정보완했다. **추가 상승 기회와 기존 ENTER_NOW 실패 감소의 두 축에서 모두 후보를 확인했다.** 정책별 실패·성공과 OR 중복을 보존하고, 실패 감소 단독12범위·추가 탐지 단독5범위·두 효과 결합9범위를 산출했다. 같은 정의/기회가 겹치므로 이를26개 독립 신규 정책이나 거래로 합산하지 않는다.

현재 선택됐던 불변 `main-residual-reviewed-20261013-v6` / commit `2223ac9e948cdbf79bf2ed1e1b6c4c5d7f069df6`, bundle `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`를 기준으로 고정했다. 타 세션의 이후 pointer/배포 변경은 별도다. 현재 정책을 과거 원천에 재생한 **확인점 평가**이며, 역사 실운영 ENTER_NOW 전부의 소비·주문·손익을 입증하는 자료는 아니다.

## 2. 원천과 성과 분모

- 9/29·30, 10/2·6·7·8·12의 **21개 파티션, 4,385,144행**을 읽었다. PRE NXT `_NX`, REGULAR·AFTER SOR `_AL`의 보유 전체 종목을 처리했다. 9/29 이전 원천은 순위·선택에 포함하지 않았다.
- 유효 normalized source 행은 **3,812,529**, 제외된 행은572,615다. quote·item·연속 구간 검증을 별도로 적용했고 추가 가설의 feature UNKNOWN은 match로 바꾸지 않았다.
- 현재 기준 정책의 canonical 확인점13,732개 중 **WIN2,592 / STOP194 / TIMEOUT1,127 / UNRESOLVED9,819**다. 확정 실패1,321개가 성공과 함께 모든 비교의 분모에 들어갔다. 미확정은 실제 손실이나0수익으로 보충하지 않았다. 이는 여러 시장·scope의 원천 census이며 정책 선정은 각 scope에서 비교한다.
- 실제 확인 ask부터1,800초, 비용률0.0023·순 목표+0.4%·손절−3%의 기존 라벨을 유지했다. 충분한 30분 경로의 미도달은 TIMEOUT, 부족한 경로는 UNRESOLVED다. 기존 동일 item 완료 분봉으로10분 이후 가격도 보조했다. 이 라벨은 실제 fill/PnL이 아니다.
- source key는 해당 normalized 시리즈의 `(date,item,epoch,sequence)`다. collector/native namespace의 현재 소유 계약을 넘겨 실제 Main claim이나 주문 신원으로 바꾸지 않았다.

### 10/12 원천 결손

| 시장 | 전체 행 | 유효 행 | 연구 처리 |
|---|---:|---:|---|
| NXT PRE | 15,347 | 0 | `source_epoch_unverified` 원천 제외 |
| SOR REGULAR | 496,054 | 0 | `source_epoch_unverified` 원천 제외 |
| SOR AFTER | 110,264 | 76,383 | 검증된 구간만 사용 |

따라서 PRE/REGULAR의10/12 표본0은 패턴 실패·무수익이 아니다. 현재값으로 역사 epoch를 채우지 않았다. 기존 수집 원본에 실제 epoch/sequence 증빙이 보존돼 있는지와 [정규화 생산자](../../src/engine/scalping/continuous_reversal_source.py)의 소비 연결을 후속 점검할 대상이다. 가격 추가 수집보다 현재 보유 증빙부터 대조해야 한다.

## 3. 고정 가설과 선별 방법

[동결 manifest](../../tmp/main-machine-joint-research-20261013/frozen-manifest.json)에 추가 탐지 A01~A09·실패 보완 F01~F16을 먼저 고정했다. 상승지속·고점 돌파·느린 momentum·FIRST1/3/5초 유지·재시험을 추가 축에서, ret/session/VWAP/BUY10/거래량/spread/낙폭/고저 구조를 실패 감소 축에서 검토했다.

종목 흐름은 첫 유효 관측 체결가 대비 변화이며 외부 지수 국면이 아니다. VWAP 특징은 확인 시점 체결가/60초 수량 가중 평균의 차이이고, 연구 spread 특징은 `100*(ask-bid)/trade_price`다. 실제 진입 label은 ask를 사용하며 native quote/source hard guard와 이 연구 특징을 혼동하지 않는다. 후속 구현은 이 frozen 특징 정의와 정확히 대조해야 한다.

9/29~10/8의6개 보유 날짜에서 후보를 정하고10/12를 따로 비교했다. 현재 기준 정책도10/12 원천을 소비했으므로 이 분할을 미관측 독립 미래 holdout이라 부르지 않는다. learning에서 정한 정의의 누적 개선을 보고하며 특정 새 날짜 WIN·최소 일수/표본·EV·성공100%/80% 보존 gate는 없다.

F는 scope 전체와 개별 branch의 보완을 각각 계산한다. 다른 OR branch가 같은 확인점을 허용하면 전체 실패 제거가 아니다. 추가 특징이 UNKNOWN인 baseline은 유지하고 검증된 불일치만 제거한다. 원 정책을 그대로 OR로 유지하면서 F를 추가한 결과를 실패 감소라고 계산하지 않았다.

### 리뷰에서 보완한 결합 비교

처음에는 단독 A/F 우위 후보만 결합했다. 그러나 A 단독이 기존 승률을 낮춰도 F와 결합하면 전체 승률이 개선될 수 있어, **이미 고정한 정의의8,032개 scope/branch 조합**을 비교하도록 수정했다. 새 threshold나 패턴을 만든 단계가 아니다. 추가 후보가 재허용하는 실패도 실제 합집합 분모에 포함했다.

[승률 최고 결과](../../tmp/main-machine-joint-research-20261013/joint-result.json)와 [성공 기회가 많은 선택/Pareto 결과](../../tmp/main-machine-joint-research-20261013/opportunity-frontier-result.json)를 구분했다. 후자는 learning에서 기존보다 높은 승률인 조합 중 확정 성공이 가장 많은 정의를 고정한 결과다. 성공 보존율의 최소 gate는 없다.

## 4. 추가 탐지 단독 결과

[전체 단독 비교](../../tmp/main-machine-joint-research-20261013/result.json)의 추가 후보5범위 중 대표 결과다. 신규 성공만 골라 평가하지 않고 추가 실패를 모두 포함했다.

| 범위 | 가설 | 기존 → OR 성공/확정 | 추가 W / FAIL |
|---|---|---|---|
| 주성 REGULAR 고가 | A03: 얕은 FIRST1초 유지＋BUY10≥60 | 914/1,292=70.74% → 1,172/1,583=74.04% | 258 / 33 |
| 알테오젠 PRE 고가 | A03 | 404/483=83.64% → 412/491=83.91% | 8 / 0 |
| 알테오젠 REGULAR 고가 | A03 | 20/81=24.69% → 49/172=28.49% | 29 / 62 |
| 일반 AFTER 고가 | A05: FIRST1초·DD0.4~1.2% | 2/2 → 3/3 | 1 / 0 |
| 일반 PRE 중가 | A09: FIRST5초・DD0.2~1.2%・VWAP/BUY60 | 29/30 → 30/31 | 1 / 0 |

일반 AFTER 고가는 목표 시각1개에 집중된 작은 표본이다. 알테오젠 REGULAR은 승률이 높아져도 추가 실패62건이 성공29건보다 많으므로 함께 공개한다. 후보 등록·실시간 root parity·주문 가능성과 구분한다.

## 5. 기존 실패 감소 단독 결과

아래는 원 정책을 보완한 반사실이다. 12개 범위 전체의 원 정의·수치·UNKNOWN·일별 결과는 `result.json`에 있다.

| 범위 | 보완 | 기존 → 보완 성공/확정 | 잃은 기존 WIN | 제거한 STOP+TIMEOUT |
|---|---|---|---:|---:|
| 두산 AFTER 중가 | F11: 고저 동반 상승 | 40/54 → 30/36 | 10 | 8 |
| 주성 AFTER 고가 | F11 | 258/664 → 54/89 | 204 | 371 |
| 주성 REGULAR 고가 | F15: spread≤0.1%＋BUY10≥60, 해당 legacy branch | 914/1,292 → 354/406 | 560 | 326 |
| 알테오젠 PRE 고가 | F15, 해당 legacy branch | 404/483 → 70/70 | 334 | 79 |
| HPSP REGULAR 중가 | F05: 확인 시점 체결가가60초 VWAP 이상, 해당 branch | 438/453 → 392/392 | 46 | 15 |
| 일반 PRE 저가 | F15, scope 전체 | 163/239 → 24/26 | 139 | 74 |

최고 승률이 기존 성공을 대량 제거하는 사례가 실제로 나왔다. 이를 성공 보존율로 자동 탈락시키지는 않지만 적용 효과를 숨기지 않는다. 특히 알테오젠 PRE의70WIN은 목표 시각2개에 집중한다.

## 6. 두 효과를 결합한 기회 확대 선택

아래9개 범위는 고정 learning에서 선택한 **성공 기회가 많은 조합**의 누적 결과다. 각 행의 정확한 원 branch·필터·추가 root·UNKNOWN·일별 결과는 Pareto JSON에 있다. scope의 정책을 재구성한 결과이며 기존 정책과 보완 정책을 그대로 OR한 결과가 아니다.

| 범위 | 기존 → 결합 승률 | 기존 → 결합 WIN | 기존 → 결합 FAIL | 잃은 WIN / 제거 FAIL / 추가 WIN / 추가 FAIL |
|---|---|---|---|---|
| 주성 AFTER 고가 | 38.86% → 41.84% | 258 → 264 | 406 → 367 | 8 / 67 / 14 / 28 |
| 주성 REGULAR 고가 | 70.74% → 73.93% | 914 → 1,109 | 378 → 391 | 63 / 20 / 258 / 33 |
| 알테오젠 PRE 고가 | 83.64% → 91.09% | 404 → 368 | 79 → 36 | 44 / 43 / 8 / 0 |
| 알테오젠 REGULAR 고가 | 24.69% → 33.33% | 20 → 101 | 61 → 202 | 0 / 61 / 81 / 202 |
| HPSP AFTER 중가 | 47.37% → 48.57% | 9 → 17 | 10 → 18 | 0 / 10 / 8 / 18 |
| HPSP REGULAR 중가 | 96.69% → 96.94% | 438 → 412 | 15 → 13 | 46 / 15 / 20 / 13 |
| 일반 AFTER 저가 | 32.43% → 32.76% | 36 → 38 | 75 → 78 | 0 / 3 / 2 / 6 |
| 일반 PRE 중가 | 96.67% → 100.00% | 29 → 28 | 1 → 0 | 2 / 1 / 1 / 0 |
| 일반 PRE 저가 | 68.20% → 74.47% | 163 → 175 | 76 → 60 | 6 / 29 / 18 / 13 |

**일반 PRE 저가와 주성 AFTER는 총 WIN 증가·총 FAIL 감소를 함께 확인했다.** 주성 REGULAR 등은 기존 실패를 일부 제거해도 새 후보의 실패가 더 많아 전체 FAIL 수가 증가한다. 이 경우 승률/실패율 개선과 실패 절대 건수 감소를 혼동하지 않는다.

대표 정의:

- 일반 PRE 저가: A08 고점 돌파＋ret≥0·DD≤0.4%·BUY10≥60, F04의 종목 흐름≤0.4% 보완을 해당 legacy volume branch에 적용. 확인 ask의175WIN/235확정, 목표 시각50개, U41이다.
- 주성 AFTER: A08와 F05 VWAP 보완의 해당 legacy branch 교체. 264WIN/631확정, 목표 시각20개, U243이다.
- 주성 REGULAR: A03 얕은 FIRST1초 유지＋BUY60와 F03 종목 흐름≥−0.4%의 해당 legacy volume branch 보완. 1,109WIN/1,500확정, 목표 시각82개, U1,289다.
- HPSP REGULAR: A09 FIRST5초 유지와 F05 VWAP의 해당 manual branch 보완. 최고 승률 쪽의 A03 조합은398/400=99.50%, 성공 기회 쪽의 A09 조합은412/425=96.94%다. 두 선택의 기회 손실을 모두 공개한다.

## 7. 삼성과 미평가 범위

삼성은 이번25개 고정 가설에서 누적 우위의 신규/보완 후보가 없다. 현재 정책 재생은 PRE13WIN/13확정(U863), REGULAR88WIN/88확정(U5), AFTER0WIN/48확정(U399)다. REGULAR의88WIN은 목표 시각7개다.

이는 **현재 정책을 보유 원천에 재생한 결과**이며 역사 실판정이 모두 정답이라는 뜻이 아니다. 특히10/12 PRE/REGULAR는 원천 증빙 결손으로 미평가다. AFTER의 확정48개는 TIMEOUT이어서 단순한 기존 확인점 필터로 새로운 WIN을 만들 수 없다. 이번 고정 추가 root에서도 충분한 새 WIN이 없어 제안하지 않았다. 다른 확인 방식·다른 기존 원천 계약의 가능성까지 소진됐다는 결론은 아니다.

## 8. 검증과 후속 순서

- 표적 pytest **19건 PASS**, 임시 Python compile·공백/diff 검사. 성공 손실 허용, UNKNOWN 유지, 다른 OR branch의 재허용, 추가 후보의 단독 열세를 포함한 결합, 최고 승률/성공 기회 선택을 검증했다.
- [라벨 검증](../../tmp/main-machine-joint-research-20261013/label-validation.json): 실제102개 확인점의 item/epoch/sequence/시각/ask 대사와 독립 선형 tick oracle, 그중 기존 완료 분봉34개 재검사, 불일치0. 원 시리즈7,658개의 수신 시각 순서를 확인했다. 재계산 표본은 전체 라벨의 미래 성과 보장이 아니다.
- [원천/코드 검증](../../tmp/main-machine-joint-research-20261013/validation.json): source/code/기준 입력 해시230개 일치. 모든21파티션 완료, current native pending overload0이다. 새 A/F runtime 구현의 pending 한도·정의 parity는 후속 등록 단계의 별도 검증이다.
- 단일 offline 계산/nice19/파티션별2GiB·CPU480초·wall600초, source/API/Provider 수집 확대0이다. 실제 운영 코드/정책·봇·주문·custody와 타 세션 작업본을 변경하지 않았다. 문서/원 가설은 English ASCII ID를 사용했다.
- [후보 인계 패키지](../../tmp/main-machine-joint-research-20261013/candidate-package.json)는 고정25개 정의에 대한 단독·최고 승률·성공 기회 선택의35개 비교 view를 담는다. 등록된35개 신규 정책이라는 뜻이 아니다. parent/result hash·정확 scope·branch 보완·root와 `registered=false`, `allowed_runtime_apply=false`를 유지한다.
- 문서 로컬 링크11개, owner/authority·공백/`git diff --check`, print-only parser23항목을 확인했다. 다른 세션이 변경한 당일 checklist는 현재 objective/mandatory rules를 다시 읽고 보존했으며 이 연구가 편집하지 않았다. Project/Calendar sync와 broad trading/provider 검증은 실행하지 않았다.

다음 작업은 **현재 보유10/12 원천의 epoch 증빙 생산→정규화 연결 대사**, 그리고 **일반 PRE 저가·주성 AFTER/REGULAR 후보의 정확한 새 정의와 branch 교체/추가 OR 소비 계획**이다. 연구 결과가 정해진 뒤 새로운 자동 threshold 탐색이나 성공 보존율 gate를 추가하지 않는다. 고정 등록 후보의 후속 장후 비교와 자연 신호·Main 소비·실제 실행은 기존 owner가 별도 증빙한다.
