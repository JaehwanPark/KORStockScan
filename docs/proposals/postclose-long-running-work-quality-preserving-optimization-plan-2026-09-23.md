# 장후 장시간 작업의 결과품질 보존형 최적화 구현계획 — 2026-09-23

상태: **구현·검증 진행 중.** 2026-09-23 현재 9/22 episode와 widget의 최종 stage는 복구 실행으로 `succeeded`이며, 이는 최초 장시간 계산의 성능 개선 증거가 아니다. 정책 결과·PID·손익의 수용은 별도다.

목표는 기존 원천 모집단, 유효 후보 탐색공간, 비용·label·holdout 의미와 정책 결과를 유지하면서 2026-09-22 장후 장시간 작업의 중복 계산, 입력 대기 및 자원 경합을 줄이는 것이다. 이 계획은 공통 장후 계산 최적화 계획의 대체물이 아니며, 아래 네 작업의 현재 구현·감사 결과를 이어받는 제한된 후속 계획이다.

## 1. 대상 작업과 현재 상태

| 작업 | 2026-09-22 관측 | 계획에서 다룰 범위 |
| --- | --- | --- |
| Main machine policy replay | 12,127개 시도와 96개 후보를 순회했고, 원 worker는 80분을 넘긴 뒤 약 3.6GiB RSS+swap에서 중단됐다. | 비용 경로가 없는 기존 BLOCK/RECHECK 재생 생략, 기존 ENTER_NOW 보존, evidence 복사/보관 축소는 [기존 replay 리뷰](../audit-reports/2026-09-22-machine-replay-resource-review.md)에 구현·리뷰·327개 대상 테스트와 bounded 동등성 결과가 기록됐다. 이 계획은 이를 다시 구현하지 않고 다음 고정 원천 실행의 실제 시간·메모리·동등성만 확인한다. |
| Widget policy | 전체 약 1시간 47분. `signal_research` 약 3,590초, EOD 대기 약 1,892초, `auto_policy` 약 912초. | 전체 종목·grid·기간을 유지하면서 EOD 대기를 계산에서 분리하고, 검증 가능한 순수 중간 계산의 재사용만 검토한다. 관련 기존 owner는 `widget_symbol_signal_policy_research.py`, `widget_auto_trade_policy_calibration.py`다. |
| Machine microstructure final refresh / episode policy | refresh wall 약 54분에 CPU 약 3분 33초. Episode policy의 첫 시도는 output validation 실패했으나 9/23 02:05 복구 stage와 `episode_policy_refresh_2026-09-22.json`은 완료됐다. | 이미 배포된 stage 분리·bounded concurrency·checkpoint 재개를 재구현하지 않는다. 현재 유효 산출물의 해시·날짜 검증을 유지한다. 다음 신규 원천에서 같은 validation 실패가 재발할 때만 producer와 validator의 첫 불일치를 고친다. `day_replay`는 기존 적응형 fast-reference 경로를 우선 사용한다. |
| Rising missed feedback | 약 6.5GB·397,509행을 약 290초에 처리했다. 원천 단일 읽기 수정이 구현·배포됐다. | [완료된 I/O 수정](../audit-reports/2026-09-22-rising-missed-feedback-io-review.md)을 유지한다. 같은 원천을 다시 전수 실행하거나 durable cache를 추가하지 않는다. 남은 병목이 자연 실행 receipt에서 확인될 때만 별도 변경을 제안한다. |

실행 가능한 변경은 해당 날짜의 checklist에 stable ID, Due, Slot, TimeWindow, Track 및 acceptance를 둔 뒤 진행한다. 이 문서는 그 checklist owner나 배포·실행 승인을 대신하지 않는다.

## 2. 품질·권한 불변조건

