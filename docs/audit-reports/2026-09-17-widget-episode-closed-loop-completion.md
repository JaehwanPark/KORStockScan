# Widget/episode remaining closed-loop implementation — 2026-09-17

사용자 지시 순서: C7/C4 → episode 증분 재생 → 디스크 관리 → 최신 코드 규모 검증. 분리 worktree에서 구현하고 최신 upstream을 통합한다. Source/fixture 검증, selected release, 실제 reader PID, 자연 신규 정책 소비, 실제 비용차감 경제성을 별도로 기록한다.

## 1. C7 원 버전 실제 성과와 C4 paired joint 비교

C7은 고정 KRX 최근30일/16일과 누적 native unique attempt의 matched-exact fee/tax terminal outcomes를 사용한다. 누적6건·최근16일4건 이상이고 두 실제 net return이 비양수인 frozen candidate revision만 retired 대상으로 삼는다. Pending/CF/missing-cost와 unattributed version은 폐기 근거가 아니다. Publisher/reader가 native feedback을 독립 재구성하고 supplied feedback 정합을 검사한다. Mature retired 후보의 carry/new BUY를 차단하고 변경된 historical parameter만 새로운 prospective revision으로 등록한다. 기존 보유 exit/custody/qty10을 보존한다.

C4는 frozen calibration/holdout calendar에서 candidate와 original incumbent을 동일 fixed allocator·cash/reservation/exposure 및 fee 계약으로 재생한다. Profit/day, notional-weighted EV, worst-day와 capital occupancy를 검증한다. 진짜 신규 종목의 incumbent는 명시적인 no-entry calendar다. Incumbent trade가 없을 때 EV를 zero로 만들거나 universal zero-loss veto를 추가하지 않는다. Native baseline 누락·partial/HELD outcome은 allocation_blocked이며 independent modeled profit을 joint 실현수익으로 바꾸지 않는다.

## 2. P3 증분 재생 및 계산 경로 선택

기존 one-day lifecycle을 분리하여 day source SHA + incoming HELD state + producer/helper/cost/profile semantic key로 lossless optional checkpoints를 만들었다. 16-candidate pages, common immutable fact SHA와 compact HELD marks를 사용한다. 변경된 날에서 state가 다시 같아질 때까지 invalidation하며 rolling partition과 original episode mutation/copy 경계를 보존한다. Full grid/caps, tie/epsilon, calendar, admission/holdout/quantity는 바뀌지 않는다.

Direct transition 회귀는 warm46 hit/replay0, one-day append46 hit/replay1 및 correction parity를 검증한다. 그러나 작은 zero/COMPLETE/HELD 270-grid fixture의 persistent cache cold/append는 native 연산보다 비쌌다. 따라서 실제 measured compute/overhead로 optional backend를 선택하고 이득이 없으면 기존 빠른 reference 재생을 사용한다. Dependency 변경 또는16 observation 추가 시 재검사한다. Cache 선택은 성능 metadata이며 economics/policy fingerprint에서 분리한다. Final tiny fixture append CPU는 reference보다 약11–13% 컸으며 기존 whole-profile cache 검증/기록 비용도 포함한다. 이를 CPU 개선으로 보고하지 않는다. **항상 unchanged-day replay0, 전체 CPU50% 목표는 OPEN이다.**

## 3. P6 optional storage 관리

추가 cache payload 합계2GiB soft cap/free10GiB reserve를 적용한다. Current process identity(boot ID/PID starttime), reader/run 및 explicit persistent reference scopes를 pin한다. Dead-process unpinned optional .json.z만 LRU로 정리한다. Pins를 나이로 만료시키지 않으며 부족하면 신규 cache write를 생략/recompute한다. Raw/policy/receipt/holding ledger의 retention·authority는 그대로다. SQLite WAL catalog는 optional cache byte/LRU metadata index이며 새로운 native source database/daemon이 아니다. Catalog missing/corrupt/symlink는 safe cache miss이고 기존 facts와 정책 증거는 손대지 않는다.

Stat-only capacity receipt는 당일 raw/projection/report/cache 비중, free bytes, cap/reserve, 기존 retention 유지와30일 동일-growth 시나리오를 기록한다. 미래 성장 실측이나 raw 전체 보존기간으로 오해하지 않는다. 구현 당시 root free 약12GiB/92% 사용이므로 cache reserve가 빠르게 write를 억제할 수 있다. 활성/rollback 데이터를 지우는 정리는 하지 않는다.

