# 2026-10-02 장후 원천·의미 모니터링

- Source date: `2026-10-02` (자정 이후 유지).
- Scope: 현행 [장후 inventory](../audit-reports/2026-09-05-postclose-work-inventory.md)의 활성 producer, 내부 산출물, 직접 consumer, strict/controller/finalization 및 다음 거래일 준비.
- Authority: 사용자 장후 모니터링·생산자 보완 지시. source-only 분석 worker 수리·최소 재실행. 주문·guard·threshold·provider 변경이나 매매 owner 수동 재기동 권한은 추가하지 않는다.
- State: 10/2 native·독립 machine·최신 controller wrapper exit0. 00:43 checklist 변경으로 발생한 준비본 검증 실패를 최신 인계 재검증으로 복구했고00:54:41 10/6 prepared_verified다. 별도 읽기 전용 current_full_contract 검증도 PASS/findings0이며 아래 최종 영수증을 따른다. 보관 생산자 재발 방지 릴리스 선택은 pending. 10/6 정식 finalization/PREOPEN/PID는 future due이며 실행 성공을 미리 주장하지 않는다.

## 발견과 수리

### 22:51 추가 복구·성능 진단

청산 스냅샷의 naive/offset-aware datetime 혼합은 첫 시도에서 525.981초 계산 뒤 TypeError를 냈다. 변경 없는 재시도 분석 child만 중단하고 KST wall-clock 정규화·명시 UTC 변환·잘못된 명시 날짜 격리를 수리했다. immutable `ac05e08f` source-only wrapper는 네 `postclose_exit` 산출물을 564.745초에 정상 생성했고, 기존 `820c7c42` manifest consumer의 원천·날짜·네 SHA 검증도 통과했다. 이 재생성은 새 체결·비용 원천을 만들지 않는다. clock/archive 회귀 64 PASS.

Widget signal 연구 producer는 v4를 발행했지만 attribution은 v2/v3만 받았다. 같은 owner/episode/cost 계약을 확인하고 v4를 명시 수용했다. immutable `a5bdd38f` 영향 회귀 130 PASS, 실제 attribution 및 후행 timing/weakness/approval 재실행은 succeeded다. v4 source는 loaded로 바뀌었으나 matched anchor 0/5는 유지된다. prospective 모집단을 추가 수용한 결과 gap 분모는 655→753이므로 이를 악화나 신규 수익으로 해석하지 않는다. 733개는 prospective micro symbol/session/venue 결손, 13개는 active Episode owner anchor, 4개는 active Widget session, 1개는 실제 Widget exact route, 2개는 OFF/retired source 주소다. OFF 원천 복원이나 `_AL`을 `_NX`로 대체하지 않는다.

Main legacy worker PID 2982369는 21:57부터 54분 이상 CPU 약98%로 계속 계산했다. 읽기 전용 CPython stack 표본은 `build_clean_baseline_mechanistic_refinement -> _mechanistic_policy_rows -> mechanistic_entry_policy_decision -> strategy.rebuild/select/digest`를 확인했다. 완전한 전략 프로필이 모든 바깥 threshold를 덮어쓰는데도 공통 후보 80개마다 같은 원천을 재평가하고 있었다. offline 고정 calibration population 내부에서 검증된 전략·계층·veto·version 및 다른 모든 field가 동일한 경우에만 selected row/hash를 재사용한다. paired/holdout/운영 경제성은 기존 kernel과 각 원 후보 receipt로 계산한다. live kernel·guard·grid·날짜·표본·비용·선정 순서는 변경하지 않았다.

같은 전체 grid/32행 fixture의 기존/재사용 각3회 전체 보고서 SHA는 모두 `52c7e00dbc5dcbe948787fee97382ed8b873a5f7838897360de4023c61d58641`, median 2.20068→0.141875초(15.51배)다. 운영 속도 증거는 별도 재실행 전 미확정이다. 영향 전략 회귀 workspace/격리 각304 PASS, 확장 producer/consumer 회귀 workspace769 PASS. 최종 immutable `a290e267` 검증 및 실제 legacy 재실행을 마친 뒤 후행 Main recovery/closure를 진행한다. 공통 selector는 아직820이며, 독립 machine unit의0a pin과 새 source-only worker 실행을 구분한다.

### 23시 실제 계산·복구 orchestration 수리

immutable `a290e267` 통합 표적 816 PASS/65.36초. 기존 legacy 분석 dispatcher만 종료하고 같은 source/publication 날짜로 재실행한 run은 22:53:15→23:05:46, 750.924초에 succeeded다. 이전 run은 55분 이상 계산해도 끝나지 않았다. 15.51배는 fixture 비교이며 실제 운영 속도 배율로 표시하지 않는다. raw/후행 봉·단계 전체 분모와 80개 공통 grid를 보존했다.

승인된 820 native 세 번째 복구 run `bc50203d3944482da5c3b6b6c4a226f1`은 다시 legacy producer를 launch했다. old code 분석만 source-only 수리본으로 교체했지만, 복구 dispatcher가 compact 선행 대기를 0초로 설정해 compact를 deferred로 남겼고 native wait/strict가 이 중간 상태를 통과했다. 23:12:10 strict는 compact 누락 및 checklist 세대 불일치 네 issue로 실패했다. 이를 성공으로 덮지 않는다. compact recovery에 기존 4시간 이내 선행 대기를 적용하고, 하나라도 terminal 실패·오염이 있으면 다른 pending peer 때문에 기다리지 않도록 수리했다. compute slot 밖 대기·SIGTERM·동일 날짜·정책/예산/가드는 유지한다. workspace/격리 dispatcher·strict 121 PASS, 실제 선행 종료 뒤 최소 compact 재실행 succeeded다.

