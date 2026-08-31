# 장중 수익극대화 모니터링 작업지시문

작성 기준: `2026-08-31 KST`

현재 가동 중인 키움증권 연동 SCALPING 런타임을 대상으로 EV와 누적 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다. 메인 봇, 위젯 매매기계, 에피소드 매매기계는 서로 독립된 주문 owner로 평가하며 주문번호·보유수량·청산 귀속을 혼합하지 않는다.

현재 튜닝 원칙과 active/open 상태는 `docs/plan-korStockScanPerformanceOptimization.rebase.md`, 실행 항목은 당일 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실제 기동 권한은 검증된 당일 PREOPEN runtime env와 exact-date machine policy를 기준으로 한다. 이 문서의 family 예시는 고정 ON 목록이나 재기동 권한이 아니다.

이 문서는 장중 반복 실행 절차다. 매 실행 시작 시 고정 예시를 신뢰하지 말고 현재 PID env, 당일 runtime verify, exact-date policy, broker 계좌·미체결, systemd process/timer와 최신 source-quality artifact를 다시 읽는다. 코드가 구현돼 있거나 전일 추천에 나타났다는 사실만으로 현재 process 반영 또는 실주문 권한을 인정하지 않는다.

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

단순 가동, 후보 수, 승률 또는 gross MFE가 아니라 실제 체결 가능성, 수수료·세금·spread·slippage를 반영한 EV와 순이익을 최종 기준으로 삼는다. `2026-08-18` 이후 R0→R3 비교 경제성은 매수 수수료 1.5bps, 매도 수수료 1.5bps, 매도 세금 20bps, Provider 비용 0원인 effective-dated 정책 계약을 사용하고, 공식 KOSPI/KOSDAQ master에서 보통주로 확인된 종목만 포함한다. exact broker receipt 손익·비용은 실거래 reconciliation 근거로 별도 보존하되 R0→R3 고정 비교비용을 암묵적으로 대체하지 않는다. 비용모델·master의 effective date 또는 source hash가 맞지 않으면 EV 입력을 차단한다.

## 2. 매매기계별 모니터링 범위

### 2.1 메인 봇 매매기계

메인 봇은 시장 전반을 스캔해 새로 나타나는 스캘핑 기회를 찾고 `selection → entry → submit → probe/residual → holding → scale_in → exit` 전체 lifecycle을 소유한다.

다음 흐름을 후보·주문·체결·보유변화·매도마다 재구성한다.

`시장·universe source → scanner source fetch/normalize → candidate pool/rank/limit → eligibility/source guard → watch budget/slot reservation → scanner promotion/WATCHING → runtime attach → fast precheck → heavy evaluation → entry AI trace/provider/trusted decision → authority gate → entry-price AI → submit guard → 선택된 bounded mode의 probe 또는 normal sizing → residual multi-leg → holding/scale-in → partial TP/trailing/exit → broker reconciliation`

확인 항목:

- 감시 슬롯·candidate/TP1·freshness·AI·latency·micro·tick-speed·가격·계좌·주문·수량·cooldown 중 최초 차단 owner와 직접 원인
- score가 baseline prior/feature로만 사용되고 단독 BUY 또는 단독 DROP 권한이 되지 않았는지
- 당일 선택된 mode에서만 probe-first가 적용됐고, one-share exploration이면 1주 cap과 일일 ledger를 지켰으며, probe 체결 뒤 fresh BBO와 방향을 다시 확인했는지
- residual 가격·수량·제출 시점과 취소가 bundle 및 broker 상태와 일치하는지
- 주문 API 응답과 WS execution receipt의 도착 순서가 바뀌어도 exact 주문번호와 immutable owner로 결속됐는지, 취소·reprice 전에 원주문 terminal absence와 KRX/NXT 전체 잔고가 확인됐는지
- continuation에서 pyramid가 과차단되지 않았고 하락 구간의 avg-down이 불리한 노출만 키우지 않았는지
- 부분익절·runner·trailing·hard/protect/emergency owner의 실행 순서와 실제 체결 지연
- 매도 후 1·3·5·10·20·30·60분 반사실을 실현손익과 분리했는지

`position_sizing_dynamic_formula`가 메인 봇 신규·추가매수 수량의 단일 owner다. micro-reversion 또는 AI 판단이 수량·broker guard·hard safety를 직접 바꾸지 않는다.

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

#### 메인 봇 risky micro-reversion 관측

`risky micro episode`는 독립 에피소드 매매기계가 아니다. 메인 봇 normal-entry에서 soft-block된 후보 중 passive 체결과 짧은 보유로 비용 차감 후 작은 순수익을 얻을 가능성을 재검사하는 `micro-reversion` 관측·handoff 분류다.

