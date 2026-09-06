# One-share opportunity / submit-drought recheck 최종 재점검

Review: 2026-09-06 KST. Source: 2026-09-04. Prepared PREOPEN: 2026-09-07.

Current review: `implementation_review_pass` (§10), 검토 범위 미해결 finding 0건. 사용자 구현 지시에 따라 §9의 R1→R5 보완·수정·재리뷰·검증을 종결했다. 자연 적용/EV 성과는 OPEN이다. §§1–9는 이전 기록이며 현재 실행 범위·판정은 §10이 소유한다.

## 1. 범위와 목적

이번 요청은 재점검이다. 기존 dirty worktree와 산출물을 읽고 메모리 내 반례와 관련 회귀로 검증했다. 실행 코드, operator lock, runtime env, cron, 주문, provider, bot 상태는 변경하지 않았다. 본 리뷰와 다음 실행 항목만 기록한다.

- `one_share_threshold_opportunity`: 강제 1주 제한의 기회비용을 primary blocker와 post-sell 결과로 분리하고 기존 family의 source-only 개선 근거를 만든다. 보고서 자체에 PREOPEN/실주문 권한이 없는 것은 결함이 아니다.
- `entry_ai_gate_backtest -> entry_opportunity_recheck_runtime`: 기존 WAIT/회복 후보 중 해당 recheck로 해결 가능한 submit drought가 있을 때 bounded probe 경로를 켜고 실제 submit/fill/청산을 환류한다. 무기한 강제 ON이나 신규 튜닝축 추가가 목적은 아니다.
- 기대효과는 실행 가능한 기회 회복과 비용 차감 순이익 개선이다. 기회 수, armed 수, 설정 ON, env verify PASS는 그 효과의 실현 증거가 아니다.

기준은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §§1–8과 [2026-09-07 checklist](../checklists/2026-09-07-stage2-todo-checklist.md)의 목적·강제 규칙이다. 9월 6일자 checklist는 없으므로 다음 예정 영업일의 실행 소유자를 사용했다. AGENTS의 과거 snapshot보다 Plan의 현재 결정과 exact-date 산출물을 우선했다.

## 2. 현재 증거와 자동화 연결

- [One-share report](../../data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_2026-09-04.json): forced record 5,523개, post-sell join 360개, 제외 gap 6개, 기존 family source-only 기회/작업지시 2개. `automatic_implementation_candidate_count=0`, `runtime_effect=false`, `allowed_runtime_apply=false`. 이 표본은 신규 drought controller의 수익 표본이 아니다.
- [Entry AI gate report](../../data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_2026-09-04.json): 9월 2·3·4일 source-quality PASS 및 critical/addressable. 신규 exact armed/direct/completed는 `0/0/0`, 비용 차감 EV와 net PnL은 없다. attempt ID 없는 기존 arm 104건은 별도 집계다. 현재는 조건부 시험 적용 근거이지 submit drought 해소·순이익 증가 입증이 아니다.
- [7월 3일 lock](../../data/threshold_cycle/operator_runtime_env_locks/entry_opportunity_recheck_2026-07-03.json)은 `enabled=false`, `explicit_close_required=false`; replacement owner는 장후 report와 PREOPEN apply다.
- [9월 7일 PREOPEN plan](../../data/threshold_cycle/apply_plans/threshold_apply_2026-09-07.json)과 [runtime env](../../data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-07.json)는 recheck ON, intraday escalation OFF다. 저장된 handoff verification은 PASS, unverified selected family는 0개다.
- 설치된 weekday cron: 20:10 postclose, 07:35 `auto_bounded_live` PREOPEN, 07:55 기존 bot launcher 기동. [장후 wrapper](../../deploy/run_threshold_cycle_postclose.sh)는 두 보고서를 기본 실행하고 [장전 wrapper](../../deploy/run_threshold_cycle_preopen.sh)는 apply를 호출한다. 이 family는 [deterministic guard](../../src/engine/threshold_cycle_preopen_apply.py:3796)로 매일 별도 사용자 승인 없이 판정된다.
- [launcher](../../src/run_bot.sh:440)는 당일 env와 persistent/dated overlay를 읽고 handoff를 검증한다. 필요한 probe-first DAILY/1주/post-probe resolver 설정은 현재 persistent operator env에 있다. 다음 날짜의 실제 PID 소비와 exact submit/청산은 이번 리뷰에서 실행하거나 입증하지 않았다.

## 3. 확인된 결함

### F1 · P1 · 유효 손익 1건으로도 10건 확대 조건 통과

위치: [exact 집계](../../src/engine/scalping/entry_ai_gate_backtest.py:414), [확대 판정](../../src/engine/scalping/entry_ai_gate_backtest.py:568), [PREOPEN 검증](../../src/engine/threshold_cycle_preopen_apply.py:1978).

완료 chain 개수와 유효 profit/net PnL 표본 수가 분리되지만 판정은 `exact_completed_count >= 10`만 확인한다. NULL 손익은 평균에서 제외되어도 경제성 계약 결손으로 표시되지 않는다.

- 재현: terminal 10개 중 1개만 EV `+0.03%`, net PnL `+15원`, 나머지 9개 손익 누락. completed=10, profit sample=1, net sample=1, contract gap=0, escalation=true였고 PREOPEN validator도 통과했다.
- 보완: 동일 exact ID의 비용 차감 EV와 net PnL이 모두 유효한 paired-economic 표본으로 floor를 판단한다. 결손은 row exclusion/계측 작업지시로 분리하고 0 또는 유효 경제성으로 대체하지 않는다. 확대·경제성 OFF 모두 같은 분모를 쓴다.
- 완료 시험: 10 terminal/1 valid pair는 확대 불가·hold_sample; 10 valid pair/양의 EV와 net은 다음 기존 guard 검증으로 진행. producer와 consumer 결과 일치.

### F2 · P1 · 무기한 누적 부진이 사실상 영구 OFF를 만든다

위치: [누적 창](../../src/engine/scalping/entry_ai_gate_backtest.py:451), [baseline 전체 조회](../../src/engine/scalping/entry_ai_gate_backtest.py:480), [stop](../../src/engine/scalping/entry_ai_gate_backtest.py:524).

exact 판정 창은 6월 5일부터 현재까지다. arm 20건/직접 submit 1건으로 5% stop이 발생하면 OFF 동안 새 arm이 생기지 않아 stop 근거가 사라지지 않는다. 새 코드나 시장 조건이 과거 누적을 자동 종료시키는 경로도 없다.

- 재현: 같은 누적 20 arm/5%에서 최신 drought 요건이 다시 충족되어도 9월 4일·10월 8일 모두 activation=true, desired_enabled=false.
- 보완: 전체 누적은 감사용으로 유지하고 운영 판정은 적용 version/episode와 최근 유효 window에 결속한다. 경제성·source-quality 중단을 구분하고 원인 해소·새 source-only 근거·bounded cooldown 후 기존 cap 안에서 재평가할 상태 전이를 둔다. 시간 경과만으로 손실을 무시하고 ON시키지 않는다.
- 완료 시험: 부진 OFF → 근거 변화 없으면 유지 → 수리/새 유효 근거/정의된 재평가 조건 충족 시 bounded 후보. 과거 결손 row 하나가 모든 이후 version을 영구 차단하지 않아야 한다.

### F3 · P1 · family env 누락 후 자동 재활성화 실패

