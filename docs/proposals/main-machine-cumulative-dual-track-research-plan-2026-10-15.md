# Main 누적 놓친 상승·ENTER_NOW 실패 감소 추가 연구 계획 — 2026-10-15

## 1. 목적과 실행 범위

사용자 요청에 따라 기존 후보의 재검증에 더해 **새 가설을 수동으로 정의하고 검증**한다. 놓친 상승 추가 포착(A), 기존 ENTER_NOW 확인점의 실패 감소(F), `F(current) OR A` 결합(J)을 모두 비교한다. 삼성·두산·HPSP·알테오젠·주성과 일반 비고정 종목, PRE NXT `_NX`·정규 SOR `_AL`·통합 AFTER SOR `_AL`을 동일 계약으로 다룬다.

이번 작업은 격리된 오프라인 연구다. 운영 후보 등록·정책 선택·배포·재기동·provider 요청·실주문을 실행하지 않는다. 장후 자동 작업이 새 가설을 만들도록 변경하지 않는다. 기존 [정책 반영 계획](main-cumulative-research-policy-adoption-plan-2026-10-14.md)은 연구 결과를 받아 별도 구현 인계로 갱신한다.

## 2. 고정한 비교 기준과 원천

- 연구 시점 selected release: `policy-custody-incident-integrated-20261015-bb4808c77`; 현재 정책 bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`.
- 이전 연구 parent `99c894…`를 baseline으로 재사용하지 않는다. 주성 AFTER 고가와 일반 PRE 저가의 기존 branch 제거를 포함하여 현재 native State로 전 partition을 재생한다. 이전 효과를 새 개선으로 중복 합산하지 않는다.
- 기존 정정 연구의 24개 partition에 완료된 10/14 3개를 추가한다. 9/29·9/30·10/2·10/6·10/7·10/8·10/12·10/13·10/14의 9개 날짜, 27개 partition, 원천 5,587,427행이다. 10/13은 기존 입증된 늦은 AFTER 구간만 포함한다.
- 10/15 현재 원천은 `main_raw_epoch_receipt_missing_or_invalid`여서 제외한다. 수집 epoch를 입증하지 못한 자료를 튜닝에 넣거나 당일 결손을 실패 0건으로 해석하지 않는다. 현재 원천을 새로 수집하지 않는다.
- 기존 완료 분봉과 10/14 원천 manifest에 결속된 완료 분봉을 개인 연구 디렉터리에 동결한다. source·code·feature·policy·bar SHA 및 cutoff는 [frozen manifest](../../tmp/main-machine-cumulative-research-20261015/frozen-manifest.json)에 기록한다.

원천 전수 확인 보완: 10/14의 325,775행은 세 시장 모두 `valid=0`이다. 309,259행은 일치하는 적격 epoch 종료 증빙이 없고, AFTER 16,516행은 종료 증빙이 있으나 `unaccounted_raw_row_exclusion`으로 거부됐다. 후자는 enqueue·persist 16,516건이 일치하지만 timestamp 사전 거절 150건 중 보존 receipt가 64건뿐이다. 이는 해당 가격 전부가 틀렸다는 증명이 아니라 현재 적격성 계약의 결손이다. 따라서 검토 날짜는 9개, 실제 적격 원천 날짜는 기존 8개로 분리한다. 상세는 [원천 제외 진단](../../tmp/main-machine-cumulative-research-20261015/source-exclusion-diagnosis.json)에 기록한다.

## 3. 새로 수동 정의한 가설

기존 A01~A09·F01~F16을 고정 비교군으로 유지하고 아래 A 7개·F 6개를 추가한다. 합계 A 16개·F 22개다. 결과를 본 뒤 같은 실험의 임계값을 바꾸지 않는다. 모든 특징은 확인점까지 수신된 prefix만 사용한다.

| ID | 추가 포착 가설 |
|---|---|
| A10 | 첫 반전 후 1초 유지; 해당 종목 세션 변화 −0.4~+0.4%, 60초 수익률 0~0.1% 미만, 5분 고점 대비 낙폭 0.2% 미만, 최근/직전 60초 거래량 비율 ≥1 |
| A11 | 60초 수익률 +0.05% 상향 전환 후 3초 가격 유지; VWAP 이상, 거래량 비율 ≥1, 수익률 0.2% 미만, 낙폭 0.4% 미만 |
| A12 | 직전 60초 고점 돌파 후 1초 유지; 종목 세션 변화 +0.4% 초과, 수익률 0~0.4% 미만, 10틱 매수 비중 ≥60%, spread ≤0.1% |
| A13 | 60초 VWAP 아래→이상 전환 후 1초 유지; 수익률 ≥0, 매수 비중 ≥60%, spread ≤0.1% |
| A14 | 최근 30초 고점·저점이 직전 30초보다 모두 높은 구조로 전환 후 3초 유지; 수익률 ≥0, VWAP 이상, spread ≤0.1% |
| A15 | 약세 종목에서 첫 저점 재확인 뒤 반전 가격 재돌파; 세션 변화 −0.4% 미만, 수익률 0~0.2% 미만, 매수 비중 ≥60%, 거래량 비율 ≥1 |
| A16 | 60초 수익률 +0.05% 상향 전환 후 5초 유지; VWAP 이상, 매수 비중 ≥60%, spread ≤0.1%, 낙폭 0.4% 미만 |

hold는 root 시점 가격 아래 체결이 발생하면 무효이며 특징은 hold가 완료된 확인점에서 다시 읽는다. 고점 돌파·VWAP·상승 구조의 `UNKNOWN→TRUE`를 `FALSE→TRUE`로 바꾸지 않는다. 반전 선행 조건은 해당 FIRST/RETEST 가설에만 적용한다.

| ID | 기존 확인점 실패 감소 가설 |
|---|---|
| F17 | 고점·저점 동반 하락이 아니며 60초 수익률 ≥0 |
| F18 | 수익률 ≥0.05%, VWAP 이상, 거래량 비율 ≥1 |
| F19 | spread ≤0.1%, 매수 비중 ≥60%, VWAP 이상 |
| F20 | 종목 세션 약세(−0.4% 미만)에서만 수익률 ≥0·VWAP 이상·고점/저점 동반 하락 아님을 요구 |
| F21 | 종목 세션 중립(−0.4~+0.4%)에서만 거래량 비율 ≥1·매수 비중 ≥60%·spread ≤0.1%를 요구 |
| F22 | 종목 세션 강세(+0.4% 초과)에서만 동반 하락 아님·VWAP 이상·수익률 ≥0.05%를 요구 |

위 약세/중립/강세는 **개별 종목의 첫 유효 세션 관측 대비 변화**다. KOSPI/KOSDAQ 등 외부 시장 환경을 입증한 분류로 부르지 않는다. 조건부 F는 해당 regime 밖에서는 원 신호를 유지한다. UNKNOWN도 원 신호를 유지한다. 특정 branch 정제는 다른 OR branch의 정상 허용을 막지 않는다.

## 4. 결과 라벨과 비교

확인점 실제 ask·30분·비용률 0.0023·비용 후 목표 +0.4%와 soft −3% 선도달 계약을 유지한다. W는 목표 선도달, STOP은 손절 선도달, TIMEOUT은 충분한 30분 관측 후 둘 다 미도달, U는 검열·미확정이다. **TIMEOUT은 실제 금전 손실을 의미하지 않는다.** 동일 item의 동결 완료 분봉은 기존 계약대로 10분 이후 가격 경로를 보조한다.

current/A-only/F-only/J를 동일 scope에서 비교하고 누적 `W/(W+STOP+TIMEOUT)`을 1순위, 동률은 W 수·current·고정 ID 순서로 선택한다. 성공 보존율 100%/80%, 최소 표본·날짜·새 holdout·추가 EV를 탈락 조건으로 넣지 않는다. 분모가 없는 baseline은 개선율을 만들지 않는다.

별도로 기존 비율 이상을 유지하면서 W가 가장 많은 기회 확대 대안도 제시하되 이를 승률 우선 winner와 혼동하지 않는다. A의 추가 W/STOP/TIMEOUT/U, F의 제거 W/STOP/TIMEOUT/U, J의 재허용과 중복, 날짜 편중·distinct target clock을 공개한다. 동일 누적 자료에서 탐색·순위를 계산하므로 독립적인 미래 성능 입증이라고 설명하지 않는다.

실제 과거 Main ENTER_NOW 캡처와 현재 정책의 과거 재생 CF는 별도로 집계한다. 실제 판정 캡처라도 미래 가격 라벨은 주문·체결·실현 수익 영수증이 아니다. 입력 key/ask가 정확히 연결되지 않는 캡처는 source gap으로 남긴다.

## 5. 구현·검토·검증

오프라인 분석 소유 위치는 [연구 디렉터리](../../tmp/main-machine-cumulative-research-20261015/)다. production 모듈과 옛 정정 결과를 수정하지 않는다. 현재 릴리스 코드를 명시적으로 import하고 전체 native State를 재생하여 이전 sparse membership cache에 의존하지 않는다.

1. 카탈로그·원천·현재 정책·코드·분봉 봉인.
2. 신규 root의 UNKNOWN 전환·미래 suffix 불변·source break hold·조건부 F·OR·성공 제거 허용 반례 검증 후 계산 실행.
3. 단일 낮은 우선순위 worker, partition별 메모리 2GiB·CPU 480초·wall 600초 한도, 불변 checkpoint로 재개. canonical 장후 보고서를 재생성하지 않는다.
4. 모든 대안을 비교하되 raw 재읽기는 조합별로 하지 않는다. 미완료 partition·hash 변경·pending overload는 완료로 표시하지 않는다.
5. 독립 선형 tick 라벨 oracle, exact key/ask 연결, 완료 분봉 재검사, 표적 native/feature parity를 확인한다.
6. 결과 보고서와 기존 정책 반영 계획을 갱신하고 문서 링크·권한·print-only parser를 검증한다.

이번 연구의 완료는 새 A/F 가설의 실제 누적 비교와 한계 공개다. 등록·운영 적용 완료와 구분한다. 10/15 체크리스트에는 `DirectFamilySourceRepairMainMechanisticEntry` OPEN이 없으므로 과거 10/14 항목을 현재 executable owner로 표현하지 않는다. 향후 등록 구현 때 현재 정책 owner와 기존 `DirectFamilyPreopenPolicyHandoff`의 적용일/수용 범위를 명확히 연결한다.
