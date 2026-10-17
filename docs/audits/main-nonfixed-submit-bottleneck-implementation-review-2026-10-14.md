# Main 비고정 관측·제출 병목 개선 구현 리뷰 — 2026-10-14

## 1. 승인·기준선·판정

사용자 후속 승인: “개선계획 리뷰 및 보완”, “계획을 구현하고 코드리뷰 후 수정보완 완료시 배포 및 재기동 승인”. [개선계획](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md)의 B0–B4를 실제 selected release `ff32b99b395b1da9cb6275da3d82263306bd7047`에서 격리해 구현했다. 기준 Main PID53125/start555479/cwd `main-io-residual-20261014-ff32b99b3/src`를 다시 확인했다. 원 PREOPEN 코드 기준은 `bd40c7f12a8c3913e638809cc8aa3cb04f29fa70`, source/publication10/13·effective10/14다.

문서 봉인 시점의 코드 수용과 실제 배포·PID 소비는 별도다. 최종 배포/시각/PID/소비 증거는 [deployment-result.json](/home/ubuntu/KORStockScan/data/report/main_nonfixed_submit_deployment/2026-10-14/deployment-result.json), native `data/runtime/release_transitions/2026-10-14/<candidate-commit>/status.json`, 같은 보고 디렉터리의 source/compatibility/auxiliary/PID receipt에 기록한다. 자연 성능·비고정 편입·실제 submit/fill/terminal·비용 후 성과는 이 문서의 코드 시험으로 닫지 않는다.

## 2. 구현과 계약 보존

| 범위 | 구현 | 보존·결손 경계 |
| --- | --- | --- |
| B0 | exact attempt/request/PID/start/hash와 실제 trace 시각으로 request/HTTP/raw/contract-valid/executable 단계를 분리; 전체 Main·fixed/scanner 분모 명시 | rotation/truncate/부분 tail·원 배열 provenance 결손은 source gap; 실제 submit과 구별 |
| B1 | reduced entry의 완성봉 close/cutoff·원 receive·WS epoch/revision/hash/watermark로 freshness 증명 | bar-open age 보존; strict/holding/reprice와 quote/transport age 불변; 미래 watermark·분 경계 결손 거부 |
| B2 | 기존 auxiliary owner에서 전체128scope·7개 프롬프트의 정확한 공통 support 설명 append를 sealed successor manifest로 발행; raw projection을 validator 전에 보존 | validator/projector/input/schema/model/options·기계 bundle/family/정의/scope 불변; 기존 잘못된 PASS를 사후 수리하거나 provider replay하지 않음 |
| B3 | exact retained fixed request가 남은 WATCHING queue에 있으면 현재 pass에서 원 result 소비; ready 우선 방문 및 worker→ready→Main clock 분리 | scanner COMMIT·orphan 경로·보호 위치·전체 population·원5초·quote/native/account/order/cooldown/custody guard 유지 |
| B4 | same-PID/current generation/route/fresh Main active snapshot에 한해 claim 전 중복 defer; 현재 적격 대기·carryover 구별 | unknown은 기존 callback; active 해제 시 즉시 복귀; physical5/long2·60/150초·rotation/quota·단일 lease/ACK 유지 |

새 Python root module·Kiwoom request/parser/FID/REG/REMOVE·provider option·cron interval·threshold·주문 실행 권한은 추가하지 않았다. 원 native bundle `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`와 family `c366914f1a2a76d85bceacd406e6c377f1fb32b2b50d757fb195484ab783ff8c`는 byte 보존 대상이다. auxiliary generation만 별도로 발행한다.

## 3. 반복 리뷰에서 보완한 결함

1. REST 조회 전 준비 시작시각으로 새 receive를 미래라고 거부하던 B1 결함을 수정했다. 실제 로컬 monotonic 소요만 capture에 반영하고 원 receive/deadline을 보존한다. 미래 WS watermark도 거부한다.
2. 신규 auxiliary manifest의5,217,257B 원 bundle을 매 요청마다 해시하던 I/O 증폭을 제거했다.128개 이하의 파일 digest만 PID/start/day/selector/native pointer/code/source signature에 결속해 재사용한다. 의미/binding 검증은 항상 수행하고 prepare/publication은 full hash한다. inode/mtime가 같아도 ctime 변화·truncation은 다시 검증한다.
3. rollback이 신규 발행 manifest field를 승계해 복원 bindings를 거부하던 문제를 수정했다. 원 manifest는 revoked generation/역사 참조로 보존하고 active issuance field를 제거한다.
4. raw projection을 frozen validator 뒤에 두면 malformed risk_verdict TypeError에서 수신 증거가 소실됐다. validator 전 보존과 실제 adapter exception fixture를 추가했다. 검증 후 로컬 실패에도 이미 소비한 transport request/PID/hash metadata를 유지한다. fallback WAIT와 실행 차단은 유지한다. received local 오류를 transport 실패 counter/circuit에 반영하던 추가 결함도 수정했다. 기존 finally의 recovery ticket abandon을 유지하며 HALF_OPEN 성공을 주장하지 않는다.
5. coordinator ready 시각을 lock 획득 전이 아닌 retained publication 안에서 기록했다. 평가 완료→ready 대기도 별도 공개한다. bridge 시험의 퇴역한 사전 capacity prefetch 기대값은 현 lazy-demand 계약으로 맞췄으며 production guard는 변경하지 않았다.
6. B4 snapshot을 callback 진입 전 시각과 비교해 항상 미래로 거부하던 문제를 수정했다. lock 안의 observed stamp와 callback 완료시각을 사용하며 원 dispatch/lease deadline을 갱신하지 않는다.

