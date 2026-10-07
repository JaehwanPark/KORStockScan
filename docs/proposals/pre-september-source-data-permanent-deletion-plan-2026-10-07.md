# 9월 이전 파일형 원천 데이터·백업 영구 삭제 계획 — 2026-10-07

## 1. 목적과 확정 범위

사용자 요청: **9월 이전 원본 raw의 실제 사용을 재확인하고 파일형 데이터의 삭제 계획을 보완한다. 원본을 참조하지 않으면 복원 가능 여부와 관계없이 삭제 대상으로 분류한다. 초기 매수수량의 연결 보고서, 기존 정책·운영자 잠금은 유지한다. DB는 대상이 아니다.**

- 폐기 경계: 실제 관측·거래 일시가 **`2026-09-01T00:00:00+09:00` 미만**인 파일형 원천. UTC 경계는 `2026-08-31T15:00:00Z`다. 수정일·압축일·정책 출처 날짜만으로 판정하지 않는다.
- 포함: 원본 JSON/JSONL/CSV, 파일형 gzip/Parquet·시세 캐시·연구 입력·raw exclusion 복구 사본, 해당 원천의 archive/backup, 릴리스/작업트리/임시 디렉터리의 독립 원천 사본. 동일 물리 파일의 링크는 중복 계산하지 않는다.
- **보존 우선:** 초기 매수수량의 현재/부모 정책과 연결 보고서·stage·후행 증빙, 기존 정책·모델 parameter·운영자 잠금·승인·종료 조건, 현재 주문/보유 소유권 상태를 유지한다. 연결 보고서의 과거 거래 행도 삭제·필터링·재작성하지 않는다.
- **DB 제외:** PostgreSQL 테이블/행/index/WAL/volume, DB 본체 파일과 DB 전용 dump를 삭제하거나 전환하지 않는다. DB 일봉·아침 KOSPI_ML scanner·EOD 저장 창 변경을 삭제 선행 조건으로 두지 않는다. DB 유래 이벤트의 파일형 JSONL/Parquet 복제본은 별도 파일 대상이며 DB 원장은 그대로 유지한다.
- 원본 raw가 현재 소비되지 않으면 백업 유무·복원 가능성·과거 재계산 가능성을 보존 조건으로 두지 않는다. 삭제할 raw와 raw 백업을 위해 새 archive/복구 사본을 만들지 않는다.
- 최초 작성은 읽기 재점검과 문서 보완이었다. 이후 사용자의 **“계획대로 점검하여 디스크공간을 확보하라”** 지시로 금일 파일 삭제를 실행했다. 승인된 단발 삭제 결과와 보존/미처리 구분은 §7에 기록하며, DB·거래 프로세스 배포/재기동 권한으로 확대하지 않는다.

[조사 기록](../audits/pre-september-source-data-use-audit-2026-10-07.md)은 직접 raw 읽기와 보고서·설정 참조를 구분한다. 구현 시점의 실행 owner는 당일 체크리스트에 등록한다. 이 계획은 새 예약 작업이나 runtime 변경 권한을 생성하지 않는다.

기존 `clean_tuning_baseline_date=2026-06-05` provenance를 일괄 치환하지 않는다. 새 파일 선택 하한은 `max(2026-09-01, 소비자의 유효한 기존 하한)`이며 기존 refresh의 9/29 하한과 현행 반전의 9월 이후 누적 원천을 유지한다. 보존 보고서·정책·부모의 출처 날짜에는 raw 선택 하한을 적용하지 않는다.

## 2. 실제 읽기 재점검 결과

