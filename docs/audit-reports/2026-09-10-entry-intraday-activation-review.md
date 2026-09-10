# KRX v10 당일 승인·고정 배포 리뷰

기준일: 2026-09-10 KST. Owner: `entry_setup_live_policy`; 자연 소비는 `RuntimeEnvIntradayObserve0910`, 경제성은 `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910`에서 계속 확인한다.

## main 병합 및 재기동 영향 점검 (12:36 KST)

병합 전 최종 review gate: 코드10개 및 직접 연결된 producer/consumer·다음날 date/cap·restart/custody 경로를 재검토했고, 격리 branch에서15개 모듈 **1947 PASS**(기존 pandas 경고1), compile·bash syntax·diff check와 print-only parser **29개 task** 검증을 통과했다. 미해결 in-scope code finding0이며 배포 진입점 통일·내일 자연 기동·체결/순이익은 별도 미완료다.

이번 커밋 대상은 검증된 release `680773d5`의 코드10개와 이 작업의 문서 기록이다. 병행 세션의 adaptive-exit/widget/episode/registry 및 PREOPEN 보완은 이 커밋에 임의로 포함하지 않는다. Git 병합·push와 현재 PID 교체는 별개이며 이번 요청에서는 재기동·cron/env/정책 변경을 하지 않는다.

- 현재 PID657193의 source root는 `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-680773d59c88`, source-dirty=false, 두 실제 recheck budget100이다. main 변경만으로 이미 실행 중인 고정 코드는 교체되지 않는다.
- 같은 고정 release의 `restart.sh`를 사용하면 기존 frozen code를 다시 기동한다. 다른 세션의 신규 commit은 자동 포함되지 않는다. 일반 작업폴더의 `restart.sh`는 source-root 차이를 감지하여 supervisor를 그 작업폴더로 전환할 수 있으므로 병행 미검토 코드가 함께 로드될 위험이 있다. 같은 basename의 명령을 어느 폴더에서 실행하는지가 중요하다.
- intraday approval은 Git commit ID 전체가 아니라 명시된10개 코드 파일과 원본 source bytes를 검증한다. 문서만 병합해 commit SHA가 바뀌어도 그 bytes가 같으면 승인 자체는 유지된다. pinned 코드 변경/원본 bundle 삭제·변경/15:30 만료는 V2.13 fallback 사유다. 이 hash가 정상이라는 사실은 pin 밖의 모든 병행 변경까지 검토했다는 뜻이 아니다.
- data/logs/tmp/.venv와 runtime 정책은 원 작업폴더와 공유한다. 고정 배포는 코드 격리이지 계좌·환경·정책 격리가 아니다. 다른 세션의 공유 env/artifact 변경은 다음 기동이나 해당 loader 재평가에 영향을 줄 수 있으며 상태 원장을 복제하거나 quota를 초기화해서는 안 된다.

현재 설치된 사용자 crontab은 매 거래 요일07:30 `tmux kill-session -t bot`,07:35 작업폴더의 `deploy/run_threshold_cycle_preopen.sh`,07:55 작업폴더의 `src/run_bot.sh` 기동이다. 따라서 현재 고정 배포를 내일도 자동 유지하는 routing은 **설치돼 있지 않다**. 기존07:30 cron은 이번 graceful handoff를 호출하지 않는 별도 중단 경로이며 이번 점검에서 변경하지 않았다. 내일07:55는 그 시점의 작업폴더 코드/미커밋 파일을 읽는다. main 병합은 이번 코드의 보존이지 작업폴더 전체를 clean 배포본으로 만드는 작업이 아니다.

매일100은 영속 operator env와 effective9/11 이후 새 KRX 후보의 risk contract에 구현됐다. 오늘 승인 pin은 내일 launcher에서 제거하며9/11 dated env만 별도로 읽는다. 장후 후보→07:35 정식 activation→07:55 PID 검증이 통과해야 V2.14/1주/100이 적용된다. 현재9/10 낮에는 source9/10 후보와9/11 정식 activation/PID 증거가 아직 없으므로 미래 기동 완료라고 판정하지 않는다. 생성 실패/부적격/기존cap3 후보 선택 시100 env만으로 정책 한도를 강제로 늘리지 않으며 V2.13 또는 원 후보 한도가 유지될 수 있다. launcher 자체 env/authority 검증 실패는 기동 차단과 별도로 구분한다.

