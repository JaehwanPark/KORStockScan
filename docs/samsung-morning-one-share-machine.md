# 삼성전자 오전 2-leg 독립 매매기계

## 결정

- 기존 KORStockScan 진입·보유·청산·ADM/LDM·AI·수량결정 로직과 분리한 전용 상태기계를 사용한다.
- 하루 신규 매수 episode는 `005930` 1회이며, 각각 1주인 두 주문으로 고정한다. NXT PREMARKET이 우선이고 각 NXT leg의 취소·미체결이 계좌조회로 확인된 뒤에만 그 leg의 09:00 SOR 통합 주문을 허용한다. 기존 package/unit 파일명은 호환성을 위해 유지한다.
- 사용자의 2026-08-12 실운용 지시에 따라 전용 systemd timer로 예약한다. 기존 widget 자동매매는 중지·필터링·재기동하지 않고 자체 판단으로 계속 거래한다.

고정 정책은 다음과 같다.

| 순서 | 시장 | 기준가 | 매수가 | 주문 종료 |
|---:|---|---|---|---|
| 1 | NXT PREMARKET | 08:00 첫 1분봉 시가 | 1주: 기준가 대비 -3.0% base, 1주: base +1호가 | 08:10 |
| 2 | SOR 정규장 | KRX 09:00 첫 1분봉 시가를 가격 기준점으로 사용 | NXT 미체결 leg별 1주: -0.75% base 또는 base +1호가 | 09:30 |

각 leg 체결 후 그 실제 체결가에서 +2호가 1주 지정가 매도를 별도로 낸다. 목표 주문에는 시간청산과 손절이 없다. 주문이 열려 있는 동안 계속 체결을 확인하고, 브로커에서 미체결 종료된 것이 확인되면 해당 1주를 그대로 보유한다. 하나만 체결되거나 하나만 목표 청산돼도 다른 leg의 주문·보유 귀속은 독립적으로 유지한다. 목표 주문 취소, 최우선 지정가 강제매도, 다음 날 자동 목표 재주문, 보유 중 신규 episode는 하지 않는다.

09:00 이후 `SOR`는 주문 라우트다. `ka10080`의 기본 `005930` 09:00 봉은 정규장 가격 기준점으로만 사용하며, 이를 SOR 통합 체결 스트림이라고 해석하지 않는다.

## 추가 1개월 분석

키움 공식 `ka10080` 연속조회로 2026-05-06~2026-08-10 자료를 확인했다. KRX 24,868봉·66거래일, NXT 45,320봉·66거래일을 확보했고, 두 시장의 필수 시가 봉이 모두 존재한 64일만 분석했다. 2026-06-08과 2026-07-31은 KRX 09:00 봉이 없어 제외했다.

판정 규칙은 매수 분봉의 `low <= 지정가`를 체결 가능으로 보고, 같은 분봉의 고가는 시간 순서를 알 수 없어 매도 성공으로 쓰지 않았다. 기존 비교에서는 목표가가 다음 분봉 이후 12분 안에 도달했는지도 관측했다. 이는 과거 도달시간 진단값일 뿐 현재 runtime의 청산 제한이 아니다. 체결가는 지정가로 가정했으며 주문대기열, SOR 라우팅/BBO, 분봉 내부 체결 순서와 실제 수수료·세금은 재구성하지 않았다.

| 기간 | 권한 | 유효일 | 진입 | +2호가 도달 | 일 기준 성공률 | 조건부 도달률 | 평균 총수익률 | 비용 0.20% 가정 후 평균 | 중앙 도달시간 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-06~06-04 | archive/audit only | 20 | 14 | 14 | 70.00% | 100.00% | 0.3512% | 0.1512% | 1분 |
| 2026-06-05~08-10 | clean baseline | 44 | 35 | 35 | 79.55% | 100.00% | 0.3576% | 0.1576% | 1분 |
| 전체 참고 | 혼합, live 근거 금지 | 64 | 49 | 49 | 76.56% | 100.00% | 0.3558% | 0.1558% | 1분 |

