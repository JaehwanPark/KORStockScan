# 가격 전진 후보 통합 코드리뷰·배포 — 2026-10-15

사용자 지정 `0d4f422a85fc3366971b7fa427108c895d512714`를 현재 운영 `ebcde3d87e3dd73f6d33e0d0bce1f71f009c9b31` 및 결과 기록 `8981a0cf5` 위에 통합한다. 작업본은 `/home/ubuntu/KORStockScan-worktrees/entry-progress-deploy-20261015`다. 주문 원장·보유 사전 snapshot·최종화 future vote reader 수리를 모두 보존한다. 사용자 승인 범위는 리뷰·보완·배포·재기동이다.

## 리뷰에서 확인·수리한 결함

1. 누적 A/F 후보의 관측 adapter 누락: native cumulative pending을 `selected_pending_count`와 branch 대기 시각에 연결하지 않아 실제 bid hold 중에도 no-match로 종료할 수 있었다. 기존 확인 상태를 읽어 대기를 투영하며 소비·재시작하지 않는다. cumulative root의 hold/기간/가격 특징, F의 원 확인점 요구와 선택적 refinement를 분리한다. 가격 전진 값은 동일 native epoch/sequence의 detector window에서만 읽고 stale은 UNKNOWN으로 유지한다. 실제 A18 hold와 A19 가격 window를 사용하는 두 회귀가 원 reader에서 실패하고 수정 후 통과했다.
2. observer raw/selected 모수 혼동: 전임 PID17:57 라온시큐어 원본의 raw_ready1/selected_ready0을 오류로 보았다. 양의 raw count는 정확한 native scope/readiness/branch truth 결속과 실제 불일치 이력이 확인될 때만 별도 모수로 인정한다. 선택 ready/TRUE/pending·stale·잘못된 PID/scope·변조 lifecycle은 거부한다. 원본은 수정하지 않고 old=false/new=true를 확인했다. 기계 평가·AI·주문 건수는 늘리지 않는다.
3. 보조 연구 capability 세대 누락: cumulative materialization/registration/catalog/reader 변경이 보조 세대 코드 해시에 포함되지 않아 이전 fixture가 새 검증 계획과 충돌했다. 실제 소비하는 누적 producer/consumer를 auxiliary 세대에 포함했다. 공통 세대 파일의 변경으로 네 family의 정확한 successor 해시와 독립 network-blocked fixture가 모두 필요하다. 기존 보고서·원 fixture를 덮어쓰지 않고 현재 코드의 별도 영수증을 발행한다.

관측 보완은 기존 `scalping/reversal_source_diagnostics.py`, `monitoring/submission_bottleneck_monitor.py`가 소유한다. 새 engine-root 파일은 만들지 않았다. Kiwoom wire 요청·FID·REG/REMOVE·인증·주문 계약은 변경하지 않았다. 기계 신호·보조 입력/응답·현재 membership·손절/preset·provider·계좌/수량·stale/hard safety는 보존한다.

## 검증과 배포 경계

- 현재 정책 128 scope/76,800행의 신규 비교에서 확인607개 및 전체 신호 SHA가 전임 배포본과 일치했다. provider0·order0인 고정 workload 비교이며 실제 제출·경제성 증명이 아니다.
- 지정 커밋의 native 연구27 partitions는 동일37개 계약 코드 SHA와 원천 파일 해시를 재검증해 재사용했다. 5,587,427행 전체를 이번에 재생한 것으로 표현하지 않는다. 실제 연구 결과와 불변 catalog는 새 연구와 구 연구로 구분한다.
- 실제 10/16 pending의 구 batch reader·근거5개 검증과 bytes 불변을 확인했다. 새 50가설 private 준비안은 같은 parent의 기존38가설 등록과 충돌하므로 intake하지 않는다. 이번 코드 배포가 새 후보의 정책 선택·활성화를 뜻하지 않는다. 기존 `CumulativePolicyAdoptionDeployment1015`의 승인·날짜·parent CAS를 유지한다.
- 관련 기능·producer/consumer·최종화·배포 경계·detector 회귀를 수행한다. 최초3개 실패는 격리 작업본에 기존 joint 원천 fixture가 없어 발생했다. 원본3개를 private 작업본으로 복사한 뒤 joint65개 PASS를 확인했다. 운영 원천을 생성/수정한 것이 아니다. 재리뷰 후 최종 전체 회귀·compile·diff·문서 parser를 확인한다.
- 배포 전 네 family 독립 fixture와 정확한 code handoff를 검증한다. 이후 기존 ordered driver로 이전 PID drain→선택→원 정책 검증→새 PID attestation을 수행하고 다음 정규 observer/detector의 같은 run·health projection·cron 최종화 결속을 확인한다. 과거 보고서를 재생성하거나 실제 source gap/지연 경고를 숨기지 않는다.

