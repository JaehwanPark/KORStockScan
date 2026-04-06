# 2026-04-06 OpenAI 듀얼 페르소나 Shadow Rollout 초안

## 목적

`Gemini`를 메인 실행 엔진으로 유지하면서, `OpenAI`를 공격적 투자자와 보수적 투자자의 경합 엔진으로 붙인다.

이번 주 목표는 `shadow mode`로 실제 주문 영향 없이 판단 품질과 충돌 패턴을 관찰하는 것이다.  
다음 주 목표는 충분한 표본과 기준점이 확보되면 제한된 범위에서 `live running`을 시작하는 것이다.

## 현재 판단

- `Gemini`는 이미 메인 표면적을 대부분 갖추고 있다.
  - 실시간 분석: `src/engine/ai_engine.py`
  - Gatekeeper: `src/engine/ai_engine.py`
  - Overnight: `src/engine/ai_engine.py`
  - Condition entry/exit: `src/engine/ai_engine.py`
- 런타임도 현재는 `Gemini`만 부팅한다.
  - `src/engine/kiwoom_sniper_v2.py`
- 반면 `OpenAI v2`는 이미 fast/deep 구조와 정량 피처 해석 흔적이 있어, 메인 엔진 복제보다 `판정 보강 레이어`로 재해석하는 편이 더 자연스럽다.
  - `src/engine/ai_engine_openai_v2.py`

이번 초안의 방향은 아래와 같다.

- `Gemini`: 메인 의사결정 엔진
- `OpenAI`: 공격/보수 경합 엔진
- 최종 합성: 코드에서 결정론적으로 계산
- 이번 주: shadow only
- 다음 주: `Gatekeeper`, `Overnight`부터 제한 적용

## 이번 초안에서 하지 않을 것

- `OpenAI`를 `Gemini`와 100% 동일한 전면 엔진으로 만들지 않는다.
- `Tier 3` 성격의 무거운 브리핑, EOD 발굴, 시장 진단은 `OpenAI`에 맡기지 않는다.
- 스캘핑 본선 매수 엔트리 루프에 이번 주 바로 live 적용하지 않는다.

## 역할 분담 초안

### 1. Gemini

- 메인 실행 엔진
- 기본 주문 판단 원본
- 기존 캐시, 게이트키퍼, 조건검색, 오버나이트, 리포트 기능 유지

### 2. OpenAI Dual Persona

- `Aggressive Persona`
  - 기회비용, 돌파 초입, 모멘텀 포착에 우호적
- `Conservative Persona`
  - 실패 확률, VWAP 이탈, 대량 매도틱, 갭 부담, 유동성 저하에 민감
- `Fused Result`
  - LLM이 아니라 코드가 가중치/규칙으로 합성

## 1차 적용 범위

이번 주 shadow mode에서는 아래 두 영역만 우선 권장한다.

1. `SWING Gatekeeper`
2. `SCALPING Overnight Decision`

이유는 아래와 같다.

- 스캘핑 진입 본선보다 latency 부담이 작다.
- 실제 손익에 미치는 영향이 크고, 보수 페르소나의 veto 가치가 높다.
- 기존 대시보드와 replay 흐름에 붙이기 쉽다.

`Condition Entry/Exit`는 이번 주에는 로그 표본만 보고, 다음 주 2차 적용 후보로 둔다.  
`Scalping analyze_target()`은 최소 1주 더 늦추는 편이 안전하다.

## 구조 초안

### 1. 공통 입력 패킷

`Gemini`와 `OpenAI`가 같은 장면을 보도록 입력 스키마를 공통화한다.

패킷은 별도 빌더 레이어에서 생성한다.

- 이름 예시: `DecisionPacketBuilder`
- 책임:
  - 실시간 컨텍스트 정규화
  - 전략/시간대/시장상태 포함
  - Gemini와 OpenAI가 같은 수치/텍스트를 보게 보장

권장 필드 예시:

```json
{
  "decision_type": "GATEKEEPER | OVERNIGHT | CONDITION_ENTRY | CONDITION_EXIT",
  "strategy": "SCALPING | KOSPI_ML | KOSDAQ_ML",
  "market_regime": "BULL | BEAR | NEUTRAL",
  "stock_name": "종목명",
  "stock_code": "000000",
  "position_tag": "KOSPI_BASE",
  "time_bucket": "OPEN | MID | LATE | PRE_CLOSE",
  "packet_version": "v1",
  "features": {},
  "context_text": "LLM용 요약 텍스트"
}
```

