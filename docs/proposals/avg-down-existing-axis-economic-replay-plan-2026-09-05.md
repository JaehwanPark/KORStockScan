# AVG_DOWN 기존 튜닝축 경제성·자동화 개선 구현계획

작성일: `2026-09-05 KST`
상태: `implementation_review_complete_natural_runtime_evidence_pending` — 판정·계측 보완, 독립 상태 재현 코어, production cadence frame capture와 격리된 기존 holding/exit full-policy adapter를 구현·검증했다. 실제 자연 paired 표본, AI/PREOPEN/PID 소비와 수익 개선은 아직 확인하지 않았으며 live 준비 완료를 뜻하지 않는다. 현재 판정은 §0.3이 소유한다.
실행 항목 소유자: [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)의 완료 기록 `AvgDownFinalReviewRepair0907`과 OPEN 자연 원천 확인 항목 `AvgDownPairedExitRuntimeEvidence0907`이다.
원칙 소유자: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1~§8. 이 제안은 baseline 정책이나 현재 runtime owner를 대체하지 않는다.
기존 계약: [report-based automation traceability](../report-based-automation-traceability.md)의 AVG_DOWN recovery calibration 및 scale-in incremental counterfactual 행.

## 0. 1차 구현 종결 기록 (2026-09-05, 이후 판정은 §0.3)

- A(P0/P1): report schema v2와 `avg_down_route_arbitration_v2` 원천 계약을 적용했다. 구형 funnel/submit proxy는 진단으로만 세고, timestamp/file-date, exact lifecycle identity, 중복·상충 event/decision/terminal, 종료 성숙도, KRX/NXT scope, same current·AVG_DOWN/sizing/cost policy cohort를 검증한다. 신규 runtime 후보는 기존 `SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE` 한 키만 허용한다.
- B(P2/P3a): 기존 reversal → shallow → aggressive → ADM 순서와 실제 반환을 바꾸지 않는 fail-open route observer를 연결했다. Observer는 shallow 손익·보유시간 parent scope에서 80/85/90을 순수 재생하고 추가 account/API/AI/order를 만들지 않는다. 기존 비용 owner를 재사용한 fixed observed exit ADD/NO_ADD 증분은 source-only이며, 정상 NO_ADD 증분은 0이다.
- C(P3b/P4/P5): 유효 후보는 unique complete parent episode 10건, 비용 차감 B 순기여 양수, B-A 양수, 경제성 표본의 KRX/NXT 공통 scope가 모두 필요하다. Paired 권한에는 A/B/C별 완료 상태·독립 종료가격·동일 exit-policy version·고유 terminal source ID·exact decision ID가 필요하며 fixed-exit 이력은 paired floor에서 제외한다. 별도 +1%·target-hit·MFE/MAE 허들은 제거했다. Candidate ID/version/hash/key/current/recommended/date는 AI와 PREOPEN에서 재검증하고, 선택 시 비전략 provenance env가 PID event까지 이어진다. `selected/env_written/pid_verified/natural_match/terminal_attributed`는 별도 집계한다.
- 이전값 보존: 정상 `hold_no_edge`, `hold_no_change`, `hold_sample`, `hold_runtime_scope` 또는 통합 report 일시 누락은 안전/source-quality 위반이 없을 때 마지막 승인 AVG_DOWN env를 명시적으로 carry-forward한다. 신규 후보값으로 간주하지 않으며 legacy 다중 env는 migration 상태를 공개한 채 동작만 보존한다. source-quality hard block, safety revert, observed/current 충돌이면 유지하지 않는다.
- 당시 runtime 판정: 생산 v2 exact-route/paired-exit 표본은 확인되지 않았고 당시 observer는 의도적으로 `fixed_observed_exit_source_only`를 발행했다. 이 결손은 §0.2~§0.3의 production capture·full-policy replay 구현으로 보완했지만, 실제 임계값 후보·exact-date 적용·수익 개선은 다음 자연 실행 전까지 여전히 미확인이다.
- 권한 경계: 실주문·수량·횟수·cooldown·quote freshness·broker/account/order·hard/protect/emergency safety·provider·봇 상태와 새 +0.30% 익절은 변경하지 않았다. 운영 보고서 재생성, 봇 재기동, 수동 live env 적용도 이 구현 종결에 포함하지 않는다.

## 0.1 목적·자동화·달성 가능성 재점검 당시 발견 기록 (2026-09-05)

당시 판정은 **보완 필요**였다. 단일 기존 축, 비용 차감 증분 경제성, 불필요한 target-hit/MFE 허들 제거는 목적에 맞았지만 실제 생산자에서 승인 가능한 근거까지의 경로가 미완결이었고, 과잉 거절과 잘못된 근거 승인 가능성을 재현했다. 아래 R1~R7은 그 시점의 발견·acceptance 기록이며 §0.2~§0.3에서 보완했다. 현재 판정은 §0.3이 소유한다.

### 자동화와 실제 적용을 구분한 증거

- 설치된 cron은 평일 20:10 장후 wrapper, 07:35 `auto_bounded_live`/AI-required PREOPEN을 실행하도록 등록돼 있다. [장후 wrapper](../../deploy/run_threshold_cycle_postclose.sh)는 AVG_DOWN producer를 daily report/AI보다 먼저 호출하고, [PREOPEN consumer](../../src/engine/threshold_cycle_preopen_apply.py)는 단일 키·후보 identity·범위·출처를 재검증한다. 이는 호출 자동화의 근거이지 AVG_DOWN 개선의 실적용 근거가 아니다.
- [2026-09-04 생산 보고서](../../data/report/scalping_avg_down_recovery_calibration/scalping_avg_down_recovery_calibration_2026-09-04.json)는 여전히 schema v1, proxy 45건, `hold_no_edge`, `allowed_runtime_apply=false`다. [2026-09-07 apply plan](../../data/threshold_cycle/apply_plans/threshold_apply_2026-09-07.json)은 해당 family `selected=false`, `decision_reason=hold_not_previously_enabled`, direct report 계약 오류 `avg_down_report_schema_version_invalid`를 기록한다. 기존 AVG_DOWN 매매 기능 자체의 OFF를 뜻하지 않는다.
- [2026-09-07 env verify](../../data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-07.json)의 전체 `pass`와 달리 AVG_DOWN은 selected family에 없다. 해당 검증에는 `pid=null`, `pid_env_available=false`이므로 실행 프로세스의 신설 AVG_DOWN 후보 소비를 확인한 것도 아니다. 신규 v2 경제성·수익 증가·실체결 품질은 미확인이다.

### 발견 사항과 보완 기준

