# Main 반복 검증·Sentinel I/O 경합 개선계획 — 2026-10-13

상태: **IO0/IO1/IO2 및 IO3 로그 tail 구현·반복 리뷰·표적 검증과 10/14 장후 배포 완료.** §11에 실제 전환을 기록했다. 10/14 08:52 점검에서 후속 선택 릴리스와 Main PID의 기존 I/O13개 파일 보존을 확인했으며, 정규 모니터·배포 전체 검증의 잔여 비용은 [추가 개선계획](main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md)이 소유한다. 아래 최초 배포 보류는 당시 이력이다. 자연 성능 수용과 비용 후 성과는 코드·배포 완료와 구분한다.

## 1. 판단과 근거 시점

Main 프로세스 안의 정책 검증과 정규 Sentinel 배치에 반복 I/O가 확인됐다. Codex 작업도 같은 호스트에서 경합하므로 별도 작업군으로 계측한다. 경보의 `I/O wait 56.1%`는 호스트 전체 값이다. 당시 프로세스별 물리 I/O 비율을 소급 확정하거나, 순수 매매 루프의 단독 원인이라고 판단하지 않는다.

근거는 [19:23 조사 보고서](../../tmp/io-attribution-audit-20261013/report.md), [원 측정 요약](../../tmp/io-attribution-audit-20261013/summary.json), [계획 작성 시 릴리스·PID·13개 소스 대조](../../tmp/io-improvement-plan-20261013/context.json)다. 큰 원본을 다시 스캔하지 않고 이 증빙과 소스 코드를 대조했다.

| 구분 | 확인 내용 | 해석·제한 |
|---|---|---|
| 경보 | 19:02:01 iowait 56.1%, 19:02:03 경보, 19:03:19 회복 로그 | CPU 순위는 I/O 기여율이 아니다. 순간 회복이 반복 비용 해소를 증명하지 않는다. |
| Main 직접 측정 | PID3387032/TID3387861, 19:14:34~19:16:04의 논리 읽기 6.312GiB, 물리 읽기 310.64MiB | 열린 전일 pipeline 2.835GiB와 `pre_submit_delay_policy/generations/.../.verify-*/.sort-*/index.sqlite`·shards를 확인했다. Python thread 이름까지 직접 매핑하지는 않았다. |
| Sentinel | 19:00:01 START→19:02:56 DONE, 경보 표본 RAM 약2.84GiB | 실제 cron 작업이다. 당일/전일 캐시 합계 약1.75GiB, summary 약169MiB를 다시 decode한다. 전일 추가 행0이어도 재적재한다. |
| Codex | 경보 때 pytest 동시 실행; 후속 같은 계열 pytest의 Codex 부모 확인 | 경보 시점 종료 PID의 부모·물리 읽기량은 미기록이다. 동일 서버 개발 부하를 배제할 수 없다. |
| 기존 조치 | Sentinel cache/summary, streaming projection/string pool, flock·nice12·ionice2:7·affinity 적용 | 캐시 파일을 사용해도 전체 JSON decode·객체 적재·재집계 비용이 남는다. 같은 조치를 새 개선으로 반복하지 않는다. |
| EBS | 200GiB 확장 완료 | 실제 volume type·IOPS·throughput·CloudWatch 한도는 미조회다. 용량 확보를 I/O 개선 수용으로 삼지 않는다. |

원 측정 릴리스는 `main-timeout-structure-20261013-v4`, commit `a72d0c47753305d23da6a3f4e38f4d14a585f387`이다. **19:44:05 재확인**한 선택 릴리스는 `main-rest-reduction-20261013`, commit `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`, 실제 PID3517912/start ticks13710100/cwd=`.../main-rest-reduction-20261013/src`다. 조사 대상 13개 파일은 원 측정 릴리스·현재 선택 릴리스·작업본에서 동일했다. 반복 I/O 구현이 남아 있다는 근거이며, 새 PID의 I/O 수치나 REST 절감 효과를 다시 측정한 증거는 아니다. 구현 시작과 배포 시 대상 identity를 다시 고정한다.

## 2. 범위와 보존 계약

