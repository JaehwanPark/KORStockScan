# 9/14 implement-now·위젯·episode 2-pass 구현 리뷰

기준 시각: `2026-09-15 00:51 KST`

대상 source generation: `2026-09-14-866f4c946f73`

권한: source/report/schema/instrumentation과 기존 자동 handoff 검증. 과거 raw 합성, 주문·수량·target·threshold·provider·bot·hard-safety 변경 없음.

## 1. Intake와 Pass 1 판정

- 전수73행: 구현 요청14, 비구현59, 미분류0.
- 구현 요청14행은 모두 main owner다. 계약이 완전한11행은 현재 선택 release에 이미 구현된 producer/consumer를 검증해 `already_implemented_verified`로 닫는다.
- Pattern Lab3행은 구현 위치·직접 consumer·acceptance가 완전하지 않아 기존 `blocked_missing_evidence`를 유지한다. native ID를 추정하거나 generic AI follow-up을 새 코드로 만들지 않는다.
- widget collector6행은 `research_watch`, widget symbol4행은 `holdout_failed_no_widget_runtime_promotion`, machine lifecycle1행은 `EVIDENCE_ACCUMULATING`이다. 원문 결정을 implement-now로 바꾸지 않는다.
- low-price episode는 source-only 사용자 검토 후보4행과 decision 결손1행이다. 아래 §3의 비용후 경제성·회전 검토에 따라 이번 pass에서 runtime policy로 구현하지 않는다.

## 2. 이미 구현된 main11행 직접 검증

| Native ID | 구현·consumer 근거 | Pass 1 판정 |
| --- | --- | --- |
| `order_entry_submit_drought_auto_resolution` | `buy_funnel_sentinel` exact attempt/cycle 계약이 drought handoff, workorder, EV/runtime summary와 strict verifier까지 보존된다. source-quality 차단과 실제 submit 회복은 별도다. | `already_implemented_verified` |
| `order_observation_source_quality_unknown_token_provenance_gap` | audit는 reviewed provenance와 신규/uncontracted UNKNOWN을 분리하고 후자를 warning/workorder로 보존한다. 9/14 unknown41은 과거 raw 결손으로 유지하며 다음 exact date에서 producer field를 확인한다. | `already_implemented_verified` |
| `order_pipeline_event_compaction_v2_shadow` | raw를 보존한 bounded producer-summary compaction, report-only 권한과 verbosity consumer가 구현돼 있다. `shadow`는 trading shadow가 아니다. | `already_implemented_verified` |
| `order_scanner_eligible_no_heavy_closed_loop` | promotion lineage별 fast-precheck/heavy/eviction/right-censor terminal 귀속과 결손 상태가 monitor/acceptance에 구현돼 있다. | `already_implemented_verified` |
| `order_scanner_scan_generation_conservation_gap` | generation별 ranked/terminal/duplicate/conflict conservation과 incomplete generation 격리가 구현돼 있다. | `already_implemented_verified` |
| `order_ws_decision_stage_stale_backoff_attribution` | decision-stage stale reason, repair-cycle state, queue/eviction causal attribution을 별도 분모로 보존한다. | `already_implemented_verified` |
| `order_ws_subscription_stale_repair_observability` | subscription snapshot이 no-tick/required-type-missing/stale/fresh, route와 bounded repair recommendation을 구분한다. 주문·threshold 권한은 없다. | `already_implemented_verified` |
| `order_ws_total_stale_escalation` | 양쪽 stale과 repair-required/not-required/not-observed receipt를 분리하고 미관측을 성공으로 보간하지 않는다. | `already_implemented_verified` |
| `order_microstructure_v3_evaluation_venue_missing_or_conflicting` | micro attribution이 evaluation venue/session 결손·충돌을 행 단위 source defect로 격리하고 workorder로 전달한다. | `already_implemented_verified` |
| `order_scanner_funnel_executable_bbo_join` | bounded observer episode, fresh executable BBO, venue/session, 비용, target/adverse/timeout first-hit과 receipt accounting을 보존한다. 전체 prune 모집단으로 EV를 외삽하지 않는다. | `already_implemented_verified` |
| `order_ws_trade_tick_quiet_low_liquidity_classification` | fresh non-trade WS와 stale/missing 0B를 subscription stale과 분리하고 cumulative-volume provenance 결손을 명시한다. | `already_implemented_verified` |

