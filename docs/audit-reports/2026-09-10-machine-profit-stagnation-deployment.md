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

## 19:19~19:20 설치·실행 확인

- 배포 코드 commit: `273807e3767bc92cd89cd0394e8aa374679795c6`. src/deploy clean. 별도 `deploy/machine-profit-stagnation-20260911` 브랜치이며 main merge/push는 이번 설치에서 실행하지 않았다.
- 9개 drop-in 설치·daemon-reload·systemd-analyze verify(서비스와 저가주 template instance) 통과. 기존 unit 백업: `/tmp/kss-machine-units-mOtQ39`; 원본 unit 수정 없음. 배포 초기 data 사본은 `/tmp/kss-machine-bootstrap-wmru4X/data`에 보존했다.
- 위젯 기존 PID327676은 주문0/idle 대사 후 정상 systemd stop으로 종료했다. 기존 코드는 별도 graceful-drain handler가 없어 장중 주문 중 drain 검증을 했다고 주장하지 않는다. 종료·시작 모두 success. 새 PID **1138215**, 시작19:19:33, `NRestarts=0`. 새 코드의 현재 policy PATH/SHA256 startup 검증 `passed=true, findings=[]`.
- 기동 receipt hash `edca74f7103becf45a9f2019c95ad329f38a23807196383053f0815989b42fda`. 메인과 공유하지 않는 env hash2개를 검증했다. 아직 정책의 자연 주문 소비를 확인했다는 의미는 아니다.
- 전후 broker: `tmp/intraday-monitor-20260910-1050/broker-191923.json` → `broker-192006.json`: KRX/NXT 조회 성공, 삼성전자25주 동일, 미체결0/원장 차이0. 위젯 주문0. 별도 매수·취소·매도·수동 잔고 편입 없음.
- 삼성 오전/정오/오후 timer는 active, 다음 실행9/11 **07:57 / 13:14 / 13:59**. 저가주 기존 profile별 timer/확인 문자열/수량은 그대로다. preflight가 거절하는 격리 profile을 강제 활성화하지 않았다. 위젯은 새 프로세스가 계속 실행되므로 내일07:58 타이머의 재시작에 의존하지 않고 기존 loop가 날짜별 정책을 읽는다.
- 9/10 현재 위젯 원장에 신규 BUY가 없어 entry timestamp가 없다. 원장의 `profit_exit_policy_status=invalid_or_missing_evidence:ValueError`는 이 빈 진입시각에서 생기는 관측 표시다. 실제 핀 파일/비용 hash 및9/11·9/14 신규 진입 통과,9/10 진입 제외는 별도 테스트로 확인했다. 내일 유효 entry에서도 같은 표시가 지속되면 실제 source/입력 blocker로 재검토한다.
- 최종 형식 보완 뒤 배포/기동 영수증 부분집합67 PASS 추가(1058과 중복, 합산하지 않음).
- main PID1048327와 공통 선택 원장 hash `eaffc240c0e68a5c78f5c9ce0b7f0e88a54b300421a2109f0887104118c50e8b`, main/장후 cron9행 검증을 유지했다. 이 세션이 main/장후 selected release를 machine release로 바꾸지 않았다.

## 후속 코드리뷰·패키징 보완 (9/10)

이번 요청은 수정사항 리뷰·보완·커밋/푸시이며 추가 배포나 장후 모니터링 실행이 아니다. `fix/machine-deployment-handoff-review-20260910` 분리 worktree에서 운영 data를 공유하지 않고 검증했다. 기존273807e3의 실행 중 코드,9개 unit,정책 pin,main 선택 원장을 수정하지 않았다.

1. **정책 패키징 누락:** 설치 파일2개가 전역 `*.json` ignore 때문에273807e3에 포함되지 않아 새 checkout의 정책 테스트가 실패했다. 두 승인 파일에만 ignore 예외를 추가하고 원본 byte hash 그대로 버전 관리한다. 설정·시작일·기존 보유 제외 계약은 불변이다.
2. **checkout 의존 테스트:** 테스트가 자신의 checkout을 운영 설치 경로와 같다고 가정했다. 로컬 정책 bytes와 versioned drop-in의 명시적 운영 경로를 따로 검증하도록 수정했다. 리뷰/CI가 실제 운영 파일을 읽어 우연히 통과하지 않는다.
3. **동결 코드의 생산자/소비자 누락:** 포함된 group replay·approval 테스트에 비해 기존 execution helper·source/study·approval 연결이 빠졌다. `ImportError`, `runtime_registry` 인자 거절, `shared_target_research` 결손을 재현하고 해당 의존성만 보완했다. 공통 관측 kernel·공유 목표의 고정 BOOK 배분/동일 horizon·결측 분모·연구 ID를 연결하며 독립 target 승인으로 전용하지 않는다. 별도 initial context/hash가 없으면 전체 adaptive family는 여전히 기본 registry에 추가되지 않는다. 최소 보조청산 정책과 별개다.
4. **운영 지시문 불일치:** main 공통 선택과 별도 machine manifest/unit을 분리하고 지속 승인값·다음날 신규 entry·연속 widget PID·rollback recovery를 현행화했다. 분석 unit 복구 권한을 매매/preflight 재기동 권한으로 확대하지 않는다. 기존 §1.3 anchor와 미래 체크리스트 ID를 보존했다.

운영에 설치된 최소 보조청산의 이전 검증과, 이 후속 패키징/연구 코드의 검증은 서로 다른 세대다. 후속 커밋은 선택 배포본 갱신이나 전체 연구 기능 활성화가 아니다. 원 작업폴더의 무관한 장중 수정은 그대로 보존하며 main 병합은 이번 요청에 포함하지 않는다.

### 후속 검증 결과와 제한

- 전체 adaptive 경로,기존 approval,최소 보조청산·배포·widget receipt: **1988 PASS / 4 기존 owner 비대상 SKIP / 186.65초**. SKIP은 widget 전용 catalog·episode 전용 terminal manager·widget daily cap의 타 owner 조합이며 수정한 테스트를 임의 skip하지 않았다.
- attribution 및 저가주/삼성3기계·preflight: **498 PASS**, 과거 운영 자료 의존 테스트2건은 분리 checkout에서 자료 부재로 실패했다. `test_all_thirteen_20260904_recommendations_bind_exact_next_profiles`의9/4 source report와 `test_20260907_exact_date_cost_quarantine_migration_is_bounded_and_idempotent`의9/4 candidate가 Git에 없는 운영 산출물이다. 이2건은 검증 미완료로 남기며 성공으로 세지 않는다. 운영 data 공유/재생성 또는 기존 정책 guard 완화로 PASS를 만들지 않았다. 공유 source 경로·hash/escape 회귀는 별도 fixture 테스트에서 통과했다.
- Ruff, 변경 Python compile,5개 wrapper `bash -n`, `git diff --check` 통과. 문서 상대 링크20개 유효,print-only backlog parser에서 다음날 기동 owner와 기존 장후 owner의 고유 ID 확인. 과거 자료 부재2건 외 검토 범위 미해결 코드 finding0이며 전체 저장소 무결함/실주문 효과를 주장하지 않는다.
- 최종 읽기 전용 대사: 실행 machine src/deploy/restart clean,정책 byte SHA256 및 main selector SHA256은19:20 receipt와 동일하다. 이번 후속에서는 매매 재기동·정책 변경·Provider 호출·장후 재생성·외부 sync를 하지 않았다.
