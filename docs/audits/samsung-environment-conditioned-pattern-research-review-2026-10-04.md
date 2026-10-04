# 삼성전자 환경·수급 조건부 패턴 연구 결과 및 리뷰

Owner: `SamsungEnvironmentConditionedResearch1004`, [실행계획](../proposals/samsung-environment-conditioned-pattern-research-plan-2026-10-04.md), [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).

## 1. 결론

보유 원천을 더 소비하면 **학습 승률이 개선되는 조건은 발견된다**. 그러나 이번에 학습에서 고정한 가격 후보는10/2에서 손실이었고, Main 원 binary 승률이 개선된 환경 단독 veto는10/2의 선택 진입이0건이다. 새 운영 정책의 우위를 입증하지 못했다. 이는 상승 패턴0건 또는 수급 데이터 무정보라는 뜻이 아니다.

- 가격 연구: `absorption_release:300:5|program_delta=flat|barrier` 학습3/3 양수·CF +0.13765%, 무조건 동일 신호는2/3·CF −0.22711%. 후단은0/1·CF −0.59232%로 재검증 실패.
- Main 원 native-group 연구: `parent_only|foreign=up|veto` 학습66.67%(2/3), 기존50%(3/6). 기존 양성1건을 제거했지만 성공 보존 veto로 탈락시키지 않았다. 후단 선택0건·비교 승률null.
- 이번 연구는51조건 ×24신호 ×3종료 =3,672개 가격 조건과3,723개 Main adapter를 계산했다. 종목 방향·프로그램·투자자·이전 발행 breadth를 소비했다. 외부 intraday 지수/업종 비교는 원천이 확인되지 않아 실행하지 않았다.
- 이어서 실제 과거 프로그램 endpoints의60/180/300/900초4모델과state_failure 종료까지1,272개 가격 조건·1,961개 Main adapter를 추가 계산했다. 총 계산은4,944개 가격 조합이며 중복 baseline·상관된 가설을 포함한다. 연속 변화 연구에서도 운영 후보는 미확보다.
- `official_policy_candidate=null`, 정책 발행/주문/API/provider/수집 확대/배포/기동 변경0. 기존 Main·Widget·Episode 및10/6 인계를 유지한다. 현재 PID 적용을 새로 주장하지 않는다.

## 2. 새로 소비한 원천과 결손의 의미

원 capture의 path·physical hash·물리행·canonical trace를 기존519개 projection과 정확히 대사했다. 프로그램과 투자자 source의 관측 시각·original expiry·recorded age·날짜·request item·snapshot route를 재검증했다. 통합 `_AL` 수급은 당시 capture 문맥이며 KRX 단독 체결로 재분류하지 않았다.

| 일자 | Main capture | 프로그램 source 유효 | 투자자 source 유효 | 프로그램 실제 join | 투자자 실제 join |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9/29 | 313 | 313 | 15 | 257 | 14 |
| 9/30 | 46 | 46 | 46 | 44 | 44 |
| 10/2 | 160 | 160 | 160 | 154 | 154 |
| 합계 | 519 | 519 | 221 | 455 | 212 |

source 유효와 join 가능은 다르다. 원 projection의 stream epoch/valid가 없던56/2/6건은 수급을 가격 문맥에 연결하지 않았다. 투자자 결손298건은9/29 원 capture의 값 부재이며, 이후 응답이나 장후 값으로 소급 채우지 않았다. 유효 투자자 값에는 외국인·기관 순매수/순매도 변화가 있어 모든 값이0인 원천은 아니다.

연속 가격 frame51,604개에 과거 capture를 붙일 때는 capture 이후부터 source 관측 시각 기준60초 이내까지만 사용했다. source clock보다 늦은 capture clock으로 expiry를 연장하지 않았다. 유효 source가 있어도 sparse capture 사이의 긴 시간은 unknown이다.

| 분류 | 사용할 수 있는 frame | 전체 대비 |
| --- | ---: | ---: |
| 종목300초 방향 | 41,229 | 79.90% |
| 종목900초 방향 | 27,553 | 53.39% |
| 프로그램 수급 | 17,381 | 33.68% |
| 투자자 수급 | 10,443 | 20.24% |

