# 분할진입 후 틱 급변동 소프트손절 분석 및 대응방안

작성일: 2026-04-17  
분석 범위: `2026-04-16 ~ 2026-04-17`, 메인(local) + 원격(remote)  
분석 기준: `분할진입 이후(stage=position_rebased_after_fill/holding_started 복수)`에 `exit_rule=scalp_soft_stop_pct`로 종료된 케이스만 집계  
원격 데이터 수집 방식: `fetch_remote_scalping_logs` 표준 경로로 원격 `pipeline_events_2026-04-17.jsonl` 및 noon snapshot을 확보해 로컬과 동일 휴리스틱으로 재집계

---

## 1. 판정

1. `2026-04-16`는 메인에서만 `분할진입 후 soft stop`이 4건 확인됐고, 원격은 동일 기준 표본이 0건이다.
2. `2026-04-17 12:00` 스냅샷 이후 재집계 기준으로 메인 16건, 원격 7건까지 늘었다. 오늘은 `partial 이후 확대 -> soft stop`이 메인 13/16, 원격 6/7로 주 패턴이다.
3. 메인 `2026-04-17`에서는 정합성 플래그 보유 케이스가 10건까지 늘었다. 분포는 `cum_gt_requested=9`, `same_ts_multi_rebase=8`, `requested0_unknown=2`다. 이 코호트는 손절 임계값 튜닝 전에 `rebase quantity 정합성` shadow 감사가 선행돼야 한다.
4. 기대값 관점에서 첫 대응축은 `전역 soft stop 강화`가 아니라 `분할진입 직후 bad scale-up 억제`가 맞다. 특히 `즉시/단계적 fallback 확대`와 `동일 종목 반복 재진입`을 먼저 줄여야 한다.

---

## 2. 근거

### 2-1. 날짜/서버별 집계 요약

| 날짜 | 서버 | 분할진입 후 soft stop | partial 후 확대 | partial-only 유지 | held <= 180s | 정합성 이상 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2026-04-16 | 메인 | 4 | 1 | 3 | 2 | 0 |
| 2026-04-16 | 원격 | 0 | 0 | 0 | 0 | 0 |
| 2026-04-17 | 메인 | 16 | 13 | 3 | 11 | 10 |
| 2026-04-17 | 원격 | 7 | 6 | 1 | 3 | 0 |

해석:
- `2026-04-16`는 `1주 partial만 남긴 채 soft stop`이 중심이었다.
- `2026-04-17`는 메인/원격 공통으로 `partial 이후 scale-up`이 중심으로 바뀌었다.
- noon 이후 표본까지 합치면 메인은 `빛과전자`, 원격은 `코미팜`에서 same-symbol repeat도 새로 확인됐다.
- 메인 `2026-04-17`은 손절 표본이 늘었을 뿐 아니라 `재산정 로그 정합성`도 같이 흔들렸다.

### 2-1-b. `2026-04-17 12:00` 이후 재집계 보정

`pipeline_events_2026-04-17.jsonl` 기준 재집계 결과:

- 메인:
  - 분할진입 soft stop `16건`
  - `partial 이후 확대` `13건`
  - `partial-only` `3건`
  - `held<=180s` `11건`
  - expanded-after-partial 중 `peak_profit<=0` `4건`
  - expanded-after-partial 중 `peak_profit<0.2` `8건`
  - same-symbol repeat: `빛과전자 2회`
- 원격:
  - 분할진입 soft stop `7건`
  - `partial 이후 확대` `6건`
  - `partial-only` `1건`
  - `held<=180s` `3건`
  - expanded-after-partial 중 `peak_profit<=0` `3건`
  - expanded-after-partial 중 `peak_profit<0.2` `5건`
  - same-symbol repeat: `코미팜 2회`

메모:

- 아래 종목별 대표 표본 표는 오전 스냅샷 기준 대표 케이스 설명용으로 유지한다.
- 최신 운영 판정과 후속 액션은 `docs/2026-04-17-noon-followup-auditor-report.md`를 우선 기준으로 본다.

### 2-2. 메인 `2026-04-16` 표본

패턴 라벨:
- `A`: partial 직후 수초 내 fallback/bulk 확대 후 soft stop
- `B`: partial-only 또는 소량 보유 상태로 유지 후 soft stop
- `C`: 단계적 fallback 확대 후 soft stop
- `D`: rebase quantity 정합성 이상 동반

