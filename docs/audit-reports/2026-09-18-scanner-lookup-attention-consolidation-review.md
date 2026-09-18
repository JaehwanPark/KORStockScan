# 조회 관심도 scanner 평가 통합 구현·재리뷰 — 2026-09-18

독립 heavy 장후 평가/발행은 폐기하고 기존 scanner monitor→Daily/EV/summary/strict→단일 execution policy의 연결을 구현했다.9/21 준비 정책은 가중치0/source_quality_blocked다. **Positive same-budget EV/자동 active promotion과 실제 경제성은 미완료**다. 현행 existing CF owner가 exact fill/exit/cost replay missing을 선언하고 미선택 original recipe/요청량/실제 guard·full capital path가 없으므로 primary EV/순익을 null/source_gap으로 남긴다. 기존 source가 제공하지 않는 값을 합성하거나 새 체결 시뮬레이터를 추가하지 않았다.

## 변경·리뷰·보완

- 기존 native incremental ledger에 decoder가 사용하는 관측/selection/receipt 필드만 보존한다. 최종 source/recipe/cost/fact revision/holdout identity fingerprint가 같은 경우 bounded 평가를 재사용한다. 장중 publisher/rolling90일 raw scan/새 service·timer·module은 없다.
- 기존 finalize boundary가 전체 compiler를 호출하며 standalone CLI/publisher는 retired/fail closed다. 과거 pure math/decoding/library helpers는 archive contract tests 및 integrated math의 기존 caller 때문에 보존한다; historical ready pair는 현행 loader/PREOPEN에서 active authority를 얻지 못한다.
- 기존 보고서 lookup section에만 generated_at/postclose phase를 주어 후속 갱신했다. 부모 monitor의9/17 19:45 intraday/as-of와 다른 분석을 장후 완료로 바꾸지 않았다. 현재 회계/비용/실제 거래 분모와 frozen 역사 분모는 분리한다. 기존110MB state/5.7GB raw를 다시 읽지 않았다.
- Review에서 현행 숫자 전용 official master validator가 uppercase alphanumeric56개 때문에 master 전체를 차단하는 것을 확인했다. 해당 metadata identity 검증만 보완하고 official content/upstream hash·schema/census/effective date를 그대로 검증해 기존5 completed를 복구했다. API/FID/parser/protocol·stock universe/주문/guard 변경은 없다.
- 삭제 전 후속 re-review에서 production decoder/prior campaign의 retired report 참조를 확인해 제거했다. 기존 exact immutable PREOPEN receipt로만 자연 bonus 기대값을 해석하고 receipt가 없으면 runtime과 동일한 bonus0으로 판정한다. Archive 검증용 decoder/math만 역사 계약을 유지하며 별도 test로 production의 old-path 조회0을 검증한다. 첫 배포를 편집하지 않는 후속 immutable release로 수리한다.
- Date/hash/cache·source gap vs no-edge·positive proxy의 실행 EV 오인·legacy ready 재유입·immutable target-day<09:00 PREOPEN·same-budget scope·미확보 비용 null·mirror conflict·완료 revision·선행/후행 소비를 재검증했다. Provider/threshold/quantity/cap/custody/scale-in 소유권을 보존했다.

## 9/17 결과 갱신과9/21 준비

Frozen original report의 valid6,277/invalid209·12날짜·candidate298/control5,979·full6/partial9·completed5·cohort 평균 차이+0.02975044%p를 compact preservation receipt에 유지한다. 이 전체 과거 분모를 migration 후 natural ledger의 새 표본으로 세지 않는다. Exact original observation→current COMPLETED fact를 재결속한5건은 fixed fee/tax comparison net575.12765원, 거래금액238,891원, equal weight EV+0.26099759%, notional EV+0.24074898%, worst−1.09067925%다. 가중치 미적용의 observational 이익이며 신규 적용 이익이나 causal uplift가 아니다.

교체 proxy3개/3날짜 Δ−2.38954987%p는 supporting no-edge다. 독립 executable primary와 portfolio budget EV/순익/tail/exposure/model error는 null/source_gap이다. Holdout은 not armed이며 과거 평가 날짜를 fresh holdout으로 재사용하지 않는다. Actual applied version은 not_applicable_before_live_apply/null이다.

