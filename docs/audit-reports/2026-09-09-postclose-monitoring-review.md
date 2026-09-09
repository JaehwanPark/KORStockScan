# 2026-09-09 장후 모니터링 실행 기록

## 1. 범위와 시작 판정

- 사용자 명시적 장후 모니터링 요청. `TARGET_DATE=2026-09-09`, 시작 `2026-09-09T19:56:23+09:00`; 자정 뒤에도 source date 유지.
- 상태: **진행 중**. 운영 terminal·허용 추천 fixed-point·자연 정책/PID·비용 후 경제성은 별도 판정한다.
- [지시문](../postclose-tuning-result-review-task-instructions.md), Plan Rebase §1–§8, 당일 checklist 전체 OPEN, runbook/traceability와 설치 cron/systemd를 대사한다. `korstockscan-review-gate` 사용. 기존 dirty/병행 구현은 보존한다.
- 매매 process·env/lock·provider/threshold·주문·custody는 변경하지 않는다. 과거 배포/재기동/수동 청산 승인은 이번 실행으로 승계하지 않는다.

## 2. 설치 owner와 시작 receipt

19:59~20:01 읽기 전용 `crontab -l`, systemd timers/services/ExecStart, process tree/lock 확인:

| KST | owner | 시작 시 판정/다음 확인 |
| --- | --- | --- |
| 20:05 | EOD cron / update_kospi.py | not_yet_due; 당일 status/최신 DONE |
| 20:10 | main threshold-cycle / controller / tuning monitoring | not_yet_due; 설치된 날짜 고정 wrapper. main의 기존 scheduled bot-action=stop은 수동 정지 권한과 분리 |
| 20:10 | widget evaluation systemd | not_yet_due; unit inactive, 당일 시작 receipt 없음. 과거 Result=success만으로 오늘 성공 처리하지 않음 |
| 20:50 | dashboard archive | not_yet_due |
| 21:05 | AI replay/follower | not_yet_due; 동일 날짜 lock/terminal 확인 |
| 21:15 | machine final-refresh systemd | not_yet_due; expansion→attribution→weakness→timing→approval→checklist 단일 owner |
| 21:55 | finalization | not_yet_due; widget/machine 당일 terminal→summary-only strict→cleanup→detector |

finalization의 5100초/23:20 predecessor deadline, summary 600초/kill-grace10초/최대2회와 cleanup·detector 각600초를 현행 shell/traceability에 대사했다. 새로운 전체 producer나 trading 재기동은 만들지 않는다.

20:00:00 main PID412924의 sniper 자연 종료: `terminal_reason=market_close`, `alive=false`, `unresolved_scalping_count=0`, codes 빈 값. 20:00:09 및20:02:11 detector `process_health=pass`, `expected_stopped_threads=[sniper_engine]`, `thread_status=expected_terminal`. bot main-loop는 별도 생존한다. 과거 keyword TypeError를 새 종료에서 관측하지 않았다. 이는 종료 계약의 자연 수용이지 수익성 완료가 아니다.

위젯 trader는 사용자 수동 중지/삼성 수동 매도 복구 기록에 따라 inactive다. [별도 복구 기록](2026-09-09-samsung-widget-ten-share-manual-exit-reconciliation.md)의 사용자 기동 후 확인을 유지하며 이번 모니터링에서 재기동하지 않는다. 삼성 collector PID727306과 독립 collector661/662는 생존한다.

## 3. 시작 시 OPEN 전수 분류

당일 checklist의 기존 ID20개를 대사했다. 아래는 시작/첫 확인 상태이며 후속 실행으로 갱신한다. 과거 window의 부분 수용과 남은 acceptance를 분리하고, 미래 항목을 overdue로 분류하지 않는다. 각 source 경로/원래 Acceptance는 [당일 원문](../checklists/2026-09-09-stage2-todo-checklist.md)에 유지한다.

