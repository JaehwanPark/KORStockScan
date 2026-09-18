# 2026-09-18 panic_sell_defense_report 결과·입력 보완 리뷰

Owner: `PanicSellDefenseSourceAcceptance0918`. 대상 장후 source date는9/17이며 사용자 승인 범위는 반복 code review/fix/검증·commit/push·소스 배포·장후 결과 갱신이다. [직전 breadth 분석](2026-09-18-microstructure-final-review-and-market-panic-breadth-analysis.md)의 다음 개별 단위다. 원 보고서·동결policy·custody·hard safety·provider·수량·정기 schedule을 보존한다. 새 panic/rebound runtime 또는 독립 튜너를 만들지 않는다.

## 먼저 식별한 실제 순서

`deploy/run_threshold_cycle_postclose.sh`의 순서는 `market_panic_breadth_collector → panic_sell_defense_report → scale_in_split_order_plan → exact trade fact sync / 후행 일일 report`다. breadth 수집은 panic/breadth 두 flag가 true일 때, panic 보고서는 panic flag가 true일 때 실행한다. 기본값은 둘 다true다. scale-in은 별도 flag의 조건부 단계이며 이번 분석 대상은 panic 보고서다.

9/17 원 wrapper는 `postclose-stepwise-20260917` 작업본의 실행 이력이다. 현행 selected source와 같은 것으로 재라벨링하지 않는다. log의 panic success/PERF/JSON·MD ready 다음에 scale-in resource guard PASS/22.392초/ready가 이어진다. 후행 native chain의 resource guard 중단과 이 단위 성공은 별개다. 확인 시 현행 main postclose cron은 설치돼 있지 않고 기존 intraday panic cron은 활성이다. 시간이20:10을 지나도 미설치 trigger가 저절로 실행되지는 않는다.

## 9/17 실행 결과와 의미

근거: `logs/threshold_cycle_postclose_cron.log`의 대상일 terminal/PERF와 [원 panic JSON](../../data/report/panic_sell_defense/panic_sell_defense_2026-09-17.json). exit0, wall40.411836초, peak child RSS259,472KiB; as_of23:49:17, generated23:49:58, latest pipeline event19:50:17이다. PERF는 해당 실행 receipt이며 반복 benchmark가 아니다.

| 항목 | 원 보고서의 수치 | 판정 |
| --- | ---: | --- |
| panic state / gate | NORMAL / normal | 해당 관측에서 발동 없음; 전체 시장 정상·유효 no-edge 판정 아님 |
| raw exit / broker-proven exit signal / stop-loss 분위수 표본 | 0 / 0 / 0 | real exit 비교/동적 stop-loss baseline 부재 |
| 판정 threshold mode | insufficient_sample | 일반 정상 무거래와 source/signal 결손을 별도로 봐야 함 |
| pipeline rows / micro 후보 event | 337,300 / 188,773 | 여러 stage 복사행과 실제 source snapshot 분모가 다름 |
| unique semantic 관측 / duplicate skip | 99,965 / 88,808 | 의미 중복 제거 후 detector 평가 |
| evaluated symbols | 3,005 | 비용/호가/완료 경제성 표본 수가 아님 |
| missing/degraded orderbook symbols | 2,468 | 충분한 depth를 갖춘 전체 시장 판정이 아님 |
| insufficient_data symbols | 537 | 추가 부족 상태; final NORMAL에 포함 |
| fresh book observation / stale or unhealthy observation | 8 / 1 | 건강한 호가 유입이 매우 얇음; symbol 수와 합산하지 않음 |
| micro risk-off / recovery signal | 0 / 0 | 고품질 paired EV의0개선과 구분 |
| active sim/probe / profit sample | 3 / 0 | 세 보유는9/6 swing state; 수익 표본 없음 |
| post-sell soft-stop trades | 0 | 원 zero rate가 동적 baseline 표본으로 잘못 집계됨 |
| 실제 비용 차감 EV / 일별 순익 | null / null | context 보고서가 직접 산출하지 않는 지표 |

