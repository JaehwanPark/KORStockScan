# 10/19 PREOPEN 경고 수리와 실행 검증

원천일은 2026-10-16, 적용 대상은 2026-10-19다. 사용자는 경고 수리·재생성·재기동을 지시했다. 최초 선택은 `958d35b2b03f0a37462c1c0121fc14c108e709b8`이며 Main/supervisor 부재를 확인했다. 기존 원 정책, 수동/퇴역 custody, 수량·threshold·provider·hard safety는 유지한다. 원 05:41 실패와 10/18 P5/P6 PASS는 각 당시 증거로 보존한다.

## 재현과 수리 범위

- 05:35 finalization은 controller/summary를 갱신한 뒤 cleanup에서 실패했다. 일반 캐시 탐색이 보존된 배포 격리 `work` 디렉터리(mode 000)에 진입했다. 준비 재생성은 후행 단계라 실행되지 않았으며 native 검증은 `prepared_source_or_release_changed`였다.
- 캐시 탐색은 `.venv/.git/data/logs/tmp/docs`를 소유권 경계에서 제외한다. 증거 내부 캐시·권한·원천을 보존하고, 일반 코드 범위 읽기 실패는 계속 cleanup 실패로 처리한다. 부분 탐색 결과로 삭제하지 않는다. 운영 계약은 [로그 보관](../operational-log-retention.md)을 따른다.
- 후속 release의 동일 정책 코드 인계는 선택된 predecessor의 native 검증을 통과한 immutable 원 준비 증거를 이어받는다. `previous_handoff`는 현재 선택 commit/family의 정식 경로만 허용하며 원 정책·원 코드 digest·전체 source·날짜·clean candidate를 재검증한다. 바뀐 controller/summary 경로에 과거 원문을 복원하지 않는다. 선택 경합·원천 변조·다른 family/정책/준비 원본은 거부한다. 이는 정책 발행·PREOPEN·PID 권한이 아니다.
- trailing 경고는 보고서 code contract와958 실제 계약의 불일치다. 기존 producer의 completion prefix→fact→quantity→holding suffix를 통해 현재 코드의 새 세대를 생성한 뒤 summary/strict/controller/준비와 연결한다.
- 초기 수량 경고의 기존 완료 모수13건은 비용/수량 결손으로 제외됐다. 운영 research cost index가 없음을 확인했다. 기존 공식 저장 자료를 native producer로 연결하며 배분 연구 비용을 canonical 실제 비용으로 바꾸지 않는다. 복구 불가 부분은 null/제외를 유지한다.
- 실제 재생성에서 `quantity_pipeline_record_partition_required`를 추가 재현했다. 첫 대형 행은 `strategy_owner_replay_seed_observed`/`record_id=null`이며 수량 거래 범위 밖이다. 64KiB 상한은 유지하고 대형 행 전체의 최상위 식별자를 구조적으로 확인한 뒤 범위 밖만 배제·계수한다. 범위 안 대형 행은 해당 거래의 경로에 명시적 source gap을 남겨 counterfactual/timeout 선택에서 제외한다. 원 완료 비용의 parent 관측은 별도로 유지한다. 식별자 누락·중복 키·잘린 구조는 계속 전체 실패다. 다음 행을 잃지 않는 Unicode/후행 식별자와 식별된 거래만 제외하는 회귀를 포함했다. 정상 fact/비용 의미·원천 hash·세대 CAS는 유지한다.
- 승인된 동일 정책 배포가 자정을 넘길 때 machine 후보의 native stopped rebind는 있지만 보조 overlay publisher는 미래 날짜만 허용하던 인계 결손을 확인했다. 당일07:35 이전·native 동일 정책 code-refresh proof·완료된 원천 controller·source-code handoff·선택 릴리스·Main/supervisor 부재·PREOPEN/live bootstrap 미생성·기존 CAS를 모두 요구하는 동일 세션 준비를 추가했다. 128개 binding/승인2 PRE 변경/rollback/원 연구 입력은 그대로 검증하며 장중 재선정 권한이 아니다. 원 준비 코드 쌍과 원76개 의존성을 보존하고 새 정확한 source generation을 별도 검증한다.

## 검증과 진행

캐시 탐색의 증거 보호·권한 거부·partial census 회귀 및 cleanup/finalization 98개 통과. 후속 정책 코드 인계·장전 준비·intraday 인계 2,646개 회귀가 통과했다. 추가 수량/당일 인계 보완 후 관련7모듈 최종2,967개와 원/발행/현재3세대 코드 변조 회귀3개가 통과했다. 이 수치는 중복이 있어 합산하지 않는다. 성공과 선택 경합·변조·다른 원본·07:35 이후·실행 PID·미완료 controller 거부를 검증했으며 Python compile, shell syntax, diff, print-only 문서 parser도 수행한다. 자기 리뷰→보완→재리뷰에서 이 변경 범위 미해결 지적0이다. 최종 native generation과 실제 배포/PID는 별도 검증한다.

기존12개 준비/정책/선택/보고서 및 원 snapshot11개 2,457,982,550bytes는 [작업 증거](../../tmp/preopen-alert-repair-20261019/)에 보존했다. 재생성·배포·실제 PID·자연 신호/비용 성과는 아직 완료로 표시하지 않는다. 기존 `DirectFamilyPreopenPolicyHandoff`, `OperationalLogRetentionRepair1016`, `InitialQuantityProducerConsumerRepair1010`, `HoldingProfitExitSourceContractRepair`의 Acceptance를 유지한다.

## 10/19 원천 재생성과 정지 상태 전환

native completion prefix와 holding suffix가 각각06:48:59,06:57:17 완료됐다. stop stage는07:06:25 완료됐고 새 정책 `e6d31662f21d7785c3ddcc7e5e361482e3d7e03486216403f3491542f3238f7b`의9개 cell이 모두 baseline carry이며 수치는 원 정책과 같다. trailing은 새 generation `4ffbfa609639acf02268343fdc8176971cd3c1f8024100731403fcfbcbea8821`이다.

