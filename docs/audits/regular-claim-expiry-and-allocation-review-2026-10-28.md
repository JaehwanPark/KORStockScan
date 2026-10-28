# 정규장 claim 만료 원인·최초/재관찰 배분 수리 리뷰 — 2026-10-28

## 결정과 경계

만료 오표시는 기존 AI 입력 preflight·trace에서 수리하고, 배정 순위 입력은 기존 bounded admission delta에 보완한다. 운영 배분 `current`, 5슬롯, 필수 입력 창·체류·재시도 due, 원5초와 별도1,200ms, source/route/epoch·계좌/주문/수량/custody 안전은 유지한다. 사용자 지시 범위는 검증된 배포본 준비이며 selector publication·hold/drain·Main 재기동·정책 선택·provider/주문은 실행하지 않는다.

원 사고는 `770b2607888f09ebd62816dc109c9955bcbc497a`/PID3510901/start80028883,11:49~12:00:39 동결이다. 구현 중 별도 RFHIC 배포를 확인하고 최신 선택 `d0790117a3b224edde4c1b8e3809417299726d7d` 위로 수리를 재배치했다. 이 둘과 후보의 PID/commit을 혼합하지 않는다. 다른 세션의 preclaim market/source 의미 수리 `9be6a91a7`는 별도 후보이며 이 분기에 파일 전체를 덮어쓰지 않았다.

## 원인과 비교

독립 KRX/KRX_REGULAR 패널의16종목은 원 상승 창 동안 SOR eligible_due가3~6회 관측됐으나 해당 PID의 probe가 없었다. 최초 관찰 대기8개(239610·067920·150900·053350·184230·226950·170790·192250), 이전 PID 관찰 뒤 재관찰 대기8개(411080·179880·053800·042510·434480·158430·072950·178320)다. 실제 fixed active5와 원 master SHA를 대사했다. 물리 종료21→다음 claim 중앙101ms/max152ms라 이미 배포된 반환 wake 수리는 유지한다. 26개 claim은 모두 최초이고 재관찰0, 적격 대기335/관측 최대665.906초, 체류 중앙149.968초다. 이는 연속 적격시간 또는 시장 전체 분모가 아니다.

현재 activity와 age-turn 모두 never-tested를 revisit 앞에 둔다. fresh 신규가 계속 오면 revisit이 밀릴 구조를 기존 native queue로 재현했다. 이미 존재하는 Q1 eligible_wait·Q2 service_wait를 재사용했다. 동결 queue를 그대로 둔 실제5슬롯 점유 control은 추가 claim0이다. 원 점유5종목을 제외한 **조건부 5슬롯 첫 batch**에서는 Q0/Q1/Q2 모두 최초5·재관찰0·16종목 선택0이다. 복원한 eligible clock은 그 dispatch에서 새로 시작하며 first_seen으로 과거 대기를 만들지 않았다. 별도 같은 입력의 age-turn 재현은 Q0/Q1 최초1, Q2 재관찰1이다. 이것은 과거 lease 시간표나 포착 개선의 증명이 아니다.

당시 admission delta에는 volume/source_kind/first_seen/last_claim/eligible_since/long-deferred가 없어 정확한 과거 전체 순위 재생이 불가능하다. 미구독16종목의 실행호가·기계 결과도 없으므로 추가 WIN/STOP/TIMEOUT은 각각 null, U16이다. 현재 source28은 미봉인이므로 적격 누적 비교·운영 Q/R 선택에 쓰지 않는다. [동결 실제 분모](../../tmp/regular-machine-coverage-20261028/1201/rising-admission-join.json), [조건부 native 배분 비교](../../tmp/regular-claim-expiry-20261028/allocation-comparison.json).

삼성 exact signal `005930:1793155776330505:5492`는12:00:30.411839 확인→첫 방문29.981ms, extreme_sell_dominant가32.397789까지11회 관측되고32.649312 해제됐다. 이후 앞선 native 요청들의 async 평가·만료·정리를 순차 처리했다.32.695/33.436/34.504 dispatch의 원 deadline은 각각33.212/34.320/34.512954이며,34.716 dispatch가 exact5492/deadline35.411839다. `reversal_extended_runtime.claim_snapshot`은 유효 ready를 epoch/sequence 오름차순 선택하고 기존 물리 작업을 중복하지 않는다. 이 serial backlog와 guard가 late claim의 확인된 경로다. 세부 CPU/네트워크 비용을 서로 겹치는 interval로 합산하지 않는다.

5492 claim은 확인+4.289초, 잔여0.711초다. 이후 준비 대기13.724ms/서비스45.229ms, coordinator evaluate0.666초와 Main guard8.949ms로 원 기한을 넘었다. 이는 provider 응답 지연이 아니며 해당7 trace의 provider 호출0이다. exact 입력 고정 refresh81.591ms, 정책 resolve62.149ms 등은 중첩을 구분한다.5분 동일 SOR 호가의 최고 bid239,500/원 ask240,000, 비교 비용0.23% 후 최고−0.43833%로 이 신호를 확정 놓친 수익이라 부르지 않는다.30분 WIN/STOP/TIMEOUT·실현손익은 null이다. [원 시계/호가](../../tmp/regular-machine-coverage-20261028/1201/samsung-exact-signal-diagnostic.json).

## 구현·리뷰·교체

