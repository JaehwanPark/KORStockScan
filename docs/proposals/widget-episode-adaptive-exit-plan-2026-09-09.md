# 위젯·에피소드 시간/진행률 청산과 빠른 접근 트레일링 제안

작성: `2026-09-09 KST`. 상태: `DESIGN_PROPOSAL / NOT_AUTHORIZED_FOR_LIVE_APPLY`.

요청 범위는 검토·구체적인 구현방안 제안이다. 이 문서는 코드 구현, 기존 목표가 주문 취소, 손절/시간청산 도입, 실거래 재기동 또는 자동 적용을 승인하지 않는다. 이번 변경은 제안서와 기존 체크리스트 owner 연결뿐이다.

후속 [상세 구현계획](widget-episode-adaptive-exit-implementation-plan-2026-09-09.md)은 수정 모듈·schema·주문 상태 전이·WP0~WP9·회귀·장후/PREOPEN 연결을 구체화한다. 구현/활성화 승인은 별도이며 본 제안의 위험 선택 미결정 상태를 유지한다.

## 1. 결론과 목적

검토할 가치가 있는 방향이다. 다만 “목표가에 늦게 도달하는 종목은 이후 하락하고 빠르게 접근하는 종목은 더 상승한다”는 현재 가설이지, 본 검토에서 검증된 사실은 아니다. 종목별 고정 시간 하나로 전량 매도하기보다 다음 두 효과를 분리해서 검증한다.

- 느린 경로: **시간 경과 + 목표 진행 부진 + 상승/반등 지지 약화**일 때 남은 보유 기대값보다 현재 청산 기대값이 유리한지 평가한다.
- 빠른 경로: **빠른 목표 접근 + 비용을 넘는 수익 여유 + 지속적인 매수 지지**일 때 일부 잔량을 트레일링하여 기존 익절 이후의 추가 상승을 확보할 수 있는지 평가한다.

최종 목적은 승률이나 매도 횟수가 아니라 `비용 차감 누적 순이익 + 유효 기회당 EV + 자본점유 대비 순이익` 개선이다. 작은 수익을 자주 얻어도 드문 큰 손실이 이를 상쇄하면 실패다. 조기청산으로 확보한 현금이 재사용되지 않았는데 추가 수익을 가정하거나, 매도 후 같은 신호를 즉시 재매수해 회전수를 부풀리지 않는다.

권장 순서는 **원천·경로 계측 → 시간/진행률 조기청산 단독 연구 → 안전한 주문 전환 구현 검토 → 일부 잔량 트레일링 → 결합 정책 검증 → 별도 승인된 제한 적용**이다. 연구는 네 대안을 비교할 수 있지만 동일 청산 stage의 실거래 변경은 한 축/한 정책 버전씩 진행한다.

## 2. 현재 구현과 확인한 한계

| 영역 | 현재 근거 | 이번 제안과의 차이 |
| --- | --- | --- |
| 저가주 에피소드 | [preflight](../../src/trading/low_price_two_leg/preflight.py)의 `stop_loss=none`, `unfilled_target=hold_position_without_forced_exit`; `target_timeout_cancel`, `forced_exit_or_stop_loss` 금지 | 새 청산 정책은 기존 계약 변경이다. 단순 entry-timing 값 조정으로 적용할 수 없다. |
| 에피소드 상태 | [공통 two-leg machine](../../src/trading/order/regular_two_leg_machine.py)의 target 제출/대사, [low-price machine](../../src/trading/low_price_two_leg/machine.py)의 목표가 정책 일치 및 기존 보유 policy carry | 고정 target 외 exit 상태·주문 역할·재시작 복구 계약이 필요하다. 과거 보유분은 생성 당시 정책을 보존한다. |
| 위젯 | [engine](../../src/trading/widget_auto_trade/engine.py)의 `_maybe_submit_take_profit`, `_cancel_pending_take_profit_sells`, `_maybe_submit_exit`; [policy](../../src/trading/widget_auto_trade/policy.py)의 종목별 `source_final_exit_action` | 일부 종목의 source EXIT와 취소 후 청산 기반은 있다. 따라서 모든 위젯에 매도 기능이 전혀 없다는 뜻은 아니다. 제안한 시간/진행률 손절 및 이익 트레일링과는 별개다. 현재 ON 여부는 당일 정책/소비 receipt를 추가 확인해야 한다. |
| 기존 장후 연구 | [turnover research](../../src/engine/monitoring/machine_lifecycle_turnover_policy_research.py)의 `target_timeout_sec=60/120/180`, rolling paired EV·자본효율 비교 | 연구는 존재하지만 `runtime_effect=false`, `allowed_runtime_apply=false`다. 새 runtime family/적용 권한이 없고 트레일링 연구도 아니다. |
| 최근 완료 원천 | [9/8 attribution](../../data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.md)의 matched unique decision lifecycle/entry-fill/exit anchors 모두 0 | 이 연구의 exact join 분모가 0이라는 뜻이다. 실거래 전체가 0이거나 가설이 틀렸다는 뜻은 아니다. 과거 결손을 반복 replay로 복원하지 않는다. |
| 비용·빈도 | [9/8 low-price tuning](../../data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_2026-09-08.md)의 드문 profile별 시도, exact 비용 일치와 모델 비용 fallback 분리 | 희소 profile에 일률적인 일별 완료 표본을 요구하면 도달하기 어렵다. 모델 비용 EV를 exact broker 순이익으로 보고하지 않는다. |