수량 native CLI는 성공했으며 stage generation `714a841f0f5570c1e56470f510928e21e4adfb4c5d9380b8ecdd36b865c11cce`는 carry_parent다. 완료13건 중 연구 배분 비용이 검증된8건을 평가했고 연구 비용 무효1건·terminal 비용/수량 결손4건은 제외했다. 실제 실행 비용 완전성은 false이고 실제 완료 net PnL은 null이다. 8건의 counterfactual 경로는 식별된 대형 행 결손으로 제외했다. 역사적 holding first-crossing5건은 복구됐다고 주장하지 않는다.

선택958 검증기는 새 원천을 재평가할 때 원 대형 행 오류를 재현했고, 후보894의 수량 검증은 통과했으나 holding 인계에서 차단됐다. 실패 시도를 보존했다. Main/supervisor·당일 PREOPEN·live bootstrap 부재 아래 실제 정책 인계, delay/holding 코드 차이, stop native committed reader, native 신호128scope/76,800행/598hit 일치와 검토 영수증을 검증한 뒤894를 정지 상태로 선택했다. 이 선택은 P5 성공이나 기동 수용이 아니며 새 source/controller/prepared와 격리 로더·PREOPEN·PID 검증을 후행 필수로 유지한다.

holding 실패는 선택을 맞춘 뒤에도 남았고, 새 observation SHA와 원 정책의 고정 source SHA 불일치로 확정했다. 기존 정책은 별도 원문으로 보존했다. 사용자 승인 범위의 명시적 재생성에서 native `create_bundle`/`validate_bundle`/`load_bundle`과 기존 summary stage lock·release lock·원천/정책 CAS를 사용했다. 새 bundle `22c4fe91c865e5e95212e9ce35eb6449594136fcf1ebe80fa2a2e43b14049eac`의12개 cell, policy set `ce7c4677ee9f930cfdb9f5ad0f17b585a9c65593e4b3ba47f0db019e57feabcc`와 incumbent carry는 원 정책과 동일하다. 과거 연구를 현재 실행 성과로 재분류하지 않는다.

첫 선택 시도는 journal owner 진입만으로 변경된 current cursor를 active-policy source가 감지해 중단됐다. selector는 바뀌지 않았고 entries/written은0이었다. 원 빈 transaction과 실패 로그를 보존하고, native release-set/selector lock 및 CAS 아래 정확한 원 verified transaction bytes로 cursor만 복원했다. 두 번째 선택은 같은 native locks와 atomic CAS를 사용했다. [선택 영수증](../../tmp/preopen-alert-repair-20261019/selection-publication.json)과 [빈 시도 복구 영수증](../../tmp/preopen-alert-repair-20261019/empty-transition-cursor-recovery.json)을 분리한다.

native summary stage 성공 후 전체 controller는 `done`, blockers0을 기록했다. 이어 native stopped rebind로 Main 후보 `281990305206840ad58d38944b87d9237b261d6eb5d012222517a236054975c8`를 생성했다. 보조 reader는 원 후보의 원 source와 새 후보의 새 source를 각각 검증하고 원128개 binding 일치를 확인했다. 새 정책 source를 반영한 controller 재검증과 최초 prepared도 통과했다. 07:34 native 보조 publisher가 overlay `5b3164ff2b19811895493da402bd832809f5afb01692b1c34aa4a5408c4b1c03`를 게시했으며128개 binding·승인2 PRE 변경·rollback 및 registry 정의가 원본과 같다. [게시 영수증](../../tmp/preopen-alert-repair-20261019/auxiliary-rebind/publication.json). 이것은 실제 PID 소비가 아니다. 07:34:38부터 정식 finalization 복구를 실행해 cleanup과 최종 detector terminal을 확인한다.

## 현재성 관측 분리와 마지막 검사 복구

`postclose_finalization --recover-closed-target --resume-final-detector`는 최종 detector만 실패한 가장 최근 native 시도에서 원 controller/strict/snapshot/cleanup 세대·실제 완료 시각·선택 release를 검증한다. 원 로그와 실패 보고서는 immutable receipt 폴더에 보존한다. cleanup 또는 policy/PREOPEN을 다시 발행하지 않으며 새 full detector와 동일 세대 검증이 통과해야 wrapper가 정식 DONE을 남긴다. 51개 회귀 및 compile/shell/diff/parser가 통과했다. 07:42:33 실제 cleanup 완료, 07:53:46 finalization/최종 detector DONE을 분리한다.

10/19 PREOPEN은07:50:46 완료됐고 Main PID274478의 선택894 소비는07:55:50 launcher 영수증으로 확인했다. 기동 observer는 기준일10/16 raw inode 교체를 발견하여 원 요약 cursor를 재사용하지 않았다. 원 요약/manifest를 보관한 정식 allow-bootstrap 재생성을 통해 현재 원천을 다시 읽고 검증한다. 과거 raw를 수정하거나 cursor만 옮기지 않는다.

all-scope trailing 원 보고서는 수량 수리 전 코드 계약84746d였고 현재894 계약은ddca6b다. 원 holding을 다시 쓰면 이미 확정된 PREOPEN·holding 정책 SHA를 깨뜨리므로 monitoring 소유 `main_trailing_currentness.py`에서 별도 native 전체 원천·partition·산술 재검증을 발행한다. health는 원 holding/report 세대, 동일 source/target/scope 및 parent policy, 현재 코드와 새 native report 결속만 관측한다. 원 계약 실패를 original_findings로 남기고 새 검증의 근거를 분리한다. 이 영수증은 bootstrap/정책 소비자에게 허용되지 않으며 원 source gap·비용 null·거래 성과 상태를 변경하지 않는다. module은 engine root 대신 monitoring 패키지에 두고 exact generation 변조/날짜/원천/권한/정책/scope 거부와 native producer failure를 회귀 검증한다.

## 08:12 이후 부분 매도·관측·연구 원천 후속

