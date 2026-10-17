# 10/15 장전 최종화·정책 생성 검증 경보 수리

05:51:38 경보의 source는2026-10-14, target은2026-10-15다. 당시 선택본은 `e74ec5c56`이며 Main은 정지 상태였다. 이 기록은 코드 검증·실제 준비 복구·후속 배포와 예약 기동을 구분한다.

## 원인과 수리

- 최종화는05:43:41에 새 controller를 발행했으나 준비 단계에서 실패했고, 고정120초 예산 소진이 원인으로 판단된다. cleanup 종료→실패는120.315초이며 [원 직접 준비](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-prepare-20261015T015055-dff2e330/receipt.json) 성공은178.140초였다. wrapper가 원 exit code를 버렸으므로 과거 exit124가 직접 기록됐다고 주장하지 않는다. [원인 대사](../../tmp/sentinel-integrated-postclose-20261014/prepared-contract-alert-055138-readonly-diagnosis.json)를 보존한다.
- 예약 wrapper는 기존 작업본의 미배포 수정에서 양의 정수 `POSTCLOSE_FINALIZATION_PREPARE_TIMEOUT_SEC` 기본600초를 가져오고, 기존06:50 마감에 따른 budget cap·kill grace10초·실패 detector·wrapper exit1을 유지한다. 이제 실제 준비 자식의 exit code도 로그에 남긴다. 이는 준비 검증 시간이며 AI 신호5초·보고서130/40/180초 예산 변경이 아니다.
- 보조 평가의 코드 세대는 선택본과 일치했지만 해당 세대의 fixture 검증 영수증이 없어 `policy_generation_unverified`는 정당했다. 별도의 현재 운영 정책이 verified라는 이유로 checklist 생성기가 capability warning을 누락한 것이 `UNRESOLVED_CURRENT_OWNER`의 원인이다. [정확 경보·원천](../../tmp/sentinel-integrated-postclose-20261014/auxiliary-generation-alert-20261015T055138-review.json)을 보존한다.
- checklist owner는 기존 capability OWNERS와 source/code/contract 세대에서 직접 투영한다. 경제성 repair와 같은 ID이면 증거를 합치고, 기존 PREOPEN 작업·manual OPEN·이력·권한을 유지한다. 이번 자동 경고의 provenance marker만 조건부 갱신에 사용하며 verified 전환에서 낡은 자동 경고를 제거한다.

## 검증과 실제 실행 경계

wrapper25개와 checklist84개 표적 시험이 PASS했고, 독립 리뷰의 미해결 지적은0이다. compile·bash 문법·diff 검사도 PASS다. [wrapper 검증](../../tmp/sentinel-integrated-postclose-20261014/finalization-wrapper-600s-source-validation-20261015.json), [checklist 독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/checklist-generation-independent-review-20261015.json)에 코드 해시를 결속한다.

실제 e74 정상 prepare를600초 외부 한도로 실행해06:45:52에178.616초/exit0으로 복구했다. 현재 정책·후보·selector·controller·summary·checklist·원 준비·평가 bytes는 그대로이고 새 c737 controller 세대의 준비 영수증을 발행했다. [실제 실행](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/prepare-execution.json)의 새로운 readiness SHA는 `1cf11dd039ae493ba4bd19e228592cefd98df3cc14ce3a4e56a3f989e6ccada0`다. 별도 full verify도06:48:21에 `current_full_contract`/findings 없음으로 통과했다. 최종화 terminal은 별도로 확인한다. 원05:51 실패를 성공으로 덮어쓰지 않는다.

보조 검증 경보는 기존 표적 fixture 검증→native evaluate를 사용해 닫는다. 원50쌍·100요청·예산·응답·resolution 내용과 기존 immutable 평가·정책/C15를 보존하고 provider·정책 재선정은 실행하지 않는다. [기존 경로 리뷰](../../tmp/sentinel-integrated-postclose-20261014/auxiliary-generation-existing-native-closure-review.json)에 재실행 범위와 원천 대사를 기록한다. 실제 완료는 별도 영수증으로 확인하며 이후 필요한 summary/checklist/controller/prepared만 재결속한다.

