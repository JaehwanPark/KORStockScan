# 보유 중 수익전환 보강 실행 플랜

작성일: 2026-04-16  
근거 문서: `2026-04-16-profit-conversion-gap-analysis.md` (운영자 검증 의견 반영)  
플랜 범위: 관찰축 1~5에 누락된 보유 → 수익전환 구간 전체

---

## 배경 및 전제

### 운영자 검증 의견 요약

| 공백 항목 | 운영자 판정 | 보정 사항 |
|-----------|------------|-----------|
| 보유 AI 수익전환 판단 | **부분보정 필요** | `task_type=scalping_holding` 분기는 존재. 단 전용 action schema(`HOLD/SELL/FORCE_EXIT`) 미분리라 실질 공백은 타당 |
| 포지션 액션 (물타기/피라미딩) | **맞음** | `REVERSAL_ADD_ENABLED=False`, `SCALP_LOSS_FALLBACK_ENABLED=False`, `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True` 전부 비활성 |
| PRESET_TP 최적화 | **대체로 맞음** | EXTEND/EXIT 분리 미완 |
| 동적 목표가 조정 | **맞음** | 운영 경로에 없음 |
| SCANNER 포지션 timeout | **부분보정 필요** | `SCANNER fallback` 한정 never-green/retrace 조기정리 로직은 이미 존재. 일반 SCANNER 장기 표류 확장이 미구현 |

### 현재 파라미터 기준값

```
REVERSAL_ADD_ENABLED          = False
REVERSAL_ADD_MAX_HOLD_SEC     = 120
SCALP_LOSS_FALLBACK_ENABLED   = False
SCALP_LOSS_FALLBACK_OBSERVE_ONLY = True
```

### 현재 구현 정합성 메모

- `SCANNER fallback` 진입(`entry_mode=fallback`)에는 이미 `scalp_scanner_fallback_never_green` / `scalp_scanner_fallback_retrace_exit` 조기정리 로직이 있다.
- `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True` 상태의 `loss_fallback_probe` 관찰은 이미 라이브 경로에서 진행 중이다.
- `REVERSAL_ADD`는 observe-only 전용 플래그가 없어 `REVERSAL_ADD_ENABLED=True`가 곧 실주문 경로 진입을 뜻한다.

### 운영 원칙

1. 모든 신규 활성화는 **원격 shadow → 원격 canary → 메인 canary → 메인 운영반영** 순서를 따른다.
2. 단계 진행 기준은 `판정 → 근거 → 다음 액션`을 명시해야 인정된다.
3. 일정 슬롯: `PREOPEN(08:00~09:00)`, `INTRADAY(09:00~15:30)`, `POSTCLOSE(15:30~)`
4. 동일 일에 복수 축을 동시 운영반영하지 않는다. 원인 귀속을 위해 1일 1축 원칙.

---

## 플랜 전체 로드맵

```
2026-04-17  T1: SCANNER fallback timeout 일반 SCANNER 확장 판정 (원격 shadow 우선)
            T7: SCALP_LOSS_FALLBACK 진행 중 관찰 1차 판정

2026-04-18  T3: HOLDING action schema 분리 설계 착수
            T4: REVERSAL_ADD 기존 후보 로그 1차 판정

2026-04-21  T5: HOLDING_GENERAL 프롬프트 분리 원격 shadow 착수
            T6: REVERSAL_ADD 원격 canary 전환 or 보류 판정
            T7: SCALP_LOSS_FALLBACK 활성화 여부 2차 판정

2026-04-22  T8: HOLDING action schema 원격 shadow 착수

2026-04-23  T9: HOLDING_GENERAL 원격 shadow 1일차 판정

2026-04-24  T10: HOLDING_CRITICAL 프롬프트 설계 착수

2026-04-25  T11: REVERSAL_ADD 메인 canary 전환 판정 (원격 canary 결과 기준)

2026-04-28  T12: PRESET_TP action schema 분리 설계 착수

2026-04-30  T13: 동적 목표가 조정 설계 문서 작성
```

---

## T1 — SCANNER fallback timeout 일반 SCANNER 확장 판정 (2026-04-17 PREOPEN)

### 목적

현재 `SCANNER fallback` 진입에만 있는 never-green/retrace 조기정리 로직을  
일반 SCANNER 장기 표류 포지션까지 확장할지 원격 shadow 우선으로 판정한다.  
롯데쇼핑(74분), 올릭스(36분) 케이스는 fallback 한정 로직으로 직접 커버되지 않았다.

