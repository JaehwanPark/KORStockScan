# 9/11 10:29~11:00 장중 모니터링

요청 종료시각11:00 KST. 이전 배포/재기동과 분리한 지속 관찰이다. 시작 main165934/common486b9cc2, 삼성 오전acf139cd 설치/정상창 종료, 위젯144180/a2e14f5d의 별도 배포를 확인한다.

## 시작 판정

10:29 최신 sentinel as-of10:25:04 KRX AI61/budget154/latency32/submit3, 자금부족 제외10. SUBMIT_DROUGHT_CRITICAL 유지. 서로 다른 raw stage unique를 단일 인과 funnel로 합산하지 않는다. 제출0029085 저스템·0029141 와이지-원·0029261 뉴로메카는10:26 재기동 이전 자연 주문이며 배포의 인과적 효과가 아니다. 와이지-원 sell_completed0029812와 gross profit_rate+0.42%는 실현비용 대사 전 net PnL로 표시하지 않는다.

V2.14 사용자 질의 점검: 당일 candidate/activation maximum_daily_exploration_probes100, 현재PID recheck/MAX_DAILY_BUY_RECOVERY 각각100, 원장 accepted_probe_count3. 기존3회 한도 소진이 아니며 이 quota의 잔여97. 기존 일반3 기본값/다른 cohort는 KRX100 적용과 별개다. 근거 `tmp/intraday-monitor-20260911-1100/v214-limit-check.json`.

10:30 NHN preflight는10:30:08 success, 실제 기동10:34 예정. SD바이오센서10:35/10:39, SK이터닉스·SK텔레콤10:40/10:44 예정. 예약을 앞당기거나 종료된 삼성 오전창을 다시 열지 않는다.

독립 census 최신 report09:15:34는 partial diagnostics이며 official master lookup/cadence/BBO coverage/outcome floor 결손으로 전체 recall 정상 근거가 아니다. 설치된5분 원천 collector는 refresh_report=false로10:25:34까지 진행했고 NXT all panel1건 shared-read-budget defer를 결손으로 보존했다. report 생성시각과 원천 수집 중단을 혼동하지 않는다. 신규 capture/직접 consumer는 이후 확인한다.

Holding sentinel AI_HOLDING_OPS는10:30 AI review72/cache miss100%/parse fail0이다. cache miss와 실제 parse 장애를 분리하며 현재 warning만으로 provider/TTL/청산을 변경하지 않는다. 삼성E&A 오전후반은10:06 checkpoint의 유효 초기 source 이후 pre-transport depth/trade stale로 NO_FILL; 삼성 오전 prearm clock 결함과 합치지 않는다.

## 체크리스트 전수 분류

시작13 OPEN. MachineProfitStagnationStartupAcceptance0911은through14:35 부분수용/수집 중. KRXDaily100NextDayStartupAcceptance0911은 window 경과 후 정책/PID/WS/Provider 수용조건 재확인. MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0911은 과거 ingress 격리와 through-close 신규원천 대기. RuntimeEnvIntradayObserve0911·SimProbeIntradayCoverage0911은 기존 부분확인 후 남은 provenance/source 조건 대사. 이5개는 overdue_unresolved 또는 ongoing acceptance이며 process 실패로 일괄 분류하지 않는다.

IntradaySourceQualityGateCheck0911(14:20), ThresholdDailyEVReport0911(16:30), HumanInterventionSummary0911(17:00), CodeImprovementWorkorderReview0911(21:15), MachineLifecycleTurnoverObjectiveFollowup0911(21:30), AutomationTriggerDecisionSummary0911·PostcloseSourceQualityGateReview0911(21:40), MachineOneDayQuantityExpiryAcceptance0914(9/14)는 not_yet_due. 예정 전 producer 조기/중복 실행 없음. 미분류0; 기존 완료된2항목은 재실행하지 않는다.

관찰 snapshot은 `tmp/intraday-monitor-20260911-1100/`에 source hash와 함께 보존한다. 과거 ingress/raw 결손·실현비용·장후/다음 정상창 acceptance는 별도 OPEN으로 유지한다.

## 10:34~10:40 관찰

NHN10:34:08/PID175490, SD바이오센서10:39:08/PID181465 정상 기동. NHN은 bar_evaluated_no_signal. TYM/삼성중공업/두산 오전후반은 신호 없이 window 종료. CJ CGV 오전 failed unit은09:09 exit4/research_half_robustness_review_requires_new_profile_revision의 terminal quarantine이며 현재 새 crash로 재실행하지 않았다.

Micro165934의 제외2행은064760/405100 호가가 packet 수신 시 이미12.122초/11.259초 지난 자료였고 packet→normalization1/8ms였다. 해당 행을 제외하고 writer 체결3/호가3·worker/queue 오류0·stopfalse로 수집 중. 과거 PID의 전수 ingress 결손과 분리한다.10:35 sentinel KRX AI71/budget166/latency36/submit3/자금제외10, detector PASS.

## 10:44~10:48 관찰

