# KORStockScan 성능 최적화 Q&A

이 문서는 `계획서 원문(prompt)`에 남기기에는 길지만 반복적으로 참조해야 하는 운영 판단 기준을 모아둔 문서다.

## 이 문서를 읽을 때의 전제

1. 최종 목적은 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 현재 단계는 `리포트 정합성 유지 + split-entry leakage 제거 + HOLDING/청산 판단 분리`다.
3. `한 번에 한 축 canary`, `shadow-only`, `즉시 롤백 가드`는 보수적 철학이 아니라 `원인 귀속 정확도`와 `실전 리스크 관리`를 위한 운영 규율이다.
4. `prompt`는 현재 실행 기준, `execution-delta`는 기본계획 대비 변경사항, `performance-report`는 정기 성과측정 baseline, `archive`는 과거 경과 보관용이다.

## 운영/문서 Q&A

### Q1. Reason code 집계 자동화는 이미 있나, 아니면 새로 만들어야 하나?

답변:

1. 현재 시점의 blocker 분포를 보는 자동화는 이미 있다.
2. `일자별 추세 비교`, `reason code 상위 변화 알림`, `sig_delta 상위 필드 랭킹`은 아직 부족하다.
3. 따라서 새로 만들 대상은 완전 신규 대시보드보다 기존 `performance-tuning` 확장이다.

운영 기준:

1. 1차는 기존 `성능 튜닝 모니터`의 blocker 집계를 일자/기간 기준으로 확장한다.
2. 2차는 `sig_delta` 상위 필드와 경고 알림을 붙인다.

### Q2. Gatekeeper 캐시 TTL은 먼저 키워야 하나, 아니면 동적 TTL로 바로 가야 하나?

답변:

1. 현재 병목은 TTL 부족보다 `저장 lifecycle`과 `sig_changed` 우회가 더 크다.
2. 따라서 단순 TTL 확대를 1단계 해법으로 두지 않는다.
3. 동적 TTL도 `원인 분해 -> 국소 정책화` 이후에 본다.

채택안:

1. 현행 TTL을 먼저 유지한다.
2. `missing_action`, `missing_allow_flag`, `sig_changed`의 실제 발생 원인을 추적한다.
3. 그 다음 전략/장세 기준 동적 TTL을 검토한다.

### Q3. `missing_action`, `missing_allow_flag`, `sig_changed`는 로그만 더 모을까, 저장 경로를 바로 고칠까?

답변:

1. 1단계는 `로그/추적 강화`를 먼저 한다.
2. 저장 로직이 완전히 없는지보다 `언제 비어 있고 언제 초기화되는지`가 핵심이다.
3. `reason_codes`는 안정적으로 유지하고, 상세 변화는 `sig_delta` 같은 별도 필드로 남긴다.

채택안:

1. `gatekeeper_fast_reuse_bypass` 같은 기존 stage에 상세 필드를 붙인다.
2. lifecycle 원인이 확인되면 그 다음 단계에서 저장 경로 수정으로 간다.

### Q4. 모니터링 기간은 모두 1주일로 잡아야 하나?

답변:

1. 아니다. `보유 AI 공통 정책`과 `스캘핑 국소 튜닝`은 관찰 기간을 다르게 본다.
2. `보유 AI 공통 정책`은 기본 `5거래일~1주일`이 맞다.
3. `스캘핑 국소 canary`는 `당일 30~60분 + 장후 평가 + 필요 시 1~2세션`이 기본이다.

운영 기준:

1. 공통 정책 변경은 최소 `5거래일`을 본다.
2. 국소 canary는 `한 번에 한 축`이고 집계 축이 분리돼 있으면 더 짧게 판정한다.
3. 목적은 보수적 대기가 아니라 `기대값 개선 속도`를 높이는 것이다.

### Q5. counterfactual(`missed_entry`, `extra_upside`) 수치는 손익과 합산해도 되나?

답변:

1. 안 된다.
2. counterfactual은 직접 실현손익이 아니라 `우선순위 판단용 진단 가치`다.
3. 실현손익 판단은 항상 `COMPLETED + valid profit_rate`만 쓴다.

해석 기준:

1. `missed_entry counterfactual`은 진입 차단 기회비용 크기를 보여준다.
2. `post_sell extra_upside`는 HOLDING/청산 품질 개선 여지를 보여준다.
3. 둘 다 `어느 축을 먼저 건드릴지` 결정할 때만 사용하고, 실현손익과 섞지 않는다.

### Q6. 기본계획과 실제 실행이 달라지면 어디에 기록하나?

답변:

1. 먼저 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에 남긴다.
2. 그 다음 현재 기준만 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)에 반영한다.
3. 세부 경과와 지나간 일정은 archive로 보낸다.

기록 원칙:

1. `무엇이 달라졌는가`
2. `왜 달라졌는가`
3. `현재 기준은 무엇인가`
4. `다음 판정 시점은 언제인가`

### Q7. `prompt`, `checklist`, `execution-delta`, `performance-report`, `archive`는 각각 언제 업데이트하나?

답변:

1. `prompt`: 현재 기준 우선순위나 주간 실행 맵이 바뀔 때
2. `checklist`: 당일 실행/보류/다음 시각이 생길 때
3. `execution-delta`: 기본계획 대비 실행이 달라졌을 때
4. `performance-report`: 장후/주간 성과 baseline과 반복 측정값이 갱신될 때
5. `archive`: 지나간 일정, 장문 경과, 상세 구현 이력을 옮길 때

판단 기준:

1. 지금 당장 실행에 필요한 정보면 `prompt` 또는 `checklist`
2. 원안 대비 변경이면 `execution-delta`
3. 반복 성과값이면 `performance-report`
4. 과거 맥락이면 `archive`

### Q8. 정기 성과측정보고서는 어떤 순서와 지표로 써야 하나?

답변:

1. 순서는 항상 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다.
2. `손익`은 마지막 결과값으로만 본다.
3. HOLDING 판단은 `missed_upside_rate`, `capture_efficiency`, `GOOD_EXIT`를 함께 본다.

기본 집계 기준:

1. `거래수`: `total_trades`, `completed_trades`
2. `퍼널`: `AI BUY -> entry_armed -> budget_pass -> submitted -> filled`
3. `blocker`: `latency/liquidity/AI threshold/overbought`
4. `체결품질`: `full_fill`, `partial_fill`, `rebase`, `same_symbol_repeat`
5. `HOLDING/청산`: `MISSED_UPSIDE`, `GOOD_EXIT`, `capture_efficiency`
6. `손익`: `COMPLETED + valid profit_rate` 기준 실현값

### Q9. broad relax(`latency/tag/threshold`)는 언제 다시 열 수 있나?

답변:

1. `split-entry leakage` 1차 판정이 먼저다.
2. HOLDING D+2 판정이 아직 안 닫혔으면 broad relax를 다시 넓히지 않는다.
3. 거래수 확대보다 손실축 제거가 앞선다.

현재 기준:

1. bugfix-only latency 재판정은 가능하다.
2. broad relax 재오픈은 `split-entry leakage` 판정 이후에만 검토한다.

### Q10. Project/Calendar 자동화가 막히면 어떻게 처리하나?

답변:

1. 우회 수동처리보다 먼저 `env`, `권한`, `필드명`, `옵션명`을 점검한다.
2. 문서는 먼저 수정하되, 같은 턴에 `sync_docs_backlog_to_project -> sync_github_project_calendar`를 시도한다.
3. 막히면 막힌 env와 재실행 명령 `1개`만 남긴다.

기록 기준:

1. 무엇이 막혔는지
2. 어떤 문서가 수정됐는지
3. 사용자가 실행할 명령 `1개`

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [plan-korStockScanPerformanceOptimization.archive-2026-04-19.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-19.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
