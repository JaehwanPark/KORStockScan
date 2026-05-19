KORStockScan 작업 기본 규칙:

## 1. 우선 참조

- 작업 시작 전 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8과 당일 `docs/YYYY-MM-DD-stage2-todo-checklist.md` 상단 요약(`오늘 목적`, `오늘 강제 규칙`)을 먼저 읽는다.
- 튜닝 원칙, 판정축, rollback guard, active/open 상태는 `Plan Rebase`를 기준으로 삼고, 실행 작업항목은 날짜별 checklist가 소유한다.
- 현재 active/open 상태는 `Plan Rebase` §7~§8을 기준으로 읽되, 과거 checklist의 `[x]` 완료 항목은 현재 OPEN owner로 보지 않는다. 완료 항목은 증적/근거 링크이고, 현재 owner는 같은 행에 명시된 runtime owner 또는 현재 checklist의 열린 항목이다.
- `docs/plan-korStockScanPerformanceOptimization.prompt.md`는 세션 진입용 경량 포인터다. 일반 작업마다 필수로 읽지 않고, 사용자가 명시적으로 요구했거나 Plan Rebase 위치, Source of Truth 문서 맵, 현재 실행표가 불명확할 때만 확인한다.

## 1.1 현재 상태 기준 (`2026-05-19 KST`)

