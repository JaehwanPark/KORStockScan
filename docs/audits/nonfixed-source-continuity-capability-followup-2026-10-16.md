# 원천 연속성 배포 후 capability 후속 검증 — 2026-10-16

## 배포 후 재리뷰 및 보완

0004e9863352ca727780d4a2b3d6a55f23af1f49의 정규 전환은19:03:40 pass/complete, PID305600/start20892914였다. 정지 전에 active-policy/지연/손절/보유 code handoff를 모두 확인했고 누락에 따른 기동 중단은 없었다. 새 PID startup Sentinel/observer가 exit0으로 발행됐고19:05:07 full detector는FAIL0/PASS5/WARN2였다. WS 실제 서버 성공 응답4개는 종목 귀속 불명을 유지하며 원천 수신과 구별해 보존됐다.

같은 점검에서 공통 handler/Main 세대 변경에 따른 rising_missed/holding_vote의 current-code capability 연결 누락을 발견했다. 수리된 entry readiness 부분은 해당 family 생산자·선택·발행을 바꾸지 않는다. 기존 정확 source-pair의 successor hash를 새 세대에 맞추고 네트워크 차단 native fixture를 새로 발급·검증한다. 원 보고서·원 fixture·source/comparison/handoff 상태와 경제성 미수용은 유지한다. 별도 추가 코드 수리 후 동일한 정지 전 인계 검증과 정규 재배포를 수행하며 최초 배포/경고는 보존한다.

후속 검증245개 및 실제 네트워크 차단 rising86/holding99 fixture가 통과했다. 원15일 보고서를 native reader로 읽어 두 current_code_capability_verified=true를 확인했으며 valid_empty/experiment_not_armed와 기존 source_gap은 유지한다.70ca220b1의 정규 재전환은19:11:21 pass/complete, PID325383/start20939041이었다.

중간 수리 중 첫 code handoff의 targeted_validation이 작업 트리 원 리뷰 문서를 참조한 상태에서 그 문서에 후속 기록을 추가해19:07:09/15/20 AI 평가 실패3건이 발생했다. 원 bytes를 복원하고 후속 기록을 이 별도 문서로 분리했으며 새 code handoff 전체 hash 검증을 통과했다. 실패 원 로그는 `intermediate-source-binding-errors.log`에 보존한다. 해당 작업 트리 원 리뷰는 현재 ancestry의 원천이므로 변경/삭제하지 않는다. 향후 handoff는 리뷰 문서의 불변 증거 사본만 참조하도록 운영 절차를 명시했다.

마지막 리뷰에서 REG 중심 종목 projection 밖의 REMOVE 응답을 운영자가 확인할 경로를 보완했다. 기존 비동기 WS dashboard writer의 shared transport projection에 연결 단위 요청/응답 최근16개씩을 추가한다. 전체 요청/응답 수와 귀속 unknown을 보존하고, 삭제된 종목 registry에 의존하지 않는다. ingress에는 동기 파일 쓰기/ACK 대기/추가 구독을 넣지 않는다. 관련WS228개 통과, native 및 rising/holding code generation 불변이다.