| 기존 ID | Due / window KST | 이번 점검·판정 | 다음 확인/남은 acceptance |
| --- | --- | --- | --- |
| IntradaySourceQualityGateCheck0909 | 9/9 14:20–14:35 | overdue_unresolved; 최신 audit 없음. 기존 감사 명령 실행은 exit75/heavy-analysis busy로 정상 중복 차단 | 19:55 rising-missed 종료 및20:10 정규 audit; 결손/unknown/exclusion→후행 quality/workorder |
| ThresholdDailyEVReport0909 | 9/9 16:30–16:45 | source9/8 tower/EV 읽기 대사 완료 | 새 경제성/정책 수용은 별도 Daily owner |
| HumanInterventionSummary0909 | 9/9 17:00–17:15 | source9/8 approval_requests=[]; 기존 구현/권한/관찰 owner 분리 완료 | source9/9 전수 추천은 아래 Code/Recovery owner |
| SniperMarketCloseHeartbeatNaturalAcceptance0909 | 9/9 20:00–20:10 | 자연 market_close/미종결0/finally metadata/detector PASS | 이 종료 acceptance 완료; 수동 heartbeat 작성 없음 |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908 | 9/9 08:40–08:45 + through-close | overdue_unresolved; 오전 완료와 과거 loss 이력 보존 | 당일 terminal collector·exclusion·Provider hold 검증 |
| WidgetEpisodeRecommendationApplyAcceptance0908 | 9/9 08:57–14:45 + 후속 | overdue_unresolved; 승인 기동/수동 복구와 자연·경제성 구분 | 사용자 재기동 receipt는 user_authority 대기;20:10 평가/21:15 독립 source |
| MarketWeaknessNaturalEvidence0907 | 9/9 09:05–15:30 | 15:26:01 source-quality ok/errors0/sample65; 전체 paired 경제성 미확인 | 장후 attribution/weakness/timing의 exact source/terminal/EV |
| OperatorPolicySuccessionAcceptance0908 | 9/9 07:35–08:45 | 기존 PREOPEN 부분 수용 유지; first-use/경제성 OPEN | 기존 source/후행 PREOPEN. 후보 강제·lock 해제 없음 |
| EntryRecheckNaturalAttribution0907 | 9/9 20:10–21:50 | not_yet_due | 새 exact funnel/controller/최근3거래일·다음 PREOPEN/실효성 |
| ScannerLookupAttentionNaturalEvidence0908 | 9/9 20:10–20:40 | not_yet_due | census/#8/#9/#49 source generation/첫 depletion/consumer |
| PatternLabSmallNetNaturalEvidence0908 | 9/9 20:10–21:55 | not_yet_due | existing paired/lab/currentness/AI/EV; Provider cap 유지 |
| DailyThresholdNaturalAcceptance0908 | 9/9 20:10–21:55 | not_yet_due | 같은 장후 paired→Daily/AI/후행, 비용null/hold_sample 분리 |
| AIDecisionActionOutcomeNaturalEvidence0908 | 9/9 20:10–21:55 | not_yet_due | #76/#77/#82/#78/#80 generation·Control·비용·자연 입력 |
| PostcloseRecoverySourceAcceptance0908 | 9/9 20:10–21:55 | not_yet_due | native intake/companion/요약/strict와21:55 늦은 source closure |
| CodeImprovementWorkorderReview0909 | 9/9 21:15–21:25 | not_yet_due | authoritative generation 전수 native ID/권한/Pass1/2 |
| MachineLifecycleTurnoverObjectiveFollowup0909 | 9/9 21:30–21:40 | not_yet_due |21:15 timing 공통 kernel/4군 연구·frozen policy 및 별도 exit child |
| MainAIQualitySourceGapArtifactContract0909 | 9/9 21:40–21:50 | not_yet_due | cycle/nested diagnostics/workorder self-hash/consumer |
| AutomationTriggerDecisionSummary0909 | 9/9 21:40–21:55 | not_yet_due | actual snapshot run/skip marker·직접 사유 |
| PostcloseSourceQualityGateReview0909 | 9/9 21:40–21:55 | not_yet_due | final audit→EV/workorder/strict, 식별된 row/window만 격리 |
| ScannerLookupAttentionCalendarMaintenance1002 | 10/2 20:10–21:55 | not_yet_due | 20유효 source일 선도래 여부는 기존9/9 scanner owner에서 확인 |

시작 미분류0. 표의 상태는 process 종료/경제성 완료를 대신하지 않는다.

## 4. 지난 window 점검과 원천 hash

20:01 대사:

- source9/8 tower 생성 `2026-09-09T00:25:39+09:00`, SHA256 `ca36263f4f8a9c3d6e96e4c1748ec643bf3c15c383e88da2c049f7e893523ee2`.
- source9/8 EV 생성 `2026-09-08T22:30:08+09:00`, SHA256 `951c62fcaf837a741f4669e6e1ec8bf18d7e7bb36b921d60dc52355250b88a33`.
- real sample0/평균null, sim sample4/평균−1.7125%, combined는 diagnostic only. live-auto-ready0, sim approved0, post-apply=`pending_applied_cohort`. 표시된 selected20은 source9/7→target9/8 이력이지 target9/9 적용 기대값이 아니다.
- headline0의 원 status는 `count_reconciled_snapshot_diagnostic_not_cost_verified`; 실제 비용 대사 완료/확정 순손익0원으로 승인하지 않는다. 이번 보고의 미검증 실현손익은 null이다. 오늘 새 generation에서도 동일 혼동이 남는지는 기존 EV/tower owner로 확인한다. 과거 정상 source를 이 사유만으로 반복 재생성하지 않는다.
- `approval_requests=[]`: 추가 approval ID를 발명하지 않는다. source9/8 frozen61행·별도 승인17행은 successor/subset 관계다. 현재 source9/9 추천 구현은 기존 Code/Recovery owner에서 전수 intake하며 새 실전 조건·종목/프로필/exit 활성화는 권한 밖이다. Codex 자동 runner OFF는 실패가 아니고 외부 Project/Calendar sync는 사용자 소유다.

