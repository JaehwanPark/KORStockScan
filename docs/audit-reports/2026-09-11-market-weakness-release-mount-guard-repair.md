# 2026-09-11 시장약세 entry guard 공유 경로 결함 수리·배포

작성 시각: `2026-09-11 14:37 KST`

## 판정

`BROAD_WEAKNESS`는 해소되지 않았다. `tmp/market_weakness_observer_state.json`의 최신 관찰은 `phase=active`, `active_markets=[KOSDAQ,KOSPI]`, `recovery_streak=0`이며 마지막 알림도 `transition=start`다. 해소 알림은 active market latch가 해제되는 `release` transition에서만 생성되므로 현재 해소 Telegram이 없는 것은 정상이다.

약세 중 widget Samsung 및 episode KEPCO의 BUY가 실행된 것은 정상 해소의 증거가 아니었다. 배포 release의 `data`와 `tmp`가 workspace 공유 symlink인데 entry guard가 `PROJECT_ROOT/data|tmp`를 엄격 no-follow JSON reader에 그대로 넘겨 `state_invalid`로 처리했고, 기존 source-unavailable 계약에 따라 비차단으로 반환한 결함이었다. Samsung widget BUY `0045909`와 KEPCO episode BUY `0049652`의 당시 guard receipt가 이 경로와 일치한다. 양쪽 왕복은 이후 전량 SELL terminal이며 이번 수리는 과거 거래의 수익 또는 정책 효과로 귀속하지 않는다.

## 수리와 리뷰

- commit: `6936e8fd411de9005902b24ebfaecafc3a7dc348` (`fix: preserve weakness guard across release mounts`)
- `src/utils/constants.py`: 공유 `tmp`의 canonical 경로인 `TMP_DIR`를 추가했다.
- `src/engine/risk/market_weakness_entry_guard.py`: state, verified symbol master, blocked-entry observation 기본 경로를 각각 resolved `TMP_DIR`/`DATA_DIR`에서 구성한다. artifact 자체의 symlink 거부와 기존 stale/missing 계약은 유지했다.
- `src/tests/test_market_weakness_entry_guard.py`: strict I/O 전에 세 공유 기본 경로가 canonical인지 검증한다.
- self review: runtime/order/provider/threshold/수량/Telegram transition 계약 변경 없음, in-scope P0~P2 finding `0`.
- 새 release root에서 관련 widget/episode/weakness 9개 suite `359 passed`, compileall 및 `git diff --check` 통과. 실제 공유 mount를 읽은 Samsung widget, Samsung episode, KEPCO episode 직접 판정은 모두 `entry_blocked_market_weakness_active`, `blocked=true`, `source_status=verified_symbol_market_loaded`였다.

## 운영 배포·재기동 receipt

- 선택 release: `/home/ubuntu/KORStockScan-runtime-releases/weakness-guard-mount-fix-20260911`
- 선택 commit: `6936e8fd411de9005902b24ebfaecafc3a7dc348`
- 이전 선택: `/home/ubuntu/KORStockScan-runtime-releases/target-pressure-audit-20260911` / `66a3189b03393bbf3f72d11a230510a912a9a0a0`
- 17개 `zz-unified-runtime.conf`를 새 고정 release로 전환하고 `daemon-reload`했다. 공통 cron routing 9개도 PASS했다.
- 14:34~14:35에 당시 실행 중이던 widget trader, Samsung afternoon, low-price afternoon 7개만 재기동했다. 새 PID는 widget `474978`, Samsung `474975`, low-price `475527/475537/475630/475662/475687/475740/475748`; 모두 새 release command, `active/running`, `Result=success`, `ExecMainStatus=0`, `NRestarts=0`이다.
- 전환 직전 14:34:11과 직후 14:36:01 broker KRX/NXT 조회는 동일하게 Samsung 25, Daewoo E&C 1, ICTK 1, 미체결 0이었다. 세 보유는 모두 `external_manual_remainder`로 균형 대사됐고 machine position으로 흡수하지 않았다. registry는 변경하지 않았고 주문·취소도 수행하지 않았다.

## 남은 확인

배포 후 직접 runtime 판정과 PID 소비는 완료됐다. 배포 뒤 아직 새 entry signal이 없으므로 자연 signal에서 blocked-entry observation이 생성되는 acceptance는 다음 자연 신호까지 `not_yet_observed`다. 실제 시장 회복은 KOSPI/KOSDAQ active latch가 기존 60초 간격의 유효 recovery 관찰 3회를 충족하고 `release` transition/Telegram receipt가 생길 때 별도로 확인한다.