새 코드의 배포·준비·정규07:35 PREOPEN/07:55 Main PID 소비는 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다. 현재 코드 검증을 배포 또는 기동 성공으로 표시하지 않는다. 원천 누락·미성숙 경제성은 null/원 상태로 보존한다.

## 실제 수정본 배포와 보조 검증 영수증

수정 commit은 `3d644d8495a2c257784d96cd01df831bfb6022f8`이다. 요청된 계산 수정 `a179bb42d`가 ancestor로 포함되어 있고, e74 대비 변경한 실행·시험 파일은 4개다. 정책 native 33개는 동일하다. [코드·109개 시험 결속](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/source-validation-109.json)과 독립 리뷰를 통과한 뒤, [실제 selector 발행](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/selector-publication.stdout.json)은 07:09:32에 PASS였다. 선택 SHA는 `75e74d193fbcb8bdbbeb624909ad258e8e1835772f02ce6b2899c84b268e925b`이며 정책 변경·Main 기동은 없었다.

해당 보조 코드 세대의 실제 fixture 시험 53개가 PASS했고, [실행 영수증](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/fixture-20261015T065554-4bba29dc/receipt.json)의 검증 파일 SHA는 `4f21d5a1c72ec78531fab27914d602ee011008bbfbd3ebbb16174e70080ea034`다. 기존 50쌍·100요청·예산 및 원 평가 bytes는 보존했다. 새 C15는 기존 immutable `evaluations/32a4…json`을 계속 참조하며, 갱신 가능한 `evaluation.json` 별칭과 fixture를 직접 참조하지 않는 것을 [별도 확인](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/new-c15-auxiliary-reference-review.json)했다.

이 시점의 선택·fixture 발행과 이후 후보 재결속·평가 갱신·최종화·정규 PID 소비의 완료 여부는 각각의 실제 영수증으로 구분한다.

## 새 투영 규칙에 따른 선행 종료 영수증 갱신

07:09 후보 재결속 첫 시도는 `stopped_postclose_rebind_whole_source_not_closed`로 중단됐고 원 후보 SHA `75a5d4c5…`는 그대로였다. [실제 full 진단](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/stage-failure-current-closure-issues.json)은 새 checklist 코드가 기대하는 owner의 projection/schedule 불일치 두 건뿐이었다. 기존 e74 코드로 배포 전 종료 계약을 검증한 것만으로는 새 코드의 checklist 규칙 적용까지 증명하지 못했다. [독립 원인 대사](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/stage-failure-causal-readonly-review.json)에 원 controller/strict/summary/checklist와 정책 후보를 보존한다.

기존 summary stage의 입력과 독립 producer가 그대로인 것을 확인해 정상 whole controller만 선행 실행했다. native controller가 summary·tower·checklist·whole strict·현재 full strict를 계산하고 summary stage를 재봉인했다. [07:19:52 실행 영수증](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/prestage-controller-20261015T071426/receipt.json)은 PASS, 새 controller SHA `5c6b9ed7c867b01c244bc49c8ecfcac15d823323ca5b9b837e51b307f3773be4`다. 별도 summary worker·정책/producer 재계산은 하지 않았다. 이후 후보 재결속 결과는 아래 실제 영수증으로 확인한다.

## 07:10 이전 실패 재감지 판정

[감지기 독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/cron-completion-0710-temporal-independent-review.json)에 따르면 07:10은 감지 시각이며, source 10/14의 마지막 finalization terminal은 여전히 `next_preopen_preparation_failed`였다. isolated prepare PASS는 전체 finalization DONE를 대신하지 않는다. 따라서 이 경보는 미해결 실패의 재감지이고, 과거 실패 행을 삭제하거나 경보를 억제하는 수정 대상이 아니다. 이후 정상 DONE와 chain/snapshot/detector 결속이 확인되면 이전 실패가 해제되고, 원 06:50 완료 기한 이후의 복구 사실은 `recovered_late`로 보존된다. 다른 detector 실패가 남으면 전체 `summary_severity=fail`일 수 있으며, 최종화 복구를 모든 경고의 해소로 표시하지 않는다.

