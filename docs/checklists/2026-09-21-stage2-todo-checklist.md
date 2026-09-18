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
  - Source: [LP-A0–A7 구현 종결](../audit-reports/2026-09-19-low-price-actual-paired-implementation-closure.md), [원래 Acceptance·History](2026-09-18-stage2-todo-checklist.md#저가주-확장-연구-보완자연-경제성-검증), [상세 계획](../proposals/low-price-two-leg-actual-conditioned-paired-economic-search-and-preopen-runtime-consumer-improvement-plan-2026-09-18.md).
  - 승인/History: 기존 사용자 구현·리뷰·commit/push·future immutable 배포 승인과 source9/17/pub9/18/effective9/21 incumbent_preserved/mutation0 증거를 유지한다. 완료된 LP0–LP6/Q0–Q5 또는 unchanged 전체 grid/raw를 재실행하지 않는다.
  - Acceptance: 정상7:35 공통 PREOPEN의 exact-date applied/hash, native preflight/service/machine의 selected source·실제PID 소비를 확인한다. Writer/reader/hash·기존accepted profile·등록된 미래seed/BBO/수량·same-date peer/비용 후 비교경제성의 기존 잔여조건을 보존한다. 자연 actual entry/fill·COMPLETED 비용 후 EV/관측일당 순익은 적용 버전에 귀속하고 미발생/null/sample/source/custody를 분리한다. Implementation closure는 자연 경제 개선 acceptance가 아니다.
  - 권한 경계: 조기 PREOPEN/수동 trading service restart·주문·새profile enrollment·quantity/target/cost/grid/floor·operator veto/custody/provider/Main restart/guard 변경 없음. 기존quarantine3·동일날짜 freeze·same-stage·rollback·hard safety를 유지한다. 전체chain 외부 FAIL을 본 family PASS로 바꾸지 않는다.
  - 다음 조치: 정상기동 receipt가 없으면 future_due/source_gap, 표본이 부족하면 hold_sample, 실제 source/경제조건을 닫으면 기존 unused paired window의 단일profile/axis 승격 경로로 넘긴다. 별도 신규 실행owner 없이 본ID를 유지한다.
