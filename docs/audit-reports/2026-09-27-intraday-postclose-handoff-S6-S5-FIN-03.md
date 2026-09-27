# 장중 생산자–장후 소비자 S6 수리 보고서 — S5-FIN-03 strict·체크리스트 세대 결속

실행일: 2026-09-27 KST. 인계: [S5 전체 체인](./2026-09-27-intraday-postclose-handoff-S5.md) `S5-FIN-03`, [S6 압축 원천 수리](./2026-09-27-intraday-postclose-handoff-S6.md), [S6 capacity 수리](./2026-09-27-intraday-postclose-handoff-S6-S5-FIN-01.md). 범위는 stage terminal → runtime summary → 다음 체크리스트 marker → strict attempt → controller DONE → finalizer의 같은 세대 검증이다. 기존 9/23–9/28 산출물은 읽기만 했고 정규 작업은 실행하지 않았다.

## 결정·재현 증거

9/23의 15개 등록 stage 가운데 `summary_handoff`를 제외한 14개 terminal이 체크리스트 원천이다. 9/28 체크리스트의 `POSTCLOSE_SUMMARY_SOURCES`는 runtime summary와 14개 stage 파일 SHA, 총 15개를 기록한다. 현재 파일을 다시 해시하면 **9개 불일치**다: `runtime_approval_summary` (`217322260aab…` → `ecd8024afbd7…`), `collector_recommendation` (`671921fc1073…` → `9d6d9ebe432f…`), `legacy_policy_approval` (`94af41f12ef5…` → `a3f10711aba4…`), `machine_attribution` (`ef7b85b54c83…` → `64b414df533d…`), `machine_timing` (`56614c1c9439…` → `b47409516266…`), `market_weakness` (`6257e09e8973…` → `f0f18727fb51…`), `research_allocation` (`450f57a8dee3…` → `c76511ea82e2…`), `research_capacity` (`d3201f6beeb9…` → `2052e9afebc5…`), `widget_policy` (`166a49e1e8a9…` → `7cf54f667313…`). 나머지 6개는 일치한다. 원인은 summary 재작성과 각 stage의 후속 attempt가 체크리스트 marker를 갱신하지 않은 채 남았기 때문이다. 이는 파일 존재나 9/28 체크리스트의 생성 이력만으로 현재 세대를 인정할 수 없음을 보여준다.

저장된 [9/24 strict PASS](../../data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-23.json)는 `verification_scope=main_terminal`, `whole_native_chain_done_claimed=false`, `summary_handoff.sha256=217322…`이다. 당시 main 봉인 영수증으로 보존한다. 현재 전체 체인 PASS로 읽으면 안 된다. 기존 attempt는 새 `generation_binding`이 없어 현재 세대 검증에서 `strict_receipt_missing_or_invalid_generation`으로 분류된다. 새 코드의 **읽기 전용** 전체 체인 검증은 `fail`: `postclose_summary_handoff:checklist:source_generation_mismatch`, 체크리스트 task projection 불일치, `widget_policy`·`episode_policy`의 작업본 대비 `code_changed`, `research_capacity:failed`, `research_allocation:deferred`를 확인했다. widget·episode의 `code_changed`는 이 작업본/릴리스 검증 상태이며 별도 family 결손으로 수리 범위를 넓히지 않는다. 9/23 summary_handoff terminal도 `failed` 그대로다.

## 수리·세대 계약

| 경계 | 수리 결과 |
| --- | --- |
| stage → marker | 기존 체크리스트 생산자의 15개 SHA marker를 유지한다. strict 전체 체인 검증은 14개 생산 stage 각각의 source/publication/effective date, run ID, terminal·receipt SHA, 입력·출력·prerequisite SHA, status를 스냅샷하고 `stage_receipt_issues`로 계약을 검사한다. `summary_handoff` stage와 controller는 자기 참조를 피하려고 strict 입력에서 제외한다. |
| summary·marker → strict | 새 strict attempt의 `generation_binding`에 source date, main run·terminal SHA, summary SHA, checklist SHA, 14개 stage identity/SHA를 기록한다. 검증 도중 summary·terminal·stage·checklist가 바뀌면 실패한다. `main_precommit`/`main_terminal` 범위는 그대로 보존하고, controller의 전체 체인 요구에는 별도 `whole_native_chain` 범위와 모든 stage 검사를 요구한다. |
| strict → controller·finalizer | controller는 독립 producer 검증, 전체 체인 strict PASS 및 새 attempt의 현재 세대 재검증이 모두 통과해야 `done`을 기록한다. 그 외 PASS는 `summary_verified`에 머문다. controller 영수증은 strict attempt 경로·SHA·main run을 보존한다. finalizer는 controller attempt 동일성, strict attempt의 소유 경로·SHA·run·현재 summary/checklist/stage 세대와 현재 전체 계약을 다시 확인한다. |

