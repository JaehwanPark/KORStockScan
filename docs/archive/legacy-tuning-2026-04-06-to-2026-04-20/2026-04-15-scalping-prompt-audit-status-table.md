# 2026-04-15 스캘핑 프롬프트 작업 감사표

> 작성일: `2026-04-15`
> 제출 대상: 감사인
> 범위: `WATCHING/HOLDING` 프롬프트 개선, 감사용 핵심값, 정량형 수급 피처, `HOLDING hybrid` 적용 준비

## 1. 총괄 판정표

| 구분 | 현재 판정 | 근거 | 다음 액션 |
| --- | --- | --- | --- |
| 작업 5 `WATCHING/HOLDING` 프롬프트 물리 분리 | `착수 완료 / 장중 검증 대기` | `2026-04-14 POSTCLOSE` write scope/rollback 확정, `2026-04-15 07:51 KST` `WATCHING shared prompt shadow` 로그 경로까지 코드 반영 | 장중 `ai_prompt_type`, `action_diverged`, `entry_funnel_delta` 누적 후 `2026-04-16` 승격 판정 |
| 작업 8 감사용 핵심값 3종 투입 | `착수 완료 / 구현 지속` | 전일 체크리스트에서 같은 날 착수 확정, 오늘 체크리스트에서 구현/검증 지속 항목 유지 | 장후 결과 정리 후 `2026-04-16` 평가 포인트 고정 |
| 작업 9 정량형 수급 피처 이식 1차 | `초안 단계` | helper scope 초안 정리만 오늘 backlog에 남아 있음 | `2026-04-17` 확정형 정리, `2026-04-18` 착수 |
| 작업 10 `HOLDING hybrid` 적용 (`FORCE_EXIT` 제한형 MVP) | `범위 확정 / 구현 지속` | `FORCE_EXIT` 제한형 MVP 범위와 rollback 가드를 `2026-04-14 POSTCLOSE`에 확정, 오늘 구현 지속 항목 유지 | 장중/장후 입력값 정리 후 canary-ready 판정 |
| `WATCHING shared prompt shadow` 비교안 | `착수 완료 / 실표본 대기` | `gemini_action/score`, `gpt_action/score`, `action_diverged`, `score_gap` 로그 필드 고정 및 원격 재기동 완료 | 첫 실표본 수집 후 장후 비교표 생성 |
| 본서버 `main` 승격 | `보류` | 프롬프트 축은 `develop` 선행 적용 후 장후 결과로만 승격 판단하는 원칙 유지 | `2026-04-16` 이후 항목별 승격 가능/불가 판정 |

## 2. 세부 진행현황 표

| 작업 | 목표 | 현재 상태 | 완료/진행 근거 | 롤백 가드 | 리스크/미완료 |
| --- | --- | --- | --- | --- | --- |
| 작업 5 `WATCHING/HOLDING` 프롬프트 물리 분리 | 진입판단과 보유판단 질문 구조 분리 | `진행중` | `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_HOLDING_SYSTEM_PROMPT`, `prompt_profile` 라우팅 반영. `WATCHING shared prompt shadow` 비교 경로 추가 | `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=false` | 장중 실표본과 장후 counterfactual 비교표가 아직 없음 |
| 작업 5-보조 `WATCHING shared prompt shadow` | `Tier2 Gemini Flash` vs `GPT-4.1-mini` 동일입력 비교 | `진행중` | `watching_shared_prompt_shadow` stage에 `gemini_action`, `gemini_score`, `gpt_action`, `gpt_score`, `action_diverged`, `score_gap`, `gpt_model`, `shadow_extra_ms` 고정 | shadow-only, 실주문 비연결 | 표본 전에는 EV 개선 여부 판정 불가 |
| 작업 8 감사용 핵심값 3종 투입 | 감사/판정용 핵심 정량값을 프롬프트 입력에 연결 | `진행중` | `2026-04-14` 체크리스트에서 착수 확정, `2026-04-15` 체크리스트에서 구현/검증 지속 및 장후 결과 정리 항목 유지 | payload/packet 버전 토글로 되돌림 전제 | 실제 프롬프트 주입 결과와 품질 개선량 미확정 |
| 작업 9 정량형 수급 피처 이식 1차 | 공통 feature helper로 정량 피처 이식 | `초안` | 오늘 체크리스트 기준 `helper scope 초안 정리`와 `2026-04-17 확정형` 정리가 남아 있음 | helper 추출 전이라 실전 영향 없음 | 아직 코드 착수 전 |
| 작업 10 `HOLDING hybrid` 제한형 MVP | `FORCE_EXIT`만 제한적으로 override 연결 | `진행중` | 범위: 일반 `HOLDING` 한정, 일반 `SELL`은 로그 우선 유지, `SCALP_PRESET_TP` 실집행 제외 | `holding_override_rule_version` / `holding_action_applied=False` fallback | 실표본 전이라 override 규칙 EV 판정 보류 |
| 작업 3 `HOLDING hybrid override 조건 명세` | hybrid 적용 전 문서 명세 확정 | `완료` | 문서 명세 작업은 닫고, 실제 구현은 작업 10으로 분리 관리 | 문서 작업이라 별도 롤백 불요 | 없음 |

