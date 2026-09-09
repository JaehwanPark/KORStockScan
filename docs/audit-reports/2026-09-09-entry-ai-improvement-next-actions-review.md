# Entry AI #76/#77/#82 → #78 → #80 다음 개선작업 점검

작성일: 2026-09-09 KST. 읽기 전용 점검이며 코드 구현·배포·장후 재생성 지시를 실행하지 않았다.

## 판정

**추가 보완 필요. 지금 우선할 작업은 sparse 원천 판정 정합성과 안전 보정 시 exact request 보존이다.** 기존 micro 입력 누락은 아래 P1-C의 후속 확인에서 다른 세션의 재기동 뒤 정상 경로 전달이 확인됐다. 같은 보완을 재구현·재기동하지 않는다. 비용 label과 versioned prompt 연구의 후속 연결도 필요하지만, 이들을 실주문 허가나 수익 실현으로 해석하지 않는다.

목표는 단순 BUY 증가가 아니라 비용 후 작은 양수 기회의 반복 포착이다. 입력 결손 때문에 WAIT한 사례, 모델이 정상적으로 DROP한 사례, 후처리로 행동이 바뀐 사례, 이후 제출·체결에서 막힌 사례를 다른 분모로 평가해야 한다. 이번 점검에서는 기존 안전·수량·주문·신선도 guard를 완화하지 않았다.

## 1. 현재 실원천에서 재현한 결함

고정 관찰창은 `2026-09-09T10:44:51+09:00 <= timestamp < 2026-09-09T12:15:00+09:00`이다. main PID `190811` 시작시각은 10:44:51이다. 원천은 `data/ai_decision_payloads/ai_decision_payloads_2026-09-09.jsonl`과 `data/ai_decision_trace/ai_decision_trace_2026-09-09.jsonl`이며, 진행 중인 전체 파일 hash를 고정 generation으로 주장하지 않는다.

### P1-A: canonical sparse 허용과 AI 분석·materialization 판정의 불일치

- Entry 실제 요청 70개 중 `fresh_dual=51`, `unusable=19`다. 19개 모두 원천 전체 상태는 `fresh_consistent`, 현재 창은 `sparse_observed_minutes`, `provider_call_allowed=true`, 현재 창 completed bar count=61이었다.
- [원천 producer](../../src/engine/scalping/entry_candle_context.py)의 관측 분봉 계약은 정상적으로 식별된 sparse 창을 합성 없이 보존한다. 하지만 [공유 AI 분석](../../src/engine/scalping/ai_decision_quality.py)의 `build_anticipatory_reversal_analysis_v1`은 현재 창 상태가 정확히 `fresh_consistent`일 때만 candle fresh로 인정한다. 따라서 원천에서 허용한 동일 19개를 전부 unusable로 바꾼다.
- 같은 파일의 canonical control 검사도 sparse 허용을 NXT/aftermarket으로만 제한한다. KRX 현재 원천 계약과의 정합성을 함께 고쳐야 하며, AI 분석 한 곳만 바꾸면 #76 학습 원천은 계속 탈락할 수 있다.
- 메모리 내 원인 격리: 19개 원본의 현재 창 상태 문자열 하나만 fresh로 대체한 진단에서 19개 모두 fresh_dual, 기존 bounded opportunity 조건 통과는 3개였다. 나머지 16개는 계속 조건 미달이다. 이는 **불일치의 영향 진단**이지 3건의 매수 승인·체결 가능성·순이익 증명이 아니다. 원본이나 정책은 수정하지 않았다.
- 개선: producer의 명시적 source 허용, exact venue/session/route, sparse provenance, 최신성·충돌·필수 현재 창 조건을 공유 predicate로 대사한다. sparse를 모두 fresh로 재라벨링하거나 누락 분봉/수익률을 합성하지 않는다. 필요한 lookback이 없는 전략 판단은 별도 미충족으로 유지한다.
- 완료: 정상 KRX/NXT sparse, 미식별 gap, stale/conflict, 필수 lookback 결손의 회귀 반례에서 runtime 분석과 #76 control 수용 이유가 일치한다. source-only 수리 검증에는 양수 EV나 실체결을 요구하지 않는다.

