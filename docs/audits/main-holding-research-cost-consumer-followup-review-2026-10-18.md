# Main 보유 연구 배분비용 소비 후속 검토 — 2026-10-18

현재 상태: **별도 holding 연구 비용 consumer 구현·독립 재리뷰·실제 완료13건 비용 대사 종결. 배분비용 provenance5건, 경제 비교 적격0건.** 원13 actual·13 alternative·482 CF, 기존 초기정책과 손익 결손을 보존했다. 새 비용 원천의 소비 구현 결손을 닫았으며 전체 보유 전략의 개선 성과나 운영 적용을 증명한 것은 아니다.

## 1. 범위와 코드 동결

[이전 보유 연구 실행](main-holding-exit-research-execution-review-2026-10-18.md)의 `initial_quantity_research_only` 배분비용8건은 holding actual 손익으로 소비할 수 없었다. 이번에는 원 공식 비용·배분 영수증·완료 projection을 독립 검증하는 `main_holding_exit_research_only` adapter를 추가했다. 원 연구 scope와 영수증·가용시각·수량·원가·BUY/SELL identity를 보존하고 holding 진단에만 연결한다.

- 격리 worktree: `/home/ubuntu/KORStockScan-worktrees/holding-exit-research-20261018`.
- base `1bf35e6c258cdcda373c813432b52725898f22ab` → commit `d81a80778a79476400c4ef4d842e6aa92a887575`, 10파일, commit 직후 clean.
- 새 코드 계약 SHA `5837075be3c7d4c7bbe2317192fe62eff71ba39c87cb828534eebc19e5ce5338`.
- [코드 종결 영수증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/code-review-closure.json)에 정확10파일 세대·검증·보완·실행 결과를 결속했다. stop worktree나 운영 선택본에 overlay하지 않았다.

새 파일은 기존 완료/비용 검증의 역할을 소유하는 `src/engine/lifecycle/holding_research_cost.py`에 배치했다. engine root에 새 모듈을 만들지 않았다. public assembler는 native completed source 검증 이후 adapter를 호출하고, source manifest와 분할 replay/handoff 검증은 명시된 cost root의 실제 의존 파일만 허용한다.

## 2. 생산자 → 소비자 계약

| 경계 | 구현·검증 | 보존한 한계 |
| --- | --- | --- |
| 공식 비용 → 배분 receipt | 기존 `broker_cost_allocation` validator와 공식 raw source를 대사한다. 계정·일자·관측시각·종목·매수/매도 turnover·총비용·배분량을 검증한다. current index가 가리키는 immutable generation을 사용한다. | 상태 문자열·digest만으로 승인하지 않는다. 미확인 단가/체결별 수수료를 만들지 않는다. |
| native 완료 → 비용 | 원 완료 producer 증명, BUY/SELL leg 보존·수량·금액·residual0·terminal 권한, 현재 원 BUY registry custody를 독립 대사한다. | BUY custody는 seller의 Main 권한이나 전체 보유 자동관리 증명이 아니다. duplicate terminal·미완료 잔량·매도 뒤 추가매수는 미지원/결손으로 남긴다. |
| 비용 신규 도착 | 같은 원 완료/체결에 후행 검증 비용을 별도 overlay한다. 실제 cost availability를 보존한다. 원 완료 snapshot을 reseal하지 않는다. | 과거 cutoff 뒤 비용을 이미 알고 있었던 것으로 사용하지 않는다. 원 비용·정책·AI·입력 원문을 수정하지 않는다. |
| holding 연구 진단 | 기존 paired modeled parent/candidate가 이미 적격인 경우에만 `candidate modeled - max(parent modeled, allocated historical net)`을 별도 진단한다. 배분 자료의 원 scope·알고리즘·source receipt를 출력한다. | 기존 selector의 `candidate - max(parent modeled, actual realized)`는 그대로다. `actual_pnl_krw=null`, `actual_execution_cost=false`, `selector_eligible=false`, `allowed_runtime_apply=false`를 유지한다. |
| 외부 cost root | 이번 명시적 root는 보존된 quantity 연구의 `repaired-temp-data`다. 의존 index/immutable receipt/공식 source만 manifest에 결속한다. | 임의 외부 경로 허용, canonical 비용 파일 변경, patched custody의 자동 신뢰를 하지 않는다. 원 live registry와 native source를 다시 검증한다. |