- 검증·집계·저장의 실행 비용을 줄인다. Main/manual custody, 가격·계좌·주문·수량·cooldown·hard/protect/emergency, operator veto, native 5초와 source freshness를 보존한다.
- 게시·준비·기동 및 변경 세대의 native 전체 검증을 유지한다. 일반 관측의 동일 세대 재사용과 실제 주문 직전의 fresh guard를 분리한다. 검증 실패를 PASS로 캐시하거나 관측 장애가 runtime env를 자동 변경하게 하지 않는다.
- Sentinel의 실제 population, exact attempt, stage·owner·venue/session, full/partial·real/sim/CF, null/cost/terminal/exclusion과 소비 필드를 보존한다. 필요한 데이터를 임의로 최근 기간/일부 종목/상위 표본으로 줄이지 않는다.
- [REST 절감 계획](main-rest-excessive-call-removal-and-input-quality-relaxation-plan-2026-10-13.md)의 별도 승인된 입력 축소를 재심사하거나 과거 입력 복원을 요구하지 않는다. 비교 기준은 구현 시작 시 선택된 REST 절감 릴리스의 계약이다.
- episode/widget 자동 실행·수집·연구·게시를 되살리지 않는다. 데이터 삭제, EBS/RAM 증설, cron 주기·경보 임계치 완화는 이번 계획의 즉시 실행 항목이 아니다.
- 이번 후속 요청은 I/O 계획 보완·구현·반복 리뷰·배포·재기동을 명시 승인했다. 원 정책·PREOPEN을 보존한 정상 ordered handoff를 사용한다.

## 3. 구현 순서와 코드 소유 위치

| 단계 | 변경 대상·역할 | 구현 결과 | 선행 조건 |
|---|---|---|---|
| IO0 | `monitoring/system_metric_sampler.py`, 기존 detector/검증 호출 경계 | 호스트·Main 검증·Sentinel·개발 작업의 구분된 비용과 정확한 byte 집계 | 기존 증거 사용, 큰 재실행 없이 시작 |
| IO1 | `scalping/pre_submit_delay_initial_policy.py`, `automation/pre_submit_delay_partitioned_research.py`, `automation/runtime_policy_bootstrap.py`, `error_detectors/artifact_freshness.py` | 성공한 동일 동결 세대의 일반 점검 재사용, warm 전체 재검증 제거; cold 중복 패스 추가 수정은 잔여 측정 후 판단 | IO0 최소 계측·호출자 census |
| IO2 | 기존 `sentinel_event_cache.py`, `buy_funnel_sentinel.py`, `pipeline_event_summary.py`; 저장 헬퍼는 `monitoring/sentinel_compact_store.py` | 증분 색인·압축 필드와 동일 입력 집계 재사용 | IO1과 분리 검증, 현 report 소비 계약 목록 |
| IO3 | `kiwoom_websocket.py`, `bd_fbuy_accum_pre_scanner.py`, `trading/market/shared_ws_snapshot.py`, 진단 로그 독자 | 남은 대형 snapshot rewrite·로그 전체 읽기 축소 | IO1/IO2 뒤 잔여 비용 확인, 모든 해당 소비자 census |
| IO4 | 개발 작업 실행 방식, 필요할 때만 기존 운영 wrapper | 대형 pytest/replay/압축 작업의 겹침 축소 | 실제 작업군 관측; Main·정규 배치의 기존 계약 유지 |
| IO5 | 기존 release handoff·자연 수용 owner | 단계별 적용 증빙, 정규 cron/매매 경로의 자연 성능 대조 | 영향 범위 리뷰·표적 검증 및 해당 적용 권한 |

기존 파일을 우선 수정한다. 새 코드가 필요하면 역할별 패키지와 가까운 소비자를 먼저 확인한다. `src/engine` 루트에 새 모듈을 추가하지 않는다. CLI 호환 표면은 기존 모듈을 사용하고 새로운 중복 구현을 만들지 않는다. 테스트는 `src/tests`의 해당 계약 시험에 둔다. 새 헬퍼는 Sentinel 진단만 소유하는 `monitoring`에 둔다. 기존 거래용/연구용 storage authority를 공유하지 않는다.

## 4. IO0 — 최소 계측과 기준선

