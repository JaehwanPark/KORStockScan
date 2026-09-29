# 장후 정책 전진 입력과 6~8월 raw 퇴역 점검 (2026-09-29)

## 결정

- 후속 정책 갱신의 첫 원천일은 `2026-09-30`이다. 선택되어 실제 소비되는 정책을 incumbent로 사용하고, 이전 원천의 누적 성과를 새 후보의 표본·비교·승계 근거로 사용하지 않는다. 과거 대상일의 재현은 기존 `2026-06-05` 계약으로 유지한다.
- 새 표본이 없거나 source/terminal/cost 영수증이 부족하면 후보를 보류한다. 결손을 0 성과로 기록하지 않는다.
- 6~8월 raw 파일 삭제는 아직 실행하지 않았다. 안전 조건을 확인한 뒤 해당 파일만 제거한다.

## 확인한 장후 입력 경로

| 생산 경로 | 기존 입력 | 전진 구간 처리 |
| --- | --- | --- |
| `ai_action_outcome_calibration`, `compact_auxiliary_paired_replay` | 과거 paired report, outcome label, machine payload, 보조 정책 계획 | 파일명 날짜를 먼저 검사하고 새 원천만 읽는다. compact 후보 계획도 전진 구간별 파일에 고정한다. |
| `entry_split_order_plan`, `scale_in_split_order_plan` | 누적 원천·보고서·DB 체결, 이전 상태 | 새 날짜의 원천·체결과 같은 구간의 이전 상태만 후보 경제성에 사용한다. incumbent 정책·주문 custody 검증은 유지한다. |
| `pre_submit_delay_tuning`, `entry_cancel_wait_tuning`, `low_price_two_leg_tuning`, `rising_missed_*`, `widget_collector_expansion_recommendation` | 과거 partition·보고서·cache·replay | 신규 갱신 입력을 `policy_refresh_start_date` 이상으로 제한한다. |
| `low_price_two_leg_expanded_candidate_research` | 6월부터의 전체 기간과 과거 cache | 전진 표본 계약이 없어 장후 단계 OFF, 새 날짜 직접 실행도 거부한다. |

원천 품질 감사, 당일 outcome label 생산, 선택 정책 조회와 미종결 주문 확인은 동일한 학습 표본이 아니다. 각 경로의 날짜·custody 용도를 구분하며 원자료 삭제 전 소비자를 재대사한다.

## 2026-09-29 19:20 KST 점검 증거

| 경로 | 6월 | 7월 | 8월 | 분류 |
| --- | ---: | ---: | ---: | --- |
| `data/pipeline_events` | 20개, 1.527 GiB | 23개, 1.532 GiB | 26개, 3.606 GiB | 원천 JSONL gzip 포함 |
| `data/analytics` | 48개, 2.859 GiB | 53개, 2.706 GiB | 53개, 8.897 GiB | Parquet 등 파생 분석 자료 |
| `data/ai_decision_payloads` | 0개 | 16개, 0.005 GiB | 40개, 0.126 GiB | AI 원천 payload |
| `data/source_quality` | 33개, 0.120 GiB | 44개, 0.252 GiB | 83개, 3.011 GiB | exclusion 및 출처 검증 자료 포함 |
| `data/threshold_cycle` | 771개, 0.285 GiB | 1,029개, 0.987 GiB | 1,634개, 0.944 GiB | 정책·승계·custody 포함, raw 일괄 삭제 대상 아님 |

월별 개수는 경로 또는 파일명에 해당 `YYYY-MM`이 들어간 일반 파일의 재귀 집계다. `pipeline_events`의 archive receipt 12개는 모두 9월 파일이며 6~8월 파일에는 해당 receipt가 없다. Parquet 존재만으로 JSONL과의 바이트·행·계약 동등성이 증명되지는 않는다.

`data/runtime/runtime_release_selection.json`이 선택한 릴리스는 `samsung-main-route-restore-20260929-45bc11e1` (`45bc11e19ccdc75278bb6d263c16a4bcf5937461`)이다. Main PID `1454744`의 cwd도 이 릴리스 `src`였다. 크론의 `THRESHOLD_CYCLE_POSTCLOSE`는 평일 20:10에 `deploy/run_runtime_release.sh postclose`를 호출한다. 이 점검 시 장후 프로세스는 실행 중이지 않았으며, 작업공간의 새 로더는 선택 릴리스에 반영되지 않았다.

## 삭제 전 남은 확인

1. 수정 코드의 리뷰·검증을 닫고, 장후 소비 릴리스가 전진 입력 계약을 실제로 선택했는지 확인한다. 선택 경로, 크론, 실제 장후 프로세스와 이전/rollback 릴리스를 각각 대사한다.
2. 6~8월 raw별 독립 보관본 또는 무손실 투영과 복원 영수증을 확인하고, source-quality exclusion·주문/custody·미종결 이력·열린 FD 의존성을 대사한다. 검증되지 않은 파일은 보존한다.
3. 검증된 파일만 경로·크기·SHA-256·삭제 시각을 영수증에 남겨 제거하고, 이후 장후 source gap과 custody 회귀를 확인한다. 재계산으로 과거 수익을 새 정책의 성과로 승격하지 않는다.
