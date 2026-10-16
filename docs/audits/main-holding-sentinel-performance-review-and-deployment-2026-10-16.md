# Holding sentinel 반복 읽기·계산 개선 및 배포 검증 — 2026-10-16

## 범위와 승인

사용자는 holding 지연 분석 후 코드리뷰·수정보완·배포·재기동을 승인했다. [원인 분석과 기동 후 검증](main-postclose-source-gap-final-release-review-2026-10-16.md)의 후속 구현이며 기존 `HoldingProfitExitSourceContractRepair`와 `DirectFamilyPreopenPolicyHandoff`를 사용한다. 정책·provider·주문·수량·threshold·freshness·Main/manual/retired custody와 원 결손을 보존한다.

기준 selected release는 `63b758ac8e98ace56e62419b677f374449fd724f`, Main PID `3474098`, start ticks `18613546`이다. 기존 격리 작업트리 `postclose-source-gap-final-release-20261016`의 `178b3bbae607d65a6a681c787185643cc29b92c4`에서 진행했다. 다른 workspace 수정은 통합/정리하지 않는다. source 위치는 기존 report producer `src/engine/holding_exit_sentinel.py`, 회귀는 기존 `src/tests/test_holding_exit_sentinel.py`다. 새 engine-root 모듈을 만들지 않는다.

`e9cfb9bcaf4f84491d4593587bc48c2bdde4ae85`는 Git 조상 자체가 아니라 63b의 통합된 코드 내용으로 포함된다. 원 변경 23개 파일 중 19개는 blob이 동일하고 4개는 최신 SOR/체결 시각/필수 TP source 보완을 포함한다. e9를 다시 merge할 때 생기는 차이는 coverage 초기화의 이전 위치 재추가뿐이다. 현재 코드는 동일 BUY identity의 `begin_coverage`를 cap 조기 return 전으로 옮겼으므로 중복 실행을 복원하지 않는다. 이번 변경은 그 23개 파일을 다시 수정하지 않는다. 증거: 정규 workspace `tmp/holding-sentinel-performance-20261016/e9-inclusion-check.json`.

## 구현과 리뷰 보완

1. scope 귀속은 record별 explicit timestamp를 한 번 정렬하고 이분 검색한다. 좌우 최단 거리·동일 timestamp의 복수 scope·동률 conflict·invalid record·원 event 순서를 유지한다. 같은 event의 scope parsing도 한 번만 수행한다.
2. 전일 비교만 native cache 세대에 결속한 작은 투영을 재사용한다. 원 source cache의 증분 유지·행 census 뒤 native writer의 shared lock을 잡고 전후 inode/ctime/mtime/size 및 전체 행 수를 확인한다. reader/store 코드 해시·필드·열 계약이 달라지면 재계산한다. 현재 일자 인과 감사는 모든 원 fields를 계속 읽는다.
3. 전일 투영은 요약에 필요한 43개 고유 필드와 원 identity/header를 보존하며 compact column 배열로 저장한다. 실제 전일 투영은 26,344,275 bytes로 기존 32MiB 캐시 상한 안이다. 원 478,787,144-byte source cache와 raw/receipt는 변경하지 않는다. 상한을 넘으면 공용 helper의 계산 fallback을 유지한다.
4. stage별 unique attempt는 stage마다 전체 행을 다시 읽는 대신 한 pass에서 모은다. 동일 입력 generation의 사전 중복 hash는 제거하고 native auditor가 최종 date/cutoff 필터 후 한 번 계산한다. 독립 원 report/generation 검증을 제거하지 않는다.
5. 초기 실제 자료에서 큰 dict 투영이 캐시 상한을 넘는 문제가 나와 column 형식으로 줄였다. 직렬화 후 list가 되는 tuple을 contract에 남기면 warm reuse가 실패하는 문제를 회귀에서 재현했고 list 계약으로 수정했다. warm run에서 전일 source cache를 열면 실패하는 테스트, source append/hash/code 계약 변경, source mutation/population, nearest 동률/정렬/invalid ID 및 거리 계산량 상한을 확인했다. summary consumer의 필드 추가가 projection 누락으로 이어지지 않도록 필드 계약도 검사한다.

