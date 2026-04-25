# 스캘핑 AI 프롬프트 튜닝용 AI 코딩 작업지시서

## 목적

본 문서는 스캘핑 자동매매의 `WATCHING/HOLDING` AI 판단 구조를 개선하기 위한 구현 백로그다.  
단, 이 문서는 `즉시 전부 구현` 지시서가 아니라 `원격 단일축 canary` 기준으로 실행 순서를 고정하는 문서다.

핵심 목표는 아래 4가지다.

1. `WATCHING`과 `HOLDING`의 질문 구조를 분리한다.
2. 프롬프트 action/score 정의와 실제 코드 사용 방식을 정합화한다.
3. 정량형 수급 피처와 포지션 컨텍스트를 Gemini 라이브 경로에 단계적으로 연결한다.
4. AI 품질 문제와 출력/운영 안정성 문제를 분리 관측한다.

## 최종 리뷰 기준 반영 요약

`2026-04-11` 최종 리뷰 기준으로 아래 4가지를 고정한다.

1. `SCALP_PRESET_TP SELL` 문제는 `DROP` 단순 정리가 아니라 `의도 확인 후 처리`다.
2. `WATCHING 75 정합화`는 원래 `원격 canary` 후보였지만, `2026-04-13` 기준 `shadow_samples=0` 반복으로 현재 잔여 작업축에서는 제외한다.
3. `HOLDING hybrid(action+score)`는 구현 전에 `override 조건 명세`가 먼저다.
4. `프롬프트 분리`와 `컨텍스트 주입`은 같은 단계로 묶지 않고 `순차 진행`한다.

## 공통 구현 원칙

1. 한 번에 한 축씩만 바꾼다.
2. 로그 스키마를 먼저 확장하고, 기능 변경은 그 다음에 한다.
3. 본서버는 현행 점검계획을 유지하고, 프롬프트 구조 변경은 원격/shadow에서 먼저 검증한다.
4. `main` 반영 예정 프롬프트 축은 원격 `develop`에 `1~2일 선행` 적용을 기본값으로 한다.
5. OpenAI v2는 엔진 교체 대상이 아니라 `공통 feature helper` 추출 후보로 사용한다.
6. 기존 fallback/보호선/하드스탑 로직은 한 번에 재설계하지 않는다.
7. raw 입력 축소는 `정량 피처 추가 후` A/B로만 진행한다.

## 이번 작업에서 하지 말 것

- `SELL` action을 공유 프롬프트에 즉시 추가
- WATCHING 75 정합화를 본서버에 즉시 반영
- HOLDING action-only 청산 전환
- raw 시퀀스/호가 원본 즉시 대거 제거
- OpenAI 라이브 엔진 즉시 전환
- 본서버 즉시 프롬프트 구조 변경

## 현재 상태

- 팩트 리포트/전문가 검토/운영자 검증 문서 작성 완료
- 프롬프트 개선 코드 변경은 아직 미착수
- 라이브 스캘핑은 여전히 `SCALPING_SYSTEM_PROMPT` 공용 구조
- 따라서 현재 단계는 `설계 검증 완료 -> 구현 순서 고정 -> 원격 canary 준비` 상태다
- 단, `작업 3 HOLDING hybrid override 조건 명세`는 `문서 명세 작업`과 `후속 구현 작업`을 분리해서 관리한다.
- `작업 3` 자체는 오늘 문서 명세를 닫고, 실제 구현 착수는 `작업 10 HOLDING hybrid 적용`과 이후 체크리스트에서 추적한다.

## 예정 일정 (2026-04-14 공격 재고정)

1. `2026-04-14 POSTCLOSE`
   - `작업 5 WATCHING/HOLDING 프롬프트 물리 분리`, `작업 8 감사용 핵심값 3종 투입`, `작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP는 같은 날 바로 착수한다
   - `작업 10`의 최소 구현 범위(MVP)와 rollback 가드를 같은 날 확정한다
   - 오늘 미착수 항목이 생기면 `사유 + 다음 실행시각`을 남기되 기본값은 미루지 않고 착수다
   - 이 날 착수하는 축은 모두 `develop` 선행 적용 대상으로 간주하고, `main` 반영 목표일을 함께 기록한다
2. `2026-04-15`
   - `작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 구현 진행 / 로그 비교축 확인
   - `작업 8 감사용 핵심값 3종 투입`은 전일 착수분을 이어서 구현/검증한다
   - `작업 10 HOLDING hybrid 적용`은 전일 착수분 `FORCE_EXIT` 제한형 MVP를 이어서 구현한다
   - `main`에는 아직 올리지 않고, 원격 `develop` 장후 결과로 승격 가능/불가 초안을 만든다
3. `2026-04-16`
   - `P1` 원격 canary 1차 결과 평가
   - `작업 10`의 `FORCE_EXIT` 제한형 MVP를 canary-ready 상태까지 밀고, `작업 9` helper scope 초안을 닫는다
   - `작업 5/8/10`은 이날 `main` 승격 가능/불가를 항목별로 판정한다
