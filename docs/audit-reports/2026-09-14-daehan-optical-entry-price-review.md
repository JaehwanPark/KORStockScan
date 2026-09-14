# 대한광통신 주문가 선정·재호가 검토

검토 기준: `2026-09-14 KST`

## 판정

대한광통신(`010170`) 주문번호 `0031943`의 미체결 취소는 `price_selection_too_passive_candidate`이면서 `entry_price_or_reprice_authority_mismatch`다. 최초 14,320원 주문이 안전 계약을 위반했다는 근거는 없지만, 당시 최우선 매수호가보다 3틱 낮아 참여 가능성이 낮았고, 시장이 위로 이동한 뒤 실행될 예정이던 재호가는 부모 AI PASS 점수 78을 전달받지 못해 `ai_score=0`으로 차단됐다.

이 단일 사례만으로 최우선 매도호가 추격, 방어폭 축소 또는 cancel wait 연장을 적용할 수는 없다. 같은 시점의 queue 우선순위와 공격적 매도 체결을 완전히 복원하지 못했으므로 14,350원 주문의 체결도 확정할 수 없다.

## 시간순 근거

| 시각 KST | 단계 | 확인 결과 |
| --- | --- | --- |
| 10:41:24.733 | 메인 진입 AI | 같은 promotion에서 `BUY`, score `78`, prompt `decision_quality_v2_15_2_balanced_bounded_recovery` |
| 10:42:05.207~10:42:05.361 | entry-price 및 제출 | Entry-price AI `USE_DEFENSIVE`, confidence `85`; 주문 3주를 14,320원에 제출. 최종 fresh BBO는 14,350/14,370원으로 주문가는 bid보다 30원, 3틱, 약 20.9bp 낮음 |
| 10:42:23.205 | post-submit reprice | fresh BBO 14,360/14,370원, quote age 0.9ms, buy pressure 95.56, trusted aggressor 10인데 `low_ai_score`로 차단. 이벤트에는 부모 `scout_ai_parent_score=78`과 reprice 입력 `ai_score=0`이 동시에 기록됨 |
| 10:43:44.168~10:43:44.799 | 취소 | 90초 wait 뒤 fill 0/3, 전량 미체결 상태로 취소 요청·확인. 제출부터 취소까지 기록된 현재가는 14,350~14,370원으로 14,320원에 접근하지 않음 |

원천은 [당일 pipeline events](../../data/pipeline_events/pipeline_events_2026-09-14.jsonl)의 promotion `SCANPROM-010170-1789350027339`, entry-price trace `entry_price:010170:1789350123078:d00561f9`, 주문 `0031943`, 취소 `0032187`이다.

## 최초 주문가 검토

Entry-price AI가 읽은 호가는 14,350/14,410원이었고 `fresh_consistent`, `entry_price_v1_contract_status=pass`였다. 최종 제출 직전 effective BBO는 14,350/14,370원으로 갱신됐지만 `normal_defensive_percent_bps`가 14,320원을 유지했고, 14,350원 reference target은 `not_better_than_defensive`로 배제됐다.

최종 submit context에는 buy pressure 95.560, trusted aggressor 10과 fresh micro reaction이 있었지만, entry-price 판단용 gap profile에는 positive signal 0, buy pressure false, trusted aggressor 0으로 기록됐다. 이후 bundle에는 ask sweep 87, bid replenishment 64, post-sweep hold 52가 계산됐으나 `computed_not_sent`였다. 따라서 방어가를 선택한 모델 판단 자체보다 **entry-price 결정 시점에 이용한 micro 입력과 최종 submit 시점의 관측 사이 단절**도 입력품질 후보로 남는다.

14,370원 ask를 즉시 지불했다면 최초 주문보다 50원, 약 34.9bp 비싸다. 고정 비교비용 23bp와 작은 순수익 목표를 고려하면 자동 ask crossing은 기대수익을 쉽게 훼손할 수 있다. 이 사례가 직접 지지하는 후보는 fresh best bid 또는 bounded reprice의 참여율 비교이며, 무조건 공격적 주문은 아니다.

## 확인된 구현 결함

[sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)는 broker 제출 후 pending order에 `ai_score=latency_signal_score`를 저장한다. 대한광통신에서는 이 값이 0이었다. [entry_reprice_after_submit.py](../../src/engine/scalping/entry_reprice_after_submit.py)는 이 `order.ai_score`가 score floor보다 낮으면 `low_ai_score`로 종결한다. 같은 pending order에 보존된 부모 AI attribution의 `scout_ai_parent_score=78`은 재호가 판정에 사용되지 않는다.

재호가는 이미 승인된 BUY attempt의 미체결 주문을 다루므로 score owner와 lineage를 명시적으로 고정해야 한다. 후속 수리는 부모 AI trace의 검증된 score/action을 pending order의 canonical reprice provenance로 전달하거나, 현행 기계+AI 계약에서 재호가가 사용해야 할 별도 score를 정의해야 한다. missing score를 0으로 보간해 경제적 veto로 사용하는 현재 동작은 허용하지 않는 편이 맞다.

## 다음 수용조건

- 같은 submit attempt의 machine action, AI PASS trace/score, entry-price trace와 pending order/reprice event가 하나의 lineage로 연결된다.
- 재호가 입력 score가 결손이면 `source_quality_blocked`로 직접 기록하며 `low_ai_score`로 오분류하지 않는다.
- 부모 score 78과 fresh quote/micro가 주어진 회귀 테스트에서 reprice가 score 결손 때문에 차단되지 않는다. 기존 spread, stale, broker/order, partial fill, cap과 hard-safety guard는 유지한다.
- 최초 방어가, best-bid 후보와 bounded reprice를 동일 시점 executable source로 누적 비교해 fill participation, 비용 차감 target/adverse first-hit와 tail을 함께 산출한다.
- 코드 수리, 선택 release 배포, 현재 PID 소비와 자연 미체결 개선은 각각 별도로 확인한다.

후속 구현·장후 handoff owner는 당일 체크리스트의 기존 `CodeImprovementWorkorderReview0914`를 사용한다. 이 리뷰만으로 닫힌 `RuntimeEnvIntradayObserve0914`의 과거 수용 범위를 다시 OPEN하거나 새 실주문 권한을 만들지 않는다.

이번 검토는 읽기 전용 주문 분석과 장중 지시문 보완이다. 주문가·threshold·provider·bot/env를 변경하거나 재기동하지 않았다.