- 두산에너빌리티49344·알테오젠49346은 사용자의 명시적 답변에 따라 `manual_operator`로 등록했다. 08:09:52 process_health PASS를 확인했다. 자동 손실 인계 원문과 실패한 첫 marker 기록도 보존했다.
- 큐리옥스49362의 원 주문0002471은 3주 중1주 체결, 잔여2주다. 부분 체결 successor를 저장하면서 pre-call 문맥/저널을 지워 취소 의도 저장이 막혔다. 부분 체결 동안 원 문맥과 동일 주문 증명을 보존하고, 재기동 시 기존 receipt journal에서 복원한다. 취소 경로는 정확한 원 주문·세대·해시 증명을 요구하며 신규 제출 검증은 그대로 유지한다. 완전 체결/DB 완료 후 원 세대를 정리한다. 기존49362 복구는 원 제출 이벤트·체결 이벤트·검증된 owner registry·DB·원 receipt의 일치를 먼저 확인하고, 승인된 ordered drain 이후에만 native journal writer로 수행한다. 취소 ACK/terminal을 만들지 않는다.
- 공식 Kiwoom HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 현재 조회했다. `kiwoom_docs`는 없으며 specs/core client/realtime decoder, packaged `kt10003`/`kt00007`/`ka10075`/`00`, PRD/MOCK Postman을 대조했다. 요청·parser·route·수량 계약 변경은 없다. 조회 시각/파일 해시는 `tmp/preopen-alert-repair-20261019/sell-partial-official-reference.json`에 보존했다.
- 동기 analyze_target의 async ID 부재를 오판한 provider lineage 검증을 수정했다. 동기 경로는 원 request ID, machine observation, native PID/start ticks, request/input/prompt 해시를 모두 결속한다. 비동기 결속 및 서로 다른 호출 혼합 거부는 유지한다. 관련857개 테스트 PASS.
- 분할매수 report/policy 원본을 유지한 native projection 재검증이 PASS했다. 이전 verification pointer를 별도 보존했다. 세대 `0a27e98626486dc68733fa94848e4e61b055ff1be1b5ec506a720e9121ce63ba`.
- trailing 재생성358081ec…는 오늘 owner registry append와 입력이 아닌 vote lock 파일 증가로 마지막 inventory 검증이 실패했다. 실패 산출물을 보존한다. 원 prefix SHA와 전체 registry hash chain을 검증하고, source date 이후이면서 과거 owner와 겹치지 않는 BUY/SELL append만 역사 연구에서 분리한다. 과거 owner·날짜 변경, 원문 변경, 잘못된 chain, 알 수 없는 날짜는 계속 실패한다. vote의 실제 jsonl/gzip은 유지하고 lock 파일은 입력에서 제외한다. 실제 policy/PREOPEN/holding snapshot을 재작성하지 않는다.
- 부분 매도/연구 통합409개, 동기 관측857개 테스트 PASS. 전체 native trailing 재생성·새 후보 preflight·승인된 재기동·최종 PID/observer 검증은 이 기록 시점 진행 중이다. 수량 비용 결손과 holding first-crossing5건은 원천 OPEN이다.

추가 검토에서 registry의 빈 줄을 event 수로 세는 경계를 보완했다. 같은 날짜 append가 빈 줄 때문에 건너뛰어질 수 없도록 native parser와 같은 유효 행 수를 사용하며 회귀를 추가했다. 중간6a083ab4c 연구 실행은 SIGINT로 종료하고 부분 산출물을 보존했다. 새 동기 관측기 바이트는 기존 original/selected 두 출처와의 정확한 SHA pair만 인계 허용 목록에 추가했다. 넓은 경로 허용이나 검증 생략은 없다. 추가350개 테스트 PASS이며 최종 후보로 다시 사전검사한다.

최종 사전검사는 observer와 연구/부분 매도 수정의 의존 파일 등록 누락을 Main 종료 전에 차단했다. 과거 허용 목록은 유지하고, 검토한76개 의존성 전체 세대와 원 delay/stop/holding3개 계약의 확장 목록을 별도로 결속했다. 파일별 대체 해시를 섞지 않으며 원 코드와 선택894 코드에서 새 코드로의 정확한 쌍만 허용한다. 현재 세대 테스트의 변조 대상도 실제 소비하는 확장 목록에 맞춰 누락·잘못된 해시·다른 family 거부를 검증한다. 기존 실패 로그와 선택/PID는 보존한다.

de3e541d9의4개 native gate 및2,757개 회귀는 PASS였다. ordered preflight는 다른 세션이 현재 체크리스트에 추가한 `SubmissionMonitorSyncLineage1019` 때문에 원 strict SHA와 다름을 감지해 Main 종료 전에 실패했다. 원 strict SHA `cda2da608d4c11d9e09495b75bb18675a9a750aad2c1bb88f4b6007ab326e034`와 정확히 일치하는 기존 bytes 및 현재 편집본을 모두 보존했다. native `preserve_checklist`는 원 strict SHA가 일치하는 명시적 원문을 immutable 역사 snapshot으로 보존하고, 이후 현재 문서가 바뀌었을 때도 그 정확한 snapshot만 재사용한다. 현재 문서 교체·새 strict 발행·다른 owner 삭제는 없으며 잘못된 원문, snapshot 변조/symlink, 원 prepared hash 불일치를 거부한다. 이 변경은 native PID 증명이나 정책/원천 검사를 생략하지 않는다.

4acb4ade4 전환은08:47:28 원 Main/PID274478을 정상 종료한 뒤49362의 원 문맥을 native writer로 복원했다. 이어 selected 단계의 보조 정책 검증이 `auxiliary_source_handoff_target_generation_invalid`로 실패해 원 startup hold를 유지했다. 원 발행894의 receipt를 새 실행 root로 다시 만들던 reader 결함이다. 역사 proof는 원 실행 root/commit에서 모든 source와 baseline 경로를 재검증하고, 현재 reader의 각 의미 코드가 동일하거나 기존 검토된 정확한 쌍인지 별도로 검사하도록 수리했다. 원 manifest/128binding/승인2변경 및 정책은 재발행하지 않았다. 실제 원 보조 manifest `efe327d2…`의 full native 검증이 PASS했으며 과거/현재 원천 변조·다른 root/commit 거부를 포함한2,796개 회귀가 통과했다.

