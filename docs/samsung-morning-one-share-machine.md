# 삼성전자 오전 1주 독립 매매기계

## 결정

- 기존 KORStockScan 진입·보유·청산·ADM/LDM·AI·수량결정 로직과 분리한 전용 상태기계를 사용한다.
- 하루 실제 체결은 `005930` 1주 왕복 1회로 제한한다. NXT가 우선이고 NXT 미체결 주문의 취소·미체결이 계좌조회로 확인된 뒤에만 KRX 주문을 허용한다.
- 사용자의 2026-08-12 실운용 지시에 따라 전용 systemd timer로 예약한다. 기존 widget 자동매매는 중지·필터링·재기동하지 않고 자체 판단으로 계속 거래한다.

고정 정책은 다음과 같다.

| 순서 | 시장 | 기준가 | 매수가 | 주문 종료 |
|---:|---|---|---|---|
| 1 | NXT | 08:00 첫 1분봉 시가 | 기준가 대비 -3.0%, 유효 호가 내림 | 08:10 |
| 2 | KRX | 09:00 첫 1분봉 시가 | 기준가 대비 -0.75%, 유효 호가 내림 | 09:30 |

체결 후 실제 체결가에서 +2호가 지정가 매도를 낸다. 12분 동안 체결되지 않으면 목표 주문을 취소·확인한 뒤 동일 시장 최우선 지정가 1주 매도로 종료한다.

## 추가 1개월 분석

키움 공식 `ka10080` 연속조회로 2026-05-06~2026-08-10 자료를 확인했다. KRX 24,868봉·66거래일, NXT 45,320봉·66거래일을 확보했고, 두 시장의 필수 시가 봉이 모두 존재한 64일만 분석했다. 2026-06-08과 2026-07-31은 KRX 09:00 봉이 없어 제외했다.

판정 규칙은 매수 분봉의 `low <= 지정가`를 체결 가능으로 보고, 같은 분봉의 고가는 시간 순서를 알 수 없어 매도 성공으로 쓰지 않았다. 목표가는 반드시 다음 분봉 이후 12분 안의 `high >= 목표가`로 판정했다. 체결가는 지정가로 가정했으며 주문대기열, BBO, 분봉 내부 체결 순서와 실제 수수료·세금은 재구성하지 않았다.

| 기간 | 권한 | 유효일 | 진입 | +2호가 도달 | 일 기준 성공률 | 조건부 도달률 | 평균 총수익률 | 비용 0.20% 가정 후 평균 | 중앙 도달시간 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-06~06-04 | archive/audit only | 20 | 14 | 14 | 70.00% | 100.00% | 0.3512% | 0.1512% | 1분 |
| 2026-06-05~08-10 | clean baseline | 44 | 35 | 35 | 79.55% | 100.00% | 0.3576% | 0.1576% | 1분 |
| 전체 참고 | 혼합, live 근거 금지 | 64 | 49 | 49 | 76.56% | 100.00% | 0.3558% | 0.1558% | 1분 |

`+1호가`는 두 기간 모두 도달률 100%였지만 비용 0.20% 가정 후 평균이 clean -0.0212%, archive -0.0244%였다. `+3호가`는 clean 91.43%, archive 92.86%로 도달 안정성이 낮아졌다. 따라서 큰 수익보다 비용 여유와 반복성을 우선하는 현재 목적에는 `+2호가`가 가장 균형적이다.

추가 월의 2026-05-26 NXT 08:00 봉은 297,000원 시가, 240,000원 저가, 거래량 227주이고 다음 봉은 08:04에 시작해 297,000원 이상으로 복귀했다. 지정가 체결을 288,000원으로 가정할 때 분봉상 최대 불리폭은 -16.67%다. 이는 +2호가 도달 여부와 별개로 NXT 초기 유동성·분봉 순서 위험이 매우 크다는 증거이며, 1주 상한과 12분 종료를 없애면 안 된다.

## 지표 계약

