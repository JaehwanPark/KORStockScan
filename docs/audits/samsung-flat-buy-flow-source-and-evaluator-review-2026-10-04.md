# 삼성전자 보합 매수 수급 원천·기계 경로 대사

작성: 2026-10-04 KST. [선행 리뷰 §7](samsung-machine-horizon-pattern-research-review-2026-10-04.md)의 다음액션을 실행했다. 삼성전자 기계판정만 분석하며 보조 AI·제출 결과를 원인에 섞지 않는다.

## 1. 판단

**기존 원천으로 후보를 더 검증할 수 있다. 확인된 개선 대상은 원천의 소비 시점과 보합 수급을 표현하지 못하는 기계 규칙이다.**

1. 고정 후보 `absorption_p60_v10`의10/2 8관측에서, 기록된 체결 지표는 당시 소비한 receipt 시점의 보관 체결과 모두 일치했다. 원 수치가 근거 없이 만들어진 것은 아니다.
2. 그중4관측은 locked BBO로 최신 갱신이 보류되어 약1.3~2.6초 전 snapshot을 사용했다. 판정시각의 최신10체결을 계산하면 값이 달라진다. 14:39 목표 관측은 매수 우위에서 매도 우위로 바뀐다.
3. 원8시각 고정 민감도는 목표3·손절2·시간종료2·조건이탈1이다. 모든 신호를 다시 시간순 점유 재생하면14:52의 다른 목표 관측이 들어와 목표4·손절2·시간종료2를 유지한다. **체결3필드만 바꾼 민감도이며 완전한 정책/feature 재생 결과는 아니다.**
4. 기존 evaluator와 기존 확인 보완 adapter로는 이 조건의 새 ENTER가 나오지 않는다. 원천 패턴의 존재와 현재 정책의 표현 가능성을 분리해야 한다.

실제 개선 순서는 **관측 cutoff/receipt 명시 → 보합 수급 전용 fact와 위험별 처리 계약 → 같은 평가 함수로 후보/parent 재생**이다. [상세 구현계획](../proposals/samsung-flat-buy-flow-source-and-evaluator-implementation-plan-2026-10-04.md)을 작성했다. 이번에는 운영 코드·정책 발행·배포·기동을 변경하지 않았다.

## 2. 입력과 재현 범위

- 기존 삼성전자684관측 중 KRX 정규장519관측:9/29 313,9/30 46,10/2 160.
- 원 projection, 고정 parent bundle, 선행 가설/가격 연구, normalized trade/depth cache와 관련 SOR 원 archive를 SHA로 대조했다. 최종 소비 입력/코드 seal은47개다.
- parent `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`로 현재 평가 함수를 호출했다.519행 모두 원 행동과 일치: ENTER38·RECHECK340·BLOCK141.
- 후보 조건은 학습에서 선정한 pressure≥60·delta>0·10체결 첫/끝 가격 보합·VWAP≤10bp로 유지했다. 기존 hard/source/invalidation 수치 guard를 통과한 조건 일치73관측:38/9/26.60분 점유를 겹치지 않게 한 원 선택은11/5/8, 합계24다.
- normalized 원천 scope는 `005930_AL/SOR/SOR_REGULAR`이다. Main의 KRX 판정 scope와 구분한다. collector nanosecond epoch를 Main transport epoch1과 같은 ID로 취급하지 않는다.

## 3. 10/2의8관측 전체 원천 대사

원 판정시각과 입력 동결시각을 구분했다. 각 동결시각 이하 마지막10체결을 선택했으며 잘못된 중간 행을 버리고 오래된 좋은 행으로 채우지 않았다. 같은 epoch/연속 sequence, source valid/flow valid, 비미래·신선도를 검사했다.

`매수비중`은 신뢰 가능한 buy 수량/(buy+sell 수량), `순수량`은 buy-sell이다. 아래 최신값은 같은 판정 cutoff의 보관 체결로 독립 재계산했다.

