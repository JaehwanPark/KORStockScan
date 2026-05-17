# DeepSeek Swing Pattern Lab

Swing 전용 pattern analysis lab. 스윙 lifecycle 전 단계(selection → db_load → entry → holding → scale_in → exit → attribution)의 fact table을 생성하고, DeepSeek로 패턴/EV 개선 후보를 분석한다.

## 운영 원칙

- `report-only / proposal-only` — 모든 산출물은 `runtime_effect=false`, `allowed_runtime_apply=false`
- 스윙 live 주문, Gatekeeper, market regime hard block, gap/protection guard, budget/qty safety, threshold runtime 값은 변경하지 않음
- 새 threshold family는 `design_family_candidate`로만 제안
- OFI/QI 단독 BUY/EXIT hard gate 금지
- 기존 스캘핑 pattern lab 산출물과 섞지 않음
- sim/probe/dry-run 표본은 `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=probe_observe_only|sim_equal_weight` provenance를 포함

## Quick Start

```bash
# Run the full pipeline
bash analysis/deepseek_swing_pattern_lab/run_all.sh

# Or run each step individually
PYTHONPATH=. .venv/bin/python analysis/deepseek_swing_pattern_lab/prepare_dataset.py
PYTHONPATH=. .venv/bin/python analysis/deepseek_swing_pattern_lab/analyze_swing_patterns.py
PYTHONPATH=. .venv/bin/python analysis/deepseek_swing_pattern_lab/build_deepseek_payload.py
```

## Configuration

Set `ANALYSIS_START_DATE` and `ANALYSIS_END_DATE` environment variables to control the analysis window:

```bash
ANALYSIS_START_DATE=2026-05-01 ANALYSIS_END_DATE=2026-05-09 bash analysis/deepseek_swing_pattern_lab/run_all.sh
```

## Input Data

| Source | Path |
|--------|------|
| Lifecycle audit | `data/report/swing_lifecycle_audit/swing_lifecycle_audit_YYYY-MM-DD.json` |
| Selection funnel | `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.json` |
| Improvement automation | `data/report/swing_improvement_automation/swing_improvement_automation_YYYY-MM-DD.json` |
| Pipeline events | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` |
| Recommendations CSV | `data/daily_recommendations_v2.csv` |
| Recommendation DB | PostgreSQL `recommendation_history` table |

## Output Fact Tables

| File | Description |
|------|-------------|
| `swing_trade_fact.csv` | Trade-level records with buy/sell prices, profit rates, strategy, position tags |
| `swing_lifecycle_funnel_fact.csv` | Date-level funnel counts (selected, gated, submitted, simulated) |
| `swing_sequence_fact.csv` | Record-level lifecycle event sequences |
| `swing_ofi_qi_fact.csv` | OFI/QI micro context samples with stale/missing flags |

## Output Reports

| File | Description |
|------|-------------|
| `swing_pattern_analysis_result.json` | Structured findings and code improvement orders |
| `final_review_report_for_lead_ai.md` | Final review report for lead AI |
| `swing_ev_improvement_backlog_for_ops.md` | EV improvement backlog for operations |
| `data_quality_report.md` | Data quality metrics and warnings |
| `deepseek_payload_summary.json` | DeepSeek LLM payload summary |
| `deepseek_payload_cases.json` | DeepSeek LLM sample cases |
| `run_manifest.json` | Pipeline execution manifest |

## Metric Contract

- `schema_version=2`
- `metric_role=primary_ev`
- `primary_decision_metric=equal_weight_avg_profit_pct`
- `runtime_effect=false`
- `forbidden_uses`: threshold mutation, order guard mutation, provider change, bot restart, broker order submit

## Direction Map

```
Input Reports → prepare_dataset.py → Fact Tables (CSV)
                                          ↓
                              analyze_swing_patterns.py → Findings + Orders (JSON)
                                          ↓
                              build_deepseek_payload.py → DeepSeek Payload + Final Reports (JSON/MD)
```

## Postclose Automation 연결

DeepSeek swing lab은 postclose 체인에서 `swing_pattern_lab_automation` source로 연결되며, 결과는 code improvement workorder와 threshold-cycle EV의 report-only 입력으로만 사용한다.
