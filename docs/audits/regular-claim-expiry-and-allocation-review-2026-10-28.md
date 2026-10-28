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
