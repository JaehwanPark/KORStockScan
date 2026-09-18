# 실제 AVG_DOWN 체결 후 분할 튜닝·최종 리뷰와 다음 장후 단위 — 2026-09-18

## 판단·승인 범위

사용자 요청에 따라 scale-in 체결 조건부 평가를 재리뷰·보완·검증하고 commit/push/immutable source 배포 및 불필요한 과거 산출물 삭제를 수행한다. 다음 단위 `entry_split_order_plan`은 코드·정책·원천·평가 결과를 변경하거나 재실행하지 않고 분석한다. 기존 병행 scanner/fact 변경과 root의 관련 없는 변경을 보존한다. Source 선택, PREOPEN 선택, actual PID 소비, 자연 체결 및 비용 차감 경제성은 각각 다른 수락 단계다.

최신 기준은 과거9/5 inventory가 아니라 selected source `53b0264c3`의 `deploy/run_threshold_cycle_postclose.sh`와 source-date9/17 native receipts다. 당일9/18 사용자 휴장·미적재 지시를 보존하며 다음 사용자 예정 적용일은9/21이다. 과거 원천을9/18 자료로 바꾸거나 calendar/cron/env/provider/주문/guard를 수정하지 않는다. 실행 owner는 현행 체크리스트의 `KiwoomCommonHealthOpportunityCostAcceptance0917` 하나를 유지한다.

## 실제 물타기 체결을 가정하면 무엇을 평가하는가

이 튜닝은 **AVG_DOWN을 할지, 얼마나 추가할지**가 아니라, 기존 가격·수량·예산으로 허용된 AVG_DOWN 주문을 **어느 가격 간격과 수량 비중의 두 leg로 실행할지** 평가한다. AVG_DOWN 판단은 Main 공통 반등·AI·기존 주문/손절 guard가 소유한다. 미진입 기회비용의 BLOCK/RECHECK/VETO 모집단은 이 분모에 넣지 않는다.

1. 기존 fact-sync가 실제 execution/quote/terminal의 작은 signed projection을 보존하고 exact-date consumer-ready receipt를 발행한다. 평가기는 DB HoldingAddHistory에서 Main/default custody·SCALPING/SCALP·AVG_DOWN·EXECUTED/receipt_confirmed 실제 체결을 read-only 조회한다. 최근20 report date, clean baseline 및 실제 order/position lineage를 유지한다. 실제 체결0, 분할 비대상, source 부재는 서로 다른 상태다.
2. 지정가·원 요청량2주 이상이어야 분할 대상이다. 실제 full fill과 COMPLETED terminal clock/가격/유효 profit_rate, receipt provenance 및 ADD lot을 동일 시도에 결합한다. 미청산은 조건부 maturity 대기이며, COMPLETED인데 terminal clock/비용 원천이 없는 것은 source gap이다. 단순 주문 접수/일부 체결만으로 완료 순익을 만들지 않는다.
3. 원 주문 시점의 기준가격·총수량·예산·route·TTL을 고정한다. 직후 최대180초의 독립 시장가격 및 유효 BBO/depth를 쓰되 후속 ADD/terminal 경계에서 관측을 끝낸다. Own fill은 시장경로를 대신하지 않는다. 기존 WS receipt의 venue/item·epoch·sequence·관측 clock을 검증한다. 현재가가 지정가를 만졌다는 사실만으로 체결을 가정하지 않는다.
4. 같은 경로에서 actual incumbent와 기존 70/30 또는50/50(0/−0.3%),60/40(0/−0.8%) 등 기존 grid를 재생한다. 유효 ask가 leg 지정가 이하이고 관측 잔량이 leg 수량을 감당해야 modeled fill을 인정한다. 같은 quote 잔량을 두 leg에서 재사용하지 않는다. 관측이 TTL 전에 끝나 미체결 여부를 모르면 censored/null이다. Candidate의 일부 leg 미체결은 충분한 관측으로 판별된 경우에만 모델 순익에 반영한다.
5. Incumbent 모델 체결량이 실제 체결량과 같고 평균가격 오차가1tick 이내여야 비교 모델을 인정한다. 공통 지원 cohort에서 후보−incumbent 비용모델 순익, 고정 notional 기준 weighted ΔEV, 일별 Δ순익, 참여율·취소·tail 및 한 tick 불리한 stress를 계산한다. 비용은 shared fixed comparison model이며 `broker_cost_reconciled=false`다. 전체 포지션 실제 profit_rate를 ADD의 증분 이익이라고 주장하지 않는다.
6. 날짜·episode와 늦은 outcome를 분리해 calibration을 최신 미사용2일 holdout보다 앞에 둔다. Calibration에서 기존 grid의 후보1개를 고르고 holdout에서 한 번만 검증한다. 실패 후 차순위 후보를 같은 holdout로 재검증하지 않는다. Calibration과 holdout 각각3개 paired sample/2일, coverage80%, modeled fill participation70%, weighted ΔEV≥+0.10%, p10 Δ≥−0.30%p, 평균 일별 Δ순익>0 및 stress 개선을 요구한다. 기준을 충족해도 작은 표본의 통계적 확실성이나 실제 수익을 보장하지 않는다.
7. 동일 실행계획이면 incumbent_preserved다. 새로운 ready outcome/revision만 grid를 열며 무체결·비대상·미성숙·변경없음에서는 비싼 raw/replay를 열지 않는다. 평가 후 immutable snapshot, consumed holdout 이력과 cursor를 보존하고 policy→hash-bound report 순서로 발행한다.

