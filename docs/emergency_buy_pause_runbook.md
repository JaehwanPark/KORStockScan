# 긴급 매매중단 운영 메모

## 1. 공식 의미
`pause.flag` 존재 시 시스템은 공식적으로 `신규 매수 및 추가매수 중단 상태`로 간주한다.

이 상태는 전체 매매중단이 아니다.

막히는 것:
- WATCHING 상태의 신규 매수 진입
- HOLDING 상태의 추가매수 (`AVG_DOWN`, `PYRAMID`)
- 기타 BUY-side 주문 생성

계속 유지되는 것:
- 웹소켓 연결과 실시간 시세 수신
- 계좌 동기화
- HOLDING 종목의 익절, 손절, 청산
- SELL 주문
- 취소 / 정정 / reconcile 처리
- 체결 영수증 처리
- DB, 로그, 텔레그램 알림

## 2. 관리자 제어 방법
관리자 전용 버튼:
- `🛑 긴급 매매 중단`
- `▶️ 매매 재개`
- `📛 현재 매매 상태`

관리자 명령:
- `/pause`
- `/resume`
- `/pause_status`
- `/trading_status`
- `/buy_pause_confirm <guard_id>`
- `/buy_pause_reject <guard_id>`

상태 라벨:
- `✅ 현재: 정상운영`
- `⏸ 현재: 매매중단`

상태조회 응답:
- `현재 상태: 정상운영`
- `현재 상태: 신규 매수/추가매수 중단`

가드 승인형 운영:
- `buy pause guard`가 `09:30~11:00` 사이 5분 간격으로 fallback canary 악화를 자동 평가
- 경보는 관리자에게만 발송되며, 자동 pause는 하지 않음
- 운영자는 `/buy_pause_confirm <guard_id>` 로 승인하거나 `/buy_pause_reject <guard_id>` 로 거절
- `guard_id`는 텔레그램 `ADMIN_ID` 숫자가 아니라, 경보 건별 운영 티켓 ID다
- 형식 예시: `BPG-20260409-1000-01`
- 텔레그램 입력 예시:
  - 경보 승인 후 buy pause 실행: `/buy_pause_confirm BPG-20260409-1000-01`
  - 경보 거절: `/buy_pause_reject BPG-20260409-1000-01`
  - 현재 상태 확인: `/pause_status`
  - guard와 무관하게 즉시 수동 pause: `/pause`
  - 수동 재개: `/resume`
- Codex 백업 경로:
  - `buy pause 실행해줘`
  - `buy resume 실행해줘`
  - `buy pause 상태 보여줘`

## 3. 부팅 시 확인 포인트
부팅 시 `pause.flag`가 남아 있으면 시스템은 자동으로 pause 상태를 유지한다.

운영자가 확인할 수 있는 신호:
- 로그: `⏸ 부팅 시 pause.flag 감지: 신규 매수 및 추가매수 중단 상태로 시작합니다.`
- 관리자 알림: 동일 문구가 관리자에게 발송될 수 있음

재시작 직후 매수가 안 나가더라도 의도된 동작일 수 있으므로 먼저 상태조회 버튼 또는 `/trading_status`로 확인한다.

## 4. 로그 태그
pause 관련 표준 태그:
- `[TRADING_PAUSED]`
- `[TRADING_RESUMED]`
- `[TRADING_PAUSED_BLOCK]`
- `[BUY_PAUSE_GUARD]`

예시 grep:
```bash
grep -E 'TRADING_PAUSED|TRADING_RESUMED|TRADING_PAUSED_BLOCK' logs/bot_history.log | tail -n 100
```

## 5. 설계 원칙
- 영속 truth source는 `pause.flag`
- EventBus는 즉시 반영용
- 최종 BUY 차단 판단은 file flag 기준
- BUY-side는 전략 판단 레벨과 주문 전송 레벨에서 모두 차단
- HOLDING 청산 로직은 차단하지 않음

## 6. 운영 첫날 체크리스트
- 관리자 키보드에 pause 관련 버튼 3개가 보이는지 확인
- `/trading_status` 응답이 현재 상태와 일치하는지 확인
- pause 후 신규 매수 / 추가매수 로그가 `[TRADING_PAUSED_BLOCK]`로 남는지 확인
- pause 후 HOLDING 청산은 계속 동작하는지 확인
- 재시작 후에도 pause 상태가 유지되는지 확인
