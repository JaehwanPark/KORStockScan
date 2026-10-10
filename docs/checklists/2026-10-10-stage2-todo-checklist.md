# 2026-10-10 Stage2 To-Do Checklist

## 오늘 목적

- Main PASS 인수·제출·재점검 연결과 진단 지연을 반복 검증하고 승인된 배포 및 다음 영업일 기동 준비를 완료한다.

## 오늘 강제 규칙

- 후속 사용자 지시로 리뷰 후 배포와 다음 영업일 기동 점검이 승인됐다. 동일 정책의 코드 결속·격리 PREOPEN 준비를 정식 경로로 갱신하며, 정책 재선정·AI 연구·장후 원장 재생성은 실행하지 않는다. 실제 Main 기동은 다음 영업일 예약이 소유한다.
- 원 요청·native claim·deadline·정책 identity 및 주문·수량·자금·freshness·Main/manual 소유권 guard를 보존한다. 퇴역 episode/widget 실행을 복원하지 않는다.
- 진단 저장 결손은 미확정으로 보고하며 주문 재전송이나 broker 거절로 합성하지 않는다. 기존 10/9 기록과 봉인된 10/12 checklist를 보존한다.
- Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다.

## 실행 항목

- [x] `[MainPassSubmitRecheckLatency1010] Main PASS 인수·제출 연결 및 진단 지연 보완·승인 배포` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [구현계획 S1–S4](../proposals/main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md).
  - 수용: take/discard 이후 원 객체 종료·후속 claim 보존, 직접 종료 사유와 전이 identity·PASS 분모 연결, 기존 단일 관측 executor의 유한 접수·원 발생 시각, bounded trace 준비 진척, 실제 제출 함수 내부부터 격리 adapter까지 검증한다. 반복 리뷰·회귀·compile·diff·print-only parser 및 동일 입력 성능 비교를 기록한다.
  - 배포 수용: 재리뷰·회귀 후 불변 릴리스와 web pin을 통합 선택하고 원 10/8 장후 세대·10/12 checklist를 보존한다. 새 릴리스의 동일 정책 code refresh, 10/12 PREOPEN 전체 계약, strict/finalization 세대 및 설치 예약 경로를 확인한다.
  - 자연 수용: 10/12 기존 DirectFamilyPreopenPolicyHandoff에서 실제 PID의 정책 소비와 관측된 PASS→제출 또는 기존 guard 종료를 확인한다. 준비 검증과 자연 기동·체결·경제성을 구분한다.
  - 완료 근거: [반복 리뷰·구현 결과](../audits/main-pass-submit-recheck-latency-implementation-review-2026-10-10.md). 최종 고정 코드 19개 suite 2,424 passed / 139.65초, 기존 Pandas 경고 1건. 동일 부하 3회 비교에서 정상 전달 261.943→185.142ms·동시 전달 60.596→49.021ms; 진단 지연과 필수 저장 지연의 만료 의미를 분리 검증했다. compile·diff·문서 검증 결과는 audit에 기록한다. 구현 수용 완료이며 배포·자연 기동 수용을 뜻하지 않는다.
  - 후속 배포 완료: 재리뷰 2,424 passed / 139.44초, 불변 릴리스 326 passed / 9.25초. `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06` 선택, runtime 1,072파일 대사 결손 0, web PID 22143·ubuntu·새 cwd/commit·HTTP 200. 기존 정책 code hash가 일치해 정책 재발행 없이 새 격리 PREOPEN을 생성했다. [최종 기동 준비](../../data/report/main_pass_submit_deployment/2026-10-10/final-readiness.json)는 10/12 `current_full_contract=pass`, finalization issues=[], cron 8개 PASS, 07:35/07:55 예약 정상이며 Main PID 자연 소비는 future_due다.