| 시각 | 원60분 결과 | 원→최신 매수비중 | 원→최신 순수량 | 소비 quote age | 원천 대사 |
|---|---|---|---|---|---|
| 10:10:08 | 손절 | 89.46→89.46% | 472→472 | 175ms | 최신 갱신·일치 |
| 10:49:05 | 목표 | 94.49→94.49% | 226→226 | 190ms | 최신 갱신·일치 |
| 10:58:16 | 시간종료 | 84.53→84.53% | 125→125 | 179ms | 최신 갱신·일치 |
| 12:14:47 | 손절 | 86.02→86.02% | 742→742 | 244ms | 최신 갱신·일치 |
| 12:59:22 | 목표 | 98.99→68.75% | 1,068→18 | 1,868ms | locked·이전 snapshot 유지 |
| 13:21:47 | 목표 | 83.33→61.11% | 76→12 | 1,371ms | locked·이전 snapshot 유지 |
| 13:31:19 | 시간종료 | 89.51→62.50% | 633→22 | 2,621ms | locked·이전 snapshot 유지 |
| 14:39:09 | 목표 | 91.10→4.46% | 2,513→−511 | 1,305ms | locked·이전 snapshot 유지 |

### 원 수치가 일치하는 시각

- 입력 trace의 canonical receipt 시각을 사용하면8/8에서 매수비중·순수량·첫/끝 가격 변화가 모두 원 값과 일치한다. 이 결과는 단순히 숫자가 비슷한 과거 window를 검색해서 얻은 것이 아니다. 동결 cutoff와 원 receipt cutoff의 두 고정 시각만 비교했다.
- 최신 판정 cutoff에서는4/8 일치다. 가격 변화는7건0이고14:39만 +0.091%다.14:39는 양의 가격 변화가 생겨도 순매도이므로 이 고정 후보를 만족하지 않는다.
- canonical quote도 별도 확인했다.0B receipt5건은 원 JSONL에서 item·clock·bid/ask에 일치하는 packet이 각각1개였고,0D receipt3건은 normalized depth에서 각각1개였다.0B clock 허용 오차1ms는 archive의 millisecond 표현과 Main의 microsecond 표현 차이를 위한 것이다. 물리 line/hash와 원 packet을 보존했다.
- locked4건의 동일 bid/ask는 실제 보관 packet에 존재한다. 결손을0으로 채운 것으로 보지 않는다. 다만 이것만으로 해당 가격의 KRX 단독 수량·즉시 실행 가능성을 입증하지 않는다.
- `가격 변화0`은 첫/끝 체결 가격이 같다는 뜻이다.10:49 목표 건에도 중간274,250원과274,500원이 섞였다. 보합을 전 체결 동일 가격·호가 재보충·흡수 완료와 같은 의미로 쓰지 않는다.

### 실제 소비 코드의 연결

`_refresh_prepared_entry_inputs` → `_pre_submit_refresh_real_ws_snapshot(refresh_even_if_input_fresh=True)` → `best_ask<=best_bid`일 때 `latest_best_levels_invalid` → 기존 입력 유지 → canonical snapshot 유효기간 재검증 → 기계 feature 생성이다.

이는 단순 API 결손이 아니다. **관측용 입력이 제출용 갱신 함수의 locked BBO 검사 영향을 받는다.** 보류된 원 입력이3초 이내라는 기존 계약은 통과할 수 있다. 따라서 `원천 무효`와 `당시 허용된 이전 원천 소비`를 분리한다. 관측 원천 갱신을 개선할 때 주문 직전 검사를 함께 완화하지 않도록 구현계획에 소유 경계를 정했다.

이 현상은 선택한8건에만 있지 않았다.9/30 전체46관측 중4,10/2 전체160관측 중26이 같은 사유로 갱신되지 않았고 모두 locked BBO였다. 이30건이 모두 잘못된 판정이나 손실을 발생시켰다고 추론하지 않는다.