`scanner_lookup_attention_policy_2026-09-18.json`의 publication9/18/source_evaluation9/17/prepared_effective9/21/bonus0/allowed_runtime_apply=false를 검증했다. 다음 장전 loader는 정상 inactive `prior_policy_not_live_auto_apply_ready`로 소비한다. 실제9/21 PREOPEN immutable receipt/PID/자연 선택/실제 완료 EV는 아직 확인되지 않았다. 전체 장후 개선 완료 뒤 정상 target window에서 준비하며 현재 integrated-entry strict blocker는 이 단위의 zero policy로 해소됐다고 주장하지 않는다.

## 검증·배포·정리 증거

`tmp/scanner-attention-consolidation-20260918/validation.json`, `scope-verifier.json`, `consumer-refresh.json`, `result-refresh.json`, `deployment.json`, `deleted-products.json`, `preservation.json`를 따른다. 관련 pytest·compile·bash syntax·diff·print-only parser와 source/date/hash 소비만 검증한다. 전체 trading/provider/order suites·90일 raw 재스캔·full postclose chain·봇/worker restart·수동 env/lock/calendar 변경·외부 sync는 수행하지 않는다.

현재 native9/17 chain의 기존 resource guard 중단과 전체 DONE/PREOPEN/Main/실제 EV는 별도다. Scope strict PASS/소스 선택은 자연/PID/positive EV acceptance가 아니다. Deployment는 실행 중 source를 수정하지 않는 clean managed release와 selector CAS를 사용하며 미래 default monitor 호출도 기존 router로 selected source를 읽는다. 다른 세션 scale-in source/정책/수량은 보존한다. 과거 standalone JSON/MD는 active input/reference/SHA를 확인하고 compact 원분모·gates·cost·outcomes/resource proof/provenance를 보존한 뒤에만 삭제한다; 원천/ledger/state/lock/fact/policy/PREOPEN/current/rollback/holdout는 삭제하지 않는다.

## 다음 조치·closure

Executable owner는 당일 `ScannerLookupAttentionConsolidation0918` 하나이며 자연/경제성은 OPEN이다. 구조결손 owner는 existing `sniper_missed_entry_counterfactual`의 exact fill/exit/cost/quantity/capital replay 계약이다. Native original requested quantity/recipe/actual guards·ordered executable depth/exit/cost·full frozen capital을 양측 선택에 재현한 same-budget portfolio 결과와 독립 forward holdout이 있어야 positive activation evaluator/publisher/PREOPEN 계약을 보완할 수 있다. 현재 validation은 unsupported ready를 거부한다. 데이터 누적을 ETA로 제시하지 않으며 ETA=null이다.


검증은 최초 관련 전체617 PASS 및 마지막 source 참조 수리 후 affected decoder/resource74 PASS다. Python compile/bash/diff/print-only parser·원분모 보존·actual fact 재결속·Daily/EV/summary/strict의 동일 section SHA 및9/21 inactive loader를 확인했다. Source commit과 최종 선택 release는 `deployment-final.json`을 따른다. 삭제 예정28개 standalone JSON/MD/reuse receipt는 source/reference/SHA와 compact preservation을 검사하고 `deleted-products.json`의 실제 unlink 결과만 최종 삭제 증거로 인정한다.


최종 bounded export 보완: 원분모 기준 일별 resource 관측은 최대58,532행이다. 현재 일자는 existing incremental state에서 수집하지만 historical report에는 이미 평가가 선택한 complete partition/후행 label proof와 exact entry/fill/conversion receipt만 내보내고 raw census는 lineage·원본에 보존한다. Report/state의 중복 저장을 무심코 history giant-state 조회로 확대하지 않는다. 기존 sampling/전체 live universe/partition/quantity/guard는 동일하며 snapshot economics 보존·필요 receipt 보존·축약 export를 기존 test에서 검증했다. 최종 관련 decoder/resource75 PASS·compile/diff와 문서 print-only parser를 완료했다. 최종 source/PREOPEN/consumer SHA와 실제삭제28개·26,377,207bytes는 owning receipts를 따른다.
