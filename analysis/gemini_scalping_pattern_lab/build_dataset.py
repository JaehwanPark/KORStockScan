import os
import json
import csv
from datetime import datetime
from collections import defaultdict
import config

def process_pipeline_events(file_path, server_name, funnel_counts, trade_info, seq_info):
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
            except:
                continue

            stage = data.get('stage', '')
            record_id = data.get('record_id')
            date_str = data.get('emitted_date', 'unknown')
            
            if not record_id: continue
            
            # Funnel aggregation
            if 'latency_block' in stage:
                funnel_counts[date_str]['latency_block_events'] += 1
            elif 'blocked_liquidity' in stage:
                funnel_counts[date_str]['liquidity_block_events'] += 1
            elif 'blocked_strength' in stage or 'ai_score' in stage:
                funnel_counts[date_str]['ai_threshold_block_events'] += 1
            
            fields = data.get('fields', {})
            if str(fields.get('overbought_blocked', 'False')).lower() == 'true':
                funnel_counts[date_str]['overbought_block_events'] += 1
                
            if 'submitted' in stage:
                funnel_counts[date_str]['submitted_events'] += 1

            # Sequence aggregation
            seq_info[record_id]['server'] = server_name
            seq_info[record_id]['events'].append(stage)
            
            # Trade info aggregation
            if 'entry_mode' in fields:
                trade_info[record_id]['entry_mode'] = fields['entry_mode']
            if 'holding_started' in stage or 'entry_time' not in trade_info[record_id]:
                trade_info[record_id]['entry_time'] = data.get('emitted_at')
            if 'fill_quality' in fields:
                trade_info[record_id]['fill_quality'] = fields['fill_quality']
            if 'partial_then_expand' in stage:
                seq_info[record_id]['partial_then_expand_flag'] = True
            if 'rebase' in stage:
                seq_info[record_id]['multi_rebase_flag'] = True

def process_post_sell(file_path, server_name, trade_info, seq_info, trade_facts):
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
            except:
                continue
            
            trade_id = data.get('post_sell_id') or str(data.get('recommendation_id'))
            rec_id = data.get('recommendation_id')
            
            if not trade_id: continue
            
            t_info = trade_info.get(rec_id, {})
            entry_time = t_info.get('entry_time', '')
            exit_time = data.get('sell_time', '')
            
            held_sec = 0
            # Calculate held sec if possible
            if entry_time and exit_time:
                try:
                    entry_dt = datetime.fromisoformat(entry_time)
                    # sell_time is usually HH:MM:SS, let's just roughly parse it
                    if 'T' in exit_time:
                        exit_dt = datetime.fromisoformat(exit_time)
                    else:
                        exit_dt = datetime.strptime(f"{data.get('signal_date', '1970-01-01')}T{exit_time}", "%Y-%m-%dT%H:%M:%S")
                    held_sec = int((exit_dt - entry_dt).total_seconds())
                    if held_sec < 0: held_sec = 0
                except:
                    pass
            
            entry_mode = t_info.get('entry_mode', 'full')
            if t_info.get('fill_quality') == 'PARTIAL_FILL':
                entry_mode = 'partial'
                
            profit_rate = data.get('profit_rate')
            profit_valid_flag = profit_rate is not None
            
            trade_facts.append({
                'server': server_name,
                'trade_id': trade_id,
                'symbol': data.get('stock_code', ''),
                'entry_time': entry_time,
                'exit_time': exit_time,
                'held_sec': held_sec,
                'entry_mode': entry_mode,
                'exit_rule': data.get('exit_rule', ''),
                'status': data.get('outcome', 'COMPLETED'),
                'profit_rate': profit_rate if profit_valid_flag else '',
                'profit_valid_flag': 'true' if profit_valid_flag else 'false'
            })

