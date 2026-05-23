# Runtime Apply Gap Audit 사용 설명서

이 보고서는 “좋아 보이는 후보가 실제 런타임 적용까지 갔는가”를 확인하는 장후 점검표다. 전략을 직접 바꾸는 실행기가 아니라, 막힌 지점과 다음 행동을 드러내는 보고서다.

## 생성 위치

- JSON: `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.json`
- Markdown: `data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_YYYY-MM-DD.md`
- 대시보드: `/bucket-tracking?date=YYYY-MM-DD`

## 먼저 볼 것

1. `상태`
   - `pass`: 당장 표면화된 적용 누락이 없다.
   - `warning`: 다음 장전 적용, 재시도, 관찰이 필요한 항목이 있다.
   - `fail`: 자동화체인 일부가 끊겼다. 그냥 넘어가면 안 된다.

2. `런타임 적용률`
   - 양수 성과 후보 중 실제 적용 방향으로 넘어간 비율이다.
   - 낮으면 “성과 후보가 없었다”가 아니라 “후보가 적용까지 못 갔다”일 수 있다.

3. `공격적 런타임 추진 대상`
   - 성과가 조금이라도 있고 기본 품질 조건을 통과한 후보 목록이다.
   - 여기 있는 항목은 다음 장전 적용, sim 정책 반영, 승인 요청, 코드 보완 중 하나로 닫혀야 한다.

4. `재시도 큐`
   - 자동화체인이 다시 실행하거나 다음 단계에서 소비해야 할 항목이다.
   - 예: 다음 장전 적용 대기, 누락 artifact 재생성, AI 검토 재시도.

5. `Codex 작업지시`
   - 코드 보완이 필요한 항목이다.
   - 여기에 항목이 있으면 사용자는 해당 작업지시를 Codex에 구현 요청할 수 있다.

## 해석 순서

보고서는 아래 순서로 읽는다. 앞 단계가 막혀 있으면 뒤 숫자는 참고만 한다.

1. `상태`를 본다.
   - `fail`이면 성과 판단보다 자동화체인 끊김을 먼저 고친다.
   - `warning`이면 적용 대기나 재시도 대상이 남아 있는 상태다.
   - `pass`면 다음 장후 성과 확인으로 넘어간다.

2. `양수 EV + source-quality pass 후보`를 본다.
   - 0이면 그날은 런타임으로 밀 후보가 거의 없었다는 뜻이다.
   - 1 이상이면 최소 한 개 후보는 적용, sim 반영, 승인 요청, 코드 보완 중 하나로 닫혀야 한다.

3. `런타임 적용률`을 본다.
   - 높으면 후보가 실제 적용 방향으로 잘 넘어가고 있다는 뜻이다.
   - 낮으면 후보가 발견됐지만 적용 단계까지 못 갔다는 뜻이다.
   - 낮은 값 자체가 실패는 아니지만, 재시도 큐나 작업지시가 같이 있으면 조치 대상이다.

4. `공격적 런타임 추진 대상`을 본다.
   - 여기는 “좋아 보이는데 아직 완전히 적용되지 않은 후보”를 보여준다.
   - `현재=post_apply_attribution_pending`이면 다음 장전 적용 또는 다음 장후 성과 확인 대상이다.
   - `현재=sim_auto_approved`이면 실주문이 아니라 sim 정책으로 먼저 열린 상태다.
   - `현재=code_patch_required`이면 코드 보완 없이는 더 못 간다.
   - `현재=source_quality_blocker`이면 성과보다 데이터 품질 문제를 먼저 해결해야 한다.

5. `재시도 큐`를 본다.
   - 여기에 항목이 있으면 그냥 기다리는 것이 아니라 다음 재시도 단계가 정해진 것이다.
   - `owner`는 다시 실행하거나 확인해야 하는 주체다.
   - `stage`는 다음에 봐야 할 자동화 단계다.
   - `deadline`은 언제까지 확인해야 하는지다.

6. `Codex 작업지시`를 본다.
   - 항목이 0이면 현재는 코드 수정 없이 재시도나 다음 장전/장후 확인으로 닫을 수 있다.
   - 항목이 있으면 사용자가 Codex에 구현 지시를 줄 수 있다.

## 자주 나오는 해석