### 2. OpenAI 출력 스키마

공격/보수 페르소나 모두 같은 JSON 구조를 사용한다.

```json
{
  "action": "BUY | WAIT | DROP | HOLD_OVERNIGHT | SELL_NEXT_DAY",
  "score": 0,
  "confidence": 0.0,
  "risk_flags": ["VWAP_BELOW", "LARGE_SELL_PRINT"],
  "size_bias": -2,
  "veto": false,
  "thesis": "핵심 논거 한 줄",
  "invalidator": "무효 조건 한 줄"
}
```

### 3. 결정론적 합성

기본 원칙:

- `Gemini`가 1차 방향을 제시
- `OpenAI aggressive`는 기회 포착 쪽으로 미세 조정
- `OpenAI conservative`는 리스크 차단 쪽으로 미세 조정
- hard veto는 코드 규칙으로 처리

합성 예시:

```text
final_score =
  gemini_score * w_gemini
  + aggressive_score * w_aggr
  + conservative_score * w_cons
  - veto_penalty
```

합성 규칙:

- 보수 페르소나가 `veto=true`이고 hard risk flag가 2개 이상이면 `WAIT` 또는 `SELL_NEXT_DAY` 우선
- 공격/보수 모두 `Gemini`와 같은 방향이면 가중치 합성 없이 해당 방향을 강화
- 세 엔진이 모두 갈리면 `Gemini`를 기준축으로 두고 보수 veto 여부만 강하게 반영

## Shadow Mode 구조

이번 주 shadow mode의 핵심은 "실제 주문 영향 0"이다.

### 기본 흐름

1. `Gemini`가 기존대로 실제 반환값을 만든다.
2. shadow 대상이면 동일 장면의 packet을 복사한다.
3. `OpenAI aggressive`, `OpenAI conservative`를 비동기 보조 작업으로 호출한다.
4. `fused result`를 계산하되, 실제 주문/차단 로직에는 사용하지 않는다.
5. 결과는 로그와 대시보드용 집계 데이터로만 남긴다.

### 왜 비동기 shadow가 필요한가

- shadow mode는 품질 측정이 목적이지 체결 경로 지연이 목적이 아니다.
- 따라서 shadow mode에서는 주문 경로 latency를 늘리지 않는 것이 원칙이다.
- 실제 반영 전까지는 background worker 또는 thread pool 기반 비동기 실행이 맞다.

## 다음 주 Live Running 초안

다음 주는 한 번에 전면 적용하지 않는다.

### 1단계 live

- 적용 범위:
  - `SWING Gatekeeper`
  - `SCALPING Overnight Decision`
- 적용 방식:
  - `Gemini` 기본 판단 유지
  - `OpenAI conservative veto`만 제한적으로 활성화
  - 공격 페르소나는 우선 로그/가중치 참고치로 유지

### 2단계 live

- 표본이 충분하면 `fused result`를 실제 반영
- 단, 초반에는 `Gatekeeper`와 `Overnight`만 적용
- `Condition Entry/Exit`는 별도 표본을 본 뒤 활성화

### 보류 영역

- 스캘핑 초단타 본선 `analyze_target`
- EOD/Tier3 계열 작업

## 초기 가중치 초안

### Shadow Mode

실제 주문에는 미반영이므로 모든 가중치는 기록용이다.

| 영역 | Gemini | Aggressive | Conservative | 비고 |
|---|---:|---:|---:|---|
| Gatekeeper | 0.50 | 0.20 | 0.30 | 보수 veto 관찰 중요 |
| Overnight | 0.45 | 0.10 | 0.45 | 보수 성향 강하게 |
| Condition Entry | 0.65 | 0.15 | 0.20 | 다음 주 후보 |
| Condition Exit | 0.55 | 0.10 | 0.35 | 다음 주 후보 |

### Live 1단계

- `Gatekeeper`
  - 최종 기준은 `Gemini`
  - 단, 보수 veto가 아래 hard rule을 만족하면 `WAIT`
- `Overnight`
  - `Gemini`와 보수 페르소나가 동시에 회피면 `SELL_NEXT_DAY`
  - `Gemini` 단독 긍정은 일단 유지하되 shadow 성과와 비교

