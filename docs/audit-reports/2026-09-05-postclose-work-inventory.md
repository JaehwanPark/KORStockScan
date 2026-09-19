# 장후작업 현행 활성 목록

## 0. 현행 기준 — 2026-09-19 KST

이 문서는 설치 schedule, 활성 wrapper 내부 호출, PREOPEN 소비자, 코드만 남은 비활성 작업을 구분한다. 실행 이력과 이미 삭제된 작업은 싣지 않는다. 결과 판정은 [장후 결과 점검 지시문](../postclose-tuning-result-review-task-instructions.md)을 따른다.

현행 근거는 설치 `crontab -l`, systemd timer, 선택 release wrapper와 직접 consumer다. 작업공간 파일의 존재만으로 설치 또는 자연 실행을 주장하지 않는다.

## 1. 설치 schedule

| 순서 | 시각 | 설치 owner | 상태와 직접 결과 |
| --- | --- | --- | --- |
| 1 | 20:05 평일 | `run_runtime_release.sh eod` | 설치 ON. EOD DB 갱신과 exact-date terminal을 확인한다. |
| 2 | 20:10 평일 | `korstockscan-samsung-widget-evaluation.timer` | 설치 ON. widget advisory, auto-trade, symbol research, runtime policy의 같은 completed date를 확인한다. |
| 3 | 21:15 평일 | `korstockscan-machine-microstructure-final-refresh.timer` | 설치 ON. attribution→hysteresis→entry timing→capacity→closed-loop→approval→checklist 순서와 unit terminal을 확인한다. |
| 4 | 07:35 평일 | `run_runtime_release.sh preopen` | 설치 ON. family publisher 뒤 runtime policy bootstrap을 생성·검증하고 다음 정상 기동이 소비한다. |

현재 crontab에는 main postclose, controller, tuning late-pass, archive, finalization router 실행행이 없다. 주석은 schedule가 아니다. 이 항목들은 설치 복구 전에는 `정기 ON`으로 표시하지 않는다.

## 2. main postclose wrapper의 현행 호출 순서

아래 순서는 wrapper가 실행될 때의 코드 순서다. 현재 설치 schedule가 없으므로 자연 실행 완료와 구분한다.

| 순서 | owner | 상태·검증 대상 |
| --- | --- | --- |
| 1 | `scalping.ai_action_outcome_calibration --ensure-economic-reference-only` | 비용 근거 준비. 결손을 0으로 대체하지 않는다. |
| 2 | `sniper_post_sell_feedback` | sim 결과 source-only. 실현 손익이나 승인으로 승격하지 않는다. |
| 3 | `monitoring.rising_missed_intraday_feedback` | miss/blocker/후행 결과 진단. |
| 4 | `observation_source_quality_audit --audit-phase preflight` | exact-date 원천 admission과 row/window exclusion. |
| 5 | `low_price_two_leg_expanded_candidate_research` → `low_price_two_leg_auto_expansion_policy` | holdout·비용·terminal이 있는 별도 family 연구와 dated 발행. |
| 6 | `market_panic_breadth_collector --report-only` | 시장 context. 주문 권한 없음. |
| 7 | `strategy_position_performance_report --sync` | real/sim·full/partial·COMPLETED valid profit·비용 fact. |
| 8 | `scale_in_split_order_plan` | 실제 ADD 원자성·paired cost EV·정책 receipt. |
| 9 | `entry_split_order_plan` | submitted/no-submit/no-fill·4-arm 비용 EV·정책 receipt. |
| 10 | `ai_decision_quality` → `ai_action_outcome_calibration --postclose-phase prepare` | source label과 compact/machine 경제성 준비. |
| 11 | `automation.entry_cancel_wait_tuning` | 실제 제출·취소·native exit/cost 기반 독립 정책. |
| 12 | Swing 계열 | 기본 OFF. `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=true`일 때만 실행한다. |
| 13 | `pipeline_event_verbosity_report` | 운영 진단. EV 근거가 아니다. |
| 14 | `observation_source_quality_audit --audit-phase final` | 최종 원천 품질과 경제성 admission. |
| 15 | `samsung_machine_entry_tuning` | actual machine entry 분석과 candidate receipt. |
| 16 | `low_price_two_leg_tuning` | actual/HELD/terminal/cost 기반 family 평가. |
| 17 | `ai_action_outcome_calibration --postclose-phase evaluate` | 준비된 동일 generation만 평가. |
| 18 | 성능/regime/producer-gap/stage-hook 분기 | 기본 OFF. 활성 flag가 있을 때만 실행하며 현재 필수 owner가 아니다. |
| 19 | `intraday_ws_freshness_monitor --finalize --monitor-only` | WS 품질 마감과 scanner family 입력. |
| 20 | `ai_action_outcome_calibration --postclose-phase finalize` | compact/machine 직접 publisher handoff. |
| 21 | Swing propagation/review | Swing가 활성일 때만 실행한다. |
| 22 | `rising_missed_classifier_prior` | 최근 20개 feedback의 동일 attempt를 비용 후 paired 평가하고 다음 장전용 dated receipt를 발행한다. 검증된 edge가 없으면 임계값을 바꾸지 않는다. |
| 23 | `runtime_approval_summary` | 위 family 원천·정책·runtime receipt의 날짜·해시를 직접 요약한다. 공통 후보를 만들지 않는다. |
| 24 | `ai_action_outcome_calibration --postclose-phase handoff` | final consumer receipt. |
| 25 | `verify_threshold_cycle_postclose_chain` | compact scoped 검증 뒤 직접 family source·hash·terminal 검증. |
| 26 | `build_next_stage2_checklist` | 직접 증거 결손만 stable task로 생성한다. |
| 27 | print-only backlog parser → pending/final verifier → status/DONE | 외부 동기화, 재기동, 주문을 실행하지 않는다. |

