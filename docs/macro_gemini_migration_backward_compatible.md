# Macro Briefing 최종 설계서
ECOS 유지 / GDELT 제거 / FRED 제거 / Gemini 구조화 JSON + freshness 검증 도입  
**후방 호환 포함: 기존 `config_prod.json` 의 `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` 구조 유지**

## 1. 결정 요약

이번 변경의 목적은 `macro_briefing_complete.py` 에서 FRED/GDELT 의 시의성 문제를 제거하고,  
ECOS 는 기존 API 추출을 유지하면서 나머지 매크로 정보는 **Gemini 기반 구조화 JSON 공급자**로 대체하는 것이다.

이번 최종안의 핵심은 아래와 같다.

- **ECOS 유지**
  - `usdkrw`, `kr3y`, `kr10y` 는 기존 ECOS API 유지
- **GDELT 제거**
  - headline/event 수집은 Gemini 구조화 JSON 으로 대체
- **FRED 제거**
  - `sp500`, `nasdaq`, `vix`, `us10y`, `brent` 는 Gemini 구조화 JSON 으로 대체
- **룰 엔진 유지**
  - `MacroSignalEngine` 는 유지
  - Gemini 는 “최종 판단기”가 아니라 “정형 데이터 공급자”
- **freshness 검증 필수**
  - `as_of`, `published_at` 가 stale 이면 폐기
- **설정 후방 호환**
  - 새 코드가 `GEMINI_API_KEYS` 와 기존 `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` 를 모두 읽음
  - 따라서 기존 `config_prod.json` 구조를 바꾸지 않아도 됨

---

## 2. 왜 후방 호환이 중요한가

현재 운영 설정은 평면 키 구조를 사용 중일 가능성이 높다.

```json
{
  "GEMINI_API_KEY": "...",
  "GEMINI_API_KEY_2": "...",
  "GEMINI_API_KEY_3": "..."
}
```

이 구조를 억지로 아래처럼 바꾸면:

```json
{
  "GEMINI_API_KEYS": ["...", "...", "..."]
}
```

다른 코드가 기존 키명을 직접 읽고 있을 경우 영향이 갈 수 있다.

따라서 가장 안전한 방식은:

- **설정 파일은 그대로 유지**
- **새 매크로 코드만 양쪽 형식을 모두 지원**

이 방식이면:
- 기존 프로그램 영향 최소화
- 신규 매크로 전환 가능
- 점진적 이전 가능

---

## 3. 제안 아키텍처

```text
config_prod.json / config_dev.json
        │
        ▼
MacroBriefingBuilder
 ├─ ECOS API (기존 유지)
 └─ GeminiMacroProvider (신규)
       └─ GeminiJsonClient (신규 경량 공용 클라이언트)
              └─ Gemini JSON 응답

Gemini raw JSON
   └─ freshness / schema 검증
         ├─ MarketSeriesPoint 로 변환
         └─ NewsHeadline 로 변환

MacroSignalEngine
   └─ 기존 룰로 risk_on / neutral / risk_off 계산
```

---

## 4. 신규/변경 파일

### 신규
- `src/engine/gemini_json_client.py`

### 수정
- `src/engine/macro_briefing_complete.py`

### 비수정
- `src/engine/ai_engine.py`
  - macro 모듈이 기존 `ai_engine.py` 를 import 하지 않음
  - 이유: 순환 import 방지

---

## 5. 설정 키 정책

### 권장
기존 `config_prod.json` 은 **그대로 유지**한다.

예시:

```json
{
  "ECOS_API_KEY": "기존값",
  "GEMINI_API_KEY": "key1",
  "GEMINI_API_KEY_2": "key2",
  "GEMINI_API_KEY_3": "key3",
  "MACRO_GEMINI_MODEL": "gemini-2.5-flash-lite",
  "MACRO_GEMINI_MARKET_MAX_AGE_HOURS": 72,
  "MACRO_GEMINI_HEADLINE_MAX_AGE_HOURS": 18
}
```

### 신규 형식도 지원
원하면 아래 형식도 가능하다.

```json
{
  "GEMINI_API_KEYS": ["key1", "key2", "key3"]
}
```

### 최종 우선순위
1. `GEMINI_API_KEYS` (list 또는 comma-separated string)
2. `GEMINI_API_KEY`
3. `GEMINI_API_KEY_2`
4. `GEMINI_API_KEY_3`
5. 이후 `_4` ~ `_10`

### 중복 키 처리
- 자동 dedupe
- 동일 키가 중복되어도 1회만 사용

---

## 6. Gemini 응답 계약(JSON)

Gemini 는 아래 구조를 반드시 반환해야 한다.

