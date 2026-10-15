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
