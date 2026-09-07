# Scanner lookup-attention tuning 최종 구현·리뷰

기준일: 2026-09-07 KST
범위: 장후 #49 `Scanner lookup-attention tuning`

현행 판정(2026-09-07 보완 실행): **R1~R5 구현·재리뷰 종결, lookup 변경 범위 미해결 finding 0, 마지막 확대 회귀1,036 PASS**. 현행 근거는 마지막의 `R1~R5 보완 구현과 최종 재리뷰`다. 아래 최초 v3 구현 및 13:19 재점검은 역사 기록이다. 실제 양의 EV·새 PID의 적용은 아직 미검증이며 운영 정책 발행·봇 재기동은 이번 작업에서 수행하지 않았다.

## 최초 구현 판정 — 아래 재점검으로 대체

권장 보완은 코드 수준에서 종결했다. 기존 구현의 목적은 `ka00198` 실시간 조회순위·순위상승·신규 top20을 0~1 관심도로 만들고, 비용 차감 EV가 확인된 경우 이미 선택된 KRX 정규장 scanner priority tier 내부에서만 0~200점 보너스를 자동 적용하는 것이다. candidate pool, slot owner, BUY/DROP threshold, provider, 주문가·수량·cap, broker 및 hard safety는 변경 대상이 아니다.

기존 조건 중 completed outcome 20건/5거래일, candidate/control 각 10건/3거래일, 독립 forward holdout은 실전 EV 승격에 필요한 최소 방어선으로 유지했다. 반면 source audit가 exact 불량행을 이미 제외하고 재검증까지 끝냈는데도 과거 제외행 수가 0이 아니라는 이유로 날짜 전체를 차단하던 조건과, locally 제외된 invalid lookup observation이 하나라도 있으면 rolling window 전체를 막던 조건은 과도하므로 제거했다.

## 구현

- source-quality audit의 `tuning_input_allowed=true`, hard gap 0, current/post-exclusion 0, applied=true, revalidation/deferred=false, manifest 존재 계약이 모두 맞으면 과거 제외행 수가 양수여도 유효행을 사용한다. 미적용·재검증 필요·deferred writer·hard gap은 계속 fail-closed다.
- valid observation을 candidate/control별 observation→full/partial/invalid/missing fill→COMPLETED로 분해한 funnel을 report에 추가했다. 고득점이 부족한지, 체결이 부족한지, 완료 lifecycle이 부족한지를 더 이상 하나의 `hold_sample`로 숨기지 않는다.
- 동일 scan generation에서 실제 promoted와 용량 때문에 pruned된 종목을 짝지어 lookup bonus 미적용/적용 top-set을 비교한다. 비교는 가격구간, priority tier, watch-budget owner, market-gainer 및 limit-down/low-rebound 예약 partition을 넘지 않으며 source-priority·등락률 tie-break도 재현한다.
- 자원배분 gate는 paired generation 20개, 5거래일, candidate/control 관측 각 10개, invalid row 0, counterfactual top-set 변경 1회 이상이다. 기존 경제성 floor와 같은 5거래일 안에서 수집되므로 별도의 장기 대기 허들이 아니다. 용량 경계가 없거나 보너스가 top-set을 바꾸지 않으면 각각 `not_observed`/`hold_no_effect`로 명시한다.
- 장후 source-quality가 일시 차단되어도 앞선 유효 `holdout_armed_since`가 연속 trading-day artifact에서 동일하면 캠페인을 보존한다. 차단일의 값 불일치·artifact gap·hash/contract 오류는 이어붙이지 않는다.
- 모든 신규 live artifact는 `scanner_lookup_attention_row_exclusion_v3` decision contract, report/policy hash, lineage/funnel/resource conservation을 함께 통과해야 한다. EV와 독립 holdout이 통과해도 resource gate가 미완료면 campaign은 유지하되 live 적용만 보류한다.
- 스캐너는 정책이 아직 비활성인 동안에도 동일 공식 0.60/200 후보식의 base/counterfactual score를 source-only로 기록한다. promoted terminal은 별도 real-source-guard 설정에 의존하지 않고 기록되므로 구조적으로 기다려도 표본이 생기지 않던 경로를 제거했다.

## 자동화와 권한 경계

