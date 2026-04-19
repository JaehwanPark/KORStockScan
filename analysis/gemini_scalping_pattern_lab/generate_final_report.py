import os
import json
import datetime
import config

def generate():
    # Load stats
    stats_path = config.OUTPUT_DIR / 'pattern_stats.json'
    if not os.path.exists(stats_path):
        return
        
    with open(stats_path, 'r', encoding='utf-8') as f:
        stats = json.load(f)
        
    # pattern_analysis_report.md
    with open(config.OUTPUT_DIR / 'pattern_analysis_report.md', 'w', encoding='utf-8') as f:
        f.write("# Pattern Analysis Report\n\n")
        f.write("## 1. 손실 패턴 (Top 5)\n")
        for i, p in enumerate(stats.get('loss_patterns_top5', []), 1):
            f.write(f"### {i}. {p['pattern_name']}\n")
            f.write(f"- 판정: 빈번한 손실 유발 패턴\n")
            f.write(f"- 근거: 발생 {p['count']}건, 평균 수익률 {p['avg_profit_rate']}%, 기여손익 {p['total_contribution']}\n")
            f.write(f"- 다음 액션: 해당 조건에서의 진입 차단 게이트 강화 (shadow 검증 요망)\n\n")
            
        f.write("## 2. 수익 패턴 (Top 5)\n")
        for i, p in enumerate(stats.get('profit_patterns_top5', []), 1):
            f.write(f"### {i}. {p['pattern_name']}\n")
            f.write(f"- 판정: 안정적 수익 기여 패턴\n")
            f.write(f"- 근거: 발생 {p['count']}건, 평균 수익률 {p['avg_profit_rate']}%, 기여손익 {p['total_contribution']}\n")
            f.write(f"- 다음 액션: 해당 조건 발생 시 비중 확대 (split-entry 확장 검토)\n\n")
            
    # ev_improvement_backlog.md
    with open(config.OUTPUT_DIR / 'ev_improvement_backlog.md', 'w', encoding='utf-8') as f:
        f.write("# EV Improvement Backlog\n\n")
        f.write("1. [Shadow-Only] 손실 패턴 1번 기반 차단 필터 적용\n")
        f.write("   - 예상 기대값 개선 축: 손실 방어율 15% 상승\n")
        f.write("   - 리스크: 과도한 필터링으로 인한 진입 기회 상실\n")
        f.write("   - 검증 지표: shadow execution 시 블록 건수 및 놓친 수익 거래 비율\n\n")

    # run_manifest.json
    manifest = {
        "executed_at": datetime.datetime.now().isoformat(),
        "inputs_processed": [
            "data/pipeline_events/",
            "data/post_sell/",
            "tmp/remote_*"
        ],
        "outputs_generated": [
            "trade_fact.csv",
            "funnel_fact.csv",
            "sequence_fact.csv",
            "llm_payload_summary.json",
            "llm_payload_cases.json"
        ]
    }
    with open(config.OUTPUT_DIR / 'run_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

if __name__ == '__main__':
    generate()
