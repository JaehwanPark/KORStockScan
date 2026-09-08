# 장후작업 상세검토 진행 목록

작성 기준: `2026-09-08 KST` (기존 review index 1~119 유지; 운영 근거는 아래 개별 as-of)

#45 후속 갱신: [반등·재진입 1차 구현 리뷰](2026-09-06-rebound-reentry-implementation-review.md). 일반 2-leg episode flat 신규 진입은 기존 timing 내 source-only paired 평가와 **조건 통과 시 별도 사용자 승인 없는 PREOPEN 자동 적용**을 연결했다. 현재 자연 EV와 신규 journal은 미확인이며 생산 정책/봇은 변경하지 않았다. 위젯 순차매수·passive/partial·terminal no-entry·세션 초과 exit는 미지원 replay로 분리한다. 아래 #45의 “평가 미구현/별도 실전 설계”는 최초 계획 시점의 기록이며 이 갱신과 리뷰 문서가 현재 상태다.

현행 기준: 2026-09-08 Plan Rebase §1·§7~§8, 9/8 체크리스트와 거기서 연결한 9/7의 아직 OPEN인 자연증거 owner를 반영한다. 과거 기능/병합 commit은 완료 증거이며 현재 owner를 대체하지 않는다.

목적: 설치된 장후 자동화의 각 실행 단위를 순서대로 검토하면서 목적·목표·기대효과·운영상태·상세검토 상태·연결 lock을 한 표에서 추적한다. 실행 원칙과 owner는 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1~§8과 [2026-09-08 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)가 우선한다.

## 1. 이번 갱신 판정