복구는 기존 `StoppedDeploymentRecovery`의 정확한 failed-selected/hold/native predecessor 증명을 사용한다. 복구 사전검사에도 active-policy 검사를 추가하고, 검증된 prepared delay 원천의 동결·정식 publisher 승계를 일반 ordered 배포와 동일하게 유지한다. 실패 선택본/hold/원 증거는 별도 보존하며 보류 파일을 임의 삭제하거나 원래 주문·정책을 다시 만들지 않는다.

08:56 native stopped recovery는 cbbea8d9d/PID349913(start ticks1228560)에서 complete였다. 첫 PID 관측은 기존 producer lock 아래 게시했으나 sentinel source가 아직 없어 semantic partial이며 full health로 보지 않는다.

08:56 후속 수량 불일치는 공존 원장이 부분 매도 잔량2를, DB가 종결 전 원수량3을 보존하면서 기존 동기화가 receipt 복원 전에 반환한 결함이다. 정확한 owner·주문·제출 문맥·내구 체결 영수증의 일치와 전체 symbol 수량 대사를 먼저 검증해 owner 잔량만 복원한다. 다른 소유자 수량, manual veto, 다른 cancel/allocation interlock은 해제하지 않는다. DB 원수량은 보존한다.

사용자가09:01:54 잔여2주를 직접 매도했다. `kt00007` 두 번의 동일 주문 이력과 완료된 `ka10075` 미체결0건에서 원 IOC0002471의1주/72,000원·잔량0과 영웅문S#0008606의2주/72,900원·잔량0을 검증했다. 격리 원장 사본에서 먼저 검증하고 native transition/manual-exit reconciliation을 이용해 원 Main custody를 보존한 채 잔량0을 기록했다. DB49362는 buy_qty3을 유지한 COMPLETED/가중매도가72,600원이며 비용 미확인 순수익률은 null이다. manual-exit execution attribution은 수동 관리 편입이 아니다. 일시 추가했던445680 manual_operator 항목은 사용자 정정에 따라 정확한 추가 행만 제거했다. 후속 사용자 지시로196170 manual_operator도 제거했고 현재 두 종목은 제외 파일에 없다.034020 기존 지정은 유지했다. 원 receipt·취소 실패 이력은 보존하며 원 종결에 취소 ACK를 만들어 넣지 않는다. 근거는 `tmp/preopen-alert-repair-20261019/sell49362-manual-exact-terminal-source.json`과 `sell49362-manual-exact-terminal-applied.json`이다.

trailing 재생성 b2afe3d3…은20,840scope complete다. 기존 snapshot과 정책·scope tree·source는 같고 native 관측시각 및 그 시각을 포함한 snapshot hash만 다르다. report-only currentness는 두 원천 manifest와 native scope 재구성·전체 tree·각 digest를 발행 시 검증하고, 시간 외 모든 scope 필드를 동일하게 유지할 때만 인정한다. 원 policy/PREOPEN/holding snapshot은 보존한다. 범위·universe·hash·시각 변조 거부 회귀를 추가했다. 이 후속 수정의 새 release/PID 적용은 별도 native transition 결과로 확인한다.

49362의 원장 수량0과 broker terminal은 확정됐지만 incumbent 메모리의 SELL_ORDERED가 DB 상태를 다시 저장하는 경합을 확인했다.84472b8cd 배포 사전검사만 중단했고 Main은 계속 실행했다. 종결 DB 상태는 동일 원 수량/가격/비용-null·원장0의 CAS를 재검증해 native drain 직후 확정한다. 원 부분 체결·pending 파일은 그때 별도 bytes로 보존한 뒤 기존 exact-generation 정리 함수로 제거한다. 재기동 후 완료된 cycle을 다시 pending으로 복원하지 않는다. 이 실행 순서 보완은 새 주문·취소와 수동 관리 편입을 하지 않는다. 회귀2,881개, 실제 active/delay/stop/holding4개 gate PASS이며 실패 시도는 보존한다.


최종 승인된 ordered 전환은795dacfbd3f547c2410632d5042cb8b8bb212223/PID404085(start ticks1340713)에서 pass/complete다.09:13:20 기존 PID349913을 정상 drain한 뒤49362 DB 종결을 CAS로 확정하고 원 부분 체결·pending 파일을 SHA 보관 후 native 정리했다. 신규 Main은09:14:20 기동했으며 알테오젠49346/1주의 startup/periodic 수량 대사도 정상이다. native custody 환경에서445680·196170의 operator_source는 비어 있고 exact-date 정책은 Main 관리를 허용한다. 두산034020 지정은 유지된다. 회귀2,881개 PASS, compile/diff/parser PASS이며 workspace의 다른 세션 변경은 보존했다. 근거: `tmp/preopen-alert-repair-20261019/ordered-partial-owner-scope-final.json`, `sell49362-completed-cycle-journal-cleanup.json`, `manual-exclusion-final-native-environment-read.json`.

원 trailing b2afe3d3…의 full currentness 재검증은 현재 inventory 변경으로 차단됐다. 바뀐 원천은 owner registry와 holding vote383b163c…의 두 파일이다. registry 원 prefix SHA·native hash chain은 보존됐고 후속2개 주문 event는19일의49362뿐이다. 다만 기존 prefix의 날짜 없는 TERMINAL_RECONCILIATION_RECORDED7개를 historical helper가 상속 해석하지 못하며, 공유 holding vote도 재생성 이후 변경됐다. 원 바이트를 되돌리거나 검증을 생략하지 않고 `DirectFamilyPreopenPolicyHandoff`/`HoldingProfitExitSourceContractRepair`의 후속 원천 검증으로 유지한다. 다음 단계는 native event ancestry와 닫힌 날짜의 vote prefix를 정확히 결속한 뒤 동일 정책·scope의 full 재검증이다. initial_quantity 실제 비용5건 결손과 holding first-crossing5건도 현재 경고/OPEN으로 유지하며 수익률0으로 대체하지 않는다.


