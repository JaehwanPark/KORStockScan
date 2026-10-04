# 삼성전자 호가 회복·흡수 지속 후속 연구계획

Owner: `SamsungQuoteRecovery1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [진입 시점 분리 결과](../audits/samsung-event-timing-isolation-and-exit-research-review-2026-10-04.md).

## 1. 질문과 범위

사용자 후속 연구 지시에 따라 기존9/29·9/30·10/2 체결·호가에서 실제 bid/mid 회복과 매도 물량 흡수 지속을 확인한다. 체결가500원 상승에 spread 내 체결 위치 변화가 섞였다는 선행 결과를 보존한다. 신규 수집·API/provider 호출·실시간 조건·정식 정책 발행·배포·재기동은 없다.

새 producer는 `src/engine/scalping/samsung_quote_recovery_research.py`에 둔다. 기존 보관 원천을 읽는 독립 오프라인 scalping 연구이며 기존 연구 kernel과 결과를 변경하지 않는다. `src/engine` root에 파일이나 compatibility wrapper를 만들지 않는다. Kiwoom request/parser/FID/REG/authentication을 변경하지 않는다.

## 2. 결과를 보기 전에 고정한 가설

모든 신호는 원래 매도 충격 후180초 안에 관측한 최초 적격 체결 수신 시점이다.500원은 공식 호가단위를 인증하지 않는 고정 연구 가격 경계다.

| 가설 | 과거 정보로 확인할 조건 |
|---|---|
| `bid_recovery` | 사건 이후 관측된 bid 저점보다 현재 bid가500원 이상 상승 |
| `mid_recovery` | midpoint 저점보다500원 이상 상승, 그 저점의 bid보다 현재 bid도 상승, spread가 저점보다 확대되지 않음 |
| `sustained_bid` | bid 회복이 연속2초 이상 유지되고 서로 다른 유효 depth 관측3개 이상 존재 |
| `absorption_then_bid` | 최근5초 동안 bid가 같고 SELL량>BUY량, SELL 체결3개 이상·유효 depth3개 이상인 흡수 유사 구간을 먼저 확인한 후, 그 bid보다500원 이상 회복하여2초 지속 |

흡수는 가격이 유지되는 동안 매도 체결이 우세했다는 관측 가설이다. 특정 주체의 호가 보충이나 실제 주문 체결을 입증하지 않는다. 최신 quote는 체결 수신 시각보다 **엄격히 이전**, 같은 collector epoch, age≤1.5초여야 한다. 서로 다른 stream의 같은 timestamp에는 공통 sequence 순서를 가정하지 않는다. 원천 단절/invalid 최신 quote에서 지속/흡수 상태를 초기화하며 과거 저점까지 연결하지 않는다. 원래 사건 이후 trade flow 단절은 해당 사건 연구를 종료한다.

## 3. 사건 분모와 진입·종료 가격

- 선행 봉인 캐시의1,026개 원래 shock identity를 재사용한다. 전체 사건의 신호 발생 census와, 겹침을 제거한 결과 평가를 분리한다.
- 결과·가설 신호 유무를 보기 전에 shock 시간순 첫 사건을 고르고 shock 시작부터842초를 예약한다. 모든 가설은 같은 anchor universe를 사용한다. 신호 없음은 `not_reached`, 원천 단절은 `source_gap`; 미진입을 손실이나 net0으로 만들지 않는다.
- 비교 기준은 **선행 연구의 최초 체결가500원 회복**이며 현재 Main 정책을 재생했다고 부르지 않는다. 기준·새 신호 모두 BUY 가격은 과거 유효 ask, SELL 결과는 이후 유효 bid다. 비용0.33%·순목표+0.1%·gross stop−0.7%를 고정한다.
- 주 paired 비교는 기준 entry+600초의 같은 절대 종료 시각·같은 사건·같은 비용/가격 기준을 쓴다. 새 신호 자체의600초 결과는 별도 표로 유지한다. 확인 지연과 admission 필터 효과를 구분한다.
- quote 결과는 invalid 행을 식별해 제외한 유효 bid 관측 경로다. 원래 depth sequence/epoch 연속성, 유효 관측 간 최대1.5초, 시작/종료 freshness, trade 가격 경로 연속성을 요구한다. 알려진 경계 도달 뒤 결손은 별도 진단에 남기지만 주 비교에서는 전체 경로 기준을 적용한다. 모든 raw quote가 valid인 엄격 경로도 민감도 결과로 함께 표시한다. 짧은 제외 구간에서 가격을 보간하거나 모르는 목표/손절 도달을 만들어내지 않는다.
- 미도달 binary는null이고, 고정 종료 관측가격 CF는 실제 체결/PnL/EV가 아니다. full path·known terminal·censored·no signal을 분리한다.

## 4. 학습과 비교 판단

9/29 학습→9/30 후단,9/29~30 학습→10/2 후단으로 고정한다. 이미 탐색한3일 자료여서 독립 holdout이 아니다. 지원수는 research event이며 Main native opportunity를 합성하지 않는다.

진입 필터 효과와 시점 효과를 분리한다. 시점은 양쪽이 진입한 같은 사건의 paired 비교다. 필터를 포함한 전략 비교 universe는 기준 결과가 유효하고 새 가설 결과도 유효하거나, 결손 없이 새 가설이 미도달한 사건이다. 새 신호가 결손이어서 없었던 사건은 의도적인 veto로 계산하지 않는다. 기준은 universe 전체·새 가설은 실제 적격 신호만의 조건부 승률이며 미진입 결과를0 PnL로 넣지 않는다.

훈련 paired source-comparable≥3 및 전략 비교 양쪽 binary 지원≥3일 때 새 가설의 조건부 승률이 기준보다 높으면 연구 후보로 선택 가능하다. 순위는 승률→Wilson 하한→지원수→단순성이다. 기존 성공100%/80% 보존 veto, 기존 성공 상실 자체의 탈락 조건, mean CF 양수 조건을 후보 탈락 조건으로 두지 않는다. 대신 누락/coverage·목표 도달 비율·평균 CF·tail·기준의 잃은/얻은 목표를 보고한다. 더 나은 가설이 없거나 비교 승률이 불명확하면 `not_selected`이며 전체4개 가설 진단은 보존한다.

현재 연구는 진입 특징을 검증한다. EXIT threshold grid나 정식 정책 재생성은 실행하지 않는다. 후속 구현 필요성은 결과의 효과·표본·원천 충분성을 분리해 판단한다.

## 5. 완료 조건

봉인된 입력/기존 정책·인계 파일 보존, 과거 정보·stream 순서·가격 기준·동일 사건 분모·결손 분류 회귀, 구현→리뷰→수정→재리뷰→표적 pytest/compile/diff, 후보 재실행 일치, 문서 link/owner·print-only parser를 완료한다. 결과와 다음 가설을 별도 audit에 남긴다. 이전10/4 완료 항목과10/6 기동 owner를 보존한다.

## 6. 원천 신호 census 이후·결과 계산 이전의 보충 범위

고정 shock anchor25/26/27개에서 호가 회복 신호8/3/2개였다. 이 신호 census는 가격 결과나 승패 계산이 아니다. 신호 없는 첫 shock의842초 예약 때문에 적격 신호의 실제 참여가 충분히 반영되지 않을 수 있어 다음을 추가 고정했다. 가격/승패 결과를 확인한 뒤 가설을 바꾸지 않는다.

- 원래1,026개 사건 전체의 결과 진단: 겹치는 결과창을 포함한 반복 관측으로 표시하고 학습/독립 지원수에 사용하지 않는다.
- 보충 실제 신호 순서 비교: recipe의 최초 적격 수신 시각 순으로 고르고, 기준/새 신호 중 더 이른 시작이 직전 예약 종료 이후인 사건만 평가한다. 예약은 둘 중 더 늦은 entry+601.5초이며 결과가 결손이어도 다음 성공 신호로 대체하지 않는다. 이 비교는 같은 사건의 시점 효과이며 신호 없는 모집단을 포함한 admission 정책 승률이라고 부르지 않는다.
- 주 고정 anchor 결과와 보충 신호 순서 결과를 모두 남긴다. 네 가설·원래 날짜·비용·가격 기준·학습 선택 조건은 유지한다.

## 7. 첫 경로 계산 후의 제한된 보충 가격 진단

### 잠금호가 관측 가격 민감도

원천 대사에서 유효 quote 간 긴 간격은 주로 bid==ask 관측 제외로 발생했다. 로컬 `forward_collector.py`와 `MarketDepthPoint`, `coverage_tier_for`는 best_ask>=best_bid를 허용하고 연구 reader만 strict bid<ask를 요구한다. broker parser나 FID를 변경하지 않는다.

strict 연구를 보존하고 별도 `--include-locked-price-context` 원천/결과에서, 같은 양수 bid==ask이고 exchange/receive clock0~5초인 기존 관측만 가격 진단에 포함한다. crossed/nonpositive/clock/sequence/epoch 결손은 유지한다. 동일4가설·학습 선택·비용·겹침 기준을 재계산한다. 잠금호가의 실제 주문 가능성·거래소별 execution route/수량·실제 체결은 입증하지 않으며 이 민감도 후보는 오프라인 연구에 한정한다. 별도 source hash·validity 계약과 strict 차이를 결과에 남긴다.

첫 계산에서 quote 경로의 유효 관측 간1.5초 초과 구간 때문에 자체600초 full path가 없었다. 실제 source 단절/잠금호가 원인을 먼저 대사하고, 전체 경로가 필요한 목표-first와 세 지점만으로 가능한 고정 종료 가격 진단을 구분한다.

동일 사건의 과거 ask 진입 두 개와 기준 entry+600초의 신선한 bid 종료, 그 구간의 trade 가격 경로만 유효하면 고정 종료 가격 차이를 계산한다. 중간 quote 결손으로 목표/손절 순서를 알 수 없어도 이 세 지점 가격 차이는 관측 가능하다. 이를 target-first 지원·정식 정책 선택·실제 승률이나 PnL로 바꾸지 않는다. 원래 네 가설·원천 source gate·학습 선택·미선정 결과는 유지하며 보충 metric은 선택에 사용하지 않는다.
