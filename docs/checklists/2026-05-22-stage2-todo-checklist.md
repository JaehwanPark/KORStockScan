# 2026-05-22 Stage2 To-Do Checklist

## 오늘 목적

- Bedrock Nova Lite v1 shadow 결과를 OpenAI `gpt-5.4-mini` Tier2 호출 지점별로 비교해 정식 승격 후보 여부를 판단한다.
- Nova Lite v1 승격 판단과 별개로, Lite v2 shadow 시행 준비 여부를 닫는다.
- Micro 승격 판단은 `2026-05-21` 장후 checklist가 소유하고, `2026-05-22`에는 미완료 follow-up이 명시적으로 이관된 경우에만 다시 본다.
- latency/cost/token/cache 절감과 parse/schema 품질을 성과 판단에서 분리해 본다.
- `sim_record_id` exact join 기반 outcome-linked performance를 우선하고, 근접 매칭이나 instrumentation 이전 unmatched 표본은 source-quality gap으로만 기록한다.
- 승격 후보가 있더라도 당일 장중 provider route 변경은 금지하고, 별도 approval/workorder와 다음 PREOPEN 적용 후보로만 연결한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 스캘핑 AI route는 OpenAI 고정으로 시작한다. Bedrock shadow 결과는 장후 판단 입력이며, 장중 provider route, threshold, 주문 판단, bot restart trigger로 직접 쓰지 않는다.
- Bedrock/Nova 비교는 `decision_authority=shadow_observation_only`, `runtime_effect=false`, `broker_order_forbidden=true`, `actual_order_submitted=false` 계약을 유지한다.
- `mini` 우회 승격 검토는 `gpt-5.4-mini` Tier2 호출 지점별로 분리한다. `holding_flow`, `entry_price`, 기타 Tier2 endpoint를 합산해 단일 결론으로 닫지 않는다.
- Lite v2 shadow는 Lite v1 정식 승격 판단과 분리한다. v2 시행은 report-only 실험 설계/토글/산출물 계약만 열고, v1 또는 v2 provider route 변경으로 직접 이어지지 않는다.
- 손익은 `COMPLETED + valid profit_rate` 또는 scalp sim post-sell의 numeric `profit_rate`만 사용하고, exact `sim_record_id` join이 없는 표본은 성과 우열 근거에서 제외한다.
- 승격 결론은 `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫는다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장후 체크리스트

- [ ] `[BedrockNovaLiteTier2PromotionReview0522] gpt-5.4-mini Tier2 호출 지점의 Nova Lite v1 정식 승격 여부 판단` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: AITransport`)
  - Source: [bedrock_nova_lite_shadow_report_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_2026-05-22.json), [bedrock_nova_lite_shadow_report_2026-05-22.md](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_2026-05-22.md), [bedrock_nova_lite_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_2026-05-22.jsonl), [bedrock_nova_lite_shadow.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_lite_shadow.py), [bedrock_nova_lite_shadow_report.py](/home/ubuntu/KORStockScan/src/tests/bedrock_nova_lite_shadow_report.py)
  - owner/status: `bedrock_nova_lite_shadow_observation`, `report_only`, `runtime_effect=false`, `decision_authority=shadow_observation_only`
  - 판정 기준: `gpt-5.4-mini` Tier2 JSON 호출 지점만 대상으로 Nova Lite v1 shadow row를 집계한다. `holding_flow`, `entry_price`, 기타 Tier2 endpoint를 분리하고, latency p50/p90/p95, cache 포함 cost ratio, action agreement, score_delta, parse/schema quality, exact `sim_record_id` outcome-linked performance를 확인한다.
  - 표본 기준: Tier2 호출은 Tier1보다 빈도가 낮으므로 endpoint별 exact outcome match가 부족하면 hard pass/fail 금지다. `holding_flow`는 청산 후보 재판정 품질을 primary로 보고, `entry_price`는 가격/주문 안전성 때문에 parse/schema와 latency tail을 먼저 본다.
  - 금지: 장중 provider route 변경, `gpt-5.4-mini` 즉시 대체, entry price/order guard 변경, threshold 변경, bot restart trigger, 튜닝체인 자동 apply 연결 금지. 승격 후보가 나오면 별도 approval/workorder와 rollback guard를 만든 뒤 다음 PREOPEN 후보로만 넘긴다.
  - 다음 액션: `promote_candidate_requires_approval`, `keep_shadow_collecting`, `reject_provider_bypass`, `defer_source_quality_gap` 중 하나로 닫고, 승격 후보일 경우 `target_endpoint`, `baseline cohort`, `candidate provider cohort`, `observe-only cohort`, `excluded cohort`, `rollback owner`, `cross-contamination check`를 기록한다.

- [ ] `[BedrockNovaLiteV2ShadowImplementation0522] Nova Lite v1 대비 Lite v2 shadow 시행 준비 및 실행 여부 판단` (`Due: 2026-05-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:45`, `Track: AITransport`)
  - Source: [bedrock_nova_lite_shadow_report_2026-05-22.json](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_report_2026-05-22.json), [bedrock_nova_lite_shadow_2026-05-22.jsonl](/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_2026-05-22.jsonl), AWS Bedrock Nova Lite v2 model availability/region/cost documentation, [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - owner/status: `bedrock_nova_lite_v2_shadow_observation`, `report_only`, `runtime_effect=false`, `decision_authority=shadow_observation_only`
  - 판정 기준: Lite v1 승격 판단과 별개로, Lite v2가 `gpt-5.4-mini` Tier2 JSON 호출 크기와 `holding_flow`/`entry_price` 응답 계약을 감당할 수 있는지 확인한다. 가능하면 v1과 동일 row schema에 `candidate_model_family=lite_v2`, `baseline_bedrock_model_id=apac.amazon.nova-lite-v1:0`, `candidate_bedrock_model_id`, `v1_v2_action_match`, `v1_v2_score_delta`, `v2_parse_ok`, `v2_latency_ms`, `v2_estimated_cost_usd`를 추가하는 report-only shadow 설계를 준비한다.
  - 시행 조건: 한국 리전 또는 운영 Bedrock profile에서 Lite v2 model id가 호출 가능하고, 비용 단가/env 토글/timeout/queue/caching 설정이 v1과 분리되어야 한다. v2 model id 또는 리전 가용성이 불명확하면 `defer_source_quality_gap`으로 닫고 v1 shadow 수집은 유지한다.
  - 금지: Lite v2 shadow를 Lite v1 정식 승격 근거와 혼합 금지, 장중 provider route 변경 금지, `gpt-5.4-mini` 즉시 대체 금지, entry price/order guard 변경 금지, threshold 변경 금지, bot restart trigger 금지, 튜닝체인 자동 apply 연결 금지.
  - 다음 액션: `start_lite_v2_shadow_report_only`, `keep_lite_v1_only`, `defer_region_or_model_gap`, `reject_lite_v2_shadow` 중 하나로 닫고, 시행 시 `target_endpoint`, `model_id`, `region/profile`, `env toggle`, `artifact path`, `sample floor`, `rollback/off switch`를 기록한다.