기존 `postclose exact fact sync -> tuning report/policy write -> producer verify -> central verifier -> 다음 거래일 loader` 경로를 유지한다. 조건을 모두 달성하면 `live_auto_apply_ready`가 생성되고 별도의 사용자 승인 없이 최신 직전 거래일 hash-valid policy를 자동 로드한다. 적용 범위는 KRX 정규장·기존 동일 tier 정렬 보너스뿐이며, stale snapshot·NXT·다른 session은 0점 rollback이다.

이번 작업은 운영 report/policy 재생성, 현재 PID 코드 교체, bot 재기동 또는 주문을 수행하지 않았다. 따라서 코드 연결 완료를 실제 적용 또는 수익 개선으로 판정하지 않는다. 신규 자연 generation은 `ScannerLookupAttentionNaturalEvidence0908`에서 확인한다.

## 반복 코드리뷰 결과

1차 리뷰에서 resource gate가 미완료일 때 이미 모인 EV/holdout 캠페인까지 초기화하는 결함과 funnel invalid-fill/receipt 계수 혼합을 수정했다. 2차 리뷰에서 실제 주 경계 사유 `max_new_codes_reached` 누락, owner·예약 partition 및 tie-break 미재현, promoted event의 unrelated guard 의존을 수정했다. 3차 리뷰에서 malformed resource count가 verifier를 예외 종료시킬 수 있는 경로, lineage status 위조 가능성, counterfactual/runtime 공식 중복을 수정했다.

## 2026-09-04 원천 읽기 전용 재생성

운영 파일을 쓰지 않는 동일 producer 재생성 결과는 `status=hold_sample`, `source_quality=pass`, `blocked_dates=[]`, validator issue 0이었다. rolling 원천은 valid observation 1,238건, exact invalid observation 제외 130건이며, 기존 구현처럼 130건 때문에 날짜 전체가 `source_quality_blocked` 되지 않았다.

그러나 full-fill observation과 completed outcome은 각각 1건뿐이고 candidate/control observation은 43/1,195로 불균형하다. 신규 rank-time resource-pair 계측은 과거 PID 원천에 존재하지 않으므로 `resource_status=not_observed`, paired generation 0이며 `allowed_runtime_apply=false`가 맞다. 즉 과도한 source-quality 허들은 제거했지만 경제성·인과 근거를 낮추거나 과거 데이터로 합성해 승격하지 않았다.

동일 재생성의 측정 runtime은 81.17초, max RSS는 148,292KB였다. 장후 실행 자체는 유한하게 종료되며 현재 병목은 계산 무한대기가 아니라 실제 full-fill/COMPLETED 및 신규 generation-pair 자연 원천 부족이다. 신규 코드가 반영된 PID부터 pair가 생성되므로 향후 개선된 결과값은 **생성 가능**하지만, 현재 데이터로 양의 EV 또는 실제 수익 개선 가능성이 높다고 판정할 수는 없다.

## 최종 검증

- tuning·policy·scanner 단독 회귀: 187 PASS.
- wrapper·postclose verifier·runtime lookup 선택 회귀: 5 PASS.
- tuning·scanner·wrapper·postclose verifier 확대 통합 회귀: 489 PASS.
- 기존 2026-09-04 artifact `--verify-only`: PASS, issue 0.
- 신규 로직의 2026-09-04 읽기 전용 재생성 2회: 모두 `hold_sample`, issue 0. 두 번째 실행에서 상세 수치와 runtime을 대사했다.
- Python compile, 변경 파일 Ruff(기존 scanner bootstrap E402 제외), Black, 변경범위 `git diff --check`, checklist print-only parser: PASS.

최초 구현 검토 범위의 미해결 finding은 당시 0건이었다. 확대 회귀에서 보고된 runtime 테스트 19건은 테스트가 운영 symbol-owner 정책을 읽는 격리 결함이었다. 전체 병합·재기동 후 검증에서 해당 module의 실패를 재현하고, 기존 manual-exclusion fixture에 임시 owner-policy 경로만 지정했다. resolver와 fail-closed guard를 mock하거나 운영 정책을 변경하지 않았다. 해당 runtime module와 scheduler·owner-policy·watch-budget 회귀는 480 PASS로 종결됐다. 기동 및 최종 통합 검증의 현재 증거는 [전체 병합·재기동 기록](2026-09-07-full-workspace-merge-restart.md)이 소유한다. 이 범위 종결은 전체 시스템 무결함이나 미래 수익을 보증하는 판정이 아니다.

