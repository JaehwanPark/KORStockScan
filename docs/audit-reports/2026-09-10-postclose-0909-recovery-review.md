# 9/9 장후 RED 복구 및 재발 방지 검증

**Postclose Control State: YELLOW — 운영 RED 해소.** 최종 관찰 `2026-09-10T01:02:16+09:00`, 대상 거래일 `2026-09-09`. 마지막 cleanup/final detector 성공과 최신 strict/controller를 확인했다. 검토한 수리 범위의 미해결 P0~P2 finding 0, 전체711 테스트 PASS. 다음 자연 수집·정책/PID 소비와 비용 후 경제성은 아직 완료가 아니다.

- Source date: `2026-09-09`; 실제 실행 시각: `2026-09-10 KST`. 자정을 지나도 source date를 변경하지 않았다.
- 사용자 지시: 해소·재발 방지가 완료될 때까지 권장 순서의 수리, 코드리뷰, 보완·재검증. 이번 범위는 source-only/report/automation 복구이며 실주문·취소, 매매 PID, live env/operator lock/provider/threshold/safety는 변경하지 않는다. 날짜별 분석 실행 mutex는 별도 자동화 계약이다.
- 이전 [23:49 RED 기록](2026-09-09-postclose-authorized-recovery-review.md), 고정 검증·추천 원장과 실제 FAIL 로그를 보존한다. 이전 판정을 소급 수정하지 않는다.

## 최초 결손과 보완

1. Low-price 원천의 검증된 수동 청산 receipt 5건이 `_sanitize_leg`에서 누락됐다. 기존 report와 state의 비-metadata 필드가 모두 같은 경우만 `--refresh-receipts-only`로 projection한다. broker 호출 0, 경제성 재계산 false, 정책 변경 0이다. attribution은 applied registry의 schema/owner/date/order/quantity/price/receipt를 독립 대사한다. 확인되지 않은 실제 체결시각·보유시간은 null, 경제성·timing eligibility는 false로 남는다.
2. 닫힌 9/9 원천의 실제 신호 18개 모두에 유효한 exact entry market window가 없었다. 원천 읽기·schema·manifest·물리 scope와 closed canary가 정상인 경우만 `closed_exact_market_window_exclusion_v2`를 발급한다. 신호 -30초~+6초는 pre-signal과 micro 0/1/3/5초 확인창을 포함한다. 두산 오후 신호의 약 20분 뒤 자료는 30분 출구 연구창 자료이지 진입 시점 자료가 아니다. 잘못된 원천·미완료 수집·미분류 scope 오류는 이 격리를 사용할 수 없다.
3. 6개 actual decision anchor의 owner timestamp 결손은 5개 applied 수동 receipt와 기존 정상 원 주문 기록으로 대사됐다. 원래 `owner_anchor_contract_invalid`와 null 시각은 보존하며 수리 가능한 companion gap 목록에서만 검증된 과거 결손을 분리한다. 새 유효 표본은 0, 원래 신호 분모 18은 유지한다.
4. 23:20 hard deadline 이후 원천을 복구해도 finalization이 다시 같은 deadline 실패로 끝나는 경로를 보완했다. `--recover-closed-target`는 오늘/전일의 기존 exact-date FAIL이 있을 때만 허용한다. 날짜별 실행 mutex, predecessor 즉시 검사, bounded summary/cleanup/detector를 유지한다. 일반 예약 실행의 deadline은 그대로다.
5. 복구 detector는 source-date cron/artifact를 읽고 나머지 현재 health를 실제 복구 시각으로 검사한다. 7개 검사를 유지하고 operational mutations는 모두 금지한다. 날짜를 소급한 새 실행으로 표시하지 않는다. detector lock 점유는 exit75로 실패하며 이전 성공으로 완료하지 않는다. 실패한 복구 invocation report도 보존한다.

## Review gate와 검증

- 00:37:37 explicit recovery는 선행/strict를 통과했으나 cleanup이 00:43:58 `invalid_result`로 FAIL했다. 저장소 CLI stdout의 Kiwoom 설정 안내 문구가 JSON 앞에 섞인 직접 원인이다. 저장소 작업 자체 exit0/healthy였어도 이를 성공으로 처리하지 않았다. 진단 stderr/JSON stdout 분리 후 저장소·cleanup 회귀140 PASS를 확인했다.
- 이 실패의 generic cleanup counter는 전부0이다. 원 완료 시각/receipt hash를 검증하는 `--recover-storage-only`를 보완해 실패한 저장소 단계만 다시 실행한다. 정상 generic lane이나 동일 oversized-log 관찰을 다시 실행하지 않고 기존 writer-defer state를 보존한다. 다른 실패·필드 누락·오래된 receipt·새 START는 reuse를 차단하는 반례 테스트를 추가했다.

