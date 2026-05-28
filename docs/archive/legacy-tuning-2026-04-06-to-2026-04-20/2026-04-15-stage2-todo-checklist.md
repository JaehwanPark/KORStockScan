# 2026-04-15 Stage 2 To-Do Checklist

## 목적

- `2026-04-14 장후` 결론을 `2026-04-15 08:30`까지 실제 실행으로 옮긴다.
- 오늘은 `관찰`보다 `착수`가 우선이다. 이미 구축한 관찰축은 변경 후 지속 점검용으로만 사용한다.
- `main` 반영은 오늘 실행하는 `develop` 축의 장후 결과가 있을 때만 연다. 같은 축의 `main` 선적용은 금지한다.
- `RELAX-DYNSTR`는 `momentum_tag` 1축 원격 canary를 시작한다.
- `partial fill min_fill_ratio`는 전용 코드 경로/롤백 토글을 먼저 추가하고, 준비가 끝나는 즉시 원격 canary를 연다.
- `Phase 2`는 오늘 시작한다. `RELAX-LATENCY`가 승격되면 `Phase 2-1`을 병행 착수하고, 승격이 보류되면 `Phase 2-2`를 단독 착수한다.
- `expired_armed` 처리 로직은 오늘 장후까지 설계 문서 완료를 목표로 한다.
- 전일 장후에 착수한 `AIPrompt 작업 5/8/10`은 오늘 구현 진행과 검증 입력 고정까지 이어간다.
- `SCALPING 모델 shadow 비교안`은 `2026-04-15`에 바로 실표본을 수집한다. `PREOPEN` 구현 착수, `INTRADAY` 첫 shadow 수집, `POSTCLOSE` 첫 비교표 생성을 같은 날 닫는다.

## 전일 장후에서 받아야 할 확정값

- `RELAX-LATENCY` 운영 반영/보류 최종 결론
- `RELAX-DYNSTR` 원격 canary 대상 `momentum_tag`
- `partial fill min_fill_ratio` 기본값과 rollback 가드
  - `2026-04-14 15:38 KST` 장후 확정 설계값은 `default=0.20`, `strong_absolute_override=0.10`, `SCALP_PRESET_TP=0.00(적용 제외)`다.
  - 코드 경로/토글은 `2026-04-14 POSTCLOSE`에 구현 완료했고, `2026-04-15`는 env 주입 + dry-run + canary 개시 판정만 수행한다.
- `expired_armed` 처리 로직 설계 범위와 문서 위치
  - `태광` 단일표본이 아니라 전수 `expired_armed` 분포 + 상위 코호트 + anchor case 조합으로 설계한다
- `AI overlap audit -> selective override` 착수 입력과 일정
- `AIPrompt 작업 5/8/10` write scope / rollback 가드 / 비교지표

## 장전 체크리스트 (08:00~08:30)

