# KORStockScan

KORStockScan은 키움 REST/WebSocket + AI 판정을 결합한 한국 주식 자동매매/복기 플랫폼입니다.

업데이트 기준: 2026-04-08

## 개요

시스템은 `감시 -> 진입 -> 보유 -> 청산 -> 복기` 흐름으로 구성됩니다.

- 감시: 스캐너 + 조건검색식으로 후보 생성
- 진입: 실시간 데이터/AI/게이트 조건 통과 종목만 주문
- 보유: 손익/시간/AI 신호 기반 상태 관리
- 청산: 익절/손절/트레일링/리스크 룰 적용
- 복기: 웹/API/JSON 스냅샷으로 운영 성과 재검증

## 현재 운영 아키텍처

- 메인 오케스트레이션: `src/bot_main.py`
- 실시간 엔진: `src/engine/kiwoom_sniper_v2.py`
- 상태머신/체결반영: `src/engine/sniper_state_handlers.py`, `src/engine/sniper_execution_receipts.py`
- 웹/API: `src/web/app.py`
- 일일 리포트: `src/engine/daily_report_service.py`
- 성능/복기 리포트:
  - `src/engine/sniper_entry_pipeline_report.py`
  - `src/engine/sniper_trade_review_report.py`
  - `src/engine/sniper_performance_tuning_report.py`
  - `src/engine/strategy_position_performance_report.py`

## 최근 반영 기능

### 1) Post-sell 피드백 파이프라인

- 매도 체결 시 후보 기록: `src/engine/sniper_post_sell_feedback.py`
- 장후 분봉 기준 자동평가(1m/3m/5m/10m/20m)
- 분류: `MISSED_UPSIDE`, `GOOD_EXIT`, `NEUTRAL`
- 장마감 관리자 브로드캐스트에 post-sell 요약 포함
- 모니터 스냅샷에 `post_sell_feedback` 저장

MVP 기본 동작:

- 매도 후 WebSocket 유지는 기본 OFF (`POST_SELL_WS_RETAIN_MINUTES=0`)
- 장후 평가는 API 분봉 조회 기반으로 수행

### 2) 공통 Pipeline 이벤트 로거

- 공통 로거: `src/utils/pipeline_event_logger.py`
- 텍스트 로그 + JSONL 이벤트 동시 기록
- 기본 스키마 버전: `PIPELINE_EVENT_SCHEMA_VERSION=1`
- 적용 구간: 진입 상태/체결 반영/오버나이트 게이트키퍼

## 자동 스케줄 (KST)

`src/bot_main.py` 기준:

- 08:45 일일 리포트 JSON 생성
- 08:50 추천 종목 브로드캐스트
- 15:40 진입 지표 + shadow + post-sell 요약 브로드캐스트
- 15:45 모니터 스냅샷 저장 + 날짜별 로그 gzip 아카이브
- 23:50 일일 재시작

## 빠른 시작

### 1) 환경 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

필수 설정 파일:

- `data/config_prod.json` (또는 `data/config_dev.json`)
- `data/credentials.json` (Google Sheets 등 연동 시)

참고:

- 설정 로더: `src/engine/sniper_config.py`
- 주요 상수: `src/utils/constants.py`

### 2) 봇 실행

```bash
python3 src/bot_main.py
```

재시작 루프가 필요하면:

```bash
cd src
bash run_bot.sh
```

### 3) 웹/API 실행

```bash
python3 src/web/app.py
```

기본 바인딩: `0.0.0.0:5000`

## 주요 API

- `GET /api/daily-report?date=YYYY-MM-DD`
- `GET /api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- `GET /api/trade-review?date=YYYY-MM-DD&code=000000`
- `GET /api/strategy-performance?date=YYYY-MM-DD`
- `GET /api/gatekeeper-replay?date=YYYY-MM-DD&code=000000&time=HH:MM:SS`
- `GET /api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS`
- `GET /api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10`

상세 스펙: `docs/web_api_spec_guide.md`

## 주요 산출물/로그 경로

- 일일 리포트: `data/report/report_YYYY-MM-DD.json`
- 모니터 스냅샷:
  - `data/report/monitor_snapshots/trade_review_YYYY-MM-DD.json`
  - `data/report/monitor_snapshots/performance_tuning_YYYY-MM-DD.json`
  - `data/report/monitor_snapshots/post_sell_feedback_YYYY-MM-DD.json`
- Post-sell 원본/평가:
  - `data/post_sell/post_sell_candidates_YYYY-MM-DD.jsonl`
  - `data/post_sell/post_sell_evaluations_YYYY-MM-DD.jsonl`
- Pipeline 이벤트: `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`
- 로그 아카이브: `data/log_archive/YYYY-MM-DD/*.gz`
- 운영 로그: `logs/*.log`

## 디렉터리

```text
KORStockScan/
├── src/
│   ├── bot_main.py
│   ├── engine/
│   ├── web/
│   ├── scanners/
│   ├── model/
│   ├── trading/
│   ├── market_regime/
│   ├── notify/
│   ├── database/
│   └── utils/
├── data/
├── docs/
├── deploy/
├── logs/
├── requirements.txt
└── README.md
```

## 테스트

예시:

```bash
.venv/bin/python -m pytest -q src/tests/test_post_sell_feedback.py
.venv/bin/python -m pytest -q src/tests/test_pipeline_event_logger.py
.venv/bin/python -m pytest -q src/tests/test_log_archive_service.py
```

## 운영 문서

- `docs/2026-04-11-codex-cloud-setup.md`
- `docs/ec2_web_service_runbook.md`
- `docs/emergency_buy_pause_runbook.md`
- `docs/latency_aware_entry_system_summary.md`
- `docs/scalping_dynamic_strength_gate_design.md`
- `docs/ml_gatekeeper_design.md`
- `docs/plan-korStockScanPerformanceOptimization.prompt.md`

## 면책

- 본 프로젝트는 자동매매 연구/운영 도구입니다.
- 투자 판단과 결과 책임은 사용자 본인에게 있습니다.
- 실거래 적용 전 모의/소액 검증을 권장합니다.
