# Main 보유 AI 문맥 사전 순회 경합 수리 — 2026-10-15

17:30:32 기존 d05ebbf87/PID2470537의 Main 보유 처리에서 `dictionary changed size during iteration`이 발생했다. traceback은 `_observe_post_probe_hard_abort_recovery`→`_post_probe_ai_thesis_context`의 frozen parent prefix 검사다. 이 관측 함수가 공유 stock 사전을 직접 순회하던 중 다른 writer가 항목을 추가·삭제해 루프를 종료시켰다. 당시 진행 중이던 observer 수정본 df2afffa7의 기동 이전 오류이며, 해당 수정본 자체에는 이 별도 결함의 수정이 없었다.

## 구현과 검증

기존 `src/engine/sniper_state_handlers.py`의 해당 함수 진입에서 공통 `ENTRY_LOCK` 아래 shallow copy 한 번을 만든다. 잠금을 즉시 해제한 뒤 모든 scalar AI provenance·신선도·holding source 판독은 동일 복사본으로 수행한다. 키만 복사한 뒤 값은 원본에서 다시 읽는 혼합도 방지한다. 이 함수는 보고용 문맥 반환이며 실제 stock 쓰기·주문·원천 신선도 완화·퇴역 scale-in 재활성화를 추가하지 않는다. 기존 stale/partial frozen/부정적 AI 문맥 판정과 hard safety를 유지한다.

Event로 순회 시점과 실제 writer를 동기화한 추가/삭제×frozen parent 유무 네 경우에서 원 코드의 동일 RuntimeError를 재현했다. 수정 뒤 같은 시험을 포함한 scale-in/보유 원천 회귀963개 PASS. 보유 처리·exit safety·실체결/손익·코드 handoff/fixture 소비 회귀1,689개 PASS(기존 pandas_ta deprecation warning1). reader 복사 뒤 writer가 완료돼야 시험이 끝나므로 잠금을 관측 전체에 유지하는 회귀도 검출한다. 미완전 frozen source를 최신 AI와 섞지 않고 최신 DROP의 원 trace/snapshot을 유지함을 확인했다.

자체 리뷰→보완→재리뷰에서 이 함수의 scalar reader, 공통 RLock writer, source-only caller 및 handoff 소비를 확인했다. 정확한 원 PREOPEN source→후속 source SHA만 추가한다. shared handler 변경에 영향을 받는 rising_missed/holding_vote capability는 새 코드 세대의 독립 network-blocked fixture로 확인하고, 원 보고서·과거 fixture·정책 원본은 보존한다. Kiwoom wire protocol 변경은 없다. 코드 검증은 실제 배포·자연 실행·경제성과 구분한다.

원본 traceback과 재현/수정 회귀는 [수리 증거](../../tmp/holding-context-race-20261015-1730/)에 보존한다. 배포 owner는 기존 `DirectFamilyPreopenPolicyHandoff`이며, 기존 사용자 배포·재기동 승인 범위에서 observer 수정과 누적/보유/원장 복구를 모두 포함한 후속 release로 ordered 전환한다. 새 PID·원 정책 바이트·WS·보유 자연 관측·정규 detector 소비를 실행 영수증으로 확인한다. 외부 동기화·검증용 주문·provider 호출·과거 보고서 재생성은 실행하지 않는다.
