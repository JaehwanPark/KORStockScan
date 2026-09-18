# scale_in_split_order_plan 체결 실적 기반 조건부 경제성 튜닝 상세 개선계획 — 2026-09-18

## 1. 확정 방향·범위

**실제 체결 실적이 있을 때만 조건부 평가한다.** 장후마다 전체 pipeline을 읽어 후보0을 반복 생성하는 운영을 끝내고, 새로운 평가 가능 체결 outcome 또는 기존 체결의 유효한 후행 outcome 변경이 있을 때만 경제성 평가를 수행한다. 조건부 trigger 판정은 기존 장후 호출에서 가볍게 수행한다. 별도 cron·상시 worker·새 수집기는 만들지 않는다.

상태는 **CS0–CS5 구현·반복 리뷰와 영향 계약 검증 완료**다. 사용자가 구현·commit/push·배포와 제한 장후 재생성을 승인했다. CS6 배포·결과 receipt는 [구현 review](../audit-reports/2026-09-18-scale-in-fill-conditioned-tuning-implementation-review.md)를 따른다. 실제 정책 선택·PID·자연 체결/COMPLETED 경제성은 별도이며 기존 실행 owner의 Acceptance는 OPEN이다.

- 대상: Main scalping의 실제 AVG_DOWN 추가매수 주문 분할 비율·가격 간격. 총수량·총허용예산·기존 TTL을 고정한다.
- 상위 반등/ADD 판단은 현행 Main 공통 기계 판정과 기존 AI/주문/손절 guard가 소유한다. 독립 AVG_DOWN 반등 threshold·PYRAMID·초기진입·widget/episode/manual·Swing 튜닝을 복원하지 않는다.
- 평가 모집단은 체결이 발생한 제출 시도다. 미진입 전체 기회·BLOCK/RECHECK/VETO 경제성과 별개이며, 이 결과를 전체 AVG_DOWN 실행 여부나 전체 전략 EV 개선으로 확대하지 않는다.
- 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`을 실행 owner로 재사용한다. CS0–CS6는 구현 순서 ID이며 새로운 checklist owner가 아니다.
- clean baseline `2026-06-05 KST`, custody·operator veto·quantity/cap·broker/account·freshness/conflict·pending/cooldown·hard/protect/emergency stop과 정책 rollback을 보존한다. 표본 확보 목적의 주문·수량 증대·시장가 전환은 없다.

근거: [현재 개별단위 분석](../audit-reports/2026-09-18-scale-in-split-order-plan-result-analysis.md), [현행 scale-in 범위 정정](scale-in-pyramid-avg-down-economic-tuning-implementation-plan-2026-09-17.md), [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [오늘 checklist](../checklists/2026-09-18-stage2-todo-checklist.md).

## 2. 현재 결손과 개선 목표

9/17 실행은 exit 0/22.392초, 당일 unique attempt 0이다. 최근 보고서의 과거 시도 4건은 모두 market-like이며, 그중 3건은 요청 수량 1, 2건은 기준가격 재구성 결손이다(사유 중복). eligible·real outcome·추가 MFE/MAE·paired는 모두 0, runtime 후보 0/apply=false, EV/net=null이다. 이 4건은 유효 경제성 표본이 아니며, 시간 경과만으로 분할 대상이 되지 않는다.

| 현재 경계 | 보완 방향 | 완료 기준 |
| --- | --- | --- |
| no-yield day에도 raw presence precheck 순회 | 실제 execution fact를 먼저 확인 | 체결0/새평가가능outcome0이면 raw/replay/grid 호출0 |
| scale 평가가 exact trade fact sync보다 앞섬 | canonical fact sync receipt 이후에 trigger/평가 | 최신 체결·COMPLETED 사실을 읽고 Daily/EV보다 먼저 결과 인계 |
| 과거cached daily outcome은 후행 재결합 안 됨 | 실제 filled pending ID만 source 변경 시 재결합 | 다음날 terminal 도착으로 outcome version이 갱신되고 같은시도중복0 |
| 같은rolling 표본으로선택·수락 | 날짜/episode 분리 calibration→holdout | holdout을보지않고후보1개선택·실패후차순위탐색금지 |
| 가격touch→leg전체체결 가정 | 관측가능한 실행 모델 검증·불확실표본분리 | actual receipt와 model error 대사, 미입증fill은진단/null |
| 비분할control만비교 | 실제 incumbent replay를 primary control로 고정 | 자기비교는보존판정, current보다개선된유일후보만검증 |
| atomic missing-plan census가첫plan에의존 | 계약시작일/actual submit·fill에서 독립검사 | 계획이하나도없는실제제출도missing-plan으로검출 |

실행시간 단축의 핵심은 **실적없는 날과 변경없는 outcome의 계산을 제거**하는 것이다. 새 cache framework·성능 guard·과도한 병렬화로 결손을 덮지 않는다.

## 3. 두 단계 조건부 trigger

### 3.1 실제 체결 존재 확인

기존 execution receipt와 exact trade fact sync가 소유한 canonical 실제 체결 fact를 첫 입력으로 사용한다. broker order/실행번호·owner·AVG_DOWN·실제양의체결량·체결시각을 확인한다. submitted flag나 assumed_fill·probe/sim·주문생성·수익필드존재는 실제 체결을 대신하지 않는다.

CS0에서 DB/receipt materialization의 정확한 producer→schema/path→consumer를 먼저 확인한다. `main_lifecycle_journal`은 현재 live path에서 기존pipeline identity를 제공하는 모듈이며 **독립 compact journal 파일이 항상 생성된다고 가정하지 않는다**. 존재가 입증된 exact fact/receipt 조회를 재사용한다. 신규 API·계좌/호가 조회·동기 live 파일쓰기·전용 collector를 추가하지 않는다. execution fact catalog가 없거나 stale/invalid이면 `blocked_execution_source`이지 `skipped_no_actual_fill`이 아니다.

신규실제체결이없어도, 이미체결된pending시도의청산/가격경로/비용/correction이새로완성된경우는trigger대상이다. clock·reportgenerated_at만바뀐경우는변경으로세지않는다. 기존체결0인상태에서force/코드버전/일자변경만으로평가를열수없다.

### 3.2 경제성 평가 가능 표본 확인

actual filled inventory를 `full_fill`, `partial_fill`, `filled_pending_terminal`, `filled_source_blocked`, `not_applicable`로 분리한다. 무체결 제출·취소는 분모/제외진단에만 남기며 평가 trigger가 아니다. partial은 실제체결 inventory에 포함하되 기존full-fill 경제성 표본에 합치지 않는다.

후보 평가 시작 조건은 `actual_fill_exists && new_or_updated_evaluable_full_outcome_count > 0 && source_preflight_valid`다. 실제체결이있어도완료청산·수량·비용·가격경로가미확정이면pending으로끝내고grid를돌리지않는다. 기존유효표본과함께rolling 평가하되모든행의actual origin은유지한다.

| 입력 상태 | 동작·출력 | 정책 영향 |
| --- | --- | --- |
| 정상execution source,실제체결0 | skipped_no_actual_fill;평가/EV/netnull | 기존정책상태보존 |
| 체결존재,모두market/qty1등비적용 | skipped_no_applicable_fill;사유별분모 | 기준완화·quantity변경없음 |
| 유효체결,terminal/경로/비용미완성 | pending_filled_outcome;해소조건표시 | grid/replay없음 |
| 경제성입력fingerprint동일 | skipped_unchanged_filled_outcome;마지막유효평가참조 | 새성공/표본으로집계금지 |
| 새ready full outcome존재 | evaluated;정확변경ID와유효rolling대조 | 아래모든선정gate후후보판정 |
| catalog/preflight/identity전역결손 | blocked_execution_source/source_contract | no-trade/no-edge로대체금지 |

`evaluated` 내부결과는기존hold_sample/hold_no_edge/후보ready를분리한다. skip/pending은정상조건부terminal이지만sourceblocked는별도block이다. null을순익0으로채우지않는다.

## 4. 원천·후행 재결합 계약

기존 report의 `input_summary.trigger_contract`와 `daily_attempt_outcomes`를 확장하는 것을 우선한다. wrapper의 기존status receipt로skip을기록하며 skip일에대형후보보고서/정책을새로쓰기않는다. 마지막유효평가의source_date/generated_at/평가범위는그대로보존한다.

- 시도identity: 실제owner·position/episode/lifecycle·AVG_DOWN decision·broker order/원주문/leg 관계. retry/정정·여러체결을원시도에결속하고order+execution_no별중복/충돌을검사한다.
- frozen 입력: 당시requested_qty·기준가격·정확route/venue/session·clock/source_digest·incumbent policy version/hash·atomic quantity/leg/price plan. 실제체결량에서원requested_qty나예산을역산하지않는다.
- fill/terminal: execution timestamp·integral quantity·가격·actual origin·완료SELL·cost source/단위·수량귀속을연결한다. net PnL은`COMPLETED + valid profit/cost`에서만정의한다. 보유전체청산손익을AVG_DOWN 추가분에그대로귀속하지않고추가fill lot의수량/청산basis를입증한다.
- price path: 같은route/session의당시관측만사용한다. ownfill price를독립market observation으로세지않는다. 미래행·stale/conflict·epoch/route단절을제외하며180초범위/기존TTL을보존한다. 청산이후가격은판정근거로유입되지않는다.
- pending 재결합: 기존filled pending ID와후행exact source변경만조회한다. 날짜가바뀌어도원anchor date를보존하고terminal date는별도필드로둔다. immutable원보고서를덮어쓰지않고현재report의versioned outcome에서같은attempt의최신유효revision 한개만사용한다.
- fingerprint: 정렬된 eligible attempt ID·outcome/source revision·incumbent/grid/model/cost/평가 contract 버전·실제 관측 경로의 cutoff를 결속한다. cutoff는 관측자료의 유효 범위이며 매일 바뀌는 scheduler as_of가 아니다. 일자·wallclock·mtime 변경이나 rolling window의 노후 행 제외만으로 heavy 평가를 열지 않는다. 모델/계약 변경에 따른 기존 체결 재분석은 별도 명시된 구현 검증 범위에서 수행하며, 매일 자동 재분석하는 우회 trigger로 사용하지 않는다. 실패/중단은 성공 cursor로 기록하지 않고 유효 완료 보고서와 evaluation key를 기존 atomic writer/lock으로 함께 확정한다.
- 소스보존실패: 식별가능한bad row/window만제외한다. 식별불가preflight/전역계약결손에서만전체block한다. 과거price/receipt가없으면excluded_source_gap으로남기고반복raw재조회/가상fill로복구하지않는다.

경제성 rolling 모집단은 기존 최근 20 report date를 유지한다. pending identity의 원청산/custody 기록은 이 연구 window와 별개로 보존한다. window 밖에서 늦게 완료된 체결은 outside_research_window로 구분하며 과거 자료를 무제한 재순회하거나 표본 기간을 자동 확장하지 않는다. 오래 pending인 행을 경제성 0으로 바꾸지 않는다. 보존 범위를 벗어나 원천이 없는 경우에는 closure 불능 사유를 남기고 보호된 custody/원장을 삭제하지 않는다.

## 5. 개선을 찾는 경제성 비교

### 5.1 control·후보

**primary control은동일기회에서실제현행incumbent를재현한실행계획**이다. incumbent가비분할이면기존unsplit control과같다. 고정unsplit 결과는별도진단으로남기되이미적용중인분할보다나쁜후보가unsplit만이겼다고개선으로선정되지않는다.

canonical 정책/실제price-qty plan별중복을제거한다. 기존정책이후보1위면`incumbent_preserved`로닫고신규개선검증성공으로세지않는다. 같은반올림결과/동일tick/동일qty계획의메타데이터차이는별도정책이아니다.

초기탐색은기존70:30/50:50의0/−0.3%,60:40의0/−0.8%와기존heuristic grid를유지한다. 각후보의총수량·허용자금·route/session·TTL·terminal·fee/tax/slippage 모델을같게한다. market-like/qty1은제외하며3leg는진단전용이다. 넓은grid·독립NO_ADD/반등threshold·모델추가는금지한다. 후보간경제적차이가관측될때만후속범위에서grid확장가치를판단한다.

### 5.2 지표

`model_delta_ev_pct = 100 × Σ(candidate_model_net_pnl − incumbent_model_net_pnl) / Σ(frozen_base_price × frozen_requested_qty)`를primary modeled증분지표로사용한다. 절대model EV·actual net PnL·equal-weight diagnostic은별도로표시한다.

같은paired 표본과날짜별동일기회범위에서Δ순익KRW·일별Δ순익·관측일당평균Δ순익·worst day·p10·fill참여·취소/partial·자금점유를표시한다. 데이터없는calendar day를0으로추가하지않는다. weighted ΔEV와aggregate Δ순익은같은ΔPnL분자에서나오므로독립적인성공증거두개라고집계하지않는다.

미체결candidate leg의0 realized model PnL은경로가TTL까지충분히관측되고no-fill/cost가정이정의됐을때만가능하다. 짧은경로·미청산·missing fee는null/censored다. 실제비용receipt가없고표준비용모델을썼다면model_cost로표시하고broker 실제납부비용으로설명하지않는다.

### 5.3 체결 모델의 단계적 보완

가격 touch만으로 leg 전체 수량의 체결을 단정하지 않는다. 기존 source에서 BBO/depth·trade size·동일 venue clock·실제 fill을 확인한다. 정확한 queue를 모르는 경우에도 관측 자료로 보수적 체결 범위와 모델 오차를 입증할 수 있으면 그 범위에서 평가한다. touch 자료만 있거나 후보 체결 범위를 입증할 수 없으면 touch_proxy_diagnostic으로 분리하고 해당 행의 검증된 candidate fill/승격 EV는 null로 둔다. 과거 원천이 없다는 이유로 새 collector/API/고빈도 capture를 추가하지 않는다.

실제incumbent full-fill 표본에서예측체결량/가격/TTL과actualreceipt의model error를먼저대사한다. 후보는같은관측가능한체결모델로평가하고, 가능한유리/보수 fill/cost/slippage scenario에서우위방향을확인한다. 정확queue를관측못하는경우의bounds는관측된depth/계약에서만정의하며임의전량fill·임의penalty계수로양수edge를만들지않는다. 후보의실제체결품질은이후actual 적용버전으로따로검증한다.

## 6. 독립 날짜 검증·선정 규칙

기존최근20 available report date/clean baseline 범위를보존한다. 오래된날짜를채워기간을인위적으로넓히거나표본이없다고holdout을줄이지않는다. 순서는다음으로고정한다.

1. outcome가ready인episode/원decision 전체를날짜순으로묶는다. 동일position의여러ADD/leg·retry·후행청산행을같은partition에둔다.
2. 과거calibration으로만후보를선택한다. calibration outcome의최종사용가능시각은holdout 시작보다앞서야한다. terminal이holdout기간에걸친episode는training에서purge하여후행정보누수를막는다.
3. 초기 partition은 시간순으로 가장 최근의 미사용 독립 source date 2일을 holdout으로 예약하고, 그 이전 최소 2일을 calibration으로 둔다. 각 구간의 표본 floor와 purge를 모두 만족하지 못하면 hold_sample이다. holdout 예약은 성과값을 보기 전에 결정하며, 실제 검증한 날짜만 consumed로 기록한다. calibration에서incumbent보다우위인정책1개만동결한다. 최신독립날짜holdout에서한번검증한다. 실패후holdout을보고차순위후보/다른grid를탐색하지않는다.
4. 기존gate의paired≥3/완료real outcome≥3/MFE·MAE≥3/경제성날짜≥2/price coverage≥80%/ΔEV≥+0.10%/modeledfill참여≥70%/p10Δ≥−0.30%p를calibration에유지한다. source coverage의분모는시장가/qty1 제외이전census와eligible 분모를함께명시한다.
5. **추가holdout설계**는독립paired≥3·source dates≥2를초기최소로고정하고동일EV/fill/tail gate와같은날짜집합의평균Δ순익KRW>0을검증한다. 이최소표본은충분한통계적확신을보장하지않는다. 표본이없으면hold_sample이며즉시live 승격을만들지않는다.
6. 같은holdout을반복선택에재사용하지않는다. 검증후learning에편입한날짜는다음후보의holdout이아니며새독립날짜가필요하다. model/grid 변경시이력·소모된holdout을보존한다.

모집단은**실제full-fill된유효AVG_DOWN 시도에조건부**다. partial/no-fill census와excluded/pending 비율을함께보고하여선택편향을노출한다. 그표본에서좋은분할이모든미체결/미진입기회에도좋다고주장하지않는다. 새로운source quality 상태가없는actualfill ledger라면sourceblocked를닫는것이먼저다.

## 7. 장후 consumer·장중 적용 경계

실행순서를 `기존 exact trade fact sync/검증 → 가벼운 체결/변경 trigger → 조건부 평가 → Daily/EV/runtime summary → 기존 tower/checklist/strict handoff`로정리한다. 기존sync를추가로실행하거나DB갱신을평가함수안에숨기지않는다. `--skip-db`/sync미실행에서최신유효receipt를입증못하면sourceblock하며추가provider호출로대체하지않는다.

- wrapper: trigger 판정은resource-heavy wait/replay앞에서수행한다. skipped/pending이면대형report·policy 파일대기를없애고기존step status receipt를검증한다. sourceblocked/실패는명시terminal로남긴다.
- Daily/EV/tower/strict: conditional skip·pending·blocked·evaluated를schema로소비한다. mandatory current step status와optional historical last-valid evaluation을분리한다. skip일의report부재를실패로만들거나과거성과를새날짜의성공으로재집계하지않는다.
- 정책발행: **비싼평가와가벼운dated incumbent carry를분리**한다. 체결0이라도이미승인된유효incumbent를다음정확KRX날짜로carry해야하는기존계약은유지한다. 유효prior없는상태에서기본50:50/applytrue를합성하지않는다. source_date/원review hash/승인·expiry와기존최대age 검증을보존하고허위재생성으로age를연장하지않는다.
- PREOPEN: source/model/grid/holdout/평가contract와selected/approval hash를결속한다. 현재v3모델gate만보는경로를새계약에맞춰producer와consumer 함께version bump한다. 구v3를새holdout검증완료로묵시승계하지않으며별도로승인된prior의carry 경계는그대로보존한다.
- 장중: 기존 `apply_scale_in_split_order_policy` 호출을재사용한다. AVG_DOWN-only·qty>1·non-market·fresh quote·policy/bucket/version/age·atomicplan·quantity conservation 검증과최종cap재검증을보존한다. 조건미충족이면기존base order를유지하며강제ADD/분할/청산이나수량증가는없다.
- 권한: holdout통과의`research_candidate_ready`와실제선정/적용승인을구분한다. CF 결과로새broker/order권한을만들지않는다. 기존동일stage bounded apply/canary·deterministic/AI·approval/rollback 계약을모두닫은경우에만기존PREOPEN 경로로인계한다. 유효승인없으면incumbent유지이며매일새수동승인절차를추가하지않는다.
- R6: 실제policy version/hash→order/leg→execution→COMPLETED를결속해actual EV/net·partial/no-fill·비용·노출·tail/model error를보고한다. actual정책손익은실현값이고model control 대비Δ는추정비교다. 동일기회actual 대조군없는상태에서인과적실현증분이익이라고단정하지않는다. 기존negative evidence rollback을보존하며임의lock해제/age만으로권한만료없음.

## 8. 구현 순서·위치·Acceptance

새production/test Python 모듈·package·CLI·service·cron은기본0개다. 기존role 파일에작은private helper/adapter를넣는다. 새파일이불가피하면AGENTS location gate와실제caller를먼저확인한다.

| ID | 기존변경위치·작업 | Acceptance |
| --- | --- | --- |
| CS0 | `sniper_execution_receipts.py`, `scalping/main_lifecycle_journal.py`, 기존exact fact producer의actualfill/owner/receipt경로확인. 의존성이기록된입력계약정의 | producer/path/schema/실제consumer 입증; assumedfill미포함·missingcatalog와0fill분리 |
| CS1 | `scalping/scale_in_split_order_plan.py` 및 `deploy/run_threshold_cycle_postclose.sh`: sync뒤trigger/semantic fingerprint·skip/status·pending inventory | actualfill0/변경0/ready0에서raw/replay/grid/새 candidate policy 발행 0; 승인된 incumbent dated carry는 §7 경계에서 별도 처리; wrapper/strict terminal 일치 |
| CS2 | 같은producer의daily_outcome loader/join: pendingfilled revision·시계/receipt/atomic검사·수량귀속 | 늦은terminal/다중fill/correction 재결합·attempt중복0·무plan actualsubmit검출 |
| CS3 | 같은producer의replay/grid/metric: incumbentcontrol·policy중복제거·실행model/비용근거·dailyΔ | 자기비교보존·유효common cohort·불확실체결/null·model vs actual분리 |
| CS4 | 같은producer의calibration/holdout/selector | 날짜/episode/purge·최소floors·후보1개freeze·holdout 실패후재탐색0 |
| CS5 | 기존Daily/EV/runtime summary/tower/strict/PREOPEN consumer 및기존tests | skipped/pending/blocked/evaluated·datedcarry·sourcehash 계약끝까지일치; legacy자동승격없음 |
| CS6 | review→수정→re-review→영향pytest/compile/bash-n/diff→승인된배포·자연소비확인 | source/PID/체결/COMPLETED/EV를분리. fixture로자연체결/실제순익완료를대신하지않음 |

CS0–CS2를 먼저 닫고 실제 filled source yield를 확인한다. 무체결이면 CS1의 정상 skip은 운영 동작의 완료이며, CS3–CS4의 경제성 검증 완료를 뜻하지 않는다. CS3–CS5 코드는 작은 fixture로 구현 검증할 수 있지만 실제 경제성은 자연 표본을 기다린다. Source가 충분해져도 CS5의 장중 적용 계약이 닫히기 전 새 후보를 live로 내보내지 않는다.

## 9. 필요한 회귀·제한 검증

기존관련test 파일에계약을검증하는최소회귀만추가한다.

- 정상0fill·submitted-only·sim/probe·market/qty1·실제partial에서skip/pending분리와heavy 함수호출0.
- 같은execution 중복·동일ID충돌·정정/재시도·filledterminal후착→정확revision/중복0. 다른owner/venue/미래/가격충돌은제외.
- 실제submit이있지만atomicplan전체0인경우pending으로숨기지않음. 실제requested qty를fill에서역산하지않음.
- incumbent identical plan이1위면보존,이미분할incumbent보다나쁜후보가unsplit만이겨서선정되지않음.
- 짧은 price path/체결 범위 미입증/cost gap은 censored/null; validTTL no-fill model과구분. 실제fill과model touch의오차관측.
- episode/leg간holdout누수·terminal후행누수·holdout실패후차순위재선택차단. consumedholdout 재사용금지.
- wrapper의sync→trigger→conditional평가→Daily/strict순서,skip일파일부재,datedprior carry·구schema/부정확hash·age/approval 검증.

작은fixture로유효한**새filled outcome**과**기존filled pending의late terminal** 두경로의producer→최종consumer를검증한다. 변경없는그룹은차분결과동일성으로재사용한다. Python 영향pytest/compile·bash-n/contract·git diff--check, 문서는link/owner/authority·print-only parser만수행한다. provider/실주문/전체chain/5.7GB raw 반복은검증방법으로쓰지않는다.

## 10. 성능·중단 기준과 완료 보고

우선순위는체결identity/완료cost·후행join→independent검증→기존consumer/PREOPEN→계산시간이다. no-fill/unchanged일raw읽기0을핵심으로하고, filled일에는변경attempt/pending exactsource 및기존window만처리한다. 큰active JSONL은stat후compact/manifest/이미보존된bounded source만사용한다. canonical소스를조회할방법이없으면sourceblock을명시하며모든raw를매일읽는fallback을붙이지않는다.

실행비용이높으면신규grid/부차적시나리오분석깊이를먼저줄이고기존기준후보와선택된1개의독립검증에집중한다. clean baseline·incumbent control·holdout·cost·source coverage·hard safety를줄여성공을만들지않는다. 과도한benchmark·cache/worker확장·추가performance guard는없다.

최종보고는 `trigger/source 상태 → actualfill/eligible/partial/pending/excluded 분모 → calibration/holdout modeled ΔEV·일별Δ순익 → 선정/정책/실제PID → actualCOMPLETED EV/net → 결손owner/다음조치` 순서다. 체결0은정상조건부skip,양수edge없음은hold_no_edge,필수원천없음은sourceblocked다. 경제성완료ETA는현재null이며실제체결/원천이없을때새효과를약속하지않는다.
