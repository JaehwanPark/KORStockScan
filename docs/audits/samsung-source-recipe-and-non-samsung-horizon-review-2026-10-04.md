# 삼성전자 원천·보합 수급 구현과 삼성전자외 전체 행동 통합 연구 — 2026-10-04

## 1. 결정과 실행 범위

사용자 지시: 삼성전자 다음 액션 실행, 삼성전자외 ENTER_NOW·RECHECK·BLOCK의 실제 상승 관측 통합 분석,10분 미도달의 이후 가격 보조 평가. 보조 AI를 분석 입력에 섞지 않았다.

- 삼성전자: 로컬 관측 원천 선택·receipt 생산을 구현하고, 별도 보합 수급 평가 함수를 **report-only**로 구현했다. 원519개 기계 행동을 재현했고 새 규칙의 ENTER 제안을 계산했다. 기존 ENTER 유지형과 조건 교체형을 비교해 앞선 두 날짜에서 교체형을 연구 선택했다.
- 삼성전자외: 삼성전자684행을 먼저 제외한 **8,109관측/764종목**을 통합했다. 세션 종료까지 목표 선도달은 **2,752관측**이며, 이 중 **1,130관측은10분 이후** 목표에 도달했다.
- 새 후보는 찾았다. 삼성전자외 `pullback_p60_v0`의10/2 비중복 비교 승률은 기존60.61% →68.75%다. 삼성전자 교체형은10/2 목표4·손절2·시간종료2다. 성공100%/80% 보존을 탈락 조건으로 사용하지 않았다.
- 코드와 격리 연구를 완료했다. 운영 정책 등록/발행·배포·기동·주문·provider/API 호출·수집 확대는 수행하지 않았다.10/2는 반복 연구한 날짜이므로 독립 검증이라고 부르지 않는다.

여기서 승률은 **목표 선도달/(목표 선도달+손절 선도달)**이다. 목표는 원 관측 ask 대비 원 비용+0.1%, 손절은 원 ask 대비 gross−0.7%다. 시간종료·자료 결손은 별도이며 실제 체결/실현 수익률이 아니다. 행 수는 반복 관측을 포함하므로 거래 건수와 같지 않다.

## 2. 삼성전자 구현

소유 계획: [보합 수급 원천·평가 함수 구현계획](../proposals/samsung-flat-buy-flow-source-and-evaluator-implementation-plan-2026-10-04.md). 코드 위치는 기존 scalping 역할 패키지이며 engine root에 새 모듈을 추가하지 않았다.

| 경계 | 구현·검증한 내용 |
|---|---|
| 로컬 원천 선택 | `entry_machine_observation.py`가 삼성전자 KRX 정규장에 한해 같은 Main transport epoch와 exact item/route의0B·0D·체결 window를 선택한다. 개별 수신시각·미래시각·stale·sequence·crossed quote를 확인한다. |
| locked 호가 | bid=ask를 관측 상태로 남기고 최신 체결을 소비한다. 기존 제출용 `_pre_submit_refresh_real_ws_snapshot`의 실행 호가 판정은 유지한다. receipt는 `executable_quote_verified=false`다. |
| 실제 feature 결속 | `scalping_feature_packet.py`가 실제 소비한 exact-route window와 sequence를 보존한다. `ai_engine_openai.py`가 cutoff·원 payload/window hash·원 시각·수급 수치를 결속한 receipt를 생산한다. |
| 신규 평가 함수 | `entry_flat_buy_flow_research.py`의 고정 조건은 신뢰10체결·매수압력≥60%·순공격매수량>0·10체결 첫끝 가격변화0·현재가의 microVWAP 대비 위치≤10bp다. 원 family/state·가격반응 false·돌파 미확인을 보존하고 `FLAT_PRICE_BUY_FLOW`를 별도 표현한다. |
| 위험별 처리 | 허용한 program/공동매도·trigger/setup fact에만 제안 상쇄를 기록한다. 원 위험 fact를 삭제하지 않는다. liquidity·미지정 위험·invalidation·parent BLOCK·기존 micro recipe·situation veto는 유지한다. |
| 소비자 검증 | receipt 자기 hash 외에 원 payload·scope·route·item·epoch·시각 순서·sequence·feature 값 결속을 직접 검사한다. 형식이 다른 행이나 bool epoch도 거부한다. |
| 정책 권한 | report-only schema는 live policy validator에서 거부된다. 평가 함수는 운영 registry/publisher에 등록하지 않았다. 삼성전자외 원 행동 상속을 회귀 검증했다. |

