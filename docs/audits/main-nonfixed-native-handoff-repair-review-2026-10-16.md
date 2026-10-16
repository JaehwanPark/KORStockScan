# 비상시 native 관측의 Main 이관 경합·영수증 연결 수리

- 최초 구현 기준: 선택 `59c92909783e967397a8d774bab60cd22ec78c96`, PID `3600286`, start ticks `18867646`.
- 최종 통합 부모: 작업 중 별도 배포된 `48968ade9022fcfaf69b9c081f703be3324d33c0`, PID `3646205`, start ticks `18963364`. 해당 탐지기·알림 보완을 보존해 rebase했으며 진입 이관 관련 production 파일은 최초 기준과 동일했다.
- 작업 트리: `/home/ubuntu/KORStockScan-worktrees/nonfixed-native-handoff-20261016`.
- 사용자 범위: 최우선 결함 구현 → 코드 리뷰 → 보완 → 재리뷰 → 표적 검증 → 커밋. 배포·재기동은 별도 진행한다.
- 실행 owner: 현재 checklist의 `NonfixedDispatchReadinessReview1012`. 기존 OPEN·Acceptance·History를 유지한다.
- 상태: 코드 검증 완료, 배포 대기. 이 문서는 실제 PID 반영·자연 제출·체결·경제성을 증명하지 않는다.

## 원인과 변경

장전 기계 ENTER_NOW 5건은 임시 감시 등록 뒤 모두 `attach_or_db_finalize_failed`로 거절됐고 원 native 기한은 3.96~4.51초 남아 있었다. 각 내부 최종화 사유가 `{}`로 유실돼 5건 모두가 동일 경합이었다고 소급 확정할 수는 없다. 최신 PID의 첫 비상시 3건은 원천/패턴 단계에서 멈췄으며, 과거 5건을 현재 PID 실패로 합산하지 않는다.

1. 관측→Main 연결이 generic `COMMAND_WS_REG`를 발행해 이미 유효한 exact 구독을 `REMOVE → REG`로 교체했다. 그 사이 item epoch/type 영수증이 사라져 Main 최종화가 유효 기한 안의 신호를 `native_handoff_invalid`로 거절할 수 있었다. 이제 provisional native 경로는 해당 명령을 발행하지 않고 `KiwoomWSManager.adopt_zero_base_probe_target`으로 기존 구독의 로컬 소유권만 넘긴다. 새 프로토콜·등록 재시도·시간 연장은 없다.
2. 이전 blocking 경로는 `payload`에 최종화 사유를 기록한 뒤 `result`에서 영수증을 읽었다. 실제 최종화 payload를 명시적으로 전달해 성공·거절·예외·스케줄러 거절 영수증에 원 사유를 보존한다. physical lease ID도 result → payload → target → 최종화까지 유지한다.
3. 후속 리뷰에서 실패한 편입이 DB의 `PROBE_READY`에 남는 정리 결함을 보완했다. 원 ID/code의 기존 provisional row 계약을 확인한 뒤 만료하고, 최초 실패 영수증과 별도 `rollback_receipt`를 유지한다. 동일 정리는 반복 실행에 안전하며 확정 감시·보유 target을 지우지 않는다. DB 정리가 실패하면 실패를 그대로 남기고 정리 완료로 합성하지 않는다. 과거 임시 행은 수정하지 않는다.

## 보존한 경계와 리뷰

- `native_observation`의 원 process/start·event/item/route·transport epoch·물리 lease·wall/perf 기한을 검사한다. 등록0B/0D 결손, 제거 중 lease, 다른 lease/epoch, 다른 runtime route, 원 기한 만료는 계속 거절한다.
- 관측 store의 가격/호가를 executable store로 복사하지 않는다. 실제 후속 REAL 0B/0D가 기존 parser를 거쳐 runtime snapshot을 채운다. REG 시각·native epoch·원천 수신 영수증을 새로 만든 것처럼 갱신하지 않는다.
- 단일 native claim, durable admission, DB commit, Main target의 원 deadline 연결을 검토했다. source-only lease cleanup은 성공한 Main 구독을 REMOVE하지 않으며, 실패한 provisional target은 기존 정리 경로로 회수한다.
- Main/manual custody, 다른 exact 관측 route, fixed-watch, retirements, provider·AI/진입 threshold·주문/수량·계좌·cooldown·stale/conflict·hard safety를 보존한다. 슬롯5/long3 및 residence60/150초도 변경하지 않는다.
- 구현은 기존 live runtime 파일 `src/engine/kiwoom_sniper_v2.py`, `src/engine/kiwoom_websocket.py`에 둔다. 기존 테스트 파일을 확장하고 새 engine-root Python 모듈은 만들지 않는다.
- 구현 → 1차 리뷰 → lease ID/실패 정리/보유 보호 보완 → 재리뷰 → 검증을 수행했다. 이 범위의 미해결 코드 결함은 없다. 자연 신호 수용은 기존 owner의 OPEN 상태다.

