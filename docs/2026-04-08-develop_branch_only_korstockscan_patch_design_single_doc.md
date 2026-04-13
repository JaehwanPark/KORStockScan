# KORStockScan 패치 설계안
기준일: 2026-04-08  
대상 저장소: `JaehwanPark/KORStockScan`

## 0. 진단 요약

오늘 손실의 본질은 **종목 선정 실패보다 진입/청산 구조 실패**다.

1. `fallback`은 현재 **저신뢰 진입 축소 모드가 아니라, 체결 방식만 바꾼 준-정규 진입**으로 동작한다.
2. `OPEN_RECLAIM`은 **실패 인식을 너무 늦게** 하고, `SCANNER/fallback`은 **확장 실패를 너무 오래 방치**한다.
3. Gatekeeper / Holding AI는 `curr`, `spread` 중심의 민감한 시그니처 때문에 **fast reuse가 거의 죽어 있고**, 빠른 상승장에서 판단이 늦어진다.

## 0-1. 근거 요약

- 2026-04-08 장마감 기준 스캘핑은 `12건`, 승률 `25.0%(3/12)`, 실현손익 `-66,367원`.
- 같은 날 `fallback` 진입 `5건`은 전패, 실현손익 `-27,742원`.
- `scalp_ai_early_exit` 종료 `4건` 전부 손실.
- `OPEN_RECLAIM` 손절 표본은 평균 보유 `492.5초`, 평균 손익률 `-0.99%`.
- `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=13,524ms`, `holding_ai_cache_hit_ratio=0.2%`.

즉, 시스템은 “강한 신호에 크게 싣는 공격성”보다  
“늦어진 신호를 fallback으로 살리고, 실패 포지션을 늦게 인정하는 방어성”에 더 가깝다.

---

## 1. 설계 목표

이번 패치의 목적은 단순히 손절을 줄이는 것이 아니다.  
목표는 아래 3가지다.

1. **늦은 진입을 정상 리스크로 받지 않게 만든다.**
2. **실패한 reclaim / fallback 포지션을 더 빨리 버린다.**
3. **판단 재사용을 살려 빠른 장에서 의사결정 속도를 회복한다.**

---

## 2. 설계 원칙

### 원칙 A. 공통 손절값을 건드리지 않는다
이번 패치는 `SCALPING` 전체 손절선을 한 번에 완화하거나 강화하지 않는다.  
반드시 아래 3개 트랙으로 분리한다.

- `SCALP_BASE / fallback`
- `OPEN_RECLAIM`
- `SCANNER / fallback`

### 원칙 B. 공격적 운영 = 아무 데나 더 사는 것 아님
공격적 운영은 “약한 신호도 더 많이 사기”가 아니라,

- 강한 신호에 더 빠르고 크게,
- 약해진 신호는 더 작게,
- 실패한 포지션은 더 빨리 버리기

를 의미한다.

### 원칙 C. fallback은 별도 리스크 클래스다
`fallback`은 더 이상 “진입 방식 옵션”이 아니라  
**저신뢰 / 저우선순위 진입 클래스**로 취급해야 한다.

### 원칙 D. 속도는 성과다
상승장에서는 정밀하지만 느린 판단보다  
조금 둔감해도 빠른 판단이 더 높은 기대값을 만든다.  
따라서 `fast reuse`와 캐시 재사용 복구는 성능 최적화가 아니라 **매매 성과 패치**다.

---

## 3. 패치 범위 개요

이번 설계는 아래 4개 트랙으로 구성한다.

- **Track A. fallback 진입 억제 / 축소**
- **Track B. OPEN_RECLAIM 조기 실패 인식**
- **Track C. SCANNER/fallback 확장 실패 조기 청산**
- **Track D. Gatekeeper / Holding AI 재사용 복구**

---

## 4. Track A — fallback 진입을 “축소된 저신뢰 진입”으로 재정의

## 4-1. 현재 문제

현재 live path는 `real_buy_qty`를 먼저 계산한 뒤,  
CAUTION이면 동일 planned_qty를 fallback 번들로 나눈다.  
즉 fallback은 **주문 형식만 다르고 총 리스크는 거의 같다**.

현 구조에서는

- 1주 `fallback_scout`
- 나머지 `fallback_main`

으로 나가지만, 손실은 전체 수량 기준으로 발생한다.

## 4-2. 패치 목표

