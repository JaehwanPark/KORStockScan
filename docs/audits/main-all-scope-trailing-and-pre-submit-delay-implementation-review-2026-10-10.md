# 전체 범위 트레일링·제출 지연 초기정책 구현 리뷰

검증일: 2026-10-10 KST

판정: 공통 코드·격리 회귀에 대해 구현→리뷰→보완→재리뷰를 수행했다. **전체 계획 수용은 아직 OPEN이다.** 전수 원천 연결, 대용량 처리와 전체 장중·장후 성능의 미완료를 단위 테스트로 대체하지 않는다. 최초 구현에서는 운영 정책 발행·선택·장후 재실행·배포·재기동을 수행하지 않았다. 이후 승인된 코드 리뷰·배포 결과는 아래 후속 기록으로 구분한다.

대상은 [전체 범위 트레일링 계획](../proposals/main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md)과 [제출 지연 초기정책 계획](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md)이다. 선행 Main PASS 보완과 사용자의 기존 문서 변경을 보존했다. 신규 Python은 scalping/lifecycle/automation 및 기존 tests 역할에 배치했으며 engine-root 모듈·worker·cron·DB를 추가하지 않았다.

## 구현과 반복 리뷰

| 경로 | 구현·수정 | 검증 근거 |
| --- | --- | --- |
| 누적 입력창 | [window generation](../../src/engine/lifecycle/holding_window_generation.py), archive·holding report·selector·summary에 소비 날짜 전체의 projection/census/cost/profile/cutoff를 결속. 작은 dependency receipt와 공유 64MiB resident-data 예산 | 과거 날짜 비용 정정의 stale reuse/reseal 거절. 파일 읽기로 바뀐 atime은 원천 변경으로 오인하지 않음 |
| 공통 scope·재생 | [scope](../../src/engine/scalping/main_exit_scope.py)의 여섯 disposition, [universal replay](../../src/engine/scalping/universal_trailing_replay.py)의 actual completed/actual-entry alternative/ENTER+PASS CF 분리. 공통 M1·trailing·유예·session kernel과 ADD/익일 상태 승계 | 세 시장·다른 종목·route/epoch 전환·부분 잔량·실제/모델 손익 구분. 완료일 증빙 없는 실제 cohort는 selector 표본 수용으로 승격하지 않음 |
| 상황 정책 | [typed policy](../../src/engine/scalping/trailing_situation_policy.py)의 causal feature·네 유형·원 pin 영속화·원 classifier/current effective hash 분리. 등록된 유한 grid에서 train 선택 후 holdout 고정 | 미래 feature는 BASE/source gap. 학습 1위가 검증에서 실패해도 2위로 재선정하지 않음. M1은 고정하고 초기 12-cell은 승인 부모를 계승 |
| 기존 selector 연결 | 실제 selector 보고서/정책의 byte-pinned 참조를 준비 단계에서 검증. 큰 연구 객체를 장중 env에 반복 삽입하지 않음 | 실제 파일 바이트 SHA와 객체 SHA 혼동 수정. classifier·type·시장·부모 결속, 여러 시장 canary 합성 거절. 경제 변경을 parent-equivalence로 표시하지 않음 |
| 격리 연구 | [all-scope CLI](../../src/engine/automation/main_trailing_all_scope_research.py)의 봉인 manifest·scope/position partition·alias dedup·최소 checkpoint·공통 cohort 두 단계 집계 | 같은 세대 resume의 source JSON decode/replay 0. 손상 checkpoint는 해당 partition만 재구축. numeric 후보/부모와 독립인 source-feature spool·분할 path를 지원. 집계 중 비용/코드 변경이면 최종 report/policy 미발행 |
| 제출 지연 v2 | [initial policy](../../src/engine/scalping/pre_submit_delay_initial_policy.py)의 두 anchor·원 신원/부모·P0 자격 후 공통 chronological split/purge·train 최선 고정·0초 fallback·committed generation/CAS | durable JSON multi-horizon 해시 수정. 원 identity 검증 후 최소 필드·full-field conflict SHA를 보관하고 공유 resident budget에 동적으로 접수. price-ready에는 원 계획수량 필요; signal 가격 진단은 수량 없이 가능. 잘못된 native 타입·부모 결손은 양수 지연을 허용하지 않음 |
| 원 PASS·due·관측 | [observer](../../src/engine/scalping/pre_submit_delay_observation.py), coordinator/WATCHING·실제 제출 함수·bootstrap을 연결. bounded heap·기존 writer의 category reserve/공정 drain·one-time native successor | scanner/fixed-watch × auxiliary v1/v2 제출 body fixture. 원 lease/deadline·cap·수량·부모와 due+기존 budget 보존. 재arm·미확정 주문 재전송 없음 |
| warm·원천 재사용 | 공급받은 WS를 route-owned touch/tape 배열로 compact화. source-projection 계약과 consumer/selection 코드 계약 분리. 늦은 callback에도 원 발생일 보존 | full/compact M1 decision·state 동등. 120+120 이력의 native 시각/sequence를 손실 없는 상대값으로 저장하고 12KiB envelope 상한을 검사했다. 같은 source에 consumer만 바뀌면 source JSON decode 0으로 다시 선정·봉인. warm policy lookup I/O 0 |

