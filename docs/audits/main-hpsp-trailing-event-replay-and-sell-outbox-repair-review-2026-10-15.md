# HPSP trailing 고점 재생·SELL outbox 코드 수리 리뷰 — 2026-10-15

판정: 요청 범위의 구현·리뷰·보완·재리뷰와 표적 검증을 완료했다. 사용자 추가 승인에 따라 `06deaab3453edcb66e493098f9128651f53b928f`를 통합한 `451b6c1ec84fafa563d95381e95c814ac2b2b18b`를 배포·재기동했고 실제 PID 소비와 HPSP outbox의 정상 복구를 확인했다. 새 포지션의 고점 재생·원천 복구 자연 수용과 실제 비용 정산은 OPEN이다.

## 범위와 원본 증거

- 사용자 지시: HPSP의 `event_peak_exceeds_trusted_peak` 결함 및 14:01:17 `log_scanner UNKNOWN(13)` 경보의 원인을 수정하고 리뷰·보완을 반복한다.
- 운영 기준: selected commit `bb4808c77087231b072efbd3ea12271fbb3889c6`, Main PID `2039852`, target `49293`, symbol `403870`. 기존 배포본은 수리 전 코드다.
- 13:33:29 quote sequence `7229`에서 실제 0B 가격은 `50400,50400,50500,50400`이었다. 최신 체결가 기반 고점 `50400`보다 정상 체결 묶음의 고점 `50500`이 커서 재생을 버렸다. 실패 경로는 그 고점을 상태에 저장하고, 성공 뒤에도 결손 표시를 남겼다.
- HPSP SELL `0043525`, execution `61455`는 13:59:04에 21주 전량 종결됐다. 이후 반복 오류는 동일 `a94be1ffcd52a869be3d6440de2b6bb2ed2d0b9270e5b1cac5995789c8259cc2` outbox leg의 ACK 실패다. 추가 주문 실패나 추가 매도 건수로 합산하지 않는다.
- [원본 결함 평가](../../tmp/hpsp-exit-monitor-20261015-1356/gap-assessment.json), [동결 journal 및 수정 전 재현](../../tmp/hpsp-exit-repair-20261015/outbox-before-reproduction.json). 원본 journal SHA256는 `0b2a7f7bdad1b517ca0934f1b72d62769b89eb7e895db37e0d7c45ea42d2bf7f`다.

## 구현과 리뷰 보완

1. `trailing_mechanical_strength.validate_replay_trade_peak`가 기존 동일 route/transport 0B 영수증의 가격·시각·연속 sequence와 선언 고점을 검증한다. replay는 정상 체결 고점을 반영하며 0D bid를 체결 고점으로 승격하지 않는다. 전체 묶음 검증 전에는 고점·cursor·first crossing을 확정하지 않는다.
2. 이벤트 상태를 position, 평균 매수가, item/transport/route/market에 결속한다. 실패 뒤 새 기준 호가를 잡고 다음 완전한 묶음에서 현재 결손 표시를 해제한다. 최초/최근 사유와 횟수는 유지하며, 누락 구간을 복구한 것으로 합성하지 않는다. fast pre-arm, fast, normal 평가가 검증된 고점을 직접 소비한다.
3. 재리뷰에서 장후 consumer의 기존 `max(previous_peak, trade_peak, bid)` 계약을 확인했다. 새 `verified_0b_only_v1` 재생은 체결 고점만 검증하고, 계약 표식이 없는 과거 행은 원래 방식으로 읽는다. 알 수 없는 계약은 실패 처리한다. 과거 원천은 수정하지 않는다.
4. 고정 감시의 동결 leg에는 scanner promotion이 없고 실제 진입 trace `analyze_target:403870:1792038802347:4a778b1f`가 있다. 별도 `native_entry_sell_receipt_v1` ACK로 원 record/symbol/trace/수신시각과 모든 동결 필드의 완전 일치를 확인한다. scanner lifecycle/attempt 또는 새로운 현재 EXIT AI 판단을 만들지 않는다. 기존 scanner ACK 검증은 유지한다.
5. 실제 journal의 `broker_execution_provenance_complete=false`를 수정 후 재현에도 그대로 보존했다. 원천 결손과 실제 비용 미확정은 custody ACK와 분리한다. 로그를 숨기거나 UNKNOWN 분류만 바꾸지 않았다.

## 검증

