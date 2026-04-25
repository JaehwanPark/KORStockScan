# 2026-04-21 Stage 2 To-Do Checklist

## 목적

- `2026-04-21 09:45 KST` 이후 기존 튜닝 승격 흐름을 일시중단하고 `Plan Rebase`로 전환한다.
- `fallback_scout/main`, `fallback_single` 오염 표본을 분리하고 기존 `partial/rebase/soft_stop` 결론을 재집계 전까지 보류한다.
- `진입/보유/청산` 로직을 전수점검해 감사인이 검토 가능한 로직표를 만든다.
- 다음 튜닝포인트는 감사인 권고를 반영해 `entry_filter_quality`를 1순위 후보로 둔다. 오늘 실전 적용한 `main-only buy_recovery_canary`는 별도 긴급축으로 분리 기록한다. `holding_exit`, `position_addition_policy`, `EOD/NXT`는 후순위로 재정렬한다.
- 물타기/불타기/분할진입은 개별 튜닝축이 아니라 `포지션 증감 상태머신` 신규 설계 대상으로 묶되, 즉시 canary 대상에서는 제외한다.
- shadow/counterfactual 선행 원칙은 철회하고, 다음 1축은 `canary 즉시 적용 + 당일 rollback guard`로 설계한다.
- `songstock` 원격서버는 더 이상 운영 비교대상이 아니다. 현재 체크리스트의 모든 판정과 후속 액션은 `main-only baseline` 기준으로만 수행한다.

## 장전 체크리스트 (08:00~)

- [x] `[AuditFix0421] gatekeeper fast_reuse 완화 구현증거 및 목표 유지 여부 장전 확인` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`) (`실행: 2026-04-21 07:59 KST`)
  - 판정 기준: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)의 `_build_gatekeeper_fast_signature()` 변경 전/후 증거를 확인한다. 변경증거가 불충분하면 `gatekeeper_fast_reuse_ratio >= 10.0%` 목표는 판정 대상에서 제외하고 보류 사유를 기록한다.
  - 판정: 구현증거 충분, 목표 유지. `_build_gatekeeper_fast_signature()`는 price/score/volume/v_pw/buy_ratio/prog_*를 coarse bucket으로 묶고 orderbook 세부값은 signature에서 제외한다.
  - 근거: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:991), [test_state_handler_fast_signatures.py](/home/ubuntu/KORStockScan/src/tests/test_state_handler_fast_signatures.py:15) `small_noise`, `price_and_orderbook_noise` 흡수 테스트 통과.
  - 다음 액션: 장후 `[QuantVerify0421]`에서 `gatekeeper_fast_reuse_ratio >= 10.0%`와 `gatekeeper_reuse_blockers`의 signature_changed 감소를 같이 판정한다.
- [x] `[Governance0421] partial fill min_fill_ratio canary 승인 로그 고정 + 유지/롤백 조건 점검` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: ScalpingLogic`) (`실행: 2026-04-21 07:59 KST`)
  - 판정 기준: `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True` 사용자 승인 로그를 고정한다. 승인 상태를 전제로 유지/롤백 조건만 점검하고, 무승인 예외로 재분류하지 않는다.
  - 판정: 승인 로그 고정 완료, 유지. 무승인 예외 분류는 해제하고 유지/롤백 조건만 장후 성과로 본다.
  - 근거: [2026-04-20-operator-response.md](/home/ubuntu/KORStockScan/docs/2026-04-20-operator-response.md:77)의 승인 증거와 재분류 기록, [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:147)의 `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True`, [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:462)의 env rollback 경로 확인.
  - 다음 액션: 장후 `partial_fill_events`, `position_rebased_after_fill_events/partial_fill_events`, `partial_fill_completed_avg_profit_rate` 기준으로 유지/롤백 후보를 판정한다. 원격 반영 상태는 운영 로그/원격 설정 증거가 없으면 별도 원격 정합성 확인으로 분리한다.
- [x] `[AuditFix0421] 테스트 카운트 불일치 재현 및 증적 기록` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`) (`실행: 2026-04-21 07:59 KST`)
  - 판정 기준: 아래 4개 파일 pytest를 재실행해 `N passed`를 고정한다. 기존 `16 passed` 주장과 불일치하면 장후 보고에서 정정 근거를 함께 기록한다.
  - 실행 명령: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_openai_v2_audit_fields.py src/tests/test_scalping_feature_packet.py src/tests/test_state_handler_fast_signatures.py src/tests/test_gatekeeper_fast_reuse_age.py`
  - 판정: 불일치 없음. 지정 4개 파일 재실행 결과 `16 passed, 1 warning`.
  - 근거: `test_ai_engine_openai_v2_audit_fields.py`, `test_scalping_feature_packet.py`, `test_state_handler_fast_signatures.py`, `test_gatekeeper_fast_reuse_age.py` 실행 완료. warning은 `pandas_ta`의 pandas copy-on-write deprecation이며 테스트 실패/카운트와 무관.
  - 다음 액션: 장후 보고에는 기존 `16 passed` 주장을 유지하고, `9 passed`로 보이는 단일/부분 테스트 실행 결과와 혼용하지 않는다.

## 장중 체크리스트 (12:30~13:00)

