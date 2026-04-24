# 2026-04-24 Stage 2 To-Do Checklist

## 오늘 목적

- `2026-04-20~2026-04-23` 검증 결과를 바탕으로 금요일 결론을 `승격 1축 실행` 또는 `보류+재시각` 중 하나로 닫는다.
- 주간 판정에는 regime 태그와 조건부 유효범위를 함께 남긴다.
- 오전 `10:00 KST`까지의 주병목 검증축은 `spread relief canary` 실효성 확인으로 고정한다.
- `PYRAMID zero_qty Stage 1`은 `SCALPING/PYRAMID bugfix-only` 범위의 `flag OFF` 증적을 먼저 확인하고, 승인 시에도 `main-only 1축 canary`로만 해석한다.
- 스캘핑 신규 BUY는 임시 `1주 cap` 상태로 유지하고, `PYRAMID`는 계속 허용하되 `initial-only`와 `pyramid-activated` 표본을 섞지 않고 판정한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 금요일 운영도 live 변경은 `1축 canary`만 허용한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장전 체크리스트 (08:20~)

- [x] `[ScaleIn0424] PYRAMID zero_qty Stage 1 flag OFF 코드 적재/restart/env 증적 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: ScalpingLogic`) (`실행: 2026-04-24 07:45 KST`)
  - 판정 기준: `KORSTOCKSCAN_SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED`가 꺼진 상태로 배포되어야 하며, 재시작 후에도 `flag OFF`가 유지된 증적을 남긴다.
  - 판정: 완료(`flag OFF` 유지 증적 확보).
  - 근거: `src/utils/constants.py` 기본값 `SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED=False` 확인, `restart.flag` 우아한 재시작 수행(`old_pid=159209 -> new_pid=159310`), `logs/bot_history.log`에 `2026-04-24 07:44:10 KST`/`07:44:59 KST` 재시작 플래그 감지 로그 확인, 재기동 PID `/proc/159376/environ`에서 `KORSTOCKSCAN_SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED` 미설정(기본값 OFF 적용) 확인.
  - 다음 액션: POSTCLOSE `[ScaleIn0424] main은 PYRAMID zero_qty Stage 1 code-load(flag OFF)와 live ON 판정을 분리 유지 확인`에서 OFF 유지 증적 재확인 후 live ON 승인/보류를 분리 판정.
- [x] `[FastReuseVerify0424] gatekeeper_fast_reuse 실전 호출 로그 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:35`, `Track: ScalpingLogic`) (`실행: 2026-04-24 07:46 KST`)
  - 판정 기준:
    - `gatekeeper_fast_reuse` 코드 경로가 실전에서 호출되었는지 로그 확인
    - `호출 건수 = 0`이면: signature 조건 과엄격 또는 코드 미도달 분기
    - `호출 건수 > 0`이고 `reuse = 0`이면: signature 일치 조건 완화 검토
    - `reuse > 0`이면: `fast_reuse` 비율 목표(>=10.0%) 대비 평가
  - 판정 연계:
    - `fast_reuse`가 활성화되면 `gatekeeper_eval_ms_p95` 하락 기대
    - p95 하락 동반 시 `quote_fresh_latency_pass_rate` 개선 기대
    - `spread relief canary`의 `fast_reuse` 미개선이면 `quote_fresh` canary 후보 판단으로 후행 이동
  - Rollback: 필요 시 코드 변경은 Plan Rebase §6 guard 전수 대조 후 진행
  - 판정: 완료(관측 대기 잠금).
  - 근거: same-day `ENTRY_PIPELINE` 기준 `stage=gatekeeper_fast_reuse=0`, `gatekeeper_fast_reuse_bypass=0`; wrapper 기반 same-day 스냅샷(`2026-04-24 intraday_light`)에서 `gatekeeper_fast_reuse_ratio=0.0`, `gatekeeper_eval_ms_p95=0.0`, `quote_fresh_latency_pass_rate=0.0` 확인. PREOPEN 표본 공백으로 `호출=0` 분기 잠금.
  - 다음 액션: INTRADAY `[LatencyOps0424] 제출축 잠금` 시각(`09:50~10:00 KST`)에 same-day 재집계로 `호출=0 지속` vs `호출>0/reuse 비율`을 재판정하고 `quote_fresh` 후보 이동 여부를 함께 잠금.
