# 장중 수익극대화 모니터링 작업지시문

작성 기준: `2026-09-08 KST`

절차 보완: `2026-09-10 KST` — §4.3 장중 수집 결손 즉시 대응 추가. 아래 과거 운영 현황의 날짜를 갱신하거나 현재 PID·수집 정상성을 인증한 기록은 아니다.

현재 가동 중인 키움증권 연동 SCALPING 런타임을 대상으로 EV와 누적 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다. 메인 봇, 위젯 매매기계, 에피소드 매매기계는 서로 독립된 주문 owner로 평가하며 주문번호·보유수량·청산 귀속을 혼합하지 않는다.

이 지시문에 따른 모니터링을 명시적으로 요청했을 때만 아래 점검·허용 범위 보완 절차를 실행한다. 문서 인용·열람·현행화는 실행 요청이 아니며, 단순 상태 조회·읽기 전용 검증도 구현이나 재생성을 자동 승인하지 않는다. 문서 수정만 요청받으면 운영 산출물·PID·env·주문을 변경하지 않는다.

명시적 모니터링에는 §4.1의 **현재 시각까지 도래한 체크리스트 실행·점검**을 포함한다. 최신 결과가 있으면 수용조건까지 대사하고, 미실행인 허용 작업은 선행 조건·권한·중복 실행 여부를 확인한 뒤 수행한다. 실행 가능한 항목을 목록 제시만으로 끝내지 않되, 단회/지속 요청의 범위와 종료조건을 보존한다.

명시적 모니터링 중 장중 수집 결손을 발견하면 §4.3에 따라 **같은 실행에서 원인 확인 → 허용된 최소 수리 → review/fix → 검증**을 수행한다. 이미 허용된 source-only 보완은 항목마다 별도 재지시를 기다리거나 장후 workorder 발행까지 미루지 않는다. 코드 수정과 현재 process 반영은 별개이며, 재기동·실주문·API 호출량 상향 권한을 추가하는 조항은 아니다.

현재 튜닝 원칙과 active/open 상태는 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8, 실행 항목은 당일 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 `docs/time-based-operations-runbook.md`, producer/consumer와 R0→R6 의존 순서는 `docs/report-based-automation-traceability.md`를 기준으로 한다. 실제 기동 권한은 검증된 당일 PREOPEN apply plan/runtime env/verify와 exact-date machine policy, 이를 읽은 현재 PID의 provenance를 함께 기준으로 한다. 이 문서의 family 예시는 고정 ON 목록이나 재기동 권한이 아니다.

이 문서는 장중 반복 실행 절차다. 매 실행 시작 시 고정 예시를 신뢰하지 말고 현재 PID env, 당일 runtime verify, exact-date policy, broker 계좌·미체결, 설치된 cron/systemd/tmux owner와 최신 source-quality artifact를 다시 읽는다. 코드가 구현돼 있거나 전일 추천에 나타났다는 사실만으로 현재 process 반영 또는 실주문 권한을 인정하지 않는다. 전일 장후 candidate는 당일 PREOPEN handoff 입력일 뿐이고, 당일 apply plan/runtime env/verify와 launcher/PID load receipt가 닫히기 전에는 적용 또는 효과로 보고하지 않는다. runbook·traceability·설치 trigger·실행 snapshot의 단계, 조건 또는 owner가 다르면 mtime이나 우연한 실행 사실로 한쪽을 선택하지 않고 `contract_drift`로 fail-closed한다.

### 현행 운영 우선순위 (`2026-09-08`)

장중 상세 분석 자원은 다음 순서로 사용한다.

1. 메인 봇 실거래: 독립 시장 상승 모집단 대비 scanner 포착률, Entry AI 입력·판단, entry price, submit, 체결, holding/exit, AVG_DOWN/PYRAMID 및 비용 차감 실제 EV
2. 독립 실주문 owner: 위젯, Samsung 오전·정오·오후와 저가주 two-leg profile의 exact-date policy, 주문번호, custody, target/terminal 및 자본점유
3. 공통 품질: broker reconciliation, 주문·체결 receipt, WS/REST freshness, process/heartbeat, source-quality, microstructure 전달과 Main AI R0→R3 프롬프트 개선 원천

Scalping Entry ADM, Holding/Exit ADM, statistical action weight, LDM policy/runtime, lifecycle AI context/attribution, bucket discovery/refinement, LDM-derived sim scale-in/runtime bridge와 `greenfield_real_environment_authority`는 `scalping_adm_ldm_retirement_20260906`에 따라 영구 퇴역이다. `institutional_flow_context`와 독립 latency recommendation도 퇴역했다. Swing은 OFF이고 bucket/LDM/arm 분석 대상이 아니다. scalp/swing sim 성과 튜닝은 현재 장중 우선작업이 아니며, 실주문 권한 누출·broker 호출·리소스 간섭·퇴역 env 재활성화 여부만 최소 확인한다. historical artifact, 호환 parser 또는 표본 0을 근거로 이 영역의 재생성·수리·ETA·승격 작업을 열지 않는다.

9/7 기동·병합 receipt는 [전일 체크리스트](./checklists/2026-09-07-stage2-todo-checklist.md)의 완료 기록이다. 특정 과거 PID·commit·선택 family 수를 현재 가동의 기대값으로 고정하지 않는다. 현재 runtime code/hash와 문서-only 변경, 실제 배포와 자연 소비를 분리하고 매 실행의 exact-date receipt를 확인한다.

### 현행 handoff와 자연 확인 owner

아래는 [9/8 체크리스트](./checklists/2026-09-08-stage2-todo-checklist.md)의 기존 항목을 연결한 문서 기준이며 현재 가동 검증 결과가 아니다. 같은 ID를 중복 생성하거나 전일 완료 검토를 다시 OPEN하지 않는다.

| 영역 | 장중 확인할 연결·남은 경계 | 기존 acceptance owner |
| --- | --- | --- |
| 전일 장후 요약 | source-date 9/7의 tower→마지막 checklist→strict verifier→controller와 오늘 PREOPEN/PID를 분리. 요약 PASS는 오늘 정책 적용이 아님 | `PostcloseRecoverySourceAcceptance0908` |
| Entry recheck / submit drought | 9/8 cache12/report6/exact3·call-local frozen parent→유효 최근3거래일→controller v4/source binding→strict/PREOPEN/PID. 구 schema5/exact2와 과거 원천 결손을 재라벨링하지 않음 | `EntryRecheckNaturalAttribution0907` (9/8로 같은 ID 이관) |
| Scanner lookup-attention | resource v2/decision v4의 자연 source·경쟁 pair·immutable receipt·PID/R6. marginal CF와 실제 full-fill EV 분리 | `ScannerLookupAttentionNaturalEvidence0908` |
| Main AI / micro source | #76→#82 v5→frozen optimizer→provider0 metadata binding→consumer와 새 exact 원천. metadata terminal은 Provider 비교·live 승격이 아님 | `AIDecisionActionOutcomeNaturalEvidence0908`, `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908` |
| 위젯·저가주 승인 적용 | widget080220와 low-price 기존8/신규3의 9/8 policy/설치 receipt 이후 자연 preflight·PID·신호·custody·실현 EV 확인 | `WidgetEpisodeRecommendationApplyAcceptance0908` |
| Machine timing | 검증된 9/7 ingress loss 격리·immediate baseline carry와 다음 exact ordered/route/epoch source 분리. 과거일 반복 재실행 금지 | `MachineLifecycleTurnoverObjectiveFollowup0908`, `PostcloseRecoverySourceAcceptance0908` |
| 품질·WS·원본 보존 요약 | #74 audit v2와 #89 독립 finalize의 진단/rolling 경제성 분리, #73 manifest·timing receipt의 자연 소비. 장중 감사 완료와 다음 원천/장후 최종 감사는 별도 | `PostcloseSourceQualityGateReview0908`, `PipelineVerbosityNaturalEvidence0908` |
| Pattern/Daily 소액 순이익 | #67/#69 exact source/currentness/AI receipt→기존 Daily owner·PREOPEN. 연구 proxy·실제 비용·선택·실수익 분리 | `PatternLabSmallNetNaturalEvidence0908`, `DailyThresholdNaturalAcceptance0908` |
| 전략 lock 승계 | 별도 승인된 첫 effective 9/9의 기존 owner·승계 receipt·PREOPEN 검증. 잔여 경제성 owner 2개는 OPEN이며 장중 lock 해제 권한 없음 | `OperatorPolicySuccessionAcceptance0908` (Due 9/9) |