| 표시 | 의미 | 사용자가 할 일 |
| --- | --- | --- |
| `ready_but_not_applied` | 적용 가능한 후보가 다음 장전 적용으로 넘어가야 한다 | 다음 PREOPEN apply 산출물과 runtime env를 확인한다 |
| `post_apply_attribution_pending` | 적용 또는 적용 대기 후 성과 연결이 아직 안 닫혔다 | 다음 장후 성과/attribution에서 붙었는지 확인한다 |
| `positive_edge_stuck_source_only` | 성과 후보가 관찰 상태에 묻혔다 | Codex 작업지시 또는 runtime bridge 보완을 요구한다 |
| `producer_consumer_handoff_missing` | 앞 report에는 후보가 있는데 뒤 report가 소비하지 않았다 | 누락된 consumer를 찾아 보완하고 verifier까지 연결한다 |
| `missing_artifact` | 필요한 report가 없다 | 빠진 report를 재생성하고 audit를 다시 실행한다 |
| `ai_review_unavailable` | AI 검토가 실행되지 못했다 | 같은 입력으로 AI review를 재시도하거나 설정을 확인한다 |
| `ai_parse_fail` | AI 응답을 schema로 읽지 못했다 | 재시도하고 반복되면 AI review 계약 보완을 요청한다 |
| `source_quality_blocker` | 데이터 품질 때문에 판단이 막혔다 | stale/missing/provenance 원인을 먼저 고친다 |
| `approval_required` | 자동 적용이 아니라 승인 artifact가 필요하다 | 승인 여부를 결정하고 artifact 없이는 적용하지 않는다 |

## 숫자를 읽는 기준

- `후보 수`가 많아도 `런타임 적용률`이 0이면, 자동화체인이 성과 후보를 적용으로 밀지 못한 것이다.
- `재시도 큐`가 0이고 `Codex 작업지시`도 0이면, 사용자가 당장 할 일은 다음 장후 결과 확인이다.
- `재시도 큐`가 1 이상이면, 다음 실행 단계와 deadline을 확인한다.
- `Codex 작업지시`가 1 이상이면, 코드 보완 없이 자동화체인이 더 진행되기 어렵다.
- `source_quality_blocker`가 많으면 threshold를 바꿀 문제가 아니라 입력 데이터 품질 문제다.
- `sim_auto_approved`는 실주문 승인이 아니다. sim 정책으로 열린 후보라는 뜻이다.

## 사용자가 할 수 있는 일

### 상태가 `pass`일 때

- 별도 조치 없이 다음 장후 성과를 본다.
- 대시보드에서 적용 후보가 실제 runtime provenance로 이어졌는지만 확인한다.

### 상태가 `warning`일 때

- `재시도 큐`를 본다.
- `ready_but_not_applied`면 다음 PREOPEN apply 결과를 확인한다.
- `ai_review_unavailable` 또는 `ai_parse_fail`이면 같은 날짜 audit를 재실행하거나 AI reviewer 설정을 확인한다.
- `post_apply_attribution_pending`이면 다음 장후 attribution에서 적용 결과가 붙었는지 확인한다.

### 상태가 `fail`일 때

- `Codex 작업지시`가 있으면 그 항목을 구현 대상으로 넘긴다.
- `missing_artifact`면 빠진 producer report를 재생성한 뒤 audit를 다시 실행한다.
- `producer_consumer_handoff_missing`이면 source report에는 후보가 있는데 bridge, workorder, runtime summary, verifier 중 어디에서 사라졌는지 보완한다.
- `positive_edge_stuck_source_only`면 성과 후보가 그냥 관찰 상태에 묻힌 것이므로 workorder 또는 runtime bridge 연결을 요구한다.

## 하지 말아야 할 일

- 이 보고서만 보고 장중 threshold, 주문 guard, provider, bot 상태를 직접 바꾸지 않는다.
- sim/probe 성과를 실주문 품질로 해석하지 않는다.
- `approval_required` 항목을 승인 artifact 없이 적용하지 않는다.
- `source_quality_blocker`를 성과가 나쁜 후보로 단정하지 않는다. 먼저 source 품질 문제를 해결한다.

## 대시보드에서 보는 방법

`/bucket-tracking?date=YYYY-MM-DD`에서 다음 항목을 본다.

- `Runtime Uptake`: 성과 후보가 적용 방향으로 넘어간 비율
- `Runtime gap`: audit 상태
- `retry/directive`: 재시도와 Codex 작업지시 수
- 상세 row의 `runtime_apply_gap` 항목: 후보별로 어디에서 멈췄는지 표시

## Codex에 요청할 때

아래처럼 지시하면 된다.

```text
runtime_apply_gap_audit_YYYY-MM-DD에서 Codex 작업지시가 있는 항목을 구현하고, 테스트와 postclose verifier 연결까지 확인해줘.
```

재시도 큐만 있는 경우에는 이렇게 지시한다.

```text
runtime_apply_gap_audit_YYYY-MM-DD의 retry_queue 항목을 확인하고, 재실행이 필요한 producer/consumer와 다음 PREOPEN 확인 항목을 정리해줘.
```

## 판정 기준

이 보고서의 목적은 “완벽한 후보만 적용”이 아니다. 작은 성과라도 품질과 안전 계약을 통과하면 런타임 방향으로 밀어붙이고, 막히는 이유를 숨기지 않는 것이다.
