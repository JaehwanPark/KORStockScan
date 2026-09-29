# 장후 정책 전진 입력과 6~8월 raw 퇴역 점검 (2026-09-29)

## 결정

- 후속 정책 갱신의 첫 원천일은 `2026-09-29`이다. 선택되어 실제 소비되는 정책을 incumbent로 사용하고, 9/28 이전 원천의 누적 성과를 새 후보의 표본·비교·승계 근거로 사용하지 않는다. 오늘 장후 작업은 오늘 원천으로 실행한다.
- 새 표본이 없거나 source/terminal/cost 영수증이 부족하면 후보를 보류한다. 결손을 0 성과로 기록하지 않는다.
- 6~8월 원천 JSONL/압축 파일 2,030개를 삭제했다. 정책·주문·source-quality 영수증과 파생 분석 자료는 보존했다.

## 확인한 장후 입력 경로

| 생산 경로 | 기존 입력 | 전진 구간 처리 |
| --- | --- | --- |
| `ai_action_outcome_calibration`, `compact_auxiliary_paired_replay` | 과거 paired report, outcome label, machine payload, 보조 정책 계획 | 파일명 날짜를 먼저 검사하고 새 원천만 읽는다. compact 후보 계획도 전진 구간별 파일에 고정한다. |
| `entry_split_order_plan`, `scale_in_split_order_plan` | 누적 원천·보고서·DB 체결, 이전 상태 | 새 날짜의 원천·체결과 같은 구간의 이전 상태만 후보 경제성에 사용한다. incumbent 정책·주문 custody 검증은 유지한다. |
| `pre_submit_delay_tuning`, `entry_cancel_wait_tuning`, `low_price_two_leg_tuning`, `rising_missed_*`, `widget_collector_expansion_recommendation` | 과거 partition·보고서·cache·replay | 신규 갱신 입력을 `policy_refresh_start_date` 이상으로 제한한다. |
| `low_price_two_leg_expanded_candidate_research` | 6월부터의 전체 기간과 과거 cache | 전진 표본 계약이 없어 장후 단계 OFF, 새 날짜 직접 실행도 거부한다. |

원천 품질 감사, 당일 outcome label 생산, 선택 정책 조회와 미종결 주문 확인은 동일한 학습 표본이 아니다. 각 경로의 날짜·custody 용도를 구분하며 원자료 삭제 전 소비자를 재대사한다.

## 2026-09-29 19:20 KST 이전 점검 증거

| 경로 | 6월 | 7월 | 8월 | 분류 |
| --- | ---: | ---: | ---: | --- |
| `data/pipeline_events` | 20개, 1.527 GiB | 23개, 1.532 GiB | 26개, 3.606 GiB | 원천 JSONL gzip 포함 |
| `data/analytics` | 48개, 2.859 GiB | 53개, 2.706 GiB | 53개, 8.897 GiB | Parquet 등 파생 분석 자료 |
| `data/ai_decision_payloads` | 0개 | 16개, 0.005 GiB | 40개, 0.126 GiB | AI 원천 payload |
| `data/source_quality` | 33개, 0.120 GiB | 44개, 0.252 GiB | 83개, 3.011 GiB | exclusion 및 출처 검증 자료 포함 |
| `data/threshold_cycle` | 771개, 0.285 GiB | 1,029개, 0.987 GiB | 1,634개, 0.944 GiB | 정책·승계·custody 포함, raw 일괄 삭제 대상 아님 |

월별 개수는 경로 또는 파일명에 해당 `YYYY-MM`이 들어간 일반 파일의 재귀 집계다. `pipeline_events`의 archive receipt 12개는 모두 9월 파일이며 6~8월 파일에는 해당 receipt가 없다. Parquet 존재만으로 JSONL과의 바이트·행·계약 동등성이 증명되지는 않는다.

당시 선택 릴리스는 `samsung-main-route-restore-20260929-45bc11e1` (`45bc11e19ccdc75278bb6d263c16a4bcf5937461`)이었다. 아래 현행 선택 릴리스 및 삭제 영수증으로 대체되었다.

## 2026-09-29 19:36 이후 현행 상태

- 선택 릴리스 `integrated-machine-forward-20260929-4baaa98a` (`4baaa98ae8a715b477aafce0526b325f0a9b84d4`)가 Main PID `1507866`에서 실행 중이다. `bash deploy/run_runtime_release.sh postclose 2026-09-29 --print-plan`은 같은 릴리스의 장후 wrapper를 가리키고 `--check-cron`은 통과했다.
- 공유 `data/source_quality/clean_baseline_policy.json`의 `policy_refresh_start_date`를 `2026-09-29`로 조정했고, 선택 릴리스의 helper가 오늘과 다음 날짜에 같은 시작일을 반환함을 확인했다. 오늘 `pipeline_events`, AI payload와 `threshold_events` 원천 파일이 존재한다.
- 20:10 장후 본 작업·DONE controller·튜닝 후속과 다음 날 05:00 최종화 cron은 활성 상태다. 9/29 wrapper에서 구형 전체 기간을 요구하는 저가 후보 확장 단계만 설치된 cron env `THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION=false`로 끈다. 한때 설치했던 전체 장후 건너뛰기 규칙은 정확히 원복했다.
- [삭제 계획](../../data/source_quality/deletion_manifests/old_raw_2026-06_to_2026-08_20260929.plan.json)의 SHA-256은 `aa3e3cdd957a64acd8997b319501b0b471d8726ba88b069d7e83b861e8cd1aff`다. [삭제 영수증](../../data/source_quality/deletion_manifests/old_raw_2026-06_to_2026-08_20260929.plan.receipt.json)은 원천 파일 2,030개, 8,435,551,672 bytes의 제거와 잔여 파일 0개를 기록한다. 대상 파일의 열린 FD는 제거 직전 `lsof` 검사에서 0개였다.
- 삭제 범위는 `pipeline_events`, AI decision payload/trace/request/prompt/outcome, threshold 날짜 파티션과 threshold event, gatekeeper snapshot, entry candidate lifecycle event, entry odds raw prediction, 과거 연구용 market data의 날짜별 JSONL/압축 파일이다. `analytics` Parquet, `source_quality/raw_row_exclusion`, report, policy, runtime 및 주문 custody, 오늘 원천은 제거 대상이 아니다. 과거 원본의 복구 가능성을 보장하는 독립 archive 영수증은 없으므로 과거 원천 재생은 퇴역한다.

## 남은 자연 검증

오늘 장후의 실제 시작·완료, 당일 원천만의 소비, 각 stage의 source gap/valid-empty/표본 부족 구분, controller 및 다음 날 최종화 영수증을 확인한다. 코드·라우팅 확인과 자연 생성·비용 후 성과는 별도다.