근거는 [장후 우선순위 복구 리뷰](./audit-reports/2026-09-08-postclose-priority-repair-review.md)와 [별도 승인 위젯·에피소드 적용 리뷰](./audit-reports/2026-09-07-widget-episode-recommendation-implementation-review.md)다. #8/#9 및 #11/#119/#23/#49의 완료된 수리는 새 결함·계약 변경·필수 handoff 실패가 입증될 때만 재개한다.

9/8 오후 후속 근거는 [15:00 관찰·call-local parent 수리](./audit-reports/2026-09-08-intraday-monitoring-1500.md)와 [15:45~16:10 due 실행·custody 복구](./audit-reports/2026-09-08-due-checklist-custody-recovery-review.md)다. 후자의 15:51 원천 감사·결손1행 격리는 `IntradaySourceQualityGateCheck0908`의 완료 기록이며 이후 유입 원천 전체를 승인하지 않는다. 4개 HELD 원장 및 SamsungE&A 공통 registry 복구는 별도 사용자 지시에 따른 과거 영수증 귀속으로, 일반 모니터링의 자동 state 수정 권한이나 새 수익이 아니다. 당시 PID682672·runtime verify PASS와 신규 parent 계측 미반영, 16:00:56 main submit0·Widget/Micro/Runtime OPEN을 분리한다. 후속 모니터링에서는 최신 receipt로 다시 판정하며 이 숫자를 현재값으로 고정하지 않는다.

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
10. 예정된 현재-owner process와 source-only observer가 실제로 살아 있고 의미 있는 output과 consumer를 가지며 dead·hung·duplicate·no-op·orphan 상태가 아닌가?
11. 현재 우선 owner의 후보·BBO·submit·terminal·mature·net-economic 표본 0 또는 floor 미달은 시간이 해결하는 부족인가, key/hook/consumer 단절로 모집단이 구조적으로 고갈된 것인가? 퇴역·OFF·비우선 sim의 0건은 shortage가 아니다.
12. 당일 실제로 소비된 입력의 효과와 장중 생성되어 장후/다음 PREOPEN으로 넘길 source-only 산출물을 서로 다른 시간축과 authority로 보고했는가?

단순 가동, 후보 수, 승률 또는 gross MFE가 아니라 실제 체결 가능성, 수수료·세금·spread·slippage를 반영한 EV와 순이익을 최종 기준으로 삼는다. `2026-08-18` 이후 R0→R3 비교 경제성은 매수 수수료 1.5bps, 매도 수수료 1.5bps, 매도 세금 20bps, Provider 비용 0원인 effective-dated 정책 계약을 사용하고, 공식 KOSPI/KOSDAQ master에서 보통주로 확인된 종목만 포함한다. exact broker receipt 손익·비용은 실거래 reconciliation 근거로 별도 보존하되 R0→R3 고정 비교비용을 암묵적으로 대체하지 않는다. 비용모델·master의 effective date 또는 source hash가 맞지 않으면 EV 입력을 차단한다.

실현손익 headline은 같은 owner·거래 집합·terminal·실제 비용으로 대사한다. 미대사/결측이면 `null`과 `realized_pnl_status` 등 직접 사유를 남기고 0원·gross EV·다른 cohort 손익으로 메우지 않는다. 건수 일치만으로 exact 비용 검증을 승인하지 않는다. 9/7 NXT 두 거래의 +453원처럼 과거 체결·손익 귀속을 복원한 것은 데이터 수리 효과이며 오늘 새 수익이나 튜닝의 인과적 개선량이 아니다.

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
- 같은 submit 호출 중 scanner promotion이 바뀌어도 call-local `entry_submit_attempt_parent_promotion_id`와 종료 이벤트가 처음 유효 parent에 결속되는지. 새 계측의 파일 존재와 현재 PID의 자연 receipt를 분리하고, 과거 parent/terminal 결손을 합성하지 않는지
- continuation에서 pyramid가 과차단되지 않았고 하락 구간의 avg-down이 불리한 노출만 키우지 않았는지
- `avg_down_route_arbitration_observed` v2의 CF route 관찰을 실제 ADD/NO_ADD·주문·체결로 오인하지 않았는지. exact identity/schema/source-only authority 검증 후에만 관찰로 분리하며, order authority가 true/unknown인 잘못된 행은 계속 결손으로 유지했는지
- 부분익절·runner·trailing·hard/protect/emergency owner의 실행 순서와 실제 체결 지연
- `entry_cancel_wait_runtime`이 퇴역한 ADM/LDM과 분리된 독립 주문취소 owner인지. 당일 PREOPEN 적용된 standard/breakout/pullback/reserve cancel wait만 주문취소 owner이고 entry-price AI `max_wait_sec`는 advisory라서 live cancel timeout을 직접 덮지 않는지
- SCALP preset +1.5% TP가 더 이상 profit-taking owner가 아니며, 신규·복구 holding의 legacy preset TP ref가 취소/disabled된 뒤 `scalp_trailing_take_profit` 경로가 이익 실현을 소유하는지. `SCALP_PRESET_TP` 호환 필드는 stop-safety provenance 외 새 주문 권한을 만들지 않는지
- 매도 후 1·3·5·10·20·30·60분 반사실을 실현손익과 분리했는지

`position_sizing_dynamic_formula`가 메인 봇 신규·추가매수 수량의 단일 owner다. 현재 선택 계약 `entry_type_5stage_cap25_v1`은 source-count/time/venue로 `10%/15%/20%/25%/25%` tier를 고르고 절대 25% cap, 95% safe budget과 최소 1주 floor를 유지하며 scale-in은 최초 tier를 재사용한다. NXT·unknown venue·invalid/missing source·복구 불가능한 최초 entry context는 tier 1로 fail-closed한다. `wait6579_ev_cohort`는 raw/source-quality provenance일 뿐이고 historical LDM 또는 은퇴한 독립 entry bridge 권한이 아니다. micro-reversion 또는 AI 판단은 수량·broker guard·hard safety를 직접 바꾸지 않는다. 실제 값은 당일 PREOPEN verify와 현재 PID receipt로 다시 확인한다.

9/7 PREOPEN에서 구 controller v3 때문에 recheck가 제외됐던 것은 과거 receipt다. 9/8에는 현행 v4·새 exact history와 target-date selection diff, 의존 probe, launcher/PID 소비를 다시 대사한다. 읽기 전용 candidate-ready나 전일 수리 완료만으로 ON을 주장하지 않는다. `entry_split_order_plan`도 당일 후보·선택 사유가 `hold_sample`이면 강제 적용하지 않는다. One-share/rising-missed source 관측과 Entry recheck 실적용은 별도 분모이며 현재 owner는 9/8 checklist의 `EntryRecheckNaturalAttribution0907`이다.

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
- 메인 봇·에피소드·수동 보유수량을 위젯이 매도하거나 자기 custody로 흡수하지 않았는지. 승인된 machine 공존 정책은 단순 타 owner 보유와 분리하되, user/manual/generic/env/auto veto와 계좌·주문 guard보다 우선하지 않는지
- expansion recommendation이 `implementation_review_ready`, sample/trading-date/spread/volatility floor와 exact-date handoff를 통과했는지; `research_watch` 등록 또는 collector 가동만으로 policy mutation이나 매매 승격을 주장하지 않았는지

9/8 승인된 widget080220는 exact-date policy/loader receipt와 이후 실제 collector·trader 소비를 분리한다. 기존 프로세스의 날짜 경계 dynamic catalog 갱신을 재기동 필요성으로 오인하지 않는다. collector 08:57 예약은 가동 성공이 아니며 현재 PID/정책/신호 receipt로 확인한다. 나머지 `research_watch` 7건과 미달 signal 후보를 승인 범위에 포함하지 않는다.

위젯의 효율은 후보 수가 아니라 completed episode의 비용 차감 EV, 목표 완료시간, 자본점유시간, 반복 가능성과 owner 정합성으로 평가한다.

### 2.3 에피소드 매매기계

에피소드 매매기계는 특정 종목·venue·시간창의 반복 패턴을 exact-date profile과 독립 process/state/ledger로 집행한다. 현재 삼성전자 시간대 기계와 저가주 two-leg profile을 대표 owner로 본다.

`2026-09-08` 적용 리뷰 기준 저가주 inventory는 56개, runtime eligible 53개, 기존 quarantine 3개다. eligible은 현재 가동 PID 수가 아니다. 별도 사용자 승인 기존8/신규 시간대3의 policy publish·timer 설치가 완료됐으며 미달 추천2는 보류다. 9/7의 inventory53/eligible50은 당시 기록으로 보존한다. 매 실행에서 target-date applied hash·preflight·timer/service·custody를 대사하고 예약 전은 `not_yet_due`로 둔다.

