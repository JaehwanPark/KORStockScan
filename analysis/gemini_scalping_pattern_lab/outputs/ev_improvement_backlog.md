# EV Improvement Backlog

1. latency guard miss EV 회수 조건 점검
   - 적용단계: report_only_observation
   - 기대효과: latency guard miss 구간에서 놓친 기대값 회수 가능성을 검증한다.
   - 검증지표: 차단건수=57022, 차단비율=99.9%
   - 필요표본: 장중/장후 snapshot 동시 확인

2. AI threshold miss EV 회수 조건 점검
   - 적용단계: canary_only_candidate_after_workorder
   - 기대효과: AI threshold miss 구간에서 놓친 기대값 회수 가능성을 검증한다.
   - 검증지표: 차단건수=51205, 차단비율=99.9%
   - 필요표본: 장중/장후 snapshot 동시 확인

3. WAIT65~79 -> submitted 단절 원인 점검
   - 적용단계: observability
   - 기대효과: EV가 남아 있는 recovery 후보가 실제 제출로 이어지지 않는 병목을 분리한다.
   - 검증지표: promoted=0, submitted=0
   - 필요표본: HOLDING 발생 이후 재관찰

4. gatekeeper latency 경로 분해(lock/model/quote_fresh)
   - 적용단계: observability
   - 기대효과: latency가 EV 회수 병목인지 성능 문제인지 구간별로 분해한다.
   - 검증지표: gatekeeper_eval_ms_p95=3431ms, quote_fresh_latency_blocks=2412
   - 필요표본: 장전/장후 snapshot 누적