- stale/conflict, broker/account/order/quantity/cooldown, 명백한 adverse tape와 비경제적 spread는 `hard_negative`로 유지한다.
- fresh executable BBO와 회복 가능성이 남은 후보는 `recheckable_soft_risk`로 짧게 재검사한다.
- passive fill 가능성, 제한된 spread, 짧은 positive micro support와 비용 초과 목표가 확인된 후보만 `cost_aware_micro_candidate`로 분류한다.
- source-only 후보는 주문하지 않는다. 승인된 bounded runtime이 있더라도 기존 submit guard와 probe-first owner로만 handoff한다.
- risky tag 자체는 residual, scale-in, 주문취소 또는 청산 권한이 아니다. continuation 확인 후 기존 normal owner로 재분류된 경우에만 잔량 확대를 검토한다.

`bid+1`, TTL 3·5·10초, 제한적 ask 진입은 source-only 반사실로 비교한다. fresh executable bid/ask, quote age, tick size, fill feasibility, 총비용, 3·10·20·30초 및 1·3·5분 target/adverse first-hit, timeout executable exit와 tail loss를 같은 lineage로 연결한다. 충분한 거래일과 실제 filled-terminal 표본 전에는 실주문 승격 근거로 쓰지 않는다.

현재호가의 매도잔량 감소는 단독 상승 신호로 사용하지 않는다. `0D` 호가와 `0B` 체결을 같은 venue·symbol·session의 local-receive 시간창으로 결속하고 각 stream의 monotonic sequence를 독립 검증해 현재 ask depletion 속도, 상위 ask 1~5호가 잔량 기울기, refill/replenishment, 매도호가 취소와 실제 공격적 매수체결의 구분, spread·BBO age, bid 지지와 가격 반응을 함께 본다. 빠른 depletion 뒤 refill 또는 bid 붕괴가 발생하면 false-positive로 보존한다. 이 축은 observer/source-only이며 검증된 policy candidate 전에는 BUY·수량·취소·청산 권한이 없다.

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

기본 live scalping AI route와 endpoint별 예외는 당일 runtime env를 기준으로 검증한다. AI를 사용하지 않는 위젯·에피소드 경로에 억지로 provider 정상성 판정을 요구하지 않는다.

### 3.3 Smoothing

Smoothing은 순간 tick·호가·OFI/QI 흔들림으로 action이 왕복하는 것을 줄이는 공통 품질축이며 별도 주문 owner가 아니다.

- live `holding_flow_ofi_smoothing`은 raw/smoothed score, EWMA state, persistence count, snapshot age, policy version과 최종 action을 함께 남긴다.
- stale snapshot, observer unhealthy 또는 입력 부족이면 smoothed 값을 사용하지 않는다.
- smoothing 적용 전후 holding·partial TP·trailing·exit 지연과 post-sell MFE/MAE를 비교한다.
- whipsaw 감소와 함께 늦은 손절, 이익반납, 진입 지연이 늘지 않았는지 확인한다.
- source-only smoothing 대안은 real action을 바꾸지 않으며 rolling/cumulative EV와 exact-path 반사실로만 판정한다.

### 3.4 위젯 튜닝

- 종목·venue·setup별 signal-to-fill, fill-to-target, target completion time과 비용 차감 EV를 누적한다.
- entry price, target tick, cooldown, 완료 episode 상한 후보를 동일 policy version의 Control과 비교한다.
- source-quality, 미체결, partial fill, 미청산 custody와 실제 terminal sample을 분리한다.
- exact-date policy와 rollback이 있는 단일 bounded axis만 다음 PREOPEN 후보가 될 수 있다.
- `micro_entry_confirmation`은 clean-baseline exact owner·symbol·session·entry-state와 실제 완료 outcome을 누적해 `0/1/3/5초` 진입 확인 지연만 고를 수 있다. 당일 completed holdout, 20 completed outcome, 5/10/20일 비용차감 EV, BBO/depth·0B/0D source-quality, delayed-entry feasibility 90%, completed paired coverage 95%, right-censored 20% 이하 floor를 모두 통과한 전체 owner 중 한 scope만 다음 exact-date policy에 반영하고, 미달이면 즉시진입 `0초`를 유지한다. 지연 뒤에는 같은 원천 signal과 기존 entry guard를 전부 다시 확인하며 coarse steady poll도 pending deadline에는 짧게 깨운다.
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
- 위젯·에피소드 systemd service/timer, exact-date policy/profile hash와 실제 process 상태
- 당일 PREOPEN apply plan/runtime env, active date, policy version, dependency와 operator override
- 실제 AI provider/failback/timeout/parse 상태와 `provider=none` 발생 여부
- Kiwoom REST/WS 연결, 가격·호가·체결·분봉 freshness와 venue provenance
- 공식 보통주 master에 결속된 독립 시장 전체 `as_of rising benchmark`의 source path·hash·수집 시각·선정 정의·전체 census와 scanner 외부 미관측 종목 재현 가능성
- scanner source fetch/normalize → candidate pool/rank/limit → universe/source guard → watch budget/slot → promotion/WATCHING → runtime attach → fast/heavy evaluation → AI/authority gate의 unique-key count·dedup·unmatched·지연과 최초 미도달 원인 보존식
- 현재 계좌 보유, owner별 ledger/custody, 미체결 주문, 주문가능금액과 broker reconciliation
- 메인 봇 재기동 전후 broker 미체결·전시장 잔고가 동일한지, `manual_operator` 및 독립 machine 주문을 취소·중복제출·흡수하지 않았는지
- KRX, `PREMARKET_KRX_LIKE`, NXT의 source·route·session 분리
- main/widget/episode별 order ID, trace/snapshot/episode/profile/leg lineage의 연결 가능 여부
- micro observer canary freshness·latency·queue/drop/error·writer·disk 상태와 당일 source-only collection target의 실제 WS 반영
- R0→R3 단계별 최신 artifact, current Provider 실행 여부·budget, lifecycle exact terminal join과 각 단계 blocker
- 구현됐지만 현재 PID/process/policy에 미반영된 변경과 rollback 값
- clean baseline 이전 데이터가 rolling/EV/runtime 판정에 혼입되지 않았는지

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

