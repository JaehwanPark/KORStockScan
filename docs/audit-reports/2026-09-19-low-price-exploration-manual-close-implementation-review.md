# Low-price LP-B0–B6 및 수동 청산 역사 성과 정정 종결

기록: 2026-09-19 KST. 원천9/17·발행9/19·다음 적용9/21. 사용자 승인 범위는 구현·리뷰/수정·커밋/푸시·미래 immutable 배포·제한 장후 재생성이다. 자연 applied/PID/실제 신규 개선은 동일 [LowPriceExpandedResearchRepair0918](../checklists/2026-09-21-stage2-todo-checklist.md) OPEN이다. 9/19 checklist는 없다.

소유 계획: [LP-B0–B6](../proposals/low-price-two-leg-exploration-promotion-gate-separation-and-economic-evidence-completion-plan-2026-09-19.md). 원래 LP-A의 기존 custody/원천/가드/단일 lock/atomic/freeze/실제 관측/후행을 재사용했다. 새 엔진·CLI·서비스·root module·거래 권한은 만들지 않았다.

## 원인과 수동 청산 보정

과거 보고서의 HELD 행은 이후 applied manual journal을 읽지 않았고 현재 state가 새 거래일로 이동하면 과거 청산 결과를 재연결하지 못했다. `episode_manual_exit_receipts.json`의 broker-verified applied 기록을 owner/symbol/entry date/order identity/as-of/whole remaining quantity로 검증해 역사 actual projection만 보정했다. 원본 state/journal/주문/수량/target은 수정하지 않았다. Duplicate/reserved/foreign owner/future date/수량불일치/기존 partial exit는 완료처리하지 않는다. 비용 exact 귀속이 갱신되지 않은 행은 fixed 추정으로 명시하고 손실 및 알 수 없는 fill time을 보존했다.

13행·20leg가 회복됐다. 카카오 오전의 unresolved3→0, 정오2→0. 비용 후 역사 실제 합계는 오전 -30,034.049원, 정오 -64,288.249원(추정 비용)이다. 과거 수동 청산 손실 복원이며 신규 손실 또는 새 경제 개선액이 아니다. 카카오 오전 후반의8/18 역사2leg에는 closing receipt가 없어 원천 미확정으로 남긴다. 현재/현재 실제 epoch의 보유로 단정하지 않으며 임의 가격으로 청산하지 않는다. 정확한 원래 owner/date/quantity의 closing receipt가 향후 복구되면 같은 projection 경로로 해소된다.

별도 정정: frozen v9의 카카오 오전 후반 actual8leg/20일/epoch unresolved0은 이미 floor를 통과했고 distinct calibration1개가 있었다. 이전 eligible0/replay0 설명은 가상 carry disposition과 실제 custody를 혼동한 오류다. Report v10은 research·promotion·actual epoch unresolved·model carry를 분리한다.

## 경제 결과와 적용 정책

Source-valid 완료1leg 연구 착수와 실제8leg/5일·flat·native execution/capital/authority 승격 기준을 분리했다. 최초 범위는 Kakao late-morning/Youngone morning의 기존 두 tightening axis, 동일 캐시/순차 경로/비용/기간이다. Identical 축은 제외해 distinct3개를 계산했다. Calibration 전체 개선만으로 선정하지 않고 두 half의 별도 비교 및 기존 최소3완료leg를 확인하도록 재리뷰 보완했다. 사전 고정 미래30/16일 계약과 단일 frozen selection은 유지했다.

Primary conservative CF는 양측 모델 carry로 resolved0이며 joint ΔEV/순익은null이다. 기존 original-target continuation price-touch CF는 별도 진단으로만 계산했으며 ranking·native 실행·승격 근거가 아니다. 아래는 unit quantity1, calibration57일의 추정 비용 진단이다.

| CF 보조 비교 | Baseline EV / Challenger EV | Baseline 순익/day / Challenger 순익/day | ΔEV(%p) | Δ순익/day(원) |
| --- | --- | --- | --- | --- |
| Kakao drawdown | 0.307559 / 0.312915% | 96.36052632 / 76.84824561 | +0.005356 | -19.51228071 |
| Youngone drawdown | 0.012939 / 0.012903% | 13.26789474 / 12.48807018 | -0.000036 | -0.77982456 |
| Youngone near-low | 0.012939 / 0.013175% | 13.26789474 / 12.16649123 | +0.000236 | -1.10140351 |

연구2profile/3distinct·보조resolved3·동시 개선0·promotion0·mutation0. 후보는 검증된 incumbent 보존이다. Policy hash `590642d99e263254fc10663b01f62966d6461f78a63a4574998115296a738ebb`. Actual/CF 손익을 합치거나 native10share 실적으로 환산하지 않았다. 보존 정책은 실제 개선 확정이 아니다.

Report v10/v9의 declared schema와 candidate v4 source hash/date를 결속했고 research bool은 strict actual floor/권한 증거를 대체하지 않는다. 후보 발행일 이후 다음 정상 거래일9/21 정책을 격리 준비했으며 candidate/applied validation 및 loader58ready/기존quarantine3를 확인했다. 실제 적용 파일은 정상 PREOPEN에 발행하며 서비스는 validated applied만 소비한다.

## 검증·후행·배포

Self review→수정→재리뷰→회귀 검증을 닫았다. 영향 범위671PASS, v9/v10·manual/readmission 추가 회귀13PASS, 원격 삼성 변경을 보존한 병합 뒤362PASS, 마지막 producer233PASS 및 stability 포함14PASS다. 겹치는 테스트 수를 합산하지 않는다. Compile/diff 및 문서 link/owner/print-only parser를 검증한다. Shell 변경0으로 기존 wrapper receipt를 재사용한다.

Native bounded regeneration은 broker API/추가 시장조회 없이 기존 캐시만 사용했다. 전량 raw/expanded204종목·1020profile 재실행0, Main/거래 서비스 start/restart/조기 PREOPEN/주문0이다. 입력 전 report/candidate/journal 원본과 SHA를 보존하고 active writer/이미 소비된 candidate를 확인했다.

Daily→EV→runtime→tower→canonical checklist→strict `require-summary-handoff`→summary-only controller가 현재 research/promotion generation을 소비하도록 갱신했다. Whole strict의 외부18issue(기존 expanded/AI/entry policy/predecessor/strategy scope 등)와 controller blocked 상태는 유지하며 family 검증으로 whole DONE을 부여하지 않는다. Exact 최종 issue/consumer/PREOPEN 준비 및 selected immutable source는 아래 receipt를 따른다.

증거: `tmp/low-price-exploration-manual-close-20260919/inputs-before.json`, `economic-evidence.json`, `handoff.json`, `prepared-policy-evidence.json`, `strict-release-final.json`, `controller-release-final.json`, `deployment.json`. 미래 source root는 `/home/ubuntu/KORStockScan-runtime-releases/low-price-exploration-manual-close-reviewed-20260919`다. Remote main/task branch push 및 selector/live·preflight template pin을 같은 clean source로 맞춘다. Actual PID 소비는 false이고 자연 확인은9/21 기존 owner에 남긴다.

복구/대기 경계: 실제 표본 미달은 추가 valid fill로 해소될 수 있다. 과거 closing/capture/BBO/capital 결손은 달력 경과로 회복되지 않는다. 새 native 관측은 기존 producer로 축적하되 과거를 대체하지 않는다. 이번 범위는 구조 수리와 가능한 경제 진단·보존 정책/자동 소비 준비를 종결했으며 실제 EV·일별 순익 동시 개선은 확인되지 않았다.
