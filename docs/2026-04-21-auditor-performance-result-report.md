# 2026-04-21 Auditor Performance Result Report

## 판정

- 종합 등급: 조건부 보류. `main-only buy_recovery_canary`는 이미 코드/runtime 반영됐으나, 최종 스냅샷(`2026-04-21 15:37 KST` 수동 갱신) 기준으로도 N gate가 부족하므로 승격 판정은 금지한다.
- canary 착수축 1개: `main-only buy_recovery_canary` 유지 관찰.
- 보류축: `entry_filter_quality` 정식 canary, AI 엔진 A/B 재개, 프로파일별 특화 프롬프트 확대.
- 기준 원칙: 손익은 `COMPLETED + valid profit_rate`만 사용하고, full fill과 partial fill은 분리한다.

## 지표표

| 지표 | 기준선/목표 | 2026-04-21 값 | 판정 |
| --- | --- | ---: | --- |
| completed_trades | 관측 | 8 | 표본 부족, 방향성만 |
| realized_pnl_krw | 관측 | -17,191 | 손실, 기대값 개선 필요 |
| full_fill_completed_avg_profit_rate | 분리 관측 | +0.587% | full fill은 양호 |
| partial_fill_completed_avg_profit_rate | >= -0.15% | -1.038% | 미달, partial 악화 |
| partial_fill_events | N gate 20 | 7 | hard pass/fail 금지 |
| position_rebased_after_fill_events/partial_fill_events | <= 1.15 | 13/7 = 1.86 | 미달 |
| gatekeeper_fast_reuse_ratio | >= 10.0% | 0.0% | 미달 |
| gatekeeper_eval_ms_p95 | <= 15,900ms | 17,594ms | 미달 |
| latency_block_events/budget_pass_events | 감소 필요 | 4,848/4,858 = 99.8% | 심각한 병목 |
| ai_confirmed_buy_count/share | buy drought 완화 | 115/744 = 15.5% | drought 지속 |
| ai_confirmed WAIT 65~79 | 회복 후보 | 231건 | buy_recovery_canary 타당 |
| wait65_79_ev_candidate | 수집 확인 | 54건 | 수집 정상 |
| blocked_ai_score | 감소 필요 | 612건 | 병목 지속 |
| missed_winner_rate | 감소 필요 | 74.8% | 기회비용 큼 |
| system metric coverage | >=360, max gap<=180s | 391건, max 61s | 통과 |

## 분석

- partial/rebase: `partial_fill_events=7`로 N gate 미달이지만 `position_rebased_after_fill_events/partial_fill_events=1.86`이고 partial 평균 손익이 `-1.038%`라 손실 증폭 방향은 명확하다. full fill 평균 `+0.587%`와 합치면 왜곡되므로 분리 유지한다.
- latency: `latency_block_events=4,848`, `budget_pass_events=4,858`로 BUY 이후 미진입의 주 병목은 latency guard다. `missed_entry_counterfactual` 기준 terminal 후보 115건 중 latency block 97건이며, explicit price 기준 missed winner rate도 `77.3%`다.
- AI 결과 경로: `ai_confirmed=744`, BUY 115건(15.5%), WAIT 474건(63.7%), DROP 155건(20.8%). WAIT 65~79는 raw `ai_confirmed` 231건이고 계량 이벤트 `wait65_79_ev_candidate` 54건이 잡혔다. `buy_after_recheck_candidate` 이벤트는 0건이라 재평가 후보가 실전 제출로 이어진 증거는 아직 없다. `wait6579_ev_cohort` 기준 expected fill rate는 `92.7037%`, 평균 기대 EV는 `+0.9808%`다.
- HOLDING: `post_sell_feedback` 기준 `missed_upside_rate=33.3%`, `good_exit_rate=55.6%`, `capture_efficiency_avg_pct=42.717`, `estimated_extra_upside_10m_krw_sum=53,001`이다. D+1 관측버퍼는 유지하되 즉시 승격/롤백 판정은 금지한다.
- 운영 관측 완전성: `logs/system_metric_samples.jsonl` 장중 샘플은 391건, 최대 간격 61초, CPU/load/memory/io/top 필드 누락 0건으로 통과한다. `2026-04-21 15:37 KST` 수동 갱신 기준 monitor snapshot 4종과 `wait6579_ev_cohort`가 갱신됐다.
- Plan Rebase: `entry_filter_quality`는 감사인 문맥의 정식 품질개선축, `buy_recovery_canary`는 Gemini WAIT 65~79 BUY drought 회복축으로 분리 잠금한다.

## 감사인 응답 반영