- `consolidated`: `_final_entry_machine_inputs`의 정확한 deadline_expired를 같은 `analyze_target` preflight에서 보존하고 primary category를 freshness_or_timing으로 전달한다. 일반 refresh_failed로 덮는 분기는 만료에 대해 removed다. 다른/unknown 오류와 동반 stale/source blockers는 유지하며 DROP·provider false·주문 금지를 바꾸지 않는다.
- `consolidated`: 기존 trace와 compact final response allowlist에 exact error·source gap kind를 보존한다. 기존 submission monitor가 이를 소비한다. 캡처된 preflight를 legacy uncaptured deadline guard로 우회하지 않는다. 역사적 원 trace/캡슐은 retained다.
- `consolidated`: 기존 runtime admission delta에 preclaim rank scalars를 추가한다. 실제 abandon 뒤/claim 전 값을 보존하고 claimed row의 postclaim count와 구분한다. 기존 MAX_ROWS·성공 append 뒤 checkpoint·실패 재시도·dispatch_samples_only를 유지한다. 새 queue/worker/원장/validator/모듈은 없다. 원 기록이 완전한 전체 배정 재생을 보장한다고 표시하지 않는다.
- `retained`: 현 queue/lease/selector/registered pattern·정책 cache·copy isolation·RFHIC BUY lineage/SELL 및 manual/retired 경계. 공통 ai_market_snapshot 분류기 수정은 이 수리에 불필요하여 리뷰 중 제거했다. 기존 category를 producer가 직접 정확히 기록하므로 공유 holding producer를 바꿀 이유가 없다.
- `deferred`: Q1/Q2/R1 운영 채택과 추가 포착·STOP/TIMEOUT 효과. 기존 두 OPEN owner가 source28 봉인 후 같은 적격 입력·실패·U를 함께 비교한다. 서로 다른 lease/epoch를 잇거나 미관측 가격을 보간하지 않는다.

native handoff는 전체 d079 predecessor profile을 상속하고 실제 변경 engine/trace/runtime와 독립 preparation reader를 결속한다. 기존 registry와 실제 delay/stop/holding issuing readers, report capability dispatches, 독립 P5, live observer/health를 하나의 소비자 inventory로 관리한다. 이전 profile은 retained다. exact candidate 성공과 missing/dirty/mixed/new generation 음성, 실제 issued d079 predecessor 성공을 검증하며 report-only 진단을 새 startup gate로 만들지 않는다.

## 검증과 남은 수용

원 오표시3개 캡슐은 canonical SHA·PID/start를 검증하고 exact final-freeze fields를 실제 analyze_target/preflight/trace에 재생했다. 모두 정확한 만료 사유와 같은 차단 동작을 확인했다. 최초 잘못된 fixture name, 공유 분류기 변경의 불필요한 holding 영향, offline queue restore가 물리 lease를 닫는 의미, master directory 누락 invocation은 원 실패로 보존하고 수리/비교 범위를 정정했다. 정상 데이터·원 receipt를 고쳐 시험을 통과시키지 않았다.

production/trace/monitor 대상2,000 PASS, 독립 준비1,053 PASS 및 final changed-pair 재확인, 완전 후보/음성·issued predecessor63 PASS, queue/runtime93 PASS, exact 회귀33 PASS. compile·diff와 문서 link/owner·print-only parser를 확인한다. 상세 [증거 디렉터리](../../tmp/regular-claim-expiry-20261028/)의 원 실패·최종 로그를 유지한다. candidate/native parity·보고서 capability·isolated P5 결과는 그 디렉터리의 최종 인계로 기록한다. 후보 PASS와 실제 배포/PID/자연수용·경제성은 별개다.

자연 수용은 `MainEntrySourceTerminalRepair1022`와 `MachinePatternOpportunityResearch1023`의10/28 REGULAR13:30~14:00, source28 장후20:05~23:59 및10/29 PRE08:05~08:20/REGULAR09:05~09:25를 따른다. 실제 후속 승인·배포된 PID/start/cwd/동일 정책의 REGULAR SOR/_AL에서 정확한 만료 trace가 일반 refresh/source 손실로 덮이지 않고 새 source loss는 계속 검출되는지 확인한다. rank는 claim 전 count/clock·당시 source/master와 일치해야 한다. 정규장 수용을 PRE/AFTER·다른 route로 닫지 않는다. 이번 준비가 자동 배포/미래 실행을 예약하지 않는다.

## 최종 준비 인계 — 2026-10-28 13:00 KST

후보는 `27d4a000c6e47e65a693ab1d8a428be6280905c7`, 경로는 `/home/ubuntu/KORStockScan-runtime-releases/regular-claim-expiry-20261028-27d4a000c`다. 최신 선택 d079/PID3661403/start80241527과 분리한 미선택 준비본이며 live 전환은 없다. 원 active policy parity128scope/76,800행/569signal·신호 SHA 일치, delay/stop/holding/active-policy native 검증과4개 report capability 재검증을 완료했다. [동일 정책 native 영수증](../../tmp/regular-claim-expiry-20261028/active-parent-handoff-issuance.json), [격리 P5](../../tmp/regular-claim-expiry-20261028/candidate-p5-reference.json), [최종 native P5 reader](../../tmp/regular-claim-expiry-20261028/final-native-p5-reader.json).

격리 P5 `3b201585e9a7405dbc2cdbfe25625974`는12소비자 로딩PASS·자식 종료·보호 원본 불변·findings0이며 runtime_effect/actual_pid_consumed false다. P5가 소비한 원 정책/준비 입력은 보존한다. 그 뒤 생성한 보고 전용 trailing currentness는 별도 native 최종 보고 reader로 검증하여 수용 역할을 구분한다. P5를 실제 Main/PID 소비나 제출 성과로 바꾸지 않는다.