### P1-B: unusable → 안전 WAIT 보정이 request lineage를 삭제

- 위 19개는 원모델 DROP → `unusable_source_fail_closed_wait` 보정 → 최종 WAIT이다. 정상적인 모델 WAIT 표본이 아니다.
- [live adapter](../../src/engine/ai_engine_openai.py)의 `_normalize_decision_quality_entry_result`가 공유 보정 결과로 payload 전체를 교체한다. 공유 보정 함수는 안전 응답만 반환하므로 원래 `openai_request_id`, envelope hash, provider response receipt 등이 소실된다.
- 결과는 임의 `aidt-*` trace로 기록된다. 19개 모두 저장된 원본 요청과 payload SHA256·종목의 유일한 일치가 있지만, 원래 request ID·envelope 연결은 없고 `request_capture_status=partial`이다. 이 진단상 유일 일치를 새 runtime exact 권한으로 쓰지 않는다.
- 예: trace `aidt-79886727ca74497fa097db498d6c8d16` / 원본 request `analyze_target:048410:1788918339260:08b7af00` / payload SHA256 `f6dd446d3605a1c4e06c6bc5df317c1f35538eaca5596fc8760dd1b71b32ee14`.
- 현재 코드의 순수 함수 재현에서도 입력에 둔 request ID·envelope hash·provider_called·response ID가 모두 사라졌다. 기존 테스트는 안전 WAIT만 검사하고 이 메타데이터 보존은 검사하지 않는다.
- [trace consumer](../../src/engine/scalping/ai_decision_quality.py)의 `_final_decision_response_findings`는 19개를 `natural_control_final_response_invalid`로 판정한다. final hash는 정상이나 합법적인 `INSUFFICIENT_DATA` 상태와 경제성 학습 불가가 schema 손상으로 섞인다. trace에는 동시에 `semantic_validation_status=pass`, `outcome_label_eligible=true`가 있어 소비 단계별 이유도 다르다.
- 개선: 모델 응답과 로컬 transport/identity를 분리하고, 보정 후 원본 메타데이터를 신뢰된 로컬 경로에서 복원·보존한다. raw → repaired → runtime mapping을 구분하고 source-unusable은 원천/판단 불가 분류로 남긴다. 정상 INSUFFICIENT_DATA의 schema 수용과 경제성 입력 제외를 분리한다. 안전 WAIT와 probe 불허는 유지한다.
- 완료: 실제 위 반례와 합성 테스트에서 original request/envelope/provider receipt 및 final hash가 일관되고, 하나의 요청이 두 독립 모델 판단으로 집계되지 않는다. #82는 원천 불가를 모델 false-WAIT/false-DROP 손실로 학습하지 않아야 한다.

### P1-C: 이전 PID의 micro 적용 공백과 새 PID에서의 후속 확인

- 고정 관찰창의 저장된 최종 요청에서 Entry `analyze_target` 70개, Holding 85개 모두 reaction 필드가 없었다. Entry 중 trace와 exact request ID가 연결된 51개는 모두 V2.13이다.
- 추가로 12:18의 exact pipeline receipt에서 계산됨·전송 안 됨을 확인했다. Entry request `analyze_target:201490:1788923934112:0e436d68`, Holding request `holding_score:327260:1788923907806:caf06a64` 모두 `computed=True`, context `ok`, `payload_included=False`, `context_sent=False`, provider `response_received`였다. Holding의 내부 source-quality 소비와 모델 전달은 다르다.
- 현 작업트리의 Entry hot/Holding canonical projection 코드는 존재하고 관련 단위 테스트는 통과한다. 두 소스 파일 mtime은 10:45:45로 현재 PID 시작보다 늦다. 오래된 로드 코드 가능성을 뒷받침하지만 mtime만으로 PID 메모리 버전을 확정하지 않는다. **현재 실전 전달이 닫히지 않았다는 사실은 최종 payload와 receipt로 확인했다.**
- 개선: 기존 보완의 배포 commit/코드 hash와 다음 승인된 기동 receipt를 결속하고 실제 request JSON에서 동일 context ID/필드·provider receipt까지 확인한다. 이번 점검은 재기동 권한이 아니며 다른 세션의 기동 owner와 조정한다.
- V2.14/V2.15는 별도 `deterministic_setup_ledger_only` provider 입력을 사용한다. replay context에 micro가 있다고 최종 모델도 읽었다고 판정하면 안 된다. 필요 시 기존 setup ledger 내 유효 micro fact 투영을 별도 version/hash 검토한다. 새 미래 outcome을 live 입력에 넣지 않는다.

