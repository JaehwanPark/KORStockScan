# 삼성전자 보관5단·전체 잔량 심화 연구

Owner: `SamsungPatternCampaign1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [연속 연구](samsung-pattern-campaign-plan-2026-10-04.md), [간격 민감도](samsung-quote-continuity-sensitivity-research-plan-2026-10-04.md).

## 남은 식별 정보와 가설

3/5단 소비 결함을 보완하면서 local depth journal의5단 및 전체 잔량이 확인됐다.3단 가설을 새로운 숫자로 다시 자르는 대신 깊은 호가와 전체 잔량이라는 아직 소비하지 않은 기존 필드를 검증한다. stock/day/item/epoch/sequence/수신 시각·BBO를 기존 캐시에 전수 결합한다. request/response parser/FID/수집/주문 흐름을 수정하지 않는다.

- `five_support`:5단 bid/ask 잔량비≥1.5/2, 저점 근처 BUY 우세.
- `five_flip`:5초 전5단 잔량비≤1에서 현재≥1.5로 전환.
- `total_support`:전체 bid/ask 잔량비≥1.5/2, 저점 근처 BUY 우세.
- `total_flip`:5초 전 전체 잔량비≤1에서 현재≥1.5로 전환.
- `deep_replenish`:5단 bid 가격이5초간 같고 SELL 우세·bid 유지 중5단 수량이1.2배 이상 증가.
- `deep_depletion`:5단 ask 가격이5초간 같고 BUY 우세·저점 근처에서5단 수량이70% 이하로 감소.

잔량 변화는 관측 수량 변화이며 특정 주문 주체/취소/체결 가능성 인증이 아니다. 제공된 모든 단의 순위·가격·수량·BBO 일치를 검사하고,5단 미제공을0으로 채우지 않는다. 전체 잔량은 제공된 모든 단의 합 이상·양수 분모·normalized combined total 일치가 있어야 한다. 과거 비교는 최신 과거5초 수신값, freshness1.5초·동일 epoch/sequence 및 그 사이 유효 snapshot을 요구한다.5단 가격이 움직인 변화를 같은 queue 보충/소진으로 바꾸지 않는다.

## 사전 고정과 위치

`src/engine/scalping/samsung_depth_profile_research.py`는 독립 오프라인 source consumer다. 기존 runtime/publisher와3개 봉인된 campaign kernel을 변경하지 않는다. 회귀는 `src/tests/test_samsung_depth_profile_research.py`에 둔다.

기존3일·두 비용 표현·과거 창60/180/300·level1/2·보유창600/1200/1800을 유지한다. 정규장전체/09시/10시 이후 및 개장15/30분, 다른4 exact scope전체를 분리한다.6×3×2×3×2×(3+2+4)=1,944개 추가 조건이며 기존10,008개와 총11,952개다. 관측 간격1.5/3/10초는 같은 조건의 가격 경로 민감도이므로 총35,856계산 조합·18가설군이며 독립 표본/독립 holdout 수가 아니다.

학습 binary≥3·기준 binary≥3·더 높은 승률→Wilson/support/단순성으로 고정한 뒤 후단을 평가한다. 성공100%/80% 보존 veto가 없다. 시간 종료 CF 양수는 운영 적합성 진단이며 선택 veto가 아니다. 현재 native Main bridge는 선택된 profile 필드와 phase를 동일 과거 시각에 반영하고 기존 guard·identity·원래 cost label을 보존한다. source gap을 실패/손익0으로 바꾸지 않는다.

## 완료와 종료

구현→5단/전체 합·가격 이동·과거 join·missing·native mask 회귀→리뷰/보완→compile/diff 후 실행한다. 실제 원천 prefix 인과성·모델별 결과·strict primary 재실행·source/kernel/plan 및 정책98개 보존을 확인한다.3초/10초 민감도에서만 생긴 결과는 운영 패턴으로 승격하지 않는다.

이 단계로 보관 가격·flow·3/5단/전체 잔량·시간·장전 기준·비용·경로 간격의 의미 있는 가설군을 마친다. 이후 같은3일의 수치/초 단위 분할이나 후단 승자 재선정은 새로운 독립 검증을 추가하지 않으므로 중단한다. 모든 가능한 수학적 패턴의 부재를 주장하지 않으며 새 수집·정책 발행·배포/기동 작업을 자동으로 만들지 않는다.
