# KORStockScan 문서 구조

작성 기준: 2026-06-04 KST

이 디렉터리는 Plan Rebase 이후의 운영 의사결정, 날짜별 실행 체크리스트, runbook, report traceability, 감리/리포트 증적을 관리한다. 현재 판단의 원본은 루트 기준 문서와 날짜별 checklist이고, 과거 전환 증적은 `archive/`에 보존한다.

튜닝 데이터 의사결정 기준일은 `2026-06-04 KST`다. 세부 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이며, 정책 artifact는 `data/source_quality/clean_baseline_policy.json`이다. 이 기준 이전 raw/report/analytics 데이터와 보고서는 archive-only/audit evidence이고, 현재 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval의 입력으로 쓰지 않는다.

## 먼저 볼 문서

- `plan-korStockScanPerformanceOptimization.rebase.md`: 현재 튜닝 원칙, active owner, live/observe/off 판정, rollback guard의 기준 문서.
- `plan-korStockScanPerformanceOptimization.prompt.md`: 작업 시작 프롬프트와 문서 참조 순서.
- `plan-korStockScanPerformanceOptimization.execution-delta.md`: 원 계획 대비 실행 차이와 보정 기록.
- `plan-korStockScanPerformanceOptimization.performance-report.md`: Plan Rebase 성과 판정과 반복 성과 기준.
- `time-based-operations-runbook.md`: 장전, 장중, 장후, 21:00 EOD 데이터 갱신 cron 확인 절차.
- `report-based-automation-traceability.md`: report 산출물, downstream consumer, runtime mutation 금지선, postclose chain contract.
- `../data/source_quality/clean_baseline_policy.json`: 현재 튜닝 데이터 날짜 기준과 pre-baseline forbidden-use 정책.
- `stage2-todo-checklist-template.md`: 날짜별 checklist 작성 형식.
- `checklists/YYYY-MM-DD-stage2-todo-checklist.md`: 날짜별 checklist의 표준 위치. 실제 실행 작업항목의 소유 문서이며, legacy root checklist도 이 위치로 정리한다.

작업 시작 시에는 `plan-korStockScanPerformanceOptimization.rebase.md` §1~§8과 당일 checklist의 `오늘 목적`, `오늘 강제 규칙`을 먼저 확인한다. 당일 checklist가 없으면 Plan Rebase §7~§8과 최신 실행표의 상단 요약을 같이 확인한다.

README, 런북(runbook), Plan Rebase, prompt, AGENTS 같은 기준 문서는 사용자의 명시 작업지시가 있을 때만 갱신한다. 문서 갱신은 runtime/order/provider/bot/threshold 변경과 분리하고, 필요한 경우 1차 수정, 2차 감리, 최종 보완 순서로 parser 검증까지 닫는다.

## 현재 루트 유지 기준

루트 `docs/`에는 아래 성격의 문서만 유지한다.

- Plan Rebase, prompt, execution delta, performance report처럼 반복 참조되는 기준 문서.
- 현재 checklist 또는 Plan Rebase가 직접 참조하는 workorder, 운영 runbook, report traceability 문서.

과거 판단 근거이지만 현재 작업항목을 직접 소유하지 않는 문서는 성격별 하위 디렉터리 또는 `archive/`로 이동한다. 이동 시 기존 링크는 새 위치로 보정하고 parser 검증을 수행한다.

## 날짜별 Checklist

- `checklists/YYYY-MM-DD-stage2-todo-checklist.md`: `build_next_stage2_checklist.py`가 생성하는 신규 checklist 위치.
- `2026-04-20-stage2-todo-checklist.md`부터 `2026-05-15-stage2-todo-checklist.md`까지의 legacy root checklist는 `checklists/`로 이동 완료했다. 루트 `docs/`에는 날짜별 stage2 checklist를 새로 두지 않는다.
- 완료된 checklist의 `[x]` 항목은 증적이며 현재 OPEN owner로 보지 않는다. 현재 owner는 Plan Rebase와 최신 checklist에서 확인한다.

## 하위 디렉터리