- fallback을 **정규 진입의 대체재**가 아니라 **소형 탐색 진입**으로 바꾼다.
- 늦은 신호는 “살릴 수 있으면 작게”, 아니면 버린다.

## 4-3. 설계안

### A1. fallback 총수량 축소
`entry_mode == "fallback"`일 때 최종 진입 수량을 정상 대비 축소한다.

제안:
- 기본 fallback 총수량 = 정상 planned_qty의 `25% ~ 35%`
- 최소 1주 보장
- `SCANNER`, `SCALP_BASE` 태그는 더 강하게 `20% ~ 25%`
- `OPEN_RECLAIM`만 상대적으로 완만하게 `35%`

### A2. fallback 허용 태그 축소
아래 태그는 CAUTION에서 fallback을 바로 허용하지 않고 더 엄격하게 본다.

- `SCANNER`
- `SCALP_BASE`

옵션:
- `SCANNER`: scout-only
- `SCALP_BASE`: fallback 자체 reject
- `OPEN_RECLAIM`: 제한적 허용 유지

### A3. fallback 메인 주문 생존시간 단축
현재 fallback main DAY 주문은 상대적으로 오래 살아남는다.  
이를 단기 유효 주문으로 바꾼다.

제안:
- fallback main 미체결 허용 시간: `10~20초`
- 미체결 시 즉시 취소
- scout만 체결된 경우는 “소형 실험 포지션”으로 관리

### A4. fallback 전용 관측 필드 추가
`ENTRY_PIPELINE`, `trade-review`, `performance-tuning`에 아래 필드를 추가한다.

- `fallback_risk_class`
- `fallback_size_ratio`
- `fallback_only_scout_fill`
- `fallback_main_expired`
- `fallback_total_qty_before`
- `fallback_total_qty_after`

## 4-4. 수정 대상 파일

- `src/engine/sniper_entry_latency.py`
- `src/trading/config/entry_config.py`
- `src/trading/entry/fallback_strategy.py`
- `src/engine/sniper_state_handlers.py`

## 4-5. 구현 포인트

### entry_config.py
신규 설정값 추가:
- `fallback_total_qty_ratio_default`
- `fallback_total_qty_ratio_scanner`
- `fallback_total_qty_ratio_scalp_base`
- `fallback_total_qty_ratio_open_reclaim`
- `fallback_main_expire_sec`
- `fallback_scout_only_tags`

### sniper_entry_latency.py
`evaluate_live_buy_entry()`에서 `ALLOW_FALLBACK` 시점에
태그별 총수량 축소 로직 적용.

### fallback_strategy.py
입력 planned_qty 자체가 축소된 수량을 받도록 정리하고,
scout/main 비중을 현재보다 더 scout 중심으로 재배분 가능하게 확장.

### sniper_state_handlers.py
`order_bundle_submitted` 로그에 fallback 축소 전/후 수량 기록.

---

## 5. Track B — OPEN_RECLAIM 조기 실패 인식 강화

## 5-1. 현재 문제

`OPEN_RECLAIM`은 현재
- AI early exit hit 수가 높고,
- never-green 정리도 늦다.

결과적으로 “살아나지 않는 reclaim”을 너무 오래 본다.

## 5-2. 패치 목표

`OPEN_RECLAIM`은 **빨리 살아나는 놈만 남기고**,  
초기 반응이 없으면 더 빨리 자른다.

## 5-3. 설계안

### B1. never-green 청산 시간 단축
현재:
- `SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC = 300`

제안:
- `150 ~ 180초`로 단축

### B2. peak_profit 조건 유지
아래 조건은 유지한다.
- `peak_profit <= 0.20%`

이 조건은 “한 번도 제대로 살아나지 못한 reclaim”만 걸러내는 데 유효하다.

### B3. AI 점수 조건 완화
현재는 `near_ai_exit` 쪽이 너무 늦게 작동한다.

제안:
- `current_ai_score <= 40~45`
- 또는 `near_ai_exit` 동반 시
- `never_green`과 결합하여 조기 청산

### B4. 양전환 이력 분리
`OPEN_RECLAIM`은 반드시 아래 2개 그룹으로 나눠야 한다.

- `never_green`
- `once_green_then_fail`

`never_green`만 먼저 공격적으로 자른다.  
`once_green_then_fail`은 기존 AI early exit / trailing 체계를 유지한다.

## 5-4. 수정 대상 파일

- `src/engine/sniper_state_handlers.py`
- 필요 시 `src/utils/constants.py`

