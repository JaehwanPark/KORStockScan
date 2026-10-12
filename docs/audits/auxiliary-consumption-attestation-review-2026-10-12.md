# 보조판정 인계 소비 증빙 후속 리뷰 — 2026-10-12

Owner: `OrderedIntradayDeploymentRepair1012`. 사용자가 코드 리뷰·수정보완·배포·재기동을 승인했다. 이 작업은 Main 기동/배포 증빙 계약을 보완한다. 거래 정책·5초 기한·주문/보유 수동관리 경계는 유지한다.

## 근거와 결함

- 11:35:10 감시의 신규 오류 16건은 `auxiliary_base_code_handoff_missing`이다. 해당 사유의 당일 기록은 11:27:33–11:42:27 총 1,398건이다. 예외 하나가 인계 검증 실패·소비 증빙 결손·PID 불일치·해시 불일치를 함께 표현하므로 역사 로그만으로 세부 실패 조건을 확정하지 않는다. [원본 대사](../../tmp/historical-alert-1135-followup-20261012/completion.json).
- 준비 영수증은 이미 배타적 생성(`open('x')`)을 사용한다. 기존 준비 영수증 덮어쓰기를 이번 결함으로 단정하지 않는다.
- 런처가 native PID 소비 기록 실패를 무시하고 일반 selector PID 등록을 진행할 수 있었다. 일반 PID 등록은 cwd 기반 배포 provenance여서 보조판정 소비 증빙을 대체하지 못한다.
- 배포 완료 검사는 bootstrap PID와 일반 handoff를 각각 검증했으나 consumed 영수증이 바로 그 새 PID/start/cwd 및 manifest에 연결됐는지 직접 검사하지 않았다.
- 운영 문서 앞부분에는 기존 PID 종료보다 selector 변경을 앞세우는 구 안내가 남아 있었다.

## 수정과 재리뷰

1. 기존 startup automation 모듈에 읽기 전용 `verify_pid_consumption`을 추가했다. CLI `--verify --pid`가 consumed schema/status/date/release, 정확한 PID/start/cwd, handoff/manifest 해시를 검증한다. native bootstrap과 보조판정 reader 검증 뒤 PID·selector·영수증·PREOPEN·env·manifest의 변경을 다시 확인한다.
2. 코드 인계가 없는 원래 PREOPEN 기동은 원래 selected commit과 실제 PID bootstrap이 모두 맞아야 통과한다. 다른 릴리스의 인계 파일 결손을 native 기동으로 대신 통과시키지 않는다.
3. 런처는 bootstrap → consume → exact-PID verify 성공 후에만 selector PID 등록을 수행한다. 실패 시 경고를 남기고 성공 등록을 생략한다. 증빙 실패 자체로 강제 종료나 정책 제어를 추가하지 않는다.
4. 순차 배포는 실제 successor PID를 인계 검증에 전달하고 마지막 PID/selector 안정성을 확인한 뒤에만 `complete`로 기록한다. 기존 detector 잠금과 이전 Main/supervisor 종료 선행 순서를 유지한다.
5. 운영 문서의 구 수동 순서를 현재 순차 배포 절차로 정리했다. 오늘 체크리스트 수정은 후보 Git에 먼저 준비하고 이전 PID 종료 후 배포기가 게시한다. 기존 장후 OPEN owner는 보존한다.

## 검증과 종료 경계

- 직접 회귀: 소비 결손/변조, 다른 PID 및 재사용 start ticks, 검증 중 PID·selector·receipt·manifest·PREOPEN·env 변경, native PREOPEN의 commit 구분, 실제 bash의 단계별 실패와 selector 등록 생략, 배포 완료 차단.
- 관련 회귀 대상: 인계·순차배포·런처·라우터·최종화 세대·cron·artifact 감시기. 정확한 결과와 소스 검증은 [검증 로그](../../tmp/auxiliary-consumption-attestation-repair-20261012/pytest.log)에 기록한다.
- Python compile, `bash -n`, `git diff --check`, 문서 링크/owner 및 print-only parser를 확인한다. 외부 문서 동기화는 실행하지 않는다.
- 코드 검증과 실제 적용은 구분한다. 최종 릴리스/PID, native 검증, 기존 정책 원본 해시, 자연 감시 결과는 [배포 완료 증빙](../../tmp/auxiliary-consumption-attestation-repair-20261012/completion.json)에서 확인한다. 증빙 검증 PASS가 AI 응답·주문·성과를 증명하지는 않는다.
