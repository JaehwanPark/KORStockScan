# 장후작업 현행 활성 목록

## 0. 현행 기준 — 2026-09-20 KST

이 문서는 설치 schedule, 활성 wrapper 내부 호출, PREOPEN 소비자, 남은 점검 대상을 구분한다. 실행 이력과 이미 제거된 작업은 현행 작업으로 싣지 않는다. 결과 판정은 [장후 결과 점검 지시문](../postclose-tuning-result-review-task-instructions.md)을 따른다.

현행 근거는 설치 `crontab -l`, systemd timer의 effective unit, 공통 router 선택 release wrapper, [2026-09-21 Stage2 체크리스트](../checklists/2026-09-21-stage2-todo-checklist.md), 직접 consumer다. 작업공간 파일의 존재만으로 설치 또는 자연 실행을 주장하지 않는다.

- 공통 router 선택 release: `compact-aux-future-evidence-reviewed-20260920-a198c3b9b`
- commit: `a198c3b9bb3e0d78bff3feebe05b3d394a467973`
- 선택 시각: `2026-09-20T11:10:56+09:00`
- 실제 PID 소비: `false` (`pending_next_normal_start`)

## 1. 설치 schedule

| 순서 | 시각 | 설치 owner | 현행 상태와 점검 경계 |
| --- | --- | --- | --- |
| 1 | 19:30~19:59 매일 | `run_monitoring_instruction_refresh.sh --mode postclose` | 설치 ON. workspace 문서 갱신 owner이며 release router를 통하지 않는다. 반복 분은 wrapper lock·currentness 계약으로 판정한다. |
| 2 | 20:05 평일 | `run_runtime_release.sh eod` | 설치 ON. 공통 선택 release에서 EOD DB 갱신을 수행한다. 장후 경제성 평가와 별도 owner다. |
| 3 | 20:10 평일 | `run_runtime_release.sh postclose` | 설치 ON. 선택 release의 main postclose wrapper를 실행한다. `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false`, bot action은 `stop`이다. |
| 4 | 20:10 평일 | `korstockscan-samsung-widget-evaluation.timer` | 설치 ON·waiting. effective `ExecStart`/working directory는 `low-price-carry-joint-economics-20260918`, `PYTHONPATH`·project/python은 `low-price-postclose-source-resume-20260918`로 갈라져 있다. 동일 source/runtime 계약이 입증되기 전에는 정상 handoff로 판정하지 않는다. |
| 5 | 21:15 평일 | `korstockscan-machine-microstructure-final-refresh.timer` | 설치 ON·waiting. effective 실행·환경은 `market-weakness-final-review-20260918`이다. main summary/DONE보다 늦게 끝날 수 있어 모든 필수 producer terminal 뒤 최종 인계 owner가 필요하다. |
| 6 | 다음 거래일 07:35 | `run_runtime_release.sh preopen` | 설치 ON. family publisher 결과로 runtime policy bootstrap을 생성·검증한다. 실제 PID 소비와 자연 주문·손익은 별도 acceptance다. |

`controller`, `tuning`, `archive`, `finalize`는 선택 release router와 wrapper가 존재하지만 설치 crontab 실행행은 없다. 특히 crontab 주석과 main wrapper는 21:55 finalization이 late widget/machine 결과를 summary→checklist→strict verification에 다시 연결한다고 전제하지만, 현재 finalization은 설치되지 않았다. 더구나 finalization wrapper는 controller·tuning·archive terminal도 기다리므로 finalization 한 줄만 추가해서는 닫히지 않는다. 이 상태는 시간이 지나도 해소되지 않는 schedule/owner 계약 결손이다.

BUY funnel, HOLD/EXIT, panic-sell defense, rising-missed, WS freshness, market-opportunity census는 장중·aftermarket source producer다. 독립 장후 튜닝 작업으로 중복 기재하지 않는다.

## 2. main postclose wrapper의 현행 호출 순서

