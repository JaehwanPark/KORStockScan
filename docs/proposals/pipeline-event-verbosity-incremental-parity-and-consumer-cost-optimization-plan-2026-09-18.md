# Pipeline event verbosity 정보 보존·증분 평가·소비자 비용 최적화 계획

작성일: 2026-09-18 KST

상태: PV0–PV6 구현·반복 리뷰·영향 범위 회귀 완료. 커밋·배포·제한 갱신 receipt 및 잔여 자연 OPEN은 [owning review](../audit-reports/2026-09-18-pipeline-event-verbosity-incremental-review.md)를 따른다. 진단 PASS는 매매 정책·EV 개선이 아니다.

## 1. 목표와 판단 기준

`src.engine.pipeline_event_verbosity_report`를 독립 매매 튜너로 확장하지 않는다. 기존 원천과 요약의 정보 보존을 수리하고, 반복 평가 비용을 줄이며, 실제 후행 소비자의 비용 감소가 있는 범위에서만 유지한다.

순서는 **기존 증거·소비자 확인 → 최초 불일치 수리 → 증분 평가 → 후행 상태 인계 → 제한 검증 → 운영 효용 판정·정리**다. 원본을 생략해 절감하는 대신 기존 raw를 보존하면서 중복 읽기·파싱·요약 재계산을 줄인다.

성과를 다음처럼 분리한다.

| 축 | 완료·성과 판단 |
| --- | --- |
| 원천 보존 | 동일 날짜·scope·완료 시간창에서 count, stage, blocker, identity 보존. 누락·중복·미성숙을 구분 |
| 계산 최적화 | unchanged 입력은 원본·요약 본문 재스캔 없이 검증된 결과 재사용; append는 미처리 완전한 행만 처리 |
| 소비자 효과 | 실제 consumer의 같은 결과를 유지하며 처리 bytes/시간·작업량 감소. 보고서 자체의 속도와 별도 측정 |
| 매매 EV | 본 작업의 primary metric이 아님. 모델 ΔEV·실제 순익·인과적 개선을 생성하거나 주장하지 않음 |

원칙 owner는 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 owner는 [현재 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)다. 캐시·incremental·source semantic key의 공통 원칙은 [기존 장후 계산 최적화 계획](postclose-computation-optimization-implementation-plan-2026-09-17.md)을 재사용한다. 이 계획의 PV0–PV6은 구현 묶음이며 native 추천 ID나 새로운 실행 예약이 아니다.

## 2. 확인된 기준과 미확정 사항

- 선택 배포본 `fa359254297ad6dd24f12101efaa77af39268568`의 Main wrapper에서 Swing/Lab 분기를 건너뛰면 verbosity 단계가 다음 기본 ON 작업이다. wrapper의 정기 cron은 현행 inventory 기준 미등록이며, 코드 ON을 자연 실행 예약으로 간주하지 않는다.
- 9/15는 원본 대상148,100건/producer146,879건, 완료 공통 시간창에서도1,145건 불일치다.
- 9/16은 원본 대상189,150건/producer188,010건, 양쪽 마지막159건을 제외한 완료 공통 시간창에서도1,140건 불일치다. `v2_shadow_parity_fail`, identity false, flush 기한 경과다. 단순 최근 flush 대기로 분류하지 않는다.
- 9/16 raw6,650,275,819bytes, potential suppressible0건/0bytes, 실제 raw 절감0, 추가 producer 요약63,786,216bytes다. latency improvement는 null이고 경제 효과는 `not_measured`다.
- 9/17은 verbosity 실행 전 resource guard300초 대기로 종료했다. 마지막 가용 메모리3,923.6MB<4,096MB, 전체 wrapper FAIL이며 해당일 보고서는 없다. producer 요약153,062건은 존재하지만 parity PASS는 아니다.
- 현행 CLI의 `status=success`/exit0은 분석 완료를 뜻하며 parity PASS와 다르다. EV reader는 missing을 표시하나 workorder builder는 보고서 부재 시 이 source의 지시를 만들지 않는다. 지시0을 결함 해결로 해석하면 안 된다.
- 현재 보고서는 raw volume 산출을 위해 전체 원본을 읽고, 별도로 raw-derived parity 요약을 갱신한다. 기존 summary checkpoint의 incremental 기능을 사용하더라도 volume 경로의 반복 전체 읽기가 남는다.
- 실제 누락의 최초 원인과 최신 source에서의 자연 재발 여부는 미확정이다. 특정 PID·종료 방식·설정·버그를 원인으로 단정하지 않고 PV0/PV1에서 입증한다.