4. `2026-04-17`
   - `작업 6 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록
   - `작업 7 WATCHING 선통과 조건 문맥 주입` 착수 또는 보류 사유 기록
   - `작업 9` helper scope 확정 및 착수 준비 마감
5. `2026-04-18`
   - `작업 9 정량형 수급 피처 이식 1차` 착수
6. `2026-04-19`
   - `작업 10 HOLDING hybrid 적용` 1차 결과 평가 / 확대 여부 판정
7. `2026-04-20`
   - `작업 11 HOLDING critical 전용 경량 프롬프트 분리` 착수
8. `2026-04-21`
   - `작업 12 Raw 입력 축소 A/B 점검` 범위 확정
9. `2026-04-22`
   - `작업 11 HOLDING critical 전용 경량 프롬프트 분리` 착수
   - 미완료 시 보강 실행

운영 원칙:
- 이 일정은 `RELAX-LATENCY/RELAX-DYNSTR` 실전축과 분리된 `프롬프트 전용 일정`이다.
- 오늘 가능한 `P1` 작업은 같은 날 바로 착수하고, 미착수 시 사유와 다음 실행시각을 남긴다.
- `작업 10`은 더 이상 후순위로 미루지 않는다. `2026-04-14 POSTCLOSE`에 `FORCE_EXIT` 제한형 MVP부터 구현을 시작한다.
- `작업 6`은 `착수 여부 판정`으로 끝내지 않는다. `착수` 또는 `보류 사유 기록` 둘 중 하나가 필요하다.
- `작업 7`은 `작업 6`과 독립 일정으로 관리하고, 같은 날 병렬 착수 가능하다.
- `작업 8`은 `P2 이후`로 미루지 않는다. `2026-04-14 POSTCLOSE`에 바로 착수하고, 미착수 시 사유와 다음 실행시각을 남긴다.

## 작업 우선순위 요약

| 우선순위 | 작업명 | 성격 |
| --- | --- | --- |
| `P0` | `SCALP_PRESET_TP SELL` 의도 확인 | 설계 확인 |
| `P0` | AI 운영계측 추가 | 관측 보강 |
| `P0` | HOLDING hybrid override 조건 명세 | 선행 설계 |
| `P1` | WATCHING/HOLDING 프롬프트 물리 분리 | 구조 개선 |
| `P2-A` | HOLDING 포지션 컨텍스트 주입 | 데이터 연결 |
| `P2-B` | WATCHING 선통과 문맥 주입 | 데이터 연결 |
| `P3` | 감사 3값 + 정량형 수급 피처 이식 | 입력 품질 개선 |
| `P4` | HOLDING hybrid 적용 | 의사결정 개선 |
| `P5` | HOLDING critical 경량 프롬프트 + raw 축소 A/B | 속도 개선 |

---

## P0. 즉시 착수 가능한 확인/계측

## 작업 1. `SCALP_PRESET_TP SELL` 의도 확인

### 목표
현재 코드의 `SELL` 비교가 단순 잔재인지, 향후 HOLDING 전용 action 체계를 염두에 둔 흔적인지 먼저 확인한다.

### 현재 문제

- 코드: `if ai_action in ['SELL', 'DROP']`
- 현재 프롬프트: `BUY | WAIT | DROP`
- 즉 `SELL`은 현재 프롬프트에서 절대 나오지 않는다.

### 확인 절차

1. `git log`, `git blame`로 도입 시점과 변경 맥락 확인
2. 필요 시 설계 메모 또는 코드 주석으로 의도 보존
3. 그 후 아래 둘 중 하나를 선택
   - 의도 없음: `SELL` 제거 + 이유 주석화
   - 향후 HOLDING 분리용 흔적: 주석 보존 후 임시 정리

### 현재 권고

- 즉시 `SELL` 추가는 하지 않는다.
- 즉시 `DROP`만으로 기계 정리하지도 않는다.
- 이 항목은 `버그 수정`보다 `의도 확인 후 정리`로 처리한다.

### 2026-04-12 확인 결과

- `SELL` 비교는 `2026-04-01` 상태핸들러 분리 시점에 함께 들어온 placeholder다.
- 현재 공유 `SCALPING_SYSTEM_PROMPT`는 여전히 `BUY | WAIT | DROP`만 허용하므로 라이브 경로에서 `SELL`은 실질적으로 비도달 상태다.
- 따라서 현 단계 판정은 `즉시 제거`가 아니라 `향후 HOLDING/exit 전용 action schema 대비 placeholder 보존 + 주석/로그 명시`가 맞다.
- 실제 운영 로그에는 `ai_action_raw`, `ai_action_used_for_exit`를 남겨 향후 전용 action 체계 분리 전후를 비교 가능하게 유지한다.

### 2026-04-13 POSTCLOSE 운영 재확인

- `15:40~16:10` workorder 기준으로 재확인했고, 오늘 장후에도 `SELL`을 실제 실집행 action으로 승격할 근거는 추가되지 않았다.
- 오늘 우선순위는 `RELAX-LATENCY` 관찰과 `post-sell / hard stop taxonomy` 해석 보강이므로, 이 항목은 `placeholder 보존 + 운영 로그 비교축 유지`로 계속 닫는 것이 맞다.
- 다음 구현 액션은 `SELL` 제거가 아니라 `HOLDING 전용 action schema`가 실제로 분리될 때 `ai_action_schema_version`과 함께 canary 비교축으로 묶는 것이다.
- 자동동기화 상태: Done

### 로그/산출물

- `ai_action_schema_version`
- `ai_action_used_for_exit`
- `ai_action_raw`
- `ai_reason_raw`
- 설계 메모 또는 코드 주석 1건

---

## 작업 2. AI 운영계측 추가

### 목표
AI 모델 품질과 출력/운영 안정성 문제를 분리해서 본다.

### 필수 계측 항목

- `ai_parse_ok`
- `ai_parse_fail`
- `ai_fallback_score_50`
- `ai_response_ms`
- `ai_prompt_type`
- `ai_score_raw`
- `ai_score_after_bonus`
- `entry_score_threshold`
- `big_bite_bonus_applied`
- `ai_cooldown_blocked`

### 경로별 집계 대상

- WATCHING
- HOLDING
- HOLDING critical
- SCALP_PRESET_TP

### 완료 기준

- parse fail 비율과 fallback 50 비율이 일별 집계된다
- Big-Bite 가점 전후 점수 분포가 분리 집계된다
- AI_WATCHING_COOLDOWN으로 인한 missed opportunity 추정이 가능하다

### 2026-04-12 운영계측 반영 범위

- `analyze_target` 결과에 아래 운영 메타를 공통 부착한다.
  - `ai_parse_ok`
  - `ai_parse_fail`
  - `ai_fallback_score_50`
  - `ai_response_ms`
  - `ai_prompt_type`
  - `ai_result_source`
- `ENTRY_PIPELINE`에는 아래 값을 함께 남긴다.
  - `ai_score_raw`
  - `ai_score_after_bonus`
  - `entry_score_threshold`
  - `big_bite_bonus_applied`
  - `ai_cooldown_blocked`
- `HOLDING_PIPELINE`에는 아래 값을 함께 남긴다.
  - `ai_score_raw`
  - `ai_score_after_bonus`
  - `ai_action_raw`
  - `ai_reason_raw`
  - `ai_action_used_for_exit`
- 해석 원칙:
  - `score == 50` 자체를 품질문제로 단정하지 않는다.
  - `ai_fallback_score_50=true`와 `ai_parse_fail=true`를 분리해 본다.
  - 휴장일/쿨다운/경합으로 AI 호출이 생략된 경우는 `ai_result_source`로 분리한다.

### 2026-04-13 10:03 KST 운영 로그 확인

- `data/pipeline_events/pipeline_events_2026-04-13.jsonl` 기준으로 `ENTRY_PIPELINE`에 운영계측 필드가 실제 기록되고 있다.
- 확인된 대표 필드:
  - `ai_score`
  - `momentum_tag`
  - `threshold_profile`
  - `overbought_blocked`
  - `blocked_stage`
- 아직 `submitted/holding_started` 표본은 없어 체결 이후 품질 검증은 장후까지 추가 관찰이 필요하다.

### 2026-04-13 13:39 KST 운영계측 완료 확인

- 운영계측 필드(`ai_parse_ok`, `ai_parse_fail`, `ai_fallback_score_50`, `ai_response_ms`, `ai_prompt_type`, `ai_score_raw`, `ai_score_after_bonus`, `entry_score_threshold`, `big_bite_bonus_applied`, `ai_cooldown_blocked`)가 `ENTRY_PIPELINE` 및 `HOLDING_PIPELINE`에 정상 기록 중.
- parse fail 비율, fallback 50 비율, Big-Bite 가점 전후 점수 분포 일별 집계 가능.
- AI_WATCHING_COOLDOWN에 의한 missed opportunity 추정 가능.
- 따라서 **작업 2 AI 운영계측 추가**는 구현 완료 상태로 판정. GitHub Project에서 `상태=Done`으로 전환 대상.
- 자동동기화 상태: Done

---

## 작업 3. HOLDING hybrid override 조건 명세

### 목표
`score + action + reason` 혼합형 도입 전에, action이 score를 언제 override하는지 먼저 문서화한다.

### 문서화 필수 항목

1. `FORCE_EXIT` override 조건
2. `SELL` override 조건
3. `smoothed_score` 우선 유지 조건
4. `reason` 로그 전용 조건
5. `SCALP_PRESET_TP`와 일반 HOLDING의 차등 규칙

### 예시 형식

```text
[override rule]
- FORCE_EXIT + profit_rate >= X : 즉시 청산
- SELL + peak_profit_retrace >= Y : 즉시 청산
- 그 외 : 기존 smoothed_score 유지
```

### 완료 기준

- 구현 전에 override 기준표가 별도 문서 또는 본 문서 부속 섹션으로 확정된다
- 원격 canary 결과를 `action 효과`와 `score 효과`로 분리 해석할 수 있다

### 2026-04-12 override 기준표 초안 고정

#### 기본 원칙

1. 기본 결정권은 `smoothed_score`에 둔다.
2. `action`은 모든 경우에 즉시 집행하지 않고, 문서화된 특정 예외에서만 override한다.
3. `reason`은 집행조건이 아니라 운영 로그/사후 리뷰 근거로만 쓴다.
4. `SCALP_PRESET_TP`는 일반 HOLDING보다 더 공격적이되, 전용 action schema 도입 전까지는 `DROP`만 실집행 신호로 본다.

#### override rule v1

```text
[override rule v1]
- FORCE_EXIT:
  profit_rate > 0 이고 peak_profit_retrace_pct >= 0.6 이면서 orderbook/tape 악화가 동반되면 즉시 청산 후보