## 5-5. 구현 포인트

### constants.py
- `SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC`
- `SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT`
- `SCALP_OPEN_RECLAIM_NEVER_GREEN_SCORE_LIMIT` 신규

### sniper_state_handlers.py
`strategy == 'SCALPING'` 구간의 `OPEN_RECLAIM` 분기에서
기존 `scalp_open_reclaim_never_green`을 더 먼저, 더 짧은 시간에 발동.

추가 필드:
- `ever_green_flag`
- `first_green_at`
- `never_green_hold_sec`

로그:
- `exit_rule = scalp_open_reclaim_never_green_fast`
- `exit_rule = scalp_open_reclaim_failed_after_green`

---

## 6. Track C — SCANNER/fallback 확장 실패 조기 청산

## 6-1. 현재 문제

`SCANNER + fallback`은 현재
- 한 번도 양전환하지 못해도,
- near_ai_exit가 오래 지속되어도,
- 너무 늦게 청산된다.

이건 “손절이 넓다”의 문제가 아니라
**실패 판정이 늦다**는 문제다.

## 6-2. 패치 목표

들어간 직후 확장이 안 나오면  
“나쁜 포지션을 오래 버티는 것”이 아니라  
“실패 진입”으로 분류해 조기 정리한다.

## 6-3. 설계안

### C1. failed-to-expand 룰 신설
신규 exit rule 추가:

`scalp_scanner_fallback_failed_to_expand`

발동 조건 제안:
- `position_tag == 'SCANNER'`
- `entry_mode == 'fallback'`
- `held_sec >= 45~60`
- `peak_profit < +0.15% ~ +0.20%`
- `current_ai_score < 55`
- `near_ai_exit` 또는 orderbook 약화 동반

### C2. 장기 never-green 보조 룰 유지
기존 `scalp_scanner_fallback_never_green`은 유지하되,
위 failed-to-expand가 먼저 작동하도록 우선순위를 올린다.

### C3. fallback_scout만 체결된 경우 더 짧게
s scout-only 체결은 실험 포지션이므로 더 짧게 본다.

제안:
- scout-only + 미확장 = `30~45초` 내 정리

## 6-4. 수정 대상 파일

- `src/engine/sniper_state_handlers.py`
- `src/engine/sniper_execution_receipts.py`

## 6-5. 구현 포인트

### sniper_execution_receipts.py
신규 진입 체결 후
- `fallback_fill_profile`
- `fallback_only_scout_filled`
- `fallback_main_filled`
를 저장.

### sniper_state_handlers.py
스캘핑 보유 청산 구간에
`SCANNER + fallback` 전용 조기 실패 분기 추가.

로그:
- `scalp_scanner_fallback_failed_to_expand`
- `scalp_scanner_fallback_scout_only_fail`

---

## 7. Track D — Gatekeeper / Holding AI 재사용 복구

## 7-1. 현재 문제

문서와 운영 로그상 blocker 상위는 `curr`, `spread`, `sig_changed`다.  
즉 캐시 TTL 부족이 아니라 **시그니처 민감도 과잉**이 핵심이다.

## 7-2. 패치 목표

- fast reuse를 되살린다.
- 빠른 장에서 “조금 둔감하지만 더 빠른 판단”으로 전환한다.

## 7-3. 설계안

### D1. Holding fast snapshot 완화
`_build_holding_ai_fast_snapshot()`의 민감도를 완화한다.

우선 완화 후보:
- `curr`
- `spread`
- `buy_ratio`

방향:
- 가격 버킷 확대
- spread 변화 1틱 단위 민감도 완화
- buy_ratio step 확대

### D2. Gatekeeper fast signature 완화
`_build_gatekeeper_fast_signature()` / `_build_gatekeeper_fast_snapshot()`도
아래 필드 중심으로 완화한다.

- `curr_price`
- `spread_tick`
- `buy_ratio_ws`

### D3. AI holding cache compact key 완화
`ai_engine.py`의 `_compact_holding_ws_for_cache()`도
같은 방향으로 둔감화한다.

### D4. 완화는 1차에 `curr/spread`만
한 번에 모든 필드를 바꾸지 않는다.  
1차 패치는 `curr`, `spread`만 완화하고,
나머지는 shadow 지표를 보고 후속 적용한다.

## 7-4. 수정 대상 파일

- `src/engine/sniper_state_handlers.py`
- `src/engine/ai_engine.py`

## 7-5. 구현 포인트

