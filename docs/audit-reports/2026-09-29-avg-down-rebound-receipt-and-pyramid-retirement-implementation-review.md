# AVG_DOWN 공통 반등·정확 BUY 영수증·PYRAMID 퇴역 구현 리뷰 — 2026-09-29

## 판정과 경계

[구현계획](../proposals/avg-down-shared-rebound-receipt-and-pyramid-retirement-implementation-plan-2026-09-28.md)의 A1–A4 코드를 작업본에 구현하고 재검토했다. 코드·표적 회귀는 통과했다. 작업본의 선택 release·실제 Main PID 소비, 첫 자연 반등·투표·ADD, 완료·정확 비용과 증분 순익은 별도 수용 항목이다. 정책·env·provider·threshold·주문·재기동은 변경하지 않았다. [9/29 체크리스트](../checklists/2026-09-29-stage2-todo-checklist.md)의 `[AvgDownSharedReboundReceiptClosure0928]`가 후속 수용 owner다.

S15와 VCP의 신규 진입은 이미 제거됐다. 이번 변경은 두 경로를 되살리지 않는다. `sniper_s15_fast_track.py`의 잔여 코드는 기존 보유·미결 주문의 custody 복구와 SELL·정산에 쓰이며, VCP 신규 진입은 `kiwoom_sniper_v2.py`의 퇴역 guard가 거절한다. 삭제된 S15 신규 후보 함수를 호출하던 낡은 테스트를 제거했다. 역사적 S15/VCP 장부나 청산 코드는 삭제하지 않았다.

## 구현과 원천 대사

| 단계 | 작업본 소비자와 검증 경계 |
| --- | --- |
| 사전검사 | `ai_engine_openai.py`가 기존 `ai_input_preflight`의 대표 blocker·범주·최대 8개 blocker/결손 원천과 snapshot 시계를 제한된 필드로 반환한다. `sniper_state_handlers.py`가 같은 보유의 `avg_down_shared_rebound_blocked`에 기록한다. 유효 기계 `BLOCK`과 원천 결손은 별도 사유로 남긴다. 후보·threshold·provider 호출은 변경하지 않았다. |
| 최초 BUY 식별자 | `sniper_execution_receipts.py`가 수락한 broker BUY 체결의 주문·체결 맵을 보유 ID별 작은 원자적 sidecar에 즉시 기록한다. `kiwoom_sniper_v2.py`는 DB/broker 보유 복원 뒤, 보유 투표 전에 ID·종목·매수시각·수량·가격·체결 identity를 검증해 복원한다. 결손·충돌·기록 실패 시 ADD 투표와 주문을 차단하고 SELL custody는 유지한다. |
| 기존 보유 복원 | 새 sidecar가 없는 보유는 기존 보유 건별 path-vote 원장에서 정확한 BUY 주문·체결 leg가 있고 DB 수량·시각·identity가 일치할 때만 1회 backfill한다. 과거 ADD/미결이 섞인 건은 판별하지 않고 차단한다. 일별 거대 raw 전량 startup 재생은 없다. |
| 장후 결속 | `sniper_trade_review_report.py`가 동일 보유 ID의 blocked→signal→PASS vote→decision/episode→제출 주문→정확 체결→완료·비용을 진단 행으로 연결한다. 미결속·미청산·비용 결손을 남기고 동일 보유 순익을 ADD 결정마다 중복 합산하지 않는다. ADD의 증분 효과는 짝지은 no-ADD 비교 전까지 `unidentified_without_paired_no_add`다. |
| PYRAMID 퇴역 | `sniper_scale_in.py`의 도달 불가능한 신규 판단·품질·동적 수량 구현을 제거했다. 공개 호환 evaluator와 직접 주문·수량 guard는 영구 차단을 유지한다. 기존 pending PYRAMID 체결·취소·SELL·정산 분기는 보존했다. 공통 AVG_DOWN 가격 안전장치에 붙은 기존 PYRAMID 명칭은 안전성 동등성 없이 제거하지 않았다. |

