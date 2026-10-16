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


배포 전 최종 검증은 통합16 suites2813 PASS, Python compile/diff/parser PASS다. 추가 실제 dated reader 대사에서 source10/15 holding 보고서가 이미5658a73a…를 원 code로 가지고 있음을 확인했다. 역사적b2087e97… source와 이 후속 source를 각각 같은 검토39d0f10c…에 exact pair로 결속하며 임의 origin/current는 거부한다. 관련 역사 보존/변조 회귀를 두 source-map에 확장해303 PASS를 확인했다. 보고서와 원 contract/code/FAIL 상태는 그대로고 현재 reader capability만 검증한다.

새 네트워크 차단 fixture는 holding91개/auxiliary83개, 합계174 PASS·네트워크 시도/provider/order0·보호 산출물 불변으로 발행됐다. 현재 native 관측은 entry_cancel_wait/rising_missed/holding_vote의 source10/15와 auxiliary의 실제 기존 source10/14를 구분해4개 모두verified다. source10/15 auxiliary evaluation.json은 없으므로10/14를10/15로 재라벨링하지 않는다. 실제 source/comparison gaps와 비용 미상은 보존한다. [날짜별 reader/fixture 대사](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/preserved-date-native-preflight.json).


## 실제 통합 기동·세 terminal ACK·optional 재결속

b4d23f65815f4326caab9d89513b816a0abc082a의 ordered 배포는08:36:58 PASS다. 선택 release의 실제 Main PID2961613/start_ticks17126763과 native bootstrap·selector 소비를 확인했다. 6cf45b5c는 실제 ancestor다. 원07:55 기동의 I/O 경고 및 두 중단/실패 시도는 별도 보존한다.

08:37:00 새 Main의 정규 startup recovery가 세 원 leg key를 모두 broker_position_sell_receipt_v1으로 append하고 해당 pending journal을 native ACK 후 제거했다. DB read-only 조회에서49300/49328/49267 모두 COMPLETED다. 수동 주문·journal 편집0이며 원 비용은 cost_source_unavailable다. [세 terminal 수용](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/native-sell-terminal-acceptance.json).

같은 선택본의 native named-user installer로 ubuntu optional code/calendar를 재결속했다. 기존 enabled/notify/설치 시각/source floor/예산과17개 야간·후보·cursor 파일 SHA를 보존했다. code hash f6f009128fb691f482170f062fd75ff793cc2b4dd5d65122f0532c4bf54bcc1a, calendar hash18df578a22076af4b963aa168e2f77c41f7df9b210f24dce1baad8f3ff229603이며 ubuntu 비특권 verify_installed_calendar는 true다. [설치 검증](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/optional-unprivileged-verification.json). 자연 야간 수용은 기존 OPEN이다.

## 08:42 observer 경고와 보유 감시기 시각 오류 보완

08:38 log_scanner는 배포 전 누적134개 오류를 뒤늦게 읽어 ERROR를 발행했고08:39:49 새 오류 없이 PASS로 회복했다. 그 원 이력을 삭제하지 않았다. 별도로 정규 holding_exit_sentinel은 raw/legacy cache에 혼재한 offset-aware/naive clock을 정렬하며 TypeError로 실패했다. 기존 KST wall-time 계약에 맞춰 파싱 경계에서 aware 시각만 KST naive로 변환한다. 원 raw bytes·microsecond·cache schema와 시간창을 보존하고 UTC/KST/naive·기존 cache/cutoff parity를 검증했다.

cron_completion은 holding_exit_sentinel 한 owner에만 기존 엄격한 owner_terminal_recovery를 opt-in한다. 같은 owner의 후속 정규 DONE만 앞선 FAIL을 supersede한다. ERROR/새 FAIL/START/SKIP/다른 owner DONE은 복구 영수증이 아니며 이전 error count/log는 보존한다. 기존 Buy Funnel 동작과 다른 cron/postclose는 변경하지 않는다. 실제 다음 정규 DONE·신선한 report/receipt와 detector를 최종 수용으로 요구한다.

