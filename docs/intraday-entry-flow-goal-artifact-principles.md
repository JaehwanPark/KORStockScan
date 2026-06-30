# Intraday Entry Flow Goal Artifact Principles

Use this text when opening an intraday entry-flow monitoring goal. It keeps generated artifacts aligned with the fixed `data/report/intraday_entry_flow/` structure.

## Goal Text Block

```text
/goal <HH:MM:SS>부터 <HH:MM:SS> KST까지 10분 간격으로 rising missed / BUY 후보 접근 / 일반 BUY submit 병목을 점검한다.

산출물 원칙:
- intraday_entry_flow report는 timestamp별 md/csv 스냅샷을 누적 보존하지 않는다.
- flow md는 반드시 고정 갱신 파일 `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_current.md`에 덮어쓴다.
- flow csv가 필요하면 `/tmp/intraday_entry_flow_YYYY-MM-DD_<window>.csv`로 임시 생성하고, 최종 확인 후 삭제한다.
- 목표 종료 시에는 최종 요약만 `data/report/intraday_entry_flow/intraday_entry_flow_YYYY-MM-DD_<HHMM>_to_<HHMM>_final_stabilization.md`로 남긴다.
- final stabilization의 `source_flow_final`은 timestamp 스냅샷이 아니라 `intraday_entry_flow_YYYY-MM-DD_current.md`를 가리키게 한다.
- 중간 `intraday_entry_flow_YYYY-MM-DD_*_to_*.md/.csv`가 생겼으면 목표 종료 전에 삭제한다.
- code-review 누적 기록은 `docs/code-reviews/intraday-entry-flow-operational-log.md`에 결정/변경/검증/운영경계 단위로만 추가한다. 10분 루프별 숫자는 누적 기록 문서에 붙이지 않는다.

판정 원칙:
1. forced scout / rising_missed_one_share_entry는 일반 BUY submit 성공으로 세지 않는다.
2. forced scout 제외 residual과 forced scout residual을 분리한다.
3. latency_state_danger는 stale quote 단정이 아니라 spread/latency pre-submit 품질가드로 root cause를 분해한다.
4. known preserved quality guard와 unknown/actionable latency danger를 분리한다.
5. threshold/order/provider/bot 변경 없이 diagnostic/source-quality 범위에서만 판단한다.
```

## Required Final Cleanup

- Confirm only the fixed current flow artifact and final stabilization summaries remain for the target date.
- Confirm temporary CSV output is gone.
- Confirm final stabilization summaries do not point to deleted timestamp snapshots.
- Add one concise operational-log entry only when the goal changes a durable rule, source-quality contract, report contract, or artifact retention decision.

## Forbidden Uses

- Do not use intraday flow diagnostics to mutate runtime thresholds intraday.
- Do not treat forced one-share scout events as normal BUY submit/fill success.
- Do not bypass stale quote, latency DANGER, spread, broker/account/order/quantity/cooldown, hard/protect/emergency guards.
- Do not use final stabilization summaries as standalone EV or real execution quality approval evidence.