### 구현 범위

`sniper_state_handlers.py` — 기존 `SCALP_SCANNER_FALLBACK_*`와 충돌하지 않도록  
일반 SCANNER 장기 표류 shadow 조건을 별도 `exit_rule`로 추가 검토

```python
# 추가할 파라미터 (constants.py)
SCANNER_NEVER_GREEN_MAX_HOLD_SEC = 1800   # 30분, 기본값
SCANNER_NEVER_GREEN_MAX_PEAK_PCT = 0.0    # peak가 0% 미만
SCANNER_NEVER_GREEN_MAX_AI_SCORE = 55     # AI 점수 기준
```

**청산 트리거 조건:**

```
pos_tag == 'SCANNER'
AND entry_mode != 'fallback'
AND held_sec >= SCANNER_NEVER_GREEN_MAX_HOLD_SEC
AND peak_profit <= SCANNER_NEVER_GREEN_MAX_PEAK_PCT
AND current_ai_score <= SCANNER_NEVER_GREEN_MAX_AI_SCORE
→ exit_rule = 'scanner_never_green_timeout_shadow'
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-17 PREOPEN 08:00~08:30 | 조건/파라미터 설계 + 원격 shadow 반영 여부 판정 |
| 2026-04-17 INTRADAY | 기존 `scalp_scanner_fallback_*`와 신규 `scanner_never_green_timeout_shadow` 후보 로그 병행 확인 |
| 2026-04-17 POSTCLOSE | shadow false-positive 샘플 검토. 승인 시 메인 canary 실행시각 확정 |

### 판정 기준

- `scanner_never_green_timeout_shadow` 이후 가격 흐름이 계속 약세인 표본이 우세 → 원격 shadow 유지 후 메인 canary 시각 확정
- shadow 후보 직후 반등 케이스 2건 이상 → 조건 강화 검토 (`AI_SCORE` 기준 낮추거나 `HOLD_SEC` 늘리기)

---

## T4 — REVERSAL_ADD 기존 후보 로그 1차 판정 (2026-04-18 POSTCLOSE)

### 목적

observe-only 전용 단계를 따로 두지 않고, 현재 라이브 경로에서 이미 남는  
`reversal_add_candidate` 표본과 포지션 수량 분포만으로 원격 canary readiness를 먼저 판정한다.

### 판정 입력

```
1. reversal_add_candidate 발생 건수 / 시간대
2. 후보 시점 buy_qty 분포 (1주 비율이 높으면 실효성 제한)
3. 후보 직후 가격 흐름 샘플
4. add_judgment_locked 및 scale_in qty 제약과의 교차
```

### 관찰 지표

```
1. `buy_qty >= 3` 비율
2. 후보 직후 1~5분 반등 비율
3. 후보 시점 AI 점수 및 profit_rate 분포
4. 실주문 전환 시 포지션 sizing이 가능한지 여부
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-17 POSTCLOSE | 전일 `reversal_add_candidate` / 포지션 수량 로그 집계 |
| 2026-04-18 POSTCLOSE | 1차 판정. `buy_qty >= 3` 비율과 반등 표본 기준으로 T6 입력 확정 |

### 판정 기준

- `buy_qty >= 3` 충족 비율 ≥ 50% → T6(2026-04-21)에서 원격 canary 전환
- `buy_qty >= 3` 충족 비율 < 50% → 진입 체결률 개선 이후 재판정으로 이월

---

## T3 — HOLDING action schema 분리 설계 (2026-04-18 PREOPEN)

### 목적

현재 HOLDING 경로가 `BUY / WAIT / DROP` action을 반환하는 구조적 결함을 해소한다.  
`sniper_state_handlers.py:2884~2886`에 이미 TODO 주석으로 명시된 사항이다.

```python
# 현재 코드 (line 2884~2886):
# Shared scalping prompt still emits BUY|WAIT|DROP today.
# Keep SELL as an explicit placeholder until a dedicated HOLDING/exit action schema lands.
if ai_action in ['SELL', 'DROP']:
```

### 설계 범위

**① 응답 파싱 분리**

```python
# ai_engine_openai_v2.py / ai_engine.py
# cache_profile == "holding" 분기에서 action 해석 분리
HOLDING_SELL_ACTIONS = {'SELL', 'DROP', 'FORCE_EXIT'}   # 청산 신호로 해석
HOLDING_HOLD_ACTIONS = {'HOLD', 'BUY', 'WAIT'}          # 보유 신호로 해석
```