최종 소비자 리뷰에서 별도 trailing `CODE_PATHS`의 AI/trace 결속을 발견하여 기존 inventory를40개 소비자로 확장했다. report-only registry4개만으로 전체 인계를 완결했다고 하지 않았다. 원 source27 계산·holding/PREOPEN/정책/selector는 보존하고, 기존 normalized reuse/체크포인트에서2,901개·684,412,384byte를 두 batch로 검증해 새 보고 세대/currentness만 발행했다. 원512MiB 한도/32MiB 미증명 원천 한도를 늘리지 않았다. 후반 native 전체 검증293.518초, 검증 full reads20,105,157byte·증명 재사용37,788,252,375byte, peak RSS193,696KiB다. 잠금 대기와 첫 copy 시간은 별도 미계측이며 총 실행시간으로 꾸미지 않는다. 신규 정책 선택/semantic verdict cache reuse0, 원 경제성 결손은 유지한다. [의존 disposition](../../tmp/regular-claim-expiry-20261028/trailing-dependency-disposition.json), [두 번째 batch·원본 보존](../../tmp/regular-claim-expiry-20261028/trailing-write-batch2-preservation.json), [최종 후보 소비자 검증](../../tmp/regular-claim-expiry-20261028/candidate-native-contracts-final.json).

기준 d079→후보의 non-test source +102/−2(net100), tests +174/−21(net153), 후보 audit +37/−0이다. 이후 canonical checklist/audit의 인계 기록은 이 코드 통계와 분리한다. 증가분은 기존 생산자/trace에 정확한 원인·rank evidence를 보존하고 complete/independent intake를 검증하기 위한 것으로, 모듈/worker/실행 entrypoint 추가0·이동0이다. [리뷰·검증과 교체 disposition](../../tmp/regular-claim-expiry-20261028/review-and-validation-summary.json), [같은 전체 소비자 목록](../../tmp/regular-claim-expiry-20261028/change-consumer-inventory-reviewed.json).

5슬롯·원 체류/due·5초/1,200ms·안전은 그대로이며 Q1/Q2/R1 운영 적용0이다. 기존 두 OPEN의 정확한 REGULAR SOR/_AL 자연 수용과 source28 봉인 후 추가 W/STOP/TIMEOUT/U 비교는 남는다. 배포 후 실제 새 PID가 수정 branch를 행사해야 런타임 해소로 닫을 수 있다. 배포 승인 전 selector/hold/drain/start/주문을 실행하지 않았다.

<a id="late-observation-anchor-20261028"></a>
## 늦은 배정·첫 유효가격과 패턴 불일치 — 2026-10-28

결론은 **관찰 시점의 편향과 선택 패턴의 좁은 포착 범위가 함께 존재하나, 기준가격 저장·복원 결함은 이번 원본에서 확인되지 않았다**는 것이다. 기준가격 재설정/단일 조건 변경만으로 추가 포착이 생기지 않았으며, 기존 상승지속 후보는 추가 WIN과 함께 TIMEOUT도 늘었다. 운영 배분·패턴·안전 기준을 변경하지 않는다. 신규 소스 수리 조건이 성립하지 않아 이 연구를 위한 별도 배포본을 만들지 않는다. 기존27d4a000c의 claim 전 rank 보존·만료 사유 수리, 별도7022d9972의 Q1/Q2 dispatch 연결은 이미 준비된 작업으로 유지하며 중복 구현하지 않는다.

### 동결 원본과 실제 소비자

13:00:13 동결은 d0790117a/PID3661403/start80241527, REGULAR·일반종목 정책 cohort·`symbol_AL` SOR 시장자료·통합 경로 큐다. 실제 거래소 체결 venue는 이 자료로 식별하지 않는다. 정책 bundle4abcce10/family8a10f096을 그대로 사용했다. 13:44:24 재핀에서도 selector d079·실제 PID3661403/cwd가 유지됐다. 통계는13:00 동결에 대한 것으로 최신 전체 장중 통계라고 하지 않는다.

원 관찰75lease 중 native receipt63개를 exact lease/native epoch/sequence로 연결했다. 95종목을 대상으로 원 market stream212,659,065byte를16MiB 이하13청크로 한 번 읽어19,139행을 투영했다(3.112초). 청크/행 offset·길이·원문 SHA·inode·동결 끝을 보존하며 이후 실험은 투영본만 재사용한다. 당일 미봉인 자료는 인과 진단용이며 적격 장후 승격 자료가 아니다. [입력·코드·실험·실패 원본](../../tmp/late-observation-anchor-20261028/).

최초 재생에서 나온 dd2건 차이는 임시 연구 reader가 rolling 진단값을 우선한 오류였다. 실제 소비자의 `actual_branch_confirmation → same-row rolling` 순서를 적용한 뒤 종단 특징값 차이0, native 최종 epoch/sequence 차이0이다. 최초 실패 result/script를 `*-v1`로 보존했다. 원 native 생산자/정책을 고쳐 연구값에 맞추지 않았다.

61lease의 branch별 TRUE/FALSE/UNKNOWN 누적 횟수는 원 receipt와 정확히 일치한다. 나머지2lease(047810·488280)는 보존 stream에서 native sequence 각각1개가 없고 원 UNKNOWN이 각각1개 많다. 같은 PID/item/시각 구간의 0B timestamp rejection 각1개가 원 수집기 거절 원장에 있으며 거래소→packet 지연12,311/10,392ms, packet→normalization0ms였다. 이는 수집 전10,000ms 거절과 일치하는 정황이나 거절 원장에 해당 native sequence/가격이 없어 exact 행을 복원하지 않는다. 두 lease는 비교에서 제외하고 source/현재성 차단을 유지한다. 정상 입력 패턴 불일치30lease는 제외되지 않았다. [정확 재생](../../tmp/late-observation-anchor-20261028/baseline-replay.json), [거절 원본 대사](../../tmp/late-observation-anchor-20261028/rejection-join.json).

### 기준가격이 미치는 영향

