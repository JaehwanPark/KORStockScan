# 계좌 여력 원천 조회 중복 보완 구현·반복 리뷰

2026-10-02 19:31 KST 기준. 사용자 승인에 따른 반복 리뷰·추가 보완·불변 배포·ubuntu 재기동·당일 정책/PID 소비와 후속 정기 감시를 완료했다. 자연 BLOCK의 정확 재사용도 확인했다. 전체 장중 절감률·정책 경제성은 별도로 남긴다.

소유자: [당일 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 `EntryCapacityReadBudgetRemediation1002`. 설계: [계좌 여력 원천 조회 보완계획](../proposals/entry-capacity-source-read-budget-remediation-plan-2026-10-02.md). 기존 ENTER_NOW/guard/residual 자연 lineage 수용은 `MainEntryEconomicLineageRepair1002`가 소유한다.

## 1. 구현과 원천·소비 경계

| 지점 | 구현 | 검증한 경계 |
| --- | --- | --- |
| `kiwoom_orders` | 정상 kt00001 원 receipt의 token scope hash·원 금액·원 시각·새 조회 generation을 저장하고 loop cache에 그대로 전달한다. | 같은 receipt의 age/cache-hit/fresh→loop-cache만 identity에서 제외한다. 새 조회는 같은 금액이어도 새 세대다. 미확인/fallback metadata는 기존 보수적 identity를 유지한다. Operator floor 금액·authority·실행 반환값은 유지한다. |
| Main capacity helper | async/pending/후속 준비가 같은 receipt/in-flight 상태를 사용한다. 동일 준비 worker만 기존 deadline 안에서 합류한다. 다른 가격은 최신 pending으로 남긴다. | Frozen observer 무대기·가격 환산 금지·미래 응답 소급 금지·실패의 cache 성공화 금지. Network I/O는 공유 lock 밖이다. Queue 8·pending 5초·retry suppression 0.5초를 유지한다. |
| 준비 예산 | 합류 실패 뒤 새 HTTP를 이어 보내지 않는다. Scope 계산 후에도 deadline과 기존 HTTP 0.30초 reserve를 다시 검사한다. | 소진된 준비는 deferred 원천 결손이다. 정확하게 제공된 route/venue/session이 기존 replay에서 불지원일 때만 capacity 준비를 생략한다. 누락 route 추정이나 기계판정 생략은 없다. |
| 필수 실행 조회 | sizing/pre-submit·leg/residual/AVG_DOWN purpose를 명시한다. | 관측 cache나 진행 중 source-only 조회가 있어도 필수 HTTP를 새로 수행한다. 기존 broker 수량/가격/마진/floor·custody·cooldown·hard safety를 유지한다. |
| 계측 | `[ENTRY_CAPACITY_READ]`에 논리 ID·평가/준비 ID·PID/commit·정확 가격·scope/financial hash·route/session/action·source clock/hash·HTTP/admission 횟수·합류 시간을 기록한다. Pending ID는 `[ENTRY_CAPACITY_PREPARATION]`으로 후속 worker와 연결한다. | 계좌번호/token/headers/raw error 미기록. 타임아웃도 전송 시도이며 unknown은 null이다. 당일/PID/목적별 논리·물리·가용 source·결과 누계를 bounded 메모리에서 기존 logger로 발행한다. 계측 예외는 실행 결과에 전파되지 않는다. |

Main key의 account/token/origin/day·정확 code/price·기존 inventory/custody signature·financial deposit identity를 보존한다. 준비/ENTER_NOW TTL 2초·BLOCK/RECHECK cache-only TTL 5초, source admission 최대 1.25초, HTTP 0.15/0.15초와 기존 retry/auth/cooldown을 유지한다. 계좌를 공용 분봉 캐시나 프로세스 간 응답 공유에 넣지 않았다. 새 thread/service/cron/report producer나 전체 raw 로딩을 추가하지 않았다.

Miss의 `inventory_or_custody`는 기존 결합 signature다. `deposit_identity_or_unproven_diagnostics`는 미확인 metadata 분기도 포함한다. 이를 금융 결손 또는 진단 오인 miss 하나로 단정하지 않는다. 원 clock·해시가 확인된 fixture만 중복 절감 근거로 사용했다.

## 2. 공식 API 대사

변경 전 18:04:27.741714 KST에 current upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`를 확인했다.

- `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`을 열람했다. 같은 commit tree에서 `kiwoom_docs`가 없음을 추가 확인했다.
- kt00001/kt00011 `POST /api/dostk/acnt`, `api-id`, Bearer/header·continuation·실전/모의 분리, kt00001 `qry_tp=3`, kt00011 raw code/정확 KRW `uv`·기존 응답 필드를 대조했다.
- SDK JSON body와 Postman query parameter 표현 차이를 기록하고 기존 JSON wire를 유지했다. 이번 변경은 provenance·호출자 purpose·전송 시도 metadata이며 응답 금액/단위/마진 해석을 바꾸지 않는다.
- 공개 원문: [specs](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/specs.py), [core client](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/core/client.py).

회수 시각·파일 SHA256·tree 확인은 `tmp/entry-capacity-implementation-20261002/official-reference.json`에 보존했다. 실제 인증/계좌/주문/provider 호출은 수행하지 않았다.

계좌 준비 deadline 재보완 전에 19:03:21 KST current upstream을 다시 확인했고 SHA는 동일했다. 재확인 증거는 `tmp/entry-capacity-release-review-20261002/official-recheck.json`이다.

## 3. 리뷰·보완·재리뷰

1. Full metadata key의 진단 변화 miss를 재현하고, TTL 확대·price 환산 없이 검증 가능한 원 receipt만 정규화했다.
2. Source worker 합류·required read 독립 HTTP·다른 가격 pending·예외 정리·frozen observer 무대기·미래 source 비채택을 검증했다.
3. Cached amount에 latest 성공 record의 다른 세대가 붙지 않도록 loop cache 자체 receipt를 사용했다. 서로 다른 token의 동시 성공에 원 clock이 섞이지 않도록 로컬 원 시각을 저장했다. 외부 metadata 사본 변경이 내부 receipt를 바꾸지 않도록 nested receipt를 복사했다.
4. 타임아웃이 HTTP 0회로 보이던 계측을 고쳤다. 전송과 admission을 구분하고 준비 deadline을 scope 계산 후 재검사했다. Financial key/원 cash cap을 계측으로 덮지 않는다.
5. 추가 재리뷰에서 자정 경계를 넘긴 늦은 완료가 새 날짜의 누계를 지우는 결함을 보완했다. 시작 KST 날짜별 2일·고정 purpose만 보관하며 더 오래된 완료는 개별 row와 `outside_retained_day_window`로 구분한다. 날짜 집계 순서를 뒤섞은 회귀를 통과했다.
6. 준비 응답이 기존 worker 마감 뒤 완료되면 ready로 표시하지 않도록 완료 시각을 재검사했다. Join도 기존 마감 내에만 채택한다. Receipt의 원 시각은 보존하고 과거 판정에 소급하지 않는다. 늦은 완료 회귀를 통과했다.
7. 비용·후행 label·BLOCK/RECHECK raw attempt·실제 AI PASS/VETO 권한·주문 소유권을 변경하지 않았다. 결손을 0원 EV로 채우지 않는다. 표적 변경 범위에서 미해결 신규 결함은 발견하지 않았다.

## 4. 회귀와 기존 실패 분리

- 격리 후보 최종 표적 **278 PASS / 6.61초**: capacity/deposit/read-control/async bridge/async coordinator 전체 및 영향 있는 scale-in capacity·cash budget·one-share·retired source selectors. 무관한 scale-in 897개는 deselect했다. Fork 회귀 deprecation warning 1개는 실패가 아니다.
- 같은 격리 후보의 `test_entry_execution_sizing_plan.py` 전체 **64 PASS / 115.04초**. BLOCK/RECHECK plan-only anchor·ID/action, exact-cost producer→projection→기계/보조 소비와 SOR/NXT 지원·미지원 경계를 모두 통과했다.
- 이전 workspace 실행의 61 PASS/3 FAIL은 기록으로 보존한다. 이전 baseline 시험은 producer만 교체한 부분 비교였으므로 전체 baseline의 기존 실패로 확정하지 않는다. 이번에 underlying isolated replay 결과까지 점검하고 변경·bypass 없이 전체 후보 64개가 통과했다. 정확 REST/cutoff 결손인 SCANNER fixture는 정상 source-gap 의미를 그대로 유지한다.
- 배포·native handoff·bootstrap·restart race 계약 **136 PASS / 5.63초**. 후보 회귀·소비·배포 계약 합계 **478 PASS**다. 기존 자연 lineage 수용은 테스트 성공과 별개로 `MainEntryEconomicLineageRepair1002`에 남긴다.
- Python compile·`git diff --check`, 문서 링크/단일 owner·print-only parser 및 배포 wrapper의 `bash -n`을 검증한다. 전체 자동화·live provider 시험은 수행하지 않는다. 승인된 봇 기동에서의 자연 초기화 호출은 별도 runtime 소비다.

로그: `tmp/entry-capacity-implementation-20261002/final-validation.txt`, `owner-chain-tests.txt`, `baseline-owner-differential.txt`. Runtime/source/test는 기존 파일을 보완했다. 새 Python 파일은 역할/location 확인 후 test 소유자 `src/tests/benchmarks`에만 추가했다.

최신 후보 증거: `tmp/entry-capacity-release-review-20261002/{isolated-targeted-tests,isolated-owner-tests,deployment-contract-tests}.txt`. 다른 세션의 가격 패턴 코드·운영 문서·checklist item은 원 workspace에 보존하고 이번 릴리스에 포함하지 않는다.

## 4.1 진단 지표 계약

`metric_role=diagnostic`, `decision_authority=report_only`, `window_policy=request_started_KST_date_and_PID; retain_two_dates`, `sample_floor=0_for_counter_reporting`, `primary_decision_metric=none`, `source_quality_gate=exact_financial_key_original_clock_hash_and_transport_metadata`, `forbidden_uses=order_provider_threshold_or_retry_authority; policy_promotion_or_EV_claim`이다. Unknown HTTP는 별도 누계로 남기고 physical HTTP에 0으로 가산하지 않는다. 비교에는 동일 venue/session·적격 원천·logical demand 분모가 필요하다. 새 지표를 주문/정책 승계 조건으로 소비하지 않는다.

## 5. 샘플 성능 3회 비교

Baseline은 작업 시작 시 보존한 3파일이며 Git `1930ac82393a6c5e02fa7aeaf8e569eb01f5d576`의 파일과 byte가 같음을 확인했다. [Test 전용 replay](../../src/tests/benchmarks/entry_capacity_source_reads.py)는 30-target 금융 signature·정확 요청/상태 변화/응답 시각과 real kt00011 parser를 사용한다. **Network/admission은 mock, API 0회·정책 발행 0회**다. 기존 streaming logger처럼 benchmark도 마지막 8행만 메모리에 유지한다.

각 1,000 batch에 동일 receipt 진단 변화 10회, 고정 ENTER_NOW/BLOCK/RECHECK 관측 각 1회, 필수 조회 5회를 재생했다. 총 18,000개 논리 수요다. **Action은 fixture 분모이며 classifier 또는 장후 정책 수익률 시험이 아니다.**

| 지표 | Baseline | Candidate |
| --- | ---: | ---: |
| Source-only 물리 HTTP | 10,000 | 1,000 |
| 필수 실행 물리 HTTP | 5,000 | 5,000 |
| 전체 물리 HTTP | 15,000 | 6,000 |
| Action별 exact capacity 가용 표본 | 각각 1,000 | 각각 1,000 |
| Wall 중앙값 | 2.078843초 | 2.142838초 |
| CPU 중앙값 | 2.078281초 | 2.142245초 |
| RSS 중앙값 | 306,048KiB | 307,368KiB |

전체 HTTP 60%·해당 중복 source fixture 90% 감소. Wall×1.030784·CPU×1.030778·RSS +1.289062MiB로 ≤1.10/≤16MiB 기준을 통과했다. 모든 run의 원 clock/hash/cash quantity digest는 `c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8`로 같았다. 원 수치/code hash: [샘플 JSON](entry-capacity-source-read-budget-sample-2026-10-02.md).

초기 100-batch 측정의 JSON decode·로그 전량 RAM 보관은 실제 logger에 없는 benchmark 비용이어서 streaming sink로 바로잡고 1,000-batch×3으로 짧은 wall 측정 변동을 줄였다. 인위적인 network/CPU 지연을 추가해 조건을 맞추지 않았다. 보류가 없는 fixture이므로 자연 보류율·실제 응답 지연·순익 개선을 주장하지 않는다. 처음부터 한 번만 읽던 경로에는 감소를 주장하지 않는다.

각 version 3회, 같은 `--batches 1000`으로 재현한다.

```bash
PYTHONPATH=. .venv/bin/python src/tests/benchmarks/entry_capacity_source_reads.py --handlers src/engine/sniper_state_handlers.py --orders src/engine/kiwoom_orders.py --utils src/utils/kiwoom_utils.py --batches 1000
```

Baseline은 source argument를 각각 같은 commit에서 보존한 `tmp/entry-capacity-implementation-20261002/baseline-src__engine__sniper_state_handlers.py`, `baseline-src__engine__kiwoom_orders.py`, `baseline-src__utils__kiwoom_utils.py`로 바꾼다. 스크립트는 명시된 source에서 검토 대상 함수만 AST로 불러 기동/인증 코드를 실행하지 않는다.

## 6. 현재 소비와 다음 수용

19:14 교체 전 Main은 ubuntu PID 2920811, supervisor 2920765, cwd는 `shared-candle-directory-20261002-d19d0d7b/src`였다. 다른 세션의 가격 패턴 코드·문서·checklist를 제외하고 `codex/entry-capacity-reviewed-20261002`에서 14개 범위 파일만 커밋했다. 원 workspace의 미커밋 작업은 보존했다.

- 불변 릴리스: `c61fefcfb8f0d5e4b6933fcd49ed0fb768fd53e0`, `/home/ubuntu/KORStockScan-runtime-releases/entry-capacity-source-read-20261002-c61fefcf`. 이 root의 최종 **478 PASS / 127.62초**, source clean, compile·shell syntax·diff·단일 owner/parser 수용. 원 checkout의 공유 경로는 `tmp/entry-capacity-release-review-20261002/release-checkout-shared-backups`에 보존 후 기존 공유 mount로 연결했다.
- 19:19:49 native policy-preserving handoff prepare PASS 후 기존 `deploy/run_runtime_release.sh restart`를 **ubuntu**로 실행했다. 기존 PID 정상 종료→drained tmux supervisor 교체→19:20:04 bootstrap verify PASS. 새 Main **2948449**, supervisor **2948381**, start ticks **55723543**, cwd는 새 release의 `src`, UID **1000**이다. Main singleton과 ubuntu tmux `bot`을 확인했다. Root 봇을 만들지 않았다.
- Native consumed receipt의 `actual_pid_consumed=true`, PID/commit/cwd·manifest SHA 결속 PASS. `--verify` 출력의 prepared `actual_pid_consumed=false`는 준비 영수증의 고정 상태이며 실제 소비 증거는 별도 `*.consumed.json`이다. 준비와 소비를 혼동하지 않는다.
- 정책/PREOPEN/prepared **5파일**, 독립 pin **416개**, ubuntu cron 및 root cron 부재 상태의 hash를 before/after 대조해 모두 동일했다. Selector UID/GID·0600을 유지했다. Widget/episode의 별도 release/policy pin은 기존 값을 보존했다.
- 새 PID heartbeat와 살아 있는 핵심 thread, ProcessHealthDetector의 **PASS / All processes and threads healthy**를 확인했다. 19:20:18 WS 연결·LOGIN ACK와 이후 실제 0B/0D 수신을 확인했다.
- 19:20 정기 sentinel이 **19:21:09 DONE**으로 종료하고 monitor `as_of=19:21:07.603034`, `runtime_effect=false`, `status=observing`을 발행했다. 교체 경계 실행과 구분해 후속 **19:30:01 START→19:30:40 DONE**을 확인했다. 최신 monitor `as_of=19:30:38.911042`, `source_as_of=19:30:09.100371`, `runtime_effect=false`, `status=observing`, `blocker=null`; selector/PID는 c61fefcf/2948449다. 19:25의 기존 cooldown 8초 SKIP은 정상 보존하고 수동 report 재실행은 하지 않았다. 이는 운영 감시 소비이며 정책 수익성/전체 source 정상 판정은 아니다.

Runtime 증거: `data/runtime/startup_readiness/2026-10-02/entry_capacity_source_read_review/{before,after,prepare,native-handoff.verify,native-handoff.consumed,process-health,release-set.after}.json`, `restart.log`; 코드 검증은 `tmp/entry-capacity-release-review-20261002/immutable-validation.txt`다. 정책 재계산·PREOPEN/독립 pin/cron 변경·직접 주문/시험용 계좌 API 호출은 하지 않았다. 승인된 봇의 자연 계좌 준비와 WS 초기화는 수행됐다.

후속 감시·자연 receipt 원 수치는 같은 runtime 증거 폴더의 `scheduled-consumer.json`, `natural-acceptance.json`에 보존했다. 문서 현행화 후 print-only parser의 해당 stable ID가 1개임을 확인했다. 검토한 변경 범위의 미해결 코드 결함은 0건이다. 위 수용으로 전체 자연/경제성 owner를 완료 처리하지 않는다.

## 6.1 실제 준비→BLOCK 소비의 유한 증거

19:20:47.781 원 시각으로 005930/275500의 source-only 준비가 성공했다. 19:20:49의 `aims-44f698cedb9c046dd1c0` BLOCK 평가가 같은 financial scope·가격·source hash `2fb5c9ea392f02cd7fb8949b6356593f7db446e8edcfbfbc5c1137b7553323e9`를 추가 HTTP **0회**로 재사용했다. PID/commit은 새 릴리스다. 원 시각을 갱신하지 않았고 source age 약 1.238초로 기존 BLOCK cache-only 5초 안이다. 준비 ID `77a158ec92f0ea90a2f4243991ee865d2ef88cd1fe6f17ca5ecd04cc57f28b66`와 관측 scope가 일치한다. 다른 코드 042700의 준비도 fresh source로 완료됐다.

이 사례는 계측·미진입 원천 보존·정확 receipt 소비의 자연 증거다. 준비 1회→관측 0회라는 사례를 전체 read 예산 개선율이나 정책 경제성으로 확대하지 않는다. 새 deposit의 증명된 진단 정규화 효과·required live sizing과 반복 적격 창의 전체 보류/가용 source 분모는 아직 `not_observed`다. Raw/비용 결손을 0 EV로 채우지 않는다.

19:26의 유한 log 관측 9건은 source 준비 `fresh_success=5`, 관측 `exact_reused=3`, 관측 `scope_changed=1`이다. Cache-only 결손 1건을 정상으로 뒤집지 않았다. 전체 장중 수요·처리량·절감률 분모로 사용하지 않는다.

배포한 candidate source hash/PID 소비 뒤 동일 venue/session·중복 수요가 있는 적격 자연 창에서 논리/물리·보류·가용 source·준비 지연을 비교한다. 표본 없으면 `not_observed`다. Raw 기계 표본·가격 라벨·owner/full-cost 경제성·실제 보조 PASS/VETO·배포/PID 소비는 각 owner로 확인한다. 과거 source gap을 새 receipt로 소급 복구하거나 준비 수리만으로 정책/순익 수용을 닫지 않는다.

전일 `postclose_finalization: terminal failure marker observed`는 이번 계좌 여력 범위에서 수정하거나 지우지 않았다. 새 기동 후에도 해당 경보가 남는다. 배포 성공을 전체 장후 정상 또는 정책 경제성 성공으로 해석하지 않는다.
