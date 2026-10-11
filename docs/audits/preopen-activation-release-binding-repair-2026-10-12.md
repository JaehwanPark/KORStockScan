# PREOPEN 기계정책 릴리스 연결 보완 — 2026-10-12

## 직접 원인

07:10 경보의 정리·최종화는 이후 native DONE으로 회복했다.07:30:26 최종화와07:35:11 정기 감시에서 recovered_late warning만 남았다. 오전 source12의 장후 계약은 아직 생성 대상이 아니며 source8→target12가 실제 계약이다.

07:35 PREOPEN은 준비 검증 PASS 이후 실제 기계정책 활성화에서 `v6_activation_release_mismatch`로07:35:33 실패했다. target12 후보는 `70945c53181320d9149ed95167c1e21a42be23d2`에 묶였지만 선택은 `5f9309222d837baf7227edcc8b4b60ff85bdfef1`이었다. 준비 검증이 후보 bytes는 확인해도 활성화가 요구하는 릴리스 동일성은 확인하지 못했다. [원 실패](../../tmp/preopen-candidate-release-repair-20261012/preopen-original-failure-excerpt.txt).

## 최종 구현과 권한

- next_preopen_readiness에서 실제 dated v6 후보의 release·bundle·file hash를 봉인하고 준비와 재검증에서 대조한다. generation-only 검증은 봉인 hash를 확인하며 full 준비는 native source/code validator를 실행한다.
- 오늘의 아직 닫히지 않은 장후 source를 전 영업일 prepared 실패로 중복 표시하지 않는다.
- 명시 승인된 실패 복구 lease는 당일 failed terminal, live bootstrap 없음, 현재 날짜 machine activation 없음, live Main 없음, native PREOPEN 독점잠금과 실패 terminal hash가 필요하다. running/succeeded/activated/hash 변경·경합은 거부한다. 원 handoff owner의08:05 기한은 유지하며 복구 lease는 당일 프리장 첫 진입 window가 닫히는08:40까지 별도로 제한한다.08:05 이후 완료는 늦은 복구로 보고한다.
- native v6 identical-policy code refresh는 원/부모 불변 릴리스 검증 및 후보 SHA CAS를 통해 등록·threshold·auxiliary 내용과 원 source/effective day를 보존한다. 준비 중 active pointer는 변경하지 않는다. 후보의 큰 immutable generation은 native family owner가 관리하고 metadata CAS는 기존 원 계약을 유지한다. 실패하면 known successor SHA·active pointer를 대사하고 원 후보 exact bytes를 복원한 다음 기존 준비 전체 PASS를 검증한다. unknown successor를 덮어쓰지 않는다.
- PREOPEN 상태 기록을 독점잠금 이후로 이동한다. 잠금 경합 소비자는 로그만 남기며 원 failed/running/succeeded terminal을 덮어쓰지 않는다. 실제 busy subprocess에서 Python 호출과 상태 bytes 변경이 없음을 검증했다.

[운영 계약](../runtime-release-routing.md)을 함께 보완한다. source/EOD/실거래 원장·retired-owner 수동관리·기존 트레일링/제출지연 정책을 보존한다. native PREOPEN 재실행과 Main 실제 기동 영수증이 각각 실제 activation/consumption을 증명한다.

## 보완 과정과 검증 범위

공유 metadata journal/budget 보완 시도는 기존 제출지연 및 트레일링 연구의 전체 code contract를 바꿔 native closure가 거부했다. 세 번의 인계 실패에서 전체 metadata를 rollback하고 원 준비 current_full_contract PASS를 확인했다. 해당 부수 변경과 상대경로 validator 보완은 이번 최종 배포에서 제거했다. source-code contract를 단순히 새 SHA로 치환하지 않았다. native 제출지연 재생성 시도도 rollback됐으며 원 정책 bytes를 최종 대사한다. [거부·원상복구 근거](../../tmp/preopen-candidate-release-repair-20261012/).

