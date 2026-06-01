# Runtime Apply Gap Audit - 2026-05-19

- 상태: `fail`
- 런타임 적용률: `0.0%`
- 양수 EV + source-quality pass 후보: `0`
- 실패 표면화: `2`
- 재시도 큐: `2`
- Codex 작업지시: `2`
- source dimension gap: `0` / actionable=`0`
- quiet gap: `2` / rollup=`2` / directive=`1`

## 공격적 런타임 추진 대상
- 대상 없음

## 재시도 큐
- `lifecycle_bucket_discovery_missing_artifact`: owner=lifecycle_bucket_discovery, stage=rerun_lifecycle_bucket_discovery, deadline=immediate_same_date_postclose_rerun
- `runtime_apply_bridge_missing_artifact`: owner=runtime_apply_bridge, stage=rerun_runtime_apply_bridge, deadline=immediate_same_date_postclose_rerun

## Codex 작업지시
- `RETRY_MISSING_ARTIFACT_CHAIN`: RETRY_MISSING_ARTIFACT_CHAIN:  후보가 runtime_apply_bridge_missing_artifact 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.
- `REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING`: REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING: observation_source_quality_audit:warning_summary 후보가 observation_warning_not_handed_off 상태입니다. 생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, runtime/order/provider/cap guard는 우회하지 마십시오.

## 계약
- 내부 AI 프롬프트 언어: `en`
- 사용자 표시 언어: `ko`
- runtime/env/live order 변경: 금지
