# 2026-09-08 15:00 장중 모니터링

관찰 시작 14:04:27 KST, 요청 종료 15:00 KST. 대상일 9/8과 장후 source-date 9/7을 분리한다. **15:00:01 KST 마지막 snapshot까지66회 관찰 후 종료했다. 운영 관찰 종료와 미해결 결함의 종결은 별개다.**

## 관찰 중 확인한 계측 결함과 보완

13:44:50~55 덕산테코피아 **record41075 / 317330**, submit ID `0de1b5a182284ccfaea95287cee79081`의 원본 7행을 보존했다. `budget_pass`의 scanner parent는 `SCANPROM-317330-1788842312240`이고, 호출이 끝나기 전 scanner가 `SCANPROM-317330-1788842693395`로 갱신했다. 후행 `rising_missed_tick_speed_entry_block`과 completion은 같은 call ID이지만 새 parent라서 Sentinel이 `submit_call_identity_contract_invalid`로 해당 attempt를 제외했다. 실주문은 없고 실제 차단 이유는 `tick_acceleration_ratio_lt_1`이다.

- [call-local observer](../../src/engine/monitoring/entry_attempt_identity.py)는 최초 parent를 `entry_submit_attempt_parent_promotion_id`로 고정한다. 처음 parent가 없으면 첫 유효 hydration에서만 결속한다. 현재 scanner metadata와 stock/order 상태는 그대로 유지한다.
- [Sentinel](../../src/engine/buy_funnel_sentinel.py)은 call ID가 있고 producer frozen parent가 발급된 행에서만 이를 attempt parent로 사용한다. frozen parent 충돌, schema/authority 위반과 legacy parent 불일치는 계속 제외한다. 원본 ID 없는 과거 행을 새 필드로 보간하지 않는다.
- [회귀 테스트](../../src/tests/test_submit_drought_contract.py)는 호출 중 parent 갱신, 지연 hydration, malformed authority/schema, frozen-parent 충돌, 중첩/thread 격리, 실제 logger의 caller spoof 제거와 원래 함수 반환/guard 보존을 확인했다. cache는 모든 source field를 보존하므로 새 cache schema나 과거일 재생성이 필요하지 않다.

`korstockscan-review-gate`로 직접 producer→logger→lossless cache→exact ledger→controller/handoff를 재리뷰했다. 최종 관련 **184 tests PASS**, Python compile와 `git diff --check` PASS. 초기 테스트 추가 위치 오류는 기존 assertions를 원래 테스트에 복원해 수정했다. 검토 범위의 미해결 코드 finding 0이며, 현재 PID682672에는 신규 계측이 미반영이다. 다음 승인된 정상 기동의 frozen parent→자연 Sentinel→controller/PREOPEN 판정은 기존 `EntryRecheckNaturalAttribution0907`에서 확인한다. 이 수리는 실주문·가격·수량·guard·provider·env를 변경하지 않는다.

## 원천 품질과 적용 경계

- 14:11:53 read-only runtime verify는 PID682672에 대해 PASS, missing/mismatch/finding0. manifest 단독 비교의14개 차이는 persistent override/자동 날짜 갱신/승인된 AI context/launcher 계약을 반영하면 해소된다. 14:22 현재 PID의 퇴역 canonical env15개도 explicit OFF와 일치한다.
- 전일 tower의7개 canonical source SHA256은14:16 실제 파일과 모두 일치했다. 전일 strict summary_handoff PASS와 controller00:27:44 DONE은 오늘 PID 적용 및 경제성의 증거와 분리한다.
- 14:29~14:31 기존 heavy-analysis lock으로 write/backfill 없는 source-quality 감사1회: 173772 events/128 stages, hard gap1행, unknown/warning1 stage. 감사 중 raw가 추가되어 `source_quality_raw_changed_during_audit`이며 전체 PASS·canonical exclusion 완료로 주장하지 않는다.
- 직접 원본 확인은 `scalp_entry_action_decision_snapshot`918행 중14:18:07 record41204/386380 한 행의 `minute_candle_window_fresh_contract` 결손이다. stale 분봉 age86397000ms, micro unavailable 상태의 값은 튜닝 입력에 사용할 수 없다. 같은 호출은14:18:11 `fresh_ai_wait_observation_only_probe_veto`로 주문 없이 종료했다. 원본 행/hash를 보존하며 장후 안정 원천의 row exclusion/직접 workorder owner에 handoff한다. 이 한 행이나 unknown-token 경고로 오늘 모든 실거래를 차단했다고 해석하지 않는다.
- Market-weakness14:14는 KOSPI 지수/업종 source 결손으로 차단됐고14:16 양 시장 source gate가 복구됐다. collector 재시도·API budget·guard는 변경하지 않았다. 이후 반복과 마지막 terminal은 종료 대사에 기록한다.
- SK텔레콤 오후 service는14:24:08 기동→14:24:14 정상 exit이지만 반환 원장은9/3 HELD10주다.14:10 broker KRX/NXT 잔고에는017670이 없다. 이를 오늘의 정상 신규 episode/현재 보유로 세지 않으며 과거 exact fill/manual-exit/custody 대사 필요 상태로 남긴다. 잔고 부재만으로 과거 목표 체결·비용·원장 terminal을 합성하거나 state를 삭제하지 않는다.

