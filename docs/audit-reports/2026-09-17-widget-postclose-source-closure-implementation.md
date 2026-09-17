# 09-17 위젯 장후 원천 폐쇄·성능 구현

사용자 명시 지시: 상세계획 구현, 코드리뷰·수정보완 반복, 검증 후 commit/push·배포·기동. [상세계획](../proposals/widget-postclose-performance-and-source-closure-implementation-plan-2026-09-16.md)의 09-16 계획 전용 문구와 구분한다. 현재 자연 acceptance owner는 [09-17 checklist](../checklists/2026-09-17-stage2-todo-checklist.md)의 `[WidgetPostcloseEvaluationPinAcceptance0916]` 하나다.

## 구현과 소비 경계

| Owner | 변경·검증하는 계약 |
| --- | --- |
| research-watch raw collector | 기존 universe helper의 기존 4 + 설정 13 + completed discovery 2 = 19종목. 실제 KRX/통합 AM route, 안전한 API/admission/HTTP/return-code detail, completed OHLCV delta·overlap dedup·conflict quarantine. local 18/min·headroom 3 유지, nominal cycle ≥228초. 원래 수신시각이 있는 fresh 검증 quote/BBO만 공통 snapshot에서 재사용하며 chart는 실제 조회 |
| runtime observer/policy writer | 실행 canonical 정책은 기존 trader가 재구성하는 기존 형식 유지. 주문 authority 없는 companion observation catalog만 diagnostic seed를 확대. exact-date evidence·seed/source/parameter hash·등록/effective/session boundary 검증. seed 부재는 raw-only receipt; token/remote/episode/order 생성 없음. latest bar도 effective boundary 이후여야 신호 평가 |
| signal research | 종목별 source 검증→fingerprint→checkpoint→평가→raw 해제. EOD terminal 있는 exact-date source snapshot만 durable 재사용. per-day source/cost/algorithm key의 bounded compressed replay cache와 TERM partial flush. monotonic high/low·continuity features, setup/exit reuse, full replay 후 half/holdout/cap 집계, stable rank winner detail만 보존 |
| local auto calibration | raw market와 seeded advisory census 별도. identifiable optional lifecycle 오류는 market OHLCV를 보존하되 event 경제성 승격은 차단. 원천 없는 scope는 grid 생략, 후보 총계는 유지하고 winning family만 보존. zero와 missing rank metric 구분. invalid universe는 명시 gap·promotion 차단 |
| shared observation recorder/paired replay | 기존 원본 writer에 optional `.calibration.jsonl` 추가. original path/line hash·producer contract·compact payload checksum·field receipt 검증, 없거나 손상되면 원본으로 fallback. price/time/BBO/quantity/paired trace/event/seed/owner 보존. paired loader의 전체 read/decode/split 복사 제거; streaming hash·verified compact 소비 |
| existing evaluation wrapper/unit | 고정 target date, stage start/end/wall/CPU/RSS와 bounded symbol/grid progress. EOD wait 별도. 분석 단계 default 5,400초, timeout은 explicit failure와 기존 checkpoint 보존; final completed/apply를 성공으로 위장하지 않음. observer의 condition만 validated raw scope로 확대 |

새 Python module/daemon/DB/service/timer/cron/mandatory report는 만들지 않았다. optional snapshot·projection·cache는 기존 데이터 산출물이다. 미래 seed로 과거 quote/BBO·실시간 continuity·신호/체결을 복원하지 않는다. raw 및 기존 exclusion manifest, full clean baseline 06-05 이후 입력·1,536 grid·cap 1~5·16-day 독립 holdout·cost/half/tail/승격 guard·custody는 유지한다.

동일 wrapper의 advisory stage는 기존 cumulative evaluation input을 유지하고 paired replay 경로만 verified streaming helper를 소비한다. tower/checklist/verifier/controller의 필수 source report 경로·schema 및 마지막 publication ordering은 유지한다. companion catalog는 기존 apply receipt의 optional metadata이며 독립 summary owner를 추가하지 않는다.

## 반복 리뷰에서 수리한 결함

