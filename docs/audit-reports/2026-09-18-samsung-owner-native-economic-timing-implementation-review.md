# 삼성 owner 승인 수량 기준 native 경제성 timing 구현 리뷰

Source target: 2026-09-18. As-of: 2026-09-19 KST. [owning plan](../proposals/samsung-owner-quantity-native-economic-timing-plan-2026-09-18.md). 사용자가 승인한 비교는 owner별 native 승인 수량 독립 비교이며 shared Samsung cash allocation은 없다.

## 원천 결손과 수리

| 경계 | 수리 | 회귀 증거 |
|---|---|---|
| 실제 체결 leg만 anchor | confirmation 전 parent opportunity 및 차단/거절/미체결 분모 | native runtime 기존 fixture의 frozen root/quantity source assertions |
| arbitrary first-hit/horizon 청산 | native limit/market BUY·weighted tick/pooled target·reserve/보유 노출 | native source→canonical projection→replay tests |
| 활성 exit pin이면 일괄 unsupported | 선택 pin 인계 + 기존 quote/pressure/stagnation arithmetic + 측정 action clocks | active pin target-path 및 programme action tests |
| 공통 guard 통과 전 CF 제출 | 원 native guard admission barrier·후속 veto 분리 | early CF BUY 금지/공통 block 회귀 |
| ADD guard의 다른 leg 재사용 | stage별 receipt 및 마지막 weakness check 뒤 허용 | original widget 3-leg 및 cross-stage 차단 회귀 |
| SOR prearm plan/source 누락 | deferred opening-price resolver의 최초 실행 시점 CAP·raw bar identity 보존 | 원 morning producer/reload 회귀 |
| 날짜별 native policy SHA로 모델 분열 | semantic native rule + quantity/cost/route/code/programme scope | dated receipt 동일 scope/target 변화 다른 scope 회귀 |
| target-only 최초 모델에 영구 고정 | 새 action의 chronological calibration/holdout에 model prefix 갱신 | 실행 가능한 fit/clock source 계약 |
| 늦게 완료한 carry의 actual 연결 | 원 checkpoint exact root/as-of actual refresh, date-reset terminal 보존 및 기존 보고서 sealed completion history | before/after as-of·중복·다른 계약 차단 회귀 |
| 과도한 observability 누적 | programme unchanged interval 압축·bounded path·terminal lookup reuse | 100 owner ticks→1 interval·cadence 보존 회귀 |

원 Kiwoom request/response parser/API/WS registration은 수정하지 않았다. native guard·수량·quantity authority·budget/custody·operator veto·기존 stop/target/override·holdout은 유지한다. src/engine root Python module/새 producer/서비스/DB/collector를 추가하지 않았다.

## 계산과 선정의 증거 구분

S0–S6의 지원 full-fill 입력 계산·model/candidate holdout·native policy 소비 및 fallback은 통제 source writer/canonical projection과 기존 runtime fixture로 검증한다. active programme pin을 유지한 동일 native scope에서도 계산→모델 holdout→별도 후보 holdout→dated reader/loader가 동작한다. 이러한 fixture는 자연 표본·실제 이익·인과적 EV 개선 증거가 아니다.

지원 범위 밖 partial BUY/취소 race/remainder/overnight CF replay는 구체 blocker/null이다. 측정한 action clock이 없으면 그 action을 실제 요청하는 경로만 차단된다. 구현된 action source writer와 양쪽 chronological 검증 계약의 표본 부족은 자연 검증 OPEN이다. 구현되지 않은 generic 청산/새 queue 모델을 이미 지원한다고 보고하지 않는다.

## 검증 및 배포

최종 영향 범위 회귀 **872 PASS**, 마지막 admission 재확인 및 own-registry identity 보완 회귀 **231 PASS**. carry/date-reset 누적 연결 보완 회귀 **258 PASS**가 추가로 통과했다. 이 suite들은 중복이 있으므로 합산 표본 수가 아니다. owned 16 Python compile, Ruff F821/F823/F811, diff whitespace, local links 및 print-only parser(기존 stable ID의 current OPEN owner 1개)가 통과했다. 통제 source writer→canonical→모델 검증→별도 후보 검증→dated loader의 활성/거절/fallback 상태를 포함한다. 자연 경제적 성과를 주장하지 않는다.