| ID / 우선순위 | 근거와 영향 | 보완 및 acceptance |
| --- | --- | --- |
| R1 / P1: paired 생산 경로와 관측 계약 단절 | [observer](../../src/engine/sniper_state_handlers.py)의 `_avg_down_route_arm_observation`은 모든 arm의 `exit_replay_method`를 fixed로 고정하지만 [경제성 evaluator](../../src/engine/monitoring/scalping_avg_down_recovery_calibration.py)의 `paired_ready`는 관측 arm부터 paired method를 요구한다. `avg_down_route_arbitration_terminal` 독립 A/B/C 생산자는 현재 engine/deploy에서 확인되지 않는다. 정상 paired terminal 10건을 추가한 합성 재현도 실제 observer 방식이면 paired 표본은 0건이다. | 원관측은 source-only로 불변 보존하고, 별도 검증된 replay 결과와 exact decision/episode로 결속해 method/authority를 판단하도록 계약을 분리한다. 기존 exit policy를 기록 입력으로 재현 가능한 범위에서만 생산하고, 불가능한 경로는 구체적 입력 결손과 함께 source-only로 종결한다. **실제 observer 형식 → replay producer → source audit → report → AI/PREOPEN 계약**의 통합 fixture를 통과해야 한다. 고정 종료 자료의 라벨만 바꾸는 승격은 금지한다. |
| R2 / P1: 다른 episode 종료 자료의 오결합 | `_collect_exact_evidence`는 explicit terminal을 decision ID로 찾은 뒤 terminal의 `position_episode_id`와 관측 episode를 비교하지 않는다. 10개 관측의 terminal episode를 모두 다른 ID로 바꿔도 `allowed_runtime_apply=true`; PREOPEN 단일 후보 validator도 오류 없이 통과했다. 실제 env 쓰기나 AI 승인을 실행한 재현은 아니다. | decision ID뿐 아니라 episode·symbol/venue·정책·시간·terminal source lineage를 결속한다. 불일치는 해당 비교에서 제외하며 제외 사유를 보고한다. 다른 episode/venue/정책 terminal은 report와 downstream 어느 단계에서도 유효 승격 표본이 될 수 없어야 한다. |
| R3 / P1: 참고용 EV가 authoritative paired 결과를 veto | paired-positive 10건에 fixed-exit-negative 20건을 더하면 paired EV는 +10.9%인데 mixed 진단 EV는 -2.966667%가 된다. `runtime_winner`가 있어도 `not source_winner` 분기에서 `hold_no_edge`, apply=false가 되고 feasibility는 동시에 `bounded_candidate_ready`다. 수치는 테스트용 합성값이지 운영 수익률이 아니다. | 충분한 paired 근거가 있으면 그 비교집합만 승격 경제성의 소유자로 삼는다. fixed 결과는 별도 진단·차이 설명으로 남기되 부정확한 가정으로 paired 결론을 자동 veto하지 않는다. 상충이 추가 조사 대상이면 명시적 조사 상태로 표현한다. state/feasibility/allowed flag가 일치해야 한다. |
| R4 / P1: 실포지션 수량 결손과 coverage의 무효 튜닝 오분류 | observer의 real ADD는 `proposed_add_qty=0`, `real_budget_not_available_without_extra_api_call`이며 calibration에 후속 sizing/receipt 보강 join이 없다. 후보 arm은 경제성에서 빠진다. 실제 producer 형태의 합성 입력은 후보 coverage가 없는데도 다른 무변화 arm 때문에 `hold_no_change`로 끝났다. 현재 shallow가 먼저 반환한 경우 tightening 후보의 미평가 ADM/LDM 경로도 비교에서 제외된다. | 이미 획득한 동일 decision의 예산·sizing·resolver snapshot을 재사용하는 보강 계약을 구현한다. 추가 API/AI/주문을 호출하거나 고정 수량으로 채우지 않는다. counterfactual downstream은 순수 재현 가능한 경우만 평가하고 나머지는 `coverage_gap`/구조 보완 대상으로 표시한다. 유효한 전체 경로 비교 없이 “축 효과 없음”으로 종결하지 않는다. |
| R5 / P2: 누적 판정에 불필요한 당일 route 발생 요구 | `build_report`의 current/cohort는 target-date route event에서만 정해지고 PREOPEN도 `same_day_runtime_route_event`만 허용한다. 누적 완결 paired 10건이 있어도 당일 이 경로가 발생하지 않으면 모든 비교 표본을 0으로 만들고 current 누락으로 차단한다. current freshness 요구는 타당하지만 우연한 당일 자연 기회까지 요구할 이유는 별도다. | 신뢰할 수 있는 source-date loaded env/PID/config snapshot으로 동일 current·전체 정책 버전을 확인하는 대체 계약을 검토한다. 검증 snapshot이 있고 동일 정책이면 당일 match 0이어도 누적 근거를 유지한다. 오래된 env나 코드 기본값 fallback은 계속 거절한다. |
| R6 / P2: 적용 후 귀속이 실제 효과와 다름 | observer의 `runtime_natural_match`는 selected shallow ADD에만 true다. 임계값 강화로 유효 NO_ADD가 된 행동 변화는 빠진다. report의 `terminal_attributed_count`는 같은 종료를 붙인 반복 decision마다 증가하며 별도 filled/unique attributed episode 및 해당 후보의 순익 비교가 없다. baseline의 PID 값 확인도 selected 후보 관측과 분리되지 않은 count에 포함된다. | selected candidate별 env/PID/match, 행동이 달라진 ADD와 NO_ADD, unique episode, 실체결 receipt와 terminal을 분리한다. 동일 episode 반복 event는 효과 표본을 늘리지 않고 후보 전후 같은 scope의 순익 차이만 성과로 보고해야 한다. |
| R7 / 설계 재검토: 모든 후보에 B 순기여 > 0 요구 | B가 정상 NO_ADD이면 C와 동일해 B-C=0이다. A-C가 음수이고 B-A가 양수인 개선도 `hold_no_edge`로 거절한다. 합성 재현에서 B-C=0, B-A=+11%가 거절됐다. 이는 §P4의 기존 엄격 양수 설계를 구현한 결과이며, 구현 누락과 구분해 목적 적합성을 재검토해야 한다. | ADD 확대 후보에는 비용 차감 B-C>0 및 B-A>0를 유지한다. 불리한 ADD를 제거하는 후보에는 유효 paired 근거로 B-C>=0, B-A>0 및 KRW 개선을 확인하는 방향별 판정을 검토한다. 결손을 NO_ADD=0으로 바꾸거나 실권한/source-quality guard를 완화하는 예외는 금지한다. |

R4의 episode 비교는 단순히 “첫 유효/유리한 행”으로 갈아끼워 해결하지 않는다. 당시 `_candidate_economics`는 첫 decision에서 episode를 점유하고 이후 판단을 제외했다. 계획의 최초 비교시점은 유지하되, 전체 A/B/C 상태·후속 leg 재현을 생산자가 소유해야 하며 미성숙 최초 판단을 건너뛴 사후 유리한 표본 선택은 금지한다. 당시 전체 AVG_DOWN·sizing·cost·exit 설정의 불변 fingerprint도 필요했다. 당시 observer의 고정 정책명 문자열만으로 전체 설정 동일성이 증명되지는 않았다.

### 조건 유지·보완·제거 판정

- 유지: source quality, 실제 체결과 sim/quote 분리, 독립 종료 정책 정합성, unique complete parent episode 10건, 한 축/최대 5%p, AI 후보 identity, same-stage owner, hard/broker/order/quantity safety. 10건이 통계적 충분성을 보장하지는 않지만 현재 병목은 자연 생산 가능한 유효 분모 자체가 없다는 점이다. 유효 일별 축적률을 확보하기 전 임의로 10→1 등으로 낮추거나 예상 달성일을 약속하지 않는다.
- 제거 완료 확인: +1% 개선율, +0.30% target-hit 비율, MFE/MAE 비율, Deep 동시 floor를 shallow 적용의 추가 필수 허들로 쓰지 않는다. 현실적인 가격 단위의 합성 paired 10건에서는 비용 차감 증분 EV **+0.087%, 합계 +870원**으로 `adjust_down`, apply 후보 true가 나왔다. 작은 양수 자체를 배제하는 수익률 허들은 확인되지 않았다. 운영 기대수익 추정치는 아니다.
- 보완/대체 검토: 당일 자연 route 의존을 검증된 config/PID provenance로 대체(R5), NO_ADD 개선에 대한 엄격 양수 조건을 방향별로 재설계(R7), 진단 EV의 숨은 추가 veto 제거(R3).
- venue 조건: 공통 env가 KRX/NXT 양쪽에 영향을 주는 동안 NXT-only 증거로 공통 변경하는 것은 계속 금지한다. 현재 코드의 무조건 `{KRX,NXT}` 요구는 검증된 실제 영향 venue 집합과 대조하는 계약으로 개선할 수 있다. 단일 venue가 유일한 실제 영향 범위라는 근거 없이 검사만 삭제하지 않는다.
- paired 경로의 재현 가능성이 낮으면 “표본 대기”로 무기한 두지 않는다. 재현 가능한 결정적 기존 exit 경로만 명시적으로 지원하거나 해당 부분을 source-only 분석으로 종결하고 live 자동 보정 완료 약속을 제거한다. 실적용 조건을 낮춰 생산자 결손을 우회하지 않는다.

### 검증 범위와 다음 순서

