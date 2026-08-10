# Scalp Micro-Reversion V1 Feasibility And Implementation Plan

- 작성일: `2026-08-08 KST`
- 제안 namespace: `scalp_micro_reversion`
- 상태: `v0_aggregate_taxable_equity_gate_failed_subcohort_execution_unresolved / no_sim_or_runtime_promotion`
- 실주문 권한: 없음
- LLM 의사결정 권한: 없음

## 1. 판정

“짧은 매도 충격 뒤 빠른 가격 복귀를 매수하고, 복귀·과열 구간에서 청산한다”는 가설은 기존 데이터로 1차 전략 가능성을 검증할 수 있다. 다만 현재 데이터는 선택된 판단 시점의 관측이 많고 연속적인 sub-second 체결·L2 호가·queue position·주문 ACK/체결 지연이 부족하므로, 기존 자료만으로 초단타 실주문 성과를 확정할 수는 없다.

따라서 진행 순서는 다음으로 제한한다.

1. 기존 clean-baseline 데이터로 coverage-aware V0 replay를 실행한다.
2. 거래세션·최소 source 계약·detector를 통과한 모든 종목은 세율 미확인이어도 V1 forward observation에 포함한다.
3. exact tax class·all-in cost·OOS clustered EV LCB·tail/concentration gate를 통과한 후보만 경제성 headline 대상으로 좁힌다.
4. 충분한 연속 경로와 forward 표본에서 비용 차감 EV와 tail loss를 검증한 뒤에만 sim assumed-fill을 별도 검토한다.
5. 실주문은 별도 사용자 승인, 별도 runtime family, 별도 rollback 계약 전에는 열지 않는다.

삭제된 `panic_buying` 코드, 리포트, artifact, euphoria stage 또는 승인 family는 입력·호환 경로·이름 재사용 대상으로 삼지 않는다.

### 1.1 구현 상태 (`2026-08-08`)

다음 source-only 범위가 `src/engine/scalping/micro_reversion/`에 구현됐다.

- `contracts.py`: observation/event/outcome/metric authority 계약
- `detector.py`: robust median/MAD, hysteresis, cooldown 기반 shock detector
- `outcome_labeler.py`: 15/30/60/120/180/300/600초 future-path label
- `replay.py`, `report.py`: 전체 관측 universe의 clean-baseline replay와 JSON/Markdown report
- `tax.py`: 날짜·상장시장·상품유형별 법정 매도세율 계약
- `symbol_master.py`: effective-date·conflict를 포함한 verified symbol master 계약
- `observation_gate.py`, `registry.py`: 넓은 관찰 gate와 좁은 경제성 gate, CORE/DISCOVERY 예산 분리
- `path_journal.py`: bounded non-blocking queue와 batch/fsync를 쓰는 연속 market-path 저널 계약
- `observation_adapter.py`: package eager import 없는 최소 sink, immutable envelope, 기본 OFF flag와 runtime metric
- `path_capture.py`: 30초 pre-event ring, parent-wave 단일 segment/reference, pre/active/post coverage
- `p2_replay.py`: source-only frozen policy, non-lookahead watermark, fill bound·partial fill·TTL·ambiguity synthetic engine
- `execution_journal.py`: 제출상태·주문원천·체결상태·증거자격을 분리한 receipt 계약
- `multi_horizon.py`: 1/3/5/10/20초 탐지와 parent-wave/state re-arm 계약
- `research_gate.py`: discovery/confirmation freeze, clustered LCB, tail·집중도·FDR 계약
- `reproducibility.py`: input/source/config/report/test hash sidecar manifest

구현은 명시적으로 인스턴스화하기 전에는 아무 동작도 하지 않는다. 기존 스캘핑 엔진, 주문, AI, ADM/LDM, threshold-cycle consumer에는 연결되지 않았다. `ObservationSink`와 thin adapter, pre-event ring, parent-wave path coalescer, runtime metric, P2-A source-only synthetic engine 계약은 구현했지만 실제 producer hook과 실제 경로 P2 실행은 하지 않았다. 세 feature flag의 기본값은 모두 `false`다. execution journal은 외부에서 관측된 실제 주문 여부를 보존할 수 있지만 journal 자체는 broker action authority가 없다.