수식은 `ΔEV%=100×Σ(후보 modeled net−incumbent modeled net)/Σ(원 기준가격×원 요청수량)`이다. 일별 Δ순익은 이 paired 모델 차이를 원 source day별로 합산한다. 무관측일을 순익0으로 보충하지 않는다.

**계산 예시이며 실제 성과가 아니다.** 원 지정가10,000원·4주·동일 terminal10,100원, 후보2주10,000원+2주9,970원이라고 가정한다. 두 leg의 TTL 내 독립 호가/잔량이 체결을 지지하고 incumbent4주 모델이 actual receipt와 맞으면, 비용률0.0023 기준 incumbent 모델 순익307원, 후보367원, Δ순익60원·ΔEV+0.15%다. 후보 평균가격9,985원에1tick(10원) 불리한 stress를 주면327원/Δ20원이다. 실제 잔량·terminal lot·holdout가 없으면 이 숫자를 산출/승격 근거로 쓸 수 없다. 한 시도 또는 하루의 양수 결과만으로 새 정책은 활성화되지 않는다.

## 장중 런타임으로의 반영

Publisher→Daily calibration envelope→EV/기존 deterministic·AI·same-stage/override guard→PREOPEN dated policy/env→실제 Main loader→AVG_DOWN 정상 주문 경로로 연결된다. 파일 생성이나 source 배포가 policy enabled 또는 actual PID 소비를 뜻하지 않는다.

`src/engine/sniper_state_handlers.py`의 실제 ADD submit 경로는 기존 action/가격·AI·paused-buy 검사 후 `apply_scale_in_split_order_policy`를 호출한다. Loader는 ENABLED/FILE/VERSION, v4 evidence·holdout chronology·source age·effective_date 및 해당 bucket을 검사한다. 적용 가능하면 가격/수량 leg shape만 바꾸고 최종 수량 cap·현금·broker/receipt/pending·stale/conflict·stop SELL 우선 등 기존 guard를 다시 거친다. 미승인/시장가/qty1/만료/부재 bucket은 원 주문을 보존한다. 장후작업이 새 물타기 주문을 실행하는 것은 아니다.

현재 source9/17의 actual census5/COMPLETED5, qty1 제외4와 frozen market-like 제외4는 중복된 집계다. 합집합5/분할 대상0/paired0이며 COMPLETED2건은 terminal clock 결손이다. 상태는 `skipped_no_applicable_fill`; EV·일별 Δ순익·실제 ADD 증분 순익은null이다. Effective9/21 정책은 `available=true/split_enabled=false`, `incumbent_unsplit_base_order`이며 positive split 후보가 아니다. 실제 적용은 다음 정상 PREOPEN/PID 및 자연 eligible fill/COMPLETED 증거로 확인한다.

## 이번 재리뷰·보완·삭제

