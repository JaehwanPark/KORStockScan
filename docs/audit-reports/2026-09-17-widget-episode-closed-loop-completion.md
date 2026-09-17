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
