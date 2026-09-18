# WS 품질·조건부 경제성 통합 구현 리뷰

작성일: 2026-09-19 KST. 범위는 `intraday_ws_freshness_monitor`의 장후 scanner 선택 경제성 subsection에서 다음 장전 정책·기존 consumer까지다. 구현·리뷰·수정보완·검증은 완료했으며 자연 PREOPEN/PID와 실제 성과는 완료로 세지 않는다.

## 결정과 구현

| 항목 | 최종 동작 |
| --- | --- |
| 원천 보존 | native decoder가 `scanner_promotion_id`를 resource row까지 유지한다. complete partition, 실제 baseline 선정 재현, KRX regular/simple capacity만 지원한다. |
| 조건부 평가 | 동일 선택은 provider0/raw rescan0으로 `no_effect`, delta0이며 절대 EV는 null이다. 변경 선택은 원 plan/quantity/guards, full terminal, reviewed pricing, 독립 prior model, 비중첩 자본을 모두 요구한다. |
| 경제 metric | 동일 frozen eligible budget으로 baseline/candidate EV·순익·날짜별 순익 차이·tail·stress·capital과 model error 하한을 재계산한다. CF는 실제 PnL로 표기하지 않는다. |
| 독립 검증 | 실제 동결 KST일까지 learning을 닫고 이후 날짜만 holdout으로 인정한다. 실제 completed20/5일·cohort10/3일·paired3/2일, EV+0.10%p, 일별 순익 양수, tail/worst 기존 gate를 유지한다. |
| 정책/PREOPEN | 평가일·발행일·policy 거래일·effective 거래일을 분리한다. shared v2 validator가 source/model/cost/holdout/hash/date/authority를 재계산한 ready만 immutable PREOPEN에 허용한다. |
| post-apply | 실제 immutable PREOPEN policy hash와 일치하는 completed 결과만 해당 버전에 귀속한다. machine/compact joint 자연 acceptance는 기존 owner에 남긴다. |
| 후행 소비 | Daily·EV·runtime summary·control tower·checklist와 scanner-only strict가 같은 source/policy hash를 검증한다. 늦은 장중 writer가 final subsection을 지울 수 없다. |

## 리뷰·검증

- Self review에서 `scanner_promotion_id` 전달 누락, publication과 source 날짜 혼동, active PREOPEN 고정 거부, holdout의 늦은 평가 시점 오염, 서로 다른 model proof를 잘못 선택할 가능성, 다른 budget에서 model error 하한을 단순 평균하던 문제, post-apply가 영구 `not_applicable`인 문제를 수정했다.
- 기존 테스트 family에 positive supported→hold→future-ready→publisher→PREOPEN→scanner bonus, same-selection/no-capacity skip, missing/partial/pricing/model gap, capital overlap, forged proof/date/hash, late writer, exact post-apply hash를 추가했다. 마지막 대상 검증은 662 passed, warning1이며 compileall·shell syntax·`git diff --check`를 통과했다.
- 합성 검증값 baseline EV0.2%, candidate EV1.0%, paired delta+0.8%p, 일별 순익 차이+960원은 경로 검증값이다. 실제 성과가 아니다.

## 현재 source9/17 결과와 잔여 owner

재생성 결과와 commit/release/consumer hash는 아래 배포 후 기록에서 갱신한다. 시작 전 실제 원천은 WS resource row328·native event0, source quality/master pass였고 compact source21건의 execution model은 `source_gap`이었다. 따라서 현재 profile의 지원되는 실행 경제 비교가 생길 가능성은 없으며, missing plan/model을0으로 바꾸거나 임의 체결을 합성하지 않는다.

WS6의 다음 자연 generation 원 plan/quantity/guard, 독립 model, 정규9/21 PREOPEN/PID, 선택 순서 변화 또는 baseline 보존, 실제 COMPLETED 비용 후 EV·일별 순익·tail·자본은 [9/21 기존 owner](../checklists/2026-09-21-stage2-todo-checklist.md)가 소유한다. 설치 main trigger 부재, 전체 장후 DONE, 주문과 봇 재기동은 이 범위의 완료 주장이 아니다.
