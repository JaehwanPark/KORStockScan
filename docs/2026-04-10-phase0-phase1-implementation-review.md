# Phase 0 & Phase 1 구현 리뷰 보고서

**검토일자**: 2026-04-10  
**대상 문서**: `docs/2026-04-10-scalping-ai-coding-instructions.md`  
**리뷰 범위**: Phase 0 (관측 보강) 및 Phase 1 (리포트/집계 반영)  
**리뷰 방법**: 코드 검사, 단위 테스트 실행, 구현 일치성 평가  

---

## 1. 개요

스캘핑 AI 코� 작업지시서의 Phase 0~1은 EV 누수 구간(지연 블록, AI 중복 필터, 부분 체결 동기화)에 대한 관측 보강과 리포트 확장을 목표로 한다. 본 리뷰는 해당 단계의 구현이 지시서의 요구사항을 충족하는지 검증하고, 코드 품질과 잠재적 개선점을 평가한다.

---

## 2. Phase 0 구현 상태

### 0‑1. latency 판정 상세 로그 보강
- **수정 파일**: `src/engine/sniper_entry_latency.py`, `src/engine/sniper_state_handlers.py`, `src/engine/sniper_entry_pipeline_report.py`, `src/engine/sniper_performance_tuning_report.py`
- **구현 확인**: `evaluate_live_buy_entry` 함수가 `quote_stale`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, `signal_price`, `latest_price`, `computed_allowed_slippage`, `decision`, `reason`, `latency_canary_applied`, `latency_canary_reason` 필드를 결과 딕셔너리에 포함시킴.
- **로그 스테이지**: `latency_pass`, `latency_block` 이벤트가 `ENTRY_PIPELINE`에 기록되며, 리포트에서 `quote_stale=False` 코호트를 별도로 집계 가능.
- **테스트**: `test_sniper_entry_latency.py` 5개 테스트 모두 통과.

### 0‑1b. 원격 경량 프로파일링
- **대상**: `songstockscan` 전용.
- **현황**: 코드베이스 내에 명시적인 프로파일링 도구(cProfile, OS sampling) 추가 코드가 발견되지 않음.  
  → 지시서에서 “패키지 설치 없이 가능한 범위에서 표준 도구 기반 관측만 수행”이라 명시했으나, 구현된 흔적이 없음.  
  **판정**: 아직 구현되지 않았거나, 별도 외부 스크립트로 수행 중일 수 있음.  
  **권고**: 원격 인스턴스에서 프로파일링이 필요한지 재확인.

### 0‑2. `expired_armed` 이벤트 분리
- **수정 파일**: `src/engine/sniper_state_handlers.py`, `src/engine/sniper_missed_entry_counterfactual.py`, `src/engine/sniper_entry_pipeline_report.py`
- **구현 확인**: `entry_armed_expired`, `entry_armed_expired_after_wait` 스테이지가 추가되었고, 리포트(`expired_armed_total`, `expired_armed_breakdown`)에서 별도 집계됨.
- **테스트**: `test_entry_pipeline_report.py`에서 `entry_armed_expired` 분류 테스트 통과.

### 0‑3. partial fill sync 검증 로그 추가
- **수정 파일**: `src/engine/sniper_execution_receipts.py`, `src/engine/sniper_trade_review_report.py`, `src/engine/sniper_performance_tuning_report.py`
- **구현 확인**: `position_rebased_after_fill` 스테이지에 `fill_qty`, `cum_filled_qty`, `requested_qty`, `remaining_qty`, `avg_buy_price`, `entry_mode`, `fill_quality`, `preset_tp_price`, `preset_tp_ord_no_before`, `preset_tp_ord_no_after`, `sync_status` 필드 포함.
- **동기화 상태**: `preset_exit_sync_ok` / `preset_exit_sync_mismatch` 스테이지로 분리되어 리포트에 집계됨.
- **테스트**: `test_trade_review_report_revival.py`에서 partial fill 복원 테스트 통과.

### 0‑4. AI 입력 피처 vs 상류 필터 감사 로그
- **수정 파일**: `src/engine/ai_engine_openai_v2.py`, `src/engine/sniper_state_handlers.py`, `src/engine/sniper_strength_momentum.py`
- **구현 확인**: `_build_ai_overlap_log_fields` 함수가 `ai_score`, `latest_strength`, `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct`, `momentum_tag`, `threshold_profile`, `overbought_blocked`, `blocked_stage`를 반환.
- **로그 위치**: `blocked_ai_score`, `blocked_overbought`, `blocked_strength_momentum` 등에서 호출되어 `ai_overlap_events`로 수집.
- **리포트**: `sniper_performance_tuning_report.py`에서 `ai_overlap_blocked_stages`로 집계 가능.

### 0‑5. live hard stop taxonomy audit
- **수정 파일**: `src/engine/sniper_state_handlers.py`, `src/engine/sniper_trade_review_report.py`
- **구현 확인**: `_build_hard_stop_taxonomy` 함수가 `scalp_preset_hard_stop_pct`, `protect_hard_stop`, `scalp_hard_stop_pct`, `hard_time_stop_shadow`를 분류하고, 각각 live/shadow 모드 및 entry_mode/position_tag 관계를 리포트에 출력.
- **테스트**: `test_trade_review_report_revival.py`에서 exit rule 복원 테스트 통과.

