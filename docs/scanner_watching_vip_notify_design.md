# 아침 브리핑 후 WATCHING 종목 VIP 안내 추가

## 목표
`final_ensemble_scanner.py`에서 `ai_engine.analyze_scanner_results(...)`가 끝난 직후,  
오늘 날짜(`rec_date=today`)로 등록된 `WATCHING` 종목의 **종목명 + (종목코드)** 목록을
`audience = "VIP_ALL"` 대상으로 별도 텔레그램 메시지로 발송한다.

이 기능은 **추가 AI 분석 없이** 단순 DB 조회 + EventBus 발행만 수행한다.

---

## 현재 구조 요약
현재 스캐너는 다음 흐름으로 동작한다.

1. 스캐너 결과를 `db.save_recommendation(...)`로 적재
2. `GeminiSniperEngine(...).analyze_scanner_results(...)`로 아침 브리핑 생성
3. `START_OF_DAY_REPORT` payload 또는 fallback 메시지를 `TELEGRAM_BROADCAST`로 발행

즉, 이번 요구사항은 **2번과 3번 사이**에 끼워 넣는 것이 가장 자연스럽다.

---

## 구현 원칙
- **별도 AI 호출 금지**
- **VIP_ALL 고정**
- `WATCHING` 종목은 오늘 날짜 기준으로만 조회
- 중복 종목은 `(종목코드, 종목명)` 기준으로 제거
- 종목이 없으면 메시지를 보내지 않음
- 기존 `START_OF_DAY_REPORT` 흐름은 유지

---

## 수정 파일
- `final_ensemble_scanner.py`

---

## 변경 사항

### 1) RecommendationHistory 모델 import 추가
`WATCHING` 목록은 ORM으로 직접 조회하는 편이 안전하다.

추가 import:
```python
from src.database.models import RecommendationHistory
```

---

### 2) WATCHING 목록 메시지 빌더 함수 추가
새 함수:
```python
def build_today_watching_message(db, target_date=None):
    ...
```

역할:
- `rec_date=today`, `status='WATCHING'` 인 레코드를 조회
- 종목명/종목코드만 뽑아서 중복 제거
- VIP 브로드캐스트용 Markdown 메시지 반환

예시 메시지:
```text
👀 **[오늘 감시 종목]**
총 `5개`

• **삼성전자** (005930)
• **SK하이닉스** (000660)
• **한화에어로스페이스** (012450)
```

---

### 3) analyze_scanner_results 직후 VIP 브로드캐스트 추가
추가 위치:
- `ai_briefing = ai_engine.analyze_scanner_results(...)` 직후
- `perf_report = get_performance_report(db)` 이전

추가 동작:
```python
watching_msg = build_today_watching_message(db, datetime.now().date())
if watching_msg:
    event_bus.publish(
        "TELEGRAM_BROADCAST",
        {
            "message": watching_msg,
            "audience": "VIP_ALL",
            "parse_mode": "Markdown"
        }
    )
```

---

## 기대 효과
- VIP 구독자는 AI 아침 브리핑 직후, **오늘 감시망에 오른 종목 전체 목록**을 바로 확인할 수 있다.
- 추가 AI 비용이 발생하지 않는다.
- 기존 아침 브리핑 로직과 충돌하지 않는다.

---

## 주의사항
- `WATCHING` 상태가 스캐너 저장 직후 실제로 채워지는 구조인지 운영 DB에서 확인 필요
- 다른 전략의 `WATCHING`도 오늘 날짜 기준이면 함께 노출된다.  
  만약 향후 `KOSPI_ML / KOSDAQ_ML`만 노출하고 싶다면 `strategy.in_(...)` 조건을 추가하면 된다.
- `START_OF_DAY_REPORT`와 별개 메시지이므로, 텔레그램 노출 순서는 EventBus 처리 타이밍에 따라 달라질 수 있다.  
  다만 현재 구조상 `analyze_scanner_results` 직후 발행되므로 실무상 충분히 가깝게 붙는다.
