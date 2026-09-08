# KORStockScan 성능 최적화 Q&A

기준일: `2026-09-08 KST`

이 문서는 Plan Rebase 본문에 길게 두기에는 크지만 반복적으로 참조해야 하는 운영 판단 기준을 모아둔 문서다. 현재 역할은 과거 latency/composite 세부 판단 FAQ가 아니라, 자동화체인에서 `승률/EV`, `daily/rolling`, `real/sim/probe`, `proposal/apply`를 혼동해 오판하지 않도록 막는 반복 Q&A다.

튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 이 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보존하며 현재 EV, rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 사용하지 않는다.

2026-05-13 자동화체인 리뉴얼 전 원문은 [qna pre-automation-renewal archive](./archive/plan-korStockScanPerformanceOptimization.qna.pre-automation-renewal-2026-05-13.md)에 보존했다.

## 이 문서를 읽을 때의 전제

1. 최종 목적은 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 중심 기준은 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md)다. Q&A는 반복 판단 해설이며 active/open owner의 source of truth가 아니다.
3. 자동화체인 산출물/consumer/apply 계약은 [report-based-automation-traceability](./report-based-automation-traceability.md)가 소유한다.
4. 실행 작업항목은 날짜별 `stage2 todo checklist`가 소유한다. 완료된 `[x]` 항목은 현재 OPEN owner가 아니라 증적이다.
5. 정기 자동화의 장중 runtime threshold mutation은 금지하며 장후 report와 다음 PREOPEN을 따른다. 별도 명시적 장중 override는 Plan Rebase의 단일 기존 축·cohort·증거·rollback·runtime mutation guard가 소유한다. Q&A나 문서 갱신이 그 권한을 부여하지 않는다.
6. clean tuning data baseline 이전 산출물은 현재 의사결정 입력이 아니라 archive-only 증적이다.
7. 새 관찰지표는 `Metric Decision Contract`를 가져야 한다. 계약이 없으면 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.

## 운영/문서 Q&A

### Q1. Q&A 문서는 아직 유효한가?

답변:

1. 유효하다. 단, 역할은 `과거 latency 실험 FAQ`가 아니라 `자동화체인 오판 방지 FAQ`다.
2. 현재 원칙과 active/open 상태는 Plan Rebase가 소유한다.
3. Q&A는 반복 질의가 생기는 판정축의 해석 기준만 남긴다.

운영 기준:

1. 현재 owner 상태를 Q&A에 복제하지 않는다.
2. 지나간 실험 수치와 장문 경과는 archive 또는 execution-delta에서 본다.
3. Q&A가 Plan Rebase와 충돌하면 Plan Rebase가 우선한다.

### Q2. 승률과 EV 중 무엇으로 판정해야 하나?

답변:

1. 기대값/순이익 판정은 `primary_ev`가 맡는다.
2. `win_rate`는 `diagnostic_win_rate`다.
3. 승률이 높아도 평균 손익, downside tail, 체결품질이 나쁘면 live/canary 승인 근거가 아니다.

운영 기준:

1. EV 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 명명한다.
2. 단순 손익 합산은 EV가 아니며 `simple_sum_profit_pct`로 표시한다.
3. `diagnostic_win_rate` 단독으로 threshold apply, canary 승격, 실주문 전환을 승인하지 않는다.

### Q3. daily-only 지표와 rolling/cumulative 지표는 어떻게 나누나?

답변:

1. `daily_only`는 incident, safety veto, freshness/source-quality, 장중 운영 trigger에 쓴다.
2. edge apply 승인은 rolling/cumulative 또는 `post_apply_version_window`와 함께 본다.
3. 단일 당일 수치만으로 threshold 완화/강화, live/canary 승격, 실주문 전환을 확정하지 않는다.

운영 기준:

1. safety breach는 daily-only여도 차단/rollback 후보가 될 수 있다.
2. 기대값 개선은 family별 `window_policy`와 sample floor를 따른다.
3. daily/rolling/cumulative 방향이 다른 경우 `hold_sample`, `hold_no_edge`, `freeze`, `instrumentation_gap` 중 하나로 닫는다.