full Main은 KRX 2,976 / PREMARKET_KRX_LIKE 514개 exact machine attempt를 수용하고 9/29·9/30·10/2를 누적했다. NXT 등 나머지 등록 scope는 3,490행 모두 다른 cohort로 제외됐으며 원천이 존재하는 KRX/장전까지 전체 차단하지 않는다. KRX 전략 89 / 장전 91개 후보 search complete이나 promotion은 false다. 장전 `selected_machine_policy`는 연구 선택이며 live 승격이 아니다. 실제 주문·운영 비용 연결이 없는 `machine_operating_population_unbound`는 EV/일일 순익 null·carry로 남긴다. compact 도착 이전 보고서의 10/2 운영 projection 부재는 후행 인계에서 다시 검증한다.

추가 Episode producer 결함은 한 loop의 `two_leg_entry_armed` 및 leg별 `entry_adverse_flow_decision`이 같은 `observed_at_kst`를 쓰면서 다른 상태 hash를 발행하는 것이다. 현재 raw에서는 `same_clock_state_generation_conflict` 106건이다. 새 producer는 profile/day/instance별 sequence와 이전 observation SHA를 원 body에 봉인한다. 소비자는 동일 producer identity·연속 sequence·정확한 이전 hash가 모두 있을 때만 같은 시각의 다음 상태를 수용한다. 유실 append는 sequence gap으로 노출하고 날짜 전환은 새 generation으로 시작한다. 기존 raw를 이 새 계약으로 재라벨링하거나 임의 순서를 합성하지 않는다. 생산·검증·conflict/missing/다른 PID/다른 generation/append 실패 회귀 포함 workspace/격리 각378 PASS. 자연 producer 배포·소비는 별도 OPEN이며 현재 Episode service pin을 변경하지 않았다.

최종 검토 후보 `bd059f365b71dbf1fc297b659e514a7b5c19c916`은 820 대비 source11/test11, 총22파일이며, immutable 추가 표적499 PASS/35.38초·compile/diff PASS다. source/deploy/restart clean 및 공유 경로를 확인했다. 이전 163 선택 승인과 820 native 복구 승인에 독립 machine 분석 service pin 전환은 포함돼 있지 않다. 해당 pin의 root/commit/WorkingDirectory/ExecStart/경로 환경만 바꾸는 proposal을 `/tmp/postclose-machine-unit-bd059f36-20261002.conf`에 준비했다. 기존 실패와 신규 실행을 분리하고, 최종 native 재개·selector·10/6 prepared 검증을 거쳐 closure를 확인한다.

### 23:39 승인한 최종 선택·분석 pin 전환

사용자가 최종 `bd059f36` 선택·독립 machine 분석 pin 전환·수리본 장후 재개를 승인했다. release-set/selection lock 안에서 이전 selector 및 분석 drop-in을 백업하고, 820 selector/0a pin을 비교 검증한 뒤 전환했다. [전환 영수증](../../data/runtime/postclose_recovery/2026-10-02/approved-release-pin-transition-bd059f36-20261002T233916.json)에 이전/신규 SHA와 백업 위치를 보존했다. `--check-release-set` PASS, 124개 owner의 경로/commit/정책 pin 검증을 통과했고 Main PID는 `not_attested`다. Episode 122개 unit의 0a pin은 유지했다.

23:39:32 native 수리본 recovery를 고정 source/publication `2026-10-02`로 시작했다. 정규 wrapper는 EOD terminal을 소비했고 Main bot session이 없어 stop을 skipped로 기록했다. 분석 unit은 daemon-reload만 수행했으며 Main·Widget·Episode 매매 service와 분석 service를 재기동하지 않았다. 기존 실패를 보존하고 신규 native terminal·후행 summary/controller·10/6 준비본으로 완료를 판정한다.

### 23:49–00시 추가 세대 경합 복구·검토

bd native run `b7e89bfc3dcc4db088e65ee68de284ad`의 Main은23:41:15→23:49:36(501.141초), compact는23:49:49에 succeeded다. native는23:49:58 main scope verifier exit2로 실패했다. 이때 병행한 collector source-only 복구의 heartbeat가 checklist source SHA를 바꿨고 정확 세대 검증이 이를 차단했다. 원 계산·기존 실패는 보존한다.

독립 machine group의 복구에서도 부모 attribution 재실행 전에 timing/weakness/approval thread가 이전 succeeded receipt를 받아 실행했다. 부모가 새 running/heartbeat를 쓰면서 세 consumer는 `prerequisite_changed_during_consumption`/`input_changed_during_consumption`으로 실패했다. attribution23:53:55 succeeded 뒤 세 consumer만 순서대로 재실행해 모두 succeeded로 복구했다. capacity는 기존22:15 receipt를 유지했고 주문·AI 호출·전체 Widget grid를 추가하지 않았다.

추가 수리는 기존 그룹을 capacity→collector/attribution 완료→후행4개→summary 순서로 실행한다. Main의 기존 stage wait도 전체 producer(자기 summary consumer 제외)가 terminal이 된 뒤 checklist 세대를 봉인한다. 원 compute slot2·thread 상한6·기존4시간 timeout·SIGTERM·OFF/정책/매매 guard를 유지한다. 강제로 consumer-first 스케줄을 주는 회귀와 독립 producer heartbeat·timeout 회귀를 추가했다.

후속 immutable `63936cf18127cea77f074c56b4c5689a109445c9`은 bd 대비 dispatcher/test2파일, workspace/격리/immutable 각각127 PASS·compile/diff PASS다. 후속 선택 전에는 selector/분석 pin이 승인된bd였다. 사용자가639 선택·분석 pin/수리본 native 재개를 별도 승인했고00:01:37 두 경로를 전환했다. [전환 영수증](../../data/runtime/postclose_recovery/2026-10-02/approved-release-pin-transition-63936cf1-20261003T000136.json)에 이전 selector/pin 및 SHA를 보존했다. release-set PASS, trading service/analysis service restart 없음. 고정10/2 native를 새 수리본으로 재개했으며 기존bd native 실패는 보존한다. 해당 전환 시점에는 실제 terminal/전체 controller/10/6 준비본이 진행 중이었다. 이후 결과는 아래 시간별 영수증을 따른다.

