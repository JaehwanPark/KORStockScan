"""
실제 Gemini API에 프롬프트를 전송해 응답 가능 여부를 확인하는 라이브 스모크 테스트.

주의:
- 실제 네트워크/API 키가 필요합니다.
- 토큰 비용이 발생할 수 있습니다.
- CI 기본 테스트보다는 수동 검증용에 가깝습니다.
"""

import json
import re
import sys
from pathlib import Path

import pytest
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine.ai_engine import (
    ENHANCED_MARKET_ANALYSIS_PROMPT,
    REALTIME_ANALYSIS_PROMPT_DUAL,
    REALTIME_ANALYSIS_PROMPT_SCALP,
    REALTIME_ANALYSIS_PROMPT_SWING,
    SCALPING_OVERNIGHT_DECISION_PROMPT,
    SCALPING_SYSTEM_PROMPT,
    SWING_SYSTEM_PROMPT,
)
from src.utils.constants import TRADING_RULES


def load_api_key_from_config():
    config_path = PROJECT_ROOT / "data" / "config_prod.json"
    if not config_path.exists():
        raise FileNotFoundError(f"config_prod.json을 찾을 수 없습니다: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    api_key = config.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("config_prod.json에 GEMINI_API_KEY 필드가 없습니다")
    return api_key


def build_client():
    return genai.Client(api_key=load_api_key_from_config())


def parse_json_text(raw_text):
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"JSON 형식을 찾을 수 없습니다: {raw_text[:200]}")
    return json.loads(match.group())


def validate_scalp_or_swing_json(payload):
    assert payload["action"] in {"BUY", "WAIT", "DROP"}
    assert isinstance(payload["score"], int)
    assert isinstance(payload["reason"], str) and payload["reason"].strip()


def validate_condition_entry_json(payload):
    assert payload["decision"] in {"BUY", "WAIT", "SKIP"}
    assert isinstance(payload["confidence"], int)
    assert payload["order_type"] in {"MARKET", "LIMIT_TOP", "NONE"}
    assert isinstance(payload["position_size_ratio"], (int, float))
    assert isinstance(payload["invalidation_price"], int)
    assert isinstance(payload["reasons"], list)
    assert isinstance(payload["risks"], list)


def validate_condition_exit_json(payload):
    assert payload["decision"] in {"HOLD", "TRIM", "EXIT"}
    assert isinstance(payload["confidence"], int)
    assert isinstance(payload["trim_ratio"], (int, float))
    assert isinstance(payload["new_stop_price"], int)
    assert isinstance(payload["reason_primary"], str)
    assert isinstance(payload["warning"], str)


def validate_overnight_json(payload):
    assert payload["action"] in {"SELL_TODAY", "HOLD_OVERNIGHT"}
    assert isinstance(payload["confidence"], int)
    assert isinstance(payload["reason"], str) and payload["reason"].strip()
    assert isinstance(payload["risk_note"], str)


def validate_realtime_markdown(text, expected_prefixes):
    assert isinstance(text, str) and text.strip()
    for prefix in expected_prefixes:
        assert prefix in text


def validate_market_briefing(text):
    validate_realtime_markdown(
        text,
        [
            "📌 **[오버나이트 매크로]**",
            "📊 **[스캐너 내부 체력]**",
            "🧭 **[오늘 장 해석]**",
            "🎯 **[행동 지침]**",
        ],
    )


