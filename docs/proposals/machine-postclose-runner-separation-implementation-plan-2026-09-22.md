# 기계 통합 장후 실행기 분리·정리 구현계획

작성: 2026-09-22 KST
상태: 계획 수립. scheduler/서비스/실행기 변경은 아직 실행하지 않았다.
실행 owner: [9/22 체크리스트](../checklists/2026-09-22-stage2-todo-checklist.md)의 `PostcloseStageRunnerSeparation`.
연결: [메인 기계정책](main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md), [보조 AI](auxiliary-ai-opportunity-error-tuning-runtime-implementation-plan-2026-09-22.md).

## 1. 문제와 소유권

`run_machine_microstructure_final_refresh.sh`는 widget 입력 대기·확장 추천, capacity source, microstructure attribution, 시장약세, widget/episode timing, widget/episode 연구 발행, 기존 policy approval, 요약을 직렬 결합한다. collector 실패면 attribution 이후가 실행되지 않고, machine terminal도 모든 타 family source를 요구한다.

메인 BLOCK/RECHECK 학습은 이 실행기에 없으며 `run_threshold_cycle_postclose.sh`의 calibration이 소유한다. 그런데 main wrapper도 episode/low-price 생산자와 compact AI 후행 단계를 포함하므로 총괄 실패와 메인 정책 실패가 혼동된다. 목표는 명칭만 바꾸는 것이 아니라 **입력 DAG·writer·실패·재시도·완료·장중 적용 경계를 분리**하는 것이다.

## 2. 목표 DAG와 stage 계약

| stage ID | 계산/발행 owner | 필수 선행 입력 | 실패의 영향 |
| --- | --- | --- | --- |
| `main_machine_policy` | 기존 calibration + strategy publisher | main raw·비용·경로 label | 해당 기계정책만 carry |
| `main_auxiliary_policy` | 기존 compact replay + AI publisher | 실제 ENTER_NOW AI 입력·응답·경로 label | AI만 carry, 기계정책 유지 |
| `widget_policy` | 기존 widget evaluation/연구 publisher | widget 원천·기존 운영 명단 | widget만 기존 정책 유지 |
| `episode_policy` | 기존 expanded research/정책 publisher | episode 원천·기존 프로필 | episode만 기존 정책 유지 |
| `collector_recommendation` | 기존 확장 추천 | 완성된 outcome-label receipt·대상 manifest | 추천만 실패·재시도 |
| `machine_attribution` | 기존 귀속 producer | 해당 machine 실행/관측 | 진단 실패, main 임계치 선정과 독립 |
| `machine_timing` / `market_weakness` | 각 기존 튜너 | 자기 귀속/시장 입력 | 해당 정책만 carry |
| `research_allocation` | 기존 공동 연구 closure | widget/episode·자본 등 완성 source | 신규 공동 자본 배분만 보류 |
| `legacy_policy_approval` | 기존 승인 queue | 자신이 담당하는 후보 | 해당 승인만 실패 |
| `summary_handoff` | controller/summary/verifier | 각 활성 stage의 exact terminal | 완료/실패/이월을 정확히 취합 |

기본 운영 profile carry와 자료 검증은 공동 연구의 allocation 개선 실패 때문에 막지 않는다. 공동 자본 증액·겹치는 custody의 신규 승격은 기존 allocation 검증이 필요하다. main/auxiliary 단계가 이를 대신 승인하지 않는다. OFF/관측 전용 stage는 freshness 실패로 복원하지 않고 explicit disposition을 기록한다.

## 3. 구현 방법: 기존 owner 재사용

1. 먼저 기존 `postclose_summary_handoff`의 receipt를 stage ID 기준으로 확장한다. `schema_version`, source/publication/effective dates, run_id, source hashes, stage code hash, status, exit_code, changed/carry policy hash, prerequisite receipts, checkpoint, retryability를 저장한다.
2. 기존 widget/machine v1 terminal은 과거 검증용으로 읽는다. 과거 machine 성공을 새 모든 stage 성공으로 합성하지 않는다. 현재 run에서 실제 stage가 남긴 완료·source 영수증만 사용한다.
3. `run_machine_microstructure_final_refresh.sh`는 한시적 호환 진입점으로 남기고 명시된 stage 호출과 exit 집계만 수행한다. 각 stage를 독립 실행/재개할 수 있게 기존 automation owner에 dispatch 옵션을 추가한다. 긴 stage가 다른 stage의 시작을 막지 않도록 자원 admission과 bounded concurrency를 적용한다. 무제한 동시 Python 작업은 금지한다.
4. main wrapper에서 `main_machine_policy`를 별도 작업으로 dispatch한다. episode/AI 실패와 무관하게 정책 generation을 발행한다. 기존 compact 호출도 자기 stage로 전환한다. 초기 migration 동안 같은 producer가 old/new 경로에서 중복 실행되지 않도록 동일 stage lock을 사용한다.
5. `machine_research_closed_loop_refresh`의 widget/episode writer와 공통 feedback/allocation을 분리한다. family별 writer는 각자의 완료 입력만 읽고, 공동 allocation은 별도 후행 stage다. 기존 함수에 family scope를 추가하고 이전 통합 모드는 호환 전용으로 제한한다.
6. summary/controller/verifier/intake/finalization과 `INDEPENDENT_SOURCES`를 동일 stage registry로 전환한다. 코드 위치는 기존 `src/engine/automation` owner를 재사용한다. 새로운 engine-root module·DB·각 family daemon은 만들지 않는다.
7. cron/router/systemd는 기존 예약 진입점을 유지하고 stage dispatch만 연결한다. 한 producer당 한 writer owner인지 확인한다. 전환 검증이 끝나면 임시 호환 분기·중복 타이머·구 환경변수는 제거하고 제거 조건을 기록한다.

