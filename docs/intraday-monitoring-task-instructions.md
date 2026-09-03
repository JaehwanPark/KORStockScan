# 장중 수익극대화 모니터링 작업지시문

작성 기준: `2026-09-03 KST`

현재 가동 중인 키움증권 연동 SCALPING 런타임을 대상으로 EV와 누적 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다. 메인 봇, 위젯 매매기계, 에피소드 매매기계는 서로 독립된 주문 owner로 평가하며 주문번호·보유수량·청산 귀속을 혼합하지 않는다.

현재 튜닝 원칙과 active/open 상태는 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8, 실행 항목은 당일 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 `docs/time-based-operations-runbook.md`, producer/consumer와 R0→R6 의존 순서는 `docs/report-based-automation-traceability.md`를 기준으로 한다. 실제 기동 권한은 검증된 당일 PREOPEN apply plan/runtime env/verify와 exact-date machine policy, 이를 읽은 현재 PID의 provenance를 함께 기준으로 한다. 이 문서의 family 예시는 고정 ON 목록이나 재기동 권한이 아니다.

이 문서는 장중 반복 실행 절차다. 매 실행 시작 시 고정 예시를 신뢰하지 말고 현재 PID env, 당일 runtime verify, exact-date policy, broker 계좌·미체결, 설치된 cron/systemd/tmux owner와 최신 source-quality artifact를 다시 읽는다. 코드가 구현돼 있거나 전일 추천에 나타났다는 사실만으로 현재 process 반영 또는 실주문 권한을 인정하지 않는다. 전일 장후 candidate는 당일 PREOPEN handoff 입력일 뿐이고, 당일 apply plan/runtime env/verify와 launcher/PID load receipt가 닫히기 전에는 적용 또는 효과로 보고하지 않는다. runbook·traceability·설치 trigger·실행 snapshot의 단계, 조건 또는 owner가 다르면 mtime이나 우연한 실행 사실로 한쪽을 선택하지 않고 `contract_drift`로 fail-closed한다.

## 1. 목표

위험을 모두 회피하는 것이 아니라 감당 가능한 위험으로 더 많은 유효 기회를 탐색하고, probe·분할 진입·동적 수량·부분익절·trailing·hard/protect/emergency guard 등 각 owner의 후단 보호장치와 함께 기대값과 누적 순이익을 높인다.

모든 주요 기회는 다음 질문으로 반복 점검한다.

1. 유효한 상승 또는 짧은 회귀 기회가 있었는데 어느 단계에서 왜 진입하지 못했는가?
2. 후단 submit 차단이 적정하더라도 시장의 실제 상승 모집단이 scanner source·universe·watch budget·평가·promotion 중 더 상위 단계에서 미관측되거나 고갈되지 않았는가?
3. 제출·체결 가격과 수량, residual multi-leg, 추가매수는 당시 executable 시장과 owner 계약에 적정했는가?
4. 비용 차감 후 수익을 확대할 수 있었는데 과차단·미체결·조기청산으로 훼손하지 않았는가?
5. 손실 가능성이 커졌을 때 owner별 보호·청산 계약이 적시에 작동했는가?
6. 당일 ON runtime과 policy는 실제 eligible 표본에서 호출되고 의도한 효과를 냈는가?
7. AI가 호출되는 경로에서는 호출·입력·판단 품질이 모두 정상이고 손익에 유리했는가?
8. smoothing이 순간 노이즈를 줄였는가, 아니면 유효한 변화까지 늦추거나 stale 상태를 숨겼는가?
9. 메인 봇·위젯·에피소드 중 어느 owner의 기회인지 명확했고 중복 진입·오청산·수량 혼합이 없었는가?
10. 예정된 process와 source-only observer가 실제로 살아 있고 의미 있는 output과 consumer를 가지며 dead·hung·duplicate·no-op·orphan 상태가 아닌가?
11. 후보·BBO·submit·terminal·mature·net-economic 표본 0 또는 floor 미달은 시간이 해결하는 부족인가, key/hook/consumer 단절로 모집단이 구조적으로 고갈된 것인가?
12. 당일 실제로 소비된 입력의 효과와 장중 생성되어 장후/다음 PREOPEN으로 넘길 source-only 산출물을 서로 다른 시간축과 authority로 보고했는가?

단순 가동, 후보 수, 승률 또는 gross MFE가 아니라 실제 체결 가능성, 수수료·세금·spread·slippage를 반영한 EV와 순이익을 최종 기준으로 삼는다. `2026-08-18` 이후 R0→R3 비교 경제성은 매수 수수료 1.5bps, 매도 수수료 1.5bps, 매도 세금 20bps, Provider 비용 0원인 effective-dated 정책 계약을 사용하고, 공식 KOSPI/KOSDAQ master에서 보통주로 확인된 종목만 포함한다. exact broker receipt 손익·비용은 실거래 reconciliation 근거로 별도 보존하되 R0→R3 고정 비교비용을 암묵적으로 대체하지 않는다. 비용모델·master의 effective date 또는 source hash가 맞지 않으면 EV 입력을 차단한다.

## 2. 매매기계별 모니터링 범위

### 2.1 메인 봇 매매기계

메인 봇은 시장 전반을 스캔해 새로 나타나는 스캘핑 기회를 찾고 `selection → entry → submit → probe/residual → holding → scale_in → exit` 전체 lifecycle을 소유한다.

다음 흐름을 후보·주문·체결·보유변화·매도마다 재구성한다.

`시장·universe source → scanner source fetch/normalize → candidate pool/rank/limit → (A) pruned first-blocker → bounded BBO schedule/observation → source-only terminal 또는 (B) eligibility/source guard → watch budget/slot reservation → scanner promotion/WATCHING → runtime attach → fast precheck → heavy evaluation → entry AI trace/provider/trusted decision → authority gate → entry-price AI → submit guard → 선택된 bounded mode의 probe 또는 normal sizing → residual multi-leg → holding/scale_in → partial TP/trailing/exit → broker reconciliation`

확인 항목:

- 감시 슬롯·candidate/TP1·freshness·AI·latency·micro·tick-speed·가격·계좌·주문·수량·cooldown 중 최초 차단 owner와 직접 원인
- score가 baseline prior/feature로만 사용되고 단독 BUY 또는 단독 DROP 권한이 되지 않았는지
- 당일 PREOPEN apply/verify가 선택한 mode에서만 probe-first가 적용됐고, source-only one-share exploration을 real 1주 주문 권한으로 오인하지 않았는지. 별도 `WAIT6579_PROBE_CANARY` budget/quantity cap의 `0`은 probe 차단이나 1주 cap이 아니라 normal new-buy dynamic sizing 사용을 뜻하며, 실제 probe 체결 뒤에는 fresh BBO와 방향을 다시 확인했는지
- residual 가격·수량·제출 시점과 취소가 bundle 및 broker 상태와 일치하는지
- 주문 API 응답과 WS execution receipt의 도착 순서가 바뀌어도 exact 주문번호와 immutable owner로 결속됐는지, 취소·reprice 전에 원주문 terminal absence와 KRX/NXT 전체 잔고가 확인됐는지
- continuation에서 pyramid가 과차단되지 않았고 하락 구간의 avg-down이 불리한 노출만 키우지 않았는지
- 부분익절·runner·trailing·hard/protect/emergency owner의 실행 순서와 실제 체결 지연
- `entry_cancel_wait_runtime`을 ADM/LDM·entry-price AI와 분리했는지. 당일 PREOPEN 적용된 standard/breakout/pullback/reserve cancel wait만 주문취소 owner이고 entry-price AI `max_wait_sec`는 advisory라서 live cancel timeout을 직접 덮지 않는지
- SCALP preset +1.5% TP가 더 이상 profit-taking owner가 아니며, 신규·복구 holding의 legacy preset TP ref가 취소/disabled된 뒤 `scalp_trailing_take_profit` 경로가 이익 실현을 소유하는지. `SCALP_PRESET_TP` 호환 필드는 stop-safety provenance 외 새 주문 권한을 만들지 않는지
- 매도 후 1·3·5·10·20·30·60분 반사실을 실현손익과 분리했는지

`position_sizing_dynamic_formula`가 메인 봇 신규·추가매수 수량의 단일 owner다. 현재 선택 계약 `entry_type_5stage_cap25_v1`은 source-count/time/venue로 `10%/15%/20%/25%/25%` tier를 고르고 절대 25% cap, 95% safe budget과 최소 1주 floor를 유지하며 scale-in은 최초 tier를 재사용한다. NXT·unknown venue·invalid/missing source·복구 불가능한 최초 entry context는 tier 1로 fail-closed한다. `wait6579_ev_cohort`는 LDM/source-quality provenance일 뿐 은퇴한 독립 entry bridge가 아니고, micro-reversion 또는 AI 판단은 수량·broker guard·hard safety를 직접 바꾸지 않는다. 실제 값은 당일 PREOPEN verify와 현재 PID receipt로 다시 확인한다.

#### 메인 봇 상승종목 탐색 포착률과 submit drought 상위원인 감사

submit drought의 AI·latency·spread·stale·broker 차단 근거가 적정하다는 판정은 그 차단에 도달한 종목에 한한다. 이 판정만으로 scanner가 시장의 상승종목을 충분히 찾았다고 결론내리지 않는다. scanner/pipeline event를 기점으로 만든 funnel·rising-missed report는 scanner 밖 미관측 종목을 분모에 넣을 수 없으므로, 독립된 시장 전체 기준 모집단이 없으면 판정은 `insufficient_evidence_scanner_recall`, blocker는 `external_opportunity_denominator_missing`으로 남긴다.

다음 두 기준 모집단을 분리해 고정한다.

1. `as_of rising benchmark`: 당시까지 이용 가능했던 독립 전종목 시장 source로 구성한 포착률 분모다. 공식 KOSPI/KOSDAQ 보통주 master의 effective date·hash, symbol, venue/session, source timestamp·hash, panel/top-N, 상승률·체결대금·거래량 등 선정 정의, lookback·capture cadence를 먼저 고정한다. panel이 `common` 또는 `liquid`라는 이름만으로 보통주·유동성 계약을 충족했다고 간주하지 않는다. 이 모집단은 후행 고가를 사용하지 않는다.
2. `ex_post executable opportunity`: 실제 놓친 수익기회인지 판정하는 action-neutral mature label이다. benchmark 최초 충족 시점 후 fresh executable BBO의 1·3·5·10·20·30·60분 target/adverse first-hit, fill feasibility와 총비용 차감 EV를 계산하되, 이 후행 label을 당시 scanner 선정이나 AI 입력으로 역류시키지 않는다.

독립 benchmark의 `symbol × venue × session × opportunity_episode_id`를 stable key로 삼는다. `opportunity_episode_id`는 최초 benchmark crossing, 선언된 validity/TTL과 reset 규칙으로 만들고 as-of capture bucket은 provenance로 남긴다. 종목·거래소별 하루 한 행으로 재진입 wave를 합치거나 반복 snapshot마다 분모를 부풀리지 않는다. 다음 funnel을 전수 대조한다.

`external market opportunity denominator → scanner source fetch/normalized → candidate pool/rank/limit → universe/source eligible and guarded → watch budget/slot reservation → scanner promotion/WATCHING → runtime attach → fast precheck → heavy evaluation → entry AI trace → provider called → trusted evaluated result → candidate/authority gate → submit safety → submit`