방향 결손은 연결된 과거300/900초 창이 없는 경우다. 수급 결손은 주로 기존 capture가 드물거나 expiry를 지난 경우다. 이 비율을0 수급/중립/0 EV로 바꾸지 않았다. frame은 상관된 관측이며 독립 기회 지원수로 세지 않았다.

### 외부 환경

- exact519 capture의 `entry_candle_context.market_context`·`sector_context`는 모두 부재다. 기존 지수 자료는6~8월 범위이고, dated stock master는 지수 시세가 아니다. 최신 시장 cache의10/2 19:48 값을 당일 장중으로 대입하지 않았다.
- 이미 발행된 일일 report는 별도로 사용할 수 있었다. 이는 **우량주 pool의 이전 일자20일선 breadth**, 전체시장이나 intraday KOSPI 방향이 아니다. 원 생산자의40/60% 경계를 그대로 썼다.
- 9/29 당시 최신9/28 report는quote_date9/23으로 고정72시간 age를 초과해 제외했다. 9/30에는9/29 19:37 report의9/28 시세·breadth39.0%,10/2에는9/30 20:50 report의9/29 시세·34.9%를 사용했다. 둘 다하락 분류다.
- 따라서 이 자료만으로 **상승장/중립장/하락장의 차이를 식별할 수 없다**. 후단이 하락 prior-breadth인 것은 알지만, 다른 환경 대비 검증 결과라고 말할 수 없다. 업종 상대강도·intraday index divergence 가설은 미실행이다.

## 3. 가격 후보 계산 결과

학습9/29·9/30에서만 고정 조건을 선택했다. 같은 state 정의와 종료 모델의 무조건 전략을 baseline으로 비교했다. 비용0.23%, ask 진입/bid 종료, net 목표+0.1%·gross stop−0.7%·최대20분, 종료 이후60초 cooldown을 유지했다. 미확정 terminal 뒤에는 추가 입장을 막았다. time600/1200 종료도 같은 방식으로 계산했다.

| 가설군 | 계산 조건 | 학습3확정·양일 지원 | baseline 대비 승률 개선 | 개선+평균 net CF 양수 |
| --- | ---: | ---: | ---: | ---: |
| 무조건 baseline | 72 | 8 | 해당 없음 | 해당 없음 |
| 종목 상승/중립/하락 | 432 | 11 | 2 | 0 |
| 프로그램 누적/변화/전환 | 576 | 6 | 1 | 1 |
| 투자자 수급 | 648 | 0 | 0 | 0 |
| 과거 VWAP 위/아래 | 288 | 15 | 3 | 0 |
| 과거 range 비용 여유 | 72 | 0 | 0 | 0 |
| 종목 방향×프로그램 | 648 | 0 | 0 | 0 |
| 프로그램×smart money | 72 | 0 | 0 | 0 |
| 이전 발행 breadth·종목 조합 | 864 | 0 | 0 | 0 |

후보를 탈락시킨 성공 보존 조건은 없다. 투자자/조합 가설의0은 효과 부재가 아니라 sparse availability·신호 교집합·양일 지원 부족이다. Main 승률 선택에는 net EV veto를 추가하지 않았고, 이 표의 양수 net CF는 **운영 가능한 가격 수익 패턴을 찾는 별도 연구 shortlist**의 조건이다.

### 학습 선정 후보와 후단

| 대상 | 시도 | 확정 양수/확정 | 검열 | 평균 net CF |
| --- | ---: | ---: | ---: | ---: |
| 9/29 후보 | 3 | 2/2 | 1 | +0.13866% |
| 9/30 후보 | 1 | 1/1 | 0 | +0.13563% |
| 학습 후보 합계 | 4 | 3/3 | 1 | +0.13765% |
| 학습 무조건 baseline | 5 | 2/3 | 2 | −0.22711% |
| 10/2 고정 후보 | 1 | 0/1 | 0 | −0.59232% |
| 10/2 무조건 baseline | 3 | 2/2 | 1 | +0.13563% |

`program_delta=flat`은 **당시 최신 프로그램 delta_qty가0**이라는 조건이며 결손 또는 프로그램 순매수 전체0이라는 뜻이 아니다. 학습에서는9/30 손실 신호를 제외했지만10/2에는 baseline의 확정 양수 신호2개를 모두 제외하고 뒤의 새로운 손실 신호1개를 admitted했다. 초기 사건을 성공할 때까지 기다려 바꾼 것이 아니라 당시 조건으로 state 신호를 필터하고 기존 terminal/cooldown 규칙을 재생한 결과다.