위치: [현재값 복원](../../src/engine/scalping/entry_ai_gate_backtest.py:740), [WAIT/probe 고정 계약](../../src/engine/threshold_cycle_preopen_apply.py:1903).

장후 자료 부족 등으로 family가 PREOPEN에서 빠지면 current 값이 코드 기본값으로 복원된다. 기본값은 `require_explicit_buy_action=true`, `allow_wait_probe_intent=false`지만 consumer는 반대 값을 요구하고 ON/OFF 외 값 변경도 금지한다.

- 재현: 로드된 빈 `env_overrides`와 충분한 최신 drought 근거에서 producer는 allowed=true/desired ON, consumer는 `drought_bounded_wait_probe_safety_contract_invalid`로 거절.
- 보완: enabled 상태와 승인된 bounded profile을 분리한다. 누락일은 fail-closed OFF, 자료 복구 후에는 승인 profile 복원 가능. 과거 enabled=true를 무조건 승계하지 않는다.
- 완료 시험: ON → report gap/family omitted → source 복구 → 자동 후보/PREOPEN 선택 성공. 사용자 lock 복원이 필요 없어야 한다.

### F4 · P1 · OR 분모를 AND로 강화해 심한 상류 drought 제외

위치: [Sentinel 원계약](../../src/engine/buy_funnel_sentinel.py:2221), [controller 분모 검사](../../src/engine/scalping/entry_ai_gate_backtest.py:186).

Sentinel은 `(AI >=20이고 submitted/AI <20%) OR (budget >=3이고 submitted/budget <=10%)`다. 새 요약은 AI와 budget 분모를 둘 다 충족해야 scope를 남긴다.

- 재현: AI 100/budget 0/submit 0, primary critical, UPSTREAM_GATE이면 원계약상 상류 drought지만 controller denominator/critical/addressable은 모두 false.
- 보완: 발생한 비율 branch의 분모만 요구하고 branch·비율·count provenance를 유지한다. **AI AND budget 동시 충족 조건은 제거 대상**이다. latency-only 활성화 금지와 quote/broker/account/quantity 안전은 유지한다.
- 완료 시험: AI 100/budget 0과 AI<20/budget>=3을 각 branch로 평가하고 해당 recheck가 해결 가능한 causal branch만 활성화한다.

### F5 · P1 · 서로 다른 venue/session의 critical과 원인 결합

위치: [scope key 소실](../../src/engine/scalping/entry_ai_gate_backtest.py:151), [독립 any 집계](../../src/engine/scalping/entry_ai_gate_backtest.py:215), [활성화](../../src/engine/scalping/entry_ai_gate_backtest.py:503).

`by_venue_session` key를 버린 뒤 critical/addressable에 독립 `any()`를 적용한다. 동일 scope에서 둘 다 성립하는지 검사하지 않는다.

- 재현: KRX는 latency-only critical, NXT는 noncritical이지만 UPSTREAM_GATE이면 일자 요약 critical=true/addressable=true. 실제 critical AND addressable scope는 0개.
- 보완: venue/session·causal branch를 보존하고 동일 scope에서 critical/addressable/분모를 함께 검증한다. 적용 scope도 evidence에 결속하고 다른 venue 근거로 공통 runtime 권한을 넓히지 않는다.
- 완료 시험: 위 교차 scope 반례는 활성화 불가, 동일 허용 scope의 실제 addressable drought는 통과.

### F6 · P2 · 일반 lifecycle fallback과 실제 partition 불일치

위치: [family 전용 조회](../../src/engine/scalping/entry_ai_gate_backtest.py:255), [registry](../../src/utils/threshold_cycle_registry.py:151), [sell outbox companion](../../src/engine/sniper_execution_receipts.py:2974), [기존 테스트](../../src/tests/test_entry_ai_gate_backtest.py:981).

집계기는 recheck family만 읽는다. 실제 registry에서 일반 submit은 dynamic_entry_price_resolver, sell_completed는 statistical_action_weight, position_rebased_after_fill은 recheck 필드만으로 threshold family가 없다. `entry_opportunity_recheck_runtime_family`도 이 routing을 바꾸지 않는다.

- 검증: 실제 registry 호출로 위 routing을 확인했다. fallback 테스트는 일반 이벤트를 수동으로 recheck partition에 넣으므로 실제 producer routing 검증이 아니다.
- 전용 이벤트가 모두 기록되는 happy path는 있다. 그러나 sell companion 발행 실패는 일반 outbox의 성공 반환에 반영되지 않아 전용 이벤트 누락 시 자동 복구를 보장하지 못한다.
- 보완: durable exact-attempt journal/outbox 또는 원래 family의 lifecycle 복구 join 중 하나를 소유 경로로 정한다. 원래 stage family를 무조건 바꿔 다른 소비자를 깨뜨리지 않는다.
- 완료 시험: 실제 registry/logger로 submit/fill/sell을 기록하고 companion 실패를 주입해도 정확히 한 chain이 복구되거나 명시적 재시도/source gap으로 닫혀야 한다. 조용히 낮은 전환율로 환산하지 않는다.

## 4. 조건 달성 가능성과 유지·제거 판정

| 조건 | 판정·조치 |
| --- | --- |
| 최신 3일 중 2일 critical, 최신일 addressable | 현재 9/2~4에서 이미 달성. 횟수 유지, branch/scope 수정 |
| AI와 budget 분모 동시 충족 | 상류 차단이 심할수록 못 채우는 추가 조건. AND 제거, 원래 OR branch 복원 |
| 비용 차감 EV>0와 net PnL>0 | 1.1% 같은 고수익 floor가 아니라 작은 양의 수익도 허용. 유지하되 paired 유효 표본 사용 |
| completed 10개 이후 확대 | 수치만으로 과도하다고 단정 불가. 실제 도달기간 미확인. 10 terminal이 아닌 10 valid pair로 판단, 부족하면 확대 없이 hold_sample |
| arm 20개에서 direct submit<10% OFF | 부진 감지는 필요. 무기한 누적 stop/복귀 부재를 version/window 중단·재평가로 교체 |
| stale/DANGER/broker/account/order/quantity/cooldown | 완화 근거 없음. 유지 |

하루 3 recovery/최대 10 recheck 설정만으로 표본 확보 일수를 보장할 수 없다. 일반 경로는 arm이 recovery count를 소비하며 bounded exploration은 caller-verified submission count를 사용하는 분기가 있으므로 분모도 구분해야 한다. 실제 accepted submit→fill→valid terminal 비율로 도달기간을 판단한다. exact 0개는 계측 시작점이지 성공이나 영구 폐기 근거가 아니다.

One-share 보고서는 기존 family source-only 진단으로 유지한다. 신규 live 튜닝축·상시 강제 lock·보고서 단독 실주문 권한은 추가하지 않는다. 코드 개선 workorder 존재와 코드 자동 수정·배포는 별개다.

## 5. 검증과 다음 실행 소유자

