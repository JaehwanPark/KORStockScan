# 2026-09-08 08:50 종료 장중 모니터링

- 대상일: 2026-09-08 KST. 전일 장후 source date: 2026-09-07.
- 관찰: 08:16:41부터 요청 종료시각 08:50까지 지속 점검. 마지막 종료 snapshot/검증: 08:50:23 KST. 지정 모니터링을 종료했다.
- 최종 판정: **YELLOW**. 관측 운용 장애 없음, 보고 결함 1건 수리·검증 완료. source-quality·exact venue/AI 자연 원천·경제성 및 이후 예약 acceptance는 미완료다.
- 범위: main / widget / Samsung·저가주 독립 owner, 공통 source-quality와 process. 실주문·취소·재기동·env/threshold/provider 변경을 수동 실행하지 않았다.

## 종료 snapshot

시계열은 [읽기 전용 관찰 snapshot](./2026-09-08-preopen-intraday-monitoring-0850-snapshots.json)에 보존했다. 아래 값은 이벤트 누적치이며 고유 거래/기회 수로 재해석하지 않는다.

| 영역 | 08:50 종료 판정·근거 | 남은 경계 |
| --- | --- | --- |
| Main | PID20318, main heartbeat08:50:20, scanner08:49:22 alive. official read-only env verifier08:50:23 PASS, findings/missing/mismatch0 | 실현손익 null; 경제성 성공 아님 |
| Scanner | promotion151/attach151, fast-precheck3761(고유 promotion 등135), heavy1303(고유119). budget pass28, latency block23, submitted0 | 반복 사건과 episode 분모 분리. 독립 NXT와 PREMARKET_KRX_LIKE의 causal recall은 미확정 |
| Prune observer | prune3386; schedule464 = 신규16+재사용24+capacity412+anchor delay12. observation156 = captured152+shared budget defer4 | local8/80/1200·0.25초와 공통 조회5/s/source-only4/s 유지. 16 episode 표본을 full prune EV로 외삽하지 않음. resolved/95%coverage/right-censor20% floor 미승인 |
| Widget | PID21846, NRestarts0, last cycle08:50:06, 당일 신규 order0 | 080220 collector08:57 및 자연 신호 이후 acceptance |
| Samsung 오전 | PID21391, NRestarts0, 신규 두 leg SOR PLANNED/position0, NXT 원주문2 terminal·filled0 | 09시 SOR 창 대기. 상위 BUY_OPEN을 미체결 실잔량으로 세지 않음 |
| Low-price | 기존 exact-date inventory56/eligible53/quarantine3, 신규3 예약 설치 검증 | 각 preflight/live 이후 확인; 현재 PID53개라고 주장하지 않음 |
| Micro | 0B callback193245→accepted115917; 0D callback171452→accepted123461. trade/depth writer 모두2 alive; queue/drop/writer error0, stop=false | stale0B77328, depth timestamp47968 제외. 마지막 depth3건 추가: 08:50:00 수신 표본은 exchange→receive14393ms/검사3ms. 과거 제외·Provider hold 유지 |
| Limit-down | 당일 load PASS, candidate/slot0, source-only, active live policy 없음 | 정상 자연 대상 부재; ordered-path 성공 아님 |
| AI/R0–R3·smoothing | 설정/PID와 자연 Provider payload·판단/holding 효과 분리 | 이번 창에서 호출·holding/terminal 경제성 미입증, 과거 metadata terminal로 대체하지 않음 |
| 공통 process/퇴역 | 최신 detector PASS, 7 detector 확인; trade restart0. retirement canonical15 OFF 일치 | 정상 실행 lock은 보존. reviewed OFF/Swing·비우선 sim에 새 shortage 없음 |

마지막 관찰 micro callback p95/p99는 0.118/0.585ms, free-disk 관측 최저 약11.14GB로 5GiB low watermark보다 높다. 초기 source timestamp 결손은 있었지만 08:18 이후 정상 원천 유입은 계속됐다. source와 economics 경고가 있으므로 전체 GREEN을 주장하지 않는다. 별도 승인 추천의 기존 원본65행과 projection26행을 합산하거나 미승인 연구 후보를 실전 확대한 조치는 없다.

## 확인된 수리

`market_opportunity_census.build_report`가 설치된 08시 NXT-only 수집 구간에서도 KRX의 미수집을 전역 cadence 실패에 포함했다. 08:18 진단은 NXT 각 panel 4회, 최대 간격 299.94초로 자체 floor를 통과했지만 빈 KRX 때문에 `capture_cadence_floor_not_met`였다.

