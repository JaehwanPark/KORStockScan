# 2026-09-08 09:27 우아한 재기동 검증

사용자 지시: `필요시 우아한 재기동`. 관찰 종료 기준: `2026-09-08 09:29 KST`.

## 판정과 필요성

메인 봇의 우아한 재기동을 완료했다. 기존 PID `20318`은 07:55에 `f9bd4637`의 `source_dirty=true` 상태로 시작했고, 이후 반영된 runtime 계측·정합성 변경의 실행 세대를 확정할 필요가 있었다. 재기동 직전 `src/`, `deploy/`, `restart.sh`는 검증·커밋된 `f67a7ec7f58fb3437035bd6215552d155fe08cf1`과 일치했다.

선행 [통합 검증](./2026-09-08-main-integration-validation.md)의 targeted 2,388 PASS와 Black CI 성공을 확인했다. 추가로 `test_restart_flag_race_guard.py`, `test_samsung_morning_authority_handoff.py`의 17개 테스트 및 `restart.sh`/`src/run_bot.sh`의 `bash -n` 검사를 통과했다. 테스트 warning 1건은 기존 pandas Copy-on-Write deprecation이다.

## 실행과 PID 검증

- 표준 `./restart.sh` 1회, exit 0. 09:27:10 restart 요청 → 09:27:11 기존 PID의 플래그 감지 → 09:27:20 신규 runtime source receipt → 09:27:21 Samsung handoff commit 순서를 확인했다.
- 새 PID는 `461794`, 실행 커밋은 `f67a7ec7`, 기동 시 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`다. 기존 PID는 종료됐고 main singleton 1개, restart flag와 임시 handoff plan은 정상 소비됐다.
- tmux `bot`의 supervisor PID `20215`는 유지됐다. launcher commit `f9bd4637`은 기존 supervisor 시작 기록이고 loaded/current launcher SHA256 `648b3cd86264d72d46b9c7ee8e8d175072a3f646ebe70425f73afc95b919cf1b`가 동일하므로 supervisor 교체가 필요하지 않았다.
- `data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-08.json`: `status=pass`, `pid=461794`, `pid_passed=true`, missing/mismatch/findings 0, runtime-policy/dated-override/unverified-family fail 0. handoff 시점 verify SHA256은 `67d6f8dba2f8c4e63c5435b68c7fe9edb6b55dc113f5b0dabb6b18ecfaacc990`이다.

## 주문·보유와 독립 owner 보존

기존 cached token만 사용한 읽기 전용 KRX/NXT 잔고·전시장 미체결 조회로 09:27:04.727529와 09:27:41.873527 스냅샷을 대조했다. 보조 조회 프로세스에서는 신규 token 발급·auth refresh를 금지했으며 별도의 주문·취소·강제 매도를 실행하지 않았다.

| 항목 | 재기동 직전 / 직후 |
| --- | --- |
| 보유 | `010140` 10주 / 동일 |
| 미체결 매수 | `0018068`, 10주, 체결 0, 잔량 10 / 동일 |
| 미체결 매도 | `0018672`, 10주, 체결 0, 잔량 10 / 동일 |
| broker canonical SHA256 | `a748ecfc751cdec97818bfcc06fc7b8fb04015ceeced1250e32a3bcb6f734e1e` / 동일 |
| owner registry | 156 rows, SHA256 `bcc2038632ba0248b32da6a3f0955ff10e37493d66fd4594878221782e8dd1a3` / 동일 |

09:25의 앞선 사전 조회와 비교하면 독립 삼성중공업 기계의 첫 leg가 **재기동 전에** 자연 체결돼 10주 보유와 target SELL이 생겼다. 이를 재기동에 의한 주문·수량 변화로 귀속하지 않는다. 재기동 직전/직후의 비교 창에서는 위 스냅샷과 registry가 동일했다.

삼성 오전 PID `21391`, 위젯 PID `21846`, 저가주 두산에너빌리티 PID `453099`, 삼성중공업 PID `453121`, SK텔레콤 PID `262537`은 모두 유지됐다. 이 독립 서비스들을 중단하거나 재기동하지 않았다.

삼성 오전 authority의 기존 main PID 연결만 `20318 → 461794`로 갱신됐다. handoff ID는 `931aa757afa63309e5413ed76674eb5ac949f5e0c56e76d36cb99a0e41a4a2ed`이며 `prepared_graceful_restart / committed`, 신규 BUY order number 0, policy/quantity/custody 변경 false다. 정책 SHA256 `f4bcc66244406a3c205e37a1590152c39493edb0e0a177a5e427bf3c3259e155`도 보존됐다. 신규 authority 생성이나 PREOPEN deadline 우회는 없다.

당일 threshold runtime env, `owner_custody.env`, exact-date symbol-owner policy의 파일 해시도 전후 동일했다. 수동 env·threshold·provider·수량·lock 변경은 하지 않았다.

## 기동 후 상태와 범위

- 09:27:30 WS 연결 및 LOGIN ACK, 09:27:33 이후 0B/0D 첫 실시간 수신, 09:28 이후 scanner attach/REG와 후속 수신을 확인했다.
- 09:28:55 기준 main heartbeat는 PID `461794`, age 2.4초이며 모든 기록된 worker의 alive는 true다. bot_main/WS/scanner error log에는 재기동 이후 새 오류가 없었다. 09:26:11 WS REMOVE 오류는 재기동 전 기록이다.
- 09:27:25에 별도 작업의 `build_code_improvement_workorder.py`, `scalping_pattern_lab_automation.py` 변경이 새로 나타났다. 이는 이번 새 PID의 source receipt 뒤에 생긴 변경이며 수정·커밋·추가 재기동하지 않았다. 기동 시 clean receipt와 이후 작업 트리 변경을 혼동하지 않는다.
- 이 결과는 기동·연결·주문 보존 acceptance다. 기존 체크리스트의 자연 표본, 장후/PREOPEN 추천, 비용 차감 EV/순이익 acceptance를 완료로 바꾸지 않는다.
