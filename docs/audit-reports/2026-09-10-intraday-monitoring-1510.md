# 15:10까지 장중 모니터링

대상일 `2026-09-10 KST`, 시작 관찰 `14:42:22`. 사용자 지정15:10까지 모니터링을 마쳤고 최종 계좌 대사는15:10:22에 확인했다. AI 집계는14:42:00 이상/15:10:00 미만, 마지막 trace15:09:59.665160 기준이다. 이번 모니터링은 주문·정책·배포·재기동·원장을 변경하지 않았다. 직전 삼성E&A 원장 정리는 [별도 승인 완료 기록](2026-09-10-samsung-ea-manual-ledger-reconciliation.md)이다.

## 종료 판정

운영 가동과 수집 지속은 확인했으나 거래/판단 품질 전체 정상은 아니다. 반복 입력 preflight와 제출 병목이 남고, SK텔레콤 episode terminal projection의 새로운 결함을 확인했다. 사용자에게 요청한 SK텔레콤 원장 정리 답변은 종료 시점까지 없어 미적용이다.

| 14:42~15:10 평가 모집단 | 정상 응답 | 입력 사전차단 | Timeout |
| --- | --- | --- | --- |
| 메인 실보유 record42433/42313: 71건 | 33 (TRIM22/EXIT10/HOLD1) | 37 (52.1%) | 1 |
| Entry screen: 17건 | 10 (WAIT5/DROP5) | 6 | 1 |
| Entry price: 7건 | 7 (USE_DEFENSIVE7) | 0 | 0 |
| 전체 trace: 116건, 위 분모 외 record 없는/sim/다른 holding 포함 | 59 | 55 | 2 |

실제 호출된 Provider가 none인 incident0, holding 품질 강제 override0. 파싱 성공은 판단 성공이 아니며 정상 Entry BUY0, 원장 탐색 사용량6/100 유지, 이번 main 신규 체결·실현익절 미확인이다.15:08 당일 PID verifier passed/pid_passed=true/status=pass를 재확인했다.

종료 broker는 삼성전자25·와이씨1·레메디1/미체결0. 삼성E&A broker/registry/state0 유지; SK텔레콤 broker/registry0이나 episode HELD10은 아래 결함으로 남긴다. 최종 collector15:10:11 trade/depth309448/465228, writer 각3/queue full·error0/stop0, invalid depth timestamp26, 여유24.95GiB. 수집 보존은 확인했으나 결손 원천·모든 후행 경제성 교집합을 정상 승인한 것은 아니다.

검증 근거는 `tmp/intraday-monitor-20260910-1510-evidence.json`의 AI 읽기 hash·byte 수·종료 snapshot·pipeline 증가분 hash/offset 및 `tmp/intraday-monitor-20260910-1050/broker-151022.json`이다. AI source SHA256 `8e398d92182909c842044d19e9739e4220c7d4b83825b8311503839dc550da7c`. pipeline의 연속 증가분 감시는14:45:17부터이며14:42부터의 전수 pipeline 통계로 과장하지 않는다. growing source의 현재 전체 hash가 아닌 읽은 시점/범위 증거다.

## 운영 및 거래 관찰

- Main PID772330, frozen release `holding-input-76995257` 유지. 14:44 기존 verifier의 당일 `--verify --date 2026-09-10 --pid 772330` 통과. 실행 코드 `src/deploy` 변경 없음, KRX V2.14/일일100의 자연 trace 소비 확인, 사용량6 유지. 다른 세션 미커밋 adaptive-exit 등 변경을 배포에 포함하지 않았다.
- 14:48:59 및14:58:12 KRX/NXT broker 대사: 삼성전자25·와이씨232140 1·레메디387690 1주, 미체결0. 공통 registry의 main 두 종목 remainder는 별도 main record42433/42313에 연결되므로 수동 보유로 재분류하지 않았다. 삼성E&A broker/registry/state0 및 COMPLETE 유지.
- 팬오션 오후: signal_features.signal_decision_at=14:40:05.147644, 두10주 BUY0059715/0059717, 지정가6000/5990.14:45:09의 entry_validity_expired 대사 후 NO_FILL/NO_TRADE0주, service inactive/exit0. 주문 생성은 이번 모니터링 전 자연 기계 동작이며 이 세션이 제출·취소하지 않았다. anchor는14:39 완성봉이 아니라 실제 signal_decision_at이다.
- 오후 SD바이오센서·롯데케미칼·두산에너빌리티·한세는 당일 scan window closed/NO_TRADE. 저가주 당일 state census는 NO_TRADE54, HELD1이며 HELD1은 아래 SK텔레콤 불일치다. 삼성E&A는 전일 state이므로 오늘 READY/성공 표본으로 세지 않는다.
- 위젯은 자연 cycle 지속, enabled4/eligible2, 최근 runtime summary의 actual_order_submitted=false. 실제 신규 episode/경제성 성공을 선언하지 않는다.