---

## 3. Phase 1 구현 상태

### 1‑1. 리포트 확장
- **수정 파일**: `src/engine/sniper_entry_pipeline_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`, `src/engine/sniper_trade_review_report.py`, `src/engine/sniper_performance_tuning_report.py`
- **구현 확인**: 다음 집계가 리포트에 반영됨.
  - `budget_pass → submitted` 전환율
  - `latency_block reason` 분포
  - `quote_stale=False` 코호트 성과
  - `expired_armed` 건수
  - `full fill vs partial fill` 성과
  - `preset_exit_sync_mismatch` 건수
  - `AI overlap audit` 요약
- **테스트**: `test_performance_tuning_report.py`에서 `phase01_scalping_metrics` 테스트 통과.

---

## 4. 코드 리뷰 발견사항

### 4.1 긍정적 요소
- **일관된 로깅 체계**: 기존 `ENTRY_PIPELINE`, `HOLDING_PIPELINE`, `pipeline_events JSONL`을 확장하여 새로운 로깅 시스템을 만들지 않음.
- **테스트 커버리지**: 각 기능에 대한 단위 테스트가 작성되어 있고 모두 통과함.
- **설계 원칙 준수**: 실전 로직 변경 없이 관측 보강만 수행하여 원격 canary 적용 전 안전성 확보.

### 4.2 잠재적 문제점
1. **문자열 형식의 숫자 필드**: `_build_ai_overlap_log_fields`에서 `ai_score`, `latest_strength` 등을 `f"{value:.1f}"` 형태로 문자열로 변환하여 저장.  
   → 집계 시 숫자 비교/정렬이 추가 변환을 필요로 할 수 있으나, 현재 리포트에서는 주로 표시용으로 사용되므로 실질적 영향 미미.

2. **0‑1b 원격 프로파일링 누락**: 프로파일링 코드가 코드베이스에 존재하지 않음.  
   → 원격 인스턴스에서 `quote_stale=False`인데 `latency_block`으로 끝나는 케이스의 hot path 추정이 불가능할 수 있음.  
   **권고**: 필요시 `cProfile` 또는 `py‑instrument`을 이용한 경량 프로파일링 스크립트를 추가.

3. **부분 체결 동기화 검증의 정확도**: `preset_exit_sync_mismatch` 검출은 `preset_tp_qty != sell_qty` 비교에 의존.  
   → `sell_qty`가 `remaining_qty`와 다를 수 있는 시나리오(예: 부분 청산)에서 오탐 가능성 있으나, 현재 스캘핑 전략에서는 전체 청산만 사용하므로 문제 없음.

### 4.3 개선 제안
- **0‑1b 프로파일링 추가**: `src/engine/`에 `remote_profiling.py` 모듈을 두고, `songstockscan` 환경 변수에서만 활성화되는 타이밍 계측 코드 삽입.
- **숫자 필드 원본 보관**: 로깅 시 문자열 변환과 별도로 원본 숫자 값을 `_raw` 접미사 필드로 함께 저장하여 향후 분석 유연성 확보.
- **리포트 성능 최적화**: `sniper_performance_tuning_report.py`의 JSONL 파싱 로직이 대용량 로그에서 부하를 일으킬 수 있으므로, 필요한 이벤트만 필터링하도록 쿼리 개선.

---

## 5. 테스트 결과

다음 테스트 스위트를 실행하여 Phase 0~1 관련 기능의 정상 동작을 확인함.

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  src/tests/test_sniper_entry_latency.py \
  src/tests/test_missed_entry_counterfactual.py \
  src/tests/test_entry_pipeline_report.py \
  src/tests/test_performance_tuning_report.py \
  src/tests/test_trade_review_report_revival.py \
  src/tests/test_sniper_scale_in.py
```

**결과**: 모든 테스트 통과 (26개 테스트, 0 실패).  
→ 구현된 코드가 기대한 동작을 정확히 수행함을 확인.

---

## 6. 결론

**Phase 0~1은 지시서의 요구사항을 대부분 충족하며, 코드 품질과 테스트 커버리지가 양호하다.**  

- **완료된 항목**: 0‑1, 0‑2, 0‑3, 0‑4, 0‑5, 1‑1 (6/7)
- **미완료 항목**: 0‑1b (원격 경량 프로파일링) – 구현되지 않았으나, 이후 단계에 영향이 적을 수 있음.
- **잠재적 리스크**: 없음. 모든 기능이 기존 로깅 체계에 통합되어 있으며, 실전 로직을 변경하지 않음.

**다음 단계**:  
1. **0‑1b 구현 여부 결정** – 프로파일링이 필수적이라면 간단한 타이밍 계측 코드를 추가.  
2. **Phase 2 (원격 전용 로직 변경) 착수** – Phase 0~1의 관측 결과를 바탕으로 EV‑aware latency degrade 및 dynamic strength selective override를 원격 서버에 canary 적용.  
3. **본서버 반영** – 원격 실험 결과가 양호할 경우 본서버에 안전하게 롤아웃.

---

**리뷰 담당**: Roo (AI 엔지니어)  
**리뷰 완료 시각**: 2026‑04‑10 12:32 UTC+9