근거: [9/16 보고서](../../data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-09-16.md), [9/17 실제 로그](../../logs/threshold_cycle_postclose_cron.log), [현행 inventory](../audit-reports/2026-09-05-postclose-work-inventory.md), [wrapper](../../deploy/run_threshold_cycle_postclose.sh).

## 3. 범위·보존·코드 소유

### 3.1 기존 모듈 중심 변경 지도

| Owner | 담당 변경 |
| --- | --- |
| `src/utils/pipeline_event_logger.py` | raw 성공→동일 payload producer 전달, mode 전환·종료·오류 인계와 분모 보존 |
| `src/engine/pipeline_event_summary.py` | 기존 raw checkpoint·요약 profile·producer flush·manifest/identity의 재현성과 증분 집계 |
| `src/engine/pipeline_event_verbosity_report.py` | 반복 full scan 제거, 안정된 source 검증·재사용, 진단 상태·효용 출력 |
| `deploy/run_threshold_cycle_postclose.sh` | scoped run/reuse/defer, resource 대기 상태와 후행 인계. 기존 전체 guard는 보존 |
| `threshold_cycle_ev_report.py`, `build_code_improvement_workorder.py` | missing/deferred/invalid/parity failure 인계, 동일 결손의 중복 작업지시 방지 |
| trigger/controller/verifier 및 tower/checklist의 기존 reader | 실제 필요한 경로만 수정. source/date/hash·strict closure 보존 |
| `src/tests/test_pipeline_event_logger.py`, `test_pipeline_event_summary.py`, `test_pipeline_event_verbosity_report.py`와 affected consumer tests | 운영 producer부터 소비자까지 회귀 |

새 service·DB·collector·독립 report producer·중복 요약·일반 캐시 framework·engine-root 모듈을 만들지 않는다. 기존 manifest에 필요한 집계와 provenance만 추가한다. 기존 profile의 역할을 확인하고 중복 순회를 합치되 다른 reader의 sample/diagnostic schema는 보존한다.

### 3.2 반드시 보존할 계약

- 원 request/response, raw candidate/attempt/submit/fill/terminal, 비용·custody·reserve·operator override 및 clean-baseline 경계.
- threshold family·주문·안전·source-quality/provenance를 담은 raw. 집계 identity 일치는 개별 순서·payload 보존이나 raw 대체 권한이 아니다.
- `runtime_effect=false`, `allowed_runtime_apply=false`, `raw_suppression_enabled=false`. 옛 `mode=suppress`가 원본 생략 권한을 갖지 않는다.
- broker/account/order/price freshness/quantity/cooldown/provider/bot·hard/protect/emergency guard. resource floor/timeout을 단순 완화해 비용 문제를 숨기지 않는다.
- 실행 중 source/snapshot과 immutable release. 작업본 변경은 관련 clean successor에서 검증·배포한다.

`shadow`는 기존 producer-summary 관측 mode의 명칭이다. 새로운 매매 shadow/canary나 정책 탐색을 뜻하지 않는다. 이번 범위에서 Kiwoom 요청·응답·FID·주문 프로토콜을 수정할 필요가 없다. 필요해지면 기존 공식 reference gate와 권한을 별도로 적용한다.

## 4. PV0 — 계약과 최초 불일치 위치 확정

