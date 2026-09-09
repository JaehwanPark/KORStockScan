# 장후작업 실행 모니터링·장애복구·추천구현 지시문

작성 기준: `2026-09-09 KST` (9/9 18:30까지의 후속 리뷰·승인 기록 대사; 현재 운영 검증 receipt가 아님)

이 지시문의 목적은 장후작업이 실행되는 동안 상태를 계속 확인하고, `FAIL`, timeout, hang, 필수 산출물 누락 또는 handoff 단절이 발생하면 최초 원인을 찾아 안전한 범위에서 수정·검증·최소 재실행하여 대상 거래일 작업을 정상 terminal 상태로 닫는 것이다.

운영 체인이 정상화된 뒤에는 같은 generation의 authoritative `implement_now`와 위젯·에피소드 매매기계의 구현 추천을 전수 intake한다. 허용 범위의 항목은 `Pass 1 구현 → review/fix → 영향 산출물 재생성 → Pass 2 재판정·추가 구현`을 fixed-point까지 반복한다.

현행 공동 최우선 개선 목표는 **메인 submit drought 해소**와 **위젯·에피소드 매수진입시점 판단품질 개선**이다. 메인은 유효 기회가 scanner·Entry AI·latency/price·최종 authority·broker 중 어디에서 사라지는지 추적한다. 위젯·에피소드는 원래 신호 선정과 신호 뒤 진입 확인을 분리하고, **micro-reversion의 반등·bid 지지와 매도잔량 감소속도·실제 매수체결 설명·refill의 결합**이 비용 후 EV·순이익·유효 참여·회전에 기여하는지 기존 owner에서 확인한다. 매도잔량 감소 자체를 BUY 신호로 쓰거나 주문 건수·수익 빈도를 위해 guard를 무차별 완화하지 않는다. 실행 실패·source-quality 복구를 선행하고, 두 우선 경로는 §1.1~§1.2와 [상세검토 진행표 §6](audit-reports/2026-09-05-postclose-work-inventory.md#6-다음-상세검토-우선순위)로 대사한다. 검토 우선순위는 설치된 producer 실행 순서를 바꾸지 않는다.

사용자가 이 지시문에 따라 장후작업을 모니터링하라고 요청하면 위 허용 범위의 2-pass 구현도 함께 지시한 것으로 본다. 별도의 구현 재지시를 기다리지 않는다. 단, 이 문서의 인용·열람·현행화 또는 읽기 전용 점검 요청은 모니터링/추천 구현 실행 지시가 아니다. 문서 수정만 요청받았으면 운영 산출물·PID·env를 변경하지 않는다.

명시적 모니터링 실행에는 **모니터링 시점까지 도래한 체크리스트 항목의 실행·점검**을 포함한다. §4.1에 따라 전수 분류한 뒤 요청 범위·권한·선행 조건이 충족된 작업은 실행하고 결과를 검증한다. 단순히 남은 목록만 제시하고 종료하지 않으며, 체크박스나 예정 시각 자체를 실주문·수동 적용·재기동 권한으로 해석하지 않는다.

상세 EV 연구, 전략별 장기성과 재평가와 모든 report의 계산 재현은 기본 범위가 아니다. 다만 공동 최우선 경로의 기존 paired 연구·선정 consumer·최초 결손과 허용 추천의 구현 가능성을 판정하는 점검은 포함한다. 기존 timing 4군 연구와 widget paired 평가를 읽는 것과 새 전략 grid·live recipe·적응형 청산 활성화는 구분하며, 범위를 확장하는 성과 연구는 별도 요청을 따른다.

튜닝 원칙과 현재 owner는 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8, 당일 실행 항목은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 `docs/time-based-operations-runbook.md`, producer/consumer 순서는 `docs/report-based-automation-traceability.md`를 따른다.

2026-09-05부터의 실행 단위별 순차 상세검토 진행상태는 `docs/audit-reports/2026-09-05-postclose-work-inventory.md`에서 추적한다. 이 진행표는 상태 요약이며 Plan Rebase나 당일 체크리스트의 owner·권한을 대체하지 않는다.

## 1. 완료 목표

다음을 모두 충족하면 장후작업과 허용된 추천 구현이 완료된 것으로 판정한다.

1. 대상 거래일이 모든 wrapper, status artifact와 후행 작업에서 동일하다.
2. 모든 필수 작업의 예정/진행/terminal 상태가 설명되고 상태 미상은 없다. 예정 전은 `not_yet_due`, 정상 대기는 `waiting`으로 구분하되 due 작업이 `running|recovering|waiting`이면 최종 완료가 아니다.
3. 필수 producer가 최신 `[DONE]` 또는 성공 status artifact로 종료되고, 실패 후 복구한 경우 이전 FAIL보다 최신인 성공 근거가 있다.
4. main postclose verifier가 terminal이고 필수 artifact, predecessor와 downstream link 결손이 없다.
5. DONE controller JSON과 controller wrapper가 모두 terminal이며, due인 AI entry replay follower도 terminal이다.
6. tuning monitoring, dashboard archive, 20:10 widget evaluation, 21:15 machine final refresh가 각각 성공했거나 명시적으로 OFF인 근거가 있다.
7. 21:55 finalization이 선행 작업을 확인한 뒤 cleanup과 final error detector까지 완료한다.
8. unresolved `FAIL`, timeout, hang, 중복 실행, 실제 점유 중인 stale lock 또는 필수 후행 누락이 없다.
9. authoritative `implement_now`와 위젯·에피소드 추천 전수가 stable ID로 분류되고 누락이 없다.
10. 허용된 구현 항목은 Pass 1과 Pass 2 fixed-point, review finding 0, targeted validation과 영향 산출물 재생성까지 닫힌다.
11. 권한 밖 추천은 구현하지 않고 `user_authority`와 필요한 승인 근거를 명시한다.
12. 대상일 submit drought의 scope별 최초 병목·해당 workorder/기존 family·다음 consumer·남은 실효성 검증이 설명된다. 경보 전달이나 코드 완료를 drought 해소로 대체하지 않는다.
13. §4.1의 체크리스트 전수 대사에서 미분류 항목이 없고, 요청 범위 안의 due 작업은 실행·검증됐거나 구체적인 대기/차단 근거가 있다. 허용된 미실행 작업을 누락한 채 완료로 보고하지 않는다.
14. 위젯·에피소드의 신호 선정→micro 확인→제출/체결→terminal/비용을 분리하고, 공통 계산·4군 연구·기존 선정/정책 consumer의 최신 generation 및 남은 자연·경제성 acceptance를 설명한다. 적응형 청산은 §1.3의 별도 구현·최초 활성화 경계를 보고하며 진입 개선이나 정상 장후 terminal로 대신 완료하지 않는다.

코드·계약 검토, 배포, 자연 산출물, PREOPEN 선택, PID 소비, 비용 차감 EV/순이익 검증은 각각 별도 상태다. 기존 review finding 0을 이유로 자연 acceptance를 완료하지 않으며, 반대로 미관측 EV를 이유로 수리 완료를 취소하지 않는다. #8/#9처럼 완료된 상세검토는 새 결함·계약 변경·필수 handoff 실패가 입증될 때만 재개한다.

source-only 자연 표본 부족이나 전략 후보 0건은 작업 실패가 아니다. 반대로 process 종료 코드가 0이어도 필수 artifact가 없거나 target date가 다르면 정상 종료로 보지 않는다.

source-date 9/8의 [장후 운영 리뷰](audit-reports/2026-09-08-postclose-monitoring-review.md)와 [2-pass 후속](audit-reports/2026-09-08-implement-now-two-pass-followup.md)은 9/9 00:27:14 strict/후행 controller 및 전일 요약 handoff의 기록이다. 당시 최신 intake61행의 요청9행은 검증 완료1·증거 차단8, 비구현52행은 관찰28·보류19·거절3·Pattern 증거 대기2로 분리됐다. [별도 승인 후속17행](audit-reports/2026-09-09-review-widget-episode-implementation.md)은 원본61행의 successor/subset이지 추가17개 고유 작업이 아니다. source9/7의65행·native projection26행과도 합산하지 않는다. 영향 없는 cleanup/detector의 전일 receipt 재사용은 원시각과 predecessor 확인을 보존하며 오늘 새 실행으로 표시하지 않는다.

현행 연결은 [현재 진행표](audit-reports/2026-09-05-postclose-work-inventory.md)와 [9/9 체크리스트](checklists/2026-09-09-stage2-todo-checklist.md)의 최신 후속 기록을 따른다. #119 cache12/report6/exact3·call-local parent와 #23 controller v4/binding1, #74/#89 공통 품질·WS cache15/단축 schedule, census v5/scoped v2 및 #49 acceptance v3의 새 원천/consumer를 각각 대사한다. 구 schema·오전 집계·과거 ingress loss를 새 원천으로 재라벨링하지 않는다. #73의 `PipelineVerbosityNaturalEvidence0908`은 완료 기록이며 새 결함 없이 재개하지 않는다.

| 현행 확인 경로 | 기존 OPEN owner — 9/9 체크리스트 |
| --- | --- |
| #119/#23 exact 원인→controller→다음 PREOPEN/PID/실효성 | `EntryRecheckNaturalAttribution0907` |
| 외부 census·#8/#9/#49 자연 원천/정책/receipt/R6 | `ScannerLookupAttentionNaturalEvidence0908` |
| #76/#77/#82→#78/#80 새 payload·Control·비용·연구 전달 | `AIDecisionActionOutcomeNaturalEvidence0908`, `MainAIQualitySourceGapArtifactContract0909` |
| 위젯 신호·micro 결합 timing·별도 적응형 청산 후속 | `MachineLifecycleTurnoverObjectiveFollowup0909` (21:30~21:40), `WidgetEpisodeRecommendationApplyAcceptance0908` |
| source/WS 연속성·final audit | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`, `PostcloseSourceQualityGateReview0909` |
| native 추천·요약·strict handoff | `PostcloseRecoverySourceAcceptance0908`, `CodeImprovementWorkorderReview0909`, `AutomationTriggerDecisionSummary0909` |

같은 ID의 이관 이력과 당일 신규 ID를 구분하며 위 표로 OPEN 전수 점검을 대체하지 않는다. 과거 별도 승인 배포·재기동·수동 청산 귀속은 당시 범위의 receipt다. 매 실행에서 현재 코드/hash·exact-date 정책·PID·consumer를 다시 읽고, dirty 코드나 unit 시작 성공을 자연 정책 소비·새 수익으로 바꾸지 않는다.

### 1.1 Submit drought 최우선 점검·개선 계약

필수 실행 실패·원천 손상이 있으면 먼저 복구한다. 아래는 검토 순서이며 설치된 cron/producer 순서나 wrapper snapshot을 바꾸지 않는다. 보고서 진단·완료된 수리의 자연 확인은 진행 중에도 읽기 전용으로 할 수 있지만, 추천 구현은 §7의 terminal·generation 고정·native ID·비권한 gate를 따른다.

1. **분모와 최초 병목 고정**: #119 `buy_funnel_sentinel`의 source date/as-of/hash, scope별 primary·threshold/sample floor, exact attempt/cycle·terminal/pending/submitted 보존식을 기록한다. `UPSTREAM_GATE`, `LATENCY_PRE_SUBMIT`, `ENTRY_AI_AUTHORITY_REVALIDATION`, `PRICE_REVALIDATION`, `BROKER_RECEIPT`를 분리하고 raw AI/budget/latency unique 수를 단일 인과 funnel로 연결하지 않는다. 뒤에서 회복된 veto·비차단 fallback을 terminal 차단으로 중복 집계하지 않는다.
2. **탐색과 원천부터 검증**: 독립 market-wide benchmark와 #8/#9/#49로 scanner 밖 미관측·watch/promotion·post-promotion 소비를 분리한다. #11/#74의 row/window exclusion, #27 micro delivery와 #89 WS freshness를 소비하며, enqueue 이전 loss가 raw 감사 분모 밖이면 별도 blocker로 남긴다. 독립 모집단·official master·forward-exact/SLA가 없으면 `insufficient_evidence_scanner_recall`이지 정상 탐색이 아니다. 상세 정의는 [장중 지시문 §2.1](intraday-monitoring-task-instructions.md#21-메인-봇-매매기계)을 따른다.
3. **AI·latency/price 경로 분리**: 같은 attempt의 AI request/response·trusted action·final authority, BBO age·refresh 결과와 다음 blocker를 연결한다. source/transport/schema/stale 결함은 개선 대상이지만 정상 WAIT/DROP·DANGER 차단의 경제적 최적성은 exact executable outcome으로 별도 검토한다. #76/#77/#78/#80/#82는 기존 offline 환류이며 provider0/control0이나 metadata terminal을 판단 개선으로 세지 않는다. #81 legacy OFF·독립 Entry live owner·holding cohort 경계를 유지한다.
4. **기존 대응 owner 확인**: #21은 one-share source-only 진단, #23은 exact 최근3거래일·동일 scope의 daily recheck controller다. 누적 Entry AI gate backtest는 on-demand only이며 무표본 복구용 정기 실행이 아니다. #48 fact sync와 기존 #75/#76/#77 원천이 #50/#51/#54에 연결되는지 확인한다. recheck·Daily·lookup-attention은 각자의 승인 계약으로 판정하며 submit drought를 모든 family의 추가 양수-EV 승인 veto 또는 무조건 승인 사유로 만들지 않는다.
5. **행동 가능한 후속 전달 검증**: `order_entry_submit_drought_auto_resolution` 및 source가 발급한 post-submit/broker receipt/fill quality/Telegram/source taxonomy 등의 native ID를 §7 ledger에 전수 분류한다. #91/#103/#110→EV→runtime summary/gap/lineage→tower→checklist→strict verifier의 같은 source generation과 `buy_funnel_sentinel_primary`, `entry_submit_drought_handoff_selected`를 확인한다. 메모리상 검증·이전 날짜 정상 보고서는 당일 canonical handoff를 대신하지 않는다. 결손은 `buy_funnel_submit_drought_handoff_missing` 등 실제 verifier contract로 처리하며 synthetic 완료 marker를 만들지 않는다.
6. **실효성의 다음 단계 명시**: 허용 수리는 review/fix/validation 후 최초 producer부터 필요한 consumer만 재생성한다. 승인된 후보의 다음 PREOPEN 선택→PID receipt→동일 scope의 자연 submit/fill/terminal·비용 EV는 기존 OPEN owner에 남긴다. 정책 적용 없이 자연 제출이 생기면 관측 회복이지 코드 효과로 귀속하지 않는다. 정상 pre-submit 차단만 있고 accepted submit이 없을 때 #55 cancel-wait·#75 split·scale-in을 첫 해법으로 삼지 않는다. 다만 #75의 기존 Daily 선행 원천 실행은 유지한다.

완료는 세 층으로 보고한다: **진단/코드 수리**, **장후 canonical handoff**, **실제 drought 해소·경제성**. 마지막 층은 선언된 동일 venue/session·관찰창에서 source-quality/원래 탐지 floor가 유효하고 기존 critical 조건을 벗어났는지, 실제 accepted submit 및 후속 전환이 확인되는지 함께 평가한다. 한 건 제출·분모 감소·표본 미달로 경보가 사라진 것을 해소로 확정하지 않으며, executable 기회 부재가 입증된 경우도 `기회 부재`로 별도 보고한다. submit 회복과 비용 차감 수익 개선은 독립 판정이다. 경제성 미관측 때문에 진단 수리 완료를 취소하거나, 수리를 닫기 위해 실주문·floor 하향을 요구하지 않는다.

`SUBMIT_DROUGHT_CRITICAL`만으로 main wrapper 실패나 재기동 사유를 만들지 않는다. 필수 운영이 성공 terminal이고 handoff가 정상이어도 drought 원인/자연 효과가 남으면 종합 상태는 YELLOW다. 미래 작업·정상 대기가 남으면 §9의 `진행 중`, 필수 artifact·handoff 실패 또는 허용 actionable 수리 누락은 RED 기준을 따른다. main의 drought 분모에 위젯·에피소드·sim 주문을 합치지 않으며 독립 owner의 필수 실행·추천 전수 intake를 생략하지 않는다.

### 1.2 위젯·에피소드 진입판단 공동 최우선 계약

[9/9 entry timing 후속 구현 §7](audit-reports/2026-09-09-machine-micro-confirmation-entry-timing-next-actions-review.md#7-후속-사용자-구현-지시에-따른-보완)은 계산 불일치·stale 시작 호가·선택 라벨/floor 요약을 보완하고 4군 연구·frozen policy evidence를 연결한 코드 검증 기록이다. 최초 읽기 전용 반례를 아직 미수리라고 반복하지 않는다. [Widget 평가·선정 후속 §7~§11](audit-reports/2026-09-09-widget-evaluation-machine-signal-quality-review.md#11-사용자-승인-배포기동-실행)은 paired 선정·incident/custody 전달 보완과 18:26 별도 승인 collector/trader 기동 receipt까지 포함한다. 이들은 오늘20:10/21:15 자연 산출물·다음 정책·실수익의 완료가 아니다. 특히 main/WS·각 episode process까지 새 kernel/투영을 소비했다고 확대하지 않는다.

1. **세 판단 단계 분리**: 원래 entry signal/확인2·3회 선정, signal 이후 micro checkpoint0·1·3·5초, 주문 집행 품질을 각각 같은 owner/symbol/profile/venue/session·policy hash에 결속한다. signal·confirmation·target을 동시에 바꾼 개선을 단일 진입 효과로 세지 않는다. 위젯/에피소드는 별도 AI 호출을 새로 요구하지 않으며 main AI의 WAIT/DROP·submit 분모와 합치지 않는다.
2. **장후/runtime 계산 일치**: `machine_confirmation_fixed_price_window_v1`을 양쪽 adapter가 실제 사용했는지 확인한다. 고정1초 창의 시작 호가 age·nominal cutoff·고정 ask 가격·중간 최소 잔량·그 최소점 이전 같은 가격 BUY·이후 refill·첫 trade·route/epoch/sequence를 대사한다. late 호출 뒤 자료·cross-epoch·UNKNOWN·누락된 level은 유효한1초 창으로 보간하지 않는다. 같은 입력/시점/정책의 metric/action parity는 진단 수용조건이며 양수 EV나 실주문을 요구하지 않는다. 기존120행/5호가 bounded 투영도 항상1초를 보장하지 않으므로 window completeness/truncation receipt와 실제 process 반영을 확인한다.
3. **결합의 증분효과**: 기존 `cohorts[].feature_ablation_study`의 `baseline / bid·rebound / depletion·trade backing·refill / combined`를 동일 lifecycle·비용·exit 계약의 4군 모두 유효한 교집합과 chronological holdout으로 비교한다. 속도(qty/sec)는 실제 매수체결·설명되지 않은 감소·refill과 함께 해석한다. 현재 연구의 양의 depletion 사용을 최적 속도 임계값 선정 또는 live 입력 활성화로 보고하지 않는다. 4군은 기존 timing 안의 offline 연구이며 네 개의 새 live 축이 아니다.
4. **전체 신호와 경제성 분모 보존**: actual `signal_decision_at`→checkpoint→submit/미제출→full/partial fill·확인된 미체결→HELD/terminal→비용의 최초 결손을 찾는다. raw 입력수·prospective anchor·4군 행수를 경제성 pair 수로 세지 않는다. 실제 즉시 full-fill control과 선택적 first-hit 진단을 분리하되 지연 ENTER의 executable/fill/exit 증거는 유지한다. CF·실현손익·정상 무노출·censored/결측을 분리하고 비용/손익 미대사는 null로 남긴다. 유입0·불가능한 join은 구조 결손/근거 결손이지 유한 ETA가 아니다. 과거9/8 ingress loss는 격리하고 새 원천을 확인한다.
5. **Widget 평가·#14/#15의 기존 선정 소비**: 삼성 paired 확인/target 평가는 같은 incumbent·최근20 KRX 거래일의 calibration과 독립 날짜 holdout, base/stress 비용 후 EV·순익/일·tail·자본시간·180초 내 양수 청산 빈도를 확인한다. 0.5% 진단 구간은 수익 상한/최소 목표가 아니며 양쪽 결과가 유효하게 끝난 뒤20분 전체 자료를 추가 gate로 요구하지 않는다. 미완료·부분체결·관측 공백은 제외/결손으로 보존한다. 정확한 scale-in trigger가 없으면 source-gap carry하고 BBO 대용으로 선정하지 않는다. 별도 symbol 연구는 기존 baseline 대비 signal-only 또는 exit-only의 한 축을 검증하며, 삼성 계약을 두산/한화의 event/source EXIT·최초 admission40일에 전용하지 않는다. #15 actual-policy semantic cohort·broker 실제금액/비용과 추정비용·#14 source-ready/경제성 상태를 분리한다.
6. **선정→정책→실제 소비**: fixed20/dynamic8 등 각 mode의 실제 validator·관측일/lifecycle/coverage/holdout 조건과 report를 맞춘다. dynamic에 fixed5/10/20일 동시 gate를 복사하거나 진단 수리에 승격 floor를 붙이지 않는다. timing의 frozen evidence hash/path/date와 최신 same-stage veto, widget의 incumbent/study hash·소비자 재계산을 확인한다. 기존 승인된 guard 통과 후보의 exact-date 자동 발행·로딩에는 매번 별도 승인을 새로 요구하지 않는다. 다만 최초 코드 배포·기동 권한, 현재 PID receipt와 이후 자연 정책 소비는 별개다. scopes0/hold는 즉시진입 baseline carry일 수 있으며 강제 선택하지 않는다. 위젯 장중 catalog refresh나 active service의 timer start를 적용 정책 교체·코드 reload로 간주하지 않는다.
7. **권한과 완료 구분**: 위젯 오류는 exact incident/parent/role별 retry·terminal·후행 복구로 확인하고 SELL 목표 실패를 BUY 실패나 신호 부재로 바꾸지 않는다. manual full-flat projection은 과거 custody 복구이며 자동 목표 성공/새 순익이 아니다. 수리·배포·자연 source/정책/consumer·비용 후 EV/순익/빈도/tail·자본점유를 독립 판정한다. 연구 결과가 있어도 실전 BUY/WAIT 계산·threshold·신호/target·주문 guard 변경은 일반 source-only 권한이 아니며, 검증된 기존 자동 계약 또는 별도 승인 범위를 확인한다.

### 1.3 적응형 청산의 별도 후속 경계

[상세계획](proposals/widget-episode-adaptive-exit-implementation-plan-2026-09-09.md)과 [최신 전체-scope 리뷰 §12](audit-reports/2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#12-위젯-원래-exit와-적응형-청산-단일-owner-중재)는 별도 사용자 구현 지시의 후속이다. 전체 종목·프로필 연구/코드 지원과 승인 범위 안 자동 적용이 목표이며, 첫 연구 scope를 다시 선택할 필요는 없다. 그러나 **최초 numeric envelope·실제 launcher 서비스·독립 validator/PREOPEN publisher/enrollment는 미완료이고 새 적응형 청산은 아직 실거래 활성화되지 않았다**. 9/9 18:30 리뷰의 gateway/port/owner-loop·수량 terminal/다음 기존 진입·위젯 원 final EXIT 단일 writer 중재 완료를 전체 활성화로 바꾸지 않는다.

- 장후에는 기존 attribution의 자연 lot/path census→20분 연구 경로→base/stress replay·paired EV/holdout→native 연구 후보와 intended consumer를 확인한다. 연구 scope 수·filled lot 수는 새 계측/경제성 pair 수가 아니며 과거 first-fill/target 시각을 발명하지 않는다.
- 합산 target의 runner/부분취소, 실제 pending BUY 취소·late fill 중재, legacy/force-flat·미해결 전일/취소·거절 복구는 별도 미완료다. 이 코드 결손을 표본 대기로 숨기지 않되 일반 모니터링이 SELL adapter/실주문 권한의 후속 구현 승인까지 상속하지 않는다. 원천/보고 수리와 권한 밖 실행 경로를 분류해 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`에 유지한다.
- exact 수량 terminal/다음 기존 신호 복귀와 주문별 실제 금액·비용 대사는 별개다. 정산 원천 계약 gap은 null/직접 사유로 남기고 반복 같은 비용 조회·가짜0원·새 next-entry 경제성 gate로 해결하지 않는다. terminal/owner/order/cap/cooldown 검증은 계속 유지한다.
- 신규 exit 후보를 기존 entry-timing delay/fixed/dynamic policy나 기존 무손절·목표유지 계약으로 우회 활성화하지 않는다. numeric envelope 없는 연구 위험값·코드/fake service·native ID는 승인값이 아니다. 모든 조기매도 양수·추가 상대1%·5/10/20일 동시 floor·최초 활성화 전 새 exit 실체결 같은 미승인 허들을 추가하지도 않는다.
- 진입 판단 개선과 청산 이후 회전/자본점유 효과를 다른 stage·정책·대조군으로 보고한다. 현재 수익 owner의 사고는 우선 대응하지만 새 exit 연구를 main drought 또는 entry confirmation의 추가 승인 gate로 만들지 않는다.

## 2. 권한 경계

### 2.1 허용 범위

- 로그, process, lock, status JSON, systemd 상태와 artifact freshness의 읽기 전용 점검
- 실패한 report/source-quality/parser/schema/instrumentation/automation wrapper의 최소 코드 보완
- 문서·테스트·오류 detector contract 보완
- `runtime_effect=false`, `allowed_runtime_apply=false`인 `implement_now` 코드 보완
- 위젯·에피소드 추천 중 source collection, parser/schema, report, instrumentation, test, source-only candidate 생성과 자동화 handoff 보완
- 수정 후 관련 producer와 필수 downstream만 순서대로 재실행
- 명백히 중복되거나 멈춘 장후 분석 worker의 증거를 보존한 뒤 해당 장후 worker만 종료·재실행
- 기존 승인된 exact-date PREOPEN 자동 적용 계약의 candidate/policy/handoff 생성 복구. 수동 env 작성은 금지한다.

기존 widget dated policy 발행/loader와 machine timing의 exact-date 자동 발행·소비는 각 기존 owner의 승인 계약을 따른다. 모든 정책을 main PREOPEN env 하나로 취급하거나 이미 승인된 일별 소비에 새 수동 승인을 요구하지 않는다. 반대로 새 adaptive-exit family 등록·승인 envelope 발명·실제 launcher 주입은 기존 timing handoff 복구가 아니다.

### 2.2 금지 범위

- 매매 bot, 위젯 매매 process 또는 에피소드 매매 process의 기동·종료·재기동
- PREOPEN/live runtime env, operator lock, threshold, provider/model/route의 수동 변경
- 실주문·취소, 주문가격·수량·cap·cooldown, broker/account/order guard 변경
- stale/conflict, price freshness, hard/protect/emergency safety 완화
- source-only·sim 결과의 실주문 권한 전환
- 추천 artifact 없이 위젯 종목·machine profile·target·진입조건을 임의 변경
- API 제한을 피하기 위한 호출량·retry 횟수·동시성 상향

금지영역이 실패 원인 또는 추천 구현조건이면 변경하지 않고 `user_authority` 또는 `external_dependency`로 보고한다. 이미 실행 중인 main wrapper는 P0 안전사고가 아닌 한 중단하지 않으며, 실행 시작 시의 immutable wrapper snapshot을 그 run의 계약으로 본다.

과거의 `필요시 우아한 재기동`·별도 collector/trader 배포 승인을 새 문서 현행화나 다른 실행에 포괄 승계하지 않는다. 해당 실행에 별도 재기동 승인이 있을 때만 정확한 대상·검증 코드 세대·기존 주문/custody 보존·정상 종료/새 PID/정책/WS receipt를 대사한다. code generation이 검증 도중 바뀌면 이전 PASS로 기동하지 않는다. runbook/traceability/설치 trigger/실행 snapshot의 계약 충돌은 `contract_drift`로 fail-closed하며 mtime으로 우선순위를 정하지 않는다.

## 3. 현재 장후 실행 owner

설치된 cron과 systemd `ExecStart`를 매 실행 시작 시 다시 확인한다. 아래 표와 실제 설치 상태가 다르면 한쪽을 임의로 정상으로 간주하지 않고 `contract_drift`로 분류한다.

| 시각 | 필수 owner | 정상 terminal 근거 |
| --- | --- | --- |
| `20:05` | KOSPI EOD update | `update_kospi` status와 log의 대상일 최신 DONE |
| `20:10` | main threshold-cycle postclose | postclose status `succeeded`, 최신 wrapper DONE, final verifier terminal |
| `20:10` | postclose DONE controller | controller JSON `done`과 controller cron log 최신 DONE |
| `20:10` | tuning monitoring | status `success`, 단계별 exit code 0, 최신 DONE |
| `20:10` | widget evaluation systemd service | unit `Result=success`; 네 producer가 같은 completed target date 사용 |
| `20:50` | dashboard DB archive | 대상일 최신 DONE |
| `21:05` | AI entry setup paired replay | 날짜별 batch terminal과 consumer terminal 또는 reviewed disabled |
| `21:15` | machine final refresh systemd service | expansion, attribution, weakness hysteresis, entry timing, approval, checklist 결과와 unit `Result=success` |
| `21:55` | postclose finalization | predecessor ready, cleanup DONE, final detector DONE |
| `21:50`까지 및 finalization 후 | System Error Detector | 대상일 canonical run이 unresolved critical 없이 terminal |

NXT 구간의 opportunity census, BUY/HOLD sentinels, rising-missed, pyramid, websocket freshness와 system metric sampler는 main postclose의 입력 owner다. 이 작업의 오류가 main source-quality 또는 verifier 실패로 이어질 때 장애복구 범위에 포함한다.

Swing은 설치된 main postclose cron의 `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false`이면 정상 OFF다. 20:10 main wrapper 안의 machine microstructure/timing/approval 사본은 21:15 systemd가 단일 owner이면 정상 OFF다. OFF·retired 단계를 누락 또는 실패로 세지 않는다. ADM/LDM·bucket·greenfield·전용 institutional aggregate는 복구하지 않는다. 남아 있는 scalp-sim control tower 전체를 폐기된 것으로 오인하지 않고 설치된 flag와 비-LDM consumer만 확인한다. sim/Swing은 현재 우선 상세튜닝 대상이 아니다.

진행표 #17~#20의 퇴역 표시는 20:10 중복 사본에 관한 것으로, 21:15 attribution/timing/approval 기능 전체의 퇴역이 아니다. 새 4군 timing 연구와 adaptive-exit 연구 child는 기존 producer 내부 소비이며 별도 병렬 정기 producer를 추가한 것으로 세지 않는다.

## 4. 모니터링 시작

대상 거래일은 처음 한 번 정하고 자정이 지나도 바꾸지 않는다.

먼저 다음 §4.1의 체크리스트 대사를 수행한 뒤 process·로그를 확인한다. `TARGET_DATE`는 원래 장후 source date, `AS_OF_KST`는 매 점검의 실제 현재 시각이며 둘을 혼합하지 않는다.

```bash
cd /home/ubuntu/KORStockScan
TARGET_DATE="YYYY-MM-DD"
AS_OF_KST="$(TZ=Asia/Seoul date --iso-8601=seconds)"

git status --short
crontab -l
systemctl list-timers --all --no-pager | rg 'korstockscan|widget|machine|postclose'
systemctl list-units --type=service --all --no-pager | rg 'korstockscan|widget|machine|postclose'
ps -eo pid,ppid,lstart,stat,etime,%cpu,%mem,cmd --sort=pid | rg 'run_threshold_cycle_postclose|postclose_done|tuning_monitoring|widget|machine_microstructure|ai_entry_setup|postclose_finalization'
lslocks -o COMMAND,PID,TYPE,MODE,PATH | rg 'KORStockScan|COMMAND'
```

다음 로그와 status artifact를 우선 확인한다.

```bash
tail -n 240 logs/update_kospi.log
tail -n 360 logs/threshold_cycle_postclose_cron.log
tail -n 240 logs/postclose_done_controller_cron.log
tail -n 240 logs/tuning_monitoring_postclose_cron.log
tail -n 200 logs/ai_entry_setup_paired_replay_postclose.log
tail -n 200 logs/dashboard_db_archive_cron.log
tail -n 200 logs/postclose_finalization_cron.log
tail -n 240 logs/run_error_detection_cron.log

jq . "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${TARGET_DATE}.status.json"
jq . "data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json"
jq . "data/report/postclose_done_controller/postclose_done_controller_${TARGET_DATE}.json"
jq . "data/report/tuning_monitoring/status/tuning_monitoring_postclose_${TARGET_DATE}.json"
```

#11 source-quality preflight는 20:10 main wrapper의 해당 stage가 당일 자연 생성 owner다. 예약 전 없는 당일 파일을 실패 또는 현재 실매매 전체 차단으로 해석하지 않는다. 기존/수동 진단 artifact와 자연 산출물을 구분해 생성시각·run/source hash를 기록하고, #74 final audit 및 영향 row/window의 실제 consumer 판정을 확인한다.

파일이 없으면 예정 시각과 process부터 확인한다. 실행시각 전이면 `not_yet_due`, predecessor를 정상 대기 중이면 `waiting`이며 실패로 처리하지 않는다.

### 4.1 모니터링 시점 체크리스트 실행·점검

이 절의 시간·목록 대사 방식은 장중에도 공통으로 사용하되, **실행 권한은 호출한 장중/장후 지시문과 별도 사용자 승인 범위**를 따른다. 장중 점검에 장후 worker 복구·2-pass 권한을 자동 부여하지 않는다.

1. 현재 KST 날짜의 체크리스트 상단 목적·강제 규칙과 OPEN 항목을 읽는다. 자정 이후 복구라면 원래 `TARGET_DATE` 체크리스트의 미종결 owner도 함께 대사하고, 현재 날짜 파일 안의 미래 Due 항목·과거 ID 이관을 구분한다. 파일명·ID 끝자리·섹션 제목 대신 각 항목의 실제 `Due/Slot/TimeWindow`, 본문 선행 조건·Source·Acceptance를 사용한다. 당일 파일 부재나 일정/owner 충돌은 `blocked_missing_evidence|contract_drift`로 남기고 날짜·권한을 추정해 실행하지 않는다.
2. stable ID별로 `checklist path/ID, Due/Slot/TimeWindow, as_of, source date/hash, 실행 owner, 선행 조건, 권한, 최신 receipt, 현재 판정, 이번 실행/점검 결과, 남은 acceptance/다음 확인 시각`을 기록한다. 같은 ID의 이관·반복 관찰은 한 항목으로 대사하고 다른 owner의 주문·경제성은 합치지 않는다.
3. 아래 표로 모든 OPEN을 분류한다. 요청 범위 밖 항목도 미분류로 버리지 말고 해당 owner에 handoff한다. `[x]`는 완료 당시 범위의 증거로만 참조하며 새 결함·필수 freshness/handoff 실패 없이 재실행하지 않는다.

| 시점·상태 | 이번 모니터링에서 할 일 |
| --- | --- |
| 미래 Due 또는 window 시작 전 | `not_yet_due`; 다음 확인 시각을 기록하고 예약 실행을 앞당기지 않음 |
| window 도래, 실행 가능한 권한·원천·선행 조건 충족 | 최신 유효 결과가 있으면 직접 consumer까지 점검. 미실행인 허용 작업은 정상 owner/명령으로 실행→결과 검증→기존 ID에 근거 기록 |
| 이미 running/recovering 또는 정상 선행 대기 | PID/lock·progress·대기 사유와 bounded deadline 확인. 자동 retry나 동일 producer를 중복 실행하지 않음 |
| window 종료 후 미확인·부분 확인 | `overdue_unresolved`로 잔여 조건부터 확인. 복구 가능한 허용 작업만 현재 시각으로 수행하고, 지나간 관측창·수집되지 않은 원천은 소급 성공/재실행으로 합성하지 않음 |
| 선행 producer가 아직 예정 전이거나 정상 bounded wait 중 | consumer 확인 시각이 됐어도 producer를 강제 기동하지 않음. producer의 `not_yet_due`와 consumer의 `waiting`, 예정/완료 예상 근거를 분리 |
| 권한·근거·외부 의존성 결손 | `user_authority|blocked_missing_evidence|external_dependency`; 직접 owner·필요 승인/근거·수용조건을 명시하고 가능한 읽기 전용 확인만 수행 |
| 정상 OFF/retired/valid-empty 또는 이미 해당 acceptance 완료 | 근거가 있는 정상 skip/완료로 대사. 무표본을 만들기 위한 수리·재기동은 하지 않음 |

4. `overdue_unresolved`는 체크리스트 확인 상태이지 process FAIL이 아니다. 당초 window에서 확인한 provenance와 through-close·다음 PREOPEN·경제성 등 남은 조건을 분리하고, 실제 producer deadline 초과·필수 artifact 결손일 때만 §5/§6 장애 대응으로 올린다. 불명확한 기한은 owner 계약을 확인해 기록하며 무제한 `waiting`으로 남기지 않는다.
5. due 작업은 **실제 안전/필수 실행 장애 → source-quality·custody 정합성 → main submit drought 및 위젯·에피소드 진입판단의 공동 최우선 원인/handoff → 그 밖의 owner** 순으로 검토하되 producer 순서와 설치된 자동실행을 보존한다. 각 due/선행 조건에 따라 두 경로를 진행하며 메인 해소까지 기계 점검을 미루지 않는다. source-only 수리도 review gate 후 영향 consumer만 검증한다. custody/state 수정은 신규 진입 가능 상태를 바꿀 수 있으므로 일반 source-only 권한이 아니다. 별도 승인된 exact receipt 복구와 단순 점검을 구분한다.
6. 기존 ID의 실행 근거에 실제 시각·명령/검사 범위·exit/receipt·원천 hash·남은 조건을 남긴다. 전체 Acceptance가 충족됐을 때만 `[x]`로 닫고, 부분 실행은 OPEN을 유지한다. 새 미래 작업만 `Due/Slot/TimeWindow/Track`으로 기록하며 같은 owner를 중복 생성하지 않는다. checklist 변경 후 print-only parser로 ID 유일성을 검증한다. 외부 sync는 실행하지 않는다.
7. 매 관찰 재개·slot 경계·producer terminal 뒤 시각과 체크리스트 변경을 다시 읽어 대기열을 갱신한다. 단회 요청은 as-of 실행·점검 범위와 잔여를 보고하고, 지속 요청은 지정 종료조건까지 새 due 작업을 포함해 반복한다. 둘 모두 미해결 상태를 완료로 바꾸지 않는다.

9/9 예시: `ThresholdDailyEVReport0909` 16:30~16:45와 `HumanInterventionSummary0909` 17:00~17:15는 각 Source에 지정된 **9/8 보고서**를 읽는 점검이며 오늘 main 20:10 조기 재실행이 아니다. `MachineLifecycleTurnoverObjectiveFollowup0909`는21:30~21:40 확인 owner이고 producer는21:15다. `OperatorPolicySuccessionAcceptance0908`은9/9 PREOPEN 부분 수용과 first-use/경제성 OPEN을 구분하며 미래9/10 작업으로 옮겨 해석하지 않는다. `ScannerLookupAttentionCalendarMaintenance1002`만10/2 Due다. 이후 모니터링에는 이 예시나 ID 끝자리를 고정하지 말고 실제 항목을 다시 읽는다.

## 5. 상태 판정과 지속 모니터링

| 상태 | 판정 기준 | 조치 |
| --- | --- | --- |
| `not_yet_due` | 예정 시각 전 | 기다림 |
| `waiting` | 정상 predecessor/resource/artifact bounded wait marker 존재 | wait 이유와 deadline 기록 |
| `running` | PID가 있고 stage/log/artifact 중 하나가 계속 전진 | 계속 감시 |
| `stalled_suspected` | 진행 marker와 artifact가 장시간 정지하고 CPU/I/O/child 변화도 없음 | process·lock·resource 증거 추가 수집 |
| `failed` | 최신 terminal marker가 FAIL, non-zero exit, invalid/missing 필수 artifact | 최초 실패 단계 격리 |
| `recovering` | controller, systemd restart 또는 승인된 최소 재실행 진행 중 | 원 run과 recovery run을 구분해 감시 |
| `done_warning` | terminal 성공이나 허용 source-only warning 존재 | warning 영향과 비권한성 확인 |
| `done` | 필수 terminal·artifact·후행 계약 모두 충족 | 다음 owner로 진행 |

일반 non-zero exit는 실패다. 단, R0–R3의 provider 미실행 source-only 모드처럼 producer가 명시적으로 `exit=2/source_only_blocked_or_deferred`를 정의한 경우에만 해당 모드·단계 결과·필수 artifact를 함께 확인해 source warning과 실행 결함을 구분한다. 이 예외를 strict verifier/controller 실패에 적용하거나 Provider 평가 완료·live 승격으로 해석하지 않는다.

단순 elapsed time만으로 hang을 선언하지 않는다. 다음을 함께 확인한다.

- latest stage marker와 최근 log mtime
- output artifact 또는 checkpoint의 size/mtime 증가
- PID/child PID, process state, CPU·memory·I/O 변화
- system metric sampler의 memory, swap, load, I/O wait
- resource guard·availability guard·artifact wait의 현재 사유와 bounded deadline
- 동일 target date producer의 중복 PID 여부

진행 근거가 있으면 기다린다. 진행 근거가 없고 동일 stage가 반복 timeout하거나 bounded deadline을 넘겼을 때만 실패 또는 hang으로 확정한다.

모니터링 중에는 사용자에게 상태가 변할 때마다 간단히 알린다. 장시간 같은 상태가 계속되면 최대 60초 간격으로 현재 단계, 대기 사유와 다음 확인 조건을 공유한다.

## 6. 실패 대응

실패가 확인되면 다음 순서를 바꾸지 않는다.

`최신 run 확정 → 최초 실패 단계 확인 → 원본 증거 보존 → 원인 분류 → 최소 보완 → review gate → targeted validation → 영향 producer부터 최소 재실행 → verifier/controller/finalization 재확인`

### 6.1 원인 분류

| 원인 | 예 | 기본 대응 |
| --- | --- | --- |
| 정상 선행 대기 | EOD, main DONE, outcome label 대기 | deadline까지 감시; 중복 실행 금지 |
| 일시적 resource pressure | memory/swap/I/O guard 대기 | sampler와 resource 회복 확인; guard 완화 금지 |
| 외부 API rate limit | Kiwoom shared-read defer, HTTP 429 | 기존 bounded retry/cooldown 유지; 호출량 상향 금지 |
| source late/missing | outcome label 또는 exact-date source 미도착 | source owner와 ETA 확인; 없는 값을 합성하지 않음 |
| deterministic code defect | traceback, parser/schema 오류, 잘못된 경로·날짜 | 최소 코드 수정 후 review gate 수행 |
| artifact contract defect | JSON invalid, target date/hash 불일치, downstream missing | producer 수정 후 영향 consumer만 재생성 |
| stale 또는 실제 점유 lock | PID 종료 뒤 lock 점유, 중복 worker | `lslocks`와 PID 확인 후 소유 process 기준 처리 |
| systemd timeout/hang | widget/machine unit timeout | journal과 child tree 보존, 원인 수정 후 해당 service 1회 재실행 |
| 권한 밖 변경 필요 | provider, bot, threshold, order guard | 변경하지 않고 `user_authority`로 보고 |

### 6.2 Lock 처리

`.lock` 파일 존재만으로 stale lock이라고 판단하지 않는다. 반드시 `lslocks`, PID와 process start time을 확인한다.

- 실제 점유가 없으면 lock marker 파일은 그대로 둔다.
- 실행 중인 정상 owner가 점유하면 기다린다.
- 중복 owner가 있으면 target date·snapshot·stage·시작시각으로 authoritative run을 식별한다. 증거 보존 후 권한 내의 중복 장후 분석 worker만 처리하고, 정상 main wrapper나 매매 process는 중단하지 않는다.
- lock 파일 삭제로 문제를 우회하지 않는다. 실행 mutex와 operator policy lock은 다른 계약이다. 오래됐거나 EV 재검증이 없다는 이유로 운영 override를 해제하지 않는다.
- `run_with_owned_log.sh`의 lock은 로그 회전 보호이며 main wrapper 전체 실행 mutex가 아님을 전제로 중복 PID를 별도로 확인한다.

### 6.3 코드 보완과 review gate

장후 실패 또는 추천을 구현해 코드·wrapper·문서를 수정할 때는 `$korstockscan-review-gate`를 적용한다.

1. 현재 worktree의 사용자 변경을 확인하고 관련 없는 변경을 건드리지 않는다.
2. 실패 producer 또는 recommendation owner, 직접 consumer, wrapper, verifier와 테스트를 함께 검토한다.
3. 최초 원인을 고치는 최소 수정만 한다.
4. `review → finding 수정 → 재리뷰 → targeted validation`을 unresolved finding 0까지 반복한다.
5. Python 변경은 관련 pytest와 compile 검사를, shell 변경은 `bash -n`과 관련 wrapper 테스트를 수행한다.
6. 항상 `git diff --check`를 수행한다.
7. 문서를 수정했으면 다음 parser validation을 수행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

문서만 바꾼 경우 직접 consumer/owner·링크·파서·권한 정합성을 검증하고 provider 호출·비용 큰 report 재생성·무관한 trading 테스트를 요구하지 않는다. 진단 수리는 exact 원인·schema·consumer로 닫으며 all-horizon MFE/MAE, 양수 EV, 실체결 또는 승격 floor를 별도 요구하지 않는다. 미래 자연 확인은 기존 OPEN acceptance를 재사용하고 없을 때만 당일 체크리스트에 `Due/Slot/TimeWindow/Track`을 갖춰 기록한다.

GitHub Project와 Google Calendar sync는 실행하지 않는다.

### 6.4 최소 재실행

- 동일 target date 작업이 실행 중이면 중복 실행하지 않는다.
- controller 또는 systemd의 기존 bounded retry가 진행 중이면 그 결과를 먼저 기다린다.
- 수정과 무관한 성공 단계를 다시 실행하지 않는다.
- 실패 producer부터 그 결과를 소비하는 downstream까지만 순서대로 재실행한다.
- 생성된 artifact의 target date, status, source hash/fingerprint와 completion time을 재확인한다.
- main wrapper 전체 재실행은 controller/runbook이 허용하고 부분 재생성으로 닫을 수 없을 때만 사용한다.
- AI Provider 호출은 검증된 checkpoint와 해당 producer의 resumable 상태만 재사용한다. terminal schema/provider/receipt rejection을 새 retry로 재개하지 않는다. 실제 실패 request도 기존 retry/capacity/ledger 계약이 허용할 때만 재시도한다.
- 자정 이후 recovery도 최초 `TARGET_DATE`를 유지한다.
- 이미 검증된 비가역적 과거 ingress/market/identity 결손은 원본을 합성하거나 동일 날짜를 반복 실행해 닫지 않는다. 격리·baseline carry를 유지하고 기존 OPEN acceptance에서 다음 exact-date 원천을 확인한다. 과거 손익 귀속 복원은 신규 수익 증가로 보고하지 않는다.
- postclose worker 재실행 전 기존 PID와 실제 lock 점유가 0인지 확인한다.

## 7. Implement-now 및 위젯·에피소드 추천 2-pass 구현

운영 체인이 terminal이 되고 authoritative generation이 고정된 뒤 수행한다. 진행 중인 wrapper가 읽고 있는 코드나 산출물을 중간에 교체하지 않는다.

### 7.1 Intake

다음 source에서 구현 지시를 수집한다.

- `data/report/code_improvement_workorder/code_improvement_workorder_TARGET_DATE.json`
- `docs/code-improvement-workorders/code_improvement_workorder_TARGET_DATE.md`
- `data/report/widget_collector_expansion_recommendation/`
- `data/report/widget_advisory_calibration/` 및 `data/report/widget_auto_trade_policy_calibration/`의 기존 paired 선정·source/incident handoff
- `data/report/widget_symbol_signal_policy_research/`
- `data/report/widget_symbol_runtime_policy_apply/`
- `data/report/samsung_machine_entry_tuning/`
- `data/report/low_price_two_leg_tuning/`
- `data/report/low_price_two_leg_expanded_candidate_research/`
- `data/report/machine_microstructure_attribution/`
- `data/report/machine_entry_timing_tuning/`
- `data/report/machine_microstructure_policy_approval/`
- 대상일 verifier, runtime apply-gap audit와 다음 checklist의 직접 handoff

timing의 `feature_ablation_study`와 attribution의 adaptive-exit child도 원 producer·source hash·native 추천까지 연결해 누락 없이 점검한다. 비교 arm 이름, 설계 WP 번호, 리뷰 finding 번호는 native 구현 ID가 아니다. 연구 child와 상위 report에 같은 native ID가 투영됐으면 한 항목으로 대사하며, 별도 승인 구현 이력은 그 승인 범위의 successor disposition으로만 연결한다.

각 항목에 authoritative producer가 발급한 stable `order_id` 또는 `recommendation_id`가 있으면 그대로 사용한다. stable native ID가 없으면 자체 ID를 만들거나 추정 구현하지 않고 `invalid_or_missing_authority`로 차단한다. 다음 필드를 ledger에 기록한다.

| 필드 | 내용 |
| --- | --- |
| ID | stable order/recommendation ID |
| owner | main, widget symbol, Samsung machine, low-price machine 또는 공통 automation owner |
| source | artifact path, target date, generation/hash |
| decision | producer 원값 보존: `implement_now`, `code_patch_required`, `objective_followup_required`, `already_implemented`, `observe`, `keep_collecting`, `defer`, `reject` 등 |
| authority | `runtime_effect`, `allowed_runtime_apply`, order/provider/bot/safety 영향 |
| reason | 직접 결함 또는 기대 개선점 |
| consumer | 수정 결과를 소비해야 하는 마지막 artifact/wrapper |
| acceptance | 테스트, report 상태와 handoff 완료조건 |
| final disposition | `already_implemented_verified`, `implemented_pass1`, `implemented_pass2`, `blocked_missing_evidence`, `blocked_external_dependency`, `user_authority`, `invalid_or_missing_authority`, `observed_no_patch`, `deferred`, `rejected`, `removed_or_superseded` |

추천 문장만 있고 구현 위치·consumer·acceptance가 없으면 추정 구현하지 않고 `blocked_missing_evidence`로 둔다. 권한 필드가 없으면 직접 producer/schema에서 비권한 계약을 확인하며, 거기에도 없으면 `invalid_or_missing_authority`로 둔다.

Pass 1 전에 현재 generation의 main/위젯/에피소드 추천 **전수**를 보존한다. 동일 owner의 같은 native ID가 JSON/Markdown에 중복되면 한 항목으로 대사하고, 원본 충돌은 intake 결함이다. ID 없는 row는 원본 경로·위치로 누락 여부만 추적하며 구현 ID를 발명하지 않는다.

- `intake_total = implementation_requested_total + nonimplementation_total`
- `implementation_requested_total = eligible_runtime_effect_false_total + user_authority_total + invalid_or_missing_authority_total`
- `nonimplementation_total = already_implemented_verified_nonrequest + observed_no_patch + deferred + rejected + blocked_missing_evidence_nonrequest + blocked_external_dependency_nonrequest + invalid_or_missing_authority_nonrequest`
- 각 pass 종료: `eligible_runtime_effect_false_total = already_implemented_verified_eligible + implemented_pass1 + implemented_pass2 + blocked_missing_evidence + blocked_external_dependency + eligible_actionable_open`
- 최종 `eligible_actionable_open=0`, `implement_now_unaccounted_count=0`, `intake_unaccounted_count=0`

`implementation_requested_total`에는 native `implement_now|code_patch_required`, §7.2 계약으로 채택된 `objective_followup_required`, 검증되지 않아 수리/증거 대기로 이관된 `already_implemented` 주장을 센다. 위 식의 클래스는 상호배타적이다. 구현이 불필요하다는 검증이 끝나지 않은 `already_implemented` 주장은 완료 계수에 넣지 않고 권한 확인 후 eligible 수리/증거 대기로 분류한다. 비구현 추천의 권한/근거 결손은 대응하는 `_nonrequest` 계수로 기록한다. 이는 집계상 구분이며 final disposition의 원래 사유를 바꾸지 않는다. `removed_or_superseded`는 이전 generation 이력에 남기고 현재 분모와 섞지 않는다.

보존식, 동일 owner/native ID 유일성 또는 source generation 대사가 실패하면 `intake_contract_defect`로 Pass 1을 시작하지 않는다. 각 pass에서 동일한 분모/분류를 재계산하고 ledger의 현재 합계와 이전 generation 변경 이력을 분리한다.

원본 canonical report를 보존한 채 producer가 native ID metadata projection을 발급한 경우 원본 path/row/hash → projection의 native ID → 별도 승인/구현 ledger를 대사한다. 원래 ID 없는 ledger를 덮어쓰거나 두 ledger를 독립 작업으로 합산하지 않는다. projection은 새 시세·경제성 재생성이 아니며 native ID 추가만으로 구현/live 권한이 생기지 않는다. 별도 승인으로 이미 구현된 축의 최신 disposition은 그 승인 ledger에서 검증하되, 미대사 항목은 완료 처리하지 않는다.

### 7.2 구현 가능성 판정

다음은 Pass 1 구현 대상이다.

- `decision=implement_now|code_patch_required`
- artifact 또는 직접 producer contract로 `runtime_effect=false`, `allowed_runtime_apply=false`, 실주문·provider·bot·safety authority 없음이 확인됨
- source-quality, parser/schema, report, instrumentation, test, wrapper, notifier 또는 existing-policy handoff 결함
- 위젯·에피소드 추천 중 기존 owner와 수량·target·safety 계약을 바꾸지 않는 관찰·후보생성·정합성 보완
- 이미 코드가 존재하더라도 producer→consumer→acceptance 근거가 없어 완료로 입증되지 않은 항목

`objective_followup_required`는 구현 위치, intended consumer, acceptance test와 비권한 계약이 artifact에 모두 있을 때만 구현 대상으로 올린다. 단순 정책값 추천, 후보 순위 또는 `observe|keep_collecting`은 코드 구현으로 바꾸지 않고 기존 candidate/policy handoff 상태만 확인한다.

다음은 자동 구현하지 않는다.

- 실주문 authority, 위젯/에피소드 매매 process 재기동, 종목 universe의 실전 확대
- 수량, leg 수, target, entry threshold, cap, provider, broker 또는 hard-safety 변경
- operator lock 해제·변경
- source-only 추천을 수동 live policy나 env로 전환하는 작업

기존 exact-date 자동 policy family의 후보가 정식 guard를 통과한 경우에는 candidate/policy/handoff producer를 복구할 수 있다. 최종 적용은 각 family의 기존 PREOPEN 또는 dated policy loader가 소유하며 수동 env를 작성하지 않는다. 공유 feature kernel의 변경이 현재 BUY/WAIT/REJECT나 SELL에 영향을 주면 단순 report 수리로 분류하지 않고 해당 runtime 변경 권한을 별도 확인한다.

### 7.3 Pass 1

1. authoritative generation의 모든 eligible `implement_now`와 위젯·에피소드 구현 추천을 ID별로 고정한다. 필수 source-quality/운영 장애를 먼저 닫고, 같은 eligible 집합 안에서는 §1.1 main submit drought와 §1.2 위젯·에피소드 진입판단의 최초 병목을 공동 최우선으로 다룬다. 완료된 수리는 최신 consumer/세대만 검증하며 그 밖의 owner도 전수 ledger에서 빠지면 안 된다. §1.3 별도 승인 구현과 일반 source-only 추천의 권한을 합치지 않는다.
2. `already_implemented`는 관련 코드 존재만으로 닫지 않고 producer·consumer·test 근거로 검증한다.
3. eligible 항목을 누락 없이 구현한다.
4. 항목별로 직접 consumer, silent-fail, target-date, source-quality와 owner 분리를 리뷰한다.
5. `$korstockscan-review-gate`를 finding 0까지 반복한다.
6. targeted test, compile/shell syntax, parser validation과 `git diff --check`를 통과한다.

### 7.4 영향 산출물 재생성

Pass 1 검증 후 수정한 최초 producer부터 intended last consumer까지 필요한 범위만 재생성한다.

source9/9부터 승인된 구현/review workflow는 확인한 disposition을 [전수 handoff 리뷰 §7.1](audit-reports/2026-09-09-workorder-summary-preopen-handoff-review.md#71-처리-receipt와-과도한-조건-방지)의 `postclose_recommendation_dispositions` companion에 현재 native ID·row/source hash·review/test/direct-consumer 근거로 기록한다. 이 기록은 별도 live 승인이나 새 사용자 개입을 요구하는 단계가 아니라 현재 허용된 구현 pass의 결과 기록이다. upstream 재생성으로 source hash가 달라지면 새 원장의 동일 ID를 대사한 뒤 유효한 검증 근거만 재결속한다. companion을 근거 없이 만들거나 과거 원장의 완료를 일괄 복사하지 않는다. 운영 요약은 companion이 없어도 미검증/차단 상태를 명시할 수 있으며, 요약 성공과 구현 완료를 구분한다.

- 재생성 전 old generation path/hash/status를 저장한다.
- 중간 producer 실패 시 이전 정상 generation을 덮어쓰지 않는다.
- AI 단계는 valid checkpoint를 재사용한다.
- 위젯과 에피소드 산출물은 main owner와 order/custody를 혼합하지 않는다.
- recommendation candidate 0건은 정상 empty일 수 있으므로 source funnel과 decision reason으로 판정한다.
- 재생성된 workorder, recommendation, verifier와 checklist의 target date와 source hash를 확인한다.
- timing의 frozen evidence/발행 정책과 widget의 incumbent/study receipt를 보존한다. canonical report 재생성만으로 이미 발행·소비된 정책 세대가 조용히 교체되거나 탈락하지 않는지 확인하며, 최신 same-stage veto와 명시적 invalidation 계약은 유지한다.
- 새 산출물 때문에 기존 terminal consumer가 stale해지면 verifier → controller → finalization을 해당 target date로 다시 닫는다.

### 7.5 Pass 2와 fixed-point

1. 새 authoritative generation의 `implement_now`와 위젯·에피소드 추천 전수를 다시 intake한다.
2. 각 ID를 `unchanged`, `new`, `removed`, `decision_changed`로 비교한다.
3. `new|decision_changed` 중 eligible한 항목을 구현하고 동일 review/fix/validation을 반복한다.
4. Pass 2 수정이 다시 추천을 만들면 재생성·diff·구현을 반복한다.
5. 다음 조건을 모두 만족할 때 fixed-point다.

- eligible `new|decision_changed implement_now=0`
- `implement_now_unaccounted_count=0` 및 `intake_unaccounted_count=0`
- `final_eligible_actionable_open_count=0` (현재 ledger의 `eligible_actionable_open`과 동일)
- 위젯·에피소드 recommendation 미분류 건수 0
- review P0~P2 finding 0
- targeted validation 통과
- verifier/controller/finalization의 최신 terminal 상태 확인

`blocked_missing_evidence`, `blocked_external_dependency`, `user_authority`, `invalid_or_missing_authority`는 구현 완료가 아니다. owner, 필요한 근거와 acceptance condition을 남기고 최종 상태를 최대 YELLOW로 제한한다.

## 8. Owner별 필수 확인

### 8.1 Main threshold-cycle

- 9/8 후속 보완 wrapper는 source-quality preflight·trade-fact sync 뒤 기존 `Entry split → AI 원천 materialization → R0–R3 내부 lifecycle paired`를 Daily 앞에서 한 번 실행한다. `Daily/cumulative/AI correction → 후행 EV/요약`이 같은 장후 paired를 소비하는지 확인한다. OFF·deferred 또는 유효 빈 표본을 경제성 승인으로 오인하지 않고, 순서 보완을 이유로 lifecycle·Daily·Provider를 중복 실행하지 않는다. 상세 계약은 [후속 구현 리뷰](audit-reports/2026-09-08-scanner-daily-net-approval-followup-review.md)를 따른다.
- #14 Samsung/#15 low-price는 #74 final audit 뒤의 실제 wrapper 순서·동일 source hash로 한 번 소비되는지 확인한다. 진행표의 review ID 번호 순서를 실행 순서로 오인하거나 앞단에서 중복 실행하지 않는다. #15 실제 정책 cohort·broker-priced 분모/손익 null과 #14 source-ready/경제성을 따로 대사한다.
- 동일 target date 최신 `[START]`, `[FAIL|DONE]`와 status JSON을 결속한다.
- wrapper 시작 시 immutable snapshot과 pipeline snapshot/checkpoint를 확인한다.
- 현재 stage와 마지막으로 완성된 artifact를 식별한다.
- OFF·retired stage를 실패로 세지 않는다.
- AI 필수 단계는 parsed/receipt 계약을, disabled 단계는 disabled provenance를 확인한다.
- 최종 순서는 `EV/workorder → runtime summary/gap/lineage → checklist → verifier → DONE → final verifier → tower → checklist → strict final verifier`가 유지돼야 한다. 요약만 복구할 때에는 tower 직전 일반 verifier로 자기 자신의 이전 handoff 오류를 제거하되, controller 완료는 마지막 strict verifier 명령 성공과 같은 세대 artifact로만 판정한다.
- DONE 이후 control tower를 생성한 뒤 `checklist 최종 refresh → verifier --require-summary-handoff`까지 닫는다. `source_generation_contract`와 checklist `POSTCLOSE_SUMMARY_SOURCES`의 대상일·source SHA256을 실제 파일과 대조한다. 이 마지막 검사를 생략한 verifier PASS는 요약 최신성 완료가 아니다. controller의 일반 복구도 이 검사를 통과해야 DONE이다. verifier/controller 자체 hash는 순환 방지를 위해 요약 source 계약에서 제외한다.
- strict verifier 또는 recovery 명령이 실패하면 이전 성공 artifact를 근거로 DONE 처리하지 않는다. 마지막 bounded attempt에도 최종 strict 명령 성공이 필요하다. EV headline의 `realized_pnl_status`가 미대사이면 PnL null을 유지하며, 건수 일치만으로 exact 비용 검증 완료를 주장하지 않는다. source-only CF route 관찰은 identity/schema/권한 검증 후 actual ADD/NO_ADD와 분리하고 malformed authority는 계속 차단한다.

### 8.2 DONE controller와 AI replay

- controller JSON `done`만으로 끝내지 않고 controller cron log의 최신 DONE을 확인한다.
- fixed 21:05 runner와 controller follower가 날짜별 replay lock으로 중복되지 않았는지 확인한다.
- active fixed runner의 lock이 해제된 직후에는 최신 batch/consumer terminal을 다시 검증한다. 대기 중 읽은 `retry_required`를 그대로 재사용해 이미 끝난 follower를 다시 실행하지 않으며, 재검증에서도 미완료인 경우에만 기존 bounded runner/lock 계약을 따른다. source9/9의22:20 경계 재실행과 [복구 리뷰](audit-reports/2026-09-09-postclose-monitoring-review.md)는 코드 수리·그 run의 실제 재실행·다음 자연 경계 확인을 분리한다.
- batch는 `completed_offline_only`, consumer는 terminal path/hash 검증 상태여야 한다.
- 21:05 follower는 `terminal detailed → #82 calibration v5 → #78 optimizer(당일 선택 고정) → provider0 batch metadata-only 재결속 → #79 holding manifest → #80 consumer` 순서와 같은 generation/hash를 확인한다. 정상 paired 행의 부분 성공 학습과 producer 전체 실패 terminal을 분리하며 학습 가능을 live promotion 성공으로 바꾸지 않는다.
- [9/9 Main AI 보완](audit-reports/2026-09-09-entry-ai-micro-profit-implementation-review.md)의 기존 reaction 실제 payload/전송·optional exact 비용 companion·무참여 연구 교체·단일 사례 prompt 초안이 #76/#82/#78/#80에 같은 parent/hash로 전달됐는지 확인한다. 비용 결손은 null이며 연구 proxy·초안 생성·Provider0 metadata는 실제 판단 개선/실주문 경제성이 아니다. 검증된 새 source가 없는데 동일 replay/Provider 호출을 반복하지 않는다.
- #77 Main AI R0–R3는 지속적인 offline prompt/input 개선 경로다. #81 legacy runtime은 `LEGACY_RUNTIME_AUTHORITY_ENABLED=False`라 표본 누적만으로 활성화되지 않는다. 지원 KRX V2.14/V2.15의 별도 `entry_setup_live_policy` 승격·PREOPEN·receipt와 혼동하지 않는다.
- 기본 OFF인 Codex workorder runner가 실행되지 않은 것을 실패로 보지 않는다.

### 8.3 Tuning monitoring과 archive

- tuning monitoring은 main postclose DONE을 기다린 후 parquet 3종, verified archive와 shadow diff를 단계별로 확인한다.
- pattern lab이 main wrapper 소유일 때 tuning monitoring의 pattern lab skip은 정상이다.
- 20:50 archive와 tuning monitoring archive가 같은 파일을 처리할 때 검증·원자 publish·skip 계약을 지켜야 한다.
- 미검증 raw를 정상 종료 목적으로 삭제하지 않는다.

### 8.4 Widget evaluation과 추천

- systemd unit의 `ActiveState`, `SubState`, `Result`, `ExecMainStatus`와 journal을 확인한다.
- advisory calibration, auto-trade policy calibration, symbol signal research, runtime policy의 네 producer와 중간 EOD 대기 gate가 같은 completed target date를 사용해야 한다. EOD gate를 다섯 번째 report producer로 세지 않는다.
- Kiwoom shared-read budget이 소진되면 빈 source로 성공 처리하거나 API 호출량을 올리지 않는다.
- 종목 확대·signal policy 추천은 exact source, sample floor, source-quality와 기존 owner guard를 확인한다.
- §1.2의 확인2/3 paired 선정, 검증 incumbent 대비 signal-only/exit-only, source/incident 및 exact manual-flat projection을 네 producer의 직접 consumer까지 대사한다. recipe carry·source-gap·sample floor·holdout/경제성 미달·실행품질 veto를 분리하고, 신호 변경일에 target이나21:15 entry timing이 같은 stage를 중복 변경하지 않는지 확인한다.
- 추천의 source-only 구현은 Pass 1/2에 포함한다. 실전 종목 확대 또는 매매조건 변경은 정식 policy candidate와 PREOPEN guard 없이는 `user_authority`다.
- 수정 또는 source 회복 뒤 evaluation service만 1회 재실행하고 unit `Result=success`와 네 단계 산출물을 확인한다.

### 8.5 Episode machine과 추천

- Samsung과 low-price machine의 profile, episode, leg, order/custody owner를 main/widget과 분리한다.
- 추천 artifact의 target date, source hash, decision, runtime effect와 acceptance test를 확인한다.
- source/parser/report/instrumentation과 candidate handoff 보완은 Pass 1/2에 포함한다.
- 기존 수량·leg·target·validity·safety 계약을 변경하는 추천은 자동 구현하지 않는다.
- exact-date PREOPEN policy candidate는 기존 apply/verify consumer까지 handoff를 검증하되 수동 env로 적용하지 않는다.
- 실제 signal/leg별 micro checkpoint·원래 target/custody·수동 successor 주문을 분리한다. §1.3의 adaptive-exit 연구/부분 구현이 있더라도 최초 승인 envelope와 실제 launcher/정책/enrollment가 닫히기 전에는 기존 보유를 이관하거나 목표주문을 취소하지 않는다.

### 8.6 Machine final refresh

- 21:15 단계는 `expansion → attribution → weakness hysteresis → entry timing → approval → checklist`다.
- attribution 실패 때문에 weakness/timing이 실행되지 않은 경우 return code 0을 성공으로 해석하지 않는다.
- 각 단계의 return code와 최종 unit `Result`를 함께 본다.
- wrapper의 최종 exit 우선순위는 `checklist builder → policy → weakness hysteresis → entry timing → attribution → expansion`이므로 최종 exit code만으로 최초 실패를 추정하지 않는다.
- source missing, timeout 또는 memory cap이 반복되면 동일 재시도를 반복하지 말고 최초 source/contract/resource 원인을 보완한다.
- attribution/timing/approval의 source-only 구현 추천을 Pass 1/2에 포함한다.
- §1.2 공통 kernel/version·window completeness·actual signal census·4군 교집합/holdout·모드별 실제 floor·frozen evidence와 최신 owner veto를 같은 generation으로 대사한다. source9/8의 signal15/eligible0·target9/9 scopes0은 과거 baseline carry이며 오늘 source나 다음 정책의 기대 건수로 고정하지 않는다.
- adaptive-exit child의 source/replay/study/native 후보는 기존 attribution 안의 별도 출구 연구다. timing study와 entry delay 정책 소비를 혼합하지 않으며, 연구 child 생성 성공을 최초 exit family 승인/실주문 활성화로 세지 않는다.
- 보완 후 해당 service만 1회 재실행하고 정책 후보 유무와 관계없이 모든 필수 단계가 terminal인지 확인한다.

### 8.7 Finalization과 error detector

- finalization은 main postclose, controller/follower, tuning monitoring, dashboard archive의 exact-date terminal을 기다린다.
- 9/9 source부터 설치된 widget evaluation·machine final refresh unit의 당일 시작/성공 terminal도 확인한다. 실행 중이면 기존 bounded wait, 실패이면 cleanup 금지다. 명시적 masked-OFF는 `done_off_masked`로 분리하며 이전 날짜 성공이나 단순 timer disabled를 당일 성공으로 바꾸지 않는다.
- 선행 terminal 뒤 기존 controller의 `--summary-handoff-only`가 최대2회 시도로 늦은21:15 source에 필요한 일반 verifier→tower→checklist→strict만 갱신한다. summary 단계는600초 process-group timeout/강제종료 grace10초이며 upstream producer·EV·Provider·Codex·매매 process·정책 변경은 allowlist 밖이다. 실패하면 cleanup을 생략하고 detector 후 FAIL로 닫는다. 원 controller wrapper/replay의 terminal 시각은 보존하고 finalization의 `summary_handoff_verified`와 갱신된 controller JSON/strict를 마지막 요약 closure 근거로 추가한다.
- `recommendation_intake`는 selected/non-selected와 main/widget/episode의 native ID·원문 decision·현재 disposition·원천/행 hash를 전수 대사한다. 실제 본문 digest/보존식도 검증하므로 source marker만 남은 요약은 PASS가 아니다. 선택적 exact-generation disposition companion은 승인된 구현/review workflow가 발급하며 과거 frozen/별도승인 ledger를 덮어쓰지 않는다. 운영 DONE, 구현 fixed-point, 증거 차단, PREOPEN 계획/manifest 및 저장 PID receipt/현재 PID·경제성은 별도다. 형식·source 수리에 양수EV·실체결·추가 표본 floor를 요구하지 않는다.
- predecessor fail/timeout이면 cleanup이 실행되지 않아야 한다.
- predecessor가 모두 성공한 뒤 cleanup DONE → `[DONE] postclose_finalization ... detector_handoff=started` → `[DONE] postclose_final_detector`를 확인한다. 중간 finalization DONE은 detector self-audit 순환 방지 marker일 뿐 최종 성공이 아니며, 이후 detector 실패의 최신 FAIL이 우선한다.
- 기본 predecessor wait 5100초/23:20 KST hard deadline과 cleanup·detector 각 600초 상한을 확인한다. predecessor 실패/timeout이면 cleanup은 건너뛰되 bounded detector를 실행하고 finalization FAIL로 닫는 현행 계약을 따른다.
- finalization 실패 후 재실행은 선행 owner를 먼저 정상화한 뒤 수행한다.
- error detector의 stale 과거 FAIL보다 최신 recovery DONE이 권위를 갖는지 확인한다.
- 자정 이후 요약·source-only tail만 복구했고 cleanup/detector의 입력·종결 계약을 무효화하지 않았음이 확인된 경우, exact-date predecessor를 읽기 전용 재확인하고 기존 cleanup/detector receipt의 시각을 별도로 보고한다. 현재 날짜로 동작하는 detector를 전일 재실행 증거로 가장하지 않는다. 실제 선행 실패나 영향받은 detector 검사가 남은 경우에는 이 예외로 완료하지 않고 target-date 지원/권한 결손을 명시한다.

## 9. 최종 판정과 보고

다음 표를 모두 채운다.

| Owner | Target date | Latest state | First failure | Repair | Validation | Latest terminal |
| --- | --- | --- | --- | --- | --- | --- |
| EOD | | | | | | |
| Main postclose | | | | | | |
| Final verifier | | | | | | |
| DONE controller/follower | | | | | | |
| Tuning monitoring | | | | | | |
| Dashboard archive | | | | | | |
| Widget evaluation | | | | | | |
| Episode recommendations | | | | | | |
| Machine final refresh | | | | | | |
| Finalization/error detector | | | | | | |

최종 상태는 다음처럼 사용한다.

- `진행 중`: 대상 거래일의 필수 운영 owner에 아직 예정 전 작업 또는 정상 running/waiting/recovering이 남으면 현재 상태만 보고하고 GREEN 완료로 종료하지 않는다. 정해진 기한 내 정상 대기를 RED 장애로 오판하지 않는다. 별도 다음 거래일 자연 관찰이나 장기 maintenance 예정은 당일 실행 중 상태와 구분하고 아래 YELLOW의 잔여 조건으로 보고한다.
- `GREEN`: 대상일 마지막 필수 owner까지 due가 되었고 모든 due 필수 owner가 성공 terminal이고, eligible implement-now·추천 fixed-point와 해당 검토 범위 review finding 0까지 닫혔으며 unresolved failure와 실제 점유 stale lock이 없다. 아래 YELLOW의 미완료 조건도 없어야 하며 운영 GREEN 자체가 전략 수익 개선의 증명은 아니다.
- `YELLOW`: 필수 실행은 정상 terminal이지만 source-only warning, 외부 dependency, user-authority 추천, 공동 최우선 경로의 원인/자연 효과·경제성 acceptance 또는 다음 거래일 관찰이 남아 있다. 적응형 청산의 미완료 실행 연결·최초 승인은 표본 대기나 전체 구현 완료로 숨기지 않는다.
- `RED`: due 필수 owner의 실패·확정 hang·비정상 missing, deadline/실패 때문에 닫히지 못한 verifier/controller/finalization, 또는 완료를 선언하면서 누락한 허용 범위 actionable 구현이 있다.

보고는 `판정 → 근거 → 다음 액션` 순서로 간단히 작성한다.

1. `Postclose Control State: 진행 중|GREEN|YELLOW|RED`
2. 대상 거래일과 관찰 종료시각
3. owner별 최신 terminal 상태
4. 발견된 최초 실패와 직접 원인
5. 수정 파일과 수정 내용
6. review finding 및 targeted validation 결과
7. 재실행한 최소 범위와 이전 FAIL보다 최신인 성공 근거
8. implement-now와 위젯·에피소드 추천 Pass 1/2 ledger 및 fixed-point 결과
9. 남은 warning, external dependency 또는 user-authority 항목
10. submit drought: scope·as-of/source hash·raw/causal 분모·최초 병목, 개선 owner/native ID·현재 disposition, canonical handoff/다음 PREOPEN/PID 상태, 실제 제출 회복과 비용 차감 경제성의 별도 판정
11. 체크리스트 대사: ID별 Due/TimeWindow·이번 실행/점검·최신 receipt·완료 또는 잔여 조건. due 미실행·기한 경과·정상 대기·권한/외부 의존성·미래 예정·범위 밖을 구분하고 미분류 0을 확인
12. 위젯·에피소드 진입판단: 원 신호/확인 횟수와 micro0/1/3/5초의 별도 분모·공통 계산/실제 PID 소비·4군 연구의 동일 표본/비용/holdout·선정/정책 전달, 실체결 EV/순익/빈도/tail/자본점유. 코드 수리·배포·자연 acceptance·경제성을 각각 판정
13. 적응형 청산: source-only 연구/후보·별도 승인 구현 완료 범위, 미완료 중재/복구·정산 원천 gap·최초 envelope/launcher/PREOPEN/enrollment 상태. 신규 BUY/SELL 권한·기존 보유 이관·실현수익을 추정하지 않음

작업이 진행 중이면 운영 완료를 선언하지 않는다. 현재 stage, PID, 마지막 progress 근거, 기다리는 조건과 bounded deadline을 알린다. 명시적으로 요청받은 지속 모니터링은 지정 종료조건까지 계속하며, 단회 점검은 as-of 상태와 미완료 조건을 보고하고 닫되 이를 장후 완료로 표현하지 않는다.