안정적인 후속은 검토된 merge로 새 clean release를 만든 뒤 수동 restart와 다음날 cron이 같은 배포 진입점을 사용하도록 통일하는 것이다. 이는 별도 배포 경로 변경이며 이번 영향도 질의만으로 실행하지 않는다. 오늘의 즉시 재기동이 따로 승인되면 현재 PID root의 스크립트와 exact custody/환경 검증을 사용한다. 내일 실제 source root/commit/dirty, 후보/activation/date/hash, 두 budget100·1주, quota 날짜 분리와 WS/Provider 첫 자연 소비는 checklist의 `KRXDaily100NextDayStartupAcceptance0911`에서 확인한다.

## 매일 100회 구현과 적용 이력

초기 3회 유지 및 중간 20회 제안은 사용자의 **"탐색한도를 100회로 하고 매일 유지"**로 대체됐다. 적용 당시 기존3회는 보존하고 잔여97회였으며 아래12:27 자연 소비 이후4/100이다. KRX 정규장 기존 1주 탐색·재검사·회복 제출 한도만100으로 맞추며 per-symbol/cooldown, broker/account, residual/scale-in 금지와 모든 safety는 유지한다. 이는 일일 최대치이며100회 제출 목표 또는 수익 보장이 아니다.

effective date가9/11 이후인 새 정식 KRX 후보는 `operator_daily_krx_one_share_limit_100_2026_09_10`을 risk contract에 기록하고 PREOPEN→PID→최종 guard가 후보와 같은100을 소비한다. 기존3회 후보는 불변 증거로 보존하고 activation만100으로 변조하면 차단한다. NXT의 기존 한도3과 별도 승인 경로는 그대로다. persistent operator env는 기존 KRX recheck ON/scope와 두 budget100을 유지하고 escalation은 OFF로 둔다. 매일 새 candidate/date/source gate를 없애는 권한은 아니며 부적격 후보를 강제 적용하지 않는다. 9/11·9/14 정식 후보→PREOPEN→resolver100 및 env budget3 불일치 차단을 회귀 검증했다.

확대 검증 배포본: `9e0044b89de1c4327f81b82d6863fb3f5b102912`. 여기에 staged handoff 보완을 포함한 실제 최종 배포는 아래 `680773d5`다. 아래 e821 기록은 첫 배포의 역사적 증거이며 최종 정상 수락이 아니다. 중간20회 배포본은 운영하지 않았다.

## 최종 적용·재점검 receipt (12:25 KST)

12:27 후속 자연 수락: canary는12:26:31 `healthy_observer_canary`/stop false, trade/depth persisted5830/9664, worker·depth·writer오류0이다. [실제 AI trace](../../data/ai_decision_trace/ai_decision_trace_2026-09-10.jsonl)에서12:25:23 티씨케이DROP,12:25:36 원익IPS WAIT,12:25:57 심텍DROP의 OpenAI 호출/parse가 모두 정상이며 세 행 모두 새 approval SHA와 maximum100이 기록됐다. Bedrock entry-price 호출도 재개됐다. 따라서 아래12:25초의 "새 Provider 아직 미확인"은 이 후속 증거로 해소됐다. 원익IPS는12:25:38 주문0045965 qty1 제출 후 기존 cancel/reprice owner로0046010 qty1을 처리했다. 후속 조회에서 일일 탐색 ledger4회로 증가해 새 한도 자연 소비가 확인됐으며 취소/미체결을 실현수익으로 세지 않는다. DROP을 강제 BUY로 바꾼 것이 아니고 실제 체결·순이익 개선은 아직 별도 수락이다.