## 4. Review and validation

Native WidgetState7일 실제 order projections + read-only cost adapter fixture에서 gross/fee/tax를 원 candidate revision에 귀속하고 mature carry 차단/위조 feedback 거부를 검증했다. Portfolio calendar/future exit/missing cost/depth/capital, rolling HELD alias/correction, subprocess pin/LRU, raw 보존과 corrupt/symlink fallback을 포함한다. 새 모듈은 existing monitoring/offline role에 배치하고 engine-root를 확장하지 않았다.

최종 source pytest/compile/Ruff/diff 및 latest upstream 통합 검증 결과는 아래 완료 receipt에 기록한다. Print-only backlog parser와 두 existing OPEN stable owners를 유지하며 Project/Calendar external sync는 실행하지 않는다.

## 5. Latest scale / deployment receipt

Frozen latest source의 populated390-bar fixture, G1536/cap1–5, N19/50/100 및 D72/120을 측정한다. Engineering remote0과 quota throttled wall/CPU/RSS를 별도로 보고한다. Budget 초과는 deferred_not_consumed/backlog이지 PASS가 아니다. 기존 baseline/다른 source hash 측정과 N1 CPU11.88/warm5.06초 preliminary 결과를 latest full-scale acceptance로 재사용하지 않는다.

Deployment는 latest current selector predecessor를 봉인하고 reviewed immutable source로 관련7개 code pins를 맞춘 뒤 필요한4 reader 서비스를 기동한다. Main process, policy/owner/custody/threshold/operator guards는 별도로 확인한다. 20:10/21:15 자연 실행·신규 seed 이후 widget10+16/episode30+16 qualified calendar·next-date consumption·실제 EV/net profit은 existing checklist owners의 OPEN이다.

### Final source gate

Source d49c51f7, latest upstream028141ee 통합48885ca0. 통합11 suites **1,157 PASS/88.92초**, immutable physical/shared7 suites **380 PASS/72.90초**. 마지막 HELD cache 숫자/type/finite 보완 후 관련105 PASS. Python compile/Ruff F,E9, wrapper bash-n 및 diff-check PASS. Print-only parser의 기존 두 stable owner는 각각1개다. Source scope unresolved finding0이며 full performance/natural/economics 목표는 별개다.

### C4/C7 normalized statistics scale

동일 native helper source SHA `c81a8a8e…`, CPUQuota20%/MemoryMax512MiB/Nice19에서 N19/50/100 × D72/120 총6조건의 normalized exact-cost synthetic fixtures·paired fixed allocator 집계를 완료했다. N100D120: wall5.096초, CPU1.023초(공동 비교0.326초), peakRSS158,404KiB, modeled paired24,000 trades·12,000 invented normalized outcomes·remote0. 모든 revision cumulative120/holdout16건 및 matured-retired100개를 확인했다. Broker reconciliation/acquisition·native promotion/publication 전체 체인의 실측으로 세지 않는다. Dataset/reproduction은 `analysis/benchmarks/widget_episode_completion_statistics.py`가 소유하며 기존 offline analysis role/location gate를 따르고 live consumer가 없다. Invocation은 `PYTHONPATH=. .venv/bin/python analysis/benchmarks/widget_episode_completion_statistics.py --output /tmp/completion-statistics-reproduction.json`이다.

### Supplemental shared-path review

C7 independent native reconstruction의 source receipt key를 resolved canonical shared path로 정규화했다. 같은 native bytes를 다른 release symlink에서 읽어도 동일 feedback이며 alias 회귀를 추가했다. 기존 source SHA c81a8a8e scale units는 첫 N19 checkpoint 이전 의도적으로 supersede/중단했고 latest code 성능으로 재사용하지 않는다. 최신 frozen 소스로 전체 grid 측정을 다시 시작한다. 이 수정은 economic/retirement floor·비용·qty·정책 authority를 바꾸지 않는다.

### Latest supplemental source / storage receipt

Shared-path normalization source f91b5cbf: source7 suites381 PASS/61.10초, affected C7/C4/publisher79 PASS 및 immutable r2 동일79 PASS/21.72초. Final producer/helper SHA `fa3fe2ae…` 고정. 최신 normalized statistics6조건 완료: N100D120 wall5.427초/CPU1.051초(공동 비교0.341초)/RSS156,224KiB/remote0이며 source byte/path 정합을 유지한다. 이는 full native chain throughput이 아니다.

