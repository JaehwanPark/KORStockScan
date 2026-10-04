# 삼성전자 관측 호가 간격 민감도 연구

Owner: `SamsungPatternCampaign1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [연속 연구계획](samsung-pattern-campaign-plan-2026-10-04.md), [개장 초기 연구](samsung-opening-regime-research-plan-2026-10-04.md).

## 관측에서 나온 질문

연구 코드의 `len(levels)==3` 검증은 정상5단 domain snapshot을 제외했다. local producer `micro_reversion/forward_collector.py::_normalize_depth_levels`는 최대5단을 보관한다. 모든 보관 단의 순위·가격·수량·BBO 일치를 검증한 뒤 상위3단을 소비한다. 보완 후 정규장332,990/334,124호가 및51,604관측 frame의 잔량 비율이 유효하다. protocol parser/FID/request/수집은 변경하지 않는다.

10/2 09:28 신호의 검열은09:30:07.347→09:30:09.305의1.958초 호가 간격 때문이다. epoch 동일·seq9013→9014로 연속이므로 이 간격만으로 기록 누락이라고 단정할 수 없다. 원래1.5초 관측 간격 기준이 패턴 결과를 가렸는지, 간격을 늘리면 오히려 미관측 손실이 드러나는지 검증한다.

별도 리뷰에서 한 개 invalid quote를 valid-index 배열이 건너뛸 수 있는 결함도 발견했다. 모든 모델에서 invalid receipt·epoch/sequence/수신 순서 단절을 만나면 해당 terminal 이전 경로를 검열한다. invalid를 건너뛰어 성공으로 바꾸지 않는다.

## 사전 고정

- 기존10,008조건·관측 frame·3일·고정 날짜 순서·비용2모델·학습 우선 승률 선택을 유지한다. 원천 추가 및 후단 재선정은 없다.
- 관측 호가 간격만1.5/3/10초로 분리한다.1.5가 strict primary이며3/10은 `quote_gap_sensitivity=true`인 관측 경로 진단이다.10초는 기존 normalized sequence prefix의 상한이고, 운영 freshness 확대가 아니다.
- 진입 및 시간 종료 BBO freshness는1.5초를 유지한다. invalid clock/가격/seq/epoch를 통과시키지 않는다. 경로 사이에 가격을 보간하거나 fill/실현 손익을 합성하지 않는다. 큰 간격 사이의 미관측 실제 시장 경로가 증명되었다고 주장하지 않는다.
- 각 모델 안에서 학습 조건을 고정해9/30·10/2를 평가한다. 성공100%/80% 보존 veto가 없고, 시간 종료 CF 양수는 선택 veto가 아닌 운영 적합성 진단이다.
- 총 탐색조건은10,008이며 간격3모델은 같은 관측을 재사용한30,024개 계산 조합이다. 독립 표본/독립 holdout 수를 늘린 것으로 부르지 않는다.

## 구현 및 종료

별도 producer를 만들지 않고 기존 offline scalping research3개 CLI에 관측 모델 인자를 추가한다. runtime caller·기계 임계값·기존 captured guard/native identity·정책 발행·배포/기동·주문/provider 권한은 바꾸지 않는다. source/kernel/plan과 정책98개를 봉인하고 기본 모델을 포함해 재계산한다.

리뷰→single-invalid/3·5단/sensitivity/sequence/endpoint freshness 회귀→재리뷰→compile/diff 후 실행한다.3모델의 결과와 strict 기본 결과 재실행, actual-source prefix 인과성과 hash 보존을 대사한다. 민감도에서만 생긴 성공은 운영 패턴으로 승격하지 않는다. 이 단계로 가격/flow/잔량/시간/장전/비용/경로 유효성의 보관 원천 가설군을 마친다. 이후 동일3일을 임의 숫자로 다시 자르는 탐색은 독립 검증을 추가하지 않으므로 중단한다.
