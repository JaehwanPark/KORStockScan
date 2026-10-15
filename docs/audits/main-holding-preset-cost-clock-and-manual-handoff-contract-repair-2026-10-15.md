# Main 보유 preset·비용 시각·수동 이관 재생 계약 수리 — 2026-10-15

## 결정과 소유권

사용자의 “보유·재생 계약을 먼저 수리하고 리뷰·수정보완 후 배포 가능한 커밋 생성” 요청을 구현했다. 기존 OPEN `HoldingProfitExitSourceContractRepair`가 소유한다. 연구 label의 비용 후 `+0.4% / -3% / 1800초 / 비용률 0.0023`, 공통 stop pin, 실제 별도 preset 및 실제 수동 등록 결과를 병렬로 보존한다. 연구 입력·응답·membership·과거 지표를 변경하거나 운용 stop을 연구 수치로 덮어쓰지 않는다.

작업 기준은 실제 선택본 `451b6c1ec84fafa563d95381e95c814ac2b2b18b`이다. 격리 작업 트리는 `/home/ubuntu/KORStockScan-worktrees/nonfixed-registration-receipt-20261015`, branch는 `fix/nonfixed-registration-receipt-20261015`다. 앞서 승인된 [비상시 등록 완료 연결 수리](main-nonfixed-registration-source-gap-review-2026-10-15.md)도 같은 커밋에 포함한다. 다른 workspace 연구·익절 변경은 수입하지 않았다. 이번 요청은 배포 준비 커밋까지이며 실제 배포·재기동·정책/env/제외 파일·주문 변경은 실행하지 않았다.

## 확인된 계약 결함과 수리

| 경계 | 수정 전 | 수정 후 |
| --- | --- | --- |
| 비용 시각 producer → replay | `known_at`의 timezone-aware ISO 문자열을 숫자 전용 reader가 거부 | 원 row/hash를 먼저 검증하고 aware ISO와 기존 숫자 epoch를 소비 시점에 해석. naive·bool·비정상·0 이하·미래 시각은 계속 결손 |
| 공통 pin → preset | `SCALP_PRESET_TP`에도 공통 soft/hard/grace만 기록 | 실제 evaluator의 preset hard/grace/emergency·보유 시간·활성화·position/pin/clock을 별도 sealed receipt로 포착. 공통 pin은 그대로 보존 |
| preset → 재생 | 공통 soft 후보가 나온 뒤에만 preset을 censor | 실제 preset safety를 먼저 평가하고 grace/emergency/protect/manual/pending/비활성 우선순위를 보존. 안전 후보는 매도·체결·모델 손익으로 바꾸지 않음 |
| 실제 등록 → 장후 consumer | 기존 수동 이관 로그만 있어 exact position/pin 결속이 없음 | 등록 결과가 결정된 뒤 기존 로그에 JSON으로 sealed receipt 추가. 대기와 등록 완료를 별도로 저장하고 기존 source index/cache/position census까지 연결 |
| 연구 → 운용 비교 | 연구 -3%와 운용 -1.4%의 관계가 불명확 | 장후 report의 연구 reference와 position별 공통 값·실효 preset·관측 safety 후보·실제 등록 결과를 별도 필드로 보고 |

실제 보조 AI에 해당 reference가 전달됐다고 새로 증명하는 필드가 아니다. `reference_contract_not_actual_ai_input`을 명시해 기존 PASS를 새 문맥의 PASS로 재표기하지 않는다. `preset_crossing`도 관측된 safety 후보이며, 완전한 first crossing 증명이 없으면 `first_crossing_proven=false`를 유지한다.

수동 이관 receipt는 동일 보유 주기·pin·role·market·record·시각과 원천 hash를 검증한다. 같은 시각의 quote와 terminal이 충돌하지 않도록 reference ID에 event kind를 분리한다. 실제 등록 완료 뒤에는 이후 가격이 emergency를 넘어도 자동매도 후보를 새로 만들지 않는다. 등록 대기를 완료로 승격하거나 수동 이관을 SELL로 기록하지 않으며 실현 순손익은 null이다. 과거 이관 로그에 exact receipt가 없으면 `unbound_handoff_events`로 남기고 소급 합성하지 않는다.

## 원본 사건의 불변 재검증

