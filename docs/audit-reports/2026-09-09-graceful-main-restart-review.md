# 2026-09-09 메인 우아한 재기동 실행·검증

## 판정과 범위

사용자 요청 `필요시 우아한 재기동`에 따라 main만 표준 [restart.sh](../../restart.sh)로 1회 재기동했다. 이전 PID는 정상 응답했지만 커밋 전 시작한 `source_dirty=true`/이전 commit receipt였다. 검증·푸시된 clean commit의 새 PID 소비를 확정하는 목적으로 실행했으며, 기존 process 장애 복구나 submit drought 해소로 보고하지 않는다.

main 재기동 검증은 완료했다. 독립 Samsung 오전 기계의 기존 preflight 차단은 별도 미해결이다. 전체 매매기계 정상화·자연 정책 효과·비용 차감 수익성은 이번 완료 범위가 아니다. 장중 전체 모니터링, 신규 주문/취소, 독립 위젯·에피소드 재기동, 수동 env/policy/owner registry 변경은 수행하지 않았다.

## 실행 영수증 (KST)

| 항목 | 확인 결과 |
| --- | --- |
| 이전 main | PID `12259`, 07:55:02 시작, commit `2c9731fe02227c38e430dd0d30850b9e15926718`, source dirty |
| 재기동 | 08:07:32 flag 소비 → 기존 PID 종료 → 08:07:40 새 process 시작, `restart.sh` exit 0 |
| 새 main | PID `24260`, runtime start receipt `2026-09-09T08:07:41+09:00`, commit `ad69d928067e8c77a571cf50aa061f3907c1e994`, `source_dirty=false` |
| supervisor | PID `12159` 유지. launcher의 이전 commit 표기는 이력이며 실제 로드된 `src/run_bot.sh` SHA256과 현재 파일은 `32efc0cc145b78db658357812113e51cb88a643374cd070d9a48b5a2cb481c85`로 일치 |
| exact-date runtime | [9/9 verifier](../../data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-09.json): PID24260, `status=pass`, `passed/pid_passed=true`, selected 18개, missing/mismatch/runtime-policy/dated-override/unverified 0 |
| WS·진행 | 08:07:53 LOGIN ACK, 08:07:55~56 자연 0B/0D 첫 수신. 08:08:03 main/scanner/sniper/telegram/error heartbeat 정상, 08:12:09 PID 생존 재확인 |
| 독립 위젯 | 기존 PID `15090`/07:57:59 시작 유지, active/running. 별도 재기동 없음 |
| Samsung 재기동 handoff | 표준 prepare/commit은 `not_required`/`morning_owner_not_active`; 독립 기계의 권한을 강제 발행하지 않음 |

근거는 `logs/bot_main_info.log`, `logs/bot_main_error.log`, `logs/kiwoom_sniper_v2_info.log`, `tmp/error_detector_heartbeat.json`, 위 exact-date verifier와 해당 systemd journal이다. 로그·verifier는 이후 정상 owner가 갱신할 수 있으므로 위 시각의 receipt와 현재 상태를 구분한다.

## 재기동 전후 계좌·owner 보존

기존 read-only broker helper로 08:05:38, 직전 08:07:31, 직후 08:08:35에 대사했다. KRX/NXT 잔고 조회와 미체결 normalization은 모두 complete였다.

- main 보유 0. 삼성전자 `005930` 25주는 widget owner, 삼성중공업 `010140` 10주는 `episode:samsung_heavy_morning:010140:2026-09-08` custody다. 세 snapshot의 수량은 동일하다.
- 미체결은 삼성중공업 SELL `0001493` 10주(체결0/잔량10, SOR) 1건이며 세 snapshot에서 동일하다. 미체결 BUY는 없다. 이 주문은 재기동 전 08:03:55부터 관측됐으나 현재 주문번호의 exact registry 귀속은 미대사다. main 주문이나 기존 자동 target `0018672`로 추정하지 않고 보존했다. 과거 주문 receipt/수동 successor의 exact 귀속은 별도 acceptance다.
- registry hash chain 유효, 18개 symbol의 quantity reconciliation PASS, unbound intent 0, 외부 미귀속 잔고 remainder 0을 확인했다. 이는 위 SELL 주문번호의 exact 귀속까지 완료했다는 뜻이 아니다.
- 아래 5개 파일은 재기동 직전/직후 SHA256이 동일했다. 모든 정책 파일을 전수 hash 검증한 것으로 확대하지 않는다.

