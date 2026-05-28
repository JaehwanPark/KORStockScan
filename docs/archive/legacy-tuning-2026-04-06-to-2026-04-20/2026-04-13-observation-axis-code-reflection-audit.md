# 2026-04-13 관찰 축 vs 코드 반영 감사표

## 목적

- 지금까지 관찰한 주요 축별로 `개별 분석 결과`, `현재 결론`, `실제 코드 반영 여부`, `실전 매매로직 반영 여부`를 한 표로 묶는다.
- "`시간을 많이 썼는데 실제 개선은 무엇이 반영됐는가`"를 문서 하나에서 바로 점검 가능하게 만든다.

## 한줄 결론

- **실전 매매로직까지 실제 반영된 축은 사실상 `RELAX-LATENCY` 원격 canary 1축뿐이다.**
- 나머지 다수는 `계측/리포트 보강`, `shadow-only`, `운영 wrapper`, `문서화`, `분석 결론` 단계에 머물러 있다.
- 따라서 "`관찰을 많이 했는데 개선이 결국 RELAX-LATENCY뿐인가?`"라는 문제의식은 **대체로 맞다**.  
  더 정확히 말하면, 지금까지의 많은 작업은 `실전 로직 변경`보다 `관찰 가능성/원인 귀속 정확도`를 올리는 데 쓰였다.

## 판독 기준

- `코드반영`: 코드/스크립트/리포트 경로가 실제 저장소에 존재하는지
- `실전반영`: 라이브 매매 판단 경로가 실제로 바뀌었는지
- `실전반영 확신도`: **지금 시점의 결론(완화/유지/보류/반영 금지 포함)을 실전 운영 판단에 써도 되는 확신도**다.
  - 높은 값이 항상 `즉시 완화/반영`을 뜻하지는 않는다.
  - `유지/보류` 결론에 대한 확신이 높은 경우도 높은 값이 가능하다.
  - `50% 미만`은 원칙적으로 `표본 부족`, `원격 비교 실패`, `거의 even`, `shadow-only`일 때만 허용한다.
- 상태 값:
  - `예`: 코드 또는 실전 로직 반영 완료
  - `부분`: 일부 경로나 원격 canary/shadow만 반영
  - `아니오`: 아직 문서/분석만 있고 코드 반영 없음

## 감사표