### 다른 날짜와 남은 대사 결손

| 날짜 | 원 비중복 선택 | 최신 cutoff와 동일 | 원 receipt 또는 최신 cutoff에서 대사 |
|---|---:|---:|---:|
| 9/29 | 11 | 9 | 9 |
| 9/30 | 5 | 4 | 5 |
| 10/2 | 8 | 4 | 8 |

9/29의2건은 미해결로 남긴다.12:46:32는 독립 보관 collector의 마지막 체결이 약815초 전이어서 비교 window가 결손이다.15:00:53은 최신·보관 quote receipt 시각 모두 원 체결 window 수치와 일치하지 않아 정확한 feature window 결속이 미입증이다. 이2건을 원 기계 수치 조작,0 EV,패턴 부재로 분류하지 않는다.9/29는 원 native가 부족한 연구 비교군이라는 선행 한계도 유지한다.

## 4. 현재 기계 규칙에서 남는 것

10/2의8건 모두 `micro.source_usable=true`, `tape_support=true`, `price_response=false`다. scalar 유동성 수치 경계는8건 모두 통과한다. 실제 fact ledger는 다음과 같다. 각 숫자는 중복 가능한 관측 수다.

| 항목 | 관측 수 | 의미 |
|---|---:|---|
| ADVERSE_TAPE | 8 | program 순매도/증분 매도 또는 외국인·기관 동반 매도 등을 원 fact로 유지 |
| CONFIRMATION_MISSING | 6 | trigger 미확인, 일부는 no_supported_setup도 포함 |
| local breakout 재확인 | 3 | 10:49 목표·10:58 시간종료·12:59 목표 |
| NO_VALID_SETUP | 2 | 13:21·14:39 목표의 기존 setup family 부재 |
| LIQUIDITY_FRAGILE fact | 2 | 10:10 손절·13:31 시간종료. scalar 수치 통과가 이 fact의 상쇄를 뜻하지 않음 |

`entry_action_counterweight_bindings`로 **각 risk 아래 모든 fact**를 출력했다. core 비교의 대표 fact 하나만 보고 나머지 위험을 누락하지 않았다.

- ADVERSE_TAPE의 기존 counterweight는 신뢰 가능한 매수 수급과 **양의 가격 반응**을 함께 요구한다. scalar micro threshold 검사뿐 아니라 fact 생성 단계도 `price_response`를 요구한다.
- local breakout recheck는 별도 경로다. trigger 미확인/no_supported_setup을 가격 조건 하나로 일괄 해소할 수 없다.
- 기존 family 확인 adapter는 부모의 일부 RECHECK reason과 matched flow family에만 작동한다.73조건 일치 관측 중43건은 그 adapter가 붙일 기존 flow family가 없다. 남은 경로에서도 **새 ENTER 전환은0**이다. 원래 ENTER였던 행의 반환을 신규 전환으로 세지 않았다.
- 원 비중복24개는 기존 ENTER1·RECHECK23이며10/2는RECHECK8이다. 별도의 보합 수급 recipe가 필요하다는 결과이며, 앞선 가격경로 목표 포착이0이었다는 뜻이 아니다.

## 5. 체결 관측시점 민감도

고정 후보를 다시 최적화하지 않았다. `observed_buy_pressure_10t`, `observed_net_aggressive_delta_10t`, `observed_price_change_10t_pct`만 최신 archive 값으로 치환했다. VWAP·원 quote/진입가/비용·다른 source fact·결과 경로·guard는 그대로다. 따라서 아래는 **부분 feature 민감도**다.

| 날짜 | 원 선택: 목표/손절/시간종료 | 원 시각 고정·최신 체결 조건 유지 | 전체 신호 재점유 |
|---|---|---|---|
| 9/29 | 7 / 3 / 1 | 6 / 2 / 1 (2건 제외) | 7 / 2 / 1 |
| 9/30 | 3 / 2 / 0 | 3 / 1 / 0 (1건 제외) | 3 / 1 / 0 |
| 10/2 | 4 / 2 / 2 | 3 / 2 / 2 (1건 제외) | 4 / 2 / 2 |