| 9/8 신규 시간대 | Preflight / 기동 예약 KST | 신호 유효 window KST |
| --- | --- | --- |
| TYM 오전 | 09:05 / 09:09 | 09:10~09:59 |
| NHN 정오 | 13:25 / 13:29 | 13:30~13:49 |
| 에스디바이오센서 오후 | 14:10 / 14:14 | 14:15~14:40 |

예약표는 설치 receipt의 예시이며 실제 설치 계약을 재확인한다. 보유 episode는 당시 target을 유지한다. 팬오션 오전후반의 신규 episode 2→4 tick도 별도 승인된 축에만 해당하며 기존 보유분이나 다른 profile로 확장하지 않는다. Samsung 오전은 baseline-only다. Samsung v9는 actual-policy/as-of 원장·기존 축의 근거 있는 rollback, low-price tuning은 실제 정책 carry를 소유하며 관측 subset만으로 신규 tightening을 승인하지 않는다. 새 상승·반등/진입지연 후보는 `machine_entry_timing_tuning`의 독립 source·경제성·PREOPEN 계약을 따른다.

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
- 원래 target 체결과 수동 정정/청산을 exact dated 주문번호·`ori_ord`·leg로 구분했는지. broker 잔고 부재만으로 HELD를 COMPLETE로 만들거나 수동 successor를 자동 target으로 흡수하지 않았는지. 실제 체결시각이 없으면 null/직접 결손 사유와 복구시각을 분리하고 주문시각·복구시각으로 대체하지 않았는지
- fill-before-submit, late broker receipt와 event-time regression을 정상 arrival provenance로 보존했는지, 동일 owner lifecycle의 KRX 진입→NXT 청산을 cross-attempt로 오판하지 않고 phase별 `entry_venue/exit_venue`로 기록했는지
- target/entry policy를 바꾸지 않는 관측축과 실제 다음 PREOPEN 후보를 명확히 분리했는지

에피소드 수량은 장후 튜닝축이 아니다. 무손절·시간청산 없음, 목표 주문 유지 등 profile 고유 계약은 단순 post-sell MFE만으로 결함 판정하거나 임의 변경하지 않는다.

## 3. 현행 우선 분석축별 반복 점검

### 3.1 Micro-reversion

급등·반전·soft-block 이후의 짧은 회귀 기회를 비용 차감 실행 가능성으로 평가한다.

`microstructure_reaction_context`는 context schema v2와 delivery telemetry v3(`computed`, `payload_included`, `confirmed_sent`, `internal_consumed`, cache identity)를 가진 diagnostic/source-quality 입력이며 직접 runtime-apply 권한이 없다. sole ADM/LDM consumer가 사라진 `institutional_flow_context`는 퇴역 상태라 생성·복구 대상으로 삼지 않는다. micro 결과는 현재 Entry AI 입력 품질, risky micro source-only 관측, 위젯·에피소드 exact signal attribution과 source-quality 개선에만 사용하고 LDM/bucket/prompt-bias 경로를 복원하지 않는다.

context의 finite exact outcome 20은 진단 해석 기준이지 별도 양수 EV·PREOPEN 승격 대기열이 아니다. 아래 경제성 비교는 해당 risky micro/timing 정책 owner의 평가에만 적용하며 context 전달·계측 수리의 완료조건으로 전용하지 않는다.

- 메인 봇 risky micro 관측, 위젯·에피소드의 microstructure attribution을 같은 축에서 비교하되 주문 owner와 정책 선택 권한은 합치지 않는다.
- mark-price MFE 대신 executable BBO와 target/adverse 선후를 사용한다.
- ask depletion은 취소·refill·공격적 매수체결·다단계 호가 이동을 분리하고, current ask 한 레벨의 감소만으로 반등 label을 만들지 않는다.
- quote/BBO/tick context 결손은 0수익으로 보간하지 않고 source-quality gap으로 분리한다.
- `source_only_candidate`, `recheck_required`, `excluded_excessive_risk`, `excluded_uneconomic_spread`, `source_quality_blocked`를 직접 근거와 함께 보존한다.
- promotion EV에는 허용된 source-only cohort만 포함하고 recheck 진단 cohort와 실제 filled-terminal 표본 floor를 분리한다.
- source-only observer의 snapshot freshness, 0B/0D callback p95·p99, queue full/drop, worker/writer error, writer 생존수와 low/critical disk watermark를 확인한다. observer stop은 Provider replay와 R3 full-gate 승격을 차단하지만 정확한 local label·Provider-floor census 자체를 누락시키는 이유로 사용하지 않는다.

판정 기준은 `추가 참여율 + 비용차감 source_quality_adjusted_ev_pct + adverse-first/tail loss + 기존 정상 경로 순이익 비훼손`이다.

### 3.2 AI 판단 품질 개선

AI가 사용되는 endpoint마다 세 층을 분리해 점검한다.

1. 호출 품질: provider, model, transport, timeout, failback, parse, cache, response ID
2. 입력 품질: exact snapshot, canonical context, 완성 분봉, executable price/BBO, 체결 tape, venue/session, 시각과 결측 처리
3. 판단 품질: raw/normalized/final action, edge/risk/reason, 이후 MFE/MAE·first-hit·체결·손익

각 자연 호출에서 request/trace/snapshot ID, prompt/payload/response hash, prompt/schema/bundle version, latency·token usage와 submit/holding/exit 결과를 연결한다.

Main AI R0→R3의 목적은 현재 프롬프트를 고정 보존하는 것이 아니라, 새로 성숙한 동일 payload/outcome 근거가 들어올 때마다 stage별 Control 대비 더 나은 Candidate 프롬프트를 탐색하고 다음 검토 가능한 manifest를 갱신하는 것이다. 따라서 “사용자가 프롬프트 변경을 원할 때만 실행”하지 않는다. R0 exact source 수집, R1 daily 해석, R2 cumulative/paired 경제성 비교는 자연 표본과 maturity가 생길 때 계속 누적한다. R3의 `research_candidates`와 full-gate `candidates`를 분리한다. 연구/정상 무표본·부분 정상행 학습을 full-gate 미달이라는 이유로 실패 처리하지 않되, 적용 검토용 후보는 source-quality, 동일 payload, complete terminal, 비용 차감 EV와 해당 표본 floor를 통과해야 한다. 두 출력 모두 자체 `runtime_effect=false`다. 프롬프트 변경·provider/model 변경·실주문 반영은 별도 review와 target-date PREOPEN/PID 계약 전에는 수행하지 않는다.

현행 #76→#82→#78은 self-hash·격리 cohort·부분 정상행 학습을 이용한 offline 평가 환류다. #81 legacy runtime은 `LEGACY_RUNTIME_AUTHORITY_ENABLED=False`이므로 R3/#82 증가를 실적용 대기로 보고하지 않는다. 지원 KRX V2.14/V2.15의 별도 `entry_setup_live_policy` 승격·PREOPEN·PID receipt와 분리한다. 코드 보완 완료와 자연 late-follower generation/경제성 확인은 `AIDecisionActionOutcomeNaturalEvidence0908`에서 별도 판정한다.

9/7 원천의 자정 이후 복구는 NXT lifecycle eligible 0→2와 metadata consumer terminal을 닫았지만, 당시 Entry exact control은 KRX/NXT 각0이고 holding provider checkpoint는 미충족이었다. market18행·legacy identity2행의 과거 결손과 신규 자연 원천을 구분한다. provider 미실행 source-only 모드에서 producer가 명시한 `exit=2/source_only_blocked_or_deferred`는 단계/artifact를 확인해 source warning으로 분리할 수 있지만 일반 실행 실패·strict verifier 실패를 정상화하는 예외가 아니다. 정상 checkpoint 재사용과 producer의 bounded resumable 상태만 허용하며 terminal schema/provider/receipt rejection을 무제한 새 retry로 재개하지 않는다.

