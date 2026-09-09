# 21:15 attribution ↔ runtime micro-confirmation / entry timing 개선작업 도출

관측 기준: `2026-09-09 14:04 KST`. 요청 범위는 점검·개선작업 도출이다. 코드, 운영 report, policy/env, PID, 주문을 변경하거나 장후 체인을 실행하지 않았다. 병행 적응형 청산 작업은 별도 범위다.

## 1. 결론

**새 튜닝축이나 threshold 완화보다 기존 entry timing의 계산·원천·평가 계약 보완이 우선이다.** 장후와 runtime이 같은 판정 함수를 호출하지만 feature 계산은 다르며, 동일 원천 반례에서 ENTER↔WAIT/REJECT가 달라졌다. 따라서 기존 회귀 PASS만으로 계산 정합성 완료를 유지할 수 없다.

목적은 원래 owner가 만든 유효 신호 중 실행 가능한 작은 비용 후 이익 기회를 지연 없이 소비하고, 취소성 잔량 감소·재보충·지지 붕괴로 인한 오진입을 구분하는 것이다. 진입 수를 줄이는 것 자체가 성공이 아니다. 유효 기회 참여, 미체결·오진입, 비용 후 EV/순익, tail과 자본점유를 함께 비교해야 한다. target·수량·exit를 바꾸는 적응형 청산과 섞지 않는다.

## 2. 실제 원천과 현재 자동화

| 완료 source date | 전체 anchor / matched | 실제 decision anchor | micro entry anchor / eligible | timing 결정 |
| --- | --- | --- | --- | --- |
| 9/4 | 65 / 0 | 6 | 28 / 0 | baseline immediate carry |
| 9/7 | 85 / 0 | 8 | 33 / 0 | baseline immediate carry |
| 9/8 | 108 / 0 | 15 | 45 / 0 | baseline immediate carry |

전체 anchor는 entry/submit/exit 등을 포함하며 micro entry anchor에는 diagnostic/prospective가 포함된다. 실제 decision anchor도 고유 체결 lifecycle 수와 같지 않다. 이 분모들을 합산해 유효 거래 표본으로 세지 않는다.

9/8 [attribution](../../data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json)의 byte SHA256은 `0b15809fc5665c2bcbd22f6eefa74a90041fc8915d0b6d90b8e71c46ef5a2012`다. `source_contract_ready=false`, canary source=`missing_or_invalid`, `immutable_ingress_receipt_loss=true`이고 `depth_source_incomplete`, exact 0B anchor/BBO/checkpoint 결손이 분리돼 있다. [timing](../../data/report/machine_entry_timing_tuning/machine_entry_timing_tuning_2026-09-08.json)은 source artifact17개를 읽었으나 실제 당일 decision15개 모두 blocked/eligible0이다. 단순히 표본이 조금 부족하거나 전략의 EV가 나쁘다는 뜻이 아니다. 이미 분류된 과거 ingress loss는 같은 날 재실행으로 복원하지 않는다.

설치된 `korstockscan-machine-microstructure-final-refresh.timer`는 active/enabled, 다음 실행9/9 21:15다. [wrapper](../../deploy/run_machine_microstructure_final_refresh.sh)는 expansion→attribution→weakness hysteresis→entry timing→approval→checklist 순서다. 오늘 예정 전 artifact 부재는 장애가 아니다.

정확한 timing 경로는 **21:15 postclose producer의 다음 effective-date 정책 staging/publish→owner의 exact-date policy loader→원래 signal의 0/1/3/5초 확인→기존 주문 guard**다. [producer](../../src/engine/automation/machine_entry_timing_tuning.py)의 postclose `write_outputs`가 다음 날짜 policy를 발행하며 08:00 이후 덮어쓰기를 막는다. `--phase preopen`은 별도 rebound/reentry owner의 재검증 함수이므로 이를 timing 전체의 두 번째 PREOPEN 승인으로 설명하면 안 된다.

[현재 policy](../../data/runtime/machine_entry_timing_policy/machine_entry_timing_policy_2026-09-09.json)는 schema v3, source9/8, target9/9, `selection_status=baseline_immediate_entry_carry_forward`, `scopes={}`다. 실제 `load_applied_policy`는 `ready`/scope0을 반환했다. 새 동적 확인은 선택되지 않았으며 이 gate가 현재 원래 진입을 막는다는 증거는 없다. 9/8 평가에는 별도로 다음 widget 005930/KRX entry 변경의 same-stage conflict도 기록돼 있다. 원천 결손과 owner 충돌을 서로 대체 원인으로 쓰지 않는다.