## 목적·자동화·조건 달성 가능성 재점검

점검 시각: 2026-09-07 13:19 KST. 재점검 요청에 따라 코드·cron·기존 산출물·당일 관련 event를 읽고 메모리 반례를 실행했다. 기존 tuning/scanner 회귀 **187 PASS**였지만, 다음 결함/설계 공백은 기존 회귀에 포함되지 않았다. 당시 판정은 **5건 OPEN, 추가 보완 필요**였으며 아래 후속 구현으로 대체한다.

### 목적과 실제 구현 범위

목표는 제한된 scanner 감시자원을 유망 후보에 먼저 배분하여 비용 차감 EV·순이익을 개선하는 것이다. 현재 기능은 고정 관심도 공식 `0.50*rank_level + 0.35*positive_rank_change + 0.15*new_top20`과 `score>0.60`, 최대 200점 보너스의 ON/OFF 검증이다. 최적 cutoff/가중치를 탐색하는 optimizer는 없다. 조회순위 상승은 주가의 상승·반등과 같지 않으며, 실제 진입 자격은 기존 scanner/entry가 소유한다.

### 추가 finding과 보완 순서

| ID·우선순위 | 코드 근거와 확인된 문제 | 기대효과/달성 가능성에 미치는 영향 | 권장 보완·수용 검증 |
| --- | --- | --- | --- |
| R1·높음 | `scalping_scanner.py:2119`의 resource eligibility는 fresh 조회순위 보유 종목에만 true다. `scanner_lookup_attention_tuning.py:412`는 나머지 경쟁 종목을 버린다. 또 `scalping_scanner.py:5159` 부근의 capacity 판정은 뒤의 후보 pre-filter보다 먼저 실행되며, resource pair는 capacity-pruned의 잔여 자격 통과 여부를 요구하지 않는다. | 조회순위 없는 기존 1위가 조회순위 있는 후보에게 밀리는 정상 효과를 놓칠 수 있다. 반대로 실제 자격 미통과 후보를 승격될 것으로 계산할 수 있다. | 동일 generation의 실제 경쟁 집합 전체를 기록한다. 조회순위 비대상은 명시적인 zero-bonus control, 손상/결측 source는 별도 제외로 구분한다. 실제 선택기를 재사용해 owner/예약/용량/기존 자격을 재현하고 무보너스 baseline이 실제 terminal과 일치해야 pair를 인정한다. 비조회순위 1위 교체와 capacity-pruned 자격탈락 반례를 필수 검증한다. |
| R2·높음 | `_cohort_book`(`tuning.py:1387`)의 고득점/저득점 COMPLETED EV와 `_resource_allocation_pair_book`(`:1496`)의 순위 변경 계수는 별개다. 변경된 종목의 수익/기회비용은 `decide_promotion` 입력에 연결되지 않는다. | 전체 고득점군 성과가 좋아도 실제 교체되는 종목의 증분 EV가 나쁠 수 있다. 현재 조건 통과가 자원배분 순이익 개선을 뜻하지 않는다. | 교체된 moved-in/out identity와 동일 시점의 검증 가능한 후행 성과를 결합해 증분 EV를 평가한다. 관측 불가능한 미선택 종목 성과는 미관측으로 남긴다. 기존 실제 full-fill EV·독립 검증은 유지하고, counterfactual을 실제 체결 품질로 승격하지 않는다. 전체군 양수/교체 pair 음수에서 적용 보류, 동일 pair 양수와 원천 완결 시 후보 생성되는 수용 검증을 추가한다. |
| R3·높음 | `collect_lineage`(`tuning.py:353`)는 최근 90일만 읽고 `_base_rows_for_prior`(`:1678`)는 그 안의 arm 이전 행만 남긴다. `decide_promotion`(`:1778`)은 base floor 미달 때 arm 날짜를 null로 만든다. | 기초 표본이 실제로 영구 고정되지 않는다. 충분한 미래 holdout이 있어도 시간이 지나면 표본이 사라져 재검증이 초기화되며, 적용 후에도 같은 이유로 비활성화될 수 있다. | arm 시점 base의 identity/내용 hash/비용·원천 계약을 immutable manifest로 보존한다. 현재 rolling/R6 악화 판정은 따로 유지한다. 90일 경과·단일 생산 누락 후에도 유효한 캠페인 근거를 복원하고, hash 위반은 차단하는 검증이 필요하다. |
| R4·중간 | 자원배분에 독립적인 `20 generation/5거래일/각 군10` floor를 다시 요구하며, `invalid_row_count=1`이면 유효 pair가 충분해도 전체 rolling resource가 `contract_invalid`다(`tuning.py:1581`). pair가 없으면 원천이 계속 있어도 `hold_sample`로 남는다. | 특정 날짜에만 용량 경쟁이 생기면 경제성 표본과 별도로 대기가 늘어난다. 정확히 격리 가능한 결손 1건도 전체를 막는 과도한 허들이 남았다. | R1/R2의 완전한 경쟁·증분 EV 계약을 먼저 구현한 뒤, 자원배분의 별도 20/5/10 계수는 진단으로 전환하는 방안을 권장한다. 결손은 관련 generation/partition만 제외하고 커버리지를 명시한다. 전체 원천을 복원할 수 없는 경우만 전체 block을 유지한다. 무용량·무효과·표본부족 상태와 유지 재검토 기한을 분리한다. |
| R5·중간 | scanner가 매 정렬 시 `load_active_policy(today)`를 부르고 loader는 이전 거래일 파일의 mtime/size 변경 시 재로딩한다(`scanner_lookup_attention_policy.py:525`). 장전 hash 고정 receipt를 요구하지 않는다. | 다음 거래일 자동 소비는 연결되어 있지만 장전 확정 정책만 하루 동안 유지한다는 보장은 없다. 장중 전일 artifact 재생성으로 같은 날 bonus가 바뀔 수 있다. | PREOPEN에 exact target-date policy hash와 선택 결과를 고정하고 runtime은 그 receipt만 읽게 한다. 검증된 후보는 별도 사용자 승인 없이 자동 선택한다. 장중 전일 artifact 교체 시 활성값 불변, 다음 PREOPEN부터 새 hash 소비를 검증한다. |