새 결함1건을 재현했다. `_partition_outcomes`가 consumed ledger의 **보고서 날짜≤최신 fill source date**만 읽어,7/6~7/7 체결을7/8에 평가해 사용한 holdout 이력을 누락했다. 이후 source revision/재평가에서 같은 holdout를 다시 쓸 수 있었다. 뒤늦게 발행된 canonical dated ledger도 읽도록 해당 필터만 제거했다. 모든 사용 이력을 보존하는 보수적 재사용 차단이며 grid·floor·비용·실행 authority를 바꾸지 않는다. 기존 테스트 파일에 late-evaluation 회귀1개를 추가했다. 수정 전 실제 FAIL, 수정 후 producer/PREOPEN/wrapper434PASS를 확인했다. 기존 구현을 다시 작성하거나 신규 module/collector를 추가하지 않았다.

재리뷰는 actual inventory/source→모델/partition→policy→PREOPEN→실제 ADD consumer와 누락/지연·self comparison·revision·custody·기존 safety 경계를 대상으로 했다. In-scope 새 미해결 finding0과 다른 family의 구조적/경제성 미해결은 분리한다. 현재 분할 대상0이어서 이번 수정이 현재 report/policy의 경제성 값을 바꾸지 않는다. 불필요한 report 재생성 대신 배포 source에서 현재 census/state 및 policy/summary SHA를 read-only 검증한다.

삭제는 `tmp/scale-in-final-review-20260918/cleanup.json`: 최근20일 밖의 참조되지 않는 과거 Markdown30개/21,354bytes다. 같은 JSON51개·policy51개·최근 보고서·reuse sidecars·lock·actual custody·outcome revision·consumed holdout·immutable/rollback 증거와 다음 단위 원본을 보존했다. 삭제 전 활성 family worker0과 source lock을 확인했고 보호129개 byte SHA·최근20일 날짜 목록 불변을 검증했다. 날짜 JSON을 단순 삭제하면 report-date window와 holdout 이력을 바꿀 수 있어 삭제하지 않았다.

## 바로 다음 작업과 실제 실행 결과 — 코드변경금지

Selected wrapper에서 fact-sync→scale-in→**entry_split_order_plan**→AI quality 원천 준비→Daily/AI correction/cumulative 순서다. 폐기된 standalone scanner lookup/Opening Rotation을 다음 작업으로 세지 않는다. Entry split은 처음 BUY의 초기 총수량×leg shape를 평가하는 owner이고 AVG_DOWN 분모와 다르다.

Native request/result/review1020은 source9/17,9/18 00:13:36.979 요청~00:14:34.763 완료/exit0이다. 요청~완료 약57.8초와 wrapper command 계측34.961초는 범위가 다르다. Frozen generation/report-policy binding은 유효하며 source warning도 tuning_input_allowed=true/hard gap0이다. Blanket source-quality 차단으로 설명하지 않는다.

| context | real sample / split 완료 관측 | 전체 real bucket 평균 % | split 완료 관측 평균 % | 현재 판단 |
| --- | ---: | ---: | ---: | --- |
| balanced_normal | 40 / 26 | −0.6835 | −0.6835 | mature parent 경제성 반대, 후보 보류 |
| guarded_or_stale | 110 / 81 | −0.4103 | −0.4103 | mature parent 경제성 반대, 후보 보류 |
| passive_wide_or_weak | 185 / 50 | −0.0001 | −0.1857 | 정확 child3건+0.7853% seed만 진단 통과, 최종 발행 차단 |
| urgent_tight_spread | 2 / 1 | +0.6200 | +0.6200 | 표본 부족 |

위 값은 observational 평균이며 incumbent 대비 paired ΔEV/증분 일별 순익이 아니다. Passive의 전체 bucket/실제 split/정확 child는 다른 모집단이다. Positive child는 qty-clipped two-leg·first weight20·probe fill-clamped BBO3건이며 전체 일반 split 효과로 확장할 수 없다. Sim429,200건과 bucket별 split 완료 관측 합158건도 합쳐 real execution quality 표본으로 세지 않는다.

당일 atomic sizing 관측3/invalid3/valid0, real submit with/missing plan0, selection_blocked=true다. Four-arm source receipt0/eligible0/complete0/calibration0/holdout0, EV·순익·join coverage는null이다. 최종 candidate0/explicit bucket0/seed false/EV validated false/runtime apply false이며 missing bucket은 keep_original_order다. 일부 child의 `candidate_passed=true`/seed 진단 PASS를 최종 publish PASS로 해석하지 않는다.

