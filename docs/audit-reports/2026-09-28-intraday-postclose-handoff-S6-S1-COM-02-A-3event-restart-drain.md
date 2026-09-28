# S6 `S1-COM-02-A` 후속 — 9/23 raw·shadow 3 event 재시작 경계

실행일: **2026-09-28 KST**. 인계: [S7 통합 검증](2026-09-28-intraday-postclose-handoff-S7.md), [기존 원천·요약·첫 stage 수리](2026-09-28-intraday-postclose-handoff-S6-S1-COM-02-A.md). 판정: **재시작 drain 이후 raw append는 계속되지만 요약 compactor가 닫혀 있던 생산자 계약 결손을 확인·수리했다.** 임시 경로 fixture에서 원천→요약 봉인→`pre_submit_delay` 첫 stage의 동세대 수용과 구세대 거절을 확인했다. 9/23 운영 manifest·stage 영수증은 그대로이며 역사적 3건을 소급 봉인하지 않았다. 선택 릴리스·PID·자연 장후 수용은 확인하지 않았다.

## 원천·identity와 분모

9/23 `data/pipeline_events/pipeline_events_2026-09-23.jsonl.gz`의 압축 크기는 **437,234,985 bytes**, 해제 논리 크기는 **6,534,993,803 bytes**, 논리 SHA-256은 `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`이다. 읽기 전용 전수 스캔의 raw **374,864 = 생산자 요약 profile 유효 166,643 + profile 외 제외 208,221 + 격리 0 + 미관측 0**이다. 저장 shadow는 **166,640 event / 70,076 row**이다. 3 event는 summary profile의 미수록분이다. scanner promotion 3,216건, 이 raw 전체, 요약 event, 요약 row는 서로 다른 단위다. 원천 중복은 0이었다.

raw와 저장 shadow의 stage별 `canonical_payload_sha256_sum_v1` 합계를 비교하고 압축본을 스트리밍해 차이의 canonical identity와 일치하는 원본 line을 찾았다. 세 line 모두 `emitted_date=storage_partition_date=2026-09-23`, base partition, `record_id=47859`, `stock_code=122350`, `scanner_promotion_id=SCANPROM-122350-1790140559661`이다. offset은 **gzip 파일의 물리 offset이 아닌 해제 논리 byte의 `[start,end)`**이다.

| stage (raw / shadow event) | KST 원본 시각 | 논리 offset | line SHA-256 | canonical identity |
| --- | --- | --- | --- | --- |
| `scalping_scanner_promotion_latency_trace` (49,736 / 49,735) | 14:20:33.225612 | 3,396,345,288–3,396,348,678 | `ddebec331525c555117066041a02b00451d8a3884274332912cb41ff0078933a` | `2bfbf2b342bbf8b5f5e89af02a2e02f58d6ed993fb312a52de62645087688860` |
| `scalping_scanner_heavy_eval_lag` (11,623 / 11,622) | 14:20:33.236401 | 3,396,348,678–3,396,351,226 | `ac1136eded073e488b5a7bf67e48f1aaa407b40d87d85fa1ad2f35a022af3911` | `746f4bb04e089aac154590917539323647fc0bbfe052b2bbee99425a7cba0cc4` |
| `scalping_scanner_heavy_eval_completion` (12,681 / 12,680) | 14:20:33.243061 | 3,396,351,226–3,396,353,897 | `2bffd0d394b6d437dac7897ad68539dd7a04a11abe62659a2c20872cf6fb68f9` | `7cb82905ff38cbb6085fbcae04b7399639d76e133bf1d09be8a1632893c4bab7` |

재현: `.venv/bin/python -c 'from pathlib import Path; from src.engine.pipeline_event_summary import _producer_raw_ledger; print(_producer_raw_ledger(Path("data"), "2026-09-23"))'`는 읽기 전용 raw 분모·stage identity 합을 얻는다. 원본 line 검사는 `gzip.open(..., "rb")`의 누적 해제 byte offset으로 위 세 범위의 SHA를 확인했다. 스캔 중 압축 파일 크기·mtime이 안정적이었으며 단일 base part 외 late part는 없었다. 저장 manifest SHA는 `59ece8b1c9ee26ddb8289d4caf5d151eec0f35d1c73a268dd9f4ecbc288d27d3`, 요약 JSONL SHA는 `93ce78d3a97b707b1acbffabc349f39b4a6d953595c45b56f4479ccd2b699e24`, 저장 `pre_submit_delay` terminal SHA는 `4237e26547a5f7cc4a24093fd791127c8c8a2061abc729d7a09c18673d891a38`이다. 운영 세 파일은 수정하지 않았다.

## 원인·직접 소비자

`logs/bot_history.log.2026-09-23:16243-16248`은 **14:20:30 KST** `operator_restart_sh` 수동 재시작 요청 뒤 **14:20:33**에 `producer summary is closed; raw must be retained` 오류 세 줄을 기록한다. 이전 PID는 `225779`, 새 bot 시작은 14:20:35다. 세 오류의 초 단위 시각·건수는 세 원본과 맞는다. 오류 줄에 record/event ID가 없어 **각 오류 줄과 각 event의 1:1 배정은 `historical_unbound`**이다. 그러나 코드에서 `emit_pipeline_event`는 raw를 먼저 append하고 compactor에 제출하며, 구 `drain_pipeline_event_summary_before_termination()`은 종료 신호 전에 compactor를 `close()`하고 pointer는 유지한다. 그 사이 다른 scanner 작업의 세 제출은 닫힌 compactor에 거절된다. 정상 9/23 partition, raw 무중복·무손상, 같은 bucket의 재시작 직전 요약 row와 로그를 함께 확인했다. profile 제외·자정 late·장후 seal 후 원천 변경이 이 세 건의 직접 원인이라는 증거는 없다.

