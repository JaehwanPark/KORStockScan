# Analysis Codebase Status

기준: `2026-05-23 KST`

## 판정

- `offline_live_canary_bundle`: retired/removed. EC2 서버 증설 후 로컬 offline export/analyze 경로를 운영 복구 수단으로 쓰지 않아 codebase와 CLI를 삭제했다.
- `offline_gatekeeper_fast_reuse_bundle`: retired/removed. 과거 증적 링크만 남기고 codebase와 legacy wrapper를 삭제했다.
- `april_follow_through_backfill.py`: retired/removed. 2026-04-28 월간 lightweight backfill 증적 이후 현재 자동화 consumer가 없어 삭제했다.
- `claude_scalping_pattern_lab`: postclose monitoring 분석랩이며, `scalping_pattern_lab_automation`이 EV backlog/observability를 machine-readable `code_improvement_order`와 `auto_family_candidate`로 집계한다. `gemini_scalping_pattern_lab`은 자동 실행에서 제거된 manual/archive-only 랩이다. live routing, threshold mutation, 주문/청산 판단, repo code patch를 직접 수행하지 않는다.

## 근거

- gatekeeper 전용 offline bundle/codebase는 `2026-04-27` checklist에서 삭제 대상으로 닫혔다.
- 최근 운영 사용 이력은 `2026-04-27` gatekeeper export와 `2026-04-28` live canary export 이후 확인되지 않았고, 로컬 분석 경로는 더 이상 사용하지 않는다.
- legacy `gatekeeper_fast_reuse`/`entry_latency_offline` compatibility summary 생성도 함께 폐기했다.
- `april_follow_through_backfill.py` 참조는 과거 `2026-04-28~04-29` checklist 증적뿐이며 현재 import/cron/test consumer가 없다.

## 금지선

- analysis lab 산출물만으로 live threshold/order/exit 판단이나 repo code를 직접 변경하지 않는다.
- performance report의 core runtime `gatekeeper_fast_reuse_ratio`/latency p95와 pattern lab 제안은 submitted/full/partial, blocker, 체결품질, `COMPLETED + valid profit_rate`와 분리해 `code_improvement_order` 또는 `auto_family_candidate(allowed_runtime_apply=false)`로만 넘긴다. 삭제된 offline compatibility summary를 현재 판단 source로 되살리지 않는다.
