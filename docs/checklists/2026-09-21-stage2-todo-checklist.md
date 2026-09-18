# 2026-09-21 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.



## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_handoff:start -->
<!-- compact_auxiliary_handoff_sha256:3a76e3ef4a10ef10498d804af32ee70ed01fa1a32a40e1f35a81824740817982 -->

## Compact auxiliary 장후 handoff

- 평가 원천 2026-09-17; 발행 2026-09-18; 적용 2026-09-21. 선정 상태 `incumbent_preserved`, 평가 상태 `source_contract_blocked`.
- 정책 bundle `4d4bce68f1e27fe50afab4b24645406d469d701326a7bc86b91d2a121d737332`; consumer generation `5472169d13176fd6529071ec2667062379453f0e98dab6082eafc19dc2cf0698`. 실제 PID 소비 및 자연 비용 후 성과는 미확인이다.
- 기존 owner `KiwoomCommonHealthOpportunityCostAcceptance0917`; 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 결손 net은 null이며 이 기록은 주문·guard·provider 변경 승인이 아니다.

<!-- compact_auxiliary_handoff:end -->

## R0–R3 독립 AI 연구 폐기

사용자 지시로 `scalping.micro_reversion.ai_quality_cycle` 장후 실행기·R2/R3 인계·legacy/current-axis 전용 런타임 및 파생 산출물을 제거한다. 별도 OPEN 복구 작업을 만들지 않는다. 현행 compact·AI 원천/라벨·주문/체결·공유 경제성 owner는 보존한다. 구현·검증·삭제 증거는 [폐기 리뷰](../audit-reports/2026-09-18-ai-quality-cycle-retirement-review.md)를 따른다. 코드 선택·실제 PID 소비와 장후 전체 DONE은 별도다.

## Low-price actual 정책 자연 적용·경제성 Acceptance

- [ ] `[LowPriceExpandedResearchRepair0918] 저가주 연구 입출력·해시·추천 handoff 보완과 배포·실소비 확인` (`Due: 2026-09-21`, `Slot: PREOPEN`, `TimeWindow: 07:35~09:35`, `Track: RuntimeStability`)
  - Source: [LP-A0–A7 구현 종결](../audit-reports/2026-09-19-low-price-actual-paired-implementation-closure.md), [원래 Acceptance·History](2026-09-18-stage2-todo-checklist.md#저가주-확장-연구-보완자연-경제성-검증), [상세 계획](../proposals/low-price-two-leg-actual-conditioned-paired-economic-search-and-preopen-runtime-consumer-improvement-plan-2026-09-18.md). [LP-B0–B6·수동 청산 정정 종결](../audit-reports/2026-09-19-low-price-exploration-manual-close-implementation-review.md), [후속계획](../proposals/low-price-two-leg-exploration-promotion-gate-separation-and-economic-evidence-completion-plan-2026-09-19.md).
  - 승인/History: 기존 사용자 구현·리뷰·commit/push·future immutable 배포 승인과 source9/17/pub9/18/effective9/21 incumbent_preserved/mutation0 증거를 유지한다. 완료된 LP0–LP6/Q0–Q5 또는 unchanged 전체 grid/raw를 재실행하지 않는다.
  - Acceptance: 정상7:35 공통 PREOPEN의 exact-date applied/hash, native preflight/service/machine의 selected source·실제PID 소비를 확인한다. Writer/reader/hash·기존accepted profile·등록된 미래seed/BBO/수량·same-date peer/비용 후 비교경제성의 기존 잔여조건을 보존한다. 자연 actual entry/fill·COMPLETED 비용 후 EV/관측일당 순익은 적용 버전에 귀속하고 미발생/null/sample/source/custody를 분리한다. Implementation closure는 자연 경제 개선 acceptance가 아니다.
  - 권한 경계: 조기 PREOPEN/수동 trading service restart·주문·새profile enrollment·quantity/target/cost/grid/floor·operator veto/custody/provider/Main restart/guard 변경 없음. 기존quarantine3·동일날짜 freeze·same-stage·rollback·hard safety를 유지한다. 전체chain 외부 FAIL을 본 family PASS로 바꾸지 않는다.
  - 다음 조치: 정상기동 receipt가 없으면 future_due/source_gap, 표본이 부족하면 hold_sample, 실제 source/경제조건을 닫으면 기존 unused paired window의 단일profile/axis 승격 경로로 넘긴다. 별도 신규 실행owner 없이 본ID를 유지한다.

  - LP-B 구현 Closure: source9/17/pub9/19/effective9/21 research2profile·distinct3개, 보조 carry CF3개 모두 순익/day 개선 없음. Applied manual13행/20leg의 역사 보정, actual/model custody 분리, v10/v9·v4 검증 및 verified incumbent carry/mutation0. Receipt: `tmp/low-price-exploration-manual-close-20260919/`. 자연 적용/PID/경제 개선과 whole-chain 외부 FAIL은 미완료로 유지.

## 삼성 native 경제성 및 기존 pipeline 자연 acceptance

- [ ] `[CodeImprovementWorkorderReview0918] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:45~20:35`, `Track: ScalpingLogic`)
  - Pipeline 재리뷰/정리 및 다음 삼성 분석: [owning review](../audit-reports/2026-09-18-pipeline-rereview-cleanup-and-samsung-machine-entry-analysis.md), `tmp/pipeline-rereview-samsung-analysis-20260918/`. 중첩 schema 손상 fallback/strict OPEN을 수리·회귀 검증하고 불필요 과거 진단125개만 제거, 원 불일치/현재/rollback 보호. 삼성 source/정책/독립 service는 read-only이며 완료 pair0/source gap을 natural wait나 no-edge로 바꾸지 않음. 배포·후행 재인계 receipt와 자연 PID/parity OPEN을 분리한다.
  - Pipeline verbosity Source/Closure: [PV0–PV6 계획](../proposals/pipeline-event-verbosity-incremental-parity-and-consumer-cost-optimization-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-pipeline-event-verbosity-incremental-review.md), `tmp/pipeline-verbosity-incremental-20260918/` receipts. 운영 producer/종료·handover·publication/증분·정정·missing/resource 및 실제 후행 소비 계약을 검증한다. 동일 `order_pipeline_event_compaction_v2_shadow`의 source/resource/자연 OPEN을 `defer_evidence`로 보존하고 반복 신규 구현/provider/full-wrapper recovery 또는 전체 chain/PREOPEN GREEN으로 바꾸지 않는다. raw·주문·정책·threshold/quantity/budget/custody/override·resource floor 및 실행 중 release는 보존한다.
  - Pipeline 자연 Acceptance: 다음 유효 source-day의 전체/완료창 parity·정상 종료/restart coverage·실제 Sentinel/execution census 소비 및 제한 비용을 확인한다. 과거9/15/16 손실의 raw fallback/원인 미확정과9/17 bootstrap을 자연 표본 대기로 숨기지 않는다. 실제 PID/주문/EV는 이 진단으로 승인하지 않는다. 해당 native owner는 이 기존 code-workorder 실행 ID를 재사용하며 별도 중복 작업/cron을 만들지 않는다.

  - 삼성 implementation Source: [S0–S6 계획](../proposals/samsung-owner-quantity-native-economic-timing-plan-2026-09-18.md), [owning review](../audit-reports/2026-09-18-samsung-owner-native-economic-timing-implementation-review.md), `tmp/samsung-owner-economic-timing-20260918/`. 비교는 owner별 승인 수량 독립이며 shared capital authority 없음. 현재 9/19 checklist 부재 및 source-day9/18을 보존한다.
  - 삼성 Acceptance: 다음 eligible/blocked/recheck native root 및 SOR deferred opening의 최초 실행시점 source→cost/code/quantity/selected exit/admission/stage guard→원 order/fill terminal projection을 대사. 자연 independent model/candidate holdout floor·coverage를 충족하기 전 승격 금지. selector/unit config와 실제 PID 소비·실제 행동을 구분하고, actual root/version별 dedup rolling/cumulative 비용 모델 순익·tail·노출·오차를 확인. settled cash net/인과적 개선은 별도 근거 없으면 null. partial/취소 race/carry CF unsupported를 natural maturity로 숨기지 않는다.
  - 금지: 새 서비스/collector/DB·전수 raw 재실행·bot restart/주문/조기 PREOPEN 확정·hard guard/quantity/budget/custody/override/holdout 완화. 자연 입력이 selected exit pin이라는 이유만으로 전수 unsupported이면 source/code defect로 재개.