09:16 새 PID observer run96b64b7333864fc095a92d5c546c9199은 completed/semantic partial이다. 현재 actor 수명으로 제한된 source 관측과 실제 deadline/source 진단을 보존했으며 이전 PID의 validated 보고서를 새 PID 완전 검증으로 재사용하지 않았다.09:17 full dry-run은 process_health/인증/stale-lock PASS, cron은 늦은 복구 warning, artifact는 resource contention으로 deferred, log scanner는 누적10건 오류로 fail, tmp budget warning이다. 따라서 전체 GREEN/오류0은 주장하지 않는다. 새 PID에 대한 보조정책 native consumed receipt도 확인했다. `final-health-795.json`/`final-runtime-custody-795.json`을 최종 근거로 사용한다.

사용자196170 수동 지정 해제 후09:15:08 기존 preset hard-stop 규칙이 손실-1.51%에서 `auto_hard_stop_handoff`를 새로 기록했다.09:18:52 native 판정에서445680은 차단 없음,196170은 operator_source 없음/auto_source=auto_hard_stop_handoff다. 사용자 수동 지정을 다시 추가하지 않았고 새 hard-stop 가드도 임의 해제하지 않았다.49362는09:18:52에도 COMPLETED/원장0/원수량3/가중매도가72,600/순수익률null이며 원 pending 파일은 없다. 알테오젠의 신규 안전 인계와 실제 source/비용 경고는 별도 잔여 사항이다.


### 09:30 제출병목 ERROR 판정 수리

현재 PID404085의 관측기는 완료된 부분 관측을 게시했지만08:33:08 이전 PID274478/start867428의 스캐너 평가 aims-a094aebe8560a91a2d90에서 파생한 source/economic 사건2개를 현재 장애로 계산했다. 원본 machine observation17bc8252…의 전체 내용 해시, promotion·attempt·symbol·venue·session·bundle6필드, PID/start, 현재 PID 출생 이전 시각을 모두 재검증할 때만 현재 health의 장애 집계에서 분리한다. 원 incident active·원 실패 내용·비용 결손은 보존한다. 시간창 이탈만으로 복구시키지 않으며 원본을 bounded continuation에 보존하고 동일 신원 충돌은 영속 차단한다.

09:27/09:28의 entry_machine_input_deadline_expired2건은 exact async PID·attempt·정책과 snapshot≤원 deadline≤종결시각, DROP, provider 미호출·주문 미실행·금지 영수증이 모두 있는 pre-adjudication terminal이다. 이 조건만 latency guard miss 진단으로 분류한다. 안전조건 누락·변조·다른 오류는 계속 오류다. deadline/guard/정책/주문 실행 코드는 변경하지 않는다. 원천의 stale/no-match/route gap·CAUTION/VETO·timeout·미결 join은 계속 보고하며 complete/source-health PASS를 주장하지 않는다.

원09:30:25 보고서의 source/hash를 보관하고 native 원천으로 격리 재검증했을 때 warning_pending/bounded_source_quality_observation으로 판정됐다. 수량 정책의 native bounded chain은 유효하며 완료13건 중8건은 연구 배분 비용 표본,49013·49266·49268·49293은 terminal 비용/수량 결손,49294는 연구 비용 검증 결손이다. 실제 비용 완전성 false·실제 순손익null을 유지한다. 근거: tmp/preopen-alert-repair-20261019/scanner-incident-native-shadow.json 및 quantity-0925-native-observation.json. 배포/PID와 자연 detector 결과는 후속 영수증으로 확인한다.


09:43:02 승인된 ordered 전환은40b21f360cfd1652f9f26c4aff32c0921e68ba1f/PID470886/start1502213에서 pass/complete다. active/delay/stop/holding4개 native 사전검사,3,993개 회귀, compile/diff와 문서 parser가 통과했다.09:42:34 launcher의 실제 PID 소비와 원 bootstrap5c9cce5f… 보존을 확인했다.09:43/09:45 자연 observer는 현재 PID의 warning_pending이며 health projection이 소비자의 재계산과 일치한다.09:44:40/09:45:42 실제 full detector에서 submission_bottleneck_monitor의 artifact ERROR는 제거됐고 process_health/log_scanner PASS다. 과거 스캐너 incident2개 active와 원 결손은 그대로 보존했다. 최초 startup observer는 기존 producer lock 대기로 owner_busy였으나 같은 배포의 기존 producer/lock에서 현재 PID 보고서를 먼저 게시한 뒤 full sweep이 이를 검증했다. I/O wait39.65% 단발 FAIL은 다음09:45 sweep에서 해소됐으며 tmp 용량·initial_quantity 비용·trailing/source 정책 경고는 별도 잔여다. 근거: tmp/preopen-alert-repair-20261019/observer-history-final-verification.json 및 ordered-observer-history-final.json. 전체 경제성/원천 정상으로 해석하지 않는다.


## 10:01 I/O 경보와 수량 원천 후속 수리

10:01:20 full detector는 I/O wait46.32%, swap 사용8,329.9MiB를 관측했다. 선택40b21f360의 정기 intraday_light PID513723은09:55:18~10:04:23 실행했고 trade_review534.149초/최대RSS5,528,364KiB였다. 직전 실행도556.267초/5,742,652KiB였다. 알테오젠49346의10/16→10/19 완료 연결에서2.1GiB의10/16 원 snapshot을 전부 디코드한 뒤 historical open census 결손으로 폐기했다. /proc 관측상 해당 worker 누적실제읽기9,995,083,776bytes와 host swap/page-in을 확인했다. 당시 다른 정기작업 및 이 세션의09:52/09:56 원천 읽기도 중첩되었으므로46.32% 전체를 한 PID에 정량 귀속하지 않는다.