### 1.2 V0 실행 판정 (`2026-08-08`)

정식 V4 replay는 당시 수동관리 제외 계약을 적용하여 `v0_aggregate_taxable_equity_gate_failed_subcohort_execution_unresolved`로 종료했다. 아래 수치는 역사적 감사 증거이며, `2026-08-10` 이후 전체 관측 universe 계약의 재평가 기준값으로 직접 사용하지 않는다. shock pattern과 15~180초 gross reversion edge는 식별됐지만 일반 과세주권 법정비용 하한 `20bp`가 최고 fixed-horizon gross `14.450139bp`보다 높아 전체 이벤트 fixed-horizon 경제성 gate는 실패했다. 다만 tax class와 execution 자료가 부족하므로 세부 cohort와 path-based 정책 탐색은 계속 연다.

| 항목 | 결과 | 판정 |
|---|---:|---|
| raw rows / deduplicated observations | `2,644,506 / 469,231` | 5거래일 입력 확인 |
| shock events / symbols | `2,399 / 640` | 패턴은 식별됨 |
| 당시 manual-control 제외 rows / event leak | `130,303 / 0` | 폐기된 구 계약의 역사적 결과 |
| 300초 mature sample | `292` | 후보 floor `1,000` 미달 |
| 10분 fully mature event | `99 (4.13%)` | coverage floor `90%` 미달 |
| 15~180초 gross EV | `+0.121910% ~ +0.144501%` | gross edge 식별 |
| 최고 관측 fixed horizon | `60초, +0.144501%` | 인샘플 설명값, 선택 권한 없음 |
| 60초 손익분기 all-in 비용 | `14.450139bps` | 실행비용 분해 필요 |
| 일반 과세주권 법정비용 / margin | `20bps / -5.549861bps` | aggregate gate 실패 |
| event tax-class coverage | `0 / 2,399` | exact gate 차단 |
| common through-60s 최고 | `30초, 15.188879bps` | 60초 selection authority 없음 |
| 60초 EV @ 10bps / 15bps / 23bps | `+0.044501% / -0.005499% / -0.085499%` | 비용 민감 |
| 600초 gross EV | `-0.061444%` | 장기 보유 edge 없음 |

따라서 전체 이벤트 fixed-horizon 정책은 기각하지만 전략군 전체는 기각하지 않는다. forward collector와 P2-A 계약은 구현했으나 producer에 연결하거나 실제 data replay를 실행하지 않았고, sim assumed-fill·실시간 registry·실주문 adapter 승격은 열지 않는다. source-only clean integration commit/manifest는 `e7051399` 기준으로 완료했다. 다음 실행 owner는 verified symbol master 원천 적재와 감리 재승인 후, 기존 구독 범위 안에서 non-blocking producer canary를 별도 change set으로 연결하는 것이다. Phase B data-readiness가 닫힌 뒤에만 P2 실제 discovery replay를 수행한다. `0bps`는 모든 마찰을 제거한 counterfactual이며 일반 과세주권 live-relevant 비용으로 해석하지 않는다.

산출물:

- `data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.json`
- `data/report/scalp_micro_reversion_v0/scalp_micro_reversion_v0_2026-08-03_to_2026-08-07.md`
- `docs/audit-reports/2026-08-08-scalp-micro-reversion-v0-implementation-result.md`

## 2. 근거 데이터

의사결정 입력은 `2026-06-05T00:00:00+09:00` 이후 clean-baseline 자료로 제한한다.

최근 원천자료의 1차 inventory는 다음과 같다.

