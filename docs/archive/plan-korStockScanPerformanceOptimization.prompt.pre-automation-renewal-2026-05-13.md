# 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

기준 시각: `2026-05-04 KST (Plan Rebase 현행화)`
역할: 다음 세션에서 중심 기준 문서로 진입하기 위한 **경량 포인터**다.

이 문서는 세션 시작용 경량 포인터다.
현재 Plan Rebase의 중심 기준은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)를 우선한다.
과거 일정, 장문 경과, 상세 해설은 `archive`, `Q&A`, `execution-delta`, `performance-report`, `data/report`/`data/threshold_cycle` README로 분리한다.

## 현재 Source of Truth

1. 현재 활성 기준은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)다.
2. 운영 실행표는 날짜별 `stage2 todo checklist`를 우선한다.
3. 현재 실행표는 [2026-05-04-stage2-todo-checklist.md](./checklists/2026-05-04-stage2-todo-checklist.md), [2026-05-06-stage2-todo-checklist.md](./checklists/2026-05-06-stage2-todo-checklist.md), [2026-05-07-stage2-todo-checklist.md](./checklists/2026-05-07-stage2-todo-checklist.md), [2026-05-08-stage2-todo-checklist.md](./checklists/2026-05-08-stage2-todo-checklist.md)를 본다.
4. 정기 report inventory와 Markdown 누락 후보는 [data/report/README.md](../data/report/README.md)를 본다.
5. threshold collector/report/apply plan 운영방법은 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)를 본다.
6. 원안 대비 실행 변경과 종료 이력은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)를 본다.
7. 반복 판단 기준과 감리 Q&A는 [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)를 본다.
8. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` 등 영문 축 표현은 [Plan Rebase 용어 범례](./plan-korStockScanPerformanceOptimization.rebase.md#2-용어-범례)를 우선한다.

## 문서 맵

| 문서 | 역할 | 언제 먼저 보나 |
| --- | --- | --- |
| [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md) | Plan Rebase 중심 기준과 용어 범례 | 세션 시작 직후 |
| [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md) | 세션 시작용 경량 포인터 | 진입점 확인 시 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 운영 판단 기준/자주 묻는 질문 | 왜 이렇게 운영하는지 확인할 때 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 기본계획 대비 실행 변경사항 | 원안과 실제 실행이 달라졌을 때 |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과측정 기준과 최신 baseline | 장후/주간 성과판정 때 |
| [2026-05-04-stage2-todo-checklist.md](./checklists/2026-05-04-stage2-todo-checklist.md) | 다음 KRX 운영일 장전/장중/장후 실행표 | 5/4 운영 작업 수행 시 |
| [2026-05-06-stage2-todo-checklist.md](./checklists/2026-05-06-stage2-todo-checklist.md) | 휴장 이월 후속, threshold/AI/scanner/보유청산 잔여작업 | 5/6 후속 작업 수행 시 |
| [2026-05-07-stage2-todo-checklist.md](./checklists/2026-05-07-stage2-todo-checklist.md) | SAW-3, ADM-2 후속 설계 | 5/7 후속 작업 수행 시 |
| [2026-05-08-stage2-todo-checklist.md](./checklists/2026-05-08-stage2-todo-checklist.md) | SAW-4~SAW-6, 체결품질/시장맥락/orderbook readiness, OFI/QI expansion ladder | 5/8 후속 작업 수행 시 |
| [data/report/README.md](../data/report/README.md) | 정기 report inventory와 Markdown 누락 후보 | JSON/JSONL 대비 Markdown 필요성을 판단할 때 |
| [data/threshold_cycle/README.md](../data/threshold_cycle/README.md) | threshold collector/report/apply plan 운영방법 | threshold 자동화나 apply plan을 다룰 때 |
| [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md) | shadow/canary/historical 분류와 런타임 ON/OFF 기준 | OFF축 재개나 canary 성격이 애매할 때 |
| [archive/closed-observation-axes-2026-05-01.md](./archive/closed-observation-axes-2026-05-01.md) | 종료/폐기 관찰축 archive | 과거 축 재개 금지선을 확인할 때 |

## 문서 운영 규칙

1. 중심 기준은 `rebase` 문서가 소유하고, `prompt`는 세션 시작용 포인터만 남긴다.
2. 기본계획과 실제 실행이 달라지면 `execution-delta`에 먼저 적고, 현재 owner/참조문서가 바뀌면 같은 변경 세트에서 `prompt`도 반영한다.
3. 장후/주간 성과 기준선과 최근 수치는 `performance-report`에 누적하고, 과거 시점 진단본은 archive 성격으로만 유지한다.
4. 과거 일정표, 완료된 실험의 상세 경과, 이미 지나간 공격 일정은 `archive`로 이동한다.
5. `Q&A`는 문서 책임, 모니터링 기간, 해석 기준 같은 반복 참조 정책만 남긴다.
6. 모든 작업일정은 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다. 상대 일정이나 조건부 유예 문구는 사용하지 않는다.
7. report 생성 필요성은 [data/report/README.md](../data/report/README.md)의 누락 후보 기준으로 판단하고, 필요하면 날짜별 checklist에 작업계획을 만든다.
8. threshold 운영은 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)의 `manifest_only` 원칙과 PREOPEN/POSTCLOSE wrapper 기준을 따른다.
9. live 영향 관찰은 오전/오후 반나절을 넘기지 않는다. 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 닫는다.
10. 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행한다. 토큰/계정/운영 승인 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청한다.
11. 문서 변경 후 parser 검증은 AI가 수행한다. Project/Calendar 동기화는 토큰 존재 여부를 AI가 확인하지 말고 사용자 수동 실행 명령 1개를 반드시 남긴다.

## 최종 목표와 운영 원칙

1. 최종 목표는 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 현재 단계는 `Plan Rebase`다. 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
3. 실전 변경은 항상 `한 번에 한 축 canary` 원칙을 지킨다. 단, 진입병목축과 보유/청산축처럼 단계와 rollback guard가 분리되면 stage-disjoint 병렬 canary로 분리 판정할 수 있다.
4. 신규 관찰축/보완축은 `shadow 금지`, `canary-only`로 운영한다.
5. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 영구 폐기한다. 재개/승격/재평가 canary 대상이 아니다.
6. `NULL`, 미완료 상태, fallback 정규화 값은 손익 기준에서 제외한다. 손익 계산은 `COMPLETED + valid profit_rate`만 사용한다.
7. 장후 리포트의 우선 지표는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익` 순서다.
8. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리 해석한다.
9. `full fill`과 `partial fill`은 같은 표본으로 합치지 않는다.
10. 원인 귀속이 불명확하면 먼저 `리포트 정합성`, `이벤트 복원`, `집계 품질`을 점검한다.
11. 현재 entry owner는 `mechanical_momentum_latency_relief`, `dynamic_entry_price_resolver_p1`, `dynamic_entry_ai_price_canary_p2`다. 단, `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True`라 score 50 fallback/neutral은 신규 BUY 제출로 내려보내지 않고 `blocked_ai_score`로 보류한다. OFI/QI는 P2 내부 live 입력 feature이며 standalone hard gate가 아니다. P2 raw `SKIP` confidence `80~89`는 non-bearish OFI일 때만 P1 defensive 경로로 demotion한다.
12. 현재 보유/청산 owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`다. OFI smoother는 `holding_flow_override` 내부 postprocessor로만 쓰며 hard/protect/order safety와 기존 max defer/worsen guard를 우회하지 않는다. `bad_entry_refined_canary`는 `2026-05-04` 장후 OFF됐고 refined 후보는 report-only counterfactual로만 유지한다. `same_symbol_loss_reentry_cooldown`은 손실 후 동일종목 반복진입을 막는 임시 운영가드이며, 5/6에는 단독 hard cooldown이 아니라 하향 재진입 복합 threshold 후보로 재판정한다.
13. `2026-05-11 KST` 사용자 운영 지시로 main live AI routing은 OpenAI로 고정한다. `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS=15000`, `KORSTOCKSCAN_OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512`, `KORSTOCKSCAN_OPENAI_REASONING_EFFORT=auto`, startup `main_scalping_openai=ON`, OpenAI tier/provenance를 확인하고, Gemini fallback은 runtime incident로 본다.
14. threshold 자동화는 POSTCLOSE report와 PREOPEN apply plan까지만 허용한다. `ThresholdOpsTransition0506` 전 live runtime mutation은 금지하며 현재 apply mode는 `manifest_only`다.
15. 기준선/롤백/승격 판단은 문서 파생값이 아니라 DB 우선 스냅샷 실필드와 canonical JSON/JSONL에서 생성된 report를 기준으로 한다.

## 현재 기준 우선순위

`active/open` 요약은 현재 owner와 다음 판정 checklist만 남기고, 종료/폐기 축은 [closed observation archive](./archive/closed-observation-axes-2026-05-01.md)에서만 확인한다.

| 워크스트림 | 현재 상태 | 판정 | 다음 닫힘 시점 |
| --- | --- | --- | --- |
| `entry operating override` | `mechanical_momentum_latency_relief` ON, score 50 buy-hold override ON | score 50 fallback은 신규 BUY 보류. mechanical relief는 score 70대/저신호 제출병목 회복축으로만 유지 | `2026-05-04 INTRADAY` override 반영, `2026-05-06 POSTCLOSE` composite 판정 |
| `entry price` | P1 resolver + P2 AI price canary live, OFI/QI P2 내부 입력 ON, low-confidence non-bearish SKIP demotion ON | entry price active owner. OFI standalone entry gate 아님 | `2026-05-06 PREOPEN` OFI smoothing 로드 확인, `2026-05-06 POSTCLOSE` manifest_only family 판정 |
| `holding/exit` | `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`, OFI smoother 내부 postprocessor, 임시 `same_symbol_loss_reentry_cooldown` 운영가드. `bad_entry_refined_canary`는 5/4 장후 OFF | 보유/청산 active owner. OFI는 standalone EXIT gate가 아니라 flow 내부 debounce/confirm이다. 동일종목 손실 후 60분 쿨다운은 최종 threshold가 아니라 5/6 복합축 전환 후보. trailing/protect 민감도는 5/4 수익 실현 양호에도 weak borderline/PYRAMID 교차가 커서 5/6 단일 owner로 재판정. 오버나이트 flow `TRIM`은 부분청산 구현 전까지 `SELL_TODAY` 유지 | `2026-05-06 PREOPEN` OFI smoothing/refined OFF/overnight TRIM 로드 확인, `2026-05-06 POSTCLOSE` cooldown/composite/trailing-protect 판정 |
| `position sizing` | `initial_entry_qty_cap_1share` 유지, `MAX_*_COUNT`는 attribution counter, generic `AVG_DOWN` 평가는 제거됐다. scalping `AVG_DOWN` add_type은 `REVERSAL_ADD` 귀속으로만 남고, `SCALPING_ENABLE_PYRAMID`는 cooldown/pending/position cap/protection으로 관리 | count gate semantics 정리 완료, 동적 수량화만 OPEN | `2026-05-04 PREOPEN`, `2026-05-06 POSTCLOSE` |
| `AI engine` | OpenAI main live routing 고정. Gemini/DeepSeek는 명시 env 또는 OpenAI key/engine failure fallback/비운영 분석 경로로만 본다. OpenAI Responses WS는 별도 transport provenance로 관리한다 | `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `main_scalping_openai=ON` 확인 | `2026-05-11 INTRADAY` 사용자 운영 지시 반영 |
| `threshold/action weight` | threshold collector/report/apply plan 자동화. apply는 `manifest_only`. `entry_ofi_ai_smoothing`, `holding_flow_ofi_smoothing` family도 manifest_only 후보만 생성 | runtime mutation 전 단계 | `2026-05-06 POSTCLOSE` acceptance |
| `report inventory` | 정기 Markdown/JSON inventory와 누락 후보 정리. `preclose_sell_target`은 2026-05-10 제거되어 과거 증적용 산출물만 보존 | report README 기준으로 작업계획 생성 | active cron/source 아님 |
| `scanner/code debt` | scanner boundary, state handler split, runtime stabilization | 설계/분해 단계 | `2026-05-06~2026-05-08` checklist |