기존 owner `DirectFamilyPreopenPolicyHandoff`, `NonfixedDispatchReadinessReview1012`, `CumulativePolicyAdoptionDeployment1015`를 재사용한다. [리뷰·시험·원본 재현·배포 증거](../../tmp/entry-progress-deploy-20261015-1820/). 실제 코드/배포/정규 소비 결과는 완료 뒤 아래에 추가한다.

## 삼성전자 체결 후 대기 경고 추가 점검

18:17:41 WS 원본은 삼성전자005930 / Main49266 / NXT 주문0060210의 SELL1주@210,000원을 기록했다. 바로 뒤 `OWNER_RECEIPT_BLOCKED / symbol_owner_policy_fail_closed:SymbolOwnerPolicyError`로 체결 반영이 중단됐다. 18:18:21 취소는 `506550:취소가능수량이 없습니다`로 거절됐고, 이후 계좌 동기화는 잔량0 / 장부1의 `owner_registry_broker_quantity_deficit`로 차단됐다. 18:34:47의 VI 의심 문구는 시간 초과 공통 경고이며 이번 사건의 VI 증거가 아니다. DB49266도 SELL_ORDERED / sell_price0 / sell_time없음이다.

원장 native projection은 writer flock 없이 조회해 정상 동시 append 중에도 fail-closed할 수 있었다. cold/warm reader 두 원본 회귀에서 writer 동시 진입을 확인했다. live projection에 기존 writer의 공유 flock을 적용하고 frozen source는 새 lock을 생성하지 않으며 해시·세대·계좌·manual disposition 검증을 유지한다. 실제18:17 오류에는 내부 예외 원문이 기록되지 않아 해당 사건의 세부 예외를 경합으로 확정할 수는 없다. 체결 consumer가 owner-policy 오류에서 종료해 이 체결을 반영하지 못한 사실은 확인됐다.

기존 read-only kt00007 단일 조회는 정확한10/15 / 0060210 / A005930 / 현금매도 / NXT / 주문1 / 체결1 / 잔량0 / 단가210,000원 / 주문시각18:17:41을 반환했다. 원본 row와 정상 continuation/normalization 메타를 보존했다. 원천 SHA `31cdaa5830579c4193b49ca6d481e5ee080fd6299c3a58b61df39d542e8861a9`. 공식 HEAD953e5dbff123f437ab4d11a78a95191a685eb51f와 packaged spec/specs/core/Postman을 재확인했다. kiwoom_docs는 없으며 주문시각을 체결시각으로, 체결단가를 실제 비용으로 변환하지 않는다.

별도 source-bound 복구 preview는 원장 사본의 기존 bytes 전부를 보존하고 기존 record_fill/terminal 계약으로 해당 Main SELL만 연결한다. 실제 체결번호는 비워 두고 terminal reason에 원천 SHA를 결속한다. Main drain 후 exact DB row CAS로 COMPLETED / sell_price210000 / sell_time NULL / profit_rate NULL을 적용하도록 준비했다. 비용·정확한 체결시각 부재를 경제성0이나 확정 순이익으로 대체하지 않는다. preview의 재실행 멱등성 및 잘못된 주문·부분체결·잔량·단가·일자·거래소·방향7종 거부를 확인했다. 실제 적용·PID 상태는 후속 영수증으로 구분한다. 새 주문·취소·WS 재생은 없다.

최종 통합 회귀3,201개 PASS, 원장·소유권·실체결·동기화 관련 추가252개 PASS(기존 warning1), Python compile/diff/print-only parser PASS. 원본 cold/warm 읽기 잠금 실패2개를 재현했고 새 reader에서 통과했다. 코드 리뷰의 해당 변경 범위 미해결 결함0이며, 원 체결에 대한 내부 예외 세부 원인은 로그 부재로 미확정이다.