- `ai-acceptance/`: Gemini, DeepSeek, OpenAI flag-off acceptance spec, parity review, bundle result.
- `audit-reports/`: Plan Rebase, OFI/QI, hotfix, 운영 감리 보고서.
- `code-improvement-workorders/`: 코드 개선 전용 workorder.
- `code-reviews/`: 스나이퍼 엔진 코드리뷰, 성능 감사, holding flow override 리뷰.
- `checklists/`: 신규 날짜별 checklist와 이동 완료된 legacy checklist.
- `proposals/`: 스캐너 개선, preclose sell target 등 운영 제안서.
- `personal/`: 개인 보조 메모. 실행 판정의 `Source`로 쓰지 않는다.
- `reference/`: API 문서, AI coding instruction 등 일반 참조 문서.

## 운영/Traceability 문서

- `time-based-operations-runbook.md`: 시간대별 cron, 산출물, 확인 절차, 운영 금지선. `16:10` postclose chain, `21:00` update_kospi 데이터 갱신 확인 절차를 포함한다.
- `report-based-automation-traceability.md`: 산출물별 producer/consumer/owner, postclose direct predecessor contract, workorder lineage, source-quality automation input 기준.
- `../data/report/README.md`: 정기 생성 Markdown report, 입력 JSON/JSONL, 누락 report 후보의 기준.
- `../data/threshold_cycle/README.md`: threshold cycle 산출물, manifest/report 운영 방법, live mutation 제한 기준.
- report 또는 threshold 산출물 변경이 작업계획에 영향을 주면 Plan Rebase와 날짜별 checklist를 함께 현행화한다.

## 루트 예외 문서

루트에 남은 `workorder-*.md`, `deepseek-*.md` 중 일부는 완료된 과거 문서지만 현재 checklist, Plan Rebase, acceptance spec에서 절대경로로 직접 참조한다. 링크 안정성과 parser 입력 보존을 위해 아래 조건 중 하나에 해당하면 이동하지 않는다.

- Plan Rebase 또는 `2026-05-13-stage2-todo-checklist.md`가 직접 참조한다.
- 과거 checklist의 `Source`로 남아 감사 추적성이 필요한 문서다.
- acceptance spec, audit report, build report가 루트 경로를 전제로 참조한다.
- 이동하려면 참조 링크 보정과 parser 검증을 같은 변경 세트에서 수행해야 한다.

## 감사/감리 문서

- `audit-reports/`: OFI/QI, Plan Rebase, 운영 감리 대응처럼 현재 또는 최근 감리 결과를 보존한다.
- `audit-reports/2026-05-03-order-flow-imbalance-application-audit-report.md`는 OFI/QI 적용 현황의 기존 증적이다.
- 감리 지적이 실행 작업으로 전환되면 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 남긴다.

## Workorder/Review 문서

- `workorder-*.md`: 현재 또는 최근 checklist가 직접 참조하는 작업 지시, 실행 로그, 결과 문서.
- `code-reviews/`: 현재 개선축에서 참조되는 코드리뷰/성능 감사 증적.
- `proposals/`: 현재 개선축에서 참조되는 운영 제안 증적.
- 완료되어 후속 checklist와 Plan Rebase에서 직접 참조하지 않고 루트 예외 조건에도 해당하지 않는 workorder는 `archive/legacy-workorders/`로 이동한다.

## Archive

- `archive/legacy-tuning-2026-04-06-to-2026-04-20/`: Plan Rebase 이전 튜닝, 감사, remote 비교, 실험 문서.
- `archive/plan-rebase-transition-2026-04-20-to-2026-04-22/`: Plan Rebase 전환기의 감사/운영자 응답/거버넌스 증적.
- `archive/legacy-workorders/`: 완료 또는 대체된 과거 workorder.
- `archive/reference-and-runbooks/`: 과거 runbook, setup, API note, 일반 참조 문서.
- `archive/archive-manifest-2026-04-21.md`, `archive/archive-manifest-2026-05-03.md`: 이동 이력.

아카이브 문서는 감사 추적용이다. 현재 의사결정에는 루트 기준 문서와 최신 checklist를 우선한다.

## 개인 문서

- `personal/personal-decision-flow-notes.md`
- `personal/personal-gemini-ai-prompt-usage-guide.md`

개인 문서는 보조 메모로만 유지한다. checklist, report, Plan Rebase의 `Source` 또는 판정 근거 링크로 사용하지 않는다.

## 문서 변경 후 검증

문서 구조, checklist, Plan Rebase, prompt를 변경하면 parser 검증을 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

Project/Calendar 동기화가 필요한 경우 사용자가 아래 표준 명령을 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