- 종목별 최초 benchmark 충족 시각, scanner 최초 fetch·promotion·fast/heavy evaluation·AI·candidate 시각과 각 지연의 p50·p95를 남긴다. benchmark capture 후 동일 code·venue·session·episode의 `forward_exact`만 인과 coverage로 인정한다.
- 포착 성공은 선언된 `scanner_detection_sla`와 opportunity validity 안에 있는 다음 scanner loop에서 판정한다. 이전 promotion, same-day retrospective·symbol-only 근접 join, cross-venue/session, 다른 promotion wave를 성공으로 세지 않고, SLA 밖 늦은 발견은 `late_discovery_after_opportunity_window`로 분리한다.
- 사건 반복 count가 아닌 unique opportunity-episode 기준의 `source_seen_recall_pct`, `watch_admission_recall_pct`, `promotion_recall_pct`, `fast_precheck_recall_pct`, `heavy_eval_recall_pct`, `candidate_recall_pct`와 분모·분자를 보고한다. primary decision metric이라고 선언한 비율은 실제 named output field, formula·window·sample floor와 일치해야 한다.
- `benchmark top-N → scanner promotion`의 discovery recall, `promotion → runtime attach/fast precheck/heavy evaluation/provider`의 post-promotion consumption, `trusted AI result → budget/latency/submit`의 downstream conversion은 서로 다른 분모로 보존한다. promotion ID, unique symbol, opportunity episode count를 함께 보고하고 반복 promotion ID를 discovery recall 성공으로 중복 집계하지 않는다.
- 각 benchmark row는 단 하나의 최초 미도달 원인으로 `scanner_source_unseen|scanner_fetch_or_normalization_gap|source_or_candidate_pool_rank_limit_pruned|intended_source_or_universe_exclusion|unexplained_or_wrong_scope_filter_exclusion|watch_budget_not_admitted|slot_starvation|promotion_rule_rejected|runtime_attach_gap|fast_precheck_gap|heavy_eval_deferred_never_evaluated|entry_ai_trace_gap|entry_ai_preflight_or_transport_block|entry_ai_untrusted_or_rejected|candidate_or_authority_gate_blocked|intended_submit_safety_block|late_discovery_after_opportunity_window|submitted|unresolved_source_quality`를 갖는다. 겹치는 사유는 secondary reason으로만 집계한다.
- 광의의 `broad_rising_population = 각 최초 미도달 상태와 submitted 상태의 배타적 합`과 단계별 input·output·dedup·unmatched 보존식을 닫고, KRX·`PREMARKET_KRX_LIKE`·NXT와 시간대별로 분리한다. 비보통주·master 불일치, 매수 시간창 밖, 명시적 upper-limit/chase protection 등 `intended_source_or_universe_exclusion`은 근거와 함께 남기되 `actionable_rising_population` 분모에서 제외한다. 근거가 없거나 잘못된 venue·session 적용은 제외하지 않는다.
- 가격 상승만 있고 executable BBO·거래대금·spread·fill feasibility·비용 계약을 충족하지 못한 종목은 탐색 recall 진단에는 남기되 실행 가능한 놓친 수익기회로 세지 않는다.
- `scanner_full_eval_loop_budget_deferred`가 validity/SLA 안에 평가됐다면 일시 backpressure로, opportunity validity가 닫힐 때까지 `deferred_never_evaluated`로 남거나 장기 slot 점유로 반복 탈락했다면 구조적 탐색 결함으로 분리한다.
- promotion 후 maturity window가 지났는데 AI handoff가 없는 종목은 scanner 미발견으로 합치지 않고 `post_promotion_handoff_gap_candidate`로 분리한다. exact promotion lineage의 runtime target attach, WATCHING skip reason, fast-precheck result·lag·queue rank, heavy-evaluation queue wait·outcome, Entry-AI trace·provider receipt까지 연결한 후 첫 결손 소유자를 판정한다.

기존 `market_opportunity_census`를 발견하면 source-only partial observer로만 사용한다. 대상일 snapshot/report, installed trigger·traceability owner, official master binding, exact-capture·lineage·detection SLA, 실제 primary metric field가 모두 닫히지 않으면 이를 현재 recall 정상 근거로 쓰지 않고 `scanner_recall_instrumentation`을 연다. 단일·얇은 top-N capture는 `early_evidence|hold_sample`로 남기고 source-quality-valid target-date·선언 sample floor·bounded detection SLA가 모두 닫힐 때만 coverage 정상을 판정한다.

최종 판정은 `insufficient_evidence_scanner_recall`, `natural_actionable_riser_absent`, `scanner_coverage_valid_submit_drought_downstream`, `post_promotion_handoff_gap_candidate`, `scanner_under_discovery_confirmed`, `compound_scanner_and_submit_drought` 중 해당 상태와 직접 근거를 남긴다. 탐색 결함이면 source ingestion, universe filter, candidate pool, watch-budget/slot, scheduler, promotion 계측·report·source-only replay를 먼저 보완한다. 이 감사는 market source enable/disable, fetch depth, candidate limit, reserved slot/WATCHING cap, scheduler/full-eval budget, promotion rule, score·entry·submit threshold, hard safety, 수량·provider·bot·broker를 장중 hot mutation하거나 재기동할 권한을 만들지 않는다. 선택 surface 변경은 source-quality-valid rolling executable outcome, same-stage single owner, rollback과 다음 PREOPEN bounded artifact 또는 명시적 사용자 권한을 따로 요구한다.

#### Scanner-pruned bounded BBO observer

promotion 이전에 `reentry_cooldown_no_material_upgrade|market_gainer_reserved_full|general_slot_limit`로 탈락한 후보는 전수 `scalping_scanner_candidate_pruned` census와 별도로, 선택된 episode만 `scalping_scanner_prune_bbo_schedule → scalping_scanner_prune_bbo_observation` source-only 경로에서 확인한다. 이 observer는 기존 Kiwoom REST `ka10004`를 exact KRX/NXT route로 조회하며 scanner 선정·slot·cooldown·threshold를 바꾸지 않는다.

