# 2026-04-17 Stage 2 To-Do Checklist

## 목적

- `P2 HOLDING 포지션 컨텍스트 주입`은 `착수` 또는 `보류 사유 기록` 둘 중 하나로 닫는다.
- `WATCHING 선통과 조건 문맥 주입`도 같은 날 병렬 착수 또는 보류 사유 기록으로 닫는다.
- `P1`에서 이미 본 결과를 기준으로 `P2`로 넘어갈지, `P1` 보강을 하루 더 할지 결정한다.
- `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope를 확정한다.

## 장후 체크리스트 (15:30~)

- [x] `[Checklist0417] AIPrompt P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:45`, `Track: AIPrompt`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: 당일 중 `착수` 또는 `보류 사유+다음 시각` 중 하나로 닫힘
  - 근거: `scalping_exit schema shadow-only` 착수 전제(파싱 양방향 호환) 일정이 후속 항목에 고정됨
  - 다음 액션: `2026-04-20 PREOPEN 08:00~08:10`에 착수 여부 재판정 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: `보류`로 종료. 금일은 일정/선행게이트 확정까지 수행, 구현 착수는 PREOPEN 슬롯으로 고정.
- [x] `[Checklist0417] AIPrompt 작업 7 WATCHING 선통과 조건 문맥 주입` 착수 또는 보류 사유 기록 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:00`, `Track: AIPrompt`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: 병렬 착수 또는 보류사유 기록
  - 근거: `작업 7`은 독립축이나 금일 우선축이 `loss_fallback/timeout shadow` 검증으로 고정
  - 다음 액션: `2026-04-20 POSTCLOSE 15:45~16:00` 재검토 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: `보류`로 종료. 병렬 가능 축임을 유지하되 당일 핵심 병목축 우선 원칙 적용.
- [x] `[Checklist0417] AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 확정 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: helper scope가 문서화돼 후속 착수 입력으로 사용 가능
  - 근거: `2026-04-15` 초안 정리 이력과 후속 착수 체크리스트가 이미 존재
  - 다음 액션: `2026-04-20 PREOPEN`에 helper 인터페이스 확정본을 코드 착수 입력으로 고정 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: `확정(문서기준)`으로 종료. 코드 착수는 익일 슬롯으로 이월.
- [x] `P1` 보류 시 `사유 + 다음 실행시각` 기록 (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: P1 보류 여부와 다음 실행시각이 명시됨
  - 근거: 금일은 PREOPEN/POSTCLOSE 판정 문서 정합과 후속축 일정 고정이 우선
  - 다음 액션: `2026-04-20 08:00 KST`에 P1 재개 여부 재판정 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: P1 `보류`, 다음 실행시각 `2026-04-20 08:00~08:20 KST`.

## 장전 체크리스트 (08:00~09:00)

- [x] `[Checklist0417] entry_pipeline latest/event 이중 지표 정합성 확인` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: Plan`) (`실행: 2026-04-17 20:52 KST`)
  - 판정 기준: `entry_pipeline_flow`에서 최신 시도 기준(`budget_pass_stocks`)과 이벤트 기준(`budget_pass_events`)이 함께 보이고, 장전 판정은 이벤트 기준 퍼널로만 내린다.
  - 근거: `budget_pass_stocks=2`는 최신 시도 요약값이라 실병목 판단을 왜곡했다.
  - 다음 액션: `budget_pass_event_to_submitted_rate`와 `latency_block_events`를 첫 판정 분모로 고정
  - 실행 메모: `build_entry_pipeline_flow_report('2026-04-16')` 재검증 결과 `budget_pass_stocks=2` vs `budget_pass_events=3923`, `order_bundle_submitted_events=24`, `budget_pass_event_to_submitted_rate=0.6` 확인.
