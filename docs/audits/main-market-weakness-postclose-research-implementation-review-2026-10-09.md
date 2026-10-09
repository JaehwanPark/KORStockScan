# Main 약세 장후 연구 구현 리뷰 — 2026-10-09

이 문서는 첫 구현 회차의 기록이다. 후속 승인에 따른 기존 5개 실패 수리·572건 통과·배포 완료는 [후속 배포 리뷰](main-market-weakness-review-deployment-2026-10-09.md)를 따른다.

당시 사용자 지시인 MW2–MW5 구현·리뷰·반복 수정보완을 수행했다. 앞선 MW0–MW1 수리, 현재 기계/보조 정책, Main/manual 소유권, 퇴역 consumer, 기존 장중 기록 경로를 보존했다. 배포·기동·cron 설치·운영 장후 재생성·실제 provider/Telegram 호출은 실행하지 않았다.

## 구현과 종료 범위

| owner | 구현 |
|---|---|
| [순수 연구](../../src/engine/scalping/market_weakness_research.py) | 실제 trace/replay projection, 기회 단위 중복·충돌 격리, source-time A/B/C/U, 시장별 raw/reconstructed 구분, 일별 cohort W/F/U, scope별 이전 세대 분위값 후보 고정, 전체 누적 기술 통계와 전향 안내 창 분리, 공통 기회 지연·U·날짜/구간 제외·동일 seed 1,000회 진단 |
| [독립 자동화](../../src/engine/automation/main_market_weakness_research.py) | 안정 cutoff·newline offset·범위 digest, read-only bounded shared objects, exact ask/label/실제 AI export·기존 compact decoder, compact partition→원자 cursor commit, 일별/누적 cache·원천 재검증, optional cron/calendar/selected code, 지속 night budget·worker supervisor·자식 회수 |
| [알림](../../src/engine/automation/main_market_weakness_research_notify.py) | 관리자 preview, 적격/winner/원천·현재 scope parent 재검증, 의미 ID, durable claim·message ID, 제한 재시도/배송 불확실, sent에 결속한 정정·철회·대체, 별도 notification disposition |
| [wrapper](../../deploy/run_main_market_weakness_research_postclose.sh), [installer](../../deploy/install_stage2_ops_cron.sh) | symlink만으로 reviewed copy를 판단하지 않고 공유 selector의 immutable release 검증, 자기 optional tag만 교체, 다른 cron/필수 stage/기동 경로 보존 |

소스가 없거나 actual ask·계약·정확 ID/시각/venue·라벨 연결이 맞지 않으면 U/미평가다. 저장된 실제 AI의 표본을 원 기계 모집단으로 사용하지 않는다. 정답을 붙이기 전 원 기계 partition·자연 trace census를 소유하고 실제 AI cohort는 별도 집계한다. 계좌/실제 체결·비용 원천이 없으므로 모든 가격 경로 결과는 configured-cost CF이며 실제 PnL이 아니다. 기존 허용 수치 역할이 선언되지 않은 기계 scope는 `numeric_adjustment_unidentifiable`다. 원 producer·AI 호출·정책 publisher를 새로 실행하여 이를 메우지 않는다.

신규 모듈은 `scalping`의 순수 연구와 `automation`의 독립 배치/전송 역할에 배치했다. Main/WS/scanner/AI/order의 새 import/call은 없다. engine-root allowlist, mandatory `STAGE_REGISTRY`, router `CRON_TARGETS/REQUIRED_CRON_TARGETS`, strict/finalization/PREOPEN 입력은 변경하지 않았다.

## 리뷰 → 수리 → 재리뷰

| 발견 | 보완·closure |
|---|---|
| 동일 기회의 retries/시간만 달라지는 행을 새 결과 또는 전체 충돌로 처리 | 원행/attempt census 보존, 실제 outcome binding 기준 중복, 식별된 충돌은 해당 scope만 격리 |
| 변경/삭제된 관찰·상장 metadata·정규화 source·shared pack을 이전 누적으로 계속 참조 | stat/hash/source-contract 검증, current 일별 세대만 집계, 영향 날짜 무효화·원천 영구 손실 source gap 종료 |
| 첫 빈 세대가 후보를 영구 고정하고 나중 scope를 놓침 | feature가 식별된 scope만 고정하고 신규 scope만 추가, 기존 cutpoint는 outcome으로 재탐색하지 않음 |
| 기존 확인점 ask에 다른 입력/응답/시각 결과를 붙일 가능성 | exact typed ID·event/time/ask·venue·label 계약·input hash·response ID·기존 decoder 검증, mismatch 제외 |
| prefix/tail·crash cursor가 원행을 건너뛰거나 빈 partition을 반복 추가 | 원행 범위 digest, stable cutoff, partition 선행 commit, tail defer, unchanged delta 0, 중복 빈 저장 제거 |
| 누적마다 전체 projection/관찰을 후보별로 재탐색 | 변경된 일별 aggregate만 계산, 시간 index로 원 300초 범위만 연결, 동일 완료 세대 cache 재사용 |
| 자정/재시도/worker exit 0이 예산·완료 상태를 잘못 표시 | 시작 KST night_id·선예약·crash 미환급, worker receipt 상태와 exit code 동시 확인 |
| 감독자/손자 프로세스가 memory/시간 한도 밖에 남음 | 감독자 RSS 포함, process-group 종료·Linux subreaper 회수, deadline 여유 유지 |
| 자식 시작 전 날짜·cursor census가 예약 예산 밖에서 계속될 가능성 | 사전 점검도 동일 wall 예약·감독자 메모리·야간 창·장후 우선권을 검사하고 초과 시 자식 미기동·독립 night summary를 남김, 예약 미환급 |
| 알림 실패를 완료로 표시하거나 불확실 배송을 재발송 | 실패/blocked/deferred/uncertain 분리, durable sending claim, 확정 message ID 필요, 불확실 자동 재시도 금지 |
| 과거 parent가 사라지면 정정도 막히거나 obsolete 철회가 발송 | 정정은 prior sent receipt·현재 무효화에 결속, 추천 회복 시 pending 철회 폐기, 같은 의미 재추천 억제 |
| 날짜/코드/다른 scope bundle 변경으로 같은 추천 재발송 | 날짜·보고 hash·코드 제외 의미 ID, 관련 machine payload/auxiliary binding 단위 현행 확인, 한 scope 현재 winner 하나 |
| user/root/systemd 중복 또는 오래된 selected 코드가 설치될 수 있음 | optional 설치 census·uid·calendar·정확 슬롯·code pin, 조회 불가/선택 코드 불일치면 설치 완료 금지 |