## 2026-05-04~2026-05-08 실행 맵

| 일자 | 핵심 실행축 | 실행 원칙 | 기대 산출물 |
| --- | --- | --- | --- |
| `2026-05-04` | runtime flag, dynamic entry price, OFI/QI provenance, holding flow, refined bad-entry, same-symbol loss reentry guard | 신규 다축 추가 금지. active owner health/provenance와 긴급 운영가드만 닫음 | PREOPEN 로드, INTRADAY health, POSTCLOSE keep/OFF/보류 사유, 유안타 하향 재진입 root-cause |
| `2026-05-06` | threshold ops transition, statistical action weight, report Markdown 후보, AI engine backlog, scanner/code debt, downtrend reentry composite | threshold live mutation 금지. acceptance와 report-only/observe-only 분리. 단독 cooldown은 복합 threshold 후보로만 판정 | threshold README 기준 운영확인, Markdown 누락 후보 작업계획 여부, cooldown/composite 전환 판정 |
| `2026-05-07` | SAW-3 eligible outcome, ADM-2 shadow prompt | decision-support ladder 유지 | runtime 판단 변경 없는 schema/readiness |
| `2026-05-08` | SAW-4~SAW-6 체결품질/시장맥락/orderbook readiness, OFI/QI expansion ladder | 3축 교차와 live 반영 금지. OFI/QI는 entry P2 내부 feature와 holding flow 내부 postprocessor로만 쓰고, 3/5/10분 wide OFI persistence는 스윙 전환 report-only 보조 증거로만 둔다 | 후속 calibration/decision-support 후보, stale 방지 owner |