1. 연구 입력은 `2026-06-05T00:00:00+09:00` 이후의 clean baseline과 기존 source-quality·row exclusion 계약을 따른다. 불량 행을 식별할 수 있으면 해당 행/구간만 제외하고 사유를 보존한다.
2. 종목 universe, 날짜 범위, 원천 행, 후보 grid, holdout, 정책 선택 기준, full/partial 결과, route/session, 비용 가정은 성능을 이유로 줄이거나 바꾸지 않는다.
3. 기존 machine `ENTER_NOW`는 모두 재평가한다. 비용·경로가 부족한 결과는 null/제외 사유로 유지하고 0 또는 gross EV로 바꾸지 않는다. 기존 BLOCK/RECHECK 생략은 현재 replay 계약의 허용 범위에만 적용한다.
4. Widget/episode의 원천 census, seed·episode identity, custody, full-cost 결과와 정책 disposition을 보존한다. `cache hit`, 빈 결과, 오류 또는 미완료를 성공·경제성 부재로 치환하지 않는다.
5. 성능 계측과 cache metadata는 정책 후보·선택·runtime 소비 입력이 아니다. 코드 완료, 산출물 검증, 정책 선정, PREOPEN/PID 소비, 자연 효과와 실제 비용조정 손익은 별도 상태로 보고한다.
6. threshold, AI/provider, 주문·수량, 계좌, bot, cap, lock/cooldown, main/widget/episode 소유권 및 hard/protect/emergency guard를 변경하지 않는다.

## 3. 구현 순서

### P0 — 비교 기준과 단계 구간 확정

- 기존 stage terminal, child resource, source hash, checkpoint와 9/22 audit receipt를 우선 사용한다. 공통 계측 프레임워크나 새 daemon/report producer를 만들지 않는다.
- 단계별 wall time을 compute, source/EOD wait, resource admission wait, retry/recovery로 나눈다. child CPU와 peak RSS가 없을 때는 미측정으로 남기며 parent CPU로 대체하지 않는다.
- 비교 입력은 완료된 immutable source snapshot으로 고정하고 source·코드·schema·설정·비용·label-as-of·후보공간 hash를 기록한다. 입력 경계가 다르면 성능 비교와 결과 동등성 주장을 하지 않는다.

### P1 — Main machine replay 자연 실행 확인

- 이미 반영된 eligibility 선계산, 허용된 non-entry replay 생략, read-only nested evidence 재사용, 1-arm 상세 cache bound가 선택된 실행본에 실제로 포함됐는지 확인한다.
- 성공·실패·미진입 모집단과 비용 제외 분모를 대사한다. 모든 incumbent ENTER_NOW 평가 여부, 후보별 경제성, 후보 순위, 최종 정책과 checkpoint source hash를 기존 세대와 비교한다.
- 성능은 전체 frozen source에서 wall/CPU/RSS/swap과 실제 replay call 수로 기록한다. 120×24 bounded fixture의 개선 수치를 전체 장후 속도 개선으로 외삽하지 않는다.
- 산출물 동등성이 깨지면 선택이나 publish를 진행하지 않고, 첫 달라진 cohort/row/metric을 좁혀 결함을 수정한다.

### P2 — Widget EOD barrier와 순수 계산 재사용

- EOD source가 유효·완료됐는지 계산 슬롯 획득 전에 판정한다. 미준비 상태는 기존 대기 예산 안에서 `waiting_for_source` heartbeat를 남기고 슬롯을 점유하지 않는다. 만료·실패·날짜 불일치는 `deferred` receipt로 남긴다. worker도 기존 EOD 검사를 반복하고, stage는 완료 EOD receipt의 입력 해시를 보존한다. 기존 timer는 변경하지 않는다.
- signal research의 기존 `ReplayContext`는 symbol-local feature/day 결과와 bounded policy page를 이미 재사용한다. 새 cache는 같은 계산의 실제 중복 CPU와 frozen source 동등성이 입증된 경우에만 해당 producer 안에 추가한다.
- optional cache key에는 target date, 전체 source generation/hash, symbol/venue/session scope, code/schema, policy/config, calendar, cost/label horizon 및 필요한 seed identity를 포함한다. 하나라도 불일치·손상·검증 실패면 cache miss 후 원래 계산을 수행한다.
- cache-on과 cache-off에서 전체 심볼 census, feature, 후보별 state, 선택 정책과 source-quality/exclusion 결과를 비교한다. 일부 종목/grid만 재생해 전체 동등성으로 간주하지 않는다.

### P3 — Episode 검증 실패 수리 후 반복 replay 축소