오래된 own synthetic fixture units를 supersede한 뒤 PID identity/live·persistent pins 부재 및 optional-only 파일명들을 확인하여72,928,483bytes의 cache payload/metadata를 정리했다. 원천·정책·runtime receipt·holding은 삭제하지 않았다. 별도 외부 정리로 변한 host 전체 free space를 본 작업의 절감으로 세지 않는다.

Episode scale generator는 `analysis/benchmarks/widget_episode_incremental_scale.py`의 offline ownership이다. Native allowlist guard가 invented symbol을 거부했으므로 guard를 유지하고 기존61 templates의 첫19개 원 symbol/profile 및 모든 native grid를 그대로 사용한다. Synthetic390-bar D120/D121 cold/warm/append 결과를 original no-cache와 비교하고 oracle/preparation CPU를 candidate compute와 분리한다. No broker/native policy acceptance이며 actual source/registry에 fixture를 기록하지 않는다.

### Latest upstream integration and final review repair

Latest upstream35955c5f native replay/EV distribution/signal-fact fast path를9031cb65에 통합했다. 12-suite source887 PASS/136.64초, immutable r3 physical/shared397 PASS/78.95초. 이후 upstreamf826ebcb의 test-only clock/source isolation을 통합하고 incoming190 PASS/15.22초를 확인했다.

최종 C4 재검토에서 episode legs가 absent/empty/one-leg여도 빈 reference로 바뀌는 누락을 수정했다. 정확히2개의 COMPLETE native legs만 변환하며 no-entry의 빈 episodes calendar와 구분한다. Final source c7292edd는 해당 보완 source83 PASS/16.97초 및 immutable r4 동일83 PASS/21.45초, Ruff/compile/diff-check와 print-only parser를 통과했다. 기존 admission/비용/qty10/holding exit/allocator·custody·threshold guards를 변경하지 않았다. Source scope unresolved finding0.

규모 측정 frozen source는 widget discovery f91b5cbf 및 episode native replay9031cb65다. 최종 변경은 C4 malformed-leg 변환 거부이며 두 측정 경로는 이 함수를 실행하지 않는다. Widget discovery/cache bytes와 episode native replay/checkpoint bytes가 final source와 동일함을 파일 SHA로 검증했다. Whole producer helper SHA는 final475e5d500c0dce57…로 달라졌으므로 이전fa3fe2ae…를 최신 전체 hash로 주장하지 않는다. Latest C4/C7 normalized synthetic6조건을 final source에서 다시 측정했다. N100D120 wall5.196초/CPU1.036초(공동 비교0.326초), RSS156,900KiB, remote0;6조건의 paired economics digest는 이전 source와 모두 일치했다. Feedback digest에는 별도 temporary source directory provenance가 포함되므로 독립 실행끼리 같은 digest를 요구하지 않는다. 이는 비용·원천 획득·발행·consumer 전체 native chain throughput 증명이 아니다.

### Final full-grid engineering scale closure

Engineering resource 계약은 CPUQuota20%/MemoryMax512MiB/Nice19이며 실제 운영 unit 자원을 증설하지 않았다. Invented390-bar fixture의 full widget G1536/caps1–5를 유지했다. N19D72: cold wall670.393초/CPU131.957초, warm293.99996초/58.804초, appendD73 300.598초/60.136초. Cold/warm digest 동일, warm1,634,608hit·miss0, append기존1,634,608hit/신규29,184miss(19×1536), write-skip0, RSS171,400KiB, remote0.

N100D120 cold는 N19 wall1,201.015초/CPU237.794초, N50 wall3,126.418초/CPU621.739초/RSS205,872KiB checkpoint를 남겼다. Final87종목 완료/13종목 미처리, observed unit elapsed5,413초/CPU1,077.837초, budget 초과exit75/deferred. 100종목 전체 PASS가 아니며 이13개는 synthetic fixture backlog다. 실제 runtime backlog나 승격 증거로 바꾸지 않는다. Remaining N50/N100D72 및 N100D120 warm/append의 full native chain acceptance를 추정으로 채우지 않는다.