`tuning.py`는 `src/engine/monitoring/scanner_lookup_attention_tuning.py`를 뜻한다. R1/R2는 분석·승격 근거의 결함이며, 실행 중 broker/hard-safety guard가 제거됐다는 뜻은 아니다.

### 반례 실행 결과

- base 20건의 arm 날짜를 `2026-09-08`로 두고, 양수 EV의 독립 미래 20건을 추가한 뒤 `2026-12-14` 기준 동일 90일 창을 적용했다. window start=`2026-09-16`, retained base=0, 미래 book pass=true인데도 `status=hold_sample`, `holdout_armed_since=null`이었다. R3는 시간 경과만으로 해소되지 않는 재현된 결함이다.
- 유효 20 generation/5일 pair에서 격리된 invalid row 1건을 전달하면 pair20이 남아도 `contract_invalid`였다.
- capacity terminal에 별도의 자격탈락 진단을 넣어도 resource selector는 이를 읽지 않아 `ready`, moved-in20이었다. 이는 실제 pre-filter 재현 계약이 없다는 반례이며 운영에서 그 후보가 매수됐다는 증거는 아니다.
- 메모리상 전체 candidate/control EV를 +0.50%/+0.10%로 두고 순위 교체 pair의 가정 순수익을 -1%/+1%로 두어도 `live_auto_apply_ready`였다. 현재 interface에는 pair 손익이 들어가지 않는다. 이 수치는 설계 반례이며 실제 시장 손익이 아니다.

### 자동화와 실제 성과·달성 상태

운영 cron의 20:10 장후 wrapper는 exact fact sync → producer `--write` → producer verifier를 실행하며 central verifier도 필수 산출물로 검사한다. runtime은 직전 KRX 거래일의 유효한 live policy를 자동 로드한다. 별도 사용자 승인이나 신규 operator lock은 요구하지 않는다. 다만 R5의 PREOPEN 고정 계약은 미구현이다.

