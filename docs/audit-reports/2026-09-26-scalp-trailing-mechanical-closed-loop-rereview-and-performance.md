# 스캘핑 강약 기계판정 폐루프 재검토·성능 기록 (2026-09-26)

범위: [구현계획](../proposals/scalp-trailing-mechanical-strength-closed-loop-tuning-plan-2026-09-25.md)의 M1 강약 8축, 3시장 수익축 결합, 완료 모수, 장후 원천, 다음 PREOPEN 선택·bootstrap, 실시간 소비와 R6 귀속. 기준 선택 릴리스는 `4ab3491d88b36bd7ec3c53d5961c05617a3e9f33`; 작업트리의 다른 미커밋 변경은 이번 배포 범위가 아니다. 9/26 체크리스트는 없고 다음 실행 owner는 [9/28 HoldingExitPositionOutcomeLineageClosure](../checklists/2026-09-28-stage2-todo-checklist.md)다.

## 처음 발견한 결함과 수정

1. clean baseline 이후 오래된 미봉인 완료 날짜가 M1 신규 정책 후보를 영구 차단했다. 첫 관측 v2 진입일 이후의 완료 ID를 별도 cohort로 묶고, 해당 기간의 누락 날짜·중복/미배치 ID는 차단하며, 비용 결손 ID는 분모 밖에 사유와 함께 남겼다. 다른 청산 규칙의 적격 완료 ID는 cohort에 포함한다. 이전 구세대 결손은 M1 성과로 보간하지 않는다.
2. 분류기×약·강 되돌림폭 후보가 빠져 있었다. 시장별 8개 단일축, 6개 강·약 판정 조합, 8개 분류기×폭 조합을 봉인했다. 실제 청산 뒤에만 발동하는 조합은 검열로 기록한다. 처음에는 이런 후보 하나가 전체 후보의 공통 비교 ID를 0으로 만들었다. **훈련 날짜의 해당 시장 직접 재생 가능 ID 30건 이상**만 공통 비교 풀에 넣도록 수리했다. 후보 전수와 제외 사유는 보고서에 남긴다. holdout은 풀 선택에 사용하지 않는다.
3. 선택기는 요약 EV만 확인하고 후보 상세 표본·종목·손실 안전 근거를 재검증하지 않았다. 후보 상세의 train/holdout, 상태전환 ID와 종목 수, 최악 슬리피지, 큰 손실 악화를 재대사하고, PREOPEN publisher가 장후 세 원천 파일의 경로·byte SHA256을 모두 확인하도록 보강했다.
4. 선택된 시장별 시작값이 무후보 날짜에 0.4%로 재설정될 수 있었다. 검증된 이전 선택 hash는 같은 값으로 carry하고, 정확한 원선택일·영수증을 보존한다. 운영자가 값을 바꾸면 기존 선택 귀속을 이어 붙이지 않는다. R6은 manifest 자체 hash, 정확 날짜 verify, 양의 PID를 구분해 기록한다.
5. 실시간 정책 벡터·분류기 hash 반복 계산이 hot path를 늦췄다. bootstrap hash가 있는 프로세스에서는 정책을 한 번 검증해 고정한다. 새 세대 hash에서만 다시 읽는다. 분류기 실패 시 로그의 hash도 기본값으로 오인하지 않게 했다.
6. 확장 회귀 첫 실행은 비동기 holding review 완료 전 단정 때문에 1건 실패했고, 그 스레드의 외부 DB 조회 경로에서 한 번 segfault가 났다. 해당 테스트는 완료 이벤트를 기다리고 외부 캔들 조회를 고립시켰다. 수정 후 같은 범위와 3시장 회귀를 포함한 **1,058건이 통과**했다.

## 테스트 자료와 결과