- [x] `[EmergencyStop0421] 지연대응 fallback 분할진입 즉시 중단 및 봇 재기동` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 09:27~09:29`, `Track: ScalpingLogic`) (`실행: 2026-04-21 09:29 KST`)
  - 판정: `fallback split-entry -> partial/rebase -> soft_stop` 손실 증폭축으로 원인 귀속을 정정하고, 지연대응 fallback 진입 전체를 즉시 OFF 처리했다.
  - 근거: 1차 응급가드가 `fallback_scout/fallback_main` 2-leg를 `fallback_single` 1-leg로 줄였을 뿐 `ALLOW_FALLBACK` 자체는 유지해 `2026-04-21 09:24~09:25`에도 `fallback_bundle_ready orders=1`이 발생했다.
  - 조치: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)의 `SCALP_LATENCY_FALLBACK_ENABLED=False`, `SCALP_SPLIT_ENTRY_ENABLED=False`, `SCALP_LATENCY_GUARD_CANARY_ENABLED=False`; [entry_policy.py](/home/ubuntu/KORStockScan/src/trading/entry/entry_policy.py)의 `latency_fallback_disabled` reject; [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)의 canary override 차단.
  - 검증: `py_compile` 통과, 정책 호출 검증 결과 `CAUTION -> REJECT_MARKET_CONDITION / latency_fallback_disabled`, 봇 PID `23848` 재기동 후 `09:29` 이후 신규 `fallback_bundle_ready/ALLOW_FALLBACK/LATENCY_GUARD_CANARY` 로그 없음.
  - 감사 정정: 기존 `partial/rebase 관찰축` 진단은 불충분했다. 원인 귀속을 `fallback split-entry -> partial/rebase -> soft_stop`로 정정한다.
- [x] `[EmergencyStop0421B] fallback_scout/main 생성 로직 폐기` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 09:39~09:45`, `Track: ScalpingLogic`) (`실행: 2026-04-21 09:45 KST`)
  - 판정: `fallback_scout/main`은 scout이라는 이름과 달리 관찰 후 추가/중단 판단이 없는 동시 2-leg 주문이므로 폐기한다.
  - 근거: 기대 구조는 `소량 탐색 -> 충분히 낮은 가격이면 추가 -> 달아나면 중단`이어야 했지만, 실제 구현은 `CAUTION/override -> scout+main 동시 제출`이라 partial/rebase/soft_stop 손실 노출을 먼저 열었다.
  - 조치: [fallback_strategy.py](/home/ubuntu/KORStockScan/src/trading/entry/fallback_strategy.py)는 빈 주문 리스트를 반환하는 deprecated null-object로 변경했다. [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)와 [entry_orchestrator.py](/home/ubuntu/KORStockScan/src/trading/entry/entry_orchestrator.py)는 빈 fallback 주문을 `latency_fallback_deprecated` reject로 처리한다.
  - 운영 규칙: `fallback_scout/main`, `fallback_single` 모두 영구 폐기. 재도입/승격/재평가 canary 대상이 아니며, 향후 유사 설계는 AI 생성 코드 체크게이트와 운영자 수동 승인을 통과해야 한다.
- [x] `[PlanRebase0421] fallback 관련 축 영구 폐기 + 신규 축 canary 전환 선언` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:40~10:50`, `Track: Plan`) (`실행: 2026-04-21 11:44 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: fallback/split-entry/legacy shadow 승격 후보를 닫고, 다음 신규 1축은 `canary 즉시 적용 + 당일 rollback guard`로 전환한다.
  - 판정: 완료. `fallback_scout/main`, `fallback_single`, latency fallback split-entry는 영구 폐기 상태로 잠그고 재평가/승격/canary 대상에서 제외한다.
  - 근거: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)의 `SCALP_LATENCY_FALLBACK_ENABLED=False`, `SCALP_SPLIT_ENTRY_ENABLED=False`, `SCALP_LATENCY_GUARD_CANARY_ENABLED=False`; [fallback_strategy.py](/home/ubuntu/KORStockScan/src/trading/entry/fallback_strategy.py)의 deprecated null-object; [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md) §5/§7.
  - 검증: `2026-04-21 09:45 KST` 이후 live 로그 기준 `fallback_bundle_ready=0`, `ALLOW_FALLBACK=0`. `LATENCY_GUARD_CANARY=2`건은 `11:40 KST` pytest fixture 로그로 live 회귀가 아니다.
  - 다음 액션: 신규 정식 canary는 감사인 정의의 `entry_filter_quality` 1축만 유지한다. 오늘 실전 적용분은 별도 `buy_recovery_canary`로 추적한다.
