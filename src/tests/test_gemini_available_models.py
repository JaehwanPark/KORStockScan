"""
Gemini API 사용 가능 모델 목록 조회 테스트
API 키값으로 사용 가능한 Gemini 모델들 raw response 출력
"""

import sys
import json
from pathlib import Path

# 프로젝트 루트 path 설정
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google import genai


def load_api_key_from_config():
    """config_prod.json에서 Gemini API 키 로드"""
    config_path = PROJECT_ROOT / "data" / "config_prod.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"config_prod.json을 찾을 수 없습니다: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    api_key = config.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("config_prod.json에 GEMINI_API_KEY 필드가 없습니다")
    
    return api_key


def test_list_available_gemini_models():
    """
    테스트: API 키로 사용 가능한 Gemini 모델 목록 조회 (raw response)
    """
    # 1. API 키 로드
    api_key = load_api_key_from_config()
    
    # 2. Gemini 클라이언트 생성
    client = genai.Client(api_key=api_key)
    
    # 3. 모델 목록 조회
    models_response = client.models.list()
    
    # 4. 모델 리스트 변환 후 출력
    models_list = list(models_response)
    
    # 구조화된 데이터로 변환
    models_data = []
    for model in models_list:
        model_dict = {
            "name": model.name,
            "display_name": getattr(model, 'display_name', None),
            "description": getattr(model, 'description', None),
            "input_token_limit": getattr(model, 'input_token_limit', None),
            "output_token_limit": getattr(model, 'output_token_limit', None),
            "supported_generation_methods": getattr(model, 'supported_generation_methods', None),
        }
        models_data.append(model_dict)
    
    # JSON으로 출력
    print(json.dumps(models_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_list_available_gemini_models()