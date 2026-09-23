# 메인 진입 실행 장후 EV 평가·장중 정책 소비 최종 구현계획

작성: 2026-09-23 KST. 상태: **구현계획**. 이 문서 작성은 코드·정책·주문·배포·장후 재실행을 수행하거나 승인하지 않는다.

범위는 메인 SCALPING의 기계판정·보조 AI 이후 실제 진입 실행과 장후 경제성 평가다. [9/23 체크리스트](../checklists/2026-09-23-stage2-todo-checklist.md)의 `DirectFamilySourceRepairEntrySplit`은 **분할 진입만**, `DirectFamilySourceRepairEntryCancelWait`는 **제출 후 취소 대기만** 소유한다. 최초 진입 지연에는 별도 `DirectFamilySourceRepairPreSubmitDelay` owner와 독립 장후 stage를 둔다. `DirectFamilyScopeDecisionMainMechanisticEntry`·`DirectFamilySourceRepairCompactAuxiliary`는 상류 판정 증거 owner이고, `scale_in_split`과 holding/exit는 실제 체결 뒤의 별도 owner다. 새 주문 엔진·공통 승인기·cron은 만들지 않는다.

**최종 결정:** 분할 진입과 최초 제출 지연은 서로 다른 튜닝축이다. 분할 진입은 **같은 제출 시각·확정 수량에서 parent/child 수량·가격 형태**를 고른다. 지연은 **같은 진입 판정·확정 수량·고정된 분할 정책에서 최초 제출 시각**을 고른다. 두 축은 같은 원천 ID·압축 시세를 읽을 수 있지만 평가 모집단·후보·모델·holdout·보고서·정책 파일·승격·런타임 로더·rollback·완료 상태가 독립적이다. `entry_cancel_wait_runtime`은 제출 **후** 취소 대기의 세 번째 독립 계약이다. 장후 재생성은 각 축의 비용 후 incumbent/후보 EV 또는 정확한 원천 결손과 dated carry를 별도로 발행한다.

기계판정·보조 AI·분할 진입·최초 제출 지연의 **정책 개입 평가와 개선 귀속은 네 갈래로 상호 배타적**이다. 동일 원본 체결·청산·비용은 두 분석의 incumbent 참고값이 될 수 있어도 실현손익 한 건을 여러 번 더하지 않는다. 각 후보 평가에는 `analysis_axis`, 동일 attempt ID, 실제 정책 세대 및 나머지 세 축의 고정 정책 hash를 기록한다. 한 축의 EV·승률·선정 상태를 다른 축의 독립 후보나 승인 증거로 전용하지 않는다.

## 1. 실제 장후 순서와 경제적 연결

메인 wrapper는 `main_machine_policy`를 먼저 독립 발행한다. 그 뒤 원천 품질 preflight, 실제 거래 사실 동기화, `entry_split_order_plan`, `outcome_labels`, `entry_cancel_wait_tuning` 등을 실행한다. `main_auxiliary_policy` stage는 `outcome_labels` receipt를 선행 입력으로 요구한다. 최초 제출 지연은 기존 `entry_split_order_plan` 안에 넣지 않고, 실제 거래 사실·공통 시세 projection을 선행 입력으로 받는 **독립 `pre_submit_delay_tuning` stage**를 wrapper와 [stage registry](../../src/engine/automation/postclose_summary_handoff.py)에 추가한다. 두 정책 stage 사이에는 성공 의존성을 두지 않는다. 각 stage는 같은 장중 기계·AI 판정 세대의 **자기 모집단**을 평가한다. 기존 [native wrapper](../../deploy/run_threshold_cycle_postclose.sh)의 계산 슬롯·terminal 계약에 새 stage를 등록하되 별도 cron은 만들지 않는다.

```text
장중 원 기회 → 기계 BLOCK/RECHECK/ENTER_NOW
                         └─ 실제 ENTER_NOW → AI 호출 여부·raw/effective 판정
                                             └─ 실제 effective PASS/CAUTION → 최종 진입 guard
                                                           ├─ 미진입: 정확한 차단 owner
                                                           └─ 확정 intent → 최초 제출 지연 정책
                                                                     → fresh 재검증·현재 실행가/확정 수량
                                                                     → 독립 분할 정책의 parent/child
                                                                     → broker 제출 → ACK/체결/취소
                                                                     → 보유·청산·실제 비용

장후: 공통 exact 원천 → [분할 형태 평가 → 분할 정책]
                      → [최초 제출 지연 평가 → 지연 정책]
                      → [제출 후 cancel wait 평가 → 취소 대기 정책]
      각자 직접 경제성/정책 → runtime_approval_summary → checklist/strict 인계
```

| 독립 평가축 | 변경하는 반사실 | 고정·제외 조건 | 미진입 책임 범위 |
| --- | --- | --- | --- |
| 기계판정 | `BLOCK/RECHECK → ENTER_NOW`의 미진입 기회비용 | AI·실행 정책을 기계 후보의 선정축으로 쓰지 않는다. 실제 성공 ENTER_NOW는 참고 양성값이지 중복 수익 표본이 아니다. | 기계가 최초로 막은 기회만 기계 owner. |
| 보조 AI | 기계 `ENTER_NOW` 뒤 `VETO → PASS` 및 잘못 허용한 PASS | 기계판정·실행 정책 세대 고정. 기계 BLOCK/RECHECK를 AI가 소급 승격하지 않는다. | AI가 최초로 막은 기회만 AI owner. |
| entry split | 기계·AI·최종 진입 guard 통과 뒤 leg/수량 비율/offset/probe 구조 변경 | 최초 제출 시각과 지연 정책 세대 고정; 주문 수량·가격 상한·exit/cost 고정. | 분할 구조의 미제출 잔여·no-fill·부분체결만 split owner. |
| 최초 제출 지연 | 같은 확정 진입 intent의 0초 대 지연초 변경 | 분할 정책 세대·계획 수량·판정·exit/cost 고정. | 대기 때문에 제출 못 하거나 승리 진입을 놓친 건만 delay owner. |

