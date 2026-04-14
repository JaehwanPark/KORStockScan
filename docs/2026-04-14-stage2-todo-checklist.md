# 2026-04-14 Stage 2 To-Do Checklist

## 목적

- `2026-04-13` 장후 판정을 `2026-04-14` 운영 체크리스트로 승격한다.
- 최우선은 `RELAX-LATENCY` 원격 강화 관찰의 반복 재현성 확인이다.
- 오늘부터 `main` 예정 작업은 원격 `develop`에 `T-2` 또는 늦어도 `T-1` 먼저 적용하는 것을 기본 규칙으로 쓴다.
- `RELAX-DYNSTR`는 `2026-04-14 장후`에 `momentum_tag` 1축과 롤백 가드를 확정하고, `2026-04-15 08:30`까지 원격 canary를 시작한다.
- `RELAX-OVERBOUGHT`는 실전 재오픈이 아니라 `표본 누적`만 진행한다.
- `관찰 축 추가`는 여기서 끝낸다. `2026-04-14 장후`에는 `반영 / 보류+단일축 전환 / 관찰 종료` 중 하나로 결론내고, `2026-04-15 장전`에는 바로 착수한다.
- `기존 관찰축`은 더 많은 분석을 위한 입력이 아니라, `2026-04-14 장후 개선 결론`과 `2026-04-15 장중 지속 점검`을 위한 검증축으로만 사용한다.
- `계측 완료 + 실전반영 확신도 50% 이상`인 축은 같은 주 canary 착수를 기본값으로 한다. 착수하지 않으면 장후 문서에 보류 사유를 명시한다.
- 장후 결론은 `상태 요약`이 아니라 `날짜 + 액션 + 실행시각` 형식으로 남긴다.
- `WATCHING 75 shadow`, `post-sell canary`, `remote_error snapshot 재점검`은 현재 잔여 작업축에서 제외한다.

## 2026-04-13 장후 승격 요약

- `RELAX-LATENCY`: `강화 유지`
  - `submitted_stocks=0` 유지라 즉시 확대 근거는 없지만, `quote_stale=False` 축을 포함한 `latency_danger_reasons` 분해와 `remote_v2` 관찰은 계속 유효하다.
- `RELAX-DYNSTR`: `유지 + 재설계`
  - `below_window_buy_value / below_buy_ratio / below_strength_base` 분해가 가능한 로그는 확보됐고, `2026-04-15 08:30` 원격 canary용 `momentum_tag` 1축을 고를 준비가 됐다.
- `RELAX-OVERBOUGHT`: `유지`
  - `blocked_overbought=20` 수준으로 표본이 누적돼 실전 완화 재오픈 근거는 없다.
- 체결 품질:
  - `entered_rows=1`, `completed_trades=1`, `holding_events=0`
  - 신규 `submitted/holding_started` 전환이 없어 `full fill / partial fill` 해석은 추가 표본이 필요하다.
- live hard stop taxonomy:
  - `hard_time_stop_shadow`는 여전히 shadow-only로 유지한다.
  - live exit는 `scalp_preset_hard_stop_pct`, `protect_hard_stop`, `scalp_hard_stop_pct`를 분리해서 본다.
- 잔여 작업축 제외:
  - `WATCHING 75 shadow`: `shadow_samples=0` 반복으로 현재 잔여 작업축 제외
  - `post-sell canary`: entry/holding 직접 코드축보다 후순위라 현재 잔여 작업축 제외
  - `remote_error snapshot 재점검`: 오늘 critical path에서 제외, 재발 시 별도 원인 수정으로 대응

## 장전 체크리스트 (08:00~09:00)

- [x] `2026-04-13` 장후 판정이 원격/본서버 설정에 의도치 않게 번진 축이 없는지 확인
- [x] 오늘 이후 `main` 예정 작업마다 `develop T-2/T-1` 선행 적용일이 같이 박혀 있는지 확인
- [x] `RELAX-LATENCY` 관찰 기준을 `quote_stale=False`, `latency_danger_reasons`, `expired_armed` 중심으로 재고정
- [x] `GitHub Project -> Google Calendar` / `Sync Docs Backlog To GitHub Project` 마지막 실행 상태 확인
- [x] `신규 관찰축 추가 금지`, `개선 먼저`, `기존 축은 개선 후 점검용` 원칙을 오늘 작업지시로 재고정
- [x] `계측 완료 + 확신도 50% 이상 = 같은 주 canary 착수` 원칙을 오늘 작업지시로 재고정
- [x] `RELAX-DYNSTR` `2026-04-15 08:30` 원격 canary에 쓸 `momentum_tag` 선정 경로와 환경 설정 경로 확인
- [x] `partial fill min_fill_ratio` 원격 canary 설정 경로와 rollback 가드 확인
제외 메모:
`WATCHING 75 shadow`, `post-sell canary`, `remote_error snapshot 재점검`은 오늘 잔여 작업축에서 다시 열지 않는다.

