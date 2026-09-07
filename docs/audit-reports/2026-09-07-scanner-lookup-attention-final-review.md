# Scanner lookup-attention tuning 최종 구현·리뷰

기준일: 2026-09-07 KST
범위: 장후 #49 `Scanner lookup-attention tuning`

## 판정

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

최종 검증 수치는 이 문서의 마지막 갱신 시점 결과를 사용한다. 검토 범위의 미해결 finding은 0건이며, 전체 시스템 무결함이나 미래 수익을 보증하는 판정은 아니다.