정규장 원 leg에 없는 route는 실제 native owner policy로 **사본에만** 결속한다. 위젯 KRX 판단 호가와 SOR execution depth를 분리하고, SOR 경로 부재를 KRX 호가로 대체하지 않는 회귀를 추가했다. 차단 후 real BUY가 허용된 recheck는 최초 허용 시각부터 admission을 갱신한다. 원 checkpoint identity 충돌은 실제 손익 평가에서 제외한다.

Commit/push/immutable deployment와 제한 재생성의 기계 검증 receipt는 아래 evidence directory에 기록한다. 최종 receipt 전에는 selected release·PID 소비·새 정책 후보가 생성됐다고 주장하지 않는다.

Evidence owner: `tmp/samsung-owner-economic-timing-20260918/`. 실행 중 배포본 수정·수동 bot restart·주문·조기 PREOPEN 확정·Project/Calendar sync는 수행하지 않는다. 현재 9/19 checklist 부재를 보고하며 다음 자연 acceptance는 기존 stable ID를 [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)에 인계한다.

## 자연 OPEN 및 closure test

1. 다음 영업일 최초 eligible 신호와 차단/recheck마다 frozen root·quantity receipt·cost/code/exit pin·admission·stage guard가 실제 checkpoint에 존재하는지 확인.
2. 자연 full-fill native terminal의 own registry/clock/price/provenance가 projection에 연결되는지 확인. selected pin 자체의 unsupported 전수 제외가 재발하면 implementation defect로 재개.
3. 독립 model/calibration/candidate holdout의 chronological coverage/floors를 충족한 뒤에만 신규 후보를 평가. valid no-edge와 source gap/unsupported/pending/insufficient sample을 구분.
4. 실제 다음 적용일 policy hash와 native scope/code/quantity/cost/programme pin을 PID/cwd/source provenance 및 실제 행동에 대사. selector·unit 설정 변경만으로 PID 소비를 주장하지 않음.
5. 실제 완료 root를 버전별로 중복 제거하고 rolling/cumulative 비용 모델 순익·노출·tail·모델 오차를 확인. broker settlement 비용을 별도로 확보하기 전 frozen fee 순익을 settled cash net이라고 부르지 않음. 인과적 개선은 적합한 비교가 확보될 때까지 null.

배포 후 추가 재리뷰 finding: date reset으로 늦게 완료한 원 root가 유실되는 경로를 발견하여 보완했다. original `_roll_date`의 native state는 그대로 초기화하되 research terminal history만 128개로 보존한다. 기존 timing 보고서의 sealed actual completion history를 한 번 bounded 읽어 checkpoint 교체 뒤에도 누적 평가에 연결한다. 새 ledger/DB/producer·raw rescan은 없다. exact cSHA/as-of/own terminal economic identity를 대사하고 충돌 tombstone은 이후에도 제외된다.

추가 clock review: measured submit latency에서 confirmation·원 공통 guard 대기 시간을 이중 차감/추가하지 않도록, 원 admission/confirmation barrier 이후의 관측 지연만 모델에 사용한다. recheck guard 3초 + 관측지연 200ms 및 confirmation 5초 사례를 분리 검증했다. exchange/wire latency 0이라는 주장은 하지 않는다.

## 최종 배포·재생성 증거

