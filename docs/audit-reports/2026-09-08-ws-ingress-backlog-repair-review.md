# 9/8 WS ingress backlog 보완 리뷰

사용자 지시: 미해결 문제 보완 → 코드 리뷰/보완 반복 → commit/push/main 병합 → 필요시 우아한 재기동. 기존 source-quality·broker·order·수량·threshold·provider·owner 정책은 유지한다.

## 원인과 수정

11:00 모니터링에서 main PID461794의 유효 micro trade9263/depth7635가 정체되고, exchange→handler 지연 약198초와 TCP Recv-Q300593bytes를 확인했다. worker/writer 오류나 디스크 부족은 없었다. 로컬 backlog가 존재하므로 전 구간을 외부 지연으로 제외하지 않았다.

동일한 합성 0B/0D 메시지500개(1000개 event), history150회 준비 후 cProfile에서 `_handle_message`35.225초 중 `_snapshot_target`34.606초가 걸렸다. 매 event마다 최대120개 recent trade와 route/depth/strength history를 전부 deepcopy한 뒤 최신값1개로 coalesce하여 대부분의 복사를 버리는 구조가 직접 병목이었다. 합성 실행은 broker/WS 연결·주문·Provider 호출 없이 로컬 handler만 호출했다.

- 기존 WS 모듈의 `_snapshot_target(include_history=False)`는 현재 event의 route/type/epoch/price/BBO·raw timestamp를 깊은 복사하고 누적 history만 제외한다. micro와 limit-down raw consumer는 각0B/0D를 원래 순서대로 전수 소비한다. 해당 consumer의 필드 사용을 검토하여 history 의존성이 없음을 확인했다.
- 기존 `REALTIME_TICK_ARRIVED` coalescing worker가 market-data lock 안에서 최신 full history를 떼어 전달한다. pending queue의 target 참조는 private이며 EventBus에 노출하지 않는다. callback은 lock 밖에서 실행한다. `get_latest_data`와 dashboard의 전체 snapshot 계약은 유지한다.
- 재리뷰에서 pending batch와 snapshot 복사 사이의 새 update 경쟁을 보완했다. ingress와 같은 market-data→tick lock 순서로 batch를 동결해 다음 batch와 중복된 최신 snapshot이 생기지 않도록 했다.
- raw 데이터 누락·순서 변경, observation-only의 runtime 이벤트 유입, consumer의 snapshot 수정이 live state를 오염시키는 회귀를 검증했다. 주문체결00, LOGIN/PING, REG/REMOVE/reconnect·freshness 기준은 바꾸지 않았다.

동일 cProfile 재현은1.325초, 수신 handler 누적시간 약26.6배 감소다. 이는 **coalescing consumer가 실행되지 않는 ingress 경로의 합성 측정**이며 전체 bot throughput·순이익 개선량이 아니다. dispatch/dashboard 전체 snapshot 비용과 자연 수집은 실제 새 PID에서 별도 확인한다.

## 공식 reference 및 검증

Kiwoom 공식 repository main을9/8 11:16 전후 조회/clone하여 SHA `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. `kiwoom_docs`가 없는 현 revision이므로 없는 문서 의미를 추정하지 않았다. `kiwoom/_data/kiwoom_api_spec.json`의00/0B/0D REAL/values, `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/{packets,decoders,events,stream}.py`, Postman collection을 확인했다. 기존 protocol/field/route/limits는 유지하고 로컬 snapshot 처리만 변경한다.

`test_kiwoom_websocket`, `test_micro_reversion_forward_collector`, `test_limit_down_watch`, `test_symbol_owner_coexistence`: **305 PASS**. Python compile 및 diff whitespace 검사 통과. 초기 limit-down handoff fixture1개는 실제 당일 owner policy를 읽고 broker-account key가 없는 test process에서 올바르게 fail-closed하여 실패했다. fixture만 임시 missing-policy 경로로 격리하고 재검증했다. 운영 owner guard 완화는 없다. pandas 의존 라이브러리의 기존 deprecation warning1개는 설치/업그레이드 없이 유지한다.

리뷰 범위 내 미해결 코드 finding0. 메인 submitted0은 별도 exact funnel/AI/latency 결과이며 신규 BUY를 만들기 위한 threshold·정책 변경은 하지 않았다. scanner 경제성 floor·과거 micro ingress loss·실현비용 미대사는 수리 완료로 닫지 않는다. 다음 자연 수집/through-close는 기존 `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`, submit/fill/terminal은 `EntryRecheckNaturalAttribution0907`에 유지한다.

## 배포·자연 수용

검증한 변경만 commit/push/main 병합 후 `restart.sh`의 기존 Samsung owner handoff/종료/새 PID 경로를 사용한다. 시작 전후 KRX/NXT broker 잔고·미체결과 owner 원장을 비교하며 독립 위젯·에피소드 process는 유지한다. 새 PID source commit/dirty·runtime env verify·WS LOGIN/first-data·micro 수집 증가·queue/writer·중복주문을 확인한다. source/authority 검증 실패 시 임의 guard 완화·추가 restart를 하지 않고 직접 실패를 보존한다. rollback은 본 WS 변경 revert와 동일한 승인·broker 대사 절차이며 운영 정책값을 이전 값으로 덮어쓰지 않는다.

코드 `7077831a`를 `codex/ws-ingress-backlog-20260908`에 push하고 main fast-forward 및 origin/main push를 완료했다.

11:26:08 재기동 전 broker 읽기 대사: widget005930/episode010140/episode181710 각10주, target0038063/0018672/0032762 각10주. 최신 intent 원장과 같은 owner·수량이고 주문번호 owner 충돌0. 삼성 위젯은 11:00 관찰 이후 자기 정책으로 새 episode를 연 상태이며 기존 완료분과 구분한다.

실제 재기동은 **미실행**이다. 병합 중 별도 작업이 같은 작업트리의 `sniper_state_handlers.py`, `entry_recheck_policy.py`, submit-drought/source-quality producer, 신규 monitoring 모듈과 postclose wrapper를 수정하기 시작했다. 해당 변경을 임의 stash/삭제/commit하거나 미검증 상태로 새 PID에 함께 로드하지 않았다. 이 배포 보류는 승인 부족이 아니라 실행 코드 generation을 검증·고정할 수 없는 상태 때문이다. [review gate](/home/ubuntu/.codex/skills/korstockscan-review-gate/SKILL.md)의 “Do not restart trading processes ... until implementation, post-fix re-review and targeted validation pass” 조건에 따라 다른 변경의 검토가 닫힌 뒤 동일한 기존 승인 재기동 절차를 이어야 한다.

기존 PID461794/f67a7ec7은 transport epoch1788834016998751407로 자연 재연결한 뒤, 유효 trade/depth가11:24 17777/16192 →11:27 20982/21308 →11:28 21787/22806으로 증가했다. timestamp rejection882087은 이 구간 동안 증가하지 않았고 worker/writer 오류0이다. 이는 **기존 코드의 자연 회복**으로 새 보완의 배포 효과가 아니다. 새 WS 코드의 PID 소비와 장마감 연속성은 OPEN. 과거 rejected 원천을 복원하거나 Provider hold를 자동 해제하지 않는다.
