# Scanner·Daily 소액 순이익 승인: 1~3 후속 구현 리뷰

기준: 2026-09-08 KST. 사용자 승인 범위는 Scanner 승인 문턱, Daily 당일 원천 연결, 자연 적용·성과 검증 경로의 보완이다. 운영 정책 발행·수동 env·operator lock·매매 재기동·주문·provider route/호출량 확대·commit/push는 수행하지 않는다.

## 구현과 목표

| 영역 | 구현 | 목표/경계 |
|---|---|---|
| Scanner 승인 | v4 자원배분/장전 계약에 `scanner_lookup_attention_small_net_v1` 경제성 추가. base·독립 holdout·mature R6에서 고정 +0.10%p 제거 | 작은 양수 순이익/증분을 반복하는 cohort도 승인 가능. 매수 횟수·승률 최대화가 아님 |
| 불확실성 | candidate 순EV−2SE>0, 증분 순EV−2(SE_candidate+SE_control)>0, candidate 원화 net>0 | SE=max(거래별 SE, 거래일 cluster SE); cohort 간 공분산을 0으로 가정하지 않는 합산 상한. 인과적 paired 비교나 신뢰구간/수익 보장이 아님 |
| 안전·비용 | 기존 base/holdout 각20건/5일·군별10건/3일, full-fill, 독립 future holdout, tail/worst-loss, source/owner/scope 유지 | CF 교체 pair와 실제 체결 cohort는 별개. 실제 체결가격에 내재한 slippage는 중복 차감하지 않음. 기존 비교 수수료·세금은 broker exact 비용 대사와 구분 |
| 정책 검증 | producer/PREOPEN/R6 공통 경제성 함수. 원천 행→book/SE→evidence 재현, mature flag 검산, 소표본 emergency loss 차단 | 요약·hash만 맞춘 잘못된 통계나 R6 loss 은폐를 승인하지 않음. 9/8 source부터 새 계약 필수; 이전 frozen 계약은 원래 gate 검증 |
| Daily 연결 | 기존 Entry split→AI 원천 materialization→R0–R3 내부 paired 순서를 Daily 앞으로 이동 | 동일 장후 paired→Daily/cumulative/기존 AI correction→다음 PREOPEN. 중복 lifecycle/Daily/Provider 실행 추가 없음. OFF/failed/deferred/빈 원천은 별도 상태 |
| 자연 성과/유지 판단 | Scanner `economic_acceptance`, Daily `condition_feasibility.natural_acceptance`에서 source 일수·완료 빈도·순이익·20유효일 review 보고 | 0매매일 포함, 미관측/미체결·청산·비용결손/edge 부족 분리. 자본시간은 값이 없으면 null, Scanner 승인 floor 아님. 자동 삭제·표본 만들기 위한 거래 확대 없음 |

Scanner는 같은 priority tier 안의 기존 bounded bonus만 소유하며 상승/반등 신호나 broker 주문 권한을 새로 만들지 않는다. 최종 BUY는 기존 진입·source·안전 guard를 계속 통과해야 한다. Daily는 기존 profile의 경제성 승인이지 entry/exit target 탐색기가 아니다.

## 자동 적용과 실제 상태