Latest native episode first19 existing templates/G총30,780(270/810/1350/2700/2970/5130/5940), D120/D121: cold candidate wall556.251초/CPU111.196초, warm1.478초/0.265초, append99.640초/19.874초. Whole-profile warm19hit, append19개는 measured cache-disabled fast-reference다. Cold/warm·append 모두 original no-cache canonical parity PASS이며 앞 source와 경제성 digest도 같다. Preparation CPU는 각13.81/13.62/13.73초, original comparison CPU53.28/0/52.83초(deepcopy 포함)로 candidate compute와 분리한다. RSS최대390,780KiB/remote0. Warm1.478초를 모든 preparation/native source 획득을 포함한 wall로 세지 않는다.

추가 metadata/fixtures의 scale receipt는 [source와 측정 범위/잔여량 결속](../../data/runtime/widget_episode_completion_scale_review_2026-09-17.json)을 참조한다. Cold optional checkpoint probe가 원본보다 비싸며 항상 unchanged-day replay0/전체 CPU50%는 OPEN이다. Largest unit MemorySwapPeak56,217,600bytes, episode final 직전 sample319,488bytes로 swap0 목표도 미달이다. RSS는512MiB 안이지만 P6 전체 baseline 이하·zero-swap acceptance를 주장하지 않는다. 다음 성능 owner는 full-grid probe/cache overhead와 lossless cold computation 재사용을 줄이고 동일 grid/calendar/원본 결과/단위 자원으로 재검증해야 한다. Admission/종목/grid/표본 축소로 목표를 맞추지 않는다. 기존20:10/21:15 natural policy와 real economics owners는 OPEN이다.

### Final predecessor preservation, deployment and actual acknowledgement

동시 배포 predecessor48a94cf1의 native source에는9d8fe03f optional deep-JSON RecursionError safe-miss 보완이 있었다. Source parent를 통합하여 관련decoder/transaction 회귀를 보존했고 latest AI phase diagnostics도 유지했다. Final source supplement85 PASS/15.84초, immutable r6 native/publisher/cache 및 incoming phase4-suite296 PASS/21.73초. Final helper SHA는 `fba8fade23708b4d96923e219890fdd4f9335e1ab3b55336d24d3a33e0ddc642`다. N19/50/100 × D72/120 normalized statistics6조건을 이 소스로 재완료했으며 N100D120 wall5.109초/CPU1.034초/pairedCPU0.333초/RSS156,936KiB/remote0였다. Cold/warm discovery와 native episode의 frozen measurement와 최종 byte/정상 분기 동등성을 explicit receipt로 분리한다. Malformed-leg rejection·optional deep-JSON exception repair가 valid benchmark 구간을 실행하지 않으며 full native end-to-end 성능 PASS로 격상하지 않는다.

배포 helper preflight에서 empty systemd property/0644 wrapper invocation·권한 제한과 boot 중 일시적 cwd 확인을 보완했다. Failed attempts는 selector/pin rollback을 수행했고, 실제 서비스 재시작이 있었던 시도는 기존 소스로 되돌렸다. Final helper는 `bash` wrapper 호출, privileged read-only `/proc` 검사,60초 이내 모든 실제 cwd 일치 대기를 사용한다. 검증을 생략하거나 다른 cwd를 허용하지 않았다. Source/guard/resource review에서 남은 in-scope finding0.

**17:39:32 KST selected/pushed immutable source fdc28f25**, `/home/ubuntu/KORStockScan-runtime-releases/widget-episode-completion-r6-20260917`. Related7개 effective source pins/cron9/postclose print-plan가 동일 release로 확인됐다. 필요한4서비스 active/NRestarts0/actual cwd=release: widget859572, episode859558, research-watch859667, symbol-runtime859568. Main780712/67da0cc7 cwd/src를 유지했고 main이 신규 selected source를 소비했다는 flag는 false다. Source-only routing과 main PID 소비를 합치지 않는다. CPUQuota/MemoryMax/Nice/EnvironmentFiles/기존 guard·argv·condition은 root aliases 외 동일하며 policy/registry/custody/threshold/operator6개 SHA도 모두 같았다.

