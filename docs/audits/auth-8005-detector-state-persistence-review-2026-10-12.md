# 8005 감시기 상태 저장 결함 리뷰 — 2026-10-12

**알림은 15:06:36 상태 JSON 읽기 실패이며, 15:07:54 정상 회복했다.** 16:03:45 운영 health artifact에서 `kiwoom_auth_8005_restart`와 `process_health`는 PASS다. PID 1020707은 선택 릴리스 `auxiliary-consumption-attestation-20261012-v1`에서 실행 중이며, 상태 JSON을 읽을 수 있고 restart.flag는 없다. 이 점검은 직접 인증 요청을 호출한 결과가 아니다. [현재 근거](../../tmp/auth-detector-state-repair-20261012/current-evidence.json)

## 원인과 수정

기존 `_save_state`는 공유 상태 파일을 `Path.write_text`로 직접 덮어쓴다. 봇 daemon과 cron이 같은 파일에 접근하지만 cron wrapper의 lock은 daemon을 직렬화하지 않는다. 따라서 저장 중 불완전한 JSON을 읽을 수 있고, 읽기→검사→cursor/restart counter 저장의 동시 갱신도 충돌할 수 있다. 당시 예외 종류/손상 bytes는 남지 않아 실제 알림이 경합, 파일 손상, 읽기 I/O 중 무엇이었는지 확정하지 않는다.

- 상태 JSON을 먼저 직렬화하고 같은 디렉터리의 고유 임시 파일에 flush/fsync한 뒤 `os.replace`한다. 기존 파일 권한을 보존하고 실패한 임시 파일은 정리한다. 기존 원장을 복제하거나 세대별 상태 이력을 새로 누적하지 않는다.
- daemon/cron 공통 상태 파일의 별도 OS lock으로 전체 상태 거래를 직렬화한다. 최대 2초 대기 후에도 busy이면 warning과 무변경 상태를 남기며, 인증 정상이나 복구 성공으로 표시하지 않는다.
- dry-run은 상태/lock/flag/token을 변경하지 않는다. 기존 과거 로그 제외, 실제 새 오류, retry 성공, cooldown/일일 재기동 cap은 유지한다.
- JSON root/파일 cursor/restart counter와 인코딩 오류를 검증하고, 다음 경고에는 예외 종류·JSON 행/열·OS errno만 남긴다. 손상 원문/인증 값은 기록하지 않는다.

## 리뷰·검증

저장 교체 실패 시 이전 JSON 유지, 임시 파일 정리·기존 권한 보존, 손상 형식/인코딩의 과거 로그 미스캔, 동시 검사 시 복구 1회와 counter 1회, busy/dry-run 무변경을 검증했다. 기존 detector/engine/admin 알림 회귀를 함께 실행하여 **84건 통과**했다. 기존 wrapper가 이미 바꾼 lock 안내 문구와 테스트 기대값의 불일치 1건도 바로잡았으며 exit 75 계약은 유지했다. [테스트 로그](../../tmp/auth-detector-state-repair-20261012/pytest.txt)

공식 `Kiwoom-Securities/Kiwoom-REST-API` HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 원격으로 재확인하고 동일 commit의 `kiwoom/core/auth.py`, `client.py`, `token_store.py`, `kiwoom/specs.py`를 확인했다. 정확 조회 시각은 현재 근거에 기록했다. 해당 tree에는 `kiwoom_docs`가 없다. 이번 수정은 감시기 로컬 상태 저장이며 인증 wire/request·응답 해석·WS/REST 호출은 변경하지 않았다.

기존 봉인 checklist는 수정하지 않았다. 앞선 native 신호 보완의 후보 checklist를 승계한 [통합 후보](../../tmp/auth-detector-state-repair-20261012/2026-10-12-stage2-todo-checklist.md)에서 기존 `Auth8005HistoricalReplayRepair1012`에 새 결함 범위를 추가하고 이전 완료 증빙을 유지했다. baseline 운영 문서와 다른 미커밋 작업은 보존했다.

코드리뷰 범위의 미해결 결함은 없다. 이번 수정은 **작업본에만 반영**됐고 배포·재기동·토큰 무효화·restart.flag 생성은 실행하지 않았다. 실제 알림은 기존 운영 코드의 다음 검사에서 먼저 회복한 것이므로 새 코드 적용 효과로 주장하지 않는다. [완료 영수증](../../tmp/auth-detector-state-repair-20261012/completion.json)