수리는 기존 log_archive_service 소유의256KiB 음성 사전검사다. 원 header가 이미 date/warning/historical-census 실패를 증명할 때만 같은 source_gap으로 조기 종료한다. 유효하거나 판독 불충분한 header는 기존 전체 row/ID 검증을 거친다. 실행하지 않을 stdin fallback snapshot의 선행 디코드도 제거했다. 이는 모든 유효 대형 snapshot의 읽기를 최적화했다는 주장이 아니다. 원본·기존 결손·거래소UNKNOWN·비용null을 보존한다. 실제당일입력 읽기 전용 리허설은1.778초/172,996KiB, 논리읽기319,843,970bytes/실제읽기54,190,080bytes, 기존49346 원천 결손 동일이다. 근거: tmp/preopen-alert-repair-20261019/io-native-rehearsal.json 및 원 worker attempt 로그.

수량5건 중49294의1,411개와49293의1,547개는 같은 native SELL 영수증 재관측이었다. 기존 검증기가UNKNOWN venue 및 native_entry 영수증 유형을 지원하지 않아 중복체결로 제외했다. 원 producer의 순수 custody identity 검증과 전체 payload/원 broker 시각 동일성으로 재검증하며, venue·실제 비용·실주문 권한은 승격하지 않는다. fresh allocator의 실패 결과는 성공 영수증 검증기에 넣어 원인을 덮지 않고 원 reason/dependency를 유지한다.49268/49293/49294의 격리 연구 비용 복원이 확인됐고 운영 report 갱신은 후속 검증 대상이다.49013의9/30 공식 일별비용980원은 주문 없는 조회로 별도증거경로에 확보했지만 Main custody 결속이 없으며,49266의 원 SELL execution_no는 비어 있다. 기존8건 중5건의 정책 영수증 결속도 partial이다. 비용 복원만으로 initial_quantity 경고 전체가 해소된다고 주장하지 않는다.

관련475개 및 정확한 의존성 세대 handoff2,503개 회귀 통과. 원 정책 digest와77개 의존성을 함께 보존하는 I/O 수정 세대를 검증했다. 추가 archive 검사159PASS/1FAIL 중 legacy gzip fixture1건은 선택40b21 원 코드에서도 동일 실패를 재현했으며 이번 변경의 회귀가 아니다. 원 archive identity/manifest 검증을 완화하지 않았다. 코드 리뷰→보완→재리뷰 후 이번 변경 범위 지적0이며 Python compile/diff/문서 parser 및 native active/delay/stop/holding 사전검사를 배포 전에 확인한다. live 적용·현재PID·정기 실행 수용은 별도 영수증으로 후행 기록한다.


10:21:07 I/O 수정 e5b3c5b8e ordered 전환은 PASS/complete, PID588224/start1734275는10:20:42 실제 소비를 확인했다.10:20 정기 intraday_light는 trade_review3.681초/308,300KiB, 전체9.341초로 완료됐다. 원09:55 작업의534.149초/5,528,364KiB와 비교했고 source gap은 보존했다.10:22 full detector의 process_health/log_scanner는PASS, I/O wait9.88%였으나 artifact 검사는 자원 경합으로 deferred였다. 근거: tmp/preopen-alert-repair-20261019/io-natural-cron-completion.json, ordered-io-final.json, io-final-health.json.

## 10:22 기동 관측기의 정상 보고서 덮어쓰기

수동 배포 후 native producer/lock 갱신 f51c8910…은 현재 PID full 관측을 게시했다. 같은 lock을 기다린 Main 기동 작업은 원150초 예산에서 producer 몫이 남지 않아 subprocess를 시작하지 않았는데75를 실제 실패로 해석했다.10:21:51 source_only3afdc4a4…가 빈 입력·필수 semantic 부재인 결과를 게시해 full 결과를 덮었고10:22:49 경보가 이를 탐지했다. 경보가 참조한 원 보고서와 기동 로그는 보존했다. 코드의 원인이며 정상 원천으로 재분류할 사안이 아니다.

run의 미실행을None으로 구분해 producer가 시작되지 않았으면 deadline 실패/미게시로 반환한다. 실제 실행한 producer의0/1/75 경로와 source-only 실패 진단은 유지하고, 원150초·주문·정책·수동보유 가드는 바꾸지 않는다. retained 보고서의 현재PID·원천·semantic 여부는 기존 첫 detector가 검증한다.20개 scheduler 회귀는 미실행 시 기존 보고서 보존과 실제 실패 시 진단 게시를 확인했다.10:25:22 현재PID native 보고서를 복구한9f1b4fa4…는full/warning_pending, unmet_conditions0이다. 코드 배포/다음PID 수용은 별도 후속 영수증으로 기록한다.


최종 수용:820b422dfe6daa896ec075f79bea0714c81465c9의 active/delay/stop/holding4개 native 검사와20개 scheduler 회귀, compile/diff/parser를 통과하고 ordered 전환을 완료했다.10:30:27 PID625590/start1793131의 실제 정책 소비와 bootstrap5c9cce5f… 보존을 확인했다. 기동 lock 대기가 다시 발생했지만 미실행 producer는 deadline 실패/producer_started=false/publication_attempted=false로 반환했고 현재 full0e77cd99… 보고서를 덮지 않았다.10:32:26 첫 자연 full detector는 artifact WARNING, process_health PASS이며 submission_bottleneck_monitor 오류가 없다. observer는 warning_pending/unmet0이고 스캐너 표본·원천 완전성은 미수용이다. I/O wait6.12%, available4,852.9MiB다. 원 수량·trailing·정책 검증·late cron·tmp 경고와 API_ERROR1개 log warning은 별도 잔여이며 전체GREEN을 주장하지 않는다. 근거: tmp/preopen-alert-repair-20261019/startup-observer-final-verification.json, startup-observer-final-native-health.json, startup-observer-final-native-observation.json.


## 10:50 원천 계약 경보 후속 수리