1. 기존 변경·회귀·9/15·9/16 보고서 및 9/17 manifest를 먼저 확인한다. 완료된 flush/hash/identity 구현을 무조건 다시 작성하지 않는다.
2. raw writer→producer admission→buffer→flush batch→summary append→manifest→health→reader의 호출 지도를 작성한다. raw를 쓰는 모든 실제 caller에 요약 mode가 적용되는지, 일부 writer가 OFF/다른 세대인지 분리한다.
3. 날짜·대상 stage·reason label·timezone·identity canonicalization을 양쪽에서 대사한다. KRX/NXT/SOR·프리/정규/애프터를 원천 scope대로 보존한다. 매매 route 모델의 지원 범위를 이 운영 count 비교에 새로 강제하지 않는다.
4. 기존 mismatch bucket·manifest·bounded sample부터 조사한다. 전체 raw의 재생성 대신 해당 날짜/분/stage/PID의 근거로 경계를 좁힌다. JSONL은 stat 후 읽으며 큰 파일의 전체 materialization은 금지한다.
5. 정규 종료, 강제 종료, mode 교체, 병렬 writer, publish 실패, retry 중복, summary queue overflow의 관측·미관측을 구분한다. 정상 함수 반환을 durable publication과 혼동하지 않는다.
6. 요약을 실제 읽는 consumer의 함수·schema·목적을 확인한다. 요약 본문 소비와 단순 report status 소비를 분리한다. 아직 consumer가 없는 요약을 미래 성능 효과로 계산하지 않는다.

산출: 하나의 owning review에 mismatch boundary·affected denominator·support scope·repair owner·closure test를 기록한다. 과거 불일치와 미래 생성 계약 수리 여부를 별도 열로 둔다. 원인 미확정이면 정확한 결손으로 남기며 producer 전체를 무조건 unsupported로 만들지 않는다.

## 5. PV1 — producer 분모·publication 수리

PV0에서 재현한 결함만 기존 writer/compactor 안에서 수리한다.

1. raw append 성공 payload와 producer가 hash하는 payload가 같음을 검증한다. summary 실패는 raw·threshold companion 기록을 중단시키지 않는다.
2. admission/rejection·buffer pending·publish 완료의 수량을 구분한다. 기존 telemetry로 원인을 알 수 있으면 재사용하고, 불가능한 필드만 기존 manifest/health에 추가한다. PID만으로 세대를 식별하지 않고 producer/parser/scope 계약을 결속한다.
3. 여러 writer의 append/manifest 갱신을 기존 generation lock 아래 대사한다. publish 중 장애·재시도에서 유실과 이중 누적을 모두 막는다. 이미 durable한 row를 다시 더하지 않는 계약을 검증한다.
4. 현재 async flush의 hot-path lock 분리와 bounded buffer를 유지한다. mode 전환 시 old compactor의 미발행 batch 인계, 종료 drain 및 retry 상태를 검증한다. raw writer lock 안에서 큰 disk flush를 수행하지 않는다.
5. 강제 종료에서 메모리 미발행분의 완전 보존을 보장할 수 없다면 summary partial을 드러내고 raw를 authoritative fallback으로 유지한다. 신규 durable queue를 만들거나 메모리 상태만으로 complete를 발급하지 않는다.
6. manifest/summary의 불일치·손상은 stale/invalid로 판정한다. 기존 valid 세대를 먼저 삭제하지 않고 validated successor를 atomic publication하는 방향으로 보완한다. 잘못된 manifest 때문에 raw를 자동 전수 재스캔하거나 복구 완료로 보고하지 않는다.

Closure: 기존 운영 logger가 만든 입력에서 완전한 publish는 raw 대상count·stage·blocker·identity와 일치한다. 지원된 정상 경로에서 실제 PASS를 만들고, 장애 경로는 raw 보존과 pending/partial/invalid·정확한 owner를 반환한다. 과거 summary 결손은 raw의 매매 원천 품질 실패로 확대하지 않는다.

## 6. PV2 — raw volume·parity의 증분 계산과 재사용

### 6.1 같은 한 번의 원천 순회에서 집계

기존 `update_and_load_pipeline_event_summaries`의 checkpoint 경로에 report가 필요한 raw line/byte·stage·eligible/suppressible/lossless·invalid/tail·coverage·identity 집계를 함께 결속한다. `_line_count_and_stage_bytes`가 같은 prefix를 다시 읽지 않게 한다.