아래 순서는 선택 release의 실제 코드 순서다. wrapper terminal, 경제성 승인, 다음 PREOPEN 소비, 실제 PID 소비를 서로 대체하지 않는다.

| 순서 | owner | 역할과 판정 경계 |
| --- | --- | --- |
| 1 | `scalping.ai_action_outcome_calibration --ensure-economic-reference-only` | 비용 근거를 준비한다. 결손을 0으로 대체하지 않는다. |
| 2 | `sniper_post_sell_feedback` | sim 결과와 후행 source를 정리한다. 실현 손익이나 승인으로 승격하지 않는다. |
| 3 | `monitoring.rising_missed_intraday_feedback` | miss/blocker/후행 결과 진단을 만든다. |
| 4 | `observation_source_quality_audit --audit-phase preflight` | exact-date 원천 admission과 row/window exclusion을 판정한다. |
| 5 | `low_price_two_leg_expanded_candidate_research` → `low_price_two_leg_auto_expansion_policy` | 저가주 확장 family의 연구와 dated handoff다. |
| 6 | `market_panic_breadth_collector --report-only` | 시장 context를 만든다. 주문 권한은 없다. |
| 7 | `strategy_position_performance_report --sync` | real/sim, full/partial, `COMPLETED + valid profit_rate`, 비용 fact를 정리한다. |
| 8 | `scale_in_split_order_plan` | 실제 ADD 원자성, 비용 차감 paired EV, 정책 receipt를 평가한다. |
| 9 | `entry_split_order_plan` | submitted/no-submit/no-fill, 4-arm 비용 EV, 정책 receipt를 평가한다. |
| 10 | `ai_decision_quality` | 오판 분석용 source label과 receipt를 materialize한다. 후보 선택·경제성 승격 owner는 아니다. |
| 11 | `automation.entry_cancel_wait_tuning` | 실제 제출·취소·native exit/cost 기반 cancel-wait family를 평가한다. |
| 12 | Swing 계열 | 기본 OFF. 현재 설치 env의 `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false`에서 실행하지 않는다. |
| 13 | `pipeline_event_verbosity_report` | 운영 진단이다. EV 근거가 아니다. |
| 14 | `observation_source_quality_audit --audit-phase final` | 최종 원천 품질과 경제성 admission을 다시 판정한다. |
| 15 | `samsung_machine_entry_tuning` | 삼성 machine-entry 관측과 candidate receipt를 만든다. 2026-09-17 summary에서는 report-only·runtime 변경 없음이다. |
| 16 | `low_price_two_leg_tuning` | actual/HELD/terminal/cost 기반 저가주 family 경제성을 평가한다. |
| 17 | `ai_action_outcome_calibration --machine-only --require-policy-publication` | 메인 기계판정 full population을 평가하고 다음 거래일 incumbent/candidate 정책을 발행한다. compact와 별도 owner다. |
| 18 | `entry_setup_paired_replay_batch --compact-only --execute-compact-candidate` → `--finalize-compact` | compact 보조 AI의 exact pre-AI plan 기반 paired 평가와 dated policy를 발행한다. 과거 결손은 제외하고 미래 정상 계약에서 새 표본을 기다린다. |
| 19 | 성능/regime/producer-gap/stage-hook 분기 | 기본 OFF. 명시적 flag가 있을 때만 실행하며 현행 필수 owner가 아니다. |
| 20 | `intraday_ws_freshness_monitor --finalize --monitor-only` | WS 품질을 마감하고 scanner family 입력을 정리한다. |
| 21 | Swing propagation/review | Swing가 활성일 때만 실행한다. |
| 22 | `rising_missed_classifier_prior` | 동일 attempt 비용 차감 paired 평가와 next-PREOPEN receipt를 만든다. 검증된 edge가 없으면 incumbent를 보존한다. |
| 23 | `runtime_approval_summary` | 각 family의 직접 원천·경제성·정책·consumer 상태를 요약한다. 공통 후보를 만들지 않는다. |
| 24 | `build_next_stage2_checklist` | source repair, 자연 성숙, handoff 항목을 다음 거래일 checklist에 투영한다. |
| 25 | `verify_threshold_cycle_postclose_chain --main-mechanistic-summary-only` / `--compact-summary-only` | family scoped 검증이다. main의 summary/checklist 미검증, compact의 적용일 다중 파일 선택 결함을 확인했다. 아래 통합 계획에서 보완한다. |
| 26 | `verify_threshold_cycle_postclose_chain --allow-pending-done-marker` | DONE 전 direct-family chain을 검증한다. |
| 27 | `sync_docs_backlog_to_project --print-backlog-only` | 문서 parser만 검증한다. 외부 Project/Calendar sync는 실행하지 않는다. |
| 28 | status/DONE marker | wrapper의 기계적 terminal을 기록한다. 경제성·자연 소비 승인과 분리한다. |
| 29 | `verify_threshold_cycle_postclose_chain` final | DONE 뒤 strict를 실행하지만 terminal 날짜·exit code·실행 세대 검사와 immutable attempt 보존이 부족하다. 독립 widget/machine 최종 인계도 별도 보완 대상이다. |