`real_exit_count`는 broker/order provenance가 있는 **exit signal** 수다. submitted/order identity·신호 profit_rate만으로 COMPLETED·실제 fill quantity·최종 왕복 비용이 입증되지는 않는다. 이름을 근거로 실현 EV를 만들지 않는다. 현행 `regular_two_leg_machine`의 target/보조 청산 state가 이 legacy HOLDING_PIPELINE exit census에 모두 연결됐다는 근거도 없다. 보고서의0을 모든 owner의 실제 청산0으로 확장하지 않는다.

## 판정 로직과 실제 튜닝의 위치

생산자 `src/engine/panic_sell_defense_report.py`는 streaming으로 micro 관측을 detector에 넘기고 exit/probe provenance/매도 receipt만 보유한다. exit는 broker identity/attempt별 중복 제거하고 real·sim/probe·unproven을 분리한다. 동일일30분 stop-loss count p95, stop-loss binary ratio p95, exit signal profit p05를 계산하며 기존 최소표본3을 유지한다. ratio는 최소70%, exit profit은 −2% 이하 경계를 사용한다. 이들은 **상태 해석 진단**이며 EV 최적화 calibration/독립 holdout이 아니다.

micro detector의 단일 종목 risk-off는 market RISK_OFF 또는 evaluated≥20·risk-off 비율의 기존 p95/max20% 기준으로 확인한다. 전체 breadth advisory는 별도 근거다. portfolio cluster만 있으면 watch, breadth만 있고 micro/cluster가 없으면 watch다. confirmed micro risk-off는 exit cluster 없이도 위험 상태에 기여할 수 있다. recovery evidence가 있어도 risk-off가 남으면 해제/완전 회복으로 보지 않는다. `NORMAL`만으로 기존 market-weakness latch를 해제하지 않는다.

active recovery는 sim/probe 수익 p75(평균 비교 threshold는 기존0.8% cap), win-rate p75(기존60% cap)와 각 표본 준비를 사용한다. post-sell은10/20분 반등률 p75와 최소50%/35% 기준, 기존 두 horizon 통계 준비를 사용한다. horizon별 비율 두 개는 독립 거래 두 건이 아니다. 손익·반등·closed actual을 합산하지 않는다.

동일일 count p95와 그 표본의 최대 rolling count 비교는 표본이 준비되고 stop-loss가 있으면 자기 표본의 최대가 p95 이상이 되는 성질이 있다. binary0/100 micro ratio p95도 일반적인 비율분포 calibration과 다르다. 이를 검증된 EV threshold 학습이라고 설명해서는 안 된다. 이번에는 근거 없이 숫자를 바꾸거나 새 threshold grid/정책을 만들지 않았다. 별도 EV 튜닝 owner는 기존 `market_weakness_entry_response → market_weakness_hysteresis_tuning`이며 [직전 분석](2026-09-18-microstructure-final-review-and-market-panic-breadth-analysis.md)의30분 BBO/full-cost/holdout 결손을 그대로 승계한다.

출력의 `panic_entry_freeze_guard`, `panic_stop_confirmation`, `panic_rebound_probe`, `panic_attribution_pack`은 report-only 상태/설계 표기다. `allowed_runtime_apply=false`이며 전용 live family가 아니다. 후보 표기가 생기거나 sim/probe 표본이 늘어도 retired panic-buying·freeze actuator 복원, 주문·holding/exit 정책 변경 권한은 생기지 않는다.

## 이번 반복 리뷰에서 수리한 결함