- [x] `[Checklist0417] latency canary signal-score 정규화 bugfix 반영 검증` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:15`, `Track: ScalpingLogic`) (`실행: 2026-04-17 20:52 KST`)
  - 판정 기준: `signal_strength=0.x` 입력이 canary 비교 시 점수(`0~100`)로 정규화되고, 로컬 회귀 테스트가 통과한다.
  - 근거: `2026-04-16` 실데이터에서 `latency_canary_applied=0`, `latency_canary_reason=low_signal 1949`로 버그 징후 확인
  - 다음 액션: 장중 첫 30분 `latency_canary_applied` 실제 발생 여부와 `low_signal` 감소 여부를 확인
  - 실행 메모: `pytest -q src/tests/test_sniper_entry_latency.py src/tests/test_entry_pipeline_report.py` 통과(12 passed), `test_latency_entry_canary_normalizes_probability_signal_strength`로 확률값 정규화 회귀 확인.
- [x] `[Checklist0417] latency canary 추가 완화(tag/min_score) 보류 또는 1축 승인` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:30`, `Track: ScalpingLogic`) (`실행: 2026-04-17 20:53 KST`)
  - 판정 기준: bugfix-only 관찰로 충분한지, 아니면 `tag expansion` 1축만 추가할지 결정한다.
  - 근거: 동일 데이터 기준 bugfix-only 잠재 복구 `110건`, `min_score 80` 완화는 잠재 복구 `490건`으로 리스크 차이가 크다
  - 다음 액션: 승인 시 `tag` 1축만 canary, 미승인 시 bugfix-only 유지
  - 실행 메모: 판정=미승인(보류). 금일은 bugfix-only 유지, 신규 완화는 장중 실표본(`latency_canary_applied/low_signal/tag_not_allowed`) 확인 후 재판정.
- [x] `[Checklist0417] 모델별 A/B 테스트 별도 시나리오 초안 확정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:30`) (`실행: 2026-04-17 20:54 KST`)
  - 판정 기준: 실험군/대조군, 중단조건, 평가지표(거래수/퍼널/blocker/체결품질) 문서 확정
  - 근거: 2026-04-16 운영반영과 실험축 분리 원칙
  - 다음 액션: 확정안 기준으로 POSTCLOSE 비교 템플릿 고정
  - 실행 메모: 확정안은 `docs/2026-04-17-model-ab-test-scenario-draft.md`에 동기화.
- [x] `[Checklist0417] SCALP loss_fallback_probe add_judgment_locked 우회 canary 검증` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`) (`실행: 2026-04-17 20:55 KST`)
  - 판정 기준: 손절 직전 `loss_fallback_probe`에서 `gate_reason=add_judgment_locked` 비중이 0%로 내려갔는지 확인
  - 근거: 기존 lock 공유로 fallback 관찰 타이밍이 구조적으로 차단됨
  - 다음 액션: 실패 시 즉시 롤백(`skip_add_judgment_lock=False`) 또는 별도 lock key 분리안 확정
  - 실행 메모: `logs/pipeline_event_logger_info.log*` 기준 `loss_fallback_probe=4건`, `gate_reason=add_judgment_locked 1건(25%)`으로 실패.
- [x] `[Checklist0417] SCALP 손절 직전 fallback 후보(loss_fallback_probe) 전일 로그 판정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`) (`실행: 2026-04-17 20:55 KST`)
  - 판정 기준: `loss_fallback_probe`에서 후보(`fallback_candidate=true`) 빈도/조건을 손절건과 대조해 유효성 판정
  - 근거: 한화오션 손절 리뷰에서 fallback 기회 계측 필요성 확인
  - 다음 액션: 1) observe-only 유지 또는 2) 실전 전환 승인안 작성
  - 실행 메모: 전일 로그 기준 `fallback_candidate=True` 0건, 전량 `False`로 후보 실효성 미충족.
- [x] `[Checklist0417] SCALP 손절 fallback 실전 전환 여부 결정(기본 OFF)` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:20~09:00`) (`실행: 2026-04-17 20:56 KST`)
  - 판정 기준: `SCALP_LOSS_FALLBACK_ENABLED/OBSERVE_ONLY` 토글값 확정 및 운영기록 반영
  - 근거: 손절 축은 체결 리스크가 높아 관찰 근거 없이 즉시 ON 금지
  - 다음 액션: 승인 시 `observe_only=False` 전환, 미승인 시 관찰기간 연장
  - 실행 메모: 판정=미승인(기본 OFF 유지). `add_judgment_locked` 25% 및 fallback 후보 0건으로 실전 전환 근거 부재.