## Hard Veto 초안

보수 페르소나의 veto는 아무 때나 쓰지 않는다. 아래 조합일 때만 강한 효력을 준다.

- `VWAP_BELOW`
- `LARGE_SELL_PRINT`
- `GAP_TOO_HIGH`
- `THIN_LIQUIDITY`
- `WEAK_PROGRAM_FLOW`
- `FAILED_BREAKOUT`

권장 규칙:

- hard risk flag 2개 이상 + `veto=true`
- 또는 `GAP_TOO_HIGH` + `FAILED_BREAKOUT`
- 또는 `VWAP_BELOW` + `LARGE_SELL_PRINT`

## 로그 초안

기존 로그 체계를 최대한 활용한다.

- entry path: `src/engine/sniper_state_handlers.py`
- replay snapshot: `src/engine/sniper_gatekeeper_replay.py`
- tuning report: `src/engine/sniper_performance_tuning_report.py`

### 신규 stage 제안

- `dual_persona_shadow`
- `dual_persona_live_applied`
- `dual_persona_veto_applied`

### 로그 필드 제안

```text
dual_mode=shadow
decision_type=gatekeeper
strategy=KOSPI_ML
gemini_action=BUY
gemini_score=84
aggr_action=BUY
aggr_score=88
cons_action=WAIT
cons_score=61
cons_veto=true
fused_action=WAIT
fused_score=71
winner=conservative_veto
agree_ga=true
agree_gc=false
agree_ac=false
hard_flags=VWAP_BELOW,LARGE_SELL_PRINT
shadow_extra_ms=1430
packet_version=v1
```

### 핵심 집계용 파생 필드

- `agreement_bucket`
  - `all_agree`
  - `gemini_vs_cons_conflict`
  - `aggr_vs_cons_conflict`
  - `all_conflict`
- `winner`
  - `gemini_hold`
  - `aggressive_promote`
  - `conservative_veto`
  - `blended`

## 대시보드 표현 초안

기존 화면을 확장하는 방식이 좋다.

- 성능 튜닝 모니터: `src/web/app.py`
- 집계 계산: `src/engine/sniper_performance_tuning_report.py`
- 복기 화면: `src/engine/sniper_trade_review_report.py`
- 전략 성과 연결: `src/engine/strategy_position_performance_report.py`

### 1. 성능 튜닝 모니터에 추가할 카드

- `Dual Persona shadow 샘플`
- `Gemini-OpenAI 충돌률`
- `보수 veto 비율`
- `가상 fused override 비율`
- `shadow extra latency p95`
- `추정 OpenAI 호출 비용`

### 2. 조정 관찰 포인트

| 지표 | 권장 범위 | 해석 |
|---|---|---|
| 충돌률 | 15% ~ 35% | 너무 낮으면 중복, 너무 높으면 프롬프트 방향 불안정 |
| 보수 veto 비율 | 8% ~ 25% | 지나치게 낮으면 가치 없음, 너무 높으면 과보수 |
| fused override 비율 | 5% ~ 15% | 초반에는 낮게 유지하는 편이 안전 |
| shadow extra latency p95 | 2500ms 이하 | shadow는 비동기이므로 집계용만 본다 |
| all_conflict 비율 | 10% 이하 | 너무 높으면 스키마/프롬프트 재정렬 필요 |

### 3. 성과 연결 카드

`strategy-performance`와 연결할 때 아래 버킷을 나눈다.

- `gemini_only_win_rate`
- `aggressive_promote_win_rate`
- `conservative_veto_saved_loss_rate`
- `conservative_veto_missed_winner_rate`
- `fused_override_avg_profit_rate`

핵심은 보수 페르소나가 "손실을 얼마나 잘 막았는지"와 "좋은 기회를 얼마나 놓쳤는지"를 같이 보는 것이다.

### 4. Gatekeeper Replay에 추가할 것

기존 replay 화면에 아래 3줄만 추가해도 충분하다.

- `Gemini 판단`
- `Aggressive 판단`
- `Conservative 판단`
- `가상 Fused 결론`

원문 전체보다 "왜 갈렸는지"가 더 중요하다.

### 5. Trade Review에 추가할 태그

- `gemini_only`
- `shadow_aggressive_promote`
- `shadow_conservative_veto`
- `shadow_blended`

