# Main 선행 진입 부분 보유와 최소 체결비율 청산 충돌 수리

## 판정과 범위

- 사용자 지정 기준: `e04ccc5793004f385dcf8b845d4ed8061470f351`.
- 작업 branch: `fix/probe-partial-holding-20261016`.
- 판정: 코드 구현·리뷰·보완·재검증 완료. 배포는 별도 사용자 승인 대상이다.
- 기본 작업 공간의 동시 변경을 보존하고 별도 worktree에서 구현했다. release selector, 실행 PID, env, 정책 파일, cron을 변경하지 않았다. 실제 계좌/API/주문·Telegram 전송과 장후 보고서 재생성은 실행하지 않았다.
- 이 수리는 기존 probe-first 진입의 부분 보유 계약을 일치시키는 코드 변경이다. 수익성 개선, 자연 체결·청산 또는 운영 적용 완료를 주장하지 않는다.

## 확인한 결함과 보완

| 결함 | 변경과 수용 기준 |
| --- | --- |
| 잔량 전체를 제출한 `residual_submitted`는 부분 보유 종료 처리에서 누락됐다. | 기존 `residual_partial_submitted`와 동일한 종료 처리로 연결했다. 전체 목표 9주 중 1주 확보만으로 비율 청산하지 않는다. |
| 취소 함수가 이미 `partial_complete/HOLDING`으로 전환한 뒤에도 외부 정리 함수가 이전 목표 수량으로 최소 체결비율을 다시 판정했다. | 완료한 보유 전환을 존중하여 일반 비율 청산으로 내려가지 않는다. 일반 단일 주문의 부분 체결 최소 비율 정책은 유지한다. |
| 마지막 체결·취소 통지가 먼저 도착하여 취소 함수 진입 시 열린 주문이 없는 경로는 probe 계약을 지웠다. | 해당 경로에서도 정상 부분 보유 종료 처리를 먼저 시도한다. 별도 `initial_quantity_bundle`의 복구·종료 소유권은 보존한다. |
| 보유 전환 검사와 상태 변경 사이에 다른 청산 소유자가 생길 수 있었다. | `ENTRY_LOCK` 안에서 phase·열린 주문·청산 권한·현재 상태를 재검사하고 전환한다. fast exit token도 기존 exit 권한 검사에 포함한다. 외부 정리 함수 역시 기존 exit 권한이 있으면 새 매도를 시작하지 않는다. |
| 과거 누적 BUY 체결 수량이 현재 잔고보다 커도 부분 보유 수량으로 사용할 수 있었다. | 현재 `buy_qty`만 사용하며 `0 < buy_qty < requested_qty`와 `BUY_ORDERED/HOLDING`을 요구한다. 종료 포지션, 0 잔고, 전량 체결은 부분 보유로 재생성하지 않는다. |
| 오래된 probe 메타데이터가 다른 entry bundle에 남아 있을 수 있었다. | probe bundle ID를 요구하고, 현재 entry bundle ID가 있으면 일치를 검사한다. 새 atomic initial-quantity owner가 있으면 legacy 종료 처리를 하지 않는다. |
| 종료 후 지연된 부분 체결 알림이 잔량을 재검증 중이라고 표시할 수 있었다. | `partial_complete` 알림은 확보 수량과 잔량 진입 종료를 표시한다. 제출 후 취소된 수량을 미제출로 표시하지 않는다. 기존 알림 전송·중복 억제 시점은 유지한다. |

영향 코드: [종료·취소·정리](../../src/engine/sniper_state_handlers.py), [체결 알림 소비자](../../src/engine/sniper_execution_receipts.py), [회귀검증](../../src/tests/test_sniper_scale_in.py).

## 최종 동작과 권한

1. 선행 주문 및 잔량 주문의 제출·체결을 기존 방식으로 처리한다. 목표 수량, 선행 확약 수량, 조건부 잔량, 실제 제출 수량은 기존 필드로 구분한다.
2. 열린 잔량 주문에는 기존 TTL·취소 및 원 주문 종료/재고 대사를 적용한다. 취소 실패·종료 미확정·일부만 취소된 상태는 기존 pending 상태를 유지한다.
3. 동일 probe bundle의 제출된 BUY 주문이 모두 종료되고 현재 부분 잔고가 있으면 `partial_complete/HOLDING`으로 전환한다. terminal bridge는 지연된 체결 영수증을 위해 유지한다.
4. 전체 계획 대비 확보 비율만으로 추가 시장가 매도를 만들지 않는다. 이후 보유·손절·익절 판단은 기존 holding/exit 소유자가 계속 처리한다.
5. 일반 주문의 최소 체결비율 기본 20%, strong override 10%, preset 예외값은 변경하지 않았다. 수량 증가, 잔량 자동 재제출, TTL 연장, quote/account/broker/cooldown/manual/hard-safety 우회도 추가하지 않았다.

