# KORStockScan

KORStockScan은 키움 REST/WebSocket 기반의 한국 주식 자동매매 시스템입니다.  
현재 시스템은 `스윙 매매`와 `스캘핑 매매`를 함께 운영하며, 최근에는 웹 대시보드와 진입/복기 도구까지 포함한 운영형 구조로 확장되었습니다.

핵심 방향은 단순합니다.

- `감시`: 스캐너와 조건검색식이 후보를 찾습니다.
- `매수`: 엔진이 실시간 게이트를 통과한 종목만 진입합니다.
- `홀딩`: 보유 중 AI/손익/모멘텀/시간 기준으로 상태를 관리합니다.
- `매도`: 손절, 익절, 트레일링, 하방 리스크 규칙으로 청산합니다.
- `복기`: 웹 대시보드와 리포트로 진입 차단, 체결, 성과를 다시 분석합니다.

---

## 빠른 시작

### 운영 웹 주소

현재 운영 중인 웹 대시보드는 아래 주소에서 확인할 수 있습니다.

- 통합 대시보드: `https://korstockscan.ddns.net/`
- 일일 전략 리포트: `https://korstockscan.ddns.net/daily-report`
- 진입 게이트 차단 화면: `https://korstockscan.ddns.net/entry-pipeline-flow`
- 실제 매매 복기 화면: `https://korstockscan.ddns.net/trade-review`
- 전략 성과 분석: `https://korstockscan.ddns.net/strategy-performance`
- Gatekeeper 리플레이: `https://korstockscan.ddns.net/gatekeeper-replay`
- 성능 튜닝 모니터: `https://korstockscan.ddns.net/performance-tuning`

통합 대시보드(`/`, `/dashboard`)에서는 아래 6개 화면을 탭처럼 전환해서 볼 수 있습니다.

1. 일일 전략 리포트
2. 진입 게이트 차단
3. 실제 매매 복기
4. 전략 성과 분석
5. Gatekeeper 리플레이
6. 성능 튜닝 모니터

추천 활용 순서:

1. 장 시작 전에는 `일일 전략 리포트`로 시장 톤과 직전 성과를 확인합니다.
2. 장중에는 `진입 게이트 차단`으로 왜 실제 주문까지 못 갔는지 봅니다.
3. 체결 후에는 `실제 매매 복기`에서 홀딩/청산 흐름을 확인합니다.
4. 장중/장후 전략별 성과 비교는 `전략 성과 분석`에서 확인합니다.
5. 스윙 보류 종목은 `Gatekeeper 리플레이`로 그 시점 AI 판단을 되짚습니다.
6. 장마감 후에는 `성능 튜닝 모니터`에서 엔진 지표와 실제 성과 추세를 같이 봅니다.

### JSON API

Flutter나 외부 서비스는 아래 API를 그대로 사용하면 됩니다.

- 일일 리포트: `/api/daily-report?date=YYYY-MM-DD`
- 진입 게이트 플로우: `/api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- 실제 매매 복기: `/api/trade-review?date=YYYY-MM-DD&code=000000`
- 전략 성과 분석: `/api/strategy-performance?date=YYYY-MM-DD`
- 동적 체결강도: `/api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- Gatekeeper 리플레이: `/api/gatekeeper-replay?date=YYYY-MM-DD&code=000000&time=HH:MM:SS`
- 성능 튜닝 모니터: `/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS`

활용 포인트:

- Flutter는 위 API를 그대로 유지한 채 화면만 별도로 구성할 수 있습니다.
- 운영 웹은 Flask에서 같은 집계 모듈을 렌더링하므로, 웹/앱/CLI 숫자가 일치하는 구조를 목표로 합니다.
- `since`를 생략하면 오늘 날짜 화면은 자동으로 최근 2시간 오프셋을 사용합니다.

### 핵심 실행 파일

- 메인 봇: `python3 src/bot_main.py`
- 일일 리포트 생성: `python3 src/web/daily_report_generator.py --date 2026-04-03`
- 동적 체결강도 집계: `python3 src/tests/test_strength_momentum_observation.py --date 2026-04-03 --top 10`
- shadow 피드백 평가: `python3 src/tests/test_strength_shadow_feedback.py --date 2026-04-03`