근거와 후속 owner: [장중 지시문](../intraday-monitoring-task-instructions.md), [당일 checklist](../checklists/2026-09-08-stage2-todo-checklist.md). 최종 관찰 snapshot과 경제성 미검증 경계는 아래 종료 기록에서 확정한다.

## 종목 탐색과 경제성 판정

독립 market census의 마지막 canonical report는12:00:35, 설치된5분 capture는 report refresh 없이 계속 원천을 추가하는 계약이다. primary `liquid_common` KRX opportunity episode166의 executable BBO join112/166(67.47%), eligible100, resolved60/right-censored37/pending3이며, right-censor38.14%다. BBO95%·right-censor20% 조건과 official-master/cadence 계약이 닫히지 않아 `insufficient_evidence_scanner_recall`이다. EV는 null이며 이 report를 현재 시각 전시장 정상 포착 근거로 쓰지 않는다. 별도 top10 scope의70행이나 post-promotion1293행을 primary166과 합산하지 않는다.

14:05 post-promotion 진단은1293 unique promotion→attach1168, heavy eligible734 중 never-evaluated22(2.9973%), promotion lineage coverage100%다. 이는 발견 후 소비 진단이며 scanner 외부 기회 포착률이나 실주문 전환율이 아니다. 적정 AI/submit 차단만으로 scanner 정상·기회 부재를 결론내리지 않았다.

Prune source-only observer의14:05:21~14:13:40 부분 창에는 schedule1072(용량 제외1049/완료 episode 재사용13/기존 episode 재사용10), observation8(captured3/shared-read-budget-deferred5)이 있다. 이 부분 창은 전체 관찰 구간이나 unique episode 분모가 아니다. 당시 일일scheduled400/1200, pending8, captured154/gap238; active8/pending80/0.25초 local bound와 공통조회5/sec·source-only4/5 reservation을 확대하지 않았다. cohort별 resolved8~14, BBO join26.9~93.75%로20 resolved/95% coverage/20% right-censor floor를 닫지 못한다. full prune census에 EV를 외삽하지 않는다.

## 독립 주문 owner와 미대사 custody

- Samsung 오후 기계: BUY0052122 10주274500→SELL0052146 10주276000(14:21:58), BUY0052124 10주274000→SELL0052390 10주275500(14:18:19). COMPLETE/position0.
- 한국전력 오후: BUY0052249 10주34000→SELL0052261 10주34200(14:11:31), 둘째 BUY0052250은 NO_FILL/0주. COMPLETE를20주 전량 체결로 해석하지 않는다.
- 삼성 위젯: 기존10주에14:07:33 BUY0052179 10주가 추가되고, 기존 목표0038063의 취소 후 SELL0052183 20주/278000이 자기 owner target이다. 종료 시 계좌 대사는 아래 별도 시각으로 확인한다. 080220은 policy/current eligible state를 확인했으나 신규 episode의 효과는 미관측이다.
- SamsungE&A 오후: BUY0054887 10주50100(14:34:15)→SELL0055228 10주50500 TARGET_OPEN. 둘째 BUY0054890은 NO_FILL. 삼성중공업 오전의 target0018672/10주는 다른 독립 owner다.
- 승인 SD 오후:14:10 preflight success→14:14 PID811820→마지막14:40 완성봉 후14:43:10 NO_TRADE/exit0/position0. CJ, 두산, 한세, TYM, 영원, SK이터닉스 및 삼성중공업 오후의 정상 NO_TRADE와 팬오션 오후 NO_FILL은 장애가 아니다. 기존3 quarantine(CJ 오전/SK 정오/영원 정오)의 preflight exit4는 기존 비용 재검증 nonpositive guard이며 새 실패/복원 대상으로 세지 않는다.
- **한국전력 오전 custody 결손:** state9/8 HELD10/target0021943 filled0, 동일 owner의 registry는 target0021477와0021943 각각 FILLED10이다. `regular_two_leg_machine._reconcile_target`는 dated fill이 늦고 current-open에 없을 때 HELD로 보존하며 `run_until_terminal`은 HELD에서 종료한다. 늦은 fill의 registry 반영 뒤 state가 남은 경로와 부합한다. 현재 잔고에 없는 오전10주를 보유로 합산하지 않으며, 실제 비용/체결시각과 state 동기화 수용은 미완료다.
- 과거 제주반도체9/3 HELD20·SK텔레콤9/3 HELD10·팬오션9/4 HELD20도14:10 KRX/NXT 잔고에 없고 해당 날짜의 exact manual-exit receipt는 미확인이다. 과거 state만으로 현재 노출이나 목표 체결을 만들지 않는다. live state 정정은 다음 신규 진입/기존 custody 판정에 영향을 주므로 `user_authority`로 분리하고 기존 `WidgetEpisodeRecommendationApplyAcceptance0908`에 다음 해당 profile 기동 전 대사 조건을 남겼다.

