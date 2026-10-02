# 10/2 장후 정책 생성 결과 점검

점검일: 2026-10-03 KST. 원천일: 2026-10-02. 적용 예정일: 2026-10-06. Artifact snapshot: 07:12:39 KST. 사용자의 단회 결과 점검 요청에 따른 읽기 전용 대사다.

판정: 상위 실행 영수증은 정상 종결이다. 개선 검증을 통과한 신규 후보는 0건이며 원천/비교 결손에 따른 기존 정책 승계가 주 결과다. 가격 패턴은 부분 분석, holding vote는 estimated provisional로 구분한다. 생성 당시 PASS였던 10/6 격리 준비본은 현재 체크리스트 세대가 바뀌어 재검증 FAIL이다. 실제 PREOPEN/PID/수익 개선을 주장하지 않는다.

## 실행과 현재 세대

- 공통 selector/native run: `63936cf18127cea77f074c56b4c5689a109445c9`, run `09e8cc2fcb144d9b81c1ccbf5c2cb82a`. Native `succeeded` 10/3 00:10:20, strict `pass` 00:53:56, controller `done` 00:54:25다. Stage terminal 15개는 succeeded 13개, 명시 OFF 2개다. OFF는 Episode 연구와 공동 research allocation이며 기존 Episode 매매 정책을 OFF로 표시한 것이 아니다.
- Runtime summary는 `direct_evidence_complete`, `validated_edge_count=0`, `policy_candidate_count=0`이다. 10개 경제성 projection은 source_gap 3, mixed 1, not_applicable 6으로 기록됐지만 이 일반 분류를 활성 cancel-wait/제출 지연 분석의 건강성 증명으로 사용하지 않는다.
- 37개 직접 산출물/경로를 읽기·streaming hash로 대사했고 summary가 기록한 기존 파일의 물리 SHA 불일치는 0건이다. 이것은 원천 분석 완결이나 새 정책 효과의 증명은 아니다. [대사 snapshot](../../tmp/postclose-policy-generation-result-review-20261003/artifact-snapshot.json).
- 10/3 현행 daily checklist는 없으며 이전 항목으로 현재 실행 권한을 대체하지 않았다. 다음 적용 인계는 [10/6 checklist](../checklists/2026-10-06-stage2-todo-checklist.md)에 있다.

## 최우선 결손: 현재 준비본 재검증 실패

10/6 `readiness.json`은 10/3 00:54:41 `prepared_verified`로 생성됐다. 현재 선택 실행본에서 `verify_prepared('2026-10-06', generation_only=True)`를 읽기 전용 호출하면 다음 finding으로 FAIL이다.

```text
postclose_controller_not_closed:strict_checklist_generation_stale,strict_generation_changed_during_recheck
```

Strict가 기록한 checklist SHA는 `e6d9f08dae68ad342638b9cf3360339ef676cecbb65cbed9e5af7dc9a364e4b0`, 현재 값은 `c3f570a4531166b47b2e5671bc8cb7412ae74c35938cddc9f3239246a4e49377`다. 이후 코드 리뷰·인계 기록을 추가한 checklist의 전체 bytes가 바뀌었다. 따라서 이전 PASS/DONE/준비 영수증은 생성 당시의 근거이며 현재 준비 완료를 증명하지 못한다.

같은 선택 실행본에서 기존 direct 경로의 `verify_summary_handoff(..., require_tower=False)`는 PASS다. 정책·summary source marker 결속과 전체 checklist physical SHA 결속을 구분해야 한다. [재검증 원 결과](../../tmp/postclose-policy-generation-result-review-20261003/revalidation.json).

