# HPSP trailing 고점 재생·SELL outbox 코드 수리 리뷰 — 2026-10-15

판정: 요청 범위의 구현·리뷰·보완·재리뷰와 표적 검증을 완료했다. `code_review_closed`, `deployment_pending`, `natural_acceptance_pending`이다. 실행 중인 PID와 복구 journal은 변경하지 않았다.

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

현재 PID는 기존 코드이므로 반복 경보와 journal pending 해소를 주장하지 않는다. 배포·재기동, live journal 재생/ACK·삭제, 정책/env/lock, provider, 주문·취소는 실행하지 않았다. 이후 별도 승인된 적용에서 같은 동결 leg의 정확한 ACK·journal 종결·중복 주문 0, 새 자연 체결 묶음의 고점/복구 및 정상 탐지기 소비를 확인한다. 실제 broker 비용 정산과 비용 후 성과는 별도 미확정이다. 기존 `HoldingProfitExitSourceContractRepair` owner와 원 Acceptance를 유지한다.