알림의 `timestamp`를 탐지 시각으로 명시하고 source/effective date 및 마지막 terminal reason을 함께 표시하는 것은 선택적 문구 개선이다. 기존 FAIL 행에 발생 시각이 없으므로 임의의 과거 시각을 채우지 않는다. 07:20 알림 감소도 최종화 완료 증거로 사용하지 않고 원 detector 결과와 실제 완료 영수증으로 확인한다.

## 새 후보·평가·완료 영수증과 실제 장전 실패 복구

[후보 재결속](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-stage-20261015T071957-a1be6c24/receipt.json)은07:26:53에 PASS했다. 후보 SHA는 `31e574ad0c9b6654c498661cad5612ea85bf7054e9412c08632488148353b053`, bundle은 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`이며 정책 판단값·현재 활성 정책·원 producer 영수증은 보존했다. [consumer 검증](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-consumer-20261015T072727-8ba50c22/receipt.json)도07:27:34에 PASS했다.

[보조 native evaluate](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/evaluate-20261015T072719-f2597af8/receipt.json)는07:27에 완료됐다. 새 평가 SHA `4de8ac9ccf803e0692016e12d3b8877fb6229ce3312155a330db0a26ab155c6d`의 policy generation 계약은 verified/findings 없음이다. 원 평가·50쌍·100요청·원 응답·경제성·정책 선택은 보존했으며 provider 호출은0이다. 갱신된 결과를 반영한 [전체 controller 실행](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/poststage-controller-20261015T073038/receipt.json)은07:36:07에 PASS, controller SHA `954070a102a65c1c26756d6b061d6192ca24d45ef480325bc20b103401b3399e`다. 보조 capability 경고의 자동 OPEN 행만 닫혔고 다른 현재 owner는 유지한다.

07:35 정규 PREOPEN은 기존 e74 준비물을 `prepared_source_or_release_changed`로 거부했다. [원 실패](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/actual-scheduled-preopen-failure-20261015T073501.json)는07:35:01/exit1/활성화 전/환경 파일 부재이며 원문 SHA `8d7203f7a9270a29a3f12892a51acd203f5532f6704450dbbf26945a7bb7867f`를 보존했다. 실제 실패만 허용하는 native `failed_preopen_recovery` lease 안에서 prepare를 한 번 호출했다. [복구 실행](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/failed-preopen-prepare-20261015T073706-a5a876ea/receipt.json)은07:40:04에177.582초/exit0으로 완료했고 새 readiness SHA는 `411bbb45d9e2fde7a49ff9d0622d12f9f9942061e8333a0cafaf59ef2b2c4747`다. 이 단계는 prepared_verified이며 정책 활성화·Main 기동·주문·provider 호출은 없었다. helper의26개 private 회귀와 [독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/failed-preopen-prepare-helper-independent-review.json)를 통과한 뒤 실행했다.

## 정상 PREOPEN 재시도와 전날 최종화 종료

설치된 cron의 router·wrapper와 기존 `THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live` 설정으로 [정상 PREOPEN을 재시도](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/normal-preopen-retry-20261015T074018/receipt.json)해07:44:28에 succeeded/exit0으로 완료했다. 준비물의 current_full_contract 검증은 findings 없음이며,07:42:30에 target15 bundle `1f069c…`를 활성화했다. 장전 성공 status SHA는 `bc535f18709ff7a21c592c491ad0529d44eb9f1741bc9b2310902e20d091f049`, bootstrap manifest 내부 seal은 `73a9a4f20bc146ea40c2f74966e107a3cb7773ef623dd1b9df0750a838adebad`다. 이 성공은 Main PID 소비와 별도다.

실제 target15 PREOPEN 성공 이후에만 source14의 역사적 최종화를 이어갔다. [고정 입력](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/historical-source14/input.json)은 새 source14 전체 controller 실행·canonical/immutable strict·summary·checklist·독립6단계와 별도 재봉인한 summary 단계·원 cleanup·실제 target15 활성 정책과 부트스트랩을 결속한다. 원 cleanup을 다시 실행하거나 PREOPEN 상태·과거 실패를 합성하지 않았다. [독립 검토](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/historical-source14/independent-review-v2.json)와18개 private 회귀를 통과했고, 정규07:45 detector 종료와 잠금 해제를 확인한 뒤 새 source14 full detector를 실행했다.

[실제 최종화 결과](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/historical-source14/result.json)는07:45:42 DONE다. 새 detector run은 `cron-20261015T074534-1440012`, report SHA는 `53bcc343652dc8bed5acd4b01b270268c1473e9628a763cd5284fb64920bff6c`, chain SHA는 `79310316b4f331d04a6ab3ad76bca5770eced98cc8db4259003e85a9bea389e2`다. 원 실패 행은 유지하고 새 DONE를 추가했다. 이 이어가기의 provider 호출·주문·추가 알림·Main 기동은0이며 정상07:55 기동 일정은 그대로다. 자식 detector의 당시 `live ancestor awaits this detector`는 부모 DONE 전 자기감지 상태이므로, 이후 정규 detector의 최종화 상태와 구분한다.

[07:50 정규 감시 관측](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/scheduled-detector-0750-after-recovery-observation.json)의 새 run `cron-20261015T075002-1440715`는07:50:08에 full7개 detector를 완료했다. source15 보고서 SHA는 `e3917ddc717bb9261055764ee9ce7b6210faab7c8398d3a076e0a96e37c964cf`다. `next_preopen_prepared_contract_invalid`와 auxiliary 생성 검증 경고는 없고, 원 최종화 실패는 `recovered_late`로 바뀌었다. 전체 severity는 fail에서 warning으로 바뀌었으며 실패 detector는0이다. 기존 entry_cancel_wait·rising_missed·holding_vote의 생성 검증 경고는 남아 있다. [현재 담당 항목 대사](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/scheduled-detector-0750-owner-binding.json)는 각 warning의 오늘 OPEN owner가 하나씩임을 확인하며 `UNRESOLVED_CURRENT_OWNER`는 없다. 이 별도 검증 업무를 이번 복구의 완료로 표시하지 않는다.

## 07:55 정규 기동과 실제 PID 소비

설치된07:55 cron이 선택본 `3d644d849`의 정상 런처를 실행했다. Main PID는 `1441388`, start ticks는 `8248936`, 실제 cwd는 선택 릴리스의 `src`다. PID 부트스트랩 검증은07:56:32에 PASS, 런처의 배포본 소비 영수증은07:56:38에 발행됐다. [07:57:02 실제 소비 대사](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/normal-startup-final-consumption-observation.json)는 native `startup_consumption_state=ready`, `reason=current_pid_consumption_complete`, `basis=native_preopen`, `pid_passed=true`, `pid_env_available=true`를 확인했다. 활성 정책은 target15 bundle `1f069c…`이며 준비·PREOPEN에서 검증한 manifest seal `73a9a4f…`와 같다. 관측 SHA는 `ce380d367d083e23d5d6499873838ba2161166a05a2d409b3239426dffd7e24d`다.

수동 Main 기동·추가 재기동은 하지 않았다. 실행 코드 선택은 계속 `3d644d849`이고 요청된 계산 수정 `a179bb42d`를 포함한다. 이 마감의 범위는 요청된 경보 복구·최종화·준비·정규 PID 정책 소비다. 거래 성과나 남은 별도 생성 검증 업무의 완료를 주장하지 않는다. 준비와 strict가 결속한 checklist 본문은 바꾸지 않고, 이 감사 기록과 실제 소비 영수증으로 최신 실행 결과를 보존한다.

[기동 후 첫 전체 상태 점검](../../tmp/sentinel-integrated-postclose-20261014/morning-alert-055138-recovery/normal-startup-first-health-observation.json)은07:58:53에 자동 생성됐다. run `24248b7b7bf44c908a111883f3a2e72b`, 원문 SHA `f855eb802f900bad72e113c0f37a3f44fdfb283cb52a415948a56a5fb2a089a0`이며 같은 PID·start ticks·선택 commit의 startup ready 이후 실행된 full7개 검사다. 초기화 실패·fail detector는0, process/thread health·resource·새 오류 로그·Kiwoom auth8005 로그 검사 모두 PASS다. 전체 warning은 기존 세 생성 검증 경고와 `recovered_late` 때문에 유지된다. 이 보고서를 위해 수동 detector나 추가 알림을 실행하지 않았다.