- [x] `[반영대상: main,remote]` `2026-04-14 장후` 결론대로 `RELAX-LATENCY` 반영/보류 상태를 운영/원격 설정에 적용
- [x] `[반영대상: remote]` `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정 완료 (`08:30`까지)
- [x] `[반영대상: remote]` `partial fill min_fill_ratio` env 주입값 확인 + dry-run 검증 완료 (`08:30`까지)
  - 기본값(`enabled=false`) 확인 후 원격 canary에서만 `enabled=true`로 전환한다.
- [x] `[반영대상: remote]` `SCALPING_PROMPT_SPLIT` 토글/실행값 확인 (`08:20`까지)
  - `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=true`(또는 unset) 확인
  - `ENTRY_PIPELINE/HOLDING_PIPELINE`에서 `ai_prompt_type=scalping_watching/scalping_holding` 표본 1건 이상 확인
- [x] `[반영대상: remote]` 장전 go/no-go 판정 기록 (`08:25~08:30`)
  - `Go`: `partial fill` dry-run 이상 없음 + 프롬프트 분리 표본 확인 + 위험 알람 없음
  - `No-Go`: dry-run 오류/프롬프트 분리 미확인/운영 리스크 발생 시 canary 보류, `사유+재시각` 기록
- [x] `Phase 2` 착수 선언 기록 (`RELAX-LATENCY 승격 시 2-1 병행`, `보류 시 2-2 단독`)
- [x] `[반영대상: main]` 오늘 `develop`에 적용한 축별 `main` 승격 최소 시점(`2026-04-16` 이후)을 작업 메모에 고정
- [x] 오늘 실행 축의 rollback 가드와 장중 관찰 포인트를 재고정
- [x] `expired_armed` 설계 입력은 `단일 종목`이 아니라 `전수 분포 + 상위 코호트 + anchor case` 기준으로 읽는다고 오늘 메모에 고정
- [x] `[반영대상: main,remote]` `SCALPING 모델 shadow 비교안` `WATCHING shared prompt` 구현 착수 및 원격/본서버 공통 로그 필드 고정
  - `08:30`까지 `Tier2 Gemini Flash vs GPT-4.1-mini` shadow 호출 경로와 `action/score/counterfactual` 로그 스키마를 develop 기준으로 닫는다.

## 2026-04-15 장전 실행 메모

- [x] `RELAX-LATENCY` 운영/원격 적용 상태 재확인 (`2026-04-15 07:50 KST`)
  - 판정: `main` 승격은 계속 보류, 원격은 기존 `remote_v2` 관찰축만 유지한다.
  - 근거: 전일 최종 결론이 `운영서버 승격 보류`였고, 오늘도 신규 latency 완화는 추가하지 않는 조건이 유지된다.
  - 다음 액션: 장중에는 `quote_stale=False` 여부보다 `latency_danger_reasons`, `expired_armed`, `preset_exit_sync_mismatch`만 재확인한다.

- [x] `RELAX-DYNSTR momentum_tag=SCANNER` 1축 원격 canary 적용 (`2026-04-15 07:50 KST`)
  - 판정: 적용 완료.
  - 근거: 원격 `override.conf`와 `bot_main.py` 런타임 env에서 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=true`, `..._TAGS=SCANNER`, 허용 사유 3종이 모두 확인됐다.
  - 다음 액션: 장중 퍼널은 `AI BUY -> entry_armed -> budget_pass -> submitted` 순으로만 기록하고, `main` 승격 판정은 `2026-04-16` 이후로 미룬다.

- [x] `partial fill min_fill_ratio` 원격 canary 개시 (`2026-04-15 07:50~07:51 KST`)
  - 판정: `Go`.
  - 근거: 원격 `.venv` 기준 관련 테스트 `74 passed`, `py_compile` 통과, `gunicorn`/`bot_main.py` 런타임 env에서 `enabled=true`, `default=0.20`, `strong_absolute_override=0.10`, `SCALP_PRESET_TP=0.00` 확인.
  - 다음 액션: 장중에는 `partial fill 억제`뿐 아니라 `submitted 감소/미진입 기회비용`까지 같이 본다.

- [x] `SCALPING_PROMPT_SPLIT` / `WATCHING shared prompt shadow` 착수 (`2026-04-15 07:51 KST`)
  - 판정: 코드 착수 및 공통 로그 필드 고정 완료.
  - 근거: `watching_shared_prompt_shadow` stage에 `gemini_action`, `gemini_score`, `gpt_action`, `gpt_score`, `action_diverged`, `score_gap`, `gpt_model`, `shadow_extra_ms`를 남기도록 구현했고, 원격 `bot_main.py` 재기동까지 완료했다.
  - 다음 액션: 장중 첫 표본 발생 후 `counterfactual` 연결은 장후 비교표에서 묶는다.

- [x] `Phase 2` 착수 선언 / 오늘 메모 고정 (`2026-04-15 07:51 KST`)
  - 판정: `RELAX-LATENCY` 승격 보류 기준으로 `Phase 2-2 단독 착수`.
  - 근거: 오늘 실제 실행 축은 `RELAX-DYNSTR`, `partial fill`, `WATCHING shared prompt`이며, `main` 승격 최소 시점은 `2026-04-16 POSTCLOSE 이후`로 고정한다.
  - 다음 액션: `expired_armed` 설계 문서는 전수 분포 + 상위 코호트 + anchor case 기준으로 장후까지 닫는다.

- [x] 오늘 실행 축 rollback 가드 / 장중 관찰 포인트 재고정 (`2026-04-15 07:51 KST`)
  - 판정: rollback 가드가 한 축씩 분리돼 있어 canary 운영 가능.
  - 근거: `RELAX-DYNSTR`는 `KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED=false`, `partial fill`은 `KORSTOCKSCAN_SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=false`, 프롬프트 분리는 `KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED=false` 1개 토글로 각각 닫힌다.
  - 다음 액션: 장중에는 `blocker 분포`, `체결 품질(full/partial 분리)`, `WATCHING shared prompt shadow action_diverged`만 본다.

