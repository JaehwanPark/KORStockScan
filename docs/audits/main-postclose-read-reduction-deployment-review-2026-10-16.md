# 반복 읽기 개선 재리뷰·배포·07:55 기동 수용 — 2026-10-16

사용자가 코드리뷰·수정보완 반복 후 배포와07:55 정상기동 오류 확인을 명시했다. 기준 구현은 `5af75ddb7cbc219b91c45b238c6be9f8540a2ed9`, 원 선택본은 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`이다. 구현1922개 PASS와 격리 입력 읽기량66.7% 감소는 [원 구현 리뷰](main-postclose-read-reduction-implementation-review-2026-10-16.md)의 결과이며 실제 배포·기동 수용과 구분한다.

## 재리뷰와 보완

07:38 확인 당시 기존 선택본의 정규 PREOPEN이 실행 중이었다. 도중에 selector를 바꾸지 않았다. PREOPEN은07:40:43 succeeded/exit0, bootstrap native 검증은 PASS/findings0으로 완료됐다. 당일 기계 bundle은 `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`로 정규 활성화됐으며 이를 신규 코드의 활성화로 재라벨링하지 않는다.

배포 리뷰에서 delay 코드 계약에 원천 검증 구현 파일도 포함됨을 확인했다. 검토한 source verifier를 바꿨다는 이유로 기존 준비 정책의 code pin을 재작성하지 않는다. 기존 `intraday_release_handoff._verify_entry_code_delta`의 정확한 source-pair 계약에 아래 한 파일만 추가했다.

- 파일: `src/engine/scalping/pre_submit_delay_initial_policy.py`.
- 원 SHA: `ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0`.
- 검토 SHA: `037af000399c501362c62a63e4361501c041e3db0289b1edd059b839e36e0a47`.

검토된 전체 파일 쌍만 인정한다. 임의의 `verify_source` 함수를 허용하는 AST allowlist를 만들지 않았다. 별도 AST 투영에서 변경 함수가 `verify_source`뿐이며 나머지 producer·qualification·selection·정책 상수가 동일함을 확인했다. native 기계 계약37개 파일도 선택본과 모두 동일하다. [원천 코드 대사](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/producer-code-projection.json).

기존 인계·ordered 배포·digest·delay 시험을 다시 수행해 **1995 PASS**를 확인했다. 원/후속/dirty/source-digest 변조 거부와 readonly 동작의 parameter matrix에 새 source map과 해당 producer 파일을 포함했다. 정책 값·원 보고서·원천 봉인·계좌/주문/수량·hard safety와 원 phase deadline은 그대로다.

## 배포 순서와 원본 보존

원 선택본·현재 정책·수동 제외·원 체크리스트·당일 PREOPEN/bootstrap/env/verify·prepared index/readiness10개를 [배포 전 manifest](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/before-manifest.json)에 결속해 private backup으로 보존했다. secret/env 내용은 출력하지 않는다.

당일 PREOPEN을 이미 열었고07:30 code-refresh 경계를 지났으므로 준비본을 새 코드로 재발행하지 않는다. 기존07:55 정기 기동의 native PID 소비를 확인한 뒤, 검토 candidate의 기존 ordered driver로 predecessor 검증→graceful drain→selector→동일 정책 handoff→native 기동/새 PID attestation을 수행한다. 진행 중인 wrapper·이전 PID 위로 selector를 먼저 바꾸지 않는다. 원 PREOPEN·bootstrap·정책을 유지하며 이전 PID와 새 PID의 결과를 분리한다.

실행 owner는 기존 `DirectFamilyPreopenPolicyHandoff`다. 원 봉인 체크리스트 bytes와 OPEN stable ID를 보존하며 새 배포 인계는 별도 감사/transition 영수증으로 남긴다. 배포 후보·실제 기동·오류 탐지의 최종 결과는 아래 후속 영수증까지 미완료다. 코드 PASS를 실제 PID 소비·자연 주문·비용 후 성과로 확대하지 않는다.


## 07:55 첫 기동과 배포 중 발견한 결함

07:55:02 정기 launcher가 기존23a13aba6을 기동했다. Main PID2934092/start_ticks16890468의 native bootstrap은07:57:03 PASS, selector의 실제 소비 영수증은07:57:14에 기록됐다. 따라서 정기 기동은 실제 PID까지 확인했다. 다만07:57:29 I/O wait37.19% >=35% resource ERROR 한 건이 발생했고,07:58:59 full detector에서21.11%/PASS로 회복했다. 최초 기동을 오류0으로 보고하지 않으며 원 error122바이트를 보존한다.

승인 ordered 배포의580d5865b 시도는 graceful drain과 selector 게시 후08:01:27 `intraday_bootstrap_invalid:main_stop_confirmation_invalid`로 실패했다. 상세 원인은 `stop_vote_source_set_changed`다. 실패 transition/원 selector/PID 증거/owned startup hold를 보존했고 Main이 정지한 상태에서 복구를 검토했다. 실패 디렉터리를 재사용하거나 원 FAIL을 PASS로 고치지 않는다.

원천 대사에서 추가/누락 파일은0이었다. 기존 holding vote 파일의763,760바이트 SHA는 원 봉인과 같았고, 오늘08:00:03 관측2행2,104바이트만 추가됐다. 두 행은2026-10-16의 SOURCE_GAP/INSUFFICIENT이며 과거 정책 입력으로 소급하지 않는다. 별도10/14 AI 원천3개는 lossless gzip이고 원 decoded 크기/SHA 모두 일치했다. [대사 증거](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/stop-vote-content-reconciliation.json).

기존 carried reader의 미래 tail 분리는 `vote_source_inventory == {}`만 허용했다. 실제 보고서는7개 vote 원천을 소비했으나9개 cell 모두 source_gap/비선정이어서 정상 당일 append도 실패했다. 새 reader는 publisher가 봉인한 path/stat/decoded SHA/크기가 consumed inventory와 정확히 같을 때만 기존 prefix 전체 SHA와 후속 행의 날짜/session/position/schema/완결성을 native writer shared lock 아래 검증한다. 검증한 identity와 dependency identity도 일치해야 한다. 과거 구간 변조·inode replacement·같은 날짜/부분행·비봉인 prefix·검증 후 append는 거부하고 full research/selected policy는 엄격히 유지한다. 원 보고서/정책/원천은 수정하지 않는다.

정지 복구는 기존 automation owner의 embedding-only `StoppedDeploymentRecovery`로 제한한다. 정확한 selected-phase handoff 실패, 원 live-captured native PID proof, 원 selector/PREOPEN/prepared/policy, Main/원 supervisor/tmux 부재, 추가 restart 요청 부재, candidate 세 code gate와 owned hold의 CAS를 요구한다. 원 실패 selector/status/hold를 새 attempt에 별도 보존하고 새 native proof는 같은 역사적 소비 증거에 후보 commit만 결속한다. 소비 영수증을 합성하지 않는다. native prepare/bootstrap/auxiliary/launcher/독립 PID 검증은 일반 배포와 동일하다. 기존 CLI는 이 복구를 자동 선택하지 않는다.

반복 리뷰 후 인계·배포·stop·digest·delay 시험 **2219 PASS**, Python compile6개와 diff 검사 PASS다. source-pair는 main_stop_postclose.py의 원 SHA `e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13`와 검토 SHA `cce1f797bd17f5ddde0aa5eec68cdb285c224e198fea7bb184d03a444ff32c05`에 한정한다. 숫자 정책이나 원 준비 code pin은 바꾸지 않는다. 신규 복구의 실제 실행/PID 소비/후속 detector 수용은 후속 영수증으로 확인한다.

08:02:53 별도 작업이 운영 checklist의 기존 시장약세 OPEN에 근거1행을 추가했다. 원 봉인f9b27df0…와 현재394a2f6e…를 별도 보존하며 이 동시 변경을 되돌리거나 배포 체크리스트로 덮어쓰지 않는다. 목적/강제 규칙과 OPEN owner 집합은 동일하다. 복구는 현재 editable bytes를 보존하고 원 strict-bound snapshot을 독립 검증한다.


## 6cf45b5c 통합과 optional code/calendar 인계

사용자가08:14 전후 `6cf45b5cfa095897c1e5a346ac91af0512be6604` 통합 및 optional 연구의 code/calendar 재결속을 추가 지시했다. 진행 중 a94b54afa의 native 복구는 원 소비 증거를 먼저 닫고, 검토 커밋은 작업 branch에 실제 두 부모 merge로 통합했다. merge `2f4e7bdc09832e78ad35f2270ffa3afc345a1c7b`에는 원 커밋이 ancestor로 남는다. 통합 코드13 suites **2508 PASS**, compile·shell syntax·diff·print-only parser를 통과했다. optional module 외 Main/native machine/stop/delay/holding 계약 소스는 a94b54afa와 같다.

최종 통합본은 승인된 배포의 후속 native handoff로 actual PID까지 확인하고, optional installer는 기존 ubuntu 한 사용자 scope를 보존하여 호출한다. 일반 신규 설치 기본값을 쓰거나 새 스케줄/worker를 추가하지 않는다. 원 `enabled=true`, `notify_enabled=true`, `installed_at=2026-10-09T11:58:21.225157+09:00`, `installed_source_date=2026-10-09`, `evidence_start_date=2026-09-29`, 원 후보/outbox/rotation/night reservations를 유지한다. code hash/재결속 시각/직전 installation ancestry와 현재 선택본만 갱신할 수 있다. 실제 crontab bytes 및 원 Main07:35/07:55 calendar를 재조회하고 새 선택본에서 `verify_installed_calendar`를 확인한다. installer의 다른 사용자/root 중복 schedule census는 권한 있는 named-user installer로 수행하고 runtime verify는 ubuntu UID에서 별도 수행한다.

연구 원천 재계산·worker 강제 실행·예약 확대·Telegram 발송은 이 재결속에 포함하지 않는다. 다음 허용 야간의 최신 source/backlog 진전·pending/migration·누적/알림 disposition은 기존 `MainMarketWeaknessPostcloseObservation1008` OPEN의 자연 수용이다. 코드 배포나 설치 PASS를 미래 야간 완료·매매·경제성으로 보고하지 않는다.


## 장중 추가 SELL terminal outbox 세 건의 수리

사용자가08:19에196170/005930,08:25에034020의 `SELL_PARTIAL_LIFECYCLE_OUTBOX_PENDING`을 전달했다. 당시 최종4c4fec0bb 배포는 preflight였고 startup hold/selector 변경/드레인 전에 driver만 SIGINT로 정상 중단했다. 원 a94b54afa Main PID2940050은 계속 실행됐다. 이 중단 시도의 원 status/KeyboardInterrupt를 보존한다.

실제 봉인 leg는 모두 `sell_completed`다. 이름에 PARTIAL이 있어도 부분체결로 오분류하지 않는다. 원 snapshot을 private 증거로 보존했다. 기록49300/196170의 key6eab6d8c…,49328/005930의 key5545ec16…,49267/034020의 key31a24908…는 원 주문/체결번호·잔량0·qty/unit contract·broker provenance·제출 custody가 유효하다. BUY-generation과 TP signal/bundle도 같은 record에 결속되지만 leg의 candidate_stock에 scanner/entry trace가 없다. 기존 trace-only native receipt 경로도 ACK할 수 없어 재시도 중이었다. 비용 실제 reconciliation은 `cost_source_unavailable`로 남는다.

새 `broker_position_sell_receipt_v1`은 이 overnight terminal 범위만 인식한다. 기존 trace가 없고, 실제 broker 체결·완전한 qty/unit·잔량0·확정 제출 custody/no source gap·동일 record BUY generation/TP lineage·원 ingress clock이 모두 일치해야 한다. scanner의 기존 lifecycle 경로를 대체하지 않고 entry trace/Main lifecycle ID를 합성하지 않는다. 원 leg/hash/field 전부를 보존하고 generated identity만 append 결과에 넣어 엄격히 검증한다. scanner·simulation 격리 회귀에서 outbox snapshot의 simulation_book/owner 보존 누락도 보완했다. native ACK는 추가 주문 권한이나 실제 비용/수익 검증이 아니다.

원 세 leg의 오프라인 리허설은 실제 journal 쓰기·provider·주문0으로 emit 계약 PASS, 원 leg/hash 불변을 확인했다. [세 leg 리허설](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/sell-outbox-offline-rehearsal-all-three.json). 위치/BUY/bundle/신호/결속/broker/custody/source-gap/수량/unit/잔량/시각/partial/trace/event 변조를 거부하고, 기존 scanner 경로·idempotent ACK·실제 비용 미상 보존을 시험했다. wire/parser/FID/주문 API는 수정하지 않았다.

선택23a13aba6→검토 receipt 파일의 정확한 쌍을 `REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES`에 결속한다. holding capability 후속은 전체 `39d0f10c41b661a3d8ea794ff66bfa86b55fab31351062bfb41463bb943bbfe5`다. 통합 시험이 auxiliary의 낡은 successor hash도 발견했고, 실제 선택23a13aba6 자체가 이미c2c4bc10…임을 재현했다. 그 family의 모든 component는 선택23과 byte 동일하다. 기존 원 계약88a49610…→현재c2c4bc10…의 exact pair를 갱신하고 fresh 네트워크 차단 fixture를 별도 요구한다. 과거 계약/보고서/정책 code pin을 바꾸지 않는다. native-v6 계약37개는 unchanged여서 정책 code refresh를 새로 발행하지 않는다.

다음 승인 배포 후 세 original key가 native replay로 ACK됐는지, final pending/기록 terminal 및 다음 자연 detector를 확인해야 운영 수용이다. journal 강제 편집·수동 replay/SELL·historical FAIL 삭제는 수행하지 않는다.
