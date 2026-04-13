# 시스템운영자 전달용 추가 검토 메모

## 목적

- `부적합`으로 분류했던 제안들에 대한 추가 전문가 의견을, 현재 코드베이스와 운영 원칙 기준으로 다시 비판적으로 검토한다.
- 각 사안은 `10점 척도 적합도`로 판정한다.
- `7점 이상`인 항목만 플랜 수정에 반영한다.

## 판정 원칙

- 기준:
  - `기대값/순이익 극대화`
  - `계측 먼저 -> 원격 단일축 실험 -> 본서버 후행 반영`
  - `현재 코드에 이미 있는 기능은 신규 과제로 과장하지 않음`
  - `다축 변경`과 `범위 과잉`은 감점

## 점수표

| 사안 | 적합도(10) | 판정 | 플랜 반영 |
| --- | --- | --- | --- |
| 기존 관리자 채널에 `rate-limit` 디버그 알림 추가 | `4` | 지금은 구조화 로그가 우선 | `반영 안 함` |
| `latency` 이유 분포 강화 + `remote_v2 vs local` 비교계측 강화 | `8` | 이미 맞는 방향이며 즉시성 높음 | `반영` |
| 원격 경량 프로파일링(`cProfile` 등 표준 도구 중심) | `7` | root cause 단정은 금지지만 관측은 가치 있음 | `반영` |
| `min_fill_ratio` / `cancel_remaining_fast` 원격 canary 즉시 착수 | `6` | partial fill 증거는 있으나 아직 sync mismatch 선행이 우선 | `반영 안 함` |
| 스캘핑 live hard stop 로직 존재 여부 코드 감사 | `9` | 실제로 live hard stop 계열이 있어 taxonomy 정리가 필요 | `반영` |
| `AI overlap audit` 이번 주 즉시 착수 | `8` | 범위 작고 기대효과 큼 | `이미 반영됨` |
| `ai_confirmed score vs realized return` 모니터링 추가 | `6` | 유용하지만 현 단계 최우선은 아님 | `반영 안 함` |

## 사안별 검토

### 1. 기존 관리자 채널에 rate-limit 디버그 알림 추가

- 점수: `4/10`
- 판정:
  - 추가 전문가 의견의 취지는 이해되지만, 지금 부족한 것은 채널이 아니라 `latency_block 세부 판정근거`, `preset_exit_sync_mismatch`, `exit_decision_source` 같은 구조화 데이터다.
  - 현재 코드에는 이미 `TELEGRAM_BROADCAST`, `TELEGRAM_ADMIN_NOTIFY`, `buy_pause_guard`, `entry_metrics`가 있다.
- 결론:
  - `7점 미만`, 플랜 반영 안 함

### 2. `latency` 이유 분포 + `remote_v2 vs local` 비교계측 강화

- 점수: `8/10`
- 판정:
  - 이 항목은 기존 플랜과도 정합적이다.
  - `quote_stale=False` 코호트, `ws_age/ws_jitter/spread/slippage`, `decision reason`, `submitted/holding_started` 전환을 같이 봐야 한다.
- 결론:
  - `7점 이상`, 플랜 반영

### 3. 원격 경량 프로파일링

- 점수: `7/10`
- 판정:
  - `quote_stale=False`만으로 내부 처리 지연을 확정할 수는 없다.
  - 하지만 `root cause 단정`과 `관측 착수`는 다르다.
  - 패키지 설치 없이 가능한 `cProfile`이나 OS 기본 sampling 수준의 경량 프로파일링은 원격 관측축으로 적합하다.
- 결론:
  - `7점 이상`, 단 `원격 전용/관측 전용`으로만 반영

### 4. `min_fill_ratio` / `cancel_remaining_fast` 원격 canary 즉시 착수

- 점수: `6/10`
- 판정:
  - partial fill 음수 기여는 중요하다.
  - 다만 현재 코드에는 partial/full fill 누적 처리와 preset TP 재발행이 이미 있어, 먼저 `sync mismatch`를 계측해야 한다.
  - `min_fill_ratio`와 `cancel_remaining_fast`는 아직 코드 흔적이 없어, 지금 바로 넣으면 관측과 실험이 한 번에 섞인다.
- 결론:
  - `7점 미만`, 플랜 반영 안 함
  - 계속 `계측 후 후보 실험`으로 유지

### 5. 스캘핑 live hard stop 로직 존재 여부 코드 감사

- 점수: `9/10`
- 판정:
  - `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=True`는 맞지만, 코드에는 별도로 live exit 성격의 `scalp_preset_hard_stop_pct`, `scalp_hard_stop_pct`, `protect_hard_stop`가 존재한다.
  - 따라서 “common hard time stop은 shadow-only”라는 문장만으로 청산 구조를 설명하면 불완전하다.
- 결론:
  - `7점 이상`, 플랜 반영

### 6. `AI overlap audit` 이번 주 즉시 착수

- 점수: `8/10`
- 판정:
  - OpenAI 실시간 입력에는 이미 `latest_strength`, `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct`가 포함된다.
  - 따라서 `AI가 이미 본 것과 후단 필터가 다시 막는 것`을 감사하는 작업은 범위 대비 가치가 높다.
- 결론:
  - `7점 이상`
  - 이미 플랜에 반영되어 있어 추가 수정은 최소화

### 7. `ai_confirmed score vs realized return` 모니터링 추가

- 점수: `6/10`
- 판정:
  - 장기적으로는 유효하다.
  - 그러나 현재는 `latency`, `partial fill sync`, `AI overlap`이 더 직접적인 병목이다.
- 결론:
  - `7점 미만`, 이번 플랜 반영 안 함

## 이번 판정으로 실제 반영하는 플랜 수정

### 반영 대상 (`>=7`)

1. `latency reason breakdown`과 `remote_v2 vs local` 비교계측 강화
2. 원격 경량 프로파일링 추가
3. 스캘핑 live hard stop taxonomy audit 추가
4. `AI overlap audit`는 즉시 착수 항목으로 유지

### 비반영 대상 (`<7`)

1. 관리자 디버그 텔레그램 추가
2. `min_fill_ratio` / `cancel_remaining_fast` 원격 canary 즉시 착수
3. `ai_confirmed score vs realized return` 모니터링 추가

## 최종 결론

- 추가 전문가 의견 중 실제 플랜을 바꿀 만큼 적합한 것은 `4개`다.
- 특히 새로 승격된 것은 아래 2개다.
  - `원격 경량 프로파일링`
  - `스캘핑 live hard stop taxonomy audit`
- 나머지는 방향성은 인정하되, 현재 단계에서는 `관측 선행` 또는 `후순위`가 맞다.
