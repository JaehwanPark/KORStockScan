# 2026-05-03 Order Flow Imbalance 적용현황 감사 보고서

기준 시각: `2026-05-03 KST`  
대상 질의: "현재 코드베이스 내 Order Flow Imbalance(OFI)가 적용된 부분이 있는가"

## 1. 판정

판정: **적용되어 있다.**

다만 현재 구현은 `Order Flow Imbalance`가 독립 전략축이나 단일 runtime gate로 직접 적용된 형태가 아니라, **`OFI/QI orderbook micro` 형태로 계산되어 `dynamic_entry_ai_price_canary_p2`의 입력 컨텍스트에 주입되는 보조 피처**다.

즉, 현재 코드는 다음 상태로 보는 것이 정확하다.

1. **호가/체결 이벤트에서 OFI 관련 미시구조 값을 실시간 계산한다.**
2. **계산 결과를 entry latency snapshot에 포함한다.**
3. **submitted 직전 Tier2 AI 진입가 판단 컨텍스트로 전달한다.**
4. **AI는 bearish micro 상태를 `SKIP` 근거로 사용할 수 있다.**
5. **하지만 OFI 단독으로 주문을 차단하는 하드 룰은 없다.**

## 2. 적용 범위 요약

| 구간 | 적용 여부 | 내용 |
| --- | --- | --- |
| 실시간 데이터 수집 | 적용 | websocket 체결/호가 이벤트에서 observer에 입력 |
| OFI/QI 계산 | 적용 | `ofi_instant`, `ofi_ewma`, `ofi_norm`, `ofi_z`, `qi`, `qi_ewma`, `micro_state` 계산 |
| entry latency snapshot 포함 | 적용 | `orderbook_stability.orderbook_micro`로 snapshot에 포함 |
| 스캘핑 P2 entry AI 컨텍스트 주입 | 적용 | `price_context.orderbook_micro`로 전달 |
| AI 프롬프트 판단 규칙 반영 | 적용 | `bearish + ready`면 `SKIP` 근거 가능 |
| 독립 hard gate / standalone canary | 미적용 | OFI 단독 차단 규칙은 현재 없음 |
| holding/exit live rule 직접 반영 | 미적용 | 현재 확인 범위에서는 직접 적용 흔적 없음 |

## 3. 코드 적용 증적

### 3.1 실시간 입력 경로

실시간 체결 데이터는 websocket 처리부에서 observer로 유입된다.

- 체결 입력: [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:822)
  - `ORDERBOOK_STABILITY_OBSERVER.record_trade(...)`
- 호가 입력: [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:860)
  - `ORDERBOOK_STABILITY_OBSERVER.record_quote(...)`

이 경로는 OFI를 사후 배치 계산이 아니라 **실시간 호가/체결 스트림 기반 입력**으로 운용하고 있음을 의미한다.

### 3.2 OFI/QI 계산 로직

OFI/QI 계산 핵심은 [src/trading/entry/orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py:249)에 구현되어 있다.

핵심 계산 항목:

- `ofi_instant`: bid/ask 변화와 잔량 변화를 조합한 즉시 OFI
- `ofi_ewma`: OFI 지수평활
- `ofi_norm`: depth 정규화 OFI
- `ofi_z`: window 내 OFI z-score
- `qi`: best bid / (best bid + best ask)
- `qi_ewma`: queue imbalance 지수평활
- `micro_state`: `bullish`, `bearish`, `neutral`, `insufficient`

세부 근거:

- OFI instant 계산: [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py:267)
- QI 계산: [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py:293)
- OFI z-score 계산: [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py:309)
- micro state 판정: [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py:320)

현재 구현 기준 micro state는 다음처럼 분류된다.

- `bullish`: `ofi_z >= 1.2` 그리고 `qi_ewma >= 0.55`
- `bearish`: `ofi_z <= -1.0` 그리고 `qi_ewma < 0.48`
- 그 외: `neutral`
- 표본 부족/수량 부재: `insufficient`