## 공통 자연 수용 인계

- [ ] `[KiwoomCommonHealthOpportunityCostAcceptance0917] 공통 health·실행 모델·compact 정책 자연 소비 및 실제 성과 검증` (`Due: 2026-09-21`, `Slot: ALL`, `TimeWindow: 07:00~20:35`, `Track: RuntimeStability`)
  - Source/History: [9/18 기존 stable ID 원 기록](2026-09-18-stage2-todo-checklist.md), [통합 계획 CI5](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md). 기존 CW/ADQ/Samsung/AVG_DOWN·공통 health·PREOPEN 외부 blocker와 별도 custody·override acceptance를 승계하며 완료된 구현 재검토를 새 owner로 복제하지 않는다.
  - Acceptance: 기존 정상 producer→lossless census/원자 plan→운영 CF→선행 실제 모델 검증→scope/route별 prompt holdout→dated policy→정규 PREOPEN/실제 PID·issued prompt→joint applied-version COMPLETED valid cost/profit의 rolling/cumulative 성과. source/model/pending/unsupported/no-edge·actual/partial/CF를 분리한다. source gap0·배포·scoped PASS는 자연EV 또는 전체 native DONE이 아니다. 모델·표본·일별 순익·tail·비용·hard guards를 유지한다.
  - Next: 다음 자연 입력의 plan/stop/route/coverage 생성과 모델 proof부터 확인한다. irrecoverable9/17 입력은 제외 유지; 같은 자료의 반복 실행·추정 복원 금지. 계획된 장전 밖 수동 apply/기동/주문 권한을 만들지 않는다.

## Limit-down 전용 축 폐기

- 사용자 지시로 전용 장후 보고/경제성/정책·관찰 슬롯·스캐너/PREOPEN 소비·verifier 요구를 작업본에서 제거하고 누적 전용 산출물을 삭제했다. 활성 OPEN 복구 owner를 만들지 않는다. 공유 원천과 과거 custody 안전은 보존한다.
- [폐기 리뷰](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md)에서 검증·삭제 증거와 선택 배포본 구분을 확인한다. 이 기록은 봇 재시작·주문·조기 PREOPEN 승인이 아니다.

- Limit-down 후속 리뷰·관련 커밋/푸시·immutable 배포: `fcfd7b8e5`. 검토 범위 결함0·통합1,531 passed(기존 wrapper 실패5/제외1은 baseline 재현)·물리 release6 passed·전용 산출물 잔여0. [최종 증거](../audit-reports/2026-09-19-limit-down-watch-retirement-review.md). main 정기 cron target 부재는 기존 상태이며 선택/route 검증과 분리한다. 독립 unit pin·공유 원천/guard 보존; 기동/주문/조기 PREOPEN 미실행·PID 소비 미확인.
