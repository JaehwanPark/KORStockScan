# 미사용 파일형 raw 추가 삭제 계획 — 2026-10-07

## 1. 목적·기준·권한

사용자 요청: **기존 계획의 삭제 완료 후 남은 미사용 원본 raw의 추가 삭제 범위를 찾아 계획을 수립한다.** 이번 산출물은 조사와 계획이며 추가 삭제·reader 구현·배포를 실행하지 않았다.

- [선행 삭제 기록](../audits/pre-september-source-data-retirement-execution-2026-10-07.md): 3,102개 파일 삭제, 실제 여유 공간 17.787GiB 증가. 이번 후보에 이미 삭제한 파일을 다시 더하지 않는다.
- **실제 사용 여부로 판정한다.** 원본을 여는 reader와 보고서의 날짜·path·hash 문자열 참조를 구분한다. 미사용 raw는 복구 가능 여부와 무관하게 삭제 대상으로 분류하며 새 raw 백업을 만들지 않는다.
- **보존:** 초기 매수수량의 현재/부모 정책 및 연결 보고서·후행 증빙과 내부 과거 행, 기존 정책·모델 parameter·운영자 잠금·승인·custody, 현재 누적 정책·진행 중인 연구의 실제 원천.
- **DB 제외:** DB 본체·행·index·WAL·volume·DB 전용 dump는 삭제하거나 변환하지 않는다. 파일형 Parquet/JSONL 복제본은 별도 후보이며 DB 원장·아침 scanner·EOD 저장 창은 이 계획의 변경 대상이 아니다.
- 9/29는 아래 특정 사본·캐시를 조사한 후보 경계다. 모든 정책의 학습 시작일·canonical raw 보존 기간을 9/29로 바꾸는 지시가 아니다. 6/5 clean-baseline provenance와 현행 Main 12+12셀 선택 계약도 그대로 유지한다.
- 단계 A0~A5는 제안 순서다. 구현·삭제 실행 시 당일 체크리스트에 단일 실행 owner와 실제 일정·수용 기준을 등록하며, 이 문서 자체로 cron/정기 purge를 등록하지 않는다.

상세 근거는 [추가 사용처 조사](../audits/additional-unused-raw-file-use-audit-2026-10-07.md)에 둔다.

## 2. 추가 후보와 회수량

10/7 10:49~11시대 파일 조사 기준이다. 용량은 inode 중복을 제거한 `st_blocks × 512` 할당량이다. **94파일·22.792GiB는 조건부 후보 전체의 상한**이며 현재 확정 회수량이 아니다. gzip 21파일은 각 64행 표본까지만 확인했고 실행용 내용 hash·전체 검증은 아직 하지 않았다.

| 구분 | 파일과 조사 기간 | 개수 | 할당량 | 판정·삭제 전 완료 사항 |
|---|---|---:|---:|---|
| A: 격리 전 raw 복구 사본 | `data/source_quality/raw_row_exclusion/*/pipeline_events_*.jsonl.gz`, 9/3~10/6 | 16 | **4.191GiB** | **미사용 사본 우선 후보.** 현행 감사/정책 소비는 manifest를 읽고 `backup_path`를 전달하며 백업 본문을 열지 않음. 실행 중 격리 작업 없음·manifest 확정·파일 단위 보존 예외를 최종 확인 후 삭제 |
| B: 과거 analytics 파일 | `data/analytics/parquet/{pipeline_events,post_sell,system_metric_samples}/date=*`, 9/1~9/28 | 39 | **14.292GiB** | **reader 보완 후 후보.** 정기 장후 비교가 `date=*`를 등록한 뒤 SQL 날짜 필터를 적용함. 요청 날짜 partition만 등록하고 현행 비교 결과가 유지되는지 검증 |
| C: 옛 threshold snapshot | `data/threshold_cycle/snapshots/pipeline_events_*.jsonl.gz`, 9/11·14·15·16·17 | 5 | **4.008GiB** | **간접 reader의 현재 창 확인 후 후보.** ADM 발행은 퇴역했지만 진입 관측 adapter가 옛 공통 loader를 재사용함. 현재 필요한 window와의 겹침·유효 표본 사용 여부 확인 |
| D: 옛 sentinel 이벤트 사본 | `data/runtime/sentinel_event_cache/{buy_funnel,holding_exit}_sentinel_events_*.jsonl[.gz]`, 9/1~9/28 | 34 | **0.301GiB** | **정확 날짜 소비 확인 후 후보.** 현재 sentinel은 대상일 cache를 사용하나 과거 날짜 flow 보고서의 fallback이 존재함. 현행 요청 범위·압축 canonical 입력 처리 확인 후 해당 캐시만 삭제 |
| 합계 | 위 네 집합의 물리 파일 중복 0 | **94** | **22.792GiB** | A는 4.191GiB, B+C+D의 조건부 상한은 18.601GiB |