새 AI 재생 검사는 원 quote 해시만으로 판정을 재사용하지 않는다. 최초 crossing의 정책값·M1 classifier·강약·보유/peak/arm/pin 문맥을 기록된 AI 입력 영수증에 결속한다. 영수증 자체를 따로 봉인해 quote hash와 순환 참조하지 않게 했다. 같은 호가/시각에서 후보값만 바뀌거나 원 입력 결속이 없으면 `candidate_holding_ai_input_unobserved`로 검열한다. 실제 AI 입력이 없는 과거 응답을 합성하거나 재호출하지 않았다.

cost-only 정정에서 normalized 원천 bytes가 그대로이면 최소 결과를 재사용하고 낡은 actual economics를 미확정으로 바꾼다. frozen model-only 결과는 유지하며 clean recompute와 최소 결과/전체 집계가 같다. 새 비용 배분을 실제 원천에 반영한 경우 source bytes가 바뀌므로 정상 재생한다. 비용을 0으로 채우지 않으며 모델 비용은 명시적으로 모델이다.


추가 report producer는 `automation/main_trailing_path_projection.py`에 배치했다. 역할은 격리된 원천/feature spool이며 runtime worker·loader가 아니다. 원 입력의 segment 수·전체 event census·route/epoch/AI 입력 해시를 유지하며 4,000-event/4MiB 초과 경로를 일반 계산과 대조했다. cached 결과를 쓰더라도 원 leaf bytes를 최종 재검증한다. source-feature spool 상한 64MiB와 shared resident-data 상한 64MiB는 서로 다른 자원이며, 이를 각 family의 무제한 저장/메모리 허용으로 사용하지 않는다. 이미 식별된 malformed path는 해당 ID의 source gap으로 보존하고 건강한 position을 유지한다.

v2 최소 필드 scan은 총 원천을 한 번 decode하며 복제 원장을 만들지 않는다. 원 record identity를 확인한 후 full-field SHA를 남겨 사용하지 않는 필드의 충돌도 검출한다. retained row/index 접수 전에 공유 예산을 증가시키며, 후보 결과도 M1·result dictionary를 할당하기 전에 접수한다.
API wire request/parser/FID/auth/account/order/continuation은 변경하지 않았다. Kiwoom·AI·broker 호출은 0회다. 주문 검증은 격리 adapter fixture만 사용했으며 Main/manual custody와 퇴역 episode/widget 원 owner 경계를 유지했다.

## 실제 원천의 격리 계산

9/29 이후 10/8까지 compact 63개 partition, 469,427 bytes를 읽기 전용 참조했다. raw/family ledger의 exact 교집합을 확인하고 task-local 최소 report/policy/manifest만 저장했다.

- 원 commit 31, ENTER+effective PASS 진단 29, 유효 P0 기회 6, price-ready 가격쌍 21.
- PASS 29건 모두 기계·보조 부모 해시 결손이며 5건은 원 native 연결도 결손이다. 현재 양수 지연 적용 근거로 승격하지 않는다.
- quote generation/epoch 불일치 43, clock/hash 불일치 7, commit/PASS 부적격 2를 격리했다. quote 제외 횟수와 기회 수는 다른 분모다.
- 격리 결과는 `initial_baseline_immediate`, 양수 cell 0, 기본 0초. actual PnL·paired net EV는 null이며 가격쌍은 체결/실현손익이 아니다.
- 동일 세대 재계산은 `source_decode_passes=0`, `minimal_projection_reused=true`. 독립 byte/ledger 검증은 유지했다.