1. Micro detector는 미래 event를 제외했지만 report의 exit/provenance retained list와 latest event는 `as_of` 이후 행을 포함할 수 있었다. 두 경로 앞에서 KST로 clock을 정규화하고 target date·declared emitted date·cutoff를 함께 확인한다. 미래 sell receipt가 과거 sparse exit를 real로 승격하거나 미래 probe row가 과거 real signal을 지우지 못한다. 제외 사유·accepted/scanned 분모를 남긴다.
2. 날짜 없는/future/다른 날짜 mutable sim/probe state가 recovery에 들어갈 수 있었다. state updated_at의 동일 target date·cutoff와 row의 actual=false/broker-forbidden=true를 모두 확인한 행만 수익 표본에 넣는다. 원 observed count·제외 수·source time status·provenance 위반을 보존한다.
3. Mutable 시장 cache와 breadth는 날짜/time/source-quality를 확인하지 않고 확인 근거로 쓰였다. market timestamp·cached session date, breadth target date/as_of·quality=ok를 확인한다. 불일치 cache는 reported state를 진단으로 보존하면서 effective UNKNOWN, invalid breadth는 advisory/weakness handoff를 비사용 처리한다. 이 날짜 검사로 시세 event freshness나 venue/session 의미가 새로 입증되는 것은 아니다.
4. 거래0일 때 생산자가 내보내는10/20분 zero 반등률 네 개가 recovery `dynamic_quantile`을 만들었다. total_soft_stop≤0이면 이 placeholder를 표본에 넣지 않는다. post-sell date와 meta.generated_at cutoff도 확인한다. horizon statistics의 sample unit을 명시한다.
5. 같은 attempt의 A/A/B 신호에서 앞 두 행만 선택하면 중복A가 B 손익을 밀어내는 결함을 수리했다. broker identity별 한 행을 보존하고 남은 receipt capacity에는 sparse 행만 연결한다. 시각 순서도 KST로 정렬한다. 실제 fill/cost를 만들어낸 수리는 아니다.
6. risk-regime contract의 primary metric이 구현하지 않은 avoided-loss EV를 암시했다. 실제 상태 지표를 선언하고 economics를 `not_evaluated_context_report / null / null`, exit profit을 signal diagnostic으로 표시한다. source 불명/실현 미확정을 순익0으로 채우지 않는다.

수정은 기존 생산자·기존 시험 파일2개 안에서 닫았다. API 요청/parser·WS/FID·broker/order·runtime threshold·grid·sample floor·quantity·cost·bot/provider·source schedule은 변경하지 않았다. 새 production module/service/cache/performance guard는 없다.

## 제한 결과 갱신과 검증

[9/17 장후 결과 판정 JSON](../../data/report/postclose_research_successor_20260917_20260918/panic_sell_defense_result_review_2026-09-17.json)은 원 execution·분모와 소스 보완 preview를 분리한다. 원 JSON/MD/breadth/동결policy는 보존했다. 작은 동일 날짜 state/source/feedback만 읽고 native detector는 원 보고서에 저장된 값으로 유지했다. **5,713,580,290bytes 원 JSONL의 stat 확인 후 재스캔/전체 보고서 재생성은 하지 않았다.** 원 streaming aggregate에 미래/다른 날짜 행이 없었다는 것을 새로 인증한 결과가 아니다.

동일 원 active state의 updated_at을 대조한 preview는 observed3 → eligible0(9/6 state 제외), post-sell zero-trade baseline은 dynamic_quantile → insufficient_sample, 두 threshold sample_count0/readyfalse/dynamicnull이다. 이는 source/평가 유효성의 개선이며 recovered realized profit 또는 EV 개선이 아니다. 원 `NORMAL`을 경제성 성공이나 전일 전체 chain DONE으로 바꾸지 않는다.

초기18개 중13PASS/5FAIL은 날짜/time이 없는 기존 fixture였다. 실제 producer timestamp/date 계약을 갖춘 fixture로 보완하고 detector 포함32PASS. 새 회귀에서36PASS/1FAIL은 기존 마지막 assert의 시험 함수 위치 문제여서 수정했다. 생산자·detector·notifier·daily/runtime의 영향 검증81PASS/276deselected, economics 계약 추가 후 생산자23PASS; 주문별 중복 보완 후 같은 영향 범위82PASS/276deselected. 실행 수를 합산하지 않는다. Compile·diff·링크·단일 owner·print-only parser로 닫는다. 전체 trading/provider/DB/API·raw replay·비싼 research·controller/finalization을 재실행하지 않았다.