12:27 후속 확인: 다른 세션이 [정오 배포](./2026-09-09-midday-main-deployment-review.md)를 수행했다. 새 PID310359/12:20:56 시작을 직접 확인했으며, 이 세션이 재기동·커밋한 것이 아니다. 별도 세션의 전체 커밋에는 이 리뷰의 초기본도 포함됐다.

- `12:20:56 <= timestamp < 12:26:00`의 새 최종 요청은 Entry5/5·Holding9/9에 reaction 필드가 있다. 정상 Entry4개와 Holding9개의 pipeline receipt에서 payload 포함·sent=true·response_received를 확인했다. Entry 예는 `analyze_target:043260:1788924253240:ac180ee6`, context `5d8cc37fa16e46648b8886cadf50b1f6`이다. 같은 요청의 여러 event는 독립 요청 수로 합산하지 않는다.
- 따라서 일반 경로의 기존 projection 적용 공백은 해소 확인이다. 다만 새 Entry5개 중1개는 P1-B의 unusable 보정을 거쳐 다시 partial trace가 되고, payload 포함=true인데 sent=false/not_attempted로 기록됐다. 이는 새로운 micro 필드 누락이 아니라 기존 보정 시 transport metadata 소실의 추가 자연 반례다.
- P1-C를 별도 재구현/재기동 작업으로 유지하지 않고 잔여 오류는 P1-B로 통합한다. 모델이 필드를 실제 판단에 활용했는지와 비용 후 효과는 별도 미검증이다.

## 2. 장후 체인·비용·prompt 연구의 현재 상태

9/8 마지막 자연 generation은 다음과 같다. 서로 다른 hash 필드(파일 bytes/canonical self hash)를 혼용하지 않았다.

| 단계 | 확인 결과 |
| --- | --- |
| #77 R0–R3 | `source_only_blocked_or_deferred`, Provider 실행 0, prepared 24 / paired micro 2 / net-economic 0 |
| #82 calibration | 22:07:29, NXT 후보 1 / current parent 24 / live review-ready 0, self hash `0c780d094c60d2c16d91a2cc110d5127909b8731178c2fd18420d684ab677e57` |
| #78 optimizer | 22:07:59, 위 #82 hash 결속, self hash `8e4823403474525395be52274cc571e366515978f7a5000b17f00489f6906048` |
| #80 consumer | 22:08:01, 위 #78 hash 결속, NXT 연결 24 / KRX `hold_no_exact_entry_control`, unclassified 0 |
| 9/9 PREOPEN | `data/runtime/entry_setup_v2_14_live_policy/entry_setup_v2_14_live_policy_2026-09-09.json`: `inactive_fallback_v2_13`, runtime effect false. 실제 Entry trace도 V2.13 |

설치 cron의 20:10 main/controller 및 21:05 follower와 [follower wrapper](../../deploy/run_ai_entry_setup_paired_replay_postclose.sh)를 확인했다. 순서는 detailed → #82 → 당일 선택 고정 #78 → Provider 0 metadata rebind → holding manifest → #80이다. **분석·후속 전달은 자동화되어 있지만, consumer terminal은 새 prompt 적용 성공이 아니다.** 9/9 장후 산출물은 이 점검 시각에 아직 예정 전이다.

### 비용 companion: 소비 코드만으로 순이익 평가가 완성되지 않음