08:42 ERROR의 실제08:40 observer 원본은 현재 PID trace4개가 전부 source_quality_blocked_before_assessment이고, machine/provider/요청/전송/PASS0이었다. 요청·pending journal은 첫 호출 전 lazy 생성되어 FileNotFoundError였다. 완전한 현재-actor trace와 전부 알려진 평가 전 차단, 모든 auxiliary/lineage 카운터0, 빈 ledger/gap, 정확한 두 native 부재 shape를 함께 증명할 때만 bounded_source_quality_observation/warning_pending을 허용한다. 원천을 유효한 빈 입력으로 만들지 않으며 source gap·partial·diagnostics·runtime admission false를 유지한다. Permission/I/O/partial/actor/설명되지 않은 trace/호출·PASS1건/잘못된 count는 계속 실패한다. 원본 불변 재현은 [08:42 health rehearsal](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/observer-0842-health-readonly-rehearsal.json)이다.

observer의 observation_health_projection 외 AST는 동일하고 native-v6 37개와 네 capability component는 byte 동일하다. 원 정책/code pin을 재발행하지 않는다. 해당 observer의 원203b3978…→검토19bdf1e4… 전체 SHA 쌍만 기존 code handoff에 추가한다. 보완7 suites **3082 PASS**, 앞선 sentinel/cache/cron167 PASS와13개 경고 경계 회귀는 중복 합산하지 않는다. Python compile·diff·print-only parser 후 immutable 후보를 새로 배포하고 실제 PID/다음 자연 cron/전체 detector로 닫는다. 코드 시험을 실제 오류 해소나 완전 원천 검증으로 보고하지 않는다.


## 3c814c05c 자연 기동과 09:01:47 추가 경고

3c814c05ca979530e38f19bdc68f328c11116f4d ordered 배포는08:57:51 PASS다. Main PID2984178/start_ticks17249376의 실제 selector 소비·bootstrap·정상 loop 및 같은 PID/commit의 WS connected/writer_loss0/projection_errors0을 확인했다. WS 등록 근거는 local_sent_registry_not_broker_ack다.08:58 독립 대사에서 새 error bytes0·hold/restart 요청 없음·optional UID1000 code/calendar 검증 true·17개 역사 SHA 불변·세 원 SELL journal 부재를 재확인했다. [실제 기동 대사](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/final-native-acceptance.json).

08:55 정규 보유 감시기는09:00:35 DONE으로 회복했다. 첫 성공 경로는334초이며 기준일 raw/cache를 읽었다. 이 비용을 개선 완료나 warm 성능으로 보고하지 않는다.08:55 제출 감시는 인계 미완료 때문에 native startup_pending/exit75로 보류됐고09:00 정규 재실행은09:01:46 completed/partial이다. 모든 원 이력은 남는다.

사용자의09:01:47 holding_semantic_receipt_missing_after_due는09:00:01에 시작한 detector가 아직 미완료였던 보고서를 읽은 경고다.09:01:58 이후 native detector는 해당 당일 JSON을 native_validated=true/observation_complete=true로 검증했다. 누락 경고는 실제 후속 소비로 닫혔다. semantic status는 policy_binding_gap이며49300의 tp_mechanical_policy_contract_invalid, 세49328/49267/49300의 tp_first_crossing_transition_missing 및 비용 unavailable/strict completed0은 보존한다. 과거 누락 transition을 합성하거나 비용을0으로 채우지 않는다.2835개의 sell_completed는 재시도 중 남은 원 terminal event 행 수이며 새2835개 체결/주문이 아니다. 원 lifecycle는 세 broker 주문을 별도로 결속한다. 기존 HoldingProfitExitSourceContractRepair의 원천/정책 결손 OPEN이다.

09:00 현재 PID 관측에서 새 경계를 발견했다. 평가 시도0·완전한 trace·native actor/source/policy/selection 검증이 모두 통과했지만 lazy pending 파일의 부재 하나만 health 실패였다. 이전 평가 전 차단 수리는 실제 trace1개 이상을 요구하여 이 경우를 놓쳤다. 보완은 strict unmet set이 정확히 source_window_not_complete:pending 하나이고 n/provider/entry_trace가0일 때만 해당 pending의 정확한 FileNotFoundError shape를 bounded 경고 경로에서 인정한다. 현재 actor birth와 모든 native reader/코드·날짜·출처 검증은 그대로 요구하고 다른 미충족·I/O·부분 trace·호출·정책 불일치면 거부한다. 원 실패 조건과 partial·허용 권한false는 남긴다. [실제09:00 원본 불변 재현](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/observer-0900-health-readonly-rehearsal.json).

