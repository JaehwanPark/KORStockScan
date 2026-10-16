# Main 기동 검증·정규 모니터의 반복 I/O 추가 개선계획 — 2026-10-14

상태: **최종 선택 릴리스 기준 재검토·구현·반복 리뷰 및 표적 회귀 완료.** 사용자 후속 지시로 구현 범위가 열렸다. 기준은 `5fb4c0a33a9df2b26e5fab4740576ce746a8cc93`이며, 09:29 KST selector는 `main_stopped_no_start_requested`/`actual_pid_consumed=false`였다. 격리 작업본에서 구현하며 선택 릴리스·Main 정지 상태를 보존한다. 구현/시험 결과는 [구현 리뷰](../audits/main-io-residual-implementation-review-2026-10-14.md)가 소유하고 배포·자연 성능 수용은 구별한다.

## 1. 판단과 확인한 범위

우선순위는 **정규 모니터의 대용량 원천 재검증 제거 → 기동·배포 단계의 중복 전체 검증 축소 → 후속 프로세스 자원 우선순위 통일**이다. 실행 중인 Main을 줄이거나 경보 임계치를 올리는 조치로 대체하지 않는다.

근거는 [08:45~08:52 점검 결과](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/result.json), [첫 연속 표본](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/samples.jsonl), [정규 배치 연속 표본](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/followup-samples.jsonl), [열린 원천](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/monitor-open-files.json), [프로세스 목록](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/process-inventory.json), [소비 코드·PID](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/runtime-evidence.json)다. 모두 KST 관측 시점의 기록이며 미래 상태를 보증하지 않는다.

| 관측 | 증거 | 판단·제한 |
|---|---|---|
| 08:44 경보 | 08:44:01 host iowait 39.04%; 기동 bootstrap·intraday consumption 실행 구간 | 경보를 출력한 `bot_main`이 전부 원인이라는 뜻은 아니다. 해당 분의 정확한 PID별 비중은 미확정이다. |
| 08:46~47 재현 | iowait 최대57.54%; Codex 자식 PID3855174 bootstrap verify, PID3855393 handoff verify가 약208~231MiB/s 읽기 | 배포 후 별도 전체 검증이 실제 디스크 부하를 만들었다. 부모의 종료 자식 I/O 회수분을 순간 읽기나 독립 기여로 합산하지 않는다. |
| 08:50 정규 배치 | 08:50:01 START→08:51:19 DONE; monitor PID3856600 약218~231MiB/s 읽기 | 열린 `pipeline_events_2026-10-13.jsonl`은7,394,107,688 bytes(약6.89GiB). 한 회 직접 관측과 매5분 새 프로세스/전체 검증 코드 경로를 함께 근거로 삼는다. |
| 배치 종료 후 | 08:51:30~08:52:00 iowait1.43~1.98%; 같은 Main PID 유지 | 평상시 회복과 반복 원인의 해소는 별도다. |
| 기존 개선 포함 | 선택 `01d9fefa4234b421fb0b2c74683562aa8a9c7358`, Main3854164/start18431371; 기존 I/O13개 파일 SHA 모두 동일 | [10/13 개선](/home/ubuntu/KORStockScan/docs/proposals/main-io-contention-and-repeated-validation-remediation-plan-2026-10-13.md)의 누락·롤백으로 해석하지 않는다. 새로 확인한 호출 경로만 보완한다. |
| 프로세스·용량 | Main1, 좀비/퇴역 worker0; IDE RSS합계916.4MiB/swap1486.0MiB; 가용 RAM5944.9MiB, 디스크약58GiB | RSS합계는 PSS가 아니다. swap 잔량과 현재 swap I/O를 구분한다. 불필요한 대형 상시 daemon은 확정하지 못했다. |

기존 observer delay 재사용·Sentinel 압축 색인·summary projection의 완료 검증은 [구현 리뷰](/home/ubuntu/KORStockScan/docs/audits/main-io-contention-and-repeated-validation-implementation-review-2026-10-13.md)가 소유한다. 최초 색인 비용, 논리 읽기79.3% 감소와80% 목표 미달, 다음 자연 수용은 그대로 보존한다.

## 2. 실제 producer → consumer 경로와 새 결함

| 경로 | 현재 동작 | 이번 개선 경계 |
|---|---|---|
| [Sentinel wrapper](../../deploy/run_buy_funnel_sentinel_intraday.sh) → Sentinel → [submission monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py) | flock으로 중첩을 막고 매5분 새 Python 실행. `nice/ionice/taskset`은 Sentinel `cmd`에만 적용되며 성공/실패 후속 monitor 호출에는 동일 prefix가 없다. | 정상 monitor와 `--source-only` 경로까지 우선순위·예산·terminal을 일치시킨다. cadence·알림 의미를 보존한다. |
| `machine_semantics` → `runtime.load_effective` → `_reversal_selection_receipt` → current/frozen family 검증 | 최근30분8MiB payload tail 외에 선택 정책과 관측에 등장한 frozen bundle 원천 전체를 검증한다. tail 제한은 전이된 원천 읽기까지 제한하지 않는다. | 현재 bundle뿐 아니라 최근 관측의 모든 서로 다른 frozen bundle도 다룬다. 첫 selection 함수만 cache로 바꿔 전체 읽기가 사라졌다고 주장하지 않는다. |
| 정상 monitor의 나머지 호출 → `entry_execution_tuning_semantics`/`source_gap_semantics` | entry split·delay·cancel-wait receipt와 bootstrap delay selector를 별도 확인한다. source gap은 당일 bounded probe/trace/pending을 읽는다. `--source-only`는 source gap만, 별도 `--delay-source-only`는 독립 delay cursor를 소비한다. | 작은 receipt 조회와 현재 source 확인은 매회 유지한다. delay selector의 전이 검증까지 비용 목록에 포함한다. source-only를 machine 검증이 있는 정상 실행과 같은 비용·의미로 집계하지 않는다. |
| [native loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py) → [v6](../../src/engine/scalping/continuous_reversal_policy_v6.py)/v4 → [code handoff](../../src/engine/scalping/reversal_code_handoff.py) | `_cached_source_hash`는1024개/1MiB의 프로세스 내 digest cache다. 원천·코드·selector·handoff dependency를 검사하지만 다음 cron 프로세스에는 남지 않는다. | report-only caller에 한정한 프로세스 간 재사용. 기존 live loader/PREOPEN/일반 CLI의 기본 검증은 변경하지 않는다. |
| monitor 상태·terminal → wrapper → [cron detector](../../src/engine/error_detectors/cron_completion.py)/[freshness detector](../../src/engine/error_detectors/artifact_freshness.py) | monitor의 blocking `LOCK_EX`가 검증·알림·state/latest/dated publication 전체를 감싼다. `issues`가 비면 pending을 제거하고 active를 historical로 전환하는 attach 경로가 있다. monitor exit0 뒤 wrapper는 cooldown/DONE을 기록한다. | deferred를 빈 정상 결과로 넘기지 않는다. 외부 상태 잠금부터 예산을 적용하고, 실행 완료·관측 가능성·알림 전송을 별도 terminal 필드로 연결한다. |
| [ordered driver](../../src/engine/automation/ordered_intraday_deploy.py) → [run_bot](../../src/run_bot.sh) → [handoff](../../src/engine/automation/intraday_release_handoff.py)/[bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py) | predecessor, candidate, launcher prestart, new PID 기록, consume, verify, driver attest가 별도 실행/중첩 검증을 한다. `verify_pid_consumption`은 handoff 확인 뒤 bootstrap도 다시 확인한다. | 같은 단계·같은 세대의 원천 내용 읽기를 공유하되 각 native verifier의 독립 semantic·identity 검사는 모두 실행한다. 전체 배포를1회 검증으로 축소하지 않는다. |

