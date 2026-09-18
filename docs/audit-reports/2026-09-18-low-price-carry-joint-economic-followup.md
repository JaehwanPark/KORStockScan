# 2026-09-18 저가주 carry·공동 목적 후보 선택 후속 보완

Owner: `LowPriceExpandedResearchRepair0918`. 사용자 재승인: carry/후보 선택 보완·반복 코드 리뷰/수정·검증, commit/push·소스 배포 및 장후 결과 갱신. [LP0–LP6 계획](../proposals/low-price-two-leg-expanded-candidate-economic-logic-improvement-plan-2026-09-18.md)의 후속이며 새 OPEN owner가 아니다. 기존 동결 정책·원 보고서·ledger·보유 custody·quantity/cost/grid/sample/provider/hard safety를 보존한다.

## 앞선 설명 정정과 실제 구조

[이전 distinct review](2026-09-18-low-price-distinct-economic-review.md)의 native 모델 성숙2·동시개선0·미확정55는 그 모델의 유효한 결과 이력이다. 그러나 native `_advance_candidate_day`는 HELD 이후 mark/exposure만 갱신하므로 같은 과거 입력을 반복해도 해당 carry가 해소되지 않는다. 55개 중 baseline43개는 holdout 시작 이전 보유로 진입이 막혔다. 이 구조의0건을 시장의 no-edge나 수익 개선 완료로 해석하지 않는다.

대화에서 EV 중심 순위라고 설명했던 부분은 잘못이었다. 실제 `_retain_calibration_candidate`는 **일별 순익 → robust EV → EV → 완료 수** 순서였으며 기존 1차 기준은 보존한다. 이번에는 baseline과 calibration에서 EV·일별 순익이 모두 개선된 distinct 후보들을 우선 pool로 분리하고 그 안에서 기존 순위를 적용한다. 우선 pool이 없으면 best distinct는 진단 후보로 남긴다. holdout을 보고 pool/후보를 바꾸지 않는다. 이 방식은 모든 grid를 확대하거나 순위식을 불필요하게 다시 쓰지 않고 목적의 두 지표를 선택 단계에 반영한다.

## 원 청산 owner 확인과 연구 모델의 경계

확인한 runtime owner는 `src/trading/order/regular_two_leg_machine.py`의 `_submit_target`, `_roll_date`, `_reconcile_target`, `_run_once_impl`과 `src/trading/order/profit_stagnation_owners.py`의 `episode_leg`이다. 원 목표가는 실제 fill price에서 policy target ticks로 계산하며 보유가 있으면 날짜가 바뀌어도 custody/state를 초기화하지 않는다. broker target의 terminal absence와 실제 보유는 HELD로 남고 별도 owner/실제 주문·체결 근거가 필요하다. 원 목표가 유지 규칙이 있다는 사실은 다음 날 broker 주문 복구·실체결 성공을 보장하지 않는다. API 요청/parser/계좌/주문/WS 프로토콜은 수정하지 않았다.

따라서 기존 native replay를 실제 청산처럼 고쳐 쓰지 않았다. 기존 연구 module 안의 명시적 cached-only 옵션 `--review-carry-target-continuation`에서만 `low_price_original_target_continuation_price_touch_cf_v1` 모델을 사용한다. **원 target이 다음 정규장부터 유효하다는 가정**으로 기존 목표가의 첫 관측 도달을 단위 price-touch CF 완료로 분류한다. 원 목표가/수수료/거래창/두 다리/수량 의미를 유지하고 손절·강제 종가청산·새 target을 만들지 않는다. 두 다리는 각각 완료될 수 있고 전부 종료하면 다음 날의 진입이 가능해진다. 보수적으로 carry 종료일 전체의 신규 진입은 막는다.

관측은 해당 날짜09:00부터 이어지는 정규장 분봉 prefix만 사용한다. 처음부터 늦게 시작하거나 시간 공백 뒤/aftermarket에서 도달한 값은 빌려 쓰지 않는다. 도달이 입증되지 않은 carry는 그대로 unresolved다. 그 결과도 임의0으로 바꾸지 않는다. 원 cache에 든 episode를 변경하지 않고 각 구간 경계의 상태를 봉인해 미래 결과가 과거 calibration/half를 바꾸지 않는다.

## 손익 구간·표본·권한 연결

holdout 이전 진입 다리가 holdout에서 CF 완료되면 **청산 날짜의 구간에 순익·완료 notional·EV를 한 번만** 반영한다. carry-in 완료 ledger의 entry date/signal/leg index/target timestamp와 원 비용을 보존한다. 새로운 signal/attempt 수를 만들지 않는다. 완료 분모에는 해당 구간에 완료한 carry-in을 포함하고 attempted-notional 수익률/시도·완료비율·episode 평균/노출은 entry-cohort 진단으로 구분한다. EV 계산은 표시용 원 단위 반올림 전에 수행하며 cashflow 금액은 기존 표시 규칙으로 반올림한다.