관측 경계8개 회귀의 초기 positive 재현 실패와 시험 fixture의 bounded-suffix 누락 보완을 보존했다. 최종8개 PASS 후 같은7 suites와 compile/diff/print-only parser를 재검증한다. observer exact successor는 a1284490d780a882b8c7591765ccf5f081b53cf9320fe350d03b620263310e55다. native-v6/네 capability/optional code hash는 변경하지 않는다. 새 immutable 배포와 후속 자연 detector로 실제 수용하며 현재3c의 잔여 pending ERROR를 코드 검증만으로 해소됐다고 보고하지 않는다.

추가 보완7 suites의 최종 결과는 **3090 PASS/16.79초**, Python compile·diff·print-only parser PASS다.09:04:48 자연 detector는 cron/process/resource/log/auth/lock6종 PASS였고 artifact의 유일한 FAIL은 pending 원천 부재다. 추가 배포 수용은 다음 실제 native 영수증으로 확인한다.


## 09:06:39 policy_binding_gap의 실제 원인과 제한 수리

09:05 자연 observer는09:05:42 completed/partial(10.48초),09:06:39 full detector는 FAIL0이었다. 사용자 추가 alert는 영수증 누락이 아닌49300의 실제 tp_mechanical_policy_contract_invalid다. 새75d6318c4 배포는09:06:42부터 preflight였고, 새 결함을 포함해 리뷰를 닫기 위해 hold/selector/드레인 전에 driver만 SIGINT로 중단했다. Main2984178은 계속 실행했다. 원 failed-phase preflight/KeyboardInterrupt를 보존한다.

원 캐시1,410,817바이트의 제한 읽기와 당시 PID2934092의 봉인된 원 receipt를 대조했다. 예외는 PreparedPin.prepare의 trailing_situation_pin_invalid다. 원 legacy pin은 target:49300:196170/BASE/legacy_context_unbound/entry_at0이며 유효한 원 classification_origin_hash를 가진다. 현재 native transition/signal의 position_key는 record:49300이다. 보고서 소비자가 두 identity를 무조건 같게 요구해 부모 BASE로 실행한 원 신호를 invalid policy로 잘못 분류했다. snapshot의 pin은 native logger가 Python dictionary repr로 기록했다. 원 bytes·신호·pin·정책은 수정하지 않는다.

수리는 기존 scalping/holding_profit_exit_semantics.py의 보고서 검증 경계에 둔다. 같은 record의 실제 두 source row에서 종목 코드도 같을 때만 record/symbol context를 전달한다. target:id:symbol이 정확히 맞고 BASE/legacy_context_unbound/entry_at0/no classifier/no feature, 유효한 BUY-generation64SHA와 원 pin hash가 모두 맞을 때 legacy pin 자체를 준비한다. 유효 값은 기존 승인 부모 vector와 완전히 같아야 한다. 분류된 pin·다른 id/symbol·세대·정책·threshold·origin 불일치는 계속 거부한다. 원 target pin을 record pin으로 재작성하지 않으며 Main/주문/provider/정책 값은 바꾸지 않는다.

native snapshot repr는 최대4096자의 정확한 flat8-key literal만 AST로 구조 검사 후 literal_eval한다. 코드 실행·함수·중첩 값·중복 키·초과 크기는 거부한다. JSON/dict 기존 형식과 원 pin 검증을 유지한다. foreign record pin의 기존 실패 계약도 보존했다. 기존 test_holding_exit_sentinel.py에21개 양·음성 회귀를 넣어 전체71 PASS다. 실제 원 first-signal만 native audit_profit_exit_flow로 읽기 전용 재현해 policy_binding_gaps0을 확인했다. 전체 날짜 의미 완료나 경제성으로 확대하지 않는다. [원 신호 native 재현](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/holding-policy-gap-49300-native-scoped-rehearsal.json).

holding generation39d0f10c…와 다른 세 capability 및 optional code hash는 동일하다. native-v6/원 보고서/code pin을 바꾸지 않는다. 최종 회귀·compile/diff/parser 뒤 새 immutable 통합본을 배포하며 정규 holding 보고서와 후속 detector에서 실제 policy_binding_gap 해소를 확인한다. 과거 first-crossing 세 원천 공백·비용 미상은 그대로 기존 owner에 남긴다.

legacy 보완 최종9 suites **3182 PASS/16.73초**, Python compile·diff·print-only parser PASS다. 원 첫 신호 native scoped audit도 policy binding0결손을 재현했다. 실제 일일 보고서·현재 PID 후속 수용은 다음 배포 영수증을 따른다.


## 다른 세션의 수동 제외·재기동과 closed-consumption 복구