사용자 재지시 범위는 원천 계약 수리·정식 재생성·기존 정책을 보존하는 승인된 배포/재기동이다. 수량 연구가 64KiB 초과 실행 행을 통째로 버려 49340/49343/49345/49347/49351의 정책 결속을 잃는 것을 확인했다. 실행 소비 필드만 bounded projection으로 보존하고 필요한 필드 자체가 크거나 식별 불가하면 원 결손을 유지한다. 이월 보고서의 native manifest/원문 SHA를 모두 검증한 후 필요한 체결 timeline만 복원하며 전체 JSON 디코드를 피한다. 2026-10-15 원문 2,024,840,392B의 SHA c3a479611331319c335cf54b7b95913087fd7214d4f5b3def57bc30ae07c0864, 4개 보유 기록을 20.982초에 검증했다. 청크 중간 들여쓰기의 가짜 root 판독도 회귀로 차단했다.

과거 원장 prefix는 native state fold로 날짜 없는 terminal reconciliation을 원 intent에 연결한다. 이미 봉인된 retired manual disposition은 보존하고, 이후 과거 owner/date 변경·신규 전역 disposition·알 수 없는 intent·증명 불일치는 거부한다. 관련 원천/현재성 431개, handoff/배포/검출기 3,132개 회귀가 통과했다. 새 코드 네 파일은 기존 전체 의존 세대의 정확한 후속으로 함께 고정하며 원 정책 해시를 바꾸지 않는다. 정식 재생성과 새 PID/검출기 수용은 아직 검증 중이다. 실제 비용 null과 원래 custody/체결 결손을 비용 0이나 가짜 완료로 바꾸지 않는다. 근거: tmp/artifact-source-repair-20261019-1050/.

재기동 실패 원인: 원본 보존용 hard link 생성이 내용·inode·mtime을 유지하면서 ctime을 변경해 정지손절 원천 검증에 실패했다. 최초 사전 검증 이후 발생한 보존 작업이므로 그 검증은 실제 기동을 보장하지 못했다. 실패한 99e158af1 전환/시작 보류를 보존했다. 후속 native reader는 monitor snapshot의 ctime만 달라진 경우 전체 원문 SHA/size를 원 봉인 세대와 다시 대조하고 안정된 현재 stat으로만 검증 context를 구성한다. 내용·mtime·inode·경로 변경은 계속 차단한다. 원 정책/PREOPEN/bootstrap/strict/controller 바이트는 수정하지 않는다.

5d6ee3354 복구 전환은 Main PID785358/start2145429의 실제 소비와 complete/PASS를 확인했다. 원 bootstrap SHA는 5c9cce5fd3a2edf5045cc38536ded48addca84b78d1c8412a779a010954ef470로 유지됐다. 같은 ctime 차이를 만난 과거 fact/holding/quantity source reader는 봉인된 source SHA 또는 native 원 manifest 전체 SHA로 원문을 재검증한다. 정상 보관·gzip 경로의 bounded 읽기는 유지한다. 실제09/30·10/15·10/16 fact와 holding 세 날짜 모두 원문 보존 상태에서 검증됐으며 관련484회귀가 통과했다. 활성 stop 정책이 봉인한 과거 snapshot/cost index는 덮어쓰지 않는다. 수량 refresh 자체와 trailing 현재성 연구만 별도 새 세대로 생성하며 비용 원천 복원과 정책 소스 교체는 구분한다.

정식 수량 refresh 27dc2f14...는 원문/비용 index를 유지한 채 완료8건·125초·peak RSS162384KiB·swap0으로 생성됐다. 5개 큰 실행 행 중 49340/49343 정책 결속이 복원됐고 1주3건은 broker 초 단위 체결시각과 그 초의 microsecond 결정 비교로 남아 있었다. 해당 경우 exact plan/attempt의 유일 요청→전송→원 주문 전체 체결·수신 bracket이 있어야만 결정 선행을 증명한다. 원 체결시각은 변경하지 않으며 증명 누락/충돌/다른 주문/다음 초/부분체결은 계속 제외한다. 관련298회귀가 통과했다. 원문 보존 후 trailing의 대용량 소비자에 남은 직접 identity 비교도 native 원문 검증으로 연결한다.

## Trailing 재생성의 대용량 반복 읽기

12:07:09 ac4aa4417/PID910016/start2377635의 정책 소비와12:08:47 ordered 전환 완료를 확인했다. 정식 quantity refresh58c2c41a…/stage5a345fcc…는8개 비용 적격 표본의 정책 결속8/8, carry_parent,107초/최대RSS158556KiB/swap0이다. `initial_quantity_stage_invalid:ValueError`는 없어졌고 실제 비용/수량/terminal 결손5건의 경고는 유지한다. 원 bootstrap5c9cce5f…와 holding e665c46b…는 그대로다.

이후 trailing 전체 재조립26f37c07…는 약6분 동안 수십GB를 읽은 뒤 당일 holding vote append 때문에 `all_scope_assembly_inventory_changed`로 실패했다.12:10:45 I/O wait40.98%를 다시 관측했고 해당 전체 재시도는 중단했다. 미래100–200GB 원천에도 이 방식을 반복하는 것은 허용 가능한 설계가 아니다. 실패 산출물과 원 보고서/정책은 보존했다.

수리는 이미 승인된4ffbfa60…의39MiB 정규화 입력만 별도 세대로 복사하고, 원 추출 코드·모든 필드·원 결손을 보존하며 현재 native replay와 독립 산술을 수행한다. 대용량 원천은 원 full-SHA와 동일 byte epoch에 결속된 native stop/market-weakness/보존 재검증 영수증으로 확인한다. 이는 semantic verdict 캐시가 아니다. 증명이 없거나 바뀐 큰 파일은 전체 읽기로 fallback하지 않고 pending으로 실패한다. 미증명 원천 합계32MiB, 별도 vote 파일 합계32MiB, invocation 전체 hash 읽기32MiB를 먼저 제한한다. 총 프로세스 읽기에는 정규화 트리·원장 검증·코드/metadata가 추가되므로 총I/O32MiB라고 주장하지 않는다.

원 historical byte prefix·native 원장 체인을 보존하면서 원 연구의 실제 참조 owner를 고정한다. 19일의49344/49346 이월 청산처럼16일 완료 연구에 없는 owner의 새 주문은 과거 입력을 무효화하지 않는다. 원 연구 owner 변경·과거 날짜의 추가/변조·새 전역 disposition·잘못된 dateless terminal proof는 계속 거부한다. future vote도 native 세션/요청시각/position 결속이 유효할 때만 과거 inventory에서 분리한다. 원 custody·실주문·정책·보유는 변경하지 않는다.