`+1호가`는 두 기간 모두 도달률 100%였지만 비용 0.20% 가정 후 평균이 clean -0.0212%, archive -0.0244%였다. `+3호가`는 clean 91.43%, archive 92.86%로 도달 안정성이 낮아졌다. 따라서 큰 수익보다 비용 여유와 반복성을 우선하는 현재 목적에는 `+2호가`가 가장 균형적이다.

추가 월의 2026-05-26 NXT 08:00 봉은 297,000원 시가, 240,000원 저가, 거래량 227주이고 다음 봉은 08:04에 시작해 297,000원 이상으로 복귀했다. 지정가 체결을 288,000원으로 가정할 때 분봉상 최대 불리폭은 -16.67%다. 이는 +2호가 도달 여부와 별개로 NXT 초기 유동성·분봉 순서 및 무손절 보유 위험이 매우 크다는 증거다. 사용자의 명시적 무손절·미청산 보유 원칙을 적용하되 총 2주·leg당 1주 상한을 유지한다.

진입가 재평가에 따라 기존 base 지정가만으로 아랫꼬리 반등을 놓치는 위험을 줄이기 위해 `base+1호가` 실행확률 leg를 추가했다. 과거 분봉의 `low <= 지정가`는 가격 touch만 보여 주며 주문대기열 체결을 증명하지 않으므로 두 leg 성과는 runtime에서 별도 귀속한다.

## 지표 계약

- `metric_role`: counterfactual morning-pattern robustness research
- `decision_authority`: clean-baseline policy evidence; pre-baseline rows are archive/audit only
- `window_policy`: at most one two-leg NXT-premarket-first/SOR-regular-fallback entry episode per trading date; each unfilled target becomes held inventory
- `sample_floor`: at least 60 common complete dates; observed 64
- `primary_decision_metric`: `equal_weight_avg_profit_pct`, with successful-day and conditional target-hit rates as diagnostics
- `source_quality_gate`: valid unique completed 1-minute OHLCV, exact NXT 08:00 and KRX 09:00 anchors, next-bar-or-later exit label
- `forbidden_uses`: queue-fill or SOR-routing proof, real execution-quality approval, pre-baseline live promotion, provider/bot/cap/hard-safety change

## 독립성과 안전 경계

전용 구현은 [package](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share) 아래에 있다. 기존 전략에서 공유하는 것은 전략 판단이 아니라 다음 인프라·안전 경계뿐이다.

- 캐시된 키움 인증 토큰 읽기. 발급·갱신·폐기 금지.
- 공식 KRX 호가단위 계산.
- 전역 신규매수 중단 veto.
- `005930`이 메인 봇의 명시적 `manual_operator` 제외 대상인지 확인한다. 이는 메인 봇과의 주문권 경계이며 독립 widget 자동매매를 막지 않는다.

전용 기계와 widget은 같은 계좌에서 동시에 `005930`을 거래할 수 있지만 서로의 장부를 공유하지 않는다. 전용 기계는 자기 상태 파일의 leg별 broker 주문번호만 조회하고 해당 체결수량 1주만 매도·취소한다. 두 leg 사이에도 주문번호·체결·목표가·보유수량을 합치지 않는다. widget 역시 자기 episode/order ledger만 소유한다. 계좌의 삼성전자 총보유수량이나 상대 전략의 주문은 어느 한쪽의 매도수량·취소대상이 아니며, 상대 주문의 존재를 신규진입 차단 사유로 쓰지 않는다.

모든 broker write 전에 intent를 원자적으로 기록한다. 호출 중 프로세스가 끊긴 상태에서는 자동 재주문하지 않고 `broker_write_interrupted`로 차단한다. 전일 목표 주문이나 보유 1주가 남아 있으면 다음 날 신규매수를 금지한다. 목표 주문이 전일 이후에도 브로커에서 열려 있으면 원주문일 기준으로 계속 조회하고, 미체결 종료가 확인되면 자동 매도 없이 `HELD`로 닫는다.

