# 2026-09-07 수동 veto·동일종목 공존 최종 리뷰

점검 시작: 2026-09-07 15:59 KST. 최종 PID/env 확인: 16:17 KST. 대상일: 2026-09-07.

## 판정

코드 검증 범위는 보완 후 미해결 P0~P2 finding 0이다. **운영 반영은 미완료이며 수동목록 초기화는 실행하지 않았다.** 현재 PID가 수정 전 코드를 사용하므로 코드 PASS를 현재 프로세스의 안전성 PASS로 해석하지 않는다.

사용자가 승인한 초기화의 목적은 평상시 기계 scope와 메인 veto의 분리다. 파일 전체 삭제나 기계 대상 전체의 무조건 매매 허용이 아니다. 검토된 legacy 기계 표식만 `machine_owner_scope`로 전환하고, 명시적 사용자·일반·env·자동 위험 veto는 보존해야 한다. 같은 파일의 별도 source-kind로 구분되며 exact-date 실행 정책과 owner 원장이 실주문 권한을 소유한다.

## 최종 리뷰에서 추가 보완한 결함

| 발견 | 보완 | 회귀 확인 |
| --- | --- | --- |
| P1: 자동/env 제외가 이미 있으면 나중 사용자 수동 등록이 생략되어 자동 제외 해제 후 사용자 금지가 사라질 수 있음 | 각 veto source를 독립 행으로 영속하고 같은 source만 idempotent 처리. 마지막 개행이 없어도 별도 행으로 추가 | manual/generic, auto/env, 개행 유무, 자동 해제 후 manual 보존 |
| P1: scanner/state 통과 후 새로 등록된 veto를 최종 주문 전송 경로가 재검사하지 않음 | main 또는 legacy no-context 호출은 owner intent 예약 전에 현재 veto를 다시 검사. BUY·SELL·원주문 CANCEL 모두 local no-call 처리 | 활성 공존 정책 아래 manual/generic/env/auto별 broker 호출 0, registry mutation 0. SELL은 local no-call token 보존 |
| P1: 다중 auto 행에서 legacy scale-in qty handoff 제거가 별도 hard-stop 행까지 지울 수 있음 | legacy retirement는 `auto_scale_in_qty_guard_block` source만 제거 | 다른 hard-stop 및 사용자 행 유지 |
| P1: 표식 전환 뒤 사용자가 예전 기계 라벨을 붙인 manual 행을 추가하면 반복 migration이 재분류할 수 있음 | current machine 표식과 함께 존재하는 legacy-labeled manual은 명시적 veto로 취급하고 재전환 금지. veto 등록 API는 기계 권한용 표식 입력 거부 | 재migration 후 manual 보존, main 차단, machine scope 유지 |
| P2 test isolation: 전체 회귀에서 선행 token-replacement/cache 상태가 주문 request-contract fixture에 유입 | 주문 테스트의 제외파일·policy·registry·token cache/lock을 각 tmp 경로로 격리 | 전체 18-file 회귀 재실행 PASS |

독립 위젯·에피소드 owner context에는 메인 veto를 적용하지 않는다. 그들의 exact policy, registry, 원주문번호와 보유수량 검증은 그대로 유지한다. 수동 처분용 `manual_operator` 주문 context도 메인 봇으로 오인하지 않는다. 정책 부재·미선택·activation 불일치와 잘못된 machine 라벨은 메인 fail-closed를 유지한다.

## 운영 읽기 전용 근거

