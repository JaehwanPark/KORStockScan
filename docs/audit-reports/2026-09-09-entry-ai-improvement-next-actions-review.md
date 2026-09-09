# Entry AI #76/#77/#82 → #78 → #80 다음 개선작업 점검

작성일: 2026-09-09 KST. 읽기 전용 점검이며 코드 구현·배포·장후 재생성 지시를 실행하지 않았다.

## 판정

**추가 보완 필요. 지금 우선할 작업은 sparse 원천 판정 정합성, 안전 보정 시 exact request 보존, 기존 micro 입력 보완의 실제 PID 소비 확인이다.** 비용 label과 versioned prompt 연구의 후속 연결도 필요하지만, 이들을 실주문 허가나 수익 실현으로 해석하지 않는다.

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

### P1-C: 기존 micro 보완 코드와 현재 실제 요청 사이의 적용 공백

- 고정 관찰창의 저장된 최종 요청에서 Entry `analyze_target` 70개, Holding 85개 모두 reaction 필드가 없었다. Entry 중 trace와 exact request ID가 연결된 51개는 모두 V2.13이다.
- 추가로 12:18의 exact pipeline receipt에서 계산됨·전송 안 됨을 확인했다. Entry request `analyze_target:201490:1788923934112:0e436d68`, Holding request `holding_score:327260:1788923907806:caf06a64` 모두 `computed=True`, context `ok`, `payload_included=False`, `context_sent=False`, provider `response_received`였다. Holding의 내부 source-quality 소비와 모델 전달은 다르다.
- 현 작업트리의 Entry hot/Holding canonical projection 코드는 존재하고 관련 단위 테스트는 통과한다. 두 소스 파일 mtime은 10:45:45로 현재 PID 시작보다 늦다. 오래된 로드 코드 가능성을 뒷받침하지만 mtime만으로 PID 메모리 버전을 확정하지 않는다. **현재 실전 전달이 닫히지 않았다는 사실은 최종 payload와 receipt로 확인했다.**
- 개선: 기존 보완의 배포 commit/코드 hash와 다음 승인된 기동 receipt를 결속하고 실제 request JSON에서 동일 context ID/필드·provider receipt까지 확인한다. 이번 점검은 재기동 권한이 아니며 다른 세션의 기동 owner와 조정한다.
- V2.14/V2.15는 별도 `deterministic_setup_ledger_only` provider 입력을 사용한다. replay context에 micro가 있다고 최종 모델도 읽었다고 판정하면 안 된다. 필요 시 기존 setup ledger 내 유효 micro fact 투영을 별도 version/hash 검토한다. 새 미래 outcome을 live 입력에 넣지 않는다.

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
2. **P1-C 배포 수용 확인:** 기존 micro projection 코드와 실제 PID/request의 차이를 닫는다. code review → 승인된 기동 owner → 실제 provider payload receipt 순서다. 단위 테스트 성공만으로 배포 완료 처리하지 않는다.
3. **비용·prompt 연구 연결:** 기존 7개 사례의 exact net-label 생산 자격, #82 비용/원인 진단, #78 초안 → 등록 검토 → 기존 bounded offline 평가의 intended consumer를 결속한다. 모르는 비용·성과는 null로 둔다.
4. **오늘 자연 handoff:** KRX/NXT 분리, accepted/excluded 이유·source hash, #82→#78→#80 및 기존 workorder/요약/strict verifier의 same-generation 전달을 검증한다. source-only 수리 완료, 배포, 자연 소비, 비용 후 경제성을 각각 보고한다. 장후 전체 재실행은 권고하지 않는다.

기존 실행 owner는 당일 체크리스트의 `AIDecisionActionOutcomeNaturalEvidence0908`, native workorder 전달은 `MainAIQualitySourceGapArtifactContract0909`, 실제 제출 병목/경제성은 `EntryRecheckNaturalAttribution0907`이다. 이 문서의 P1 번호는 리뷰 위치이며 새 recommendation ID나 runtime 승인이 아니다.

## 4. 검증과 경계

- targeted pytest 36개 PASS(optimizer/consumer 전부 및 micro 전달 회귀), 별도 선택 5개 PASS 중 4개 중복: 고유 37개다.
- 기존 테스트가 모두 통과해도 P1-A/B는 미수정이다. 특히 기존 unusable→WAIT 테스트에는 transport identity 보존 assertion이 없어 순수 함수 재현으로 누락을 확인했다. 코드 finding 0을 주장하지 않는다.
- 수정 범위는 이 리뷰 문서와 기존 체크리스트 owner의 점검 연결이다. review-gate의 문서·owner·권한·parser 검증을 적용한다. 코드·정책·runtime artifact·Provider/broker 호출·재기동·커밋/푸시·외부 sync는 하지 않았다.
