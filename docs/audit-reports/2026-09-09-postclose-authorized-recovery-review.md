# 9/9 RED 복구·2-pass·9/10 위젯/에피소드 승인 후속

시작: `2026-09-09T22:50:32+09:00`. 최종 관찰: `2026-09-09T23:49:21+09:00`. source/target date는9/9, 사용자가 말한 내일의 effective date는9/10으로 고정한다. **Postclose Control State: RED**. 아래 코드 수리·승인 예약은 완료됐지만, 과거 원천 결손·controller 차단과 finalization deadline으로 전체 완료는 아니다.

## 승인 범위와 진행 순서

사용자는 `RED 해소하고 결함보완, 결함이 없을때까지 반복실행, implement now 2pass 구현, 위젯/에피소드 추천사항 구현 및 내일 실행`을 명시 승인했다. [앞선22:48 결과](2026-09-09-postclose-monitoring-review.md)는 새 승인 전 frozen receipt로 보존한다.

1. machine source/terminal의 최초 결손 및 verifier/controller/finalization RED 원인 수리. 과거 raw/체결시각/비용을 합성하지 않고 검증 가능한 row/epoch만 소비한다.
2. 현재 native 추천 전수와 직접 producer/consumer를 재검토해 메타데이터 결손·잘못된 반복 승격·실제 코드 결함·미관측 경제성을 구분한다. review/fix/test→최소 재생성→Pass2를 반복한다.
3. widget/episode 추천은9/10 effective 정책·원천/추천 ID·rollback·기존 timer/loader/guard에 결속한다. 사용자 승인과 기존 sample/source/cost/holdout 검증을 함께 요구하며 research_watch/reject를 live 추천으로 바꾸지 않는다. 새 adaptive-exit의 numeric envelope나 미래 실체결을 발명하지 않는다.
4. 매매 수량/leg·broker/account/order/price-freshness/hard safety·provider route·main env/lock은 이번 복구의 완화 축이 아니다. 기존 보유 target/custody와 신규 dated 정책을 분리한다. 내일 실행 승인으로 오늘 주문 또는 모든 매매 process의 즉시 기동을 추론하지 않는다.

`korstockscan-review-gate`를 사용한다. 기준5개 수리와418 tests는 이전 턴 검증이며 이번 새 변경의 테스트를 대신하지 않는다. 외부 Project/Calendar sync는 실행하지 않는다. 내일의 실행/자연 수용은 [9/10 checklist](../checklists/2026-09-10-stage2-todo-checklist.md)의 기존 machine followup과 별도 승인 적용 확인 항목으로 연결한다.

## 새로 확인한 결함

- one-share 기존 family 관찰을 repeat counter만으로 `implement_now`로 승격하던 경로를 좁은 implemented/source-only 계약에 한해 수정했다. 실제 source gap은 계속 escalation한다.
- closed/lossless pre-enqueue receipt와 timestamp census가 일치하는 마지막 epoch만 machine offline 입력에 허용했다. 마지막 epoch `1788932497558153946`(14:41:37 이후), 동일 PID의 receipt20개를 검증하고 이전6개 epoch는 market/depth/reference 모두 제외했다. R0/Provider 전역 hold와 과거 원천은 그대로다.
- main Micro delivery 분모에 들어간 명시적 `simulated_execution_view_only` 평가390건을 분리했다. 실제 주문/record/owner 충돌 또는 불명확한 권한은 제외하지 않는다. `required_holding_payload_missing` 추천은 새 producer에서 사라졌으며 실제 main anchor1/venue162 결손은 남는다. raw 자체를 삭제하거나 sim를 main 성과로 합치지 않았다.
- main source-only workorder의 직접 downstream을 실제 `runtime_approval_summary` owner까지 명시했다. consumer 이름 보완은 원래 시장/경제성 결손의 완료가 아니다.
- Pass2 재검토에서 scanner bounded rejection의 명시적0 예약을 양수 horizon 검증에 넣던 결함을 확인했다. 실제 `097520/SCANGEN-12259-1788908595862-3142502089484`의 `active_episode_capacity_rejected`, count0, 네 비권한 필드가 근거다. 선언된 rejection만 horizon 미발행으로 보존하고 실제 예약0/invalid authority는 계속 conflict다. 같은 시각의 다른 status/count/authority가 중복으로 버려지지 않게 fingerprint도 보완했다. cache v16으로 원본 gzip을 다시 읽는다. 호출량/slot/선정/BBO 경제성 조건은 변경하지 않았다.