### sniper_state_handlers.py
- `_price_bucket_step()` 재사용 범위 확대
- holding / gatekeeper snapshot의 `curr`, `spread` 버킷 재정의
- `sig_delta` 로깅은 유지

### ai_engine.py
- `_compact_holding_ws_for_cache()`의
  - `curr`
  - `best_ask`
  - `best_bid`
  - `buy_ratio`
  민감도 조정

목표:
- `holding_skip_ratio` 유지 또는 개선
- `holding_ai_cache_hit_ratio` 회복
- `gatekeeper_fast_reuse_ratio` 0% 탈출

---

## 8. 보조 패치 — exit_rule 복원 및 리뷰 정확도 강화

이번 패치는 “로직 수정”만이 아니라
“수정 결과를 정확히 읽을 수 있게 만드는 패치”도 포함해야 한다.

## 8-1. 목적

- `exit_rule='-'` 미복원 거래를 줄인다.
- fallback / reclaim / scanner 분기 결과가 복기 리포트에서 바로 구분되게 한다.

## 8-2. 설계안

신규 또는 정비 대상 `exit_rule`
- `scalp_open_reclaim_never_green_fast`
- `scalp_open_reclaim_failed_after_green`
- `scalp_scanner_fallback_failed_to_expand`
- `scalp_scanner_fallback_scout_only_fail`
- `fallback_main_expired_no_fill`

## 8-3. 수정 대상 파일

- `src/engine/sniper_trade_review_report.py`
- `src/engine/sniper_performance_tuning_report.py`
- `src/web/app.py`

---

## 9. 구현 순서

### Step 1
`Track A` 먼저
- fallback 총수량 축소
- fallback 메인 주문 수명 단축
- fallback 관측 필드 추가

### Step 2
`Track B`
- OPEN_RECLAIM never-green 조기 정리
- 양전환 이력 분리

### Step 3
`Track C`
- SCANNER/fallback failed-to-expand 추가
- scout-only 실패 분리

### Step 4
`Track D`
- holding / gatekeeper `curr`, `spread` 민감도 완화
- cache compact key 완화

### Step 5
리포트/대시보드 보강
- exit_rule 복원
- 신규 분기별 성과 카드 추가

---

## 10. 롤아웃 원칙

### Canary 1
fallback 축소만 먼저
- 목표: fallback 손실총액 즉시 축소
- 롤백 조건: 진입 건수만 줄고 질 개선이 전혀 없을 때

### Canary 2
OPEN_RECLAIM 조기 정리
- 목표: 평균 보유시간 단축, -1%대 지연 손절 감소
- 롤백 조건: 조기 잘림 급증 + 이후 상승 재개가 반복될 때

### Canary 3
SCANNER/fallback failed-to-expand
- 목표: never-green 장기 손실 제거
- 롤백 조건: 1분 내 재상승 성공 케이스가 빈번할 때

### Canary 4
curr/spread 민감도 완화
- 목표: fast reuse / cache hit 회복
- 롤백 조건: 재사용은 늘지만 판단 품질 악화가 확인될 때

---

## 11. 성공 기준

### 성과 기준
- `fallback` 손실총액 50% 이상 축소
- `OPEN_RECLAIM` 평균 보유시간 유의미 단축
- `SCANNER/fallback` never-green 장기 보유 감소

### 구조 기준
- `gatekeeper_fast_reuse_ratio > 0%` 복귀
- `holding_ai_cache_hit_ratio` 유의미 회복
- 신규 `exit_rule` 미복원율 축소

### 해석 기준
복기 화면에서 아래 3개가 바로 분리되어야 한다.
- `fallback 과민/실패 진입`
- `OPEN_RECLAIM 지연 실패`
- `SCANNER fallback 확장 실패`

---

## 12. 이번 패치에서 하지 않을 것

- 공통 hard time stop 전면 적용
- 스캘핑 공통 손절값 일괄 완화
- `near_safe_profit` / `near_ai_exit` 공통 band 즉시 완화
- 듀얼 페르소나 Gatekeeper 재활성화
- `RISK_OFF` day 스윙 완화

---

## 13. 최종 한 줄 결론

이번 패치는 “더 많이 사는 공격성”이 아니라,  
**약한 fallback을 더 작게 받고, 실패한 reclaim/fallback을 더 빨리 버리고, 판단 속도를 되찾아 강한 놈만 더 세게 타는 구조**로 바꾸는 설계다.