- **9/8 오후 문서 대사**: 아래 최신 연결은 [15:00 관찰](2026-09-08-intraday-monitoring-1500.md)과 [15:45~16:10 due 실행·복구](2026-09-08-due-checklist-custody-recovery-review.md), 당일 checklist의 후속 기록을 반영한다. 이 문서 갱신에서 운영 모니터링·복구를 새로 실행하거나 병행 worktree 코드 전체를 재검증한 것은 아니다. 현재 작업은 두 지시문의 시점별 체크리스트 실행·점검 계약을 맞추는 문서 범위다.
- **#119/#23 최신 계약과 실제 소비 분리**: 오전 schema5/exact2 이후 새 결함에 대한 cache12/report6/exact3 수리와 call-local frozen parent 보완을 각각 [추가 수리](2026-09-08-buy-funnel-entry-recheck-remediation-review.md), [15:00 계측 리뷰](2026-09-08-intraday-monitoring-1500.md)에서 추적한다. [drought 후속 구현](2026-09-08-drought-handoff-objective-final-review.md#후속-권장보완-구현)의 controller `source_binding_version=1`·지시별 summary receipt·strict/PREOPEN 공통 검증·20유효일 유지 진단은 기존 `EntryRecheckNaturalAttribution0907`의 자연 수용이다. 과거 원천 복원·신규 계측 PID 소비·실제 제출/순익은 코드 완료와 별개다.
- **#74/#89 상세검토 대기 해제, 자연 수용 유지**: [2차 보완 리뷰](2026-09-08-ws-freshness-source-quality-remediation-review.md)의 1,093 PASS는 audit v2 공통 품질 gate·WS finalize/episode receipt·snapshot as-of·그룹별 rolling 진단/경제성 분리의 검토 범위다. 새 자연 finalize→native workorder와 audit→실제 verifier/PREOPEN은 `PostcloseSourceQualityGateReview0908`에서 확인한다. 단순 무표본 때문에 완료된 코드 리뷰를 반복하지 않는다.
- **장중 완료/잔여 정정**: 15:51 writer-safe 감사의 결손1행 격리 후 `IntradaySourceQualityGateCheck0908`은 완료 기록이다. 이후 유입·unknown warning 장후 handoff는 별도다. 별도 승인으로 4 HELD 원장과 SamsungE&A registry를 복구했지만 Widget/Runtime/Micro acceptance는 OPEN이다. 16:00:56에도 main submit0이며, custody 수리·공간 확보·코드 PASS를 drought 해소나 새 수익으로 합산하지 않는다. 과거 PID/잔고 수치는 새 모니터링 때 다시 읽는다.
- **전략 operator lock 후속 구현**: [25개 전수 분류·기존 owner 통합 리뷰](2026-09-08-operator-policy-succession-review.md). 최초 effective 9/9이며 현재 env/원본 lock/PID는 변경하지 않았다. 직접 승계2·정식 Entry owner 통합5·기존 owner 관리 component2·보호/운영11·혼합1·비활성4. 후속 명시 승인으로 weak-pullback/low-profit-stagnation의 한 단계 exact replay + 실제 full-fill 품질 → rolling_20d → 다음 적격 PREOPEN의 한 cohort·최대 7일 canary → 실제 profile 검증/미달·만료 복귀를 연결했다. Daily-only 전달, 동일 날짜 양쪽 arm 요구, 복수 합격 전부 탈락, 비판단 로그 설정 hash 및 score cohort 소비 결함을 보완했다. 무제한 탐색·보호 lock 해제가 아니며 배포·새 자연 source·실제 PID·비용 차감 순익은 `OperatorPolicySuccessionAcceptance0908` 한 곳에서 계속 확인한다. 새 원천 없이 9/9에 canary를 강제하지 않는다.
- **9/8 최우선 개선 목표는 메인 submit drought 해소**다. 필수 운영 terminal·source-quality 확보를 선행하고, §6 순서로 최초 병목과 수정 가능성을 확인한다. 주문 건수만 늘리는 것이 아니라 기존 안전 계약 안에서 유효 기회의 제출→체결→비용 차감 순이익 경로를 회복하는 목표다. 검토 우선순위이지 cron 재배열·guard 완화·실주문 권한이 아니다.
- **9/8 10:10:03 KRX 관측**: `buy_funnel_sentinel_2026-09-08.json`의 `KRX|KRX_REGULAR`은 `SUBMIT_DROUGHT_CRITICAL`. exact attempt **64 = terminal 59 + pending 5 + submitted 0**, 미분류 terminal 0이며 terminal causal 축은 upstream28/latency26/Entry-AI 재검증5/price0/broker0이다. raw stage unique AI25/budget41/latency6은 서로 다른 모집단이라 25→41→6의 인과 funnel로 쓰지 않는다. JSON SHA256=`06f59784582fa63364a42f7733d0e19774c27197b1d1b1d47e3f36b14f2f53df`; 이는 읽은 generation 기록이며 이후 자연 갱신 파일이나 장마감 판정을 대신하지 않는다. source: `data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-08.json` (저장소 루트 기준).
- **오전 수리·배포 기록 갱신**: [10:03 재리뷰](2026-09-08-intraday-due-work-execution.md#1003-재리뷰와-남은-작업-실행)의 위젯 blocked-policy hash 결정성·과거 receipt 비정규화·micro frozen compatibility 검증은 관련295 PASS 후 `c1bd9660`으로 main/원격에 반영됐다. [09:27 재기동](2026-09-08-graceful-restart-0927.md)은 그보다 앞선 `f67a7ec7`/PID461794의 별도 승인 기록이다. 커밋은 새 위젯 PID 소비·drought 해소 증거가 아니다. raw41529/72stage 감사 PASS도 enqueue 전 micro loss를 포함하지 않으므로 Provider hold·자연 acceptance는 유지한다.
- **9/8 현행 판정: 문서·계약 보완 종결과 운영 YELLOW를 분리**한다. [9/7 source 우선순위 복구 리뷰](2026-09-08-postclose-priority-repair-review.md)의 955 targeted PASS는 요약 세대·controller·CF 귀속 등 해당 수리 범위의 증거다. 전체 119개 작업의 경제성 전수검토 완료가 아니다. 9/8 00:27:43 strict verifier는 handoff PASS/필수·후행·세대 결손 0, 00:27:44 controller DONE이다. cleanup/detector는 원래 9/7 23:23:29/23:23:30 receipt를 보존했고 재실행하지 않았다.
- **실적 귀속 복원**: CF route 관찰 3행 분리로 NXT 실제 eligible lifecycle 0→2, custody gap 5→2. 두 기존 거래의 비용 차감 +453원은 과거 귀속 복원이지 신규 수익/전략 개선량이 아니다. 다른 집합의 headline PnL은 `null/unresolved_trade_review_count_mismatch`를 유지한다. legacy identity 2행과 과거 market 18행을 합성하지 않는다.
- **AI·machine는 새 원천 필요**: provider0 source/metadata 재생성은 consumer terminal을 닫았지만 KRX/NXT exact control 각 0, holding checkpoint 미충족, machine 8 anchor/eligible 0이다. 검증된 9/7 ingress loss는 격리·immediate baseline carry를 유지한다. 같은 날짜 무변경 재실행 대신 기존 OPEN의 다음 exact source를 확인한다.
- **별도 승인 위젯·에피소드 적용**: [추천 구현·적용 리뷰](2026-09-07-widget-episode-recommendation-implementation-review.md)의 399 targeted PASS 및 9/8 policy/설치 receipt는 별도 사용자 승인 범위다. widget 080220, low-price 기존8/신규3 적용, inventory56/eligible53/격리3, 신규 timer6 설치. 자연 preflight/PID·신호·체결·비용 EV는 `WidgetEpisodeRecommendationApplyAcceptance0908` OPEN이다. 이 문서 갱신으로 추가 운영 변경을 실행하지 않는다.
- **ledger 중복 방지**: frozen postclose 65행(구현 검토9/비구현56)의 ID 결손26은 당시 canonical 기록이다. 이후 별도 승인 native projection 26행(구현11/이미 검증2/관찰8/보류5)은 원본 hash·위치로 연결한 후속 ledger이며 새 경제성 재생성이 아니다. 65+26을 고유 작업 총수로 합산하거나 9개 workorder 증거 대기까지 완료로 바꾸지 않는다.

아래 9/7 이전 요약은 당시 기록이며 위 현행 판정과 개별 행의 최신 근거를 우선한다.

- **9/7 현행 요약**: #8/#9 및 #11의 상세검토 완료는 유지한다. #119/#23, #49, #76/#78/#82의 최신 코드 보완·재리뷰도 종결했으며 각 자연 acceptance는 아래 §5.1의 기존 OPEN owner로 분리한다. #77은 [R0–R3 보완 리뷰](2026-09-07-main-ai-r0-r3-remediation-review.md)에서 연구/누적 심사·격리·명목 비교와 별도 현행 Entry adapter 연결을 구현했다. adapter 기본 OFF·등록/첫 승인/배포·새 collector 성능/자연/실수익 acceptance는 별도다. #79/#80 전체 상세검토 완료로 확대하지 않는다. #81 legacy runtime은 DISABLED이며 예약 호출 제거 후 정상 SKIP이고 별도 `entry_setup_live_policy`와 같은 경로가 아니다.
- **배포와 자연 효과 구분**: [9/7 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)의 `FullWorkspaceSecondMergeRestart0907` 완료 기록은 16:59 main `81fac7da`·PID653712/verify PASS를 보고한다. 이는 당시 배포 receipt이며 현재 PID를 고정하는 값이 아니다. 위젯 배포·기계표식 전환은 `ManualVetoCoexistenceDeployment0907`, 다음-session 적용은 `SameSymbolMachineScopePreopenAcceptance0908`에 별도 OPEN이다. 이번 문서 현행화는 배포/재실행 작업이 아니다.
- **9/7 17:05 설치 확인**: cron은 20:05 EOD, 20:10 main(stop-only/Swing OFF)·controller·tuning monitoring, 20:50 archive, 21:05 replay, 21:55 finalization이며 systemd timer는 widget20:10/machine21:15다. 당시 미래 작업은 `not_yet_due`였으며 현재 예약 전 여부는 새 target date/시각으로 판정한다.
- **아래 9/5~9/6 및 오전 수치·ON 판정은 당시 기록**이다. 최신 코드 상태는 개별 행, 운영 상태는 exact-date artifact/PID receipt, 실행 owner는 당일 체크리스트를 따른다.

- **2026-09-06 전체 재통합 리뷰**: dirty 전체 범위를 재검토했고, 최종 리뷰에서 #45의 source-only 비교비용이 exact-date 적용 후보와 결속되지 않은 live 권한 경계 1건을 발견해 다음 거래일 비용 값·날짜·SHA-256을 candidate/evidence/runtime에 고정했다. 수정 후 변경범위 20개 test module **1,562 PASS**, rebound 단독 **34 PASS**, Python 47개 Black/Ruff/compile, wrapper 3개 `bash -n`, parser 42개 OPEN, diff check를 통과했다. 생산 report/policy/env·봇 상태·실주문은 변경하지 않았다.
- **main 통합 완료**: 누적 장후 runtime 계약 보완을 전용 브랜치에 커밋·푸시한 뒤 명시적 merge commit으로 main에 병합했다. 병합 전 수정·신규 테스트 전체 2,928건, 포맷 보완 후 receipt·수익 귀속 관련 1,184건, Entry/Institutional/Microstructure 관련 1,260건을 각각 PASS했다. Python 97개 변경 파일 Black/compile, wrapper 3개 `bash -n`, 신규 systemd unit verify, checklist parser와 diff check도 PASS했다.
- #15~16, #21, #23, #26~27까지 상세검토·보완 결과를 반영했다. 현재 완료 범위는 저가 2-leg/확장 추천의 source-only 경제성, one-share 기회 진단과 일일 drought controller, Institutional 전용 aggregate 폐기, Microstructure freshness/delivery v3/finite outcome 진단이다. 다음 자연 PID·PREOPEN·장후 성과 확인은 각 checklist OPEN owner가 소유한다.
- #119 BUY Funnel Sentinel→submit drought handoff의 **R1~R5 코드 보완·재리뷰를 종결**, 자연 적용/성과는 OPEN이다. schema5/exact2 source binding, 실제 broker/upstream stage, retry cycle, 비차단 fallback 분리, 분모/schema/downstream generation 대사를 구현하고 raw suppression·확장 upstream의 recheck 권한 누출을 추가 보완했다. 통합 **1,061 PASS**, [현행 리뷰 §11](2026-09-07-buy-funnel-submit-drought-handoff-review.md#11-r1r5-보완-구현과-최종-재리뷰). 완료 증거는 `BuyFunnelFinalContractReviewRepair0907`, 자연 후속 owner는 `EntryRecheckNaturalAttribution0907`이다. 새 exact history·다음 PREOPEN/PID 소비가 확인되기 전 실적용·수익 개선으로 해석하지 않는다.
- Entry AI gate 누적 backtest는 `on_demand only`이고 20:10 정기 wrapper producer가 아니다. 병합 전 gate에서 이를 반대로 요구하던 stale retirement 회귀를 정정해 일일 controller 유지와 누적 backtest 미호출을 함께 고정했다.
- #23 R1→R5 구현·재리뷰: **코드 보완 종결, 자연 적용/성과 확인 OPEN**. 새 평가/과거 arm 분리, 잔량 확장 full-position 경제성, 시장·세션별 stop/재심, 기존 총량 내 durable submit 예약, 누적 진단 정기 실행 제외를 구현했다. 최종 통합 회귀 **2,088 PASS**, 관련 파일의 검증 전후 해시 동일, 검토 범위 미해결 finding 0건이다. 실제 env/PID·보고서는 이번에 덮어쓰지 않았으며 새 schema 산출물과 자연 비용 차감 EV는 별도 확인이다. 현재 판정은 [리뷰 §10](2026-09-06-one-share-drought-final-review.md#10-r1r5-구현수정재리뷰), 완료 증거는 `EntryRecheckFeasibilityRepairReview0907`, OPEN owner는 `EntryRecheckNaturalAttribution0907`이다.
- 9월 6일 ADM/LDM 정리: #22, #29~42, #52~53의 scalping matrix·context·bucket·bridge 실행/승인 경로를 폐기했다. #28은 LDM 전용 단독 실행만 제거하고 #13 AVG_DOWN의 증분 CF·full-policy replay helper는 유지한다. raw candidate/order/fill/terminal lineage, Samsung·Entry AI gate·AVG_DOWN·PYRAMID 및 hard safety는 폐기 대상이 아니다.
- PREOPEN은 폐기 namespace를 OFF로 고정하고 보관 산출물의 재승격을 차단한다. 상세검토·검증 근거는 [ADM/LDM 정리 리뷰](2026-09-06-adm-ldm-retirement-review.md)를 따른다. bot 재기동이나 기존 다음-session env의 수동 재적용은 하지 않았다.
- 이번 정리의 최종 통합 회귀는 **3,036 PASS**다. 코드리뷰·수정·재리뷰 반복 후 검토 범위 미해결 finding 0건이며, 9월 7일 실제 PREOPEN/PID/장후 소비는 별도 자연증거 확인이다.
- #21/#23 후속 재개 **이전 격리 검증 기록(현재 ON 근거 아님)**: ADM/LDM 폐기 완료 상태에서 one-share 진단과 기존 recheck 조건부 정책의 producer→PREOPEN→runtime/receipt 계약을 재검증했다. F1~F6, source-quality 불합격 기간의 복귀 근거 오인, 폐기 필터의 생성기 해시 손실을 보완했고 최종 통합 회귀 **2,345 PASS**다. 9/4 report·sim-only catalog와 9/7 PREOPEN를 재생성·verify PASS했다. recheck는 KRX 정규장/NXT 애프터마켓 ON, 장중 확대 OFF이며 실제 PID·수익개선은 자연증거 대기다. 상세는 [recheck 최종 리뷰 §7](2026-09-06-one-share-drought-final-review.md#7-admldm-폐기-완료-후-재개-검증)을 따른다. 위 ADM/LDM 폐기 검증 수치와 합산하지 않는다.
- #14 Samsung entry **v9 구현·재리뷰 종결, 자연 효과 검증 OPEN**. actual-policy/as-of·청산 원장, 기계별 연속 적용 cohort, broker 체결금액 EV와 기존 timing owner의 Samsung 상승·반등 recipe를 연결하고 신규 subset tightening 권한은 제거했다. 962 PASS이며 현재 OPEN owner는 `SamsungEntryRiseReboundNaturalEvidence0907`이다.
- #45 Market panic breadth **R1~R5 및 일반 2-leg 반등 평가/자동 PREOPEN 구현 종결, 자연 효과 검증 OPEN**. 이전 정상 관측 688건/CF 4건은 새 paired 근거가 아니다. 후속 [구현 리뷰](2026-09-06-rebound-reentry-implementation-review.md)는 8/31~9/4 격리 재생성에서 과거 신규 원천 부재로 pair/후보 0건임을 확인했다. 최종 통합 리뷰에서는 다음 거래일 비용 계약의 값·날짜·hash를 candidate/영수증/runtime에 결속해 source-only 비교값의 직접 live 권한 누출을 차단했다. `MarketWeaknessReboundReentryIntegration0907`은 완료 증거이며 현재 OPEN owner는 `MarketWeaknessNaturalEvidence0907`과 미지원 recipe/유지 판정의 `MarketWeaknessReboundReentryRetention0911`이다. 실제 운영 lock·정책값·봇 상태는 변경하지 않았다.
- 아래 1~13 종결 및 1,964 PASS 수치는 9월 5일의 이전 검증 기록이다. 이번 정리 변경의 통합 검증 수치와 혼용하지 않는다.

- `Bot stop`부터 `AVG_DOWN recovery calibration`까지 13개 실행 단위의 코드·계약 점검과 허용된 보완을 완료했다.
- 1~9번은 기존 동작과 격리·재현·source-only 권한 계약을 확인했다. 별도 전략 또는 runtime 변경은 없었다.
- 10~12번 PYRAMID/source-quality 구간은 exact event·BBO/resolver·terminal·비용·candidate identity를 보완했다. 2026-09-04 구형 원천은 exact-ready 0건이므로 경제성 실패가 아니라 과거 source contract 결손으로 유지한다.
- 13번 AVG_DOWN은 production cadence capture, frozen full-policy snapshot, 독립 A/B/C 상태 재현, 격리된 기존 holding/exit policy adapter, source audit, postclose report, AI/PREOPEN/verifier 연결을 구현했다.
- 구현 종결은 실적용·수익개선 종결이 아니다. 2026-09-05는 토요일이므로 새 자연 runtime frame, paired exit, 당일 장후 AI, 다음 PREOPEN 선택, PID 소비 및 post-apply EV는 아직 관찰되지 않았다. 이 확인은 OPEN `AvgDownPairedExitRuntimeEvidence0907`과 `PyramidEconomicFeasibilityHandoff0907`이 소유한다.
- 이번 재검증은 관련 AVG_DOWN/PYRAMID/holding/scale-in/source-quality/daily-AI/PREOPEN/verifier 테스트 `1,964 passed`, 기존 외부 pandas-ta 경고 1건이다.

## 2. 상태와 lock 표기

| 표기 | 의미 |
| --- | --- |
| `구현·점검 종결` | 요청한 코드·계약 보완과 targeted validation 완료 |
| `자연증거 대기` | 구현은 닫혔지만 다음 자연 거래일 산출물·runtime 소비·EV는 미확인; 기존 OPEN acceptance로 추적 |
| `부분 확인` | 명시 시각의 일부 자연 receipt만 관측; 일중 전체·실현 EV 또는 모든 PID 반영을 의미하지 않음 |
| `not_yet_due` | 예약된 producer 실행 전; 누락/장애나 live block으로 단정하지 않음 |
| `상세검토 대기` | 현재 자동실행 상태만 식별했고 이번 순차 상세검토는 아직 시작하지 않음 |
| `OFF` | 현재 wrapper/cron 정책상 비실행 |
| `RETIRED` | 자동실행 경로 폐기 |
| `E1` | owned-log writer/rotation lock; 전체 wrapper 실행 mutex는 아님 |
| `E2` | threshold resource guard와 artifact generation lock |
| `E3` | 개별 intraday `tmp/run_*.lock` |
| `E4` | rising-missed/PYRAMID 공용 `tmp/intraday_heavy_analysis.lock` |
| `E5` | tuning-monitoring 단일실행 lock |
| `E6` | 날짜별 AI entry replay lock |
| `E7` | systemd oneshot 단일 인스턴스 |
| `E8` | system metric writer lock |
| `E9` | log/storage maintenance lock |
| `P14/P18` | 기존 PYRAMID quality/operator lock |
| `P15` | 기존 rising-missed normal BUY bridge lock |
| `P16/P17` | scalp-sim AI budget/candidate-window lock |

### 9/8 승인 문턱 교차 점검

[소액 순이익 승인 재설계·재점검](2026-09-08-small-net-profit-approval-review.md)에 이어 [1~3 후속 구현](2026-09-08-scanner-daily-net-approval-followup-review.md)에서 #49의 고정 +0.10%p 문턱을 작은 양수 net·거래일 변동/불확실성 검사로 대체하고, #50의 당일 paired 소비 지연을 실행 순서로 보완했다. 아래 번호는 stable inventory ID이며 #75~77의 원천 생성은 #50보다 먼저 실행된다. 기존 자연 owner에서 PREOPEN/PID/실수익·20유효일 유지 판단을 계속한다. #75 등 상세검토 대기 작업 전체를 완료 범위로 편입하지 않으며 운영/source guard·retired 권한은 그대로다.

### 2.1 모니터링 시점의 체크리스트 대사

이 진행표는 상세검토 index와 근거 연결이며 **실행 큐는 현재 체크리스트**다. 모니터링을 명시적으로 요청받으면 [장후 §4.1](../postclose-tuning-result-review-task-instructions.md#41-모니터링-시점-체크리스트-실행점검) 또는 [장중 §4.1](../intraday-monitoring-task-instructions.md#41-모니터링-시점-체크리스트-실행점검)에 따라 실제 KST 시각까지 도래한 항목을 전수 분류하고 허용된 실행·검증까지 수행한다. 이 문서의 열람·현행화는 해당 절의 실행 요청이 아니다.

- 파일 날짜·ID 끝자리 대신 `Due/Slot/TimeWindow`와 Source·선행 조건·Acceptance를 읽는다. 지난 window의 부분 확인과 실제 장애, 미래 Due와 정상 선행 대기, 코드 리뷰 종결과 다음 자연/경제성 수용을 구분한다.
- 같은 ID는 이관 이력을 보존한 한 owner로 대사한다. 완료 `[x]`는 근거이며 새로운 실패 없이 다시 OPEN하지 않는다. OPEN도 구현 권한이나 매매 process 재기동 권한 자체가 아니다.
- 최신 성공 결과가 있으면 소비 계약을 확인하고, 미실행인 due 작업은 요청 범위·권한·source가 충족될 때만 정상 owner로 실행한다. 진행 중 producer를 복제하거나 PREOPEN/매매 시간창을 소급 실행하지 않는다.
- ID별 현재 판정·이번 수행·최신 receipt·미수행 사유·남은 수용조건을 기존 checklist에 남긴다. 미분류가 없어야 하며, 부분 실행·기한 경과·권한 차단을 전체 완료로 합치지 않는다.

| 9/8 기존 실행 owner | 시점 판정에 필요한 경계 |
| --- | --- |
| `IntradaySourceQualityGateCheck0908` | 15:51 완료 기록. 장후 `PostcloseSourceQualityGateReview0908`과 이후 원천까지 완료한 것은 아님 |
| `RuntimeEnvIntradayObserve0908`, `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`, `WidgetEpisodeRecommendationApplyAcceptance0908` | 오전 window 경과 후에도 현재 receipt·through-close/경제성 잔여를 분리해 점검. 시간 경과만으로 실패 또는 재기동 필요를 선언하지 않음 |
| `ThresholdDailyEVReport0908`, `HumanInterventionSummary0908` | 16:30~16:45 / 17:00~17:15에 각 Source의 9/7 보고서를 읽음. 당일 main 20:10 조기 재실행 아님 |
| Entry recheck / Scanner / AI / Pipeline / Pattern / Daily / Postclose recovery 기존 OPEN | 실제 20:10 이후 선행 owner와 자연 산출물을 확인. review index 순서로 cron을 재배열하지 않음 |
| `OperatorPolicySuccessionAcceptance0908`, `ScannerLookupAttentionCalendarMaintenance1002` | Due 9/9 PREOPEN / 10/2 POSTCLOSE. 같은 9/8 파일의 항목이라도 오늘 overdue가 아님 |

위 시각은 9/8 checklist 예시다. 재개 시 실제 현재 시각과 변경된 원 항목을 다시 확인하며 새 고정 일정·중복 checkbox를 이 진행표에 만들지 않는다.

## 3. 상위 장후 실행 목록

아래 표는 20:10 main wrapper 내부 단계만 나열했을 때 빠지는 병렬·후행 작업을 포함한 상위 스케줄이다. 기존 15:10 sim overnight preclose는 2026-09-06 폐기되어 현행 스케줄에서 제외한다.

| 시각 | 작업/owner | 목적·목표 | 기대효과 | 운영상태 | 이번 상세검토 상태 | 연결 lock |
| --- | --- | --- | --- | --- | --- | --- |
| `09:05~19:20` | BUY Funnel Sentinel → submit drought handoff (#119) | KRX/NXT BUY→submit 병목을 exact attempt 기준으로 분리해 장후 workorder에 전달 | broad threshold 완화 없이 실제 병목 owner를 식별하고 submit·후속 EV 분모 회복 | producer ON / source-only handoff ON | **계약 수리·재리뷰 종결, 자연 적용 대기**; [#119 현행 리뷰 §11](2026-09-07-buy-funnel-submit-drought-handoff-review.md#11-r1r5-보완-구현과-최종-재리뷰) | E3; 당일 장후 E2 미확인 |
| `20:05` | EOD KOSPI update | NXT 종료 뒤 일봉 DB·추천 원천 갱신 | 장후 producer의 최신 시장자료 확보 | ON; 9/7 20:55:49 terminal | 운영 terminal 확인; 전체 상세검토는 별도 | 없음 |
| `20:10` | Main threshold-cycle wrapper | bot stop 뒤 tuning/source-quality/AI/approval/verifier 체인 실행 | 다음 PREOPEN 후보와 결손 workorder 생성 | ON, stop-only | 1~13 이전 종결; #22/#29~42/#52~53 폐기 검토, 나머지는 각 행 기준 | E1, E2, E3/E4/E6, P14~P18 |
| `20:10` | Widget evaluation systemd | advisory·auto-trade calibration과 다음-session widget policy 생성 | widget 독립 정책의 당일 source-date 일치 | ON; 9/7 22:08:41 success | 네 producer/EOD 연결 확인; 별도 승인 추천은 §5.1 | E7 |
| `20:10` | Postclose DONE controller | main wrapper terminal 대기·복구·최종 verifier 조정 | 부분 실패 은폐 방지 | ON; 9/8 00:27:44 source-date 9/7 DONE | strict 명령/복구 실패 은폐 방지 보완 종결; 자연 wrapper는 별도 | E1, follower E6 |
| `20:10` | Tuning monitoring | main postclose DONE 뒤 Parquet/DuckDB late-pass 갱신 | 분석 조회속도와 데이터 재사용 개선 | ON; 9/7 22:35:39 success | 운영 terminal 확인; 전체 상세검토는 별도 | E5 |
| `20:15` | Swing live dry-run | swing 연구 산출물 생성 | swing 후보 탐색 | **OFF** | 현재 불필요 지정 유지 | 없음 |
| `20:50` | Dashboard DB archive | 검증된 DB/raw 세대 압축 | 디스크·조회비용 억제 | ON; 9/7 20:50:30 DONE | 운영 terminal 확인; 전체 상세검토는 별도 | E9 |
| `21:05` | AI entry setup paired replay follower | terminal detailed→#82→optimizer 당일 freeze→provider0 metadata 재결속→holding manifest→consumer | 신규 상세결과를 동일 세대 offline 평가에 환류 | ON, source-only; #81 live OFF | 연결부 보완 유지; 9/7 batch terminal/9/8 metadata consumer 확인, control·holding provider 준비와 전체 경제성은 별도 | E6 |
| `21:10` | Swing model retrain/auto-promote | swing 모델 재학습 | swing 모델 갱신 | **OFF** | 현재 불필요 지정 유지 | 없음 |
| `21:15` | Machine microstructure final refresh systemd | expansion→attribution→hysteresis→entry timing→approval→checklist 실행 | machine 단일 owner의 다음-session 후보 종결 | ON | 단일 owner 확인; 9/7 22:13:18 success. ingress-loss 격리/8 anchor·eligible0, 새 source 대기 | E7 |
| `21:55` (bounded) | Postclose finalization | 모든 predecessor terminal 뒤 cleanup·final detector 실행 | 미완료 원천 보존과 장후 종결 확인 | ON, fail-closed | 9/7 cleanup23:23:29/detector23:23:30; 9/8 predecessor7개 ready 재확인. 원 receipt와 복구 시각 구분 | E1, E8, E9 |

## 4. 20:10 main wrapper 상세 목록

표의 번호는 순차 상세검토를 위한 기존 review index다. #117 tower 뒤에 #112 checklist 최종 refresh와 #116 strict verifier가 다시 실행되며 번호는 재부여하지 않는다. 일반 final verifier PASS만으로 이 마지막 요약 handoff를 완료 처리하지 않는다. `Wrapper immutable snapshot`은 실제 프로세스 bootstrap에서 `Bot stop`보다 먼저 고정되지만, 완료 구간 명칭인 `Bot stop ~ AVG_DOWN recovery calibration`과 index 연속성을 유지하기 위해 번호는 바꾸지 않았다.

### 4.1 격리·수집·초기 품질 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Bot stop | 장후 자원 격리 | postclose 시작 시 bot session 중지, 완료 후 자동 재시작 금지 | 분석 중 주문·DB·메모리 경합 방지 | ON, cron=`stop` | **구현·점검 종결**; 기존 stop-only 유지 | E2 |
| 2 | Wrapper immutable snapshot | 실행 도중 wrapper 변경 격리 | syntax-checked sibling snapshot으로 한 generation 실행 | 혼합 버전 실행 방지 | ON | **구현·점검 종결**; 변경 불필요 | 임시 snapshot |
| 3 | Pipeline immutable snapshot | 장후 입력 고정 | 동일 raw hash를 모든 후속 producer가 소비 | 보고서 간 재현성 확보 | ON | **구현·점검 종결**; 변경 불필요 | E2, partition lock |
| 4 | Snapshot retention cleanup | 오래된 snapshot 정리 | 보존기간 밖의 완료 snapshot만 제거 | 디스크 증가와 scan 비용 억제 | ON | **구현·점검 종결**; live source 삭제 권한 없음 확인 | E9 |
| 5 | Threshold compact/backfill | raw event를 날짜별 compact로 변환 | checkpoint·source hash·bounded resource guard로 EOF 도달 | 후속 EV 분석 입력 안정화 | ON | **구현·점검 종결**; 기존 availability/resource fail-closed 유지 | E2, partition lock |
| 6 | Sim post-sell feedback | sim 후보의 성숙 결과 생성 | sim outcome과 monitor snapshot 완결 | sim 정책 평가 가능 | ON | **구현·점검 종결**; real execution authority 없음 확인 | E2, P16/P17 |
| 7 | Limit-down watch report | 하한가·급락 위험 관찰 | exact-date source-only 위험 보고 생성 | 급락·유동성 위험 오판 방지 | ON | **구현·보고서 계약 점검 종결**; 유효 정책 후보·PREOPEN/PID 소비·natural match·post-apply EV는 미판정. 이를 소유하는 별도 현행 OPEN 항목은 없음 | E2 |
| 8 | Rising-missed finalization | 놓친 상승 후보 최종 집계 | intraday source와 blocker를 exact-date로 종결 | missed-upside 원인 분해 | ON | **구현·점검 종결**; source-quality pending은 별도 표기 | E2, E4, P15 |
| 9 | Rising-missed scout workorder | 개선 가능한 missed 원인을 구현 항목으로 변환 | stable workorder와 source-only authority 결속 | 반복되는 entry source gap 감소 | ON | **구현·점검 종결**; runtime threshold 권한 없음 | E2, P15 |
| 10 | PYRAMID feedback finalization | 추가매수 기회·차단·종료 연결 | same-event gate/BBO/resolver/terminal/coverage 보존 | 무효 추가매수 표본 제거 | ON | **구현·점검 종결, 자연증거 대기** | E2, E4, P14/P18 |
| 11 | Observation source-quality preflight | 필수 field·label·lineage 검사 | 결손 row/window 제외 또는 fail-closed | 오염 자료의 EV·runtime 승격 방지 | ON, hard gate | **구현·점검 종결**; AVG_DOWN replay frame 계약 포함 | E2 |
| 12 | PYRAMID quality calibration | 기존 min-profit 한 축의 증분 경제성 재현 | 동일 complete episode에서 current/candidate/NO_ADD와 비용 1회 비교 | 작은 유효 순기여 후보 식별, 과도한 허들 제거 | ON | **구현·점검 종결, 자연 AI/PREOPEN 증거 대기** | E2, P14/P18 |
| 13 | AVG_DOWN recovery calibration | 기존 shallow buy-pressure 한 축의 A/B/C 경제성 재현 | production frame→full-policy replay→report→AI/PREOPEN/verifier 연결 | 중복 경로·고정 종료 착시 제거, 유효 후보만 선별 | ON | **구현·점검 종결, 자연 paired/PID/EV 증거 대기** | E2; 신규 operator lock 없음 |
| 14 | Samsung machine entry tuning | 실제 적용 정책·신호·청산 기준의 독립 머신 진입 분석 | 기존 timing owner에서 Samsung 상승·반등 후보를 비용 차감 EV로 선별 | 허위 subset tightening 제거와 종목 전용 진입 순이익 개선 기대 | ON; v9 구현·재리뷰 종결, 자연 증거 대기 | [Samsung 최종 리뷰](2026-09-05-samsung-machine-entry-final-review.md): actual-policy/as-of·청산 원장·연속 적용 cohort·broker 체결금액 EV·상승/반등 recipe 연결, 962 PASS. 실적용·수익개선은 `SamsungEntryRiseReboundNaturalEvidence0907` OPEN | E2, E7; 신규 operator lock 없음 |
| 15 | Low-price two-leg tuning | 저가주 2-leg 실제 결과·적용 정책 감사 | 실제 applied 정책 carry; 부분집합은 진단만 유지 | 허위 개선·근거 없는 정책 변경 차단 | ON | LP-F1/F2 보완 유지; 별도 승인 9/8 적용은 inventory56/loader-ready53/격리3. 관측 subset의 신규 tightening 자동승격은 없으며 자연 효과는 별도 | E2 |
| 16 | Low-price expanded recommendation | 기존 두 필터 경로 비교·후보/profile 연구 | 동일기간 순이익·양수 EV, 날짜 간 HELD, half 진단 | EV 착시와 보유 단절 제거 | ON, content-bound checkpoint/resume | LP-F3~F5 및 native ID/projection 보완 종결. 경제성 연구 자체는 source-only; 별도 사용자 승인 기존8/신규3 적용은 §1·§5.1의 독립 receipt/ledger로 확인 | E2 |
| 17 | Machine microstructure attribution 20:10 사본 | 과거 중복 attribution 실행 | 21:15 단일 owner로 통합 | 이중 heavy 실행·혼합 generation 방지 | RETIRED (2026-09-05) | 20:10 실행·복구 경로 제거; 현재 기능 owner는 21:15 final refresh | 없음 |
| 18 | Market-weakness hysteresis 20:10 사본 | 과거 중복 hysteresis 실행 | 21:15 attribution 후 단일 순서로 통합 | stale attribution 소비 방지 | RETIRED (2026-09-05) | 20:10 실행·복구 경로 제거; 현재 기능 owner는 21:15 final refresh | 없음 |
| 19 | Machine entry timing 20:10 사본 | 과거 중복 timing 실행 | 21:15 단일 owner로 통합 | 이중 후보·정책 generation 방지 | RETIRED (2026-09-05) | 20:10 실행·복구 경로 제거; 현재 기능 owner는 21:15 final refresh | 없음 |
| 20 | Machine policy approval 20:10 사본 | 과거 중복 approval 실행 | 21:15 결과만 PREOPEN handoff | 중복 승인·알림 방지 | RETIRED (2026-09-05) | 20:10 실행·복구 경로 제거; 현재 기능 owner는 21:15 final refresh | 없음 |

17~20번은 기능 자체의 폐기가 아니라 **20:10 중복 scheduled copy의 폐기**다. 현재 네 기능은 위 21:15 `korstockscan-machine-microstructure-final-refresh.timer`와 전용 wrapper만 소유한다.

### 4.2 진입·분할·LDM·microstructure 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 21 | One-share threshold opportunity | 강제 1주 제한의 기회비용 진단 | primary blocker·실제 청산 후 결과를 분리해 기존 family source-only 작업지시 생성 | 불필요한 제한과 계측 결손 식별; 보고서 자체에는 주문 권한 없음 | ON, source-only | **구현·점검 종결**; runtime 전환·수익개선 증거와 분리 | E2; 신규 operator lock 없음 |
| 22 | Scalp Entry ADM | entry 상태·행동 matrix | score 단독이 아닌 다차원 분류 | 진입 판단 정밀화 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 23 | Entry recheck daily controller + Entry AI gate diagnostic | 기존 recheck의 조건부 drought 대응과 누적 score/action 진단을 분리 | 같은 시장·세션 drought→고정 probe profile→PREOPEN→exact attempt/full-position receipt→fill-quality별 EV; 누적 sweep는 별도 CLI 수동 진단 | 허위 arm/정상 잔량 경제성 누락·scope 혼합 중단·미제출 한도 소진을 제거; 실제 EV·wall-clock 개선은 자연 확인 | **일일 controller ON 유지**, 누적 backtest 정기 실행 제외/on-demand only; 새 v4/v3 산출물·실제 PID 소비 확인 대기 | **R1~R5 구현 회귀 2,088 PASS, 폐기 후 최종 통합 2,345 PASS**. 고정 profile 운영 제어이며 최적 신호 자동 탐색은 아님. 구 9/4 artifact/기존 9/7 env ON을 새 계약 실적용으로 해석하지 않는다. 다음 자연 owner `EntryRecheckNaturalAttribution0907` | E2; 7/3 recheck lock archive-disabled, 이번 변경 없음 |
| 24 | Scalp-sim overnight | 미결 sim 포지션 종결 | 과거 overnight outcome 완결 | 과거 sim label 누락 감소 | RETIRED 2026-09-06 | 실제 SCALPING no-overnight 목적과 불일치하고 clean-baseline 327건 모두 `SELL_TODAY`, `HOLD_OVERNIGHT=0`이었다. 15:10 producer·current report/EV/verifier 소비를 제거하고 기존 holding loop의 venue별 마지막 매도 가능 구간에서 `scalp_same_session_terminal_exit`로 통합했다. historical artifact/내부 replay는 archive-only | 별도 튜닝축 없음; same-session sim post-sell feedback이 종결 증거 소유 |
| 25 | Overnight OpenAI recovery | 미결 sim 결과 보완 | active-undecided가 있을 때만 OpenAI 호출 | 과거 sim outcome 완결성 | RETIRED 2026-09-06 | 20:10 live OpenAI recovery와 provider env를 제거했다. CLI와 잔존 preclose wrapper는 폐기 상태만 반환하며 current artifact를 생성·변경하지 않는다 | provider budget 불필요; 종결 실패는 terminal reconciliation incident로 분리 |
| 26 | Institutional flow context | 기관수급 context 생성 | lifecycle feature 제공 | regime 구분 개선 | RETIRED 2026-09-06 | sole consumer인 scalping ADM/LDM 폐기에 따라 scheduled producer와 current EV/runtime 소비 제거. exact AI investor/program context는 유지하고 historical artifact·CLI는 archive/offline only | E2 |
| 27 | Microstructure reaction context | micro 반응 feature 생성 | entry/holding receipt 및 같은 시점 결과 진단 | 정확한 source-quality·기회 진단과 기존 개선 작업 전달 | ON diagnostic; A~D 구현, 자연 PID 미확인 | [구현 후 재리뷰 §7](./2026-09-06-institutional-microstructure-context-final-review.md#7-ad-구현-후-재리뷰): 공통 freshness/feature v2, delivery v3·cache/logger, finite same-attempt EV/rollup schema2, 독립 후보 제거, unique coverage/workorder 검증. 20건은 진단 기준이고 PREOPEN 승격은 N/A. stale wrapper 회귀는 on-demand 계약으로 정합화했으며 다음 정상 기동/장후 receipt만 checklist OPEN으로 유지 | E2 |
| 28 | Scale-in incremental CF | 추가 leg의 증분 효과 분리 | 기존 보유와 추가분 손익 분리 | scale-in 착시 제거 | 독립 단계 RETIRED | #13 경제성 replay helper 유지; report namespace 공통 retirement filter 등록 | 독립 E2 사용 종료; wrapper `-m`/artifact wait 없음 |
| 29 | LDM daily | lifecycle 단계별 귀속 | entry→exit 병목 분류 | 개선 owner 식별 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 30 | Scalp-sim scale-in approval | sim scale-in window 판정 | sim-only 확대 여부 결정 | 표본 수집 가속 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 31 | Lifecycle AI attribution | AI 결과의 단계 귀속 | prompt 영향 분리 | AI 경제성 분석 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 32 | LDM context refresh | AI attribution 반영 | same-date matrix 재계산 | context 누락 방지 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 33 | Lifecycle AI context | 다음 AI 입력 context 생성 | feature bundle 완결 | prompt 품질 향상 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 34 | LDM parent refinement | 얇은 child를 parent 가설로 통합 | 검증 가능한 분모 확보 | 영구 thin-bucket 감소 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 35 | Lifecycle bucket daily | 신규·충돌 bucket 탐색 | daily source-only taxonomy 생성 | 이상 조기탐지 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 36 | LDM rolling5d | 단기 lifecycle EV | 최근 변화 확인 | 시장 적응 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 37 | Bucket rolling5d | 단기 parent 집계 | daily noise 완화 | 후보 지속성 확인 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 38 | LDM rolling10d | 중기 lifecycle EV | 일별 변동 완화 | 안정적 방향 확인 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 39 | Bucket rolling10d | 중기 parent 집계 | 표본 안정성 확인 | 과적합 완화 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 40 | LDM MTD | 월간 lifecycle EV | promotion window 생성 | 실전 근거 강화 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 41 | Bucket MTD | 월간 parent 집계 | sim/live candidate 입력 | promotion 안정화 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 42 | Runtime apply bridge | 후보와 실제 consumer 연결 | blocker/owner/env mapping 명시 | 보고서만 생성되는 경로 차단 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 43 | Scalp-sim auto-approval | sim catalog 자동 생성 | 다음 PREOPEN sim handoff | sim 연구 자동화 | ON | LDM 정책·가설 제외; rising-missed 독립 source 유지 | E2, P16/P17 |
| 44 | Latency recommendation | 독립 latency 임계값 추천(구 목적) | BUY Funnel/performance diagnostic으로 통합 | 죽은 후보·중복 권한 제거, hard safety 유지 | RETIRED (2026-09-06) | [보완 최종 검증 §7](2026-09-06-latency-recommendation-retirement-review.md#7-r1r3-보완-구현-및-최종-재검증): R1 raw manifest/writer 차단, R2 calibration·AI 후보 제거, R3 event-candidate 허위 결손 제거와 가격해결기 오귀속 해소. 1,490 PASS·변경 범위 미해결0 | 과거 artifact archive only; 별도 spread-only operator lock 유지. 구현 완료 기록 `LatencyRetirementFinalReviewRepair0907`, 다음 자연 확인 owner `LatencyDiagnosticNaturalEvidence0907` |
| 45 | Market panic breadth | 시장 panic 폭 계산 | 개별종목과 시장 위험 분리 | 과잉 차단·놓친 상승과 약세장 신규노출의 비용 차감 EV 균형 | ON; R1~R5 및 일반 2-leg 반등 평가/자동 PREOPEN 1차 구현; 자연 적용/경제성 검증 대기 | 기존 CF 4/778건은 새 paired 근거 아님. 신규 source→기존 timing 내 A0/A2 비교→조건 충족 시 추가 승인 없는 한 scope PREOPEN 적용. 위젯 순차·partial/passive·세션 초과 exit 등은 지원 외 계약으로 분리. [1차 리뷰](2026-09-06-rebound-reentry-implementation-review.md); 자연 검증/Retention OPEN | E2, E3, E7 유지 |
| 46 | Panic-sell defense report | panic regime 종결 | recovery 상태 귀속 | exit 안정화 | ON | 상세검토 대기 | E2 |
| 47 | Scale-in split plan | AVG_DOWN 총수량 보존 2-leg 정책 | 유효한 paired 증분 경제성을 policy·PREOPEN에 연결 | 체결 참여율·순이익 개선 기대, 실제 효과 미검증 | PRODUCER ON / v3 보완 완료 / 9월 7일 env 비선택 | [보완 §6](2026-09-06-scale-in-split-order-plan-final-review.md#6-f1f7-구현-및-반복-리뷰): F1~F7 및 재리뷰 결함 수정. BUY/SELL lifecycle join·공유 TTL 10/20초·fixed control·버전별 R6·결측 이월·paired>=3/2일·lineage 일치. 시장가 runtime 제외·3-leg 진단 전용. 943 PASS, 검토 범위 미해결0. v1/v2 승격 금지, 실제 cancel delta는 미계측 진단 | 구현 완료 기록 `ScaleInSplitFinalReviewRepair0907`; 자연 실행·실효성 확인 OPEN owner `ScaleInSplitNaturalEvidence0907`. 현재 표본 부재를 강제 수량/조건 완화로 해결하지 않음 |
| 48 | Strategy-position fact sync | 완료 거래 fact 갱신 | 실제 체결·PnL 확정 | EV 정확성 향상 | ON | 상세검토 대기 | DB writer lock |
| 49 | Scanner lookup-attention tuning | `ka00198` 조회집중도로 기존 동일 tier 감시자원을 재배분해 순EV 개선 | 소액 net·불확실성 기반 실제 경제성/독립 holdout + 별도 CF 교체 pair | 고정 개선폭 제거, 원천 행 통계 재현·기간 한정 유지 판단 | 장후 ON; v4 + small_net_v1 보완, 자연 효과 미검증 | [1~3 후속 리뷰](2026-09-08-scanner-daily-net-approval-followup-review.md): base/holdout/R6 고정 +0.10%p 제거, candidate net·증분의 robust SE, full-fill/독립 holdout/tail/immutable receipt 유지. 자연 owner `ScannerLookupAttentionNaturalEvidence0908` | E2; 기존 scope·상한 유지; 통과 시 다음 장전 자동 적용, 별도 재승인 없음 |
| 50 | Daily threshold report | 일별·clean-baseline 누적 후보 통합 | 실제 비용 차감 순EV·반복성 승인 | 소액 양수 edge를 당일 근거로 식별 | ON; 승인 재설계·기존 profile 재선택 보완, 자연 수용 대기 | [동일 장후 연결](2026-09-08-scanner-daily-net-approval-followup-review.md) 유지; [#67/#69 후속 공통-owner 보완](2026-09-08-pattern-lab-owner-selection-followup-review.md): 실거래 한 축 profile 재선택, train/holdout·partial 순익 여력·AI search SHA→PREOPEN. 20거래일·20건/2일·scoped version 유지, CF2%/close1%/MFE2%/drought 제거 유지 | E2; 운영 lock 우선 유지; 자연 owner `DailyThresholdNaturalAcceptance0908`; 수동 env/봇 변경 없음 |
| 51 | Threshold AI correction | 현재 적용 가능한 비결정적 조정 후보 2차 검토 | 정확히 필요한 family만 parsed review 확보 | 잘못된 자동후보 차단, hold/결정적 handoff의 불필요한 호출·재시도 제거 | ON, OpenAI conditional | [#50 보완 리뷰](2026-09-07-daily-threshold-report-remediation-review.md): eligible `adjust_up/down`만 manifest·누적 context에 싣고 대상 0개는 무호출 parsed-empty receipt. payload char/hash는 실제 ASCII 전송 바이트와 일치한다. PREOPEN gross fallback 제거, 기계 부적격은 차단하되 operator lock 우선권 유지 | 실제 검토 후보가 있을 때만 provider budget lock |
| 52 | Statistical action weight | 행동별 통계 가중치 | report-only 진단 | ADM 해석 개선 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 53 | Holding/Exit ADM | holding/exit matrix | exit owner 분리 | 조기·지연청산 개선 | RETIRED (2026-09-06) | 폐기 계약 구현; 리뷰 보고서 참조 | 없음; 기존 E2 사용 종료 |
| 54 | Threshold cumulative | 2026-06-05 이후 clean-baseline 누적 EV | sample-weighted exact cohort·비용 계약 완결성과 rolling 지속성 검증 | daily 과적합·gross/zero-cost 착시 방지, 적용근거 안정화 | ON, embedded output; bounded projection/cache 구현 | [#50 보완 리뷰](2026-09-07-daily-threshold-report-remediation-review.md): 날짜별 1회 load, consumer projection, bounded diagnostics로 무기한 I/O/파일 팽창 경로 제거. 선택 partition read 실패·대용량 raw skip은 적용 차단 source-quality failure이며, 기존 source와 타 consumer는 보존 | E2 |
| 55 | Entry cancel-wait tuning | BUY 취소시간 CF | entry pattern별 대기시간 조정 | 체결률·기회비용 균형 | ON, 독립 family | 상세검토 대기 | E2 |

### 4.3 Swing·pattern·Entry split·Main AI 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 56 | Swing daily simulation | swing dry-run | 일별 lifecycle 생성 | swing 연구 | OFF | 현재 불필요 지정 유지 | 없음 |
| 57 | Swing strategy discovery | 8-arm 후보 탐색 | safe-pool sim 확장 | 신규 alpha 탐색 | OFF | 현재 불필요 지정 유지 | 없음 |
| 58 | Swing labels | 성숙 outcome 생성 | 후보별 결과 확정 | swing EV 계산 | OFF | 현재 불필요 지정 유지 | 없음 |
| 59 | Swing EV | 후보 경제성 계산 | 우수 arm 선별 | 저EV 후보 제거 | OFF | 현재 불필요 지정 유지 | 없음 |
| 60 | Swing LDM | swing 단계 matrix | 병목 식별 | 정책 정교화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 61 | Swing buckets | swing parent bucket | Tier2 후보 생성 | 표본 안정화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 62 | Swing lifecycle audit | swing 체인 감사 | review/approval 산출물 생성 | 계약 검증 | OFF | 현재 불필요 지정 유지 | 없음 |
| 63 | Swing AI review | swing Tier2 검토 | parsed 후보만 유지 | 오승격 차단 | OFF | 현재 불필요 지정 유지 | 없음 |
| 64 | Swing improvement automation | swing 개선 후보 가공 | runtime-approval 입력 | 연구 자동화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 65 | Swing runtime approval | swing 적용 판정 | full-live 전 fail-closed | 실주문 보호 | OFF | 현재 불필요 지정 유지 | 없음 |
| 66 | DeepSeek swing lab | swing pattern 탐색 | 독립 후보 생성 | 패턴 다양화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 67 | Claude scalp pattern lab | 검증된 순이익·거래빈도 연구 | 일별/rolling10거래일/누적 경제성 및 가설 생성 | 비용 차감 후 작은 수익의 반복 가능성 평가 | ON / source-only | **기존-owner 재선택·AI 숫자 전달·20유효일 유지 검토 보완, 자연 경제성 대기**; [후속 리뷰](2026-09-08-pattern-lab-owner-selection-followup-review.md), `PatternLabSmallNetNaturalEvidence0908` | E2; 독립 실전 승인 lock 없음. score-recovery 운영 override 우선 |
| 68 | Gemini scalp pattern lab | 과거 provider lab | 자동실행 제거 | 중복비용 제거 | RETIRED | 상태 확인만 남음 | 없음 |
| 69 | Scalping pattern automation | 단일 활성 lab을 기존 전략 연구 입력으로 전달 | exact generation → EV/workorder → 기존 owner | 불가능한 합의·폐기 ADM/LDM 대기 제거 | ON / source-only | **native 유지 검토→design workorder와 AI 전수 ID 전달 보완, 자연 전달 대기**; [후속 리뷰](2026-09-08-pattern-lab-owner-selection-followup-review.md). 실전 후보는 기존 Daily/AI/PREOPEN/lock 계약 | E2 |
| 70 | Swing pattern automation | swing pattern handoff | swing 후보 변환 | swing 자동화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 71 | Pattern currentness audit | pattern 원천·소비 세대 검증 | 실제 payload receipt와 날짜/hash 대사 | 낡은 가설·허위 소비 완료 방지 | ON, trigger-gated / source-only | **소비 receipt·trigger 결함 보완, 자연 확인 대기**; [#71/#72 리뷰](2026-09-08-pattern-currentness-ai-review-remediation.md), `PatternLabSmallNetNaturalEvidence0908` | E2; 존재·가용·실제 소비 구분, 독립 실전 승인 없음 |
| 72 | Pattern AI review | pattern 연구·source-only 추천 감사 | 필수 실패 전수 대사·원본 AI 입력 보존 | 유효한 작은 순익·빈도 연구의 기존-owner 전달 | ON / source-only | **material v2·대상일 2회 상한 재검토·복구/verifier 연결·기존 경제성 owner의 순익/자금효율 평가 보완, 자연 확인 대기**; [#71/#72 리뷰](2026-09-08-pattern-currentness-ai-review-remediation.md), `PatternLabSmallNetNaturalEvidence0908` | E2; 소진·중단/거절은 명시적 미검토 source-only terminal, PREOPEN 권한 아님 |
| 73 | Pipeline verbosity | 원본 증거를 보존한 중복·과다 event 진단 | 원본/요약 장애 격리·exact hash 대사·실제 절감 대상 구분 | 경량 요약과 호출 경로의 disk 대기 제거; 실제 봇 지연·순이익 효과는 별도 검증 | ON, exact-date terminal freshness reuse; raw suppression 비활성 | [9/8 보완 리뷰](2026-09-08-pipeline-verbosity-remediation-review.md); 분리 잠금·주기 결속 timeout·hash-bound timing receipt 보완. `PipelineVerbosityNaturalEvidence0908`의 새 PID/자연 소비는 별도 | E2; producer manifest별 기록 mutex 및 분리 publish lock, operator policy lock 아님 |
| 74 | Source-quality final audit | #11과 동일 producer의 최종 원천 재검사 | EV/PREOPEN/최종 verifier 공통 날짜·승인·generation 검증 및 결함 행 격리 | 잘못된 승인과 verifier 불일치 차단, 정상 입력 보존 | ON, trigger-gated; 공통 품질 gate | [9/8 보완 리뷰](2026-09-08-ws-freshness-source-quality-remediation-review.md); 2차 보완, 자연 v2 소비 별도 | E2 |
| 75 | Entry split order plan | 최초진입 분할 정책 | 1·2차 가격·타이밍 후보 생성 | 체결률/slippage 개선 | ON | 상세검토 대기 | E2; operator lock 없음 |
| 76 | AI decision-quality materialization | trace/outcome/replay 입력 준비 | exact cohort 생성 | prompt EV 측정 | ON; 자기해시·부분 성공 학습 계약 | [9/8 Entry 보완](2026-09-08-entry-ai-submit-drought-remediation-review.md): retirement token 오마스킹 수리, 원모델/보정/final response·hash 분리, 비용 결손 pair 격리. 과거 원본 결손은 합성하지 않음 | 새 코드 배포·자연 exact control·provider 평가·경제성은 별도 |
| 77 | Main AI R0–R3 | exact A/B/C prompt·입력 비교 | 연구 후보와 full-gate manifest·동일 prompt/input 소비 연결 | 비용 차감 EV·paired 원화 순이익 개선 검증 | 연구 ON; 현행 Entry adapter 기본 OFF | [연결 구현](2026-09-07-main-ai-r0-r3-remediation-review.md), [새 소스 합성 성능 PASS](2026-09-07-main-ai-current-axis-approval-performance-deployment.md): 승인·배포 지시 접수, prospective baseline 준비 | exact 후보/승인 artifact·active chain 종료·clean 배포·자연/실수익 OPEN; #81 계속 OFF; V2.14/V2.15 alias 아님 |
| 78 | Main AI prompt optimizer | 기존 prompt 후보 평가 개선 | 격리된 누적 EV로 오프라인 평가 후보 유지·전진 | 무의미한 반복 평가 감소 | ON; #82 v5 source-generation 검증 및 offline 선택 소비 | [최종 재보완](2026-09-07-ai-decision-action-outcome-calibration-final-review.md) 유지; [9/8](2026-09-08-entry-ai-submit-drought-remediation-review.md) 작은 target-first 비용 proxy 진단을 기존 개선목표에 연결. 당일 선택 고정/registry 고갈 계약 유지 | runtime 권한 없음; proxy를 수수료·세금/실체결 net으로 해석 금지 |
| 79 | Holding-base replay | holding control manifest | base path hash binding | 비교 기준 안정화 | ON | metadata hash/manifest 연결부 복구·확인; holding provider checkpoint 미충족. 전체 replay 경제성 상세검토는 대기 | E2 |
| 80 | Main AI prompt consumer | entry/holding path 연결 | 모든 request path 분류 | 소비경로 누락 제거 | ON | 9/8 source-date 9/7 consumer terminal 연결 확인; Entry KRX/NXT exact control 각0. 전체 비교표본·live 효과 검토는 별도 | E2 |
| 81 | Main AI runtime family | 기존 exact R3 runtime 설계 | 현재 실적용 권한 없음 | 자동반영 기대효과를 주장하지 않음 | DISABLED; LEGACY_RUNTIME_AUTHORITY_ENABLED=False | postclose/PREOPEN 예약 호출 제거·retired_disabled SKIP. 별도 V2.14/V2.15 entry owner와 혼동 금지 | 9/7 오전 blocked_fail_closed는 과거 receipt; 새 wrapper의 자연 SKIP는 별도 확인 |
| 82 | AI action-outcome calibration | AI action과 사후결과 비교 | 정상 누적 경제성을 기존 오프라인 평가에 환류 | 평가 후보 선택 개선 가능성 | ON; schema v2/policy v5, 자연 근거 대기 | [9/8 보완](2026-09-08-entry-ai-submit-drought-remediation-review.md): 비용 결손 노출의 재검사/행 격리, 작은 기회 진단 전달. 기존 부분 성공·hash·21:05 재결속·review gate 유지 | `AIDecisionActionOutcomeNaturalEvidence0908` OPEN; 실수익/실적용 미검증 |
| 83 | Codebase performance workorder | 코드 runtime 병목 분석 | 자동 성능 workorder 생성 | 장후시간 단축 | OFF | 상세검토 대기 | 없음 |
| 84 | Time-window regime CF | 시간대별 정책 비교 | regime 후보 탐색 | 장중 적응 | OFF | 상세검토 대기 | 없음 |
| 85 | Producer-gap bundle | 누락 producer 근거 수집 | gap 분석 입력 생성 | 원천 결손 해결 | OFF | 상세검토 대기 | 없음 |
| 86 | Producer-gap discovery | AI 기반 gap 탐색 | 구현 workorder 생성 | 영구 gap 해소 | OFF | 상세검토 대기 | 없음 |
| 87 | Stage-hook discovery | lifecycle hook 누락 탐색 | hook workorder 생성 | attribution coverage 확대 | OFF | 상세검토 대기 | 없음 |
| 88 | Stage-hook scaffold | hook 골격 생성 | source-only 관찰점 추가 | 결과 불능 경로 해소 | OFF | 상세검토 대기 | 없음 |
| 89 | WS freshness finalize | WS 정상 안전 차단·원천/전달 결손의 장후 종결 | episode receipt·snapshot as-of 검증→workorder, 소목표 포함 별도 rolling 비교 | 결손 정상화 방지, 무기한 진단 대기 제거, 증분 처리 | 독립 기본 ON; --finalize, 직접 runtime apply 없음 | [9/8 보완 리뷰](2026-09-08-ws-freshness-source-quality-remediation-review.md); 2차 보완, 자연 terminal/경제성 별도 | E2, E3 |

### 4.4 EV·승인·최종검증 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 90 | EV pre-workorder refresh | 최신 EV 통합 | workorder 전 기준 고정 | 잘못된 개선작업 방지 | ON | PnL null/분모·최종 세대 계약 보완 종결; 모든 경제성 계산 전수검토는 별도 | E2 |
| 91 | Code-improvement workorder 1차 | gap을 구현항목으로 변환 | stable ID 작업 생성 | 반복결함 해소 | ON, trigger-gated | frozen native intake 대사 완료; 증거 대기9건은 구현 완료 아님 | E2 |
| 92 | EV post-workorder refresh | workorder linkage 반영 | downstream 최신화 | stale link 방지 | ON | #90과 동일 producer 수리 반영; 전체 경제성 검토와 구분 | E2 |
| 93 | Pattern propagation audit 1차 | pattern→workorder→runtime 추적 | 끊긴 handoff 식별 | 연구 방치 방지 | ON, trigger-gated | 상세검토 대기 | E2 |
| 94 | Pattern AI provenance 1차 | audit 기반 source binding 갱신 | hash/provenance 일치 | 잘못된 참조 방지 | ON | 상세검토 대기 | E2 |
| 95 | EV post-propagation | pattern 연결 반영 | approval 입력 최신화 | stale EV 방지 | ON | #90과 동일 PnL/source 계약 수리 반영; pattern 전체 검토는 별도 | E2 |
| 96 | Runtime approval summary 1차 | family 적용상태 집계 | 적용·차단 사유 명시 | PREOPEN 판단 단순화 | ON | 최종 summary source hash 대사 확인; 각 family의 실적용/EV는 별도 | E2, operator locks |
| 97 | Runtime apply-gap audit | 산출·소비 단절 탐지 | bridge/consumer gap 분류 | 보고서-only 잔류 방지 | ON, trigger-gated | 상세검토 대기 | E2 |
| 98 | Key-lineage ledger | env key 계보 기록 | owner·충돌 확인 | authority leak 방지 | ON | 상세검토 대기 | E2, operator locks |
| 99 | Conversion lane | source→sim→live 단계 분류 | 다음 승격조건 명시 | 성급한 적용 방지 | ON, swing 제외 | 상세검토 대기 | E2 |
| 100 | Rising classifier prior | missed 분류 prior 갱신 | 누적 근거 생성 | 재검토 정확도 향상 | ON | 상세검토 대기 | E2, P15 |
| 101 | Rising workorder refresh | 새 prior 반영 | classifier/workorder 정합 | 오래된 개선안 방지 | ON | 상세검토 대기 | E2, P15 |
| 102 | Scalp-sim control refresh | 누적 prior 반영 재승인 | same-date catalog 최신화 | PREOPEN 일관성 | ON | 상세검토 대기 | E2, P16/P17 |
| 103 | Code workorder 2차 | conversion 결과 반영 | 구현목록 보완 | 누락 축소 | ON | 최종 native intake와 대사; 증거 대기9건의 직접 원인 검토 필요 | E2 |
| 104 | EV post-conversion | 2차 workorder 반영 | 최종 EV 최신화 | 승인 정합 | ON | 최종 workorder·PnL/source 세대 대사 보완; 수익개선 미입증 | E2 |
| 105 | Runtime summary 2차 | workorder 이후 재집계 | 최종 blocker 반영 | stale summary 방지 | ON | 최종 source hash·15개 선택/9개 구현 검토 대사; PID 적용 아님 | E2 |
| 106 | Next checklist 1차 | 다음 거래일 항목 생성 | parser 가능한 owner 목록 | 후속 누락 방지 | ON | source generation marker·수동 영역 보존 계약 수리 종결 | E2 |
| 107 | Pattern propagation final | bootstrap link 재검증 | 임시 pending 제거 | 거짓 경고 감소 | ON | 상세검토 대기 | E2 |
| 108 | Pattern AI provenance final | 최종 source binding | verifier 입력 확정 | hash drift 방지 | ON | 상세검토 대기 | E2 |
| 109 | EV final-consumer | 모든 consumer 반영 | 최종 EV 생성 | PREOPEN stale 방지 | ON | PnL null/세대 수리·재생성 확인; 기존 +453원 귀속 복원과 신규 EV 개선 구분 | E2 |
| 110 | Code workorder final | 최종 source 반영 | 마지막 workorder 확정 | 누락 최소화 | ON | 65행 frozen intake 보존; 별도 승인26행 projection과 중복 집계 금지 | E2 |
| 111 | Runtime summary final | 최종 승인상태 | PREOPEN owner artifact 확정 | 적용 판단 단일화 | ON | 최종 source hash 대사; 현행 PID/EV 검증과 구분 | E2, operator locks |
| 112 | Next checklist final | 최종 상태로 checklist 재생성 | 다음 거래일 owner 확정 | 중간상태 노출 방지 | ON | tower 이후 추가 최종 refresh·POSTCLOSE_SUMMARY_SOURCES 수리 종결; 다음 자연 실행 OPEN | E2 |
| 113 | Verifier pending-DONE | DONE 전 구조검증 | 필수 artifact 확인 | incomplete DONE 방지 | ON | 요약 전 일반 검증과 strict 최종 검증 분리 보완; 전체 전략 검토 아님 | E2 |
| 114 | Docs backlog print-only | checklist parser 확인 | 외부 sync 없이 읽기 검증 | 문서 오류 탐지 | ON | print-only parser 검증 확인; 외부 Project/Calendar sync 미실행 | E2 |
| 115 | Status/DONE marker | terminal 성공 기록 | controller/monitoring 대기 해제 | 후속 체인 진행 | ON | controller 실패·과거 성공 은폐 방지 수리 종결; 00:27:44 source-date 9/7 DONE | E1 |
| 116 | Verifier final | DONE 포함 최종검증 | exact-date terminal 계약 | 성공 오판 방지 | ON | tower→checklist 뒤 strict --require-summary-handoff 수리 종결; 00:27:43 warning/handoff PASS | E2 |
| 117 | Tuning performance control tower | EV/runtime 결과 요약 | 유지·중단·수정 후보 분류 | 불필요 작업 식별 | ON | source_generation_contract·최신 분모·PnL null 수리 종결; 최신 요약이지 수익성 입증 아님 | E2 |
| 118 | Bot restart | 완료 후 runtime 재개 | 명시 승인 시에만 재시작 | 무인 운영 | OFF, stop-only | 상세검토 대기 | 없음 |

### 4.5 Main wrapper 외 핵심 선행 입력

실행 시각은 번호 순서와 다르다. 아래 번호는 기존 review index를 보존하면서 누락 단위를 독립 추적하기 위해 끝에 추가했다.

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 119 | BUY Funnel Sentinel → submit drought handoff | BUY 후보가 submit에 이르지 못한 원인을 단계별로 분리 | 다섯 core axis의 exact attempt·terminal을 분리해 실제 causal owner에 전달 | 무차별 threshold 완화 없이 submit 병목 수리와 후속 비용 차감 EV 표본 회복 | 5분 producer/장후 handoff ON; 직접 runtime 권한 없음, 간접 recheck PREOPEN 경로 있음 | [9/8 추가 수리·재리뷰](2026-09-08-buy-funnel-entry-recheck-remediation-review.md): schema6/exact3의 실제 가격/micro/tick terminal, 공통 refresh ledger, call-local ID/종료 관측. 탐지/활성 floor와 safety 유지. [9/7 R1~R5](2026-09-07-buy-funnel-submit-drought-handoff-review.md#11-r1r5-보완-구현과-최종-재리뷰)는 이전 완료 기록 | E3; 9/8 자연/이력 복원·controller·PREOPEN/PID·효과 후속 OPEN=`EntryRecheckNaturalAttribution0907` |

## 5. 다음 자연 실행에서 분리해 확인할 것

### 5.1 현행 자연 acceptance와 재검토 경계

| 영역 | 코드·계약 검토 | 다음 자연 확인과 OPEN owner |
| --- | --- | --- |
| #8/#9 Rising-missed | 9/5 종결 유지 | 당일 원천·handoff를 통상 소비한다. 새 결함/계약 변경/필수 소비자 실패가 없으면 상세검토를 다시 열지 않는다. |
| #11 Source-quality preflight | 9/5 종결 및 #74 공통 품질 gate 후속 보완 | 20:10 main의 해당 stage 실행 전 당일 자연 artifact 부재는 `not_yet_due`. 장중 수동 감사의 완료 범위와 자연 postclose를 구분한다. 현재 `PostcloseSourceQualityGateReview0908`에서 v2 source date/generation·row/window exclusion·EV/PREOPEN/최종 verifier 소비를 대사한다. |
| #74/#89 최종 품질·WS | [9/8 2차 리뷰](2026-09-08-ws-freshness-source-quality-remediation-review.md) 1,093 PASS 기록; 전체 배포/경제성 미검증 | `PostcloseSourceQualityGateReview0908`: audit v2→공통 consumer, 독립 `--finalize`→native workorder·episode 전수 receipt, 과거 snapshot과 current freshness 분리, 그룹별 rolling 원천 hash. 진단 완료에 경제성 20개 outcome을 추가 gate로 요구하지 않음 |
| #119/#23 submit drought | [9/8 schema6/exact3 추가 수리](2026-09-08-buy-funnel-entry-recheck-remediation-review.md); controller v4의 ON 조건 유지 | 10:25 raw 재구성107=terminal107+pending0+submit0, refresh7pass/5records=AI6+가격1. 이는 누락/재시도 귀속 수리이지 자연 발행·제출 해소가 아니다. `EntryRecheckNaturalAttribution0907`: 자연 cache12/report6→구 history의 원본 복원 가능성/유효 최근3거래일→controller→PREOPEN/PID→submit/fill/terminal/비용 EV. paired10은 초기 ON 허들이 아니다. 이전 schema5/exact2 완료 기록은 역사이며 현재 계약의 소비 증거로 재사용하지 않는다. |
| #49 lookup-attention | v4/resource v2·PREOPEN receipt + small_net_v1 승인 보완; [9/8 census·유지 판단 보완](2026-09-08-market-census-scanner-submit-drought-remediation-review.md) | `ScannerLookupAttentionNaturalEvidence0908`: 새 generation 경쟁군/교체 pair→정책→다음 PREOPEN immutable receipt→PID/R6. census v4 구간 진단과 native workorder handoff, 0완료일·조건부 표본 민감도도 확인한다. 20유효일/10월2일 유지 재검토이며 자동 OFF나 실제 full-fill 승인 완화가 아니다. |
| #76/#78/#82 AI calibration | self-hash·부분 정상행 학습·offline 선택·late refresh 종결 | `AIDecisionActionOutcomeNaturalEvidence0908`: terminal detailed→#82 v5→당일 선택 고정 optimizer→provider0 재결속→consumer 동일 hash. 실수익·별도 live owner receipt는 미확인이다. |
| #81 Main AI legacy runtime | DISABLED 유지 | 표본 누적으로 켜지는 경로가 아니다. #77 현행 Entry adapter는 별도 구현·기본 OFF이며 승인 접수와 실제 배포/소비는 각각 해당 receipt로 확인한다.  KRX V2.14/V2.15의 `entry_setup_live_policy`도 독립 owner다. |
| #73 Pipeline verbosity | 원본 보존·잠금 분리·bounded summary/timing receipt 보완 기록 | `PipelineVerbosityNaturalEvidence0908`: 새 PID의 manifest/hash-bound receipt와 장후 v2 소비. raw suppression OFF와 기존 원천 보존을 유지하며 디스크 정리를 원천 생략 승인으로 바꾸지 않음 |
| #67/#69·#50 Pattern/Daily | 기존 owner의 소액 net·source/currentness/AI 전달 후속 리뷰 기록 | `PatternLabSmallNetNaturalEvidence0908`, `DailyThresholdNaturalAcceptance0908`: 자연 paired/비용 source→manifest/currentness/AI→EV/workorder→정식 PREOPEN. 동시 수정 중인 코드·임시 fixture를 생산 generation/전체 review0으로 간주하지 않음 |

recheck·lookup-attention·AI 자연 acceptance 3개는 [9/8 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)로 같은 ID를 이관했고 [9/7 checklist](../checklists/2026-09-07-stage2-todo-checklist.md)는 이관/과거 근거를 보존한다. 나머지 과거 링크의 OPEN/완료 여부는 개별 원 항목을 확인한다. 다음 행은 9/8 신규 완료 선언이 아니라 코드와 남은 acceptance의 연결이다.

| 추가 영역 | 확인된 범위 | 남은 OPEN acceptance |
| --- | --- | --- |
| #90~#117 요약/EV/검증 연결 | 955 targeted PASS 범위의 PnL/source hash·strict verifier/controller 보완; 9/7 원천 복구 terminal | `PostcloseRecoverySourceAcceptance0908`: 다음 자연 tower→checklist→strict verifier; workorder9개 exact evidence |
| #76~#82 lifecycle/AI | CF 관찰 분리, 실제 NXT lifecycle2와 metadata consumer 연결 | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`, 기존 `AIDecisionActionOutcomeNaturalEvidence0908`: 새 exact 원천/비용/후보 비교. provider0·control0을 AI 성능 PASS로 바꾸지 않음 |
| 21:15 machine timing | 9/7 ingress loss 격리와 baseline carry; 같은 날짜 재실행 미실시 | `MachineLifecycleTurnoverObjectiveFollowup0908` 및 `PostcloseRecoverySourceAcceptance0908`: 새 exact ordered/route/epoch source와 경제성 준비 |
| #15/#16·widget 별도 승인 | 9/8 policy/설치 및 native projection 26행 대사: 구현11/이미 검증2/관찰8/보류5 | `WidgetEpisodeRecommendationApplyAcceptance0908`: 예정 window의 preflight/PID/신호·독립 custody/terminal/비용. 원본 canonical ID 결손26행과 합산하지 않음 |

### 5.2 오전 자연 관측 기록 — 현재 PID/일중 최종 판정 아님

판정 시점은 [2026-09-07 10:20 KST 정규 모니터링](2026-09-07-intraday-1020-monitoring.md)과 `10:30 KST` PYRAMID feedback이다. 장중 snapshot을 일중 전체 성과로 외삽하지 않으며, 아래 `부분 확인`은 runtime/원천 소비가 관측됐다는 뜻일 뿐 비용 차감 EV acceptance 완료가 아니다. 최종 owner는 당일 checklist의 같은 이름 OPEN 항목이다.

| 영역 | 당시 판정 | 해당 시각의 자연 실행 근거 | 별도 acceptance |
| --- | --- | --- | --- |
| ADM/LDM retirement | 부분 확인 | PREOPEN verify `pass`, PID `46656`, mismatch/missing `0/0`, canonical retirement env 15개 OFF. 현재 선택·실주문 권한 누출은 관측되지 않았다. | 장후 폐기 artifact 누락이 FAIL/workorder를 만들지 않고 Entry AI gate·Samsung·AVG_DOWN/PYRAMID handoff가 유지되는지 `AdmLdmRetirementNaturalEvidence0907`에서 종결한다. 과거 report/lock은 감사자료로 보존하며 operator lock을 일괄해제하지 않는다. |
| PYRAMID | `not_observed` | 10:30 feedback의 pyramid/real scale-in/closed outcome이 모두 0이고 비용 차감 EV는 산출 불가다. report 생성 성공은 runtime 효과가 아니다. | exact-ready parent episode, KRX 근거, 비용 차감 next-step EV, same-ID AI 검토와 단일 scale-in owner 소비를 자연 표본에서 확인한다. |
| AVG_DOWN | `not_observed` | 메인 신규 fill/terminal이 없어 route arbitration·exit replay·real scale-in 경제성 표본이 형성되지 않았다. | `avg_down_route_arbitration_observed`와 연속 `avg_down_exit_replay_frame_observed`, A/B/C 독립 terminal, source audit와 same-ID AI/PREOPEN/PID 소비를 확인한다. 허들을 낮춰 표본을 만들지 않는다. |
| Low-price 독립 머신 | 부분 확인 | target-date applied policy는 53개 profile을 싣고 비용 재검증 비양수 3개 profile을 제외했다. 한화오션 late-morning은 10주 두 leg가 체결돼 `TARGET_OPEN`으로 자연 runtime 소비가 확인됐다. | HELD·partial/full fill·terminal·broker 비용 차감 paired EV를 `LowPriceEconomicReplayNaturalEvidence0907`에서 분리한다. open position은 realized EV에 넣지 않는다. |
| One-share 관측 | source 관측, 실주문 미확인 | rising-missed/one-share source 관측과 Entry recheck runtime 적용은 별도 계약이다. 10:30 PYRAMID feedback의 `one_share_event_count/closed_count`는 0이다. | 고정 KRX/NXT profile의 exact submit/fill/terminal과 비용 차감 EV가 생길 때만 성과를 판정한다. 누적 backtest는 정기 실행하지 않는다. |
| Entry recheck | 당일 PID 미적용 | 실제 9/7 PREOPEN verify는 구 controller v3를 현행 v4로 인정하지 않아 `entry_opportunity_recheck_runtime`과 `entry_split_order_plan`을 `disabled_or_removed` 처리했고 selected family는 22개다. 따라서 이전 격리 검증의 ON/23개를 현재 PID 적용 증거로 사용할 수 없다. | 다음 정상 장후 controller v4 생성→다음 거래일 PREOPEN 선택→PID 소비→exact attempt/submit/fill/terminal을 `EntryRecheckNaturalAttribution0907`에서 확인한다. 현재 PID에 수동 주입하지 않는다. |
| Microstructure | 부분 확인 | context schema v2와 delivery telemetry v3의 computed 및 holding 내부 소비가 관측됐다. entry derived reaction의 payload 미포함은 현 계약상 정상이며 provider sent와 동일 의미가 아니다. | payload included/confirmed sent/internal consumed/cache identity를 같은 evaluation/attempt outcome과 결합하고 source coverage·timeout을 `ContextDeliveryNaturalEvidence0907`에서 판정한다. 20건은 진단 해석 기준이며 PREOPEN 승격 조건이 아니다. |
| Samsung 독립 머신 | 부분 확인 | morning은 exact-date policy와 target-ticks override를 소비해 10주 두 주문을 냈으나 validity 종료까지 미체결되어 정상 `NO_FILL`로 끝났다. midday/afternoon은 snapshot 시점에 아직 예정 전이었다. | 상승·반등 recipe 자연 원천, 각 시간대 PREOPEN/PID 소비와 broker 체결금액 EV를 `SamsungEntryRiseReboundNaturalEvidence0907`에서 확인한다. NO_FILL을 손익 0으로 보간하지 않는다. |
| Market weakness/rebound | 부분 확인 | 최신 source-quality는 허용 상태이고 latch는 회복/released 상태로 소비됐다. weak-context 차단의 비용 차감 paired EV는 아직 없다. | immutable hysteresis·observer health·0B/0D source yield는 `MarketWeaknessNaturalEvidence0907`, 재진입 보존성과 paired EV는 `MarketWeaknessReboundReentryRetention0911`에서 분리한다. |
| Scale-in split | `not_observed` | 자연 AVG_DOWN/qty>=2 split apply와 R6 경제성 귀속이 없고 당일 selected runtime family도 아니다. | qty>=2 자연 AVG_DOWN의 v3 policy/PREOPEN/R6 귀속을 `ScaleInSplitNaturalEvidence0907`에서 확인한다. 무표본을 음의 EV로 보거나 수량·허들을 완화하지 않는다. |

구현 완료를 실현 수익 개선으로 표시하지 않는다. 자연 match 0은 경제성 실패가 아니며 source/adapter gap과 자연 희소성을 구분한다. bot 재기동, 수동 env 적용, operator lock 변경, 주문·수량·provider·hard-safety 변경은 이 현행화 범위에 포함하지 않는다.

## 6. 다음 상세검토 우선순위

**메인 submit drought 해소를 최우선으로 하는 점검·개선 대기열**이다. 필수 owner의 실패 복구·source-quality 확보가 먼저이며 cron/immutable wrapper의 실행 순서는 바꾸지 않는다. 완료 항목의 자연 확인과 미검토 항목의 코드 상세검토를 분리한다. source-only 보고서와 실전 효과의 완료 기준은 [장후 지시문 §1.1](../postclose-tuning-result-review-task-instructions.md#11-submit-drought-최우선-점검개선-계약)을 따른다.

| 순위 | 점검·개선 대상 / 기존 review ID | 반드시 확인할 근거와 consumer | 실행·자연 acceptance owner (9/8 checklist) |
| --- | --- | --- | --- |
| 1 | **최초 병목 확정**: #119 BUY Funnel, #11 preflight·#74 final audit | 대상일 마지막 정상 generation의 exact attempt/cycle·terminal 보존식과 5개 core axis를 대사한다. upstream/latency/AI 재검증을 우선 분해하고 `PRICE_REVALIDATION`·`BROKER_RECEIPT`의 0을 결손과 정상 미도달로 구분한다. raw census 비율과 exact 인과 분모를 혼합하지 않는다. Sentinel·당일 pipeline snapshot과 이를 소비하는 #23 controller/workorder의 날짜/hash 연결을 확인한다. | `EntryRecheckNaturalAttribution0907`, `PostcloseRecoverySourceAcceptance0908` |
| 2 | **scanner 상위 탐색·관측 지연**: 외부 market census, #8/#9 rising-missed, #49 lookup-attention, #27 micro·#89 WS freshness | 독립 보통주 시장 모집단→fetch/pool/watch/promotion→attach/fast/heavy eval의 최초 결손·지연을 확인한다. benchmark·BBO/SLA가 없으면 recall 정상이나 유효 기회 없음으로 닫지 않는다. lookup-attention의 동일-tier 자원배분은 전체 시장 포착률의 대체 검증이 아니다. timestamp loss·source/queue·callback 지연을 분리하고 유효 row/window만 소비한다. | `RuntimeEnvIntradayObserve0908`, `ScannerLookupAttentionNaturalEvidence0908`, `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908` |
| 3 | **Entry AI 입력·판단·submit 직전 재검증**: #76/#77/#78/#80/#82, #27/#89 | 최신 AI trace/payload/response·완성봉·BBO·세션과 final authority를 exact attempt에 연결한다. 10:10 quote refresh의 latency 회복5 중 AI 재검증 차단4, budget 단계 잔류1이며 제출0이다. stale/untrusted/schema/transport 결손과 정상 WAIT/DROP의 경제적 오판 가능성을 분리한다. action-neutral outcome·같은 payload replay로 확인하고 미래 label을 입력에 역류시키지 않는다. #79 holding은 별도 cohort이며 #81은 계속 OFF다. | `AIDecisionActionOutcomeNaturalEvidence0908`, `EntryRecheckNaturalAttribution0907` |
| 4 | **기존 대응 후보의 실효 경로**: #21 one-share 진단·#23 daily recheck, #48 fact sync·#75/#76/#77 원천→#50/#51/#54 Daily/cumulative/AI correction | #23의 정확한 최근3거래일 source·scope·controller v4→기존 PREOPEN 후보를 확인한다. on-demand 누적 backtest를 정기 복구 대상으로 삼지 않는다. #50은 같은 장후 paired/실제 비용을 소비하고 정상 hold·missing/source failure를 분리한다. submit0을 이유로 모든 family의 양수 순EV 후보를 일괄 거부하거나, 반대로 drought 경보를 자동 승인으로 사용하지 않는다. 새 수량·threshold·cap 변경은 이 목록의 권한이 아니다. | `EntryRecheckNaturalAttribution0907`, `DailyThresholdNaturalAcceptance0908` |
| 5 | **개선 지시의 누락·stale handoff 차단**: #91/#103/#110 workorder→#90/#92/#104/#109 EV→#96/#97/#98/#105/#111 summary/gap/lineage→#117/#112/#116 | `order_entry_submit_drought_auto_resolution`과 원본이 발급한 weak-contract native ID 전수를 현재 disposition으로 대사한다. 10:03 메모리상 6개 검증은 장후 canonical 발행이 아니다. `buy_funnel_sentinel_primary`, `entry_submit_drought_handoff_selected`, 마지막 strict `--require-summary-handoff`와 다음 PREOPEN 소비를 확인한다. 코드 완료·후속 전달·실제 drought 해소는 별도다. | `PostcloseRecoverySourceAcceptance0908`, `EntryRecheckNaturalAttribution0907` |
| 조건부 | **제출 이후 품질**: #48 receipt/fact, #55 cancel-wait·#75 Entry split, #46 holding/exit·#12/#13/#47 scale-in | exact accepted submit 뒤 미체결·부분체결·잘못된 가격/취소/귀속이 최초 병목일 때 상세검토를 앞당긴다. pre-submit0만으로 cancel timeout·split·scale-in을 첫 해법으로 삼지 않는다. 기존 NXT identity/receipt workorder는 지우지 않고 별도 scope로 계속 대사한다. #75는 Daily 선행 원천으로서 정상 실행을 유지한다. | 기존 해당 family owner 및 `PostcloseRecoverySourceAcceptance0908` |

#67/#69 pattern lab의 새 source-only 연구는 기존 owner의 순EV/빈도 개선 근거를 보강하지만, 위 drought 원인 점검을 지연시키는 추가 합의·승인 gate가 아니다. 다른 세션의 관련 수정·리뷰 기록은 보존하며 이번 문서 검토의 코드 완료 범위에 포함하지 않는다. 위젯·Samsung/저가주 거래와 machine timing은 독립 owner로 필수 운영·추천 intake를 유지하되 메인 submit0의 분모나 대체 성공 근거로 합산하지 않는다.

§5.1의 #11/#74/#89/#119/#23/#49/#76/#78/#82는 **각 최신 리뷰에서 닫힌 범위의 자연 acceptance 확인**이지 다시 처음부터 상세검토할 목록이 아니다. 후속 코드가 계속 변경되면 해당 diff의 검토·배포 여부를 따로 확인한다. #8/#9는 신규 결함이 없으면 재개하지 않는다. OFF/RETIRED와 비우선 sim/bucket/Swing은 단순 무표본 때문에 우선순위에 넣지 않는다. 실행·재확인 시점은 현재 체크리스트의 기존 owner를 따르며 이 표는 새 자동실행 권한이나 일정이 아니다.
