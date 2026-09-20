# 장후 최종 검증·통합 재생성·9/21 PREOPEN 기동 준비 계획

작성일: 2026-09-20 KST. 범위: 장후 목록 25–29번 최종 검증, 앞서 지적한 구현 계약 재판정, 전체 활성 장후 체인의 복구·재생성·모니터링 및 다음 정상 기동 준비.

## 1. 목적과 기준

사용자 확인: **9/17 장후 실패, 9/18 봇 중지로 매매 관측 미적재, 이후 전체 장후 개선, 다음 정상 적용일 9/21**이다. 9/18을 거래소 휴장 또는 정상 무거래로 간주하지 않는다. 다른 DB/EOD/독립 source가 존재하면 별도 날짜·owner로만 사용한다.

이번 요청의 산출물은 점검과 상세계획이다. 코드·cron·systemd·정책 변경, 장후 재실행, PREOPEN 확정, 봇 기동은 이 문서 작성으로 실행되지 않는다. 후속 실행은 기존 승인 경계 안에서 아래 순서를 따른다.

- `source_date=2026-09-17`: 실패분 재평가 원천 날짜. 원 관측시각과 모집단을 유지한다.
- `publication_date=2026-09-20`: 실제 재생성·준비 발행일. 자정을 넘으면 실제 발행일을 기록하고 적용일과 freeze 경계를 다시 검증한다.
- `effective_date=2026-09-21`: 다음 정상 PREOPEN에서 소비할 날짜. `next_trading_day(source_date)`만으로 계산하면 9/18이 되므로 publication/effective 계약을 사용한다.
- `run_id`, code commit, source generation, report/policy hash를 구분한다. 날짜가 같다는 이유로 이전 성공·실패·부분 재실행을 합치지 않는다.
- 신규 양수 후보가 없으면 검증된 incumbent/baseline carry로 기동 준비를 닫을 수 있다. 해당 필수 consumer에 유효 incumbent 또는 기존에 허용된 fallback/disabled 계약까지 없으면 그 기동 readiness는 FAIL이다. 진단 family의 경제성 결손을 전체 기동 금지로 확대하지 않는다. source gap을 no-edge나 이익 0으로 바꾸지 않는다.
- 전체 재생성이란 **모든 활성 owner의 현재 코드·입력에 대한 결과와 최종 소비를 빠짐없이 재검증하는 것**이다. 동일 fingerprint의 유효 결과는 hash·scope·후행 의존을 검증해 reuse하고, 변경·실패·미완료·누락 단계는 실제 재생성한다. 과거 raw 전체 스캔·holdout 재학습·퇴역 producer 복원은 포함하지 않는다.

선택 기준은 `compact-aux-future-evidence-reviewed-20260920-a198c3b9b`, commit `a198c3b9bb3e0d78bff3feebe05b3d394a467973`이다. 점검 시 `actual_pid_consumed=false`였다. 실행 시작 시 다른 세션의 successor와 선택 상태를 다시 읽고, dirty 작업본 전체를 배포본에 복사하지 않는다.

## 2. 25–29번 재점검 결과

코드 근거는 위 선택 release의 `src/engine/verify_threshold_cycle_postclose_chain.py`, `deploy/run_threshold_cycle_postclose.sh`, `src/engine/automation/postclose_done_controller.py`, `postclose_summary_handoff.py`다.