- 원본 총bytes와 대상bytes는 같은 encoding/행 단위 정의를 유지한다. 압축 저장bytes와 비압축 streambytes를 분리한다.
- incomplete 마지막 행은 처리 offset을 넘기지 않고 다음 append에서 한 번만 포함한다.
- 기존 `default`와 `producer_parity`는 stage/detail 계약이 다르다. default3,089rows 같은 값을 producer153,062events의 분모로 바꾸지 않는다. 전체 payload를 요구하는 reader는 counts-only 요약으로 대체하지 않는다.
- 최초 유효 집계가 없는 날짜는 bootstrap 필요를 명시한다. 자동 lookback 전수 backfill을 금지하고, 승인된 source-day·기존 cache·제한 streaming으로 처리한다. bootstrap을 미리 완료했다고 가정하지 않는다.

### 6.2 source별 동작 계약

| 입력 변화 | 처리와 기대되는 읽기 |
| --- | --- |
| 동일 frozen source·동일 계약 | native manifest·본문 integrity receipt 확인 후 reuse. raw/summary 본문 전체 순회0 |
| 같은 generation의 append | 원본 last-good byte offset 이후만 처리. producer의 새 완전한 rows/batches만 집계 |
| incomplete tail 완성 | tail 시작 offset에서 재개. 해당 행을 정확히 한 번 더함 |
| 축소·교체·과거 정정 | generation/정정 계약에 따른 invalidation. silent reuse 금지; 해당 날짜/범위의 제한 복구 또는 explicit blocker |
| parser/stage/reason/identity version 변화 | 의미가 달라진 요약만 invalidation. 다른 profile/owner까지 무조건 재생성하지 않음 |
| 압축 archive | 기존 검증된 summary/압축 provenance를 사용. gzip seek를 상수 비용 append로 주장하지 않음 |
| 요약/manifest 손상 | invalid/miss와 owner/closure test. 이전 PASS·깨진 집계값 재사용 금지 |

재사용 key는 target date, native source generation/원 snapshot hash, 처리 offset·complete cutoff, schema/parser/stage/reason/identity 계약, producer generation·manifest/본문 binding, report 구현 hash를 포함한다. source path/inode/size/mtime만으로 과거 in-place 정정 부재를 증명하지 않는다. 정정 식별 계약이 없는 mutable source는 reuse 지원 범위를 제한하고 그 이유를 노출한다.


재사용 무결성은 대형 파일을 읽지 않고 hash가 검증됐다고 주장하는 방식으로 구현하지 않는다. 항상 읽는 소형 checkpoint/report 본문은 digest를 검증하고, 대형 source prefix는 기존 owner의 검증된 append-only/sealed-generation 계약이 있는 경우에만 재사용한다. 그 계약이 없는 경로는 content 검증 필요 또는 unsupported fast-path로 드러내되 정상 streaming 계산을 지원한다. 동일 size/mtime을 강제로 유지한 정정까지 metadata-only 검사로 발견했다고 보고하지 않는다. 기존 owner에 sealing이 없으면 이 입력에서는 본문 재읽기0 acceptance를 주장하지 않고 지원 경계를 먼저 확정한다.

### 6.3 완료 시간창과 memory

공통 완료 watermark 이전과 tail을 별도 집계한다. emission 시간과 실제 append/publish 시각이 다르므로 late-arrival이 기존 완료 bucket을 바꾸면 해당 bucket을 갱신한다. watermark 이후 미발행 tail 때문에 완료 prefix 실패를 숨기지 않는다.

요약 소비도 기존 reader의 streaming/chunk 경로를 우선 사용한다. report에는 전체 rows를 담지 않고 stage/blocker/identity totals와 bounded mismatch preview만 담는다. hash multiset 검증을 샘플로 대체하지 않는다. 같은 generation의 증분 결과는 통제 입력에서 단회 재계산 결과와 의미가 같아야 한다.

