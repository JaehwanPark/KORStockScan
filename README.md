# 🚀 KORStockScan V3.1 - AI 기반 코스피 퀀트 스나이퍼

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![Kiwoom API](https://img.shields.io/badge/API-Kiwoom_Open%2B-green?style=flat-square)
![Machine Learning](https://img.shields.io/badge/ML-XGBoost_%7C_LightGBM-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blueviolet?style=flat-square&logo=telegram)

**KORStockScan**은 키움증권 REST API와 머신러닝(Stacking Ensemble)을 활용하여 코스피(KOSPI) 우량주를 스캐닝하고, 실시간 웹소켓을 통해 최적의 타점을 잡아내어 완전 자동매매를 수행하는 퀀트 트레이딩 봇입니다. 

단순한 기술적 지표를 넘어 **'스마트 머니 가속도(외인/기관 매집 속도)'**와 **'시장 상태(Regime) 판독'**을 통해 블랙스완(폭락장)에서도 살아남는 강력한 생존력을 목표로 설계되었습니다.

---

## ✨ 핵심 기능 (Key Features)

* 🧠 **콰트로 앙상블 AI (Stacking Meta Model)**
  * XGBoost와 LightGBM을 기반으로 상승장(Bull) 전용 모델과 범용 하이브리드 모델을 혼합하여 단기 상승 확률(Prob)을 0~100%로 수치화합니다.
* 📊 **스마트 머니 가속도 필터 (Smart Money Accel)**
  * 외국인과 기관의 단순 순매수를 넘어, MACD 원리를 응용한 '단기/장기 매집 가속도'를 계산하여 폭락장 속 세력의 은밀한 매집을 포착합니다.
* 🔫 **0.1초 반응 실시간 스나이퍼 (WebSocket)**
  * `WATCHING` -> `PENDING` -> `HOLDING` -> `COMPLETED` 4단계 상태 머신을 통해 미체결 주문 취소, 최유리지정가 매수 등을 안정적으로 처리합니다.
  * 단순히 AI 점수만 높다고 매수하지 않으며, **실시간 체결강도 100(매수 우위) 이상**일 때만 방아쇠를 당기는 2중 안전장치가 탑재되어 있습니다.
* 🛡️ **동적 트레일링 스탑 & 가변 손절선 (Drawdown Defense)**
  * 시장이 '상승장(BULL)'인지 '조정장(BEAR)'인지 봇이 스스로 판독하여 손절선을 타이트하게 조절합니다.
  * 고점 도달 후 꺾일 때 슬리피지(Slippage)를 최소화하여 이익을 보존하는 강력한 가변 익절(Trailing Stop) 로직이 실전 검증되었습니다.
* 📱 **텔레그램 관제 센터 (Admin & VIP Auth)**
  * 장중 스캐너 결과 및 실시간 매수/매도 체결 알림을 마크다운 리포트로 전송합니다.
  * SQLite(`users.db`)를 통한 권한 제어(A: 어드민, V: VIP)를 지원하며, 수동 종목 추가 시 즉각적으로 **차트 기반 저항대(20일 전고점 & 볼린저밴드 상단) 목표가**를 브리핑합니다.

---

## 🏗️ 시스템 아키텍처 (Architecture)

시스템은 철저하게 단일 진실 공급원(`constants.py`)의 룰을 따르며, 3개의 핵심 스크립트가 스케줄에 맞춰 유기적으로 동작합니다.

1. **`update_kospi.py` (데이터 파이프라인)**
   * 매일 정규장 마감 후, 네이버 모바일 API와 키움 API를 혼합하여 KOSPI 전 종목의 일봉, 거래량, 수급 데이터를 수집 및 정제하여 SQLite에 적재합니다.
2. **`final_ensemble_scanner.py` (전략 스캐너)**
   * 적재된 DB를 바탕으로 AI 모델이 분석을 수행합니다. 장전(정규) 스캔과 장중(Intraday) 실시간 급등주 스캔을 병행하며, 생존 종목의 정확한 'AI 확신지수'를 DB에 장전합니다.
3. **`kiwoom_sniper_v2.py` (실시간 트레이딩 봇)**
   * 스캐너가 장전해 둔 타겟을 웹소켓에 등록하여 실시간 호가창을 감시하며, 조건 도달 시 즉시 무인 매매를 집행합니다.

---

## ⚙️ 설치 및 설정 (Installation & Setup)

### 1. 환경 준비
* **Windows/LINUX OS** (키움증권 REST API 구동 필수 환경)
* **Python 3.13+**

### 2. 패키지 설치
```bash
git clone [https://github.com/your-username/KORStockScan.git](https://github.com/your-username/KORStockScan.git)
cd KORStockScan
pip install -r requirements.txt
```

### 3. 설정파일 셋업
```json
{
  "TELEGRAM_TOKEN": "your_bot_token_here",
  "ADMIN_ID": "your_telegram_chat_id",
  "KIWOOM_ACCOUNT": "your_8_digit_account_number"
}
```

### 4. 전략 튜닝 (constants.py)

모든 매매 기준은 단일 진실 공급원(`constants.py`)에서 중앙 통제됩니다. 시장 상황에 맞게 수치를 조절하세요.

1. **`TRAILING_START_PCT` (가변 익절 방어선 가동 시작점 (예: 3.5%))**  
2. **`TRAILING_DRAWDOWN_PCT` (고점 대비 하락 허용폭 (예: 1.5%))**
3. **`STOP_LOSS_BULL / STOP_LOSS_BEAR` (시장 상태에 따른 탄력적 손절선)**
4. **`PROB_RUNNER_PICK` (AI 최소 매수 확신도 임계값)**


## ⚠️ 면책 조항 (Disclaimer)

본 레포지토리의 코드는 알고리즘 트레이딩 연구 및 학습 목적으로 작성되었습니다.
제공되는 AI 모델과 매매 로직은 수익을 보장하지 않으며, 실제 투자에 적용하여 발생하는 모든 금전적 손실에 대한 책임은 전적으로 사용자(투자자) 본인에게 있습니다.
반드시 모의투자를 통해 충분한 검증을 거친 후 소액으로 실전에 적용하시기 바랍니다.