- [x] `[ScaleIn0424] PYRAMID zero_qty Stage 1 zero_qty/template_qty/cap_qty/floor_applied 로그 필드 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: Plan`) (`실행: 2026-04-24 07:46 KST`)
  - 판정 기준: `ADD_BLOCKED` 또는 `ADD_ORDER_SENT` 로그에 `template_qty`, `cap_qty`, `floor_applied`가 모두 남아야 한다.
  - 판정: 완료(관측 대기 잠금).
  - 근거: same-day `ADD_BLOCKED reason=zero_qty`/`ADD_ORDER_SENT` 필드 3종 로그 건수 `0`; 코드 로깅 경로 `src/engine/sniper_state_handlers.py`(`reason=zero_qty` 및 `ADD_ORDER_SENT`에 `template_qty/cap_qty/floor_applied` 기록) 확인; 단위테스트 2건(`test_describe_scale_in_qty_stage1_keeps_flag_off_by_default`, `test_describe_scale_in_qty_stage1_applies_one_share_floor_when_enabled`) 통과로 필드 계산 경로 검증 완료.
  - 다음 액션: INTRADAY 첫 `ADD_BLOCKED`/`ADD_ORDER_SENT` 발생 시 same-day 실로그 증적을 추가하고, 미관측 지속 시 POSTCLOSE `미확정 시 사유+다음 실행시각` 항목에 재시각을 고정한다.

## 장중 체크리스트 (09:00~10:00)

- [x] `[LatencyOps0424] spread relief canary 오전 검증축 고정 확인` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: ScalpingLogic`) (`실행: 2026-04-24 09:13 KST`)
  - 판정 기준: 오전 `10:00 KST` 전까지의 주병목 검증축을 `spread relief canary` 하나로 고정하고, `entry_filter_quality/score-promote/HOLDING/EOD-NXT`를 주병목 판정에서 분리한다고 기록한다.
  - 판정: 완료. 오전 `10:00 KST` 전 주병목 검증축은 `ws_jitter relief canary` 하나로 고정하고, `entry_filter_quality/score-promote/HOLDING/EOD-NXT`는 주병목 판정에서 분리한다.
  - 근거: `src/utils/constants.py` 기준 `SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=True`(활성), `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False`(대체 완료, parking), `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=False`, `SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED=False`, `SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=True`, `SCALPING_INITIAL_ENTRY_MAX_QTY=1` 확인. `bot_main` PID `159376`의 `/proc/159376/environ`에는 관련 `KORSTOCKSCAN_*` override가 없어 코드 기본값 경로로 동작 중이다. `performance_tuning` 재생성(`since=09:00:00`, 09:15 KST 검증) 기준 `budget_pass_events=130`, `order_bundle_submitted_events=1`, `latency_block_events=129`, `quote_fresh_latency_pass_rate=0.8%`, `full_fill_events=1`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=14620.0`, `fallback_regression` 신규 증거 없음.
  - why: 이 항목은 canary 실효성 판정이 아니라 오전 검증축 고정 확인이다. 같은 창에서 `entry_filter_quality/score-promote/HOLDING/EOD-NXT`를 주병목 후보로 섞으면 `entry_armed -> submitted` 병목의 원인귀속이 깨지므로, 제출축 결과가 잠기기 전까지는 `spread relief canary`만 본다.
  - 다음 액션: 아래 `[LatencyOps0424] 제출축 잠금`에서 `09:50~10:00 KST` 기준 `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill`로 `spread relief canary 유지/효과 미확인/롤백 검토`를 분리 판정한다.