작업본에는 다른 장후·REST·연구 변경이 있다. 구현 착수 시 그때의 selected root/commit·실제 PID·해당 파일 SHA를 다시 고정하고 격리 작업본에서 이 범위만 다룬다. 문서 근거를 만들기 위해 대형 verifier나 원천 replay를 재실행하지 않는다.

## 3. RIO0 — 검증 경계·비용을 먼저 고정

1. native 호출마다 `phase`, caller role, release/root, target/source/effective date, bundle/manifest/handoff SHA, dependency 수·크기, cold/full/reuse 여부와 wall/CPU/RSS/논리·물리 I/O를 남긴다. 단계별 native full 호출 수와 실제 파일 read를 구분한다.
2. `/proc` PID+start ticks로 leaf 작업을 계측하고 parent/child 합산과 종료 자식 회수 중복을 제거한다. 누락 PID는0비용으로 대체하지 않는다. 디스크는 물리 장치1개를 기준으로 하고 swap-in/out·PSI·queue·await를 보조 관측한다.
3. 비용 계측은 기존 진단/검증 receipt에 연결한다. 새 상시 daemon, Main tick마다 원천 조회, 주기적인 대형 probe는 만들지 않는다. 진단 metric은 report-only이며 주문·정책 승인 근거가 아니다.
4. 구현 전 호출 목록에 정상/source-only/delay-source-only, current/historical bundle, split/delay/cancel-wait, 기동의 prepare/consume/verify/attest를 각각 기록한다. 각 항목에 full-content read, 작은 fresh 검사, state mutation, terminal consumer를 연결한다. 일부 경로가 계측되지 않으면 전체 읽기 제거로 수용하지 않는다.

## 4. RIO1 — 정규 모니터의 검증 결과 재사용 (최우선)

### 4.1 최종 릴리스 재검토에 따른 구현 설계

선택 결과 전체를 저장하는 초안은 **큰 파일의 실제 SHA-256만 저장하는 방식**으로 바꾼다. 정책 선택·current/optional 파일 탐색·directory membership·env/날짜·PID·영수증 semantic 검사는 매번 native 코드가 수행한다. 따라서 재사용한 PASS나 projection이 새 조건을 가리는 경로가 없다. 잘못된 원천의 실제 digest를 다시 사용하더라도 기대 SHA와의 비교는 계속 실패한다.

- 소유 모듈은 `src/engine/infrastructure/validation_digest_session.py`다. observer와 transition이 공유하는 파일 검증 비용 계층이며, monitor 시간 제한은 `src/engine/monitoring/observation_budget.py`가 소유한다. `src/engine` root는 늘리지 않는다.
- opt-in 호출만 `ContextVar`로 digest session을 연다. 기본 library/일반 `--verify`/PREOPEN/live 매매 호출은 원 full 경로다. env만으로 native reader를 바꾸거나 monkeypatch하지 않는다.
- native 연결점은 `mechanistic_entry_runtime_policy._cached_source_hash`, `continuous_reversal_postclose.file_hash`, `holding_window_generation.byte_generation`이다. 마지막 경로가 delay ledger의 같은 historical raw를 다시 읽는 점도 최신 코드에서 확인했다. 작은 파일 JSON/기대 hash·부재·목록·누적 compact hash는 원래대로 읽는다.
- monitor 정상/source-only 모드 모두 fresh source/incident를 계산한다. digest가 대신할 수 없는 parser·별도 구형 origin subprocess는 full이며 비용·한계를 숨기지 않는다. 원 정책·종목·시장·candidate·hard safety 범위는 유지한다.

### 4.2 파일 digest의 필수 계약