**② 프롬프트 응답 스키마 점진 전환**

- 1단계: 파싱은 양쪽 호환(기존 `DROP/BUY` + 신규 `SELL/HOLD` 동시 수용)
- 2단계: 프롬프트에 `HOLD / SELL / FORCE_EXIT` 명시 추가
- 3단계: 기존 `BUY/WAIT/DROP` 응답 지원 종료

**③ HOLDING 입력 스키마 경량화**

```python
# _format_market_data() holding 분기에서 제거
# - raw 분봉 시계열 (HOLDING에서 불필요)
# - raw 10틱 원본
# 추가
# + 현재 손익률, 보유시간, 고점 대비 되밀림
# + 최근 AI score 이력 (3~5개)
# + 포지션 컨텍스트 (매수가, 수량, 진입모드)
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-18 PREOPEN 08:00~09:00 | 설계 문서 작성, 파싱 양방향 호환 구조 확정 |
| 2026-04-18 POSTCLOSE | 설계 문서 완료, 구현 착수 여부 판정 |
| 2026-04-21 PREOPEN | 원격 shadow 반영 (파싱 호환 + 입력 경량화 1단계) |

### 판정 기준 (2026-04-21)

- parse 에러율이 현행 대비 증가하지 않으면 메인 반영 승인
- `ai_parse_ok=False` 비율이 현행보다 5%p 이상 상승 시 롤백

---

## T5 — HOLDING_GENERAL 프롬프트 분리 원격 shadow (2026-04-21 PREOPEN)

### 목적

`2026-04-13-scalping-holding-prompt-final-design.md` 설계안의 `HOLDING_GENERAL` 경로를  
원격 서버에서 shadow로 먼저 실행한다.

### 분기 조건

```python
# ai_engine.py 또는 ai_engine_openai_v2.py
if cache_profile == "holding":
    if profit_rate < 0 or profit_rate >= 0.5:
        → HOLDING_CRITICAL  (빠른 판단, 최소 입력)
    else:
        → HOLDING_GENERAL   (일반 보유 판단, 포지션 컨텍스트 위주)
```

### HOLDING_GENERAL 입력 구조 (확정안)

```
[system]
당신은 스캘핑 포지션 보유 전담 판단 AI입니다.
신규 진입 여부가 아니라, 지금 보유 중인 포지션을 유지할지 청산할지 판단합니다.

[position_context]
매수가: {buy_price}원 | 수량: {buy_qty}주 | 진입모드: {entry_mode}
현재 손익: {profit_rate}% | 보유시간: {held_sec}초
고점 손익: {peak_profit}% | 고점 대비 되밀림: {drawdown}%

[ai_score_history]
최근 AI 점수 이력 (구→최신): {ai_score_history}

[market_summary]
핵심 수급 수치: {supply_summary}

[response_schema]
action: HOLD | SELL | FORCE_EXIT
score: 0~100
reason: 1줄
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-21 PREOPEN | 원격 HOLDING_GENERAL 프롬프트 shadow 반영 |
| 2026-04-21 POSTCLOSE | parse 에러율, score 분포, action 분포 집계 |
| 2026-04-23 POSTCLOSE | 2일차 판정. parse_ok율 ≥ 95% 이면 canary 전환 |

---

## T6 — REVERSAL_ADD 원격 canary 전환 판정 (2026-04-21 POSTCLOSE)

### 판정 입력

- T4(2026-04-17~18) 기존 후보 로그 판정 결과
- `buy_qty >= 3` 충족 비율
- 충족 시점 이후 가격 흐름 샘플

### 판정 기준

| 조건 | 결정 |
|------|------|
| `buy_qty >= 3` 비율 ≥ 50% AND 충족 후 회복 케이스 ≥ 1건 | 원격 canary 전환 (`REVERSAL_ADD_ENABLED=True`, 실주문) |
| `buy_qty >= 3` 비율 < 50% | 진입 체결률 개선 이후 재판정으로 이월 |
| 충족 건수 0건 | 파라미터 재검토 (`PNL_MIN/MAX` 범위 조정) |

---

## T7 — SCALP_LOSS_FALLBACK 진행 중 관찰 판정 (2026-04-17 PREOPEN 시작)

### 목적

