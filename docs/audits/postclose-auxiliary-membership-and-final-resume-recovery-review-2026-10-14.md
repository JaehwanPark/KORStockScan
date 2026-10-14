# 10/14 장후 보조 집합·최종 인계 복구 구현 리뷰

Source/publication `2026-10-14`, effective `2026-10-15`. Base `43a79e569215c0c373554a9e1aae7ec7572a5db5`. 사용자 지시의 실패 보완·최소 재실행과 다음 기동 준비 점검 범위다.

## 판정과 보완

- 원 Main `76c3731bfb234bb4ba13e47e177165e1`은 `7c517c920`에서 EOD 대기 중 시작됐다. 승인된 후속 선택 `43a79e569`와 active-policy reader root가 달라 기계/legacy/보조 단계에 `active_policy_code_reader_root_changed`가 발생했다. 원 실패 영수증·로그를 data/runtime/postclose_recovery/2026-10-14 아래 보존하고, 기계·legacy만 현재 release에서 재실행해 정상 종료했다. 원 지연·라벨·수량·exit snapshot·stop 계산은 재실행하지 않는다.
- 현재 release의 보조 재실행은 `auxiliary_tuning_machine_membership_changed`를 냈다. `J.apply_selection`의 승인된 whole-variant 선정으로 집합이 달라졌지만 `T.prepare`가 초기 등록 변경 외의 차이를 거부한 producer/consumer 결함이다. 검증된 native parent에서 manifest/cells를 재구성하고 native selector를 다시 적용해 manifest·cells·selection·basis가 모두 정확히 같을 때만 수용한다. 신규 scope/variant/authority, 변조·원천/parent 불일치는 계속 거부한다. 기존 캠페인·예산·raw 응답은 보존한다.
- 원 Main은 partial summary/checklist 뒤 scoped strict exit 2로 21:52:49 실패했다. 기존 final resume가 이전 scoped-resume proof만 허용하는 결함을 보완했다. `normal` 원 run의 실제 완료 command receipts가 모두 있어야 하며, 다른 regeneration/reuse, 부족 prefix, 다른 commit, changed source는 거부한다. 모든 native stage·exit snapshot·수량 terminal의 검증을 그대로 요구한다. 이전 scoped ancestry는 원 hash/ID로 유지하며 새로운 이전 복구를 합성하지 않는다.

## 리뷰·검증

Implementation → self review → 보완 → re-review: 위 두 결함의 producer/consumer와 stale/missing 입력·원천 identity·권한·budget/custody를 검토했다. 현재 native parent와 실제 10/14 machine-comparison의 정확한 선정 재현 PASS. 검토 범위의 미해결 코드 finding 0; 운영 종결은 후속 native receipts로 별도 확인한다.

- `pytest -q src/tests/test_reversal_auxiliary_tuning.py src/tests/test_joint_reversal_source_repair.py::test_registration_exact_delta_native_publisher_and_dated_handoff`: 30 PASS. 실제 native family/selector와 fixture Store를 사용한 준비 수용, parent/receipt/definitions/nongroup/cells/metrics/authority/source 변조 거부, provider attempt 0 및 동일 캠페인 재사용을 검증했다.
- `pytest -q src/tests/test_threshold_cycle_wrappers.py`: 57 PASS. 완전한 normal prefix 수용 및 partial/reuse/다른 commit/누락 command/변경 source 거부, 기존 scoped ancestry·저장·wrapper 경계를 검증했다.
- 관련 compile, `bash -n`, `git diff --check`: PASS.
- native 계약 33 파일과 정책 payload/현재 pointer는 불변이다. 기존 검증된 native parity는 동일 parent·33 SHA·621 confirmation hits·mismatches 0으로 source-only code handoff에 재사용하며 새 PID/주문/성과 증거로 표시하지 않는다.

## 권한과 후속 종결

새 모듈·cron/서비스·패키지·Main 재기동·수동 env/lock/provider/threshold·주문/취소·가격/수량/cap·retired consumer 권한은 만들지 않는다. 기존 approved custody profile을 native router와 동일하게 전달한다. 단일 실패 보조 producer → 최종 summary/tower/checklist/strict/controller → exact 10/15 prepared readiness를 확인한다. 기동 준비와 미래 PREOPEN/PID·자연 주문·비용 후 성과는 별도다.

운영 결과는 [전수 점검 기록](postclose-monitoring-and-next-session-readiness-2026-10-14.md)에 후속 기록한다. 05:35 최종화·07:35 PREOPEN·07:55 기동의 실제 예정 상태는 완료로 합성하지 않는다.