기존 연구 내부의 `candidate_realized=true`는 반사실 경로의 종료 계산이다. 실제 후보 정책이 주문·체결됐다는 뜻으로 재사용하지 않는다. 확장 schema에서는 `counterfactual_exit_resolved`와 `actual_broker_terminal`을 명시적으로 분리하고 기존 consumer 호환성을 검토한다.

### 가장 중요한 주문 제약

현재 목표가에 전량 매도주문이 이미 접수돼 있으면, 목표가 도달 시 주문이 먼저 체결될 수 있다. **체결된 물량을 나중에 트레일링할 수 없다.** 목표가 직전 전환하거나 처음부터 다른 출구를 가진 물량을 나눠야 한다.

초기 권장안은 기존 목표가 주문을 유지하다 **도달 전** 일부 잔량만 전환하는 방식이다. 두 개 10주 leg 구조에서는 한 leg는 원래 목표가, 다른 leg의 미체결 잔량만 전환 후보로 삼는다. 이는 총수량 증액은 아니지만 청산 역할 변경이므로 새 승인이 필요하다. 위젯은 실제 filled lot과 주문별 수량으로 별도 배분하며 무조건 절반/10주를 가정하지 않는다.

취소 중 원래 목표가가 체결되면 정상 baseline 익절로 종결한다. 이를 트레일링 누락 결함으로 간주하거나 물량을 재매수하지 않는다. 진입 때부터 runner target을 걸지 않는 대안은 무주문 보유와 소프트웨어 장애 노출을 더 크게 만들므로 초기안에서 제외한다.

## 3. 청산 정책 설계

### 3.1 공통 기준과 시간축

정책 key는 `order owner × symbol × profile/setup × venue/session × entry policy version`이다. 종목명이 같아도 main/widget/episode 또는 오전/오후 표본을 같은 승인 분모로 합치지 않는다.

- 기준 시각은 실제 첫 매수 체결이다. `signal → BUY 접수 → 첫 체결 → target 접수` 지연은 별도로 남긴다. 부분체결 lot의 나이를 보존하고, 새 체결이나 재기동으로 오래된 보유의 시간을 리셋하지 않는다.
- `age_active_sec`와 wall-clock age를 모두 저장한다. VI/거래정지/세션 종료를 정상 거래시간과 구분한다. 장중 유효 거래시간 타이머와 별도의 세션 경계 잔고 처리 계약을 명시한다.
- `P_entry`는 해당 평가 단위의 실제 체결 원가, `P_target`은 그 정책 버전의 원래 목표가다. 잔량을 팔 수 있는 깊이와 수량을 확인한 executable bid를 `P_exec`로 사용한다.
- 목표 진행률은 `(P_exec - P_entry) / (P_target - P_entry)`다. 분모가 양수가 아니거나 호가/잔량이 유효하지 않으면 계산 불가다. 음수·100% 초과 값도 원형을 보존한다. 매도 목표가만 위로 바꾸면서 진행률/시간 기준을 리셋하지 않는다.
- 목표가 touch, 수량 충족 executable target, 실제 목표 주문 fill, episode COMPLETE는 서로 다른 사건이다. 호가 touch만으로 queue 선점·체결을 확정하지 않는다.
- 위젯 추가체결로 평균단가/target이 바뀌면 ordered policy/position epoch를 남기고 v1 승인 cohort와 분리한다. 청산 intent 이후 새 scale-in 제출은 중단하고 미체결 BUY를 대사한다. 이 우선순위 변경도 새 청산 계약의 승인 범위에 넣는다.