9/14 자연 report에 남은 missing/unknown/not-observed는 구현 부재로 덮지 않는다. 해당 source는 당시 장중 PID가 생성했으며 현재 선택 release의 구현 검증과 다음 날짜 자연 소비는 별도 acceptance다.

## 3. 위젯·episode 추천 검토

- widget collector6행은 모두 `research_watch`다. source 수집을 계속하되 종목 확대·실전 신호 변경 코드를 생성하지 않는다.
- widget symbol4행은 모두 독립 holdout 실패다. rejected를 구현하면 same-stage 경제 gate를 우회하므로 그대로 둔다.
- `machine_lifecycle_turnover_policy_research_v1`은 `EVIDENCE_ACCUMULATING`이다. 현재 구현된 rolling paired 연구를 유지하고 표본을 만들기 위한 target/timeout/cooldown 변경은 하지 않는다.
- low-price four-row review:
  - LX세미콘 morning `+4 ticks`: 비용후 EV `0.211979%`, incumbent 대비 `+0.183025%p`지만 동일3 episode/6 leg에서 자본점유가 completed bar `24 -> 139`로 증가한다. 작은 수익의 빈번한 회전 목적에 반하고 source-only4 completed leg뿐이므로 runtime 적용을 보류한다.
  - 두산에너빌리티 midday `0.001616%`, 영원무역 late-morning `0.031581%`는 비용후 `+0.10%`에 미달한다.
  - SK이터닉스 morning `0.265946%`는 양수지만 incumbent보다 `-0.277001%p` 낮다.
- 따라서 네 행의 원래 `source_only_requires_review_and_user_approval` disposition은 `deferred`를 유지한다. 이는 후보 누락이 아니라 비용후 EV와 회전 목표를 적용한 명시적 비선정이다. decision 없는1행은 implementation contract가 없어 `blocked_missing_evidence_nonrequest`를 유지한다.

## 4. 리뷰·targeted validation

- 관련 producer/consumer10개 test module: `799 passed`.
- 검증 범위: drought/workorder/runtime summary, unknown provenance, pipeline compaction, scanner/WS causal census, subscription repair snapshot, executable-BBO attribution, micro venue defect.
- P0~P2 unresolved finding: 0 (main11행의 현재 코드·consumer 계약과 위젯/episode 비선정 판정 범위).
- 실주문·Provider 호출·runtime env 변경·재기동·과거 raw 재생성은 수행하지 않았다.

## 5. Pass 2 결과

Pass 1 disposition companion을 발행한 뒤 같은9/14 source를 재-intake하고 summary handoff consumer를 갱신했다. `eligible_actionable_open=0`, 구현 요청 미분류0, 전수 미분류0이며 새 또는 decision-changed eligible 항목이 없어 `implementation_fixed_point=true`다. Pattern Lab3행과 low-price decision 결손1행은 필요한 계약을 명시한 근거 차단으로 남으며 구현 완료로 세지 않는다.

strict verifier의 summary handoff는 PASS이고 controller는 `2026-09-15 01:12:06 KST`에 DONE이다. 반복 finalization 중 누적된 preopen active-log writer defer는 owner 전용 무손실 rollover로 원문·gzip 복원 SHA-256을 검증한 뒤 해소했다. 최신 finalization은 `01:17:28`, final detector는 `01:17:29`에 DONE이다. 이 복구는 filesystem instrumentation이며 runtime·order·provider·threshold authority가 없다.