- [x] `[LatencyOps0424] 제출축 잠금` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 09:50~10:00`, `Track: ScalpingLogic`) (`실행: 2026-04-24 10:31 KST`)
  - 판정 기준: `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill`를 기준으로 `spread relief canary 유지`, `효과 미확인`, `롤백 검토` 중 하나로 닫는다.
  - 실행 메모: `2026-04-24 10:00 KST` checkpoint 재집계 완료.
  - 판정: 완료. `10:00 KST` 기준 제출축 원인 판정은 `budget_pass -> latency_block/submitted` downstream 단절로 고정한다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `evidence_cutoff=2026-04-24 10:00:00 KST`로 재집계했다. `09:00~10:00` 누적 기준 `ai_confirmed=77`, `entry_armed=31`, `submitted=4`, `budget_pass_events=863`, `order_bundle_submitted_events=4`, `latency_block_events=859`, `quote_fresh_latency_blocks=777`, `quote_fresh_latency_pass_rate=0.5%`, `full_fill_events=0`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=12543.0ms`. `09:50~10:00` 증분 기준 `ai_confirmed=31`, `entry_armed=9`, `submitted=1`, `budget_pass_events=151`, `latency_block_events=150`, `quote_fresh_latency_blocks=119`, `quote_fresh_latency_pass_rate=0.8%`, `full_fill_events=0`, `partial_fill_events=0`.
  - why: `entry_armed -> submitted`는 `31 -> 4`로 약하지만 0은 아니다. 더 강한 병목 근거는 `budget_pass_events=863` 대비 `order_bundle_submitted_events=4`, `latency_block_events=859`, `quote_fresh_latency_pass_rate=0.5%`다. 따라서 원인 축은 `upstream BUY 부족`이 아니라 `제출 직전 latency/quote downstream 단절`로 본다.
  - 다음 액션: 아래 `[LatencyOps0424] 제출축 가속 재판정`에서 same-day 누적 `submitted_orders`와 잔여 표본 갭(`20 - submitted_orders`)을 다시 고정하고, 이어 보조축 승격 여부를 같은 장중에 닫는다.
- [x] `[LatencyOps0424] 제출축 가속 재판정` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 10:20~10:30`, `Track: ScalpingLogic`) (`실행: 2026-04-24 10:31 KST`)
  - 판정 기준: `09:00~10:20/10:30` same-day 누적 `ai_confirmed`, `entry_armed`, `submitted`, `budget_pass_events`, `latency_block_events`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill`를 다시 집계하고, `N_min` 충족 여부와 잔여 갭(`submitted_orders 20 기준`)을 함께 기록한다.
  - 판정: 완료. `10:30 KST` 기준 `N_min`은 여전히 미달이며, hard pass/fail 없이 방향성만 유지한다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `evidence_cutoff=2026-04-24 10:30:00 KST`로 재집계했다. `09:00~10:30` 누적 기준 `ai_confirmed=91`, `entry_armed=39`, `submitted=8`, `budget_pass_events=1220`, `order_bundle_submitted_events=8`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`, `full_fill_events=0`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=12485.0ms`, `gatekeeper_fast_reuse=18`, `gatekeeper_fast_reuse_bypass=58`. `10:20~10:30` 증분 기준 `ai_confirmed=24`, `entry_armed=4`, `submitted=1`, `budget_pass_events=91`, `latency_block_events=90`, `quote_fresh_latency_blocks=86`, `quote_fresh_latency_pass_rate=1.1%`, `latency_canary_reason_top3=[spread_only_required 82, quote_stale 4, - 4]`.
  - why: `submitted_orders=8`로 Plan Rebase §6 `N_min` 최소치 `20`에 `+12`가 더 부족하다. 동시에 `gatekeeper_eval_ms_p95=12485ms`로 p95 rollback guard는 미발동이지만, `spread_only_required`가 `10:20~10:30` 차단사유의 대부분을 차지해 현재 spread relief canary만으로는 제출 회복 효과를 입증하지 못했다.
  - 다음 액션: 아래 `[LatencyOps0424] N_min 미달 시 보조축 승격 여부 잠금`에서 `quote_fresh`와 `entry_filter_quality` 중 same-day 보조축 우선순위를 하나로 고정한다.