파일 목록: [후보 분류](../../tmp/additional-unused-raw-audit-20261007/candidate-file-groups.json), [개수·할당량 합계](../../tmp/additional-unused-raw-audit-20261007/candidate-summary.json). 이는 **계획용 inventory이며 삭제 CLI의 apply manifest가 아니다.** 기존 보존 목록 3,101개와의 겹침은 0이지만, 현재 신규 연구·정책 의존성까지 보호한다는 증명은 별도로 갱신한다.

### 별도 소량 후보 — 위 합계에서 제외

- 선행 계획에서 남은 pre-September real post-sell 102개와 sim 42개, 합계 **6.223MiB**. real reader는 누적 보유/청산 분석 때문에 읽으며, sim은 entry-split 및 counterfactual/discovery helper의 날짜 선택을 추가 확인해야 한다. [기존 계획 D1](pre-september-source-data-permanent-deletion-plan-2026-10-07.md#d1--실제-원천-reader-보완)의 존재 날짜 기반 읽기와 유효 소비 범위 분리를 완료한 항목부터 처리한다. 단순히 sim/OFF라는 이유로 삭제하지 않는다.
- `tmp/widget-retirement-execution-20261006/widget-dedicated-data-before.tar.gz` **53.656MiB**. raw 캐시와 보고서·정책·수동 주문 상태·lock이 혼합되어 있다. raw cache 256개는 논리 크기 25.605MiB이며 압축 archive의 회수량과 같지 않다. 보존 member의 정확한 bytes/hash가 기존 보존 위치에 있는지 확인하고 부족한 **nonraw만** 보존한 뒤 archive를 제거한다. 추가 raw 백업을 만들지 않는다. 필요한 nonraw 추출량이 archive보다 클 수 있어 **순회수량이 양수인 것으로 가정하지 않는다.**

## 3. 후보별 실제 참조와 보완

### A — raw exclusion 복구 사본

생산자는 [observation_source_quality_audit.py](../../src/engine/observation_source_quality_audit.py)의 `_exclude_hard_blocking_rows_from_raw()`다. 사본 생성 후 원 canonical raw에서 식별된 결손 행을 격리하고 manifest에 원인·행·백업 경로를 남긴다. 현재 `_existing_applied_raw_row_exclusion()`과 workorder는 manifest를 읽는다. `backup_path`가 문자열로 존재하는 것과 백업 파일을 여는 것은 다르다.

삭제 대상은 16개 gzip 본문이다. **manifest·감사 보고서·원인별 격리 metadata와 현재 canonical pipeline은 보존**한다. 과거 `backup_path` 문자열은 감사 이력이며 경로가 없어졌다고 과거 격리가 실패했다고 바꾸지 않는다. 별도 삭제 영수증에 삭제일·사본 hash·원 manifest 식별자를 남긴다. 기존 sealed manifest/report를 재작성해 현재 정책 검증 hash를 바꾸지 않는다.

[source_quality_hard_gate.py](../../src/engine/automation/source_quality_hard_gate.py)의 `_archived_raw_digest()`는 canonical raw의 압축 세대 검증이다. 이 canonical `.jsonl.gz`와 raw-exclusion 하위 복구 사본을 혼동하여 함께 삭제하면 안 된다.

**종료 시험:** 후보 백업 경로만 `open/gzip/exists`를 금지한 순수 읽기 검증에서 적용된 격리 manifest 선택·source preflight·workorder 원인 분류가 동일해야 한다. 격리 적용 중 생성되는 임시 사본은 완료 receipt 전 삭제하지 않는다. 이후 새 격리 사본을 생성하는 동작은 현재 남아 있으므로 이번 단발 삭제만으로 영구 재발 방지를 주장하지 않는다. 정기 정리가 필요하면 별도 owner에서 완료된 사본만 manifest 기준으로 처리한다.

### B — analytics Parquet

정기 실행 경로는 `ubuntu crontab → run_runtime_release.sh tuning → run_tuning_monitoring_postclose.sh → compare_tuning_shadow_diff → TuningDuckDBRepository.register_parquet_dataset`이다. **현재 필수 소비가 없는 역사 CLI만 있는 것으로 보면 안 된다.**

- 현재 wrapper 기본 `DIFF_DAYS=3`은 달력일 기준이다. 실제 source 10/6 완료 status에는 **10/4~10/6** 비교 성공이 기록돼 있다. 같은 기본값의 10/7 실행은 10/5~10/7이다. 실행 시 override와 실제 target/start를 다시 확인한다.
- `register_parquet_dataset()`의 기본 `partition_pattern="date=*"`가 범위 밖 파일까지 view/schema 등록에 포함한다. SQL WHERE가 있다고 과거 파일을 전혀 열지 않는 것으로 단정하지 않는다. 반대로 모든 과거 행을 매번 전량 집계한다고도 단정하지 않는다.
- dataset별 **요청 시작~끝 날짜의 실제 존재 파일 목록**을 먼저 만들고 해당 목록만 등록한다. window 밖 missing partition은 재계산/복원 대상이 아니다. window 안 필수 입력 누락·오염은 `source_gap`으로 유지한다. 유효 empty와 파일 누락을 구분하고 `union_by_name`에 필요한 schema를 명시적으로 유지한다.
- 후보 39파일은 footer 기준 9/1~9/28, **6,336,400행**이다. 남기는 9/29 이후 pipeline 4파일의 schema 합집합에 현재 비교가 요구하는 stage/date/overbought/fill-quality 필드가 있다. 이는 query 결과 동등성 시험을 대체하지 않는다.

**종료 시험:** 운영 DB 접속 없이 임시/in-memory fixture로 명시 partition 선택·누락·schema union·날짜 경계·gzip/JSONL 비교를 시험하고, 현재 대상일의 원 보고서와 변경 reader의 읽기 전용 결과를 대조한다. 비교 과정에서 DB 원장·영속 DB 파일을 변경하지 않는다. 과거 file partition을 다시 만드는 자동 backfill을 추가하지 않는다. 현행 wrapper는 `--single-date TARGET_DATE`만 생산하므로 B의 옛 날짜를 기본 재생성하지 않는다.

### C — threshold snapshot

`build_scalp_entry_action_decision_matrix_report()`와 CLI가 retired인 것은 확인했다. 그러나 다음 **실제 raw reader 연결**이 남아 있다.

`entry_context_intraday_probe / entry_ai_gate_backtest → entry_observation_source.load_entry_observations → scalp_entry_action_decision_matrix._iter_relevant_events → _event_paths → snapshots gzip`

probe는 요청 대상일을 읽고, gate backtest는 명시 start/end를 지원한다. 정규 postclose wrapper의 gate backtest는 현재 `on_demand/false`다. 따라서 오늘 자동으로 9/11~17을 읽는다고 볼 근거는 없지만, 모듈 퇴역만으로 간접 helper까지 미사용이라고 판정할 수도 없다.

**분류·보완:** 현재 작업과 승인된 연구가 요청하는 날짜에 후보가 전혀 포함되지 않고 보호 의존성도 없으면 미사용으로 확정해 삭제한다. 과거 날짜를 수동 인자로 줄 수 있다는 이유만으로 보존하거나 reader 수정을 의무화하지 않는다. 실제 현재 창에 포함되는 후보만 adapter의 canonical base/late/압축 경로를 정리하고 snapshot fallback을 분리한다. 그때 후보에만 존재하는 유효한 현재 요구 표본이 있는지 record ID/시간/owner 기준으로 검사하며, 필요한 표본이 있으면 해당 파일은 보존으로 재분류한다. archive 복원·과거 판정 재계산은 조건으로 두지 않는다. 기존 dedupe·lineage·격리 semantics를 유지한다.

**종료 시험:** snapshot 접근을 차단한 상태에서 현행 probe와 유효 backtest window의 입력 ID·분모·후행 결합이 동일하다. 폐기한 옛 날짜의 on-demand 요청에는 의도적 폐기 상태를 명시하고 자동 복원/빈 표본 정상 처리로 숨기지 않는다. 현재 canonical 파일 자체가 빠지면 기존 source gap을 유지한다.

### D — sentinel 캐시

[sentinel_event_cache.py](../../src/engine/sentinel_event_cache.py)는 대상일 raw와 cache generation을 사용한다. [intraday_entry_flow_report.py](../../src/engine/monitoring/intraday_entry_flow_report.py)의 `_default_event_cache_path()`는 **비압축 pipeline 파일이 없을 때** buy-funnel day cache를 선택한다. 압축 canonical만 남아 있어도 fallback이 선택될 수 있다.

**분류·보완:** 현재 요청일 집합과 보고서 소비를 확인한다. 9/1~28 cache의 실제 현재 소비가 없으면 raw 사본을 삭제하며 과거 날짜 수동 재현을 보존 조건으로 두지 않는다. 현재 필요한 날짜에 fallback이 발생하는 경우만 `.jsonl/.jsonl.gz` 존재 판정을 통일하고 결과 동등성을 확인한다. `.meta.json` 등 비raw metadata는 별도 분류하며 34개 raw 용량에 합산하지 않았다. 보존 보고서의 path 문자열 때문에 cache를 의무 재생성하지 않는다. 현재 당일 cache와 source generation 검증은 유지한다.

**종료 시험:** 현재 target일 sentinel/flow 보고서가 동일하고 후보 파일 open은 0이다. 요청 범위 밖 폐기일의 cache 자동 재생성은 없다. 압축 canonical·base/late·missing current source를 각각 시험한다.

## 4. 이번에 보존하는 실제 원천과 이유

| 원천·파일 | 보존 이유 |
|---|---|
| 9월 이후 canonical `data/pipeline_events/*.jsonl[.gz]` | AVG_DOWN calibration의 `_iter_events_paths_for_window()`가 clean baseline 이후 **실제 존재 날짜 전체**를 읽어 현재 누적 route/실행/청산 근거를 만듦. Main의 특정 refresh 하한만으로 삭제할 수 없음 |
| 현재 반전의 quote/trade/완성 분봉·forward observation 원천 | `continuous_reversal_source` 및 삼성 새 분기의 확인시점·30분 라벨·정확 경로·비용 비교 입력. 원천 없는 보고서 hash만으로 대체됐다고 증명되지 않음 |
| 실제 AI 요청·응답 및 현행 누적 평가 원천 | 보조 12셀의 실제 prompt/input/schema에 대응한 판정·응답 검증과 누적 분모. 구 문구 제외 표본도 현재 감사 보존과 원천 미사용 여부를 별도로 판정 |
| 삼성/연속 반전의 현재 research tmp와 source manifest | [병행 정책 계획 §8.3](main-multi-policy-parallel-entry-and-samsung-shallow-pullback-implementation-plan-2026-10-07.md#83-cache와-원천-유지)이 동결 source/event/bars/후보/code를 참조. `tmp`·오래된 날짜만으로 삭제하지 않음 |
| 초기 수량 연결 보고서, trade_review snapshot, machine projection 등 | 보고서/후행 증빙이며 raw 사본이라는 증명 없음. 특히 초기 수량 연결 8파일과 내부 347개 과거 행은 사용자 보존 대상 |
| 정책·모델·잠금·수동 주문/보유 상태와 이전 archive에서 보존한 nonraw | 사용자 보존 대상. 크기·날짜·퇴역 family 명칭으로 정책이나 custody를 raw로 재분류하지 않음 |
| DB 본체/원장/DB 전용 dump | 명시적 범위 제외. 파일형 복제본 제거를 이유로 DB 보존 기간/행을 바꾸지 않음 |

보존은 해당 실제 소비 근거에 한정한다. 새로운 reader 분리·native source 이관으로 raw 접근이 없어지면 후속 조사에서 재분류할 수 있으며 복구 가능성을 추가 요구하지 않는다.

## 5. 실행 설계

| 단계 | 작업 | 종료 조건 |
|---|---|---|
| A0 | 최신 파일·selected release/actual consumer·프로세스 FD·진행 중 writer·보존 목록 재고정 | 목록의 realpath/device/inode/nlink/크기/mtime/ctime/hash, reader와 유효 window, 보호 근거 기록. 계획 작성 뒤 새 파일을 glob으로 자동 포함하지 않음 |
| A1 | 후보별 삭제 manifest 구현·리뷰 | 기존 v1의 `<2026-09-01` 조건을 전역 완화하지 않음. 새 사유 class/버전으로 **미사용 사본**과 **reader 보완된 범위 밖 파일**을 구분. DB·symlink/hardlink·열린 FD·보호 파일 검사는 유지 |
| A2 | A의 16개 복구 사본부터 최종 검증·삭제 | 완료된 격리 세대만 처리. 현재 canonical·metadata·보고서·정책 내용 불변. B/C/D 수정 완료를 A의 공통 선행 조건으로 묶지 않음 |
| A3 | B reader 보완, C/D 현재 사용 여부 확정 및 실제 필요한 reader만 보완·리뷰·표본 검증 | 각 §3 종료 시험 통과. reader를 바꿨다면 실제 후속 작업에 선택될 경로까지 확인. 현재 미사용인 C/D에 불필요한 구현·재기동을 공통 조건으로 붙이지 않음 |
| A4 | 소량 post-sell·혼합 widget archive 분류 완료 후 별도 처리 | 유효 consumer 분리 및 nonraw 보존. 혼합 archive는 nonraw 보존 후 순회수량도 확인 |
| A5 | 파일 삭제·보존·공간 및 다음 자연 작업 확인 | manifest의 삭제 파일 잔존 0/보호 유실 0, 실제 `df` 증감 기록. 영향받은 정규 작업의 다음 자연 완료와 code 검증을 구분 |

현재 [source_data_retirement.py](../../src/engine/automation/source_data_retirement.py)는 pre-September manifest v1이며 threshold snapshot family도 allowlist에 없다. **이 문서의 94파일을 기존 `--apply`에 바로 넣으면 안 된다.** 기존 `unused_generation_preselection` 예외를 모든 raw에 재사용하지 않는다. 구현 위치는 기존 `src/engine/automation` 소유자를 확장하며 engine root에 새 삭제 모듈을 만들지 않는다.

정규 reader/예약 자동화를 실제 변경할 때는 operating 문서와 당일 checklist도 함께 갱신한다. 원본을 새로 압축·백업하거나 삭제 후 DB/API에서 자동 복원하는 경로를 만들지 않는다. 정책/준비 문서 bytes가 변하지 않는 단순 미사용 사본 삭제에 새로운 정책 승계 조건을 붙이지 않는다. 실제 native 입력 계약이 바뀐 class만 해당 검증·필요한 PREOPEN 재준비를 수행한다.

## 6. 수용·검증과 이번 완료 범위

- **분류 정확성:** path/hash metadata 참조와 실제 open을 구분한다. C의 간접 adapter, B의 정기 등록, D의 gzip fallback을 누락하지 않는다.
- **의미 보존:** 현재 정책/보고서의 ID·분모·비용·후행 결합·source gap 분류를 보존한다. 결손을 0 수익/정상 empty로 바꾸거나 삭제 때문에 EV·최소 표본/일수·holdout 등 새 채택 문턱을 추가하지 않는다.
- **파일 경계:** 적용 시 내용 hash·정체성·보호/DB/open-FD 경계를 다시 확인한다. payload 표본을 전수 기간 검증이라고 부르지 않는다. 무관한 dirty 코드·문서·생성물을 변경하지 않는다.
- **회수량:** 22.792GiB 상한, class별 실제 삭제 할당량, 다른 writer와 nonraw 보존을 반영한 `df` 순증가를 각각 기록한다.
- 이번에는 파일 metadata 조사, Parquet footer 전수 확인, gzip 표본, archive member 목록, 현재 코드/선택 릴리스/예약 경로 및 이전 삭제 영수증을 읽고 문서를 작성했다. 문서 리뷰·보완·링크 검사·print-only backlog parser·`git diff --check`로 마감했다. 실제 삭제, 코드 구현, DB query/변경, broker/provider 호출, 보고서 재생성, 배포·재기동 및 자연 장후 검증은 실행하지 않았다.
