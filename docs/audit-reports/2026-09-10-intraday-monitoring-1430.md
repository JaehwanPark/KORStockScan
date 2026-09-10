# 14:00~14:30 장중 모니터링 종료

대상일2026-09-10 KST. 사용자 지정14:30까지 관찰 완료, 종료 계좌 대사14:30:28. 평가 집계는 decision_ts 기준14:00 이상/14:30 미만이다. 이 실행은 재기동·정책·주문·원장 수정을 하지 않았다. 이전 수리는 [holding 입력/custody 적용 리뷰](2026-09-10-holding-input-custody-repair-review.md)의 별도 완료 기록이다.

## 판정

- 운영 고정본76995257/PID772330 유지. 14:27 exact env verify passed/pid_passed=true, missing/mismatch·policy/dated fail0. KRX 승인 SHA95a10c8513acedad7044678cf026ce47ecf5c2f041aeec107ee8f3341da20da0, 1주 일일100과 사용6 유지. 다른 세션 미완료 adaptive-exit 변경을 메인 배포에 포함하지 않았다. 이번 커밋/푸시/main 병합 없음.
- 수집 영속 정상과 입력 품질을 분리한다. 정상 real holding Provider 응답의 microstructure 품질 강제 HOLD 재발0이지만 시세/tape/broker snapshot 사전차단은 남았다. 신규 실체결0, 실제 빠른 익절·순이익 개선은 미입증이다. 미래 표본이나 sim 체결로 보완하지 않는다.
- 삼성E&A는 실제 HELD 보유가 아니다. 사용자가 다시 확인한 전일 수동매도 완료와 broker0주를 반영하면, 잔여 HELD/registry10주는 수동 successor 귀속 미정리다. 이를 정상 보유나 당일 신규 episode로 보고하지 않는다.

## AI와 매매 흐름

| 모집단 | 평가·호출 결과 | 남은 경계 |
| --- | --- | --- |
| main 실보유42433/42313 holding | 75평가: OpenAI parse57(TRIM31/EXIT23/HOLD3), 입력 사전차단18, 품질 override0 | 모델 action은 직접 매도 명령이 아님. 실제 청산/순익 미발생 |
| Entry screen | 15평가: parse13(WAIT9/DROP4), 원익14:08:55 timeout1(5초 budget/provider4936ms), 입력 사전차단1 | 강제 BUY 복구 없음, 연쇄 장애 확인 안 됨 |
| Entry price | Bedrock parse7, 모두 USE_DEFENSIVE | 실제 submit 성공과 별도 |
| 전체 trace | 122평가 | sim/record 없는 holding 포함이므로 실제 보유75와 혼합하지 않음 |

근거는 data/ai_decision_trace/ai_decision_trace_2026-09-10.jsonl(집계 마지막14:29:56.394626), data/ai_decision_payloads/ai_decision_payloads_2026-09-10.jsonl과 pipeline_events의 읽은 시점별 byte offset이다. 전체 과거 pipeline의 반복 복제·대용량 funnel 재생성 없이 최초 bounded tail 이후 증가분만 관찰했다. stage event 수는 unique 기회/주문 수가 아니다.

14:02 실제 holding pipeline에서 latest_cache_acquired 및 fresh source의 TRIM 소비를 확인했다. 일부 fresh 결과도 기존 score/TTL/손실·이익/지속 조건을 거쳐 청산 여부가 결정된다. 14:11 와이씨 EXIT/raw34→effective43, profit-0.64%와 미청산을 함께 기록한다. 레메디14:06:15 low_profit_stagnation_confirmation 시작(+0.42%, peak+0.42%)은 평가이익 관찰이지 실현익절이 아니다. 단일 후행 가격으로 기존 청산 조건 완화 권한을 만들지 않는다.

14:15:06 BUY Funnel의 당일 누적은 ai_confirmed235→241, submitted6 그대로, submitted/AI2.5%, SUBMIT_DROUGHT_CRITICAL/LATENCY_DROUGHT다. 누적에는 수정 전 구간이 포함된다. 14:00 이후에도 liquidity/latency/zero-quantity/최종 authority·revalidation 차단이 관찰되어 AI만 단독 원인으로 귀속하지 않는다. 14:06:57 900270은 blocked_zero_qty/guard_intended_zero다. 계좌 guard·탐색 cap을 변경하지 않았다.

Scanner source fetch/promotion/fast-heavy evaluation·prune schedule은 계속 관찰됐다. 시장 census 종합 report12:00은 예정 refresh(09:15/12:00/15:15/19:45) 계약이며 dead producer가 아니다. 5분 capture는 계속되고14:05 KRX/NXT×all/liquid_common 네 capture 모두 성공했다. 일부 이전 shared read budget defer는 제외/결손으로 보존한다. top-N/panel 및 bounded prune observer만으로 전시장 actionable recall·미포착 순이익을 입증하지 않는다: insufficient_evidence_scanner_recall, 현재 종합 recall 재생성 없음.

## 수집·원천 감사

