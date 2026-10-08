# Main 시간외 패턴 등록·상태 정합성 보완 구현계획 — 2026-10-08

## 1. 범위와 선행 상태

사용자 요청은 **프리·애프터 연구 실행과 별도 결함보완 계획 수립**이다. 이 문서는 후속 구현계획이며 등록·정책 발행·배포·재기동을 실행한 영수증이 아니다. 운영 AI 한도/장후 비교 100회, 주문·자본·custody·manual veto·원천 freshness 보호는 그대로 적용한다.

10/8 추가 리뷰에서는 **P0 경로 결함의 최소 복구 단위**와 **신규 후보 등록 단위**를 분리했다. P0 완료를 13개 후보 구현·보조 실호출·성과 비교 완료까지 미루지 않는다. 이번 요청으로 수행하는 변경은 이 계획의 보완이며, 기존 세션의 승인 범위는 해당 작업 인계에서 보존한다.

연구는 [시간외 실행계획](main-pre-after-additional-pattern-research-plan-2026-10-08.md)과 [결과 검토](../audits/main-pre-after-additional-pattern-research-review-2026-10-08.md)가 소유한다. 구현 착수 시 [현재 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry`를 이어가며 중복 owner를 만들지 않는다. 날짜가 바뀌면 같은 ID의 acceptance/이력을 당일 문서에 인계한다.

07:48 점검 기준 활성 bundle은 `cdacf6eed9d77e95d0bdf1a417ec2549323ea2491b91e41b8f948b900434895f`, release는 `operating-union-20261008-v13` / `e6ec7950c663fa1d4a1d431510274e48dc4b7da3`다. 48셀/128route 전부 `union_v5`로 정책 계약에 들어 있고, 추가 8개는 SOR REGULAR 14개 범위에만 등록됐다. 이 수치는 historical as-of이며 착수 시 current/선택 release/소비 PID를 재확인한다.

**사용자 후속 정정: 실제 운용은 PRE=NXT `_NX`, REGULAR·통합 AFTER=SOR `_AL`이다.** 128개 계약 셀을 모두 실운용 경로로 표현한 초기 범위 설정을 정정한다. 이번 연구·신규 등록은 PRE NXT 16셀과 AFTER SOR 16셀을 대상으로 한다. PRE SOR·AFTER NXT/KRX는 신규 등록 대상으로 확장하지 않는다. 기존 호환 셀/과거 증거는 삭제하지 않는다.

## 2. 확인된 보완 지점

| ID | 현재 근거와 문제 | 수정 소유자 | 종료 검사 |
|---|---|---|---|
| PA0 / P0 | 10/8 실제 PID cwd가 release/src인데 v5 source validator가 `Path(record['path'])`로 `data/...` 7개 원천을 해석하여 active_machine_policy_invalid 유발 | 원천 경로 resolver·source receipt producer·실제 loader preflight | 같은 bundle/source가 workspace·release root·release/src·무관 cwd에서 동일 검증, 훼손/누락은 동일 차단 |
| PA1 | `reversal_path_catalog.applicable()`은 새 8개를 REGULAR/SOR로 제한 | 버전별 catalog/명시 등록 batch | PRE NXT/AFTER SOR에만 승인 후보 ADD, 비운용 route 신규 등록 0 |
| PA2 | `matches()`의 신규 경로는 `symbol+'_AL'`을 요구하여 PRE NXT 신규 후보와 충돌 | catalog source contract | PRE는 `_NX`, REGULAR/통합 AFTER는 `_AL` 원 출처 일치. AFTER에 별도 NXT/KRX detector 신설하지 않음 |
| PA3 | `reversal_path_runtime.State.observe()`의 유지 1초, 재시험 120초·0.2%, phase 목록이 기존 8개에 맞춰짐 | 공통 causal root detector | 이번 13개에 필요한 고점 회복·30/120초·0/0.2%·구조 필터를 정확 재생하고 기존 hold/breakout 보존 |
| PA4 | v5 `validate_family()`가 현재 전역 `C.SHA256`/정의를 요구. 기존 catalog 직접 수정 시 과거/현재 bundle 검증이 깨질 수 있음 | family/schema dispatch 및 version registry | 기존 v4/v5 및 새 catalog가 자기 생성 당시 버전으로 통과, 위조는 거부 |
| PA5 | v5 `detector_manifest(...changes=...)`는 존재하지만 operating `machine_report()`는 changes 없이 호출 | 승인 batch 소비·장후 인계 | 승인 ADD의 정확 부모/범위가 manifest에 반영되고 재실행 중복 0 |
| PA6 | `machine_report()`의 `membership_status=pending_exact_union_auxiliary_pair`가 발행 결과에 복사됨 | operating report finalizer | 128개 등록 완료와 비교 미완료가 독립 표시, 오래된 pending을 현재 등록 실패로 오독하지 않음 |
| PA7 | checklist의 future handoff는 summary 생성 당시 snapshot. 현재 준비·활성화와 과거 pending이 혼재할 수 있음 | summary/checklist 표시 소비자 | source/target/generation/as-of를 표시하며 과거 snapshot과 현재 검증 결과를 별도 읽음 |
| PA8 | semantic monitor가 `cumulative_winrate_selected`를 고정 반환. 지정 초기 등록을 성과 비교 우승으로 오인 가능 | artifact_freshness 의미 투영 | operator initial / comparison selected / verified carried / incomplete / source gap 구분 |
| PA9 | release selection의 과거 hold 문구는 현재 hold 파일/해제 영수증과 달라질 수 있음 | runtime release 상태 투영 | 승인 hold 상태와 PID 소비 상태를 별도 표시, 해제만으로 PID PASS 처리 금지 |
| PA10 | 계약상 128 route 셀 수와 실제 운용 세션·경로가 혼동됨 | policy inventory/상태 투영 | `contract_scope`와 `operating_route`를 구분, PRE NXT·REGULAR/AFTER SOR 기준으로 표시 |
| PA11 | `reversal_operating_evaluation.coverage()`가 요구하는 `dd`/`volume`이 `State.features()` 결과에 없고 observe 내부 지역 사본에만 보강됨. 정상 legacy 조건 불일치도 UNKNOWN으로 집계될 수 있음 | 정확 phase 특징/기여도 coverage 소비 | 같은 원천에서 detector의 TRUE/FALSE/UNKNOWN과 보고서 coverage 일치, 실제 결손 UNKNOWN 보존 |
| PA12 | `reversal_path_auxiliary`의 허용 phase에 고점 회복 PEAK가 없고, 재시험 증명 검증도 120초·0.2%로 고정됨 | typed 보조 입력·증명·응답 계약 | 13개 후보의 root/필터/증명과 실제 공통 AI 요청을 동일 정의로 검증 |
| PA13 | v5는 next_session 전용이고 V4 `transition_parent()`는 v5 코드 변경 예외를 인계하지 않음 | 원 생성 코드 검증·동일 정책 코드 복구 발행 | 현재 대상일의 명시 code-only 복구와 다음 세션 신규 정책 발행을 분리, 날짜 위조/정책 재선정 0 |
| PA14 | 등록 상태·채택 이유, 전체 manifest 로드·실제 route 판정이 기존 계획의 상태 enum에서 혼재 | 상태 projection·정확 PID/판정 영수증 | 등록/채택 근거/검증 단계/실제 관측 scope를 독립 표시 |

PA0/PA13은 기동 후 정책 검증 오류의 복구 경로, PA1은 시간외 등록 범위 확장 요청이다. PA1은 현재 시간외 정책이 비어 있다는 뜻이 아니다. PA2/PA3/PA4/PA5/PA12는 새 후보를 실제 소비하기 위한 구현 결손, PA6~PA10/PA14는 상태 계약 정합성 보완, PA11은 기여도 계산 결함이다. historical 표시를 지우거나 과거 증거를 현재 값으로 덮는 방식으로 해결하지 않는다.

PA11 재현: 9/22 삼성 SOR AFTER 17:27:18.198의 연속 원천·유효 호가에서 prior high와 확인가격이 존재하지만 `features()`에 dd가 없어 coverage가 UNKNOWN이다. [격리 재현 영수증](../../tmp/main-pre-after-pattern-research-20261008/coverage-defect-reproduction.json)을 근거로 삼는다. 현재 관측가격을 과거 결손에 채울 문제가 아니며 당시 정상 source로 정확 특징을 소비해야 한다. legacy FIRST는 저점 기준 DD, 경로 후보는 확인가격 기준 DD를 사용할 수 있으므로 공통 이름 하나에 임의 대입하지 않는다.

## 2.1 P0 — 실제 기계판정 차단의 경로 계약 보완

### 확인 근거와 영향

사용자가 전달한 10/8 08:10 장중 집계는 신규 탐색 79개 중 정책 차단 62·원천 부족 16이며 삼성/두산은 `active_machine_policy_invalid`로 WAIT라는 내용이다. 이 집계 전체를 이번 연구에서 다시 계산했다고 주장하지 않는다. 다음 원인은 직접 재확인했다.

- PID `1304291` cwd: `/home/ubuntu/KORStockScan-runtime-releases/operating-union-20261008-v13/src`.
- 같은 활성 bundle의 frozen machine report `source_receipts`에 상대경로 `data/report/continuous_reversal/2026-10-07/normalized/...` **7개**가 있다.
- `/home/ubuntu/KORStockScan/data/...`에서 **7/7 파일 존재 및 기록 SHA 일치**, PID cwd에서 해석한 `release/src/data/...`는 **7/7 존재하지 않음**.
- [정확 경로·해시 대조 영수증](../../tmp/main-pre-after-pattern-research-20261008/relative-source-path-defect.json).
- `continuous_reversal_policy_v5.validate_sources()`는 frozen receipt와 actual response evidence에서 cwd 상대 `Path(record['path'])`를 사용한다. 부팅의 root cwd 검증 PASS와 실제 src cwd의 정책 로드 결과가 갈릴 수 있다. release PID attestation과 개별 기계판정 성공도 별도다.

이는 새 패턴 성과 부족이나 자동으로 완화할 매매 조건이 아니다. 같은 원천을 읽는 위치 계약을 바로잡는 P0이며, **추가 패턴 등록 전에** 닫는다. HPSP/알테오젠/주성의 NXT 적격성 대기는 별도 조건으로 유지하며 이 오류 수정으로 적격성을 꾸며내지 않는다.

### 구현 순서

1. **현재 증거 동결:** 선택 release·PID cwd·기동 argv의 안전한 식별자·bundle/source/report hash·최초 예외의 recorded/resolved path를 보존한다. 실제 API/provider/주문을 호출하지 않는 최소 source resolver 재현을 남긴다.
2. **단일 기준점으로 해석:** consumer에 검증된 `data_root`/명시 source anchor를 전달한다. 이번 legacy `data/...`는 정확한 `data/` 접두를 해제해 전달된 shared data root에 결합한다. 이미 절대경로인 historical receipt는 원 경로와 해시로 검증한다. process cwd, `os.chdir`, 임의 파일검색, 이름만 같은 파일 찾기를 사용하지 않는다.
3. **경로 무결성:** 상대 `..` 탈출·미지원 접두·모호한 root는 명시 오류로 남긴다. 선택 release의 허용된 shared mount/symlink를 실제 경로로 확인하고 외부 임의 경로로의 우회를 막는다. cache/dependency signature key도 같은 canonical source identity를 사용한다. source를 못 찾았을 때 검증을 생략하거나 현재 파일로 해시를 교체하지 않는다.
4. **생산자 정상화:** normalized source manifest와 source/results/actual-response receipt writer를 조사해 새 발행물은 명시 root+상대경로 계약 또는 절대경로로 일관되게 기록한다. source hash는 파일 내용에 결속하고 경로 표준화가 보고서 hash를 바꾸면 정식 새 세대로 발행한다. **기존 봉인 report의 path만 in-place 수정하지 않는다.**
5. **전체 소비 경로:** v3/v4/v5 부모 검증, `mechanistic_entry_runtime_policy` load/cache/dependency 서명, report/evidence 검증, historical origin subprocess가 같은 기준점으로 읽는지 점검한다. 비운용 route를 포함한 frozen 영수증을 삭제해 검증을 통과시키지 않는다. source resolver는 적절한 기존 owner에 두고 중복 wrapper를 만들지 않는다.
6. **코드 증빙 호환:** v5 validator 자체가 contract hash에 들어 있으므로 수정 코드를 기존 bundle의 생성 코드로 사칭하지 않는다. 기존 origin 검증·후속 bundle/릴리스 인계 방식을 확정하고, 필요 시 같은 정책 payload의 successor 발행/인계만 수행한다. 이 보완이 임계값·정책 내용 교체를 요구하지 않음을 대조한다.
7. **실제 기동 조건 preflight:** launch cwd=`release/src`와 production imports/data root를 사용해 write/provider/order 없는 실제 loader 검증을 실행한다. bootstrap만 통과하면 종료하지 않는다. 시작 전 검사와 자연 장중 validator가 서로 다른 resolver/cache를 사용하지 않도록 한다.

### 경로 해석·캐시의 구체 계약

- 입력은 `recorded_path`, 신뢰된 `data_root`, 기록 SHA와 원 보고서 identity다. 새 receipt는 `path_kind=data_root_relative`와 `relative_path`의 버전 계약을 우선 사용하고, legacy `data/...` 및 기존 절대경로는 호환 reader에서만 해석한다. root는 receipt의 임의 문자열이나 cwd에서 추정하지 않는다. 실제 저장 schema를 변경하면 원천 writer/reader를 같은 버전으로 인계한다.
- `data/...`는 anchor 내부, legacy 절대경로는 원래 검증된 source/release 범위에서 읽는다. 정상적인 shared data symlink를 일괄 거부하지 않는다. 동일 basename 탐색, 잘못된 root에서 다른 root로 fallback, `src/data` 임시 링크와 process-wide `chdir`는 해결책으로 사용하지 않는다.
- `mechanistic_entry_runtime_policy._read`, `_signature`, `_source_hash`, `_READ_DEPENDENCIES`, `_CURRENT_CACHE`에 전달하는 경로 identity를 대조한다. 상대 문자열과 실제 파일 경로가 서로 다른 dependency로 남지 않아야 한다. 파일 read 전후 stat 검사를 유지하고, lexical symlink 대상 교체도 감지한다. 처음 resolve한 대상만 cache에 남겨 새 mount를 계속 무시하지 않는다.
- 원 생성 코드 subprocess는 과거 증거 검증 전용이다. subprocess PASS가 현재 runtime cache의 dependency 추적을 대신하지 않는다. 현재 loader는 current pointer·parent·report·원천·선택 코드/anchor의 변경을 재검증하며 historical 결과를 그대로 live cache에 넣지 않는다.
- 파일 전수 hash는 cache miss/서명 변경 시 수행하고 cache hit는 현재 dependency 서명 검사로 닫는다. 모든 tick에서 원천 전량을 다시 읽는 수정은 피한다. 고정 fixture에서 첫 load·반복 hit·원천 교체 후 miss의 read/hash 횟수를 측정한다.

### PA13 — 당일 코드 복구와 다음 세션 정책 발행

현재 [v5 publisher/validator](../../src/engine/scalping/continuous_reversal_policy_v5.py)는 `effective_mode=next_session`, `publication_date < effective_date`, `target_date=next_target(publication)`를 요구한다. [V4 인계](../../src/engine/scalping/continuous_reversal_policy_v4.py)의 `stage_code_refresh()`는 v5 복구 API가 아니며, `transition_parent()`도 `v3/v4_contract_code_changed`만 처리한다. 따라서 **기존 함수로 같은 날 refresh하면 된다는 전제를 두지 않는다.**

1. 구현 착수 시 이미 다른 세션에서 해결된 경로가 있는지 먼저 확인한다. 남아 있으면 원본 v5/v4 bundle을 각자 생성 commit·immutable origin에서 검증하고, 실패 원인이 경로 계약인지 코드 변경인지 구분한다. 모든 `ValueError`/파일 결손을 historical fallback으로 삼지 않는다. origin 검증 환경의 명시 anchor는 고정하되 운영 process cwd를 변경하지 않는다.
2. **새로운 기계·보조 정책 내용 없이 당일 복구가 필요한 경우**에 한해 versioned `code_only_repair` successor와 해당 loader/activation 인계를 설계한다. 기존 next-session schema에 intraday 예외를 조용히 추가하지 않는다. 원 source/publication/effective 날짜는 origin 항목으로 보존하고, 실제 `repair_created_at`, `repair_effective_from`, target KST 날짜·부모 bundle·검토 코드 SHA를 별도 결속한다. 새 report의 발행일을 어제로 위조하지 않는다.
3. 복구 전후 **모든 128 계약 route**의 branch 집합·정의/root/필터·기계 payload·보조 arm/input/prompt/schema/model/validator의 의미·실행 backend·label·운용 route를 비교한다. 파생 코드/실행 hash와 경로 receipt 변경만 허용한다. 보조/등록 변경이 섞이면 code-only로 발행하지 않고 해당 승인 변경 단위로 분리한다. 새 연구 13개는 이 단계에 넣지 않는다.
4. `validate/validate_sources/load_effective/current` schema dispatch, configure/claim, `continuous_reversal_policy.compose`, activation·PID 소비, bootstrap·handoff·semantic 상태 소비자를 한 버전으로 검증한다. 새 스키마를 인식 못한 소비자가 legacy 분기로 조용히 빠지지 않도록 한다. 기존 v4/v5 동작·origin 증빙은 그대로 남긴다.
5. 실제 발행·cutover는 당시 유효한 사용자 승인 범위에서만 수행한다. publisher lock 아래 부모 current CAS를 검사하고 successor 읽기 검증 후 교체한다. 중도 실패 시 current pointer·선택 release·PREOPEN/기동 receipt의 조합을 정상으로 표시하지 않는다. `contract_code_changed`, 같은 날 target 거부, 부모 동시 교체가 후속 오류로 재발하지 않는지 종료 검사에 포함한다.
6. 새 branch 등록과 새로운 정책 비교는 다음 세션 발행 경로로 진행한다. 당일 기술 복구의 날짜 예외를 신규 alpha를 즉시 적용하는 범용 경로로 사용하지 않는다.

### cutover·되돌림 경계

코드 hash는 scope 실행 hash에도 포함되므로 정책 내용이 같아도 기존 state/claim이 무효화될 수 있다. 교체 시 in-flight claim과 provider/intent/outbox를 원 generation에 남기고 결과를 대사한다. 준비된 과거 확인점을 새 실시간 신호로 재방출하거나 불확실 provider 요청을 다시 호출하지 않는다. `opportunity_key`는 정책 세대와 독립적인 기존 namespace·원천 stream identity를 유지하고 새 요청 hash와 구분한다.

실패 시 직전 release와 정책 쌍을 **실제 launch cwd에서 검증한 경우에만** 복귀 대상으로 사용한다. 경로 오류가 있던 v13으로 돌아갔다는 이유만으로 복구 완료로 표시하지 않는다. 정상 복귀 쌍이 없으면 기존 정책 오류 차단과 보유/취소/SELL 소유권을 보존하고 정확 실패 원인을 남긴다. 새로운 자동 매매 중지·재시작 규칙을 이 문서에서 추가하지 않는다.

### 회귀·종료 기준

- 동일 frozen bundle을 workspace root, release root, release/src, 독립 cwd에서 읽어 결과가 같아야 한다. 이 중 실제 봇 cwd를 필수 fixture로 둔다.
- 절대/legacy `data/...`/허용 shared symlink, 존재하지만 SHA 불일치, 누락, path traversal, 잘못된 mount, 이전 report 세대, parent origin 검증, 캐시 생성 후 cwd 변경을 테스트한다.
- cache hit 후 source 교체·symlink 대상 교체·current CAS 충돌·origin 코드 변조·같은 날 repair를 검사한다. 올바른 파일을 검증한 뒤 다른 파일을 읽는 경쟁도 실패로 남겨야 한다.
- **유효 입력의 `active_machine_policy_invalid`가 경로 오류 때문에 발생하지 않아야 한다.** 실제 기계판정이 ENTER_NOW일 필요는 없다. 정상 조건 불일치/원천 결손은 본래 판정으로 남는다.
- 코드 gate 후, 별도 후속 실행 범위가 승인되면 reviewed release·필요 인계·기동을 수행한다. 자연 판정에서 bundle/source/exception 원인을 확인하고 정책 검증 오류 제거를 보고한다. 주문 제출이나 수익을 기술 결함 종료 조건으로 강제하지 않는다.
- 신규 패턴 연구/등록 결과는 P0와 분리하여 보존한다. P0를 해결하기 위해 provider 한도·NXT 적격성·원천 freshness·주문/자본/custody 보호를 변경하지 않는다.

## 3. 단계 R0 — 기준과 등록 인계물 고정

1. 최신 부모 bundle, operating manifest, registry/정의/code hash, 실제 release와 schema dispatch를 재동결한다. 이 문서의 bundle을 후속 구현 시 무조건 부모로 사용하지 않는다.
   - 이번 연구 도중 다른 세션에서 `reversal_auxiliary_registry`, `reversal_auxiliary_tuning`, `reversal_auxiliary_intraday`와 operating producer dispatch를 변경 중임을 확인했다. 해당 작업본은 수정하지 않았다. 구현 착수 시 완료 commit/배포 여부와 정확 보조 version·프로필·장후 campaign/장중 소비 계약을 다시 확인하여 실제 최신 소비자에 연결한다. 현재 작업본 존재를 배포 완료로 간주하거나 기존 보조 경로를 별도로 복제하지 않는다.
2. 연구 추천 후보는 `proposed_not_installed` batch로 유지한다. 후보마다 고정 ID·정의 SHA·root 계약·특징 시점·포함/제외 경계·정확 scope/item·원천/결과 hash·단독/기존+후보 W/F/U·날짜/목표 시각 집중도를 저장한다.
3. 누적 기계 승률 순위와 보조 AI 실제 비교, 실제 체결/손익은 별도다. 같은 데이터 탐색 결과를 독립 검증으로 표시하지 않는다. 최소 일수/표본/holdout/EV·기존 성공 100%/80% 보존 gate를 추가하지 않는다.
4. 빈 결과는 `no_source`, `source_unusable`, `valid_no_signal`, `all_outcomes_unresolved`, `no_improvement`, `candidate_found`로 실제 근거에 따라 구분한다. 무자료 범위에 타 경로·정규장 후보를 복제하지 않는다.

### 등록 인계물과 정확 구현 범위

[제안 batch](../../tmp/main-pre-after-pattern-research-20261008/proposed-registration-batch.json)는 연구 schema이며 v5 `changes` 객체가 아니다. `baseline_bundle`을 최신 부모 CAS로 바꾸거나 `operator_receipt`를 임의 생성해 직접 넘기지 않는다. 원 연구 batch/hash는 보존하고 실제 승인 시 `research_batch_sha256`, `parent_bundle_sha256`, 승인 receipt, ADD scope, definition hash를 가진 별도 적용 객체로 변환한다. 최신 부모에서 기존 정의와 동일한 항목은 idempotent no-op, 같은 ID/다른 정의는 충돌이다. 기존 사용자 승인으로 해당 batch가 이미 지정됐다면 다시 승인받지 않고 그 receipt를 인계한다.

| 구현할 root | 이번 13개 후보 수 | 정확 지원 계약 |
|---|---:|---|
| FIRST | 5 | native 첫 반전, 확인 시점 특징. legacy 저점 DD와 신규 확인가격 DD 구분 |
| PEAK | 2 | 첫 반전 후 원 고점 회복, 120초·원 저점 아래 0.2% 허용. 저점 재접촉은 필수 아님 |
| MOMENTUM | 3 | 60초 수익률 +0.05% 또는 +0.2%의 known FALSE→TRUE 전환 |
| RETEST_PEAK | 1 | 저점 재접촉 뒤 원 고점 회복, 120초·0.2% |
| RETEST_FIRST | 2 | 저점 재접촉 뒤 원 첫 반전 가격 회복, 30초·0% 또는 0.2% |

`RISING`/`MIXED`는 이번 batch에서 구조 **필터**다. 연구한 44개 root 전체나 FIRST_HOLD 3/5초·독립 RISING_STRUCTURE root를 이번 등록의 필수 구현으로 확대하지 않는다. 기존 8개에 사용되는 hold/high-breakout 등은 기존 계약 보존·회귀검사 대상이다. 이후 승인 batch가 필요로 할 때 별도 지원한다.

추천 13개 중 9개는 기준 확정 결과가 있고 4개는 `baseline_unresolved`다. 현재 공통 관측 mask로 기여도까지 확인된 두산 PRE·일반 저가 AFTER와 PA11 재집계가 필요한 나머지를 구분한다. 미확정/단일 날짜 집중은 보고 정보이며 새 최소표본·성공보존 gate로 바꾸지 않는다. 최초 선정의 기준 bundle과 등록 당시 최신 bundle이 달라지면 동일 원천·고정 후보로 차이를 재계산하고, 원 수치를 최신 기준의 개선이라고 재사용하지 않는다.

연구 인계물이 `tmp/`에만 있으므로 등록 전에 batch/정의·manifest·결과·검증 영수증과 필요한 원천 참조를 기존 postclose 보존 owner 아래 내용 hash로 고정하고 참조를 인계한다. 이 문서 리뷰에서는 이동/정리를 실행하지 않는다. 실행에 필요한 파일이 사라지면 현재 원천으로 대체하거나 숫자만 문서에서 복원하지 않는다.

## 4. 단계 R1 — 버전과 탐지 계약 보완

- 기존 8개의 ID/정의/원천 계약을 변경하지 않는다. 새 registry 버전과 신규 정의를 추가하고 family loader가 기록된 registry 버전으로 검증하도록 한다. 기존 v5→새 schema 또는 동등한 version dispatch 중 하나를 구현 설계에서 확정한다. 기존 `C.SHA256`만 교체하고 nested parent를 현재 catalog로 재검증하는 방식은 금지한다.
  - 현재 v5는 `validate_family()`를 historical origin 분기보다 먼저 호출하며, nested v4도 현재 catalog를 참조한다. 과거 registry/phase/auxiliary 계약을 원 버전으로 고정하는 dispatcher를 먼저 만든다. origin subprocess만 추가한 뒤 바깥 family 검증이 새 catalog로 옛 정책을 거부하는 상태를 남기지 않는다. freeze한 v4/v5 bundle을 새 registry 추가 전후 동일하게 읽는 fixture가 필수다.
- 새 source 파일은 `src/engine/scalping/`이 소유한다. engine root에 신규 모듈/중복 compatibility 구현을 만들지 않는다. 관련 테스트는 `src/tests/`의 기존 reversal/operating 테스트 근처에 둔다.
- 이번 batch의 FIRST·PEAK·MOMENTUM·RETEST_FIRST/PEAK를 수동 등록된 계약으로 정확 dispatch한다. 미지원 root/필드는 등록 validation error이며 silently FIRST/기본 임계값으로 대체하지 않는다.
- 모든 운용 branch는 같은 유효 tick을 독립적으로 소비한다. 한 branch의 false/UNKNOWN/새 anchor가 다른 branch의 pending/root를 취소하지 않는다. 미래 접두·결과 라벨은 특징 계산에 넣지 않는다.
- root별 `known_false_to_known_true`, warmup, 저점 strict breach/inclusive touch, 만료시간, 실제 확인 ask, 동일 가격대 전환을 정확히 구현한다. FIRST의 과거 low 기준 DD와 새 연구의 확인가격 기준 DD는 필드 계약으로 구분한다. 첫 TRUE 관측·UNKNOWN→TRUE·재연결은 FALSE→TRUE 증거가 아니다. 등록 후 warmup으로 과거 신호를 emit하지 않는다.
- root 상태는 동일 계약/경로/종목에서 공유 가능하되 정책별 필터·pending 소유권을 보존한다. 등록 수에 비례해 동일 rolling window/원천 조회를 반복하지 않는다. 큐 한도 초과는 지연/누락 영수증으로 남기며 조용히 신호를 버리지 않는다.
- item 판정은 PRE NXT `_NX`와 REGULAR/통합 AFTER SOR `_AL`의 기존 native source 계약을 재사용한다. 신규 AFTER 탐지는 기존 `_AL` 경로에서 수행한다. source spelling만 바꾸어 동일 시장으로 간주하거나 `_AL` 관측을 `_NX` 성과로 복사하지 않는다. API 요청/FID/recovery 변경까지 필요하면 구현 시 공식 Kiwoom reference gate를 먼저 수행한다.

### PA11 — 탐지 상태를 소비하는 기여도 판정

`coverage()`에서 현재 row만으로 root의 과거 state를 새로 추론하지 않는다. detector가 같은 row를 처리한 시점의 root 가능 여부·필수 특징·실제 조건 결과와 이유를 불변 snapshot으로 넘기고 TRUE/FALSE/UNKNOWN을 계산한다. 현재의 `hits=TRUE`는 유지하고, root 없음이 입증된 FALSE, 필수 특징 미상 UNKNOWN, 조건의 알려진 FALSE를 구분한다. phase와 definition에 따른 평가 순서를 맞춰 모든 필드 하나라도 null이면 무조건 UNKNOWN이 되는 규칙도 점검한다.

변경 후 기존 branch의 확인점/기계 결과/ask는 같고 coverage만 정정돼야 한다. 불일치가 나오면 공통 feature 변경으로 실시간 판정까지 바뀐 원인을 먼저 분리한다. detector·coverage·snapshot serializer가 같은 값을 쓰는 검사를 FIRST/PEAK/RETEST/MOMENTUM, warmup·무반전·단절·누락별로 수행한다. 독점 기여 UNKNOWN은 결과 UNRESOLVED와 다른 축으로 남긴다.

### PA12 — 보조 입력까지 완결된 root 계약

[기존 typed 보조 계약](../../src/engine/scalping/reversal_path_auxiliary.py)의 `PHASES`, `validate_signal`, `PROOF_FIELDS`, `production_request`, `binding`, `validate_response`와 [공통 요청 조립](../../src/engine/scalping/reversal_operating_auxiliary.py)을 함께 보완한다. PEAK를 `RETEST_RECLAIM_PEAK`로 바꾸어 없는 touch를 만들어서는 안 된다. root proof와 확인 epoch/sequence, 정의에 기록된 30/120초·0/0.2%·전환 임계값을 정확 검증한다. 유효한 proof를 허용하는 검사 외에 **정의와 다른 proof를 거부하는 검사**를 둔다.

동일 확인점의 모든 branch는 같은 ask/clock/item/route와 하나의 요청을 사용하되, 각 신호의 실제 phase와 특징 시점을 보존한다. 최초 반전·최초 조건 전환의 과거 특징을 확인 시점 특징으로 혼용하지 않는다. 새 root/parameter가 직렬화에서 빠져 AI가 다른 유형으로 해석하지 않도록 입력 bytes parity를 검증한다. prompt/schema/version은 내부 English ASCII 계약을 따른다. 실제 모델 호출 없이 fixture 요청·응답 validator로 구현을 검증하고, 실제 장후 비교는 별도 승인/기존 100회 계약에서 처리한다.

## 5. 단계 R2 — 명시 ADD와 평가·실시간 연결

1. 승인된 registration batch를 정확 부모 bundle에 대한 ADD/REPLACE/RETIRE로 소비한다. 단순 catalog 존재는 운영 활성화를 뜻하지 않는다. v5의 `wanted()`가 기존 manifest를 복사하는 경로와 실제 report producer에 batch를 연결한다.
2. 비교는 현재 적용 목록, 동일 목록의 새 엔진 재생, 신규 단독, 기존+각 신규, 연구에서 고정한 합집합이다. 장후에 threshold grid/powerset/새 패턴 생성은 하지 않는다. 진단 순위가 등록 목록을 자동 삭제하지 않도록 한다.
3. 후보 단독·합집합 확인점의 탐지 TRUE/FALSE/UNKNOWN과 결과 W/F/U를 분리한다. 기준 정책 UNKNOWN인 곳을 `exclusive_win`으로 승격하지 않고 `exclusive_unproven`으로 남긴다. 현재 연구의 단순 미포함 추가점은 이 최종 기여도 검사 전 증거다.
   - PA11을 먼저 보완하여 실제 확인 phase의 native event/rolling snapshot을 coverage에 전달한다. first root 부재가 입증되면 FALSE, first root가 있고 필수 특징이 빠지면 UNKNOWN이다. 지역 사본/캐시 alias 누락과 실제 가격 단절을 다른 원인으로 기록한다. 이전 coverage를 새 세대에서 재산출하고 미수정/수정 집계를 함께 보존한다.
4. 같은 종목·날짜·세션·route·item·native epoch/sequence 확인점에 매칭한 모든 branch를 하나의 공통 보조 입력과 한 intent에 결속한다. 영속 dedup/outbox를 재사용하여 restart/timeout/모호한 전송 재시도에서도 중복 provider/주문이 생기지 않게 한다.
   - `reversal_operating_auxiliary.opportunity()`의 native stream namespace는 재배포·registry 변경·provider 요청 변경 때문에 바꾸지 않는다. 같은 원천의 다른 파일/세대 alias는 하나로 대사한다. 위조·모순 identity는 격리하고, 기존 unresolved outbox/intent를 새 key로 우회하지 않는다. 한 branch의 무효화 후 남은 branch만 재검증하며 새 branch를 이미 전송한 요청에 사후 추가하지 않는다.
5. 보조 AI는 실제 확인 접두의 입력/prompt/schema/model/validator/공통 branch 집합이 정확히 같을 때만 원 응답을 재사용한다. 기계 WIN을 PASS로 만들거나 branch별 응답을 합쳐 공통 응답으로 꾸미지 않는다.
6. 장후 신규 provider 호출은 source-day 누적 100회 계약과 불확실 예약을 보존한다. 새 batch/세대로 한도를 리셋하지 않는다. 호출 부족은 비교 incomplete로 유지하고 기계 연구 결과 자체를 삭제하지 않는다.
7. **사용자 지정 채택과 자동 비교 선택을 구분한다.** 이후 사용자가 특정 batch 초기 운용을 지정하면 그 지시와 정확 계약으로 채택하며, 비교 완료/경제성 입증을 추가 gate로 만들지 않는다. 이번 연구·계획 요청 자체는 초기 채택 지시가 아니다. 자동 교체는 기존 승인된 장후 비교 계약을 따른다.

장후 재계산은 이번 고정 후보와 해당 날짜에 실제 적용한 정책 목록만 소비한다. 기계 rank는 동일 label·원천 cutoff·scope의 누적 `WIN/(WIN+FAIL_STOP+FAIL_TIMEOUT)`와 U를 사용하고, 단순 union·공통 관측 union·기존 excluded 수·독점/중복/leave-one-out을 함께 보존한다. 0/0은 0%가 아니다. 확인점 수와 중복 제거 목표 시각 수, 실제 주문/체결 수를 같은 단위로 합치지 않는다. 다른 세션의 보조 arm 탐색/저장 최적화는 별도 owner이며 여기서 새 보조 모델/threshold 탐색을 추가하지 않는다.

확인 시점 이후 가격은 outcome에만 사용한다. 동일 item의 이후 보유 완성 분봉, 명시 cutoff, 30분 horizon과 장벽 동시 도달의 native 보수적 처리로 기존 라벨을 재현한다. PRE에서 발생한 신호가 이후 세션의 같은 `_NX` 가격으로 평가되더라도 확인 scope는 PRE로 유지하며 `_AL`로 대체하지 않는다. 10분 미도달을 실패/0으로 조기 확정하거나 시장 종료 후 다음 날 가격까지 horizon을 늘리지 않는다.

## 6. 단계 R3 — 상태 원천과 표시 정합성

### 6.1 표시할 독립 필드

`research_state`, `registration_state`, `adoption_basis`, `comparison_state`, `publication_state`, `activation_state`, `prepared_state`, `policy_validation_state`, `pid_consumption_state`, `startup_hold_state`를 분리한다. 각 값에는 source_date/target_date, generation 또는 bundle/manifest SHA, producer/receipt path, observed_at을 둔다. 단일 `selected`/`pending`으로 여러 단계를 압축하지 않는다. 새 필드는 기존 owner의 보고서/읽기 projection에 추가하며 독립 주기 작업이나 새 자동 복구 owner를 만들지 않는다.

- 등록: `not_registered` / `registered` / `retired`. 활성화는 별도 필드다. 채택 근거: `operator_designated` / `comparison_selected` / `carried` / `not_applicable`.
- 비교: `complete` / `incomplete` / `completed_no_pass` / `completed_unresolved` / `valid_empty` / `source_gap`.
- PID: `not_started` / `not_observed` / `consumed_exact` / `mismatch`. 준비 PASS에서 PID 상태를 추정하지 않는다.
- 정책 검증: `valid` / `invalid` / `not_observed`와 `validation_stage=bootstrap|launch_loader|intraday_decision`를 결속한다. bootstrap PASS와 intraday invalid를 함께 표시할 수 있어야 한다. 오류 원인·recorded/resolved path·당시 generation을 보존하되 자격증명은 출력하지 않는다.
- hold: 현재 승인 hold 파일·해제 영수증을 기준으로 확인한다. 과거 selection의 문구는 as-of 이력으로 표시한다.
- scope: `contract_scope_count`, `operating_scope_count`, `loaded_scope_count`, `observed_decision_scope_count`를 따로 기록한다. v5 PID receipt의 128개 `union_v5` 수는 로드한 구성 수이며, 모든 시장에서 판정이 발생했다는 증거가 아니다. 실제 PRE NXT/REGULAR SOR/AFTER SOR route별 마지막 판정과 eligible/source/decision 상태는 별도다.

### 6.2 생산자→소비자

`continuous_reversal_operating_postclose` 발행 시 실제 machine/auxiliary scope 결과로 membership 상태를 산출한다. `direct_handoff`는 같은 발행 세대의 상태를 소비한다. `artifact_freshness._continuous_reversal_result_semantics`는 adoption basis와 comparison 상태를 함께 투영한다. 등록 완료를 `cumulative_winrate_selected`로 일괄 표현하지 않는다.

`postclose_summary_handoff.direct_future_handoff` / `build_next_stage2_checklist`의 과거 marker는 생성 당시 값이라는 표시를 갖는다. 현재 활성화/준비/PID 표시는 정확 날짜·generation의 append-only receipt를 조회해 별도 제공한다. 불변 marker를 UI 최신 상태로 계속 덮어 PREOPEN seal을 깨는 설계를 피한다.

시점·세대가 다른 receipt를 합쳐 PASS로 만들지 않는다. 현재값이 없으면 `not_observed`와 마지막 관측 시각을 표시한다. legacy 필드가 필요하면 일관된 파생값으로만 만들고 신규 소비자가 그 값 하나로 실행 권한을 결정하지 않게 한다.

PID는 숫자 하나 대신 기존 attested identity의 시작 시각·실행 경로·release commit·bundle을 결속한다. projection read 전후 current/selector/PID identity가 바뀌면 `changed_during_read`로 반환하고 섞인 결과를 현재값으로 캐시하지 않는다. 재검사는 기존 모니터 주기에서 수행한다. 과거 오류가 남은 receipt와 새 PID의 정상 판정을 구분하며 시간만 새로 찍어 freshness를 갱신하지 않는다.

### 6.3 봉인 순서

이번 연구에서는 historical report/checklist/selection을 수정하지 않는다. 후속 구현에서 보고서를 새 세대로 발행할 때는 terminal→summary/tower→checklist→strict handoff→controller/finalization→정확 target-date PREOPEN 순서를 한 번 완료한다. 활성 봇용 상태 조회는 쓰기 없는 projection으로 만들며 EOD/원천 생성/기동을 자동 재실행하지 않는다.

## 7. 리뷰·검증표

| 구분 | 필수 사례 |
|---|---|
| P0 경로 | root/src/독립 cwd 동일 결과, 명시 data anchor, SHA/누락/탈출/잘못된 mount 거부, 실제 loader 무외부호출 검증, cache hit 후 symlink/원천 교체 |
| P0 인계 | v5→검토한 동일 정책 successor, 당일 repair 날짜·parent CAS, nested v4 원 생성 코드, 실패/되돌림 쌍 검증, 실제 매매·provider 호출 0 |
| 버전 | 기존 v4/v5 loader·과거 producer hash 검증 유지, 새 정의/범위 hash 변조 거부 |
| 독립 탐지 | 무하락 상승지속, 다른 branch의 BLOCK/UNKNOWN/pending과 공존, 순번 단절·재연결·재시작 |
| root parity | 13개 전부의 실제 source prefix 확인점·특징·ask 일치, PEAK 무 touch, 30/120초·0/0.2% 경계, 구조 필터·가격대 경계 |
| 보조 phase | PEAK/RETEST 구분, 정의와 다른 proof 거부, 모든 매칭 branch 요청 bytes·prompt/validator 버전, 기존 hold/breakout 회귀 |
| 세션·item | PRE NXT `_NX`, REGULAR/통합 AFTER SOR `_AL`, 비운용 route 신규 활성화 금지, 잘못된 suffix 거부 |
| 가격대·union | 가격대 이동·동일 확인점 중복·동일 root 여러 filter·독점 기여 UNKNOWN, PA11 정상 DD/VOL false와 실제 결손의 구분 |
| 승인·비교 | batch 재실행/CAS 부모 충돌, 사용자 지정 초기 채택과 사후 비교 미완료의 독립성 |
| AI/주문 | 정확 요청만 재사용, budget source-day 유지, outbox reservation/ambiguous 응답, one intent |
| 상태 | 등록 완료+비교 미완료, 준비 PASS+장중 validator 오류, 과거 pending+현재 활성, hold 해제+PID 없음, 128 loaded≠실운용 전 scope 판정 |
| 봉인 | 다른 generation 혼합 거부, checklist snapshot 보존, 새 세대 인계 후 native verifier PASS |
| 부하 | 동일 frozen 시간외 원천에서 처리량/큐지연/메모리 비교. 실주문을 부하 시험으로 만들지 않음 |

구현→리뷰→보완→재리뷰→관련 pytest/compile/diff 및 문서 parser 순서로 닫는다. 문서 검토 PASS와 runtime 지원/등록/선택/배포/PID/실현 성과를 따로 보고한다. 배포·기동은 후속 구현 지시의 범위와 당시 승인·시장 상태에 따라 수행한다.

검증은 변경 단위별로 종료한다. P0는 `test_mechanistic_entry_runtime_policy.py`, `test_reversal_operating_policy.py`, `test_reversal_path_policy.py`, 실제 선택한 handoff/bootstrap 소비자 테스트를 우선한다. 후보/보조/기여도는 `test_reversal_operating_policy.py`, `test_reversal_path_policy.py`와 정확 신규 fixture, 상태 표시는 `test_error_detector_artifact_freshness.py`, `test_runtime_policy_bootstrap.py`, `test_next_preopen_readiness.py`의 영향을 받은 사례를 사용한다. 저비용 재현부터 확인하며 모든 trading suite·장후 전체 보고서 재생성·실모델 호출을 문서 리뷰의 gate로 실행하지 않는다.

## 8. 실행 순서와 인계

1. **PA0/PA13 상대경로·당일 코드 인계와 실제 launch-cwd preflight를 독립 복구 단위로 먼저 닫는다.** 당시 승인된 기술 복구를 연구/13개 등록 완료 때문에 지연하지 않는다. 운영 차단 해소와 장후 연구 성과는 별도 보고한다.
2. 연구 scope별 우선 후보를 확인하고 R0/R1 버전·탐지 parity와 PA11 기여도 특징 전달을 닫는다.
3. PA12 보조 typed 계약과 R2 명시 등록·실시간 union·장후 비교 연결을 구현한다. 13개 각각의 정의·적용 scope·미지원 원인 census를 남긴다.
4. R3 상태 표시를 함께 보완하고 회귀·문서 검증한다.
5. 후속 승인 범위의 대상일 발행·준비·배포를 수행하고 실제 PID 소비는 해당 시점에 별도 확인한다.

이 계획은 기존 Main 등록 운영을 계속 사용하는 동안 진행할 수 있다. 시간외 자료가 없는 종목·경로를 채우기 위한 수집 확대는 이 계획의 기본 작업이 아니다.

## 9. 10/8 계획 재리뷰 결과와 남은 실행 경계

| 리뷰 발견 | 계획 보완 위치 | 구현 종료 증거 |
|---|---|---|
| P0에 후보 연구/전체 발행을 묶으면 당일 오류 복구가 지연됨 | §1·§2.1·§8 | 정책 내용 동일성, 실제 launch loader, 별도 복구 receipt |
| 상대경로만 정규화하면 dependency/symlink 교체를 놓칠 수 있음 | §2.1 경로·캐시 계약 | cache hit/miss·source 교체·독립 cwd 회귀 |
| v5 당일 refresh 및 부모 origin 인계가 기존 API로 가능하다고 가정 | PA13·§2.1 | 검토 successor·날짜·CAS·rollback 검증 |
| 44개 연구 root와 실제 13개 등록의 구현 범위가 혼재 | §3 정확 root 표 | 5개 root 계열·13개 고정 정의 일치 |
| PEAK·30초/0% 재시험이 typed 보조 계약으로 전달되지 않음 | PA12·§4 | 신호→정확 입력→validator·union fixture |
| PA11을 공통 feature 보정만으로 해결하면 실제 판정도 변경될 위험 | §4 PA11 | 기존 탐지 불변·coverage 변화의 원인 대사 |
| batch schema·최신 부모·tmp 원천 보존 인계가 불명확 | §3·§5 | 명시 ADD 변환·idempotence·원천 hash 보존 |
| 등록/채택 근거 및 loaded/실제 판정 상태가 혼재 | PA14·§6 | stage·route·generation·PID identity별 상태 fixture |

이번 리뷰 결과는 **계획의 구현 누락을 보완한 상태**다. PA0~PA14의 운영 코드 수정·발행·배포가 완료됐다는 뜻이 아니다. 기존 연구의 19 테스트·6,603개 대사·3,500개 라벨 검사는 이전 연구 영수증으로 유지하며 이번 문서 변경의 코드 검증으로 재사용하지 않는다. 이번 변경은 링크·단일 owner·권한·일관성·print-only parser와 diff 검사를 수행한다. 다른 세션에서 구현이 완료되면 R0에서 해당 항목을 대조해 중복 수정을 피한다.


## 10. 후속 구현 승인에 따른 구현 결과

이후 사용자가 이 계획의 구현·반복 리뷰·배포·재기동을 명시 승인했다. PA0은 기존 정책을 보존한 source-anchor 릴리스로 먼저 복구했다. PA1~PA14의 versioned v6 탐지·typed 보조·명시 ADD·장후 승계·기여도/현재 상태 projection 구현 및 리뷰 근거는 [구현 검토](../audits/main-pre-after-pattern-implementation-review-2026-10-08.md)에 기록한다. 동결 v4/v5 파일은 변경하지 않는다.

13개 정의 등록은 다음 영업일(2026-10-12) 발행을 위한 intake이며, 장중 코드 재기동으로 신규 정책을 당일 활성화하지 않는다. 현재 bundle, 코드 배포, 신규 등록, 장후 발행, 다음 PID 소비는 각각 별도의 상태다. 초기 등록과 미완료 보조 비교는 독립이며 장후 호출 한도는 원천일당 100회다. EOD/전체 장후를 이번 구현 검증 때문에 재실행하지 않는다.