## 장중 체크리스트 (09:00~15:30)

- [x] `RELAX-LATENCY` 반복 재현성 관찰
  - `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 재확인
  - `quote_stale=False latency_block`와 `expired_armed`를 분리 기록
  - `latency_danger_reasons` 상위 사유 1~3개가 유지되는지 본다
- [x] 체결 품질 관찰
  - `full fill / partial fill`을 분리 기록
  - `preset_exit_sync_mismatch` 여부를 함께 본다
  - `partial fill min_fill_ratio` 원격 canary에 바로 쓸 수 있을 정도로 `min_fill_ratio` 대표 분포를 확인한다
- [x] `RELAX-DYNSTR` 1축 착수용 `momentum_tag` 확정 관찰
  - `below_window_buy_value / below_buy_ratio / below_strength_base`를 `momentum_tag / threshold_profile`별로 계속 분리 기록
  - `missed_winner` 빈도가 가장 높은 `momentum_tag` 1개를 장후에 확정할 근거만 확보한다
- [x] `RELAX-OVERBOUGHT` 표본 누적
  - `blocked_overbought`가 missed-winner와 직접 연결되는지 계속 분리 기록
- [x] `expired_armed` 처리 설계용 대표 표본 고정
  - `latency_block`과 별도 누수 경로로 읽을 대표 케이스와 재진입 허용 후보 조건을 메모한다
- [x] live hard stop taxonomy 관찰
  - `scalp_preset_hard_stop_pct / protect_hard_stop / scalp_hard_stop_pct / hard_time_stop_shadow` 표본 여부를 계속 기록
- [ ] `AI overlap audit`를 `selective override` 착수 입력으로 정리
  - `blocked_stage / momentum_tag / threshold_profile` 교차표가 `2026-04-16` 설계 착수에 바로 쓰일 수준인지 확인한다
- [ ] 장후 개선 결론 준비
  - 신규 가설 발굴이 아니라 `RELAX-LATENCY 반영/보류`, `RELAX-DYNSTR 1축 착수`, `partial fill min_fill_ratio canary`, `expired_armed 설계`를 결정할 만큼만 기존 관찰축을 점검한다

## 장후 체크리스트 (15:30~)

- [x] `RELAX-LATENCY` 운영서버 승격 가능/불가 1차 결론
- [ ] `RELAX-LATENCY` 운영서버 승격 가능/불가 최종 결론
  - `10:00 KST` 중간판정 이후 재점검 시각은 `2026-04-14 15:30 KST` 장후로 고정한다.
- [x] `2026-04-15 main` 예정 축에 대응하는 `develop` 선행 적용 축이 모두 오늘까지 시작됐는지 확인
- [x] 체결 품질 표본이 생기면 `full fill / partial fill / preset_exit_sync_mismatch`까지 포함해 재판정
- [x] `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정값 확정 (`2026-04-15 08:30` 실행용)
- [ ] `partial fill min_fill_ratio` 원격 canary 설정값 확정 (`기본값/예외/롤백가드` 포함)
  - 현재는 `min_fill_ratio` 전용 코드 경로 부재가 blocker이며, 재점검/최종판정 시각은 `2026-04-14 15:30 KST` 장후로 둔다.
