# 위젯 PID 환경 검증 보완

대상일: 2026-09-07 KST. 기준 commit: `d568e90b3b91821cc9e3298e1a6126be526d5cc6`.
사용자 지시: 위젯 PID 환경 조회 권한 문제 보완 및 `korstockscan-review-gate` 적용.

## 범위와 판정

위젯은 `ubuntu:www-data`(UID1000/GID33), 점검 프로세스는 `ubuntu:ubuntu`(UID1000/GID1000)다. `/proc/PID/environ`은 추가 ptrace credential 검사를 받아 같은 UID만으로 외부 조회가 허용되지 않는다. 서비스의 `.env` 적재 장애 또는 재기동 명령 권한 오류와는 별개다.

서비스 권한을 바꾸지 않는 startup 자기 기록과 read-only 검증 경로를 구현한다. 기존 데이터 dirty 파일을 보존하고 systemd 설치·User/Group·NoNewPrivileges·ptrace 설정·sudoers·현재 PID·policy/env·매매목록·주문·계좌 원장을 변경하지 않는다. 커밋/푸시/재기동은 이번 요청 범위에서 실행하지 않는다.

## Producer → consumer 계약

- 신규 모듈 위치는 위젯 운영 진단 owner인 `src/trading/widget_auto_trade/runtime_verification.py`; engine root 신규 모듈 없음.
- `service.main`: singleton lock → trader 생성 → startup receipt → 기존 once/forever cycle. 주문 engine, gateway, parser, guard는 변경하지 않는다.
- 기본 출력은 `data/runtime/widget_signal_auto_trade_state.runtime-receipt.json`. `--state-path`를 쓰면 같은 경로에서 suffix만 바뀐다. 임시 파일 0600, fsync 후 atomic replace. 기존 state나 custody를 덮어쓰지 않는다.
- 환경변수는 exact allowlist 8개만 값 해시/미설정 null로 남긴다. prefix wildcard, 원문·API key·token·계좌 식별자·계좌 식별자 해시는 제외한다.
- effective config hash는 실제 trader의 enabled, entry_qty, 정렬된 symbol, execution policy manifest, 정규화된 interval 및 once를 canonical JSON SHA-256으로 계산한다. loaded execution policy hash는 trader가 이미 검증·로드한 `_dated_execution_policies`의 canonical SHA-256이다. 현재 디스크 파일을 다시 읽어 과거 소비값으로 포장하지 않는다.
- Consumer CLI는 fixed 위젯 unit의 active/running/MainPID와 start ticks/boot ID/UID/GID를 검증 전후 대조한다. 다른 PID 환경을 읽거나 승격 권한을 요청하지 않는다. 모든 CLI 결과에서 비밀값과 원본 exception 내용을 제외한다.
- Receipt hash는 오염 감지용이며 서비스 UID에 대한 암호학적 서명/위조 방지가 아니다. trusted service-user 경계와 systemd metadata를 전제로 한다.
- 기대값을 주지 않으면 `observed_not_compared`, exit2. 독립 reviewed 기대값을 제공하고 요청한 항목이 일치해야 `verified_requested_startup_fields`, exit0. 부분 키 검증을 전체 설정 검증으로 확대하지 않는다.
- startup-only이며 current policy reload, 계좌 binding, symbol-owner 정책의 주문 시점 실제 소비, source commit, WS·broker/terminal, 수익성·실주문 승인 검증은 포함하지 않는다. `runtime_effect=false`, `allowed_runtime_apply=false`, `current_policy_consumption_verified=false`를 고정한다.
- Publisher 오류는 고정 warning과 False를 반환하여 기존 custody cycle을 막지 않는다. Verifier는 missing/unreadable/invalid/old receipt에 대해 blocked로 닫는다. 기존 PID의 기록을 소급 생성하지 않는다.

## Review/fix/re-review

1. 최초 구현을 producer→consumer→service 진입·singleton·기존 매매 분기 순으로 리뷰했다.
2. 재리뷰에서 FIFO/device를 JSON으로 열 때 검증이 멈출 수 있는 경로를 확인해 nonblocking open·regular-file 검사·symlink 거부를 추가했다. JSON 중복키·크기 상한·malformed/hash/date/authority 검증도 fail-closed다.
3. process credential의 길이/형식, boot UUID 형식, bool/int identity 혼동과 원문 exception 노출을 검토·보완했다. 미사용 test import도 제거했다.
4. 기존 PID receipt 부재와 기대값 미제공을 성공으로 오판하지 않으며, 기록 실패가 broker safety/custody 중단으로 이어지지 않는지 검증한다.
5. 실제 CLI 실행에서 패키지의 eager engine import가 JSON 앞에 broker 설정 안내문을 출력하는 P2 결함을 재현했다. `widget_auto_trade.__init__`의 기존 public export를 lazy import로 보존하고 verifier는 stdlib-only 경로 기준을 사용하도록 보완했다. 새 Python 프로세스 테스트로 engine/constants 미적재·stdout 단일 JSON·stderr 빈값과 기존 export 호환을 검증했다.

## 검증 및 잔여 acceptance

아래 205 PASS는 최초 구현 검증 기록이다. 후속 명시적 재리뷰에서 재현된 3건과 수정 후 최종 판정은 아래 `추가 코드리뷰`를 따른다. 운영 source 또는 기존 PID receipt는 테스트를 위해 수정/생성하지 않았다. 실제 생성·소비는 다음 허용된 정상 기동 후 `ManualVetoCoexistenceDeployment0907` 및 `SameSymbolMachineScopePreopenAcceptance0908`의 OPEN acceptance로 유지한다.