- `korstockscan-review-gate`: producer→직접 consumer→wrapper→verifier, null/owner/route/epoch·원천 읽기 실패, authority, 날짜·최신 terminal, lock 경합을 재검토했다.
- 최종 targeted regression: **711 passed in 141.24s**. attribution/timing/low-price, controller/finalization, detector/cron/artifact freshness, storage/cleanup의 10개 test file. 앞선565 PASS 이후 실제 cleanup JSON 오염을 발견해 보완했고, 부분 복구의 반례까지 포함해 전체를 재실행했다.
- Python compile, shell `bash -n`, `git diff --check`, print-only parser 통과. 현재 checklist14개 포함/중복0. source-generation/direct handoff와 detector report contract를 최종 시점에 읽기 전용 재검증했다.
- 이 검증은 수리 경로의 계약 검증이며 신규 매매 정책·재기동·실수익 또는 다음 자연 수집의 성공을 증명하지 않는다.

## 최소 재생성과 추천 fixed-point

- 보존 위치: `/tmp/korstockscan-postclose-0909-after-midnight.8u7isn/`. 원 low-price report, attribution/timing/controller/verifier, manual registry 및 수정 전 주요 코드와 각 실행 로그를 보존했다. 이전 frozen 원장은 변경하지 않았다.
- 실제 재생성: low-price receipt projection → attribution → weakness hysteresis → timing → postclose approval → summary-only controller의 일반 verifier/tower/checklist/strict. 중간 17/18 판정은 마지막 정확한 시간창 반례를 보완한 뒤 해당 producer와 직접 consumer만 다시 생성했다.
- 기존 main/EOD/widget evaluation 전체, Provider replay 및 매매 process는 재실행하지 않았다. low-price `policy_mutations=[]`, timing baseline carry/선정 0을 유지한다.
- [새 generation 전수 원장](2026-09-10-postclose-0909-recovery-intake.json): **72=요청11+비요청61**, native ID 72 동일, 신규/삭제/결정 변경/처리상태 변경 0, 보존식 PASS, 미분류/actionable 0. source hash가 바뀐 기계 보고서를 현재 generation으로 다시 결속했다.
- 요청11은 `blocked_missing_evidence`이며 구현 완료 0이다. 비요청61=관찰23+보류32+거절3+증거대기3. 내부 fixed-point true와 전체 구현 완료 false를 분리한다. 과거 승인된 widget/episode 21개 successor는 이 원장의 subset이며 별도 고유 작업으로 합산하지 않는다. 승인된 9/10 정책/기동의 자연 소비는 기존 `WidgetEpisodeApprovedNextDayExecution0910`에서 확인한다.

## 남은 효과와 재발 관찰

- Main submit drought: 기존 exact source as-of 9/9 19:20:05. KRX terminal1111=upstream654+latency320+AIauthority101+price36+broker0; NXT-aftermarket225=175+26+12+12+0, accepted submit0. 이번 metadata/automation 수리는 제출 회복이나 비용 차감 순익 개선이 아니다. 원 `EntryRecheckNaturalAttribution0907`의 PREOPEN/PID/실제 제출·체결·terminal·비용 acceptance를 유지한다.
  - `buy_funnel_sentinel_2026-09-09.json` SHA256=`4152ac14b0a4dcb07e05eb2d20503065043065016fcd7cbd6ca88daed22750b7`. primary `NXT|NXT_AFTERMARKET:SUBMIT_DROUGHT_CRITICAL`; KRX도 critical이다. raw unique KRX AI361/budget549/latency105/submit0, NXT AI60/budget75/latency12/submit0은 위 exact terminal 인과 분모와 별개다. 원 floor AI20/budget3와 submit/AI20%·submit/budget10% 기준은 변경하지 않았다. 경보·canonical handoff는 정상 전달됐지만 실제 drought 해소·비용 차감 경제성은 미완료다.