10/2 재점유는14:39를 제외하고14:52:57을 새로 선택했다.14:52 원 pressure57.33%·delta22·가격변화+0.091%는 후보 밖이었으나 최신 체결은88.66%·75·0으로 후보 안이다. 이 시각은 원 `latest_ws_snapshot_fresh` 경로여도 동결 cutoff 전의 후속 체결과 소비 window가 달라질 수 있음을 보여준다. feature별 정확한 window receipt가 필요한 이유다.

원10/2 기준선은 시간종료2로 목표/손절 확정 승률은 **null**이다. 후보의4/(4+2)=66.67%를 기준선0% 대비 개선이라고 쓰지 않는다. 두 후보 재생의 비용 후 평균 가격 CF는약−0.3192%로 같으며 실현 PnL은 아니다. 고정8시각에서 조건 이탈만 반영한7관측은60%, 평균 CF약−0.3791%다. 선행의 비용·native 반복·첫 봉·관측밀도 민감도와10/2 반복 연구 한계는 해소되지 않았다.

## 6. 리뷰·수정·검증

격리 코드 위치는 `tmp/samsung-absorption-contract-review-20261004/`다. 운영 module·자동화·API/수신 parser는 수정하지 않았다.

1. 최초 구현→self review에서 기존 ENTER 반환을 신규 전환과 혼동할 수 있는 집계 이름을 발견해 부모 행동이 non-ENTER인 전환만 별도 집계했다.
2. 유효하지 않은0가격 window가 나눗셈 오류를 만들 수 있는 경로를 보완했다. source gap은0값으로 대체하지 않는다.
3. refresh trace가 없는 역사 입력에는 값과 item이 맞는 snapshot BBO receipt를 별도 owner로 조회하도록 보완했다.9/29 미해결2건은 억지로 대사하지 않았다.
4.14표적 회귀: 미래 tick 배제, epoch/sequence/continuity/valid/flow/side 결함, 오래된/짧은/빈 window, 중간 가격 변동과 첫·끝 보합 구분, original risk/cost/label 보존,0가격/결손 처리.
5. 보완본을 `final/`에 다시 생성하고519원행 재현·47입력/코드 seal·출력 hash·quote 결속·분모·신규 전환0을 재검토했다. compile·diff·문서 link/owner·print-only parser를 확인한다. 최초 출력은 superseded 연구 receipt이고 최종 근거는 아래 `final/`이다.

### 최종 산출물

- [고정 계약·47입력 seal](../../tmp/samsung-absorption-contract-review-20261004/final/frozen-contract.json)
- [519관측 evaluator/원천 ledger](../../tmp/samsung-absorption-contract-review-20261004/final/observation-review.json), [원24선택 상세](../../tmp/samsung-absorption-contract-review-20261004/final/selected-24.json)
- [0B 원 packet·물리 line 결속](../../tmp/samsung-absorption-contract-review-20261004/final/inline-quote-receipts.json), [집계·시점 민감도](../../tmp/samsung-absorption-contract-review-20261004/final/result.json)
- [재현 코드](../../tmp/samsung-absorption-contract-review-20261004/review.py), [표적 회귀](../../tmp/samsung-absorption-contract-review-20261004/test_review.py), [검증 receipt](../../tmp/samsung-absorption-contract-review-20261004/final/validation.json)

광범위 매매 suite, canonical 장후 정책 재생성, live policy/PID·PREOPEN 점검은 이번 연구 범위 밖이므로 실행하지 않았다. 현재 검증은 관측/규칙 대사와 구현계획의 완료이며, 새 정책 선정·실현 수익 검증·P0–P3 운영 구현 완료가 아니다.