- [x] `[PlanRebase0421] AI 엔진 A/B 보류 + Gemini 라우팅 고정` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:55~11:05`, `Track: AIPrompt`) (`실행: 2026-04-21 11:44 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: live 스캘핑 AI 라우팅을 Gemini로 고정하고 `OpenAI/Gemini A/B` 및 dual-persona shadow는 `entry_filter_quality` canary 1차 판정 완료 후 재개 여부를 별도 판정한다. 최대 기한은 `2026-04-24 POSTCLOSE`다.
  - 판정: 완료. 기본 스캘핑 route는 Gemini로 고정하고, OpenAI/Gemini A/B와 dual-persona shadow는 `entry_filter_quality` canary 1차 판정 전까지 보류한다.
  - 근거: [runtime_ai_router.py](/home/ubuntu/KORStockScan/src/engine/runtime_ai_router.py)의 기본 route `gemini`, [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)의 `OPENAI_DUAL_PERSONA_ENABLED=False`, [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py)의 Plan Rebase OpenAI 스캘핑 초기화 skip 경로.
  - 검증 증거: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_runtime_ai_router.py src/trading/tests/test_fallback_strategy.py src/trading/tests/test_entry_policy.py src/trading/tests/test_entry_orchestrator.py src/tests/test_sniper_entry_latency.py` 결과 `25 passed`.
  - 주의: `logs/runtime_ai_router_info.log`에는 pytest가 의도적으로 생성한 `scalping_route=openai` 케이스도 남는다. 이 로그는 A/B 재개 증거가 아니라 라우터 분기 테스트 증거로만 해석한다.
  - 운영 원칙: `songstock` 원격 비교, remote canary, 서버 간 차이 해석은 현재 의사결정 입력에서 제외한다.
- [x] `[PlanRebase0421] 진입/보유/청산 로직표 확정` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:50~11:30`, `Track: ScalpingLogic`) (`실행: 2026-04-21 11:44 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: `진입`, `보유`, `청산` 로직의 현재 상태/전이/관찰필드/폐기경로를 한 표로 확정한다.
  - 판정: 확정. 현재 튜닝 해석 단위는 `진입 -> 보유 -> 청산` 상태 전이를 분리하고, fallback 폐기경로는 정상 표본과 합산하지 않는다.
  - 로직표:
    | 구간 | 현재 유효 경로 | 폐기/보류 경로 | 관찰필드 |
    | --- | --- | --- | --- |
    | 진입 | `SAFE -> ALLOW_NORMAL -> entry_mode=normal` | `ALLOW_FALLBACK`, `fallback_scout/main`, `fallback_single`, legacy split-entry | `entry_mode`, `order_tag`, `latency_state`, `decision`, `blocked_stage`, `submitted_qty`, `filled_qty` |
    | 보유 | AI holding review, peak/elapsed/never-green/near-exit 관찰 | 물타기/불타기/분할진입 live 적용 | `ai_score`, `profit_rate`, `peak_profit`, `held_sec`, `capture_efficiency`, `add_position_candidate` |
    | 청산 | soft stop, hard stop, trailing/preset exit, AI early exit, EOD 판단 | NXT 가능/불가능 미분리 overnight 단일판정 | `exit_rule`, `profit_rate`, `hold_sec`, `sell_order_status`, `sell_fail_reason`, `is_nxt` |
  - 다음 액션: 장후에는 이 표를 기준으로 `entry_filter_quality` 설계축과 이미 적용된 `buy_recovery_canary` guard를 분리하고, `position_addition_policy`는 후순위로 유지한다.
- [x] `[PlanRebase0421] fallback 오염 코호트 재집계` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 11:30~11:50`, `Track: Plan`) (`실행: 2026-04-21 11:44 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: `normal_only`, `fallback_scout_main_contaminated`, `fallback_single_contaminated`, `post_fallback_deprecation`, `scale_in_profit_expansion`, `avg_down_candidate` 코호트를 분리하고 `fallback_single`은 `symbol + timestamp`로 합산 오염을 교차검증한다.
  - 판정: 완료. `trade_review_2026-04-21.json`의 `COMPLETED + valid profit_rate`만 손익 코호트에 사용하고, fallback 오염 표본을 정상 표본에서 분리했다.
  - 근거 스냅샷: `trade_review=2026-04-21 11:35:07`, `performance_tuning=2026-04-21 11:35:35`, `missed_entry_counterfactual=2026-04-21 11:35:51`.
  - 코호트 재집계:
    | 코호트 | 표본 | 평균 profit_rate | 실현손익 | 비고 |
    | --- | ---: | ---: | ---: | --- |
    | `normal_only` | 6 | `-0.670%` | `-23,731원` | fallback 제외 정상 체결 |
    | `fallback_single_contaminated` | 2 | `+0.295%` | `+6,540원` | `09:25:22~09:25:53`, `entry_mode=fallback`; tag 세분화 미보유로 timestamp 교차검증 필요 |
    | `fallback_scout_main_contaminated` | 0 | `N/A` | `0원` | trade_review 완료표본에는 scout/main tag 없음 |
    | `post_fallback_deprecation` | 1 | `+1.170%` | `+12,001원` | `09:45` 이후 신규 완료 표본 |
    | `scale_in_profit_expansion` | 0 | `N/A` | `0원` | 현재 완료표본 필드에 추가진입 확정 태그 없음 |
    | `avg_down_candidate` | 0 | `N/A` | `0원` | 현재 완료표본 필드에 물타기 후보 확정 태그 없음 |
  - 해석: `fallback` 2건은 수익이지만 설계 폐기 판단을 되돌릴 근거가 아니다. 문제는 수익/손실 방향이 아니라 `관찰 후 추가/중단 없는 fallback 다중/단일 진입`이 표본을 오염시킨 구조다.
- [x] `[Midday0421] 오전 체결 기준 1차 판정 잠금` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 12:30~12:45`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:36 KST, 지연실행`)
  - 판정 기준: 오전 표본 기준 `soft_stop_count/partial_fill_events`, `position_rebased_after_fill_events/partial_fill_events`, `partial_fill_completed_avg_profit_rate`, `gatekeeper_fast_reuse_ratio`, `gatekeeper_eval_ms_p95`를 먼저 기록한다.
  - 표본 규칙: `partial_fill_events < 20` 또는 `gatekeeper_eval_samples < 50`이면 hard pass/fail 금지, `방향성 판정`으로만 잠근다.
  - 사전 산출(`2026-04-21 11:35~11:36 KST` 스냅샷): `completed_trades=8`, `realized_pnl=-17,191원`, `soft_stop_count=4`, `partial_fill_events=7`, `soft_stop_count/partial_fill_events=57.1%`, `position_rebased_after_fill_events/partial_fill_events=13/7=1.86`, `partial_fill_completed_avg_profit_rate=-1.038%`, `full_fill_completed_avg_profit_rate=+0.587%`, `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=21,033ms`, `gatekeeper_bypass_evaluation_samples=50`.
  - 사전 판정: 표본 부족(`partial_fill_events < 20`)으로 hard pass/fail 금지. 방향성은 부정적이며 `partial_fill`과 `full_fill`은 분리 해석한다.
  - 판정: 표본 부족으로 hard pass/fail 금지. 방향성 부정으로 잠금한다.
  - 근거(스냅샷 재확인): `trade_review_2026-04-21.json`, `performance_tuning_2026-04-21.json` 기준 `completed_trades=8`, `realized_pnl=-17,191원`, `partial_fill_events=7`, `position_rebased_after_fill_events=13`, `position_rebased_after_fill_events/partial_fill_events=1.86`, `partial_fill_completed_avg_profit_rate=-1.038%`, `full_fill_completed_avg_profit_rate=+0.587%`, `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=21,033ms`, `gatekeeper_bypass_evaluation_samples=55`.
  - 다음 액션: 장후 `[QuantVerify0421]`에서 동일 지표를 재판정하고, `partial_fill_events < 20`이면 방향성 유지로 자동 보류한다.
- [x] `[Midday0421] 미진입 blocker 4축 오전 분포 잠금` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 12:45~12:55`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:36 KST, 지연실행`)
  - 판정 기준: 오전 `AI BUY -> 미진입`을 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리 집계한다.
  - 목적: 오후 무체결 구간과 분리해 오전 집중구간의 기회비용 분포를 먼저 고정한다.
  - 사전 산출(`missed_entry_counterfactual_2026-04-21.json`, `2026-04-21 11:35:51 KST`): terminal 후보 기준 `total_candidates=115`, `missed_winner_rate=76.5%`, `estimated_counterfactual_pnl_10m_krw_sum=647,365원`.
  - 4축 사전 분포: `latency guard miss=97/115(84.3%)`, `liquidity gate miss=1/115(0.9%)`, `AI threshold miss=0/115(terminal 기준)`, `overbought gate miss=0/115(terminal 기준)`.
  - 보조 분포: terminal 기준에는 `blocked_strength_momentum=17/115(14.8%)`가 별도 축으로 존재한다. event overlap 기준은 `blocked_overbought=20,819`, `blocked_ai_score=233`, `latency_block=3,332`이나 denominator가 달라 terminal 4축 분포와 합산하지 않는다.
  - 판정: 4축 잠금 완료. `latency`가 압도적 1차 병목으로 유지된다.
  - 근거(스냅샷 재확인): `missed_entry_counterfactual_2026-04-21.json` 기준 `total_candidates=115`, `missed_winner_rate=76.5%`, `estimated_counterfactual_pnl_10m_krw_sum=647,365원`, `latency guard miss=97/115(84.3%)`, `liquidity gate miss=1/115(0.9%)`, `AI threshold miss=0/115(terminal 기준)`, `overbought gate miss=0/115(terminal 기준)`.
  - 다음 액션: 장후 최종판정에서 `latency_block` 축을 1차 해석축으로 고정하고, `blocked_strength_momentum`은 보조축으로 분리한다.
- [x] `[Midday0421] 장후 최종판정 후보축 1차 고정` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 12:55~13:00`, `Track: Plan`) (`실행: 2026-04-21 12:36 KST, 지연실행`)
  - 판정 기준: `canary 착수축 후보 1개`, `보류축 후보`, `오후 추가확인 항목` 3줄을 문서에 잠근다.
  - 메모 규칙: 장후에는 이 1차안을 덮어쓰지 말고 `변경사유`를 덧붙여 최종판정으로 승격한다.
  - 사전 후보: `실전 적용축 후보=main-only buy_recovery_canary`, `정식 다음축 후보=entry_filter_quality`, `보류축 후보=holding_exit/position_addition_policy/EOD-NXT/AI 엔진 A/B`, `오후 추가확인=latency p95 21,033ms 지속 여부, partial fill low-N 방향성, 09:45 이후 fallback 회귀 0건 유지, Gemini WAIT 65/70 과밀 여부`.
  - 판정: 1차 후보축 잠금 완료.
  - 근거: `실전 적용축=main-only buy_recovery_canary` 유지, `정식 다음축=entry_filter_quality` 유지, `보류축=holding_exit/position_addition_policy/EOD-NXT/AI 엔진 A/B` 유지. 추가확인 항목은 `latency p95 21,033ms`, `partial_fill low-N`, `fallback 회귀 0건`, `WAIT 65~79 BUY 회복 실측(현재 BUY 전환 0건)`으로 잠근다.
  - 다음 액션: `[Workorder0421]` 및 `[QuantVerify0421]`에서 장후 최종판정 시 유지/보류/롤백 후보를 분리 기록한다.
