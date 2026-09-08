# #119 BUY Funnel → #23 Entry recheck: 10:25 submit 병목 점검

이 문서는 보완 전 점검 기록이다. 이후 명시적 구현 요청에 따른 수정·재대사 결과는 [보완·재리뷰](2026-09-08-buy-funnel-entry-recheck-remediation-review.md)를 따른다. 아래 미수정 판정과 수치는 당시 근거로 보존한다.

## 판정과 범위

**장후 전체 재실행이 아니라 #119 원인/identity 전달 수리가 우선이다. #23 강제 ON은 권고하지 않는다.** 이번 요청은 점검이며 코드 구현·runtime 변경 지시로 확대하지 않았다. 매매 PID, env/lock, 주문, Provider, canonical report/cache는 변경하지 않았다.

9/8 10:25 산출물은 이미 다음 정기 generation으로 갱신됐으므로 그 파일을 현재 원본으로 제시하지 않는다. schema10 lossless cache를 직접 읽고 KRX/KRX_REGULAR 및 `emitted_at <= 2026-09-08T10:25:05`로 제한해 기존 순수 집계 함수를 메모리에서 실행했다. 요청에 제시된 **71=terminal66+pending5+submit0**, upstream33/latency28/AI authority5와 refresh 5=AI4/budget1을 동일하게 재현했다. 이 재현은 기존 계산과의 일치이며 아래 raw 누락·identity 결함이 없는 완전한 모집단이라는 뜻이 아니다.

## 1. 실제 #23은 OFF를 정상 소비 중

| 연결 | 관측 |
| --- | --- |
| 9/7 controller | 21:21:10 생성, controller v4. `desired_enabled=false`, `stop_reasons=[drought_history_source_quality_gap]`, valid critical day1 |
| 이전 source | 9/3·9/4 Sentinel 모두 schema3. 해당 KRX exact 계약이 현재 consumer 검증에서 제외됨. 9/7만 valid/critical/addressable |
| 9/8 PREOPEN | 07:35:03 apply plan에서 controller `loaded`, quality update `entry_opportunity_recheck_runtime:drought:2026-09-03:2026-09-07:off`; false 값을 생성 |
| 현재 main PID | 461794, 09:27:19 시작. 11시 점검 당시 `/proc/461794/environ`의 해당 key만 읽어 `ENABLED=false`, `ALLOWED_SCOPES=''`, `INTRADAY_ESCALATION_ENABLED=false`, source dirty=false 확인 |
| 자연 recheck | 원본 pipeline에서 점검 시점까지 `entry_opportunity_recheck_*` stage 0. 이를 단독 결함 또는 적용 성공으로 보지 않음 |

`allowed_runtime_apply=true`/candidate ready는 **OFF 변경을 적용할 수 있다는 뜻**이지 ON이라는 뜻이 아니다. #119의 `followup.owner=postclose_threshold_cycle`, `runtime_effect=auto_workorder_no_intraday_mutation`도 확인했다. 장중 critical 발생만으로 #23이 즉시 켜지는 구조는 아니다. 다음 장후 controller→다음 PREOPEN가 기존 owner다.

현재 구현은 정확한 최근3거래일 모두 source-quality PASS이고, 마지막 날을 포함한 최소2일의 addressable critical이어야 ON을 고려한다. 9/8이 유효 critical로 마감해도 9/4 invalid가 남아 있으므로 **현 계약 그대로면 다음9/9 장전 ON은 보장되지 않는다**. 이력 수리 없이 새 유효일만 채우는 경우 9/7·8·9의 조건 충족 뒤9/10 PREOPEN가 최초 가능한 창이다. 이는 조건부 일정이지 source 회복·경제성 ETA가 아니다.

## 2. 확인한 진단 결함

### F1 — 가격 재검증 terminal이 cache/축 분류에서 누락

010170 / record41181 / promotion `SCANPROM-010170-1788828780350`:

| 시각 | 원본 stage/판정 |
| --- | --- |
| 09:56:44.264013 | `latency_pass`, quote refresh 적용 |
| 09:56:44.824654 | **`entry_submit_revalidation_block`**, `standard_stale_context_or_quote` |
| 09:57:01.932139 | 다음 평가의 `budget_pass` |
| 09:58:36.739463 | 재시도 `latency_pass` |
| 09:58:41.781339 | fresh AI DROP20, authority veto |