| 소비자 | 실제 읽는 자료 | 원본 raw 의존 판정 | 삭제 계획 반영 |
|---|---|---|---|
| 진입 타이밍 `_source_reports()` / `build_report()` | `data/report/machine_microstructure_attribution/*.json` 및 그 보고서 자체의 bytes/hash | 8월 보고서 참조는 원본 JSONL 재조회가 아님 | 다른 소비자의 실제 raw 접근도 없는 원본은 삭제 대상. 보고서의 날짜/path/hash만으로 raw를 보존하지 않음 |
| 삼성 native actual 보완 | runtime checkpoint와 기존 timing 결과 보고서 한 세대 | 과거 원본 raw 재생이 아님 | 필요한 현재 checkpoint·보고서는 유지. 해당 원본 보존 이유로 사용하지 않음 |
| 초기 매수수량 PREOPEN 검증 | 현재/부모 정책, parent-current, stage, replay·candidate·following-bars 보고서 | 아래 읽기 제한 검증에서 원본 raw 접근 **0**, native 검증 **PASS** | 연결 보고서와 그 내용·hash를 그대로 보존. 보고서 삭제용 adoption/retirement receipt 구현은 제거. 다른 소비자가 읽지 않는 원본은 삭제 대상 |
| 초기 매수수량 재계산 `join_post_fill_paths()` | 거래 진입일의 `pipeline_events_YYYY-MM-DD.jsonl[.gz]`를 직접 읽음 | 재계산 함수는 raw reader. 현행 정책 기동 검증과 구별 | 정상 후속 refresh의 parent 적용일 이후 창 유지. 삭제한 6~8월 seed를 다시 계산하지 않으며 원본 복원 불요. DB trade fact는 유지 |
| 보유·청산 `_load_post_sell_rows()` | `data/post_sell/post_sell_candidates_*.jsonl[.gz]`, `post_sell_evaluations_*.jsonl[.gz]`; 별도로 trade_review snapshot | post-sell은 실제 파일형 raw 읽기. 현재 6/5부터 날짜를 열거 | 실제 존재하는 허용 날짜를 선택하는 D1 보완 후 해당 과거 원본 삭제. 현재 생산 누락과 의도적 과거 폐기를 구별 |
| 반전 `completed_bars()` | 당일 machine 가격 보고서와 `runtime/shared_ws_completed_bars/*/*/*.json` | shared cache 파일을 먼저 열고 내부 날짜를 거르는 실제 시세 읽기 | 파일 선택을 열기 전에 제한. 필요한 현재 가격 보고서·9월 이후 원천은 유지 |
| DuckDB 역사 조회 CLI | analytics의 `date=*/*.parquet` 파일 | Parquet 실제 읽기이며 DB 일봉 원장과 별개. 현재 필수 소비는 확인되지 않음 | 옛 Parquet를 삭제 대상으로 분류하고 명시 날짜 파일만 등록. 분석 DB 본체는 삭제하지 않음 |
| 운영자 잠금/정책/모델 loader | 설정 JSON, override env, 승인/출처 hash, 모델 parameter | 설정 참조 자체는 원본 raw 읽기가 아님 | 기존 경로·값·내용·권한을 유지. 오래된 파일명 때문에 삭제·이관하지 않음 |
| KOSPI_ML scanner·EOD | DB 일봉 조회/저장 | DB 소비자 | 전부 이번 변경 대상에서 제외. DB 시세의 과거 기간은 파일 삭제를 막는 조건이 아님 |

### 초기 매수수량의 읽기 제한 검증

workspace의 `selected_initial_quantity_env(current.json, 2026-10-07)`를 읽기 전용으로 실행했다. 원본 pipeline/post-sell/AI raw/Parquet 접근 및 외부 연결·subprocess를 차단한 상태에서 **PASS**였고, 프로젝트 data의 읽기 대상은 다음 **8개 파일**뿐이었다.

- `data/runtime/initial_quantity/`: current, 현재 runtime 정책, 부모 baseline 정책, parent-current의 4개 파일.
- `data/report/initial_entry_quantity_type_policy/review_following_final_2026-09-26/`: stage, replay, candidate, following-bars의 4개 파일.

근거: [읽기 경로와 consumer hash](../../tmp/pre-september-source-use-audit-20261007/initial-quantity-original-raw-read-verification.json). 이는 해당 workspace validator의 결과이며 전체 자동화·선택 릴리스·실제 PID의 모든 동적 접근을 증명하지 않는다. 보고서에 기록된 347개 과거 진입 행은 **보존 지시 대상**이며 삭제량에서 제외한다.

