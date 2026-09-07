# 2026-09-07 전체 변경 병합·우아한 재기동

사용자 요청: `전체 커밋&푸시&main 병합 후 우아한 재기동`.

## 범위와 실행 경계

- 현재 작업 트리의 전체 소스·테스트·deploy wrapper·검토 문서를 대상으로 한다. 실행 중 계속 갱신되는 `data/cache`, `data/runtime`, `data/report` 산출물과 임시 파일은 보존하되 소스 커밋에서 제외한다.
- BUY Funnel schema5/exact2·controller/PREOPEN binding, AI trace caller lineage, census wrapper 실패 전파·SLA recall, micro timestamp source-quality, scanner lookup-attention source 제외·자원배분 증거 계약을 통합한다.
- 병합 전 producer/consumer·runtime authority를 리뷰하고 관련 회귀·compile·shell syntax·diff·checklist parser를 검증한다. 검증 중 소스가 바뀌면 해당 세대의 검증을 반복한다.
- 표준 `restart.sh`만 사용한다. Samsung owner handoff와 exact-date runtime verification이 실패하면 우회하지 않는다. 주문 취소·강제 매도·수량/threshold/provider/cap 변경은 요청 범위가 아니다.

## 사전 확인

- 시작 HEAD/main/origin/main: `314ca993`. 메인 봇 PID `195755`, tmux supervisor `bot`.
- 기존 PID exact-date `2026-09-07` runtime verification PASS: missing/mismatch/findings 0, runtime policy/dated override/unverified family 0.
- 12:57:40 KST read-only broker 확인: KRX/NXT inventory complete, 005930 40주·010140 10주·042660 20주, 미체결 SELL 5건. snapshot SHA256 `62899c67a12ee6bd88d56f2446dd862d9f0436e71c171e90b4901c175b189283`. 토큰은 existing cached token만 사용했고 신규 발급이나 주문 호출은 하지 않았다.
- 초기 통합 회귀 1,686 PASS, dependency deprecation warning 1건. 이후 scanner 코드 추가 변경을 확인하여 최종 검증 세대를 다시 확인한다.
- Ruff 전체 선택 파일에서 기존 `E402` 43건·`E722` 1건. 기존 HEAD의 `ai_engine_openai.py` 26건·`scalping_scanner.py` 18건과 동일하며 새 lint 진단은 없다. Python compile 및 shell syntax/diff 검사 PASS.

## 최종 결과

- 추가 scanner 검증 보완까지 포함한 마지막 재실행은 **1,689 PASS**, dependency warning 1건이다. 검증 전후 선택 소스·테스트·wrapper SHA256이 동일했다. malformed resource count의 fail-closed 처리, lineage/fill/resource census 대사, 정렬 시점 profile 고정과 versioned resource pair 검증을 재리뷰했다. traceability 표에서 이탈한 기존 5개 행은 원래 위치로 복원하고 신규 보충 설명은 표 밖에 유지했다. 검토 범위의 미해결 코드 finding은 0건이다.
- 최종 검증된 세대를 커밋 대상으로 고정한다. 커밋·병합 또는 재기동 직전 소스가 추가 변경되면 미검증 코드를 그대로 재기동하지 않고 재검증한다.
- 구현 commit `851f4505`를 `codex/full-workspace-verified-20260907`에 push하고, main에 no-ff 병합한 `9c712b4c`를 origin/main에 push했다. 서버는 기존 권한에 따른 PR-required rule bypass 알림을 반환했고 push는 성공했다. 저장소 보호 규칙이나 권한 설정은 변경하지 않았다.
- 표준 `bash restart.sh` exit 0. 기존 PID `195755`가 정상 종료된 뒤 **13:08:27 KST PID `356899`**가 시작됐다. singleton 1개, restart.flag 제거, tmux `bot` supervisor 유지. 강제 kill이나 별도 중복 프로세스 기동은 하지 않았다.
- 신규 PID `KORSTOCKSCAN_RUNTIME_GIT_COMMIT=9c712b4c3be0139d0579752faca02d28820a072a`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`. launcher는 기존 시작 commit을 보존하지만 loaded/current `src/run_bot.sh` SHA256은 `648b3cd86264d72d46b9c7ee8e8d175072a3f646ebe70425f73afc95b919cf1b`로 동일하다.
- exact-date runtime verify artifact `data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-07.json`와 재확인 모두 PASS: pid missing/mismatch/findings 0, runtime policy fail 0, dated override fail 0, unverified selected family 0. Samsung morning prepare/commit은 각각 `not_required / morning_owner_not_active`로 정상 종결했다.
- 재기동 직전 13:07:47 및 직후 13:08:45 KST read-only broker snapshot의 canonical SHA256은 위 사전 확인 값과 동일하다. 3종목 보유 수량과 SELL 5건의 주문번호·수량·잔량이 보존됐으며 별도 주문/취소/매도/신규 토큰 발급은 수행하지 않았다.
- 13:08:46 이후 WS 첫 실시간 `0B`/`0D` 수신, 13:09:14~16 scanner runtime attach 및 새 종목 수신을 확인했다. bot_main/scalping_scanner/kiwoom_websocket error log는 재기동 이후 갱신되지 않았다. 기동 확인을 미래 수익 개선이나 자연 source acceptance 완료로 해석하지 않는다.
- 후속 테스트 격리·완료 기록은 별도 commit/push하며 운영 Python/deploy 소스는 변경하지 않는다. 기존 자연 표본·장후/PREOPEN·실제 효과 확인 checklist owner는 OPEN으로 유지한다.

## 재기동 후 추가 검증

- 병행 scanner 검토 문서의 runtime 테스트 실패 19건을 확인하고 해당 module에서 실패를 재현했다(첫 실패까지만 실행: 20 PASS/1 FAIL). 기존 테스트 fixture는 manual-exclusion 파일만 격리했고 실제 당일 symbol-owner 정책은 읽고 있었다. 이번 병합에서 해당 runtime handler·owner-policy resolver·guard의 생산 코드는 변경되지 않았다.
- `test_kiwoom_sniper_market_regime_runtime.py` fixture에 임시 owner-policy 경로를 명시했다. 운영 파일/계좌/registry/guard를 변경하거나 resolver를 mock하지 않았으며 실제 검증 로직은 유지한다. 수정 후 해당 module 및 scheduler·owner-policy·watch-budget 회귀 **480 PASS**, compile/Ruff/diff PASS. 이 보완은 테스트-only이므로 다시 봇을 재기동하지 않는다.
- 일반 테스트 프로세스의 운영 정책 직접 해석은 `symbol_owner_policy_explicit_broker_account_key_required`로 fail-closed되는 것을 확인했다. 이 실패를 해소하기 위해 운영 계좌 키를 테스트에 주입하지 않고 운영 파일과의 의존성을 제거했다.
- 기존 통합 회귀와 위 6개 모듈을 한 번에 재실행한 최종 결과는 **2,169 PASS / 기존 dependency warning 1건**이다. 문서/location gate 53개도 이 수치에 포함되며 별도 가산하지 않는다. checklist print-only parser PASS, 완료 작업은 OPEN 목록에서 제외되고 자연 acceptance owner는 유지됐다. 검토 범위의 미해결 finding 0건이다.
- census installed-trigger receipt의 wrapper SHA256과 현재 wrapper 값도 동일함을 읽기 전용 확인했다. 새로운 설치·cron 변경·리포트 재생성을 수행하지 않았다.