원본의 첫 차단은 `price_context_stale_at_submit=True`, 가격결정 context age9148ms, price decision age3027ms였다. 당시 `quote_stale_at_submit=False`, quote-consistency block=false, canonical fresh quote age247.851ms다. 호가를 새로 받아도 **가격결정의 입력 문맥이 새로워지는 것은 아니다**. 기존 safety가 이를 차단했으며 지금 그 safety 완화 근거는 없다.

`entry_submit_revalidation_block`이 [Sentinel stage 목록](../../src/engine/buy_funnel_sentinel.py:59)에 없고 `_payload_to_cache_row(..., exclude_summary_stages=True)`가 이 실제 row에 `None`을 반환한다. exact axis와 downstream 목록에도 없어서 보고서의 PRICE_REVALIDATION0/budget잔류1이 실제 최초 원인을 놓친다. 같은 오전 PREMARKET 08:23:57/473980도 동일 stage가 탈락하지만 KRX 분모에 섞지 않았다.

### F2 — refresh의 5는 exact 실행 횟수가 아닌 record 수

[refresh 집계](../../src/engine/buy_funnel_sentinel.py:2129)는 record 기반 key 집합을 만든 뒤 각 record의 **첫** latency pass 이후 첫 인식 event만 읽는다. 따라서 10:25까지 실제 refresh pass **7회/5records**를 5건으로 표시한다. 387690의 두 시도와010170의 두 시도를 구분하지 않는다.

일곱 pass의 관측 후속은 **fresh DROP4회, probe 의도 없는 WAIT1회, timeout1회, 가격 문맥 stale1회**다. 010170 가격 차단 후 재시도를 `budget 잔류` 하나로 끝내고, 뒤의 DROP도 놓친다. 이 수치는 위 raw/cache 시각 대사이며 아직 수정된 authoritative report의 새 exact attempt 수가 아니다.

### F3 — 서로 다른 단계의 attempt ID 가용성 때문에 cycle 귀속이 갈라짐

[exact partition](../../src/engine/buy_funnel_sentinel.py:904)은 producer ID로 `main_lifecycle_attempt_id`만 읽는다. 실제 `budget_pass/latency_pass/authority_block`에는 scanner promotion이 있지만 main ID가 없는 반면 `ai_confirmed`에는 둘 다 있다.

- 052690(record41080): 09:32 이전 AI의 promotion `...7437188`; 09:40 budget/latency의 promotion `...7809778`. 그런데 budget/latency가 이전 cycle1에 붙고, 뒤 새 AI/authority는 cycle2에 붙는다. cycle1이 `pending`으로 남는 것을 실제 비동기 작업 대기라고 해석할 수 없다.
- 387690(record41223): timeout 뒤 budget/latency로 생긴 cycle2가 pending으로 남고, 같은 promotion의 새 AI가 explicit-state map의 과거 cycle을 다시 선택한다. 이전 timeout과 뒤 WAIT를 서로 독립적인 실행 terminal로 완전히 보존하지 못한다.

그러므로 **71/66/5와 미분류0의 보존식만으로 exact 연결 완료를 선언할 수 없다**. 새 ID를 임의 발명하거나 scanner promotion 하나를 모든 재시도의 유일 ID로 삼는 것도 해법이 아니다. producer의 실행시도 ID, parent promotion, AI request/trace, ordered retry를 별도 결속해야 한다.

## 3. #23 ON으로 이번 회복 실패를 해결할 수 있는가

아니다. 확인한 여섯 AI authority event는 rising-missed scout 계약이며 #23의 정상 WATCHING 재검토와 동일한 경로가 아니다. fresh DROP4, 관찰전용 WAIT63(명시 probe intent false)1, timeout/NOT_EVALUATED1이다. fresh 결과의 age는0.108~0.399초로 대부분 AI TTL 만료 문제가 아니다. #23의 기존 profile은69~74.999점, canonical probe/quality 계약이며 DROP veto·timeout·가격 stale·latency DANGER를 우회할 수 없다.

