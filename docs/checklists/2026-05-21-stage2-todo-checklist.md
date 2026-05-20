# 2026-05-21 Stage2 To-Do Checklist

## 오늘 목적

- 2026-05-20 postclose에서 산출된 `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=160` 후보가 장전 runtime env에 정상 반영됐는지 확인한다.
- 장중 수집된 scalp sim row가 LDM stage/action bucket별로 충분히 분산됐는지 장후에 판정한다.
- `max_daily=160` 및 reserve/bucket quota 적용 결과를 검증한 뒤 `240` 상향 여부를 postclose LDM joined/action bucket coverage로만 결정한다.
- sim/probe 표본은 source-quality/EV 입력으로만 쓰고 real execution 품질이나 실주문 전환 근거로 쓰지 않는다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- `SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY` 추가 상향 또는 reserve/bucket quota 변경은 장중 env 수정이나 restart flag로 처리하지 않고, postclose 산출물과 다음 PREOPEN 후보로만 다룬다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장후 체크리스트

- [ ] `[ScalpSimLdmMaxDaily240Review0521] LDM joined/action bucket coverage 확인 후 scalp sim max_daily 240 상향 여부 결정` (`Due: 2026-05-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:40`, `Track: ScalpingLogic`)
  - Source: [lifecycle_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/lifecycle_decision_matrix.py), [lifecycle_decision_matrix_2026-05-21.json](/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-21.json), [threshold_runtime_env_2026-05-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-21.env)
  - 판정 기준: `max_daily=160`과 reserve/bucket quota 적용 후 postclose LDM의 `stage sample`, `joined_sample`, `join_rate`, `action_namespace`, `source_stage`, `risk_context_owner`, `risk_direction` bucket coverage를 확인한다. stage floor만 통과한 상태가 아니라 entry/scale_in/exit와 panic/euphoria action bucket이 한쪽으로 과도하게 쏠리지 않았는지 본 뒤 `240` 상향 후보 여부를 결정한다.
  - 금지: `240` 상향을 장중 runtime env 직접 수정, restart만으로 적용, real order enable, Telegram BUY/SELL, provider route, bot restart trigger로 연결하지 않는다.
  - 다음 액션: `keep_160_coverage_enough`, `preopen_candidate_240`, `hold_160_until_persistent_counter_fixed`, `defer_source_quality_or_bucket_skew` 중 하나로 닫고, `preopen_candidate_240`이면 다음 PREOPEN `threshold_cycle_preopen_apply` 확인 항목을 생성한다.