- [x] `[AIPrompt0421] WAIT65_79 EV 코호트 고정수집 + paper-fill + full/partial N gate + 소량 실전 probe canary 반영` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 13:00~13:20`, `Track: AIPrompt`) (`실행: 2026-04-21 13:37 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: `wait65_79_ev_candidate`에 `buy_pressure/tick_accel/micro_vwap_bp/latency_state/parse_ok/ai_response_ms`를 고정 수집하고, terminal blocker를 결합한 `wait6579_ev_cohort` 스냅샷을 생성한다.
  - 판정: 완료. WAIT65_79 전용 행 기반 코호트 수집 + paper-fill 기대 체결/EV 산출 + full/partial 최소 N gate + 소량 실전 probe canary를 코드/리포트에 반영했다.
  - 근거: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)의 `wait65_79_ev_candidate`/`wait6579_probe_canary_applied` stage, [wait6579_ev_cohort_report.py](/home/ubuntu/KORStockScan/src/engine/wait6579_ev_cohort_report.py), [log_archive_service.py](/home/ubuntu/KORStockScan/src/engine/log_archive_service.py)의 `wait6579_ev_cohort` 스냅샷 저장 경로.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_wait6579_ev_cohort_report.py src/tests/test_log_archive_service.py src/tests/test_state_handler_fast_signatures.py` 결과 `16 passed`.
  - 다음 액션: 장후 판정에서 `approval_gate.min_sample_gate_passed`를 1차 통과조건으로 잠그고, 통과 후 `ev_directional_check_passed`로 임계값 하향 승인 여부를 결정한다.
- [x] `[AIPrompt0421] Gemini 라우팅 누락 보정(OpenAI v2 피처 parity) 즉시 반영` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:20`, `Track: AIPrompt`) (`실행: 2026-04-21 14:34 KST`)
  - Source: [2026-04-11-scalping-ai-prompt-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-11-scalping-ai-prompt-coding-instructions.md)
  - 판정 기준: Gemini 엔진 경로에서 `_extract_scalping_features` 누락을 보정하고, 프롬프트 입력 정량 피처를 OpenAI v2 수준으로 확장한다.
  - 판정: 완료. [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py)에 `_extract_scalping_features`를 추가해 `extract_scalping_feature_packet`을 직접 반환하도록 반영했고, `[정량형 수급 피처]` 블록에 `spread/top-depth/microprice_edge/curr_vs_micro_vwap_bp/curr_vs_ma5_bp/volume_ratio` 등 누락 필드를 확장했다.
  - 기대효과: `wait65_79` probe 피처가 0으로 고정되는 문제를 제거해 `buy_recovery_canary` 승격 후보 표본이 정상 수집된다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalping_feature_packet.py src/tests/test_wait6579_ev_cohort_report.py src/tests/test_log_archive_service.py src/tests/test_ai_engine_openai_v2_audit_fields.py` 결과 `12 passed, 1 warning`.
- [x] `[AIPrompt0421] Gemini 프롬프트 프로파일/액션 분리 스키마 전면 이식` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 14:40~15:00`, `Track: AIPrompt`) (`실행: 2026-04-21 14:49 KST`)
  - Source: [2026-04-11-scalping-ai-prompt-coding-instructions.md](/home/ubuntu/KORStockScan/docs/2026-04-11-scalping-ai-prompt-coding-instructions.md)
  - 판정 기준: Gemini analyze 경로에 `watching/holding/exit/shared` 프로파일 분기를 모두 반영하고, 보유/청산 액션을 `HOLD/TRIM/EXIT` 스키마로 분리한다.
  - 판정: 완료. [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py)의 `_resolve_scalping_prompt()`에 `exit` 프로파일을 추가하고 prompt_type을 `scalping_entry/scalping_holding/scalping_exit/scalping_shared`로 정렬했다. `_normalize_scalping_action_schema()`를 추가해 `action_v2`(신규 스키마)와 `action`(legacy 호환)을 동시 제공한다.
  - 호환 규칙: `HOLD->WAIT`, `TRIM->SELL`, `EXIT->DROP`.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_cache.py src/tests/test_scalping_feature_packet.py src/tests/test_wait6579_ev_cohort_report.py src/tests/test_log_archive_service.py src/tests/test_ai_engine_openai_v2_audit_fields.py` 결과 `26 passed, 1 warning`.

## 장후 체크리스트 (15:20~)

- [x] `[PlanRebase0421] 다음 튜닝포인트 1축 재선정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:40`, `Track: Plan`) (`실행: 2026-04-21 12:18 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 감사인 권고에 따라 정식 다음축은 `entry_filter_quality`로 고정한다. 오늘 실전 적용한 `buy_recovery_canary`는 별도 긴급축으로 분리 기록한다. `holding_exit`, `position_addition_policy`, `EOD/NXT`는 후순위로 기록한다. 코호트 데이터가 반대 근거를 보이면 사유를 명시한다.
- [x] `[PlanRebase0421] buy_recovery_canary 설계 + rollback guard 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:10`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:18 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: `main-only buy_recovery_canary` 규칙(`WAIT 65~79`, feature allowlist, `SCALPING_SYSTEM_PROMPT_75_CANARY` 재사용)과 `N_min`, `reject_rate`, `loss_cap`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`, `buy_drought_persist` guard를 수치로 고정한다.
  - 정식 guard: `trade_count < 50`이고 `submitted_orders < 20`이면 방향성 판정; canary cohort 일간 합산 실현손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 OFF; `entry_reject_rate >= normal_only baseline + 15.0%p`이면 OFF; `gatekeeper_eval_ms_p95 > 15,900ms`이면 OFF; `partial_fill_ratio >= baseline + 10.0%p`는 경고이며 동시에 `loss_cap` 또는 `soft_stop_count/completed_trades >= 35.0%`이면 OFF; fallback 신규 1건 발생 즉시 OFF; canary 이후에도 `ai_confirmed_buy_count`가 main baseline 하위 3분위수보다 낮고 `blocked_ai_score_share`가 개선되지 않으면 OFF.
  - 판정: 완료. 코드 반영 + 테스트 + runtime 반영까지 종료.
  - 근거: `src/utils/constants.py`, `src/engine/sniper_state_handlers.py` 수정, `pytest 21 passed`, `src/bot_main.py` 재기동으로 실전 반영.
- [x] `[MainOnly0421] songstock 비교축 종료 + main-only baseline 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 서버 비교, 원격 canary, `remote_error` 해석을 현재 의사결정 입력에서 제거하고 `normal_only`, `post_fallback_deprecation`, `main-only missed_entry_counterfactual`만 기준으로 남긴다.
  - 판정: 완료. 오늘 rollback/source-of-truth 기준은 `main-only` 스냅샷(`trade_review`, `performance_tuning`, `post_sell_feedback`, `missed_entry_counterfactual`)으로 고정하고, `server_comparison/songstock/remote_error`는 현 의사결정 입력에서 제외한다.
  - 근거: `data/report/monitor_snapshots/server_comparison_2026-04-21.json`은 참고만 하며, 실제 판정표는 main snapshot에서 산출했다.
  - 운영 조치: `2026-04-21 21:52 KST` crontab에서 원격 서버 접속/수집 항목 `REMOTE_LATENCY_BASELINE_*`, `REMOTE_SCALPING_FETCH_1600`, `SHADOW_CANARY_*`를 제거했다. 재추가 방지를 위해 `deploy/install_stage2_ops_cron.sh`, `deploy/install_shadow_canary_check_cron.sh`도 원격 항목을 추가하지 않도록 정리했다.