- compact 필수 current price 및 nested paired BBO/quantity/confirmation trace 누락을 native writer→loader 동등성 테스트로 수리했다. optional projection open/read 실패도 raw fallback이며 기존 원본 retention 때 sidecar를 같이 정리한다.
- expanded observation metadata를 canonical execution policy에 넣으면 pinned 구버전 trader의 재구성 검증이 실패했다. legacy canonical + expanded companion으로 수리하고 diagnostic 종목이 execution loader에 들어가지 않는 native publisher test를 추가했다.
- registration보다 이른 effective seed 및 과거 bar로 늦게 등록한 seed를 평가하는 위험을 registration/session/latest-bar 경계로 차단했다. legacy registration unknown은 새 시각으로 채우지 않는다.
- candidate memory pruning 후 전체 calibration-ready 계수가 보존량으로 줄어드는 오류를 별도 full counter로 수리했다. stable tie와 selected family/cap chronology는 유지한다.
- 동일 API response 안의 중복 bar가 기존 parser dedup에서 사라지던 경로를 optional duplicate preservation으로 수리했다. legacy unique-bar parser 기본값은 유지하고 raw delta의 실제 conflict quarantine을 검증한다. runtime observer는 conflict 검사→kernel→raw record→shared snapshot 순서로 수리하여 bad bar에서 entry/exit 또는 episode advancement를 만들지 않는다. public quote metadata는 실제 cache의 원래 received timestamp를 공유한다.
- snapshot의 whole receipt checksum·bar digest·unique timestamp·strict OHLCV/KST/session 검증 및 symbol publication lock, checksum 없는 symbol checkpoint 차단을 보완했다. snapshot parser/acquisition hash와 replay/cost/seed hash를 분리하여 비용/seed 변경으로 원천을 재조회하지 않는다. EOD receipt generation·original retrieval time·listing symbol/route를 검증하고, remote overlap이 불완전한 revision을 드러내면 원본 bars/provenance는 보존하면서 completion을 취소한다. 같은 overlap은 original retrieval time을 유지한다. incremental fetch가 target range 밖 identifiable 오래된 잘못된 row로 새 날짜를 차단하지 않도록 범위 제외를 먼저 수행한다.
- 성장 중 당일 input과 64MiB 초과 파일은 full scan하지 않고 explicit file/source gap을 남긴다. optional event 오류·wrong symbol·naive time·nonfinite price·universe invalid를 source acceptance로 정규화하지 않는다.

## Kiwoom 공식 참조 gate

조회 `2026-09-16T23:54:47Z` (`09-17 08:54:47 KST`), upstream HEAD [`953e5dbff123f437ab4d11a78a95191a685eb51f`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f).

실제 checkout `/tmp/widget-kiwoom-reference-20260917`에서 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 ka10001/ka10004/ka10080, `postman/kiwoom-openapi.postman_collection.json`의 PRD/MOCK matching request를 교차 확인했다. REST POST path·api-id·header/continuation·stock suffix(KRX bare/NXT _NX/SOR _AL), chart `tic_scope=1`, `upd_stkpc_tp=1`, optional `base_dt`, array/분봉 time·signed price·volume·error/real-demo 계약을 검증했다. upstream revision에 `kiwoom_docs` directory가 없다는 참조 공백을 그대로 기록한다. examples는 실행 근거로 쓰지 않았다. authentication/account/order/WS 호출은 추가하지 않았으며 reference evidence는 local safety를 변경하지 않는다.

## 검증·성능 증거

합성 계산 결과는 실제 market coverage, 정책 자연 생성, 주문·비용 반영 수익 증거가 아니다. benchmark source role은 `synthetic_frozen_benchmark_only`이며 runtime publisher는 이 role의 승격을 차단한다. 경로는 `/tmp`로 고립하고 canonical report/policy/apply를 생성하지 않는다.

- bounded legacy/new oracle: full 390-bar session·전체 1,536 policies·4,224 completed episodes의 시각/가격/entry ordinal/exit/cost/경제성 dict exact equality. legacy CPU 3.769926878초/wall 4.378455053초, optimized CPU 0.223527044초/wall 0.279511430초: CPU 94.07% 감소. peak RSS 163,280KiB. fixture flat/no-episode 결과를 성능 표본으로 대체하지 않았다.
- discovery selection oracle: 26dates·32policies·160cap candidates의 selected policy·96 calibration-ready 계수·half/holdout/economics dict exact equality.
- local auto calibration legacy/new oracle: 26dates·90candidate fixture의 selected parameter·63trades·전체 출력 exact equality. zero-vs-missing 및 새 source isolation은 별도 수정된 input 계약으로 검증한다.
- full synthetic engineering benchmark: 실제 19-symbol universe·72clean trading dates·390bars/date·전체 grid/caps/halves/16day holdout, 20% quota·384MiB limit·swap 금지. wall 1,132.405초, CPU 226.485초, peak RSS 271,632KiB(약265.3MiB), systemd MemoryPeak 253,227,008bytes, swap 0. fixture SHA `e68a5b920a6bece0df470ea689890a50523db5c0e4ef220fc5b2cea9fe60317a`의 정확한 원본 digest는 아래 machine receipt에 결속한다. 이 최초 benchmark 실행 중 source/checkpoint 보완이 있었으므로 최종 exact generation의 native cold/warm 재검증을 별도로 남긴다.
- frozen snapshot warm 요청 0·credential access 없음, missing/corrupt day 및 next day만 조회, no EOD marker durable reuse 없음, day-cache corruption/source change miss, native raw writer→role census, native runtime writer→compact/raw calibration, native companion publisher→legacy execution/expanded observation loader, wrapper timeout/target/checkpoint 계약을 검증한다.

