# Main 트레일링·제출 지연 잔여작업 완료계획 — 2026-10-10

상태: **W0–W5의 부모 계승·0초 초기 정책 발행·배포·장후 최종화·10/12 PREOPEN 준비는 완료했지만, 신규 학습 정책 생성의 정상 원천 경로에는 구조적 결함이 남아 있다.** 10/10 21:27 KST [생성 가능성 재점검](../audits/main-trailing-delay-policy-generation-structural-review-2026-10-10.md)에서 TG1–TG4/DG1–DG4를 확인했다. 앞선 [실행 감사](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md)의 전체 구현 finding 0은 정상 AI 증빙·classifier 인과성·현재 PASS 부모 연결의 도달 가능성까지 검증한 결론으로 사용하지 않는다. [기존 최종 준비 영수증](../../data/report/main_trailing_delay_deployment/2026-10-10/final-residual-readiness.json)은 당시 부모/0초 준비의 근거이며 W6 자연 기동/PID 소비는 10/12 기존 `DirectFamilyPreopenPolicyHandoff`가 확인한다.

이번 재점검은 코드·격리 진단 및 문서 정정이다. 데이터 증가만으로 해결되지 않는 quote/holding-AI 연결, 새 classifier SHA를 과거 pin에 요구하는 순환, 대용량 시장 후보 미전달, 현재 PASS/AI 부모 누락과 결손 셀 전역 차단을 별도 수리 대상으로 남긴다. 후속 구현 착수 시 두 기존 stable ID의 완료 이력을 유지해 현재 checklist에서 재개하고 정상 producer→후보→selector/lookup의 도달·결손 격리 시험을 종료 조건에 추가한다. 현재 정책·선택 릴리스·봉인 10/12 checklist를 이번 진단에서 변경하지 않는다.

다섯 단계의 상세 수정 계약·원천/소비 경계·정상/실패 시험은 [정책 생성 구조 보완계획 P1–P5](main-trailing-delay-policy-generation-structural-remediation-plan-2026-10-10.md)를 따른다. 현재 PASS/해시→pre-signal holding-AI→classifier 인과성→결손 격리/대용량 연결→일반 악화/horizon 조건을 이 순서로 수리한다. 최초 수량·손절·감시기 개선은 해당 상세계획 범위에 포함하지 않는다.

## 1. 결정과 완료 범위

남은 작업은 **전수 원천 연결 → 상한 초과 분할·재개 → 초기정책 계산·소비 → 전체 성능 검증 → 정식 발행·장후 인계 → 다음 영업일 기동 준비**까지 수행한다. 공통 코드만 배포하고 전체 계획을 다시 미완료로 남기는 것을 종료 조건으로 삼지 않는다. 실제 자연 PID·주문·청산·경제 결과는 도래한 시점에 별도로 확인한다.

실행 owner는 [오늘 체크리스트](../checklists/2026-10-10-stage2-todo-checklist.md)의 `MainAllScopeTrailingReplay`, `PreSubmitDelaySituationImplementation1010` 두 개를 재사용한다. W 번호는 두 owner 내부의 작업 순서이며 새 backlog owner가 아니다. [PASS 제출 경로 계획](main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md)의 완료된 구현·배포는 유지하고, 연결 변경에 영향을 받는 회귀만 다시 수행한다.

사용자가 이미 승인한 두 계획의 구현·반복 리뷰·배포·다음 영업일 기동 점검 범위를 유지한다. 앞선 selector의 `approval_scope`가 공통 코드와 기존 정책 유지로 좁혀진 것은 당시 배포 기록이며 전체 구현 승인 철회가 아니다. 후속 실행은 아래 전체 완료 조건과 기존 family 선택 계약을 따른다. 문서 작성 자체로 운영 파일을 바꾸지는 않는다.

기존 상세 계약은 [전체 범위 트레일링 AT0–AT7/TP1–TP7](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md), [제출 지연 S0–S6](pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md)를 따른다. 본 문서는 미완료 항목의 순서·구현 경계·종료 검사와 운영 인계를 보완한다.

## 2. 출발점과 잔여 원인

10/10 읽기 전용 확인 기준 선택 릴리스는 `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28`이다. v2 loader와 공통 runtime 코드는 포함됐지만 selector의 `full_plan_acceptance=open`, `v2_policy_selected=false`다. 후속 실행 때 release/PID/lock/source를 다시 고정한다.

| 구분 | 확인한 상태 | 이번 잔여작업 |
| --- | --- | --- |
| 전수 원천 | 전체 scope 계산기는 외부에서 정규화한 manifest를 소비함. 마스터·native·후행 경로·비용 자동 결합은 미완료 | W1에서 실제 원천부터 manifest까지 생성하고 정상 장후 caller에 연결 |
| 대용량 | checkpoint·segment replay·예산 검사는 있음. 상한 초과 시 분할 필요로 종료 | W2에서 자동 분할·재개·전역 대사·선정과 bounded cache eviction 구현 |
| 초기정책 | 부모 동등 trailing 12 cell은 배포. 제출 지연은 임시 경로에서 0초 baseline 계산 | W3에서 원천 자격·호환성·fallback을 검증하고 W5에서 정식 발행 |
| 성능 | 컴포넌트 결합 normal/burst/slow-writer는 통과. 전체 Main/due/보유청산/장후 조합은 미측정 | W4에서 동일 전체 입력·작업량의 통합 시험 |
| 운영 인계 | 기존 정책 기준 PREOPEN 준비는 PASS. 신규 제출 지연 v2의 정식 장후 세대는 미발행 | W5에서 affected family부터 finalization/PREOPEN까지 새 세대로 종료 |