- [x] `[PlanRebase0421] 용어 분리 잠금(entry_filter_quality vs buy_recovery_canary)` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 감사인 문맥의 `entry_filter_quality=불량 진입 감소/진입 품질 개선`과 오늘 실전 적용한 `buy_recovery_canary=Gemini WAIT 65~79 BUY 회복`을 문서 세트 전체에서 혼용하지 않도록 고정한다.
  - 판정: 완료. `entry_filter_quality`는 정식 품질개선/불량 진입 감소축이고, `buy_recovery_canary`는 WAIT 65~79 BUY drought 회복축이다. 두 축은 승격/롤백 기준을 공유하지 않는다.
- [x] `[AIPrompt0421] Gemini BUY drought main-only 계량` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, 최종갱신: 2026-04-21 15:37 KST`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 메인 로그 기준 `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79` 분포, `blocked_ai_score`, `buy_after_recheck_candidate`, `missed_winner_rate`를 같은 표로 잠근다.
  - 판정: BUY drought 지속. `ai_confirmed=744`, BUY `115`(`15.5%`), WAIT `474`(`63.7%`), DROP `155`(`20.8%`)다.
  - 근거: `ai_confirmed` WAIT 65~69 `222건`, 70~74 `5건`, 75~79 `4건`; raw `WAIT 65~79=231건`; `wait65_79_ev_candidate=54건`; `blocked_ai_score=612건`; `buy_after_recheck_candidate=0건`; `missed_entry_counterfactual.missed_winner_rate=74.8%`; `wait6579_ev_cohort.expected_fill_rate_pct=92.7037`, `avg_expected_ev_pct=0.9808`.
  - 다음 액션: 04-22 12:00 이후 `[AIPrompt0422]`에서 canary 이후 `ai_confirmed -> submitted` 개선 여부와 full/partial 분리를 재판정한다.
- [x] `[AuditResponse0421] 감사 응답 반영 상태와 timestamp/evidence 분리 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - 판정 기준: `체크리스트 예정 TimeWindow`, `실제 실행시각`, `근거 로그/스냅샷 시각`을 분리 기록한다. 사후 일괄 판정 시각은 실제 실행시각으로 쓰지 않는다.
  - 판정: 완료. 예정 TimeWindow는 원문 그대로 유지하고, 실제 실행시각은 `2026-04-21 15:24 KST`, 최종 evidence cutoff는 `monitor_snapshots=2026-04-21 15:37 KST`, `system_metric_samples=2026-04-21 15:30:01 KST`로 분리한다.
  - 재확인: `2026-04-21 15:37 KST` 수동 갱신으로 monitor snapshot 4종(`trade_review`, `performance_tuning`, `post_sell_feedback`, `missed_entry_counterfactual`)이 최종 갱신됐다.