- SELL:
  일반 HOLDING에서는 즉시 집행 금지
  최소 canary 단계에서는 "강한 경고 action"으로만 기록하고 score/시장상태와 함께 본다
- DROP:
  SCALP_PRESET_TP 전용 검문에서는 즉시 청산 허용
- smoothed_score 유지:
  명시 override 조건을 충족하지 않으면 기존 smoothed_score 기반 청산 로직 유지
- reason:
  exit_rule 선택 근거와 사후 리뷰 태그로만 사용
```

#### 경로별 차등 규칙

1. `SCALP_PRESET_TP`
   - `DROP` 즉시 청산 허용
   - `SELL`은 placeholder로 기록만 하고, 전용 schema 도입 전까지는 실질적으로 비도달
2. 일반 `HOLDING`
   - `FORCE_EXIT`만 즉시 청산 후보
   - `SELL`은 최소 1차 canary에서는 로그 우선, 점수/보호선과 교차 확인
3. `HOLDING critical`
   - 전용 프롬프트 분리 후 재정의
   - 현재 문서 기준으로는 일반 HOLDING과 동일 원칙 적용

### 2026-04-13 POSTCLOSE 운영 재확인

- `15:40~16:10` workorder 기준 재확인 결과, 오늘 `holding_events=0`이라 action override를 실거래 표본으로 재평가할 수는 없었다.
- 따라서 판정은 `override rule v1 유지`다.
- 다음 액션은 `FORCE_EXIT` 실표본 또는 `SCALP_PRESET_TP DROP` 표본이 쌓일 때만 원격 canary로 좁혀 검증하는 것이며, 일반 `SELL`은 계속 로그 우선으로 본다.
- 판정 정리:
  - `작업 3` 범위인 `override 조건 명세`는 오늘 시점으로 완료 처리한다.
  - 실제 구현은 `작업 10 HOLDING hybrid 적용`의 착수/보류 판단에서 별도로 추적한다.
- 후속 구현 일정:
  - `2026-04-16`에는 `작업 10` 착수 준비 입력을 닫고,
  - `2026-04-21` 이내 `작업 10 HOLDING hybrid 적용` 착수 또는 보류 사유를 문서에 남긴다.
- 자동동기화 상태: Done

---

## P1. 원격 canary 대상 판단 기준/구조 변경

## 작업 4. WATCHING 75 정합화 원격 canary

### 목표
프롬프트 설명과 실제 라이브 기준의 불일치를 줄인다.

### 현재 문제

- 프롬프트: `80~100 = BUY`
- 라이브 기준: `score >= 75`

### 주의

이 작업은 `문구 수정`처럼 보이지만 실제로는 AI score/action 분포를 바꿀 수 있다.  
따라서 `즉시 병합`이 아니라 `원격 canary`가 맞다.

### 구현 옵션

#### 옵션 A
- 프롬프트 구간을 `75~100 = BUY`, `50~74 = WAIT`, `0~49 = DROP`으로 변경

#### 옵션 B
- 실제 진입 기준을 `>= 80`으로 상향

### 현재 권고

- `80` 상향은 하지 않는다.
- 다만 `75` 정합화도 본서버 즉시 반영은 금지한다.
- `원격 canary`에서만 반영하고 score/action 분포 변화를 본다.

### 2026-04-12 canary 구현 기준

- 본서버 라이브 판정은 기존 `80~100 BUY` 공유 프롬프트를 유지한다.
- 대신 원격/실험 환경에서만 `AI_WATCHING_75_PROMPT_SHADOW_ENABLED=true`를 켜면,
  `75~79` 경계구간의 `WAIT/DROP` 응답에 한해 `75~100 BUY` shadow 프롬프트를 1회 추가 호출한다.
- shadow 결과는 `ENTRY_PIPELINE stage=watching_prompt_75_shadow`로만 기록하고, 실주문 로직에는 연결하지 않는다.
- 비교 핵심:
  - `main_action/main_score`
  - `shadow_action/shadow_score`
  - `buy_diverged`
  - `ai_response_ms`

### 완료 기준

- 75~79 구간의 action/score 분포 변화가 리포트로 남는다
- `entry_armed -> submitted` 전환과 missed-winner 분포를 같이 비교할 수 있다

### `2026-04-12` 원격 활성화 메모

- `songstockscan` 원격에는 작업 4 최소 패치(`ai_engine.py`, `sniper_state_handlers.py`, `constants.py`)를 선별 반영했다.
- `run_bot.sh`에 shadow env export를 추가해 다음 거래일 `07:40 KST` cron `tmux bot` 기동 시 자동 활성화되게 맞췄다.

### `2026-04-13` 작업축 재분류

- `2026-04-25 KST` 기준 `watching_prompt_75_shadow` 런타임/상수/전용 report/check script는 코드베이스에서 제거됐다. 아래 내용은 historical implementation note로만 본다.
- `2026-04-10`, `2026-04-13` 모두 `shadow_samples=0`, `buy_diverged=0`, `joined_missed_rows=0`이었다.
- 따라서 이 축은 **현재 잔여 작업축에서 제외**한다.
- 재오픈 조건:
  - 실제 shadow 표본이 누적되거나
  - `75~79` 경계구간이 실거래 로그에서 다시 의미 있게 잡힐 때
- 자동동기화 상태: Deferred
- `korstockscan-gunicorn.service.d/override.conf`에도 동일 env를 주입해 운영 환경 변수 정렬을 맞췄다.
- 추가 보정:
  - 초기 구현에는 `AI_WATCHING_75_PROMPT_SHADOW_*` env를 `TRADING_RULES`가 읽지 않는 훅 누락이 있어, `constants.py`의 env override 경로를 함께 보강했다.

### 집계 스크립트

- 파일: `src/engine/watching_prompt_75_shadow_report.py`
- 기본 입력:
  - `data/pipeline_events/pipeline_events_<date>.jsonl`
  - 선택: `missed_entry_counterfactual` JSON 또는 런타임 재계산
- 산출:
  - `buy_diverged` 건수/비율
  - `75~79` score band 분포
  - `buy_diverged x MISSED_WINNER`
  - `score_band x MISSED_WINNER`

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.watching_prompt_75_shadow_report \
  --date 2026-04-13 \
  --data-dir data \
  --json-output tmp/watching_prompt_75_shadow_2026-04-13.json \
  --markdown-output tmp/watching_prompt_75_shadow_2026-04-13.md
```

