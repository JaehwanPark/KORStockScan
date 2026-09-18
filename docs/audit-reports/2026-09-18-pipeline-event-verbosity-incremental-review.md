# Pipeline event verbosity 원천·증분·후행 인계 구현 리뷰

작성일:2026-09-18 KST. 범위 owner는 [PV0–PV6 계획](../proposals/pipeline-event-verbosity-incremental-parity-and-consumer-cost-optimization-plan-2026-09-18.md)이다. 사용자 승인 범위는 구현·반복 리뷰/보완/검증·관련 commit/push·검증된 immutable successor 선택 및 제한 source-day 갱신이다. 봇 재시작·실주문·조기 PREOPEN·guard/threshold/provider/resource floor 완화·전체 장후 rerun은 수행하지 않는다.

실행 증거 owner:`tmp/pipeline-verbosity-incremental-20260918/`. 최종 SHA/root/test 수·실제 source-day 결과는 `validation.json`, `deployment.json`, `regeneration.json`, `consumer-closure.json`, `cleanup-receipt.json`을 따른다. 소스 테스트·선택 배포·실제 PID·자연 parity·운영 비용·매매 EV는 서로 다른 판정이다.

## 최초 불일치와 소비자

9/16 완료 공통 시간창에서도1,140건 불일치다. 압축된 두 기존 summary만 streaming 대사해12개 minute로 좁혔다. 상위08:36/202·13:17/201·11:17/176·15:20/131·16:16/124·14:13/107·11:16/50·15:19/44이며 promotion latency372·fast precheck280·runtime queue lag172·heavy completion94·heavy lag91이 주요 stage다.11개 PID health에는 rejected_summary_count가 없었다. 과거 summary의 row별 writer/종료 causal identity가 없으므로 이 숫자를 특정 PID/종료 원인으로 단정하지 않는다.9/15/16 원 불일치 증거는 보존한다.

재현 가능한 수리 경계는 기존 graceful self-SIGTERM이다. bot_main의 야간/flag 종료2곳과 sniper의 flag 종료1곳은 SIGTERM 기본 종료를 사용하지만 summary는 atexit에만 등록돼 있었다. 통제 child에서 raw1건은 보존되고 producer pending1건은 SIGTERM 종료 시 미발행으로 사라지는 것을 재현했다. 기존 guard 뒤·기존 SIGTERM 직전에 bounded drain을 호출해 통제 child의 raw/producer1:1을 확인했다. 임의 외부 SIGTERM/SIGKILL·concurrent 종료 이후 raw append·시스템 강제종료의 완전 보존을 주장하지 않으며 해당 경우는 raw authoritative fallback·partial/parity failure로 드러낸다. 실제 봇 종료/재시작을 실행한 증거가 아니다.

| 실제 consumer | 보존·변경 경계 |
| --- | --- |
| BUY Funnel Sentinel | default blocker summary와 producer upstream exclusion evidence는 유지한다. native optional summary가 invalid면 raw/cache fallback과 blocker/owner를 전달한다. attempt를 summary count로 재구성하지 않는다 |
| entry-split execution projection census | native producer stages·size commit·lossless execution identity 검사를 보존한다. counts-only checkpoint로 주문 원천을 바꾸지 않는다 |
| EV/workorder | exact-date 진단 상태·owner/closure를 전달한다. 동일 native order의 defer_evidence를 반복 implement_now/provider 작업으로 확대하지 않는다 |
| tower/checklist/strict/controller | direct diagnostic source hash/absence를 receipt에 결속한다. operations OPEN을 표시하고 full-chain DONE/PREOPEN GREEN으로 수용하지 않는다 |

## 구현·보완