기존 튜닝 producer `scalping/strategy_owner_replay`는 frozen price-ready opportunity를 source-bound 네 arm(기존/후보 quantity×기존/후보 leg)으로 재생하고 signed receipt를 발행한다. Evaluator는 동일 시도·exit/비용·quantity/capital·route/session·hash와 chronological calibration/holdout를 검사한다. 현행 complete30/coverage80%/후보 cost-adjusted EV0.1%/participation 감소≤5%와 frequency·capital efficiency·tail 비열화 조건을 보존한다. 기존 baseline 사용과 challenger promotion은 별개다. Native raw_plan_rows0/completed0/maturity_waiting0과 atomic invalid3은 같은 분모가 아니다.

## 기다리면 달라질 것과 현재 결손

| 분류 | 현재 증거 | 다음 조치와 closure |
| --- | --- | --- |
| 조건부 성숙/축적 | post-sell pending223, urgent real2/split 완료1 | 유효 source/terminal horizon가 이미 존재하는 건만 자연 완료/축적을 관찰. censored·irrecoverable 결손을 먼저 제외하며223건 전부 완료를 약속하지 않는다. ETA=null |
| 현재 source/contract 차단 | atomic valid0, native eligible price-ready plan0, four-arm0 | 기존 emitter→decoder→strategy_owner_replay→evaluator에서 다음 자연 유효 plan1건의 recipe/qty/hash/route→exact signed receipt→consumer complete 증가를 확인. 시간만으로 과거 frozen BBO/qty/비용을 복원할 수 없다 |
| 상세 원인 미확정 | compact 원본에는 invalid3의 구체 blocker/recipe가 없음 | plan_block의 정상 fail-closed와 malformed plan을 구분해야 한다. 코드가 plan과 plan_block을 invalid 진단에 포함하므로 invalid3만으로 emitter 결함3건이라고 확정하지 않는다. 이미 유지된 compact/native evidence를 우선 대조;5.7GB raw 전체 재스캔은 이번 분석에서 생략 |
| 측정된 관측 경제성 한계 | parent 일부 음수, positive exact child3건, paired four-arm 없음 | 표본 증가만으로 ΔEV가 양수가 되지는 않는다. 같은 historical seed를 새 holdout로 재사용하지 않으며 원 분모와 형태·source version을 유지 |
| 적용/실제 성과 미완료 | disabled/not-selected policy, actual consumption 미입증 | 정상 dated PREOPEN→actual PID/version→자연 full/partial fill→COMPLETED 실제 비용 원장을 확인. Model ΔEV와 actual 증분 이익은 별도로 기록 |

현재 source blocker의 직접 owner는 existing entry execution sizing/price-ready emitter·native decoder·strategy_owner_replay·entry split evaluator다. 구조적 불가능을 단정하는 데 필요한 invalid3의 세부 source 증거는 아직 없다. 구현 경로가 존재한다는 사실도 자연 유입0을 해소했다는 증거는 아니다. 다음 유효 source receipt가 도달하기 전에는 sample floor 완화나 후보 확장이 첫 조치가 아니다.

Daily 후속 native1023의 rolling real completed18/loss4·sim22 및 same-day projection3518은 이 split 후보의 인과 개선값이 아니다. AI correction은19 families 중 review required0로 skipped_no_review_candidates/추가 provider 호출0이다. OFF envelope 전달 가능성(`runtime_apply_eligible_now`)과 positive split activation을 구분한다. Source9/17 native 전체chain의 blocked_native_resource_guard와 다른 family의 strict 결손은 유지되며 이 리뷰로 전체 DONE/경제성 PASS를 발행하지 않는다.

## 최종 증거·남은 수락

Commit/push·selected immutable root/router와 source tests, 보호 SHA·현재 census/handoff는 `tmp/scale-in-final-review-20260918/{validation,deployment,cleanup,scope-verifier}.json`을 따른다. 추가 trading/provider suite·다음 단위 source 수정/재실행·원시5.7GB/537MB 전체 scan·전체 장후 재실행·service/Main restart·orders·수동 env/guard·외부 sync는 수행하지 않았다. 잔여 위험은 작은 실제 유입, unreconciled broker 비용, 과거 source 결손, 정상 PREOPEN/PID 및 자연 rolling/cumulative 경제성 미완료다.