### 3.2 시간/진행률 조기청산

초기 연구 시간 후보는 기존 `60/120/180초`를 재사용한다. 이는 실전 권장값이 아니며, 관측상 훨씬 긴 회복시간이 정상인 profile에는 목표 first-hit 분포로 별도 후보 범위를 정한다. 종목별 단위 tick, 목표 거리, spread, 거래시간대 차이를 무시한 공통 3분 청산은 채택하지 않는다.

`age >= T_soft`일 때 다음을 당시 정보만으로 평가한다.

1. 목표가 미체결 잔량이 존재한다.
2. 진행률이 해당 정책의 최소 기준에 미달하고, 최근 진행률 개선도 약하다.
3. fresh BBO의 bid 지지·가격 회복·매수체결 뒷받침이 약하거나 adverse-first 경로다.
4. 보유 지속 대비 지금 청산의 증분 기대값이 비용·체결 오차를 감안해 우세한 조건으로 장후 검증됐다.

이 조건이면 `EARLY_EXIT_INTENT`를 만들고 원래 목표 주문의 잔량 취소부터 수행한다. runtime에서 매 tick 새 AI를 호출하지 않는다. 장후에 검증된 작고 결정론적인 규칙과 bounded 상태만 사용한다.

반등/진행이 유효하면 정해진 한 번의 유예 `T_extension`을 허용하는 대안도 비교하되, 유예 반복으로 무기한 보유를 재현하지 않는다. `T_hard`에서 청산을 강제할지 여부, 최대 허용 손실/노출, 세션 종료 처리는 별도 승인값이며 아직 정해지지 않았다. 시간 손절은 **T_soft 이전의 급락을 막는 가격 손절이 아니다**. 초기 연구에서도 그 구간의 tail loss를 함께 측정한다.

조기청산 거래 일부가 손실인 것은 이 정책의 실패 조건이 아니다. 더 큰 손실/자본점유를 줄여 전체 전략의 순이익을 개선하는지가 기준이다. 조기청산 subset에도 반드시 양수 수익을 요구하는 승인 기준은 두지 않는다.

### 3.3 빠른 접근 시 일부 잔량 트레일링

다음은 연구 파라미터 예시이며 적용값은 아니다.

- `age <= T_fast`이고 목표 진행률이 `70/80/90%` 등 사전에 제한한 후보 중 선택 기준 이상이다.
- 비용·spread·틱 반올림·전환 지연을 고려해도 보존할 이익 여유가 있다.
- 가격 상승/반등, bid 지지와 실제 매수체결이 함께 확인된다. ask 잔량 감소 하나로 상승을 단정하지 않는다.
- 전환할 leg/lot의 target 잔량 취소가 확인된 후에도 최신 원천에서 조건이 유효해야 한다.

조건 충족 시 해당 잔량에만 `TRAIL_ACTIVE`를 부여한다. 조건이 취소 대기 중 사라졌다면 승인된 전환 후 처리 규칙에 따라 청산 또는 target 재보호를 수행하며, 둘을 동시에 제출하지 않는다.

`high_water`는 실제 활성화 이후 관측한 유효 executable bid 고점이다. 트레일 기준은 개념적으로 `max(직전 trail 기준, 비용 회수 기준, high_water - gap)`이며 gap은 종목별 tick/spread/짧은 가격 흔들림을 반영한다. 기준은 내려가지 않고, 고점 갱신마다 broker 정정 주문을 쏘지 않는다. 가격이 기준 아래로 내려왔을 때 하나의 exit intent를 만든다.