사용자가 다른 세션에서 수동관리종목 제외와 봇 재기동을 했다고 확인했다. Main2984178은09:09 전후 사라졌고,09:14:05 기존3c의 별도 기동은09:14:54 bootstrap 단계에서 실패했다. 이 동시 작업을75d driver 중단의 결과로 단정하지 않는다. 기존 source/manifest/env/PREOPEN·준비본 해시는 그대로였다. 최신 수동 제외 파일의456010/operator_manual_control 추가와 SHA9d169aed…를 private snapshot으로 보존하고 덮어쓰지 않았다.

bdd461fde 최초 일반 preflight는 원 PID 부재로 selector 전 차단됐다. 원 실패 로그를 보존했다. 이미 완료된3c transition·같은 PID/start_ticks/cwd의 봉인 consumption·75d의 원 live predecessor identity와 frozen 파일을 대조한 뒤 existing native previous-stopped 인계를 사용했다. 별도 private operational helper는 Main/원 supervisor/요청/hold 부재, 정확한 historical receipt와 native handoff verify 및 세 code gate를 확인하고, 실패 출력이 보존된 exact dead pane만 정리한다. 새 owned hold/selector와 native prepare/bootstrap/auxiliary/launcher/독립 PID attestation은 기존 Deployment를 사용한다. 과거 PID를 현재 alive로 합성하지 않으며 원 중단/실패 attempt는 남긴다. helper의 dead-pane capture target 형식 실패는 공유 상태 변경 전이었고 해당 로그도 보존했다.

복구는09:23:32 PASS, 실제 Main3016558/start_ticks17406712,09:23:48 정책 reader/보유 복원/정상 loop 확인이다. optional code/calendar true·17개 역사 SHA 불변·앞선 세 원 SELL journal 부재·현재456010 포함 수동 제외 bytes 불변을 확인했다. 원 익절 비용/source gap은 보존한다.

## 036930 SOR terminal ACK와 상시감시4개의 공통 원인

사용자가09:24:31/32 036930의 key15519689…를 추가했고 상시감시4개 이유를 요청했다.09:23:48 실제 SELL은 record49294/order0015649/execution30414/qty1/remaining0이다. 원 journal을 보존했다. 같은 BUY/TP bundle/signal·제출 custody·qty/unit·broker final reconciliation은 유효하지만 SOR 실제 거래소가 official_exchange_fields_ambiguous_or_missing/UNKNOWN이라 broker_execution_provenance_complete=false다. 기존 traceless broker-position ACK가 이를 전부 거부했다. 실제 거래소를 KRX로 추정하거나 비용·출처를 complete로 바꾸지 않는다.

수리는 receipt custody만 대상으로 한다. 정확한 UNKNOWN/원 source label·SOR 요청/route·기존 normalized raw envelope/source-type·packet ingress clock 일치·session contract와 모든 기존 terminal/BUY/TP/custody/qty/final/잔량0 검증이 함께 맞을 때만 typed ACK를 허용한다. native_receipt_source_gap=actual_execution_venue_unresolved와 venue unknown/provenance false를 명시적으로 남긴다. 기존 entry-trace receipt도 불완전 venue의 custody ACK를 허용하므로 이 경계에 맞추되 scanner coverage/Main lifecycle/actual cost/order authority는 만들지 않는다. REST/WebSocket 요청·parser·FID 매핑은 수정하지 않았다.

원036930 leg의 읽기 전용 fake-append 리허설은 ACK 계약 PASS·원 bytes/hash 불변·journal/provider/order 쓰기0이다. 새19개 venue/route/envelope/clock/custody/qty/BUY/simulation/변조 회귀를 포함한 live-profit suite138 PASS를 확인했다. [원 leg 재현](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/sell-outbox-036930-offline-rehearsal.json). receipt exact successor49e76d6b…와 holding generation0c461429…의 기존 두 원 source-pair를 결속하고 새 isolated fixture를 요구한다.

고정 목록은005930/034020/403870/196170/036930의5개다. 실제3016558은 WATCHING4개였고 036930은 완료49294의 ACK가 미완료라 revive49342/WATCHING의 DB 생성 후 런타임 attach가 보류됐다. source DB readonly 대사로 나머지4개 WATCHING과49342를 확인했다.456010은 고정 목록이 아니며 수동 제외 때문에5→4가 된 것이 아니다. 원 ACK 수리 후 native revive/현재 PID의 실제5개 편입으로 닫는다. 상시감시 충돌 guard를 낮추거나 중복 watch를 생성하지 않는다. [DB 대사](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/fixed-watch-five-readonly-db.json).

