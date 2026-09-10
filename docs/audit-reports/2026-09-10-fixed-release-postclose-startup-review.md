# 9/10 입력 보완 재리뷰 및 장후·다음날 고정 배포 유지 조건

작성: 2026-09-10 18:10 KST. 대상은 현재 배포한 entry 입력 보완과 실제 launcher/cron 연결이다. 병행 위젯 적응형 청산·profit-stagnation·custody 변경 전부를 리뷰한 결과가 아니다.

## 판정

- 현재 main은 `a722b27fd8c3e3158ce0aeb93fe9f53b04b7764c`, PID1048327, 17:54:12 시작이며 source clean이다. 고정 root는 `/home/ubuntu/KORStockScan-runtime-releases/entry-price-latest-20260910`이다. 정상 소스에서 긴급 교체를 요구하는 새 자연 장애는 확인되지 않았다. 기존 guard·collector/broker 상태가 유지되면 장후 전까지 이 배포를 유지할 수 있다. 제출 drought나 경제성 개선 완료를 뜻하지 않는다.
- malformed source 방어 처리 결함1건을 local 회귀에서 재현·수정했다. 수정은 작업폴더와 별도 `review/entry-input-postclose-20260910` 작업트리에만 있으며 현재 fixed release/PID에는 미반영이다. 실시간 원천에서 해당 malformed 구조가 발생했다는 근거는 없다. 이 잠재 결함이 없다는 뜻으로 현재 배포를 무조건 안전하다고 표현하지 않는다.
- 현재 설치 상태는 다음날 고정 배포 자동 유지가 아니다. cron/env/서비스/재기동/정책·quota·주문을 변경하지 않았다. 사용자 질문만으로 공통 deployment routing 변경을 승인한 것으로 간주하지 않았다.

## 재현·수리·리뷰

`revalidate_entry_candle_snapshot`가 저장된 `sources`, `sources.investor`, `sources.program`을 mapping이라고 가정했다. 비어 있지 않은 list/string이면 `.get()`에서 AttributeError가 나서 caller의 명시적인 source 거절 처리를 벗어났고, 빈 list/None은 빈 source로 묵인됐다. `test_malformed_source_mapping_rejects_handoff_without_leaking_exception[sources]`에서 기존 fixed 코드의 AttributeError를 먼저 재현했다.

생산된 canonical source의 구조를 검사해 잘못된 타입이면 `ValueError(entry_context_source_mapping_invalid)`로 거절하도록 보완했다. 정상 source·관측시각·provider·threshold·broker/수량/주문 권한은 유지한다. Handoff consumer는 잘못된 인계를 제거하고 기존 fresh rebuild로, 가격 AI consumer는 기존 candle-source veto로 연결된다. broker/Provider 요청 또는 Kiwoom parser/FID 변경은 없다.

`korstockscan-review-gate`로 producer→snapshot 재검증→handoff single-use/parent→가격 AI source veto→최종 제출 guard를 재리뷰했다. source3위치×잘못된 타입4개 반례와 가격 AI consumer의 malformed program source 반례를 추가했다. 별도 tree는 실제 배포 commit a722b27f에서 시작했으며 테스트 전 공유 data/logs symlink를 설치하지 않았다. 다른 세션의 소스를 섞어 테스트하지 않았다.

검증 대상은 entry snapshot/candle/market snapshot, sniper latency/scale-in, restart, entry live policy/intraday activation, PREOPEN apply, postclose chain verifier의10개 test 모듈이다. 최종 **1908 PASS / 24.11초**, 기존 경고1개. Ruff/Black check·compile·shell syntax·diff check PASS, 수정한 두 파일은 작업폴더와 별도 tree byte 일치를 확인했다. 작업폴더 직접 영향2모듈 **81 PASS**는1908개와 중복이므로 합산하지 않는다. 수정 후 재리뷰에서 이번 source 구조 방어/consumer 범위의 미해결 finding0이다. 실제 장후 보고서 생성·Provider replay·내일 자연 기동은 이 테스트에 포함되지 않는다.

## 실제 실행 경로