### EOD 기존 키 필터 후 기간 삭제

실제 EOD PID `2961593`의 immutable `820c7c42`와 작업본 모두 같은 결함을 갖고 있었다. 수신 데이터에서 DB 기존 키를 제외한 뒤 해당 종목의 최근 100일 DB 행을 삭제해 신규 행만 삽입한다. exit 0이어도 과거 원천이 소실될 수 있다. 저장 전 source worker만 TERM으로 종료했다. 대기 중 Main/widget wrapper는 수정하지 않았다.

20:25경 실제 DB 대사: 10/1 2,627종목, 9/30 1종목, 9/29 2,627종목, 9/28 1종목. 날짜별 결손은 확인됐으나 삭제 최초 발생일·모든 결손의 개별 인과를 확정하지 않는다. 복구 전 68개 날짜/93,581행 census는 [원 receipt](../../data/runtime/postclose_recovery/2026-10-02/eod-recovery-before.json)에 보존했다.

수신 날짜·종목의 원자 upsert로 교체하고 미수신 키는 보존한다. 재실행 중복·수신 수정·늦은 chunk 실패 시 전체 롤백·PostgreSQL 문법/원래 null을 검증했다. 대상일 행 전무/전체 미수신은 failed이며 추천을 실행하지 않는다. 후행 producer 실패도 completed_with_warnings로 정상화하지 않는다. 부분 종목 결손은 명시한 census와 warning으로 격리한다. API 요청·호출 간격·동시성·정책/주문 owner는 바꾸지 않았다.

작업본 10 PASS/2.09초, immutable `e02e9239` 10 PASS/3.85초; compile/diff PASS. 리뷰 후 추가 보완으로 후행 실패 상태 전파를 검증했다. isolated 검증 초기에는 공유 config 부재로 collection이 실패했고, 표준 공유 경로 구성 후 위 immutable 검증을 통과했다. 추가 empty/stale/partial census·EOD consumer gate 회귀는 workspace/격리 후보에서 각각 15 PASS. 합성 로그가 운영 파일에 기록될 수 있는 fixture 결함도 logger 격리로 보완했으며 20:33:18의 1/2종목 합성 수치를 실제 EOD 진행으로 해석하지 않는다.

20:26:26경 `eod-source-preservation-20261002-e02e9239` root에서 Ubuntu source worker PID `2964380`을 재실행했다. 공통 selector는 `820c7c42`, 진행 중 wrapper와 독립 systemd pin은 그대로다. 원 run의 TERM과 새 source run을 구분한다. 과거 결손 날짜의 새 공식 수신 데이터는 source reconstruction이며 새 거래/실현손익이 아니다. 재수집·DB 저장·모델·EOD terminal·직접 gate 소비는 아직 pending이다. 향후 정규 EOD가 수리본을 선택하는 배포 수용도 별도 필요하다. 추가 회귀를 포함한 불변 후보 `9531cf10`을 준비했다. 실행 중 e02e9239와 update_kospi 소스 SHA는 동일하며 현재 공통 selector 820c7c42의 변경은 EOD 소스·해당 시험 2파일뿐이다.

### 전일 scale-in source block

10/1 scale-in exit 2는 preflight의 `source_quality_raw_missing` 때문에 발생했다. 실제 fill 0을 경제성 0으로 계산한 결과가 아니다. 감사 artifact의 원 pipeline path가 없었고 source read bytes/event count 0이었다. 오늘 raw는 존재하며 대형·증가 중이므로 전체 수동 재스캔 대신 scheduled preflight의 frozen generation과 raw contract projection을 검증한다. 전일 보고서를 재생해 결손을 감추지 않는다.

### EOD 종목 namespace 손실

EOD의 독자 정규화는 `00088K`를 `000088`로 변경하고 긴 숫자 코드도 뒤 6자리로 축약한다. 공용 `kiwoom_stock_code_identity`의 lossless identity와 현행 numeric-equity admission에 맞춰 원 코드를 보존하고 미지원 namespace를 `excluded_symbol_identities`로 명시한다. 미지원 식별자를 다른 종목으로 요청하거나 유효 무기회로 대체하지 않는다. 기존 numeric-equity 범위를 넓히거나 공용 API/주문 guard를 변경하지 않는다.

공식 reference gate: `2026-10-02T20:39:47.418593+09:00`, upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`. [공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)의 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json` ka10081/ka10099, `kiwoom/core/client.py`, PRD/MOCK Postman을 확인했다. `kiwoom_docs`는 이 revision에 없다. 종목 코드와 suffix는 String이며 로컬 numeric-equity 지원 범위를 유지한다. 요청 JSON/headers/continuation/sign/unit/date/real-demo 계약과 호출 한도는 변경하지 않는다.

반복 리뷰·검증 후 후보 `daf4b101`: 격리 16 PASS, immutable 재검증 PASS·compile/diff PASS·source clean. 공통 selector의 변경 범위는 계속 EOD 생산자·해당 시험 2파일이다. active EOD e02e9239의 코드를 교체하거나 정상 numeric 원천을 재수집하지 않는다. 현재 run은 기존 intake의 종목 결손을 그대로 보고하며 새로운 intake disposition을 과거 run에 소급하지 않는다. 향후 정규 producer가 이 최종 수리본을 소비하는 선택 수용은 별도다.

