# Main PID 206123 워밍업 제외 평가 지연·REST/WS 병목 관측

작성일: 2026-10-08 KST. 요청 범위: Main PID 206123을 15:00까지 관측하고 병목을 진단한다. 실행 변경 권한: 없음. 이 문서는 진단 결과이며 배포, 재기동, provider 호출, 주문, guard 완화 지시가 아니다.

## 판정

평가루프 지연은 초기 워밍업 이후에도 발생했다. 우선 결함은 실제 상시감시 Main 호출의 비동기 coordinator 누락과 원천 경로 변경의 provider 실패 오분류다. 14:43:58 Entry AI 엔진이 비활성화됐고, 뒤이은 두 ENTER_NOW는 provider 호출 없이 DROP됐다. AI 호출이 없어져 짧아진 루프를 정상 실행 개선으로 인정할 수 없다.

REST/WS 구현 자체와 실제 호출 경로 연결은 다른 상태다. WS 호가의 표본 신선도와 분봉 writer 무손실 계수는 양호했지만, 상시감시 비동기 준비 경로는 사용되지 않았고 분봉 REST 대체도 관측되지 않았다. 반복 소유권 저널 복사·상태 환산과 공유 WS lock 안의 전체 이력 복사는 실제 PID의 반복 비용으로 확인됐다.

## 관측 경계와 신원

- PID `206123`, process start ticks `2010467`, 시작 `14:23:38 KST`를 고정했다. 다른 PID의 이전 오류는 제외한다.
- 실제 cwd: `/home/ubuntu/KORStockScan-runtime-releases/main-rest-ws-latency-20261008-v3/src`.
- 실행 release commit: `6f3ee1c02955fa6c50913e8f598ac33904b2bede`. selector와 실제 PID cwd가 일치한다.
- 실제 소비 bundle SHA256: `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`. `data/runtime/mechanistic_entry_policy/consumed/2026-10-08/206123.json`에 `actual_pid_consumed=true`가 있다.
- 상시감시: 삼성전자 `005930`, 두산에너빌리티 `034020`, HPSP `403870`, 알테오젠 `196170`, 주성엔지니어링 `036930`. 로그의 `WATCHING=5 / HOLDING=0`은 Main 관리 상태이며 계좌 전체 잔고가 0이라는 뜻이 아니다.
- 첫 루프 `84.111초`는 제외한다. 보수적으로 14:30 이전도 전부 제외하고, 첫 사후 snapshot `14:30:49.182739`의 누적 histogram/counter를 기준값으로 차감한다. 의도된 sleep을 제외한 `loop_work_warm` 작업 시간을 분석한다.
- 실시간 수집은 기존 로그·procfs 읽기, WS 파일 60초 표본, CPython frame 메타데이터의 비정지 읽기로 제한했다. frame 읽기는 비원자적이며 오류·표본 누락을 보존했다. 스택 빈도는 CPU 시간 비율이 아니다.
- 별도의 compact 장중 채택 작업이나 dirty workspace 변경을 이 release의 적용 증거로 사용하지 않는다.

## 최종 수치

수집기는 15:00:00에 종료했고, PID와 start ticks는 종료 표본 및 15:00:43 대조에서도 동일했다. 루프/HTTP 마지막 성능 snapshot은 **14:59:25.121318**이다. 따라서 아래 누적 차이는 마지막 35초의 모든 루프를 포함한다고 주장하지 않는다. procfs와 WS는 15:00 경계 표본까지 수집했다(WS 표본 15:00:00.011은 경계 읽기이며 원천 snapshot 생성은 15시 이전).