source SHA: `07834af274dceb46f25123da1d79c76c3abc5205f9dad7849e746777a6e34a5e`.

최종 격리 policy SHA: `4f7d628eb22986042b2c90b2116227094484d0ef5bd3844d7880ae789956c3e6`, committed manifest SHA: `8a6bd02c0b2d52004cb4d4c859efe491edd682f5c345c14c96391309667c2e81`. report 34,217 bytes, policy 3,060 bytes. 이 파일은 운영 소비·PREOPEN·PID의 영수증이 아니다.

현재 비용 inventory도 다시 읽었다. 9/29–10/8의 exact execution settlement receipt는 날짜별 0개이며 공식 비용 source 파일은 10/8에만 2,295 bytes로 존재한다. 파일 존재는 비용 배분 성공이 아니다. 공급되지 않은 비용·호가·native 증빙을 만들어내지 않았다.

## 성능 측정과 한계

source/workload/code/해상도/공유 예산을 후보 측정 전에 동결했다. 최종 코드 검증 뒤 같은 host의 새 Python process에서 baseline/candidate를 번갈아 각 3회 측정했다. baseline은 중복 source decode와 candidate 경로 준비를 재현한 계산 비교다. 과거 설치 release 전체 Main/job과의 비교로 사용하지 않는다.

| 고정 작업 | baseline wall ms 3회 | candidate wall ms 3회 | 중앙값 감소 | 판정 |
| --- | --- | --- | --- | --- |
| 제출 지연 계산 | 76.255, 76.654, 77.276 | 42.977, 42.894, 42.777 | 44.0% | 동일 / wall·CPU·RSS 비악화 |
| 트레일링 재생 | 130.610, 129.948, 130.060 | 49.106, 49.099, 49.179 | 62.2% | 동일 / wall·CPU·RSS 비악화 |

제출 지연은 동일 21쌍에서 source decode 3→1회, 트레일링은 30 position×9 alias에서 M1 경로 준비 270→30회다. 비교 semantic hash는 각각 같고 필수 byte 검증은 유지했다. RSS는 fresh-process high-water이며 전체 Main 메모리 감소로 일반화하지 않는다.

10,000종목×8경로=80,000 scope와 실제 source snapshot을 동시에 보관한 합산 입력 시험은 claim 44,715,416/67,108,864 bytes, RSS 증가 30,508 KiB, peak 80,680 KiB, wall 0.883초였다. 이는 scope/상주 입력 시험이며 80,000범위 전수 경제 replay 또는 Main+due+청산의 합산 성능 PASS가 아니다. 64MiB는 공유 resident-data allowance이며 Python 전체 RSS 한도가 아니다.

budget SHA: `d1754efdd7df2db8430bef382218b9e056a835606aec58b24ea10fb9ffae0ce7`. 최종 code contract: delay `aae86014ede7b56c5e5faef3222c8842579706ad999c28130b5ccbe4e4ba9303`, replay `05f5d60e79c1c1de47e2d9bd321ced279ab073142e68fab401d2bd370569bf2a`.

근거는 `tmp/all-scope-trailing-delay-20261010/`의 `final-performance-budget.json`, `final-performance-results.json`, `final-combined-budget-result.json`, `final-real-source-result.json`, `final-cost-inventory.json`, `final-validation.log`, `final-type-reference-validation.log`, `final-path-validation.log`, `streaming-delay-validation.log`다. full raw/AI 비교 원장을 복제하지 않았다.

## 검증