| 번호 | 확인된 현행 동작 | 보완할 계약 |
| --- | --- | --- |
| 25 main scoped | `_main_mechanistic_scope`가 source date로 모든 dated policy를 찾아 마지막 파일을 선택한다. report→policy는 검증하지만 해당 함수 자체는 summary/checklist를 대조하지 않는다. | 원하는 effective date를 명시해 단일 정책을 선택하고 main source→bundle→summary/checklist를 검증한다. 다른 적용일 파일이 나중에 생겨도 올바른 기존 적용일 결과가 바뀌면 안 된다. |
| 25 compact scoped | `verify_compact_handoff`가 모든 적용일에서 같은 source/hash policy가 정확히 하나라고 요구한다. scoped CLI 분기는 `--require-summary-handoff`를 별도 해석하지 않는다. | source/publication/effective date를 고정한다. 두 날짜의 유효 carry가 공존해도 요청 날짜만 검증한다. scoped PASS에 검증한 범위를 명시하고 summary 결속 옵션을 실제 수행하거나 부적합 조합을 거부한다. |
| 26 DONE 전 verifier | `--allow-pending-done-marker`는 terminal 검사를 생략하고 일반 `status=pass`를 반환한다. `disabled_stages`, `allow_pending_entry_replay`는 현 함수에서 사실상 메타데이터다. | `preterminal_verified`와 전체 terminal PASS를 구분한다. 활성 owner 누락을 allow-pending/OFF 인자로 숨길 수 없게 한다. 폐기된 옵션은 호환 진단 또는 명시적 거부로 정리한다. |
| 27 print-only parser | 현 parser는 정상 동작하지만 출력 27건 중 현재 체크리스트 11건 외에 runbook 3건·4월 reference 13건도 포함한다. wrapper는 stdout을 버린다. | 전체 parser 성공과 현재 체크리스트 owner 검증을 구분한다. 현재 Due/ID/중복/필수 owner를 검증한 요약을 기존 run 증거에 남긴다. 역사적 reference를 현재 실행 큐로 승격하지 않는다. |
| 28 status/DONE | wrapper 2042행부터 `succeeded`와 DONE을 쓴 뒤 2048행부터 final strict를 실행한다. 실패 trap은 뒤늦게 FAIL을 기록한다. | 후행 소비자가 임시 DONE을 성공으로 먼저 읽는 경합을 제거한다. 검증 완료 상태와 최종 성공 상태를 분리하고 마지막 필수 검증 통과 후에만 최종 DONE을 발행한다. |
| 29 final strict | `require_done_marker`는 `postclose.status == succeeded`만 검사한다. target date·exit code·실행 ID·code generation을 확인하지 않는다. | terminal schema/date/run/exit/source generation을 검증한다. 오래된 성공 또는 다른 실행의 성공을 현재 완료로 인정하지 않는다. |
| 29 검증 receipt | `_write_verification_receipts`는 `immutable=true`를 기록하지만 날짜별 동일 `attempt_YYYY-MM-DD.json`을 덮어쓴다. family-only 결과는 stdout에만 있다. | 기존 attempts 저장 위치를 활용해 run/attempt별 불변 receipt를 저장하고 canonical은 latest 포인터/요약으로 관리한다. 실제 명령·종료코드·mode·해시를 남기고 실패 후 옛 PASS를 재사용하지 않는다. |
| 후행 controller/finalizer | controller의 `summary_handoff_only`는 main terminal 검사 없이도 `status=done`을 낼 수 있다. 기다림/재시도 인자는 현재 본문에서 실행되지 않는다. finalizer는 설치되지 않은 controller/tuning/archive를 고정 선행조건으로 기다린다. | scoped summary 완료와 전체 chain 완료를 분리한다. 선행조건을 현행 실행 owner에 맞추고, 필요한 bounded wait를 실제 구현하거나 호출자가 책임지도록 단일화한다. |

**읽기 전용 재현 증거:** 실제 9/17 summary를 그대로 읽고 메모리에서 terminal만 바꿨다. 현 원본은 `fail / postclose_terminal_status_missing`; `{status:succeeded,target_date:2000-01-01,exit_code:17}` 및 `{status:succeeded}`는 모두 `pass / issues=[]`였다. 운영 파일·정책은 쓰지 않았다. 이는 유효 경제성의 실패가 아니라 전체 완료 판정의 false PASS 결함이다.

현재 canonical verifier 9/20 11:13:58 결과는 issue 한 개 `postclose_terminal_status_missing`이며 실제 9/17 status는 `failed/command_failed/exit_code=1`이다. 이 하나를 수동 수정해 성공으로 만들면 안 된다. 현 verifier가 검사하지 않는 실행 세대·독립 timer·기동 소비 계약도 함께 닫아야 한다.

## 3. 앞선 구현계약 지적의 재판정

