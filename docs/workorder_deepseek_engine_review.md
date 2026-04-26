# 작업지시서: `ai_engine_deepseek.py` 코드리뷰 후속 정리

작성일: `2026-04-26 KST`  
대상: [`src/engine/ai_engine_deepseek.py`](../src/engine/ai_engine_deepseek.py)  
참조: [`src/engine/ai_engine.py`](../src/engine/ai_engine.py), [`src/tests/test_ai_engine_cache.py`](../src/tests/test_ai_engine_cache.py)  
ApplyTarget: `src/engine/ai_engine_deepseek.py` 단일축 우선, 필요 시 호환 테스트만 최소 추가. 실전 경로 변경은 `1축 canary + rollback guard` 전제.

---

## 1. 최종 판정

1. **승인(P0): JSON 파싱 fast-path 추가**
   - `_call_deepseek_safe()`의 `require_json=True` 경로에서 `json.loads(raw_text)` 직접 시도를 먼저 두고, 실패할 때만 `_parse_json_response_text()` fallback을 타는 변경은 **저위험/즉시 가능**하다.

2. **조건부 승인(P1): 재시도 정책 개선**
   - 현재 `0.8초 고정 대기 + 키 로테이션`은 단순하다.
   - 다만 실시간 진입/게이트키퍼 경로에 무거운 exponential backoff를 바로 넣으면 `api_call_lock` 점유 시간이 늘어 **미진입 기회비용**이 커질 수 있다.
   - 따라서 `report/Tier3`와 `realtime/Tier1~2`를 분리한 **bounded backoff + jitter**로 설계할 때만 승인한다.

3. **보류(P2): 실시간 리포트 JSON 모드 일괄 전환**
   - 방향성은 맞지만, 현재 문제를 `이중 API 호출`로 정의한 부분은 부정확하다.
   - `evaluate_realtime_gatekeeper()`는 내부적으로 `_generate_realtime_report_payload()`를 한 번만 호출한다. 즉, 현재 병목은 `문자열 라벨 파싱의 취약성`이지 `게이트키퍼 자체의 중복 호출`로 확정할 수 없다.
   - 이 변경은 퍼블릭 인터페이스와 테스트 가정을 건드리므로 **flag + fallback + canary** 없이 바로 넣으면 안 된다.

4. **보류(P3): holding cache 버킷 축소**
   - `_compact_holding_ws_for_cache()`는 `cache_profile == "holding"`일 때만 쓰이며, 현재 의도는 holding/exit 미세 노이즈를 흡수하는 것이다.
   - 실제로 테스트도 미세 변동 흡수를 기대한다.
   - 기대값 개선 근거 없이 버킷을 세밀화하면 캐시 미스와 호출량만 늘 수 있으므로 **증거 수집 전 수정 보류**가 맞다.

5. **후순위(code debt): Google Search 흔적 정리, Tool Calling 검토**
   - 현재는 기능 리스크가 아니라 정리 과제다.
   - 실전 EV 개선과 직접 연결되지 않으므로 이번 1차 작업지시 범위에서는 우선순위를 낮춘다.

---

## 2. 근거

### 2-1. JSON 파싱

- [`src/engine/ai_engine_deepseek.py`](../src/engine/ai_engine_deepseek.py) `_call_deepseek_safe()`는 `require_json=True`일 때 `response_format={"type": "json_object"}`를 건 뒤, 응답 문자열을 곧바로 `_parse_json_response_text()`로 넘긴다.
- `_parse_json_response_text()` 자체도 첫 후보로 원문 전체를 `json.loads()` 시도하지만, 그 전에 fence/block 정규식 두 번을 먼저 돈다.
- 따라서 **정확성 이슈라기보다 미세한 hot-path 낭비**로 보는 편이 맞다.
- 결론: `raw_text.strip()` 직접 파싱 성공 시 즉시 반환, 실패 시 기존 helper fallback 유지가 적정하다.

### 2-2. 재시도

- `_call_deepseek_safe()`는 `RateLimitError`, `429/quota/503/unavailable/timeout/server/too_many_requests` 계열에서 모두 `time.sleep(0.8)` 후 키를 바꿔 재시도한다.
- 문제는 `개선 필요` 자체보다 **적용 방식**이다.
- DeepSeek 엔진은 `analyze_target()`, `evaluate_realtime_gatekeeper()`, `evaluate_condition_entry/exit()` 같은 실시간 경로와 `analyze_scanner_results()` 같은 비실시간 경로를 같이 가진다.
- 따라서 모든 경로에 동일한 exponential backoff를 넣는 것은 안정성은 높여도 실전 진입 타이밍에는 불리할 수 있다.

### 2-3. 실시간 리포트 / 게이트키퍼

- `generate_realtime_report()`는 `_generate_realtime_report_payload()["report"]`를 반환하는 래퍼다.
- `evaluate_realtime_gatekeeper()`는 별도 텍스트 리포트를 다시 파싱하지 않고, 같은 `_generate_realtime_report_payload()`를 직접 호출해 `action_label`을 추출한다.
- 즉, 현재 사실관계는:
  - `게이트키퍼 경로 = 1회 모델 호출`
  - `문제 = 자유형 텍스트에 행동 라벨이 없거나 깨질 때 취약`