즉, 현재 코드베이스에서 OFI는 단순 raw imbalance가 아니라 **depth-normalized + z-score화된 orderbook micro feature**로 쓰인다.

### 3.3 latency snapshot 포함

entry latency 판단 결과를 구성할 때 `ORDERBOOK_STABILITY_OBSERVER.snapshot(code)`가 포함된다.

- 근거: [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:1021)

여기서 `orderbook_stability` 아래에 `orderbook_micro`가 실리므로, OFI/QI는 단순 로그 유실 없이 이후 단계로 전달 가능한 구조다.

### 3.4 entry AI price canary 컨텍스트 주입

P2 진입가 AI 컨텍스트 빌더는 `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED`가 켜져 있으면 `orderbook_micro`를 `price_context`에 넣는다.

- 플래그 가드: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1853)
- 컨텍스트 구성: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1946)
- AI 호출 직전 주입: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2006)

주입 필드:

- `ready`
- `reason`
- `qi`
- `qi_ewma`
- `ofi_norm`
- `ofi_z`
- `depth_ewma`
- `micro_state`
- `sample_quote_count`
- `spread_ticks`

즉, OFI는 현재 **`price_context.orderbook_micro.ofi_z`** 같은 구조로 AI 입력에 직접 들어간다.

### 3.5 AI 판단 규칙 반영

entry price prompt에는 OFI/QI micro 상태의 사용 원칙이 명시돼 있다.

- 근거: [src/engine/ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:118)

현재 프롬프트 규칙의 핵심:

1. `orderbook_micro`가 `ready`
2. `micro_state=bearish`
3. 체결강도/latency/가격 context가 반박하지 않음

위 조건이면 `SKIP` 근거로 사용할 수 있다.

반대로:

- `neutral`
- `insufficient`

상태에서는 **OFI/QI만으로 SKIP하지 말라**고 명시돼 있다.

이 설계는 OFI를 사용하되 **단독 과잉차단을 피하는 fail-closed 보조 입력**으로 제한한 형태다.

### 3.6 엔진별 반영 범위

entry price 판단은 Gemini/OpenAI/DeepSeek 경로 모두 `price_context`를 동일하게 입력받는다.

- Gemini: [src/engine/ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1653)
- OpenAI: [src/engine/ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py:1799)
- DeepSeek: [src/engine/ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:1208)

세 엔진 모두 `user_input` JSON에 `price_context`를 넣고 있으므로, OFI/QI micro는 provider별 분기 없이 공통 입력으로 전달된다.

### 3.7 runtime 플래그

현재 기본 상수에서 feature는 활성화 상태다.

- 근거: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:178)
- 핵심 플래그: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:183)

현재 기본값:

- `SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True`
- `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True`

따라서 기본 설정 기준으로는 OFI/QI micro 입력이 꺼져 있는 상태가 아니다.

## 4. 로그/운영 증적

`sniper_state_handlers.py`는 OFI/QI micro 상태를 로그 필드로도 남긴다.

- log field 구성: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1889)
- `latency_pass` 로그에 포함: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3947)
- AI fallback/skip 로그에도 포함: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2013)

운영 로그로 남는 대표 필드:

- `orderbook_micro_ready`
- `orderbook_micro_reason`
- `orderbook_micro_state`
- `orderbook_micro_sample_quote_count`
- `orderbook_micro_qi`
- `orderbook_micro_qi_ewma`
- `orderbook_micro_ofi_norm`
- `orderbook_micro_ofi_z`
- `orderbook_micro_depth_ewma`
- `orderbook_micro_spread_ticks`

즉, 감리 시에는 단순히 "코드에 있다" 수준이 아니라 **실행 시점 provenance를 로그로 역추적할 수 있는 상태**다.

## 5. 테스트 증적

### 5.1 OFI/QI 계산 테스트