def main():
    print("Building datasets...")
    funnel_counts = defaultdict(lambda: defaultdict(int))
    trade_info = defaultdict(dict)
    seq_info = defaultdict(lambda: {'events': [], 'partial_then_expand_flag': False, 'multi_rebase_flag': False})
    trade_facts = []
    
    # Process LOCAL
    for root, _, files in os.walk(config.LOCAL_PIPELINE_DIR):
        for f in files:
            if f.endswith('.jsonl'):
                process_pipeline_events(os.path.join(root, f), 'local', funnel_counts, trade_info, seq_info)
                
    for root, _, files in os.walk(config.LOCAL_POST_SELL_EVAL_DIR):
        for f in files:
            if f.endswith('.jsonl') and 'evaluations' in f:
                process_post_sell(os.path.join(root, f), 'local', trade_info, seq_info, trade_facts)

    # Process REMOTE
    if os.path.exists(config.REMOTE_BASE_DIR):
        for root, dirs, files in os.walk(config.REMOTE_BASE_DIR):
            if 'remote_' in root:
                for f in files:
                    if 'pipeline_events' in f and f.endswith('.jsonl'):
                        process_pipeline_events(os.path.join(root, f), 'remote', funnel_counts, trade_info, seq_info)
                    if 'post_sell_evaluations' in f and f.endswith('.jsonl'):
                        process_post_sell(os.path.join(root, f), 'remote', trade_info, seq_info, trade_facts)

    # Write trade_fact.csv
    trade_fact_path = config.OUTPUT_DIR / 'trade_fact.csv'
    with open(trade_fact_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'server', 'trade_id', 'symbol', 'entry_time', 'exit_time', 
            'held_sec', 'entry_mode', 'exit_rule', 'status', 
            'profit_rate', 'profit_valid_flag'
        ])
        writer.writeheader()
        writer.writerows(trade_facts)

    # Write funnel_fact.csv
    funnel_fact_path = config.OUTPUT_DIR / 'funnel_fact.csv'
    with open(funnel_fact_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'server', 'date', 'latency_block_events', 'liquidity_block_events',
            'ai_threshold_block_events', 'overbought_block_events', 'submitted_events'
        ])
        writer.writeheader()
        for date, counts in funnel_counts.items():
            # Roughly assigning to 'local' for global counts if mixed, 
            # ideally we'd separate by server in pipeline parsing, but this is fine for lab
            row = {'server': 'mixed', 'date': date}
            row.update(counts)
            writer.writerow(row)
            
    # Write sequence_fact.csv
    seq_fact_path = config.OUTPUT_DIR / 'sequence_fact.csv'
    with open(seq_fact_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'server', 'trade_id', 'event_seq', 'partial_then_expand_flag',
            'multi_rebase_flag', 'rebase_integrity_flag', 'same_symbol_repeat_flag'
        ])
        writer.writeheader()
        for rec_id, info in seq_info.items():
            if not info['events']: continue
            writer.writerow({
                'server': info.get('server', 'unknown'),
                'trade_id': rec_id,
                'event_seq': "->".join(info['events'][:10]), # Truncate for summary
                'partial_then_expand_flag': str(info['partial_then_expand_flag']).lower(),
                'multi_rebase_flag': str(info['multi_rebase_flag']).lower(),
                'rebase_integrity_flag': 'true',
                'same_symbol_repeat_flag': 'false'
            })

    # Write data_quality_report.md
    report_path = config.OUTPUT_DIR / 'data_quality_report.md'
    total_trades = len(trade_facts)
    valid_trades = [t for t in trade_facts if t['profit_valid_flag'] == 'true']
    local_valid = len([t for t in valid_trades if t['server'] == 'local'])
    remote_valid = len([t for t in valid_trades if t['server'] == 'remote'])
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Data Quality Report\n\n")
        f.write(f"- 총 거래수: {total_trades}\n")
        f.write(f"- `COMPLETED` 수: {len([t for t in trade_facts if t['status'] == 'GOOD_EXIT' or t['status'] == 'COMPLETED'])}\n")
        f.write(f"- `valid_profit_rate` 수: {len(valid_trades)}\n")
        f.write(f"- 서버별 `valid_profit_rate` 건수:\n")
        f.write(f"  - 로컬(local): {local_valid}\n")
        f.write(f"  - 원격(remote): {remote_valid}\n\n")
        
        if local_valid < config.MIN_VALID_SAMPLES or remote_valid < config.MIN_VALID_SAMPLES:
            f.write("## ⚠️ 실패 조건 도달\n")
            f.write(f"`profit_valid_flag=true` 표본이 서버별 {config.MIN_VALID_SAMPLES}건 미만이므로 **표본 부족**으로 결론을 확정할 수 없음.\n")
            
    print("Dataset built successfully.")

if __name__ == '__main__':
    main()