| 시점/동작 | 설치된 경로와 동작 | 현재 고정 배포 유지 여부 |
| --- | --- | --- |
| 현재 PID / 현 supervisor의 자식 재시작 | `entry-price-latest-20260910/src/run_bot.sh`, 종료 후5초 재시도·당일 env/정책 재검증 | 코드 경로 유지. 정책 수락은 별개 |
| 다른 세션의 수동 restart | 실행한 `restart.sh`의 PROJECT_DIR가 목표. root가 다르면 old child drain 뒤 supervisor 교체 | 작업폴더 restart를 실행하면 고정 배포가 풀릴 수 있음 |
| 오늘20:10 장후 | `/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh`, `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop` | `bot` tmux 세션 종료 예정. 장후 Python은 작업폴더 코드 사용 |
| 오늘21:05 paired replay | 작업폴더 `deploy/run_ai_entry_setup_paired_replay_postclose.sh` | live fixed 코드와 별도의 작업폴더 generation 사용 |
| 내일07:30 | `tmux kill-session -t bot` | 현재 세션을 유지하는 예약이 아님 |
| 내일07:35 PREOPEN | 작업폴더 `deploy/run_threshold_cycle_preopen.sh` | 작업폴더에서 새 날짜 후보/env/activation 생성·검증 |
| 내일07:55 기동 | 작업폴더 `src/run_bot.sh` | 현재 fixed release로 자동 연결되지 않음 |

20:10/07:30의 기존 tmux 종료는 이번에 사용한 custody-aware graceful restart 절차와 별개다. 이번 리뷰로 중단 방식까지 우아한 종료로 바뀌었다고 주장하지 않는다. 장후 stop 동작은 source root가 아닌 세션명 `bot`을 대상으로 하므로 fixed root 때문에 기존 정지 대상에서 빠지지 않는다. `stop` 설정은 장후 자동 재기동을 요청하지 않는다.

## 고정 배포가 유지되는 조건

1. live release의 tracked source/launcher를 수정·checkout/pull하지 않고 현재 supervisor를 유지한다. worktree가 분리됐다는 것은 강제 read-only 또는 자동 영구 pin을 뜻하지 않는다.
2. 재기동이 승인됐다면 실제 PID의 `KORSTOCKSCAN_RUNTIME_SOURCE_ROOT` 경로에서 `restart.sh`를 실행하고 새 PID root/commit/dirty·strict env/policy/custody를 다시 확인한다. 다른 작업폴더의 같은 이름 스크립트는 같은 배포를 의미하지 않는다.
3. 공유 `data`, `logs`, `tmp`, `restart.flag`, `.venv`와 source bundle을 보존한다. 고정 release도 이 경로는 작업폴더와 공유한다. 코드 고정은 dependency·policy/state·데이터 고정이 아니다. 정책 producer가 합법적으로 갱신하는 상태와 임의 덮어쓰기를 구분한다.
4. 당일 effective date, pin 코드/source hash, dependency, operator override와 만료 조건을 유지한다. 코드가 그대로여도 정책 만료/미승인/불일치로 V2.13 fallback 또는 기동 차단이 발생할 수 있다.
5. 내일까지 같은 코드로 기동하려면 예약 기동과 승인된 수동 restart의 release 선택을 통일해야 한다. 현재 이 조건은 미충족이다. `.env`에 commit 문자열을 적거나 main을 push하는 것만으로 cron의 실행 경로가 바뀌지 않는다.

## 오늘 장후·내일 기동을 위한 권장 후속

검토된 통합 release를 확정하고 공통 배포 진입점에서 main 기동·재기동 및 장후/PREOPEN의 code generation을 명시적으로 선택하도록 정리하는 것이 우선이다. 현재 a722b27f를 모든 장후 경로에 단순 대입하면 병행 producer 보완을 누락할 수 있으므로 live/장후 producer 호환성과 source hash를 먼저 검증해야 한다. 검토되지 않은 전체 dirty 작업폴더를 통째로 freeze하는 것도 하지 않는다.

이 release-routing 변경은 별도 사용자 승인 후 설치할 작업이다. 설치 시 현재 PID/위젯/episode는 건드리지 않고 정적 경로·shell·모의 기동 검증을 먼저 닫으며, 실제 재기동은 추가 승인 또는 기존 유효한 적용 계약을 따른다. 20:10 실행 중 wrapper/code는 교체하지 않는다.

내일 V2.14/1주/KRX100은 코드 유지와 별개로 source9/10 후보→9/11 PREOPEN/activation→PID 실제 소비를 통과해야 한다. 오늘 intraday pin은 launcher가 지우므로 전일 승인을 그대로 연장하지 않는다. NXT 후보 미승인·과거 source 결손을 KRX100 또는 반복 replay로 우회하지 않는다. 자연 기동 확인은 기존 `KRXDaily100NextDayStartupAcceptance0911`에 남긴다.

## 18:31 후속: 사용자 승인에 따른 공통 경로 설치

위의 18:10 경로 표와 승인 대기는 당시 상태다. 이후 사용자가 위젯/에피소드 적응형 청산 작업을 제외하고 경로를 통일하도록 명시 지시했다. 다음 설치 결과가 현재 경로 상태를 대체한다. 매매 정책·주문·현재 봇 재기동 승인을 확대하지 않는다.

