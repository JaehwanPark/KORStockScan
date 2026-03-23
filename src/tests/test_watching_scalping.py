#!/usr/bin/env python3
"""
Test handle_watching_state for SCALPING strategy.
Query DB for rec_date = '2026-03-23', status = 'WATCHING', strategy = 'SCALPING'.
Evaluate each condition that could cause exclusion.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime, time as dt_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import RecommendationHistory
from src.utils.constants import POSTGRES_URL

# Mock global variables used in kiwoom_sniper_v2
from src.engine import kiwoom_sniper_v2

# Set up mock globals (we'll need to adjust for time conditions)
kiwoom_sniper_v2.KIWOOM_TOKEN = None
kiwoom_sniper_v2.WS_MANAGER = None
kiwoom_sniper_v2.AI_ENGINE = None
kiwoom_sniper_v2.highest_prices = {}
kiwoom_sniper_v2.alerted_stocks = set()
kiwoom_sniper_v2.cooldowns = {}
kiwoom_sniper_v2.LAST_AI_CALL_TIMES = {}
kiwoom_sniper_v2.TIME_09_00 = dt_time(9, 0)
kiwoom_sniper_v2.TIME_09_03 = dt_time(9, 3)
kiwoom_sniper_v2.TIME_16_00 = dt_time(16, 0)

# Import the function after mocking globals
from src.engine.kiwoom_sniper_v2 import handle_watching_state

def evaluate_condition(stock, code, ws_data, admin_id, radar=None, ai_engine=None):
    """
    Evaluate conditions step by step, printing which condition fails.
    This is a manual simulation of the logic in handle_watching_state.
    """
    raw_strategy = (stock.get('strategy') or 'KOSPI_ML').upper()
    strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
    pos_tag = stock.get('position_tag', 'MIDDLE')
    
    now = datetime.now()
    now_t = now.time()
    
    # 1. Time condition
    if strategy == 'SCALPING':
        strategy_start = kiwoom_sniper_v2.TIME_09_00 if pos_tag == 'VCP_NEXT' else kiwoom_sniper_v2.TIME_09_03
    else:
        strategy_start = kiwoom_sniper_v2.TIME_09_05
    
    if now_t < strategy_start:
        print(f"  ⏰ Before strategy start time {strategy_start}. Exclude.")
        return False
    
    # 2. Cooldown check
    if code in kiwoom_sniper_v2.cooldowns and time.time() < kiwoom_sniper_v2.cooldowns[code]:
        print(f"  🕒 Cooldown active. Exclude.")
        return False
    
    # 3. SCALPING after 16:00
    if strategy == 'SCALPING' and now_t >= kiwoom_sniper_v2.TIME_16_00:
        print(f"  🚫 SCALPING after 16:00. Exclude.")
        return False
    
    # 4. Already alerted
    if code in kiwoom_sniper_v2.alerted_stocks:
        print(f"  🔔 Already alerted. Exclude.")
        return False
    
    # 5. Current price valid
    curr_price = int(float(ws_data.get('curr', 0) or 0))
    if curr_price <= 0:
        print(f"  💰 Invalid current price. Exclude.")
        return False
    
    # 6. For SCALPING, additional checks
    if strategy == 'SCALPING':
        # VCP_CANDID exclusion
        if pos_tag == 'VCP_CANDID':
            print(f"  🚫 VCP_CANDID position tag. Exclude.")
            return False
        
        current_vpw = float(ws_data.get('v_pw', 0) or 0)
        ask_tot = int(float(ws_data.get('ask_tot', 0) or 0))
        bid_tot = int(float(ws_data.get('bid_tot', 0) or 0))
        open_price = float(ws_data.get('open', curr_price) or curr_price)
        fluctuation = float(ws_data.get('fluctuation', 0.0) or 0.0)
        
        # Surge checks
        MAX_SURGE = 20.0  # default
        MAX_INTRADAY_SURGE = 15.0
        if fluctuation >= MAX_SURGE:
            print(f"  📈 Fluctuation {fluctuation} >= MAX_SURGE {MAX_SURGE}. Exclude.")
            return False
        intraday_surge = ((curr_price - open_price) / open_price) * 100 if open_price > 0 else fluctuation
        if intraday_surge >= MAX_INTRADAY_SURGE:
            print(f"  📈 Intraday surge {intraday_surge} >= MAX_INTRADAY_SURGE {MAX_INTRADAY_SURGE}. Exclude.")
            return False
        
        # Liquidity
        MIN_LIQUIDITY = 500_000_000
        liquidity_value = (ask_tot + bid_tot) * curr_price
        if liquidity_value < MIN_LIQUIDITY:
            print(f"  💧 Liquidity {liquidity_value} < MIN_LIQUIDITY {MIN_LIQUIDITY}. Exclude.")
            return False
        
        # VPW limit
        VPW_SCALP_LIMIT = 120
        if current_vpw < VPW_SCALP_LIMIT:
            print(f"  📉 VPW {current_vpw} < VPW_SCALP_LIMIT {VPW_SCALP_LIMIT}. Exclude.")
            return False
        
        # Gap check
        scanner_price = stock.get('buy_price') or 0
        if scanner_price > 0:
            gap_pct = (curr_price - scanner_price) / scanner_price * 100
            if gap_pct >= 1.5:
                print(f"  📊 Gap {gap_pct:.1f}% >= 1.5%. Exclude.")
                return False
        
        # AI score check (simplified)
        current_ai_score = float(stock.get('rt_ai_prob', 0.5) or 0.5) * 100
        if current_ai_score < 75 and current_ai_score != 50:
            print(f"  🤖 AI score {current_ai_score} < 75 and not 50. Exclude.")
            return False
        
        # Radar required
        if radar is None:
            print(f"  📡 Radar is None. Exclude.")
            return False
    
    # If all passed
    print(f"  ✅ All conditions passed.")
    return True

def main():
    target_date = '2026-03-23'
    
    engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"🔍 Querying SCALPING WATCHING records for date {target_date}...")
    records = session.query(RecommendationHistory).filter(
        RecommendationHistory.rec_date == target_date,
        RecommendationHistory.status == 'WATCHING',
        RecommendationHistory.strategy == 'SCALPING'
    ).all()
    
    print(f"📊 Found {len(records)} SCALPING WATCHING records.")
    
    for rec in records:
        print("\n" + "="*60)
        print(f"Stock: {rec.stock_name} ({rec.stock_code})")
        print(f"Position Tag: {rec.position_tag}")
        print(f"Prob: {rec.prob}")
        print(f"Buy Price (scanner): {rec.buy_price}")
        
        # Build stock dictionary
        stock = {
            'name': rec.stock_name,
            'strategy': rec.strategy,
            'position_tag': rec.position_tag,
            'buy_price': rec.buy_price,
            'prob': rec.prob,
            'rt_ai_prob': rec.prob if rec.prob else 0.5,
            'id': rec.id,
        }
        
        # Mock websocket data with typical values (adjust to test)
        # Let's assume some default values that may pass or fail
        curr_price = rec.buy_price if rec.buy_price and rec.buy_price > 0 else 10000
        ws_data = {
            'curr': curr_price,
            'v_pw': 130.0,  # good VPW
            'fluctuation': 0.5,
            'ask_tot': 100000,
            'bid_tot': 100000,
            'open': curr_price * 0.99,
            'orderbook': {},
        }
        
        admin_id = None  # no admin to prevent actual buy
        radar = None  # no radar for simplicity
        ai_engine = None
        
        print("Evaluating conditions:")
        passed = evaluate_condition(stock, rec.stock_code, ws_data, admin_id, radar, ai_engine)
        
        if passed:
            print("  Would proceed to handle_watching_state.")
            # Actually call the function to see if any other internal conditions fail
            try:
                handle_watching_state(stock, rec.stock_code, ws_data, admin_id, radar, ai_engine)
                if stock.get('status') == 'BUY_ORDERED':
                    print("  🛒 BUY_ORDERED triggered.")
                else:
                    print("  ❌ No buy trigger (maybe internal conditions).")
            except Exception as e:
                print(f"  🚨 Error in handle_watching_state: {e}")
        else:
            print("  ❌ Excluded by conditions.")
    
    session.close()
    print("\n" + "="*60)
    print("Test completed.")

if __name__ == '__main__':
    main()