# 2026-10-07 Stage2 To-Do Checklist

## 오늘 목적

- 10/6 원천일의 연속 반전 기계·보조 전환, EOD 제외 장후 전체 재생성 및 10/7 정상 예약기동 준비를 완료한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- 공통 Daily/EV 튜닝 및 generic workorder는 퇴역 상태를 유지하고 family owner의 직접 근거만 사용한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

- 사용자 명시 승인 override: Main 연속 반전 12셀은 30분 비용 후 +0.4%/soft -3% 선도달의 누적 raw 승률로 선택한다. EV·손익비·최소 표본/일수·holdout·기존 제출 보존 gate를 추가하지 않는다. 운영 AI 횟수 quota는 영구 None이며 provider 간격·외부 rate limit·중복·timeout과 broker/order/custody/수량/자본 cap·hard safety는 유지한다.

## 전일 OPEN 인계

- [ ] `[DirectFamilySourceRepairCompactAuxiliary] 연속 반전 보조 입력·실제 AI 누적 승률·정규장 승계의 장후 통합` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 10/6 보완 연구 후~10/7 01:30 정책 확정 및 06:50 최종 인계`, `Track: RuntimeStability`)
  - Source: [통합 계획 §6](../proposals/continuous-reversal-machine-policy-nextday-plan-2026-10-06.md#6-보조판정-정책-확정과-장후-학습-전환), [보조 보완 연구·코드 검토](../audits/auxiliary-reversal-phase-repair-and-call-quota-review-2026-10-06.md).
  - 현재 완료: 최종 운영 문구/input/schema를 그대로 사용한 2,232회 실제 호출 시도·2,231개 응답 ID, 최종 요청 1,860개 중 1,859개 응답·timeout 1개. 비교는 공통 기계 적격 334점이며 구 C 문구 372개는 보존·제외. 정기 compact producer/12셀 publisher/runtime 직접 연결을 구현·리뷰하고 release `879d324f`에 배포했다. 새 장후 native 발행·consumer terminal은 전체 재생성에서 확인 중이다. 기계 ENTER+provider_called trace 모집단은 새 family에서 사용하지 않는다.
  - 완료 기준: 전수 반전 원천·분리 라벨→같은 기계 부모의 실제 AI raw PASS 누적 승률→12셀 선택·무표본 동일 유형 정규장 payload/hash 승계→단일 writer/loader·새 machine/label dependency·summary 직접 소비. EV·손익비·최소 표본/일수·구 독립 holdout/기존 제출 보존을 새 채택 문턱으로 요구하지 않는다. 문구가 바뀌면 실제 해당 prompt/input/schema hash로 재비교한다.
  - 역할 경계: 이 ID는 보조 producer/consumer 통합을 소유한다. 최종 release·EOD 제외 장후 전체 재생성·strict/controller/PREOPEN/PID의 통합 종결은 `DirectFamilySourceRepairMainMechanisticEntry`에 결과를 인계하며 별도 전체 실행을 중복 시작하지 않는다. 무제한 호출 승인은 계수/영속 예약/실제 응답 보존을 없애지 않는다. 주문·수량·자본 cap·custody·operator veto·hard safety는 유지한다.
  - 이전 원천 기록 보존: source 10/2의 `exact_stop_distance_missing_or_invalid`, runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, [원 summary](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json), 원 `compact_auxiliary_paired_economic_2026-10-02.json`은 source_gap 감사 이력으로 보존한다. 옛 `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`를 새 반전 family의 채택/인계 조건으로 되살리지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-02.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`historical_submission_or_source_unreconciled`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[DirectFamilySourceRepairEntrySplit] entry_split 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-10-02.json`.
  - 상태: family=`entry_split`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`operating_paired_source_missing`.
  - 완료 기준: closure_owner=`entry_split_order_plan`, closure_test=`same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[DirectFamilySourceRepairLowPriceTwoLeg] low_price_two_leg 직접 family 원천·경제성 계약 수리` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-10-02.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json)
  - 증거: runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, source_artifact=`/home/ubuntu/KORStockScan/data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-10-02.json`.
  - 상태: family=`low_price_two_leg`, task_role=`producer_contract_repair`, comparison_status=`mixed`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`profile_source_gap`.
  - 완료 기준: closure_owner=`low_price_two_leg_tuning`, closure_test=`profile_leg_durable_denominator_custody_cost_and_dated_consumer`. policy_receipt_valid=`True`, source_date=`2026-10-02`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 연속 반전 기계·보조 12셀 전환·최종 배포·EOD 제외 장후 전체 재생성·10/7 정상기동 준비` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 10/6 22:03~10/7 06:50 및 07:32~08:05 소비 확인`, `Track: RuntimeStability`)
  - Source: [통합 전환·전체 재생성 계획](../proposals/continuous-reversal-machine-policy-nextday-plan-2026-10-06.md), [보조 보완 실제 호출·운영 quota 코드 검토](../audits/auxiliary-reversal-phase-repair-and-call-quota-review-2026-10-06.md), [전수 가격 반전 연구](../audits/continuous-price-reversal-zero-base-research-2026-10-06.md), [장후 중단 영수증](../../data/report/postclose_operator_stop/2026-10-06/operator-stop-receipt.json).
  - 현재 완료: 통합 코드·연구 승계 리뷰 및 release `879d324f` 배포, cron 8개/release-set/기존 episode 186개 pin PASS. 원 연구 12셀 재현, 입력 372개 및 반전 모집단 701,638개 실시간 접두 parity PASS, 최종 actual AI 2,232회 시도. 운영 quota total/group=None이며 기존 env로 복원되지 않는다. 최초 전체 실행의 분할주문 합계 byte-budget 결함을 보완하고 198회귀·실제 295개 원천 census 일치를 검증했다. 최종 변경 계약 173 PASS. 00:40:27부터 source/publication 10/6/effective 10/7 EOD 제외 전체 generation 재생성 중. 원 중단/실패와 v1 실패를 보존하며 native 정책 발행·strict/controller/prepared·07:35/07:55 소비는 각 영수증으로 확인한다. [실행 검토](../audits/continuous-reversal-implementation-postclose-execution-review-2026-10-06.md).
  - 권한/범위: 사용자가 통합 구현·반복 리뷰·최종 배포·장후 전체 재실행·정상기동 준비를 승인했다. 오프라인 연구 무제한 호출과 운영 AI 호출한도 영구 해제를 명시 승인했다. 운영 total/group cap=None, 예전 횟수 env의 자동 복원 금지. 계수·중복/오류 재시도/외부 provider rate limit과 broker/order/custody/manual/retirement guard는 유지한다. code/release/새 terminal/prepared/실제 예약 PID를 구분한다.
  - Acceptance: 기존 판정 행을 모집단으로 쓰지 않는 연속 반전 kernel→30분/+0.4%/soft -3% 라벨→삼성 시장 3셀·비삼성 시장×가격대 9셀의 기계 누적 승률 및 보조 실제 원 PASS 누적 승률→동일 runtime consumer. 보조 문구/input/schema가 달라지면 실제 해당 hash로 재비교하며 EV·보정 승률·최소 표본/일수·기존 제출 통과 보존 문턱은 추가하지 않는다. 프리/애프터 무표본은 같은 종목군·가격대의 정규장 payload/hash를 그대로 승계하고 로컬 승률은 null로 남긴다.
  - 배포/재생성 Acceptance: 계획 P1~P7. 전환 machine+aux code 최종 immutable release→source/publication 기준 10/6/effective 10/7 단일 generation으로 **EOD 제외 활성 장후 전체** 재생성. main embedded/등록 stage·machine refresh·tuning·archive·summary/tower/checklist·strict/controller/finalization·cleanup/final detector·bootstrap 포함. EOD updater는 재실행하지 않고 원 terminal/hash를 검증한다. OFF/퇴역 family 복원·구 성공 표지만 변경하는 재사용 금지.
  - 종료/소비: 06:30 목표·06:50 상한까지 전체 장후 complete와 exact-date prepared를 각각 확인, 07:32 owner/07:35 Main PREOPEN 및 07:55 정상 PID에서 code·기계/보조 hash·quota=None 소비 확인. 문서 최종 hash 고정 뒤 strict→controller→prepared. 미완료는 원 실패/미준비를 유지하고 검증된 정규장/기존 정책 carry 가능 여부만 따로 기록한다. 실제 주문·체결·손익은 별도 관측이다.
  - 이전 원천 기록 보존: source 10/2 `machine_operating_population_unbound`, runtime_summary_sha256=`36668269ccbb3ab8a7c61b106cee3754ee867dc4e03123d89a32a7d9c384eb92`, [원 summary](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-10-02.json). 기존 completed-profit/EV 완료 문구는 새 기계정책 채택 기준으로 재사용하지 않는다. stable ID는 유지하며 `MainSubmitDroughtPathAcceptance1006`의 기존 경로 수리 자연 수용은 별도 보존한다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[JejuEpisodeRetirementHpspAlteogenMainFixedWatch] 에피소드 8종목 퇴역·Main 고정감시 5종목 다음 기동 자연 확인` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:32~08:05 및 적격 정규장 자연 판정`, `Track: RuntimeStability`)
  - Source: [실행 계획](../proposals/jeju-episode-retirement-hpsp-alteogen-main-fixed-watch-initial-policy-plan-2026-10-06.md).
  - 범위: 제주·TYM·CJ CGV·영원무역·SK텔레콤·한세실업·NHN·카카오 27개 profile와 timer 54개 및 service instance 54개 퇴역; HPSP·알테오젠·주성엔지니어링을 기존 삼성·두산 Main spec/정책/주문 경로에 추가한다.
  - 권한: 사용자 계획 실행·반복 리뷰·배포·재기동 승인. 신규 3종목 초기 정책은 기존 비삼성 Main 부모로 지정하며 성과/표본 적격성 증명을 선행 조건으로 요구하지 않는다. 원천·세션·주문·수량·custody·operator veto·hard safety는 보존한다.
  - Acceptance: 종목별 fresh broker/custody/전체 날짜 intent flat, 27개 전용 profile·54개 timer 제거 및 54개 instance mask, 재등록/auto expansion 차단, 남은 31개 profile 원 정책 값 보존, 5종목 실제 metadata→기계 resolver 및 compact AI 역할, WS publication/연구 저장 독립 검증, 신규 3종목별 10개 후보 연구, reviewed release/정상 Main singleton 및 policy/hash 소비. 자연 source/판정/제출/체결/수익은 각각 별도 receipt; 해당 session 미관측은 `not_observed`로 인계한다.
  - 기존 `DoosanEpisodeToMainFixedWatch`, `FixedWatchSourceAndCleanupRepair1006`, `FixedWatchBudgetSummaryPostcloseAcceptance1006`의 별도 자연 수용과 원 장후 실패/원천 결손은 보존한다.
  - 10/6 실행 완료: 코드 `511664f3`/Main PID `169115` bootstrap·프로세스 건강 PASS, native 퇴역 timer 54개 제거·instance 54개 mask, 현재 31개 profile·186개 policy pin·cron 8개 PASS, 원 자료 34개 SHA 보존. 1,304개 통합·추가 router 90개 회귀 PASS; 신규 3종목별 10개 후보 연구는 source_gap 처분. [최종 실행 검토](../audits/episode-eight-retirement-main-five-execution-review-2026-10-06.md).
  - 잔여 자연 확인: 현재 신규 3종목은 `fixed_watch_nxt_eligibility_unproven` WAIT이며 기존 listing/eligibility 원천으로 확인한다. 10/7 owner PREOPEN의 현재 15종목 scope, 31개 episode 실 기동, 5종목 정확 admission→기계 hash/compact 역할·WS/원천을 확인한다. KRX 정규장은 NXT 대기를 적용하지 않는다. 해당 session 미관측은 `not_observed`이며 성과 사전 입증 또는 주문/threshold/guard 우회 조건을 새로 만들지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[WidgetFullRetirement1006] 위젯 런타임·장후·관측·연구·화면/API 전체 제거` (`Due: 2026-10-07`, `Slot: MANUAL`, `TimeWindow: 실행 중; 외부 제거·자연 장후/기동 후 종결`, `Track: RuntimeStability`)
  - Source: [위젯 전체 제거계획](../proposals/widget-full-runtime-postclose-retirement-plan-2026-10-06.md), [정적 의존성·설치 현황](../../tmp/widget-full-retirement-planning-20261006/inventory.json).
  - 상태: 서버 코드·배포·정리 검증 완료. 커밋 `b53a3835`, 대상 3,382 PASS/skip 1, 전용 unit 11개 mask, API 404, 설치 Widget dispatch 0, 정책 pin 366개 검증. 전용 데이터 2,668개와 임시 릴리스 삭제 후 약 639MiB 확보. [최종 감사](../audits/widget-full-retirement-execution-review-2026-10-06.md). Main/에피소드 새 코드·episode fact producer의 실제 소비, 10/7 dated 정책 생성은 자연 장후/기동 receipt로 확인한다.
  - 외부/자연 acceptance: Windows는 운영자가 직접 제거 예정. 실제 제거 확인과 새 장후·다음 기동 receipt 전까지 G4/G5를 완료하지 않는다.
  - 범위: 자동/수동 위젯 주문, 가격 API·Windows client, collector/Telegram, 종목·보조 연구와 정책 발행, unit/timer/installer, 장후/PREOPEN/감시·배분, 전용 cache/data 정리.
  - 선행조건: 신규 widget BUY/ADD·수동 진입 차단 뒤 fresh broker/custody 대사; 잔여 노출 종결 또는 승인된 정확한 인계. 당시 로컬 수량 0은 broker flat 증거가 아니다.
  - 완료 기준: 계획 G0~G5. active 위젯 실행·필수 의존성 0, 공통 계산 이관과 Main/에피소드 회귀 통과, archive/삭제 manifest, 외부 Windows 확인, 자연 장후·다음 기동 증거를 구분한다.
  - 권한 경계: 이번 제거 실행은 승인되었다. 청산 주문·소유권 재분류를 추정 승인하지 않으며 Main 삼성 고정 감시·에피소드·공통 토큰/WS·order registry와 hard safety를 보존한다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[EpisodeCaptureSequence1006] Episode 동일 시각 상태 전이의 원천 sequence 소비 인계` (`Due: 2026-10-07`, `Slot: INTRADAY`, `TimeWindow: 09:00~20:00`, `Track: SourceQuality`)
  - Source: [10/2 원천·의미 복구 감사](../audits/postclose-semantic-source-monitoring-2026-10-02.md). 기존 active custody 원천 보완이며 OFF 신규 연구 복원은 아니다.
  - Acceptance: producer의 profile/day/instance sequence·이전 observation SHA와 소비자의 정확 predecessor 검증, same-clock 전이·append 유실·다른 PID/generation·날짜 reset 회귀를 유지한다. 기존 raw106건 conflict는 재라벨링하지 않는다. source-only 코드378 PASS와 Episode 실제 service pin/PID 소비를 구분하며, 별도 배포 권한 전에는 해당 매매 service pin/기동을 변경하지 않는다. 자연 해당 source가 없으면 not_observed로 인계한다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[DoosanEpisodeToMainFixedWatch] 두산 에피소드 제거·Main 초기 정책 지정의 PREOPEN 전환` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:00~08:00`, `Track: Runtime`)
  - Source: [전환 계획](../proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), [구현·검토 증빙](../audits/doosan-main-fixed-watch-implementation-review-2026-10-06.md).
  - 사용자 기준: 초기 정책 적격성 입증 불필요. 두산 초기값은 현재 Main 비삼성 정책 지정; 연구 source_gap/표본 부족은 지정 보류 사유가 아니다. 실제 원천·owner·broker·수량·주문·수동 veto guard 유지.
  - 구현 상태: workspace 3 profile/6 timer 및 override·dispatch 제거, symbol/owner 재등록 차단, Main 두 종목 고정감시와 WS exact item 승계, all-date intent 확인, 원래 policy hash 유지한 archive projection과 공용 원천 기록기 수리. 연구 25건 중 native lineage 결손 24·다른 scope 1, native 고정감시 0; 신규 수익성 증거 아님.
  - Acceptance: G0 fresh broker/원장 flat·미확정 intent 0; G1 installed 전용 timer/drop-in 제거·퇴역 instance mask; G2 새 코드와 rollback에 episode BUY 0; G3 종목별 고정 target/slot/상태 분리; G4 exact 0B/0D→quote→판정 source gate; G5 초기 지정과 후속 연구 구분; G6 exact-date owner/PREOPEN·release·PID·자연 기동 receipt. 코드 PASS를 설치 삭제/PID/실제 수익으로 대체하지 않는다.
  - 당일 전환: 14:23 native broker/원장/미확정 intent 0 재확인 후 timer 6개 삭제·instance 6개 mask 및 terminal 퇴역 receipt 발행. 14:24 Main 새 release/PID bootstrap PASS, 삼성·두산 독립 고정 target와 exact 신규 0B/0D 확인. 후속 mask 해석·installer priority·control receipt 권한 수리를 반영한 최종 d0a539ab/PID 4146183에서 14:33 bootstrap·실제 소비 PASS. 116 route/348 policy pin과 cron 8개 확인, 최종 139 PASS. 58-profile 소비 호환성을 위해 다음 template 시작 code를 맞추되 다른 종목의 현재 active PID·정책 값은 유지했다.
  - 후속 권한/리뷰: 사용자가 배포·재기동 승인. 122 PASS 추가 리뷰로 retiring/unknown order process만 차단하며 검증된 다른 종목 에피소드·Main 소유자는 유지한다. 당일 기존 owner/PREOPEN/bootstrap을 보존하고 episode BUY guard만 영구 제외한다. 다음 PREOPEN에서 Main·수동 owner만 발행한다.
  - Next: 당일 설치·Main code handoff/PID/자연 source는 완료. 10/6 native 장후 source→strict/controller→10/7 준비·10/7 owner 활성화는 예약 chain의 후속 수용이며 미래 완료를 추정하지 않는다. 기존 log_rotation_cleanup/postclose_finalization 실패·episode failed 3개의 별도 원천 상태는 성공으로 덮지 않는다. 기존 custody 자동 이관·청산 주문·다른 에피소드 재기동 없음.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[FixedWatchSourceAndCleanupRepair1006] 삼성·두산 기계정책 연결과 WS 원천 지연 보완의 자연 수용` (`Due: 2026-10-07`, `Slot: INTRADAY`, `TimeWindow: 15:10~20:00`, `Track: Runtime`)
  - Source: [결함·수정·정리 복구 증빙](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md).
  - 사용자 권한: 확인 결함 수정/리뷰 및 기존 cleanup_failed 복구. 두산 배포·재기동의 기존 승인 범위에서 정책 보존 후속 handoff; 새로운 정책·주문·원천 age/cap/read budget 변경 없음.
  - 코드: fixed symbol별 기계 owner 연결, dashboard 출력 window만 lock 안 동결, 단일 episode fact worker 분리, capture clock 보존, 예약/정산과 같은 lock 안 Provider summary 발행. 관련 642 고유 pytest PASS, compile/diff/parser 확인.
  - 정리 완료: 원장 36개 기록·manifest 원본 유지, 요약 복구 Provider 0; 15:09:46 target 10/2 네이티브 cleanup DONE, storage·compression·data failures 0. 과거 FAIL을 보존했다.
  - Acceptance: A1 reviewed immutable release/PID와 당일 원 정책 해시 동일; A2 삼성·두산 exact 0B/0D freshness/epoch와 snapshot lock/publication; A3 두산 자연 기계판정 trace와 BLOCK/RECHECK의 Provider 호출 전 종료. 예산 원장 장후 수용은 아래 별도 owner로 연결한다. 짧은 관찰을 종일 결손 0/수익 증거로 대체하지 않는다.
  - A5 과거 완료 복구: [v2 증거 소비·최종화 복구 계획](../proposals/postclose-v2-evidence-finalization-recovery-plan-2026-10-06.md). 10/2 v2 선행 12개 원 code/output/input/prerequisite를 읽기 검증하고 summary만 현재 v3로 재계산한 뒤 strict/controller→native cleanup/detector→최종화 DONE을 확인한다. 15:05 predecessor 실패와 15:09 cleanup PASS는 보존한다. 15:40 재시도의 `future_preopen_generation_stale`는 기존 당일 정책 보존 handoff의 frozen 파일/권한/소비/current PID 검증을 장후 소비자에 연결해 보완한다. 적용일이 지난 과거 복구는 다음 날짜 PREOPEN을 생성하지 않는다. A5 결과는 원 finalization DONE 및 후속 detector `recovered_late` 영수증으로 확인하며 10/6 자연 장후/10/7 기동 수용을 대체하지 않는다.
  - A5 연결 수리: 독립 읽기 owner `eeccb1f4`에서 요약을 재생성했다. 삭제된 원 `designated-machine-policy-20261005-3d0e5106` 코드 root는 Git 원본으로 복원하여 기존 기계 단계 해시와 대조했고, 12개 선행 원 정책/입력은 유지했다. 16:04 native summary 완료와 정책 bootstrap 검증 PASS. 이후 당일 정책 보존 재기동 및 원 날짜 최종화 결과는 위 A5의 native receipt로 판정한다. 복원한 원 코드 root는 선행 정책 증명에 필요하므로 보존한다.
  - 당일 반영: af780d9b immutable/PID 13210, 15:13:54 bootstrap 소비 PASS, 원 정책·PREOPEN 5개 해시 동일. 두 actual target/current PID env resolver 모두 기계 primary. 15:15~15:17 121 frame 연결 정상, snapshot 최대 1.471초, 두 종목 0B/0D 3초 초과 0. capture lock 중앙값 201.732ms 및 CPU 한 core 100.53%는 그대로 공개한다. A1/A2 해당 창 PASS, A3 새 자연 machine 이벤트 미관측은 OPEN. 장후 companion 수용은 별도 owner에서 확인한다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[FixedWatchBudgetSummaryPostcloseAcceptance1006] 장후 Provider 원장 요약의 자연 발행 결속 확인` (`Due: 2026-10-07`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~06:50`, `Track: Postclose`)
  - Source: [수정·검증 증빙](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md), 위 `FixedWatchSourceAndCleanupRepair1006`의 A4 후속 수용을 이관했다. 코드·10/3 원장 복구·10/2 cleanup DONE 증거는 그대로 보존한다.
  - Acceptance: 10/6 native 장후에 Provider 예약/정산을 실제 발행하면 execution-date ledger/manifest/summary의 head/bytes·예산·가격·authority 결속을 확인한다. 미호출/OFF는 not_applicable이며 입증을 위한 Provider 재호출을 하지 않는다. 새 v3 stage→summary→strict/controller/finalization을 원 source/publication/effective date로 확인하고 과거 10/2 v2 성공을 새 producer 성공으로 합성하지 않는다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.

- [ ] `[MainSubmitDroughtPathAcceptance1006] Main 제출 경로 수리의 다음 기동·자연 평가 확인` (`Due: 2026-10-07`, `Slot: PREOPEN`, `TimeWindow: 07:32~08:05 및 적격 session 자연 판정`, `Track: RuntimeStability`)
  - Source: [실행·리뷰](../audits/main-submit-drought-remediation-execution-review-2026-10-06.md), [계획](../proposals/main-submit-drought-priority-remediation-plan-2026-10-06.md).
  - 권한: 사용자 구현·반복 리뷰·배포·재기동 승인. 공통 WATCHING 평가 가격 gate 분리 및 등록 recipe 증거 계약 수리. A/B/C/D/E 비교 우위 없음으로 추가 전략 완화·정책값 변경 없음.
  - Acceptance: reviewed release/당일 bootstrap PID 소비, source-valid WATCHING의 목표가 위 평가→exact 기계 캡처, BLOCK/RECHECK provider 0, recipe ENTER_NOW→새 확인 fact/provider 원응답→동일 policy/source validator→기존 WAIT/probe 또는 BUY guard 경로. 정상 미통과와 원천 결손을 분리하며 적격 기회 없음은 `not_observed`; 실제 주문·체결·비용 수익을 코드 수리 조건으로 만들지 않는다.
  - 기존 `FixedWatchSourceAndCleanupRepair1006`, `DirectFamilySourceRepairMainMechanisticEntry`, `DirectFamilySourceRepairCompactAuxiliary`, `DirectFamilySourceRepairEntrySplit`, `JejuEpisodeRetirementHpspAlteogenMainFixedWatch`의 원천·장후·자연 수용 소유와 hard/source/account/order/quantity/cooldown/custody/veto guard를 보존한다.
  - 10/6 코드 수리·반복 리뷰 및 가격 manifest 소비 보완 완료: `fbfc9dd6`, Main PID `338586`/20:03 bootstrap PASS, 원 정책·PREOPEN 34개 SHA 보존, 에피소드 31개 profile·186개 pin 보존. 회귀 실행 1,877건 PASS(중복 포함); 454종목 가격 재계산 후 비삼성 현재 7/36승 대 D 16/102승, A/B/C/D/E 추가 완화 미선정. 현재 자연 KRX 정규장 recipe 수용은 `not_observed`, 다음 적격 session에서 해당 exact trace를 확인한다.
  - 날짜 인계: 10/6 원 Acceptance와 미관측 기록을 보존하며, 현재 실행 owner는 이 10/7 체크리스트이다.