## 3. 코드/문서 반영 증적표

| 구분 | 반영 내용 | 증적 |
| --- | --- | --- |
| 코드 | `WATCHING/HOLDING` 프롬프트 라우팅 및 prompt version 기록 | [src/engine/ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:46), [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1701) |
| 코드 | `WATCHING shared prompt shadow` OpenAI 비교 경로 | [src/engine/ai_engine_openai_v2.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai_v2.py:1139), [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:423) |
| 코드 | `partial fill min_fill_ratio` canary 경로 | [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1235), [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:146) |
| 테스트 | 프롬프트 라우팅/운영 로그 메타 검증 | [src/tests/test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py:318), [src/tests/test_state_handler_fast_signatures.py](/home/ubuntu/KORStockScan/src/tests/test_state_handler_fast_signatures.py:94) |
| 문서 | 프롬프트 작업지시/착수 메모 | [docs/2026-04-11-scalping-ai-prompt-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-11-scalping-ai-prompt-coding-instructions.md:516) |
| 문서 | 오늘 장전 실행/장중·장후 계획 | [docs/checklists/2026-04-15-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-15-stage2-todo-checklist.md:27) |

## 4. 검증 현황 표

| 검증 항목 | 결과 | 비고 |
| --- | --- | --- |
| 로컬 `.venv` pytest | `77 passed` | 프롬프트 라우팅, 운영 로그 메타, state handler, scale-in 관련 검증 포함 |
| 원격 `.venv` pytest | `74 passed` | 원격 `develop` 기준 관련 스위트 통과 |
| 원격 `py_compile` | `통과` | `ai_engine_openai_v2.py`, `sniper_state_handlers.py` |
| 원격 canary env 반영 | `확인 완료` | `dynamic strength`, `partial fill`, `prompt split`, `WATCHING 75 shadow` 런타임 env 확인 |
| 원격 봇 재기동 | `완료` | `tmux bot`, `python bot_main.py` 상주 확인 |

## 5. 향후 계획표

| 날짜 | 작업 | 목표 산출물 | 승격/판정 기준 |
| --- | --- | --- | --- |
| `2026-04-15 INTRADAY` | 작업 5/8/10 장중 검증 | `action_diverged`, `entry_funnel_delta`, 감사값 입력 표본, `FORCE_EXIT` 입력 정리 | 로그 필드 누락 없음, 위험 알람 없음 |
| `2026-04-15 POSTCLOSE` | shadow 첫 비교표, 작업 8/10 결과 정리 | `WATCHING shared prompt` 1차 비교표, 감사값/override 진행 결과 메모 | 실표본 확보 여부와 추가 canary 필요성 판정 |
| `2026-04-16` | 작업 5/8/10 승격 가능/불가 판정 | 항목별 `main` 승격 초안 | 표본, 퍼널, 리스크 기준 충족 시에만 승격 |
| `2026-04-17` | 작업 9 helper scope 확정 | 정량형 수급 피처 1차 helper 확정안 | helper write scope/rollback 명확화 |
| `2026-04-18` | 작업 9 착수 | 1차 코드 반영 | 입력 품질 개선이 다른 축과 분리돼야 함 |
| `2026-04-19` | 작업 10 1차 결과 평가 | `FORCE_EXIT` 제한형 MVP 평가표 | override 확대/유지/보류 판정 |

## 6. 감사인 확인 포인트

