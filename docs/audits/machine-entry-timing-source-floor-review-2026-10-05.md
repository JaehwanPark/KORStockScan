# 기계진입 타이밍 원천 보고서 허용 하한 점검 및 리뷰

## 결정과 범위

사용자 요청에 따라 6~7월 원천 미소비를 확인한 뒤 이 소비자의 원천 보고서 최소 날짜를 `2026-08-01`로 변경했다. 공통 생산자/기존 정책 provenance의 `clean_tuning_baseline_date=2026-06-05`와 소비자 허용 하한을 구분한다. Main 기계/보조 판정 생성기나 타 family의 날짜 경계를 변경한 작업이 아니다.

코드 소유 위치는 기존 `src/engine/automation/machine_entry_timing_tuning.py`, 완료 이력 reader는 기존 `src/engine/monitoring/machine_entry_confirmation_study.py`다. 회귀는 기존 `src/tests` 모듈을 보완했다. 새 engine-root 모듈·새 runtime owner는 없다.

## 직접 대사한 원천

대상은 공식 `machine_entry_timing_tuning_2026-10-02.json`의 `source_artifacts`, 현재 attribution 로더 결과, 진입 앵커 시각과 embedded native contract 날짜, 완료 결과 복원 이력이다.

| 월 | 원천 보고서 | 진입 입력 앵커 | 튜닝 적격 앵커 |
| --- | ---: | ---: | ---: |
| 6~7월 | 0 | 0 | 0 |
| 8월 | 11 | 28 | 26 |
| 9월 | 20 | 74 | 58 |
| 10월 | 2 | 1 | 1 |

33개 원천의 경로·SHA는 공식 보고서 기록과 모두 일치했다. 실제 소비 앵커 103개는 모두 보고서 날짜와 같은 날이며 6~7월 시각은 없다. embedded native 계약 4개는 9/21~9/23이고 최신 완료 이력 root는 0개다. 저장된 timing 보고서 이력 파일도 8~10월뿐이었다. 따라서 현재 자료에서는 6~7월 원천을 소비하지 않는다고 확인했다. 8월 원천은 실제 후보 계산 입력으로 남는다.

## 구현과 리뷰 보완

1. attribution `_source_reports`는 `max(CLEAN_BASELINE_DATE, MIN_SOURCE_REPORT_DATE)`부터 target date까지만 JSON을 읽는다. 이전/미래 날짜 파일은 source-quality 오류로 오인하지 않고 읽기 전에 제외한다. PREOPEN rebound 재검증도 같은 함수를 호출한다.
2. 리뷰 중 별도 완료 이력 reader에 상한만 있음을 확인했다. 실제 `build_report` 호출이 동일 하한을 전달하도록 보완했다. 유효 날짜 이력의 hash/identity/knowledge-date 검증과 custody는 보존한다.
3. 신규 JSON/Markdown은 `minimum_source_report_date`를 표시하고 metric window도 해당 하한을 명시한다. 기존 생산자의6/5 품질 계약, 적용 정책 schema, 비용·수량·주문·동일 stage guard는 그대로 검증한다.
4. 기존 양성 시나리오가7월까지 역산하던 테스트 표본을8월 이후로 옮겼다.20일 fixed-delay 및28일 model/calibration/holdout 계약과 정책 로더 검증을 유지하고9/4 이후 source ownership 계약을 fixture에 명시했다.
5. rebound 테스트에서 설치된 실제 timing-policy receipt를 읽는 격리 결함을 확인했다(`staged_timing_policy_invalid:entry_timing_source_report_path_invalid`). fixture를 임시 timing-policy 디렉터리로 격리했다. 운영 receipt나 runtime 코드를 고쳐 테스트를 통과시키지 않았다.

## 검증 결과

- `test_machine_entry_timing_tuning.py`, `test_machine_confirmation_study.py`, `test_machine_rebound_reentry.py`: **130 PASS**. 이전/미래 파일을 열지 않는 반례,8/1 포함, 과거 target의 valid-empty, 공통 품질 계약/owner 하한 분리, 허용 날짜의 손상 이력 거부, 원천→선정→exact-date reader 및 PREOPEN 재검증을 포함한다.
- 실제10/2 원천에6/5와8/1 하한을 각각 적용한 격리 계산: 입력 경로/SHA33개 및37cohort 계산·선정 결과 동일. 생성시각과 하한 metadata만 비교에서 제외했다. `source_quality_blocked`, `baseline_immediate_entry_carry_forward`, `runtime_winner=null` 유지.
- 공식10/2 보고서, 기존 timing runtime 정책 파일,10/6 Main 기계 정책·체크리스트 SHA 불변. 공식 보고서·runtime 정책 발행 없이 메모리 계산과 별도 증빙만 기록했다.
- 근거: [직접 대사·차등 영수증](../../tmp/machine-entry-timing-source-floor-20261005/inspection-and-differential.json). 최종 compile/diff/document parser 결과는 같은 디렉터리의 `validation.json`에 기록한다.

## 잔여 경계

작업본 수정 완료와 운영 릴리스 적용은 별도다. 이번 요청으로 배포·재기동·원천 삭제·전체 장후 재생성을 실행하지 않았다. 준비된10/6 정책의 bytes와 거래 권한은 바뀌지 않았으며, 날짜 하한 변경으로 기존 source-quality 결손이나 경제성 미선정을 해소했다고 주장하지 않는다.