- [x] `[AuditFix0421] HOLDING baseline 재계산 + 관측버퍼(D+1) 확인` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, 최종갱신: 2026-04-21 15:37 KST`)
  - 판정 기준: HOLDING baseline만 재계산하고, 성과판정은 D+2(`2026-04-22`)로 이관한다.
  - 판정: baseline 재계산 완료, 성과판정은 D+1/D+2 버퍼 유지. `post_sell_feedback` 기준 `total_candidates=9`, `missed_upside_rate=33.3%`, `good_exit_rate=55.6%`, `capture_efficiency_avg_pct=42.717`, `estimated_extra_upside_10m_krw_sum=53,001`.
  - 다음 액션: 04-22 POSTCLOSE `[AuditFix0422] HOLDING 성과 최종판정`에서 missed upside와 GOOD_EXIT를 확정한다.
- [x] `AIPrompt 작업 12 Raw 입력 축소 A/B 점검 범위 확정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - 판정 기준: 실패 시 별도 체크항목을 만들지 않고 이 항목 하위에 `사유 + 다음 실행시각`을 기록한다.
  - 판정: 범위 확정. Raw 입력 축소 A/B는 오늘 즉시 실전 적용하지 않고 `프로파일별 특화 프롬프트 canary`의 측정 컬럼으로 흡수한다.
  - 점검 범위: `ai_confirmed_buy_count/share`, WAIT 65/70/75~79, `blocked_ai_score`, `ai_confirmed->submitted`, full/partial 분리, `COMPLETED+valid profit_rate`.
  - 다음 실행시각: `2026-04-22 12:00~12:20 KST`, `[AIPrompt0422] 프로파일별 특화 프롬프트 canary 1차 계량 잠금`.
