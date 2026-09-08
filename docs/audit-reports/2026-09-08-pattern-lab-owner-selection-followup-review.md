# Pattern lab 기존-owner 후보 선택·승인 후속 보완 리뷰

기준: 2026-09-08 KST. #67 Claude scalp pattern lab / #69 Scalping pattern automation의 재점검 후 권장 보완 구현이다. 앞선 [v3 source-only 보완](2026-09-08-pattern-lab-small-net-remediation-review.md)과 구분하며, 이번 요청에는 커밋·배포·실전 운영값 변경이 포함되지 않는다.

## 판정

기존 Daily/PREOPEN owner에 **실제로 거래된 bounded profile의 재선택**을 연결했다. Lab에 별도 실전 승인 주체를 추가하지 않는다. 비용 차감 후 작은 순이익도 평가하며 거래당 EV뿐 아니라 손실·부분체결 비용·무거래 원천일을 포함한 순익/일과 완료 빈도를 함께 비교한다.

이는 미거래 신규 profile의 체결 성과를 합성하는 탐색이나 인과적 증분수익 증명은 아니다. 실거래 대안 profile 자체가 없으면 새 설정은 나오지 않는다. 이 상태를 무한 표본 대기로 숨기지 않고 유지·수리·통합·폐기 검토로 연결한다. 코드 보완과 자연 생성·실전 적용·실수익 검증은 별도 상태다.

## 권장 순서별 보완

| 결함 | 구현 | 남기는 경계 |
| --- | --- | --- |
| Daily 추천값이 항상 현재값이고 PREOPEN은 변경값을 거부 | `score_recovery_economics.evaluate_policy`를 Daily·PREOPEN이 공유. 앞쪽 원천일로 후보 한 개를 고정한 뒤 뒤쪽 원천일에서 비교. Daily 추천값·승인 version에 선택 profile을 결속 | 실제 거래된 동일 profile만 사용. score 범위·주문 수량·cap·effective 반등 floor는 탐색하지 않음 |
| Lab 경제성이 AI 입력에서 누락, native automation workorder 필터 누락 | AI 입력에 비용/순익/빈도·window·source hash·owner 판정 전달. scalping automation 작업 ID 전수와 상세 생략 수 명시 | 최대 20개 상세/코호트와 전체 건수 구분. 제목만으로 경제성 완료 판정 금지 |
| 부분체결 손실 한 건이면 전체 veto | full/partial EV는 분리. 고립된 작은 partial 손실은 full의 보수적 순익 여력 이내이면 허용 | 순익 여력 소진 또는 여러 거래일에 반복되는 음수 partial 근거는 차단. 여력은 실제 full 순익보다 클 수 없음 |
| 20유효일 유지 판단이 표시 flag뿐이고 작은 양수로 사라짐 | Lab → automation native `order_pattern_lab_bounded_maintenance_review` → workorder `design_family_candidate` 연결 | `retain_with_evidence / repair_source / integrate / retire`의 명시적 판단. 기존 설정의 양수 성과만으로 새 개선 가능성 검토를 닫지 않음. 자동 폐기·자동 BUY 없음 |

## 단일 owner와 자동 적용

1. 기존 paired producer → Daily의 rolling 20거래일 real book → 후보 선택/경제성 → 기존 AI correction → 다음 거래일 PREOPEN이 실전 경로다. Lab은 **앞서 생성된 같은 날짜 Daily**의 판정을 재계산하고 report bytes hash를 함께 보관한다. 뒤에서 생성되는 Lab 파일을 앞선 Daily가 기다리는 순환은 만들지 않았다.
2. Lab → automation → AI review → EV/workorder는 연구·유지 판단 전달 경로다. Lab의 표시 창은 daily/rolling 10거래일/cumulative이며 승인 owner의 20거래일 창을 대체하지 않는다.
3. 다른 값을 추천할 때 AI correction에 검토 current/recommended profile과 policy-search SHA256을 기록하고 PREOPEN에서 재검증한다. 구형 AI 승인이나 instrumentation 예외로 새 값을 통과시키지 않는다.
4. 승격 조건과 기존 guard를 통과한 후보는 기존 PREOPEN이 자동 반영한다. **operator lock이 우선하는 현행 계약은 그대로다.** 9/8 기존 apply artifact는 `score65_74_recovery_probe_real_operator_override_2026-06-11`을 보존했다. 이것은 새 Lab 후보 적용 증거가 아니다. 향후 경제성 통과 후보도 이 lock과 충돌하면 보류되며, 이번 구현은 lock 해제 권한을 만들지 않는다.