- 영향 suite 32개: 1,764 passed / 39.35초. 이후 손상 spool의 크기 재계수·source-date 검증 보완의 관련 suite 37 passed / 6.40초.
- 실제 자료의 격리 발행·durable 재읽기·loader dry-run·warm projection 재사용 통과. 다중 horizon·consumer 코드 변경·wrong native 타입·늦은 비용/코드 변경·AI 입력 변경·selector byte SHA·warm I/O·partial/ADD/익일 회귀를 수행했다.
- 최종 compile/diff/문서/print-only parser 결과는 검증 종료 기록에 남긴다. wrapper는 수정하지 않아 신규 bash 검사는 해당하지 않는다.
- 10/9·10/12 checklist SHA를 보존한다: `8eb45bab1300fdd67953739408fa60e7691c8e61afbaf4a5e999dd70055d462d`, `9e7d9f001a13cfac3b0fbd566bcfa860bd598ce41a9d1280437dcccaefff40a3`. 기존 selected release/PREOPEN은 새 코드 적용 증거가 아니다.

## 전체 계획의 미완료 수용

| 항목 | 현재 한계 | owner / 다음 종료 검사 |
| --- | --- | --- |
| AT2–AT3 전수 원천·비용 | CLI는 봉인된 normalized universe/position/path manifest를 소비한다. 전체 마스터·native/ENTER/PASS·역사 archive의 자동 전수 결합 producer와 모든 owner의 실제 비용 배분은 완료하지 않았다 | `MainAllScopeTrailingReplay`: 기존 source owner의 전수 manifest·전체 ID 대사·coverage 및 실제 비용 배분 영수증 |
| AT5 실제 유형 후보 선택 | 등록된 유한 grid의 train 선택/holdout 고정과 byte-pinned 실제 selector 참조는 구현했다. 원천/AI 입력 결속·실제 selector 기준을 충족한 유형별 경제 후보의 생산·선정은 미관측이며 CF를 대신 적용하지 않음 | 같은 owner: 적격 actual/type/classifier/source-bound 보고서와 기존 selector 수용; 초기 부모 계승에는 새 경제 gate를 추가하지 않음 |
| TP3–TP7 대용량·계층 처리 | unchanged checkpoint와 cost-only 원천 decode 0은 구현했다. numeric 후보/부모 변경은 source-feature spool을 재사용하고, 4MiB 초과의 단일 position path는 봉인 segment에서 M1 상태를 이어 재생한다. source-feature 저장 64MiB/전체 candidate result admission을 넘는 job의 자동 분할·cache eviction·candidate block은 미완료 | 같은 owner: 상한 초과 job의 전수 분할·재개·bounded cache eviction·공통 cohort 유지 |
| S0/S2 대용량 전수 처리 | v2는 2GiB scan-job/64KiB record 상한 내 원 identity를 검증하고 필요한 필드만 공유 64MiB 데이터 예산에 접수한다. retained index/기회/최종 artifact 또는 legacy holding의 상한 초과는 분할 필요로 거절하며 tail sampling하지 않는다. global census/split·timing projection shard 발행은 미완료 | `PreSubmitDelaySituationImplementation1010`: 상한 초과 입력의 분할·재개·전체 ID/split/선정 동일성 |
| AT7/S5 전체 성능 | 계산 절감과 scope/입력 예산을 측정했다. first/warm/burst/slow-writer/청산 및 전체 장후 cold/warm/delta의 결합 gate는 미완료 | 두 owner: 동결한 전체 workload의 queue/deadline·합산 CPU/RSS/I/O·미측정 경로 수용 |
| AT8/S6 운영 인계 | source-only 격리 결과다. 운영 family 발행·strict/controller/finalization·새 PREOPEN·배포·PID·자연 체결/경제는 미실행 | 별도 승인된 운영 실행에서 동일 source/code 세대의 마지막 consumer까지 확인 |

두 현재 owner는 OPEN으로 유지한다. 구현된 경로의 회귀 통과를 전체 계획 완료나 운영 준비 GREEN으로 표시하지 않는다.

## 검증 종료 기록

최종 변경 Python 38개 compile, `git diff --check`, 관련 문서의 local link 63개 검증을 통과했다. print-only parser는 OPEN 22건을 읽었으며 두 implementation stable ID의 현행 owner가 각각 한 개임을 확인했다. 운영/외부 sync·wrapper 실행·provider/AI/주문·release 선택·PREOPEN 재생성·재기동은 수행하지 않았다. 수정하지 않은 wrapper의 신규 bash 검사는 해당하지 않는다. 실제 소스·모델/CF·최종 적용/PID·경제 수용을 분리하고 미완료 구현/성능은 위 OPEN 표에 남긴다.


## 후속 코드 리뷰와 승인 배포 준비