- [x] `[VisibleResult0421] 다음 영업일 canary 착수축 1개 고정 또는 보류 사유 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: Plan`) (`실행: 2026-04-21 12:18 KST`)
  - 판정 기준: 04-22 장전 적용 후보를 `main-only buy_recovery_canary`로 고정하거나, 코호트 근거상 보류해야 하면 사유와 다음 판정시각을 기록한다. 별도로 다음 정식 설계축은 `entry_filter_quality`로 유지한다.
  - 판정: 완료. 04-22 장전 후보는 `buy_recovery_canary`로 고정했고, 실제 적용은 조기 반영으로 선행 완료했다. 정식 다음축 명칭은 `entry_filter_quality`로 복원했다.
- [x] `[DataAudit0421] baseline source-of-truth audit 최종닫힘 및 rollback 기준 소스 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - 판정 기준: `trade_review=당일 손익`, `performance_tuning=퍼널/체결품질`, `post_sell_feedback=HOLDING`, `missed_entry_counterfactual=기회비용`을 고정하고 `rolling trend`와 문서 파생값을 rollback 기준에서 배제한다.
  - 판정: 완료. rollback 기준 소스는 `data/report/monitor_snapshots/trade_review_2026-04-21.json`, `performance_tuning_2026-04-21.json`, `post_sell_feedback_2026-04-21.json`, `missed_entry_counterfactual_2026-04-21.json`으로 고정한다.
  - 배제: `rolling trend`, 문서 파생값, `server_comparison/songstock` 비교값은 rollback trigger에서 제외한다.
- [x] `[QuantVerify0421] 감사 응답 정량 기대효과 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 최종갱신: 2026-04-21 15:37 KST`)
  - 기준선: `2026-04-20` `soft_stop_count=18`, `partial_fill_events=31`, `position_rebased_after_fill_events=44`, `partial_fill_completed_avg_profit_rate=-0.25`, `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=19917ms`, `latency_block_events/budget_pass_events=838/866`
  - 판정 기준: `soft_stop_count/partial_fill_events <= 0.46`, `position_rebased_after_fill_events/partial_fill_events <= 1.15`, `partial_fill_completed_avg_profit_rate >= -0.15`, `gatekeeper_fast_reuse_ratio >= 10.0%`, `gatekeeper_eval_ms_p95 <= 15900ms`, `ai_result_source=- 신규 표본 0건`
  - 표본 기준: `partial_fill_events < 20` 또는 `gatekeeper_eval_samples < 50`이면 hard pass/fail이 아니라 방향성 판정으로 기록하고, 방향성 판정은 2영업일 이내 재판정한다. 미재판정 시 자동 보류한다.
  - 판정: hard pass/fail 금지, 방향성은 미달. `partial_fill_events=7(<20)`, `position_rebased_after_fill_events/partial_fill_events=13/7=1.86(목표 1.15 초과)`, `partial_fill_completed_avg_profit_rate=-1.038%(목표 -0.15% 미달)`, `gatekeeper_fast_reuse_ratio=0.0%(목표 10.0% 미달)`, `gatekeeper_eval_ms_p95=17,594ms(목표 15,900ms 초과)`, `latency_block_events/budget_pass_events=4,848/4,858=99.8%`.
  - 근거: 표본 부족으로 승격 금지. 다만 기대값 관점에서는 latency guard miss와 partial fill 손실 증폭이 우선 해결 대상이다.
- [x] `[Workorder0421] 오늘 적용사항 결과검증 워크오더 실행 및 판정 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:40`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 최종갱신: 2026-04-21 15:37 KST`)
  - Source: [workorder-0421-validate-0420-applies.md](/home/ubuntu/KORStockScan/docs/workorder-0421-validate-0420-applies.md)
  - 판정 기준: 워크오더 지표를 전부 채우고 `canary 착수축 1개/보류축`을 분리해 `2026-04-22` 후속 액션을 같은 문서 세트에 기록한다.
  - 판정: 실행 완료. canary 착수축은 `main-only buy_recovery_canary`, 보류축은 `entry_filter_quality`, `AI engine A/B`, `프로파일별 특화 프롬프트 확대`다.
  - 근거: `docs/2026-04-21-auditor-performance-result-report.md`에 8개 이상 지표와 D/E/F 상태, 04-22 후속 액션을 기록했다.