## 3. 확인된 결함과 설계 결손

### P1 — 동일 정책에 서로 다른 잔량 계산을 공급

[장후 `_best_ask_metrics`](../../src/engine/scalping/micro_reversion/ask_depletion.py:605)는 고정 ask 가격의 초기→최소 잔량 감소, 그 최소 시점 이전 해당 가격의 공격적 매수체결, 감소 후 최대 재보충/감소량을 계산한다. [runtime builder](../../src/trading/market/micro_confirmation.py:939)는 시작→끝 잔량 차이, 창 전체 매수체결, `(끝 잔량+매수체결-시작 잔량)/시작 잔량`을 쓴다. 중간 최소·고정 가격 체결 귀속·refill 분모가 다르다.

기존 test fixture의 같은 NXT item/epoch·가격·시간·수량 원천을 각 실제 adapter에 넣고 공통 state evaluator로 비교했다. 정책값·비용·owner limit은 고정했다. 장후 horizon은 두 경우 모두 feature eligible였다.

| ask 잔량 경로 / 창 전체 BUY | runtime backing / refill / action | 장후 backing / refill을 같은 정책에 넣은 action |
| --- | --- | --- |
| 100→20→80 / 50주 | 1.0 / 0.30 / ENTER | 0.50 / 0.75 / WAIT |
| 100→20→100 / 40주 | 1.0 / 0.40 / ENTER | 0.375 / 1.00 / REJECT |

이것은 실제 거래 성과가 아닌 재현 가능한 코드 반례다. 장후는 첫 0B를 event anchor로 삼아 그 이후 trade 설명을 사용하므로 첫 trade 포함 여부도 통일해야 한다. 어느 계산을 무조건 정답으로 채택하기보다 fixed-price causal 계산 계약을 먼저 고정하고 양쪽을 같은 함수로 연결해야 한다.

### P1 — 관찰창·원천 완전성 계약도 다름

- [장후 checkpoint adapter](../../src/engine/monitoring/machine_microstructure_attribution.py:5394)는 직전1초의 첫 0B부터 명목 checkpoint 직전까지 읽는다. runtime은 명목 checkpoint−1초의 depth를 시작으로 실제 호출 `now`까지 사용한다. 최대1.5초 늦은 호출에서는 평가 범위가 더 길어진다. wall-clock 미래 입력이라는 뜻은 아니지만 장후의 명목 checkpoint와 같은 실험이 아니다.
- runtime은 시작 depth의 age를 검사하지 않는다. 정상 fixture에서 시작 depth만60초 전으로 바꿔도 `source_quality_status=eligible`, `quote_age_ms=0`, `ENTER`가 재현됐다. 이는 끝 quote가 fresh인 것과 전체1초 창이 유효한 것을 혼동한다.
- [snapshot 투영](../../src/engine/bd_fbuy_accum_pre_scanner.py:848)은 recent trade/depth 각각16개와 top1만 전달한다. per-row sequence·window completeness·truncation receipt가 없어 거래가 몰릴 때 누락 여부와 고정 ask level 이동을 완전히 대사할 수 없다. [WS depth buffer](../../src/engine/kiwoom_websocket.py:3959) 자체도 maxlen16이다. **14:00:43 실제 snapshot46개 route에서는 depth16개가1초 미만으로 잘린 경우0**이므로 현재 고빈도 truncation을 실관측 결함이라고 주장하지 않는다. 미검증 경계·잠재 실패를 회귀에 포함한다.
- 6초 기본 machine poll 자체를 결함으로 재분류하지 않는다. `RegularTwoLegMachine._next_loop_delay_sec`가 pending checkpoint deadline에 맞춰 깨우는 코드가 이미 있다.

### P2 — 결합 가설의 증분효과를 분리하지 못함

현재 [공통 판정](../../src/trading/market/micro_confirmation.py:571)은 bid 상승/저점 반등 + trade backing + refill + 양수 modeled net edge를 결합한다. 하지만 checkpoint 입력에는 감소속도(qty/sec), 설명되지 않은 감소량, refill half-life/top3·5가 전달되지 않는다. 계산된 ask-depletion report가 존재하는 것과 속도 효과를 판단에 소비하는 것은 다르다.