실제 native 사전검사는6.395초, full-hash17,139,911B, 논리 rchar169,488,726B, 실제 disk read2,187,264B, peakRSS154612KiB였다. 대용량 proof42개를 두 검사에서 재확인했고 원 source-window hash48b3bea8…가 일치했다. 준비/검증은 native 전체 산술 완료, 배포, 현재PID 수용과 다르다. 근거: tmp/artifact-source-repair-20261019-1050/reuse-native-preflight.json 및 reuse-window-probe.log.

후속 사용자 지시에 따라 미래 원천 writer→색인→consumer까지 구현했다. AI payload/trace/prompt/request, pipeline raw와 보유 vote는 기존 append lease 안에서 원 offset/size/SHA·projection SHA·native hash chain을 기록한다. 완료 snapshot은 쓰는 바이트를 해시하고 resident completed 행을 immutable normalized tree와 census/cost/원 snapshot 결속 manifest로 발행한다. Trailing 조립·원 요청 검증·날짜/보유별 vote·압축 뒤 논리 소비와 delay 원천 관측기는 이를 직접 읽는다. 미증명 대형 legacy/gzip은 원본 전체 읽기로 fallback하지 않고 pending이며 explicit migration은최대8MiB/기본1초의 재개 가능한 단계다. 현재 일자 background catch-up은0.5초 turn/회전 namespace, checkpoint는 최대 분당1회다. Native append 경합은 resident 원 바이트의16MiB/128건 제한 재시도로 처리하고, 경합·누락·변조·원천 결손을 complete로 바꾸지 않는다.

호가 관측은 기존0D local cache만 읽는50ms sampler로0·1·3·5초 horizon을 Main 방문 주기에서 분리했다. 원 route/epoch·0.7초 신선도·0.25초 short tolerance와 실제 관측시각을 유지하며 provider/구독/주문을 추가하지 않는다. PASS 후 최종 auxiliary 검증은 현재 정책 불변 뷰를 사용하고 pointer 출구 검사·최신 revocation·원5초 경계는 계속 실행한다. 같은 live bundle의 읽기 전용 warm 중앙값은 기존 복사31.4ms→불변 뷰7.3ms다. 이는 해당 로딩 구간 측정이며 실제 broker 제출/순익 개선 증명이 아니다.

재리뷰에서 기존 pipeline archive 영수증 발행 조건 축소, 날짜 없는 legacy vote consumer, native vote source-generation 비교와 completed cohort 밖 원장 혼입을 수정했다. 대형 raw 재열기 금지·200GiB sparse 입력·회전/압축·future event·native busy 재시도·기존 deadline/안전 가드를 회귀로 확인한다. 최종 exact94-file handoff·색인·writer 검사2521개 PASS, 구현/consumer/회귀 결과와 새 후보·native 생성·PID 수용은 아래 후속 영수증으로 구분한다. 근거: tmp/artifact-source-repair-20261019-1050/index-handoff-regression.log, index-native-final-edges.log, index-review-second-pass.log, index-archive-final-fix.log, policy-view-latency-probe.json.

최종 검증: index-consumer-final-review의1062 PASS 뒤 archive 회귀6건의 원인(기존 pipeline 파일명 계약 축소)을 고쳐53 PASS, writer parent 회귀는 Main 사전 준비를 포함해17 PASS, 최종 handoff/index/fork/busy writer2521 PASS다. 추가 계약 검사는530 PASS/2 FAIL/1 deselected였으며 새 parent 준비 회귀는 수정·재검증했다. 잔여 pipeline `test_restart_drain_keeps_late_scanner_rows_bound_to_first_stage`는 원 ac4 baseline에서도 같은 family ledger 분류 차이로 실패하는 기존 항목이다. legacy gzip fixture1건도 기존 baseline 실패로 제외했다. 이 두 기존 실패를 PASS로 바꾸거나 최신 결과에 합산하지 않는다.36개 변경/신규 Python compile·diff·print-only parser23 owner PASS. 테스트 결과는 중복이 있어 합산하지 않는다.

정식 trailing 재생성은38.106초/20,840scope complete, 원 추출 provenance 보존·현재 전체 산술 검증·semantic verdict 재사용false로 완료됐다. full hash18,824,751B, normalized/검증 포함 rchar535,686,246B/disk126,214,144B/최대RSS182776KiB다. report adfcad8b… 및 currentness7884f735…를 발행했으며 원 정책/holding/PREOPEN은 미변경이다. 최초4c7a71245 후보 preflight는 이전 ac4 Git 세대에 없는 새 selector를 요구하여 Main drain 전에 거부됐다. 후보가 Git에서 소유하는 selector 삭제는 계속 거부하고, 원 Git에도 없는 이전 세대만 historical closure로 검증하도록 고친 뒤2505 PASS다. 실패 로그와 후보를 보존했다. 근거: tmp/artifact-source-repair-20261019-1050/index-trailing-native-generation.log, index-native-preflight.log, index-predecessor-fix-tests.log.

최종 제출 경계 최적화는 frozen auxiliary reader5개를 바꾸지 않도록 `reversal_evaluation_context.validate_submit` 및 두 native 호출부로 이동했다. 원 reader/등록 바인딩/next-session manifest bytes를 유지하고 최신 revocation·5초·독립 전송 guard를 재실행한다. 이전 fa751d3c5용 reader 호환 초안은 미선택 후보의 증거로 보존하며 기존 overlay/manifest를 재발행하지 않는다. 최종 source/handoff/reuse 검사2531 PASS, submit/auxiliary 계약192 PASS다. 별도 auxiliary readiness mock2건은 ac4에서도 같은 missing current-pointer 예외로 실패하여 baseline 증거로 구분한다. 실제 candidate readiness는 정식 현재 pointer와 기존 source/reader 호환 영수증으로 다시 검증한다.
