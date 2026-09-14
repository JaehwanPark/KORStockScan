# 기계 ENTER + compact AI 보조심사 장후 구현·리뷰

기준 시각: `2026-09-14 17:48 KST`
구현 지시: [통합 workorder](../proposals/machine-compact-auxiliary-postclose-implementation-workorder-2026-09-14.md)
권한: 장후 source/report/선정/publisher/consumer 자동화 보완. 현재 PID·수동 env·주문·threshold·hard safety 변경 없음.

## 1. 판정

코드 구현과 검토 범위는 `PASS`, 자연 성과와 다음 PREOPEN/PID 소비는 `OPEN`이다. 장중 frozen 정책이 compact가 아니거나 compact 자연 호출이 없으면 그 날짜의 legacy 결과를 compact 성과로 섞지 않고 incumbent compact를 유지한다. 장후 결과는 exact compact partition과 비용후 성숙 경로가 있을 때만 다음 거래일 등록 prompt variant 선정에 영향을 준다.

## 2. 최초 결함과 보완

| WP | 최초 결함 | 보완·현재 판정 |
| --- | --- | --- |
| WP0 | 선택 release는 compact v3 코드이나 현재 PID는 이전 release에서 시작해 당일 frozen prompt를 소비 | 현재 PID 불변. 새 코드는 20:10 장후와 다음 PREOPEN 경로만 대상으로 함 |
| WP1 | 서로 다른 compact generation 또는 한 손상 scope가 섞이면 전체 측정을 막는 전역 gate | `version×venue×session×machine bundle` partition, exact issued prompt hash/variant, partition ID와 독립 allowed 상태를 추가. 정상 partition만 #82로 전달 |
| WP2 | `20 호출 + missed-VETO/dangerous-PASS 건수 차이`가 비용·성숙·분모 차이를 반영하지 않음 | `compact_auxiliary_economic_selection_v2`로 교체. 비용후 경로와 PASS/VETO별 분모·rate·tail·경계 도달시간을 분리하고 결측을 null/제외로 보존 |
| WP3 | legacy R0–R3 독립 selector 연구가 compact 보조심사와 같은 역할처럼 보일 수 있음 | #80에 legacy=`offline_independent_selector_prompt_research_only`, compact=`machine_enter_post_selection_risk_adjudication`를 명시. 자연 compact 평가는 Provider replay로 합성하지 않음 |
| WP4 | publisher/consumer가 단순 aggregate를 신뢰하고 새 경제성 보존식·source hash를 검증하지 않음 | source manifest와 경제 outcome hash를 publisher가 재계산하며 consumer·strict verifier가 역할/schema/hash/권한을 검증 |
| WP5 | #119/#23에 machine-primary funnel과 legacy recheck 경계가 이미 존재 | 재검증 결과 patch 불필요. machine RECHECK/BLOCK은 legacy #23 eligible로 올리지 않고 ENTER→AI→final guard→broker accepted 분모 유지 |
| WP6 | compact/legacy 역할과 다음 날짜 자동선정 상태가 consumer·runtime summary에 독립 표시되지 않음 | #80 handoff와 runtime summary에 역할·selection·source/economic hash·자동 publisher·현재 PID 미주장을 명시. strict verifier가 필수 receipt 결손을 실패 처리 |
| WP7 | 현재 장중 PID에 새 postclose 코드를 즉시 반영하면 frozen 실행을 바꿈 | 현재 PID 재기동 없음. 검증 commit을 새 immutable release로 배포하고 설치 route의 다음 자연 owner가 소비하도록 함 |

## 3. 확정한 자동선정 계약