9/4 저장 산출물은 `source_quality_blocked`이고, 이전 작업의 읽기 전용 v3 재생성만 `source_quality=pass, hold_sample`이었다. 이번에는 운영 artifact를 덮어쓰지 않았다. 9/7 현재 loader는 실제 9/4 저장 policy를 읽어 `active=false`, `allowed_runtime_apply=false`다.

| 근거 구간 | 관측·성과 | 해석 |
| --- | --- | --- |
| 9/2~9/4 기존·읽기 전용 재생성 근거 | valid attach1,238, candidate/control43/1,195; full-fill/COMPLETED1; completed candidate0/control1; 유일한 control 순EV +0.29243455% | 관심도 고득점 후보의 실제 EV는 아직 계산 불가다. control 한 건의 양수 수익을 보너스 성과로 해석하지 않는다. |
| 9/7 장중 관련 stage만 읽은 부분 census | valid attach153, full-fill0; 신규 resource row36, invalid0; 유효 paired generation1/1일, paired candidate0/control5, reorder0 | 신규 PID에서 계측 생성은 확인됐다. 부분 장중 자료이며 전체 source-quality 감사나 당일 장후 성과를 대체하지 않는다. |
| 자동 적용 최소 경제성 조건 | base와 독립 holdout 각각 COMPLETED20/5일, 군별10/3일; 양수 candidate EV, uplift>=0.10%p, tail/worst guard | 적어도 서로 겹치지 않는 총40건/10거래일이 필요하다. 현재 candidate 완료0이므로 달성시점이나 개선 확률을 제시할 근거가 없다. |

따라서 **신규 자료 생성 가능성은 확인됐지만, 현 구조를 유지한 채 수익 개선 후보가 나올 가능성이 높다고 판정할 수 없다**. 경제성 floor 자체를 무조건 낮추기보다 R1/R2의 목적에 맞는 평가와 R3의 표본 보존을 우선 수리해야 한다. 정해진 기간 동안 유효한 한계 경쟁 pair가 없으면 유지 의사결정을 다시 열어야 하며, 무신호를 자동 승인 근거로 쓰지 않는다.

### 유지·보완·제거 권장안

1. 조회순위 raw 수집과 기존 scanner 진입·체결 원천은 유지한다. 신규 PID에서 source 생성이 확인됐으므로 기능 전체를 지금 폐기할 근거는 부족하다.
2. 구현 순서는 R1 경쟁 집합/실제 선택기 재현 → R2 변경 pair 증분 EV → R3 immutable base/캠페인 복원 → R4 중복 floor·격리 가능한 전체차단 제거 → R5 PREOPEN 고정 receipt다. R3/R5도 자동 적용 후보 발행 전에 종결해야 한다.
3. 경제성·신선도·exact identity와 독립 검증은 유지한다. 자원배분 별도 계수는 R1/R2를 대체하는 독립 승격 허들로 두지 않는 방안을 권장한다.
4. 자연 증거 재검토에서 source coverage가 충분한데도 순위 교체가 없으면 무효과 정렬 보너스·독립 장후 평가를 기존 scanner 진단으로 통합하는 정리안을 검토한다. source 결손이면 생산 경로를 먼저 수리하고, 증분 EV가 음수이면 후보를 거절한다. 이번 리뷰는 실제 삭제/조건 변경을 실행하지 않았다.

당시 문서 정정은 `korstockscan-review-gate`로 재리뷰했고 print-only parser와 diff 검증이 PASS했다. 그 시점의 코드 finding 5건은 구현 대기였으며 다음 후속 구현으로 종결한다. 자연 후속 owner는 `ScannerLookupAttentionNaturalEvidence0908`이다.

## R1~R5 보완 구현과 최종 재리뷰

사용자 지시에 따라 R1→R2→R3→R4→R5 순서로 구현하고 `korstockscan-review-gate`의 producer/consumer·권한·실패 경로 리뷰를 반복했다. 신규 순수 계산 모듈은 `src/engine/scalping/scanner_lookup_attention_resource.py`로 두었다. engine root에 새 구현을 추가하지 않았으며, `kiwoom_sniper_v2.py` 수정은 내부 scanner provenance 전달 4줄뿐이다. API 요청/응답·FID·계좌/주문 프로토콜은 변경하지 않았다.

