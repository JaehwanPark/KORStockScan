# 2026-05-01 Stage2 To-Do Checklist

## 오늘 목적

- `2026-05-01`은 근로자의 날 KRX 휴장일이므로 실전 장전/장중/장후 판정 작업을 실행하지 않는다.
- `2026-04-30` 장후 판정에서 새 후속 작업이 필요하면 다음 KRX 운영일인 `2026-05-04` 체크리스트에 `Due`를 고정한다.
- 이 파일은 workorder/Project/Calendar가 휴장일에 실전 작업을 잘못 생성하지 않도록 남기는 휴장 기록이다.

## 오늘 강제 규칙

- 휴장일에는 실전 `PREOPEN/INTRADAY/POSTCLOSE` 작업을 새로 열지 않는다.
- 단, threshold collector 초기 적재처럼 실전 주문/판정에 영향을 주지 않는 maintenance bootstrap은 `RuntimeStability` 작업으로만 허용한다.
- 미래 작업은 상대 표현이 아니라 다음 KRX 운영일 `2026-05-04 KST` 기준 `Due`, `Slot`, `TimeWindow`로 재작성한다.
- 손익/퍼널/체결 품질 판정은 `2026-04-30`까지 확보된 `COMPLETED + valid profit_rate`와 다음 운영일 신규 표본을 분리해 해석한다.

## 장전 체크리스트

- [x] `[ThresholdBootstrap0501-AM] threshold collector 휴일 bootstrap 1차 실행 및 IO guard 확인` (`Due: 2026-05-01`, `Slot: PREOPEN`, `TimeWindow: 09:00~10:30`, `Track: RuntimeStability`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [backfill_threshold_cycle_events.py](/home/ubuntu/KORStockScan/src/engine/backfill_threshold_cycle_events.py)
  - 판정 기준: `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl` partition이 생성되고, `data/threshold_cycle/checkpoints/YYYY-MM-DD.json`에 `byte_offset`, `raw_line_count`, `written_count`, `partitions`, `last_sample_metrics`, `completed/paused_reason`이 기록되는지 확인한다.
  - 실행 원칙: 첫 실행은 raw full scan 반복이 아니라 checkpoint/resume 가능한 bootstrap으로만 수행한다. 기본 line cap은 `--max-input-lines-per-chunk 20000`, `--max-output-lines-per-partition 25000`이며, IO 우려가 있으면 더 작은 cap으로 시작한다.
  - rollback/중단 기준: `paused_by_availability_guard`, `iowait_pct>=20`, `disk_read_mb_delta>=128`, `mem_available_mb<512`, `stopped_source_changed` 중 하나가 나오면 즉시 추가 scan을 멈추고 checkpoint와 system metric sample만 보고한다.
  - 실행 메모 (`2026-05-01 KST`): `2026-04-30` raw pipeline `508,715,934 bytes`를 checkpoint/resume 방식으로 bootstrap 완료했다. 최종 checkpoint는 `completed=true`, `paused_reason=null`, `byte_offset=508715934`, `raw_line_count=469809`, `written_count=10894`, `recommended_next_input_lines_per_chunk=20000`이다.
  - 추가 실행 메모 (`2026-05-01 KST`): 휴일 bootstrap 범위를 `2026-04-25`, `2026-04-27`, `2026-04-28`, `2026-04-29`, `2026-04-30` 가용 raw 전체로 확장했다. 5개 일자 모두 `completed=true`, `paused_reason=null`로 완료했고, 5/4부터 `07:35 PREOPEN manifest`, `16:10 POSTCLOSE collector/report` cron 자동화를 설치했다.
  - 판정 결과: `완료 / 4월 가용 raw partitioned_compact 적재 완료, 5/4 daily cycle manifest-only 자동화 설치`
  - 근거: partition 총량은 `2026-04-25=6`, `2026-04-27=7653`, `2026-04-28=8583`, `2026-04-29=15093`, `2026-04-30=10894`다. 4/30 최종 system metric sample은 `iowait_pct=0.76`, `disk_read_mb_delta=15.805`, `mem_available_mb=12404.0`으로 중단 기준(`iowait_pct>=20`, `read>=128MB`, `mem<512MB`)에 걸리지 않았다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-04-30 --skip-db --print` -> `data_source=partitioned_compact`, `partition_count=5`, `line_count=10894`, `checkpoint_completed=true`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.threshold_cycle_preopen_apply --date 2026-05-04 --source-date 2026-04-30` -> `manifest_ready`, `runtime_change=false`
    - `deploy/install_threshold_cycle_cron.sh` -> `35 7` PREOPEN, `10 16` POSTCLOSE cron 등록 확인
    - `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_backfill_threshold_cycle_events.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py` -> 통과
  - 다음 액션: 5/4부터 daily incremental 운영은 자동 실행한다. 단 live threshold runtime mutation은 5/6 `[ThresholdOpsTransition0506]` acceptance 전까지 `manifest_only`로 막고, 장전 manifest와 장후 report/attribution 결과만 자동 생성한다.

## 장중 체크리스트

- 없음

## 장후 체크리스트

- [x] `[StatActionMatrixReport0501-Maintenance] statistical_action_weight/AI decision matrix 산출물 자동생성 구현` (`Due: 2026-05-01`, `Slot: POSTCLOSE`, `TimeWindow: 09:00~09:20`, `Track: RuntimeStability`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)
  - 판정 기준: 장후 `daily_threshold_cycle_report` 실행 시 `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.md/json`과 `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.md/json`이 같이 생성되는지 확인한다. 실전 runtime 변경은 없어야 한다.
  - 실행 메모 (`2026-05-01 KST`): `daily_threshold_cycle_report`에 운영자용 statistical action Markdown/JSON 저장과 AI holding/exit decision matrix Markdown/JSON 저장을 추가했다. `run_threshold_cycle_postclose.sh`는 기존처럼 `daily_threshold_cycle_report`를 호출하므로 5/4 이후 장후 자동 실행에 산출물이 포함된다.
  - 판정 결과: `완료 / 휴장 maintenance 구현, runtime_change=false`
  - 근거: `2026-04-30` 기준 `statistical_action_weight` 리포트는 `completed_valid=109`, `price_known=109`, `volume_known=103`, `time_known=109`, `weight_source_ready=true`로 생성됐다. AI decision matrix는 `holding_exit_decision_matrix_v1_2026-04-30`, entries `14`, `runtime_change=false`로 생성됐다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_backfill_threshold_cycle_events.py src/tests/test_threshold_cycle_preopen_apply.py` -> `16 passed`
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/daily_threshold_cycle_report.py` -> 통과
    - `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-04-30` -> 두 산출물 자동 생성 확인
  - 다음 액션: 5/6 `[StatActionMarkdown0506]`, `[AIDecisionMatrix0506]`는 구현이 아니라 실제 운영일 산출물 health check와 shadow prompt 주입 전제 확인으로 본다.