- volume 집계를 기존 raw checkpoint 순회와 합쳐 volume 경로의 반복 full raw 순회를 제거했다. incomplete tail은 offset을 전진시키지 않으며 완성 시 한 번만 처리한다. late append·KST UTC emission의 분모/완료 watermark를 대사한다.
- native manifest에 volume과 compact bucket/stage count·전체 payload hash multiset·원래 partition dimensions hash multiset을 저장한다. raw/sample/execution projection은 보존하며 checkpoint/report에 전체 payload를 복제하지 않는다. append는 raw delta와 producer committed delta만 파싱하고 unchanged managed input은 raw/summary 본문을 읽지 않는다.
- source/parser/callback/volume-registry 계약·checkpoint/report digest·generation/offset·commit size·ctime/mtime 변경을 확인한다. managed O_APPEND/partition lock·producer generation lock과 sealed gzip owner 범위다. hostile metadata restoration 검출·대형 raw prefix hash 재검증을 주장하지 않는다. unmanaged source는 실제 streaming 계산을 지원하고 zero-read acceptance를 발급하지 않는다.
- stale rebuild는 valid 파일을 먼저 삭제하지 않고 staging→replacement→manifest publication한다. commit 실패 시 이전 정상 파일/receipt를 복구하며 crash 중간 generation mismatch는 invalid이다. summary append/manifest의 정상 실패는 rollback/retry하고 uncommitted producer suffix는 다음 정상 누적으로 은폐하지 않는다. batch file fsync 및 unique atomic manifest 임시파일을 사용한다.
- mode handover는 비동기 old owner를 종료 drain에 보존한다. 반복 실패 시 retiring1/current1의 bounded ownership을 유지하고 raw fallback을 사용한다. 한 owner의 실패가 다른 owner의 drain을 막지 않는다. retry/queue rejection·companion/raw 보존을 검증했다.
- 소형 input의 정정·교체·축소/손상·schema/hash/callback/계약 변경을 검증한다. 압축 전환/손상 generation은 explicit blocker이고 `--allow-bootstrap`의 승인된 단일 source-day streaming으로 실제 복구·PASS·reuse가 가능하다. 자동 lookback backfill은 없다.
- wrapper resource wait의 floor/timeout을 유지한다. 이 진단의 timeout은 resource_deferred·null parity를 쓰고 독립 후행 계산은 각각 기존 global guard를 계속 적용한다. 다른 source fail·기존 FAIL marker를 지우지 않는다.

## PV0–PV6 판정

| 항목 | 코드·통제 검증 | 자연/실제 잔여 |
| --- | --- | --- |
| PV0 | 실제 reader·scope·불일치 minute와 재현 가능한 SIGTERM 경계를 확정 | 과거1,140건의 row/PID 원인 미확정 |
| PV1 | 정상 운영 logger→raw/compactor publish의 parity PASS, handover/drain·장애/retry·size ledger 검증 | 다음 자연 restart/crash 포함 coverage·old source 불일치 |
| PV2 | unchanged0-body-read·append delta·단회 집계 동등성·tail/KST·generation/digest/압축/scoped repair | 실제 다음 source-day 완료창 parity 및 제한 비용 |
| PV3 | missing/defer/parity fail→동일 native owner→EV/workorder/tower/checklist/strict/controller OPEN | 기존 전체 chain·개별 경제성/PREOPEN의 타 축 OPEN 보존 |
| PV4 | 실제 운영 producer/후행 회귀와 baseline/final successor 좁은 비교·compile/shell/diff/parser | fixture를 자연 샘플/매매 성과로 바꾸지 않음 |
| PV5 | 실제 consumer가 존재하므로 native summary와 증분 진단 유지. 독립 heavy raw 반복은 중단 | 운영 input/report/checkpoint/불일치/rollback 증거 보존; 참조 없는 이번 scratch만 receipt 대사 후 삭제 |
| PV6 | 실행 가능한 미래 생성·평가·defer/복구·소비 계약 구현 | 실제 PID 소비·자연 parity·다음 영업일 economics는 별도 OPEN |

## 제한 비용 검증과 경제성 경계