현재 비교는 immediate baseline 대 fixed1/3/5초·고정 dynamic recipe다. **baseline / 반등·bid 지지만 / 속도·체결 설명·refill만 / 결합**의 같은 표본 비교와 독립 chronological holdout은 없다. 현재 tuning 분모는 `actual_order_submitted=true`와 realized outcome으로 제한되므로 미제출·미체결·열린 보유의 기회 손실을 완전히 설명하지 못한다. 이 제한을 제거해 미체결을 실체결로 바꾸는 대신 전체 signal census와 증거 유형을 별도 연결해야 한다.

### P2 — 평가 라벨 의존성과 floor 설명 보완

[`_dynamic_baseline_observation`](../../src/engine/automation/machine_entry_timing_tuning.py:606)은 실제 완료 손익·비용이 유효한 즉시 ENTER(0초)에도 별도 first-hit/5분 label을 필수로 요구한다. 기존 fixture를0초 supportive로 재결속한 뒤 실제 outcome은 그대로 두고 first-hit section만 제거하면 observation이 유효→None으로 바뀌었다. 즉시실행 control 손익 산출에 불필요한 진단 라벨 결손까지 결합돼 있다. label 무결성 검증을 끄는 대신 **실제 paired economics와 first-hit 진단 eligibility를 분리**하는 것이 권고다. 지연·미실행 반사실의 체결/청산 증거가 필요한 경우는 별도 계약을 유지한다.

[표본 상태 작성](../../src/engine/automation/machine_entry_timing_tuning.py:2269)은 Samsung rise/rebound에만 dynamic evaluation을 넣어, 다른 dynamic 지원 scope의 요약에 fixed floor20이 표시된다. 실제 dynamic 승인 floor8과 달라 조건 달성성 설명이 부정확하다. 모드별 floor·source/terminal/경제성/owner blocker·유입률을 별도 노출해야 한다.

## 4. 지금 수행할 구현 순서와 완료 판정

| 순서 | 개선작업 | 완료 판정 |
| --- | --- | --- |
| 1 / 최우선 | 기존 `trading/market`에 순수 공통 feature kernel을 두고 장후/runtime adapter를 연결. fixed-price, 첫 trade, 창 시작·끝, nominal/actual cutoff, 초기 depth age, 중간 최소·refill·sequence/epoch를 명시 | 위2개 행동 반례·60초 stale 시작·가격 level 이동·late/순서/중복/UNKNOWN·epoch 변경에서 동일 입력/시점/정책의 metric와 action 일치. 결손은 별도 이유이며 0/중립으로 대체하지 않음 |
| 2 / 원천 | 기존 bounded WS buffer·snapshot/저장 원천을 재사용해 signal ID→route/epoch→window completeness→checkpoint→submit/fill/terminal 결속. 필요 시 기존 budget 안에서 시간창 보존과 truncation receipt 보완 | 새 정확한 원천에서 최초 결손이 수집·등록·수신·투영·timestamp·join·terminal별로 설명됨. 과거 ingress loss 격리 유지; 없는 과거 자료를 반복 재생성하지 않음 |
| 3 / 평가 | 실제 economics와 선택적 first-hit 진단 분리; 전체 실제 signal census와 위4개 고정 연구 비교를 동일 cohort/비용/exit 계약으로 평가 | 미제출·미체결·partial/full·HELD·terminal·CF/실체결을 구분. 비용 후 EV·순익·유효 기회 참여·tail·자본점유의 증분 및 holdout 결과가 함께 나옴. 새 live 튜닝축4개가 아니라 기존 entry timing의 연구 비교 |
| 4 / 조건 | fixed/dynamic 모드별 floor와 달성성 요약 수정. fixed5/10/20 동시 성과 조건의 추가 효용은 별도 비교하고 dynamic에 복사하지 않음 | 실제 적용 validator와 보고서의 floor/이유 일치. 유입0이면 ETA null/source repair; 가짜 도달 날짜·자동 floor 하향 없음 |
| 5 / handoff | 공통 계산 버전·exact source hash·policy scope·actual checkpoint receipt를 기존 timing producer/loader 및 요약/checklist에 결속. mutable source 재생성과 적용 receipt의 경계도 시험 | 같은 generation의 source→timing→exact-date policy→각 owner consumer 대사. 재생성만으로 적용정책이 조용히 탈락/교체되지 않도록 immutable receipt 또는 명시적 invalidation 경계. same-stage·기존 수량/target/주문 guard 유지 |