036930 보완6 suites **2365 PASS/14.10초**, compile·diff·print-only parser PASS다. 기존3182 검증과 중복 합산하지 않는다. 새 generation fixture와 승인 배포/자연4-key ACK·5개 편입·최종 detector는 별도 후속 수용이다.


새 holding generation0c461429…의 native isolated fixture91 PASS/네트워크·주문0을 발행했고 네 family reader와 delay/stop/holding 세 code gate 및 optional calendar를 검증했다.8ddb 배포는 기존 full detector를 기다리다60초 native drain timeout으로 공유 상태 변경 전 차단됐다. 원 로그를 보존한다.

09:25 자연 보고서는 현재 PID3016558의 별도 tp_situation_policy_receipt_missing을 드러냈다. native PID archive는 manifest env의 situation_policy를 포함하지만 sentinel은 bare manifest receipt를 current PID에 먼저 넣어 동일 PID의 정상 augmented archive를 conflict로 제외했다. 기존 holding_exit_sentinel._profit_exit_bootstrap_binding에서 원 manifest/hash/verification/as-of 검증 뒤, 동일 env의 typed policy를 native PreparedTrailingPolicy.prepare로 검증하여 augmented copy로 비교한다. 원 manifest/receipt/archive는 바꾸지 않는다. 실제 다른 vector/변조/다른 날짜·미래/as-of/상충 PID는 계속 거부한다. 새5개 양·음성 회귀를 포함한6 suites2364 PASS와 실제 현재 PID+036930 original signal의 native scoped audit에서 policy/runtime binding gap0을 확인했다. [현재 PID 재현](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/current-typed-receipt-native-036930-rehearsal.json). source gap과비용 미상은 그대로다.

이 추가 sentinel 수리는 native-v6/네 family generation/optional hash를 바꾸지 않으며 방금 발행한0c461429 fixture를 그대로 검증한다. 최종 새 commit에서 정상 ordered 배포를 수행하고 실제 native036930 ACK·49342 runtime WATCHING 및 고정5개, 정규 의미 보고서·전체 detector를 수용한다.


## 기존 PID preflight 반복 읽기와120초 timeout 보완

01136801e의 첫 두 실행은 detector lock 대기로 상태 변경 전 중단됐다. 기존 full detector가 끝난09:39:58 새 native 시도가 preflight를 시작했으나 기존bdd의 H --verify가120초에 timeout됐다. phase preflight/selector 불변/Main3016558 계속 실행이며 원 status와 로그를 남긴다. 단계 마감시간을 늘리지 않는다.

기존 Deployment.run_json은 candidate에만 validation-session을 전달했다. 현재 predecessor도 같은 CLI/digest 기능을 갖고 있어 큰 immutable 원천을 호출 안/사이에서 반복 읽었다. 같은 automation 파일의 compatibility reader는 두 root의 digest 구현 전체 bytes와 해당 CLI 전체 AST가 같을 때만 predecessor에도 같은 session UUID를 전달한다. H의 검토된 overnight receipt source-pair 한 상수 값만 CLI 호환성 비교에서 분리하며 모든 검증 호출·parser·동작은 같아야 한다. 이 비교가 source-pair 수용이나 semantic PASS를 대신하지 않는다. legacy/다른 CLI 또는 cache 구현은 원 native full 경로를 유지한다.

각 code source는2MiB 이하 regular/no-follow로 읽고 descriptor/경로 전후 identity를 대조한다. 데이터 파일 stat·source set·기대 hash·날짜·정책·hard safety·native 의미 검사·120초 timeout은 그대로다. session의 기존 digest 저장소/TTL/무효화 규칙을 바꾸지 않는다. compatibility proof는 호출 옵션만 고르고 actual verdict는 각 native subprocess가 다시 만든다.

18개 compatibility/옵션·deadline 경계 회귀를 포함한6 suites2389 PASS, descriptor identity 보완 후 automation suite156 PASS와 현재bdd→후보의 실제 두 CLI compatibility true를 확인했다. [실제 코드 호환성](/home/ubuntu/KORStockScan/tmp/postclose-read-reduction-deploy-20261016-0740/predecessor-actual-cli-compatibility.json). 새 후보를 clean immutable release로 만들고 실제 preflight validation_io·원 deadline 내 통과·PID·ACK·고정5개·정규 detector로 확인한다. 예상 읽기 절감을 실제 측정으로 확대하지 않는다.