- [x] `[Checklist0417] SCALP lock 분리 vs 롤백 방향 확정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:50`, `Track: ScalpingLogic`) (`실행: 2026-04-17 07:21 KST`)
  - 판정 기준: `loss_fallback_probe add_judgment_locked` 해소를 위한 다음 1축을 구현 착수 가능한 수준으로 고정
  - 근거: 구조적 결정 항목이며 실표본 추가 수집 없이도 today decision 가능
  - 다음 액션: 1차는 `롤백 우선(skip_add_judgment_lock 우회 제거)`, lock key 분리안은 후순위 shadow 검토
- [x] `[Checklist0417] SCANNER fallback timeout 일반 SCANNER 확장 shadow 판정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:30~09:00`) (`실행: 2026-04-17 20:57 KST`)
  - 판정 기준: 현행 `SCANNER fallback` 전용 조기정리 로직과 별개로 일반 SCANNER 장기 표류 shadow 조건/exit_rule을 확정
  - 근거: 롯데쇼핑/올릭스는 fallback 한정 로직으로 직접 커버되지 않음
  - 다음 액션: 승인 시 원격 shadow 우선 반영, 미승인 시 보류 사유와 재판정 시각 기록
  - 실행 메모: 판정=조건부 승인(`shadow-only`, 1축). `제우스(held_sec=3348)`는 timeout shadow 포함, `올릭스(held_sec=461, stagnation=false)`는 timeout 대상이 아닌 add_lock 반복 코호트로 분리.

## 후속 체크리스트 (자동 동기화 대상)

- [x] `[Checklist0417] latency canary bugfix-only 장중 09:00~09:30 실표본 재판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`, `Track: ScalpingLogic`) (`실행: 2026-04-17 12:52 KST`)
  - 판정 기준: `latency_canary_applied`, `low_signal`, `tag_not_allowed`, `quote_stale` 분포 변화 확인
  - 근거: 신규 완화 미승인 상태에서 bugfix-only 실효성 검증 필요
  - 다음 액션: 추가 완화(`tag/min_score`)는 미승인 유지. 남은 장중 표본 누적 후 장후에 한 번 더 확인
  - 실행 메모: noon 실표본 재판정 완료. 로컬 `canary_applied=19`, `low_signal=2271`, `tag_not_allowed=1158`, `quote_stale=769`; 원격 `canary_applied=3`, `low_signal=2599`, `tag_not_allowed=1266`, `quote_stale=866`. bugfix-only는 유효하지만 추가 완화는 아직 이르다.
- [x] `[Checklist0417] SCALP loss_fallback_probe lock 분리안 또는 롤백안 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: `loss_fallback_probe`에서 `add_judgment_locked` 비중 0% 달성 가능한 구현안 확정
  - 근거: 전일 로그에서 `add_judgment_locked` 25%(1/4) 확인
  - 다음 액션: 롤백 적용 후 `loss_fallback_probe gate_reason` 재계수, 잔존 시 lock key 분리안으로 1축 승격
  - 실행 메모: 코드 반영 완료. `loss_fallback_probe`에서 `skip_add_judgment_lock` 우회 제거.
  - 원격 반영 메모(2026-04-17 07:35 KST): `songstockscan` 동일 파일 적용 완료, 원격 `.venv` `py_compile src/engine/sniper_state_handlers.py` 통과.
  - 원격 프로세스 메모: 적용 시점 원격은 `gunicorn`만 동작했고 `bot_main.py`는 미기동 상태여서 bot 재기동 단계는 스킵.
- [x] `[Checklist0417] SCANNER 일반 포지션 timeout shadow 로그 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:00`, `Track: Plan`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: `scanner_never_green_timeout_shadow` 후보의 false-positive 비율/사후 경로 점검
  - 근거: 금일 PREOPEN은 조건부 승인(shadow-only)만 확정
  - 다음 액션: `2026-04-20 PREOPEN 08:40~09:00`에 1일차 shadow 로그를 timeout/add_lock 코호트 분리 포맷으로 판정 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: `제우스 timeout cohort` 포함, `올릭스 add_lock cohort` 분리 기준으로 1일차 판정 기준 확정.
- [x] `[Checklist0417] scalping_exit schema shadow-only 착수 일정 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: `파싱 양방향 호환 -> HOLDING schema shadow-only` 착수 시각과 담당 축을 문서 고정
  - 근거: 순서는 확정됐지만 착수 Due 미기입 상태였음
  - 다음 액션: `2026-04-20 PREOPEN 08:00~08:10` 착수, `2026-04-20 POSTCLOSE` 1차 shadow 판정 (`2026-04-18~2026-04-19 휴일 이관`)
  - 실행 메모: 일정 고정 완료(착수: `2026-04-20 08:00~08:10`, 판정: `2026-04-20 15:30~16:00`).