전일 실제 latest DB 2,627행의 mandatory OHLCV 결측/비양수 가격/음수 거래량/가격 경계 모순 census는 각각 0이었다. 오늘 저장 이후 같은 직접 대사를 다시 수행한다.

### 후행 추천의 원천 없음 → exit 0

`recommend_daily_v2`는 panel empty 또는 최신 날짜 행 전무일 때 정상 return해, 원천 실패에도 exit 0과 stale 산출물이 남을 수 있었다. 유효 source의 선정 0건과 구분해 두 조건에 명시적 source-error를 발생시킨다. 실제 retained consumer는 `monitoring.machine_candidate_lifecycle`의 completed daily generation/Widget admission catalog이며 OFF인 Swing research를 재활성화하는 수리가 아니다. 모델·점수·선정 threshold·주문 권한은 변경하지 않았다. 기존 EOD required producer failure 시험의 completed_with_warnings 기대도 failed 계약으로 수정하고, 해당 fixture logger를 격리했다.

표적 4 suite 51 PASS/3.34초, 격리 후보 51 PASS/2.80초. 최종 불변 후보는 `163cc8b2`이며 현행 820c7c42 대비 소스 2파일/EOD·model 시험 3파일이다. 최종 immutable 51 PASS/4.61초·compile/diff PASS·source clean. 사용자가 장후 종료 뒤 이 릴리스 선택·10/6 준비본 검증을 승인했다. 매매 재기동 승인으로 확대하지 않는다. 진행 중 e02e9239 원 run은 변경하지 않았고 실제 모델 원천/생성일/분모·terminal의 자연 수용은 기다린다. 원 run에 후보 수정 내용을 소급한 성공을 기록하지 않는다.

## 현재 단계별 수용

### 21:21 execution 원천 custody 실패와 최소 복구

Main은 entry split 입력의 `part-execution-202610021739.jsonl` 읽기 PermissionError로 exit 1이었다. 오늘 compact 원천 306개 중 unreadable은 이 3,108-byte 파일 하나이며 `root:root 640`, 부모 directory는 ubuntu 소유였다. 생산 경로는 `pipeline_event_logger._append_partition_jsonl`의 lossless execution projection이며 신규 파일은 호출 사용자 소유로 만들어진다. 해당 행은 17:39의 `entry_ai_economic_source_gap`으로, 권한 복구가 유효 경제성/매매 권한을 부여하지 않는다. 당일 root 호출의 직접 실행 주체는 미확인이다.

기존 logical partition lock을 nonblocking으로 획득하고 no-follow regular-file·UID·예상 SHA를 확인한 뒤 파일 하나만 부모 UID/GID로 복구했다. mode 640, inode/size/mtime/content hash `1d262625ac437b8d97e8bea90e6c52298aa224401b1062694bbb922204e08252`는 불변이다. lock 제거·내용 변경·전체 tree chown은 하지 않았다. 실제 ubuntu 읽기를 재확인하고 entry split만 먼저 재실행해 exit 0을 확인했다. native root의 관련 lossless/bounded projection 회귀 2 PASS/1.17초·bash syntax PASS·print-only parser PASS. 정상 ubuntu producer의 권한 계약을 바꾸지 않았다.

entry split은 계산 성공과 별도로 `operating_paired_source_missing`, `operating_owner_source_invalid:actual_outcomes`, `clean_baseline_paired_realized_population_incomplete` 때문에 경제성 source gap, EV null·valid_no_edge false다. 실제 제출 없는 계획 2건을 체결/terminal로 만들지 않는다. cancel wait는 verified submission census 0, unresolved prior custody 0이라 `no_submitted_orders`이며 기존 threshold carry다.

사용자는 원천 복구·표적 검증 뒤 기존 820c7c42/설치 설정으로 중단 Main 체인 재개를 명시 승인했다. 21:34경 router를 통해 native recovery를 재개했다. BOT_ACTION=stop은 설치값 그대로이며 이미 종료된 bot의 재기동은 하지 않는다. 새 run과 이전 failed run을 구분하고 완료된 독립 stage/cache는 native 검증으로 재사용한다. 승인한 163cc8b2 선택은 전체 실행 종료 뒤다.

### 기계·Widget 계산의 의미적 수용과 성능 진단

승률 producer는 21:31:45 완료, 입력 7,069 / accepted 2,975, 후보 search 8, `incumbent_carried`다. 현재 incremental loader는 9/29 하한을 적용한다. 생성 정책과 실제 신규 edge/적용/PID를 구분한다. pre-submit도 succeeded이나 상세 경제성/정책 근거는 추가 대사한다.

기계 최초 projection 9/29 607.2MiB, 9/30 274.0MiB, 10/2 316.9MiB가 생성됐다. loader의 cache read 조건은 64MiB 이하이므로 생성된 큰 projection이 다음 호출에서 재사용되지 않는 성능 결함을 확인했다. 실행 중 immutable 코드를 바꾸지 않는다. source/row/hash/label/cost를 보존하면서 이 읽기·동결 경계를 수리하는 별도 review가 필요하며, 큰 raw 반복 재생을 정상 표본 대기로 설명하지 않는다. 첫 worker는 약 10분 동안 CPU/입출력이 진행됐고 종료 뒤 후속 resource wait가 풀렸다.

Widget 보조 calibration의 005930 KRX carry는 기존 -80/-160bp scale-in runtime trigger를 BBO-only proxy로 계산하지 못하는 source gap이다. 034020/042660의 baseline 없음은 해당 보조 owner가 `include_symbol_expansion=False`로 standard execution policy(현재 005930만)를 소비하는 경계다. 독립 expansion/live 정책을 임의 이관하지 않는다. NXT premarket은 paired path 결손을 남기고 carry한다. 이 진단 성공을 full-cost 실제 경제성이나 전체 Widget 4 producer 완료로 해석하지 않는다.

