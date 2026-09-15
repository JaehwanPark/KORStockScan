# 9/15 implement-now·위젯·episode 2-pass 리뷰

기준 코드: `916c675fcf9e42073f241989dd9d9fd62b0e506e`

권한은 source/report/schema/instrumentation과 기존 자동 handoff 검증으로 제한했다. runtime policy, Provider budget, 당일 prompt 선택, 주문 및 safety guard는 변경하지 않았다.

## Pass 1

현재 generation의 75행을 전수 대사했다. 구현 요청 20행 중 11행은 현재 producer, 직접 consumer, source-quality 및 authority 계약이 구현돼 있음을 검증해 `already_implemented_verified`로 판정했다.

- `order_entry_submit_drought_auto_resolution`
- `order_microstructure_v3_evaluation_venue_missing_or_conflicting`
- `order_observation_source_quality_unknown_token_provenance_gap`
- `order_pipeline_event_compaction_v2_shadow`
- `order_scanner_eligible_no_heavy_closed_loop`
- `order_scanner_funnel_executable_bbo_join`
- `order_scanner_scan_generation_conservation_gap`
- `order_ws_decision_stage_stale_backoff_attribution`
- `order_ws_subscription_stale_repair_observability`
- `order_ws_total_stale_escalation`
- `order_ws_trade_tick_quiet_low_liquidity_classification`

새 `order_entry-prompt-revision-087251275cfaeb3c0da19f54`는 세 exact parent의 비용 근거가 모두 `source_unavailable`이고 producer가 `implementation_only_closure_allowed=false`를 명시한다. parent/hash와 영어 appendix만으로 새 prompt를 구현하지 않고 `blocked_missing_evidence`로 유지한다. owner는 `AIDecisionActionOutcomeNaturalEvidence0908`이며, 같은 parent의 검증된 exact 비용 결과를 materialize한 뒤 distinct version/hash를 기존 bounded offline evaluation으로 검증해야 닫힌다.

기존 Pattern Lab 8행도 구현 위치·직접 consumer 또는 필요한 source contract가 없어 `blocked_missing_evidence`를 유지한다. 위젯·episode 추천의 원문 `research_watch`, `keep_collecting`, holdout veto 및 source-only 비선정은 구현 요청으로 바꾸지 않았다.

## 리뷰와 검증

- P0~P2 unresolved finding: 0.
- main producer/consumer/source-quality 계약 13개 test module: `1102 passed`.
- cleanup/finalization 계약: `70 passed`.
- release worktree의 의도된 `data` symlink 때문에 `git check-ignore` 두 검사가 128을 반환한 환경 차이는 일반 worktree에서 같은 commit으로 재실행해 포함된 전체 `1102 passed`로 확인했다.
- shell syntax와 `git diff --check`: 통과.
- 실제 주문, Provider 호출, runtime env 변경 또는 trading process 재기동: 없음.

## Consumer handoff

검증된 11행은 code review, targeted validation 및 direct consumer evidence를 같은 report hash에 결속한다. prompt 제안은 source-gap evidence로만 결속한다. companion 재생성 뒤 `eligible_actionable_open=0`, `implement_now_unaccounted_count=0`, `intake_unaccounted_count=0`과 새 또는 decision-changed eligible 항목 0을 Pass 2에서 확인한다.