독립 리뷰는 producer→consumer→실제 Main guard, sealed registry/source/code/CAS/rollback, dirty release/original PREOPEN hash 계약을 포함한다. 구체 반례를 수리한 뒤 표적 시험을 다시 실행한다.

## 4. 표적 검증·원 창 재현

검증 로그: [integrated-tests.log](/home/ubuntu/KORStockScan/tmp/main-nonfixed-submit-implementation-20261014/integrated-tests.log), [deployment-tests.log](/home/ubuntu/KORStockScan/tmp/main-nonfixed-submit-implementation-20261014/deployment-tests.log). 최종 count와 source hash는 배포 build evidence가 봉인한다. B0–B4 관련20개 suite는1,316 passed, 배포/router/bootstrap/PREOPEN/auxiliary readiness6개 suite는935 passed를 확인했다. 마지막 received-local circuit 보완은 AI transport/entry circuit/shared deadline260 passed로 재검증했다. 최종 exact source pair를 갱신한 뒤 handoff726 passed를 확인했다. 이 recheck들은 앞선 수와 중복되며 합산해 고유 시험 수로 보고하지 않는다. 별도 gate JSON/로그/source hash를 봉인한다. Python compile, `git diff --check`, 문서 링크·stable owner·AUTO byte 및 print-only parser를 최종 문서에서 확인했다. 문서 작성 단계의 관련 owner4개와 최종 source owner를 포함한 stable parsed owner5개는 각각1개, parser 전체25개와 active checklist byte 불변을 대사했다. 최종 변경 문서2개의 로컬 링크55개와 실제 배포 결과 링크를 publication workspace에서 확인했다. 외부 sync는 실행하지 않는다.

[B0 frozen 재현](/home/ubuntu/KORStockScan/tmp/b0-frozen-reproduction.json)은 원43분 창의 machine10/attempt12/prepared4/HTTP4/raw3/timeout1/rawPASS2/contract-validPASS1/executablePASS0을 대사했다. first stop은 candle5/pre-provider native3/CAUTION1/validPASS후native1/timeout1/rawPASSsupport invalid1이다. 과거3응답의 raw 배열 provenance 결손은 유지했다. 원5개 stale 사례 전체를 오차단으로 복원하지 않는다. 원 nonfixed32=no-pattern22+sourcegap10이며 conflict40을 실제 물리 관측40으로 환산하지 않는다.

## 5. 성능 판단과 미완료 증거

[교대3쌍 component 비교](/home/ubuntu/KORStockScan/tmp/main-nonfixed-submit-implementation-20261014/b3-component-comparison.json)는 fixed5/nonfixed5+holding/order 전체12개·보호 위치를 유지하며 완료 target 방문을9번째→1번째로 옮겼다. helper p95는 약3.7→8.6µs로 증가했다. 추가 약5µs 비용은 숨기지 않으며 전체 Main CPU/I/O/COMMIT·guard 개선으로 주장하지 않는다. 전체 Main 비교가 모든 pair에서 악화되면 계획의 발행 중단/되돌림 기준으로 재검토한다.

현재 `performance_not_established`: 실제 Main 부하에서 native-ready→claim p95≤250ms, signal→capture p95≤1초, ready→guard p95≤100ms/p99≤250ms 및 worker→ready 구간을 함께 확인해야 한다. 정규5분3슬롯의 보고 실행 완료는 §8에 기록했다. 그 창의 전체 source 검증·현재 PID의 다음 정상 attempt·지연 목표 및 비용 후 성과 수용은 pending이다. 성능 미입증은 provider/timeout/threshold 완화나 실주문 시험의 권한이 아니다.

## 6. 배포·재기동과 실패 처리

[운영 절차](../runtime-release-routing.md)의 existing ordered transition을 사용한다. immutable candidate의 정확한 source pair, native33module byte parity와 보존된128scope replay 증거, full auxiliary binding parity/reader compatibility를 확인한다. 변경된 원 policy/PREOPEN/env/manifest나 검증되지 않은 source mismatch는 중단한다.

배포 전에는 shared checklist만 consumed handoff의 frozen bytes와 달랐다. 현재 active checklist는 새 consumed handoff와 byte가 일치한다. 편집본과 exact old sealed incumbent 문서를 보존하고 기존 release-set/detector/Sentinel locks 안에서만 predecessor strict 검증에 원 문서를 사용한다. graceful drain 전 selector/document를 발행하지 않는다. 선택 이전 실패에는 byte CAS로 편집본을 복구한다. 성공 시 candidate checklist와 검토된 문서를 발행한다. 원 prepared/PREOPEN receipt를 덮어쓰지 않는다.