기존 AVG_DOWN calibration 테스트 **13건 통과**. 추가로 기존 fixture 생성기를 메모리 event 수집기로 대체하고 preflight를 정상으로 고정해, 정상 paired 대조군·실제 observer method·mixed EV·잘못된 episode·당일 관측 부재·NO_ADD 개선·real sizing 결손·작은 양수의 **8개 시나리오**를 검증했다. 정상 fixture는 통과하지만 생산 계약과 다른 branch를 미리 paired로 표시하므로 생산→승격 완결성을 증명하지 못한다. 오결합 후보는 PREOPEN 후보 validator에도 별도로 통과함을 확인했다. broker/API/AI 호출, env 쓰기, 운영 보고서 재생성, 봇 변경은 하지 않았다. 광범위 회귀는 이번 read-only 코드 리뷰에서 다시 실행하지 않았다.

당시 실행 순서는 **R2 오승인 차단 → R3/R4 판정·coverage 교정 → R1 실제 생산자와 소비자 통합 → R5/R6 및 R7 설계 결정 → 통합 회귀·재리뷰 → 허용된 자연 실행 증거 확인**이었다. 코드 보완 owner `AvgDownFinalReviewRepair0907`은 §0.3 기준 완료됐고, 자연 match/AI/PREOPEN/PID 확인은 OPEN `AvgDownPairedExitRuntimeEvidence0907`이 소유한다. 유효한 미래 표본이나 수익 개선 발생은 구현 완료와 구분한다.

## 0.2 확대 구현과 재검증 (2026-09-05)

사용자는 단순 source-only 종결 대신 **독립 청산 재현 엔진까지 확대 구현**을 선택했다. 아래 구현과 미완료 연결부를 구분한다. §0.1의 발견 기록을 삭제하거나 전체 완료로 덮어쓰지 않는다.

- R2: terminal의 decision뿐 아니라 episode, 원관측 ID, symbol/venue, AVG_DOWN/sizing/cost policy lineage를 대조한다. 다른 episode·정책 자료는 제외한다.
- R3: 충분한 paired 경제성은 mixed fixed-exit 진단과 별도로 판정한다. state/feasibility 모순을 제거했다.
- R4: 이미 끝난 실제 sizing 결과를 동일 decision·2초 이내·동일 원가/수량·동일 가격/기존 action에만 보강한다. 추가 account/API/AI 호출이나 가정 수량으로 채우지 않는다. 다른 action/가격/만료된 문맥, downstream/수량 결손은 `route_economic_coverage_gap`이며 무효 튜닝으로 종결하지 않는다. tightening에서 미평가된 기존 ADM adapter는 복사한 문맥의 결정적 조회로만 평가한다.
- R5: source-date의 실제 loaded rule/process env config가 일치하면 당일 shallow 자연 기회가 없어도 동일 정책 누적 근거를 보존한다. 코드 default fallback, PID 불일치, snapshot 권한 누수는 대체 원천이 아니다. 구조화 append 실패 시 다음 관측에서 재시도한다.
- R6: 이전 pressure를 비전략 provenance로 전달하고 유효 NO_ADD 전환을 계측한다. selected PID와 baseline PID, observation 수와 unique candidate/episode, 행동 변화와 terminal을 분리한다. 실제 ADD receipt 및 실현 개선은 아직 추정하지 않으며 `realized_improvement_claimed=false`다.
- R7: ADD 확대에는 B-C>0와 B-A>0를 유지한다. ADD를 제거하는 tightening은 추가 ADD가 없고 제거 ADD가 있을 때 B-C>=0, B-A>0 및 KRW 개선을 허용한다. 별도 +1% 허들은 없다. 누락된 수량을 NO_ADD 0으로 만드는 예외는 없다.
- 추가 수정: 당시 cost policy의 rate로 비용을 한 번만 계산한다. 현재 프로세스 rate로 과거 결과를 바꾸지 않는다. 비용 버전이 해석되지 않으면 결손이다. NO_ADD의 거절 문구 차이만으로 행동 변화라 하지 않으며 throttled/append 실패 관측에 sizing 자료를 연결하지 않는다.

### 독립 엔진의 구현 경계

새 [avg_down_replay.py](../../src/engine/lifecycle/avg_down_replay.py)는 **offline lifecycle evidence** 소유다. 새 튜닝축, engine-root module, cron 또는 주문 실행기를 만들지 않는다. 기존 AVG_DOWN postclose producer가 매 실행에서 `independent_exit_replay`를 계산하며 wrapper checkpoint dependency에 새 엔진을 포함한다.

- A/current, B/grid, C/NO_ADD가 각자 수량·평단·leg·peak·policy state·pending order로 진행한다. 후속 ADD, 만료 후 명시적 CANCEL_ADD, 경로별 HOLD/EXIT와 독립 종료를 지원한다.
- 당시 비용률, 최초 비교시점 고정, clean baseline, observation/frame/episode/symbol/venue/policy ID, frame 순서·중복·상충, full-policy input digest/cutoff/state-after를 검증한다. 다른 경로의 AI 결과를 복사하지 않는다.
- 기록된 `avg_down_exit_replay_frame_observed`와 exact-state full-policy evaluation을 읽는다. 프레임은 원관측 뒤 별도 이벤트로 연결하며 미래 자료를 최초 관측에 끼워 넣지 않는다. 정책 판정이 없으면 상태·market·input digest가 붙은 `replay_requests`를 만든다. quote/정책/sequence 결손과 미종료는 이유별 blocker로 남긴다.
- quote-touch full fill은 가정 체결이다. partial ADD/EXIT는 full fill로 합치지 않고 명시적 미지원 결손으로 닫는다. 완결된 결과도 outcome과 report 모두 `source_only_paired_exit_replay`이며 `allowed_runtime_apply=false`, `runtime_authority_ready=false`다. 기존 runtime-authoritative terminal 파서로 이 outcome을 복사해도 승인 표본이 되지 않는다.

**당시 남은 구현 작업(R1):** 이 시점에는 production 원관측 full holding/exit policy snapshot, 연속 frame 생산자와 기존 전체 holding/AI/청산 정책 adapter가 연결되지 않았다. 이 기록은 §0.3의 후속 구현으로 종결됐으며, 당시 callback/합성 fixture만으로 완료를 주장하지 않았던 이력을 보존한다.

검증은 synthetic state/price/full-policy fixture, 원관측→별도 frame→기존 postclose producer, source-only 권한 보존, sizing/config 계측, AI/PREOPEN identity 및 주변 PYRAMID 회귀를 대상으로 한다. 이는 실제 수익 증가·실체결 품질의 검증이 아니다. 봇 재기동, live env 선택, 운영 산출물 재생성은 수행하지 않았다.

## 0.3 Production capture·full-policy adapter 구현 종결 (2026-09-05)