- Widget/episode: 실제 신호18/eligible0, owner timestamp 제외6, closed entry window 제외18. 공통 kernel 및 4군 연구의 정상 산출과 실제 유효 paired/holdout·경제성 표본은 별개다. 다른 venue 자료, 과거 unverified epoch, 후행 exit-study 자료로 진입창을 메우지 않는다. 9/10 08:40 collector owner와 이후 장중 actual signal→micro→submit/fill→terminal/비용이 남는다. 유입이 없으면 유한 ETA나 경제성 PASS를 발명하지 않는다.
- Adaptive exit: 기존 연구/부분 구현과 최초 numeric envelope·실제 launcher·validator/PREOPEN/enrollment 미완료를 구분한다. 이번 복구는 새 SELL family 활성화나 기존 보유 이관이 아니다.
- 재발 방지 코드의 회귀 검증과 다음 자연 실행 수용은 별도다. 과거 원천 복원 불가를 무한 재실행하지 않고 기존 next-source owner를 유지한다.

## 최종 운영·체크리스트 대사

9/10 00:55:05 최종 explicit recovery는 선행 owner 전부 ready를 확인하고 00:55:49 strict handoff PASS→00:55:50 controller done→00:57:06 cleanup DONE→00:57:08 final detector DONE으로 종료했다. `error_detection_2026-09-09.json`의 실제 timestamp는00:57:07/실제 as-of-date9/10, source-date9/9이며 7개 detector 모두 PASS·운영 mutation0이다. cron/artifact는 exact source-date, 나머지 health는 current-at-recovery임을 명시한다. 마지막 PID/실제 lock 점유0이고 원래 FAIL보다 최신 성공 근거가 있다.

| Owner | Target date | Latest state | First failure / 원인 | Repair | Validation | Latest terminal |
| --- | --- | --- | --- | --- | --- | --- |
| EOD |9/9|done|이번 수리 대상 없음|재실행 안 함|exact-date status/log|9/9 20:55:48|
| Main postclose |9/9|succeeded|22:06 workorder 권한 필드 누락(앞선 수리)|기존 tail 수리 보존|exit0/status·wrapper|9/9 22:13:08|
| Final verifier |9/9|done_warning|상위 갱신 뒤 summary stale|일반 verifier→tower/checklist→strict|handoff PASS/issues0|9/10 00:55:49|
| DONE controller/follower |9/9|done|구조 결손을 과거 자료 대기로 반복|검증된 timestamp/window 격리 후 summary-only|현재 controller done; batch offline terminal/consumer closure|JSON9/10 00:55:50; 원 wrapper9/9 22:25:46; consumer22:25:44|
| Tuning monitoring |9/9|success|이번 수리 대상 없음|재실행 안 함|status exit0/검증 archive 유지|9/9 22:18:52|
| Dashboard archive |9/9|done|이번 수리 대상 없음|재실행 안 함|exact-date DONE|9/9 20:50:11|
| Widget evaluation |9/9|done_warning|이번 수리 대상 없음|재실행 안 함|unit Result=success/exit0·네 producer 같은 날짜|9/9 22:11:40|
| Episode recommendations |9/9|source-only terminal/증거 잔여|수동 receipt projection 누락|metadata5→owner gap6 독립 대사|경제성/null 보존, 정책 변경0, intake 전수 대사|projection9/10 00:23:43; approval00:33:02|
| Machine final refresh |9/9|done_warning/과거 source 격리|exact entry window18 결손|attribution→weakness→timing→approval 최소 재생성|18/0 유지, 검증된 owner 제외6/수리 가능한 gap0|원 unit9/9 22:25:34; attribution9/10 00:31:49/timing00:32:46/approval00:33:02|
| Finalization/error detector |9/9|done/pass|구조 차단·23:20 deadline, 이후 cleanup JSON stdout 오염|explicit source-date recovery + strict JSON stdout + 실패 storage lane만 재실행|선행 전부 ready/strict PASS/cleanup DONE/7 detector PASS/mutation0|9/10 00:57:08|

부분 cleanup의 generic 원 receipt는 `2026-09-10T00:43:58+0900`, SHA256=`9ec79da79aca9a32c219fb6ecdc8de92a84b012b3923d5a73997fcce1d51bb9c`다. storage 재검증 receipt `tmp/micro_reversion_storage_maintenance.IEQge4.json`은 strict JSON/exit0/status pass/healthy, 신규 storage action0·report artifact action0이다. 일반 cleanup을 새 실행으로 가장하지 않았으며 `generic_cleanup_reexecuted=false`를 기록했다. 기존 writer-defer 관찰2회도 그대로 유지했다.