| 범위 | 관측값 | 해석 |
|---|---:|---|
| pipeline events `2026-08-03`~`2026-08-07` | `2,644,506` rows | 이벤트/가격 경로 가설 탐색 가능 |
| 당시 수동관리 제외 후 rows | `2,514,203` | 폐기된 구 계약의 역사적 inventory |
| 당시 non-manual `current_price_observed` | `2,440,443` occurrences | 폐기된 구 계약, 중복·비정규장 관측 포함 |
| `2026-08-07` pipeline events | `471,544` rows | 단일 거래일 source-quality audit 가능 |
| 5일 정규장 deduplicated symbol-seconds | `468,245` | coarse horizon label 재구성 가능 |
| 완전한 best bid + best ask rows | `381` | 연속 호가 replay에는 부족 |
| orderbook micro capture rows | `783` | 선택 시점 micro feature 검토 가능 |
| microstructure report rows | `34,682` | source-quality 분리 분석 가능 |
| microstructure `ok` | `600` | 일부 탐색 표본 |
| missing/unusable | `34,082` | 전체-universe 연속 replay로 해석 금지 |
| favorable unique entry opportunities | `11` | 초기 신호, 표본 부족 |
| exact outcome joins | `3` | 실행 승인 근거로 부족 |
| source-quality pass outcomes | `2` | 실행 승인 근거로 부족 |

근거 artifact:

- `data/pipeline_events/pipeline_events_2026-08-03.jsonl.gz` ~ `2026-08-07.jsonl.gz`
- `data/report/microstructure_reaction_context/microstructure_reaction_context_2026-08-07.json`
- `data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-07.json`

`2026-08-07` source-quality audit는 선언된 현재 계약에 대해 `tuning_input_allowed=true`지만, 이것은 micro-reversion에 필요한 연속 호가 계약이 존재한다는 뜻이 아니다. 신규 전략은 별도의 source-quality 계약과 coverage 분모를 선언해야 한다.

### 2.1 탐색적 shock-reversion 사전 검증

V0 구현 가치만 판단하기 위해 다음의 단순하고 고정된 탐색 규칙을 적용했다.

```text
기간: 2026-08-03 ~ 2026-08-07
세션: 09:00 ~ 15:30
당시 수동관리 제외(폐기된 구 계약): 950160, 005930, 034020, 042660
가격: current_price_observed를 symbol-second로 deduplicate
shock: 약 5초 수익률 <= -30bps
event cooldown: 60초
성숙 조건: 15/30/60초 가격이 각 horizon +6초 안에 존재
```

결과:

| 항목 | 탐색 결과 |
|---|---:|
| 성숙 event | `1,427` |
| event 보유 종목 | `402` |
| median shock | `-45.30bps` |
| median MFE 15/30/60초 | `17.01 / 22.57 / 32.47bps` |
| 60초 full reclaim | `41.91%` |
| 60초 half reclaim | `61.95%` |
| 60초 additional half-shock continuation | `29.92%` |
| 60초 MFE `>=23bps` | `57.95%` |

`half reclaim > continuation`이고 5개 거래일 모두 event가 발생했으므로 평균회귀 가설을 정식 V0 replay에서 검증할 가치는 있다. 그러나 이 결과는 매수·청산 규칙, spread, fill, slippage를 적용한 EV가 아니며 수익성 판정으로 사용할 수 없다.

특히 median MAE가 모든 horizon에서 `0bps`로 나온 것은 하락 위험이 없다는 뜻이 아니다. 현재 pipeline의 선택 관측과 중복 제거 시계열이 event 이후 저가 경로를 충분히 포착하지 못했을 가능성이 큰 source-quality 경고다. 따라서 기존 데이터의 MFE는 가설 탐색에 사용하되, MAE·tail loss·체결 가능성은 V1 forward journal 전에는 승인 근거로 사용하지 않는다.

## 3. V0 백테스트가 답할 수 있는 질문

기존 데이터는 다음 질문에 사용할 수 있다.

- 짧은 하락 pulse 후보가 얼마나 자주 발생하는가?
- 15/30/60초 가격 경로에서 recovery-first와 continuation-first 중 어느 쪽이 우세한가?
- 이벤트 이후 MFE/MAE와 p90/p95 tail MAE는 어느 정도인가?
- 비용 차감 회복폭이 양수인 종목·세션·시간 bucket이 존재하는가?
- 관측 가능한 경우 aggressive-flow, tick acceleration, spread, OFI/QI가 회복 확률을 분리하는가?
- 동일 종목에서도 `KRX/NXT`, 장초/장중/장후 결과가 달라지는가?