- 12:24:07 기동 PID **657193**, release `680773d59c882a775d31979ad8a069b5ea06a1b8`, source root `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-680773d59c88`, `source_dirty=false`. old PID624616 종료 후 singleton으로 교체했다.
- [당일 승인](../../data/runtime/entry_setup_intraday/entry_setup_intraday_2026-09-10_680773d59c88_100.json) artifact SHA `95a10c8513acedad7044678cf026ce47ecf5c2f041aeec107ee8f3341da20da0`; 원본 candidate/source 파일과 effective9/11 불변. resolver V2.14/evidencev10/composerv11 및 maximum100 확인.
- [실제 PID verify](../../data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-09-10.json) `pass`, PID/env 누락·불일치0, runtime/dated policy fail0. 실제 PID의 두 recheck budget100과 one-share cap100이 일치한다. ledger accepted3, 잔여97; 초기화 없음.
- 기존 strict old-PID verify→plan `537fa0e19dd5e981be359b3c92370fe927c70793cf06805ed93e9fc499c5d770`→100 env 게시→exact check→restart→strict new-PID verify→Samsung handoff sequence5 commit 완료. Samsung policy/수량/custody 변경과 handoff 중 새 매수주문은0, 독립 service PID327358 유지.
- 12:24:38부터 새 0B/0D 수신, 12:24:50 canary는 `warming_up`, stop false/stop reasons 없음. trade worker646/depth1170 처리, journal persisted231/depth1052, worker/depth/writer 오류0. 이것은 수집 복구이며 latency 표본 floor/경제성 수락과 구분한다. 보수적인 source-gap 기록은12:00:28~12:24:50이며 미관측 경로를 합성하지 않는다.
- 실제 PID env+최종 code의 AI preflight는 `ready_operator_directed_exact_v2`. 기존7/29 승인 원본 path/hash/env를 정상 해석한 것이며 신규 validation bypass가 아니다. 12:25 점검 시 새 Provider 자연 호출은 아직 확인되지 않았으므로 모델 판단 개선/실거래 효과는 OPEN이다.
- [재기동 전 broker](../../tmp/intraday-monitor-20260910-1050/broker-121812.json)와 [12:24:54 사후 broker](../../tmp/intraday-monitor-20260910-1050/broker-122455.json)는 삼성전자45·SK텔레콤10주, SELL0022607/0018662/0015751 각각10주 미체결 및 exact owner1개가 동일하다. 삼성E&A 과거 registry10/broker0 불일치는 그대로 분리한다. 계좌 전역 완전 reconciliation PASS로 주장하지 않는다.
- 검토 범위 unresolved finding0; 확대1943 PASS 및 후속63 PASS(중복 포함), syntax/lint/diff/parser PASS. 별도 고정 release commit은 생성·배포했지만 원 작업 트리의 모든 미커밋 수정이나 main 병합·push를 수행한 것은 아니다.

## 첫 배포 사후 결함과 보완

최종 검증: 입력/호가 collector/preflight/AI/recheck/order/custody 15개 모듈 **1943 PASS**. 이어 환경 전환 순서 결함을 보완한 고정release `680773d59c882a775d31979ad8a069b5ea06a1b8`을 사용한다. `restart.sh`의 명시적 `KORSTOCKSCAN_RESTART_PREPARED_HANDOFF_ID`는 기존 strict old-PID prepare가 발급한 exact same-date/non-expired plan을 기존 runtime restart guard로 다시 검사한다. wrong plan/expired/owner 없는 우회는 차단하고 새 PID strict verify와 Samsung commit은 그대로 필수다. 한 번 사용한 키는 supervisor로 상속하지 않는다. 이 후속 검증은63 tests이며1943과 중복 포함이라 합산하지 않는다.

운영 순서는 old env를 일시 복원→old PID fresh verify→기존 prepare→승인된100 env/pin 게시→exact prepared plan 재검사 restart→new PID strict verify/commit이다. 새 값을 먼저 저장해 old PID와 비교하면 mismatch가 나는 것을 무시하거나 PASS로 고쳐 쓰지 않는다. 이 순서 때문에 source/budget 설정이 임시로 이전값일 수 있으나 기존 사용 ledger는 한 번도 초기화하지 않는다.

