# 10/14 EOD·장후 전수 점검과 10/15 기동 준비

현재 판정: 운영 실패 복구 중; 분석/정책·준비의 최종 종결은 아직 미확정. Source/publication `2026-10-14`, effective `2026-10-15`를 자정 이후에도 유지한다. 이 기록은 종료 시 최신 receipts로 갱신한다.

## 확정 원천·실행

EOD는 20:05:04 시작, 20:55:53 `completed_with_warnings` 종료했다. PostgreSQL 최신일 10/14·2,622행, bulk insert 175,480행이다. 결손 `266690`, `468670`, `486510`은 OHLCV 부족으로 유지한다. 원천 감사는 342,078 event·식별 결함 15행 제외·hard contract gap 0·tuning input allowed이다. warning/unknown-token 및 attempt conservation 결손은 성공/경제성0으로 바꾸지 않는다.

20:10 원 Main/controller/tuning과 20:50 archive는 정확일자 EOD를 기다렸다. Archive는 20:56:02 DONE이다. 설치 Main stop을 실제 실행한 owner는 원 postclose wrapper이며 수동 기동/재기동은 수행하지 않는다. 원 run `76c3731bfb234bb4ba13e47e177165e1`/`7c517c920`은 21:52:49 strict exit2로 실패했다. 진행 중 승인된 선택은 `17aac0dae`→`43a79e569`로 변했으며 원 run을 새 release로 relabel하지 않는다. 실제 PID 1263868/4167445는 `43a79e569`를 소비했으나 현재는 장후 stop 상태다.

## Native stage 상태

| Owner | 실행 | Native run | Terminal |
| --- | --- | --- | --- |
| legacy_machine_report | succeeded | `e44e7ae6b9354bef9109d77351b5c41a` | 2026-10-14T21:42:23.708372+09:00 |
| main_auxiliary_policy | failed | `b27de35817d446428c78e7481910cbe7` | 2026-10-14T21:37:30.143877+09:00 |
| main_machine_policy | succeeded | `a02a0f5dc72d4096b2809be80732d2fd` | 2026-10-14T21:33:38.714443+09:00 |
| main_stop_confirmation | succeeded | `b11d125b4ce647cc95fa311f0d022560` | 2026-10-14T21:50:43.923136+09:00 |
| outcome_labels | succeeded | `f98cb4b2f10444148f3988f6b75e79bc` | 2026-10-14T21:07:49.011344+09:00 |
| pre_submit_delay | succeeded | `26bbdff170b140ba8f1e4ea47b7e2b79` | 2026-10-14T21:07:21.044939+09:00 |

기계·legacy의 원 root mismatch 실패와 보조의 신규 membership 오류는 [구현/복구 리뷰](postclose-auxiliary-membership-and-final-resume-recovery-review-2026-10-14.md) 및 data/runtime/postclose_recovery/2026-10-14의 원 JSON/log로 보존한다. 완료 계산·원 정책·budget ledger·불변 원천은 보존하며 earliest failed producer→직접 downstream→마지막 consumer만 재개한다.

## 분석·경제성·소비

10/14 economic reference는 병행 Main owner가21:34:12 생성한 `verified=true/status=pass`이며 source-only producer 조회는 기존 검증 원천을 재사용했다. 원 계좌별 broker receipt/비용·실제 주문/체결/COMPLETED 손익·CF를 분리한다. 경제성 결손은 null이며 분석 종료나 새 정책 준비를 실현순익으로 보고하지 않는다. Family별 마지막 결과 및 native command census는 종결 후 같은 source generation으로 대조한다.

약세 연구의 설치 code/calendar는 현재 release에서 검증됐고21:40 자연 실행은 `regular_postclose_or_eod_active`로 유예했다. 과거10/13 source-gap 결과를 오늘 결과로 재사용하지 않는다. 실제 다음 야간 attempt→누적→notification disposition을 별도 확인한다.

## 다음 거래일

설치 예약은10/15 05:35 finalization,07:35 PREOPEN,07:55 Main start이다. 현행 지시문의05:00 표기와 설치05:35의 차이는 contract drift로 기록하며 실제 예약 기준으로 추적한다. Source14/target15의 current selected release·candidate/유효 carry·summary/controller/checklist·manifest/env/verify SHA가 맞는 `prepared_verified`를 검증해야 준비를 완료로 판단한다. 아직 이 계약은 종결 전이다. future PREOPEN/PID·자연 submit/fill/terminal/비용 후 성과는 `not_yet_due`이며 prepared와 별도다. startup hold는 없고 현재 Main은 stop 상태다.

기존 daily stable IDs와 원 Acceptance/History를 보존한다. 보고 결과를 위해 DONE·sample0·profit0·추가 live/EV 권한을 합성하지 않는다.