- [x] `[Checklist0417] GH_PROJECT_TOKEN 운영장애 복구 및 동기화 재실행` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: Plan`) (`실행: 2026-04-17 07:31 KST`)
  - 판정 기준: `sync_docs_backlog_to_project`, `sync_github_project_calendar`가 에러 없이 완료
  - 근거: 미반영 판정 항목이 아니라 인프라 장애 항목으로 별도 추적 필요
  - 다음 액션: 사용자 수동 동기화 원칙에 따라 자동 실행은 생략, 수동 실행 결과만 문서에 역기록
  - 실행 메모: `수동 진행`으로 전환. 본 세션 자동화 명령은 의도적으로 미실행.
- [x] `[Checklist0417] split-entry soft-stop rebase quantity 정합성 감사 기준 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`, `Track: ScalpingLogic`) (`실행: 2026-04-17 12:58 KST`)
  - 판정 기준: `requested_qty/cum_filled_qty/remaining_qty/fill_quality` shadow 포맷과 이상 판정식이 문서화됨
  - 근거: 메인 `2026-04-17` 분할진입 후 soft stop 16건 중 10건에서 정합성 플래그(`cum_gt_requested=9`, `same_ts_multi_rebase=8`, `requested0_unknown=2`) 확인
  - 다음 액션: 남은 장중 표본은 신규 stage `split_entry_rebase_integrity_shadow`로 추가 수집
  - 실행 메모: `src/engine/split_entry_followup_audit.py` 추가, 런타임 `split_entry_rebase_integrity_shadow` stage 반영. 감리 보고서: `docs/2026-04-17-noon-followup-auditor-report.md`
- [x] `[Checklist0417] split-entry soft-stop 즉시 재평가 shadow 설계 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 13:02 KST`)
  - 판정 기준: `partial 이후 확대` 코호트에서만 동작하는 shadow 조건과 관찰 지표가 확정됨
  - 근거: `2026-04-17` expanded-after-partial 코호트는 로컬 `13건`, 원격 `6건`; 로컬은 `held<=180s 10건`, `peak_profit<=0 4건`, `peak_profit<0.2 8건`
  - 다음 액션: 남은 장중 표본은 신규 stage `split_entry_immediate_recheck_shadow`로 추가 수집
  - 실행 메모: trigger=`partial_then_expand|multi_rebase`, shadow_window=`90초`로 고정. 런타임 stage 반영 완료, 봇 재기동 후부터 실표본 누적 가능.
- [x] `[Checklist0417] split-entry soft-stop 동일종목 cooldown shadow 여부 판정` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 15:28 KST`)
  - 판정 기준: cooldown 분(min)과 예외 조건이 확정됨
  - 근거: noon 기준 반복 코호트가 메인 `빛과전자 2회`, 원격 `코미팜 2회`로 새로 확인됨
  - 다음 액션: 판정=승인(`shadow-only`). `same_symbol_soft_stop_cooldown_shadow` 20분 기준으로 코드 반영 후보 고정, `2026-04-20 08:40 KST`에 1일차 누적 로그 재판정.
  - 실행 메모(2026-04-17 15:40 KST): 코드 반영 완료. `handle_watching_state` 쿨다운 분기에서 `same_symbol_soft_stop_cooldown_shadow` shadow emit 추가.
