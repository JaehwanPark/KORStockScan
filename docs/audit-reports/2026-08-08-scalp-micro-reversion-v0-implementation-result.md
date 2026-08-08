# Scalp Micro-Reversion V0/P0.6 구현결과 감리 보고서

- 작성일: `2026-08-08 KST`
- 검증 기간: `2026-08-03`~`2026-08-07` 5거래일
- canonical status: `v0_aggregate_taxable_equity_gate_failed_subcohort_execution_unresolved`
- report schema: `scalp_micro_reversion_v0_report_v4`
- implementation base commit: `a44875c339971a3f6ee6acb156282cc2e01ce498`
- working tree at generation: `dirty=true`; 실제 변경 식별은 source manifest hash가 소유
- observer producer/runtime 연결: 없음 (`clean deployment baseline` 대기)
- trading/sim/broker 반영: 없음

## 1. 최종 판정

감리 재검토에서 승인한 `Producer Observation Adapter + Pre-event Ring Buffer + Parent-wave Path Coalescing + Runtime Observer Metrics + P2 Replay Contract/Synthetic Test Skeleton`을 관찰·연구 전용으로 구현했다. 기존 스캘핑 producer와 주문·AI·ADM/LDM·threshold consumer에는 연결하지 않았다. producer hook을 보류한 이유는 현재 working tree가 `dirty=true`여서 감리의 clean integration commit/manifest 선행조건을 아직 충족하지 못했기 때문이다.

일반 과세주권 전체 이벤트 fixed-horizon 전략은 계속 기각한다. 최고 관측 gross `14.450139bp`가 법정 매도비용 하한 `20bp`보다 `5.549861bp` 부족하다. 반면 세부 cohort와 path-based 정책은 아직 연속 경로가 없으므로 판정하지 않았다.

```text
v0_source_only_implementation=approved
aggregate_fixed_horizon_strategy_rejected=true
subcohort_opportunity_discovery=open
positive_ev_hypothesis_supported=false
execution_data_gate=false
candidate_gate_passed=false
applied_to_sim=false
real_runtime_reflected=false
actual_order_submitted=false
broker_order_forbidden=true
trading_runtime_effect=false
```

P2 entry×exit의 계약·synthetic engine까지만 구현했고 실제 data replay는 `blocked_no_forward_continuous_path`다. P3 sim assumed-fill도 불승인 상태다.

```text
p2_engine_contract_implemented=true
p2_synthetic_and_golden_tests=true
p2_real_data_discovery_run=false
p2_policy_selection_authority=false
p2_runtime_effect=false
observer_adapter_implemented=true
observer_producer_connected=false
observer_runtime_loaded=false
observation_capture_active=false
trading_decision_effect=false
```

## 2. 감리 권고 반영표

| 권고 | 구현 결과 | 현재 권한 |
|---|---|---|
| P0.4 재현성 | V4 report와 input/source/config/report/test hash sidecar 추가 | audit-only |
| 과거 상태 단일화 | 체크리스트의 구 판정을 `superseded`, 자동소비 불가로 표시 | document-only |
| raw/event-joined coverage 분리 | BBO·micro raw 후보와 event join 분모를 별도 필드로 보고 | report-only |
| P0.5A symbol master | effective date, source, verified time, conflict fail-close 구현 | source-only |
| 관찰/경제성 gate 분리 | tax unknown도 관찰 가능, 경제성 headline·sim은 차단 | source-only |
| CORE/DISCOVERY registry | propensity를 관찰 허가권이 아닌 자원 우선순위로 제한 | source-only |
| P0.5B path schema | event baseline/검출/180초 경로 필드와 sequence 계약 구현 | source-only |
| hot-path 비차단 | bounded queue, `put_nowait`, 전용 batch/fsync writer, drop/degraded metric | source-only |
| P0.5C execution provenance | submission/origin/fill/evidence를 직교 분리하고 exact pairing 검증 | observation-only |
| P1A multi-horizon | 1/3/5/10/20초 detector, parent wave와 state re-arm | source-only |
| confirmation gate | policy freeze, clustered LCB, tail·집중도·FDR, unresolved bounds | research-only |
| thin observation adapter | 수동관리 선검사, immutable envelope, fail-isolated `put_nowait`, 기본 OFF flag | source-only/not connected |
| pre-event ring | symbol+venue+session별 30초 bounded ring, gap/duplicate/out-of-order 계수 | source-only |
| parent-wave coalescing | parent wave당 segment 1개, 여러 shock event reference, pre/active/post phase | source-only |
| storage/metric guard | partition path, open segment/file/disk watermark, self-disable 계약과 producer/queue/writer/path metric | source-only |
| P2-A replay skeleton | frozen policy, exchange/local/sequence watermark, touch upper/trade-through lower, partial fill, entry/holding TTL, ambiguity, runner 계약 | research-only/no real data run |

## 3. 핵심 안전계약

### 3.1 수동관리 제외

