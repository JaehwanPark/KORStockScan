#!/usr/bin/env python3
"""
Test script to verify Kiwoom deposit API (orderable amount).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import json
import time
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.engine.kiwoom_orders import get_deposit

def get_token():
    """Load config and get Kiwoom token."""
    target = Path('data/config_prod.json') if Path('data/config_prod.json').exists() else Path('data/config_sample.json')
    try:
        with open(target, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        log_error(f"Config load failed: {e}")
        return None
    token = kiwoom_utils.get_kiwoom_token(config)
    return token

def test_deposit(token):
    """Test deposit API and print orderable amount."""
    print("\n🔍 Testing deposit (orderable amount) API")
    try:
        amount = get_deposit(token)
        print(f"   Orderable amount: {amount:,} KRW")
        if amount > 0:
            print("   ✅ Deposit retrieval successful")
        else:
            print("   ⚠️ Deposit amount is zero or API returned error")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False
    return True

def main():
    print("🚀 Starting deposit API test")
    token = get_token()
    if not token:
        print("❌ Failed to obtain Kiwoom token. Exiting.")
        sys.exit(1)
    print(f"✅ Token obtained (first 10 chars): {token[:10]}...")
    
    test_deposit(token)
    
    print("\n✅ Test completed.")

if __name__ == '__main__':
    main()