### Q4. sim/probe/counterfactual 결과는 어디까지 쓸 수 있나?

답변:

1. source bundle, approval request, workorder evidence에는 쓸 수 있다.
2. real execution 품질이나 broker order enable 근거로 단독 사용하지 않는다.
3. `actual_order_submitted=false` 표본은 실주문 표본과 분리한다.

운영 기준:

1. `sim_equal_weight`, `probe_observe_only`, `counterfactual_only`, `combined_diagnostic` authority를 JSON/Markdown에 드러낸다.
2. combined 진단은 튜닝 후보 산출에만 쓰고, 주문 실패율/receipt/fill 품질은 real-only로 본다.
3. counterfactual은 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.

### Q5. `runtime_approval_summary`는 무엇을 승인하나?

답변:

1. 아무 것도 직접 승인하지 않는다.
2. `runtime_approval_summary`는 read-only 요약 artifact다.
3. 스캘핑 selected family, 스윙 approval request, panic approval 후보를 한 화면에 모아 보여준다.

운영 기준:

1. `runtime_mutation_allowed=false`면 flow 조정, 주문 차단, threshold mutation 권한이 없다.
2. summary에 `approval_required`가 있으면 final-stage user approval 후보로 본다. Pre-final 후보는 `sim_auto_approved`, `dry_run_auto_apply_ready`, `live_auto_apply_ready`, or `auto_approved_real_canary`처럼 별도 auto state를 가져야 한다.
3. 다음 장전 적용 여부는 preopen apply manifest와 parsed AI Tier2/deterministic guard 또는 final user approval artifact가 닫힌 뒤에만 본다.

### Q6. 새 관찰지표가 생기면 무엇을 같이 정해야 하나?

답변:

1. 지표값만 만들면 안 된다.
2. 자동화체인이 소비하는 새 관찰지표는 생성 시점에 판정 계약을 가져야 한다.
3. 계약이 없으면 threshold candidate가 아니라 instrumentation/source-quality backlog다.

필수 항목:

1. `metric_role`
2. `metric_definition`
3. `decision_authority`
4. `window_policy`
5. `sample_floor`
6. `primary_decision_metric`
7. `secondary_diagnostics`
8. `source_quality_gate`
9. `runtime_effect`
10. `forbidden_uses`

### Q7. Sentinel, panic, error detector 이상치는 자동 튜닝 명령인가?

답변:

1. 아니다.
2. 이들은 report-only/source-quality/incident 입력이다.
3. 반복 이상치가 있어도 먼저 `incident/playbook`, `threshold-family 후보`, `instrumentation_gap`, `normal drift`로 라우팅한다.

운영 기준:

1. Sentinel 결과로 score/spread/fallback/restart를 자동 변경하지 않는다.
2. panic 결과로 stop/TP/trailing/자동매도/자동매수/provider route를 자동 변경하지 않는다.
3. System Error Detector 결과로 전략 threshold/order guard를 자동 변경하지 않는다.

### Q8. 스윙 approval request가 있으면 다음 장전 env에 반영하나?

아니다. 현재 Swing은 operator OFF다. 과거 approval/phase0 artifact가 활성화 지시가 아니며 OFF 산출물 부재를 복구·승격 작업으로 만들지 않는다. 향후 별도 재개 지시가 있더라도 현행 owner/guard/승인을 확인해야 한다. 예전 hard floor나 parsed review만으로 실주문·cap/provider/bot 권한을 복원하지 않는다.

### Q9. code-improvement workorder가 생성되면 자동으로 repo를 수정하나?

답변:

1. 아니다.
2. workorder는 Codex 구현 세션 입력용 작업지시다.
3. 명시적 구현 요청 또는 장후 모니터링 지시문의 명시적 실행 호출이 있어야 허용 범위 구현으로 넘어간다. 후자는 source-only 복구·추천 2-pass를 포함하지만 live/lock/env/order/provider/bot 권한을 추가하지 않는다. 문서 열람·인용·현행화는 실행 호출이 아니다.

운영 기준:

1. `runtime_effect=false`, `allowed_runtime_apply=false` order는 실운영 변경으로 해석하지 않는다.
2. workorder 생성은 evidence 정리이지 code mutation이 아니다.
3. 구현 후 review→수정→재리뷰→targeted validation을 닫고 허용된 영향 producer/consumer만 재생성한다. 문서-only 작업은 링크·owner·권한·파서 검증으로 닫는다. 미래 자연/EV 확인은 기존 checklist owner를 재사용한다.

### Q10. Project/Calendar 동기화는 누가 실행하나?

답변:

1. AI가 직접 GitHub Project/Calendar 동기화를 실행하지 않는다.
2. 문서/checklist 변경 후 parser 검증은 AI가 실행한다.
3. 실제 Project/Calendar 동기화는 사용자가 표준 명령으로 수동 실행한다.

표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

### Q11. legacy latency/composite Q&A는 어디서 보나?

답변:

1. 현재 Q&A 본문에서는 제거한다.
2. 과거 latency composite, offline bundle, split-entry leakage 같은 판단은 historical/reference다.
3. 필요하면 2026-05-13 이전 Q&A archive와 closed observation archive에서 본다.

운영 기준:

1. legacy 기준을 현재 auto-bounded apply 판정에 직접 섞지 않는다.
2. legacy 축을 재개하려면 새 workorder, 새 rollback guard, 새 checklist가 필요하다.
3. 현재 자동화체인에서는 family별 `Metric Decision Contract`, source-quality gate, window policy를 우선한다.

### Q12. 코드와 verifier가 PASS면 수익개선도 완료인가?

아니다. 코드 검토, 배포, 자연 산출물, 정책 선택, PID 소비, 비용 차감 EV는 별도다. 누락된 과거 체결·손익 귀속의 복원은 데이터 정확성 개선이지 새로운 순이익 증가가 아니다. headline PnL의 대상 집합이 미대사이면 null과 사유를 남긴다. 건수만 맞는다고 비용까지 검증된 것은 아니다.

### Q13. 장후 DONE 이후 요약이 바뀌거나 자정이 지나면?

tower→마지막 checklist→strict verifier `--require-summary-handoff`의 같은 source date/hash를 확인한다. 과거 PASS 파일로 새 verifier 명령 실패를 숨기지 않는다. 자정 이후에도 원 target date를 유지한다. 영향받지 않은 cleanup/detector는 predecessor 읽기 검증 뒤 기존 receipt 시각을 별도 공개할 수 있으나, 현재 날짜 detector 실행을 전일 성공으로 바꾸거나 실제 영향받은 필수 검사를 생략하지 않는다.

### Q14. 결과가 0이면 계속 재실행해야 하나?

정상 빈 후보, 아직 성숙하지 않은 표본, 복구 가능한 계약 오류, 비가역적인 과거 source loss, 유효 표본의 음수 EV를 먼저 구분한다. 검증된 과거 입력 유실은 재실행으로 복원되지 않는다. 원천을 합성하거나 floor를 낮추지 않고 다음 exact-date 수집을 기존 OPEN owner에서 확인한다. source-only/metadata terminal과 provider 평가·runtime 승격은 별도다.

### Q15. 원본 ledger는 ID 없음인데 후속 구현은 완료일 수 있나?

가능하다. 원본 canonical bytes를 고정한 뒤 producer가 native ID metadata projection을 만들고 별도 사용자 승인을 받아 구현했다면 원본 path/row/hash→native ID→승인/구현 ledger를 대사한다. 원본 결손 이력은 보존하되 현재 disposition은 검증된 후속 근거로 판단한다. 두 ledger를 고유 작업으로 합산하지 않으며 projection을 새 경제성 산출물로 보지 않는다. 새 ID 자체는 구현/live 권한이 아니다.

## 참고 문서

- [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)
- [report-based-automation-traceability.md](./report-based-automation-traceability.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [qna pre-automation-renewal archive](./archive/plan-korStockScanPerformanceOptimization.qna.pre-automation-renewal-2026-05-13.md)
- [closed observation archive](./archive/closed-observation-axes-2026-05-01.md)