SK이터닉스10:44:10/PID187488·SK텔레콤10:44:11/PID187519 정상 기동,10:47 네 신규 기계 모두bar_evaluated_no_signal.10:45 sentinel KRX AI76/budget178/latency37/submit3·자금제외10, exact terminal upstream121/latency97/AIauthority20/price23/broker0. 개별 stage 분모와 동일attempt terminal을 구분한다. Micro11행 제외 중 증가분은361570 호가 시각 정체가 주원인이며packet→normalization0~9ms,writer/queue/참조오류0, 주요0B/0D 수신 유지. 선택486b9cc2/main165934 유지.

## 신규 제출과 별도 제한 결함

10:50 sentinel 신규 아이씨티케이456010/order0033561/1주18140원, quota accepted4/100. 기존3건 이후 실제4번째 제출이므로 3회cap 차단이 아니다.10:51:28 broker KRX+NXT는005930 25주/348340 1주/417840 2주/456010 1주, 미체결0이다. 공통 registry의 external_manual_remainder 표시는 해당 registry 미귀속 분모이지 이 매수가 수동 주문이라는 증명이 아니다. main pipeline의 고유 주문·체결과 따로 대사한다. 종목명은 원문417840 저스템/019210 와이지-원/348340 뉴로메카로 정정했다.

저스템 추가1주는AVG_DOWN/order0031582/fill15850원/new_qty2, reason late_loss_avg_down_retry다. 같은record42879의 초기 probe0029085는entry_setup_bounded_exploration_probe_only로 residual을 차단했고 지속 probe 원장에도aborted/scale_in_forbidden=true가 남는다. 이를 정상 정책 전환이나 수익 개선으로 승인하지 않는다.

선택 release의 `_clear_superseded_entry_setup_exploration_arm`를 AST로 격리해 실제 함수와 dict-mutation stub만 실행한 반례에서 status HOLDING/buy_qty1/phase aborted의 제한을 current_policy_mode baseline으로 지울 수 있음을 확인했다. `tmp/intraday-monitor-20260911-1100/exploration-clear-reproducer.json`에 source hash/전후 필드를 보존했다. 이는 함수 결함 반례이며 저스템의 실제 호출 인과를 입증한 것은 아니다. 후보 수리 범위는 미제출 상태에서만 arm 정리, filled/terminal 탐색 제한 보존, 재기동 복원 및 최종 scale-in 소비 검증이다. 실제 BUY/수량 guard를 바꾸므로 일반 source-only 모니터링 권한으로 적용하지 않았다. 기존 Runtime/CodeImprovement owner에서 이 live guard 수리·배포 권한과 실제 lifecycle cause를 분리해 처리해야 한다. 수리 완료/finding0을 선언하지 않는다.

## 11:00 종료 점검과 자동 청산 제외 경보

11:00:05 sentinel KRX AI85/budget196/latency40/submit5, 현금부족 제외10, SUBMIT_DROUGHT_CRITICAL 유지. quota 원장10:56:07 accepted_probe_count5/100이며 기존3회 제한이 아님을 자연 제출로 확인했다.11:01:01 최종 snapshot으로11시 경계 산출물을 확인하고 지속 모니터링을 종료한다. Micro11:00:59 row exclusion14, stopfalse/p99 0.130ms. main165934/선택486b9cc2 유지.

10:56:37 아이씨티케이456010/record42892는 HARD_STOP_MANUAL_HANDOFF 경로에서 hard-stop 제출 전 수동관리 제외를 등록했다. 현재PID의 KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED=true 및 retry5초를 확인했다. 코드의 operator_hard_stop_manual_control_handoff 경로이며 브로커 주문 거절로 단정하지 않는다.10:57:18 자동 청산 감시 제외,11:00:48 detector FAIL. current_auto_source=auto_hard_stop_handoff/current_operator_source 공백으로 명시적 수동 소유권 근거가 없다.10:58:09 broker는 아이씨티케이1주 보유/전체 미체결0, 삼성25·뉴로메카1·저스템2도 확인했다. 사용자/다른 창의 수동관리 변경 여부는 질의 후 미확인이다.

자동 제외 해제·SELL·hard-stop 정책 변경은 이번 일반 모니터링에서 실행하지 않았다. RuntimeEnvIntradayObserve0911에서 현재 operator 계약과 자동 제외 원인을 우선 대사하고, 명시적 소유권 또는 승인된 자동 감시 복구 및 주문/보유 정합성으로 닫아야 한다. 단순 재기동으로 owner 정책을 바꾸지 않는다. 저스템 추가매수 제한 문제와 함께 미해결이며 전체 finding0/정상 완료를 선언하지 않는다.

이번 변경은 관찰 문서/기존 체크리스트 근거 기록이다. 원천 생성/관측, 코드 반례, 실제 guard 수리 권한, 경제성 수용을 분리했다. 체크리스트13 OPEN 전수 분류/미분류0을 유지하고 미래 예정 producer는 실행하지 않았다. 실현 순손익은 exact 비용 미대사로 미확정이다.