다음 질문에는 답할 수 없다.

- 250ms/1s/2s의 완전한 경로와 L2 queue 변화
- 과거 bid replenishment/depletion의 연속 sequence
- 목표 수량의 실제 queue position과 fill probability
- receive -> decision -> submit -> broker ACK -> fill latency
- 실거래 슬리피지와 부분체결 품질

따라서 V0 결과에는 반드시 coverage tier를 붙인다.

| tier | 필수 관측 | 허용 용도 |
|---|---|---|
| `price_path` | event anchor + horizon price | 방향/회복 가설 탐색 |
| `bbo_context` | price path + fresh bid/ask | 비용·spread 조건부 탐색 |
| `micro_context` | BBO + usable aggressor/OFI/QI | micro feature 후보 비교 |
| `execution_grade` | 연속 L2 + order/fill latency | 기존 데이터에서는 생성 금지 |

상위 tier 결손을 0 또는 정상값으로 대체하지 않는다. tier 사이의 표본을 합쳐 하나의 headline EV로 보고하지 않는다.

## 4. 키움 API 보완 범위

공식 upstream 확인:

- repository revision: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- inspected path: `kiwoom_docs/차트.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`
- retrieved at: `2026-08-08T15:26:08+09:00`
- API: `ka10079`, `POST /api/dostk/chart`

`ka10079`는 종목코드와 틱 범위 기반으로 체결시간, 현재가, 거래량, OHLC 및 수정주가 metadata를 제공한다. 다음 용도로만 사용한다.

- 기존 pipeline의 특정 event timestamp 전후 가격·거래량 공백 보완
- non-manual symbol의 coarse tick-path 확인
- continuation header를 보존한 read-only 수집

다음 정보는 복원할 수 없으므로 API 보완값으로 위조하지 않는다.

- 과거 L2 호가 depth와 queue 변화
- aggressor side의 완전한 과거 sequence
- 로컬 수신 timestamp
- 주문 ACK/체결 latency

API adapter는 주문·계좌 endpoint를 import하거나 호출하지 않는다. cached token이 없으면 `source_unavailable`로 종료하며 전략 수집을 위해 토큰을 새로 발급·갱신하지 않는다.

## 5. 수동관리 제외 책임 경계

micro-reversion의 수집·탐지·경로 저장·replay·P2·경제성 평가는 수동관리 제외목록을 조회하거나 종목을 다르게 취급하지 않는다. 수동관리 여부는 시장 신호의 존재나 전략 가설의 평가 자격과 무관하므로 observation, registry, event, journal, report schema에도 해당 필드를 두지 않는다.

수동관리 제외의 유일한 책임 경계는 실제 주문 직전의 기존 공통 매매 guard다. 향후 micro-reversion이 real-order adapter와 연결되더라도 주문 계층이 최신 제외목록을 다시 평가하여 제출을 차단해야 한다. 이 계약은 micro-reversion 내부 표본을 삭제하거나 평가를 왜곡하는 근거로 사용하지 않는다. 현재 V0/V1/P2는 broker authority 자체가 없으므로 실제 주문 경로는 열려 있지 않다.

## 6. Loose-Coupled V1 구조

```text
Broad Observation Universe
              |
              +--> CORE_REGISTRY (evidence-priority)
              |
              +--> DISCOVERY_REGISTRY (bounded rotation)
              |
              v
Multi-horizon Detector (deterministic, no LLM)
              |
              v
Event Path Capture + propensity re-estimation
              |
              +--> diagnostic observation envelope only
```