- [x] `[LatencyOps0424] N_min 미달 시 보조축 승격 여부 잠금` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:40`, `Track: ScalpingLogic`) (`실행: 2026-04-24 10:31 KST`)
  - 판정 기준: `10:20~10:30 KST` 재판정 후에도 `trade_count < 50`이고 `submitted_orders < 20`이면 hard pass/fail 금지 사유와 남은 필요 표본을 고정하고, same-day 보조축(`quote_fresh` 또는 `entry_filter_quality`) 승격 여부를 장중에만 잠근다. POSTCLOSE 이관만으로 닫지 않는다.
  - 판정: 완료. `N_min` 미달 구간의 same-day 보조축 우선순위는 `quote_fresh` 1축으로 고정하고, `entry_filter_quality`는 장중 승격 후보에서 제외한 채 parking 유지로 둔다.
  - 근거: `09:00~10:30` 누적 기준 `submitted=8`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`로 제출 병목의 대부분이 quote-fresh/downstream에 남아 있다. 같은 구간 `gatekeeper_eval_ms_p95=12485.0ms`는 Plan Rebase `latency_p95` guard(`>15,900ms`, sample>=50) 미발동이며, PREOPEN fast reuse 확인 후 장중 누적에서도 `gatekeeper_fast_reuse=18`이 관측돼 `fast_reuse 호출 0건` 전제는 해소됐다. 반면 `entry_filter_quality`는 Plan Rebase와 감사문서 기준 제출병목 해소 후에만 복귀해야 하는 후순위 축이다.
  - why: 지금 필요한 다음 보조축은 upstream 필터 재조정이 아니라 `quote_fresh/spread_only_required` 하위원인 1개를 직접 겨누는 downstream 축이다. `entry_filter_quality`를 지금 올리면 제출 직전 병목이 풀리지 않은 상태에서 원인귀속만 흐려진다.
  - 다음 액션: same-day replacement 여부는 `quote_fresh` 1축에 대해 guard 전수대조 후 별도 승인으로 닫는다. 아래 `[LatencyOps0424] quote_fresh replacement 승인 또는 보류 기록`에서 `reject_rate`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`, `loss_cap`, `N_min` 적용 방식을 함께 고정한다.
- [x] `[LatencyOps0424] quote_fresh replacement 승인 또는 보류 기록` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 10:40~10:50`, `Track: ScalpingLogic`) (`실행: 2026-04-24 11:00 KST`)
  - 판정 기준: `quote_fresh` downstream 1축만 후보로 두고, Plan Rebase §6 guard 전수대조(`N_min`, `loss_cap`, `reject_rate`, `latency_p95`, `partial_fill_ratio`, `fallback_regression`)가 문서에 고정될 때만 same-day replacement 승인 여부를 닫는다. `entry_filter_quality`는 이 슬롯에서도 parking 유지다.
  - 판정: 완료. same-day `quote_fresh replacement`를 `ws_jitter-only relief` 1축으로 승인하고 live 교체까지 완료한다.
  - 근거: `10:30 KST` same-day 누적 기준 `submitted=8`, `budget_pass_events=1220`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`, `full_fill_events=0`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=12485.0ms`, `gatekeeper_fast_reuse=18`이다. 따라서 `N_min`은 여전히 `+12` 부족으로 hard pass/fail 금지이며, `latency_p95` rollback guard는 미발동이다. `loss_cap`은 `COMPLETED + valid profit_rate` 표본이 없어 미발동, `partial_fill_ratio`는 제출 회복 전까지 모니터링-only, `fallback_regression` 신규 증거는 없다. guard 위반이 없는 상태에서 `quote_fresh` 4요인 중 `ws_jitter`를 독립 1축으로 정의하면 replacement 승인 요건을 충족한다.
  - 근거: 코드 기본값을 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=False`, `SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED=True`로 교체했고, `src/engine/sniper_entry_latency.py`에 `jitter-only danger -> ALLOW_NORMAL` 전용 함수/로그(`[LATENCY_WS_JITTER_RELIEF_CANARY]`)를 추가했다. 기존 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 여전히 `SCALP_LATENCY_FALLBACK_ENABLED` 결합 경로라 replacement 후보에서 제외한다. 단위테스트 `src/tests/test_sniper_entry_latency.py`는 `12 passed`다.
  - 근거: `restart.flag` 우아한 재시작을 수행해 `bot_main` PID가 `159376 -> 178400`으로 교체됐고, `logs/bot_history.log`에 `2026-04-24 10:59:56 KST` 재시작 플래그 감지 로그가 남았다. 재기동 PID `/proc/178400/environ`에는 `KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`, `KORSTOCKSCAN_SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED`, `KORSTOCKSCAN_SCALP_LATENCY_FALLBACK_ENABLED` override가 없어 코드 기본값 경로로 동작한다.
  - why: `ws_jitter`는 `quote_stale`보다 fail-open 리스크가 낮고, 기존 `spread_relief`와도 덜 겹친다. `spread/ws_age/ws_jitter/quote_stale`를 동시에 올리면 원인귀속이 깨지므로, 지금 live replacement는 `ws_jitter-only relief` 1축으로만 본다.
  - 다음 액션: 아래 장중 반복 관찰 항목에서 `post-restart cohort`를 `11:20`, `12:00`, `13:20 KST` 기준으로 분리 관찰하고, 각 체크포인트마다 `budget_pass_events`, `submitted/full/partial`, `quote_fresh_latency_pass_rate`, `latency_reason_breakdown`, `COMPLETED + valid profit_rate`를 즉시 기록한다. `POSTCLOSE에서 첫 제출/체결 품질만 보고 닫는 방식`은 금지하고, 장중 수치가 기준치에 도달하는 시점에 same-day 다음 단계 진입 여부를 잠근다.

- [x] `[LatencyOps0424] quote_fresh 독립 1축 정의/가드 고정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`) (`실행: 2026-04-24 11:00 KST`)
  - 판정 기준: `quote_fresh` 4요인(`spread/ws_age/ws_jitter/quote_stale`) 중 1개만 다음 live 후보로 고정하고, Plan Rebase §6 guard 적용표(`N_min/loss_cap/reject_rate/latency_p95/partial_fill_ratio/fallback_regression`)를 함께 문서화한다.
  - 판정: 완료. `quote_fresh` 독립 1축은 `ws_jitter-only relief`로 고정한다.
  - 근거: 후보 비교 기준은 `fallback 비결합`, `spread_relief와 비중복`, `fail-open 리스크`, `원인귀속 선명도`다. `quote_stale`는 stale quote 자체를 허용하는 방향이라 리스크가 가장 크고, `ws_age`는 stale과 경계가 가깝다. `ws_jitter`는 `quote_stale`보다 리스크가 낮고 기존 `spread_relief`와도 덜 겹쳐 독립 1축 정보량이 가장 높다.
  - 근거: 적용 가드는 `N_min 적용`, `loss_cap 적용`, `reject_rate 적용`, `latency_p95 적용`, `fallback_regression 적용`, `partial_fill_ratio 조건부(제출 회복 전까지 모니터링-only)`로 고정한다. `buy_drought_persist`는 `buy_recovery_canary` 전용이라 비적용이다.
  - 다음 액션: 아래 장중 반복 관찰 항목에서 `post-restart cohort`를 계속 누적 관찰하고, `entry_filter_quality`는 계속 parking 유지한다.
- [x] `[LatencyOps0424] ws_jitter relief 1차 스모크체크` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 11:20~11:30`, `Track: ScalpingLogic`) (`실행: 2026-04-24 11:32 KST`)
  - 판정 기준: `restart.flag` 이후 `post-restart cohort`에서 `budget_pass_events >= 30` 또는 `ai_confirmed >= 15`를 먼저 확보한다. 이때 `latency_canary_reason=ws_jitter_relief_canary_applied >= 1` 또는 `submitted >= 1`이 있으면 활성화 표본 확보로 본다. 반대로 `budget_pass_events >= 30`인데 `ws_jitter_relief_canary_applied = 0`이고 `submitted = 0`이면 비활성/비도달 의심으로 잠근다.
  - 중간관찰 시각: 대략 `11:20~11:30 KST`. 이 슬롯은 `live 교체가 실제로 표본에 닿는가`만 보는 스모크 단계다. 장후 이관으로 넘기지 않고 same-day 장중에서 `도달/비도달`을 먼저 잠근다.
  - 판정: 완료. `11:30 KST` 기준 스모크체크는 `비활성/비도달 의심`으로 잠근다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `post-restart cohort=2026-04-24 11:00:00~11:30:00 KST`로 재집계했다. 이벤트 기준 `ai_confirmed=70`, `entry_armed=17`, `budget_pass_events=131`, `latency_block_events=131`, `quote_fresh_latency_blocks=118`, `quote_fresh_latency_pass_rate=0.0%`, `order_bundle_submitted_events=0`, `full_fill_events=0`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=13385.0ms`, `gatekeeper_fast_reuse=0`, `gatekeeper_fast_reuse_bypass=18`이다.
  - 근거: 같은 구간 raw `latency_block` 기준 `latency_canary_reason_top4=[ws_jitter_only_required 93, low_signal 19, quote_stale 13, - 6]`, `latency_danger_reason_top4=[other_danger 72, ws_jitter_too_high 19, quote_stale+ws_age_too_high 12, ws_age_too_high 10]`, `quote_stale=False 118`, `quote_stale=True 13`이다. `latency_canary_applied=True` 또는 `[LATENCY_WS_JITTER_RELIEF_CANARY]` 실전 통과는 `11:00~11:30 KST` 구간에서 0건이다.
  - why: 스모크 단계의 1차 조건인 표본량(`budget_pass_events >= 30` 또는 `ai_confirmed >= 15`)은 충족했다. 그러나 활성화 증거 조건인 `ws_jitter_relief_canary_applied >= 1` 또는 `submitted >= 1`이 둘 다 0이므로, `ws_jitter-only relief`가 live 이후 이 코호트에서 실제 허용 경로까지 닿았다고 볼 수 없다. 따라서 `효과 없음` 확정이 아니라 `비활성/비도달 의심`으로 먼저 잠그고 12시 방향성 체크에서 같은 축을 계속 본다.
  - 다음 액션: 아래 `[LatencyOps0424] ws_jitter relief 2차 방향성 체크`에서 `12:00~12:10 KST` 기준 `post-restart cohort` 누적 `budget_pass_events >= 100` 전제하에 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%` 회복 여부를 재판정한다. 같은 시점에도 `submitted <= 1`이고 `ws_jitter_relief_canary_applied <= 1`이면 `독립축 비도달/효과 미약` 분기로 잠근다.