한 사건에 여러 원인이 연속으로 보여도 `최초 실제 차단 지점`을 경제적 결손의 주 owner로 하나만 기록한다. 독립 검증의 비교 기준으로 다른 축의 원본 결과를 **읽는 것**과 그 축의 **개선 효과로 다시 계상하는 것**을 분리한다. hard safety·가격·브로커 guard 차단은 네 튜너의 미진입 성과로 대체하지 않고 해당 guard owner로 보낸다.

`machine_attribution → machine_timing`, widget/episode 정책과 공동 allocation은 독립 stage다. `rising_missed`는 기계판정 이전 기회 발견의 진단 원천이다. 이들 결과를 메인 AI PASS 이후 주문 성과의 분모에 합치지 않는다. `runtime_approval_summary`는 각 family 평가·후행 소비 상태를 투영하며 EV를 새로 계산하지 않는다.

## 2. 9/22 원천의 현재 결손과 첫 작업

| Owner | 관측 상태 | 보완 대상과 종료 검사 |
| --- | --- | --- |
| `main_mechanistic_entry` | 장후 stage는 성공했으나 [전체 평가 보고서](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-22.json)의 `machine_full_evaluation.state=source_gap`, 전체 2,036건·paired 비교 0건·독립 후보 0건, `machine_operating_population_unbound`, 일별 순익 차이 null. Direct family 요약은 `unsupported_scope`와 무효 정책 receipt를 기록한다. | 기존 `ai_action_outcome_calibration`·publisher·직접 요약 사이에서 **정책 선택용 모집단**과 **변경 판정의 운영 비용/자본 모집단**을 구분한다. 동일 attempt의 실제 실행 owner·terminal·비용이 있는 행만 비교에 넣고, 지원하지 않는 scope는 이유를 남긴다. 전체 평가 성공이나 정책 파일 변경을 paired 순익 입증으로 표시하지 않는다. 종료 검사는 현재 source/policy/consumer 해시와 자연 machine 판정·후행 owner 결과의 재결속이다. |
| `compact_auxiliary` | 9/23 08:31 기준 [경제성 산출물](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-22.json)은 `source_contract_blocked`: 52건 검사·52건 제외·paired 0건. exact stop 결손 16건, terminal 경로 미평가 27건, 자연 응답 의미/전송 결손 9건. Exact-plan prospective 경로는 구현됐으나 자연 exact 행은 0건이다. | 실제 기계 `ENTER_NOW` 후 AI 호출 건만 보존한다. 기존 owner/exact-stop 평가와 독립된 AI 10분 고정경로 평가의 분모·label·cost를 분리한다. 사전 plan hash, 응답 원본/의미, 후행 terminal·비용을 같은 attempt에 연결한다. 과거 결손을 보충 추정하지 않고 다음 자연 exact 행에서 처음 검증한다. 종료 검사는 양성 PASS 보존, VETO/PASS 양방향 전이, paired holdout과 실제 owner 경로의 개별 receipt다. |
| AI stage 인계 | 9/22 `main_auxiliary_policy` terminal은 9/23 02:03의 산출물 hash에 묶였고, 최종 요약은 02:17 생성됐다. 이후 08:31 경제성 파일이 바뀌었다. 기록된 코드 hash를 고정한 read-only stage 검사는 `output_generation_changed`를 반환한다. | 현재 terminal을 최신 파일의 완료 영수증으로 사용하지 않는다. 기존 stage owner의 current-generation 검증으로 변경된 AI 산출물부터 영향을 받는 요약·strict consumer까지 재대사한다. 필요한 하류만 갱신하며 입력이 그대로인 기계/entry split/cancel wait의 고비용 평가를 일괄 재실행하지 않는다. |
| `entry_split` / `entry_cancel_wait` | [직접 family 요약](../checklists/2026-09-23-stage2-todo-checklist.md)은 각각 `operating_paired_source_missing` / `execution_producer_census_unsealed`를 첫 blocker로 둔다. | 아래 ES/CW package로 실제 제출·체결·terminal 모집단을 먼저 닫는다. 두 family의 비용 비교 준비 전에는 null을 0 또는 측정된 no-edge로 바꾸지 않는다. |

위 숫자는 명시된 9/22 source date와 9/23 조회 시점의 스냅샷이다. 구현 착수 때 현재 선택 release, 실제 consumer PID/cwd, 원천·정책 hash, 이후 생성된 산출물과 checklist owner를 다시 대조한다. 현재 작업 트리에 미추적 9/28 checklist가 있고 print-only parser는 같은 stable ID의 향후 owner를 그쪽에서 읽으므로, 9/23 실행 근거와 향후 이전을 혼동하지 않는다. 작업 트리의 다른 변경이나 미추적 TES 계획·향후 checklist는 이번 문서의 완료 증거가 아니다.

## 3. 공통 실행 원천과 비교 단위: D0