## 새 결함: SK텔레콤 목표 체결 후 에피소드 HELD 잔존

- Exact owner `episode:sk_telecom_morning:017670:2026-09-10`, BUY0021585 10주, original target SELL0022607 10주×90,700원. 다른 BUY0021588은 NO_FILL이다.
- 에피소드 audit14:35:08.633546은 `ka10075_terminal_absence_confirmed`와 당시 dated receipt filled0을 근거로 `target_terminal_absence_position_held`, position10을 기록했다.
- 공통 registry는14:35:09.392728에 동일 target의 FILL_RECORDED10주를 기록하고 shared_ws_execution_receipt_terminal로 종결했다. 에피소드 service는14:35:13 exit0이지만 원장은 HELD10 그대로다.
- 15:00의 기존 read-only kt00007 재조회에서 target0022607 filled10/remainder0/price90700/REST API/SOR를 확인했다. 실제 broker0 및 공통 registry0과 에피소드 state10의 불일치다. 수동매도나 다른 owner 청산으로 추정하지 않는다.
- 최초 결함은 주문목록 부재 관찰과 약0.76초 뒤 체결 receipt 사이의 순서에서 에피소드가 후행 fill을 놓친 terminal/custody projection이다. source 자체 소실이 아니다. 고정본 `regular_two_leg_machine.py`의 `_reconcile_target` 해당 경로는 current-open 부재 뒤 잔여수량에 따라 HELD를 기록한다.
- 사용자에게 별도 원장 정리 여부를 비동기로 확인 요청했다. 답변 전 state/registry를 수정하거나 service를 다시 시작하지 않는다. 공유 registry에 SELL을 다시 추가하면 이중 청산이므로 금지하며, 승인 시 기존 exact-original-target reconciler로 에피소드만 정리해야 한다.
- 지속 보완은 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에서 late receipt/terminal absence 경쟁과 idempotent exact-owner 반영을 검토한다. 기존 원천으로 체결을 대사하되 미확인 체결시각·비용 합성, 다른 owner 흡수, 실주문으로 수리하지 않는다. 운영 custody 코드 및 타 세션 미완료 변경에 걸친 반영은 별도 권한·리뷰를 요구한다.

## AI·제출·원천 품질

- 관찰 구간 trace는 decision_ts 기준14:42 이상/15:10 미만으로 종료 시 집계한다. record 없는/sim holding과 실제 main record42433/42313은 분리한다. 입력 preflight에서 Provider를 부르지 않은 HOLD/DROP은 모델 판단이나 Provider 장애가 아니다.
- Timeout 확인: 케이에스피073010 entry_screen14:43:31.678069/5264ms/5초 예산, 레메디387690 holding_score14:54:30.612679/7028ms. 이후 정상 응답은 지속됐다. 중간 메시지의 삼성제약 명칭은 오류로 정정했으며 정확한 종목은 케이에스피다.
- 진입 preflight의 직접 blockers는 bbo/current_price/tape stale, realtime type provenance, 일부 source_time_skew다. 실제 holding에는 stale_tick_context, 판단 TTL 만료, 일부 broker snapshot advisory가 관측됐다. 신선한 모델 EXIT/TRIM이 downstream에 보존된 경우와 기존 유효성·청산 조건으로 실제 주문하지 않은 경우를 구분한다. 모델 EXIT를 실매도 완료로 세지 않는다.
- 14:55:04 정기 BUY Funnel은 SUBMIT_DROUGHT_CRITICAL + LATENCY_DROUGHT, 당일 submitted/AI2.30%·submitted/budget1.10%를 기록했다. 이는 일누적 진단이지 이번28분 성과나 unique missed-profit이 아니다. 자동 후속은 postclose workorder이며 장중 threshold/restart 권한이 없다.
- 14:50 WS report는 자연 갱신, source_missing0/diagnostic_generated이며 당시 subscription-stale historical workorder는 여전히 observe/source-only다. 실행 중 collector 진행과 과거 source loss·정책 경제성을 혼합하지 않는다.
- 12:00 external market census의 whole_population_scanner_recall_state는 insufficient_evidence_scanner_recall. official master lookup gap/cadence/BBO coverage/resolved/right-censor floor 미충족이므로 scanner 전체 포착 정상 또는 놓친 순이익을 선언하지 않는다. 오후 report를 조기/중복 재생성하지 않았다.
- Micro collector14:42 trade/depth188052/293370→15:02 272809/412016, writer 각3, queue full/error0, canary stop0. invalid depth timestamp19→25는 row exclusion이며 정상 데이터로 보간하지 않는다. 여유 공간25.49→25.09GiB; 원천 삭제·압축·budget 확대 없음. 파일 증가와 모든 source/후행 economic join 정상은 별개다.
- 이전14:20 감사의 hard gap1/unknown warning4 및 raw changed fail은 [14:30 기록](2026-09-10-intraday-monitoring-1430.md)의 미해결 조건이다. growing 원본 반복 재생으로 PASS를 만들지 않았고 안정된 generation의 exclusion/producer 검토는 기존 장후 owner에 남긴다.