| id | 종목 | 패턴 | held_sec | exit% | 비고 |
| --- | --- | --- | ---: | ---: | --- |
| 2507 | 지투파워(388050) | A | 73 | -1.50 | `1 -> 84` 확대 후 56초 내 매도 완료 `-1.56%` |
| 2508 | 지투파워(388050) | B | 140 | -1.66 | 1주 partial만 보유한 채 soft stop |
| 2520 | 지투파워(388050) | B | 631 | -1.57 | 같은 종목 재진입 후 재차 soft stop |
| 2403 | 파미셀(005690) | B | 6181 | -1.51 | 장시간 표류 후 soft stop |

핵심:
- `지투파워`가 같은 날 3회 반복 손절됐다. `동일 종목 재진입 억제 부재`가 직접 손실로 연결됐다.
- 아직은 `partial-only 표류` 비중이 높아서 timeout/취소 계열 대응도 의미가 있다.

### 2-3. 원격 `2026-04-16` 표본

- 동일 기준(`분할진입 이력 + soft stop`)에서는 0건.
- 원격 `2026-04-16` 전체 거래수는 30건이지만, 이 코호트는 메인 전용 현상이었다.
- 따라서 `2026-04-16` 기준으로는 메인에서만 `same-symbol repeat` 문제가 두드러졌다.

### 2-4. 메인 `2026-04-17` 표본

| id | 종목 | 패턴 | held_sec | exit% | 비고 |
| --- | --- | --- | ---: | ---: | --- |
| 2579 | 인텔리안테크(189300) | A | 32 | -2.30 | `1 -> 9`, peak `-0.05%`, 매도 완료 `-2.03%` |
| 2602 | 코미팜(041960) | A+D | 170 | -2.04 | `20 -> 145`, `cum_filled_qty 145 > requested_qty 126`, 별도 매도실패 버그 이슈 존재 |
| 2616 | RF머트리얼즈(327260) | A | 133 | -1.55 | `1 -> 12`, 확대 후 2분 내 soft stop |
| 2632 | 디바이스(187870) | A | 37 | -1.96 | `1 -> 35`, peak `-0.23%`, 매도 완료 `-2.36%` |
| 2644 | 성호전자(043260) | C+D | 147 | -1.53 | `1 -> 5 -> 11 -> 18 -> 41`, `cum_filled_qty 41 > requested_qty 24` |
| 2634 | 이수스페셜티케미컬(457190) | C+D | 260 | -1.55 | `1 -> 8 -> 17 -> 27`, `requested_qty=0/UNKNOWN` 잔존 |
| 2599 | 현대무벡스(319400) | B | 797 | -1.62 | partial-only 1주 유지, peak `-0.23%` |
| 2606 | AP위성(211270) | C+D | 184 | -1.54 | `1 -> 26 -> 80 -> 151`, `cum_filled_qty 80 > requested_qty 72` |
| 2649 | 더블유씨피(393890) | C+D | 523 | -1.72 | `1 -> 67 -> 145`, `cum_filled_qty 145 > requested_qty 79` |
| 2631 | 아주IB투자(027360) | A | 104 | -1.54 | `1 -> 109`, 확대 직후 2분 내 soft stop |

핵심:
- 오늘 메인은 `partial-only`보다 `확대 후 급락`이 중심이다.
- `held <= 180s`가 11/16으로, 첫 3분 안에 손실이 확정되는 표본이 과반이다.
- `peak_profit < 0` 또는 거의 0인 상태에서 확대가 이루어진 케이스가 적지 않다.
- 특히 `cum_filled_qty > requested_qty`가 섞여 있어, 이 표본 일부는 경제 현상과 이벤트 복원 이슈가 같이 들어 있다.

### 2-5. 원격 `2026-04-17` 표본

| id | 종목 | 패턴 | held_sec | exit% | 비고 |
| --- | --- | --- | ---: | ---: | --- |
| 1012 | 대한광통신(010170) | B | 56 | -2.05 | partial-only 1주 상태로 56초 내 soft stop |
| 1076 | 코미팜(041960) | A | 306 | -1.66 | API 상 `partial -> fallback holding_started` 흔적 확인 |
| 1023 | 더블유씨피(393890) | A | 559 | -1.55 | `1 -> 9` fallback 확대 후 soft stop |
| 1077 | 아주IB투자(027360) | A | 24 | -1.37 | `1 -> 11`, 매우 짧은 보유 후 soft stop |
| 1014 | 에이치엠넥스(036170) | A | 226 | -1.70 | `1 -> 18`, 확대 후 4분 내 soft stop |

