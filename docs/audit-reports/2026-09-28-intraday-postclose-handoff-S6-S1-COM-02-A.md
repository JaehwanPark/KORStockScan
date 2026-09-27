# S6 `S1-COM-02-A` — pipeline 원천·요약·첫 stage 세대 결속

실행일: **2026-09-28 KST**. 범위: [S1](2026-09-27-intraday-postclose-handoff-S1.md) `S1-COM-02-A`, [S5](2026-09-27-intraday-postclose-handoff-S5.md), [scanner reader S6](2026-09-27-intraday-postclose-handoff-S6-S1-COM-01-A.md). 판정: **fixture 코드 수리·리뷰 완료, 실제 9/23 재생성·자연 소비 미확인**. 이 작업은 작업본만 수정했고 정규 장후작업, PREOPEN, 배포, PID, 실주문·정책·서비스·provider·threshold를 변경하거나 실행하지 않았다.

## 원인과 수리

`src/utils/pipeline_event_logger.py`는 raw JSONL을 먼저 append한 뒤 `ProducerSummaryCompactor.submit()`을 호출한다. 기존 `pipeline_event_producer_summary_manifest`는 `shadow` 요약 event/row와 저장 크기만 기록했다. 첫 `pre_submit_delay` stage는 그 파일의 SHA를 입력 영수증에 묶었지만 raw 날짜·partition·논리 SHA·offset 및 원본/유효/제외/미관측 분모를 확인하지 않았다. 9/23 기존 manifest SHA `59ece8b1c9ee26ddb8289d4caf5d151eec0f35d1c73a268dd9f4ecbc288d27d3`와 stage input SHA 일치는 **manifest 이후** 연결만 증명한다. 9/23 raw 감사 374,864건과 `shadow` 요약 166,640 event/70,076 row는 다른 profile·단위다.

| 경로 | 수리·거절 기준 |
| --- | --- |
| raw base·late, plain·gzip → producer summary | 장후 `seal_producer_summary_source`가 같은 날짜의 논리 원천을 스트리밍해 SHA·decoded bytes·part별 논리 시작/끝 offset·물리 representation·원본/유효/제외/격리/미관측/중복 건수와 사유를 기록한다. profile별 stage 유효 event 수와 canonical evidence-hash 합을 요약 row의 수·identity와 대조한 뒤 manifest에 ledger를 봉인한다. malformed·잘못된 날짜는 식별해 격리하고, 다음 날짜에 방출된 late row는 해당 emission-date profile의 미관측으로 분리한다. 요약 대상 event 중 정확한 중복과 원천/요약 불일치는 거절한다. |
| manifest → 첫 `pre_submit_delay` stage | stage 시작 전 봉인과 ledger 검증을 요구한다. raw 부재·producer OFF/잘못된 profile·불일치·손상은 `deferred(exit=75, source_gap)`로 남겨 명령을 시작하지 않는다. 명시적으로 OFF인 stage는 기존 `off` 영수증을 유지한다. stage 영수증에 ledger SHA와 manifest 입력 SHA를 고정하고 실행 종료 후 두 세대를 다시 확인한다. 성공 영수증 재검증에도 같은 ledger가 필요하다. |
| 압축·재시도 | plain과 gzip의 해제 내용이 같으면 하나의 논리 part로 계산한다. 표현만 바뀐 경우 기존 manifest 세대를 보존한다. 내용·날짜·요약 본문 변경, 다른 late part의 후착, 부분 파일 및 동시 변경은 stale/invalid로 거절한다. valid-empty는 빈 raw와 **명시적 producer 증거**가 있을 때만 봉인한다. manifest가 없다는 사실만으로 빈 입력이나 OFF를 추정하지 않는다. |
| 장중 timing receipt | 장후 ledger가 manifest를 확장하기 전 producer manifest SHA를 ledger에 보존한다. timing reader는 그 SHA와 장중 health receipt를 대조한다. 봉인 때문에 이전 장중 측정이 허위 `missing_or_unbound`가 되는 회귀를 수정했다. |

9/23 원본 `pipeline_events_2026-09-23.jsonl.gz`(저장 437,234,985 bytes), 요약 JSONL(65,337,822 bytes), manifest(2,503 bytes), 기존 stage terminal은 읽기 전용 `stat`으로만 확인했다. **6.5 GB급 해제 원천을 이 작업에서 전수 재스캔하지 않았고 기존 영수증을 소급 수정하지 않았다.** 따라서 9/23의 실제 quarantine 11행을 이 ledger의 새 profile 건수로 옮겨 쓰지 않았다. 과거 terminal은 새 원천 ledger가 없는 상태 그대로이며 현재 코드가 이를 자연 성공으로 수용하지 않는다.

## 실패 회귀·리뷰·검증

- 구현 전 `seal_producer_summary_source` 부재 3건과 raw 부재 상태에서 첫 stage가 명령까지 진행하는 결손을 fixture로 실패 재현했다. 원천 2건→유효 1/제외 1, raw 3건→유효 1/격리 1/다음 날짜 late 1, 원천 drift·요약 재작성·중복·날짜 오류·plain/gzip 충돌·OFF·명시적 valid-empty를 검증했다. 같은 ledger의 성공 stage receipt와 실행 중 raw 변경 거절도 확인했다.
- 자가 리뷰에서 장후 봉인이 장중 timing health SHA를 끊는 문제를 발견했다. 실패 회귀를 추가한 뒤 preseal SHA 검증을 구현하고 재리뷰했다. 검토 범위의 남은 코드 결함은 0이다.
- 영향 pytest: `test_pipeline_event_logger.py`, `test_pipeline_event_summary.py`, `test_pipeline_event_verbosity_report.py`, `test_postclose_summary_handoff.py`, `test_pre_submit_delay_tuning.py` **215 passed** (최종 실행 결과는 아래 검증 명령으로 갱신). Python compile과 `git diff --check` 통과. wrapper 수정은 없어 `bash -n`/wrapper 계약 검사는 해당 없음.

## 잔여 수용 경계와 인계

이 코드는 작업본이며 선택 릴리스·PID 또는 실제 9/23 stage의 새 원천 세대 소비가 아니다. 장후 한 번의 전체 raw 스트리밍과 요약 읽기의 wall·CPU·RSS·I/O는 **S7**에서 승인된 고정 원천으로 측정하고 실제 raw 374,864와 stage/profile별 원본·격리·미관측 ledger를 대사한다. 새 자연 terminal→strict의 같은 세대 수용도 S7 대상이다. 릴리스 선택·PREOPEN·PID는 **S8**에 남긴다. `S5-FIN-05`는 다음 자연 source date 재현 조건부, S2 BUY·S3 SELL 및 나머지 S4 결손은 별도 S6 묶음이다.