테스트와 운영 점검은 저장소 가상환경 기준 실행을 권장합니다.

- 가상환경 파이썬: `/home/ubuntu/KORStockScan/.venv/bin/python`
- 예시:
  `/home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_condition_open_reclaim.py`

---

## 시스템 라이프사이클

이 프로젝트는 기능별보다 `감시 -> 매수 -> 홀딩 -> 매도 -> 복기` 흐름으로 이해하는 것이 가장 쉽습니다.

### 1. 감시

감시 단계에서는 스캐너와 조건검색식이 “지금 볼 만한 종목”을 좁혀 줍니다.

- 스윙 감시
  - `src/scanners/final_ensemble_scanner.py`
  - `src/scanners/kosdaq_scanner.py`
  - `src/model/recommend_daily_v2.py`
- 스캘핑 감시
  - `src/scanners/scalping_scanner.py`
  - `src/engine/sniper_condition_handlers.py`
  - `src/engine/kiwoom_websocket.py`

주요 특징:

- 스윙은 일봉/수급/모델 점수 기반으로 후보를 압축합니다.
- 스캘핑은 조건검색식, 실시간 체결, 호가 흐름을 기반으로 즉시 감시망을 구성합니다.
- 감시 종목은 DB와 메모리 상태를 함께 사용해 `WATCHING` 상태로 진입합니다.

현재 운영 중인 주요 스캘핑 조건검색식:

- `scalp_open_reclaim_01`
  - 사용 시간: `09:03 ~ 09:20`
  - 태그: `OPEN_RECLAIM`
  - 즉시 감시 편입형
- `scalp_vwap_reclaim_01`
  - 사용 시간: `10:00 ~ 14:00`
  - 태그: `VWAP_RECLAIM`
  - 즉시 편입하지 않고 전처리 후 편입
  - 편입 조건: `현재가 > VWAP` 이고 `VWAP 대비 +0.1% ~ +1.0%`

조건검색 운용 원칙:

- 같은 종목이라도 `strategy`가 다르면 active target 공존이 가능합니다.
- 조건검색 편입 중복 기준은 `code + strategy`입니다.
- `position_tag`는 내부적으로 전략별 기본 태그로 정규화됩니다.
  - `SCALPING -> SCALP_BASE`
  - `KOSPI_ML -> KOSPI_BASE`
  - `KOSDAQ_ML -> KOSDAQ_BASE`
- 실시간 엔진의 active target 중복 판정도 `code + strategy`가 아니라 `target_identity(code, strategy)` 기준으로 맞춰져 있습니다.

### 2. 매수

매수 단계에서는 “좋아 보이는 종목”이 아니라 “실시간으로 아직 늦지 않은 종목”만 진입합니다.

핵심 파일:

- `src/engine/kiwoom_sniper_v2.py`
- `src/engine/sniper_state_handlers.py`
- `src/engine/sniper_entry_latency.py`
- `src/engine/kiwoom_orders.py`
- `src/trading/entry/`
- `src/trading/market/`

주요 게이트:

1. 스캐너/조건검색 기반 감시 상태 확인
2. AI 확답 또는 전략 자격 확인
3. 동적 체결강도/정적 VPW/시장환경/게이트키퍼 점검
4. 주문 가능 금액과 전략 비중 계산
5. latency-aware entry 판단
6. 실제 주문 전송

매수 관련 운영 포인트:

- 주문 수량은 `주문가능금액 x 전략비중 x 안전계수`를 기본으로 계산합니다.
- 1주 매수는 가능한데 95% 절삭 때문에 0주가 되는 경우에만 완화 안전계수로 1회 재계산합니다.
- `pause.flag`가 있으면 신규 매수와 추가매수는 막고, 청산은 계속 수행합니다.
- 스캘핑은 `entry_armed` 상태를 두어 자격 게이트를 통과한 직후 다시 되감기지 않도록 보강되어 있습니다.

### 3. 홀딩

홀딩 단계에서는 “보유 중인 종목이 여전히 들고 갈 가치가 있는지”를 계속 재평가합니다.

