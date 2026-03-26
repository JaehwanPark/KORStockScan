#!/usr/bin/env python3
"""
Test script to verify Kiwoom inventory API responses for different exchanges and query types.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import json
import time
import requests
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info

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

def test_exchange_qrytp_combinations(token):
    """Test API with exchanges KRX/NXT and qry_tp 1/2."""
    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'kt00018',  # same as get_my_inventory
    }
    
    exchanges = ['KRX', 'NXT']
    qry_tps = ['1', '2']
    
    for exchange in exchanges:
        for qry_tp in qry_tps:
            params = {'qry_tp': qry_tp, 'dmst_stex_tp': exchange}
            print(f"\n🔍 Testing exchange={exchange}, qry_tp={qry_tp}")
            try:
                response = requests.post(url, headers=headers, json=params, timeout=10)
                print(f"   HTTP status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    rt_cd = data.get('rt_cd', data.get('return_code', ''))
                    print(f"   Return code: {rt_cd}")
                    if str(rt_cd) == '0':
                        stock_list = data.get('acnt_evlt_remn_indv_tot', [])
                        print(f"   Number of items: {len(stock_list)}")
                        # Print first few items for inspection
                        for i, item in enumerate(stock_list[:3]):
                            code = item.get('stk_cd', '')
                            name = item.get('stk_nm', '')
                            qty = item.get('rmnd_qty', 0)
                            print(f"     {i+1}. {name}({code}) qty={qty}")
                        if len(stock_list) > 3:
                            print(f"     ... and {len(stock_list)-3} more items")
                    else:
                        err_msg = data.get('return_msg', data.get('err_msg', 'No error message'))
                        print(f"   Error: {err_msg}")
                else:
                    print(f"   Response text: {response.text[:200]}")
            except Exception as e:
                print(f"   Exception: {e}")
            time.sleep(0.5)  # avoid rate limiting

def main():
    print("🚀 Starting inventory API test")
    token = get_token()
    if not token:
        print("❌ Failed to obtain Kiwoom token. Exiting.")
        sys.exit(1)
    print(f"✅ Token obtained (first 10 chars): {token[:10]}...")
    
    test_exchange_qrytp_combinations(token)
    
    print("\n✅ Test completed.")

if __name__ == '__main__':
    main()