20:01대 실행 명령: `PYTHONPATH=. timeout --kill-after=10s 360s .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-09 --write --print-summary`. 결과 `skipped_heavy_analysis_busy`, exit75; audit 생성/원본 격리는 실행되지 않았다. 처음 path-filtered lslocks에 보이지 않은 점유를 fuser/process tree로 재확인했다. 19:55 정기 rising-missed wrapper836986/worker837120가 공통 lock을 보유하며20:02 CPU78%로 전진 중이다. 정상 점유를 stale로 처리하거나 lock을 삭제하지 않는다. 이후 정규 audit receipt까지 이 항목은 OPEN이다.

## 5. 후속 실행 기록

### 5.1 20:05–20:08 원천과 공동 우선 경로

- rising-missed19:55 run은20:04:50 DONE. 공통 lock 해제 후20:05:27 기존 audit --write/--print-summary를 재개했다(PID843555).20:07 CPU 누적74초/메모리36MB로 streaming 진행 중이며 audit terminal 전 성공으로 세지 않는다.
- EOD20:05:04 START, PID843075.20:07 현재 CPU 작업 중이며 status 파일은 아직 미발행이다. 지난9/8 DONE을 오늘 성공으로 사용하지 않는다.
- micro 마지막 snapshot20:00:32.912 SHA256 `5bd943549e6593977c75e6b865687731d66fa71406585a6819a91f96a60afef3`: epoch1788932497558153946/closed/stopped_clean, trade561171/depth884617, drop·worker/writer error0·close failure0·잔존 worker/writer0. current-process rejected-depth20=receipt20, exact exclusion proven=true, 최소 free31,022,997,504B. 이 마지막 epoch의 종료·제외 증거를 오전 과거 유실 복원이나 당일 전체 Provider hold 해제로 확대하지 않는다.
- market weakness15:26:01 source-quality ok/sample65, observer health ready/연속실패0/last-healthy15:26:01. 장 종료 후 이를 계속 fresh live 입력으로 사용하라는 뜻은 아니다.21:15 paired/경제성은 별도다.
- systemd 실패 표시 두 midday preflight는 당일13:14 exit4의 기존 terminal quarantine다. 영원무역은 `research_half_robustness_review_requires_new_profile_revision`; 신호 window 뒤 강제 기동/재시도나 기존 quarantine 해제는 하지 않는다.

Main Sentinel source9/9 as-of19:20:05, SHA256 `1a610a969f428386b4fcc388818afc039d773fc1fd4b4345925a82e6e795958f`:

| scope | raw AI/budget/latency/submit unique | exact attempt = classified terminal + unclassified + pending + submitted | 최초 terminal upstream/latency/AI/price/broker |
| --- | --- | --- | --- |
| KRX regular | 361/549/105/0 |1111=1104+7+0+0 |647/320/101/36/0 |
| NXT aftermarket |60/75/12/0 |225=225+0+0+0 |175/26/12/12/0 |
| CONFLICT |0/10/0/0 |10=10+0+0+0; 별도 제외 |2/8/0/0/0 |
| PREMARKET_KRX_LIKE |0/0/0/0 |0 |0/0/0/0/0 |

각 scope의 missing exact-key 진단1은 원본 결손으로 유지하며 raw unique를 인과 funnel로 이어 합산하지 않는다. KRX/NXT는 `SUBMIT_DROUGHT_CRITICAL`; 실제 제출 회복·순이익 개선은 미관측이다.

확인된 source-only 분류 결함: KRX 미분류7건의 마지막 stage는 `blocked_gap_from_scan`. raw cache의 `metric_role=baseline_prior_feature`, `decision_authority=source_quality_only`, `runtime_effect=False`, `gate_action=risk_context_only`와 producer registry/코드(실제 return 차단 없음)가 일치하지만 `_exact_submit_drought_axis_summary`의 포괄 `blocked_` 처리가 prior terminal을 unclassified로 바꾼다. 기존 `EntryRecheckNaturalAttribution0907`/workorder owner에서 비차단 관찰·실제 terminal/결손 보존 회귀를 준비한다. 단순 stage 이름 삭제로 실제 unknown 차단까지 숨기거나 실매매 gap guard를 수정하지 않는다. 운영 중 wrapper에 코드/원천 세대를 교체하지 않으며 최종 repair/validation/consumer 확인 전 해결로 표시하지 않는다.

외부 census19:46:18 SHA256 `b9741f12abc1d9cf850dbe6609c26a564e3b06f6407f722872dfa4707e4b5c14`: partial_diagnostics_ready/scoped_diagnostics_available, primary `entry_ai_provider_reach_rate_pct`. master lookup gap/cadence/BBO join/일부 resolved floor/right-censored ceiling이 남아 전체 scanner recall 정상·실제 놓친 수익 확정으로 쓰지 않는다. bounded cohort와 외부 전수 분모를 보존한다.