- [x] `[Checklist0417] split-entry partial-only timeout shadow 기준 확정` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 15:29 KST`)
  - 판정 기준: `partial-only` 전용 timeout 조건과 분리 리포트 포맷이 고정됨
  - 근거: `파미셀`, `현대무벡스`, `대한광통신`, `지투파워` 계열이 별도 코호트로 존재
  - 다음 액션: 판정=승인(`shadow-only 우선`). `held_sec>=180 and peak_profit<=0.0` 기준과 분리 리포트 포맷을 확정하고 `2026-04-20 15:30 KST`에 첫 누적 판정.
  - 실행 메모(2026-04-17 15:41 KST): 코드 반영 완료. `handle_holding_state`에 `partial_only_timeout_shadow` 조건/중복방지 로깅 추가.
- [x] `[Checklist0417] protect_trailing_stop 음수청산 라벨/상태초기화 분리 수정안 확정` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:10`, `Track: ScalpingLogic`) (`실행: 2026-04-17 15:30 KST`)
  - 판정 기준: `protect_trailing_stop`의 음수 손익 라벨 정책과 `sell_completed/revive/new entry` 시 `trailing_stop_price/hard_stop_price/protect_profit_pct` 초기화 범위가 분리 설계됨
  - 근거: 아주IB투자 `id=2710`, `id=2722`에서 이전 `PYRAMID` 보호선 `12,607원` 잔존 정황 + 음수 손익에도 `익절 완료` 오표시 확인
  - 다음 액션: 판정=수정안 확정(C-1/C-2). 코드 적용은 `2026-04-17 15:40~16:10` 1차, 미완료 시 `2026-04-17 21:00 KST` 백업 슬롯 재실행.
  - 실행 메모(2026-04-17 15:39 KST): C-1/C-2 코드 반영 완료.
    - C-1: `sell_completed/sell_revive_cleanup`에서 `trailing_stop_price/hard_stop_price/protect_profit_pct` 초기화 추가.
    - C-2: `TRAILING` + `profit_rate<=0`를 손절 라벨로 표기하도록 분기 교정.
    - 검증: `PYTHONPATH=. pytest -q src/tests/test_sniper_scale_in.py -k "resolve_sell_order_sign_trailing_negative_treated_as_loss or same_symbol_soft_stop_cooldown_shadow_once or partial_only_timeout_shadow_logs_when_partial_stuck or holding_exit_signal_logs_exit_rule or scalp_preset_tp_hard_stop_logs_exit_rule"` => `5 passed`.
    - 원격 반영(2026-04-17 15:44 KST): `windy80xyt@songstockscan.ddns.net`에 동일 파일 배포 + 원격 `.venv` `py_compile` 통과.
- [x] `[Checklist0417] 원격 performance_tuning/entry_pipeline_flow timeout 원인 또는 fallback 유지방침 기록` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:00`, `Track: Plan`) (`실행: 2026-04-17 15:31 KST`)
  - 판정 기준: 원격 `TimeoutError`의 원인 또는 `fetch_remote_scalping_logs` fallback 유지 방침이 문서에 고정됨
  - 근거: `server_comparison_2026-04-17`에서 원격 `Performance Tuning`, `Entry Pipeline Flow` 모두 `remote_error(timeout)`이며 noon 판정은 fallback 경로에 의존
  - 다음 액션: 원인=원격 API read timeout 미해소(2026-04-17 15:26 KST curl 재현). 방침=live API 판정 보류, `fetch_remote_scalping_logs` fallback 유지 후 `2026-04-20 08:40 KST` 재점검.
- [x] `[Checklist0417] 코미팜 ghost hard_time_stop_shadow same-day 재발 기준 기록` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: ScalpingLogic`) (`실행: 2026-04-17 15:32 KST`)
  - 판정 기준: `COMPLETED` 이후 shadow emit 재발 여부를 어떤 로그 조건으로 확인할지 명시됨
  - 근거: `id=1664` ghost shadow는 당일 직접 재현되지 않았으나 명시적 재발 기준 없이 이월됨
  - 다음 액션: same-day 점검식 확정: `rg -n "stage=hard_time_stop_shadow" logs/pipeline_event_logger_info.log* -S` 후 `id별 반복 + status/qty` 교차확인. `2026-04-20 09:20 KST`에 기준식으로 재판정.
  - 실행 메모(2026-04-17 15:45 KST): 기준식 즉시 재실행 완료.
    - `id=1664`는 `2026-04-17 09:23/09:25/09:27` 3건(`normal_3m/5m/7m`) 확인.
    - 당일 `hard_time_stop_shadow` id별 집계에서 `1664`는 3건(후속 무한반복 징후 없음)으로 확인.
    - status/qty 교차는 로컬에 `recommendation_history` 원본 테이블 부재로 로그기반 교차만 수행됨(완전 교차는 `2026-04-20 09:20 KST` 재실행 시 포함).