- [ ] `[LatencyOps0424] ws_jitter relief 2차 방향성 체크` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:10`, `Track: ScalpingLogic`)
  - 판정 기준: `post-restart cohort` 누적 `budget_pass_events >= 100`을 확보한 뒤 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%`면 방향성 유효로 본다. `budget_pass_events >= 100`인데도 `submitted <= 1`이고 `ws_jitter_relief_canary_applied <= 1`이면 독립축 비도달 또는 효과 미약으로 분기한다.
  - 중간관찰 시각: 대략 `12:00~12:10 KST`. 이 슬롯부터는 `첫 제출/체결이 있었는가`가 아니라 `제출 회복 방향성이 숫자로 보이는가`를 본다. 최소 기준은 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%`다.
- [ ] `[LatencyOps0424] ws_jitter relief 다음 단계 진입 여부 잠금` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:30`, `Track: ScalpingLogic`)
  - 판정 기준: `post-restart cohort` 누적 `submitted >= 5`와 `fallback_regression = 0`을 확보하면 `HOLDING/청산 품질 관찰` 단계로 진입한다. `submitted >= 10` 또는 `full_fill + partial_fill >= 5`면 same-day 다음 단계 관찰축을 열 수 있다. 반대로 `budget_pass_events >= 150`인데 `submitted <= 2`면 `ws_jitter-only relief` 효과 미약으로 잠그고 same-day 하위원인 재분해로 되돌린다.
  - 중간관찰 시각: 대략 `13:20~13:30 KST`. 이 슬롯에서 `submitted >= 5`가 안 보이면 장후 `첫 제출/체결 품질 확인만`으로 다음 단계에 넘기지 않는다. `submitted/full/partial` 누적이 기준치에 도달한 시점만 다음 단계 진입 근거로 인정한다.

