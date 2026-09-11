# 2026-09-11 위젯·에피소드 체결 전용 Telegram 리뷰

## 요청·직접 원인

사용자는 한화·두산의 관찰 신호 메시지를 중단하고 모든 위젯·에피소드의 실제 매매만 알리도록 요청했으며, 추가 선택에서 **매수·매도 체결 시만 알림**을 확정했다.

- collector별 notifier는 관찰 ENTRY/EXIT를 발송한다.
- 기존 widget notifier는 일부 7개 종목의 BUY 접수만 발송한다. SELL 체결과 종목 확대/에피소드에 공통 발송 경로가 없다.
- 기존 원장은 실제 양방향 체결과 정확한 소유자를 이미 보존하므로 trading loop 변경 대신 `src/notify`의 독립 read-only consumer로 해결했다.

## 구현·리뷰

[운영 계약/전환 절차](../machine-fill-telegram-operations.md)를 따른다. 독립 수리 worktree는 `/home/ubuntu/KORStockScan-runtime-releases/review-machine-fill-telegram-20260911`이다.

첫 구현 후 producer의 FILL_RECORDED뿐 아니라 정정 부모/후속과 취소 대사의 체결 증가를 추가 검토했다. 과거 migration/manual-flat을 신규 체결로 세지 않도록 최초 INTENT_RESERVED provenance를 요구했다. production account를 state와 CLI에 pin하고 종목 allowlist를 제거했다. live BUY/SELL 결정·source collector·정책·주문 API는 수정하지 않는다.

재리뷰에서 다음을 보완했다.

- 명시적 Telegram 거절의 서버 retry_after를 전체 queue에 적용하여 다음 주문 알림이 rate limit을 우회하지 않게 했다.
- HTTP 성공만으로 완료 처리하지 않고 ok/message_id를 검증한다. 모호한 전송/crash는 durable uncertain으로 남긴다.
- read-only --check가 active service의 instance lock과 충돌하거나 directory/lock을 생성하지 않도록 분리했다.
- source 변경이 없을 때 불필요한 projection/state fsync를 줄였다. registry lock은 nonblocking shared snapshot 구간만 사용한다.
- source rewrite/truncation 및 state 손상은 fail-closed다. 새 상태로 조용히 초기화하지 않는다.

## 검증

- 신규 23개 + 기존 widget/Doosan/Hanwha/Samsung notifier 테스트: **69 passed**.
- module py_compile, git diff --check 통과.
- 실제 원장 753행 read-only 재생: 알림 후보 99개(episode BUY45/SELL44, widget BUY8/SELL2). 이는 **역사적 재생 검증이며 발송 0건**이다. production 설치는 전량 과거 발송 대신 설치 시점 baseline을 사용한다.
- 삼성 당일 BUY0014018/1주 09:07:51, SELL0014048/1주 09:25:54가 각각 정확히 한 체결 알림으로 매핑됐다. amount-only 후속은 중복 메시지가 되지 않았다.
- 검토 범위 P0~P2 미해결 finding 0. 실제 전송/자연 체결 acceptance는 코드 검증과 별개다.

## 배포 경계

이 리뷰 시점에는 code/unit template만 준비했고 신규 알림 service 설치·기동, 네 기존 service 알림 drop-in 적용·재기동은 실행하지 않았다. 기존 알림은 아직 runtime에서 유지된다. widget은 당시 PID144180/`widget-profit-stagnation-20260911`을 사용하며 원 source/정책 pin을 변경할 필요 없이 알림 flag만 false로 소비하면 된다. 실제 전환 시 최신 root/PID/order 상태를 재확인해야 한다.

이전 보조익절 배포 승인은 그 수리의 receipt다. 이번 추가 알림 전환의 widget trader 재기동은 요청 범위를 명확히 확인한 뒤 수행한다. collector 세 개와 notification service는 알림 전환에 종속되며 에피소드 재기동은 불필요하다. 자연 체결 수신 후속은 당일 `MachineFillTelegramAcceptance0911` owner에 남긴다.

## 배포 준비 최종 검증

main commit `26d3e689`를 고정한 `/home/ubuntu/KORStockScan-runtime-releases/machine-fill-telegram-20260911`을 준비했다. data/.venv는 기존 workspace 공유 경로이며 src/deploy tracked diff 0이다. 같은 고정 root에서 69 tests 재검증 PASS, production config 로컬 읽기·원장753행 hash chain PASS, Telegram API 호출0이다. systemd-analyze verify PASS, 문서 parser PASS 및 `MachineFillTelegramAcceptance0911`이 정확히1개 파싱된다. 실제 systemd 설치/daemon-reload/재기동/알림 state 초기화는 미실행이다.