검증 묶음은 최초 epoch/one-share288건, low-price/owner428건, Micro187건, 재결합310건, scanner/WS273건과 추가 multi-revision6건이다. 서로 겹치는 테스트를 고유 합계로 더하지 않는다. scanner 첫 회귀의5실패에서 동일 timestamp의 다른 선언이 dedup되는 경계를 확인해 수정했고 재실행273건 PASS다. Python compile/bash syntax/diff 검사 PASS이며 마지막 consumer 재생성·원장 hash 대사는 아래 후속으로 기록한다.

## 9/10 승인 profile 검증·예약 준비

source9/9 native 추천7개 중5개를 기존 positive calibration 양쪽/holdout/full·67거래일·0.23% 비용 재계산으로 검증했다. 실제 numeric 변경은 `kepco_late_morning`1개, 신규는 `lotte_chemical_morning`, `lotte_chemical_afternoon`, `tym_late_morning`3개다. `sk_telecom_morning`은 기존 수치 재확인이다. 영원무역·두산 정오는 각각 calibration 한쪽EV−0.00087%/−0.003339%로 보류한다. 전체 catalog59/기존격리3·10주×2 leg를 유지한다.

원천 SHA256 `362b22217dd46da839ab9eb0795ee37e3e5aa438a1091532ea65ef4a906c16a5`, [승인 projection](2026-09-09-low-price-recommendation-apply-evidence.json) canonical SHA256 `9fd7c9b681f8e3dca3ab47dd2e01c5e5bc31dbee740bd35873a02e98414b5389`를 결속했다. 새19종목 standing authority는9/10부터만 유효하고 원래9/9 authority를 덮어쓰지 않는다. 현재 주문/custody는 이관하지 않으며 next PREOPEN broker reconciliation이 독립 수용조건이다.

관련428 tests, compile, shell syntax, 신규 timer6개 `systemd-analyze verify`, diff 검사 PASS. 재리뷰에서 신규wrapper 등록·도입일·과거날짜 catalog 테스트 및 복수 revision 승계 경계를 보완했다. 이 검증은 아래 예약 설치의 선행조건이지 내일 실제 policy/PID 소비나 수익의 완료가 아니다.

23:17 실제 신규timer6개를 설치·enable했고 NEXT는 모두9/10이다. 롯데화학 오전 preflight09:15/live09:19, 오후14:15/14:19, TYM 오전후반09:55/09:59다. 거래 service3개는 inactive/MainPID0이며 오늘 매매 process를 기동하지 않았다. 기존07:32 symbol-owner 자동 적용 wrapper는9/10부터 별도19종목 standing authority를 읽도록 연결했다. 원래9/9 authority는 보존하고 `011170 # machine_owner_scope lotte_chemical_low_price_two_leg_owner` 한 행만 registry에 추가했다. manual/user 배제·기존 주문/custody는 해제하지 않았다. 설치 시 재실행한 것은 timer 등록뿐이며 broad installer·오늘 PREOPEN 수동 적용은 하지 않았다.

## 아직 닫히지 않은 원천·경제성

- machine actual signal18/eligible0:17개 신호는 검증된 마지막epoch 이전이며 마지막 widget NXT17:55 신호에는 이후 exact-route raw가 없다. NXT raw의 마지막 관측은14:42:44이고 NXT_AFTERMARKET partition도 없다. 알려진 다른 거래소/세션으로 채우지 않았다. owner invalid6에는 manual-sell 실제 청산시각 결손이 포함되며 target 주문의 timestamp-loss receipt와 혼동하지 않는다. timing policy는9/10 scopes0/immediate baseline carry다. epoch 수리 자체는 완료해도 실제 timing/4군 경제성은 미완료다.
- pipeline raw291147/producer290196(951결손), flush deadline20:01:59 초과는 보존한다. raw suppression OFF와 검증 gzip 원본이 유지된다. 원래 producer 영수증을 raw-derived 집계로 덮어써 parity 성공을 만들지 않는다.
- main submit0, executable BBO/anchor/venue/AI 비용·새 prompt 검증은 별도다. 수정된 진단·내일 machine 신규 정책을 오늘 main drought 해소 또는 실수익으로 보고하지 않는다.
- adaptive-exit의 first-fill/path/정산과 최초 numeric envelope/launcher/enrollment 미완료는 기존 machine owner에 남긴다. 이번 승인으로 거절/research-watch를 임의 live policy로 바꾸거나 승인 수치를 발명하지 않았다.