- 코드 commit/push: `c66d13421` → 완료 root 보존 `e2e4b8991` → 최종 clock 수리 `03810263ad9d70727266738670e6c391eb0254c9`. origin/main push 성공. immutable source release: `/home/ubuntu/KORStockScan-runtime-releases/samsung-owner-economic-timing-reviewed-20260919-03810263a`.
- Selector와 Samsung morning/midday/afternoon·widget 4개 unit의 미래 WorkingDirectory/PYTHONPATH/ExecStart를 최종 successor로 연결했다. 원 argv·PYTHONPATH 외 environment SHA가 동일하다. 원 policy pin/수량/guard·enabled 상태를 변경하지 않았다. manual restart/order/early PREOPEN은 수행하지 않았다. widget PID27445는 관측 시 이전 release에 있으며 새 code 실제 소비를 주장하지 않는다.
- 제한 regeneration: `monitoring.samsung_machine_entry_tuning --target-date 2026-09-18` 및 `automation.machine_entry_timing_tuning --target-date 2026-09-18 --effective-date 2026-09-21 --write` 모두 exit0. 기존 normalized canonical MicroAttr만 읽었으며 raw rescan/new provider call 없음.
- 준비 정책: `data/runtime/machine_entry_timing_policy/machine_entry_timing_policy_2026-09-21.json`, `baseline_immediate_entry_carry_forward`, scopes `{}`, file SHA `9235965c3d14f208dcc70726a9246690dbcec7a8475516a21bb65b915eee2c9f`. successor dated reader `ready`; immutable source evidence SHA `021b4b518127dc7a3a6656c12d30d205dc86bc4730782a2b56a1d818ca75e1b6`. 신규 양수 정책이 아니다.
- 기존 삼성 자연 입력 26개는 모두 당시 frozen operating projection이 없는 source gap. episode morning8/afternoon4, widget KRX_REGULAR10/NXT_AFTERMARKET1/NXT_PREMARKET3. valid no-edge로 바꾸지 않는다. model paired ΔEV·settled 실제 순익·인과적 개선은 null이며 자연 completed version0이다.
- 최신 전체 native 후행 상태는 **FAIL**이다. Tower exit0이나 source-gap 판정이다. 9/18 threshold_cycle_ev 등이 없어 checklist builder exit1, strict `--require-summary-handoff` exit1/60 issues, controller `--summary-handoff-only --dry-run`은 dry_run_planned이며 DONE이 아니다. 진행 중 predecessor를 종료하거나 없는 9/18 상위 generation을 대체·전수 재생성하지 않았다. 해당 global owner가 상위 source/EV/Daily/approval/closed-loop를 생성한 뒤 summary→tower→checklist→strict→controller를 재검증해야 한다. 이번 삼성 code closure 및 dated incumbent 준비와 전체 chain closure를 분리한다.
- Canonical integration은 다른 세션의 source/doc 변경을 보존했다. print-only parser는 `[CodeImprovementWorkorderReview0918]`의 current OPEN owner가 9/21에 1개임을 확인했다. 9/19 checklist는 없다.

기계 증거: [validation](/home/ubuntu/KORStockScan/tmp/samsung-owner-economic-timing-20260918/validation.json), [deployment](/home/ubuntu/KORStockScan/tmp/samsung-owner-economic-timing-20260918/deployment.json), [regeneration](/home/ubuntu/KORStockScan/tmp/samsung-owner-economic-timing-20260918/regeneration.json), [dated consumer](/home/ubuntu/KORStockScan/tmp/samsung-owner-economic-timing-20260918/final-consumer-evidence.json), [native handoff](/home/ubuntu/KORStockScan/tmp/samsung-owner-economic-timing-20260918/handoff-execution.json).

S0–S6의 지원 full-fill 미래 생성·저장·계산·chronological 독립 검증·선정·dated loader/fallback·actual version 경로는 구현 및 통제 회귀 PASS다. 자연 root·independent model20 witness(2일 이상)/candidate5일·8pair·85% coverage·실제 PID 적용 및 실제 완료 손익은 OPEN이다. partial/remainder/carry CF 등 adapter의 선언된 unsupported 범위는 자연 표본 대기로 숨기지 않는다. 전체 9/18 native handoff의 상위 산출물 결손/active predecessor는 별도 운영 OPEN이다.

동시 세션 최종 대사: 공통 selector는 2026-09-19 01:04 KST 다른 승인 세션의 successor `988baa142` / `low-price-exploration-manual-close-reviewed-20260919`로 전환됐다. 이 successor는 삼성 source038을 포함한다. owned Python SHA를 비교한 차이는 MicroAttr의 저가주 v10 schema 허용 1줄뿐이며 삼성 kernel·계산·dated loader는 동일하다. 이 선택을 덮어쓰지 않았으며 독립 Samsung/widget 4개 unit은 검증된 삼성 release038을 유지한다. 준비 정책 file SHA와 current OPEN owner1은 재확인했다. 자세한 대사는 `final-consumer-evidence.json.current_common_selection`에 기록했다.
