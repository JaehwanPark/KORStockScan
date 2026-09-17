# 장후 계산 최적화 부분 구현·리뷰 — 2026-09-17

## 1. 판정·범위

기존 [계산 계획](../proposals/postclose-computation-optimization-implementation-plan-2026-09-17.md)의 **O0 main wrapper·O3 감사 행 내부·O2 삼성 관측 feature 부분 수리**다. 전체 O0–O3/P1–P6 구현 완료가 아니다. 신규 모듈·collector·장후 작업·timer·TR/Provider 호출을 만들지 않았다. 다른 세션의 final-refresh wrapper/verifier/test/문서/generated 변경은 보존하고 이번 commit에서 제외한다.

## 2. 구현·반복 리뷰

- `run_threshold_cycle_postclose.sh`: 기존 process-group supervisor에서 명령별 wall·reaped child user/system CPU·largest waited child RSS·exit를 stderr `[PERF] postclose_command_metrics_v1`로 출력한다. 단순 `sleep`은 `bounded_wait`; 나머지 command의 내부 local/Provider/선행 대기는 아직 분리되지 않았다. stdout/status/경제성 report/hash에는 계측을 넣지 않는다. argv/payload/token은 출력하지 않는다. 정상/비정상 exit는 원래 값을 유지한다. HUP/INT/TERM은 원래 signal termination을 유지하며 부분 wall과 CPU/RSS null·`measurement_complete=false`를 남긴다. KILL 또는 supervisor 시작 전 종료의 완전 receipt는 보장하지 않는다. CPU는 shell/supervisor 사용량이 아니며 RSS는 동시 process-group 합계 peak가 아니다.
- `observation_source_quality_audit.py`: 각 행의 동일 정규화 결과를 계약 검사에 전달하여 재정규화를 제거한다. 원천·generation·이전 판정의 persistent cache를 쓰지 않는다. 반복 field-name source 분류만 pass-local 최대4,096개/label256자 bound로 재사용하고 값·의사결정은 저장하지 않는다. `_raw_generation`에 ctime을 추가해 동일 크기/mtime 복원 정정을 놓치지 않는다. JSON/gzip·유효/손상 행·원문 digest·행 제외·unknown/label/authority guard는 보존한다.
- `samsung_machine_entry_tuning.py`: cohort/window의 candidate-invariant drawdown/proximity 숫자를 한 번 변환한 뒤 기존 전체4군을 순서대로 평가한다. Matching·집계·순서·gate·정책 의미·owner state를 바꾸지 않는다. 현재 tightening subset-only 연구를 전수 미진입/완화 연구 완료로 표시하지 않는다.
- `scalping_avg_down_recovery_calibration.py`: 기존 replay source fingerprint의 size/mtime 뒤에 device/inode/ctime을 결속하여 같은 크기·mtime 복원 정정/원자 교체를 cache hit로 오인하지 않는다. 기존2필드 fingerprint는 새5필드와 불일치하여 한 번 miss/revalidation하며 과거 receipt를 새 검증으로 재라벨링하지 않는다. 정상 warm replay·Provider0 회귀와 실제 `_load_replay_cache`의 정정 시 결과 cache0을 검증했다. Provider 재시도·수량/추가매수/exit 권한을 바꾸지 않는다.

Supplemental review에서 spawn 실패 계측 누락, cache 위치/크기 bound, empty normalized mapping의 truthiness 오인, generation 동일 크기 정정, signal 부분 계측과 stderr 비공개성을 점검·회귀 보완했다. 검토 범위의 최종 finding0은 targeted 재검증 뒤 확정하며 전체 계획 finding0으로 전용하지 않는다.

## 3. 고정 fixture 성능·목적 부합성

등록183개 계약 ×3개 원천 변형 ×20반복 = **10,980행/2,527,440 bytes**. Fixture SHA256 `baad8b7b43dbe183f4e196a227af6b8c11b372c103fa6e3052b37d609588c57a`. 변형은 missing source·unknown/zero·integrated aftermarket axes다. Committed reference와 optimized를 같은 고정 in-memory JSON decode 원천으로 교대로5회 측정했다. 운영 raw/API/Provider를 읽지 않았다.

- Reference CPU초: 0.594407126, 0.624808520, 0.595821394, 0.621308951, 0.597064418.
- Optimized CPU초: 0.523170161, 0.509799198, 0.538800433, 0.516603978, 0.540112449.
- 중앙값0.597064418→0.523170161초, **12.376% 감소**, 전체 결과·행 제외·집계 동일. 마지막 label 길이 bound 보완 전 계측이므로 최종 managed 재측정은 별도 기록한다. Lifetime self peak RSS90,240KiB는 두 경로 독립 peak 비교가 아니며 RSS 개선을 입증하지 않는다.
- 감사의 계약 행 정규화2회→1회; 삼성 회귀 fixture의 관측 문자열 변환28회→7회. 후보 축소·sample/floor·holdout·경제성/비용 모델 변경 없이 중복 계산만 줄였다.

