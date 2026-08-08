# Scalp Micro-Reversion V1 Feasibility And Implementation Plan

- 작성일: `2026-08-08 KST`
- 제안 namespace: `scalp_micro_reversion`
- 상태: `v0_replay_implementation_recommended / execution_validation_not_ready`
- 실주문 권한: 없음
- LLM 의사결정 권한: 없음

## 1. 판정

“짧은 매도 충격 뒤 빠른 가격 복귀를 매수하고, 복귀·과열 구간에서 청산한다”는 가설은 기존 데이터로 1차 전략 가능성을 검증할 수 있다. 다만 현재 데이터는 선택된 판단 시점의 관측이 많고 연속적인 sub-second 체결·L2 호가·queue position·주문 ACK/체결 지연이 부족하므로, 기존 자료만으로 초단타 실주문 성과를 확정할 수는 없다.

따라서 진행 순서는 다음으로 제한한다.

1. 기존 clean-baseline 데이터로 coverage-aware V0 replay를 실행한다.
2. 유효한 가설만 V1 forward shadow observer로 옮겨 연속 이벤트 저널을 쌓는다.
3. 충분한 forward 표본에서 비용 차감 EV와 tail loss를 검증한 뒤 sim assumed-fill을 연다.
4. 실주문은 별도 사용자 승인, 별도 runtime family, 별도 rollback 계약 전에는 열지 않는다.

삭제된 `panic_buying` 코드, 리포트, artifact, euphoria stage 또는 승인 family는 입력·호환 경로·이름 재사용 대상으로 삼지 않는다.

## 2. 근거 데이터

의사결정 입력은 `2026-06-05T00:00:00+09:00` 이후 clean-baseline 자료로 제한한다.

최근 원천자료의 1차 inventory는 다음과 같다.

| 범위 | 관측값 | 해석 |
|---|---:|---|
| pipeline events `2026-08-03`~`2026-08-07` | `2,644,506` rows | 이벤트/가격 경로 가설 탐색 가능 |
| 수동관리 제외 후 rows | `2,514,203` | V0 universe의 상한 inventory |
| non-manual `current_price_observed` | `2,440,443` occurrences | 중복·비정규장 관측 포함 |
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
수동관리 제외: 950160, 005930, 034020, 042660
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

## 5. 수동관리 제외 하드 계약

`evaluate_manual_control_exclusion(code)`를 다음 모든 경계의 첫 번째 검사로 사용한다.

1. historical replay universe 구성 전
2. 키움 보완 API request 구성 전
3. pattern propensity scanner 입력 전
4. active symbol registry 등록·갱신 전
5. 실시간 detector state 생성 전
6. event journal write 전
7. 향후 sim/live adapter 호출 전

제외 판정은 전략 외부 guard log에 `manual_control_excluded` provenance만 남기고 해당 종목의 전략 feature, event journal row, API 요청을 생성하지 않는다. 이미 active인 종목이 장중 제외되면 내부 registry/state만 폐기한다. 주문 취소·매도·수량 변경은 수행하지 않는다.

현재 제외 파일의 `950160`, `005930`, `034020`, `042660`은 V0 분석과 모든 보완 조회에서 제외한다. 특히 `034020`의 위젯 전용 owner는 이 전략의 예외가 아니다.

## 6. Loose-Coupled V1 구조

```text
existing market-data snapshot/event
              |
              v
manual-control exclusion veto
              |
              v
Pattern Propensity Scanner (slow, offline/intraday refresh)
              |
              v
Active Symbol Registry (TTL, venue/session keyed)
              |
              v
Scream Pulse Detector (deterministic, no LLM)
              |
              v
Reversion State Machine
              |
              +--> Event Journal + future-path labeler
              |
              +--> shadow decision envelope only
```

V1은 기존 스캘핑 엔진의 주문 함수, AI 판단기, ADM/LDM runtime policy를 호출하지 않는다. 기존 market-data producer에서 immutable snapshot을 받는 얇은 adapter와 event journal만 연결한다.

권장 source ownership:

```text
src/engine/scalping/micro_reversion/
  contracts.py
  universe.py
  detector.py
  state_machine.py
  journal.py
  replay.py
  kiwoom_tick_backfill.py
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

## 8. 이벤트 저널 계약

이벤트 시작 시 최소 필드:

```text
event_id, symbol, venue, session_bucket, time_bucket
detected_at, peak_at, reference_bid, reference_ask
reference_price, micro_vwap, spread_bps
return_z, acceleration_z, sell_pressure_z
coverage_tier, source_quality_status
manual_control_exclusion_checked=true
actual_order_submitted=false
broker_order_forbidden=true
decision_authority=shadow_observation_only
```

성숙 후 다음 label을 append-only로 붙인다.

```text
mfe/mae at 5s, 10s, 15s, 30s, 60s
recovery_first, continuation_first
micro_vwap_reclaimed, reclaim_time_ms
second_shock, cost_adjusted_return
outcome_source_quality_status
```

신규 metric은 다음 계약을 함께 선언한다.

- `metric_role`
- `decision_authority`
- `window_policy`
- `sample_floor`
- `primary_decision_metric`
- `source_quality_gate`
- `forbidden_uses`

EV는 `source_quality_adjusted_ev_pct` 또는 `notional_weighted_ev_pct`로 보고한다. 승률은 `diagnostic_win_rate`로만 사용한다.

## 9. 구현 단계와 종료 조건

### Phase A — V0 coverage-aware replay

- clean-baseline raw inventory와 required-field coverage report 생성
- 수동관리 제외를 적용한 event reconstruction
- price/BBO/micro tier별 15/30/60초 MFE·MAE·recovery/continuation 계산
- 날짜 walk-forward split과 보수적 거래비용 적용
- 종목·venue·session bucket별 sample floor와 Wilson lower bound 계산

종료 조건:

- look-ahead 없는 deterministic replay test 통과
- 동일 입력 재실행 결과 hash 동일
- 수동관리 제외종목 event/API request count `0`
- usable coverage와 결손 분모가 함께 보고됨

### Phase B — V1 forward shadow observer

- active registry와 deterministic detector 구현
- append-only event journal 및 future label scheduler 구현
- LLM, broker, order manager import 금지 test 추가
- source-quality fail-closed와 process restart state 복원 검증

종료 조건:

- `actual_order_submitted=false`, `broker_order_forbidden=true` 고정
- event dedupe/hysteresis/cooldown test 통과
- venue/session 분리 test 통과
- required micro fields forward coverage `>=90%`
- 최소 5거래일과 전체 성숙 event `>=200`

### Phase C — sim assumed-fill 후보

다음을 모두 충족할 때만 별도 작업으로 연다.

- rolling parent bucket 성숙 event `>=100`
- 보수적 비용 차감 `source_quality_adjusted_ev_pct > 0`
- recovery Wilson lower bound가 continuation 비율보다 큼
- p90/p95 MAE가 사전 정의한 sim risk budget 안에 있음
- 특정 1일·1종목·thin child bucket에 성과가 집중되지 않음
- source-quality unknown과 API 보완 provenance가 해소됨

Phase C도 실주문 근거가 아니며 sim-only다.

## 10. 금지사항

- 삭제된 panic-buying artifact 재사용 또는 이름만 변경한 복원
- manual-control 제외종목의 scanner/API/journal/sim/live 처리
- missing orderbook/aggressor 값을 정상값 또는 0으로 대체
- selected decision-time 표본을 전체 universe 표본으로 해석
- 승률 또는 단순 수익률 합계를 EV로 사용
- V0/V1 결과만으로 BUY threshold, TP, stop, provider, bot, quantity, cap 변경
- shadow observer에서 주문·취소·매도 호출
- 사용자 승인 없는 real-order adapter 추가

## 11. 최종 권고

구현 가치는 있다. 다만 가치는 “즉시 매매기계”가 아니라, 평균회귀형 종목과 실제 shock-reversion event가 존재하는지 빠르게 기각하거나 확인하는 독립 검증기에서 시작한다.

첫 구현 범위는 `Phase A V0 replay + coverage report`로 제한한다. V0에서 비용 차감 EV 또는 event coverage가 성립하지 않으면 V1 observer를 만들지 않고 전략을 종료한다. V0가 통과하면 V1은 기존 스캘핑 아키텍처에 주문 권한을 주지 않는 forward shadow observer로 구현한다.