### 21:34 raw ledger 생산 연결 결손과 원천 요약 11건 복구

첫 승인 recovery는 `atomic_sizing_source_generation_stale`로 실패했다. atomic sizing consumer는 존재하는 요약 파일만으로 수용하지 않으며, 동일 raw 세대와 결속한 `raw_source_ledger`가 필요한데 정규 preflight가 이 기존 seal 생산자를 호출하지 않았다. ledger를 합성하거나 검증을 완화하지 않고 preflight의 기존 생산 경계에 연결한다.

원 raw census 99,102건 중 producer profile 적격 26,670건, profile 외 72,432건, quarantine 0이었다. 기존 요약은 26,659건으로 `strength_momentum_observed` 6건 / `blocked_strength_momentum` 5건이 부족했다. 동결된 raw에서 기존 profile·identity 규칙으로 재구성하고 stage별 count/hash 합계를 대사했다. 원본 요약·manifest는 별도 hash directory에 그대로 보존했다. duplicate·원천 변경·활성 writer·profile 불일치·publish 실패는 차단 또는 롤백하며, 재구성을 실제 producer timing이나 새 경제성 원천으로 주장하지 않는다.

21:54 실제 source-only 복구 21.803초, raw 적격/요약 모두 26,670, ledger issues 0. [복구 receipt](../../data/runtime/postclose_recovery/2026-10-02/producer-summary-recovery.json)의 ledger SHA는 `638b043f98c0af05def4daf0140660243ef45a39235237a588ab72843db8df9f`다. 승인한 동일 820c7c42 native chain을 두 번째 recovery run `fb59a1c47f644237b8c5b9639c23f3c8`으로 재개했으며 entry split 및 후행 내부 계산이 진행됐다. 실패 run의 terminal을 성공으로 소급하지 않는다.

### 큰 기계 projection의 실제 재사용과 품질 보존 수리

기존 64MiB 읽기 조건 때문에 607/274/317MiB cache가 계속 재계산됐다. 기존 daily source/kernel/dependency 및 semantic hash를 유지하면서 lossless gzip level 1로 저장하고, 압축 파일 64MiB·해제 본문 1GiB 상한 안에서 strict hash를 검증한다. 다른 kernel은 작은 header에서 먼저 제외한다. 누적 rich row는 기존 offline `FrozenRows`에 저장해 날짜별 payload를 다음 partition 전에 해제한다. 전체 날짜·row·NULL·비용·결과·후보 grid를 축소하지 않는다. live memory/order guard는 변경하지 않는다.

생산자·소비자 4 suite 484 PASS/47.76초, 추가 mutation rollback/profile·disk sequence와 실제 기계 case table/metric parity 검증 54 PASS/5.76초. 현재 running immutable 820c7c42는 변경하지 않았으므로 이번 native worker의 성능 개선을 주장하지 않는다. 격리 통합 후보 검증과 후속 선택은 별도 gate다.

### 내부 결과의 원천 적격성

pre-submit 누적 committed/eligible 28건, 0/30/60/120/180초 유효 quote 5/6/4/4/4건이다. route mismatch 48, epoch/generation mismatch 43 등은 분석 quote 단위이며 고유 attempt 수와 합산하지 않는다. 120/180초 paired 4건의 가격 변화는 진단값이고 실제 fill/terminal/cost model 미검증 때문에 delay 선정과 EV는 null, incumbent carry다. 당일 제출 census 0을 누적 committed 28과 혼동하지 않는다.

outcome labels 15건 중 mature 9 / partial 6이지만 원 canonical input bundle·exact context·provider-enforced schema/semantic receipt가 없어서 primary diagnostic 적격 0, label contract source gap 15다. 후행 가격 수신만으로 원 판정 입력을 재구성하지 않는다. 원천 손실은 각 label의 owner/closure test로 보존하며 별도 기계/compact 모집단의 적격성을 이 숫자로 대체하지 않는다.

### 21:17–21:19 실제 EOD 복구 수용

복구 PID 2964380은 exit 0, exact-date EOD는 21:17:36 `completed_with_warnings`로 종료했다. 오늘 2,627종목의 mandatory OHLCV 결측·비양수 가격·음수 거래량·가격 경계 모순은 모두 0이다. 복구 전 68개 날짜의 행 수 감소는 0이며, 9/28·9/30은 각각 1→2,628행으로 복원됐다. 비교 구간 전체는 93,581→185,376행이며 원 수신-key upsert 181,048행은 순증 행 수와 구분한다. [복구 후 census](../../data/runtime/postclose_recovery/2026-10-02/eod-recovery-after.json)에 보존했다.

추천은 21:17:35 생성, latest date 10/2, candidate 297 / safe pool 3 / selected 2로 갱신됐다. 기존 ML 모델 결과이며 퇴역 AI Score의 복원이나 실제 주문/경제성 증거가 아니다. 미수신 48종목에는 기존 namespace 손실/원 universe 결손 44종목과 OHLCV 20행 미달 4종목이 포함된다. 진행 중 run의 기존 intake 결손을 새 후보 코드로 소급 지우지 않는다.

eligibility는 PARTIAL 2,630 / UNKNOWN 45다. 005930의 KRX regular/NXT는 true, KRX aftermarket는 null이며 주요 PARTIAL 원인은 `krx_aftermarket_eligibility_unknown`이다. 공식 field 미제공을 유효 aftermarket 권한으로 추정하지 않는다. UNKNOWN의 phantom identity는 승인 후보의 lossless intake에서 격리한다. 관측 계약 revision은 기존 producer의 `234560d...`이며 이번 코드리뷰의 upstream HEAD와 구분한다.