핵심 파일:

- `src/engine/sniper_state_handlers.py`
- `src/engine/sniper_execution_receipts.py`
- `src/engine/kiwoom_sniper_v2.py`

주요 관리 항목:

- 평균단가와 누적 체결 수량
- AI 점수 추이
- 손익률, 고점 대비 되밀림
- 추가매수 조건
- 보유 시간과 전략 태그

홀딩 관련 운영 포인트:

- 최근 버전에서는 `HOLDING_PIPELINE` 로그를 별도로 남겨, 보유 중 판단 흐름을 복기하기 쉽게 했습니다.
- AI 조기 개입은 휩소 방어를 위해 `손실폭`, `최소 유지 시간`, `연속성` 가드를 적용합니다.
- fallback 진입의 scout/main 체결도 하나의 포지션으로 정합성 있게 복원하도록 보강되어 있습니다.
- 스캘핑 체결 복원 시 `position_tag='MIDDLE'`로 되돌리지 않고, 전략 기본 태그 또는 원래 태그를 유지하도록 정규화됩니다.

### 4. 매도

매도는 스윙과 스캘핑 모두에서 가장 보수적으로 동작해야 하는 단계입니다.

대표 규칙:

- 하드스탑 / 소프트스탑
- 목표 수익 도달 후 익절
- 트레일링 익절
- AI 하방 리스크 조기 청산
- 시간 초과 청산

핵심 파일:

- `src/engine/sniper_state_handlers.py`
- `src/engine/kiwoom_orders.py`
- `src/engine/sniper_execution_receipts.py`

운영 포인트:

- SELL은 pause 상태에서도 막지 않습니다.
- entry BUY 미체결이 남아 있으면 취소 후 청산으로 넘어가도록 처리합니다.
- 시장가, 지정가, IOC 성격은 주문 계층에서 일관되게 관리합니다.

### 5. 복기

복기 단계는 이제 운영의 일부입니다.  
진입이 왜 막혔는지, 실제 체결 후 왜 손절/익절됐는지, 하루 성적이 어땠는지를 웹에서 확인할 수 있습니다.

웹 화면:

1. 일일 전략 리포트
2. 진입 게이트 차단
3. 실제 매매 복기
4. 전략 성과 분석
5. Gatekeeper 리플레이
6. 성능 튜닝 모니터

핵심 파일:

- `src/web/app.py`
- `src/web/daily_report_generator.py`
- `src/engine/daily_report_service.py`
- `src/engine/sniper_entry_pipeline_report.py`
- `src/engine/sniper_trade_review_report.py`
- `src/engine/sniper_strength_observation_report.py`
- `src/engine/sniper_gatekeeper_replay.py`
- `src/engine/sniper_performance_tuning_report.py`

---

## Topic 별 구조

아래는 “파일이 어디에 있는가”보다 “무슨 책임을 갖는가” 기준의 정리입니다.

### 1. 스캐너와 후보 생성

- `src/scanners/`
  - 스윙, 코스닥, 스캘핑, 위기 감시 스캐너
- `src/model/`
  - V2 추천 모델, 피처 엔지니어링, 추천 CSV 생성
- `data/daily_recommendations_v2.csv`
  - 모델 결과를 엔진 감시 후보로 넘기기 직전의 브리지 파일

### 2. 실시간 엔진과 상태머신

- `src/engine/kiwoom_sniper_v2.py`
  - 전체 실시간 매매 엔진 오케스트레이션
- `src/engine/sniper_state_handlers.py`
  - `WATCHING`, `BUY_ORDERED`, `HOLDING`, `SELL_ORDERED` 상태 처리
- `src/engine/sniper_execution_receipts.py`
  - 체결 영수증, 평균단가, 수량 정합성 반영
- `src/engine/kiwoom_orders.py`
  - 주문/취소/청산 래퍼

### 3. 실시간 체결·호가·웹소켓

- `src/engine/kiwoom_websocket.py`
  - 실시간 시세/체결/조건검색식/프로그램 매매 데이터 수신
- `src/engine/sniper_condition_handlers.py`
  - 조건검색식 포착/이탈과 전략 라우팅
