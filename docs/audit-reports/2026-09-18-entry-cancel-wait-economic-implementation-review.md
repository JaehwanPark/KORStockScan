# Entry cancel-wait 실제 제출 조건부 경제성 구현 리뷰

2026-09-18 KST. 사용자 승인 범위는 계획 구현, 반복 리뷰/보완/검증, commit/push, immutable 선택 배포 및 제한 장후 재생성이다. 실행 중인 Main 재시작·주문·조기 PREOPEN·수동 env/provider/guard 변경은 수행하지 않는다.

## 구현과 리뷰

CW0–CW6을 기존 파일에서 구현했다. lossless 실제 submission/cancel census와 durable 주문 원장을 결합하며 거절/불명확 dispatch도 누락하지 않는다. 실제 제출 직전 가격/수량/예산·profile/route/유효 timeout·seed/model/cost/exit를 고정하고, 기존 entry operating replay에서 증명 가능한 no-fill/partial cancel terminal을 평가한다. proxy는 진단 전용이다.

선정은 같은 parent 요청 notional의 비용 후 EV와 동일 자본 일별 net 하한의 동시 양수 → 일별 net 하한 → EV 하한 → 변경량 → 고정 ID 순이다. 학습 선택을 동결한 후 미사용 holdout을 한 번 평가하며 실패 후 차순위 재선택은 없다. 공통 timeout을 보존하고 exact date/hash/venue/session/route/profile에만 scoped override를 적용한다. 다음 거래일 정책은 검증 후보 또는 incumbent 보존이며 PID 소비를 주장하지 않는다.

리뷰 보완: durable 원장만 있는 시도를 제출0에서 제외; 실제 비용 receipt의 owner canonical SHA 사용; signed 보고서를 PREOPEN의 진단 sanitizer로 변형하지 않음; 연속 scoped 정책의 common base/actual incumbent 분리; 진단 capture/append 실패가 주문 처리에 영향을 주지 않도록 격리; 이전 custody를 일별0으로 오인하지 않음; 지연 발행의 평가일/발행일/다음 거래일을 분리했다.

지원 범위는 사전에 선택한 한 scope다. 가상 queue/passive 체결과 cancel ACK 이전 partial holding frame, overnight inventory의 일별 cash 분배는 unsupported/null이다. 미래 actual model calibration/독립 model 및 policy holdout·정규 PREOPEN/PID·완료 비용 성과는 자연 acceptance이며 구현 PASS로 대체하지 않는다.

## 검증과 배포 결과

최종 검증·source/remote commit·immutable 선택·제한 재생성·strict handoff 결과는 `tmp/entry-cancel-wait-economic-20260918/closure.json`에서 확인한다. 초기 affected 366건 및 entry/proof/wrapper 회귀496건 PASS 후 추가 리뷰 보완을 재검증한다. 과거 9/17 giant raw는 읽지 않으며 provider/DB/전체 native 재실행은 생략한다. 기존 source gap은 유효한 no-edge나 신규 양수 개선이 아니다.

최종 통합 회귀1,096PASS(최신 main의 Pattern Lab 폐기 반영), 후속 scope/context285PASS, incumbent manifest 수정240PASS 및 cancel ACK race/원 projection 재검증87PASS. compile/bash/diff/print-only parser PASS다. 재생성 QA에서 verifier receipt를 incumbent manifest로 오인하는 이름 glob 결함을 발견해 exact dated manifest만 읽도록 수정했고 90/120/600/1200초 보존을 회귀로 확인했다.

제한 재생성은 source9/17→publication9/18→effective9/21이며 과거 raw 재스캔/가격·AI 조회가 없다. 과거 producer census가 새 실제 제출 stage를 증명하지 못해 `source_gap`, 제출 parent 수 null/zero 미확정, 비용 후 ΔEV·일별 net delta null, 신규 개선 후보0이다. 독립 incumbent carry 정책과 read-only standalone selector의 다음9/21 handoff, tower/checklist exact source generation을 확인한다. 이는 정상 PREOPEN 실행·actual PID·실제 수익 개선 증거가 아니며 whole native DONE=false를 유지한다. 원 report·summary·checklist/selection bytes는 tmp predecessor manifest에 보존한다.