1. 원 기회 ID, evaluation attempt/revision, 종목·venue·session·route, source generation/as-of, 기계 component/hash/action, 실제 AI 호출 여부와 raw/effective verdict, 최종 guard를 한 시간순서로 결속한다. 기계 BLOCK/RECHECK를 과거 AI 호출로 소급 편입하지 않는다.
2. `PASS → 가격/수량 계획 → broker parent/child/retry/replace → ACK → full/partial/no-fill → cancel/late fill → 보유/청산 terminal → 비용`을 연결한다. 현재 기계/AI 정책 세대가 다른 기회는 층을 분리한다. 동일 parent의 여러 child와 재시도를 독립 수익 표본으로 중복 계산하지 않는다.
3. `planned`, `committed`, `submitted`, `filled`, `held`, `exited` 수량과 시각을 분리한다. 미제출 잔여는 취소·거부·체결로 합성하지 않는다. [TES probe-first 계획](./probe-first-residual-liveness-tes-repair-plan-2026-09-23.md)의 수량 보존식은 개별 원천 사례로 사용하고 이번 문서에서 그 구현을 완료했다고 표시하지 않는다.
4. 원천 미완결, source-quality 제외, 미성숙 terminal, 모델 미지원 및 유효한 무후보를 서로 다른 상태로 남긴다. clean baseline `2026-06-05T00:00:00+09:00` 이전 자료는 튜닝 입력으로 사용하지 않는다. 실제 PnL에는 `COMPLETED + valid profit_rate` 및 해당 attempt의 확인된 비용만 사용한다.

산출물은 기존 source/receipt에 필요한 최소 identity·count·first-blocker 필드만 추가한다. 64MiB 초과 또는 성장 중인 JSONL은 manifest/summary/offset과 bounded 읽기를 우선하고, 새 전수 스캔·중복 저장소를 기본 방안으로 삼지 않는다. D0 종료는 같은 parent에서 판정·주문·terminal의 누락/중복을 재현하고 각 family의 적격/제외 분모를 고정하는 것이다.

## 4. 구조 결손과 조정 가능한 축

9/22 [entry split 산출물](../../data/report/entry_split_order_plan/entry_split_order_plan_2026-09-22.json)은 `operating_paired_source_missing`으로 비교 가능한 정책 후보가 없다. 이는 후보가 현재 정책보다 열등하다는 뜻이 아니다. [실행 계획기](../../src/engine/scalping/entry_split_order_plan.py)는 `operating_template`을 만들 수 있어도, 런타임에서 `market_first_leg_active` 또는 `probe_config["enabled"]`이면 shape mismatch로 원래 계획을 반환한다. 따라서 오프라인 후보의 분할 형태와 실제 probe 1주→잔여 경로가 일치한다는 보장이 없다. 9/23 관측의 큰 계획 수량·probe 1주 제출·잔여 차단 사례는 이 결손의 영향 범위를 보여주지만, 관측된 차단을 수익 기회나 주문 실패로 일괄 간주하지 않는다.

| 축 | 장후 평가와 런타임 처리 |
| --- | --- |
| 분할 leg 수·수량 비율·가격 offset·첫 leg 방식 | 실제 probe-first, 잔여 source 재검증 및 적용 가능한 venue/session과 **동일한 실행 형태**로 paired 평가한다. 기존 4-arm 후보를 우선 재사용한다. 새 범주는 기존 메뉴로 표현할 수 없을 때만 추가한다. |
| probe 시작 조건·초기 수량·잔여 실행 가능성 | 현재 두 독립 방향 source와 quote 준비 상태를 **현재 시점**에 확인한다. 미래 3초 내 source 도착을 보장한다고 주장하지 않는다. 준비되지 않은 큰 계획은 full-quantity 주문으로 자동 우회하지 않고, 보류 또는 명시적으로 승인된 소량 계획으로만 전환한다. 계획·제출 수량의 차이와 사유를 남긴다. |
| 잔여 TTL·두 source·quote freshness/conflict·가격 상한·수량/브로커 guard | 운영·안전 계약이다. 경제성 튜너가 암묵적으로 완화하지 않는다. TTL 등의 별도 정책축이 실제로 존재하는지 코드와 운영 설정을 census하고, 미연결/고정 항목은 정책 후보에 넣지 않는다. |
| 제출 **후** cancel wait | 독립 `entry_cancel_wait_runtime` owner. 최초 제출 전 지연의 대리변수가 아니며 현재 timeout 정책을 보존한다. |
| 확정 판정→최초 BUY 제출 지연 | 현재 메인 장후 조정축이 없다. 독립 `pre_submit_delay_tuning` 보고서·dated 정책·loader·runtime intent를 추가한다. `entry_split_order_policy`나 `entry_cancel_wait` 값을 읽거나 고치지 않는다. 기존 제출 후 10분 tick-band 진단을 이 축의 근거로 오인하지 않는다. |

**교차축 고정 계약:** 분할 후보 비교에서는 최초 제출 지연을 incumbent 값으로 고정한다. 지연 후보 비교에서는 분할 형태를 해당 기회에서 실제 유효했던 incumbent 정책으로 고정한다. 같은 거래를 두 축이 각자 분석할 수는 있어도 두 정책의 수익 개선을 합산하거나 하나의 `(분할 × 지연)` 후보 grid로 최적화하지 않는다. 한 축의 `source_gap`·`no_edge`·정책 carry는 다른 축의 후보 발행을 막거나 대신 승인하지 않는다.

**세 결과군을 모두 쓰는 계약:** 두 튜너 모두 각자의 적격 원 기회를 분모로 고정하고 아래 세 결과군을 빠짐없이 분류한다. `실제 진입 성공`만 강화하거나 `실패`만 제거하는 학습은 금지한다. 실현손익은 완료된 실체결에만 붙이고, 미진입의 기회비용은 원천이 입증된 반사실 비교로만 평가한다.