- `src/engine/sniper_strength_momentum.py`
  - 동적 체결강도 계산

운영 주의:

- 웹소켓 `REG`는 현재 배치 전송을 사용합니다.
- 기본 배치 크기는 `WS_REG_BATCH_SIZE=20`입니다.
- `숫자 6자리`가 아닌 종목코드는 실시간 등록에서 자동 제외됩니다.
- 재연결 루프가 생기면 `logs/bot_history.log`에서 `code`, `reason`, 등록 제외 코드, 조건검색식 목록을 먼저 봅니다.
- 조건검색식별 편입 규칙은 핸들러에서 바로 처리합니다.
  - `scalp_open_reclaim_01`: 시간창만 맞으면 즉시 편입
  - `scalp_vwap_reclaim_01`: VWAP 밴드 전처리 통과 시에만 편입
- 조건검색/포지션 태그 구조 점검 문서는 [docs/position_tag_strategy_impact_audit.md](/home/ubuntu/KORStockScan/docs/position_tag_strategy_impact_audit.md)를 참고합니다.

### 4. 진입 품질 제어

- `src/trading/entry/`
  - entry policy, fallback strategy, orchestrator
- `src/trading/market/`
  - websocket quote health/cache
- `src/trading/order/`
  - tick utils, order manager
- `src/trading/config/entry_config.py`
  - 레이턴시/스프레드 기준
- `src/engine/sniper_entry_latency.py`
  - 엔진과 latency 계층 연결

핵심 원칙:

- 주문 직전 가격 재조회 대신 내부 websocket cache를 사용합니다.
- `SAFE`는 일반 진입, `CAUTION`은 fallback, `DANGER`는 진입 차단입니다.
- 늦은 체결 영수증은 grace window 안에서 다시 매칭합니다.

### 5. 시장 환경과 거시 판단

- `src/market_regime/`
  - VIX, WTI, Fear & Greed 기반 시장환경 판단
- `src/engine/sniper_market_regime.py`
  - 시장환경 결과를 실시간 엔진 게이트와 연결

운영 포인트:

- 시장환경 스냅샷은 세션 캐시/폴백을 사용합니다.
- 일시적인 외부 데이터 빈값 때문에 전체 진입 로직이 흔들리지 않도록 설계되어 있습니다.

### 6. 운영 제어와 알림

- `src/notify/telegram_manager.py`
  - 텔레그램 제어/알림
- `src/utils/runtime_flags.py`
  - `pause.flag` 관리
- `src/engine/sniper_entry_metrics.py`
  - 장중/장마감 진입 지표 요약

메시지 대상 구분:

- 관리자 즉시 알림
- 관리자 전용 브로드캐스트
- VIP/관리자 공용 브로드캐스트

### 7. 웹 대시보드와 외부 서비스

- `src/web/app.py`
  - Flask 웹 엔트리포인트
- `src/web/daily_report_generator.py`
  - 일일 리포트 생성
- `src/engine/*_report.py`
  - 웹/API용 집계 모듈

외부 서비스 운영 원칙:

- `bot_main.py`는 리포트 JSON 생성 담당
- `src/web/app.py`는 `gunicorn + nginx` 조합으로 외부 공개
- Flutter는 JSON API를 그대로 소비하는 구조를 유지

---

## 디렉터리 구조

현재 운영 관점에서 보면 아래 구조로 이해하면 됩니다.

```text
KORStockScan/
├── src/
│   ├── bot_main.py                # 메인 실행 진입점
│   ├── core/                      # 공용 EventBus, 코어 유틸
│   ├── database/                  # DB 세션/모델
│   ├── engine/                    # 실시간 엔진, 상태머신, 보고서 집계
│   ├── market_regime/             # VIX/WTI/FNG 기반 시장환경 판단
│   ├── model/                     # V2 모델 학습/추천 파이프라인
│   ├── notify/                    # 텔레그램 알림/명령
│   ├── scanners/                  # 스윙/스캘핑/코스닥 스캐너
│   ├── tests/                     # 운영 점검용 스크립트와 테스트
│   ├── trading/                   # latency-aware entry 계층
│   │   ├── config/
│   │   ├── entry/
│   │   ├── logging/
│   │   ├── market/
│   │   └── order/
│   ├── utils/                     # 상수, 로거, 키움 유틸, 런타임 플래그
│   └── web/                       # Flask 대시보드와 리포트 생성기
├── data/                          # 추천 CSV, 캐시, 리포트, shadow 결과
├── deploy/
│   ├── nginx/                     # nginx 설정 샘플
│   └── systemd/                   # gunicorn/web 서비스 파일
├── docs/                          # 설계 문서, 런북, 운영 문서
├── logs/                          # 파일 로그
├── requirements.txt
└── README.md
```

