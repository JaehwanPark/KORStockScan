# 최초 수량 정책 장후 원천 수리 릴리스 선택 — 2026-09-27

## 결정

메인 선택 릴리스를 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-refresh-20260927-538bad38` (commit `538bad38af6095c41928316ef90469bfd5b366ff`)로 갱신했다. `data/runtime/runtime_release_selection.json`이 정확한 선택 영수증이다. 직전 선택은 `3e57a9dbd8c45f0e672cf8e1999e2febb2a8b592`이며 백업은 `tmp/runtime-release-selection-before-initial-quantity-refresh-20260927.json`에 보존했다.

범위는 클린 기준 이후 완료 거래의 장후 갱신 전수, 익절 후행 원천, 같은 census의 타임아웃 연구, 주문 attempt·수량 판정 정책 SHA 계보, 해당 날짜 stage의 summary/strict 결속, 정수 초 시간표 연구 코드다. 9/28 PREOPEN 읽기 전용 manifest는 기존 초기 정책 파일 SHA `dcd937b4015eb0869a38ce4ff3d2ffc62baf2933b9a63668ba2c993e90c52e39`를 유지했다. 유형별 변경 수량·분할·총시간은 발행하거나 선택하지 않았다.

## 리뷰·검증

- 격리 릴리스 테스트 219건 통과. 패키징 재검토에서 신형 테스트와 구 시간표 모듈의 불일치를 발견해 정수 초 시간표 모듈을 포함하고 재실행했다. Python compile, 변경 SCALPING 모듈 Ruff, wrapper `bash -n`, `git diff --check` 통과. 기존 `postclose_summary_handoff.py`의 Ruff 스타일 위반 37건은 변경 지점 밖이어서 범위를 넓혀 수정하지 않았다.
- 실제 9/27 자료의 완료 거래 0건은 `carry_parent`로 source-only terminal을 발행했고 validator와 summary source receipt가 통과했다. 내부 측정은 재생 0.356초, 타임아웃 연구 0.002초, peak RSS 약 129MB다. 거래 387건·익절 244건의 전체 원모수 비용 수정 재생은 [별도 성능 영수증](./2026-09-27-initial-quantity-cost-contract-rereplay.json.txt)의 367.075초·154,960KB와 동일 코드다. 첫 거래가 생기는 정규 9/28 장후 전체 체인과 외부 후행 API 냉·온 성능은 아직 실측하지 못했다.
- 선택 후 `--check-release-set` PASS, cron 8개 경로 PASS, 9/28 `preopen --print-plan`이 새 commit을 가리킨다. 선택 시 메인 PID는 없고 `actual_pid_consumed=false`다. release/PREOPEN 라우팅은 자연 주문·체결 또는 비용 후 성과의 증거가 아니다.

## 남은 변경 정책 경계

새 순차 `T/n`의 실제 BUY 호출·취소 요청·broker/owner/계좌 terminal·재시작 복구, 유형별 단일 수량×분할×시간 정책의 publisher/current CAS와 로더는 이 릴리스에 없다. `initial_quantity_terminal.py`의 정확 주문 종료 증명은 작업공간의 격리 구현이며 live dispatcher가 호출하지 않는다. 해당 기능을 검증하기 전에는 변경 정책을 선택하지 않는다. 상세 소유자는 [구현 계획 §18–§21](../proposals/scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md)과 9/28 체크리스트의 `InitialQuantityClosedLoop0928`이다.