- `src/engine/monitoring/market_opportunity_census.py`: `required_in_observed_window`로 실제 snapshot watermark에서 예정된 venue/session만 전역 cadence 분모에 포함한다. KRX 개별 floor는 false를 유지한다. 09시 이후 기대되지만 없는 KRX/NXT 세션은 계속 실패하며 빈 전체 source도 PASS가 아니다. snapshot 기준 판정이며 현재 시각의 source freshness를 대체하지 않는다.
- `src/tests/test_market_opportunity_census.py`: NXT-only 장전, 정규장 시작 후 KRX 결손, 전체 source 부재의 회귀 검증을 추가했다.
- 검증: 관련 pytest 56 passed, 두 Python compile, `git diff --check` PASS. producer·설치 wrapper·report consumer의 예정 구간/권한을 재리뷰했다. 검토한 수정 범위의 unresolved finding 0.
- 영향 확인: 08:23 읽기 전용 계산에서 NXT 5회 cadence PASS, KRX `required_in_observed_window=false`; 오탐 blocker 제거. 실제 recall과 경제성은 다른 gate로 계속 차단됐다. canonical report는 덮어쓰지 않았으며 자연 consumer는 09:15 예약 report다. 이 수리는 bot PID 재기동을 요구하지 않는다.

## 관찰 근거와 경계

- Main PID 20318 / 07:55:01 시작, widget PID 21846 / 07:58:00, Samsung 오전 PID 21391 / 07:57:20. 당일 runtime verify는 PID 20318에 PASS, missing/mismatch 0. 이후 다른 작업의 디스크 코드 변경을 이 PID의 소비 증거로 사용하지 않는다.
- 9/7 strict verifier 9/8 00:27:43 warning·summary handoff PASS, controller DONE. 08:24 읽기 전용 `verify_summary_handoff`에서 실제 tower/checklist source hash PASS. 기존 9/7 cleanup/detector 종결시각은 기존 복구 리뷰를 따르며 이번 실행에서 새로 수행하지 않았다.
- Samsung NXT 0000060/0000063은 각 10주 미체결 후 08:10:01 취소(0002448/0002450), 08:10:04 exact owner terminal과 SOR fallback 대기로 전환했다. 취소는 기존 기계가 수행했다. PLANNED SOR leg, position 0이며 상위 `BUY_OPEN` 문자열을 실제 미체결 잔량으로 오인하지 않는다.
- Widget 080220는 당일 정책과 시작 receipt가 있고 KRX 전용이다. collector 08:57은 이번 종료시각 이후다. 이전 state의 unmanaged quantity는 broker 현재 잔고가 아니며 별도 owner 대사 없이 실보유로 합산하지 않는다.
- 저가주 56 inventory / 53 eligible / 기존 quarantine 3. eligible은 PID 수가 아니다. 신규 TYM 09:05/09:09, NHN 13:25/13:29, SD Biosensor 14:10/14:14는 아직 예약 전이다. 기존 적용 acceptance owner를 유지한다.
- Main의 `PREMARKET_KRX_LIKE` 승격·평가와 외부 census의 `NXT_PREMARKET`을 cross-venue 성공으로 합치지 않는다. 08:23 primary NXT liquid-common top20의 unique episode 31, exact source-seen/promotion 0은 해당 scope의 결손이며 main 전체가 31종목을 미발견했다는 증거는 아니다. full-market 전체 분모나 실체결 수익기회로 외삽하지 않는다.
- micro canary는 source row exclusion을 가진 정상 수집 상태. 08:20 timestamp rejection 예시는 exchange→receive 10,202ms, receive→검사 4ms; 마지막 rejection 08:18:37 이후 08:25까지 누적 stale 77,328이 증가하지 않고 유효 수집은 증가했다. callback 이후 writer 장애는 관측되지 않았다. 수신 이전의 외부/내부 원인은 미확정이며 과거 exclusion은 복원하지 않는다.

## 남은 확인 owner

아래 shortage는 코드 결함 또는 경제성 실패와 동의어가 아니다. floor 없는 경로에 임의의 양수 EV·실체결 요구를 추가하지 않는다.

