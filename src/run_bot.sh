#!/bin/bash

# 무한 루프 시작
while true; do
    echo "🚀 KORStockScan 스나이퍼 엔진을 시작합니다..."

    # 봇 실행 (경로나 파일명은 환경에 맞게 수정)
    python bot_main.py

    echo "🛑 봇 프로세스가 종료되었습니다."
    echo "⏳ 5초 후 엔진을 재가동합니다. (완전 종료를 원하면 지금 Ctrl+C를 누르세요)"
    sleep 5
done

# 깃허브 연동 테스트