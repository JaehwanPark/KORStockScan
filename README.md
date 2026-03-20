# 🚀 KORStockScan V14.0 - 완전 자동화 멀티 엔진 퀀트 스나이퍼

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python&logoColor=white)
![Kiwoom API](https://img.shields.io/badge/API-Kiwoom_REST-green?style=flat-square)
![Machine Learning](https://img.shields.io/badge/ML-XGBoost_%7C_LightGBM-orange?style=flat-square)
![Generative AI](https://img.shields.io/badge/AI-Gemini_2.5_Flash-FF1493?style=flat-square&logo=google)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blueviolet?style=flat-square&logo=telegram)
![Security](https://img.shields.io/badge/Security-Fernet_Encrypted-red?style=flat-square)

**KORStockScan**은 키움증권 REST API와 머신러닝(Stacking Ensemble), **gpt-5.4 를 활용한** 조건검색식 과 **생성형 AI(Gemini 2.5 Flash)**를 결합하여 주식 시장을 실시간 스캐닝하고, 웹소켓을 통해 최적의 타점을 잡아내어 완전 자동매매를 수행하는 **지능형 퀀트 트레이딩 봇**입니다.

최신 업데이트를 통해 기존 코스피 우량주 스윙 매매를 넘어, 코스닥 주도주(하이브리드)와 초단타 스캘핑까지 동시에 감시하는 **'3-Way 멀티 스레드 아키텍처'**로 진화했습니다. 

특히, 시스템의 전두엽 역할을 하는 **'Gemini-Brain(`ai_engine.py`)'**이 도입되어, 단순한 조건 검색을 넘어 호가창의 뎁스(Depth)와 틱 체결 흐름을 AI가 실시간으로 판독합니다. 수급강도(VPW)라는 기계적 기준에 AI의 직관(Score)을 더한 **동적 타점 제어(Dynamic Pullback Matrix)** 시스템을 통해, 시장 상황에 맞춰 매수 그물의 깊이를 스스로 조절하는 진정한 의미의 무호흡 무인 매매를 집행합니다.

---

## 📂 프로젝트 구조 (Project Structure)

```text
/KORStockScan
├── src/
│   ├── core/
│   │   └── event_bus.py              # 🔄 이벤트 드리븐 아키텍처의 핵심 척추 (비동기 메시지 라우터)
│   │  
│   ├── data/  
│   │   ├── db_manager.py             # 🗄️ PostgreSQL 통합 ORM 매니저 (안전한 세션 및 커넥션 풀링 관리)
│   │   └── models.py                 # 📊 SQLAlchemy 기반 데이터베이스 스키마 및 객체(Entity) 정의
│   │  
│   ├── engine/  
│   │   ├── ai_engine.py              # 🧠 Gemini API 기반 수석 트레이더 엔진 (호가창 분석 및 다중 모델 스위칭)
│   │   ├── kiwoom_sniper_v2.py       # 🔫 메인 트레이딩 엔진 (하이브리드 아키텍처, 타임 라우팅, 상태 머신)
│   │   ├── kiwoom_websocket.py       # 🌐 실시간 웹소켓 매니저 (다중 조건검색 PUSH 및 호가/체결 데이터 스트리밍)
│   │   ├── kiwoom_orders.py          # 🛒 스마트 주문 및 SOR(대체거래소) 통합 잔고/체결 관리 모듈
│   │   ├── signal_radar.py           # 📡 실시간 수급/지표 분석 및 정밀 타점 계산 (스마트 라운드피겨 회피 탑재)
│   │   └── ml_predictor.py           # 🔮 순수 머신러닝 추론기 (단일 책임 원칙 적용 및 Stacking 앙상블 모델)
│   │  
│   ├── model/  
│   │   ├── feature_engineer.py       # 🧬 단일 진실 공급원(SSOT) 피처 가공 모듈 (학습-추론 불일치 원천 차단)
│   │   ├── train_bull_models.py      # 🐂 상승장(Bull) 특화 XGBoost/LightGBM 하위 전문가 모델 학습기
│   │   ├── train_lightgbm.py         # ⚡ 변동성 패턴 포착에 특화된 LightGBM 하위 전문가 모델 학습기
│   │   ├── train_stacking.py         # 🧠 4개 베이스 모델 예측을 융합하는 최종 결정권자(Meta-Model) 스태킹 학습기
│   │   ├── train_xgboost.py          # 🌲 추세 돌파 포착에 특화된 XGBoost 하위 전문가 모델 학습기
│   │   ├── backtest_stacking.py      # 📊 AI 예측값 기반 3일 스윙 정밀 백테스터 (트레일링/갭하락/복리 반영)
│   │   └── tune_backtest_params.py   # 🛠️ 그리드 탐색(Grid Search) 기반 최적 매매 파라미터 자동 튜닝기
│   │  
│   ├── notify/  
│   │   └── telegram_manager.py       # 📱 EventBus 기반 텔레그램 UI 및 알림 브로드캐스터 (권한 라우팅 및 원격 제어)
│   │
│   ├── scanners/
│   │   ├── final_ensemble_scanner.py # 🔍 KOSPI 우량주 스윙 타점 필터링 및 장전 AI 앙상블 브리핑 (Batch)
│   │   ├── kosdaq_scanner.py         # 🔍 장중 코스닥 수급 폭발 종목 포착 및 AI 추론 연동 스캐너
│   │   ├── scalping_scanner.py       # 🔍 1분 주기 초단타(Scalping) 타겟 발굴 및 실시간 웹소켓 감시 지시
│   │   ├── crisis_monitor.py         # 🚨 글로벌 매크로/지정학적 리스크 RSS 실시간 감시 및 헷지(Hedge) 알림
│   │   └── eod_analyzer.py           # 🌙 장 마감 후 쌍끌이 매집 기반 내일의 주도주 TOP 5 분석기 (Gemini Pro)
│   │
│   ├── utils/
│   │   ├── constants.py              # ⚙️ 시스템 전역 상수 및 매매 룰(Trading Rules) 중앙 관리 (Dataclass)
│   │   ├── kiwoom_utils.py           # 🛠️ 키움증권 REST API 래퍼 및 잡주 필터링, 호가/틱 변환 유틸리티
│   │   ├── logger.py                 # 📝 시스템 전역 독립 로깅 유틸리티 (파일/콘솔 에러 추적)
│   │   └── update_kospi.py           # 💾 전 종목 일봉/보조지표 수집 및 PostgreSQL 고속 벌크 인서트 (배치)
│   │   
│   └── bot_main.py                   # 🤖 메인 컨트롤러 (시스템 가동 및 텔레그램 인터페이스)
│
├── data/
│   └── config_prod.json              # ⚙️ 설정 파일 (API 키, ADMIN_ID, 모델 설정)
│
├── README.md                   # 📝 프로젝트 문서 (AI 모델 사양 및 매매 로직 가이드)
└── .gitignore                  # 🙈 보안 파일 및 DB 캐시 제외 설정
```
---

## ✨ 핵심 기능 (Key Features)  

### 🗄️ Data Module: Database & ORM System
기존 SQLite 환경의 병목을 해소하기 위해, 다중 스레드 실시간 트레이딩 환경에 최적화된 PostgreSQL과 SQLAlchemy ORM 기반으로 데이터베이스 시스템을 전면 개편했습니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **안전한 트랜잭션 관리 (Context Manager)**
  `@contextmanager`를 활용해 DB 세션을 열고 닫는 과정을 완벽하게 캡슐화했습니다. 쿼리 실행 중 에러가 발생하면 자동으로 롤백(`session.rollback()`)을 수행하여, 매매 루프 도중 에러가 발생하더라도 장부(DB)가 꼬이는 데이터 무결성 훼손을 원천 차단합니다.
* **고성능 커넥션 풀링 (Connection Pooling)**
  웹소켓, 메인 스나이퍼 루프, 계좌 동기화 쓰레드 등 여러 프로세스가 동시에 DB에 접근하더라도 병목이 생기지 않도록 `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True` 등의 커넥션 풀링을 세팅하여 24시간 무중단 환경을 구축했습니다.
* **정밀한 상태 머신(State Machine) 추적 로직**
  단순한 매수/매도 기록을 넘어서, 종목의 생애 주기를 `WATCHING` ➡️ `BUY_ORDERED` ➡️ `HOLDING` ➡️ `SELL_ORDERED` ➡️ `COMPLETED` 상태로 쪼개어 관리하는 `RecommendationHistory` 테이블을 설계했습니다. 고유 `id` 기반의 Primary Key를 도입하여 동일 종목 다중 스캘핑 시 덮어쓰기 오류를 방지합니다.
* **보안 및 텔레그램 유저 권한 관리**
  `User` 테이블을 통해 텔레그램 봇 사용자의 권한(`auth_group` - Admin/VIP/User)과 차단 여부(`is_active`)를 관리하여, 허가된 사용자만 봇의 제어 및 VIP 타점 정보를 받을 수 있도록 보안 계층을 분리했습니다.
* **Pandas 네이티브 연동**
  AI 엔진이나 퀀트 스캐너가 데이터를 분석할 때, SQLAlchemy 엔진과 `pandas.read_sql`을 직접 연결하여 대규모 주가 데이터(`DailyStockQuote`)의 로드 및 데이터프레임 변환 속도를 극대화했습니다.


### 🧠 AI Engine: Gemini-Powered Chief Trader
단순한 기계적 지표(RSI, 이동평균선)에 의존하는 기존 봇과 달리, 구글의 최신 Gemini API를 탑재하여 호가창의 미세한 흐름과 수급의 '의도'를 파악하는 AI 트레이딩 엔진을 구축했습니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **다중 API 키 로테이션 (Multi-Key Rotation & Failover)**
  실시간 초단타 매매 중 AI 호출 한도 초과(`429 Quota`)나 서버 과부하(`503 Unavailable`)가 발생하더라도, 봇이 뻗지 않도록 여러 개의 API 키를 순환(Cycle)하며 즉시 대체 키로 재시도하는 무중단 로테이션 아키텍처를 구현했습니다.
* **동적 모델 라우팅 (Dynamic Model Routing)**
  상황의 긴급성에 따라 AI 모델을 동적으로 스위칭합니다. 0.1초가 중요한 장중 스캘핑 타점 판별에는 속도가 가장 빠른 `gemini-2.5-flash-lite`를 사용하고, 장 마감 후 깊은 사고가 필요한 내일의 주도주 분석(EOD)이나 아침 시장 브리핑에는 추론 능력이 뛰어난 `gemini-pro-latest`를 덮어씌워(`model_override`) 호출합니다.
* **호가창 불균형 및 틱 가속도 분석 (Micro-structure Analysis)**
  AI에게 단순한 주가만 던져주는 것이 아닙니다. 매도/매수 호가잔량의 불균형 비율, 최근 10틱이 체결되는 데 걸린 시간(가속도), 매수 압도율(Buy Pressure), 당일 최고가 대비 이격도(Drawdown) 등 프랍 트레이더들이 보는 HTS 상의 모든 핵심 가공 데이터를 포맷팅하여 AI의 컨텍스트(Context)로 주입합니다.
* **전략별 맞춤형 프롬프트 파이프라인**
  목적에 따라 AI의 페르소나와 출력 형식을 완벽하게 통제합니다.
  * `SCALPING_SYSTEM_PROMPT`: 시스템 매매 루프가 직접 읽을 수 있도록 잡담 없이 철저히 JSON(`action`, `score`, `reason`) 형식으로만 응답하도록 강제.
  * `REALTIME/EOD_PROMPT`: 텔레그램 알림용으로, 사람이 읽기 좋게 이모지와 마크다운을 활용한 전문 애널리스트의 브리핑 리포트를 생성.
* **Thread-Safe AI 호출 (Locking)**
  다수의 종목이 동시에 조건검색에 포착되어 AI 엔진을 동시다발적으로 호출할 때 병목이나 충돌이 발생하지 않도록, `threading.Lock()`을 통해 안전하게 순차 처리 및 쿨타임(최소 호출 간격)을 제어합니다.


### 🔫 Core Engine: Sniper V2 & Real-time WebSocket
초당 수백 건씩 쏟아지는 증권사 호가 데이터를 파이썬 환경에서 지연(Latency) 없이 처리하기 위해, 제어 흐름과 데이터 흐름을 분리한 **하이브리드(Hybrid) 아키텍처**를 독자적으로 구축했습니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **제어(Event-Driven)와 데이터(Polling)의 분리**
  주문 체결, 조건검색 포착 등의 '상태 변화'는 `EventBus`를 통해 즉각적인 PUSH 방식으로 처리하여 0.1초 만에 엔진을 깨웁니다. 반면, 방대한 틱/호가 데이터는 웹소켓 매니저가 메모리에 최신 스냅샷만 덮어쓰고(Update), 스나이퍼 엔진이 필요할 때만 당겨오는(Pull) 방식을 채택하여 파이썬 GIL 한계와 이벤트 큐 병목 현상을 완벽하게 극복했습니다.
* **조건검색 타임 라우팅 (Time-based Routing)**
  HTS에서 설정한 다수의 조건검색식을 웹소켓으로 동시 구독합니다. 아침 9시의 공격형 검색식부터 13시 오후장 전용 검색식까지, 포착된 종목의 이름표(seq)를 확인하고 지정된 시간표에 맞지 않으면 0.001초 만에 폐기(Drop)하는 정밀 타임 라우팅을 수행합니다.
* **안전한 5단계 상태 머신 (State Machine) & 자가 복구 (Self-Healing)**
  종목의 생애 주기를 `WATCHING` ➡️ `BUY_ORDERED` ➡️ `HOLDING` ➡️ `SELL_ORDERED` ➡️ `COMPLETED` 5단계로 통제합니다.
  * **타임아웃 방어:** 매수(20초), 매도(40초) 주문 전송 후 영수증이 오지 않으면 호가 꼬임/VI 발동으로 간주하고 즉각 주문 취소 후 이전 상태로 롤백합니다.
  * **90초 정기 계좌 동기화:** 증권사 통신 오류로 체결 영수증이 누락되더라도, 90초 주기로 백그라운드에서 증권사 실제 잔고를 훔쳐보고 DB 상태를 강제로 맞춰버리는 불사조 로직이 탑재되어 있습니다.
* **AI 점수 스무딩(EMA Smoothing) & 동적 트레일링 익절**
  보유 종목(HOLDING)이 위험/수익 구간(Critical Zone)에 진입하면 AI 호출 쿨타임을 3초로 대폭 줄입니다. 이때 AI의 순간적인 호가창 발작을 막기 위해 과거 점수 관성(60%)과 새로운 판단(40%)을 혼합하는 스무딩 필터를 거치며, 점수에 따라 손절폭과 트레일링 익절폭을 동적으로 고무줄처럼 조절합니다.
* **가비지 컬렉터 (Memory TTL & FIFO Queue)**
  장시간 횡보하는 스캘핑 타겟으로 인해 봇이 무거워지는 것을 막기 위해, 포착 후 120분이 지나거나 감시 큐가 40개를 초과하면 가장 오래된 종목부터 꼬리를 잘라내는(EXPIRED) 메모리 최적화 기능이 포함되어 있습니다.


### 🛒 Trading Module: Smart Order & Execution Management
단순한 매수/매도 API 호출을 넘어, 실전 트레이딩에서 발생하는 슬리피지(Slippage)를 최소화하고 다중 거래소 환경에 완벽하게 대응하는 스마트 주문 모듈입니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **스마트 매도 로직 (Smart Sell & Slippage Protection)**
  무조건 시장가로 던지는 멍청한 봇이 아닙니다. 매도 신호 발생 시 실시간 호가창(Orderbook)을 분석하여 매수 1호가의 잔량이 내 물량의 1.2배 이상 넉넉하면 **'지정가(00)'**로 던져 손실을 방어하고, 잔량이 부족하면 **'최유리지정가(6)'**로 전환하여 슬리피지를 최소화합니다. 단, AI가 위험을 감지한 긴급 손절(LOSS) 시에는 가격 불문 **'시장가(3)'**로 즉각 탈출합니다.
* **SOR (대체거래소) 완벽 대응 아키텍처**
  새롭게 도입된 복수 거래소 체제에 대응하기 위해, 계좌 잔고 조회 시 `KRX(한국거래소)`와 `NXT(넥스트트레이드)` 양쪽의 잔고를 각각 조회한 뒤 종목코드(Key)를 기준으로 수량을 완벽하게 병합(Aggregate)합니다. 이를 통해 엔진은 거래소가 나뉘어 체결되더라도 단일 잔고로 인식하여 혼선 없이 매도를 수행할 수 있습니다.
* **AI 맞춤형 예약 주문 (Price Normalization)**
  `reserve_buy_order_ai` 함수를 통해 AI가 문장으로 뱉은 목표가(예: "50,500원 부근 눌림목")에서 숫자만 정밀 추출한 뒤, 한국 증시의 가격대별 호가 단위(Tick Size) 규격에 맞게 내림 정규화 과정을 거쳐 키움증권 서버에 정확한 낚싯바늘(지정가 매수)을 투척합니다.
* **안전한 자본 관리 & 원클릭 취소**
  매수 시 시장가 갭상승으로 인한 증거금 부족 에러를 막기 위해, 배정된 예산의 95%만 사용하는 안전 계수를 적용했습니다. 또한, 주문 후 체결이 되지 않을 경우 원주문번호(odno)와 `qty=0`(전량 취소) 파라미터를 통해 즉각적인 미체결 주문 취소(`kt10003`)를 지원합니다.


### 📡 Analytics & ML Module: Signal Radar & Stacking Predictor
단순 돌파 매매의 한계를 극복하기 위해, 실시간 호가창 미시구조(Micro-structure) 분석과 자체 학습된 머신러닝 앙상블 모델을 결합하여 매매 성공률을 극대화합니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **스마트 타점 계산기 (Round Figure Avoidance)**
  `signal_radar.py`는 AI 확신도와 체결강도를 바탕으로 진입 타점을 동적으로 계산합니다. 특히 호가창에 매물이 쌓이는 심리적 저항선인 라운드 피겨(예: 10,000원, 50,000원) 바로 아래의 악성 매물대를 피하기 위해, 타점을 한 호가 더 깊게 내리는(예: 49,900원 ➡️ 48,800원) 실전 프랍 트레이딩 기법이 하드코딩되어 있습니다.
* **초단타용 Micro 지표 실시간 연산**
  HTS에서 제공하지 않는 초단타용 지표를 1분봉 차트와 틱 데이터를 통해 직접 연산합니다. `pandas_ta`를 활용하여 최근 5분 거래량 가중 평균 주가(Micro-VWAP), RSI, MACD 히스토그램 등을 실시간으로 뽑아내어 AI 엔진의 컨텍스트로 제공합니다.
* **머신러닝 추론기 단일 책임 원칙 (SRP) 분리**
  기존 스캐너에 강결합되어 있던 ML 추론 로직을 `ml_predictor.py`로 완전히 분리했습니다. 이를 통해 무거운 스캐너 루프를 돌리지 않고도, 텔레그램 봇이나 스나이퍼 엔진 등 시스템 내 어떤 모듈이든 가볍게 AI 판독 결과를 즉시 요청(On-demand)할 수 있습니다.
* **XGBoost & LightGBM 메타 스태킹 (Stacking Ensemble)**
  단일 모델의 과적합을 방지하기 위해 4개의 베이스 모델(상승장/하락장별 XGBoost, LightGBM)이 1차 확률을 예측하고, 메타 모델(Meta Model)이 이 예측값들을 다시 학습하여 최종 확신지수(Probability)를 산출하는 고급 스태킹 앙상블 아키텍처를 채택했습니다.
* **방탄 예외 처리 (Bulletproof Fallback)**
  `ml_predictor.py`의 추론 과정 중 피처 누락이나 연산 에러가 발생하더라도 시스템이 다운되지 않도록 전체 로직을 감싸고, 예외 발생 시 안전하게 0점을 반환하여 통계에서 자연스럽게 탈락(`DROP`)되도록 설계했습니다. 시장 지수 조회 시에도 FDR(FinanceDataReader) 실패 시 키움 API(`ka20006`)로 우회하는 2중 폴백을 지원합니다.


### 🤖 MLOps & Backtesting Module: Stacking Ensemble Pipeline
단순한 백테스트 스크립트 모음이 아닙니다. 데이터 전처리부터 베이스 모델 학습, 스태킹 앙상블, 그리고 실전 시뮬레이션까지 이어지는 완전한 퀀트 트레이딩 MLOps 파이프라인을 구축했습니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **학습-추론 불일치(Training-Serving Skew) 원천 차단**
  `feature_engineer.py`를 단일 진실 공급원(SSOT)으로 설계했습니다. 과거 DB 데이터를 불러와 모델을 학습시킬 때와, 장중 실시간 틱 데이터로 AI 추론(`ml_predictor.py`)을 수행할 때 100% 동일한 수학 공식(RSI, MACD, 외인/기관 수급 가속도 등)을 사용하도록 강제하여 실전에서 모델이 오작동하는 것을 방지합니다.
* **2-Stage 메타 스태킹 앙상블 (Meta-Stacking Ensemble)**
  특정 장세나 모델의 과적합(Overfitting)을 막기 위해 4개의 하위 전문가 모델(범용 XGB/LGBM, 상승장 특화 XGB/LGBM)을 병렬로 학습시킵니다. 이후 `train_stacking.py`에서 로지스틱 회귀(Logistic Regression) 메타 모델이 하위 모델들의 예측값(OOF)을 다시 학습하여, 여러 전문가의 의견을 종합한 궁극의 최종 확신지수를 도출합니다.
* **실전 지향적 정답지(Target) 레이블링**
  AI가 단순히 "내일 오를까/내릴까"를 맞추는 것이 아닙니다. 훈련 데이터의 정답지(Target)를 **"매수 후 3일 이내에 손절선(-3.0%)을 건드리지 않고, 목표 익절선(+4.5%)에 도달했는가?"**로 엄격하게 정의(`Target = 1 or 0`)하여, 모델의 목적 함수와 실제 트레이딩 수익 로직을 완벽하게 일치시켰습니다.
* **고해상도 백테스팅 엔진 (High-Fidelity Backtester)**
  단순 수익률 합산이 아닌, 실제 자금 흐름과 시간의 흐름을 흉내 내는 정밀 백테스터를 자체 구현했습니다. 
  * 최대 5종목 제한 및 20% 분산 복리 투자
  * 장세(Bull/Bear)에 따른 동적 손절선 조절 (-3.0% / -3.5%)
  * 수익 보존을 위한 트레일링 스탑(Trailing Stop) 가동 및 오버나잇 갭하락 페널티 현실 반영
* **그리드 탐색 기반 하이퍼파라미터 튜닝**
  `tune_backtest_params.py`를 통해 진입 확률, 익절 폭, 손절 폭 등 수십 가지의 파라미터 조합을 시뮬레이션하고, 가장 승률과 누적 수익률이 높은 TOP 5 매매 전략을 자동으로 뽑아내어 실전 엔진의 룰(Rule)을 지속적으로 업데이트할 수 있습니다.


### 📱 Notification Module: Telegram UI & Broadcaster
매매 엔진과 알림 시스템의 강결합을 끊어내고, 메신저를 하나의 완벽한 '원격 관제탑(Remote Control Tower)'으로 진화시킨 스마트 알림 모듈입니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **EventBus 기반 비동기 알림 (Decoupled Broadcasting)**
  스나이퍼 매매 엔진이나 웹소켓 모듈 안에는 텔레그램 발송 코드가 단 한 줄도 없습니다. 엔진이 허공(`EventBus`)에 `TELEGRAM_BROADCAST` 이벤트를 쏘면, `telegram_manager.py`가 이를 구독(Subscribe)하여 비동기적으로 메시지를 전파합니다. 이를 통해 알림 전송 지연이 매매 타점에 영향을 주는 것을 완벽하게 차단했습니다.
* **정밀한 타겟 라우팅 (Audience Routing & Auth)**
  모든 메시지를 일괄 발송하지 않습니다. `ADMIN_ONLY` (관리자 전용 시스템 에러 및 체결 로그)와 `VIP_ALL` (구독자를 위한 타점 및 AI 브리핑) 권한을 구분하여 메시지를 스마트하게 라우팅합니다.
* **On-Demand 실시간 AI 분석 (Interactive UI)**
  단방향 알림을 넘어, 사용자가 챗봇에 6자리 종목코드를 입력하거나 `/why 005930` 명령어를 치면 즉시 봇이 해당 종목의 실시간 호가창과 차트를 분석하여 Gemini AI의 타점 리포트를 회신하는 양방향 인터랙티브 기능을 제공합니다.
* **스마트 상태 감지 및 메모리 최적화 (State Tracking)**
  사용자가 봇을 차단(`403 Forbidden` 에러)하거나 대화방을 나가면(`kicked`/`left` 이벤트) 봇이 이를 즉각 감지하여 DB의 `is_active` 상태를 `False`로 변경합니다. 불필요한 API 호출 낭비를 막고 텔레그램 서버 리밋에 걸리지 않도록 방어합니다.
* **원격 관제 및 자동화 결제 (Remote Control & Payment)**
  관리자는 텔레그램 내부에서 `/restart` 명령어로 엔진의 우아한 종료(Graceful Shutdown)와 재시작을 지시할 수 있으며, 텔레그램 자체 결제 연동(`successful_payment`)을 통해 후원자의 등급을 자동으로 VIP로 승격시키는 수익화 파이프라인이 내장되어 있습니다.


### 🛠️ Infrastructure Module: Common Utilities & Data Pipeline
매매 엔진의 비즈니스 로직에 하드코딩이 섞이는 것을 방지하고, 대규모 데이터 수집과 API 통신을 안정적으로 지원하는 시스템 인프라 계층입니다.

**[✨ 핵심 피처 및 아키텍처 포인트]**

* **불변성(Immutability) 기반 매매 룰 중앙 관리 (`constants.py`)**
  시스템 곳곳에 흩어져 있던 익절/손절 퍼센트, 진입 비중, 타임아웃 시간 등의 매직 넘버(Magic Number)를 `@dataclass(frozen=True)` 형태의 `TradingConfig` 객체 하나로 완벽하게 통제합니다. 이를 통해 의도치 않은 변수 변경을 원천 차단하고, 매매 룰 수정 시 이 파일 하나만 수정하면 전체 시스템에 즉각 반영됩니다.
* **스마트 환경 감지 및 안전망 (`kiwoom_utils.py`)**
  * **Auto URL Switching:** 서버에 `config_dev.json` 파일이 있는지 스스로 탐지하여, 개발 환경(Mock API)과 운영 환경(실거래 API)의 통신 URL을 자동으로 스위칭합니다.
  * **Garbage Stock Filter:** ETF, ETN, 스팩, 우선주, 관리종목 등 트레이딩에 부적합한 특수 종목들을 API 응답 즉시 필터링하여 스캐너의 낭비를 막습니다.
  * **Tick Size Normalizer:** 2023년 개정된 한국거래소(KRX)의 통합 호가 단위 규격을 완벽하게 반영하여, AI가 제시한 목표가를 실제 주문 가능한 가격으로 안전하게 정규화합니다.
* **초고속 벌크 적재 파이프라인 (`update_kospi.py`)**
  매일 장 마감 후 전 종목의 일봉 데이터를 DB에 업데이트하는 무거운 배치 작업을 최적화했습니다. 한 줄씩 `INSERT`하는 느린 방식을 버리고, Pandas DataFrame에 `feature_engineer.py`의 보조지표 연산을 한 번에 입힌 뒤, SQLAlchemy의 `to_sql(method='multi')`와 묶음 트랜잭션(`engine.begin()`)을 사용하여 수십만 건의 데이터를 수 초 내에 PostgreSQL에 고속 밀어넣기(Bulk-Insert) 합니다.

---
## 🛰️ 스캐너 엔진 비교 (Scanner Comparison)

KORStockScan 시스템은 시장의 특성과 매매 호흡에 따라 **3가지의 독립적인 탐색 및 매매 엔진**을 가동합니다. 특히 초단타(Scalping) 엔진은 기존의 폴링(Polling) 방식을 벗어나 **웹소켓 기반의 100% 이벤트 드리븐(Event-Driven)**으로 동작하며, 0.1초의 지연도 허용하지 않습니다.

모든 엔진의 최종 의사결정은 **Gemini API (Flash-Lite / Pro)**와 자체 학습된 **머신러닝 앙상블(XGBoost+LightGBM)** 모델에 의해 통제됩니다.

| 구분 | ⚡ V3 웹소켓 스캘핑 (Scalping) | 🏢 코스피 스태킹 앙상블 (KOSPI) | 🚀 코스닥 스태킹 앙상블 (KOSDAQ) |
| :--- | :--- | :--- | :--- |
| **작동 방식** | **실시간 PUSH (Event-Driven)** | **15분/EOD 주기 배치 (Polling)** | **15분 주기 배치 (Polling)** |
| **감시 대상** | HTS 다중 조건검색식 포착 종목 | 코스피 대형/우량주 중심 (`001`) | 코스닥 중소형/테마주 중심 (`101`) |
| **핵심 뇌(Brain)** | **Gemini 2.5 Flash-Lite** (실시간) | **Meta-Stacking ML** + Gemini Pro | **Meta-Stacking ML** + Gemini Pro |
| **분석 깊이** | 호가 불균형 + 틱 가속도 + 체결강도 | 15종 기술/수급 지표 + 외인/기관 롤링 | 12종 변동성 지표 + 스마트머니 가속도 |
| **매수 타점** | **[스마트 눌림목]** AI 확신도(75점↑) + 라운드 피겨 회피 동적 타점 계산 | **[스윙 타점]** 메타 모델 확률(70%↑) 돌파 및 차트 정배열 확인 | **[스윙 타점]** 메타 모델 확률(70%↑) 돌파 및 체결강도/수급 폭발 |
| **매도 전략** | **AI 개입 조기 손절** 및 수익 구간 진입 시 **EMA 스무딩 동적 트레일링 익절** | 장세(Bull/Bear) 연동 가변 손절선 및 **최대 3일 보유 시간 청산** | 코스닥 전용 가변 익절선 및 **최대 2일 보유 시간 청산** |
| **전략 태그** | `SCALPING` / `SCALP` | `KOSPI_ML` | `KOSDAQ_ML` |
| **핵심 모듈** | `kiwoom_websocket.py` <br> `kiwoom_sniper_v2.py` | `final_ensemble_scanner.py` <br> `train_stacking.py` | `kosdaq_scanner.py` <br> `ml_predictor.py` |

---
## ⚙️ 설치 및 설정 (Installation & Setup)

### 1. 환경 준비 (Prerequisites)
* **OS**: Windows, Linux, Mac 모두 지원 (키움증권 신형 REST API 및 웹소켓 기반으로 OS 제약이 없습니다.)
* **Python**: 3.13 버전 이상 권장
* **데이터베이스**: **PostgreSQL** (다중 스레드 기반의 고성능 실시간 트레이딩을 위해 기존 SQLite에서 마이그레이션 되었습니다.)

### 2. 패키지 설치
저장소를 복제하고 필요한 라이브러리를 설치합니다.
```bash
git clone [https://github.com/JaehwanPark/KORStockScan.git](https://github.com/JaehwanPark/KORStockScan.git)
cd KORStockScan
pip install -r requirements.txt
```
---

## ⚠️ 면책 조항 (Disclaimer)
본 소프트웨어는 개인적인 투자 참고 및 알고리즘 트레이딩 학습 목적으로 제작되었습니다. 

1. **투자 책임**: 모든 투자 결정에 대한 최종 책임은 사용자 본인에게 있습니다. 제작자는 이 프로그램을 사용하여 발생한 어떠한 경제적 손실에 대해서도 법적 책임을 지지 않습니다.
2. **시스템 리스크**: 주식 거래는 원금 손실의 위험이 매우 크며, 자동 매매 시스템의 예기치 못한 오류, 네트워크 장애, 또는 API 통신 지연으로 인해 손실이 발생할 수 있습니다.
3. **사전 테스트**: 실투자 전에는 반드시 모의투자 환경에서 충분한 테스트를 거친 후 운용하시기 바랍니다.