핵심:
- 원격도 오늘은 `partial 이후 확대`가 주 패턴이다.
- 메인/원격 공통 종목은 `코미팜`, `더블유씨피`, `아주IB투자`다. 따라서 오늘 패턴은 메인 전용 잡음이 아니라 공통 운영 이슈에 가깝다.
- 다만 메인에서 보인 `rebase quantity 이상`은 원격 API 응답 기준으로는 복원되지 않았다.

### 2-6. 구조적 해석

1. `2026-04-16` 문제의 핵심은 `partial-only 표류`와 `동일 종목 재진입 반복`이다.
2. `2026-04-17` 문제의 핵심은 `partial 이후 fallback 확대`다. 손절선 자체보다 `나쁜 구간에서 포지션이 커지는 구조`가 기대값을 더 많이 훼손한다.
3. 메인 `2026-04-17`의 일부 표본은 `rebase quantity` 복원 이상을 같이 포함하므로, 이 데이터를 바로 손절 임계값 튜닝 근거로 쓰면 위험하다.
4. `AI threshold`만 강화하는 것은 우선순위가 아니다. 오늘 손절 표본에는 `AI 58/64/69`처럼 낮지 않은 값도 포함되어 있어, 본질은 `틱 급변 + 확대 타이밍`에 더 가깝다.

---

## 3. 대응 방안

### 3-1. 우선순위 1: `rebase quantity 정합성 shadow 감사`

목적:
- 메인 `2026-04-17`의 `cum_filled_qty > requested_qty`, `requested_qty=0 + UNKNOWN` 케이스를 분리해 `경제 손실`과 `이벤트 복원 오류`를 혼합하지 않게 한다.

권고:
- 다음 축 튜닝 전에 `split_entry_rebase_integrity_shadow`를 먼저 둔다.
- shadow 항목은 최소 아래를 기록한다.

```text
requested_qty
cum_filled_qty
remaining_qty
fill_quality
entry_mode
buy_qty_after_rebase
same_ts_multi_rebase_count
```

판정 기준:
- `requested_qty < cum_filled_qty`
- `requested_qty == 0 and fill_quality == UNKNOWN`
- 동일 초(`same_ts`) 다중 rebase로 누적수량이 비상식적으로 점프

이유:
- 이 감사가 먼저 끝나야 `soft stop`, `size cap`, `cooldown` 중 어느 축이 실제 기대값 개선축인지 방어할 수 있다.

### 3-2. 우선순위 2: `partial -> fallback 확대 직후 즉시 재평가` shadow

목적:
- 오늘 메인 16건 중 13건, 원격 7건 중 6건이 `확대 후 급락`이다. 먼저 막아야 할 것은 손절 임계값이 아니라 `나쁜 확대`다.

권고:
- `partial_fill 이후 hold_count>=2` 또는 `rebase_count>=2`가 되면 즉시 1회 재평가를 실행하는 shadow 축을 둔다.
- 첫 `90초`는 별도 코호트로 본다.

관찰 지표:
- 확대 직후 `5초/10초` 수익률
- 확대 후 `held<=180s` soft stop 비중
- 확대 직후 `peak_profit < 0` 지속 비율
- 조기 차단 시 5분 후 missed upside

이유:
- 전역 손절 강화는 승자도 같이 자르지만, `확대 직후 재평가`는 문제 코호트만 겨냥한다.

### 3-3. 우선순위 3: `동일 종목 soft stop 재진입 cooldown` shadow

목적:
- `2026-04-16 지투파워`처럼 같은 종목을 같은 날 반복 손절하는 누수를 막는다.

권고:
- `split-entry soft stop` 발생 종목에 한해 `20~30분 cooldown` shadow를 둔다.
- 전체 종목 일괄이 아니라 `동일 종목 + split-entry soft stop`에만 제한한다.

관찰 지표:
- same-symbol repeat soft stop 건수
- cooldown으로 차단된 재진입 수
- 차단 후 10분/30분 missed upside

이유:
- 반복 손절은 기대값을 거의 순수하게 깎는다. 먼저 막아도 upside 훼손이 상대적으로 작다.

### 3-4. 우선순위 4: `partial-only 표류` 전용 timeout/정리 shadow

대상:
- `파미셀`, `현대무벡스`, `대한광통신`, `지투파워 2508/2520`

권고:
- `partial-only` 상태가 `120~180초`를 넘고 `peak_profit <= 0`이면 별도 shadow 신호를 둔다.
- 이 축은 `확대 후 급락` 축과 분리해서 검증한다.

이유:
- `partial-only`는 확대 후 급락과 다른 코호트다. 같은 규칙으로 섞어 튜닝하면 왜곡된다.

### 3-5. 우선순위 5: `분할진입 코호트 한정 never-green 강화`