수리와 테스트는 지금 착수할 수 있다. 자연 장후 검증은 오늘21:15 owner 이후 해당 산출물로 진행하며, 전체 postclose 재실행이나 현재 PID/threshold 변경은 이번 권고의 선행조건이 아니다. WS request/parser/FID/등록/복구를 실제 수정해야 한다면 별도 공식 Kiwoom reference gate를 먼저 수행한다. 단순 buffer/내부 투영 보완도 API 호출량·retry·동시성 우회로 해결하지 않는다.

## 5. 조건의 과도성 판단

- dynamic의 절대 EV 개선 floor `0.005 percentage point = 0.5bp`는 거래당1.1% 수익을 요구하는 조건이 아니다. 현재 목적만으로 과도하다고 판정할 근거는 없다. 후보의 비용 후 EV 양수·원가/정확한 체결 구분·tail·same-stage 보호는 유지한다.
- dynamic은5개 관측일·8개 고유 lifecycle/완료 outcome·replay/paired85%·right-censored≤35%·완전한5-source-day window 및 관측 freshness를 요구한다. 10/20일은 dynamic의 필수 동시 승격 gate가 아니다. fixed에는20개 표본·5/10/20일 조건이 남아 있어 독립 증분효과 확인 뒤 단순화 후보로 검토한다.
- 지금 가장 큰 막힘은 **계산 불일치와 유효 source0**, 그 다음 미완성 결합 평가다. 새 표본이 늘면 모든 조건이 자연 해소된다고 설명하지 않는다. 선택적인 진단 라벨의 불필요한 결합과 잘못된 floor 표시는 지금 보완 대상이다.

## 6. 검증·추적

기존 `test_dynamic_micro_confirmation`, `test_micro_reversion_ask_depletion`, `test_machine_entry_timing_tuning`, `test_machine_microstructure_attribution` **192 PASS**. 별도 read-only 메모리 반례로 위 계산/age/label 결손을 재현했다. 테스트 PASS는 새 finding 해소를 뜻하지 않는다. 코드 수정·신규 회귀 반영은 아직 미실행이다.

관찰한 주요 파일 byte hash: `micro_confirmation.py=f700c4459f45a81c00e94c9a9a7cee05115a564c7e24908f9a7ab54a929f512c`, `machine_entry_timing_tuning.py=70e14e6c6e3339aa84f21ffe7fc12d40e8b861ffc0b8bdaae1bd87f70cf19f58`, `ask_depletion.py=51cf8c2d934b27ef0f7675733c70863ece8c44155e1f2b4ca0f84d8193b38f00`. 병행 세션의 attribution adaptive-exit child 추가와 신규 adaptive-exit 모듈은 이 검토의 수정·검증 완료 범위가 아니다.