- [x] `[AuditorDelivery0421] 감사인 전달용 성과측정결과 및 분석보고서 생성` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:10`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 최종갱신: 2026-04-21 15:37 KST`)
  - Source: [workorder-0421-auditor-performance-report.md](/home/ubuntu/KORStockScan/docs/workorder-0421-auditor-performance-report.md)
  - 판정 기준: 감사인 전달 문서 1건을 생성하고 지표 `8개 이상` + 미결 `D/E/F` 상태 + `2026-04-22` 후속 액션을 동일 보고에 명시한다.
  - 판정: 완료. 산출물: [2026-04-21-auditor-performance-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-21-auditor-performance-result-report.md).
- [x] `[OpsVerify0421] system metric sampler 장중 coverage 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:20`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 최종확인: 2026-04-21 15:37 KST`)
  - 판정 기준: `logs/system_metric_samples.jsonl`에서 `09:00~15:30 KST` 샘플 `>= 360`, 최대 샘플 간격 `<= 180초`, CPU/load/memory/io/top process 필드 누락 `0건`
  - 판정: 최종 통과. `09:00:01~15:30:01 KST` 샘플 `391건`, 평균 간격 `60.0초`, 최대 간격 `61초`, 필수 필드 누락 `0건`.
  - 재확인: `2026-04-21 15:32 KST` 기준 15:30 샘플까지 수집 완료.
- [x] `[PlanRebase0422] buy_recovery_canary 장전 적용` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:18 KST, 조기적용`)
  - Source: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)
  - 판정 기준: 04-21 장후 확정된 `main-only buy_recovery_canary`와 guard를 확인하고 canary ON 여부를 결정한다. 적용 시 같은 날 rollback 판정 시각을 문서에 남긴다.
  - 판정: 완료(조기적용). `WAIT 65~79` 2차 재평가 + `BUY promote>=75` 경로가 live 코드에 반영된 상태다.
- [x] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, Project stale due 이관`)
  - 판정 기준: `entry_filter_quality` canary 1차 판정이 완료됐으면 A/B 재개 여부를 결정한다. 3영업일 내 판정이 불충분하면 A/B 재개/추가보류를 별도 사유와 함께 기록한다.
  - 판정: 오늘 실행 대상 Project 항목은 이관 완료. 실제 판정은 `2026-04-24` 체크리스트에 별도 항목으로 유지한다.
- [x] `[Governance0422] GPT 엔진 금지패턴 및 AI 생성 코드 체크게이트 문서화` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, 문서화 선행 완료`)
  - 판정 기준: `fallback_scout/main` 동시 다중 leg 패턴 금지, AI 생성 코드의 의도-구현 일치/단위테스트/운영자 수동승인 체크게이트, `ai_generated/design_reviewed` 라벨링 규칙을 문서화한다.
  - 판정: 문서화 완료. 산출물: [2026-04-22-ai-generated-code-governance.md](/home/ubuntu/KORStockScan/docs/2026-04-22-ai-generated-code-governance.md).
- [x] `[AIPrompt0422] Gemini BUY recovery canary 1일차 판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, Project stale due 이관`)
  - 판정 기준: `2026-04-22` 오전 구간까지만 표본을 수집하고, `12:00` 이후 생성된 스냅샷 시점을 판정 고정 시점으로 사용한다. `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed -> submitted`, `missed_winner_rate`, `full fill / partial fill`을 main-only로 판정하고 유지/롤백/재교정 사유를 기록한다.
  - 판정: 오늘 Project due 정리/이관 완료. 실제 1일차 판정은 04-22 12:00 이후 데이터가 필요하므로 04-22 체크리스트에 동일 제목으로 유지한다.

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-19-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [workorder-0421-validate-0420-applies.md](./workorder-0421-validate-0420-applies.md)
- [workorder-0421-auditor-performance-report.md](./workorder-0421-auditor-performance-report.md)
- [workorder-0421-tuning-plan-rebase.md](./workorder-0421-tuning-plan-rebase.md)

<!-- REMOTE_COMPARISON_DECOMMISSIONED_START -->
### 원격 비교축 종료 기록 (`2026-04-21 21:52 KST`)

- 판정: `songstock` 원격서버는 운영 비교대상에서 제외한다.
- crontab 제거: `REMOTE_LATENCY_BASELINE_*`, `REMOTE_SCALPING_FETCH_1600`, `SHADOW_CANARY_*`
- 유지 cron: main-only 스냅샷(`RUN_MONITOR_SNAPSHOT_1000`, `RUN_MONITOR_SNAPSHOT_1200`), system metric sampler, dashboard archive, log cleanup, tuning monitoring postclose
- 손익/rollback 기준: `COMPLETED + valid profit_rate`가 있는 main-only 스냅샷만 사용한다.
<!-- REMOTE_COMPARISON_DECOMMISSIONED_END -->