### 파일별 판정 규칙

1. `delete_unused_raw`: 해당 원본을 실제로 여는 현행 reader가 없고 보존 지시 대상이 아닌 과거 raw/사본. **백업·복원·옛 보고서 재현 가능성과 무관하게 삭제 가능 대상으로 기록한다.**
2. `delete_after_reader_fix`: 실제 reader가 있다. 정확한 함수·파일·기간·사용 이유와 필요한 읽기 제한/관측 날짜 보완을 명시하고 해당 보완 후 삭제한다. 관련 없는 DB·정책 이관을 추가하지 않는다.
3. `keep_reference_report`: 초기 매수수량 및 현행 검증이 읽는 연결 보고서·후행 증빙. 과거 행을 포함해 원래 bytes/hash를 유지하며 삭제 대상과 분리한다.
4. `keep_current_policy`: 정책·잠금·parameter·승인·현재 custody. 기존 위치와 기능을 유지한다.
5. `excluded_database`: DB 본체·원장·전용 dump. 파일 시스템에서 발견되어도 raw 삭제기로 처리하지 않는다.
6. `needs_consumer_classification`: 동적 reader가 불명확한 항목. 확인할 함수와 분류 종료 기준을 명시한다. 단순 경로 문자열·미복원·백업 미확인을 실제 raw 의존으로 대체하지 않는다.

## 3. 조사된 물리 범위와 보존 예외

| 파일 범위 | 조사 시점 확인량 | 계획 |
|---|---:|---|
| 8월 analytics Parquet | 53파일·8.897GiB·7,132,536행 | 과거 이벤트/metric/post-sell 파일 partition과 불필요한 파일 index 참조 정리 |
| 9월 이전 source-quality 파일 | 83파일·3.011GiB, 대부분 raw exclusion 복구 사본 | 원본 payload·복구 사본 삭제. 현재 격리 계약에 필요한 원천 없는 metadata 유지 |
| pre-August source archive | `data-through-2026-07-31.tar.zst`·4.162GiB | 해당 raw archive 삭제. 대체 raw 백업을 만들지 않음 |
| 날짜 파일의 나머지 원천/독립 사본 | 날짜 파일 전체 9,218개·18.660GiB 안에 포함 | 실제 raw와 보존 보고서·설정·현재 custody를 분류한 뒤 raw만 삭제 |
| 9월 폴더의 혼합 분봉 cache | 882파일·3.830GiB; 9월 이전 19,720,433행 + 9월 이후 4,873,972행 | 생성일은 기간 근거가 아님. 소비되지 않는 세대는 전체 삭제 대상으로 분류하고 필요한 현재 행은 같은 소비자 계약으로 분리 |
| 무일자 CSV·연구 fact·역사 로그 | 별도 payload clock census | 실제 과거 원천 여부 확인 후 분류. 현재 열린 로그·주문 영수증 보존 |
| 초기 매수수량 연결 보고서·기존 정책/잠금 | 현재 validator 8개 파일, 잠금 24개 합계 75,676바이트, 분할 주문 기준 657바이트 | **삭제 예외.** 과거 날짜·거래 행이 있어도 사용 중인 연결 보고서와 설정 유지 |
| DB/DB 일봉/원장/DB 전용 backup | 과거 별도 조사 존재 | **범위 제외. 건수·저장량을 삭제량에 포함하지 않음** |

기존 **22.490GiB**는 날짜 파일과 혼합 cache의 조사 범위다. 현재 보고서·정책·혼합 현재 행이 들어 있어 확정 회수량이 아니다. 보존 예외를 제외한 파일 manifest와 삭제 후 `df`로 회수량을 판정한다.