12:00:28 PID624616으로 guarded restart/verify PASS, 12:00:44 WS login 및12:00:48 0B/0D first-data, Samsung same-date handoff는 정책/수량/신규주문 변경 없이 완료했다. 11:59:54와12:01:16 broker 조회에서 보유/미체결3건/소유자가 동일했다. 그러나12:00:54 observer worker261/depth412 오류로 auto-stop했고 새 AI는 `runtime_preflight_artifact_not_ready`로 Provider 미호출이었다. 따라서 **첫 배포의 자연 소비는 FAIL**이며 정상 완료로 분류하지 않는다.

원인은 별도 선언된 collector 기본 출력 root와 multi-timeframe promotion의 path identity가 아직 release/data symlink를 사용한 데 있었다. collector도 trusted data mount만 canonical화하고 실제0B/0D writer 회귀에서 각1행·worker오류0을 확인했다. promotion은 canonical DATA_DIR를 사용하고 기존 원본 승인의 path/hash/env/날짜 검사는 그대로다. 수정 release에서 실제 PID env로 `ready_operator_directed_exact_v2`와 journal no-follow check가 통과했다. 새 bypass·과거 approval rewrite는 하지 않았다.

12:00 첫 배포부터 복구된 새 PID의 healthy writer 확인 전까지는 source gap으로 보존한다. 누락된 호가/체결을 합성하거나 이 구간을 정상 micro/EV 표본에 포함하지 않는다. 실제 시작·복구 시각은 최종 적용 receipt에 기록한다.

## 초기 결정과 범위 (100회 지시 이전 기록)

사용자의 "다음액션 실행 후 재점검"은 직전 제안한 당일 KRX 1주 탐색 scheduling exception과 코드·정책 일치 후 조건부 우아한 재기동의 실행 지시다. 원래 9/11 후보를 9/10 후보로 고쳐 쓰지 않는다. 별도 명시 승인 receipt가 원본 날짜/후보/Provider 근거/code hash와 당일 15:30 만료를 결속한다. KRX 정규장 SCANNER의 V2.14, evidence v10/composer v11, 기존 1주 탐색만 허용한다. NXT·일반 수량 확대·residual·scale-in·Provider·safety 변경은 없다.

9/10 일일 탐색 cap은 이미 **3/3 사용**이다. 설치·재기동으로 ledger를 초기화하거나 추가 주문 한도를 만들지 않는다. 오늘 추가 탐색 주문·수익 증가를 예상 효과로 주장하지 않는다. 기대효과는 새 판단 입력/finite recheck와 합쳐진 모니터링 결함 수리의 실제 소비이며, 다음 거래일 적용은 그 날짜의 정식 candidate/PREOPEN 계약으로 별도 판정한다.

## 원본과 배포 세대

- 원본 후보: `/tmp/kss-entry-v10-stage-4m6XWX/candidates/entry_setup_v2_14_bounded_live_candidate_2026-09-09.json`.
- file SHA256: `1416cd01a5917acfd7958d16a99c90f690c2bdb1690420f38b3498617a533b86`; artifact SHA256: `315550104afd19f7ef34864067b7d7bb52491fd4a1efb81e26f2c3dc3b495d0e`.
- source9/9, generated9/10 10:34:16, original effective9/11. KRX 30 판단/21 probe intents/18종목; 실제 exposure와 비용 검증 표본은 0, net EV는 null이다. 원본 v9 PREOPEN/candidate도 보존한다. 새 Provider 실행/과거 재생 없음.
- 검토된 main 기반: `2aadb8ac925f0a2446189c8bfbf7d565e20c08e3`(장중 모니터링 R1~R3 및 recheck 수리 포함).
- 별도 고정 배포 commit: `e821241521dceb493b3b253ba0bc2c10b645d0b2`; 경로 `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-e821241521dc`.
- 원 작업 트리의 병행 adaptive-exit/widget/episode/registry 미커밋 변경은 포함하지 않았다. 배포 commit은 원 작업 트리 main/사용자 index를 이동시키지 않는 detached release다.
- data/logs/tmp/.venv는 기존 상태를 공유한다. 코드는 고정된 release를 사용하고 data/logs 루트만 canonical 경로로 해석해 artifact child의 no-follow 검사는 유지한다. 기존 state/DB/주문 원장을 복사하거나 초기화하지 않는다.