- 9/22 최종 episode stage와 publication receipt는 완료 상태다. 최초 실패 로그는 보존하되, 유효한 동일 날짜 최종 산출물을 실패로 재분류하거나 전수 재생하지 않는다. 신규 원천에서 재발하면 producer 출력과 validator의 schema, source date/generation, row census, hash 및 prerequisite 간 첫 불일치를 찾는다.
- 기존 `cache_disabled_fast_reference`는 cold replay가 더 싼 경우 cache를 끄는 적응형 경로다. 새 cache 설계 전에 동일 frozen fixture에서 `day_replay`, hit, probe CPU와 결과 동등성을 계측한다. 개선 입증 전에는 기존 안전 경로를 유지한다.
- cache/재생 경로가 유효하면 날짜·episode·source hash 단위로 한 번 계산한 순수 결과만 재사용한다. episode state, 시간 경계, terminal·cost·seed가 다르면 분리 계산한다.
- 검증 기준은 episode별 disposition, outcome/terminal, 비용, 후보·정책 출력과 최종 validator receipt의 동일성이다. invalid source report는 성공 cache로 재사용하지 않는다.

### P4 — Stage 자원 배치와 재시도

- 9/22에 배포된 독립 stage dispatch, source 대기 시 compute slot 비점유, 최대 두 child compute slot, stage lock 및 checkpoint 재개를 기준선으로 삼는다.
- widget full grid와 main replay 등 CPU·메모리 집약 단계의 동시 실행이 자연 resource samples에서 반복 압박을 만드는 경우, 기존 scheduler/admission owner 안에서 실행 순서 또는 slot admission만 조정한다. 새 timer·cron·worker·무제한 병렬화는 추가하지 않는다.
- 재시도는 실패/deferred stage와 hash가 바뀐 하류 stage에만 적용한다. 성공 receipt는 현재 입력·코드·prerequisite 검증 후 재사용하고, 같은 실패 입력을 무한 반복하지 않는다. immutable release 간 재사용은 관리 release 안의 동일 stage 코드 hash와 artifact·input·prerequisite hash가 모두 일치할 때만 허용한다.
- market/source validation 실패는 해당 owner에 귀속하고, 무관한 성공 stage나 기존 유효 정책을 취소·삭제하지 않는다.

### P5 — Rising 최적화 유지

- 완료된 단일 source-prefix read, bounded compressed spool, append cutoff와 failure cleanup 계약을 그대로 유지한다.
- 새로운 full-day 측정은 별도 필요가 생기기 전까지 요구하지 않는다. 정상 receipt에서 메모리·I/O 또는 wall deadline 문제가 재발하면 단계별 측정으로 남은 bottleneck을 특정한 후 수정 범위를 다시 제안한다.

## 4. 리뷰와 검증 계획

구현 시 각 P단계는 `구현 → self review → 보완 → re-review → 대상 검증` 순서로 닫는다. 새 source file/module/service/test 파일은 기본적으로 만들지 않고 기존 owner와 테스트를 우선 사용한다.

필수 검증:

- 동일 frozen input old/new differential: row/census, exclusion reason, episode/attempt identity, 후보 전이, candidate economics, selected rank/policy hash 비교.
- 무효화 회귀: source append/replace/truncate, 날짜·코드·schema·비용·label·seed·calendar 변경, partial output, corrupted cache, 중단·재개, 동시 요청.
- 안전 경계 회귀: 기존 hard guard 및 machine ENTER_NOW 보존, null economics, cost/path exclusion denominator, stage owner·lock·checkpoint·publisher 일관성.
- 영향받은 기존 pytest와 import/compile, `git diff --check`. 문서/checklist 변경 시 링크·owner·authority 검토 및 print-only backlog parser.
- 처리량 지표는 engineering 진단이다. 동일 결과를 전제로 compute CPU 또는 compute wall의 20% 이상 감소를 목표로 측정하되, 미달을 이유로 입력·grid·holdout을 줄이지 않는다. 감소가 확인되지 않으면 “성능 개선 미입증”으로 기록하고 임의 목표 달성을 보고하지 않는다.

## 5. 게시·재개·롤백 경계

- 변경은 현재 검증된 source tree와 새 immutable release에서 수행한다. 기존 release를 수정하지 않고, 관련 없는 dirty workspace 변경을 포함하지 않는다.
- optional cache 오류는 miss 후 native 계산으로 돌아간다. 필수 source·cost·lineage·schema 오류는 해당 stage를 fail/deferred 처리하고 잘못된 산출물 publish를 막는다.
- 산출물은 기존 atomic publication과 stage writer를 사용한다. 정책 pointer, runtime env 및 실제 매매 프로세스는 이 성능 변경으로 변경하지 않는다.
- 성능 변경으로 결과 차이, 누락 cohort, stale receipt 또는 memory/resource safety regression이 생기면 직전 immutable release와 기존 full computation 경로로 되돌린다. 신규 산출물과 실패 receipt는 증거 보존 정책에 따라 유지한다.
- 배포 승인, stage 재실행, trading restart, 자연 PREOPEN 소비 및 경제성 확인은 각각 별도 authorization/acceptance owner에서 처리한다.