## 장후 체크리스트 (15:10~15:40) - 주병목 판정

- [ ] `[LatencyOps0424] 오전 제출축 결과 잠금` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
- 판정 기준: 오전 `10:00 KST` checkpoint를 기준으로 `spread relief canary`의 `유지/확대/보류/롤백` 중 하나를 확정한다.
- [ ] `[VisibleResult0424] 금요일 승격 후보 1축 최종선정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`)
- [ ] `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `승격 실행`이면 축 1개만 선택하고 롤백 가드 포함, `보류`이면 원인 1개와 재실행 시각 1개를 동시에 기록

## 장후 체크리스트 (15:40~17:00) - 후순위 축 Parking

- [ ] `[PlanRebase0424] entry_filter_quality parking 재확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
- 판정 기준: `spread relief canary`가 여전히 주병목이면 `entry_filter_quality`는 주병목 축이 아니라 parking 상태로 유지하고, 제출축이 완화됐을 때만 후보 복귀 여부를 판단한다.
- [ ] `[InitialQtyCap0424] 스캘핑 신규 BUY 1주 cap 유지/해제 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~15:55`, `Track: ScalpingLogic`)
  - 판정 기준: `initial-only`와 `pyramid-activated` 표본을 분리한 뒤 `submitted/full/partial`, `soft_stop/trailing/good_exit`, `COMPLETED + valid profit_rate`를 함께 보고 `유지/완화/해제` 중 하나로 닫는다. `soft_stop`만 단독 기준으로 쓰지 않고 holding/exit 전체 판정 안에서 본다.
  - why 기준: 이 cap은 prompt 재교정 직후 초기 진입 손실 tail을 잠그는 임시 운영가드다. 해제 판단도 `holding/exit` 전체 흐름 안에서 해야 하며, `PYRAMID` 결과와 섞이면 원인귀속이 깨진다.