## Pass1/Pass2와 canonical 전달

[Pass1](2026-09-09-postclose-authorized-intake-pass1.json)은74행/요청13/비요청61, [Pass2](2026-09-09-postclose-authorized-intake-pass2.json)는72행/요청11/비요청61이다. 후속WS/sim분리에서 `order_scanner_scan_generation_conservation_gap`·`order_microstructure_v3_required_holding_payload_missing` 두 요청이 제거됐고 new/decision_changed는0이다. 앞서 잘못 승격된 one-share2건은 기존 family 관찰로 환원했다. report-only panic native 행의 최상위 authority도 원래 provenance대로 보완해 invalid authority0을 확인했다.

현재 요청11건은 전부 source-only·`blocked_missing_evidence`이며 구현 완료0으로 보존한다. 비요청61=관찰23+보류32+거절3+증거대기3이다. 미분류0/actionable0·보존식PASS·내부 `implementation_fixed_point=true`는 **더 할 수 있는 허용 구현 미분류가 없다는 뜻이고 전체 구현완료가 아니다**. `all_implementations_completed=false`를 유지한다. [고정 검증 근거](2026-09-09-postclose-authorized-recovery-validation.md)와 현재 행/원천hash로 companion12행(11차단·1관찰)을 재결속했다. 옛 companion/원장은 `/tmp/korstockscan-postclose-recovery-20260909.XQD48N/`에 보존했다.

[위젯/에피소드 successor21행](2026-09-09-widget-episode-approved-successor-ledger.json)은 이72행의 subset이다. low-price5건 구현/예약, 기존 widget080220정책1건 verified, 나머지는 기존 보류/거절/증거대기/연구관찰이다. 원 source decision을 덮어쓰거나72+21=93개로 합산하지 않는다. 원래 Source-only companion의 상태와 별도 사용자 승인의 실행 disposition을 구분한다.

최소 재생성은 machine attribution→weakness→timing→approval, main Micro/WS→workorder→EV→workorder→runtime summary→apply-gap→key lineage→conversion→workorder/EV/final summary→tower→checklist→strict다. R0/Provider·Pattern·EOD/widget 전체/매매 process는 재실행하지 않았다. apply-gap AI는 기존provider를 유지한 `not_required`라 새호출0이다. CLI에서 source-date와 completed-machine-source-date를 동시에 준 첫checklist 명령은 exit2로 중단했고, 문서화된source-date 단일명령으로 수정한후 check/strict를 재실행했다. 실패를 성공으로 소급하지 않는다.

23:43:13 strict는 status warning/summary_handoff PASS/issues0, 같은72행·11차단·미분류0과 sourcehash를 검증했다. machine source `requires_structural_repair`는 계속 남는다. 이것은 canonical handoff 수용과 운영 RED·경제성 미수용이 동시에 존재하는 상태다.

## 마지막 source binding

| Source9/9 | SHA256 |
| --- | --- |
| machine attribution | `3533c0f2be720f2b0180a0f144270a22ddc7aff51b2ad3fc41241c8d4d3373a1` |
| machine timing | `9623b8c8379237e68133561ed47ef0278fda6304f30a4c84cad3950b3b63312a` |
| main Micro | `6b3e7b1b772b602245d4a81d83dbf12cd8482277530ca21b2cc06f6869f3f0ef` |
| WS/scanner | `d763da61a9a5fd4b87bc6ed61ef16fdba2deb0f253314d840cece3ce6c5b9fe1` |
| code workorder | `7e0d3fca903bcca14f3883b19e172006cb3ee510d12587a28a539047d45df11a` |
| disposition companion | `0887c3eb594b16fca1693c93bef59da2efd3b1c56805e534e939ae60a847fa54` |

## 체크리스트 전수 대사

23:43:49에9/9현재OPEN14개를 실제Due/Window와대사해 각기존ID에 결과를추가했다.13개는 provenance/수리와남은자연·경제성·운영차단을분리한`overdue_unresolved`, `ScannerLookupAttentionCalendarMaintenance1002`는10/2 `not_yet_due`다. 미분류0이며 이전완료6개는 재실행하지않았다. 별도승인9/10실행은 `WidgetEpisodeApprovedNextDayExecution0910`에두고 예약/PID/자연수용을분리한다. print-only parser44/unique44 PASS, 외부sync미실행.