최종 release의 **계약명 정렬로 봉인한 별도 fixture**는 같은 행수/bytes이며 SHA256 `da71e0ddc93f5fc0bf4fe605d00a2ad0b166c3018ecd415ebb5467a92d69c113`이다. 초기 unsorted 계약 iteration fixture와 합산/교차 비교하지 않는다. 최종 label-length bound를 포함하고 managed module import를 확인했다. Reference CPU초 `[0.609637697,0.610918852,0.607378428,0.613136583,0.622512081]`, optimized `[0.520953290,0.510450110,0.542502740,0.510234277,0.542144525]`: 중앙값 **0.610918852→0.520953290초,14.726% 감소**. 전체 output parity와 digest `476f432f49357440ba31019a57fe620979840094ee597495f471e52a852140fe`를 확인했다. Memory-source decode/compute 비교이지 운영 disk read/critical-path benchmark가 아니다.

이는 작은 비용 후 수익을 빈번하게 만들기 위한 **계산 낭비 축소**이지 참여/실현순익 효과 증거가 아니다. 기계진입·AI보조·가격·수량/leg·scale-in·청산 및 hard/broker/custody/호가 guard를 변경하지 않았고 추가 live 승인·새 승격 floor를 만들지 않았다. 기존 자동 장후 producer는 해당 release 소비 시 계산 경로를 사용한다. 자연 실행·next-date selection/PID 소비·실체결 비용 후 EV는 별도다. O3 CPU30%/decode60%, O2 CPU50% 전체 목표를 달성했다고 주장하지 않는다.

## 4. 검증·릴리스

최초 감사/wrapper314건, 삼성/감사/wrapper/EV/router429건 후 ctime/cache 회귀 보완431건 통과. Signal/exit/stdout/CPU/wait 추가 targeted3건 통과. 최종 전체 재검증·source/import/hash·release routing은 아래에 추가한다.

매매 런타임 함수는 이번 변경 대상이 아니다. 기존 router가 main/start/postclose를 하나의 selected release로 관리하므로 selection/PID 계약을 닫는 데 필요한 main1회만 별도 승인된 안전 절차로 재기동했다. 독립 trader/collector/research unit은 유지한다. 변경 중인 장중 raw full scan·expensive 보고서·예정 전 service를 실행하지 않았다.

## 5. 미완료·다음 owner

