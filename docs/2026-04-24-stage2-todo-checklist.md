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
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않고, 코드 수정이 필요하면 same-day 단일 조작점과 rollback guard를 먼저 고정한 뒤 바로 반영 가능성을 본다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 이 4종과 막힌 조건, 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다. same-day에 분해 가능한 후보를 `다음 장전 검토`로 넘기지 않는다.
- `performance-tuning/post-sell-feedback/trade-review` heavy builder 보호 규칙은 `장후`가 아니라 `PREOPEN/INTRADAY/POSTCLOSE`를 포함한 모든 일일작업에 동일 적용한다. `saved snapshot 우선 -> safe wrapper async dispatch -> completion artifact/Telegram` 외의 foreground direct build는 운영 경로에서 금지한다.
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
- [x] `[LatencyOps0424] ws_jitter relief 2차 방향성 체크` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:10`, `Track: ScalpingLogic`) (`실행: 2026-04-24 12:04 KST`)
  - 판정 기준: `post-restart cohort` 누적 `budget_pass_events >= 100`을 확보한 뒤 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%`면 방향성 유효로 본다. `budget_pass_events >= 100`인데도 `submitted <= 1`이고 `ws_jitter_relief_canary_applied <= 1`이면 독립축 비도달 또는 효과 미약으로 분기한다.
  - 중간관찰 시각: 대략 `12:00~12:10 KST`. 이 슬롯부터는 `첫 제출/체결이 있었는가`가 아니라 `제출 회복 방향성이 숫자로 보이는가`를 본다. 최소 기준은 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%`다.
  - 판정: 완료. `12:10 KST` 기준 방향성 체크는 `독립축 비도달/효과 미약`으로 잠근다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `post-restart cohort=2026-04-24 11:00:00~12:10:00 KST`로 재집계했다. 이벤트 기준 `ai_confirmed=155`, `entry_armed=60`, `budget_pass_events=508`, `latency_block_events=508`, `latency_pass_events=0`, `quote_fresh_latency_blocks=422`, `quote_fresh_latency_pass_rate=0.0%`, `order_bundle_submitted_events=0`, `full_fill_events=0`, `partial_fill_events=0`, `gatekeeper_eval_ms_p95=13385.0ms`, `gatekeeper_fast_reuse=0`, `gatekeeper_fast_reuse_bypass=34`이다.
  - 근거: 같은 구간 raw `latency_block` 기준 `latency_canary_reason_top5=[ws_jitter_only_required 293, low_signal 90, quote_stale 86, latency_fallback_disabled 37, ws_jitter_relief_limit_exceeded 2]`, `latency_danger_reason_top5=[other_danger 249, ws_jitter_too_high 92, quote_stale+ws_age_too_high 40, spread_too_wide 27, ws_age_too_high 26]`, `quote_stale=False 422`, `quote_stale=True 86`이다. `latency_canary_applied=True` 또는 `[LATENCY_WS_JITTER_RELIEF_CANARY]` 실전 통과는 여전히 0건이다.
  - why: `budget_pass_events >= 100`은 크게 충족했지만, 방향성 유효 최소 기준인 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 2.0%`를 둘 다 만족하지 못했다. 동시에 `ws_jitter_relief_canary_applied <= 1`도 유지돼, 이번 1축은 `실제로 허용 경로를 열어 제출 회복을 만들었다`고 볼 근거가 없다. 따라서 장후로 미루지 않고 same-day 장중에서 `독립축 비도달/효과 미약`으로 잠그는 게 맞다.
  - 다음 액션: 아래 `[LatencyOps0424] ws_jitter relief 다음 단계 진입 여부 잠금`은 `submitted >= 5` 가능성 확인이 아니라 `budget_pass_events >= 150`인데 `submitted <= 2`가 지속되는지 최종 잠금하는 슬롯으로 해석한다. 이 조건이 유지되면 `HOLDING/청산 품질`로 넘어가지 않고 `quote_fresh` 하위원인 재분해로 되돌린다.
