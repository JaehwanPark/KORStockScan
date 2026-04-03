# KORStockScan

KORStockScan은 키움 REST/WebSocket 기반의 한국 주식 자동매매 시스템입니다.  
현재 버전은 크게 두 축으로 운영됩니다.

- 스윙 매매: 일봉/수급/머신러닝 기반의 후보 선별 후 장중 엔진이 진입/청산
- 스캘핑 매매: 조건검색식과 실시간 호가/체결 흐름을 기반으로 짧은 호흡으로 진입/청산

최근 버전에서는 아래 기능이 반영되어 있습니다.

- `pause.flag` 기반의 긴급 매매중단
  신규 매수와 추가매수만 차단하고, 기존 보유 종목 청산은 계속 유지
- latency-aware entry system
  주문 직전 가격 재조회 없이 내부 웹소켓 캐시만으로 진입 유효성 판단
- fallback entry
  애매한 latency 구간에서는 `scout + main` 분할 진입 사용
- entry metrics
  관리자 텔레그램에서 장중 수동조회, 장마감 자동요약 제공

---

## 디렉터리 구조

```text
KORStockScan/
├── src/
│   ├── bot_main.py
│   ├── core/
│   ├── database/
│   ├── engine/
│   ├── market_regime/
│   ├── model/
│   ├── notify/
│   ├── scanners/
│   ├── tests/
│   ├── trading/
│   ├── utils/
│   └── web/
├── data/
├── docs/
├── logs/
├── requirements.txt
└── README.md
```

---

## 디렉터리별 주요 기능

### `src/bot_main.py`
- 시스템 시작점
- 텔레그램 수신탑, 스캐너, 스나이퍼 엔진, 장마감 요약 브로드캐스트를 연결

### `src/core/`
- `event_bus.py`
  엔진 간 결합도를 낮추기 위한 내부 이벤트 버스

### `src/database/`
- `db_manager.py`
  SQLAlchemy 세션/트랜잭션 관리
- `models.py`
  추천 이력, 사용자, 일봉 데이터 등 핵심 테이블 정의

### `src/engine/`
- `kiwoom_sniper_v2.py`
  메인 실시간 매매 엔진
- `sniper_state_handlers.py`
  `WATCHING`, `BUY_ORDERED`, `HOLDING`, `SELL_ORDERED` 상태별 핵심 매매 로직
- `sniper_execution_receipts.py`
  체결 영수증 반영, 평균단가/수량 누적, fallback entry fill 처리
- `kiwoom_orders.py`
  매수/매도/취소 주문 API 래퍼
- `sniper_condition_handlers.py`
  조건검색식 포착 종목을 어떤 전략으로 감시/진입시킬지 결정
- `sniper_s15_fast_track.py`
  초단타 fast-track 진입 로직
- `trade_pause_control.py`
  긴급 매매중단 상태 동기화
- `sniper_entry_latency.py`
  기존 엔진과 latency-aware entry 계층을 연결하는 브릿지
- `sniper_entry_state.py`
  fallback bundle, late receipt, 공용 락 등 entry runtime state 관리
- `sniper_entry_metrics.py`
  장중/장마감 진입 지표 집계

### `src/scanners/`
- `final_ensemble_scanner.py`
  스윙 후보를 선별하고 DB에 적재
- `scalping_scanner.py`
  초단타 감시 후보를 발굴하고 웹소켓 감시 등록
- `kosdaq_scanner.py`
  코스닥 계열 종목 스캔
- `crisis_monitor.py`
  글로벌 위험 이벤트 감시

### `src/model/`
- V2 추천 모델 학습/추론 파이프라인
- `feature_engineering_v2.py`
  학습과 추론에 공통으로 쓰는 피처 생성
- `dataset_builder_v2.py`
  모델용 패널 데이터 생성
- `train_hybrid_xgb_v2.py`, `train_hybrid_lgbm_v2.py`
  범용 base model 학습
- `train_bull_specialists_v2.py`
  상승장 특화 base model 학습