[원본 추출 manifest](../../tmp/holding-stop-contract-repair-20261015/original-extraction.json)와 [수정 전후 소비 결과](../../tmp/holding-stop-contract-repair-20261015/original-probe-verification.json)를 보존했다. 기존 17MiB 발췌본에서 필요한 hash의 행까지 4,576,888 bytes만 순차 읽었다. 원본 내용 hash `644e366042e9d1b01846e67276d75a78838332da43c907d4c279763dc9e7ac73`와 문자열 `2026-10-15T14:06:34.802536+09:00`을 그대로 사용했다.

- 사건 실행본 `bb4808c77`: `source_gap/cost_model_source_missing` 재현.
- 수정본: 비용 시각을 통과한 뒤 원본 `partial_fill=true`에 따라 `censored/alternative_lifecycle_unidentified`. 원천·시각·hash를 수정하지 않았다.
- 주문 1/1 체결과 계획 bundle 1/5를 동일한 전량체결로 만들지 않았다. 이 행의 flag를 제거해 경제성 재생을 강행하지 않았다.
- 원본에는 새 preset receipt가 없으므로 과거의 정밀 first crossing/전체 주문 경로 재생 완료를 주장하지 않는다. 원본 `actual_broker_cost=false` 모델은 실제 정산 비용이 아니며 실현 순손익·새 주문 모두 생성하지 않았다.

## 리뷰·수정보완과 검증

`korstockscan-review-gate`에 따라 생산자 → 기존 logger → reference index → replay/cache → publication reader와 fast/normal·수동 제외 경계를 리뷰했다. 첫 보유 회귀 176개, 보완 뒤 관련 회귀 390개가 통과했다. 리뷰에서 다음을 추가 수리했다.

1. scalar 문자열 logger에 nested dict를 직접 넘기지 않고 canonical JSON으로 고정해 native reader가 읽도록 수정했다.
2. 등록 예약 때의 position/pin과 관측 receipt를 비교하고, pin 결손·손상 관측 실패가 실제 이관의 주문 차단을 깨지 않도록 격리했다.
3. fast prearm 관측을 활성 safety 평가로 재표기하지 않고, 수동 이관 이후 emergency를 자동관리 후보로 해석하지 않도록 보완했다.
4. 마지막 확장 테스트에서 발견된 replay의 safety 함수 인자명 오기를 수정하고 동일 전체 표적 집합을 다시 검증했다. 실패 로그는 보존하며 PASS로 세지 않는다.
5. quote coverage·시계·route/epoch 결손 행에서 safety crossing을 새로 추론하지 않도록 보완했다. 이후 실제 등록 receipt가 있어도 앞선 quote 결손은 source gap으로 남긴다.

최종 테스트 결과는 [최종 표적 검증](../../tmp/holding-stop-contract-repair-20261015/final-targeted-validation-round4.log), compile·링크/단일 owner·print-only parser 및 원천 보존은 [리뷰 manifest](../../tmp/holding-stop-contract-repair-20261015/review-result.json)가 소유한다. 새 Python module/test 파일을 추가하지 않고 기존 scalping/automation owner와 기존 테스트 파일을 보완했다. 기존 source writer의 queue/용량 제한을 유지하고 장중 추가 API/AI/분봉 조회나 대용량 원천 polling을 넣지 않았다. 장후 운용 계약 비교는 기존 position materialization을 재사용하며 원 raw를 추가 전수 decode하지 않는다.

## 배포 후 남는 수용

이 커밋은 코드·계약 수리의 배포 준비다. 선택·PID 소비·새 자연 발생 receipt·정산 경제성과 다르다. 기존 OPEN owner를 닫지 않으며 추가 경제성 채택 gate를 만들지 않는다.

허용된 후속 배포에서 동일 position/pin으로 새 preset receipt → safety 후보 → 등록 대기/완료 receipt → 장후 native index/cache/report 소비를 확인한다. 기존 공통/preset/emergency·수동 custody·stale·계좌·주문·수량·cap·cooldown·provider 안전장치를 그대로 유지한다. 과거 원천 결손이나 실현 비용 부재는 null/source gap으로 남긴다. 이번 범위 밖인 보유 AI context 결손과 trailing 전이 한도/상황 pin의 자연 수용은 기존 owner의 별도 Acceptance로 유지한다.