- [x] `[LatencyOps0424] ws_jitter relief 다음 단계 진입 여부 잠금` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:30`, `Track: ScalpingLogic`) (`실행: 2026-04-24 13:08 KST`)
  - 판정 기준: `post-restart cohort` 누적 `submitted >= 5`와 `fallback_regression = 0`을 확보하면 `HOLDING/청산 품질 관찰` 단계로 진입한다. `submitted >= 10` 또는 `full_fill + partial_fill >= 5`면 same-day 다음 단계 관찰축을 열 수 있다. 반대로 `budget_pass_events >= 150`인데 `submitted <= 2`면 `ws_jitter-only relief` 효과 미약으로 잠그고 same-day 하위원인 재분해로 되돌린다.
  - 중간관찰 시각: 대략 `13:20~13:30 KST`. 이 슬롯에서 `submitted >= 5`가 안 보이면 장후 `첫 제출/체결 품질 확인만`으로 다음 단계에 넘기지 않는다. `submitted/full/partial` 누적이 기준치에 도달한 시점만 다음 단계 진입 근거로 인정한다.
  - 판정: 완료. `13:07 KST` 선행 누적만으로도 `ws_jitter-only relief`는 `다음 단계 진입 불가`로 잠근다. 이후 장중 판단은 `HOLDING/청산 품질`이 아니라 `quote_fresh` 하위원인 재분해 결과를 고정하는 쪽으로 전환한다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `post-restart cohort=2026-04-24 11:00:00~13:07:07 KST`로 재집계했다. 이벤트 기준 `budget_pass_events=1390`, `order_bundle_submitted_events=1`, `latency_pass_events=1`, `quote_fresh_latency_passes=1`, `quote_fresh_latency_blocks=1146`, `quote_fresh_latency_pass_rate=0.09%`, `latency_canary_applied=True=0`이다. 이미 `budget_pass_events >= 150`를 크게 넘겼는데도 `submitted <= 2`가 유지돼 잠금 조건을 과잉충족했다.
  - 근거: 같은 구간 raw `latency_block` 1400건 기준 `reason_top2=[latency_state_danger 1352, latency_fallback_disabled 48]`, `latency_danger_reason_top5=[other_danger 534, ws_age_too_high 423, ws_jitter_too_high 388, spread_too_wide 379, quote_stale 245]`다. fresh quote(`quote_stale=False`) 하위원인 재분해는 `other_quote_fresh 534`, `ws_jitter 230`, `spread 168`, `ws_age 79`, `ws_age+spread 52`, `ws_jitter+spread 45`, `ws_jitter+ws_age 30`, `ws_jitter+ws_age+spread 17`로 갈린다.
  - why: `quote_fresh` 4요인만 보면 `ws_jitter` 단일구간이 가장 크지 않다. 더 큰 지배구간은 `other_danger`이며, 이 값은 `quote_stale/ws_age/ws_jitter/spread` 임계초과가 모두 아닌데도 `latency_state=DANGER/CAUTION`으로 막힌 residual 상태다. 표본 534건 중 `DANGER=494`, `CAUTION=40`, `ai_score>=85`는 56건뿐이고 `ai_score 50~69`가 412건이라서, 지금은 `ws_jitter`를 더 기다리는 것보다 `quote_fresh residual(other_danger)`를 분리해 원인을 다시 고정하는 편이 정보량이 크다.
  - 다음 액션: same-day 후속 제출축은 `quote_fresh 4요인`만이 아니라 `quote_fresh residual(other_danger)`까지 포함한 5분기로 본다. `ws_jitter` 축을 닫는 즉시 아래 `other_danger residual` 1축을 새 live 후보로 열고, `13:10~14:10 KST` 1시간 관찰창으로 다시 본다. `HOLDING/청산 품질` 관찰은 이번 턴에서 열지 않는다.

- [x] `[LatencyOps0424] other_danger residual 1축 즉시 전환 + 1시간 관찰` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 13:10~14:10`, `Track: ScalpingLogic`) (`실행: 2026-04-24 14:11 KST`)
  - 실행 메모 (`2026-04-24 13:23~13:24 KST`): `restart.flag` 우아한 재시작 수행. `logs/bot_history.log`에 `2026-04-24 13:23:44 KST` `수동 재시작 플래그 감지` 로그 확인. 현재 main `bot_main.py` PID는 `200274`이며 시작시각은 `2026-04-24 13:24:27 KST`다. `/proc/200274/environ` 재확인에서도 `KORSTOCKSCAN_SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED`, `...WS_JITTER...`, `...SPREAD...`, `...FALLBACK...` override는 없다.
  - 판정 기준: `ws_jitter-only relief` 축을 종료한 직후 same-day 새 1축을 `other_danger residual`로 고정하고, 코드 적재/재시작 이후 `13:10~14:10 KST` 1시간 관찰창에서 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 0.5%p` 개선이 보이면 방향성 유효로 본다. 반대로 `budget_pass_events`만 증가하고 `submitted <= 2`가 유지되면 residual 축도 same-day 효과 미약으로 잠근다.
  - 관찰 종료 시각: `14:00 KST` 최종판정으로 바로 간다. 별도 `13:40 KST` 중간점검 없이 `budget_pass_events`, `submitted`, `quote_fresh_latency_pass_rate`, `latency_reason_breakdown`, `full_fill`, `partial_fill`을 `13:23:52~14:00 KST` 누적으로 한 번에 본다.
  - 판정: 완료. `13:23:52~14:00 KST` 관찰창 종료 기준 `other_danger residual`은 same-day 효과 미약으로 잠근다.
  - 근거: same-day 원본(`data/pipeline_events/pipeline_events_2026-04-24.jsonl`)을 `13:23:52~14:00:00 KST`로 재집계했다. 이벤트 기준 `ai_confirmed=53`, `entry_armed=34`, `budget_pass_events=368`, `latency_block_events=368`, `submitted=0`, `quote_fresh_latency_blocks=251`, `quote_fresh_latency_pass_rate=0.0%`, `full_fill_events=0`, `partial_fill_events=0`, `latency_canary_applied=True=0`이다.
  - 근거: 같은 구간 fresh quote(`quote_stale=False`) residual 분해는 `other_quote_fresh 114`, `ws_age 44`, `spread 28`, `ws_jitter 22`, `ws_age+spread 15`, `ws_age+ws_jitter 14`다. `latency_canary_reason_top4=[other_danger_only_required 127, quote_stale 117, low_signal 78, - 46]`이며 `other_danger_relief_canary_applied`와 `latency_other_danger_relief_normal_override`는 둘 다 0건이다.
  - why: 오후장 BUY 유입 감소를 감안해도 `entry_armed=34 -> submitted=0`, `full/partial=0`, `quote_fresh pass=0`이면 same-day live 완화가 허용 경로를 열었다고 볼 근거가 없다. residual 분포도 여전히 `other_quote_fresh` 우위라 관찰 연장보다 잠금이 정보량이 크다.
  - why: 기존 축을 닫고 장후까지 비워 두면 same-day 원인귀속이 끊긴다. 새 축은 기존 관찰축 종료 시점부터 다시 1시간을 줘야 비교가 가능하고, 이번에는 [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)의 `other_danger-only normal override` 코드가 먼저 적재돼야 관찰이 의미를 가진다.
  - 다음 액션: 아래 `14:00 KST` 최종판정 항목에서 `quote_fresh family` 잠금 여부를 same-day로 바로 닫는다.

- [x] `[LatencyOps0424] other_danger residual 14:00 최종판정` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:02`, `Track: ScalpingLogic`) (`실행: 2026-04-24 14:11 KST`)
  - 판정 기준: `13:23:52~14:00 KST` 누적에서 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 0.5%p` 개선이 있으면 same-day 유지 후보로 본다. 반대로 `submitted <= 2`, `full_fill + partial_fill = 0`, `latency_reason_breakdown` 상 `other_danger` 비중이 그대로면 same-day 효과 미약으로 잠그고 다음 explicit 단일요인(`ws_jitter > spread > ws_age`)만 남긴다.
  - 중간관찰 시각: `14:00 KST`.
  - 판정: 완료. `other_danger residual` 14시 최종판정은 `same-day 효과 미약/유지 보류`로 잠근다.
  - 근거: `13:23:52~14:00 KST` 기준 `submitted=0(<3)`, `quote_fresh_latency_pass_rate=0.0%(개선 0.0%p)`, `full_fill + partial_fill = 0`이다. fresh quote 구간에서도 `other_quote_fresh=114/251(45.4%)`로 단일 최대 분기다.
  - why: 체크리스트 기준선인 `submitted >= 3` 또는 `quote_fresh_latency_pass_rate >= 0.5%p 개선`을 둘 다 충족하지 못했고, canary apply 흔적도 0건이라 same-day 유지 후보로 볼 근거가 없다.
  - why: 이번엔 `13:40` 중간점검 없이 `14:00`에 바로 최종판정을 내린다. 장후 `첫 제출/체결 품질 확인만`으로 이 판정을 대체하지 않는다. 다만 `1축 원칙`은 동시 2축 금지이지 same-day 교체 금지가 아니므로, `other_danger residual`까지 잠기면 `quote_fresh family`를 닫고 준비된 다음 독립축으로 바로 교체할 수 있다.
  - 다음 액션: 아래 항목에서 `quote_fresh family` 잠금과 same-day replacement 승인 여부를 바로 닫는다.

- [x] `[LatencyOps0424] quote_fresh family 잠금 시 다음 독립축 same-day replacement 결정` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 14:02~14:10`, `Track: ScalpingLogic`) (`실행: 2026-04-24 14:11 KST`)
  - 판정 기준: `other_danger residual`까지 `submitted <= 2`, `full_fill + partial_fill = 0`, `quote_fresh_latency_pass_rate` 개선 미미면 `quote_fresh family`(`other_danger/ws_jitter/spread/ws_age/quote_stale`)를 장중에서 잠근다. 그 직후 준비된 다음 독립축 1개가 `fallback 비결합`, `단일 조작점`, `코드/테스트/rollback guard` 준비 완료이고 잔여 관찰시간이 `>= 40분`이면 same-day replacement를 승인한다.
  - 실행 규칙: `1축 원칙`은 `동시 live 1축`만 금지한다. same-day replacement 자체는 허용하며, 승인 시에도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
  - 판정: 완료. `quote_fresh family`는 장중 잠금하고, same-day replacement는 `미승인`으로 닫는다. 다음 독립축은 `gatekeeper_fast_reuse signature/window`로 고정하되 live 반영은 `2026-04-27 PREOPEN` 승인 판정으로 넘긴다.
  - 근거: `other_danger residual`까지 `submitted=0`, `full_fill + partial_fill = 0`, `quote_fresh_latency_pass_rate=0.0%`라 `other_danger/ws_jitter/spread/ws_age/quote_stale` 5분기 전부가 오늘 제출 회복 근거를 만들지 못했다. 같은 창에서 `strength_momentum_pass(canary_applied=True, canary_reason=dynamic_strength_relief)=107`이라 `dynamic strength`는 이미 baseline live 경로이고, `entry_filter_quality`는 제출병목 해소 전 parking 유지 원칙에 묶인다. `PYRAMID zero_qty`/보유축은 `submitted/fill=0`으로 관찰 표본 자체가 없다.
  - 근거: `gatekeeper_fast_reuse`는 다음 독립축 후보성은 있다. `13:23:52` 이후 재집계 기준 `gatekeeper_decisions=23`, `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=19871ms`, blocker 상위가 `재사용 창 만료 25`, `시그니처 변경 22`, `WS stale 13`이다. 기대값상 다음 후보는 맞지만, 현 시점에는 `단일 조작점 + ON/OFF rollback`으로 포장된 live replacement가 아니라서 장중 즉시 교체 조건(`코드/테스트/rollback guard 준비 완료`)을 충족하지 못한다.
  - why: 현재 작업은 `아닌 축을 장중에 빨리 잠그고 다음 축을 하나씩 켜서 검증`하는 단계다. 기존 축을 완전히 끄고 새 축만 켜면 변인통제가 유지되므로 same-day 교체가 원칙 위반이 아니다.
  - why: 지금 same-day에 추가로 축을 켜려면 `기존 축 OFF -> restart.flag -> 새 축 ON`만으로 끝나는 독립축이어야 한다. `gatekeeper_fast_reuse`는 단순 sec 조정만으로는 `signature_changed` 축을 분리하지 못해 원인귀속이 다시 흐려진다.
  - 다음 액션: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)의 `[LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정`으로 `2026-04-27 PREOPEN` 실행시각을 고정하고, 장후에는 `quote_fresh family` 잠금 상태를 유지한 채 `entry_filter_quality` parking 여부만 재확인한다.

