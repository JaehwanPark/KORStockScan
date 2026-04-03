from src.engine.ai_engine import GeminiSniperEngine
from src.utils.constants import TRADING_RULES


def _build_engine():
    return GeminiSniperEngine.__new__(GeminiSniperEngine)


def test_realtime_quant_packet_includes_ws_microstructure_fields():
    engine = _build_engine()
    realtime_ctx = {
        "strat_label": "KOSPI_ML",
        "position_status": "NONE",
        "avg_price": 0,
        "pnl_pct": 0.0,
        "curr_price": 12570,
        "fluctuation": 3.42,
        "target_price": 12800,
        "target_reason": "watching gatekeeper",
        "trailing_pct": 4.0,
        "stop_pct": 2.0,
        "trend_score": 78.0,
        "flow_score": 84.0,
        "orderbook_score": 72.0,
        "timing_score": 69.0,
        "score": 81.0,
        "conclusion": "눌림 후 재돌파 감시",
        "today_vol": 1450000,
        "vol_ratio": 182.5,
        "today_turnover": 18450000000,
        "v_pw_now": 118.2,
        "v_pw_1m": 111.5,
        "v_pw_3m": 106.7,
        "v_pw_5m": 102.4,
        "buy_ratio_now": 63.4,
        "buy_ratio_1m": 59.8,
        "buy_ratio_3m": 56.2,
        "trade_qty_signed_now": 1250,
        "prog_net_qty": 18500,
        "prog_delta_qty": 2200,
        "prog_buy_qty": 24300,
        "prog_sell_qty": 5800,
        "prog_buy_amt": 301000000,
        "prog_sell_amt": 82000000,
        "foreign_net": 4300,
        "inst_net": 5200,
        "smart_money_net": 9500,
        "tick_trade_value": 28500,
        "cum_trade_value": 950000,
        "buy_exec_volume": 1240,
        "sell_exec_volume": 730,
        "net_buy_exec_volume": 510,
        "buy_exec_single": 210,
        "sell_exec_single": 95,
        "buy_ratio_ws": 62.9,
        "exec_buy_ratio": 62.9,
        "micro_flow_desc": "단기 매수 체결 우위",
        "best_ask": 12580,
        "best_bid": 12570,
        "ask_tot": 184000,
        "bid_tot": 219000,
        "orderbook_imbalance": 0.84,
        "spread_tick": 1,
        "tape_bias": "매수 우위",
        "ask_absorption_status": "매도벽 소화 시도",
        "net_bid_depth": 12000,
        "bid_depth_ratio": 118.0,
        "net_ask_depth": -3500,
        "ask_depth_ratio": 94.0,
        "depth_flow_desc": "매수 잔량 개선",
        "program_flow_desc": "프로그램 절대 매수 우위",
        "vwap_price": 12490,
        "vwap_status": "상회",
        "open_position_desc": "시가 상회 (+2.01%)",
        "high_breakout_status": "고가 재도전 구간",
        "box_high": 12610,
        "box_low": 12420,
        "daily_setup_desc": "20일선 위 눌림 후 전고점 재도전",
        "ma5_status": "5일선 상회",
        "ma20_status": "20일선 상회",
        "ma60_status": "60일선 상회",
        "prev_high": 12650,
        "prev_low": 12120,
        "near_20d_high_pct": -0.8,
        "drawdown_from_high_pct": -1.1,
    }

    packet = engine._build_realtime_quant_packet("쏠리드", "050890", realtime_ctx, "SWING")

    assert "프로그램 절대 매수/매도" in packet
    assert "순간 체결대금/누적: 28,500 / 950,000" in packet
    assert "매수/매도 체결량: +1,240 / +730 (순매수 +510)" in packet
    assert "체결 매수비율(WS): 62.9% / 체결량 기준 62.9%" in packet
    assert "잔량 개선: 매수 +12,000 (118.0%) / 매도 -3,500 (94.0%)" in packet
    assert "수급 요약: 단기 매수 체결 우위 / 프로그램 절대 매수 우위" in packet
    assert "잔량 요약: 매수 잔량 개선" in packet


def test_gate_threshold_constants_reflect_first_tuning():
    assert TRADING_RULES.MAX_INTRADAY_SURGE == 16.0
    assert TRADING_RULES.MAX_SWING_GAP_UP_PCT_KOSPI == 3.5
    assert TRADING_RULES.MAX_SWING_GAP_UP_PCT_KOSDAQ == 3.0
