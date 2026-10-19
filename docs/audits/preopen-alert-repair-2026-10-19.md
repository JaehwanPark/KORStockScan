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