- 기존 회귀: `test_entry_ai_gate_backtest`, `test_entry_opportunity_recheck`, `test_one_share_threshold_opportunity` 73 PASS; `test_threshold_cycle_preopen_apply`, `test_pipeline_event_logger` 255 PASS. 합계 328 PASS.
- 추가 read-only 재현: 현재 후보 validator 통과, F1~F5 반례, F6 registry routing 확인. 기존 테스트 PASS가 결함 부재를 의미하지 않는다. 반례는 아직 regression test 파일에 추가하지 않았다.
- 문서 재리뷰 후 checklist parser PASS(신규 OPEN 2건 인식), diff whitespace PASS를 확인했다. broker/API 실행, bot 재기동, 보고서 재생성, PREOPEN 재적용은 하지 않았다. `korstockscan-review-gate`의 런타임 후속 실행 승인 조건은 미충족이다.
- 실행 소유자: checklist `EntryRecheckFinalReviewRepair0907`, `EntryRecheckNaturalAttribution0907`. 기존 `EntryOpportunityRecheckConditionalAutomation0907` 완료 표시는 과거 구현·env 생성 기록이며 결함 수정 완료나 실효 입증으로 재사용하지 않는다.
- 권장 순서: F1 유효 경제성 → F4/F5 분모·scope → F3 profile 복귀 → F2 window/state → F6 durable attribution → 반례 회귀/재리뷰 → exact-date PREOPEN 재검증 → 정상 운영의 PID/실제 chain 귀속 확인. 현재 저장된 ON 후보는 validator를 통과하지만 무개입 운영 완결 판정은 보류한다.

## 6. 후속 구현 및 재리뷰

Status: `implemented_integration_validation_blocked_by_concurrent_changes`. 최종 무결함·장전 적용 완료 판정은 아직 내리지 않는다.

- 기존 family 내부의 공통 판정 계약을 [entry_recheck_policy.py](../../src/engine/scalping/entry_recheck_policy.py)에 분리했다. scalping 정책 소유 모듈이며 engine root에 새 producer나 독립 튜닝축을 만들지 않았다. report schema v5/controller v2와 exact attribution v2를 사용한다.
- F1: 동일 terminal에서 유효한 EV/net PnL pair만 분모로 사용한다. 서로 다른 결손 terminal 행의 값을 합쳐 pair를 만들지 않는다. finite 값·receipt 경제성 완결·청산 1주를 확인하며 원래 정밀도의 비용 차감 수익률을 유지한다. 선택 시장·세션별 10 valid pair/양의 경제성도 확대 전에 확인한다. 기본 bounded 경로는 이 확대 표본이 없어도 drought 조건으로 평가한다.
- F2: 최근 20거래일과 causal episode의 교집합, 원 arm 시각, exact v2로 평가한다. 부진 stop은 감사 가능한 controller state로 유지한다. 3거래일 cooldown만으로 풀지 않고 addressable 원인 scope/axis 변화 또는 관측된 drought 해소 후 재발을 요구한다. 재평가 episode는 판정일 다음 날짜부터 시작하여 과거 terminal을 새 실적으로 쓰지 않으며 즉시 확대하지 않는다. 같은 날짜 재산출은 당일 이전 상태에서 다시 계산한다. 현재 runtime OFF를 보고서의 과거 ON 추천만으로 유지·승계하지 않는다.
- F3: 승인된 고정 WAIT/probe profile과 enabled 상태를 분리했다. 로드된 manifest에서 family가 빠져 기본값으로 돌아가도 새 유효 drought 조건으로 profile을 복원할 수 있다. 구 mode/무기한 lock만으로는 현 family를 재활성화하지 못한다.
- F4/F5: OR 분모 branch를 복원하고 동일 scope의 critical/addressable을 확인한다. scope key·counts·branch를 보존하여 PREOPEN에서 재계산하고 `ALLOWED_SCOPES`를 실제 runtime에 전달한다. 미선택·unknown scope, 누락 scope env는 fail-closed다. 다른 family가 단지 `same_stage_owner_claim=false`라고 기재해 owner 검사를 빠져나가는 경로도 막았다.
- F6: 전용 청산 companion 실패 시 기존 durable outbox leg를 완료 처리하지 않는다. 일반 sell_completed의 statistical_action_weight partition을 원래 routing 그대로 읽고 exact 상태를 복구한다. 실제 logger→raw→backfill→family partition→집계 통합 시험과 중복 전파/누락 companion 시험으로 검증한다.
- 추가 재리뷰: 재arm 시 이전 주문/fill 식별자 잔류 제거, legacy attempt의 v2 오인 방지, episode 밖 원 arm의 늦은 청산 제외, NaN/Inf·모순된 중복 경제성·집계 분모 불일치 차단, source 날짜와 장전 요청 날짜 불일치 차단, 이전 controller 상태 형식·시간 검증을 보완했다.
- 식별 가능한 결손/충돌 attempt는 명시적 `excluded_attempts`로 전환율·경제성 분모에서 먼저 제외한다. 제외 개수/사유 계약이 닫히지 않거나 식별 불가능한 JSON/source-quality 결손이면 family 적용을 막는다. 작은 양의 수익률(예: `0.001%`)을 표시용 `+0.00`으로 덮어쓰지 않으며 fractional/boolean/비유한 청산 수량은 1주 경제성으로 인정하지 않는다.
- controller state JSON은 fsync/atomic replace로 게시한다. 게시 실패 시 기존 checkpoint를 보존한다. 손상 상태에서 파생된 freeze report를 새 stop 근거로 삼지 않고 원본을 재검사하여 원본 수리 후 자동 복구할 수 있게 했다.

### 6.1 통합 검증 중 발견한 별도 동시 변경

- 2026-09-06 06:41~06:49 KST에 이번 recheck 수정과 별개인 `scalping_adm_ldm_retirement_20260906` 변경이 동일 worktree의 PREOPEN consumer, 장후 wrapper, entry AI report producer에 반영되는 것을 확인했다. 신규 `src/engine/lifecycle/retirement.py`, `src/engine/scalping/entry_observation_source.py`와 관련 수정이 현재 병행 작업 범위다. 이를 되돌리거나 폐기 정책을 임의로 변경하지 않았다.
- 동시 변경 전 핵심 회귀 1,439 PASS와 인접 회귀 374 PASS를 확인했다. 이후 공유 상태의 확대 회귀는 **1,797 PASS / 25 FAIL**이었다. 실패는 ADM/LDM·bridge·sim PREOPEN 선택 기대 및 삭제된 wrapper producer 기대와 관련되므로 기존 PASS를 현재 통합 PASS로 재사용하지 않는다.
- 추가 공유 producer 입력 경로 변경 후 기존 report fixture 검증도 2건 실패했다. 신규 입력이 기존 fixture 격리를 우회해 실제 data를 탐색하는 것을 확인하여 **우리 pytest 프로세스만** 중단했다(35 PASS / 2 FAIL / 나머지 미실행). 별도 작업의 pytest 프로세스와 파일은 중단하거나 되돌리지 않았다.
- 마지막 보완 후 제한 회귀는 1,261 PASS(`entry_recheck_policy`, runtime, receipt, sniper scale-in, one-share, location gate, logger, backfill)이고 family 전용 PREOPEN 테스트는 9 PASS(212 deselected)다. 두 범위 합계 1,270 PASS이며 공유 report 전체와 PREOPEN/wrapper 전체를 통과했다는 의미가 아니다. 수정 Python compile, 범위 내 Ruff, diff whitespace와 checklist parser(OPEN 2건 포함 36개 인식)는 PASS다. 공유 report에 동시 추가된 retirement import 관련 Ruff 2건과 기존 fixture 입력 경로 불일치는 해당 작업 통합 시 재검증 대상이다.
- `korstockscan-review-gate`의 통합 validation 조건이 닫히지 않아 이번 턴에서는 9월 4일 report 재생성, 9월 7일 PREOPEN 재적용, bot 재기동, 주문을 수행하지 않았다. 기존 준비 env에 새 `ALLOWED_SCOPES` 계약이 없으면 새 runtime/verify는 fail-closed이므로 **다음 장전 재적용 완료로 오인하면 안 된다**.
- 다음 소유자 `EntryRecheckFinalReviewRepair0907`는 OPEN으로 유지한다. 병행 폐기 작업 완료 확인 → 공유 producer/consumer/wrapper 통합 회귀 → 최종 재리뷰 → 9월 4일 report와 9월 7일 PREOPEN 재생성·verify 순으로 종결한다. 실제 기동 소비·submit drought 해소·순이익 증거는 별도 `EntryRecheckNaturalAttribution0907`가 소유한다.

