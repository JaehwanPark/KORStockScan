# 2026-05-22 Stage2 To-Do Checklist

## 오늘 목적

- Bedrock Nova Micro shadow 결과를 OpenAI `gpt-5-nano` 호출 지점별로 비교해 provider 우회 승격 가능성을 판단한다.
- 판단 대상은 `gpt-5-nano` Tier1 fast 호출 중 shadow가 수집된 entry/watch 및 scalp sim holding/exit 구간으로 한정한다.
- latency/cost/token/cache 절감과 parse/schema 품질을 성과 판단에서 분리해 본다.
- `sim_record_id` exact join 기반 outcome-linked performance를 우선하고, 근접 매칭이나 instrumentation 이전 unmatched 표본은 source-quality gap으로만 기록한다.
- 승격 후보가 있더라도 당일 장중 provider route 변경은 금지하고, 별도 approval/workorder와 다음 PREOPEN 적용 후보로만 연결한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 스캘핑 AI route는 OpenAI 고정으로 시작한다. Bedrock shadow 결과는 장후 판단 입력이며, 장중 provider route, threshold, 주문 판단, bot restart trigger로 직접 쓰지 않는다.
- Bedrock/Nova 비교는 `decision_authority=shadow_observation_only`, `runtime_effect=false`, `broker_order_forbidden=true`, `actual_order_submitted=false` 계약을 유지한다.
- `nano` 우회 승격 검토는 `gpt-5-nano` 호출 지점별로 분리한다. entry/watch, holding/exit, 기타 unknown/no-stage를 합산해 단일 결론으로 닫지 않는다.
- 손익은 `COMPLETED + valid profit_rate` 또는 scalp sim post-sell의 numeric `profit_rate`만 사용하고, exact `sim_record_id` join이 없는 표본은 성과 우열 근거에서 제외한다.
- 승격 결론은 `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫는다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장후 체크리스트

- [ ] `[BedrockNovaMicroBypassPromotionReview0522] OpenAI nano 호출 지점의 Bedrock Nova Micro 우회 정식 승격 여부 판단` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:05`, `Track: AITransport`)
  - Source: [bedrock_nova_micro_shadow_report_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_report_2026-05-22.json), [bedrock_nova_micro_shadow_report_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_report_2026-05-22.md), [bedrock_nova_micro_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl), [sim_post_sell_candidates_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `outcome_linked_performance`의 exact `sim_record_id` matched sample을 primary로 보고, `entry/watch`, `scalp_sim_holding_review`, `unknown/no-stage`를 분리한다. `nova_minus_openai_outcome_score`, `nova_edge_count/openai_edge_count/tie_count`, stage별 `avg_profit_rate`, action confusion, parse_ok_rate, cache 포함 cost ratio, p50/p90/p95 latency를 함께 확인한다.
  - 표본 기준: exact outcome match가 부족하거나 stage별 표본이 한쪽에 쏠리면 `defer_source_quality_gap` 또는 `keep_shadow_collecting`으로 닫는다. unmatched row, 근접 시간 매칭, instrumentation 이전 row는 승격 근거가 아니라 join-quality 보완 근거로만 쓴다.
  - 승격 가능 조건: Nova가 해당 stage에서 latency/cost 우위뿐 아니라 outcome-linked score에서 OpenAI 대비 명확한 우위 또는 동등 성과를 보여야 하며, parse/schema 실패율과 action normalization 문제가 없어야 한다. entry/watch와 holding/exit는 각각 별도 후보로 판단하고 한쪽 우위가 다른 쪽 provider route 변경 근거가 되지 않는다.
  - 금지: 장중 provider route 변경, threshold 변경, 주문 판단 변경, real order enable, bot restart trigger, OpenAI route 즉시 대체, 튜닝체인 자동 apply 연결 금지. 승격 후보가 나오면 별도 approval/workorder와 rollback guard를 만든 뒤 다음 PREOPEN 후보로만 넘긴다.
  - 다음 액션: `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫고, 승격 후보일 경우 `target_stage`, `baseline cohort`, `candidate provider cohort`, `observe-only cohort`, `excluded cohort`, `rollback owner`, `cross-contamination check`를 함께 기록한다.