- 원격 fetch 산출물을 바로 볼 때는 `--data-dir tmp/remote_2026-04-13/data`처럼 바꿔서 사용한다.

### `2026-04-13 10:43 KST` 장중 관찰 메모

- `src.engine.watching_prompt_75_shadow_report` 기준 오늘 현재 `shadow_samples=0`이다.
- 원인은 기능 미기동보다 `트리거 band 미도달` 쪽이 강하다.
- `ai_confirmed` 최근 3일 분포:
  - `2026-04-09`: `ai_confirmed=339`, `WAIT 65=92`, `BUY 85=11`, `BUY 92=9`, `eligible_shadow(75~79)=0`
  - `2026-04-10`: `ai_confirmed=568`, `WAIT 65=168`, `BUY 85=16`, `BUY 92=5`, `eligible_shadow(75~79)=1`
  - `2026-04-13 10:39 기준`: `ai_confirmed=88`, `WAIT 65=26`, `BUY 92=3`, `fallback50=4`, `eligible_shadow(75~79)=0`
- 해석:
  - 분포가 `WAIT 65`와 `BUY 85/92`로 양극화돼 있어 `75~79 WAIT/DROP` 경계구간 표본이 거의 없다.
  - 따라서 지금 `shadow 하한을 60/55로 즉시 낮추는 변경`은 보류가 맞다.
  - 먼저 `3일 히스토그램 반복성`, `WAIT 65 -> MISSED_WINNER` 연결, `fallback50` 원인을 더 본 뒤 다음 축으로 넘긴다.