## 최종 운영 판정 — RED

| Owner | Target | Latest state | First failure | Repair / validation | Latest terminal |
| --- | --- | --- | --- | --- | --- |
| EOD |9/9|done_warning|OHLC59 제외|기존2701/2760 완료 receipt 보존, 재실행 없음|20:55:48 DONE|
| Main postclose |9/9|succeeded|22:06 workorder 권한 필드 누락|앞선 안전 수리·tail 성공, 이번 영향 source/consumer만 갱신|22:13:08 succeeded|
| Final verifier |9/9|warning / summary PASS|이전세대 handoff|current72행/companion/source hash 일치·issues0|23:44:49 exit0|
| DONE controller/follower |9/9|blocked_structural_contract_gap / follower done|machine18/eligible0|마지막epoch 수리·재생성 후에도 exact BBO/owner gap 유지, 계약 완화 없음|controller23:44:50 exit1; follower22:25:46 기존 terminal|
| Tuning monitoring |9/9|success|없음|검증 archive 및 기존 step0 보존|22:18:52 DONE|
| Dashboard archive |9/9|done|없음|기존 verified receipt 보존|20:50:11 DONE|
| Widget evaluation |9/9|success|없음|4 producer 동일source;080220 next-day policy verified/3holdout 거절|22:11:40 service success|
| Episode recommendations |9/9→9/10|부분 구현·예약 완료|일부calibration/ordered source gap|별도 승인5건 검증·신규3의6timer, 기존guard/legacy custody 보존|23:17 설치;23:43 재확인·현재PID0|
| Machine final refresh |9/9|producer done / source blocked|actual18/eligible0,owner invalid6|attribution→weakness→timing/approval 재생성,9/10 scopes0 baseline carry|원service22:25:34;보완report23:00~23:17|
| Finalization/error detector |9/9|FAIL / detector 실행DONE·severity fail|controller 구조 차단 및23:20 hard deadline|23:46:06 최소 확인 재실행, deadline을 연장하지 않음. cleanup 미실행/삭제0, detector mutation0|23:46:06 finalization exit1;23:46:08 detector DONE|

finalization은 `same_date_hard_deadline`으로 실패했고 기존 bounded detector를 실행했다. detector run `cron-20260909T234606-962465`, target9/9, timestamp23:46:07, summary_severity=fail, operational_mutation_count=0이다. 이 실패보다 오래된 DONE을 최종 정상으로 재사용하지 않는다. 동일 원천으로 main/Provider/기계 전체를 반복하거나 deadline·source gate를 완화하지 않았다. 현재 실행 중인 본 작업의 장후 worker는 없다.

Main drought는 동일as-of19:20:05에서 KRX terminal1111=UPSTREAM654+LATENCY320+AI재검증101+PRICE36, NXT_AFTERMARKET225=175+26+12+12다. broker terminal과 accepted submit은 둘 다0이다. stage별 AI/budget/latency 수(KRX361/549/105,NXT60/75/12)는 서로 다른 stage 관측 분모라 단일 연속 funnel 비율로 나누지 않는다. 뒤에서 회복된 veto/비차단 관찰은 terminal 합계에서 분리됐다. next recheck는 최근3거래일 중9/7 구schema 원천 gap으로 activation=false/stop=true이며 강제 ON하지 않는다. actual submit 회복과 비용 후 순익 개선 모두 미입증, headline 비용 미대사는 null을 유지한다.

진입판단은 원래 signal/확인 횟수, micro0/1/3/5초, 주문집행, full/partial·terminal·실제 비용을 별도 유지한다. 오늘4군35cohort의 유효paired0과 공통 kernel·창 계산 검증 완료는 별개다. adaptive-exit 최초 numeric envelope/launcher/validator·enrollment는 미완료이며 연구162scope/30row를 실체결 pair나 승인값으로 쓰지 않는다.

다음 안전한 확인은9/10 07:32 기존symbol-owner 자동 적용,08:40~09:00 승인정책/preflight 대사, 각 원래timer 시각의 정상 기동·신호/custody·terminal/비용이다. 내일의 새로운 원천은 내일 acceptance이며 오늘 미수집 BBO/과거 manual timestamp를 복원한 것으로 바꾸지 않는다. RED 해소·11요청 전체 구현·내일 실제 거래 또는 이익을 완료했다고 보고하지 않는다.