주문번호·체결은 관찰 근거이며 정확한 수수료·세금의 당일 전체 대사는 수행하지 않았다. `realized_pnl=null`, `realized_pnl_status=unreconciled_exact_cost`; gross 가격차나 과거 원장 복원을 이번 수리의 순이익 증가로 보고하지 않는다.

## 자연 표본·후속 ledger

아래 shortage ID는 이 보고서의 진단 key이며 실행 owner는 기존 checklist ID를 재사용한다. 유입률·rolling expiry·maturity를 닫지 못한 축에 임의 finite ETA를 주지 않는다.

| Shortage ID / 실행 owner | 최초 결손·분모 | 상태 / 다음 확인 |
| --- | --- | --- |
| `scanner_recall_krx_liquid_common_0908` / RuntimeEnvIntradayObserve0908 | primary166, BBO112/166;95% 필요, 유효 exact join46개 부족. resolved60≥20이나 right37/97=38.14%>20%, master/cadence 미완료 | blocked_missing_evidence; 다음 정식 census report에서 같은 scope/master/SLA/floor 확인. 신규 capture만으로 과거 gap 복원 금지 |
| `scanner_prune_outcome_0908` / ScannerLookupAttentionNaturalEvidence0908 | cohort resolved8~14/20, deficit6~12; coverage26.9~93.75%/95% | blocked_missing_evidence; owner별 unique source와 mature BBO/rolling denominator 필요, 전체 prune EV로 외삽 금지 |
| `submit_call_parent_0908` / EntryRecheckNaturalAttribution0907 | same call 안 parent 변경으로 exact ledger 제외; 수리184 PASS, 현재 PID 미반영 | structural_population_exhaustion의 계측 원인 수리, deployment pending. 다음 승인된 정상 기동→frozen parent 자연행→Sentinel/controller; 과거4 unclassified를 합성해 제거하지 않음 |
| `source_minute_window_0908` / IntradaySourceQualityGateCheck0908 | stale minute-window1행/검사된 snapshot918행, audit raw 변경 | blocked_missing_evidence; 장후 안정 source의 exact row exclusion/workorder. 진단 수리에 별도 양수 EV를 요구하지 않음 |
| `machine_late_terminal_custody_0908` / WidgetEpisodeRecommendationApplyAcceptance0908 | 한국전력 오전 state와 exact filled target 불일치 및 과거3 state 미대사 | structural_population_exhaustion: 자연 신규 표본 대기로 해결할 수 없는 terminal 동기화 문제. exact receipt·계좌·현재 주문 부재 및 권한 내 state 정정 검증 필요 |
| `ai_exact_economic_0908` / AIDecisionActionOutcomeNaturalEvidence0908 | provider 호출 성공과 partial/missing exact replay source 분리; 현재 net-economic floor census 미완료 | blocked_missing_evidence; 자연 R0→#82→frozen optimizer→metadata consumer와 별도 full-gate receipt. 무제한 Provider replay·과거 ingress 재합성 없음 |

Main 신규 submit0의 원인은 위 상위 탐색과 후단 차단을 함께 확인해야 하므로 단순 시간 해결형 shortage로 분류하지 않는다. limit-down은 실제 load/heartbeat와 natural target0이어서 `healthy_no_natural_sample`이며 승격 ETA 대상이 아니다. main real holding/exit가 없는 관찰 창의 smoothing·AVG_DOWN/PYRAMID 효과는 미관측이다.

## 종료 계좌 대사

마지막 broker read-only 조회 **14:57:34.939 KST**: KRX/NXT normalization complete, 삼성전자30주=widget owner30주/SELL0057234 30주277000, 삼성중공업10주=오전 episode/SELL0018672 10주, 삼성E&A10주=오후 episode/SELL0055228 10주. 미체결은 이3개 SELL이며 main position0, owner collision0이다.14:10 잔고와 차이는 자연 체결·한국전력/Samsung 오후 청산 및 위젯14:51 추가매수다. 위젯은 BUY0057233 10주 체결 뒤 기존20주 target0052183을 취소하고 자기30주 target0057234로 갱신했다. 이 계좌 조회 시각을15:00 원자 snapshot으로 표시하지 않는다.