최초 일반 정리에서 retention에 따라 system metric72행과 재생성 가능한 Python/test/tool cache36개를 정리했다. metric 원본은 별도 백업이 없으면 복원할 수 없다. active/archive log 삭제0, 원시 source-exclusion 삭제0, micro storage purge0이다. 검증 압축으로 약3.03GB를 회수했고 압축 자료는 원래 내용으로 복원 가능하다. 두 번째 부분 복구는 이 정리를 반복하지 않았다.

마지막 read-only 대사에서 source/rows hash가 [현재 원장](2026-09-10-postclose-0909-recovery-intake.json)과 같고, 72행 보존식·fixed-point·미분류0 및 tower/checklist handoff PASS를 재확인했다. 11개 증거 차단 요청, 실제 submit0, 원천·경제성/자연 policy 소비, adaptive 최초 승인 미완료 때문에 GREEN은 아니다.

### ID별 as-of 분류 (9/10 00:40 KST)

원래 9/9 체크리스트의 due 13개는 기한 내 완료와 복구 시각을 구분한 `overdue_unresolved/부분 수용` 기록이다. 아래 사유를 process FAIL로 바꾸지 않는다. 9/10 14개 및 10/2 1개는 `not_yet_due`이며 정상 예약을 앞당기지 않았다. 원천·generation은 위 전수 원장과 각 원 체크리스트 Source/Receipt를 따른다. 새 producer 실행 여부는 최소 재생성 절에 한정한다.

