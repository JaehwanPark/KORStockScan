# 최초 수량 유형 기본정책 릴리스 선택 — 2026-09-27

## 결정과 범위

최초 정책 생성에는 기존 정책 대비 우월성·독립 holdout·초 단위 후행저가를 요구하지 않는다. 2026-09-23까지 클린 베이스라인 이후 완료된 메인 최초 실거래 387건과 익절 244건의 실현 순이익 원화 가중 후행 1분봉 원천을 결속한 정책 후보에서, 6개 유형 모두 부모 5단계 수량·기존 주문 형상·기존 프로필 시간을 선택했다. 이 **행동 동등 초기 기본정책**만 새 정책 세대로 활성화했다. 연구용 원본 후보는 `runtime_apply_allowed=false`로 보존했다.

선택 정책은 `data/runtime/initial_quantity/current.json` → `initial-quantity-baseline-17c98ba548db.json`이다. 정책 파일 SHA256은 `dcd937b4015eb0869a38ce4ff3d2ffc62baf2933b9a63668ba2c993e90c52e39`, current 내용 SHA256은 `49e02aadfa61c50321e869421cdbe4bb0a503e4b77d110f068364404ee953ed7`다. 정책의 `effective_from=2026-09-24`는 최초 효력 하한이며 매일 만료되지 않는다.

## 리뷰·검증

- 별도 불변 코드 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-baseline-20260927-3e57a9db`, commit `3e57a9dbd8c45f0e672cf8e1999e2febb2a8b592`를 생성했다. 원 작업공간의 다른 미커밋 변경은 그대로 두었다.
- 자체 리뷰에서 malformed 유형 정책이 런타임 예외를 낼 수 있는 문제를 찾아 정확한 schema/키 계약으로 거절하도록 고쳤다. 현재 유형 정책 행을 수량 결정 전에 조회하고 `quantity_type_policy_row`를 영수증에 남긴다. 현재 값과 다른 형상·총시간·수량 상한 완화는 초기 정책 발행에서 차단한다.
- 릴리스 복사본에서 영향 테스트 109건 통과, Python compile·Ruff·`git diff --check` 통과. 이전 작업공간의 전체 영향 집합 119건도 통과했다. 문서 print-only parser는 `InitialQuantityBaselinePid0928` 단일 OPEN 소유자를 확인했다.
- 실제 387건 stage를 사용하는 임시 9/28 장전 manifest/env 생성 및 verifier는 PASS, findings 0이다. 27개 수량/시장/가격 입력에서 기존값과 새 정책의 tier·ratio·effective_qty·binding cap 불일치는 0건; 정책 로더 중앙값 0.0781ms/판정, 실제 stage 장전 결속 8회 중앙값 0.08초였다. 원 장후 전수 재생·후행 수집·시간 연구 성능은 [구현계획 §12–§13](../proposals/scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md)에 기록됐다.

## 선택 영수증과 남은 수용

- 2026-09-27 KST에 메인 릴리스 selector만 새 commit으로 원자 교체했다. 직전 선택 `1f69eb1c6bdc63723aa3b26628e025d2167121fa` 영수증은 `tmp/runtime-release-selection-before-initial-quantity-20260927.json`에 보존했다. `--check-release-set` PASS, cron 8개 경로 PASS, 9/28 `preopen --print-plan`이 새 릴리스로 향한다.
- 선택 당시 메인 PID는 없었고 `actual_pid_consumed=false`다. 9/28 자연 PREOPEN terminal→manifest/env 검증→실제 PID의 정책 파일/SHA→첫 `quantity_type_policy_row`를 순서대로 대사해야 한다. 실제 주문·체결·비용 후 EV는 그 뒤의 자연 영수증으로 판정한다. 릴리스 선택이나 print-plan만으로 이를 PASS 처리하지 않는다.
- 새 `T/n` 순차 dispatcher, broker cancel terminal bridge, 유형별 변경된 분할·총시간, 정규 장후 후속 정책 갱신은 이 **초기 행동 동등 릴리스의 적용 범위 밖**이다. 기존 주문 안전 경로와 프로필 시간을 유지한다. 후속 변경은 별도 코드 리뷰·수량 보존·취소 최종 확인·재시작 복구·장후 성능 및 비용 근거를 닫고 나서만 적용한다.