1. `error_detection_loop → run_all → artifact_freshness/준비 검증 → bootstrap.verify_bootstrap → _pre_submit_delay_handoff → committed_paths/verify_source`의 **실제 호출 경로**를 확인한다. IO1 진입 전 call count·caller·target/source date·generation·full/reuse·실패 이유와 stage wall/CPU를 기존 health/진단 경계에 결속한다. 파일 목격만으로 특정 Python daemon의 호출 횟수를 확정하지 않는다.
2. 기존 sampler에서 `/sys/class/block/<name>/partition` 및 실제 block topology로 device를 식별한다. root 물리 디스크와 그 partition을 동시에 더하지 않는다. dm/다중 volume은 선택한 계층·장치별 값을 명시하고 이중 합계를 만들지 않는다. 과거 이중 합산 bytes는 참고 이력으로 보존한다.
3. Main PID/start identity, 검증 thread 또는 직접 함수 계측, Sentinel의 cron 부모, Codex/pytest/replay 부모·자식 관계를 분리한다. `/proc`의 `rchar/wchar`와 `read_bytes/write_bytes`, RSS, major fault, host swap-in/out·I/O PSI·device await/queue를 interval delta로 기록한다. process 합계와 task 합계를 다시 더하지 않는다. 종료·권한 부족·PID 재사용·짧은 자식 미관측은 `unobserved`로 남긴다.
4. 전체 명령줄·환경변수·토큰을 새 기록에 넣지 않는다. 제한된 작업 이름/owner·PID birth만 보관한다. 평상시 기존 cadence와 유한한 레코드 크기를 사용하고, 진단할 때만 60~90초 bounded 관측을 한다. 매 tick `/proc` 전수/FD/raw 스캔을 새로 설치하지 않는다.
5. 현재 릴리스·정책 세대·원천 cutoff/행수·캐시 cold/warm·시장 세션·개발 작업 동시성을 측정표에 고정한다. IO1 전후 동일 frozen 입력은 격리 경로에서 대조하고, 자연 부하는 작업군 유무를 함께 기록한다. 라이브에서 OS page cache drop이나 전체 report 중복 실행으로 cold 조건을 만들지 않는다.