- 7-file targeted regression: **205 passed**, 18.80초. `test_widget_runtime_verification`, `test_widget_signal_auto_trade`, `test_widget_auto_trade_policy`, `test_widget_auto_trade_notifications`, `test_widget_auto_trade_policy_calibration`, `test_widget_symbol_runtime_policy`, `test_engine_location_gate`.
- 검증 범위: 비밀값 제외, missing/empty 구별, partial expectation, PID/start/boot/credential 불일치, 검증 도중 PID 교체, 미래/자정·UTC/KST, hash/authority/schema/중복 JSON/크기 상한/FIFO/symlink, atomic publish 실패·원본 보존, singleton, 실제 trader 생성 결과 해시, 기존 매매/정책/알림·public import 호환.
- 변경 Python 4개 Black/Ruff/compile PASS, `git diff --check` PASS. 문서/checklist parser print-only exit0; Project/Calendar sync 미실행.
- 현재 위젯 `MainPID=9704`, `start_ticks=282572`, UID1000/GID33. 새 진단 경로가 일반 사용자 권한으로 필요한 systemd/proc metadata를 읽는 것을 확인했다. `/proc/PID/environ`은 재조회하지 않았다.
- 수정 후 실제 CLI 출력은 추가 안내문 없는 단일 JSON, `status=blocked`, `findings=[receipt_missing]`, exit2. 구버전 PID 미계측을 올바르게 차단했으며 기존 PID용 receipt를 합성하지 않았다. service active/running 및 07:58 기동 유지.
- 현재 PID에서의 새 publisher 실행과 계좌/broker 실호출 시험은 재기동·주문 권한 범위 밖이므로 미실행이다. full-repository test나 비싼 장후 report 재생성도 이번 진단 계측 변경의 검증 범위가 아니다.
- 작업 도중 다른 운영 문서/AGENTS 변경이 나타났으며 보존했다. 이번 변경은 위젯 Python 3개(신규 verifier·service·package init), 신규 테스트, 본 리뷰 문서와 traceability/checklist의 해당 추가 문단뿐이다. 다른 변경의 리뷰/완료를 주장하지 않는다.

읽기 전용 점검:

```bash
PYTHONPATH=. .venv/bin/python -m src.trading.widget_auto_trade.runtime_verification --target-date 2026-09-07
```

구버전 PID에서는 `receipt_missing`, exit2가 예상 결과다. 단순 source 배치로 현재 PID가 새 계측을 소비했다고 선언하지 않는다. 검증용 기대 JSON은 runtime 적용 env가 아니며, 승인된 설정의 allowlist 항목만 담는다. 실제 호출 시 당일 또는 점검 대상 startup 날짜를 명시한다.

## 추가 코드리뷰

사용자의 `코드리뷰후 수정보완, 결함이 없을때까지 반복` 지시에 따른 재검토다. 이전 자연 acceptance의 부재 때문이 아니라 아래 새 재현 결함으로 코드 검토를 재개했다.

| ID | 심각도 | 재현한 결함 | 보완 및 재검증 |
| --- | --- | --- | --- |
| WVR-R1 | P2 | self-hash/PID가 맞으면 mode0666인 receipt도 PASS; trusted service-user 경계를 파일 owner/mode로 검증하지 않음 | 열린 fd의 소유 UID를 대상 filesystem UID와 비교하고 mode0600만 허용. foreign UID 및 666/620/602/644/400 거부, 정상600 유지 |
| WVR-R2 | P2 | 두 번째 systemd 확인 때 동일 bytes의 새 inode로 receipt를 교체해도 PASS | 한 read의 시작/끝 fstat 및 최종 재읽기의 device/inode/owner/mode/size/ns timestamps/content를 대조. 교체·in-place 수정·삭제·읽는 도중 수정 모두 blocked |
| WVR-R3 | P2 | publisher 실패 뒤 warning logger가 OSError를 내면 service의 첫 cycle 진입 전 예외 전파 | 고정 메시지만 사용하는 safe warning과 stderr fallback. 양쪽 sink 및 임시파일 정리까지 실패해도 기존 custody 경로로 예외를 전파하지 않음 |

- 수정 전 `pytest -q src/tests/test_widget_runtime_verification.py -k test_review`: **3 failed / 45 deselected**로 세 결함을 실제 재현했다. 운영 파일은 사용하지 않았다.
- 보완 후 전용 경계와 기존 위젯·policy·알림·calibration·location gate를 포함한 동일 7-file 전체 회귀: **217 passed**, 18.25초. 최초 205개에 12개 사례를 추가했다.
- 서로 다른 test 실행 UID에 따라 owner 검증 결과가 바뀌지 않도록 fixture UID를 현재 실행 UID로 격리했다. 운영 User/Group은 변경하지 않았다.
- 수정 후 producer→error handler→최초 cycle, reader→schema→file trust→PID→기대값→최종 generation consumer를 다시 검토했으며 검토 범위 미해결 P0~P2 finding **0**이다. 최종 Black/Ruff/compile/diff 및 print-only parser **PASS**다.
- 새 운영 receipt 발행·서비스 재기동·권한/정책/주문/목록 변경·커밋·푸시·Project/Calendar sync는 하지 않는다. 계좌 binding·동적 policy 실제 소비·다음 정상 기동 acceptance는 여전히 별도이며 이 코드 검증으로 완료 처리하지 않는다.