---

## 웹 페이지 안내

운영자가 가장 자주 보는 화면은 아래 6개입니다.

### 1. 통합 대시보드

- 주소: `https://korstockscan.ddns.net/`
- 용도: 일일 리포트, 진입 차단, 실제 매매 복기를 한 화면에서 전환

추천 상황:

- 장 시작 전: 당일 전략 리포트 확인
- 장중: 진입 차단 이유 확인
- 장 종료 후: 체결/청산 복기
- 튜닝 검토: 성능 튜닝 모니터와 함께 연결 확인

### 2. 일일 전략 리포트

- 주소: `https://korstockscan.ddns.net/daily-report`
- 용도: 시장 진단, 전일 성과, 전략별 성과, 후보 리스트 확인

유용한 옵션:

- 강제 새로 생성:
  `https://korstockscan.ddns.net/daily-report?date=2026-04-03&refresh=1`

### 3. 진입 게이트 차단 화면

- 주소: `https://korstockscan.ddns.net/entry-pipeline-flow`
- 용도: 감시 종목이 실제 주문까지 가지 못한 이유를 단계별로 추적

확인 포인트:

- 어떤 게이트에서 가장 많이 막히는지
- 특정 종목이 `AI 확답`까지 갔는지
- 마지막 확정 진입 실패 사유가 무엇인지

### 4. 실제 매매 복기 화면

- 주소: `https://korstockscan.ddns.net/trade-review`
- 용도: 체결 이후 보유/청산까지의 흐름과 실제 손익을 재분석

예시:

- 특정 종목 복기:
  `https://korstockscan.ddns.net/trade-review?date=2026-04-03&code=388050`

### 5. Gatekeeper 리플레이

- 주소: `https://korstockscan.ddns.net/gatekeeper-replay`
- 용도: 스윙 보류 시점의 `realtime_ctx + action + report`를 다시 확인

추천 상황:

- `게이트키퍼: 눌림 대기`가 과하게 보이는지 점검할 때
- `전량 회피` 판단이 실제로도 타당했는지 복기할 때
- 프롬프트나 FID 문맥을 바꾼 뒤 전후 차이를 비교할 때

### 6. 전략 성과 분석

- 주소: `https://korstockscan.ddns.net/strategy-performance`
- 용도: `strategy x position_tag` 기준으로 실제 종료 성과를 일 단위로 비교

핵심 포인트:

- 같은 전략 안에서도 `SCANNER`, `SCALP_BASE`, `VCP_NEXT` 같은 태그별 손익 차이가 나는지
- 승률보다 `평균 기대손익`, `미종료 비중`, `평균 보유시간`이 더 나쁜 버킷이 없는지
- 최고 성과 버킷과 주의 버킷이 매일 어디에 형성되는지

최근 KPI:

- 종료 승률
- 평균 기대손익
- 미종료 비중
- 평균 보유시간
- 최고 성과 버킷 / 주의 버킷
- 최고 익절 거래 / 최대 손실 거래

### 7. 성능 튜닝 모니터

- 주소: `https://korstockscan.ddns.net/performance-tuning`
- 용도: 캐시/fast reuse/skip 비율 같은 엔진 지표와, 스캘핑·스윙 실제 성과를 연결해서 봄

핵심 포인트:

- 보유 AI skip 비율이 높을 때 실제 손익이 유지되는지
- Gatekeeper fast reuse 비율이 높을 때 스윙 진입 기회가 줄어드는지
- 최근 5거래일 / 20거래일 성과 추세가 현재 튜닝 방향과 맞는지