## 동일 원천 parity와 성능

처음에는 이미 append된 입력을 과거 보고서와 비교했고 격리 worktree의 policy selector가 없어 binding gap이 났다. 이 실패를 PASS로 쓰지 않는다. 실제 selected release의 변경되지 않은 정책 consumer를 사용하고, 원 native generation SHA가 정확히 일치하는 원천 prefix 36,103개를 고정했다. 당시 cache snapshot 이후 append된 16개는 이 private 역사적 parity에서만 제외했다. 원천·정책 검증을 bypass하지 않았으며 정규 보고서의 현재 입력은 제외하지 않는다.

- 원 기준 시각: `2026-10-16T13:00:05.562981+09:00`.
- 원 generation: `c55c7bd09de83eabde317e399bcc92c84089200b5a39660bcf50307ba57bcd52`.
- **전체 report dict 동일**, 달라진 top-level field 0. 과거 source gap 5건·policy/runtime 소비·scope/분모·baseline/분류를 포함한다.
- 전체 candidate warm run 2회: **5.580 / 5.585초**. 원 운영 wrapper 12:48 시도는 339초였고 13:00 시도는 365초였다. 각 측정의 실행 환경/원천 snapshot 차이는 보존하며 운영 개선율은 새 배포의 실제 wrapper로 확인한다.
- warm 전일 native cache read **0회**를 실제 open guard로 확인했다. 전체 프로세스 read characters 약 462.3MB로 원 951.3MB보다 작다. 현재 일자 원 fields와 정책 ancestry 검증은 유지했다. 기존 479MB 전일 cache는 26.3MB 투영으로 재사용한다.
- 측정 프로세스 peak RSS는 **468,492 KiB**, 원 프로세스 관측 RSS는 851,944 KiB였다. peak/current RSS의 차이를 보존한다.

원본 실패 시도와 최종 증거는 정규 workspace `tmp/holding-sentinel-performance-20261016/`에 둔다: `holding-tests-{first,second,third}.log`, `exact-input-parity.json`, `verified-exact-input-parity.json`, `verified-native-parity-benchmark.json`, `final-integration-tests.log`. 후자의 검증된 native parity만 수용 근거다.

## 검증과 운영 수용

구현→self review→보완→재리뷰 뒤 **2,679개 회귀 PASS**(21.61초), 변경 Python 2개 compile, 문서 print-only parser·link·diff 검사를 통과했다. 리뷰 범위 미해결 finding은 0이며 원 WARN/unknown을 성공이나 0원으로 바꾸지 않는다. entry_cancel_wait/rising_missed/auxiliary/holding_vote 네 capability 구성 해시가 실제 selected release와 모두 동일함을 확인했다. 원 exact-code fixture를 재사용하며 같은 fixture를 다시 생성하지 않았다. 증거: `capabilities-unchanged.json`.

승인된 후속은 clean immutable release 생성→현재 정책/PREOPEN·PID·broker/WS 확인→정규 ordered drain/select/start→새 PID 소비→기동 이후 새 holding/BUY 보고서→정확한 보고서 SHA를 소비한 full detector다. 기동 전 보고서·이전 PASS·selector만으로 종료하지 않는다. 배포 terminal/실제 지연/남은 source acceptance는 후속 영수증을 아래에 추가한다.


## 13:26 실제 성능 배포와 기동 후 수용

성능 커밋 `59c92909783e967397a8d774bab60cd22ec78c96`를 정규 ordered 경로로 배포했다. 13:26:11 terminal PASS, Main PID3600286/start18867646이다. 이전 wrapper의 늦은 완료는 새 기동 수용에서 제외했다. 새 native holding 보고서는13:26:42/asof 이후 생성됐고 실제6.42초·peak469120KiB, SHA `05b25da618a84a5a767fc8cb1941040d2d9eea8180f347a53e37d5f0a483262a`다. policy/runtime gap과 native finding은0, 과거 first-crossing5건은 source_gap으로 보존됐다. BUY는13:27:26/SHA1814bce3ef0070429075afb9465b7e80be0c8f4ddeac2efddb34f85d871f0b17, completed/bounded_no_applicable_observations/unmet0이다. native 정규 full13:29:27은 두 SHA를 직접 소비하고 FAIL0·health6PASS를 확인했다. 수동13:28 full의 resource-wait는 수용 PASS로 사용하지 않았다.

