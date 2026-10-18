# Main 정책 로딩·보유 연구 통합 배포 후보 — 2026-10-18

사용자는 `57a4659f4`를 포함한 통합 배포본 준비를 지시했고, P5는 다른 연구 세션이 끝난 뒤 실행한다고 정했다. 이번 범위는 코드 통합·리뷰·오프라인 회귀·표준 공유 경로를 갖춘 선택 전 배포 후보 구성이다. 실제 준비 세대의 Main child(P5), 선택 변경·정책/인계 발행·Main 재기동은 실행하지 않는다.

## 통합 범위

- 기준은 `7c241ea21619ce3153f1a338f1b846b0313a894f`다. 현재 선택 `900234d791b0bf31797cd4e823d0ae40296f790b`와 이후 source-control/snapshot 경로 수리를 계승한다.
- 정책 로딩 검증 `590fccd7002082db3fbd02dd4fe3a47de5a39174`를 유지하고 보유 연구 `57a4659f471044f8c8a59db53fc01b12d194333a`를 merge한다.
- 보유 연구의 선행 `0ab270be0 → d07c3ee3f → 7dc2a934e → 1bf35e6c2 → a4a51fd8b → 57a4659f4` 여섯 commit을 모두 보존한다. tip의 두 파일만 옮기지 않는다.
- 두 branch의 직접 변경 파일 교집합은0이다. 다른 연구 세션의 후속 commit·dirty workspace는 자동 포함하지 않는다. canonical의 동시 문서·연구 원천·선택본은 보존한다.
- 통합 작업본은 `/home/ubuntu/KORStockScan-worktrees/main-policy-holding-integrated-20261018`, branch는 `prepare/main-policy-holding-integrated-20261018`이다. 최종 commit·후보 root·결과는 `/home/ubuntu/KORStockScan/tmp/main-policy-holding-integration-20261018/integration-manifest.json`에 결속한다.

## 통합 리뷰와 보완

파일 충돌 없는 merge와 정책 코드 인계의 적합성은 다르다. 연구 delta는 frozen delay inventory의 상태 처리 코드, stop inventory의 상태 처리/holding 원 AI/연구 assembler, holding inventory의 위 경로와 비용 모델·replay에 교차한다. 기존590의 exact source pair만으로는 새 연구 bytes를 허용할 수 없다.

원7f 코드와 새 통합 코드의 exact SHA 쌍5개를 기존 native 인계 검증기에 추가한다. 새 상태 처리 코드가 참조하는 `trailing_entry_research_source.py`와 `kiwoom_utils.py`도 해당 세대에서만 조건부로 exact SHA·candidate Git object와 대조한다. 원 정책 digest와 세 family의 역사적 inventory는 수정하지 않는다. 원래 handler를 쓰는 역사적 선택본에는 새 도우미를 요구하지 않는다. 준비 인계 검증은 native delta를 매번 다시 호출하며, startup 검증 context는 전체 요청 원천을 다시 대조한다. 이미 로딩된 메모리 cache는 기존 불변 릴리스 계약을 유지하며 매 주문마다 전체 파일을 해시하지 않는다.

독립 리뷰에서 live/shared 변경이 기존 수량·가격·stale·retirement·주문 안전을 바꾸지 않음을 확인했다. 새 경로는 연구용 진입 영수증과 보유 linkage를 붙이거나 지우며, ADD·재진입에 과거 연결을 상속하지 않는다. 계좌·원천 불명은 연구 gap이다. Kiwoom 변경은 기존 설정 읽기에서 비밀정보 없는 provenance를 기록하며 추가 API/WS 요청·인증 규약·외부 조회를 만들지 않는다. 실제 손절·trailing·슬롯·경제 선정·운영 권한은 변경하지 않는다.

## 검증과 후보 구성

최종 표적 회귀는 **3,917 PASS**다. `integrated-regression.txt`의32개 모듈3,861 PASS와 `prepared-contract-regression.txt`의별도2개 모듈56 PASS는 서로 겹치지 않는다. startup native-child·공통 loader·Bash env·parent·OS 격리·code context·launcher/router·prepared/intraday handoff와 보유 연구를 포함한다. 원57 연구 테스트13개 모듈의 초기494 PASS는 반복이므로 더하지 않는다. 변경 Python60개 compile·shell3개 syntax·위치 gate·diff check·문서 링크/owner·print-only parser도 확인했다. 실제 연구 재생·provider·정책 생성은 이 회귀 범위가 아니다. 독립 코드·테스트·문서 재리뷰의 미해결 지적은0건이다.

최종 통합 commit으로 관리 디렉터리의 detached Git worktree를 만든다. 새 checkout의 `data`·`docs` 등 공유 경로 자리는 build evidence 아래로 이동해 보존하고, `data/logs/tmp/.venv/docs/restart.flag`를 canonical 절대 경로에 연결한다. 기존 canonical 파일을 삭제하거나 덮어쓰지 않는다. `runtime_release_router.validate_release`는 selector 발행 없이 candidate HEAD·관리 경로·공유 경로·퇴역 guard·`src/deploy/restart.sh` clean을 검증한다. `requirements.txt`도 따로 확인한다. 공유 `.venv`의 패키지는 변경하지 않는다.

`ordered_intraday_deploy`에는 준비 전용 dry-run이 없으므로 후보 검증 목적으로 호출하지 않는다. 후보의 배치·코드 계약 PASS는 배포 실행이나 P5 결과가 아니다.

## 남은 순서

[MainPolicyLoadAndExitValidation1018](../checklists/2026-10-18-stage2-todo-checklist.md)의 OPEN을 유지한다. 다른 연구 세션 종료 뒤 포함할 최종 commit과 원천 세대를 다시 고정하고, 바뀐 코드가 있으면 후보를 다시 구성한다. 그 뒤 기존 native 절차의 코드/원천 handoff·필요한 quantity monitor/research 코드 세대 현행화와 실제 준비본 결속을 확인하고 P5를 실행한다. 원 정책·PREOPEN·strict/controller·실패/인계 bytes를 고쳐 쓰지 않는다.

이번에는 그러한 canonical 영수증·readiness를 발행하지 않는다. 실제10/19 PREOPEN·운영 PID는 기존 [DirectFamilyPreopenPolicyHandoff](../checklists/2026-10-19-stage2-todo-checklist.md)가 유지한다. 선택900은 그대로이며 `actual_pid_consumed=false`, `runtime_effect=false`다. 자연 감시·주문·체결·비용 성과를 준비 완료의 근거로 주장하지 않는다.