```json
{
  "created_at": "2026-03-30 06:40:00 KST",
  "series": {
    "sp500": {
      "value": 5712.2,
      "prev_value": 5668.3,
      "change": 43.9,
      "change_pct": 0.77,
      "as_of": "2026-03-29 16:00:00 EDT",
      "source": "grounded_gemini"
    },
    "nasdaq": {
      "value": 18123.4,
      "prev_value": 18495.1,
      "change": -371.7,
      "change_pct": -2.01,
      "as_of": "2026-03-29 16:00:00 EDT",
      "source": "grounded_gemini"
    },
    "vix": {
      "value": 21.4,
      "prev_value": 18.8,
      "change": 2.6,
      "change_pct": 13.83,
      "as_of": "2026-03-29 16:00:00 EDT",
      "source": "grounded_gemini"
    },
    "us10y": {
      "value": 4.27,
      "prev_value": 4.19,
      "change": 0.08,
      "change_pct": 1.91,
      "as_of": "2026-03-29 16:00:00 EDT",
      "source": "grounded_gemini"
    },
    "brent": {
      "value": 83.7,
      "prev_value": 81.1,
      "change": 2.6,
      "change_pct": 3.21,
      "as_of": "2026-03-29 16:00:00 EDT",
      "source": "grounded_gemini"
    }
  },
  "headlines": [
    {
      "title": "Brent jumps as Middle East supply risk rises",
      "source": "Reuters",
      "published_at": "2026-03-30 05:58:00 KST",
      "url": "https://...",
      "score": 0.9,
      "tags": ["oil", "middle_east", "risk_off"]
    }
  ],
  "notes": ["optional notes"]
}
```

---

## 7. freshness 검증 규칙

### 시리즈 데이터
각 시리즈는 아래를 통과해야 한다.

- `as_of` 존재
- `as_of` 파싱 가능
- `현재시각 - as_of <= MACRO_GEMINI_MARKET_MAX_AGE_HOURS`
- `value` 또는 `change_pct` 중 최소 하나 존재

실패 시:
- 해당 시리즈는 `None`
- `missing_sources` 에 기록
- 전체 실패로 간주하지 않음

### headline 데이터
각 headline 은 아래를 통과해야 한다.

- `title` 존재
- `published_at` 존재
- `published_at` 파싱 가능
- `현재시각 - published_at <= MACRO_GEMINI_HEADLINE_MAX_AGE_HOURS`

실패 시:
- 해당 headline 폐기
- `missing_sources` 에 기록

---

## 8. 구현 포인트

### A. 룰 엔진 유지
Gemini 가 바로 risk_on/risk_off 를 말하더라도 최종 판정은 `MacroSignalEngine` 가 수행한다.

### B. 순환 import 금지
`src/engine/gemini_json_client.py` 를 별도로 두고 `ai_engine.py` 는 건드리지 않는다.

### C. 전체 실패보다 부분 누락 허용
일부 시리즈나 headline 만 stale 이어도 브리핑 전체를 죽이지 않는다.

### D. 설정 변경 없는 전환
이번 변경은 운영 설정 충격을 최소화하는 것이 중요하므로 `config_prod.json` 구조를 강제 변경하지 않는다.

---

## 9. 수동 테스트 시나리오 5개

1. **기존 flat key 구조 테스트**
   - `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, `GEMINI_API_KEY_3` 만 있는 config 로 실행
   - Gemini provider 가 정상 초기화되는지 확인

2. **신규 배열형 키 테스트**
   - `GEMINI_API_KEYS` 배열만 있는 config 로 실행
   - 정상 초기화 및 로테이션 확인

3. **stale market data 테스트**
   - Gemini 응답의 `as_of` 를 7일 전으로 만들어 주입
   - 해당 시리즈만 `missing_sources` 로 빠지고 전체는 계속 동작하는지 확인

4. **stale headline 테스트**
   - `published_at` 을 2일 전으로 만들어 주입
   - headline 폐기 및 로그 기록 확인

5. **ECOS 정상 + Gemini 부분 실패 테스트**
   - Gemini 일부 시리즈 누락
   - ECOS 값은 정상 반영되고 `build_macro_text()` 가 부분 브리핑을 만드는지 확인

---

## 10. 잠재 버그 / 주의점 5개

1. Gemini 가 timezone 문자열 형식을 들쭉날쭉하게 줄 수 있음
2. `as_of` 없이 숫자만 주는 응답은 freshness 검증에서 탈락함
3. 주말/휴장일에는 market age 허용 시간을 너무 짧게 잡으면 false stale 이 날 수 있음
4. headline 중복 제목이 아주 미세하게 다르면 dedupe 가 완벽하지 않을 수 있음
5. 장기적으로는 Gemini grounding 품질 변화에 따라 prompt 조정이 필요할 수 있음

---

## 11. 운영 권고

- 지금은 **config_prod.json 구조를 바꾸지 말 것**
- 새 코드만 후방 호환으로 넣을 것
- 안정화 후에만 `GEMINI_API_KEYS` 배열형 통합을 검토할 것