## 리뷰와 보완

1. 기존 full candidate/source/cumulative validation을 재사용하되 original scheduled date와 actual runtime date를 분리했다. 명시적인 두 env pin 없이는 당일 승인이 작동하지 않는다. source/code 변조·일자/시간/owner/scope 불일치·operator OFF는 V2.13 fallback이다.
2. malformed 후보에서 enabled=true가 먼저 남을 수 있는 순서를 수정했다. 승인 파일은 exclusive create하며 기존 승인을 덮어쓰지 않는다.
3. release의 shared restart flag는 canonical 경로로 원자 발행/소비한다. source root 또는 launcher 세대가 달라지면 old child 종료를 확인한 뒤 tmux supervisor만 교체한다.
4. 초기 release 확대 시험의 38개 실패는 shared data symlink와 strict no-follow 충돌이었다. trusted mount만 canonical화하고 child symlink 거부 회귀를 추가했다. 실패한 초기 배포본은 운영하지 않았다.
5. long-lived launcher가 전일 intraday pin을 상속하는 결함을 막았다. 매 기동에서 두 pin을 unset한 뒤 해당 날짜 operator env를 다시 읽는다.

고정 release의 12개 관련 테스트 모듈 **1826 PASS**, 기존 pandas 경고 1건. Python lint/format, shell syntax와 diff check 통과. 검토 범위 unresolved finding 0이며 병행 미커밋 코드 전체 또는 경제성 승인을 뜻하지 않는다. 문서 parser 검증 후에만 설치/재기동한다.

## 적용 전 소유권 및 후속 수락

11:47 readonly broker 조회: KRX/NXT 조회 완료, 삼성전자45주·SK텔레콤10주, SELL 미체결3건 각각 exact owner1개. 삼성E&A028050 과거 수동청산 귀속은 registry10/broker0 불일치로 남으며 새 주문/보유의 정상 근거로 사용하지 않는다. 무관한 custody 정리·주문취소는 하지 않는다. 실행 직전 broker 상태를 다시 확인한다.

설치 후에는 실제 approval path/hash, 새 PID/source root/commit/dirty, runtime env 검증, KRX resolver V2.14/v10, WS first-data와 소유권 불변을 기록한다. 새 PID 실행만으로 실제 요청 전송·주문·비용후 개선까지 완료라고 하지 않는다. runtime 반영/자연 증거 결과는 아래에 추가한다.

## 운영·롤백

실제 PID의 `KORSTOCKSCAN_RUNTIME_SOURCE_ROOT`가 고정 release인지 먼저 읽고 **그 경로의 `restart.sh`**만 사용한다. 원 작업 트리의 `restart.sh` 실행은 미검토 코드로 배포 위치를 되돌릴 수 있으므로 금지한다. 당일 승인 expiry는15:30이며 이후 V2.13 fallback; 다음날 launcher는 당일 pin을 상속하지 않고 그날 정식 후보/PREOPEN을 검증한다. 영속 KRX 탐색 한도100과 별개로 부적격 후보 승인은 강제하지 않는다. 조기 롤백은 기존 `entry_setup_live_policy` operator OFF와 recheck override OFF를 명시 적용하되 위 staged handoff 순서로 수행한다. 단순 승인 pin 제거만으로 구 v9 승인이 다시 유효하다고 간주하지 않는다. 모든 기존 order/freshness/custody/hard safety guard는 계속 유지한다.