| 확인 항목 | 감사 관점 질문 | 현재 답변 |
| --- | --- | --- |
| 프롬프트 분리 | 진입판단과 보유판단이 여전히 같은 질문 구조인가 | 아니오. 코드 경로 분리 착수 완료, 장중 실표본 검증만 남음 |
| shadow 비교 | Gemini와 OpenAI를 실주문에 직접 연결했는가 | 아니오. `WATCHING shared prompt shadow`는 shadow-only다 |
| hybrid override | `SELL/FORCE_EXIT`를 무제한 적용했는가 | 아니오. 일반 `HOLDING`의 `FORCE_EXIT` 제한형 MVP만 검토 중이며 로그 우선 원칙 유지 |
| 승격 통제 | `main`에 선반영했는가 | 아니오. `develop` 선행 적용 후 `2026-04-16` 이후 승격 판정 원칙 유지 |
| EV 관점 | 단순 손실 억제 중심으로 설계했는가 | 아니오. `partial fill`, `missed opportunity`, `counterfactual`을 함께 보도록 설계 유지 |

## 7. 현재 실제 프롬프트

### 7-1. 진입 프롬프트 (`WATCHING`)

현재 코드 기준 `WATCHING` 실제 프롬프트는 아래와 같다.

```text
너는 극강 공격적 초단타 진입 트레이더다.
목표는 '지금 이 순간 진입해도 기대값이 플러스인지'만 판단하는 것이다.
이미 통과한 기계 게이트(유동성/갭/모멘텀)는 다시 의심하지 말고, 돌파 지속 가능성만 본다.

[진입 판단 규칙]
1. 즉시 돌파 지속 가능성이 높으면 BUY.
2. 애매하면 WAIT.
3. 돌파 실패/흡수 실패/속도 둔화가 보이면 DROP.

[스코어링 기준 (0~100)]
- 80~100 (BUY): 즉시 진입 유효
- 50~79 (WAIT): 관찰 유지
- 0~49 (DROP): 진입 금지

분석 결과는 반드시 아래 JSON 형식으로만 출력:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "진입 관점 핵심 근거 1줄"
}
```

감사인 질의 포인트:

| 점검 항목 | 질문 포인트 |
| --- | --- |
| 기계 게이트 재판단 금지 | 실제로 필요한 보호논리까지 누락시키는지 |
| `BUY/WAIT/DROP` 3분기 | 진입 보류와 진입 금지의 구분이 충분히 선명한지 |
| `reason` 1줄 제한 | 감사/사후분석에 필요한 설명력이 부족하지 않은지 |
| 점수구간 | `80/50` 경계값이 현재 EV 기준에 맞는지 |

### 7-2. 보유 프롬프트 (`HOLDING`)

현재 코드 기준 `HOLDING` 실제 프롬프트는 아래와 같다.

```text
너는 초단타 보유 포지션 리스크 매니저다.
목표는 '추세 유지 vs 즉시 이탈'을 빠르게 판정하는 것이다.
청산 action schema가 아직 분리되지 않았으므로, 현재는 BUY/WAIT/DROP 중 DROP을 사실상 EXIT 신호로 사용한다.

[보유 판단 규칙]
1. 추세 유지/재가속이면 WAIT 또는 BUY.
2. 모멘텀 붕괴, 되밀림 심화, 하방 리스크 확대로 즉시 이탈이 유리하면 DROP.
3. reason에는 보유/청산 판단의 핵심 트리거를 명시한다.

[스코어링 기준 (0~100)]
- 80~100: 보유 우호
- 50~79: 중립
- 0~49: 청산 우호(DROP 가능성 높음)

분석 결과는 반드시 아래 JSON 형식으로만 출력:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "보유 관점 핵심 근거 1줄"
}
```

감사인 질의 포인트:

| 점검 항목 | 질문 포인트 |
| --- | --- |
| `DROP=EXIT` 간접 사용 | 전용 청산 action schema 부재가 판단 왜곡을 만드는지 |
| `BUY`와 `WAIT`의 보유 의미 | 실제 보유 연장 결정에서 둘의 차이를 더 분명히 해야 하는지 |
| 하방 리스크 표현 | `모멘텀 붕괴`, `되밀림 심화`가 정량 트리거로 충분히 연결되는지 |
| score/action 결합 | 향후 `FORCE_EXIT` 제한형 hybrid와 어떻게 접합하는 게 맞는지 |

### 7-3. 프롬프트 검토 요청 포맷

감사인에게는 아래 항목을 기준으로 개선 의견을 요청한다.

