# Entry AI 판단·micro 활용 개선 실행 설계

작성: `2026-09-09 KST`. 근거 확인: `08:08~08:12`, source-date `2026-09-08`, machine policy target-date `2026-09-09`. 사용자 요청: “구현 및 개선방안 구체화하라”.

이번 산출물은 **수정 위치·입출력 계약·검증·적용 순서를 정한 구현 설계**다. 아래 제안 상태·필드는 아직 구현된 API가 아니다. 이 문서 작성으로 live prompt, Provider, 주문, 수량, threshold, 프로세스 또는 정책이 변경되지는 않는다. 현재 구현과 남은 구현을 분리하고, 실행·자연 acceptance는 [9/9 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 owner에 연결한다.

## 1. 판정과 확인된 출발점

메인 봇의 기회 포착·판단·학습 환류를 우선 개선해야 한다. **BUY 건수를 늘리는 것 자체가 목적은 아니다. 실행 가능한 양수 순수익 기회를 놓친 원인과, 계속 참여하지 않는 후보를 개선하지 못하는 원인을 각각 닫는 것이 목적이다.**

| 확인된 근거 | 해석 및 구현상 의미 |
| --- | --- |
| [BUY Funnel](../../data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-08.json): as-of `19:20:05`, final action DROP194 / WAIT79 / 미평가4 / BUY0, main accepted submit0 | 277개 기록 이벤트이며 고유 시장 기회 수나 원모델 응답 수와 동일하지 않다. 원모델→보정→runtime action→최초 차단을 나누어야 한다. 당일 전체 또는 9/9 현재값으로 쓰지 않는다. |
| [Entry paired batch](../../data/report/ai_entry_setup_paired_replay_batch/ai_entry_setup_paired_replay_batch_2026-09-08.json): KRX exact Control0, NXT24 | KRX 판단 개선의 재현 입력이 막혔다. NXT24건의 비교 성공으로 KRX 학습이나 전체 AI 개선을 승인할 수 없다. |
| [NXT 상세 비교](../../data/report/ai_prompt_detailed_paired_replay/ai_prompt_detailed_paired_replay_2026-09-08_decision_quality_v2_14_setup_risk_adjudicator_venue_nxt_session_nxt_aftermarket.json): Control DROP18/WAIT6 → V2.14 DROP16/WAIT8, 즉시 노출0, probe arm6 | V2.14가 즉시 진입을 개선했다는 근거가 없다. arm은 주문이 아니므로 후속 재확인 결과와 따로 평가한다. |
| 같은 상세 비교: 작은 target-first execution-proxy 누락 DROP2 / WAIT5 | 오판 재검토 사례7건이다. `net_profit_opportunity=null`이므로 확정 순이익7건으로 부르지 않는다. 기존 gross1% 진단만으로 작은 기회가 없다고 결론내리면 안 된다. |
| [Micro context](../../data/report/microstructure_reaction_context/microstructure_reaction_context_2026-09-08.json): computed325, payload included0 / sent0, internal consumed116 | 내부 계산·holding 품질 소비와 AI 입력 전달은 다르다. 이 과거 집계에는 배포 전 호출도 있으므로 새 PID/호출의 결함으로 단정하지 않고 재현한다. |
| [R0→R3](../../data/report/main_ai_quality_r0_r3/main_ai_quality_r0_r3_cycle_2026-09-08.json): source-only blocked/deferred, Provider 미실행 | micro 대조군 paired2 / economic0 및 observer exclusion 경계를 먼저 확인한다. 유효한 local label·원천 census 생성과 Provider/full-gate 실행을 분리한다. |
| [Machine attribution](../../data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json): anchor108 / matched0; [9/9 timing policy](../../data/runtime/machine_entry_timing_policy/machine_entry_timing_policy_2026-09-09.json): `scopes={}` | 0/1/3/5초 consumer 코드가 있어도 선택된 동적 scope는 없다. 즉시진입 baseline carry이며 신규 micro timing의 실수익 효과는 미입증이다. |

독립 에피소드의 수익 거래는 메인 봇의 탐색 누락을 확인할 좋은 사례다. 앞선 대조에서 9/8 수익 leg가 있는 `015760/006800/181710/028050`은 [당일 AI trace](../../data/ai_decision_trace/ai_decision_trace_2026-09-08.jsonl)의 `stock_code` 기준으로 발견되지 않았다. 이는 **AI가 그 거래를 DROP했다는 증거가 아니다**. 정확한 signal 시각·route·session에서 scanner 이전부터 대조해야 한다. 수익 거래만 뽑아 EV를 계산하지 않고 같은 owner의 손실·미체결·HELD도 보존한다.

이미 [9/8 보완](./2026-09-08-entry-ai-submit-drought-remediation-review.md)에서 exact redaction 허용 경로, `ai_entry_decision_layers_v1`, final response hash, 작은 기회 taxonomy, 비용 결손 pair 격리를 구현했다. 이 코드를 다시 만드는 작업은 열지 않는다. 새 원천에서 계약 실패가 재현된 부분만 추가 수리한다.

추가로 확인한 [별도 재기동 기록](./2026-09-09-graceful-main-restart-review.md)은 9/9 08:07:41 PID24260/ad69d928 및 runtime verify PASS를 남겼다. 이는 이 설계 작업에서 실행한 재기동이 아니다. P0의 다음 증거는 이 배포 이후의 자연 request/전송/Control이며, 배포 기록만으로 모든 endpoint의 입력 전달이나 KRX 학습 정상화를 승인하지 않는다.

근거 파일의 읽기 시점 byte SHA256은 Entry batch `1c690112bd680ed3556ba957611c0b13ff818373981529a345a1eec1b220c782`, micro context `e9a9fe5440ccb63bcb1f7afd78f4ca34ea81c56acf80fc5d4516ac12da541298`, target9/9 machine timing policy `c2efec5a47baad8bce6865b2836b2719d29a6992b2029c1d8aed88437d3efd25`다. 이후 자연 갱신된 파일은 새 generation으로 대조하며 이 hash를 현재 기대값으로 고정하지 않는다.

## 2. 수정 단위와 우선순위

P0 원천·전달 복구를 먼저 닫는다. P1 연구 판단 개선은 유효한 기존 원천으로 설계·테스트할 수 있지만 결손 입력을 정상화하지 않는다. P2 실적용은 기존 정책 owner와 검증된 target-date 계약을 따른다.

| 단위 | 구체적 변경 또는 검증 | 기존 코드 owner | 완료 증거 |
| --- | --- | --- | --- |
| P0-A KRX exact 학습 입력 | 새 호출의 prepared request→실제 전송 payload→원응답→검증·보정된 final response→Control manifest를 같은 ID/hash로 대사. 최초 결손 사유 하나와 secondary reasons를 분리 | [ai_decision_trace.py](../../src/engine/scalping/ai_decision_trace.py), [ai_engine_openai.py](../../src/engine/ai_engine_openai.py), [ai_decision_quality.py](../../src/engine/scalping/ai_decision_quality.py) | 새 유효 KRX 호출의 exact Control 포함 또는 직접 제외 사유. 코드가 이미 충족하면 `existing_implementation_verified`; 과거 redacted/final-response 결손은 제외 유지 |
| P0-B micro 실제 전달 | context identity와 factual feature가 endpoint의 최종 직렬화 payload에 있는지 검사. 전송 시도·Provider 확인·내부 소비·cache 재사용을 각각 기록 | [microstructure_reaction_context.py](../../src/engine/scalping/microstructure_reaction_context.py), `ai_engine_openai.py`, `ai_decision_trace.py` | 기존 delivery v3 identity로 `computed→payload_included→confirmed_sent`가 연결. required endpoint의 누락은 행별 결함. 단순 계산 성공을 sent로 세지 않음 |
| P0-C machine 원천 결속 | REG/first-data→실제 signal_decision_at→같은 route/epoch의 checkpoint→leg terminal을 잇고 최초 결손을 분류 | [machine_microstructure_attribution.py](../../src/engine/monitoring/machine_microstructure_attribution.py), [micro_confirmation.py](../../src/trading/market/micro_confirmation.py) | fresh 원천의 exact anchor/checkpoint 또는 구체적 gap. 과거 ingress loss와 target timestamp 결손을 복구시각으로 메우지 않음 |
| P1-A 비용을 반영한 기회 평가 | 기존 작은 execution-proxy 진단 옆에 충분한 원천이 있는 경우만 action-neutral net label 및 비용별 근거를 추가. action layer별 놓친 기회를 집계 | `ai_decision_quality.py`, [ai_action_outcome_calibration.py](../../src/engine/scalping/ai_action_outcome_calibration.py) | proxy/CF net/실현손익의 분리, 분모 보존, 동일 payload 대조, 새 필드의 #82→#78 소비 |
| P1-B 참여0 후보의 연구 종료조건 | sample 미달로 같은 후보만 반복할 때 원천 부족·후속 actuator 미지원·기회 부재·기회가 있는데 무참여를 구분. 아래 bounded 연구 선택 규칙을 추가 | [main_ai_prompt_optimizer.py](../../src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py), [entry_setup_paired_replay_batch.py](../../src/engine/scalping/entry_setup_paired_replay_batch.py), [main_ai_prompt_consumer.py](../../src/engine/scalping/main_ai_prompt_consumer.py) | 반복 입력으로 진전이 생기지 않으며, 새 유효 원천에서 연구 유지/다음 후보/구체적 prompt patch 제안 중 하나가 이유·hash와 함께 출력 |
| P1-C scanner 미도달 대조 | 독립 시장 census와 독립 machine 사례를 서로 다른 모집단으로 대조. 미관측과 AI 거부를 구분 | [market_opportunity_census.py](../../src/engine/monitoring/market_opportunity_census.py), [rising_missed_scout_workorder.py](../../src/engine/monitoring/rising_missed_scout_workorder.py) | exact 시각·venue·session·episode의 최초 미도달 stage. 시장 전체 recall의 분모는 독립 census 유지 |
| P2 기존 owner 적용 | Main의 검증된 KRX V2.14/V2.15 또는 machine timing의 통과 scope만 각 기존 policy→PREOPEN→loader/PID→실제 결과로 확인 | [entry_setup_live_policy.py](../../src/engine/scalping/entry_setup_live_policy.py), [machine_entry_timing_tuning.py](../../src/engine/automation/machine_entry_timing_tuning.py), [machine_entry_timing_policy.py](../../src/trading/config/machine_entry_timing_policy.py) | 적용 hash·시각·scope·rollback·실제 소비 receipt와 이후 비용 차감 성과. 빈 scopes나 legacy R3 metadata 성공은 적용 성공이 아님 |

새 Python root module, 병렬 report producer, cron, 별도 주문 owner를 만들 필요는 없다. 현재 module의 계약과 consumer를 확장하는 설계다. 실제 구현에서 protocol/REG/시간·FID 파서를 바꾸게 되면 먼저 [Kiwoom 공식 reference gate](../kiwoom-api-data-contract.md)를 수행해야 한다.

## 3. 메인 AI 개선의 데이터·평가 계약

### 3.1 원모델과 후처리의 책임 분리

현재 `ai_entry_decision_layers_v1`을 재사용한다. 각 자연 요청에 request/trace/snapshot, endpoint, stage, venue/session, prompt/schema/bundle/hash, source timestamp, provider response ID와 final response hash를 연결한다. 원모델 DROP/WAIT/BUY, adapter 보정, deterministic composer, runtime authority, submit safety를 개별 열로 남긴다.

보고서에는 고유 request, 고유 promotion, 고유 opportunity episode를 각각 명시한다. 첫 결손 기준으로 `request_not_captured → payload_not_exact → response_unbound → final_response_missing → source_invalid → outcome_not_mature → economic_contract_missing` 중 하나를 부여하고 중복 경고는 secondary로 둔다. `input = retained + excluded + pending`을 닫는다. 유효한 KRX 요청이 존재하는데 계속 Control0이면 단순 대기 대신 해당 첫 결손 owner를 수리한다.

### 3.2 작은 수익 기회를 과장 없이 평가

기존 `entry_small_profit_opportunity_v1`과 gross1% 진단은 보존한다. 추가 net 평가의 가격은 decision 이후 실제로 관측된 executable BBO와 선언된 체결 가능성 모델로만 만든다. 평가 수량·depth·fill feasibility가 없으면 해당 조건부 CF도 `null`이다. 미래 high/first-hit은 label에만 사용한다.

- 비교 정책: `2026-08-18` 이후 매수1.5bps + 매도1.5bps + 매도세금20bps, Provider 비교비용0원. 공식 보통주 master의 effective date/hash와 cost policy hash를 함께 결속한다.
- gross0.30%의 비용 전 여유는 고정 왕복비용 약0.23%를 빼면 약0.07%p다. 추가 체결비용에 따라 없어질 수 있으므로 proxy-positive를 net-positive로 승격하지 않는다.
- executable ask 진입/bid 청산을 썼다면 spread는 이미 가격에 반영된다. 별도의 spread 차감을 또 하지 않는다. 수수료·세금·추가 slippage의 포함 여부를 항목별로 기록한다.
- 평가 horizon/target/adverse/TTL은 비교 시작 전에 기존 owner의 계약으로 고정한다. 결과가 좋은 horizon을 사후 선택하지 않고 KRX/NXT, Entry/holding, full/partial, CF/실체결을 분리한다.
- 주문하지 않은 WAIT/DROP도 성숙한 action-neutral 시장 경로가 있으면 CF 학습에 남긴다. 이를 위해 메인 봇 실체결을 요구하지 않는다. 반대로 actual realized PnL에는 exact broker terminal·실제 비용을 요구한다.

신규 metric의 제안 계약은 다음과 같다. 구현 시 producer와 소비자 양쪽에 동일 계약 버전·source hash를 넣는다.

| 제안 output field | formula / role | window·floor·결손 처리 |
| --- | --- | --- |
| `cost_aware_actionable_episode_count` | 당시 owner 자격·기존 safety 적격, 유효 source·체결 가능성·고정 비용·성숙한 양수 net target-first를 충족한 고유 episode 수; 진단 분모 | daily 및 기존 rolling5/10/20 source-day를 별도 출력. 유효 행1개부터 진단 가능하며 승격 표본 기준으로 쓰지 않음. 자격/안전 제외의 당시 근거와 raw 분모는 보존 |
| `cost_aware_opportunity_capture_pct` | 같은 분모 중 유효한 평가 action과 선언된 체결 가능성 모델이 기회 유효시간 안의 노출을 선택한 episode / 위 분모 ×100; CF 진단 | 분모0이면 null과 기회 부재/원천 결손 이유. 실제 fill 포착률과 별도 출력. arm만 된 WAIT는 capture가 아니며 후속 유효 recheck를 따로 연결 |
| `source_quality_adjusted_ev_pct` / paired delta | 기존 경제성 owner의 유효 동일 payload·동일 비용 비교를 재사용; primary EV | 해당 owner의 기존 경제성 floor/holdout을 유지. 무노출 평가0과 exposure EV null을 함께 표시. 표본/비용 결손은 0EV로 대체하지 않음 |
| `realized_net_pnl_krw`, capital occupancy | exact owner/order/terminal/비용의 실제 결과; 실행 성과 | 복원된 과거 손익·CF를 더하지 않음. 미대사 null, HELD는 열린 자본점유로 별도 표시 |

위 신규 count/recall은 `decision_authority=diagnostic_source_only`, `allowed_runtime_apply=false`다. 경제성 선택은 기존 primary EV owner가 소유한다. 모든 신규 필드에 metric_role, window_policy, sample_floor, primary_decision_metric, source_quality_gate, forbidden_uses를 명시한다.

### 3.3 후보 프롬프트를 바꾸는 연구 루프

현재 optimizer의 `_select_entry_challenger()`는 V2.14→V2.15→V2.16 registry를 탐색하지만, 일부 누적경제성 탈락 조건에 `candidate_exposure_floor`를 요구하고 promotion 표본이 미달이면 같은 후보를 유지한다. 이 코드만으로 영구 정체를 확정하지는 않는다. 다만 무참여 후보의 **연구 수정·교체 판단**을 실거래 승격 표본 대기와 분리해야 한다.

다음은 구현 제안이며 현행 선택 규칙이 아니다.

1. 매 generation마다 `new_exact_parent_count`, 새 유효 source일, source/비용 결손, 실제 opportunity 수, 즉시 노출, arm, 유효 recheck terminal, 동일 후보 반복 사유를 기록한다. 새 원천이 없으면 checkpoint 재사용 또는 valid-empty로 닫고 같은 payload의 새 Provider 호출을 만들지 않는다.
2. 단일 유효 사례부터 원모델·후처리 오판 가설과 English ASCII prompt patch 초안을 생성할 수 있다. 이는 진단 수리/연구 제안이며 Provider 실행·경제성 승격을 기다릴 이유가 아니다. 새 모델 호출량을 자동 증설하지 않는다.
3. **기존 연구 최소창인 5 source일·5 exact parent·3종목을 연구 유지 재검토 시점으로 재사용하는 안**을 검증한다. 달력5일과 유효5일을 구분하고, source0/유효기회0/후속 recheck 미성숙은 모델의 실패로 판정하지 않는다. live floor를 낮추는 안이 아니다.
4. 이 시점에 유효 net 기회가 있는데 즉시 노출과 유효 recheck 참여가 계속0이면 `zero_participation_with_valid_opportunities`로 연구를 재검토한다. 기회1건만으로 양수 EV나 후보 우월성을 승인하지 않는다. source 결손이면 수리 owner, 후속 actuator 부재이면 runtime 설계 owner, 모델·보정의 무참여이면 다음 지원 후보 또는 명시적 prompt patch 제안으로 보낸다.
5. 대체 후보는 같은 frozen payload/outcome에서 Control과 비교한다. 장중에 여러 live 축을 켜지 않는다. V2.15도 미검증이면 새로운 실험 후보이며 우월하다고 가정하지 않는다. V2.16은 sequential actuator가 미등록이므로 runtime-ready로 내보내지 않는다.
6. 작은 양수 기회 누락 감소와 함께 adverse-first 오진입, p10/tail, 비용 차감 EV, 기회당 참여·순익/자본시간을 본다. 같은 거래일을 반복 튜닝해 holdout으로 쓰지 않는다. 독립 다음 source-day 검증 전에는 개선 효과를 확정하지 않는다.

프롬프트 초안은 [ai_prompt_contracts.py](../../src/engine/ai_prompt_contracts.py)의 기존 registry 경계를 따른다. 초안 manifest에는 `parent_prompt_hash`, 수정한 문장, 원인 가설, 근거 case IDs, 실패할 수 있는 반례, 지원 schema/actuator, 평가 모집단, rollback hash를 넣는다. 기존 버전의 내용을 바꾸고 hash를 유지하지 않는다.

첫 가설은 “현재 target·비용·fresh BBO를 기준으로 작은 양수 기회를 평가하고, 지속 가능한 회복과 일시적 ask 취소/refill을 구분하는가”다. `hard_negative`, `recheckable_soft_risk`, `cost_aware_micro_candidate`는 분석 분류이며 BUY 명령이 아니다. 미래 결과를 입력에 주입하거나 단순 점수·잔량 감소를 BUY 규칙으로 바꾸지 않는다.

### 3.4 입력 개선과 프롬프트 개선의 효과 분리

기존 optimizer의 2×2 설계를 사용한다. A=Control+현재 입력, B=Candidate+같은 입력, C=Control+검증된 micro 사실 입력, D=Candidate+같은 micro 입력이다. B−A는 prompt 효과, C−A는 입력 효과, D−C는 풍부한 입력에서의 prompt 효과로 별도 보고한다. 실제 구현은 기존 batch가 지원하는 셀부터 진행하며 optional input 셀의 Provider consumer 미연결을 성공으로 세지 않는다.

micro 교집합이 없으면 A/B의 유효 base 연구는 계속할 수 있다. C/D만 원천 결손으로 남긴다. 다만 각 경로에 실제로 적용되는 observer/source-quality·Provider budget gate는 유지한다. 셀 추가는 reviewed budget을 나눠 쓰는 설계이며 호출량 증액이 아니다. 하나의 stage에서 입력과 prompt를 동시에 live 변경해 효과를 섞지 않는다.

## 4. Micro-reversion·매도잔량 감소속도 전달 설계

### 4.1 공통 계산과 Main AI

[ask_depletion.py](../../src/engine/scalping/micro_reversion/ask_depletion.py)와 [ai_quality_bridge.py](../../src/engine/scalping/micro_reversion/ai_quality_bridge.py)를 재사용한다. 같은 symbol/venue/session/connection epoch의 0B·0D 순서, 원본 receive timestamp, quote age와 sequence 검증을 먼저 통과한다.

Main의 기존 stage context 안에 포함할 사실 입력은 현재 best ask 잔량 감소속도(qty/sec), 관측창 길이, top1/3/5 변화, 공격적 매수 backing, 설명되지 않은 감소/취소 추정, refill 정도·회복시간, bid 지지, spread, 가격 반응, source quality다. 취소와 체결을 구분할 수 없으면 미확정으로 남긴다. ask 가격 level 변경은 동일 level 잔량 감소와 분리한다. 종목 간 비교에서는 raw qty/sec와 초기 잔량 대비 비율·거래량 문맥을 함께 보존한다.

existing reaction context의 sweep/replenishment score와 ask-depletion 원시 feature는 같은 자료가 아니다. 모든 필드를 이미 live AI에 보낸다고 주장하지 않는다. **기존 전달 계약의 누락 수리**와 **새 factual field를 모델 입력으로 추가하는 변경**을 별도 diff로 만든다. 전자는 해당 endpoint 계약을 복구하고, 후자는 source-only 비교·schema/version review 후 기존 입력 적용 owner의 권한을 따른다. 이미 승인된 multi-timeframe context의 전역 적용 gate를 새 canary나 재승격 대기로 바꾸지 않는다.

필수 검증은 최종 payload의 실제 값, context/evaluation/cache ID, provider receipt다. 코드 필드 존재·`computed=true`·내부 holding 소비만으로 전달을 승인하지 않는다. 미래 target/adverse first-hit, 사후 고가, terminal PnL은 prompt input에서 금지한다. 누락·stale·cross-epoch이면 unavailable로 전달하고 기존 판단/안전 계약을 유지한다.

### 4.2 위젯·에피소드

이 경로에는 새 AI 호출을 붙이지 않는다. 기존 [위젯 엔진](../../src/trading/widget_auto_trade/engine.py), [two-leg 엔진](../../src/trading/order/regular_two_leg_machine.py), [Samsung 엔진](../../src/trading/samsung_morning_one_share/machine.py)의 timing consumer를 사용한다.

실제 `signal_decision_at` 후 `0/1/3/5초` checkpoint에서 **각 시점 직전1초의** fresh exact-route same-epoch BBO/0B/0D를 읽어 direct support·반등·trade backing·refill을 평가한다. 미래 first-hit은 장후 label이다. 선언된 원래 signal의 가격·수량·target을 유지하고, ENTER/fallback 직전에 기존 manual-owner/account/order/global-pause/liquidity/velocity/market-weakness/broker guard를 다시 검사한다.

고정 mode의 기존20 completed·BBO/paired95%·depth/feasibility90%·right-censored20% 및 complete5/10/20일 조건을 유지한다. 동적 mode도 기존5 observed dates·8 unique/8 completed·replay/paired85%·right-censored35% 이하·complete5 source-day 경제성/0.005%p uplift/p10 및 최신 자연 신호 조건을 유지한다. selection floor 미달을 줄이기 위해 HELD 완료 처리, profile 병합, sample 복제 또는 floor 하향을 하지 않는다.

이번9/9 `scopes={}`는 즉시진입 baseline이다. 다음 scope가 통과하면 기존 exact-date publication/승계 절차를 따른다. 데이터가 없어도 blind wait나 새 hard veto를 만들지 않는 기존 fallback을 보존한다. 목표가, 무손절/시간청산 없음, 보유 target, 독립 두10주 leg와 legacy custody는 이 축의 수정 대상이 아니다.

## 5. 검증·handoff·종료조건

실제 구현은 P0-A/B/C → P1-A/B/C → P2 순서로 작은 diff와 독립 review를 만든다. 이미 구현된 P0의 자연 receipt가 닫히면 그 항목은 추가 코드 없이 종료한다. 결손 과거일의 반복 재생성 대신 새 exact 원천을 사용한다.

| 변경 범위 | 반드시 검증할 반례 | 기존 targeted test |
| --- | --- | --- |
| exact Control / action layer | 원모델 WAIT→adapter DROP, final hash 변조, 실제 secret redaction, legacy final snapshot 결손, provider none, valid+invalid 혼합 보존 | `test_ai_decision_trace`, `test_ai_decision_quality`, `test_ai_engine_openai_transport`, `test_entry_setup_paired_replay_batch` |
| context 전달 | computed-only, serialized-but-send-failed, 확인된 전송, cache reuse, 다른 epoch/venue, Entry/holding payload 혼합, unavailable 필드 | `test_microstructure_reaction_context`, `test_microstructure_reaction_context_report`, `test_ai_engine_openai_transport` |
| 비용/후보 연구 선택 | gross 양수/net 음수, 비용 결손, spread 이중차감, no-exposure null 구분, 무기회 vs 무참여, arm 후 미성숙/성숙, 같은 parent 반복, 미지원 actuator, 정상 부분학습 | `test_ai_decision_quality`, `test_ai_action_outcome_calibration`, `test_main_ai_prompt_optimizer`, `test_main_ai_prompt_consumer` |
| machine timing | signal 이전 자료 부재, 같은1분봉 미래 high 유입, cross-route/epoch, snapshot 결손 fallback, guard 재검증, HELD/custody 혼합, 빈 scope | `test_dynamic_micro_confirmation`, `test_machine_microstructure_attribution`, `test_machine_entry_timing_tuning`, `test_machine_microstructure_policy_approval` |

코드 변경마다 관련 pytest/compile과 `git diff --check`, review→fix→re-review를 수행한다. consumer/registry/wrapper가 변경되는 경우 해당 계약 테스트와 문서도 함께 변경한다. review finding0 전 비싼 재생성·runtime follow-up을 실행하지 않는다. 자연 수집·진단 전달 수리에 양수 EV나 실체결을 추가 완료조건으로 붙이지 않는다.

| 기존 acceptance owner | 기존 Due / TimeWindow(KST) | 이번 설계의 handoff / 다음 확인 |
| --- | --- | --- |
| `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908` | 9/9 PREOPEN 08:40~08:45 | P0-B/C의 현재 source·first-data·epoch·loss/exclusion. 창 종료 후의 정상 지속 수집과 다음 source-quality 감사를 분리 |
| `AIDecisionActionOutcomeNaturalEvidence0908` | 9/9 POSTCLOSE 20:10~21:55 | P0-A/B, P1-A/B 및 optional2×2. source9/9의 exact Control→detailed→#82→frozen optimizer→metadata rebind→consumer hash. 후속 구현 제안/구현 완료/자연·경제성 상태를 별도 보고 |
| `ScannerLookupAttentionNaturalEvidence0908` | 9/9 POSTCLOSE 20:10~20:40 | P1-C. 외부 census와 machine 감사 사례 분모 분리 및 최초 scanner 미도달 stage |
| `EntryRecheckNaturalAttribution0907` | 9/9 POSTCLOSE 20:10~21:50 | action layer 이후 fresh recheck·원본 parent·submit/fill/terminal. 현재 정책 적용은 별도 exact-date receipt |
| `MachineLifecycleTurnoverObjectiveFollowup0909` | 9/9 POSTCLOSE 21:30~21:40 | P0-C 및 P2 machine. 새 exact source→timing 연구·baseline/선택 scope, net·자본점유 |
| `MainAIQualitySourceGapArtifactContract0909` | 9/9 POSTCLOSE 21:40~21:50 | 제안의 설계 번호를 native workorder ID로 위조하지 않고 기존 canonical source-gap workorder identity/hash와 연결 |

위 시간은 예정된 확인 창이며 이 문서로 producer를 조기 실행하거나 오늘 내 경제성 완료를 약속하지 않는다. 새로운 차기 작업은 기존 owner를 이관하거나, 실제 독립 owner가 필요할 때만 Due/Slot/TimeWindow/Track을 갖춘 checklist 항목으로 만든다. 선행 source0을 달력 시간이 해결할 것이라고 예측하지 않는다.

완료 보고는 `design_status`, `repair_status`, `deployment_status`, `natural_acceptance`, `economic_acceptance`로 나눈다. 이번 요청은 설계를 구체화하며 코드·실적용·수익 개선 완료를 뜻하지 않는다. 재기동·수동 env/lock·Provider route·threshold·주문/수량·안전 변경은 기존 명시 권한 없이 수행하지 않는다. 퇴역 ADM/LDM/#81 legacy authority는 복원하지 않는다.

## 6. 설계 문서 검토

`korstockscan-review-gate`의 문서 모드로 원천/consumer 경계, 기존 구현 중복, 동일 owner, 신규 제안과 현행 계약, 과거 source-date와 현재 적용일을 검토했다. 1차 리뷰에서 CF 포착률과 실제 fill 포착률을 더 명확히 분리하고, actionable 분모에 당시 owner 자격·안전 적격 및 제외 근거를 명시했다. 이 문서는 자동화 report 입력이나 정책 artifact가 아니다.

문서 범위 재리뷰의 미해결 finding은0이다. local link/anchor, 기존 owner6개 각각 현재 checklist에서1건 파싱, print-only parser 및 `git diff --check`를 검증했다. 신규 Python/거래 코드 변경이 없어 trading pytest·Provider 호출·운영 report 재생성은 이 문서 검증에 포함하지 않는다. 관련 코드 구현 여부와 경제성 수용은 §5의 후속 단계다.

Project/Calendar sync는 [체크리스트의 표준 수동 명령](../checklists/2026-09-09-stage2-todo-checklist.md#projectcalendar-동기화)을 사용자가 실행한다. 이번 작업에서는 print-only parser만 실행한다.

## 7. 후속 구현 receipt (2026-09-09)

위 문서-only 설계 이후 사용자가 구현과 결함이 없어질 때까지의 리뷰·자동화/조건 달성 가능성 점검을 명시 요청했다. 그 후속 실행은 [구현 리뷰](./2026-09-09-entry-ai-micro-profit-implementation-review.md)와 [검증 JSON](./2026-09-09-entry-ai-micro-profit-implementation-validation.json)에 기록했다. 앞 절의 설계 작성 시점과 과거 수치는 보존한다.

P0-B payload 누락 수리, P1-A exact 비용 label companion의 기존 상세/누적 consumer 연결, P1-B 최근 유효5 source일의 무참여 연구 교체 및 단일 사례 prompt 초안, P2의 중복 당일 arm floor/가상 전역 적용 조건 제거를 구현했다. P0-A/C와 P1-C는 기존 구현과 관련 회귀검증을 재사용했다. 연구 교체는 경제성 탈락과 별도이며 execution-proxy 사례로도 offline 가설을 탐색할 수 있게 §3.3의 net 근거 대기를 조정했다. proxy를 확정 net 기회로 승격하거나 live floor를 낮춘 것은 아니다.

관련996 tests 및 최종 영향302 tests(중복 집합), compile/diff 검증을 수행했다. 실제9/8 NXT24 parent에서 사례7개가 초안1개로 연결됐지만 source1일로 교체 대기이며 과거 비용 진단 결손은 유지한다. 기존 예약·등록된 적용 owner의 연결을 확인했고 현재 PID의 새 코드 소비와 자연 경제성은 기존 checklist owner에 OPEN으로 남겼다. 이 구현 receipt는 주문·재기동·수동 정책 적용 receipt가 아니다.