- 원천: #74의 exact incumbent compact partition만 사용한다. 다른 버전·scope·bundle·prompt hash 손상은 해당 partition만 제외한다.
- 경제 분모: 비용 계약, `net_target_first|exact_stop_first`, 경계값이 모두 있는 unique machine ENTER + AI PASS/VETO만 포함한다. 호출 수·미성숙·비용 결손은 floor를 채우지 않는다.
- 기본 floor: 경제적 유효20건, 선택 방향의 분모5건, 해당 오류3건, 오류율25% 이상, 반대 오류율보다10%p 이상 높음.
- tail: 비용후 counterfactual PASS 손실이 -1.0% 이하인 material tail이 하나라도 있고 PASS 분모5건이 있으면 risk-specificity variant가 우선한다. 이는 한 큰 손실을 다수의 작은 이익 건수로 가리지 않기 위한 제한이다.
- 분모0: rate는 `null`; all-PASS/all-VETO를 0% 오류로 보간하지 않는다. 충분한 방향별 근거가 없으면 carry한다.
- 권한: selector는 등록 compact variant만 다음 거래일 bundle로 자동 발행한다. 자유문구 생성, 기계 threshold·수량·가격·주문·hard safety 변경 권한은 없다. 수동 사용자 승인은 요구하지 않는다.
- rollback/carry: source 미관측과 source 손상을 구분한다. 미관측은 정상 carry, 손상은 해당 partition 제외/carry다. 현재 날짜 bundle과 PID는 불변이다.

이 조건은 모든 horizon·5/10/20일 동시 gate나 후보 적용 전 실체결을 요구하지 않아 과도한 무기한 차단을 피한다. 반대로 호출20건만으로 바꾸지 않으며, 비용후 작은 순익 빈도와 큰 tail 손실을 같은 단위에서 함께 본다.

## 4. 오늘 자연 원천 읽기 전용 점검

17:45 KST 시점 #74 입력을 새 계약으로 읽었고 파일·정책·Provider를 쓰지 않았다.

- machine capture 2,960: BLOCK 1,758 / RECHECK 1,172 / ENTER_NOW 30.
- entry screen trace 4,604: provider called 95 / not-called 4,509. AI 미호출을 Provider 실패나 AI VETO로 세지 않았다.
- exact snapshot/bundle/action join 2,957, action mismatch 3은 격리 대상이다.
- compact 자연 trace 0: 현재 장중 PID의 frozen 세대가 compact가 아니므로 `not_observed_on_source_date`, `measurement_allowed=false`가 정상이다.
- 비용후 machine case 0: 당일 장후 economic reference가 아직 없어서 2,957건 모두 `full_round_trip_cost_missing`이며 값을 0이나 gross target으로 보간하지 않았다.
- 따라서 successor는 compact v3 carry이고 오늘 이 읽기 전용 점검만으로 opportunity/risk variant, 수익 개선, 현재 PID 적용을 주장하지 않는다.

## 5. 예상 효과와 별도 acceptance

예상 효과는 (1) 과거/손상 source의 전역 차단 감소, (2) 비용 없는 호출 건수 기반 과잉 전환 제거, (3) missed-profit VETO와 dangerous PASS의 서로 다른 분모 공개, (4) 작은 비용후 이익을 보존하면서 material tail을 우선 억제, (5) legacy R0–R3 결과가 compact runtime 선택을 오염시키지 않는 것이다.

이는 코드 계약의 기대 효과이며 실제 이익 증명은 아니다. 다음 자연 compact generation에서 `prompt_version/variant/system prompt hash/machine bundle`, 경제 유효 분모, 자동 selection/carry, next-date bundle, PREOPEN 선택, PID first-use, accepted submit/fill/terminal과 비용후 순익을 순서대로 확인한다.

## 6. 리뷰·검증

- P0~P2 unresolved finding: 0 (본 변경 범위).
- 반례: 정상+손상 compact partition 혼재, compact 미관측, 비용 유효2/호출20, all-PASS 분모0, semantic invalid, material tail 1건, source/economic hash 변조, 기존 frozen migration/carry.
- targeted pytest: 관련 source audit/calibration/publisher/consumer/verifier/live-policy/funnel/recheck/runtime summary 724건과 runtime/replay prompt parity 69건 PASS.
- Python compile, formatter, `git diff --check`, 문서 링크/print-only parser를 최종 commit 전에 재검증한다.
- Provider 호출, 실주문, 현재 PID 재기동, 20:10 producer 조기 실행은 수행하지 않았다.