| 입력/범위 | 관측 | 권한 한계 |
| --- | --- | --- |
| 완료 80개 합성 clone, REGULAR, 22후보 | 원천 결손 0, 후보 공통 비교 80, 자동 후보 0. 계산 5회 wall 1.309~1.317초, 최대 RSS 약 53 MB, swap 0. | 한 완료일·합성 자료이므로 holdout·실거래 EV 근거 아님. |
| 완료 120개 합성 clone, 시장당 40개, 66후보 | 원천 결손 0, 공통 비교 120. 최종 수정본 5회 wall 2.169~2.184초, 최대 RSS 62.6~62.7 MB, swap 0. 자동 후보 0. | 한 완료일·합성 자료; 시장별 자연 성과·실제 비용 효과는 미식별. |
| 두 스레드, 보유 2개, 1,000 fast 평가, mock I/O | 구 M1 p99 중앙값 1.809ms, 신 M1 약 1.92ms; 25%·5ms 한계 안. 신호·추가 REST·AI·주문 0. | 무신호 pre-arm 입력이며 실제 주문 지연 아님. |
| 같은 1,000 fast 평가, 임시 경로 실제 JSONL append·bootstrap hash 고정 | 구 M1 p99 중앙값 2.925ms, 신 M1 2.814ms. 각 실행 1,512 raw 행, 무신호·swap 0. | compactor·외부 I/O를 고립한 원시 append 시험. 실제 거래소/DB와 신호→주문 시간은 미측정. |

분류기 기본 설정의 기존 STRONG/WEAK/UNKNOWN 이벤트 경로, 500ms 원시 0B 재계산, 첫 crossing·폭, 3시장 120개 ID의 직접/검열/결손 분할을 회귀로 대사했다. 구세대의 집계된 순체결 수량으로 500ms를 대체하지 않는다. 자연 M1 직접 적격·독립 완료일 후보가 없으므로 수익성·선택 허가는 아직 없다.

## 결론과 다음 수용

코드 검토·수정·회귀와 합성 성능 범위는 통과한다. 배포 가능한 코드는 **익절 owner의 후보 생산·검증·무후보 carry**이며 새 임계값 선택은 아니다. 메인 PID는 0이므로 선택 릴리스의 실제 소비와 자연 체결·비용 후 EV는 아직 미확인이다. 다음 영업일에는 정확 날짜 postclose 세 원천·M1 cohort·terminal, 다음 PREOPEN의 hold/carry 또는 한 시장 canary, 실제 PID hash, 자연 완료 결과를 차례로 대사한다.

확인 범위: Python 표적 회귀, 관련 모듈 compile, wrapper `bash -n`, `git diff --check`, checklist print-only parser, release-set/cron 라우팅. Project/Calendar sync, 패키지 변경, bot restart, 주문, 광범위 장후 보고서 재생성은 실행하지 않았다.

## 코드 배포 영수증

이번 범위만 `4ab3491d` 기준 별도 worktree에서 검토·커밋해 불변 릴리스 `scalp-mechanical-closed-loop-20260926-e61b5b05` / `e61b5b05752e07cd34c93acc4132a56d29e19a76`를 만들었다. 2026-09-26 09:59:52 KST에 Main·scheduled main selector를 이 commit으로 전환했다. 이전 선택 `4ab3491d`와 선택 JSON 원본은 `tmp/runtime-release-selection-before-scalp-mechanical-closed-loop-20260926.json`에 보존했다. 별도 위젯·에피소드 release pin은 변경하지 않았다.

전환 뒤 `--check-release-set=passed`, `--check-cron=verified`, 9/28 PREOPEN·postclose `--print-plan` 모두 새 릴리스 경로를 가리킨다. PREOPEN publisher의 읽기 전용 실행은 `hold_source_gap`, `allowed_runtime_apply=false`였다. **메인 PID 0**이므로 실제 정책 소비·자연 비용 후 성과는 9/28 수용 대기다. 새 임계값 선택, bot restart, 주문은 실행하지 않았다.
