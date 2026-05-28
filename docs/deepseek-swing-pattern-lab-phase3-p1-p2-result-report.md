# DeepSeek Swing Pattern Lab Phase3 P1/P2 Result Report

- 작성일: 2026-05-09 KST
- 기준 작업지시서: [workorder-deepseek-swing-pattern-lab-phase3-remaining.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder-deepseek-swing-pattern-lab-phase3-remaining.md)
- 완료 범위: P1 관찰축/DB 적재 gap 보강, P2 AI contract 및 AVG_DOWN/PYRAMID report-only family 보강
- 미완료 범위: P3 fresh single-day DeepSeek re-entry 조건 확인

## 완료 판정

P1/P2는 완료로 판정한다. 스윙 live 주문, Gatekeeper, market regime hard block, gap/protection guard, 예산/주문 safety, model floor, threshold runtime 값은 변경하지 않았다. 신규 필드는 모두 report-only/proposal-only provenance이며 `runtime_change=false` 원칙을 유지한다.

생성되는 모든 `swing_improvement_automation` workorder item은 `runtime_effect=false`, `allowed_runtime_apply=false`를 명시한다. 신규 family candidate 역시 `runtime_change=false`, `allowed_runtime_apply=false`를 유지하며, 실제 live 반영은 사용자가 별도 workorder를 수동으로 Codex에 넣을 때만 가능하다.

P3는 지금 완료 판정하지 않는다. fresh single-day DeepSeek re-entry는 해당 영업일의 fresh 산출물과 `run_manifest.json`의 `analysis_window.start == target_date == end` 증적이 필요하므로 [2026-05-11-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-11-stage2-todo-checklist.md)에 미완료 항목으로 유지했다.

## 구현 요약

- [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py)
  - `recommendation_db_load` 섹션을 추가해 추천 CSV row와 DB row divergence를 `db_load_gap`, `db_load_skip_reason`, `db_load_error`, `selection_modes`로 분리했다.
  - `scale_in_observation`을 추가해 `AVG_DOWN/PYRAMID/NONE`, add trigger, price policy, add ratio, post-add outcome, guard blocker, zero-sample reason을 집계한다.
  - `ai_contract_metrics`를 추가해 schema valid rate, parse fail, disagreement, `latency_ms`, cost, prompt/model 분포를 report-only로 남긴다. 작업지시서의 `model_call_ms_p95` acceptance는 구현상 `ai_contract_metrics.latency_ms.p95`로 확인한다.
  - `swing_improvement_automation`의 DB gap evidence, EV summary, scale-in sample-gap evidence에 위 provenance를 연결했다.

- [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py)
  - selection funnel에도 `recommendation_db_load`를 추가해 `swing_lifecycle_audit`와 동일한 DB 적재 gap 사유를 확인할 수 있게 했다.

- [2026-05-11-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-11-stage2-todo-checklist.md)
  - P1/P2는 완료 처리하고 검증 명령을 기록했다.
  - P3는 fresh single-day 산출물 필요 항목으로 유지했다.

## 검증 결과

- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py` -> 15 passed
- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_code_improvement_workorder.py src/tests/test_threshold_cycle_ev_report.py` -> 7 passed
- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py` -> 30 passed
- `PYTHONPATH=. .venv/bin/python -m compileall -q src/engine` -> passed
- `git diff --check` -> passed

## 리뷰 포인트

- DB gap reason은 `loaded`, `no_recommendation_csv_rows`, `db_load_error`, `diagnostic_only_recommendation_rows`, `csv_rows_positive_db_rows_zero` 중 하나로 남는다.
- DB load gap 판정 로직은 현재 [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py)와 [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py)에 중복돼 있다. 두 리포트 소비자가 분리돼 있어 현 단계에서는 허용하지만, 차기 리팩터링에서는 공용 helper로 묶는 것이 좋다.
- scale-in zero sample은 live 로직 변경 근거가 아니라 관찰 부족 사유다. fresh 표본 없이 `AVG_DOWN/PYRAMID` 주문 여부, 수량, 가격을 바꾸지 않는다.
- AI contract metric은 현재 이벤트에 값이 있을 때만 집계된다. latency acceptance는 `model_call_ms_p95`라는 별도 top-level key가 아니라 `latency_ms.p95`로 남긴다. 실제 prompt 교체, 모델 tier 변경, OpenAI/Gemini/DeepSeek live routing 변경은 별도 workorder가 필요하다.
- 모든 automation order와 신규 family candidate는 `runtime_effect=false`, `allowed_runtime_apply=false` 확인 대상이다.

## 다음 액션

- P3는 2026-05-11 postclose에 fresh single-day DeepSeek 산출물이 생긴 뒤 `run_manifest.json`과 필수 JSON schema 유효성을 확인한다.
- Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