최종 후행 연결 보완279/74PASS: 기존 tower/checklist producer가 정기 실행에서도 동일 family view를 생성하며, strict verifier는 source hashes뿐 아니라 report/policy/최종 view/체크리스트 본문 의미를 재대조한다. 변조된 최종 선정 상태가 이전 generation PASS를 재사용하지 못하는 회귀를 추가했다. 실제 source9/17/publication9/18/effective9/21의 strict standalone handoff PASS와 selector common90/120/600/1200 carry를 재확인했다. 원자료가 없는 역사적 census bootstrap과 실제 모델 표본/자연 정책 성과는 실행하거나 성공으로 집계하지 않았다.

## 후속 재리뷰·정리와 다음 장후작업 분석

이번 재리뷰는 실제 제출→signed 주문 원장→operating entry replay→독립 model/policy holdout→scoped policy→PREOPEN selector→tower/checklist/strict를 대상으로 했다. Runtime의 venue 대조에 비해 session alias 및 broker route 상충 검사가 빠진 결함을 보완했다. stock/machine의 venue·session·route canonical/alias가 충돌하면 scoped override를 적용하지 않고 common incumbent와 충돌 receipt를 보존한다. 실제 주문 API·가격/수량·guard는 변경하지 않았다. 상충 route·session 및 stock 내부 alias 회귀를 기존 테스트에 추가하고 재리뷰했다.

코어/실행모델/PREOPEN 회귀311PASS. 후행 handoff/router322PASS, compile/bash/diff/print-only parser PASS. 최종 commit/선택 배포·제한 재생성 receipt는 `tmp/entry-cancel-wait-rereview-20260918/closure.json`에 기록한다. 거대한 역사적 raw와 provider 호출·전체 장후 재실행은 하지 않는다. 과거 producer census 결손은 새 코드 배포로 소급 복구되지 않는다. 따라서 독립 정책은90/120/600/1200초 incumbent 보존이며 신규 경제 개선·자연 PID 소비를 주장하지 않는다.

과거 정리는 exact 파일명 참조 검색 및 활성 작업 확인 후 수행한다. 9/14 이전 미참조 Markdown과 현행 v2 reader가 읽지 않는 옛 `.json.reuse-contract.json`만 대상이다. 전 날짜 JSON 경제/감사 원본, 현재 report/policy·modern cache, 주문/보유/cost/원천 및 rollback 증거는 보존한다. 총67개/40,408bytes 삭제 완료. 삭제 파일 목록·크기·SHA와 참조 점검 범위는 `tmp/entry-cancel-wait-rereview-20260918/cleanup.json`에 기록한다. 과거 JSON에서 retained source/count/holdout을 읽는 현행 경로에 영향을 주지 않는다.

### 다음 기본 ON 작업 식별