실제 생산자는 같은 종목·venue·item·시장 세션·날짜의 **첫 유효 관측 체결가**를 보존한다. 재관찰/재기동 때 다시 잡지 않으며 전일 종가·장 시작가·KRX 분봉으로 대체하지 않는다. `reversal_path_runtime` 수신→`reversal_anchor_index` 저장/복원→`continuous_reversal_branches`의 `100*(현재가/anchor-1)`→registered `session_trend`가 실제 경로다. adapter의 `int(received_ts*1000)`와 native 소수초를 생산자 정밀도에 맞춰 대사한74개 원 anchor는 가격·epoch·sequence·item이 모두 일치했다.

정상 입력 패턴 불일치30lease 중24개는 해당 관찰에서 처음 anchor가 생겼고6개는 이전 anchor를 유지했다. 따라서 늦게 처음 관찰된 종목은 이미 발생한 상승을 session 수익률에 포함하지 못한다. 반대로 과거 높은 가격을 보존한 재관찰은 단기 반등 중에도 session DOWN일 수 있다. 둘 다 현재 정의의 결과이며 자동 리셋이 수리는 아니다.

- 씨티알모빌리티308170: KRX 패널12:25 4,360→12:35 4,480의 상승 뒤12:55:30에 첫 `_AL` 체결4,450이 관찰됐다. 종단 session0%, ret60 −0.336%, structure MIXED로 G4에 불일치한다. 앞선 상승을 본 뒤 놓친 반등으로 확정할 native 호가/패턴 원천은 없다.
- 디아이003160:10:34 anchor42,950을12:32 재관찰에도 보존했다. 재관찰 첫 체결41,800, 종단 session−2.794%·ret60−0.120%·MIXED였다. G1의 UP 기준은43,121.8 이상이므로 첫 재관찰가 대비 약3.16% 회복이 필요하다. KRX 패널의 주요 회복은12:35 관찰 종료 뒤13:00 42,700까지 나타났다. 실제 관찰 중 패턴 차단과 이후 재관찰 부재를 구분한다.

61개 정확 재생 lease의 실제 등록 반등 확인점은567개(G4 346/G1 165/G2 56)였다. **session 조건만 실패하고 다른 조건이 모두 TRUE인 점은0개**다. G4에서는 spread 상한275·dd 상한239·session247개가 각각 실패했다(중첩 수치). 이는 종단30건의 조건 집계와 다른 분모다. 기준가격을 바꾸기 전에 실제 확인점의 동반 조건을 함께 봐야 한다.

### 동일 입력 비교와 WIN·STOP·TIMEOUT

[사전 고정 실험](../../tmp/late-observation-anchor-20261028/experiment-plan.json)은 원 lease 종료/기한을 유지한다. 첫30/60초를 제거한 실험은 늦게 관찰했을 때의 정보 손실 민감도이며 실제 Q 배분 재생이나 미관찰 과거의 복원이 아니다. 별도 최초 anchor 변경과 retained anchor를 나눴다. 운영 적용·provider·주문0이다.

| 당일61lease 실험 | 추가 확인점 | WIN | STOP | TIMEOUT | 미확정 |
|---|---:|---:|---:|---:|---:|
| 현행 | 0 | 0 | 0 | 0 | 0 |
| lease 첫 가격으로 anchor 리셋(진단만) | 0 | 0 | 0 | 0 | 0 |
| session 조건만 제외(진단만) | 0 | 0 | 0 | 0 | 0 |
| 최초 입력30/60초 지연, anchor 보존/최초 재설정 각각 | 0 | 0 | 0 | 0 | 0 |
| G4 구조에 MIXED 또는 RISING만 추가 | 0 | 0 | 0 | 0 | 0 |
| 현행 + A01(60초 고점 돌파) | 4 | 0 | 0 | 0 | 4 |
| 현행 + A14(상승 구조3초 유지) | 3 | 0 | 0 | 0 | 3 |

A01/A14 모두 원 정의의 spread≤0.1%와 원 source/quote 조건을 유지했다. 추가7점은5종목에서 나왔으며 현재 선택은 그대로다. 같은 실제 lease의 후행 원천은0~68.827초만 남아30분 결과를 판정할 수 없다. 기존 생산자의 보존 REST revision·WS 완료 분봉 reader까지 확인했으나 해당5종목의 동일 `_AL` 완료 원천이 없었다. 다른 item이나 lease를 이어 TIMEOUT/승리를 만들지 않는다. [실험 결과](../../tmp/late-observation-anchor-20261028/experiment-results.json), [native 보존 분봉 소비 결과](../../tmp/late-observation-anchor-20261028/completed-outcome-check.json).

당일 미확정과 별도로, source27까지 기존 적격 공통29,403확인점의 native 비교표/원천 manifest SHA·seal·기존 직접 집계 증명을 재검증·재사용했다. 비용0.23%, 목표 순+0.4%, STOP 순−3%,30분 label은 기존 계약이다. 다음은 현행 G4 대비 **추가** 확인점 결과이며 실제 주문 수나 실현손익이 아니다.

| 기존 누적 후보 | 추가 WIN | 추가 STOP | 추가 TIMEOUT | 추가 미확정 | 조합 WIN/해결 |
|---|---:|---:|---:|---:|---:|
| G4 + A01 | 90 | 0 | 335 | 427 | 94/429 (21.91%) |
| G4 + A14 | 32 | 2 | 87 | 128 | 36/125 (28.80%) |

현행은4/4이며 현재 owner의 선택 지표는 `cumulative_raw_win_fraction`이다. 작은 현행 표본을 전체 기회의 우월성으로 일반화할 수 없지만, 후보의 추가 WIN만으로 현행 선택 지표가 개선됐다고 할 수도 없다. 별도 cluster 진단/미확정과 원 경제성 한계를 보존한다. [봉인 비교와 배분 재사용 증명](../../tmp/late-observation-anchor-20261028/sealed-comparison-and-allocation-reuse.json).

