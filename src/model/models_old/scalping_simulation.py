import time
from datetime import datetime, timedelta

# 테스트용 가상 설정값
TRADING_RULES = {
    "SCALP_TARGET": 2.0,
    "SCALP_STOP": -2.5,
    "SCALP_TRAILING_LIMIT": 0.5,
    "SCALP_TIME_LIMIT_MIN": 10,
    "MIN_FEE_COVER": 0.05,
}

highest_prices = {}


def simulate_trade(scenario_name, price_movement, ai_scores):
    """
    price_movement: 분당(또는 틱당) 가격 리스트
    ai_scores: 각 시점별 AI 점수 리스트
    """
    print(f"\n🎬 시나리오 테스트 시작: [{scenario_name}]")
    print("-" * 70)

    # 가상 종목 설정
    code = "005930"
    buy_price = price_movement[0]
    stock = {
        "name": "삼성전자",
        "code": code,
        "buy_price": buy_price,
        "strategy": "SCALPING",
        "order_time": time.time(),
        "rt_ai_prob": ai_scores[0] / 100.0,
    }

    highest_prices[code] = buy_price

    for i, curr_p in enumerate(price_movement):
        # 1. 데이터 업데이트
        ws_data = {"curr": curr_p}
        stock["rt_ai_prob"] = ai_scores[i] / 100.0
        current_ai_score = ai_scores[i]

        # 2. 로직 실행 (handle_holding_state의 핵심부 추출)
        if code not in highest_prices:
            highest_prices[code] = curr_p
        highest_prices[code] = max(highest_prices[code], curr_p)

        profit_rate = (curr_p - buy_price) / buy_price * 100
        drawdown = (highest_prices[code] - curr_p) / highest_prices[code] * 100

        # 파라미터 세팅
        if current_ai_score >= 75:
            dynamic_stop_pct = TRADING_RULES["SCALP_STOP"] - 1.0
            current_trailing_limit = TRADING_RULES["SCALP_TRAILING_LIMIT"]
        else:
            dynamic_stop_pct = TRADING_RULES["SCALP_STOP"]
            current_trailing_limit = 0.3

        is_sell_signal = False
        reason = ""

        # 매도 판단
        if profit_rate <= dynamic_stop_pct:
            is_sell_signal = True
            reason = f"🔪 손절선 이탈 ({dynamic_stop_pct}%)"
        elif profit_rate >= 0.3:
            if (
                profit_rate >= TRADING_RULES["SCALP_TARGET"]
                and drawdown >= current_trailing_limit
            ):
                is_sell_signal = True
                reason = f"🔥 트레일링 익절 (-{drawdown:.2f}% 밀림)"
            elif drawdown >= 0.8:
                is_sell_signal = True
                reason = f"⚠️ 심리적 고점 방어"

        if not is_sell_signal:
            if current_ai_score < 50 and profit_rate >= 0.5:
                is_sell_signal = True
                reason = f"🤖 AI 모멘텀 둔화 ({current_ai_score}점)"

        # 결과 출력
        status = "HOLD" if not is_sell_signal else "🚩 SELL"
        print(
            f"[{i+1:02d}회차] 가격:{curr_p:,.0f} | 수익:{profit_rate:+.2f}% | 고점대비:-{drawdown:.2f}% | AI:{current_ai_score}점 | {status}"
        )

        if is_sell_signal:
            print(f"✅ 결과: {reason}로 매도 완료!")
            break


# --- 시나리오 1: 목표가 달성 후 수급 믿고 버티다 하락 (트레일링 스탑 테스트) ---
prices_1 = [10000, 10100, 10250, 10300, 10280, 10220]  # +3% 찍고 밀림
ai_1 = [80, 85, 90, 88, 80, 78]
simulate_trade("트레일링 스탑 (수급 강세)", prices_1, ai_1)

# --- 시나리오 2: 수익권 진입 후 갑자기 AI 점수 폭락 (지능형 조기 익절 테스트) ---
prices_2 = [10000, 10050, 10080, 10070]  # 0.8% 수익 중인데 힘 빠짐
ai_2 = [70, 60, 40, 35]
simulate_trade("AI 지능형 조기 익절", prices_2, ai_2)

# --- 시나리오 3: 수급은 좋은데 가격이 밀리는 경우 (개미털기 방어/확장 손절 테스트) ---
prices_3 = [10000, 9800, 9700, 9650]  # -3.5%까지 수급 믿고 버티기
ai_3 = [95, 90, 85, 80]
simulate_trade("개미털기 방어 (확장 손절)", prices_3, ai_3)