- 현재 상세 replay CLI는 exact net-label과 bridge를 읽고 request/trace/symbol/venue/session/time/payload/envelope hash를 대사하도록 구현돼 있다. #82/#78의 진단 전달도 존재한다.
- 하지만 9/8 `data/report/ai_micro_reversion_materialized_replay_requests/ai_micro_reversion_action_neutral_outcome_labels_2026-09-08.json`은 없다. #77의 paired=2와 net-economic=0의 교집합 부재 및 collector row-exclusion 상태가 명시되어 있다. label 생산의 원천 자격과 일반 base replay 표본 자격은 같지 않다.
- 우선 기존 7개 작은 기회 execution-proxy 사례 각각의 label 생산 가능 여부·탈락 source/hash를 대사한다. valid mature 경로에는 비용을 한 번만 차감한 action-neutral outcome을 결속하고, non-micro/미성숙/원천 결손에는 정확한 이유와 기존 producer owner를 남긴다. 비용 결손 24개를 0수익·기회 없음으로 처리하지 않는다.
- 같은 exact 입력으로 원모델/보정/최종 행동의 비용 후 기회 포착·오진입·미체결·tail을 비교할 준비를 한다. 그 이후 signal→submit→fill→terminal은 #119/#23와 exact attempt로 연결한다. CF net label과 실제 full/partial fill 순손익은 분리한다.

### 연구 교체와 prompt 초안: 자동 연구와 자동 배포를 구분

- 기존 보완은 단일 검증 사례로 source-only 초안을 만들며, 5 유효 source일/5 unique parent/3종목·최근 노출 0 조건에서 기존 등록 후보 내 연구 교체를 지원한다. 이 조건은 실주문·양수 EV가 필요한 조건이 아니다. 과거 자연 9/8 24개는 NXT 1일이므로 KRX 효과나 5일 완료로 사용할 수 없다.
- #78 초안은 parent/rollback hash·case ID·반례·English ASCII appendix를 포함하고 #80으로 전달된다. 그러나 `registration_status=new_version_and_hash_review_required`이며 초안 생성·전달 자체가 새 prompt 등록·평가·배포를 실행하지 않는다.
- 지금 할 일: 기존 사례에 근거한 versioned prompt 패치 검토를 기존 owner에 명시하고, 원본 hash를 바꾸지 않는 새 버전의 등록·동일 입력 비교 경로를 설계한다. 고정된 당일 선택과 기존 Provider budget을 유지한다. 유효 사례로 초안을 만드는 데 5일·노출 5건·실체결을 추가 요구하지 않는다.
- 5일 교체 조건을 즉시 제거할 증거는 현재 없다. 먼저 KRX 표본 유실과 source 불일치를 고친 뒤 유효 source일이 실제 증가하는지 확인한다. 합리적인 bounded 연구 대기와 영구 미등록·전달 단절은 다른 문제다.
- #81 legacy runtime은 OFF이고, 지원 KRX V2.14/V2.15의 기존 독립 승인·PREOPEN 경로만 참조한다. NXT/holding/미등록 버전은 이 경로의 권한을 상속하지 않는다.

## 3. 권고 실행 순서와 완료 기준

1. **P1-A+B 구현·회귀 검증:** canonical sparse 판정 공유 → 보정 메타데이터 보존 → INSUFFICIENT_DATA schema/학습 제외 분리. 변경 전 위 19개 반례를 테스트로 고정한다. 새 strategy axis를 추가하지 않는다.
2. **P1-C 중복 작업 제거:** 다른 세션의 새 PID에서 일반 micro 전달을 확인했으므로 재구현·재기동을 반복하지 않는다. 보정 경로의 sent 오분류는 P1-B에 통합하고, 정상 전달과 판단 활용·경제성 효과는 분리한다.
3. **비용·prompt 연구 연결:** 기존 7개 사례의 exact net-label 생산 자격, #82 비용/원인 진단, #78 초안 → 등록 검토 → 기존 bounded offline 평가의 intended consumer를 결속한다. 모르는 비용·성과는 null로 둔다.
4. **오늘 자연 handoff:** KRX/NXT 분리, accepted/excluded 이유·source hash, #82→#78→#80 및 기존 workorder/요약/strict verifier의 same-generation 전달을 검증한다. source-only 수리 완료, 배포, 자연 소비, 비용 후 경제성을 각각 보고한다. 장후 전체 재실행은 권고하지 않는다.

기존 실행 owner는 당일 체크리스트의 `AIDecisionActionOutcomeNaturalEvidence0908`, native workorder 전달은 `MainAIQualitySourceGapArtifactContract0909`, 실제 제출 병목/경제성은 `EntryRecheckNaturalAttribution0907`이다. 이 문서의 P1 번호는 리뷰 위치이며 새 recommendation ID나 runtime 승인이 아니다.