## 실제 복구·배포

- 통합 배포 commit `05b78a4011ab7627b7e8ddc341d688fecf8f6a4e`; 작업 트리 `/home/ubuntu/KORStockScan-worktrees/entry-progress-deploy-20261015`. 지정0d4f422a8과 기존 운영 수리를 함께 포함한다.
- 네 계열의 별도 network-blocked fixture: entry_cancel_wait93 / rising_missed86 / auxiliary83 / holding_vote91 PASS, 총353개. 기존 source14 원 보고서를 덮어쓰지 않았다. 정확한 candidate delay/stop/holding와854개 source hash code handoff를 검증했다.
- 18:58:19 Main drain 구간에서 원장 전체 prefix를 유지하고 정확한0060210 체결1/금액210000 및 terminal 기록을 append했다. terminal event `7392027d88867d40361de6f97ff4d273533ed1605f78cced8cef092b24a3cd71`, 기존49266 owner 수량0, DB CAS는 COMPLETED / sell_price210000 / sell_time NULL / profit_rate NULL이다. [실제 복구 영수증](../../tmp/entry-progress-deploy-20261015-1820/samsung-recovery-applied.json). 원천 기반 복구 script SHA50758eb60354b0bd4bb5c86ce508405cd31e5c8b736684da9c8d24a709e4d542, ordered driver embedding SHA924c1a9bc579c610eb8965e2d82f8a57c3f471268b9c5b848036cdba3899b2d6. 새 broker 주문/취소0.
- 19:00:41 ordered transition complete/pass. 전임PID2552591 종료, 새PID2610988/start12230101, cwd `/home/ubuntu/KORStockScan-runtime-releases/entry-progress-custody-20261015-05b78a401/src`. native bootstrap/handoff 소비와 현재 WS 연결 PASS. 원 정책·PREOPEN/env·기존10/16 pending·수동 제외·10/14 controller/strict/summary/stop 원본 SHA 유지. [전환 영수증](../../tmp/entry-progress-deploy-20261015-1820/deployment-result.json).
- 19:02:57의 새 PID 218초 관측에서 삼성전자 경고/owner receipt/sync 오류0, 기존49266 포지션 수량0과 DB 완료 및 원본 보존9조건 PASS. 두산·알테오젠의 기존 보유 관측은 자연 재개했고 주성의 기존 수동 이관은 유지한다. 새 주문 성공·비용 포함 경제성 개선으로 확대 해석하지 않는다.
- 19:02:07 첫 정규 detector는 artifact_freshness warning(첫 현재세대 관측 대기와 기존 holding_exit_sentinel_aftermarket_report stale), log_scanner/process_health PASS. resource_usage는 실제 I/O wait39.63% >=35% fail이었으므로 해당 실패를 보존하고 후속 회복을 별도로 확인한다. cron은 원10/14 최종화의 recovered_late 경고를 유지하며, 새 PID의 historical generation 소비/세대 결속에는 오류가 없다.

## 정규 산출물 수용과 남은 관측

19:04:37의 정규 detector/observer 동일 run·health projection·현재 commit/PID 결속을 포함한 배포15조건이 모두 PASS다. artifact_freshness fail0이며, 기존 holding_exit_sentinel_aftermarket_report stale와 scanner 기계 식별0에 따른 관측 부분 범위 warning은 남는다. 현재 observer의 health_unmet는 앞선 오류 묶음에서 해소됐지만 full semantic coverage나 자연 주문 성공으로 선언하지 않는다. [배포 수용](../../tmp/entry-progress-deploy-20261015-1820/postdeploy-verification.json).

동일 탐지의 resource_usage는 PASS로 회복했다. 다만 log_scanner는 별도 OpenAI analyze_target timeout4건으로 fail이다. 19:04:14~19:04:48 실제 삼성전자 재진입 평가에서 잔여 예산223~831ms의 timeout5건이 기록됐다. 이번 매도 주문0060210의 상태 오류 재발이 아니며 provider/예산/threshold는 변경하지 않는다. 기존 `AuxiliaryCircuitRecoveryRepair1012`가 원 기계/AI 요청 시각·총예산·잔여예산 원천을 연결해 후속 원인을 확인한다. [별도 API 경보 원본](../../tmp/entry-progress-deploy-20261015-1820/postrestart-provider-errors.json). 배포 수용 PASS와 전체 시스템 무경고/보조 판단 자연 성공을 구분한다.