LIVE_CASES = [
    {
        "name": "scalping_system",
        "model": TRADING_RULES.AI_MODEL_TIER1,
        "prompt": SCALPING_SYSTEM_PROMPT,
        "user_input": """종목명: 테스트반도체
실시간 체결: 최근 10틱 모두 매수 우위, 체결 속도 가속
호가: 매도잔량 180,000 / 매수잔량 95,000
매수 압도율: 78%
현재가: 51,200원 / Micro-VWAP: 50,950원
당일 고가 돌파 직전이며 거래대금이 3분 동안 급증""",
        "require_json": True,
        "use_google_search": False,
        "validator": validate_scalp_or_swing_json,
    },
    {
        "name": "swing_system",
        "model": TRADING_RULES.AI_MODEL_TIER2,
        "prompt": SWING_SYSTEM_PROMPT,
        "user_input": """종목명: 테스트금융
현재가: 73,500원
5일선/20일선 위에서 8거래일 횡보 후 전고점 돌파 시도 중
프로그램 순매수 +142,000주, 외인 +55,000주, 기관 +31,000주
거래량은 최근 20일 평균 대비 185% 수준이며 과열 이격은 아직 크지 않다.""",
        "require_json": True,
        "use_google_search": False,
        "validator": validate_scalp_or_swing_json,
    },
    {
        "name": "realtime_scalp_report",
        "model": TRADING_RULES.AI_MODEL_TIER2,
        "prompt": REALTIME_ANALYSIS_PROMPT_SCALP,
        "user_input": """🚨 [요청 종목]
종목명: 테스트AI
종목코드: 005930
선택된 분석 모드: SCALP

📊 [실시간 전술 패킷]
[공통 상태]
- 현재가격: 82,300원
- VWAP: 82,050원
- 고가 돌파 여부: 직전 고가 재돌파 시도
- 체결강도 현재/1분/3분/5분: 148.0 / 136.0 / 121.0 / 110.0
- 프로그램 순매수 현재/증감: +25,000주 / +6,000주
- 매수/매도 체결량: +18,200 / +11,400 (순매수 +6,800)
- 체결 매수비율(WS): 63.0% / 체결량 기준 61.5%
- 스프레드: 1틱
- 일봉 구조: 전일 눌림 후 재돌파 초입""",
        "require_json": False,
        "use_google_search": False,
        "validator": lambda text: validate_realtime_markdown(
            text,
            [
                "📍 **[한 줄 결론]**",
                "🧠 **[핵심 해석]**",
                "⚠️ **[리스크 포인트]**",
                "🎯 **[실전 행동 지침]**",
            ],
        ),
    },
    {
        "name": "realtime_swing_report",
        "model": TRADING_RULES.AI_MODEL_TIER2,
        "prompt": REALTIME_ANALYSIS_PROMPT_SWING,
        "user_input": """🚨 [요청 종목]
종목명: 테스트조선
종목코드: 009999
선택된 분석 모드: SWING

📊 [실시간 전술 패킷]
[공통 상태]
- 현재가격: 48,700원
- VWAP: 48,200원
- 전일 고점: 49,000원
- 5/20/60일선 상태: 모두 상향 정배열
- 프로그램 순매수 현재/증감: +48,000주 / +7,500주
- 외인/기관 당일 가집계: 외인 +21,000주 / 기관 +14,000주
- 최근 20일 신고가 근접도: -1.8%
- 고가 대비 눌림폭: -0.9%""",
        "require_json": False,
        "use_google_search": False,
        "validator": lambda text: validate_realtime_markdown(
            text,
            [
                "📍 **[한 줄 결론]**",
                "🧠 **[핵심 해석]**",
                "⚠️ **[리스크 포인트]**",
                "🎯 **[실전 행동 지침]**",
            ],
        ),
    },
    {
        "name": "realtime_dual_report",
        "model": TRADING_RULES.AI_MODEL_TIER2,
        "prompt": REALTIME_ANALYSIS_PROMPT_DUAL,
        "user_input": """🚨 [요청 종목]
종목명: 테스트로봇
종목코드: 001234
선택된 분석 모드: DUAL

📊 [실시간 전술 패킷]
[공통 상태]
- 현재가격: 31,250원
- VWAP: 31,050원
- 체결강도 현재/3분/5분: 141.0 / 126.0 / 118.0
- 프로그램 순매수 현재/증감: +16,000주 / +3,200주
- 일봉 구조: 20일선 지지 후 박스 상단 돌파 시도
- 최근 20일 신고가 근접도: -0.7%
- 고가 돌파 여부: 장중 고가 재도전""",
        "require_json": False,
        "use_google_search": False,
        "validator": lambda text: validate_realtime_markdown(
            text,
            [
                "⚡ **[스캘핑 판단]**",
                "📈 **[스윙 판단]**",
                "🎯 **[최종 채택 관점]**",
                "🧭 **[실전 행동 지침]**",
            ],
        ),
    },
    {
        "name": "overnight_decision",
        "model": TRADING_RULES.AI_MODEL_TIER2,
        "prompt": SCALPING_OVERNIGHT_DECISION_PROMPT,
        "user_input": """🚨 [15:30 SCALPING 오버나이트 판정 요청]
종목명: 테스트반도체
종목코드: 005930

📊 [판정 입력 데이터]
- 포지션상태: HOLDING
- 평균단가: 80,500원
- 현재가: 82,100원 (손익 +1.99%)
- 보유분수: 46.0분
- 현재 전략라벨: SCALPING
- VWAP: 81,850원 / 상태: 상회
- 체결강도 현재/3분전/5분전: 137.0 / 129.0 / 120.0
- 프로그램 순매수 현재/증감: 32,000주 / +4,800주
- 외인/기관 순매수: 21,000주 / 7,000주
- 고가돌파 상태: 장중 고가 유지
- 일봉 구조: 박스 돌파 초입
- 5/20/60일선 상태: 상향, 상향, 상향
- 전일 고점/저점: 81,700 / 79,900
- 최근 20일 신고가 근접도: -0.4%
- 퀀트 종합점수/결론: 82.0 / 상승 지속 가능성 우세
- 주문상태 참고: 미체결 없음""",
        "require_json": True,
        "use_google_search": False,
        "validator": validate_overnight_json,
    },
    {
        "name": "market_briefing",
        "model": TRADING_RULES.AI_MODEL_TIER3,
        "prompt": ENHANCED_MARKET_ANALYSIS_PROMPT,
        "user_input": """현재 UTC 시각: 2026-04-06T00:15:00Z

[스캐너 통계]
- 전체 후보: 138개
- 최종 생존: 7개
- 탈락 사유 비중: 기초 품질 미달 31%, AI 확신도 부족 28%, 수급 부재 22%, 단기 급등/이격도 과다 19%
- 생존 업종 편중: 반도체 3, 전력기기 2, 조선 2

[오버나이트 매크로]
- 미국 증시는 반도체 강세와 함께 기술주 중심으로 상승 마감
- VIX는 전일 대비 하락했고 미 10년물 금리는 보합권
- 달러/원은 큰 변동 없이 안정적
- 한국 시장에 유리한 업종은 반도체/전력기기, 불리한 업종은 방어주로 요약 가능""",
        "require_json": False,
        "use_google_search": True,
        "validator": validate_market_briefing,
    },
]