## 7. ADM/LDM 폐기 완료 후 재개 검증

Status: `review_passed_preopen_prepared_natural_attribution_pending`. 검토·검증 범위의 미해결 finding 0건; 실제 PID 소비·수익개선은 별도 자연증거다.

- 사용자 완료 통보 후 Plan §1의 폐기 override와 현재 checklist를 확인했다. `entry_observation_source` 원천 정규화→실제 청산/반사실 분리→report→PREOPEN→runtime/receipt→장후 귀속을 다시 검토했다. 폐기 owner·prompt·bridge를 복원하지 않았다.
- 6.1의 공유 경로 실패는 재실행에서 해소됐다. 첫 회귀 1,871 PASS 후 재리뷰에서 source-quality 불합격 기간이 `recovery_observed`로 남을 수 있는 추가 결함을 발견했다. 유효한 3일 품질 창의 해소만 복귀 근거로 인정하도록 보완하고, 불량 자료의 해소→동일 원인 재발 반례를 추가했다.
- 보완 후 핵심/공유 통합 회귀 **1,872 PASS**, 인접 report/장후 verifier 회귀 **461 PASS**, 합계 **2,333 PASS**. Python compile, Ruff, Black, Bash syntax, diff whitespace도 PASS다. 전체 저장소 테스트를 모두 실행한 것은 아니다.
- 첫 report 재생성은 위 추가 결함 발견 시 게시 전에 중단했고 기존 JSON이 보존된 것을 확인했다. 최종 검증 뒤 표준 CLI로 재생성을 재개했다. 기존 report/장전 산출물 6개는 `/tmp/entry-recheck-preopen-20260907.Hu5dBh`에 백업했다.
- 설치된 weekday 20:10 장후 producer, 07:35 `auto_bounded_live`/`require_ai=true` PREOPEN, 07:55 정상 launcher 경로를 읽기 전용으로 확인했다. 본 작업은 cron이나 bot 상태를 변경하지 않는다.
- 운영 재적용 비교에서 scalp-sim 카탈로그가 생성기 변경으로 stale 제외되는 것을 확인하여 해당 source-only approval/catalog 2개를 추가 백업·갱신했다. 갱신 후에도 발생한 stale 오판은 폐기 필터가 `generator_provenance.files.lifecycle_bucket_discovery.py` 해시를 지우는 결함이었다. PREOPEN은 원본 해시를 무결성 비교에만 사용하고 정책·seed는 계속 폐기 필터를 통과하도록 좁혀 수정했다. 정상 해시/변조 해시와 폐기 seed 재유입 반례를 함께 검증했다.
- 위 최종 보완을 포함한 **최종 통합 회귀 2,345 PASS / 54.30초**, compile/Ruff/Black/Bash syntax/diff 검증 PASS. 이는 위 중간 회귀의 중복 합산이 아닌 새 통합 실행 결과다. 구현→리뷰→추가 수정→재리뷰→검증 루프를 종결했다.

### 7.1 실제 생성·소비 검증

| 항목 | 최종 결과 |
| --- | --- |
| 9/4 entry AI report | schema v5/controller v2 재생성; PREOPEN loader 후보 1건, 계약 오류 없음 |
| drought 창 | 9/2·9/3·9/4, source-quality 3일 PASS; 동일 scope의 OR 분모·addressable critical 충족 |
| 적용 scope | `KRX|KRX_REGULAR`, `NXT|NXT_AFTERMARKET`; 다른 scope는 허용하지 않음 |
| 기존 bounded profile | ON; score prior 69~74.999, 종목당 1회, 일일 recheck 10/회복 3, fresh/DANGER/probe-first/1주/post-probe resolver 유지 |
| 장중 확대 | OFF; exact armed/direct/fill/completed/valid pair 모두 0, EV/net PnL 없음 |
| 과거 표본 | 최근 20거래일의 attempt ID 없는 arm 101건은 legacy 진단이며 신규 exact 성과가 아님 |
| 9/7 PREOPEN | `auto_bounded_live_ready`, `require_ai=true`, 기존 parsed AI review; recheck는 전용 deterministic guard로 selected |
| 최종 handoff verify | PASS; selected family 23개, missing/runtime-policy-fail/unverified family 모두 0 |
| 파일→설정 소비 smoke | 생성 env+operator overlay를 격리 환경에서 로드: 두 scope, DAILY/1주 probe, fresh/DANGER, resolver, 확대 OFF 확인; bot/order 호출 없음 |
| 독립 sim catalog | `rising_missed_classifier_prior` 정책 1개/active seed 2개를 유지; 폐기 LDM 정책·seed 없음; sim-only/주문 금지 유지 |

갱신 전 백업과 비교해 새 family 추가는 없고 `lifecycle_decision_matrix_runtime`, `lifecycle_bucket_discovery_sim_auto_approval`만 선택에서 제거됐다. 기존 독립 `scalp_sim_auto_approval`은 위 해시 결함 보완 후 정상 유지된다. 7/3 recheck lock은 계속 disabled이며 복원·삭제하지 않았다.

누적 score/action 진단은 유효 source 44일, 실제 청산 join 293건과 counterfactual 27,145건을 분리한다. 과거 canonical WAIT/recovery 계약 결손과 score-only 진단 충돌이 남아 해당 sweep는 live threshold 승인 근거가 아니다. 기존 recheck의 현재 drought 판정 및 신규 exact 성과와 혼합하지 않는다.

`EntryRecheckFinalReviewRepair0907`는 완료 처리한다. 다음 9/7 정상 PREOPEN/07:55 기동 뒤 실제 PID 및 exact submit→fill→유효 청산 결과는 OPEN `EntryRecheckNaturalAttribution0907`가 소유한다. `--verify`는 PID 없이 실행했으므로 JSON의 `pid_passed=true`를 실제 PID 검증으로 해석하지 않는다. 이번에는 대상 report·sim-only catalog·장전 파일만 갱신했고, 전체 장후 체인·bot 재기동·실주문·provider 변경은 수행하지 않았다.

## 8. 일일 controller 분리 및 최종 보완

Status: `review_passed_daily_controller_applied_natural_ev_pending`. 구현·코드리뷰·수정보완·재리뷰 범위의 미해결 finding은 0건이다. 다음 거래일 설정 파일까지 자동 생성됐지만 실제 PID 소비와 비용 차감 EV 개선은 아직 자연 표본 대기다.