replay·registry·path journal·execution journal의 진입 전에 수동관리 제외 확인을 요구한다. 이번 5일 replay는 제외 row `130,303`, event leak `0`이다. 제외종목에 대해 전략 feature, path row, 실행 증거 또는 주문 행동을 만들지 않는다.

### 3.2 verified symbol master

필수 provenance는 `symbol`, `listing_market`, `instrument_type`, 파생 `instrument_tax_class`, `effective_from/to`, `metadata_source`, `source_reference`, `verified_at`, `conflict_status`다. 실행 venue를 listing market으로 간주하거나 숫자 market code를 추정하지 않는다. unknown/conflict는 관찰은 가능하지만 exact 경제성 gate에서 fail closed한다.

현재 실제 verified master artifact는 공급되지 않았으므로 event tax coverage는 여전히 `0/2,399`다. 이것은 구현 실패가 아니라 원천 blocker이며 임의 metadata로 채우지 않았다.

### 3.3 market-path journal

`MarketPathPoint` V2는 exchange/local timestamp, source sequence, trade/BBO/depth/quote age, parent wave, path phase, detector와 capture provenance를 검증한다. `ObservationSink`가 producer에 노출하는 유일한 downstream 동작은 bounded `put_nowait`이다. adapter는 수동관리 제외를 envelope 생성보다 먼저 확인하고 모든 예외를 격리한다. JSON/file/fsync/detector/replay/statistics/symbol-master/broker/LLM dependency는 adapter에 없다.

30초 bounded ring은 event 이전 경로를 보존한다. 최초 horizon event만 pre-event buffer를 flush하고 같은 `parent_wave_id`의 후속 horizon event는 동일 `path_segment_id` reference만 추가한다. segment lookup은 symbol/venue/session으로 격리되며 20초 active와 이후 180초까지 post coverage를 분리한다.

writer는 batch append/fsync, cross-batch monotonic guard, queue high-water/full/drop, write/flush/fsync latency, bytes/disk remaining, critical disk self-disable를 제공한다. 종료는 queue shutdown marker 삽입에 의존하지 않는 독립 stop event로 닫고, `writer_alive`와 `last_writer_error_type`을 남긴다. `PathStoragePolicy`는 daily/venue/session partition, maximum partition bytes/open segments, low/critical watermark, compression/retention 계약을 고정한다. compression/retention 실제 scheduler와 환경별 watermark 확정은 canary 배포 작업에 남아 있다.

producer 연결과 실제 path row는 아직 `0`이다. 따라서 장중 latency, bytes/day, collector coverage와 경제성을 판정하지 않는다. 현재 구현 metric은 callback/enqueue p50/p95/p99, queue, writer, sequence, exchange/local·quote age, disk, last sequence, pre/active/post 분모를 노출하지만 실제 canary 값은 없다.

### 3.4 P2-A source-only replay

P2 엔진은 explicit in-memory path만 받으며 data discovery CLI와 ranking consumer가 없다. decision exchange timestamp, local receive timestamp, source sequence watermark 이후의 점만 사용한다. passive entry는 `UPPER_TOUCH`와 보수적인 `LOWER_TRADE_THROUGH`를 분리하고, lower bound는 첫 trade-through 가용수량만 partial fill로 인정한다. entry TTL과 최초 fill 이후 holding TTL은 분리된다.

동일 path point가 TP와 STOP을 모두 포함하면 `STOP_FIRST` 또는 `MARK_AMBIGUOUS`만 허용한다. `PARTIAL_TP_RUNNER`는 TP ratio, runner TTL, trailing bps, exit trigger를 policy 생성 시 고정하지 않으면 거부한다. 미체결은 `net_return_per_detected_signal_bps=0`으로 남겨 전체 탐지 신호 분모에서 사라지지 않는다. 아직 실제 path run, policy ranking, discovery selection, confirmation, sim 연결은 모두 false다.

### 3.5 execution journal V2

다음 상태를 별도 축으로 유지한다.

```text
submission_state = NOT_SUBMITTED | SUBMITTED | UNKNOWN
order_origin = NONE | COUNTERFACTUAL | EXTERNAL_OTHER_STRATEGY | MICRO_REVERSION
fill_state = NOT_APPLICABLE | TOUCH_ONLY | TRADE_THROUGH | NO_FILL |
             PARTIAL_FILL | FULL_FILL | RECEIPT_INCOMPLETE
execution_evidence_eligible = true | false
```

외부 전략 주문은 micro-reversion evidence가 될 수 없다. `NO_FILL`은 submit과 terminal receipt를 요구하며, full fill은 first-fill과 FILLED terminal receipt를 요구한다. micro-reversion origin은 제출 여부와 무관하게 decision ID와 quote snapshot pairing을 요구한다.

## 4. V4 replay 결과

