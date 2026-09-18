# PYRAMID·AVG_DOWN 경제성 튜닝 및 자동 적용 보완 구현계획 — 2026-09-17

## 현행 사용자 정정 — PYRAMID 폐기·AVG_DOWN 공통 반등 신호 소비

사용자의 2026-09-18 지시는 아래 SI0–SI6의 독립 scale-in 튜닝 목표를 대체한다. SI0–SI6 및 이전 배포 receipt는 과거 구현·검증 이력이며 신규 튜닝/정책/런타임 복원 권한이 아니다.

- **PYRAMID**: Main/Swing 판단·수량·주문 진입, intraday feedback, 장후 quality calibration, Daily 후보 intake, PREOPEN 적용/승계와 cron 재설치를 폐기한다. 오래된 env/lock/report 또는 직접 호출로 다시 활성화할 수 없다. 기존 주문의 pending/체결/청산 정산과 원장은 보존한다.
- **AVG_DOWN**: 독립 threshold grid·recovery calibration·source-only account/budget 수집·250ms exit replay capture를 폐기한다. 이미 취득한 Main holding completed bars와 현재 WS tick/BBO를 기존 Main 기계 entry 판정/정책에 넣고 `PULLBACK_RECOVERY`, `RECOVERY_CONFIRMATION`, `MICRO_RECOVERY` 중 `ENTER_NOW` 신호만 추가매수 후보로 소비한다. Main 정책의 기존 장후 학습→dated publisher→PREOPEN 계열을 공유하며 별도 AVG_DOWN 후보/승격 owner는 만들지 않는다.
- 삼성/widget/episode 전용 machine rebound 연구는 custody·venue/session·policy scope가 다르므로 Main HOLDING에 직접 연결하지 않는다. 현재 Main 정책 bundle/scope 또는 신선한 원천이 없으면 ADD하지 않고 기존 source gap owner에 남긴다. 신규 collector/API/provider/model/cron은 없다.
- 공통 BUY pause·operator veto·source freshness/conflict·holding-AI submit veto·현금/broker 수량·최초 BUY 수량 대비 추가매수 cap·cooldown·pending·custody·exit claim과 hard/protect/emergency stop을 유지한다. 기존 손절 직전 강제 ADD, 추가매수 이유의 stop 유예/재시도는 폐기한다. 손절/SELL을 반등 신호로 대체하지 않는다.
- 신호는 symbol·보유 basis·현재 원 WS digest·기계 정책 version/hash·source signal ID·episode/decision에 결속한다. 재평가 clock만 변경해 같은 source를 새 신호로 세지 않는다. 제출 permit은 2초 내 현재 basis/source만 허용하며 접수한 신호는 재사용하지 않는다. 정책/신호는 가격·수량·주문 권한이 아니고 기존 집행 guard를 거친다.

이전 `1.5%`는 추가매수 이후 최소 이익이나 손절값이 아니라 **기존 보유분 현재 net return이 이 값 이상이어야 PYRAMID를 평가하는 선행 허들**이었다. 기존 incumbent는 code default `SCALPING_PYRAMID_MIN_PROFIT_PCT=1.5`; 9/17 보고서 selected 값도1.5였으나 신규 경제성으로 선정된 값이 아니었다. current PID 소비 증거가 없으므로 실제 live loaded value로 단정하지 않는다. 빈번한 작은 이익이라는 목표에 최적이라는 근거는 없으며 이번 지시로 허들/정책 적용 자체를 폐기한다. AVG_DOWN과 common exit의 이익 목표·slippage/비용 계약은 임의 변경하지 않는다.