## 4. 완료·장전 준비·재개

- stage status는 `pending/running/succeeded/failed/deferred/off`이며, 정책 disposition은 `updated/incumbent_carry/no_valid_candidate/source_gap`으로 분리한다. 후보 없음은 성공한 계산일 수 있고, 실패한 계산을 carry라고만 표시해 숨기지 않는다.
- `postclose_all_active_stages_complete`와 `next_session_policy_ready`는 서로 다른 결과다. 전자는 필수 활성 작업의 실패가 남으면 false, 후자는 main/widget/episode의 기존 유효 정책·현재 loader·startup 계약이 모두 맞으면 true일 수 있다. 보조 진단 미완료가 정책 자체를 삭제하지 않는다.
- checkpoint에는 단계 내부 진척과 완성 source generation을 묶는다. 재개는 failed stage부터 진행하고 필요한 하류만 invalidate한다. 입력·코드·발행 hash가 바뀐 completed cache는 재검증한다. 보고서 파일 존재·프로세스 종료만으로 성공 처리하지 않는다.
- label producer는 임시 파일에 쓰고 검증 후 atomic publish한다. collector는 source date/manifest/hash 일치한 committed receipt를 기다린다. 소비 도중 source generation이 바뀌면 재시도하며 partial label로 recommendation을 만들지 않는다.
- source/publication/effective date는 시작할 때 명시적으로 pin한다. 자정 이후에도 source 날짜를 유지하며 prepared target과 현재 소비 시각을 구분한다.
- 날짜·stage별 lock, PID/start identity·heartbeat를 사용한다. 실제 진척이 있는 작업에 stale lock 삭제나 중복 실행을 하지 않는다. 중단은 저장된 chunk 경계에서 하고 wrapper 전체를 재실행하지 않는다.
- 위젯100·에피소드 신규50 상한과 기존 운영 명단 보존을 유지한다. source coverage → 완료 추천 → 이전 train 성과 순서로 자원을 배정하고 이월을 source 부족과 분리한다.

## 5. 이행 순서와 검증

| 순서 | 작업 | acceptance |
| --- | --- | --- |
| R1 | stage registry·v2 receipt·v1 reader | legacy 읽기, stage 누락/위조 성공 거절, source hash 검증 |
| R2 | main/auxiliary 독립 dispatch | AI/episode 실패 주입에도 main 계산·발행 성공 유지 |
| R3 | widget/episode/attribution/timing 분리 | 한 stage 실패가 독립 stage를 취소하지 않음, writer 중복0 |
| R4 | controller·최종화·장전 준비 판정 | 전체 완료와 정책 준비를 별도 출력, 기존 유효 정책 carry 확인 |
| R5 | scheduler 전환·오래된 경로 정리 | 예약 목록·실제 실행 cwd·source 날짜·락 점유와 terminal 일치 |
| R6 | 완료 source 재사용 실실행 | 실패 단계만 재개, 비용 큰 학습 재계산 없이 최종 인계 검증 |

실패 주입: collector label 지연/부분 파일, widget 실패, episode 실패, AI timeout, summary 실패, 자정, 같은 source 동시 요청, 코드 변경·과거 terminal 재사용. 기존 wrapper/summary/controller/router 테스트에 추가하고 `bash -n`, 대상 pytest, diff, parser를 실행한다.

자동화 변경 구현 시 [장후 운영 문서](../postclose-tuning-result-review-task-instructions.md)·daily checklist를 같은 변경집합으로 갱신한다. baseline Rebase/README/AGENTS는 별도 요청 없이 수정하지 않는다. 계획 단계에서는 cron/서비스를 수정하거나 작업을 실행하지 않는다.

## 6. 세 계획의 적용 순서

R1의 최소 stage receipt 계약과 M1~M5를 먼저 보완하고, M6에서 기계정책을 장중 적용한다. R2~R5의 나머지 family 분리는 그 기계정책의 장중 적용을 대기시키지 않는다. AI는 확보된 실제 호출 원천으로 A1~A5를 준비하고 A6에서 독립 적용한다. AI 표본 부족이나 source gap은 main 정책 유지·갱신을 막지 않는다. 마지막에 R6로 독립 장후 자동 갱신을 검증한다.

문서 검증: 세 계획의 상대 링크·현재 stable owner·실행 권한 경계를 재리뷰했고 print-only parser/diff를 통과했다. 문서 전용 단계이므로 shell/Python 테스트·서비스 전환·보고서 재생성은 실행하지 않았다.