propensity는 관찰 허가권이 아니라 자원 배분 우선순위만 소유한다. tax class `UNKNOWN`은 DISCOVERY 관찰에는 남길 수 있지만 경제성 headline·sim 승격에는 사용할 수 없다. V1은 기존 스캘핑 엔진의 주문 함수, AI 판단기, ADM/LDM runtime policy를 호출하지 않는다. 향후 연결도 기존 market-data producer에서 immutable envelope을 받는 얇은 adapter와 bounded non-blocking queue까지만 허용한다.

권장 source ownership:

```text
src/engine/scalping/micro_reversion/
  contracts.py
  detector.py
  multi_horizon.py
  registry.py
  observation_gate.py
  symbol_master.py
  path_journal.py
  observation_adapter.py
  path_capture.py
  p2_replay.py
  execution_journal.py
  research_gate.py
  replay.py
  report.py
  reproducibility.py
```

- live/scalping 역할이므로 `src/engine/scalping` 하위가 owner다.
- `src/engine` root에는 신규 module을 만들지 않는다.
- 설정은 독립 policy artifact로 두고 기존 BUY score/TP/stop/provider env를 재사용하지 않는다.
- thin integration adapter 외에는 `sniper_state_handlers.py`에 전략 상태를 넣지 않는다.

## 7. 결정론적 신호 계약

초기 detector는 고정 가중치 최적화보다 robust feature와 hysteresis를 사용한다.

```text
downside_return_robust_z
downside_acceleration_robust_z
aggressive_sell_robust_z (available tier only)
micro_vwap_deviation_robust_z
spread/depth source-quality gate
```

상태 전이는 다음으로 제한한다.

```text
IDLE
 -> SHOCK_CANDIDATE
 -> SHOCK_ACTIVE
 -> REVERSION_CANDIDATE
 -> REVERSION_CONFIRMED | CONTINUATION_BLOCKED
 -> RELIEF_EXIT_CANDIDATE
 -> CLOSED
 -> COOLDOWN
```

trigger와 release threshold를 분리하고, 하나의 하락 파동이 여러 event로 중복 집계되지 않도록 `symbol + venue + session + event_id`를 사용한다. V0에서 threshold를 결과에 맞춰 임의 고정하지 않고 train window quantile로 만들고 다음 거래일 walk-forward window에 적용한다.

### 7.1 체결확인형 resting take-profit 변경안

비용민감도 검증 후 `fill_confirmed_resting_take_profit_v1`은 exit 후보 중 하나로 유지한다. 현재는 `design_only_not_implemented`이며 주문 권한이 없다. 단일 TP를 확정하지 않고 `SINGLE_TP`, `PARTIAL_TP_RUNNER`, `TP_LADDER`를 entry 정책과 공동 replay한다.

```text
BUY_SUBMITTED
 -> BUY_PARTIAL_FILLED | BUY_FILLED
 -> TARGET_PRICE_RESOLVED
 -> TAKE_PROFIT_SUBMITTED
    |-> TAKE_PROFIT_PARTIAL_FILLED -> TAKE_PROFIT_SUBMITTED (remaining qty)
    |-> TAKE_PROFIT_FILLED -> CLOSED
    |-> TTL_EXPIRED -> TTL_CANCEL_REQUESTED
                      -> TTL_CANCEL_CONFIRMED
                      -> DEFENSIVE_EXIT_ELIGIBLE
                      -> CLOSED
```

- broker 주문번호 반환을 체결로 보지 않고 confirmed fill receipt만 수량 권한으로 사용한다.
- `confirmed buy fill - sell-covered qty - open sell reserved qty`의 양수 delta만 지정가 매도한다.
- TP1·TP2·runner allocation 합계는 confirmed sellable qty를 넘지 않는다.
- 목표가는 실제 fill VWAP에 검증된 all-in 비용, 최소 순이익, uncertainty buffer를 더하고 tick ceiling한다.
- 보호손절은 TP보다 우선하지만 기존 TP 취소확인과 late-fill reconciliation 전에는 같은 수량을 중복 매도하지 않는다.
- 공식 주문 계약상 atomic OCO를 가정하지 않는다.
- 과거 touch replay와 forward full/partial/no-fill receipt가 닫히기 전에는 sim/live adapter를 열지 않는다.