## 15:00 최종 판정

**관찰 완료 / 주의·미해결 항목 유지.** [보존 evidence](./2026-09-08-intraday-monitoring-1500-evidence.json)는66회 관찰,14:57:34 broker 대사, runtime verify/retirement/source SHA와 실제 결손 원본을 포함한다. 파일 취합은15:00:21이며 상태 원장 사본은 그 취합 시각이다. AI 집계는 decision timestamp14:04:27~15:00:00, 마지막 주기 snapshot은15:00:01로 고정한다.

| Owner / 영역 | 마지막 관찰과 판정 | 남은 경계 |
| --- | --- | --- |
| Main / PREOPEN | PID682672 유지, selected20 handoff read-only PASS; 최신14:55:05 funnel AI214/budget574/latency87/submit0 | SUBMIT_DROUGHT_CRITICAL. 원인별 exact terminal UPSTREAM337/LATENCY331/AI79/PRICE92/BROKER0은 별도 causal 분모이며 stage 수와 합산하지 않음 |
| Micro / WS |14:59:54 trade847283/depth898332, worker/writer/queue 오류0, writer2+2, 자동중지 없음; disk7.72GB | invalid depth/timestamp 관측은 유효 입력으로 보간하지 않음. 수집 정상과 경제성/모든 quote freshness 정상은 별개 |
| Limit-down | fresh loaded heartbeat, active target0, active live policy 없음 | source-only healthy_no_natural_sample; ordered0B+0D 신규 대상 수용은 미관측 |
| Widget | PID21846/collector249964 유지; 삼성30주 target0057234,080220 정책/current eligible 확인 | 삼성 target 미완료,080220 자연 episode 효과 미관측; exact net PnL null |
| Low-price/Samsung | 현재날짜 state50개: NO_TRADE42/COMPLETE5/TARGET_OPEN2/HELD1. Samsung 오후 COMPLETE 별도 | HELD1은 한국전력 오전의 stale custody이며 현재 보유로 인정하지 않음. 과거3 HELD도 별도 미대사; eligible53은 현재 PID 수가 아님 |
| 공통 process/error | 마지막 snapshot detector14:59:37 warning, process/resource/lock 등6 PASS, panic-sell 최근 오류 이력 warning; 기존 quarantine3 유지 | 최근 FAIL은 최신14:16 source 회복과 구분. 새 critical·hang·중복 owner 미관측 |
| 퇴역/OFF/비우선 | 현재 PID canonical15 explicit OFF, Swing/sim의 새 실주문 owner·독립 resource 간섭 미관측 | not_applicable_retired_or_deprioritized; 무표본 복원·승격 대기열 없음 |

AI trace74건 중 실제 Provider 호출56건(Entry OpenAI11/entry-price Bedrock28/analyze-target OpenAI14/holding-score OpenAI3)은 parse_ok56/56이다. 미실행18건(Entry7/holding-score11)은 입력 preflight와 분리한다. 실제 호출의 request capture는 captured45/partial11, payload replay exact31/nonexact25로 **호출 성공이 exact replay·입력 비교·판단 경제성 완료를 뜻하지 않는다**. holding-score trace 자체로 main 실보유·매도 owner를 인정하지 않는다. main 실보유가 확인되지 않은 이 관찰에서 smoothing·scale-in·holding-flow 실제 개선을 주장하지 않고, R0→R3/다음 PREOPEN 및 경제성 검증은 기존 OPEN owner에 남긴다.

이번 보완은 call-local parent 계측/consumer3개 파일과 관련 문서다. 관련184 tests·compile·self-review PASS, 수정 범위 미해결 finding0. **현재 PID에 새 계측 미반영**, 거래 프로세스 재기동·주문·env·threshold·provider·operator lock 변경 및 비싼 report 재생성은 수행하지 않았다. 수리 완료로 drought 해소·live 자동 적용·순이익 개선을 선행 선언하지 않는다. 새 custody finding은 source-only 권한으로 state를 변경할 수 없어 미해결이며 scoped review0에 포함해 감추지 않는다.

문서 print-only parser는34 tasks를 출력하고 RuntimeEnvIntradayObserve0908/EntryRecheckNaturalAttribution0907/IntradaySourceQualityGateCheck0908/WidgetEpisodeRecommendationApplyAcceptance0908을 각각1회 포함한다. 외부 sync는 실행하지 않았다. 필요한 경우 사용자가 실행할 표준 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