| 결과군 | 분할 진입 평가 | 최초 제출 지연 평가 |
| --- | --- | --- |
| 실제 진입 승리 | 동일 parent의 full/partial fill과 `COMPLETED + valid profit_rate`·확인된 비용을 한 건으로 결속한다. 후보가 이 승리의 체결량·순익을 보존하는지 본다. | 0초 실제 체결 승리를 기준으로 지연 시각의 실행 가능 가격·잔량·체결확률·비용을 비교하고, 지연 때문에 놓칠 승리의 비율을 guard로 둔다. |
| 실제 진입 실패 | 손실·비용·부분체결·취소·late fill을 같은 parent에 귀속한다. 다른 분할 형태가 손실을 줄일지 동일 원천·exit 조건에서 비교한다. | 현재 0초 손실 진입이 지연 후에도 체결됐을지, 더 낮은 체결가나 no-fill이 비용 후 성과를 개선하는지 비교한다. 손실 회피만으로 승격하지 않는다. |
| 미진입 기회비용 | **실제 진입 intent가 있었으나** 분할 leg 미제출·잔여 차단·no-fill로 못 산 수량과 이후 실행 가능 경로를 평가한다. 1주 probe의 수익을 미제출 잔여 906주의 수익으로 확대하지 않는다. | **확정 진입 intent가 있었으나** 지연 중 source/AI/가격 guard 만료·가격 상승·no-fill로 놓친 승리와, 0초에는 못 샀지만 지연 시각에는 살 수 있었던 기회를 양방향 평가한다. |

모든 결과군의 후보 평가는 **같은 frozen attempt·목표 수량·venue/session·원 판정·자본·exit·cost**에서 paired로 수행한다. 실제 실현손익과 반사실 EV는 별도 열·분모로 보존한다. 미진입 행에 route·신선한 ask/depth·실행 가능성·후행 terminal/cost가 없으면 기회 건수와 결손 사유는 남기되 EV는 `null`이다. 기계 `BLOCK/RECHECK`, AI `VETO`, 마지막 진입 guard에서 탈락한 건은 이 두 실행축의 미진입으로 소급 편입하지 않고 각각의 상류 owner가 평가한다. 완료되지 않은 보유·청산도 검열 상태로 남긴다.

| 계약 | 분할 진입 `entry_split` | 최초 제출 지연 `pre_submit_delay` |
| --- | --- | --- |
| 조정 대상 | 최초 제출 시각을 고정한 상태의 leg 수·수량 비율·가격 offset·probe/잔여 실행 형태 | 확정된 진입 intent부터 **최초** broker BUY 호출까지의 대기 시간(0/30/60/120/180초) |
| 비교 시 고정 | 원 판정·최초 제출 시각·목표 수량·지연 정책 hash·exit/cost | 원 판정·목표 수량·분할 정책 hash·exit/cost; 후보 시각마다 fresh source 재검증 |
| 장후 산출물 | 기존 `entry_split_order_plan` 보고서와 `entry_split_order_policy` | 별도 `pre_submit_delay_tuning` 보고서와 `pre_submit_delay_policy` |
| 런타임 소비 | 기존 분할 allocator, 제출 시점 이후 | 별도 loader와 제출 전 intent/timer, 분할 allocator **이전** |
| 실패·승격 | own `source_gap/insufficient_evidence/no_edge/selected`, own hash/rollback | own `source_gap/insufficient_evidence/no_edge/selected`, own hash/rollback; 결손 시 0초 또는 유효한 동일 축 carry |

### ES0–ES4: 실제 entry split 폐루프

분할도 모든 종목에 동일 leg·비율을 강제하지 않는다. 동일한 사전 관측형 venue/session·호가단위·유동성·변동성에서 parent 대비 분할 형태의 실행 가능성·비용 후 EV를 평가한다. 다만 ES selector는 **분할 형태만**, 아래 PD selector는 **최초 제출 시각만** 선택한다. 두 selector의 leaf·표본·승격 증거를 공유하거나 교차곱으로 동시 최적화하지 않는다. 각 유형의 paired/holdout이 부족하면 해당 축의 검증된 parent 정책으로 내려가고, 원천이 없는 유형을 다른 종목의 승리로 채우지 않는다.

1. **ES0, exact census:** 최종 진입 가능 판정의 attempt/revision과 frozen 목표 수량, source/정책 hash, 현재 probe eligibility, 준비 source, 실제 parent/child, submitted/filled/미제출 잔여, quote 상태, cancel/terminal/cost를 한 번만 결속한다. 제출 parent와 미제출 적격 기회를 각각 봉인하고, 정상 fail-closed와 원천/lineage 누락을 구분한다.
2. **ES1, 실행 형태 일치:** 후보 평가기가 probe-first child와 잔여의 실제 재검증·수량·가격·TTL 조건을 모델링한다. 런타임은 선택한 `operating_template`이 현재 probe/market-first 계약과 불일치하면 원래 full-size 주문으로 조용히 돌아가지 않고 **정책 비적용 사유를 기록하며 기존 승인된 안전 경로만** 사용한다. probe 시작 전 source 준비 조건을 만족하지 못하면 큰 잔여를 약속하지 않는다. one-share-only로 전환할 경우 목표 수량 자체를 사전 승인·기록하고 잔여 0으로 선언한다.
3. **ES2, 모델 검증:** 실제 제출/ACK/full·partial·no-fill/잔여 미제출/late fill 및 확인된 비용·terminal에 대해 가격·체결확률·잔여 실현율 예측오차를 검증한다. 실제 체결가를 미래 후보의 시작 가격으로 쓰거나, 1주 probe 결과를 전체 수량 성과로 확대하지 않는다. 미지원 scope는 후보 비교에서 제외하되 수량과 차단 사유는 보고한다.
4. **ES3, paired 선택:** 위 세 결과군을 동일 frozen 기회·목표 수량·가격 상한·hard guard·exit/cost·자본 조건에서 incumbent와 실행 가능한 분할 후보로 비교한다. 비용 후 attempt당 EV와 관측일당 순익, 실제 승리·실패·미진입 각각의 건수와 EV 기여, full/partial/no-fill·missed upside·winner retention·p10/tail을 calibration/시간순 독립 holdout에 출력한다. 실제 성공한 ENTER_NOW는 보존해야 할 양성 사례와 winner-retention 지표로 사용하되 승자만 복제·과가중하지 않는다.
5. **ES4, 정책/소비:** 유효 후보 또는 이유가 명시된 incumbent carry를 기존 entry split publisher와 dated PREOPEN 계약에 발행한다. source·model·holdout·policy hash, 유효 venue/session, 적용일, 실제 PID 소비를 각각 검증한다. 자연 제출·체결과 실현 수익은 배포 이후 별도로 관측한다.