Actual native C6 receipt는 widget3종목005930/034020/042660, episode3프로필auto_028670_midday/auto_034020_midday/auto_111770_late_morning을 `consumed`, rejected0, import_root/cwd=release로 확인했다. 기존 검증된 incumbent 소비이며 새로운 prospective candidate 승격이나 신규 주문/실현이익 증명이 아니다. [Sanitized 실제 deployment/consumer receipt](../../data/runtime/widget_episode_completion_acceptance_2026-09-17.json)와 [규모/저장소 receipt](../../data/runtime/widget_episode_completion_scale_review_2026-09-17.json)가 source binding과 실제 scope를 소유한다.

**잔여 acceptance:** N100D1205400초 미달/13fixture backlog·untested native 규모 조건, adaptive backend의 universal day-replay0/overallCPU50%, swap0·전체 cold baseline 이하가 OPEN이다. Lossless cold replay/whole-grid probe overhead 축소 후 동일 grid/source/자원으로 재검증한다. 오늘20:10 evaluation/21:15 final refresh는 배포 당시 not_yet_due이며 자연 신규 종목/정책10+16 widget·30+16 episode qualified calendar, next-date 실제 소비와 version 비용차감 EV/net profit은 기존2개 OPEN owner가 담당한다. Broad postclose regeneration/외부 sync/추가 main restart/직접 주문은 실행하지 않았다.


### Bounded cold-probe follow-up

사용자가 과도한 성능 검증과 불필요한 코드 확장을 금지한 후속 범위다. 기존 episode checkpoint의 초기 backend probe를 기존16-candidate page 하나로 제한했다. Cache 처리 CPU가 원 재생보다 크면 나머지 후보는 fast-reference로 끝까지 평가하며 useful warm cache는 유지한다. 신규 module/collector/job/benchmark와 영속 EV 통계는 추가하지 않았다. 원 grid/calendar/비용/수량/holding alias/승격 floor 및 주문·custody·safety 계약은 그대로다. Prefix proof 없는 raw delta는 기존 full fallback을 유지한다.

관련3-suite218 PASS/41.47초와 추가 quote/runtime/closed-loop6-suite145 PASS/18.70초(일부 중복)를 확인했다. 추가 회귀는 미진입·청산·보유 상태에서 probe 중단 이후에도 전수 후보 수와 원 선정/경제성 동일함을 검증한다. Self review → supplemental fix → re-review에서 범위 내 미해결 finding0. Ruff F,E9/compile/diff-check와 print-only parser를 적용하며 큰 규모 조건을 반복하지 않는다.

기존 offline fixture를 CPUQuota20%/MemoryMax512MiB/Nice19로 제한했다. Episode3 native templates,46일/append47일, G총6,480: cold compute wall7.418초/CPU1.462초, warm0.200초/0.040초, append6.734초/1.344초. 원본 canonical parity와 full grid를 확인했다. 별도 original comparison CPU3.194/0/3.319초에는 deepcopy가 포함되므로 순수 재생 대비 감소율로 주장하지 않는다. RSS최대225,472KiB·remote0. Widget2종목,32일/append33일, G1536/cap1–5: cold21.785초/CPU4.346초, warm11.097초/2.218초, append12.195초/2.435초. Warm49,184hit/miss0·cold/warm digest 동일, append49,184hit/신규3,072miss·write-skip0·RSS140,556KiB·remote0. Widget CLI 최소 fixture 기간32일을 따르며 실제 widget10+16/episode30+16 qualified calendar를 줄인 것이 아니다. 전체 시장 native/source acquisition/publication throughput이나100종목 deadline/무조건 replay0/swap0 달성을 추정하지 않는다.

종료된 optional synthetic cache2개, 사용되지 않는 원격 복구 가능 배포본9개, 작업본1개를 삭제해 allocated1.580GiB를 확보했다. 삭제 시 현재/이전 selector·실제 PID·effective systemd/EnvironmentFiles·dirty/untracked source·원격 복구 가능 여부를 확인했다. 고유 변경/설정이 있거나 원격 Git-tree 원본과 같다고 증명할 수 없는 복사본은 보존했다. 원천 시장/연구 데이터·정책·holding/receipt/운영 권한 파일은 삭제하지 않았다. 신규 배포본은 하나만 만들고 현재 release는 rollback으로 보존한다.

Source commit/push와 actual release/PID 기동 receipt는 아래 배포 완료 후 기록한다. 기존 두 stable owners의 자연20:10/21:15 생성·다음 날짜 신규 정책 소비·실제 비용차감 EV/net profit은 계속 OPEN이다.