raw 백업·사본의 조사 위치는 storage/runtime archives, release mount/checkout backups, worktrees, project tmp와 프로젝트 관련 `/tmp`다. 코드·문서·정책만 담긴 archive와 DB 전용 dump는 raw archive로 분류하지 않는다. 필요한 연결 보고서가 archive 안에만 있는 경우 그 보고서의 정확한 내용·hash를 원래 소비자가 요구하는 경로에 유지한 뒤 raw archive를 제거한다. 원본 raw를 보존하는 새 archive는 만들지 않는다.

## 4. 구현·삭제 순서

### D0 — 파일 manifest와 보존 목록 확정

- 기존 `src/engine/automation` 또는 `src/engine/infrastructure`에서 파일형 source-retirement 소유자를 구현한다. engine root에 새 모듈을 만들지 않는다.
- 실제 경로/realpath/inode·논리 기간·파일 종류·reader 함수·사용 이유·위 분류·예상 할당량을 기록한다. 초기 수량의 연결 보고서와 정책·잠금·DB 제외 목록을 삭제 후보보다 먼저 적용한다.
- 파생 보고서의 path/hash를 원본 open으로 단정하지 않는다. 현재 설정/보고서의 완전한 의존성 읽기에서 원본을 실제로 여는지 확인한다.
- 삭제 미대상 DB를 새로 조회·변경하지 않는다. 과거 조사 결과는 참고 기록이며 DB 전환의 실행 owner가 아니다.

### D1 — 실제 원천 reader 보완

- 보유·청산은 존재하는 snapshot/projection·post-sell 파일/manifest 날짜를 먼저 발견하고 허용 범위의 날짜 합집합으로 집계한다. 6/5 이후 매 평일을 강제하거나 9/1로 고정 시작일만 치환하지 않는다.
- 실제 관측 시작/끝·읽은 날짜·분모를 기록한다. gzip 중복, 파일 파손, target 필수 입력·COMPLETED census/producer 선언의 누락은 실제 source gap으로 유지한다. 명시 폐기일과 의무 없는 옛 공백은 재처리/복구 대상으로 만들지 않는다.
- shared WS cache·Parquet·원천 discovery는 파일을 열기 전에 허용 기간을 선택한다. 삭제 대상 원본을 보고서에서 재생성하거나 DB/API로 자동 복원하는 **파일 생산 경로**만 제한한다. DB 저장 창·scanner 지표·Kiwoom 프로토콜 변경을 이번 작업에 포함하지 않는다.
- 초기 매수수량은 기존 report 기반 검증과 정상 parent 적용일 이후 refresh를 유지한다. 삭제한 6~8월 seed를 다시 계산하지 않고 원본이 없는 상태에서 현행 검증이 통과하는지 확인한다.

### D2 — 연결 보고서·정책·잠금 보존

- 현재/부모 initial quantity 정책, parent-current, stage/replay/candidate/following-bars 및 검증이 추가로 읽는 관련 보고서의 존재·bytes/hash를 보존한다. 거래 347행 삭제, 보고서 재작성, seed/report 삭제용 adoption receipt는 계획에서 제거한다.
- 기존 정책·모델 parameter·운영자 잠금·승인·종료 조건은 기존 파일에 유지한다. 날짜 때문에 이동·재승인·재학습하거나 제한을 종료하지 않는다.
- 실제 source reader 변경으로 준비/소비자 계약이 바뀐 경우에만 해당 native 검증/PREOPEN 재준비를 수행한다. 보고서만 읽는 정책에 새 배포·승계 조건을 만들지 않는다.

### D3 — 파일 원본·압축·사본·백업 삭제

- `delete_unused_raw`는 복원 가능성을 요구하지 않고 삭제 대상으로 확정한다. `delete_after_reader_fix`는 해당 reader 보완을 확인한 뒤 삭제한다. 다른 class의 수정 완료를 공통 선행 조건으로 묶지 않는다.
- 파일명/mtime 대신 payload clock으로 혼합 데이터를 분류한다. 보존 목록에 있는 보고서의 내부 과거 행은 변경하지 않는다. 현재 원천·정책 출처 날짜를 과거 raw로 오인하지 않는다.
- 원본/gzip/Parquet/raw exclusion backup/archive/독립 checkout/temp 사본을 연결해 삭제하고 같은 raw의 다른 인코딩을 남기지 않는다. 복구용 새 백업·복원 테스트를 요구하지 않는다.