- 일일 runtime 판정을 `entry_recheck_drought_controller`로 분리했다. 이 경로만 최근 3거래일 drought와 현재 causal episode의 exact 귀속을 읽어 후보 최대 1건을 만들고, PREOPEN은 이 보고서만 소비한다. 기존 `entry_ai_gate_backtest`는 clean-baseline 누적 score/action 진단만 수행하며 `runtime_candidate_ready=false`, `allowed_runtime_apply=false`, runtime update 계약 없음으로 고정했다.
- runtime funnel을 `evaluated -> armed -> submitted -> filled -> completed -> paired`로 확장하고 평가 사유 및 scope별 사유를 남긴다. 한 scope의 paired 경제성, 장중 recovery mark, 확대 cap을 다른 scope가 재사용하지 않도록 scope별 escalation 목록과 상태를 분리했다. WAIT 상단은 실제 bounded profile과 같은 `74.999`로 맞췄다.
- 장후 wrapper는 controller를 매일 실행하고 누적 진단은 금요일 운영일 또는 명시적 on-demand에만 실행한다. 동일 target-date 이중 producer는 flock으로 fail-fast하며 원자 게시를 유지한다. PREOPEN은 controller schema/type/date/value/env/3거래일 window/재계산 결과를 검증하고 구 backtest로 fallback하지 않는다.
- 최종 리뷰 중 controller schema 미검증, scope 승인 간 cap 상태 오염, checkpoint migration 테스트 배치 오류, attribution version 문자열 중복, 최상위 source-quality PASS 누락을 발견해 보완했다. 잠금 파일은 경쟁 안전을 위해 유지하되 `data/report/**/.*.lock`만 Git ignore 대상으로 추가했다.

### 8.1 재생성 결과와 런타임 비용

| 항목 | 결과 |
| --- | --- |
| 9/4 일일 controller | `0.84초`, 최대 RSS `127,212KB`; source-quality PASS, 후보 1건 |
| 9/4 누적 진단 | `892.44초`, 최대 RSS `824,968KB`; 유효 source 44일, 실제 join 293건, counterfactual 27,145건 |
| 일일 경로 개선 | 누적 진단 대비 실행시간 약 `99.91%` 감소, 최대 RSS 약 `84.58%` 감소. 누적 진단 자체는 삭제하지 않고 주간/수동으로 격리 |
| 진단 성과 | score-only 최선 threshold 64의 실제 source-quality-adjusted EV `+0.052187%`/64건이나 10분 counterfactual `-0.184118%`/3,328건이며 canonical WAIT/recovery 표본은 0건. `diagnostic_apply_ready=false` |
| exact runtime 성과 | evaluated/armed/submitted/filled/completed/paired 모두 0, `runtime_not_evaluated`; 과거 ID 없는 arm 101건은 legacy 진단으로만 유지 |
| 9/7 PREOPEN | `0.71초`, `auto_bounded_live_ready`; KRX 정규장/NXT 애프터마켓 ON, 69~74.999, 일일 recheck 10/recovery 3, intraday escalation OFF |
| handoff 검증 | PASS; runtime-policy fail 0, unverified selected family 0. PID 없는 검증이므로 실제 프로세스 소비 증거는 아님 |

기존 9/7 산출물과 비교한 결과 다른 selected family의 추가·제거와 기존 env 값 변경은 0건이고, 신규 `KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_INTRADAY_ESCALATION_SCOPES=""`만 추가됐다. 갱신 전 파일은 `/tmp/entry-recheck-final-20260907.lzRWHL`에 백업했다.

### 8.2 목적 부합성과 향후 EV 판정

- 목적 부합: 매수를 늘리기 위한 score 완화가 아니라, 동일 scope의 실제 submit drought에서 canonical WAIT + EDGE + recovery intent + fresh quote + strong micro + probe-first 계약을 모두 만족한 1주 probe만 복구한다. DANGER, stale quote, broker/account/order/quantity/cooldown 및 hard/protect/emergency guard는 유지된다.
- 자동화: 장후 일일 controller 생성부터 다음 PREOPEN env 선택·무결성 검증까지 자동화됐다. 누적 진단의 실행 여부와 결과는 다음 장전 후보 생성의 선행조건이 아니다.
- 조건 달성 가능성: drought ON 조건은 현재 실제 자료로 충족했으므로 진입 자체가 영구 0이 되게 하는 구조적 허들은 제거됐다. 평가 호출부터 blocker가 계측되므로 앞으로 결과가 없을 때도 미호출, arm 전 차단, submit/fill/terminal 결손을 구분해 다음 보완점을 낼 수 있다.
- EV 가능성: 개선된 결과가 생성될 구조적 가능성은 높아졌지만 현재 exact 표본 0건이라 수익개선 확률이나 효과 크기는 아직 산정할 수 없다. score-only 양의 EV는 반사실 지표와 충돌하고 canonical 계약이 0건이므로 실전 확대 근거가 아니다. 다음 판정은 checklist의 OPEN `EntryRecheckNaturalAttribution0907`에서 실제 PID 소비와 scope별 exact chain, 비용 차감 paired EV/net PnL로 수행한다.

중간 보완 영향군 1,684 PASS와 controller/PREOPEN/wrapper 영향군 370 PASS 뒤, 현재 최종 코드 기준 확대 회귀는 **2,143 PASS / 44.62초**다. 각 수치는 중복 합산하지 않는다. Python compile, Ruff, Black, Bash syntax, diff whitespace 및 checklist parser(OPEN 36건 인식)도 PASS다. bot 재기동, 실주문, provider·수량·cap·hard-safety 변경은 수행하지 않았다.

## 9. 목적·자동화·조건 달성 가능성 재리뷰

Review: 2026-09-06 KST. 판정: `changes_required`; **일일 controller 유지·보완, 누적 diagnostic의 자동 정기 실행 제거/on-demand 전환 권고**. 이번 요청은 재점검이므로 실행 코드·cron·lock·PREOPEN env·bot 상태를 변경하지 않았다. 아래는 실제 발생 사고가 아니라 현재 코드에서 재현한 결함/운영 제약과 설계 검토 결과다.

### 9.1 기대효과와 자동화의 실제 범위

| 판단 축 | 확인 결과 | 판정 |
| --- | --- | --- |
| 상승/반등 기회 회복 | canonical WAIT/EDGE/recovery intent, fresh quote, micro confirmation, probe-first 및 기존 잔량 재검증을 요구한다. 단순 score만으로 BUY하지 않는다 | 전략 방향은 부합. 실제 초과 EV는 미입증 |
| 장후→장전→정상 기동 | 일일 controller→전용 PREOPEN consumer→exact-date env→정상 launcher가 연결된다. 9/7 파일은 두 scope ON/확대 OFF | 설정 생성·소비 경로 자동화는 구현됨. 다음 거래일 실제 PID 소비는 아직 미확인 |
| EV 기반 최적값 갱신 | controller는 기존 고정 profile의 ON/OFF·scope·확대 허용을 판정한다. 누적 score/action sweep는 diagnostic-only이고 runtime 후보를 만들지 않는다 | 자동 운영 제어와 최적 신호 파라미터 탐색은 다름. 후자의 완결을 주장할 수 없음 |
| 실제 성과 | 9/4 exact evaluated/armed/submitted/filled/completed/paired 모두 0, EV/net PnL 없음 | 수익개선 크기·확률 산정 불가. 단순 시간이 지나면 채워진다고도 단정 불가 |
| 작업 비용 | §8의 실측 controller 0.84초 vs 누적 diagnostic 892.44초 | 서로 다른 작업의 비용 비교다. 동일 알고리즘/전체 장후/장중 주문 latency가 99.91% 개선됐다는 뜻이 아님 |