- 현재 단계는 `Plan Rebase`의 자동화체인 튜닝 단계이며, 목적은 손실 억제가 아니라 기대값/순이익 극대화다.
- 중심 루프는 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`다. 산출물/consumer/apply 계약은 `docs/report-based-automation-traceability.md`가 소유한다.
- 장중 runtime threshold mutation은 금지한다. 기본 적용 경로는 postclose artifact와 AI/deterministic guard를 거친 다음 PREOPEN `auto_bounded_live` runtime env다. 사용자 운영 override 이력은 `docs/archive/plan-rebase-runtime-history-2026-05-19.md`에 보존하고, 현재 owner 판정에는 selected family/provenance/post-apply attribution만 남긴다.
- `lifecycle_decision_matrix_runtime`은 ADM 확장 umbrella owner다. 기존 Entry ADM, Holding/Exit ADM, submit 관찰, scale-in bias adapter를 `entry`, `submit`, `holding`, `scale_in`, `exit` arm으로 감싸며 기본 OFF, auto-bounded micro canary 후보로만 열린다.
- 기존 fixed threshold는 삭제하지 않고 역할을 바꾼다. broker submit guard, stale quote submit block, price freshness, hard/protect/emergency stop, account/order/cooldown/qty guard는 `hard_safety`; `BUY_SCORE_THRESHOLD`, VPW/strength/momentum, entry score cutoff는 `baseline_prior`; latency caution, score65_74 probe, soft stop/holding flow, scale-in price guard는 `bounded_tunable`; fallback scout/main, fallback single, latency fallback split-entry, legacy latency composite, closed shadow axes는 `legacy_archive`다.
- lifecycle matrix와 ADM의 우선순위는 `hard safety veto -> account/order/broker guard -> lifecycle matrix runtime policy -> 기존 ADM adapter -> baseline fixed threshold fallback`이다. matrix/ADM은 broker submit guard나 stale/price freshness/stop/qty guard를 우회할 수 없다.
- sim-first lifecycle은 새 독립 체인이 아니라 기존 threshold-cycle 자동화체인의 입력/해석 범위다. 스캘핑과 스윙의 BUY/selection 가능 후보 전체를 `selection -> entry -> holding -> scale_in -> exit` virtual lifecycle로 넓게 실행해 최적 threshold 후보와 기능개선 workorder를 찾지만, 실주문 enable/cap 해제/provider 변경/bot restart의 단독 근거로 쓰지 않는다. `scalp_sim_candidate_window_expansion`은 2026-05-19 장중 사용자 override로 score 55~100 WAIT/blocked 후보까지 sim-only로 넓힌 관찰 owner이며, `scalp_sim_ai_budget_manager`는 확대된 sim holding의 OpenAI 호출을 상태변화/예산 기반으로 제어하는 sim-only owner다. 둘 다 `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only`를 유지한다. sim-only 후보는 BUY 분석/주문 텔레그램 알림을 보내지 않고 provenance만 남기며, sim AI budget은 provider route, BUY/submit threshold, broker guard를 변경하지 않는다.
- live 스캘핑 AI route는 OpenAI 고정이다. provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다. OpenAI 초기화 실패로 Gemini fallback이 발생하면 runtime incident로 본다.
- 스캘핑 entry/price/holding은 자동화체인 attribution으로 판정한다.
  - score 50 fallback/neutral은 신규 BUY 제출로 내려보내지 않고 `blocked_ai_score`로 보류한다.
  - score bucket은 baseline prior와 feature일 뿐 score 단독으로 BUY/WAIT/DROP을 확정하지 않는다.
  - `dynamic_entry_price_resolver_p1`/`dynamic_entry_ai_price_canary_p2`는 entry price owner다. passive probe submit revalidation이 `stale_context_or_quote`이면 브로커 제출 전 차단한다.
  - `soft_stop_micro_grace`, selected `soft_stop_whipsaw_confirmation`, `holding_flow_override`, Entry/Holding ADM, lifecycle matrix는 hard/protect/emergency/order safety를 우회하지 않는다.
  - scale-in price resolver/dynamic qty safety는 유지한다. 신규/추가매수 1주 cap 해제는 `position_sizing_cap_release` approval request 이후 사용자 승인으로만 다룬다.
- `scalp_ai_buy_all_live_simulator`, swing dry-run, probe/counterfactual 표본은 `actual_order_submitted=false` authority로 본다. source bundle과 approval request 근거가 될 수 있지만 real execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다. sim-first 탐색에서는 예수금 부족, 1주 cap, 실주문 미제출을 후보 제외 사유가 아니라 provenance tag로 남긴다.
- 스윙은 dry-run self-improvement 체인이다. `swing_lifecycle_audit`, `swing_threshold_ai_review`, `swing_improvement_automation`, `swing_runtime_approval`이 장후 source bundle을 만들 수 있지만 별도 approval artifact 없이는 env apply, one-share real canary, scale-in real canary, 전체 실주문 전환 금지다. `swing_strategy_discovery_sim`은 safe pool 후보를 sim-only candidate/8-arm으로 확장하고, `swing_strategy_discovery_label_builder`와 `swing_strategy_discovery_ev_report`가 label/EV/source-only 분석을 수행한다. 이 체인은 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`, `decision_authority=swing_sim_exploration_only`를 유지하며 기존 스윙 runtime이나 `recommendation_history`를 대체하지 않는다.
- `BUY Funnel Sentinel`, `HOLD/EXIT Sentinel`, `panic_sell_defense`, `panic_buying`, `System Error Detector`는 report-only/source-quality/incident 입력이다. `panic_regime_mode`는 `NORMAL -> PANIC_DETECTED -> STABILIZING -> RECOVERY_CONFIRMED` risk-regime 해석 계층이고, V2.0 후보는 scalping `entry_pre_submit` 전용 `panic_entry_freeze_guard`다. `panic_buy_regime_mode`는 `NORMAL -> PANIC_BUY_DETECTED -> PANIC_BUY_CONTINUATION -> PANIC_BUY_EXHAUSTION -> COOLDOWN` risk-regime 해석 계층이고, V2.0 후보는 기존 보유분 TP/runner 전용 `panic_buy_runner_tp_canary`다. approval artifact, runtime env key, rollback guard, same-stage owner rule 없이 score/stop/TP/trailing/threshold/provider/bot restart/자동매도/미체결 주문 cancel/holding-exit 강제 변경/추격매수/시장가 전량청산 금지다.
- 새 관찰지표는 생성 시점에 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언해야 한다. 계약이 없으면 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.
- 승률은 `diagnostic_win_rate`, EV는 `primary_ev`다. `simple_sum_profit_pct`는 EV가 아니며, EV 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 명명한다.
- `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`, legacy latency composite, closed shadow axes는 archive 기준 historical/reference다. 재개하려면 새 workorder, 새 rollback guard, 새 checklist가 필요하다.

## 1.2 AGENTS.md 일일 개정 절차