## 휴일 재배치 체크리스트 (2026-04-18~2026-04-19 휴일)

- [x] `[HolidayReassign0417] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 당일 장후 착수 여부 판정 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:45`, `Track: AIPrompt`) (`실행: 2026-04-17 15:33 KST`)
  - 판정 기준: 오늘 장후 `착수` 또는 `보류 사유+다음 실행시각` 중 하나로 종료
  - 근거: 원래 `2026-04-18` 착수 항목이나 휴일로 실행 불가
  - 다음 액션: 판정=보류(우선순위: C/D/E/timeout/ghost). 다음 실행시각 `2026-04-20 PREOPEN 08:00~08:10 KST`.
- [x] `[HolidayReassign0417] 작업 6/7 보류 항목` 다음 실행시각 재기록 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:00`, `Track: AIPrompt`) (`실행: 2026-04-17 15:34 KST`)
  - 판정 기준: 보류 사유와 다음 실행시각이 문서에 명시됨
  - 근거: 원래 `2026-04-18` 장후 재기록 항목이나 휴일로 실행 불가
  - 다음 액션: 작업6/7 모두 보류 유지, 다음 실행시각 `2026-04-20 POSTCLOSE 15:45~16:00 KST`로 재기록 완료.

## 운영 점검 메모

- [x] `[OpsCheck0417] 코미팜(041960) 보유 이후 감시 누락 여부 확인` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 07:47 KST`)
  - 판정: 감시 누락 없음. 실계좌 불일치는 `매도가능수량` 오해석(COMPLETED 오판정) 버그로 분리
  - 근거: `id=2602`는 `holding_started -> ai_holding_review 연속 -> exit_signal` 체인 유지. 다만 `sell_order_failed(125주 매도가능)`에서도 기존 코드가 `COMPLETED` 전환
  - 다음 액션: `0주 매도가능`일 때만 완료 처리하도록 패치 반영 + 원격 재기동 후 재발 모니터링
  - 참고 문서: `docs/2026-04-17-komipharm-holding-monitoring-check.md`