## 공식 Kiwoom 참조

수정 전 `2026-10-16T13:32:38+09:00`에 공식 저장소의 현재 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 조회했다.

- 원천: [Kiwoom-Securities/Kiwoom-REST-API](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f).
- 확인: `kiwoom/realtime/packets.py`, `kiwoom/realtime/stream.py`, `kiwoom/core/ws_client.py`, `kiwoom/core/auth.py`, `kiwoom/specs.py`, `postman/kiwoom-openapi.postman_collection.json`.
- 현재 upstream에는 `kiwoom_docs`와 요구된 카테고리 문서가 없다. 문서 부재를 protocol contract gap으로 보존하며 미정의 FID·단위·suffix·제한을 추정하지 않는다. 이번 변경은 기존 exact 등록 영수증의 로컬 custody 이관에 한정한다. request/response·REG/REMOVE envelope·refresh·URL·인증·reconnect·parser·FID·계좌/주문 프로토콜은 변경하지 않는다. 공식 packet builder의 REG/REMOVE와 refresh 의미를 교차 확인했다.
- SHA·경로·파일 해시: [공식 원천 확인 영수증](/home/ubuntu/KORStockScan/tmp/nonfixed-handoff-implementation-20261016-1330/official-reference.json).

## 검증과 제한

- 원 선택본의 두 production 파일로 되돌린 격리 재생에서 NXT/SOR 정상 편입, 실패 provisional 정리, blocking 상세 영수증의 회귀 **4개 실패**를 확인한 뒤 수정본을 복구했다.
- 수정본 관련 **729개 PASS**: WebSocket, native Main attach, zero-base probe/queue/runtime, fixed watch, claim 진단, native pending, source 연속성, scanner bridge/scheduler, Main-only retirement.
- 확장 검증의 최초 실패 중 2개는 승인된 long3과 달리 long2를 가정한 오래된 테스트였다. 테스트 기대값만 현 계약에 맞췄다. 나머지 3개는 worktree에 없던 pinned 원천 때문이었다. 필요한 5개 파일만 원본 해시와 동일하게 복사해 검증했으며 live data를 symlink하거나 수정하지 않았다.
- 최신 부모48968ade9 위 최종 통합 검증은 위729개와 artifact freshness·admin 알림 계약을 포함해 **1,016개 PASS**였다.
- Python compile, `git diff --check`, 현재 checklist print-only parser를 검증했다. 외부 Project/Calendar 동기화는 실행하지 않는다.
- 외부 HTTP·provider·broker 호출, 실제 주문 경로 재생, 배포·재기동은 미실행이다. 최종 통합 검증의 기존 deprecation warning5개(pandas1개, FIFO 경계 테스트의 multi-threaded fork4개)는 테스트 성공과 별도로 남는다.
- [회귀 원본](/home/ubuntu/KORStockScan/tmp/nonfixed-handoff-implementation-20261016-1330/baseline-regression.txt), [표적 JUnit](/home/ubuntu/KORStockScan/tmp/nonfixed-handoff-implementation-20261016-1330/targeted-junit.xml), [최종 통합 JUnit](/home/ubuntu/KORStockScan/tmp/nonfixed-handoff-implementation-20261016-1330/final-integrated-junit.xml), [격리 원천 해시](/home/ubuntu/KORStockScan/tmp/nonfixed-handoff-implementation-20261016-1330/isolated-fixture-sources.json).

배포 후에는 같은 native signal/physical lease의 `WATCHING` 확정 → 원 claim 1회 인수 → 정상 AI 평가 경로를 실제 PID에서 확인한다. 등록 성공·단위 테스트·선택본만으로 제출/체결을 완료 처리하지 않는다. 신호 미발생은 pending으로 남기고 안전 guard를 우회하지 않는다.
