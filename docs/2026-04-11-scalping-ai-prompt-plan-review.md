# 스캘핑 AI 프롬프트 개선안 비교검토 및 플랜 보완안

## 목적

- `2026-04-10` 현행 플랜과 `2026-04-11` 프롬프트 검토/구현 지시 문서를 대조해, 유지할 축과 추가할 축을 분리한다.
- 기준은 `기대값/순이익 극대화`, `한 번에 한 축 canary`, `원격 선행`, `본서버 현행 점검 유지`, `리포트 정합성 우선`이다.

## 1. 종합 판정

- 판정:
  - `2026-04-10` 플랜의 큰 축은 유지가 맞다.
  - `latency / partial fill / hard stop taxonomy / AI overlap audit` 중심의 현행 점검계획은 그대로 살아 있어야 한다.
  - `2026-04-11` 문서는 이 플랜을 뒤집는 문서가 아니라, `프롬프트 구조 / 입력 패킷 / 출력 정합성` 축을 별도 트랙으로 추가하는 문서로 해석하는 것이 맞다.
- 핵심 결론:
  - 본서버:
    - `2026-04-10-scalping-ai-coding-instructions.md`
    - `2026-04-13-stage2-todo-checklist.md`
    기준의 현행 점검계획을 그대로 팔로우한다.
  - 원격서버 또는 shadow:
    - 프롬프트 분리
    - HOLDING 컨텍스트 주입
    - WATCHING 선통과 문맥 주입
    - 정량 피처 이식
    같은 `의사결정 변경성`이 있는 작업을 순차 canary로 태운다.
  - 즉시 착수할 항목은 `의도 확인`, `override 조건 명세`, `운영 계측 보강` 위주다.

## 1-1. 이번 재검토로 조정된 4가지

1. `SCALP_PRESET_TP SELL` 문제는 `DROP` 단순 정리가 아니라 `의도 확인 후 처리`로 재분류한다.
2. `WATCHING 75 정합화`는 문구 수정이 아니라 판단 기준 변경 가능성이 있으므로 `원격 canary`로 재분류한다.
3. `HOLDING hybrid`는 구현보다 먼저 `override 조건 명세`를 선행한다.
4. `프롬프트 분리`와 `컨텍스트 주입`은 같은 단계가 아니라 `순차 canary`로 나눈다.

## 2. 현행 플랜과 4/11 문서의 관계

| 항목 | 현행 플랜 상태 | 4/11 문서 제안 | 병합 판정 |
| --- | --- | --- | --- |
| `latency reason breakdown` | 이미 Phase 0/1 축에 포함 | 직접 제안은 약함 | `그대로 유지` |
| `partial fill sync mismatch` | 이미 Phase 0/1 축에 포함 | 직접 제안은 약함 | `그대로 유지` |
| `AI overlap audit` | 이미 감사축으로 포함 | WATCHING 선통과 문맥, 감사 3값 투입 제안 | `확장 병합` |
| `hard stop taxonomy audit` | 이미 감사축으로 포함 | HOLDING action 활용 논의와 연결 | `그대로 유지 + exit authority 해석에 활용` |
| `WATCHING/HOLDING 프롬프트 분리` | 현행 플랜에 없음 | 강하게 제안 | `신규 추가 (2-A: 물리 분리만)` |
| `HOLDING 포지션 컨텍스트 주입` | 현행 플랜에 없음 | 강하게 제안 | `신규 추가 (2-B: 분리 안정 후)` |
| `WATCHING 사전 통과 문맥 주입` | overlap audit과 부분 연결 | 강하게 제안 | `신규 추가 (분리/holding 주입 후 순차)` |
| `SCALP_PRESET_TP action 정합화` | 현행 플랜에 없음 | 즉시 수정 제안 | `즉시 추가가 아니라 의도 확인 후 처리` |
| `WATCHING score band vs live threshold` | 현행 플랜에 없음 | 즉시 정합화 제안 | `원격 canary 재분류` |
| `parse fail / cooldown / Big-Bite 계측` | 현행 플랜에 없음 | 운영 계측 제안 | `신규 추가` |
| `정량형 수급 피처 이식` | 현행 플랜에 없음 | OpenAI v2 피처 이식 제안 | `원격 2단계 추가` |
| `HOLDING action 직접 사용` | 현행 플랜에 없음 | 혼합형 사용 제안 | `원격 후순위 추가` |
| `HOLDING hybrid override 조건 명세` | 현행 플랜에 없음 | 명시적 언급 부족 | `선행 문서화 추가` |
| `raw 입력 대폭 제거` | 현행 플랜에 없음 | 경량화 제안 | `후순위 / A/B 전제` |
| `OpenAI live 전환` | 현행 플랜과 불일치 | 일부 문서에서 시사 | `병합 안 함` |