### PD0–PD4: 판정 후 최초 제출 지연의 독립 튜닝축

**유형별 선택 계약:** 하나의 지연시간을 전 종목에 일괄 적용하지 않는다. 기계판정이 이미 사용하는 사전 관측형 `venue/session`, `price_tick_band`, `liquidity_band`, `volatility_band`를 지연 평가의 후보 구분 근거로 재사용할 수 있다. 지연 family는 이 값과 원본 시각·source hash를 **진입 의도 확정 시점에 동결**하고, 기계 정책의 selector/leaf 또는 임계치를 지연 정책으로 복사하지 않는다. 우선 `venue/session`별 0초 parent를 두고, 충분한 paired 원천이 있는 경우에만 tick 비율 또는 유동성·변동성 중 **한 번에 한 축**으로 분기한다. 가격대 자체와 시가총액은 당시 유효한 원천·표본·홀드아웃에서 독립적인 체결 차이를 보일 때만 후보로 추가한다. 시총 원천이 없으면 `UNKNOWN`으로 남기고 최신 시총을 과거에 붙이지 않는다. 표본이 부족하거나 시점·route 원천이 없는 leaf는 검증된 parent의 지연시간 또는 0초를 사용하며, 얕은 leaf의 1건 승리로 분기하지 않는다. 정책은 하나의 root+검증된 selector/leaf 묶음으로 발행하고, 각 leaf의 적격/제외 분모·0초 대비 비용 후 paired EV·승리 진입 유지율·시간순 holdout·fallback을 별도로 보고한다. 런타임은 동결된 유형으로 leaf를 고르고 대기 중 venue/session 또는 안전 계약이 바뀌면 그 intent를 취소한다. 유형별 이익을 합산해 기계판정·AI·분할 정책의 개선으로 계상하지 않는다.

현재 구현의 첫 유형 키는 `venue|session|price_tick_band`이며 `venue|session` parent로 내려간다. 유동성·변동성·시총은 이 시점에 검증된 값이 없어 `UNKNOWN`으로 기록하고 selector로 사용하지 않는다. 장후 보고서는 관측된 각 parent/leaf의 적격 건수와 후보별 quote coverage를 별도로 내고, 실행·완료·비용·시간순 holdout의 같은 분모가 닫히기 전에는 각 leaf를 명시적 0초 carry로 발행한다. 기존 대형 raw pipeline의 호가 존재 진단은 끝 64MiB만 읽으며 하루 전체의 부재나 체결가능성을 주장하지 않는다.

1. **PD0, 시간 원점:** 기계 `ENTER_NOW`와 실제 필요한 AI effective PASS/CAUTION 및 마지막 진입 guard가 모두 확정된 시점을 `decision_committed_at`으로 기록한다. 이 시점의 venue/session/route, 목표 수량, 현 가격 상한, BBO/depth와 AI 권한 시각을 동결한다. 이미 발생한 관측 지연을 정책 지연으로 합산하지 않는다.
2. **PD1, 가격·체결 원천:** 우선 기존 raw pipeline, 분봉 및 BBO/0D source를 **한 번만** 시간·종목·실행 route별로 색인해 재사용한다. 예컨대 9/23 크라우드웍스의 제출 직전 SOR 경로 ask 1,564원/잔량 1주와 약 2초 뒤 잔여 검증 ask 1,568원은 원본에 있다. 따라서 원천 부재를 일괄 선언하지 않는다. 원점과 0/30/60/120/180초에서 각 후보 시각에 맞는 신선한 **실제 매수 가능 ask·잔량·route·session·source timestamp**를 대조한다. 분봉은 30초 이상 후보의 방향·범위를 정하는 보조 자료이며, 분봉 저가나 나중의 holding/exit 호가를 해당 시점의 체결가로 대체하지 않는다. 이미 0초에 주문했어도 동일 기회의 뒤따른 원본 호가가 충분하면 재사용하고, 실제로 부족한 시점만 기존 WS cache의 bounded source-only 관측으로 보완한다. 별도 주문·provider 조회는 하지 않는다. 결손은 **종목·route·시점·필드별** `source_gap`으로 기록한다. ask 한 점의 가격 개선과 계획 수량 전체의 체결 가능성은 분리한다.
   - 9/23 13시대의 잠정 원본 점검에서는 실제 제출 9종목 모두에 제출 전후 호가 필드가 있었으나, 후보 시각 ±3초의 단순 필드 검색에서는 30·60초 0종목, 120초 1종목, 180초 3종목이었다. 이는 신선도·경로 검증 전의 **필드 존재 수**이며 체결 불가능 건수가 아니다. 일중 파일이 계속 자라므로 장후 봉인 원천에서 다시 계산한다. 1호가 잔량이 목표 수량보다 적다는 사실만으로 no-fill을 단정하지 않으며, 후속 호가 단계·체결·시장 이동의 불확실성을 모델과 결과에 남긴다.