Upstream terminal33도 strength/momentum17, AI score10, VPW3, first WAIT1, liquidity1, zero quantity1로 나뉜다. 모두를 recheck로 해결 가능한33건으로 보지 않는다. latency terminal28의 raw reason은 micro-spread/일반 spread가 중심이며 reason 다중 태그 합계를28에 다시 더하지 않는다. AI DROP의 경제적 정당성/입력 품질은 별도 exact trace 검증 전에는 확정하지 않는다.

## 4. 구체적인 보완 순서와 acceptance

실행 owner는 당일 기존 `EntryRecheckNaturalAttribution0907`을 유지하며 새 중복 work item을 만들지 않는다. 아래는 이번 점검의 권고이며 구현/기동 승인으로 쓰지 않는다.

1. **#119 수집·분류 보완:** 실제 `entry_submit_revalidation_block`과 명시적인 비동기 대기/재시도 terminal을 분류한다. 가격 차단을 PRICE_REVALIDATION에 연결하고 cache/schema 세대와 직접 consumer 검증을 함께 갱신한다. 위010170 raw 반례가 누락0, 최초 가격 차단과 뒤 DROP을 각각 보존해야 한다. 안전 차단은 유지한다.
2. **identity 전달 보완:** budget→latency→AI→authority→submit의 같은 실행 ID 전달, promotion 교체·같은 promotion 재시도·기존 explicit state 복귀 반례를 회귀화한다. refresh는 record census와 실행별 결과를 분리하고 공통 exact ledger를 소비한다. 순서 미확정 row는 pending 성공 대기가 아닌 명시적 lineage gap으로 분리한다. 올바른 새 분모는 재구축 후 확정한다.
3. **#23 조건 달성 가능성 검토:** 9/3·9/4 원본이 남아 있고 필요한 identity를 복원할 수 있을 때만 해당 Sentinel→controller의 최소 재생성을 검토한다. 불가능한 역사를 합성하지 않는다. `3일 source 완전성`과 `2/3 critical`을 분리하는 migration 정책 대안도 검토하되 invalid를 정상일로 간주하거나 live 허들을 수동 해제하지 않는다. 향후 ON/OFF는 유효 source와 기존 PREOPEN owner가 결정한다.
4. **실제 효과 acceptance:** #23 적용 후보군과 rising-missed 최종 AI 경로를 분리한 뒤, eligible→evaluated→armed→submit→fill/terminal/net을 비교한다. 새 ID/분류 수리만으로 수익·제출 개선을 주장하지 않는다. 이번엔 장후 전체 chain을 돌리지 않는다.

## 근거와 검증

- [당일 lossless cache](../../data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-09-08.jsonl): schema10, 직접 읽기만. 원본 append 중 마지막 partial row를 정상 source로 쓰지 않는다.
- [당일 raw pipeline](../../data/pipeline_events/pipeline_events_2026-09-08.jsonl): 명시 stage/record/시각을 streaming으로 대사. 원본 수정/압축/캐시 갱신 없음.
- [9/7 controller](../../data/report/entry_recheck_drought_controller/entry_recheck_drought_controller_2026-09-07.json), [9/8 apply plan](../../data/threshold_cycle/apply_plans/threshold_apply_2026-09-08.json), [9/8 env](../../data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-08.env). PID461794는 위 시각의 읽기 전용 receipt이며 미래 PID를 보증하지 않는다.
- 기존 Sentinel/controller/recheck 테스트3개 파일 **92 PASS**. F1 실제 raw cache 탈락, F2 record-collapse, F3 자연 cycle 분리 반례는 위 별도 읽기 전용 재현으로 확인했으며 기존 테스트 PASS로 미해결 결함을 지우지 않는다.
- 문서 review gate: 근거/시각/scope/권한을 재검토했고 기존 OPEN owner 1건 유지, 로컬 링크 8건 존재, print-only parser와 `git diff --check` 통과를 확인했다. **코드 결함 F1~F3 미수정**이며 finding0/장후 GREEN을 주장하지 않는다. Provider/broker 호출·report 재생성·봇/env/lock 변경 없음.
