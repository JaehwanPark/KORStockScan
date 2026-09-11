# 목표가 상향 원천 증거 보완·운영 배포

기준 시각: `2026-09-11 14:21 KST`

## 판정

코드 리뷰와 보완은 finding 0으로 닫혔고, 검토 commit `66a3189b03393bbf3f72d11a230510a912a9a0a0`을 운영 release `/home/ubuntu/KORStockScan-runtime-releases/target-pressure-audit-20260911`에 배포했다. 목표가 상향 판단식·threshold·수량·가격·비용·broker guard와 세 policy 파일의 바이트 hash는 변경하지 않았다. 배포 뒤 새 자연 목표가 평가 표본은 아직 없다.

## 발견과 보완

- 기존 `target_reached`는 실제 목표가 체결 여부가 아니라 `executable_bid >= target_price`를 뜻했고, `target_or_net_edge_guard`는 호가 도달과 비용 후 순이익 실패를 구분하지 않았다. 판단 기준은 유지하고 의미·하위 guard를 별도 필드로 기록한다.
- 1초 창의 첫/최근 0.5초 로컬 매수체결 수량, 목표가 이상 매수주도 체결 수량, trade/depth watermark age와 exact-route local projection 범위를 기록한다. 시장 전체 completeness로 확대하지 않는다.
- 마지막 판단 외의 흐름을 복원할 수 없던 결손을 보완해 최근 32회 요약을 보존한다.
- depletion/refill의 중간 호가행을 hash만으로는 독립 재계산할 수 없어, 목표가 pressure consumer에 한해 hash 입력에 사용한 정규화 depth/trade 행을 함께 보존한다.

변경 파일은 `src/trading/market/confirmation_window.py`, `src/trading/market/target_pressure.py`, `src/trading/order/target_ratchet.py`와 직접 테스트다. 첫 commit `2ef47511` 뒤 중간 호가행 결손을 재리뷰에서 찾아 `66a3189b`로 보완했다.

## 검증

- 직접·인접 consumer 회귀: `673 passed, 2 skipped`.
- 새 release에서 widget/episode 목표가 상향 테스트: `120 passed`.
- 관련 Python compile과 `git diff --check` PASS.
- 운영 source tree는 검토 코드 commit `66a3189b`로 고정했다. 후행 배포 문서 commit은 실행 코드를 변경하지 않는다.
- target-ratchet policy SHA256은 배포 전후 `d455951e180966d78cee6b70e8b11df3e69b3206c74c7c32d2c36a1a6acc6f08`로 동일하다. profit-stagnation `aa2d4794...`, entry-adverse `1536dfab...` pin도 실제 PID에서 검증했다.

## 배포·재기동 receipt

14:17:57 KST에 공통 선택 원장과 systemd 17개 경로를 새 release로 연결하고 cron 9개 routing 및 postclose/finalize print-plan을 검증했다. 변경 코드를 실제 소비하는 아래 네 active 매매 service만 보유·미종결 주문 0을 확인한 뒤 재기동했다.

| Unit | 이전 PID | 새 PID | 상태 |
| --- | ---: | ---: | --- |
| widget signal auto trader | 364143 | 452008 | active/running, Result=success, NRestarts=0 |
| Samsung afternoon | 427218 | 452023 | active/running, Result=success, NRestarts=0 |
| Samsung Heavy afternoon | 427486 | 452198 | active/running, Result=success, NRestarts=0 |
| SK Eternix afternoon | 427462 | 452399 | active/running, Result=success, NRestarts=0 |

배포 직전 한국전력 afternoon은 1주와 원 목표 주문이 있어 재기동 대상에서 제외했다. 14:14:13 KST 원 목표 1주가 정상 체결되어 `COMPLETE/position_qty=0`으로 종료됐고, 이후 broker 대사에서도 미체결 주문은 0건이었다. 재기동 전후 registry는 804행으로 동일했다. 기존 broker 보유는 삼성전자25주와 다른 owner/manual 1주 세 종목이며 이번 배포가 custody를 흡수하거나 주문을 생성하지 않았다.

현재 main PID363990과 변경 파일을 사용하지 않는 장기 collector/notifier PID는 중단하지 않았다. main은 이전 R2 root를 계속 소비하고, 장후·다음 예약 및 future machine start는 새 선택 root를 사용한다. 이를 새 PID 소비로 재라벨링하지 않는다.

## 남은 자연 확인

배포 뒤 목표 주문이 열린 widget/episode가 없어 `holding_target_decision_audit` 신규 행은 0이다. 다음 자연 목표가 평가에서 로컬 0.5초 수량·목표가 touch·executable bid·비용 guard·원천 hash 입력행과 최종 주문 결과를 대사한다. 표본 생성을 위한 주문·threshold 완화·기계 조기 기동은 하지 않는다.