`benchmark-baseline.json`과 `benchmark-successor-release.json`은 frozen 통제750→751건의 baseline1회/final successor1회다. 보고서와 기존 EV 진단 reader를 함께 호출하고 raw/summary/checkpoint bytes·wall/CPU·RSS·동일 반환 의미를 기록했다. source-semantic/gzip/handover 최종 보완으로 이전 draft successor 측정을 변경된 게시·계약 범위에서 좁게 갱신했으며 이 중간 측정을 신규 실적으로 중복 계산하지 않는다.

unchanged는 baseline raw1,793,140/summary451,360bytes에서 successor raw0/summary0이다. append는 baseline 전체 prefix 대신 새 raw2,391/producer summary897bytes만 파싱했다. checkpoint 읽기·fsync 비용은 남고 append wall 개선을 보장하지 않는다. baseline/successor의750/751건 parity 및 EV reader 반환은 동일하다. Sentinel/runtime/broker latency·실제 운영 처리량·매매 순익 개선으로 확장하지 않는다. 실제 numeric wall/CPU/RSS는 최종 receipt를 따른다.

9/18 휴장으로 raw가 없으며 이를 유효 대상0이나9/17 자연 검증 PASS로 대체하지 않는다. 다음 예정 유효 영업일9/21의 정책은 기존 기계·compact·개별 주문 튜너 owner가 준비한다. 이 진단은 신규 매매 정책/양수 ΔEV/실제 순익/인과적 개선을 생성하지 않는다. raw suppression은 false이고 runtime_effect/allowed_runtime_apply도 false다.

## 배포·제한 갱신·정리

실행 중 source와 독립 서비스 pin을 수정하지 않고 origin/main의 다른 세션 successor를 포함해 clean branch를 fast-forward push한다. canonical 관련 diff는3-way로 인계하고 다른 세션의 source/문서를 보존한다. immutable successor의 HEAD·src/deploy/restart.sh clean·shared path/source SHA·selector CAS·read-only router plan을 확인한다. 선택은 future invocation 전용이며 실제 Main PID 기동/소비를 합성하지 않는다.

승인된 단일9/17 source-day의 최초 volume/parity streaming bootstrap 및 필요한 작은 후행 갱신만 수행한다. 시행 여부·정확한 처리 bytes/시간·상태·현재 resource gate·전후 source generation·policy 보호는 regeneration/consumer receipt에 고정한다. 다른 개별 튜너/grid/collector/전국 symbol·raw lookback·provider/full wrapper를 실행하지 않는다. native strict 전체 상태가 FAIL이면 해당 원 owner/실제 blocker를 보존한다.

cleanup은 benchmark 통제 입력·중복 중간출력·완료 후 staging scratch만 대상으로 path/realpath/hash/size·active cwd/FD/lock·정책/receipt 참조를 확인한다. canonical raw/order/custody/cost/frozen input, 현재 summary/manifest/report,9/15/16 mismatch·실제 정책/rollback provenance와 immutable release는 보호한다. 삭제하지 않은 보호물과 실제 삭제수를 cleanup receipt에서 구분한다.


## 최종 실행 receipt