추천 상황:

- 레이턴시와 outdated trade-off를 조정할 때
- 스캘핑 동적 체결강도 문턱이 너무 보수적인지 점검할 때
- 스윙 Gatekeeper와 gap 기준을 완화할지 판단할 때

---

## 웹 활용 가이드

웹 대시보드는 단순 조회 화면이 아니라 `운영 판단 보조도구`로 쓰는 것이 핵심입니다.

### 1. 장 시작 전

- `일일 전략 리포트`에서 시장 톤, 직전 매매일 성적, 전략별 상태를 확인합니다.
- `성능 튜닝 모니터`에서 최근 추세가 약해진 전략이 있는지 먼저 점검합니다.

### 2. 장중 진입 점검

- 신규 후보가 안 들어오면 `진입 게이트 차단`을 먼저 확인합니다.
- 스캘핑은 `동적 체결강도`, `지연 리스크`, `AI 점수`를 봅니다.
- 스윙은 `게이트키퍼`, `스윙 갭상승`, `시장환경`을 봅니다.

### 3. 장중/장후 체결 복기

- 실제 체결 건은 `실제 매매 복기`에서 봅니다.
- 보유 중 AI 조기 개입, 손절, 익절, fallback 진입이 어떻게 작동했는지 `HOLDING_PIPELINE` 기반으로 확인합니다.

### 4. 스윙 보류 해석

- 스윙이 자주 막히면 `Gatekeeper 리플레이`를 사용합니다.
- `눌림 대기`는 재평가를 기다릴 가치가 있는지, `전량 회피`는 구조적 리스크 판단이 타당한지 봅니다.

### 5. 튜닝 결정

- `성능 튜닝 모니터`에서 엔진 지표만 보지 말고, 스캘핑/스윙 성과 카드와 자동 권장 코멘트를 같이 봅니다.
- `전략 성과 분석`에서 손실이 집중되는 `strategy / position_tag` 버킷이 있는지 먼저 확인하면 튜닝 우선순위를 더 빨리 정할 수 있습니다.
- 최근 5거래일과 20거래일 추세가 엇갈리면 즉시 완화/강화보다 보수적 관찰이 더 안전합니다.

---

## 운영 점검 명령

### 봇과 웹

- 메인 봇 실행:
  `python3 src/bot_main.py`
- Gunicorn 상태:
  `sudo systemctl status korstockscan-gunicorn.service`
- Nginx 상태:
  `sudo systemctl status nginx`

### 로그 확인

- Gunicorn 로그:
  `sudo journalctl -u korstockscan-gunicorn.service -f`
- Nginx 로그:
  `sudo journalctl -u nginx -f`
- 엔진 정보 로그:
  `tail -f logs/sniper_state_handlers_info.log`
- 체결 영수증 로그:
  `tail -f logs/sniper_execution_receipts_info.log`
- 운영 히스토리:
  `tail -f logs/bot_history.log`

로그 운영 원칙:

- `sniper_state_handlers_info.log`는 당일 평문 로그와 회전본을 우선 사용합니다.
- 장마감 후에는 핵심 모니터 스냅샷과 날짜별 gzip 아카이브를 함께 남깁니다.
- 과거 복기 화면은 평문 로그가 밀려도 저장 스냅샷과 gzip 아카이브를 fallback으로 읽도록 설계되어 있습니다.

### 리포트/집계

- 일일 리포트 점검:
  `python3 src/tests/test_daily_report.py --date 2026-04-03`
- 진입 플로우 점검:
  `python3 src/tests/test_entry_pipeline_flow.py --date 2026-04-03 --top 10`
- 실제 매매 복기 점검:
  `/home/ubuntu/KORStockScan/.venv/bin/python src/tests/test_trade_review_report.py --date 2026-04-03 --code 388050`
- 전략/포지션태그 성과 점검:
  `/home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_strategy_position_performance_report.py`
- 조건검색식 시간창/전처리 점검:
  `/home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_condition_open_reclaim.py`
