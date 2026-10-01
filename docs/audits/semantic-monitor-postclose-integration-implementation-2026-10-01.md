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

### 첫 배포 뒤 재리뷰 보완

첫 불변 배포 `6a61b5b8`에서 597 PASS/11 분리, 실제 root/commit/코드 hash 소비와 report 계약 결손 0을 확인했다. 9/30 새 controller 전체 `done`/strict PASS, 정식 10/2 준비 `prepared_verified` 및 `current_full_contract` 재검증 PASS였다. 이때 실제 경보에서 당일 경제성 6건에 누적 CF 적격 10건이 섞인 표시를 발견했다. 당일 경제성·가격 라벨·계획 lineage 적격을 각각 같은 당일 분모에 연결하고, non-pending 정상 winrate 후속 세대는 native ancestry 검증을 재사용하도록 최종 보완했다. 최종 보완 회귀 598 PASS/11 분리, compile/diff PASS. 후속 불변 릴리스와 새 준비본을 다시 선택·검증한다.

서비스 변경 없는 감시 배포다. 기존 Widget/collector/fill notifier 5개 active PID와 NRestarts=0, 독립 소비 코드 `0a8fa0a0`·정책 pin, Episode 122개 예약/366개 policy pin을 보존했다. Main selector의 trading/utils/bot 코드는 기존 통합 릴리스와 같으며 오늘 Main OFF다. cron의 다른 112행과 8개 기존 라우팅은 불변이다. 기존 Episode failed preflight 61건은 Main OFF의 과거 상태로 남기고 성공으로 재라벨링하지 않는다.

실제 읽기 전용 health의 process/auth/resource/stale-lock은 PASS이며 artifact/cron은 과거 원천·일정 결손으로 FAIL, log는 warning이다. 전체 health GREEN을 주장하지 않는다. 보조 라벨 source gap 6건·writer plan 결손·운영 비교 0/6은 보존되고, 의미적 인계 `done`/prepared PASS와는 별개다. Telegram은 mock 계약만 검증했고 정규 알림 자연 소비는 기존 예약에서 확인한다.

### 유효 준비본의 최종 성능 보완

`167b0535`에서 실제 유효 준비본을 포함한 재측정은 artifact-only wall/CPU 1.695배, 정규 full wall 1.342배·CPU 1.376배로 상대 목표를 초과했다. 위 초기 측정은 작업본의 release identity mismatch로 준비본의 후속 검증이 생략된 범위였으므로 최종 수용 근거로 사용하지 않는다.

원인은 generation-only 경로가 초기수량 정책 경제성까지 다시 검증한 구간이었다. 기존 bootstrap 원천 SHA 대사 블록을 같은 owner의 공통 순수 함수로 추출했다. 정규 감시는 봉인된 full PASS·manifest/env/검증 파일·incumbent/operator/lock/direct-family 원천·초기수량 current 및 네 원천 파일의 현재 해시를 확인하며 파일당 64 MiB 제한을 적용한다. 경제성을 재계산하거나 정책을 다시 선택하지 않는다. 정식 prepare/verify/PREOPEN 기본 전체 재검증은 그대로다. mock 회귀는 gen-only 경제성 재호출 금지와 원천 변경 차단을 추가 검증한다.

보완 작업본의 같은 봉인 입력 정규 full 3회 비교 중앙값은 wall 0.6778→0.8024초(1.184배), CPU 0.6120→0.7297초(1.192배), RSS 170,712→175,732 KiB(1.029배)였다. 최종 불변 릴리스 재검증·새 준비본·코드 provenance와 실제 owner pin은 배포 인계 영수증에서 확인한다. 작업이 자정을 넘겼어도 승인된 기동 대상일은 **2026-10-02**, 닫힌 평가 원천은 **2026-09-30**으로 유지한다.

실제 내일 PREOPEN·Main PID·Widget 날짜 전환·Episode 당일 preflight/live 소비는 `FinalPolicyStartupAcceptance1002`, 자연 v7/v4 장후 생성은 기존 해당 장후 owner가 확인한다. 준비 PASS를 미래 정상 기동이나 수익의 증명으로 취급하지 않는다.
