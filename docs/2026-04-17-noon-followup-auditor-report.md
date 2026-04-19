# 2026-04-17 Noon Snapshot 후속 점검 감리 보고서

작성일: 2026-04-17  
대상: `2026-04-17-stage2-todo-checklist.md` 기준 noon 후속 4개 항목  
범위: 로컬 `data/pipeline_events/pipeline_events_2026-04-17.jsonl`, `data/report/monitor_snapshots/*_2026-04-17.json`, 원격 `tmp/remote_2026-04-17/*`

---

## 1. 판정

1. `latency canary bugfix-only 장중 실표본 재판정`은 **지금 재오픈 가능했고 실제로 재판정 완료**했다.
   - 결론: bugfix-only는 `0건` 상태를 벗어났으나, 추가 완화(`tag/min_score`)는 아직 **미승인**이 맞다.
   - 보강 메모: 로컬 `canary_applied=19`, 원격 `3`의 격차는 실표본 분포 차이 또는 noon 이전 반영 시차 가능성이 있어, `2026-04-20 PREOPEN`에 원격 퍼널 timeout 해소 여부와 함께 재확인한다.
2. `split-entry rebase quantity 감사 기준 확정`은 **지금 확정 가능했고 shadow 수집 코드까지 반영**했다.
   - 결론: 메인 `2026-04-17` 분할진입 soft stop 16건 중 10건에서 정합성 플래그가 관찰돼, 이후 손절축 판단 전에 이 감사가 우선이다.
3. `split-entry 즉시 재평가 shadow 설계 확정`은 **지금 확정 가능했고 candidate shadow stage를 실전 코드에 반영**했다.
   - 결론: 전역 손절 강화보다 `partial 이후 확대 직후 재평가` shadow를 먼저 쌓는 것이 맞다.
4. `same-symbol cooldown`은 **초안만 당김**이 맞고, **최종 판정은 오늘 장후 유지**가 맞다.
   - 결론: 메인 `빛과전자 2회`, 원격 `코미팜 2회` 반복이 확인돼 초안의 유효성은 올라갔지만, 장후 추가 표본까지 보고 최종 시간을 확정한다.

---

## 2. 근거

### 2-1. 12:00 스냅샷 생성 확인

- 로컬 `trade_review_2026-04-17.json`: `saved_snapshot_at=2026-04-17 12:00:09`
- 로컬 `performance_tuning_2026-04-17.json`: `saved_snapshot_at=2026-04-17 12:00:27`
- 원격 fetch 스냅샷:
  - `tmp/remote_2026-04-17/trade_review_2026-04-17.json`: `saved_snapshot_at=2026-04-17 12:00:05`
  - `tmp/remote_2026-04-17/performance_tuning_2026-04-17.json`: `saved_snapshot_at=2026-04-17 12:00:22`

### 2-1-b. 원격 API timeout 및 우회 경로

- `server_comparison_2026-04-17.md` 기준 원격 `Performance Tuning`, `Entry Pipeline Flow`는 모두 `TimeoutError` 상태다.
- noon 판정에서는 원격 퍼널 API를 직접 신뢰하지 않고, 아래 우회 경로로 원격 표본을 복원했다.
  - `PYTHONPATH=. .venv/bin/python -m src.engine.fetch_remote_scalping_logs --date 2026-04-17 --include-snapshots-if-exist --snapshot-only-on-live-failure`
  - 확보 경로: `tmp/remote_2026-04-17/trade_review_2026-04-17.json`, `tmp/remote_2026-04-17/performance_tuning_2026-04-17.json`
- 따라서 오늘 noon 보고서의 원격 split-entry/latency 판정은 `remote live API`가 아니라 `원격 로그/스냅샷 fetch fallback` 기준이다.
- 후속 액션: timeout 원인 자체는 `2026-04-20 PREOPEN` 후속항목으로 분리한다.

### 2-2. latency canary 재판정

로컬:

- `latency_block=4215`
- `latency_pass=48`
- `latency_canary_applied=19`
- `latency_canary_reason.low_signal=2271`
- `latency_canary_reason.tag_not_allowed=1158`
- `latency_canary_reason.quote_stale=769`
- `latency_block_quote_not_stale=3446`

원격:

- `latency_block=4735`
- `latency_pass=31`
- `latency_canary_applied=3`
- `latency_canary_reason.low_signal=2599`
- `latency_canary_reason.tag_not_allowed=1266`
- `latency_canary_reason.quote_stale=866`
- `latency_block_quote_not_stale=3869`

판정 근거:

- bugfix 이후 `canary_applied`는 로컬/원격 모두 `0건`을 벗어났다.
- 하지만 `low_signal`과 `tag_not_allowed`가 여전히 주 blocker다.
- 따라서 지금 시점에서 `tag/min_score` 추가 완화까지 밀면 해석 가능성이 떨어진다.

### 2-3. split-entry rebase quantity 감사 기준

메인 `2026-04-17`:

- 분할진입 후 `scalp_soft_stop_pct`: `16건`
- `partial 이후 확대`: `13건`
- `partial-only`: `3건`
- `held<=180s`: `11건`
- 정합성 플래그 보유 케이스: `10건`
- 플래그 분포:
  - `cum_gt_requested=9`
  - `same_ts_multi_rebase=8`
  - `requested0_unknown=2`

원격 `2026-04-17`:

- 분할진입 후 `scalp_soft_stop_pct`: `7건`
- `partial 이후 확대`: `6건`
- `partial-only`: `1건`
- `held<=180s`: `3건`
- 정합성 플래그: `0건`