비용 회수 기준과 현재 bid 사이에 충분한 간격이 없으면 이익 트레일링을 무리하게 활성화하지 않는다. 이미 걸린 trail이 급락으로 건너뛰어진 경우 기준을 낮춰 회복을 기다리지 않고, 유효한 시장 원천과 승인된 청산 방식으로 처리한다. **손익분기/트레일 가격은 트리거이지 보장 체결가가 아니다.** 시장가 계열은 가격 불확실성, 지정가 계열은 미체결 위험이 있다. [SEC 주문 위험 설명](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15)

특히 몇 tick의 작은 목표에서는 `비용 회수 가격 + 최소 trail 여유 < 목표가 - 취소 지연 여유`를 만족하는 활성화 구간 자체가 없을 수 있다. 이런 profile은 전환 시점을 억지로 늦추거나 target을 올려 통과시키지 않고 **고정 익절 유지/트레일링 부적합**으로 분류한다. 빠른 상승이라는 가설이 맞아도 전환 후 실제 남는 순이익이 없으면 채택하지 않는다.

잔량 전체를 trailing하는 대안과 한 leg만 trailing하는 대안을 같은 entry 집합에서 비교한다. “빠르게 올랐다”만으로 전량 target을 취소하는 것은 작은 익절의 빈도를 낮추고 이익반납을 키울 수 있으므로 초기 기본안으로 삼지 않는다.

## 4. 주문·상태·장애 처리

필수 상태 흐름은 다음과 같다. 상태 이름은 설계안이며 현재 구현된 enum이 아니다.

`TARGET_WORKING → EXIT/TRAIL_INTENT → CANCEL_PENDING → 잔량 대사 → FLAT | EXIT_PENDING | TRAIL_ACTIVE → FLAT`

1. intent와 원주문번호·owner·policy hash·잔량을 broker 호출 전에 영속화한다. 같은 intent 재처리로 주문이 중복되지 않아야 한다.
2. 취소 응답 접수는 원주문 terminal 확인이 아니다. 취소 중 부분체결, 취소 거절, fill-before-response, late receipt를 원주문/정정 계보와 함께 대사한다.
3. 재주문 수량은 해당 owner의 미청산 수량에서 아직 살아 있는 SELL 예약 수량을 뺀 범위이며, 계좌의 전시장 가용 잔고와도 일치해야 한다. 조회 실패·결손을 미체결 0으로 취급하지 않는다.
   - 위젯의 한 target 주문이 여러 lot을 합산한 경우 runner lot 선택만으로 해당 수량의 취소가 완료되는 것은 아니다. 원주문 부분취소의 잔량/체결을 정확히 결속해야 하며 지원·대사가 불명확한 결합 주문은 v1 전환 대상에서 제외한다. 연구 단계부터 이 제외율을 공개한다.
4. 원주문 취소/체결이 불명확하면 `RECOVERY_REQUIRED`로 두고 확인 전 다른 SELL을 내지 않는다. 취소 후 SELL 접수 응답이 유실된 경우에도 조회·receipt로 먼저 확인한다.
5. 청산 intent가 활성화되면 기존 `_maybe_submit_take_profit`가 취소한 target을 다시 만드는 일을 막는다. source EXIT, 시간청산, trailing, 남은 BUY 취소를 하나의 owner별 우선순위로 중재한다.
6. 기존 수량, 일일 cap, cooldown과 재진입 원칙을 유지한다. 조기청산을 COMPLETE로 분류하더라도 당일 성공 episode 수/시도 예산/손실 예산을 우회하지 않도록 terminal reason을 별도로 보존한다.
7. main·widget·다른 profile·수동 주문을 취소하거나 그 물량을 매도하지 않는다. 동일 종목 공존 정책은 이 소유권 제한을 대체하지 않는다.
8. 재기동 후 frozen entry/exit policy, 시계, high-water, cancel/submit intent를 복원한다. 과거 봉 고가로 고점을 소급 생성하거나 불명확한 주문을 새 주문으로 복구하지 않는다.

### 실행 방식과 운영 제약

