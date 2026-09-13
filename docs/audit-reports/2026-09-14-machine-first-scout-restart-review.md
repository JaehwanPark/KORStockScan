# 최초 기계판정 연결 수리 배포·재기동

## 판정

2026-09-14 08:49 KST: 코드 커밋·푸시·배포와 메인 재기동 검증 완료. 새 PID 이후 최초 기계/AI 판정 및 경제성은 미관측이며 별도 확인한다.

## 변경 및 검증

- 사용자 승인: 직전 최초 판정 수리의 commit/push/deploy/restart 및 기동 재점검.
- 코드 commit: `5e30fdb3fa0ca4f37d450b2006bb8e2b94dab927`, origin/main push 완료.
- Rising Missed의 action 누락·빈값·`-`를 기존 bounded 선판정 호출로 연결. 보유·미체결·가격 제한은 호출 전 차단하고 normal BUY caller의 별도 완료 action 입력은 보존한다. 기존 최종 authority/order 가드는 유지한다.
- 새 detached release에서 진입/submit 회귀 239개와 기계/AI 계약 44개, 총 283개 PASS. compile·diff 검사 PASS. 별도 기존 실패 3건(NXT TP1 2건, split-probe 필드 1건)은 변경 전 코드에서도 재현했으며 전체 테스트 무결함으로 보고하지 않는다.
- 관련 없는 수동 제외종목·custody·병행 테스트 변경은 커밋/코드 배포에서 제외했다.

## 배포·PID receipt

- 선택 root: `/home/ubuntu/KORStockScan-runtime-releases/machine-first-scout-repair-20260914`.
- 롤백 root: `/home/ubuntu/KORStockScan-runtime-releases/machine-all-continuous-r2-20260914`, commit `6207a60c`. 공유 data/logs/tmp/.venv/docs/restart.flag 유지. 기존 배포본을 수정하지 않았다.
- `bash restart.sh`의 기존 flag/정상종료/빈 supervisor 교체 경로로 old PID `10384` 종료 → new PID `67225`, 시작 `08:48:36 KST`.
- 새 PID cwd/root/commit 일치, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`. 당일 runtime env verify `pid=67225, status=pass`.
- 삼성 오전 authority handoff `committed`, 동일일자 PID binding만 교체하고 신규 권한을 발급하지 않음. 독립 매매 서비스는 재기동하지 않았다.
- WS 08:48:51 이후 실제 0B/0D 첫 수신 확인. 공통 cron routing 9개 PASS.
- 기계 bundle `3f6d353fdf930cac4ab31f6a49187a53deb667d14ac6d8be28c0058ef834d983`, 당일 env/operator override 및 독립 deployment manifest의 전후 파일 hash 동일.
- 실행 로그/롤백 선택/보호 hash: `tmp/machine-first-scout-deploy-20260914.RonIgd/`의 `restart.log`, `previous-selection.json`, `protected-hashes-before.json`.

## 잔여 확인

기존 [RuntimeEnvIntradayObserve0914](../checklists/2026-09-14-stage2-todo-checklist.md)에서 새 PID 이후 machine observation의 bundle과 source 시각, ENTER_NOW인 경우 AI PASS/VETO 및 최종 제출 guard를 확인한다. 08:49 점검 당시 새 판정 row는 0건이며 재기동 성공을 실제 판정·수익 개선으로 대체하지 않는다. 08:50 이후 정상 quiet 구간의 무수신을 장애로 단정하지 않는다. 장후 재생성·정책 변경·외부 sync는 실행하지 않았다.