- 추가 메모:
  - 최근 3일 `WAIT 65`는 총 `286건`, 이 중 `missed_entry_counterfactual`에 붙은 표본 `85건`에서 `MISSED_WINNER=62`, `AVOIDED_LOSER=20`, `NEUTRAL=3`이다.
  - 오늘 `fallback50` 표본 `4건`은 모두 `ai_result_source=cooldown`이라 파싱 실패보다 쿨다운 경로로 읽는 것이 맞다.
  - `작업 5 WATCHING/HOLDING 프롬프트 물리 분리`는 `작업 4` 표본과 분리해 즉시 착수한다.

### `2026-04-13 10:50 KST` WAIT 65 통합 권고 반영

- `WAIT 65`는 `AI threshold miss` 단독 문제로 보지 않는다.
- 현재 우선순위:
  1. `latency_block`
  2. `blocked_strength_momentum`
  3. `overbought` 후순위
- 즉시 개선축:
  - `quote_stale=False` 중심 `latency canary`
  - 단, 전면 완화가 아니라 `latency_state_danger` 하위 이유(`quote_stale / ws_age / ws_jitter / spread`)를 로그에 분리하고, 필요 시 canary를 reason allowlist로 더 좁게 제어한다.
- 병행 분석 범위:
  - `WAIT 65 + latency_block`: `quote_stale / ws_jitter / armed_expired_after_wait`
  - `WAIT 65 + blocked_strength_momentum`: `below_window_buy_value / below_buy_ratio / below_strength_base`
- 보류:
  - `WAIT 65` 전면 완화
  - `shadow 하한 60/55` 조정 선행
  - `overbought` 우선 완화

### `2026-04-13 12:51 KST` 운영계측 확인 메모

- `ENTRY_PIPELINE` 기준 오늘 현재 운영계측 필드가 실제로 누적되고 있다.
- 확인된 항목:
  - `ai_parse_ok / ai_parse_fail / ai_fallback_score_50 / ai_response_ms / ai_prompt_type / ai_result_source`
  - `momentum_tag / threshold_profile / blocked_stage / overbought_blocked`
  - `latency_danger_reasons`
- 해석:
  - `작업 2 AI 운영계측 추가`는 장중 운영 로그 기준으로 유효하다.
  - 특히 `latency_danger_reasons`가 `ws_jitter_too_high / other_danger / ws_age_too_high / spread_too_wide / quote_stale`로 실제 누적돼 `WAIT 65 + latency_block` 하위 분해에 바로 사용할 수 있다.

---

## 작업 5. WATCHING/HOLDING 프롬프트 물리 분리

### 목표
`WATCHING`과 `HOLDING`이 다른 질문을 하도록 호출 구조를 분리한다.

### 구현 내용

- `SCALPING_WATCHING_SYSTEM_PROMPT`
- `SCALPING_HOLDING_SYSTEM_PROMPT`

### 이번 단계의 범위

- `호출 분기`와 `질문 구조`만 바꾼다.
- 입력 데이터 payload는 최대한 기존 유지로 묶는다.
- 즉, 이 단계에서는 컨텍스트 주입을 같이 하지 않는다.

### 적용 경로

- 일반 HOLDING AI 리뷰
- WATCHING 진입 판단
- `SCALP_PRESET_TP`는 의도 확인 후 분기 연결 여부를 결정

### 참고 설계안

- 북극성 문서: [2026-04-13-scalping-holding-prompt-final-design.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-13-scalping-holding-prompt-final-design.md)
- 해석 원칙:
  - 최종 설계안은 목표 구조와 장기 적용 순서를 설명하는 문서다.
  - 실제 구현은 아래 `P1 전용 실행 범위`만 수행하고, `P2~P5`는 본 문서의 후속 작업으로 분리한다.