정확한 체결별 실비·포지션 총 실비와 이 배분 연구비용은 다른 등급이다. 배분비용의 검증 성공이 원 source gap·수동 이관·자동관리 미증명을 해소하지 않는다.

## 3. 자원 상한과 독립 리뷰 보완

첫 독립 리뷰에서 신규 전체 비용행을 resident list로 누적하던 문제와 매 record마다 같은 registry/공식 원천을 재해시하던 문제를 확인해 수리했다.

- 전체 비용행은 기존 managed SQLite index와 bounded evidence tree로 저장한다. 보고서는 `holding_allocated_cost_rows_ref`·census·작은 비교 집계만 유지한다. 출력 상한을 넘는 행을 조용히 삭제하지 않는다.
- 공식 source/receipt는 4slot LRU와 shared Claim으로 admission·eviction한다. 동일 batch의 exact stat(inode/ctime 포함)이 유지되면 해시와 공식 semantic 검증 결과를 재사용하고 assembler 종료 시 source generation을 다시 대사한다. receipt/공식 source/registry의 개별 파일 상한과 aggregate shared64MiB 예산을 별도로 적용한다.
- 변경·실패 경로의 Claim 반환, close 후 cache/registry 참조 해제, FIFO와 symlink/ancestor symlink, 동일 크기·mtime의 inode 교체를 검증했다. 거부된 원천을 cache reuse로 승인하지 않는다.
- 20회 같은 record 시험에서 최초4개 byte-generation 읽기만 수행했다. 이는 동일 batch의 중복 해시 제거 검증이며 실제 Main 전체 성능 PASS가 아니다.

7파일 표적 회귀 **295 PASS/55.16초** 이후 마지막 ancestor guard를 보완하고 adapter·diagnostics **36 PASS/6.40초**를 통과했다. 독립 재리뷰는 지적0이며, 독립 adapter·diagnostics34 PASS/7.00초와 마지막 ancestor/cache3 PASS/0.81초를 확인했다. 이 시험은 중복되므로 합산하지 않는다. 변경10파일 compile, 관련 모듈 Ruff(E9/F821/F822), diff check도 통과했다.

## 4. 실제13건 후속 대사

[attempt-02 보고서](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/attempt-02/report.json)와 [결과 재검증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/attempt-02/result-validation.json)는 원 v3 cutoff `1792284633.131831`을 유지한다. 해당 완료일4개의 현재 native completed projection과 원 producer/custody dependency를 재검증하고 기존 immutable allocation/공식 raw를 대사했다.

| 비용 검증 결과 | ID | 건수 |
| --- | --- | ---: |
| `research_cost_allocated` | 49351, 49347, 49345, 49343, 49340 | 5 |
| `holding_research_cost_index_missing` | 48376, 49013, 49268, 49293 | 4 |
| `holding_research_cost_terminal_unverified` | 49267, 49294, 49300, 49328 | 4 |

검증된5건의 배분비용은 각각568/565/121/1326/590원, 배분비용을 적용한 과거 net 진단은932/435/-121/174/1410원이다. **실제 체결별 순손익·정책 성과·경제 적격5건이라는 뜻이 아니다.** 특히49345는 비용 provenance만 확인한 진단이며 자동청산 적격으로 편입하지 않는다. stop 연구의 seller/custody 적격 분모와 이 비용 출처 분모를 합치지 않는다.

원 projected `automatic_management_allowed=false`13건을 그대로 보존했다. native flat 원필드는 false11건/null2건(48376·49013)으로 각각 유지했으며 null을 원본의 false로 고치지 않았다. 모든 actual의 native custody early guard는 계속 `position_identity_or_custody_unverified`다. 원19개 candidate별13건, **247개 actual outcome의 `actual_pnl_krw`/`modeled_net_pnl_krw` 결손**을 그대로 확인했다. 경제 paired 적격은0이다.