근거: [일일 산출물](../../data/report/entry_recheck_drought_controller/entry_recheck_drought_controller_2026-09-04.md), [누적 진단](../../data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_2026-09-04.md), [장후 실행](../../deploy/run_threshold_cycle_postclose.sh:1619), [고정 profile](../../src/engine/scalping/entry_recheck_policy.py:29), [launcher](../../src/run_bot.sh:440).

§8.2의 “drought ON 충족이므로 영구 0 구조 제거”는 철회한다. ON은 평가 기회를 여는 설정일 뿐, 실제 eligible input·주문·청산·경제성 귀속이 모두 가능함을 입증하지 않는다. PID 소비 후 evaluated=0도 유효 입력 분모가 없으면 호출 결함이라고 단정하지 않는다.

### 9.2 새 발견과 권장 보완 순서

#### R1 · P1 · 거절된 새 평가가 이전 arm 상태를 상속해 자동 중단 유발

- [평가 로그](../../src/engine/sniper_state_handlers.py:64599)는 새 attempt ID를 만들지만 stock의 기존 arm 상태를 지우기 전에 기록한다. [공통 logger](../../src/engine/sniper_state_handlers.py:12965)는 stock의 attribution을 먼저 합치며, [collector](../../src/engine/scalping/entry_ai_gate_backtest.py:379)는 stage가 평가 거절이어도 `armed=true`이면 arm으로 센다.
- 메모리 반례: 이전 arm 상태를 보유한 stock에서 서로 다른 새 ID의 거절 평가 20건을 실제 collector에 입력하면 `evaluated=20, armed=20, submitted=0`, contract gap/identity conflict=0이 나온다. controller는 품질 PASS로 인정하고 전환율 미달 stop latch를 건다. 새로 arm한 거래 20건의 증거가 아니다.
- 보완: 평가 event는 현재 attempt 상태만 쓰고 다른 ID의 armed/submit/fill/terminal 필드는 상속하지 않는다. 기존 주문 custody 상태 자체를 지우지 말고 event snapshot 경계를 분리한다. collector도 명시적인 해당 attempt arm event/계약 없이는 arm으로 승격하지 않는다.
- 수용시험: 이전 arm→주문 전 차단→거절 재평가 20건에서 새 arm=0/허위 stop 없음; 이미 제출된 이전 주문의 fill/terminal 귀속은 계속 보존.

#### R2 · P1 · 정상 잔량 확장 후 수익이 경제성 표본에서 제외됨

- [귀속 함수](../../src/engine/scalping/entry_opportunity_recheck.py:136)는 경제성 완료를 `cumulative_sell_qty == 1`로 제한한다. [receipt](../../src/engine/sniper_execution_receipts.py:2796)는 포지션 누적 청산 수량을 전달하며 [collector](../../src/engine/scalping/entry_ai_gate_backtest.py:436)는 완료=false면 손익을 제외한다.
- 반면 일반 recheck는 `entry_opportunity_recheck_probe_only=true`를 기록해도 잔량 확장 금지 소비 조건이 아니다. 명시적인 `one_share_exploration`만 [별도 금지](../../src/engine/sniper_state_handlers.py:64714)하고, 일반 probe는 [기존 잔량 경로](../../src/engine/sniper_state_handlers.py:82587)를 이용할 수 있다.
- 동일한 유효 청산/양의 손익 입력에서 누적 수량 1은 인정, 2와 10은 제외되는 반례를 확인했다. 따라서 반등 확인 후 확장한 거래가 표본에서 빠지고, 1주로 종료한 거래만 남는 선택 편향/표본 미달 경로가 있다. 1주만 청산하는 명시적 exploration에는 이 수량 제약이 타당하다.
- 보완: 최초 1주 주문 ID→잔량 bundle/leg→전체 buy/sell receipt를 연결해 full-position 경제성과 probe-only 경제성을 분리한다. 잔량·추가매수의 비용/수량 대사를 완결한 cohort만 승인에 사용한다. 단순히 `==1`을 삭제하거나 수익 표본 확보를 위해 잔량 확장을 금지하지 않는다.
- 수용시험: 1주 단독·1+잔량·부분체결·부분청산·scale-in 혼합·중복 receipt별 순손익/EV 및 재처리 일관성. 타 owner의 손익을 recheck alpha로 잘못 귀속하지 않음.

#### R3 · P1 · 확대는 scope별이지만 손실 중단은 전 시장 합산

- [전환율/경제성 stop](../../src/engine/scalping/entry_recheck_policy.py:288)과 stop latch는 전역이다. scope별 경제성은 확대 목록에만 쓰이고 전역 reasons가 있으면 모든 allowed scope를 비운다.
- 반례 A: KRX 10건 EV +0.1%/순익 +100원, NXT 1건 EV -2%/순손실 -200원 → source-quality PASS인데 KRX 포함 모두 OFF.
- 반례 B: KRX 10건 EV +0.3%/+300원, NXT 10건 EV -0.1%/-100원 → 둘 다 기본 ON. NXT 확대는 막지만 자체 10건 손실에 따른 중단은 되지 않는다.
- 보완: 운영 경제성/전환율·episode window·stop/recovery는 동일 시장·세션 단위로 판정한다. 전체 포트폴리오의 hard safety와 정상적인 총량 제한은 별도 유지한다. 손실 scope를 흑자 scope의 근거로 유지하거나 반대로 흑자 scope를 무조건 중단하지 않는다.
- 수용시험: 위 양방향 반례와 scope별 recovery/새 episode에서 경제성·중단 상태 교차 사용 없음.

#### R4 · P2 · 제출 전 arm이 일일 회복 한도를 소진하고 늦은 시장을 차단

- [runtime arm 분기](../../src/engine/sniper_state_handlers.py:64658)에서 recheck와 buy-recovery 카운터를 동시에 올린다. 일반 mode는 accepted submit이 아닌 이 전역 카운터로 한도를 판단한다. verified submission override는 별도 exploration mode에만 연결된다.
- 반례: KRX에서 주문제출 없는 arm 3건 후 NXT의 fresh/canonical/micro 조건을 모두 만족한 새 후보도 `daily_buy_recovery_cap_exhausted`. 실제 recheck 사용은 3/10이고 NXT 제출은 0건이다.
- 보완 검토: 총 주문/cap 값을 올리지 않고 평가 시도와 주문 예약/accepted submit을 구분한다. 명확한 미제출은 예약을 반환하고 제출 여부 불명·미체결 실주문은 재대사 전까지 예약 유지한다. 기존 총량 안에서 scope별 기회 배분을 검토한다. 거래가 없는 scope의 cap을 무작정 늘리는 방식은 제외한다.
- 수용시험: arm 후 명확한 실패/주문번호 불명/accepted/fill/restart/동시 호출/시장 전환에서 중복 주문·한도 초과 없음. early-session 미제출만으로 later-session을 고갈시키지 않음.

#### R5 · P2 · 진단은 런타임 비필수지만 금요일 장후 체인의 필수 성공 작업으로 남음