Q0/current·Q1/eligible_wait·Q2/service_wait는 기존12:00 동결의 같은 조건부 첫5개 배정에서 모두 최초5/재관찰0, 미관찰 상승16종목 추가0이었다. 실제5슬롯 점유 control의 추가 배정은0이었다. 이 제한된 비교를 전체 시간축의 동등성으로 일반화하지 않는다. 과거 전체 dispatch의 claim 전 rank/eligible clock과 미구독 가격 경로가 없으므로 세 후보의 추가 WIN/STOP/TIMEOUT은 **null**이다. 신규 적격 시각을 first_seen으로 소급하지 않는다.27d4a000c의 기존 admission delta 보존 수리가 배포·자연 소비된 뒤 같은 owner에서 후속 비교하며, 증명되지 않은 기회 복원 때문에 슬롯·체류·재시도 기한을 늘리지 않는다.

### 리뷰·검증·남은 단계

연구 구현→self review→dd 투영/시각 정밀도 보완→재리뷰→원 receipt 대사와11개 민감도 실험을 마쳤다. 선택 release의 anchor 복원·등록 branch·누적 policy·queue 회귀174 PASS(16.96초), 원본/음성 포함 기존 테스트를 재사용했다. 새 테스트/validator/생산 모듈/worker/entrypoint0이다. 문서 링크·stable owner·print-only parser·diff 검사 결과는 같은 증거 디렉터리에 기록한다.

교체 disposition: 임시 연구의 잘못된 rolling 우선 분기는 **removed**, 진단값 선택은 실제 소비자 순서로 **consolidated**(v1 실패 원본 retained)했다. 실행 anchor·registered 조건·queue·hard safety는 **retained**(현재 소비자 유지), 기존27d4a000c/7022d9972 수리는 **retained**(중복 구현0), Q1/Q2/A01/A14 운영 채택과 후행 label 폐쇄는 **deferred**다. 프로덕션 non-test source/tests 변경0·삭제0·이동0이며 canonical 기준1756de1d9에서 이번 문서 증분만 audit+61/checklist+1·삭제0이다. 기존 dirty 변경은 이 수치에 포함하지 않는다. 이번 연구는 배포/재기동·정책 선택·실제 PID 자연 수용·경제성을 완료했다고 주장하지 않는다.

기존 `MachinePatternOpportunityResearch1023`의10/28 source28 20:05~23:59 봉인/생산자·소비자 수용,10/29 REGULAR09:05~09:25 자연 창에서 새 실제 actor·policy와 claim 전 rank를 결속한다. 당일7개 미확정은 해당 item의 인증된 후행 원천이 있을 때만 다시 판정한다. 현재 자료로 복원 불가능한 과거 미관찰 가격은 null로 유지한다. 동일 branch·route의 새 source loss는 계속 검출한다. 미래 창은 OPEN 인계이며 자동 예약이나 배포 권한이 아니다.

<a id="rank-deployment-and-sealed-recheck-20261028"></a>
## 순위 보존 통합·실제 PID와 장후 재검증 인계 — 2026-10-28 14:00

배포 담당의 기존 승인된 전환을 관찰했다. `27d4a000c`의 순위 보존 수리는 cherry-pick `7611084a8`→통합 `3171f2a92`→기동 검증 수리 `138443c8d`에 포함됐다. 세대 이름만 확인하지 않고 원 수리본·통합317·실제 선택138의 `zero_base_discovery_runtime.py` 전체 Git blob과 물리 파일을 대사했다. 모두 SHA256 `06eb8c05864ab691c86e15b320ae99a19fb782a78899ac70ea79191c64040c9d`로 일치한다. 이 연구 작업이 별도 배포나 재기동을 실행하지 않았다.

13:50에는 d079/PID3661403이었고13:54:41에는138 선택/이전 PID drain,13:59:28에는 native transition complete로 바뀌었다. 전환 중 부재한 `actual_pid_receipt`를 과거 PID 영수증으로 대체하지 않았다. 원 조회 실패는 `integration-transition-first-attempt.json`에 보존하고 상태별 reader로 보완했다.14:00:09에 **PID4183243/start80802539/cwd=`holding-expiry-integrated-20261028-138443c8d/src`**, native `current_pid_consumption_complete`를 확인했다. manifest5c709d4d의 기존 정책 소비이며 다음날 정책/기동이나 경제성 증거가 아니다. 후보 및 선택 후 격리 P5도 각각 `passed/findings=[]`였으며 실제 소비와 구분한다.

REGULAR SOR 통합 경로의 새 PID 자연 admission6개/385행에서 `preclaim_rank_inputs_v1`을385행 모두 확인했다. claimed6·eligible_due362·in_flight9·active_target_deferred7·retry_not_due1행이며 반복 delta를 고유 종목 수로 세지 않는다. claimed6건은 최초4/재관찰2, 배정 전 claim_count→배정 후 count가 모두+1이고 원 due·eligible clock 검증 findings0이다. 예: 디아이003160은2→3, SK스퀘어402340은1→2였다. 운영 allocation은 **current**, 기록된 가용 슬롯은 최대5다. 관측 적격 대기42.777~53.747초는 **재기동 후 새 적격 clock**이며 종전 수십 분 대기의 감소 효과로 비교하지 않는다.4MiB 원 pipeline suffix의 byte offset/길이/SHA를 보존한 표본으로, 전체 dispatch census를 증명하지 않는다. [실제 PID·코드 결속](../../tmp/late-observation-anchor-20261028/integration-140009/identity.json), [자연 rank·claim 검증](../../tmp/late-observation-anchor-20261028/integration-140009/natural-admission-sample.json).