- 기존 owner gateway/registry를 재사용한다. 빠른 출구는 허용된 가격 범위의 marketable limit와 잔량 처리부터 비교하되 가격 허용폭·유효기간·최대 시도·최종 잔량 처리 방식은 구현 전 확정한다. 미체결 시 시장가로 무제한 전환하는 기본값은 두지 않는다.
- 공식 Kiwoom spec에는 매도 `kt10001`, 정정 `kt10002`, 취소 `kt10003`과 매도 구분 `28`(스톱지정가)이 있다. 이 사실만으로 모든 venue에서 native trailing/OCO·원자적 cancel-replace가 가능하다고 가정하지 않는다. 이번 검토는 API 요청을 수행하지 않았다. [공식 고정 revision spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json)
- 제안 검토 시 upstream `main` SHA=`234560d213acd8871ae344b5481aecd2f30287fa`, 확인 파일=`kiwoom/_data/kiwoom_api_spec.json`, 확인 시각=`2026-09-09 12:34 KST`. 실제 API/WS 변경 구현 전에는 [공식 reference gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)에 따라 최신 revision·SDK·Postman·receipt/continuation 및 venue별 허용 주문을 다시 대조해야 한다. 본 부분 확인을 전체 protocol review 완료로 사용하지 않는다.
- 현재 공통 machine의 `run_until_terminal`은 `HELD`도 종료로 취급한다. 기본 live service가 항상 그 모드를 쓰는 것은 아니므로 설치 wrapper/실제 모드를 확인하되, 새 exit 관리가 필요한 보유를 정상 종료/no-op로 넘기지 않는 수명 계약이 필수다.
- 몇 초 간격의 기존 polling으로 초단기 trailing을 보장할 수 없다. 기존 읽기 전용 WS 원천 기반으로 deadline-aware 평가·bounded event coalescing을 검토하고, 실제 callback→판정→취소확인→SELL 지연 분포를 replay에 넣는다. API 한도·worker 동시성·재시도량을 올려 해결하지 않는다.
- 아직 target이 살아 있는데 원천이 stale이면 전환하지 않고 기존 주문 보호를 유지한다. 이미 target을 취소했다면 단순 feature OFF로 방치할 수 없다. 별도 승인된 잔량 recovery/알림과 유효한 신규 원천 확인이 필요하다. 거래정지·호가 공백·가격제한·프로세스 장애에서 즉시 청산/손실 상한은 보장할 수 없다.
- rollback은 신규 episode의 새 정책 선택 중단과 기존 활성 exit 상태의 안전한 종결을 나눈다. 기존 runner를 무조건 옛 target으로 되돌리거나 프로세스를 종료하지 않는다. 전일 보유·legacy 1주 custody는 자동 이관 대상에서 제외한다.
- generic/manual/operator veto와 broker/소유권/유효가격 guard는 유지한다. 매수 전용 global pause와 이미 승인된 매도 권한을 혼동하지 않도록 테스트하며 새 정책이 veto를 우회할 권한을 만들지 않는다.

## 5. 가설 검증과 경제성 평가

### 필요한 원천

clean baseline(`2026-06-05`) 이후 실제 signal/entry/target/exit policy 버전, order/episode/leg/lot ID, 부분체결, 취소·정정·최종체결, exact venue/session, 실제 비용·비용모델 버전, 동일 epoch의 ordered 0B/0D와 executable depth가 필요하다. 자료가 없으면 `unknown/source_quality_gap`이며 0원·현재가·봉 고가로 대체하지 않는다.

기존 entry/target 체결 이후에도 사전 선언한 범위에서 가격 경로를 관측해야 trailing의 반사실을 평가할 수 있다. 이 수집은 existing source-only observer의 제한과 API budget 안에서만 설계한다. 빈 과거 경로를 재실행으로 채우지 않으며, 샘플링된 관측의 효과를 전체 종목 모집단으로 외삽하지 않는다.

### 비교 설계

| 비교군 | 바꾸는 항목 | 구분하려는 효과 |
| --- | --- | --- |
| A | 현행 target/보유 정책 | 기준선 |
| B | 시간/진행률 조기청산만 | 손실·장기점유 감소와 너무 이른 청산 손해 |
| C | 빠른 접근 일부 trailing만 | 추가 이익과 익절빈도 감소/이익반납 |
| D | B+C의 한 고정 정책 | 상호작용 및 전체 순이익 |