| shortage_id | 분모·required/current/deficit | 최초 결손·분류 | 다음 trigger / acceptance owner |
| --- | --- | --- | --- |
| `scanner-external-nxt-premarket-20260908` | 08:34 NXT liquid-common top20 unique episode33; BBO coverage96.97%>=95%; resolved20/20; right-censored10, ceiling20% 초과 | source-scope exact scanner join0; economic terminal censoring. `blocked_missing_evidence`; 미래 표본 유입만으로 현재 censoring/venue 결손이 닫힌다고 가정하지 않아 finite ETA 없음 | 09:15 자연 report, exact venue/session source·fresh BBO와 terminal 분모 재검증. `ScannerPremarketCensusNaturalAcceptance0908`는 cadence 수리만 소유하며 경제성/recall 성공을 승인하지 않음 |
| `main-provider-premarket-20260908` | qualified provider-required exact attempt 분모 미확정; AI trace0. 단순 heavy 반복 횟수는 provider-required 분모가 아님 | heavy WATCHING→Entry trace 사이의 eligible 조건/종결 근거 확인 필요. `blocked_missing_evidence`, 유입률을 임의 산출하지 않아 ETA 없음 | 기존 `RuntimeEnvIntradayObserve0908`·`EntryRecheckNaturalAttribution0907`에서 qualifying attempt와 명시적 pre-AI blocker/호출 receipt 연결 |
| `micro-timestamp-source-20260908` | callback별 timestamp 계약; stale 0B77,328·depth timestamp47,965 제외, exact rejected-row exclusion 증거 미완료. 양수 EV floor 아님 | before enqueue timestamp source. 새 유효 입력은 회복했으나 과거 제외 원천을 복원하지 않음. `blocked_missing_evidence` | `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`: exact exclusion 또는 다음 clean source와 close까지 연속성; Provider replay hold 유지 |
| `machine-exact-route-20260908` | 26 selected registration item 각각 required 0B+0D. 08:44 양 type11 / 0B-only8 / 미수신7; 이는 eligible signal floor와 별도 | 등록→exact type receipt. 예정 전 KRX와 actual NXT source gap을 구분; 전체 floor 해소는 `blocked_missing_evidence` | 기존 `PostcloseRecoverySourceAcceptance0908`와 machine timing owner에서 route/epoch/ordered 신규 source. `_AL`을 `_NX`로 합치거나 전일 ingress 재실행으로 닫지 않음 |
| `widget-episode-natural-window-20260908` | widget080220 collector08:57, 신규 low-price 각 preflight/live window. 주문/청산 floor를 예약 전 추가하지 않음 | `pending_declared_window` | 기존 `WidgetEpisodeRecommendationApplyAcceptance0908`, 08:57~14:45의 exact policy/PID/signal/custody |

Limit-down은 당일 manager load와 active candidate/slot0이 확인된 정상 자연 대상 부재다. 새로운 economic shortage를 만들지 않는다. Retired/OFF/비우선 sim은 `not_applicable_retired_or_deprioritized`이며 표본 수집 owner를 만들지 않았다.

## 추가 검증

- 08:41 `verify_runtime_env_handoff('2026-09-08', pid=20318)` 읽기 전용 재실행: PASS, missing/mismatch0, policy/dated override fail0, unverified selected0, findings0. 장전 env byte hash `f529bb62dd1c75579d2506017d479629aa41595b648805f3b4954795800ee6bc` 유지. env 파일 단독과 PID의 14개 차이는 operator/dated/launcher 적용 우선순위를 무시한 비교이므로 결함으로 세지 않았다.
- 멀티타임프레임 context: PID의 당일 entry/holding/공통 context ON, 기존 7/29 `promoted_all_market_sessions_full` PASS receipt 확인. 새 승격이나 endpoint별 추가 gate를 만들지 않았다. 자연 AI payload/Provider/판단·PnL 효과는 이번 무호출 창에서 미검증이다.
- main은 08:38 기준 147 promotion ID/101 symbol, 모두 PREMARKET_KRX_LIKE; fast-precheck pass1915를 포함한 반복 사건과 heavy WATCHING794건은 unique opportunity episode 분모가 아니다. latency 차단23건은 spread caution17/too-wide6으로 분리했다. 실제 미체결·probe/residual/scale-in/holding/exit/부분익절·smoothing 효과는 신규 main fill/terminal 부재로 미평가이며 손익은 null이다.
- risky micro는 source-only candidate/BBO 관찰을 계속 생성한다. ask depletion/refill/trade backing의 mature exact outcome·passive fill·tail loss 또는 전체 모집단 EV 성공은 이번 점검에서 재계산하지 않았다. 생성 건수와 실현 수익을 합산하지 않는다.
- 실제 조회를 추가하지 않고 기존 broker reconciliation state/order-owner registry를 사용했다. 삼성 원주문 terminal2와 해당 owner cancel2가 연결되고 filled0이다. 위젯 이전 unmanaged carry는 현재 broker 전체 inventory로 대사되지 않았으므로 계좌 전체 무보유·완전 대사를 주장하지 않는다.
- 문서 parser PASS; 신규 census owner와 기존 micro continuity owner는 당일 출력에 각각 1회. 외부 sync/token 조회 없음. 다른 세션의 수정은 보존했다. 이 gate는 census 수정·테스트·본 관찰 문서 범위이며 저장소 전체 무결함 판정이 아니다.

- `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`: 08:40~08:45 disk·writer·queue·새 clean window 및 exact exclusion/Provider hold. 수집 개선은 과거 결손이나 경제성 완료가 아니다.
- `ScannerPremarketCensusNaturalAcceptance0908`: 09:15 자연 report가 수정된 예정 구간 분모를 소비하고 due 결손을 계속 차단하는지 확인한다.
- `ThresholdEnvAutoApplyPreopen0908`, `EntryRecheckNaturalAttribution0907`, `ScannerLookupAttentionNaturalEvidence0908`, `AIDecisionActionOutcomeNaturalEvidence0908`, `WidgetEpisodeRecommendationApplyAcceptance0908`: 기존 당일 checklist의 각 scope/시간창과 acceptance를 유지한다.