**장후 비교는 아직 실행 완료가 아니다.**14:00 기준 source28의 native source manifest·machine comparison·main_machine_policy terminal이 모두 부재하다. 이는20:05 EOD/20:10 EOD 완료 후 postclose라는 설치 cron/원 owner 이전의 `not_yet_due`다. native calendar의 다음 거래일은10/29다. 기존 PID 종료로 원 연구 collector epoch1793157912919452308은 `closed_main_raw_epoch`로 검증됐지만, 이 사실만으로 source28 전체 봉인·비교 완료를 주장하지 않는다. 장후 wrapper를 조기 실행하거나 새 worker/예약을 만들지 않는다. [준비 상태와 원 epoch](../../tmp/late-observation-anchor-20261028/integration-140009/postclose-readiness.json).

기존 `MachinePatternOpportunityResearch1023`의10/28 20:05~23:59에 source28/target29를 고정하고 다음 순서로 재검증한다. 아직 도래하지 않은 결과는 null/OPEN이다.

1. source28의 종료 epoch·row exclusion·native source/comparison seal·원 정책/코드/원천 hash를 검증한다. 기존 정규 producer와 소비자의 봉인 결과를 재사용하고 변화 없는 전체 raw 재생·provider 호출을 하지 않는다. 별도 장후/배포 담당의 실행과 경쟁하지 않는다.
2. Q0/current·Q1/eligible_wait·Q2/service_wait를 동일 적격 시점·claim sequence·점유5슬롯·최초/재관찰·원 체류·due에서 비교한다. 적격 대기 median/p95/max와 관측 eligible symbol-seconds, 창 끝 미종료 대기를 분리한다. `dispatch_samples_only` delta의 원천·누락/대기 backlog·초기 상태가 전체 재구성을 뒷받침하는 범위만 사용한다.13:58 이후 rank가 배포 전 누락을 소급 복구하지 않는다. 미구독 반사실 가격 경로가 없으면 추가 WIN/STOP/TIMEOUT은 봉인 뒤에도 null이며 관측 가능한 후보/시간 구간만 구분해 보고한다.
3. A01 4건·A14 3건의 원 case ID·native epoch/sequence·lease·확인시각·entry ask·branch를 [7건 고정 입력](../../tmp/late-observation-anchor-20261028/integration-140009/sealed-recheck-inputs.json)에 보존했다.077970/234690/114810/452280의 A01과456010/234690/114810의 A14를 기존 비교 원장의 실제 point/snapshot에 연결한다. 같은 `_AL`의 원 source 또는 봉인된 완료 분봉/개별 REST revision만 후행 label에 사용하고 clock/cutoff/동일 봉 양방향 접촉 ambiguity를 유지한다. 원 특징·기준가격·진입호가를 후행 자료로 바꾸지 않는다. WIN/STOP/TIMEOUT/U를 각각 대사하고7건을 일괄 성숙 완료 처리하지 않는다.

5슬롯·체류·재시도 due·5초·1,200ms·기존 source/가격/주문/custody 안전은 유지하며 Q1/Q2·A01/A14 운영 채택0이다. 새 생산 코드·tests·worker·validator·entrypoint 변경0, 기존 배포본과 native reader는 retained다. 임시 조회의 running-only 가정은 전환 대기 상태와 분리해 consolidated했고 원 실패는 retained다. 소스 미생성에 따른 장후 재검증만 기존 owner에 deferred이며 자동 실행 예약 완료로 표시하지 않는다. 문서/관측 검증은 같은 증거 디렉터리에 기록한다.

<a id="source28-phase-inspection-and-pattern-priority"></a>
## 장후 검증기 전환 수리와 패턴 불일치 우선 분석 — 2026-10-28

사용자가 장후 시작 전 검증기 수리·리뷰·회귀와 source28 봉인 관찰/비교를 지시했다. 기존 임시 `check_integration.py`가 종료된 Main의 `_process_start_ticks`를 무조건 읽는 원인을 수리했다. 실제 종료 PID4183243/start80802539에서 원 predicate의 `runtime_pid_not_running`을 재현했으며, 같은 actor의 native 정상 종료 원천 영수증으로 `stopped_source_closed`를 판정한다. 이 상태는 현재 PID 소비나 source28 전체 봉인이 아니다. PID 영수증 부재·재사용·cwd 상충, 선택 세대 전환과 다음 세션 PID를 구분하고 source date를 CLI에서 명시한다. EOD 선행 대기·native stage의 pending/running/deferred/failed와 발행된 terminal/원천 검증을 분리했다. 장후 발행 원 reader root와 명시적 shared data root로 원 세대와 source/report 물리·의미 해시를 검증하며 봉인 입력 변경은 계속 거부한다.

28개 회귀 PASS, compile 및 실제 source27의 원 발행 reader 성공 intake를 확인했다. source27 검증은 2.82초/381,862,078바이트/73 native full reads이며 원 자료 재계산·재봉인이나 source28 수용은 아니다. 재검증은 생성된 영수증을 재사용하고 같은 무변경 원천을 반복 스캔하지 않는다.14:55:36에는 별도 담당이 배포한 f4cdac806/PID197518의 현재 소비와 rank 표본3개/413행/findings0, source28 `not_yet_due`를 관찰했다. 원138과 f4의 전체 scanner 파일 해시는 다르므로 동일 전체 blob으로 표시하지 않고 선택본의 Git/물리 파일 일치·rank schema와 실제 표본을 확인했다. [수리·리뷰·회귀 근거](../../tmp/late-observation-anchor-20261028/phase-repair/review.json), [원 발행 reader 대사](../../tmp/late-observation-anchor-20261028/phase-repair/native-reader-rehearsal.json).

