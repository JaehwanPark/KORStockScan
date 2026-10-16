# 장기4·원천·감시 신원·로그 보존 통합 검토

사용자 지정 `04c1a4d65d27380e36e1f94eada8c48605adedff`에 추가 수리를 통합한다. 실제 선행 선택은 `922b9cbc370c4c6c002b3c1fcdb3ed061719e4a2`, PID3729660/start19142841이다. 손절 기준은 사용자 후속 답변에 따라 그대로 유지한다. 구현·리뷰·보완 후 배포와 재기동은 승인됐으며 운영 결과는 별도 영수증으로 확인한다.

## 원인과 수리

- 장기 관측은 물리5개 안에서 3→4개로 배분하고 단기1개를 남긴다. 원 residence60/150초·native deadline·freshness·순번/lease 해제·주문 권한은 바꾸지 않는다. 기존 큐 동시성 안에서 긴 관측의 처리량을 늘리며 실효 처리량과 제출 개선은 자연 표본으로 확인한다.
- Main fixed-watch 매도 후 WATCHING을 생성할 때 원 DB owner 신원을 보존하고 현재 세션의 venue/bucket과 새로운 admission/warmup을 함께 저장한다. commit 이후 메모리 반영 실패의 재기동 복구도 같은 DB 필드를 사용한다. 이전 실행 호가·broker route·first-exact 시각은 새 감시에 재사용하지 않는다. symbol만 같은 과거 unknown 행은 fixed 소유권으로 추정하지 않는다.
- native TRUE/FALSE 관측 이력과 현재 실행 가능한 원천을 분리한다. 과거 유효 이력이 있어도 현재 stale/결손이면 주문과 source-covered 분모에는 넣지 않는다. exact item/epoch/PID/scope·sequence·lifecycle count 결속을 검증한 이력만 별도 관측으로 인정한다.
- 443670·007610의 기존 수신0 사례는 당시 local REG 송신만 확인됐으며 broker ACK나 wire 수신을 소급하지 않는다. 새 임시 lease에서는 0B/0D별 local REG→wire→normalized→native 경계와 최초 수신 시각을 terminal에 기록한다. 다른 item/transport epoch의 수신은 포함하지 않는다. 진단 hook 실패가 원 terminal 관측을 지우지 않도록 독립적으로 처리한다. VI 원천 결속은 추가하지 않는다.
- 15:01 경보의 298690/14:56:50 원 행은 150초 residence 중 첫 체결이148.097초에 도착했고 native_sequence1/observed_seconds0/UNKNOWN1이었다. observer의 양수 관측시간 조건이 이 유효한 필수 피처 부족 증거를 거부했다. 0초는 feature-gap 진단에만 허용하고 no-match/현재 coverage/ENTER_NOW/AI PASS에는 허용하지 않는다. 원 행 재생에서 feature-gap 검증 성공·no-match 거부를 확인했다. 나머지 실제 stale·route snapshot 결손은 계속 남긴다.

## 로그 LR01–LR09

[운영 계약](../operational-log-retention.md)이 정리 owner와 pin/참조/FD·한도 계약을 소유한다. 일반 운영 파일은 `src/engine/infrastructure/log_retention.py`, 기존 compressor는 구조화 원천의 native 계약을 소유한다. engine root에 새 모듈을 만들지 않는다.