이미 `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True`로 실행 중인 `loss_fallback_probe` 관찰축을  
전일 손절 리뷰와 연결해 후보율, 락 해소 효과, 이후 가격 흐름을 판정한다.  
신규 shadow 시작이 아니라 기존 관찰축 재판정이다.

### 현재 상태 확인

```
SCALP_LOSS_FALLBACK_ENABLED      = False
SCALP_LOSS_FALLBACK_OBSERVE_ONLY = True
SCALP_LOSS_FALLBACK_MIN_AI_SCORE = 65
SCALP_LOSS_FALLBACK_ALLOWED_REASONS = ('reversal_add_ok',)
```

### 관찰 지표

```
1. loss_fallback_probe 발동 건수 / 일
2. fallback_candidate=True 비율
3. gate_reason 분포 (add_judgment_locked 비율 별도 집계)
4. 발동 시점의 이후 가격 흐름
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-17 PREOPEN | `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True` 유지 상태 확인 + 전일 `loss_fallback_probe` 로그 판정 |
| 2026-04-18 POSTCLOSE | 2일차 판정. `fallback_candidate=True` 비율 및 이후 흐름 분석 |
| 2026-04-21 POSTCLOSE | 활성화 여부 최종 판정 |

---

## T8 — HOLDING action schema 원격 shadow (2026-04-22 PREOPEN)

### 목적

T3에서 설계한 파싱 양방향 호환 구조를 원격 shadow로 먼저 적용한다.

### 검증 지표

```
1. ai_parse_ok 비율 (현행 대비 변화)
2. action 분포: HOLD / SELL / FORCE_EXIT / 기타
3. score 분포 변화
4. holding 이벤트당 레이턴시 변화
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-22 PREOPEN | 원격 반영 |
| 2026-04-22 POSTCLOSE | 1일차 지표 집계 |
| 2026-04-23 POSTCLOSE | 판정. parse_ok 현행 대비 -5%p 이상이면 롤백 |
| 2026-04-24 PREOPEN | 메인 shadow 반영 여부 판정 |

---

## T10 — HOLDING_CRITICAL 프롬프트 설계 (2026-04-24 PREOPEN)

### 목적

손실 구간(`profit_rate < 0`) 또는 수익 임박 구간(`profit_rate >= 0.5%`)에서  
3~10초 안에 즉시 탈출 여부를 판단하는 최경량 프롬프트를 설계한다.

### 설계 원칙

```
입력: 5개 수치만
  - 현재 손익률
  - 고점 대비 되밀림
  - AI score 최근값
  - 보유시간
  - 직전 틱 방향 (상승/하락/횡보)

출력: action(HOLD/FORCE_EXIT) + score(0~100)
레이턴시 목표: < 1초
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-24 PREOPEN | 설계 문서 작성 |
| 2026-04-25 PREOPEN | 원격 shadow 반영 |
| 2026-04-28 POSTCLOSE | 1주 관찰 후 canary 전환 판정 |

---

## T11 — REVERSAL_ADD 메인 canary 전환 판정 (2026-04-25 POSTCLOSE)

### 입력

- T6(2026-04-21) 원격 canary 결과 (4일치)
- 실주문 발동 건수, 손익 분포, 손절 회피 케이스

### 판정 기준

| 조건 | 결정 |
|------|------|
| 원격 canary 발동 ≥ 3건 AND 평균 손익 개선 확인 | 메인 canary 전환 (limited, 1일 최대 2건) |
| 원격 canary 발동 < 3건 | 표본 부족, 원격 canary 연장 1주 |
| 발동 후 평균 손익 악화 | 파라미터 재검토 후 shadow 재시작 |

---

## T12 — PRESET_TP action schema 분리 설계 (2026-04-28 PREOPEN)

### 목적

`profit_rate >= 0.8%` 구간에서 1회 AI 검문을 수행하는 PRESET_TP 경로에  
전용 action(`EXTEND / EXIT`)을 분리한다.

현재 코드가 `SELL`을 확인하는데 프롬프트는 `DROP`을 반환하는 불일치를 해소한다.

### 설계 범위

```python
# sniper_state_handlers.py — SCALP_PRESET_TP 분기
if preset_tp_ai_check:
    if ai_action in ['EXIT', 'SELL', 'DROP']:   # 호환 수용
        → 즉시 청산
    elif ai_action in ['EXTEND', 'HOLD', 'BUY']:
        → 목표가 유지 또는 상향 검토
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-28 PREOPEN | 설계 문서 작성 |
| 2026-04-29 PREOPEN | 원격 shadow 반영 |
| 2026-05-06 POSTCLOSE | 1주 관찰 후 메인 반영 판정 |