3. **PD2, paired 경제성:** 실제 0초 진입의 승리·실패와 확정 intent의 미진입 기회비용을 같은 분모로 묶고 즉시 제출(0초)과 각 지연 후보를 비교한다. 각 시각에 **실제로 실행 가능했을** 가격·수량·체결확률을 재생하며 값싼 ask뿐 아니라 미체결, 가격 급등으로 놓친 성공 진입, partial fill, exit/cost와 자본 점유를 포함한다. 체결 기회가 관측되지 않은 후보는 싼 가격 체결로 간주하지 않는다. 비용 후 EV와 관측일당 순익 증가를 주 지표로, 원래 성공 진입의 유지율·tail·제출률을 guard로 둔다. 세 결과군별 실제/반사실 기여, 동일 분모, 보정 승률, 시간순 holdout과 모델오차를 공개한다.
4. **PD3, 런타임 소비:** 별도 `pre_submit_delay_policy` loader가 분할 정책과 무관하게 dated 지연 정책을 검증한다. 기존 메인 진입 handler의 **분할 적용 전** 공통 submit 경로에 versioned intent를 저장하고 비차단 monotonic timer에서 만료시킨다. 잠든 스레드, 신규 AI 호출이나 새 주문 경로를 추가하지 않는다. 1주·probe-first·다중 leg 모두 이 경로를 통과하되, 지연 만료 후에만 기존 분할 owner를 호출한다. 만료 시 AI freshness·quote/depth·route/session·가격 상한·확정 수량·broker/cooldown·hard guards를 다시 확인하고, 허용될 때만 현재 실행 가능한 가격으로 기존 제출 경로를 한 번 호출한다. 그 사이 verdict 변경, 보유/미체결/중복 parent, 정책 세대 변경, 마감·stop·재기동이면 intent를 취소하고 사유를 기록한다. 재기동 후 오래된 intent를 자동 주문으로 복원하지 않는다. 실패나 source gap을 즉시 주문으로 우회하지 않는다.
5. **PD4, 독립 발행:** `pre_submit_delay_tuning`은 자체 보고서·정책 파일·세대 hash·선택/disposition을 발행한다. 신규 지연 정책의 기본값은 0초다. 유효한 EV 우위가 없거나 model/holdout 결손이면 직전 **지연 정책만** 원래 expiry와 권한 범위 안에서 carry하고, 직전 지연 정책이 없으면 0초를 명시한다. 분할 정책 변경·발행·실패는 지연 정책 세대를 바꾸지 않는다. 정책 값만 있고 실제 loader/consumer가 없으면 완료로 보지 않는다.

PD는 **진입 여부 판정을 바꾸지 않는 제출 시각/가격 실행 정책**이다. 지연 중 최초 의도 수량·가격 상한을 높이거나 stale AI를 재사용하지 않는다. 승인된 다른 진입 및 hard guard의 authority를 침범하지 않는다. 30초~3분 후보의 재검증 시점에 기존 AI·기계 권한이 만료된다면 그 후보는 실행 불가능으로 격리한다. 권한 TTL을 늘리거나 새 AI 호출을 암묵적으로 추가하지 않는다. 분봉 저가만으로 30초/1·2·3분 뒤 체결을 가정하지 않는다.

## 5. 제출 뒤 취소 대기: 범위 유지

`DirectFamilySourceRepairEntryCancelWait`는 실제 제출 BUY parent의 ACK·full/partial/no-fill·cancel 요청/ACK·late fill·terminal/cost census 결손을 수리한다. 기존 `entry_cancel_wait_tuning`의 timeout 정책과 런타임 소비를 그대로 분리한다. 이 원천이 닫히면 기존 owner의 paired 경제성 평가를 재개할 수 있지만, 이번 메인 개선의 선행조건으로 묶거나 cancel-wait 값을 최초 BUY 제출 지연에 사용하지 않는다. 미제출 잔여를 실제 cancel 건수로 세지 않는다. [기존 cancel-wait 상세계획](./entry-cancel-wait-submitted-order-conditioned-paired-economic-tuning-and-runtime-consumer-improvement-plan-2026-09-18.md)은 이 독립 owner에만 적용한다.

## 6. 조건부 후속과 장후 인계: H0–H2

- H0: 동일 기회에서 `AI PASS` 이후 미제출 원인이 가격·stale/latency·liquidity·overbought 등으로 귀속되면 그 원인의 owner를 분리한다. `PD`는 **모든 진입 guard를 통과해 제출 intent가 확정된** 모집단만 평가한다. 정상 hard guard를 수익성 숫자만으로 완화하지 않는다. `machine_timing`은 `machine_attribution`의 별도 후행 stage이지 이 제출 지연축의 owner가 아니다.
- H1: 실제 체결 뒤의 holding/exit와 scale-in 결과는 해당 position/custody owner에서 평가한다. 현재 `scale_in_split`의 insufficient sample을 entry split의 EV0이나 주문 실패로 섞지 않는다. 출구 성과가 손실 원인이면 진입 AI의 false PASS로 자동 귀속하지 않는다.
- H2: family evaluator·publisher가 산출한 결과만 `runtime_approval_summary`가 직접 증거 상태로 투영한다. source generation이 바뀐 AI stage와 그 하류 terminal/strict verifier를 먼저 재검증한다. summary `complete`, stage `succeeded`, PREOPEN `verified`, PID 소비, 자연 제출·체결, 실현 순익은 각각 별도 receipt다.

동일한 원천 결손 때문에 무관한 family의 완료 stage를 다시 계산하지 않는다. ES와 PD는 압축 원천만 공유한다. 각자의 모델·holdout·정책·terminal이 독립이므로 한 축의 결손이나 성공을 다른 축의 완료·승격 근거로 재사용하지 않는다.

## 7. 검증·리뷰와 수용 기준