## 검증과 한계

- 신규 전용 테스트: projection/joins/labels/statistics, source/cursor/cache/supervisor/cron/decoder, outbox 세 suite의 **97건 모두 통과**.
- 관련 observer·panic·guard·위치 gate·release router·cron completion 및 live codec까지 최종 확장 검증: **397 passed, 5 failed (12.56초)**. 실패 5개는 아래 기존 mixed payload writer 결함이며 제외·xfail로 숨기지 않았다. 새 코드의 미해결 발견과 기존 producer 원천 결함을 구분한다.
- 합성 10,000행 집계·비교: wall 1.29초, peak RSS 131,724KiB(약 129MiB), 외부 호출 0. 이는 초기 구현의 합성 계측이며 실제 날짜/원천 규모의 야간 완료 시간이나 장중 자연 성능 영향 0의 증거가 아니다.
- Ruff, Python compile, 두 shell `bash -n`, `git diff --check` 통과. print-only parser는 현행 stable ID owner를 10/9 checklist에서 정확히 1개 찾았다. 변경 문서의 실재 로컬 링크도 확인했다. runbook의 기존 fenced 예제 `YYYY-MM-DD` placeholder는 실재 파일로 요구하지 않는다. 외부 Project/Calendar sync는 실행하지 않았다.
- 시작 시 기존 dirty/untracked 40개 hash를 기록했다. 최종 대조에서 owning 계획/현재 checklist 외 기존 파일의 hash 변경은 0개다. 미래 10/12 checklist SHA `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9`는 유지했다.
- selected release는 `main-integrated-bottlenecks-20261009-v1`, selection commit `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`, `actual_pid_consumed=false`, `awaiting_scheduled_main_start_20261012`였다. 이를 새 연구 배포/PID 소비 또는 자연 observer 수용으로 표시하지 않는다.

## 별도 확인한 기존 원천 결함 — 전체 런타임 GREEN 아님

확장 `test_reversal_auxiliary_wire.py::test_full_analyze_target_records_raw_then_decodes`의 `completed/incomplete/truncated/unknown_alias/refusal` 5개가 `ai_trace_dedup_preparation_pending`과 actual request row 0으로 실패했다. 신규 연구 suite 없이 기존 `completed` 단독 실행에서도 같은 실패를 재현했다. startup 준비 함수를 fixture에 추가해도 같아, 시험적인 fixture 변경은 원복했다.

직접 연결은 [mixed payload writer](../../src/engine/scalping/ai_decision_trace.py)의 pre-AI machine observation → request-key 없는 새 inode 생성 → [trace_dedup](../../src/engine/scalping/trace_dedup.py)의 inode/준비 상태 무효화 → actual AI request capture의 hot-read 거부다. 계측한 fixture에서 payload 29,896bytes는 이미 있었지만 request-envelope index는 inode None·offset 0·ready true인 빈 파일 준비 상태였다. 새 inode를 인식하면서 ready false로 교체되어 capture가 보류됐다. provider 성공/실패를 broker 주문 실패로 대체하지 않는다.

이 경로는 새 연구의 consumer가 아니라 기존 장중 기록 producer다. 본 계획 §4의 장중 기록/계산 유지 조건에 따라 writer·dedup를 변경하지 않았다. 코드 수준 재현이며 현재 운영 PID에서 동일 손실의 자연 발생 여부는 확인하지 않았다. 연구는 해당 exact actual capture가 없으면 U/미평가로 처리하고 성공·0 승률·원천 보강 완료로 위장하지 않는다.

후속 owner는 `ai_decision_trace._append_jsonl → trace_dedup → capture_ai_request` 계약이다. 다음 조치는 장중 쓰기 횟수/본문/authority를 늘리지 않는 mixed-row index 수리의 별도 범위를 확정하는 것이다. closure는 첫 machine→actual request 자연 순서, 기존 위 5개 회귀, concurrent append/rotation/partial tail·충돌·hot-budget 검증이다. **새 MW2–MW5 코드 리뷰 완료와 이 기존 source-writer 결함 수리를 구분한다.**

## 다음 수용

현재 구현은 작업본의 advisory 코드다. 실제 설치·선택 release 소비, 자연 일별 terminal→누적→notification disposition→night summary, unchanged delta 0, 비적격 무발송, 첫 적격 실제 receipt가 MW6 후속이다. 현재 후보 수치/실제 송달/정책 채택/수익 개선은 선언하지 않는다. optional 설치 기본값은 preview이며, 허용된 실운영 설치에서 관리자 안내 목적대로 `--notify-enabled`를 사용한다. Main 시작·기존 초기 정책 등록에는 이 연구의 경제성·비교 완료 gate를 추가하지 않는다.
