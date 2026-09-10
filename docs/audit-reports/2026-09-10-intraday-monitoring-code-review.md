# 2026-09-10 장중 모니터링 수정 코드 재검토

기준: 2026-09-10 09:39:49 KST. 요청은 장중 수정의 review→fix→re-review이며, 09:30 종료한 지속 모니터링을 연장하지 않는다. `korstockscan-review-gate`를 적용했다.

검토 범위는 [09:30 모니터링](./2026-09-10-intraday-monitoring-0930.md)에서 변경한 `market_opportunity_census.py`, `intraday_ws_freshness_monitor.py`와 각각의 테스트, 직접 연결된 review/receive-expectation consumer 및 기존 wrapper다. 병행 중인 Entry AI·adaptive exit 등의 변경은 이번 finding 0 범위에 포함하지 않는다.

## 판정과 수리

추가 결함 2개를 테스트로 재현한 뒤 수정했고, 재검토 범위의 미해결 finding은 0개다.

| Finding | 재현 및 영향 | 보완 및 수용 확인 |
| --- | --- | --- |
| WS snapshot 획득 중 기준시각 역전 | event scan 전에 읽더라도 시작 시각 09:05:03.999와 실제 읽기 09:05:04.001 사이 갱신된 snapshot09:05:04를 future로 제외해 진단 모집단이 0행이 됨 | 기본 실행은 snapshot을 읽은 뒤 평가시각을 확정. `report_started_at`과 provenance `evaluated_at`을 분리하며, 명시적 as-of는 고정. 경계 테스트에서 1행/age0.001초, 실제 future·stale·cross-date 제외 및 historical 계약 유지 |
| NXT capture와 BBO 관측시각의 휴지 경계 불일치 | ranking08:49:59가 유효해도 BBO08:50:00이 경제성/freshness 원천으로 들어감. prune 및 promoted WS 원천에도 동일 우회 경로 존재 | 검증된 external/prune/promoted WS BBO 전체에 실제 `observed_at` 기준 NXT-only08:50≤t<09:00:30 제외 적용. KRX09:00 및 NXT09:00:30 유지. raw bytes·실제 REST reservation 보존, `nxt_scheduled_pause_bbo_excluded` 사유 기록 |

첫 반례 실행의 2개 실패는 `tmp/intraday-monitor-review-20260910/reproduction.log`, 수정 후 결과는 같은 디렉터리의 `validation.log`에 보존했다. NXT 테스트는 실제 외부 BBO 계약 및 prune/promoted WS parser를 거쳐 report consumer까지 검증한다. 제외 행을 정상·0 EV로 바꾸지 않고, request budget 보존식과 raw 불변을 함께 검사했다.

## 검증과 목적 부합성

- 관련 pytest 4개 모듈 190개 PASS: WS freshness, market census, market opportunity review, WS receive expectation.
- 기존 source-only wrapper/설치 계약과 cooldown/CPU 계약 테스트 2개 PASS. 합계 192개 PASS.
- 변경 Python 4개 compile/Black `--check --no-cache`, wrapper 2개 `bash -n`, `git diff --check` PASS.
- 코드·직접 consumer 재검토에서 silent-empty, 시간 경계, venue 격리, 원본/예산 보존, 권한 누출을 확인했다. 주문·provider·수량·threshold·bot state와 protocol request/parser는 수정하지 않았다.

기대효과는 유효한 현재 WS 진단이 시각 경쟁으로 사라지는 오류와 NXT 휴지 원천이 실행 가능 기회로 집계되는 오류의 제거다. 이는 비용 차감 후 작은 수익기회를 평가할 입력의 정확도를 높이는 수리다. BUY 증가나 실현 순이익 개선은 이번 테스트로 입증하지 않았으며, 진단 수리 완료에 양수 EV·실체결 floor를 추가하지 않는다.

## 자동 소비와 남은 확인

설치 cron과 실제 wrapper를 읽어 연결을 확인했다. WS는 5분 trigger/성공 후720초 cooldown, census는 5분 capture와09:15·12:00·15:15·19:45 report refresh다. 각 report는 새 Python process에서 수정 코드를 읽으므로 메인 봇 재기동은 필요하지 않다. 조기/중복 report 생성은 실행하지 않았다.

09:39:49 읽기 전용 확인:

- WS09:35:03 report는 `before_event_scan`, snapshot09:35:01/age2.465917초/selected·current_freshness_usable=true로 기존 모니터링 수리의 자연 소비를 확인했다. SHA256 `3eab9404924cef5b5a0abe2424c73f0e49d4dbb4957034b6946d7ccb2efe97f6`. 이번 추가 `evaluated_at`/`report_started_at`은 아직 없으므로 보완 반영은 별도 대기다.
- Census 최신 report는09:15:37, SHA256 `fa3209d140b7b8dcf4737359e6cfc0b433548fe06f56e31ea3d66334fb72731b`. 이번 관측시각 보완 후 report 자연 소비는 아직 확인되지 않았다.

receipt 원문 요약은 `tmp/intraday-monitor-review-20260910/natural-generation-receipts.json`에 보존한다. 기존 [RuntimeEnvIntradayObserve0910](../checklists/2026-09-10-stage2-todo-checklist.md)의 OPEN을 재사용한다. 다음 WS 예상09:50에는 acquisition provenance/현재 snapshot 판정을, census12:00에는 generation과 pause BBO 제외/예산 보존을 확인한다. 예약은 성공 receipt가 아니며 이 문서에서 미래 실행·경제성 완료를 주장하지 않는다.

문서 검증: 링크·현재 OPEN12/unique12·print-only parser PASS. 파서의 당일 RuntimeEnv owner 포함을 확인했다. 외부 동기화가 필요할 때 사용자가 실행하는 표준 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
