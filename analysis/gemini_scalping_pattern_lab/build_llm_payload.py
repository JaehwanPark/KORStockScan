import os
import json
import csv
import config

def build_llm_payload():
    # Load funnel facts
    funnel_facts = []
    if os.path.exists(config.OUTPUT_DIR / 'funnel_fact.csv'):
        with open(config.OUTPUT_DIR / 'funnel_fact.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            funnel_facts = list(reader)
            
    # Load pattern stats
    pattern_stats = {}
    if os.path.exists(config.OUTPUT_DIR / 'pattern_stats.json'):
        with open(config.OUTPUT_DIR / 'pattern_stats.json', 'r', encoding='utf-8') as f:
            pattern_stats = json.load(f)
            
    # Build summary
    summary_payload = {
        'analysis_period': {
            'start_date': config.START_DATE,
            'end_date': config.END_DATE
        },
        'funnel_summary': funnel_facts,
        'patterns': pattern_stats
    }
    
    with open(config.OUTPUT_DIR / 'llm_payload_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)
        
    # Build cases
    cases_payload = []
    if os.path.exists(config.OUTPUT_DIR / 'trade_fact.csv') and os.path.exists(config.OUTPUT_DIR / 'sequence_fact.csv'):
        # load sequences
        seq_map = {}
        with open(config.OUTPUT_DIR / 'sequence_fact.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                seq_map[row['trade_id']] = row
                
        # select a few top/bottom trades as cases
        with open(config.OUTPUT_DIR / 'trade_fact.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            trades = [row for row in reader if row['profit_valid_flag'] == 'true']
            
        for t in trades:
            t['profit_rate'] = float(t['profit_rate'])
        trades.sort(key=lambda x: x['profit_rate'])
        
        # Bottom 5, Top 5
        representative_trades = trades[:5] + trades[-5:]
        for t in representative_trades:
            case = t.copy()
            if t['trade_id'] in seq_map:
                case['sequence'] = seq_map[t['trade_id']]
            cases_payload.append(case)
            
    with open(config.OUTPUT_DIR / 'llm_payload_cases.json', 'w', encoding='utf-8') as f:
        json.dump(cases_payload, f, indent=2, ensure_ascii=False)
        
    print("LLM payload built successfully.")

if __name__ == '__main__':
    build_llm_payload()