## 승격/보류 게이트

1. `live` 승격은 하루에 `1축`만 연다.
2. 신규 관찰축/보완축은 shadow를 만들지 않고 canary로만 착수한다.
3. 모든 판정 행에는 최소 `N_min`, `PrimaryMetric`, rollback guard를 남긴다.
4. `canary -> live` 전환은 applied/not-applied cohort, cross-contamination 부재, restart/rollback 경로를 같이 닫는다.
5. threshold live mutation은 `ThresholdOpsTransition0506` acceptance와 별도 workorder 전까지 금지한다.
6. OFI/QI bucket runtime calibration은 기본 OFF이며, ON은 별도 workorder와 restart 기준이 닫힌 뒤에만 가능하다.
7. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.
8. `full fill`, `partial fill`, `fallback_contaminated`, `normal_only`, `post_fallback_deprecation`은 항상 별도 코호트로 본다.

## 현재 기준 문서 입력 규칙

1. 날짜별 실제 실행과 판정은 해당 `stage2 todo checklist`에 남긴다.
2. 원문 계획과 다른 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에 남긴다.
3. 장후/주간 baseline과 반복 성과값은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)에 누적한다.
4. report 생성 필요성, 정기 Markdown 현황, 누락 후보는 [data/report/README.md](../data/report/README.md)에 반영한다.
5. threshold cycle 운영방법과 금지선은 [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)에 반영한다.
6. 장문 경과, 이미 지난 공격 일정, 세부 구현 경위는 archive로 이동한다.