기존 Main 정상 drain 후 code selection 및 auxiliary contract manifest를 기존 publisher의 lock/CAS로 발행하고, native stopped preparation·bootstrap·auxiliary readiness·ordinary launcher·actual PID/start/cwd 소비를 각각 확인한다. held/selected 실패는 phase evidence와 owned hold를 보존한다. force kill·alert suppression·monitor cursor reset·expensive postclose regeneration은 없다. rollback은 검증된 code/auxiliary 조합과 기존 native owner를 사용하며 retired widget/episode executor를 복원하지 않는다.

## 7. 다음 action과 단일 owner

[10/14 checklist](../checklists/2026-10-14-stage2-todo-checklist.md)의 기존 owner를 유지한다: `DirectFamilyPreopenPolicyHandoff`는 선택/기동/PID·원 날짜/해시, `AuxiliaryCircuitRecoveryRepair1012`는 실제 정상 attempt 대사, `NonfixedDispatchReadinessReview1012`는 적용 후5분3슬롯·중복/해제·full cohort, `DirectFamilySourceRepairMainMechanisticEntry`는 완성봉 source 계약을 맡는다. 코드 closure·배포·자연 실행·경제성은 서로의 PASS를 대체하지 않는다.

## 8. 실제 배포·기동 및 후속 경보 점검

- 실제 code release: `f8dc4431d0b3cc2cb84610979ec4f3440d3e8e46`, root `/home/ubuntu/KORStockScan-runtime-releases/main-nonfixed-submit-20261014-f8dc4431d`.
- 정상 drain/selection13:05:27, transition 완료13:07:20. Main PID378870/start1473429, 정확한 src cwd·native128/auxiliary128scope·7registry 소비를 확인했다. Auxiliary overlay `e79262dfbb296dd8bd643c2c6f20621ee97d5a5ebc3eae7ad24a2105c02592ee`, manifest `91a300d341e02324d15cdcf038c8336267f61c5e2017cf8a1b183ac013e415d2`. 원 native pointer/policy/PREOPEN/env/prepared bytes는 보존됐고 own hold/restart flag는 남지 않았다.
- [PID·source 검증](/home/ubuntu/KORStockScan/data/report/main_nonfixed_submit_deployment/2026-10-14/postdeployment-verification.json)과 [release-set 검증](/home/ubuntu/KORStockScan/data/report/main_nonfixed_submit_deployment/2026-10-14/release-set-verification.json)은 실제 selected PID 일치, 다른 live episode owner0을 확인했다. 기본 작업공간의 별도 source 변경은 보존하고 격리된 검증 코드만 배포했다.
- 13:06:54 strict checklist 경보는 소비 증명 이전이었다.13:07:11 consumed PASS 후13:08:50 health가 exact historical snapshot/PID를 검증해 recovered_late로 복귀했다. 원 늦은 완료08:49:10 이력은 유지하며 새 finalization을 생성하지 않았다. 봉인13:26:54 health의 resource는PASS/I/O wait12.19%다.
- 현재 submission monitor는 partial이다.10/13 entry_split 보고437.86MiB > consumer8MiB, 현재 후보 정책은 비설치/blocked이며 operator incumbent과 다르다. scanner sample 부재는 완전한 cache/raw generation·누적 decode/부분 tail proof가 없으므로 검증된 valid_empty로 단정하지 않는다. Source gap을 덮어쓰거나 threshold/alert/provider/order를 변경하지 않았다. 후속 작은 producer-owned 원 generation-bound projection은 기존 `DirectFamilySourceRepairEntrySplit`, scanner source completeness·자연 수용은 기존 `NonfixedDispatchReadinessReview1012`가 소유한다.
- 후속 병렬 stdout 기록이 이미 source-hash에 묶인 시험 파일을 덮어쓴 것을 발견했다. 새 stdout을 별도 보존하고 원 history의 정확한 offset/SHA에서 봉인 bytes를 atomic 복구했다. native handoff receipt는 다시 작성하지 않았고 해당 증거 hash가 원값과 같음을 확인했다. 이 사건·복구 경로를 최종 검증 JSON에 보존한다.
- 정규13:10/13:15/13:20 실행은 새 release로 완료됐다. 최초 cold validation97파일/11,600,227,205B/36.45초를 포함해 기록했다.13:20 warm full hash0회/3.36초, 해당 실행 physical read약49.7MB다. 현재 PID의 자연 machine/auxiliary 시도·전체 Main 지연 목표·주문 및 비용 후 성과는 pending이다.

최종 판정은 **코드·배포·PID/policy custody 수용 PASS**, **전체 observer coverage partial**, **자연 판정/성능/경제성 pending**이다. 후속 문서 상태 기록은 actual code release를 이동하거나 기동된 source를 변경하지 않는다.