| 대상 | 재확인 결과 | 통합 작업에서 할 일 |
| --- | --- | --- |
| cancel-wait | 기존 CW0–CW6, lossless projection/census, native cancel/exit/cost 평가와 회귀가 이미 있다. 9/17 producer manifest에는 신규 execution stages가 선언돼 있지 않다. | 과거 census 부재를 미래 producer 미구현으로 단정하지 않는다. 현 선택 코드의 emitter→flush→partition→census→reader 연결을 실제 회귀로 확인하고, 과거 제외·미래 계약·자연 모델 표본을 별도 전달한다. |
| entry split | ES0–ES6 경제성/holdout/정책 소비 및 ES7 성과 경로 완료 리뷰가 초기 미완료 리뷰를 대체한다. 현 코드에는 producer roundtrip·활성 정책·holdout 회귀가 존재한다. | 초기 리뷰를 근거로 재구현하지 않는다. 현 release 포함 여부와 exact producer 지원 입력부터 확인한다. 과거 `operating_paired_source_missing`과 미래 정상 유입 여부를 분리하고 같은 source gap을 취소/분할에서 중복 수리하지 않는다. |
| low-price actual/expansion | source gap·no-fill·actual floor·custody가 profile별로 공존한다. expansion은 summary에서 `target_date_matches=false`, receipt invalid다. | 날짜 필드 의미/selector와 실제 경제성 원천을 따로 점검한다. missing-stage=정상 0으로 처리하지 않고 실제 durable producer·profile/leg 분모·bounded reader를 대사한다. 이미 구현된 LP-B0–B6를 다시 만들지 않는다. |
| scale-in split | actual fill 5건, applicable 0, terminal clock 결손 2건이 같이 존재한다. | 수량/시장성 때문에 부적격인 것과 clock 유실을 나눈다. clock 미래 writer가 입증돼야 해당 결손을 자연 대기로 닫는다. closure-test 누락을 보완한다. |
| main mechanistic | summary `_economic_section`은 `report_scope`와 `noncompact_sections_refreshed`만으로 미래 생성 계약 verified를 추정한다. 1715는 full population이며 operating paired 유효 수와 같지 않다. | **자연 대기만 남았다는 앞선 판정을 정정한다.** [메인 계획 §14 ME8–ME13](main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md#14-공통-데이터미진입-기회비용-경제성-연결-상세-보완계획)의 별도 owner가 changed 8건·scope·실행 경제성·미래 생성 근거를 보완한다. 이 통합 작업은 결과/회귀/정책 해시를 받아 소비한다. |
| compact auxiliary | exact-plan 미래 계약 수리와 incumbent publication이 있으나 과거 21건은 비교0이다. | EO 후속 코드의 실제 emitter→model→paired→consumer 계약을 reuse 검증한다. 자연 표본/독립 holdout 부재와 구현 결손을 혼합하지 않는다. |
| 공통 요약/closure metadata | main/compact에만 역사·미래 분리 특례가 있고, 다른 source-gap/mixed는 대체로 `producer_repair`로 투영된다. 일부 closure test는 null이다. | 기존 producer의 검증된 future 계약/회귀 version·first blocker·owner·closure를 읽도록 보완한다. flag를 무조건 true로 추가하거나 보고서 완료만으로 자연 대기를 만들지 않는다. |
| 설치·release binding | main 20:10/07:35 PREOPEN/07:55 기동은 cron에 있다. widget evaluation과 live widget service 일부가 실행 root와 PROJECT_DIR/PYTHON_BIN 환경이 다르다. machine timer는 별도 구버전 pin이다. | 서비스별 실제 사용 env를 추적하고 호환성이 검증된 source root로 정렬한다. 서로 다른 서비스의 정상 고정 정책 경로/override까지 일괄 최신화하지 않는다. |

경제성 계산·future emitter의 완료 여부는 기존 증거+현 코드+영향 회귀로 확정한다. 단순 source gap 보고서나 이전 “완료” 문구만으로 어느 쪽도 단정하지 않는다. 회귀 통과한 과거 결손은 원본 제외를 보존하고, 미지원 scope나 실제 누락은 구체 수리로 남긴다.

## 4. 기존 owner 중심 구현 묶음

### R0 — 실행 입력·병행 작업 고정

1. 최신 선택 release/remote commit, dirty worktrees, 활성 PID/cwd·lock/FD, 디스크·메모리를 한 번 확인한다. active writer의 코드/입력·실행 중 배포본은 수정하지 않는다.
2. 메인 ME8–ME13와 compact 공유 helper의 편집 owner를 확인한다. 미완료 변경을 가져와 임의 완료 처리하지 않고 커밋·영향 테스트·미지원 범위 receipt를 인계받는다.
3. 기존 status/verification/정책/holdout ledger/원장을 hash와 함께 보존한다. 9/17 실패 이력은 새 복구 run의 predecessor다. source·publication·effective 날짜를 각 owner에 적용한 표를 준비한다.
4. 실행 plan을 기존 wrapper/controller 경로에서 출력 가능하게 한다. 현재 없는 recovery/effective-date 인자는 구현·테스트 뒤에만 사용한다. 새 서비스·DB·collector·범용 scheduler는 만들지 않는다.

### R1 — 25번 family verifier의 정확한 날짜·소비 연결

- 기존 CLI/helper에 필요한 effective/publication 선택을 추가하고 모든 caller가 동일 요청 날짜를 전달한다. 날짜 미지정 호환 경로는 기존 dated receipt로 한 날짜가 확정될 때만 허용한다.
- main과 compact는 같은 bundle 안에서도 독립 source hash·scope·terminal·parent를 검증한다. 하나의 finalize가 다른 family를 덮으면 FAIL이다.
- summary/checklist 검증과 family-only 검증의 범위를 receipt에 명시한다. compact marker만 맞고 본문이 변조된 경우도 현재 의미 계약과 대사한다.
- stale·self-hash·parent·scope·holdout failure는 해당 승격을 차단한다. 유효 carry는 통과시키되 신규 경제 개선으로 기록하지 않는다.

### R2 — 26~29번과 controller의 완료 상태 정리

- 기존 status에 run identity·source/code generation·phase·검증 receipt 참조를 보강한다. state 흐름은 `running → producers_completed → verification_passed → succeeded`; 실패는 해당 run의 `failed`와 first cause를 기록한다. 이름은 기존 계약과 통합하되 임시 완료가 전체 DONE으로 해석되지 않게 한다.
- 마지막 strict는 `producers_completed` 증거와 봉인된 산출물 집합을 검증하고, wrapper가 그 성공 receipt를 결속해 원자적으로 `succeeded/DONE`을 발행한다. consumer는 둘의 일치를 확인한다. terminal을 요구하는 verifier와 terminal을 기다리는 wrapper 사이 순환 의존을 만들지 않는다.
- report→policy→summary→checklist→verification→terminal은 단방향 hash로 구성한다. verifier/controller/self hash를 선행 summary hash에 재귀적으로 넣지 않는다. canonical 파일 갱신 중단·프로세스 종료에도 이전 PASS가 현 run 성공으로 보이지 않아야 한다.
- reuse한 producer는 원래 run/code/as-of/hash를 보존하고 이번 run의 채택 receipt에 호환성·입력 fingerprint·제외 사유를 결속한다. 재사용 원본의 실행 시각/commit을 이번 값으로 위조하지 않는다.
- 기존 attempts 디렉터리에 실제 불변 파일을 쓰고 canonical receipt는 해당 attempt를 가리킨다. 재시도 때 첫 실패 원인은 보존하고 새 시도는 독립 기록한다.
- `summary_handoff_only`는 summary scope만 완료한다. main 실패를 전체 DONE으로 바꿀 수 없다. 전체 완료 consumer는 mode·run·terminal을 함께 검사한다.
- 현재 체크리스트 파싱 결과를 검증하되 과거 reference workorder를 새로운 실행 대상으로 가져오지 않는다. wrapper/schedule 계약을 실제 수정하는 후속 변경에는 영향받는 운영 문서와 기존 checklist owner도 함께 갱신한다. scoped 또는 pending PASS만으로 PREOPEN 준비 완료를 선언하지 않는다.

### R3 — 실제 활성 작업과 finalization 의존 정리

권고 topology는 **main + widget + machine 독립 producer → 기존 finalizer의 한 번 최종 인계**다. controller는 finalizer가 호출하는 summary/검증 helper로 재사용하고 별도 20:10 중복 cron을 자동 복원하지 않는다.

- 현 설치에서 OFF/비설치인 tuning late-pass·archive가 실제 현행 consumer에 필수인지 확인한다. 필수면 기존 owner만 일정/의존에 명시하고, 비필수면 finalizer의 무조건 대기에서 제외한다. 과거 cron 주석을 근거로 모두 복원하지 않는다.
- EOD는 시장 DB owner다. 9/18 DB가 있더라도 봇 미수집 사실을 바꾸지 않는다. 9/17 frozen 원천 평가에 사용 가능한 as-of 쿼리를 검증한다. 최신 DB 날짜가 9/18이라는 이유만으로 9/17 행 존재/coverage를 실패시키지 않는다.
- widget 4단계와 machine 8단계의 단계별 rc·source date·generation을 기존 receipt로 결속한다. unit 현재 Result만으로 과거 재실행 성공을 판정하지 않는다.
- main summary가 machine보다 먼저 끝난다고 단정하지 않는다. 소요시간과 무관하게 **모든 필수 producer terminal 후 최종 hash 집합**을 묶어야 한다.
- `postclose_summary_handoff.source_paths`의 현 direct 모드는 runtime summary 하나만 참조한다. widget/machine 결과가 그 summary에 없으면 이 최종 검증으로 보장되지 않는다. 기존 intake/summary owner에 active dependency receipt를 보강해 source/정책/모든 실행 owner 미분류0을 검증한다. 공통 Daily/EV를 복원하지 않는다.
- tower를 유지한다면 경제성/선택을 새로 계산하지 않는 요약으로 한 번 갱신한다. 필수 consumer가 없다면 whole DONE의 허위 전제에서 제외하되 최종 직접 evidence coverage는 줄이지 않는다.

### R4 — 9/17 과거 복구 모드와 9/21 정책 발행

- main은 현재 `THRESHOLD_CYCLE_POLICY_PUBLICATION_DATE`를 지원한다. split/cancel/scale/low-price/scanner/위젯·machine publisher도 각 기존 CLI의 source/effective 계약을 조사해 동일 적용일로 연결한다. 지원하지 않는 인자를 있다고 가정하지 않는다.
- widget wrapper는 현재 명시 날짜를 받지 않고 최신 완료 거래일을 계산한다. machine wrapper는 명시 과거일을 거부한다. 기존 wrapper에 명시적 historical recovery를 보강해 target 9/17을 고정하고 자동 정기 날짜 선택은 유지한다.
- finalizer의 기존 `--recover-closed-target`는 0~1일 전만 허용하므로 9/20의 9/17 복구에는 사용할 수 없다. 기존 recovery owner에 승인된 source date·입력 manifest·freeze·run lock 조건을 검증하는 과거 재생성 경로를 보완한다. 시스템 시각·원천 날짜·성공 marker를 위조하지 않는다.
- `research_native_capacity_source`는 당일 20:05 이후 계좌 상태만 허용한다. 과거 복구에서는 저장된 당시 capacity/custody를 읽고, 없으면 null/excluded를 유지한다. 오늘 계좌·미체결·현금 조회를 9/17 원천으로 저장하지 않는다. `--collect-costs`도 당시 provenance가 있는 저장 증거만 쓰도록 분리한다.
- source snapshot과 이미 소비된 과거 정책은 불변이다. 아직 freeze되지 않은 9/21 prepared 정책만 승인된 generation으로 발행한다. 후보 재학습/holdout 재사용은 기존 원장을 존중하고 동일 구간 재계산은 역사 진단임을 기록한다.
- 복구 모드의 Telegram notify·자동 workorder 실행·기동/주문 side effect를 명시적으로 비활성화한다. 원래 승인된 guard·수량·budget·custody·operator override는 그대로 검증한다.

### R5 — 결손 분류와 기존 경제성 구현의 closure

- cancel/split 공유 lossless source를 한 번 검증한다: 실제 emitter→compact/partition→producer seal/census→bounded consumer→native owner receipt. 임의 완성 evaluator fixture만 넣는 검증으로 대체하지 않는다.
- low-price는 profile별 actual/expanded 분모, source availability, holding/custody, 유효 비용·정책 날짜를 분리한다. large raw를 매번 전수 읽는 reader가 있으면 기존 partition/index/checkpoint를 우선 연결한다.
- main 경제성 보완은 기존 ME8–ME13 owner의 변경과 테스트를 통합한다. summary의 future verified 추론과 full population=paired count 표기를 고친다. main 개선 범위를 compact 보조판정으로 대체하지 않는다.
- `historical_evidence_state`, `future_contract_state`, `economic_state`, `promotion_state`, `startup_readiness`를 기존 report section에서 서로 구분한다. 모든 상태에 blocker/owner/closure가 있어야 하며 표본 부족도 지원 계약이 입증돼야 한다.
- 검증된 모델 ΔEV, 실제 완료 순익, 인과적 개선은 별도다. 미래 성과 부재는 구현 종료를 막지 않지만 실행 가능한 미완료 계약을 자연 OPEN으로 넘기지 않는다.

### R6 — 기동 consumer와 release 준비

- 공통 router와 widget/episode/live·preflight·collector unit을 별도로 대사한다. 서비스별 ExecStart/cwd/import/project/python이 의도한 reviewed release를 소비하는지 확인한다. 여러 서비스가 서로 다른 릴리스를 쓰더라도 계약 호환이 증명되면 강제 단일화하지 않는다. 한 서비스 안의 혼합 경로는 해소한다.
- 기존 고정 exit 정책 파일, custody 원장, owner별 승인 수량, 수동 override/expiry, 계좌 guard를 보존한다. main의 공통 bootstrap이 widget/episode 전체를 승인했다고 해석하지 않는다.
- 준비 검증은 offline reader/selector와 임시 검증 경로를 사용한다. 9/21 PREOPEN canonical env/applied receipt를 오늘 조기 생성하지 않는다. 준비 policy→동일 loader/fallback/hard block 검증은 오늘 완료한다.
- 필요한 코드 리뷰·영향 회귀 뒤 관련 변경만 commit/push하고 immutable successor를 선택한다. 기존 실행 PID는 변경하지 않는다. 실제 unit/env pin 변경은 배포 diff에 포함해 재검증한다.

## 5. 전체 활성 장후 재생성 순서

아래 큐는 검증된 successor에서 수행할 **후속 실행계획**이다. 불변 source와 run ID를 공유하고 단일 writer lock을 확보한다. main 내부 기존 순서는 유지하며 교차 의존이 변경된 경우 소비자부터 재생성 범위를 산정한다.

| 묶음 | 포함 작업 | 재생성·reuse 판정 |
| --- | --- | --- |
| A 입력 확정 | 기존 EOD/DB의 9/17 as-of, retained compact/partitions/census/owner ledger/비용 provenance, source-quality preflight | 체크포인트·크기·해시 선확인. 원천 없음은 명시적 결손, 9/18 미적재는 정상0으로 추가하지 않음 |
| B main 초기 | economic reference, sim post-sell feedback, rising-missed feedback, 저가주 expanded/auto-expansion, breadth, strategy-position fact sync | unchanged 결과는 지원된 reuse; 원장/DB fact 쓰기는 기존 owner의 idempotence 검증 후 한 번 |
| C execution families | scale-in split, entry split, ADQ source/labels, cancel-wait, pipeline verbosity, source-quality final, 삼성 관측, low-price actual | active scope 전부 결과/제외/후보/carry를 남김. old giant raw나 반복 모델 학습을 강제하지 않음 |
| D main/compact | main full evaluator/publisher → compact candidate/finalize → WS/scanner 부모 평가 → rising-missed prior | main·compact 독립 원천 보존; prepared 9/21 bundle. final audit 또는 부모 source가 바뀌면 종속 family만 무효화해 순차 재생성 |
| E widget | advisory calibration → auto-trade policy calibration → historical EOD gate → symbol signal research → symbol runtime policy | 독립 기동 owner·당시 승인 수량 기준. 원천 부족이면 검증된 기존 정책 carry 또는 정확한 block |
| F machine | 저장 capacity 확인 → collector expansion → microstructure attribution → weakness hysteresis → entry timing → research closed-loop → microstructure postclose approval → completed-machine checklist 연결 | 과거 복구에서 fresh account/cost 조회 금지. 단계별 실패를 마지막 builder 성공으로 숨기지 않음 |
| G 최종 인계 | 모든 필수 producer terminal → runtime summary/필요한 tower → 다음 checklist → #25 family 검증 → #26 preterminal 검증 → #27 parser → #29 final evidence 검증 → #28 최종 terminal 발행/receipt 대조 | 정상/재사용/유효 제외/부적격/실패 구분, 현 run 전체 coverage 확인. #28/#29의 기존 순서는 R2에서 경합 없이 변경 |
| H 운영 마감 | 기존 finalizer/controller의 전체 완료 receipt, 필요한 storage/cleanup·detector | cleanup은 모든 writer 종료 뒤. 원천·holdout·rollback·준비 정책 보존. 운영 storage 실패와 경제성0을 구분 |

main 29개 행에는 OFF 분기·상태 marker·검증이 포함돼 있으므로 29개 경제 튜너가 아니다. E/F 독립 timer 내부 작업도 전체 재실행 범위에 포함한다. 퇴역 Daily/EV/Pattern Lab/PYRAMID/전용 drought/limit-down 등을 missing을 이유로 재활성화하지 않는다.

새 동일 날짜 산출물이 upstream hash를 바꾸면 그 소비자부터 마지막 strict까지 닫는다. 이번 실행 중 candidate/holdout 날짜를 반복 선정하거나 최적값이 나올 때까지 돌리지 않는다. full run이 실패하면 first failing owner를 수리하고 해당 후행만 재개하며, 이미 완료된 원천 수집 전체를 다시 돌리지 않는다.

## 6. 집중 회귀와 완료 조건

기존 `test_verify_threshold_cycle_postclose_chain.py`, wrapper/finalization/controller, `test_runtime_approval_summary.py`, `test_build_next_stage2_checklist.py`, policy/producer tests를 확장한다. 기존 광범위 PASS를 무의미하게 재실행하지 않고 변경 함수와 직접 소비자만 검증한다.

| 계약 | 반드시 재현할 통과·실패 사례 |
| --- | --- |
| terminal | 현재 날짜/실행/commit/exit0/필수 rc 전부 일치 PASS; 과거 성공·날짜 누락·exit17·새 FAIL 뒤 옛 DONE·프로세스 중단은 FAIL |
| 단계 권한 | scoped/preterminal/summary-only PASS는 whole DONE 아님; pending/disabled 옵션으로 active stage 누락 우회 불가 |
| 적용일 | source9/17/pub9/20/effective9/21; 같은 source의 다른 날짜 정책 공존; 자정 경과; frozen/이미 소비된 정책 덮어쓰기 거부 |
| 경제성/분류 | supported producer 입력의 실제 계산→독립 holdout→후보→loader, no-edge carry, 과거 census 부재+미래 계약 검증, 미래 미구현은 repair, null 보존 |
| holdout | input/code correction 뒤 같은 holdout 재사용을 독립 증거로 승격하지 않음; incumbent/후보 총수량·예산·공통 guard 동일 |
| final handoff | widget/machine late generation 후 모든 직접 hash 갱신; self-hash 순환 없음; 실패 writer/rc를 summary나 체크리스트 생성으로 은폐 불가 |
| recovery side effect | fake clock/account/provider/order/notify adapter로 과거 날짜의 fresh 조회·주문·기동·중복 provider 호출 0; 기존 saved source만 소비 |
| 정상 기동 | prepared policy의 승인 candidate/유효 carry loader 성공, stale/hash/scope/operator 충돌은 기존 차단, main/widget/episode owner별로 확인 |

Python compile, shell `bash -n`, affected pytest, `git diff --check`, 문서 link/owner/print-only parser를 시행한다. 이번 계획 수립에서는 코드 테스트 전수를 실행하지 않았다. 위 terminal false PASS만 메모리 fixture로 재현했다.

## 7. 오늘 실행과 내일 자연 모니터링

### 7.1 9/20 준비 마감

1. R0–R6 수리·리뷰·재검증과 병행 main 변경 통합을 먼저 닫는다.
2. A–H 전체 활성 큐를 실행/검증 reuse하고 actual run ID·명령·rc·hash·wall time을 기존 logs/status/receipt에 남긴다.
3. 준비 완료 보고에 9/21 family별 `candidate / incumbent / disabled / blocked`, source/publication/effective date, 직접 consumer, operator/custody guard, failure fallback을 제시한다.
4. 목표는 9/20 안에 준비 완료다. 미완료 시 next action/예상 잔여·현재 blocker를 공개하고 **최종 기동 준비 검증은 9/21 07:20 이전**에 판정한다. 이 시각은 새 cron이 아니라 07:35 PREOPEN 이전 준비 여유다. 미충족을 PASS로 처리하지 않으며 기존 fail-closed를 우회하지 않는다.

### 7.2 실행 중 모니터링

- 장기 명령은 기존 detached 실행/owned log와 PID/cwd/lock을 결속한다. 30~60초 간격으로 bounded tail·단계 시작/종료·checkpoint progress를 확인하며 수분 단위로 진척을 설명한다.
- 자원 대기는 기존 guard의 이유·현재 progress·timeout을 기록한다. 메모리 floor를 낮추거나 제한을 풀어 성공시키지 않는다. live 단위와 중복 실행을 중지시킬 권한은 별도로 확인한다.
- 원천 대기·모델 표본 대기·계산 진행·source gap·실행 실패를 별도 표시한다. 재현 불가 과거 원천은 terminal exclusion으로 닫고 무한 polling하지 않는다.
- notify/API/provider 실행이 필요한 경로는 기존 승인 scope·예산 안인지 확인한다. source gap이면 불필요한 호출0. 거래/기동 검증용 주문은 하지 않는다.
- 실패 후 수정은 새 immutable successor에서 한다. 이전 run은 실패 receipt로 남기고 입력/checkpoint 호환성을 검증한 뒤 필요한 후행만 재개한다.

### 7.3 9/21 설치된 정상 경로

| 시각/경로 | 확인할 사실 | 완료 증거 |
| --- | --- | --- |
| 07:20 준비 검토 | 전체 재생성 terminal, 신규/보존 정책9/21, service pin·정책 경로 실존/해시·기동 hard blocker | 날짜별 준비표, 검증 receipt; 신규 이익 보장 아님 |
| 07:35 공통 PREOPEN | 각 family publisher→bootstrap→entry/holding loader, 실제 종료코드/accepted/rejected/fallback | 당일 PREOPEN manifest/env/verify와 정책 hash; 오늘 조기 실행 금지 |
| 07:55 main cron | selected release/cwd·실제 자식 PID·bootstrap/bundle hash 소비, health/source writer | 실제 PID receipt. 배포 receipt와 분리 |
| 07:57 삼성 morning episode | 해당 service의 source root, owner 수량·custody·전용 preflight와 dated policy | episode loader/ready 또는 정확한 block 사유 |
| 07:58 widget | service root·runtime policy·승인 symbol/quantity·기존 exit/custody guard | widget ready/실제 소비 receipt. main bootstrap만으로 대체 불가 |
| 08:57/08:58 collector | 설치된 symbol runtime/research collector의 scope·등록·freshness | 첫 자연 source·coverage. 앞선 주문 서비스의 필수 의존이면 늦은 기동 순서 결함으로 수리; 비의존이면 그대로 유지 |
| 09:15 이후 저가주/별도 episode preflight | 각 profile별 실제 timer와 source date·policy·guard | scheduled preflight/loader 결과. 없는 기회·주문을 만들지 않음 |
| 장중·장후 | 미래 exact plan/census/route→판정/submit/terminal→비용; 적용 version별 중복 제거 | rolling/cumulative 순익·EV·tail·노출·모델오차, 모델 ΔEV와 분리 |

점검 당시 `DirectFamilyPreopenPolicyHandoff` 시간창 08:45~08:55는 07:55 main/07:57 episode/07:58 widget 기동보다 늦다. 현재 체크리스트는 기존 ID를 유지해 07:35~08:05로 보정했다. builder도 동일 시간창을 생성하도록 수리하고 준비 점검과 기동 후 receipt 확인을 그 안에서 구분한다. 자연 경제성은 기존 family/공통 acceptance owner가 계속 소유한다.

## 8. 종결 판정과 결과 보고

- 구현 종결: 25–29번·controller/finalizer·날짜/source/미래 분류·직접 소비 결함과 지원 입력 회귀가 닫혔다. 미검증 future flag로 자연 대기를 만들지 않았다.
- 재생성 종결: 모든 활성 producer가 현 generation에서 실행/reuse/정당한 비적용으로 대사되고, 필수 stage 실패가 없다. 9/17 원 실패 이력과 복구 run은 따로 보존됐다.
- 준비 종결: 9/21 정책은 candidate 또는 유효 carry이며 모든 기동 owner의 실제 reader·환경·정책 경로가 준비됐다. 조기 PREOPEN/PID/주문은 수행하지 않았다.
- 자연 종결: 내일 정상 PREOPEN·실제 PID 소비·유효 source 유입·완료 비용 손익은 발생 후에만 보고한다. 현재 양수 후보·실제 EV 개선·인과 이익은 보장하지 않는다.
- 실행 결과에는 코드/커밋/푸시/배포, 테스트, owner별 재생성/재사용/실패, 적용일 정책, 자연 OPEN을 따로 제시한다. 지원 불가능한 과거 자료가 있어도 operational closure는 가능하지만 유효 정책·hard startup guard가 충족되지 않으면 정상기동 준비 완료는 아니다.

실행 큐는 [현재 체크리스트](../checklists/2026-09-21-stage2-todo-checklist.md)의 기존 `PostcloseLateSourceFinalHandoffAudit0920`를 통합 owner로 사용한다. 개별 family stable ID·과거 acceptance는 보존하고 중복 일정을 만들지 않는다. [현행 작업 목록](../audit-reports/2026-09-05-postclose-work-inventory.md)은 이 계획의 재판정을 반영한다.

## 9. 이번 계획 변경의 검증 증거

- 변경 범위: 이 계획, 현행 장후 목록, 기존 9/21 체크리스트 owner/시간창. 런타임 코드·정책·설치 schedule은 변경하지 않았다.
- 읽기 전용 defect 재현: 현 terminal FAIL 확인 및 날짜/exit가 잘못된 succeeded 입력의 false PASS 확인. 운영 파일을 바꾸지 않은 통제 입력 검증이다.
- 문서 자체 리뷰 후 과거 source gap=미래 미구현 단정, main 자연대기 단정, 서비스 전체 단일 release 강제, 진단 source gap의 전체 기동 차단으로 확대되는 표현을 보완했다.
- 문서 링크·공백·OPEN stable ID 검증 통과. print-only parser는 27건을 읽었으며 현재 checklist OPEN은 11건/중복0, 통합 owner와 PREOPEN owner는 각각 1건이다. 나머지는 runbook 3건과 역사 reference 13건으로 현재 장후 미완료 16건을 뜻하지 않는다.
- `git diff --check` 통과. 외부 Project/Calendar sync, 장후 재생성, 코드 전수 테스트, commit/push/deploy, PREOPEN/기동/주문은 실행하지 않았다. 구현 계획의 계약 closure와 내일 자연 acceptance는 아직 완료 상태가 아니다.


## 10. 승인된 통합 실행과 현재 구현 경계 (2026-09-20)

사용자가 이 계획의 통합 구현·검증·커밋/푸시·immutable successor 배포·A–H 전체 재생성 및 필요한 schedule/service binding 수리를 승인했다. 봇 수동 기동/재시작·주문·조기 PREOPEN 및 외부 sync/불필요 알림은 실행하지 않는다. 앞선 §1/§9의 문서 전용 상태는 계획 작성 당시 이력이다.

실행 baseline은 선택 release `main-machine-economic-reviewed-20260920-d9e2cdae3`, code `d9e2cdae3`, 리뷰 증거 `a189e7d57`로 갱신됐다. 기존 mutable workspace와 병행 변경을 보존하기 위해 별도 `fix/postclose-integrated-recovery-20260920`에서 보완한다. ME8 일부 alias 대사, ME9/ME10 전체 운영 경제성은 기존 메인 owner의 구조적 OPEN이다. 통합 인계 완료 또는 carry 발행으로 이를 자연 대기/경제성 완료로 바꾸지 않는다.

- R1/R2: source/publication/effective 선택, scoped/checklist 본문 결속, 실제 불변 attempt, run/code/clock/exit/proof terminal 검증, strict 이후 DONE, summary-only 범위 분리를 구현한다. 현재 checklist 직접 owner의 ID와 Due/Slot/TimeWindow를 검증하고 parser 출력도 run별 보존한다.
- R3: 독립 widget/machine wrapper가 exact-date·run·code·source hash terminal을 저장한다. finalizer는 그 terminal 이후 최종 summary/checklist/strict를 갱신한다. 퇴역 controller/tuning/archive를 무조건 기다리지 않는다. 최종 detector가 자기 부모를 검사하는 동안은 `pending_self_audit`이고 전체 DONE은 detector 이후다.
- R4: 역사 복구일과 publication 기반 적용일을 분리한다. widget/episode 정책은 source 날짜와 별도 발행일을 검증해 재구성하고 기존 hash/freeze/guard를 유지한다. recovery의 새 계좌·비용 조회와 알림은 비활성이다.
- R5/R6: 기존 지원 입력 producer/evaluator 회귀와 dated reader를 검증한다. 새로운 양수 후보를 강제하거나 과거 결손을 0으로 채우지 않는다. 9/18 봇 관측 미적재는 그대로 유지한다. 서비스 source/env 불일치만 승인 범위에서 정렬하며 timer 시각/주문 인자/수량/guard는 유지한다.

전체 준비 판정은 실행 후 감사 기록의 owner별 receipt와 9/21 loader 검증에 따른다. 이 절의 구현 설명 자체는 A–H 실행 완료·자연 PREOPEN/PID 소비·EV 개선의 증거가 아니다.

최종 실행 증거: [9/20 통합 복구 리뷰의 최종 결과](../audit-reports/2026-09-20-postclose-integrated-recovery-review.md#최종-복구-결과--2026-09-20-152654-kst). A–H 실행/검증 재사용과9/21 carry/fallback 준비는15:26:54 마감했다. R5의 기존 메인 운영 경제성 구조적 OPEN은 분리 보존하며 자연 PREOPEN/PID/완료 손익은 미확인이다.