### 2.1 별도 timer 내부 활성 작업

main의 29개 행은 OFF 분기·검증·marker를 포함하며 전체 경제 튜너 수가 아니다. 다음 독립 호출도 전체 재생성/최종 소비 검증 대상이다. 선택 release의 내부 호출과 설치 unit의 실제 import root는 별도로 대사한다.

| owner | 내부 호출 순서 | 점검 경계 |
| --- | --- | --- |
| widget evaluation | `monitoring.widget_advisory_calibration` → `widget_auto_trade_policy_calibration` → EOD gate → `widget_symbol_signal_policy_research` → `widget_symbol_runtime_policy` | 4개 producer와 EOD gate. 현 wrapper의 과거 target 지정 및 EOD as-of 계약 보완이 필요하다. |
| machine final refresh | `monitoring.research_native_capacity_source` → `widget_collector_expansion_recommendation` → `machine_microstructure_attribution` → `automation.market_weakness_hysteresis_tuning` → `machine_entry_timing_tuning` → `machine_research_closed_loop_refresh` → `machine_microstructure_policy_approval` → `build_next_stage2_checklist` | 8개 호출. 과거 복구에서 현재 계좌/cost를 당시 값으로 채우지 않고 단계별 rc·정책·최종 consumer를 확인한다. |

## 3. 최근 직접 결과 — source date 2026-09-17

`runtime_approval_summary_2026-09-17.json`은 직접 원천 `11/11`을 찾았고 `direct_evidence_complete`로 끝났지만, 경제성 결과는 `mixed`, validated edge `0`, 신규 policy candidate `0`이다. 다음 적용일은 2026-09-21이며 PREOPEN은 아직 `pending`, 실제 PID 소비는 `false`다.