- Scanner: 검증된 다음 장전 후보 → 09:00 전 immutable exact-date receipt → scanner/runtime attach → R6. 기존 자동 계약에 별도 사용자 재승인 없음. 장중 frozen receipt를 교체하지 않는다.
- Daily: source-quality preflight·trade-fact sync 뒤 원천 owner가 선행한다. Daily의 기존 AI correction·PREOPEN guard·operator lock 우선순위는 유지된다. 새 wrapper snapshot부터 당일 근거 지연이 해소되는 구조이며 이번에 main wrapper를 실행했다는 뜻은 아니다.
- 9/8 08:57 전후 읽기 전용 확인: 9/7 Scanner actual full-fill outcome은 1건이며 **candidate 0 / control 1**. control의 기존 비교비용 차감 net은 +390.985원(0.29243455%)이고 새 기준도 `hold_sample`이다. 후보 성과/증분 수익으로 해석하지 않는다.
- 기존 9/8 Scanner PREOPEN receipt는 유효·inactive, 사유 `prior_policy_not_live_auto_apply_ready`. 원본을 수정하지 않았다.
- 9/7 paired 자기해시/날짜는 유효하지만 신규 profile 결속 full/partial은 0/0이다. 9/8 pipeline에서 새 score 계측 stage는 해당 확인시점 미관측이다. 이를 결함·PID 미로드 확정이나 수익 개선 완료로 단정하지 않는다.
- 현재 자연 owner는 9/8 체크리스트의 `DailyThresholdNaturalAcceptance0908`, `ScannerLookupAttentionNaturalEvidence0908` 두 기존 ID를 유지한다. 장후 예정 전 output 결손은 `not_yet_due`이며 미래 실체결/EV acceptance는 OPEN이다.

## 리뷰·검증

`korstockscan-review-gate`를 따라 변경부뿐 아니라 source→producer→policy validator→PREOPEN frozen receipt→R6 및 wrapper 순서를 확인한다. 새 Python 모듈을 engine root에 만들지 않았고 테스트는 기존 `src/tests` owner에 추가했다.

1. 고정 gate가 세 경계에 따로 남는 문제를 공통 검사로 보완했다.
2. 거래일 내 반복 관측·cohort 간 독립성 가정에 의한 불확실성 과소평가를 day-cluster/합산 SE로 보완했다.
3. 빈 표본의 SE null은 sample wait이고 malformed 통계는 계약 실패로 구분했다.
4. 새 계약 삭제/legacy gate 다운그레이드, 원천 행과 통계 불일치, mature R6를 false로 숨기는 경우와 소표본 emergency loss를 차단했다.
5. 실행 순서 변경에 맞춰 wrapper failure-isolation 테스트의 경계를 수정하고, source 차단일은 holdout을 비워 보존된 base와 구분했다.

### 최종 결과

- 13개 관련 test module **1,357 PASS / 36.89초**. Scanner source/resource/net 승인·PREOPEN/runtime 통합, Daily/cumulative/장전, lifecycle, Main AI cycle, wrapper 및 strict verifier 회귀를 함께 실행했다. 기존 pandas_ta의 Pandas4Warning 1종은 패키지 변경 없이 남겼다.
- 합성 실제체결 계약의 candidate +0.06%, control +0.02% (증분 +0.04%p)가 base/독립 holdout/R6와 PREOPEN frozen receipt→runtime loader를 통과했다. 실제로 이 수익이 발생했다는 뜻은 아니다. 음수/동률, 거래일 집중 변동, 큰 손실, malformed SE, 계약 downgrade, 통계 변조, 거짓 maturity, emergency loss 및 빈 표본을 반례로 검증했다.
- 실제 `build_artifacts` 호출의 ready/source-blocked/post-loss 세 분기와 원천 행 재현 validator를 검증했다. wrapper는 기존 source owner와 Daily를 한 번만 배치하고 기존 resource/command/artifact 실패 격리를 유지한다.
- Black·Ruff·변경 Python compile·`bash -n`·`git diff --check` 통과. 문서 print-only parser에서 두 자연 owner가 현재 9/8 checklist에 각각 한 번 존재함을 확인했다. 외부 Project/Calendar sync는 실행하지 않았다.
- **이번 1~3 보완 구현/코드 리뷰 범위의 미해결 finding 0.** 운영 보고서·정책을 쓰는 재생성, Provider 실평가, 실제 매매 재기동과 미래 자연 성과 검증은 수행하지 않았다. 3항의 관측·유지 판단 경로는 구현했으나 실제 자연 생성/PREOPEN/PID/순수익 acceptance는 OPEN이다.