## 8. 연속 경로·실행 저널 계약

연속 market-path는 event baseline부터 event 이후 180초 또는 정책 종료까지 다음을 append-only로 보존한다.

```text
event_id, path_segment_id, symbol, venue
exchange_timestamp, local_receive_timestamp, source_sequence
trade_price, trade_qty, best_bid, best_ask, bid_depth, ask_depth
quote_age_ms, aggressor_side, detector_version
capture_started_at, event_detected_at, capture_ended_at
dropped_message_count
actual_order_submitted=false
broker_order_forbidden=true
decision_authority=continuous_market_path_observation_only
```

producer dependency는 `producer → ObservationSink → thin adapter → bounded queue`로만 허용한다. hot path는 최소 envelope 검증, `put_nowait`, metric increment만 수행하고 전용 writer가 batch append/flush/fsync를 담당한다. JSON/file/fsync/detector/replay/statistics/symbol-master I/O/broker/LLM과 수동관리 제외목록 조회는 hot path에서 금지한다. adapter 예외는 producer에 전파하지 않는다.

active series별 20~30초 bounded ring은 shock 탐지와 capture 시작시각 계산에만 유지한다. 저장은 accepted producer series sequence당 `market_stream` row를 정확히 한 번 기록하고, shock 발생 시 `symbol/venue/session/sequence_epoch + capture_started_at/event_at/capture_ended_at` window reference만 append한다. source sequence와 local receive time이 단조이고 FID `20` exchange time만 최대 1초 역행한 row는 canonical stream V3에 raw provenance로 보존하되 `path_consumer_eligible=false`로 detector/path/P2에서 격리한다. 1초 초과 역행, source sequence 역행, local receive time 역행은 canary hard stop을 유지하며 exchange time을 재정렬·보간·clamp하지 않는다. 같은 tick을 event별·segment별로 복제하지 않고, 동일 `parent_wave_id`의 1/3/5/10/20초 event는 하나의 `path_segment_id`를 공유하며 이후 독립 impulse가 state re-arm을 통과한 경우에만 새 segment를 연다. P2는 eligible reference를 canonical stream에 join하여 필요한 pre/active/post window를 재구성한다.

저장 계약은 trade date/venue/session별 `market_stream.jsonl`, 512 MiB shard, 최대 8 shard, partition hard cap 4 GiB, 장중 6.5시간 projected cap 2 GiB, disk low/critical watermark, post-session compression, 14일 retention, storage-only self-disable를 선언한다. shard 상한 도달 시 `market_stream.part-NNNNNN.jsonl`로 회전하고 `market_stream.manifest.json`을 최초 shard·회전·정상 종료 시 atomic write한다. 종료 reconciliation은 manifest만 신뢰하지 않고 연속 shard를 직접 streaming scan하며 sequence 중복, shard gap, manifest 오류, projected/hard cap 위반을 canary stop으로 처리한다. `storage_maintenance` CLI는 기본 dry-run이며 `--apply`일 때만 현재 거래일을 제외한 closed date JSONL을 gzip roundtrip SHA-256 검증 후 압축하고 manifest를 `.gz` shard로 갱신하며, 14일 초과 partition만 제거한다. critical 상태에서는 observation storage만 degraded/self-disabled로 닫고 기존 producer/runtime은 계속한다. writer 종료는 독립 stop event로 queue를 drain하고 `writer_alive`와 마지막 오류유형을 보고한다.

필수 metric은 callback/enqueue p50/p95/p99, queue depth/high-water/full/drop, write/flush/fsync, source sequence gap/duplicate/out-of-order, bounded exchange-time regression quarantine/exceeded/max-ms, local-receive regression, exchange/local gap과 quote age, bytes/disk, writer recovery/last sequence, pre/active/post coverage다. observer가 실제로 적재될 때는 `observer_runtime_loaded`와 `observation_capture_active`를 별도로 보고하고, `trading_decision_effect`, order/broker/sim/threshold effect는 계속 false다.