권고:
- 전 종목 공통 손절 강화는 보류한다.
- 대신 `split-entry` 코호트에서만 `peak_profit < 0` 또는 `peak_profit ≈ 0`이 유지되는 경우를 shadow로 따로 본다.

이유:
- 오늘 메인 표본 중 `인텔리안테크`, `디바이스`, `현대무벡스`, `더블유씨피`는 사실상 한 번도 의미 있는 녹색 구간을 만들지 못했다.
- 다만 이 축은 `rebase quantity 정합성` 문제가 먼저 정리된 뒤 적용해야 한다.

### 3-6. 비권고

1. 전역 `soft stop`을 일괄 강화하는 것
- 승자 훼손 범위가 넓고, 오늘 핵심 문제인 `bad scale-up`을 직접 겨냥하지 못한다.

2. `AI score` 기준만 올리는 것
- 실제 손절 표본에 `AI 58/64/69`도 포함되어 있다. AI alone 문제로 보기 어렵다.

3. full fill / partial fill / step fill을 한 코호트로 합치는 것
- 원인과 대응이 다르므로 분리 유지가 맞다.

---

## 4. 권고 실행 순서

1. `rebase quantity 정합성 shadow 감사`
2. `partial -> fallback 확대 직후 즉시 재평가` shadow
3. `동일 종목 split-entry soft stop cooldown` shadow
4. `partial-only 표류 timeout` shadow
5. 위 4개 결과를 본 뒤에만 `never-green 강화` 또는 실제 실전 canary 1축 승인

---

## 5. 후속 작업 항목

- [ ] `[Checklist0417] split-entry soft-stop rebase quantity 정합성 감사 기준 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`, `Track: ScalpingLogic`)
  - 판정 기준: `requested_qty/cum_filled_qty/remaining_qty/fill_quality` shadow 포맷과 이상 판정식이 문서화됨
  - 근거: 메인 `2026-04-17` 10건에서 rebase 정합성 이상 확인
  - 다음 액션: 이상 표본과 정상 표본을 분리해 후속 canary 입력으로 사용
- [ ] `[Checklist0417] split-entry soft-stop 즉시 재평가 shadow 설계 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:40`, `Track: ScalpingLogic`)
  - 판정 기준: `partial 이후 확대` 코호트에서만 동작하는 shadow 조건과 관찰 지표가 확정됨
  - 근거: 오늘 메인 16건 중 13건, 원격 7건 중 6건이 확대 후 soft stop
  - 다음 액션: 1축 shadow 반영 후 `held<=180s soft stop` 감소 여부 관찰
- [ ] `[Checklist0417] split-entry soft-stop 동일종목 cooldown shadow 여부 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:00`, `Track: ScalpingLogic`)
  - 판정 기준: cooldown 분(min)과 예외 조건이 확정됨
  - 근거: `2026-04-16` 지투파워 반복 손절
  - 다음 액션: 차단 건수와 missed upside를 같이 추적
- [ ] `[Checklist0417] split-entry partial-only timeout shadow 기준 확정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:50`, `Track: ScalpingLogic`)
  - 판정 기준: `partial-only` 전용 timeout 조건과 분리 리포트 포맷이 고정됨
  - 근거: `파미셀`, `현대무벡스`, `대한광통신`, `지투파워` 계열이 별도 코호트로 존재
  - 다음 액션: 확대형 코호트와 분리해 shadow 판정

---

## 6. 검증 / 재현 명령

```bash
# 메인 실로그 기준 soft stop + split-entry 코호트 추출
.venv/bin/python - <<'PY'
from pathlib import Path
import glob, re
line_re = re.compile(r'^\[(?P<ts>[^\]]+)\].*?\[HOLDING_PIPELINE\] (?P<name>.+?)\((?P<code>\d+)\) stage=(?P<stage>\S+) (?P<rest>.*)$')
PY

# 원격 구조화 응답 기준 복원
curl -fsSL 'https://songstockscan.ddns.net/api/trade-review?date=2026-04-17'

# 오늘 메인 실로그에서 대표 케이스 확인
rg -n "id=2579|id=2602|id=2616|id=2632|id=2644|id=2634|id=2599|id=2606|id=2649|id=2631" logs/pipeline_event_logger_info.log -S
```

검증 결과:
- 메인 `2026-04-16`: 4건
- 원격 `2026-04-16`: 0건
- 메인 `2026-04-17`: 16건
- 원격 `2026-04-17`: 7건
- 메인 `2026-04-17` rebase 정합성 이상: 10건
- 원격 데이터는 `fetch_remote_scalping_logs` 확보본 기준 재집계