소유자/다음 조치: 기존 `summary_handoff`·strict/controller·next_preopen_readiness owner가 최종 checklist를 고정한 다음 현재 세대 strict/controller와 10/6 준비본을 같은 release/source로 최소 갱신·재검증한다. 경제 producer/raw/전체 wrapper를 반복 재실행하는 문제는 아니다. Closure: 현행 checklist SHA와 strict 일치, controller 현재 세대 검증 및 prepared sealed-generation PASS. 이번 결과 점검에서는 영수증 재작성·재생성·배포·재기동을 실행하지 않았다.

## 정책별 결과

| 정책/논리 owner | 생성·분석 결과 | 원천/경제성 판정 | 직접 소비·다음 경계 |
| --- | --- | --- | --- |
| Main 승률 `main_machine_policy` | `incumbent_carried`; 입력 7,069, accepted 2,975. Train 9/29·9/30, holdout 10/2 | successor holdout 날짜·적격 후보/selected sample 부족. 새 승률 후보 없음 | 10/6 dated Main 정책 승계. 다음 적격 train/holdout과 정확 parent로 재평가 |
| Full Main 전략 `legacy_machine_report` | full evaluation complete, candidate 0 | `machine_operating_population_unbound`, 비용 후 paired EV/null | Main 정책은 보존. 동일 운영 모집단/owner replay가 필요한 source gap이며 단순 날짜 대기로 종료하지 않음 |
| Compact `main_auxiliary_policy` | stage succeeded, `source_contract_blocked`, incumbent preserved | `exact_stop_distance_missing_or_invalid`; paired 0·source day 0 | 같은 Main 부모의 10/6 dated 정책. 정확 stop/owner/cost 원천 확보 뒤 family 평가 |
| `pre_submit_delay` | 새 `pre_submit_delay_price_pattern_v1` 부분 분석. 기회 28, 지연별 가격 비교 17 | 실제 체결·청산 없이 가격 분석을 수행함. Scope 혼재, 공통 learning pair 0·validation pair 0; 추천 null. 별도 경제 모델은 미검증 | 가격 연구 report-only. Runtime 지연 정책 unselected, apply false. 동일 scope의 검증 quote pair가 다음 경계 |
| `entry_cancel_wait` | 10/6 incumbent preserved: 90/120/600/1200초, scope override 없음 | 당일 제출 0과 과거 대사를 구분해야 함. 기존 보고서에는 9/30 제출·취소 관련 8 events가 있지만 source counts는 10/2만, parent 0. 새 historical ledger가 없으므로 과거 미해결 0을 수용하지 않음 | 작업본 보완 코드가 선택 실행본과 다름. [기존 동일 ID](../proposals/entry-cancel-wait-source-reconciliation-remediation-plan-2026-10-02.md)의 새 계약 generation/직접 소비 수용은 OPEN |
| Initial entry split | 보고서·보존 정책 작성, 새 후보 0 | `operating_paired_source_missing`, source gap | 기존 주문 형태 보존. Same-capital 운영 paired 원천·독립 모델/holdout이 필요한 owner 과제 |
| Scale-in split | v4 보존 정책, `skipped_no_actual_fill` | 실제 적용 fill 0, paired 0; valid skip, EV null | 10/6 기존 주문 형태. 다음 적격 actual ADD fill/완료 revision이 조건부 평가 trigger |
| 초기 수량 | 기존 current 정책 유지 | source 9/23·effective 9/24의 receipt를 준비본이 결속. 이번 새 수량 개선으로 집계하지 않음 | 기존 initial_quantity owner/PREOPEN receipt 유지 |
| Low-price two-leg | 후보 문서 작성, 경제성 후보 0·incumbent preserved | profile별 valid_empty와 source gap 혼재, `profile_source_gap` | 적격 profile만 평가하고 HELD/manual/actual custody 분리. Gap profile의 원천 결속이 종료 조건 |
| Widget | 연구 complete, live selected 0·withheld 100, `observation_only` | 신규 signal policy candidate 없음. Observation catalog loader 비교 PASS | 10/6 observation policy/catalog 인계. Observation 등록을 live admission으로 표시하지 않음 |
| Episode / 공동 allocation | `off/explicit_schedule_disabled` | 현재 연구 OFF에 따른 valid skip | 기존 Episode 실제 매매/applied 정책과 분리. 신규 공동 자본 정책 없음 |
| Machine timing | `source_quality_blocked`, `baseline_immediate_entry_carry_forward` | 원천 readiness 결손, 새 timing winner 없음 | 10/6 baseline staging. 정확 source-ready cohort가 필요, ETA 미확정 |
| Market weakness | `current_policy_carried_forward` | 신규 hysteresis 개선 선정 아님 | 기존 정책/원 source 결속 보존. 다음 적격 owner 증거로 갱신 |
| Collector / legacy approval | `no_qualified_candidate`·기존 PREOPEN/승계 승인 인계 | Source/watch 추천과 live 자본/정책 선정은 별개 | Collector/approval native owner 유지, 새 collector/주문/자본 권한 없음 |
| Rising missed | `valid_empty/hold_valid_empty`, incumbent preserved | paired 0·source day 0; 새 개선 EV 없음 | 10/6 보존 정책. 원 source 없는 행을 0 EV로 합성하지 않음 |
| Holding path vote | 10/6 bundle 15 cells, `estimated_provisional`; 준비본에 결속 | provisional 판단 모델이며 realized paired EV KRW null | 기존 provisional owner의 별도 loader·PREOPEN/PID 수용. 검증된 신규 순익 개선 후보로 합산하지 않음 |