## 6. 완료 보고 형식

각 작업을 `판정 → 근거 → 다음 액션`으로 보고하고 다음을 별도 기재한다: 기존/신규 code hash, frozen source identity와 비교 가능 여부, 결과 동등성, row·candidate 분모, wall/CPU/RSS/swap, wait·retry 시간, cache hit/miss 및 사유, terminal/exit, 정책 disposition, runtime effect, 실제 PID 소비와 비용조정 결과 상태.

성능 개선은 코드·산출물 계약을 닫았다는 뜻이다. 자연 정책 선택·PID 소비·실제 체결·순손익을 대신하지 않는다.

### 2026-09-23 구현·리뷰 결과와 남은 자연 검증

- P0/P2/P4: 기존 stage runner가 Widget EOD 완료·정확한 날짜·양수 행수를 계산 슬롯 전에 확인하고 기존 worker가 재검사한다. stage 입력에는 EOD receipt hash를 묶었고 `source_wait_sec`, `resource_admission_wait_sec`를 분리 기록한다. 기존 timer, 두 child slot, 정책·grid·종목 모집단은 유지했다.
- P1: 9/22 machine terminal은 `completed`이고 최종 stage는 9/23 02:02 복구 실행으로 `succeeded`였다. 이 실행은 약 0.14초의 기존 결과 검증이므로 12,127 시도 전체의 신규 성능·동등성 측정으로 보고하지 않는다. 신규 고정 원천 전체 실행이 생길 때 기존 machine 결과/terminal/checkpoint를 비교한다.
- P2: signal research의 기존 bounded `ReplayContext`와 page cache를 확인했다. 추가 cache는 반복 CPU와 동등성 근거가 없어 만들지 않았다.
- P3: 9/22 episode 최종 stage와 publication receipt는 `succeeded`/`complete`이고 source·policy hash가 있다. 이전 validation 실패는 복구됐으므로 같은 원천을 다시 전수 계산하지 않는다. 기존 day replay의 적응형 fast-reference 경로도 유지한다.
- P5: Rising의 완료된 단일 읽기 경로는 변경하지 않았다.
- 다음 신규 원천에서 Widget EOD 대기 중 슬롯 비점유, 전체 census·policy 동등성, compute wall/child CPU/RSS와 source hash를 확인해야 성능 효과를 수용할 수 있다. 9/22 복구 결과는 이 자연 검증을 대신하지 않는다.

## 7. 관련 owner와 근거

- [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md): source quality, 비용 기반 성과, owner/authority, promotion 경계.
- [기존 장후 계산 최적화 계획](./postclose-computation-optimization-implementation-plan-2026-09-17.md): 공통 계측과 연구 계산 최적화의 기존 범위. 이 계획은 해당 구현을 중복하지 않는다.
- [Machine replay resource review](../audit-reports/2026-09-22-machine-replay-resource-review.md): 중단 원인, 수정 계약, 327개 대상 테스트와 bounded 동일결과 benchmark.
- [Rising missed I/O review](../audit-reports/2026-09-22-rising-missed-feedback-io-review.md): 단일 원천 읽기 수정, 결과 동등성, 실제 실행 receipt.
- [Postclose stage separation plan](./machine-postclose-runner-separation-implementation-plan-2026-09-22.md) 및 [review](../audit-reports/2026-09-22-postclose-stage-separation-review.md): 독립 stage, bounded concurrency, 실패 재개와 기존 release 범위.
- [Widget postclose performance/source plan](./widget-postclose-performance-and-source-closure-implementation-plan-2026-09-16.md): widget 기존 producer, cache/source contract와 consumer 검증 owner.
- 실행 가능한 후속 owner는 당일 checklist에서 관리한다. 본 계획만으로 provider 호출, 정책 선정·적용, 배포·재기동, 주문 또는 장후 재실행을 시작하지 않는다.
