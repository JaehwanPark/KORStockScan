# Main 진입 기계판정 전체 임계치 폐루프 결손 보완계획 — 2026-09-26

상태: **코드 보완·격리 검증 진행. 9/24·9/25 원천 결손은 격리됐고, 9/28 장전 활성화·PID 소비 및 새 자연 원천 성능 수용은 미완료.** 이 문서는 [기존 승률 초기/일일 계획](./main-entry-winrate-initial-daily-tuning-runtime-implementation-plan-2026-09-24.md)의 결손 보완안이다. 새 정책 소유자나 독립 실행기를 만들지 않는다. 실행 항목은 [9/28 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `[MainEntryWinRateInitialPolicy0928]`와 `[MainEntryWinRateDailyPostclose0928]`가 소유한다.

## 1. 현재 결손과 완료 범위

| 경로 | 확인된 상태 | 장전 전 수용 조건 |
| --- | --- | --- |
| 전체 전략 좌표 | `entry_strategy_policy.REGISTRY`의 82개 좌표는 런타임 profile 계약에 있다. 기존 등록은 raw 61, trusted aggressor 2, momentum 2, micro window 4, 완료봉 13으로 분류해 공통 micro 2개·유동성 3개의 실제 원천을 놓쳤다. 기존 탐색 예산은 96개 후보 중 단일 좌표 20슬롯이므로 모든 좌표·조합의 평가를 보장하지 않았다. 9/23 평가에는 일부 scope의 원천 공백과 PREMARKET 구조 좌표 13개의 미지원이 기록됐다. | 좌표별 `supported / source_gap / evaluated / not_reached_budget` 분모와 정확한 원천·시장·후보/parent hash를 남긴다. 지원 가능한 각 좌표가 최소 한 번의 단일 좌표 변형 평가를 받거나, 미평가 사유와 다음 cursor를 남긴다. 조합 전수 탐색은 완료 주장 대상이 아니다. |
| 공통 기계 임계치 | `entry_setup_evidence`의 기존 5개 값은 런타임에서 소비된다. 별도 `MECHANISTIC_COMMON_FEATURE_GRID`는 그중 유동성 3개만 훑는다. 전략 profile은 5개를 모두 포함하지만, 두 경로의 후보·적용 범위를 혼동하기 쉽다. | 5개 각각을 전략 좌표 등록·지원 원천·실제 판정 소비·장후 후보·발행 hash에 대사한다. 독립적으로 튜닝하지 않는 축은 `fixed` 또는 `unsupported` 이유를 기록하고, 다른 owner의 하드 가드를 임계치로 오인하지 않는다. |
| 승률 초기·후속 정책 | `current.json`은 활성 `99cb0e3a…`, 9/28 대기 bundle은 `4d08df81…`이다. 대기는 `KRX|KRX_REGULAR`의 유효·신선 micro VWAP 68.75bp 이상에서 parent `ENTER_NOW→BLOCK`만 추가한다. | 초기 9/22·9/23 frozen 재현은 변경 불가 증거로 별도 검증한다. 후속 날짜는 이 고정 표본과 비교해 실패시키지 않고 현재 활성 parent·새 원천으로 평가한다. 9/28 대기 bundle과 parent CAS·scope 불변을 유지한다. |
| 실제 장후 단계 | 과거 9/24·9/25 `main_machine_policy` 실패 원인은 `initial_frozen_reproduction_mismatch`였다. 수리 후 두 날짜는 비거래일 원천 결손으로 보고서·terminal `source_gap`, stage `deferred`다. | 원천 없는 날짜를 `succeeded` 또는 신규 EV로 가장하지 않는다. 동일일 report↔terminal 해시와 명시적 source-gap stage를 수용한다. 새 거래일 후속 consumer/strict/controller는 자연 원천으로 따로 검증한다. |
| 런타임 소비 | `load_effective → for_cohort → mechanistic_entry_policy_decision`의 소비 코드는 있다. 9/26 선택 릴리스의 PID 영수증은 `not_started_on_selected_release`다. | 9/28 장전에서 날짜별 정책·`current.json`·bootstrap·선택 release·실제 PID의 bundle 및 exact-scope machine hash를 대사한다. 코드/파일 검증만으로 실제 적용을 선언하지 않는다. |

여기서 **전체 임계치 폐루프**는 모든 안전·브로커·가격·주문 임계치를 전략 튜너로 끌어오는 뜻이 아니다. 범위는 기계판정 전략 registry 82개와 기존 공통 5개에 대한 **원천 적격성 → 후보 평가 또는 명시적 격리 → 정책 선택/유지 → 런타임 소비**의 추적 가능성이다. 82개 모든 조합의 최적성, 모든 scope의 양(+) EV, 9/28 실제 거래 성과는 이 일정으로 입증할 수 없다. 보조 AI·entry split·제출 지연·청산은 별도 소유자로 유지한다.

## 2. 구현 순서: 먼저 반복 실패를 닫는다

1. **초기 재현과 일일 평가 분리:** [평가기](../../src/engine/scalping/ai_action_outcome_calibration.py)의 `build_winrate_policy_report`가 parent에 veto가 없다는 이유만으로 매일 `initial=True`로 들어가는 조건을 고친다. 날짜/원천일과 고정 초기 세대의 발행·대기 상태를 함께 본다. 고정 9/22·9/23 census, 68.75bp, train 11기회 10승과 날짜순 진단 4기회 3승은 최초 발행 전용 검증으로 보존한다. 이미 검증된 9/28 대기 generation이 있으면 9/24·9/25 실행은 이를 덮어쓰지 않는다. 후속 데이터가 부족하면 `insufficient_sample` 또는 `incumbent_carried` 보고서와 terminal을 생성한다. 원천/스키마가 실제로 손상됐으면 명시적 실패로 둔다.
2. **발행기의 CAS 및 날짜 경계:** [발행기·로더](../../src/engine/scalping/mechanistic_entry_runtime_policy.py)는 중복 일일 실행이 기존 9/28 초기 대기 정책을 덮거나 parent를 건너뛰지 못하게 한다. 초기 세대가 활성화되기 전 새 일일 원천은 관측·평가하되 동일 대상일의 staged generation 변경은 명시적 검토와 동일 parent CAS가 필요하다. 9/28 activation 이후에는 마지막 활성 machine payload/hash를 parent로 사용한다. 이미 활성화된 AI 자식 세대는 검증된 한 단계 조상 경로만 허용한다.
3. **장후 stage 종결:** [stage dispatcher](../../src/engine/automation/postclose_summary_handoff.py)의 `main_machine_policy`가 성공·적격 후보·적격 후보 없음·source gap을 서로 다른 상태로 남기게 한다. report→terminal→staged 또는 incumbent carry의 해시와 날짜를 검사하고 `legacy_machine_report`/summary/strict/controller가 실패 영수증을 PASS로 재사용하지 않게 한다. 9/24·9/25는 변경된 stage에서 마지막 영향 consumer까지 제한 재실행한다. 9/23 frozen 보고서, 원본 ledger, holdout 소비 영수증은 덮어쓰지 않는다.

## 3. 전체 좌표의 평가 및 선정 계약

1. **좌표 목록을 단일 소유자로 고정:** `REGISTRY`와 `registry_contract()`를 evaluator·runtime의 단일 기준으로 사용한다. 좌표명, 기본값, 범위, 원천, source 지원 여부, 바뀐 action 수, 평가 후보 수, 제외 사유를 exact scope별 출력한다. 새 Python 모듈이나 별도 크론은 추가하지 않는다. 5개 공통값과 전략 profile 값이 다른 경우 유효 profile/계층 fallback 값을 `applied_thresholds`와 정책 hash로 기록한다.
2. **계산 예산 안에서 전 좌표를 순회:** 현재 96후보/20 단일 좌표 슬롯만으로 82개가 한 번씩 평가된다고 주장하지 않는다. 원천 지원 좌표의 단일 변형을 먼저 결정적 순서·영속 cursor로 순회하고, 그 뒤 제한된 다좌표·유형 분기 후보를 사용한다. 중단/재개 시 동일 입력·코드·parent·원천 계약 hash이면 cursor와 결과를 재사용하고, 달라지면 새 세대로 시작한다. 날짜별 계산 시간·CPU/RSS/swap·후보/replay 횟수를 남긴다. 시간이 모자라면 `not_reached_budget`로 남기며 holdout이나 종목을 조용히 줄이지 않는다.
3. **동일 모집단의 승패·경제성:** 기계판정 자체의 `BLOCK/RECHECK→ENTER_NOW`와 기존 `ENTER_NOW`의 유지/제외를 같은 exact attempt·고유 기회 모집단에서 재생한다. AI 결과나 후단 주문을 기계 후보의 대리 승패로 쓰지 않는다. 비용 결속 `net_target_first/exact_stop_first`의 기회 가중 승률을 정책 선택 계약으로 사용하고, 표본수 보정 승률·선택 기회 수·coverage·기존 승자 보존을 함께 검사한다. 비용 후 경로 EV, paired 진입 변화, 최악 손실과 실제 완료 손익은 **별도 진단/안전 증거**로 남긴다. 결손 EV를 0이나 gross로 채우지 않는다. 기존 `machine_admission_rank`의 EV tie-break와 승률 단독 후속 계약이 동시에 같은 후보를 발행하지 않도록 정책 소유·선정 우선순위를 한 곳으로 확정한다. 68.75bp 이외의 좌표를 실운영 후속 선정에 포함하려면 구현 시 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1·§2·§7과 [traceability](../report-based-automation-traceability.md)의 등록된 정책 범위를 함께 갱신·검증한다. 그 전까지 전체 좌표 평가는 연구 증거이며 9/28 초기 정책의 적용 권한을 넓히지 않는다.
4. **유형별 fallback과 원천 공백:** exact venue/session과 사전 관측 price/tick·유동성·변동성·시총·watch age 분기는 현재 전략 tree 안에서만 선택한다. 사전 원천이 없으면 검증된 조상 profile로 돌아가고 그 사유를 기록한다. 없는 PREMARKET 구조봉이나 NXT 모집단에 임의 값을 채우지 않는다. scope별 `input → source excluded → replayable → train/holdout → selected`를 남긴다. 기존 3개 전략 scope의 설정을 다른 6개 scope로 복사하지 않는다.
5. **후보 승격:** 마지막 활성 parent와 같은 모집단·같은 비용 라벨로 비교하고, 학습에 쓰지 않은 날짜순 holdout 및 현재 [승률 계획](./main-entry-winrate-initial-daily-tuning-runtime-implementation-plan-2026-09-24.md)의 후속 표본·coverage·승자 보존 허들을 재사용한다. 초기 `winrate_initial_v1`에는 이를 소급하지 않는다. 원천·표본이 불충분하거나 동일/열위 후보뿐이면 활성 machine payload/hash를 유지한다. 원천 지원 좌표의 *평가 가능성*과 후보의 *승격 자격*을 별도 상태로 보고한다. 그 밖의 hard safety, provider, 가격, 수량, 주문 및 보조 AI 판정은 바꾸지 않는다.

## 4. 9/28 장전 직전 검증·전환 순서

| 시점 | 수행 | 중단 조건과 완료 증거 |
| --- | --- | --- |
| 9/26~9/27, 코드·격리 재생 | 실패 회귀 테스트 → 최소 수정 → self review → 보완 → 재검토. 9/23 frozen 초기 정책, 9/24·9/25 일일 후속 상태, 모든 scope·좌표의 source/evaluation manifest를 격리 입력으로 확인한다. Python compile·영향 pytest·wrapper `bash -n`·`git diff --check`, 문서 parser를 실행한다. | frozen 9/23 결과나 9/28 staged hash가 달라지면 중지한다. 9/24·9/25 원천 자체가 없거나 손상된 경우에는 source gap 영수증으로 격리하고, 결과를 합성하지 않는다. 두 날짜의 최신 terminal·후행 strict 증거가 없으면 일일 폐루프 완료를 주장하지 않는다. |
| 9/28 06:30 이전, 선택 릴리스 | 수정 커밋과 불변 릴리스를 비교하고 장후 dispatcher 및 PREOPEN 실제 경유 코드가 같은 릴리스를 소비하는지 확인한다. 설치 unit의 독립 소유자는 별도로 대사한다. | 작업본 테스트나 selector PASS만으로 PID·정책 효과를 승인하지 않는다. 릴리스 원천·정책 hash 충돌 시 기존 활성 세대를 유지한다. |
| 9/28 PREOPEN, 초기 정책 | 기존 9/28 staged `4d08df81…`와 활성 parent `99cb0e3a…`의 source/parent/rollback hash 및 exact scope를 대사한다. PREOPEN loader/bootstrap 통과 후 정해진 activation 경로로 `current.json`을 CAS 전환하고 실제 Main PID의 bundle·scope hash를 확인한다. | staged 초기 정책이 안전하게 재현되지 않거나 source/PID가 불일치하면 기존 정책을 유지하고 정확한 blocker를 남긴다. 새 자연 수익·승률은 장중 이후에만 평가한다. |
| 9/28 POSTCLOSE, 첫 새 원천일 | 등록 좌표의 평가/격리 분모, 승률·비용 후 EV 진단, 후속 허들, carry/선택, report→terminal→summary→full strict→controller/finalizer를 검증한다. 새 자연일의 wall/CPU/RSS/swap·대기 시간을 기록한다. | 이는 **장전 직전까지 완료 가능한 항목이 아니다.** 다음 원천일의 양(+) EV나 후보 선정을 장전 완료 조건으로 가장하지 않는다. |

완료 보고는 `코드 폐루프`, `9/24·9/25 장후 복구`, `9/28 초기 정책 활성화`, `실제 PID 소비`, `9/28 이후 자연 승률·비용 후 EV`를 별도로 판정한다. 안전/출처 결손은 fail closed, 적격 후보 부족은 마지막 검증된 정책 carry로 끝낸다. 이 문서는 코드 변경·릴리스 선택·봇 재기동을 실행하지 않는다.

## 5. 9/26 구현·원천 대사

- 초기 고정 재현은 9/23에만 적용하고, 9/28 대기 세대가 있는 후속 원천일은 parent·대기 bundle hash를 결속한 carry 보고서를 쓴다. 발행기는 대기 초기 세대를 덮어쓰지 않는다. `main_machine_policy`와 의미적 감시기는 `pending_initial_preserved`를 원 보고서 hash와 구분해 검사한다.
- Registry 검색은 총 96후보 예산을 유지하면서 단일 좌표 82슬롯을 먼저 방문하고, source·시도·평가·무효·다음 cursor를 좌표별로 남긴다. 공통 5개는 micro 관측 2개·tail 유동성 관측 3개와 실제 소비자 및 계층 fallback에 대사한다. 후속 연구 후보가 incumbent와 같으면 승격 적격으로 표시하지 않는다. 좌표별 평가 후보 hash·중복 후보 수도 기록한다. 승률 연구 점수는 표본수 보정 승률·원시 승률·고유 기회 수만 사용하며 비용 결속 순경로 EV·최악값·짝지은 진입 변화는 별도 진단값이다. 사용한 holdout은 선정 버전 변경 후에도 재탐색하지 않는다. 전체 registry 연구 후보의 즉시 활성화 경로는 차단한다.
- 저장소 거래일 달력에서 9/24·9/25는 비거래일이다. 해당 날짜의 `ai_decision_payloads`, `ai_decision_trace`, 요청·프롬프트·결과 및 기계 원천 파일이 현 저장본에 없다. 두 날짜의 source audit는 `source_gap`이며, 이전 날짜 누적 행을 해당 날짜 적격 표본처럼 재사용할 수 없다. 제한 재생성 결과는 날짜별 report와 terminal을 기록하되 `accepted_attempt_count=0`, terminal `source_gap`, stage `deferred`/`machine_observation_source_gap`이다. 비거래일의 후속 strict나 신규 EV를 완료로 주장하지 않는다. 기존 9/23 frozen 보고서와 9/28 staged `4d08df81…`, 활성 parent `99cb0e3a…`는 변경되지 않았다.
- 9/28 장전 적용은 불변 릴리스와 실제 PID 검증을 포함해 아직 열린 작업이다. 새 자연 원천에서 비용·승률과 82좌표 평가/격리 분모를 다시 확인한다.
- 보존된 9/23 원천 2,085행의 제한 연구 재생에서는 기존에 선택·소비한 holdout을 재검색하지 않는 계약 때문에 신규 후보 평가는 0건이다. 세 scope 모두 parent와 동일한 frozen 후보를 `candidate_equals_incumbent`로 격리했다. 좌표별 상태는 정규장·애프터마켓 각 82개 `not_reached_budget`(사유 `frozen_holdout_reuse_forbidden`), 프리마켓 13개 `source_gap`·69개 미평가다. 이는 모든 좌표를 최적화했다는 증거가 아니다. evaluator 자체는 wall/CPU 약 38.8초, peak RSS 약 1.2GiB, swap 0으로 계측됐으며 누적 원천 적재 시간은 이 수치에 포함되지 않는다. 9/28 이후 새 독립 원천에서 검색을 재개해야 한다.

## 6. 9/26 계획 대비 추가 재검토

- 격리 테스트 입력 13건·200건에서 96슬롯을 끝까지 순회했다. 200건에서는 고유 후보 88개를 평가했고 좌표 63개 `evaluated`/19개 `source_gap`, 평가 좌표의 후보 hash 63개를 확인했다. wall 20.20초, user CPU 20.33초, 최대 RSS 132,788KiB였다. 선택된 테스트 후보의 train 승률 66.67%, holdout 승률 66.0%, 비용 결속 경로 EV는 각각 −0.0333%, −0.04%였다. **격리 입력의 코드·성능 검증이며 실거래 EV나 9/28 정책 선정 증거가 아니다.** 표본은 두 날짜에 복제한 fixture이므로 대규모 자연 원천의 지연·메모리 상한을 증명하지 않는다.
- 기존 registry rank의 EV·paired delta 동률 해소는 승률 단독 선정 계약과 충돌했고, `machine-policy-only --activate-now` 및 직접 strategy 활성화는 `allowed_runtime_apply=false` 연구 후보를 적용할 수 있었다. 이 경로를 막고 선정 버전을 올렸다. 연구 결과는 계속 보고 전용이며 초기 68.75bp의 별도 장전 경로와 권한을 혼합하지 않는다.
- 남은 수용: 9/28 자연 원천에서 82좌표의 정확한 source/평가/격리 분모와 stage wall·CPU/RSS/swap을 확인하고, 별도 승률 후속 허들과 전체 terminal chain을 검증한다. 200건 결과만으로 장후 대규모 성능이나 실거래 수익성을 완료 판정하지 않는다.