- Git branch `main`, HEAD `e7d3886a15deb5ca9bbc953735cccc3140dddbf1`. 이번 수정 및 다른 AI/scanner 작업의 미커밋 변경이 공존한다. 무관한 변경을 되돌리거나 커밋하지 않았다.
- main PID `356899`, 시작 `2026-09-07 13:08:27 KST`, 실제 env commit `9c712b4c3be0139d0579752faca02d28820a072a`, 시작 당시 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`. 현재 수정은 이 PID의 메모리에 반영되지 않았다.
- widget service PID `9704`, 시작 `07:57:59 KST`, active. 삼성 오전 service는 inactive이며 이 점검은 기계 service를 새로 시작하지 않았다.
- 현재 `manual_control_excluded_codes.txt`는 알려진 legacy 기계 표식 18행이다. 별도 명시적 사용자·자동 veto 행은 발견되지 않았다. 파일 SHA-256은 점검 전후 `56efd7881ab1ff04a47fa351e42bc4ca6a93770057715e23d535a094a8c1804d`로 동일하다.
- 당일 policy ID `same_symbol_owner_auto:2026-09-07:9e239f52eb45c030`, 파일 SHA-256 `208eb5b4b866b8275a8081b6554e0c89cd1c8df8eccb26b47dd5de6890b68a5a`. 16종목의 `COEXIST_ENTRY_ENABLED`와 exact activation을 검증했다. 삼성전자 `005930`, 한국전력 `015760`은 당일 적용 시 제외된 scope이므로 현재 잔고가 해소됐다는 이유로 당일 immutable policy를 확대하지 않는다.
- `16:09:30.499811+09:00` 읽기 전용 KRX·NXT broker snapshot은 대상 18종목 잔고 0, 미체결 0. owner registry도 대상별 수량 0, external remainder 0, open-order set 일치였다. transient snapshot canonical SHA-256 `66def9903ad67f1cf369919a3e60d6b8398fc62491a1d9b49b213e8d1d720818`. 이는 시점 관측이며 후속 mutation 직전의 연속 두 snapshot 또는 durable apply receipt를 대신하지 않는다.

## 공식 Kiwoom gate

2026-09-07 16:05 KST 전후에 [공식 Kiwoom 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 main revision `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. 해당 revision의 `kiwoom/_data/kiwoom_api_spec.json`(kt10000/kt10001/kt10003), `kiwoom/specs.py`, `kiwoom/core/client.py`와 Postman 계약을 대조했다. checkout에 `kiwoom_docs`는 없었다. 이번 변경은 로컬 메인 권한 veto이며 REST endpoint, api-id, 주문 payload, 가격·수량·broker safety를 변경하지 않는다.

## 검증 범위

- manual exclusion, coexistence, policy apply/auto-apply, widget, 저가 two-leg, Samsung morning/midday/afternoon 및 preflight, scanner pool, live PnL, process health, Kiwoom 주문, scale-in, restart race의 18-file 통합 회귀: **1,998 passed**, 55.99초. 외부 `pandas_ta`의 pandas4 deprecation warning 1건.
- 최초 전체 실행의 fixture 오염 1건을 보완한 후 전체를 다시 통과했다. broker/provider 실호출은 테스트에서 사용하지 않았다.
- 변경 runtime Python compileall 및 `git diff --check` PASS. 관련 source/test Ruff PASS; 기존 테스트의 `holidays` stub 후 import 2행만 의도된 E402 예외로 검사했다.
- 최종 검토는 diff뿐 아니라 scanner→state→broker 전송, recovery→owner 원장, machine ownership fallback, PREOPEN producer→pending receipt→재시도 consumer를 포함한다.
- 문서/checklist parser print-only 검증 PASS(49개 OPEN task; 새 배포 항목 포함). Project/Calendar sync는 실행하지 않았다.
- 테스트 검증은 live 체결 품질·실수익·재기동 후 실제 소비를 증명하지 않는다. 다음 PID, 다음 exact-date policy, 자연 pass/block/terminal 증거는 별도 OPEN acceptance다.

## 운영 blocker와 다음 acceptance

`process_reflection`: 현재 main/widget PID는 수정 전 코드다. `user_authority`: 현재 요청의 조건부 목록 초기화만으로 무관한 미커밋 변경까지 일괄 커밋·배포했다고 간주하지 않는다. 운영 runbook의 graceful restart 계약은 검증된 로컬 커밋과 clean source generation을 요구한다.

배포 범위를 확정하고 관련 변경을 커밋한 뒤, 기존 runtime/owner 연속성 계약에 따라 필요한 프로세스를 우아하게 교체해야 한다. 표식 전환은 trading process quiescence, 현재 policy/activation과 fresh broker·registry 재대사, 원본 hash/rollback 보존이 확인된 허용 적용 절차에서만 수행한다. PREOPEN 자동화의 시간창을 장중 시각 조작으로 우회하거나 old PID 실행 중 파일부터 비우지 않는다.

완료 조건은 ① 새 PID에서 수정 코드 소비 ② 사용자/auto veto 보존 ③ legacy 기계 표식만 변환 ④ 그 날짜의 허용 subset만 main 공존 ⑤ owner별 잔고·미체결 연속성 및 중복주문 0이다. 다음 PREOPEN 관측 owner는 `SameSymbolMachineScopePreopenAcceptance0908`이다.

이번 실행의 운영 변경: 목록 초기화 0, policy/env 변경 0, owner registry mutation 0, 주문/취소 0, process restart 0, commit/push 0.