| 관찰 축 | 개별 분석 결과 | 현재 결론 | 코드반영 | 실전반영 | 실전반영 확신도 | 주요 근거 |
| --- | --- | --- | --- | --- | ---: | --- |
| `RELAX-LATENCY` | `budget_pass 이후 latency_block`이 주병목이고, `quote_stale=False` 코호트도 충분히 존재한다. `submitted/holding_started` 개선 증거는 아직 약하다. | `강화 유지`, 단 `2026-04-14 장후`에 반영/보류 결론 필요 | `예` | `부분` | `74%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md`, `docs/plan-korStockScanPerformanceOptimization.prompt.md` / 코드: `src/engine/sniper_entry_latency.py`, `src/engine/sniper_state_handlers.py`, `src/engine/sniper_entry_pipeline_report.py`, `src/engine/sniper_performance_tuning_report.py`, `src/utils/constants.py` |
| `RELAX-DYNSTR` | `blocked_strength_momentum`이 2순위 blocker이고, 세부 사유는 `below_window_buy_value / below_buy_ratio / below_strength_base`로 분해 가능하다. | `유지 + 재설계`, 전역 완화 금지 | `부분` | `아니오` | `61%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md`, `docs/plan-korStockScanPerformanceOptimization.prompt.md` / 코드: 관련 집계는 `src/engine/sniper_state_handlers.py`, `src/engine/sniper_strength_observation_report.py`, `src/engine/sniper_entry_pipeline_report.py`에 존재하지만 selective override 로직은 미착수 |
| `RELAX-OVERBOUGHT` | `blocked_overbought=20` 수준으로 누적되고, `WAIT 65` missed-winner의 주원인은 `overbought`보다 `latency/strength` 쪽이다. | `유지`, 실전 완화 재오픈 금지 | `부분` | `아니오` | `57%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md`, `docs/plan-korStockScanPerformanceOptimization.prompt.md` / 코드: overbought 관련 계측은 `src/engine/sniper_state_handlers.py`, `src/engine/sniper_performance_tuning_report.py`에 존재하나 완화 로직 변경은 없음 |
| `WAIT 65 통합 운영판단` | `WAIT 65`는 AI threshold miss 단독 문제가 아니고, 주원인은 `latency_block`, 2순위는 `blocked_strength_momentum`이다. | `WAIT 65` 전면 완화 금지, 관련 축을 통한 우회 개선만 허용 | `부분` | `아니오` | `68%` | 문서: `docs/plan-korStockScanPerformanceOptimization.prompt.md`, `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md`, `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 직접적인 `WAIT 65` threshold 변경 코드는 없음 |
| `체결 품질 / partial fill sync` | `full fill / partial fill / preset_exit_sync_mismatch`를 분리해 볼 수 있게 됐지만, 오늘 표본은 작아 성과 일반화는 아직 어렵다. | 관찰 가능 상태, 실전 해석은 추가 표본 필요 | `예` | `아니오` | `46%` | 문서: `docs/2026-04-10-phase0-phase1-implementation-review.md`, `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 코드: `src/engine/sniper_execution_receipts.py`, `src/engine/sniper_trade_review_report.py`, `src/engine/sniper_performance_tuning_report.py` |
| `미결 이월 / expired_armed` | `latency_block`과 `entry_armed_expired_after_wait`를 분리해야 실제 missed opportunity 원인을 나눠 읽을 수 있다. 오늘도 `태광` 등 상위 종목이 누적됐다. | 계측/리포트는 완료, 실전 로직 변경은 아직 없음 | `예` | `아니오` | `55%` | 문서: `docs/2026-04-10-phase0-phase1-implementation-review.md`, `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 코드: `src/engine/sniper_state_handlers.py`, `src/engine/sniper_entry_pipeline_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`, `src/engine/sniper_performance_tuning_report.py` |
| `AI overlap audit` | AI가 이미 본 피처와 후단 필터가 같은 row에서 비교 가능해졌고, `blocked_stage / threshold_profile / momentum_tag` 교차 해석이 가능해졌다. | 감사축은 유효, 하지만 이걸 근거로 한 selective override는 미착수 | `예` | `아니오` | `58%` | 문서: `docs/2026-04-10-phase0-phase1-implementation-review.md`, `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 코드: `src/engine/sniper_state_handlers.py`, `src/engine/sniper_performance_tuning_report.py` |
| `live hard stop taxonomy audit` | `scalp_preset_hard_stop_pct`, `protect_hard_stop`, `scalp_hard_stop_pct`는 live, `hard_time_stop_shadow`는 shadow-only로 구분 가능하다. | 구조 설명은 가능, 성과 판정은 표본 부족 | `예` | `아니오` | `44%` | 문서: `docs/2026-04-10-phase0-phase1-implementation-review.md`, `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 코드: `src/engine/sniper_trade_review_report.py`, `src/engine/sniper_state_handlers.py` |
| `0-1b 원격 경량 프로파일링` | `quote_stale=False latency_block`의 hot path 후보를 찾기 위한 운영 도구가 필요했고, 장전/장중 baseline 및 thread/top snapshot으로 후보 1~3개를 추렸다. | 운영 도구는 있음, 실전 로직과 직접 연결은 아직 없음 | `예` | `아니오` | `59%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md`, `docs/plan-korStockScanPerformanceOptimization.prompt.md` / 코드: `src/engine/collect_remote_latency_baseline.py`, `deploy/run_remote_latency_baseline.sh` |
| `fetch_remote_scalping_logs / snapshot 재현성` | `file changed as we read it` 실패 이력 때문에 `live snapshot copy -> tar` 안정화가 핵심 운영축이 됐다. 현재 smoke 기준 경로는 재현 가능하다. | 기존 fallback 유지, 즉시 재작업 불필요 | `예` | `아니오` | `72%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md` / 코드: `src/engine/fetch_remote_scalping_logs.py`, `src/tests/test_fetch_remote_scalping_logs.py` |
| `원격서버 비교검증` | `Trade Review`, `Post Sell Feedback`는 비교됐지만 `Performance Tuning`, `Entry Pipeline Flow`는 `remote_error(TimeoutError)`였다. 즉 오늘 비교는 완결형이 아니었다. | API 비교만으로 닫지 말고 snapshot 기준 재점검 필요 | `예` | `아니오` | `39%` | 문서: `data/report/server_comparison/server_comparison_2026-04-13.md`, `docs/checklists/2026-04-14-stage2-todo-checklist.md` / 코드: `src/engine/server_report_comparison.py`, `src/engine/fetch_remote_scalping_logs.py` |
| `post-sell exit timing canary` | `estimated_extra_upside_10m_krw_sum`, `timing_tuning_pressure_score`, `exit_rule_tuning`, `tag_tuning`, `priority_actions`를 읽을 구조는 있으나, 오늘 표본은 너무 작다. | 후보안만 작성, 실전 적용 보류 | `예` | `아니오` | `37%` | 문서: `docs/checklists/2026-04-13-stage2-todo-checklist.md`, `docs/plan-korStockScanPerformanceOptimization.prompt.md` / 코드: `src/engine/sniper_post_sell_feedback.py`, `src/web/app.py` |
| `WATCHING 75 정합화 shadow` | 실제 분포가 `WAIT 65`와 `BUY 85/92`로 양극화돼 있어 `75~79` 경계구간 표본이 거의 없었다. shadow는 존재하지만 표본이 부족하다. | shadow-only 유지, 본서버 즉시 반영 금지 | `예` | `부분` | `34%` | 문서: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md` / 코드: `src/engine/watching_prompt_75_shadow_report.py`, `src/engine/check_watching_prompt_75_shadow_canary.py`, `src/engine/sniper_state_handlers.py` |
| `SCALP_PRESET_TP SELL 의도 확인` | 현재 프롬프트는 `BUY | WAIT | DROP`만 허용하고, `SELL`은 placeholder 성격이 강하다. | `SELL` 제거도, 실집행 승격도 하지 않음. placeholder 유지 | `부분` | `아니오` | `63%` | 문서: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md` / 코드: `src/engine/sniper_state_handlers.py`의 `ai_action_used_for_exit` 로그는 존재하나 로직 변경은 없음 |
| `HOLDING hybrid override` | `FORCE_EXIT`만 즉시집행 후보, `SELL`은 로그 우선, `DROP`은 `SCALP_PRESET_TP` 전용이라는 기준표는 정리됐다. | override rule v1 문서화만 완료, 구현은 미착수 | `아니오` | `아니오` | `41%` | 문서: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md` / 실제 `holding_override_rule_version` 연결 및 hybrid 적용은 후속 작업 |