| 항목 | 구현·반례 검증 결과 | 권한/해석 경계 |
| --- | --- | --- |
| R1 경쟁 집합/자격 | 비조회순위 후보를 명시적 zero-bonus control로 포함. 같은 가격구간/tier/watch owner/예약 partition의 전체 count/code hash, 기존 scanner 자격 및 actual score top-K를 재현. 자격탈락·경쟁군 누락·실제 선택 불일치·stateful replacement/probe/upgrade는 해당 증거 제외 | capacity-pruned를 자동으로 매수 가능 종목으로 간주하지 않는다. 추가 read-only 검사 실패는 source-only 부적격이며 기존 실전 guard는 원래 위치에서 다시 수행 |
| R2 목적에 맞는 경제성 | 보너스로 들어오는/밀려나는 종목의 동일 미래 generation, 180~360초 관측 가격과 고정 비용으로 순수익·증분 수익을 계산. 전체군 EV가 좋아도 marginal 수익이 음수면 승격 안 됨 | scanner snapshot은 실행가능 quote/체결가가 아니다. source-only 기회비용 proxy이며 실제 full-fill COMPLETED base·독립 holdout을 대체하지 않음 |
| R3 base 영구 보존 | arm 당시 결과 identity/book/hash/비용·full-fill·decision 계약을 manifest에 결속. rolling90일 경과·생산일 누락·일시 SQ 차단에도 유효 캠페인 복원. hash/계약 위반·최신 명시적 음수 정책은 건너뛰지 않음 | 현행 source-quality와 rolling/R6 악화/rollback은 유지. 오래된 base를 근거로 현재 성과 검증을 생략하지 않음 |
| R4 중복 허들·전체차단 제거 | 별도 resource20 generation/5일/군별10은 진단으로 전환. 완결되고 label이 관측된 비중복 marginal pair3/2일에서 incoming 및 증분 순수익 모두 양수 필요. 불량 partition은 국소 격리 | 실제 경제성 base·독립 holdout은 각각20건/5일, 군별10/3일, EV uplift>=0.10%p와 tail/worst guard 유지. 증거 없는 자동 BUY는 없음 |
| R5 장전 자동 고정 | 다음 거래일09:00 전 PREOPEN 한 번만 선택. report/policy 원본과 hash를 exact-date receipt에 포함. runtime은 receipt만 읽고 장중 원본 교체·캐시 초기화·재기동에도 같은 값. scanner→payload→runtime attach→장후에 receipt hash 전달 | 2026-09-08 이후 wrapper의 AUTO_APPLY + auto_bounded_live에서 자동 실행. 별도 사용자 승인/신규 lock 없음. 당일 최초 장중 발행 금지, 기존 receipt 손상/발행 실패는 PREOPEN FAIL. 없음·비활성은0점 |

최종 적용 계약은 `scanner_lookup_attention_marginal_preopen_v4`, 자원배분은 `scanner_lookup_attention_resource_pair_v2`, activation mode는 `preopen_frozen_exact_date_policy_auto_loaded`다. 과거 비활성 v3 보고서는 역사 검증 가능하지만 v3로 신규 live 권한을 만들지 않는다.

### 추가 리뷰에서 수정한 결함

- PREOPEN hash가 scanner event에만 있고 runtime payload/attach에 빠지는 누락을 수정하고 두 경계를 각각 회귀로 고정했다.
- source-only 사전 검사 예외가 live promotion을 중단하거나 DB 조회 실패를 정상 자격으로 포장하지 않도록 분리했다. 보너스 가능성이 없는 partition은 추가 자격 DB 검사를 생략한다.
- 잘못된 날짜·timezone·embedded payload, non-object JSON, 재해시한 허위 resource 통계, 동일 pair의 겹치는 시간 구간·서로 다른 미래 generation을 거부한다.
- 생성물 검증 전에 운영 파일을 쓰던 순서를 `build → validate → write`로 바꿨다. PREOPEN receipt는 exclusive atomic 발행으로 동일일 덮어쓰기를 막는다.
- 장기 자원배분 raw를 계속 복제하지 않도록 최근20 KRX 거래일·시간순 첫32 비중복 pair/일로 source-only 평가를 한정했다. 선택은 미래 수익을 보기 전이며 1,024행을 넘는 일별 원천은 전체 경쟁 partition과 실제 선택된 label 증거로 압축한다. raw/retained/invalid는 분리한다. 압축 전후 경제성 일치 및 뒤쪽 큰 수익으로 앞쪽 음수 표본을 치환하지 않는 반례를 검증했다. 이 bounded 표본을 전체 시장 EV로 외삽하지 않는다.