- [ ] `expired_armed` 처리 로직 설계 범위와 `2026-04-15 장후` 완료 기준 확정
- [x] `AI overlap audit` 기반 `selective override` 설계 착수일을 `2026-04-16`로 고정
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` write scope / rollback 가드 / 비교지표를 오늘 확정하고 같은 날 착수
- [ ] `SCALPING 모델 shadow 비교안` 범위 / 로그 필드 / 성과 비교식을 오늘 확정
  - 범위 1차는 `WATCHING shared prompt` 동일 입력에 대해 `Tier2 Gemini Flash` vs `GPT-4.1-mini` shadow 비교로 제한한다.
  - 비교 필드는 `gemini_action/score`, `gpt_action/score`, `action_diverged`, `score_gap`, `entered_if_gemini`, `entered_if_gpt`, `realized_pnl_if_gemini`, `realized_pnl_if_gpt`, `missed_winner_cost_if_gemini`, `missed_winner_cost_if_gpt`로 고정한다.
  - `수익예측`은 순수 예측치 대신 장후 체결/미진입 복기와 연결한 `counterfactual realized outcome` 기준으로 먼저 본다.
  - `HOLDING`/`SCALP_PRESET_TP`까지 한 번에 열지 않고 `WATCHING` 1차 shadow가 쌓인 뒤 확장 여부를 판정한다.
- [x] `AIPrompt 작업 8 감사용 핵심값 3종 투입`은 오늘 같은 날 착수
  - 미착수 시 `사유 + 다음 실행시각`을 장후 결론에 남긴다
- [x] `AIPrompt 작업 10 HOLDING hybrid 적용`의 `FORCE_EXIT` 제한형 MVP 범위와 rollback 가드를 오늘 확정하고 같은 날 착수
  - 미착수 시 `사유 + 다음 실행시각`을 장후 결론에 남긴다
- [x] 오늘 착수한 `develop` 축 각각에 대해 `main` 승격 가능 가장 빠른 시점(`2026-04-15` 또는 `2026-04-16`)을 함께 기록
- [x] `2026-04-15` 장전 반영/착수 항목과 `2026-04-16` 후속 설계 착수 항목을 별도 체크리스트로 승격
- [ ] 장후 결론을 `날짜 + 액션 + 실행시각` 형식으로 기록
- [x] `2026-04-15 장중 지속 점검용 관찰축`만 남기고, `신규 관찰축 추가`는 명시적으로 중단
제외 유지 메모:
현재 잔여 작업축에서 제외한 `WATCHING 75 shadow`, `post-sell canary`, `remote_error snapshot 재점검`은 재오픈 조건 없이는 다시 올리지 않는다.

## 2026-04-14 장후 실행 메모

- [x] `GitHub Project -> Google Calendar` / `Sync Docs Backlog To GitHub Project` 마지막 실행 상태 확인
  - 로컬 실행 기준 점검 명령은 `.venv`로 고정하고, 같은 턴에 `sync_docs_backlog_to_project -> sync_github_project_calendar` 순서로 다시 검증했다.
  - 현재 세션 재실행 결과는 두 스크립트 모두 `missing required env: GH_PROJECT_TOKEN`에서 중단됐다.
  - 즉 자동화 로직 자체보다 자격증명 미주입이 현재 blocker다.
- [x] `2026-04-13` 장후 판정이 원격/본서버 설정에 의도치 않게 번진 축이 없는지 확인
  - `2026-04-14 11:54 KST` 기준 재확인 결과 로컬은 `main@42ad673`, 원격은 `develop@7f7bf60e`로 분리 유지 중이다.
  - 원격 `develop` 선행 반영 축과 본서버 `main`은 여전히 분리돼 있고, `partial fill min_fill_ratio`처럼 아직 구현되지 않은 축이 의도치 않게 실전 설정으로 번진 흔적은 확인되지 않았다.
  - 따라서 이 항목은 장전 1회 점검 성격으로 보고, 늦게라도 확인 완료한 시점에서 닫는 것이 맞다.
- [x] `RELAX-DYNSTR` `2026-04-15 08:30` 원격 canary에 쓸 `momentum_tag` 선정 경로와 환경 설정 경로 확인
  - 선정 근거는 `docs/2026-04-13-stage2-todo-checklist.md`의 `momentum_tag / threshold_profile / missed_winner` 관찰 메모를 사용한다.
  - 실행 경로는 [src/engine/sniper_strength_momentum.py](/home/ubuntu/KORStockScan/src/engine/sniper_strength_momentum.py:28)와 [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:162)다.
  - 오늘 보강으로 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED`, `..._TAGS`, `..._ALLOWED_REASONS`, `..._MIN_BUY_VALUE_RATIO`, `..._BUY_RATIO_TOL`, `..._EXEC_BUY_RATIO_TOL` env 경로를 확보했다.