- 같은 entry 기회·동일 수량·동일 정책 원천으로 paired 비교한다. 미래 target hit 여부를 당시 arm/exit 판단의 입력으로 사용하지 않는다. 미래 데이터는 결과 label로만 사용한다.
- 목표가 미도달/HELD/수동청산을 빼고 완료된 익절만 분석하지 않는다. 시간별 risk set에서 빠른 도달·느린 도달·미도달·관측 종료를 구분한다. 초기 target 거리/비용비율/변동성/시간대 차이도 통제한다.
- 실제 완료+정확한 비용이 있는 손익, 미완료 실제 보유, 같은 사전 고정 horizon의 executable mark-to-market 반사실을 별도 출력한다. 무기한 보유 기준선이 terminal이 아니면 실제 paired 실현손익은 미확정이다. 그러나 그 보유를 버리는 대신 공통 horizon 연구에서 tail/점유를 평가할 수 있다. CF 결과를 broker 실현 PnL로 합산하지 않는다.
- 실행 가능한 bid/depth라도 체결이 확정된 것은 아니다. target queue, 취소 대기 중 체결, 전환 후 adverse move, partial fill, 재제출 지연을 보수적으로 모형화하고 실제 실행 검증과 분리한다.
- 매수 원가는 전체 lifecycle EV에 포함하되, “지금 팔기 vs 추가 보유” 비교에서 이미 지불한 동일 매수 비용을 한쪽에만 다시 부과하지 않는다. 실제 fill→fill 손익에는 spread/slippage가 이미 반영돼 있으므로 같은 비용을 중복 차감하지 않는다. 반사실에는 executable bid/ask 사용으로 반영된 부분과 추가 지연·시장충격 가정을 분리한다.
- 원 단위 순이익/기회당 EV/일별 누적 순이익을 우선 보고하고, 순이익·자본시간 효율·보유시간 p50/p90·HELD 비율·하위 손익·최대 손실·익절 횟수·취소 실패율·매도 후 회복 기회손실을 함께 본다.
- freed capital의 추가 수익은 별도 동일 신호/예산의 포트폴리오 replay에서만 평가한다. 같은 원금을 즉시 무한 재사용하거나 손실 후 재진입을 가정하지 않는다.
- 종목별 파라미터는 소수 후보로 제한하고 날짜 단위 chronological holdout을 둔다. 동일 episode의 두 leg와 반복 tick을 독립 표본으로 세지 않는다. 다른 종목의 통계는 연구 prior로만 쓰고 현재 owner/symbol/session의 직접 검증을 대체하지 않는다.

## 6. 승인 기준 재설계 제안

현재 turnover 연구는 5일 관측·20 unique lifecycle·BBO 95%·depth 90%, rolling `5/10/20일` 각각 paired `5/10/20건`과 모두 양수 EV/개선, 20일 상대 EV 개선 `1%`·순이익 양수·p10 비악화를 요구한다. 이는 현재 **source-only 후보 생성 기준**이지 자동 live 승인 기준이 아니다.

다음 문제는 새 정책 연구에 그대로 옮기지 않는다.

1. 희소 profile의 매일 한 건 수준을 전제하는 rolling 5/10/20건 동시 조건은 관측 가능 수와 충돌할 수 있다. 유입·성숙·expiry·무신호일을 포함한 scope별 달성 가능성을 먼저 계산한다.
2. 겹치는 세 구간 모두 EV 양수/개선은 독립된 세 번의 검증이 아니다. 주 평가창+시간순 holdout을 사전 선언하고, 짧은 구간은 이상징후/rollback 보조로 사용한다.
3. 기준 EV가 0이면 현재 상대 개선율은 정의되지 않아 차단된다. 0 근처에서도 비율이 불안정하므로 **같은 집합의 비용 차감 절대 증분 EV(%p)/순이익**과 추정 불확실성을 우선한다. `1% 상대 개선`을 `1%p 절대 수익` 요구로 잘못 바꾸지 않는다.
4. 기존 `current_realized` paired 경제성만으로는 장기 HELD 회피 효과를 충분히 평가할 수 없다. 공통 horizon 연구와 실제 completed 경제성을 별도로 설계한다.

권장 단계는 다음과 같다. 아래는 신규 승인 계약의 설계이며 현행 floor를 수정하지 않았다.

