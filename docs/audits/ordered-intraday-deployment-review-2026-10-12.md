# 장중 배포 순서 재발 방지 — 2026-10-12

사용자의 배포 순서 보완·반복 코드리뷰·배포·재기동 승인을 따른다. 기계/보조 정책·5초 기한·보유/수량/주문 보호조건은 유지한다.

## 원인

- 12:08:00 새 selector가 먼저 발행됐고 이전 PID 727995가 12:08:49까지 실행됐다. `auxiliary_pid_release_mismatch` 78건은 72건과 6건으로 나뉘어 알림에 잡혔다. 새 PID 761193 기동 이후 같은 오류는 관측되지 않았다.
- 12:06:39 공유 체크리스트 편집과 새 인계 소비 사이에 기존 최종화 관찰이 `strict_checklist_generation_stale`를 냈다. 역사 체크리스트 관찰 자체는 현재 문서 변경을 허용했지만, 내부 bootstrap의 delay/holding 코드 검증은 다시 일반 인계 검증을 호출해 현재 문서를 요구했다.

## 구현과 권한

신규 CLI의 위치는 `src/engine/automation/ordered_intraday_deploy.py`다. 실제 진입/주문 코드가 아닌 기동 자동화 소유 기능이며 engine 루트나 별도 임시 배포 구현을 추가하지 않는다. 테스트는 기존 `src/tests`에 둔다.

1. 불변 후보는 기존 router와 같은 검증기를 통해 선택 전 검증한다. 사용자 확인 문자열, 현재 날짜, source cleanliness, 공유 경로, 퇴역 기능 부재와 이전 singleton PID·supervisor를 확인한다.
2. 기존 operator hold/재기동 요청이 있으면 실패한다. 이 작업 소유의 기동 보류를 생성한 후 일반 restart flag로 정상 종료를 요청한다. 이전 Main과 supervisor의 종료 확인 전에는 selector/체크리스트를 발행하지 않는다. 종료 시간 초과·PID 변경·다른 Main 등장 시 다음 단계로 진행하지 않는다.
3. 종료 후 후보 Git의 검토된 체크리스트와 selector를 발행하고 native stopped-predecessor 인계를 준비한다. bootstrap·보조판정 호환성을 검증한 뒤 기존 launcher를 시작한다. 원 PREOPEN/정책 bytes 및 실제 새 PID 소비까지 대조한다.
4. stopped 준비의 코드 검증은 해당 호출 안에서만 종료된 이전 소비 증빙을 허용한다. 예외/종료 시 문맥을 해제하고, 일반 호출 및 살아 있는 이전 PID에는 적용하지 않는다.
5. 역사 최종화의 내부 정책 검증도 검증된 역사 관찰 문맥을 사용한다. 일반 `verify`·`consume`·정책 활성화에는 적용하지 않는다. 다른 원천/정책/hash/PID 결손은 여전히 실패한다.
6. 실패 시 단계와 원 selector/문서를 보존한다. 새 PID 존재 가능성이 있는 상태에서 selector를 과거로 돌리지 않으며, 시작 실패 후에는 이 작업 소유 기동 보류를 복구한다. 다른 operator hold를 지우거나 로그 감시 cursor를 초기화하지 않는다.

최초 실배포 검사에서 기존 Main/supervisor 종료 선행은 확인됐지만 stopped 인계 검증이 실패했다. `python -m`의 `__main__`과 내부 reader가 import한 정규 모듈에 별도 문맥 인스턴스가 생기는 결함이었다. 기동을 차단한 상태에서 정확한 원 selector/체크리스트를 복구하고 이전 릴리스 검증 후 정상 launcher로 복구했다. CLI도 정규 모듈의 `main`을 호출하도록 수정하고 실제 `runpy` 진입점 회귀를 추가했다. 정책 파일을 바꾸거나 검증을 생략하지 않았다.

## 검증과 적용

단계별 실패에서 후속 발행/기동이 실행되지 않는지, 살아 있는 Main/변경된 selector·원천·hold 거부, stopped 준비의 격리, 일반 검증 엄격성, 문서 권한 보존과 launcher 실패 후 보류를 검증한다. bootstrap·delay/holding·cron/finalization·router 관련 회귀를 함께 실행한다. 문서 parser는 print-only로 실행하며 외부 동기화는 하지 않는다.

현재 체크리스트 보완 내용은 후보 Git에 먼저 준비하고, live 공유 문서는 실제 종료 후 native publisher가 갱신한다. 코드 검증 완료와 실제 배포는 분리하며 테스트 건수·불변 후보·정상 종료→선택→새 PID 시각 및 자연 알림 검사는 [완료 영수증](../../tmp/ordered-release-deploy-repair-20261012/completion.json)에 기록한다. 실제 주문이나 경제성 개선을 검증 목적으로 만들지 않는다.