| 요청 항목 | 요청 내용 |
| --- | --- |
| WATCHING 개선안 | 진입 기대값 극대화 관점에서 `BUY/WAIT/DROP` 규칙, 점수 경계, `reason` 포맷 개선안 |
| HOLDING 개선안 | 보유/청산 판단 정확도 개선을 위한 action schema, score 해석, 리스크 문구 개선안 |
| 공통 개선안 | 정량형 피처를 더 직접적으로 반영하는 문장 구조, 불필요한 모호성 제거안 |
| 감사 관점 경고 | 현재 프롬프트에서 EV 왜곡이나 기회비용 과소평가를 부를 수 있는 표현 |

## 8. 감사인 질의문 초안

아래 질문문은 감사인에게 그대로 전달 가능한 초안이다.

```text
검토 대상:
1. 현재 WATCHING(진입) 실제 프롬프트
2. 현재 HOLDING(보유) 실제 프롬프트
3. 현재 운영 방향: 기대값/순이익 극대화, 미진입 기회비용까지 포함한 해석

질문 1. WATCHING 프롬프트
- 현재 WATCHING 프롬프트가 "즉시 진입 기대값 판단"이라는 목표에 비해 너무 추상적이거나 모호한 표현이 있는지 검토해 주십시오.
- BUY / WAIT / DROP의 경계가 실제 스캘핑 진입 의사결정에서 충분히 선명한지, 아니면 WAIT와 DROP이 과도하게 섞일 위험이 있는지 의견을 부탁드립니다.
- 점수 구간(80/50 기준)이 현재 목적에 맞는지, 또는 기대값 극대화 관점에서 조정이 필요한지 검토해 주십시오.
- `reason` 1줄 구조가 감사/사후복기/실전 로그 관점에서 너무 빈약하지 않은지, 더 나은 출력 포맷이 있다면 제안해 주십시오.

질문 2. HOLDING 프롬프트
- 현재 HOLDING 프롬프트가 DROP을 사실상 EXIT 신호로 간접 사용하고 있는데, 이 구조가 보유/청산 판단을 왜곡할 위험이 있는지 검토해 주십시오.
- HOLDING에서 BUY와 WAIT를 동시에 허용하는 현재 구조가 실제 보유 지속 판단에 도움이 되는지, 아니면 action schema를 더 분리해야 하는지 의견을 부탁드립니다.
- "모멘텀 붕괴", "되밀림 심화", "하방 리스크 확대" 같은 표현이 정량형 트리거로 충분히 연결될 수 있는지, 더 명확한 문장 구조가 필요한지 검토해 주십시오.
- 향후 FORCE_EXIT 제한형 hybrid(action+score) 구조와 결합할 때 가장 위험한 설계 함정이 무엇인지 지적해 주십시오.

질문 3. 공통 구조
- WATCHING과 HOLDING 프롬프트가 현재 수준에서 충분히 역할 분리되어 있는지, 아니면 아직도 질문 구조가 겹치는 부분이 남아 있는지 검토해 주십시오.
- 정량형 피처(예: momentum, buy pressure, retrace, position context)를 더 직접적으로 반영하려면 어떤 질문 구조가 적합한지 제안해 주십시오.
- 현재 프롬프트가 손실 회피에 치우치지 않고 기대값/순이익 극대화를 지향하는지, 또는 보수적으로 흐를 위험이 있는지 평가해 주십시오.

질문 4. 감사 관점 요청
- 현재 문구 중 실전 운용 시 기회비용을 과소평가하거나, 미진입을 과도하게 정당화할 위험이 있는 표현을 지적해 주십시오.
- 반대로 과도한 공격성으로 인해 체결 품질 악화, partial fill 확대, EXIT 지연을 유발할 수 있는 문구가 있는지도 함께 검토해 주십시오.
- 최종적으로 "지금 즉시 수정해야 할 문구", "canary 후 판단할 문구", "그대로 유지해도 되는 문구"로 나누어 제안해 주시면 감사하겠습니다.
```

### 8-1. 감사인 답변 요청 형식

| 항목 | 요청 형식 |
| --- | --- |
| 즉시 수정 필요 | 문구 / 이유 / 수정안 |
| canary 후 판단 | 문구 / 우려 포인트 / 필요한 관측지표 |
| 유지 가능 | 문구 / 유지 이유 |
| action schema 제안 | WATCHING / HOLDING 각각 권장 action set |
| score 체계 제안 | 권장 score band와 해석 기준 |