같은 original-target-continuation 모델 아래 baseline과 후보를 함께 평가하므로 모델 의미 변경 자체를 정책 개선으로 세지 않는다. 기존 calibration/holdout/full sample·carry risk guards와 source 품질을 보존한다. 이미 본9/17 holdout은 탐색 결과이며 독립 미래 검증이 아니다. checkpoint는 source content·원 baseline parameters/hash·cost·native grid·선택 목적·CF/native replay contract·implementation hash에 연결한다. native day checkpoint는 mark-only transition이므로 CF와 공유하지 않으며 기존 profile checkpoint만 분리 재사용한다. 별도 성능 guard/cache module/service를 추가하지 않았다.

paired economics의 `live_replay_supported=false`를 CF 모델에 부여했다. prospective promotion과 native auto-expansion policy의 새 추천 검증이 이 모델을 거부한다. cached review는 추천 notifier/native publisher/seed/order를 호출하지 않는다. 기존 이미 동결된 v6 정책 읽기는 보존한다. 따라서 CF 양수가 나오더라도 새 live enrollment 또는 현재 정책 변경이 아니다.

## 반복 리뷰·검증

초기 465PASS·7FAIL 중6개는 baseline calibration 비교 추가에 따른 oracle 호출 순서 기대값이었고 후보 검증의 holdout 비참조 검사를 보존하여 수정했다. 나머지1개는 시험의 joint candidate가 baseline과 같은 값이어서 fixture를 실제 distinct 값으로 고쳤다. 재검증 관련4 suite475PASS. 후속 carry/현금흐름/반올림/정규장·공백/목표가·custody/후보 고정/CF 승격 거부 회귀17PASS(중복 포함)이다. 리뷰에서 native day cache가 외부 CF transition을 덮어쓸 가능성을 확인해 CF는 분리된 profile checkpoint 경로만 사용하도록 보완했다.

실제 동결9/18 정책 readonly load3개 PASS; policy hash `5cd93e2f3520ac0a420a10fc022b523036736e044d1ae9b9961df6ba8cdb89cc` 불변. 로그/보호 hash/검증 receipt는 `tmp/low-price-carry-joint-economic-20260918/`에 둔다. pytest 실행을 합산하지 않는다. 원 API·provider·주문·전체1,020/전체 장후chain·계좌 수집·Trading restart·외부sync는 실행하지 않는다. 관련 compile·diff·링크·단일 owner·print-only parser로 닫는다.

## 최신 결과·배포

기존 캐시64개만 한 번 재평가하며 전체1,020개/추가 시장 조회는 하지 않는다. [사전 고정 manifest](../../data/report/postclose_research_successor_20260917_20260918/carry_joint_economic_review_20260918/checkpoints/review_manifest.json)와 [최종 비교 JSON](../../data/report/postclose_research_successor_20260917_20260918/carry_joint_economic_review_20260918/low_price_existing_logic_full_comparison_2026-09-17.json)이 해당 모델의 경제성 근거다. 최종 수치·소스 배포·직접 reader 소비는 실행 종료 후 아래 receipt에 기록한다.

## 잔여 closure

CF 가정의 broker recovery/queue/quantity/partial-fill·실제 terminal·비용 근거, 미사용 미래 검증 및 과거 widget/cash/inventory/reservation/same-stage joint source는 별개 OPEN이다. 기존 target rule 검토만으로 이 결손을 닫지 않는다. equivalent 보존 원천이 없으면 과거 joint EV/net은 null이다. 자연/실제 acceptance는 현재 단일 checklist owner로 유지한다.

## 제한 재평가 최종 판정

64개 모두 종료, 새 checkpoint hit0/miss64,392.461초(6분32초), 신규API0. CF/native를 섞지 않고 동일 CF에서 비교했다. 성숙 distinct 비교18개·holdout EV/일별 순익 동시 양수차12개·미청산/terminal미확정27개·표본부족19개다. 12개 중10개는 calibration에서도 동시 개선된 우선 pool에서 선택됐고, NHN 점심/팬오션 오전2개는 calibration joint가 미확정이거나 없었던 진단 후보다. 후자2개를 calibration+holdout 일관 개선으로 세지 않는다. TYM 점심은 일별 차+0.0125원으로 매우 작아 실질 개선 대표값으로 내세우지 않는다. independent future/live 경제성 확인은12개 모두 아니다.

| calibration·holdout 일관 CF 비교의 예 | 기존 → 후보 EV | 기존 → 후보 일별 순익 | 변경 |
| --- | --- | --- | --- |
| 롯데케미칼 점심 | 0.094617% → 0.419234% | 32.790625 → 145.290625원(+112.5) | 원 native target2→4 ticks만 변경 |
| 두산에너빌리티 auto 점심 | 0.002423% → 0.234846% | 1.042500 → 101.042500원(+100) | target2→4 ticks만 변경 |
| 영원무역 auto 오전후반 | 0.044223% → 0.316784% | 42.332500 → 289.679375원(+247.346875) | scan/lookback/near-low/target 변경 |