이번 작업은 원 v3 재생 결과를 재사용하고, 현재 완료 원천·비용을 검증한 후 기존 custody 첫 guard를 다시 실행한 **비용 전용 후속**이다. 전체 연속 quote 경로·12GB 원천의 fresh replay 또는 전체 현재 재해시를 실행했다고 표현하지 않는다. 결과 검증은 원 manifest/report 및 실제 사용 비용·custody 의존19파일의 세대 일치를 별도로 확인했다. 원 모집단 **13 actual + 13 alternative + 482 CF = 508**과 기존 초기정책 SHA `421f7bb9e59080452d7221c8032f95d101cccb0a6ef3e8b2e40806fb526210d7`를 native policy validator 및 원 보고서와 대사했다.

실제 비용 전용 실행은 wall **23.721초**, CPU22.634초, peak RSS168,692KiB이며 shared Claim 종료 used0/limit67,108,864B다. 이 수치를 원 full replay 성능 또는 full Main 부하 측정과 직접 비교하지 않는다.

[attempt-01 로그](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/attempt-01.log)·원 driver도 보존했다. 최초 private driver가 연속 날짜만 허용하는 `capture_window`에 비연속4일을 전달해 원천 처리 전에 거부됐다. attempt-02는 각 일자별 기존 verifier를 사용했으며 제품 소스 변경은 없었다. 결과 확인기의3개 원 실패(CF label 오기, native null/derived false 혼동, policy SHA owner 혼동)도 closure에 원문으로 보존했다. 최종 확인기는 실제 field와 native policy validator를 사용해 통과했다. 격리 config 파일 부재 경고는 로그에 남았으며 설정을 만들거나 계좌/API를 호출하지 않았다.

## 5. 종결 범위와 남은 결론

`MainAllScopeTrailingReplay`의 **별도 holding 배분비용 consumer 구현 결손**은 이번 commit·합성 public producer→assembler→replay/diagnostic 검증·실제13건 대사로 닫았다. 이를 이유로 원천이 더 쌓여도 비용 소비가 영구 불가능한 구조는 남기지 않았다. 다만 현재13건의 전체 보유 custody/경로 증명을 소급 생성하지 않으므로 실제 경제 비교는 미지원 결론이다.

미기록 ADD/부분잔량의 주문·잔량·TTL과 SELL 이후 실제 없었던 AI/경로는 배분비용으로 복구할 수 없다. 해당 과거 cohort는 명시적 미지원이며 자연 표본을 기다리면 같은 과거가 복구되는 것으로 취급하지 않는다. 향후 새 실험이나 범위 확장은 먼저 후보·입력·평가 기준을 등록해야 한다. 원 자료로 실행하지 않은 E4/E5/E7 연구까지 완료했다고 확대하지 않는다.

운영 발행·Main 재시작·provider/계좌/API·신규 구독·주문·P5는 실행하지 않았다. 초기 parent 동등 정책의 자연 장후 생산·PREOPEN·정확 PID 수용은 기존 owner의 별도 수용이며 추가 경제 승인 게이트를 붙이지 않았다. 이 후속은 이전 감사의 역사적 결과를 덮어쓰지 않는다.


## 6. native 비용 결손 사유 보완과 최종 별도 대사

동시 진행한 [보유·익절 후속 연구](main-holding-exit-followup-research-execution-review-2026-10-18.md)와 비용 소비 계약을 대사하면서, native `_completed_trade_projection`이 생산하는 비용 전용 사유 `source_gap_exact_cost_missing`을 이 adapter가 허용하지 않는 결손을 확인했다. 비용 영수증이 나중에 검증돼도 이 사유 하나로 연구 배분비용을 소비하지 못하므로 기존 비용 전용 사유 집합에 추가했다. terminal·수량 보존·잔량·native 권한·시각·원 BUY/SELL leg·custody·공식 비용 검증은 그대로다. duplicate 또는 알 수 없는 다른 사유가 함께 있으면 계속 source gap이며 순손익은 null이다.