짧은 체결 window를 다른 경로/REST로 채우지 않으며 모든 삼성전자 관측에10체결을 강제하는 새 전역 차단도 두지 않았다.10체결 완전성은 이 신규 연구 규칙의 원천 조건이다.

### 원천 재생의 정확한 범위

원519행의 **전체 captured feature/setup**을 사용했다. 외부 archive의 같은 원천시각10체결로 pressure·delta·첫끝 가격변화3값을 다시 계산해 결속했다. 조건 일치76행 중 원천 증명과 위험 계약을 통과한 신규 ENTER 제안은54행이다. 전체 source 유효는430행이다.54행은 중복 관측을 포함한다.

과거 archive의 collector epoch는 Main epoch와 다르므로 별도 historical receipt를 쓴다. `main_epoch_equivalence=false`, `native_promotion_support=false`다. 앞선 대사의9/29 불일치2건도 임의로 시각을 탐색해 맞추지 않았으며 새 규칙의 source 통과로 강제하지 않았다.

**과거 최신 snapshot의 모든 market/program/candle feature를 다시 만드는 작업은 완료하지 못했다.** 해당 시각의 완전한 feature-build 입력이 없어 원 전체 capture를 보존했다. 이번 source selector 구현의 과거 최신시각 성능이나 자연 운영 소비가 입증됐다고 표현하지 않는다. 선행3필드 부분 덮어쓰기 민감도와도 구분한다.

### 같은 점유 조건의 비교

한 종목의 가상 보유가 끝날 때까지 후속 신호를 건너뛰는60분 재생이다. augment는 기존 ENTER에 신규 제안을 추가하고, replace는 조건·원천·guard를 만족하지 않는 기존 ENTER도 RECHECK로 바꾼다.

| 날짜 | 기존 정책: 목표/손절/시간종료 | 유지+추가형 | 조건 교체형 |
|---|---|---|---|
| 9/29 | 3/4/0,42.86% | 6/5/1,54.55% | 4/3/1,57.14% |
| 9/30 | 0/1/0,0% | 2/2/0,50% | 2/2/0,50% |
| 10/2 | 0/0/2,승률 미산정 | 2/2/2+후속 부족1,50% | **4/2/2,66.67%** |

선행 연구의 순위 함수로9/29·9/30만 비교해 **replace**를 선택했다. 표본 기준은 각 학습일 선택4·목표/손절 확정3이며, 최소 날짜 Wilson 하한→최소 날짜 승률 개선→합산 승률 순이다. 이는 연구 선별 기준이며 새 운영 승인 조건이 아니다. 비교 날짜10/2로 mode를 재선정하지 않았다.

- 기존 ENTER38관측 중33관측을 제외할 수 있도록 했다. 기존 성공 보존율에 따른 탈락은 없다.
- 원10/2 선택8관측 중10:10과13:31은 `LIQUIDITY_FRAGILE`이 남아 승격되지 않았다. 나머지6개는 제안 ENTER지만 전체 신호를 다시 점유하면 다른 관측이 들어가므로 원8관측과 새8진입을 같은 집합으로 간주하지 않는다.
- 첫 부분 봉의 선도달이 불확실한 경우를 제외하면 교체형9/29는 목표2·손절2·시간종료1·불확실1이며 승률50%다.9/30과10/2는 위 결과를 유지했다.
- 원 native ID는9/29 선택0,9/30·10/2 각각 fixed-watch1개로 여러 관측이 반복된다. 이를 독립8기회로 늘리지 않았다.
- 10/2 비용 반영 가격경로 평균은 기존−0.2300%, 교체형−0.3079%다. 목표 도달 빈도 개선이 평균 수익 개선을 보장하지 않는다. 이 값을 실현 PnL이나 후보 자동 탈락 조건으로 바꾸지 않았다.