- [실제 sequence 7229 수정 후 재현](../../tmp/hpsp-exit-repair-20261015/peak-after-reproduction.json): 정상 체결 고점 `50500` 반영, replay 1건, current gap false.
- [동결 SELL leg 수정 후 재현](../../tmp/hpsp-exit-repair-20261015/outbox-after-reproduction.json): 원 leg 변경 없이 ACK 성공. scanner identity 합성 없음, 원 broker provenance 결손 유지. 모두 메모리 내 emit 대체를 사용했으며 live journal·DB·broker에 쓰지 않았다.
- 관련 7개 모듈 pytest **377 passed**: 고점 묶음/first crossing/실패 후 복구/partial-fill 평균가 rebase/transport 변경, stale·미래시각·sequence 결손 차단, fast·normal exit, native·scanner receipt 및 공용 source-recovery 회귀. [검증 로그](../../tmp/hpsp-exit-repair-20261015/pytest-final.log).
- 변경 Python compile 및 `git diff --check` 통과. [Ruff F/E9 비교](../../tmp/hpsp-exit-repair-20261015/lint-comparison.json): 신규 finding 0. 기존 handler 17건·receipt 5건은 HEAD와 동일한 범위 밖 이슈이며 전체 lint clean으로 보고하지 않는다.
- 재리뷰 후 본 수리 범위의 미해결 코드 finding 0. 공용 handler 및 체크리스트의 별도 완료봉 원천 복구 변경과 사용자 문서 변경을 보존했다.
- source/test는 기존 `src/engine/scalping`, 기존 runtime owner 및 `src/tests`에만 수정했다. engine root 새 모듈 없음. Kiwoom 요청·응답/FID parser, 인증·REG/REMOVE·주문 API 계약 변경 없음. shell 변경이 없어 bash 검증은 해당 없음.

## 후속 수용과 권한

### 사용자 승인 통합 배포 — 14:15 이후

사용자는 추가 코드 리뷰·보완 후 배포·재기동과 `06deaab3453edcb66e493098f9128651f53b928f`의 통합을 명시했다. 기준은 실제 선택본 `bb4808c77`이며, 작업공간 HEAD로 운영본을 덮어쓰지 않는다. 기존 운영본의 aftermarket eligibility 및 후속 배포/문서/정책 수리를 보존하고 HPSP 수정과 지정 커밋의 source recovery 함수·시험만 통합한다. 변경 consumer의 원 PREOPEN→후보 exact source pair와 rising_missed/holding_vote의 새 코드 세대 fixture를 검증한 뒤 기존 ordered 전환으로 진행한다. 배포 전 source 계약 검증과 배포/PID/자연 수용 결과는 `tmp/hpsp-integrated-deploy-20261015/`의 영수증으로 구분한다. 아래 미실행 문장은 최초 코드 수리 시점의 기록이며, 후속 실제 결과가 게시되기 전까지 완료를 뜻하지 않는다.

최초 코드 수리 시점에는 기존 PID를 유지했으며 live journal·DB·broker를 수정하지 않았다. 아래 실제 적용은 후속 사용자 승인에 따른 정상 ordered 전환과 시작 복구다. 수동 journal ACK·삭제 또는 추가 주문·취소로 복구를 만들지 않았다.

### 통합 리뷰·배포·시작 복구 영수증