최신 사용자 지시는 반복 코드 리뷰 후 배포와 다음 영업일 정상기동 점검을 승인했다. 이번 코드 배포의 수용 대상은 기존 0초 동작·부모 경제값을 유지하는 공통 runtime 및 유한 입력 연구 경로다. S6 신규 v2 정책 발행·장후 재생성과 위 표의 전수 입력/대용량 구현 및 전체 연구 성능 수용을 코드 배포 완료로 닫지 않는다.

| 발견한 결함 | 보완·재검증 |
| --- | --- |
| 같은 파일에서 enable/active date 변경 시 준비된 정책이 남음 | PID·target date·manifest·경로·enable·active date를 cache key에 결속. 준비 실패는 이전 key/map을 함께 제거 |
| bootstrap이 만료한 v2 manifest 환경변수를 남김 | 기존 pre-submit env 제거 목록에 manifest SHA 추가. 선택되지 않은 정책의 hash 잔존 회귀 |
| compact quote가 마지막 source SHA 추가 후 12KiB를 넘을 수 있음 | 최종 envelope bytes에서 상한 검사 |
| 한 completed row의 malformed ADD 수량이 전체 census를 중단 | 해당 position을 source gap으로 격리. 불완전하게 재구성한 ADD 경로를 사용하지 않고 정상 position 유지 |
| scope와 결과 context가 예산 접수 전에 할당됨 | 전체 scope expansion과 각 partition 결과를 보관 전에 공유 예산에 접수 |
| 같은 호가를 outer/inner 관측에서 두 번 조회 | 단일 기회는 한 번 조회, 동일 종목의 복수 기회는 route/epoch별 정확 snapshot·hash 공유. intent identity는 분리 |
| 매 append의 중복 mkdir/stat 비용 | 실제 writer profile로 확인 후 parent lstat를 먼저 수행하고 부재 시에만 생성. 매 append의 no-follow·inode·flock·short write·fsync 경계는 유지 |

최종 영향 suite 30개는 **1,079 passed / 29.77초**, 기존 Pandas 경고 1건이다. writer의 warm 경로에서 mkdir 0, 경로 교체 시 다음 append 거절을 별도 회귀로 확인했다. 관련 producer/consumer·초기 정책 만료·대용량 접수·malformed source·typed parent/CF·제출 adapter·예약 bootstrap을 재리뷰했으며 이 bounded 코드 범위에서 미수정 finding은 없다.

### 실제 writer를 포함한 결합 비교

기존 선택 릴리스 `b26aae701314d91a75056fac576b5f460beb3c06`과 최종 검증 후보 `702a9fbf7393c28b6d516726e8f678e2b9467e19`를 같은 host에서 교대로 각 3회 비교했다. 원 호가 observer·부모 policy lookup·공통 청산 kernel·실제 canonical/compact writer와 기존 단일 queue를 함께 실행했다. 정상 32종목, burst 128종목, slow writer는 append당 2ms, 각 종목 0/30/60/120/180초 horizon을 유지했다. 사전 workload hash/1ms 해상도/512MiB RSS 상한·기존 queue 예산을 유지했다.

| 조건 | 기존 wall ms (3회) | 후보 wall ms (3회) | 기존 CPU ms (3회) | 후보 CPU ms (3회) |
| --- | --- | --- | --- | --- |
| 정상 | 72.099 / 70.804 / 69.950 | 68.117 / 65.839 / 65.336 | 52.532 / 51.861 / 52.236 | 48.607 / 48.830 / 48.464 |
| burst | 207.953 / 208.347 / 209.934 | 186.186 / 186.046 / 183.676 | 191.225 / 191.091 / 192.864 | 171.847 / 172.309 / 169.481 |
| slow writer | 443.103 / 441.617 / 442.782 | 437.635 / 436.308 / 436.899 | 56.985 / 56.066 / 56.823 | 51.595 / 50.246 / 51.229 |

세 조건 모두 identity/관측/청산 판단 hash 동일, 누락·중복·queue 거절·append 실패 0. wall/CPU/RSS/p95/p99/max·holding 간격의 사전 비악화 기준을 통과했다. 후보 peak RSS는 최대 149,056KiB, 정상 최대 callback 1.709ms, burst 1.776ms였다. 이는 해당 결합 경로 측정이며 전체 Main 루프·AI/provider·양수 due 재평가 또는 전체 장후 연구 성능으로 확대 해석하지 않는다.

