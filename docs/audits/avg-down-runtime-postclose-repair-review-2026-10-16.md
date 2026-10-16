# AVG_DOWN 런타임·장후 연구 보완 검토 — 2026-10-16

## 범위와 기준

- 사용자 지시: 배포본 `922b9cbc3`, PID `3729660` 기준 보완 → 코드리뷰 → 수정보완 → 커밋. 배포는 별도 세션에서 수행한다.
- 기준 커밋: `922b9cbc370c4c6c002b3c1fcdb3ed061719e4a2`.
- 독립 worktree: `/home/ubuntu/KORStockScan-worktrees/avg-down-lifecycle-20261016`; branch: `fix/avg-down-lifecycle-20261016`. 원 workspace의 미커밋·동시 작업은 포함하지 않았다.
- 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [당일 checklist](../checklists/2026-10-16-stage2-todo-checklist.md), [원 구현계획](../proposals/avg-down-shared-rebound-receipt-and-pyramid-retirement-implementation-plan-2026-09-28.md).
- 14:11–14:15 KST에 확인하고 14:44–14:46에 재확인한 선택본·프로세스: `/proc/3729660/cwd`는 `KORStockScan-runtime-releases/probe-partial-integrated-20261016-922b9cbc3/src`, 시작 ticks는 `19142841`.
- `data/runtime/runtime_release_selection.json`의 선택 SHA가 기준 커밋과 일치한다. `data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-16.json`은 PID `3729660`, `passed=true`, `pid_passed=true`, 검증 시각 `14:11:31+09:00`이다.
- `data/runtime/mechanistic_entry_policy/consumed/2026-10-16/3729660.json`은 `continuous_reversal_pid_consumption_v6`, 같은 release commit, family SHA `75af4c634cc9bd3695e2e2d810371a3ff9978b5de8945c853757838631df54ce`이다. 이 영수증은 수정 전 배포본의 소비 증거다.

## 결함과 수정

| 결함 | 보완 | 확인한 경계 |
| --- | --- | --- |
| 실제 Main은 continuous reversal v6를 소비하지만 물타기 평가는 이전 mechanistic 경로만 사용 | 선택된 family의 기존 native snapshot을 읽고 동일한 순수 dispatcher로 평가 | Main ready/claim·정책 상태 기록을 소비하거나 변경하지 않음. 원 정의가 반등인 matched branch만 ADD 신호가 됨 |
| Main 고정관심 보유의 `SCALP_BASE`와 entry 정책 scope가 불일치 | 원 admission의 코드·날짜·세션·route·generation을 검증한 뒤 정책 조회에만 `SCANNER` 사용 | 실제 보유 tag·custody는 유지. 이전 날짜/세션의 유효 admission도 보유 동안 유지. 다른 owner는 채택하지 않음 |
| 정규장 통합시장의 정책 venue가 canonical `KRX`와 불일치 | 기존 venue resolver의 정규화 사용 | native 원천은 정확한 item의 SOR/KRX/NXT partition을 계속 사용 |
| native 신호가 만료되어도 새 holding permit의 유효기간이 남을 수 있음 | native 5초 expiry를 permit 검사와 최종 submit 직전 모두 검사 | 기존 permit 2초, source·position digest, 가격·수량·계좌·cooldown·공통 stop 및 hard safety 유지 |
| ADD 완료/취소/다음 주문 초기화가 체결 map을 지워 최초 BUY identity로 돌아감 | 보유 기간 전체의 exact BUY legs를 누적하고 receipt v2로 저장·복원 | `(order_no, execution_no, qty)` 불일치 거부. v1도 검증 후 읽음. 실제 SELL 완료/재진입에는 원 보유 legs 정리 |
| 현재 ADD reason이 체결 후 반등평가 전환 대상에서 누락 | `shared_main_rebound_entry` 체결을 기존 `POST_ADD_EVAL`로 연결 | 신규 주문 제출만으로 전환하지 않고 실제 accepted fill에서 전환 |
| 장후 lineage에서 누락 BUY identity끼리 같다고 판단 가능 | BUY·bundle·vote policy hash와 최소 유효 투표 수를 검증 | 결손은 `lineage_gap_buy_fill_identity` / `lineage_gap_policy_identity` / `lineage_gap_valid_vote`로 유지 |
| partitioned 장후 보고서가 보유 신호·투표 원본을 버리고 항상 빈 목록 재생 | per-position 신호·exact BUY·원 요청 참조를 봉인해 동일 strict 완료/비용 cohort에서 재생 | 원 요청 bytes를 봉인 시점과 소비 시점에 검증. 미검증/변조 입력 제외. 대용량 결손은 명시적 row exclusion |
| ADD 투표를 exit 장후 owner의 독립 수치 후보로 제시 | `ADD_REBOUND` 후보 grid 제거, incumbent 진단 재생만 유지 | 실제 ADD 시점은 선택된 Main machine이 소유. exit 숫자 연구의 기존 범위 유지 |

새 runtime adapter는 역할 패키지 `src/engine/scalping/avg_down_rebound.py`, 회귀는 `src/tests/test_avg_down_rebound.py`에 배치했다. engine root에 새 모듈을 만들지 않았다. 장후 assembly의 code contract에도 새 adapter와 replay consumer를 포함했다.

## 리뷰와 재검증