10/14 최종화 recovered_late와 기존 holding sentinel 경고는 보존한다. 새 코드·PID의 역사적 finalization 결속, generation issues없음, handoff done/findings없음 및 원 보고서 SHA 불변은 확인했다. 별도 API log_scanner fail 때문에 모든 detector 무실패를 요구하는 통합 finalization 관측은 아직 pending이며, finalization 자체의 generation stale 재발을 뜻하지 않는다. 19:04:59 기준 새 PID341초 동안 매도 대기/owner receipt/sync 오류0 및 원장/DB9조건 PASS. [삼성전자 재기동 후 검증](../../tmp/entry-progress-deploy-20261015-1820/samsung-postrestart-verification.json).


## 19:06 API 및 artifact 경보 재발 — 현재 수용 미완료

19:04:37의 artifact 비실패는 해당 관측 시점의 역사적 결과다. 19:05:49 observer `e3827a8c1fe84dfd99d5789e2ceb3656`에서 실제 시간 초과와 원천 결손이 새로 관측됐다. 후속 19:19:24 정규 detector도 19:15:50 observer `8e93046c19a74a0180898cabc524a12a`와 동일 run으로 결속되며 artifact_freshness FAIL을 유지한다. 따라서 현재 상태를 **무오류 수용 미완료**로 정정한다. 배포된 코드/PID는 `05b78a4011ab7627b7e8ddc341d688fecf8f6a4e` / 2610988 / start12230101 그대로다. [원본 해시·요청 결속·현재 탐지 진단](../../tmp/entry-budget-alert-20261015-1906/diagnosis.json).

- 19:05:49의 정확한 현재 PID 분모: 기계 관측21 / 연결 trace20 / 실제 provider 시도12 / 응답5 / timeout7. 원 응답은 CAUTION4·VETO1·PASS0이다. `pending_or_withheld_auxiliary_pass_not_quiet` 문구만으로 실제 PASS 보류가 있었다고 해석하지 않는다. 미연결 관측1건은 복구 또는 진행 중 여부를 추가 대사해야 하며, 누락 결함으로 확정하지 않는다.
- 19:04:14~48 timeout5건은 모두 삼성전자 새 진입 평가의 OpenAI 원 기한 소진이다. 각 trace의 signal ID·원 epoch+5·PID/start·요청을 결속했고 HTTP 예산223~831ms, HTTP local lock 대기0ms를 확인했다. 실제 SDK가 timeout 후 언제 종료했는지, provider 서버 자체가 느렸는지는 이 자료로 확정하지 않는다. 매도0060210의 체결 반영 복구와 다른 사건이다.
- 19:13:19 누적 성능 표본에서 native-ready→claim52건 p95 4.880초 / max4.944초다. 준비 queue50건 max23.45ms, 준비 service50건 max159.84ms, 응답 성공10건 max1.484초다. 서로 다른 단계·표본의 p95를 더하지 않는다. 주 지연은 provider 요청 이전에 존재하며 준비 queue 단독 병목 근거는 없다.
- 현재 v6 selector는 유효 ready를 event epoch/sequence 오름차순으로 확보한다. 진행 중 평가가 끝나는 동안 후속 신호가 누적되면 원5초가 거의 소진된 신호가 다시 선택될 수 있다. 이를 곧바로 최신 신호 우선이나 후보 폐기로 바꾸면 기존 priority/전체 기회 보존 계약을 바꾸므로 이번 진단에서 변경하지 않았다. 지연 전체를 selector 구현 결함 하나로 단정하지 않는다.
- 기계 원천에는 candle 시간/age 실패2건과 입력 refresh 실패3건도 별도로 존재한다. `machine_trace:entry_machine_input_deadline_expired` 외 원천 문제를 전부 provider timeout으로 합치지 않는다. 코드·정책 publication 검증 성공이 이 원천/요청 결손의 해소를 뜻하지 않는다.