- 통합본은 실제 운영 기준 `bb4808c77`과 지정 `06deaab3453edcb66e493098f9128651f53b928f`를 두 parent로 가진다. [통합 리뷰](../../tmp/hpsp-integrated-deploy-20261015/integration-review.json)는 지정 source recovery 함수의 정확한 일치, 기존 aftermarket guard 보존, workspace index 보존과 변경 함수 범위를 확인했다. 원 작업공간의 별도 연구 문서와 operator manual exclusion을 보존했다.
- 통합본 pytest **1,664 passed**와 배포 계약 **216 passed**. 변경된 rising_missed·holding_vote 코드 세대의 독립 fixture **86+91 passed**는 네트워크 차단·원 보고서/정책 보존 조건에서 검증했다. [본체 회귀](../../tmp/hpsp-integrated-deploy-20261015/candidate-tests.log), [배포 계약](../../tmp/hpsp-integrated-deploy-20261015/deployment-contract-tests.log), [배포 전 원천 계약](../../tmp/hpsp-integrated-deploy-20261015/preflight.json). 본체 경고1건과 앞서 기록한 기존 lint finding은 별도이며 전체 lint clean으로 표시하지 않는다.
- 기존 PID `2039852`와 supervisor의 정상 종료는 **14:25:27**, ordered 전환 완료는 **14:28:02**다. 새 Main **PID `2276473` / start ticks `10594101`**, cwd는 `/home/ubuntu/KORStockScan-runtime-releases/hpsp-peak-outbox-source-recovery-20261015-v1/src`다. [전환 영수증](../../data/runtime/release_transitions/2026-10-15/451b6c1ec84fafa563d95381e95c814ac2b2b18b/status.json), [실제 PID 소비](../../data/runtime/release_transitions/2026-10-15/451b6c1ec84fafa563d95381e95c814ac2b2b18b/starting-intraday_release_handoff.log), [bootstrap 소비](../../data/runtime/release_transitions/2026-10-15/451b6c1ec84fafa563d95381e95c814ac2b2b18b/starting-runtime_policy_bootstrap.log)는 PASS다.
- Main 정책 bundle `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`, 원 bootstrap manifest/env와 manual exclusion 파일 bytes를 유지했다. 새 WS producer가 같은 PID/start/commit으로 연결됐으며 completed-bar writer loss·projection error는 0이다. 계좌의 정규 KRX+NXT 읽기에서 inventory_complete/open_orders_verified가 참이고 미체결0을 확인했다. 추가 provider 평가나 검증용 주문은 만들지 않았다.
- **14:28:00.554470**에 시작 복구가 원 record `49293`의 `sell_completed`를 정확히1건 ACK했다. 원 주문 `0043525`, 체결 `61455`, 수량21, 원 수신시각 `13:59:04.110963+09:00`, native entry trace를 유지한 채 journal을 정상 종결했다. 원 journal 동결본/hash는 보존했다. drain 이후 HPSP 주문 registry 추가0이며 receipt/sync 오류 증가0이다. [적용 후 검증](../../tmp/hpsp-integrated-deploy-20261015/postdeploy-verification.json). 이는 원 매도의 attribution 종결이며 새 매도·새 손익 표본이 아니다. `broker_execution_provenance_complete=false`, 실제 비용 `cost_source_unavailable`도 유지했다.
- 14:30:19 첫 새 PID 탐지기의 `UNKNOWN(34)`는 이전 탐지 이후 drain 전 쌓인 receipt33건·sync1건이다. 원 오류 파일 inode/offset이 유지되고 drain 이후 증가0이므로 새 실행 오류와 분리한다. [첫 탐지 원본](../../tmp/hpsp-integrated-deploy-20261015/detector-2026-10-15T143019_0900.json)을 보존하며 다음 정규 탐지 소비를 별도 확인한다.
- **14:31:43** 새 정규 탐지에서 `log_scanner=pass`·새 오류0·`process_health=pass`를 확인했다. 이 시점의 전체 severity는 CPU compute busy95.68%로 fail이며 기존 report 경고도 남는다. 동시에 별도 누적 연구 parity 작업이 실행 중인 프로세스 관찰을 보존하되 CPU 원인을 이번 코드나 특정 작업으로 확정하지 않는다. 이 검증의 PASS 범위는 통합 코드 배포·동일 정책 실제 소비·HPSP attribution 복구이며 전체 시스템 green 또는 경제성 수용이 아니다.
- **14:33:00** 후속 탐지에서는 fail0, 전체 warning이며 CPU93.31% warning·기존 report 경고를 유지한다. `log_scanner/process_health=pass`다. 새 정규 observer `ace8c9ef2cb3473cb1eaa5752bf7df24`는 새 PID/start/commit으로14:32:28 게시됐고, 탐지기가 같은 run과 `observation_health`를 재계산 일치로 소비했다. generation/current actor/freshness는 검증됐지만 분모·원천 미완전으로 `warning_pending`, `semantic_status=partial`, `full_coverage_proven=false`다. 이를 자연 주문·신규 고점 복구·성과 성공으로 확장하지 않는다. [최종 적용 후 검증](../../tmp/hpsp-integrated-deploy-20261015/postdeploy-verification.json).
- 14:33:16 이후 다른 종목 `196170`, record `49268`에서 정상 Main BUY `0046833/0046834` 각1주가 자연 접수·체결됐다. HPSP 복구의 중복 주문과 분리한다. 검증 스크립트의 초기 전체 registry 추가0 가정은 이 정상 거래로 거짓이 됐으므로 [초기 판정](../../tmp/hpsp-integrated-deploy-20261015/verification-before-natural-trade-scope-correction.json)을 보존하고 HPSP symbol/owner의 중복 여부로 검사 범위를 명확히 했다. 실제 새 거래·provider를 검증 스크립트가 생성하거나 중단하지 않았다.

기존 `HoldingProfitExitSourceContractRepair`와 `AuxiliaryCircuitRecoveryRepair1012`의 자연 수용/경제성 Acceptance를 유지한다. 다음 새 포지션에서 검증된 0B 고점·실패 후 복구, source 실패→fresh source/완료봉→새 claim/평가/Main disposition을 확인한다. 기존 `holding_exit_sentinel`의 offset-naive/aware datetime 정렬 실패와 stale 경고는 이전 선택본에서도 발생한 별도 report producer 결함이며, 원 로그와 이 owner의 원천 수리 범위에 남긴다. 다음 조치는 producer 시간 정규화의 원 시각·as-of 보존 검토와 mixed-timezone 회귀 후 정상 정규 게시 확인이다. 원 경고·장후 cutoff 초과 이력 또는 비용 원천 부재를 이번 코드 적용으로 해소했다고 표시하지 않는다.