- `src/engine/scalping/avg_down_replay_capture.py`가 최초 AVG_DOWN 원관측의 loaded rule/env, 외부 policy file, ADM/LDM matrix 선택, holding state, AI budget과 implementation identity를 credential 제외 frozen snapshot으로 고정한다. 기존 source-only cadence는 이미 구독한 WS cache에서 1초 frame을 bounded 수집하고 누락·지연·quote conflict를 gap으로 남긴다.
- `src/engine/lifecycle/avg_down_policy_replay.py`가 disposable interpreter에서 기존 fast-exit와 holding policy를 A/current, B/candidate, C/NO_ADD 가상 상태별로 실행한다. virtual order/receipt와 frozen file/clock/input만 허용하고 미기록 외부 I/O·AI·부분체결은 `ReplayInputGap`으로 차단한다.
- 기존 holding policy가 AI를 요구하면 exact input digest·cutoff·policy version에 결속된 현재 prompt/provider replay만 bounded postclose에서 보충한다. 이 호출은 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`이며 실주문·runtime provider 변경 권한이 없다.
- main runtime cadence, AVG_DOWN observer, source-quality audit, calibration, daily AI, PREOPEN 단일축 validator, postclose verifier와 wrapper checkpoint dependency가 연결됐다. 현재값 동등성·source-only 권한·서로 다른 episode/policy/venue 결속·mixed diagnostic EV 분리·ADD 제거 tightening·unique attribution 계약을 유지한다.
- 후속 리뷰 보완: 실제 로그의 문자열 수량/평단 정규화, source/decision 재결속, 저장된 EXIT 라벨의 adapter 우회 차단, loaded helper/class code identity, AI 엔진 상태와 LDM counter의 arm별 독립성, credential 제외와 AI token-budget 보존, policy file 압축 해제 한도, SQLite/socket/file-write 차단을 확인했다. 이미 종료한 경로는 이후 관측 gap으로 무효화하지 않되 상충 duplicate는 전체 source conflict다.
- 운영 비용: 기존 observer는 episode 7,200 frame/32 MB·동시 8개·일별 frame payload 256 MB로 제한하며 큰 snapshot의 text 중복을 제거했다. AI replay는 episode 16회/180초, report 64회/600초다. 검증된 과거 결과는 동일 source-file size/mtime·implementation·observation/result digest일 때만 재사용하고 exact-policy/input/cutoff 응답을 다음 날짜에도 보존한다. source-only 결과 캐시는 live 후보 권한 캐시가 아니다.
- 검증 범위와 잔여 위험: 실제 producer 형식의 JSONL→수집기→기존 fast-exit→독립 종료→보고서 및 캐시 재사용 통합 테스트를 포함해 **2,503 passed**, 기존 pandas-ta 경고 1건이다. 변경부 Ruff·compile·wrapper 문법·diff·checklist parse를 통과했다. 기동 모듈의 기존 lint 93건은 HEAD와 동일하며 신규 증가가 없다. 구현 범위 내 미해결 review finding은 없고, 실환경 AI 유료 호출·봇 재기동·운영 report 재생성·실주문/PREOPEN 적용은 수행하지 않았다.
- 지원 경계: fresh/conflict-free BBO의 full quote-touch 가정, 기록 입력을 사용하는 기존 정책, single-limit 후속 ADD 경계를 지원한다. 부분체결, split/market ADD, 미기록 account/AI/정책 입력은 임의 full fill/HOLD나 가짜 잔고로 보충하지 않는다. zero-latency policy 평가와 virtual order acceptance/durability는 명시적 모델 가정이며 실제 execution quality가 아니다.
- 다음 자연 거래일에 source/정책/AI/input gap과 비용 차감 B-A/B-C를 확인한다. **독립 재현이 완료되어도 그 quote 가정 outcome은 source-only다.** 표본 증가만으로 기존 runtime-authoritative terminal 계약이 닫히거나 PREOPEN이 선택되는 구현은 아니다. source-only→실권한 전환은 별도 운영자 승인 범위이며, 승인 근거·AI/PREOPEN 선택·PID 소비·post-apply EV가 확인되기 전 실적용·수익개선 완료로 판정하지 않는다.

## 1. 구현 방향과 성공 기준

기존 `scalping_avg_down_recovery_quality_gate`를 유지하고, 고정 설정 26개를 한꺼번에 복원하는 producer를 **동일 기회의 비용 차감 증분 경제성으로 기존 값 하나만 추천하는 producer**로 개선한다. 별도 family, cron, approval owner, shadow 매매, 수량 튜닝축을 만들지 않는다.

초기 보정 대상은 `SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE` 한 키다. 기존값 85는 수익 목표나 최적값이 아니라 현재 설정의 코드 기본값이다. 선정 이유는 기존 shallow 경로의 관측 가능한 품질 조건이고 손익 구간·보유시간·매도정책·횟수·신선도를 동시에 바꾸지 않고 비교할 수 있기 때문이다. 이 값의 경제적 유효성은 아직 증명되지 않았다. 다른 AVG_DOWN 경로가 같은 주문을 허용해 최종 행동이 바뀌지 않으면 후보를 생성하지 않는다.

성공 기준은 세 가지를 분리한다.

1. 구현 품질: 중복·미체결·미종료·비용·권한 혼합 없이 기회, 차단, 종료와 결손이 대사된다.
2. 경제성: 현재값 A, 한 단계 후보 B, 추가매수 없음 C를 같은 기회에서 비교하고 B의 양의 비용 차감 순기여와 B-A 개선 여부를 판정한다. 작은 개선에 별도의 +1% 수익/개선 허들을 추가하지 않는다.
3. 적용 품질: 분석 완료, 후보 검토, PREOPEN 선택, PID/runtime 소비, 적용 후 성과를 별도 상태로 보고한다. 분석 코드 완성을 실매매 수익 증가 또는 실적용 완료로 보고하지 않는다.

기대효과는 허위 회복 표본과 무효 튜닝을 줄이고 작은 순기여 후보를 식별하는 것이다. 수익 증가 자체는 이후 검증 대상이다. 유효한 후보가 없다는 재현 가능한 결론도 평가기 개선의 정상 완료 결과다.

## 2. 출발점과 결함 대응

2026-09-04 생산 보고서는 shallow 38건, deep 7건으로 기존 표본 기준 10/5를 충족하지만 `hold_no_edge`다. 보고서상 최종 관측 수익률은 각각 약 -0.539%, -0.681%이며, 이는 아래 계약 보완 전의 proxy이지 실제 추가매수 증분 순익이 아니다. 기본값과 고정 추천값도 같아서 증거가 좋아져도 `hold_no_change`다.

관련 증거:

- [AVG_DOWN 최근 보고서](../../data/report/scalping_avg_down_recovery_calibration/scalping_avg_down_recovery_calibration_2026-09-04.md)
- [장후 AI 검토](../../data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-09-04_postclose.md): 해당 family가 검토됐으나 문자열 제안이 `proposed_value_not_numeric_or_bool`로 거절됐다.
- [9월 4일 PREOPEN](../../data/threshold_cycle/apply_plans/threshold_apply_2026-09-04.json): 9월 3일 source의 해당 family는 `runtime_apply_not_allowed`로 미선택됐다. 보정 미선택은 기존 AVG_DOWN 기능 OFF와 다르다.
- 코드 감사의 메모리 내 재현: 제출 1초 뒤 mark가 30분 결과로 인정됐고 중복 제출이 두 표본으로 집계됐다. 좋은 합성 표본에서는 횟수 1→2 및 허용 quote age 500→1,500ms의 묶음 추천에 적용 계약 blocker가 없었으며, 다른 quality ID의 AI 승인도 허용됐다. 운영 설정이나 생산 보고서를 변경한 재현은 아니다.

| 결함 | 보완 단계 | 핵심 완료 기준 |
| --- | --- | --- |
| 고정 33% 추가 가정, 원포지션 수익률을 추가분 경제성으로 사용 | P1, P3 | 실제/가정 가격·수량·비용 출처 분리 및 ADD/NO_ADD 손계산 일치 |
| 1초 mark, 미체결, 중복을 완료 표본으로 인정 | P1 | unique episode/decision/receipt와 명시적인 maturity·fill 상태 검증 |
| sim funnel의 금지된 runtime 표본 사용 | P0, P1, P4 | 원천 authority 보존, diagnostic과 실적용 근거의 분모 분리 |
| shallow/deep 동시 통과와 고정 추천 | P4 | 경로별 판정, 기존 품질값 한 개만 추천, 무효 축 명시 종결 |
| 횟수·quote freshness·여러 값이 한 번에 변경 가능 | P0, P5 | producer와 PREOPEN 독립 allowlist 및 exactly-one-changed-key 검사 |
| +0.30% TP 및 deep emergency 값에 실제 실행 소비자가 없음 | P0, P3 | 자동 추천에서 제거하고 진단/호환 필드로 표시; 새 매도·안전 기능은 만들지 않음 |
| AI와 후보 증거 identity 미결속 | P5 | date/ID/hash/schema/current/recommended 불일치 시 env 없음 |
| 여러 AVG_DOWN 허용 경로로 인한 귀속 혼합 | P2, P3 | 기존 우선순위 보존, 최종 행동·상태 변화 기준 counterfactual |

## 3. 통폐합 경계와 변경하지 않을 것

통폐합은 우선 **증거 계약·순수 계산·최종 선택 귀속의 통합**이다. 서로 다른 전략을 한 손익 버킷으로 합치거나 기존 허용 경로를 무조건 차단하는 방식이 아니다. LDM/ADM의 기존 runtime 권한 및 hard-safety 우선순위는 그대로 둔다.

| 대상 | 계획 |
| --- | --- |
| reversal, shallow, aggressive, ADM AVG_DOWN 제안 | 하나의 decision ID와 공통 결과 계약으로 연결한다. 기존 반환 순서를 보존하는 단일 평가 진입점을 구성하되 각 경로의 조건·이유·used-count 의미는 분리한다. |
| deep recovery, late-loss retry | 별도 하위 경로와 stop/exit 문맥으로 유지한다. shallow와 EV/표본을 합치지 않고 공통 receipt·비용·종료 계산만 재사용한다. 이번 v2 초기 자동 조정 대상은 아니다. |
| `scalping_avg_down_recovery_quality_gate` | 기존 direct calibration 소유자로 유지한다. 초기 live-target allowlist는 shallow buy-pressure 한 키뿐이며 LDM을 대체하지 않는다. |
| 과거 shallow/deep quality family명 | PREOPEN prefix 호환 문자열과 실제 producer/현재 selected owner를 구별한다. 활성 소비자가 없는 문자열만 후속 정리 대상으로 식별하고 이력 파싱은 유지한다. |
| `scale_in_incremental_counterfactual` | 공통 가격/추가분 순익 계산을 재사용한다. 기존 `runtime_authority_ready=false` 의미와 sim-only 출력 계약을 바꾸지 않는다. |
| PYRAMID, sizing, price resolver, broker guard | 통합하지 않는다. PYRAMID와 같은 scale-in stage의 누적 품질 갱신은 기존 최대 1건 선별을 유지한다. |

금지/제외 범위: enable 토글, 손익·보유시간 구간 변경, requested quantity·수량 공식·position/day cap·추가 횟수·cooldown, quote freshness, price/order/broker/account, hard/protect/emergency stop, provider, 봇 상태, 새로운 익절·매도 정책. 초기 추천 목록에서 `*_MAX_PER_POSITION`, `*_MAX_QUOTE_AGE_MS`, `*_POST_ADD_TAKE_PROFIT_PCT`, `DEEP_RECOVERY_AVG_DOWN_EMERGENCY_PCT` 등을 제외한다. 효과 없는 설정은 reader·운영 override 의존성을 확인한 뒤 진단/호환 필드로 남기며 실제 다른 안전장치를 삭제하지 않는다.

실제 경로 우선순위 변경·경로 폐기·새 +0.30% 익절 구현이 필요하면 이 계획에 숨겨 넣지 않고, 전후 행동·영향 포지션·근거를 제시하는 별도 승인 범위로 분리한다. 계획의 `Due`는 검토 일정이지 실매매 적용 기한이 아니다.

## 4. 단계별 구현계획

### P0. 잘못된 자동 추천 경로부터 제한

변경 위치: `scalping_avg_down_recovery_calibration.py`, `threshold_cycle_preopen_apply.py` 및 관련 기존 테스트.

- v2 계약에서 `target_env_keys`를 초기 단일 키로 제한한다. candidate 단일성과 변경값 단일성을 각각 검사한다. 모든 값의 강제 emit을 제거하고 실제 변경된 전략 값만 출력한다. provenance 메타데이터는 전략 변경키 수에 넣지 않되 별도 allowlist를 둔다.
- 금지키, 둘 이상의 변경, finite 아닌 값, 누락 current, bounds/step 불일치, old schema, source-only evidence의 실권한 승격을 producer와 PREOPEN 양쪽에서 거절한다. generic `allowed_runtime_apply=true`만 신뢰하지 않는다.
- v1 결과는 `legacy_proxy_diagnostic`으로 읽을 수 있으나 새 live 추천 근거로 사용하지 않는다. AI의 오래된 family 승인으로 v1을 복구하지 않는다.
- report schema는 v2로 올리고 `evidence_contract_version=avg_down_paired_economics_v2`를 명시한다. 그 안에서도 `evaluation_method`와 `evidence_authority`를 별도 검증하여 fixed-exit source-only 결과가 v2라는 이유만으로 승격되지 않게 한다. 기존의 횟수 증가와 다중 ENV emit을 정답으로 기대하는 테스트는 v1 진단 호환/신규 적용 거절 테스트로 전환한다.
- 기존 baseline 실행 ON/OFF는 변경하지 않는다. 이전 사용자 override·보유 상태·다른 family env를 삭제하거나 기본값으로 덮어쓰지 않는다. 기존 AVG_DOWN 선택 이력이 있는 경우에는 마지막 승인값·출처와 신규 계약의 migration을 대조하고, 불명확하면 자동 초기화하지 말고 `hold_runtime_scope`로 명시한다.
- 회귀 fixture: 횟수 1→2, quote age 500→1,500ms, 두 품질값 변경, disabled→enabled, TP/emergency 키, 다른 family 키, v1 candidate는 모두 무단 env 생성 없이 거절된다.

완료 기준: 알려진 다중값·금지값 통과 재현이 차단되고 기존 정상 family/명시적 사용자 override 처리에는 회귀가 없다. 이 단계 완료만으로 봇 재기동하거나 실제 env를 적용하지 않는다.

### P1. 정확한 기회·체결·종료·source authority 계약

변경 위치: 기존 calibration `_iter_events`/`_build_rows`, `sniper_state_handlers.py`의 scale-in 계측, `observation_source_quality_audit.py`, 기존 receipt/terminal 소비 경로.

- 기존 event에 `schema_version`, `source_event_id`, `position_episode_id`, `scale_in_decision_id`, symbol, venue/session, decision timestamp, 경로, original-entry lineage를 연결한다. episode ID는 날짜별 record ID를 단순 재생성하지 않고 overnight/carry를 포함한 실제 소유 생명주기를 보존한다. 구형 ID가 모호하면 합성하지 않고 제외한다.
- 중복 동일 event/receipt는 한 번만 센다. 같은 ID의 상충 내용은 source gap이다. 반복 판단은 독립 체결 표본이 아니며 같은 episode의 여러 추가 leg는 횟수·노출을 보존하되 표본 수를 부풀리지 않는다.
- 당시 configured/effective 값, 전체 AVG_DOWN 정책 버전, PID/env source, 실제 decision trace, 현재 보유 원가·수량, BBO·timestamp·route, 기존 resolver의 가격/허용 이유, 동일 sizing owner의 결과를 저장한다. 관측 계측 때문에 추가 AI/API 호출, quota 소비, lock/cooldown 갱신 또는 주문을 만들지 않는다.
- 증거 계층을 `gate_observed`, `submit_evaluable`, `quote_counterfactual`, `real_fill_completed`로 구분한다. gate 관측에 실제 fill을 요구하지 않으며, 반대로 quote 관측을 fill로 취급하지 않는다. 대상 pressure 조건의 pass/blocked 양쪽에서 이미 계산된 입력을 보존하고, 당시 실행하지 않은 downstream 판단은 unknown으로 둔다.
- 주문 제출, 취소/미체결, 부분체결, 완전체결, pending receipt, 포지션 종료를 분리한다. Deep의 submitted 이벤트는 fill 증거가 아니다. 실제 성과에는 `COMPLETED + valid profit_rate`와 연결된 가격·수량·비용·terminal receipt의 일관성을 확인한다.
- 30분 horizon 진단은 horizon 도달 여부와 종료시점을 명시한다. 30분 이전에 실제 종료됐다면 `completed_before_horizon`, 종료 없이 관측만 끊기면 `pending_outcome` 또는 `coverage_gap`이며 1초 mark를 `final_30m`으로 치환하지 않는다. 주 경제성은 P3의 실제 종료 정책 기준으로 평가한다.
- 원천별 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 보존한다. `scalp_sim_scale_in_candidate_funnel`은 기회 분모 진단일 뿐 runtime EV 표본이 아니다. 완결 sim counterfactual도 실체결로 승격하지 않는다.
- clean baseline `2026-06-05T00:00:00+09:00` 이후의 각 source-date preflight와 실제 event timestamp를 검사한다. 가능한 결손 row/window만 제외하고 전체 block은 기존 preflight 정책을 따른다. malformed/missing/nonfinite를 0으로 정규화해 EV에 넣지 않는다.
- `raw_event_count`, `duplicate_event_count`, `unique_decision_count`, `unique_episode_count`, terminal 상태별 count, `excluded_by_reason`을 구별한다. unique episode의 최종 상태는 mutually exclusive하게 대사하고 이벤트 단계 count는 중복 합산하지 않는다.

완료 기준: 1초 mark·중복·취소·부분체결·overnight·다른 venue·원가 변경·미래시각·source quality 제외 테스트가 통과한다. 9월 4일 proxy 45건을 억지로 유지하지 않고 새 계약 기준 유효/진단/pending/결손으로 다시 분류할 수 있다.

### P2. 행동을 보존하면서 중복 판단과 귀속 통합

변경 위치: `sniper_scale_in.py`의 reversal/shallow/aggressive 평가와 `sniper_state_handlers.py`의 호출 경계, `holding_exit_matrix_runtime.py`의 AVG_DOWN adapter.

- 먼저 현재 호출 순서·조기 반환·상태 변경을 characterization test로 고정한다. 입력은 얕은/깊은 손실, micro/AI, quote, holding, quota/lock, source-gap recheck, ADM/LDM active owner를 포함한다.
- 순수 판단과 실행 시 상태 변경을 분리한다. 기존 `evaluate_scalping_reversal_add`와 ADM adapter를 재사용하는 평가 진입점에서 `candidate_routes`, `selected_route`, `rejection_reasons`, `not_evaluated_routes`, `shared_safety_veto`를 반환한다. 실제 런타임에서 평가하지 않은 후속 경로를 pass/false로 꾸미지 않는다.
- 현재값 replay의 최종 action, reason, selected owner, resolver/sizing 입력과 used-count/cooldown 상태 전이가 기존 호출과 같아야 한다. replay는 globals/env/time/stock을 직접 변경하지 않으며 과거 AI 결과를 새로 호출하지 않는다.
- 후보 평가에서는 buy-pressure 한 값만 바꾸고 기존 전체 선택 순서를 재현한다. shallow가 거절돼도 aggressive/ADM이 같은 실행을 하면 `no_effect_after_route_arbitration`이다. 경로 이유만 같거나 다르다는 사실이 아니라 주문·수량·후속 상태를 포함한 행동 동등성으로 판단한다.
- 기존 동일 단계 owner가 직접 후보를 덮어쓰거나 선정 권한이 충돌하면 이를 명시한다. 기존 LDM/ADM 안전 우선순위를 바꾸거나 shallow gate를 전 경로 공통 hard veto로 격상하지 않는다.
- Deep·late-loss는 실행기 통폐합 대상에서 제외하고 공통 증거 adapter만 연결한다. 매도 신호를 지연시키는 새로운 행동을 추가하지 않는다.

완료 기준: 현재값 동등성 위반 0건, 평가 과정의 추가 주문/AI/quota/state mutation 0건. 무효 튜닝은 성공 후보가 아니라 경로 중복 근거로 보고한다. 기존 경로의 폐기는 별도 효과 검증/승인 없이 수행하지 않는다.

### P3. ADD / NO_ADD 경제성 재현과 종료 정책 정합성

변경 위치: calibration 내부 계산, `scale_in_incremental_counterfactual.py`의 재사용 가능한 순수 계산, `trade_profit.py`의 기존 비용 owner. 기존 모듈의 private helper 전체를 무검증 재사용하지 않고 가격·rounding·비용 계약부터 손계산 fixture로 확인한다.

- A=current policy, B=buy-pressure 한 단계 후보, C=no additional buy를 동일 episode universe에서 비교한다. 시점마다 당시까지 알려진 데이터만 사용하고 미래 최고가로 추가매수 기회를 고르지 않는다. 다중 추가가 있으면 앞선 추가가 뒤 판단·평단·수량에 미친 영향을 보존한다.
- 비교 universe와 최초 비교시점은 후보값이나 후행 손익을 보기 전에 고정한다. 현재 shallow의 손익/보유시간 scope에 들어온 기존 평가 이벤트를 시작점으로 삼고, 다른 경로 선점·pressure 차단·정상 NO_ADD도 대사한다. 후보가 통과한 행만 사후 선택하지 않는다. 원천에 현재 통과 표본만 있어 완화 후보 구간을 관측하지 못했다면 `coverage_gap`이며 해당 완화 효과를 추정하지 않는다.
- 가격은 동일 venue/session의 fresh BBO 및 기존 resolver 또는 실제 fill을 사용한다. fixed 33%나 수익률 역산 가격으로 누락을 채우지 않는다. 수량은 기존 sizing 공식·cap을 고정해 계산하고 실제/가정 수량을 구분한다.
- P3a는 `fixed_observed_exit_counterfactual`로 구현한다. 실제 관측 종료가격을 고정하고 추가분의 비용 차감 기여를 계산하되 **source-only**로 제한한다. 이 결과는 평단 변경에 따른 stop/trailing/holding 변화까지 재현한 인과 효과가 아니다.
- P3b는 기존 exit policy와 기록된 입력으로 A/B/C의 상태·종료를 독립 재현할 수 있는지 판정한다. 평균단가 변화로 exit가 달라지거나 새 AI 응답이 필요하지만 그 경로가 재현 불가능하면 `requires_paired_exit_replay`로 닫는다. 고정 종료 분석에 승인 플래그만 붙여 승격하지 않는다. 모든 경로를 무리하게 구현하지 않고 재현 가능한 범위를 명시한다.
- +0.30% target-hit와 MFE/MAE는 진단으로 남긴다. 초기 버전은 기존 매도 정책을 평가하며 새 +0.30% 익절을 실행하지 않는다. 기존 정책으로 순기여가 없으면 `hold_no_edge`이고, 이를 해결하려고 추가매수 승인에 익절 변경을 섞지 않는다.
- 비용은 추가 leg 수수료·세금을 공통 cost owner로 한 번만 차감한다. 과거/상품별 비용 basis·버전과 이미 net인 입력을 구분한다. 사용자 목적에 맞게 별도 slippage penalty는 기본 지표에 추가하지 않으며 BBO/실체결 가격에 내재한 spread·체결 차이를 다시 차감하지 않는다.

지표 계산 계약:

- `delta_pnl_X = net_pnl(X) - net_pnl(C)`. C의 증분 0은 원포지션 전체 손익 0이 아니다. 실제 fill 성과와 반사실 delta는 별도 evidence class다.
- `source_quality_adjusted_ev_pct(X) = mean(100 * delta_pnl_X / reference_notional)`로 같은 비교 가능 episode 집합에서 계산한다. `reference_notional`은 각 episode의 첫 비교시점 추가매수 전 보유원가금액으로 고정하며 A/B/C 모두 같다. 가격·수량·비용이 필요한 주 지표이고 거래 발생 표본만 골라 평균내지 않는다.
- `notional_weighted_ev_pct(X) = 100 * sum(delta_pnl_X) / sum(reference_notional)`와 증분 순익 KRW를 함께 보고한다. `equal_weight_avg_profit_pct`는 실제/가정 추가 leg 발생 표본의 평균으로 별도 표기한다. 실제 `primary_ev` 판정 필드명은 이 세 canonical 이름만 사용한다.
- 완결된 정상 NO_ADD 기회는 증분 0, 어느 한쪽의 결과/가격/수량이 미확인이면 paired 비교 양쪽에서 제외하고 제외율·이유를 공개한다. 데이터 결손을 행동 NO_ADD로 위장하지 않는다.
- candidate scope의 B 순기여 > 0 및 B-A > 0과 KRW 순기여 방향을 확인한다. sim/quote 가정/full fill/partial fill을 합치지 않는다. KRX/NXT, owner, 정책 버전이 다른 손익을 무검증 공통값으로 풀링하지 않는다.

완료 기준: 비용 1회·분모·rounding·음수 기여·평단 변화·다중 leg·조기 종료·미종료·미체결 fixture의 손계산 일치. P3a 완료와 P3b/runtime 근거 준비 여부를 따로 보고한다. 기존 sim incremental 보고서의 `runtime_authority_ready=false`는 유지한다.

### P4. 기존 단일값 후보와 과도한 조건 정리

변경 위치: calibration의 `_current_values`, 고정 `recommended` 생성, `decision_guards`, metric/runtime update contract 및 상태 출력.

- 초기 tunable allowlist는 `SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE` 한 키다. 다른 기존 값은 replay의 고정 입력이다. Deep 후보를 추가하거나 여러 파라미터 중 당일 성과가 좋은 것을 동시에 최적화하지 않는다.
- 초기 **제안** 탐색 범위는 buy-pressure 80/85/90%, 한 단계 최대 5%p다. 이는 수익률 5%가 아니라 매수압도율 단위이며, 작은 국소 민감도 비교를 위한 설계값이지 기존 승인 bounds 또는 수익 근거가 아니다. 실제 current는 검증된 source-date env/PID/event provenance에서 읽고 코드 기본값으로 대체하지 않는다. 범위 안의 비정렬 current도 정확히 비교하며 양쪽 인접 grid 중 최대 변경폭 안에 있는 후보만 평가한다. 현 current가 제안 범위 밖이면 기존값을 강제 복원하지 않고 정확한 현재값 비교와 `hold_runtime_scope`를 남긴다.
- 위 범위의 PREOPEN 사용은 구현 리뷰에서 bounded-tunable 계약·현재 owner와 일치함을 확인하고 candidate/consumer에 같은 versioned bounds를 넣은 뒤에만 가능하다. 확인 전에는 source-only grid이며 범위/변경폭 자동 확대는 금지한다. 이 계획 자체는 live env 선택 승인이 아니다.
- shallow의 기존 10건은 초기 **해당 경로의 unique complete eligible parent episode** 기준으로 유지한다. source-only 분석의 표본과 실권한 계약에 사용 가능한 표본 수는 별도 필드로 보고한다. 구형 sim funnel 38건을 그 실권한 분모로 재사용하지 않는다. Deep 5건은 Deep 진단에만 유지하며 shallow 후보에 AND로 요구하지 않는다. child별 추가 10건, 모든 window 동시 양수, 별도 +1% 개선율 조건을 만들지 않는다. 미승인 후보를 실제로 먼저 거래해 표본을 채우라는 순환 조건도 만들지 않는다.
- daily는 운영/source-quality 진단, clean-baseline cumulative 및 동일 policy-version window는 추천 근거로 구분한다. 기존 rolling window는 최근 방향과 변화 탐지에 사용하고 서로 다른 버전의 평단/매도 정책 손익을 같은 근거로 섞지 않는다. 탐색에 쓴 표본을 독립 검증이라 부르지 않는다. 후보 고정 뒤 시간순 후행 검증의 성숙도·방향을 별도로 보고하고 명시된 기존 승격 계약을 따른다.
- +0.30% 도달률 25%/50%, MFE/MAE 비율 1.0, 고정 30분 마지막 mark 양수는 경제성 승격의 중복 필수조건에서 제거하고 진단으로 전환한다. 이를 제거한 자리는 유효한 종료정책의 비용 차감 순기여·B-A 비교가 대체한다. source quality와 hard safety는 완화하지 않는다.
- source-only 경제성 양수는 `economic_candidate_source_only`이며 실권한 후보가 아니다. P3b의 재현 계층, 허용된 source authority와 real receipt evidence, 기존 동일 단계 승격 계약이 닫혔을 때만 `allowed_runtime_apply=true`가 가능하다. LDM bridge 경로로 보내는 경우에는 그 소유 계약을 따르고 direct family를 이용한 우회 승격을 만들지 않는다.
- 초기값·step·범위를 바꿔야만 효과가 나거나 최종 행동 변화가 없으면 임계값을 무한 탐색하지 않는다. 다른 기존 값으로 보정 대상을 교체하는 것도 근거와 계약 버전 변경으로 별도 검토하며 새 동시 튜닝축으로 추가하지 않는다.

| 종결 상태/이유 | 다음 재평가 trigger |
| --- | --- |
| `source_quality_blocked` | 해당 원천/계약 복구 또는 새 정상 구간 |
| `hold_sample` / `pending_outcome` | 새 unique 완결 표본; 예상 도달일을 근거 없이 약속하지 않음 |
| `hold_no_change:no_effect_after_route_arbitration` | 경로 통폐합 검토 결과 또는 정책 버전 변경 |
| `hold_no_edge:economic_hypothesis_rejected` | 새 완결 표본 또는 명시적으로 변경된 가설/비용 계약 |
| `requires_paired_exit_replay` | 기존 정책의 독립 상태·종료 재현 가능성 확보; 단순 표본 대기와 구분 |
| `hold_runtime_scope` | source 권한, same-stage owner, venue 또는 bounds 계약의 구체적 결손 해소 |
| `candidate_reviewed_preopen_pending` | 정확한 다음 PREOPEN 선택 및 runtime provenance |

새 상태를 기존 consumer가 모르면 호환 가능한 calibration state와 별도 reason으로 직렬화하고 테스트한다. 같은 evidence hash는 계산 결과를 재사용할 수 있지만 날짜별 preflight와 maturity는 다시 확인한다. 동일 자료로 매일 무제한 AI 재시도하지 않는다.

완료 기준: Deep 부족만으로 shallow 후보가 막히지 않고, 최종 행동이 같으면 후보가 없으며, 작지만 양의 유효 순기여 후보가 불필요한 hit-rate/MFE 비율 허들로 거절되지 않는다. 경제적 이유가 없는 후보를 통과시키는 예외는 없다.

### P5. AI → PREOPEN → runtime → attribution 동일 후보 연결

변경 위치: `daily_threshold_cycle_report.py`, `threshold_cycle_preopen_apply.py`, `verify_threshold_cycle_postclose_chain.py`, 기존 runtime 계측 및 postclose wrapper의 해당 family checkpoint.

- candidate에 source/target date, family/stage/route, `quality_update_id`, `evidence_contract_version`, `evidence_digest`, 현재/추천 scalar, exact target key, bounds/step, 비교 universe hash, cost/exit/sizing policy version, source authority, feasibility, rollback 값을 넣는다. 표시용 생성시각 변화와 실질 증거 변화는 hash에서 구분한다.
- AI 입력은 scalar `current_value`/`recommended_value`를 제공해 현재의 null/문자열 제안 문제를 줄인다. AI는 동일 후보에 대한 검토만 하며 새로운 값·경로·enable·수량 권한을 만들지 않는다. 내부 reviewer/schema prompt는 English ASCII로 작성한다.
- AI output에 candidate identity와 검토한 current/recommended 값을 돌려받는다. direct report 재생성 뒤 같은 family의 과거 review를 재사용하지 않는다. producer와 AI/PREOPEN의 ID/date/hash/schema/key/value 일치가 모두 필요하다.
- PREOPEN은 source-date freshness·preflight, 허용된 증거 계층, count/authority, bounds/step, exactly-one-changed-key를 독립 검사한다. generic accepted 플래그나 same-family만으로 통과시키지 않는다. 공통 env에 NXT-only 증거를 적용하지 않으며 공통 영향 scope의 근거가 없으면 결손을 명시한다.
- 기존 PYRAMID/AVG_DOWN single cumulative update 선별을 유지한다. source-only 후보는 stage slot을 점유하지 않는다. wrapper가 후보를 AI 전에 생성하는지, dependency/hash 변경 시 checkpoint를 무효화하는지 검증하고 cron을 추가하지 않는다.
- runtime event는 선택된 candidate ID, config/policy version, effective pressure, 실제 route·적용/미적용 이유를 기록한다. 주문·receipt·terminal까지 같은 decision/episode로 연결한다. `selected`, `env_written`, `pid_verified`, `natural_match`, `filled`, `attributed`를 구분한다.
- 적용 후 비교는 같은 정책 버전·동일 scope의 applied/not-applied와 행동 차이가 난 episode를 분리한다. 자연 match 0은 실패나 순익 0이 아니다. 일반적인 EV 미달은 다음 bounded calibration hold/freeze로 처리하고 safety rollback과 구별한다.
- rollback은 실제 적용 전의 검증된 값과 기존 trigger를 사용한다. provenance 손상, owner conflict, 주문/안전 오류는 기존 guard로 닫는다. last accepted 값·명시적 사용자 override를 보고서 누락만으로 조용히 기본값/enable 변경으로 덮어쓰지 않는다.

완료 기준: 정상 fixture는 전략 key 한 개와 비전략 provenance만 선택하고, AI mismatch/old schema/sim-only/금지키/owner 충돌은 전략 env를 만들지 않는다. 실제 반영 완료는 exact-date env와 프로세스 관측 이후에만 보고한다. 구현 검증에서는 생산 env·봇·주문을 변경하지 않는다.

## 5. 파일 소유권과 구현 묶음

| 묶음 | 우선 파일 | 검증 |
| --- | --- | --- |
| A: P0 + P1 | `monitoring/scalping_avg_down_recovery_calibration.py`, `threshold_cycle_preopen_apply.py`, `sniper_state_handlers.py`, `observation_source_quality_audit.py` | legacy/금지키 차단, maturity/fill/dedupe/authority, 원천 계측 부작용 없음 |
| B: P2 + P3a | `sniper_scale_in.py`, `holding_exit_matrix_runtime.py`, `sniper_state_handlers.py`, `lifecycle/scale_in_incremental_counterfactual.py`, 기존 `trade_profit.py` 사용 | 현재값 행동 동등성, 전체 경로 귀속, source-only 증분 손계산 |
| C: P3b 가능성 판정 + P4 + P5 | calibration, daily report, PREOPEN, postclose verifier와 해당 wrapper | 종료정책 재현/권한 계층, 단일값·identity·stage 선별·attribution |

파일은 모두 `src/engine/` 아래 기존 소유 위치를 뜻한다. `src/engine` root에 새 Python module을 만들지 않는다. 분리가 꼭 필요하면 기존 구조를 먼저 확인한 뒤 live 순수 판단은 `src/engine/scalping/`, offline 증거/replay는 `src/engine/lifecycle/` 또는 기존 `monitoring/` 소유로 배치하고 이유를 남긴다. 테스트는 `src/tests/`, 계획은 `docs/proposals/`다. wrapper 복제나 새 독립 report producer는 만들지 않는다.

기존 PYRAMID 개선의 dirty changes와 source 계약을 보존한다. 공통 helper 변경은 PYRAMID·기존 sim incremental consumer까지 회귀 검증하고, 같은 개념처럼 보여도 데이터 권한이 다른 schema를 억지로 통합하지 않는다.

구현 시에는 traceability의 AVG_DOWN/증분 EV 행과 일일 checklist를 함께 갱신한다. 자동화 wrapper 계약을 바꾸면 관련 운영 문서도 같은 변경 묶음으로 검토하되 README/runbook/Plan Rebase/AGENTS baseline 수정은 별도 명시 요청 범위를 따른다. Kiwoom 요청·응답·receipt protocol 변경은 이번 계획에 없으며 필요해지면 공식 reference gate를 먼저 수행한다.

## 6. 테스트·리뷰·완료 판정

각 묶음은 `구현 → 자체 리뷰 → 결함 수정 → 재리뷰 → targeted validation`을 반복한다. 개별 테스트 pass만으로 전체 결함 없음이라고 하지 않는다.

필수 검증 사례:

- source: timestamp/file-date 불일치, 중복 ID 상충, sim/real 섞임, forbidden-use 입력, row exclusion, 잘못된 venue, 구형 schema, missing/NaN/Inf.
- lifecycle: 1초 mark, 30분 전 정상 종료, 미성숙/관측 단절, 주문 취소/부분체결/완전체결, receipt 중복, overnight 연결, 여러 추가 leg와 평균원가 변경.
- behavior: 현재값 동등성, shallow 거절 뒤 aggressive/ADM 허용, 다른 owner, 동일 최종 행동, 평가 중 mutation/추가 AI 호출 없음, 기존 hard/broker/quantity/cooldown 우선순위.
- economics: 비용 1회, 비용 반영 후 음수, 같은 reference denominator, 정상 NO_ADD의 증분 0, 결손의 양쪽 제외, fixed-exit source-only 한계, 추가 후 stop/trailing 변화, same-window 탐색/검증 구분.
- apply: 허용키 하나, 2개/금지키 차단, bounds/step/current 출처, stale AI ID/hash/date/key/value, unknown schema, 단일 scale-in owner, source-only slot 미점유, NXT-only 공통 env 차단, rollback/이전 승인값 호환.

기존 테스트 우선 실행 목록은 `test_scalping_avg_down_recovery_calibration.py`, `test_scale_in_incremental_counterfactual.py`, `test_sniper_scale_in.py`, `test_handle_holding.py`, `test_holding_exit_matrix_runtime.py`, `test_daily_threshold_cycle_report.py`, `test_threshold_cycle_preopen_apply.py`, `test_observation_source_quality_audit.py`, `test_verify_threshold_cycle_postclose_chain.py`다. 영향이 있는 공통 경로에는 PYRAMID 회귀 테스트도 포함한다. `.venv`를 사용하고 패키지를 임의 설치/업그레이드하지 않는다.

최종에는 변경 모듈 compile, 해당 lint/format 검사, `git diff --check`, 문서/checklist parser를 실행한다. 운영 보고서 재생성·광범위 자동화·봇 재기동은 no-defect 최종 review와 해당 검증 통과 및 별도 실행 권한이 모두 있을 때만 검토한다. 최초 원천 검증은 승인된 범위의 임시 출력으로 한정하고 생산 산출물을 덮어쓰지 않는다.

묶음 A→B→C의 이전 구현 기록은 §0에 보존하며, 현재는 §0.1 최종 리뷰에 따라 보완이 필요하다. 후속 판정은 (1) 유효 exact-route 기회 식별, (2) 작은 비용 차감 순기여 후보의 유무, (3) AI/PREOPEN/PID 자동화 연결 단계, (4) 실적용까지 남은 source/authority/exit/owner 결손을 각각 보고한다. P3b가 닫히기 전에는 고정 종료 분석을 실권한으로 포장하지 않고 구체적인 repair/acceptance를 유지한다.

이전 review/fix/re-review에서 source-only 후보의 `target_env_key` identity를 PREOPEN뿐 아니라 postclose verifier도 동일 validator로 검사하도록 보완했다. 또한 paired 표시만으로 하나의 관측 매도가를 A/B/C에 공통 적용해 승격할 수 있던 결함을 제거했다. Paired terminal은 A/B/C별 완료 상태·독립 종료가격·동일 exit-policy version·고유 source ID·exact decision ID를 요구하고, 각 경로의 비용 차감 총손익을 독립 계산하며 fixed/paired 누적 분모를 분리한다. 당시 수정 후 AVG_DOWN·holding/LDM·daily AI·PREOPEN·source audit·postclose verifier·공통 PYRAMID·main lifecycle 영향 회귀 2,148건과 checklist parser 테스트 53건을 통과했다. Ruff, Black, 변경 모듈 compile, postclose wrapper `bash -n`, 실제 checklist parse 및 `git diff --check`도 통과했다. 당시 결함 0건 판정은 §0.1에서 확인한 신규 결함으로 대체되며 현재 최종 gate 통과를 뜻하지 않는다. 외부 `pandas_ta`가 발생시킨 pandas 4 deprecation 경고 1건은 해당 계약 변경과 무관한 잔여 경고다.