- [x] `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정값 확정 (`2026-04-15 08:30` 실행용)
  - `momentum_tag=SCANNER` 1축으로 고정한다.
  - 허용 사유는 `below_window_buy_value`, `below_buy_ratio`, `below_exec_buy_ratio`만 유지한다.
  - 초기값은 `min_buy_value_ratio=0.85`, `buy_ratio_tol=0.03`, `exec_buy_ratio_tol=0.03` 그대로 두고, 롤백은 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=false` 1개로 닫는다.
  - `main` 승격 판단은 `2026-04-16 POSTCLOSE` 전 금지한다.
- [x] `RELAX-LATENCY` 관찰 기준을 `quote_stale=False`, `latency_danger_reasons`, `expired_armed` 중심으로 재고정
  - 오늘 `10:00 KST` 기준 로컬 `ALLOW_FALLBACK=3`, 원격 `ALLOW_FALLBACK=5`를 다시 확인했고, 오늘 표본은 `quote_stale=False`가 유지된 상태에서 `latency_danger_reasons=ws_age_too_high` 또는 `other_danger`로 모인다.
  - 따라서 장중 해석은 `quote_stale 여부`보다 `latency_danger_reasons`와 `expired_armed` 분리를 우선 기준으로 유지한다.
- [x] `신규 관찰축 추가 금지`, `개선 먼저`, `기존 축은 개선 후 점검용` 원칙을 오늘 작업지시로 재고정
  - `fallback 허용 후 3분 성과`, `늦은 완전체결`은 새 관찰축으로 올리지 않고 기존 `RELAX-LATENCY`/`partial fill` 보조 메모로만 유지한다.
- [x] `계측 완료 + 확신도 50% 이상 = 같은 주 canary 착수` 원칙을 오늘 작업지시로 재고정
  - `RELAX-DYNSTR`는 이미 `2026-04-15 08:30` 원격 canary 시작으로 닫았고, `partial fill min_fill_ratio`는 코드 경로 부재가 blocker라 착수 대신 blocker 기록이 우선이다.
- [x] `partial fill min_fill_ratio` 원격 canary 설정 경로와 rollback 가드 확인
  - 현재 코드베이스에는 `min_fill_ratio` 또는 `cancel_remaining_fast` 전용 설정 경로가 없다.
  - 확인된 현행 경로는 [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1171)의 `partial fill kept, remaining entry orders cancelled` 복구 로직과 [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2286)의 `fallback_qty_canary_applied`뿐이다.
  - 따라서 `2026-04-15 08:30` 실행형 `min_fill_ratio` canary는 값 확정보다 먼저 구현/경로 추가가 필요하고, 전용 rollback 가드도 아직 없다.
- [x] `RELAX-OVERBOUGHT` 표본 누적
  - 현재 판정은 `표본 누적 계속`이며, 실전 완화 재오픈은 하지 않는다.
  - `WAIT 65` missed-winner의 주원인은 여전히 `overbought`보다 `latency/strength` 축으로 본다.
- [x] `expired_armed` 처리 설계용 대표 표본 고정
  - `태광(023160)`은 단일 대표본이 아니라 `anchor case`로만 고정한다.
  - 설계 입력의 본체는 전수 `expired_armed` 표본과 상위 코호트 분포다.
  - `태광`을 남긴 이유는 `entry_armed_expired_after_wait` 누적 상위이면서 `latency_block`과 분리된 기회비용 누수 경로를 설명하기 쉬운 사례이기 때문이다.
  - `2026-04-15 POSTCLOSE` 설계 문서는 `태광` 1건만으로 결론내지 않고, `세미파이브/태광/레이크머티리얼즈/코세스` 상위 코호트와 전수 분포를 함께 사용한다.
- [x] `AI overlap audit` 기반 `selective override` 설계 착수일을 `2026-04-16`로 고정
  - `2026-04-15` `RELAX-DYNSTR` 1일차 canary 결과를 하루 연결한 뒤 시작한다.
  - 설계 입력은 `blocked_stage / momentum_tag / threshold_profile` 교차표로 고정한다.
- [x] `AIPrompt 작업 8 감사용 핵심값 3종 투입`은 오늘 같은 날 착수
  - 착수 범위와 rollback 가드를 `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md`에 고정했다.
  - `develop` 선행 적용 후 `2026-04-16` 1차 평가 전까지 `main` 승격 금지로 둔다.