## 4. 최초 읽기 전용 점검의 검증과 경계 (후속 구현 전 기록)

- targeted pytest 36개 PASS(optimizer/consumer 전부 및 micro 전달 회귀), 별도 선택 5개 PASS 중 4개 중복: 고유 37개다.
- 기존 테스트가 모두 통과해도 P1-A/B는 미수정이다. 특히 기존 unusable→WAIT 테스트에는 transport identity 보존 assertion이 없어 순수 함수 재현으로 누락을 확인했다. 코드 finding 0을 주장하지 않는다.
- 수정 범위는 이 리뷰 문서와 기존 체크리스트 owner의 점검 연결이다. review-gate의 문서·owner·권한·parser 검증을 적용한다. 코드·정책·runtime artifact·Provider/broker 호출·재기동·커밋/푸시·외부 sync는 하지 않았다.
- print-only parser 36 tasks / 기존 해당 owner 1개, 문서 상대 링크 결손0, `git diff --check` PASS. 진단 집계의 임시 Counter 오류는 tuple 변환으로 재실행하여 닫았으며 원천·코드 파일 변경은 없었다.

## 5. 사용자 후속 구현 지시에 따른 보완 결과

위 §1~4는 최초 진단 당시 기록이다. 후속 구현에서는 `korstockscan-review-gate`의 producer/consumer·원천 격리·권한·회귀 검증을 적용했다. 이번 작업은 전체 장후 재실행이나 현재 매매 PID 변경이 아니다.

| 보완 | 구현과 최종 소비 계약 | 기대효과 / 한계 |
| --- | --- | --- |
| P1-A sparse 판정 | 기존 `entry_candle_context`에 관측 sparse predicate를 두고 실제 V2.13 분석과 exact control 검증이 공유한다. source=fresh, 명시적 Provider 허용, ka10080 관측행/무합성 provenance, blocker 없음이 필요하다. KRX만 일괄 제외하던 조건은 제거했다. | 고정 창의 실제 sparse 입력19/19가 새 코드에서 fresh_dual. 없는 lookback은 null이며 stale quote·불명확 결손은 계속 제외한다. BUY·submit·수익19건이 아니다. |
| P1-B safe WAIT·identity | 전체 응답 안전 보정 후에도 원래 request/envelope/Provider receipt를 보존한다. INSUFFICIENT_DATA는 WAIT·up/down null·probe 비활성인 유효 응답으로 검증하되 경제성 control에서는 명시적으로 제외한다. | 원모델 DROP→안전 WAIT와 정상 모델 WAIT를 구분하고 partial trace/sent 오분류를 방지한다. 과거 aidt 행을 exact로 소급 변경하지 않는다. |
| 비용 생산 자격 | 상세 CLI가 label 유무와 독립적으로 bridge를 읽는다. 전체 원천 commitment와 exact trace/종목/시장/세션/시각/payload/envelope를 검증한 후 기존 label-ready/current-ablation 판정 함수를 그대로 사용한다. | label 결손을 비용0·순수익0으로 해석하지 않는다. parent 중복제거 flag들을 새 결합 gate로 만들지 않는다. |
| #82→#78→#80/#91 | 사례별 비용/null·기존 producer 자격/탈락 사유가 calibration과 초안에 남는다. #78이 native recommendation ID를 발급하고 #80과 #91은 동일 calibration/date/hash·초안 재구성·권한을 검증한다. #91 v7은 ID·원본 결정·초안 본문·반례·비용·source hash를 보존한다. | 초안이 보고서 안에만 머무르지 않고 기존 source-only 구현/review intake에 도달한다. 임의 새 버전 등록, Provider 호출, 실전 prompt 적용 권한은 생기지 않는다. |

### 실제 비용 사례 7건 대사 (9/8 보존 원천, 메모리상 검증)

24/24 요청을 저장된 exact payload와 기존 bridge self hash `c1f3a608064cc73ca34738dc0fccb713cef64dab8dbb421eaeeeda31b9de929b`에 결속했다. 작은 기회 execution-proxy 사례7건의 검증된 비용 label은 여전히0이며 다음의 원천 사유가 있다.