계측의 목적은 반복 읽기의 실제 제거와 회귀 확인이다. 별도 장기 수집 프로젝트를 선행 조건으로 만들지 않는다. 새 자동화 소비 지표를 추가한다면 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=exact_interval_and_same_generation`, `sample_floor=단계별 §8`, `primary_decision_metric=반복 검증/재적재 제거와 동일 출력`, `source_quality_gate=정확 identity·완전 interval`, `forbidden_uses=정책·주문·수익 승인`을 선언한다. 계측 누락은 0비용이나 안전 PASS가 아니다.

## 5. IO1 — 동일 정책을 매번 다시 만들지 않기

### 5.1 확인한 비용과 첫 변경

`committed_paths(validate_selection=True)`는 sharded `validate()`를 통해 동결 전체 projection에서 selection을 rebuild한다. 매번 `.verify-*` 임시 디렉터리·SQLite sort·shards를 생성한다. `verify_source()`는 compact 파일의 seal·누적 해시와 raw/compact ledger를 반복 확인한다. `runtime_policy_bootstrap.verify_bootstrap`의 pre-submit handoff도 이 경로를 호출한다. `next_preopen_readiness`의 `generation_only=True`는 이미 있으므로, 그 바깥으로 이어지는 호출과 각 함수의 실제 mode 전달을 확인한다.

먼저 **일반 health 점검 전용으로 성공한 검증 결과를 재사용**한다. 공개 verifier의 기본값을 얕은 검사로 바꾸지 않는다. publication/preparation/startup caller와 observer caller를 명시적으로 구분하고, 원 full verifier를 기준 판정기로 유지한다. 글로벌 `validate_selection=False` 전환만으로 완료하지 않는다.

### 5.2 재사용 계약

- **초기 검증:** 동일 프로세스에서 native full selection/source 검증에 성공한 결과만 유한 크기로 보관한다. 디스크에 남은 `PASS=true` 하나나 이전 PID 메모를 믿지 않는다. 재시작·코드 변경 시 재검증한다. cross-process 공유가 필요하면 별도 publisher custody·content binding 검증을 먼저 설계하며 첫 구현의 지름길로 사용하지 않는다.
- **동일성 키:** source/apply date·scope·effective/expiry·parent, pointer/manifest/policy/report/projection/tree leaf identity, 알고리즘·비용·mapping·code contract, 원천 목록과 resolved custody path를 포함한다. 각 파일의 dev/inode/size/mtime_ns/ctime_ns와 필요한 owner/mode, 디렉터리 membership을 대조한다. 이름 변경·late partition·삭제·gzip/raw alias 교체·동일 크기 덮어쓰기를 놓치지 않는다.
- **비용 경계:** 일반 점검은 작은 manifest와 파일/목록 signature를 확인한다. warm signature를 만드는 과정에서 다시 모든 body를 해시하거나 모든 shard를 decode하지 않는다. full 검증 때 구한 content digest와 현재 signature를 결속한다. signature는 OS가 관측한 동일성 증거이며 무조건적인 내용 무결성 보장으로 설명하지 않는다. native 전체 검증 경계는 유지한다.
- **경합:** 한 프로세스의 같은 key는 single-flight로 전체 검증을 합친다. 검증 전후 pointer·inventory를 다시 확인하고 변경 중이면 결과를 게시하지 않는다. 부분 객체 공유·검증 중 오래된 PASS 사용·무한 wait를 막는다. hard safety/주문 경로가 진단 lock을 기다리게 하지 않는다.
- **무효화:** 검증 실패·파일 교체/누락·inventory/날짜/코드/parent 변경·receipt 손상은 reuse 불가다. 성공 cache를 즉시 분리하고 원 native 오류 상태를 보고한다. 원천 결손을 새 valid-empty·기본 policy로 대체하지 않는다.
- **실패 재시도:** 바뀐 입력은 full 검증 대상이다. 동일하게 깨진 세대를 매60초 rebuild하는 실패 폭주를 만들지 않는다. 영구 계약 결손은 입력 변화 때, 일시 I/O 오류는 유한 backoff로 재시도하며 각 점검은 failure/pending을 계속 표시한다. 실패 기억은 PASS나 정상 freshness 갱신의 근거가 아니다.
- **live 경계:** 현재 source age·revocation·scope·registry·claim·모델·실제 계좌/가격/주문 가드는 각 원 consumer에서 수행한다. 과거 receipt를 최신 검증/소비 시각으로 고쳐 쓰지 않는다. 관측 오류가 bot stop/env 변경을 자동 실행하지 않으며, 기동·새 정책 수용의 실패는 원 native 계약대로 처리한다.

### 5.3 전체 검증 자체의 비용

재사용을 먼저 닫은 뒤, 한 full 검증 안에서 파일당 하나의 스트림으로 byte seal·ordered cumulative hash·ledger 입력을 공유할 수 있는지 확인한다. 정렬·alias·source window·원 selection 의미를 보존하고 전체 결과를 기존 verifier와 대조한다. 필요하면 SQLite 외부 정렬을 유지한다. 이미 적용된 `synchronous=OFF`를 새 개선으로 제시하거나 fsync 보호를 임의로 없애지 않는다.

`continuous_reversal_policy_v6`의 과거 origin subprocess 검증과 hash cache churn은 잔여 후보로 둔다. 현재 지배 비용으로 직접 입증되지 않았으므로 IO1 성공을 그 경로의 재작성까지 확대하지 않는다.

## 6. IO2 — Sentinel을 증분 소비자로 전환

### 6.1 처리 구조

현재 cache는 raw append 해석을 줄이지만 `load_rows=True`에서 전일·당일 전체 cache를 다시 리스트로 적재한다. 단순히 `load_rows=False`로 바꾸면 필요한 downstream row가 사라진다. 모든 report field와 exact ledger의 소비 계약을 목록화한 뒤 다음 구조로 함께 전환한다.

1. cache의 `dev/inode/size/mtime_ns/ctime_ns + schema/projection/code + complete offset`에 결속한 SQLite 색인을 둔다. source position을 primary key로 사용해 같은 attempt의 stage/retry/terminal과 중복 행을 보존한다. 새 완결 행만 색인에 추가하고 한 transaction에서 행·count·cursor·세대를 commit한다. 원 raw와 기존 cache는 보존한다.
2. 첫 생성은 전체 native cache를 검증한다. 이후 raw writer의 기존 append 계약과 단일 cache writer lock을 사용하며 raw inode 교체·truncate·동일 크기 edit, cache 외부 수정·projection/schema 변화는 재검증/실패 대상으로 삼는다. 이 계약은 임의의 과거 prefix 수정과 append가 동시에 발생했음을 암호학적으로 검출하지 않는다. 그러한 정정은 native writer 계약 밖이며 원 cache를 보존한 명시적 재생성이 필요하다. tail hash를 완전한 무결성 증명으로 추가하지 않는다.
3. 필드 전체는 SQLite payload에 lossless 압축으로 보관하고 요청된 행만 읽는다. blocker/identity/scope의 짧은 값은 작은 metadata로 직접 소비한다. payload cache는 날짜별64MiB/8,192개, decoded mapping은128개·개당64KiB와 큰 mapping2개·개당8MiB로 제한한다. event header와 digest는 전체 일간 모집단을 유지한다. stage 귀속·가장 가까운 scope·exclusion·늦은 terminal은 단순 합산이 불가능하므로 **변경된 population/window는 기존 native 집계기로 계산**한다. 전체 ordered row digest·summary·code·기간이 같은 집계 결과만 재사용한다. 기간의 경계가 입력 범위 안이면 원 microsecond를 key에 보존한다.
4. 전일도 같은 세대 확인을 거친다. 변경된 원천·late/out-of-order 행·code/비용 정의는 결과 key를 바꾸며 기존 집계를 다시 실행한다. 전일이 무조건 불변이라고 가정하지 않는다. 결과 cache는32개/64MiB로 제한한다. 이 구현을 모든 변경 cohort의 증분 집계로 표현하지 않는다.
5. native `pipeline_event_summary` reader의 `include_samples=False` 결과를 원 파일 세대·reader code/strict mode·내용 hash에 묶은 작은 projection으로 저장한다. 첫 생성/원천 변경 때만 큰 summary를 decode한다. 원 검증/준비 caller는 기본 opt-out이며 Sentinel만 사용한다. projection 손상/쓰기 실패는 native reader로 돌아간다.
6. report schema와 exact ledger 출력을 보존한다. 실제 전체 출력은 약1.67MiB이며 출력 streaming 재설계보다 수GiB의 반복 field 객체 제거를 우선한다. 큰 출력이 생기면 그 비용을 분리해 측정한다.

### 6.2 일관성·복구

- 완결 source offset과 색인 commit을 사용한다. 입력 세대가 바뀌는 도중의 색인 build는 거부하며 report 생성시각으로 원천 freshness를 합성하지 않는다.
- native cache를 fsync하고 metadata를 봉인한 뒤 optional index를 갱신한다. index 실패/ENOSPC는 report 완료가 아니며 다음 호출은 검증된 cache로 재생성한다. 행/payload checksum·population 손상은 현재 호출 실패, state 무효화 후 재생성이다. DB 파일/테이블 자체가 읽히지 않으면 보존하고 실패하며 native cache로 별도 재생성한다. cache 자체의 append와 metadata 봉인 사이 crash는 불일치 원본을 보존하고 실패한다. 이 경우 자동 삭제/중복 append로 복구하지 않는다.
- cursor가 앞서가거나 실패가 DONE으로 발표되지 않아야 한다. optional 집계 cache의 쓰기 실패는 이미 계산된 native 결과를 사용할 수 있다. 큰 원 raw/기존 cache는 삭제하지 않는다.
- 5분 cron·flock·cooldown0·600초 freshness와 override를 유지한다. 초기 build와 warm 비용은 격리 출력으로 별도 검증하고 정규 wrapper의 자연 실행은 별도로 수용한다.

## 7. IO3·IO4 — 남은 쓰기와 개발 작업 경합

### IO3: 측정된 잔여 비용만 변경

WS snapshot은 측정 당시 약839KB/181종목을 약1초마다 썼다. 비동기 writer와 consumer frame cache는 이미 존재한다. 이 파일은 매매·completed-bar consumer도 쓰므로 UI 파일로 취급하지 않는다. 각 필드/종목/route/time의 실제 독자를 먼저 추적하고 작은 live transport projection과 덜 빈번한 진단 projection의 분리, registration receipt의 변경 세대 게시를 검토한다. 변경 없는 payload 재사용에도 producer clock·freshness를 정직하게 유지한다. 장시간 무체결을 임의 heartbeat로 fresh quote로 만들지 않는다.

현행 REST 절감 reader의 required symbols·closed-bar 의미·freshness를 기준으로 검증한다. KIWOOM request/response·FID·REG/REMOVE·recovery를 수정하게 되면 구현 전에 공식 upstream revision/파일/조회 시각을 기록하는 API Reference Gate를 수행한다. 프로토콜·구독 범위를 성능만으로 축소하지 않는다.

`cron_completion`의 전체 `readlines()`는 bounded tail/회전 marker index로 바꾸되 현재 run의 START/terminal을 정확하게 찾고, 오래된 DONE을 재사용하지 않는다. 이는 수십MiB 수준의 작은 보완이며 GB 읽기의 주원인으로 단정하지 않는다. 비필수 진단 append의 묶음 저장은 소비·손실 허용 계약이 있는 부분만 검토한다. order/custody/request/decision의 필수 영속화·write-before-submit 순서는 보존한다. pipeline writer가 모든 행에 fsync한다는 잘못된 전제도 사용하지 않는다.

### IO4: 개발 작업을 구분해서 실행

Main/정규 Sentinel와 Codex 대형 pytest·replay·압축·대량 hashing의 시간·물리 I/O·메모리 겹침을 기록한다. 우선 같은 호스트의 대형 개발 작업은 한 번에 하나씩 실행하고 좁은 영향 시험을 먼저 수행하는 작업 방식을 사용한다. 이미 실행 중인 사용자 작업을 임의로 중단하거나 Main의 자원 우선순위를 낮추지 않는다. nice/ionice는 보조 수단이며 메모리·page cache 경합의 해결 보증이 아니다.

장기적으로 개발/대형 연구를 분리할지는 IO1/IO2 뒤 남은 경합으로 판단한다. EBS volume type·실제 provisioned IOPS/throughput·latency/queue·credit/limit과 RAM/swap churn을 read-only 조회한 뒤 필요 용량·비용을 제안한다. 조회되지 않은 gp3 성능이나 증설 효과를 가정하지 않는다. 이번 계획에서 인프라 변경이나 패키지 설치를 실행하지 않는다.

## 8. 수용 기준과 표적 검증

아래 수치는 **성능 목표**이며 실제 격리 측정은 §10과 구현 리뷰에 별도로 기록한다. 의미·안전 계약 위반은 수정해야 할 결함이고, 성능 목표 미달은 해당 단계의 잔여 항목으로 남긴다. 비교 가능한 자연 표본이 없으면 `pending`이며, 예산 확대·추가 실주문·경제성 입증을 수리를 위한 선행 gate로 추가하지 않는다.

| 대상 | 필수 계약·검증 | 성능 목표·측정 조건 |
|---|---|---|
| IO0 | root disk/partition 중복0; PID 재사용/종료·읽기 거부는 missing, task/process 중복 합산0 | 기존 샘플러 대비 추가 wall/CPU·기록 bytes를 함께 측정. 새 원천 전수 읽기0 |
| IO1 warm | 동일 검증 세대의 연속5회 일반 점검: selection rebuild0, `.verify`/SQLite/shards 생성0, raw/compact body 재독해0 | 해당 검증 stage 논리 read 95% 이상 절감 목표. metadata/작은 manifest 읽기는 별도 기재; 전체 Main read0을 요구하지 않음 |
| IO1 invalidation | pointer/code/day/expiry/parent 변경, 동일 크기 edit, inode 교체, source/leaf 누락, late partition, 검증 중 변경, 실패 뒤 복구, 동시 caller, restart | full verifier의 원 판정 유지; 같은 key의 중복 full 검증1개 이하; timeout/failure를 PASS로 반환0 |
| IO2 frozen parity | 동일 source cutoff에서 기존/후보의 전체 count·identity·dedup·ledger·window·cost/null·source 판정 일치 | 최초 cold build와 warm delta 비용 분리. warm source decode가 신규/교정 행에 비례하며 전일 무변경 전체 decode0 |
| IO2 bounded memory | partial tail·truncate/rotate·gzip alias·duplicate·out-of-order·late correction·midnight·crash/ENOSPC·schema 변경·동일 크기 edit 검증 | 비슷한 약40만행 입력에서 peak RSS ≤1GiB, warm wall ≤60초, 논리 입력 read ≥80% 감소 목표. 전체 출력 bytes/물리 read·write를 별도 기재 |
| IO2 자연 실행 | 정규5분 cron 연속3회 DONE/exit·후속 consumer·report source freshness ≤600초, 전체 분모 보존 | 감소한 RSS/wall/I/O 확인. 기존 175초 실행과 단순 비교하지 않고 input/append량·cache·동시 부하를 함께 고정/기록 |
| IO3 | 소비 필드·종목·route·clock·closed bar·필수 receipt와 최종 guard 동일 | 잔여 snapshot/진단 write 비용 감소. 비용이 작으면 추가 재설계 보류 |
| Main 자연 수용 | 동일 세션의 source-age, holding/exit 지연, normal submit guard, 원 native5초·attempt clocks | loop/local p95/p99·timeout/censored 분모를 전후 대조. offered/미호출/실패를 빼고 성공만으로 개선 주장하지 않음 |
| 호스트/IO4 | 각 작업군과 disk await/queue·swap-in/out·PSI 동시 관측 | 비교 가능한 30분 관측에서 35% 초과 표본 빈도·연속 초과 길이와 p95 추적. 호스트 iowait만으로 개별 코드 PASS/FAIL 또는 수익 개선을 선언하지 않음 |

기존 `src/tests/test_pre_submit_delay_initial_policy.py`, `test_pre_submit_delay_partitioned_research.py`, `test_pre_submit_delay_tuning.py`, `test_error_detector_artifact_freshness.py`, bootstrap/readiness 계약 시험을 IO1에 사용한다. IO2는 `test_sentinel_event_cache_parity.py`, `test_buy_funnel_sentinel.py`, `test_pipeline_event_summary.py`의 전체 의미 대조와 복구 fixture를 확장한다. IO0/IO3은 sampler·`test_error_detector_cron_completion.py`·공유 WS 소비자의 영향 시험을 고른다. 미래 구현 시 실제 파일 존재·변경 계약에 맞춰 명령을 확정하며 모든 거래 시험을 일괄 실행하지 않는다.

큰 frozen fixture는 한 번만 준비하고 이전/후보를 순차 실행한다. `.venv`의 targeted pytest/compile, wrapper 변경 시 `bash -n`/contract, `git diff --check`를 수행한다. 보고서 비교에서 생성시각·물리 layout처럼 허용된 비의미 필드만 명시적으로 정규화한다. 같은 counts만 맞고 label/cost/attempt가 다른 결과를 parity로 인정하지 않는다. 추가 source scan으로 성능 측정을 오염시키지 않는다.

## 9. 적용 순서·기존 owner·되돌림

실행 순서는 `IO0 최소 계측 → IO1 구현/리뷰/표적 검증·별도 비용 측정 → IO2 구현/검증·별도 parity/비용 측정 → 잔여 IO3/IO4 → 승인된 ordered 적용 → IO5 자연 수용`이다. 각 단계는 격리 증빙으로 검증하며, 이번 후속 승인에서는 검증된 변경을 한 불변 릴리스로 묶어 정상 재기동한다. 한 단계의 개선량과 부작용을 분리할 수 있게 stage/release별 기록을 남긴다. 문서·코드 리뷰 PASS, release 선택, PID 소비, 자연 성능, 경제성은 별도 상태다.

| 기존 stable ID | 이 계획에서 연결하는 후속 수용 | 완료 증빙 |
|---|---|---|
| `DirectFamilyPreopenPolicyHandoff` | IO1 source/selection 의미·정확 날짜·bootstrap/PREOPEN, 허용된 release/PID handoff | native 판정 대조, 원 정책/receipt, release/PID/start/cwd, code binding |
| `NonfixedDispatchReadinessReview1012` | IO0/IO2 report population·RSS·DONE/freshness, IO3 실제 shared-source 소비 | frozen parity와 정규 cron3회, source-age·source consumer 결과 |
| `AuxiliaryCircuitRecoveryRepair1012` | I/O 감소 뒤 같은 attempt의 Main local/auxiliary 경로·원5초·필수 저장 | stage p95/p99, offered/timeout/censored·Main disposition, 원 safety 경계 |

이 stable ID들은 [현재 checklist](../checklists/2026-10-13-stage2-todo-checklist.md)의 기존 OPEN과 Acceptance/History를 유지한다. 새 중복 OPEN을 만들지 않는다. 이번에는 승인된 구현·ordered 배포와 남은 자연 수용을 연결한다. 구현·자연 수용이 다음 날짜로 넘어가면 실제 대상일의 `Due/Slot/TimeWindow/Track`와 원 Acceptance/History를 함께 이전하고 parser상 한 current owner를 확인한다. 과거 오전 시간이나 다른 변경의 배포 승인을 재사용하지 않는다.

실제 배포 전 그 시점 incumbent/rollback·active/staged policy·PID·checklist 봉인과 다른 동시 변경을 다시 고정한다. AUTO/strict 역사 bytes를 재작성하지 않는다. 문서 추가로 checksum이 달라진 최신 편집본을 과거 strict PASS로 주장하지 않으며 실제 handoff에서 final checklist와 native 역사 snapshot을 함께 검증한다. 자동화/wrapper를 수정할 때에는 그 변경을 소유한 운영 문서와 checklist를 같은 change set에서 일치시킨다.

잘못된 cache hit, source/판정 차이, freshness 위반, 필수 receipt 손실, hard/protect/exit 지연이 확인되면 후보 적용을 중단하고 해당 최적화의 원 검증/reader 경로로 되돌린다. 오류가 난 candidate cache만 격리하고 원 raw/policy/custody를 보존한다. 진단 프로세스가 임의로 bot·env·주문을 바꾸지 않는다. live rollback/restart는 당시 허용된 정상 handoff를 따른다. 퇴역 owner를 되살리는 과거 release를 rollback 대상으로 사용하지 않는다.

## 10. 구현 리뷰와 적용 증빙

[구현 리뷰](../audits/main-io-contention-and-repeated-validation-implementation-review-2026-10-13.md)에 변경 파일·발견 결함/수정·표적 시험·실제42만행 전체 보고서 parity·cold/warm 비용·불변 릴리스와 PID 소비를 기록한다. 실험 산출물은 `tmp/io-remediation-20261013/`에 보존한다. 기준136.323초/2.68GiB, 첫 압축 시도194.964초/2.82GiB로 목표 미달이 확인되어 압축 mapping과 재사용을 추가 보완했다. 실패한 성능 시도도 기록을 보존한다.

검증 재사용은 observer context에만 전달하고 공개 CLI/prepare/startup/live guard 기본은 full이다. 비표준 evidence tree는 native full 검증을 유지한다. IO3은 bounded log tail을 구현하고, WS payload 분리는 IO1/IO2 후 지배 비용이 확인될 때만 추가한다. IO4는 큰 벤치마크를 한 worker로 순차 실행하고 nice/ionice를 적용했다. 패키지·인프라·cron cadence·경보 임계치를 변경하지 않는다.

성공한 frozen 실험은 자연 거래·정규 cron 수용이 아니다. 오늘19시 이후 정규 Sentinel 슬롯이 끝났으므로 연속3회 자연 실행은 다음 정규 슬롯의 기존 owner가 수행한다. 실제 배포/재기동/PID receipt는 완료 시 구현 리뷰에 기록하며 주문·수익 성과를 합성하지 않는다.

최종 동일 입력420,430행의 기준선95.548초/2798.96MiB 대비 warm18.492초/808.56MiB, 논리 읽기2,152,933,122→445,630,521 bytes(79.3% 감소)다. 전체 보고서 SHA는 일치한다. warm wall/RSS 목표는 충족하고 읽기80% 목표는0.7%p 미달한다. 최초 색인 생성159.370초/858.36MiB와 약1.12GiB의 파생 저장공간을 별도 비용으로 기록한다. observer의 같은 세대5회는7.652~7.758ms/103,604 bytes로 full1회12,937.661ms/3,051,402,308 bytes와 구분한다. 전부 격리 측정이며 Main 전체 개선률이나 자연 성능으로 확대하지 않는다.

배포 직전 기존 Main의20:00 자연 종료와21:18:12 장후 `initial_entry_quantity_refresh`의 `research_resource_admission_timeout` 실패를 확인했다. 장후 controller·tuning wrapper는 이전 선택 릴리스에서 선행 복구를 기다리고 있다. [릴리스 운영 경계](../runtime-release-routing.md)의 실행 중 wrapper 전환 금지 및 ordered driver의 실제 predecessor 조건 때문에 selector·당일/익일 정책·PREOPEN을 전환하지 않는다. 승인 재요청 사유가 아니다. 기존 `DirectFamilyPreopenPolicyHandoff`가 장후 terminal/프로세스 부재 확인→그 시점 날짜/정책·선택 재고정→native 준비/기동→실제 PID 소비를 소유한다. 오늘의 live predecessor 가정을 내일 그대로 재사용하지 않는다. 이 I/O 수리는 실패한 장후 계산의 자동 재실행·잠금 삭제·대기 작업 강제 종료를 포함하지 않는다.

## 11. 장후 완료 후 실제 적용

위 배포 보류는 10/13 최초 시도의 기록이다. 후속 사용자 지시에 따라 장후 복구 owner의 최종 Main·controller·tuning 성공과 프로세스 종료를 확인하고, 10/14 `373d5f10f3aecf2c31e5a6b8864080e6760c2263`를 선택했다. 장후 수리와 I/O 결합 시험 202개, 정책 계약 33개 동일성, auxiliary 128 scopes 검증을 통과했다. 활성 정책 pointer·behavioral family·원 source/publication 10/13을 유지하며 다음 적용일은 10/14다. 영향받은 delay와 직접 하류·prepared 검증 및 실제 배포 증거는 [장후 배포·기동 준비 감사](../audits/main-io-postclose-deployment-and-next-session-readiness-2026-10-13.md)에 기록한다.

실제 PID와 정규 Sentinel 3회·Main 자연 성능은 [10/14 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 원 stable ID/Acceptance/History로 인계했다. 예정 07:35 PREOPEN·07:55 기동과 준비 PASS를 실제 PID·주문·비용 후 성과와 구분한다. 독립 웹 service pin은 이번 Main 배포 범위에서 유지한다.