## 요약 집계

| 구분 | 개수 | 설명 |
| --- | ---: | --- |
| 전체 주요 관찰/감사 축 | `14` | 본 문서 표 기준 |
| 실전 매매로직이 실제 바뀐 축 | `1` | `RELAX-LATENCY` 원격 `remote_v2` canary |
| 계측/리포트/운영도구는 반영됐지만 실전 로직은 안 바뀐 축 | `8` | `partial fill`, `expired_armed`, `AI overlap`, `hard stop taxonomy`, `0-1b`, `fetch_remote`, `server comparison`, `post-sell` |
| shadow-only / 원격 실험 경로만 있는 축 | `2` | `WATCHING 75`, `RELAX-LATENCY` 일부 reason allowlist 경로 |
| 문서화/분석 결론만 있고 코드/실전 변경이 없는 축 | `3` | `RELAX-DYNSTR`, `RELAX-OVERBOUGHT`, `HOLDING hybrid override` |
| `실전반영 확신도 >= 50%` 축 | `8` | `RELAX-LATENCY`, `RELAX-DYNSTR`, `RELAX-OVERBOUGHT`, `WAIT 65`, `expired_armed`, `AI overlap`, `fetch_remote`, `SCALP_PRESET_TP SELL` |
| `실전반영 확신도 < 50%` 축 | `6` | 표본 부족, `remote_error`, shadow-only, holding 표본 부족 등으로 즉시 판단이 어려운 축 |

## 감사 메모

1. 지금까지의 투자 시간은 `실전 개선 그 자체`보다 `실전 개선을 할 수 있을 만큼 원인 귀속을 분해하는 작업`에 더 많이 쓰였다.
2. 그 결과 저장소에는 `실전 매매로직 개선`보다 `계측/리포트/운영 wrapper`가 더 많이 쌓였다.
3. 따라서 "`개선한다고 해놓고 지금 실전 반영이 RELAX-LATENCY뿐인가?`"라는 문제의식은 과장이 아니다.
4. 정확히는 `RELAX-LATENCY 1축 원격 canary`만 실전 로직 수준으로 움직였고, 나머지는 아직 `왜 바꿔야 하는지`를 증명하는 단계에 가깝다.
5. 이 문서 기준으로 `2026-04-14 장후`에는 최소한 아래 둘 중 하나가 나와야 한다.
   - `RELAX-LATENCY` 실전 반영/확대 결론
   - `RELAX-DYNSTR` 1축 canary 착수 결론
6. `50% 미만`으로 둔 축은 모두 `표본 부족`, `remote_error`, `shadow-only`, `holding_events=0` 같은 명시적 제약이 있는 경우로만 제한했다.

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-13-stage2-todo-checklist.md](./checklists/2026-04-13-stage2-todo-checklist.md)
- [2026-04-10-phase0-phase1-implementation-review.md](./2026-04-10-phase0-phase1-implementation-review.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