최종 commit은 **`3ab6916e28ee3301402c6ac8b64fbc2090f49000`**, 코드 계약은 `bf4f140b0648ddb71115796caeee8793702d8be81347021e1625f9bca2f25228`이다. 실제 native 완료 producer 원문 → 원 registry → 공식 비용/배분 producer → adapter 양성과 duplicate/unknown 사유 음성을 추가했다. 비용 모듈 **20 PASS/5.21초**, 변경2파일 compile·Ruff(E9/F821/F822)·diff check, 독립 재리뷰 지적0으로 닫았다. 최초 합성 시험의 비숫자 주문/체결 ID를 기존 계약이 거부한 로그도 남겼으며, fixture 최초 입력을 숫자 ID로 바꾸어 검증했다. 기존 실제 evidence를 수정하거나 제품 validator를 완화하지 않았다.

[최종 코드 종결 v2](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/code-review-closure-v2.json)는 앞선 d81a 종결과 실패 로그를 참조한다. [attempt-03](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/attempt-03/report.json)·[결과 재검증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/attempt-03/result-validation.json)은 새 코드를 사용한 별도 비용 대사이며 attempt-02를 덮어쓰지 않았다. **원508개(13 actual/13 alternative/482 CF), 배분비용 provenance5건/결손8건/경제 paired0건**은 그대로다. 원247개 actual outcome의 손익 null, native false11/null2 및 derived false13, 초기정책과 사용19개 의존파일 세대를 보존했다. wall23.513초·CPU22.421초·peak RSS168,648KiB·종료 shared Claim used0/64MiB를 확인했다. 재사용/현재 검증 범위는 §4와 같으며 전체 quote 경로 재생이나 전체12GB의 현재 재해시를 새로 수행하지 않았다.

### 6.1 동시 연구의 비용8건과 이 adapter의5건

[두 세대 대사](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/cost-followup/two-generation-comparison.json)는 동시 branch `57a4659f471044f8c8a59db53fc01b12d194333a`의8건과 이 branch의5건을 같은13개 완료 ID로 비교한다. 공통5건의 원 영수증 SHA·비용·net 참고값은 정확히 같다.

| 경계 | 등록된 terminal 비용 진단(57a) | strict holding adapter(3ab) |
| --- | --- | --- |
| 연구 scope | 원 `initial_quantity_research_only`를 유지한 terminal reference | 별도 `main_holding_exit_research_only` annotation |
| 비용 reference | 8건, 비용4,065원/net 참고19,535원 | 5건, 비용3,170원/net 참고2,830원 |
| 추가3건 49267/49300/49328 | 등록 acceptance의 native 재관측 audit와 원 체결 identity/producer/시각을 결속한 별도 bridge로 수용 | 원 completed projection의 duplicate strict 사유로 미지원 |
| 경제 적격 / canonical 손익 / 운영 | 0 / 불변 / 적용 없음 | 0 / 불변 / 적용 없음 |

57a의 추가3건은 projection의 `completion_at == first_observed_at`과 원 체결 `completed_at == original_occurred_at`을 구분하며 record·order/execution·native identity/payload digest·동일 producer SHA·시각 순서·cutoff를 대사한다. 시간 허용오차는0이고 `raw_source_events_reverified_here=false`다. **추가3건을 확보 불가능한 과거 원천으로 단정하지 않는다.** 별도 등록 증명을 소비하는 계약의 차이이며, 이 adapter에 그 acceptance/audit bridge를 통합·검증하지 않은 상태에서5건을8건으로 바꾸지 않았다. 49294는 양쪽 모두 부적격이다.

두 branch는 같은1bf35e6c에서 분기한 별도 구현이며 서로 overlay하지 않았고 통합 검증도 수행하지 않았다. 57a의 terminal 참고 진단과 이 adapter의 public assembler/replay 진단 경로를 하나의 검증 완료 구현으로 합쳐 부르지 않는다. 실행·원천 재검증 범위도 달라0.142초와23.513초로 성능 개선율을 계산하지 않는다. 원 비용·보조 AI·custody·초기정책·selector는 보존했고 **P5는 별도 지시 전 실행하지 않는다.**