교체 disposition: 기존 running-only assert와 hour-only readiness는 **removed/consolidated**, 원본 bytes·앞선 결과와 기존 entrypoint는 **retained**다. 명시 source-date CLI와 함수 분리로 임시 source +288/-117, 임시 회귀 파일은 별도 추가했다. 프로덕션 non-test source/tests +0/-0이며 배포·재기동은 필요하지 않은 임시 읽기 도구 수리다. 기존 생산자·소비자·5슬롯·체류·원 retry due·5초·1,200ms·모든 가격/원천/주문 안전과 정책 선택은 **retained**다. source28 봉인·Q0/Q1/Q2 효과·A01/A14 7건의 실제 재검증은 계속 OPEN이며 source27 rehearsal이나 미래 시계 테스트로 닫지 않는다.

사용자는 이어서 패턴 불일치와 그 원인을 최우선으로 지정했다. 원본은 [14:45:52 동결 분석](../../tmp/submit-cause-latest-20261028-1447/144552/analysis.json)과 그 source-window이며,138/PID4183243의13:57:58~14:45:52 종료106건/97종목이다. 선택 신호0·패턴 불일치39·확정 대기2·원천 미준비/stale65,14:45:45의 적격 대기422를 새 f4/PID의 현재 분모로 혼합하지 않는다. 원천/호가 current는 모든 특징·전환 조건 완성을 뜻하지 않는다. 불일치39건에서도 일부 descriptor의 structure 결손이 있으므로 마지막 feature/실제 확인 시점·조건별 FALSE/UNKNOWN·anchor/관찰 지연·hard spread 차단을 함께 분석한다. 정상 조건 차단과 놓친 반등을 실제 lease·branch·source item에 연결하고, 임의 조건 완화 없이 원 결함 수리 또는 등록 후보의 추가 WIN/STOP/TIMEOUT/U를 비교한다. 이 우선순위는 같은 `MachinePatternOpportunityResearch1023`가 소유하며 source28 후속을 취소하거나 새 운영 정책을 승인한 것이 아니다.

원39건/36종목은 최초26·재관찰13, 저가19·중가12·고가8건이다. 이전 원천 checkpoint212,659,065바이트 뒤 append만 기존256MiB 상한 안에서 한 번 동결하고 당시138 코드·선택 정의·원 lease·anchor로 재생했다. **39건 모두 native ID·branch별 TRUE/FALSE/UNKNOWN 횟수·특징값 불일치0, 현행 신호0**이다.13개 재관찰은 원 anchor를 보존하며26개 최초 관찰의 anchor는 해당 lease에서 생겼다. source/quote current인39건 중36건은 종료 특징이 완성됐고3건은 structure가 미완성이다.3건(동화약품000020·메가터치446540·한중엔시에스107640)은 wire→enqueue→native 관측 수가 각각5/7/16으로 일치하며 마지막 특징 시점의 이전30~60초 bucket에 수신된 체결이0개다. 현재 틱/호가가 있어도 두30초 high/low 비교가 완성되지 않는 관측 공백이며, wire 이후의 특징 계산/전달 결함은 확인하지 못했다. 거래소 자체의 거래 공백인지 wire 이전 전달 누락인지는 독립된 동일 item/시간창 체결 원천이 없어 **미확정**이다. 수신 수 일치만으로 거래소 무거래를 증명하지 않는다.

| 실제 선택 branch | 실제 조건 평가 | 주요 불충족 조건(중복 포함) |
| --- | ---: | --- |
| 저가 G4 | 318회/18lease | spread≤0.1 실패264, session UP 실패216, dd<0.4 실패170, FALLING 실패152. 나머지1lease는 FIRST 반등 root 자체가 없음 |
| 중가 G1 | 192회/12lease | session UP124, dd≥0.4 124, RISING99, ret<0 97 |
| 중가 누적 MOMENTUM_HOLD의 원 의존 branch | 실제 hold 확정12개/9lease | dd>0.8가12개 모두 실패, session DOWN9, ret<0.2 5. 이 원 branch는 단순 상승 추종이 아니라 DOWN·MIXED·0.8~1.2 낙폭 반등에 해당 |
| 고가 G2 | 307회/8lease | session DOWN307, dd>0.8 300. session만 단독 불충족인 native 지점은 유진테크084370의1개이며 다른 안전/후행 성과를 증명하지 않음 |

이는 반복 root 평가이며 독립 기회·수익 건수가 아니다. 마지막 prefix 특징만으로 전체 lease의 원인을 추정하지 않고 실제 FIRST/hold 확정의 조건 호출을 원 native 판단과 대사했다. **현재 확인한 우선 원인은 좁은 선택 패턴의 포착 범위**다. G4·G1·G2와 중가의 추가 branch도 특정 눌림·낙폭·session 방향에 묶여 있어 일반적인 상승세를 포착한다는 보장이 없다. 스프레드 차단을 해제하거나 최초 anchor를 초기화해 신호를 만들지 않는다. [39건 인과 요약·원 증거 해시](../../tmp/late-observation-anchor-20261028/priority-pattern39/causal-summary.json), [전체 lease·실제 root 재생](../../tmp/late-observation-anchor-20261028/priority-pattern39/replay-v2.json).

등록된 A01/A14를 같은39lease·원 anchor·체류 종료·원천 공백에서 비교했다. 현행0에 대해 A01은6종목10개(저가6/중가1/고가3), A14는2종목2개(저가2)의 확인 지점을 만들었다. 관측 entry의 bid 분모 spread 최대0.08681%이며 기존0.1% 기준을 완화하지 않았다. 그러나12개 모두 원 lease 후행이0~80.201초여서 **WIN/STOP/TIMEOUT은 아직 미확정**이고 추가 승률·수익 개선을 주장하지 않는다. 종전 다른 PID의 A01/A14 7건과 이번12건은 별도 분모로 유지하고 독립 holdout으로 합치지 않는다. [동일 관측 입력의 등록 후보 비교](../../tmp/late-observation-anchor-20261028/priority-pattern39/registered-variant-comparison.json).

