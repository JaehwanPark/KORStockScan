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
7. 장후 읽기 검증은 별도 검토된 immutable report root에서도 현재 Main의 native handoff를 대조할 수 있다. `prepare`와 `consume`의 selected cwd·PID 요구는 유지한다. 요약 실패가 같은 요약을 필요로 하는 기동 guard까지 차단할 때는 현재 Main selector/PID를 유지한 상태에서 별도 report root의 native `summary_handoff`만 먼저 완료한다. 정상 요약 증명 이후 새 release의 정책 보존 handoff와 최종화를 실행한다.

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
- 후속 `999ee899`의 기동 사전 검증은 이미 실패한 요약의 holding-vote 원천 검증에서 중단됐다. 재기동하지 않았으며 selector를 `72716b6c`로 원복했다. 원 정책 파일과 현재 PID는 유지했다. 원 prepared 세대에 봉인된 summary/controller를 canonical에 복귀시킨 시도도 `summary_handoff:code_changed`로 검증 실패했다. 원복된 과거 controller의 DONE은 현재 최종화 성공으로 사용하지 않는다. 실패 canonical은 `failed-controller-before-sealed-rollback.json`과 `failed-summary-before-sealed-rollback.json`에 보존한다. 위 7번의 독립 report owner로 정상 요약을 재생성한다.
- 독립 report 실행 `eeccb1f4`의 첫 시도는 `main_machine_policy:code_changed`에서 차단됐다. 10/5 16:05 원 기계 단계는 삭제된 `designated-machine-policy-20261005-3d0e5106` 경로의 코드에 결속되어 있었다. Git 원 커밋 `3d0e5106`을 그 경로로 복원하여 원 해시 `90e05fddf53cb08ba9a2aa19d4255da483154312f75a78b3e4c38d4be2c537ca`와 대조했다. 정책 재생성이나 과거 영수증 수정 없이 12개 선행 단계가 모두 검증됐다. 이 root는 원 정책 코드 증명 의존성이므로 보존 대상이다.
- 16:04:34 독립 native summary `6f8f01b92a12412a907476006566ce09` succeeded; 현재 holding-vote/bootstrap 읽기 검증 PASS. 첫 수정의 400 PASS, 인계 소비자 보완 444 PASS, 독립 읽기 경로 최종 94 PASS, compile/bash/diff/print-only parser PASS를 확인했다. 정상 최종화 결과는 아래 별도 완료 증거로 판정한다.

## 최종 복구 결과

- `eeccb1f4127a39d7454c8bb464f1018cb4365812` 반영 후 16:05:35 Main PID `60572`의 singleton/root/bootstrap 및 native intraday 소비 PASS. 원 정책·입력·선행 영수증·PREOPEN 등 보호 파일 30개와 holding-vote 원 파일의 SHA는 모두 동일하다.
- 16:08:30 native cleanup DONE, 16:08:38 native `postclose_finalization` 및 `postclose_final_detector` DONE. 대상 source=`2026-10-02`, 원 적용일=`2026-10-06`을 유지했으며 10/7 PREOPEN을 생성하지 않았다.
- controller DONE/whole chain strict PASS, 현재 선행 12개+summary 검증 결손 0. chain=`2ffd804360a6c73ec5b0b861245aebbe934a7b5012b5f5d9214620d26a22d6f7`; snapshot=`de8c7a024a0ad4b385fda97148f5e1043fdc6e3161eb981ecbd12f7b081bf112`; final detector run=`cron-20261006T160830-105951`/SHA=`326e7abfb046fbdc1033ffc2f5f7a513469ecace742c96234445c5859d427c55`.
- 완료 뒤 16:09:24 native full 탐지 및 16:10:07 재관측에서 FAIL 0, Main process health PASS, 두 job 모두 `recovered_late`. 오전 06:50 기한 초과 경고는 유지한다. Machine/auxiliary 운영 경제성·plan/label 원천 및 Episode producer 변경의 기존 warning도 보존하며 이번 완료로 해결된 것으로 표시하지 않는다.
- 상세 증거와 검증 범위: [완료 리뷰](../audits/postclose-finalization-contract-recovery-review-2026-10-06.md), `tmp/postclose-finalization-contract-recovery-20261006/after.json`. A3 자연 판정 및 10/6 자연 장후·10/7 기동 수용은 현재 OPEN owner에서 별도로 확인한다.