- `train_meta_model_v2.py`
  base model 출력 결합용 meta model 학습
- `recommend_daily_v2.py`
  당일 추천 종목 CSV 생성
- `backtest_v2.py`
  V2 모델 백테스트
- `common_v2.py`
  V2 모델 경로, 공통 피처, 추천 CSV 경로 정의

### `src/trading/`
- latency-aware entry 전용 독립 계층
- `entry/`
  entry policy, fallback strategy, state machine, orchestrator
- `market/`
  websocket quote health/cache
- `order/`
  tick utils, order manager, order types
- `config/`
  latency-aware entry 설정값

### `src/notify/`
- `telegram_manager.py`
  관리자/사용자용 텔레그램 인터페이스와 알림 처리

### `src/utils/`
- `constants.py`
  전역 매매 규칙과 경로 상수
- `runtime_flags.py`
  `pause.flag` 생성/삭제/조회
- `kiwoom_utils.py`
  키움 API 유틸, 종목 필터, 호가 단위 처리
- `logger.py`
  파일/콘솔 로거
- `update_kospi.py`
  일봉 데이터 적재 및 야간 배치 연결

### `src/web/`
- 웹 리포트 및 진단 페이지 관련 코드

### `data/`
- 모델 파일, 추천 CSV, 예측 CSV, 설정 파일 저장 위치

### `docs/`
- 운영 문서, 설계 문서, 런북 모음

---

## 파일별 핵심 포인트

### 매매 엔진 핵심 파일

| 파일 | 주요 기능 |
| --- | --- |
| `src/engine/kiwoom_sniper_v2.py` | 실시간 엔진 실행, 웹소켓/상태머신/계좌 동기화 오케스트레이션 |
| `src/engine/sniper_state_handlers.py` | 신규 진입, 보유 관리, 청산, 추가매수, timeout/cleanup 처리 |
| `src/engine/sniper_execution_receipts.py` | 체결 영수증 기준 메모리/DB 상태 갱신 |
| `src/engine/kiwoom_orders.py` | 주문 전송, 취소, 스마트 매도, IOC/지정가 매핑 |
| `src/engine/sniper_entry_latency.py` | SAFE/CAUTION/DANGER 진입 판단 |
| `src/engine/trade_pause_control.py` | 긴급 매매중단 상태와 EventBus 반영 |

### 스캐너/추천 계층 핵심 파일

| 파일 | 주요 기능 |
| --- | --- |
| `src/scanners/final_ensemble_scanner.py` | 스윙 추천 후보 선별, V2 추천 CSV 적재 |
| `src/scanners/scalping_scanner.py` | 초단타 감시 종목 발굴 후 실시간 감시망 등록 |
| `src/model/recommend_daily_v2.py` | V2 모델 점수 계산 후 `daily_recommendations_v2.csv` 생성 |
| `src/model/feature_engineering_v2.py` | 모델 공통 피처 생성 |
| `src/model/train_meta_model_v2.py` | 메타 랭커 학습 |

### 운영/제어 핵심 파일

| 파일 | 주요 기능 |
| --- | --- |
| `src/notify/telegram_manager.py` | 텔레그램 명령, 관리자 제어, 상태 조회 |
| `src/utils/runtime_flags.py` | pause flag truth source |
| `src/engine/sniper_entry_metrics.py` | 진입 지표 수동조회/장마감 요약 |
| `src/bot_main.py` | 전체 프로세스 기동 및 스케줄링 |

---

## 매매 로직 개요

## 1. 스윙 매매 로직

### 스윙 매수 로직
스윙 매수는 크게 두 단계로 나뉩니다.

1. 장 시작 전 또는 주기 배치에서 스캐너가 후보를 선별
2. 실시간 엔진이 `WATCHING` 상태에서 실제 진입 여부를 최종 판단

주요 흐름:

- `final_ensemble_scanner.py`가 코스피/코스닥 후보를 스캔
- V2 모델 점수와 수급 조건을 통과한 종목을 DB에 `WATCHING`으로 저장
- 장중 `kiwoom_sniper_v2.py` + `sniper_state_handlers.py`가 실시간 현재가, radar, 시장 상태를 확인
- latency-aware entry gate가 진입 시점의 유효성을 다시 점검
- `SAFE`면 일반 진입, `CAUTION`이면 fallback 진입, `DANGER`면 진입 차단

스윙 매수 특징:

- 일봉/수급/ML 점수 기반으로 후보를 먼저 압축
- 실시간 진입에서는 늦은 진입을 기본적으로 포기
- 주문 수량은 `주문가능금액 x 전략비중 x 안전계수`로 계산
- 기본 안전계수는 보수적으로 적용하되, 전략 예산으로 1주 매수가 가능한데 95% 절삭 때문에 0주가 되는 경우에만 완화 안전계수로 1회 재계산
- pause 상태에서는 신규 매수와 추가매수 차단

### 스윙 매도 로직
스윙 매도는 `HOLDING` 상태에서 손익, 보유 기간, 전략 태그를 기준으로 판단합니다.

대표 조건:

- 목표 수익 도달 후 익절
- 손절선 이탈 시 방어적 청산
- 전략별 최대 보유 기간 초과 시 시간 청산
- 일부 태그는 트레일링 방식으로 수익 보호

스윙 매도 특징:

- SELL은 pause 상태에서도 계속 허용
- 긴급 매매중단은 신규 BUY/add만 막고 청산은 막지 않음

---

## 2. 스캘핑 매매 로직

### 스캘핑 매수 로직
스캘핑은 감시 후보 발굴과 실시간 진입이 더 촘촘하게 연결됩니다.

주요 흐름:

- `scalping_scanner.py`가 거래량/등락률/수급 급변 종목을 발굴
- 종목을 `WATCHING`으로 저장하고 웹소켓 실시간 감시 등록
- `sniper_condition_handlers.py`가 조건검색식 포착 종목을 전략별로 라우팅
- `sniper_state_handlers.py`가 호가/틱/AI/radar 기반으로 신규 진입 판단
- `sniper_entry_latency.py`가 신호 시점 가격/시간을 freeze 하고 진입 허용 여부 판단

latency-aware 진입 기준:

- `SAFE`: 일반 진입
- `CAUTION`: `scout + main` fallback 진입
- `DANGER`: 진입 차단

추가 특징:

- 주문 직전 별도 현재가 API 재조회는 하지 않음
- fallback entry는 정찰병 + 본대를 나눠서 진입
- 늦은 체결 영수증도 terminal entry order grace window로 재매칭
- 매수 수량은 `주문가능금액 x 전략비중 x 안전계수`를 기본으로 계산하고, 1주도 안 나오는 경우에만 완화 안전계수 재시도로 과도한 0주 판정을 줄임
- pause 상태에서는 신규 스캘핑 BUY도 차단

### 동적 체결강도 관측과 shadow 피드백
스캘핑 진입에서는 기존 `VPW_SCALP_LIMIT` 하드 게이트를 유지하면서, 별도로 동적 체결강도 가속도 관측을 병행합니다.

핵심 개념:

- 누적 체결강도는 최소 베이스 확인용으로만 사용
- 같은 window 안의 BUY 체결대금, BUY 체결량 비율, 순매수 체결량을 함께 확인해 휩소를 방어
- 정적 `VPW_SCALP_LIMIT`에는 막혔지만 동적 조건은 통과한 후보는 `shadow candidate`로 저장
- 장마감에는 이 후보들이 실제로 진입 가치가 있었는지 분봉 기준으로 사후 평가

현재 기본 동작:

- 웹소켓 실시간 체결 데이터에서 동적 체결강도 지표를 계산
- `sniper_state_handlers.py`가 `strength_momentum_observed`, `strength_momentum_pass` 로그를 남김
- 동적 체결강도와 AI 확답을 통과하면 스캘핑 `entry_armed` 상태로 잠시 고정되어, 다음 루프에서는 자격 게이트를 다시 되감지 않고 주문 안전 게이트만 재확인
- `SCALP_DYNAMIC_VPW_OBSERVE_ONLY=False`이면 동적 게이트를 실전 진입에 적용하고, `dynamic_vpw_override_pass`로 정적 `VPW_SCALP_LIMIT` 우회 진입을 기록
- `SCALP_DYNAMIC_VPW_OBSERVE_ONLY=True`로 돌리면 정적 `VPW_SCALP_LIMIT`에 막히면서도 동적 조건은 통과한 경우 `shadow_candidate_recorded` 로그를 남기고 후보를 저장
- 장마감 요약 시 기존 진입 지표 요약 뒤에 `shadow feedback` 결과를 함께 관리자에게 전송

주요 로그 위치:

- 실시간 파이프라인 로그: `logs/sniper_state_handlers_info.log`
- 운영 히스토리 로그: `logs/bot_history.log`

주요 로그 키워드:

- `strength_momentum_observed`
- `strength_momentum_pass`
- `blocked_vpw`
- `blocked_strength_momentum`
- `dynamic_vpw_override_pass`
- `shadow_candidate_recorded`

저장 파일:

- shadow 후보: `data/shadow/strength_shadow_candidates_YYYY-MM-DD.jsonl`
- shadow 평가: `data/shadow/strength_shadow_evaluations_YYYY-MM-DD.jsonl`

수동 점검 명령:

- 동적 관측 집계:
  `python3 src/tests/test_strength_momentum_observation.py --date 2026-04-03 --top 10`
- shadow 피드백 평가:
  `python3 src/tests/test_strength_shadow_feedback.py --date 2026-04-03`

운영 해석 포인트:

- `blocked_vpw`인데 `dynamic_allowed=True`면 기존 120 하드게이트 때문에 놓친 후보일 수 있음
- `shadow_candidate_recorded`가 쌓이면 이후 장마감 리포트에서 실제 가치가 있었는지 `GOOD/NEUTRAL/BAD`로 확인 가능
- 분봉 평가는 신호 즉시 틱 재현이 아니라 “신호 직후 다음 분부터”의 보수적 성과 측정 기준을 사용
- 수동 평가 스크립트는 `kiwoom_utils` 의존성을 타므로 실행 환경에 `pandas` 등 런타임 의존성이 필요

### 웹 리포트와 일일 대시보드
운영 화면은 Flask 웹 서버가 제공하며, 실시간 관측 대시보드와 일일 전략 리포트를 같은 톤으로 확인할 수 있습니다.

주요 화면:

- 일일 리포트: `/` 또는 `/daily-report`
- 동적 체결강도 대시보드: `/strength-momentum`
- 진입 게이트 플로우 대시보드: `/entry-pipeline-flow`

주요 API:

- 일일 리포트 JSON: `/api/daily-report?date=YYYY-MM-DD`
- 동적 체결강도 JSON: `/api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- 진입 게이트 플로우 JSON: `/api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`

일일 리포트 생성:

- 수동 생성:
  `python3 src/web/daily_report_generator.py --date 2026-04-03`
- 점검 요약:
  `python3 src/tests/test_daily_report.py --date 2026-04-03`
- `bot_main.py` 부팅 시 1회 자동 생성
- 매 영업일 `08:45`에 웹/API용 JSON 자동 갱신

자동기동:

- 웹 서비스 파일: `deploy/systemd/korstockscan-web.service`
- 서버 반영 후:
  `sudo systemctl enable --now korstockscan-web.service`
- 상태 확인:
  `sudo systemctl status korstockscan-web.service`
- 로그 확인:
  `sudo journalctl -u korstockscan-web.service -f`

운영 원칙:

- `bot_main.py`는 리포트 JSON 생성 담당
- `src/web/app.py`는 별도 프로세스(systemd)로 상시 실행
- Flutter 앱은 위 JSON API를 그대로 소비하는 것을 기준으로 설계

### 스캘핑 매도 로직
스캘핑 매도는 스윙보다 더 짧은 주기로 손절/익절/모멘텀 약화를 감시합니다.

대표 조건:

- 하드스탑 / 소프트스탑 도달
- AI 점수 급락 시 조기 손절
- 수익 구간 진입 후 모멘텀 둔화 시 익절
- 고점 대비 되밀림 발생 시 트레일링 익절
- fast-track/S15 계열은 별도 초단타 처리 로직 사용

추가 특징:

- 일부 스캘핑 포지션은 preset TP를 사용
- fallback 부분체결 뒤에도 TP 수량이 누적 체결 수량으로 재발행되도록 보강됨
- SELL 직전 미체결 entry BUY가 남아 있으면 먼저 취소 후 청산으로 넘어감

---

## 추가매수와 긴급 매매중단

### 추가매수
추가매수는 `AVG_DOWN`, `PYRAMID` 두 계열로 관리됩니다.

- `AVG_DOWN`: 눌림/손실 구간에서 평균단가 조정
- `PYRAMID`: 수익 구간에서 추세 강화 시 증액

추가매수는 `HOLDING` 상태에서만 검토되며, 전략/시장상태/횟수 제한을 따릅니다.

### 긴급 매매중단
`pause.flag`가 존재하면 시스템은 아래 상태로 간주합니다.

- 신규 매수 및 추가매수 중단 상태

유지되는 것:

- 웹소켓 연결
- 실시간 시세 수신
- 계좌 동기화
- HOLDING 종목 청산
- 체결 영수증 처리
- DB/로그/텔레그램 알림

즉, pause는 전체 중단이 아니라 BUY-side 중단입니다.

---

## Latency-Aware Entry System

최근 진입 제어는 `src/trading/` + `src/engine/sniper_entry_latency.py` 계층으로 분리되었습니다.

핵심 원칙:

- 신호 발생 시점 가격/시간을 기준으로 판단
- 주문 직전 가격 재조회 금지
- 내부 websocket cache만 사용
- 늦었으면 안 삼
- 위험 latency 상태면 신규 진입 차단

주요 구성:

- `src/trading/entry/entry_policy.py`
  진입 허용/차단 정책
- `src/trading/entry/fallback_strategy.py`
  `scout + main` 주문 계획 생성
- `src/trading/market/market_data_cache.py`
  quote health 계산용 실시간 캐시
- `src/trading/order/tick_utils.py`
  한국 주식 호가단위 처리

---

## V2 모델 설명

현재 일일 추천 계층은 V2 모델 파이프라인을 기준으로 움직입니다.

구성:

- `hybrid_xgb_v2.pkl`
- `hybrid_lgbm_v2.pkl`
- `bull_xgb_v2.pkl`
- `bull_lgbm_v2.pkl`
- `stacking_meta_v2.pkl`

의미:

- `hybrid_*`
  일반 구간에서 쓰는 base model
- `bull_*`
  상승장 특화 base model
- `stacking_meta_v2`
  여러 base model 출력을 다시 결합하는 meta ranker

학습/추천 흐름:

1. `dataset_builder_v2.py`가 패널 데이터 생성
2. `feature_engineering_v2.py`가 공통 피처 생성
3. 4개 base model 점수 산출
4. meta model이 최종 score 계산
5. `recommend_daily_v2.py`가 추천 CSV 저장

---

## `daily_recommendations_v2.csv` 설명

파일 위치:

- `data/daily_recommendations_v2.csv`

이 파일은 당일 스윙 추천 후보의 최종 결과물입니다.  
주로 `final_ensemble_scanner.py`가 우선 로드하여 DB 추천 이력에 적재하는 입력 소스로 사용합니다.

대표 컬럼:

- `date`: 추천 기준 거래일
- `code`: 종목코드
- `name`: 종목명
- `hx`, `hl`, `bx`, `bl`: 각 base model 출력
- `mean_prob`, `bull_mean`, `hybrid_mean`: base score 요약값
- `bull_regime`: 장세 구분 정보
- `score`: meta model 최종 점수

운영 의미:

- `score`는 최종 정렬용 점수
- `hybrid_mean`은 1차 안전망처럼 사용
- 스캐너는 이 파일을 읽어 `MAIN` 또는 `RUNNER` 성격으로 DB에 적재

즉, `daily_recommendations_v2.csv`는 “모델 결과를 엔진이 실제 감시/매매 후보로 넘기기 직전의 브리지 파일” 역할을 합니다.

---

## 텔레그램 기능

텔레그램은 운영/조회 용도로만 간단히 정리하면 아래와 같습니다.

- 관리자 전용 긴급 매매중단 / 재개
- 현재 매매 상태 조회
- 장중 진입 지표 수동 조회
- 장마감 진입 지표 자동 요약
- 종목 코드 기반 실시간 분석 조회

중요한 점:

- 텔레그램 제어는 관리자 권한 검증 후에만 실행
- 버튼 노출과 실제 실행 권한은 별도로 검사

### 메시지 발송 구분

내부적으로는 EventBus를 통해 메시지를 발행하고, `telegram_manager.py`가 이를 실제 텔레그램 전송으로 라우팅합니다.

> Remark: 현재 메시지 라우팅은 운영 중인 실제 흐름 기준으로 정리한 것이며, 세부 메시지 종류와 audience 정책은 추후 추가 정리 및 재분류될 수 있습니다.

| 구분 | 내부 이벤트 / audience | 수신 대상 | 대표 메시지 유형 |
| --- | --- | --- | --- |
| 관리자 즉시 알림 | `TELEGRAM_ADMIN_NOTIFY` | 관리자 1인 | 주문 거절, 주문 전송 예외, 시스템 예외, 즉시 확인이 필요한 운영 경고 |
| 관리자 전용 브로드캐스트 | `TELEGRAM_BROADCAST` + `ADMIN_ONLY` | 관리자 1인 | pause 상태 변경, 부팅 시 pause 감지, 장마감 진입지표 요약, 데이터 갱신 상태, overnight gatekeeper 리포트, 관리자용 AI/디버그 메시지 |
| VIP/관리자 브로드캐스트 | `TELEGRAM_BROADCAST` + `VIP_ALL` | 관리자 + VIP 사용자 | 장전 추천 리포트, 장중 코스닥/스윙/스캘핑 후보 알림, 일부 체결 알림, 종목 분석 브리핑 |

### 운영 해석 포인트

- `TELEGRAM_ADMIN_NOTIFY`
  아주 짧고 즉시성이 필요한 경고를 관리자에게 바로 보낼 때 사용합니다.
- `ADMIN_ONLY`
  시스템 운영 상태나 제어 결과처럼 관리자만 알아야 하는 메시지에 사용합니다.
- `VIP_ALL`
  실제 매매 후보, 브리핑, 일반 서비스성 알림처럼 관리자와 VIP가 함께 받아야 하는 메시지에 사용합니다.

---

## 실행 메모

주요 실행 파일:

- 메인 실행: `src/bot_main.py`
- 일봉/야간 배치: `src/utils/update_kospi.py`
- 일일 추천 생성: `src/model/recommend_daily_v2.py`
- 동적 체결강도 관측 집계: `src/tests/test_strength_momentum_observation.py`
- shadow 피드백 수동 평가: `src/tests/test_strength_shadow_feedback.py`

필요 파일:

- `data/config_prod.json`
- 키움 API 인증 정보
- PostgreSQL 연결 정보

---

## 면책사항

본 프로젝트는 개인 연구, 시스템 트레이딩 실험, 운영 자동화 목적으로 작성되었습니다.

1. 모든 투자 판단과 매매 실행의 책임은 사용자 본인에게 있습니다.
2. 자동매매 시스템은 네트워크 장애, API 변경, 체결 지연, 데이터 오류, 로직 버그로 인해 손실이 발생할 수 있습니다.
3. 실거래 적용 전에는 반드시 모의환경 또는 소액 검증을 거쳐야 합니다.
4. 본 저장소의 코드와 문서는 수익을 보장하지 않으며, 특정 종목 매수/매도를 권유하지 않습니다.
