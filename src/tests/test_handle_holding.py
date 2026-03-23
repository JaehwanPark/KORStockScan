#!/usr/bin/env python3
"""
Test script for handle_holding_state logic.
Queries HOLDING records for rec_date = '2026-03-23' and applies the function
with mock websocket data to see what decisions are made.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime, date
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.engine.kiwoom_sniper_v2 import handle_holding_state
from src.utils.constants import TRADING_RULES

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

def main():
    target_date = '2026-03-23'
    db = DBManager()
    
    print(f"🔍 Querying HOLDING records for date {target_date}...")
    with db.get_session() as session:
        records = session.query(RecommendationHistory).filter(
            RecommendationHistory.rec_date == target_date,
            RecommendationHistory.status == 'HOLDING'
        ).all()
    
    print(f"📊 Found {len(records)} HOLDING records.")
    
    for rec in records:
        print("\n" + "="*60)
        print(f"Stock: {rec.stock_name} ({rec.stock_code})")
        print(f"Strategy: {rec.strategy}, Position Tag: {rec.position_tag}")
        print(f"Buy Price: {rec.buy_price}, Buy Qty: {rec.buy_qty}")
        
        # Build stock dictionary as expected by handle_holding_state
        stock = {
            'name': rec.stock_name,
            'strategy': rec.strategy,
            'position_tag': rec.position_tag,
            'buy_price': rec.buy_price,
            'buy_qty': rec.buy_qty,
            'buy_time': rec.buy_time,
            'order_time': None,  # assuming not available
            'rt_ai_prob': rec.prob if rec.prob else 0.5,
            'last_ai_profit': 0.0,
            'id': rec.id,
        }
        
        # Mock websocket data: simulate current price with a slight profit
        # Let's set current price = buy_price * 1.01 (1% profit)
        buy_price = rec.buy_price if rec.buy_price and rec.buy_price > 0 else 10000
        curr_price = int(buy_price * 1.01)
        ws_data = {
            'curr': curr_price,
            'orderbook': {},  # empty orderbook for simplicity
        }
        
        # Mock admin_id (None to prevent actual sell order)
        admin_id = None
        market_regime = 'BULL'  # assume bull market
        radar = None
        ai_engine = None
        
        # Call handle_holding_state
        print(f"  Current price: {curr_price}, Buy price: {buy_price}")
        print(f"  Profit rate: {(curr_price - buy_price) / buy_price * 100:.2f}%")
        try:
            handle_holding_state(stock, rec.stock_code, ws_data, admin_id, market_regime, radar, ai_engine)
        except Exception as e:
            print(f"  ❌ Error in handle_holding_state: {e}")
            import traceback
            traceback.print_exc()
        
        # Check if stock dict was modified (sell signal)
        if stock.get('status') == 'SELL_ORDERED':
            print("  🎯 SELL SIGNAL TRIGGERED")
        elif stock.get('status') == 'HOLDING':
            print("  🔄 Still HOLDING")
        # Check highest_prices tracking
        if rec.stock_code in kiwoom_sniper_v2.highest_prices:
            print(f"  📈 Highest price tracked: {kiwoom_sniper_v2.highest_prices[rec.stock_code]}")
    
    print("\n" + "="*60)
    print("Test completed.")

if __name__ == '__main__':
    main()