- [wrapper](../../deploy/run_threshold_cycle_postclose.sh:1629)는 기본 weekly 진단 실행일에 동기 `run_postclose_cmd`와 artifact 대기를 수행한다. [ERR trap](../../deploy/run_threshold_cycle_postclose.sh:547)은 실패 시 전체 장후를 종료한다. 따라서 PREOPEN의 직접 입력 의존성은 제거했지만, 금요일의 시간/실패 의존성까지 제거한 것은 아니다.
- 현재 canonical WAIT/recovery 평가 가능 표본 0, 누적 diagnostic runtime 후보 0. 과거 누락된 recovery intent를 반복 sweep한다고 복원할 수 없다. 현재 892.44초는 9/4의 이전 재생성 실측이며 이번 리뷰에서 다시 실행하지 않았다.
- 권장: 정기 실행에서 제외하고 명시적 on-demand 진단으로 유지한다. 정기 실행을 남기려면 가벼운 source-contract 변화 검사와 구체적인 downstream 개선 workorder가 있는 경우에만 별도 실패 격리 작업으로 실행한다. 일일 controller 및 raw lineage는 유지한다.
- 수용시험: diagnostic 미실행/실패/timeout이 일일 controller·다른 장후 report·최종 완료를 막지 않음. controller 자체 실패/부재는 계속 FAIL, 구 diagnostic fallback 없음.

### 9.3 조건의 과도함과 달성 가능성

| 조건 | 판정 | 권고 |
| --- | --- | --- |
| 최근 3거래일 품질 + 최신일을 포함한 동일 scope 2일 이상 addressable critical; AI 분모 20/제출비율 <20% **또는** budget 분모 3/제출비율 ≤10% | 9/2~9/4 실제로 충족. 현재 activation을 막는 과도 허들은 아님 | 유지. AND로 바꾸거나 시장을 합쳐 채우지 않음 |
| canonical WAIT/EDGE/recovery intent·micro 확인·fresh quote·DANGER 차단·1주 probe-first·broker/account/order guard | 상승/반등 확인 및 안전에 필요한 조건. 현재 분모 0만으로 과도하다고 판정할 근거 없음 | 유지. 실제 eligible 입력 분모와 단독 blocker를 추가 대조 |
| score 69~74.999 | runtime은 hard gate가 아니라 prior. 75도 나머지 계약이 맞으면 허용하는 테스트 존재 | “이 범위만 매수”라는 해석 제거. diagnostic의 score band 표본과 runtime 모집단을 동일하다고 설명하지 않음 |
| 확대용 동일 scope exact paired ≥10 + 비용 차감 EV >0 + 순손익 >0 | 최소한의 양의 경제성 확인 자체는 과도하다고 단정 못함. 현재 집계/기회 배분 결함 때문에 달성 가능성을 왜곡 | 숫자를 먼저 낮추지 말고 R1~R4 선행. 유효 10건도 최적성/통계적 확실성의 증명은 아님 |
| 최근 20거래일 표본 창 + 일반 mode 전역 arm 3건/일 | 완전 가동해도 60 arm/20일. 한 scope 10 pair는 16.7%, 두 scope 합 20 pair는 33.3%의 arm→유효 청산 전환이 필요 | 이 값은 확률 추정이 아닌 용량 상한 계산. 전환율·정상 확장 포함 표본을 측정한 뒤 동일 version/episode 누적 창 보완을 검토; 낡은 손실을 시간으로 세탁하지 않음 |
| OFF 이후 복귀 | 3거래일 cooldown만으로 복귀하지 않고 시장 recovery 또는 causal scope/axis 변경을 요구 | 시간만으로 재가동하지 않는 guard는 유지. 동일 원인의 코드 수리가 검증돼도 자동 새 episode 근거가 되는 별도 경로는 없으므로, 수리 hash/인과 replay/기존 권한 범위의 재심 계약을 후속 검토 |

추가 설계 한계: 현재 controller에는 micro/recovery 파라미터의 후보 탐색·비교·채택 루프가 없다. [보고서 안내](../../src/engine/scalping/entry_recheck_drought_controller.py:225)도 blocker 완화를 유효 paired floor 이후의 후속 설계로 남긴다. 실주문이 구조적으로 0이면 코드/계측 수리까지 그 floor를 기다리게 해서는 안 된다. 코드·source 계약 수리는 별도로 먼저 검증하고, 실제 주문 권한/신호 완화는 인과·경제성·rollback 계약을 갖춘 기존 owner에서 별도 승인해야 한다. score-only 양의 EV를 이 승인 근거로 전환하지 않는다.

### 9.4 검증과 다음 소유자

- 이번 재실행: `test_entry_recheck_policy.py`, `test_entry_opportunity_recheck.py`, `test_entry_recheck_drought_controller.py`, `test_entry_ai_gate_backtest.py` **71 PASS / 1.06초**. 전체 저장소 테스트가 아니며 기존 §8의 2,143 PASS와 합산하지 않는다.
- 추가 메모리 반례: (1) 거절 평가 20건→collector→전환율 stop, (2) 정상 경제성의 수량 1/2/10 대조, (3) scope별 흑자/적자 양방향 stop 판정, (4) KRX 미제출 arm 3건 후 NXT 차단. 실제 함수를 호출했고 broker/API 요청·파일 report 생성·실거래는 하지 않았다. 기존 테스트 PASS가 이 교차 계약의 정합성을 보증하지 못함을 확인했다.
- 실행 코드 수리는 이번 재점검 범위 밖이며 미해결 finding R1~R5를 남긴다. 권장 구현 순서는 R1→R2→R3→R4→R5, 이후 위 수용시험과 producer/PREOPEN/runtime/receipt 통합 회귀·재리뷰를 거친다. 결함 종결 전에 review gate 통과나 재생성 권한이 있다고 해석하지 않는다.
- 현재 OPEN 수리 검토 owner는 checklist `EntryRecheckFeasibilityRepairReview0907`, 실제 PID/자연 성과 관측 owner는 `EntryRecheckNaturalAttribution0907`이다. 이전 완료 항목은 수정 당시의 증거로 보존한다. 이번에는 이 감사보고서·검토 목록·checklist만 갱신한다.
- 문서 재리뷰: 과거 완료 증거와 현재 OPEN 판정을 분리했고 checklist parser는 OPEN 37건과 신규 수리 검토 owner를 인식했다. `git diff --check` PASS. 이 문서 검증 PASS는 R1~R5의 코드 수리 완료나 runtime follow-up gate 통과를 뜻하지 않는다.

## 10. R1→R5 구현·수정·재리뷰

### 10.1 범위 및 구현 결과

후속 사용자 구현 지시에 따른 코드 보완이다. 기존 dirty worktree의 다른 작업을 보존했다. 새 구현은 `src/engine/scalping`의 receipt 경제성·제출 한도 소유 모듈이며 engine root에는 새 모듈을 만들지 않았다.