초기 harness는 실제 writer lock 없이 매 append fsync를 강제했고, 다음 버전은 drain을 busy poll하여 시험기 비용이 섞였다. 두 결과는 수용 근거에서 제외하되 보존했다. native condition으로 대기하는 올바른 harness에서도 초기 후보의 정상 CPU 악화를 관측했고, 원천 조회·writer 중복 작업을 수정한 뒤 같은 workload에서 위 결과를 얻었다. 무변경 재측정을 통과까지 반복하지 않았다.

근거: `tmp/all-scope-trailing-delay-review-20261010/`의 `v3-native-wait-performance-budget.json`, `v3-native-wait-performance-results.json`, `writer-profile.txt`, `final-test-manifest.json`, `final-review-tests.log`.

최종 코드의 실자료 격리 재계산도 기본 0초·양수 cell 0이었다. commit 31 / PASS 진단 29 / P0 6 / 가격쌍 21, 부모 해시 결손 29와 source SHA는 기존과 같다. code contract는 `452646852502988b769bd10bb61e7330973408347621270cee0261f338e062a3`, 격리 policy SHA는 `2f8d3961dcbb19888ce0544b931e7e233ebea45f66f89bf71cc0f8b7a289e149`다. 운영 정책 발행 증거가 아니다.


## 승인된 공통 코드 배포·다음 영업일 준비 결과

- 불변 release: `main-trailing-delay-20261010-v1`, commit `d61b36b00696865ca9dd13a466d8544a886e2e28`. 성능 검증 후보와 runtime/deploy 소스 차이는 0이며 최종 불변 릴리스에서 추가 262 passed / 14.08초를 확인했다.
- 두 정식 deployment lock 아래 selector와 웹 pin을 전환하고 새 10/12 prepared generation을 생성했다. 웹 PID 48969, ubuntu, 새 cwd/commit, HTTP 200이다.
- [최종 준비 근거](../../data/report/main_trailing_delay_deployment/2026-10-10/final-readiness.json): `current_full_contract=pass`, findings=[], finalization generation issues=[], cron 8경로 PASS, release-set PASS. `preopen`과 `start` print-plan의 root/commit도 최종 release와 같다.
- 10/12 07:35 PREOPEN·07:55 Main 예약을 확인했다. 토요일 Main은 가동하지 않았으며 `actual_main_pid_consumed=false`, 자연 기동은 `future_due`다. 다음 영업일의 실제 PID/정책 소비는 기존 당일 owner의 자연 수용이다.
- 10/9·10/12 checklist, 10/8 controller/summary, 10/12 기계·보조 policy bytes와 bundle SHA는 모두 보존했다. 트레일링 초기 12 cell은 `parent_carry`다. pre-submit v2 운영 선택은 false이며 기존 기본 동작을 유지한다.
- 기존 10/8 최종화는 세대 무변경을 재검증하여 원 완료 영수증을 재사용했다. 정식 장후·정책 선정·AI/provider/주문 호출은 수행하지 않았다. S6 신규 v2 정책 발행·전수 원천 연결·상한 초과 분할·전체 연구 성능은 위 OPEN 항목으로 남는다.

라우터 CLI의 workspace는 cwd가 아닌 모듈 파일 위치에서 결정된다. 최초 release 디렉터리에서의 라우터 점검은 `release_workspace_mismatch`로 거절됐고 운영 변경은 없었다. 정식 workspace router로 다시 점검해 8개 cron과 release-set, 새 release의 실제 명령/cwd를 확인했다. 이를 Main 기동 실패로 집계하지 않는다.

최종 문서 검증은 로컬 링크 75개 결손 0, print-only backlog 22건이며 두 OPEN stable ID의 현행 owner는 각각 1개다. 최종 release 전체 `src` compile과 `git diff --check`를 통과했다. 이번 작업에서 만든 미선택 review worktree 3개(약 300MiB)는 현재 selector/PID/공유 link/깨끗한 runtime source를 확인한 뒤 제거했고 재현용 commit과 작은 시험 근거는 보존했다. 기존 release와 공유 data/log/정책 원천은 삭제하지 않았다.
