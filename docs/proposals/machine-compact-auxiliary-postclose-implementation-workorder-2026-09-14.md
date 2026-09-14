# 기계 진입·축약형 AI 보조심사 장후 전환 통합 작업지시서

작성: 2026-09-14 KST. 상태: **구현 계획**. 이 문서는 새 구현·자연 실행·배포 성공 receipt가 아니다.

설계 owner: [기존 통합 설계 §22·§23](entry-prompt-balanced-adjudication-design-review-plan-2026-09-13.md#22-보조심사-전용-축약형-직접-전환과-장후작업-변경계획).
실행 추적 owner: [9/14 체크리스트](../checklists/2026-09-14-stage2-todo-checklist.md)의 `CodeImprovementWorkorderReview0914`와 해당 원천/정책 자연 acceptance owner. 다음 날짜로 이관할 때 같은 ID·이력을 보존한다.

## 1. 일괄 실행 지시

다음 문장으로 본 지시서 전체를 실행하도록 요청할 수 있다.

> 이 통합 작업지시서의 WP0~WP7 및 통합 종결을 일괄 실행하라. 작업은 의존 순서에 따라 분할하고, 각 작업에서 구현→코드리뷰→finding 보완→재리뷰→targeted validation을 반복하라. 독립 작업의 구현은 분리할 수 있지만 source generation과 파일 소유권을 고정하고 공유 consumer의 변경은 통합 검증하라. 검증된 부분과 잔여를 기록하고 단순 목록 제시로 종료하지 마라. 사용자별 승인 단계를 새로 추가하지 말고 기존 장후 자동 선정→다음 거래일 정책 발행→PREOPEN→PID 소비로 연결하라. 완료 후 승인된 범위의 커밋·푸시·배포를 수행하고, 재기동이 필요한 경우에만 현재 실행·정책·주문/custody 보존 계약을 확인해 수행하라. 구현 완료, 자연 소비, 경제성은 각각 보고하라.

지시서 작성·열람·리뷰만 요청받은 경우 위 실행 문구는 발동하지 않는다. WP 번호는 설계상 작업 단위이며 producer native recommendation ID나 새로운 checklist ID가 아니다. 자동 선정은 검증된 등록 compact 변형 안에서 수행한다. 자유형 prompt 생성물의 무검증 live 등록, provider/model 변경, 기계 threshold·수량·주문·hard safety 변경은 이 작업의 기본 범위가 아니다.

## 2. 목표와 기존 완료 범위

목표는 기계가 선정한 현재 ENTER 지점에서 AI가 물질적 위험을 심사하고, 그 품질을 장후에서 계속 평가·보완해 **비용을 차감한 작은 순익의 반복 기회와 누적 순익**을 개선하는 것이다. PASS 수·승률·gross 상승률을 목표의 대용으로 삼지 않는다.

기존 완료 범위는 재구축하지 않는다.

- compact v3의 PASS adverse 인용·bounded VETO positive 인용, 기존 frozen v1/v2·변형 bytes/hash 보존, 다음 거래일 semantic migration.
- 기계 원천 capture, machine-primary BUY funnel, 자연 source 감사와 #76/#82 연결의 기존 구현.
- compact registry 변형 자동 선택과 기존 publisher/PREOPEN/loader 경로. 개별 사용자 승인 단계는 추가하지 않는다.
- 기존 runtime/PID가 어느 정책을 소비했는지는 실행 시작 시 다시 확인한다. `7f88c35c`는 코드 검증 기준점이지 미래의 고정 배포 기대값이 아니다.

현재 코드에서 확인한 결손과 추가 확인 과제를 구분한다.

| 영역 | 식별 근거 | 작업 성격 |
| --- | --- | --- |
| #82 | `screened_enter_now_count`가 compact outcome 전체 합이며 오류 건수 차이로 선정 | 평가 분모·경제성 계약 수정 |
| #78/replay | `ENTRY_CANDIDATE_ORDER`와 batch 기본 후보가 기존 V2.14/15/16 | compact 평가 경로 전환 |
| #80 | 기존 optimizer 후보/hash registry 중심 소비 | compact 계약과 end-to-end 결속 보완 |
| #11/#74 | 한 compact 버전만 있을 때 measurement 허용 | 정상 다세대·scope 격리 개선 및 자연 전수 대사 |
| #76/#77/#119/#23/요약 | 일부 기계 경로는 구현됨 | 직접 소비 누락을 입증한 부분만 최소 보완 |

## 3. 분할 실행·의존 관계

| 단위 | 산출물 | 선행 | 코드 수정 책임 |
| --- | --- | --- | --- |
| WP0 | 현재 계약·원천 census·변경 파일 책임표 | 없음 | 통합 담당 |
| WP1 | #11/#74·#76 partition별 원천 계약 | WP0 | source 감사·materialization |
| WP2 | #82 경제적 평가·자동 선정 계약 | WP1 계약 고정 | calibration·publisher |
| WP3 | #77·#78·21:05 compact 평가 계약 | WP1 계약 고정 | 연구·optimizer·replay |
| WP4 | #80·verifier·정책 전달 검증 | WP2, WP3 | consumer·검증기 |
| WP5 | #119→#23 machine 경로 자연 연결 | WP1 | funnel·recheck |
| WP6 | EV/workorder/tower/checklist/strict 전수 요약 | WP2~WP5 | 요약·handoff |
| WP7 | 통합 검증·최소 재생성·배포·자연 acceptance | WP1~WP6 코드 통과 | 통합 담당 |

WP2/WP3/WP5는 공유 schema가 고정되면 독립 개발할 수 있다. 같은 파일은 한 시점에 한 작업만 편집한다. 특히 `ai_action_outcome_calibration.py`와 공통 prompt registry의 최종 소유자를 WP0에서 지정한다. 다중 agent 사용은 필수가 아니다. 이 표는 개발 순서이며 cron/systemd/실행 중 wrapper의 producer 순서를 바꾸지 않는다.

각 분할 기록에 `WP, base commit, 변경 파일, source date/hash, contract version, state, findings, tests, direct consumer, 잔여, 다음 작업`을 남긴다. 상태는 `planned/implementing/reviewing/validated/blocked/integrated`로 사용하며 blocked를 완료로 세지 않는다. 날짜·slot의 실행 owner는 체크리스트 한 곳에 둔다.

## 4. WP0 — 현재 상태·원천·계약 고정

1. Plan Rebase §1~§8, 현재 KST 체크리스트의 목적·강제 규칙과 관련 OPEN, review skill을 읽는다. worktree·원격 commit·selected release·실제 PID·당일 policy를 대사한다.
2. source 거래일과 as-of를 분리한다. 예약 전 보고서 부재는 실패가 아니다. 실행 중인 wrapper snapshot·PID·lock과 artifact 변경 여부를 확인한 뒤 개발/재생성 범위를 정한다.
3. #11/#74, #76 materialized rows, #77 결과, #82, #78, replay batch, #80, #119/#23, bundle/activation, 최종 요약의 path/date/schema/hash/mtime/status를 읽기 전용 목록으로 고정한다.
4. 계약은 `기계 전체 평가 → ENTER → AI 호출 → 의미 유효 심사 → outcome 평가 가능 → 실행/실제 비용`으로 나눈다. 각 stage의 행 수와 최초 결손을 기록한다.
5. 설치된 producer→consumer 및 CLI/flag를 확인하고 아래 계획의 명칭과 실제 경로가 다르면 계약을 먼저 수정한다. 오래된 문서의 단계 번호만으로 새 작업을 실행하지 않는다.

완료조건: 코드로 입증된 결손/자연 확인 과제/정상 OFF·valid-empty가 분류되고, 수정 파일과 최종 consumer·검사 명령이 확정된다. source가 없으면 없는 이유를 기록하며 과거 raw를 합성하지 않는다.

## 5. WP1 — #11/#74·#76 전수 원천 소비

주 파일: `src/engine/observation_source_quality_audit.py`, `src/engine/scalping/ai_decision_quality.py`, `src/engine/scalping/ai_action_outcome_calibration.py`의 원천 로딩 부분. 마지막 consumer는 WP2/WP3다.

### 입력·분모 계약

- stable key는 기존 evaluation/attempt ID와 source-date·owner·venue/session을 사용한다. prompt version/hash/variant, machine bundle hash와 snapshot/micro provenance는 검증 binding이다. 같은 attempt의 상충 binding을 서로 다른 정상 행으로 분리하지 않는다.
- `machine_total = valid_ENTER + valid_RECHECK + valid_BLOCK + excluded_identity_or_source`를 성립시킨다. 정상 AI 미호출, 호출 예정/진행, transport 실패, schema 실패, 의미 실패, 유효 심사를 별도 상태로 둔다.
- 유효 심사 분모는 `PASS+VETO+CAUTION+INSUFFICIENT`; outcome은 `evaluable/pending_maturity/censored/irrecoverable_gap`으로 분리한다. transport/schema 오류가 모델의 올바른 위험 차단으로 집계되면 안 된다.
- 정상 partition은 `owner × venue/session × prompt version/hash × machine policy generation`으로 격리한다. 여러 정상 버전이 있다는 이유만으로 전체 일자를 차단하지 않는다. 같은 버전의 알 수 없는 hash·source 충돌은 해당 partition/행을 격리하고, 안정적인 격리가 불가능할 때만 전체 차단한다.
- actual signal·machine action/reason·hierarchy selection·micro 창·AI trace·후행 outcome을 exact key로 연결한다. raw 이벤트 수, AI 재시도 수, unique 평가 수를 혼합하지 않는다.
- per-partition receipt와 전체 보존식을 기존 artifact에 추가한다. schema 변화는 구 reader/새 writer·명시적 검증 오류를 갖추며 구 receipt를 새 계약으로 재라벨링하지 않는다.

### 검증·완료조건

오늘 이용 가능한 natural 원천을 전수 대사한다. compact 미관측이면 `not_observed`이며 legacy 원천을 compact 성과로 전환하지 않는다. 한 정상 partition+한 손상 partition, 두 정상 compact 버전, AI 미호출 RECHECK/BLOCK, 중복 retry, source 파일 중간 교체, unknown hash, micro 결손을 테스트한다. 필수 미분류 0, 보존식 일치, #76/#82의 동일 source manifest 소비까지 확인한다. 신규 collector·서비스·DB를 기본 해법으로 만들지 않는다.

## 6. WP2 — #82 비용 후 평가·자동 선정 보완

주 파일: `scalping/ai_action_outcome_calibration.py`, `scalping/mechanistic_entry_runtime_policy.py`. 원천은 WP1 receipt이며 최종 소비자는 next-date publisher다.

### 분모·경제성

1. `screened_total`은 운영 호출 진단으로 보존하고, `semantic_valid_count`, `outcome_evaluable_count`, `economic_eligible_count`, 제외 사유별 count를 새 계약으로 명확히 구분한다. 정책 선정 sample floor는 해당 정책이 요구하는 평가 가능 분모를 사용한다.
2. 같은 기계 ENTER 지점에서 correct PASS, dangerous PASS, correct VETO, missed-profit VETO, CAUTION 후 재확인/기회소실, INSUFFICIENT 원천 결손을 분류한다. 정상 무노출과 미체결·HELD·결측을 구분한다.
3. `missed_veto_rate = missed_profit_veto / evaluable_veto`, `dangerous_pass_rate = dangerous_pass / evaluable_pass`로 보고하며 분모 0은 null이다. 두 rate의 의미와 모집단이 다르므로 단순 차이를 EV로 사용하지 않는다.
4. 실행 가능한 action-neutral 경로의 비용 차감 수익·손실, target/adverse 순서·정해진 horizon, latency/체결 가능성·자본점유를 사용한다. 실제 broker full-fill/terminal/cost 결과는 별도 지표로 유지한다. CF 차단 손실/놓친 순익을 실제 실현손익에 합산하지 않는다.
5. 동일 eligible 기회 집합에서 현재 심사에 따른 `screened_opportunity_net_ev`와 평가 가능한 노출/미노출 비율을 계산한다. 미노출의 기회 수익은 CF이며, 명시적 무노출 행동의 현금흐름 0과 결측 수익 null을 구별한다. 희소한 큰 손실이 여러 작은 이익 건수로 가려지지 않게 tail·손실 크기를 함께 보고한다.

### 자동 선정 계약 확정

기존 20건/10% 건수 차이는 기존 버전의 기록으로 남기고 신규 경제적 선택의 유일한 기준으로 쓰지 않는다. WP2 구현자는 아래 gate 표를 **코드 상수/정책 schema·근거·테스트까지 확정**한 뒤 작업을 닫는다. 숫자를 미정으로 남기거나 테스트를 맞추기 위해 floor를 낮추지 않는다.

| Gate | 확정해야 할 내용 | 과도한 조건 방지 |
| --- | --- | --- |
| source | WP1의 해당 partition 유효성·동결 원천 hash | 관계없는 partition 오류로 전체 차단 금지 |
| sample/window | 기존 평가창 안 unique 경제적 유효 표본·PASS/VETO별 적용 가능한 분모·rolling/버전 창 | 모든 horizon·5/10/20일 동시 조건을 관성적으로 추가하지 않음 |
| objective | 비용 후 기회 EV·참여·작은 순익 빈도·tail의 단위/식/우선순위 | PASS quota·단순 오류 건수로 선정 금지 |
| successor | 등록 변형의 근거와 incumbent 대비 판정, 충분한 증거가 없는 경우 carry | 후보 적용 전 후보의 실체결을 선행 요구하지 않음 |
| stability | 같은 source 재실행 멱등, 동일 날짜 선택/freeze, 왕복 변경·창 만료 처리 | 무기한 정지·추가 사용자 승인 금지 |
| rollback | 충분한 post-apply 악화와 source 부재를 구분하고 다음 날짜 처리 | 결측을 0 EV·측정 악화로 간주하지 않음 |

초기 compact 전환/인용 수리는 별도 완료 범위이며 대조군·경제성 gate를 새로 부과하지 않는다. 지속적인 변형 평가는 기존 incumbent/등록 변형·recorded outcome을 이용한다. 새 장기 live 대조군 실험을 자동 추가하지 않는다. 새 후보에 대한 비교 근거가 없다면 자연 오류의 방향은 연구 추천이고 검증된 개선량은 아니다. 현행 정책 carry와 필요한 근거를 명시한다.

`automatic_successor_selection`은 contract version, exact incumbent/candidate, partition, source/economic hashes, denominator/exclusion, metrics, bounds, direction/reason, effective-date, runtime authority를 담는다. publisher는 aggregate만 신뢰하지 않고 원천 receipt/선정 보존식·등록 prompt hash·같은 scope·동일 stage를 독립 검증한다. 일별 guard 통과 결과는 자동 발행하며 수동 승인 대기열을 만들지 않는다.

필수 반례: 20호출 중 경제적 유효2건, 모든 VETO/모든 PASS, 큰 손실1건과 작은 이익 다수, 미성숙 다수, 비용 누락, 같은 버전·다른 machine policy, stale incumbent, 중복/상충 attempt, 기존 버전 결과만 있는 날, source 재실행. 인용 수리 migration과 성과 선정 gate를 별도로 테스트한다.

## 7. WP3 — #77·#78·21:05 평가 역할 전환

주 파일: `scalping/ai_decision_quality.py`, `scalping/micro_reversion/main_ai_prompt_optimizer.py`, `scalping/entry_setup_paired_replay_batch.py`, 관련 기존 R0–R3 owner. WP0에서 실제 wrapper/CLI를 확인한다.

- 기계 평가 집합은 ENTER/RECHECK/BLOCK 전체다. 보조 AI 평가 집합은 당시 기계 ENTER와 정확히 결속된 호출만이다. AI 미호출을 Provider 실패나 AI veto로 변환하지 않는다.
- compact 전환 전 legacy cohort는 해당 과거 prompt/역할로 격리한다. compact cohort의 기본 후보는 등록된 compact 세대에서 선택하며 V2.14/15/16 independent-selector 연구를 현재 compact의 기본 개선으로 선정하지 않는다. holding/exit owner는 그대로 유지한다.
- 실제 runtime의 versioned system prompt + provider-visible 입력 + 응답 schema + 기계 context/bundle을 공통 builder에서 재사용한다. compact에 기존 optimizer base prompt나 과거 승률 설명을 덧붙이지 않는다. system/wrapper/schema/input의 hash를 각각 남기고 runtime/replay parity를 검증한다.
- exact replay 원장에는 full provenance를 보존한다. provider 입력의 metadata 축소가 필요하면 explicit projection version·필수 fact 보존·source hash와 transmitted hash 분리를 먼저 구현한다. 미래 outcome·당일 종료 후 분석값을 request input으로 보내지 않는다.
- #77은 기계 선정 품질·AI 차단 품질·최종 실행 품질을 별도 R1/R2/R3 section과 native handoff로 전달한다. #78은 WP2 경제적 평가와 같은 표본/비용 계약을 소비하고 #80에 실행한 후보 및 carry 이유를 발급한다.
- 기존 21:05 bounded lock/checkpoint/budget/timeout/terminal 계약을 유지한다. 정상 완료 request를 다시 호출하지 않으며 prompt/schema/input hash 변경 시 과거 checkpoint를 동일 요청 성공으로 재사용하지 않는다. provider 미실행 모드는 명시적 deferred/metadata 상태로 보존한다.
- 최초 compact migration을 replay 완료의 선행 조건으로 만들지 않는다. 이미 수행된 frozen batch의 prompt를 중간 교체하지 않으며 새 계약은 다음 실행 generation부터 사용한다.

완료조건: compact ENTER fixture의 runtime/replay 최종 prompt·input/schema parity, legacy/holding 격리, CAUTION/INSUFFICIENT/transport/schema taxonomy, full census·bounded selection·resume 검증 통과. natural compact 부재 시 등록/원천 결손과 정상 미관측을 구분하고 Provider 호출로 표본을 합성하지 않는다.

## 8. WP4 — #80·verifier·자동 정책 consumer

주 파일: `scalping/main_ai_prompt_consumer.py`, `verify_threshold_cycle_postclose_chain.py`, `scalping/entry_setup_live_policy.py`, `scalping/mechanistic_entry_runtime_policy.py`.

1. consumer가 compact registry·schema와 실제 실행 후보/원천 hash를 검증하도록 확장한다. legacy optimizer의 성공 metadata가 compact 소비 성공을 대신하지 않게 한다.
2. `source→calibration→optimizer/replay→consumer` 연구 receipt와 `calibration selection→bundle→PREOPEN→PID` 적용 receipt를 연결하되 의존 순환을 만들지 않는다. 21:05 결과가 기존 늦은 요약을 갱신하는 실제 owner/순서는 WP0 계약을 따른다.
3. verifier는 partition/분모 보존, eligible selection provenance, version/hash, 후보/carry reason, 미래 날짜 정책과 당일 frozen 불변을 확인한다. compact 미관측/유효 후보0은 명시적 정상 carry이고 필수 source 누락은 실패다.
4. policy가 발행됐어도 현재 PID 소비는 따로 검증한다. 정상 exact-date 자동 loader에 개별 사용자 승인이나 불필요한 재기동을 추가하지 않는다.

필수 테스트: source hash 변조, 잘못된 scope/version/schema, 실행 후보와 optimizer 재선정 불일치, companion 부재·잘못된 날짜, provider0 metadata만 존재, 기존 frozen policy 유지, 성공 exit지만 필수 receipt 누락. 마지막 strict가 실패하면 이전 PASS로 완료하지 않는다.

## 9. WP5 — #119 BUY funnel→#23 recheck

주 파일: `buy_funnel_sentinel.py`, `scalping/entry_recheck_drought_controller.py`와 직접 source consumer.

- 기존 `machine_primary_entry_funnel_v1`을 재사용해 평가→기계 ENTER→AI 호출/PASS/VETO→final guard→broker accepted submit을 전수 대사한다. schema·계수·이벤트의 같은 attempt/scope binding을 확인한다.
- 기계 RECHECK/BLOCK, AI VETO, transport/schema·semantic 실패, latency/price/authority/broker 차단의 최초 원인을 분리한다. 뒤에서 회복된 일시 veto는 terminal 차단에 중복 집계하지 않는다.
- legacy recheck와 machine recheck의 owner를 유지한다. machine lane을 legacy controller에 억지로 eligible로 만들지 않는다. #23이 소비하지 않는 진단이라면 실제 다음 owner/native workorder를 지정한다.
- 주된 차단의 경보·후속은 #82의 기계 정책/AI 보조 품질 분모와 일치해야 한다. AI 미호출 전체를 AI 성과 분모에 넣지 않는다.
- 최신 generation에서 이미 계약이 닫혔다면 code patch 없이 `already_implemented_verified`로 종결한다. 실제 drought 해소는 scope별 accepted submit·후속 비용/terminal 관측으로 따로 판정한다.

테스트: machine ENTER+VETO, ENTER+PASS+price block, RECHECK+AI 없음, PASS+broker reject, recovered intermediate veto, duplicate events, legacy/machine 혼합, accepted submit과 fill 구분.

## 10. WP6 — 요약·native workorder·strict 전수 전달

주 파일: `runtime_approval_summary.py`, `runtime_apply_gap_audit.py`, `build_code_improvement_workorder.py`, `automation/tuning_performance_control_tower.py`, 기존 EV/checklist builder와 strict verifier.

요약에 다음 상태를 각각 전달한다: 기계 선정 성과, AI 보조심사 성과, source/transport/semantic 결손, compact semantic migration, 경제적 successor 선정/carry, bundle 발행, PREOPEN 선택, 현재 PID first-use, 실제 비용 후 성과. 소비하지 않은 compact·legacy 결과가 같은 headline으로 합산되지 않아야 한다.

각 native workorder는 owner/stage/ID·source generation·권한·consumer·acceptance를 보존한다. WP 번호나 arm 이름을 native 구현 ID로 만들지 않는다. 같은 ID의 projection·별도 승인 이력을 추가 고유 작업으로 세지 않는다. 기존 최종 `EV/workorder→runtime summary/gap/lineage→tower→checklist→strict`의 source-generation contract를 유지한다.

완료조건: selected/non-selected 추천의 전수 보존식, 작업 누락0, body/source hash 검증, 마지막 strict PASS와 controller terminal. 운영 terminal·코드 fixed-point·배포·경제성을 따로 표시한다. 미래 정책/PID가 아직 도래하지 않으면 예정/잔여로 남긴다.

## 11. WP7 — 통합 검증·최소 재생성·배포

1. WP1~WP6의 최신 코드와 contract version을 고정하고 source→최종 consumer 통합 리뷰를 수행한다. 영향을 받지 않은 완료 영역은 재개하지 않는다.
2. 아래 targeted suite와 Python compile, shell 변경 시 `bash -n`/wrapper 계약, 항상 `git diff --check`를 수행한다. 문서는 링크·owner·권한·print-only parser를 검증한다.
3. 재생성 전 old path/hash/status를 보존하고, PID/lock·retry 상태를 확인한다. 실행 중·예약 전 producer를 중복/조기 실행하지 않는다. 검증된 실제 producer CLI로 영향 최초 단계부터 필요한 downstream까지만 실행한다.
4. 성공한 source나 Provider 결과를 비용 없이 재사용할 수 있는 기존 checkpoint만 사용한다. 원천이 없는 과거 ingress/identity gap에 동일 replay를 반복하지 않는다. 대상일을 자정 이후에도 유지한다.
5. 정책 발행이 다른 machine threshold나 holding 정책도 바꾸는지 diff를 검토한다. 이번 권한 밖 변화가 생기면 해당 owner의 기존 자동 계약을 확인하고 분리한다. 수동 env로 자동화 결손을 우회하지 않는다.
6. 코드·문서만 선별 커밋/푸시하고 사용자/운영 생성 변경을 보존한다. 선택 release와 커밋·실제 파일 hash·shared path·설치 라우팅을 검증한다. 현재 PID가 다른 코드/정책을 쓸 경우 정확히 보고한다.
7. 재기동 필요성이 입증된 경우 기존 승인과 runbook에 따라 현재 미체결·잔고/custody·정책·정상 종료/새 PID·WS·first-use receipt를 검증한다. 미래 정책만 바뀌는 경우 기존 다음 기동 owner를 사용한다.

### 관련 검증 파일

| 단위 | 기존 pytest 대상 (`src/tests/`) |
| --- | --- |
| WP1 | `test_observation_source_quality_audit.py`, `test_ai_decision_quality.py`, `test_ai_action_outcome_calibration.py` |
| WP2 | `test_ai_action_outcome_calibration.py`, `test_mechanistic_entry_runtime_policy.py`, `test_entry_setup_live_policy.py` |
| WP3 | `test_ai_engine_openai_transport.py`, `test_entry_setup_evidence.py`, `test_main_ai_prompt_optimizer.py`, `test_entry_setup_paired_replay_batch.py`, `test_ai_decision_quality.py` |
| WP4 | `test_main_ai_prompt_consumer.py`, `test_verify_threshold_cycle_postclose_chain.py`, `test_entry_setup_live_policy.py` |
| WP5 | `test_buy_funnel_sentinel.py`, `test_entry_recheck_drought_controller.py` |
| WP6 | `test_runtime_approval_summary.py`, `test_runtime_apply_gap_audit.py`, `test_build_code_improvement_workorder.py`, `test_tuning_performance_control_tower.py`, strict verifier tests |
| WP7 | 변경 의존성에 따른 위 통합 subset, 실제 wrapper/router tests |

새 테스트·module을 추가할 경우 AGENTS의 location gate를 먼저 적용한다. 기존 role package 안에서 보완하고 `src/engine` root에 새 producer를 추가하지 않는다.

## 12. 리뷰 반복과 재개 가능한 종료조건

내부 runtime prompt는 English ASCII, 사용자 보고는 한국어로 작성한다. 각 WP에서 다음 루프를 생략하지 않는다.

`반례/직접 원인 확정 → 최소 구현 → producer/consumer 리뷰 → finding 수정 → 재리뷰 → targeted validation → WP receipt → 다음 WP`

- finding별 severity, file/line, 재현 입력, 실제 영향, 수정, 회귀 테스트를 기록한다. P0~P2 미해결이 있으면 해당 WP를 validated로 표시하지 않는다.
- 정상 사례, 빈 입력, 결손/오래된 입력, 중복/경합, 날짜·scope 경계, authority leak을 검토한다. 테스트 PASS만으로 자연 경제성을 완료하지 않는다.
- 다음 WP에서 공유 계약의 새 결함을 발견하면 영향받는 선행 WP만 다시 열어 같은 루프를 수행한다. 전체 초기화나 무관한 suite의 무제한 반복은 하지 않는다.
- source 재생성 후 새 eligible recommendation/decision 변경이 있으면 stable ID로 재intake하고 허용된 수리를 반복한다. 근거 부족·외부 의존성·권한 밖 항목은 owner/필요 근거/다음 확인 조건을 명시한다.
- 분할 실행 중단 시 마지막 validated commit, artifact generation, 실행 중 PID/lock, 잔여 WP·finding·재개 명령을 남긴다. 다음 실행은 근거 변화를 확인하고 미완료 부분부터 재개한다.

코드 통합 완료조건: eligible actionable open 0, 미분류 native recommendation 0, review P0~P2 finding 0, targeted checks PASS, 변경에 필요한 consumer 검증 완료. 자연 source/다음 PREOPEN/PID/경제성 대기는 별도 상태로 기존 체크리스트에 남긴다.

최종 보고는 판정→근거→다음 액션 순으로 작성하고 WP별 상태, 수정 파일, 최초 finding과 보완, 테스트, 최소 재생성 범위와 최신 terminal, source/date/hash, commit/push/release/PID, 선정/carry 사유, 미확인 자연 효과를 포함한다. 코드 수리나 한 건의 submit으로 비용 후 이익 증가를 추정하지 않는다.

문서 변경 후 검증:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

Project/Calendar sync는 실행하지 않는다. 사용자용 표준 명령은 다음 한 개로 한정한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