| 순서 | 보완 결과 | 수용 근거 |
|---|---|---|
| R1 | 새 평가에 이전 stock arm/submit/fill 귀속을 복사하지 않는다. collector는 정확한 `probe_armed` stage만 arm으로 계산한다. | 거절 평가 20건이 허위 arm이나 전환율 stop을 만들지 않는 실제 logger→collector 회귀 |
| R2 | 현재 attempt의 주문별 누적 BUY receipt와 전체 포지션 SELL receipt를 수량·금액·비용으로 대사한다. 1주/같은 probe bundle 잔량 full/partial 체결을 구분하고 scale-in 혼합은 진단 전용으로 남긴다. | 1/6/10주, 중복·불완전·충돌·혼합, terminal outbox custody 보존, 단위체결·수량 계약 누락 제외 회귀 |
| R3 | 경제성·전환율 stop, 중단 latch, 재심·근거 시작일을 시장/세션별로 분리한다. 다른 시장 손익으로 중단·확대를 승인하지 않는다. | KRX 흑자/NXT 적자 및 반대 사례, scope별 재개 창, producer→PREOPEN의 일부 scope ON/다른 scope OFF 및 변조 거절 |
| R4 | arm이 아니라 제출 직전 원자적 예약과 accepted submit이 기존 주문 한도를 점유한다. 명백한 무주문 거절만 반환하며 불명확·재기동 상태는 유지한다. | KRX 미제출 arm 3건 후 NXT 기회, 다중 프로세스 경합, 동일 attempt 재전송 차단, 손상 원장 fail-closed, 압축된 당일 기존 accepted 로그 복원 |
| R5 | 누적 `entry_ai_gate_backtest`를 정기 장후 wrapper에서 제거했다. 과거 daily/weekly override도 호출을 복구하지 못하며 별도 CLI 수동 진단만 남는다. 필수 일일 controller는 유지한다. | wrapper에 누적 진단 호출/대기 경로 없음, controller 필수·verifier·PREOPEN 회귀 |

추가 리뷰에서 체결이 REST 응답보다 먼저 도착하는 순서, 미전송이 확정된 local owner/시간 차단의 예약 누수, 최신 알 수 없는 checkpoint version의 과거 상태 fallback, 예약 원장 I/O 뒤 quote freshness 재검증 누락을 찾아 보완했다. I/O 이후 현재 raw quote로 기존 stale-submit guard를 다시 계산해 오래된 cached age가 fresh로 오인되지 않게 했으며 미전송 stale 차단은 예약을 반환한다. 체결 선도착은 검증된 BUY ledger와 정확한 accepted 주문번호로만 연결하며 응답 시간을 체결 시간으로 꾸미지 않는다. 새 평가/체결 계약은 `exact_attempt_v3`, scope별 controller는 v4다. 이전 stop checkpoint는 보수적으로 이관하며 구 schema의 왜곡 가능한 pair를 새 성과로 재사용하지 않는다.

제출 예약 원장은 `data/runtime/entry_recheck_submit_budget/YYYY-MM-DD.json`이다. 예약부터 broker I/O까지 순서를 보장하고 파일 잠금·atomic replace·fsync로 중복/재기동 한도 소실을 막는다. 브로커 전송 여부가 불명확한 예약은 시간 경과만으로 반환하지 않는다. 명확한 브로커/owner 대사가 필요한 운영 사건이지 매수 권한을 넓히는 근거가 아니다. 기본 총량 3, 기존 조건부 상향 cap, probe 1주, 수량 공식, freshness, DANGER, broker/account/order/cooldown/hard safety는 변경하지 않았다.

### 10.2 기대효과와 자동화 판단

- 구조적 개선: 허위 arm 중단과 정상 잔량 확장 승자의 경제성 제외를 제거하고, scope별 손익·중단을 분리해 EV 판단 왜곡을 줄였다. 미제출 arm의 예산 선점을 제거했지만 실제 accepted 주문이 기존 총량을 채우면 다른 시장의 추가 주문은 계속 제한한다. 시장별 할당 신설이나 cap 증액은 하지 않았다.
- 런타임 자동화: 새 장후 controller→다음 PREOPEN 계약 재검증→선택된 scope/profile→runtime→receipt 귀속 연결을 유지한다. JSON과 Markdown은 scope별 중단 사유·근거 창·fill-quality별 EV/net PnL을 별도로 표시한다. 이 controller는 고정 profile 운영 제어이며 최적 신호 파라미터 탐색 엔진이 아니다.
- 조건: 확대에는 동일 scope·fill-quality cohort의 유효 pair 10건과 양의 비용 차감 EV·순이익이 필요하다. full/partial 5건씩을 합쳐 10건으로 승인하지 않는다. 숫자 완화보다 모집단 복원과 귀속 수리를 우선했다. 현재 자연 exact pair가 없어 달성 확률이나 수익 개선을 입증하지 못한다. 무조건 매수 경로를 추가하지 않았으며 기존 canonical recovery/micro 확인과 안전 조건을 유지한다.
- 런타임 비용: 기존 9/4 누적 진단 892.44초는 정기 critical path에서 제외되는 작업량의 근거다. 일일 controller 0.84초는 이전 실행 기록이며, 이번 변경 후 총 장후 wall-clock 단축을 실측했다는 의미가 아니다.
- 전환 경계: 기존 9/4 산출물·9/7 PREOPEN env·실제 PID를 이번에 덮어쓰거나 재기동하지 않았다. 구 controller 계약은 새 PREOPEN 검증을 자동 통과한다고 가정할 수 없다. 새 schema의 일일 산출물 생성/선택/PID 소비와 자연 성과 확인은 `EntryRecheckNaturalAttribution0907`에 남긴다. 구 artifact/설정의 ON을 보완 코드 실적용으로 보고하지 않는다.

### 10.3 공식 계약·검증·최종 판정

- 주문 payload/FID/인증/parser는 변경하지 않았다. 로컬 receipt/주문 직전 경계 검토에 앞서 공식 [Kiwoom REST API 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa)를 확인했다. 조회 `2026-09-06T10:19:16.996650+09:00`, SHA `234560d213acd8871ae344b5481aecd2f30287fa`; 확인 경로 `kiwoom/specs.py`, `kiwoom/core/errors.py`, `kiwoom/realtime/__init__.py`, `kiwoom/_data/kiwoom_api_spec.json` (kt10000/00), `postman/kiwoom-openapi.postman_collection.json` (PROD/MOCK kt10000). 해당 revision에 `kiwoom_docs/`는 없으며 미정의 의미를 추정하지 않았다.
- 최종 통합 회귀 **2,088 PASS / 46.34초**: recheck policy/economics/submit-budget/controller, AI gate, runtime AI-score gate/entry-latency/scale-in/split-order, live profit/receipt, PREOPEN, wrapper, pipeline logger, postclose verifier, error-detector coverage, engine location gate. 검증 전후 이 범위 source/test 파일 SHA-256이 동일함을 확인했다. 앞선 PASS 수치와 합산하지 않는다. 저장소 전체 테스트나 실주문 검증은 아니며 기존 pandas-ta deprecation 경고 1건이 있다.
- 검증 중 공용 verifier가 변경된 실행에서 12개 초기화 오류가 발생했다. 현재 파일의 초기화 이후 handoff 위치를 확인했고, 다른 작업의 변경을 덮어쓰지 않았다. 해당 파일 단독 **189 PASS**와 위 최종 통합 재실행으로 해소를 확인했다. 실패 실행을 최종 PASS로 대체한 것으로 꾸미거나 테스트를 제외하지 않았다.
- 변경 Python Ruff/compile, 핵심 모듈·테스트 Black, 변경 handler 구간 formatting, Bash syntax, `git diff --check`, checklist parser를 확인했다. `korstockscan-review-gate`의 producer/consumer·권한 누출·source quality·동시 처리·재기동·실패 전파 재리뷰를 거쳐 이번 구현 범위 미해결 finding 0건으로 종결한다. 전체 시스템 무결함이나 미래 수익을 보증하지 않는다.
- 이번 변경은 봇 재기동, 실주문·취소, runtime env 수동 재적용, operator lock 변경, 무거운 누적 보고서 재생성, provider 변경, 커밋/푸시를 수행하지 않는다. 실제 수익 효과와 다음 자연 적용 확인은 코드 결함 종결과 구분한다.
