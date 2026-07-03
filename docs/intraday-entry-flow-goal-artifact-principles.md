# Intraday Entry Flow Goal Artifact Principles

Use this text when opening an intraday entry-flow monitoring goal. It keeps generated artifacts aligned with the fixed `data/report/intraday_entry_flow/` structure.

## Goal Text Block

```text
/goal <HH:MM:SS>부터 <HH:MM:SS> KST까지 10분 간격으로, 상승했거나 BUY 후보 단계까지 접근했으나 일반 BUY/submit/fill/holding/exit로 이어지지 못한 종목의 intraday entry flow를 진단한다. 단, `rising_missed_one_share_entry` 강제 1주 scout/매수 이벤트는 일반 BUY 병목, submit/fill 성공, rising_missed 해소 판정에서 제외하고 별도 관측값으로만 취급한다.

진단 목적은 모든 blocker를 동일하게 붙잡는 것이 아니라, BUY 제출/체결/보유/청산으로 이어질 수 있는 actionable major blocker에 감시예산과 수정예산을 집중하는 것이다. 회복 시도 후에도 source-quality가 해소되지 않는 종목은 빠르게 감시대상 큐에서 제외하여 다른 기회에 예산을 재할당한다.

목표는 손실 억제가 아니라 기대값과 순이익 최대화다. forced scout 1주 익절/손절은 일반 BUY 성공으로 세지 않는다. 이 라인은 별도 관측/기회비용 증거로 분리하고, 일반 BUY 병목, submit drought, fill 성공률, holding/exit 품질 판단과 혼합하지 않는다.

핵심 판정 순서:
1. decision: 해당 흐름이 유효한 source quality로 식별됐는지, sim/source-only로 적용됐는지, real runtime 반영까지 무엇이 남았는지 먼저 판정한다.
2. evidence: normal BUY/submit/fill, forced scout lineage, post-sell outcome, complete lifecycle 여부, stage-only bucket, submit drought, source-quality warning, cooldown/hard-safety, latency/freshness, strength/momentum/VPW, AI score near-buy, overbought/liquidity, bridge/live-auto 차단 사유를 분리한다.
3. next action: 즉시 코드개선 workorder, postclose 자동분석 handoff, 다음 PREOPEN `auto_bounded_live` 후보, 또는 monitor_only 중 하나로 정리한다.

운영 규칙:
- intraday runtime threshold mutation은 금지한다.
- broker submit guard, stale quote/price freshness, hard/protect/emergency stop, account/order/cooldown/quantity guard는 우회하지 않는다.
- forced scout 수익이 계속 나오고 normal submit BUY가 0이면 `window_submit_drought_observation`으로 기록한다. 단, 공식 critical 판단은 BUY Funnel Sentinel의 일중/일간 floor와 submitted/AI, submitted/budget 기준을 함께 본다.
- rising missed 1주 결과는 기회비용/후보 증거로 사용하되 real-order enablement, cap release, provider 변경, bot restart, hard safety 완화의 직접 근거로 쓰지 않는다.
- source-quality unrecoverable row는 빠르게 제외하고 예산을 actionable major blocker에 재배치한다.
- clean tuning baseline은 `2026-06-04T14:29:09+09:00 KST` 이후 데이터만 사용한다. 이전 raw/report/analytics는 archive/audit evidence 전용이다.
- hot runtime pressure relief는 수동 조정에만 의존하지 않도록 자동 관측/자동 조절 가능한 구조를 우선 고려한다. 빈번히 바뀌는 값은 봇 재기동 없이 동적 반영되도록 설계한다.
- 실매매 한정 운영 압력 완화나 관측 보강이 기존 승인된 runtime family/override 범위 안에서 필요한 경우에만 provenance와 rollback 값을 남긴다. 실주문 권한, hard guard 완화, threshold 변경, provider 변경, bot restart가 필요하면 먼저 사용자에게 보고한다.
- graceful restart는 `restart.flag` 방식을 우선 사용한다. runtime 반영 실패가 확인될 때에만 프로세스 kill을 검토한다.

산출물 원칙:
- intraday 중에는 `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_current.md`만 overwrite 갱신한다.
- intraday_entry_flow report는 timestamp별 md/csv 스냅샷을 누적 보존하지 않는다.
- flow md는 반드시 고정 갱신 파일 `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_current.md`에 덮어쓴다.
- flow csv가 필요하면 `/tmp/intraday_entry_flow_YYYY-MM-DD_<window>.csv`로 임시 생성하고, 최종 확인 후 삭제한다.
- 목표 종료 시에는 최종 안정화 문서만 1회 `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_<HHMM>_to_<HHMM>_final_stabilization.md`로 남긴다.
- final stabilization의 `source_flow_final`은 timestamp 스냅샷이 아니라 `intraday_entry_flow_YYYY-MM-DD_current.md`를 가리키게 한다.
- 중간 `intraday_entry_flow_YYYY-MM-DD_*_to_*.md/.csv`가 생겼으면 목표 종료 전에 삭제한다.
- code-review 누적 기록은 `docs/code-reviews/intraday-entry-flow-operational-log.md`에 결정/변경/검증/운영경계 단위로만 추가한다. 10분 루프별 숫자는 누적 기록 문서에 붙이지 않는다.

postclose 자동 handoff:
- `rising_missed_intraday_feedback`
- `rising_missed_scout_workorder`
- `rising_missed_first_touch_calibration`
- `one_share_threshold_opportunity`
- `code_improvement_workorder`

위 postclose 산출물은 source-only/code-improvement 후보를 만들 수 있지만, real runtime 반영은 다음 PREOPEN의 `auto_bounded_live` env 선택과 hard safety guard를 통과해야 한다.

시간 규칙:
- `<HH:MM:SS>`부터 `<HH:MM:SS>` KST까지 10분 간격으로 확인한다.
- 매수 가능 창 밖에서는 새 BUY 병목 판정을 확장하지 않고 pause/monitor_only로 둔다.
- 기준 매수 창은 `KORSTOCKSCAN_SCALPING_BUY_WINDOWS=08:03:00-08:40:00,09:03:00-15:20:00,16:00:00-19:45:00`이다.
- 목표 종료 시각 이후에는 goal을 종료하고 final stabilization만 남긴다.

blocker 분류:
1. `actionable_major_blocker`: 코드 수정, 관측 보강, runtime pressure relief, `restart.flag` 재기동 등으로 해소 가능하며 BUY 제출/체결 흐름을 실질적으로 막는 병목.
2. `intended_guard`: stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency stop 등 정상 보호장치. 우회하지 않고 major blocker로 집계하지 않는다.
3. `runtime_backpressure_observation`: scanner full-eval budget deferred 등 자동 governor가 동적으로 조절하거나 이후 평가로 회복 가능한 압력 관측. 반복되더라도 submit 병목으로 단정하지 않고 governor 효과와 deferred-then-evaluated 여부를 먼저 본다.
4. `source_quality_exclusion_candidate`: REST quote, WS REG/recheck, subscription recheck snapshot 적용을 시도했는데도 WS tick/strength/history가 회복되지 않는 종목. 반복되면 병목으로 붙잡지 말고 감시대상 큐에서 제외해 예산을 회수한다.

판정 원칙:
1. forced scout / rising_missed_one_share_entry는 일반 BUY submit 성공으로 세지 않는다.
2. forced scout 제외 residual과 forced scout residual을 분리한다.
3. latency_state_danger는 stale quote 단정이 아니라 spread/latency pre-submit 품질가드로 root cause를 분해한다.
4. known preserved quality guard와 unknown/actionable latency danger를 분리한다.
5. threshold/order/provider/bot 변경 없이 diagnostic/source-quality 범위에서만 판단한다.
6. 동일 actionable_major_blocker가 2회 이상 반복되면 root cause를 분해하고 최소 1개 이상의 해소 조치를 검토한다. `stale_or_delayed_eval`은 diagnostic stale, full-eval 지연, WS quote 결손, pre-AI stale, pre-submit hard stale로 분리한다.
7. price-only REST quote recovery, no-tick, subscription alive but no 0B tick처럼 BUY 제출 가능성을 높이지 못하고 감시예산만 소모하는 유형은 source-quality exclusion 또는 watch-budget reallocation으로 처리한다.
8. `scanner_full_eval_loop_budget_deferred`는 기본적으로 runtime backpressure observation이다. `deferred_then_evaluated`는 major blocker에서 제외하고, `deferred_never_evaluated` high-delta 후보가 반복될 때만 actionable pressure 병목으로 승격한다.
9. `entry_cooldown_active`는 intended guard다. cooldown이 감시 슬롯을 오래 점유하면 BUY guard 완화가 아니라 pool rotation/예산회수 대상으로 처리한다.
10. 익절 발생 시 트레일링 과정을 분석하고 익절 이후 상승 MFE 분포 기반으로 익절 로직 개선 후보를 분리한다.
11. 미체결 상승종목 중 entry price 때문에 체결되지 않은 유형은 주문가/취소대기/체결품질 병목으로 별도 분석한다.
12. 보유중 손절선 터치 및 손절 청산 발생 시 감시부터 청산까지 분석하고, 6월 이후 전체 손절 데이터와 누적하여 유형을 분리한다. 필요한 경우 MFE 분포 기반 추천선 및 stop-loss recovery backtest 후보로 넘긴다.
13. 하나의 blocker에 집착하지 말고 매 루프에서 전체 blocker 분포를 재검토한다. major issue 우선순위는 actionable_major_blocker 중 submit/fill 전환 가능성이 높은 것부터 둔다.
14. 가격, 수량, WS/quote, scanner source, strength/momentum, liquidity, account/order context에서 `0`, `0.0`, `"0"`, missing-to-zero fallback이 block/fallback/skip/fail로 이어진 사례를 별도 집계한다. `actual_zero`, `missing_defaulted_zero`, `stale_defaulted_zero`, `not_applicable_zero`, `guard_intended_zero`를 분리한다.
15. 동일한 `missing_defaulted_zero` 또는 `stale_defaulted_zero`가 2회 이상 반복되고 유효한 대체 원천값이 같은 시점에 존재하거나 기존 guard 전에 0으로 잘못 접힌 정황이 확인되면 코드 버그픽스 후보로 승격한다.
16. 버그픽스는 stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency stop guard를 우회하지 않으며 threshold mutation 없이 provenance 보강, fallback 위치 조정, fail-closed 복원, structured diagnostics 추가, 감시대상 제외/예산회수 로직 보강 중 최소 1개 이상으로 제한한다.
17. 동일 세션에서 이미 수정한 로직을 다시 개선할 때는 누적 관측 데이터를 먼저 확인하고 개선 방향을 수립한다.
18. 모든 actionable_major_blocker가 해소되어 남은 항목이 intended_guard, runtime_backpressure_observation, source_quality_exclusion_candidate의 정상 회전, 또는 submit/fill 이후 보유/청산 관측뿐이면 신규 완화/코드수정을 중단한다.
19. 목표 종료 전 최소 1개 루프에서 rising missed BUY의 actionable_major_blocker 잔여, `deferred_never_evaluated` high-delta 후보, price-only/no-tick/source-quality churn 회전, pre-submit hard stale 및 broker/account/order/quantity/cooldown/hard stop guard 유지, 실제 submit/fill/holding/exit report 반영 여부를 확인한다.
20. 위 조건을 만족하면 final stabilization report를 남기고 코드/override 변경을 더 하지 않는다.
21. runtime override를 적용한 경우 rollback 값, effective 값, 적용 시각, 재기동 여부를 변경목록에 남긴다. 문제가 없으면 장중 임의 rollback은 하지 않고 postclose attribution 또는 다음 PREOPEN 판단으로 넘긴다.
22. 검증이 끝난 코드 변경 단위는 자체 리뷰와 테스트 통과 후에만 publish 대상으로 본다. 이후 목표는 `monitor_only` 상태로 전환하고 새 actionable blocker가 다시 발생할 때만 해소 루프를 재개한다.
```

## Required Final Cleanup

- Confirm only the fixed current flow artifact and final stabilization summaries remain for the target date.
- Confirm temporary CSV output is gone.
- Confirm final stabilization summaries do not point to deleted timestamp snapshots.
- Add one concise operational-log entry only when the goal changes a durable rule, source-quality contract, report contract, or artifact retention decision.

## Forbidden Uses

- Do not use intraday flow diagnostics to mutate runtime thresholds intraday.
- Do not treat forced one-share scout events as normal BUY submit/fill success.
- Do not bypass stale quote, latency DANGER, spread, broker/account/order/quantity/cooldown, hard/protect/emergency guards.
- Do not use final stabilization summaries as standalone EV or real execution quality approval evidence.