Main은 21:18 EOD receipt를 자연 소비하고 정규 wrapper의 기존 BOT_ACTION=stop을 실행했다. Widget도 EOD hash를 결속해 running으로 전환했다. archive는 21:18:01 DONE, retention 0이다. machine final refresh는 Widget 선행 systemd job 대기이며 전일 status 75를 오늘 실패로 집계하지 않는다. Main의 첫 resource wait는 봇 종료 직후 이전 sample 3,861.8MiB로 발생했고 실제 가용 메모리는 4,537MiB로 회복됐다. threshold는 변경하지 않는다. 전체 장후/정책/strict/controller 수용은 아직 진행 중이다.

| Owner | 실행 (00:01 추가 전환 기준) | 의미·원천 검증 및 다음 경계 |
| --- | --- | --- |
| EOD + recommendation / archive | succeeded with source warnings / DONE | 2,627행 OHLCV 결함0·68일 행 감소0·추천 selected2; 미수신48/eligibility 결손은 격리 유지 |
| Main 원천 preflight | 이전 복구 succeeded, 신규 native running | raw 적격26,670/요약26,670/ledger issues0. 신규 코드·원천 세대 검증 유지 |
| main_machine_policy | succeeded, native 재검증 예정 | 적격 KRX2,975, carry·runtime apply false; full Main/compact 모집단과 합산 금지 |
| scale-in / entry split / cancel wait / initial quantity | 산출물 생성, native 재검증 예정 | 실제 fill/submit0, 계약 결손/유효 no-submit/carry를 구분. EV null |
| pre_submit_delay | succeeded이나 compact 세대 변경 | 누적28·horizon별 quote/route/epoch 결손; 최신 compact 이후 최소 재생성 필요 |
| outcome_labels | succeeded, native 재검증 예정 | 15건 mature9/partial6; 원 exact context/receipt 결손15. 후행 가격으로 원 판정을 합성하지 않음 |
| legacy_machine_report | succeeded, native 재실행 예정 | exact machine3,490, KRX89/장전91 후보 search 완료. 실제 운영 결속 결손·EV null·승격 false |
| main_auxiliary_policy | 23:22:53 succeeded | 15개 경제성 입력 모두 계약 제외·incumbent carry. 누적 behavioral17 적격과 경제성0을 구분 |
| episode_policy / research_allocation | OFF | OFF 연구 복원 없음. 기존 applied/live custody와 별개. 새 source sequence의 Episode 실제 pin/PID는 후속 OPEN |
| widget_policy | 네 producer succeeded | 98개 observation seed, live 신규0, withheld100; exact dated carry. selected bd/actual 독립 pin 재검증 필요 |
| research_capacity | succeeded | 22:15 native cash/inventory receipt. recovery에서 원 receipt 재사용, 재조회·과거 합성 금지 |
| collector_recommendation | succeeded이나 labels 세대 변경 | no qualified candidate·collector 생성0. 최종 labels 뒤 최소 refresh 필요 |
| machine_attribution / timing / weakness / approval | 수리본 succeeded | v4 loaded·anchor0/5·gaps753, timing carry, weakness report-only/carry; 최종 입력 세대 대사 |
| breadth / WS finalize / classifier / postclose_exit4 | 산출물 생성·snapshot hash 검증 PASS | breadth65, classifier valid-empty, 실제 오늘 완료 거래0; snapshot 재사용으로 새 체결/순익을 주장하지 않음 |
| summary/tower/checklist/strict/controller/tuning | bd scoped verifier FAIL 보존,639 native running/전체 controller waiting | 최신 모든 terminal→같은 generation→strict→whole done 필요. summary_verified만으로 종료 금지 |
| finalization/cleanup/final detector | future due | 10/6 05:00 정식 owner·06:00 wait/06:50 hard deadline. 현재 실행 성공으로 표시하지 않음 |
| next PREOPEN/startup | future due, prepared pending | 10/6 exact Main/compact·Widget·Episode loader의 준비본 검증 필요. PREOPEN07:35/PID/주문/순익 별도 |

## 00:11 보관 생산자 결함과 00:29 전체 복구

639 native run `09e8cc2fcb144d9b81c1ccbf5c2cb82a`은00:10:20 exit0/strict issue0/DONE이다. Main 계산은378.627초, compact00:09:59 succeeded다. 수리본 machine 그룹에서는 부모 collector00:11:52/attribution00:12:18 완료 뒤 consumer가 시작해 timing/weakness/approval은 모두 succeeded다. 부모·후행 경합 수리는 실제 실행에서도 확인됐다.

그러나 설치 tuning monitoring의 기존 `compress_db_backfilled_files --days 0 --date 2026-10-02`가 Main DONE만 소비한 뒤00:11 raw 및 청산 snapshot3개를 압축했다. manifest 존재/DB 적재를 후행 canonical 파일 소비 완료로 취급했다. holding summary는 원 `.json` 부재로 정책 결손을 보고했고 pre-submit은 raw representation 변경을 차단했다. tuning의 기계적 DONE00:11:35를 의미 수용으로 대신하지 않는다.

[봉인 snapshot 복원](../../data/runtime/postclose_recovery/2026-10-02/manifest-snapshot-archive-restoration.json)은 새 계산 없이 gzip 해제 bytes와 원 manifest SHA를 대사한 뒤 `.json`3개를 atomic no-overwrite로 복원했다. 각 gzip도 보존했다. trade review 원본은 이미존재/원 SHA 일치다. raw는 기존 archive identity를 검증·재결속했고3.686초, 적격26,670 및 ledger SHA `638b043f...`는 동일하다. [raw 재결속 receipt](../../data/runtime/postclose_recovery/2026-10-02/archived-raw-producer-reseal.json). pre-submit 및 summary만 최소 재생성했다. failed final-audit 단독 시도는 explicit verified projection 인자가 없어 쓰기 전에 차단됐으며 원 audit를 변경하지 않았다.