기존 첫 reader `postclose_summary_handoff.run_stage("pre_submit_delay")`는 raw ledger와 shadow count·identity 불일치 시 **`deferred(exit=75)`**로 명령 시작을 막는다. 이 fail-closed 판정은 올바르므로 reader 구현은 바꾸지 않고, 수리 전 실패와 수리 후 동세대 성공·재작성 후 stale 거절을 같은 fixture에서 검증했다. 9/23 옛 manifest에는 raw ledger가 없어 저장 stage `succeeded`도 현재 reader에게는 `raw_source_ledger_missing`이다.

## 실패 재현→수리→자가 리뷰

먼저 `src/tests/test_pipeline_event_logger.py::test_restart_drain_keeps_late_scanner_rows_bound_to_first_stage`를 추가했다. 임시 DATA_DIR에서 첫 scanner event→재시작 drain→같은 record의 세 scanner event→첫 stage 순으로 실행하면, 수정 전 raw 네 건은 남지만 세 요약 제출이 `closed`로 실패하고 첫 stage가 **`deferred(exit=75)`**가 되어 테스트가 실패했다.

수리는 `src/utils/pipeline_event_logger.py`의 재시작 drain에서 현재 compactor를 **flush하고 열린 채로 유지**하며, 이후 들어오는 compactor에도 drain 모드를 적용한다. `src/engine/pipeline_event_summary.py`의 drain 모드는 종료 전 늦은 각 유효 요약 제출을 동기 flush한다. 실제 종료의 atexit close와 실패 시 raw 보존은 유지한다. 변경 후 fixture는 원본 4·유효 4·제외 0·격리 0·미관측 0, 세 stage의 identity 포함 manifest 봉인, 첫 stage `succeeded`와 동세대 영수증 검증을 통과한다. 이후 새 event를 기록하면 기존 stage가 `raw_source_ledger_missing`으로 **구세대 거절**된다. 이를 새 세대의 성공으로 자동 치환하지 않는다.

자가 리뷰는 raw 우선 append, compactor mode handover·retiring owner, 중복 drain, 실패 시 raw 보존, `SIGTERM` 이후 atexit 미실행, 첫 reader의 fail-closed, 날짜·identity·source-quality 및 운영 권한 경계를 점검했다. 범위 내 확인된 결함은 수리했고 재리뷰의 미해결 코드 결함은 0이다. **남은 운영 위험:** SIGTERM이 별도 thread의 raw append와 동기 submit 사이에 도착하면 이 수리만으로 원자적 종료를 보증할 수 없다. 해당 gap은 새 source date의 ledger 봉인이 차단하며, 운영 경로의 자연 재시작 수용은 아직 미관측이다. 재시작 중 동기 disk flush의 실제 latency도 측정되지 않았다.

## 검증·닫힘·인계

- 실패 fixture 수정 전 **1 failed** (`pre_submit_delay deferred(exit=75)`); 수정 및 구세대 거절 보완 뒤 영향 pytest 5파일 **222 passed**: `test_pipeline_event_logger.py`, `test_pipeline_event_summary.py`, `test_pipeline_event_verbosity_report.py`, `test_postclose_summary_handoff.py`, `test_pre_submit_delay_tuning.py`. 운영 경로와 분리된 임시 fixture 출력만 생성했다.
- 변경 Python 3파일 compile, `git diff --check`, 보고서 상대 링크 2개·trailing whitespace 0, print-only backlog parser **exit 0·32 task**를 확인했다. wrapper는 수정하지 않아 `bash -n`/wrapper 계약 검사는 해당 없음이다.
- owner: `pipeline_event_logger` raw append·drain, `ProducerSummaryCompactor` 요약 제출·flush, `postclose_summary_handoff` 첫 stage 봉인. 다음 **자연 source date**에서 같은 날짜·partition·논리 SHA·offset/identity에 대해 원본=유효+제외+격리+미관측, 요약 profile의 stage별 count·identity 합과 manifest, 첫 stage 입력·terminal SHA의 일치를 검사한다. 재시작 직전/직후 event와 로그의 ID 결속도 확인한다. 이어 **S7의 운영과 분리된 격리 재측정**으로 넘긴다. 9/23 옛 manifest를 채워 넣거나 세 건을 임의 제외해 봉인하지 않는다.
- 9/23 `research_capacity=failed(exit=2)`→`research_allocation=deferred(exit=75)`→summary 실패, 과거 `main_terminal` strict PASS는 그대로다. scanner 압축 reader, 새 자연일 조건부 `S5-FIN-05`, 나머지 S7 전체 체인 성능은 별도 범위다. 릴리스·PREOPEN·실제 PID·자연 경제성은 S8 경계다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포·정규 장후작업·PREOPEN을 변경하거나 실행하지 않았다.
