# 작업지시서: `ai_engine.py` 코드리뷰 후속 정리

작성일: `2026-04-26 KST`  
대상: [`src/engine/ai_engine.py`](../src/engine/ai_engine.py)  
참조: [`src/tests/test_ai_engine_cache.py`](../src/tests/test_ai_engine_cache.py), [`src/tests/test_gemini_live_prompt_smoke.py`](../src/tests/test_gemini_live_prompt_smoke.py)  
ApplyTarget: `src/engine/ai_engine.py` 우선. 테스트는 기존 Gemini 계약을 깨는 범위만 최소 보강. live Gemini 경로 변경은 `1축 canary + rollback guard` 전제.

---

## 1. 최종 판정

1. **조건부 승인(P1): system instruction 분리**
   - 현재 `_call_gemini_safe()`는 `contents=[prompt, user_input]` 방식으로 프롬프트를 일반 입력에 섞는다.
   - 로컬 SDK 기준 `GenerateContentConfig`는 `systemInstruction`/`system_instruction` 계열 필드를 지원하므로, 구조 개선 자체는 타당하다.
   - 다만 이 변경은 **현재 live Gemini의 실제 BUY/WAIT/DROP 분포를 바꾸는 행동 변경**이므로, 무조건 same-day 반영 대상은 아니다.

2. **조건부 승인(P1): deterministic generation config 추가**
   - 현재 JSON 경로에서도 `temperature/top_p/top_k`가 명시되지 않는다.
   - 다만 `temperature=0.0`을 전 호출에 일괄 적용하는 것은 과하다.
   - 기계형 JSON 응답 경로에 한해 보수 설정을 넣는 방향은 맞지만, 텍스트 리포트/브리핑 경로와 분리해야 한다.

3. **보류(P2): response schema 전면 도입**
   - `response_schema` 미활용 지적은 사실이다.
   - 하지만 현 엔진의 JSON 응답은 단일 schema가 아니라 `entry`, `holding/exit`, `overnight`, `condition entry`, `condition exit`, `EOD top5` 등 여러 계약으로 나뉜다.
   - 따라서 이 항목은 범용 `_call_gemini_safe()` 한 줄 수정이 아니라, **schema registry + endpoint별 fallback**이 필요한 별도 작업이다.

4. **즉시 승인(P0): JSON 파싱 fast-path 보강**
   - 리뷰서에는 직접 안 적혔지만, 현재 `_call_gemini_safe()`는 `application/json`을 요청하고도 원문 `json.loads()`를 먼저 시도하지 않고 정규식 추출에 바로 의존한다.
   - 이는 behavior change가 아니라 파싱 보강이므로 **선반영 가능**하다.

5. **과장 보정**
   - `system prompt를 일반 contents에 넣었으니 모델이 지시를 거의 망각한다`, `temperature만 내리면 허튼소리 확률이 0에 수렴한다`는 표현은 과장이다.
   - 이번 작업지시서는 `환각 0%` 같은 문구 대신 **계약 안정성, 파싱 실패율, 판정 일관성, live 영향 범위** 기준으로 정리한다.

---

## 2. 근거

### 2-1. system instruction

- 현 구현의 `_call_gemini_safe()`는 `contents = [prompt, user_input] if prompt else [user_input]`로 프롬프트를 일반 contents에 포함한다.
- 로컬 `.venv`의 `google.genai.types.GenerateContentConfig` 시그니처에는 `systemInstruction`, `temperature`, `topP`, `topK`, `responseSchema`가 모두 존재한다.
- 따라서 리뷰의 핵심 사실관계는 맞다.
- 다만 현재 live 스캘핑 엔진은 Gemini가 고정이며, `SCALPING_SYSTEM_PROMPT`, `SCALPING_WATCHING_SYSTEM_PROMPT`, `SCALPING_BUY_RECOVERY_CANARY_PROMPT` 등 핵심 진입 경로가 모두 이 호출부를 지난다.
- 결론: 구조 개선은 맞지만 **판정축 변경**으로 봐야 하며, 무행동 보강과 같은 우선순위로 취급하면 안 된다.

### 2-2. deterministic generation config

- 현 코드의 `GenerateContentConfig`는 JSON일 때 `response_mime_type="application/json"`만 넣고 있다.
- 따라서 JSON 응답의 일관성 개선 여지는 있다.
- 하지만 텍스트 리포트(`generate_realtime_report`)와 브리핑(`analyze_scanner_results`)은 사람이 읽는 출력이며, JSON 기계 계약과 같은 강도로 묶을 필요는 없다.
- 결론: `require_json=True` 경로 우선으로 한정해야 한다.

### 2-3. response schema

- 리뷰의 방향은 맞지만 범위 정의가 부족하다.
- 현재 `ai_engine.py`에는 최소 다음 JSON 계약이 공존한다.
  - 진입/감시: `{"action","score","reason"}`
  - 보유/청산: `{"action","score","reason"}` 후 내부 compat 변환
  - 오버나이트: `{"action","confidence","reason","risk_note"}`
  - 조건검색 진입: `{"decision","confidence","order_type","position_size_ratio","invalidation_price","reasons","risks"}`
  - 조건검색 청산: `{"decision","confidence","trim_ratio","new_stop_price","reason_primary","warning"}`
  - EOD 번들: `{"market_summary","one_point_lesson","top5":[...]}`
