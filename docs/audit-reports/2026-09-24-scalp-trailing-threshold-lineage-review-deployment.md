# 스캘핑 익절 임계치 원천 연결 리뷰·배포 영수증

시각: 2026-09-24 22:46 KST. 범위: 메인 `scalp_trailing_take_profit`의 설정 원천·판정 관측·장후 소비. 임계치 값과 주문 권한은 유지했다.

## 구현·리뷰

- 기준 `2a099e1acff0c975abc221fc2d37d629ab11e794`에서 격리 작업트리 `feature/scalp-trailing-lineage-20260924`의 `60a657ae`, `ae307c39`, `cef02f562e061b38276fcc0f43a4f0e6cb0aed0a`를 검토했다. 메인 네 값의 bootstrap receipt/hash, fast·normal 입력 전이, 구조화 이벤트 분할 hash, 완료·열린 포지션 분모, 장후 보고서→sentinel/summary 소비가 연결됐다. 폐기 `SCALP_TRAILING_LIMIT`와 중복 spread 계산을 제거했다.
- 리뷰에서 빠진 receipt가 bootstrap 검증을 통과하고, 잘못된 구조화 이벤트 partition과 position ID 누락이 조용히 빠지는 결함을 발견했다. 마지막 커밋에서 각각 startup `fail`, projection `source_gap`으로 바꿨다. 기존 테스트 fixture도 날짜와 custody 증명이 없을 때 적격으로 계상하지 않도록 바로잡았다.
- 첫 targeted 실행: 95 PASS, 3 FAIL. fixture와 결손 처리 수리 후 306 PASS, 추가 보유 AI·runtime bridge·wrapper 영향 검사 59 PASS. Python compileall, `git diff --check` PASS. Kiwoom API 요청·parser·FID·복구 흐름은 변경하지 않았다.

## 날짜·결손 계약

- 트레일링 익절에는 별도 활성 날짜 스위치가 없다. 공통 launcher는 날짜가 맞는 bootstrap env·검증 영수증이 있어야 기동한다. `SCALP_FAST_EXIT_GUARD_ENABLED/ACTIVE_DATE`는 fast 손절 경로의 날짜 조건이다. 9/28 bootstrap에는 `ENABLED=true`만 있고 `ACTIVE_DATE`가 없어 그 파일만으로는 fast 손절 guard가 켜지지 않는다; 실제 PID 환경은 아직 없다. 익절은 실거래 SCALPING 보유, 수동 제어 허용, SELL 미대기, 유효 매수가·수량, 시작 수익률, 신뢰 호가·route 품질을 통과해야 한다. 정규 holding 경로는 이미 결정된 다른 SELL 신호와 opening rotation 우선순위도 따른다.
- bootstrap receipt와 네 설정값의 env/owner 중 하나라도 빠지면 새 검증기가 실패한다. 판정 전이 이벤트의 날짜/position ID가 불량하면 구조화 원천 상태가 `source_gap`이다. 보고서의 열린 포지션은 현재일 DB census만 사용하며 과거일은 복원 불가 상태로 남긴다. 시세·AI·주문/체결·비용 결손, bounded sample cap, 자정 경계는 후보 paired replay 적격에서 제외한다. 후보값과 live review 권한은 여전히 없다.

## 배포·다음 증명

- 관리 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/scalp-trailing-lineage-r1-20260924-cef02f56`, Git SHA `cef02f562e061b38276fcc0f43a4f0e6cb0aed0a`. 공유 `data/logs/tmp/.venv/docs/restart.flag`가 canonical workspace로 연결됐다. 이전 selector 백업: `tmp/runtime-release-selection-before-scalp-trailing-lineage-20260924-224625-809538.json`.
- 9/28 bootstrap 이전본은 `tmp/scalp-trailing-bootstrap-before-cef02f56-20260924-224533/`에 보존했다. 새 bootstrap의 env 차이는 익절 네 값과 `KORSTOCKSCAN_SCALP_TRAILING_VALUE_SHA256`뿐이다. selected family, operator lock, source incumbent는 동일하다. 새 `verify_bootstrap('2026-09-28')`는 PASS, PID는 없다.
- 전환 후 `--check-release-set` PASS, `--check-cron` PASS, 9/28 PREOPEN `--print-plan`이 새 릴리스를 가리킨다. 메인 `MainPID=0`, inactive이므로 실제 PID 소비와 자연 SELL·정확 비용·후행 가격·경제성은 미확인이다. 별도 widget/episode 서비스는 전환하지 않았다. release-set 검사는 기능적 건강을 평가하지 않으며 episode inventory에는 failed 28, inactive 94가 별도 남아 있다.
- 9/28 [현재 checklist owner](../checklists/2026-09-28-stage2-todo-checklist.md)의 새 자연 표본에서 position→input transition→signal→order/fill→cost→완전 사후창을 같은 ID/hash로 확인한다. 결손을 0 또는 미발동으로 채우지 않는다. 후보 grid의 첫 crossing·반사실 체결 비용·독립 holdout을 확보하기 전에는 튜닝값을 선택하지 않는다.