- [x] `AIPrompt 작업 10 HOLDING hybrid 적용`의 `FORCE_EXIT` 제한형 MVP 범위와 rollback 가드를 오늘 확정하고 같은 날 착수
  - MVP는 일반 `HOLDING`의 `FORCE_EXIT` 제한형만 포함한다.
  - `SELL` 로그 우선 유지, `SCALP_PRESET_TP` 실집행 확장 제외를 오늘 가드로 고정했다.
  - rollback은 `holding_override_rule_version` 기준 on/off와 `holding_action_applied=False` fallback 경로를 기준으로 둔다.
- [x] `2026-04-15` 장전 반영/착수 항목과 `2026-04-16` 후속 설계 착수 항목을 별도 체크리스트로 승격
  - [docs/2026-04-15-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-15-stage2-todo-checklist.md:1)와 [docs/2026-04-16-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-16-stage2-todo-checklist.md:1)에 후속 항목을 유지한다.
- [x] 장후 결론을 `날짜 + 액션 + 실행시각` 형식으로 기록
  - `2026-04-15 08:30`: `RELAX-DYNSTR momentum_tag=SCANNER` 1축 canary 시작
  - `2026-04-15 POSTCLOSE`: `expired_armed` 설계 문서 완료
  - `2026-04-16 INTRADAY`: `AI overlap audit -> selective override` 설계 착수
- [x] `RELAX-LATENCY` 반복 재현성 관찰
  - `10:00 KST` 기준 로컬은 `ALLOW_FALLBACK=3`, 원격은 `ALLOW_FALLBACK=5`가 확인됐다.
  - 오늘 표본에서 `decision=ALLOW_FALLBACK`은 `씨아이에스`, `후성`, `휴림로봇`, 원격 `와이씨` 등으로 반복됐고, `quote_stale=False` 상태의 `ws_age_too_high`/`other_danger`가 계속 보인다.
  - 다만 `fallback 허용 후 3분 성과`는 아직 대표 표본이 얕아 `RELAX-LATENCY` 하위 메모로만 유지한다.
- [x] 체결 품질 관찰
  - 로컬 `씨아이에스`는 `1주 scout -> 108주 44초 후 full fill`로 늦은 완전체결 표본이 생겼고, 원격 `씨아이에스`/`와이씨`는 `preset_exit_sync_mismatch`가 같이 관찰됐다.
  - 따라서 오늘 체결 품질은 `full fill / partial fill / preset_exit_sync_mismatch` 분리 재판정이 가능한 상태다.
- [x] `RELAX-DYNSTR` 1축 착수용 `momentum_tag` 확정 관찰
  - 오늘 `10:00 KST`까지 추가 관찰에서 `SCANNER` 1축 결정을 뒤집을 반례는 없고, `missed_winner` 빈도 기준 `SCANNER` 고정 결론을 유지한다.
- [x] live hard stop taxonomy 관찰
  - 로컬 오늘 표본은 `scalp_preset_hard_stop_pct=2`, `hard_time_stop_shadow=2`, `scalp_soft_stop_pct=1`이다.
  - 오늘 시점에는 `protect_hard_stop`, `scalp_hard_stop_pct` live 표본은 아직 없고, `hard_time_stop_shadow`는 계속 shadow-only로 남아 있다.
- [x] `RELAX-LATENCY` 운영서버 승격 가능/불가 1차 결론
  - `10:00 KST` 1차 결론은 `승격 보류 유지`다.
  - 이유는 `quote_stale=False` fallback 허용은 반복 관찰되지만, 아직 운영서버 승격을 밀 만큼의 반복 개선 근거보다 `씨아이에스` 같은 fallback hard-stop 표본이 더 강하기 때문이다.
- [x] 체결 품질 표본이 생기면 `full fill / partial fill / preset_exit_sync_mismatch`까지 포함해 재판정
  - `씨아이에스`와 원격 `와이씨` 표본으로 재판정했고, `preset_exit_sync_mismatch`는 단발이 아니라 운영 리스크로 계속 추적할 가치가 있다고 본다.
- [x] `2026-04-15 장중 지속 점검용 관찰축`만 남기고, `신규 관찰축 추가`는 명시적으로 중단
  - `2026-04-15`에는 `RELAX-LATENCY`, `RELAX-DYNSTR`, `partial fill`, `expired_armed`, `AIPrompt 5/8/10`만 유지하고, `fallback 허용 후 3분 성과`/`늦은 완전체결`은 독립 축으로 올리지 않는다.