최종 source validation 전 단계 workspace 위젯·order/custody·wrapper 회귀는 741 passed, strict verifier contract는 196 passed다. 마지막 schema census 보완 후 관련 auto-policy 검증과 release 동일 계약 검증을 아래에 결속한다. compile/bash/lint/diff와 print-only parser는 통과했고 stable ID의 current parsed OPEN owner는 09-17 하나다. exact final generation native full19 cold/warm benchmark와 배포 receipt는 완료 뒤 아래에 결속한다. 실제 EOD/API acquisition 시간과 오늘 AM source/seeded signal/full-cost holdout·strict final chain은 아직 이 합성 성능 결과로 확인하지 않았다. 기존 실패 2시간13분을 완료 baseline으로 사용하지 않는다.

## 배포·rollback·자연 owner

영향받는 consumer는 `korstockscan-widget-research-watch-collector.service`, `korstockscan-widget-symbol-runtime-collector.service`, `korstockscan-samsung-widget-evaluation.service`와 기존 20:10 timer다. 기존 main/trader/legacy collectors·machine refresh·global runtime selection을 변경하지 않는다.

검증한 commit의 새로운 immutable worktree release를 만든 뒤 shared data/docs/logs/tmp/.venv/restart.flag, clean src/deploy, wrapper executable 및 actual import origin을 확인한다. 이전 drop-in 내용/hash·selector/정책 generation·실행 PID를 `data/runtime/widget_postclose_source_closure_2026-09-17.json`에 보존한다. override는 세 unit의 code root/ExecCondition/ExecStart만 지정하며 자원·budget·timer를 확대하지 않는다. raw collector는 graceful restart, inactive runtime observer는 validated raw scope로 start; inactive expensive evaluation은 timer schedule을 유지하여 자연 실행한다.

rollback은 이번 세 pin drop-in을 이전 상태로 복원하고 daemon-reload 뒤 영향 collector만 restart한다. 이전 release/selector·raw/exclusion/seed/holding receipt는 삭제하지 않는다. 오늘 seed 부재는 정상 raw-only로 축적하고 AM/20:10 평가 `not_yet_due`, strict tower→checklist→verifier `--require-summary-handoff`→controller/finalization과 비용 반영 economics는 동일 stable OPEN owner에서 실제 generation 기준으로 확인한다. 새 error detail의 실제 오류/recurrence 확인 전 producer-gap을 완료로 표시하지 않는다.

## 최종 코드 generation 검증

최종 native CLI의 research contract SHA는 `4f694f7d63321b0a1836b6592ca76269cfed995c95b7ebefc3504bdbc0ca01de`다. `/tmp/widget-native-scope-benchmark-20260917/summary.json`에 실제 `main --write`의 19종목·72거래일·전체 grid/cap/half/holdout을 기록했다. cold frozen 평가 wall **1,209.895초** / CPU **241.968초**, 같은 날짜 signed checkpoint 재시도 wall **43.818초** / CPU **8.776초**, 두 실행 모두 remote request **0**·credential access 없음·peak RSS **288,100KiB(약281.3MiB)**다. 20% CPU /384MiB/MemorySwapMax=0 transient unit은 10:11:31 정상 종료, systemd final journal은 CPU 255.413초·259.8MiB memory peak·swap peak 0B를 기록했다. 준비 작업과 warm retry를 포함한 unit CPU와 개별 CLI CPU를 구분한다. snapshot들은 synthetic fixture와 mock EOD proof로 고립돼 있으며 실제 broker/EOD source를 검증한 결과가 아니다. 실제 next-day API acquisition의 전체 19종목 시간은 미측정이고 missing-date/corruption/seed·cost 분리 계약은 targeted test로 검증했다.

마지막 schema census 보완 후 관련 63건 통과. workspace 전체 관련 회귀 741건과 strict verifier 196건, compile/ruff/bash/diff check 및 print-only parser가 통과했다. 소스의 affected producer→consumer·silent fallback·stale/missing·권한 경계 리뷰와 보완 후 **미해결 in-scope finding 0**이다. unrelated verifier/test 및 mixed wrapper/checklist 변경은 source commit에서 제외한다. immutable release의 독립 validation과 actual PID·rollback receipt는 아래 배포 결과로 추가한다.