| family | 현재 결과 | EV·정책 해석 | 다음 상태 |
| --- | --- | --- | --- |
| `entry_cancel_wait` | 과거 `source_gap`; `execution_compact_coverage_unproven` | 9/17 manifest에 신규 execution census가 없어 ΔEV·실제 이익은 null. 미래 producer/평가 구현은 존재한다 | 현재 release의 미래 생성 회귀·summary 분류 재확인 |
| `entry_split` | 과거 `source_gap`; `operating_paired_source_missing` | ES0–ES6 구현·회귀는 존재한다. 9/17 자료의 운영 비교 결손만으로 미래 구현 부재를 단정할 수 없다 | 기존 지원 입력 producer→평가→소비 검증·자연 표본 분리 |
| `scale_in_split` | `insufficient_sample`; applicable paired fill `0` | 확인된 fill 5건이 있어도 현 평가 scope에 적용 가능한 표본이 0이라 EV는 null, incumbent 보존 | 자연 표본 대기와 closure-test 명시 보완 |
| `low_price_two_leg` | `mixed`; `actual_sample_floor` | no-trade/no-fill과 held/custody/source-gap이 섞여 비용 차감 우위를 확정하지 못함, handoff blocked | 구조 수리와 자연 표본을 분리해야 함 |
| `main_mechanistic_entry` | summary상 `insufficient_sample`; full population `1715` | 1715는 운영 유효 paired 수가 아니다. 진단 ΔEV `+0.0054462573%p`는 실제 순익이 아니며 changed 8건의 운영 평가 미지원·candidate `0` | 메인 계획 §14 ME8–ME13 계약 보완 후 자연 검증 |
| `compact_auxiliary` | 과거 source gap; paired sample `0` | 과거 21건은 복구 불가로 제외했다. 미래 exact-plan producer 계약은 구현됐으며 신규 candidate `0`, incumbent 보존 | 첫 미래 자연 표본·독립 holdout 대기 |
| `rising_missed` | `measured_no_edge`; 17일·302 paired, 후보 6 | 비용 차감 edge가 확인되지 않아 incumbent 보존 | terminal incumbent; 새 결함 없으면 재점검 대상 아님 |
| `machine_entry`, `source_quality`, `ws_freshness` | `not_applicable` 또는 진단 | 직접 EV 승격 family가 아니다 | 원천/진단 owner로 유지 |

## 4. 남은 점검 대상

### 4.1 구현·계약 보완과 기존 구현 재확인

상세 근거·수리 owner·회귀·재생성 순서는 [장후 통합 검증·복구·다음 PREOPEN 준비 계획](../proposals/postclose-integrated-verification-recovery-and-next-preopen-readiness-plan-2026-09-20.md)을 따른다. 9/17 실패와 9/18 봇 중지/관측 미적재를 구분하며, 9/18을 정상 무거래나 휴장으로 간주하지 않는다.

| 우선순위 | 대상 | 재확인한 문제 | 완료 판정 |
| --- | --- | --- | --- |
| 1 | 목록 25–29번 | scoped 적용일/summary 검사, preterminal PASS 의미, terminal 날짜·exit·run identity, DONE 선발행, 덮어쓰는 immutable attempt | 다른 날짜·exit17의 성공 marker를 거부하고 현재 실행의 필수 증거에만 최종 DONE 발행 |
| 2 | late-source·복구 날짜·기동 release | finalizer 미설치/폐기 의존, widget 혼합 root, 과거 target 제한, 현재 계좌를 과거 원천으로 쓸 위험 | 현재 활성 owner만 최종 인계. 서비스 내부 source 정렬·서비스 간 호환 검증. 명시 source9/17→publication→effective9/21 준비 |
| 3 | main mechanistic 및 summary | future 계약을 보고서 flag로 verified 추정, full population을 paired로 표기. 메인 §14 보완은 별도 세션 owner | ME8–ME13 실제 지원 입력·경제성·미래 생성 회귀 인계 후 분류 갱신. 자연 대기만으로 종결하지 않음 |
| 4 | cancel-wait / entry split | 과거 census/운영 원천 결손은 확인되지만 기존 미래 emitter·ES/CW 회귀가 있어 미구현 단정은 정정 | 기존 producer→projection/census→평가→정책 소비 회귀를 확인하고 과거 결손·자연 표본·신규 결함 분리 |
| 5 | low-price actual/expansion | sample floor·durable source·custody 혼재, expansion receipt의 `target_date_matches=false` | 날짜 selector와 원천 결손을 별도 수리. profile별 분모·no-fill·held·유효 비용 비교 보존 |
| 6 | direct-family closure metadata / scale-in | 일부 closure test missing, terminal clock 결손과 비교 부적격 혼재 | 검증된 future 계약의 owner/version/closure를 전달. 실제 미래 writer 미입증 상태는 repair로 유지 |

### 4.2 위 계약이 검증된 후의 자연 acceptance와 별도 intake