| 항목 | 구현 계약 |
|---|---|
| namespace | `data/runtime/validation_digests/{observer,transition}/`; schema/role/lexical 및 resolved root/boot ID/target date/code root·검증 코드 hash 결속. observer와 transition 저장 영역은 서로 사용하지 않는다. |
| 내용 | 1MiB 이상인 동일 local data mount의 파일만 대상. 실제 내용 SHA와 lexical/resolved 경로, dev/inode/size/mtime_ns/ctime_ns/mode/uid, 부모·symlink identity를 저장한다. SHA만 공유하고 모든 native 기대값 비교는 다시 실행한다. |
| 신뢰 | ext 계열/xfs/btrfs/tmpfs/overlay와 같은 local filesystem만 사용한다. metadata는 내용 전체 재해시와 동일한 암호학적 보증이 아니다. 신뢰하는 native writer/동일 OS·소유자 경계이며 관리자에 의한 파일·cache 변조 방어라고 주장하지 않는다. 부적격 storage는 full fallback이다. |
| 저장·상한 | private directory0700/file0600, 비symlink·regular file·owner·schema·payload digest 검증, atomic replace/fsync. 역할별32 generation·generation512KiB·4096 entries 이내이며 초과는 truncate된 proof로 쓰지 않는다. 정상 warm hit는 store를 다시 쓰거나 fsync하지 않는다. |
| 수명 | observer 최대6시간, transition120초. 파일 hash를 실제 구한 시각을 유지하며 hit로 TTL을 연장하지 않는다. day/boot/generation 변경은 별도 namespace다. |
| 비용·실패 | full/reused count·bytes, role/generation, PID, wall, thread I/O delta, process peak RSS를 기록한다. 해시 hit가 semantic PASS나 실제 개선 완료를 뜻하지 않는다. 저장 손상/ENOSPC는 full fallback이며 changed source는 원 native 오류다. |

### 4.3 변경·실패·동시성

1. 파일/경로 identity를 읽기 전후 확인한다. append/truncate/같은 크기 rewrite/mtime 복원/rename/삭제/권한·symlink 변경은 full 재검증 또는 native 오류다. 새 current/후보/설정은 cached selection이 없으므로 매번 native 선택에 반영된다.
2. 같은 role의 store lock 대기는 최대2초다. Main/주문/필수 기동과 observer 잠금을 공유하지 않는다. lock inode를 삭제하지 않고 descriptor를 자식에 상속하지 않는다. 독립 CLI·구형 origin 실행에는 cache 사용을 강제하지 않는다.
3. monitor의 단일120초 monotonic 예산은 잠금·단계 계산·출력과 회수를 포함한다. 계산은 마지막15초를 publication/알림에 남기며 알림은 기존10초 transport 제한에 필요한12초가 남을 때만 시도한다. wrapper는 전체180초 내 각 자식과 마지막5초 회수를 묶는다. source-only fallback에도 같은 남은 예산을 사용한다.
4. 시간 초과는 일반 parser의 `except Exception`에 먹히지 않는 전용 예외로 반환하고 `validation_deferred`/exit75를 기록한다. 같은 실행이 full을 반복하지 않는다. 전체 native PASS를 저장하는 방식의 실패 backoff는 채택하지 않는다. 이미 완료된 파일 digest는 저장할 수 있지만 실패한 내용 읽기와 미완료 semantic 판정은 성공 기록이 아니다.
5. 다음 정상5분 슬롯에서 재평가한다. 연속2슬롯 보류 또는 source age600초 초과는 자연 수용 실패다. 실제 source 시각·first_seen을 새 출력시각으로 갱신하지 않는다.

### 4.4 상태·알림·완료 계약

- **scope별 `validated`, `invalid`, `unobservable/deferred`를 구별한다.** timeout을 `issues={}`인 정상 결과로 attach하지 않는다. 새롭게 입증한 issue는 반영하되 검증하지 못한 scope의 pending/active·first_seen·last_seen·notified_status·history·cursor를 보존한다. 보류 시각은 별도 진단이다. 기존 pending의 시간을 초기화하거나 active를 historical/recovered로 내리지 않는다. 다른 fresh scope의 정상 전이는 계속 수행한다. 현재 하나의 incident key로 합쳐진 machine/entry-execution 상태는 일부 scope 정상만으로 해소하지 않으며, 원 incident의 전체 범위가 확인됐는지를 따로 판정한다.
- 미관측만으로 새 alert·recovery를 합성하지 않는다. 이미 pending인 알림의 기존 retry/idempotency는 유지한다. `pending → deferred → 같은 issue 재관측`은 최초 관측시간을 유지하고, `active → deferred`는 기존 전송 상태를 보존한다. scope 전체가 검증됐을 때만 원래의 정상/해소 전이 규칙을 적용한다.
- 현재 blocking state lock도 최대2초의 비차단 재시도로 바꾼다. 미획득 실행은 active writer의 state/latest/dated 파일을 쓰거나 lock inode를 지우지 않고 자기 실행 terminal만 남긴다. 획득한 한 writer가 기존 state 전이·알림·publication을 소유한다. 계산 중 잠금을 풀었다가 오래된 state를 덮어쓰는 방식은 채택하지 않는다. 알림 transport와 정리 시간도 남은 예산에 포함한다.
- state/latest/dated가 서로 다른 시점에 교체될 수 있으므로 동일 `run_id`, target date, generation과 개별 publication 결과를 기록한다. 중간 write 실패를 전체 publication 성공으로 만들지 않는다. wrapper는 자기 자식의 작은 structured terminal을 확인하며, 이전 실행의 latest/mtime를 성공 근거로 쓰지 않는다.
- `execution_status`(completed/deferred/failed), `semantic_status`(validated/partial/unobservable), `notification_status`를 분리한다. 정상 valid-empty와 실제 issue가 있는 정상 완료는 실행 실패가 아니다. 기존 monitor exit0를 모든 semantic PASS나 Telegram 전달 성공으로 해석하지 않는다. resource budget 때문에 필요한 검증을 못 했거나 state/publication이 실패하면 성공 cooldown을 갱신하지 않는다.
- 로그 marker를 임의로 새로 만들어 detector가 놓치게 하지 않는다. wrapper·cron/freshness detector·운영 문서가 같은 terminal schema를 소비하도록 함께 수정·시험한다. `[DONE]`은 실행 완료 의미를 유지하되 부가 semantic 상태와 reason을 표시하고, deferred/failed는 detector의 명시적 비성공 상태에 매핑한다. Sentinel 실패 뒤 source-only 성공은 원 실패를 가리지 않는다. 알림 retry/configuration 문제는 독립 상태로 남기고 중복 전송을 만들지 않는다.

## 5. RIO2 — 기동·배포 검증의 단계 내 공유

### 5.1 필요한 단계는 유지

