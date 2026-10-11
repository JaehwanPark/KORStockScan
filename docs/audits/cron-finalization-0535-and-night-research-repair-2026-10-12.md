# 최종화 05:35 예약·야간 연구 계약 보완 — 2026-10-12

범위: 사용자가 승인한 최종화 05:35 실제 예약 변경·기타 결함 보완·배포. 현재 코드 리뷰 및 workspace 회귀 282건 PASS이며 불변 릴리스 검증과 정식 인계 결과는 아래 후속 기록으로 구분한다.

## 보완 사항과 리뷰

- 오늘 서버는05:30:53, cron은05:30:58에 기동해05:00 예약을 놓쳤다. 최종화 예약을05:35로 변경한다. 선행 대기 마감06:00, 전체 종료06:50, 스캐너07:20, PREOPEN07:35, Main07:55는 유지한다. 선행 대기는 실효25분이며 기존3,600초 설정으로06:00을 넘길 수 없다. 서버가05:35 이후 기동하면 예약은 여전히 누락될 수 있으며 새 catch-up 실행 권한을 만들지 않는다.
- [라우터](../../src/engine/infrastructure/runtime_release_router.py)는05:35·`POSTCLOSE_FINALIZATION_0535`를 정규 계약으로 생성하며05:00·06:00·21:55 구 marker는 migration 입력으로만 처리한다. 재설치가05:00으로 되돌리지 않도록 idempotence/이행 회귀를 검증했다.
- [크론 감시기](../../src/engine/error_detectors/cron_completion.py)는 finalization/cleanup을05:35부터 검사하며06:50 완료 및 직전 KRX source-date/원 terminal generation 검증을 보존한다.05:34의 미도래와05:35의 결손 관측을 구분했다.
- [야간 연구 검증](../../src/engine/automation/main_market_weakness_research.py)은 전체 crontab 순서 equality 대신 해당 owner의 exact 행을 검증한다. 줄 위치 변경은 허용하지만 시간·명령·중복·설치 코드 SHA·Main 준비 calendar의 변경은 거부한다. 기존 야간 창·자원·호출/알림 설정은 유지한다.
- [연구 wrapper](../../deploy/run_main_market_weakness_research_postclose.sh)는 기존 owned-log runner로 `logs/main_market_weakness_research_cron.log`에 disposition을 보존한다. cron MTA 부재로 stdout이 폐기돼도 보류·실패 원인이 남는다. 선택 릴리스 재라우팅과 report-only/주문 금지 경계는 유지한다.

## 검증과 적용 경계

workspace 회귀282 passed, Python compile·shell syntax·diff 검증. 크론 행 위치3가지와 시간/명령/중복/Main 시간/code hash 변조5가지, owned-log 수신·선택 release wrapper, 구 marker migration·예약 재설치·감시 창 경계를 검사했다. 관련 묶음은 불변 릴리스에서 다시 검증한다. API/Provider/AI/주문·장후 전수 연구는 실행하지 않는다.

새 릴리스는 `cron-0535-night-repair-20261012-v1` / `5ca5f585b104bb4c441f949d4051ff090a9c0e9a`다. 원 EOD·수량·기계/보조·holding/stop/trailing/delay 정책값을 보존하고 source10/8→target10/12의 summary/checklist→strict/controller→PREOPEN을 정식 CAS successor로 결속한다. 실제05:35 예약의 첫 자연 실행과 야간 연구의 다음 자연 실행은 발생 후 별도로 수용한다. 오늘 이미 지난05:35를 실행 성공으로 표시하지 않는다.

[작업 근거](../../tmp/cron-0535-repair-20261012/)에 테스트·배포·예약 이전 bytes와 전환/준비 결과를 남긴다.

## 실제 배포·예약 설치·정식 종료

- workspace와 불변 release에서 각각282 passed(동일 묶음이므로 합산하지 않는다). 검토한7개 source/test 파일의 bytes가 workspace/release와 일치한다. 실제 설치 readback은 후보 crontab 전체와 동일하며 변경은 finalizer 한 행뿐이다. 필수8경로·release-set 검증PASS다.
- 첫 인계 시 재발행일10/12를 새 정책 publication으로 넣으면 다음 영업일 적용13일 계약을 요구해 `stage_date_contract_invalid`가 발생했다. [첫 실패 원본](../../tmp/cron-0535-repair-20261012/formal-handoff-attempt1.log)을 보존하고 전체CAS rollback·기존PREOPEN PASS를 확인했다. 정책 재선정 없이 원 publication10/11·effective10/12를 유지하는 코드 인계로 보완했다. [성공 CAS](../../data/runtime/research_release_transition/cron_0535_night_repair_20261012_v2/transition.json)는verified다.
- [정식 인계](../../tmp/cron-0535-repair-20261012/formal-handoff.json)의 summary/strict/controller와 exact-date PREOPEN은PASS다. 승인된 수동 native finalization은 **07:12:10 KST DONE, exit0**이며 current chain/snapshot의issues0이다. [최종 재검증](../../tmp/cron-0535-repair-20261012/final-readiness.json)은 2026-10-12T07:12:51.454873+09:00 기준 `current_full_contract=pass`다. 원EOD·기계/보조·초기수량·holding/stop/trailing/delay 정책값은 보존했다.
- 이번 수동 복구는06:50 cutoff 뒤라 [cron detector](../../tmp/cron-0535-repair-20261012/cron-detector-final.json)가`recovered_late` warning으로 기록한다. 실제05:35 예약 실행이나 정상 마감으로 바꾸지 않는다. 미래 예약의06:00/06:50 guard는 그대로며 다음 영업일05:35 자연 실행은pending이다.
- 야간 연구 installation을 새code SHA에 재결속하면서 uid·calendar·야간 시간·알림 및 기존 예산 설정을 보존했다. 실제 wrapper를 야간 창 밖에서 실행해`outside_night_window` 무연구 보류를 확인했고 owned-log에disposition이 저장됐다. worker reservation·Provider/AI/Telegram/주문 호출0이다. 다음 자연 야간 연구 성공은 아직 미관측이다.
- 기존10/12 `DirectFamilyPreopenPolicyHandoff` 한 owner가07:35/07:55 새 릴리스/정책 PID 소비를 확인한다. 현재 실제Main PID 소비는false다. 이 작업에서 봇을 조기 기동하거나 재기동하지 않았다.