1. Main 정보 로그의 반시간 truncate cron을 제거하고 writer가20MiB에서 닫힌 세대를 등록한다.
2. `.log` 이름/14일 기반 포괄 삭제를 제거한다. 열린 inode·변경된 세대·문서 참조·pin·미등록 파일은 보존한다.
3. resource recovery는 짧은 log lane만 호출한다. 종료0과 정확한 run-id/applied/complete terminal을 모두 확인해야 성공 cooldown을 기록한다.
4. 등록된 닫힌 세대에30일·10개·200MiB 한도를 적용한다. 보호 때문에 초과한 bytes와 다음 검토기한을 남긴다. 삭제 의도/완료 tombstone을 기록해 재시도한다.
5. sampler·sentinel·WS·snapshot·census stdout와 내부 tee를 첫 open 전 회전에 연결한다. cron 재설치 시 기존 aftermarket 항목이 중복되는 결함도 보완한다.
6. 매일06:17 달력 주기의 일반 로그/metric/tmp lane을 추가한다. postclose 선행 실패와 독립이며 원천 gate는 그대로다.
7. 과거10/08·12·13·14는 원 strict가 봉인한 checklist snapshot으로 전체 native 세대 검증을 다시 수행할 수 있다. 모든 다른 조건은 유지하고 원 controller/strict/checklist SHA를 gzip receipt에 기록·재검증한다. 당일10/16과 다음 정책일이 아직 지나지 않은10/15는 보호한다. 날짜 한정 pipeline 압축만 허용하며 원 영수증을 다시 PASS로 봉인하지 않는다.
8. tmp는 명시적인 owner/closed/expiry/hash manifest만 정리한다. 중단 시 삭제 의도가 없는 결손은 성공으로 만들지 않는다. worktree/OPEN/미등록 증거는 보존하고 전체8GiB·2일2GiB 증가 경보를 별도로 기록한다.
9. journald는30일/512MiB persistent/128MiB runtime/1GiB 여유 상한을 명시한다. 설치 전 설정 백업과 서비스 확인을 수행하며 즉시 vacuum은 하지 않는다.

## 리뷰·검증 및 인계

04c 기준 관련1,522개, 원천/감시/WS/router1,398개, retention/정책 인계2,114개 회귀가 통과했다. full cleanup/writer/compressor86개도 통과했고 후속 writer/cron 재설치44개도 통과했다. 기존 pandas 경고1개는 테스트 종속성 경고이며 실행 실패가 아니다. Python compile·shell 구문·diff·문서 print-only parser를 수행한다. 패키지 변경, 외부 sync, 실제 provider/계좌/주문/Telegram 호출은 코드 검증에 포함하지 않는다.

[공식 Kiwoom revision](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)의 specs.py, packaged0B/0D, core/client.py·ws_client.py, realtime/packets.py·stream.py 및 Postman을 확인했다. upstream에는kiwoom_docs가 없었다. 조회 시각·파일 SHA는 [공식 참조 기록](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/official-reference.json)에 있다. 요청/FID/REG/REMOVE/auth 프로토콜을 바꾸지 않고 원 packet의 exact-item 진단만 추가한다.

원 PREOPEN23a13aba6→검토된 최종 consumer18개 SHA pair만 handoff에 등록한다. 이전 승인된 수리와04c의 보유·재생 변경을 포함하며 dirty/다른 before·after/origin 세대는 계속 거부한다. 정책 숫자와 원 bundle/hash는 보존하고 코드 변경 family의 network-denied fixture를 새로 게시한 다음 정규 ordered deployment로 선택·PID 소비를 확인한다.

- [기준04c 검증](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/base04-tests.log)
- [원천 검증](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/source-final-tests.log)
- [보관·인계 검증](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/retention-handoff-final-tests.log)
- [작성자·cron 검증](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/writer-final-tests.log)
- [15:01 원 행 재생](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/alert1501-frozen-row-replay.json)
- [과거 원천 보관 판정](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/historical-storage-readonly-verification-after.json)
- [검토 source pairs](/home/ubuntu/KORStockScan/tmp/long4-retention-integrated-20261016/reviewed-source-pairs.json)

기존 `NonfixedDispatchReadinessReview1012`, `AuxiliaryCircuitRecoveryRepair1012`, `HoldingProfitExitSourceContractRepair`, `DirectFamilyPreopenPolicyHandoff`와 새 `OperationalLogRetentionRepair1016`가 각 수용을 소유한다. 과거 주성 WATCHING49353의 유실된 fixed 소유권은 원 매도→새 row의 정확한 연결 증거 없이 역으로 채우지 않는다. 다음 자연 매도/재감시와 새 lease 수신, 실효 처리량·제출·비용 후 성과는 코드 PASS와 별도 OPEN이다. 오래된 원천·unknown 신원·수동/retired custody·DANGER·계좌/주문/수량 안전장치는 유지한다.

배포 전 추가 리뷰에서 rising/holding 보고서의 현재 capability 세대 연결도 새 코드로 갱신했다. 원 보고서·이전 fixture를 보존하는 정확한 source→successor 쌍이며 새 fixture 없이는 검증되지 않는다. 관련147개 회귀가 통과했다.