### P1 전용 실행 범위

1. `ai_engine.py`
   - `SCALPING_SYSTEM_PROMPT`는 유지한다.
   - `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_HOLDING_SYSTEM_PROMPT`를 추가한다.
   - prompt router는 `WATCHING` vs `HOLDING` 2갈래만 만든다.
2. `sniper_state_handlers.py`
   - 일반 HOLDING AI 리뷰 구간만 새 HOLDING 프롬프트를 사용하게 분기한다.
   - WATCHING 진입 판단은 새 WATCHING 프롬프트를 사용하되 기존 payload/threshold/bonus 로직은 유지한다.
3. `로그`
   - `ai_prompt_type`
   - `ai_prompt_version`
   - 최소 위 2개는 WATCHING/HOLDING 모두 남긴다.

### 이번 단계에서 하지 말 것

- `holding_context` 신규 인자 추가
- `holding_general`, `holding_critical`, `preset_tp` cache profile 확장
- `SCALP_PRESET_TP`를 `EXTEND/EXIT` schema로 전환
- 공통 feature helper 추출
- raw payload 제거 또는 최소셋 formatter 도입
- `FORCE_EXIT/SELL` override helper 연결

### 후속 작업 연결

- `작업 6`: HOLDING 포지션 컨텍스트 주입
- `작업 8/9`: 감사값 + 공통 feature helper 이식
- `작업 10`: hybrid override 제한 연결
- `작업 11/12`: HOLDING critical + raw 축소 A/B
- `PRESET_TP EXTEND/EXIT`: 위 단계 관측 후 별도 canary

### 완료 기준

- WATCHING/HOLDING이 서로 다른 프롬프트 상수를 사용한다
- prompt version 로그가 남는다
- payload 변경 없이 `분리 자체의 효과`를 원격에서 1축 관측할 수 있다
- `작업 6~12` 범위가 이번 패치에 섞이지 않는다

### `2026-04-14 POSTCLOSE` 확정/착수 메모

- write scope:
  - `src/engine/ai_engine.py`: `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_HOLDING_SYSTEM_PROMPT`, prompt router 추가
  - `src/engine/sniper_state_handlers.py`: WATCHING/HOLDING 호출 분기 연결
- rollback 가드:
  - `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=false` 1개 토글로 기존 `SCALPING_SYSTEM_PROMPT` 단일 경로로 즉시 복귀
- `main`은 `develop` shadow 비교 전 승격 금지
- 비교지표:
  - `ai_prompt_type`, `ai_prompt_version`, `action_diverged_rate`, `entry_funnel_delta(submitted/entered/holding_started)`
  - 장후 비교는 `WATCHING shared prompt shadow` 기준 `Tier2 Gemini Flash` vs `GPT-4.1-mini` counterfactual 결과로 묶는다
- `2026-04-15 07:51 KST` 구현 착수 메모:
  - `handle_watching_state()` 직후 `watching_shared_prompt_shadow` 비동기 로그 경로를 추가했다.
  - 공통 로그 필드는 `gemini_action`, `gemini_score`, `gpt_action`, `gpt_score`, `action_diverged`, `score_gap`, `gpt_model`, `shadow_extra_ms`로 고정했다.
  - 이 경로는 실주문 비연결 shadow-only다. 장중 첫 표본은 오늘부터 누적하고, `counterfactual` 연결은 장후 비교표에서 계산한다.
- 오늘 착수 정의:
  - write scope/rollback/비교지표를 문서에 고정하고 `2026-04-15 PREOPEN` 코드 반영으로 이어간다
  - `2026-04-14 POSTCLOSE`에 `WATCHING/HOLDING` 프롬프트 상수 분리와 `analyze_target(prompt_profile=...)` 경로를 먼저 반영한다

---

## P2. 컨텍스트 주입 순차 진행

## 작업 6. HOLDING 포지션 컨텍스트 주입

### 목표
AI가 현재 포지션 상태를 이해한 뒤 청산 판단하도록 한다.

### 1차 필수 입력값

- `buy_price`
- `profit_rate`
- `peak_profit`
- `held_sec`
- `position_tag`
- `trailing_stop_price`
- `hard_stop_price`
- `ai_low_score_hits`
- `exit_mode`

### 2차 확장 입력값

- `protect_profit_pct`
- `entry_mode`
- `last_ai_profit`
- `near_ai_exit_band`
- `near_safe_profit_band`

### 구현 위치

- HOLDING용 formatter 분기
- 또는 `cache_profile="holding"` 전용 formatter

### 로그 추가

- `holding_context_payload_version`
- `holding_profit_rate_sent`
- `holding_peak_profit_sent`
- `holding_held_sec_sent`
- `holding_position_tag_sent`

### 완료 기준

- 프롬프트 분리 이후 별도 canary로 payload 추가 효과를 단독 관측 가능

### `2026-04-14` 일정 재고정

- `작업 6`은 `2026-04-17`에 `착수 여부 판정`이 아니라 `착수` 또는 `보류 사유 기록`으로 닫는다.

---

## 작업 7. WATCHING 선통과 조건 문맥 주입

### 목표
AI가 이미 통과한 기계 게이트를 다시 의심하지 않고, 현재 타점 해석에 집중하도록 한다.

### 프롬프트에 추가할 문맥 블록