| 파일 | 직전·직후 동일 SHA256 |
| --- | --- |
| `data/runtime/order_owner_registry.jsonl` | `c02ee779bc1a8d2bd44ff0860b936d387214dbe1851893b41a49d44381b8ce66` |
| `data/runtime/symbol_owner_policy/owner_custody.env` | `4e5e742ae9cbbfeaea6dff1c1b8cd80b2aad1656d7a6fb3a78ac76d1a8b5f89c` |
| `data/runtime/symbol_owner_policy/symbol_owner_policy_2026-09-09.json` | `cb24152c69a8885dd518279909f2dc2e0d8f7488a62e26489431a9e3bc3ffc02` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.env` | `ed11902d30be836f5fd792ded90fd118f08442de9f7d903695a321829b7c35a3` |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-09.json` | `a5f800eec8a17e3024e771bdb3e25d4238f35c4ea6e0aceac679da4120892129` |

## 별도 미해결: Samsung 오전 preflight

08:05:15/08:06:17/08:07:18의 재기동 전부터 `exact_date_authority_missing_or_stale` 경고가 있었다. 08:12:09에도 기존 preflight PID14358(07:57 시작)은 `activating/start`, morning live service는 MainPID0/inactive이며 선행 preflight 대기다. `Result=success`/이전 exit0 필드만으로 진행 중 preflight를 성공 terminal로 판정하지 않는다.

직접 사유는 `prior_reentry_order_or_position_unresolved`다. [reentry.py](../../src/trading/samsung_morning_one_share/reentry.py)의 `prior_reentry_allows_new_first_episode`는 전일 `NO_TRADE`에 대해 `attempt_consumed=false` 및 빈 legs/orders인 경우만 empty terminal로 허용하고, 시도한 두 leg의 terminal 허용은 상위 `COMPLETE`에 한정한다. 실제 전일 원장은 다음과 같아 현재 predicate에 거부된다.

- `data/runtime/samsung_morning_sor_reentry_state.json`, source date 9/8, SHA256 `baf805de4008e6e5b3f7d6df16d33db4ac0388ce9555ac5569aad7831140ffe7`.
- 상위 `NO_TRADE`, position0, `attempt_consumed=true`, 두 leg 모두 `NO_FILL`/filled0/remaining0, `last_buy_reconcile_source_ok=true`(전일09:44:04 receipt).
- 원래 주문 `0022725`/`0022729`와 추가 owned order `0023329`/`0023331` 이력 보존. 이 원장을 빈 미시도 상태로 만들거나 broker 잔고0만으로 `COMPLETE`로 바꾸지 않는다.

따라서 경고를 실제 잔여 보유가 입증됐다는 뜻으로 확대하지 않는다. `NO_TRADE + 시도한 NO_FILL legs`의 terminal 계약과 취소/주문 receipt를 대사해야 하는 별도 경계다. 이를 통과시키는 guard/code/state 변경은 조건부 재기동 권한에서 추론하지 않았다. 기존 wrapper의 bounded retry와 09:25:00 deadline을 유지했고 중복 preflight/live 기동은 하지 않았다.

후속은 [당일 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `WidgetEpisodeRecommendationApplyAcceptance0908`에서 exact 전일 주문 terminal → 허용된 contract 보완/review → 정상 preflight authority/PID → 자연 acceptance로 연결한다. 별도 수리 승인 전에는 차단을 보존한다. main 재기동을 반복해도 이 predicate는 해결되지 않는다.

## 리뷰·검증과 남은 경계

`korstockscan-review-gate`로 재기동 wrapper/authority handoff, singleton·flag race, 동일 날짜/PID consumer, 주문 owner 보존을 검토했다. 재기동 전에 관련 `test_restart_flag_race_guard.py`와 `test_samsung_morning_authority_handoff.py` **17 tests PASS**, `bash -n restart.sh src/run_bot.sh` PASS였다. pandas_ta deprecation warning 1건은 별도다. 이번 실행에서 코드 수정은 없으며 기존 전체 검증을 이번 새 테스트 결과로 중복 집계하지 않는다.

문서/기존 checklist 기록의 링크·owner·권한 경계 검토, print-only parser **39건/변경한 두 stable owner 각각 1건**, `git diff --check`와 신규 문서 whitespace 검사 PASS다. 08:14:38 재확인에서도 main PID24260·widget PID15090은 유지됐고 main heartbeat08:14:34/sniper08:14:38의 진행을 확인했다. 삼성 기존 preflight 차단과 미체결 SELL의 exact 주문 귀속은 미해결로 남으며 이번 기록의 main 재기동 성공과 분리한다. 신규 PID의 자연 eligible 경로·장후 exact funnel·실제 accepted submit/fill/terminal/net EV는 기존 OPEN owner의 후속 acceptance이며, clean commit이나 runtime PASS만으로 닫지 않는다.

외부 Project/Calendar sync는 실행하지 않았다. 필요한 경우 사용자 실행 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