- 결론: `response_schema`는 가능하지만 endpoint별 schema 분리가 필수다.

### 2-4. JSON 파싱

- 현 `_call_gemini_safe()`는 JSON 응답에서 `re.search(r'\\{.*\\}', raw_text, re.DOTALL)`만 사용한다.
- `application/json`을 요청한 이상 원문이 이미 순수 JSON이면 `json.loads(raw_text)`가 더 직접적이다.
- 결론: `raw_text -> json.loads -> fallback regex` 순으로 바꾸는 것이 가장 저위험이다.

---

## 3. 작업지시

### 3-1. P0 즉시 작업

1. `_call_gemini_safe()` JSON fast-path 추가
   - 변경:
     - `require_json=True` 경로에서 `raw_text = (response.text or "").strip()`
     - 먼저 `json.loads(raw_text)` 시도
     - 실패 시 기존 정규식 추출 fallback 유지
   - 금지:
     - 기존 regex fallback 즉시 제거
     - system instruction, temperature, schema 변경을 이 change set에 섞기
   - acceptance:
     - 기존 진입/오버나이트/조건검색/EOD JSON 반환 contract 불변
     - 텍스트 응답 경로 영향 없음
     - 관련 테스트 회귀 없음
   - rollback guard:
     - fast-path 분기 제거만으로 원복 가능해야 한다

### 3-2. P1 조건부 작업

2. system instruction 분리 적용
   - 변경:
     - prompt를 contents에서 분리하고 SDK 지원 `system instruction` 필드로 이동
     - contents에는 `user_input`만 남김
   - 범위:
     - 1차는 `require_json=True` 경로만 적용 검토
     - 텍스트 리포트/브리핑까지 일괄 확대하지 않는다
   - acceptance:
     - `BUY/WAIT/DROP`, `HOLD/TRIM/EXIT`, `condition/eod` JSON contract 유지
     - live-sensitive 경로에서 판정 변화량을 비교할 수 있도록 로그/메모 기준이 있어야 한다
   - rollback guard:
     - `TRADING_RULES` 또는 로컬 상수 1개로 ON/OFF 가능해야 한다
   - 운영 규칙:
     - live Gemini는 현재 기준 엔진이므로, 이 변경은 단순 refactor가 아니라 **실전 canary 후보**로 취급한다

3. deterministic config를 JSON 경로에 한정 적용
   - 변경:
     - `require_json=True`일 때만 `temperature=0.0` 우선 검토
     - `top_p/top_k`는 고정값 하드코딩보다 선택형 상수로 분리
   - 금지:
     - 텍스트 리포트/브리핑/EOD prose 경로까지 일괄 zero-temperature 적용
   - acceptance:
     - JSON 응답 일관성 개선이 목적이며, 단순 응답 길이 축소만으로 완료 판정하지 않는다
   - rollback guard:
     - `temperature/top_p/top_k` 세트 전체를 한 번에 끄는 스위치가 있어야 한다

### 3-3. P2 별도 축 후보

4. endpoint별 response schema registry 도입
   - 권장 방식:
     - `_call_gemini_safe()`에 범용 bool만 두지 말고 `schema_name` 또는 `response_schema` 인자를 명시적으로 받는다
     - `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1`처럼 분리한다
   - 필수 조건:
     - schema 적용 실패 시 기존 파싱 경로 fallback
     - endpoint별 후처리(`_normalize_scalping_action_schema`, EOD top5 정규화)와 충돌하지 않아야 한다
   - 금지:
     - 단일 `{"action","score","reason"}` schema를 전체 JSON 호출에 공통 적용
   - acceptance:
     - 최소 6개 계약 각각에 대해 테스트가 있어야 한다
     - `consecutive_failures` 증가율과 parse_fail 축을 별도 관찰 가능해야 한다

---

## 4. 권장 적용 순서

1. `P0 JSON fast-path`만 먼저 반영
2. 테스트 통과 후 parse_fail 회귀 없음 확인
3. `P1 system instruction`은 flag-off 기본값으로 설계
4. `P1 deterministic config`는 JSON 경로에만 제한
5. `P2 response schema`는 endpoint registry와 fallback까지 준비된 뒤 별도 change set으로 진행

---

## 5. 완료 기준

- **완료 판정**
  - `P0`는 same-day 코드/테스트로 닫을 수 있다.
  - `P1`은 `flag + rollback guard + live 영향 관찰 기준`이 없으면 착수 불가다.
  - `P2`는 endpoint별 schema/test/fallback 세트가 준비되지 않으면 착수 불가다.

- **다음 액션**
  - checklist에는 `P0 fast-path`, `P1 system instruction`, `P1 deterministic JSON config`, `P2 schema registry`를 한 항목에서 승인/보류로 닫는 후속 판정 슬롯을 남긴다.
  - live Gemini 변경축은 `buy_recovery_canary` 등 기존 active 축과 섞지 않고, 같은 날 반영 시에는 `기존 축 OFF -> restart.flag -> 새 축 ON` replacement 원칙을 따른다.
