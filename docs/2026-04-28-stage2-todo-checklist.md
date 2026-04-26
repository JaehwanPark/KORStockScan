# 2026-04-28 Stage 2 To-Do Checklist

## 오늘 목적

- `Gemini(main)` live 기준 엔진의 `P2 response schema registry`를 endpoint별 계약 + fallback 단위로만 잠그고, 전역 교체는 금지한다.
- `DeepSeek(remote)`는 `gatekeeper structured-output`을 text report 유지 전제의 option 축으로만 검토하고, 계약/rollback이 없으면 착수하지 않는다.
- `holding cache`와 `Tool Calling`은 기대값 개선 근거와 운영 필요성이 없으면 설계 메모 또는 보류 판정으로만 닫는다.
- `P0/P1`에서 넣은 flag-off 변경은 실로그/테스트 acceptance를 깨지 않는지 확인하고, `P2+`는 live 엔진 분포 변경과 분리해 다룬다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 `1축 canary`만 허용하고, replacement도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 예외: 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되고 판정이 provisional임을 명시할 때만 `stage-disjoint concurrent canary`로 검토할 수 있다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장후 체크리스트 (18:05~19:20)

- [ ] `[GeminiSchema0428] Gemini JSON endpoint schema registry 적용 범위 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 6개 endpoint를 분리하고, `response_schema` 실패 시 기존 `json.loads/raw regex fallback` 경로로 즉시 복귀할 수 있어야 한다. `system_instruction`/deterministic JSON config flag와 schema registry를 한 change set에서 묶어 global live 전환하지 않는다.
  - why: Gemini는 `main` 실전 기준 엔진이라 범용 `_call_gemini_safe()` 한 줄 변경으로 전 경로를 동시에 바꾸면 BUY/WAIT/DROP 분포와 parse_fail 축이 함께 흔들린다.
  - 다음 액션: schema registry가 준비되면 endpoint별 테스트 목록과 fallback 필드를 아래 항목에서 잠그고, 준비가 안 되면 막힌 이유 1개와 재시각 1개를 same-day 메모에 남긴다.

- [ ] `[GeminiSchema0428] Gemini schema/fallback 테스트 매트릭스 및 관찰 필드 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` 계약 테스트, `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 영향 관찰 필드를 같이 고정한다. live canary를 검토하려면 `flag default OFF`, `rollback owner`, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 문서에 잠겨 있어야 한다.
  - why: schema는 파싱만 바꾸는 게 아니라 장애 관측 축과 rollback 경계까지 같이 정하지 않으면 `main` live 엔진에서 원인귀속이 흐려진다.
  - 다음 액션: 조건이 충족되면 `2026-04-29 POSTCLOSE` canary 검토 슬롯을 열고, 미충족이면 same-day 보류로 닫는다.

- [ ] `[DeepSeekGatekeeper0428] DeepSeek gatekeeper structured-output option 축 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `generate_realtime_report()`의 사람용 text report는 유지하고, `evaluate_realtime_gatekeeper()`에만 JSON option 경로를 검토한다. `flag default OFF`, JSON 실패 시 text fallback, `action_label/allow_entry/report/selected_mode/timing` contract 유지 테스트가 없으면 착수하지 않는다.
  - why: DeepSeek는 `remote` 운용 엔진이지만, gatekeeper structured-output은 퍼블릭 contract와 캐시 테스트를 건드려 진입 판단 분포를 바꿀 수 있다.
  - 다음 액션: 승인되면 `remote observe-only` 또는 `remote canary-only` 중 1개 경로만 택하고, 미승인이면 막힌 조건과 다음 절대시각을 남긴다.

- [ ] `[DeepSeekHolding0428] DeepSeek holding cache bucket 조정 근거 점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `holding cache miss 증가 -> completed_valid 품질 개선` 근거가 있는지, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 분리 기준에서 gain이 있는지 먼저 확인한다. 근거가 없으면 `_compact_holding_ws_for_cache()` 버킷 축소는 same-day 보류로 닫는다.
  - why: holding cache 세분화는 비용/호출량을 늘릴 수 있지만 기대값 개선이 아직 고정되지 않았다.
  - 다음 액션: 승인 근거가 생기면 `2026-04-29 POSTCLOSE` 설계 슬롯으로 넘기고, 없으면 `보류 유지`로 닫는다.

- [ ] `[DeepSeekTooling0428] DeepSeek Tool Calling 필요성/범위 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: Tool Calling이 실제로 `JSON parse_fail`, contract drift, 운영 복잡도 감소에 기여하는지 판단하고, 아니면 설계 메모로만 남긴다. SDK/응답 schema/테스트/rollback 구조가 준비되지 않으면 구현 작업으로 승격하지 않는다.
  - why: 현재 Tool Calling은 기능 개선보다 code debt/설계 검토 성격이 강하다.
  - 다음 액션: 필요성이 약하면 backlog 관찰로만 남기고, 필요성이 강하면 별도 workorder 초안과 테스트 범위를 same-day 문서화한다.