- 추가로 [`src/tests/test_ai_engine_cache.py`](../src/tests/test_ai_engine_cache.py)는 `generate_realtime_report()`를 monkeypatch해서 게이트키퍼 캐시를 검증한다.
- 결론: JSON 모드 전환은 가능하지만, **호환 계층을 유지하는 별도 축**으로 다뤄야 한다.

### 2-4. holding cache

- `_build_analysis_cache_key_with_profile()`는 `cache_profile == "holding"`일 때만 `_compact_holding_ws_for_cache()`를 사용한다.
- 이는 entry 병목이 아니라 holding/exit 분석 캐시 축이다.
- 현재 테스트는 미세 호가/수급 노이즈를 캐시가 흡수하기를 기대한다.
- 결론: `0.2% 이내로 좁혀라`는 제안은 아직 **성능/EV 근거보다 감각적 제안**에 가깝다.

---

## 3. 작업지시

### 3-1. P0 즉시 작업

1. `_call_deepseek_safe()` JSON fast-path 추가
   - 변경:
     - `require_json=True`면 `raw_text = str(response.choices[0].message.content or "").strip()`
     - `json.loads(raw_text)`를 먼저 시도
     - 실패 시 기존 `_parse_json_response_text(raw_text)` fallback 유지
   - 금지:
     - `_parse_json_response_text()` 제거
     - fence/block fallback 삭제
   - acceptance:
     - 기존 JSON 반환 contract 불변
     - 텍스트 경로 영향 없음
     - DeepSeek 엔진 관련 캐시/게이트키퍼 테스트 회귀 없음
   - rollback guard:
     - fast-path 분기만 제거하면 즉시 원복 가능해야 한다

### 3-2. P1 조건부 작업

2. retry 정책을 `context-aware bounded backoff`로 재설계
   - 1차 범위:
     - `시장 브리핑`, `EOD`, 기타 Tier3/비실시간 경로에 한해 exponential backoff + jitter 허용
   - 보수 조건:
     - `analyze_target`, `evaluate_realtime_gatekeeper`, `evaluate_condition_entry/exit`는 현행 대비 sleep 총량이 늘지 않도록 상한을 둔다
     - `api_call_lock` 장기 점유를 피하는 cap을 문서에 적는다
   - 권장 구현:
     - `_compute_retry_sleep(context_name, attempt, live_sensitive)` 헬퍼 분리
     - `live_sensitive=True` 경로는 `짧은 cap`, `report/eod`는 `완화된 cap`
   - acceptance:
     - live-sensitive 경로의 worst-case 대기 상한이 문서화돼 있어야 한다
     - 재시도 정책 변경이 실전 진입 병목 축과 섞이지 않게 단일 조작점으로 남아야 한다
   - rollback guard:
     - `TRADING_RULES` 또는 로컬 상수 1개로 새 retry 정책 ON/OFF 가능해야 한다

### 3-3. P2 별도 축 후보

3. gatekeeper structured-output 전환은 별도 canary로 분리
   - 현재 작업 범위:
     - `generate_realtime_report()`의 사람용 텍스트 응답은 유지
     - `evaluate_realtime_gatekeeper()`에만 JSON 전용 경로를 **옵션**으로 추가 검토
   - 필수 조건:
     - flag 기본값 `OFF`
     - JSON 파싱 실패 시 기존 텍스트 경로 fallback
     - `action_label`, `allow_entry`, `report`, `selected_mode`, timing 필드 contract 유지
     - 기존 `test_ai_engine_cache.py` 가정을 깨지 않거나, 깨면 테스트/호출부를 같은 change set에서 같이 고친다
   - 금지:
     - 텍스트 리포트 퍼블릭 인터페이스 즉시 제거
     - flag 없이 live gatekeeper 판정 경로를 통째로 교체

### 3-4. 보류 항목

4. `_compact_holding_ws_for_cache()` 버킷 조정은 관측 근거 확보 전 보류
   - 선행 근거:
     - holding cohort에서 cache miss 증가가 실제 `completed_valid` 품질 개선으로 이어지는지
     - `partial/full`, `initial/pyramid` 분리 기준에서 exit 품질 훼손 또는 missed upside 개선이 있는지
   - 근거가 쌓이기 전에는 현행 캐시 전략 유지

5. Tool Calling 도입 검토는 설계 메모로만 남김
   - 즉시 구현 범위 아님
   - 퍼블릭 응답 schema, fallback, 테스트, SDK 제약을 먼저 정리해야 함

---

## 4. 권장 적용 순서

1. `P0 JSON fast-path`만 먼저 반영
2. 테스트 통과 확인
3. `P1 retry`는 live-sensitive cap/rollback guard 문서화 후 별도 change set으로 진행
4. `P2 gatekeeper JSON`은 flag-off 기본값으로만 설계/착수
5. holding cache / Tool Calling은 관찰 backlog로 유지

---

## 5. 완료 기준

- **완료 판정**
  - `P0`는 코드/테스트 기준으로 same-day 닫을 수 있다.
  - `P1`은 `live-sensitive 상한 + rollback guard`가 문서와 코드에 같이 있으면 착수 가능하다.
  - `P2`는 `flag-off + fallback + contract 유지 테스트`가 없으면 착수 불가다.

- **다음 액션**
  - 익일 checklist에는 `P0 즉시 반영 여부`, `P1 retry 조건부 승인 여부`, `P2 JSON gatekeeper 분리 여부`를 한 항목으로 고정한다.
  - Project/Calendar 동기화 대상은 checklist 소유로 유지한다.