## 7. PV3 — 운영 상태·실제 consumer·resource 인계

기존 report에 분석 상태, 실행 상태, source generation, complete watermark, blocker, owner, next action, closure test를 분리한다. operational pending을 no-edge/표본부족으로 바꾸지 않는다.

| 상태 | 의미·후행 처리 |
| --- | --- |
| `parity_pass` | 선언된 source/scope/완료창만 보존 검증 완료. raw 생략·매매 승격 권한 없음 |
| `no_eligible_events` | 유효 원천·coverage 안에서 실제 대상0. 파일 부재/휴장 비대상과 별도 |
| `pending_flush` | 지원된 flush 기한 안의 미발행분. 완료 prefix 판정과 기한을 보존 |
| `partial_coverage` / `parity_fail` | writer/scope 또는 완료창 불일치. 실제 영향받는 요약 consumer만 fallback·수리 |
| `invalid_source` / `unsupported_scope` | 구체 계약 결손. null·blocker·owner·closure test 반환 |
| `resource_deferred` | 계산 전 resource guard 미충족. 분석 PASS 아님; 기존 원천·상태 보존 |
| `missing_report` | 해당일 보고서 없음. 의도적 defer/disabled/retired와 혼동 금지 |

기존 state 이름의 compatibility는 실제 reader가 필요한 경우만 유지한다. 공통 상태 framework를 새로 만들지 않는다. `--check-reusable`은 재사용 가능한 terminal이라는 뜻과 parity 성공을 구분하고, 현재 source binding·본문 integrity·마지막 실행 상태를 확인한다. mtime만 최신인 FAIL 산출물로 PASS를 재사용하지 않는다.

resource 처리는 먼저 PV2로 작업량을 줄인다. 다음으로 이 운영 진단의 대기 실패가 독립 경제성 작업을 중단시키는 필요성을 실제 dependency로 판단한다. **요약에 의존하지 않는 후행 작업은 scoped defer를 기록하고 계속할 수 있게 하는 것**을 목표로 하되 다음 조건을 모두 충족한다.

- 기존 global resource guard·raw source-quality·broker safety는 유지한다. 위험한 후행 계산을 guard 밖에서 실행하지 않는다.
- 보고서/기존 checkpoint에 `resource_deferred` 이유·source date/generation·owner·재확인 조건을 남긴다. 새 빈 success나 과거 PASS로 대체하지 않는다.
- verifier/controller는 이 상태를 explicit operations OPEN으로 소비한다. 필수 source가 없는데 전체 경제성/DONE/PREOPEN GREEN으로 발급하지 않는다. 기존 중단 세대 FAIL marker는 자동 삭제하지 않는다.
- EV/workorder/tower/checklist에 같은 native `order_pipeline_event_compaction_v2_shadow`의 disposition을 전달한다. unchanged source gap을 매 refresh마다 새 지시·provider review·full wrapper rerun으로 확대하지 않는다.

운영 문서/현재 checklist와 wrapper/trigger/controller/verifier의 계약 변경은 같은 구현 change set에서 갱신한다. 새로운 cron/timer나 추가 후행 실행을 설치하지 않는다.

## 8. PV4 — 제한 회귀·리뷰와 비용 검증

새 synthetic evaluator를 따로 만들지 않고 기존 운영 logger→저장/flush→report→consumer 경로를 사용한다.

필수 회귀는 다음 여덟 묶음이다.

1. 정상 단일/복수 writer에서 원본·요약의 count/stage/blocker/identity 일치와 raw 보존.
2. 종료 drain·mode 교체·publish 실패/retry·queue rejection에서 유실·중복·거짓 complete 방지.
3. unchanged reuse의 raw/summary 본문 전체 읽기0; append가 delta만 읽고 단회 집계와 동등함.
4. partial line·late event·KST 날짜경계·완료 watermark/tail의 정확한 포함·제외.
5. truncate/replacement/in-place correction·schema/hash 변경·손상/압축 입력의 invalidation과 bounded fallback.
6. raw 보호 대상·옛 suppress override·summary 장애가 주문/threshold/원천 기록을 바꾸지 않음.
7. missing/defer/parity fail의 EV→workorder→tower/checklist→verifier/controller 인계와 중복 recovery 차단. 유효 PASS와 정상0도 실제 계산해 소비함.
8. 실제 소비자가 바뀌는 경우 동일 frozen 입력·동일 반환 의미에서 baseline/successor 비교. 요약을 읽지 않는 consumer의 성능을 개선 실적으로 포함하지 않음.