## 3. PREOPEN 및 장중 소비 순서

1. low-price, machine microstructure, machine entry timing, scanner lookup-attention의 기존 family publisher를 실행하고, 존재하는 rising-missed TP1 dated receipt를 수집한다.
2. `automation.runtime_policy_bootstrap`이 마지막 검증된 incumbent, allowlist를 통과한 rising-missed 단일축 정책, operator lock, explicit retirement OFF를 합성한다. Rising-missed `incumbent_preserved` receipt는 환경을 바꾸지 않는다.
3. bootstrap은 EV를 계산하거나 후보를 만들지 않는다. manifest/env 날짜·원천 해시·self hash가 틀리면 기동을 차단한다.
4. entry setup과 holding policy는 family별 dated artifact를 직접 검증한다.
5. `src/run_bot.sh`는 exact-date bootstrap env를 source하고 handoff를 검증한 뒤 정상 기동 경로로 간다. 기존 실행 PID에 hot reload하지 않는다.
6. 자연 PID 소비, 주문, 체결, terminal, 비용 반영 EV는 배포 성공과 별도의 acceptance다.

## 4. 코드베이스만 남은 비활성 작업

다음 구현은 다른 진단·역사 날짜 호환·명시적 수동 분석을 위해 코드가 남아 있으나 현행 main wrapper 또는 설치 schedule의 필수 작업이 아니다.

| 코드 owner | 현행 분류 |
| --- | --- |
| `runtime_apply_gap_audit`, `key_lineage_ledger`, `conversion_lane` | 비활성 진단. 직접 family 검증의 완료 조건이 아니다. |
| `build_code_improvement_workorder` | main wrapper 기본 OFF. 공통 튜닝 입력으로 자동 생성하지 않는다. |
| `tuning_performance_control_tower`, `postclose_summary_handoff` | 수동/호환 요약. runtime authority가 없고 직접 family summary만 참조해야 한다. |
| Swing discovery/lifecycle/pattern modules | 기본 OFF. 명시적 Swing scope에서만 실행한다. |
| performance/regime/producer-gap/stage-hook modules | 기본 OFF. 코드 존재를 설치 또는 당일 결손으로 해석하지 않는다. |

## 5. 결과 점검 순서

각 활성 owner를 `terminal → 원천 날짜·해시·표본 → 비용 반영 비교 EV/일별 순익 → policy receipt → 직접 runtime consumer → 자연 PID·결정·주문·terminal` 순서로 확인한다. `PASS`, `DONE`, 파일 존재, 배포 receipt는 경제성 승인과 분리한다. source gap, no-trade, no-fill, partial, held, custody-censored를 서로 대체하지 않는다. ETA를 입증할 수 없으면 `null`로 둔다.