- Q1 `entry_filter_quality`와 `buy_recovery_canary` 분리: 적절함. `entry_filter_quality`는 진입 품질 저하 원인 분석(partial/rebase 손실, parse_bad, latency gate 설계)이 목적이고, `buy_recovery_canary`는 BUY drought 완화를 위한 행동 변경 canary다. 동일 축으로 묶으면 실적 변동 원인을 어느 쪽에 귀속할지 판정할 수 없으므로 분리 유지한다.
- Q2 `WAIT65~79` 기대 EV 양수 + 실전 제출 0건: threshold 하향보다 `recheck -> submitted` 연결성 검증을 먼저 둔다. preflight 기준 `budget_pass_candidates=40`, `latency_block_candidates=40`으로 budget 통과 후보 전원이 latency guard에서 막혔다. threshold를 낮춰도 candidate pool만 늘고 `submitted_candidates=0` 병목은 해소되지 않는다.
- Q2 후속: 04-22 `[AIPrompt0422]` 전 `latency_state_danger=33`, `latency_fallback_disabled=7` 경로를 분리해 본다.
- Q3 partial fill 표본 기준: `partial_fill_events=7 < N_min=20`이므로 hard fail이 아니라 방향성 미달로 처리하는 기준이 적절하다. `rebase/partial=1.86`, `partial_avg=-1.038%`는 나쁜 방향의 신호지만 소표본에서는 단일 이상 케이스 영향이 클 수 있다.
- Q3 후속: 방향성 미달이 2~3일 연속 동일 패턴으로 나타나면 `N_min` 충족 전이라도 행동 canary 개시 검토 근거로 올린다.
- Q4 다음 canary 우선순위: 04-22 `[AIPrompt0422]` 1차 판정 후 단일 축 전환 방식으로 latency budget pass 경로 canary를 검토한다. `latency_block/budget_pass=99.8%`는 entry threshold 완화보다 제출 경로 병목이 우선임을 의미한다.
- Q4 장전 우선 확인: `latency_fallback_disabled=7`이 구조적 버그인지 먼저 확인한다. 현재 `buy_recovery_canary`가 가동 중이므로 04-22 장전에는 두 번째 행동 canary를 동시에 열지 않는다.

## 감사 미결

- D(`ai_parse_ok=False` 분포/진입 여부): 보류 유지. `ai_confirmed` 내 parse_bad 25건, fallback50 18건이 관측됐으나 진입 손익과의 연결은 별도 코호트가 필요하다.
- E(`same_symbol_repeat_flag` 산식): 보류 유지. 오늘 Project 대상이 아니며, split-entry/rebase 축과 분리 가능한 표본 확보 후 판정한다.
- F(테스트 카운트 불일치): 조치 완료 상태 유지 확인. 오늘 문서 검증은 데이터 계량 중심이며 코드 테스트는 변경 파일 대상으로 별도 수행한다.
- 종합: 오늘 반영된 `preflight` 함수 추가와 `pipeline_events` OOM fix는 모두 observability/bugfix 범위다. 실주문 행동 변경은 없고 rollback guard는 유지된다. shadow diff는 `all_match=true`다.

## 다음 액션

- `2026-04-22` INTRADAY `12:00~12:20`: `[AIPrompt0422] Gemini BUY recovery canary 1일차 판정` 실행.
- `2026-04-22` POSTCLOSE `17:00~17:20`: `[Governance0422]` governance 문서 기준 코드 체크게이트 재확인.
- `2026-04-24` POSTCLOSE `16:00~16:20`: `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` 실행.
- rollback guard: `N_min`, 일간 합산 NAV 대비 `loss_cap <= -0.35%`, `reject_rate +15.0%p`, `gatekeeper_eval_ms_p95 > 15,900ms`, partial fill 복합 경고, fallback_regression, buy_drought_persist 유지.
- `2026-04-22` PREOPEN: `latency_fallback_disabled=7` 경로가 구조적 버그인지 확인한다. bugfix가 아니면 행동 변경은 `[AIPrompt0422]` 1차 판정 이후 단일 축 전환으로만 검토한다.

## 운영 해석 및 감사인 질의

- `OpsVerify0421` 통과 의미: 튜닝 성과가 좋아졌다는 뜻이 아니라, `09:00~15:30` 장중 운영 관측 데이터가 1분 단위로 끊기지 않았다는 뜻이다. 따라서 오늘의 `latency`, `partial/rebase`, `BUY drought` 미달은 관측 누락보다 실제 운영 병목일 가능성이 높아졌다.
- `QuantVerify0421` 개선방향: `partial_fill_events=7`로 표본은 작지만, `rebase/partial=1.86`, `partial_avg=-1.038%`, `latency_block/budget_pass=99.8%`가 동시에 나빠서 추가 canary 승격보다 `latency guard miss -> 제출 실패`, `partial fill -> rebase/soft-stop 손실`을 분리 보정하는 쪽이 우선이다.
- `AIPrompt0421` 해석: `missed_winner_rate=74.8%`로 개선폭이 작고 `buy_after_recheck_candidate=0`이라, 오늘 적용한 WAIT65~79 회복축이 실제 제출/체결까지 연결됐다는 증거는 아직 없다. 다만 `wait6579_ev_cohort.avg_expected_ev_pct=+0.9808%`라 후보군 자체는 유지 가치가 있다.
- 장전 파라미터 조정 원칙: 04-22 장전에는 threshold를 추가로 공격적으로 낮추기보다, 이미 반영된 `main-only buy_recovery_canary`를 유지하고 `WAIT65~79 -> recheck -> submitted` 계측 경로가 실제로 발생하는지 먼저 확인한다. 단, 장전 preflight에서 `buy_after_recheck_candidate=0`이 코드/로그 누락으로 확인되면 파라미터가 아니라 이벤트/재평가 경로부터 수정한다.
- 감사인 응답 결론: `entry_filter_quality`와 `buy_recovery_canary`는 분리 유지한다. 04-22 오전에는 threshold 추가 완화보다 `recheck -> submitted` 연결성 및 `latency_state_danger/latency_fallback_disabled` 분리 확인을 우선한다.

