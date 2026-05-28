# 2026-05-05 Stage2 To-Do Checklist

## 오늘 목적

- `2026-05-05`는 어린이날 KRX 휴장일이므로 실전 장전/장중/장후 판정 작업을 실행하지 않는다.
- 기존 `0505` 작업항목은 휴장 보정으로 `2026-05-06` 체크리스트에 이관한다.
- 이 파일은 workorder/Project 상태 drift 방지를 위한 휴장 기록으로 유지한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `latency_entry_price_guard`는 신규 entry canary가 아니라 기존 active entry canary의 BUY 체결품질 보호 가드로 해석한다.
- 3틱은 v1 임시값이며, 재튜닝 전에는 정식 정책으로 고정하지 않는다.
- fallback/scout/split-entry는 재도입하지 않는다.
- `NaN cast` follow-up은 live canary가 아니라 런타임 안정화/집계 품질 보강 축으로만 다룬다.
- 휴장일에는 실전 `PREOPEN/INTRADAY/POSTCLOSE` 작업을 새로 열지 않는다. 이월 작업은 다음 KRX 운영일인 `2026-05-06`에 `Due`를 다시 고정한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:10)

- [x] `[LatencyEntryPriceGuard0505] 3틱 v1 fill/slippage/profit 재튜닝 판정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `latency_override_defensive_ticks=3` 적용 cohort와 기존/비적용 normal cohort를 `fill_rate`, `realized_slippage`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`, `normal_slippage_exceeded`로 비교한다.
  - why: 3틱은 v1 임시값이며 1주 데이터 없이 정식 정책으로 고정하지 않는다.
  - 다음 액션: 우위가 확인되면 유지 또는 v2 전환 설계로 넘기고, fill 손실/기회비용이 크면 1틱/2틱/가격대별 table 재튜닝 후보를 연다.

- [x] `[LatencyEntryPriceGuardV2] bps/가격대별 defensive table 설계` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: ScalpingLogic`)
  - Source: [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: fixed tick 대신 저가주/중가주/고가주 가격대별 bps 부담을 반영한 defensive table을 설계한다.
  - why: 동일 3틱이라도 가격대별 bps 비용이 달라 기대값/체결률 trade-off가 왜곡될 수 있다.
  - 다음 액션: v2 승인 전까지 v1 3틱은 임시값으로만 유지하고, table 후보는 shadow/counterfactual 로그부터 추가한다.

- [x] `[LatencyExitPriceGuardReview] 매도/청산 latency 가격가드 현황 명문화` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: 이번 변경은 BUY 진입가 전용이다. SELL/청산가에 latency 위험 대칭 정책이 있는지 확인하고, 기존 정책 유지/별도 canary/observe-only 중 하나로 명문화한다.
  - why: 진입 방어폭만 강화하고 청산가 정책을 불명확하게 두면 realized slippage와 missed upside 해석이 섞인다.
  - 다음 액션: 매도 측 정책 변경이 필요하면 진입가 v1 재튜닝과 별도 축으로 분리하고, 같은 날 한 축 canary 원칙을 유지한다.

- [x] `[NaNCastGuard0505] NaN cast runtime 안정화 후속계획 확정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:10`, `Track: RuntimeStability`)
  - Source: [2026-04-28-nan-cast-guard-hotfix-report.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-28-nan-cast-guard-hotfix-report.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 원격과 동일 patch set 복제 여부가 아니라 메인 코드베이스 기준 `NaN/inf` 안전 캐스팅 최소 범위, 재발건수, 상태전이 실패 경로, upstream source 후보(`buy_qty/buy_price/target_buy_price/marcap/preset_tp_*`, websocket `curr/ask_tot/bid_tot`, 체결 `price/qty`)를 확정한다.
  - why: `NaN cast`는 루프 중단과 체결 후 상태전이 실패를 만들어 기대값과 미진입/미청산 기회비용을 직접 훼손한다. same-day hotfix를 보고서로만 남기면 메인 기준의 수정범위와 재발 방지 계획이 비어 있다.
  - 다음 액션: 메인 기준 최소 safe cast patch 범위와 테스트(`pytest`/`py_compile`)를 잠그고, 재발이 있으면 source 추적 작업을 다음 거래일 PREOPEN/POSTCLOSE checklist로 승격한다.

- [x] `[PreSubmitGuardDist0505] 80bps 임계 분포 부록 및 percentile 재앵커` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:25`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: 최근 `30~60` 영업일 `submitted` 코호트를 대상으로 `(best_bid - submitted_price) / best_bid * 10000` 분포를 재구성해 histogram과 `p90/p95/p99/p99.5`를 확정하고, `80bps`가 어느 percentile에 위치하는지 문서 부록으로 고정한다. 현재 `2026-04-28~2026-04-29` stage-paired 표본 `8건`은 provisional reference로만 사용한다.
  - why: 대한전선 단일 사례는 `337~412bps` outlier를 보여주지만, `80bps` 자체의 적정성은 분포 기반으로 다시 잠가야 한다.
  - 다음 액션: `80bps`가 너무 타이트하면 완화 후보를, 너무 느슨하면 강화 후보를 열고, 결정값은 `PreSubmitGuardKPI0505`와 함께 SLO로 고정한다.

- [x] `[PreSubmitGuardObserve0505] 비-SCALPING observe-only guard logging 범위 확정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: `BREAKOUT/PULLBACK/RESERVE` 등 비-`SCALPING` 전략에 대해 차단 없는 `pre_submit_price_guard_observe` 이벤트를 기록할지, 기록한다면 동일 임계(`80bps`)와 어떤 필드(`submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, strategy`)를 남길지 확정한다.
  - why: 차단 없는 observe-only는 회귀 위험이 거의 없으면서도 P1 resolver 설계의 사각지대를 줄인다.
  - 다음 액션: 구현 범위가 잠기면 1~2주 누적 후 전략별 pathology 존재 여부를 닫고, 차단 확대 여부는 분포 기준으로만 결정한다.

- [x] `[BuyPriceSchemaSplitP1] submitted_order_price canonical 승격 조건 확정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~17:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: `BUY_ORDERED.buy_price`를 언제 `submitted_order_price` canonical로 승격할지 closing condition을 문서로 고정한다. 최소 조건은 `P1 resolver 도입`, downstream 손익/보유/리포트 경로 영향도 목록화, migration/alias 정책 확정이다.
  - why: schema 보존은 P0에서는 맞는 결정이지만, closing condition 없이 두면 영구 부채가 된다.
  - 다음 액션: trigger가 잠기면 P1 change set에 schema split을 묶고, trigger가 아직 모호하면 막힌 조건을 명시한다.

- [x] `[DynamicEntryResolverIngress0505] P1 resolver ingress gate와 anchor case 확정` (`Due: 2026-05-05`, `Slot: POSTCLOSE`, `TimeWindow: 17:55~18:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: P1 승인 전 단계(`backtest -> observe-only -> canary`)와 각 단계 산출물(`가격차 분포`, `resolver divergence rate`, `submitted_but_unfilled_rate`, `slippage_bps`, `time_to_fill_p50/p90`)을 확정하고, `record_id=4219`가 backtest/observe-only에서 abort되는지 unit test anchor case로 고정한다.
  - why: ingress gate가 없으면 P1이 기술 판단이 아니라 정치적 승인 사안으로 변질된다.
  - 다음 액션: gate가 잠기면 `LatencyEntryPriceGuardV2`와 분리된 독립 change set으로 resolver 검증축을 연다.

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-05 15:45:38`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-05.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