| 항목 | 워밍업 제외 관측 결과 |
|---|---:|
| 평가 작업 루프 | 849회; 5초 초과 **11회 / 1.30%**; 10초 초과 1회 |
| 작업 시간 p95 / p99 | **2초 초과~3초 이하 / 5초 초과~10초 이하** |
| 14:30:49~14:39:57 | 294회, 5초 초과 0회 |
| 14:39:57~14:44:03 (ENTER/실패 발생 창) | 112회, 5초 초과 4회 |
| 14:44:03~14:59:25 (AI 비활성화 이후 창) | 443회, 5초 초과 **7회** |
| 상시감시 machine capture / attempt trace join | 56회 / 56회; BLOCK 49, ENTER_NOW 7 |
| ENTER_NOW 7회의 AI 결과 | WAIT 5, DROP 2; provider 호출 2, 미호출 5 |
| async 준비/commit | preparation queue/service, source/capacity prepare, main commit 모두 0 |
| Kiwoom physical HTTP | started=terminal=response **1,097회**; timeout/exception/inflight_unknown 0 |
| HTTP source-only / runtime-required | 697 / 400회 |
| ka10080 분봉 HTTP | probe **400회** + Main **116회** = 516회, 전체 HTTP의 47.0% |
| ka10080 logical demand / REST 유지 | 첫 기준 snapshot 이후 256 / 256; WS 대체 선택 관측 없음 |
| WS 경계 포함 파일 표본 | 17개; capture lock **35.864~321.281ms** |
| WS 파일 생성→파일 읽기 age | 0.079~1.130초 |
| 5종목 executable quote age 최대 | 삼성 555ms, 두산 554ms, HPSP 1,123ms, 알테오젠 1,278ms, 주성 731ms; native quote limit 3,000ms 이내 |
| 완료 분봉 writer loss / projection error | 모든 파일 표본에서 0 / 0; 기존 item rejection 계수는 별도 보존 |
| Main 평가 / Telegram / tick dispatch CPU | 1코어 기준 **24.75% / 22.09% / 15.54%** (14:37:59~15:00 thread tick 차이) |

HTTP는 minute bucket의 상한 512에 도달했으므로 마지막 snapshot만 사용하지 않았다. 모든 저장 snapshot에서 동일 minute/API/owner/request class/code/origin digest 키의 최신 계수를 합쳐 579개 키를 보존했다. `started = response + timeout + exception + inflight_unknown`을 검증했다. client physical 시도/페이지 기준이며 broker server receipt는 관측되지 않는다.

마지막 성능 snapshot에서도 provider transport 누계는 2회, response validate / main commit / submit guard / order acknowledgement는 0이었다. 14:43:58 disable 이후 복구나 추가 provider 호출 증거가 없다. 15시까지 수집한 exact attempt 증거에도 ENTER_NOW는 위 7회다. ingress ready 483 / claimed 13은 누계 진단값이며 적격 기회 483건을 뜻하지 않는다.

동일 사후 구간의 WS lock 관측 108,657개에서 50ms 초과 wait는 1,763개, hold는 191개였다. histogram은 `summary.json`에 보존했다. 파일 표본의 호가 freshness는 snapshot producer 기준이며, 파일을 읽은 시각의 추가 age와 동일하지 않다. registration 증거는 `local_sent_registry_not_broker_ack`이므로 broker ACK나 모든 packet 무손실을 입증하지 않는다. 프로세스 `/proc/io`의 write bytes는 관측 창에서 약 2.76GB 증가했지만, 전부 WS/trace 비용 또는 디스크 포화라고 귀속할 증거는 없다.

percentile은 누적 histogram 차이의 nearest-rank 구간이다. 정확한 interval p95/p99 값이 없어 구간을 표시하며, 누적 또는 rolling percentile을 서로 차감하지 않는다. HTTP 구간은 14:30 분부터 마지막 15:00 이전 성능 snapshot까지로, 루프 구간과 첫 49초가 다르다. 응답 도착은 broker 서버 처리 성공·payload 의미 유효성·주문 체결 증거가 아니다.

## 우선 병목과 수리 방향

### P0: 실제 Main 상시감시 호출에서 coordinator 누락

배포된 `src/engine/kiwoom_sniper_v2.py:16115`의 일반 WATCHING 호출은 `scanner_async_eval_coordinator`를 전달하지 않는다. 같은 파일의 wrapper `:1097` 기본값은 None이다. `src/engine/sniper_state_handlers.py:61542`는 runtime에서 coordinator를 찾고, `:61561`은 없는 경우 `not_enabled`를 반환한다. 상시감시도 이를 거쳐 기존 동기 AI 경로로 내려간다. coordinator를 생성한 사실만으로 실제 호출 연결을 입증할 수 없다.

