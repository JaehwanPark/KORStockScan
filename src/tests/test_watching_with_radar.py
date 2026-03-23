#!/usr/bin/env python3
"""
Test handle_watching_state with a mock radar object.
Show that with proper radar and AI score >= 75, the function may trigger BUY_ORDERED.
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

# Set up mock globals
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

# Create a mock radar class
class MockRadar:
    """Mock radar with minimal methods needed for handle_watching_state."""
    def get_smart_target_price(self, curr_price, v_pw, ai_score, ask_tot, bid_tot):
        # Return a target price slightly below current price (simulating drop target)
        target = int(curr_price * 0.995)
        drop_pct = 0.5
        return target, drop_pct
    
    def analyze_signal_integrated(self, ws_data, ai_prob):
        # Return a dummy analysis with high score
        score = 80
        prices = {'curr': ws_data.get('curr', 0)}
        conclusion = "BUY"
        checklist = []
        metrics = {'v_pw': ws_data.get('v_pw', 0)}
        return score, prices, conclusion, checklist, metrics

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
    
    # We'll test only the first record for demonstration
    if records:
        rec = records[0]
        print("\n" + "="*60)
        print(f"Testing stock: {rec.stock_name} ({rec.stock_code})")
        
        # Build stock dictionary with high AI score (>=75)
        stock = {
            'name': rec.stock_name,
            'strategy': rec.strategy,
            'position_tag': rec.position_tag,
            'buy_price': rec.buy_price,
            'prob': rec.prob,
            'rt_ai_prob': 0.80,  # Set to 80% to pass AI threshold
            'id': rec.id,
        }
        
        # Mock websocket data with favorable conditions
        curr_price = rec.buy_price if rec.buy_price and rec.buy_price > 0 else 10000
        ws_data = {
            'curr': curr_price,
            'v_pw': 130.0,          # good VPW
            'fluctuation': 0.5,
            'ask_tot': 1000000,
            'bid_tot': 1000000,
            'open': curr_price * 0.99,
            'orderbook': {},
        }
        
        admin_id = 7008158381  # use the admin ID from earlier logs
        radar = MockRadar()
        ai_engine = None  # no AI engine for simplicity
        
        print(f"  Using mock radar.")
        print(f"  AI score: {stock['rt_ai_prob']*100:.0f}")
        print(f"  Current price: {curr_price}")
        print(f"  VPW: {ws_data['v_pw']}")
        
        # Call handle_watching_state
        try:
            handle_watching_state(stock, rec.stock_code, ws_data, admin_id, radar, ai_engine)
            if stock.get('status') == 'BUY_ORDERED':
                print("  ✅ BUY_ORDERED triggered!")
                print(f"  Target buy price: {stock.get('target_buy_price')}")
            else:
                print(f"  ❌ No buy trigger. Status: {stock.get('status')}")
                # Check possible reasons
                if rec.stock_code in kiwoom_sniper_v2.cooldowns:
                    print(f"  Cooldown active until {kiwoom_sniper_v2.cooldowns[rec.stock_code]}")
                if rec.stock_code in kiwoom_sniper_v2.alerted_stocks:
                    print(f"  Already alerted.")
        except Exception as e:
            print(f"  🚨 Error in handle_watching_state: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No records to test.")
    
    session.close()
    print("\n" + "="*60)
    print("Test completed.")

if __name__ == '__main__':
    main()