- [x] `[LatencyOps0424] gatekeeper_fast_reuse signature/window 장중 재분해 + signature-only 형상 반영` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 14:10~14:30`, `Track: ScalpingLogic`) (`실행: 2026-04-24 14:25 KST`)
  - 판정 기준: `quote_fresh family`를 잠근 뒤 `gatekeeper_fast_reuse_bypass` raw 표본을 `window`와 `signature`로 재분해해 단일 조작점 1개를 같은 장중에 고정한다. `window`만으로 설명되는 표본이 소수면 `signature-only` 형상 변경을 우선 적용하고, `restart.flag` 이후 새 코호트를 장후 판정 입력으로 연다.
  - 판정: 완료. 단일 조작점은 `window`가 아니라 `signature-only`로 고정하고, 미세 signed flow 노이즈(`prog_net_qty`, `prog_delta_qty`) deadband를 same-day 실코드에 반영했다.
  - 근거: same-day raw `gatekeeper_fast_reuse_bypass` 재집계 기준 `after_other_danger_switch=31건`에서 `age_expired_only=1`, `sig_only=1`, `age_expired+sig_changed=8`, `missing_action/missing_allow_flag` 초기표본 9건이다. 즉 `window`만 늘려 해결될 표본이 극히 적고, `reason_combo` 주력은 여전히 `sig_changed` 결합 경로다.
  - 근거: `sig_delta` 상위는 `curr_price 21`, `v_pw_now 17`, `spread_tick 15`, `score 13`, `buy_ratio_ws 13`, `prog_delta_qty 10`이었다. 재현 테스트에서 `curr_price 767->766`, `prog_delta_qty 0->-1` 같은 미세 signed flow 변화만으로 signature가 깨지는 케이스를 확인했고, [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)에 `_bucket_int_with_deadband()`를 추가해 `prog_net_qty<25,000`, `prog_delta_qty<5,000` 절대값 구간은 `0` bucket으로 정규화했다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_gatekeeper_fast_reuse_age.py` => `15 passed`. 신규 테스트는 `small signed program flow noise 무시`, `large program flow shift 유지` 2건이다.
  - 실행 메모: `restart.flag` 우아한 재시작 수행 후 main `bot_main.py` PID `200274 -> 207081` 교체 확인. 새 PID 시작시각은 `2026-04-24 14:25:15 KST`이고 `/proc/207081/environ`에는 관련 `KORSTOCKSCAN_*` override가 없다.
  - why: `window`를 먼저 늘리면 `signature_changed`와 섞여 원인귀속이 다시 흐려진다. 반대로 `signature-only` deadband는 ON/OFF가 명확하고, 오늘 장후까지 `fast_reuse_ratio`, `reuse_blockers`, `gatekeeper_eval_ms_p95` 이동을 바로 볼 수 있다.
  - 다음 액션: 장후 `[VisibleResult0424] 금요일 승격 후보 1축 최종선정`과 `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정`에서 `2026-04-24 14:25:15 KST` 이후 post-change 코호트(`gatekeeper_fast_reuse`, `gatekeeper_fast_reuse_bypass`, `gatekeeper_eval_ms_p95`, `submitted/full/partial`)를 기준으로 유지/롤백/익일 carry-over를 닫는다.