자연 증거: native claim과 ENTER_NOW가 있었는데 `preparation_queue / preparation_service / source_prepare / capacity_prepare / main_commit`은 0이다. 이 계수만으로 결론 내리지 않고 위 실제 caller→wrapper→handler 연결과 함께 판정했다. 신호 생성에서 machine capture까지 1.086~3.630초가 이미 소모됐다. provider 호출 두 번에서 남은 budget은 2,538ms와 938ms였다.

다음 작업: 기존 coordinator를 실제 상시감시 Main caller에 전달하고 원래 native claim의 generation·deadline을 유지한다. 준비 worker에는 broker/state 변경 권한을 주지 않고 Main commit에서만 재검증한다. 종료 시험은 실제 `run_sniper → handle_watching_state` 호출을 거쳐 준비 계수가 발생하고, 동기 fallback·중복 provider·late commit·claim 시간 갱신이 없음을 입증해야 한다. helper 단위 fixture 통과만으로 닫지 않는다.

### P0: 원천 경로 변경이 provider 연속 실패로 집계됨

동일 PID 오류와 exact attempt join을 확인한 순서는 다음과 같다.

| 시각 KST | 종목 | 원인 | provider 호출 | 연속 실패 |
|---|---|---|---|---:|
| 14:40:22 | 주성엔지니어링 | HTTP wall deadline; budget 2,538ms, provider 2,715ms | 있음 | 1 |
| 14:40:52 | 주성엔지니어링 | `reversal_signal_path_changed` | 없음 | 2 |
| 14:41:18 | 주성엔지니어링 | `reversal_signal_path_changed` | 없음 | 3 |
| 14:41:42 | 주성엔지니어링 | HTTP wall deadline; budget 938ms, provider 921ms | 있음 | 4 |
| 14:43:58 | 알테오젠 | `reversal_signal_path_changed` | 없음 | 5; 엔진 비활성화 |

938ms budget 사례는 provider 시간만으로 초과를 설명할 수 없다. 로컬 준비·전체 deadline도 포함되므로 921ms를 938ms보다 크다고 해석하지 않는다. 두 provider 시도는 각각 physical attempt 1회이며 caller의 `future_cancelled=false`를 보존한다.

`src/engine/ai_engine_openai.py:10758` generic exception 처리는 `entry_machine_input_deadline_*`만 별도 반환하고, 다른 경로 변경은 `:10765`에서 실패 계수에 더한다. `:2197`에서 5회면 `ai_disabled=True`가 된다. 이 release의 해당 클래스에는 init의 False와 disable의 True 외 재활성화 대입이 없다. 14:44:08 및 14:44:19 알테오젠 ENTER_NOW는 `AI 엔진 일시 중단 (연속 실패)`로 DROP, `provider_called=false`였다. 종료까지 복구 증거가 있는지는 최종 수치와 계수로 구분한다.

다음 작업: native/source eligibility 종료와 실제 provider/transport 실패의 책임을 분리한다. 경로가 바뀐 신호는 계속 fail closed 처리하되 provider 실패 차단기를 소모하지 않도록 해야 한다. native guard, provider circuit guard, original deadline, late physical completion 보존을 함께 검증한다. 단순 실패 계수 초기화·5초 확대·API키 변경·재기동으로 정상화 판정을 하지 않는다.

### P1: 변경 없는 소유권 저널도 반복 전체 복사·환산

`src/trading/order/owner_custody_registry.py:214`는 journal signature cache hit에도 전체 `deepcopy`를 반환한다. `native_owner_contract:1923`은 journal을 읽고 전체 intent 상태를 다시 환산한다. Main WATCHING의 manual exclusion/기존 management disposition 확인이 `decision_activation_matches:2438`를 통해 이를 호출한다.

14:39, 14:44, 14:55의 세 비정지 스택 표본에서 Main 평가 TID `206251`의 `native_owner_contract` 및 `_read_locked` 경로를 반복 확인했다. 마지막 표본에서는 성공 관측 59개 중 19개가 native owner contract, 17개가 full journal read/copy를 포함한다. 함수 집계는 서로 중복되며 정확한 전체 루프 기여율은 아직 측정하지 않았다.