| 단계 | 반드시 새로 확인할 사실 | 공유 가능한 부분 |
|---|---|---|
| incumbent preflight | 현재 선택·실제 기존 PID/start/cwd·native 정책/env·원천·수동 custody | 현재 구형 predecessor는 full 유지. 새 candidate/launcher 호출부터 명시적 digest session 적용 |
| candidate prepare/prestart | 이전 worker 종료, selector CAS, reviewed code, 원 PREOPEN/정책 보존, 후보 handoff | 후보 세대에서 full로 확인한 불변 dependency digest. candidate publication 전후를 같은 상태로 취급하지 않는다. |
| new PID consumption | 새 PID/start/cwd/env 및 실제 manifest 소비, 원본 불변, 새 consumption receipt | post-launch 세대에서 검증한 frozen 내용 digest. consume·receipt 발행은 실제로 수행한다. |
| driver completion | launcher 성공, 정확히1개 Main, 현재 identity/selector/source 일치, 독립 bootstrap/handoff verify, stage terminal | 동일 post-launch 세대·새 PID의 원천 digest만 공유한다. launcher의 PASS를 driver의 독립 검사로 대체하지 않는다. |

1. `src/engine/automation`에서 단계별 내부 검증 API를 구성한다. context가 제공하는 것은 **성공한 full-content 검증에 결속한 digest 공급**이며 native verifier 전체 PASS가 아니다. caller별 check ID·입력·실패 사유·실제 실행 receipt를 기존 CLI와 대조한다. phase/source/PID가 명시된 opaque context만 받고 임의 `verified=True` 인자로 대체하지 않는다.
2. 동일 프로세스의 consume/verify는 context를 전달한다. launcher→driver처럼 프로세스 경계를 넘을 때에는 `data/runtime/validation_digests/transition`의 원자적 digest entry를 사용한다. schema·role·boot ID·transition ID·prestart/post-launch phase·code root/hash·날짜·PID/start/cwd와 파일별 identity를 재확인한다. 파일 내용 full hash 완료 전에는 해당 digest를 발행하지 않는다. 부재/목록/env와 정책 의미는 cache 밖에서 native 코드가 확인한다. 소유자·lexical/resolved 경로·비symlink·크기 한도·원 proof digest와 발행 전후 CAS를 확인하고, 저장된 digest만으로 발행자의 native 성공을 합성하지 않는다. 기본 수명은 해당 내용 해시 시작 시각부터 최대120초이며 hit로 연장하지 않는다. RIO1 cache는 입력으로 인정하지 않는다. 이는 native PASS proof가 아니라 명시적 CLI 검증 세션의 파일 digest 저장소다. native in-process hash cache와 같은 local 파일 세대 검출 신뢰를120초로 제한한다. admin 변조 방어·암호학적 immutable storage를 추가한 것으로 주장하지 않는다. 부적격 source는 full을 유지한다.
3. 파일 identity가 그대로여도 PID/env·현재 selector·lock/hold 소유·원 정책 보존은 그때마다 fresh 검사한다. source 변화·PID 재사용·expired proof·실패/누락 proof는 기존 full 경로 또는 해당 phase 실패로 처리한다. 같은 배포 안에서 재시도는 bounded이며 이미 stop/start한 단계를 무조건 반복하지 않는다.
4. 일반 CLI 단독 `--verify`, PREOPEN, 정책 apply·주문 guard는 기본 full을 유지한다. 이 계획은 기존 [릴리스 운영 계약](../runtime-release-routing.md)의 native predecessor/새 PID 수용을 생략하지 않는다. RIO2가 들어가는 변경 세트에서는 실제 변경된 내부 공유 방식과 operating/checklist owner를 함께 반영한다.
5. Codex 후속 확인은 해당 transition의 성공 proof·source generation·현재 PID를 우선 읽는다. 동일 단계/세대의 대용량 full 읽기를 결과 확인용으로 불필요하게 반복하지 않는다. 표준 native verify는 그대로 사용할 수 있다. 새 결함·정책/source/code/PID 변경으로 full이 필요하면 필요 근거와 실제 비용을 남긴다. 실패한 stage나 이전 날짜 PASS를 재사용하지 않는다.
6. bootstrap verify artifact·consumption receipt·selector PID 기록처럼 **정상 실행이 변경하는 출력**은 frozen 입력과 분리한다. 각 변경은 native caller가 수행하고 허용된 이전→다음 identity/hash·CAS를 기록한다. 넓은 output 경로 제외나 mutable 파일 무시로 무효화를 피하지 않는다. frozen 정책/source/code 변화는 새 generation이며 이전 proof가 만료된다. consumed/verified 기록을 cache에서 복사해 publication을 생략하지 않는다.
7. 새 PID consumption과 driver completion은 검사 단계가 달라도 동일 post-launch generation에서만 digest 공유가 가능하다. predecessor→candidate→new PID 경계를 넘어 PASS를 승계하지 않는다. ordered driver의 기존 detector lock 대기60초·개별 verifier120초·소비 대기150초를 유지한다. launcher 자체의 기존 기동 한계는 별도다. proof 만료에 따른 full fallback도 해당 단계의 남은 monotonic 예산 안에서 수행하며 대기/재시도로 원 마감시간을 연장하지 않는다. 실패가 Main 강제 종료나 자동 stop/start 반복 권한을 만들지 않는다.

## 6. RIO3 — 후속 monitor까지 자원 경계 적용