구현 순서는 **D0 exact 원천 봉인 → 분할 ES0–ES4와 지연 PD0–PD4를 독립 검증·발행 → 각 stage의 H2 인계**다. 공통 projection 준비만 공유하고 어느 튜너의 `selected`나 terminal도 다른 튜너의 선행조건으로 두지 않는다. CW census도 같은 projection을 재사용할 수 있으나 별도 분모/권한을 유지한다. 상류 기계·AI 정책 튜닝이나 cancel-wait EV가 완성될 때까지 두 실행축을 직렬 대기시키지 않는다. 특정 attempt의 실제 AI 권한 또는 완료 원천이 없으면 그 행의 해당 경제성 비교만 보류한다.

| 검증 축 | 최소 회귀와 수용 증거 |
| --- | --- |
| 원천·동일성 | exact attempt/revision, machine/AI component hash, source date/route/session, parent-child 수량·시각 보존; 같은 source를 두 정책 세대로 소급 재표기하지 않음. |
| 경제성 | 같은 frozen cohort/비용/자본·exit의 incumbent/candidate paired 결과, 독립 holdout, full/partial/no-fill과 실제/CF 분리, null 유지, tail·안전 veto. 실현 PnL·반사실 EV·모델 추정값의 분모와 불확실성을 따로 낸다. |
| 승격 판정 | 실행 가능한 같은 분모에서 비용 후 paired EV 및 관측일당 순익 차이가 개선되고, 독립 holdout이 방향을 뒤집지 않으며, 성공 진입 유지율·tail·source coverage와 hard guard가 악화되지 않는 후보만 선택한다. 표본/모델이 부족하면 `insufficient_evidence`, 동일 분모에서 우위가 없으면 `evaluated_no_edge`, 원천이 없으면 `source_gap`으로 분리한다. 단일 승자·최저 ask 한 점·소수 100% 승률은 승격 근거가 아니다. |
| 실패·재개 | late terminal/cost, 부분 파일, source correction, code/모델/비용 revision, 중단·중복 실행에서 현재 hash receipt만 재사용하고 영향받는 하류만 무효화. |
| 권한 | main BLOCK/RECHECK를 AI PASS로 승격하지 않음; stale/conflict·가격 신선도·브로커/계좌/주문/수량/cooldown·hard/protect/emergency·operator lock 유지. |
| 소비 | source→family별 evaluator→dated policy/기존 runtime bootstrap→PREOPEN→실제 PID의 정확한 component/hash·유효일 소비→자연 주문/terminal·cost, 이어서 current summary/checklist/strict verifier까지 exact generation 대사. 선택 release만 확인하고 장중 적용으로 표기하지 않는다. |

**정책 계약:** `entry_split_order_policy_v1`은 분할 전용으로 유지한다. 신규 `pre_submit_delay_policy_v1`은 별도 dated 파일과 env 선택자·schema·세대 hash·loader·PREOPEN receipt를 가진다. 지연 정책에 분할 leg·비율·offset을 넣지 않고, 분할 정책에 지연 초를 넣지 않는다. 두 정책은 각자 source/model/cost/holdout hash, venue/session, `source_date`·`effective_from`·expiry, 이전 **동일 축** 정책 hash, `metric_role=primary_ev`, `window_policy`, `sample_floor`, `primary_decision_metric=paired_net_ev_delta`, `source_quality_gate`, `forbidden_uses`를 기록한다. 지연의 `decision_authority`는 `next_preopen_bounded_pre_submit_delay_policy`로 분할 authority와 다르다. `diagnostic_win_rate` 단독 승격은 금지한다. 같은 메인 실행 경로에서는 한 번에 한 축의 live canary만 바꾸고 다른 축은 정확한 incumbent hash로 고정한다. 미지원 schema/날짜/route나 현재 runtime 세대와 다른 parent는 해당 축 신규 후보만 적용하지 않고, 지연은 0초/유효한 지연 carry, 분할은 기존 안전 경로로 각각 돌아가며 사유 receipt를 남긴다. 만료 carry를 유효하다고 합성하지 않는다. 두 stage가 각자 원자적 artifact 세대를 발행하고 bootstrap의 정확한 날짜·hash를 검증한다. 다음 적격 거래일의 장중에 소비 가능해야 하며, 장중 재발행·교체는 단일축 CAS와 현재 PID 소비 검증을 통과한 경우에만 허용한다.

**코드 경계:** 분할 보고서·후보·dated 정책은 기존 [`entry_split_order_plan.py`](../../src/engine/scalping/entry_split_order_plan.py)에 남긴다. 지연 평가기·정책 로더는 역할에 맞는 별도 `src/engine/scalping/pre_submit_delay_tuning.py`에 둔다. 이는 신규 튜닝축의 최소 소유 파일이며 엔진 root에 파일을 늘리지 않는다. 비차단 intent와 최종 submit 재검증은 기존 [`sniper_state_handlers.py`](../../src/engine/sniper_state_handlers.py)의 공통 제출 경로에 연결하되 `apply_entry_split_order_policy()` 내부로 넣지 않는다. [`runtime_policy_bootstrap.py`](../../src/engine/automation/runtime_policy_bootstrap.py)·[`postclose_summary_handoff.py`](../../src/engine/automation/postclose_summary_handoff.py)·[`runtime_approval_summary.py`](../../src/engine/runtime_approval_summary.py)에는 독립 지연 family의 필요한 날짜·hash·소비 계약만 추가한다. 기존 [wrapper](../../deploy/run_threshold_cycle_postclose.sh)에 별도 지연 stage를 등록하지만 cron과 주문 경로는 재사용한다. 자동화 규칙 변경이므로 운영 문서·현재 checklist를 같은 변경집합에서 갱신한다.