execution receipt는 다음 네 축을 혼합하지 않는다.

```text
submission_state = NOT_SUBMITTED | SUBMITTED | UNKNOWN
order_origin = NONE | COUNTERFACTUAL | EXTERNAL_OTHER_STRATEGY | MICRO_REVERSION
fill_state = NOT_APPLICABLE | TOUCH_ONLY | TRADE_THROUGH | NO_FILL |
             PARTIAL_FILL | FULL_FILL | RECEIPT_INCOMPLETE
execution_evidence_eligible = true | false
```

외부 전략 주문은 micro-reversion fill evidence가 될 수 없다. `NO_FILL`은 실제 submit과 terminal receipt가 모두 확인될 때만 허용한다. micro-reversion 원천은 제출 여부와 무관하게 `event_id + order_decision_id + entry_policy_version + quote_snapshot_id` pairing을 요구한다.

신규 metric은 다음 계약을 함께 선언한다.

- `metric_role`
- `decision_authority`
- `window_policy`
- `sample_floor`
- `primary_decision_metric`
- `source_quality_gate`
- `forbidden_uses`

complete-case EV는 진단값으로만 남긴다. 경제성 headline은 모든 탐지 signal을 분모로 하고 resolved/unresolved, optimistic/conservative fill bound와 clustered lower confidence bound를 함께 보고한다. 승률과 recovery rate는 진단지표로만 사용한다.

## 9. 구현 단계와 종료 조건

### Phase A — V0 coverage-aware replay

- clean-baseline raw inventory와 required-field coverage report 생성
- 전체 관측 universe의 동일 기준 event reconstruction
- price/BBO/micro tier별 15/30/60초 MFE·MAE·recovery/continuation 계산
- 날짜 walk-forward split과 보수적 거래비용 적용
- 종목·venue·session bucket별 sample floor와 Wilson lower bound 계산

종료 조건:

- look-ahead 없는 deterministic replay test 통과
- 동일 입력 재실행 결과 hash 동일
- 종목별 동일 수집·탐지·평가 계약과 결과 재현성 확인
- usable coverage와 결손 분모가 함께 보고됨

### Phase B — forward collector 건강성 gate

- CORE/DISCOVERY registry와 deterministic multi-horizon detector 구현
- append-only continuous path journal 및 future label scheduler 연결
- 기존 WebSocket 등록 종목의 이미 수신 중인 `0D`를 별도 bounded queue와
  `market_depth_stream.jsonl`에 기록한다. 0B canonical stream은 그대로 두고,
  P2는 동일 symbol/venue/session의 최신 과거 0D만 freshness 한도 안에서 offline
  join한다. 신규 구독·route 확대와 future/cross-venue/imputed join은 금지한다.
- LLM, broker, order manager import 금지 test 추가
- source-quality fail-closed와 process restart state 복원 검증

종료 조건:

- `actual_order_submitted=false`, `broker_order_forbidden=true` 고정
- event dedupe/hysteresis/cooldown test 통과
- venue/session 분리 test 통과
- coverage 분모 고정, required path fields forward coverage `>=90%`
- queue drop/restart/dedupe/recovery test 통과
- 최소 5거래일과 전체 성숙 event `>=200`

이 종료조건은 수집기 건강성만 승인하며 경제성 또는 sim 승격 근거가 아니다.

### P2-A — path-only joint replay

Phase B data-readiness가 닫힌 뒤 실제 경로 discovery를 실행한다. 현재 source-only P2 schema는 exchange/local/sequence decision watermark, deterministic first-touch, touch upper/trade-through lower bound, partial fill, 분리된 entry/holding TTL, same-point `STOP_FIRST|AMBIGUOUS`, frozen partial-runner에 더해 `RECLAIM_ENTRY`와 `HYBRID_ENTRY`를 구현한다. Reclaim은 event 이후 running low에서 사전 고정 bp 회복을 실제 체결로 확인하고 같은 관측의 ask를 사용하지 않은 채 다음 fresh ask에서만 체결을 가정하며, 체결 전 신저가가 나오면 confirmation을 취소한다. Hybrid는 사전 고정 passive TTL 안의 bid fill을 먼저 평가하고 no-fill일 때만 reclaim 단계로 전환한다. 이 replay는 passive 취소 receipt나 실제 fill을 추정하지 않으며 실제 V0/forward data discovery와 policy ranking은 하지 않는다.