- wrapper의 동일 `nice/ionice/taskset` 정책을 Sentinel, 정상 monitor, `--source-only` monitor 모두에 명시적으로 적용한다. 기존 flock·5분 cadence·freshness≤600초·알림 suppression/idempotency·exit propagation을 보존한다. nice/ionice 설정만으로 실제 I/O 상한이 보장된다고 주장하지 않는다.
- cold 검증·수동 대형 진단을 동일 호스트에서 동시에 시작하지 않도록 report/진단 owner끼리 bounded admission을 적용한다. 실제 startup/ordered transition의 필수 검증은 진단 잠금을 기다리지 않는다. live 시장·주문·hard exit 작업을 배치 예산에 넣지 않는다.
- lock 충돌/timeout/child 실패/부분 관측은 start→wait/reuse/full→terminal에 구분해서 기록하고 §4.4의 상태 전이를 따른다. 성공 cooldown 파일은 요구된 하류가 정상 완료됐을 때만 갱신한다. 실패 fallback이 원 Sentinel 실패 코드를 덮어쓰지 않는지 검증한다. wrapper의 단일180초 cold deadline은 Sentinel·monitor·fallback·회수 전체를 포함하며 monitor에는 자체120초와 wrapper 남은 예산 중 작은 값을 전달한다. warm60초는 성능 목표이며 새 Main timeout이 아니다.
- 일반 worker의 `nice/ionice` 적용과 프로세스별 실제 priority를 검증한다. 후속 monitor에는 기존 Sentinel affinity 값을 적용하며 새 affinity 값이나 Main CPU pin을 도입하지 않는다. EBS 설정, cgroup I/O cap, cron 간격, 경보35% 상향은 이번 기본 구현의 전제로 삼지 않는다.

## 7. RIO4 — 프로세스 정리 후보

우선 live PID/start/cwd·systemd/cgroup·연결된 IDE/SSH 세션·cron/수동 작업 소유자를 확인한다. Main1개, 별도 Gunicorn master/worker3개, Postgres·nginx·SSM은 실제 owner가 있으므로 중복이나 퇴역 worker로 간주하지 않는다. 새 진단 명령이 자신의 자식 프로세스를 불필요 작업으로 판정하지 않게 한다.

사용하지 않는 IDE 세션/Pylance/Copilot은 사용 여부가 확인됐을 때 정상 종료 후보로 기록한다. `fwupd`·`ModemManager`·`multipathd`는 필요 기능/장치/접속 의존을 확인해야 하며, 당시 RSS합계약33MiB이므로 반복 원천 읽기 수리보다 우선하지 않는다. `swapoff`, page-cache drop, `kill -9`, DB/웹 임의 종료로 측정값을 낮추지 않는다. 이 문서는 정리 계획이며 서비스 삭제/disable을 실행한 기록이 아니다.

## 8. 검증과 수용 기준

### 8.1 의미·실패 회귀

- 정상 완료 입력의 cold/full 대 warm 출력은 selection, bundle/scope/attempt, source-invalid·required-feature·provider/submit/terminal, missing/censored/null, window coverage, incident/notification decision을 대조한다. 정상/source-only/delay-source-only 각 모드에서 baseline과 candidate의 실제 실행 scope가 같아야 한다. 시각/성능 metadata만 명시적 allowlist로 제외한다. 기존 보류 처리 결함을 고치는 실패 입력은 §4.4의 명시적 기대 전이와 별도로 대조하며, 옛 pending 삭제 동작을 parity 기준으로 삼지 않는다. count 일부만 같으면 PASS가 아니다.
- 현재+과거 복수 bundle, 정책 carry, date/boot rollover, native v4/v6 부모/code handoff, native default opt-out, cache 상한 초과, 같은 크기 rewrite/mtime 복원/ctime 변화, lexical alias·symlink 전환, raw→gzip 교체, 없던 current 생성·더 최신 directory 후보 추가·설정 변경, permission/ENOSPC/corruption/부분 publication/concurrent append/crash를 시험한다. 큰 파일 읽기의 연결점 밖에서 수행되는 I/O와 구형 origin subprocess full 비용도 별도로 확인한다.
- 상태 회귀는 pending→deferred→동일 issue, active→deferred, partial scope의 새 issue와 미관측 scope 보존, 정상 valid-empty, 알림 전송 실패/재시도, state lock 경합, lock FD 상속 차단, state/latest/dated 중간 write 실패를 포함한다. 보류로 first_seen/cursor를 잃거나 새 recovery·중복 전송을 만들면 실패다. 알림은 fake sender로 검증한다.
- deployment는 stage마다 결함 주입: 기존/새 PID 교체, start ticks 재사용, cwd/env/selector 변경, predecessor source 누락, proof 후 source 수정, expired/위조/다른 transition proof, 자식 실패, partial consume, 정상 output CAS 및 예상 밖 output 변경, 원 operator hold/lock 및 hard safety 보존. launcher PASS 뒤 driver에서만 보이는 결함도 독립 native 검사가 검출해야 한다. default CLI와 proof opt-in 모두 원 실패를 검출하고 검사 ID 누락이 없어야 한다.
- wrapper는 정상/실패/source-only 모두 priority 상속·bounded state/cache/admission 대기·공유 deadline·child 회수·terminal/exit/freshness·알림 중복0을 확인한다. cron/freshness detector가 같은 run_id의 deferred/partial/publication failure를 정확히 소비하는지도 시험한다. 신규 provider/실주문은 시험 방법으로 사용하지 않는다.

### 8.2 성능 목표 (아직 측정 완료 아님)

| 대상 | 수용 목표 | 증명 방법 |
|---|---|---|
| monitor 동일 frozen generation | 지원되는 동일 local 파일 세대의 warm에서 historical raw full read0회, monitor 전체 논리 읽기 baseline 대비≥90% 감소 | 전체 논리 읽기에는 current tail·작은 receipt·cache 조회도 포함하고 구성별 bytes를 병기한다. file별 open/read와 leaf I/O를 대조한다. cache 비대상/cold/deferred를 분모에서 숨기지 않고 발생 수·bytes·수용 실패를 별도로 보고한다. |
| 검증 공유 | 동일 phase/source generation의 공유 가능한 파일 내용 전체 읽기 최대1회; 모든 caller의 독립 semantic 검사 유지 | native 호출 수·semantic check ID·full-content pass 수를 각각 기록한다. native verifier 자체 호출1회로 축소하지 않는다. 공유 불가 파일과 fallback 비용을 공개한다. |
| 정규 wrapper | warm 총wall≤60초, peak RSS≤1GiB, source freshness≤600초 | Sentinel/monitor 합계와 단계별 시간. cold full 예산120초와 전체cold≤180초를 별도 확인한다. |
| 서버 경합 | 동등한 background 조건의10초 표본 p95<20%, 35% 이상2표본 연속 발생0 | 연속3개5분 슬롯 전체15분의 예정90개 표본과 실제 N·누락 수, worker 활성 구간의 N/p95/max를 각각 보고한다. idle 포함 수치만으로 수용하지 않는다. 해당 비교 구간에서만 유효한 목표이며 다른 reader/배치/swap 기여·혼합 부하·귀속 불가를 공개한다. |
| 자연 수용 | 적용 후 정규5분 슬롯 연속3회 terminal 정상, 의미/분모·source age 보존 | 실제 실행 슬롯을 owner에 기록.3회만으로 장기 p95를 주장하지 않으며 이후 누적 표본수·max·분위수를 분리한다. |
| Main 보호 | 같은 정상 attempt의 local 지연·timeout/censored·필수 receipt/guard가 악화하지 않음 | Main PID/source별 관측. 새로운 주문·경제성 floor를 이 I/O 수리의 승인 조건으로 추가하지 않는다. |