종목·시장·세션 allowlist를 새로 만들지 않았다. 고정 관찰 HPSP와 일반 종목을 포함하여 KRX 정규, NXT 장전·중첩 정규·장후, SOR 정규·장후 입력으로 같은 계약을 검증한다. 실제 시장별 실행 허용은 기존 route/session/order guard가 소유한다.

새 REST/계좌 조회, 파일 전체 재생, 대기·재시도는 없다. 비대상 phase는 기존처럼 즉시 반환하고, 대상 phase의 재검사와 상태 변경만 같은 잠금 안에서 수행한다. 성능 개선 수치나 운영 지연 개선을 측정한 것으로 보고하지 않는다.

## 리뷰 및 검증

- 1차: 기존 코드에서 목표 9주/확보 1주 사례가 두 residual phase 모두 `SELL_ORDERED`로 내려가는 것을 회귀검증으로 재현했다. 종료 처리와 중복 청산 차단을 구현했다.
- 2차: 청산 권한 경쟁, 과거 누적 수량, 종료 상태 재개방, 다른 bundle 소유권을 점검하고 보완했다. 실제 스레드의 잠금 대기 중 exit token이 생성되는 경우도 검증한다.
- 3차: producer의 probe bundle ID 보존, cancel terminal bridge, 일반 최소 체결비율 및 strong 예외, 기존 hard-stop/manual/exit 경로, 지연 알림 소비자를 재검토했다. 수정 범위의 미해결 코드 결함은 없다.

```bash
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k 'probe or partial or pending_entry or hard_stop or manual or exit_authority or split_entry or holding_sell_cancels' --tb=short
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m pytest -q src/tests/test_entry_split_order_plan.py src/tests/test_initial_quantity_bundle_state.py src/tests/test_initial_quantity_terminal.py -k 'probe_runtime or partial or terminal or receipt' --tb=short
/home/ubuntu/KORStockScan/.venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/engine/sniper_execution_receipts.py src/tests/test_sniper_scale_in.py
git diff --check
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

검증 결과: 첫 pytest 154건, 연관 consumer pytest 60건 통과. compile·diff·문서 parser 및 문서 상대 링크 검사도 통과했다. HTTP는 pytest의 기존 차단 장치와 모의 응답으로 격리했다. 일부 기존 테스트의 지연 quote worker가 `unit_test_http_not_mocked` 로그를 남기며, 실제 HTTP 전송은 차단됐다. 테스트의 모의 체결·종료는 실제 broker terminal이나 경제성 증거가 아니다.

## 공식 API 참조 확인

- 구현 전 조회: `2026-10-16T04:48:11.383894+00:00` / `13:48:11 KST`.
- official upstream: `Kiwoom-Securities/Kiwoom-REST-API`, SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`.
- 확인 경로: `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `ka10075/kt00007/kt10003/kt10001`, `postman/kiwoom-openapi.postman_collection.json`의 같은 API PRD/MOCK 항목. 현재 tree에 `kiwoom_docs`는 없었다.
- header `api-id/authorization/cont-yn/next-key`, POST JSON, account `/api/dostk/acnt`, order `/api/dostk/ordr`, 원 주문·확인 수량·체결 수량 및 venue 필드를 대조했다. `04:51:01 UTC` 보충 대조에서도 같은 revision을 사용했다.
- 요청/응답 parser, 전송, 인증, WS/FID, continuation, 실제 주문·취소 envelope는 수정하지 않았다. 기존 broker terminal 증거와 현재 재고 대사를 그대로 사용한다. upstream 예제를 주문 실행 권한으로 사용하지 않았다.

## 배포 인계 경계

이 문서는 배포 승인이나 일일 실행 항목을 생성하지 않는다. 코드 검증 결과와 향후 운영 적용·현재 PID 소비·자연 주문 종료·비용 후 성과는 별도 증거다. 이미 제출되었거나 완료한 매도 주문을 이 변경으로 되돌리거나 과거 손익을 수정하지 않는다. 배포와 재시작은 사용자의 별도 승인이 남아 있다.