수리본 controller는00:29:39 `done`/whole_native_chain_done_claimed=true,00:29:54 native controller wrapper DONE 및10/6 `prepared_verified`다. 별도 준비본 검증도 `current_full_contract` PASS/findings0. Main PID 실제 소비 false, 매매 재기동 없음. 기존 native/독립/old-controller 실패는 attempts/log에 보존한다.

후속 보관 producer 수리는 native 미종결·다음 KRX 정책일 미경과·전체 controller 미종결/미검증 시 해당 원천 압축을 보류한다. raw/snapshot/threshold snapshot/canonical context/summary/partition에 같은 custody guard를 적용하고 보류 사유를 산출한다. malformed/broken symlink receipt는 fail closed, 정책일 경과 후에도 기존 전체 controller 검증자를 통과해야 한다. 후보 `a151b7ebb3b41fec7b9b82ab46278b7ffa895557`은639 대비 source/test2파일이며 workspace/격리/immutable 각각146 PASS·compile/diff PASS다. 후보에서 기존 전체 controller receipt issues0,10/6 보호 사유를 확인했다. 현재639 선택/분석 pin과준비본은 유지하며 신규 common selector 및 prepared 재검증은 승인 대기다. 분석 pin/매매service 변경·전체 계산 재실행을 요구하지 않는다.

## 의미 검증 census와 복구 한계

아래 수치는 최종 native 이전 완료 producer의 원 분모이며 최신 소비 인계에서 다시 대사한다. 원천 결손을 정책 선정·신규 edge·0 EV로 바꾸지 않는다.

| 생산자 / 소비자 | 의미 결과·원천 결손 | 다음 owner / closure test |
| --- | --- | --- |
| EOD / 추천 feature | 오늘 OHLCV 결함0, 미수신48. 과거68일 보존 및2일 복구 확인. `00088K` 손실은 신규 intake 수리이나 기존 run에 소급되지 않음 | `update_kospi` → `recommend_daily_v2`: 신규 정규 producer의 lossless identity/대상일 source·모델 검증. UNKNOWN/공식 aftermarket null은 원 계약 유지 |
| Main full / operating handoff | machine3,490 수용. KRX2,976/장전514 외 등록 scope는 다른 cohort. 실제 운영 모집단 결속 부족으로 EV/순익 null | `ai_action_outcome_calibration` → `mechanistic_entry_runtime_policy`: exact attempt·policy·route·completed/cost 원 결속. 오늘 실제 주문0은 broker 실패가 아님 |
| compact / exact plan 경제성 | 원15건 중 stop distance11/semantic2/transport2 제외. 누적 behavioral17 적격과 primary economic0은 다른 분모. 원 writer plan/trace/owner seed 연결0 | `entry_setup_paired_replay_batch`/Main plan producer: 지원 scope·exact broker capacity·원 plan hash·terminal/cost 증거. 원 latency DANGER/guard 차단을 우회하지 않음 |
| label 진단 / collector | 15개 중 mature9/partial6이나 원 canonical input/context/provenance 결손. 후행 가격 cache4,042 재사용은 원 판정 복구가 아님 | `ai_decision_quality` → collector/compact: 원 실행 당시 요청·응답·schema·provider receipt 보존. 복구 불가능한 과거 입력은 명시 제외 |
| Widget 연구 / dated policy | catalog636 중100평가/536이월, 98 적격/2 history quarantine. observation98, 신규 live0, withheld100. 표준 source2,552 중 valid3/gap1,465/not-applicable1,084 | `widget_symbol_signal_policy_research` → `WidgetSymbolRuntimePolicyLoader`: qualified date/holdout·비용·signal/seed·exact route/BBO 계약과 dated carry. 001550/452260 history missing 유지 |
| Widget raw coverage / 연구 census | 실제 설치 collector priority는006800/010140/080220 세 종목. 전체 catalog를 enrolled로 부른 raw missing 분모는 설치 수집 scope와 구분해야 함 | `widget_research_watch_collector`/research population owner: 원 설치 scope/budget snapshot 결속. 설치 밖 raw absence를 collector failure 또는 유효 무신호로 주장하지 않음. env 확대·새 collector 없음 |
| Episode raw / attribution | legacy 같은 시각 서로 다른 상태106건·active anchor13개 부적격. 새 sequence 계약은 앞으로 생성될 원천만 수용 | `low_price_two_leg.machine` → `low_price_two_leg_tuning`: [10/6 OPEN](../checklists/2026-10-06-stage2-todo-checklist.md) `EpisodeCaptureSequence1006`, 별도 Episode 배포 권한과 실제 source sequence. 기존 raw 재라벨링 금지 |
| Widget exact route / attribution | active Widget session4·005930 NXT premarket route1 결손. 등록 manifest23/25 완료 및 `_AL` source가 `_NX` 직접 소비 증거는 아님 | 실제 Widget route owner: 원 item/type/epoch·session/owner anchor를 연결. 주문 구독을 바꾸거나 다른 route를 대체하지 않음 |
| timing / weakness / approval | attribution matched0/5, timing source-quality carry. weakness147 qualified60초 관측, 실제 비용 비교 부족. approval은 진단 후행이지 매매 승인 아님 | 해당 dated loader·approval producer: 최신 attribution generation 재소비, exact10/6 carry와 기존 hysteresis2/3 확인. 새 threshold 선정 없음 |
| scale-in / entry split / initial qty | scale-in actual fill0, entry split3 valid plan/3 blocked receipt·real submit0, initial qty carry_parent. CF/미제출을 실제 체결로 합산 금지 | 각각 실제 plan/submit/fill/terminal/cost source owner. 기존 quantity/guard·AVG_DOWN custody 보존 |
| cancel wait / pre-submit | cancel wait 제출 census0·불확실 custody0은 유효 no-submit carry. pre-submit 누적28, 실행 지연 모델 미검증·EV null·가격 pair4는 진단 | `entry_cancel_wait_tuning`/`pre_submit_delay_tuning`: frozen inventory/source ledger·최신 compact projection 재소비. 과거 source gap 승계와 미래 자연 제출 별도 |
| holding / post-sell / missed CF | 오늘 completed/entered/full/partial0. holding strict eligible0·old unsealed completed IDs는 오늘 cost/PnL 근거가 아님. missed CF는 가격 연구 | snapshot 직접 consumer: 정확 postclose_exit4 hash/date·현재 policy/cost 계약. legacy display0을 비용 후 실제 손익으로 바꾸지 않음 |
| research capacity / allocation | 22:15 원 cash/inventory receipt complete, 원 auth refresh/order/candidate API calls0. Episode OFF로 joint allocation OFF | `research_native_capacity_source` → family refresh: recovery에서 원 receipt 검증·재조회 없음. OFF 연구 복원 없음 |