| 요청 / 사례 | 기존 생산자 판정 |
| --- | --- |
| `010950:1788855416473:191757e0`, `010950:1788855432491:18a70c23` (각 `analyze_target:` prefix) | sidecar는 유효하지만 `bridge_primary_horizon_not_mature`. 요구된10초 창의 비용 경로가 없다. 두 사례 모두1초만 mature이며 이를10초 경제성으로 전용하지 않는다. |
| `000720:1788860203884:815d576e`, `052690:1788861602227:80dd6417`, `052690:1788861606148:58d52e33`, `052690:1788862740885:e902eef5` | `not_applicable_no_shock_event`; 현재 micro timestamp 계약이 성립하지 않는다. 일반 base prompt 표본으로는 유지한다. |
| `000720:1788860385029:c1f7933e` | `source_unavailable_no_sidecar`, current timestamp invalid. quantity/execution basis/liquidity/source-quality 결손도 함께 보존한다. |

7건 모두 `producer_materializable=false`, 비용 후 수익/target-first는 null이다. 원천 없는 과거 결과를 반복 재생성하지 않고 기존 `MainAIMicroExactEconomicIntersectionRepair`와 현재 일일 자연 evidence owner로 전달한다. 실제 full/partial fill·terminal 순손익은 별도다.

### 조건·자동화 최종 판정

- 불합리한 조건으로 입증된 KRX sparse 일괄 제외는 제거했다. 반면 각 lookback, 정확한 시각/시장/세션, 요구 청산창의 비용 증거와 실주문 안전조건은 유지한다. 10초 자료가 없는데1초 결과로 대체하는 것은 허들 개선이 아니다.
- 단일 사례의 source-only prompt 초안/리뷰 전달은 실체결·양수 EV·5일을 기다리지 않는다. 최근 유효5 source일/5 parent/3종목은 기존 등록 후보의 무참여 연구 교체 조건으로만 유지하며 live gate가 아니다. 현재1일의 NXT 표본만으로 이를 과도하다고 판정하거나 KRX에 전용하지 않는다.
- 기존20:10 main과21:05 follower의 상세→#82→당일 선택 고정 #78→metadata rebind→#79/#80을 유지한다. #91은 새 optimizer를 source fingerprint에 포함하고 기존 요약/strict verifier·controller의 source-drift 복구 대상이 된다. 새 cron/Provider budget/매매 owner는 만들지 않았다.
- 디스크의 코드 수정은 현재 장기 실행 PID 적용 증거가 아니다. 후속 Python 작업은 새 코드로 실행되지만, live adapter는 승인된 정상 기동과 원래 request ID·sent receipt의 자연 확인이 필요하다. 이 세션은 재기동·live env/lock/threshold 변경·Provider/broker 호출·canonical report 재생성·커밋/푸시를 하지 않았다.
- 새 초안의 버전 등록과 실제 bounded 비교는 기존 source-only review workorder가 소유한다. 지원 KRX V2.14/V2.15 승격·PREOPEN/PID와 #81 legacy OFF는 그대로다. “초안 전달 자동화”를 “새 prompt 자동 실전 배포”로 보고하지 않는다.

최종 검증: #80 exact 초안 소비/손상 격리, #91 실제 builder의 native ID·본문·비용 전달 및 원문 무변형/손상 원천의 repair 분기를 보완한 뒤 **13개 관련 모듈의 pytest 1,124개 PASS**. Python compile, `git diff --check`, print-only parser 36 tasks/기존 AI owner1개 PASS. 신규 문서 링크 결손0이며 전체 링크 검사에서 남은5개는 기존 체크리스트가 가리키는 오늘 장후 예정 artifact로 `not_yet_due`다. 이 수리 범위의 재리뷰에서 미해결 P0~P2 코드 finding0이다. Provider/broker 호출·실시간 적용·새 prompt 경제성 검증은 수행하지 않았다. 기존 사용자/다른 세션의 산출물·문서는 보존한다. 코드 종결, 배포, 자연 표본/소비와 비용 후 수익 acceptance를 혼동하지 않는다.