| Checklist | Stable ID | Due / TimeWindow | 이번 분류·확인 / 잔여 |
| --- | --- | --- | --- |
| 2026-09-09 | `CodeImprovementWorkorderReview0909` | 2026-09-09 21:15~21:25 | 현재 72행 재대사, 요청11 증거 차단·미분류0 |
| 2026-09-09 | `MachineLifecycleTurnoverObjectiveFollowup0909` | 2026-09-09 21:30~21:40 | 18/0 과거 격리·owner6 대사, 새 수집/경제성·adaptive 최초 승인 잔여 |
| 2026-09-09 | `AutomationTriggerDecisionSummary0909` | 2026-09-09 21:40~21:55 | trigger 원래 기록 유지, 새 controller/strict 정상; finalization 최종 receipt 확인 |
| 2026-09-09 | `PatternLabSmallNetNaturalEvidence0908` | 2026-09-09 20:10~21:55 | 새 Pattern 원천 없음, 기존 source-only/자연 증거 잔여; 반복 Provider 실행 없음 |
| 2026-09-09 | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908` | 2026-09-09 08:40~08:45 | 과거 exact 창18 격리; 9/10 Continuity0910에서 새 epoch/route/창 확인 |
| 2026-09-09 | `PostcloseRecoverySourceAcceptance0908` | 2026-09-09 20:10~21:55 | 계약 수리·current hash handoff, 요청11 원천/자연 acceptance 잔여 |
| 2026-09-09 | `AIDecisionActionOutcomeNaturalEvidence0908` | 2026-09-09 20:10~21:55 | 기존 22:25 follower terminal 보존, provider0/control·경제성 미수용 |
| 2026-09-09 | `WidgetEpisodeRecommendationApplyAcceptance0908` | 2026-09-09 08:57~14:45 | 기존 9/9 기동/수동 custody 기록 보존, 9/10 별도 승인 후속은 미래 |
| 2026-09-09 | `MarketWeaknessNaturalEvidence0907` | 2026-09-09 09:05~15:30 | 영향 weakness report 재생성, 실제 정책/PID·비용 EV acceptance 잔여 |
| 2026-09-09 | `OperatorPolicySuccessionAcceptance0908` | 2026-09-09 07:35~08:45 | 기존 PREOPEN 부분 수용 보존, first-use/경제성 미완료 |
| 2026-09-09 | `DailyThresholdNaturalAcceptance0908` | 2026-09-09 20:10~21:55 | 기존 Daily/EV 보존, 새 PREOPEN·자연 수익 미관측 |
| 2026-09-09 | `EntryRecheckNaturalAttribution0907` | 2026-09-09 20:10~21:50 | 동일 scope accepted submit0; 9/10 PREOPEN/RuntimeEnv owner 직접 연결 |
| 2026-09-09 | `ScannerLookupAttentionNaturalEvidence0908` | 2026-09-09 20:10~20:40 | 기존 source/정책 보존, exact executable BBO/독립 모집단·receipt/R6 잔여 |
| 2026-09-09 | `ScannerLookupAttentionCalendarMaintenance1002` | 2026-10-02 20:10~21:55 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `WidgetEpisodeApprovedNextDayExecution0910` | 2026-09-10 08:40~09:00 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910` | 2026-09-10 08:40~08:45 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `ThresholdEnvAutoApplyPreopen0910` | 2026-09-10 08:50~08:55 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `RisingMissedScoutRuntimePreopen0910` | 2026-09-10 08:55~09:00 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `RuntimeEnvIntradayObserve0910` | 2026-09-10 09:05~09:20 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `SimProbeIntradayCoverage0910` | 2026-09-10 09:35~09:50 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `IntradaySourceQualityGateCheck0910` | 2026-09-10 14:20~14:35 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `ThresholdDailyEVReport0910` | 2026-09-10 16:30~16:45 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `HumanInterventionSummary0910` | 2026-09-10 17:00~17:15 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910` | 2026-09-10 18:00~18:20 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `CodeImprovementWorkorderReview0910` | 2026-09-10 21:15~21:25 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `MachineLifecycleTurnoverObjectiveFollowup0910` | 2026-09-10 21:30~21:40 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `AutomationTriggerDecisionSummary0910` | 2026-09-10 21:40~21:55 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |
| 2026-09-10 | `PostcloseSourceQualityGateReview0910` | 2026-09-10 21:40~21:55 | not_yet_due; 해당 창에서 기존 owner·선행 조건 확인 |

미분류 0. print-only parser는 exit0, 현재 9/10 체크리스트 14개 모두 포함하고 current ID 중복 0이다. 원래 source9/9의 미완료 acceptance를 오늘 실행 성공이나 새로운 미래 수익으로 소급하지 않는다.

01:01 후속: `AutomationTriggerDecisionSummary0909`는 지정 source9/8의 total14/run6/disabled8/skip0/source_missing5/force0 재확인과 최신 source9/9 summary/terminal 복구로 `trigger_contract_pass` 완료했다. 위 표는00:40 intake snapshot이며, 최종9/9 OPEN은12개 부분/증거·자연 acceptance와10/2 예정1개다. 다른 acceptance를 함께 완료 처리하지 않았다.

### 검증 코드 generation

기존 dirty worktree 전체의 재검토 완료를 뜻하지 않으며, 이번 수리의 최종 파일 bytes를 고정한다.

| File | SHA256 |
| --- | --- |
| `src/engine/monitoring/low_price_two_leg_tuning.py` | `269bf9056a146f1c7beb8bb0e376026834f4fe68ffa1633523753560c4268e1f` |
| `src/engine/monitoring/machine_microstructure_attribution.py` | `7574030e633266e2ae7e5d96a8c3cd9950f3727d4d5e05a55a4f0693f002b5e2` |
| `src/engine/automation/machine_entry_timing_tuning.py` | `20e8d40d19c6fb340aa906e3213bae9099961108c179430bdcd23f23b0f38ecd` |
| `src/engine/error_detector.py` | `215e6bf89ca61505a1967db108f87ec0e8685ac38038aa7331b4a8a772c6175c` |
| `src/engine/error_detectors/cron_completion.py` | `49aaa6a20b9bc15c3eebf725dd04ca68280cd0562c322171a32834badfc988b9` |
| `src/engine/error_detectors/artifact_freshness.py` | `8c5986f6a9bfc32b9db485eb8acbbc210131ae9d78c449f4722bf211fcd5efcc` |
| `deploy/run_postclose_finalization.sh` | `099f3f7cb59f7d6b58fd8232d0179072cb5d272580c7b6135ff7f9af4686dfba` |
| `deploy/run_logs_rotation_cleanup_cron.sh` | `92518b16cc82d02180b48af70d6c863a3a90069d3bb0b355a53d0e6c264a2ce1` |
| `src/engine/scalping/micro_reversion/storage_maintenance.py` | `438923f08fe3e5d1aa7750d3506cf5341417b7f8986ac195d5e3733584e97dde` |
| `deploy/run_error_detection.sh` | `3fc6dd8e4a926d793b9b4a867154ccfc4ab7415abfb8307cf4ede28832bbc4c3` |