실행 owner는 기존 `AuxiliaryCircuitRecoveryRepair1012`다. 해야 할 일은 (1) 원 priority·전체 signal identity·원5초·기존 동시성을 보존한 Main 인수 및 정책 검증의 확인된 비용 축소, (2) 미연결 관측1건과 완료봉 실패의 producer→consumer 대사 후 재현된 결함 수리, (3) 같은 workload의 p95 목표와 다음 정규 observer/detector 동일 run 수용이다. 목표는 기존 native-ready→claim p95≤250ms / signal→live capture p95≤1초를 유지한다. 오류를 warning/PASS로 덮거나 최소 잔여시간 veto를 추가해 성능을 개선한 것으로 집계하지 않는다.

재발 후 이번 점검은 원본·현재 PID·요청·code path 대조와 문서 정정이다. 새 runtime code 수정/커밋·배포·재기동·provider 호출·주문·전체 주문 경로 재생은 수행하지 않았다. 따라서 추가 수리 완료나 전체 detector 정상으로 보고하지 않는다. 문서 변경은 print-only parser와 diff 검증으로 닫으며, 기존 통합 코드 시험 수를 이번 재발 해결 시험으로 재사용하지 않는다.

## 후속 승인에 따른 요청 결속·검증 비용 수리

사용자가 수리·코드리뷰·보완·배포·재기동과 `7b2e421e3` 통합 확인을 지시했다. 실제 선택본 `05b78a4011ab7627b7e8ddc341d688fecf8f6a4e`와 PID2610988/start12230101을 다시 확인했다. 지정7b2e421e3은 이미 선택본의 ancestor이며 이번 후속 통합에서도 유지한다. 기존0d4f422a8·보유/재생·체결 반영 수리도 보존한다. 이는 코드 포함 확인이며 새 누적 정책 후보의 intake/선택 승인을 합성하지 않는다.

확인된 결함은 source/preflight 또는 non-entry의 조기 반환이 provider transport metadata를 거치지 않아 원 async 요청 ID·PID/start·마감·venue·scanner generation을 결과/trace에 남기지 않는 경로다. 원 여섯 필드만 공통 결과 병합에 전달하고 실제 trace writer까지 검증한다. arbitrary metadata의 decision 유입과 provider 호출/주문은 거부한다. 원 구현을 격리한 두 회귀에서 ID 유실 실패를 재현했고 새 구현은 통과했다. 이것으로 원천 부재를 정상으로 바꾸거나 진행 중이던 과거 미연결 한 건을 누락 결함으로 확정하지 않는다.

정책 검증은 이미 절대경로인 문자열을 매번 Path로 재구성하던 비용만 줄였다. 각 경계의 전체 file stat·symlink/ancestor·inode/ctime·pointer 변경 검증은 유지한다. 실제 같은893개 의존 원천을 변경 없이 교차50회 측정한 검증 구간 p95는10.867ms→5.488ms, median10.261ms→5.336ms이고 전 signature가 동일하다. 전체 native→claim 지연이나 provider timeout이 같은 비율로 개선됐다는 증거는 아니다. 기존 priority·기회·동시성·원5초·원천/주문 안전장치와 오류 분류는 변경하지 않는다. [측정 원본](../../tmp/entry-budget-alert-20261015-1906/signature-benchmark.json).

생산자·조기 반환·정상 provider 응답·기록기·의존 검증·exact source handoff를 자기 리뷰하고 trace 실기록 검사와 변조 거부 검사를 보완했다. 기본 관련550개, 계약1,692개 PASS 후 새 exact map45개를 더했으며 최종 handoff1,506개와 trace321개 회귀를 통과했다(중복 합산하지 않는다). Python compile·diff·print-only parser로 문서/코드를 닫는다. Kiwoom wire/parser/recovery 계약, provider 값, 기계 판단값과 안전 임계값은 변경하지 않았고 전체 주문 경로/provider replay는 실행하지 않았다. native37개 계약 파일의 원 parity 해시는 동일하고 네 family의 기존 코드 세대 fixture를 현재 코드/원천으로 재검증한 뒤 재사용한다. 실제 배포·정규 산출물 수용은 아래 후속 영수증으로 구분한다.