## 장중 체크리스트 (09:00~15:30)

- [x] `RELAX-DYNSTR` 1축 canary의 `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 변화를 기록 (`2026-04-15 15:58 KST`)
  - 판정: `budget_pass`까지는 반복 진입, `submitted` 전환은 미확인
  - 근거: `ENTRY_PIPELINE` 집계 `entry_armed=6`, `entry_armed_resume=55`, `budget_pass=61`, `submitted=0`; `dynamic_reason`은 `strong_absolute_override` 중심
  - 다음 액션: `2026-04-16 PREOPEN`에 `budget_pass -> submitted` 절단 지점(`order_submit_guard/cooldown/orderbook`) 분리 계측 후 1축 재판정
- [x] `partial fill min_fill_ratio` canary(개시 시)의 `partial fill 억제 / 체결 기회 감소`를 함께 기록 (`2026-04-15 15:58 KST`)
  - 판정: 표본 부족으로 효과 판정 유보
  - 근거: 메인/원격 `trade_review` 공통 `partial_fill_events=0`, `full_fill_events=0` (당일 해당 코호트 표본 없음)
  - 다음 액션: `2026-04-16 INTRADAY`부터 `partial_fill_ratio_below_min` 이벤트와 `submitted 감소`를 동시 수집
- [x] `RELAX-LATENCY`는 전일 결론대로 적용된 축만 지속 점검하고, 신규 완화는 추가하지 않는다 (`2026-04-15 15:59 KST`)
  - 판정: 준수
  - 근거: 오늘 신규 latency 완화 토글/코드 반영 없음, 관찰은 `latency_block/expired_armed` 계측 중심으로 유지
  - 다음 액션: `2026-04-16`에도 신규 완화 없이 동일 축 점검 지속
- [x] 기존 관찰축은 `변경 후 검증`에 필요한 범위로만 유지한다 (`2026-04-15 15:59 KST`)
  - 판정: 준수
  - 근거: 장중 기록이 `RELAX-DYNSTR`, `partial fill`, `watching shared shadow`, `expired_armed` 4축으로 수렴
  - 다음 액션: 신규 관찰축 추가 금지, 기존 4축의 지표 완결도만 보강
- [x] `expired_armed` 전수 분포 재확인 (`2026-04-15 16:00 KST`)
  - 시간대 / 종목 / `momentum_tag` / `threshold_profile` / `entry_armed_expired_after_wait` 상위 코호트를 다시 묶는다
  - `태광`은 anchor case로만 유지하고 단일 종목 결론으로 확대하지 않는다
- [x] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 구현 진행 / 로그 비교축 확인 (`2026-04-15 16:01 KST`)
  - 판정: 진행 중(검증축 확인 완료)
  - 근거: `SCALPING_PROMPT_SPLIT_ENABLED=true`(원격), `watching_shared_prompt_shadow` 표본 `remote=22`, `main=1`, `action_diverged` 기록 확인
  - 다음 액션: `2026-04-16`에는 `holding` 경로의 분리 품질(`prompt_type`, `decision_type`)을 추가 검증
- [x] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 구현/검증 지속 (`2026-04-15 16:02 KST`)
  - 판정: 구현 경로 확인, 운영 로그 검증은 부분완료
  - 근거: 코드에 `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct` 계산/주입 경로 존재
  - 다음 액션: `*_sent` 감사 로그 키가 운영 로그에 직접 노출되도록 `2026-04-16 POSTCLOSE` 보강
- [x] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 구현 지속 / canary-ready 입력 정리 (`2026-04-15 16:03 KST`)
  - 판정: MVP 착수 상태 유지, canary-ready는 보류
  - 근거: 설계 문서/코드 경로는 존재하나 `FORCE_EXIT` 실집행 표본과 오발동 안전지표 미충족
  - 다음 액션: `2026-04-16` 입력(`override_triggered`, `FORCE_EXIT precision`, `trailing 충돌률`) 고정 후 canary-ready 재판정
- [x] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리 (`2026-04-15 16:04 KST`)
  - 판정: 초안 확정
  - 근거: `tick_acceleration_ratio`, `same_price_buy_absorption`, `large_sell_print_detected`, `ask_depth_ratio`, `net_aggressive_delta_10t`를 1차 helper 범위로 고정
  - 다음 액션: `2026-04-17` 확정본으로 승격
- [x] `SCALPING 모델 shadow 비교안` 첫 실표본 수집 시작 (`2026-04-15 16:04 KST`)
  - `WATCHING shared prompt` 동일 입력에 대해 `gemini_action/score`, `gpt_action/score`, `action_diverged`, `score_gap`를 오늘 장중부터 누적한다.
  - 판정: 수집 시작 완료
  - 근거: 원격 `watching_shared_prompt_shadow=22건`, `action_diverged=6건`; 메인 `1건`
  - 다음 액션: 장후 비교표에서 EV 근사치와 함께 결론화
- [x] 원격 `BROKER_RECOVER legacy` 포지션 과손절 가드 적용 및 `kt00008` 대조 연결 (`2026-04-15 11:10 KST`)
  - 판정: legacy 보유 복구 포지션은 감시 유지, 즉시 스캘핑 손절 제외로 긴급 완화 완료.
  - 근거: `006360/016360/066570/138040` 계열은 복구 직후 `SCALPING` 손절 규칙에 태워질 위험이 있었고, 코드에서 `broker_recovered_legacy` 플래그로 `soft/hard stop`, `never_green`, `AI early exit`를 건너뛰게 수정했다. 동시에 `kt00008` 익일결제예정 체결 스냅샷으로 전일 매수 체결 여부를 대조해 `legacy=true`, `exec_verified=true`를 로그에 남기도록 보강했다.
  - 다음 액션: 장후에는 `legacy 가드 적용 종목의 장중 PnL drift`와 `수동/overnight 정리 필요 종목`을 분리 기록한다.

## 장후 체크리스트 (15:30~)

- [x] `2026-04-15` 장후 운영모드 판정 고정 (`2026-04-15 14:20 KST`)
  - 판정: **No-Decision Day** (`분석/복기 진행`, `실전 파라미터 변경·승격 보류`)
  - 근거: 장중 서비스 오류/다중 재기동으로 상태전이·집계 왜곡 위험이 높음
  - 다음 액션: 품질게이트 통과 항목만 익일 장전에 canary 1축으로 반영 검토
- [x] `report integrity gate` 통과 여부 판정 (오늘 의사결정 전제조건) (`2026-04-15 15:55 KST`)
  - `COMPLETED + valid profit_rate` 기준 손익 집계 재검증
  - `NULL/미완료/fallback 정규화값` 손익 제외 여부 확인
  - 원격/메인 `실계좌 vs DB vs 메모리` 스냅샷 정합성 로그 1세트 첨부
- [x] `event restoration gate` 통과 여부 판정 (`2026-04-15 15:56 KST`)
  - 재기동 전후 `BUY_ORDERED→HOLDING`, `HOLDING→COMPLETED` 강제전환 이벤트 복원 품질 점검
  - `broker_recover`, `periodic_account_sync`, `preset_exit_sync_mismatch` 분리 집계
- [x] `aggregation quality gate` 통과 여부 판정 (`2026-04-15 15:57 KST`)
  - 대시보드 기준일(`rec_date`)과 실보유(`all open holdings`) 분리 표기 검증
  - full fill / partial fill 분리 지표 재생성
- [x] `expired_armed` 처리 로직 설계 문서 작성 완료 (`2026-04-15 16:06 KST`)
  - 재진입 허용 여부는 `태광` 1건이 아니라 전수 분포와 상위 코호트 기준으로 판정한다
  - 문서에는 `anchor case`와 `통계 입력`을 분리해서 쓴다
  - 결과 문서: [2026-04-15-expired-armed-design.md](./2026-04-15-expired-armed-design.md)
- [x] `RELAX-DYNSTR` 1일차 canary 결과 1차 정리 (`2026-04-15 16:06 KST`)
  - 판정: 유지/보정 필요 (`submitted 전환 부재`)
  - 근거: `entry_armed+resume`는 증가했으나 `budget_pass_to_submitted_rate=0.0%`
  - 다음 액션: `2026-04-16` 장전에는 신규 완화 없이 계측 보강 후 재평가
- [x] `partial fill min_fill_ratio` 구현/검증 결과와 canary 개시 여부 1차 정리 (`2026-04-15 16:07 KST`)
  - 판정: canary 개시는 유지, 효과 평가는 유보
  - 근거: 토글 활성은 확인(`remote env=true`), 당일 partial/full fill 이벤트가 없어 효익/기회비용 계량 불가
  - 다음 액션: 최소 표본(`partial_fill_events>=3`) 확보 시점에 재판정
- [x] 오늘 `develop` 결과 기준으로 `2026-04-16 main` 승격 가능/불가 초안을 항목별로 기록 (`2026-04-15 16:08 KST`)
  - 오늘은 승격/파라미터 변경 확정 금지, `가능/불가 초안`까지만 작성
- [x] `2026-04-16` `AI overlap audit -> selective override` 설계 착수 입력값을 고정 (`2026-04-15 16:09 KST`)
  - 판정: 입력값 고정 완료
  - 근거:
    - `expired_armed_total`: main `374`, remote `394`
    - `budget_pass_to_submitted_rate`: main/remote `0.0%`
    - `watching shadow action_diverged`: main `1/1`, remote `6/22`
  - 다음 액션: `2026-04-16 PREOPEN`에 `override 후보 stage`를 `entry_armed_expired_after_wait`, `budget_pass_no_submit`, `watching_diverged` 3축으로 고정
- [x] `AIPrompt 즉시 코드축` 구현 진행 결과 정리 (`2026-04-15 16:10 KST`)
  - `작업 5/8/10`의 `2026-04-16` 평가 포인트를 고정한다
- [x] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 결과 정리 (`2026-04-15 16:11 KST`)
  - 판정: 부분완료
  - 근거: 코드 주입 확인, 운영 로그의 `*_sent` 감사키 노출 미확인
  - 다음 액션: `2026-04-16 POSTCLOSE`에 감사키 로그 명시화
- [x] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안을 `2026-04-17` 확정형으로 정리 (`2026-04-15 16:11 KST`)
  - 판정: 초안 정리 완료(확정 대기)
  - 근거: 대상 피처 6개와 helper 경계 정의 완료
  - 다음 액션: `2026-04-17 10:00 KST` 확정본 반영
- [x] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 착수 상태와 `2026-04-16` 입력값 정리 (`2026-04-15 16:12 KST`)
  - 판정: 착수 유지, 실전 canary 미개시
  - 근거: `FORCE_EXIT` 제한형 설계는 있으나 운영 표본/안전지표 부족
  - 다음 액션: `2026-04-16` 입력값(precision/false positive/override 충돌률) 고정 후 canary-go/no-go
- [x] `SCALPING 모델 shadow 비교안` 첫 장후 비교표 생성 (`2026-04-15 16:12 KST`)
  - `entered_if_gemini`, `entered_if_gpt`, `realized_pnl_if_gemini`, `realized_pnl_if_gpt`, `missed_winner_cost_if_gemini`, `missed_winner_cost_if_gpt`를 오늘 체결/미진입 복기와 연결해 1차 비교표로 남긴다.
  - 1차 비교표(당일 표본):
    - `main`: shadow `1`, diverged `1` (`score_gap=-45`)
    - `remote`: shadow `22`, diverged `6`
    - `entered_if_gemini/gpt`: 당일 로그만으로 확정 불가(실집행 매핑키 부족) → EV 비교는 익일 보강
- [x] 오늘 보류된 항목이 있으면 `사유 + 다음 실행시각`을 문서에 명시 (`2026-04-15 16:13 KST`)
- [x] `kt00007/ka10076` 파라미터 확정 후 `원주문번호 API 대조` 2차 고도화 (`2026-04-15 17:25 KST`)
  - 판정: 완료 (`query profile`: `qry_tp=0`, `stk_bond_tp=0`)
  - 근거:
    - `kiwoom_utils`에 `kt00007/ka10076` 공통 정규화 스냅샷(`ord_no`, `orig_ord_no`)과 대조 매처를 추가했다.
    - `sniper_sync` `broker recover` 경로에 2차 대조(선택 실행) 연동: `kt00008` 미검증이어도 주문참조 매칭 시 `exec_verified=True` + `odno` 복구.
    - 테스트: `test_kiwoom_order_ref_snapshot.py`, `test_periodic_account_sync_recovers_order_ref_when_kt00008_empty` 통과.
  - 다음 액션: `2026-04-16 POSTCLOSE`에 원격 실표본 1건 이상에서 `ord_no/orig_ord_no` 매칭률과 오탐 여부를 기록해 canary 유지/보정 판정

### 2026-04-15 보류 항목 및 재실행 시각

- [x] `kt00007/ka10076 원주문번호 API 대조 2차` 보류
  - 사유: 장중/장후 핵심 품질게이트 및 canary 판정 우선 처리
  - 다음 실행시각: `2026-04-16 10:30~11:00 KST (INTRADAY)`
- [x] `task8 감사키 *_sent 로그 명시화` 보류
  - 사유: 코드 주입은 확인됐으나 운영 로그 포맷 보강 미완
  - 다음 실행시각: `2026-04-16 15:40~16:00 KST (POSTCLOSE)`
- [x] `shadow EV counterfactual(entered_if_*/realized_pnl_if_*)` 확정 보류
  - 사유: 당일 로그에서 실집행 매핑키가 부족해 EV 산출 신뢰도 부족
  - 다음 실행시각: `2026-04-16 16:00~16:20 KST (POSTCLOSE)`

## 익일 이월 작업 (수동 동기화 예정)

- [x] `No-Decision Day` 해제 판정 (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:25`) (`실행: 2026-04-15 15:55 KST`)
  - 판정: `해제 보류` (No-Decision Day 유지)
  - 근거:
    - `integrity`: `main valid/invalid=31/0`, `remote valid/invalid=42/0`으로 통과
    - `restoration`: `15:47` 양 서버 `데이터 동기화 완료 + 메모리 일치` 확인
    - `aggregation`: `report_2026-04-15.json`에 `trades` 섹션 부재, `open holdings` 노출 불완전으로 미통과
  - 다음 액션: `2026-04-16 PREOPEN`에 aggregation 보정 전까지 운영 의사결정 권한을 `분석/복기`로 제한
