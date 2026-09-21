# 메인 제출병목 인과 복원 — 작업본 구현·리뷰

- 범위: [수리계획](../proposals/main-submit-bottleneck-causal-repair-plan-2026-09-21.md)의 확인된 판정/관측 연결 결함. 사용자 후속 구현·반복 리뷰 승인에 따른 작업본 변경이며 커밋푸시·배포·재기동·주문은 실행하지 않았다.
- 자연 검증 owner: [당일 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 `SubmissionBottleneckMonitorNatural0921`. WS P2/P3와 비용 경제성은 기존 별도 owner를 유지한다.
- 운영 재확인: 14:35 KST PID174887의 cwd는 `capital-coverage-repaired-20260921-4b3b4080c/src`, 시작12:57:39. 작업본 HEAD=`ea4788788`이며 이 변경의 배포 영수증이 아니다. 기존 dirty WS/문서/테스트 변경을 보존했다.

## 구현과 반복 리뷰

1. **S1 판정 이력:** 기존 capture hash를 경제성 관측·AI 결과·terminal까지 전달한다. 관찰 중인 종목당 하나의 process/정책/시도 식별 receipt로 명시적 부모 hash를 연결한다. Sentinel은 같은 six-field attempt, 순서·parent·owner·revision 내 action/screen을 검증한 전이만 최종 revision으로 집계한다. 구형·누락·fork·역순·같은 시각의 순서 불명·동일 revision 충돌·이전 실행 흔적은 계속 contract gap이다. 최초 ENTER_NOW와 전체 경제성 이력을 별도 보존하며 attempt/submit 분모를 늘리지 않는다.
2. **경제성 소급 금지:** revision별 proof를 분리해 다른 입력의 정상 proof를 충돌로 오인하지 않는다. 후속 성공이 최초 ENTER_NOW의 결손을 메우거나 앞선 proof가 최신 revision의 누락을 채우지 못하게 했다. 비진입 cache-only 관측 제외를 과거 ENTER_NOW가 있는 시도에 적용하지 않는다. 캐시 schema 재구축/과거 incident 삭제는 없다.
3. **S2 제한적 RECHECK 복원:** 기존 setup producer가 단독 large-sell·정상 source/완료봉·유효 setup·구조 edge·확인 volume·tail risk 없음으로 WAIT_CONFIRMATION을 만든 경우에만 실제 main core/policy도 RECHECK다. 매도 위험을 COMPENSATED/ENTER_NOW로 바꾸지 않는다. 구조 실패·불량 source·극단 스프레드 등 복합 위험은 BLOCK을 유지한다. main composer는 WAIT/no probe/기존 scanner 재평가를 유지한다.
4. **판정 원본과 로그:** 구형 feature probe 필드를 덮지 않고 `entry_decision_large_sell_print_detected`를 exact payload/hash에서 전달한다. terminal 중복 억제도 attempt뿐 아니라 revision을 구분하여 후속 재확인 종료가 사라지지 않게 했다.
5. **guard 원인:** 기존 guard 결과의 WS age/jitter·spread·stale·분류 상세/적용 한도·시각을 `pre_ai_observation_only` 영수증에 보존한다. 실제 제출 guard 실행 증거로 사용하지 않는다. 분류 로직·한도·추가 계좌 요청은 바꾸지 않았다. 현 evaluate_live_buy_entry 경로는 RTT 입력을0으로 전달하므로 과거 DANGER를 오래된 실제 주문 RTT의 영향이라고 추정하지 않는다.
6. **후보 경로:** `returned/partial_adapter_return`은 탈락 사유가 아니다. 동일 scanner generation의 후속 prune receipt가 확인되면 실제 사유를 연결하고, cycle가 명시적으로 충돌하거나 세대가 없으면 `candidate_disposition_missing`으로 남긴다. source_seen의 다른 cycle 사유를 전용하지 않는다. 후보·slot/cap/cooldown을 변경하지 않았다.

보완 리뷰에서 발견·수정한 문제:

- 관측 guard dict가 기존 문자열 wire contract에서 Python repr로 변환되어 파서에서 누락됨 → 명시적 JSON 직렬화 및 실제 logger→slim cache 회귀로 보완.
- process-local revision receipt가 경제성 operating snapshot에 섞여 replay digest에 영향을 줌 → 거래 상태 snapshot에서 진단 receipt만 제외. 원본·기계 hash·경제성 연결은 별도 identity에 유지.
- 동일 attempt의 후속 revision terminal이 기존 중복 억제에 걸림 → revision별 terminal 기록, 동일 revision 중복은 계속 억제.
- 경제성 이벤트 자체가 없는 revision에 다른 revision proof가 전용될 수 있음 → 각 revision의 존재 여부까지 검사.

## S0 원천 고정·실제 표본 재현

`data/ai_decision_payloads/ai_decision_payloads_2026-09-21.jsonl` 읽은 prefix 21,596,569 bytes, SHA256=`cf668c5d27da17ccc76443f2a98eb470a07554f57420db5a4a5cb26427b2fc32`. 13:20:11–13:50:11의 저장된 BLOCK39행을 기존 기본 policy/core로 재현했다. 보고서의 확정 BLOCK37과 분모가 다르며 충돌 시도에 포함된 후속 BLOCK2도 포함한다. 변경은 아래4행의 BLOCK→RECHECK뿐, 나머지35행 BLOCK 유지, 새 ENTER_NOW0. 아래4행의 comparison validator 오류0, main policy RECHECK도 확인했다. 원본을 복제/수정하지 않고 byte range와 line hash로 고정한다.

| Snapshot ID | Byte offset / length | 원본 행 SHA256 |
| --- | --- | --- |
| aims-66d3e5f8c1c07233e752 | 15222594 / 39912 | cd3b4a3201ec19e7d088d534b5680ed3627fc5b200ae0c0f4bc11ac27a8a563b |
| aims-c64ab5cea08621d3a5e5 | 15469143 / 36418 | bdb5a60b0c739c16a2f5bdcf349e5efe50ee7e383530989632ca48b4e05179e8 |
| aims-382eefbf0d05278cb7fa | 16950648 / 36128 | 305acf9d688a82a428046b5aa124b07052328a95b966fa894dc2f983d3129711 |
| aims-4426caf5c08d6fe53215 | 17638812 / 36064 | 8039967452a0bf735423617066dbf7f5d85ba12fbcf586df5342ad1737a95068 |

증분 cache의 bounded range `[27503729,61058161)`에서 두 시도의9event를 읽어 순수 snapshot 함수로 재현했다. 추출 `{offset,bytes,sha256}` 목록의 sorted-key JSON SHA256=`1661f9fd692df416d53c0d028fc1e1010ea3b00f8d7bf1095e359b801cec9af7`. 두 시도 모두 initial ENTER_NOW/latest BLOCK/legacy_unverified/UNKNOWN을 보존한다. latest 운영 산출물은 쓰지 않았다.

- 078350: 최초13:39:32.114134 `common_guard_block:latency_state_danger`, 후속13:39:36.708197 비진입 cache miss.
- **계획 진단 정정:** 085910의 최초13:43:11.236436은 `exact_broker_capacity_missing / kt00011_empty`이며 DANGER가 아니다. 후속13:43:14.742266 비진입 cache miss와 분리한다. 두 사례를 같은 원인으로 묶었던 설명을 수정했다. 과거 `kt00011_empty`의 상세 HTTP 원인이나 자금 부족을 이 표본만으로 확정하지 않는다.

## 검증과 미완료 경계

- 1차 affected4file 회귀305 PASS. 추가 revision/소급 금지/세대 결합/guard 직렬화/terminal 검증을 보완했다.
- guard 실제 producer/logger/cache 경로42 PASS(7 route/session × 2 position tag × 3 machine action). 이 검증 중 발견된 JSON 직렬화 누락은 수정 후 통과했다.
- 확장 합집합666 PASS, 관측 receipt를 추가한 producer1case에서 replay digest 실패를 발견했다. 진단 상태를 운영 snapshot에서 제외한 뒤 동일 case와 receipt 단위검증2 PASS로 재검증했다. 실패를 기존 문제로 제외하지 않았다.
- 최종 affected core/monitor/census244 PASS, main nonentry/revision terminal2 PASS, 최종 guard 차단 producer/receipt2 PASS. 중복 포함 개수이며 실주문/자연 수익성 검증 개수가 아니다.
- Python compile·git diff --check PASS. 로컬 문서 링크28개 결손0, print-only parser29task/기존 제출 owner1개 확인. 전체 trading suite·유료 provider/API 재호출·대용량 report 재생성·외부 sync는 하지 않았다. API 요청/응답/FID/구독/계좌 호출 구현은 수정하지 않아 공식 protocol 변경 검증을 수행했다는 주장도 하지 않는다.
- 최종 worktree에서 동시 작업의 WS/위젯 gateway/liquidity guard 변경도 확인했다. 이 수리에서 생성·수정한 코드가 아니므로 보존하며, 해당 변경의 전체 리뷰/배포 gate를 이 테스트 결과로 대신하지 않는다.
- pandas_ta의 기존 pandas copy_on_write deprecation warning은 별도다.

남은 자연 검증: 배포 후 명시적 revision의 producer→cache→report 소비, 신선한 후속 재평가, 실제 제출 직전 기존 자금 연결(S4), 정상 제출/정당 guard의 end-to-end. 최초 구현 turn에는 배포/재기동 권한이 없었으며 후속 승인은 아래에 별도로 기록한다. 운영 효과·ENTER_NOW 증가를 주장하지 않는다. 과거 DANGER와 I/O의 직접 인과, 미기록 AI 실패 상세, failed_breakout 차단의 비용 후 적정성은 미확정이다. S3 WS 성능 수리/P2·P3와 S4 자금 재구현을 근거 없이 추가하지 않았다.

## 후속 승인 — 반복 리뷰·통합 배포·메인 재기동

- 사용자 “코드리뷰 후 수정보완 반복, 배포 및 재기동 승인”에 따라 메인 수리를 재리뷰하고 분리된 immutable worktree로 검증했다. 추가 임계치/정책·계좌 요청·주문 변경은 없다. 검토 범위의 source/consumer·구형/충돌 receipt·경제성 소급 금지·RECHECK/주문 안전을 확인했다.
- 메인 수리 commit=`83016c96fb7db92c92d6127da1406ffe97593dac`, 물리 release727 PASS. 현재 작업본/인덱스를 전환하거나 unrelated 변경을 합쳐 커밋하지 않고 별도 release branch/index로 고정했다. 일부 기존 테스트 fixture 보완은 테스트 snapshot에 보존되지만 타 작업의 미배포 trading source는 포함하지 않았다.
- 배포 준비 중 별도 WS P2E가14:45에 `81eb16c09`/PID242503으로 배포된 사실을 발견했다. 구형 `4b3b4080c` 기준 selector를 덮지 않았으며, 이미 배포된 WS source를 그대로 보존한 merge commit=`9e828ab856e104e5b855504bc39876c24db5eb88`을 만들었다. 파일 충돌0, 실제 통합 release의 공유 WS/유동성/수집기/지연/main 연결493 PASS. source clean·compile·bash syntax·기존 정책/PID 검증 PASS. 원격 push는 실행하지 않았다.
- selection 변경 직전 active owned wrapper0 및 selector 원본 일치를 확인하고 selection lock 아래 compare-and-replace했다. rollback은 `widget-p2e-20260921-81eb16c09`이며 더 오래된 main 코드로 WS producer 변경을 되돌리지 않는다. [이전 selector](../../tmp/main-submit-deploy-20260921-6yZCqT/selection-before.json), 기존 release와 tracked data/docs 백업을 보존했다.
- 표준 `deploy/run_runtime_release.sh restart`로 graceful handoff: PID242503→244168. 실제 cwd=`/home/ubuntu/KORStockScan-runtime-releases/main-submit-integrated-20260921-9e828ab85/src`, launcher PID receipt14:48:36.854841, exact-date bootstrap14:48:38 PASS/findings0. bot singleton 확인. 삼성 morning owner는 당일 one-shot 종료 상태이므로 기존 handoff owner가 `not_required/morning_owner_not_active`로 판정했다. 보유/주문 ledger를 되돌리거나 지우지 않았고, 위젯 unit source/설정·독립 PID를 이 배포에서 변경하지 않았다.
- **전체 health GREEN 아님:**14:48:59 메인/스레드·수집기5개 정상이나 위젯 시작 receipt가 새 계약과 맞지 않아 process_health fail, I/O wait33.88% warning.14:50:01 I/O wait42.13% fail. 위젯 PID223297/14:14:03 기동과 구형 receipt를 확인했다. 새 `ENV_KEYS` 계약과 별도 unit/PID 인계는 P2E owner에서 정합화해야 하며 main 정상 기동으로 이 결손을 해소했다고 간주하지 않는다. 안전 임계치나 receipt 검증을 완화하지 않았다.
-14:50 점검 당시 신규 main 평가/명시적 revision 자연 소비는 아직 미관측이다. 다음 정기 Sentinel 및 새 평가에서 확인하며 과거 결손·실제 제출·경제성은 OPEN으로 보존한다. 자연 generation은 이 재기동14:48:36 이후로 구분한다.
- 후속 소비 확인:14:50 정기 Sentinel은14:50:29.982811 source를 만들고14:51:32 정상 종료했다.112개 기존 평가 row에 `revision_chain_status`가 생성되어 새 report consumer를 확인했다. 재기동 이후 평가를 포함하지 않은 창이므로 이112개를 신규 main 효과로 세지 않는다.
-14:53 bounded raw 범위 `[3294556008,3311333224)`의 신규8event/2attempt(144960·468530,14:52:57–14:53:00)에서 경제성 관측→terminal/AI 결과의 동일 machine hash와 `single_revision`을 확인했다. BLOCK2/계약 충돌0, 비진입 exact capacity 관측 결손1/관측 DANGER guard 제외1을 원인 그대로 보존한다. 재기동 후 전체 평가 전수나 실제 재평가 chain/ENTER_NOW·주문 성공 표본은 아니다.
-14:53:08 health는6 PASS/위젯 receipt1 FAIL. I/O wait 경보는 해제됐으나 이전42.13% 기록은 보존한다. main loop·스레드·collector liveness와 위젯 구형 시작 영수증의 인계 결손은 구분한다. 별도 P2E unit/PID 인계 및 신규 revision chain/실제 제출 검증이 후속이다.

## 후속 작업본 — 국소 돌파/stale 연결 및 장후 의미 분리

- 권한: 후속 “계획구현하고 코드리뷰 후 수정보완 반복실행”. 기존 변경 보존, 구현·자기리뷰·보완·재검증만 수행했다. 이 추가 변경의 commit/push·배포·재기동·실주문·실 API/provider 호출·장후 report 재생성은 수행하지 않았다. 위 배포 이력은 이번 변경의 소비 증거가 아니다.
- 돌파: entry context만 `entry_local_breakout_completed_v1`로 분리했다. 첫 종가 돌파 직전10봉의 저항·지지, 기준 봉시각/확인 봉시각/available_at, 원천 hash·route/session-bound episode ID를 보존한다. 고가 접촉은 확인 돌파가 아니며 새 고점으로 고정선을 옮기지 않는다. 첫 아래 복귀와 지속 실패를 구분한다. 구형 failed만 해제됐다고 ENTER_NOW로 승격하지 않고 setup→기계판정의 기존 RECHECK 사유로 연결한다. hard/source/유동성 차단과 공용 holding 기본 분류는 유지했다. 10봉 부족을 독립 opening-flow의 일괄 차단으로 확대하지 않았다.
- 표본 정정: 092220의14:58 종가 돌파 직전10봉 고점은14:57의3,135원이다. 최근3봉 이전 고점3,120원 및 후속 고점3,185원과 구별한다. 036810의 접촉/동률, 진짜 실패, forming/결손/역순·세션 날짜 경계를 회귀했다. 실제 최근3봉 수치+통제된 선행봉 fixture이며 전체 raw 재생/경제성 수용을 주장하지 않는다. 후속2개 연속 하향 종가 기준은 의미 구현값이지 비용 최적값이 아니다.
- stale: 분석 내부의 느린 정책/문맥·파일 기반 micro 입력 준비 후 최종 로컬 WS 재검증을 연결했다. sync/async watching, numeric/early-accel 재확인, pre-submit AI authority retry 다섯 caller를 확인했다. 단일 평가 as_of·snapshot·feature age와 quote stale 표현을 연결하고, 동일 갱신 입력을 경제성 observer에 전달한다. 원 수신시각·평가 ID·parent snapshot은 보존한다. 새 연결은 REST/계좌 요청을 추가하지 않는다.
- 안전 보완: deadline 전/후 검사와 원 attempt deadline 보존, route/transport epoch 변경·refresh 예외·quote clock 충돌의 source-invalid 처리, 실패 refresh가 재검증으로 지워지지 않는지 확인했다. 원본 WS를 수정하지 않는다. 3초 호가·기존 체결·주문 직전 guard는 완화하지 않았다. 실제58초 지연 함수별 원인/빈도는 자연 telemetry 이전에는 미확정이다.
- 장후: main machine-only common/hierarchy/joint에서 현재 구조 의미만 튜닝 입력으로 격리한다. 구형 case table·전체 표본 수·버전별 제외 수와 신형 eligible 수를 분리하고 원본 frozen setup은 수정하지 않는다. 첫 회귀에서 전체 표본 count까지 축소된 결함을 발견해 별도 current eligible 필드로 보완했다. cache fingerprint/economic-kernel hash에 producer를 포함했다. 기존3축·비용/holdout·PREOPEN/PID 조건 유지, 새로운 breakout/TTL 자동 튜너는 만들지 않았다.
- 5초 비진입 cache-only 보존: `entry_cash_capacity_contract` 회귀에 포함했다. ENTER_NOW/사전준비2초·실제 sizing fresh조회·계좌/가격/상태세대/hash 검증·주문 우선권은 그대로다.
- 검증: 관련7개 suite (`entry_snapshot_revalidation`, `ai_engine_openai_transport`, `entry_candle_context`, `entry_setup_evidence`, `ai_action_outcome_calibration`, `scanner_async_entry_bridge`, `entry_cash_capacity_contract`) **667 PASS**. 반복 실행 수를 합산하지 않았다. 최종 compile/diff/parser 결과는 아래 기록한다. review-gate에 따라 producer→setup→machine→observer/capture→장후 consumer를 재검토했고 무관한 WS/위젯 작업은 보존했다.
- 최종 보완 후 같은7개 suite **667 PASS/10.29초**. 변경 Python source/test compile PASS, `git diff --check` PASS, print-only parser **29 tasks / SubmissionBottleneckMonitorNatural0921 1개**. malformed refresh receipt의 2차 예외와 micro 원천 읽기 예외의 정상 입력 대체를 막았고, 평가 직전 deadline도 재검사했다. 전체 trading suite·실제 운영 지연/비용 재생·외부 sync는 수행하지 않았다.
- 잔여: 추가 작업본은 미배포다. 새 natural 입력의 stale 일치·RECHECK/정당 BLOCK·자금 관측 coverage, 정상 제출 경로와 비용 후 경제성은 기존 `SubmissionBottleneckMonitorNatural0921`/main 경제성 owner에 남긴다. 이번 코드 테스트로 ENTER_NOW 증가·병목 전면 해소·수익 개선을 주장하지 않는다.

## 후속 승인 — 국소 돌파/stale 최종 배포와 재기동

- 사용자 “코드리뷰 후 수정보완 반복, 배포 및 재기동 승인”에 따라 위 미배포 작업을 재리뷰했다. 현재 실제 메인이 최신 WS/P2 `4914977fd`/PID259944였으므로 이전12bb/9e828 배포로 되돌리지 않고 **4914977fd를 부모로 수리 파일만 포함**했다. 기본 작업본/인덱스·무관한 변경은 보존했다. 독립 widget/episode unit·PID·custody·정책은 이번에 변경하지 않았다.
- 추가 발견/수리1: 저장 snapshot이 dict가 아닌 손상 입력이면 최종 refresh 실패 후 identity 추출에서 다시 예외가 났다. 기존 source-invalid 경로로 닫고 provider 호출0을 회귀했다. 작업본668 PASS, 첫 물리 배포본 `886f32624`786 PASS.15:53:02 PID279482로 첫 인계·정책 검증 PASS.
- 추가 발견/수리2: 마지막 저장 consumer 대사에서 capture의 임의 metadata는 저장되지 않는 것을 확인했다. `entry_machine_input_trace`를 실제 immutable exact payload에 포함하여 정상 판정 및 source-invalid의 as_of·원 수신/snapshot 시각·단계 지연·parent snapshot이 보존되게 했다. observer 전달과 실제 JSONL 저장을 각각 회귀했고, 검증 후 별도 immutable 보완 배포로 인계했다. 첫 배포가 이 저장 결함까지 닫았다고 보지 않는다.
- 최종 commit **9e998bddd743b9fd916b7abd5431ce20ad6a644a**, release=`/home/ubuntu/KORStockScan-runtime-releases/main-local-structure-20260921-9e998bddd`. 실제 release의10개 관련 suite **865 PASS/18.39초**(반복 실행 합산 아님), compile·bash syntax·diff/source clean PASS. 기존 pandas_ta copy_on_write deprecation warning1은 별도 보존했다. [배포 전 검증 receipt](../../tmp/main-local-structure-final-20260921-OD3AUT/validation.json).
- selector lock 아래 원본 일치/부모 commit·현재 PID/cwd·공유 경로·active owned wrapper0을 확인한 compare-and-replace를 사용했다. 표준 `deploy/run_runtime_release.sh restart`로 PID279482→**280948**, launcher receipt **15:55:30.977304+09:00**, 실제 cwd는 위 release의`src`, main singleton1. 당일 runtime policy/env handoff **15:55:32 PASS/findings0**. 삼성 morning은 기존 owner의`not_required/morning_owner_not_active`; 종료된 one-shot을 재활성화하지 않았다. [최종 selector/PID receipt](../../tmp/main-local-structure-final-20260921-OD3AUT/selection-after.json).
- 재기동 후 자연 정기 health **15:55:38 7/7 PASS**(process/thread·resource·artifact·cron·log·auth·lock). [동결 health](../../tmp/main-local-structure-final-20260921-OD3AUT/health-after.json). 이는 같은 시각 건강 상태이며 무기한 정상/전략 성과 보장이 아니다.
- rollback: 직전886f release/selector는 [직전 selector](../../tmp/main-local-structure-final-20260921-OD3AUT/selection-before.json), 전체 신규 의미 변경 이전의 최신 WS/P2 4914977fd는 [수리 전 selector](../../tmp/main-local-structure-deploy-20260921-FsOZ5t/selection-before.json)에 보존했다. 보유·주문·정책 원본을 삭제/되돌리지 않았다. 원격 push·수동 주문·API 조회·장후 재생성·외부 sync는 미실행이다. 임시 배포 helper의 미설치 psutil 의존은 selector 변경 전 실패했으며 표준 라이브러리 `/proc` 검사로 교체했고 패키지 설치는 하지 않았다.
- 자연 수용 잔여: 최종 재기동 후 확인에서 당일 machine/AI payload 파일은24,843,980 bytes, 마지막 수정15:09:01로 **최종 재기동 이후 신규 machine capture는 미관측**이다. 새 입력의 local-breakout/동일 as_of/timing 저장·5초 재사용 coverage·정상 제출·비용 후 경제성은 기존 OPEN owner가 자연 평가에서 확인한다. 테스트를 자연 입력이나 주문 성공으로 세지 않는다.
- 문서/owner 검증: diff check PASS, print-only backlog29 tasks/기존 제출 owner1개 유지. 외부 Project/Calendar 동기화는 하지 않았다.

## 후속 승인 — 체결·분봉 시간대 결함 한정 배포

- 범위: 사용자 시간대 결함 우선 수리 및 후속 리뷰·배포·재기동 승인. UTC 평가시각과 KST HHMMSS를 혼용한 체결·분봉 나이 계산만 수정했다. epoch/default clock도 호스트 시간대와 독립적으로 KST를 사용한다. 기존 naive KST 호환·자정 경계·미래시각 거부·5초 체결/3초 호가 guard를 보존했다. 대량 매도 조건, 호가 원천 선택, 준비 지연, 주문/계좌/정책은 변경하지 않았다.
- 리뷰·검증: 수정 전 회귀5개 실패로 재현, 수리 후1차335 PASS, 경계/UTC 호스트 보완 후6개 관련 suite576 PASS. 과거 원본12행을 쓰기 없이 다시 계산하여 -9시간이0~3초로 교정됨을 확인했다. 과거 기록을 덮거나 자연 수용으로 세지 않았다. 최종 물리 release에서도 같은6개 suite **576 PASS/13.19초**, compile·bash syntax·diff/source clean PASS, 해당 수리 범위 미해결 리뷰 finding0. [검증 receipt](../../tmp/entry-clock-deploy-20260921-CO225k/validation.json).
- 기존 최신 AL/위젯 배포 `4c5dc8a063a39aff3c356ff310385c5c0783cdbe`를 부모로3개 파일만 포함한 **5e3f48bd9ff6080dd7b6e717cf9c9fbe3cfc3d7c**를 별도 index/worktree로 만들었다. 기본 작업본/인덱스·무관한 변경은 보존했다. release=`/home/ubuntu/KORStockScan-runtime-releases/entry-clock-20260921-5e3f48bd9`. 원격 push는 하지 않았다.
- selection lock 아래 원본 일치·부모/PID/cwd·공유 경로·active wrapper0 확인 후 표준 restart. PID285831→**297783**, actual release cwd 일치·singleton1, PID receipt **16:29:19**. 당일 정책/env 인계 **16:29:20 PASS/findings0**, 삼성 morning 기존 `not_required/morning_owner_not_active` 보존. [PID receipt](../../tmp/entry-clock-deploy-20260921-CO225k/selection-after.json), [정책 인계](../../tmp/entry-clock-deploy-20260921-CO225k/policy-after.json). 독립 위젯/episode unit은 재기동하지 않았다.
- **전체 health PASS 아님:**16:29:28 **6/7 PASS**, process/thread·resource·artifact·cron·auth·lock 통과. log_scanner는 이전 PID 종료16:29:17의 `producer summary is closed; raw preserved`5건으로 FAIL. 같은 오류가16:05:32에도 있었음을 원 로그에서 확인했다. 이번 clock patch와 별개로 기존 logger 종료 경로 결손을 보존하며 로그를 지우거나 임계치를 완화하지 않았다. [동결 health](../../tmp/entry-clock-deploy-20260921-CO225k/health-after.json).
- rollback은 부모4c5dc8a06과 [배포 전 selector](../../tmp/entry-clock-deploy-20260921-CO225k/selection-before.json).16:30:44 확인 당시 payload25,834,548 bytes/마지막16:28:05로 재기동 후 신규 capture는 미관측이다. 자연 clock/stale 정상화·실제 제출·비용 후 성과는 기존 OPEN owner에 남긴다. 장후 보고 재생성·수동 주문/API·외부 sync를 실행하지 않았다.
- 후속 자연 확인:16:31:41의437730,16:31:43의067310에서 체결 나이0ms·최종RECHECK,16:31:47의003160에서2000ms를 확인했다. 신규3건 모두 `tick_context_stale=false`, 분봉 `fresh_bar_window`, 미시구조 `ok`, 최종 입력 오류 없음이다. 운영에서 시간대 교정이 소비된 표본이며 전체 원천 결손/제출병목/경제성 종결은 아니다. 문서 링크5개 결손0·print-only parser 기존 제출 owner1개 확인.

## 후속 작업본 — 준비 구간 추적·호가 원천 시각 정합화

- 범위: 사용자 구간 추적·정합 기준 구현·반복 리뷰 승인. 배포/재기동·임계치 변경·실제 API/provider 호출은 포함하지 않는다. 당시 저장 trace43건의 준비 중앙값358.326ms, 상위109606.695/23517.155/18796.146ms. clock conflict8건 중7건은 준비1초 미만이므로 긴 준비와 호가 시각 선택 충돌을 별개로 취급한다. 과거 구간별 시간이 없어 지연 원인을 특정 함수/I/O로 단정하지 않는다.
- 구현 전 공식 reference gate:2026-09-21T16:34:32+09:00 upstream HEAD=`953e5dbff123f437ab4d11a78a95191a685eb51f`를 새 clone으로 확인했다. `kiwoom_docs`는 해당 revision에 없다. `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의0B/0D/ka10004, `kiwoom/realtime/schemas.py`·`packets.py`·`stream.py`, Postman PRD/MOCK ka10004 요청을 검토했다.0B FID27/28 최우선호가와0D FID41/51 호가1은 서로 다른 원 수신시각을 갖는다. 기존 정규화 값·원 receipt만 사용하고 원 프로토콜/parser/REG/인증/REST 요청은 변경하지 않는다. Postman query표현과 spec body표현 및 REST 기준시간 description 불명확성은 새 의미로 추론하지 않으며 ka10004 재해석은 범위 밖이다.
- 정합 기준: 실제 사용하는 동일 BBO·item/route·transport epoch가 입증될 때만 공용 quote-clock receipt를 canonical BBO에 결합한다. 최신 전송시각을 호가·체결·깊이 시각으로 대체하지 않는다. 원0D 깊이/provenance·stale·route·deadline guard는 보존한다. 충돌은 기준시각/원천을 남긴 source-invalid이며 과거 증거를 소급 갱신하지 않는다.
- 구현: `entry_context`/`entry_screen`만 동일 값·item/route/epoch와 신선한0D 깊이를 검증한0B 최우선호가 receipt를 canonical BBO에 결합한다. 원 깊이 수신시각은 별도로 보존하며 holding/REST 재해석은 변경하지 않았다. 최종 검증은 age뿐 아니라 실제 feature top-of-book 값도 대사하고 실패 직전 canonical/feature 원천·값·시각을 immutable trace에 남긴다.
- 구간 계측: 정책 해석, runtime 문맥, context 후보 저장, micro 원천 준비(첫 import 포함), 기타 준비, 최종 로컬 refresh, canonical 재검증을 분리했다. 이전110초의 상세 구간은 복원 불가다. 새 cache·비동기 worker·임의 timeout·추가 REST 호출로 덮지 않고 느린 준비 뒤 원 수신시각을 보존하는 기존 최종 갱신 경계를 유지했다. `metric_role=source_quality_diagnostic`, `decision_authority=report_only_no_order_or_threshold_authority`, `window_policy=same_evaluation_attempt`, `sample_floor=one_attempt`, `primary_decision_metric=stage_elapsed_ms`, `source_quality_gate=exact_capture_identity`; 미래 증거 소급·시각 재날인·stale/주문 guard 우회는 금지다.
- 반복 리뷰: 최초431개 회귀 중 stale-depth 우회1건을 발견했다(430 PASS/1 FAIL).0D freshness·정확한 depth receipt/정수 epoch 검증으로 보완하고, bool epoch·다른 item/epoch·실제 호가 값 충돌·holding 비변경·canonical 재검증 중 deadline 초과 회귀를 추가했다. 구간 합계와 실제 observer 전달, JSONL 저장을 확인했다. 공식 SDK core/client.py의 요청/continuation도 교차 확인했으며 변경된 wire 호출은 없다.
- 최종 검증:9개 affected suite **906 PASS/12.16초**, 별도 주문 직전 latency/market enrichment2개 suite **222 PASS**. 합계1128개(재실행 합산 아님), compile·diff·문서 print-only parser PASS/로컬 링크 결손0. 기존 pandas_ta copy_on_write deprecation warning1은 별도다. 공유 receipt의 다른 소비자도 대사했으며 본 범위 미해결 코드리뷰 finding0이다.
- 권한/잔여:16:44 확인 selected release=`5e3f48bd9`, PID297783로 이전 배포 유지. 이번 변경의 commit/push·배포·재기동·장후 보고 재생성·외부 sync는 하지 않았다. 구간별 실제 지연 비중, 자연 quote-clock conflict 감소, 운영 수용은 미확인이다. 과거8건을 해소된 자연 표본으로 재분류하거나 전체 제출병목 해소로 보고하지 않는다.

## 후속 승인 배포 — 준비 구간 추적·호가 시각 정합화

- 사용자 반복 리뷰·수정보완·배포·재기동 승인으로 위 작업본만 반영했다. `korstockscan-review-gate`에 따라 원천 receipt→canonical→최종 feature 대사→immutable capture 및 기존 latency/market-enrichment 소비자를 재리뷰했다. 추가 in-scope finding0이며 앞선 stale-depth/epoch/deadline 보완을 유지한다. 기존 dirty 작업본·기본 index·위젯 별도 변경은 보존했다.
- 부모 `5e3f48bd9` 위에 정확히 source3개/test3개만 alternate index로 커밋한 불변 배포본 `90dd032e34efb36fb0ace5d9022fc7bcecb1eaf6`. **실제 배포 디렉터리에서 11개 suite 1120 PASS/62.97초**, compile·bash syntax·diff check PASS. 작업본1128과 차이8은 이번 범위 밖 위젯 reader/census 회귀이며 배포에 혼입하지 않았다. 기존 pandas_ta 경고1건은 보존했다. [검증 receipt](../../tmp/entry-input-deploy-20260921-ZcHsjD/validation.json).
- selector lock 안에서 부모·PID cwd·소스 clean·공유 링크·활성 장후 wrapper 없음 확인 후 표준 `bash deploy/run_runtime_release.sh restart`로 기동했다. 메인 PID **310711**,16:51:06 새 release cwd 소비·singleton1,16:51:07 exact-date 정책 환경 인계 PASS. 삼성 morning owner는 `morning_owner_not_active`로 handoff 불필요 판정. [선택/PID](../../tmp/entry-input-deploy-20260921-ZcHsjD/selection-after.json), [정책 인계](../../tmp/entry-input-deploy-20260921-ZcHsjD/policy-after.json).
- 자연 startup health **16:51:19 7/7 PASS**, 신규 log 오류 없음. 이는 앞선16:29 logger 오류의 수리 증거가 아니며 해당 과거 결손을 삭제하지 않았다. [동결 health](../../tmp/entry-input-deploy-20260921-ZcHsjD/health-after.json).
- rollback 기준은 부모5e3f48bd9와 [이전 selector](../../tmp/entry-input-deploy-20260921-ZcHsjD/selection-before.json).16:51:19 확인 당시 payload 마지막16:50:27로 재기동 후 신규 자연 평가 미관측이다. 준비 단계의 실제 지연 분포·0B 동일 호가 clock 채택·충돌 감소는 기존 `SubmissionBottleneckMonitorNatural0921` OPEN owner의 자연 수용으로 남긴다. 과거110초 지연은 원인미상이며 이번 코드검증/PID/health로 해소됐다고 주장하지 않는다. 임계치/요청한도/주문 안전장치·widget/episode 프로세스·장후 재생성·외부 sync·remote push는 변경/실행하지 않았다.