## 04-22 오전 운영 결정

- `[AIPrompt0421]`의 BUY drought 존재 여부는 이미 판정 가능하다. 다만 `buy_recovery_canary` 효과 판정은 04-22 오전까지 집계가 필요하다. 목적은 `missed_winner_rate` 재확인이 아니라 `WAIT65~79 -> recheck -> submitted -> full/partial` 연결 여부 확인이다.
- 04-22 장전에는 AI threshold를 추가 완화하지 않는다. 현재 `buy_after_recheck_candidate=0`이므로, 추가 완화 전 `recheck/submitted` 이벤트 경로와 주문 제출 전 latency blocker의 위치를 먼저 확인한다.
- `latency guard miss -> budget_pass 후 제출 실패` 개선은 내일 오전 검증을 위해 오늘 반영하는 편이 논리적으로 맞다. 단, 이미 `buy_recovery_canary`가 켜져 있으므로 두 번째 행동 canary를 동시에 열면 원인 귀속이 깨진다.
- 따라서 오늘 허용 범위는 `instrumentation/preflight/bugfix-only`다. 실주문 행동을 바꾸는 latency threshold 완화나 budget pass 조건 변경은 04-22 오전 `AIPrompt0422` 1차 판정 후, 필요 시 단일 축 전환으로 처리한다.
- 예외: 코드상 `budget_pass` 이후 제출이 구조적으로 불가능한 버그가 확인되면, 이는 canary가 아니라 bugfix로 분류해 오늘 반영 가능하다. 이 경우 문서에는 `behavior tuning 아님`, `bugfix-only`, `rollback guard 유지`를 명시한다.
- 반영 결과: [wait6579_ev_cohort_report.py](/home/ubuntu/KORStockScan/src/engine/wait6579_ev_cohort_report.py)에 `preflight` 요약과 API 조회 없는 `build_wait6579_preflight_report()`를 추가했다. 산출 필드는 `recovery_check_candidates`, `recovery_promoted_candidates`, `probe_applied_candidates`, `budget_pass_candidates`, `latency_pass_candidates`, `latency_block_candidates`, `submitted_candidates`, `order_fail_candidates`, `submission_blocker_breakdown`, `latency_block_reason_breakdown`, `behavior_change=none`이다.
- 현재 preflight: `total_candidates=54`, `recovery_check_candidates=8`, `recovery_promoted_candidates=0`, `probe_applied_candidates=0`, `budget_pass_candidates=40`, `latency_block_candidates=40`, `submitted_candidates=0`, `submission_blocker_breakdown=latency_block 40 / no_budget_pass 14`, `latency_block_reason=latency_state_danger 33 / latency_fallback_disabled 7`.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_wait6579_ev_cohort_report.py` 결과 `3 passed`. `build_wait6579_preflight_report('2026-04-21')` 실행 결과 `behavior_change=none`, `observability_passed=true`.

## Tuning Monitoring Postclose Sync

- 판정: 최초 cron 실행은 실패, 수동 보수 후 재실행은 통과.
- 실패 증적: `logs/tuning_monitoring_postclose_cron.log` 기준 `2026-04-21 18:05 KST`에 `pipeline_events 2026-04-21` 처리 중 프로세스가 `Killed`로 종료되어 `post_sell`, `system_metric_samples`, shadow diff, Gemini/Claude 분석랩이 실행되지 않았다.
- 원인: `pipeline_events_2026-04-21.jsonl`이 약 459MB이고 기존 parquet builder가 원본 이벤트 dict 전체를 메모리에 적재한 뒤 DataFrame으로 변환했다.
- 조치: `build_tuning_monitoring_parquet.py`에서 `pipeline_events`를 읽는 즉시 분석용 축소 row로 변환하도록 수정했다. 실전 매매 로직 변경은 없다.
- 복구 실행: `deploy/run_tuning_monitoring_postclose.sh 2026-04-21`를 `2026-04-21 19:23~19:26 KST` 수동 재실행.
- 산출물: `pipeline_events_20260421.parquet=421,220 rows`, `post_sell_20260421.parquet=9 rows`, `system_metric_samples_20260421.parquet=802 rows`.
- DuckDB/shadow diff: `data/analytics/shadow_diff_summary.json` 기준 `2026-04-19~2026-04-21`, `all_match=true`, `trade_count/completed_count/missed_upside/funnel blocker/submitted/full_fill/partial_fill` 전 항목 `delta=0`.
- 분석랩 manifest: Gemini/Claude 모두 `data_source_mode=duckdb_primary`, `history_coverage_ok=true`.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_tuning_monitoring_parquet.py src/tests/test_tuning_duckdb_repository.py` 결과 `18 passed`.