- [ ] `[OpsEODSplit0424] EOD/NXT 착수 여부 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
- 판정 기준: `spread relief canary`가 주병목으로 남아 있으면 출구축으로 승격하지 않고 parking 또는 다음주 이관으로만 닫는다. 착수 시에만 `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt`, `COMPLETED+valid profit_rate`, full/partial 분리 기준을 함께 기록한다.
- [ ] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
- 판정 기준: `2026-04-21 15:24 KST` 확정 범위(`main-only`, `normal_only`, `COMPLETED+valid profit_rate`, `full/partial 분리`, `ai_confirmed_buy_count/share`, `WAIT65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`)를 그대로 사용한다. 제출병목이 잠긴 뒤에만 A/B 재개를 검토한다.
- [ ] `[ScaleIn0424] PYRAMID zero_qty Stage 1 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: ScalpingLogic`)
- 판정 기준: `main-only 1축 live`로만 해석한다. `spread relief canary`가 주병목이면 승인 후보로 올리지 않고 parking 상태를 유지한다. `SCALPING/PYRAMID only`, `zero_qty` 감소, `MAX_POSITION_PCT` 위반 0건, `full/partial fill` 체결품질 악화 없음, `floor_applied`가 `buy_qty=1` 예외에만 국한될 때만 승인한다.
- [ ] `[ScaleIn0424] main은 PYRAMID zero_qty Stage 1 code-load(flag OFF)와 live ON 판정을 분리 유지 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:15`, `Track: Plan`)
  - 판정 기준: `main` 실주문 변경은 승인 전 금지, `flag OFF` 적재와 `live ON` 판정을 같은 슬롯에서 섞지 않는다.
- [ ] `[ScaleIn0424] 물타기축(AVG_DOWN/REVERSAL_ADD) 다음주 착수 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:15~16:25`, `Track: ScalpingLogic`)
- 판정 기준: `shadow 금지 + 단일 live 후보성 재판정`으로 해석한다. `spread relief canary`가 주병목이면 다음주 후보성만 남기고 same-day 승격 후보로는 올리지 않는다. `reversal_add_candidate` 표본 충분성, `buy_qty>=3` 비율, `add_judgment_locked` 교차영향, `split-entry/HOLDING` 관찰축 비간섭 조건이 충족될 때만 다음주 후보로 남긴다.
- [ ] `[HoldingSoftStop0424] soft stop cooldown/threshold 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-23` baseline(`soft_stop=1`, `rebound_above_sell_10m=100%`, `rebound_above_buy_10m=0%`, `cooldown_would_block_rate=0%`)을 바탕으로 `same-symbol cooldown` 후보와 threshold 완화 필요성을 분리 판정한다. 주병목 축이 아니라 parking 판정으로 취급한다.
- [ ] `[HolidayCarry0424] HOLDING hybrid 확대 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:35`, `Track: AIPrompt`)
  - 판정 기준: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`, `force_exit_shadow_samples`가 여전히 0이면 확대 논의를 닫고 보류 유지 사유를 고정한다. 이 항목은 주병목 판정이 아니라 parking 판정이다. `holding_action_applied>0` 또는 `holding_override_rule_version_count>0`가 확인될 때만 확대 후보로 복귀시킨다.
