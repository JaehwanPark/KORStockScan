# 🚀 KORStockScan v12.1

> **AI Stacking Ensemble 기반 KOSPI 데이트레이딩 자동매매 시스템**

KORStockScan v12.1은 4개의 베이스 모델(XGBoost, LightGBM, Bull Specialists)과 최종 결재권자인 Meta-Model을 결합한 **스태킹 앙상블(Stacking Ensemble)** 기술을 통해 시장의 노이즈를 극복하고 압도적인 정밀도를 실현한 차세대 트레이딩 봇입니다.

텔레그램 봇 @KORStockScan

---

## 📊 핵심 성과 (v12.1 Backtest Result)

단순한 우상향을 넘어, 통계적으로 승리할 수밖에 없는 구간을 공략합니다.

* **승률 (Win Rate):** **63.33%**
* **누적 수익률:** **+719.43%** (최근 6개월 시뮬레이션)
* **회당 평균 수익:** **+0.28%** (수수료 및 슬리피지 0.25% 차감 후)
* **매매 로직:** 장중 **+2.0% 익절** / **-2.5% 손절** / **15:15 일괄 타임컷**

---

## 🏗 시스템 아키텍처 (Architecture)

본 시스템은 **데이터 수집 ➡️ 학습 ➡️ 검증 ➡️ 선별 ➡️ 집행**으로 이어지는 유기적인 파이프라인으로 구성되어 있습니다.

### 1. 기반 및 데이터 관리 (The Foundation)

* `setup_init_db.py`: 시스템 운영을 위한 SQLite DB 및 테이블 스키마 초기화.
* `update_kospi.py`: 매일 아침 신선한 주가 데이터와 기술적 지표를 공급하는 보급관.
* `kiwoom_utils.py`: 전 시스템이 공유하는 핵심 계산 로직 및 API 통신 유틸리티.

### 2. AI 모델링 및 검증 (The Intelligence)

* `train_xgboost.py` / `train_lightgbm.py`: 추세와 변동성을 각각 전공하는 베이스 모델 양성.
* `train_bull_models.py`: 상승장 특화 패턴만을 학습한 엘리트 모델 2종 생성.
* `train_stacking.py`: 4인의 전문가 의견을 통합하여 최종 판단을 내리는 '메타 모델' 훈련.
* `backtest_stacking.py`: 과거 데이터를 통해 v12.1 전략의 수익성과 MDD를 냉정하게 검증.

### 3. 실전 매매 및 인터페이스 (The Execution)

* `final_ensemble_scanner.py`: 전 종목을 전수 조사하여 최종 확신도 0.75 이상의 종목을 전투 부대에 하달.
* `kiwoom_websocket.py`: 0.1초 단위의 실시간 체결 데이터를 수신하는 고속 정보 통신망.
* `kiwoom_sniper_v2.py`: 실시간 수급을 체크하여 방아쇠를 당기고 리스크를 관리하는 실행 엔진.
* `kiwoom_orders.py`: 키움증권 서버에 실제 매수/매도 주문을 집행하는 최종 집행관.
* `bot_main.py`: 텔레그램을 통해 전 과정을 보고하고 제어하는 지휘소(UI).

---

## 🛠 실행 가이드 (Quick Start)

### 1. 환경 설정

`config_prod.json` 파일에 필요한 API 정보를 설정합니다.

```json
{
  "TELEGRAM_TOKEN": "YOUR_TOKEN",
  "ADMIN_ID": "YOUR_ID",
  "DB_PATH": "trading_history.db"
}

```

### 2. 데이터 업데이트 및 종목 선별

매일 장 시작 전 데이터를 최신화하고 오늘의 공략주를 선정합니다.

```bash
python update_kospi.py
python final_ensemble_scanner.py

```

### 3. 시스템 가동

텔레그램 봇과 트레이딩 엔진을 동시에 시작합니다.

```bash
python bot_main.py

```

---

## 💡 v12.1 핵심 전략 (Sniper Logic)

* **스태킹 앙상블:** 개별 모델의 편향을 제거하기 위해 5개의 모델이 협동 판독.
* **포지션 사이징:** 계좌 자산의 **10% 비중** 분산 투자를 통해 MDD(최대 낙폭)를 철저히 관리.
* **장중 대응:** 웹소켓 기반의 초저지연 데이터 분석으로 +2.0% 목표가 도달 시 즉시 익절.
* **오버나잇 금지:** 15:15 타임컷 로직을 통해 당일 매수 종목은 당일 모두 청산하여 내일의 변동성 차단.

---

## ⚠️ 면책 조항 (Disclaimer)

본 프로젝트는 개인 연구 목적으로 제작되었으며, AI의 판단은 통계적 확률일 뿐 투자 수익을 보장하지 않습니다. 모든 투자 결정의 책임은 본인에게 있으며, 실제 자금 운용 전 반드시 소액 테스트 기간을 거칠 것을 권장합니다.

---

**Developed by 코이컴퍼니**
*Copyright 2026. All rights reserved.*