성능 baseline/candidate는 동일 frozen source manifest·코드 차이·host 조건·실행 순서·page-cache 상태를 기록한 비교쌍을 쓴다. 기존08:50 관측은 원인 근거이며 새 구현과 완전히 동등한 baseline으로 가장하지 않는다. warm parity와 read 감소가 주 수용 근거다. work 생략/deferred 증가, scope·종목·시장 축소, cache 삭제/drop으로 목표를 맞추면 실패다. 호스트 비교의 교란이나 표본 부족은 `performance_not_established`로 남기고 원인 확인에 필요한 비교만 수행한다.

구현 검증은 기존 `test_submission_bottleneck_monitor.py`, `test_mechanistic_entry_runtime_policy.py`, `test_runtime_policy_bootstrap.py`, `test_intraday_release_handoff.py`, `test_ordered_intraday_deploy.py`, `test_error_detector_cron_completion.py`, `test_error_detector_artifact_freshness.py`와 실제 영향 wrapper 시험을 선택한다. 새 cache/phase 시험은 `src/tests`에 둔다. 관련 Python compile, shell `bash -n`, diff 검사를 수행한다. 변경하지 않은 전체 매매 suite를 반복하지 않는다.

큰 실제 source 검증은 기존 측정 증거를 먼저 재사용하고, 필요한 동일 입력 비교만 조용한 허용 구간에1worker로 순차 실행한다. page cache를 지우지 않으며 cold/warm을 구분한다. 새로운 대형 실험으로 장중 경보를 재발시키지 않는다.

## 9. 구현 순서·owner·배포 경계

실행 순서는 `RIO0 비용/의존성 고정 → RIO1 상태·잠금·terminal 보존 및 cache + RIO3 하류 priority → RIO2 phase digest 공유 → 각 코드 리뷰/보완/표적 검증 → 허용된 immutable 배포 → 자연 수용`이다. RIO1/RIO3와 RIO2는 개별 리뷰·릴리스가 가능하다. 구형 predecessor/origin CLI에는 새 flag나 cache를 강제하지 않으며 해당 full 비용을 유지·공개한다. RIO4의 IDE/OS 정리는 독립 후보 검토다. 기존10/13 구현 전체를 다시 열지 않는다.

| 기존 owner | 맡을 범위 | 닫는 증거 |
|---|---|---|
| `NonfixedDispatchReadinessReview1012` | RIO1/RIO3·Sentinel/monitor의 의미·분모·freshness·자원 비용 | frozen parity + 실제 정규3회 + host/PID 비용 |
| `DirectFamilyPreopenPolicyHandoff` | RIO2의 native 계약·release/policy/prepared·PID 소비 | phase별 source/code/identity 결속·원 정책 불변·실제 successor receipt |
| `AuxiliaryCircuitRecoveryRepair1012` | 개선 후 Main 정상 attempt 지연·guard | 동일 attempt의 offered/timeout/censored·필수 저장·원5초 계약 |

[10/14 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)의 stable ID·원 Acceptance/History를 사용한다. 기존07:35~08:15 및08:00/08:05/08:10 시간창은 이번 새 구현의 미래 수용 시간이 아니다. 구현 change set의 격리 checklist에 조건부 적용·자연 수용 TimeWindow를 반영하고 parser상 current owner1개를 확인한다. 현재 공유 operational checklist는 배포 시 native snapshot/CAS 절차 전까지 보존한다. 단순 계획 링크를 실행 일정이나 새 배포 승인으로 해석하지 않는다.

RIO2 또는 wrapper 구현 때에는 소유 운영 문서와 checklist를 같은 change set에서 갱신한다. checklist-only 변경도 현재 native 봉인 영향이 있으므로 [릴리스 운영 계약](../runtime-release-routing.md)에 따라 역사 snapshot·CAS·필요한 source reseal을 검증한다. 문서 작성만을 이유로 지금 보고서/strict/PREOPEN을 재생성하지 않는다.

실제 적용에서는 그 시점에 유효한 기존 사용자 승인 범위와 runtime/runbook 경계를 따르며, 이미 승인된 범위에 중복 승인을 요구하지 않는다. active wrapper와 live policy generation을 보존하고 candidate code review·대상 시험 완료 뒤 ordered driver를 사용한다. 현재 구현 작업은 배포 실행과 구별한다. 선택 기록의 Main 정지 경계를 유지하며 새 기동을 합성하지 않는다.

## 10. 되돌림과 문서 리뷰