실행된 신호의 retained/removed/added 대사:

- 9/29: 공통1·제외1·새 입장2, 새 양수1. 앞선 불명 terminal 신호를 조건으로 제외하면 뒤의 원래 신호가 모델 입장 가능해졌다.
- 9/30: 공통1·제외2·새 입장0.
- 10/2: 공통0·제외3·새 입장1, 기존 양수2 제외·새 양수0.

전 기간 합계는 사후 audit이며 선정에 쓰지 않았다. 후보 확정 승률75%(3/4), baseline80%(4/5). 후보의 평균 net CF −0.04484%, baseline−0.08201%. CF 손실폭은 작아져도 승률 우선 목적의 개선을 주장할 수 없다. 비용0.33%에서10/2 CF는−0.69232%,1초 지연에서도−0.59232%로 후단 결론은 동일하다. 모두 관측 가격 CF이며 Widget 실현 수익·실제 Main 체결/PnL과 합산하지 않았다.

## 4. Main 기존 정책과 직접 비교

원 binary·원 비용·원 native-group estimand로24상태×51환경×3 adapter =3,672개를 계산했다. 리뷰에서 신호의 제약을 분리하기 위해51개 parent ENTER 환경 단독 veto를 더했다. 최초 가격 재생 이후 추가한 탐색 보완이며 pristine holdout이 아니다. unknown 조건은 parent를 유지하고 환경 단독 veto가 BLOCK/RECHECK를 승격하지 않는다.

- baseline 학습6 native group 중3승,50%. 환경 단독 `foreign=up` 학습3 group 중2승,66.67%. support-adjusted 승률은22.126→25.353%로 +3.227%p다.
- 이 후보는 기존 양성3건 중2건을 선택한다. 양성1건 감소를 보존 veto로 탈락시키지 않았다. 학습 지원 날짜는9/29뿐이다.
- 10/2 foreign는0 또는음수라 기존 ENTER3건을 모두 제외했다. 후보 선택0건·승률null. baseline ENTER3건도 원 binary가미도달이므로 후단 baseline 비교 승률은null이다. **결과가 좋은 정책을 보존하겠다는 탈락 조건이 아니라 비교할 확정 결과가 없다는 사실**이다.
- trace 분모에서는 `program_delta=flat` 단독 veto가 학습5/7,71.43%이지만 native 집계와 다른 분모다. 후단 선택0건이므로 운영 개선 증거가 아니다.
- 원native 상한은 학습16/후단1, 현재 publisher는30/10을 요구한다. 공식 발행 적격성이 없지만 이 floor 때문에 가격 연구를 중단하지는 않았다. synthetic native 지원을 만들지 않았으며 현재 Main 정책을 바꾸지 않았다.

## 5. 리뷰·검증과 재현성

새 오프라인 module만 추가하고 기존 sealed kernel/live producer·API parser·정책/인계는 수정하지 않았다. 리뷰에서 optional clock 예외/route suffix의 독립 검증, native metric key, optional breadth 불량 입력의 국소 제외를 보완했다. 환경 단독 parent veto와 선택 신호 대사를 추가해 상태 신호 제약과 환경 효과를 분리했다. 내부 field/rule text는 English ASCII다.

- 232 표적 tests: 두 새 연구와 기존 state/price/opportunity consumer. 미래 capture, source expiry 연장, route/item/date/epoch, missing/0 구분, past quote continuity, train-only 선택, 성공 보존 veto 부재, optional external source 격리 및 강제 report-only authority를 확인했다. 프로그램 동일clock 충돌의 격리 지속 및 과거 endpoint 간격이 최신expiry를 연장하지 않는 것도 검증했다.
- 실제 source9 prefix·77,412 frame 분류 비교: 미래 체결/호가/capture를 제거해도 동일했다. 이는 중복 prefix 비교수이며 신규 독립 기회수가 아니다.
- compile·diff 검사와 local link/owner·print-only parser를 실행했다. 기존10/6 parsed owner23개를 보존한다. Project/Calendar sync는 실행하지 않는다.
- 최종 증거는 아래 accepted generation과 validation closure다. 초기 `cold/`는 리뷰 보완 이전의 탐색 결과이며 final source seal로 재사용하지 않는다. 초기 kernel/plan snapshot은 `review-initial/`에 남겼다.