선택 배포본의 Main postclose wrapper 순서는 cancel-wait report/policy 확인→Daily에서 이미 생성한 cumulative report 대기→조건부 Swing/Lab→`src.engine.pipeline_event_verbosity_report --date TARGET_DATE`다. Cumulative 대기는 새 튜닝 실행이 아니다. `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false` 기본값 아래 Swing simulation/audit와 Swing-only currentness/AI review를 건너뛰므로 다음 기본 ON 실행 작업은 **pipeline_event_verbosity_report (#73)**다. Swing을 명시적으로 켜면 다음 실행은 `deploy/run_swing_daily_simulation_report.sh`로 달라진다. wrapper ON과 실제 예약은 별개이며 현재 설치 cron에서 postclose native 정기 호출 부재를 확인했다. cron 설치 파일의20:10 템플릿은 설치 사실을 증명하지 않는다.

### 실제 결과와 역할

| 평가일 | 실제 상태 | 기존 결과로 확인한 근거 |
| --- | --- | --- |
| 9/15 | 분석 완료, `v2_shadow_parity_fail` | raw 대상148,100 / producer146,879. 공통 완료 분창147,831 /146,686, 차이1,145; identity 불일치, flush 기한 경과 |
| 9/16 | 분석 완료, `v2_shadow_parity_fail` | raw 대상189,150 / producer188,010. 공통 완료 분창188,991 /187,851, 차이1,140; 양쪽 tail159 제외 후에도 불일치·pending_flush=false |
| 9/17 | producer 실행 전 resource guard timeout, 해당일 report 없음 |300초 대기 후 가용 메모리3,923.6MB<4,096MB; wrapper FAIL. Producer manifest의153,062건은 비교 PASS가 아님 |

9/16 raw는6,650,275,819bytes이고 producer 저장은63,786,216bytes 추가됐다. suppressible 대상0건/0bytes, raw_reduction_bytes=0, runtime_latency_improvement=null, economic_effect=not_measured다. Producer submit p95 0.973ms/p99 6.426ms는 관측치이며 비교 baseline이 없어 성능 개선으로 해석할 수 없다. 보고서 exit0/`status=success`는 분석 함수 완료이고 parity 성공이 아니다.

이 작업은 timeout/AI/매매 threshold를 탐색하는 EV 튜너가 아니다. Raw와 producer compact summary의 exact-date count·stage·blocker·payload identity 및 common watermark를 비교하는 운영 진단이다. `runtime_effect=false`, `allowed_runtime_apply=false`, `raw_suppression_enabled=false`이며 dated 매매 정책이나 신규 ΔEV/일별 순익을 생성하지 않는다. 직접 EV 성과는 **미측정/평가 비대상**이다. 다른 튜너의 원천 보존·소비 비용 개선을 돕는 간접 가치만 있다.

### 시간 경과와 구조적 결손의 구분

| 구분 | 시간만으로 해소 가능성 | 수리/확인 owner와 closure |
| --- | --- | --- |
| 현재 작업의 실행 전 메모리 부족 | 다른 작업 종료 후 개선될 수 있으나 ETA 미확정. 과거 FAIL/report 부재는 자동 복구되지 않음 | 기존 resource/postclose owner; 승인된 날짜·scope 실행과 exact-date 결과/terminal 필요. Guard 완화·전체 재실행 안 함 |
| 기한 내 최신 tail의 pending flush | 정상 producer가 계속 동작하면 가능 | producer flush/manifest; 동일 watermark의 count·identity 일치 확인 |
| 9/15·9/16 공통 완료 prefix의 누락 | 단순 대기·체결 누적·더 많은 표본으로 해소되지 않음 | logger→producer admission/buffer→flush publication→reader 원인 경계를 좁힌 뒤 재현/수리. 특정 PID나 강제 종료가 원인이라고 현재 증거로 단정하지 않음 |
| 반복 전체 raw volume scan | 현행 구현은 `_line_count_and_stage_bytes` 전수 순회 뒤 별도 raw-derived parity 갱신; 시간만으로 구조 개선 없음 | 기존 summary checkpoint/verbosity owner의 동일 prefix 중복 읽기 제거·정정/append 무결성 회귀 및 실제 consumer bytes/time 비교 필요 |
| 보고서 부재의 후행 인계 | EV reader는missing 경고를 남기지만 workorder는 보고서가 없으면전용 지시[] | EV/workorder/tower/checklist existing consumer. 지시0은 해결0건이 아닌 입력 부재; missing/deferred/parity 실패를 동일 native ID로 소비하는 계획의 보완 대상 |
| 직접 EV/수익 개선 산출 | 본 작업 역할 밖 | EV 튜너 신설/가격 proxy 사용 금지; 운영 count PASS와 비용 후 매매 성과를 분리 |

### 소비 경로·유지 판단

`pipeline_event_logger → pipeline_event_summary producer/manifest → pipeline_event_verbosity_report`가 생산 경로다. `threshold_cycle_ev_report._pipeline_event_verbosity_summary`는 상태·parity·raw 크기를 운영 요약/경고로 읽는다. `build_code_improvement_workorder._pipeline_event_verbosity_followup_orders`는 repair 상태에서 기존 `order_pipeline_event_compaction_v2_shadow` instrumentation 지시를 만든다. 지시는 source repair/ops CPU·IO용이고 runtime_apply=false다. 이후 summary/tower/checklist/strict가 postclose 소비를 담당하며 Main 매매 판단으로 직접 적용되는 경로는 없다. Compact execution reader는 실제 lineage payload/per-stage census를 별도로 요구하므로 verbosity parity 성공만으로 체결·EV 입력을 승인하지 않는다.

유지 가치는 **원천 정합성 수리 및 실제 reader의 비용 절감이 검증되는 범위**다. 현재 직접 EV 개선 작업으로는 평가할 수 없고 raw 생략 효과도0이다. 우선순위는 완료 prefix의 최초 불일치/후행 missing 인계 수리→기존 증분 집계 재사용→같은 frozen 입력에서 실제 consumer 비용 비교다. 별도 계획 `pipeline-event-verbosity-incremental-parity-and-consumer-cost-optimization-plan-2026-09-18.md`는 이 방향과 일치하나 이번 요청에서는 해당 작업의 코드 변경/보고서 재실행을 하지 않았다.