- position_tag 정규화 점검:
  `/home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_position_tag_normalization.py`

### 인증서와 웹서비스

- 인증서 갱신 점검:
  `sudo certbot renew --dry-run`
- Nginx 설정 검사:
  `sudo nginx -t`

상세 절차는 [docs/ec2_web_service_runbook.md](/home/ubuntu/KORStockScan/docs/ec2_web_service_runbook.md)를 참고합니다.

---

## 배포와 운영 구조

현재 외부 서비스 공개는 EC2 기반으로 운영합니다.

구성:

1. `Domain / DDNS`
2. `Elastic IP`
3. `Nginx(80/443)`
4. `Gunicorn(127.0.0.1:5000)`
5. `Flask app`

관련 파일:

- [deploy/nginx/korstockscan.conf](/home/ubuntu/KORStockScan/deploy/nginx/korstockscan.conf)
- [deploy/systemd/korstockscan-gunicorn.service](/home/ubuntu/KORStockScan/deploy/systemd/korstockscan-gunicorn.service)
- [docs/ec2_web_service_runbook.md](/home/ubuntu/KORStockScan/docs/ec2_web_service_runbook.md)

운영 원칙:

- 외부 공개 포트는 `80`, `443`만 사용합니다.
- Gunicorn은 로컬 루프백에서만 수신합니다.
- TLS는 `certbot --nginx`로 관리합니다.

---

## V2 모델과 추천 파일

현재 일일 추천 계층은 V2 모델 파이프라인을 기준으로 움직입니다.

주요 구성:

- `src/model/dataset_builder_v2.py`
- `src/model/feature_engineering_v2.py`
- `src/model/train_hybrid_xgb_v2.py`
- `src/model/train_hybrid_lgbm_v2.py`
- `src/model/train_bull_specialists_v2.py`
- `src/model/train_meta_model_v2.py`
- `src/model/recommend_daily_v2.py`

주요 산출물:

- `data/daily_recommendations_v2.csv`

운영 의미:

- 이 CSV는 모델 결과를 엔진의 실제 감시 후보로 넘기기 직전의 브리지 파일입니다.
- 스캐너는 이 파일을 읽어 `WATCHING` 추천 이력을 생성합니다.

---

## 문서 모음

자주 참고하는 문서:

- [docs/ec2_web_service_runbook.md](/home/ubuntu/KORStockScan/docs/ec2_web_service_runbook.md)
- [docs/latency_aware_entry_system_summary.md](/home/ubuntu/KORStockScan/docs/latency_aware_entry_system_summary.md)
- [docs/market_time_offset_audit.md](/home/ubuntu/KORStockScan/docs/market_time_offset_audit.md)
- [docs/scalping_dynamic_strength_gate_design.md](/home/ubuntu/KORStockScan/docs/scalping_dynamic_strength_gate_design.md)
- [docs/scalping_dynamic_strength_gate_work_order.md](/home/ubuntu/KORStockScan/docs/scalping_dynamic_strength_gate_work_order.md)
- [docs/ml_gatekeeper_design.md](/home/ubuntu/KORStockScan/docs/ml_gatekeeper_design.md)

---

## 필수 환경

필요한 대표 입력:

- `data/config_prod.json`
- 키움 API 인증 정보
- PostgreSQL 연결 정보
- 모델 파일과 일봉 데이터

권장:

- 실거래 적용 전에는 모의환경 또는 소액 검증
- 웹/봇/리포트는 같은 운영 데이터 기준으로 확인

---

## 면책사항

본 프로젝트는 개인 연구, 시스템 트레이딩 실험, 운영 자동화 목적으로 작성되었습니다.

1. 모든 투자 판단과 매매 실행의 책임은 사용자 본인에게 있습니다.
2. 자동매매 시스템은 네트워크 장애, API 변경, 체결 지연, 데이터 오류, 로직 버그로 인해 손실이 발생할 수 있습니다.
3. 실거래 적용 전에는 반드시 모의환경 또는 소액 검증을 거쳐야 합니다.
4. 본 저장소의 코드와 문서는 수익을 보장하지 않으며, 특정 종목 매수/매도를 권유하지 않습니다.