## 3. 보완된 실행 구조

### A. 트랙 A: 현행 점검계획 유지

- 본서버는 아래 축을 그대로 유지한다.
  - `latency`
  - `expired_armed`
  - `partial fill sync`
  - `AI overlap audit`
  - `hard stop taxonomy audit`
- 이유:
  - 현재 단계의 최상위 목적은 여전히 `주문전 차단 구조 분해`와 `EV 누수 구간 계측`이다.
  - 이 축을 흔들면 `4/10~4/13` 기준으로 이미 고정된 비교체계가 무너진다.

### B. 트랙 B: 프롬프트 구조 보강

- 프롬프트/입력 패킷 개선은 `기존 플랜의 대체재`가 아니라 `별도 개선 트랙`으로 편성한다.
- 적용 순서는 아래가 맞다.

#### Prompt-P0. 즉시 착수 가능한 확인/계측

1. `SCALP_PRESET_TP SELL` 의도 확인
   - 현재 코드의 `SELL` 비교는 `2026-04-01` 리팩터 커밋 `b4eb938` 시점부터 존재한다.
   - 따라서 단순 오타로 단정하지 말고 `의도 확인 후 처리`가 맞다.
   - 정리 방식은 아래 순서가 맞다.
     - 의도 없음: `SELL` 제거 + 이유 주석화
     - 향후 HOLDING 분리용 흔적: 주석 보존 후 임시 정리
   - 즉시 `SELL`을 프롬프트에 추가하지는 않는다.

2. `AI 운영 계측` 추가
   - `ai_parse_ok / ai_parse_fail`
   - `fallback_score_50`
   - `AI_WATCHING_COOLDOWN` 중 재기회 차단
   - `Big-Bite` 가점 전/후 점수
   - 이 계측은 본서버에도 넣을 수 있다.
   - 단, 새 로깅 시스템이 아니라 기존 `ENTRY_PIPELINE / HOLDING_PIPELINE` 확장으로 넣는다.

3. `HOLDING hybrid override 조건 명세`
   - `FORCE_EXIT`, `SELL`, `score`, `reason`의 상호 우선순위를 먼저 문서화한다.
   - 구현보다 먼저 아래를 정해야 한다.
     - 어떤 조건이면 `action`이 `score`를 override 하는가
     - 어떤 조건이면 `smoothed_score`를 계속 우선하는가
     - 어떤 조건이면 `reason`은 로그 전용인가

#### Prompt-P1. 원격 canary 대상 판단 기준/구조 변경

1. `WATCHING score band` 75 정합화
   - `80 -> 75`는 단순 문구 수정이 아니라 AI 스코어/action 분포에 영향을 줄 수 있다.
   - 따라서 본서버 즉시 병합이 아니라 `원격 canary`가 맞다.

2. `SCALPING_WATCHING_SYSTEM_PROMPT / SCALPING_HOLDING_SYSTEM_PROMPT` 물리 분리
   - 이 단계에서는 `호출 분기`와 `질문 구조`만 바꾼다.
   - 데이터 payload는 최대한 기존 유지로 묶는다.

- 이 단계는 의사결정 표면을 바꾸므로 `원격 또는 shadow 우선`이 맞다.
- 본서버는 최소한 현재 점검 구간이 끝날 때까지 live 반영을 보류한다.

#### Prompt-P2. 컨텍스트 주입 순차 진행

1. HOLDING 포지션 컨텍스트 주입
   - `buy_price`
   - `profit_rate`
   - `peak_profit`
   - `held_sec`
   - `position_tag`
   - 이 단계는 `프롬프트 분리`와 분리해서 단독 관측한다.

2. WATCHING 사전 통과 문맥 주입
   - `dynamic strength PASS`
   - `threshold_profile`
   - `gap_pct`
   - `target_buy_price`
   - 이 단계도 HOLDING 주입과 다시 분리하는 것이 맞다.

#### Prompt-P3. 입력 패킷 보강

1. 감사 3값 투입
   - `buy_pressure_10t`
   - `distance_from_day_high_pct`
   - `intraday_range_pct`
2. OpenAI v2 정량 피처 1차 이식
   - `tick_acceleration_ratio`
   - `same_price_buy_absorption`
   - `large_sell_print_detected`
   - `net_aggressive_delta_10t`
   - `ask_depth_ratio`
   - `net_ask_depth`