근거 위치:

- [최종 result](../../tmp/samsung-environment-conditioned-research-20261004/accepted-cold/result.json)
- [source census·원 capture·조건별 Main 원 outcome](../../tmp/samsung-environment-conditioned-research-20261004/accepted-cold/source-census.json)
- [가설군별 처분](../../tmp/samsung-environment-conditioned-research-20261004/validation/hypothesis-disposition.json)
- [실제 source 인과성](../../tmp/samsung-environment-conditioned-research-20261004/validation/accepted-causal-prefix.json)
- [프로그램 구간 변화·종료 결과](../../tmp/samsung-environment-conditioned-research-20261004/accepted-sequence-cold/result.json)
- [프로그램 모델별 처분](../../tmp/samsung-environment-conditioned-research-20261004/validation/sequence-disposition.json)
- [최종 검증 receipt](../../tmp/samsung-environment-conditioned-research-20261004/validation/closure.json)

## 6. 이어서 실행한 구간 수급 변화·효력 소멸 가설

[보완 실행계획](../proposals/samsung-program-sequence-research-plan-2026-10-04.md)에 따라 별도 오프라인 producer로 실행했다. 기존 환경 연구의봉인kernel/plan은 유지했다. 동일 snapshot 반복을 독립 관측으로 세지 않고, 시각역전·counter감소·gap·epoch 단절 및동일clock 다른값을 격리했다.

60초 비교 간격에서는9/30·10/2의 distinct endpoints가 이어지지 않았다. 따라서 최신source의60초expiry와 과거 endpoint 비교창을 구분해180/300/900초 모델을 더 검증했다. source를 stale 상태로 쓰거나 빈 구간을 보간하지 않았으며 **구간 평균 변화**로만 해석한다. coarse 모델을 added한 것은 이미60초 결과를 본 뒤의 탐색 보완이다.

| 과거 endpoint 최대 간격 | 9/29 변화/3점rate frame | 9/30 변화/3점rate frame | 10/2 변화/3점rate frame | 학습 양일·3확정 지원 조건 | 승률 개선 | 개선+평균netCF양수 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 60초 | 4,959 /2,308 | 0 /0 | 0 /0 | 0 | 0 | 0 |
| 180초 | 6,640 /5,299 | 1,625 /951 | 5,250 /3,862 | 9 | 2 | 0 |
| 300초 | 7,139 /6,294 | 2,116 /1,956 | 6,825 /6,415 | 8 | 4 | 0 |
| 900초 | 7,216 /6,567 | 2,116 /1,956 | 6,918 /6,624 | 8 | 4 | 0 |

각 모델13조건×12신호×2종료312개와공통baseline24개다. 학습25조건은지원이있었고10계산조합은승률이개선됐지만평균netCF양수는0이어서가격shortlist는없다. 모델간같은사건을중복포함하므로10개독립패턴이라는뜻이아니다. state_failure도실제운영exit계약으로치환하지않았다.

Main은 `parent_only|past_gap_180|program_change=down`이학습native5개중3승,60%로기존50%보다높았다. support-adjusted는22.126→27.248%,+5.122%p다. 원binary승률만으로rank했고net EV veto는없다. 후단은기존3ENTER가그대로남아모두원binary미도달이므로비교승률null이다. publisher30/10지원을충족하지못하고실제정책우위를입증하지못했다. 캡처과거2prefix×3일×4모델24비교도일치했다.

## 7. 종료 범위

계획한 환경 부호·종목 방향·수급 교집합·구간 수급 변화·효력 소멸 가설을 학습 고정과 후단 재생까지 완료했다. 이번 가용 원천으로 구별되는 이 가설군에서는 운영 유효 후보를 확보하지 못했다. **학습 개선은 발견됐으며 재검증 또는 비교 지원이 부족했다**는 결론이다. 삼성전자 데이터를 삼성전자 외 정책에 섞지 않았다.

intraday 외부 지수/업종 상대강도 및 상승/중립/하락 간 효과는 현재 원천에서 검증하지 못해미실행으로유지한다. 자료가없는영역을추가숫자튜닝으로채우거나전체접근법의효과부재라고주장하지않는다. 추가raw수집을요청/실행하지않았으며이번가설군의리뷰·검증작업은완료한다.