실행/자연 acceptance는 [당일 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`를 재사용한다. 이 문서의 검토 항목은 producer가 발행한 native workorder ID가 아니며 자동 구현·live 승격 권한으로 쓰지 않는다. `korstockscan-review-gate`에 따라 문서 근거·권한·링크·diff 검증과 print-only parser를 통과했다(36 tasks, 기존 machine owner1개). 이는 위 코드 finding의 수정 완료가 아니다. Project/Calendar sync는 실행하지 않았다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 7. 후속 사용자 구현 지시에 따른 보완

9/9 14:31 이후 별도 구현 요청으로 아래 수리와 재리뷰를 수행했다. §1~§6의 도출-only/미실행 문장과 byte hash는 14:04 이력이다. 현재 작업은 entry confirmation/timing 범위이며 병행 적응형 청산의 SELL adapter·승인 family 미완료를 대신 닫지 않는다.

### 7.1 구현 및 리뷰 결과

| 보완 | 최종 계약 |
| --- | --- |
| 계산 통일 | [공통 kernel](../../src/trading/market/confirmation_window.py)의 `machine_confirmation_fixed_price_window_v1`을 [장후 adapter](../../src/engine/monitoring/machine_microstructure_attribution.py)와 [runtime adapter](../../src/trading/market/micro_confirmation.py)가 함께 사용한다. 고정 1초의 시작 경계 호가, 중간 최소 잔량, 같은 초기 ask 가격에서 최소점 이전 BUY, 최소점 이후 실제 refill을 계산한다. 첫 체결 누락·전 가격 체결 합산·종점 잔량만 비교하던 차이를 제거했다. |
| 시점·source | nominal checkpoint 뒤 row는 late 평가에서도 사용하지 않는다. 시작 호가·종점 freshness, epoch/sequence/중복 충돌·고정 가격 level 결손·UNKNOWN aggressor를 분리하고 source gap은 성공으로 보간하지 않는다. checkpoint 사이 reconnect도 최초 signal epoch와 재검증한다. 최신 causal 0D BBO와 reference bid를 공통 사용하고 first-hit entry label도 같은 quote에 결속한다. |
| 기존 원천 투영 | WS의 기존 per-route sequence를 각 0B/0D row에 보존한다. trade120행의 snapshot 16행 절단을 제거하고 depth도 bounded120행과 관측5호가를 보존한다. 왼쪽 경계·중간 sequence·snapshot endpoint 결손은 source gap이며 120행이 언제나 1초를 보장한다고 주장하지 않는다. API 요청·구독·retry·동시성은 늘리지 않았다. |
| 경제성·4군 연구 | [기존 timing producer](../../src/engine/automation/machine_entry_timing_tuning.py)의 `cohorts[].feature_ablation_study`에 baseline / bid·rebound / depletion·trade backing·refill / combined를 연결했다. [연구 모듈](../../src/engine/monitoring/machine_entry_confirmation_study.py)은 같은 lifecycle의 4군 모두 경제성 재현이 유효한 교집합만 비교하며, 최신 source일을 chronological holdout으로 분리한다. 비용 후 EV·순익·p10·자본시간·참여·수익 기회 거절·음수 진입을 표시한다. 연구 arm은 live 후보/새 튜닝축이 아니다. 속도는 측정값과 양의 depletion 유무로만 사용하며 새 최적 속도 임계값을 발명하지 않는다. |
| 전체 분모 보존 | 미제출, 확인된 미체결, full/partial 보유, 체결 후 terminal 미상, full/partial realized를 source에 있는 범위만 census로 분리한다. 경제성 결손/미체결/partial/열린 보유는 0원으로 넣지 않는다. 실제 fill baseline과 다른 진입/청산의 modeled CF는 별도이며 실체결 품질로 승격하지 않는다. |
| 불필요한 조건 분리 | 실제 full-size 즉시 ENTER control과 결정론적 REJECT 무노출 비교에는 선택적 300초 first-hit 라벨을 요구하지 않는다. 해당 라벨이 유효하지 않으면 진단값은 null이다. 지연 ENTER에는 기존 정확한 executable first-hit·원가·청산 증거를 계속 요구한다. |
| 조건 달성성 | 모든 dynamic scope에 실제8건 기준을 표시하고 fixed20건 진단을 별도 보존한다. 완료수만 충족해도 관측일·고유 lifecycle이 부족하면 floor 완료로 표시하지 않으며 ETA에 남은 날짜·lifecycle을 포함한다. 유입률 증거가 없으면 ETA는 null이다. 실제 승인 수치·one-scope·same-stage·price/quantity/target/hard safety는 변경하지 않았다. |
| 정책 전달 | 발행 전에 report hash를 확인하고 `policy_dir/evidence/HASH.json`을 먼저 저장한 뒤 exact-date policy가 이를 참조한다. 진단 report 재생성은 기존 발행 세대를 바꾸지 않는다. frozen evidence 자체의 위변조·날짜/hash/경로 불일치는 차단하며 최신 canonical report의 same-stage owner veto도 명시적으로 반영한다. 적용 provenance에는 source hash와 frozen 경로가 남는다. |

리뷰 중 추가로 발견한 stale reference bid, checkpoint 간 epoch 변경, 잘못된 side/epoch 입력의 예외, 완료건수만으로 floor 완료를 선언하는 문제, 새 owner veto를 무시할 수 있는 frozen consumer 경계를 보완했다. 기존 shock-event 전용 ask-depletion producer는 다른 연구 consumer를 위해 유지하며 checkpoint 계산만 새 kernel로 통합했다.

### 7.2 검증 및 공식 참조

- 최종 receipt: **9/9 15:13 KST, 23개 관련 test module 1,101 PASS / 35.00초**, Ruff13개 파일·compile8개 production module·기존21:15 wrapper `bash -n`·`git diff --check` 통과. 문서 parser는36개 task, 기존 machine owner1개다. 이번 entry confirmation/timing 구현 범위의 미해결 review finding0이며 전 저장소 무결함이나 병행 적응형 청산 기능 완료를 뜻하지 않는다. 중간338/603/1055/1100 및 마지막 부분189 PASS는 서로 겹치므로 합산하지 않는다.
- 최종 통합 실행 전후 주요6개 파일 byte hash가 동일함을 확인했다. kernel=`58eda87aa02e283e378ea3bcdbda3bbc1543726252092ca744f1d0f31d2f29d3`, runtime adapter=`8b9b1cbf3ed256cadd5c44249e870efd0e1d5b467b5c1eea7da3f80610bd5f5f`, attribution=`8455dedc068b90e4f067b99fb25f91d55bcdaeb733f60a40bc02b599507505a4`, study=`f8c161f696e6ce5a377efb30fd3457b9ae8f0a680fb455d63f2e7cfb86935058`, timing=`51f5f24af06ad5acb422e0225015062a435dc083b77d5d789d369ddf4286b2ab`, policy loader=`1bc9f681327af02e477ddc61e54850686c79bdc2c654219925661a63482ef5ba`. 이는 worktree 검증 receipt이며 commit/PID receipt가 아니다.
- 회귀는 두 잔량 반례의 metric/action parity, 첫/다른 가격 체결, downward reprice, stale 시작 호가, future/late cutoff, sequence/epoch/UNKNOWN/NaN, dense snapshot 경계, 실제 control의 선택 라벨 분리, 비용 결손·partial 배제, 4군 교집합/holdout, frozen source/신규 veto를 포함한다.
- 14:42 병행 리뷰가 기록한 attribution fixture 2 FAIL은 이 변경의 새 checkpoint 계약으로 fixture를 보완하고 다시 검증했다. 병행 적응형 청산의 기능 미완료는 별도 OPEN이다.
- Kiwoom 공식 upstream은 9/9 14:33 KST `git ls-remote`로 `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. 같은 SHA checkout의 `kiwoom/_data/kiwoom_api_spec.json` 0B/0D, `kiwoom/specs.py`, `kiwoom/realtime/{packets,decoders}.py`, `kiwoom/core/ws_client.py`, Postman collection을 대조했다. 이 revision에는 `kiwoom_docs`가 없고 Postman에서 WS 항목을 찾지 못했으므로 미정 의미를 추정하지 않았다. 기존 41/61·51/71 가격/수량·item route 및 로그인/REG/REMOVE 프로토콜을 변경하지 않았다. 실제 broker/provider 호출은 하지 않았다.

### 7.3 자동화·목적 부합성과 잔여 경계

9/9 15:00대 읽기 전용 확인에서 설치 timer는 active, 다음 실행은 **9/9 21:15**, service의 기존 Result는 success다. `expansion → attribution → weakness → timing → approval → checklist` 순서는 유지하며 새 연구는 기존 timing 실행 안에서 자동 산출된다. 기존 승인된 dynamic/fixed 후보가 source·경제성·owner 조건을 통과하면 다음 exact-date 정책 발행과 기존 widget/episode consumer 로딩은 추가 개별 승인 없이 진행된다. `--phase preopen`의 별도 rebound family와 이 timing 발행 경로를 혼동하지 않는다.

현재 9/9 policy loader는 `ready`, `scopes={}`, `baseline_immediate_entry_carry_forward`다. 후보0을 강제 승격하지 않았고 현재 PID·env·lock·주문·수량·target을 변경하지 않았다. 코드가 공유 worktree에 있다는 것과 실행 중인 collector/owner가 새 import를 소비했다는 것은 다르다. 새 per-row sequence/snapshot은 해당 프로세스의 승인된 배포·정상 기동 이후 확인해야 한다. 이번에는 commit/push/restart/장후 전체 또는 운영 report 재생성을 실행하지 않았다.

기대효과는 잘못된 ENTER/WAIT를 줄이고 비용 후 작은 기회의 진입 시점·회전·tail을 같은 원천으로 평가할 수 있게 하는 것이다. `0.005%p = 0.5bp`는 EV 개선 폭이지 거래당1.1% 이익 조건이 아니다. 불필요한 control 라벨 의존·잘못된 floor/ETA는 제거했으나, source0·실체결/EV 미관측을 이유로 안전 또는 경제성 조건을 임의 하향하지 않았다. fixed5/10/20의 추가 효용은 자연 데이터에서 확인할 대상으로 유지하며 dynamic에 추가하지 않는다.

자연 source→21:15 report/study→같은 generation policy→새 PID checkpoint→실제 fill/terminal·비용 후 EV/빈도/순익의 acceptance는 기존 `MachineLifecycleTurnoverObjectiveFollowup0909` 하나에 남는다. 과거 ingress loss는 복원하지 않으며 실수익 개선은 아직 입증하지 않았다.
