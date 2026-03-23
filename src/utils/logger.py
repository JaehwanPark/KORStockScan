# src/utils/logger.py
import os
import inspect
from datetime import datetime
from src.utils.constants import LOGS_DIR

def log_error(msg: str, send_telegram: bool = False):
    """
    중앙 집중형 에러 관리 함수 (호출한 파일명으로 분리 & 상세 원인 자동 기록)
    """
    try:
        # 1. 누가 나를 불렀는지 역추적
        caller_frame = inspect.stack()[1]
        caller_filename = os.path.basename(caller_frame.filename).replace('.py', '')
        
        # 2. 에러 메시지 포맷팅
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] 🚨 ERROR in {caller_filename}: {msg}\n"
        
        # 3. 파일에 기록 (logs/파일명_error.log)
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_filepath = LOGS_DIR / f"{caller_filename}_error.log"
        
        with open(log_filepath, 'a', encoding='utf-8') as f:
            f.write(log_message)
            
        print(log_message.strip()) # 콘솔에도 출력
        
        # 💡 주의: 텔레그램 발송 기능은 순환 참조 방지를 위해 여기서 직접 import하지 않고,
        # bot_main.py나 최상단 계층에서 비동기로 처리하는 것이 안전해!
        if send_telegram:
            pass # (임시 보류) 알림 시스템 리팩토링 시 콜백 구조로 연결할 예정
            
    except Exception as e:
        print(f"[FATAL] 로깅 시스템 자체 에러 발생: {e}")

def log_info(msg: str, send_telegram: bool = False):
    """
    중앙 집중형 정보 로깅 함수 (호출한 파일명으로 분리 & 자동 기록)
    """
    try:
        # 1. 누가 나를 불렀는지 역추적
        caller_frame = inspect.stack()[1]
        caller_filename = os.path.basename(caller_frame.filename).replace('.py', '')
        
        # 2. 정보 메시지 포맷팅
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] 📢 INFO in {caller_filename}: {msg}\n"
        
        # 3. 파일에 기록 (logs/파일명_info.log)
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_filepath = LOGS_DIR / f"{caller_filename}_info.log"
        
        with open(log_filepath, 'a', encoding='utf-8') as f:
            f.write(log_message)
            
        print(log_message.strip()) # 콘솔에도 출력
        
        # 💡 주의: 텔레그램 발송 기능은 순환 참조 방지를 위해 여기서 직접 import하지 않고,
        # bot_main.py나 최상단 계층에서 비동기로 처리하는 것이 안전해!
        if send_telegram:
            pass # (임시 보류) 알림 시스템 리팩토링 시 콜백 구조로 연결할 예정
            
    except Exception as e:
        print(f"[FATAL] 로깅 시스템 자체 에러 발생: {e}")