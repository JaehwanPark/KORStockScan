# Plan Rebase Runtime History Archive - 2026-05-19

이 문서는 `Plan Rebase`와 `AGENTS.md`에서 현재 가이드라인이 아니라 날짜별 운영 경과로 남아 있던 내용을 분리 보존한다. 현재 active/open 판단은 `docs/plan-korStockScanPerformanceOptimization.rebase.md`와 당일 checklist를 기준으로 한다.

## 2026-05-15 이전 상태

- `2026-05-15` PREOPEN 기준 `auto_bounded_live` selected runtime family는 `soft_stop_whipsaw_confirmation` 1개였다.
- `score65_74_recovery_probe`는 `2026-05-13` selected 및 5/13 source 재검증상 open 가능 후보였지만, 5/15 실제 preopen apply에서는 5/14 source rolling_5d primary 재평가 결과 `hold/no_runtime_env_override`로 runtime env에 포함되지 않았다.
- 당시 원칙은 장중 runtime threshold mutation 금지, OpenAI route 고정, sim/probe/counterfactual의 real execution 품질 단독 근거 금지였다.

## 2026-05-18 Operator Override

- `2026-05-18` runtime env는 사용자 운영 override를 포함했다.
- 스캘핑은 `score65_74_recovery_probe`, pre-AI soft gate 재배치, `scalp_entry_adm_runtime_bias_p1`, `holding_exit_matrix_runtime_bias_p1`이 켜졌다.
- 스윙은 one-share real canary와 gatekeeper reject cooldown이 env에 명시됐다.
- 이 상태는 자동화체인의 무단 장중 mutation이 아니라 사용자 명시 operator override이며, threshold/provider/broker submit safety guard 우회 권한은 없었다.

## 2026-05-19 Runtime Framework Migration

- `lifecycle_decision_matrix_runtime` 구현으로 ADM은 개별 source artifact가 아니라 umbrella policy framework로 확장됐다.
- Entry ADM, Holding/Exit ADM, submit observation, scale-in bias는 lifecycle matrix runtime resolver가 감쌀 수 있는 adapter가 됐다.
- 기존 fixed threshold는 삭제하지 않고 `hard_safety`, `baseline_prior`, `bounded_tunable`, `legacy_archive`로 재분류했다.
- runtime 우선순위는 `hard safety veto -> account/order/broker guard -> lifecycle matrix runtime policy -> existing ADM adapter -> baseline fixed threshold fallback`이다.

## Archive 처리 원칙

- 이 문서의 날짜별 항목은 현재 owner가 아니다.
- 현재 owner와 금지선은 Plan Rebase §5~§8과 당일 checklist가 소유한다.
- 과거 operator override, selected family, sample 상태는 증적/근거 링크로만 사용한다.