검증/배포/자연 증거는 [현행 review receipt](../audit-reports/2026-09-18-pyramid-retirement-avg-down-shared-rebound-review.md), 실행 Acceptance는 당일 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`이 소유한다. Main 정상 PREOPEN/PID가 없으면 code selection을 자연 적용으로 보고하지 않는다. 성과는 새 code/공통 machine version에 결속된 실제 `COMPLETED + valid profit_rate/cost` episode를 중복 제거하고 rolling/cumulative EV·순익·tail·노출을 평가한다. model ΔEV는 별도이며 Main entry 학습의 positive edge를 AVG_DOWN 실제 증분 이익으로 전환하지 않는다.

## 1. 목적·범위·권한

목표는 실제 보유 종목의 **추가매수 실행·차단·미실행 기회**를 동일 모집단에서 평가하여, 비용 차감 EV와 원화 순이익이 incumbent보다 개선되는 기존 bounded 후보를 만들고 다음 거래일 PREOPEN 자동 적용·실제 소비·적용 후 귀속까지 연결하는 것이다. 보고서 생성이나 후보 개수 증가를 경제성 개선으로 계산하지 않는다. 양수 edge가 없는 입력에서 후보를 강제로 만들지 않는다.

상태: **사용자 지시로 구현·재리뷰·검증과 clean managed release 배포를 수행 중**. 최신 코드/배포/PID·자연 수집·경제성 판정은 [9/18 receipt](../audit-reports/2026-09-18-scale-in-economic-tuning-deployment-and-performance-review.md)에서 각각 확인한다. 신규 threshold 정책 선정·실제 순익 개선은 별도 자연 Acceptance이며 배포만으로 완료가 아니다. 문서 작성은 provider 호출, 거래 프로세스 재기동, 주문, env/lock/threshold/cap 변경 권한이 아니다. 후속 구현 요청을 받으면 검증된 기존 자동 선정 경로를 완성하며, 정상 bounded 선정에 매일 수동 후보 승인·env 편집을 추가하지 않는다. 초기 코드 배포/거래 프로세스 follow-up은 그때의 사용자 지시·운영 계약을 따른다.

소유 원칙:

- [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md): EV·clean baseline·stage·canary·hard safety·rollback 계약.
- [현재 일일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`: 기존 기회비용 계획의 U10B/U11 중 scale-in 잔여 실행 owner. 본 문서의 SI 번호는 구현 package 식별자이며 별도 자동 파싱 OPEN owner가 아니다. 날짜 이관 시 원 stable ID·Acceptance를 보존한다.
- [기회비용 전체 모집단 계획 U10B/U11](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md#u10b--남은-active-raw-기반-family의-선정편향-정합화): 본 계획은 scale-in 상세 분해다. 다른 Entry/widget/episode package 전체 완료를 선행 조건으로 추가하지 않는다.
- [장후 계산 계획 O2/O3](postclose-computation-optimization-implementation-plan-2026-09-17.md): 실제 AVG_DOWN 반복 원천 처리만 협력한다. 별도 동일 cache/job을 만들지 않는다.

대상은 Main scalping의 `scalping_pyramid_quality_gate`, `scalping_avg_down_recovery_quality_gate`다. Swing OFF, 퇴역 ADM/LDM, widget/episode/manual custody는 독립 유지한다. 초기 Entry quantity/leg 정책으로 AVG_DOWN/PYRAMID 수량을 바꾸지 않는다. `real_pyramid_scale_in_quality_guard_runtime`은 별도 기존 guard이고 본 튜닝의 적용 receipt가 아니다.

## 2. 확인한 실패 지점과 closure 기준

9/16·9/17 기존 산출물·command 계측 기준의 snapshot이다. 후속 구현 시작 시 선택 release·실제 consumer·source generation을 다시 고정한다. 아래 수치를 새 실행 결과나 최신 PID 증거로 재사용하지 않는다.

| 지점 | 확인된 근거 | 수리 후 closure |
| --- | --- | --- |
| PYRAMID 경제성 표본 단절 | 누적 gate row889/episode46, comparable0. 가격·resolver/BBO·청산·schema·owner gap 중첩 | 유효 blocked episode도 paired 평가에 진입; excluded 사유와 원 identity 대사 |
| 진단 표본과 선정 표본 혼동 | 진단 sample87, decision sample/universe0 | census·진단·paired·holdout·actual 표본을 별도 표시; 0과 null 분리 |
| 현재 baseline 확인 실패 | 9/17 gate0, verified env에 해당 override0 → code default1.5와 provenance missing | 기회 발생 여부와 무관하게 실제 loaded rule·PID·정책 출처 확인; default를 관측으로 합성하지 않음 |
| AVG_DOWN 대량 읽기·희소 유효 판단 | 약19,375,105 raw events → exact decision9/episode6; legacy proxy55,064는 episode ID 결손 | 유효 최신 source만 재처리; irrecoverable 과거 제외는 보존; 새 기회 결속률 보고 |
| 오늘 정책 cohort 미확정 | 9/17 config/route0 → same-policy decision0 | 실제 현재 설정을 별도 확인하고 호환 정책 cohort 결정; opportunity0와 source missing 구분 |
| replay와 후보 경제성 단절 | paired terminal consumer 존재, engine emitter 미확인; 독립 replay는 후보 계산 뒤 진단 필드로 생성 | 독립 replay → 검증된 paired economics adapter → 후보 재평가 연결 및 최종 consumer 회귀 |
| 모델 결과의 authority 경계 | quote-touch CF·source-only, runtime_authority_ready=false | 모델 결과 권한은 유지; 별도 family guard가 통과한 후보만 PREOPEN 적용 허용 |
| 긴 반복 수행 | PYRAMID feedback약34초/calibration약1.15초; AVG_DOWN 완료약1,000/1,028초, 중단2회 | 변경 없는 과거 raw 재순회 제거; 중단·재시도에서 유효 완료 결과 재사용 |

근거 owner: `data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-09-16.json`, `scalping_pyramid_quality_calibration` 및 `scalping_avg_down_recovery_calibration`의9/16·9/17 JSON, `logs/threshold_cycle_postclose_cron.log`의 `postclose_command_metrics_v1`.

## 3. 코드 위치·기존 경로 재사용

새 production Python module·package·CLI·cron·collector·범용 replay/cache framework는 기본적으로 **0개**다. 먼저 기존 함수에 필요한 adapter/fields를 넣는다. 작은 private helper는 기존 역할 파일 안에 둔다. 독립 파일이 불가피하면 AGENTS location gate와 실제 공통 caller 근거를 먼저 남긴다. `src/engine` root 새 Python 파일은 만들지 않는다.

| 책임 | 기존 변경 위치 | 제한 |
| --- | --- | --- |
| 실시간 판단·기회·설정 provenance | `sniper_state_handlers.py`, `sniper_scale_in.py`, `sniper_execution_receipts.py` | 관측·순수 함수 입력 보완 우선; live action/guards 변경은 별도 경제성 package |
| frozen state·market capture | `scalping/avg_down_replay_capture.py` | 기존 frame/capture 재사용; 실계좌/호가/provider 추가 조회 없음 |
| PYRAMID raw join·coverage | `monitoring/scalping_pyramid_intraday_feedback.py` | 기존 보고서/metric contract에 추가; 새 diagnostic 보고서 금지 |
| family별 평가·선정 | `monitoring/scalping_pyramid_quality_calibration.py`, `monitoring/scalping_avg_down_recovery_calibration.py` | 기존 grid/axis/bounds 유지; diagnostic와 decision 의미 분리 |
| 독립 청산·체결 모델 | `lifecycle/avg_down_replay.py`, `lifecycle/avg_down_policy_replay.py`, `lifecycle/scale_in_incremental_counterfactual.py` | 기존 격리 adapter 확장; 실제 broker 호출 금지 |
| AVG_DOWN 실행 quantity/leg 후속 | `scalping/scale_in_split_order_plan.py` | action 후보와 별도 owner·정책; 최초 범위에서 동시 최적화하지 않음 |
| source contract·전달 | `observation_source_quality_audit.py`, `automation/source_quality_hard_gate.py`, `daily_threshold_cycle_report.py` | 해당 family gate만 변경; 공통 전역 gate 완화 금지 |
| PREOPEN·실제 소비·R6 | `threshold_cycle_preopen_apply.py`, 기존 runtime verifier/EV/approval/gap/lineage/tower/strict verifier | 기존 publisher/loader/manifest를 사용; 새 apply daemon 금지 |
| schedule·재사용 | `deploy/run_threshold_cycle_postclose.sh` 및 필요 시 기존 PREOPEN wrapper | 같은 target-date·resource·provider budget·review 계약 유지 |

`scalping/strategy_owner_replay.py`는 현재 WEAK/PROFIT component의 first-use owner다. snapshot/격리 replay의 기존 하위 primitive만 활용하고 PYRAMID·AVG_DOWN을 그 family/20-real-full-fill gate에 억지로 넣지 않는다. sibling 계약을 복사하거나 퇴역 consumer를 복원하지 않는다.

Kiwoom wire/parser/REG/복구/order protocol 변경은 현재 단계에 필요하지 않다. 후속에서 필요해지면 수정 전에 공식 reference gate를 수행하고 upstream SHA·경로·retrieval time을 기록한다. local normalized receipt 확장을 upstream protocol 변경으로 오인하지 않는다.

## 4. SI0 — source·현재 설정·모집단 계약 고정

### 4.1 실제 범위와 분모

모집단은 **Main custody의 실제 scalping 보유 episode에서 해당 scale-in owner가 평가 가능한 기회**다. 최초 매수 fill은 실제 보유 anchor 검증용이고, 이후 ADD fill은 기회 모집단 가입 조건이 아니다. 시장 전체 종목이나 모든 tick을 모집단이라고 주장하지 않는다.

- 가격/수익 임계값으로 탈락하기 전 owner-ready 판단을 포착한다. hard safety/다른 owner veto는 census에 남기고 가상 bypass로 경제성 표본에 넣지 않는다.
- observed ADD, blocked/no-ADD, 미제출, 취소·무체결, 부분체결, holding/censored를 분리한다. source-invalid도 census에는 보존한다.
- polling 중 동일 원 packet/동일 state/정책의 재평가는 중복 episode 표본이 아니다. source bundle·보유수량·peak·유효가격·정책·route 상태 변화가 후보 판단을 바꾸는 시점은 보존한다. 임의 간격 표본추출로 좋은/나쁜 기회를 누락하지 않는다.
- 보존식: owner-ready 기회 = source-invalid + owner/safety-ineligible + 경제성 입력 eligible. eligible = paired-complete + pending/censored + 명시 economics-gap. 중복 attempt/cycle·retry count는 별도다.
- route/BBO/fill 실제 venue·session·epoch를 구분한다. KRX/NXT/SOR와 PREMARKET·정규·aftermarket을 임의 합치지 않는다. scope aggregate와 episode 집계는 별도이고 공통 axis 승인 범위는 기존 contract를 따른다.

### 4.2 최소 identity·현재값

기존 이벤트에 원 `position_episode_id`, decision/evaluation ID, attempt/order/fill identity, source-event 위치/hash, input cutoff·source generation, original entry sizing formula, owner, policy/cost/exit versions, effective venue/session/epoch, gate-before/gate-after·blocker, configured/effective loaded value를 결속한다. 가까운 종목/시각·터미널 가격만으로 episode를 추정하지 않는다.

현재 설정은 기존 process-loaded rules/PID receipt를 관측한다. env override 없음은 규칙 default가 실제 로드될 수 있는 정상 상태지만, postclose 코드 default 자체는 소비 증거가 아니다. 기존 AVG_DOWN config observation에 PYRAMID 값도 포함하거나 기존 runtime verifier receipt를 확장하여 **일자/프로세스/loaded-rule signature당 한 번**, 기회가 없는 날에도 확인한다. logger 실패는 live 판단을 바꾸지 않고 report에서 source gap으로 남긴다.

현재 PID가 장후에 정상 종료됐으면 target-date 마지막 유효 소비 receipt와 종료 상태를 명시한다. 죽은 PID의 `/proc` 재조회 실패를 source0 또는 default 소비 확인으로 바꾸지 않는다. 다음 PREOPEN은 새 실제 PID를 별도로 검증한다. operator override의 출처·expiry·custody·동일 stage 소유권을 보존한다.

### 4.3 과거 source 사용

clean baseline6/5 이후 자료도 identity/정책/가격/비용/청산 호환성을 통과해야 한다. 과거 metadata 부재는 원 durable receipt로 동등 계약을 증명할 때만 복원한다. 결손55,064행에 ID를 합성하지 않는다. 구현 SHA가 달라졌다는 이유로 현재 코드를 과거 정책으로 대체하지 않는다. 기존 frozen snapshot으로 당시 의미 재현이 가능한 cohort만 재사용하며 불가 복원은 영구 제외 이유·다음 전향적 owner로 닫는다.

Acceptance: blocked/zero-fill 기회가 census에 남고 actual-only 조건이 붙지 않음; valid-empty와 missing 구분; default/override/current PID receipt 출처 충돌0; 보존식과 제외 manifest 대사.

## 5. SI1 — 차단 기회의 가격·수량·후행 경로 보완

### 5.1 baseline 차단 때문에 사라지는 경제성 입력

기존 판단은 실제 gate가 통과해야 downstream 가격·수량 계산에 도달할 수 있다. 그대로면 임계값을 낮춰 허용될 기회의 가격이 없어 연구가 계속0이다. live submit 분기를 열지 않고, **기존 resolver와 sizing 순수 부분을 frozen 입력에서 source-only로 재평가**한다.

- 당시에 확보된 fresh conflict-free BBO·가격 resolver input을 사용한다. `curr`/나중의 ask를 그 시점 주문가로 소급하지 않는다. resolver output/input BBO·route·clock을 동일 receipt에 결속하여 기존 mismatch를 실제 producer/consumer 단위로 수리한다.
- 당시 original-entry sizing formula·보유수량·이미 확보한 account budget·예약/동시 order context를 사용한다. 격리 replay/telemetry 소비자는 실계좌 API를 새로 부르지 않는다. 9/18 사용자 지시의 budget 원천 수리는 기존 Main budget owner에 한정한다. Main이 실제 initial BUY receipt가 완전하고 공통 safety/order/cooldown·매수시간 gate가 허용한 episode/buy basis/family의 최초 기회 전에 기존 normalized `kt00011`을 최대1회 source-only로 확보한다. 별도 deposit/호가/provider 조회·주문·복구는 없으며, 요청 재시도1회·read-rate 대기0·connect/read 각150ms·Main 대기 총300ms다. pending 주문이면 복구 함수를 호출하기 전에 종료한다. 종목/가격/clock/hash·현재 inventory/reservation이 맞는2초 이내 source만 순수 sizing/capital 소비에 전달하고 늦은 worker 결과를 과거 decision에 넣지 않는다. 현재 gate 차단은 수리된 원천에서 challenger를 계산하는 조건이지 live ADD 허용이 아니다. budget/quantity가 없으면 economics-gap이며 임의1주·현재 deposit으로 원화 수익을 계산하지 않는다.
- quantity=0과 unknown은 구분한다. 명시 guard가 quantity0이면 valid no-exposure, quantity 미관측이면 gap이다.
- 후보 axis만 변경하고 stale/conflict/broker/account/order/cooldown/수량/cap/hard stop guard는 모두 유지한다. 관측 중에도 실제 BUY/SELL branch가 호출되지 않음을 확인한다.

### 5.2 frame 보존과 누락

기존 `avg_down_replay_capture`의 state·시장 frame을 PYRAMID에도 필요한 범위에서 재사용한다. MAX_ACTIVE8/frame gap5초/daily256MB 등 현재 bounds는 구현 시 검증하고 무조건 올리지 않는다. 실제 새 이벤트·quote update가 없는 polling duplicate는 frame 재사용 가능하나 capture 시각을 source 시각으로 신선화하지 않는다.

episode의 실제 청산 뒤에도 대안 arm이 아직 holding이면 기존 local market 관측 경로의 가용 범위에서 후행 frame을 보존한다. 그 경로가 종료/retention/budget으로 끊기면 `censored`를 남긴다. 새 구독·REST 조회·상시 collector를 암묵적으로 추가하지 않는다. 실제 source 연속성이 없으면 해당 독립 청산 비교를 승인 표본으로 사용하지 않는다.

cap으로 수집되지 못한 ready 기회는 dropped count·scope·시간·원인을 기존 coverage 필드에 남긴다. 수집된 첫8개만으로 전수·대표성 완료를 주장하지 않는다. 유효 기회가 현 bounds를 지속적으로 넘으면 기존 저장의 중복/불필요 state부터 줄인다. source-valid 평가 구간을 사전에 선언하고, 미관측 구간을 결과를 본 뒤 좋은 구간만 남기는 방식으로 선택하지 않는다.

승인 scope의 capture 누락이 특정 손익·blocker·시간·후보에 집중되거나 누락 편향을 판별할 수 없으면 그 scope의 경제성 promotion은 막는다. 이 경우 전체 시장의 source를 blanket block하지 않고, named coverage gap을 수리하거나 기존 계약에서 허용하는 입증된 scope만 사용한다. 공통 scalar axis에 국소 scope 성공을 확대 적용하지 않는다.

Acceptance: baseline profit/pressure 차단 기회도 가격·수량 계약이 있으면 challenger 계산 가능; 미래 source 사용0; cap/drop는 census에서 설명; 프레임 끊김을 정상 HOLD/NO_ADD0원으로 바꾸지 않음.

## 6. SI2 — 동일 기회 집합의 독립 paired 경제성

### 6.1 arm과 정책 상태

각 episode의 첫 eligible 결정 상태에서 `NO_ADD`, `incumbent`, bounded `challenger`를 구성한다. PYRAMID 기존0.2~2.5 grid와 AVG_DOWN80/85/90 grid를 유지한다. PYRAMID의 고정 청산 결과는 탐색/회귀 진단으로 유지하고, 최종 후보는 AVG_DOWN의 기존 격리 holding adapter를 통해 수량·평균단가 변경 이후 **arm별 독립 exit**를 재생한다.

모든 arm은 동일 과거 정보·원 clock에서 시작하되 virtual inventory/peak/cooldown/미체결 잔여/예약예산은 복제해서 분리한다. 미래 high/MFE·나중 AI·terminal 가격으로 entry/action을 결정하지 않는다. 최초 eligible 시점만 비교하는 정의와 반복 ADD lifecycle 정의를 혼동하지 않는다. 초기 구현은 기존 first-decision episode 계약을 유지하고, 이후 반복 ADD 효과는 실제 guard·예산이 재현될 때 같은 adapter의 state transition으로 확장한다.

실제 arm은 broker receipt로 full/partial fill을 검증한다. 가상 arm은 기존 체결 모델을 이용해 executable quote·수량·limit/market·time-in-force·cancel deadline·부분체결/무체결을 구분한다. 호가 touch만으로 실제 체결을 선언하지 않는다. 이후 quote 자료·잔량/continuity로 모델이 지원하지 않는 경우 gap/censored다. 실제 arm 재현 오차를 가격·수량·fill 시각·exit/cost별로 분리하여 모델 범위를 검증한다.

기존 policy AI replay는 exact state/input digest·provider/model/prompt generation으로 결속한다. ADD로 state가 달라지면 NO_ADD AI 응답을 대입하지 않는다. provider budget64/report600초 등 기존 상한을 보존하고 필요한 arm만 bounded 호출한다. 변경 없는 요청의 기존 완료 cache를 사용한다. budget 부족은 pending이고, 이후 신규 입력/남은 budget으로 재개하며 원천 불변 실패를 계속 호출하지 않는다. actual input·stored prompt·cached answer가 재현되지 않으면 당시 AI 결정으로 추정하지 않는다.

### 6.2 비용·자본·보고 지표

각 arm에서 전체 보유 episode의 실현/모델 순손익을 계산하고 NO_ADD와 incumbent 차이를 별도로 둔다.

- `net_pnl_krw = sell_proceeds - buy_notional - declared_commission_tax - modeled_slippage_cost`. 기존 trade-profit helper가 이미 차감한 비용은 두 번 빼지 않는다.
- episode별 `delta_net_krw = challenger_net_krw - incumbent_net_krw`와 `delta_ev_pct`를 동일 공통 분모에서 계산한다. 기존 family reference-notional 정의를 문서화하고 후보마다 유리한 분모로 바꾸지 않는다. equal-weight EV, notional-weighted EV·합계 순익을 명칭부터 구분한다.
- `NO_ADD` 전체 position PnL은0이 아니다. incremental-add PnL만 명시적으로0일 수 있다. 미체결 arm도 기존 inventory exit·비용을 포함한다. no-opportunity/missing 결과의 EV는null+이유다.
- 추가 buy notional·현금 예약·자본 점유시간·peak exposure·동시 order/cap 충돌을 기록한다. 다른 종목의 자본 재배분 근거가 없으면 그 기회이익은 추정하지 않고 missing 범위를 밝힌다. 실제 이미 소비한 예산과 가상 budget을 중복 사용하지 않는다.
- actual full-fill/partial/canceled-unfilled, modeled full/partial/no-fill, sim/probe, holding/censored를 섞지 않는다. actual PnL은 COMPLETED+valid profit/cost 계약만 사용한다.
- baseline 비용 외에 기존 supported price/fill 모델의 보수적 slippage·fill delay stress를 평가한다. 동일 자료에 없는 체결을 stress0 손실로 대체하지 않는다. 모델 가정/스트레스 값은 구현 전에 source 지원 범위·현 family guard를 기준으로 고정한다.

### 6.3 replay → candidate 연결

`build_report`에서 exact input을 수집한 뒤 독립 replay를 먼저 완결하고, 검증된 output을 기존 candidate-economic adapter로 전달한다. 지금처럼 candidate를 만든 뒤 replay를 부록에 붙이는 순서를 해소한다.

`avg_down_route_arbitration_terminal`의 요구 fields를 기존 report 내부 paired terminal adapter가 발급한다. raw live JSONL에 합성 terminal을 append하지 않는다. 실제 `sell_completed`와 modeled terminal은 별도 origin/type·source mapping을 유지한다. 기존 event 이름/contract를 재사용할 수 없는 semantics이면 같은 producer 안에서 report schema successor를 발급하고 모든 소비자를 함께 변경한다. 새 emitter daemon은 만들지 않는다.

terminal에는 arm별 outcome ID·source observation/decision/episode·정책/exit/cost/수량·venue/session·input cutoff·source hashes·frame continuity·fill evidence class·완료 상태를 결속한다. 같은 terminal ID를3arm에 복제하지 않는다. 검증한 modeled paired output은 family economics 입력으로 쓸 수 있지만 `runtime_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`를 유지한다. `runtime_authority_ready=false`를 결과 복사만으로 true로 바꾸지 않는다.

Acceptance: 유효 차단/미체결 episode가 paired_complete가 되면 같은 실행에서 후보 economics 표본에 반영; realized recovered profit과 새 delta 구분; missing cost/frame/quantity는 제외; 후보 결정을 막던 terminal gap이 실제 adapter로 닫힘.

## 7. SI3 — 과적합·선정편향을 막는 경제성 후보 선정

### 7.1 탐색과 검증

source-valid·current-compatible·owner/venue/session/policy/cost cohort를 고정한다. 실제 ADD만 남기지 않고 eligible no-ADD/blocked 기회를 공통 denominator에 포함한다. 모든 후보에서 유효한 공통 episode 집합을 비교하고 candidate-dependent exclusion을 따로 보고한다. 일부 후보에만 frame gap이 있는 episode를 silently 제외해 winner를 바꾸지 않는다.

calibration은 과거 source-day, holdout은 그 뒤 최신 eligible source-day로 사전에 고정한다. 같은 episode가 경계를 넘으면 label 완결/embargo를 반영하고 calibration↔holdout 양쪽에 넣지 않는다. 후보/axis·tie-break는 calibration에서 확정한 뒤 holdout을 한 번 평가한다. holdout 실패 뒤 그 holdout으로 다른 후보를 고르는 반복을 금지한다. 다음 신규 source-day에서만 새 선택을 검증한다.

rolling 평가창은 호환 source가 누적될 때 사용하고 clean cumulative는 장기 안정성/커버리지 진단으로 유지한다. 다른 family의56/16일·1,536 grid를 가져오지 않는다. chronological cutoff·일자별 입력 count를 artifact에 남기며, 미래 holdout/실제 terminal로 과거 정책을 재승인하지 않는다.

### 7.2 기존 숫자와 실제 통과 조건

| 대상 | 유지하는 기존 기준 | 보완 |
| --- | --- | --- |
| PYRAMID | 기존 eligible episode20, step0.1%p, grid/bounds | 진단87을20floor에 대입하지 않음; independent paired net·EV·holdout·tail/capital guards |
| shallow AVG_DOWN | unique complete eligible parent10, pressure80–90, step5 | paired arms·same-policy/cost/sizing·common KRX/NXT scope; 신규 ADD는 기존 net EV>=+0.10% 및 delta EV/순익 양수 유지 |
| AVG_DOWN 제거형 tightening | 기존 NO_ADD control 비교의 zero-EV 예외 | 현재 대비 EV·순익 개선은 요구; ADD 양수 alpha로 부르지 않고 risk-reduction 유형으로 명시 |
| 실행 sizing/leg | `scale_in_split_order_plan` 기존3real outcome/3MFE-MAE/2date/80%price join/+0.10% 등 해당 계약 | action과 floor 섞지 않음; 합성 opportunity로 actual-only fill-quality floor 대체 금지 |

10/20 floor를 total economics floor로 유지하며 calibration/holdout 각각에 같은10/20을 중복 요구하지 않는다. holdout에 실제 비교가 가능하고 행동 차이가 발생한 표본·양의 paired 결과가 있어야 하며, 설계 시 고정한 uncertainty/tail 판단을 충족하지 못하면 hold다. primary metric이 양수라도 순익 개선·스트레스·tail/노출이 충족되지 않으면 선정하지 않는다. sample/EV 수치를 낮춰 후보를 만들어내지 않는다.

최종 predicate는 최소한 `source_valid AND current_provenance_valid AND paired_complete AND total_sample_floor_passed AND calibration_winner_fixed AND holdout_delta_ev_positive AND holdout_delta_net_positive AND cost_stress_passed AND tail_capital_guards_passed AND execution_quality_guard_passed AND runtime_scope_ready AND same_stage_owner_clear AND operator_veto_absent`로 명시한다. 신규 ADD형은 family의 absolute positive-EV 조건도 포함하고 제거형 tightening은 위 예외를 적용한다. 기존 tail/capital guard의 실제 필드·값·출처를 SI0에서 적어둔다. 없는 값은 임의 상수로 통과시키지 않고 baseline 대비 악화 없음 등 검증 가능한 규칙의 contract successor를 holdout 열람 전에 확정한다. 사후 값 조절로 실패한 holdout을 통과시키지 않는다.

first-use에 challenger의 실제 ADD20개를 먼저 요구하는 순환을 새로 만들지 않는다. 정확한 paired 모델 경제성·incumbent 실제 체결 모델 검증과 **해당 family의 기존 deterministic/AI/실제 실행 품질·same-stage contract**를 함께 충족해야 bounded 적용 가능하다. 모델 CF만으로 실체결 품질을 승인하지 않는다. 기존 first-use authority가 이 근거를 수용하지 않는 경우 named authority gap으로 명시하고 별도 contract successor를 검토한다. source 수리 성공을 근거로 임의 canary/1주 실주문을 열지 않는다.

경제성 adapter 자체는 source-only 결과를 반환한다. `allowed_runtime_apply`는 그 결과를 받은 family selector가 위 모든 predicate를 검증한 **별도 후보 레코드**에서만 결정한다. 이를 producer·Daily·AI guard·PREOPEN contract에 함께 반영하여, replay의 false 권한을 유지하면서도 검증된 후보가 자동 선정될 실제 경로를 만든다. 순수 schema 통과를 economic/promotion 통과로 대체하지 않는다.

PYRAMID와 AVG_DOWN은 같은 scale-in stage의 competing 후보일 수 있다. 겹치는 cohort의 두 변경을 동시 선정하지 않는다. incumbent/NO_ADD 대비 공통 비용·자본 기준의 검증된 증분 순익을 기존 selector에 전달해 one owner를 선택한다. 서로 다른 모집단 EV 수치만 직접 정렬하지 않는다. operator veto/lock가 우선이다.

### 7.3 상태·계속 개선 조건

- `valid_empty`: 실제 owner-ready 기회0, 관측 경로 정상. 유효 incumbent carry, 보류 원인 꾸며내지 않음.
- `source_gap`/`model_unsupported`/`authority_gap`: 입력·구현·권한 공백. owner 파일·predicate·closure test·필요 source를 명시. 신규 sample만 기다리는 상태로 숨기지 않음.
- `pending`/`censored`: 미완결 경로. 실제 maturation 또는 새 후행 source에서 재개; unchanged input 무한 replay 금지.
- `hold_sample`: 정확한10/20 decision 표본 미달. 유입0이면 ETA null이고 자연 유입 owner를 제시.
- `hold_no_edge`: 충분한 자료에서 delta/EV/순익/holdout 불충족. baseline 유지, 같은 데이터에서 다른 axis를 무제한 탐색하지 않음.
- `candidate_ready`: family guard·경제성·owner·scope·target-date를 통과한 다음 PREOPEN 후보. PID 적용·실수익과 구분.

구현에서 실제 canonical label owner와 맞춰 기존 equivalent label을 우선 사용한다. 표의 의미를 위해 새 global taxonomy를 만들지 않는다. missing EV를0으로 출력하던 PYRAMID grid 필드는 decision path에서null+reason으로 수정하고 명시적인 valid NO_ADD0과 분리한다.

## 8. SI4 — 기존 자동 정책 발행·PREOPEN·실제 소비

1. family 보고서에 source hashes·paired universe·calibration cutoff/holdout·cost/fill model·before/after·scope·bounds/step·rollback·quality_update_id를 포함한다. final-source receipt와 report body hash를 결속한다.
2. Daily merge 및 PREOPEN direct loader는 동일 schema/evidence generation을 사용한다. 두 경로에서 같은 후보를 중복 apply하지 않는다. AI correction은 해당 evidence digest/quality ID에 bind하고 단독 action authority는 없다.
3. 검증된 후보는 **기존 calibration artifact/선정 manifest/publisher**에 원자적으로 발행한다. scalar env 후보에 불필요한 새 정책 파일을 추가하지 않는다. 실제 loader가 dated artifact를 요구할 때만 기존 namespace에 생성한다.
4. next trading date는 프로젝트의 기존 시장 calendar/resolver로 구한다. 자정 넘어도 source target-date를 유지하며 source date와 apply date를 혼동하지 않는다. freeze·stale·source 변경·유효기간 초과면 신규 후보를 적용하지 않고 기존 명시 carry/lock 계약을 따른다.
5. 동일 stage selector·operator override·AI/deterministic guard가 통과하면 정상 PREOPEN env에 기존 두 key만 반영한다. alias/retired family/quantity/cap/provider/bot key를 추가하지 않는다. bounded 후보마다 수동 env 수정·별도 승인을 요구하지 않는다.
6. 기존 scheduled start/restart 계약에서 actual PID의 loaded rule·candidate version/hash/scope를 확인한다. intraday watcher로 자동 재기동하지 않는다. 코드 selected/manifest env_written/PID_consumed를 별도 기록한다.
7. 자연 판단에서 applied policy/quality ID·before/after 판정·actual submit/fill·terminal을 결속하고 R6로 보낸다. 기회0이라도 PID receipt는 확인 가능하지만 behavior_changed와 경제성 acceptance는 미완료다.
8. source→EV/runtime approval/gap/lineage/tower→checklist→strict `--require-summary-handoff`→controller/finalization에 같은 generation을 전달한다. verifier/controller self hash는 summary source에 넣지 않는다. stale PASS나 이전 DONE을 신규 후보의 성공으로 재사용하지 않는다.

Acceptance: eligible fixture 자동 발행→PREOPEN 선택→허용 env key→loader/hash/PID verifier→natural attribution 경로가 연결되고, no-edge/missing/owner-conflict는 정확한 hold/carry/fail로 닫힌다. unsupported scope가 공통 axis에 섞여 적용되지 않는다.

## 9. SI5 — 비용을 줄이는 최소 변경

경제성 수정의 reference 의미를 먼저 고정한다. 이전 filled-only/fixed-exit 결과와 일치하는 것을 새 모델 correctness로 삼지 않는다. 비용 절감 diff는 수정된 reference와 동일 결과인지 확인한다.

- 현재값·scope·global preflight/authority를 **싼 receipt로 먼저 판정**한다. 결정 불가면 자동 적용 후보 계산은 멈추고 coverage/disposition 요약은 생성한다. 유효 과거 cohort 탐색은 cached source facts로 계속할 수 있으나 신규 provider replay를 불필요하게 시작하지 않는다.
- `_collect_exact_evidence` 누적 raw full scan을 기존 일자별 source projection/checkpoint로 대체한다. O2/O3에 검증된 source cache가 있으면 그대로 확장하고 별도 저장 engine을 만들지 않는다. snapshot physical generation·ctime/inode/size/mtime·logical identity·본문 digest·parser/semantic SHA·원 provenance를 검증한다.
- 한 번의 불가피한 cold pass에서 해당 family의 config/route/sizing/frame/terminal 및 coverage만 보존한다. 필요 원천을 버리는 early stage filter는 금지한다. tiny per-day JSON/기존 shard 정도로 시작하고 대량 raw를 여러 consumer가 다시 hash하지 않는다. corrupt/old/cache busy는 해당 day의 원 streaming fallback이다.
- 날짜 append는 신규 day와 unresolved episode에 영향을 준 terminal/frame만 처리한다. 과거 정정은 해당 day·dependent episode·economic aggregate만 무효화한다. 정책/cost/exit/model 변경은 해당 결과를 무효화하고 비용 불변 raw facts는 재사용한다.
- episode가 여러 day를 넘으면 pending index에 기존 identity를 유지하고 후행 late shard를 합친다. calibration/holdout 경계 이동은 집계를 다시 하되 cached terminal을 미래 정보로 소급하지 않는다.
- 변경 없는 episode replay와 provider 답변은 existing verified cache를 사용한다. TERM/부분 write는 완료 checkpoint로 승격하지 않는다. 동일 source의 retry는 atomic completed 결과를 재사용하며 concurrent wrapper의 overwrite를 막는다.
- family별 선택/집계는 deterministic order/tie-break를 유지한다. 후보 state는 공유하지 않고 immutable source facts만 공유한다. canonical counts/EV/순익/선정 parity가 깨지는 sampling·grid 축소·top-symbol 제한은 하지 않는다.

검증은 representative frozen source **한 묶음**의 cold/warm/한 날짜 append/정정·중단 회귀로 제한한다. 기존 command PERF를 사용하고 새 benchmark suite·scale matrix·CPU50% 의무 목표를 추가하지 않는다. 합격 기준은 결과 parity와 warm의 unchanged historical full scan 없음, append의 신규 source/의존 episode 처리, resource 계약 불변이다. 한 번의 warm 계측에서 cache 검증/쓰기 비용까지 포함해 악화되면 그 최적화만 보류한다. 이후 성능은 정상 장후 한 회의 기존 receipt로 관찰하고 새 결함/병목이 없으면 반복 점검을 끝낸다.

## 10. SI6 — 적용 후 실제 EV·순이익과 다음 개선

모델 결과는 `modeled_policy_delta`, 실제 결과는 `actual_policy_outcome`으로 기존 R6/EV 보고서에서 분리한다. 선정 당시 evidence와 실제 applied version/hash·quantity/cost/venue/session을 join한다. 실제 fill과 독립 NO_ADD/다른 정책의 모델을 비교하는 값은 모델 비교임을 표시하며 실제 추가 이익이라고 합산하지 않는다.

대조는 사전에 정의한 같은 owner·scope·원 정책 context의 applied/not-applied cohort 또는 chronological post-apply version window다. 시장 차이·기회 유입·fill/부분체결·출구·비용·자본 점유를 설명하고 applied cohort가 없어도 성과를 합성하지 않는다. 같은 stage에 새 shadow/canary lane을 만들어 대조 표본을 채우지 않는다.

기존 rolling/cumulative 보고에서 actual COMPLETED+valid cost/PnL, 제출·체결 참여율, 증분 모델의 예측/실제 오차, 손실 tail·hard-stop 지연·주문 오류·노출을 본다. daily-only 승률·총합으로 full promotion하지 않는다. severe loss/주문 실패/provenance/owner 충돌/stop 지연은 기존 safety rollback을 적용하고, thin sample/no-edge는 calibration hold이며 old lock을 임의 해제하지 않는다.

다음 개선은 evidence에 따라 한 축씩 진행한다.

1. SI0–SI4에서 기존 두 axis의 정상 후보/자동 소비를 먼저 닫는다. 구조결손은 계속 수리하고, 실제 no-edge는 가설의 실패로 인정한다.
2. 새 실제 model-error가 가격/체결/exit에서 발생하면 기존 adapter의 그 부분만 개선한다. threshold 완화로 source 오류를 상쇄하지 않는다.
3. AVG_DOWN quantity/leg 개선은 기존 `scale_in_split_order_plan`에서 action/exit 고정 paired 비교로 수행한다. action·quantity·leg 동시 변경으로 귀속을 잃지 않는다.
4. PYRAMID AI/pressure/continuation 축이나 AVG_DOWN 다른 route를 열려면 기존 축의 충분한 valid 관측에서 이름 붙은 단일 bottleneck과 개선 가설이 있어야 한다. 같은 owner evaluator에 작은 등록 후보를 추가하고 별도 package/framework를 먼저 만들지 않는다. bounds/approval 변화는 별도 contract 변경이며 본 계획에서 자동 허용하지 않는다.
5. 양의 holdout/실제 R6가 반복되면 기존 family promotion 계약으로 개선을 이어간다. source/단계가 이미 닫혔고 새 입력/가설/defect가 없으면 unchanged replay·추가 taxonomy·테스트 확대를 중단한다.

## 11. 실행 순서·산출물·종료 조건

| Package | 직접 의존 | 완료 산출물 | 종료 시험 |
| --- | --- | --- | --- |
| SI0 | current source/release 계약 확인 | 기존 report의 census/current baseline/source disposition | blocked·valid-empty·override/missing 보존식 |
| SI1 | SI0 | 같은 source 관측의 resolver/sizing/frame 결속 | baseline-blocked challenger 입력 및 미래/guard 차단 |
| SI2 | SI1 | report 내부 검증된 paired terminals/economics | 독립 arm·fill/비용/exit 및 같은 실행의 후보 입력 |
| SI3 | SI2 | calibration 고정 winner·holdout·family guard 결과 | positive candidate와 no-edge/누락/owner-conflict 분기 |
| SI4 | SI3 + 해당 consumers | 기존 자동 publisher/PREOPEN/R6 연결 | end-to-end fixture·schema/hash/date/허용 keys/strict |
| SI5 | SI0 source contract, SI2/3 reference 의미 | 기존 source/replay checkpoint 최소 확장 | 동일 결과·warm/append/정정/TERM 한 묶음 |
| SI6 | SI4의 허용 배포·자연 소비 | 기존 실제 version별 EV/순익·다음 disposition | source/selection/PID/자연/actual 경제성 별도 대사 |

SI5의 cheap preflight·day facts 재사용은 SI1/2와 병행 설계할 수 있다. SI3/4를 CPU 목표 달성 대기로 묶지 않는다. package별 `implementation → self review → fix → re-review → targeted validation`로 닫고 in-scope defect는 후속 지시 없이 수리한다. 작업본에서 유효 후보 경로를 검증한 후 허용된 최소 regenerate/release follow-up만 수행한다. active wrapper가 쓰는 code/artifact를 바꾸지 않는다.

code closure는 SI0–SI5의 변경 범위 finding0/targeted PASS/consumer 연결이다. 운영 closure는 selected release·scheduled producer·actual PID·정상 장후 generation/strict이다. 경제성 closure는 **별도의** holdout 모델 ΔEV·ΔNet과 실제 post-apply cost-adjusted EV/net 계약 충족이다. 정책0은 source/sample/no-edge/authority 중 원인을 분류하며 코드완료와 이익완료를 섞지 않는다.

## 12. 적정 검증·문서 전달

기존 test 파일에 계약을 검증하는 fixture만 추가한다. 실제 변경한 함수/consumer의 suite만 선택하고 관련 없는 trading·sim·widget 전수 suite를 매번 실행하지 않는다.

필수 회귀는 아래를 묶어서 수행한다.

- 실제 ADD0·blocked/미제출·zero fill·부분체결·no-ADD 이후 청산: population 보존·arm state 분리·valid0/null 구분.
- baseline 임계값 차단·fresh resolver/BBO 일치·quote stale/future/cross epoch·budget missing/quantity0: source-only 계산과 live guard 불변.
- 독립 ADD/NO_ADD 평균단가/quantity/exit 변화·frame gap·hard/protect/emergency exit·AI state digest 불일치: 누락을 HOLD/이익으로 덮지 않음.
- 과거 policy implementation/cost 수정·terminal ID 충돌·late terminal·duplicate decision·capture cap: 정확한 제외/무효화·coverage 대사.
- calibration 고정/holdout 실패·다른 후보 재선정 금지·동일 stage 충돌·operator lock·신규 ADD 양수 및 제거형 tightening 분기.
- candidate report→Daily/direct PREOPEN→manifest→verifier/R6/strict: version/hash/target-date·허용 key·모델/actual authority 일치.
- warm/append/정정/TERM 중단 cache: 수정 완료 reference와 counts/paired universe/EV/순익/선정 parity.

사용 파일: `src/tests/test_scalping_pyramid_intraday_feedback.py`, `test_scalping_pyramid_quality_calibration.py`, `test_scalping_avg_down_recovery_calibration.py`, `test_avg_down_replay.py`, `test_avg_down_policy_replay.py`, `test_scale_in_incremental_counterfactual.py`, `test_sniper_scale_in.py`, `test_scale_in_split_order_plan.py`와 실제 변경된 PREOPEN/source-quality/EV/verifier/wrapper의 기존 tests. 전체를 항상 실행하라는 목록이 아니다.

Python 변경은 project `.venv` targeted pytest·관련 compile, wrapper 변경은 `bash -n`·해당 contract tests, 마지막 `git diff --check`. 설치/업그레이드 불필요. 검증된 범위 뒤에는 새 변경/실패/미해결 우려가 없으면 test와 benchmark를 반복하지 않는다.

후속 automation/wrapper 규칙 변경 시 해당 operating instruction·checklist를 같은 changeset에서 정합화한다. README/Plan Rebase/prompt/AGENTS의 명시 요청 없는 변경은 하지 않는다. 본 문서는 monitoring invocation이 아니다. 문서·owner/link 검증 후 print-only parser만 실행하고 외부 sync/token 조회는 하지 않는다.

사용자 실행용 표준 sync는 한 개만 남긴다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
