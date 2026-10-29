# Main 보유·청산·익절 및 약세장 기회 연구 실행 검토 — 2026-10-23

## 1. 판정·범위

AGENTS.md와 Plan Rebase §1–§8,10/23 checklist를 재로딩하고 [계획 §18](../proposals/main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#18-2026-10-23-방향-갱신과-새-원천-연구-실행)을 갱신했다. 기존 `HoldingProfitExitSourceContractRepair`가 보유 원천 후속 작업을 소유한다.10/18 종결 연구를 재개방한 것이 아니라 새10/22 봉인 원천과10/23 실제 거래를 사용한 후속 분석이다.

**약세장에도 상승 기회가 확인되지만, 후행 상승만으로 현재 trailing이 그 수익을 보존한다고 판단할 수 없다.** 원천 적격화→진입 후 단계별 보유 판단→최고점과 executable bid의 괴리→실제 체결·비용의 순서로 연구한다. 고정 폭 민감도는 실행했으나 신규 수치·classifier의 경제 우위는 미입증이다. 현 승인 시작률0.4%·weak0.4%·strong0.8%를 변경하지 않았다.

이번 작업은 로컬 원천 읽기·읽기 전용 DB·격리 계산·문서 변경이다. 외부 API/provider/주문/구독·정책 발행·배포/재기동·Project/Calendar sync는 실행하지 않았다. 시스템의 자연 매매와 다른 세션의 배포를 이 연구의 실행으로 기록하지 않는다.

## 2. 실제 보유·청산·정책 소비

실적 census 기준은 **10/23 12:09:50 KST**다. `COMPLETED` 및 유효 `profit_rate`를 확인했다. Main SCALPING/SCALP의 `HOLDING/SELL_ORDERED/BUY_ORDERED` DB 행은0이며, 전체 계좌·수동 보유까지 flat이라는 뜻은 아니다.

| 날짜 / record | 실제 BUY → SELL | 청산 사유 | 설정 비용 반영 결과 | 해석 |
| --- | --- | --- | --- | --- |
|10/23 /49480 삼성전자 |11:22:56,207,500원×1 →11:37:40,208,500원×1 |`scalp_trailing_take_profit` |+0.250602%, 약+520원 | 부분 진입 체결의 보유1주가 완료됨. broker 실제 비용 순익은 null이다. |
|10/22 /49445 주성엔지니어링 |09:19:24.621630,198,900원×1 →12:12:09,188,700원×1 |`scalp_preset_hard_stop_pct` |−5.346405%, 약−10,634원 | 자동 보유 복구 전 시간이 포함돼 정상 보유/익절 정책 성과에서 분리한다. |

주성의 실제 fill과 DB `BUY_ORDERED`/수량 인계 불일치 및12:11:46 복구→12:12:09 청산은 [기존 복구 감사](postclose-root-cause-recovery-review-2026-10-19.md)의10/22 원 영수증을 따른다. 이 사건을 “약세 반등을 기다린 보유 정책이 실패했다”거나 “hard stop을 풀었으면 이익”으로 해석하지 않는다.

삼성49480은 최고가209,500원, 평가 시 executable bid208,500원이었다. `(209500−208500)/209500×100=0.477327%`가 weak0.4%를 넘었고 최고 수익률 약+0.73%가 시작률0.4%를 넘었다. 사건 당시 release `926ebca82aa48119ea1ff1483ef33cd78be508ee`, PID1982231이었다. `mechanical_strength_v2`의 마지막 상태는 `WEAK/valid_weak_evidence`다.3999개 상태 기록 중 WEAK2145·STRONG1838·UNKNOWN16이며, 반복 기록이므로 독립 판정 기회 수가 아니다.

`exit_signal`11:37:39.553544→`sell_order_sent`11:37:40.179730→`sell_completed`11:37:41.616393이 연결되고 체결가는 신호 bid와 같다. 이는 로컬 단계 기록 간격으로, 브로커 왕복 지연 전체의 측정값은 아니다. 동일 BUY 신원·first-crossing 원천·`main_stop_normal_exit_decision`이 존재한다. 다만 상세 경로 전체의 재생 적격을 뜻하지 않는다.

작업 중 selector가 다른 세션의 **`a2ca8e7d8d6b77456b509f6f7133a6ba2911e562` / PID2333464 / start ticks36885727**로 바뀌었다.12:09 이후 재확인에서 `/proc` cwd/start와 selector receipt가 맞고,11:58:41 bootstrap 검증은 `passed=true`, PID2333464, manifest SHA `131abef39e624b33cd9394e1397d224aa52a1d2dbc7a1479fa345e6a1e0b7ef6`이다. 현재 PID 환경의 세 시장 trailing 수치는0.4/0.4/0.8, holding policy SHA는 `a18be12637c5248cbda44ae129d4f59afa0c3168e7299f2bdc1ca55d8958ad6a`다. **오늘 체결 사건의 PID와 현재 PID를 구별한다.** 가격 진단·context·vote의 관련4개 파일은 두 release의 SHA가 같음을 검증했다.

### 시장 신원과 매도 후 호가

두 실제 거래는 정규장, 정책 cohort KRX, 원천 `_AL/krx_nxt_integrated`, 주문 SOR다. 운영 KRX 귀속과 달리 broker 확인 물리 거래소는 UNKNOWN, `actual_execution_venue_verified=false`다. 아래는 통합 route BBO이며 물리 KRX 체결 증명이 아니다.

| record | SELL 대비1분 bid |3분 |5분 |10분 | 자연 원천 상태 |
| --- | ---: | ---: | ---: | ---: | --- |
|49480 삼성 |0.0000% |+0.239808% |+0.239808% |+0.239808% |4/4 `fresh_executable_bbo_observed`,005930_AL/SOR |
|49445 주성 |+0.105988% |+0.052994% |+0.105988% |+0.423953% |4/4 같은 상태,036930_AL/SOR |

8개 horizon은 각 시점의 신선한 호가 증거이며 구간 전부가 연속이거나 해당 수량이 체결된다는 뜻은 아니다.10/21의 과거 후행 결손을 소급해 채우지 않는다. `_AL`/SOR 원천의 자연 회귀 증거를 `_NX`/NXT 수용으로 확대하지 않는다.

## 3. 정책 수립·적용에서 남은 두 원천 문제

**보유 AI 입력:**49480 원 vote store29행은 `path_input_missing:executable_exit_pnl_missing`22행과 `quote_or_tape_unusable`7행이다. provider 호출0, 유효 투표0이며 EXIT_TRAILING_TP 신호 snapshot은 `INSUFFICIENT/quorum_or_freshness_missing`이다. 모델이 매도에 동의하거나 반대했다고 볼 수 없다. `decision_proceeds`는 이 경우 청산을 유예하지 않은 결과다.

선택 release의 `holding_exit_vote.path_vote_input_gaps()`는 `payload.flow.execution_pnl.executable_sell_price`와 `estimated_net_executable_pnl_pct`를 검사한다. producer `holding_decision_context.build_holding_decision_context()`는 가격·frozen cost·전량 visible bid depth로 비용 추정을 만들며 absent와 explicit invalid를 구별한다. 원 gap source에는 context present/enabled·partial, source-ready와 필요한 필드 결손이 남아 있다. **현재 보관 증거만으로 cost model 부재, book 정합성, 개별 fee/slippage 값 중 어느 내부 분기가 최초 원인인지까지는 확정하지 않았다.** gap을 비용0이나 가상의 AI 응답으로 바꾸지 않고 같은 owner의 exact 입력 대사를 다음 작업으로 둔다.

**상세 재생 기록:** `_observe_scalp_trailing_input_transition()`은11:22:57.791부터11:23:29.836까지256개 상세행+한도 고지1개를 남겼다. 마지막 `observation_coverage_exhausted=True` 이후 같은 보유에서 early return하는 producer 조건을 코드와 원 이벤트로 확인했다. 전체 보유883초 중 약32초 만에 포화됐다. 별도 mechanical3999개·stop source2047개와 first crossing/terminal은 계속 남으므로 “청산 판단이 멈췄다”는 뜻은 아니다. 기존 writer/index/segment 및 공통 state 참조를 재사용하는 보완이 필요하며 cap 상향이나 전체 raw 반복 스캔을 해결책으로 삼지 않는다.

**장후 연구:**10/22 trailing 보고서는 등록2,602종목×8scope=20,816, 비교 모집단724, 공통 적격 ID0, `raw_census_complete=false`, 유형 연구 `hold_sample_or_source`다.12cell은 `parent_carry`, classifier=null이다. 등록 scope 상태는 operating_unobserved9/registered_nonoperating20,807이며 이것을 실제 가격 관측 수로 해석하지 않는다. `eligible_evaluation_complete=true`와 보고서 `complete`는 적격 부분의 계산 완료이며 신규 정책 학습 성공이 아니다. 승인 부모값을 계승하는 동작은 적절하지만 이 데이터로 그 수치가 최적이라고 주장할 수 없다.

## 4. 실행한 새 연구와 결과

기존 [기계 누적 연구](main-machine-pattern-dual-track-research-review-2026-10-21.md)의10/22 normalized 원천과 현재 정책 member 확인 지점을 재사용했다. 기존 readonly object store에서 NXT 두 분할의 native record를 추가 대사했다. source hash·native epoch/sequence·item·ask를 확인하고 네 분할을 각각 한 번 decode했다. 새 원천 수집이나 provider 호출은 없다.

연구 입력은 체결가·bid·ask·quote age·sequence·epoch이며, 현재 공통 pure `evaluate_trailing_take_profit()`을 사용했다. 최고 체결가의 설정 비용 반영률0.4%에서 시작하고 고정 폭0.4/0.8을 별도로 비교했다. sell-notional 비용률0.0023은 기존 연구 설정값이며 실제 세금/수수료로 확정하지 않는다. 관측 trade의 비용 반영−3%는 기존 연구와 같은 비교선일 뿐 native hard-stop 전체 재생이 아니다. horizon1800초, 불명/5초 초과 호가·item/epoch/sequence 단절에서는 censor한다.5초는 이 연구의 기존 호가 적격 기준이며 runtime stale guard를 변경하거나 통과를 보증하지 않는다.

**이 결과는 가격 조건 민감도다.** M1 강약 전환, 원 holding AI, 실제 진입/청산 시간 guard, 주문 latency·queue·전량 depth·실제 비용은 재생하지 않았다. 실제 대체청산 성과 또는 수익률 개선으로 부르지 않는다.569개 확인 지점은 겹칠 수 있으며 독립 거래/승률 분모가 아니다. 소스22는 부모 학습에도 사용돼 독립 holdout이 아니다.

| 역사 원천 분할 | 확인 지점 / 종목 |0.4폭 가격 종점 수¹ |0.8폭 가격 종점 수¹ |두 종점 공통 |0.4 우세 /0.8 우세 /동일 |
| --- | ---: | ---: | ---: | ---: | ---: |
|NXT_PREMARKET |41 /11 |29 |29 |29 |27 /2 /0 |
|NXT_REGULAR_OVERLAP |179 /3 |35 |30 |30 |30 /0 /0 |
|SOR_REGULAR |160 /6 |128 |109 |109 |76 /32 /1 |
|SOR_AFTERMARKET |189 /15 |87 |48 |48 |32 /2 /14 |
|합계 |569 /종목 중복 있음 |279 |216 |216 |165 /36 /15 |

¹ trailing 조건 또는 trade stop 비교선이 관측된 종점. horizon/원천 종료/단절은 종점 수익을 null로 남긴다. 공통 종점만의 비교에도 censor 선택 효과가 있어 우월 정책 추정으로 사용하지 않는다. normalized 전체 관측행은559,048개이며 이 중 현재 member 확인569개를 진단했다. NXT_REGULAR_OVERLAP은 당시 별도 관측 경로이며 현 Main 정규장 기본 SOR를 NXT로 바꾼 것이 아니다. 미관측 scope를 제외해 전시장 지원을 삭제하지 않으며 등록 범위와 관측 coverage를 분리한다.

0.8폭에서 목표 bid를 먼저 보았지만 가격 종점이0 이하인 지점은 장전7·NXT 정규21·통합 정규24·장후21개다. 이 숫자는 중첩 진단이며 거래 손실 건수가 아니다. **폭을 넓히는 것만으로 상승 기회 보존을 해결할 수 없다.** 시작률·최고가 기준·호가 괴리·tick 및 상황별 강약 상태를 함께 평가해야 한다.

## 5. 약세장 상승과 놓친 기회

**오늘 실제 상승 사례:** 삼성49480 진입55초 전11:22:01의 source-ready 시장 관측은 BROAD_WEAKNESS, KOSPI−2.45%·KOSDAQ−3.44%였다. 이때 진입한 삼성1주가 이후 +0.250602% 설정 비용 반영 결과로 완료됐다. 약세라는 이유만으로 명확한 상승 기회가 없다고 볼 수 없다. 다만1건이 약세장 진입 정책의 기대수익을 증명하지는 않는다.

**10/22 미포착·추가 패턴의 예시:** 기존 연구에서 시장 관측≤120초, 선행 A33/A36 패턴 확인, 그 시점 ask→후행 bid 순서를 갖춘4건을 다시 대사했다. 실제 주문이 없었던 예시이며 전량 체결/순익을 약속하지 않는다. 이4건은 사후 상승 사례로 선택된 설명용 부분집합이므로 §4의 집계에 추가하지 않았다.

| 코드 / 확인 시각 KST |당시 ask → 첫 목표 bid |목표까지 |시장 KOSPI/KOSDAQ |0.4폭 가격 종점² |0.8폭 가격 종점² |
| --- | --- | ---: | --- | ---: | ---: |
|003010 /14:04:58.845 |11,120→11,210 |214.699초 |−3.32/−2.81% |−0.3197% |−0.3197% |
|034020 /09:34:30.933 |62,800→63,200 |351.176초 |−1.11/−1.41% |+1.0410% |+0.5643% |
|036930 /11:08:36.104 |189,100→190,300 |161.300초 |−2.03/−1.75% |+0.3504% |−0.0717% |
|290720 /14:32:07.244 |1,679→1,690 |12.600초 |−3.83/−3.46% |−0.2300% |−0.1112% |

² 첫 가격 조건 종점의 설정 비용 반영 bid 값이며 실제 매도/전략 수익이 아니다.003010은 시작2.699초 뒤 trade11,200/bid11,110/ask11,140,290720는6.7초 뒤 trade1,692/bid1,679/ask1,686이었다. trade 최고점이 먼저 시작률을 넘고 bid는 뒤처져 trailing 조건을 먼저 충족했다. 호가시각이 있다는 것만으로 해당 trade/BBO의 runtime 일관성 guard 통과를 증명하지 않는다. 따라서 원 timestamp·route·일관성 검증을 선행하고 양쪽 가격 기준의 차이를 연구한다. 뒤의 상승을 근거로 “이익을 확실히 놓쳤다”고 단정하지 않는다.

실제 보조 PASS 뒤 차단된 다른 모집단은 [post-aux 연구](main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md)의10/23 실행에서6개 중 target-first1·timeout5로 분리돼 있다.034020의 generation-change 차단 사례가 target-first였다는 사실과 위09:34 패턴 예시는 **서로 다른 attempt**다. blanket 약세 veto 연구도 기존160지점에서 winner1과 timeout4를 함께 제거했으므로 실패만 줄인 정책이 아니다. 원 결과를 임계치 완화나 guard 해제 근거로 사용하지 않는다. 장후의 정규장 지수 snapshot은 오래됐으므로 장후 약세 기회 판정에서는 별도 미확인으로 남긴다.

## 6. 원천·재현·성능·리뷰

- [사전 입력 봉인](../../tmp/holding-exit-opportunity-research-20261023/freeze.json): 새 계산 전에 범위·고정 비교폭·비용·원천·한계를 기록했다. 이미 본 소스의 탐색 연구임을 명시했다.
- [가격 경로 결과](../../tmp/holding-exit-opportunity-research-20261023/result.json), SHA256 `3882b412819a462b31aeeb5aff429834d50555702b2b89973188e49b544ded56`. 최초 결과의 부수 중앙값 계산 정정 전 원본은 `result-attempt01.json`에 보존했다.
- [현재 실적·원 이벤트 참조](../../tmp/holding-exit-opportunity-research-20261023/live-snapshot.json), [현재 PID·정책 소비](../../tmp/holding-exit-opportunity-research-20261023/current-consumption.json), [가격 괴리 세부](../../tmp/holding-exit-opportunity-research-20261023/illustration-detail.json), [검증](../../tmp/holding-exit-opportunity-research-20261023/validation.json).
- 원 normalized 압축8,529,811B를 사용했다. wall16.888초·CPU17.022초·peak RSS383,688KiB, 명시1.5GiB/120CPU초 상한이다. 이 비용은 계산 구간이며 snapshot/검증 시간은 포함하지 않는다. 원10/22 raw 약5GB 전체 재스캔·전체 postclose 재생성은 하지 않았다. Main 지연 비악화의 부하 시험을 수행한 것은 아니다.
- 기존 pure 결정기·normalized kernel·readonly object store를 재사용했다. 임시 `study.py/snapshot.py/test_study.py`는 재현용 연구 파일이며 production module/dispatcher/report owner/cron을 추가하지 않았다. 기존 실제/CF 원천 파일·두 폭별 censored 결과·원 실패 기록을 보존했다.

자체 리뷰에서 미래 horizon 전에 sequence 단절을 먼저 확인하도록 보완했다. 미래 고점 누수, quote age 누락/stale, route/epoch/sequence 전환, 모델 비용을 뺀 시작률, target 이후 손실 조건, stop 우선순위, censor를0으로 합산하지 않는 검증과 오늘 실제 pure 조건 재현, 짝수 모집단 중앙값을 포함해 **9 PASS**다. 중앙값은 최초 결과를 보존하고 기존 종점만 재집계했으며 가격 재생은 반복하지 않았다. 별도 선형 순회로4개 약세 예시의 첫 목표 bid·시각을 재검증했고 두 release 관련4개 파일 hash가 일치했다. 정확한 `KORSTOCKSCAN_` 환경변수 접두어 및 `payload.flow` 소비 이름을 대사했다. 실제 비용·전량 depth/queue·강약/AI·실제 주문 guard가 없는 비교를 경제 재생이라고 부르지 않도록 결과 표현도 보완했다.

변경 기준 HEAD는 `609cdcf12403ec2e2ed7e273cd49e839e781ac9d`다. 비테스트 production source0·production test0, 계획 및 이 감사·현재 checklist만 본 작업의 문서 변경이다. tmp 연구 스크립트/검증과 산출물은 별도다. 기존 구현은 모두 **retained**: runtime/장후/재생이 현재 소비하므로 제거 대상이 아니다. 중복 소비자를 대체하거나 파일을 이동하지 않았다. 새 문서는 새 증거의 감사 기록이며 별도 보고서 producer나 tracking owner가 아니다. 병행 작업의 dirty source·문서·AGENTS는 수정하지 않았다.

checklist 편집 전 native `preserve_checklist()`는 이미 원 봉인 후 편집된 문서라 `intraday_checklist_not_current_sealed_generation`을 반환했다. 최신 prepared receipt SHA→controller→strict가 가리키는 원 archive `91d9874a2fe47a5bcebe281c052ca65d0c978fe3477562557a7e735ae8b23011.md`가 기존 historical_checklists에 존재하고 exact SHA가 맞음을 확인했다. 원 strict/controller/준비/과거 문서를 다시 쓰지 않았다. 현재 owner 문서에만 연구 결과와 다음 검사를 추가한다.

최종 문서 link/owner/authority·diff 및 print-only parser 검증은 아래 완료 기록을 따른다. 거래 회귀 전체·외부 provider·P5·배포·장후 전체 재생성은 이 연구의 범위가 아니므로 실행하지 않는다. 후속 새 source23 봉인 연구의 예정 창은 기존 `MachinePatternOpportunityResearch1023`의10/26 07:40–08:00이고, 현재 증명되지 않은 보유 입력/포화 개선은 기존 holding owner에 남긴다.

### 문서·연구 검증 완료

9개 표적 연구 검사·3개 파일 compile, 원천/결과/code hash 및569개 분모 대사, 새/변경 영역의 로컬 링크16개·현재 holding owner1개, `git diff --check`와 print-only parser를 통과했다. parser26개 중 holding owner는10/23 checklist의1개이며10/26 기계 연구 예정 창도 유지됐다. 본 작업 문서 순증은 계획+34/−1, 이 감사+104/−0, 병행 작성 중인 현재 checklist에 연구 항목+2/−0이다. production source/test는 각각+0/−0이며, 격리 연구 재현 스크립트는344행·연구 test는78행을 추가했다. 운영 owner/분기/entrypoint 증가는0이다. 원 연구와 실제 정책 최적성의 한계를 재리뷰에 반영했으며 남은 운영 원천 작업의 검증 완료로 확대하지 않는다.


## 7. 2026-10-23 보유 입력·연속 재생 원인 수리

사용자 승인 범위는 소스 구현·코드리뷰·보완·오프라인 검증이다. 배포는 별도 승인이다. 구현은 선택 release `a2ca8e7d8d6b77456b509f6f7133a6ba2911e562`에서 만든 `/home/ubuntu/KORStockScan-worktrees/holding-input-replay-stream-20261023`, branch `fix/holding-input-replay-stream-20261023`에 격리했다. 기존 작업공간의 병행 소스 변경을 덮어쓰지 않았다. 13:04 KST 재확인에서도 selector SHA `1eea4fd7dc8a651761a3a8170e83ddc95e3da5d4c601cc75e6013a2af661a91c`, PID2333464/start36885727, 선택 a2ca가 유지됐다. [재확인](../../tmp/holding-input-replay-stream-20261023/consumer-recheck.json).

### 최초 위반과 수리

1. **보유 AI의 실행 손익 결손**: `freeze_entry_operating_context.frozen_at`은 aware ISO 문자열이고 Main 진입 생산자가 이를 `_trailing_entry_cost_model.known_at`에 그대로 동결한다. 원49480은 `2026-10-23T11:22:56.081940+09:00`였다. `holding_decision_context._observed_exit_costs`만 숫자 epoch를 요구하여 정상 비용 원천을 거부했다. 기존 `holding_vote_exit_models.cost_known_epoch`를 재사용해 aware ISO/기존 epoch를 동일하게 해석한다. 원문·원 비용 SHA를 바꾸지 않는다. 모델 비용과 실제 체결 비용은 계속 구별한다. 미래/naive/invalid/bool 시각, 부족한 전량 호가, stale/conflict, 명시된 미확정 비용은 계속 null이다. 원 사건22개 PnL 결손과 별도7개 quote/tape 불가는 구별하며 후자를 해결했다고 주장하지 않는다.
2. **상세 재생 조기 종료**: `_observe_scalp_trailing_input_transition`의 `MAX_POSITION_SAMPLES=256`은 보유 전체를 한 번만 세는 제한이었다. 새 기계 원천마다 상세 이벤트를 남겨32초에 소진됐고, 이후 생애 기록을 영구 중단했다. 해당 상수·중단 분기를 제거하고 기존 `BoundedObservationQueue`의 `trailing` 예약을 사용한다. 전체1024건/4MiB, 개별64KiB는 그대로이며 trailing은 최대128건/512KiB로 더 작게 제한된다. 기존 executor·8건/4ms 양보·native 종료 drain을 재사용한다. 새 thread/pool, 동기 fallback, 무제한 메모리 누적을 만들지 않는다.
3. **저장·소비 계약**: 진단 입력은 admission 시 finite JSON으로 동결한다. worker에서 `universal_trailing_quote`를 무손실 zlib+base64로 저장하며 원문 길이/SHA, 원 의미 `source_sha256`, item/route/epoch/clock을 유지한다. 기존12KiB quote 원문 상한도 유지한다. `universal_trailing_replay.decode_quote` 하나로 기존 dict/JSON과 새 압축 포맷을 읽고 길이·hash·trailing bytes·잘못된 codec을 검증한다. text_payload에는 sequence/원천 SHA/상태를 참조하여 큰 본문을 중복 저장하지 않는다. 원 canonical fields와 threshold companion은 보존한다.
4. **마지막 누락까지 검증**: admission 거절/None/false는 다음 이벤트와 종료 원천에 결손을 남긴다. 큐 등록 성공을 저장 성공으로 계산하지 않는다. 실제 SELL의 `_SELL_RECEIPT_SNAPSHOT_KEYS`→`_build_sell_lifecycle_outbox_leg`에 `trailing_observation_close`를 동결하여 reset·재시도 이후에도 position/첫 BUY 결속/예상 sequence 수/결손을 유지한다. 재생의 상수 메모리 `ObservationCoverage`는 전 구간 순서·누락·중복·native SOURCE_GAP 및 종료 수를 대사한다. 중간 또는 마지막 저장 실패와 전부 누락도 source gap이다. cap 소진된 과거 자료를 완전한 경로로 복구했다고 표시하지 않는다.

| 생산/소비 경계 | 변경 및 검증 대상 |
| --- | --- |
| 비용 생산자 → context → vote | ISO 동결 계약 유지 → 공유 시각 해석 → `payload.flow.execution_pnl` 전달. 원래 실패하는 회귀를 먼저 재현하고 수정했다. |
| Main 관측 → 공통 queue/writer | 영구256건 절단 제거, 동일 executor 예약·동결·shutdown. 종목/시장 whitelist 없음. |
| native terminal snapshot → outbox → 실제 JSONL | 예상 관측 수와 원 generation 동결. 실제 outbox ACK 계약으로 저장 결과를 검증한다. |
| 원 pipeline → 기존 index → entry-plan/CF assembler | 압축 quote reader를 연결하고 원 index hash/offset/계보는 그대로 사용한다. raw 재스캔 없음. |
| completed resident/stream → partitioned replay | 두 projection이 동일하게 디코딩·종료 대사, metadata에 결손을 전달한다. 기존 분할·캐시·대용량 stream 경로 재사용. |
| pre-submit-delay 연구의 quote 소비 | 같은 decoder를 사용한다. 요청·정책·주문 경로를 변경하지 않는다. |

Premarket `_NX`/nxt_only/NXT, Regular `_AL`/integrated/SOR/cohort KRX, Aftermarket `_AL`/integrated/SOR/cohort integrated를 재명명하지 않는다. 실제 거래소 UNKNOWN/미검증은 그대로다. 보유·장후·재생에 종목 특례나 시장 제외를 추가하지 않았다. 과거 원천 계약은 그 날짜 의미로 읽는다. 외부 Kiwoom 요청/응답/FID/인증/주문 parser를 수정하지 않아 이번 변경은 Official Kiwoom Reference Gate의 API 변경 대상이 아니다.

### 리뷰와 성능 검증

자체 리뷰에서 (a) 공통 logger의 모든 field가 문자열이 되는 실제 경계, (b) 일반 보유 로그와 별도인 native SELL/outbox 생산자, (c) `SOURCE_GAP` 행을 단순히 생략했을 때의 허위 완전성, (d) quote가 text_payload에 다시 저장되는 낭비, (e) None/false admission의 조용한 실패를 확인하고 보완했다. terminal 회귀 fixture의 주문/체결 identity 누락도 기존 ACK guard를 유지한 채 올바른 offline fixture로 수정했다. source 실패를 숨기거나 ACK/guard를 완화하지 않았다.

[동일 부하 비교](../../tmp/holding-input-replay-stream-20261023/benchmark-result-attempt04.json)는 원49480의 고정256개 payload를 반복한 각1024건이며 자연 거래1024건이 아니다. 입력 gzip2,773,080B는 한 번 읽었고 SHA `e45c321144c21fe29a2e29a1258ea1391ba9732fd32725b2bd1727974d5a270c`를 보존했다. private root에서 기존 raw/threshold/index writer를 사용하고 text 출력/summary 작업은 양쪽 동일하게 제외했다. 최초 측정·보완 전 결과01–03도 보존했다. Main 전체 처리량/실시간 주문 지연을 측정한 것은 아니다.

| 동일1024건 측정 | 기존 동기 저장 | 수리 후 bounded 비동기/압축 |
| --- | ---: | ---: |
| 생산자 호출 중앙값 | 1.120ms | 0.178ms |
| 생산자 호출 p95 | 1.306ms | 0.216ms |
| raw bytes/건 | 30,988 | 13,194 |
| 총 process CPU/건 | 1.090ms | 1.429ms |
| 저장 성공/실패/거절 | 1024/0/0 | 1024/0/0 |

호출 p95 약83.5%, raw 용량 약57.4%가 감소했다. 반면 총 CPU는 약31.1% 증가했다. 동결·비동기 전달·압축의 비용이며 전체 CPU 개선이라고 쓰지 않는다. 5ms 간격 스트레스 입력에서 queue 최대9건/129,551B, 종료 pending0, 원257개 quote 무손실 대사 PASS다. 큐 건수/bytes·기존 worker 양보가 Main의 추가 대기와 무제한 부하를 막는다. 실제 동시 보유·Main CPU/lag·등록 손실은 배포 승인 이후 자연 수용에서 측정한다. 호출이 원래 누락되어 생략됐던 보유 AI의 정상 복구에 따른 호출 증가는 기존 주기·예산·provider 제한을 따른다.

확장 일괄 검사는1,519 PASS/4 FAIL이었다. 이 중 native terminal fixture 보완은 앞선 별도 실패에서 이미 해결됐다. 4건은 기존 baseline에서도 실패하는 원 AST 해시 검사2건, 이번 진단 sink 등록을 반영하지 않은 startup parity1건, 묶음 실행에서만 실패한 delay observer 검사1건이다. 후자는 전역 상태 간섭을 의심하지만 정확한 선행 테스트는 확정하지 않았다. [수정 전 baseline 대사](../../tmp/holding-input-replay-stream-20261023/baseline-parity-check.json)를 보존했다. startup은 정확한 등록2문장만 제거했을 때 원 본문과 일치하도록 검사하며, 선택 a2ca 대비 loop/run/close parity도 추가했다. delay 파일은 별도 process로 검증한다. 기존 baseline 실패2건의 hash를 성공값으로 덮거나 xfail로 숨기지 않았고 이 수리의 통과로 주장하지 않는다. [최초 확장 검사](../../tmp/holding-input-replay-stream-20261023/pytest-final-attempt01.log), [runtime 보완 검사205 PASS](../../tmp/holding-input-replay-stream-20261023/pytest-supplemental-runtime.log), [startup 진단 추가 검사8 PASS](../../tmp/holding-input-replay-stream-20261023/pytest-supplemental.log).

### 대체·제거 및 남은 수용

- **removed**: `MAX_POSITION_SAMPLES` 및 보유 생애256건 중단 분기. callers는 기존 관측 함수 하나이며 새 소비자는 큐의 resource bounds를 따른다.
- **consolidated**: 상세 transition 동기 저장은 기존 공통 queue/writer로, 각자 JSON 해석하던 직접 소비는 공통 codec으로 모았다. 새로운 Python module·report producer·wrapper·cron·worker pool은0이다.
- **retained**: 일반 holding/first-crossing/SELL의 동기 영수증 경로, source index/partition reader, 과거 coverage_exhausted 독자, 거래소·stale·수량·custody·hard stop·AI 판정/주문 guard. 현재 소비자가 있어 제거하지 않는다. 파일 이동0, 이 범위의 미사용 대체 경로/임시 wrapper0이다.
- **OPEN**: 배포 승인, exact release/PID 소비, 실제 모든 활성 세션의256초과 관측→native terminal→장후 projection/재생, queue/CPU/lag/bytes 검증. 같은 `HoldingProfitExitSourceContractRepair` owner에서 배포 승인 후 첫 가용 `_AL`/SOR 및 별도 `_NX`/NXT 자연 창을 잡는다. 관측/입력 수용을 위해 주문을 만들지 않는다. 원49480의 cap 이후 자료와 누락된 AI 판정을 소급 생성하지 않는다. 실제 비용·정책 경제 우위·수익 증가도 아직 증명하지 않았다.


### 소스 수리 최종 검증

[최종 대상 회귀](../../tmp/holding-input-replay-stream-20261023/pytest-final-scoped.log) **1,509 PASS**, [별도 process의 delay 계약](../../tmp/holding-input-replay-stream-20261023/pytest-delay-isolated.log) **13 PASS**다. 수정 전 실패가 재현된 역사적 AST 검사2건만 최종 범위에서 명시적으로 제외했으며 원 실패 로그는 보존했다. 총1,522개 통과를 전체 저장소 GREEN이나 배포 수용으로 확대하지 않는다. Python18파일 compile, diff check, 새 수리 문서 링크, 현재 stable owner1개 및 print-only parser를 통과했다. [검증 원장](../../tmp/holding-input-replay-stream-20261023/validation.json).

소스 기준a2ca 대비 비테스트10파일 **+247/−33**, 테스트8파일 **+239/−12**다. 무손실 codec·종료 coverage·negative 검증 때문에 순증했으며 새 source module/실행 entrypoint/거래 decision branch는 없다. 기존 관측 queue category와 startup/close 등록만 추가됐다. 이 감사의 앞104행은 선행 연구이며 수리 기록을 같은 owner에 이어 썼다. base checklist에는 본 수리 진행1행만 추가했고 병행 항목은 보존했다. immutable checklist archive `91d9874a2fe47a5bcebe281c052ca65d0c978fe3477562557a7e735ae8b23011`의 원 bytes/SHA를 편집 전에 재확인했다. 외부 sync·패키지·provider·Kiwoom 요청/주문·정책 임계치·원 장후 산출물·선택 release/PID를 변경하지 않았다.


### Integration review before runtime transition (2026-10-23)

선행9e820 소비 이후 c4a177을 병합하고 재리뷰했다. 기존204개 exact code profile/변조·누락·세대 혼합 검사와488개 ordered/replay/startup 검사, fixture 원장격리 보완 후94개 런타임 검사를 통과했다. 원 AST 해시 실패2개는 기존 평가시각 수리의 정확한 두 delta로 원인이 확정됐고, 해시를 바꾸지 않고 해당 delta를 검증하여 모두 통과했다. 커밋 전 dirty verifier 거부는 원 실패로 보존했다.

추가 과거 발행726179 원천 검사에서9e820도 거부하던 기존 코드 계보 누락을 재현했다. 기존 source-pair table의 정확한2단계 경로16개를 고정된 direct pair로 연결하고, c4 producer 변경7개 원천도 exact successor profile에 결속했다. 동적/임의 전이 허용은 추가하지 않았다. [기존 검토 경로 대사](../../tmp/quantity-historical-recovery-20261023/c4-existing-review-chain-audit.json). 원 policy·manifest·summary·PID 영수증은 그대로 유지하고 전체 successor profile 검사와 독립 준비 inventory가 계속 필요하다.

대체/제거는 앞 수리의256건 생애 cap 제거와 공통 bounded queue·codec 소비 통합을 유지한다. 통합 보완은 기존 handoff/preparation code owner에 exact source표를 추가하고 실제소비9e820 profile을 retained했다. 새 source module·report producer·wrapper·worker·실행 entrypoint·이동0. 등록/codec/terminal 검증 때문에 순증하며 승인 원천을 모르는 hash는 계속 거부한다. 9e820 대비 본 기록 직전 증감: {"source": {"files": 13, "added": 433, "deleted": 35}, "tests": {"files": 10, "added": 301, "deleted": 15}, "docs": {"files": 3, "added": 171, "deleted": 0}}. 이 기록 자체는 문서 추가로 별도 계산한다. 전체 저장소 테스트 완료나 자연 수집/경제성 완료로 확대하지 않는다. 최종 immutable 후보의 native 원천 갱신·P5·ordered 실제 전환 결과는 기존 배포 기록에 이어 보존한다.


### Integrated runtime acceptance (2026-10-23 15:30)

승인된c4a177cb8은 선행 정책 수리를 포함한6d8891ac3으로15:30:40 배포·재기동 완료했다. Main3299469/start38150614의 native 정책 소비와candidate/selected P5가 통과했다. 변경된 trailing/수량 code의 native 근거도 재검증했다. 앞선 배포 전 OPEN 중 승인·선택·PID 항목은 이 후속 증거로 종료하고,256초과 자연 관측→native SELL 종료→장후 재생/경제성은 기존 holding owner에서 유지한다. [통합 배포·잔여 수용·검증 시간](postclose-root-cause-recovery-review-2026-10-19.md#holding-stream-integration-deployment-and-quantity-validation-timing-2026-10-23). 원9e820 대비 source13파일+433/-35, tests10파일+301/-15, 배포 전 docs3파일+180/-0이며 본 완료 기록은 별도 문서 추가다.

## 8. 2026-10-28 안랩 진입 연결·재생 원천 수리와 공동 연구

### 판정과 사건 범위

사용자가 요청한 진입 원천 연결, 재생 호가 결손 보완과 시작률·반납폭·비용 반영 보호·강세 해제 공동 연구를 구현하고 두 차례 코드 리뷰의 발견 사항을 보완했다. 기준 commit은 `1756de1d9d7943739d539d5207cc55484185bff5`다. [기존 현재 owner](../checklists/2026-10-28-stage2-todo-checklist.md)는 `HoldingProfitExitSourceContractRepair`이며 새 작업 ID를 만들지 않았다. 이 절은 소스 구현과 격리 연구의 결과다. 배포, 정책 발행, 선택 release 변경, 재기동, 외부 원천 호출 또는 주문을 수행하지 않았다. 앞 절의10/23 배포 수용은 이번 수정의 수용이 아니다.

안랩053800/record49559는5주 계획 중 probe1주만96,200원에 체결되고4주는 미제출됐다. BUY 수신08:17:18.738107→SELL 수신08:17:47.663135, 보유28.925028초다. 장전 정책 cohort PREMARKET, 데이터053800_NX/nxt_only, 요청 NXT, native 체결 영수증의 실제 거래소 NXT를 각각 구별했다. 사건 release `29a3c14758f2f7935fc811b8b49719314bb0702c`, PID2852722/start78626491은 역사 신원이며 현재 실행을 주장하지 않는다.

최고 체결가97,000원에서 비용 반영 peak 약+0.60%로 시작률0.4%를 넘었고, bid96,200원에서 반납률0.824742%가 STRONG 폭0.8%를 넘었다. 동일 매수·매도가의−0.23%는 설정 비용률0.0023을 반영한 결과이며 실제 브로커 비용 순익은 null이다. 실제 경로는 `scalp_trailing_take_profit`이다. AI 투표0건/INSUFFICIENT가 매도를 유예하지 않았고, soft-stop60초 유예는 이 경로에 적용되지 않았다. [원 사건 분석](../../tmp/ahnlab-immediate-exit-review-20261028/analysis.json), [원본 범위](../../tmp/ahnlab-immediate-exit-review-20261028/source-review.json).

### 최초 결함과 생산자·소비자 보완

| 최초 원인 | 기존 소유자에서의 보완 | 소비·잔여 경계 |
| --- | --- | --- |
| 계획 known_at08:17:18.1840398이 초 단위 FID908 체결08:17:18보다 뒤라는 비교로 원 진입 연결을 폐기 | `trailing_entry_research_source`의 v3 연결에 원 체결시각과 첫 native packet ingress08:17:18.738107을 별도 보존. 동일 초·공식 시각·동일 BUY generation·계획≤수신≤관측 조건 검증 | `validate_holding_link`와 assembler의 기존 독자가 v3를 소비한다. v1/v2 역사 독자와 계좌·수량·비용·custody·CF 동등성 검증은 유지. 소수점 체결시각을 만들지 않는다. |
| 직접 native 결과 인계가 async 완료 분기의 진입 context 생성 지점을 우회하여 원 계획의 entry_context=null | 초기 주문 공통 계획 생성 지점으로 생성 책임을 통합. 정확한 evaluation_attempt_id, 결과 완료시각, 이미 확보된 completed bars·호가·VWAP만 사용 | 기존 capture→계획→보유 연결/상황 pin 소비를 유지. ADD가 최초 진입을 덮어쓰지 않는다. 원 사건의 소실 context는 소급 생성하지 않는다. |
| 최신0B의 BBO 시각과 별도0D depth 시각을 같아야 한다고 판단 | 공통 호가 context에서 item·route·epoch·양쪽 BBO 일치와0D 자체 freshness를 검증. 실제 `orderbook` 형식은 기존 공통 판독기로 읽고, 연구 quote의 시각·route_sequence를 실제0D에 결속 | 일반/fast 경로가 같은 context를 소비한다. 다른 route·epoch, 가격 불일치, stale/future·수량 결손은 계속 거부한다. 실행 호가 또는 매도 guard를 완화하지 않는다. |
| coverage=false이면 이미 확보한 bounded history까지 즉시 폐기 | 기존 `universal_trailing_replay` projection이 확보된 history를 `kind=GAP`, `coverage_complete=false`로 보존 | 기존 codec→source assembler→연구 독자를 사용한다. 상세 자료 보존과 완전 재생 적격은 별개이며 GAP은 정상 QUOTE로 수용되지 않는다. |

원101개 transition은 정상 quote62개, `bid_identity_missing`36개, `bid_clock_missing`3개다.36개는0B/0D clock 비교 결함의 대상이지만, 당시 폐기된 상세 입력이 없으므로36개를 복구된 정상 quote로 세지 않았다. 향후 수집의 오분류와 진단 자료 폐기를 보완했다. 원284행은 확보 시 raw offset/size/SHA로 대사됐으며 원본은 변경하지 않았다.

키움 wire parser·필드·구독은 수정하지 않았다. `broker_execution_time_source`, `broker_execution_received_at`, `broker_execution_receive_time_source`, route별0D `orderbook`은 이미 존재하는 생산자 필드를 실제 소비 지점까지 확인했다. 보유 연결 v3의 reader를 함께 갱신했다. 신규 외부 원천, 생산자 없는 임의 지표 또는 확보 불가능한 실제 대체체결을 요구하지 않는다. 실제 비용·원 당시 AI 판단·누락 구간 최초 교차는 미확인으로 남긴다.

### 공동 연구 설계와 실행 결과

기존 수동 연구 소비자인 `automation/main_trailing_research_diagnostics`를 확장했다. 새 런타임 classifier나 자동 정책 발행기를 추가하지 않았다. 입력은 봉인된 quote, 원 parent 값·classifier, frozen 비용 모델이며 native M1을 snapshot당 한 번 계산해72개 가설에 공유한다. 같은 경로에서 아래 축을 함께 비교한다.

| 축 | 고정 탐색 범위 | 인과·비용 경계 |
| --- | --- | --- |
| 시작률 | 시장 parent 대비−0.2/0/+0.2%p, 최소0.1% | 이 사건 parent0.4%에서는0.2/0.4/0.6%. 각 가설의 arm 상태를 별도 보존 |
| 반납폭 | weak·strong 각각 parent의0.5/1배 | 이 사건 weak0.2/0.4%, strong0.4/0.8%. 공통 pure trailing 판정 재사용 |
| 비용 반영 보호 | 없음 / 순수익0% / +0.2% | trailing arm 이후 실제 관측 bid 순수익이 보호선을 먼저 넘은 경우만 보호 활성화. 다음 tick의 하향 돌파는 음수 체결 지점도 허용 |
| 강세 해제 | 원 M1 / 매도 OFI와 signed tape가2회 연속 불리하면 해제 | 후자는 양의 queue imbalance만으로 강세를 계속 유지하는 경우를 비교하는 연구 가설. 실제 정책은 그대로 유지 |

72=`3×2×2×3×2`이며, 모든 조합에0/30/100bp 슬리피지 민감도를 기록한다. 실제 전량 체결을 가정하지 않고 visible bid 수량이 부족하면 가격 순익도 null이다. ADD는 같은 원가·수량 가설의 진행을 중단한다. 누락·해시·route·clock·classifier 불명은 censor하며, 출력은 **관측 snapshot에서의 조건 충족**이다. buffered depth 이벤트 전부의 최초 교차나 완전 경로 재생이라고 부르지 않는다.

안랩 원본을 이용한 [수정 전 실패→v3 독자 수용 및 공동 결과](../../tmp/ahnlab-trailing-source-repair-20261028/incident-reviewed.json)에서는 초 단위 원 체결시각을 그대로 유지하면서 연결 실패가 해결됨을 재현했다. 연구의 진입 가용 시점은 첫 packet 수신시각으로 보수적으로 고정했고, 이를 체결 발생시각으로 바꾸지 않았다. 원 quote의 봉인된 parent·classifier hash를 대사했으며62개 정상 quote만 계산에 사용했다.

| 안랩 비교 조건 | 관측된 청산 조건 시각 KST | bid | 설정 비용 반영률 | 30bp 불리한 체결 민감도 |
| --- | --- | ---: | ---: | ---: |
| 원0.4/0.4/0.8·원 강세·보호 없음 |08:17:46.435 |96,200 |−0.2300% |−0.5293% |
| 같은 수치·매도 흐름2회 강세 해제 |08:17:41.509 |96,600 |+0.1848% |−0.1157% |
| 같은 수치·원 강세·순수익0% 보호 |08:17:42.872 |96,400 |−0.0226% |−0.3225% |
| 같은 수치·원 강세·순수익+0.2% 보호 |08:17:41.509 |96,600 |+0.1848% |−0.1157% |

**더 이른 관측 지점은 있으나 수익 우위는 미입증이다.** 0% 보호도 tick 도약 때문에 손익분기를 보장하지 않는다. 모든 비교는 결손이 포함된 단일 사건이고 실제 대체 주문·체결이 아니다. 반납폭만 줄이기보다 executable bid의 비용 반영 수익과 강세 유지 조건을 함께 연구해야 한다는 원인 가설을 지지한다.

과거 확대 연구는 가족 refresh 시작2026-09-29부터10/27까지 원 입력 generation `351d0b861be6216a3967e85941720dbfe43014d74101d7e1030ebf1e42889fa1`을 사용했다. [사전 가설·입력 봉인](../../tmp/ahnlab-trailing-source-repair-20261028/joint-forward-window-reviewed/registration.json), [결과](../../tmp/ahnlab-trailing-source-repair-20261028/joint-forward-window-reviewed/research.json). 입력 manifest SHA `6888d362580dccc59bfc3108abe15a202e14e3061c8599658156677d293e214a`와 원 연구 보고서 SHA `669f23315a22471e443a9c57fff44928c51b4bfa04bc7e0511d400b852f5b7cf`를 보존했다. 과거 보고서가 현재 변경 코드의 검증을 통과했다고 주장하지 않는다.

실제 완료37건 중 custody 제외24건, 자동관리13건의18,324행을 한 번 읽었다. 검증 quote4,716개, 비용·수량 generation 조건을 끝까지 유지한7건, 가설 평가116,736회다.13건 중 원 기준과 비교 가능한 관측 교차는295310/49402 한 건이며 이 건도 censored다. 나머지12건을 손실·실패·무효 전략으로 세지 않는다. 이 자료는 독립 holdout이 아니며 EV·실제 순익·선택 정책은 null, `allowed_runtime_apply=false`다. 거래 실적이 늘기만 기다려 해결할 문제와 수집·연결 결함을 구별했다. 이번 수리는 후자를 직접 보완한다.

### 성능·리뷰·검증·잔여 수용

운영 경로는 별도 WS getter·REST·AI·파일 읽기 없이 이미 확보한 context의 필요한 필드만 복사한다. 큰 prepared context 전체 해동을 제거했다. 기존 history120개·codec12KiB·공통 writer의 한도를 높이지 않았다. 연구는 source 한 번 읽기, 포지션당72개 상태, native resident-data claim128KiB와 기존 disk index/tree로 출력한다. 모든 포지션의72개 상세 결과를 메모리 summary에 누적하지 않는다.

격리 확대 실행16.323초, 최대 RSS56,688KiB(약55.4MiB), 첫 포지션 이후 고수위 증가 없이 완료했다. 앞 실행의1,022,428KiB 측정도 원 결과에 보존했으며 동일 프로세스 조건의 성능 개선률로 사용하지 않는다. 안랩101행 공동 계산은 약0.089초다. [반복 비교 비용](../../tmp/ahnlab-trailing-source-repair-20261028/performance.json)의12회 중앙값은 기존 관측 요약28.22ms→새72개 가설 포함84.47ms다. 이 추가 계산은 격리 연구 비용이며 Main 주문 latency 개선을 주장하지 않는다.

첫 리뷰에서 실제0D 생산자의 `orderbook`과 시험용 최상위 가격 필드 차이, canonical0D 시각에0B sequence가 남는 문제를 찾아 공통 판독기와0D sequence로 보완했다. 다음 리뷰에서 숫자 직렬화 비용 소비와 전체 context 해동 비용을 보완했다. 같은 초의 공식 시각/수신시각, future·wrong generation·route·epoch·BBO·stale, 원 바 해시, 비용 부재·수량 부족·ADD·GAP의 생산/소비 회귀를 확인했다. [최종 대상 회귀](../../tmp/ahnlab-trailing-source-repair-20261028/pytest-final.log)609 PASS, [추가 비용 소비자](../../tmp/ahnlab-trailing-source-repair-20261028/pytest-cost-consumer.log)37 PASS다.9개 Python compile, 최종 diff check, 새 문서 링크·현재 owner1개·print-only parser 결과는 [검증 원장](../../tmp/ahnlab-trailing-source-repair-20261028/validation.json)을 따른다. 범위 밖 병행 변경은 수정하지 않았다.

대체·제거: async 전용 entry context 생성은 **consolidated**(공통 초기 계획으로 이동);0B/0D 동일시각 강제와 incomplete history 즉시 폐기는 **removed**; v1/v2 역사 독자·기존 주문/하드 안전장치·연구 selector는 **retained**(현재 또는 역사 소비자 존재). 새 engine module·실행 entrypoint·worker·cron·임시 wrapper·파일 이동은0이다. 소스4파일 +387/−33, 테스트5파일 +432/−1로, 명시적 clock 계약·bounded 공동 연구·음성 회귀 때문에 순증했다. 기존 병행 변경은 이 수치와 검토 범위에서 제외했다.

의존성 disposition은 원 사건/raw·10/27 봉인 입력·원 연구 보고서 **reuse/read-only revalidate**, 새 가설 결과만 **regenerate**다. 원 입력/보고서/selector/bootstrap을 덮어쓰지 않았다. 수동 연구 호출과 테스트가 새 진단 tree의 소비자이며 자동 장후 dispatch나 정책 선택에 연결했다고 주장하지 않는다.

후속은 같은 `HoldingProfitExitSourceContractRepair`에서 승인된 배포 이후 첫 자연 초기 진입의 plan→v3 link→quote/terminal→장후 assembler 수용을 확인한다. 검토 창은10/28 잔여 REG/16:00~20:00 통합 세션과, 미배포·미관측이면10/29 08:00~08:50 NXT PRE 및09:00~15:30 REG다. 배포가 이루어지지 않으면 해당 창은 수용 완료가 아니다. next postclose에서 v3 수용·GAP 보존·해시/epoch/시퀀스·진입 context 원천 결속과 CPU/queue lag/bytes를 검사하며 자연 주문을 만들지 않는다. 실제 비용과 독립 시간 분할 검증, 슬리피지 후 우위가 갖춰진 뒤 기존 정책 연구·선택 owner에서 승격을 별도 판단한다. 이번 코드 리뷰 종료와 미관측 자연 수용·경제성은 분리한다.

## 9. 2026-10-29 엠씨넥스 진입·보유 원천 수리와 순실행 손절 연구

판정: record49580의 기존 원문을 보존하고 **입력/응답 계약의 구현과 제한된 관측 연구**를 수행했다. 완료 분봉 입력의 운영 활성화, 정책 선정, 배포/PID 소비, 자연 응답·청산 및 실제 비용 대사는 별도 OPEN이다. 실행 owner는 현행 체크리스트의 `HoldingProfitExitSourceContractRepair` 하나를 유지한다. 기존 -3%/60초, hard/protect/emergency, AI VETO 정족수, 주문·수량·수동 custody, 신선도 및 provider/model을 변경하지 않았다.

### 사건과 재현 원천

- 원 사건: 2026-10-29 PREMARKET, Main `ce358bce0f0bbea932f0a3591ec4b40fd60b2cda`, PID1366991/start87314610, 엠씨넥스097520/record49580. 세션 PREMARKET, 정책 PREMARKET_KRX_LIKE, 원천097520_NX/nxt_only, 요청·유효 주문 NXT, broker 확인 BUY/SELL NXT를 구분했다. 원 실적11주/평균20,759.0909→20,100, 설정비용 반영-3.397854%를 실제 비용 대사 완료로 승격하지 않는다.
- 원 분석: [진입·보유 검토](../../tmp/mcnex-entry-holding-review-20261029-49580/review.md), [원문 투영 및 native receipts](../../tmp/mcnex-entry-holding-review-20261029-49580/evidence.json). 별도 RFHIC49558 역사 BUY-null을 신규 사건의 원인으로 사용하지 않는다.
- 08:04 완료 봉 O20,800/H21,100/L20,650/C20,650/V31,602가 수집됐지만 실제 compact AI fact ledger에는 전달되지 않았다. 이번 재현은 이 원 OHLCV와 native 시각·원천 item을 사용한다. 긴 윗꼬리·종가 하락·거래량 증가는 관측 사실이며 자동 진입 금지나 사후 손실 라벨이 아니다.
- native holding payload46건의 원 bytes SHA와 native source-index generation을 검증했다. 그중 전량 실행 비용·신선 호가·입력 계약을 갖춘42건을 공통 분모로 사용했고, 실행 PnL 결손4건을 제외했다. 원 유효/부족 투표 슬롯69건과 provider 요청46건은 서로 다른 분모다.
- 초기 결손 입력에는 보유11주/최우선 bid9주가 관측됐다. 전체 visible depth 및 설정비용 증거가 없으면 순손익은 null이다. 최우선 호가에 전량 체결됐다고 가정하거나 missing cost=0으로 만들지 않는다.
- 원 trailing 전이8,071건의 QUOTE5,418/source_gap2,653 중 결손 분류를 원 raw row SHA로 재조회했다. 기존 사유는 `bid_clock_missing`2,474건/`coverage_exhausted`179건이었다. 후자의 관측 소진 flag는 False여서 fallback 사유가 잘못됐다. 이 값을 기준으로 오래된256건 cap이 재발했다고 판단하지 않는다. 원천의 실제 결손은 유지한다. 추가 재조회 중 live index가 `InputPending:trailing_index_coverage_incomplete`를 반환한 시도는 진행 중 writer의 미완성 범위로 남기고 강제 재색인·coverage 승격을 하지 않았다. 앞서 검증한 세대/원본은 보존한다.

### 구현과 생산자 → 소비자

| 변경 | 생산자와 소비자 | 경계/잔여 수용 |
| --- | --- | --- |
| 완료 분봉·추세 위험 전달 | 기존 `entry_candle_context` → `ai_engine_openai.analyze_target` → `reversal_auxiliary_intraday.apply_request` → registry/production_input → compact wire/schema → 응답 decode | 별도 `auxiliary_completed_candle_risk_production_v2` opt-in. 기존 v1은 입력/판정 동등성을 유지한다. 원천 item·날짜·완료 시각·OHLCV·quality를 검사하고 최대5개 완료 봉에서 윗꼬리/종가 변화/거래량비를 만든다. 정상 forming suffix는 제외하고 완료 선행 봉을 보존한다. 새 고정 veto/추가 확인 조건은 없다. |
| 진입 입력의 연구 전달 | 동일 registry `request(..., entry_context=...)` → 기존 offline request/wire/hash | 기존 machine capture의 동일 시점 분봉을 명시 전달한다. 과거 normalized tick snapshot만으로 분봉을 복원하거나 최신 REST로 과거를 채우지 않는다. 자동 장후 모집단 확장·새 registry 발행은 이번 실행 범위에 포함하지 않았다. 원천 없는 행은 unavailable이며 해당 정보 효과를 검증한 표본으로 셀 수 없다. |
| 보유 응답 형식 | `path_vote_response_schema` → 실제 `_call_openai_safe(response_schema_override=...)` → 기존 `normalize_path_vote_bundle` | 요청 snapshot/path별 enum·사유 prefix·5~64자·1~6개를 요청에서도 강제한다. 잘못된 응답은 계속 INSUFFICIENT. 미래 거절에는 `response_contract_errors`로 필드/사유 수/길이/prefix/문자 위반을 남긴다. 과거 invalid_path_vote9건의 원 raw 응답이 현 ledger에 없어 각 원 위반을 소급 확정하지 않는다. |
| 비용·호가 원천 결손 설명 | 기존 `_observed_exit_costs` → `execution_pnl.cost_estimate_status` → model payload → `path_vote_gap_source.execution_pnl_source` | frozen cost 부재/위반, stale quote, 비정상 bid level, 전량 depth 부족을 구별한다. API/구독/비용률/수량을 바꾸지 않고 available partial book을 완전한 fill로 승격하지 않는다. |
| 재생 원천 사유 일치 | `_main_stop_quote_context`의 동일 predicate 목록 → complete와 source_gap_reasons → 기존 trailing 전이 사유 | 서로 다른 중첩 판정식을 통합했다. 부적격은 그대로이며 stale/future bid·가격 불가 등이 실제 용량 소진으로 기록되지 않는다. 기존 source_gap 원문은 수정하지 않는다. |
| 기준선·임계치·유예 공동 관측 | native holding payload → `main_stop_replay.compare_soft_stop_basis` → 독립 연구 JSON | 4096개 관측/최대8×8 조합, 원 request·BUY identity·cost source 및 원문 해시를 유지한다. 비교 결과는 report_only이고 native policy selector 입력이 아니다. |

외부 원천 계약: 필요한 완료 분봉, 현재 native bid/depth, 원 체결 BUY identity, 설정 비용은 기존 소유자가 이미 수집/동결하는 값이다. 추가 키움 요청·parser·subscription·route 변경은 없다. 미래 호가, 미관측 깊이, 과거 queue fill, 대사되지 않은 실제 broker 비용은 확보된 것으로 간주하지 않는다. 문자열 변수명은 위 실제 생산 필드 그대로 사용하며 mark profit, bid gross, modeled net, 실제 비용 대사를 구분한다.

### 연구 실행 결과와 후속 절차

원 정책 `56457d97a9395b3ccc5832a936936e1e1ff8a4d248f2105e735adedd881d0985`의 SCANNER/PREMARKET 값을 읽었다. soft 임계치 `[-3.5,-3.25,-3.0,-2.75,-2.5]`와 유예 `[0,15,30,45,60]`의25조합을 동일42개 적격 관측에 비교했다. 원 임계치·안전 기준 및 source date는 결과에 봉인했다.

| soft 임계치 | 현재가 순손익 위반 관측 | 전량 visible bid 순손익 위반 관측 |
| --- | ---: | ---: |
| -3.50% | 0 | 0 |
| -3.25% | 0 | 0 |
| -3.00% | 0 | 2 |
| -2.75% | 5 | 6 |
| -2.50% | 7 | 7 |

비용은 동일 frozen 모델로 한 번만 반영하고, bid/VWAP에 들어간 spread를 다시 차감하지 않았다. 위 수치는 독립 거래 수/승률/실현 이익이 아니다. 유예는 각 관측이 최초 touch일 경우의 conditional deadline까지만 계산했다. 드문 AI 평가 사이의 연속 유지·회복, 실제 최초 touch, 체결 가능성 및 지연 효과를 보간하지 않아 `paired_ev_krw=null`, `continuous_coverage_proven=false`다. -3%의2건 차이는 실행 기준 연구의 필요성을 뒷받침하지만, 새 최적값 또는60초의 실제 손실 기여를 입증하지 않는다.

다음 연구도 같은 owner에서 진행한다.

1. **동일 원천 실험 고정:** 기존 native `main_stop_experiment`의 parent/code/operator lock/원천 window·BUY generation·시장 cohort·학습/holdout/embargo·후보 grid를 고정한다. 기준선 원본, 순실행 기준만 바꾼 대조, 임계치·유예 결합 후보를 분리한다. 이번 탐색 결과를 이미 사전등록된 독립 holdout으로 부르지 않는다.
2. **입력 완결성:** 모든 등록 포지션/기회 분모에서 eligible/excluded/unknown을 보존한다. 실제 손절한 거래만 모을 필요는 없다. 완전한 연속 원천을 가진 정상 보유·청산·미청산/censored 경로도 기존 native schema로 비교한다. 새 입력 v2는 실제 capture의 완료 봉을 명시적으로 연결해 학습·재생·provider wire가 동일해야 한다. 원천 없는 normalized tick 표본을 v2 관측 표본으로 조용히 대체하지 않는다.
3. **실행 기준·임계치·유예:** 기존 `main_stop_replay`의 actual evaluation lane, quantity, manual custody, normal exit/terminal, bid depth·가격·시각, 비용과 `holding_vote_exit_models`를 그대로 사용한다. 현재가/전량 bid VWAP의 설정비용 순손익을 비교하되 hard/protect/emergency의 우선순위와 기존 가격·route 검증은 독립 유지한다. 유예의 최초 touch/회복 reset/ADD 이후 즉시 경로/강제 종료를 재생한다. 소프트 임계치와 유예가 서로의 영향을 숨기지 않도록 단일 축 결과와 결합 결과를 함께 낸다.
4. **선정:** 기존 family의 clean boundary와 더 좁은 refresh window, 실제 parent/lock, paired net KRW EV·tail loss·missed upside·censoring·날짜별 holdout 및 비용 grade를 적용한다. 기계 진입 전용 win-rate 예외를 손절 선정에 전용하지 않는다. 실제 비용 누락과 visible depth censor는 null/제외 사유로 보존한다. 누적 시간이나 표본 수만으로 자동 해소됐다고 판단하지 않는다.
5. **마지막 소비:** qualified 후보가 있을 때 기존 publisher→loader/PREOPEN→실제 PID receipt와 원 request/policy/code hash를 대사한다. 이번에는 registry/정책 발행, 운영값 변경, 배포·재기동·주문을 하지 않았다. source2026-10-29 장후/다음 적격 세션의 자연 수용은 기존 체크리스트의 창을 따르되 새 버전이 실제로 배포·선택된 이후 표본만 새 코드의 자연 수용으로 센다.

### 리뷰·검증·성능·제거 대사

- 기준 Git `1756de1d9d7943739d539d5207cc55484185bff5`와 작업 시작 당시 파일 SHA를 기록했다. 다른 세션의 변경이 있는 `sniper_state_handlers.py` 및 observation test는 작업 직전 bytes를 별도로 보존하고 그 이후 본 변경만 patch에 포함했다. 다른 dirty 파일·원 정책·원 실적을 덮어쓰지 않았다.
- 1차 구현 후 source→registry→wire→decode와 보유 consumer를 리뷰했다. forming 봉이 존재하면 완료 봉까지 전부 사라지는 구조를 고쳤다. 중복 완료 봉 파싱을 한 번으로 줄였다. 기존 compatibility reader의 세대 길이 차이를 처리하되 original/new transform 혼합은 거부하고, 새 v2는 v1의 역사 hash 호환 권한을 받지 않게 했다.
- 회귀 검사에서 발견한 limit-up fixture 실패는 보존한 수정 전 predicate에서도 동일하게 재현됐다. 실제 depth ask가 빠진 fixture를 native ask와 일치시키고, 운영의 bid/ask 동일성 guard는 유지했다. 잘못된 호가·sink 실패 negative는 계속 거부한다. 실패 원 로그를 보존했다.
- 영향11 suites **806 PASS** 후 forming suffix/중복 파싱 보완에 대해 entry producer/wire suites를 재검증했다. entry 최종98 PASS이며 비용 결손의 component 상태 보완 후 holding 영향 suites도 다시 통과했다. 최종 결과는 [검증 로그](../../tmp/mcnex-source-repair-20261029/entry-final-tests.log)에 보존한다. compile 및 `git diff --check`, 문서 print-only parser를 함께 확인한다. 실제 provider 호출 및 운영 P5는 미실행이다.
- 격리100회, 원 v1 대비 v2의 동기 request+wire p50 **2.133→2.484ms**, p95 **2.178→2.530ms**, wire **3,599→5,448bytes**였다. 새로운 분봉/호가 조회0회, 최대5봉·기존 요청1회 안에서 처리한다. 운영 end-to-end/provider latency 개선으로 주장하지 않으며, 배포 후 동일 route/call의 p95·timeout·writer lag·큐 실패를 비교한다. 실제 음성/누락 표본을 재시도 폭증으로 보충하지 않는다.
- 제거/대체: 중복 source completeness/결손 사유 조건은 동일 predicate owner로 **consolidated**, 이전 fallback `coverage_exhausted` 오분류 분기는 **removed**. v1 입력은 현재 정책·역사 reader가 소비하므로 **retained**; v2는 explicit native 등록 전 운영 미선택이다. 기존 hard/protect/emergency·vote·quote producer 및 publisher는 **retained**. 새 Python module/worker/CLI/스케줄·병렬 청산 owner는 추가하지 않았다.
- 소스9파일 +552/-107, 테스트6파일 +371/-2, 문서 추가는 이 기존 audit 섹션 하나다. 증가분은 bounded source projection/요청 schema/실패 증거/관측 비교이며, 기존 필수 guards 및 역사 reader를 삭제하지 않는다. 배포본은 아니며 [범위 patch](../../tmp/mcnex-source-repair-20261029/source-repair.patch), [파일별 전후 SHA·규모](../../tmp/mcnex-source-repair-20261029/change-manifest.json), [25조합 연구](../../tmp/mcnex-source-repair-20261029/holding-basis-research.json), [원천 결손 분류](../../tmp/mcnex-source-repair-20261029/coverage-diagnosis.json), [성능 측정](../../tmp/mcnex-source-repair-20261029/performance.json)에 보존했다.

완료 상태: 코드 수정·자체 리뷰·보완·재리뷰·격리 검증과 사건 관측 연구까지. 실제 운용 적정성 개선, 자동 장후 v2 모집단 연결/정책 선정, 새 PID 소비, 정상 응답률 및 전량 청산·비용 경제성은 OPEN이다. 원 과거 응답/호가 결손을 소급 정상화하거나 선택되지 않은 입력을 이미 운영 중이라고 표시하지 않는다.

Project/Calendar 외부 동기화는 실행하지 않았다. 필요 시 사용자 실행 명령은 아래 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 10. 2026-10-29 자동 장후 완료 분봉 연결과 배포 인계

요청 범위는 원천 수리·자동 모집단 연결·선정 경로 검증·배포본 인계다. 이 세션의 live 설정/정책 변경, provider 호출, 주문 및 재기동은0이다. 실제 새 정책의 비교·채택은 원천 부족으로 OPEN이며 코드 검증과 구분한다.

- 원천 owner는 `completed_history.publish/read`다. 새 수집기나 Kiwoom 호출/응답 parser를 추가하지 않고 기존 불변 REST revision에서 동일 item·native session·확인 시각 이전 prefix를 읽는다. outcome용 장후 최종 분봉은 설명 변수로 쓰지 않는다. auth scope는 내부 조회에만 쓰며 출력하지 않는다. 상충 scope, 미래 revision, 전일/진행 분봉, 오래된 suffix는 적격 원천이 아니다.
- `reversal_auxiliary_research_population.attach_completed_contexts`가 원래 outcome-blind 표본 선정 후에 원천을 동결하고, cumulative/changed-scope 연구와 `reversal_auxiliary_tuning.prepare`가 함께 소비한다. `registry.production_request`가 동결 문맥을 실제 wire/응답 검증으로 전달한다. 없는 원천은 두 비교군에서 함께 제외하고 provider 예산을 소모하지 않는다. v1의 입력/결정 권한은 유지한다.
- 날짜별 metadata 조회와 scope index, revision별 호출 내 cache를 사용한다. 한 번에 최대4096개를 읽되 누적 모집단은 분할 처리하므로4097번째 표본부터 영구 생성 불가가 되는 제한을 만들지 않는다. 장중 소비는 순수 투영이며 DB 조회가 없다. 정기 스케줄·예산·timeout을 늘리지 않는다.
- 현재 자동 설정은 REGULAR48scope의 기존 후보이며 변경하지 않았다. PRE/REGULAR/AFTER128scope에 대한 v2 후보 및 기존 seed/max_pairs를 보존한 **설정안**을 별도 배포 자료에 넣었다. 이 설정을 live에 native 등록·승계하지 않으면 새 후보의 자동 비교는 시작되지 않는다. 단순 코드 배포를 정책 채택으로 보고하면 안 된다.

실제 연구는 source2026-10-28의 원래 native campaign85개 표본을 동일하게 사용했다. 원천 적격0/85이며 저장소 부재58, 당시 revision 부재24, suffix/품질 미충족3이다. Native `Store`/`tuning.evaluate`에 같은85개 제외 사유를 전달했고 새 후보의 `comparison_complete=false`를 보존했다. 결론은 `incumbent_preserved_source_gap`이며 no-edge/비용EV0/선정 성공으로 바꾸지 않는다. 엠씨넥스10/29 확인 시각08:05:28.575357에 대해 최초 REST revision 수신08:05:28.679는0.103643초 뒤이므로 확인시점 재생에 소급 삽입하지 않는다. 앞 절의25개 순실행 손절/유예 진단 셀도 연속 보유경로·prospective holdout·실제 비용 증거가 아니므로 runtime 손절 임계치를 바꾸는 선정 근거로 승격하지 않는다. 단일축·operator lock·hard/protect/emergency는 유지한다.

검증과 보완:

- 원 작업본 회귀543PASS. 통합본은 현재 선택 `6d9ed3575cfe28225b187f3251a314cb9fe73a86` 기준으로 별도 index/source tree에 구성했다. 이 과정의534PASS/1FAIL은 compatibility의 기존4세대 고정 테스트였으며, 실제5세대와 원 identifier successor를 함께 보존하도록 보완한 후 production/population83PASS. 누적4097개 배치 회귀를 추가한 population 최종22PASS도 별도 보존한다. 실패 원 로그는 삭제하지 않는다.
- 성공 원천의 publisher→as-of reader→동결 snapshot→native prepare→wire→mock transport→native evaluate가 연결되며, 동일 판단은 개선 없음으로 남는다. 없는 원천은 양쪽 요청0·호출0으로 끝난다. 미래 수정·상충 인증 scope·stale·최소1분봉·다음 세대 및 원본 frozen 계약의 혼합 거부를 검증했다. Mock 응답은 테스트이며 실제 연구 응답이 아니다.
- 자체 리뷰에서 누적 모집단의 단일4096 상한을 수리했다. 배포본에 기존 시장별 source inventory 및 identifier repair를 보존했다. 원 작업본의 다른 변경을 commit에 섞거나 되돌리지 않았다. Native active-parent/독립 준비 reader 검증과 후보/선택 P5는 메인 배포 세션의 통합 후 단계다.

대체/제거: 기존 `production_request`의 문맥 미전달과 `prepare`의 원천 없는 후보 요청 생성을 같은 함수 안에서 보완했다(`consolidated`). 기존 complete predicate의 중복은 앞 절에서 제거했다(`removed`). v1 reader, 실제 비용/손절 selector, operator lock과 안전 경로는 현재 소비가 있어 `retained`다. 배포 기준의 단일 identifier-successor 비교표는 동일 원본 hash를 누적 reviewed-generation 비교로 합쳤으며, 별도 wrapper/worker/스케줄은0이다. 새 소스 파일은0, 기존 소스 함수2개와 호출 연결을 추가했다. 기존 장후 단일축 selector를 공동 민감도 진단으로 대체하지 않았다.

기존 `HoldingProfitExitSourceContractRepair`가 다음을 계속 소유한다: 메인 세션에서 코드 통합·정책 인계·P5·실제 PID 소비, 승인된 장후 후보 설정의 native 승계, source2026-10-29 정규 장후20:10 이후 새 적격 분봉/paired 응답과 target2026-10-30 PREOPEN07:35/Main07:55~08:05 소비. 원천가용성이 확인되지 않은 표본은 다음 날로 미뤄 정상 처리하지 않고 원 날짜의 제외 상태를 유지한다. RFHIC49558의 기존 BUY 결손과 이번 역사 분봉 결손, 신규 생산자 결함은 서로 다른 분모로 기록한다. 아직 후보별 실제 경제성 개선이나 자연 수용을 주장하지 않는다.

[배포 인계 지시문 및 검증 자료](../../data/audit/holding_source_repair/2026-10-29/HANDOFF.md). 원본과 연구 실패 시도는 `tmp/mcnex-source-repair-20261029` 및 `tmp/mcnex-postclose-completion-20261029`에 보존한다. 외부 Project/Calendar 동기화는 실행하지 않았으며 기존 표준 사용자 명령을 유지한다.

## 11. 적격 원천 0건 원인 재분류와 자동 선정 정체 수리 — 2026-10-29

Owner: `HoldingProfitExitSourceContractRepair`. 기준은 §10의 `c709099a04c160662e065f6d2e64bd043400b4f0`이며, 이번 범위는 source-only 수리·격리 검증·배포 인계다. Main 재기동, live 설정·정책, provider/주문 변경은 수행하지 않았다. [후속 배포 인계 및 전체 증거](../../data/audit/holding_source_repair/2026-10-29/source-gap-v2/HANDOFF.md).

### 원인과 역사 결손

기존 85개 표본의 적격0은 유지된다. 그러나 이를 전체 모집단의 원천0 또는 손절 실적 축적 필요로 해석한 것은 잘못이었다. REST minute history는 기존 요청 때만 생산되며 **모든 확인 신호의 생산자가 아니다**. §10의 범위 주장을 이 조사로 정정한다.

| 기존85건 | 수 | 원천 기준 분류 |
| --- | ---: | --- |
| 이력 DB 부재 | 58 | 9/29·30,10/2·6·7·8. 저장소에 해당 producer가 처음 추가된 commit은10/9 `9dc8ac91e`. 해당 native revision은 현재 보존 원천에 없다. |
| 같은 item 수집 부재 | 9 | 보존 DB의 전체 revision에 item이 없다. 새 날의 수집 결함과 동일 사건으로 합산하지 않는다. |
| 다른 session에서 뒤늦게 수신 | 12 | REGULAR 확인 뒤 AFTER/CLOSED에 수집. session alias 결함이 아니며 장후 outcome 자료를 당시 feature로 사용할 수 없다. |
| 같은 session 첫 수신이 확인 이후 | 3 | 당시 정보 가용성 위반이므로 소급 사용 불가. |
| 최신 완료 suffix가 오래됨 | 3 | 10/21 11:06~11:14 확인에10:36까지의 봉만 존재. 결손 구간을 합성하지 않는다. |

합계85. **보존된 native history에서 복구 가능한 당시 입력은0**이다. 사후 Kiwoom 조회로 과거 수신 시각·당시 revision을 만들 수 없다. 다만 DB 부재만으로 다른 모든 원본 archive까지 소실되었다고 단정하지 않는다. 대체 당시 원본이 발견되면 native 원천·item/session·수신 시각·hash를 검증한 새 세대로만 복원한다. 이 불확실성은 역사 결손 진단이며 신규 적격 원천의 연구를 막지 않는다.

엠씨넥스10/29 확인08:05:28.575357과 첫 REST revision08:05:28.679는 서로 다른 시각이다. 실제 AI 단계에는 완료 분봉이 있었으나 확인 시각 replay에는 없었다. 이 자료를 확인 이전으로 옮기거나 임의0.1초 유예로 적격화하지 않는다. 실제 AI 단계 연구를 확장하려면 그 단계의 동결 입력·cutoff·원래 capture 계보를 별도로 사용해야 한다.

### 재현된 구조 결함과 수리

1. **원천 검사 전 표본 선정**: 결손의 낮은 hash 순위가 유효 표본의 연구 슬롯을 차지했다. `reversal_auxiliary_tuning.prepare`를 원천 적격성 확인→기존 seed/scope round-robin→동일 양측 request 순서로 변경했다. outcome으로 source를 고르지 않는다. 개발·충돌 제외, 예산, 기존 selector 경제성/유지 조건은 그대로다.
2. **빈 campaign 영구 재사용**: 같은 machine/config/code 아래 original revision 복원이 있어도 준비 cache key가 바뀌지 않았다. native revision hash/scope/available 집합의 content generation을 cache에 결합했다. 없는 DB와 나중에 복원된 DB는 서로 다른 세대다. 미래에 수신된 자료는 generation이 바뀌어도 계속 제외한다.
3. **쓰기 파일 한도를 읽기 전체 차단에 재사용**: 10/12 DB134,332,416byte와10/13 DB134,299,648byte가128MiB를 넘어서 cumulative reader가 `history_causal_database_unbounded`로 중단됐다. 이후 날짜가 늘어도 같은 과거 파일 때문에 반복되는 결함이다. writer의128MiB/범위 제한은 유지하고, reader는 indexed metadata의 실제 읽기량을 같은 한도 안에서 검사한다. 기존 named revision·원시 행 hash 검증 및5봉 projection을 유지했다.
4. **전체 제외 근거와 성능**: 기존 comparison store에서256개 단위 source qualification/checkpoint를 재사용한다. gap preview는256개이며 전체 제외는 동일 store의 hash-bound chunk manifest로 보존하고 campaign intake/evaluation까지 전달한다. source/date/code 세대가 달라지면 재검증하고 source가 검사 도중 바뀌면 campaign 발행을 중단한다. 별도 DB·수집기·실시간 history 조회·provider 호출은 추가하지 않았다.

### 실제 원천 재검증

- 최신 native machine `fcd5ad61b9a6d4a8bd7af9a432955af4e2f334cd21f85c0a5b28b784df3b46ab`의 원41950 point를 확인했다. 기존85개 모두 이 원천 집합에 존재한다. 기존 campaign machine `3e849b7c…`와 최신 machine 세대는 구분해 보존했다.
- 기존48 REGULAR scope: 현재 확인6313개 중 source 적격1. 10/26 HPSP036930_AL, key `17b43f431ee0e2ece6c02c0e27d943c27d3474a812b2405c3f84b11286683fd5`. 기존85 표본에서 누락됐다.
- 제안128scope: 현재 확인10596개 중 source 적격148(PRE84/REGULAR1/AFTER63), DB 부재8156/당시 revision 부재1915/suffix·품질 결손377. 적격은6개 날짜(10/15·22·23·26·27·28)에 존재한다. **148은 source 적격 수이며 provider 비교 완료·선정된 정책 수가 아니다.**
- 148개를 native materializer→v2 registry request까지 검증했다. original object와 frozen source·request hash는 private qualification store 및 증거 JSON에 보존했다. 기존85 원본, 실패 시도와 앞선 배포본은 변경하지 않았다.
- 같은10596개 첫 qualification6.929초/동일 세대 재사용0.509초, process peak RSS136200KiB. DB physical bytes/실제 Main latency는 미측정. 둘 다 같은 source census이며 장중 성능 개선 주장으로 사용하지 않는다.

### 리뷰·대체·검증 및 인계

`implementation → self review → fixes → re-review`에서 빈 cache 영구화, 오래된 DB 전체 실패, v1 cache의 불필요한 재조회, 제외 근거의 무한 inline 증가와 point/date cache 결합을 보완했다. 실제 범위3개 기존 source owner·기존 test1개를 확장했고 새 module/worker/entrypoint는 없다. 기존 sample-first exclusion은 **replaced**, 물리 DB 크기 reader 차단은 **removed**, 동일 writer 한도/기존 source reader/하드 안전장치/v1 입력은 **retained**다. 현 배포본의 모든 기존 원천·매수/보유/손절 보완은 선행c709에 계속 포함된다.

원 코드에서 starved/cached-zero 회귀2건 실패를 재현했다. 수리 후 해당 시험, 없는·미래·stale·다른 scope·conflict·복원 세대·4097 chunk·300개 제외 manifest·native paired request/evaluate를 검증했다. 198개 관련 시험 통과 후 최종 보완한 population/tuning 및 날짜 음성 시험을 재검증했다. 최종 수/로그·compile·ruff·diff·문서 검증과 source/test/doc 증감은 배포 manifest가 소유한다.

의존성 disposition: raw/native history·machine calculation·원085 campaign은 `reuse/read-only revalidate`; 변경된 auxiliary preparation/source qualification/campaign/request/evaluation은 native owner로 `regenerate`; report/policy publisher→PREOPEN→PID는 그 결과에 따라 재준비·검증한다. 기존 성공한 다른 family 계산과 cleanup을 재실행하지 않는다. 원 연구 설정128scope·seed·max_pairs50·예산안은 source-code contract가 같으므로 그대로 인계하되 live config CAS/진행 writer를 다시 확인한다. source148개 발견만으로 후보를 live 채택하지 않는다.

현재 checklist의 동일 owner와 source10/29 장후→10/30 PREOPEN/Main 창을 유지한다. 실제 자동 campaign의 적격 수/양측 완료/선정·incumbent 보존 사유, native 정책 인계·P5·배포 후 exact PID/observer/health, 새 BUY→signal→terminal→assembler와 비용 후 경제성은 각각 별도 수용이다. 일정 변경은 native calendar/schedule에 맞춰 인계 세션이 갱신한다.
