# Entry-split 대용량 보고서 검증·관측 및 보조판정 timeout 보완계획 — 2026-10-14

## 1. 목표와 권한

10/13 entry-split 보고서가 모니터의 8MiB JSON 제한을 초과하는 문제를 **원 전체 보고서 검증에 결속된 작은 검증 projection**으로 해결한다. 보고서 읽기·검증 가능 여부, 경제성 원천 결손, 후보 선정·설치·PID 소비를 별도 상태로 전달한다.

10/14 후속 사용자 지시로 계획 리뷰·보완, 구현·반복 코드리뷰/수정, 검증 완료 후 배포·Main 재기동을 수행한다. 원 보고서·정책 의미·bootstrap 원본과 후보 선정 권한을 보존한다. 실행 owner는 [당일 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 `DirectFamilySourceRepairEntrySplit`, 적용 인계 owner는 `DirectFamilyPreopenPolicyHandoff`다. Main 기계 연구 후보 반영은 [별도 계획](main-cumulative-research-policy-adoption-plan-2026-10-14.md)을 따른다.

10/14 추가 요청에 따라 **13:36:17 삼성전자 OpenAI timeout의 원인·해소계획을 §10 T0–T5에 추가**한다. 이 축은 `AuxiliaryCircuitRecoveryRepair1012`가 소유하고 혼합 감시 순환은 `NonfixedDispatchReadinessReview1012`와 대사한다. entry-split 크기 결함과 timeout 사이의 인과관계는 미입증이며 두 축의 완료를 독립 판정한다. 승인 범위는 검증/관측 reader와 Main 전달·로컬 처리 결함 수리, 검토된 코드 배포·Main 재기동이다. 시험을 위한 provider/주문 호출, 정책 재선정, 원 보고서 전체 연구 재생성은 수행하지 않는다.

## 2. 현재 확인한 최초 단절과 독립 결손

| 단계 | 확인한 증거 | 의미 |
|---|---|---|
| 보고서 | [10/13 report](../../data/report/entry_split_order_plan/entry_split_order_plan_2026-10-13.json) 459,131,089 bytes = 437.86MiB | 8MiB 상한의 약54.7배 |
| 불변 원본 | 같은 generation의 `generations/entry_split_order_plan_2026-10-13_f9224cfaead3cb85ea13f4376085a1d3bf11795f37f1051b0088c40828c364c3.json` 539,058,129 bytes = 약514.09MiB | 별도 native bounded reader의512MiB 상한도 초과. 날짜 alias와 bytes가 같다고 가정할 수 없음 |
| 모니터 reader | [submission_bottleneck_monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py)의 `_latest_dated_json` → `_small_json` | 파일 크기 검사에서 `semantic_artifact_size_limit`; native report-policy 검증까지 도달하지 못함 |
| 재확인 | [latest monitor](../../data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json), 10/14 13:26:00, run `8419e78a46494df08132e944ffef99f6` | execution completed, semantic partial, entry_split unobservable/size_limit |
| 별도 관측 | 같은 monitor의 `blocker=no_identified_scanner_machine_evaluation` | 크기 결함만 수리해 전체 monitor 정상이라고 할 수 없음 |
| 후보 정책 | [10/13 policy](../../data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-10-13.json) | `runtime_apply_allowed=false`, buckets 0, execution_model_disposition=source_gap |
| 정책에 기록된 결손 | `operating_owner_source_invalid:actual_outcomes`, `clean_baseline_paired_realized_population_incomplete` | 실제 결과·누적 paired 원천 문제. 모니터가 읽기 전에 이미 후보 비활성 상태 |
| 준비된 적용 정책 | [10/14 bootstrap](../../data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-14.json)의 ENTRY_SPLIT env | 기존 7/28 정책 파일·버전을 가리킴. 10/13 후보 설치 증거가 아님 |

13:10 완료·partial에 대한 사용자 보고와 같은 size-limit 원인이 13:26 artifact에도 남아 있었다. 이번 읽기 점검에서 438MiB 전체 native 검증을 실행하지 않았다. 작은 정책에 쓰인 hash·결손 값의 확인을 전체 report-policy PASS로 승격하지 않는다. bootstrap env 확인 역시 현재 PID의 개별 정책 소비 확인이 아니다.

정책에 기록된 generation은 `f9224cfaead3cb85ea13f4376085a1d3bf11795f37f1051b0088c40828c364c3`, report **semantic** SHA는 `944b4c067923da070ca6f96f9c996917e4c8f7c37376fe75350086c1cc59d4ca`다. 이 값은 원 파일 byte SHA가 아니다. 구현 때 두 hash와 원 generation을 독립 검증한다. 날짜 alias에만 적용된 기존 서식 압축 기록이 있으나, 이번 stat 확인만으로 두 보고서의 값이 같다고 확정하지 않았다.

## 3. 생산자·소비자에서 바꿀 지점

| owner | 현재 계약 | 보완 |
|---|---|---|
| [entry_split_order_plan](../../src/engine/scalping/entry_split_order_plan.py) | report/policy canonical digest binding, immutable generation과 날짜 alias 발행 | native validator와 파일 bytes를 그대로 유지. 기존 [장후 wrapper](../../deploy/run_threshold_cycle_postclose.sh)의 publication adapter에서 검증 worker·projection 발행 |
| 같은 owner의 `_read_entry_report` | 최대512MiB를 한 번에 읽고 json.loads; read 전후 일부 stat 검사 | 원 함수를 보존하고 새 role helper의 strict bounded reader·값 보존 임시 사본을 장후/이관 worker에서 사용 |
| 같은 owner의 `validate_report_policy_generation` | 원 full report와 policy의 canonical hash 재계산, schema/date/recommended/atomic/model 계약 확인 | projection 작성의 native 판정 owner 유지; 축약 dict를 full report로 가장해 호출하지 않음 |
| [runtime_approval_summary](../../src/engine/runtime_approval_summary.py)의 `_large_companion` | 큰 report를 native reader로 읽어 binding 검증 | verified receipt를 재사용할 수 있는 같은 family reader 도입; cold full 검증과 warm reuse 분리 |
| submission bottleneck monitor | 날짜 report를 bounded JSON으로 직접 읽음 | entry-split 전용 verified projection reader 사용; 다른 family의 8MiB 제한 유지 |
| [bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py), [summary handoff](../../src/engine/automation/postclose_summary_handoff.py), [artifact detector](../../src/engine/error_detectors/artifact_freshness.py) | prepared policy·source/hash·완료 상태 소비 | alias/manifest 변경 시 같은 세대 확인; source gap/미선정/미설치 상태 그대로 전달 |

location gate: 원 의미·검증 producer는 기존 scalping owner, 관측 adapter는 기존 monitoring owner에 둔다. 분리가 필요하면 이 패키지 안에 family 전용 module을 둔다. `src/engine` 루트 신규 모듈, 독립 cron, 별도 주문/정책 publisher를 추가하지 않는다. 자동화 wrapper나 운영 절차를 바꾸는 구현은 관련 운영 문서·현재 checklist를 같은 변경에 갱신한다.

## 4. E1 — 작은 검증 산출물 계약

### 4.1 세 산출물

1. **Projection**: 모니터가 실제 사용하는 report 요약. 목표 ≤256KiB, 최대512KiB. 후보 전체 재생 row/trace를 담지 않는다. 상태·count·경제성 값·blocker가 늘면 상세는 별도 ref로 제공하며 전체 개수와 생략 여부를 함께 기록한다. 필수 상태를 truncate해 성공으로 보이지 않게 한다.
2. **Validation receipt**: 원 full report-policy native 검증 결과와 projection의 내용 결속. 최대64KiB. 실패도 이유/검증 범위를 기록하되 verified receipt로 재사용하지 않는다.
3. **Generation manifest**: 위 두 파일, immutable full report·policy의 경로/hash/size, 날짜 alias의 선택 generation을 연결한다. 최대64KiB. 마지막에 원자적으로 교체하는 유일한 commit pointer다.

proposed schema는 `entry_split_monitor_projection_v1`, `entry_split_monitor_validation_v1`, `entry_split_monitor_generation_v1`이다. 실제 필드/배치는 구현에서 native schema와 함께 version 관리한다. 신규 경로는 기존 `data/report/entry_split_order_plan`의 generation 하위로 한정한다.

### 4.2 필수 결속 필드

- source_date, publication/validation time, prepared_effective_date, generation_id.
- 원 report/policy path, byte SHA256, canonical content SHA256, byte size. canonical hash는 기존 `artifact_generation_binding` 제외 규칙 그대로 계산한다.
- source inventory/계약 hash, 원 producer code ref/hash, 검증기 version/code hash, projection schema/hash와 본문 hash.
- `native_validation.status/reason`, `report_policy_binding`, `execution_model_contract` 판정과 검증한 범위.
- 모니터가 사용하던 `economic_acceptance` 필드, 후보 개수, 누적 source date 개수, clean baseline, policy version, runtime_apply_allowed, scope/bucket 개수, native blocker 목록/count. 수치 null은 그대로 유지한다.
- `decision_authority=report_only`, `runtime_effect=false`, `allowed_runtime_apply=false`를 **projection 권한**에 설정한다. 원 정책의 `runtime_apply_allowed`는 별도 nested 필드에 보존한다. 작은 receipt가 정책 권한으로 사용되지 않게 한다.
- full report 자체를 검증한 결과와 작은 projection만 파싱한 결과를 구별한다. 원 코드로 생성된 역사 결과는 생성 당시 code ref로 검증하고, 새 검증기가 결과를 재계산했다고 표시하지 않는다.

원 보고서의 작은 header/hash를 복사한 것만으로 validation PASS를 만들 수 없다. producer가 가진 full object의 native 검증과 최종 bytes 결속을 수행하고, migration/independent validation에서 동일 결과를 재현한다. semantic hash와 byte hash를 혼용하지 않는다.

## 5. E2 — 발행·변경 감지·성능 경계

### 5.1 발행 순서

1. 기존 family lock·source/date를 고정한다. full report/policy를 생성하고 native generation 검증을 완료한다.
2. immutable report/policy를 임시 파일에 쓰고 fsync한다. 기존 semantic generation을 유지한다. 원본을 변경하는 새 generation이면 새 ID를 사용한다.
3. report/policy에서 projection을 만들고 **모니터가 실제 필요로 하는 필드와 원 full report의 projection 결과가 정확히 같은지** 검증한다. 기록된 bytes를 독립 hash해 receipt와 결속한다.
4. projection/receipt를 immutable 경로에 쓰고 directory fsync 후 마지막에 manifest를 atomic rename한다. report/policy 날짜 alias의 기존 독자는 유지하되 새 모니터는 commit manifest의 generation을 읽는다. 전환 중 alias와 manifest가 다른 세대면 pending/mismatch이며 혼합 PASS를 내지 않는다.
5. 재실행은 같은 generation/bytes에 대해 idempotent하다. policy 의미가 같더라도 서식 변경으로 bytes가 달라지면 byte receipt를 새로 검증한다. semantic generation만 같다는 이유로 옛 byte receipt를 재사용하지 않는다.

### 5.2 읽기와 cache

- warm monitor는 작은 manifest/projection/receipt/정책을 읽고 원 파일 존재·신원을 검사한다. 438MiB full JSON을 매5분 read/parse하지 않는다. cache miss에서 모니터가 큰 작업을 동기 실행하지 않고 `verification_pending`을 보고한다.
- 원 경로의 workspace/release/data root를 명시적으로 해석한다. `release/src` cwd 의존, 다른 날짜 fallback, parent symlink/경로 탈출을 허용하지 않는다. 기존 허용 release/data 경로 규칙과 맞춰 검증한다.
- 검증 cache에는 실제 내용 검증으로 얻은 hash와 `device/inode/size/mtime_ns/ctime_ns`, manifest/receipt/schema/validator generation, consumer role을 결속한다. stat 일치만으로 첫 검증 PASS를 생성하지 않는다. mtime-only cache나 파일명만의 cache는 금지한다.
- `open`한 fd의 fstat와 경로 lstat를 전후 대조한다. 삭제/rename/동일크기 덮어쓰기/mtime 복원/정책-only 변경/alias 교체/읽는 중 mutation은 검증 무효화 대상이다. 부모 경로 변경도 확인한다. 이 계약의 정상 파일시스템 범위를 벗어난 변경 가능성이 있으면 warm reuse를 사용하지 않는다.
- 기존 검증 세션 재사용 기능이 family/role/내용 결속을 만족하면 재사용한다. Main 기동마다 monitor code가 대용량 파싱을 다시 하거나, 모든 validator role의 PASS를 하나로 공유하지 않는다. 코드 변경은 원 source 불변 여부와 새 reader 호환 여부를 분리하며 실제 native 의미 변경이면 재검증한다.
- full 검증은 기존 장후 producer 또는 명시된 일회 migration 작업이 수행한다. 추가 요청/공급자 호출은 없다. 캐시 미적중·실패의 재시도는 generation 변경/명시적 작업 완료를 기준으로 하고 동일 불변 파일을 매 슬롯 재검증하지 않는다.

### 5.3 큰 JSON의 처리 한계

현재 native reader는512MiB 상한이지만 **438MiB 파일을 메모리 효율적으로 streaming parse하는 구현은 아니다.** 불변 원본514.09MiB는 이 reader에 바로 넣을 수 없다. RSS를 파일 크기로 추정하지 않는다. 10/13 일회 이관은 아래 E0 절차와 기존 native 검증기의 실제 peak RSS·wall·read bytes를 측정해 허용된 worker 예산 안에서 수행한다. 예산 부족이면 원 상태를 유지하고 작업을 재설계한다.

**E0 — 상한 초과 불변 원본의 값 보존 검증:** 원본을 스트리밍 hash하면서 격리 임시 파일에서 JSON 문자열 밖의 연속 ASCII 공백을 첫 공백 한 개로 줄인다. 공백을 전부 지워 `1 2`를 `12`로 바꾸는 잘못된 원본 복구는 허용하지 않는다. 문자열·escape·Unicode·수치 표현은 변경하지 않는다. 입력/출력 크기·디스크·시간·읽기 중 변경을 제한하고 출력이512MiB 이내일 때만 기존 bounded JSON/native verifier로 넘긴다. JSON malformed/truncated/비정상 숫자·key 계약 위반은 실패로 남긴다. 원본 전체 byte SHA, 변환기 코드/규칙, 임시 사본 SHA, native semantic generation을 receipt에 연결한다. 날짜 alias도 별도로 native 검증해 semantic hash와 projection을 비교한다. 두 대형 객체를 동시에 메모리에 유지하지 않는다. 압축 사본은 검증 전용이며 원 immutable 경로·policy source ref를 교체하지 않는다. 사본도 상한을 초과하면 임의로 제한을 올리지 않고 아래 partition 계약이 준비될 때까지 partial을 유지한다.

기존 장후 publication adapter가 native 원본 검증 후 작은 projection을 발행하여 모니터의 재파싱을 없앤다. native owner 전체 파일을 변경하면 역사 probe 가격 커널 hash가 달라지므로 해당 파일 bytes를 보존한다. 장기적으로 full report 크기가512MiB를 넘거나 producer 메모리 자체가 병목이면 기존 연구 row를 immutable partition에 분리하고 index/누적 digest로 참조하는 별도 version을 구현한다. 모든 full consumer와 canonical 의미를 함께 바꾸고 native 동등성 시험을 통과해야 한다. 새 패키지 설치나 검증되지 않은 streaming canonicalizer를 이 계획의 숨은 선행조건으로 두지 않는다.

## 6. E3 — 상태 표시와 실제 결손의 처리

| 관측 결과 | 표시/행동 |
|---|---|
| projection 없음·손상·원 hash 불일치·native 미검증 | 해당 축 unobservable/verification_pending 또는 invalid, semantic partial 유지 |
| full binding 검증됨, 경제성 source gap 존재 | verification=verified, economics=source_gap, candidate not promoted; 실제 blocker 유지 |
| 비교 완료·정상 후보 없음 | verified no-candidate/incumbent carry; 결손을 후보0으로 위장하지 않음 |
| 후보 runtime 적용 가능, bootstrap가 다른 정책 | promoted_candidate_not_bound; 기존 설치 결손 표시 |
| 후보 비활성, 검증된 incumbent 준비 | incumbent_preserved_candidate_not_promoted; 후보 미설치를 배포 실패로 과장하지 않음 |
| bootstrap 후보 binding 확인 | prepared/bound; 실제 PID receipt 없으면 consumed는 not_proven |

`execution completed`는 파일 발행 작업이 끝났다는 뜻으로 유지한다. semantic complete 여부는 검증된 scope/분모와 실제 이슈를 근거로 결정한다. 크기 결함이 해결돼도 비고정 평가 분모 부재 등 다른 partial 사유는 지우지 않는다. 모니터 전체 `issues={}`만으로 PASS를 추론하지 않고 각 축의 unobservable 상태도 집계한다.

실제 `actual_outcomes`/paired 결손은 기존 `DirectFamilySourceRepairEntrySplit`가 exact 원 계획→submitted order→terminal fill→원 비용/자본/exit 증빙을 확인한다. 존재하는 원 기록의 join·schema·범위 오류만 수리하고 과거 결손을 현재 값으로 채우지 않는다. 모델/원천 계약이 불완전하면 경제성은 null/source_gap, 정책은 비활성으로 남는다. **관측 reader 결함의 완료에 경제성 개선/실제 주문 발생을 요구하지 않는다.** 반대로 관측 완료로 entry-split native 경제성·승인 조건을 면제하지 않는다.

## 7. E4 — 기존 10/13 보고서 이관

1. selected code와 원 report/policy 날짜·경로·bytes·semantic generation·source ref를 pin한다. 진행 중인 동일 family writer 여부를 기존 lock으로 확인한다.
2. 원 report의 날짜 alias와 immutable snapshot의 현재 크기/신원을 조사한다. §5.3 E0으로514.09MiB 원본의 값 보존 사본을 만들고 양쪽의 native 검증을 격리 worker에서 수행한다. 둘의 의미/선택 세대가 다르면 이관을 중단한다. 이 단계는 보고서 재생성이나 정책 재선정을 수행하지 않는다.
3. 검증이 통과한 **비활성 정책 상태도 그대로** projection/receipt에 기록한다. 원 파일·policy_version·원 생성 시각을 변경하지 않는다. migration 생성 시각/검증 코드 ref만 별도 필드로 둔다.
4. 격리 fixture와 읽기 비교에서 새 reader와 native 결과의 필드 parity, bootstrap incumbent 결속, 손상 반례와 warm I/O 예산을 확인한다.
5. 코드 리뷰·표적 검증을 닫은 뒤 승인된 배포 범위에서 monitor consumer를 전환한다. 원 연구 전체 재실행이나 후보 설치로 size 오류를 해결하지 않는다.
6. source family publication/handoff의 입력 hash가 실제 변경되는 경우에만 해당 summary→checklist→strict verifier→controller를 기존 자동화 owner로 갱신한다. report-only 부속 projection만 추가됐을 때 관련 없는 장후 family를 전부 재생성하지 않는다. 실패한 검증에 옛 PASS를 붙이지 않는다.

원본 삭제·gzip 교체·원 경로의 서식 재압축은 수행하지 않는다. 필요한 값 보존 사본은 격리 검증용이며 기존 release/PID가 소비하는 immutable generation과 원 source 증거를 보존한다. 임시 사본의 정리는 receipt 검증·소비 완료 뒤 해당 파일만 대상으로 한다.

## 8. 검증표와 완료 기준

| 범위 | 표적 검증 |
|---|---|
| native binding | full report와 projection/receipt 결과 일치, schema/date/version/atomic/model 검증 누락 0, canonical vs byte SHA 구분 |
| 크기/자원 | 8MiB 경계 아래·위/437.86MiB alias/514.09MiB immutable/512MiB reader 한계, projected 필수 필드 초과 시 명시 실패, warm full report read bytes=0 |
| 값 보존 변환 | 문자열 속 공백·escape된 quote/backslash·Unicode·수치·chunk 경계·마지막 잘림, native semantic 동등성, 원본 미변경, 변환 실패/출력 상한 초과에서 PASS0 |
| 무결성 | source/report/policy/projection 각각 변조, 누락, symlink·cwd, read 중 교체, same size+mtime 복원, stale receipt, rollback generation |
| 원자성 | report만·policy만·projection만 저장 후 crash, 마지막 manifest 전/후 crash; 혼합 generation의 PASS 0 |
| 의미 | inactive+source_gap, valid-no-candidate, candidate-bound/not-bound, incumbent carry, PID 미입증, 다른 축 partial 각각 보존 |
| 권한 | 후보 설치·policy 값·bootstrap env·주문/수량/holdout/cap/provider 변경 0, projection의 report-only 권한과 원 policy 권한 분리 |
| 자연 관측 | 정상 예약 슬롯에서 새 receipt generation/원 policy 상태 관측, size-limit만 제거됐는지 확인; 다른 경보/실제 결손 유지 |

목표 warm 입력 합계는 metadata ≤1MiB, entry-split adapter p95 ≤100ms이며 계획 예산이다. cold/migration은 peak RSS·wall·full read bytes, warm은 full read0와 cache-hit bytes·wall을 따로 계측한다. 같은 report/정책·보안검사·모니터 분모로 비교하고 전체 host/모니터 지연 개선으로 확대 주장하지 않는다. 예산 초과나 binding 불일치면 해당 새 경로 발행을 중단하고 명시적 partial로 돌아간다.

구현 표적 시험은 `test_entry_split_order_plan.py`, `test_submission_bottleneck_monitor.py`, 변경 시 `test_runtime_approval_summary.py`, `test_runtime_policy_bootstrap.py`, `test_error_detector_artifact_freshness.py`, 관련 handoff 시험이다. compile/diff와 문서 parser도 검증한다. 임계값 완화나 broad trading suite 성공으로 원 binding 반례를 대체하지 않는다.

## 9. 계획 리뷰 결과와 인계

리뷰로 다음 오해를 제거했다: 8MiB 상향만으로 해결, gzip 크기만 검사, 작은 정책 hash를 full 검증으로 간주, 검증용 hash와 설치 상태 혼동, 서식 압축을 canonical generation 변경으로 오판, cache 미적중 시 monitor hot path에서 대형 JSON 재해석, 과거 producer hash를 현재 code와 같아야 한다고 강제하는 방식.

완료를 세 단계로 보고한다: **관측 코드/receipt 결함 수리 완료**, **정상 슬롯의 원 상태 관측 확인**, **실제 경제성 원천/정책 적용 상태**. 마지막이 source_gap이어도 첫 두 단계의 기술적 완료와 구분한다. 이 구현과 실제 이관·배포·자연 관측 수용은 위 기존 owner에 연결한다. 외부 동기화 명령은 함께 작성한 정책 반영 계획의 표준 명령 하나를 사용한다.

## 10. T0–T5 — 삼성전자 보조판정 timeout 원인·해소계획

### 10.1 T0 — 같은 시도의 원 기록 대사

대상은 사용자 경보의 `OpenAI Responses HTTP timeout budget exhausted: endpoint=analyze_target, attempts=1, budget_ms=777, provider_total_ms=765`다. 발생 당시 release는 `main-nonfixed-submit-20261014-f8dc4431d`, commit `f8dc4431d0b3cc2cb84610979ec4f3440d3e8e46`, PID/start ticks는 `378870/1473429`다. 아래 수치는 해당 시도의 기록이며 현재 작업본·새 PID의 성능으로 일반화하지 않는다. 기동 후 약29분인 구간으로 초기 기동 warmup에 해당하지 않는다.

| 연결키 | 값 |
|---|---|
| scope | `005930 / SOR / 005930_AL / REGULAR / 2026-10-14` |
| native signal | `2026-10-14:SOR:SOR_REGULAR:005930:1:10118` |
| machine attempt | `aims-3f97b783c077c5ccb40c` |
| AI request | `analyze_target:005930:1791952576696:1165b426` |
| async request | `fixed-watch:ebf1d6b296a9a6b469ed0600c31fb406f30ba56fb3ea7999471702d4b09be1b5:watching:95655b24cbd29a61` |
| matched branch | `manual_path_35c2d4b8fb178441` |
| bundle SHA | `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215` |
| model / schema | `gpt-5.4-nano / continuous_reversal_union_auxiliary_v3` |

근거는 [AI trace](../../data/ai_decision_trace/ai_decision_trace_2026-10-14.jsonl)의 해당 request(점검 시52행), [요청 기록](../../data/ai_decision_requests/ai_decision_requests_2026-10-14.jsonl)의 같은 request(20행), [pipeline events](../../data/pipeline_events/pipeline_events_2026-10-14.jsonl)의 `native_signal_lifecycle`, `entry_async_disposition`, `scanner_async_result_commit`, [runtime performance 기록](../../logs/runtime_performance_info.log)의 13:37:04 snapshot이다. log rotation·append 뒤에는 행 번호보다 위 연결키로 찾는다. native lifecycle은 13:37:04에 배치 기록됐지만 내부 원 시각은 아래 13:36 구간이다. 전체 JSONL을 재생성하거나 full prompt/계좌정보를 복사하지 않고 필요한 필드만 투영한다.

| 구간 | 원 기록·계산 | 판정 |
|---|---|---|
| native 최초 eligible | 13:36:12.644622; 원 deadline 13:36:17.644622 | 원 신호5초의 시작과 만료. 마지막 eligible 관측은13:36:15.645343 |
| Main 최초 방문·claim | 13:36:15.749985 | **eligible→claim 3,105.363ms**. claim 시 남은 원 시간 약1,894.637ms |
| 분석 시작→provider adapter 호출 | 동일 PID monotonic `16517.624235105→16518.341193128` | **716.958ms**. 최초 native 관측 monotonic→분석 시작은3,333.037ms; wall 구간과 중복 합산하지 않음 |
| HTTP 예산 | override777ms, adapter local 전처리11ms, HTTP lock 대기0ms | 777ms는 원5초의 잔여 시간에서 산출된 호출 상한. API가 별도5초를 받는 구조가 아님 |
| executor 대기 | enqueue→start 약0.058ms | 이 시도의 executor queue가 주요 지연이라는 증거 없음 |
| SDK 시작→caller timeout | 약764.972ms; provider_total_ms=765 | 응답 ID 없음. 서버의 실제 처리시간·네트워크 시간으로 분해할 수 없는 로컬 elapsed |
| 실제 작업 종료 | 후속 settlement의 sdk_finished=`16519.122142053`, future_settled=`16519.122178099` | caller adapter 종료=`16519.119227214` 후 약2.951ms에 settle. `future_cancelled=false`를 무기한 잔류로 해석하지 않음 |
| worker 완료→coordinator ready→Main guard | 100.770ms + 71.527ms = **172.298ms** | timeout 이후 전달 지연. worker 완료는13:36:17.560667, 원 deadline 약83.955ms 전 |
| 최종 소비 | `evaluation_deadline_expired`, `commit_allowed=false`, `actual_order_submitted=false` | 보조 결과는 `not_evaluated_transport_timeout`, PASS 없음. 유효 응답을 얻은 후 주문이 거절된 사례로 세지 않음 |

**확인한 원인:** 호출 전에 원5초의 상당 부분이 소진되어 HTTP 상한이777ms로 줄었고, 그 안에 응답을 얻지 못했다. 최초의 큰 지연은 native eligible→Main claim 3.105초다. 분석 준비 약0.717초가 추가로 HTTP 가용 시간을 줄였다. 다만 Main의 어느 phase/lock/현재 처리 단위가3.105초를 만들었는지는 기존 per-attempt 기록만으로 확정되지 않는다. `provider_total_ms=765`를 OpenAI가765ms에 응답했다거나 OpenAI 자체가 느리다는 증거로 사용하지 않는다.

호출 전 세부 비용은 `entry_policy`140.158ms, `entry_machine_assess`98.574ms, `entry_machine_capture`37.865ms, `entry_economics`155.644ms, `entry_native_check`80.454ms다. `entry_native_load/claim/auxiliary`는 native_check의 자식이므로 부모와 중복 합산하지 않는다. 원 `kt00011`은 같은 attempt의 exact-price 조회에 약62.714ms, admission wait 약0.111ms, 1회 `fresh_success`였다. 해당 호출을 REST 속도 제한·자금조회 timeout으로 분류할 근거가 없다.

원 0B/0D age는 약159/158ms로 이 시점의 체결·호가 노후화가 timeout을 만들었다는 증거도 없다. 같은 PID의 확인한 AI trace에는 앞선13:23:17 응답 수신과 이번13:36:17 timeout이 있으나, 이를 전체 API 계정 부하나 장애율의 분모로 사용하지 않는다. 이 request의429·인증 실패 근거는 없다. [OpenAI 공식 오류 구분](https://developers.openai.com/api/docs/guides/error-codes)은 timeout과429·인증 오류를 구분하며, 이번 문자열은 로컬 wall-clock wrapper에서 생성됐다. 일반 retry 안내로 원 deadline·중복 전송 방지를 변경하지 않는다.

### 10.2 원 계약과 수정 owner

발생 release의 [EntryDeadline](../../src/engine/scalping/entry_deadline.py)은 native anchor+5초와 caller deadline의 더 이른 시점을 유지하고 wall/monotonic 중 더 짧은 잔여 시간을 사용한다. `transport_ms`는 `min(기존 HTTP 상한, (remaining-response_reserve)×1000)`에서 정수 ms를 산출하며 최소시간을 덧붙이지 않는다. 당시 reserve 실측값·산출 직전 remaining은 request별로 직접 기록되지 않아777ms의 항별 역산은 미완료다. 이를 관측 결손으로 보완하며 reserve가 잘못됐다고 단정하지 않는다.

| owner | 확인한 현재 경로 | 수정 방향 |
|---|---|---|
| [runtime_performance](../../src/engine/monitoring/runtime_performance.py), [Main loop](../../src/engine/kiwoom_sniper_v2.py) | `record_native_ready`가 기존 completion event를 깨우고, `prioritize_native_watches`가 Main 처리 단위 사이에서 WATCHING 순서를 변경 | event 도입은 이미 구현됨. 이번 방문 지연/긴 처리 단위의 새 결함만 재현·수리 |
| [state handler](../../src/engine/sniper_state_handlers.py), [async coordinator](../../src/engine/scalping/scanner_async_eval.py) | native claim→prepare→AI worker→완료→Main guard | 고정/비고정의 동일 원 신호·단일 claim/lease와 보호 위치를 유지하며 전달 지연 축소 |
| [ai_engine_openai](../../src/engine/ai_engine_openai.py), EntryDeadline | policy/source/machine/economics/최종 검증→request 저장→HTTP 잔여 예산→SDK future | 기존 계약이 같은 중복 준비를 줄이고 남은 시간·실제 SDK 종료를 정확히 구분 |

위 링크는 작업본 owner 위치다. 읽기 점검에서 `ai_engine_openai.py`, `runtime_performance.py`, `sniper_state_handlers.py`는 발생 release와 작업본 bytes가 달랐고 EntryDeadline은 같았다. 구현 시작 시 최신 selected/PID와 작업본 diff를 다시 pin하여 다른 세션의 수리를 덮어쓰거나 이미 적용된 변경을 재구현하지 않는다.

선행 [공유 deadline 계획](main-entry-auxiliary-shared-deadline-latency-remediation-plan-2026-10-13.md)과 [10/14 제출 병목 계획 B3](main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md)의 원5초·동일 workload·완료 우선순위·자연 수용 계약을 재사용한다. source file/test는 위 기존 role package에 두고 engine root 신규 module·cron·worker·별도 provider 경로를 추가하지 않는다.

### 10.3 T1 — 3.105초를 만드는 구간 확인

1. 기존 bounded 진단에 같은 PID/start ticks·signal/attempt·scope generation으로 `eligible`, wake hint 등록, Main wake, 해당 loop phase/처리 단위 시작·종료, target enqueue/최초 방문, claim, prepare dispatch를 연결한다. wall 원 시각을 보존하고 elapsed는 같은 PID monotonic으로 계산한다. 신호가 이미 방문한 target에 발생했는지, pending target에 발생했는지도 구분한다.
2. 기존 event/hint가 언제 소비되는지, queue 정렬 뒤 해당 target 방문 전에 다음 loop로 이월되는지, 동기 정책검증·진단 flush·계좌 동기화·다른 target 처리·의도된 wait가 원 신호 창과 겹치는지 확인한다. 지금은 이들을 원인 후보로 두며 특정 작업을3.105초의 원인으로 확정하지 않는다.
3. `budget_before_transport_ms`, 사용한 `response_reserve_ms`, timeout override, capture 전후 remaining, executor enqueue/start의 remaining, caller 종료와 실제 future settlement를 기존 request 진단에 포함한다. 원 숫자 의미를 바꾸거나 caller 종료를 SDK 종료로 채우지 않는다.
4. per-tick 파일 쓰기·fsync·DB/API 조회 없이 bounded 메모리 표본과 기존 배치 sink를 사용한다. 표본 소실·eviction·loop phase 미식별은 unknown으로 표시한다. entry-split 작업과 I/O 경합을 주장하려면 동일 시각 host/phase 증거가 추가로 필요하다.

### 10.4 T2 — native-ready에서 Main claim까지 우선 전달

1. T1로 재현된 경로에만 수정한다. 이미 있는 wake event·WATCHING 우선순위가 Main의 실제 다음 방문까지 이어지도록 한다. 이전 loop에서 이미 처리된 target의 신규 신호도 기존 eligible queue에 인계하되 동일 signal을 재claim하지 않는다. 단순 hint pop을 실제 방문 완료 receipt로 사용하지 않는다.
2. 한 동기 처리 단위가 긴 경우 권한이 없는 선택적 진단·반복 조회를 기존 배치/캐시로 옮기거나 bounded 단위 사이에 native/완료 인계를 넣는다. 계좌·주문·custody의 원자적 작업 중간을 중단하지 않는다. 오래된 ready hint는 원 deadline/generation 검증으로 제거하고 새5초를 부여하지 않는다.
3. HOLDING/EXIT/COMMIT 보호 위치, 고정·비고정의 원 admission·순환 fairness·정원·단일 lease/ACK를 보존한다. 삼성만 먼저 처리해 다른 종목의 만료가 늘어나는 변경을 개선으로 인정하지 않는다. 대상 제거·감시 quota 감소·worker/동시성 증가로 처리시간을 줄이지 않는다.
4. 목표는 기존 계획의 최초 eligible→Main claim·prepare dispatch **0.50초 이하**다. 해당3.105초에서 어느 구간이 줄었는지 paired evidence로 보고한다. 아직 측정된 개선치가 아니다.

### 10.5 T3 — 호출 전 약0.717초의 중복 처리 감소

1. 같은 불변 policy/source/model/registry/overlay generation에서 이미 검증한 view만 공유한다. policy resolve·machine assessment·capture·economic observer·native 최종 확인을 세분하고 실제 중복 load/serialization/hash를 수리한다. current pointer·revocation·claim 생존·freshness·경제/계좌/주문 guard는 원 시점에 계속 검증한다.
2. cold policy 검증을 기존 준비 단계에서 끝내고 hot call에서는 내용에 결속된 warm view를 사용한다. 실패·generation 교체·내용 변경은 재검증 또는 명시적 보류다. 검증을 생략하거나 다른 generation의 성공을 캐시로 붙이지 않는다.
3. 원 request capture/outbox 예약·필수 append는 전송 전에 완료한다. 같은 객체를 여러 번 만드는 비용과 선택적 큰 진단 projection을 줄이되 crash 복구·중복 전송 억제를 보존한다. 이번 trace fsync 약5.892ms만으로 전체0.717초를 설명하지 않는다.
4. 이번 `kt00011` 성공62.714ms를 근거로 TTL·exact 가격 계약·rate guard를 완화하지 않는다. T3는 같은 유효 입력의 재사용과 중복 소비를 개선한다. 새 Kiwoom 요청/응답/복구 변경이 필요해지면 별도 공식 API Reference Gate를 먼저 이행한다.
5. `analyze_target` 시작→실제 SDK 시작 **0.50초 이하**, attempt별 전체 warm local p95 **1.60초 이하**라는 기존 목표를 재사용한다. 구간별 p95나 부모·자식 시간을 합산하지 않는다. 남은 시간을 HTTP에 돌려주되 모델·프롬프트·원5초·reserve 상한을 조정하는 효과와 섞지 않는다.

### 10.6 T4 — 응답/timeout 종료와 Main 인계

1. worker 완료→coordinator ready→Main guard의 **100.770/71.527ms**를 개별 계측하고 기존 completion notification과 Main 완료 인계를 연결한다. polling/재정렬/선택적 로그 때문에 생기는 대기를 줄인다. 결과의 원5초·scope·claim·보조 응답 계약을 Main에서 다시 검사한다.
2. 이번은 provider 응답 자체가 없었다. 인계172.298ms를 줄였다고 이 timeout을 PASS나 제출 가능 결과로 바꿀 수 없다. 유효 응답이 있는 별도 자연 시도에서 원 기한 내 소비가 개선됐는지 확인한다. 무응답·기한 후 응답·실제 FAIL은 구분하고 자동 PASS fallback을 만들지 않는다.
3. 성공/실패 공통 후처리의 실제 비용으로 reserve 적합성을 점검한다. 실패 전체 추가 로그 시간을 성공 reserve에 일괄 합산하거나 reserve를 키워 HTTP 시간을 더 줄이지 않는다. 기존 무표본0·상한250ms 계약을 유지하며 초과 비용은 별도 보고한다.
4. `SDK 미시작`, `SDK 시작 후 caller timeout`, `응답 수신/계약 실패`, `429`, `인증 오류`, `원 deadline 만료`를 정확한 request로 분리한다. 기존 회로·backoff·provider quota·outbox uncertain 계약을 유지한다. 이번 future가 정상 settle된 점을 회귀 근거로 보존하고, 일반 future 미종료 반례에서는 실제 settle 전 슬롯/예약을 중복 해제하거나 재호출하지 않는다.

### 10.7 T5 — 검증·완료 기준과 실행 순서

| 검증 | 필수 반례·수용 |
|---|---|
| 원 시도 재현 | 고정 clock/stub으로3.105초 claim 지연·777ms HTTP budget·응답 없음·늦은 Main 소비를 재현. outcome은 transport not-evaluated/expired 유지 |
| wake/queue | sleep 진입 전후·다른 target 처리 중·대상 방문 후 신규 신호·hint pop 뒤 loop 이월·완료 이벤트 동시 발생. lost wake/중복 claim/보호 위치 이동0 |
| deadline | wall clock 이동·잔여0/1ms 경계·reserve 무표본/상한·capture가 예산 소비·executor가 원 기한 초과. 신호/재시도/prepare에서 deadline 연장0 |
| future/terminal | caller timeout 뒤 성공/예외/미종료/취소 실패, late settlement 중복 callback. SDK 종료와 caller 종료 구분·slot/outbox exact once·늦은 결과 제출0 |
| 의미/안전 parity | 같은 source/정책/model/prompt에서 정상 기계·보조 의미, revocation/원천 노후화/계좌·주문·custody guard, 고정/비고정 fairness 및 누락 분모 유지 |
| 성능 | 같은 replay workload에서 baseline/candidate를 최소3회 교차 비교. 준비/동기/timeout을 포함한 offered 분모·unknown·cold/warm·계측 overhead를 명시하고 claim/SDK 전/local total/Main 인계를 따로 비교 |
| 자연 수용 | 승인된 적용 후 같은 PID/release/attempt의 실제 시각과 provider response·Main terminal 연결. 표본 부재는 pending, 성공/ENTER/PASS/주문 건수는 별도 |

표적 시험 owner는 기존 `test_native_signal_claim_diagnostics.py`, `test_scanner_async_eval.py`, `test_scanner_async_entry_bridge.py`, `test_main_rest_ws_latency.py`, `test_ai_engine_openai_transport.py`다. 필요한 반례만 추가하고 provider는 stub을 사용한다. Python 수정 시 해당 pytest·compile·diff, 문서 수정 시 링크/owner/권한 확인과 print-only parser를 실행한다. 실제 provider 호출·실주문을 시험 목적으로 발생시키지 않는다.

실행 순서는 **T0 원 시도 보존 → T1 원인 세분 → T2/T3 표적 수리 → T4 인계/분류 보완 → 자기 리뷰·수정·재리뷰·표적 검증 → 승인된 적용의 자연 T5 수용**이다. E0–E4 대용량 검증은 별도 worker/예산에서 수행하며 장중 Main의 시간 예산을 사용하지 않는다. 구현·배포·자연 관측·비용 후 성과를 따로 닫는다. timeout0이나 수익 발생을 보장하지 않으며 로컬 시간을 줄인 뒤에도 모델 응답 시간이 원 기한을 넘을 수 있다.

### 10.8 이번 계획 보완의 리뷰 결과

재리뷰로 다음을 명시했다: **3.105초 구간은 확인됐으나 내부 phase 원인은 미식별**, HTTP765ms는 서버 시간 아님, reserve 실측은 미기록, future는 후속 기록에서 종료 확인, timeout에 PASS 없음, 뒤의 Main 지연은 독립 구간, entry-split와 인과관계 미입증. 기존 구현과 충돌하지 않도록 발생 release와 현재 작업본을 분리하고 기존 stable owner를 재사용한다. 이 절의 원인 수치는 구현 전 읽기 점검 결과다. 코드 수리·표적 검증·이관·배포·자연 성능 결과는 별도 구현 리뷰와 실제 receipt로 보고한다.

초기 계획 보완의 문서 검증 기록: 로컬 링크24개·표8개의 정합성과 기존 OPEN owner4개의 단일 소유를 확인했다. print-only parser는25항목을 파싱하고 exit0, diff/공백 검사도 통과했다. 해당 초기 단계는 문서만 변경해 실행 시험을 하지 않았다. 후속 승인 구현의 시험·배포 결과는 §11과 구현 리뷰의 별도 증거를 따른다.

## 11. 구현 전 추가 리뷰와 배포 경계

- 현재 소비 릴리스 `f8dc4431d`에서 격리 작업본을 만든다. 기본 workspace HEAD `fbeb73eeb`에는 배포된 일부 Main/AI/감시/코드 인계 수리가 없으므로 workspace 파일을 통째로 복사하지 않는다. 다른 세션의 미커밋 변경은 보존한다.
- T2 코드 리뷰로 hint가 정렬 순간 소모되고 이미 방문한 WATCHING 대상의 새 ready가 같은 pass에 재편입되지 않는 경로를 확인했다. 실제 방문 token과 ACK를 연결하고 동일 pass의 재편입 횟수를 제한한다. 이 두 경로의 결함 확인을 과거3.105초의 특정 내부 원인 입증으로 확대하지 않는다.
- 작은 보고서의 기존 native 검증은 유지한다. 큰 원본의 projection이 누락·invalid·stale면 모니터 hot path에서 full parse로 fallback하지 않는다. source gap과 receipt 결함/미관측을 별도 표시하며 bootstrap PASS만으로 미관측 축을 observed로 표시하지 않는다.
- warm 재사용은 cron마다 새 프로세스로 실행되는 경우까지 포함한다. 이미 실제 full 검증·hash를 수행한 producer receipt의 소스 신원·validator/role·작은 내용 결속을 대사하며 매 슬롯 대형 source를 다시 읽지 않는다. 신뢰된 불변 writer/로컬 파일시스템 범위와 임의 관리자 변조에 대한 한계는 그대로 명시한다.
- 이관 worker는 시간·입력/출력/디스크·주소공간 예산을 고정하고 peak RSS·wall·read bytes를 기록한다. 같은 보고서의 native 객체를 동시에 두 개 유지하지 않는다. 자원 초과는 명시적인 pending/실패이며 의미 검증을 생략해 성공시키지 않는다.
- 배포 전 delay·stop·holding-vote 코드 검증과 원 PREOPEN→후보의 정확한 reviewed source pair, active-policy code handoff를 닫는다. 원 machine bundle·128scope membership·현재 auxiliary common-support overlay를 보존하며 과거 보조정책 발행을 재실행하지 않는다.
- 공유 checklist와 선행 봉인 문서가 다르면 두 bytes를 보존한다. 기존 release-set/detector/Sentinel 잠금 아래 그 문서만 CAS 절차로 다루며 다른 source mismatch를 무시하지 않는다. graceful drain→selector/문서 발행→native 준비→기동→singleton successor PID/start/cwd 소비 확인의 순서를 따른다.
- 기존 `DirectFamilySourceRepairEntrySplit`, `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`, `DirectFamilyPreopenPolicyHandoff`를 사용한다. 코드·기동 수용으로 경제성 source_gap이나 자연 성능 pending을 닫지 않는다.

추가 구현 리뷰에서는 원본 JSON 토큰 사이 공백을 전부 제거하면 잘못된 숫자/키워드를 정상 값으로 바꿀 수 있는 결함, 재검증 시각 때문에 불변 receipt가 충돌하는 결함, worker 강제 시간 종료 뒤 임시 사본이 남는 결함을 수리 대상으로 확인했다. 연속 공백 축소·strict JSON 검증·내용 결속된 idempotent 재사용·부모 소유 임시 디렉터리 정리로 보완하고 반례를 검증한다. source/정책·작은 산출물의 경로는 관리 data root의 정확한 family/date 경로로 한정한다.

실제 발행은 기존 장후 wrapper의 정상 생산/최종 handoff 복구 지점에 인접한 bounded worker로 수행한다. 이전부터 승인된 정상 publication의 alias 서식 처리와 새 검증 migration을 구분한다. 새 migration은 기존 alias/불변 원본·정책의 bytes를 변경하지 않으며, 현재 수리에서 native owner 전체 파일 hash와 역사 probe 커널 증거를 보존한다. runtime summary의 장후 byte SHA 전체 읽기는 유지되며 warm monitor의 full read0 측정에 포함하지 않는다.

## 12. 실제 이관·첫 예약 실행의 추가 수리

10/14 실제438MiB alias/514MiB 불변 원본의 native 검증은66.66초/최대RSS1,884,928KiB로 통과했다. 원 bytes와 generation을 보존하고7,017bytes projection을 발행했다. 새 프로세스3회의 warm fullreport read는0, 소비13.528/13.576/13.549ms였다. 첫 코드 릴리스4e21d783e는14:24:53 PID547164/start1938099의 native 정책 소비와 보호 정책11개 해시 보존을 확인했다.

그러나 첫 예약 Sentinel(14:26:25)은 raw `release/data` mount 경로를 소비자가 전달해 strict canonical source 검증에 거부됐다. trusted data root를 consumer 진입점에서 한 번 resolve하고 이후의 family/date 파일·자식 symlink 검사는 유지한다. 실제 native proof와 release/data symlink를 사용하는 whole consumer 반례2개가 수정 전 실패함을 확인하고 재검증한다. native kernel/helper/원 보고서/정책·기계/보조/매매 코드는 이 추가 수리에서 변경하지 않는다. 동일 승인으로 scoped source pair·반복 리뷰·표적 검증 후 ordered 재배포·실제 PID와 후속 예약 결과를 수용한다.

## 13. 재기동 직후 진단 순서의 근본 보완

14:36:49 경보를 재검증한 결과, Main 내부의 첫 full error detector가 launcher의 bootstrap 검증→intraday consume/verify→최종 record-pid보다 먼저 실행됐다. 14:37:18 소비 완료 뒤 strict generation 오류가 없어졌다는 사실만으로 이 순서 결함을 닫지 않는다. 첫 full 진단은 실제 자기 PID/start ticks/cwd·선택 commit/root·당일 bootstrap/verify·해당 시 consumed receipt와 final record-pid가 모두 일치한 뒤 실행한다. 이번 ordered 배포로 시작한 PID는 같은 transition의 complete/pass·successor identity까지 기다린다. record-pid만으로 먼저 진단하는 추가 경합을 닫으며, 이미 완료된 과거 배포의 PID로 이후 같은 릴리스 재기동이나 다음 날짜 native PREOPEN을 묶지 않는다. Main 평가 스레드는 이 진단 대기와 독립적으로 시작하며 대기 중 heartbeat를 갱신한다. 시작 시점부터 기존150초 한도를 고정하고 timeout/잘못된 영수증/세대 변경은 명시적인 startup failure와 실제 점검으로 노출한다. 대기를 PASS나 정책 소비 성공으로 발행하지 않는다.

최종 record-pid는 기존 launcher의 마지막 위치와 권한을 유지하되 현재 선택된 immutable router를 호출한다. 과거 workspace router로 새 receipt 필드가 누락되는 경로를 없앤다. receipt의 start ticks를 포함해 PID 재사용과 이전 기동 영수증을 거부하고, 정상 native PREOPEN과 장중 handoff를 각각 검증한다. 이 작은 영수증 대조에 native full 검증·10GB 원천 읽기·provider 호출을 재실행하지 않는다.

Sentinel은 기존 observer owner에서 run 시작/완료·선택 bytes SHA·code root/commit·PID receipt 신원을 작은 observer_generation으로 결속한다. 발행 전에 선택 세대가 바뀌면 deferred/partial로 남긴다. ordered publish는 기존 dated monitor의 정확한 경로·byte SHA·mtime·run/date/as_of·완료/semantic 상태를 작은 predecessor 증거로 저장한다. detector는 그 bytes 그대로인 과거 partial만 현재 승인된 complete transition의 다음5분 slot+전체 wrapper180초 한도 안에서 pending으로 구분한다. 기존600초 stale·실패·잘못된 JSON/신원·현재 세대 partial은 그대로 실패하며, 모르는 세대나 임의 grace로 성공 처리하지 않는다. 이전 실패 내용도 진단에 보존한다.

실제14:40 예약→14:41:59 완료에서 entry-split은 verified projection·full report read0·metadata18,581B로 확인됐다. 그러나 전체 partial에는 scanner 평가 분모 미식별과 장중 deadline 결손이 별도로 남는다. 이를 시작 순서 수리로 숨기거나 source gap을 valid_empty로 바꾸지 않는다. 원5초·정책/모델/프롬프트·매매/원천 stale guard·custody와 자연 경제성 경계는 유지한다.

표적 종료 시험은 native/intraday 정상 준비, 자기 PID/start/root/날짜·manifest/소비/선택 오류, timeout·재시도 한도 불변, Main/heartbeat 진행, stale/실패/현재 partial 및 잘못된 predecessor·세대 변경 거부, 원 report/economic 상태 보존이다. 기존 startup/router/daemon·ordered deployment·monitor/artifact 시험 owner를 사용한다. 수리→독립 리뷰→반례 보완→재리뷰·표적 시험 후 같은 승인으로 ordered 배포하며, 실제 첫 진단과 첫 예약 발행을 별도 수용한다.

최종 통합 시험에서 기존 coverage 선언이 이미 제거된 옛 Markdown `code_improvement_workorder` 감시를 요구하는 불일치도 확인했다. 선행08dbea와 후보에서 같은 실패를 재현했고, 제거 커밋2c3b7597a를 대사해 이 오래된 선언만 제거한다. 현행 runner JSON·performance workorder 감시를 유지하며 퇴역 producer를 복원하지 않는다.

## 14. 실제 CLI 계약 누락과 실패 기동의 보존·복구

40357c426 배포는15:12:11 `deployment_pid_attestation_timeout`으로 실패했다. 신규 호출의 `--workspace`를 실제 router parser에 등록하지 않은 구현 결함이며, Python을 대체한 wrapper 모의 시험만으로 수용한 검증 결함도 있다. Main658998/start2212901의 H 소비·bootstrap PID 검증은 통과했지만 final record-pid가 CLI exit2로 실패했다. 첫 health는 실패를 그대로 드러냈으므로 이 시도를 정상 기동이나 전체 수용으로 표시하지 않는다. 원 실패 status·hold·selector와 첫 health/자연 Sentinel을 별도 실패 증거로 보존한다.

수리는 `--workspace`를 final record-pid 용도로만 등록하고 실행 router가 정확한 selected immutable source이며 모든 공유 mount/선택 root·commit·PID가 맞는지 기존 guard로 검증한다. 일반 operation/cron/print 또는 별도 root/relative/alias workspace에는 이 입력을 허용하지 않는다. 실제 `python -I selected/router.py ...`와 clean temporary managed Git release/실제 child PID를 사용하는 positive/negative subprocess 시험으로 parser와 workspace 해석까지 검증한다.

복구는 기존 release-set/detector/Sentinel 잠금과 원 실패·hold bytes SHA를 유지한다. 현재 PID의 native H/manifest/verify와 실제 source/cwd/start·singleton을 다시 확인한 뒤 검토된 이전 native PID 기록 API로 사실인 소비 메타데이터만 기록할 수 있다. 이는 실패 transition의 완료나 startup PASS를 뜻하지 않으며 해당 terminal/hold를 변경하지 않는다. 새 배포기는 명시적인 failed-hold adoption에서만 canonical current-selected 실패가 starting/attestation timeout이고 hold 소유와 원 이전 PID가 실패 receipt에 일치하는지 검증한다. 모든 표준 native preflight/code/source 검증 뒤 old hold bytes를 보존하고 새 owned hold로 CAS 원자 교체한다. unlink 공백·foreign/operator hold 삭제·실패 terminal의 성공 수정은 금지한다.

후속 새 commit/transition의 graceful drain·native 준비·실제 record-pid/complete/첫 health를 다시 검증하며, 실패한 시도의 immutable code를 직접 수정하지 않는다. 복구 수용 owner는 `tmp/startup-router-cli-repair-evidence-20261014`와 `data/report/startup_router_cli_repair_deployment/2026-10-14`다.

## 15. 15:37 이후 경보의 독립 원인 표시 보완

945c30637의 ordered 배포는15:31:42 완료했고 PID679747/start2339199의 첫 full sweep은22.056ms 뒤 시작했다. 15:37:02 경보는15:26:10 발행된 이전 observer가646.7초를 넘긴 상태를 읽었다. 기존 status 검사가 partial에서 먼저 반환해 stale와 이전 세대 원인을 가렸다. 이후 현행 세대 보고서의 partial은 별도다. upstream snapshot은15:35:12로 새 자료이나 관련 latest_event가15:08:54여서600초 조건을 통과하지 못했다. monitor.source_as_of15:15는 이전 수용 snapshot에서 승계한 값이며 현재 upstream 입력 시각이 아니다.

작은 같은 보고서 snapshot의 execution/semantic·정확한 run/date·freshness·선택/코드 generation·원 blocker를 독립 진단한다. stale/잘못된 세대가 partial 문구에 가려지지 않게 하고 현재 partial의 blocker와 축별 상태를 남긴다. 일반600초 stale·실제 결손 partial FAIL과 과거 실패 보존을 유지하며, 아래 사용자 승인 예외만 pending WARNING으로 구분한다. 판정 없음이나 issues={}만으로 valid_empty/정상·복구를 합성하지 않는다.

최근145개 이벤트는5상시종목의 session_generation_mismatch 대기였고 기존 평가 stage 모집단에서 제외됐다. 관련 평가 부재와 원천 유실은 구분하며, 세션경계 quiet의 현재 완전성은 별도 source owner의 후속 수용이다. entry-split은 verified projection/full report read0다. 첫 새 release digest cold11.60GB와 다음 자연 warm full read0/3.84초를 구분한다. 다른 source의 cold 검증을 이번 작은 진단 수리에 추가 재실행하거나 cache 경계 완화로 바꾸지 않는다.

표적 시험은 stale+partial+이전 generation 동시 결함, current partial의 실제 blocker, malformed/신원 변경, pending의 WARNING·미검증, 같은 bounded snapshot과 원 실패/경제 상태 보존을 포함한다. 기존4owner·원 정책과 승인된 ordered 배포를 사용하고 새 자연 evidence는 `data/report/observer_alert_dimensions_deployment/2026-10-14`에 분리한다.

사용자는15:40 재경보 후 충분한 대기 시간 또는 지연 원인 해소로 반복 오류를 끝내도록 명시했다. 같은 승인 범위에서 두 경계를 보완한다. (1) ordered 완료 당시600초 안이었던 정확한 captured predecessor는 첫 정상5분 slot+기존 전체 wrapper180초까지 WARNING/pending을 유지할 수 있다. 대기 중 과거 파일이600초를 넘겼다는 사실·원 partial/실패 이력은 보존한다. 이미 완료 시점에 stale였던 자료, bytes/신원 변경, 명시적 생산 실패·기한 초과·현행 보고서에는 이 유예를 적용하지 않는다. 현재/일반 보고서와 매매 원천 stale 기준은 변경하지 않는다. (2) 새 보고서의 partial은 fresh upstream·필수 reader 정상 완료·정책/분할/지연 native 증빙을 재검증한다. 판정 표본 부재, 원 계약에 결속된 SOURCE_INVALID/필수 특징 보호 판정, 정상 BLOCK/RECHECK 및 요청·응답·화면 계약이 정확한 CAUTION/VETO, Main의 정확한 거절 또는 처리 종료가 확인된 PASS는 observation_pending WARNING으로 구분할 수 있다. 원 source gap·partial/unobservable·미검증은 보존하며 valid_empty/PASS/복구를 합성하지 않는다. 미확인 PASS 소비·실패/모순 제출·실제 계약 충돌·읽기/생산 실패·세대/시각 오류는 FAIL이다. 현재 건강 cohort는 단일 as_of의 최근600초·현재 PID/start를 machine/lineage/Main 증빙에 동일하게 적용한다. 기존30분/allPID 모집단과 과거 미확인/실패는 별도로 보존하며 과거 성공을 만들지 않는다. 자연 보고서와 detector에서 새로운 출력·기존 오류의 비재발을 확인한 뒤 수용한다.

## 16. 애프터마켓 주성 조합 입력의 실제 생산 결함 수리

16:05 관측의 path_auxiliary_feature_input_conflict10건은 실제 계약 오류로 유지했다. 이후 같은036930 AFTER 조합에서29건까지 늘어 원 trace ID/attempt/원문 SHA를 보존했다. 요청·원 machine payload 발행 전 예외라 과거 개별 숫자를 복구했다고 주장하지 않는다. 같은 joint 정의의 deterministic State 입력에서 UNKNOWN/TRUE 두 확인 경우 모두 source DD0.5484460694698434와 보존된 원 FIRST DD0.6363636363636349의 불일치로 동일 오류를 재현했다.

원인은 J.compose가 원 확인 event의 top-level DD/volume를 보존하고 refinement의 rolling branch_features만 교체하는데, 상속 source projector가 DD/volume까지 rolling feature에서 읽은 것이다. reversal_extended_state.State._source의 composed 전용 override에서 validate_composed와 원 event top/base 일치를 확인한 후 두 source facts만 원 확인 정의로 맞춘다. 원 event/refinement/proof·매칭 조건·validator의 strict equality·prompt/모델·정책 membership과 원5초는 보존한다. noncomposed source bytes는 기존과 동일하다.

해당 native 모듈1개만 바뀌므로 이전128scope 근거를 그대로 수용하지 않는다. 기준945/수리 candidate를 같은76,800행에 새로 재생해128scope·621hits·동일 signal SHA를 확인하고 runner/원본·후보 source hash/결과를 결속한다. source-only 수리의 새 code handoff는 이 정확한 old/new 모듈과 fresh parity를 검증한 뒤 기존 정의/bundle/pointer를 보존해 발행한다. C.issue의 source_semantics_repair 계약을 사용하며 새 정책·원천 과거 채움·추가 경제 gate를 만들지 않는다. 새 PID의 자연 주성 입력 생성/기존 conflict 비재발과 detector 결과를 별도로 확인한다.

## 17. 첫 진단의 영수증 갱신 경합 수리

b0d795c1c의 ordered 배포는16:43:08 PASS지만, 첫 진단은16:42:53에 시작해 실패했다. 읽기 중 최종 영수증이 원자 교체되자 startup_receipt_changed_during_read를 영구 실패로 취급한 것이 원인이다. 그 결과 완료 전 시각으로 이전 observer 세대를 검사해 observer_generation_not_current가 함께 발생했다. 최초 실패 영수증·원 보고서·배포 PASS는 서로 구분해 보존한다.

startup_consumption_state는 정확한 읽기 CAS 경합만 pending으로 되돌려 기존 원150초 안에서 재확인한다. polling이 기한을 연장하지 않으며 지속 경합은 원 기한 실패다. 잘못된 PID/세대/정책·symlink/손상·명시적 실패·source provenance는 실패를 유지한다. observer grace, 기계/보조 정책, native kernel, source stale, 원5초는 변경하지 않는다. 실제 router 검사와 daemon 대기를 조합한 경합→ready/지속 경합→timeout/실제 invalid 실패 반례를 검증한 뒤 기존 ordered 절차로 배포한다. 첫 full sweep은 정확한 complete/PID 소비 이후여야 하며 정규 observer 예약과 후속 자연 진단으로 수용한다. 증거 owner는 data/report/startup_receipt_race_deployment/2026-10-14다.

## 18. 현재 PID 수명 구간과 정상 원천 대기 구분

다섯 번째 정규16:45 예약의 b0 보고서는16:46:32→16:47:21에 발행됐으며 generation·entry-split projection은 검증됐다. 남은 충돌3건의 시각은16:39:15/16:39:33/16:40:27로, 실제 PID809464의16:42:16 기동보다 모두 앞선다. 원 trace에 PID가 없다는 이유만으로 이를 새 PID 결함으로 세면 안 된다. 원10분/allPID 기록은 보존하고, 현재 PID/start와 검증된 native birth 하한을 함께 사용해 명백한 기동 전 행만 historical로 분리한다. 기동 후 신원 미확인은 여전히 실패다.

32MiB probe tail의 시작16:37:40은 전체10분 시작16:36:32보다 늦지만 현재 PID 출생보다 앞선다. 현재 PID의 건강 검증에는 max(원600초 시작, 보수적 native 출생 하한) 이후 전체 읽기 범위를 입증하고 실제 유효 시작·과거 제외 건수를 표시한다. 원10분 reader의 partial을 바꾸거나 전체 원천 완전성으로 표시하지 않는다. 현재 수명 구간조차 덮지 못한 tail, malformed/누락 시각/미완성 행, 잘못된 actor/출생 증빙은 계속 실패다.

현재 warmup5건·exact_0B_missing1건은 source quality pass/정확한 시장·상시 종목·actual_order=false/broker_forbidden=true인 보호 대기다. native confirmation_pending_at_residence_end1건은 원 native receipt의 source_current/미확정 분모를 검증한 관측 대기다. 기존 native validator를 통과하는 정확한 상태만 WARNING/pending으로 표시하며 UNKNOWN/censored/pending 수치와 원 결손·partial은 보존한다. no-match/PASS/정책 적격/경제성 성공을 합성하지 않는다. 다른 진짜 원천/실행 계약 오류, 미분류 원인, 실제 미완전 읽기는 실패다. 보고서 생산 고장과 정책 입력 대기를 구분하는 수리이며 신호·정책·원5초·매매 권한을 바꾸지 않는다.

## 19. 최종 보고서 실행 건강과 제한된 데이터 검증 경계

§15/§18의 엄격한 표본·완전 범위 검증 경로는 유지하되, 최신 자연 보고서에서 별도 정상 상태가 확인됐다. 보고서는 current generation으로 정상 발행됐고 현재 source/machine issues는 비어 있지만,32MiB/8MiB 읽기 한계가 전체10분/30분을 덮지 못하고 AI 응답·Main 소비 일부가 미검증인 상태다. 이를 보고서 생산 실패로 합치면 정상 예약마다 동일 오류를 반복한다. 이는 최근 데이터를 더 완전하게 읽었다는 근거나 AI/주문 성공의 증거가 아니다.

최종 진단은 두 경로다. 첫 경로는 기존 엄격한 관측/보호/종료 증빙을 검증한다. 두 번째 bounded_source_quality_observation은 정상 발행·fresh/current generation·정확한 live actor/출생·입력 시각/schema/count/정책/native bootstrap/split/delay 증빙이 유효하고 현재 stage issues가 없을 때만 제한 관측을 WARNING/pending으로 표시한다. 허용된 읽기 부족은 명시적 tail_truncated·window_covered=false와 실제 bytes/source identity가 있는 clean bounded tail뿐이다. malformed/시각 누락/미완성 행/읽기 IO오류·신원/해시/정책 변조·실제 current 계약 issues는 FAIL이다. 미분류 진단은 임의로 허용하지 않는다.

이 두 번째 경로에서는 원 semantic partial, 원 uncovered 범위·unmet_conditions·source_gaps·AI invalid/timeout·미확인 PASS/소비/사건 수치를 보존한다. current_observation_verified/full_coverage_proven은 false이며 PASS/복구/정책·주문 권한을 발행하지 않는다. AI 응답·Main 소비의 실제 guard는 원래대로 실패/보류하며 각 원천 품질 알림도 유지한다. 앞 절의 미확인 결과/깨끗한 bounded coverage 자체를 artifact FAIL로 취급하던 초기 기준은 이 경계로 보완한다. 실제로 없는 과거 결과나 source receipt는 만들지 않는다.

## 20. 실제 main 발행 순서와 최종 projection 일치

f25d3282d의17:19:54 기동/첫 진단 순서는 통과했지만17:20 정규 보고서의 건강 projection은 실패했다. main이 최종 observer_generation을 붙이기 전에 건강을 계산해 발행 후 재계산과 달라진 실제 결함이다. notify 전후에 generation을 두 번 확인하므로 단순히 첫 확인 뒤로 옮기는 것으로는 부족하다. 최종 세대 재확인과 알림 상태 갱신이 끝난 직후, 세 canonical 파일을 쓰기 직전에 건강을 계산한다. 같은 발행 dict에서 선언값과 재계산값이 일치해야 하며 세대 변경은 publication 없이 deferred다. 실제 정식 대기명 fixed_watch_post_receipt_warmup도 동일한 기존 typed/native scope/금지 주문 flags 계약으로 구분한다.

회귀는 helper 조립 fixture만으로 닫지 않고 실제 main() parser→stage attach→notify→마지막 generation→projection→write 경로를 실행한다. optional notify 뒤 두 번째 generation 시각 변경, 실제 발행 dict 재계산 equality, 선택 세대 변경 시 미발행을 확인한다. provider/실원천 재계산·정책/매매 권한을 만들지 않는다. 원 f25 첫 진단 PASS와 자연 semantic 실패는 그대로 보존한다. 새 배포와 실제 첫 정규 보고서/후속 진단의 수용 owner는 data/report/observer_publication_order_deployment/2026-10-14다.