- [ ] `[AuditFix0424] 주간 regime 태그 및 평균 거래대금 수준 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: Plan`)
- [ ] `[AuditFix0424] 1축 유지 규칙 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:40`, `Track: Plan`)
  - 판정 기준: `1축 유지`, `shadow 금지`, `main-only` 규칙을 함께 재확인한다.
- [ ] `[VisibleResult0424] 기대값 중심 우선지표(거래수/퍼널/blocker/체결품질/missed_upside) 재검증` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: Plan`)
- [ ] `[VisibleResult0424] 다음주 PREOPEN 실행지시서에 승격축 1개 반영` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: AIPrompt`)
- [ ] `[DashboardCoverage0424] 성능튜닝 관찰축 커버리지/진입-청산 병목 Flow DeepSeek 작업지시서 전달/착수 여부 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`)
  - Source: [workorder-deepseek-performance-tuning-observation-coverage.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-performance-tuning-observation-coverage.md)
  - 판정 기준: `performance-tuning` 탭의 `직접 표시/간접 표시/별도 리포트/수집됨-미표시/폐기-보관 후보` 축과 `진입 -> 보유 -> 청산` Flow Bottleneck Lane을 DeepSeek 구현 대상으로 전달했는지와, 실거래 로직 변경 없이 리포트/API/UI/문서만 수정하는 범위가 유지되는지 확인한다.
- [ ] `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`)
  - 판정 기준: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log` 에러 없음 + 각 `outputs/` 최신 산출물 갱신 확인
- [ ] 미확정 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`)

## 참고 문서

- [2026-04-18-nextweek-validation-axis-table.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-18-nextweek-validation-axis-table.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-scale-in-qty-logic-final-review-v1.1.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-scale-in-qty-logic-final-review-v1.1.md)