- [x] `SCALPING 모델 shadow 비교안` 1차 판단
  - 현재 코드 기준 `OpenAI 듀얼 페르소나 shadow`는 `gatekeeper/overnight` 전용이며, 라이브 `SCALPING analyze_target()`와 직접 비교되는 구조는 아니다.
  - 따라서 `Tier2 Gemini Flash vs GPT-4.1-mini` 비교는 가능하지만, 별도 `WATCHING shared prompt shadow` 로그 경로와 장후 `counterfactual outcome` 집계가 먼저 필요하다.
  - `수익예측`은 모델 자체 예측문보다 `실제 체결/미진입 결과와 연결된 counterfactual realized outcome` 비교를 1차 기준으로 둔다.
- [x] 스캘핑 공용 프롬프트 실행 모델을 `Tier2 / Gemini Flash`로 통일
  - `analyze_target(strategy=SCALPING)` 경로를 `Tier1 flash-lite`가 아니라 `Tier2 flash`로 라우팅하도록 수정했다.
  - 메인/원격 공통 코드 변경이며, `condition entry/exit`의 `Tier1` 경로와 `overnight/realtime report`의 `Tier2` 경로는 그대로 유지한다.

## 2026-04-14 장중 거래 복기 메모

- `씨아이에스(222080)` 손절 직접 원인은 `main`과 원격 `develop` 모두 `scalp_preset_hard_stop_pct` 도달이다.
- 공통 진입 배경:
  - `09:16` 전후 `strong_absolute_override + AI BUY`로 진입했고, 둘 다 `latency=CAUTION`, `decision=ALLOW_FALLBACK`, `latency_danger_reasons=ws_age_too_high` 상태에서 fallback bundle을 사용했다.
  - 즉 이번 손절은 `AI threshold miss`나 `overbought gate miss`가 아니라, fallback 허용 후 기대한 즉시 돌파가 이어지지 않은 케이스로 본다.
- `main` 체결/청산:
  - `1주 @ 12,220` scout 체결 뒤 `108주 @ 12,190`가 `44초` 후 추가 체결돼 `avg_buy_price=12,190.28`, `qty=109`가 됐다.
  - `09:19:29~31`에 `sell=12,120`, `ret=-0.80%`, `peak_profit=+0.02%`로 청산됐다.
- 원격 `develop` 체결/청산:
  - `1주 @ 12,220`, `18주 @ 12,200`, `22주 @ 12,200`으로 부분 체결이 이어졌고, 정기 동기화에서 최종 보유 수량이 `23주`로 교정됐다.
  - `preset_exit_sync_mismatch`, `refreshed preset TP order number missing`, `매도가능수량 부족`이 같이 발생해 출구 주문 동기화 품질이 깨졌다.
  - `09:19:28~29`에 `sell=12,120`, `ret=-0.88%`, `peak_profit=-0.07%`로 청산됐다.
- 해석:
  - 손절의 본체는 `fallback 진입 후 3분 내 즉시 돌파 실패`다.
  - `main`은 대량 체결이 늦어져 보유 시간 대부분을 불리한 가격대에서 보냈고, 원격은 여기에 `preset_exit_sync_mismatch`와 수량 교정 이슈가 겹쳐 손익이 더 나빠졌다.
  - 이번 건은 `latency guard miss`라기보다 `latency caution 허용 + fallback 체결 품질 저하` 축에 가깝고, 원격은 `holding/protect sync 품질` 이슈가 추가로 증폭 요인이다.
- 후속 메모:
  - `fallback 허용 후 3분 성과`는 별도 관찰축으로 승격하지 않고, 기존 `RELAX-LATENCY` 하위 지표로 `2~3거래일` 더 누적한 뒤 표본이 `5건 이상`이면 승격 여부를 다시 본다.
  - `늦은 완전체결`은 당장은 `partial fill` 메모 안에서 함께 해석하고, 반복 표본이 더 생기면 그때 `delayed_full_fill`로 분리한다.

## 참고 문서

- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-14 12:00:55`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-14.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`6`
  - all_rows local=143 remote=151 delta=8.0; total_trades local=6 remote=12 delta=6.0; entered_rows local=6 remote=12 delta=6.0
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=4 remote=8 delta=4.0; evaluated_candidates local=4 remote=8 delta=4.0
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`5`
  - total_events local=216707 remote=241695 delta=24988.0; tracked_stocks local=133 remote=136 delta=3.0; submitted_stocks local=4 remote=7 delta=3.0
<!-- AUTO_SERVER_COMPARISON_END -->