- 14:00:39→14:30:25 collector persist trade29122→136414/depth46568→217825. 최종 writer3/3, queue full0/0, writer error0/0, canary healthy_observer_canary_with_source_row_exclusions/stop 없음, callback p99 0.121466ms. free28.193→27.632GB. 디스크 watermark 장애/삭제 없음.
- invalid depth timestamp1→17은 원천 제외다. 관찰된 일부0D exchange→packet lag는10초 이상이며 packet 이후 normalization 지연과 분리된다. 이것만으로 외부 시스템 단독 원인이라고 확정하지 않는다. 저장되지 않은 과거 ingress gap은 raw 감사로 복원하지 않는다.
- 14:20~14:22 기존 observation_source_quality_audit를 ionice/nice로 단회 읽기 전용 실행했다. 명령: PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-10 --print-summary. 명령 exit0과 감사 status=fail은 별개다. --write 미사용, canonical audit/원본/제외 manifest 수정 없음.
- 193877 events/176 stages, hard_blocking_contract_gap_count1, hard_blocking_excluded_row_count1(검출·제외대상 수이지 실제 제거 완료 아님), unknown_token_stage_count4/review_warning_count4, high-volume no-source0. tuning_input_allowed=false/blocked_reason=source_quality_raw_changed_during_audit. 장중 append가 계속되므로 읽은 generation의 전체 승인 불가이며 전일 PASS로 대체하지 않는다.
- 해당 stage만 추가 검증한1030행 중12:15:26.432076/record42154/488280 한 행의 invalid_fields=[minute_candle_window_fresh_contract]를 특정했다. stage=scalp_entry_action_decision_snapshot. 과거 발생분이며 이번14:00 이후 신규 위반으로 보고하지 않는다. 퇴역 ADM authority를 복원하는 작업이 아니라 원천 계약/제외의 후속이다.
- 경고 stages: avg_down_exit_replay_frame_observed, scalping_scanner_source_fetch_census, stat_action_decision_snapshot, scalping_scanner_candidate_pool_census. 정확한 결손행 격리/producer·unknown 계약 검토와 writer 종료 후 안정된 generation 재감사는 기존 장후 owner로 인계한다. 동일 live generation을 반복 감사해 PASS를 만들지 않는다.

## 독립 기계와 계좌

- 13:59/14:04 기동한 한국전력·NHN·삼성중공업·SK이터닉스·팬오션,14:14 CJ CGV/SD바이오센서,14:19 두산에너빌리티/한세/롯데케미칼은 당일 READY/유효창 무신호를 확인했다.14:24 SKT,14:29 TYM/영원도 실제 PID를 확인했으나 종료시각에는 일부 신호창 대기이므로 이후 결과 미판정이다. 이 관찰은 timer 수동 실행이 아니다.
- 삼성 오후는 READY/완성봉 무신호, 삼성 오전 두10주 leg의 COMPLETE는 이 구간 이전 결과다. 위젯 heartbeat14:30:16, actual_order_submitted=false; 구현 중 적응형 청산 신규 활성화·기존 보유 편입 없음.
- 삼성E&A 오후 service14:19:17은 전일2026-09-09 HELD 원장을 출력하고 exit0으로 종료했다. 현재 생존 process/오늘 무신호 성공과 다르다. [08:30 exact 수동매도 대사](2026-09-10-intraday-monitoring-0830.md): SELL0056859는 원주문0053225의 수동 정정 successor,10주@50600원 체결/미체결0, 매체 영웅문S#. 원주문시각을 fill시각으로 합성하지 않는다. 사용자의 이번 재확인과 broker0주가 일치한다. 원장 정합성 수리·다음 신규 시작 허용은 별도이며 이번 수정/주문 없음.
- [종료 broker](../../tmp/intraday-monitor-20260910-1050/broker-143029.json), as_of14:30:28: KRX/NXT 조회 성공, 삼성전자25/SKT10/와이씨1/레메디1주. 기존 SELL0022607 SKT10주 한 개, exact owner match1. 시작/중간/종료 대사 동일, 중복 주문·수량 흡수 관찰 없음. 028050 registry10/broker0는 위 수동 귀속 gap. main 두1주를 generic registry remainder라는 이유로 manual 소유로 오분류하지 않는다.

## 후속 owner와 검증

현재 OPEN 분류: RuntimeEnvIntradayObserve0910은 본 구간 PID/수집/자연 입력 확인, 경제성·후단 차단 수락은 OPEN. WidgetEpisodeApprovedNextDayExecution0910은 예정 기동 확인/삼성E&A 수동 successor 원장 미정리 및 미래 신호 결과 OPEN. MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910은 저장 지속 확인/과거 ingress와 일부 입력 신선도 OPEN. SimProbeIntradayCoverage0910은 sim과 real 분리·이번 실주문 누출 관찰 없음이며 기존 sim 원장 보존식은 이번 상세 수리 범위 밖이다. IntradaySourceQualityGateCheck0910은 위 읽기 전용 감사·hard gap/경고 식별까지 완료, 실제 격리·canonical gate 수락은 미완료다.

16:30 ThresholdDailyEVReport0910,17:00 HumanInterventionSummary0910,18:00 MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910,21:15 CodeImprovementWorkorderReview0910,21:30 MachineLifecycleTurnoverObjectiveFollowup0910,21:40 AutomationTriggerDecisionSummary0910/PostcloseSourceQualityGateReview0910은 not_yet_due/요청 종료 이후다. KRXDaily100NextDayStartupAcceptance0911은 내일07:30~08:05; 오늘 frozen PID 성공은 원 작업폴더를 사용하는07:55 cron의 동일 배포 보증이 아니다. OPEN 분류 누락0, 전체 수용 완료나 미래 실행을 주장하지 않는다.

이번 변경은 이 감사 기록과 기존 체크리스트의 관찰·handoff 메모뿐이다. korstockscan-review-gate로 시각·실현/평가·sim/real·원장/실보유·권한·링크를 재검토하고 print-only parser/diff 검증한다. 거래 코드 테스트/재기동/Provider replay/장후 전체 자동화/외부 Project·Calendar 동기화는 실행하지 않았다. 기존 payload 길이 실패와 내일 배포 경로는 별도 미완료이며 이 모니터링으로 닫지 않는다.