broker KR/NXT 재동기화·현재 Main036930 1주 및 수동042660/475150 보존·미체결0, 새 PID/transport epoch의 fixed5종목0B/0D 실제 수신을 확인했다. bootstrap JSON/env·prepared index·수동 제외·원 editable checklist bytes는 모두 불변이다. 이 수용은 자연 TP 새 양성 표본·실현 비용 회복·경제적 성과를 증명하지 않는다. 증거: 같은 tmp 디렉터리의 ordered-deploy-result, postrestart-holding-timing/native, natural-postrestart-full-detector, postdeploy-release-set/frozen-check, postrestart-ws-receipts/snapshot JSON.

## 13:30 동일 결손 반복 통지 원인과 보완

사용자 경보13:30:17은 위05b 보고서의 동일5개 결손이다. 기존 semantic fingerprint가 generation과 release별 absolute artifact 경로를 포함해 재게시/재배포를 새 사건으로 취급했다. 새로운 원천 결손으로 판정할 증거는 없다. 원 기록을 새로 만들 수 없으므로 source_gap 경고는 유지한다.

보고서 검증 이후 전체 source_gaps/details/lifecycle을 대조해 position·BUY fill identity·signal·원 사유·sampled-grid 소진 disposition을 결속한다. native v2·정확한 full census·유일 identity·추가 finding/정책/런타임 gap 부재를 만족한 missing-crossing만 최대128개로 안정 식별한다. 하나라도 누락·모호·변경·다른 결손이면 기존 generation 기반으로 계속 경보를 낸다. 다른 stage의 identity·cooldown·delivery/retry·거래 동작은 그대로다.

기존 발송 key 이행은 같은 원 보고서 SHA·날짜·native complete binding으로만 허용한다. 이미 식별된 사건을 다른 identity로 덮어쓰는 초기 결함을 회귀에서 재현하고 수정했다. 발송하지 않은 경보를 발송 완료로 이행하지 않으며 원 세대와 파일 경로는 관측 provenance로 보존한다. 다른 과거 세대는 동등하다고 추정하지 않으므로 처음 한 차례 신규 통지가 가능하다. fake sender 회귀와 private state 사본으로 검증하며 운영 Telegram 수동 발송·state 삭제/수동 편집은 하지 않는다.

기존 producer/monitor/notifier와 기존 test 모듈만 보완한다. source_gap 상태 및 미복구 disposition·원 source bytes·정책/quantity/provider/threshold/safety는 유지한다. 구현→리뷰→보완→재리뷰, 관련9개 모듈 **2,707개 PASS(20.97초)**를 확인했다. 마지막 exact binding 조건 보완 뒤 notifier/artifact 회귀와 compile/diff/parser를 재확인한다. 새 release 선택·기동 후 native 소비·정규 notifier의 동일 사건 중복 억제는 별도 후속 수용이다.


## 동일 사건 알림 수리의 실제 배포·소비

소스 커밋 `48968ade9022fcfaf69b9c081f703be3324d33c0`를 `holding-gap-incident-20261016-48968ade9` 불변 release로 배포했다. 정규 ordered terminal은13:42:08.954319 PASS, Main PID3646205/start18963364이다. 이전59c/PID3600286은13:40:49에 정상 drain됐다. 기존37개 native 정책 파일이 같아 원 exact parity를 재사용하되 새 리뷰/시험을 새 code handoff에 결속했다. 정책 재선택·bootstrap JSON/env·prepared index·수동 제외·원 editable checklist 변경은0이다. 관련2,707개 회귀 후 최종 결속 조건을 보완하고287개 targeted 회귀·compile·diff·print-only parser를 다시 통과했다.