- 기본 bound는 process-local active episode 8개, pending sample 80개, KST 거래일당 최대 1,200 request, request 시작 간격 최소 0.25초다. 표본 시점은 anchor 후 `0·3·10·20·30·60·180·300·600·1200초`이며 anchor→schedule delay는 2초 이하여야 한다.
- 이 local bound와 별도로 운영 국내주식 계좌/토큰별 조회 TR 5회/초 cross-process gate를 확인한다. scanner-prune·external-census·widget research/advisory·pure-market backfill은 `source_only`로 합산 최대 4/5 slot까지만 사용해 `runtime_required|execution_critical` 조회 한 slot을 보존한다. 주문 TR 5회/초는 별도 버킷이고, 모의투자 조회는 token+origin+`api-id`별 1회/초다. local 0.25초·분당·일일 cap은 공통 상한을 대체하지 않는다.
- 각 schedule/observation은 `scanner_prune_observer_episode_id`, scan generation/rank, prune reason, code·venue·session, request/response code, due/request/observed 시각, schedule lag, best bid/ask, quote age와 gap reason을 보존한다. exact response route가 다르거나 BBO가 invalid/crossed/nonpositive이면 captured로 정규화하지 않는다.
- HTTP 429와 `1700|1701|1702`는 shared cooldown으로 전파하고, bounded retry가 소진되거나 유효 응답이 끝내 없으면 `ka10004_rate_limited`, local admission/cooldown defer는 `ka10004_shared_read_budget_deferred`로 분리한다. 한도 감지 뒤 exact valid 응답으로 복구된 요청은 `rate_limit_detected=true`, `rate_limit_retry_exhausted=false` warning provenance를 보존하되 실패 표본으로 버리지 않는다. owner/PID/class/api-id/request code/attempt/wait/scope digest를 남기며 bearer token은 저장·로그하지 않는다. retry·일일 budget·호출 밀도 상향을 복구로 사용하지 않는다.
- full prune census와 bounded observer denominator를 분리한다. observer의 EV나 coverage를 전체 탈락 모집단으로 외삽하지 않고 `full_funnel_population_ev_extrapolation_allowed=false`를 유지한다.
- implementation 존재만으로 완료라고 하지 않는다. 당일 fresh PID가 collector를 구성하고 자연 prune에서 `new_episode_scheduled|existing_episode_reused`와 exact-route capture 또는 명시적 source-quality gap receipt를 생성해야 runtime hook이 확인된다. eligible prune은 있었지만 schedule receipt가 0이면 `runtime_hook|process_reflection`, schedule은 있었지만 observation이 없으면 queue/worker/REST/source gap의 최초 결손을 분리한다. eligible prune 자체가 없으면 별도 PID import/configure receipt가 있을 때만 `healthy_no_natural_sample`이며, 그 receipt도 없으면 `pending_declared_window|blocked_missing_evidence`로 둔다.
- decision contract는 `scanner_prune_bbo_observation_only`, `runtime_effect=false`, `market_data_request_effect=true`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`다. resolved outcome 20건, BBO episode coverage 95% 이상, right-censored 20% 이하의 선언 floor가 닫히기 전에는 선택 surface나 실주문 근거로 사용하지 않는다.

#### 메인 봇 risky micro-reversion 관측

`risky micro episode`는 독립 에피소드 매매기계가 아니다. 메인 봇 normal-entry에서 soft-block된 후보 중 passive 체결과 짧은 보유로 비용 차감 후 작은 순수익을 얻을 가능성을 재검사하는 `micro-reversion` 관측·handoff 분류다.

- stale/conflict, broker/account/order/quantity/cooldown, 명백한 adverse tape와 비경제적 spread는 `hard_negative`로 유지한다.
- fresh executable BBO와 회복 가능성이 남은 후보는 `recheckable_soft_risk`로 짧게 재검사한다.
- passive fill 가능성, 제한된 spread, 짧은 positive micro support와 비용 초과 목표가 확인된 후보만 `cost_aware_micro_candidate`로 분류한다.
- source-only 후보는 주문하지 않는다. 승인된 bounded runtime이 있더라도 기존 submit guard와 probe-first owner로만 handoff한다.
- risky tag 자체는 residual, scale-in, 주문취소 또는 청산 권한이 아니다. continuation 확인 후 기존 normal owner로 재분류된 경우에만 잔량 확대를 검토한다.

`bid+1`, TTL 3·5·10초, 제한적 ask 진입은 source-only 반사실로 비교한다. fresh executable bid/ask, quote age, tick size, fill feasibility, 총비용, 3·10·20·30초 및 1·3·5분 target/adverse first-hit, timeout executable exit와 tail loss를 같은 lineage로 연결한다. 충분한 거래일과 실제 filled-terminal 표본 전에는 실주문 승격 근거로 쓰지 않는다.

현재호가의 매도잔량 감소는 단독 상승 신호로 사용하지 않는다. `0D` 호가와 `0B` 체결을 같은 venue·symbol·session의 local-receive 시간창으로 결속하고 각 stream의 monotonic sequence를 독립 검증해 현재 ask depletion 속도, 상위 ask 1~5호가 잔량 기울기, refill/replenishment, 매도호가 취소와 실제 공격적 매수체결의 구분, spread·BBO age, bid 지지와 가격 반응을 함께 본다. 빠른 depletion 뒤 refill 또는 bid 붕괴가 발생하면 false-positive로 보존한다. 이 축은 observer/source-only이며 검증된 policy candidate 전에는 BUY·수량·취소·청산 권한이 없다.

#### Limit-down ordered-path observer

`limit_down_watch`의 현재 관측 계약은 같은 symbol·KRX session에서 ordered `0B` 체결과 `0D` 호가를 모두 요구한다. REG 요청은 `required_realtime_types=(0B,0D)`와 wire `realtime_types=(0B,0D)`를 명시하고, type별 first/last receipt와 monotonic event 순서를 따로 보존한다. quote-only 수신을 ordered-path 성공이나 trade backing으로 정규화하지 않는다.

- 당일 natural 대상이 없고 manager load/configure가 별도로 확인되면 `no_observation|healthy_no_natural_sample`, 대상과 REG receipt가 있으나 한 type이 없으면 `source_quality_gap`, 두 type은 있으나 동일 symbol/session의 유효한 event order가 아니면 `ordered_path_invalid`로 분리한다. manager receipt도 없으면 자연 부재로 정상화하지 않고 `process_reflection|blocked_missing_evidence`로 둔다.
- 전일 `limit_down_watch_ordered_path_not_observed`는 수정된 코드나 report 존재만으로 해소되지 않는다. fresh PID의 신규 자연 표본이 ordered 0B+0D와 downstream report/verifier lineage를 닫을 때까지 `collecting_after_structural_repair`다.
- source observer는 `decision_authority=limit_down_source_observation_only`이며 자체 실주문 권한이 없다. 별도의 target-date PREOPEN policy가 실제 로드·검증되지 않았다면 과거 live-auto candidate, historical sample 또는 관측 성공으로 entry·수량·가격·slot·재진입 권한을 열지 않는다.

### 2.2 위젯 매매기계

위젯 매매기계는 종목별 source-qualified 신호를 독립된 소규모 실주문 episode로 집행한다. 메인 봇 threshold 완화 경로나 에피소드 profile의 대체 owner가 아니다.

다음 흐름을 위젯별로 재구성한다.

`widget signal → source-quality/policy match → episode lock → entry order → fill confirmation → target order → terminal/custody reconciliation`

확인 항목:

- signal source, policy version, symbol, venue/session과 exact episode ID의 일치
- `ENTRY_CAUTION/ENTRY_READY` 등 허용 신호가 아닌 반복 snapshot이나 stale 신호가 신규 episode를 만들지 않았는지
- 중복 episode 차단, entry fill과 target 주문번호, 실제 남은 수량 귀속의 정확성
- 종목별 entry price, target tick, cooldown, 일일 완료 episode 상한과 terminal 조건이 당일 policy와 일치하는지
- 목표 도달 전·후 순서를 executable 가격으로 판정하고 같은 1분봉 고가를 체결 후 수익으로 오인하지 않았는지
- 미청산 right-censored episode를 손익 0 또는 완료 표본으로 섞지 않았는지
- 짧은 회전 목적에 비해 open episode가 자본을 과도하게 점유했는지, 반대로 성급한 청산으로 비용 차감 수익을 훼손했는지
- 메인 봇·에피소드·수동 보유수량을 위젯이 매도하거나 신규 진입 차단 근거로 사용하지 않았는지
- expansion recommendation이 `implementation_review_ready`, sample/trading-date/spread/volatility floor와 exact-date handoff를 통과했는지; `research_watch` 등록 또는 collector 가동만으로 policy mutation이나 매매 승격을 주장하지 않았는지

위젯의 효율은 후보 수가 아니라 completed episode의 비용 차감 EV, 목표 완료시간, 자본점유시간, 반복 가능성과 owner 정합성으로 평가한다.

### 2.3 에피소드 매매기계

에피소드 매매기계는 특정 종목·venue·시간창의 반복 패턴을 exact-date profile과 독립 process/state/ledger로 집행한다. 현재 삼성전자 시간대 기계와 저가주 two-leg profile을 대표 owner로 본다.

다음 흐름을 profile/episode/leg별로 재구성한다.

`exact-date policy → session/setup 확인 → 두 개 10주 leg 제출 → leg별 체결 확인 → leg별 target 주문 → COMPLETE/NO_TRADE/HELD/BLOCKED → custody reconciliation`

확인 항목:

- 당일 exact-date policy, profile hash, systemd timer와 실제 process 기동 일치
- 신규 episode의 두 개 10주 leg, 최대 20주 계약과 legacy 1주 custody 비확대
- 각 leg의 지정가·체결·부분체결·잔량취소·목표 주문이 원주문번호에 정확히 귀속됐는지
- 종목·venue·시간창별 target tick과 signal validity가 profile 계약과 일치하는지
- 다른 episode, 위젯, 메인 봇 또는 수동 보유수량을 합치거나 대신 매도하지 않았는지
- `HELD`가 목표 미체결 보유를 뜻하는 정상 custody 상태인지, 실제 장애·고아 주문·누락된 reconciliation인지 구분됐는지
- 수동 청산이 있었으면 broker receipt와 exact owner ledger에 실현손익·비용·terminal 상태가 반영됐는지
- fill-before-submit, late broker receipt와 event-time regression을 정상 arrival provenance로 보존했는지, 동일 owner lifecycle의 KRX 진입→NXT 청산을 cross-attempt로 오판하지 않고 phase별 `entry_venue/exit_venue`로 기록했는지
- target/entry policy를 바꾸지 않는 관측축과 실제 다음 PREOPEN 후보를 명확히 분리했는지

에피소드 수량은 장후 튜닝축이 아니다. 무손절·시간청산 없음, 목표 주문 유지 등 profile 고유 계약은 단순 post-sell MFE만으로 결함 판정하거나 임의 변경하지 않는다.

## 3. 튜닝축별 반복 점검

### 3.1 Micro-reversion

급등·반전·soft-block 이후의 짧은 회귀 기회를 비용 차감 실행 가능성으로 평가한다.

- 메인 봇 risky micro 관측, 위젯·에피소드의 microstructure attribution을 같은 축에서 비교하되 주문 owner와 정책 선택 권한은 합치지 않는다.
- mark-price MFE 대신 executable BBO와 target/adverse 선후를 사용한다.
- ask depletion은 취소·refill·공격적 매수체결·다단계 호가 이동을 분리하고, current ask 한 레벨의 감소만으로 반등 label을 만들지 않는다.
- quote/BBO/tick context 결손은 0수익으로 보간하지 않고 source-quality gap으로 분리한다.
- `source_only_candidate`, `recheck_required`, `excluded_excessive_risk`, `excluded_uneconomic_spread`, `source_quality_blocked`를 직접 근거와 함께 보존한다.
- promotion EV에는 허용된 source-only cohort만 포함하고 recheck 진단 cohort와 실제 filled-terminal 표본 floor를 분리한다.
- observer canary의 snapshot freshness, 0B/0D callback p95·p99, queue full/drop, worker/writer error, writer 생존수와 low/critical disk watermark를 확인한다. canary stop은 Provider replay와 R3 승격을 차단하지만 정확한 local label·Provider-floor census 자체를 누락시키는 이유로 사용하지 않는다.

판정 기준은 `추가 참여율 + 비용차감 source_quality_adjusted_ev_pct + adverse-first/tail loss + 기존 정상 경로 순이익 비훼손`이다.

### 3.2 AI 판단 품질 개선

AI가 사용되는 endpoint마다 세 층을 분리해 점검한다.

1. 호출 품질: provider, model, transport, timeout, failback, parse, cache, response ID
2. 입력 품질: exact snapshot, canonical context, 완성 분봉, executable price/BBO, 체결 tape, venue/session, 시각과 결측 처리
3. 판단 품질: raw/normalized/final action, edge/risk/reason, 이후 MFE/MAE·first-hit·체결·손익

각 자연 호출에서 request/trace/snapshot ID, prompt/payload/response hash, prompt/schema/bundle version, latency·token usage와 submit/holding/exit 결과를 연결한다.

- `BUY`, `WAIT + probe intent`, `WAIT observation-only`, `DROP`, `INSUFFICIENT_DATA`의 의미를 혼합하지 않는다.
- semantic/schema 오류와 모델의 실질적 오판을 분리한다.
- provider/schema 성공을 판단품질 성공으로 간주하지 않는다.
- 동일 exact payload의 Control/Candidate replay에서 선행 adverse 뒤 회복, 직접 상승과 순서 불명을 구분한다.
- AI는 직접 주문·수량·broker safety 권한이 아니며 비정상 출력을 임의 BUY로 복구하지 않는다.

장중에는 R0 source가 이후 R1 daily, R2 cumulative, R3 source-only manifest로 이어질 수 있는지 미리 점검한다. exact prepared request census, A/B/C 동일 source pool, action-neutral label, Provider replay receipt, main lifecycle exact join을 분리하고, Provider 일일 budget 또는 observer/source-quality gate 때문에 replay가 미실행된 상태를 판단 실패나 R3 생성 성공으로 포장하지 않는다. Provider replay와 R3는 reviewed 호출량·거래일·common parent·종목 floor 및 lifecycle terminal 계약을 모두 통과할 때만 진행한다.

생성 파일 크기, materialized request 수 또는 provider/schema 성공만으로 경제적 유효 표본이 있다고 판단하지 않는다. `exact request/response binding → source-quality-valid payload → action-neutral mature outcome → lifecycle terminal join → effective-dated cost/master binding → net-economic eligible row` funnel을 전수 대조한다. 마지막 값이 0이면 최초 0 stage를 찾고, 아직 정해진 maturity deadline 전인 표본과 exact companion/hash·BBO·terminal join이 영구 누락되는 구조적 결손을 분리한다. 결손 row를 0 EV로 보간하거나 대용량 source artifact를 유효 denominator로 대체하지 않는다.

기대 baseline은 기본 live scalping AI가 OpenAI이고, `entry_price`만 Bedrock Qwen3 32B primary → Nova Lite v2 failback 뒤 double-failure defensive close이며 OpenAI third fallback이 없고, `holding_flow`는 Nova Lite v2 primary → OpenAI failback인 계약이다. 실제 route는 당일 runtime env와 현재 PID provider receipt로 검증하고, transport/failback incident와 전략 threshold·가격·수량 효과를 분리한다. AI를 사용하지 않는 위젯·에피소드 경로에 억지로 provider 정상성 판정을 요구하지 않는다.

### 3.3 Smoothing

Smoothing은 순간 tick·호가·OFI/QI 흔들림으로 action이 왕복하는 것을 줄이는 공통 품질축이며 별도 주문 owner가 아니다.

- live `holding_flow_ofi_smoothing`은 raw/smoothed score, EWMA state, persistence count, snapshot age, policy version과 최종 action을 함께 남긴다.
- `soft_stop_whipsaw_confirmation`은 현재 OFF/source-only이며 exact-path rolling evidence와 별도 적용 계약 없이 live soft-stop owner로 세지 않는다.
- stale snapshot, observer unhealthy 또는 입력 부족이면 smoothed 값을 사용하지 않는다.
- smoothing 적용 전후 holding·partial TP·trailing·exit 지연과 post-sell MFE/MAE를 비교한다.
- whipsaw 감소와 함께 늦은 손절, 이익반납, 진입 지연이 늘지 않았는지 확인한다.
- source-only smoothing 대안은 real action을 바꾸지 않으며 rolling/cumulative EV와 exact-path 반사실로만 판정한다.

### 3.4 위젯 튜닝

- 종목·venue·setup별 signal-to-fill, fill-to-target, target completion time과 비용 차감 EV를 누적한다.
- entry price, target tick, cooldown, 완료 episode 상한 후보를 동일 policy version의 Control과 비교한다.
- source-quality, 미체결, partial fill, 미청산 custody와 실제 terminal sample을 분리한다.
- exact-date policy와 rollback이 있는 단일 bounded axis만 다음 PREOPEN 후보가 될 수 있다.
- `micro_entry_confirmation`은 clean-baseline exact owner·symbol·session·entry-state와 실제 완료 outcome 중 `supportive_confirmation_candidate`만 누적해 `0/1/3/5초` 진입 확인 지연을 고를 수 있다. `adverse_veto_candidate|recheck_required|source_quality_blocked`는 live 지연 근거에서 제외한다. 당일 completed holdout, 20 completed outcome, 5/10/20일 비용차감 EV, BBO/depth·0B/0D source-quality, delayed-entry feasibility 90%, completed paired coverage 95%, right-censored 20% 이하 floor를 모두 통과한 전체 owner 중 한 scope만 다음 exact-date v2 policy에 반영하고, 미달·v1/변조 policy이면 즉시진입 `0초`를 유지한다. 선택된 지연 뒤에는 같은 원천 signal과 기존 entry guard를 전부 다시 확인하고, signal 시점과 due 시점의 exact symbol·route `ka10004` BBO가 fresh하며 bid·ask가 매수자 관점에서 악화되지 않고 owner의 기존 가격·target 안에서 정책 고정비용 차감 modeled 순 edge가 양수일 때만 기존 BUY 경로로 진행한다. 이 값은 broker receipt exact 비용이나 미래 target 체결을 주장하지 않는다. 이 확인은 신호를 만들거나 수량·가격·target을 바꾸지 않으며 coarse steady poll도 pending deadline에는 짧게 깨운다.
- 위젯 calibration은 메인 봇 또는 에피소드 runtime을 변경하지 않는다.

### 3.5 에피소드 튜닝

- profile·종목·venue·시간창·leg별 제출, fill, target, terminal과 실현비용을 누적한다.
- clean baseline 이후 rolling/cumulative 결과와 최신 거래일 holdout을 사용한다.
- 미청산 episode는 completed EV에서 제외하고 custody 부담과 자본점유를 별도 지표로 보존한다.
- 신규 profile과 기존 profile 변경을 분리하고 exact-date transition hash와 PREOPEN 적용 여부를 확인한다.
- 진입 확인 지연 연구는 완성 1분봉 시각이 아니라 원장에 영속된 실제 `signal_decision_at`만 anchor로 사용한다. 이 값이 없는 legacy episode는 진단에는 남기되 진입시점 정책 표본에서는 제외한다.
- 수량, provider, bot, broker guard와 legacy custody는 자동 calibration 축이 아니다.

## 4. 시작 시 공통 확인

- 메인 봇 PID, 시작 시각, commit, source-dirty, runtime env와 당일 ON/OFF runtime 목록
- 전일 postclose candidate와 당일 PREOPEN apply plan/runtime env/verify의 generation·hash·selection diff, launcher load 시각과 현재 PID의 exact env/policy receipt
- 위젯·에피소드 systemd service/timer, exact-date policy/profile hash와 실제 process 상태
- 당일 PREOPEN apply plan/runtime env, active date, policy version, dependency와 operator override
- 실제 AI provider/failback/timeout/parse 상태와 `provider=none` 발생 여부
- Kiwoom REST/WS 연결, 가격·호가·체결·분봉 freshness와 venue provenance
- 공식 보통주 master에 결속된 독립 시장 전체 `as_of rising benchmark`의 source path·hash·수집 시각·선정 정의·전체 census와 scanner 외부 미관측 종목 재현 가능성
- scanner source fetch/normalize → candidate pool/rank/limit → universe/source guard → watch budget/slot → promotion/WATCHING → runtime attach → fast/heavy evaluation → AI/authority gate의 unique-key count·dedup·unmatched·지연과 최초 미도달 원인 보존식
- scanner-pruned 전수 census와 bounded BBO schedule/observation의 분리, collector active/pending/daily bound, worker/receipt failure, exact route와 full-population 외삽 금지
- Kiwoom 국내주식 token-wide 조회 5회/초, source-only 4/5 reservation, 주문 버킷 분리, HTTP/body-limit shared cooldown과 owner/PID/request-code별 admission/gap provenance
- 현재 계좌 보유, owner별 ledger/custody, 미체결 주문, 주문가능금액과 broker reconciliation
- 재기동이 별도로 허용된 실행에서만 재기동 전후 broker 미체결·전시장 잔고가 동일한지, `manual_operator` 및 독립 machine 주문을 취소·중복제출·흡수하지 않았는지
- KRX, `PREMARKET_KRX_LIKE`, NXT의 source·route·session 분리
- main/widget/episode별 order ID, trace/snapshot/episode/profile/leg lineage의 연결 가능 여부
- micro observer canary freshness·latency·queue/drop/error·writer·disk 상태와 당일 source-only collection target의 실제 WS 반영
- limit-down natural target/REG receipt, required·requested realtime type 0B+0D, type별 first-data·sequence와 ordered-path downstream lineage
- R0→R3 단계별 최신 artifact, current Provider 실행 여부·budget, lifecycle exact terminal join과 각 단계 blocker
- 구현됐지만 현재 PID/process/policy에 미반영된 변경과 rollback 값
- clean baseline 이전 데이터가 rolling/EV/runtime 판정에 혼입되지 않았는지
- runbook/설치 cron·systemd/tmux registry가 선언한 expected process별 MainPID/cgroup/lock/heartbeat, 최근 progress marker, output과 실제 consumer

## 5. 당일 runtime 판정

당일 runtime과 policy는 이름이나 로그 존재만으로 정상 판정하지 않는다. 실제 owner·stage·eligible 표본에 연결해 다음 상태로 분류한다.

- 정상 호출·의도한 효과 확인
- ON이지만 자연 표본 없음
- ON이지만 호출되지 않음
- 호출됐지만 입력·venue·policy·provenance 결손
- 과차단·과제출·익절 지연·조기청산·손실 확대
- 구현됐지만 현재 PID/process/policy 미반영
- source-only 정상 관측이며 실주문 효과 없음
- OFF·은퇴 상태로 현재 검증 모집단 아님
- not_yet_due|bounded_wait
- dead_expected_process|hung_or_stale|crash_or_restart_loop|duplicate_owner|no_op_success|orphan_producer|unconsumed_artifact|unknown_contract

blocked 상태는 `source_quality`, `sample_floor`, `external_opportunity_denominator`, `scanner_recall_instrumentation`, `scanner_discovery`, `watch_budget_or_slot`, `post_promotion_handoff`, `submit_drought`, `env_mapping`, `runtime_hook`, `post_apply_attribution`, `AI_review`, `safety_or_broker_guard`, `user_authority`로 분류하고, owner artifact·관측 근거·다음 보완·acceptance test를 각각 기록한다. 단순히 “계약 미완료” 또는 “데이터 부족”으로 종결하지 않는다.

자동연장 runtime은 active key, `enabled=true`, 당일 active date, dependency, policy file/version, launcher/PID 반영과 실제 pass/block/recheck/submit/exit 수를 확인한다. 자동연장은 효용성 승인이나 live 승격 근거가 아니다.

`greenfield_real_environment_authority`는 target-date PREOPEN env가 enable하고 exact policy·promoted bucket·runtime hook·rollback/post-apply lineage가 모두 닫힌 경우에만 현재 PID 권한으로 인정한다. 어느 하나라도 없으면 real action을 fail-closed하며 legacy live 권한으로 묵시 후퇴하지 않는다.

process 이름이나 PID 존재만으로 정상이라고 하지 않는다. `declared owner → installed/enabled trigger → expected window → PID/exit/heartbeat → artifact 또는 valid terminal skip → registered consumer → consumed field → decision/report role`을 연결한다. 예정 시각 전 one-shot 종료, reviewed disabled/retired, eligible input 0이 입증된 valid-empty는 dead/no-op에서 제외한다. 반대로 성공 exit인데 artifact가 없거나 stale하고 consumer receipt도 없으면 `no_op_success`, source를 계속 만들지만 현재 consumer가 없으면 `orphan_producer|unconsumed_artifact`다. 이 판정만으로 process를 kill·disable·restart하지 않는다.

WebSocket error burst는 오류 건수만으로 bot 재기동이나 전략 변경을 실행하지 않는다. exact connection epoch, LOGIN ACK, reconnect/resubscribe, required type별 first data, queue/drop, duplicate writer, stale age와 affected owner를 확인한다. 정상 reconnect 경계는 새 sequence epoch로 분리하고 cross-epoch 0B/0D join을 금지한다. bounded recovery 뒤 first-data가 복구되지 않거나 반복 disconnect가 진행을 막을 때만 runtime incident로 승격한다.

Swing과 은퇴한 opening-rotation·upper-limit rotation·panic-buying 경로는 현재 장중 실주문 SCALPING 검증 모집단에서 제외한다. historical artifact나 compatibility parser 존재를 재기동 가능성으로 해석하지 않는다.

## 6. 표본·모집단 부족과 구조적 고갈 판정

장중 report나 runtime에서 candidate·natural match·BBO·AI request·submit·fill·terminal·mature outcome·net-economic eligible 모집단의 0건 또는 sample floor 미달을 문제로 제시하면 최종 숫자만 보고 기다리지 않는다. owner·family/arm/bucket·stage·venue/session·metric contract·window·floor denominator를 결속한 stable `shortage_id`로 다음 funnel의 최초 고갈 단계를 기록한다.

`raw opportunity/source → source-quality-valid → contract eligible → policy/PREOPEN loaded(필요한 경우) → runtime natural matched(필요한 경우) → authority-declared last consumer/floor-owning stage → submit/fill/terminal/mature/net-economic(계약상 필요한 경우)`

- `time_resolvable_shortage`: producer→intended consumer 경로와 source quality가 정상이고 동일 denominator의 신규 unique 표본이 유입될 수 있으며, maturity와 rolling expiry를 반영해 선언 horizon 안에서 floor에 도달하는 finite 근거가 있는 경우만 사용한다. 무기한 HELD, 유입률 0 또는 양(+) 유입일만 고른 평균은 ETA에 넣지 않는다.
- `structural_population_exhaustion`: impossible predicate, policy/key mismatch, systematic join/exclusion, missing runtime hook/consumer, eligible upstream 뒤 반복되는 0-conversion, 계약상 최대 관측 가능 수가 floor 미만인 경우다. submit drought나 net-economic eligible 0은 upstream 후보가 많다는 이유만으로 시간 해결형이 아니다.
- window/sample floor/maturity/effective horizon 또는 source census가 없어 둘 중 하나를 입증할 수 없으면 `blocked_missing_evidence`, 신규 경로의 선언된 최소 관찰창 전이면 `pending_declared_window`로 둔다. 이는 정상 대기 또는 세 번째 최종 shortage class가 아니다.
- 정상 handoff에서 opportunity 자체가 없는 하루, 다음 PREOPEN 전 candidate, 아직 fixed maturity deadline 전인 row는 구조적 고갈이 아니다. 반대로 구현 파일·schedule receipt·report 생성만으로 구조 보완이 해결됐다고 하지 않는다.
- 구조 보완 후 `collecting_after_structural_repair`는 review finding 0과 fresh PID/consumer receipt가 닫힌 뒤에만 사용한다. `resolved`는 신규 source-quality-valid unique 표본이 같은 corrected path의 first depleted stage를 실제 통과하고 floor/lineage가 닫힐 때만 허용한다.
- 표본을 맞추기 위한 row 복제, owner·venue·session 병합, right-censored/HELD의 completed 변환, pre-baseline 재사용, child provenance 삭제, sample floor 하향, hard-safety·broker guard·threshold 완화는 금지한다.

장중 shortage 판정은 source-only 계측·parser/schema·report·test·instrumentation 보완과 당일/장후 workorder handoff까지만 권한을 가진다. live threshold, provider, bot, cap, 수량, 주문 또는 safety 변경이 필요하면 `user_authority`로 분리한다.

## 7. 보완 원칙

명백한 결함이나 수익기회 병목이 확인되면 다음 루프를 수행한다.

`원인 분리 → 단일 owner 확인 → 최소 보완 → 코드리뷰 → clean-baseline real replay → 결함 보완 → 재리뷰 → 허용된 runtime 반영 → post-apply 귀속`

구조적 결함은 읽기 전용 진단만으로 종료하지 않는다. source-quality·parser/schema·report·test·instrumentation·sim/source-only 범위의 보완은 원인을 확인한 뒤 구현하고 review gate를 닫는다. 실주문 권한, PREOPEN live env 선택, provider route, bot process, cap, broker/order guard, hard/protect/emergency safety 또는 장중 threshold mutation은 별도 사용자 지시나 유효한 적용 artifact 없이는 변경하지 않는다.

- hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown을 우회하지 않는다.
- KRX, `PREMARKET_KRX_LIKE`, NXT 성과를 혼합하지 않는다.
- main/widget/episode의 주문·수량·보유·청산 owner를 공유하거나 파편화하지 않는다.
- full fill과 partial fill, completed와 active/HELD, real과 sim/source-only, 실현손익과 counterfactual을 합산하지 않는다.
- 정상 진입 미달을 곧바로 기회 없음으로 해석하지 않되 hard-negative를 작은 목표라는 이유로 완화하지 않는다.
- 후단 submit 차단이 적정해도 상위 scanner 포착률 감사를 닫지 않는다. 독립 market-wide 분모가 없으면 정상으로 간주하지 말고 instrumentation gap을 먼저 닫는다.
- threshold/runtime 변경은 동일 stage의 기존 bounded owner 한 축, before/after, 근거, active date와 rollback을 기록한다.
- 일별 mature 표본은 cumulative ledger에 누적하되 1건으로 실주문 권한·hard safety·수량을 자동 변경하지 않는다.
- source-quality 결손은 계측·report·provenance 보완으로 먼저 닫고 결손값을 0 또는 정상으로 보간하지 않는다.
- baseline 이후 hard contract gap은 식별 가능한 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 날짜 전체 차단은 preflight artifact missing/invalid, exclusion 생성 실패 또는 high-volume no-contract 결손을 안정적으로 분리할 수 없을 때만 사용한다. unknown-token finding만으로 날짜 전체를 차단하지 않되 producer/schema review와 workorder handoff는 남긴다.
- 코드 변경 후 review finding 0과 targeted validation 전에는 재기동·비싼 report 재생성·runtime apply를 하지 않는다.
- 재기동이 허용된 경우에도 먼저 main/widget/episode/manual owner별 broker 미체결과 전시장 inventory를 대사하고, 우아한 종료·새 PID env verify·WS login/first-data·canary·중복주문 0건을 사후 확인한다.
- 키움 최초 WS 수신 전 외부 지연은 코드 결함 원인에서 제외하되 최초 수신 이후 내부 queue·scanner·AI·submit 지연은 측정한다.

## 8. 보고

각 항목은 `판정 → 근거 → 다음 액션` 순서로 보고한다.

마지막에는 반드시 다음을 분리한다.

- 종목탐색: 독립 `as_of rising benchmark`의 정의·source/hash·분모, discovery·post-promotion consumption·downstream conversion의 독립 분모, scanner source/watch/promotion/fast·heavy evaluation/AI/candidate 단계별 recall·지연·최초 미도달 원인, scanner 밖 미관측 종목의 executable outcome과 최종 판정 상태
- scanner-pruned observer: 전수 prune census와 bounded schedule/observation 표본, active/pending/request bound, token-wide 5/sec·source-only 4/5 reservation, exact route·BBO freshness·rate-limit/local-defer gap, resolved/right-censor/coverage floor와 full-population 외삽 금지
- 메인 봇: 상위 탐색 결과와 후단 submit drought를 분리한 놓친 수익기회, 적정 차단, probe/residual/scale-in, 매도와 post-sell
- 위젯: signal·episode·fill·target·terminal, 비용 차감 EV, owner/custody 정합성
- 에피소드: profile/leg별 제출·체결·target·COMPLETE/HELD/BLOCKED와 실현비용
- micro-reversion: 상태별 후보, ask depletion/refill/체결 귀속, recheck, passive fill feasibility, target/adverse first-hit, tail loss, canary·disk 상태와 현재 runtime authority
- limit-down: natural target/REG, ordered 0B+0D type별 receipt·sequence·same-session lineage, `collecting_after_structural_repair` 또는 resolved acceptance와 runtime authority
- AI 판단 품질: 호출·입력·판단, R0→R3 단계별 생성/차단, exact replay, downstream submit/holding/exit 결과
- smoothing: raw 대비 action 안정성, whipsaw 감소와 지연·손익 훼손 여부
- 당일 runtime별 정상·결함·자연 표본 부족·미호출·미반영·source-only 상태
- owner 충돌, 중복 주문, broker reconciliation과 venue provenance 결함
- 적용한 보완, 현재 process 반영 여부와 rollback 조건
- process 감사: authoritative expected set, PID/cgroup/lock/heartbeat, dead·hung·duplicate·no-op·orphan·unconsumed 분류와 valid-empty 오탐 제외
- 부족 ledger: stable `shortage_id`, exact floor denominator, required/current/deficit, first depleted stage, funnel count, `time_resolvable_shortage|structural_population_exhaustion|blocked_missing_evidence|pending_declared_window`, finite ETA 또는 waiting 불가 이유, 다음 due·재분류 trigger·acceptance test
- 아직 해결되지 않은 병목, 다음 표본·재검증·구현 owner

보고서나 runtime 이름의 존재는 효과의 증거가 아니다. `identified → source quality → 당일 PREOPEN/PID 실제 owner/runtime 소비 → executable 체결·terminal outcome → 비용 차감 rolling/cumulative EV → post-apply attribution`이 연결됐을 때만 당일 정상 효과로 판정한다. 장중 생성된 장후/다음-session source-only artifact는 authority에 맞는 intended last consumer와 handoff까지만 보고하고 다음 PREOPEN/PID 소비나 실주문 효과를 선행 주장하지 않는다.