## 체크리스트 전수 분류와 경계

현재 OPEN13개 중 도래5개는 부분 확인/잔여 acceptance 유지, 미래8개는 not_yet_due다. 미분류0이며 전체 완료를 뜻하지 않는다.

| OPEN owner | 이번 분류 | 남은 조건 |
| --- | --- | --- |
| WidgetEpisodeApprovedNextDayExecution0910 | due/부분 확인 | SK텔레콤 exact target terminal projection, 전체 natural/경제성 |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910 | due/through-close 수집 중 | 새 원천의 exact consumer·장후 label 교집합; 과거 loss 제외 유지 |
| RuntimeEnvIntradayObserve0910 | due/PID·정책 확인 | 제출·입력 신선도·실제 terminal/순이익 미완료 |
| SimProbeIntradayCoverage0910 | due/비우선 source-only | 기존 보존식 결손 유지; 실주문·경제성 권한으로 전환하지 않음 |
| IntradaySourceQualityGateCheck0910 | due/이전 감사 fail 유지 | 안정된 generation exclusion 및 unknown producer/workorder handoff |
| KRXDaily100NextDayStartupAcceptance0911 | 미래9/11 07:30~08:05 | 당일 후보/PREOPEN·기동경로·새PID; 오늘 pin 영구상속 금지 |
| ThresholdDailyEVReport0910 / HumanInterventionSummary0910 | 미래16:30 /17:00 | 전일 source 결과 대사; 조기 실행 없음 |
| MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910 | 미래18:00 | exact source/label/cost·Provider 및 후보 구분 |
| CodeImprovementWorkorderReview0910 / MachineLifecycleTurnoverObjectiveFollowup0910 | 미래21:15 /21:30 | source repair·기계 custody/회전 후속, 별도 live 권한 |
| AutomationTriggerDecisionSummary0910 / PostcloseSourceQualityGateReview0910 | 미래21:40 | 실제 wrapper/최종 generation/handoff·exclusion |

퇴역 ADM/LDM/Opening Rotation/Swing 등은 재활성화하지 않았다. 별도 runtime/env verifier의 퇴역 선택 차단 결과와 현재 process 관찰만 사용하고, 모든 historical 경로의 무누출을 전수 증명했다고 주장하지 않는다. 장후 전체 재생성·Provider replay·패키지 설치·커밋/푸시·외부 Project/Calendar sync도 실행하지 않았다.

리뷰는 korstockscan-review-gate에 따라 관찰시각/원장별 권한/실제 주문과 판단/과거 감사와 현재 수집/OPEN owner를 대사했다. 문서의 함수명·지정가 표현을 보완하고 print-only parser 및 diff 검증으로 닫는다. 이번에는 runtime 코드 변경이 없어 거래 pytest를 다시 실행하지 않았고, SK텔레콤 코드·원장 결함을 finding0 또는 복구 완료로 보고하지 않는다.