이 태그가 있어야 주말 복기에서 "이겼는데 왜 이겼는지", "졌는데 누가 막았어야 했는지"를 분리해서 볼 수 있다.

## 이번 주 운영 체크리스트

### 월~수

- shadow mode만 활성화
- 주문 영향이 전혀 없는지 확인
- `Gatekeeper`, `Overnight` 표본 30건 이상 확보
- 충돌률과 veto 비율이 과도하지 않은지 확인

### 목~금

- `trade-review`, `performance-tuning`, `gatekeeper-replay`로 표본 복기
- `보수 veto`가 실제 손실 회피에 의미가 있는지 확인
- `aggressive promote`가 잡아낸 이익 기회가 있는지 확인
- 다음 주 live 대상 범위 확정

## 다음 주 live 진입 조건

아래 4개 중 3개 이상 만족 시 live 1단계 진입을 권장한다.

- shadow 표본 50건 이상
- `conservative_veto_saved_loss_rate`가 의미 있게 높음
- `conservative_veto_missed_winner_rate`가 허용 범위 내
- `all_conflict` 비율이 10% 이하
- replay 복기에서 prompt 해석 오류가 반복되지 않음

## 중단 또는 재조정 조건

- 충돌률이 45% 이상으로 치솟음
- 보수 veto가 대부분 정상 진입을 막는 것으로 보임
- aggressive promote가 잡음성 매수로 보임
- shadow 결과가 일관되게 비상식적임
- 로그/대시보드에 충분한 필드가 남지 않아 해석이 어려움

## 구현 파일 초안

### 1차 구현 후보

- `src/engine/ai_engine_openai_v2.py`
  - dual persona 호출기
  - aggressive / conservative prompt 분리
  - fused result 계산기
- `src/engine/kiwoom_sniper_v2.py`
  - `OPENAI_API_KEY*` 로딩
  - shadow/live 플래그 부팅
- `src/engine/ai_engine.py`
  - Gemini 결과 이후 shadow dispatch hook
  - 이후 live 모드에서 fused 적용 지점 연결
- `src/engine/sniper_state_handlers.py`
  - pipeline 로그 필드 추가
- `src/engine/sniper_performance_tuning_report.py`
  - dual persona 집계 추가
- `src/web/app.py`
  - 성능 튜닝 모니터 카드/표 추가
- `src/engine/sniper_trade_review_report.py`
  - shadow/live 태그 노출
- `src/engine/strategy_position_performance_report.py`
  - winner bucket 성과 연결

## 설정값 초안

실제 구현 시 아래와 같은 설정 플래그를 권장한다.

```text
OPENAI_DUAL_PERSONA_ENABLED = true
OPENAI_DUAL_PERSONA_SHADOW_MODE = true
OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER = true
OPENAI_DUAL_PERSONA_APPLY_OVERNIGHT = true
OPENAI_DUAL_PERSONA_APPLY_CONDITION = false
OPENAI_DUAL_PERSONA_APPLY_SCALPING = false
OPENAI_DUAL_PERSONA_WORKERS = 2
OPENAI_DUAL_PERSONA_MAX_EXTRA_MS = 2500
OPENAI_DUAL_PERSONA_GATEKEEPER_G_WEIGHT = 0.50
OPENAI_DUAL_PERSONA_GATEKEEPER_A_WEIGHT = 0.20
OPENAI_DUAL_PERSONA_GATEKEEPER_C_WEIGHT = 0.30
OPENAI_DUAL_PERSONA_OVERNIGHT_G_WEIGHT = 0.45
OPENAI_DUAL_PERSONA_OVERNIGHT_A_WEIGHT = 0.10
OPENAI_DUAL_PERSONA_OVERNIGHT_C_WEIGHT = 0.45
```

## 최종 정리

이번 주에는 `Gemini` 주문 경로를 건드리지 않는다.  
`OpenAI`는 shadow mode에서 공격/보수 판단을 남기고, dashboard와 replay로 기준점을 확보한다.  
다음 주에는 `Gatekeeper`, `Overnight`만 제한 적용하고, `Scalping` 본선은 더 늦게 붙인다.

이 초안의 핵심은 아래 세 줄로 요약된다.

- `Gemini`는 메인
- `OpenAI`는 듀얼 페르소나 심판
- 실제 반영 전에는 반드시 shadow로 기준점을 먼저 만든다