---

## T13 — 동적 목표가 조정 설계 (2026-04-30 PREOPEN)

### 목적

현재 preset TP는 진입 시 고정. 보유 중 시장 상황 변화에 대응하지 못한다.  
올릭스처럼 +0.04% 달성 후 preset에 못 미쳐 익절 못하는 케이스를 해소한다.

### 설계 방향

```
조건: HOLDING_GENERAL AI score >= 70 AND profit_rate >= 0.3%
행동: preset TP를 현재가 + α로 하향 조정 (조기 익절 허용)

조건: HOLDING_GENERAL AI score < 40 AND profit_rate < -0.3%
행동: 현재 목표가보다 손절선을 조기 당겨 손실 축소
```

### 일정

| 시각 | 작업 |
|------|------|
| 2026-04-30 PREOPEN | 설계 문서 작성 |
| 2026-05-06 | 원격 shadow 반영 판정 |

---

## 전체 일정 요약표

| 날짜 | Task | 대상 | 메인/원격 | 내용 |
|------|------|------|-----------|------|
| **2026-04-17** | T1 | SCANNER timeout | 원격 shadow 판정 | fallback 전용 조기정리의 일반 SCANNER 확장 조건 정리 |
| **2026-04-17** | T7 | LOSS_FALLBACK | 진행 중 observe | `loss_fallback_probe` 1차 판정 |
| **2026-04-18** | T3 | HOLDING schema | 설계 | action 분리 설계 문서 |
| **2026-04-18** | T4 | REVERSAL_ADD | 판정 | 기존 후보 로그 1차 판정 |
| **2026-04-21** | T5 | HOLDING_GENERAL | 원격 shadow | 프롬프트 분리 1단계 |
| **2026-04-21** | T6 | REVERSAL_ADD | 판정 | 기존 후보 로그 기반 원격 canary 전환 판정 |
| **2026-04-21** | T7 | LOSS_FALLBACK | 판정 | 실전 활성화 여부 2차 판정 |
| **2026-04-22** | T8 | HOLDING schema | 원격 shadow | action 파싱 호환 구조 |
| **2026-04-23** | T9 | HOLDING_GENERAL | 판정 | 2일차 판정, canary 전환 여부 |
| **2026-04-24** | T10 | HOLDING_CRITICAL | 설계 | 최경량 손실/익절 판단 프롬프트 |
| **2026-04-24** | — | HOLDING schema | 판정 | 메인 shadow 반영 여부 |
| **2026-04-25** | T11 | REVERSAL_ADD | **메인 canary 판정** | 원격 canary 4일 결과 기준 |
| **2026-04-28** | T12 | PRESET_TP | 설계 | EXTEND/EXIT schema 분리 |
| **2026-04-28** | — | HOLDING_CRITICAL | 원격 shadow | 1주 관찰 시작 |
| **2026-04-30** | T13 | 동적 목표가 | 설계 | 조정 로직 설계 문서 |

---

## 중단 기준 (공통)

각 Task는 아래 중 하나라도 해당하면 다음 단계 진행을 중단하고 원인 분석 후 재판정한다.

- `ai_parse_ok=False` 비율이 현행 대비 **+5%p 이상** 증가
- `holding_skip` 비율이 현행 대비 **+10%p 이상** 증가
- 당일 실현 손익이 직전 5거래일 평균 대비 **-30% 이상** 악화
- `scale_in_locked` 발동 건수 급증 (일 2건 이상)

---

## 기존 플랜과의 관계

| 기존 워크스트림 | 이 플랜과의 관계 |
|----------------|----------------|
| WS-A 스캘핑 관측/리포트 | 독립. 이 플랜은 WS-A 완료 여부와 무관하게 진행 가능 |
| WS-B 원격 canary/롤아웃 | T1/T4/T6/T11이 원격 선행 원칙을 그대로 따름 |
| WS-C AI 프롬프트 개선 | T3/T5/T8/T10/T12가 WS-C의 Phase 3-2/3-3을 구체화 |
| WS-D 보조 운영/데이터 품질 | T7(LOSS_FALLBACK)이 WS-D partial fill canary와 병행 가능 |