## 시간으로 해소될 것과 구조적 결손

| 판정 | 첫 owner / 근거 | 다음 조치 | Closure |
| --- | --- | --- | --- |
| 조건부 동일일 표본 부족 | report의 real exit rolling baseline0/최소3 | broker-proven unique exit가 실제 유입되는 날 재평가 | 같은 날 valid signal·분리 profit 표본·중복/real/sim partition 확인; 단순3일 대기로 대체 없음 |
| horizon maturity | 기존 post-sell owner의10/20분 outcome | 실제 valid sell과 horizon path가 있을 때만 cutoff 도달 대기 | source-valid mature rows와 horizon 분모; 가격/window 누락은 기다림으로 복구 없음 |
| 고정9/17 BBO/관측 결손 | detector2,468 book missing·537 insufficient·fresh8 | 기존 exact-route producer의 원 packet/연속 depth/시계·등록→소비를 조사 | 같은 scope의 자연 usable 유입; 보존 원천 없으면 과거는 exclusion/null |
| stale/off source | swing state9/6·Swing OFF | 이번 source 제외 유지; 새로운 회복 sample을 약속하지 않음 | 기존 켜진 owner의 same-day/clock/provenance에 맞는 유입만 인정 |
| 현행 machine exit coverage 미입증 | legacy HOLDING_PIPELINE census와 dedicated order state 분리 | 기존 machine attribution/ledger의 자연 fill/terminal·owner lineage 확인 | native ID·quantity·비용·COMPLETED와 정확히 연결; 강제 주문/가상 청산 금지 |
| 반등 horizon 분모 미선언 | post-sell producer는 total soft-stop 분모/zero rates를 export | 별도 그 producer 리뷰에서 관측 가능한 horizon 분모를 확인 | missing horizon을 false/0으로 세지 않는 원천 계약; 이번0거래 placeholder 수리와 별개 |
| EV/일별 순익 비교 부재 | context report에 paired full-cost/control/holdout 없음 | 기존 market-weakness tuner의 원천을 먼저 닫음 | 비용/수량·시장/owner·동일기회·독립 holdout·tail·노출; context count를 EV로 전환하지 않음 |
| native postclose 미설치 | 설치 cron 조회 / 단계별9/17 복구 이력 | OFF 상태 유지, 이미 활성 intraday와 기존 예약 owner를 구분 | 승인 없이 cron 복원 없음; 실행 권한/trigger 없으면 ETA null |
| collection vs market event clock | breadth23:48 snapshot, global cache19:50, pipeline19:50 | 원 market timestamp·venue/session contract 조사 | 날짜·수집 clock 통과를 fresh market price로 오인하지 않음 |

경제성 개선 ETA는 null이다. 유효 source/holdout이 모이더라도 수익 개선이 보장되지는 않는다. 우선순위는 **동일 날짜/cutoff·zero-sample 결손 수리 → 자연 source yield/현행 owner coverage → 기존 EV 튜너 → 비용 후 실제 효과**다.40초 보고서의 과도한 성능튜닝/새 성능 guard보다 이 순서가 먼저다.

## 배포·소비 경계

검토된 clean managed source와 실제 consumer를 별도 receipt로 기록한다. 공통 selector는 다음 invocation용이다. 기존 독립 widget/episode service pin·PID를 불필요하게 옮기지 않는다. 활성 intraday cron은 workspace wrapper를 사용하므로 selected release만으로 그 producer 소비를 주장하지 않는다. 해당 생산자 파일의 검토본 동등성/다음 자연 결과 여부를 따로 확인하고 schedule/notifier/guard/order authority는 보존한다. source 선택·direct reader·자연 writer·실제 경제성은 서로 다른 상태다.