성능 검증은 baseline1회/successor1회로 시작한다. unchanged·small append fixture의 읽기 bytes/count와 필요한 wall/CPU·peak memory만 측정한다. 실패·변동 원인이 있을 때만 좁게 반복한다. 전국 symbol/grid·장후 전체·과거 raw 전수 benchmark는 금지한다. 기존 timing의 submit p95/p99는 summary 호출 측정이며 broker 주문 지연 개선으로 보고하지 않는다.

고정된 임의 속도 향상률·EV floor를 만들지 않는다. **무변경 반복 전체 raw 읽기0**, **append delta 계산의 동등성**, **지원 입력의 명확한 상태 전이**를 구현 acceptance로 삼고 실제 wall/I/O 차이는 측정값 그대로 남긴다. 통제 회귀·자연 parity·실제 consumer 비용 효과를 별도 보고한다.

## 9. PV5 — 유지·통합·중단 판정과 누적 산출물 정리

| 실제 검증 결과 | 결정 |
| --- | --- |
| 원천 보존 PASS + 실제 consumer 비용 감소 | 기존 요약과 증분 진단 유지; metric은 운영 비용으로 한정 |
| 보존 PASS + 진단 reader만 존재/절감 없음 | standalone 반복 heavy 평가는 기존 품질/final summary의 가벼운 section으로 통합하는 방향. 별도 raw 재순회 중단 |
| consumer 없음 + 추가 producer 비용만 존재 | 필요한 instrumentation 사용처를 먼저 보존·이관한 뒤 불필요한 관측 mode/반복 평가 제거 검토. 새 consumer를 억지로 만들지 않음 |
| 보존 FAIL | affected summary를 authoritative 대체 입력으로 사용하지 않음. raw fallback과 기존 owner 수리 유지 |

정리는 구현·리뷰·소비자 전환 후 수행한다. 대상은 필요 없어지는 중복 parity/raw-derived scratch, 대체된 보고서 세대, 임시 benchmark 출력이며 파일별 path/realpath/hash/size·active process/FD/lock·current policy/receipt 참조를 manifest로 확인한다.

원본 raw·frozen source·order/custody/cost, 현재 report/manifest/checkpoint, 실제 적용/rollback provenance, immutable release와 다른 세션의 tracked source는 보존한다. summary가0건이라고 해당일 raw나 주문 원장을 지우지 않는다. 현재 소비자가 새 경로를 읽고 제거 경로를 재생성하지 않는 것까지 검증한다. retention 기간을 근거 없이 새로 정하지 않고 기존 승인된 보존 owner를 따른다.

## 10. PV6 — 구현 완료와 자연 OPEN·후속 실행

### 구현 완료 조건

- PV0에서 소비자와 support scope·first mismatch 경계를 확정했고, PV1의 미래 producer 계약이 기존 운영 경로 회귀로 검증됨.
- 유효 입력에서 실제 parity 계산·PASS/zero/pending/fail이 동작하며 모든 입력을 inactive/unsupported로 막는 구현이 아님.
- PV2 unchanged/append·정정/손상·세대/본문 검증과 동등성 회귀 완료.
- PV3 scoped resource/missing·후행 source/date/hash·단일 작업 owner·strict 상태가 일관됨.
- PV4 영향 범위 pytest/compile·shell 변경 시 bash-n/계약 tests·diff check·문서 parser 완료. 리뷰→수정→재리뷰에 미해결 in-scope 코드 결함0.
- PV5 유지·통합 결정과 승인된 정리의 consumer/보호 manifest가 확인됨. 실제 삭제는 별도 실행 증거로 보고.