- source/semantic 차이, false cache hit, guard·필수 receipt 손실, freshness 위반 또는 새 resource 악화가 있으면 해당 cache/shared proof를 무효화하고 기존 native full/reader 경로로 복원한다. fallback도 남은 worker 예산에 포함하며 모든 cron에서 무제한 full 재시도를 만들지 않는다. 원 정책·원천·custody·incidents는 보존한다. cache 파일을 삭제한 것만으로 배포/롤백 완료를 주장하지 않는다. 저장 schema 변경에는 old/new reader 호환·명시적 migration 시험을 포함하고, rollback 시 incident/cursor reset으로 정상화하지 않는다.
- rollback 대상은 그때 검증된 Main-only recovery release다. 퇴역 owner가 살아나는 과거 실행본으로 돌아가지 않는다. 배포·PID·자연 수용·수익성은 별도로 보고한다.
- 1차 리뷰 보완: `load_effective`의 선행 full과 historical bundle 경로, code-handoff transitive dependency, metadata 재사용의 신뢰 한계, parent/child I/O 중복, 후속 monitor priority 누락을 계획에 반영했다.
- 2차 리뷰 보완: report-only durable cache와 startup phase proof를 분리했다. cold 예산은 bundle별 반복이 아닌 실행 전체 상한으로 고쳤고, resource wait와 실제 source 손상을 구분했다. 저장 경로/권한/삭제 범위, 미완료 proof 발행 금지, 기존 monitor affinity 적용 범위를 명시했다. missing/changed/expired/failure에서 native full 또는 명시적 실패로 닫는 경로와 원 authority를 재검토했다.
- 계획 리뷰 당시 아래 결함을 보완했고, 후속 구현에서 원천 읽기와 independent semantic 검사를 분리하여 해결했다. 실제 배포·자연 성능 수용은 별도다.

| 발견한 계획 결함 | 반영한 보완 | 구현 시 닫는 검사 |
|---|---|---|
| machine 외 selector·monitor 상태/terminal 경로 누락 | §2/§3의 전체 호출 목록, §4.4 scope별 상태와 detector 연결 | 전체 경로 I/O 목록·동일 run terminal 소비 |
| resource 보류를 빈 issues로 넘길 때 pending 삭제/active 하향 가능 | §4.4 tri-state 및 원 경보 이력 보존 | pending/active deferred 회귀·알림 fake sender |
| cache lock 제한 밖의 blocking state lock과 누적 timeout | §4.3/§4.4/§6 단일 deadline·상태 잠금 대기·자식 회수 | 경합·부모 종료·fallback 합산 예산 |
| 파일 부재/후보 추가/직접 읽기가 cache 무효화에서 빠질 위험 | §4.1–4.2 전체 선택 검사를 native로 유지하고 digest만 재사용 | 새 current/후보·subprocess dependency 결함 주입 |
| launcher proof로 driver 독립 검사가 생략될 위험 | §5 digest 공급과 semantic 검사 분리, native output CAS | caller별 check ID 완전성·driver 전용 결함 검출 |
| 성능 분모·표본·부분 성공 및 rollback 상태 보존 불명확 | §8 전체 bytes/활성 구간/비대상 공개, §10 schema 호환 | parity·frozen 비교쌍·자연3슬롯·rollback 회귀 |

계획만 검토했던 당시 기록은 [문서 리뷰 검증](/home/ubuntu/KORStockScan/tmp/resource-recheck-20261014-0845/plan-review-validation.json)이다. 후속 구현은 회귀1,450건, Python compile/shell syntax, diff와 print-only parser 및 owner 검증으로 닫는다. 최신 근거·보완 이력·미실행 범위는 [구현 리뷰](../audits/main-io-residual-implementation-review-2026-10-14.md)를 따른다.

### 승인 배포의 추가 계약 gate