- `DirectFamilyPreopenPolicyHandoff`: 9/21 07:35 PREOPEN부터 07:55/07:57/07:58 기동까지 날짜·hash·scope·accepted/rejected와 실제 PID 소비를 확인한다. 기존 08:45 시간창은 늦으므로 기존 ID를 유지해 바로잡는다.
- `main_mechanistic_entry`: ME8–ME13 인계 완료 후 미래 exact changed-decision replay·독립 holdout·완료 비용 손익을 확인한다.
- `compact_auxiliary`: 검증된 미래 exact pre-AI plan·stop·cost·owner·route 원천의 첫 자연 표본과 독립 holdout을 확인한다.
- `scale_in_split`: terminal clock 생성 계약을 확인한 뒤 수량 2 이상이며 실제 분할 비교 가능한 ADD fill을 기다린다.
- 정책별 자연 적용: 결정 변경·주문·체결·terminal·적용 버전별 중복 제거 손익은 배포·파일 생성과 분리한다.
- `LowPriceExpandedResearchRepair0918`: 날짜 receipt/producer 결손은 먼저 수리하고 PREOPEN 실소비·자연 경제성을 확인한다.
- `KiwoomCommonHealthOpportunityCostAcceptance0917`: 공통 health·실행 모델·compact 정책의 자연 소비와 실제 성과 owner를 보존한다.
- `CodeImprovementWorkorderReview0918`: 자연 표본 대기가 아니라 사용자 구현 지시가 필요한 native recommendation을 판별하는 수동 intake다.

시간은 유효 표본·독립 holdout·완료 손익의 축적을 도울 수 있다. 날짜·원천/identity·완료 판정·schedule·closure 결함은 구현/설치 계약을 고쳐야 한다. 후보0·null을 임의로 no-edge·0으로 바꾸지 않는다.

## 5. PREOPEN 및 장중 소비 순서

1. family publisher가 dated policy 또는 incumbent receipt를 만든다.
2. `automation.runtime_policy_bootstrap`이 검증된 incumbent, operator override/lock, explicit retirement OFF를 합성한다.
3. bootstrap은 EV를 계산하거나 후보를 만들지 않는다. 날짜·원천 hash·self hash·scope가 틀리면 fail closed한다.
4. entry setup과 holding policy consumer는 family별 artifact를 직접 검증한다.
5. `src/run_bot.sh`가 exact-date bootstrap env를 소비한다. 기존 실행 PID에 hot reload하지 않는다.
6. 자연 PID 소비, 주문, 체결, terminal, 비용 반영 EV는 release 선택과 별도 acceptance다.

## 6. 현행 필수 작업이 아닌 코드

| 코드 owner | 현행 분류 |
| --- | --- |
| `runtime_apply_gap_audit`, `key_lineage_ledger`, `conversion_lane` | 비활성 진단. 직접 family 검증의 완료 조건이 아니다. |
| `build_code_improvement_workorder` | main wrapper에서 OFF. 사용자 구현 지시가 있을 때만 쓰는 수동 작업본이며 자동 runtime 변경 owner가 아니다. |
| `run_ai_entry_setup_paired_replay_postclose.sh` | 수동 호환 wrapper. 설치 schedule의 owner가 아니다. |
| Swing discovery/lifecycle/pattern modules | 기본 OFF. 명시적 Swing scope에서만 실행한다. |
| performance/regime/producer-gap/stage-hook modules | 기본 OFF. 코드 존재를 설치 또는 당일 결손으로 해석하지 않는다. |

## 7. 공통 결과 점검 순서

각 활성 owner를 `terminal → 원천 날짜·해시·표본/제외 분모 → 비용 반영 paired EV·일별 순익·tail·노출 → 독립 holdout → policy receipt → 직접 runtime consumer → 자연 PID·결정·주문·terminal` 순서로 확인한다. `PASS`, `DONE`, 파일 존재, release receipt는 경제성 승인과 분리한다. source gap, no-trade, no-fill, partial, held, custody-censored를 서로 대체하지 않는다. ETA를 입증할 수 없으면 `null`로 둔다.
