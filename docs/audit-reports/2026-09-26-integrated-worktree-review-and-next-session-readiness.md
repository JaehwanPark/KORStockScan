# 9/26 통합 작업본 재검토와 9/28 장후 준비 점검

범위: 9/26 작업본의 코드·스크립트·테스트·문서, Main 선택 릴리스, 9/28 PREOPEN·장후 실행 owner. 이 기록은 코드/라우팅 준비와 향후 자연 실행·PID 소비·경제성을 구분한다.

## 재검토 및 수정

- 작업본의 코드·스크립트·테스트 바이트는 기존 선택 릴리스 `e61b5b05752e07cd34c93acc4132a56d29e19a76`와 같았다. 별도 차이는 체크리스트·기준 문서와 미커밋 검토 기록이었다.
- 시작값 회귀 하나는 실행 중 환경변수만 바꾸고 부팅 정책 hash를 유지하면서 기본값으로 되돌아갈 것으로 기대했다. M1 런타임은 검증한 벡터를 프로세스에 고정하는 계약이며 별도 고정·hash 교체 회귀가 있다. 해당 오래된 기대값을 고정 정책값으로 수정했다. 실시간 캐시·정책 변경 권한은 수정하지 않았다.
- 9/28 체크리스트의 익절 owner가 이전 `4ab3491d`와 `e61b5b05`를 현재 선택 commit으로 고정해 적은 부분을 실제 selector 영수증 대사로 바꿨다. 과거 배포 기록의 역사적 commit은 그대로 보존했다.

## 9/28 실행 준비와 남은 수용

- 로컬 KRX 달력에서 9/24·9/25는 휴장, 9/28은 개장이다. 평일 cron이 휴장일 9/25에도 장후 작업을 호출해 Main은 `scale_in_split_order_plan`의 `blocked_source_contract`/exit 2에서 중단됐다. 독립 `main_machine_policy`와 `episode_policy`도 휴장일 원천에서 실패했고, controller·strict verifier는 완료되지 않았으며 finalizer는 선행 실패로 종료됐다. 9/25 실패 영수증은 9/28 장후 완료 근거가 아니다. 이 건은 휴장일 예약/terminal 처리의 별도 운영 결함이며, 9/28 개장일 입력 적격 여부는 자연 실행으로 확인해야 한다.
- 9/23 Main 장후 status는 `succeeded`이고 첫 Main 승률 정책 terminal은 9/28 대상 `staged`, `initial_adopted`, `current_unchanged`다. 9/28 PREOPEN 이전 발행과 당일 activation·bootstrap·PID 소비는 서로 다른 단계다.
- 장후 cron 전수 대사에서 20:50 `archive` 예약이 빠져 있었고 마지막 실행은 9/16이었다. 기존 선택 release router 경유 예약을 복구하고 cron 검증을 전체 활성 8개 owner에 적용했다. 21:05 paired replay는 현행 수동 호환 wrapper이므로 예약을 복원하지 않았다. 9/28 archive의 실제 terminal은 별도 수용한다.
- 현재 selector `e61b5b05`에서 release-set/cron 검증과 9/28 PREOPEN·postclose·finalize print-plan이 정상이다. Main 서비스는 inactive/MainPID 0이다. widget/episode 별도 pin은 현재 selector만으로 변경되거나 검증된 자연 실행이 되지 않는다.
- 9/28에는 Main·controller·tuning·widget·machine final refresh·finalizer의 같은 원천일 terminal, postclose exit 세 원천/manifest hash, summary/checklist/strict, cleanup/detector, 다음 장전 정책·PID를 각각 확인해야 한다. 정책 후보 없음·자연 M1 표본 없음·비용 결손은 EV 0이나 수익성 PASS가 아니다.

## 검증 경계

대상 Python 회귀, compile, `bash -n`, `git diff --check`, 체크리스트 print-only parser, release-set/cron 및 9/28 print-plan으로 코드·라우팅을 검증했다. 장후 wrapper 본실행, provider 호출, 주문, bot restart, Project/Calendar sync는 수행하지 않았다. 통합 commit·새 불변 릴리스의 정확한 SHA와 선택 시각은 `data/runtime/runtime_release_selection.json` 영수증이 소유한다.