감사 기준 확정:

```text
requested_qty
cum_filled_qty
remaining_qty
fill_quality
entry_mode
buy_qty_after_rebase
rebase_count
same_ts_multi_rebase_count
integrity_flags
```

이상 판정식:

- `requested_qty < cum_filled_qty`
- `requested_qty == 0 and fill_quality == UNKNOWN`
- 동일 초 다중 rebase(`same_ts_multi_rebase_count >= 2`)

### 2-4. split-entry 즉시 재평가 shadow 설계

메인 `2026-04-17`, `partial 이후 확대` 13건 기준:

- `held<=180s`: `10건`
- `peak_profit<=0`: `4건`
- `peak_profit<0.2`: `8건`

원격 `2026-04-17`, `partial 이후 확대` 6건 기준:

- `held<=180s`: `2건`
- `peak_profit<=0`: `3건`
- `peak_profit<0.2`: `5건`

설계 확정:

- trigger 1: `partial_then_expand`
- trigger 2: `multi_rebase`
- shadow window: `90초`
- 수집 목적: `확대 직후 나쁜 포지션 확대` 코호트를 손절 임계값과 분리해서 관찰

### 2-5. same-symbol cooldown 초안

반복 soft stop:

- 메인: `빛과전자 2회`
- 원격: `코미팜 2회`

초안:

- 적용 후보: `same-symbol + split-entry soft stop`에만 제한
- 초안 시간: `20분`
- 최종 판정 보류 이유: 오늘 장중 후반 반복 케이스가 더 붙는지 확인 필요

---

## 3. 실전 반영

### 3-1. 코드 반영

- 신규 분석 유틸 추가:
  - [split_entry_followup_audit.py](/home/ubuntu/KORStockScan/src/engine/split_entry_followup_audit.py)
- 런타임 shadow stage 추가:
  - [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py)
  - 추가 stage:
    - `split_entry_rebase_integrity_shadow`
    - `split_entry_immediate_recheck_shadow`

### 3-2. 문서 반영

- [2026-04-17-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-17-stage2-todo-checklist.md)
- [2026-04-17-softstop-after-partial-fill-analysis.md](/home/ubuntu/KORStockScan/docs/2026-04-17-softstop-after-partial-fill-analysis.md)
- 본 보고서:
  - [2026-04-17-noon-followup-auditor-report.md](/home/ubuntu/KORStockScan/docs/2026-04-17-noon-followup-auditor-report.md)

### 3-3. 재기동 필요 사항

- 이번 변경 중 런타임 수집이 필요한 것은 `sniper_execution_receipts.py`다.
- 재기동 완료 시각:
  - 로컬 `bot_main.py`: `2026-04-17 12:52 KST` 실행 확인
  - 원격 `bot_main.py`: `2026-04-17 12:53 KST` 실행 확인 (`tmux bot`, 신규 PID 확인)
- 따라서 아래 shadow stage의 실표본 수집 시작 시각은 각각 위 재기동 완료 이후다.
- noon 이전 장중 표본은 신규 stage 2종에 소급 적재되지 않는다.
- 재기동 후부터 남은 장중 표본에 아래 stage가 추가 적재된다.
  - `split_entry_rebase_integrity_shadow`
  - `split_entry_immediate_recheck_shadow`

### 3-4. noon 시점 live risk 메모

- 아주IB투자 `protect_trailing_stop` stale protection 이슈는 noon 보고서 작성 시점에 **미수정 live risk**였다.
  - `id=2710`, `id=2722` 모두 음수 손익인데 `익절 완료`로 오표시됐고, 이전 포지션 보호선 `12,607원` 잔존 정황이 확인됐다.
  - 이번 턴에서는 코드 수정 없이 `2026-04-20 PREOPEN 09:00~09:20` 후속 설계 항목으로만 고정했다.
- 코미팜 `id=1664` 유령 `hard_time_stop_shadow`는 오늘 현재 로그 재검색에서 동일 `id` 재현은 확인되지 않았으나, 명시적 same-day 재발 기준이 없었으므로 후속 판정 기준을 체크리스트에 추가한다.

---

## 4. 테스트 / 검증 결과

- `pytest -q src/tests/test_split_entry_followup_audit.py src/tests/test_split_entry_followup_runtime.py`
  - 결과: `4 passed`
- `python -m py_compile src/engine/sniper_execution_receipts.py src/engine/split_entry_followup_audit.py`
  - 결과: 통과
- 원격 fetch:
  - `PYTHONPATH=. .venv/bin/python -m src.engine.fetch_remote_scalping_logs --date 2026-04-17 --include-snapshots-if-exist --snapshot-only-on-live-failure`
  - 결과: `status=ok`

---

## 5. 다음 액션

1. 장중 잔여 시간에는 신규 shadow stage 2종 누적을 우선 수집한다.
2. `same-symbol cooldown` 최종 판정은 오늘 장후에 내린다.
3. `2026-04-20 PREOPEN`에는 원격 `Performance Tuning/Entry Pipeline Flow timeout` 원인 또는 fallback 유지 방침을 기록한다.
4. `2026-04-20 PREOPEN`에는 `protect_trailing_stop` stale protection 수정안과 코미팜 ghost shadow 재발 기준을 함께 재판정한다.
5. `GitHub Project / Calendar` 동기화는 사용자 원칙대로 수동 진행한다.
