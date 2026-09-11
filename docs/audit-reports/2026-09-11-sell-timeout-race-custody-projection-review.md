# 2026-09-11 sell-timeout 상태 경쟁·episode 체결 투영 수리 리뷰

작성 시각: `2026-09-11 15:29 KST`

## 결론

두 결함을 같은 검토 branch에서 수정했다.

1. main SCALPING 매도 terminal과 main-loop timeout이 같은 mutable target에서 경합할 때, 완료 후 생성된 새 `WATCHING` 행을 이전 cancel 실패 경로가 `SELL_ORDERED`로 되살릴 수 있었다.
2. 독립 episode의 원 target 전량체결은 owner registry에 exact 누적 체결금액과 최초 fill receipt 시각이 있어도 episode leg에 가격·시각이 투영되지 않았다.

수리는 owner·행·주문 identity를 좁히고 이미 존재하는 broker receipt fact만 전달한다. 주문 수량·가격·route·timeout·retry, Entry/Holding/Exit 판단, provider, threshold와 safety 계약은 변경하지 않는다.

## 공식 Kiwoom reference gate

- 확인 시각: `2026-09-11 15:26 KST`
- upstream: `Kiwoom-Securities/Kiwoom-REST-API`
- HEAD: `234560d213acd8871ae344b5481aecd2f30287fa`
- 확인 파일: `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`
- 확인 API: `kt10003`, `kt00007`, `ka10075`

`kt10003`은 `/api/dostk/ordr`, exact `orig_ord_no`, `stk_cd`, `dmst_stex_tp`, `cncl_qty` 계약이며 ACK는 체결 또는 terminal absence가 아니다. `kt00007`과 `ka10075`의 주문번호·원주문번호·체결/미체결·거래소 provenance를 별도로 확인했다. 이번 수리는 기존 request를 변경하거나 API를 추가 호출하지 않는다. 완료 receipt가 cancel dispatch와 경합하면 동일 행 소유권을 잃은 timeout 작업이 memory/DB 상태를 변경하지 못하게 하는 local interlock이다.

## 구현

- `src/engine/sniper_state_handlers.py`
  - sell-timeout dispatch가 최초 target ID와 `SELL_ORDERED` 상태를 고정한다.
  - outbox, intent/ack durability, cancel response, terminal absence, broker inventory와 DB 전환 경계에서 동일 소유권을 재검증한다.
  - memory mutation은 `ENTRY_LOCK` 안에서 ID와 허용 상태를 함께 검사한다.
  - DB 보존 predicate를 exact `id + stock_code + SELL_ORDERED`로 좁힌다.
- `src/trading/order/owner_custody_registry.py`
  - `FILL_RECORDED`의 immutable receive 시각을 후속 terminal event 뒤에도 `fill_observed_at_kst`로 보존한다.
- `src/trading/order/profit_stagnation_owners.py`
  - exact episode owner/position/symbol/date/order, 전량체결 수량과 나누어떨어지는 양수 누적 fill amount가 모두 일치할 때만 원 target 체결가격·시각을 episode leg에 투영한다.
  - 결손·partial·multi-price 비정수 평균·identity 불일치는 계속 null이다.

## 반복 리뷰

첫 race 수리 뒤 재리뷰에서 broker/network 대기 후 일부 상태 mutation이 소유권 검사와 원자적으로 묶이지 않은 P1 결함을 발견했다. 모든 후속 memory mutation을 lock 내부 검사와 결속하고 DB predicate도 좁혔다. 성공적인 cancel terminal 처리 중 기존 helper가 먼저 `HOLDING`으로 바꾸는 정상 경로는 같은 target ID에 한해 최종 cleanup을 허용한다. 재리뷰 결과 범위 내 미해결 finding은 0이다.

## 검증

- `pytest -q src/tests/test_scalp_exit_safety_monitor.py src/tests/test_profit_stagnation_exit.py`: `146 passed`
- 앞선 custody 직접/인접 검증: `96 passed`, 확대 검증 `366 passed, 2 skipped`
- Python compile: PASS
- `git diff --check`: PASS

최신 main `59b5f6af` 위로 rebase한 뒤 sell/custody/profit-stagnation 및 S15 인접 suite를 확대 실행해 `329 passed`를 확인했다. compileall과 clean worktree 검사도 통과했다.

고정 release의 공유 `data` mount에서 같은 suite를 재실행하자 S15 receipt 테스트 2개가 운영 exact-date owner policy를 읽어 fail-closed했다. runtime 결함은 아니지만 배포 환경에 따라 결과가 달라지는 테스트 격리 결함이므로, 두 테스트에 명시적인 unmanaged-symbol owner-policy/registry stub을 주입했다. 수정 뒤 동일 확대 suite는 다시 `329 passed`다.

코드 리뷰 완료, 배포, 새 PID 소비, 자연 재발 0건과 비용 경제성은 별도 상태로 기록한다.
