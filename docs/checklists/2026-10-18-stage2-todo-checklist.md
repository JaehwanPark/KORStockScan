# 2026-10-18 Stage2 To-Do Checklist

## 오늘 목적

- 수량 연구 비용·의미 감시 후속 결함을 검증하고 다음 정규 기동용 배포를 마친다.

## 오늘 강제 규칙

- 선택 릴리스와 기존 정책·보조 binding·원천 및 실패 영수증을 보존하고 격리 후보에서 검증한다.
- 연구 원천일10/16과 적용 대상10/19를 유지한다. 코드·선택 배포·실제 PREOPEN/PID·자연 생산·비용 후 성과를 구분한다.
- 사용자 승인된 확정 총비용 배분은 연구에만 사용한다. canonical 실제 비용·손익·정책값·Main/manual custody·주문/provider·hard safety 권한을 임의 변경하지 않는다.
- 비영업일에 Main을 강제로 기동하지 않는다. 최초 정책에 추가 경제성·자연소비 허들을 부과하지 않는다.
- 문서 검증은 print-only parser만 사용한다. 외부 Project/Calendar 동기화는 사용자가 수행한다.

## 실행 항목

- [ ] `[InitialQuantityBrokerCostClosure1017] 키움 확정 총비용 배분 생산자와 수량 연구 소비 폐루프 보완` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 비용 미확인 반복 지적 및 보완 지시, 확정 총비용의 매수·매도 거래대금 배분을 연구에 사용한다는 사용자 확정, [비용 생산자·소비자 계약](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#8-2026-10-17-비용-생산자소비자-보완-계약).
  - 범위: 선택 c4467c424 기준 격리 구현 후 새 선택3abcc524c의 지연 연구 수리를 누적 보존한다. 연구 전용 배분 비용 생산·bounded fact/완료 overlay/수량/timeout 소비, 검증된 custody 문맥, 정산 대기 날짜 수집·소비 ack·정정 원본/세대 보존을 연결한다. canonical actual 손익·정책값·실주문 권한을 배분 자료로 변경하지 않는다.
  - Acceptance: 다회 거래/익일 청산/미청산/수동 잔여/반올림 보존식·원천/영수증 변조·과거 비용 정정·시간 역전/holdout·v2 호환·정산 대기/실패/경합/예산, 실제 봉인 자료와 비어 있지 않은 fixture 성능, 독립 리뷰·수정·재리뷰·문서 parser. 배포·정규 자연 생산·실제 PID/경제성은 별도 근거로 확인한다.
  - 완료: `e12256dec`에 최신3abcc 지연 수리를 누적 통합하고 독립 코드리뷰·수정·회귀781/인계547/지연66 PASS, 새 holding116 및 native128범위 신호 동일을 확인했다. 실제10/16 완료9건 중 연구 비용8건 admission·제외1건/미청산3건·총비용6,256원 보존과3회 성능/1,000건 예산 검증을 기록했다. 23:21 다음 정규 기동용 선택 발행 후 current_full_contract PASS/findings0, 정책값/128연결/두PRE/원6OPEN·운영 비용/fact 보존, provider/주문/재시작0·actual_pid_consumed=false다. [최종 검토](../audits/initial-quantity-broker-cost-closed-loop-repair-review-2026-10-17.md). 자연 생산·정산/경제성은 기존 InitialQuantityProducerConsumerRepair1010, 실제10/19 PREOPEN/PID는 DirectFamilyPreopenPolicyHandoff가 유지한다.
  - 재개: e122 발행 뒤 마지막 소비자 점검에서 의미 감시기의 compact completion/fact 참조 직접 비교 결함을 확인했다. 공통 증명 검증과 연구 영수증 일치 검사를 보완·회귀한 후 후속 불변 릴리스로 재배포한다. 원 e122 배포·발행 직후 PASS 영수증은 보존하며 자연 수용 owner는 유지한다.
  - 이관: 10/17의 e122 발행·후속 결함·실패 이력을 보존하고 동일 ID로 10/18에 이어간다. 연구 source10/16·다음 정규 적용10/19를 유지한다. 당일 감시는 current source/code/cost를 재검증하고 이미 승인된 과거 정책 ancestry에는 새 경제성·원천 최신성 허들을 추가하지 않는다.