실패·deferred stage는 전체 체인 PASS를 막는다. 명시적 `OFF`는 유효 terminal 영수증이 있을 때만 허용된다. valid-empty는 기존 stage별 output 계약을 통과해야 하며 누락·실패의 대체값이 아니다. stage 재시도나 summary·체크리스트 재작성 뒤 과거 strict attempt는 그대로 보존하고 새 동세대 strict attempt를 요구한다.

## 실패 재현 → 구현 → 리뷰·검증

먼저 추가한 회귀 2개는 기존 코드에서 `require_whole_native_chain` 인자 부재로 실패했다. 구현 후에는 실패 stage와 현재 marker의 조합이 전체 체인 strict를 차단하고, 저장된 strict attempt가 summary 또는 stage 재작성을 stale로 판정한다. 추가 회귀는 유효한 명시적 OFF 영수증 집합의 동세대 수용 → 실패 재시도 거절 → 새 marker·strict 수용과 controller의 `main_terminal` PASS 승격 거절, finalizer의 strict attempt SHA 변경 거절을 검증한다.

자가 코드리뷰에서 main terminal 세대와 strict attempt 소유 경로가 빠진 것을 찾아 보강했다. 재리뷰에서 검증 중간의 세대 변경, DONE 직전 재검증, finalizer의 저장 attempt 재확인을 확인했다. 기존 wrapper 순서 fixture는 synthetic controller만 작성하므로 strict 영수증 검증도 명시적으로 mock하도록 보완했다. 실제 검증 함수의 SHA 변경 거절은 별도 controller 단위 테스트에 남겼다.
이 묶음의 코드·fixture 리뷰에 남은 미해결 결함은 0건이다.

| 검증 | 결과 |
| --- | --- |
| `test_verify_threshold_cycle_postclose_chain.py`, `test_postclose_done_controller.py`, `test_postclose_summary_handoff.py`, `test_build_next_stage2_checklist.py` | **163 passed** |
| `test_postclose_finalization.py`, `test_threshold_cycle_wrappers.py` | **35 passed**. 첫 실행에서 synthetic controller에 strict attempt가 없어 성공 fixture 1건이 실패했고 fixture의 검증 경계를 수정한 뒤 재실행 통과 |
| 변경 Python 파일 `py_compile` | 통과 |
| 문서 링크·owner·권한, print-only backlog parser | 연결된 세 보고서 존재; parser 통과, 미완료 parsed 31건, 외부 sync 없음 |
| `git diff --check` | 통과 |
| wrapper `bash -n`·변경 wrapper 계약 | wrapper 수정 없음. 기존 finalization/wrapper 계약 테스트 35건 통과 |
| 9/23 현재 파일의 읽기 전용 전체 strict 3회 | 5.028·4.821·4.818초, 모두 `fail`/결손 6개. 새 controller의 DONE 직전 재검증과 finalizer 검증은 이 읽기 비용을 추가하므로 S7에서 cold/warm 전체 체인 시간을 측정할 것 |

## 남은 경계·인계

실제 9/23 capacity `failed(run=254f2077…)`, allocation `deferred(run=1931beff…)`, summary_handoff `failed(run=d6bfce76…)`와 controller 차단은 변경하지 않았다. 두 앞선 S6 수리는 미배포 작업본이며, 이 수리도 선택 릴리스·PID나 자연 terminal 수용 증거가 아니다. `S5-FIN-04`의 다음 PREOPEN pointer·PID 결속, `S1-COM-01-A` scanner 압축 reader, S7의 성능·동세대 자연 chain, S8의 릴리스·실제 PID 수용을 각각 후속 owner로 유지한다. 현재 KST 9/27 일일 체크리스트 파일은 없고 9/28 체크리스트만 존재한다. 이 문서는 그 부재를 과거/미래 체크리스트로 대체하지 않는다.

실주문·정책·서비스·provider·threshold·정규 장후작업·PREOPEN·배포는 변경하거나 실행하지 않았다.
