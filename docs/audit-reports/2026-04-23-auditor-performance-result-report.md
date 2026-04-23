# 2026-04-23 Auditor Performance Result Report

## 판정

- 종합 판정: `조건부 보류 유지`. 2026-04-23의 주병목은 여전히 `entry_armed -> submitted`이며, `entry_filter_quality` 착수/승격 축과 혼합할 수 없다.
- 주축 상태: `buy_recovery_canary`는 upstream 후보 생성용으로 유지, `score/promote` 및 AI A/B 본격 재개는 보류.
- `Spread relief canary`는 구현/배치되었으나 실증 신호는 미약하여 실시간 제출 회복으로 이어진 증거는 없음.
- Plan Rebase 준수: `main-only`, `일일 1축 canary`, `shadow 금지`, `remote 비교 제외`.

## 근거

- 지표 요약 (`performance_tuning_2026-04-23.json`, `saved_snapshot_at=2026-04-23 14:03:44`):
  - `candidates(스캘핑)=154`, `ai_confirmed=78`, `entry_armed=45`, `submitted=1`
  - `budget_pass_events=4373`, `order_bundle_submitted_events=3`, `budget_pass_to_submitted_rate=0.1%` (심각)
  - `latency_block_events=4370`, `quote_fresh_latency_blocks=4029`, `quote_fresh_latency_pass_rate=0.1%`
  - `reject_rate=99.7`, `ready=false`, `n_current=4373`, `primary_metric=budget_pass_to_submitted_rate`
  - `gatekeeper_decisions=33`, `gatekeeper_eval_ms_p95=22653ms`, `gatekeeper_lock_wait_ms_p95=0ms`, `gatekeeper_model_call_ms_p95=22653ms`, `gatekeeper_fast_reuse_ratio=0.0`
  - `full_fill_events=2`, `partial_fill_events=0`, `full_fill_completed_avg_profit_rate=-0.465`
  - `top_blocker=scalping: AI 점수(60.7%)`, `latest_blockers`에서 과열/지연 리스크도 동반
- 성능-성과 요약 (`trade_review_2026-04-23.json`, `saved_snapshot_at=2026-04-23 15:51:38`):
  - `total_trades=2`, `completed_trades=2`, `open_trades=0`, `win=1`, `loss=1`
  - `avg_profit_rate=-0.47`, `realized_pnl_krw=-10317`
  - `full_fill_events=2`, `partial_fill_events=0`
  - `holding_events=67`, `entered_rows=2`, `expired_rows=130`
- HOLDING 검토 (`post_sell_feedback_2026-04-23.json`, `saved_snapshot_at=2026-04-23 16:00:23`):
  - `missed_upside_rate=0.0`, `good_exit_rate=50.0`, `capture_efficiency_avg_pct=58.3`
  - 표본 2건, `estimated_extra_upside_10m_krw_sum=13118`으로 구조적 확대판단 부적합.
  - `soft_stop_forensics`에서 `soft_stop=1`만 존재, `rebound_above_sell_rate(10m)=100%`, `rebound_above_buy_rate(10m)=0%`.
- WAIT65~79 확장 후보(`/wait6579_ev_cohort_2026-04-23.json`, `saved_snapshot_at=2026-04-23 14:04:18`):
  - `total_candidates=307`, `entered_attempts=0`, `entered_rate=0.0`
  - `recovery_check=27`, `recovery_promoted=15`, `budget_pass=18`, `latency_pass=0`, `latency_block=18`, `submitted=0`
  - `submission_blocker=no_budget_pass 289 (94.1%)`, `latency_block 18 (5.9%)`
  - `terminal_blocker=blocked_ai_score 80.5%(247)`, `blocked_strength_momentum 12.1%(37)`, `latency_block 5.9%(18)`
  - `approval_gate: min_sample_gate_passed=false` (`full_samples=305`, `partial_samples=1`, `min_sample=20` 미달)
- 원격 대조:
  - `server_comparison_2026-04-23.md`의 remote API는 `remote_error`(timeout)로 모두 조회 실패, `excluded_from_criteria`.

## 분석(판정 중심)

- BUY 자체의 후보 생성은 완전히 사라진 상태가 아니다. 오히려 스캘핑에서 `ai_confirmed=78`, `entry_armed=45`로 상위 단계 후보는 존재한다.
- 그러나 `budget_pass_to_submitted=0.1%`가 구조적 병목이며, 제출단계에서 단절이 과도하다.
- `latency_block`가 예산통과 이후 대규모로 발생하고, `quote_fresh`의 통과율이 0.1%로 낮아 **제출 직전 quote freshness/latency 경로가 핵심 병목**이다.
- gatekeeper는 `p95=22,653ms`로 느려졌으나 `lock_wait=0`이고, `rejection` 다수를 설명하지 못할 만큼 표본은 `entry_armed -> submitted` downstream 병목이 더 크다.
- HOLDING/청산 계열은 거래 표본 2건으로 결과가 작고 변동성이 커 `확장/완화 판단을 바로 붙이는 건 근거가 약함`.
- remote 수치가 없음에도 판단은 로컬 `COMPLETED + valid profit_rate`, `full/partial 분리`, `병목 분해` 위주로 유지되므로 기준 위반 없음.

## 다음 액션

1. 장후 판정: `entry_filter_quality`는 오늘 기준 `미착수 유지`로 고정하고, 2026-04-24에서 동일 기준 재판정.
2. `AI A/B`는 2026-04-21 확정된 preflight 범위를 그대로 유지하고, `2026-04-24-stage2-todo-checklist.md`의 재판정 슬롯에서만 논의.
3. `score/promote`는 이번에는 보류 유지. 승인조건: `wait6579`에서 최소 샘플 통과 + `latency_block`/`submitted` 병목의 실제 완화 동반 시에 한해 재개 검토.
4. HOLDING·soft-stop·EOD/NXT·물타기 축은 표본 확대 전까지 `보류/내일 재판정`으로 유지.
5. 동일-day 운영 검증은 계속 `entry_armed -> submitted` 분해로 통일: 
   - `entry_armed -> submitted` 누수 추적 강화
   - `quote_fresh` 세분화(spread/ws_age/ws_jitter/quote_stale) + gatekeeper-model latency 분리
   - `no_budget_pass`와 `latency_block`의 순위 전환 여부를 장중/장후 누적 비교

## 검증 기록

- 파서 기반 산출물 사용 가능성: 세 스냅샷(performance_tuning/trade_review/wait6579/post_sell_feedback) 모두 유효 JSON 로드 및 지표 추출 가능.
- 문서 상관성: 2026-04-23 Stage2 POSTCLOSE 결정(특히 `entry_armed -> submitted` 제출병목 잠금, HOLDING·score/promote·entry_filter_quality 보류)과 일치.