## 제출 지연 가격 패턴의 실제 결과

| 지연 | 비교 수 | 기회 28 대비 coverage | 평균 가격 개선 bp |
| --- | ---: | ---: | ---: |
| 0초 기준 관측 | 5 | 17.86% | 0 |
| 30초 | 5 | 17.86% | 0 |
| 60초 | 4 | 14.29% | 0 |
| 120초 | 4 | 14.29% | 1.29852 |
| 180초 | 4 | 14.29% | 1.29852 |

17은 양의 지연별 pair 합계이며 고유 체결 수가 아니다. 120/180초 각각 개선 1·악화 1·동일 2, 중앙값 0이다. 검증 가능한 0초 quote가 없는 기회 23개는 제외된다. 관측 pair의 가격은 모두 frozen price cap 초과로 표시돼 실행 가능 fill/PnL로 해석하지 않는다. Scope별 common learning·validation pair 부족 때문에 `recommended_delay_sec=null`이다. “더 기다리면 유리한 가격이 관측되었는가”의 진단과 runtime 정책 선정을 분리한 정상 보존 결과이며 EV가 0이라는 판정은 아니다.

## 소비·운영 한계

10/6 PREOPEN·Main PID·자연 주문/비용 후 성과는 아직 도래하지 않았다. 준비본의 17 `selected_families`는 기존 baseline/guard/override 합성 목록이며 이번 장후 신규 후보 17개가 아니다. 실제 적용 예정 family의 정책/차단 값·retirement guard는 기존 exact-date PREOPEN이 소유한다.

현재 direct 전체 strict는 `require_tower=False`이며 공통 tower는 이번 native 생성 경로에 없다. 그 부재만으로 기존 전체 장후 실행을 실패로 바꾸지 않는다. 새 cancel-wait 작업본이 요구하는 전용 tower/checklist/semantic 수용은 기존 direct 전체 PASS와 별개이고 아직 관측되지 않았다. 운영 보고서에는 새 reconciliation contract도 없다. 파일 존재·이전 PASS를 새 계약 적용으로 수용하지 않는다.

읽기 전용 점검과 결과 문서·link/owner·print-only parser 검증만 수행했다. 테스트/경제성 replay/AI·Kiwoom API/notification 발송/외부 sync는 실행하지 않았다. 새로운 코드 수정·현재 정책 변경·배포·재기동 또는 OFF 연구 복원은 없었다.