위는 unit-per-leg CF 금액이며 실제10주 주문 순익으로 환산하지 않는다. 순수 target 변경2건은 비용 대비 target margin 보완(H1)을 추가 검증할 구체적 근거다. 실제 체결빈도·overnight target 재개·partial quantity·queue·비용 실현 입력 없이 매매에 적용하지 않는다. 여러 profile의 금액은 기회/자본이 겹치므로 합산하지 않는다. 원 native 모델의2비교/0개선은 역사 결과로 보존하며 CF 모델의18/12를 그 모델의 성과로 바꿔 쓰지 않는다.

양측 정책의 최종 full episode에서 holdout 완료/carry-in ledger·순익·notional·EV·다리별 기여를 독립 재구성해64개 모두 일치했다. paired economics도64개 동일하며 live replay 지원false를 확인했다. [최신 장후 기계 판정](../../data/report/postclose_research_successor_20260917_20260918/carry_joint_economic_review_20260918/low_price_full_research_result_review_2026-09-17.json)은 native 원 판정과 조건부CF/10개 일관 개선을 구분한다. 원 보고서2개/동결policy SHA 불변이다. 같은 원천 재실행은 하지 않는다.

대표 target2→4 비교는 완료 빈도가 유지돼도 노출이 증가했다. 롯데케미칼 holdout은 signal5·완료9를 유지하면서 entry-cohort exposure16→239bars, worst filled MAE−0.173913%→−1.391304%였다. 두산 auto 점심은 signal4·완료8 유지, exposure42→137bars, MAE−0.370828%→−1.173709%다. 순익 증가만으로 위험까지 개선됐다고 판단하지 않는다. source-quality와 원 family/custody/sample guard 및 미래 tail 검증은 유지한다.

원격 main의 미시구조 통합·진단-only historical metadata 보존 source `53aecf746`을 구현 `e1b3591f1`과 병합해 다른 승인된 작업을 보존했다. CF 두 source helper의 bytes/hash는 분석 시작부터 종료·병합까지 같아 결과 lineage가 바뀌지 않았다. 병합 wrapper는 최초124PASS·5FAIL 후 비용 원천 선행 호출과 full calibration 호출을 구분하고 퇴역 raw study 부재를 검증하도록5개 oracle를 보완했다. 영향받은5개만 재검증한다. production wrapper/guard를 이전 계약으로 복원하지 않았다.

병합 wrapper 재검증은3PASS 후 남은2개의 구 daily 단일 호출/퇴역 raw toggle 기대값을 full calibration1회·기존 진단-only refresh1회·raw producer 부재 계약으로 보완하여2PASS로 닫았다. 최초124PASS와 수정5개 각각의PASS를 확인했고 전체 suite를 무조건 반복하지 않았다. wrapper runtime/source를 추가 변경한 것은 없다.

## 실제 커밋·푸시·소스 배포와 직접 소비

- 구현 `e1b3591f1`, 미시구조 후속 권한 계약 `09accdc80`까지 병합한 리뷰 source `ca30a3fa77f43aa6a4bda370610e01f541803c4b`. 원격 main 및 `fix/low-price-economic-comparison-20260918` atomic fast-forward push 완료. 해당 미시구조 report handoff의 영향 suite7PASS; 저가주 CF source bytes/hash와 완료 분석 lineage는 병합 후에도 같다.
- 12:59:03 KST managed root `/home/ubuntu/KORStockScan-runtime-releases/low-price-carry-joint-economics-20260918`를 selector와 기존3unit 다음 invocation의 source로 배포했다. 기존 auto-expansion PID41757/NRestarts0, widget PID0/NRestarts0, machine-final-refresh PID0/NRestarts9가 배포 전후 같았다. WorkingDirectory/ExecStart 및 기존 resource/security/restart guards를 검증했다. daemon reload만 했으며 service/bot restart·새 service/timer/cron·정책 재발행은 없다. 직전 미시구조 selected source09acc를 포함하여 보존한다.
- [배포 receipt](../../tmp/low-price-carry-joint-economic-20260918/deployment.json), [검증 receipt](../../tmp/low-price-carry-joint-economic-20260918/validation.json), [배포소스 직접 reader receipt](../../tmp/low-price-carry-joint-economic-20260918/deployed-readonly-consumption.json). 새 release에서64개 pair·holdout cashflow/EV/다리별 기여를 최종 episode로 재구성하고 실제 동결정책3개를 readonly load하여PASS. 최종 비교 SHA `87c14c2a101886e4a1fd1a2415a07b6f83487ae234a055d4e9c0589bedc8d037`, 원 보고서2개/동결policy SHA 불변이다. router `postclose 2026-09-17 --print-plan`도 동일 root/commit으로 확인했다. 시장/API/order 호출·경제계산 재실행·전체chain 실행 없이 reader만 검증했다.
- 이 배포는 다음 invocation의 source 선택이며 실제 새 trading PID 소비·자연 broker target 회복/체결·미사용 미래 경제성·공동자본 EV 수락은 아니다. native 기존0건, 조건부CF12건(그중 calibration 일관10건), actual 미확정, joint EV/net null을 별도로 보존한다. `LowPriceExpandedResearchRepair0918`은 이 잔여 acceptance의 단일 OPEN owner다. 구현 범위 unresolved finding0과 관련 검증PASS로 코드 closure를 닫고 같은 입력의 반복 연구는 하지 않는다.
