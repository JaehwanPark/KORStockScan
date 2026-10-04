# 삼성전자 장전 확인 조건 분해 연구 실행계획

## 1. 질문·소유·범위

사용자의 `상세연구계획을 수립하고 실행하라` 지시를 실행한다. 선행 [Main/Widget 대조](../audits/samsung-fixed-watch-evaluation-and-owner-comparison-review-2026-10-04.md)에서 발견한 장전 Main 판정의 확인 조건을 연구한다. 실행 owner는 [오늘 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `SamsungPremarketConfirmation1004`다.

구현 위치는 기존 오프라인 연구 역할의 `src/engine/scalping/samsung_premarket_confirmation_research.py`, 회귀는 `src/tests`다. 선행 봉인 코드·계획·보고서를 변경하지 않는다. 보유9/29·9/30·10/2 자료만 읽고 새 `tmp/samsung-premarket-confirmation-20261004` generation에 출력한다. API/provider·수집·주문·정책 발행·배포·재기동은 실행하지 않는다. 삼성전자 외·보조판정·일반 종료 grid 탐색은 이번 조작 대상이 아니다.

## 2. 원천·분모·확인 원인

1. 3일의 원projection에서 삼성전자 `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE` 전부를 census한다. 현재 발견량은0/3/2관측이다. 관측 부재, valid-empty, 결함 제외를 구분한다.
2. 원AI payload archive의 canonical machine hash·trace·clock·bundle·raw quote/current/features를 exact 대사한다. 개별 식별 가능한 결함은 exclusion ledger로 남긴다. 누락/충돌된 전역 parent·봉인 manifest는 실행을 차단한다.
3. 원bundle의 **장전 scope parent**로 판정을 재계산해 원action/reason을 재현한다. 정규장 policy를 장전에 대입하지 않는다. `source_usable`, 완성봉 수, phase/family, micro delta/가격 변화, 미보상 risk, liquidity/local-breakout/entry-situation veto를 기록한다.
4. `no_supported_setup`은 유효 원천에서 허용 setup이 성립하지 않은 경우인지, `micro_continuation_unconfirmed`는 양수 매수/가격 반응 뒤 추가 확인이 없는 경우인지 구분한다. 유효한0값은 결손이 아니다. 1초 depletion feature의 체결 근거·refill 및 과거5/15초 bid 연속성도 함께 소비한다.
5. `NXT_PREMARKET/005930_NX` 보관 체결·호가만 별도 가격 진단에 사용한다. `_AL`은 `_NX`를 대체하지 않는다. 캡처 transport epoch와 archive sequence epoch는 다른 식별 공간이며 같은 epoch라고 주장하지 않는다. archive 내부의 clock/sequence/epoch를 지킨다.
6. projection census와 원archive census를 별도로 대사한다. 발견한10/2 08:33 원capture는 setup family/state validation 오류가 있어 원producer가 제외한 행이며, local-breakout 확인 조건을 해제해 표본에 넣지 않는다. 상시감시 identity는 원watch3필드로 대사하며 사용하지 않는 scanner ID의 null sentinel을 native 충돌로 해석하지 않는다. 이 보완은 연구 consumer에만 적용하고 원projection·live kernel을 수정하지 않는다.

## 3. 사전 고정 유한 가설

공통 envelope는 원parent RECHECK이며 미보상 위험이 기존 soft confirmation fact에만 한정된 행이다. BLOCK·source/liquidity/large-sell/구조/entry-situation/local-breakout 등 다른 guard는 승계한다. 새 fact를 production setup에 삽입하지 않고 오프라인 마스크만 계산한다.

| ID | 확인 조건 | 단일 비교점 |
| --- | --- | --- |
| soft_only_bound | soft 확인만 해제 | 필요 확인 없이 열었을 때의 진단 상한; 선정 제외 |
| positive_micro | 기존 신뢰 매수 delta 및10틱 가격 변화 양수 | 원micro 입력의 확인 grammar를 대체하는 기준 가설 |
| nonnegative_price | 위 조건에서 가격 변화≥0 | positive_micro의 가격 부호1개 변경 |
| bid_rise_5 | positive_micro + 과거5초 bid 상승 | positive_micro에 호가 연속성 추가 |
| bid_hold_5 | 위 bid 상승을 비하락으로 변경 | bid_rise_5의 bid 부호1개 변경 |
| bid_hold_15 | bid_hold_5의 과거창15초 | 창1개 변경 |
| nonnegative_bid_hold_5 | bid_hold_5의10틱 가격 변화≥0 | 가격 부호1개 변경 |
| trade_backed_1 | 매수 delta +1초 ask 소진 체결근거≥50%, 소진>0, 하향 재호가 없음 | positive_micro의 가격 반응을 체결 근거로 대체 |
| trade_backed_refill_half | trade_backed_1 + refill≤50% | refill 조건1개 추가 |

매수 delta는 exact parent의 원최솟값을 유지한다. 양수/비음수 가격을 반영해볼 뿐 adverse flow·신뢰성·stale를 해제하지 않는다. native 반복관측은 원watch/date cluster다. 성공100%/80% 보존을 탈락조건으로 쓰지 않는다.

## 4. 동일 가격·비용·종료 실험

- **Main 판정 panel:** 각 원stamp의 원ask를 유지한다. 원scope 비용·원binary label을 별도로 보존한다. archive 과거ask가 원ask와 다르면 `captured_quote_mismatch`로 CF만 결손 처리한다. 모든 마스크는 동일한 행의 같은20분 barrier, 비용0.23%, net target0.1%, gross stop−0.7%, ask 진입/bid 종료 결과를 참조한다. exit/가격/비용을 후보별 변경하지 않는다.
- **연속 가격 panel:** 기존 archive의 첫 유효 체결/초 grid에서 같은 가설을 계산한다. 최근10체결의 신뢰 delta/가격, 과거5/15초 bid, 과거1초 같은ask 소진·BUY 양을 past-only로 계산한다. 이것은 Main setup 전체를 재생하지 않는 시장 자료 진단이며 generic Main native로 올리지 않는다. 캡처1초 feature와 재구성 feature의 의미·clock을 혼동하지 않는다.
- 모든 가설의 비중첩 모델 진입은 최초 충족 신호이며 원native와 별도로 기록한다. 검열된 모델 보유는 뒤 진입을 보류한다. full-fill/실현PnL gate를 가격 진단에 추가하지 않는다.
- 주모델은 최대 quote gap1.5초. 기존10초 관측 민감도는 사전에 고정하고 선정에 쓰지 않는다. invalid/sequence/epoch break를 gap 완화로 연결하지 않는다. 미도달·검열·결손은 실패나 손익0으로 치환하지 않는다.

## 5. 선정·성능·종료

9/29·9/30에서 조건 registry와 선정 결과를 고정한 뒤 이미 반복 탐색한10/2를 후단 진단으로 재생한다. 이는 pristine holdout이 아니다. 원parent ENTER가0이면 기존 Main 승률은 null이고 우월성을 주장하지 않는다. 연속 가격 panel의 soft_only_bound는 가격 자료 기준일 뿐 parent 정책이 아니다.

연구 선정은 주모델의 학습 binary≥3, 기준 binary≥3 및 기준 대비 승률 개선을 요구한다. 순위는 승률·지원량·고정ID이며 비용 후 평균/최악·확정양수·미확정은 별도 보고한다. 가설9개 중 상한1개는 선정하지 않는다. 이는 연구 floor이며 운영 publisher 계약이 아니다. 원watch cluster와 날짜 수를 반드시 병기한다. 새 확인 kernel은 미등록이므로 공식 candidate는 null이다.

후단의 같은 고정 후보가 개선을 재현하지 못하면 처분을 남기고 이 유한 확인 가설군을 종료한다. 선행 두 고정 후보의 이후 자동 원천 검증은 기존 `SamsungFrozenCandidateValidation1006` owner를 유지한다. 장전 새 연구 후보의 이후 검증은 이번 결과가 유효해 별도 구체화될 때만 계획하며 기존 owner acceptance를 암묵적으로 확장하지 않는다.

## 6. 코드·실행 검증

구현→리뷰→보완→재리뷰→표적pytest/compile/diff 통과 뒤 cold/warm 실행한다. 회귀는 hard guard·local breakout·source/quote/clock·route·epoch/sequence·future mask·기존 비용/종료 불변·native/day 분모·null 처리·holdout 비선정·봉인 output 재사용 거부를 검증한다. 실제 archive3일 prefix에서 미래를 가린 feature/mask 동일성을 확인한다.

선행176source/kernel seal과98policy/handoff hash 및10/3dirty checklist·10/6checklist hash를 시작/끝 대사한다. 신규 코드/plan/input을 봉인해 두 실행의 결과 bytes를 비교한다. 링크/단일 owner 및 print-only parser를 검증한다. 결과는 별도 audit에 기록한다. baseline 문서의 과거80% 보존/날짜 대기 문구는 현재 사용자 지시보다 낮은 우선순위로 적용하지 않으며, 승인되지 않은 baseline 문서 정리는 이번 범위 밖이다.