blocked 상태는 `source_quality`, `sample_floor`, `external_opportunity_denominator`, `scanner_recall_instrumentation`, `scanner_discovery`, `watch_budget_or_slot`, `post_promotion_handoff`, `submit_drought`, `env_mapping`, `runtime_hook`, `post_apply_attribution`, `AI_review`, `safety_or_broker_guard`, `user_authority`로 분류하고, owner artifact·관측 근거·다음 보완·acceptance test를 각각 기록한다. 단순히 “계약 미완료” 또는 “데이터 부족”으로 종결하지 않는다.

자동연장 runtime은 active key, `enabled=true`, 당일 active date, dependency, policy file/version, launcher/PID 반영과 실제 pass/block/recheck/submit/exit 수를 확인한다. 자동연장은 효용성 승인이나 live 승격 근거가 아니다.

Swing과 은퇴한 opening-rotation·upper-limit rotation·panic-buying 경로는 현재 장중 실주문 SCALPING 검증 모집단에서 제외한다. historical artifact나 compatibility parser 존재를 재기동 가능성으로 해석하지 않는다.

## 6. 보완 원칙

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
- 코드 변경 후 review finding 0과 targeted validation 전에는 재기동·비싼 report 재생성·runtime apply를 하지 않는다.
- 재기동이 허용된 경우에도 먼저 main/widget/episode/manual owner별 broker 미체결과 전시장 inventory를 대사하고, 우아한 종료·새 PID env verify·WS login/first-data·canary·중복주문 0건을 사후 확인한다.
- 키움 최초 WS 수신 전 외부 지연은 코드 결함 원인에서 제외하되 최초 수신 이후 내부 queue·scanner·AI·submit 지연은 측정한다.

## 7. 보고

각 항목은 `판정 → 근거 → 다음 액션` 순서로 보고한다.

마지막에는 반드시 다음을 분리한다.

- 종목탐색: 독립 `as_of rising benchmark`의 정의·source/hash·분모, discovery·post-promotion consumption·downstream conversion의 독립 분모, scanner source/watch/promotion/fast·heavy evaluation/AI/candidate 단계별 recall·지연·최초 미도달 원인, scanner 밖 미관측 종목의 executable outcome과 최종 판정 상태
- 메인 봇: 상위 탐색 결과와 후단 submit drought를 분리한 놓친 수익기회, 적정 차단, probe/residual/scale-in, 매도와 post-sell
- 위젯: signal·episode·fill·target·terminal, 비용 차감 EV, owner/custody 정합성
- 에피소드: profile/leg별 제출·체결·target·COMPLETE/HELD/BLOCKED와 실현비용
- micro-reversion: 상태별 후보, ask depletion/refill/체결 귀속, recheck, passive fill feasibility, target/adverse first-hit, tail loss, canary·disk 상태와 현재 runtime authority
- AI 판단 품질: 호출·입력·판단, R0→R3 단계별 생성/차단, exact replay, downstream submit/holding/exit 결과
- smoothing: raw 대비 action 안정성, whipsaw 감소와 지연·손익 훼손 여부
- 당일 runtime별 정상·결함·자연 표본 부족·미호출·미반영·source-only 상태
- owner 충돌, 중복 주문, broker reconciliation과 venue provenance 결함
- 적용한 보완, 현재 process 반영 여부와 rollback 조건
- 아직 해결되지 않은 병목, 다음 표본·재검증·구현 owner

보고서나 runtime 이름의 존재는 효과의 증거가 아니다. `identified → 실제 owner/runtime 소비 → 체결·terminal outcome → rolling/cumulative EV → post-apply attribution`이 연결됐을 때만 정상 효과로 판정한다.