- [x] 품질게이트 3종(`integrity/restoration/aggregation`) 통과 결과를 기준으로 canary 1축 실행 여부 확정 (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:25~08:35`) (`실행: 2026-04-15 15:56 KST`)
  - 판정: `canary 1축 신규 실행 보류`
  - 근거:
    - gate-1(integrity)=`PASS`
    - gate-2(restoration)=`PASS`
    - gate-3(aggregation)=`FAIL`
  - 다음 액션: `gate-3` 보정 후에만 canary 1축 재판정 (`pass 조건: dashboard에 all-open holdings와 기준일 집계 분리 표기`)
- [x] 실전 파라미터/승격 변경은 `gate pass=true`일 때만 적용 (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:45`) (`실행: 2026-04-15 15:57 KST`)
  - 판정: `오늘 변경 없음` (정책 준수)
  - 근거: 3개 게이트 중 1개(`aggregation`) 미통과로 `gate pass != true`
  - 다음 액션: `2026-04-16 PREOPEN` 재판정 전까지 `main/develop` 실전 파라미터 및 승격 동결

### 2026-04-15 15:55~15:57 KST 검증 결과

- [x] 메인 정합성 검증: `EXCH_OK=KRX,NXT`, `ONLY_REAL=[]`, `ONLY_DB=[]`, `QTY_MISMATCH=[]`
- [x] 원격 정합성 검증: `EXCH_OK=KRX,NXT`, `ONLY_REAL=[]`, `ONLY_DB=[]`, `QTY_MISMATCH=[]`
- [x] 메인/원격 손익 무결성: `COMPLETED_INVALID=0` 확인
- [x] 메인/원격 복원 로그: `15:47 데이터 동기화 완료/메모리 일치` 확인
- [x] 집계 품질 점검: 메인/원격 `report_2026-04-15.json` 공통 `trades` 섹션 비어 있음(`{}`) 확인