def run_live_cases():
    client = build_client()
    results = []

    for case in LIVE_CASES:
        try:
            config_kwargs = {}
            if case["require_json"]:
                config_kwargs["response_mime_type"] = "application/json"
            if case["use_google_search"]:
                config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
            config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

            response = client.models.generate_content(
                model=case["model"],
                contents=[case["prompt"], case["user_input"]],
                config=config,
            )
            raw_text = (response.text or "").strip()
            parsed = parse_json_text(raw_text) if case["require_json"] else raw_text
            case["validator"](parsed)

            preview = json.dumps(parsed, ensure_ascii=False) if case["require_json"] else parsed
            results.append(
                {
                    "name": case["name"],
                    "model": case["model"],
                    "ok": True,
                    "preview": preview[:400],
                }
            )
        except Exception as e:
            results.append(
                {
                    "name": case["name"],
                    "model": case["model"],
                    "ok": False,
                    "error": str(e),
                }
            )

    return results


@pytest.mark.live_api
def test_live_gemini_prompt_smoke():
    results = run_live_cases()
    assert len(results) == len(LIVE_CASES)
    failed = [item for item in results if not item["ok"]]
    assert not failed, json.dumps(failed, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(json.dumps(run_live_cases(), indent=2, ensure_ascii=False))