`onset_quality.py`는 V2 event reference와 canonical path에서 detector clock, reference/shock 가격, trigger 수량·aggressor, additional MAE, 저점 도달 지연, 저점 이후 reclaim을 재구성한다. 저장자료만으로 robust/warm-up trigger basis를 확정할 수 없으면 `UNKNOWN_RECONSTRUCTED`를 유지하고 보간하지 않는다. 이 결과는 shock onset이 바닥이나 진입점이라는 뜻이 아니며 Gate B 전에는 source-quality/pattern-timing 진단으로만 사용한다.

### P2-B — discovery policy selection

discovery 기간에 `policy_family`, entry/exit/cost version, cohort, selected/frozen timestamp, multiple-test family를 고정한다. 결과는 `selection_authority=false`이며 tax unknown은 gross/path 진단만 허용하고 economic headline과 promotion은 false다.

### P2-C — frozen confirmation

별도 confirmation window에서 policy/cohort/cost/target/stop/TTL을 변경하지 않고 다음을 판정한다.

- `net_ev_per_all_detected_signal` clustered lower confidence bound `> 0`
- per-filled-trade EV와 expected fill fraction은 secondary metric
- p90/p95 tail budget과 capital-time efficiency
- trade_date·symbol·parent_wave concentration
- multiple-test FDR
- all/resolved/unresolved와 optimistic/conservative bound 동시 보고

### Phase C — sim assumed-fill 후보

P2-C confirmation이 닫힌 뒤 별도 사용자 작업과 재감리로만 연다. 현재 불승인이다.

## 10. 금지사항

- 삭제된 panic-buying artifact 재사용 또는 이름만 변경한 복원
- micro-reversion 내부에서 수동관리 제외목록을 이용한 수집·평가 차등 처리
- 향후 실제 주문 adapter에서 기존 공통 수동관리 제외 guard 우회
- missing orderbook/aggressor 값을 정상값 또는 0으로 대체
- selected decision-time 표본을 전체 universe 표본으로 해석
- 승률 또는 단순 수익률 합계를 EV로 사용
- V0/V1 결과만으로 BUY threshold, TP, stop, provider, bot, quantity, cap 변경
- execution observation journal에서 주문·취소·매도 호출
- 사용자 승인 없는 real-order adapter 추가

## 11. 최종 권고

구현 가치는 있다. 다만 가치는 “즉시 매매기계”가 아니라, 평균회귀형 종목과 실제 shock-reversion event가 존재하는지 빠르게 기각하거나 확인하는 독립 검증기에서 시작한다.

Phase A V0 replay와 P0 tax/common-maturity/journal 계약, producer-safe adapter/ring/coalescer/metric, P2-A source-only joint replay와 onset 품질 진단, source-only clean integration commit/manifest는 완료됐다. 일반 과세주권 aggregate fixed-horizon gate는 실패했으므로 전체 이벤트 실행정책은 종료한다. 다음 실행은 forward collector Gate B를 닫고 실제 경로 discovery policy/cohort/cost를 별도로 동결하는 것이다. 수집기 건강성 gate가 닫히기 전에는 실제 경로 P2 discovery를 실행하거나 정책을 ranking하지 않는다. 관측·P2 경로에는 주문권한을 부여하지 않는다.

0D depth 보완은 구독 추가가 아니라 기존 연속 0D producer의 누락된 관측
consumer를 복구하는 source-quality 작업이다. 기능은 기본 OFF이며 코드리뷰 후
별도 runtime 승인으로만 켠다. 활성화 후에는 depth join coverage와 age 분포를 먼저
확인하고, depth 자체를 진입 또는 fill 증거로 사용하지 않는다.
