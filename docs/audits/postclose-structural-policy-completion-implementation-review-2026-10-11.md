# 장후 정책 생성 구조 보완 구현·반복 코드리뷰

작성일: 2026-10-11 KST. 범위: [상세 계획 P0–P9](../proposals/postclose-policy-generation-structural-completion-and-retirement-remediation-plan-2026-10-11.md)의 구현·영향 검증과 후속 승인 배포. **검토 범위의 미해결 코드 finding 0, 불변 릴리스 배포·정식 운영 인계·10/12 기동 준비 PASS. 전체 숫자 실험 성능·실제 PID/자연 수용은 OPEN**이다. 구현·리뷰 시점의 기준은 §1–§6, 후속 승인 배포 결과는 §7–§8로 구분한다.

## 1. 구현·리뷰 착수 시점의 기준과 권한

- 착수 workspace HEAD: `38f66369c74f7773822fa8b8b03c4d645eba83d3`. 최초 변경은 10/11 checklist와 이전 감사·계획 문서뿐이었다. 그 기존 내용을 보존했다.
- 선택 릴리스: `main-stop-semantic-20261011-v1`, commit `91edc62844180be6a279e761f32996c3c76ce72e`. 이번 구현은 해당 불변 릴리스에 반영된 코드가 아니다.
- 원천10/8→target10/12 봉인 PREOPEN의 readiness SHA는 `148da6e3b9a8f6201718f4a8dc8afb2dd47ba450416d88eadffcbf9aad2f357c`. 새 작업트리의 준비·PID 소비를 증명하지 않는다.
- Main/manual custody, operator veto, hard/emergency/protect safety, 기존 trailing·delay·최초 수량 소비, 초기 holding vote adoption을 유지했다. ADD vote 세 cell과 episode/widget/PYRAMID/Opening 자동실행을 복원하지 않았다.
- 이 작업에서 정책 재생성, selector 변경, 배포, bot 재기동, provider/계좌/주문 호출, Telegram 발송, 외부 문서 동기화를 실행하지 않았다.
- Kiwoom upstream revision `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회 `2026-10-11T13:19:19+09:00`. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, Postman의 기존 계좌 조회 계약을 대사했다. upstream `kiwoom_docs`는 없었다. 신규 checkpoint는 기존 정규화 결과의 투영이며 wire/parser/요청 수를 변경하지 않는다. [원본 확인 영수증](../../data/report/postclose_structural_implementation/2026-10-11/official-reference.json).

## 2. 구현한 생산자→소비자

| 묶음 | 원천과 계산 | 소비 및 실패 처리 |
| --- | --- | --- |
| P1 cancel wait | 기존 account sync의 broker coverage·원 journal 세대를 observation queue로 전달하여 immutable Main custody checkpoint 생성. 역사 경제 모집단과 현재 Main open/intent/외부 수탁을 분리 | `entry_cancel_wait_tuning`→native summary/strict. 과거 source-gap은 보존하면서 새 complete economic population은 평가 가능. 현재 custody 불명은 적용 차단; retired residual을 Main 미해결로 전환하지 않음 |
| P2 rising TP1 | 차단 시점의 기존 exact-price capacity cache, 0D depth/route/epoch, 실제 수량 formula, 계좌·inventory 세대. 원 allocation reference와 executable ask 분리. 시계순 wallet에서 exit 전까지 자본 점유 | feedback→classifier-prior→기존 publisher/bootstrap. complete 후보만 비용 반영 KRW paired 평가. 미래 원천·계좌 변경·부분 체결·회수 시점 불명은 censor/NULL. 새 REST·provider 호출 없음 |
| P3 auxiliary | frozen campaign 원 rows 보존; 원천 영구 결손과 미시도·완료·불확실 transport 및 durable top-up 예산을 분리 정산 | 기존 auxiliary evaluation/publication. fully accounted exclusion은 비교의 종결 상태에 반영. 불확실 transport는 미종결. 0-PASS는 NULL, 재호출·예산 reset·자동 교체 없음 |
| P4 EXIT vote | 실제 dated parent와 원 요청 bytes, 원 vote population을 기존 stop/trailing model의 독립 arm에서 재생. POST_ADD는 검증된 집계 basis/qty/cost·현재 ADD 세대에만 결합 | 숫자 후보를 train에서 한 번 확정한 후 holdout. frozen experiment/전체 성능 receipt 없으면 `experiment_not_armed` 및 검증된 incumbent carry. v2 publisher→strict/bootstrap/runtime reader; ADD 세 cell 그대로 유지 |
| P5 보호선 | PYRAMID의 `avg_price*1.003/1.01` 생성 branch 제거. AVG_DOWN soft-stop reset 유지. 기존 line을 manual/legacy_retired/unverified로 출처 표시 | 새 익절 owner를 만들지 않음. 원 hard stop이 POST_ADD·AI defer보다 우선. 활성 기존 line의 안전 소비 및 수동·역사 수탁 유지 |
| P6 공통 지원 | native WS attention의 기존 integrated selection을 compact generation projection으로 summary에 전달. 같은 holding snapshot·원 vote store 사용 | source-gap을 N/A/0으로 숨기지 않음. legacy companion은 별도 진단. 공통 full-policy replay의 원 ledger를 각 arm의 메모리 상태로 재생하여 파일 쓰기·arm 간 상태 전파 차단 |
| P7 의미적 감시 | 4개 family의 source/comparison/selection/publication/reader 능력, code/source/clock·fixture receipt 결합 | 10/12 cutover 후 미검증·미지원 경로가 visible finding. incident는 native 세대와 blocker에 결합. 정산과 비교, valid-empty와 unsupported 분리. native intake는 원 식별자로 중복 제거 |
| P8 퇴역 | 현행 caller의 pure source/neutral helper를 역할 패키지로 이전. 퇴역 publisher/연구/CLI의 실행 본체 제거 | archive는 역사 원천 해석만 보존. 직접 CLI/build/write/apply는 inert. 기존 문서 명령 호환만 일시 유지하며 live import는 이행 |

### 2.1 NXT와 통합시장 집계

정책 분석의 `decision_market_scope`, 원천의 `market_data_route`, 주문 route, 실제 `actual_execution_venue`는 서로 다른 축이다.

| 구간 | 정책 분석 모집단 | NXT 별도 숫자의 의미 |
| --- | --- | --- |
| 프리마켓 | 기존 `PREMARKET_KRX_LIKE` 프리마켓 정책 구간; NXT-only 원천/주문 경로 별도 검증 | 허용되는 프리마켓 원천/경로 하위 집계. 독립적인 정규장 정책으로 승격하지 않음 |
| 정규장 | 통합 호가가 확인된 `KRX_NXT_INTEGRATED` | 실제 체결시장·원천/route 진단만 가능. 같은 판단/시도를 KRX·NXT 양쪽의 정책 표본으로 중복 계산하지 않음 |
| 애프터장 | 통합 호가가 확인된 `KRX_NXT_INTEGRATED` | 같은 원칙. legacy `nxt_*` 시간구간 이름만으로 NXT 전용 정책을 만들지 않음 |

실제 장중 생산자의 구형 `rising_missed_effective_venue=KRX/NXT`는 기존 NXT 안전조건에서도 사용한다. 이 필드를 무작정 바꾸지 않고 독립 `decision_market_scope`를 추가했다. 통합 원천을 증명하지 못한 정규장/애프터장 표본은 `UNKNOWN`이며 추측으로 통합하거나 소급 재분류하지 않는다. native `KRX_NXT` alias도 통합 scope로 정규화한다. broker route가 NXT라고 해서 실제 fill venue를 NXT로 꾸미지 않는다.

## 3. 반복 리뷰에서 고친 결함

1. 현재 broker checkpoint를 과거 종료 여부와 혼합하던 적용 veto, checkpoint 이후 dispatch 연속성·journal prefix·negative Main quantity 대사 결손을 분리했다.
2. quantity capture가 native depth의 `price_krw` 대신 존재하지 않는 `price`를 읽고 정상 ask/reference spread를 거부하던 연결을 수정했다. 원 allocation price와 executable ask는 각각 보존한다.
3. NXT post-block BBO의 실제 source label과 consumer label 불일치를 수정했다. 기존 sampler의 같은 snapshot에서 depth qty·route·epoch·clock을 전달하며 새 sampler를 만들지 않는다.
4. 통합시장 정책 분석 축이 구형 KRX/NXT 진단 축에 덮이는 문제를 수정했다. 프리마켓 및 정규장·애프터장 native capture와 한 시도 한 행 회귀를 추가했다.
5. auxiliary immutable evaluation이 재평가 벽시계에 따라 다른 SHA를 만드는 문제를 제거했다. 원 campaign과 예산은 그대로 두고 종결 정산을 revision으로 기록한다.
6. POST_ADD의 미래/다른 세대 cost와 pending ADD, vote source/basis 오결합, hard-stop 우선순위를 검증했다. trailing은 당시 native effective values를 요구하고 현재 parent로 역사값을 메우지 않는다.
7. 원 holding handler 재생에서 peak/stop pin 원장 쓰기를 시도하던 장애를 수리했다. 원 ledger의 같은 판단·record 방법을 독립 메모리 저장소에서 실행한다. 누락 파일 읽기와 주문/provider/스레드 부작용 차단을 유지한다.
8. 실제 사용 가능한 frozen experiment 파일 bytes가 v2 publication receipt에서 빠질 수 있는 문제, numerical 후보와 native publisher/bootstrap의 status label 불일치를 고쳤다. 미발행 결과는 `pending_publication`이다.
9. 대용량 WS companion에서 attention 지원 여부가 summary에 누락되던 문제를 compact 원천 투영으로 수정했다. 최종 selection 보존 후 projection/hash를 갱신한다.
10. generation fixture의 schema/component 타입 검증, 원 source/code/clock·receipt SHA, cutover 경계, 의미적 복구의 원 세대 결합을 보강했다. 목록만 있는 비결합 observation은 회복 증거가 아니다.
11. code cache가 한 파일의 정정으로 모든 파일을 다시 읽던 낭비를 bounded file-generation cache로 수리했다. ctime까지 검증하며 원천·비용 bytes는 cache하지 않는다.
12. Opening Rotation direct SELL helper가 permanent owner retirement 밖에서 호출 가능하던 잔재를 inert 처리했다. stale caller가 Main 수탁/상태를 변경하거나 매도할 수 없다.
13. capability code-generation 목록에 실제 capture 생산자가 빠질 수 있는 문제를 보완했다. cancel의 account/snapshot/queue, TP1의 handler/시장 enrichment, EXIT의 handler/receipt/원 재생·vote owner까지 receipt 해시에 결합한다. 최종 관련 379개 회귀를 다시 통과했다.
14. 추가 재리뷰에서 EXIT 실험의 source SHA에 원 vote ledger·request/payload/prompt bytes가 빠지는 결함을 확인했다. bounded 원천 index에서 immutable vote 참조를 먼저 조립하고, 전체 원천 hash를 frozen contract와 대사한 뒤에만 arm 계산을 시작한다. v2 발행·reader도 원천 inventory에서 hash를 재계산한다. 원 요청 bytes 정정·inventory 바꿔치기·미확정 source hash를 선정 증거로 사용할 수 없다.
15. raw decoder의 `unidentifiable_raw_rows`를 숫자 EXIT 생산자가 확인하지 않아 파싱 불가 행을 정상 incumbent carry로 표시하던 누락을 고쳤다. 격리 불가능한 원천은 `source_gap`으로 표시하고 검증된 parent를 보존한다.
16. frozen contract의 `performance_receipt`·`max_step`·`allowed_keys` 타입 오류가 미처리 예외 또는 불명확한 오류로 끝나는 경로를 재현·수정했다. 명시적인 계약 결손으로 반환하며 숫자 후보를 내보내지 않는다.
17. 완료 원천 metadata의 같은 ID가 두 번 들어오면 SQLite UNIQUE 예외로 작업이 중단되는 문제를 재현했다. 동일 metadata는 한 번만 소비하고, 내용 충돌은 `holding_vote_actual_metadata_conflict`로 표시해 parent를 유지한다. 다른 기록을 임의 우선순위로 덮어쓰지 않는다.
18. EXIT source freeze를 검토하면서 raw loader·position index·비용 대사·bounded storage 구현도 experiment 및 의미적 capability code hash에 포함했다. 입력 해석 코드가 달라지면 이전 fixture/실험 영수증을 그대로 인정하지 않는다.
19. 후속 승인 배포의 실제 원천 인계에서 구형 v10 부모의 15cell 전체 hash와 현재 생존 12cell hash가 혼용되는 호환 결함을 확인했다. 첫 전환은 CAS rollback으로 복구하고 원 native hash와 활성 정책 hash를 분리했다. 원 부모 bytes·12개 정책값·퇴역 상태를 유지하면서 구형 부모→v2 발행→source handoff→runtime loader 회귀를 추가했다. 실제 실패와 재검증은 §7에 기록한다.

구형 자동 발행·주문을 요구하던 테스트는 퇴역 음성 회귀로 변경했다. pure 역사 reader/수학 테스트는 archive를 직접 검증한다. 불일치 assertion을 정상 동작으로 우회하지 않았으며 삭제·이전 근거는 [test migration](../../data/report/postclose_structural_implementation/2026-10-11/retired-test-migration.json)에 남겼다.

## 4. 퇴역과 위치 검증

- 삭제: `src/trading/order/target_amend.py`, `deploy/run_shadow_canary_check.sh`, `src/engine/lifecycle_decision_matrix_runtime.py`.
- 활성 helper owner: `scalping/entry_observation_events.py`, `lifecycle/avg_down_event_source.py`, `ai/retired_lifecycle_context.py`, `lifecycle/neutral_decision_context.py`. 기존 실제 caller 때문에 필요한 단일 구현이며 engine root에 새 Python 모듈을 만들지 않았다.
- 역사 reader owner: `lifecycle/archive`. 원 수식·schema·과거 receipt 해석만 보존한다. 내부 live code가 retired compatibility module을 다시 import하지 않는지 대사했다.
- root/CLI compatibility는 과거 문서의 실제 `-m` 명령·forensic API만 보존한다. 해당 명령 문서와 외부 reader가 이전된 뒤 삭제한다. 임시 facade로 중복 구현·현재 publisher를 유지하지 않는다.
- `install_shadow_canary_check_cron.sh`는 기존 shadow cron을 제거하는 도구다. 삭제한 launcher를 재설치하지 않는다. 이 작업에서 installer/cron 변경은 실행하지 않았다.
- selected/rollback/prepared가 참조하는 기존 release를 파일 단위로 수정·삭제하지 않았다. 역사 registry/env 이름은 과거 계약 해석을 위한 문자열이며 active publisher 또는 신규 정책 요구가 아니다.
- [최종 import·변경 호출 census](../../data/report/postclose_structural_implementation/2026-10-11/retirement-final-census.json), [이전 근거](../../data/report/postclose_structural_implementation/2026-10-11/retirement-migration.json).

## 5. 검증과 성능

최종 검증:

- 추가 재리뷰의 최종 영향 검증: **15개 모듈 364 passed**, 82.41초. [추가 회귀 로그](../../data/report/postclose_structural_implementation/2026-10-11/rereview-regression.txt). 아래 기존 검증과 중복이므로 합산하지 않는다. 원 요청 기반 native assembly→선정 양성, 요청 bytes 변경 시 계산 전 차단, 원천 결손·계약 타입·완료 metadata 중복/충돌 및 발행 source binding 음성을 포함한다. [추가 로컬 검증](../../data/report/postclose_structural_implementation/2026-10-11/rereview-local-validation.json).
- 같은 재리뷰에서 TP1 자본 모델·취소 runtime의 fixture/소비자 **27 passed**, 0.72초를 추가 확인했다. [소비자 회귀](../../data/report/postclose_structural_implementation/2026-10-11/rereview-fixture-consumers.txt). 이번 두 묶음은 서로 다른 17개 모듈, 총391개 테스트다.
- 58개 모듈 **2,109 passed**, 177.40초. dependency의 기존 Pandas4Warning 1건이며 실패 없음. [대상 목록](../../data/report/postclose_structural_implementation/2026-10-11/final-test-files.json), [통합 회귀](../../data/report/postclose_structural_implementation/2026-10-11/final-regression-2.txt).
- 마지막 capability producer-hash 변경 후 9개 영향 모듈 **379 passed**, 47.38초. [generation 영향 회귀](../../data/report/postclose_structural_implementation/2026-10-11/final-generation-review.txt). 위 통합 회귀와 중복이므로 합산하지 않는다.
- 별도 cancel runtime/attribution·strict chain **62 passed**, 1.34초. [최종 strict 소비자 회귀](../../data/report/postclose_structural_implementation/2026-10-11/final-strict-consumer-review.txt).
- 변경·이전 Python 129개 compile, 관련 기존 wrapper 4개 `bash -n`, `git diff --check` PASS. 로컬 링크·현행 stable owner와 print-only parser를 검증했다. parser 항목 23개이며 현행 통합 owner는 1개다. Project/Calendar sync는 실행하지 않았다.
- 최종 4개 family의 [추가 재리뷰 code-fixture receipts](../../data/report/postclose_structural_implementation/2026-10-11/rereview-generation-fixture-receipts.json)를 실제 PASS 로그와 현재 code-generation에 결합하고 native inspection으로 검증했다. [이전 리뷰 영수증](../../data/report/postclose_structural_implementation/2026-10-11/generation-fixture-receipts.json)은 그대로 보존했다. 구성된 frozen 코드 경로의 증거이며 자연 원천·경제성·selected/PID·운영 발행 증거가 아니다. 원 runtime 보고서는 다시 생성하지 않았다.
- protected 6개 고유 파일의 bytes, PREOPEN의 env/manifest/summary/verifier/controller 파일 SHA, 최초 수량 current pointer bytes와 delay의 **native content SHA**를 대사했다. [로컬 검증](../../data/report/postclose_structural_implementation/2026-10-11/local-validation.json). file SHA와 semantic policy SHA를 혼동하지 않는다.
- archive의 파일 변경/request 호출 0, 현행 내부 retired-compat import 0. [설치 cron/unit census](../../data/report/postclose_structural_implementation/2026-10-11/installed-entrypoint-census.json)의 퇴역 진입점 연결 0. 역사 reader 31개 파일은 오프라인 수식·schema 해석을 위해 남는다.

완전 원천 양성: cancel의 역사 gap 보존 + 새 후보 선정, TP1 5일 60건 blocked population의 자본·비용 모델→publish/bootstrap, 원 실제 요청 bytes의 4 position/day EXIT 재생→train/holdout→v2 publisher, 실제 parent 그대로 unarmed carry, frozen auxiliary terminal accounting 및 native publication을 검사했다. 이는 synthetic/frozen 코드 도달성이다. 이번 자연 운영의 수익·policy 생성·PID 소비가 아니다.

[제한된 성능 protocol](../../data/report/postclose_structural_implementation/2026-10-11/scoped-benchmark-protocol.json)을 측정 전에 고정하고 B1/B2 순서를 교대해 각3회 실행했다. [결과](../../data/report/postclose_structural_implementation/2026-10-11/scoped-benchmark-result.json)는 원 byte 동등성, 독립 비용 정정, 100/1,000개 complete source projection, cold/warm/incremental/resume code generation을 확인한다. 각 batch의 절대 2초 예산은 이 제한된 측정에만 적용한다.

현재 제한된 측정의 median: warm code hash 약4.58→0.63ms, 한 code 파일 변경 약4.58→0.76ms, 1,000행 projection 약25.23→17.28ms. cold/resume은 strong stat 검증 비용으로 약16~18% 느렸다. 이 수치를 전체 runtime 성능 PASS나 기존 owner의 허용 오차로 사용하지 않는다. source/cost bytes는 매번 별도로 검증했다.

전체 decision/submit/cancel·slow-writer/queue·실제 heavy-job 결합·전체 후보 재생은 **미실측**이다. `runtime_and_postclose` frozen 성능 receipt를 만들지 않았으며 EXIT 실험/런타임 변경의 운영 수용 gate는 OPEN이다. 원천 0건이나 작은 benchmark로 P9 전체를 완료 처리하지 않는다.

추가 재리뷰의 원천 선행 조립은 장후 disposable index와 기존 immutable vote tree를 재사용한다. 장중 수집·provider 호출을 늘리지 않는다. 위 제한 측정은 이전 리뷰의 결과이며 이번 원천 선행 조립을 포함한 전체 처리량·P9의 성능 수용 근거로 재사용하지 않는다.

## 6. 구현·리뷰 완료 시점의 소유와 다음 종료 조건

| 잔여 | 현행 owner/증거 | 다음 행동·종료 검사 |
| --- | --- | --- |
| 통합 운영·성능 | 10/11 `PostcloseStructuralPolicyCompletion1011` | 동일 complete-source 전수/후보와 실제 결합 부하 검증 후 불변 release/native handoff 대사 |
| cancel 자연 checkpoint/후보 | 10/12 `DirectFamilySourceRepairEntryCancelWait` | 새 native checkpoint·current journal/clock 연속성·다음 source 평가; history gap과 현재 적용 veto를 각각 확인 |
| auxiliary 정산/비교 | 10/12 `DirectFamilySourceRepairCompactAuxiliary` | 실제 durable campaign/native resolution 소비·budget/transport terminal 대사; 0-PASS는 NULL 유지 |
| EXIT 실험·stop | `MainStopLossRetirementRuntimeTuning1010` | 실제 parent/source/grid와 승인된 freeze/split/허용 숫자·전체 성능 receipt 준비, 이후 독립 train/holdout/native publication |
| 의미적 감시 release 채택 | `SemanticMonitorLatestReleaseRepair1010` | selected code와 native capability/fixture 세대 대사; 작업트리 fixture는 selected/PID 증거로 사용하지 않음 |
| 다음 영업일 정식 준비·자연 소비 | `DirectFamilyPreopenPolicyHandoff` | 허용된 successor 선택 후 기존 strict/summary/controller와 exact-date PREOPEN 재봉인; 새 PID 소비는 별도 확인 |

봉인된 10/12 checklist와 PREOPEN을 이 작업에서 고쳐 쓰지 않는다. 현행 10/11 stable ID는 운영 종료 증거가 남아 있으므로 OPEN을 유지한다. 새로운 성능 기준·임의 실험 숫자·추가 초기 adoption 승인 조건을 만들어 운영 gate를 통과시키지 않는다.

## 7. 후속 배포 승인과 실제 인계 재리뷰

사용자의 후속 `배포승인 및 내일 정상기동여부 점검`에 따라 불변 릴리스와 source10/8→target10/12 native CAS 인계를 진행했다. 앞 절의 무배포·봉인 보존은 구현/리뷰 시점의 기록이며 이번 승인으로 해당 운영 인계를 수행한다. 전체 숫자 EXIT 경제 실험의 성능·자연 수용은 별도 OPEN이다.

- [첫 배포본](../../tmp/postclose-structural-deploy-20261011/attempt-v1/release-build.json)의 불변 회귀 **625 passed**, 기존 Pandas 경고1건. [회귀 로그](../../tmp/postclose-structural-deploy-20261011/release-tests.log).
- [측정 전 고정 protocol](../../tmp/postclose-structural-deploy-20261011/performance-protocol.json)에 따라 기존 stop owner의15% 한도로 정상/집중/느린 writer를 교대 각3회 비교했다. [18회 결과](../../tmp/postclose-structural-deploy-20261011/runtime-performance-summary.json)의 반환 p99 증가는 각각9.58%/12.04%/4.11%, 청산 전달9.66%/11.98%/3.30%였고 각500건 판단·격리 dispatch가 같았다. 실제 주문·provider 호출은0이다.
- 기존 cache의 완전한 TP1 원천과 custody enqueue를 실제 장후 원천 재검증과 함께 실행했다. [9회 capture 결과](../../tmp/postclose-structural-deploy-20261011/capture-performance.json)는 각각500건·완료4500건·거부/실패0, p99 최대1.46ms로 사전5ms 한도 안이다. 100종목 snapshot·16건 burst와1ms 격리 writer를 사용했다. 최초 fixture의 통합시장 item suffix 누락은 source-gap으로 거절됐으며 `_AL` 원 fixture를 적용한 뒤 측정했다. 운영 프로토콜·성능 한도를 완화하지 않았다.
- 첫 전환은 `holding_vote_successor_parent_invalid`로 summary가 실패했다. 구형 v10 부모의15cell 전체 hash를 생존12cell 승계 hash로 사용한 결함이었다. [실패 원본](../../tmp/postclose-structural-deploy-20261011/attempt-v1/formal-handoff.log)과 [첫 CAS 원장](../../data/runtime/research_release_transition/postclose_structural_20261011_v1/transition.json)을 보존했다. 자동 CAS rollback 뒤 기존 선택본과 기존 PREOPEN full contract를 다시 검증했다.
- 원 native15cell 영수증을 보존하면서 active12cell의 rollback hash를 분리했다. retired3cell을 다시 소비하지 않으며 ADD를 포함한 생존 정책값은 유지한다. 구형 부모→v2 발행→원천 인계→runtime loader 회귀를 추가했고 workspace **203 passed**, [수정 불변본203 passed](../../tmp/postclose-structural-deploy-20261011/release-v2-tests.log)를 확인했다. 앞선625개와 중복이므로 합산하지 않는다.
- 수정 릴리스는 `main-postclose-structural-20261011-v2`, commit `5106ddaefb8fdaff8b06d92f8064a66f3256eaaa`다. [구성132개 경로](../../tmp/postclose-structural-deploy-20261011/release-build.json)는129개 파일과3개 삭제를 포함한다. [성능 재사용 대사](../../tmp/postclose-structural-deploy-20261011/performance-reuse-v2.json)는 수정된 오프라인 parent projection·startup binding·회귀 파일3개 외에 측정한 실시간 경로의 bytes가 동일함을 확인한다. [현재4개 family fixture](../../tmp/postclose-structural-deploy-20261011/generation-fixture-receipts.json)는 마지막 불변 코드에 결합했다.

이 측정은 이번 구조 보완 배포의 영향 경로 수용이다. 전체 Main/모든 heavy-job·완전 경제 모집단의 신규 숫자 EXIT 실험 성능을 대신하지 않으며 `runtime_and_postclose` 실험 영수증을 만들지 않았다. 코드 생성·예약 준비·실제 PID/주문·경제성은 별도로 판정한다.

## 8. 승인 배포 완료와 10/12 기동 준비

판정: **`main-postclose-structural-20261011-v2` / `5106ddaefb8fdaff8b06d92f8064a66f3256eaaa` 배포·선택 완료, source10/8→target10/12 정상기동 준비 PASS**. 실제 월요일 기동·인증·WS 접속·PID 정책 소비는 아직 미래다. [최종 준비 영수증](../../data/report/postclose_structural_deployment/2026-10-11/final-readiness.json), [선택 원장](../../data/runtime/runtime_release_selection.json), [성공 CAS 원장](../../data/runtime/research_release_transition/postclose_structural_20261011_v2/transition.json).

- native `pre_submit_delay`·`summary_handoff`가 성공했고 strict/controller가 통과했다. [인계 결과](../../tmp/postclose-structural-deploy-20261011/formal-handoff.json). 정식 finalization wrapper도 실제 실행해 **15:58:07 KST `DONE`, exit0**을 확인했다. cleanup·최종 detector 및 chain/snapshot 세대를 종료 기록과 대사했고 issues는0이다. 준비 파일 생성만으로 종료 성공을 대신하지 않았다.
- 종료 절차가 재생성한 [10/12 PREOPEN receipt](../../data/runtime/policy_bootstrap/prepared/2026-10-12/2026-10-08_b8c9cbcdb66a3782_5106ddaefb8fdaff/readiness.json)의 SHA는 `ace08e0b1b138cc282e8552ad28c65df5808a435b2de4678ef683ff803d61351`이다. `current_full_contract=pass`, findings0이며 새 selector·summary·controller·10/12 checklist·정책 hash를 결합한다. `actual_pid_consumed=false`, 당일 activation은 아직 미실행이다.
- 설치된 필수 cron8개와 release-set을 검증했다. **10/12 07:35 PREOPEN, 07:55 Main** 모두 새 릴리스 경로다. [PREOPEN 경로](../../tmp/postclose-structural-deploy-20261011/preopen-routing-plan.json), [Main 경로](../../tmp/postclose-structural-deploy-20261011/start-routing-plan.json), [cron 대사](../../tmp/postclose-structural-deploy-20261011/cron-check.log). cron active·KST/NTP 정상, 디스크 여유 약38GiB를 확인했다. 일요일 Main은 비가동 상태이며 조기 기동하지 않았다.
- [정책값 보존 대사](../../tmp/postclose-structural-deploy-20261011/policy-value-preservation.json): 기계·보조 공통 정책 bytes와 보호 대상6개 파일은 그대로다. holding active12cell·ADD·손절·트레일링·최초수량·operator lock·rollback env 값이 유지됐다. delay는 기본0초와 cells_ref가 동일하고 code/report/policy receipt hash만 바뀌었다. 최종 재봉인 manifest도 같은 값이다. 신규 숫자 EXIT는 `experiment_not_armed`; 경제 비교 표본 결손을0으로 대체하지 않았다.
- [최종 코드 대사](../../tmp/postclose-structural-deploy-20261011/final-code-validation.json): 배포132경로가 검토본과 일치, Python129개 compile·실제 shell5개 syntax·diff check PASS. workspace/index와 기존 롤백 릴리스는 보존했다. 문서·현행 owner는 print-only parser로 검증하며 Project/Calendar sync는 실행하지 않는다.

최종 detector는 **7/7 실행, 실패0, warning4**다. [경고 해석](../../tmp/postclose-structural-deploy-20261011/semantic-warning-review.json)을 기동 준비 판정과 함께 보존한다.

- 인증8005는 **10/9 22:36:36 `ka10080` 원 로그**다. 현재 Main PID가 없는 dry-run에서 아직 소비하지 않은 로그를 `fresh`로 표시했으며 이번 작업의 재발·실시간 인증 검증 결과가 아니다. restart 요청·token cache 무효화는 실행하지 않았다. 선택 코드의 시작 owner는 `require_issued_today=True`로 전일 token을 거부한다. [기동 cache 회귀3개](../../tmp/postclose-structural-deploy-20261011/auth-startup-tests.log), [PID 인계·dry-run 회귀3개](../../tmp/postclose-structural-deploy-20261011/auth-detector-tests.log)를 격리 실행해 통과했다. 실제 당일 발급 성공은 미래 수용 항목이다.
- `update_kospi_status`는 원천10/8의2629종목 중2626종목 완료, `266690`·`468670`·`486510`의 당일 일봉 결손 경고다. 원천 결손을 보존하며 정상기동 준비 전체 실패나 정책값 변경으로 확대하지 않는다.
- cron 경고는 자식 detector가 살아 있는 부모 종료를 PASS로 선행 표시하지 않는 `pending_self_audit`였다. 이후 같은 세대의 실제 부모 `DONE`으로 종료를 확인했다. log scanner는 새 error burst 없이 역사 로그가 남았다는 경고다.

기존 10/12 **`DirectFamilyPreopenPolicyHandoff`** 단일 owner에 새 release/준비 정책의 실제 PID 소비, 당일 인증·WS·자연 원천 수용을 연결했다. 이 항목은 승인 CAS 안에서 갱신한 뒤 봉인했으며 이후 수동 수정하지 않았다. 10/11 `PostcloseStructuralPolicyCompletion1011`의 전체 결합 성능 잔여와 기존 stop/semantic/family owner의 경제·자연 수용은 OPEN을 유지한다. 배포 성공을 새 수익 개선이나 전수 경제 비교 완료로 해석하지 않는다.