### 목적·자동화 검증과 실제 자료

실제 경제성 입력을 가정한 통합시험에서 producer가 v4 report/policy를 만들고 verifier를 통과한 후, 다음 장전 receipt가 추가 승인 없이 발행되어 score0.9에 150점 bounded bonus를 반환했다. 같은 base/holdout EV에 marginal 수익만 음수로 바꾸면 `forward_holdout_armed`와 0점이 유지됐다. 이는 코드의 조건 달성 가능성 검증이며 실제 시장 수익률이 아니다.

9/4 원천의 v4 읽기 전용 재계산은 **source-quality PASS, hold_sample, 검증 issue0, runtime apply=false**였다. 관측1,238(candidate43/control1,195), 실제 full-fill/COMPLETED1(candidate0/control1), 유일한 control 순EV +0.29243455%다. resource v2 증거가 과거에 없으므로 pair0/`not_observed`가 맞으며 새 증거를 합성하지 않았다. 운영 산출물은 덮어쓰지 않았다.

재계산 wall time은 **81.38초**, max RSS **148,272KB**였다. 이전81.17초와 사실상 같은 수준이며 현 데이터로 실행시간 개선을 주장하지 않는다. 새 원천의 장기 누적 부하 제한은 합성 압축시험으로만 확인했다.

### 검증 판정 및 남은 자연 확인

- 최종 lookup tuning/resource/scanner/runtime/source-quality 회귀 **729 PASS**, 관련 PREOPEN/postclose wrapper·central verifier 선택 회귀 **8 PASS**로 총 **737 PASS**다. 기존 pandas-ta deprecation warning1건은 기능 실패가 아니다.
- 마지막 확대 회귀는 7개 module **1,036 PASS / FAIL0**다(20.44초). 앞선 실행에서는 병행 Main AI wrapper5건/AI calibration verifier1건이 실패했지만 해당 병행 변경과 테스트 보완이 반영된 후 같은 확대 회귀를 다시 통과했다. `deploy/run_threshold_cycle_postclose.sh` 및 Main AI 보정 소스의 병행 수정은 이 작업의 구현 실적으로 포함하지 않는다. 검증한 module 범위의 PASS를 전체 workspace 무결함·수익 보장으로 확대하지 않는다.
- 구9/4 저장 artifact verifier(issue0), Python compile, shell syntax, Ruff(기존 scanner bootstrap E402 제외), 선택 파일 Black, `git diff --check` PASS. Checklist print-only parser PASS(OPEN46개, lookup 구현 owner 완료/자연 owner OPEN 정상 인식). Project/Calendar sync는 실행하지 않았다.

예상한 개선 후보를 평가하고 자동 적용할 경로는 연결됐지만, 현재 candidate 완료0이므로 양의 EV 후보가 나올 확률이나 달성일은 추정할 수 없다. 고정0.60/200점 공식의 ON/OFF 검증이지 cutoff/계수 전역 optimizer 구현은 아니다. 매수 여부는 기존 상승·반등 확인/entry guard가 계속 소유하며 조회순위 상승만으로 BUY하지 않는다.

다음은 정상 배포된 새 PID의 v2 원천 → 장후 v4 판정 → 다음 장전 immutable receipt → 실제 runtime hash/R6 확인이다. 20관찰일 동안 유효 교체가 없으면 독립 보너스·장후 평가를 기존 scanner 진단에 통합할지 재검토한다. 이 자연 확인은 checklist `ScannerLookupAttentionNaturalEvidence0908`에 OPEN으로 남겼다. 현재 PID 교체, 운영 보고서/정책 발행, 주문, commit/push는 이번 작업에서 수행하지 않았다.