장후 reader도 실제 frozen15-column+원 행 ordinal, source별 명시 data root, socket/collector namespace 연결과 원 entry ask·시각을 검증하도록 보완했다. 동일 item의 **봉인된** 완료 분봉/REST revision만 사용하고 현재 mutable DB로 후퇴하지 않는다. 46회귀 PASS, source27의 실제 원 발행 reader→봉인 입력→원 comparison point/snapshot까지 격리 소비 PASS(자연 source28 아님). 최종 원 reader 검증2.58초/381,862,078 native hash bytes/프로세스 최고 RSS100,120KiB이며 native thread write_bytes0이다. 임시 inspector +392/-117, 기존 임시 research reader +199/-61이고 프로덕션 source/tests는+0/-0이다. 이전 버전·시도·원 코드 SHA와 source27 증거는 보존했다. [최종 리뷰·소비 인계](../../tmp/late-observation-anchor-20261028/phase-repair/review-final-before-observation.json).

관찰은 기존 임시 inspector의 단일 foreground invocation으로 수행하며 새 service/cron/collector/운영 stage를 추가하지 않는다.20:05 EOD 전에는 정규 작업을 조기 호출하지 않고, 이후 상태 변경에서만 스냅샷을 보존하며 새 child가 실제 선택 code root를 읽는다. source28은 자정 뒤에도28로 고정하고 기존 다음 영업일 finalization의06:50을 관찰 상한으로 삼되, 실제 worker의 원 기한·실패는 변경하지 않는다. source28 봉인 시 기존 native reader로 검증한 뒤 원7건과 추가12건, 누적 WIN/STOP/TIMEOUT/U, 기존 Q0/Q1/Q2 증거를 읽는다. Q의 복원되지 않은 적격 clock·미구독 반사실 가격은 null로 유지한다. 이 제한 연구 관찰의 완료를 전체 장후→다음 Main 기동 완료로 표시하지 않는다.

15:54:54에 실제 단일 관찰 **PID309277/start81504099**를 시작했다. 이는 거래 Main PID가 아니라 공유 tmp의 읽기 검증기이며 source28/target29, 원20:05 EOD·20:10 postclose 예약을 고정했다. 첫 상태는 Main running/source28 `not_yet_due`/findings0다. EOD 전에는 예약 시각까지 기다리고 새 원천/구독/주문을 만들지 않는다. [실제 관찰 invocation·원 예약·코드 pin](../../tmp/late-observation-anchor-20261028/phase-repair/observation-start.json), [최종 수리 gate](../../tmp/late-observation-anchor-20261028/phase-repair/review-final.json). 시작은 봉인·연구 완료 증거가 아니며 현재 owner는 OPEN이다.

16:04:49 보완 리뷰: 원 raw label을 나중 재관찰 틱까지 연장할 수 있는 경계를 확인해 **자연 source28 소비 전** 수리했다. 자신의 임시 observer309277만 종료하고 원 attempt/코드/종료 기록은 보존했다. 거래 Main은 종료·재기동하지 않았다. 원7건·후속12건에 실제 lease 시작과 `min(원 종료, 원 residence deadline)`을 결속하고 raw 판정은 그 안에서만 수행한다. 이후 보완은 적격한 원 entry와 동일 item의 봉인된 완료 분봉/REST만 허용한다.19개 확인 지점 모두 원 deadline 안이며, 원7건과 후속12건의 분모·확인 수는 바뀌지 않는다. 재관찰의 상승 틱이 승리를 만들 수 없다는 회귀를 포함해 **47 PASS**, bounded 원 comparison point/snapshot의 source27 실제 intake도 PASS다.5개 원 case 입력의 물리 SHA와 socket/collector 연결을 보존한다. [원 임시 observer 종료 근거](../../tmp/late-observation-anchor-20261028/phase-repair/observation-stop-for-review.json), [보완·재리뷰·소비 검증](../../tmp/late-observation-anchor-20261028/phase-repair/review-lease-boundary-final.json). 원 worker deadline·관찰 상한·모든 안전기준과 프로덕션 code/test 변경0은 유지한다.

16:11:22에 **임시 observer PID348145/start81602912**로 재개했다. source28 `not_yet_due`/findings0이고 실제 Main은 별도 running 상태다. 원06:50 관찰 상한·코드 pin·기존 EOD/postclose 예약을 유지했다. [현재 관찰 인계](../../tmp/late-observation-anchor-20261028/phase-repair/observation-resume.json). 자연 봉인·후행 승패 수용은 여전히 OPEN이다.

선정 원인도 source27의 봉인 table·native `cumulative_selection`·실제 발행/현재 선택 코드의 `select_variant` 함수와 대사했다. 현행 저가G4는4/4·중가 union은8/8(U7 별도)·고가G2는2/2(U4 별도) WIN으로 모두 carried다. native primary metric은 비용 결속 누적 target-first 승률이고 이 계약의 sample_floor는 none이다. 같은 table의 A01/A14 승률은 저가21.91%/28.80%, 중가30.70%/46.09%, 고가48.66%/60.53%여서 WIN 수가 더 많아도 선택되지 않았다. 동률에서는 WIN 수 증가도 개선으로 인정하므로 단순한 동률 잠금 결함은 아니다. **좁은 조건과 이를 유지하는 선정 목적이 함께 현재 포착 범위에 영향을 준다**는 인과 해석이며, 작은4/8/2 표본의100%를 미래 성과로 일반화하지 않는다. 선정 metric/표본 기준을 수리 명목으로 바꾸지 않고 source28과 별도 독립 검증에서 추가 WIN·STOP·TIMEOUT·U 및 기존 WIN 손실을 비교한다. [선정·승계 인과 증거](../../tmp/late-observation-anchor-20261028/priority-pattern39/selection-cause.json).