- AGENTS.md는 매일 작업 현황에 맞춰 갱신할 수 있는 `작업 지시 snapshot`이다. 단, 실행 작업항목의 원본 소유자는 항상 날짜별 checklist이고, 튜닝 원칙/active-open 판정의 원본은 `Plan Rebase`다.
- 장전 또는 작업 시작 시에는 `Plan Rebase` §1~§8과 당일 checklist 상단 요약을 읽고, AGENTS.md의 `현재 상태 기준` 날짜와 active owner 요약이 맞는지 확인한다.
- 장중/장후에 owner, live/observe/off 상태, rollback guard, 다음 판정 checklist가 바뀌면 먼저 `Plan Rebase` 또는 날짜별 checklist를 수정하고, 그 다음 AGENTS.md `1.1 현재 상태 기준`만 짧게 갱신한다.
- AGENTS.md에는 자동 파싱 대상 `- [ ]` 신규 작업항목을 만들지 않는다. 미래 작업, 특정 시각 작업, 재확인 작업은 날짜별 checklist에만 `Due`, `Slot`, `TimeWindow`, `Track`이 있는 체크박스로 남긴다.
- AGENTS.md에 과거 checklist ID를 링크할 때는 `완료 기록`, `현재 owner`, `다음 확인 owner`를 구분한다. `[x]` 완료 항목을 현재 OPEN owner처럼 쓰지 않는다.
- 매일 갱신 시 최소 확인 항목은 `entry owner`, `holding/exit owner`, `operating override`, `observe/report-only 축`, `OFF/폐기 축`, `Project/Calendar 동기화 규칙`이다.
- 문서 갱신 후에는 parser 검증을 실행한다. Project/Calendar 동기화는 AI가 직접 실행하지 않고, 사용자에게 표준 동기화 명령 1개만 남긴다.

## 2. 판정 원칙

- 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
- `Plan Rebase` 기간 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
- 실전 변경은 동일 단계 내 1축 canary만 허용한다. 진입병목축과 보유/청산축처럼 단계, 조작점, 적용시점, cohort tag, rollback guard가 분리되면 stage-disjoint concurrent canary로 병렬 검토할 수 있다.
- 신규/보완 alpha 튜닝축은 shadow 없이 `canary-only`로 본다. 단, AI transport/schema, statistical action weight, decision matrix처럼 문서에 observe/report-only로 명시된 운영/지원축은 실전 주문·청산 판단을 바꾸지 않는다.
- 원격/server 비교값은 Plan Rebase 의사결정 입력에서 제외한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용한다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외한다.
- `full fill`과 `partial fill`은 합치지 않는다.
- 승률은 보조 진단이고, 기대값/순이익 판정은 EV primary metric으로 한다.
- daily-only 지표는 safety/source-quality/운영 trigger에는 쓸 수 있지만, live/canary/threshold apply 승인은 rolling/cumulative 또는 post-apply version window와 함께 본다.
- BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
- 원인 귀속이 불명확하면 리포트 정합성, 이벤트 복원, 집계 품질부터 점검한다.
- 운영 자동화 증적(cron/runbook/manifest/report/parser 정상화)은 전략 효과나 live 승인 근거와 분리한다.
- 답변은 가능하면 `판정 -> 근거 -> 다음 액션` 순서로 정리한다.

## 3. 문서/자동화

- 관련 문서가 있으면 함께 업데이트한다.
- 날짜별 checklist 상단은 매번 장문의 `목적/용어 범례/운영 규칙` 반복본을 복제하지 말고, `오늘 목적`과 `오늘 강제 규칙`만 짧게 적는다. 상세 용어/정책/가드는 `Plan Rebase` 또는 관련 부속문서를 참조한다.
- 개인문서(`docs/personal-decision-flow-notes.md`)는 다른 문서의 `Source`/판정 근거 링크로 참조되지 않는다. 실행 판정의 근거는 checklist/report/plan 기준문서에서 직접 가져온다.
- 미래 작업, 특정 시각 작업, 재확인 작업은 답변에만 남기지 말고 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 기록한다.
- checklist 작업항목을 만들거나 수정했으면 parser 검증을 수행하고, Project/Calendar 동기화는 토큰 존재 여부를 확인하지 말고 사용자에게 실행할 1개 명령을 남긴다.
- 문서 변경 후 parser 검증은 AI가 실행한다. GitHub Project / Google Calendar 동기화는 AI가 직접 실행하지 않고, 사용자가 수동 실행한다.
- 사용자에게 남길 동기화 명령은 아래 1개로 통일한다.
  - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar`
- 자동화 규칙, cron, workflow, wrapper를 바꾸면 운영문서와 checklist를 같은 변경 세트로 맞춘다.

## 4. 실행 환경

- Python 작업은 프로젝트 `.venv`를 기본으로 사용한다.
- 패키지 설치/업그레이드/제거 전에는 사용자 의사결정을 받는다.
- 임시 스크립트보다 재현 가능한 명령과 프로젝트 표준 실행 경로를 우선한다.
