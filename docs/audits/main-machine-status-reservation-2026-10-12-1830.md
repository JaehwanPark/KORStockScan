# 18:30 최신 재기동 이후 기계판정 일회성 점검 예약 — 2026-10-12

사용자 지시: **2026-10-12 18:30 KST에 최신 재기동 이후 기계판정 현황 점검.** 상태는 **예약 실행·원천 수집 완료**다. 아래 예약 당시 검증과 실제 실행 결과를 구분한다.

## 실행 범위와 소유

- user systemd 일회성 timer `korstockscan-machine-status-20261012-1830.timer`가 같은 이름의 service를 한 번 실행한다. 달력 시각은 `2026-10-12 18:30:00 Asia/Seoul`, AccuracySec=1초다.
- 이 일회성 사용자 요청의 운영 증빙은 이 문서와 [예약 receipt](../../tmp/main-machine-status-20261012-1830/reservation.json)다. 현재 거래 PID에 봉인된 checklist·selector·런타임 정책·cron은 변경하지 않는다. 기존 당일 family/postclose owner를 이 별도 점검으로 완료 처리하지 않는다.
- 임시 도구는 [snapshot.py](../../tmp/main-machine-status-20261012-1830/snapshot.py), 소유 위치는 `tmp`의 단회 offline 진단이다. engine module·주문/정책 producer·추가 봇/agent를 만들지 않는다. 표준 라이브러리만 사용하고 engine import·API/Provider 호출·Telegram/외부 메시지 발송·설정 변경·재기동은 없다.
- 실행 명령은 project `.venv`와 절대 경로를 사용한다. 실제 시점의 selector→actual PID receipt→`/proc` start/cwd→원천을 연결한다. 수집 전후 selector/PID가 변하면 성공으로 확정하지 않는다.
- transient user timer는 현재 서버 user manager에서 실행한다. 서버/user manager 재시작으로 transient 정의가 소실되면 예약이 보장되지 않는다. 계속 반복하는 cron이나 거래 service에는 연결하지 않는다. 대화창으로 자동 결과 알림을 보내는 예약은 아니다.

## 읽는 근거와 산출물

1. 실제 최신 PID의 시작 시각 이후 `mechanistic_entry_observation_v1` 캡처를 PID/start와 결속한다. 상시·비상시 Main, probe 관측, 시장별 판정을 구분하고 서로 다른 role을 합산하지 않는다.
2. 현재 PID의 분 단위 execution partition에서 비상시 physical lease 종료, worker/보조 결과와 Main disposition, native lifecycle을 중복 제거한다. 서로 다른 Main 단계는 배타적 주문 결과로 합산하지 않는다.
3. 최신 exact-PID performance에서 첫 loop와 warm loop, 전달/준비·응답 처리 지연을 분리한다. source quiet·missing·UNKNOWN을 정상 BLOCK 또는 API 장애로 단정하지 않는다.
4. 최대 원천 읽기 256MiB, 파일당 128MiB, 개별 row 2MiB다. 초과·partial tail·parse/identity/성능 자료 결손은 보고서에 표시하고 집계를 관측 하한으로 둔다. 전체 무결성을 입증하지 못한 0건은 정상 실적이 아니다.
5. service 자원 상한은 RuntimeMaxSec=180초, MemoryMax=256MiB, CPUQuota=25%, Nice=19다. 원 source/PID·정책·주문·custody 상태를 변경하지 않는다.

[결과 JSON](../../tmp/main-machine-status-20261012-1830/result/snapshot.json)과 [결과 보고서](../../tmp/main-machine-status-20261012-1830/result/report.md)에 실제 점검 시각·릴리스/PID·분모·원천 범위·결손을 기록한다. 실행 전 파일은 `scheduled_not_executed`이며 자연 결과가 아니다. 기존 손익/후행 maturity·주문 terminal은 이 로컬 집계만으로 확정하지 않는다.

## 리뷰·검증

- 실제 stdlib reader를 fixture로 검사한 [표적 회귀](../../tmp/main-machine-status-20261012-1830/test_snapshot.py) 7건 통과: PID/start 분리, 중복 캡처·async 행, probe/live 분모, 충돌 verdict, 재기동 전/미래 행, partial tail, 도래 전 실행 거절.
- self review에서 async stage mapping의 Counter 집계와 성능 미관측/노후화 표시를 보완했다. pytest·compile과 실제 읽기 전용 preview가 통과했다. preview는 [별도 폴더](../../tmp/main-machine-status-20261012-1830/preview/report.md)에 두며 예정 시각의 결과로 사용하지 않는다.
- 예약 등록 당시 운영 docs·로컬 링크 6개·공백 및 print-only parser 19항목을 검증했다. 당시 systemd timer는 `active/waiting`, 다음 실행 시각 `2026-10-12 18:30:00 KST`, AccuracySec=1초와 service 자원 상한을 확인했고 LastTrigger는 비어 있었다. Project/Calendar sync는 실행하지 않았다.

## 실제 실행 결과

- 실제 관측은 **2026-10-12 18:30:00.683309 KST**에 완료됐다. service `Result=success`, `ExecMainStatus=0`, `inactive/dead`와 [종료 receipt](../../tmp/main-machine-status-20261012-1830/completion.json)를 보존한다. 예약 당시 receipt는 덮어쓰지 않았다.
- 릴리스 `native-readiness-20261012-v2`, commit `cf650549e7a07ed470cd95a500af43336d31232c`, Main PID1215171/start4182334를 수집 전후 동일 신원으로 확인했다. 로컬 집계의 source gap은 없으나 이는 거래 원천 결손이 해결됐다는 뜻이 아니다.
- 재기동 이후 상시 Main ENTER_NOW122, 별도 probe ENTER_NOW9/BLOCK1, 비상시 Main BLOCK1/RECHECK1이다. worker PASS31·CAUTION15·VETO1·미평가/불명95는 별도 단계이며 주문 수가 아니다.
- 비상시 종료838 중 source715, required feature113, assessed10이다. 잔여 원인과 상세계획은 [진단·연구 리뷰](main-post-readiness-residual-and-pattern-research-review-2026-10-12.md)에 연결한다. 현재 정책·주문·Provider·custody를 변경하지 않았다.

사용자 실행용 표준 동기화 명령은 [상세계획 §9](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md#9-1830-실제-점검과-이번-작업의-검증)에 둔다.