- 동적 체결강도 PASS 여부
- `window_buy_ratio`
- `window_exec_buy_ratio`
- `threshold_profile`
- 유동성 PASS 및 `liquidity_value`
- 추격률 PASS 및 `gap_pct`
- `target_buy_price`
- `position_tag`
- `momentum_tag`

### 주의

- HOLDING 포지션 컨텍스트 주입과 같은 세션에 묶지 않는다.
- WATCHING payload 추가 효과를 따로 관측한다.

### 로그 추가

- `watching_gate_context_version`
- `watching_target_buy_price_sent`
- `watching_gap_pct_sent`
- `watching_threshold_profile_sent`

### 완료 기준

- gate context 주입 전/후의 action/score 분포와 entry funnel 변화를 따로 비교할 수 있다

### `2026-04-14` 일정 재고정

- `작업 7`은 `작업 6`과 독립적으로 `2026-04-18` 이내 착수한다.

---

## P3. 입력 패킷 보강

## 작업 8. 감사용 핵심값 3종 투입

### 목표
이미 계산 중인 값을 최소 공수로 프롬프트에 반영한다.

### 즉시 추가 대상

- `buy_pressure_10t`
- `distance_from_day_high_pct`
- `intraday_range_pct`

### 구현 원칙

- WATCHING 우선
- HOLDING에는 `distance_from_day_high_pct`, `buy_pressure_10t`부터 반영
- raw 제거 없이 먼저 구조화 값만 추가

### 로그 추가

- `buy_pressure_10t_sent`
- `distance_from_day_high_pct_sent`
- `intraday_range_pct_sent`

### `2026-04-14` 일정 재고정

- `작업 8`은 `P2 이후`로 미루지 않는다.
- `2026-04-14 POSTCLOSE`에 `format_market_data()` 수정 범위를 확정하고, 가능하면 같은 날 바로 착수한다.
- 늦어도 `2026-04-14 POSTCLOSE`에는 구현 착수 상태를 문서에 남긴다.

### `2026-04-14 POSTCLOSE` 착수 메모

- write scope:
  - `WATCHING/HOLDING` 프롬프트 payload 생성부의 `format_market_data()` 경로
  - 감사 3값 주입과 `*_sent` 로그 필드 추가만 이번 착수 범위로 제한
- 오늘 착수 정의:
  - `format_market_data()` 수정 범위 확정
  - `buy_pressure_10t / distance_from_day_high_pct / intraday_range_pct` 주입 포인트와 검증 로그 이름 고정
  - `develop` 선행 적용 후 `2026-04-16` 1차 평가까지 유지
- rollback 가드:
  - `packet_version` 또는 payload 토글 1개로 되돌릴 수 있게 유지
  - 값 계산은 유지하고 프롬프트 주입만 끄는 방향을 기본 rollback으로 쓴다
  - `main` 승격은 `develop` 장후 비교 전 금지

---

## 작업 9. 정량형 수급 피처 이식 1차

### 목표
OpenAI v2 경로의 유효 정량 피처를 `공통 feature helper` 형태로 Gemini 경로에도 공급한다.

### 1차 우선 이식 대상

- `tick_acceleration_ratio`
- `same_price_buy_absorption`
- `large_sell_print_detected`
- `net_aggressive_delta_10t`
- `ask_depth_ratio`
- `net_ask_depth`

### 구현 원칙

- 엔진 클래스 직접 결합 금지
- 공통 helper 또는 util로 추출
- WATCHING/HOLDING에 의미를 동일하게 유지
- 원본 배열 제거 전에 정량값만 먼저 넣는다

### 로그 추가

- `scalp_feature_packet_version`
- `tick_acceleration_ratio_sent`
- `same_price_buy_absorption_sent`
- `large_sell_print_detected_sent`
- `ask_depth_ratio_sent`

### `2026-04-14` 일정 재고정

- `2026-04-17` 이내 helper 추출 범위를 확정한다.
- `2026-04-19` 이내 구현 착수한다.

---

## P4. HOLDING 의사결정 구조 보강

## 작업 10. HOLDING hybrid 적용

### 목표
현재 score-only 구조를 보완해 AI의 청산 의도를 제한적으로 반영한다.

### 전제

- 작업 3의 override 기준 문서화가 먼저 끝나 있어야 한다.

### 현재 구조

- `raw_score` 수신
- `smoothed_score = old*0.6 + new*0.4`
- `action`, `reason`은 주로 로그성

### 적용 원칙

#### 일반 HOLDING

- `score`는 기존처럼 평활화 유지
- 단, 문서화된 override 조건에 한해서만 `action` 직접 반영

#### SCALP_PRESET_TP

- `SELL`/`FORCE_EXIT` 도입 여부는 의도 확인과 전용 프롬프트 분리 이후 확정
- 현재 단계에서 action 확장은 바로 켜지지 않는다

### 로그 추가

- `holding_ai_action`
- `holding_ai_reason`
- `holding_action_applied`
- `holding_force_exit_triggered`
- `holding_override_rule_version`

### 완료 기준

- action override가 어떤 룰로 발동했는지 로그에서 추적 가능하다
- score와 action의 효과를 분리 비교할 수 있다

### `2026-04-14` 일정 재고정

- `작업 10`은 더 이상 `P3 이후` 설명만 두지 않고 `2026-04-14 POSTCLOSE`부터 `FORCE_EXIT` 제한형 MVP를 착수한다.

### `2026-04-14 POSTCLOSE` 착수 메모