- 선택 release: `/home/ubuntu/KORStockScan-runtime-releases/unified-runtime-20260910`, commit `b665e0a3abdff1abdf6902d3fc39af9df6591f64`. a722b27f 기반에 앞서 검토한 source mapping 방어와 PREOPEN OFF 표시 분류 보완, 배포 실행기 및 회귀 테스트/운영 문서만 포함했다. 다른 세션의 adaptive-exit/profit-stagnation/custody 변경은 포함하지 않았다. 이 commit은 별도 로컬 배포 branch이며 이번에 main 병합이나 원격 push는 하지 않았다.
- 선택 원장: `data/runtime/runtime_release_selection.json`. 선택 HEAD 일치, `src/deploy/restart.sh` clean, 공유 data/logs/tmp/.venv/docs/restart.flag를 매 실행 전 검사한다. 선택 원장 누락·변조·dirty code에는 작업폴더 fallback 없이 차단한다. 코드 선택은 당일 trading authority가 아니다.
- cron 9행만 공통 실행기로 교체하고 readback을 대사했다. 07:35 PREOPEN, 07:55 main start, 20:05 EOD, 20:10 postclose/controller/tuning, 20:50 archive, 21:05 paired replay, 21:55 finalization이다. 원래 시각·env 값·로그·나머지 모든 cron 행을 보존했다. 위젯/에피소드 systemd 및 다른 장중 observer/scanner 경로는 변경하지 않았다.
- 작업폴더 `restart.sh`는 같은 선택 release의 기존 restart 절차로 위임한다. 작업폴더 shim만 바꾸고 fixed release의 원본 `restart.sh`는 보존했다. `bash restart.sh --print-plan` 및 실행기 10개 operation의 9/11 모의 경로가 모두 동일 commit으로 해석됨을 확인했다. 실제 restart/start/장후/Provider 실행은 하지 않았다.
- 새 release의 bootstrap data/logs/docs는 삭제하지 않고 `tmp/unified-release-bootstrap-15Gc0w`로 이동한 후 공유 symlink를 설치했다. cron 전후 백업은 `tmp/runtime-release-cron-1kh4wtvu/{before,after}.crontab`이다. 전일 release는 유지한다. rollback 시 이전 release도 새 공유 docs 계약을 충족해야 하며, 이후 변경이 있으면 cron 백업을 통째로 덮어쓰지 않는다.

최종 별도 release 테스트 **1951 PASS / 24.50초**, 기존 pandas 경고1개. 입력·PREOPEN·정책·재기동·장후 verifier·라우터 11개 모듈이다. 실제 workspace shim 설치 후 라우터/재기동 회귀 **54 PASS**는 이 집합과 중복이므로 합산하지 않는다. Ruff/Black/compile/bash syntax/diff 검사 통과. 잘못된 operation prefix를 설치된 cron으로 오인하는 경우도 보완·회귀 검증했다. 이번 코드/배포 routing 범위 미해결 finding0이다.

기존 intraday 승인 artifact의 code pin10개와 source pin3개는 새 release에서 모두 일치한다. 이는 9/10 KRX 승인 시간창 연장 또는 NXT 승인 획득이 아니다. 9/11 실제 후보/env/activation·기동·자연 WS/AI·경제성은 아직 미래 검증이다.

18:30 readback 기준 main PID1048327/a722b27f(17:54:12), widget PID327676(07:57:59)은 그대로다. 따라서 현재 메모리에 새 source mapping 방어가 적용됐다고 주장하지 않는다. 오늘 20:10부터 예약 장후 작업은 선택 release, 다음 정상 기동도 선택 release를 사용한다. 기존 20:10/07:30 stop 동작은 바꾸지 않았고, 기존 supervisor의 자체 자식 재시작은 old root를 계속 사용한다. 현재 main을 새 root로 즉시 옮기려면 별도 승인된 우아한 재기동과 실제 PID 검증이 필요하다.

유지 조건 및 read-only 점검법은 [공통 배포 경로 운영](../runtime-release-routing.md)에 기록했다. 선택 release를 직접 수정/pull하거나 오래된 cron installer가 경로를 재작성하면 같은 배포가 유지된다고 보장하지 않는다. 향후 release 변경은 실행 중 장후 chain이 없을 때 검토된 root/commit으로 선택 원장을 원자적으로 교체하고 cron check 및 다음 PID를 확인한다. 적응형 청산 코드를 main에 병합하는 것만으로 이 선택 release가 자동 변경되지는 않는다.

설치 후 현재 a722b27f root에서 PID1048327의 9/10 strict verify를 읽기 전용 실행하여 `passed=true`, `pid_passed=true`, errors0을 재확인했다. 선택 release source clean 및 cron9행 검증도 PASS다. 문서 parser는27개 OPEN을 정상 출력하며 다음날 기동 owner가1개 존재한다. Project/Calendar 외부 동기화는 실행하지 않았다.