원천 부족 scope는 해당 direct-family OPEN에 전달하고 유효 incumbent carry를 별도로 검증한다. 반복 계산으로 과거 미수신 receipt/체결/비용을 생성할 수 없으므로 동일 입력 무한 재실행을 하지 않는다. 미래 자연 표본의 수익 개선은 오늘 장후 기계적 정상 종료 및 다음 날짜 준비본 통과와 다른 수용 경계다.

## 종결 조건

내부 producer까지 실행 terminal·분모·필수 source schema/date/hash·분석 판정·정책 및 intended consumer를 대사한다. 복구 가능한 결함은 수리·표적 검증·최소 재생성 후 다시 리뷰한다. 원천/비용/후행경로가 복구 불가하면 source gap과 owner/closure test를 남기고 적격 incumbent carry를 검증하며 결측을 0이나 유효 empty로 바꾸지 않는다. 예약 전 PREOPEN/PID를 미리 성공으로 표시하지 않는다.

## 00:40 이후 최종 실행·체크리스트 generation 대사

독립 machine 수리본 wrapper의 최종 재실행은00:39:59 exit0이며 capacity의 기존22:15 검증 receipt를 재사용했다. 각 부모 완료 뒤 후행을 실행하고 전체8결과는 succeeded/유효OFF다. 원 unit의22:31:52 exit1은 과거 실제 실행으로 보존한다. source-only wrapper 복구의 exit0·stage 검증을 대조한 후 해당 독립 분석 unit의 failed 표시만 reset했다. start/restart는 실행하지 않았고 unit ExecMainStatus1을 신규 성공으로 바꾸지 않았다. [복구 종결 영수증](../../data/runtime/postclose_recovery/2026-10-02/machine-group-recovery-close-63936cf1.json)을 따른다.

00:43:43 전체 controller done 뒤00:43:56 다음10/6 checklist에 다른 작업의 인계가 추가됐다. strict의 원 checklist SHA `9870ffd8359b7303e82579a0f553a19129c1222a1720b2a7c6bc59b10b5663da`와 현재 `3c31c475059113f07a37b059b04029403e2e567b913dd02a9076172b8a0ca9c5`가 달라 준비본 생성은 `strict_generation_changed_during_recheck`로 exit1이었다. 읽기 전용 재검사에서 checklist만 변경됐고 summary/Main terminal/각 producer stage는 동일함을 확인했다. 다른 작업의 추가 인계를 보존하며00:52:26 선택639의 summary/controller/체크리스트/준비본 연결만 재검증한다. Main/Widget 연구 전체 계산·계좌/AI 호출·매매 재기동은 추가하지 않는다. 앞선00:29 PASS는 당시 generation의 이력이며 최신 완료 판정으로 재사용하지 않는다.

최신 controller wrapper는00:54:41 exit0/DONE이며 전체 controller `done`·모든15 stage issue0/유효terminal이다. 최신 controller SHA `adf73d4ac8bb15153eb2db03ae2780097e1a491f51593ebff11adda8e3f62285`, summary SHA `34829f81a39457a811cf8b8dd945ac1212d7b66367246b7f3cc4ec94bace330c`, Main/compact 10/6 policy SHA `58dcce5f8cfc4d945098fb774359625af657f0da35d7948da374fb311226c98c`다. 이 generation의 준비본은00:54:41 `prepared_verified`이며 실제 PID 소비 false다. 다른 작업의 checklist 추가 인계를 보존했고 가드 완화 없이 최신 strict로 다시 봉인했다.

별도 최종 `next_preopen_readiness --verify --target-date 2026-10-06`는 `current_full_contract` PASS/findings0이고 release-set124 owner/122 Episode unit/366 policy pin도 PASS다. [현재 chain·준비본 closure](../../data/runtime/postclose_recovery/2026-10-02/current-chain-prepared-closure-63936cf1.json)에 현재 selector/controller/strict/준비본 SHA와15 stage issue0을 함께 기록했다. 신규 edge/candidate0·경제성 source_gap을 유효 승격으로 바꾸지 않았으며 기계적 완료와 날짜별 incumbent carry 준비를 구분한다. 현재 수행 중 장후는 종결됐고10/6 05:00 정식 finalization·cleanup·final detector 및07:35 PREOPEN/07:55 startup는 future due다. 현재 Main PID는 not_attested/actual_pid_consumed=false다. a151 보관 재발 방지의 common selector 전환은 여전히 사용자 승인 대기이며 분석 pin639/매매 service는 유지한다. 문서 print-only parser/diff 검증 PASS, 외부 sync는 실행하지 않았다.