## 달성 가능성과 과도한 허들 재검토

- full 20건/2거래일, 비용 대사, 양수 순익과 평균−2표준오차 양수 조건을 유지한다. 큰 고정 수익률·drought·모든 horizon 결과를 추가하지 않는다. 학습/검증 각각에 20건을 다시 요구하지 않는다.
- 실제 대안 profile 중 매수압력 55~75(최대 변경 5), tick acceleration 0.8~1.5(최대 변경 0.1), micro-VWAP 10~20bp(최대 변경 5bp)에서 **한 축만** 변경한다. 기존 bounded 범위와 effective 상승/반등 floor를 유지한다. runtime의 raw micro 0은 기존 effective floor 투영으로 10으로 기록되는지 회귀 검증한다.
- 앞쪽 기간의 순익/일·full EV 개선으로 후보 하나를 고정한다. 뒤쪽 기간에서도 양수 순익/일과 full EV가 기준보다 좋아야 한다. 실패 후 holdout을 보고 차순위로 교체하지 않는다. 부분체결 손익은 금액 비교에 포함하되 EV 표본으로 합치지 않는다.
- 한 시장의 개선 때문에 다른 기존 승인 가능 시장이 사라지거나 악화되는 후보는 유지하지 않는다. 동일 env profile을 쓰는 consumer의 scope 손실 방지다.
- 관측된 과거 profile 간 비교에는 시장·노출량 차이가 남을 수 있다. `observed_real_profiles_not_causal_counterfactual`로 표시하고 실수익 향상 확정치로 보고하지 않는다.
- 20개 유효 원천 거래일 이후에도 선택 가능한 개선 후보가 없으면 typed 유지 검토를 생성한다. 현행 profile이 양수라는 이유만으로 이를 없애지 않는다. 유효 원천일 미달, profile 없음, 비교군 없음, 순익 없음은 서로 다른 병목이다.

## 코드 리뷰·검증

- 1차 구현 뒤 직접 producer/consumer와 기존 AI/PREOPEN, workorder 분류기를 재검토했다.
- 보완 리뷰에서 부분체결 비용 누락에 의한 후보 순위 왜곡, 보수적 여력이 실제 순익을 넘는 문제, 타 시장 적용 범위 유실, 오래된 AI 승인 재사용, holdout을 본 차순위 재선택을 방지했다. 학습 비교 숫자도 ledger에 남기고 scope 정렬을 고정했다.
- 격리 fixture에서 Daily 추천 갱신 → PREOPEN 메모리상 env 선택, AI 검토 세대 일치/불일치, Lab의 Daily 판정 재계산, native 유지 검토 분류, 작은 순익·손실·부분체결·malformed contract를 검증했다. provider 호출이나 실전 env 쓰기는 없다.
- 최종 관련 12개 모듈 **786 passed**(18.34초). 영향 Python 11개 compile, Ruff E9/F63/F7/F82, 문서 print-only parser 및 `git diff --check`를 통과했다. 기존 자연 owner 두 개가 각각 한 번씩 현재 날짜 체크리스트에서 파싱된다. 검토 범위 내 미해결 finding 0이며 자연 장후 report를 재생성하거나 운영 artifact를 덮어쓰지 않았다.

## 실제 자료와 다음 수용

- 기존 9/7 Daily canonical score family는 `hold_sample`, real-book 원천일 0·관측 0이다. 이전 v3 읽기 전용 확인의 Lab 원천 10거래일·경제성 후보 0과 혼동하지 않는다. 새 구현으로 자연 생성된 결과가 아니다.
- 따라서 **현재 개선값·추가 순익은 입증되지 않았다.** 과거 결손 비용을 합성하거나 operator override 성과를 이번 패치의 수익으로 귀속하지 않는다.
- [9/8 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 `PatternLabSmallNetNaturalEvidence0908`와 `DailyThresholdNaturalAcceptance0908`에서 자연 source, 같은 날짜 owner/AI generation, 후보/lock 판정, 후속 PREOPEN/PID 및 실제 비용 차감 손익을 구분해 확인한다. 새 OPEN을 중복 생성하지 않는다.
- `korstockscan-review-gate`에 따라 코드 결함 종결과 미관측 경제성·운영 권한을 분리했다. 실전 env·운영 lock·매매 process·주문·provider 설정은 바꾸지 않았고, canonical 재생성·외부 Project/Calendar sync·커밋/푸시도 실행하지 않았다.
