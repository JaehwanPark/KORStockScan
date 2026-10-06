# Main 기계 원천·판정 계약 보완 배포 및 기동 수용

## 권한과 범위

사용자가 코드리뷰 후 수정보완 반복 및 배포·재기동을 명시 승인했다. [원천 갱신·증거 해시 보완](main-machine-source-refresh-and-admission-hash-remediation-2026-10-06.md)과 [018880 probe 관측 시각 보완](main-entry-pre-ai-probe-clock-and-018880-lineage-audit-2026-10-06.md)을 통합한다. owner는 당일 체크리스트의 `MainMachineSourceRepairDeploy1006`이다.

현재 기계·보조 정책과 당일 PREOPEN 입력을 보존하는 코드 릴리스 교체다. 위젯 퇴역, 에피소드 격리, 기존 원천 freshness/conflict·수량·cap·broker·custody·operator lock 및 hard safety를 유지한다. 미지원 probe 경제성 재생을 유효 수익으로 바꾸지 않는다.

## 반복 리뷰와 코드 검증

1. 원천 lease의 scope/expiry/1회 retry, 새 exact 0B·신선한 0D와 기존 완료 판정 cooldown, 부모·자식 identity 및 비동기 generation을 재리뷰했다.
2. immutable setup hash, 후속 screen 거부 시 기계 action 보존, 관측 clock의 KST 단일 확정, live 예약과 관측의 경계를 재리뷰했다.
3. source wait가 cached BUY·추가 REST/AI·주문 경로를 열지 않는 실제 WATCHING handler를 검증했다. 새 Python 모듈은 scalping package의 Main entry 원천 일정 소유이며 engine root에 추가하지 않았다.
4. 확인된 범위의 미해결 코드 결함은 없다. 관련 12개 module **1,143 PASS**, 실제 handler **3 PASS / 911 deselected**. 수정 Python compile, Ruff `E9,F63,F7,F82`, `bash -n` 및 diff 검사를 통과했다. 기존 pandas 옵션 deprecation warning 1건은 별도다.

실행 로그: `tmp/machine-source-deployment-20261006/`에 검증·배포 receipt를 보존한다. package 설치·업그레이드, 정책 재생성, 실제 주문 테스트는 실행하지 않는다.

## 재기동 전 직접 상태

- Main PID `3956345`, root `next-session-ready-20261005-e16ac48b`. cron이 시작한 tmux `bot` 감독자가 관리한다. Main systemd unit으로 재기동하지 않는다.
- 선택 릴리스는 `widget-retired-20261006-b53a3835`이며 기존 PID는 이를 아직 소비하지 않았다. 코드와 선택 경로 및 실제 PID를 구분한다.
- 기존 read-only API helper의 새 완전조회: KRX/NXT 잔고 **0**, 미체결 **0**, 정상 응답·정규화 계약 확인. 로컬 DB의 HOLDING/BUY_ORDERED/SELL_ORDERED **0**.
- 최초 감사 receipt 작성에서 venue set의 JSON 직렬화가 실패했다. API 성공은 확인했지만 이를 저장된 receipt로 간주하지 않고, 정렬된 venue 목록으로 새 완전조회 receipt를 발행했다. 제품 API/매매 코드는 변경하지 않았다.
- 증거: [broker 전 상태](../../tmp/machine-source-deployment-20261006/broker-before.json), [로컬 custody 전 상태](../../tmp/machine-source-deployment-20261006/local-custody-before.json).

## 배포·기동 완료 조건

통합 commit의 깨끗한 immutable release, selector와 설치 소비 경로, 이전 릴리스/설정 rollback, 원 정책/bootstrap/PREOPEN hash 보존, 당일 intraday release handoff를 검증한다. 기존 graceful restart로 singleton 이전 child를 종료하고 새 감독자와 Main child를 기동한다.

완료 후 실제 PID/root/commit·정책 hash·bootstrap·intraday consumption·WS first-data·heartbeat, fresh broker inventory/미체결 및 중복 Main 프로세스/주문을 재확인한다. 자연 새 기계 attempt·원천 복구·제출/체결·비용 수익 증거는 별도 상태다.

배포 및 실제 기동 수용 결과는 완료 receipt와 함께 이 문서에 추가한다.

## 재기동 gate에서 발견한 추가 결함과 보완

새 릴리스의 fresh bootstrap 검증이 `holding_path_vote_policy_receipt_mismatch`와 `holding_path_vote_policy_stale_env`를 반환했다. 기존 Main PID의 원 릴리스에서 같은 입력은 통과했다. 정책 값이 바뀐 문제가 아니라 위젯 퇴역 시 장후 terminal schema를 v3으로 변경하여, 퇴역 전 발행된 v2 summary의 보유 정책 소비까지 거부한 호환성 결함이다.

- 실패한 전환은 selector·설치 drop-in을 원 상태로 rollback했으며 Main 재기동은 요청하지 않았다.
- `stage_receipt_issues`에 보유 정책 소비자만 사용하는 historical summary 검증을 추가했다. source/publication이 `2026-10-06` 이전인 v2 summary만 읽고, 기존 receipt digest·원 코드 hash·정확 input/output/prerequisite 세대·적용 세션 검증을 유지한다. 과거 widget/collector terminal은 증빙으로만 읽는다.
- 새 생산자의 기본 검증은 v3을 요구한다. 오늘 발행 또는 새 복구에서 v2 PASS를 재사용하지 않는다. 퇴역 producer·매매 권한은 복원하지 않는다.
- 새 보완의 변조·결손·발행일·코드·실패 terminal 회귀와 policy/bootstrap/Widget 퇴역 검증 **181 PASS**. 원래 1,146건과 중복 module이 있으므로 고유 건수로 합산하지 않는다. compile·Ruff·diff 통과.
- 실제 보유 정책 consumer는 `estimated_provisional_loaded`, 기존 PID의 fresh bootstrap은 `pass`로 정상화됐다. 보유 bundle `43fcaac44792cb55fced0883b12216f2423468703bea2aee2765d01f01daa926` 및 당일 정책/PREOPEN 5개 frozen hash는 그대로다.
- [실패 검증](../../tmp/machine-source-deployment-20261006/bootstrap-before-fresh.json), [보완 후 검증](../../tmp/machine-source-deployment-20261006/bootstrap-before-repaired.json).