- [src/tests/test_orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/tests/test_orderbook_stability_observer.py:57)
  - `qi`, `qi_ewma`, `ofi_instant`, `ofi_ewma`, `ofi_norm`, `depth_ewma` 계산 검증
- [src/tests/test_orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/tests/test_orderbook_stability_observer.py:92)
  - 최소 샘플 충족 후 `ready=True`, `ofi_z != None`, `micro_state` 생성 검증

### 5.2 entry AI context 주입 테스트

- [src/tests/test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py:1650)
  - `orderbook_micro.ready=True`, `micro_state=bearish`, `spread_ticks=1`이 context에 포함되는지 검증
- [src/tests/test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py:1683)
  - feature flag 비활성 시 `orderbook_micro`가 context에서 제거되는지 검증

따라서 현재 구현은 문서상 계획이 아니라 **계산 테스트 + context 주입 테스트까지 있는 반영 상태**다.

## 6. 비적용 범위와 한계

현재 감사 기준에서 다음은 확인되지 않았다.

1. **OFI standalone hard gate**
   - 예: `ofi_z < X`이면 주문 차단 같은 규칙
2. **holding/exit 실전 로직 직접 반영**
   - 현재 확인 경로는 entry price P2 중심
3. **OFI 단독 승격 canary**
   - 현재 문서 기준도 standalone canary가 아니라 `P2 내부 feature`
4. **OFI 단독 손익 판정 체계**
   - 현 단계에서는 fill quality, skip, soft stop, missed upside와 연결해 봐야 함

따라서 감리인에게는 "OFI가 live trading rule의 1차 문지기냐"라고 설명하면 과장이다.  
정확한 설명은 **"OFI/QI orderbook micro가 submitted 직전 AI 진입가 재판단의 입력 feature로 live 연결돼 있다"**가 된다.

## 7. 문서 증적과 코드베이스 정합성

중심 문서도 현재 상태를 같은 방향으로 설명한다.

- [docs/plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md:41)
  - `dynamic_entry_ai_price_canary_p2`에 OFI/QI orderbook micro feature가 반영됐다고 명시
- [docs/checklists/2026-05-02-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-02-stage2-todo-checklist.md:21)
  - `OrderbookMicroP2Canary0502-DesignApply` 완료 기록
- [docs/checklists/2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-04-stage2-todo-checklist.md:150)
  - `OrderbookMicroP2Canary0504-Postclose` 장후 keep/OFF 판정 예정

문서와 코드가 모두 "OFI/QI는 P2 entry price 내부 feature"라는 동일한 결론을 가리킨다.

## 8. 감리용 결론 문안

다음 문안으로 요약 가능하다.

> 현재 코드베이스에는 Order Flow Imbalance가 `OFI/QI orderbook micro` 형태로 구현돼 있으며, 실시간 호가/체결 이벤트로부터 계산된 `ofi_norm`, `ofi_z`, `qi`, `qi_ewma`, `micro_state`가 스캘핑 `dynamic_entry_ai_price_canary_p2`의 AI 입력 컨텍스트에 반영됩니다. 다만 이는 독립 hard gate가 아니라 submitted 직전 주문가/주문보류(`SKIP`) 판단을 보조하는 입력 feature이며, `neutral` 또는 `insufficient` 상태에서는 OFI/QI 단독으로 주문을 차단하지 않도록 제한돼 있습니다.

## 9. 다음 액션

1. 운영 로그에서 `orderbook_micro_state=bearish`가 실제 `entry_ai_price_canary_skip_order`로 이어진 표본 수를 집계한다.
2. micro-enabled cohort를 `submitted/full fill/partial fill/soft stop/missed upside`로 분리해 기대값 관점에서 keep/OFF를 판정한다.
3. 감리인이 원하면 다음 단계로 `실거래 로그 기준 OFI 영향 샘플 5~10건` 추적 보고서를 별도로 작성한다.