멀티타임프레임 입력은 [Plan Rebase §7](./plan-korStockScanPerformanceOptimization.rebase.md#7-current-open-state-summary)의 별도 사용자 승인 계약을 따른다. `entry_candle_context_v1`·`holding_decision_context_v1`과 공통 `scalping_multi_timeframe_context_v1`은 두 stage schema/하나의 파생 버전이며 세 번째 병렬 payload가 아니다. 지정된 PREMARKET 최종 검증의 binary gate 전에는 source-only, 검증 통과 후에는 승격 receipt가 기록한 검증 완료시각부터 모든 대상 scalping 종목·활성 세션·AI endpoint가 적용 범위다. 세션별 추가 승격·canary 또는 다음 PREOPEN 대기를 새로 요구하지 않는다. 다만 actual payload/trace·`provider!=none`·비교 가능 필수값 `MISMATCH=0`·완성봉·freshness·schema/version·rollback과 각 호출의 venue/session을 확인하고, 전역 적용 범위를 전 endpoint 자연 호출 완료나 수익성 입증으로 바꾸지 않는다. 이 문서 갱신·일반 모니터링은 별도 승격 작업이나 process 재기동 실행을 지시하지 않는다.

micro-reversion은 Main AI에 action label을 주입하는 별도 권한축이 아니다. exact same-epoch BBO·0B/0D, spread, refill/trade backing, venue/session과 후행 action-neutral outcome을 입력 품질·오판 taxonomy에 결속하되 future first-hit이나 사후 MFE를 당시 prompt input으로 역류시키지 않는다. Entry와 holding/exit payload cohort를 합치지 않고 각각 `entry_candle_context_v1`, `holding_decision_context_v1` 경계를 유지한다.

- `BUY`, `WAIT + probe intent`, `WAIT observation-only`, `DROP`, `INSUFFICIENT_DATA`의 의미를 혼합하지 않는다.
- semantic/schema 오류와 모델의 실질적 오판을 분리한다.
- provider/schema 성공을 판단품질 성공으로 간주하지 않는다.
- 동일 exact payload의 Control/Candidate replay에서 선행 adverse 뒤 회복, 직접 상승과 순서 불명을 구분한다.
- AI는 직접 주문·수량·broker safety 권한이 아니며 비정상 출력을 임의 BUY로 복구하지 않는다.

장중에는 R0 source가 이후 R1 daily, R2 cumulative, R3 source-only manifest로 이어질 수 있는지 미리 점검한다. exact prepared request census, A/B/C 동일 source pool, action-neutral label, Provider replay receipt, main lifecycle exact join을 분리하고, Provider 일일 budget 또는 observer/source-quality gate 때문에 replay가 미실행된 상태를 모델 오판이나 full-gate 승격 성공으로 포장하지 않는다. Provider replay와 full-gate 후보에는 각각 해당 producer의 reviewed 호출량·거래일·common parent·종목 floor·terminal 계약을 적용한다. source-only materialization·research/metadata 종결을 Provider 실행 완료와 혼동하지 않는다.

생성 파일 크기, materialized request 수 또는 provider/schema 성공만으로 경제적 유효 표본이 있다고 판단하지 않는다. `exact request/response binding → source-quality-valid payload → action-neutral mature outcome → lifecycle terminal join → effective-dated cost/master binding → net-economic eligible row` funnel을 전수 대조한다. 마지막 값이 0이면 최초 0 stage를 찾고, 아직 정해진 maturity deadline 전인 표본과 exact companion/hash·BBO·terminal join이 영구 누락되는 구조적 결손을 분리한다. 결손 row를 0 EV로 보간하거나 대용량 source artifact를 유효 denominator로 대체하지 않는다.

기대 baseline은 기본 live scalping AI가 OpenAI이고, `entry_price`만 Bedrock Qwen3 32B primary → Nova Lite v2 failback 뒤 double-failure defensive close이며 OpenAI third fallback이 없고, `holding_flow`는 Nova Lite v2 primary → OpenAI failback인 계약이다. 실제 route는 당일 runtime env와 현재 PID provider receipt로 검증하고, transport/failback incident와 전략 threshold·가격·수량 효과를 분리한다. AI를 사용하지 않는 위젯·에피소드 경로에 억지로 provider 정상성 판정을 요구하지 않는다.

### 3.3 Smoothing

Smoothing은 순간 tick·호가·OFI/QI 흔들림으로 action이 왕복하는 것을 줄이는 공통 품질축이며 별도 주문 owner가 아니다.

Holding/Exit ADM이 퇴역했어도 `holding_flow_ofi_smoothing`은 기존 holding-flow hard guard 안의 독립 bounded 입력 안정화 경로로 유지된다. 이를 퇴역 ADM/LDM의 잔존 권한이나 재활성화 근거로 해석하지 않는다.

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
- `micro_entry_confirmation`의 fixed mode는 clean-baseline exact owner·symbol·session·entry-state의 `supportive_confirmation_candidate` 완료 outcome만 누적하고 기존 20 completed·BBO/paired 95%·depth/feasibility 90%·right-censored 20%·complete 5/10/20일 기준으로 `1/3/5초`를 고른다. 동적 mode는 `machine_dynamic_micro_confirmation_replay_v2`의 actual signal마다 `신호+0/1/3/5초` 직전 1초 past-only exact-route same-epoch BBO·0B/0D, direct support/저점 대비 rebound, trade backing/refill과 owner 가격·target·비용을 결속한다. 5 observed dates·8 unique/8 completed·replay/paired 85%·right-censored 35% 이하·complete 5 source-day positive/improved EV·순이익·자본효율·0.005%p uplift·p10을 통과하고 마지막 자연 신호가 당일 또는 직전 KRX 거래일인 한 scope만 다음 exact-date v3 policy에 들어간다. 이틀 연속 무신호, source/cost/hash 결손, same-stage mutation이면 즉시진입 baseline을 유지한다. 선택된 동적 scope는 다음 기동부터 기존 신호 직후 read-only WS snapshot을 0/1/3/5초 순차 평가한다. snapshot 파일/상위 계약 결손은 blind wait 없이, 정상 snapshot의 exact-route 일시 결손은 bounded checkpoint terminal에서 신규 차단이 아니라 같은 원천 signal과 기존 manual-owner/account/order/global-pause/liquidity/velocity/market-weakness/broker safety 전체 재검증으로 fallback한다. `ENTER`도 이 guard를 모두 통과해야 원래 가격·수량·target의 BUY 경로로 진행한다. future first-hit은 action input이 아니며 이 축은 signal·수량·가격·target·holding/exit·provider/bot/cap·broker/hard-safety를 바꾸지 않는다.
- 위젯 calibration은 메인 봇 또는 에피소드 runtime을 변경하지 않는다.

### 3.5 에피소드 튜닝

- profile·종목·venue·시간창·leg별 제출, fill, target, terminal과 실현비용을 누적한다.
- clean baseline 이후 rolling/cumulative 결과와 최신 거래일 holdout을 사용한다.
- 미청산 episode는 completed EV에서 제외하고 custody 부담과 자본점유를 별도 지표로 보존한다.
- 신규 profile과 기존 profile 변경을 분리하고 exact-date transition hash와 PREOPEN 적용 여부를 확인한다.
- 진입 확인 지연 연구는 완성 1분봉 시각이 아니라 원장에 영속된 실제 `signal_decision_at`만 anchor로 사용한다. 이 값이 없는 legacy episode는 진단에는 남기되 진입시점 정책 표본에서는 제외한다.
- 수량, provider, bot, broker guard와 legacy custody는 자동 calibration 축이 아니다.

추천을 장중 대사할 때 frozen canonical report와 이후 producer native metadata projection·별도 승인 ledger를 구분한다. 원본 path/row/hash→native ID→승인/구현 disposition→당일 policy/receipt를 연결하며 원본 ID 결손 이력을 지우거나 같은 작업을 두 번 세지 않는다. 9/7 source의 postclose65행과 별도 승인 projection26행을 91개 고유 작업으로 합산하지 않는다. projection은 새 시장/경제성 재생성이 아니고 native ID만으로 실주문 권한이 생기지 않는다.

### 3.6 퇴역·OFF·비우선 영역 최소 확인

다음 영역은 장중 성과 최적화·표본모집·조건완화 대상이 아니다.

- ADM/LDM, lifecycle bucket·AI context·statistical weight, greenfield real authority: canonical env OFF, producer/consumer/PREOPEN selection 부재와 historical artifact 재유입 0건만 확인한다.
- Swing: process·실주문 권한이 OFF인지와 main/scalping 모집단에 혼입되지 않았는지만 확인한다. arm/bucket EV, sample floor, drought 또는 ETA를 생성하지 않는다.
- scalp/swing sim: `actual_order_submitted=false`, `broker_order_forbidden=true`, real cash·provider·threshold·cap 비변경과 장중 CPU/메모리/AI budget 간섭만 확인한다. 현재 실수익 최적화 보고의 headline·shortage owner로 사용하지 않는다.
- 퇴역 latency recommendation, institutional aggregate, opening/upper-limit rotation, panic-buying: producer·PREOPEN·runtime·재활성화 경로가 없어야 한다. 기존 runtime latency safety, exact investor/program context, 일반 limit-up 보호와 panic-sell defense는 별도 현행 owner로 유지한다.

이 최소 확인에서 OFF가 정상이고 누출이 없으면 `not_applicable_retired_or_deprioritized`로 한 줄 종결한다. 퇴역 env가 ON이거나 실주문·broker 호출·현재 consumer가 관측될 때만 `retired_authority_leak` 또는 `orphan_producer` 결함으로 승격한다.

## 4. 시작 시 공통 확인

### 4.1 모니터링 시점 체크리스트 실행·점검

[장후 지시문 §4.1](./postclose-tuning-result-review-task-instructions.md#41-모니터링-시점-체크리스트-실행점검)의 **시각·ID·선행 조건·결과 대사 방식**을 공통 사용한다. 해당 문서의 장후 worker 복구·전체 2-pass 권한을 장중에 상속하지 않으며 구현·재생성은 이 문서 §7의 허용 범위로 한정한다.

1. 매 실행 시작과 재개 시 현재 KST 시각·대상 거래일을 기록하고 당일 checklist의 목적/강제 규칙과 OPEN **전수**를 읽는다. 실제 `Due/Slot/TimeWindow`, Source·선행 조건·Acceptance를 사용하며 제목의 시간대·ID 끝자리나 전일 완료 목록만으로 실행 대상을 고르지 않는다.
2. 도래한 PREOPEN/INTRADAY와 모니터링 구간에 들어온 POSTCLOSE 확인 항목을 누락 없이 분류한다. 이미 성공한 producer는 최신 receipt와 직접 consumer를 확인하고, 미실행인 허용된 점검·source-only 수리는 정상 owner/명령과 review gate로 실행·검증한다. cron/systemd의 실행 중 작업·bounded retry는 기다리며, 예정 전 producer나 비용 큰 report를 체크박스만 보고 조기/중복 실행하지 않는다.
3. 지난 window의 OPEN은 `overdue_unresolved`로 검토하되 실패로 단정하지 않는다. provenance 확인 완료·through-close 수집 중·다음 PREOPEN·경제성 미관측을 분리한다. 시간 민감한 신규 주문/기동을 늦게 보충하거나 놓친 자연 원천을 합성하지 않는다. 실제 필수 owner의 실패·deadline 초과는 직접 원인과 권한 경계로 처리한다.
4. 미래 작업은 `not_yet_due`, 정상 선행 대기는 `waiting`과 다음 확인 조건/기한, 권한·근거·외부 결손은 `user_authority|blocked_missing_evidence|external_dependency`로 둔다. 요청 범위 밖 항목도 owner/이관 사유를 기록한다. `[x]` 항목은 완료 범위만 보존하고 새 결함이나 필수 freshness 실패가 없으면 재실행하지 않는다.
5. `ID·Due/TimeWindow·as_of·source date/hash·실행 owner/권한·이번 실행 또는 점검·최신 receipt·남은 acceptance·다음 확인 시각`을 기존 항목에 기록한다. 전체 수용조건을 충족한 항목만 닫는다. 현재 OPEN 전수의 미분류가 0인지 확인하고, 일부 실행 성공을 전체 체크리스트 완료로 보고하지 않는다. 변경 후 print-only parser로 현재 owner 유일성을 검증한다.
6. 지속 요청이면 매 slot 경계와 상태 변경 뒤 새 due 항목을 포함해 반복한다. 단회 요청이면 현재 시각의 실행·점검 범위와 남은 대기를 명시하고 종료하며, 요청하지 않은 야간 전체 모니터링으로 자동 연장하지 않는다.

9/8의 `ThresholdDailyEVReport0908` 16:30~16:45, `HumanInterventionSummary0908` 17:00~17:15는 **9/7 원천을 읽는 예정 점검**이다. 20:10 main 원천을 조기 생성하는 작업이 아니다. `OperatorPolicySuccessionAcceptance0908`은 9/9 PREOPEN, `ScannerLookupAttentionCalendarMaintenance1002`는 10/2 Due이므로 같은 9/8 파일에 있어도 오늘 overdue가 아니다. 예시는 현재 체크리스트 본문으로 매번 갱신한다.

### 4.2 현재 owner·원천 공통 확인

- Plan Rebase current-owner override와 이 문서의 현행 우선순위를 먼저 확인하고, ADM/LDM·bucket·greenfield·Swing·retired sim-scale-in을 현재 owner 목록에서 제거했는지
- 메인 봇 PID, 시작 시각, commit, source-dirty, runtime env와 당일 ON/OFF runtime 목록
- launcher와 bot source commit/hash, exact-date verifier의 PID mismatch/missing, 퇴역 canonical env 15개 explicit OFF. 이후 문서-only commit과 실행 코드 commit 차이는 실제 runtime source diff와 분리한다.
- 전일 postclose candidate와 당일 PREOPEN apply plan/runtime env/verify의 generation·hash·selection diff, launcher load 시각과 현재 PID의 exact env/policy receipt
- 전일 요약의 `source_generation_contract`와 checklist `POSTCLOSE_SUMMARY_SOURCES`, 마지막 `--require-summary-handoff` 성공을 실제 source date/hash로 대사. 자정 이후 source-date 9/7 복구와 9/8 runtime을 혼합하지 않고, 이전 PASS artifact로 최신 명령 실패를 가리지 않음. 결손 발견은 영향 owner에 handoff하며 장중 전체 postclose/provider 재실행을 자동 시작하지 않음
- 위젯·에피소드 systemd service/timer, exact-date policy/profile hash와 실제 process 상태
- 당일 PREOPEN apply plan/runtime env, active date, policy version, dependency와 operator override
- operator policy lock과 실행 mutex를 분리. 오래됐거나 새 EV 재검증이 없다는 이유로 운영 override를 해제하지 않음. 실행 lock 파일 존재만으로 stale을 선언하거나 삭제하지 않고 실제 점유 PID/시작시각·owner를 확인
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
- micro observer freshness·latency·queue/drop/error·writer·disk 상태와 당일 source-only collection target의 실제 WS 반영. `microstructure_reaction_context`는 diagnostic/source-quality이고 퇴역 institutional/LDM consumer를 요구하지 않는다.
- 디스크는 사용률과 free bytes·증가 시각을 함께 확인하고 당일 pipeline/micro 원천, 파생 요약, 테스트/리뷰 임시 산출물, 복구 증거를 분리. #73 raw suppression OFF와 원본 보존 유지. `tmp` 이름만으로 삭제하지 않으며 당일 원천·미검증 checkpoint·감사 문서가 참조하는 복구 증거는 보존. 공간 회복은 source 품질·Provider hold 해제나 전략 효과의 증거가 아님
- limit-down natural target/REG receipt, required·requested realtime type 0B+0D, type별 first-data·sequence와 ordered-path downstream lineage
- R0→R3 단계별 최신 artifact, current Provider 실행 여부·budget, lifecycle exact terminal join과 각 단계 blocker
- 구현됐지만 현재 PID/process/policy에 미반영된 변경과 rollback 값
- clean baseline 이전 데이터가 rolling/EV/runtime 판정에 혼입되지 않았는지
- runbook/설치 cron·systemd/tmux registry가 선언한 expected process별 MainPID/cgroup/lock/heartbeat, 최근 progress marker, output과 실제 consumer

### 4.2.1 동시호가·NXT 휴장 구간의 수신 기대

정상 평일 **08:50~09:00 KST**의 연속매매 0B/0D 무수신·age 증가는 단독으로 subscription 장애가 아니다. NXT-only는 메인마켓 시작 **09:00:30**까지 같은 구분을 적용한다. KRX/SOR 또는 KRX가 섞인 등록은09:00에 이 예외가 끝나며, 알 수 없는 route/시각은 임의 면제하지 않는다. 예상체결·호가·연결 제어 패킷까지 반드시 중단된다는 뜻은 아니다.

- 이 구간의08:50~08:55 PREOPEN·08:55~09:00 scout 체크리스트는 **전일 source→당일 정책/hash→PID 연결** 확인이다. 현재 체결수·수신속도·시장 포착률을 요구하거나 체결 무수신만으로 FAIL/재기동/REMOVE→REG를 지시하지 않는다.
- `ws_opening_receive_expectation_v1`은 `expected_market_quiet`와 원래 age/관찰 상태·resume 시각을 별도 기록한다. WS freshness 진단 및 #89 report의 absence-only subscription/quiet workorder 분모에서 분리하며 실제 freshness·first-receipt 성공을 만들지 않는다. 수신 기반 dashboard는08:49:30 이후 생성된 same-date/확인된 route 파일만 해당 구간 동안 과거 진단 자료로 사용할 수 있고 `current_freshness_usable=false`다. 더 오래된/잘못된 schema/다른 날짜 파일은 계속 결손이다.
- LOGIN/연결/REG ACK 오류, 실제 미등록·route 불일치, queue/drop·writer/disk/parser 실패는 정상 휴지로 덮지 않는다. 진입·주문 stale/price/broker guard도 그대로이며 과거 호가를 실행 가능한 fresh 자료로 승격하지 않는다. 정상 휴지 여부와 별개로 실제 signal에 필요한 입력창이 없으면 timing/경제성 제외는 유지한다.
- 08:50 이전부터 이미 stale했던 원천은 휴지 예외로 덮지 않는다. quiet-only 창의 수신 결손 진단률은 null/평가 분모0이지 정상0% 수신 성공이 아니며 혼합 창에서도 quiet를 장애율 분모에서 분리한다.
- 재평가 시 새 명시적 오류·복구 지시는 과거 quiet의 보존 필드보다 우선한다. dashboard 투영도 오류 필드를 보존하고, 잘못된 age는 `receive_age_contract_invalid`로 유지하여 정상 무수신으로 바꾸지 않는다. 등록 route가 없는 fallback은 제시된 route들을 함께 확인하므로 관측 NXT와 KRX/SOR 정보가 섞이면09:00 이후 면제하지 않는다. 개장 후 저장된 no_tick marker도 복구 권고 집계로 복원한다.
- KRX09:00·NXT-only09:00:30 이후에는 현재 as-of로 예외를 다시 계산하고 기존 freshness/수집 SLA로 재개 여부를 확인한다.09:05~09:20에는 실제 입력→판단→제출 귀속을 대사한다. 영속된 quiet marker나 장후 실행 시각으로 과거 event의 판정을 바꾸지 않는다.
- [9/10 구현 리뷰](audit-reports/2026-09-10-ws-opening-auction-quiet-review.md)는 코드 검증 기록이다. 기존 short-lived #89 producer는 다음 실행에서 새 코드를 읽지만 실행 중 WS PID의 reload/재기동은 별도 승인·receipt가 필요하다. 이 계약은 자동 재기동 승인이 아니다.

### 4.3 장중 수집 결손 즉시 대응

현재 우선 owner의 실제 신호·요청·수집 대상이 있는데 필요한 원천이 없거나, 유효 원천 뒤 저장·join·consumer가 끊기면 아래 절차를 즉시 시작한다. 일마감 보고서의 eligible 0이나 장후 실패를 기다리지 않는다. 단, 예정 전·정상 bounded wait·아직 성숙하지 않은 outcome·근거 있는 자연 대상 부재·OFF/퇴역은 결손으로 만들지 않는다. 감지 기준과 기한은 해당 owner의 기존 수집 주기·freshness·window·maturity 계약을 사용하며 임의의 공통 timeout이나 새 표본 floor를 만들지 않는다.

1. **최초 단절과 영향 범위 고정**: 대상 거래일·관찰 시각, owner/symbol/profile·venue/session, 실제 signal/attempt/episode ID와 원래 시각, 필요한 입력창, 현재 PID/code/config generation, 마지막 정상 receipt와 최초 실패를 기록한다. raw·로그·checkpoint·manifest의 경로/hash와 재현 가능한 결손 행·구간을 보존한다. 계속 쓰이는 파일은 읽은 범위와 시점을 명시하며 진행 중 generation을 덮어쓰거나 원본·lock을 삭제하지 않는다.
2. **수집부터 직접 consumer까지 추적**: 해당 경로에 적용되는 `설치 trigger/현재 PID 설정 → 대상 선정·예약/REG → REST 응답 또는 type별 WS 최초 수신 → callback → enqueue 이전 처리 → queue/worker → writer 영속 저장 → manifest/checkpoint → parser/projection/exact join → intended consumer의 실제 필드`를 대사한다. 단계별 입력·성공·중복·제외·실패·대기 수와 exact 행 연결로 첫 결손 owner를 찾는다. enqueue 이전 loss가 저장 raw 분모 밖이면 별도 ingress 증거/계측 결손으로 남기고 raw 감사 정상으로 가리지 않는다. 파일 증가·PID 생존·report exit 0만으로 유효 수집을 인정하지 않는다.
3. **원인별 수리 선택**: 아래 구분으로 현재 복구 가능한 부분을 먼저 처리한다. 원천이 있는데 후단이 버린 경우 수집기를 불필요하게 바꾸지 않으며, 서로 다른 결함이 있으면 최초 원인과 후행 결함을 따로 기록한다.

| 결손 유형 | 직접 확인과 허용된 대응 |
| --- | --- |
| 원천 미수집·손상 | 대상/예약·필수 type·route/epoch·freshness, callback/drop, queue/writer·disk·저장 실패를 확인. 기존 owner의 비권한 계측·저장·source-only 수집 코드 결함을 최소 수리하고, 실제 재가동은 아래 권한 경계를 따름 |
| 원천은 있으나 사용 불가 | parser/sanitizer의 필드 유실, schema/date/hash·identity·projection/join 불일치, main/widget/episode 또는 real/sim 혼입을 수리. 정확한 원본이 있는 범위만 영향 consumer에 재전달하고 실제 누락값을 합성하지 않음 |
| 후행 자동화·계약 결함 | stale receipt, generation/handoff 누락, wrapper 출력·중복 실행 판정 등을 직접 owner에서 분리. 이를 장중 시세 미수집이나 전략 판단 실패로 바꾸지 않음 |
| 외부 제한·권한 필요·과거 원천 소실 | 기존 cooldown/bounded retry와 정상 원천은 보존. `external_dependency`, `user_authority`, `blocked_missing_evidence` 중 해당 상태와 정확한 필요한 조치·근거를 기록하고, 독립적으로 가능한 허용 코드 수리까지 포기하지 않음 |

4. **같은 실행에서 수리·재발방지 검증**: §7의 source-only 권한 안이면 추가 구현 승인을 기다리지 않고 최소 보완한다. 최초 실패를 재현하는 회귀 테스트에 정상 입력 보존과 해당 수리에 관련된 malformed/missing·route/epoch/date 불일치의 명시적 제외를 포함하고, 조용한 drop이나 성공 위장이 남지 않도록 기존 계측·detector·consumer 계약을 보완한다. `$korstockscan-review-gate`의 review → fix → 재리뷰 → 관련 테스트/구문 검증을 미해결 finding 0까지 반복한 뒤, 허용된 최소 producer/consumer만 검증한다. 예정 전 장후 producer, 전체 postclose, Provider replay·호출을 조기/중복 실행하지 않는다.
5. **실제 반영 권한 확인**: source-only라는 이름만으로 공유 BUY/WAIT/SELL 계산 변경, 거래 process나 collector의 기동·종료·재기동, live env/정책·REG 설정 수동 변경을 승인하지 않는다. 해당 실행에 유효한 별도 사용자 승인 또는 명시적인 runbook 복구 권한이 있을 때만 정확한 대상·명령·중복 PID/실제 lock·rollback을 확인하고 반영한다. 권한이 없으면 안전한 코드 수리는 검증까지 닫되 `deployment_status=user_authority`와 필요한 정확한 반영 조치를 즉시 사용자에게 알린다. 기존 process가 새 파일을 자동 소비하는 계약이라면 reload/consumer receipt로 확인하며 불필요한 재기동을 요구하지 않는다. Kiwoom 요청·응답 parser·FID·REG/REMOVE·재연결을 수정할 때는 [공식 API reference gate](./kiwoom-api-data-contract.md)의 upstream SHA/경로/조회시각 검증을 선행한다. rate/retry/동시성·조회 budget 상향, source-only reservation 침해, safety 완화로 수집을 회복하지 않는다.
6. **실제 필요한 창과 새 원천으로 수용**: 위젯·에피소드 진입 확인은 실제 `signal_decision_at`과 각 0/1/3/5초 checkpoint의 계약상 past-only 입력창, 동일 route/epoch의 0B/0D·BBO와 window completeness를 확인한다. 긴 파일이나 이후 exit 연구 경로가 있어도 신호 직전 창 결손을 채운 것으로 보지 않는다. Main AI는 exact request/payload/response와 후행 label/terminal/cost 결속을 구분하고, scanner는 독립 모집단과 schedule/observation을 구분한다. 수정 후 자연 원천이 영속 저장되고 해당 parser/join·직접 consumer에 같은 identity/hash로 도달했는지 확인한다. 아직 예정 전인 최종 장후 consumer는 장중의 안전한 계약 검증과 실제 예정 handoff를 분리한다. 실주문 발생·양수 EV·승격 표본 floor를 진단 수리의 추가 조건으로 요구하지 않는다.
7. **과거 손실과 잔여 조건 보존**: 수집하지 못한 과거 tick·호가·체결시각은 새 시세, 다른 session, 분봉·후행 고가 또는 복구 시각으로 채우지 않는다. 원본이 실제 존재하는 재파싱 복구와 비가역적 과거 exclusion을 분리하고, 재개 후 첫 유효 시각부터 새 원천을 판정한다. 같은 날에도 새 유효 입력창이 열리면 확인하되, 지나간 신호의 결손이 복원됐다고 하지 않는다. §4.1의 기존 OPEN ID에 원인/영향 창·수정/테스트·반영 권한/PID·새 수집/consumer receipt·남은 acceptance와 다음 확인 시각을 남긴다. 반복 결손은 같은 owner의 최초 미해결 지점을 재검토하며 동일 재실행을 무한 반복하지 않는다.

완료는 `repair_status`(코드·계약 수리), `deployment_status`(실제 반영), 수집/전달의 자연 acceptance, §6의 `shortage_status`(유효 표본), `economic_acceptance`로 나눠 보고한다. 테스트 PASS나 코드 저장만으로 “장중 수집 정상화·재발방지 완료”라고 하지 않는다. 자연 대상이 없으면 configure/load receipt와 유효한 무대상 근거까지만 보고하고 다음 자연 창은 OPEN으로 둔다. 수집 경로가 닫혀도 경제성 미관측은 별도로 남기며, 결손 해결을 위해 실주문을 만들지 않는다.

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

`greenfield_real_environment_authority`는 현행 ADM/LDM retirement 범위로 영구 OFF다. target-date artifact나 historical promoted bucket이 있어도 현재 PID 권한으로 인정하지 않으며, env·selection·runtime consumer가 다시 나타나면 `retired_authority_leak`으로 fail-closed한다. legacy live 권한으로 묵시 후퇴하거나 greenfield 복구 workorder를 만들지 않는다.

process 이름이나 PID 존재만으로 정상이라고 하지 않는다. `declared owner → installed/enabled trigger → expected window → PID/exit/heartbeat → artifact 또는 valid terminal skip → registered consumer → consumed field → decision/report role`을 연결한다. 예정 시각 전 one-shot 종료, reviewed disabled/retired, eligible input 0이 입증된 valid-empty는 dead/no-op에서 제외한다. 반대로 성공 exit인데 artifact가 없거나 stale하고 consumer receipt도 없으면 `no_op_success`, source를 계속 만들지만 현재 consumer가 없으면 `orphan_producer|unconsumed_artifact`다. 이 판정만으로 process를 kill·disable·restart하지 않는다.

WebSocket error burst는 오류 건수만으로 bot 재기동이나 전략 변경을 실행하지 않는다. exact connection epoch, LOGIN ACK, reconnect/resubscribe, required type별 first data, queue/drop, duplicate writer, stale age와 affected owner를 확인한다. 정상 reconnect 경계는 새 sequence epoch로 분리하고 cross-epoch 0B/0D join을 금지한다. bounded recovery 뒤 first-data가 복구되지 않거나 반복 disconnect가 진행을 막을 때만 runtime incident로 승격한다.

Swing, ADM/LDM/bucket/greenfield, 비우선 scalp/swing sim과 은퇴한 opening-rotation·upper-limit rotation·panic-buying 경로는 현재 장중 실수익 최적화 모집단에서 제외한다. historical artifact나 compatibility parser 존재를 표본부족·재기동·재생성·승격 가능성으로 해석하지 않는다. 단, 비우선 sim의 실주문 권한 누출이나 자원 간섭은 운영 결함으로 계속 감시한다.

## 6. 표본·모집단 부족과 구조적 고갈 판정

장중 report나 runtime에서 현재 우선 owner의 candidate·natural match·BBO·AI request·submit·fill·terminal·mature outcome·net-economic eligible 모집단의 0건 또는 sample floor 미달을 문제로 제시하면 최종 숫자만 보고 기다리지 않는다. owner·family·stage·venue/session·metric contract·window·floor denominator를 결속한 stable `shortage_id`로 다음 funnel의 최초 고갈 단계를 기록한다. historical arm/bucket 또는 OFF·퇴역 family에는 shortage ID를 만들지 않는다.

`raw opportunity/source → source-quality-valid → contract eligible → policy/PREOPEN loaded(필요한 경우) → runtime natural matched(필요한 경우) → authority-declared last consumer/floor-owning stage → submit/fill/terminal/mature/net-economic(계약상 필요한 경우)`

- `time_resolvable_shortage`: producer→intended consumer 경로와 source quality가 정상이고 동일 denominator의 신규 unique 표본이 유입될 수 있으며, maturity와 rolling expiry를 반영해 선언 horizon 안에서 floor에 도달하는 finite 근거가 있는 경우만 사용한다. 무기한 HELD, 유입률 0 또는 양(+) 유입일만 고른 평균은 ETA에 넣지 않는다.
- `structural_population_exhaustion`: impossible predicate, policy/key mismatch, systematic join/exclusion, missing runtime hook/consumer, eligible upstream 뒤 반복되는 0-conversion, 계약상 최대 관측 가능 수가 floor 미만인 경우다. submit drought나 net-economic eligible 0은 upstream 후보가 많다는 이유만으로 시간 해결형이 아니다.
- window/sample floor/maturity/effective horizon 또는 source census가 없어 둘 중 하나를 입증할 수 없으면 `blocked_missing_evidence`, 신규 경로의 선언된 최소 관찰창 전이면 `pending_declared_window`로 둔다. 각각 증거 대기와 예정 관찰창 전의 잠정 상태이며 세 번째 최종 shortage class가 아니다. 예정창 전 대기만으로 장애나 구조적 고갈을 확정하지 않는다.
- 정상 handoff에서 opportunity 자체가 없는 하루, 다음 PREOPEN 전 candidate, 아직 fixed maturity deadline 전인 row는 구조적 고갈이 아니다. 반대로 구현 파일·schedule receipt·report 생성만으로 구조 보완이 해결됐다고 하지 않는다.
- OFF·퇴역·비우선 family의 0건은 `not_applicable_retired_or_deprioritized`이며 finite ETA나 표본 수집 계획을 요구하지 않는다. current owner로의 권한 누출이 발견된 경우에만 shortage가 아니라 contract defect로 분류한다.
- `repair_status`(코드·진단 수리), `deployment_status`(반영), `shortage_status`(표본), `economic_acceptance`(효과)를 분리한다. `collecting_after_structural_repair`는 review finding0과 수정 경로의 실제 consumer/generation receipt가 있어야 하며, PID 갱신이 필요한 수정일 때만 fresh PID 반영을 추가 확인한다. `shortage_status=resolved`는 그 owner의 first depleted stage·declared denominator/floor·lineage가 닫혔을 때만 허용한다. 진단 수리 자체에 별도 양수 EV·실체결·모든 horizon MFE/MAE·PREOPEN 승격 floor를 붙이지 않는다.
- 비가역적 과거 ingress/market/identity 결손은 과거 source exclusion으로 고정하고 당시 원천 없이 같은 replay를 반복하지 않는다. 다음 날짜의 신규 source와 수집 경로를 기존 OPEN owner에서 확인한다. 새 원천 유입이 입증돼도 과거 결손이 복원됐다고 바꾸지 않는다.
- 표본을 맞추기 위한 row 복제, owner·venue·session 병합, right-censored/HELD의 completed 변환, pre-baseline 재사용, child provenance 삭제, sample floor 하향, hard-safety·broker guard·threshold 완화는 금지한다.

장중 shortage 판정은 source-only 계측·parser/schema·report·test·instrumentation 보완과 당일/장후 workorder handoff까지만 권한을 가진다. live threshold, provider, bot, cap, 수량, 주문 또는 safety 변경이 필요하면 `user_authority`로 분리한다.

최초 고갈 원인이 수집·저장·전달의 구현 결함이면 §4.3을 같은 실행에서 수행한다. 구조적 결손이 확인됐는데도 `hold_sample`이나 유한 근거 없는 ETA로 돌려 장후까지 수리를 미루지 않는다. 반영 승인 또는 외부 원천이 필요한 부분은 코드 수리와 별도 차단 상태로 남긴다.

## 7. 보완 원칙

명백한 결함이나 수익기회 병목이 확인되면 다음 루프를 수행한다.

`원인 분리 → 단일 owner·권한 확인 → 최소 보완 → review/fix/re-review → targeted validation → 허용된 영향 consumer 검증 → 별도 승인된 반영·자연/경제성 acceptance`

`korstockscan-review-gate`를 적용해 검토 범위의 미해결 finding이 없어질 때까지 수정·재검증한다. Python은 관련 pytest/compile, shell은 `bash -n`/wrapper 계약을 확인하고 `git diff --check`를 수행한다. 실거래 replay는 해당 수리의 계약에 필요하고 안전한 offline 실행이 허용된 경우에만 clean-baseline exact source로 수행한다. 문서-only는 링크·owner·권한·print-only parser로 닫으며 무관한 trading test·provider 호출·비싼 report 재생성을 요구하지 않는다.

이 지시문을 명시적으로 실행하는 요청에서는 현재 우선 owner의 허용된 구조적 결함을 읽기 전용 진단만으로 종료하지 않는다. source-quality·parser/schema·report·test·instrumentation·허용된 source-only 범위의 보완은 원인을 확인한 뒤 구현하고 review gate를 닫는다. 퇴역·OFF·비우선 sim의 단순 무표본이나 낮은 EV는 구현 owner가 아니다. 실주문 권한, PREOPEN live env 선택, provider route, bot process, cap, broker/order guard, hard/protect/emergency safety 또는 장중 threshold mutation은 이 일반 모니터링의 권한이 아니다. 기존 승인된 자동 consumer의 적용을 확인하는 것과 수동 실행을 구분한다. policy artifact가 있다고 bot 재기동·수동 env/lock/주문 변경 권한을 추론하지 않는다.

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
- 재기동이 허용된 경우에도 먼저 main/widget/episode/manual owner별 broker 미체결과 전시장 inventory를 대사하고, 우아한 종료·새 PID env verify·WS login/first-data·선택된 runtime owner·중복주문 0건을 사후 확인한다.
- 외부 지연임이 입증된 최초 WS 수신 전 구간은 내부 처리 지연과 분리한다. 단지 첫 data 이전이라는 이유로 local 로그인/등록/worker 결손을 외부 탓으로 제외하지 않는다. 최초 수신 이후 내부 queue·scanner·AI·submit 지연도 측정한다.

미래 확인은 당일 checklist의 기존 OPEN ID를 재사용하고, 없는 새 후속 작업만 `Due/Slot/TimeWindow/Track`을 갖춰 기록한다. 전일 항목을 이관하면 같은 ID·수용조건·이력을 보존하고 당일 파서에 한 번만 포함되는지 확인한다. 문서/checklist 변경 후 아래 print-only 검증을 실행한다. 외부 Project/Calendar sync 및 token 검사는 실행하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

## 8. 보고

각 항목은 `판정 → 근거 → 다음 액션` 순서로 보고한다. 관찰 target date·as-of 시각, source date·generation, 적용일·현재 PID receipt를 함께 기록한다. 단회 점검은 해당 snapshot으로 닫고 지속 모니터링을 요청받았을 때만 지정 종료조건까지 반복한다. 지속 작업 중에는 상태 변화와 현재 대기 이유·다음 확인 조건을 최대 60초 간격으로 공유하며 새 데이터가 없는 구간의 API 호출량이나 중복 worker를 늘리지 않는다.

마지막에는 반드시 다음을 분리한다.

- 체크리스트 실행·점검: 현재 KST 시각과 ID별 Due/TimeWindow, 이번 수행/최신 receipt, 완료·부분 확인·기한 경과·정상 대기·미래 예정·권한/외부 차단·범위 밖. OPEN 미분류 0과 남은 acceptance/다음 확인 조건을 명시

- 현행 우선순위: 메인 실거래·위젯·Samsung/저가주 독립 머신·공통 품질의 실제 상태와, 퇴역/OFF/비우선 영역의 최소 누출 점검 결과
- 종목탐색: 독립 `as_of rising benchmark`의 정의·source/hash·분모, discovery·post-promotion consumption·downstream conversion의 독립 분모, scanner source/watch/promotion/fast·heavy evaluation/AI/candidate 단계별 recall·지연·최초 미도달 원인, scanner 밖 미관측 종목의 executable outcome과 최종 판정 상태
- scanner-pruned observer: 전수 prune census와 bounded schedule/observation 표본, active/pending/request bound, token-wide 5/sec·source-only 4/5 reservation, exact route·BBO freshness·rate-limit/local-defer gap, resolved/right-censor/coverage floor와 full-population 외삽 금지
- 메인 봇: 상위 탐색 결과와 후단 submit drought를 분리한 놓친 수익기회, 적정 차단, probe/residual/scale-in, 매도와 post-sell
- 위젯: signal·episode·fill·target·terminal, 비용 차감 EV, owner/custody 정합성
- 에피소드: profile/leg별 제출·체결·target·COMPLETE/HELD/BLOCKED와 실현비용
- micro-reversion: 상태별 후보, ask depletion/refill/체결 귀속, recheck, passive fill feasibility, target/adverse first-hit, tail loss, observer·disk 상태와 현재 runtime authority
- limit-down: natural target/REG, ordered 0B+0D type별 receipt·sequence·same-session lineage, `collecting_after_structural_repair` 또는 resolved acceptance와 runtime authority
- AI 판단 품질: 호출·입력·판단, R0→R3 단계별 생성/차단, same-payload prompt Control/Candidate exact replay, downstream submit/holding/exit 결과와 runtime 미반영 경계
- smoothing: raw 대비 action 안정성, whipsaw 감소와 지연·손익 훼손 여부
- 당일 runtime별 정상·결함·자연 표본 부족·미호출·미반영·source-only 상태
- 퇴역·OFF·비우선 영역: canonical OFF·실주문 누출 0·broker/resource 간섭 여부만 요약하고 정상 무표본에 shortage/ETA를 만들지 않음
- owner 충돌, 중복 주문, broker reconciliation과 venue provenance 결함
- 적용한 보완, 코드 review/검증 결과, 현재 process 반영 여부와 rollback 조건; 문서-only/미재생성 범위와 미검증 자연/경제성 acceptance를 별도 공개
- 별도 승인 추천의 원본/projection/승인 ledger·policy/현재 소비 대사; 중복 집계·미승인 확대 없음, 승인된 신규 신호와 기존 보유 target 분리
- process 감사: authoritative expected set, PID/cgroup/lock/heartbeat, dead·hung·duplicate·no-op·orphan·unconsumed 분류와 valid-empty 오탐 제외
- 장중 수집 결손: 원천 미수집/기존 원천의 파싱·전달 누락/후행 자동화 결함 구분, 최초 단절 단계·영향 신호/입력창, 이번 즉시 수리·회귀 검증, 실제 반영 권한/PID와 수정 후 첫 유효 저장·consumer receipt. 과거 비가역적 손실, 자연 수용 미확인, 별도 승인 필요 조치와 다음 확인 시각은 미해결로 명시
- 부족 ledger: stable `shortage_id`, exact floor denominator, required/current/deficit, first depleted stage, funnel count, `time_resolvable_shortage|structural_population_exhaustion|blocked_missing_evidence|pending_declared_window`, finite ETA 또는 waiting 불가 이유, 다음 due·재분류 trigger·acceptance test
- 아직 해결되지 않은 병목, 다음 표본·재검증·구현 owner

진단·코드 수리 완료와 실제 경제성 성공은 독립 판정이다. 신규 경제 표본이 없다는 이유만으로 닫힌 수리 검토를 취소하지 않으며, 수리 완료로 실현 EV 개선을 선언하지도 않는다. 보고서나 runtime 이름의 존재는 효과의 증거가 아니다. `identified → source quality → 해당 owner의 승인·실제 runtime 소비 receipt → executable 체결·terminal outcome → 비용 차감 rolling/cumulative EV → post-apply attribution`이 연결됐을 때만 경제성 효과를 판정한다. 소비 receipt는 해당 계약의 PREOPEN/PID 또는 별도 승인 승격 receipt를 사용하며 다른 owner의 추가 승격 gate를 요구하지 않는다. 장중 생성된 장후/다음-session source-only artifact는 authority에 맞는 intended last consumer와 handoff까지만 보고하고 다음 PREOPEN/PID 소비나 실주문 효과를 선행 주장하지 않는다.