별도 읽기 전용 복사 microbenchmark: journal 1,904,922bytes / 1,489events, 20회 deepcopy p50 18.456ms, p95 18.859ms. 이는 offline copy-only 비용이며 실제 lock 대기·reducer·디스크 비용을 포함하지 않는다.

다음 작업: 기존 registry 안에서 검증된 immutable journal generation과 symbol/owner별 파생 상태를 재사용한다. 주문/intent 변경 시 정확히 무효화하고 manual veto·역사적 owner attribution을 보존한다. 종료 시험은 같은 generation 재조회 시 전체 복사/환산 감소, generation 변경 즉시 반영, 오염된 journal fail closed, Main/manual custody parity다. retired episode holdings를 삭제하거나 Main 자동 매도 대상으로 채택하지 않는다.

### P1: WS 공유 lock 안의 full-history snapshot 복사

`src/engine/kiwoom_websocket.py:2840`은 shared snapshot lock을 잡은 상태에서 pending 종목 모두에 `_snapshot_target(..., _defer_finish=True)`를 수행한다. `:2246` snapshot은 full-history copy를 포함한다. JSON serialize를 밖으로 옮겼어도 freeze/copy 자체는 lock 안에 남아 있다. dashboard writer도 lock 안에서 전체 target을 freeze한다.

세 스택 창의 tick dispatch TID `206286`에서 snapshot copy/lock 경로를 반복 확인했다. WS 파일 표본에서 capture lock은 최대 321.281ms였다. 계측 결과가 호가 전체 단절을 입증하지는 않지만, 수신·평가가 함께 쓰는 lock의 반복 비용으로 개선을 제한한다.

다음 작업: full-fidelity 원천 journal은 유지하면서 실제 소비 목적에 맞는 불변 projection과 짧은 freeze 경계를 설계한다. mutable reference를 lock 밖으로 유출하거나 callback history를 조용히 줄이면 안 된다. 종료 시험은 exact item/route/transport epoch·raw provenance·consumer 독립성·writer loss parity와 같은 부하에서 lock wait/hold histogram 감소다.

### P1: 430개 완료 분봉 계약 때문에 REST 유지

`src/engine/scalping/entry_candle_context.py:364`는 요청 limit과 `SOURCE_BAR_LIMIT=430` 중 큰 값을 요구한다. `src/engine/scalping/multi_timeframe_context.py:26`이 이 floor의 owner다. session WS completed-bar projection이 430개를 갖추지 못하면 REST 유지 경로를 선택한다. zero-base probe가 40개를 요청해도 같은 helper의 430개 계약을 적용받는다. 14:23 시작한 현 PID의 session WS 이력만으로 이 요구를 만족할 수 없다.

자연 증거: `ws_selected_http0`가 관측되지 않았고 ka10080 분봉 HTTP 중 source-only probe 비중이 크다. REST response 계수가 정상이어도 반복 source 조회가 사라진 것은 아니다. physical HTTP는 continuation 페이지를 포함하므로 logical demand와 같은 숫자로 비교하지 않는다. snapshot 중간에는 logical demand/REST 선택의 계수 차이가 1일 수 있어 미종료 시도나 계측 경계도 보존한다.

다음 작업: exact route/session 계약을 갖춘 역사 분봉 seed와 WS 완료 분봉 continuation을 연결하고, probe/Main의 목적·완료봉·generation이 같은 경우만 캐시 공유한다. 종료 시험은 기존 MTF source parity와 같은 demand에서 `ws_selected_http0` 실제 증가, physical 페이지 수 감소, source gap/REST 복구의 명시적 이유다. 430 floor 완화나 seed 없는 WS 승격을 성능 수리로 포장하지 않는다.

### P2: Telegram polling의 SQLite cache 비용

TID `206248`은 반복 `telebot.get_updates → requests_cache → sqlite.__getitem__` 스택과 상당한 CPU를 보였다. 이는 Kiwoom REST나 OpenAI provider 경로가 아니다. 현재 notify 호출은 long polling 설정이므로 poll 주기만으로 원인을 단정하지 않는다. cache patch의 실제 설치 주체와 polling 응답 캐시 의미는 이번 조사에서 확정하지 못했다.

