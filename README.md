# Swing-Automated-Trading-System
본 프로젝트는 AI 기반의 종목 선별(Scanner)과 웹소켓 기반의 실시간 정밀 타격(Sniper)을 결합한 하이브리드 자동매매 시스템입니다.

1. 시스템 아키텍처 (Architecture)시스템은 크게 오프라인 학습 레이어와 온라인 실행 레이어로 나뉩니다.
   Offline: 기초 데이터 수집 → 피처 엔지니어링 → 모델 학습 → 백테스팅
   Online: 데일리 업데이트 → 콰트로 스캐너(종목 추출) → 스나이퍼(실시간 감시 및 매매)
   
2. 주요 프로세스별 명세 (Component Specifications)
   ① 기초 데이터 수집 및 업데이트 (update_database)
     역할: 모델 학습 및 스캔을 위한 원천 데이터 확보.
     내용: * FinanceDataReader를 통한 KOSPI 전 종목 시세 및 거시경제 지표(금리, 환율 등) 수집.
     SQLite DB를 활용한 증분 업데이트(Upsert).
   ② 모델 학습 및 백테스팅 (train_model & backtest)
     역할: 과거 데이터를 바탕으로 승률이 높은 패턴 학습 및 검증.
     원리: XGBoost/LightGBM 등 머신러닝 알고리즘을 활용해 내일의 상승 확률($P$)을 예측.
     지표: 이동평균선 괴리율, RSI, 볼린저 밴드, 거래량 변동성 등 20여 가지 피처 활용.
   ③ 콰트로 스캐너 (run_scanner)
     역할: 장 시작 전/후, 학습된 모델을 통해 당일의 사냥감(Target) 포착.
     분류:MAIN: AI 예측 확률 70% 이상의 고확신 종목.RUNNER: 수급 및 기술적 지표가 정배열된 추세 종목.
     결과: recommendation_history 테이블에 WATCHING 상태로 저장.
   ④ 스나이퍼 (run_sniper)
     역할: WATCHING 종목을 실시간 감시하여 최적의 타점에 진입.
     작동원리: * 통합 수신: WebSocket을 통해 0B(체결강도)와 0D(호가잔량) 데이터를 100% 실시간 스트리밍.
     확신 지수($Score$): $Score = (AI\,Prob \times 50) + (Supply/Demand \times 25) + (Execution \times 25)$
     상태 변화: WATCHING → HOLDING(매수) → COMPLETED(익절/손절).

3. 운영 방식 (Operation Manual)
   시간대,작업 (Task),설명
08:00 - 08:30,DB Update & Scan,전일 데이터 업데이트 및 당일 WATCHING 종목 리스트 생성
08:30 - 09:00,Sniper Standby,"웹소켓 연결 및 텔레그램 리스너 가동, 구독(REG) 설정"
09:00 - 15:30,Real-time Sniping,실시간 점수 계산 및 WATCHING → HOLDING 자동 전환
장중 상시,Manual Analysis,텔레그램 /분석 [코드] 명령으로 즉석 리포트 확인
장 종료 후,Performance Review,당일 매매 결과 정리 및 모델 재학습 데이터 적재

4. 기술 스택 및 통신 규격
Language: Python 3.13
Database: SQLite3
API (Kiwoom K-Series):
REST API (POST): ka10001(종목명: stk_nm), au10001(토큰 발급)
WebSocket: 0B(주식체결: Fid 10, 228), 0D(호가잔량: Fid 121, 125)
Libraries: asyncio, websockets, pandas, scikit-learn, requests