**장후 실행시간 계약:** 성장하는 JSONL을 후보별·축별로 재스캔하지 않는다. 기존 event cache/checkpoint의 offset·source hash로 공통 exact-attempt/짧은 quote 관측창을 한 번만 압축한다. 분할 evaluator와 지연 evaluator는 이 **읽기 전용 feature pack**을 서로 다른 필터·고정조건으로 소비하며 서로의 후보·결과·정책을 입력으로 쓰지 않는다. 각 stage는 wall/CPU/RSS·읽은 bytes·대상/제외 건수·cache hit와 source fingerprint를 별도 기록한다. 같은 source/cost의 재실행은 검증된 중간산출물을 재사용하고 late terminal 등 바뀐 parent와 각 영향받은 하류만 무효화한다. worker/IO 동시성·chunk 수·벽시계 시간은 장후 계산 슬롯 안에서 제한하고 초과 시 checkpoint로 중단·재개한다. 동일 source-date의 전후 실행시간과 반복 실행을 비교해 성능 저하를 검출한다. 장중에는 지연 축의 메모리 정책 조회·단일 timer만 추가하고 p95 결정→submit 및 이벤트루프 지연을 0초 incumbent와 비교한다. 진단 대상 축소 시 데이터 완전성·추천·사전 EV 가능성 순으로 고르되 **부분 표본을 전체 모집단의 승격 결과로 표시하지 않는다**. 공통 분모가 미완성이면 해당 축 source gap/carry를 낸다. 추가 provider 조회·장후 외부 AI 호출은 0건을 목표로 한다.

**최소 회귀:** 분할 테스트는 probe-first 운영 후보 비적용 시 full-size 주문 누출 방지, planned/submitted/filled/미제출 수량 보존, 기존 v1 정책 호환성을 검사한다. 지연 테스트는 0초 incumbent 동등성, 1주와 다중 leg 적용 범위, stale AI·quote conflict·venue 변경·중복 parent·restart·stop의 무주문, 같은 frozen split hash의 paired 경제성 및 winner 과가중 금지를 검사한다. 독립성 테스트는 한 축의 정책 파일·load 실패·source gap·새 후보가 다른 축의 정책/hash/결과를 바꾸지 않는지 검사한다. 여러 후보의 단일 source read·checkpoint 재개와 cancel-wait timeout 불변도 확인한다. 코드 수정은 구현→self review→보완→re-review→대상 pytest·compile·`git diff --check`로 닫는다. wrapper/자동화 규칙 수정과 함께 운영 문서·checklist를 갱신하고 `bash -n`·계약 검증·print-only parser를 실행한다.

## 8. 배포·롤백·성과 판정 경계

구현 완료 후에는 해당 source date의 **분할 stage와 신규 지연 stage를 각각** 재생성한다. `공통 source projection → (분할 보고서·정책) / (지연 보고서·정책) → 각자 runtime_approval_summary 인계 → strict terminal`의 source/hash·시간 순서를 확인하고 신규 지연 stage wall/CPU/RSS 및 분할 stage 성능 불변을 비교한다. 유의미한 EV 출력은 양수 후보를 강제로 만든다는 뜻이 아니다. 각 축의 적격·제외·보류 분모, 실제 완료 PnL, incumbent 비용 후 EV, 후보별 EV·차이·불확실성·winner 유지율 및 모델 오차를 내거나, 불가능한 항목은 정확한 first blocker와 owner를 **각각** 낸다. `EV=null`을 0 또는 no-edge로 대체하지 않는다.

검증된 code와 current source 계약을 immutable release로 인계하고 실제 scheduler/consumer를 확인한다. 장후 재생성 뒤 정책 적용과 매매 process 재기동은 해당 실행 범위의 권한·영수증에 따라 수행한다. 정책이 다음 장중 소비되었음을 주장하려면 정확한 bootstrap 정책 hash·effective date·선택 release·PID receipt와 자연 판정/intent/submit 사건을 대조한다. source/수량/안전 또는 지연 성능 회귀 시 이전 release·정책으로 되돌리고 실패 원본을 보존한다. 정상 source gap·표본 부재·평가된 no-edge만으로 다른 family를 OFF/ON하지 않는다.

완료 보고는 family별 `결정 → 증거 → 다음 행동`으로 정리한다. 최소한 원천 적격·제외/보류 분모, 비용 후 paired EV·관측일당 순익 차이, 후보·발행 상태, 실제 PID 소비, 자연 제출/부분·전체 체결/청산, 비용 차감 실현손익을 분리한다. Counterfactual 개선이나 한 건의 잔여 주문 회복을 실현 순익 개선으로 표시하지 않는다.

## 9. 기존 owner 문서

- [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md): clean baseline, family 권한, 비용·경제성 및 정책/실현 분리.
- [기계 전체 장후 폐루프](./main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md)와 [보조 AI 양방향 평가](./auxiliary-ai-opportunity-error-tuning-runtime-implementation-plan-2026-09-22.md): 각자 독립 모집단·source/holdout·publisher 계약.
- [Entry split 상세계획](./entry-split-order-plan-submitted-order-replay-and-economic-tuning-improvement-plan-2026-09-18.md), [cancel-wait 상세계획](./entry-cancel-wait-submitted-order-conditioned-paired-economic-tuning-and-runtime-consumer-improvement-plan-2026-09-18.md), [TES 잔여 주문 원천 사례](./probe-first-residual-liveness-tes-repair-plan-2026-09-23.md): 기존 실행/경제성 owner의 상세 계약.
- [장후 stage 분리계획](./machine-postclose-runner-separation-implementation-plan-2026-09-22.md), [직접 증거 인계계획](./runtime-approval-summary-direct-evidence-handoff-optimization-plan-2026-09-19.md): 독립 stage와 마지막 소비자 계약.
