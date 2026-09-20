# 메인 기계 전수 경제성 연결 보완 리뷰 — 2026-09-20

범위: [복구계획 §14](../proposals/main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md#14-공통-데이터미진입-기회비용-경제성-연결-상세-보완계획), 공통 데이터·기회비용 U6/U7/U11의 메인 최초진입 연결. 기존 health·원시각·306파일 migration과 독립 owner 전체를 다시 구현하지 않았다.

**판정: 비교·선정·발행의 확인된 결함을 보완했지만 전체 실행 경제성 완료는 아니다.** 운영 정책 발행과 원화 EV 완성은 별도 수용조건이다. 후보 없음/유효 incumbent carry를 양수 경제성 또는 ME8–ME14 전부 완료로 보고하지 않는다.

## 구현·검증한 변경

- 현행 incumbent부터 기존 bounded grid를 탐색한다. 학습 행동이 모두 같으면 가장 엄격한 첫 좌표를 자동 선택하던 동률을 제거했다. 같은 행동의 후보 수를 독립 개선 비교 수로 보고하지 않는다.
- 등록된 main scope마다 고유 incumbent·비용·기계 원천을 평가한다. 공통/계층 후보가 각 scope의 source/parent를 결속해 기존 발행기로 전달되도록 연결했다. 다른 scope의 KRX 후보 성공을 요구하지 않는다.
- 기존 날짜별 sealed compact 원천을 optional owner 실행 근거로 소비한다. 최신 하루의 projection이나 다른 날짜의 model proof를 과거 전체에 빌려주지 않는다. 기계 모집단 자체는 compact 표본으로 줄이지 않는다.
- 현재 기계가 막지만 당시 고정 보조판정과 실행 모델이 있는 사례는 후보 ENTER를 기존 owner arm과 비교할 수 있다. 이를 자연 Provider 호출이나 broker fill로 다시 기록하지 않는다.
- 전체 모집단의 실행·비용 근거가 일부만 있으면 원화/day를 null로 유지한다. 동일 promotion 반복과 미종결 RECHECK의 순차 재생이 없으면 포트폴리오 합산을 금지한다. 동일 정책의 대리 Δ=0은 원화 순익 0의 근거가 아니다.
- 실행 지원 후보의 일별 순익·보수적 paired EV를 먼저 비교한다. 기존 0.10%·표본·tail 계약은 유지한다. calibration에서 후보를 동결하고 동결 이후 source-day만 독립 승격 holdout으로 수용한다. hierarchy의 holdout 통과 규칙만 사후 골라 묶는 경로를 제거했다.
- 새 기계 정책 변경과 새 AI prompt의 미검증 동시 변경을 막는다. source hash/현재 parent/날짜별 loader 검증을 유지한다.
- summary에서 report 실행 플래그를 미래 writer 검증으로 오인하던 판단을 제거했다. owner replay 없음 자체를 역사적 복원 불가로 선언하지 않는다. 미확정은 `source_gap`이며 기존 checklist의 producer 수리 역할로 전달한다.

리뷰→수정→재리뷰→관련 pytest **459 passed**. 기존 테스트 파일에 signed owner proof, 신규 진입/비진입, 부분 coverage, 반복 promotion, RECHECK, incumbent 동률, 동결 전 holdout 금지, scope별 발행·부모 정책 결속을 검증했다. Python compile 및 diff check 통과. Provider/브로커 호출·주문·봇 재기동은 이 검증에 사용하지 않았다.

## 아직 닫히지 않은 경제성 경계

1. **원래 BLOCK/RECHECK의 frozen 실행 입력.** 기존 `_observe_entry_economics_before_ai`는 ENTER_NOW에만 실행 계획을 기록한다. 당시 가격/수량/가용자본·고정 compact 결과 없는 BLOCK은 현재 값으로 복원할 수 없다. 이 범위의 새로운 prospective producer가 검증됐다고 주장하지 않는다.
2. **독립 실행 모델 지원.** exact scope의 실제 실행/청산과 모델을 검증한 proof가 있어야 한다. 이번 signed fixture 성공을 실제 운영 데이터의 model validation으로 대체하지 않는다.
3. **반복 재평가와 공통 자본.** 단일 독립 episode 지원은 반복 RECHECK·겹치는 자본의 순차 행동 재생을 의미하지 않는다. 미지원 모집단은 제외/원인 보존이며 정상0이 아니다.
4. **과거 회복 가능성.** source date 9/14–9/16의 sealed compact owner projection이 없고 9/17도 operating model proof가 부족하다. 원본이 영구 소실됐다는 증명과는 다르므로 `historical_unrecoverable`로 종결하지 않는다. 당시 source를 exact 재구성할 수 있는지와 미래 writer 보완을 같은 기존 owner에서 이어야 한다.

이 결손은 단순한 표본/시간 대기가 아니다. ME9/ME10의 전체 실행·순차 재생과 ME14의 실제 비용 후 경제성 수용은 OPEN이다. 다음 거래일의 자동 carry는 운영 연속성일 뿐 결손 완료증명이 아니다.

## 실행 receipt

대상 원천일 2026-09-17, 발행일 2026-09-20, 예정 effective date 2026-09-21. 결과와 정책·후행 검증 hash는 아래에 실제 실행 후 기록한다. 작업본 base는 `a198c3b9bb3e0d78bff3feebe05b3d394a467973`이며 다른 세션의 compact 증거 분리 보완을 포함한다. 현재 날짜 9/20 checklist는 없고 9/21은 미래 owner다.