기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`을 유지한다. O0 machine wrapper/producer별 read bytes·row·cache·Provider/선행 wait 계측, 완료일 disk fixture·cold/warm/append/correction/cost/TERM 전체 matrix, O3 sealed-prefix projection/delta와 cumulative EV sufficient stats, O2 family checkpoint/grid 공통 state-aware replay, O1 exact request/예약·warm reuse 확장, P1–P6 scale acceptance는 **미완료**다. 이번 수리를 기존 source projection/전체 폐루프 완료로 합산하지 않는다. 다음 자연 장후 run의 phase receipt와 결과 parity를 기존 tower→checklist→strict→controller→finalization 체인으로 확인해야 한다.

## 6. 최종 검증·배포·실제 PID receipt

- Source/main `9c69864c`와 cache 보완 `2166c12c` push 완료. Managed `release/postclose-compute-20260917`의 `e64dae4ed37478be65c750140a095e3f0daed8d6` push 완료. Root `/home/ubuntu/KORStockScan-runtime-releases/postclose-compute-20260917`은 당시 실제 선택3261 baseline에 이번 source/test diff9파일만 적용했다. Main의 다른 연구 배포분/dirty 변경을 현재 거래 release에 임의 혼입하지 않았다. Independent research/evaluation pins의 기존 별도 릴리스를 보존한다.
- Workspace5 suite432 pass, AVG_DOWN3 suite106 pass와 추가 감사/cache260 pass. Managed final8 suite **531 passed/2 deselected**. 두 제외는 공유 `data` symlink 때문에 Git `check-ignore`가128을 반환하는 fixture이며 기능/경제성 테스트 제외가 아니다. Physical 경로의 해당2 fixture는 **2 passed**, shared 경로 복원 확인. 첫 physical5 suite427 pass, 첫 shared 경로425 pass/2 Git fixture fail을 숨기지 않고 분리했다. 최종 compile·shell·code-clean·diff 검증·4개 source/wrapper SHA 일치, print-only parser 확인. 검토된 부분 범위 finding0이며 전체 계획 closure가 아니다.
- Existing main selector를 기존 lock 아래 compare-before-atomic-move로 게시하고 router의 cron9 target·dated postclose/start print-plan을 확인했다. Selection backup `tmp/runtime_release_selection.pre-postclose-compute-20260917.json`, SHA `ebb089e169777e36c758d206f0d582aebb2e1582f538ca996d779362f5fb5f56`; 원본 physical mount backup `tmp/runtime_release_mounts/postclose-compute-20260917.ZIfe4w`는 보존했다.
- Main graceful1회: **12:38:35.088894 KST/PID384157**이 e64dae4e actual cwd/env/launcher receipt를 소비했고 source-dirty=false·singleton1·strict 당일 env/PID PASS(mismatch/missing0)다. **12:37:39.025287 사전→12:38:56.289945 사후** 양시장 broker 조회 complete, 삼성전자25주/매수가269471·미체결0으로 같았다. Owner registry `2975c91a…`, runtime env `65121195…`, 당일 machine policy `395a9447…` SHA 모두 같다. 주문 제출/취소·custody/env/정책 변경은 하지 않았다.
- 새 tmux session_created1789616313/current cwd가 새 root이며 bounded4000line/4MiB pane에서 로그인 응답 확인1·005160/043260 첫0B와010140/034020 등 첫0D 수신 marker를 확인했다. 과거 info/error 파일의 bounded tail에는 새 receipt가 없었으므로 그 파일을 최신 근거로 쓰지 않았다. 전scope quote freshness/실제 정책판정·새 submit/fill·순익 개선 증거는 아니다.
- Widget trader327012·episode auto-expansion327094와 collectors282239/282392는 원래 active/running PID/root를 유지한다. 20:10 widget evaluation·21:15 final refresh는 기존 admission release pin/MainPID0·not_yet_due이며 오늘 성공 terminal로 세지 않는다. Main 장후 producer는 아직 자연 실행 전이다. 오늘 장후 phase/consumer/strict 확인과 비용차감 economics는 OPEN이다.
- Scoped validation `data/runtime/runtime_release_validation/postclose-compute-20260917-e64dae4e.json`은 operating DONE·전수 구현 완료·경제성 승인 receipt가 아니다. Rollback도 현재 broker/owner 확인 후 기존 selector를 복구하고 main만 안전 재기동하는 범위이며 실행 중 wrapper/research pin을 교체하지 않는다.

## 7. O1 discovery-local floor 재파싱 보완

- `_historical_backfill_dates`→각 날짜 `_historical_backfill_floor`가 같은 historical floor JSON을 반복 decode하는 기존 경로를 대사했다. 기존 `ai_quality_cycle.py` 안에서만 discovery-local fact cache를 전달한다. Invocation마다 새 cache이며 최대32 entry/decoded entry256KiB다. No new module/collector/job/timer; checkpoint/Provider 결과·reservation/budget/state는 캐시하지 않는다.
- Pinned no-follow parent와 plain/gzip 양쪽의 device/inode/size/mtime/ctime census를 매번 확인한다. 변경·새 dual copy·상충·손상·삭제·symlink·부모 교체는 strict reader 재검증/원래 실패로 처리한다. Decode 도중 변경은 cached PASS가 되지 않는다. Writer lock busy이면 기다리지 않고 cache를 비운 뒤 원래 strict pinned reader로 fallback한다. Floor 의미 hash/날짜/기존 first-bound floor·source lineage·orphan/예산·Provider admission은 매 사용마다 원래 validator를 거친다.
- Private discovery/selection 경로에서 floor는 read-only 사실 자료다. 해당 consumers와 leaf validator의 비변경을 확인했다. 최초 방어적 deep-copy 안은 frozen fixture CPU79.63% 증가로 폐기했다. Mutable candidate/owner state를 공유하지 않으며 정규화 결과의 대조/hash 검증을 생략하지 않는다.
- Final frozen JSON53,805bytes SHA `094e10feb3a50c0c2060b2e3ba772ec24adbb688b2c4dae9aba2fc3d71467fd3`, 동일30회 read×교대5회. Reference CPU `[0.016753638,0.013910598,0.014493494,0.013942529,0.014309171]`, optimized `[0.004743998,0.004745768,0.004642915,0.004539572,0.004854461]`; median0.014309171→0.004743998초, **66.846% 감소**와 전체 output parity. 실제 discovery→2개 날짜 selection fixture strict decode3→1을 확인했다. 이는 작은 local floor read benchmark이며 전체 O1 CPU30% 목표/Provider transport·운영 critical path·RSS·순익 개선 근거가 아니다.
- Workspace 관련5 suite **430 passed**: cycle/runtime-family/standing-authorization/bridge/release-router. 추가 plain/gzip·수정·원자 교체·append·dual conflict·손상·symlink·missing·읽는 도중 변경·부모 교체·busy fallback·memory bound·별도 invocation·선정 oracle 회귀. Compile/diff check PASS; review finding0은 이 O1 부분 범위만이다. Live entry/AI 보조/가격/수량/leg/scale-in/exit·provider/model/cap/cost/floor는 변경하지 않았다.
- 전체 O0 내부 phase 계측/완료일 고정 fixture, O3 frozen projection·prefix proof/delta·EV 충분통계, O2 full-grid state-aware replay/append/정정/holdout, O1 전체 exact-request/aggregate reuse, P1–P6 scale matrix는 여전히 미완료다. 오늘 장후 자연 producer→consumer→strict 및 비용 차감 economics는 별도 OPEN이다. 이번 범위의 배포·실제 PID 근거는 검증 완료 뒤 별도 추가한다.