후속 사용자가 배포 및 Main 기동을 승인했다. 실제 준비에서 holding vote code pin 누락을 발견해 exact reviewed holding-generation pair와 선택 전 native holding code 검증을 추가했다. delay/stop/holding 세 계약을 모두 preflight하고 원 정책/PREOPEN byte 불변을 대사한다. 첫 차단 시도와 복구·후속 결과는 [구현 리뷰](../audits/main-io-residual-implementation-review-2026-10-14.md#기동-전-holding-계약-결함과-보완)에 보존한다.


## 장후 CLI 실행 내 재사용 보완 — 2026-10-16

사용자 지시로 선택 코드23a13aba6 기준 별도 작업본에서 postclose controller/next-session prepare의 반복 원천 읽기를 보완한다. 기존 observer/transition 저장소와 수명은 유지한다. 구현·검증·배포 상태는 [10/16 리뷰](../audits/main-postclose-read-reduction-implementation-review-2026-10-16.md)가 소유한다.

- `postclose_done_controller` CLI의 실제 native controller 실행과 `next_preopen_readiness --prepare`만 기존 digest 계층의 `postclose` 역할을 사용한다. 라이브 library·standalone verify·PREOPEN의 기본 전체 검증을 바꾸지 않는다.
- postclose 해시는 해당 프로세스/호출의 메모리에만 보존한다. 실행 시작은 cold이며 persistent observer/transition 해시·PASS를 읽거나 쓰지 않는다. 중첩된 같은 root/date 호출만 공유하고 종료/예외에 비운다. PID가 바뀐 fork는 재사용할 수 없다. 최대4096개 항목·개별 digest600초의 비연장 수명이며 기존 단계 마감시간을 늘리지 않는다.
- 파일의 lexical/resolved path·부모/alias·dev/inode/size/mtime/ctime/mode/owner를 매번 확인한다. 실제 해시만 공유하며 정책 선택·기대 SHA 비교·파일 discovery·원천 격리·현재 날짜/selector/PID·hard safety 판정은 각 native consumer가 다시 수행한다. nonlocal/부적격 저장소는 full 경로를 유지한다.
- delay compact 검증은 파일별 SHA·ordered 전체 SHA·날짜별 cumulative SHA를 한 스트림으로 구한다. descriptor와 경로의 전후 identity/byte count, 마지막 inventory/identity 검사를 수행한다. 원 raw/compact ledger·plain/gzip/late-part 검사는 그대로 수행한다.
- CLI stdout의 `validation_io`는 이 호출의 완료된 해시 읽기/재사용량과 thread I/O 계수다. controller·prepared canonical 산출물에 새 계측 필드를 넣어 원 해시를 바꾸지 않는다. 파일 내용 SHA 재사용을 semantic PASS로 기록하지 않는다.
- 실제 적용과 자연 장후 cold/warm 소요시간 수용은 기존 `DirectFamilyPreopenPolicyHandoff` 및 당일 체크리스트로 확인한다. full strict/currentness 호출을 생략하거나600초 예산을 늘리지 않는다. 현재 봉인 준비본 재생성·거래 재기동·주문 권한은 이 구현에서 열지 않는다.


### 10/16 승인 배포의 source-pair 수용

사용자 후속 지시로 위 구현의 배포와07:55 정기 기동 검증이 승인됐다. 기존 인계의 `REVIEWED_POSTCLOSE_READ_SOURCES`는 원23a13aba6의 delay source verifier와 검토된 단일 패스 구현의 정확한 파일 SHA 쌍만 인정한다. 원 정책/보고서/code pin은 유지하고 source/코드 변조와 native 원천 결손은 계속 거부한다. PREOPEN 진행 중 선택 전환이나 code-refresh 시한 우회는 하지 않는다. 정기 첫 기동의 native 소비 뒤 기존 ordered driver를 사용하며 원 기동/후속 배포 PID를 분리한다. [재리뷰·배포 수용](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md)을 따른다.


### 10/16 정지한 selected-phase 실패의 제한 복구

07:55 원본 native 기동 후 첫 ordered 배포에서 carried stop의 consumed vote 원천에 당일 관측 tail이 추가되어 인계가 실패했다. 원 consumed prefix의 publisher 봉인과 전체 SHA를 유지한 채 엄격히 후속 날짜의 완결된 native holding 행만 분리 검증한다. full research와 selected cell은 이 경로를 쓰지 않는다. 정확한 source-pair와 코드·변조·동시성 시험을 유지한다.

복구는 기존 automation 패키지의 embedding-only `StoppedDeploymentRecovery`가 소유한다. 정지한 Main/원 supervisor/tmux, 정확한 selected-phase 실패와 owned hold, 원 live-captured PID proof 및 원 정책/PREOPEN/prepared, 새 candidate delay/stop/holding 검증 후 새 attempt에서 hold를 CAS 인계한다. 기존 FAIL과 selector를 보존하고 native prepare/bootstrap/auxiliary/기동/독립 PID 검증을 반복한다. 일반 CLI의 임의 hold 인수나 자동 복구 권한을 열지 않는다. owner는 기존 `DirectFamilyPreopenPolicyHandoff`이고 원 봉인 체크리스트는 유지한다. [배포·복구 리뷰](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md).


### 장중 terminal receipt 수리 인계 — 2026-10-16

추가 사용자 오류의 세 overnight SELL은 이미 체결한 `sell_completed` outbox다. 별도 broker/BUY-generation identity로 원 frozen field/시각/qty/custody를 검증해 ACK하며, scanner/entry trace를 합성하거나 주문을 재전송하지 않는다. simulation scope를 outbox snapshot에도 보존한다. 정확한 코드 쌍과 새 holding/auxiliary capability fixture, 원 정책/PREOPEN 불변, native PID/세 원 key ACK/최종 detector를 배포 수용으로 확인한다. [수리·인계 근거](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md#장중-추가-sell-terminal-outbox-세-건의-수리). 원 journal과 실제 비용 미상은 보존한다.


### 10/16 자연 감시 결과의 추가 보완

실제 b4d23f658 기동과 세 SELL terminal native ACK, optional code/calendar 재결속을 확인했다. 후속 정규 감시에서 holding_exit_sentinel의 aware/naive clock 혼용을 발견하여 기존 raw/cache 파싱을 KST wall-time으로 통일한다. cron 복구는 이 owner만 같은 owner의 후속 DONE을 요구하며 기존 FAIL 이력과 새 오류 감지를 보존한다. observer는 완전한 현재 PID 평가 전 차단 trace·호출0을 증명한 lazy 요청/pending 부재만 제한 경고로 분류한다. partial/source gap/runtime admission false는 유지한다. 운영 수용은 같은 DirectFamilyPreopenPolicyHandoff 아래 새 native PID·자연 sentinel DONE·전체 detector로 확인한다. [원인·경계·시험·수용](../audits/main-postclose-read-reduction-deployment-review-2026-10-16.md#0842-observer-경고와-보유-감시기-시각-오류-보완). 다음 자연 optional 야간은 기존 MainMarketWeaknessPostcloseObservation1008 OPEN이다.


09:01:47의 보유 의미 영수증 누락은 첫 자연 감시가09:00:35 완료된 뒤 후속 native detector의 exact-date/source-generation 검증으로 해소됐다. 과거 first-crossing/정책 결손·비용 미상은 원 owner에 유지한다. 추가로 평가 시도0인 현재 PID의 모든 strict 계약이 통과하고 pending 파일 부재만 남은 경우를 같은 bounded 경고 경로로 제한한다. 다른 미충족과 partial/권한은 보존하며 source-pair·회귀·새 native 배포/자연 detector를 요구한다. 세부 근거는 위 배포 리뷰의09:01:47 절을 따른다.


09:06:39 policy_binding_gap 추가 수리는 기존 보고서 consumer에서 원 legacy BASE target pin과 native record/symbol을 엄격히 결속한다. 원 pin/hash를 보존하고 승인 부모 vector와 동일한 값만 검증하며 native logger의 bounded flat dictionary repr를 안전하게 읽는다. 매매/정책/수량/provider를 변경하지 않는다. driver preflight 중단·원 신호 재현·회귀·새 native 배포 및 자연 보고서 수용은 위 배포 리뷰의09:06:39 절을 따른다. 원 first-crossing/비용 source gap은 원 owner에 유지한다.


036930의 확인된 SOR SELL은 venue UNKNOWN을 보존한 typed custody ACK로 닫는다. 기존 native terminal/BUY/TP/qty/custody/packet-clock 검증과 source-gap 표기를 요구하며 거래소·비용·전략 권한을 승격하지 않는다. 앞선 세 key와 새036930 ACK, native revive 후 고정5개 실제 편입, 최신 수동 제외 보존·새 generation fixture/PID·자연 detector를 수용한다. 원인·동시 재기동/정지 복구 증거는 위 배포 리뷰에 보존한다.

현재 PID와 native archive의 typed receipt shape도 같은 manifest env로 검증해 비교한다. 실제 conflict는 보존하며 정책/runtime 값을 바꾸지 않는다. 원인·회귀·원036930 scoped audit 및 detector-lock timeout은 위 배포 리뷰에 기록한다.