## 3. 삼성전자외: 세 기계 행동의 상승 통합

분모는9/29·9/30·10/2의 기존8,793행에서 삼성전자684행을 제외한8,109행이다. KRX 정규장6,550행, 장전994행, 장후565행이며 원 native group은 전체166개다. 가격·비용·exact request/venue/session을 결속했고 세션 경계를 넘지 않았다.

| 원 기계 행동 | 전체 관측 | 10분 이내 목표 선도달 | 10분 이후 목표 선도달 | 목표 선도달 합계 |
|---|---:|---:|---:|---:|
| ENTER_NOW | 317 | 67 | 55 | **122** |
| RECHECK | 5,555 | 1,107 | 797 | **1,904** |
| BLOCK | 2,237 | 448 | 278 | **726** |
| 합계 | **8,109** | **1,622** | **1,130** | **2,752** |

같은 전체 분모에서 손절 선도달은2,432행이다. 이 중1,085행은 손절 이후 목표까지 반등했고1,347행은 관측 범위에서 목표를 확인하지 못했다. 손절 후 반등을 목표 선도달 성공으로 바꾸지 않았다.

나머지는 첫 부분 봉 순서 불확실1,436·후속 가격 부족625·비용 결손857·동일 완전 봉 양 경계 도달7행이다. 합계8,109와 일치한다. 세션 종료 미도달0은 결손을 성공/실패로 채운 결과가 아니며, 자료 부족625행을 별도로 보존한 집계다.

### 10분 미도달2,968관측의 연장 평가

| 평가 종료 | 목표 선도달 | 손절 선도달 | 아직 미도달 | 후속 가격 부족 |
|---|---:|---:|---:|---:|
| 20분 | 518 | 555 | 1,702 | 193 |
| 30분 | 775 | 827 | 1,046 | 320 |
| 60분 | 1,017 | 1,104 | 377 | 470 |
| 같은 세션 종료 | **1,130** | **1,283** | 0 | 555 |

가격 간격90초 초과 이후의 최초 선도달은 확정하지 않았다. 간격 결손보다 먼저 확인된 경계는 유지한다. 이전 구현이 전체 경로를 `internal_price_gap`으로 둔155행을 대사해 목표45·손절30·동일 봉 불확실10을 복원했고, 나머지70은 자료 부족으로 남겼다.

1분 OHLC의 첫 봉이 판정 이전 구간을 포함하면서 경계에 닿으면 최초 도달 순서를 알 수 없다. 삼성전자외 본문 수치는 이를 **처음부터 불확실로 분리한 엄격 집계**다. 따라서 이전 단순 봉 순서 집계의 목표3,509행과2,752행을 혼용하지 않는다.

## 4. 상승·손절의 원천 패턴과 관측 유형

아래는 해당 값이 있는 행의 중앙값이다. 결과 분류는 사후 설명이며 진입 feature에 넣지 않았다. 반복 빈도·날짜·유형별 대조는 `patterns.json`에 함께 보존했다.

| 원천 지표 | 빠른 목표 | 늦은 목표 | 손절 후 반등 | 손절·목표 미관측 |
|---|---:|---:|---:|---:|
| 현재가−microVWAP(bp) | 2.745 | 1.825 | 3.120 | 4.780 |
| spread(bp) | 11.81 | 10.89 | 13.11 | 14.45 |
| fillability score | 72 | 77 | 64 | 64 |
| 매수압력(%) | 60.37 | 66.37 | 56.37 | 64.47 |
| 당일 가격범위(%) | 6.5245 | 5.051 | 6.916 | 4.909 |
| 원 비용(%) | 0.28905 | 0.28445 | 0.29555 | 0.30225 |

