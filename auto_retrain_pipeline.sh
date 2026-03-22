#!/bin/bash

# ==============================================================================
# KORStockScan V2 자동 재학습 파이프라인 (Auto Retrain Pipeline)
# 실행 주기: 1~3개월 단위 (주말 또는 야간)
# ==============================================================================

# 에러 발생 시 즉시 스크립트 실행을 중단하여 잘못된 모델이 배포되는 것을 방지합니다.
set -e

# 프로젝트 루트 경로 설정 (본인의 환경에 맞게 수정하세요)
PROJECT_DIR="/home/ubuntu/KORStockScan" # 예: AWS EC2 우분투 기본 경로
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/retrain_$(date +'%Y%m%d').log"

echo "==================================================" | tee -a $LOG_FILE
echo "🚀 KORStockScan V2 자동 재학습 시작: $(date)" | tee -a $LOG_FILE
echo "==================================================" | tee -a $LOG_FILE

# 1. 가상환경 활성화
echo "▶️ [1/5] 가상환경(venv) 활성화 중..." | tee -a $LOG_FILE
source $VENV_DIR/bin/activate

# 작업 디렉토리 이동
cd $PROJECT_DIR

# 2. 최신 KOSPI 데이터 적재 (업데이트 로직)
# (주의: 별도의 데이터 업데이트 스크립트가 있다면 경로를 맞춰주세요. 예: src/data/update_kospi.py)
echo "▶️ [2/5] DB 최신화 및 KOSPI 데이터 적재 중..." | tee -a $LOG_FILE
# python src/data/update_kospi.py >> $LOG_FILE 2>&1

# 3. Base 모델 4종 재학습 (절대 평가 안전망 갱신)
echo "▶️ [3/5] Base 모델(XGB, LGBM) 재학습 진행 중..." | tee -a $LOG_FILE
echo " - Hybrid XGB 학습..." | tee -a $LOG_FILE
python src/models/train_hybrid_xgb_v2.py >> $LOG_FILE 2>&1

echo " - Hybrid LGBM 학습..." | tee -a $LOG_FILE
python src/models/train_hybrid_lgbm_v2.py >> $LOG_FILE 2>&1

echo " - Bull Specialists(상승장 특화) 학습..." | tee -a $LOG_FILE
python src/models/train_bull_specialists_v2.py >> $LOG_FILE 2>&1

# 4. Meta Ranker 모델 재학습 (상대 평가 랭킹 갱신)
# Base 모델의 예측 결과를 바탕으로 최근 3개월의 트렌드에 맞춰 랭킹 모델을 갱신합니다.
echo "▶️ [4/5] Meta Ranker 모델(LGBMRanker) 재학습 중..." | tee -a $LOG_FILE
python src/models/train_meta_model_v2.py >> $LOG_FILE 2>&1

# 5. 최종 백테스트 및 검증
# 학습된 모델이 실전 설정(슬리피지, 갭, 수수료 반영)에서 누적 수익 양수를 내는지 검증합니다.
echo "▶️ [5/5] V2 정밀 백테스터 구동 및 수익률 검증 중..." | tee -a $LOG_FILE
python src/models/backtest_v2.py >> $LOG_FILE 2>&1

echo "==================================================" | 파이프라인 | tee -a $LOG_FILE
echo "✅ 모든 파이프라인이 성공적으로 완료되었습니다: $(date)" | tee -a $LOG_FILE
echo "📄 상세 로그: $LOG_FILE" | tee -a $LOG_FILE
echo "==================================================" | tee -a $LOG_FILE

# 가상환경 비활성화
deactivate