근거는 [기존 구현 감사의 미완료 목록](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md#전체-계획의-미완료-수용)과 [현재 기동 준비 기록](../../data/report/main_trailing_delay_deployment/2026-10-10/final-readiness.json)이다. 임시 제출 지연 결과의 commit 31/PASS 진단 29/P0 6/가격쌍 21 및 부모 hash 결손 29건은 동결 입력의 진단 수치다. 복원 후 분모를 다시 대사하며 양수 지연·실현 순익의 근거로 재사용하지 않는다.

## 3. 실행 순서와 책임

| 순서 | 기존 owner / 대응 단계 | 산출물과 종료 검사 | 다음 단계 |
| --- | --- | --- | --- |
| W0 실행 기준 고정 | 두 owner / AT0·S0 | 현재 release/source/부모/custody/입력 목록, 기존 chain hash, 하나의 성능·저장 예산. 미정 자원 수치 0 | W1·W2 |
| W1 전수 원천 결합 | trailing AT1–AT3, delay S0·S1 | 자동 source manifest·전체 ID/범위 대사·복원/제외/비용 미배분 목록. 수작업 normalized manifest 없이 재현 | W3 |
| W2 분할·재개와 전역 집계 | 두 owner / TP3–TP7·S0/S2 | 초과 입력의 모든 shard 완료·재개·bounded cache·전역 split/cohort·consumer 검증. 단일 입력 기준과 의미 동일 | W3 |
| W3 초기정책과 소비 연결 | trailing AT4–AT6, delay S2–S4 | 실제/CF 분리, 부모 계승 및 가격정책·due 재평가·loader/report/monitor 연결. 모든 값이 그대로여도 근거가 유효하면 완료 | W4 |
| W4 전체 리뷰·성능 | 두 owner / AT7·S5 | 전체 연결 리뷰의 미해결 구현 finding 0, 영향 회귀·독립 계산·전체 workload 성능 gate PASS | W5 |
| W5 정식 발행·장후 인계·기동 준비 | 두 owner / AT7·S6 | 불변 최종 코드, formal policy/report, affected stage/summary/checklist/strict/controller/finalization, 신규 PREOPEN의 정확 hash·예약 경로 일치 | 구현·운영 준비 종료 |
| W6 자연 소비 확인 | 해당 적용일 `DirectFamilyPreopenPolicyHandoff` | 실제 PID/cwd/start generation·정책 hash·source date·Main/manual/퇴역 OFF·자연 disposition | 도래 후 관측 종료 |

W0의 요구사항 대사표에는 AT0–AT7/TP1–TP7/S0–S6별 실제 producer/caller·consumer·미구현 함수/계약·필수 시험·산출물 경로·종료 상태를 기록한다. W4는 이 표의 구현/성능 행 전부와 W5 인계 시험을 확인하고, W5는 실제 발행·인계 영수증을 채운다. `source_gap`, 경제 후보 부재, `future_due`는 해당 증거 행에만 적용하며 미구현 caller·분할·consumer 행을 면제하지 않는다. 범위를 줄인 시험 집합을 전체 계획의 finding 0으로 재정의하지 않는다.

의존 순서는 W0→W1/W2→W3→W4→W5이며 W1/W2는 동일 manifest·예산 계약으로 결합한다. W4 실패는 발견한 코드/자료구조 결함을 보완하고 영향 시험으로 돌아간다. 무변경 반복 측정·무변경 원천 재생으로 통과를 만들지 않는다. 단계별 산출물을 남기되 구현 전체 완료 전의 부분 배포를 전체 계획 완료로 표시하지 않는다.

실행 날짜가 넘어가면 같은 두 stable ID의 수용·진척·다음 단계를 실제 KST 날짜 checklist로 정식 이전하고 current parsed owner가 각각 하나인지 확인한다. 완료 기록이나 이 문서의 W 번호를 실행 owner로 사용하지 않는다. 기존 source date와 마지막 검증 세대는 날짜 이전으로 바꾸지 않는다.

현재 목표는 10/12 07:35 예약 PREOPEN 전에 W5를 끝내는 것이다. W0에서 전체 입력의 측정 처리량과 남은 시간으로 작업창을 확인한다. 검증/발행이 그 창을 넘으면 기존 유효 준비·정책을 유지하고 실제 완료일의 다음 적격일로 새 적용일을 계산한다. 기한 때문에 미완료 정책을 선택하거나 봉인 시각을 소급하지 않는다.

## 4. W0–W1: 전수 원천과 복원·제외

### 4.1 입력과 실제 caller

- `source_date`는 마지막 적격 원천일을 실행 시작 때 고정한다. 현재 준비 기준은 10/8이며 `publication_date`는 실제 발행일, `effective_date`는 저장소 달력의 다음 적격 거래일이다. 자정이 넘어도 원 source date를 유지하고 적용일을 소급하지 않는다.
- 신규 후보의 forward 학습창은 현행 9/29 경계를 따른다. 비용 의존 검사는 각 기존 report가 실제 소비한 모든 날짜를 포함하고, 이전 정책의 역사적 증빙을 신규 후보 학습 승인으로 바꾸지 않는다.
- 종목 마스터 전체와 지원 session/route, native ENTER_NOW, 원 auxiliary PASS·Main disposition, broker position/fill/terminal, 후행 archive/path와 custody/cost를 목록화한다. 삼성/비삼성·fixed/scanner·프리/정규/통합 애프터를 원천 계약별로 모두 대사한다. 통합 애프터의 관측 route는 SOR/`KRX_NXT_INTEGRATED`이며 실제 체결 venue와 구분한다.
- [전체 scope 연구](../../src/engine/automation/main_trailing_all_scope_research.py)에 manifest 생성 adapter를 연결한다. 실제 producer 경로는 [log archive의 profile snapshot](../../src/engine/log_archive_service.py)의 `save_monitor_snapshots_for_date_with_profile`→[기존 holding report](../../src/engine/holding_exit_observation_report.py)의 `build_holding_exit_observation_report`→holding source bundle이며, 적용 consumer는 [mechanical selector](../../src/engine/automation/scalp_trailing_mechanical_policy_apply.py)와 bootstrap이다. 이 경로의 기존 report schema/actual cohort를 유지하며 공통 연구 결과를 명시적 확장 필드·봉인 참조로 연결한다. source assembler는 원 raw/census를 읽고 자신을 호출한 holding report를 다시 입력으로 요구하는 순환을 만들지 않는다. 현재 stage registry에는 별도 trailing stage가 없으므로 존재하지 않는 stage 명령을 실행계획으로 적지 않는다. 신규 코드는 기존 `automation`·`scalping`·`lifecycle` 역할 패키지에 두고 위치 gate를 먼저 확인한다.
- [제출 지연 producer](../../src/engine/scalping/pre_submit_delay_tuning.py)는 기존 raw/compact 공통 ID와 family source ledger를 읽고, 신규 PASS 원천 adapter를 같은 날짜·부모·anchor 계약으로 연결한다. 과거 원장과 연결 projection을 두 개의 고유 기회로 더하지 않는다.

### 4.2 필수 연결과 결손 처리

기회별 필수 연결은 원 판정 identity/native attempt, 원 발생·known-at 시각, machine/aux 부모 hash, symbol/session/route/epoch, anchor와 당시 가격계획/호가, 해당 후행 범위다. 실제 거래 재생에는 position·buy generation·주문/체결/잔량·실제 비용을 추가한다. 취소 대기·분할·수량·행동 정책을 제출 지연에 합치지 않는다.

1. 기존 판정 receipt·request/response·pipeline·compact·archive·당시 정책 파일에서 exact ID로만 복원한다. 현재 정책 hash를 과거 행에 붙이거나 당시 P0를 현재 REST 가격으로 채우지 않는다. 원 bytes를 수정하지 않고 원 경로/offset/hash·복원 필드·근거를 projection에 남긴다.
2. 부모 hash 결손 29건과 native 미검증 행을 각각 대사한다. 유일한 원 영수증이 없으면 `unverified_lineage`로 남겨 해당 양수 timing 후보에서 제외한다. 유효 가격쌍은 진단에 보존하고 다른 부모의 학습 근거로 합치지 않는다.
3. 후행 경로는 처음 신호부터 연결한다. PASS 이후부터 관측한 자료를 반전/ENTER_NOW 시점의 연속 원천으로 가장하지 않는다. 예정 horizon의 결손을 최근 호가로 채우지 않는다.
4. [비용 대사](../../src/engine/lifecycle/broker_cost_reconciliation.py)는 복수 position·partial·ADD·익일·venue/manual 혼재에서 exact 귀속을 검사한다. 유일 배분이 안 되면 실제 경제 cohort에서 제외하고 census에는 `actual_cost_unallocated`로 남긴다. 공식 집계 비용의 금액 비례 임의 배분을 하지 않는다.
5. 제출 지연의 가격 비교에는 체결·청산·실제 비용을 추가 필수 조건으로 넣지 않는다. 트레일링 실제 손익은 유효 actual cost가 필요한 별도 cohort다. CF 비용모형·가격 추정은 actual 손익의 대체 증거가 아니다.
6. 식별 가능한 손상 행/구간은 제외하고 정상 행을 진행한다. 글로벌 source preflight/manifest 무효·분리 불능인 손실만 해당 입력 전체를 차단한다. 복원 불가능한 과거 필드는 결손을 확정해 같은 자료의 재호출·재생을 중단한다. 새로운 API/parser/WS mapping 수정이 필요할 때만 공식 Kiwoom gate의 최신 revision·파일·조회시각을 먼저 확보한다.

전수 대사는 아래 세 장부로 나눈다. 시장 범위 수와 기회/거래 건수를 같은 보존식으로 합치지 않는다.

| 장부 | 기준 ID·보존식 | 판정 |
| --- | --- | --- |
| 범위 | symbol×market×route의 고유 `scope_key`; 현재 [scope 계약](../../src/engine/scalping/main_exit_scope.py)의 여섯 disposition 합계=`scope_count` | `operating_observed`, `operating_no_opportunity`, `operating_unobserved`, `registered_nonoperating`, `not_tradable`, `custody_excluded`를 유지. 연속 coverage 증거가 있어야 무기회 0건이며 무관측은 0건이 아님 |
| 기회 | raw 고유 event→canonical opportunity+검증된 retry alias/중복+격리 event를 대사; 각 기회는 한 번만 baseline 모집단에 포함 | source-invalid는 해당 기회/anchor 자격에서 제외, horizon 결손은 해당 pair에서 제외. 제외 주사유 하나와 복수 상세 reason을 분리 |
| 실제 거래 | position/buy generation와 정확 execution leg→적격 actual/비용 미배분/검열/수탁 제외 대사 | partial/ADD/익일을 보존하고 CF 기회 수와 합산하지 않음 |

같은 canonical ID의 서로 다른 필수 내용은 읽기 순서로 승자를 고르지 않는다. 다른 shard에서 늦게 발견한 conflict도 그 ID의 앞선 결과·split·선정을 무효화하고 함께 격리한다. 단순한 retry alias는 원 native/요청 연결이 입증된 경우만 접는다. 전체 dedup/conflict 대사가 끝나기 전에 정책을 발행하지 않는다.

## 5. W2: 상한 초과를 처리하는 분할·재개

상한을 올려 거대 입력을 한 번에 메모리에 올리는 방식으로 해결하지 않는다. 현재 공유 resident-data 64MiB, source-feature 디스크 cache 64MiB, record 64KiB, 기존 scan-job 2GiB 및 4MiB artifact 제한은 역할별로 유지하고 W0에서 합산 RSS/temp/durable output의 실제 한도를 고정한다. 디스크 cache의 메모리 상주 부분도 공유 resident 예산에 포함한다. 동일 예산을 두 family에 각각 배정하지 않는다.

현재 [Claim 예산](../../src/engine/lifecycle/research_input_budget.py)은 **한 프로세스 안에서만** 공유되며 stage dispatcher는 host-wide slot 두 개로 별도 자식을 동시에 실행할 수 있다. 이를 이미 합산 64MiB가 보장되는 구조로 보지 않는다. 이번 두 heavy 연구 job은 기존 admission 경계에서 순차 실행하도록 구현한다. 두 slot을 모두 확보하는 가중 접수를 자식 실행 전에 수행하고, 둘째 확보 실패 시 첫째도 즉시 반환한 뒤 기존 유한 대기/재개로 처리한다. 한 slot을 쥔 채 다른 job의 종료를 무한 대기하지 않는다. 직접 CLI와 profile 경로도 같은 admission을 사용하고 이미 예약한 dispatcher 자식은 예약을 중복 획득하지 않는다. 유효 lock 강제 해제·worker/slot 수 증가·새 서비스는 필요하지 않다. 두 family 동시 요청·기존 일반 stage 점유·중단/재개 반례에서 합산 peak/접수 대기·기한을 확인한다.

현재 dispatcher의 stage writer lock→host slot 순서를 기준으로 직접 CLI/profile도 같은 job writer→slot 순서를 사용한다. 예약된 자식이라는 환경변수만으로 admission을 건너뛰지 않고 실제 parent reservation·PID/start generation을 검증한다. W5 전환은 계산 job의 종료와 slot 반환을 확인한 뒤 시작하여 계산/발행/선택 lock의 역순 경합을 만들지 않는다.

| 계층 | 잔여 구현 | 종료 검사 |
| --- | --- | --- |
| 원천 scan | 파일/offset inventory와 bounded record stream으로 scan-job을 분할. 원 바이트 hash·global ID conflict/dedup index 유지 | 2GiB 초과 원천도 명시적 job 묶음으로 전수 처리. tail sampling·파일 앞부분 절단 0 |
| normalized input/feature | 경로 segment에서 상태를 이어 처리. job/candidate block별 feature cache의 eviction·재구축과 최소 완료 checkpoint | 4MiB path와 64MiB feature를 넘는 입력에서 상태/ADD/epoch/AI 인과성 동일, 완료 partition 재생 0 |
| 전역 분모·시간 분할 | bounded 정렬 run/merge로 전체 parent·anchor·session별 시각/ID 순서, 70/30 split·183초 purge 확정. 유형은 부모 split 상속 | shard 경계/크기/재개 순서를 바꿔도 qualified/train/validation/purge ID와 논리 digest 동일 |
| 후보 집계 | canonical candidate dedup·alias, 전 후보 common cohort 확정 후 최소 통계 streaming 집계 | 작은 입력의 기존 단일 계산과 전체 후보·검열·학습 승자/검증 결과 동일 |
| report/policy | 대형 qualified projection·ID 집합·history는 봉인 shard로 분리하고 root manifest에 count/hash/index. 활성 lookup은 해당 부모·시장 준비 map만 적재 | 20,000기회·4,096 cell·4MiB report를 넘는 경우도 전수 연구 완료. bootstrap/validator는 명시적 준비 상한과 전체 shard 검증 유지 |
| 재개/원자 발행 | source/code/schema/부모/cost/split generation에 결속한 완료 checkpoint와 단일 committed pointer. 필요한 leaf 전부 검증 후 CAS | 중간 종료·손상 shard·late cost·동일 크기 source 변경에서 stale 재사용/부분 정책 발행 0 |

현재 partition 수·segment/piece 수 제한도 단일 job/manifest의 상한으로 유지한다. 그보다 큰 모집단은 bounded 하위 manifest와 root inventory로 전수 연결하며 부모와 leaf의 count/hash·consumer 계약을 함께 검증한다. root에 모든 ID/segment를 다시 펼쳐 상한을 우회하지 않는다.

**물리 hash와 논리 digest를 구분한다.** 경로·분할 크기·압축·leaf 구성 변경은 artifact/manifest byte hash를 바꾼다. canonical 순서의 ID/필수 값·split/후보 결과에서 계산한 논리 digest만 동일성을 요구한다. source/code/원가 세대와 leaf byte hash는 별도로 결속하여 논리 digest가 같아도 오래된 물리 참조를 재사용하지 않는다. 재개 후 전역 시간순 split이 바뀌면 기존 pair/feature는 재사용할 수 있지만 옛 train/holdout label·후보 순위는 재계산한다.

20,000기회·4,096 cell은 현 단일 객체의 제한이며 전수 모집단을 잘라내는 기준으로 사용하지 않는다. 기존 v1/v2 단일 파일 의미는 보존한다. sharded evidence/policy가 필요하면 versioned schema와 source verifier·publisher·loader·summary/strict·semantic consumer migration을 같은 변경으로 구현한다. 작은 기존 artifact도 계속 검증한다. bootstrap은 활성 대상별 준비 map을 생성하되 실제 활성 대상이 준비 예산을 넘으면 적용은 명시적으로 차단하고, 연구 대사 완료와 구분한다.

보존할 최소 checkpoint/result와 재생성 가능한 feature cache를 구분한다. eviction은 재생성 가능한 feature에만 적용하고 완료 근거/필수 원천을 지우지 않는다. 같은 source·후보의 정상 재개는 완료 결과를 재사용하며, evicted feature가 필요한 새 후보 작업의 재계산은 해당 범위에만 계수한다. warm 결과 재사용에서도 독립 verifier의 필수 byte 검증은 유지한다. 임시·출력 disk 예상량이 예산을 넘으면 처리량을 축소하지 말고 필요한 저장량과 대상 job을 명시한다.

디스크 예산은 cache만이 아니라 정렬 run·dedup index·최소 결과·old/new generation 공존·atomic write 임시본을 합친 peak다. 이미 committed/준비된 정책이나 실행 중 job이 참조하는 leaf는 eviction 대상에서 제외한다. 회수 가능한 실패 세대·중복 cache의 목록과 해제된 참조를 기록하고, source/evidence를 지워 새 출력 공간을 확보하지 않는다. 읽기 record가 64KiB를 넘으면 완전한 record 경계를 보존해 격리/지원 상태를 기록하며 잘라 읽은 JSON을 정상 행으로 집계하지 않는다.

## 6. W3: 초기정책과 실제 소비

트레일링은 승인 시장 부모를 전체 상황 유형으로 계승하고 공통 runtime/replay 동등성을 검사한다. source-gap·표본 없는 cell도 `parent_carry`로 완결한다. 실제 비용·후행·AI·selector 조건을 충족한 후보만 기존 family 선택 계약으로 검토한다. 경제 후보 부재는 자동 연결/전수 처리 구현의 미완료 사유로 사용하지 않는다. CF나 부족한 actual 근거로 변경값을 적용하지 않는다.

경제값을 바꾸는 후보는 기존 one-market selector·same-stage canary·부모 CAS/rollback 계약을 유지한다. 전체 공통 엔진과 부모 동등 초기 구성을 모든 지원 범위에 연결하는 작업을 그 변경 후보의 한 시장 제한으로 축소하지 않는다. timing/exit의 증거와 stage 권한은 서로 대체하지 않는다.

제출 지연은 `price_ready`의 0/30/60/120/180초 초기정책을 계산한다. `signal_ready`는 별도 anchor의 진단으로 유지한다. 유효한 동결 가격 비교가 있고 양수 cell을 선정할 근거가 부족하면 근거·미지원 범위와 함께 0초 baseline을 정식 발행할 수 있다. 부모/native 미검증 cell의 `runtime_apply_allowed=false`를 유지하고 준비된 lookup이 다른 부모의 양수 cell을 빌리지 않는지 확인한다. 전체 원천/가격쌍이 무효라면 정책은 `blocked`, 기존 즉시 동작은 유지한다. blocked는 코드 리뷰 완료와 구분해 source owner/영향 범위/다음 조건을 기록한다.

정식 0초 baseline은 글로벌 source 계약이 유효하고 `price_ready` 유효 pair가 최소 한 개 있는 경우다. 이때 정책 전체의 baseline 수용과 개별 미검증 cell의 양수 실행 불가는 별도 필드로 남긴다. `signal_ready` pair만 있거나 P0만 있고 Pd pair가 없으면 가격정책은 blocked다. 특정 부모에만 미검증 행이 있으면 그 부모/cell을 제한하고 다른 exact 부모의 적격 계산은 진행한다. 새 부모가 lookup에 없으면 그 부모의 기존 즉시 동작을 사용하며, 미검증 `legacy` 부모 키를 호환 wildcard로 사용하지 않는다.

양수 cell은 기존 시간순 학습 승자를 고정하고 독립 검증으로 확인한다. 검증 결과를 보고 후보·split·공통 모집단을 다시 고르지 않는다. 원 PASS/native 요청은 원 deadline 안에서 소비·종료하고, due에는 기존 scheduler로 새 기계·보조 증거를 재평가한다. 제출은 successor 요청 자신의 deadline과 `due + 기존 entry budget(현재 5초)`를 모두 만족해야 한다. 원 요청의 만료 시각을 successor에 그대로 붙이거나 원 TTL을 늘리지 않는다. 한 원 기회의 successor가 또 delay를 arm하지 않게 하며 새 유효 PASS·가격/자금/수량/부모·기존 guard가 성립한 경우만 기존 제출 경로로 진행한다. 정규/fixed/scanner × v1/v2, due 동시 만료·새 PASS·WAIT·native claim 취소/교체를 실제 handler→guard→격리 adapter 경계에서 검증한다.

## 7. W4: 전체 리뷰·성능·종료 검사

W0의 하나의 workload/budget manifest를 동결하고 baseline/후보를 같은 host·동일 기회/호가/event 분모로 교대 측정한다. 순증 기능 비용과 기존 기능 개선을 나누되 전체 CPU/RSS/I/O/queue/deadline도 함께 검사한다. 기존 컴포넌트 시험의 수치는 reference이며 아래 미측정 경로의 PASS로 전용하지 않는다.

기존 코드가 거대 입력을 상한에서 거절하면 그 짧은 실패 시간을 성능 baseline으로 삼지 않는다. 기존 지원 범위의 동일 성공 작업은 직접 비교하고, 확장 범위는 같은 전수 입력을 처리하는 유한 순차 기준 계산과 W0 절대 예산으로 검증한다. 기준 계산도 전역 cohort/split/purge를 유지하며 shard별 평균이나 shard별 후보 승자의 투표로 대체하지 않는다. 작은 독립 손계산으로 기준 계산의 의미부터 검사하고, 대응되는 성공 baseline이 없는 신규 기능은 전체 완료량/시간/자원 수치로 보고한다.

| 시험 | 필수 측정·반례 |
| --- | --- |
| Main warm/first | 전체 정상 loop의 response→claim→guard→adapter, 정책 파일 I/O/전체 hash 0, 원 5초 의미·만료·lock 대기, fixed/scanner 공정성 |
| due/burst/slow writer | 실제 due scheduler와 새 평가 완료 경로, 다른 scanner 수요, 현재 quota 최대 기회와 horizon 동시 도래, 느린 필수/진단 writer, callback 양보·거절/유실/중복 |
| 보유 보호/청산 결합 | Main 실행 중 fast/normal trailing·soft/hard/protect/emergency의 실제 handler, 복수 보유·partial·ADD·익일·manual/퇴역 custody. 보호 판정·처리 간격 악화 0 |
| 장후 cold/warm/delta | 전체 census/source→feature→replay→selection. 변경 없음·과거 cost-only 정정·source 추가·부모/classifier/grid 변경, shard/eviction·중간 종료 재개 |
| 예산 초과 | 2GiB scan-job·64MiB cache/resident·20,000기회·4,096 cell·4MiB artifact 초과 입력을 분할한 결과와 독립 작은 기준 계산의 동일성 |
| chain 무효화 | source/checklist/code/정책/shard hash 변경, 실패한 strict 뒤 오래된 PASS, prepared successor 교체, retired consumer 부활 0 |

추가 통합 반례는 두 heavy job의 동시 admission, shard 간 뒤늦은 중복/conflict, 같은 논리 입력의 다른 shard byte hash, committed leaf를 참조한 상태의 eviction, 0초 전역 baseline과 미검증 cell, `signal_ready`만 있는 입력, W5 각 발행 경계의 강제 중단/복구다. 메모리 제한을 자료구조의 추정치만으로 통과시키지 않고 자식/부모와 남아 있는 이전 job을 포함한 실제 합산 RSS를 측정한다.

실시간 비교는 같은 입력을 baseline/후보 각 3회부터 측정하고 N·p50/p95/p99/max·개별값/변동폭·CPU·peak RSS·bytes·queue 완료/거절·deadline을 기록한다. 작은 N의 분위수를 새 합격선으로 만들지 않는다. 결정적 의미 검사는 fake clock/exception으로 독립 검증한다. 장중 tail·만료·보호 간격·queue·절대 자원 비악화와 정책/관측의 실측 개선, 장후 cold 비악화 및 warm/delta 작업량·시간 또는 CPU 개선을 기존 두 계획 gate대로 수용한다.

통합 시험은 실제 producer/handler/scheduler/writer 코드를 사용하되 모델·계좌·broker 경계는 격리 adapter와 동결 응답으로 대체한다. 검증을 위한 추가 provider/AI 호출·실제 주문은 만들지 않는다. 거대 입력은 기존 봉인 원천 참조 또는 bounded streaming fixture로 검사하며 2GiB 원장 복제본을 회차마다 저장하지 않는다. 시험기의 처리/대기 비용과 측정 대상 비용을 분리하고 task-local 임시 저장도 W0 disk 예산에 포함한다.

리뷰는 producer→projection/shard→publisher→selector→loader→due/exit→guard/adapter→summary/strict/semantic까지 수행한다. 결함을 수정하고 영향 pytest·compile·diff·문서 parser와 동일 workload를 다시 검사한다. 성능 또는 구현 결함을 OPEN으로 남긴 채 전체 구현 finding 0을 선언하지 않는다. 재리뷰·목표 시험 통과 후 입력/알고리즘 변경이 없으면 불필요한 대규모 재검증을 반복하지 않는다.

## 8. W5–W6: 최종 배포·장후 인계·기동

1. **불변 코드·전환 세트 준비:** W4를 통과한 전체 작업본으로 release 후보를 만들고 동일 producer/validator/loader·예약 cwd를 검사한다. 선택 release만 먼저 바꾸지 않는다. 원 selector·정책 committed pointer·summary/checklist/strict/controller/finalization·prepared index/manifest·관련 release 설정을 하나의 전환 목록에 원 hash와 함께 기록한다. 기존 승인 범위의 최종 release를 사용하며 당시 공통 코드 selector의 좁은 설명을 신규 승인 요구로 재해석하지 않는다.
2. **affected family 후보 생성:** 고정 source date/실제 publication date로 trailing 부모 계승 bundle과 선정 적격 후보, 제출 지연 v2를 검증 release의 명시적 input/output root에서 준비한다. 무거운 재생은 release 전환 lock을 잡기 전에 완료한다. trailing은 §4.1의 실제 snapshot/report 호출과 별도 family selector를 따른다. 기존 producer에 격리 root나 해당 profile의 제한 재생이 없으면 W1–W4에서 그 경로부터 구현·검증한다. EOD/전체 wrapper를 대신 실행하지 않는다.
3. **정식 완료 검증:** stage terminal receipt와 실제 report/policy·committed manifest/source/code/hash를 검사한다. launch exit 0이나 임시 report 존재로 완료 처리하지 않는다. source-invalid 정책을 valid-empty로 포장하지 않는다.
4. **영향받은 chain 갱신:** final source→runtime summary/source bundle→tower→대상일 checklist→strict `--require-summary-handoff`→controller/finalization 순으로 닫는다. source date와 target date를 유지하며 verifier/controller self hash 순환을 만들지 않는다. EOD와 무관한 기계/보조 AI 연구·다른 정책 재선정은 반복하지 않는다.
5. **체크리스트 successor와 최종화:** 현재 10/12 봉인 checklist는 문서 작업에서 바꾸지 않는다. W5의 실제 정식 정책 변화가 필요할 때 원 bytes/history를 보존한 successor를 발행하고 동일 stable ID `DirectFamilyPreopenPolicyHandoff`의 source/receipt/수용을 새 chain에 연결한다. 그 이후 checklist를 수정했다면 strict/finalization/PREOPEN을 다시 봉인한다. `strict_checklist_generation_stale`·`finalization_chain_generation_changed`·prepared source/release changed의 재현과 최종 무결성을 검사한다.
6. **PREOPEN·예약 확인:** 최종 release/선택 정책/source/effective date와 신규 prepared generation을 결속한다. 변경하지 않은 기계/보조 등 정책 bytes와 Main/manual custody·퇴역 OFF는 보존한다. 실제 적격일 07:35/07:55 예약의 root/계정/env/loader 및 cron routing을 확인한다. 이전 incumbent-only readiness PASS를 신규 v2 증거로 재사용하지 않는다.
7. **자연 수용:** W5 종료 시 미래 기동은 `future_due`다. 적용일 owner에서 실제 PID/cwd/start ticks·선택 부모/정책 hash를 확인하고 자연 disposition을 보고한다. PASS/주문이 없으면 `not_observed`이며 이 표본을 만들려고 호출/주문하지 않는다. 준비 PASS를 자연 제출·체결·순익 PASS로 바꾸지 않는다.

3–6은 다음 **하나의 제한된 전환 절차**로 실행한다. 기존 [release set/selection lock](../../deploy/with_runtime_release_set_lock.sh) 순서를 사용하고 active stage writer·예약기동 충돌을 재확인한다. 이 lock이 모든 family reader/writer를 자동으로 잠근다고 가정하지 않는다. family publication lock과 reader의 committed-generation pin을 함께 확인하고, 미지원 consumer는 W4에서 먼저 보완한다. nested helper가 같은 lock을 재획득해 자기 대기에 빠지지 않도록 한 owner가 전환을 소유한다.

전환은 `prepared → publishing → verified` 상태와 원/후속 pointer hash를 영속 기록한다. source/부모/selector CAS 확인→불변 policy/report와 정식 committed pointer→영향 summary/checklist/strict/finalization→최종 release 및 prepared generation의 결속 검증 순으로 진행한다. 필요한 중간 selector 변경은 같은 전환 창에서만 수행하고 마지막 정확 release 기준 검증 전에는 기동 준비 성공으로 게시하지 않는다. 여러 파일 rename을 한 개의 원자적 transaction이라고 부르지 않는다.

각 경계에서 중단을 주입해 재개 또는 **원 전환 세트 전체**의 복구를 검증한다. 새 policy pointer를 둔 채 release만 복구하는 경우를 실패로 잡는다. 복구는 이 전환이 쓴 pointer가 여전히 현재인지 CAS로 확인한 후 기존 owner의 정식 경로로 수행한다. 다른 writer의 후속 변경은 덮어쓰지 않는다. 이전 정책의 expiry/source/retirement 검사가 통과할 때만 기존 prepared를 다시 쓸 수 있으며, 실패하면 명시적 기동 준비 blocker로 남긴다. `_pre_submit_delay_handoff`는 잘못된 committed generation에서 즉시 invalid를 반환하므로 단순히 v1 파일이 남아 있다는 이유로 fallback을 가정하지 않는다.

W5는 적용일 이전의 준비이고 당일 apply는 W6 예약 경로다. [PREOPEN wrapper](../../deploy/run_threshold_cycle_preopen.sh)의 실제 순서인 readiness 검증→family apply→bootstrap을 격리한 목표일 clock으로 검증하고, 대상일 전 `--require-today`를 해제하거나 live wrapper를 수동 실행하지 않는다. trailing selector가 적용할 결과와 준비된 예상 결과가 같아야 하며, 당일 선택이 달라지면 해당 generation 불일치를 처리한다.

제출 지연은 기존 [stage dispatcher](../../src/engine/automation/postclose_summary_handoff.py)의 `--stage pre_submit_delay --date SOURCE_DATE --publication-date PUBLICATION_DATE --recover-closed-target --launch` 경로를 사용한다. `SOURCE_DATE/PUBLICATION_DATE`는 W0에서 정하는 자리표시자다. W4 종료 후 실제 운영 지침의 affected recovery/last-consumer 절차를 읽어 실행하며, 이 계획 작성에서는 명령을 실행하지 않는다. 최종 준비 확인 후 별도 산출물을 계속 변경해 봉인을 다시 무효화하지 않는다.

## 9. 완료·차단·보존 기준

- **구현 완료:** W1 전수 연결·W2 자동 초과 처리·W3 계산/소비·W4 전체 리뷰/성능의 잔여 구현 finding 0. unrecoverable source와 미래 표본을 구현 누락의 다른 이름으로 사용하지 않는다.
- **정책/운영 준비 완료:** 유효 부모 동등/0초/선정 적격 정책이 W5 정식 chain과 적용일 PREOPEN을 통과. 정당한 whole-source block이면 blocked family와 유지 정책을 명시하고 신규 정책 적용 완료라고 주장하지 않는다.
- **자연 완료:** W6 실제 소비 영수증. 실현 경제성은 valid COMPLETED/cost와 별도 window에서 평가한다. 자연 표본 부재는 구현·준비 작업을 다시 OPEN으로 만들지 않는다.
- **중단 근거:** budget 불충족, 글로벌 원천 계약 무효, source 변경 중 발행, 미해결 코드/성능 결함, strict/finalization/PREOPEN 불일치 각각을 owner/artifact/영향 범위/다음 조건/종료 시험으로 기록한다. 추가 경제 gate로 부모 계승과 0초 baseline을 막지 않는다.
- **보존/정리:** immutable 원천/원 정책/승계 이력/최종 manifest·최소 결과/검증 근거를 보존한다. full raw/AI ledger를 검증 회차마다 복제하지 않는다. 완료 후 미사용 중복·재생성 가능한 임시 cache만 사용·참조·현재/rollback 의존을 대사한 삭제 목록으로 정리하며, 원천 부족을 이유로 원 증빙을 삭제하지 않는다.

후속 실행 결과 보고는 owner별 W0–W5 상태, 전수 분모/제외/부모 계승·0초/양수 cell, source 및 코드 hash, 성능, 정식 chain/PREOPEN, 미래 PID·실현 경제 상태를 구분한다. 이전의 bounded 리뷰 완료 표현으로 전체 계획 완료를 대체하지 않는다.

## 10. 문서 검토·검증

이번 변경은 본 잔여작업 계획과 두 상세계획·PASS 계획의 연결 및 오늘 checklist 보완이다. baseline 문서와 봉인된 10/12 checklist, runtime code/정책/selector/PREOPEN은 변경하지 않는다. 로컬 링크·현재 stable owner·권한/완료 조건·공백과 print-only parser를 검사한다. provider/AI/주문·장후 재생·배포·재기동·외부 sync 및 코드 pytest/compile·성능 재측정은 문서 범위 밖이므로 실행하지 않는다.

최초 문서 리뷰에서 과거 release를 현재로 표현한 상태 설명, S6를 새 승인 대기로 오해할 여지, 상한 초과 job/manifest의 전역 분모·consumer migration 공백, 구현 완료와 자연 수용 혼용을 보완했다. parser에서 제출 지연 owner의 적용 대상이 `-`로 나오는 것도 확인해 stable ID를 유지한 채 title에 Main을 명시했다. 최초 검증은 로컬 링크/anchor 95개 결손 0, print-only parser OPEN 22건·두 현행 owner 각 1개였다. 후속 리뷰의 검증은 아래에 별도 기록하며 문서 검증을 전체 구현·성능·운영 완료로 보고하지 않는다.

### 10.1 실제 producer/consumer 대조 후 보완

| 발견한 공백 | 보완한 계약 |
| --- | --- |
| process-local Claim을 두 프로세스의 합산 한도로 오해 가능 | 기존 2-slot admission의 heavy job 가중 접수·순차 실행·직접 CLI/중단/재개 대사 |
| 추상 trailing stage만 있고 실제 등록 stage/caller 불명확 | profile snapshot→holding report→source bundle→기존 selector 연결, 입력 순환·EOD 전체 실행 방지 |
| scope·기회·거래 단위가 섞인 보존식 | 현행 6개 scope disposition과 기회/실제 거래 장부 분리, 뒤늦은 shard conflict의 전역 무효화 |
| shard 변경에도 모든 hash 동일 요구 | canonical 논리 digest와 physical manifest/leaf byte hash 분리 |
| cache만 고려하고 증거·old/new generation 공존 공간 누락 | 합산 peak disk 및 live/committed 참조 leaf 보호·안전한 eviction |
| 0초 전역 baseline/개별 cell 불가, original/successor deadline 혼동 | price_ready pair 최소 자격·cell 격리·두 successor deadline·재arm 금지 |
| 실패한 legacy 실행을 확장 기능 성능 baseline으로 쓸 가능성 | 동일 성공 작업/전수 순차 기준 계산/신규 기능 절대 예산 구분 |
| release 선택과 다중 pointer 발행·실패 복구 경계 누락 | 전환 세트·CAS/lock/상태 기록·전체 참조 복구·실제 PREOPEN 순서 검증 |

실행 문서의 권한이나 기존 정책을 바꾸지 않고 요구사항·시험·산출물 대사표로 전체 완료 여부를 판정한다. 이번 문서 리뷰의 미해결 사항은 구현 항목으로 명시했으며 이 구현이 이미 존재하거나 검증됐다고 표시하지 않는다.

후속 검증: 변경 연계 문서 5개의 로컬 링크/anchor **104개 결손 0**, 공백/fence·`git diff --check` 통과. print-only parser는 **OPEN 22건·경고 0**, 두 현행 owner는 각각 1개이며 `apply_target=main`이다. 10/12 봉인 checklist와 Plan Rebase의 SHA는 변경 전과 동일하다. 이번 계획 리뷰에서 발견한 8개 공백을 반영했으며 코드 pytest/compile·성능 측정·정책 발행·운영 재생은 실행하지 않았다.

## 잔여 구현 실행 기록 — 2026-10-10

[반복 리뷰·실제 원천·성능 근거](../audits/main-trailing-delay-residual-implementation-review-2026-10-10.md)를 따른다. 전수 streaming/shard·전역 중복/split·부모 승계와 0초 초기값·정식 writer/consumer 연결을 구현했다. 코드 수용과 W5 발행/chain, 10/12 자연 PID 수용을 분리한다. 최종 v6 발행·native finalization DONE·10/12 `current_full_contract=pass`까지 수용했다. 실제 적용일 PID·경제 결과만 별도 자연 관측으로 남는다.