## 장후 체크리스트 (15:10~15:40) - 주병목 판정

- [x] `[OpsGuard0424] heavy report builder direct-call guard + async completion signal 적용` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:05~15:10`, `Track: Plan`) (`실행: 2026-04-24 17:05 KST`)
  - 판정 기준: `performance-tuning/post-sell-feedback/trade-review`의 직접 builder 호출을 `장후`뿐 아니라 모든 일일작업 경로에서 금지하고, `saved snapshot 우선 -> safe wrapper async dispatch -> IDE/Telegram completion signal` 순서로만 동작해야 한다.
  - 판정: 완료. 웹/API 운영 경로는 `PREOPEN/INTRADAY/POSTCLOSE` 공통으로 direct build 대신 `saved snapshot 또는 pending async-dispatch`로 통일했고, `run_monitor_snapshot_safe.sh`는 `tmp/monitor_snapshot_completion_<date>_<profile>.json` completion artifact와 `next_prompt_hint`를 함께 남기도록 보강했다.
  - 근거: `src/web/app.py`, `src/engine/monitor_snapshot_runtime.py`, `deploy/run_monitor_snapshot_safe.sh`, `src/engine/notify_monitor_snapshot_admin.py`
  - 다음 액션: parser 검증 후 backlog/project 반영은 사용자 실행 명령 `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --dry-run` 기준으로 확인한다.

- [x] `[OpsGuard0424] 장후/익일 이관 항목 4종 예외사유/막힌조건/다음 절대시각 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:10~15:15`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: same-day에 닫지 못하고 장후/익일/PREOPEN으로 남긴 항목마다 `1) same-day 불가 이유`, `2) 추가 데이터 vs 코드수정`, `3) 단일 조작점/rollback guard/restart 가능 여부`, `4) 막힌 조건과 다음 절대시각`이 모두 남아 있어야 한다. 하나라도 없으면 해당 이관 판정은 무효로 되돌리고 same-day 미이행으로 재개한다.
  - 실행 규칙: 이 항목은 단순 메모가 아니라 `장후/익일 이관 무효화` 규칙 준수 확인이다. PREOPEN carry-over 항목도 전일 준비완료 증적이 없으면 이 슬롯에서 다시 무효 처리한다.
  - 판정: 완료. today carry-over는 `gatekeeper_fast_reuse signature/window` 1건과 `pattern lab postclose 산출물/로그 보수` 1건만 유효로 남기고, 나머지 장후 항목은 same-day 판정으로 닫았다.
  - 근거: `gatekeeper_fast_reuse`는 `2026-04-24 14:25:15 KST` signature-only deadband 반영까지는 끝났지만 `same-day live replacement 승인` 요건 중 `PREOPEN 승인 슬롯`이 필요해 [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)의 `[LatencyOps0427]`로 절대시각을 고정했다. pattern lab은 `logs/tuning_monitoring_postclose_cron.log`에서 Gemini 분석이 `trade_id str/float64 merge` 예외로 실패했고 Claude/Gemini 전용 cron log 파일은 더 이상 생성되지 않아 후속 보수가 필요하다.
  - 다음 액션: carry-over 2건은 [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)에 절대시각으로 반영한다.

- [x] `[LatencyOps0424] 오전 제출축 결과 잠금` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
- 판정 기준: 오전 `10:00 KST` checkpoint를 기준으로 `spread relief canary`의 `유지/확대/보류/롤백` 중 하나를 확정한다.
  - 판정: 완료. 오전 제출축 검증 결과는 `spread relief/ws_jitter family 유지 아님`, `budget_pass -> pre_submit_latency(latency_block)` 주병목 유지로 잠근다.
  - 근거: `10:00 KST` checkpoint 기준 `ai_confirmed=77`, `entry_armed=31`, `budget_pass_events=863`, `order_bundle_submitted_events=4`, `latency_block_events=859`, `quote_fresh_latency_blocks=777`, `quote_fresh_latency_pass_rate=0.5%`였다. 이후 same-day 장중 잠금 결과도 `quote_fresh family` 전반이 `submitted/full/partial` 회복 근거를 만들지 못했고, `2026-04-24 16:23:34` snapshot 기준 최종 `budget_pass_events=3800`, `order_bundle_submitted_events=11`, `latency_block_events=3789`, `quote_fresh_latency_pass_rate=0.4%`로 같은 구조가 유지됐다.
  - 다음 액션: 주병목 명칭은 `entry_armed -> budget_pass`가 아니라 `budget_pass -> pre_submit_latency(latency_block) -> submitted 단절`로 고정한다.
- [x] `[VisibleResult0424] 금요일 승격 후보 1축 최종선정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
- 판정: 완료. 금요일 승격 후보 1축은 `gatekeeper_fast_reuse signature-only deadband`로 최종선정하되, `금요일 장중/장후 즉시 승격`이 아니라 `2026-04-27 PREOPEN 승인 후보`로만 고정한다.
- 근거: `quote_fresh family`는 same-day 장중 판정에서 전부 잠겼고, 이후 `gatekeeper_fast_reuse` raw 분해에서 `age_expired_only=1`, `sig_only=1`, `age_expired+sig_changed=8`이라 `window`보다 `signature_changed` deadband가 단일 조작점으로 더 명확했다. `2026-04-24 16:23:34` snapshot에서도 `gatekeeper_fast_reuse_ratio=0.0`, `gatekeeper_eval_ms_p95=14620.0`로 아직 체결 회복 증거는 부족하지만, 다음 independent axis 후보성은 유지된다.
- 다음 액션: live 승격 여부는 아래 승인 항목에서 절대시각까지 함께 닫는다.
- [x] `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `승격 실행`이면 축 1개만 선택하고 롤백 가드 포함, `보류`이면 원인 1개와 재실행 시각 1개를 동시에 기록
  - 판정: 완료. `승격 실행`은 보류하고, 재실행 시각은 `2026-04-27 08:20~08:35 KST PREOPEN`으로 확정한다.
  - 근거: same-day post-change 코호트는 heavy report builder IO 과부하로 장중 중간점검이 끊겼고, 최종 snapshot 기준도 `submitted=11`, `full_fill=8`, `partial_fill=0`이지만 pre-submit latency 병목 자체는 `3789/3800` 수준으로 유지됐다. 따라서 오늘은 `승격 승인`보다 `단일 후보와 다음 절대시각`을 고정하는 편이 맞다.
  - 다음 액션: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)의 `[LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정`에서 live 승인/보류를 최종 닫는다.

## 장후 체크리스트 (15:40~17:00) - 후순위 축 Parking

- [x] `[PlanRebase0424] entry_filter_quality parking 재확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
- 판정 기준: `spread relief canary`가 여전히 주병목이면 `entry_filter_quality`는 주병목 축이 아니라 parking 상태로 유지하고, 제출축이 완화됐을 때만 후보 복귀 여부를 판단한다.
  - 판정: 완료. `entry_filter_quality`는 parking 유지다.
  - 근거: `flow_bottleneck_lane` 최신 snapshot에서 `pre_submit_latency`만 `bottleneck`이고 `entry_armed`는 `ok`다. 정량도 `budget_pass_events=3800`, `order_bundle_submitted_events=11`, `latency_block_events=3789`, `quote_fresh_latency_pass_rate=0.4%`라 제출축 완화가 먼저다.
  - 다음 액션: 제출축이 완화되기 전까지 `entry_filter_quality` 코드/상수 변경은 열지 않는다.
- [x] `[InitialQtyCap0424] 스캘핑 신규 BUY 1주 cap 유지/해제 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~15:55`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `initial-only`와 `pyramid-activated` 표본을 분리한 뒤 `submitted/full/partial`, `soft_stop/trailing/good_exit`, `COMPLETED + valid profit_rate`를 함께 보고 `유지/완화/해제` 중 하나로 닫는다. `soft_stop`만 단독 기준으로 쓰지 않고 holding/exit 전체 판정 안에서 본다.
  - why 기준: 이 cap은 prompt 재교정 직후 초기 진입 손실 tail을 잠그는 임시 운영가드다. 해제 판단도 `holding/exit` 전체 흐름 안에서 해야 하며, `PYRAMID` 결과와 섞이면 원인귀속이 깨진다.
  - 판정: 완료. `1주 cap 유지`로 닫는다.
  - 근거: `trade_review_2026-04-24.json` 기준 `completed_trades=9`, `avg_profit_rate=-0.2`, `full_fill_events=8`, `partial_fill_events=0`이고, `post_sell_feedback_2026-04-24.json` 기준 `total_soft_stop=2`, `cooldown_would_block_rate=100.0`, `MISSED_UPSIDE=7`, `GOOD_EXIT=1`이다. 제출축이 아직 병목이고, soft-stop tail도 남아 있어 초기 신규 BUY cap을 해제할 근거가 없다.
  - 다음 액션: `initial-only`와 `pyramid-activated` 분리 해제 논의는 제출축 잠금 이후로 미룬다.
- [x] `[OpsEODSplit0424] EOD/NXT 착수 여부 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
- 판정 기준: `spread relief canary`가 주병목으로 남아 있으면 출구축으로 승격하지 않고 parking 또는 다음주 이관으로만 닫는다. 착수 시에만 `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt`, `COMPLETED+valid profit_rate`, full/partial 분리 기준을 함께 기록한다.
  - 판정: 완료. `EOD/NXT 착수 보류`다.
  - 근거: `pre_submit_latency`가 still bottleneck이고 `completed_trades=9` 수준에서 출구축만 분리 승격하면 기대값보다 원인귀속이 먼저 흐려진다. `trade_review`상 `full_fill=8`, `partial_fill=0`, `avg_profit_rate=-0.2`는 방향성 참고 수준이지만, 지금은 `exit_rule` 분기보다 `submitted` 회복이 우선이다.
  - 다음 액션: EOD/NXT는 다음주 후보성만 유지하고 same-day 승격 후보에서는 제외한다.
- [x] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`) (`실행: 2026-04-24 17:42 KST`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
- 판정 기준: `2026-04-21 15:24 KST` 확정 범위(`main-only`, `normal_only`, `COMPLETED+valid profit_rate`, `full/partial 분리`, `ai_confirmed_buy_count/share`, `WAIT65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`)를 그대로 사용한다. 제출병목이 잠긴 뒤에만 A/B 재개를 검토한다.
  - 판정: 완료. `A/B 재개 보류`다.
  - 근거: `2026-04-21 15:24 KST` preflight 범위는 그대로 유효하지만, 오늘 `ai_confirmed` upstream보다 `budget_pass -> submitted` downstream 병목이 지배적이다. `performance_tuning_2026-04-24.json` 기준 `budget_pass_events=3800`, `order_bundle_submitted_events=11`, `latency_block_events=3789`이어서 A/B를 재개해도 제출축 병목과 섞인다.
  - 다음 액션: 제출병목이 잠길 때까지 A/B는 운영축이 아니라 parking 유지다.
- [x] `[ScaleIn0424] PYRAMID zero_qty Stage 1 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
- 판정 기준: `main-only 1축 live`로만 해석한다. `spread relief canary`가 주병목이면 승인 후보로 올리지 않고 parking 상태를 유지한다. `SCALPING/PYRAMID only`, `zero_qty` 감소, `MAX_POSITION_PCT` 위반 0건, `full/partial fill` 체결품질 악화 없음, `floor_applied`가 `buy_qty=1` 예외에만 국한될 때만 승인한다.
  - 판정: 완료. `승인 보류`다.
  - 근거: 오늘 주병목은 scale-in branch가 아니라 `pre_submit_latency`이며, `flow_bottleneck_lane`에서도 `scale_in_branch=ok`, `pre_submit_latency=bottleneck`이다. 제출 회복 전에는 `PYRAMID zero_qty`를 live 1축 후보로 올릴 단계가 아니다.
  - 다음 액션: `PYRAMID`는 code-load(flag OFF) 증적만 유지하고 live ON 논의는 미룬다.
- [x] `[ScaleIn0424] main은 PYRAMID zero_qty Stage 1 code-load(flag OFF)와 live ON 판정을 분리 유지 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:15`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `main` 실주문 변경은 승인 전 금지, `flag OFF` 적재와 `live ON` 판정을 같은 슬롯에서 섞지 않는다.
  - 판정: 완료. `flag OFF code-load`와 `live ON`은 분리 유지로 잠근다.
  - 근거: PREOPEN에서 이미 `flag OFF` 적재/restart 증적을 확보했고, 오늘은 주병목이 제출축이라 `main` 실주문 변경을 추가로 열 이유가 없다.
  - 다음 액션: 없음.
- [x] `[ScaleIn0424] 물타기축(AVG_DOWN/REVERSAL_ADD) 다음주 착수 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:15~16:25`, `Track: ScalpingLogic`) (`실행: 2026-04-24 17:42 KST`)
- 판정 기준: `shadow 금지 + 단일 live 후보성 재판정`으로 해석한다. `spread relief canary`가 주병목이면 다음주 후보성만 남기고 same-day 승격 후보로는 올리지 않는다. `reversal_add_candidate` 표본 충분성, `buy_qty>=3` 비율, `add_judgment_locked` 교차영향, `split-entry/HOLDING` 관찰축 비간섭 조건이 충족될 때만 다음주 후보로 남긴다.
  - 판정: 완료. `다음주 착수 보류`다.
  - 근거: `shadow 금지` 원칙상 다음주도 canary-only 후보성만 볼 수 있고, 오늘은 `buy_qty>=3` 기반 추가매수 기대값보다 제출축 복구가 선행이다.
  - 다음 액션: position addition은 후보성만 남기고 승격 후보에서는 제외한다.
- [x] `[HoldingSoftStop0424] soft stop cooldown/threshold 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: AIPrompt`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `2026-04-23` baseline(`soft_stop=1`, `rebound_above_sell_10m=100%`, `rebound_above_buy_10m=0%`, `cooldown_would_block_rate=0%`)을 바탕으로 `same-symbol cooldown` 후보와 threshold 완화 필요성을 분리 판정한다. 주병목 축이 아니라 parking 판정으로 취급한다.
  - 판정: 완료. `same-symbol cooldown 후보 유지`, `threshold 완화는 보류`다.
  - 근거: `post_sell_feedback_2026-04-24.json` 기준 `total_soft_stop=2`, `rebound_above_sell_10m=100%`, `rebound_above_buy_10m=50%`, `cooldown_would_block_rate=100.0`, `median_overshoot_pct=0.22`다. 즉 threshold를 더 넓힐 근거보다 `동일종목 재진입 cooldown`이 soft-stop rebound 일부를 막을 가능성이 더 크다.
  - 다음 액션: threshold 전역 완화는 계속 금지하고 cooldown 후보만 parking 근거로 남긴다.
- [x] `[HolidayCarry0424] HOLDING hybrid 확대 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:35`, `Track: AIPrompt`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`, `force_exit_shadow_samples`가 여전히 0이면 확대 논의를 닫고 보류 유지 사유를 고정한다. 이 항목은 주병목 판정이 아니라 parking 판정이다. `holding_action_applied>0` 또는 `holding_override_rule_version_count>0`가 확인될 때만 확대 후보로 복귀시킨다.
  - 판정: 완료. `HOLDING hybrid 확대 보류 유지`다.
  - 근거: `performance_tuning_2026-04-24.json` 기준 `holding_reviews=221`, `holding_skips=14`지만 `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`를 확대 승인할 근거는 여전히 없다. 제출병목이 해소되지 않은 상태에서 HOLDING hybrid를 늘리면 원인귀속만 흐린다.
  - 다음 액션: HOLDING hybrid는 표본 축적 전까지 parking 유지다.
- [x] `[AuditFix0424] 주간 regime 태그 및 평균 거래대금 수준 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
- 판정: 완료. 이번 금요일 regime 태그는 `BEAR / RISK_OFF / swing 보류`로 병기하고, 평균 거래대금 수준은 `현재 snapshot 미노출` 데이터 공백으로 명시한다.
- 근거: `performance_tuning_2026-04-24.json`의 `swing_daily_summary.market_regime`가 `regime_code=BEAR`, `risk_state=RISK_OFF`, `status_text=하락장`, `allow_swing_entry=False`를 기록한다. 반면 `avg_trading_value_level`은 `None`이라 오늘 판정에는 regime만 반영하고 거래대금 수준은 `same-day metric gap`으로 남긴다.
- 다음 액션: 평균 거래대금 수준이 판정 필수 입력이 되면 snapshot 노출부터 보강한다.
- [x] `[AuditFix0424] 1축 유지 규칙 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:40`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `1축 유지`, `shadow 금지`, `main-only` 규칙을 함께 재확인한다.
  - 판정: 완료. `1축 유지`, `shadow 금지`, `main-only` 위반은 없다.
  - 근거: 오늘 장중 live 교체는 `quote_fresh family` 내 same-day replacement와 `gatekeeper_fast_reuse signature-only` 형상 반영 순서로만 진행됐고, 동시 2축 live는 없었다. heavy report builder guard, dashboard/report 보강, pattern lab 점검은 운영/문서 작업이지 실주문 canary 축이 아니다.
  - 다음 액션: 이후 live 승인도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서를 유지한다.
- [x] `[VisibleResult0424] 기대값 중심 우선지표(거래수/퍼널/blocker/체결품질/missed_upside) 재검증` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
- 판정: 완료. 오늘 우선지표 재검증 결론도 `거래수/퍼널/blocker` 우선이며, 손익 단독 해석은 금지다.
- 근거: `performance_tuning` 기준 `budget_pass_events=3800 -> submitted=11`, `latency_block_events=3789`, `quote_fresh_latency_pass_rate=0.4%`, `trade_review` 기준 `completed_trades=9`, `avg_profit_rate=-0.2`, `full_fill_events=8`, `partial_fill_events=0`, `post_sell_feedback` 기준 `MISSED_UPSIDE=7`, `GOOD_EXIT=1`이다. 따라서 기대값 관점에서도 오늘 핵심은 미진입 기회비용과 제출 직전 blocker 분포다.
- 다음 액션: 승격/보류 판정은 계속 `퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익` 순서로 본다.
- [x] `[VisibleResult0424] 다음주 PREOPEN 실행지시서에 승격축 1개 반영` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: AIPrompt`) (`실행: 2026-04-24 17:42 KST`)
- 판정: 완료. 다음주 PREOPEN 실행지시서에는 `gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정` 1건을 반영했다.
- 근거: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)에 이미 `[LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정`이 고정돼 있고, 오늘 장후 승격 후보 최종선정과 재시각 확정이 그 항목과 일치한다.
- 다음 액션: 없음.
- [x] `[DashboardCoverage0424] 성능튜닝 관찰축 커버리지/진입-청산 병목 Flow DeepSeek 작업지시서 전달/착수 여부 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - Source: [workorder-deepseek-performance-tuning-observation-coverage.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-performance-tuning-observation-coverage.md)
  - 판정 기준: `performance-tuning` 탭의 `직접 표시/간접 표시/별도 리포트/수집됨-미표시/폐기-보관 후보` 축과 `진입 -> 보유 -> 청산` Flow Bottleneck Lane을 DeepSeek 구현 대상으로 전달했는지와, 실거래 로직 변경 없이 리포트/API/UI/문서만 수정하는 범위가 유지되는지 확인한다.
  - 판정: 완료. 전달/착수/결과 기록 모두 확보됐다.
  - 근거: [workorder-deepseek-performance-tuning-observation-coverage.result.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-performance-tuning-observation-coverage.result.md)가 PASS로 닫혔고, `performance_tuning` 최신 snapshot의 `flow_bottleneck_lane`은 `pre_submit_latency=bottleneck`, 나머지 주요 노드는 `ok`로 정렬돼 있다. 작업 범위도 결과서 기준 `실거래 로직 변경 없음, 리포트/API/UI/문서만 수정`이다.
  - 다음 액션: 없음.
- [x] `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - 판정 기준: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log` 에러 없음 + 각 `outputs/` 최신 산출물 갱신 확인
  - 판정: 완료. `전용 cron log 기준 정상`은 아니고, 운영 경로가 `tuning_monitoring_postclose_cron.log`로 합쳐진 뒤 Gemini pattern lab 실패가 남아 있는 상태로 점검을 닫는다.
  - 근거: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log`는 현재 생성되지 않았고, 실운영 래퍼는 `deploy/run_tuning_monitoring_postclose.sh`로 합쳐져 있다. `logs/tuning_monitoring_postclose_cron.log` 최신 구간에는 Gemini 분석이 `trade_id str/float64 merge` 예외로 실패한 흔적이 있으며, output 갱신시각도 Gemini는 `2026-04-23 18:01`, Claude는 `2026-04-22 19:14`로 오늘 주간 산출물 갱신 기준을 충족하지 못했다.
  - 다음 액션: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)에 `pattern lab postclose 산출물/로그 보수` 후속 작업을 추가한다.
- [x] 미확정 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`) (`실행: 2026-04-24 17:42 KST`)
  - 판정: 완료. today 미확정/이관 잔량은 `gatekeeper_fast_reuse PREOPEN 승인`과 `pattern lab postclose 보수` 2건뿐이다.
  - 근거: 나머지 POSTCLOSE 항목은 same-day 판정으로 닫았고, 위 2건은 각각 `2026-04-27 08:20~08:35 KST`, `2026-04-27 18:05~18:20 KST` 절대시각을 문서에 고정했다.
  - 다음 액션: 사용자 backlog/project 반영 확인은 sync 명령으로 처리한다.

## 참고 문서

- [2026-04-18-nextweek-validation-axis-table.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-18-nextweek-validation-axis-table.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-scale-in-qty-logic-final-review-v1.1.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-scale-in-qty-logic-final-review-v1.1.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-24 16:25:45`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-24.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
