# 장후 연계 의미감시 구현·반복 리뷰·배포

원천 확인일: 2026-10-01 KST. 다음 기동 대상일: 2026-10-02.

## 구현과 보완

- 기존 `artifact_freshness`에 보조 v4 동결 1위·부모·train hash·시간순 split/purge·full-cost/진단 분모·완료 응답 census를 연결했다. 같은 날 검증을 허용하며 owner 경제성과 독립 CF를 혼합하지 않는다. 과거 v3와 기계 기존 버전에는 새 요건을 소급하지 않는다.
- 기계 v7은 기존 `promotion_errors`를 재사용하며 두 기계 단계의 report/terminal 원출력 hash를 각각 결속한다. 실패 단계·변조·선정 계약 결손과 정상 carry/표본 대기를 구분한다. Widget/Episode 출력·strict/controller 세대·prepared/실제 소비 경계를 기존 owner에서 읽는다.
- 조치 대상 의미 warning만 Telegram 알림에 추가했다. 날짜/stage/scope/reason 지문으로 중복을 억제하고 unobservable·타 날짜·무효 보고서를 복구로 처리하지 않는다. 날짜가 지난 결손은 미복구 이력으로 보존한다. 여러 경보의 표시 잘림을 피하도록 분할 전송하며 전송 실패는 재시도 가능 상태로 유지한다. 테스트는 mock 전송만 수행한다.
- full detector 정규 cron을 `error-detection` release router로 연결하고 실제 실행 코드 provenance를 health에 기록한다. cron 시각·로그·finalization owner는 유지한다.
- 반복 리뷰에서 단계 실패 은폐, report-source path 결속, 완료 응답 분모, 다른 날짜의 거짓 recovery, 알림 표시 밖 지문 저장을 보완했다. 신규 source module/daemon/producer는 없다. 주문·provider·threshold·quantity·custody/hard safety 변경은 없다.

## 성능·검증 경계

9/30 같은 봉인 보고서의 구/신 3회 읽기 전용 비교에서 초기 whole-chain 재계산 초안은 약 37배 CPU와 과다 RSS로 부적합했다. 이를 제거하고 native generation-only 대사와 출력 streaming SHA로 보완했다. 최종 중앙값: wall 0.2997→0.3435초(1.146배), CPU 0.2988→0.3370초(1.128배), 프로세스 누적 최대 RSS 중앙값 69,048→75,600 KiB. 메모리 비교는 동일 프로세스 순차 실행이라 신버전에 보수적으로 누적된다. 계획의 wall/CPU·RSS 한도를 통과했다. 정식 준비·장전·최종화의 전체 재검증 기본값은 변경하지 않았다.

최종 감시·장후·알림·router·제출병목 표적 회귀 472개, 장전 bootstrap·기계 정책·wrapper 127개로 **599개 통과**했다. 초기 registry 테스트 13개는 실제 운영 자금 정책을 읽는 fixture 오염이었다. registry에만 격리 root/자금 의미 fixture를 적용했으며 실제 의미 helper 시험은 그대로 유지한다. 기존 자금/holding 전용 9개는 이번 변경 범위 밖으로 분리한다. compile/bash/diff 및 print-only parser(29개) 통과. 불변 릴리스와 배포 결과는 아래에 기록한다.

## 배포·다음 기동

현재 배포 검증 진행 중이다. Main은 오늘 OFF를 유지하며 Widget/Episode 기존 소비 코드·정책 hash·예약을 보존한다. 감시기와 Main 다음 기동 selector를 새 불변 릴리스로 선택하고 9/30 닫힌 원천의 strict/controller 세대와 10/2 준비본을 정식 경로로 갱신·전체 검증한다. 기존 controller/strict 시도 및 준비본은 이력으로 보존한다. 과거 경제성·라벨 보고서 재생성이나 원천 결손 삭제는 수행하지 않는다.

실제 내일 PREOPEN·Main PID·Widget 날짜 전환·Episode 당일 preflight/live 소비는 `FinalPolicyStartupAcceptance1002`, 자연 v7/v4 장후 생성은 기존 해당 장후 owner가 확인한다. 준비 PASS를 미래 정상 기동이나 수익의 증명으로 취급하지 않는다.