1. producer → holding scope → Main family → source preflight → ADD vote → permit → 주문/체결 → receipt 복원 → 장후 완료/비용 소비 순서로 검토했다.
2. 최초 회귀에서 발견한 aftermarket admission bucket 대소문자와 stream closure의 `nonlocal` 누락을 수정했다. 기존 partitioned source-gap 기대값도 실제 봉인 입력 계약에 맞춰 검증했다.
3. 재리뷰에서 원 요청 검증의 시점을 보완했다. 봉인 후 원 payload 파일이 바뀌면 해당 VALID 투표는 소비 시점에 제외된다. 실제 원 요청 capture/ledger/assembly를 사용하는 fixture로 정상·미검증·봉인 후 변조를 검증했다.
4. 실제 receipt handler의 ADD 체결 → pending cleanup → identity 유지 → 재기동 복원, 취소 후 다음 ADD·복수 재기동, v1 bytes 보존을 검증했다. 실제 v6 family/native buffer fixture에서 ADD 판독 후에도 같은 Main claim이 가능함을 확인했다.

최종 대상 검증: **1,522 passed, 40.97초**.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/pytest -q -p no:cacheprovider \
  src/tests/test_avg_down_rebound.py \
  src/tests/test_holding_exit_vote.py \
  src/tests/test_holding_path_vote_replay.py \
  src/tests/test_trade_review_report_revival.py \
  src/tests/test_sniper_scale_in.py \
  src/tests/test_ai_engine_openai_transport.py \
  src/tests/test_reversal_extended_policy.py \
  src/tests/test_research_json_stream.py \
  src/tests/test_main_trailing_source_assembler.py \
  src/tests/test_holding_exit_observation_report.py \
  src/tests/test_holding_vote_numeric_successor.py \
  src/tests/test_scale_in_split_order_plan.py \
  src/tests/test_engine_location_gate.py
```

추가 gate도 통과했다: 변경 Python 21개 compile, `git diff --check`, 문서 상대 링크 4개, print-only backlog parser(`--print-backlog-only --limit 500`, exit 0). 실제 provider·broker 호출, 광범위 장후 보고서 재생성, external sync는 이 코드 검증에 포함하지 않았다.

## Kiwoom 공식 참조

복원·체결 경로 수정 전 2026-10-16 `14:21:33+09:00`에 공식 저장소 HEAD를 확인했다: [Kiwoom REST API commit 953e5db](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f).

- 확인 경로: `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `00`·`kt10000`, `kiwoom/realtime/schemas.py`, `decoders.py`, `events.py`, `kiwoom/core/client.py`, Postman PRD/MOCK의 `kt10000`.
- 해당 revision에는 `kiwoom_docs` 디렉터리가 없다. 주문/체결 식별자 `9203/909`, 수량 `900/902/911/915`, 누적대금 `903`, 가격 `901/910/914`, route `2134–2136`을 대조했다.
- 이번 수정은 기존 accepted execution의 내부 보유 identity를 보존한다. REST 요청·WebSocket parser/FID·인증·REG/REMOVE·연속조회 wire 계약은 수정하지 않았다. 기존 SDK/Postman 차이로 새 해석을 만들지 않았다.

## 배포 인계와 남은 수용 범위

- **코드 수정·대상 검증 완료이며 배포·재기동은 미실행이다.** 다른 세션은 이 branch의 커밋을 실제 선택본과 대조한 뒤 기존 배포 절차로 인계한다. 별도 작업의 미커밋 파일을 덮어쓰지 않는다.
- 기준 PID의 `KORSTOCKSCAN_HOLDING_DECISION_CONTEXT_ENABLED`, KRX/NXT/PREMARKET별 활성값은 모두 `false`다. 이 활성 계약은 변경하지 않았다. 따라서 이 커밋만으로 자연 ADD 유효 투표·주문이 발생한다고 판정할 수 없다. forensic context를 live 입력으로 승격하지 않는다.
- 당일 정책·bootstrap·새 PID 소비는 [당일 checklist](../checklists/2026-10-16-stage2-todo-checklist.md)의 `DirectFamilyPreopenPolicyHandoff` 등 기존 소비 확인 owner가 맡는다. 배포 후에는 새 source hash로 정상 장후 assembly/report 및 strict handoff가 생성·소비되는지 별도 확인한다. 이전 산출물을 새 코드의 결과로 간주하지 않는다.
- receipt v2는 새 reader가 v1과 함께 읽는다. v1 전용 옛 코드로 rollback하면 새 v2 receipt의 복원이 거부된다. rollback 시에는 이 reader 호환성을 포함해야 하며 원 receipt 삭제·과거 체결 재생성으로 맞추지 않는다.
- 자연 실행 수용은 동일 보유의 반등 신호 → 유효 ADD 투표 → 실제 submit/accepted/fill → 청산/실비용으로 확인한다. 현재 paired ADD/NO_ADD 경제성은 관측되지 않았으며 `null`을 유지한다. 완료 보유의 PnL만으로 물타기의 추가 효과를 주장하지 않는다.
- S15·VCP·PYRAMID 신규 판단/튜닝은 복원하지 않았다. 과거 미결 주문의 복구·정산 소비는 유지했다. 주문·provider·threshold·env·정책 selector·프로세스에 대한 실제 변경은 이 작업에 없다.