| 항목 | 결과 | 해석 |
|---|---:|---|
| raw / accepted rows | `2,644,506 / 1,267,733` | clean-baseline·세션·제외 적용 |
| deduplicated observations | `469,231` | coarse path inventory |
| shock events / symbols | `2,399 / 640` | gross pattern 식별 |
| fully mature 600초 | `99 (4.1267%)` | coverage gate 실패 |
| raw BBO candidate rows | `1,998` | raw accepted-row 분모 |
| event-joined BBO context | `0` | execution replay 불가 |
| raw micro / complete micro candidate | `0 / 0` | micro 경로 없음 |
| event-joined micro context | `0` | micro 경제성 불가 |
| verified tax events | `0 / 2,399` | exact tax gate 차단 |
| 최고 fixed-horizon gross | `60초, 14.450139bp` | 인샘플 설명값만 허용 |
| 일반 과세주권 statutory margin | `-5.549861bp` | aggregate 전략 기각 |
| legacy 300초 complete-case EV @23bp | `-0.151012%` | headline 권한 없음 |
| candidate/sim/runtime | `false / false / false` | 승격 없음 |

V4는 horizon마다 `all_detected_signal_count`, `resolved_outcome_count`, `unresolved_outcome_count`, complete-case EV와 all-signal zero-unresolved EV를 분리한다. optimistic/conservative fill bound와 coverage-adjusted LCB는 forward execution evidence가 없어 `null`이다. complete-case 양수만으로 positive EV를 선언하지 않는다.

## 5. 구현 경계와 다음 owner

이번 변경으로 열린 것은 source-only schema와 deterministic 연구 도구뿐이다. 다음 owner는 아래 순서다.

1. 변경범위를 분리한 clean integration commit을 만들고 source/test/deployment hash manifest를 재생성한다.
2. 공식·검증된 symbol master 원천 artifact를 공급하고 conflict/coverage report를 만든다.
3. 구현결과보고서와 clean manifest를 감리인에게 제출해 producer 연결 전 재검토를 받는다.
4. 감리 재승인 후 기존 구독 범위를 늘리지 않고 market-data producer에 최소 `ObservationSink` adapter만 연결한다.
5. feature flag 기본 OFF 상태로 canary를 배포한 뒤 observer만 켜고 producer latency 악화 없음, 정상장 drop 0을 확인한다.
6. 최소 5거래일, 성숙 event 200건, 필수 path field coverage 90%, gap/restart/recovery와 pre/active/post coverage로 Gate B를 닫는다.
7. Gate B 이후 P2 실제 discovery를 실행하고 policy/cohort/cost를 freeze한다. 별도 confirmation에서 all-signal clustered LCB·tail·집중도·FDR을 통과하기 전에는 sim을 열지 않는다.

다음 단계에서도 주문 제출, 취소, 매도, threshold/provider/bot/quantity/cap 변경은 금지한다.

## 6. 재현성 manifest

아래 sidecar는 V4 replay 생성시점의 manifest다. 이번 P0.6 source-only 추가분은 working tree가 clean integration commit이 된 뒤 source/test/deployment manifest를 별도로 재생성한다. 따라서 아래 source hash를 producer 배포 hash로 사용하지 않는다.

| 항목 | SHA-256 / 값 |
|---|---|
| implementation base commit | `a44875c339971a3f6ee6acb156282cc2e01ce498` |
| input manifest | `863d4165d9bfafa9469b04f5db9207370e30a45fb3bd14665d06292bdd4aabf0` |
| source manifest | `5f73fd099e4fadd4056a501ca103b4236682a2fb092678045e146bcff5507b29` |
| policy config | `2f70f0c569ae2ac79d0782a4cf4460ab7893d00533bbcc0f8d90142f5e5a4ab3` |
| test selection | `0f6916581f1e452944311e6d7e039884a3fc67a15ead6acfd6b64f8391a660d3` |
| report JSON | `7a5e4a4ffd3f7c00a9570e4a4c12b171acdc0bda7d70cad44845ca03627f920e` |
| report Markdown | `5bc6331346fe9aa70306e01dcccd60599c195858a78e57c4d375010bc423176d` |
| sidecar file | `7f322b07d78f1e0182c3e458d09ea40560b847157b04b562cc77289303cf4f3c` |

산출물:

- `data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.json`
- `data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.md`
- `data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.reproducibility.json`

## 7. 코드리뷰 및 검증

- targeted pytest: `69 passed`
- Ruff: 통과
- Black: 통과
- compileall: 통과
- thin adapter import graph/금지 dependency scan: 통과
- checklist parser (`count=30`): 통과
- `git diff --check`: 통과
- 5거래일 V4 replay: 통과
- canonical status invariant: 통과
- 수동관리 event leak: `0`

현재 코드리뷰 판정은 승인된 관찰/P2 synthetic 구현범위 내부다. producer 연결은 clean deployment baseline 전 보류, P2 실제 discovery는 Gate B 전 보류, policy selection/sim/live는 계속 불승인이다.
