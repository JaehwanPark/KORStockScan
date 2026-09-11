# 위젯·에피소드 체결 Telegram 운영

2026-09-11 사용자 요청: 관찰/표본 수집 신호와 주문 접수 알림을 제외하고, 모든 위젯·에피소드의 실제 매수·매도 **체결 시만** 관리자 Telegram 알림을 발송한다. 종목 allowlist는 두지 않는다. 장후 추천 보고서 전달 및 시스템 장애 통보는 별도 owner다.

## 발송 계약

- owner는 `src/notify/machine_trade_telegram.py`, 독립 `korstockscan-machine-fill-telegram.service`다. `src/notify`는 알림 전달 패키지이며 trading engine 또는 새 engine-root producer가 아니다.
- 입력은 기존 `data/runtime/order_owner_registry.jsonl` 하나다. 기존 원장 reader의 schema/hash chain을 검증하고, 기존 writer lock을 read-only/nonblocking shared lock으로 잡아 snapshot만 읽는다. Telegram I/O는 lock을 놓은 뒤 수행한다. broker API/주문/정책/custody writer를 호출하지 않는다.
- 명시한 production account alias의 `widget_auto_trade|episode`, 실제 예약에서 시작한 NEW 주문의 BUY/SELL 체결 증가만 발송한다. 원장 정정 receipt로 NEW로 전환된 후속 주문, 원주문 추가 체결, 취소 대사 중 확인된 체결도 포함한다. CANCEL 자체는 체결 알림이 아니다.
- 부분체결은 이번 증가량과 주문별 누적/요청 수량으로 표시한다. 순차 3/10→10/10이면 3주 부분체결과 추가 7주 전량체결 알림이다. 금액만 늦게 갱신된 경우 재발송하지 않는다. 가격·비용·손익은 수량 receipt만으로 추정하지 않는다.
- 접수/거절/미전송/관찰/표본/다른 계정/main/sim 및 과거 migration/manual-flat 복원은 제외한다. 수동 매도 원장 복구를 자동 기계의 신규 매도로 표시하지 않는다.
- 처음 설치할 때만 `--initialize`로 기존 원장을 기준점으로 저장한다. 기존 과거 체결을 다시 보내지 않는다. 재시작은 저장 cursor/hash/발송 원장을 이어 읽는다. state 누락/손상·source rewrite/truncation은 자동 초기화하지 않는다.
- 5초 poll, poll당 최대 1회 발송. Telegram의 명시적 거절은 최대 3회이며 최소 30초 및 서버 `retry_after`의 긴 쪽을 전체 발송 queue에 적용한다. 성공은 API `ok=true`와 `message_id`를 확인한다.
- POST 결과가 불명확하거나 발송 중 crash이면 `uncertain`을 보존하고 자동 재발송하지 않는다. Telegram sendMessage에 idempotency key가 없으므로 완전한 exactly-once를 주장하지 않는다. `failed|uncertain`은 state에 남고 journal에 60초마다 미해결 건수를 출력한다. 운영자가 실제 수신 증거로 개별 대사해야 하며 state 전체 삭제/재초기화로 우회하지 않는다.

## 검토된 전환 대상

- 신규 알림 service의 코드 경로: `/home/ubuntu/KORStockScan-runtime-releases/machine-fill-telegram-20260911`.
- unit template: `deploy/systemd/korstockscan-machine-fill-telegram.service`.
- 다음 네 service에만 `deploy/systemd/machine-fill-telegram-only.conf`를 `99-machine-fill-telegram-only.conf` drop-in으로 적용한다.
  - `korstockscan-doosan-widget-collector.service`
  - `korstockscan-hanwha-ocean-widget-collector.service`
  - `korstockscan-samsung-widget-collector.service`
  - `korstockscan-widget-signal-auto-trader.service`
- collector 관찰 알림 4개 env와 widget 접수 알림 1개 env만 false로 바꾼다. 표본 수집과 trading source/전략/기존 release root/policy pin은 유지한다. 에피소드 process 재기동은 필요 없다.
- 기존 unit template도 동일 false 값을 갖춰 이후 installer가 관찰·접수 알림을 다시 활성화하지 않게 한다. 기존 알림 클래스의 강제 True 호출을 신규 표준 경로로 사용하지 않는다.

## 배포·기동 순서와 검증

1. 검토 commit·현재 service root/PID/drop-in·policy pin·주문/custody와 알림 설정을 기록하고 네 unit/drop-in을 백업한다. notification release에는 검토한 코드만 고정하며 공통 runtime selector를 변경하지 않는다. 기존 배포본의 source를 patch하지 않는다.
2. release의 data는 workspace data를 공유한다. state directory는 `data/runtime/machine_fill_telegram`이며 unit의 유일한 쓰기 허용 경로다. custody journal과 config는 read-only다.
3. 해당 운영 전환 승인을 확인한 뒤 알림 state를 한 번만 초기화하고 새 notification service를 시작한다. 초기화와 시작 사이에 추가된 체결은 cursor 이후 queue에 들어간다. 초기화 전에 발생한 체결은 과거 기준점으로 남는다.
4. 네 drop-in 설치/daemon-reload 후 collector 세 개 및 widget trader의 설정 소비를 확인한다. widget trader 재기동은 해당 변경의 운영 승인과 안전한 주문 상태 확인이 필요하다. 원래 source root·정책 pin·수량/미체결 보존을 검증한다. 다른 session의 배포를 덮지 않는다.
5. `ActiveState/Result/MainPID/cwd`와 실제 PID의 지정된 5개 알림 env만 검사한다. 전체 environ/config token을 출력하지 않는다. 새로운 매수·매도 자연 체결의 state `sent/message_id` 및 사용자 수신이 자연 acceptance다. 시험 주문이나 시험 Telegram 메시지를 만들지 않는다.

release cwd에서 아래 명령은 초기 설치용이며 한 번만 실행한다.

```bash
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.notify.machine_trade_telegram --account-key kiwoom-live-primary --registry /home/ubuntu/KORStockScan/data/runtime/order_owner_registry.jsonl --state /home/ubuntu/KORStockScan/data/runtime/machine_fill_telegram/state.json --initialize
```

같은 명령의 `--initialize` 대신 `--check`는 active service와 함께 실행 가능한 read-only config/source/cursor 검사다. 외부 메시지를 보내지 않는다. `--check` 없는 정상 실행은 실제 새 체결을 발송한다.

Rollback은 알림 service 중지와 해당 알림 drop-in의 백업 복원 범위다. state/cursor/receipt와 원장·정책은 보존한다. 기존 관찰/접수 알림 복원이 사용자 선택과 맞는지 확인하며, 불명확한 발송 row를 자동 replay하지 않는다. 매매 process 재기동 권한은 별도로 유지한다.