- MVP 범위:
  - 일반 `HOLDING`에 한해 `FORCE_EXIT`만 즉시집행 후보로 연결
  - 일반 `SELL`은 계속 로그 우선으로 유지
  - `SCALP_PRESET_TP`는 이번 MVP에서 실집행 확장 제외
- rollback 가드:
  - `holding_override_rule_version` 기준으로 `FORCE_EXIT` 제한형 룰만 on/off 가능해야 한다
  - `holding_action_applied=False` 기본 경로를 남겨 action 미적용 fallback을 즉시 복구점으로 사용한다
  - `develop`에서만 먼저 검증하고 `main`은 `2026-04-16` 장후 판정 전 열지 않는다
- 오늘 착수 정의:
  - override 적용 범위, 로그 필드, canary-ready 입력을 같은 날 문서/코드 기준으로 고정
  - 미착수 시 `사유 + 다음 실행시각`을 남기되 기본값은 착수다

---

## P5. 속도/안정성 개선

## 작업 11. HOLDING critical 전용 경량 프롬프트 분리

### 목표
3~10초 재검토 구간에서 토큰 수를 줄이고 응답 일관성을 높인다.

### 적용 대상

- `profit_rate >= 0.5%`
- 또는 `profit_rate < 0`

### 입력 최소셋

- `profit_rate`
- `peak_profit`
- `held_sec`
- `position_tag`
- `tick_acceleration_ratio`
- `buy_pressure_10t`
- `ask_depth_ratio`
- `large_sell_print_detected`
- `net_aggressive_delta_10t`

### 운영 원칙

- 일반 HOLDING 프롬프트와 별도 버전 관리
- `holding_critical_prompt_version` 로그 필수

### `2026-04-14` 일정 재고정

- `작업 11`은 `2026-04-20` 이내 착수한다.

---

## 작업 12. Raw 입력 축소 A/B 점검

### 목표
Raw 원본 제거가 정확도 저하 없이 가능한 경로를 찾는다.

### 방식

#### Phase 1
- 정량 피처 추가
- Raw는 유지

#### Phase 2
- HOLDING critical부터 Raw 제거
- WATCHING은 유지

#### Phase 3
- 일반 HOLDING에서 호가 원본 제거 여부 검토

### 비교 기준

- 응답 지연

### `2026-04-14` 일정 재고정

- `작업 12`는 구현까지 한 번에 요구하지 않지만, `2026-04-21` 이내 `범위 확정`은 끝낸다.
- parse fail 비율
- HOLDING 조기청산 비율
- WATCHING 진입 통과율
- realized pnl
- exit quality

---

## 구현 순서 제안

## 1주차

1. `SCALP_PRESET_TP SELL` 의도 확인
2. AI 운영계측 기본 로그 추가
3. HOLDING hybrid override 조건 문서화
4. WATCHING/HOLDING 프롬프트 물리 분리
5. 감사용 핵심값 3종 프롬프트 추가
6. HOLDING hybrid 적용 `FORCE_EXIT` 제한형 MVP

## 2주차

7. HOLDING 포지션 컨텍스트 주입
8. WATCHING 선통과 조건 문맥 주입
9. 정량형 수급 피처 1차 이식
10. HOLDING critical 경량 프롬프트 분리

## 3~4주차

11. Raw 입력 축소 A/B 테스트
12. prompt version / packet version / override version 비교 리포트 생성

## 롤아웃 규칙

1. 본서버 즉시 반영 금지
2. 각 축은 `원격 30~60분 압축 모니터링 + 장후 평가 + 필요 시 1~2세션 추가` 후 판정
3. 프롬프트 분리와 컨텍스트 주입은 반드시 따로 판정
4. score band 정합화와 hybrid 도입은 판단 기준을 바꾸므로 `원격 canary` 외 경로 금지
5. 모든 canary는 `prompt_version / packet_version / override_rule_version`으로 추적 가능해야 한다

## 완료 기준

### 기능 완료 기준

- WATCHING과 HOLDING 프롬프트가 분리되어 있어야 한다
- `SCALP_PRESET_TP SELL` 처리 의도가 문서화되어 있어야 한다
- HOLDING 프롬프트에 포지션 컨텍스트가 실제로 들어가야 한다
- WATCHING 프롬프트에 기계 선통과 조건과 핵심 정량값이 들어가야 한다

### 운영 완료 기준

- parse fail 및 fallback 50 비율이 일별 집계된다
- prompt type별 응답시간이 집계된다
- Big-Bite bonus, cooldown, score threshold 영향이 분리 집계된다
- override rule별 발동 건수가 추적된다

### 검증 완료 기준

- prompt version별 진입률/청산률/실현손익 비교가 가능하다
- HOLDING critical 경량 프롬프트의 응답시간 개선 여부를 수치로 확인할 수 있다
- action 도입 후 조기청산 오탐 비율을 확인할 수 있다

## 최종 지시

이번 작업의 핵심은 프롬프트 문구를 예쁘게 다듬는 것이 아니다.  
핵심은 아래 세 가지를 코드 수준에서 바로잡는 것이다.

1. 진입과 보유에 다른 질문을 하도록 구조를 분리할 것
2. AI가 판단해야 할 수급·포지션 데이터를 실제로 전달할 것
3. AI 응답을 현재 코드가 해석 가능한 구조로 정합화할 것

단, 이 세 가지도 `즉시 전면 반영`이 아니라 `의도 확인 -> 계측 -> 원격 1축 canary -> 장후 판정` 순서로만 진행한다.