대우건설 `047040`, 보유 `48376`의 9/28 기존 path-vote 원장에는 최초 주문 `0029186`, 체결 `131176`, 1주가 기록돼 있다. 원본 변경 없이 임시 디렉터리 복사본으로 복원했을 때 `restored_from_path_vote`와 동일 BUY identity가 생성됐다. 이 검증은 **복원 코드의 재생 결과**이며 현행 Main PID 복원 성공 영수증이 아니다. 기존 정규화 체결 원천에는 계좌 식별자 전체가 없으므로 이 건의 계좌 수준 대사는 별도 broker/원장 근거 없이는 주장하지 않는다. 당시 유효 ADD 투표·주문·체결이 없었던 것은 0원 효과나 무효 전략 판정이 아니다.

## 리뷰·검증

- 첫 검토에서 sidecar 결손 시 기존 보유의 exact BUY 원천 복원이 빠진 점을 발견해, 크기를 제한한 기존 path-vote 원장 backfill을 추가하고 충돌·과거 ADD·pending 차단 회귀를 넣었다.
- 확장 회귀에서 삭제된 S15 신규 후보 함수를 호출하던 테스트 1건이 실패했다. 신규 진입이 퇴역했다는 현재 계약을 확인하고 그 테스트·전용 fixture를 제거했다. 두 번째 검토에서 중복 import를 정리했다.
- 후속 재검토에서 체결 콜백의 KST 시간대 포함 `buy_time`과 DB의 시간대 없는 `DateTime`이 같은 시각이어도 불일치해 재기동 ADD를 막는 결함을 재현·수정했다. 저장·복원 양쪽을 KST 시각으로 정규화하고 기존 시간대 포함 sidecar도 읽는다. 손상된 과거 path-vote 원장의 필드형 오류가 startup을 중단할 수 있던 경로는 원천 결손으로 차단하도록 고쳤다. 기존 원장 크기 계약(16 MiB)과 복원 상한도 일치시켰다.
- 이전 날짜 보유 건의 반등 차단 관측이 다음 날 청산 보고서에서 사라지던 결함은 보유 건별 사유·횟수 요약으로 이월한다. 옛 snapshot에 요약이 없으면 결손으로 표시하되, 그 결손만으로 물타기 관측 건수를 만들지 않는다. 과거 snapshot 조회는 **청산된 보유 건**의 기존 이월 경로에 한정해 열린 장기 보유의 매일 반복 조회를 피한다. ADD 주문 2주 중 체결 1주 같은 부분체결은 full fill과 다른 상태로 보고하고, 제출량을 넘는 체결은 lineage gap으로 남긴다.
- 영향을 받는 9개 테스트 파일에서 **1,916 passed**, pandas_ta의 기존 deprecation 경고 1건. BUY sidecar round-trip/변조/재기동, 시간대 포함 시각과 DB 시각 일치, 손상 원장 차단, 이전 날짜 차단 횟수 이월, 부분체결 분리, source blocker, 장후 ID·비용 결속, PYRAMID 신규 차단·기존 pending, S15 custody 복구와 VCP guard가 포함됐다.
- 임시 파일시스템에서 sidecar 100회 기록 약 618 ms(건당 약 6.2 ms), 100회 복원 약 9 ms, 파일 최대 약 516 B였다. 이는 로컬 측정이며 실제 Main loop 성능·PID 적용 증거가 아니다.
- 1,000개 동일 차단 관측의 열린 보유 projection 요약은 1행·138 B, 로컬 처리 약 0.35 ms였다. 전날 차단 이벤트 1,000개를 다음 날 timeline에 복사하지 않는다.
- 변경 Python의 `py_compile`, 문서 print-only parser(24개 작업, 이 stable ID의 현행 owner 1개), 연결 문서 경로·권한 경계, `git diff --check`가 통과했다.

## 남은 수용

작업본은 현재 Main PID의 immutable release가 아니다. 선택 release와 실제 PID, 당일 정책 bundle 및 첫 자연 기회 영수증을 대사한 뒤에야 운영 소비를 판정한다. 자연 원천이 없으면 `natural_first_use_pending`이고, 완료·정확 비용·동일 조건 no-ADD 비교가 없으면 증분 경제성은 `null`이다. 수량·분할 실행 효과는 별도 `[DirectFamilySourceRepairScaleInSplit]` owner가 맡는다.
