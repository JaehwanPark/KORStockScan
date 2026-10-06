# 과거 v2 장후 증거와 최종화 복구 — 2026-10-06

## 대상과 원인

- 대상 원천일은 `2026-10-02`, 원 적용일은 `2026-10-06`으로 고정한다. 10/6 15:05 최종화 재시도는 `predecessor_terminal_failure`; 실제 정리는 15:09:46 별도 DONE이다.
- Widget 퇴역의 v3 전환이 과거 완료 v2 영수증의 읽기까지 차단했다. 두산 고정감시의 새 코드 해시 구성도 과거 Main 기계 단계에 소급되어 원 코드 증명과 불일치했다.
- 기존 strict 영수증은 이후 체크리스트 수정으로 `strict_checklist_generation_stale`이다. 과거 PASS를 현재 PASS로 그대로 재사용하지 않는다.

## 보완 계약

1. 독립 producer 완료 조회, 요약, strict 소비자는 clean baseline 이후의 `source_date <= publication_date < 2026-10-06`인 v2만 읽을 수 있다. digest/run/date/code/output/input/prerequisite 검증을 모두 유지한다. producer의 새 실행, cache 재사용 및 `--check`는 v3를 요구한다.
2. 과거 Main 코드 구성은 관리되는 원 immutable release의 dispatcher와 원래 계산 모듈 해시에 대조한다. 새 고정감시 파일 세 개가 과거 구성에 없었다는 차이만 인정한다. 새 v3 단계는 세 파일도 계속 검증한다.
3. 복구 시 summary 영수증이 현재 계약에 맞지 않으면 현재 dispatcher로 `summary_handoff`만 재계산한다. 원 v2는 attempts에 보존한다. 기계·AI·에피소드 정책 및 capacity 원천 producer는 재실행하지 않는다.
4. 이후 native controller가 summary/tower/checklist/strict를 갱신하고 현재 단계 세대를 검증한다. 정리와 최종 detector, source/snapshot/attempt 해시가 확인된 뒤에만 원 날짜 finalization DONE을 발행한다.
5. 과거 적용일의 PREOPEN 07:35가 지났다면 복구는 `preopen=not_applicable_historical_recovery`다. 과거 자료로 다음 날짜 준비를 생성하지 않는다. 정상 예약 최종화는 원천에 대응하는 정확한 적용일을 명시한다.
6. 당일 정책 보존 재기동의 원 PREOPEN manifest와 새 PID 검증은 서로 다른 코드 release를 가리킬 수 있다. 장후 소비자는 기존 native intraday handoff의 frozen 파일, 명시 권한, 현재 날짜/selector, consumed 영수증, 현재 Main PID/start ticks/cwd와 canonical 검증을 대조한다. 모두 일치할 때만 `intraday_preserved`로 연결하며 원 manifest의 release 이름을 바꾸지 않는다. 변경된 정책·이전 PID·인계 미소비·다음 날짜는 이 경로에서 거부한다.

## 실행 및 수용

- 기존 승인 범위: cleanup 실패 및 연결된 완료 절차 보완; reviewed immutable 배포와 당일 정책 보존 handoff. 주문·정책 값·provider·cap·custody·다른 에피소드 PID 변경 없음.
- 리뷰 → 보완 → 관련 회귀/compile/bash/diff → print-only parser가 통과한 뒤 immutable release를 반영한다. 실행 중인 기존 run은 코드나 원천을 교체하지 않는다.
- 최종화는 native owned-log runner, immutable root, `2026-10-02 --recover-closed-target`으로 실행한다. 요약 전 선행 단계가 실패하거나 원본 해시가 바뀌면 실패를 유지하고 해당 원천 owner를 점검한다.
- 수용: 12개 선행 영수증과 정책 원본 해시 불변, 새 summary v3/strict/controller DONE, native cleanup 실패 0, 최종 detector run/report hash와 chain/snapshot hash, 최종화 DONE. 이후 오류 탐지의 `postclose_finalization_status=recovered_late` 및 fail 해소를 확인한다.
- 지연 완료를 06:50 기한 준수로 표시하지 않는다. 10/7 정상 기동과 10/6 자연 장후 성공은 기존 `FixedWatchBudgetSummaryPostcloseAcceptance1006` owner에서 별도 확인한다.

## 운영 증거

- 실행·테스트: `tmp/postclose-finalization-contract-recovery-20261006/`.
- 이전 정리 복구 및 정책 보존: [기존 감사](../audits/fixed-watch-source-delay-and-cleanup-remediation-review-2026-10-06.md).
- 현재 실행 owner: [10/6 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)의 `FixedWatchSourceAndCleanupRepair1006` A5.
- 1차 수정 `72716b6c`, native Main PID `25432`, 당일 bootstrap/PID PASS. 15:40 복구는 선행 검증을 통과한 뒤 요약 소비자의 `future_preopen_generation_stale`에서 실패했다. 단순 selector 교체로 원 manifest 소유권을 증명하지 않았으며, 위 6번의 native 인계 소비 계약을 후속 보완했다. 원 실패 영수증은 보존한다.