기동 이후 직접 생성한 native holding은13:42:30.150812/SHA46f9de3c4d835f6d88c9f9f88e4974dc991536cb6e6a0e0f9adb79c0c565aa0a,6.56초/peak484908KiB였다. 새 PID를 포함하고 policy/runtime gap·native finding0, 원5개 source_gap 그대로다. 새 BUY는13:43:19/completed, 현재3646205 actor가 결속됐다. coverage partial은 기록된 guard/cohort 대기이며 unmet_conditions[]다. scanner 분모의 자연 평가가 없다는 상태를 fixed-watch 관측으로 대체하거나 full PASS로 만들지 않는다.

수동 full13:43:34는 정확한 위 holding SHA를 검증하고 FAIL0·health6PASS였다. 정규13:45:23은 resource contention/deferred로 수용하지 않았다. 정규 Main full13:46:39는 기동 후13:45:05 holding SHA99ea377fdf7adaeaf16463adbb6935552dbaa806f357d6e233d484c369bb7d92를 native complete로 소비했고, BUY13:45:40/SHAa9532767ae5b485cf364b8d0ae1a553e06c1e9b9ef88c81e67daedf38a7bbe41의 completed·current actor verified·bounded pending을 확인했다. 원 policy_generation 두 warning 및 holding 원5건은 유지한다.

13:50:17 정규 notifier는 원 발송 기록에 없던 새 identity를 최초1회 통지하고 실제 운영 state에 기록했다. 원 legacy 보고서012cc9…와 새 보고서99ea…가 달라 같은 bytes의 무통지 이행 근거가 없었던 경우다. runtime state를 지우거나 발송했다고 수동 조작하지 않았다.13:51:48 정규 full이 이후 holding13:50:07/SHAd37ca3be491124d8bbbb70fef26ff67fd07c172f8045348fa0837170e96d3e35를 소비한 결과를 실제 운영 state 사본으로 재생하자 duplicate_incident·추가 발송0이었다. 이 private 재생은 fake sender만 사용했고 운영 발송 완료로 기록하지 않았다. 다음 예약 주기의 실제 결과를 아래에 별도 기록한다.

KRX/NXT 모두 complete·inventory/open-order row valid·native checkpoint digest·query/journal generation 일치를 확인했다. 전후 Main036930 1주와 수동042660 10주/475150 20주가 같고 미체결0이다. fixed5종목은 새 PID/commit/transport epoch1792125715887487에서 실제0B/0D를 받았다. REG 전송만으로 수신을 인정하지 않는다. 원5개 미기록 전이의 복원·신규 mandatory TP 양성 영수증·실현 비용/수익 성과는 이번 알림 수리로 증명하지 않는다.

증거는 정규 workspace `tmp/holding-sentinel-performance-20261016/`의 incident-* 파일이다. 특히 incident-review-validation, incident-ordered-deploy-result, incident-postrestart-holding-timing/native, incident-natural-postrestart-full-detector, incident-notify-state-first-stable, incident-natural-notifier-first-report, incident-operating-state-new-generation-replay, incident-broker-before-after, incident-postrestart-ws-receipts, incident-postdeploy-frozen-check를 구분해 보존한다.13:45 defer 및 predecessor BUY13:40 관측도 보존하고 새 기동 증거로 사용하지 않는다.


13:55:18 정규 full/notifier에서 실제 후속 세대까지 수용했다. holding SHA가99ea…→d37ca…로 바뀌고 native_validated/observation_complete=True·원5건 source_gap 상태가 유지됐으며, 운영 state의 사건 key는 d233f7ee1fd7ed0dd59e62099e37e9bf6daa06543bf6552ef9fdd77d6a899828로 동일했다. wrapper 결과는 **duplicate_incident**, last_seen13:55:18·last_sent13:50:17 불변으로 **추가 통지0건**이다. 최종 source·PID·hold 제거·동결5개 파일도 재확인했다. 구현/배포 및 오늘 동일 사건의 재통지 수리는 닫고, 원5건 미복구·다음 mandatory TP 자연 양성·경제성 OPEN은 기존 owner에 유지한다. 최종 증거: `tmp/holding-sentinel-performance-20261016/incident-final-verification.json`, `incident-native-second-notification.log`, 두 정규 report/state 사본. 미래의 새로운 결손·사유·BUY/signal 변경이나 부분 관측에 대한 새 경보는 계속 허용한다.