- 이 단계도 live 판단을 바꾸므로 `원격 1축 canary`가 맞다.
- `WATCHING`과 `HOLDING`을 한 번에 바꾸지 말고, 먼저 `WATCHING` 또는 `HOLDING` 한쪽만 고른다.

#### Prompt-P4. HOLDING 의사결정 구조 보강

1. `score-only`에서 `score + action + reason` 혼합형으로 확장
2. `FORCE_EXIT` 또는 제한된 `SELL` 조건만 직접 반영
3. `HOLDING critical` 경량 프롬프트 분리
4. raw 입력 축소 A/B

- 이 단계는 사실상 `청산 구조 미세 재설계`에 가깝다.
- 따라서 `원격 후순위`가 맞고, 본서버 즉시 반영 대상은 아니다.

## 4. 코드베이스 적합성 기준으로 수정한 구현 우선순위

### 우선순위 1

- `SCALP_PRESET_TP SELL` 의도 확인
- `parse fail / fallback 50 / cooldown / Big-Bite` 계측 추가
- `HOLDING hybrid override 조건 명세`

### 우선순위 2-A

- `WATCHING score band` 75 정합화 원격 canary
- `WATCHING/HOLDING` 프롬프트 물리 분리

### 우선순위 2-B

- `HOLDING` 포지션 컨텍스트 주입

### 우선순위 2-C

- `WATCHING` 선통과 문맥 주입

### 우선순위 3

- 감사 3값 프롬프트 투입
- OpenAI v2 정량 피처의 Gemini 입력 패킷 이식

### 우선순위 4

- HOLDING action 혼합형 사용
- HOLDING critical 경량 프롬프트
- raw 입력 축소 A/B

## 5. 원격서버 / 본서버 역할 분리

### 본서버

- 현행 점검계획 유지
- 비교 기준 유지가 중요한 계측/리포트만 반영
- 실시간 의사결정이 바뀌는 프롬프트 변경은 보류

### 원격서버 (`songstockscan`)

- 프롬프트 구조 변경 canary
- 입력 패킷 확장 canary
- HOLDING action 혼합형 실험
- 필요 시 `position_tag` 또는 `exit_mode` 제한 canary

### 공통 원칙

- `한 번에 한 축`
- `prompt_version / packet_version / action_schema_version` 로그 필수
- 즉시 롤백 가능한 env flag 또는 설정값 필요

## 6. 구현 시 코드베이스 적합성 메모

1. 프롬프트 선택 분기는 `strategy` 전체가 아니라 `cache_profile="holding"` 또는 별도 `decision_mode` 기준으로 거는 편이 안전하다.
   - 현재 `strategy="SCALPING"` 경로가 WATCHING, 일반 HOLDING, `SCALP_PRESET_TP`를 함께 쓰고 있기 때문이다.

2. `OpenAI v2` 피처는 엔진 교체가 아니라 `공통 feature helper` 후보로 보는 편이 맞다.
   - Gemini 경로가 OpenAI 엔진 클래스에 직접 의존하게 만들면 결합도가 높아진다.

3. `HOLDING action`은 즉시 전면 권한을 주지 말고 `hybrid`로 시작해야 한다.
   - 현재 보유 청산은 `smoothed_score`, `ai_low_score_hits`, `protect/hard stop`, `trailing`과 묶여 있다.
   - 단, hybrid 적용 전 `override 조건 명세`가 먼저 있어야 실험 해석이 가능하다.

4. raw 입력 축소는 `정량 피처 먼저, raw 제거는 나중` 순서가 맞다.
   - 지금 단계에서 raw를 먼저 걷으면 정확도 악화 원인과 속도 개선 원인을 분리하기 어렵다.

## 7. 최종 결론

- `2026-04-10` 플랜은 유지한다.
- `2026-04-11` 프롬프트 개선안은 `Prompt Track`으로 별도 병합한다.
- 본서버는 현행 점검계획을 계속 팔로우하고, 원격서버는 프롬프트 구조 변경을 1축씩 실험하는 구성이 현재 코드베이스와 운영원칙에 가장 잘 맞는다.
- 이번 재검토로 조정된 핵심은 아래 4가지다.
  - `SELL`은 `DROP` 단순 정리가 아니라 `의도 확인 후 처리`
  - `WATCHING 75 정합화`는 `원격 canary`
  - `HOLDING hybrid`는 `override 조건 명세` 선행
  - `프롬프트 분리`와 `컨텍스트 주입`은 `순차 진행`

## 참고 문서

- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-10-scalping-review-validation.md](./2026-04-10-scalping-review-validation.md)
- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-review-validation.md](./2026-04-11-scalping-ai-prompt-review-validation.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
