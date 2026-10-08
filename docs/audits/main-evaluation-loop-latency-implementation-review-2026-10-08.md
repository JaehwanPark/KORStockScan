# Main 평가루프 지연 구현·성능 검토 — 2026-10-08

## 범위·기준

사용자가 구현→리뷰/보완 반복→성능 확인→배포·재기동을 승인했다. 실행 owner는 당일 `DirectFamilySourceRepairMainMechanisticEntry`다. 구현 시 기준은 실제 Main PID `34821`/start ticks `299797`, release `pre-after-intraday-20261008-v1`/`f08405fb`, 활성 v6 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`다. 기계 128 contract scope/48 operating scope, 승인된 추가 13개, 보조 binding과 native carry를 유지한다.

근거는 [측정 manifest](../../data/report/main_loop_latency/2026-10-08/benchmark-summary.json) 및 같은 디렉터리 원 측정값/테스트 로그다. 최초 계획의 구 PID 24520 증거는 manifest의 경로·바이트 hash로 보존했다. 최신 PID의 50초 수동 프레임 관측은 Main `run_sniper` 스레드 95개 중 `load_effective` 48, `record_pid_consumption` 34, `configure_bundle` 3이다. 중첩 표본이고 원자 스냅샷이 아니며 전체 스레드 frame read 오류 125개가 있어 정확 CPU/경과시간 비율로 해석하지 않는다.

## 구현·리뷰

- `mechanistic_entry_runtime_policy`가 검증된 불변 view를 발급한다. 같은 동기 평가의 영수증 읽기만 view를 공유하고 외부 loader의 dict는 계속 격리한다. current pointer 변경은 context 진입·중첩 조회·종료에서 차단한다. AI 응답 및 제출의 기존 검증 경계는 독립이다.
- 매 평가의 파일 stat 검사를 유지하면서 공통 상위 경로 해석을 한 pass 안에서 공유한다. 경로/링크 inode·ctime·target, 내용 파일 inode·mtime·ctime·크기, 누락·원자 교체를 확인하고 pass 종료에 상위 경로를 재확인한다. cache miss는 단일 검증자/최대 2초 대기이며 실패한 옛 view를 반환하지 않는다. 파일 hash는 streaming으로 계산한다. 실제 원천 766개에 기존 32-entry cache가 매번 1,063회 miss를 내는 것을 확인하여, 물리 파일 identity 단위 최대 1,024개·accounted metadata 1MiB의 이중 상한을 적용했다. 파일 본문은 저장하지 않고 경로 provenance 검사는 각 호출에 남긴다.
- 새 orchestration은 `scalping/reversal_evaluation_context.py`에 둔다. 같은 검증 세대/일자/PID start ticks/cwd/선택 commit/backend에서 구성과 소비 영수증을 재사용한다. 현재 selector·정책 의존 원천·보조 overlay/취소·registry/reader·handoff·기계/보조 consumed 파일의 변경은 계속 검사한다. 실패한 부분 구성은 완료로 cache하지 않는다. 기존 reader의 process-lifetime handoff set이 바뀐 handoff 검증을 생략하지 않도록 추가 검증했다. 코드 pin에 포함된 v4/v5/v6 모듈은 수정하지 않았다.
- WS는 `infrastructure/snapshot_copy.py`의 격리 복사를 사용한다. 전체 history 길이/순서/타입 및 alias/cycle을 보존하고, 원본 참조를 잠금 밖으로 내보내지 않는다. unknown 객체는 deepcopy protocol을 유지한다. 이미 격리된 payload의 health/형식 후처리만 잠금 밖으로 이동했다. raw 무손실 전달·pending 병합/lock 순서는 보존한다. Kiwoom 요청/parser/FID/REG/recovery는 수정하지 않았다.
- 실제 claim 검사는 무거운 준비/claim lock 대기 뒤의 현재 시각을 사용한다. replay는 주어진 oracle 시각을 유지한다. 원 신호 epoch와 5초 TTL을 갱신하지 않는다.
- `monitoring/runtime_performance.py`가 모든 완료 loop 및 단계 시간을 메모리로 집계하고 기존 60초 로그에 출력한다. 종류별 최대 4,096개 표본, 신호별 연결 최대 128개이며 provider 미호출/관측 없는 구간은 null이다. 첫 loop와 warm loop를 분리하고 원천 품질/주문/승률/경제성 판정에는 사용하지 않는다. 동기 tick 파일 쓰기·원장 복제·실험 AI 호출은 추가하지 않는다.

소비자 검토: `REALTIME_TICK_ARRIVED`의 SignalRadar는 통합 점수·Big-Bite와 후속 `TRADE_SIGNAL_DETECTED`를 사용한다. live `get_latest_data/get_exact_item_data/get_all_data`는 Main 진입·보유·청산의 기존 전체 snapshot 계약을 유지한다. dashboard만 원래 120행 계약을 유지한다. 따라서 소비자용 필드를 줄이거나 임의 history 제한/새 payload schema를 도입하지 않았다.

## 검증·성능

| 구간 | 변경 전 중앙값 | 변경 후 중앙값 | 범위 |
| --- | ---: | ---: | --- |
| 같은 정책의 warm load/receipt 재조회/configure | 222.5ms | 9.5ms | 각 50회, receipt I/O 모의, 실제 기계/정책 로직 |
| WS snapshot 120행 | .891ms | .369ms | 각 50회, nested 수정 격리 |
| WS snapshot 2,000행 | 7.513ms | 2.015ms | 전체 history |
| WS snapshot 10,000행 | 36.092ms | 9.128ms | 전체 history, p99 87.5→55.6ms |

정책 전체 내용 digest가 일치했다. 이는 오프라인 부분 경로 개선이며 전체 Main loop p95≤2초/p99<5초, 실제 WS lock p99≤10ms의 달성을 뜻하지 않는다. 특히 10,000행 재현의 긴 꼬리는 남는다. 실제 확정 신호가 없으면 confirmed→claim 및 후속 stage 목표는 관측 불가로 유지한다. 두 프로세스가 같은 서버에서 진행한 초기 비교에는 live 부하와 다른 benchmark의 경합이 포함되어 있고, 자연 실행 전후 수치로 최종 확인한다.

검증 그룹은 중복되어 합산하지 않는다: 초기 원천/WS/고정감시/루프 355 PASS, 정책/등록/보조 70 PASS, WS/AI전송/기동/라우터 통합 647 PASS, 최종 변경 영향 302 PASS. 신규 반례는 12 PASS(원천 ctime/원자 교체, 링크 동일 target 교체와 dotdot, 동시 miss, 검증 중 변경/실패/대기 상한, configure 실패, overlay 변경, 수정 격리, 실제 5초 경계, bounded 진단). compile 및 diff check를 수행했다.

v2 구형 postclose 보고 회귀 한 건의 `KeyError: routes`는 현재 수정본과 기준 immutable `f08405fb`에서 동일하게 재현했다. `continuous_reversal_policy`의 구형 report projection 문제이며 이번 current v6 latency 변경으로 도입되지 않았다. 핀된 과거 정책을 바꾸는 수정은 이번 코드에 섞지 않았다. 활성 v4 carry/v5/v6 및 13개 등록 회귀를 별도로 검증한다.

## 배포·자연 실행 인계

승인된 immutable 배포/재기동 후 정확 release/PID/start ticks/cwd, v6 및 보조 소비, 원 PREOPEN 보존, strict/finalization 봉인을 확인한다. 새 release의 자연 loop/lock/claim 결과는 이 절에 후속 기록한다. 실제 주문·체결·수익 개선은 성능 시험의 종료 조건이나 이 문서의 주장 범위가 아니다. 기존 보조 연구의 미커밋 변경은 보존하고 이번 배포에서 제외한다.

### 자연 실행 중 재리뷰

첫 배포의 자연 검증에서 policy refresh의 `machine_policy_generation_changed_during_evaluation`을 확인했다. 기존 handler가 이 예외를 조용히 넘겨 원인이 가려져 있었으므로 최대 16종/종별 60초 간격의 원인 기록을 보완했다. canonical data root가 같은 release data 링크/절대 anchor의 cache 충돌을 발견하여, cache/검증 view 식별자에 lexical anchor와 실제 target을 함께 결속했다. 경로 혼용 회귀를 추가했고 관련 184 PASS를 확인했다. 첫 배포의 빠른 일부 loop는 정책 준비가 끝나지 않은 상태여서 최종 자연 성능 개선 근거에서 제외한다. 개선된 release의 실제 기계·보조 소비를 다시 확인한다.

v3 PID 57809의 기계·보조 소비 및 실제 ENTER_NOW 판정 관측으로 경로 혼용 수정의 소비를 확인했다. 이 상태의 Main warm loop 123회는 p95 8.250초/p99 9.526초/max 12.168초, 5초 초과 19회로 초기 목표 미달이다. 신호 claim 6회는 최대 4.919초이며 실제 claim된 분모만 포함한다. 주문·체결 개선으로 해석하지 않는다.

보고용 원천 반복 검증을 추가 측정했다. `hash-working-set.json`의 기존 2회 검증은 1.564/1.552초, 각각 1,063 miss였다. `hash-working-set-after.json`의 bounded cache 적용 후 첫 검증 1.310초/766 miss, 이후 0.285/0.286초와 0 miss다. metadata 457,302 bytes, 766 entries이며 signature/원천 hash 일치는 그대로 검사했다. 해당 변경 관련 208 PASS, 최종 추가 반례 포함 18 PASS(서로 중복)를 확인했다. 읽기 실패·읽는 중 내용 변경은 cache에 기록하지 않고, hardlink alias의 digest 재사용과 링크 교체 차단, entry/byte eviction, 동시 single-flight를 검증했다. 보고 프로세스 분리는 이번 재사용 개선 이후 남은 자연 경합 측정에 따라 후속 판단한다.

v4 PID 70105의 50초 추가 스택 표본에서 Main 96회 중 31회는 `manual_control_exclusion → decision_activation_matches → policy_activation_matches`의 원장 잠금 대기였다. 반면 detector 93회 중 86회는 주기 대기였고 file_digest 표본은 없었다. 표본 read 오류 129개와 비원자 관측 한계는 그대로 공개한다. v4 warm loop 105회는 p95 5.505초/p99 7.472초/max 9.125초, 5초 초과 12회였다. 다른 시각·입력 부하의 자연 표본이므로 개선율의 통제 실험으로 쓰지 않는다.

남은 원장 조회 병목은 기존 소유자 `trading/order/owner_custody_registry.py`에서 보완했다. 원래의 EX flock을 그대로 획득하고 원장 전체 hash chain 검증으로 얻은 증빙 행만 재사용한다. 경로/실제 대상/파일 및 링크 inode·size·mtime·ctime 변경과 append는 즉시 폐기한다. 읽기 전후 identity가 달라도 실패한다. 계좌·일자·종목·policy·mode·allowed owners·migration·broker snapshot·entry authority 비교는 매 호출 수행하므로 판정/수동 통제 결과를 cache하지 않는다. 최대 64행×ASCII JSON 4,096 bytes이고 큰 행은 기존 검증 읽기로 돌아간다. mutation·주문 예약/append·보유/청산·권한 정의는 변경하지 않았다.

정확한 현재 원장 1,476 event/1,891,615 bytes를 한 번만 격리 임시 복사한 뒤 양쪽 30회 비교하여 25.201ms→0.053ms 중앙값을 확인했다(`activation-lookup-benchmark.json`; 측정 후 임시 사본 자동 삭제). 신규 호출·주문·실원장 변경은 없었다. 계좌 및 모든 authority 필드, ctime/동일 mtime 변경, 삭제/원자 교체/링크 교체/append, 읽는 중 변경, 동시 조회, 반환 row 격리 및 큰 row fallback 관련 기존·추가 회귀 251 PASS다. review에서 이 보완을 LP4의 실측 병목 범위에 포함했으며 다른 소유권 규칙은 확장하지 않았다.
