# Main 약세 연구 반복 리뷰·배포 — 2026-10-09

사용자가 반복 수리와 배포를 승인했다. 약세 관찰/독립 장후 연구와 발견된 AI 기록 결함이 이번 배포 범위이며, 별도 보유청산 작업본은 보존한다. 정책 발행·실주문·강제 봇 시작·수동 연구 재생성은 수행하지 않는다.

## 수리와 재리뷰

- 기계 관측이 AI payload 파일을 먼저 만들 때 request 인덱스가 무효화되는 결함을 수리했다. key 없는 행도 정확한 검증 prefix만 이어가며, 이미 쓴 bytes로 tail을 갱신해 추가 파일 재읽기나 본문 복제를 하지 않는다.
- 정상 JSONL 행 뒤에 미완성 tail이 있을 때 hot 준비가 ready=false를 반환한 채 다음 request를 붙일 수 있던 결함을 수리했다. 미완성 tail은 명시적 결손이며 파일을 변경하지 않는다.
- 새 inode·외부 append·미검증 과거를 건너뛰지 않는 회귀, 150KB 기계 관측 뒤 추가 read 없이 request capture를 이어가는 회귀를 추가했다. 기존 5개 실패를 포함한 관련 테스트 148건 통과.
- root가 ubuntu 예약을 설치하면 namespace 소유권이 root로 남는 결함을 수리했다. cron 실제 재조회가 일치해야 설치 성공으로 표시한다. 연구 전용 테스트 99건 통과.

## 배포 검증

리뷰한 15개 코드·wrapper·테스트 파일의 hash로 현행 selected release의 후속 immutable release를 만들었다. 작업본과 불변 릴리스에서 **각각 572개 테스트 모두 통과**했다. 기존 실패 5개도 실제 codec 통합 경로에서 통과하며 skip/xfail로 숨기지 않았다. Ruff·compile·두 wrapper의 `bash -n`·`git diff --check`를 통과했다.

- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/main-market-weakness-20261009-v1`
- commit: `7e1a826318e7b8418afd2e2436b79bf2febf8f67`; 부모 `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`
- [배포 원천·hash](../../data/report/main_market_weakness_deployment/2026-10-09/build.json), [작업본 검증](../../data/report/main_market_weakness_deployment/2026-10-09/review-tests.txt), [릴리스 검증](../../data/report/main_market_weakness_deployment/2026-10-09/release-tests.txt)
- [다음 기동 준비](../../data/report/main_market_weakness_deployment/2026-10-09/prepared-verified.json): source `2026-10-08`, target `2026-10-12`, 새 selected release 결속, `current_full_contract=pass`, `actual_pid_consumed=false`
- [필수 cron](../../data/report/main_market_weakness_deployment/2026-10-09/cron-routing.json): 8개 경로 검증. [릴리스 집합](../../data/report/main_market_weakness_deployment/2026-10-09/release-set-after.json): 퇴역 서비스/설치본 복구 없음.
- [Optional 설치](../../data/report/main_market_weakness_deployment/2026-10-09/optional-install-verified.json): ubuntu(uid 1000) 한 곳, `40 0-5,21-23 * * *` KST, namespace/설정 소유권 일치, 기존 cron bytes 보존. `notify_enabled=true`는 계획의 적격 관리자 안내이며 실제 발송은 아직 없다.
- wrapper를 실제 selected 경로로 확인한 결과 낮에는 `deferred_resource_or_window / outside_night_window`로 종료했고 무거운 연구를 시작하지 않았다.
- [Finalization 원천 연결](../../data/report/main_market_weakness_deployment/2026-10-09/finalization-verified.json): source 10/8의 controller·strict·checklist·4종 snapshot 현재 hash 검증 PASS, `strict_checklist_generation_stale` 없음. 10/8 최종화 완료 marker는 다음 영업일 10/12 예정으로 별도 구분하며 생성했다고 주장하지 않는다.

배포 전의 기존 미커밋 파일 중 이 작업에 속하지 않는 파일은 hash로 보존했다. 10/12 checklist SHA `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9`도 그대로다. 작업본의 별도 보유청산 구현은 이번 릴리스에 포함하지 않았다.

## 남은 자연 수용

현재 Main은 정지 상태를 유지하며 10/12 07:35 PREOPEN·07:55 예약기동을 준비했다. 새 release의 실제 PID 소비·첫 mixed-row 자연 기록·첫 야간 연구 terminal→누적→알림 disposition·실제 적격 안내는 아직 관측하지 않았다. 표본과 actual cost가 없는 곳은 U/미평가이며, 이번 코드·배포 검증은 정책 개선/수익 개선의 증거가 아니다. 운영 연구/원 producer 재실행·실제 AI 호출·Telegram 수동 발송·강제 봇 시작은 없었다.