| 단계 | 완료 조건 | 요구하지 않을 것 |
| --- | --- | --- |
| 계측/코드 수리 | exact identity·유효 시계/비용·source 분리·주문 상태 회귀·producer/consumer 계약 | 양수 EV, 실제 신규 exit 체결, 20일 대기 |
| 가설 연구 | 같은 기회 집합·미완료 포함·실행비용/지연·저차원 후보·날짜 holdout·표본/불확실성 공개 | 모든 horizon 동시 개선, 연구 후보를 live 후보와 동일 취급 |
| 제한 적용 검토 | 사전 승인한 owner/profile 범위·손실/노출/실행위험 예산, 완전한 주문 안전 테스트, 직접 scope의 경제성/holdout 근거, 새 exit family/rollback/수명 계약 | 아직 활성화하지 않은 정책의 실제 체결을 최초 활성화 전 필수로 요구하는 순환 조건 |
| 확대/자동 유지 | 실제 후보 정책의 submit/cancel/fill/terminal·비용·미체결·tail·잔고 대사와 정책 버전별 누적 효과 | offline 결과만으로 전종목 확대, 수익성 없는 회전 증가 |

표본 수와 경제적 비열등/개선 허용폭은 scope별 관측률·분산·허용 손실에 맞춰 **후보 결과를 보기 전에** 확정한다. 구체적 숫자는 아직 산출/승인되지 않았으며 이 문서만으로 자동 후보를 통과시킬 수 없다. 표본이 적다는 이유로 실행 안전성을 낮추거나 같은 leg/tick을 복제하지 않는다. 부족하면 연구는 계속 가능하되 live는 baseline 유지다. 불확실성이 큰 작은 표본에 '양수 평균'만으로 수익성이 입증됐다고 하지 않는다.

## 7. 장후작업·PREOPEN 자동화 제안

현재 코드상 연결된 것은 attribution과 source-only turnover 연구까지다. **시간청산/트레일링의 다음 장전 자동 적용은 아직 연결돼 있지 않다.** Entry timing용 자동 적용 경로가 존재한다는 사실은 새 exit 권한이 아니다. 오늘 설치 상태/실행 성공을 이 코드 검토 결과로 대신하지 않는다.

기존 실행 owner를 활용해 아래 의존 연결을 추가하는 안이다. 새 시각의 병렬 cron은 먼저 만들지 않는다.

1. 기존 widget evaluation 4개 producer와 Samsung/low-price tuning에서 실제 policy·fill·target·terminal·비용 원천을 같은 completed source date로 고정한다.
2. 21:15 machine final refresh의 attribution을 소비하는 `machine_lifecycle_turnover_policy_research`를 확장해 A/B/C/D, 속도별 outcome·HELD·실행전환 반사실·승인 달성 가능성을 생성한다. current generation이 고정되기 전 후보를 발급하지 않는다.
3. 별도 exit candidate/policy schema에 native recommendation ID, owner scope, source/entry/exit policy hash, 비용 계약, 파라미터, 유효일, 승인 근거, rollback을 기록한다. 기존 entry-timing approval의 금지 필드를 임의 해제하지 않는다.
4. 새로운 exit family 등록과 기존 PREOPEN consumer 확장은 **사용자의 최초 정책 계약 승인 후** 구현·배포한다. 이후 승인된 범위 안에서는 유효 후보를 다음 exact-date PREOPEN에 자동 선택하고 매일 별도 수동 승인 없이 반영할 수 있도록 설계한다.
5. owner별 loader/preflight/현재 process의 policy-load receipt와 새 episode의 frozen exit version을 검증한다. 날짜가 틀리거나 candidate hash·필수 source·authority가 맞지 않으면 신규 episode는 baseline을 유지한다. 기존 활성 exit 관리는 §4의 복구 계약으로 계속 책임진다.
6. workorder→요약/checklist→strict source-hash verifier에 새 산출물과 소비 결과를 연결한다. 다음 장중/장후에는 선택·PID 소비·실제 exit 호출·체결·순이익을 각각 보고한다.

자동 적용의 허용 범위는 최초 승인에서 `대상 profile/신규 보유만/허용 모드/시간·진행률·gap 범위/손실·노출 한도/동일 stage 경쟁정책/세션·거래정지 처리/rollback`으로 제한한다. 새 종목 확대, 수량·재진입 cap 변경, 기존 보유 이관이나 그 범위 밖 파라미터는 재승인 대상이다.