- 코드 commit/push:`2fca169c599122235dcc4e6507bdd8904f4af029`. origin/main의 cancel-wait 최종 재리뷰 `609f3dbb09a2e398f2d573dd939dea3a3f85e945`를 포함했다. 영향15개 테스트 파일1,068PASS, 마지막 게시 경계178PASS, 최신 base 영향254PASS다. 중복 테스트를 합산한 신규 건수로 표시하지 않는다. compile·bash-n·diff·링크·print-only parser 통과, 현재 code-workorder 실행 owner는1개다.
- 선택 root:`/home/ubuntu/KORStockScan-runtime-releases/pipeline-verbosity-incremental-reviewed-20260918`. HEAD·src/deploy/restart.sh clean·shared path·read-only router plan·selector CAS 통과. future invocation 전용이며 actual PID 소비는 false다. 실행 중 release/독립 서비스 pin·봇 재시작·주문·PREOPEN 확정은 변경하지 않았다.
- 9/17 최초 source-day bootstrap은 raw5,713,580,290bytes·producer52,891,450bytes를 처리해49.614초에 완료됐다. 전후 inode/size/mtime/ctime가 동일하다. raw 대상156,549/producer153,062이며 공통 완료창156,167/152,769다. 기존 완료창 손실이므로 `v2_shadow_parity_fail`을 유지한다. invalid identity rows0을 parity PASS로 바꾸지 않는다. 미래 수리 검증과 과거 입력의 손실을 분리한다.
- EV는 작은 pipeline 진단 section만 갱신했고 다른 경제 section의 canonical JSON SHA가 동일함을 확인했다. 기존 JSON-only workorder builder·runtime approval summary·tower·next checklist를 갱신했다. `order_pipeline_event_compaction_v2_shadow`는1개·`defer_evidence`이며 source date·구현 상태를 보존했다. 원래 runtime-gap owner 보고서는 as-of 재사용했고 provider review는 수행하지 않았다.
- 최종 `--require-summary-handoff` native strict는 **FAIL**이다. low-price tuning hash/schema/target/profile/authority, machine timing 적용 원천 FileNotFound, 원래 FAIL marker·predecessor와 Swing 잔여가 원 owner에 남는다. 직접 summary handoff는 **PASS/issue0**이고 pipeline operations는 **OPEN**이다. controller dry-run 판정도 DONE=false다. whole-chain/PREOPEN GREEN을 생성하지 않았다.
- 재생성된 managed9/17 보고서의 warm integrity/source binding check는8.473ms·raw/summary 본문 읽기0으로 재사용 가능했다. 이는 report reuse 검사이지 실제 봇/broker 지연 개선이 아니다. frozen750→751 fixture 최종 successor의 unchanged wall1.544ms/CPU1.549ms, append wall20.802ms/CPU8.610ms다. append wall은 baseline18.431ms보다 증가했으므로 wall 개선을 주장하지 않는다. 비용은 checkpoint/fsync와 실제 consumer scope로 제한해 보고한다.
- 보호 manifest 대사 후 이번 합성 benchmark scratch43파일/9,138,645bytes만 삭제했다. production 과거 삭제0, 원 mismatch·raw·주문/custody/비용·현재 summary/checkpoint/report·정책/rollback·immutable release는 보존했다. generator/hash·baseline/final numeric receipt와 테스트/실행 증거는 남겼다.
- canonical 작업본은 다른 세션의 dirty 변경을 보존한 혼합 상태이며 배포 검증 authority는 clean successor다. canonical 보충 검증177PASS/5FAIL 중3개는 old canonical에 없는 upstream execution-projection 계약,2개는 다른 세션의 wrapper stage 제거와 upstream test 차이다. 이를 clean successor 회귀 실패로 숨기거나 해당 타 세션 변경을 덮어쓰지 않았다. 관련 문서/인계와 최종 selector만 승인 범위대로 반영했다.

PV0–PV6의 실행 가능한 구현·리뷰·회귀 검증은 종결했다. 잔여 자연 OPEN은 다음 유효 영업일의 정상 producer 생성·종료 coverage/완료창 parity·실제 Sentinel/execution census 비용과 실제 PID 소비다. 과거9/15–17 summary 누락의 row/PID causal 원인은 복구 증거가 없으며 raw authoritative fallback을 유지한다. 새 매매 정책·양수 ΔEV·실제 순익·인과적 개선은 본 작업으로 생성하거나 입증하지 않았다. 세부 수치와 판정은 [validation](../../tmp/pipeline-verbosity-incremental-20260918/validation.json), [deployment](../../tmp/pipeline-verbosity-incremental-20260918/deployment.json), [regeneration](../../tmp/pipeline-verbosity-incremental-20260918/regeneration.json), [consumer closure](../../tmp/pipeline-verbosity-incremental-20260918/consumer-closure.json), [cleanup receipt](../../tmp/pipeline-verbosity-incremental-20260918/cleanup-receipt.json)을 따른다.