- [x] `[OpsCheck0417] 아주IB투자 보호 트레일링 음수청산/익절 라벨 오표시 원인 확인` (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 12:20~12:40`, `Track: ScalpingLogic`) (`실행: 2026-04-17 12:27 KST`)
  - 판정: `익절 완료` 표시는 메시지 분기 오류이며, 청산 자체는 이전 포지션의 `trailing_stop_price=12,607원`이 재진입 후에도 잔존한 `stale protection` 가능성이 높음
  - 근거: 아주IB투자 `id=2710`, `id=2722` 모두 `exit_rule=protect_trailing_stop`인데 `profit_rate=-0.47/-0.15`. `12,607원`은 `11:27:42` 아주IB투자 `PYRAMID add`의 `new_avg=12569.5683`에 `*1.003` 적용한 보호선과 일치
  - 다음 액션: 코드 수정은 보류하고, `1) protect_trailing_stop 음수 손익 라벨 교정`, `2) sell_completed/revive/new entry 경계에서 trailing/hard/protect 초기화`를 후속 계획으로 분리
  - 참고 문서: `docs/2026-04-17-ajouib-protect-trailing-mislabel-audit.md`
- [x] `[OpsCheck0417] noon shadow stage 재기동/수집 시작시각 기록` (`Due: 2026-04-17`, `Slot: INTRADAY`, `TimeWindow: 12:50~13:00`, `Track: ScalpingLogic`) (`실행: 2026-04-17 12:59 KST`)
  - 판정: noon 후속 shadow 2종은 로컬 `12:52 KST`, 원격 `12:53 KST` 재기동 이후 표본부터만 수집됨
  - 근거: 로컬 `python bot_main.py` 실행 확인, 원격 `tmux bot` 신규 세션과 `python bot_main.py` 신규 PID 확인
  - 다음 액션: 재기동 이전 표본은 소급 수집되지 않으므로 장후 판정 시 수집 시작시각을 기준으로 해석
  - 참고 문서: `docs/2026-04-17-noon-followup-auditor-report.md`

### 장전 사전검증 (2026-04-16 15:36 KST, 모니터링 기준)

1. 판정: 내일 장전에서 **다축 신규 튜닝 승인 요건은 미충족**이지만, `latency canary signal-score` bugfix-only 반영은 가능하다.
- 근거: 최신 시도 기준 `budget_pass_stocks=2`는 착시였고, 이벤트 기준으로는 `budget_pass_events=3923`, `submitted_events=24`, `budget_pass_event_to_submitted_rate=0.6%`다. 동시에 `latency_canary_applied=0`, `latency_canary_reason=low_signal 1949`로 구현 버그가 확인됐다.
- 다음 액션: PREOPEN은 bugfix-only + 지표 정합성 보정까지 진행하고, 추가 완화는 1축만 재판정한다.

2. 판정: `COMPLETED + valid profit_rate` 집계 품질 게이트는 **충족**.
- 근거: `trade_review_2026-04-16` 기준 `completed_trades=20`, `valid_profit_rate_count=20`, full/partial 분리 이벤트(`5/27`) 확인.
- 다음 액션: 손익 평가는 동일 필터(`COMPLETED + valid profit_rate`)만 유지.

3. 판정: 지연/보유 축은 **관측 강화 단계 유지**이나, `latency canary` 경로는 먼저 정상화해야 한다.
- 근거: `performance_tuning_2026-04-16` 기준 `gatekeeper_eval_ms_p95=27408`, `latency_block_events=3899`, `quote_fresh_latency_blocks=2963`, `quote_fresh_latency_passes=24`다. stale이 아닌 차단이 대부분이고 canary 실적은 0건이었다.
- 다음 액션: bugfix 반영 후 `latency_canary_applied`, `low_signal`, `tag_not_allowed`, `quote_stale` 분포를 다시 본다.

4. 판정: 관찰축 5는 **튜닝 입력 신호는 확보**, 실전 전환 요건은 미확정.
- 근거: `add_blocked_lock_2026-04-16` 기준 `total_blocked_events=1392`, `stagnation_blocked_events=941`, 상위 코호트 편중.
- 다음 액션: 종목/시간대/held_sec 코호트 기준으로 PREOPEN 가설 1축만 고정.

5. 판정: 원격 비교 기반 승격 판정은 **보류**.
- 근거: `server_comparison_2026-04-16`에서 `performance_tuning`, `entry_pipeline_flow`가 `remote_error(timeout)`.
- 다음 액션: PREOPEN에 원격 재비교를 먼저 수행하고, timeout 해소 전에는 메인 승격 금지.

## 참고 문서

- [2026-04-16-stage2-todo-checklist.md](./2026-04-16-stage2-todo-checklist.md)
- [2026-04-17-preopen-judgment-basis-for-auditor.md](./2026-04-17-preopen-judgment-basis-for-auditor.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-17 15:47:21`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-17.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`7`
  - holding_events local=13744 remote=4155 delta=-9589.0; all_rows local=232 remote=199 delta=-33.0; completed_trades local=65 remote=41 delta=-24.0
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=68 remote=39 delta=-29.0; evaluated_candidates local=68 remote=39 delta=-29.0
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