키움 공식 참조는 `Kiwoom-Securities/Kiwoom-REST-API` commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`이며, `kiwoom_docs/주문.md`, `계좌.md`, `차트.md`, `kiwoom/specs.py`, API spec, Postman을 2026-08-11 15:30:19 KST에 다시 대조했다. 공식 `kt10000/kt10001/kt10003/kt00007` 계약의 `dmst_stex_tp`가 `SOR`를 지원함을 확인했다. 사용 API는 `ka10080`, `kt10000`, `kt10001`, `kt10003`, `kt00007`뿐이다.

## 2026-08-12 기동 설정

실주문은 다음 네 조건이 동시에 있어야 코드상 가능하다.

1. `KORSTOCKSCAN_SAMSUNG_MORNING_ONE_SHARE_ENABLED=true`
2. CLI `--live --confirm 005930_MORNING_TWO_LEG_LIVE`
3. `005930`의 명시적 `manual_operator` 제외 소유권
4. 당일 07:57 PREOPEN 점검에서 생성한 `data/runtime/samsung_morning_one_share_authority.json`

`korstockscan-samsung-one-share-preflight.timer`는 평일 07:57에 메인 봇 tmux, 공유 캐시 토큰, 메인 봇 제외 소유권을 확인한다. 통과한 당일에만 `korstockscan-samsung-morning-one-share.timer`가 07:59부터 전용 기계를 시작한다. 두 timer는 `Persistent=false`라 설치 시각에 이미 지난 당일 작업을 소급 실행하지 않는다.

전용 기계는 `COMPLETE`, `NO_TRADE`, `HELD`, `BLOCKED`에서 종료한다. `HELD`는 하나 이상의 목표가 매도가 체결되지 않아 해당 leg를 그대로 보유하는 정상 종결 상태다. 실패 재시작도 당일 권한 artifact와 원자적 write-intent 상태를 다시 검증하므로 모호한 broker write를 반복하지 않는다. active legacy 1주 상태와 leg 간 주문번호 충돌은 자동 이관하지 않고 차단한다. 전용 기계 문제가 생기면 다음 unit만 중지하며 widget unit에는 손대지 않는다.

이번 변경은 source와 배포 unit 정의만 갱신했다. 기존 설치 unit은 새 confirmation 계약과 다르므로 자동으로 재기동하지 않으며, 코드리뷰 종료 후 별도 명시적 설치·기동 단계가 필요하다.

## 장후 진입 기준 누적 관찰

라이브 episode가 arm될 때 state의 `signal_features`에 NXT/SOR route, 실제 opening price, 적용 drawdown, 진입창, 두 leg 지정가와 +2호가 정책을 고정한다. 20:10 `samsung_machine_entry_tuning` report는 당일 state와 자기 이전 일별 report만 읽으며 시세나 과거 원천을 재조회하지 않는다. 실제 주문·체결·목표 결과만 leg별로 누적하고 주문번호와 audit는 복사하지 않는다. 오전은 route별 현재 drawdown 정책의 실제 결과만 관찰하며, 신호가 없던 날의 미관측 가격을 이용한 완화 threshold 반사실은 만들지 않는다.

report 자체는 `runtime_effect=false`, `allowed_runtime_apply=false`이고, clean v2 complete episode/leg 표본, source-quality preflight, rolling/cumulative EV, `HELD`·열린 주문 guard를 통과한 결과만 다음 PREOPEN candidate로 넘긴다. 오전은 관찰된 대안 정책이 없으므로 현재 NXT 3.0%·SOR 0.75% baseline만 carry-forward한다.

preflight wrapper는 정확일자 applied artifact를 먼저 생성하고 service는 schema/hash가 검증된 오전 policy만 읽는다. 후보 없음/기간 만료는 baseline으로 닫고, 최신 후보 또는 이미 생성된 당일 artifact가 손상되면 broker gateway 생성 전에 기동을 차단한다. 당일 유효 artifact는 덮어쓰지 않고 재사용한다. 무손절·미청산 보유, leg별 1주 두 개, +2호가, 독립 주문원장, provider/bot/cap/broker guard는 튜닝 축이 아니다.

```bash
sudo systemctl disable --now korstockscan-samsung-morning-one-share.timer korstockscan-samsung-one-share-preflight.timer
sudo systemctl stop korstockscan-samsung-morning-one-share.service korstockscan-samsung-one-share-preflight.service
```