## 참고 문서

- [2026-04-14-stage2-todo-checklist.md](./checklists/2026-04-14-stage2-todo-checklist.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-15-tuning-result-report-for-auditor.md](./2026-04-15-tuning-result-report-for-auditor.md)
- [2026-04-15-main-scalping-performance-pros-cons-audit-report.md](./2026-04-15-main-scalping-performance-pros-cons-audit-report.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-15 12:01:01`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-15.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`6`
  - all_rows local=184 remote=193 delta=9.0; total_trades local=25 remote=31 delta=6.0; entered_rows local=25 remote=31 delta=6.0
- `Performance Tuning`: status=`ok`, differing_safe_metrics=`14`
  - holding_review_ms_avg local=6312.72 remote=5721.19 delta=-591.53; gatekeeper_eval_ms_p95 local=13249.0 remote=12876.0 delta=-373.0; gatekeeper_action_age_p95 local=1484.18 remote=1310.83 delta=-173.35
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=22 remote=26 delta=4.0; evaluated_candidates local=22 remote=26 delta=4.0
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`5`
  - total_events local=104550 remote=97741 delta=-6809.0; tracked_stocks local=142 remote=152 delta=10.0; submitted_stocks local=3 remote=5 delta=2.0
<!-- AUTO_SERVER_COMPARISON_END -->