### D4 — 재유입 방지와 종료 검증

- release/worktree의 현재 체크아웃에서 실제 raw 사본을 제거하고 이후 checkout/export가 폐기 원본을 자동으로 재배치하지 않도록 한다. 정책·잠금·보고서 파일은 보존한다.
- Git 과거 객체·원격 clone의 복원 가능 여부나 history 재작성 완료를 **현재 파일 삭제의 선행 조건으로 두지 않는다.** 작업트리 삭제를 모든 Git 객체의 파기로 확대해 주장하지 않는다.
- 삭제 manifest의 실제 파일/기간/분류/결과와 확보 용량을 확인한다. 사용 중인 보고서·정책·잠금·현재 원천의 유실 0, 삭제 대상 raw 백업 잔존 0을 각각 기록한다. DB 삭제/maintenance나 원본 복원을 실행하지 않는다.

## 5. 샘플·회귀 검증과 수용 기준

| 검증 | 수용 기준 |
|---|---|
| raw 실제 의존성 | 실제 원본 open·gzip·Parquet·hash/exists 검증을 구분해 기록. path 문자열만 있는 보고서 참조를 raw 의존으로 표시하지 않음 |
| 미사용 원본 삭제 | 보고서/정책을 그대로 둔 상태에서 과거 raw 읽기가 없으면 복원/백업 여부와 관계없이 삭제 가능으로 분류 |
| 초기 매수수량 | 원본 raw 읽기 차단 상태에서 현행 native 검증 PASS. 연결 8파일 및 필요한 추가 보고서의 원래 bytes/hash 유지. 내부 347개 옛 거래 행 유지 |
| DB 범위 제외 | manifest에 DB 본체·volume·WAL·DB 전용 dump 삭제 후보 0. SQL 삭제/maintenance·scanner/EOD 변경 0 |
| 정책·잠금 | 값·shape·quantity·대기·제한·veto·owner·승인·명시 종료 조건 동일. 기존 위치 유지 |
| 날짜/관측 | KST 9/1 경계, 실제 존재 날짜 합집합, 월 전환 누적, gzip 중복·파손·target/census 누락 검사. 폐기 날짜 재현 요구 0 |
| 현재 반전 | 현재 9월 이후 source/라벨/분모/기계·보조 12+12셀 유지. 삭제 때문에 EV·최소 표본/일수·holdout 등 새 채택 문턱을 추가하지 않음 |
| 파일/백업 삭제 | 원본·압축·격리·archive·사본별 결과 및 보존 예외 검사. 실제 삭제량과 조사 상한 구별. 새 raw 백업·복원 절차 없음 |
| 다음 장후/기동 | 변경된 reader의 정상 장후 계산·native 종료·필요한 PREOPEN·실제 소비를 각각 검증. retired 날짜 원본 복원은 종료 조건이 아님 |

## 6. 이번 보완과 검증 범위

원본 raw 접근을 타이밍·초기 수량·보유/청산·shared WS cache·Parquet·설정 loader별로 재점검했다. 초기 수량 validator의 직접 읽기 제한 검증은 PASS이며 실제 data read 8파일/원본 raw 0이다. **보고서 보존·DB 제외·기존 정책/잠금 유지·미사용 원본의 복원 여부와 무관한 삭제 가능 분류**를 전체 단계와 수용 기준에 반영했다.

최초 계획 보완은 문서와 읽기 전용 검증으로 마감했다. 이후 승인된 단발 실행은 아래 §7의 코드 리뷰·물리 삭제·native 검증으로 구분한다. 정규 reader/예약 자동화 변경 시에는 당일 실행 owner와 운영 문서를 함께 갱신한다.

## 7. 승인된 단발 삭제 실행 — 10/7 10:27 KST