추천 상태는 `source_quality_gap`, `research_only`, `insufficient_evidence`, `candidate_ready_pending_initial_authority`, `eligible_for_next_preopen`, `loaded_not_yet_called`, `actual_exit_verified`, `economic_acceptance_pending`, `rollback_required`로 구분한다. 신규 family가 없거나 권한이 없는데 표본 부족 ETA로 보고하지 않는다.

## 8. 구현 단위와 테스트

| 순서 | 구현 위치/역할 | 필수 검증 |
| --- | --- | --- |
| 1 | 기존 attribution/turnover research 및 owner event schema 확장 | 첫 fill clock·target/lot 정책 epoch·same-route/epoch·censor·비용·후행 관측·consumer 명칭의 실제/CF 분리 |
| 2 | 공통 순수 판정 로직은 `src/trading/order/`의 역할에 맞는 모듈; 주문은 owner adapter만 | 같은 원천·시점에서 offline/runtime 동일 결과, 미래 경로 차단, tick/단위·진행률 경계·유예 횟수·trailing 단조성 |
| 3 | widget engine 및 Samsung/low-price 공통 machine의 상태/registry 연동 | target 재생성 차단, BUY/SELL 경합, cancel ACK≠terminal, 부분체결, 중복 callback, 취소 실패, 응답 유실, crash/restart 각 경계 |
| 4 | 별도 exit policy/authority/PREOPEN consumer와 wrapper/서비스 수명 | baseline carry, old custody 비이관, hash/date 불일치, operator veto, HELD인데 manager 조기 종료, WS stale·rate limit·세션 경계 |
| 5 | 다음 장후 post-apply attribution | owner별 실제 exit reason·fill/비용·미체결·tail·빈도·자본시간, 수정/배포/소비/경제성 분리 |

`src/engine` root에 신규 Python 파일을 추가하지 않는다. 실제 새 파일 위치는 구현 때 인접 패키지/consumer를 확인하는 location gate를 다시 수행한다. 코드/주문 API 변경은 공식 reference gate와 `korstockscan-review-gate`, targeted pytest/compile, wrapper 변경이면 `bash -n`을 통과한 뒤 별도 승인된 실행만 허용한다. mock/CF 통과는 실제 broker 체결 품질 검증 완료가 아니다.

## 9. 다음 액션과 이번 검토 완료 범위

기존 [9/9 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 `MachineLifecycleTurnoverObjectiveFollowup0909`에서 새 원천 가능성·time/progress 가설 연구·높은 허들/CF 명명·신규 exit 계약 승인 필요를 대사한다. 이 owner의 현행 권한은 source-only이고 이 제안으로 확장하지 않는다. 별도 승인 전 자동 매도 구현·PREOPEN 정책 발행·기동을 시작하지 않는다.

실전 구현 요청 시 먼저 확정할 선택은 대상 신규 profile, 조기청산 손실/시간 상한, trailing 대상 lot/leg, 주문가격 허용폭과 미체결 잔량 처리, 세션 밖 보유/장애 정책이다. 수익 가설과 source 확보는 먼저 읽기 전용으로 검증할 수 있지만, 이 위험 선택을 시스템이 임의로 결정해서는 안 된다.

이번 검토는 코드·기존 완료 산출물·공식 주문 자료에 근거한 설계 검토다. 새 replay, 손익 통계 재계산, 현재 PID/계좌 전체 실사, 정책/주문/서비스 변경은 수행하지 않았다. 경제적 기대효과는 미검증이며 기존 실현손익을 신규 수익 증가로 주장하지 않는다.

문서 review/fix에서는 작은 target의 전환 가능 구간 부재, 합산 target 주문의 부분취소/lot 결속, 코드상 자동화와 실제 가동 증거의 구분을 추가 보완했다. 링크·owner/권한·단위·상태 흐름을 재검토했으며 이 설계 문서 범위의 미해결 finding은 0이다. 실행 코드는 검토 완료/무결함으로 선언하지 않는다.

print-only checklist parser와 `git diff --check`는 통과했고 기존 OPEN owner는 한 번만 포함된다. 거래 코드를 수정하지 않아 trading 테스트/비싼 report 재생성은 실행하지 않았다. 외부 동기화는 실행하지 않는다. 필요하면 사용자가 다음 표준 명령 한 번만 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