늦게 목표에 도달한 집합은 낮은 VWAP 이격·작은 spread·높은 fillability가 함께 나타났다. 매수압력 하나만으로 목표/손절이 분리되지는 않았다. 신뢰할 수 있는 pressure가 있는 목표 행은 **1,088/2,752**뿐이다. 결손을0으로 채우지 않았고, 종목별 거래량 규모가 다른 절대 delta를 공통 강도로 해석하지 않았다.

이전 학습 기준을 고정한 정규장 관측 유형도 비교했다. A는 spread≤48.219999bp·VWAP 이격≤30.869999bp, A1은 여기에 fillability≥60·당일 가격범위≤7%다. 산업 섹터나 종목의 고정 속성이 아니라 당시 관측 상태다.

| 유형 | 관측 수 | 빠른 목표 | 늦은 목표 | 손절 선도달 | 경계 확정 승률 |
|---|---:|---:|---:|---:|---:|
| A1 | 2,230 | 473 | 535 | 768 | 56.76% |
| A_other | 3,273 | 802 | 495 | 1,072 | 54.75% |
| B | 865 | 148 | 55 | 259 | 43.94% |
| C | 181 | 16 | 1 | 36 | 32.08% |

원천 결손 유형1행은 첫 봉 불확실이다. A1은 빠른 목표보다 늦은 목표가 많아10분 종료만으로 가능성을 평가하면 누락이 커진다. B/C는 첫 봉 불확실 비중도 크므로 위 확정 집합 승률을 전체 진입 승률로 해석하지 않는다.

BLOCK 목표726행 중714행에는 `large_sell_print_present`,11행에는 `adverse_distribution_no_edge`,2행에는 `failed_structure`가 있었다(위험 중복). 나중의 상승만으로 당시 guard를 제거하지 않았으며 아래 후보의 실제 선택 BLOCK은0이다.

## 5. 삼성전자외 후보와 민감도

결과 확인 전에 기존66개 가설·원천 hash·날짜 분할을 봉인했다. 후보 생성/선택부터 삼성전자를 제외했다.9/29·9/30 각20선택·경계 확정10·5종목 이상이며 양 날짜에서 parent보다 높은 승률인 후보를 최소 날짜 Wilson 하한과 최소 승률 개선 순으로 연구 선택했다. 이 연구 표본 기준은 운영 gate가 아니다.

선택된 **`pullback_p60_v0`**는 신뢰 가능한 매수압력≥60%, 순공격매수량>0, 현재가≤microVWAP 조건이다. 삼성전자 보합 규칙과 달리 첫끝 가격변화0을 요구하지 않는다. 원 source·invalidation·수치 liquidity 조건을 유지했다.

| 날짜 | 기존 정책 목표/손절 | 기존 승률 | 후보 목표/손절 | 후보 승률 |
|---|---|---:|---|---:|
| 9/29 | 49/43 | 53.26% | 51/29 | 63.75% |
| 9/30 | 12/19 | 38.71% | 24/12 | 66.67% |
| 10/2 | 20/13 | **60.61%** | 22/10 | **68.75%** |

10/2 후보는39종목·49선택이며 시간종료3·첫 봉 불확실5·비용 결손3·후속 부족6을 별도로 포함한다. 원 행동별로 ENTER3(목표2·비용 결손1), RECHECK46(목표20·손절10 포함), BLOCK0이다. 기존 ENTER 상승 원 관측21개도 조건에서 제외했지만 성공 보존율로 탈락시키지 않았다. 원21관측과 비중복 기존 목표20은 분모가 다르다.

리뷰 민감도:

- 10/2 전체 관측의393종목을 하나씩 제외한393회 비교 모두 승률 개선이 유지됐다: **+6.06~+11.08%p**. 후보가 선택한 종목은39개다. 후속 리뷰에서 반복 횟수 표기를 정정했으며 계산 artifact는 변경하지 않았다.
- 조건 적용 전에600초 간격으로 관측을 줄이면10/2는55.56→71.43%이나9/29는62.50→62.07%로 개선이 사라졌다. 반복 관측 선택의 영향이 남아 있다.
- 원 native 연결행만 쓰면 후보는9/29 목표3·손절2,9/30·10/2 선택0이다. 전체 관측에서 발견한 규칙과 실제 기회에 연결된 선정 증거를 구분해야 한다.
- 10/2 비용 반영 가격경로 평균은 기존−0.3230%→후보−0.2672%로 개선됐지만 여전히 음수다. 실제 주문/청산 수익은 아니다.
- 전체 위험 fact를 새 기계 규칙으로 처리하는 삼성전자외 evaluator 변환은 이번에 구현하지 않았다. 이 후보는 관측 필터 연구이며 기존 기계에서 ENTER가 실제로 늘었다는 증거는 아니다.

## 6. 리뷰·검증과 다음 검증 경계

수정 후 재리뷰에서 동시 구독의 aggregate 시각을 exact-route 시각과 비교하던 문제, 원 session 소문자 정규화, receipt 소비자의 route/clock/epoch 직접 검증을 보완했다. 짧은 window·미래/교차경로/교차epoch·locked 제출 거절·다른 종목 상속·모든 위험 보존·report-only validator·첫 봉/가격 간격·success 보존 veto 부재를 회귀했다.

- 표적 pytest **202 passed**: 신규 원천/recipe, entry snapshot, feature packet, confirmation research, engine location gate, 비삼성 가격경로 연구 테스트.
- 영향 Python compile, `git diff --check`, 문서 링크/실행 owner, print-only 문서 parser 검증. 전체 매매 suite·canonical 장후 재생성·외부 문서 동기화는 실행하지 않았다.
- 원519행 parent 일치, 이전47개 source seal(변경한3개 kernel은 보존한 baseline 사본), 새 kernel hash, 비삼성8,109행과 원천/가격/output seal을 검증했다.
- 공식 Kiwoom HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, 확인시각 `2026-10-04T21:00:09+09:00`. `kiwoom_docs` 부재를 기록하고 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/realtime/{packets,decoders,stream}.py`, packaged API spec, Postman을 확인했다. wire/parser/FID/auth/REG/order 변경은 없다. 상세 경로/hash는 아래 receipt에 있다.

다음 연구는 고정한 비삼성 후보의 원 risk ledger와 실제 evaluator 제안 행동, 원 native 연결을 대사하는 것이다. 삼성전자는 구현한 원천 receipt의 실제 producer→consumer 확인과 완전한 입력이 있는 시각의 동일 함수 재생이 필요하다. 새로운 임계값 탐색이나 수집 확대를 먼저 요구하지 않는다. 독립 날짜 성능·자연 실행·실현 경제성은 미입증으로 남긴다.

## 7. 재현 자료

- [삼성전자 최종 재생 결과](../../tmp/samsung-flat-buy-flow-implementation-20261004/final-v4/result.json), [원천·위험별519행](../../tmp/samsung-flat-buy-flow-implementation-20261004/final-v4/decisions.json), [학습 mode 선정·첫 봉 민감도](../../tmp/samsung-flat-buy-flow-implementation-20261004/final-v4/selection-review.json).
- [비삼성 결과/관측기간](../../tmp/non-samsung-machine-horizon-20261004/result.json), [전체 관측](../../tmp/non-samsung-machine-horizon-20261004/observations.json), [원천 패턴](../../tmp/non-samsung-machine-horizon-20261004/patterns.json), [66후보/선정](../../tmp/non-samsung-machine-horizon-20261004/candidate-results.json), [민감도](../../tmp/non-samsung-machine-horizon-20261004/review-sensitivity.json), [사전 계약](../../tmp/non-samsung-machine-horizon-20261004/frozen-contract.json).
- [공식 API 확인 receipt](../../tmp/samsung-flat-buy-flow-implementation-20261004/official-reference.json), [최종 검증 receipt](../../tmp/samsung-flat-buy-flow-implementation-20261004/validation.json).
- 실행 owner: [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `SamsungFlatBuyFlowImplementation1004`, `NonSamsungMachineHorizonUnion1004`. 기존10/6 자연 수용 owner는 변경하지 않는다.