실행 근거는 사용자의 디스크 확보 지시다. D3의 class별 독립 실행에 따라 현재 소비되지 않는 원천부터 제거했다. **미사용 원천 정리는 완료했으며 D1의 정규 reader 전환·배포까지 완료한 것으로 표시하지 않는다.** [실행·코드 리뷰 기록](../audits/pre-september-source-data-retirement-execution-2026-10-07.md), [물리 삭제 결과](../../data/report/pre_september_source_retirement/2026-10-07/execution-result.json).

- 물리 파일 **3,102개 / 할당량 20.507GiB** 삭제. Archive의 모델·설정·보고서 등 nonraw 8,112개 / 2.430GiB는 별도 보존했으며 raw 복구 사본을 만들지 않았다.
- 실제 파일시스템 여유 공간은 **14.625 → 32.412GiB**, 확보량 **17.787GiB**, `df` 사용률은 **90% → 78%**다. 삭제 할당량과 실제 여유 증가는 구분한다. 실행 중 현재 runtime 원천 쓰기도 계속됐다.
- Parquet 53개, 미사용 분봉 cache 882개, 8월 격리 raw gzip 19개, 기존 pre-August raw archive 1개, 위젯 분봉 cache 1,933개·관측 114개, sentinel cache 40개, 과거 pipeline summary 원천 60개를 삭제했다. Manifest metadata·보고서·설정은 원천 파일과 구분해 유지했다.
- 삭제기의 소유 위치는 [automation/source_data_retirement.py](../../src/engine/automation/source_data_retirement.py)다. 검토한 manifest만 `--apply`로 처리하며 기본은 dry-run이다. payload clock/consumer receipt, 내용 hash·inode·크기·mtime/ctime, symlink/hardlink·열린 FD·DB 경계·보존 hash를 확인한다. 새 cron/정기 purge/거래 runtime 연결을 만들지 않았다.
- 보존 대상 **3,101개 hash 일치**, 유실 0. 초기 수량은 원본 raw 읽기 차단 상태에서 **8파일 / raw 0 / native PASS**, 연결 replay 387행 중 9월 이전 **347행도 그대로 유지**했다. 현재 PID bootstrap PASS, PID/start_ticks/cwd·선택 릴리스·기계/보조 정책·기존 finalization chain/snapshot hash가 유지됐다.
- D1 보완이 필요한 실제 post-sell raw **102파일**과 동적 sim 소비를 확정하지 않은 **42파일**, 총 **6.223MiB**는 보존했다. reader 수정·실제 보고서 소비자 전환을 확인한 뒤 별도로 삭제한다. [남은 파일과 종료 조건](../../data/report/pre_september_source_retirement/2026-10-07/retained-reader-dependent-raw.json).
- manual custody·정책·보고서와 response cache가 섞인 `widget-dedicated-data-before.tar.gz` 53.656MiB도 보존했다. 해당 archive를 raw-only로 선언하거나 현재 보존 계약 없이 삭제하지 않았다. 삭제 확정 후보의 원본/사본 잔존은 0이며, **조사된 모든 raw 백업 잔존 0을 주장하지 않는다.**
- D4: 삭제한 raw 데이터는 Git의 현재 추적 대상이 아니므로 통상 checkout/export가 이 집합을 다시 공급하지 않는다. 현재 자동 writer의 날짜 선택·9/29 refresh 시작은 유지했으며, 모든 역사 CLI의 생산 차단을 구현했다거나 Git 과거 객체·원격 사본을 파기했다고 주장하지 않는다.

현재 체크리스트와 sealed 장후/PREOPEN 원천은 원래 bytes/hash를 보존했다. 이번 단발 수동 삭제의 실행 결과는 본 절과 실행 manifest로 종결하며, 정규 reader 전환/자동화 등록은 미실행 상태다. DB 접근·provider/AI 호출·주문·정책/threshold 변경·봇 재기동은 모두 0이다. Permission-denied PID의 FD 조회는 `unobservable`로 남기며 전체 PID 관찰 성공으로 대체하지 않는다.
