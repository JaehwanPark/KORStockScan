import os
import csv
import json
from collections import defaultdict
import config

def analyze_patterns():
    trade_fact_path = config.OUTPUT_DIR / 'trade_fact.csv'
    if not os.path.exists(trade_fact_path):
        print("trade_fact.csv not found")
        return

    # Read trades
    trades = []
    with open(trade_fact_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['profit_valid_flag'] == 'true':
                row['profit_rate'] = float(row['profit_rate'])
                trades.append(row)

    # Group by (exit_rule, entry_mode) as a proxy for "pattern"
    pattern_stats = defaultdict(lambda: {'count': 0, 'profits': [], 'total_profit': 0.0})
    
    for t in trades:
        pat_key = f"{t['entry_mode']}_{t['exit_rule']}"
        pattern_stats[pat_key]['count'] += 1
        pattern_stats[pat_key]['profits'].append(t['profit_rate'])
        pattern_stats[pat_key]['total_profit'] += t['profit_rate']

    patterns = []
    for k, v in pattern_stats.items():
        v['profits'].sort()
        count = v['count']
        avg_p = v['total_profit'] / count if count > 0 else 0
        mid_idx = count // 2
        med_p = v['profits'][mid_idx] if count > 0 else 0
        patterns.append({
            'pattern_name': k,
            'count': count,
            'avg_profit_rate': round(avg_p, 3),
            'median_profit_rate': round(med_p, 3),
            'total_contribution': round(v['total_profit'], 3)
        })

    # Sort by total_contribution
    patterns.sort(key=lambda x: x['total_contribution'], reverse=True)
    
    profit_patterns = [p for p in patterns if p['avg_profit_rate'] > 0][:5]
    loss_patterns = [p for p in reversed(patterns) if p['avg_profit_rate'] < 0][:5]

    # Save to outputs
    result = {
        'profit_patterns_top5': profit_patterns,
        'loss_patterns_top5': loss_patterns
    }

    with open(config.OUTPUT_DIR / 'pattern_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    print("Patterns analyzed and saved to pattern_stats.json")

if __name__ == '__main__':
    analyze_patterns()
