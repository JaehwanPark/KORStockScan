# 위젯·에피소드 최소 보조청산 배포 검증

기준: 2026-09-10 KST. 사용자 요청은 다른 세션 구현의 배포와 다음날 기동이다.
후속 답변으로 최초 설정을 9/11 신규 진입분부터 이후 거래일에도 유지하도록 승인했다.

## 범위와 승인값

- 대상은 인계 리뷰 §32~33의 최소 `machine_profit_stagnation_v1`이다. 전체 adaptive group/trailing/AI 연구 family 활성화가 아니다.
- 정체180초, 변동0.15%p, 고점개선0.10%p, 비용0.23%와 추가 slippage5bps, SELL TTL10초, 최대 관측공백12초를 핀한다. 호가 신선도2초·정확한 owner/수량·취소 terminal 검증은 불변이다.
- `valid_from=2026-09-11T00:00:00+09:00`, `valid_until=9999-12-31T00:00:00+09:00`은 사용자 철회 전 지속 운영의 표현이다. 자동 최적값 또는 비용 정확성 보장이 아니다. 기존 보유는 자동 이관하지 않는다.
- 비용 원천은 별도 사용자 승인 `deploy/machine-profit-stagnation/operator-cost.json`이다. source-only 비교 리포트에 실주문 권한을 부여하지 않는다. 실제 broker 비용/실현손익은 별도 대사한다.
- 정책 SHA256: `aa2d47945590d48dde89875d8873d01387e24f66c48f65b99b8d98ec740e3ceb`.
- 비용 원천 SHA256: `5aea42fa0de70d765d160e678e82d3e82c66aa8f63a1510ca3f69ef5946f3612`.

## 코드와 경로

별도 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/machine-profit-stagnation-20260911`에 인계된 trading 구현과 의존성을 동결했다. main/장후 공통 선택 b665e0a3와 실제 main PID1048327/a722b27f는 변경 대상이 아니다. 위젯·에피소드의9개 service/preflight drop-in이 이 machine 릴리스를 사용하며 기존 unit의 사용자/그룹, 자원 제한, 시작 조건, profile와 타이머는 유지한다.

data/logs/tmp/.venv는 canonical workspace 공유 경로다. 새 원장 복제본이나 별도 계좌를 만들지 않는다. 신규 policy pin은 이9개 unit에만 있고 main env에 주입하지 않는다. 작업폴더의 다른 세션 수정은 덮어쓰거나 포괄 커밋하지 않는다.

## 배포 전 리뷰와 보완

1. 저가주 preflight의 승인 source가 공유 data symlink를 통해 canonical workspace로 해석되면 원래 PROJECT_ROOT containment가 정상 리포트도 거부했다. 실제 통합 테스트에서 `research_source_report_unreadable`을 재현했다. 기존 release 내부와 명시적 canonical DATA_DIR/report만 허용하고 외부 파일·symlink escape·hash 변조·결손 거절을 추가 검증했다.
2. 다섯 machine wrapper의 workspace 절대경로를 wrapper 자신의 release root로 바꿨다. 기존 profile/수량/확인 문자열/정책 발행·preflight 조건은 바꾸지 않았다.
3. widget startup receipt의 안전한 env hash allowlist에 보조 정책 PATH/SHA256을 추가했다. 실제 PID 기동 영수증과 기능의 자연 소비를 구분한다.
4. widget은 계속 실행되는 service여서 07:58 타이머만으로 새 코드를 로드하지 않는다. 현재 owner가 idle이고 broker 미체결·원장 차이가 없는지 확인한 뒤 별도 재기동해야 한다. 19:12:34 읽기 전용 대사: KRX/NXT 모두 조회 성공, 삼성전자25주, 미체결0·registry gap0. 위젯4종목 원장 주문0. 삼성전자25주를 위젯 소유라고 판정하지 않았다.

최종 영향 검증: **1058 PASS / 2 기존 비대상 owner SKIP / 28.81초**. 실제 owner loop/fake wire, 취소확정·부분체결·TTL·원목표 복원, 저가주·삼성3서비스·widget·재진입·preflight·기동 영수증·정책 날짜/핀/지속 조건을 포함한다. Ruff, compile, bash -n, diff check 검증. 이 범위 미해결 코드 finding0이며 주문 효과나 경제성 완료가 아니다.

## 운영·rollback과 자연 수락

설치 시 drop-in `70-machine-profit-stagnation-release.conf`만 새로 추가하고 이전 unit 원문·PID·타이머를 보존한다. 실제 설치 결과와 widget 새 PID는 아래 후속 receipt로 남긴다. 에피소드는 오늘 강제 기동하지 않고 기존 내일 시간표를 따른다.

정책 철회는 신규 후보를 막되 이미 취소/SELL이 진행 중인 원장은 이 릴리스의 복구 consumer로 유지해야 한다. 열린 successor가 있는 상태에서 예전 코드로 되돌리거나 원장을 삭제하면 안 된다. 모든 보조 주문이 terminal/원 목표로 복귀했음을 대사한 후에만 이전 코드/drop-in을 복원한다. cost/시간/수량·target 값 자동 확장은 없다.

정상 기대 동작은 양수 추정 순이익과 fresh 전량 depth가180초 정체 → 원 목표 취소확정 → 보호 지정가 → TTL/부분체결 잔량의 원 목표 복원이다. 기존 위젯 EXIT가 우선하며 에피소드2×10주 계약은 그대로다. 응답 유실·모호한 예약·전일 receipt 부족은 직접 recovery 사유로 남고 추측 재주문하지 않는다.

다음 거래일 실제 unit/PID/pin, source 수신, 정책 selected 또는 직접 blocker, 신규 entry 제외/포함, 주문 전환/terminal, 총 비용 후 순이익·자본점유·불리한 결과는 아직 미래 수락이다. 표본0을 기동 결함이나 개선 성공으로 표시하지 않는다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에 장후 인계를 연결하고 다음날 기동 확인은 명시적 체크리스트 항목에 남긴다.