확장 검증413회와 wrapper 보완47회를 수행했다. 최종 최소 수정본은 workspace와 불변 release에서 관련 표적 회귀를 다시 수행한다. 중복 검사를 합산하지 않는다. 실제 선택·native PREOPEN·최종화·Main PID 및 최신 경보 결과는 후속 근거로 구분하고 기존 DirectFamilyPreopenPolicyHandoff 단일 owner에 연결한다. 경제성 개선이나 자연07:55 완료로 확대하지 않는다.

## 최종 배포·실행 근거

- 최종 릴리스 `preopen-candidate-binding-20261012-v4` / `29118f4754e05c5672e6caaa48d736771cf27d6a`. 최종 최소 수정본 workspace와 불변 릴리스 각각377 passed이며 동일 묶음을 합산하지 않는다. runtime 코드 exact bytes를 대사했고 canonical test EOF 정리는 같은 AST임을 검증했다.
- [정식 CAS](../../data/runtime/research_release_transition/preopen_activation_binding_repair_20261012_v4/transition.json)는 verified. staged 후보와 원 후보의 거래/보조 payload가 동일하고 원 active pointer는 실제 PREOPEN 전까지 유지됐다. 원 EOD·수량·제출지연 policy bytes와05:35 실제 cron 예약은 보존했다.
- native PREOPEN은 **08:11:03 succeeded**.07:55 예약은 인계 보호 상태에서 실제 Main을 기동하지 못했으며 **08:20 정상 기동 경로로 복구**, 현재 PID **230886**, `ubuntu`, cwd는 새 릴리스의 `src/`다. [actual PID/bootstrap 검증](../../tmp/preopen-candidate-release-repair-20261012/live-pid-bootstrap.json)은 PASS다. 이 결과를 자연07:55 완료로 보고하지 않는다.
- 기동 이후 누적된 보조판정 오류는 새 bundle에 맞는 reader compatibility receipt 부재였다. origin 불변 릴리스의 reader5개 exact SHA와 기존128 scope의 registry definition/binding을 검증하고91 fixture 요청/형식 동일성 비교 및 invalid response 거부 동일성을 확인했다. 기존 native compatibility issuer로 source-bound 영수증을 보완했다. [근거](../../tmp/preopen-candidate-release-repair-20261012/auxiliary-reader-source-repair.json). 별도 provider 호출·정책 변경은0이며 원 반복 오류 마지막은08:34:07이다.
- **08:42 최종화 native exit0/DONE**. [완료·검증](../../tmp/preopen-candidate-release-repair-20261012/completion-verification.json)에 실제 marker와 chain/snapshot hash가 있으며 generation issues0이다. Source8→target12의 prepared 참조는 당일 PID 소비 metadata와 최신 controller를 대사해 source-only 재봉인했다. env values·live env·live manifest·policy bytes는 그대로다. [재봉인](../../tmp/preopen-candidate-release-repair-20261012/post-preopen-source-reseal.json)의 검증은 **sealed_generation PASS**이며 별도의 current PREOPEN completion/PID bootstrap PASS와 구분한다.
- 최신 read-only 검사에서 `cron_completion` fail 없음, `process_health` PASS다.06:50 이후 완료이므로 cleanup/finalization recovered_late warning을 보존한다. 원 next_preopen_prepared_contract_invalid 및 미완료 marker 경보는 현재 재현되지 않는다.

## 별도 잔여 경고

holding_exit_sentinel의 report as_of는 초 단위, v2 semantic as_of는 같은 시각의 마이크로초 단위라 소비자의 exact timestamp 비교가 `semantic_v2_generation_or_state_invalid`를 만든다. 당일 source_generation과 valid_empty는 일치한다. 이 별도 producer/consumer 정밀도 결함은 이번8개 코드 수정 범위에 포함하지 않았으며 현재 warning으로 남는다. 새 경고를 원03개 경보 또는 broker/API 장애로 집계하지 않는다. 후속 보완은 producer의 동일 as_of 사용과 precision/날짜/상태 회귀, 새 릴리스 연계가 필요하다. 현재 owner 조회는 미해결로 보고한다.

Project/Calendar 외부 sync는 수행하지 않았으며 print-only parser와 변경 문서 링크를 검증했다. [최종 readonly 세부](../../tmp/preopen-candidate-release-repair-20261012/final-readonly-detectors.json).