다음 작업: third-party/global session patch의 생성 주체를 좁혀 확인하고 Telegram 통신과 시장/API transport의 cache 경계를 검증한다. 종료 시험은 notifier 전달·long polling 의미 보존, cache 조회 비용 및 관련 CPU 감소다. cache/라이브러리 설정을 이번 관측 중 변경하지 않았다.

## 개선 효과의 인정 범위

| 층 | 이번 관측에서 인정한 상태 |
|---|---|
| 구현·선택·PID 소비 | v3 release/PID/bundle 일치. 별도 compact 작업의 적용은 입증하지 않음 |
| 상시감시 async 준비 | actual caller coordinator 누락; 자연 준비/commit 계수 0 |
| 기계판정 | exact-PID capture와 attempt trace join으로 분모 확인 |
| provider | 호출 2회 이후 실패 차단; 로컬 경로 변경 3회가 실패 계수에 혼입 |
| WS 원천 | 제한된 표본의 호가 신선도와 writer 계수 확인; 모든 packet 수신/무손실 또는 broker ACK를 입증하지 않음 |
| REST 절감 | 분봉 WS 대체는 관측 안 됨. 배포 전 동일 부하 HTTP 기준이 없어 절감률은 null |
| submit/fill/경제성 | 위 ENTER_NOW 사례에서 PASS/submit 진입 증거 없음. 계좌 전체 주문 census·체결·비용조정 수익은 조사 범위 밖 |

ready 계수는 ingress에서 본 native-ready membership이며, 원래 claim filtering 전의 값이다. ready−claimed를 놓친 적격 진입 수로 해석하지 않는다. 경로 변경과 source invalid는 provider 미호출로 구분하며 모두 5초 만료로 합치지 않는다. Main 평가 작업, HTTP 응답, 실제 체결 및 경제적 효용을 분리해 보고한다.

## 증거·기존 실행 owner·검증

진단 자료: [summary.json](../../tmp/main-pid-206123-monitor-20261008-1500/summary.json), [monitor manifest](../../tmp/main-pid-206123-monitor-20261008-1500/monitor_manifest.json), [performance snapshots](../../tmp/main-pid-206123-monitor-20261008-1500/performance.jsonl), [PID observations](../../tmp/main-pid-206123-monitor-20261008-1500/proc_observations.jsonl), [WS observations](../../tmp/main-pid-206123-monitor-20261008-1500/ws_observations.jsonl), [exact attempt evidence](../../tmp/main-pid-206123-monitor-20261008-1500/attempt_observations.jsonl), [source read byte bounds](../../tmp/main-pid-206123-monitor-20261008-1500/attempt_source_reads.jsonl), [14:55 stacks](../../tmp/main-pid-206123-monitor-20261008-1500/stacks-1455.jsonl), [offline copy cost](../../tmp/main-pid-206123-monitor-20261008-1500/owner-journal-copy-cost.json). tmp 자료는 장기 보존을 보장하지 않으며, manifest의 파일 hash는 봉인 시점의 진단 복사본에만 적용한다.

기존 실행 owner는 [10월 8일 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry`이다. 이번 진단은 별도 OPEN owner나 완료/승인 receipt를 만들지 않는다. [v3 구현 리뷰](main-rest-ws-latency-implementation-review-2026-10-08.md), [REST/WS 개선 계획](../proposals/main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md), [평가루프 개선 계획](../proposals/main-evaluation-loop-latency-remediation-plan-2026-10-08.md), [compact 장중 채택 계획](../proposals/main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md)과 연결하되, 기존 완료 리뷰의 역사적 증거를 현재 실제 호출 연결의 입증으로 대체하지 않는다.

문서 self review → 수치/호출 경로 보완 → 재리뷰를 완료했다. 로컬 링크 14개, histogram/HTTP 계수 보존식, print-only backlog parser(21개 항목; 기존 실행 owner 1개), diff whitespace 검증을 통과했다. 문서/진단 전용 작업이므로 trading pytest, provider/broker 호출, 보고서 재생성, 외부 Project/Calendar sync, 배포·재기동은 수행하지 않았다. 배포 전 HTTP 비교 분모, 전체 packet 원천 결손, 반복 비용의 정확한 wall-time 기여율은 잔여 미입증 사항이다.