- `metric_role`: counterfactual morning-pattern robustness research
- `decision_authority`: clean-baseline policy evidence; pre-baseline rows are archive/audit only
- `window_policy`: one NXT-first/KRX-fallback round trip per complete common trading date
- `sample_floor`: at least 60 common complete dates; observed 64
- `primary_decision_metric`: `equal_weight_avg_profit_pct`, with successful-day and conditional target-hit rates as diagnostics
- `source_quality_gate`: valid unique completed 1-minute OHLCV, exact NXT 08:00 and KRX 09:00 anchors, next-bar-or-later exit label
- `forbidden_uses`: queue-fill proof, real execution-quality approval, pre-baseline live promotion, provider/bot/cap/hard-safety change

## 독립성과 안전 경계

전용 구현은 [package](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share) 아래에 있다. 기존 전략에서 공유하는 것은 전략 판단이 아니라 다음 인프라·안전 경계뿐이다.

- 캐시된 키움 인증 토큰 읽기. 발급·갱신·폐기 금지.
- 공식 KRX 호가단위 계산.
- 전역 신규매수 중단 veto.
- `005930`이 메인 봇의 명시적 `manual_operator` 제외 대상인지 확인한다. 이는 메인 봇과의 주문권 경계이며 독립 widget 자동매매를 막지 않는다.

전용 기계와 widget은 같은 계좌에서 동시에 `005930`을 거래할 수 있지만 서로의 장부를 공유하지 않는다. 전용 기계는 자기 상태 파일에 기록한 broker 주문번호의 체결만 조회하고 그 체결수량 1주만 매도·취소한다. widget 역시 자기 episode/order ledger만 소유한다. 계좌의 삼성전자 총보유수량이나 상대 전략의 주문은 어느 한쪽의 매도수량·취소대상이 아니며, 상대 주문의 존재를 신규진입 차단 사유로 쓰지 않는다.

모든 broker write 전에 intent를 원자적으로 기록한다. 호출 중 프로세스가 끊긴 상태에서는 자동 재주문하지 않고 `broker_write_interrupted`로 차단한다. 전일 주문이나 보유 1주가 해결되지 않은 상태에서도 다음 날 신규매수를 금지한다.

키움 공식 참조는 `Kiwoom-Securities/Kiwoom-REST-API` commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`이며, `주문.md`, `계좌.md`, `차트.md`, API spec, Postman을 2026-08-11 10:16:56 KST에 대조했다. 사용 API는 `ka10080`, `kt10000`, `kt10001`, `kt10003`, `kt00007`뿐이다.

## 2026-08-12 기동 설정

실주문은 다음 네 조건이 동시에 있어야 코드상 가능하다.

1. `KORSTOCKSCAN_SAMSUNG_MORNING_ONE_SHARE_ENABLED=true`
2. CLI `--live --confirm 005930_ONE_SHARE_LIVE`
3. `005930`의 명시적 `manual_operator` 제외 소유권
4. 당일 07:57 PREOPEN 점검에서 생성한 `data/runtime/samsung_morning_one_share_authority.json`

`korstockscan-samsung-one-share-preflight.timer`는 평일 07:57에 메인 봇 tmux, 공유 캐시 토큰, 메인 봇 제외 소유권을 확인한다. 통과한 당일에만 `korstockscan-samsung-morning-one-share.timer`가 07:59부터 전용 기계를 시작한다. 두 timer는 `Persistent=false`라 설치 시각에 이미 지난 당일 작업을 소급 실행하지 않는다.

전용 기계는 `COMPLETE`, `NO_TRADE`, `BLOCKED`에서 종료한다. 실패 재시작도 당일 권한 artifact와 원자적 write-intent 상태를 다시 검증하므로 모호한 broker write를 반복하지 않는다. 전용 기계 문제가 생기면 다음 unit만 중지하며 widget unit에는 손대지 않는다.

```bash
sudo systemctl disable --now korstockscan-samsung-morning-one-share.timer korstockscan-samsung-one-share-preflight.timer
sudo systemctl stop korstockscan-samsung-morning-one-share.service korstockscan-samsung-one-share-preflight.service
```