### 자연 OPEN

다음 실제 영업일에 same-generation raw/producer summary의 완료창 parity, restart/crash를 포함한 실제 coverage 및 제한 운영 비용을 확인한다. 휴장/미유입은 자연 acceptance 비대상이며 미래 계약 구현을 중단하는 이유가 아니다. 과거9/15·9/16 summary 손실은 수리 가능성·복구 범위를 따로 명시한다.

다음 장전 정책은 기존 기계·compact·개별 주문 튜너의 owner가 준비한다. 이 진단의 parity PASS가 새 dated 매매 정책을 생성하거나 현재 정책을 승격하지 않는다. 전체 source-quality·경제성·PREOPEN/PID·자연 완료 손익 OPEN을 운영 비용 개선으로 닫지 않는다.

후속 구현 요청 시 PV0–PV6을 기존 변경 보존→구현→리뷰→보완→재검증 순서로 진행한다. 승인된 경우만 관련 commit/push·검증된 immutable successor 선택 및 영향받는 source-day의 제한 report/후행 refresh를 수행한다. 봇 재시작·주문·조기 PREOPEN 확정·resource/threshold/safety 완화·전체 장후 rerun은 실행하지 않는다. 최종 증거는 한 owning review와 제한 receipts에 모으며 중복 계획·OPEN·상시 producer를 생성하지 않는다.


## 11. 실행 지원 범위와 완료 기록

- 실제 본문 소비자는 BUY Funnel Sentinel의 optional blocker summary/producer exclusion evidence와 entry-split execution projection census다. EV/workorder/tower/checklist는 작은 진단 결과를 소비한다. 따라서 raw 및 두 summary profile/실행 projection을 보존하며 standalone heavy 반복 raw 재순회만 증분 순회·결과 재사용으로 교체한다.
- raw fast-path는 기존 logger의 `O_APPEND`·logical partition lock·regular-file owner 계약이 있는 입력, producer는 기존 generation lock·commit size ledger가 있는 append에 한정한다. in-place 수정의 ctime/mtime·inode/축소와 checkpoint digest·코드 계약 변경을 확인한다. hostile metadata restoration을 검출하거나 대형 raw prefix hash를 재검증했다고 주장하지 않는다. owner가 없는 mutable 입력은 streaming 계산을 지원하되 본문 읽기0 acceptance를 발급하지 않는다. gzip는 native archive의 고정 세대 metadata 변경을 탐지하며 최초 압축 stream 순회·재계산 비용을 상수 seek로 표시하지 않는다.
- native raw manifest에 volume과 compact bucket/stage count·전체 canonical payload SHA256 multiset 및 원래11개 partition dimension의 별도 SHA256 multiset을 보존한다. stock/전략/시장별 full source row/sample을 checkpoint에 중복 복사하지 않는다. payload·partition·count·stage·blocker와 완료 watermark를 모두 비교하며 이는 다른 consumer의 raw/sample/execution projection 대체 입력이 아니다.
- resource defer·missing·불일치는 동일 `order_pipeline_event_compaction_v2_shadow`와 기존 checklist code-workorder owner가 맡는다. defer만으로 provider/full-wrapper recovery를 반복하지 않는다. strict/controller는 operations OPEN을 허용 완료 warning으로 취급하지 않는다. 원래 chain FAIL과 타 축 OPEN은 유지한다.
- 과거9/16의12개 불일치 minute와 실제 SIGTERM/atexit drain 결함을 구분한다. 과거 각 row/PID의 종료 원인을 추정하지 않는다. 종료·handover·publish/retry의 미래 계약은 운영 producer 회귀로 검증하고, hard kill의 미발행 메모리는 raw fallback 및 parity failure/partial로 남긴다.
- 원천·주문·정책·현재 checkpoint/report·9/15/16 불일치 증거·rollback/immutable release는 삭제 대상이 아니다. 승인 범위 안에서 참조 없는 이번 구현의 중간 scratch만 보호 manifest 대사 후 정리한다. 근거 없는 새 retention을 도입하지 않는다.
